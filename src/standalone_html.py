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

In the two stand-alone modes the notebook calls :func:`make_standalone_pod_page`
at the end, which builds the POD's html page with the framework's own
:class:`~src.output_manager.HTMLPodOutputManager`, so the page matches the one
the framework would make. :func:`export_run_settings` writes the notebook's
settings text out as files so the same run can be repeated in batch.

Only the per-POD page is built; the framework's top-level ``index.html`` and
``<pod>.data.log`` need the full framework objects and are not made here.
"""
import os
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
        (see :func:`case_list_for_html`), ``work_dir`` (run's top WORK_DIR),
        ``pod_work_dir``, ``obs_data`` and ``catalog``.
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
        s.work_dir = os.path.abspath(s.runtime_cfg['WORK_DIR'])
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
                             verify_links_flag: bool = True, make_tar: bool = False,
                             log=None) -> str:
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
        make_tar: Also write ``<work_dir>/<pod_name>.tar.gz`` holding the POD
            output directory plus the MDTF banner, so the page displays
            correctly when unpacked elsewhere (like the framework's
            ``make_variab_tar``; netCDF and PS files are left out).
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
    if make_tar:
        tar_path = make_pod_tar(work_dir, pod_name)
        print("Wrote", tar_path)
    return page


def make_pod_tar(work_dir: str, pod_name: str) -> str:
    """Write ``<work_dir>/<pod_name>.tar.gz`` with the POD's output directory and
    the MDTF banner image (which POD pages link to as ``../mdtf_diag_banner.png``).
    Leaves out netCDF and PostScript files, as the framework's tar option does.
    """
    import tarfile
    skip_dirs = {'netCDF', 'PS'}
    skip_ext = ('.nc', '.ps', '.eps', '.PS', '.EPS')

    def _filter(ti):
        parts = ti.name.split('/')
        if any(p in skip_dirs for p in parts) or ti.name.endswith(skip_ext):
            return None
        return ti

    tar_path = os.path.join(work_dir, pod_name + '.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tar:
        banner = os.path.join(work_dir, 'mdtf_diag_banner.png')
        if os.path.isfile(banner):
            tar.add(banner, arcname='mdtf_diag_banner.png')
        tar.add(os.path.join(work_dir, pod_name), arcname=pod_name, filter=_filter)
    return tar_path


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
    nb_stem = os.path.splitext(os.path.basename(nb))[0]
    settings_env = "" if install_pod_settings else f"{POD_SETTINGS_ENV}={out['settings_jsonc']} "
    print("\nTo repeat this run in batch:")
    print("  MDTF framework (reads settings.jsonc from the POD directory"
          + ("" if install_pod_settings else "; use install_pod_settings=True first") + "):")
    print(f"    cd {repo_root()} && ./mdtf -f {out['runtime_yml']}")
    print("  Stand-alone notebook, no Jupyter:")
    print(f"    cd {run.pod_code_dir} && {RUNTIME_CONFIG_ENV}={out['runtime_yml']} {settings_env}"
          f"jupyter nbconvert --to html --execute {nb}"
          f" --output-dir {run.pod_work_dir} --output {nb_stem}_ipynb")
    return out
