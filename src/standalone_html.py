"""Helpers for running a notebook POD outside the MDTF framework.

A notebook POD can be run three ways:

- ``framework``: by the MDTF framework (``mdtf -f input.yml``). The framework
  sets environment variables (``POD_HOME``, ``WORK_DIR``, ``case_env_file``,
  the POD's ``pod_env_vars``, ...) and builds the POD's html page itself.
- ``headless``: stand-alone, without Jupyter, e.g.
  ``MDTF_RUNTIME_CONFIG=input.yml jupyter nbconvert --to html --execute nb.ipynb``.
- ``interactive``: stand-alone in Jupyter, with the run settings typed into the
  notebook as text in the same formats as the framework's files (an
  ``input_*.yml`` runtime config and the POD's ``settings.jsonc``).

In the two stand-alone modes the notebook calls :func:`make_standalone_output`
at the end. It writes the same output layout the framework writes
(``<WORK_DIR>/MDTF_output/`` with ``index.html``, the MDTF banner, the POD's
page, logs and ``case_info.yml``, ``config_save.json``, and optionally
``<WORK_DIR>/MDTF_output.tar``), using the framework's own html templates and
:class:`~src.output_manager.HTMLPodOutputManager`.

:func:`open_catalog_var` reads a case's model data from an ESM-intake catalog
with the same query the framework uses (with the variable name translated to
the case's convention by :func:`translate_pod_var`), and :func:`export_run_settings` writes
the notebook's settings text out as files so the run can be repeated in batch.
"""
import os
import sys
import io
import re
import shutil
import logging
import datetime
import types
import yaml

from src import util
from src import output_manager, verify_links
from src.util import json_utils

_log = logging.getLogger(__name__)

# Environment variable that points a headless run at its runtime config file
RUNTIME_CONFIG_ENV = "MDTF_RUNTIME_CONFIG"
# Optional environment variable pointing a headless run at a POD settings file
# (default: settings.jsonc in the POD's code directory)
POD_SETTINGS_ENV = "MDTF_POD_SETTINGS"
# Set by the command-line runner (python -m src.standalone_html run ...): fixed
# output directory, and leave the tar to the runner (made after nbconvert has
# written the executed notebook, as in the framework)
OUTPUT_DIR_ENV = "MDTF_STANDALONE_OUTPUT_DIR"
DEFER_TAR_ENV = "MDTF_STANDALONE_DEFER_TAR"


def repo_root() -> str:
    """Absolute path of the MDTF-diagnostics checkout this module lives in."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _TagTolerantLogger(logging.LoggerAdapter):
    """Logger that accepts (and drops) the framework's ``tags=`` keyword, so
    framework code written for MDTFObjectLogger can be given a plain logger.
    """
    def process(self, msg, kwargs):
        kwargs.pop('tags', None)
        return msg, kwargs


def _get_logger(log=None):
    if log is None:
        log = _log
    if isinstance(log, _TagTolerantLogger):
        return log
    return _TagTolerantLogger(log, {})


# ---------------------------------------------------------------------------
# Reading settings text
# ---------------------------------------------------------------------------

def parse_runtime_yml(text: str) -> dict:
    """Parse runtime config text (``input_*.yml`` format) into a dict."""
    cfg = yaml.safe_load(text)
    if not isinstance(cfg, dict):
        raise ValueError("Runtime config text did not parse to a dict.")
    if not cfg.get('case_list'):
        raise ValueError("Runtime config has no 'case_list' entries.")
    return cfg


def parse_pod_settings(text: str) -> dict:
    """Parse POD settings text (``settings.jsonc`` format, ``//`` comments
    allowed) into a dict, with the same parser the framework uses.
    """
    return json_utils.parse_json(text)


def _read_text(path: str) -> str:
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def year_of(date_str) -> str:
    """Year (4 digits) from an MDTF date string such as ``19950101000000`` or
    ``1995-01-01``.
    """
    m = re.match(r'\s*(\d{4})', str(date_str))
    return m.group(1) if m else ""


def case_list_for_html(runtime_cfg: dict) -> dict:
    """Case list in the shape the html templating expects
    (``pod.multicase_dict['CASE_LIST']``): ``{case: {CASENAME, startdate,
    enddate, convention, FIRSTYR, LASTYR, ...}}``.
    """
    out = dict()
    for case_name, case in runtime_cfg['case_list'].items():
        d = {str(k): v for k, v in (case or {}).items()}
        d['CASENAME'] = case_name
        d['FIRSTYR'] = year_of(d.get('startdate', ''))
        d['LASTYR'] = year_of(d.get('enddate', ''))
        out[case_name] = d
    return out


# ---------------------------------------------------------------------------
# Deciding where the run settings come from
# ---------------------------------------------------------------------------

def detect_run_mode() -> str:
    """Return ``'framework'``, ``'headless'`` or ``'interactive'``.

    - framework: the MDTF framework's environment variables are set
      (``POD_HOME`` and ``case_env_file``).
    - headless: ``$MDTF_RUNTIME_CONFIG`` names a runtime config file.
    - interactive: neither; settings come from the notebook's text cells.
    """
    if os.environ.get('POD_HOME') and os.environ.get('case_env_file'):
        return 'framework'
    if os.environ.get(RUNTIME_CONFIG_ENV):
        return 'headless'
    return 'interactive'


def load_run_settings(pod_name: str, pod_code_dir: str,
                      runtime_yml_text: str = None,
                      pod_settings_text: str = None) -> types.SimpleNamespace:
    """Collect everything a notebook POD needs to run, whichever mode it is in.

    Args:
        pod_name: Short name of the POD (its code directory name).
        pod_code_dir: The POD's code directory.
        runtime_yml_text: Runtime config text from the notebook (interactive mode).
        pod_settings_text: POD settings text from the notebook (interactive mode).

    Returns:
        SimpleNamespace with: ``mode``, ``runtime_cfg`` (dict; in framework
        mode a minimal one built from the framework's case_info.yml),
        ``runtime_yml_text`` (None in framework mode), ``settings`` (full parsed settings.jsonc),
        ``pod_settings_text``, ``pod_env_vars`` (dict of str), ``case_list``
        (see :func:`case_list_for_html`), ``work_dir`` (the run's output
        directory holding the POD directory: ``<WORK_DIR>/MDTF_output`` as in
        the framework, with a version suffix if it exists and ``overwrite`` is
        false), ``pod_work_dir``, ``obs_data`` and ``catalog``.
    """
    mode = detect_run_mode()
    pod_code_dir = os.path.abspath(pod_code_dir)
    s = types.SimpleNamespace(mode=mode, pod_name=pod_name, pod_code_dir=pod_code_dir)

    # --- POD settings (settings.jsonc) ---
    if mode == 'interactive' and pod_settings_text:
        s.pod_settings_text = pod_settings_text
    else:
        path = os.environ.get(POD_SETTINGS_ENV) or os.path.join(pod_code_dir, 'settings.jsonc')
        s.pod_settings_text = _read_text(path)
    s.settings = parse_pod_settings(s.pod_settings_text)
    env_defaults = s.settings.get('settings', {}).get('pod_env_vars', {}) or {}
    if mode == 'framework':
        # framework passes pod_env_vars as environment variables
        s.pod_env_vars = {k: os.environ.get(k, str(v)) for k, v in env_defaults.items()}
    else:
        s.pod_env_vars = {k: str(v) for k, v in env_defaults.items()}

    # --- Runtime config (input_*.yml) ---
    if mode == 'framework':
        s.runtime_cfg = None
        s.runtime_yml_text = None
        with io.open(os.environ['case_env_file'], 'r', encoding='utf-8') as f:
            case_info = yaml.safe_load(f)
        s.case_list = dict()
        for case_name, case in case_info['CASE_LIST'].items():
            d = dict(case)
            d.setdefault('CASENAME', case_name)
            d['FIRSTYR'] = year_of(d.get('startdate', ''))
            d['LASTYR'] = year_of(d.get('enddate', ''))
            s.case_list[case_name] = d
        s.pod_work_dir = os.environ['WORK_DIR']   # framework's WORK_DIR is the POD's dir
        s.work_dir = os.path.dirname(s.pod_work_dir.rstrip(os.sep))
        s.obs_data = os.environ.get('OBS_DATA', '')
        s.catalog = case_info.get('CATALOG_FILE', '')
        # runtime-config-like dict so notebook code can treat all modes alike
        # (catalog is the framework's preprocessed-data catalog)
        s.runtime_cfg = {
            'case_list': {c: {k: d[k] for k in ('convention', 'model', 'startdate', 'enddate')
                              if k in d}
                          for c, d in s.case_list.items()},
            'DATA_CATALOG': s.catalog,
            'WORK_DIR': s.work_dir,
            'OBS_DATA_ROOT': os.path.dirname(s.obs_data.rstrip(os.sep)) if s.obs_data else '',
        }
    else:
        if mode == 'headless':
            s.runtime_yml_text = _read_text(os.environ[RUNTIME_CONFIG_ENV])
        else:
            if not runtime_yml_text:
                raise ValueError("Interactive mode needs the runtime config text.")
            s.runtime_yml_text = runtime_yml_text
        s.runtime_cfg = parse_runtime_yml(s.runtime_yml_text)
        s.case_list = case_list_for_html(s.runtime_cfg)
        # Same output directory rule as the framework (src/util/path_utils.py):
        # <OUTPUT_DIR or WORK_DIR>/MDTF_output, versioned if not overwriting.
        base = s.runtime_cfg.get('OUTPUT_DIR') or s.runtime_cfg['WORK_DIR']
        base = os.path.abspath(os.path.expandvars(os.path.expanduser(base)))
        out_dir = base if 'MDTF_output' in base else os.path.join(base, 'MDTF_output')
        if os.environ.get(OUTPUT_DIR_ENV):
            out_dir = os.environ[OUTPUT_DIR_ENV]
        elif not s.runtime_cfg.get('overwrite', False) and os.path.exists(out_dir):
            out_dir, _ = util.bump_version(out_dir)
        s.work_dir = out_dir
        s.pod_work_dir = os.path.join(s.work_dir, pod_name)
        obs_root = s.runtime_cfg.get('OBS_DATA_ROOT') or ''
        s.obs_data = os.path.join(obs_root, pod_name) if obs_root else ''
        s.catalog = s.runtime_cfg.get('DATA_CATALOG', '')
    return s


def make_pod_work_dirs(pod_work_dir: str):
    """Create the framework's standard POD output layout
    (``model/{PS,netCDF}``, ``obs/{PS,netCDF}``) under *pod_work_dir*.
    """
    for sub in ('model', 'obs'):
        for sub2 in ('PS', 'netCDF'):
            os.makedirs(os.path.join(pod_work_dir, sub, sub2), exist_ok=True)


# ---------------------------------------------------------------------------
# Building the POD page
# ---------------------------------------------------------------------------

def make_standalone_pod_page(pod_name: str, pod_code_dir: str, work_dir: str,
                             settings: dict, case_list: dict,
                             driver: str = "", obs_data: str = "",
                             extra_env: dict = None, save_ps: bool = False,
                             verify_links_flag: bool = True, log=None) -> str:
    """Build the POD's html page in ``<work_dir>/<pod_name>/`` the same way the
    framework does, without running the framework.

    Uses :class:`~src.output_manager.HTMLPodOutputManager` with a lightweight
    stand-in for the framework's POD object. Steps (as in the framework):
    template every ``*.html`` in the POD's code directory into the POD's work
    directory, convert any ``model/PS`` and ``obs/PS`` vector figures to png,
    copy premade obs figures, and remove PS directories unless *save_ps*.
    The MDTF banner image is copied to *work_dir* so the template's
    ``../mdtf_diag_banner.png`` link works.

    Args:
        pod_name: Short name of the POD; the template is ``<pod_name>.html``.
        pod_code_dir: The POD's code directory (holds the html template).
        work_dir: Top-level output directory of the run (the POD's output goes
            in ``work_dir/pod_name``).
        settings: Parsed settings.jsonc dict.
        case_list: ``{case: {CASENAME, startdate, enddate, ...}}``.
        driver: Path of the notebook (shown on the page as ``{{driver}}``).
        obs_data: The POD's obs data directory (``OBS_DATA``), may be empty.
        extra_env: Additional template values (strings).
        save_ps: Keep ``model/PS`` and ``obs/PS`` after conversion.
        verify_links_flag: Check that files linked from the page exist; missing
            files are logged as warnings and returned in the log, not raised.
        log: Logger to use (default: this module's logger).

    Returns:
        Path of the written html page.
    """
    log = _get_logger(log)
    pod_code_dir = os.path.abspath(pod_code_dir)
    work_dir = os.path.abspath(work_dir)
    pod_work_dir = os.path.join(work_dir, pod_name)
    make_pod_work_dirs(pod_work_dir)

    settings_block = dict(settings.get('settings', settings))
    env = {str(k): str(v) for k, v in (settings_block.get('pod_env_vars') or {}).items()}
    env.update({
        'POD_HOME': pod_code_dir,
        'OBS_DATA': obs_data or "",
        'WORK_DIR': pod_work_dir,
        'DATADIR': pod_work_dir,
        'DATE_TIME': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    if extra_env:
        env.update({str(k): str(v) for k, v in extra_env.items()})

    pod = types.SimpleNamespace(
        name=pod_name,
        full_name=f"<{pod_name}>",
        driver=driver or "",
        pod_settings=settings_block,
        pod_env_vars=env,
        multicase_dict={'CASE_LIST': case_list},
        paths=types.SimpleNamespace(
            POD_CODE_DIR=pod_code_dir,
            POD_WORK_DIR=pod_work_dir,
            # find_files on a missing dir just finds nothing
            POD_OBS_DATA=obs_data or os.path.join(pod_work_dir, '_no_obs_data_'),
        ),
        log=log,
        failed=False,
    )

    om = output_manager.HTMLPodOutputManager(
        pod, {'save_ps': save_ps, 'save_pp_data': True},
        types.SimpleNamespace(CODE_ROOT=repo_root())
    )
    om.make_pod_html()
    om.convert_pod_figures(os.path.join('model', 'PS'), 'model')
    om.convert_pod_figures(os.path.join('obs', 'PS'), 'obs')
    om.cleanup_pod_files()

    # banner image, linked from POD pages as ../mdtf_diag_banner.png
    banner = om.html_src_file('mdtf_diag_banner.png')
    if os.path.isfile(banner):
        shutil.copy2(banner, work_dir)

    page = om.pod_html(pod)
    if verify_links_flag:
        missing = find_missing_links(page, pod_name, log=log)
        if missing:
            log.warning("%s: %d linked file(s) missing from the page: %s",
                        pod_name, len(missing), ", ".join(missing))
        else:
            log.info("%s: all linked files found.", pod_name)
    return page


def find_missing_links(page: str, pod_name: str, log=None) -> list:
    """Files linked from POD page *page* (and its sub-pages) that do not exist,
    relative to the POD's work directory. Uses the framework's LinkVerifier.
    """
    log = _get_logger(log)
    pod_work_dir = os.path.dirname(os.path.abspath(page))
    verifier = verify_links.LinkVerifier(
        page, os.path.dirname(pod_work_dir), verbose=False, log=log
    )
    return verifier.verify_pod_links(pod_name)


# ---------------------------------------------------------------------------
# Reading model data from a catalog (stand-alone runs)
# ---------------------------------------------------------------------------

def translate_pod_var(var_name: str, settings: dict, data_convention: str,
                      pod_name: str = "pod"):
    """Translate one POD variable to the naming convention of the model data,
    with the framework's variable translation (``src/translation.py`` and the
    ``data/fieldlist_*.jsonc`` tables), as the framework does in a full run.

    *settings* is the POD's parsed ``settings.jsonc``; its ``convention`` is
    the POD's own convention and *var_name* a key of its ``varlist``.
    *data_convention* is the case's ``convention`` from the runtime config
    (e.g. ``CESM``, ``CMIP``, ``GFDL``).

    Returns the POD's :class:`~src.varlist_util.VarlistEntry`, with the
    translated variable in its ``translation`` attribute (e.g. ``zg`` at
    500 hPa -> ``Z500`` for CESM, ``zg500`` for CMIP, ``hght500`` for GFDL).
    """
    from src.translation import VariableTranslator
    from src.varlist_util import Varlist

    translator = VariableTranslator(repo_root())     # singleton
    if not translator.conventions:
        translator.read_conventions(repo_root())
    pod_convention = settings.get('settings', {}).get('convention', 'no_translation')
    pod = types.SimpleNamespace(
        name=pod_name, pod_data=settings.get('data', {}),
        pod_dims=settings.get('dimensions', {}),
        pod_vars={var_name: settings['varlist'][var_name]},
        pod_settings={'convention': pod_convention}, _log_name=pod_name)
    var = Varlist.from_struct(pod).vars[0]
    var.translation = translator.translate(var, to_convention=data_convention,
                                           from_convention=pod_convention)
    return var


def _full_field_names(var) -> list:
    """Names, in the translated variable's convention, of the full (all
    levels) field that a scalar-coordinate slice such as ``zg500`` is taken
    from (e.g. ``zg``, ``Z3``, ``hght``): fieldlist entries with the same
    standard_name and realm and one more dimension."""
    from src.translation import VariableTranslator

    tv = var.translation
    if not tv.scalar_coords:
        return []
    try:
        lut = VariableTranslator().get_convention(tv.convention).lut
    except (AttributeError, KeyError):    # no_translation: no fieldlist
        return []
    ndim = len(tv.dims) + 1
    return [name for name, att in lut.items()
            if att.get('standard_name') == tv.standard_name
            and att.get('realm', tv.realm) == tv.realm
            and int(att.get('ndim', 0) or 0) == ndim]


def open_catalog_var(catalog: str, case_name: str, var_settings: dict,
                     names=None, out_name: str = None, level=None, var=None):
    """Open one variable of one case from an ESM-intake catalog.

    Uses the same selection as the framework's preprocessor query
    (src/preprocessor.py ``query_catalog``): the case name must appear in the
    file path, and frequency, realm and standard_name must match the POD's
    varlist entry.

    Variable names: with *var*, the POD variable translated to the case's
    convention by :func:`translate_pod_var`, the catalog's ``variable_id`` is
    the translated name (e.g. ``Z500``), or else the full field it is a slice
    of (e.g. ``Z3``); the data are then converted to the POD's units and
    coordinate names with the framework's preprocessor functions
    (``ConvertUnitsFunction``, ``RenameVariablesFunction``). Without *var*,
    *names* (e.g. ``['Z500', 'zg']``) restricts ``variable_id`` and the
    first name that is found is used; with neither, the first variable found.

    If the variable has a vertical dimension and *level* (hPa) is given (default:
    the varlist entry's ``scalar_coordinates`` lev), that level is selected.
    The variable is renamed to *out_name* (default: the POD's variable name
    when *var* is given).

    Returns:
        (xarray.Dataset with the variable renamed to *out_name*, list of files)
    """
    import intake
    import xarray as xr

    if var is not None:
        names = [var.translation.name] + _full_field_names(var)
        out_name = out_name or var.name

    cat = intake.open_esm_datastore(catalog)
    df = cat.df
    sel = df['path'].astype(str).str.contains(case_name, regex=False)
    for col, key in (('frequency', 'frequency'), ('realm', 'realm'),
                     ('standard_name', 'standard_name')):
        if col in df.columns and var_settings.get(key):
            sel &= df[col].astype(str) == str(var_settings[key])
    sub = df[sel]
    if names:
        found = [n for n in names if (sub['variable_id'].astype(str) == n).any()]
        if not found:
            raise util.DataRequestError(
                f"No catalog entries for case {case_name} with variable_id in {list(names)}, "
                f"frequency {var_settings.get('frequency')}, standard_name "
                f"{var_settings.get('standard_name')} in {catalog}.")
        var_id = found[0]
        sub = sub[sub['variable_id'].astype(str) == var_id]
    else:
        if sub.empty:
            raise util.DataRequestError(f"No catalog entries for case {case_name} in {catalog}.")
        var_id = str(sub['variable_id'].iloc[0])
    files = sorted(sub['path'].astype(str).unique())
    ds = xr.open_mfdataset(files, combine='by_coords', chunks={'time': 365})
    ds = ds[[var_id]]

    if level is None:
        level = (var_settings.get('scalar_coordinates') or {}).get('lev')
    zdims = [d for d in ds[var_id].dims if d in ('lev', 'plev', 'level', 'pressure', 'isobaric')]
    if zdims and level is not None:
        z = ds[zdims[0]]
        zdesc = f"{z.attrs.get('standard_name', '')} {z.attrs.get('long_name', '')}".lower()
        if 'hybrid' in zdesc or 'sigma' in zdesc or 'formula_terms' in z.attrs:
            raise util.DataRequestError(
                f"{var_id} for case {case_name} is on model levels ({zdims[0]}: "
                f"{z.attrs.get('long_name', '')}), not pressure levels; {level} hPa needs "
                f"vertical interpolation, which stand-alone runs do not do. Add the "
                f"pressure-level field to the catalog or run with the MDTF framework.")
        lev = float(level) * (100. if float(z.max()) > 2000. else 1.)   # Pa or hPa coordinate
        ds = ds.sel({zdims[0]: lev}, method='nearest').drop_vars(zdims[0], errors='ignore')

    if var is not None:
        # The framework's preprocessing steps for units and coordinate names
        from src.preprocessor import ConvertUnitsFunction, RenameVariablesFunction
        tv = var.translation
        if var_id != tv.name:
            ds = ds.rename({var_id: tv.name})
        ds = ConvertUnitsFunction().execute(var, ds)
        ds = RenameVariablesFunction().execute(var, ds)
        var_id = tv.name
    if out_name and out_name != var_id:
        ds = ds.rename({var_id: out_name})
    return ds, files


# ---------------------------------------------------------------------------
# Full framework-style output (index page, logs, tar)
# ---------------------------------------------------------------------------

def make_standalone_output(run, settings: dict = None, driver: str = "",
                           data_files=None, pod_log_text: str = "",
                           make_tar=None, log=None) -> str:
    """Write the framework's output layout for a stand-alone run.

    In ``run.work_dir`` (``<WORK_DIR>/MDTF_output``): the POD page and figures
    (see :func:`make_standalone_pod_page`), ``<pod>/<pod>.log``,
    ``<pod>/<pod>.data.log`` (also copied to the top level, as the framework
    does), ``<pod>/case_info.yml``, a copy of the driver notebook,
    ``MDTF_main.<date>.log``, ``config_save.json``, ``index.html`` built from the
    framework's templates (src/html), and, if *make_tar* (default: the runtime
    config's ``make_variab_tar``), ``<WORK_DIR>/MDTF_output.tar`` made with the
    framework's tar command.

    Returns:
        Path of index.html.
    """
    log = _get_logger(log)
    settings = settings if settings is not None else run.settings
    pod, out_dir = run.pod_name, run.work_dir
    pod_dir = run.pod_work_dir
    os.makedirs(pod_dir, exist_ok=True)
    now = datetime.datetime.now()
    data_files = list(data_files or [])

    page = make_standalone_pod_page(pod, run.pod_code_dir, out_dir, settings, run.case_list,
                                    driver=driver, obs_data=run.obs_data, log=log,
                                    save_ps=bool(run.runtime_cfg.get('save_ps', False)))

    # driver copy (the framework runs a copy of the notebook in the POD dir)
    if driver and os.path.isfile(driver):
        dest = os.path.join(pod_dir, os.path.basename(driver))
        if os.path.abspath(dest) != os.path.abspath(driver):
            shutil.copy2(driver, dest)

    # case_info.yml (same layout as the framework's case env file)
    with io.open(os.path.join(pod_dir, 'case_info.yml'), 'w', encoding='utf-8') as f:
        yaml.dump({'CATALOG_FILE': run.catalog, 'CASE_LIST': run.case_list}, f,
                  allow_unicode=True, default_flow_style=False)

    # data log, in the POD dir and at the top level
    data_log = (f"# Input model data files used in this run of POD {pod}:\n"
                + "".join(f"{p}\n" for p in data_files)
                + f"\n# Preprocessed files used as input to POD {pod}:\n"
                  "# (Stand-alone notebook run: no framework preprocessing.)\n")
    for d in (pod_dir, out_dir):
        with io.open(os.path.join(d, pod + '.data.log'), 'w', encoding='utf-8') as f:
            f.write(data_log)

    # POD log and main log
    settings_block = settings.get('settings', settings)
    head = util.mdtf_log_header(f"MDTF {pod} DIAGNOSTIC LOG")
    pod_log = (head + f"Stand-alone notebook run ({run.mode}) of {driver}\n"
               f"Finished {now:%Y-%m-%d %H:%M:%S}\n\n### POD settings (pod_env_vars):\n"
               + "".join(f"  {k}: {v}\n" for k, v in run.pod_env_vars.items())
               + "\n### Cases:\n"
               + "".join(f"  {c}: {d.get('startdate', '')} - {d.get('enddate', '')}\n"
                         for c, d in run.case_list.items())
               + ("\n" + pod_log_text if pod_log_text else ""))
    with io.open(os.path.join(pod_dir, pod + '.log'), 'w', encoding='utf-8') as f:
        f.write(pod_log)
    main_log = os.path.join(out_dir, f"MDTF_main.{now:%Y-%m-%d:%H.%M.%S}.log")
    with io.open(main_log, 'w', encoding='utf-8') as f:
        f.write(util.mdtf_log_header("MDTF STAND-ALONE NOTEBOOK RUN LOG"))
        f.write(f"POD {pod} run stand-alone ({run.mode}) from {driver}\n"
                f"Output: {out_dir}\nPOD page: {page}\n")

    # config_save.json: the runtime config used
    util.write_json(run.runtime_cfg, os.path.join(out_dir, 'config_save.json'), log=log)

    # index.html from the framework's templates, as HTMLOutputManager.make_html does
    html_dir = os.path.join(repo_root(), 'src', 'html')
    tdict = {str(k): str(v) for k, v in run.pod_env_vars.items()}
    tdict.update(output_manager.html_templating_dict(types.SimpleNamespace(
        name=pod, pod_settings=settings_block, pod_env_vars=dict(tdict),
        multicase_dict={'CASE_LIST': run.case_list},
        driver=driver)))
    tdict.update({'DATE_TIME': now.strftime("%A, %d %B %Y %I:%M%p (UTC)"),
                  'PODNAME': pod, 'WORK_DIR': pod_dir, 'OUTPUT_DIR': pod_dir,
                  # relative, so the link works when the output is moved or put on the web
                  # (the framework writes the absolute path)
                  'MAIN_LOG': os.path.basename(main_log)})
    index = os.path.join(out_dir, 'index.html')
    if os.path.exists(index):
        os.remove(index)
    util.append_html_template(os.path.join(html_dir, 'mdtf_header.html'), index, tdict)
    with io.open(index, 'a', encoding='utf-8') as f:
        f.write("<TABLE><TR><TD style='font-weight:bold'>Case Settings\n        ")
        for case_name, case in run.case_list.items():
            f.write(util._DoubleBraceTemplate("""
        <TR><TD align=left>{{CASENAME}}\n
        <TR><TD align=left>Date Range: {{startdate}} - {{enddate}}\n
        <TR><TD align=left>Data Convention: {{convention}}\n
        """).safe_substitute({str(k): str(v) for k, v in case.items()}))
    util.append_html_template(os.path.join(html_dir, 'pod_result_snippet.html'), index, tdict)
    util.append_html_template(os.path.join(html_dir, 'mdtf_footer.html'), index, tdict)
    print("Wrote", index)

    if make_tar is None:
        make_tar = bool(run.runtime_cfg.get('make_variab_tar', False))
    if make_tar and os.environ.get(DEFER_TAR_ENV):
        print("Tar file will be made by the runner after the notebook finishes.")
    elif make_tar:
        print("Wrote", make_output_tar(out_dir))
    return index


def make_output_tar(out_dir: str) -> str:
    """``<out_dir>.tar`` (gzip), made with the same command as the framework's
    HTMLOutputManager.make_tar_file.
    """
    out_dir = out_dir.rstrip(os.sep)
    out_path = out_dir + '.tar'
    tar_flags = ' '.join(f"--exclude=.{s}" for s in ('netCDF', 'nc', 'ps', 'PS', 'eps'))
    util.run_shell_command([f'tar {tar_flags} -czf {out_path} -C {out_dir} .'])
    return out_path


# ---------------------------------------------------------------------------
# Exporting the notebook's settings for a batch run
# ---------------------------------------------------------------------------

def export_run_settings(run, dest_dir: str = None, notebook: str = None,
                        install_pod_settings: bool = False) -> dict:
    """Write the run's settings text to files so the run can be repeated in batch.

    Writes ``input_<first case>.yml`` (runtime config, verbatim) and
    ``settings.jsonc`` (POD settings, verbatim) to *dest_dir* (default: the
    POD's work directory) and prints the commands to repeat the run.

    Args:
        run: Namespace returned by :func:`load_run_settings`.
        dest_dir: Directory for the exported files.
        notebook: Path of the notebook (for the printed nbconvert command).
        install_pod_settings: Also copy settings.jsonc into the POD's code
            directory, where the framework reads it (overwrites that file).

    Returns:
        dict with the paths written: ``runtime_yml``, ``settings_jsonc`` and,
        if installed, ``installed_settings``.
    """
    if run.runtime_yml_text is None:
        raise ValueError("No runtime config text to export (framework run).")
    dest_dir = os.path.abspath(dest_dir or run.pod_work_dir)
    os.makedirs(dest_dir, exist_ok=True)
    first_case = next(iter(run.case_list))
    out = dict()
    out['runtime_yml'] = os.path.join(dest_dir, f"input_{first_case}.yml")
    out['settings_jsonc'] = os.path.join(dest_dir, "settings.jsonc")
    for path, text in ((out['runtime_yml'], run.runtime_yml_text),
                       (out['settings_jsonc'], run.pod_settings_text)):
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(text.strip('\n') + '\n')
        print("Wrote", path)
    if install_pod_settings:
        out['installed_settings'] = os.path.join(run.pod_code_dir, 'settings.jsonc')
        shutil.copy2(out['settings_jsonc'], out['installed_settings'])
        print("Installed", out['installed_settings'])

    nb = notebook or os.path.join(run.pod_code_dir, f"{run.pod_name}.ipynb")
    print("\nTo repeat this run in batch:")
    print("  MDTF framework (reads settings.jsonc from the POD directory"
          + ("" if install_pod_settings else "; use install_pod_settings=True first") + "):")
    print(f"    cd {repo_root()} && ./mdtf -f {out['runtime_yml']}")
    print("  Stand-alone notebook, no Jupyter (same output layout as the framework):")
    settings_opt = "" if install_pod_settings else f" --settings {out['settings_jsonc']}"
    print(f"    cd {repo_root()} && python -m src.standalone_html run {nb}"
          f" --config {out['runtime_yml']}{settings_opt}")
    return out


def export_saved_notebook(notebook: str, out_dir: str, since: float = None) -> str:
    """Interactive runs: write the SAVED copy of the notebook as
    ``<out_dir>/<notebook>_ipynb.html`` (``jupyter nbconvert --to html``, not
    re-executed), the same file a headless or framework run makes.

    nbconvert reads the notebook file on disk, not the kernel, so the html only
    shows the outputs as of the last save. If *since* (a ``time.time()`` value,
    e.g. when the run started) is given and the file has not been saved since
    then, nothing is written and a message asks the user to save first.

    Returns:
        Path of the html file, or "" if it was not written.
    """
    import subprocess
    import time
    stem = os.path.splitext(os.path.basename(notebook))[0]
    html = os.path.join(out_dir, stem + '_ipynb.html')
    if not os.path.isfile(notebook):
        print(f"Executed notebook not written: {notebook} not found.")
        return ""
    if since is not None and os.path.getmtime(notebook) < since:
        saved = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(notebook)))
        print(f"Executed notebook not written: {os.path.basename(notebook)} was last saved at "
              f"{saved}, before this run started, so it does not have this run's outputs.\n"
              f"Save the notebook (Ctrl-S) and re-run this cell.")
        return ""
    cmd = [sys.executable, '-m', 'nbconvert', '--to', 'html', notebook,
           '--output-dir', out_dir, '--output', stem + '_ipynb']
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Executed notebook not written, nbconvert failed:\n" + res.stderr[-2000:])
        return ""
    print(f"Wrote {html} (outputs as of the last save)")
    return html


# ---------------------------------------------------------------------------
# Command-line runner for headless stand-alone runs
# ---------------------------------------------------------------------------

def run_notebook(notebook: str, config: str, settings: str = None,
                 kernel: str = None) -> str:
    """Run a notebook POD stand-alone without Jupyter, writing the framework's
    output layout: executes the notebook with ``jupyter nbconvert --execute``
    (the notebook builds the page and logs), saves the executed notebook as
    ``<pod>/<notebook>_ipynb.html`` and then, if the runtime config sets
    ``make_variab_tar``, makes ``MDTF_output.tar``.

    Returns:
        The run's output directory.
    """
    import subprocess
    notebook = os.path.abspath(notebook)
    pod_code_dir = os.path.dirname(notebook)
    pod_name = os.path.basename(pod_code_dir)
    env = dict(os.environ)
    env[RUNTIME_CONFIG_ENV] = os.path.abspath(config)
    if settings:
        env[POD_SETTINGS_ENV] = os.path.abspath(settings)
    for k in ('POD_HOME', 'case_env_file'):   # never look like a framework run
        env.pop(k, None)
    # resolve the output directory once, here, so notebook and runner agree
    saved = {k: os.environ.get(k) for k in (RUNTIME_CONFIG_ENV, POD_SETTINGS_ENV, OUTPUT_DIR_ENV)}
    os.environ[RUNTIME_CONFIG_ENV] = env[RUNTIME_CONFIG_ENV]
    if settings:
        os.environ[POD_SETTINGS_ENV] = env[POD_SETTINGS_ENV]
    os.environ.pop(OUTPUT_DIR_ENV, None)
    try:
        run = load_run_settings(pod_name, pod_code_dir)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    os.makedirs(run.pod_work_dir, exist_ok=True)
    env[OUTPUT_DIR_ENV] = run.work_dir
    env[DEFER_TAR_ENV] = "1"
    stem = os.path.splitext(os.path.basename(notebook))[0]
    cmd = ['jupyter', 'nbconvert', '--to', 'html', '--execute', notebook,
           '--ExecutePreprocessor.timeout=-1',
           '--output-dir', run.pod_work_dir, '--output', stem + '_ipynb']
    if kernel:
        cmd.append(f'--ExecutePreprocessor.kernel_name={kernel}')
    print("Running:", ' '.join(cmd))
    subprocess.run(cmd, cwd=pod_code_dir, env=env, check=True)
    if run.runtime_cfg.get('make_variab_tar', False):
        print("Wrote", make_output_tar(run.work_dir))
    print("Output:", os.path.join(run.work_dir, 'index.html'))
    return run.work_dir


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog='python -m src.standalone_html',
        description='Stand-alone runs of MDTF notebook PODs.')
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help='run a notebook POD without Jupyter, framework-style output')
    r.add_argument('notebook', help='path of the POD notebook')
    r.add_argument('--config', '-f', required=True, help='runtime config (input_*.yml)')
    r.add_argument('--settings', help="POD settings file (default: the POD's settings.jsonc)")
    r.add_argument('--kernel', help='Jupyter kernel name (default: the notebook\'s)')
    a = p.parse_args(argv)
    if a.cmd == 'run':
        run_notebook(a.notebook, a.config, a.settings, a.kernel)


if __name__ == '__main__':
    main()
