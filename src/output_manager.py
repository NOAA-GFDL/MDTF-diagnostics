"""Implementation of the OutputManager plugin, which templates html and organizes
the PODs' output files.
"""
import os
import abc
import datetime
import glob
import io
import shutil
import yaml
from src import util, verify_links

import logging
_log = logging.getLogger(__name__)


class AbstractOutputManager(abc.ABC):
    """Abstract interface for any OutputManager."""
    def __init__(self, case): pass


def html_templating_dict(pod) -> dict:
    """Returns the dict of recognized substitutions to perform in html templating
    for *pod*.
    """
    template = pod.pod_env_vars.copy()
    d = {str(k): str(v) for k, v in template.items()}
    for attr in ('name', 'long_name', 'description', 'convention', 'realm'):
        d[attr] = str(pod.pod_settings.get(attr, ""))
        if not any(d[attr]):
            d[attr] = str(getattr(pod, attr, ""))
    d['driver'] = str(getattr(pod, 'driver', "")) # want the full path to the driver script
    if len(pod.multicase_dict['CASE_LIST']) > 1:  # multi-case PODs
        case_number = 1
        for case_name, case_dict in pod.multicase_dict['CASE_LIST'].items():
            case_str = f'CASE_{case_number}'
            d[case_str] = case_name
            case_number += 1
            for att_name, att in case_dict.items():
                d[att_name] = att
    else:  # single-case PODs
        for case_name, case_dict in pod.multicase_dict['CASE_LIST'].items():
            for att_name, att in case_dict.items():
                d[att_name] = att
    return d


class HTMLSourceFileMixin:
    """Convenience method to define location of html templates in one place.
    """

    @property
    def CASE_TEMP_HTML(self):
        """Path to temporary top-level html file for *case* that gets appended
        to as PODs finish.
        """
        return os.path.join(self.WORK_DIR, '_MDTF_pod_output_temp.html')

    def html_src_file(self, file_name):
        """Returns full path to a framework-supplied html template *file_name*
        or other part of the output page.
        """
        return os.path.join(self.CODE_ROOT, 'src', 'html', file_name)

    @staticmethod
    def pod_header_html_template_file_name(pod):
        """Name of the html template file to use for *pod*."""
        return pod.name + '.html'


    def pod_html(self, pod):
        """Path to *pod*'s html output file in the working directory."""
        return os.path.join(pod.paths.POD_WORK_DIR, self.pod_header_html_template_file_name(pod))

    def write_data_log_file(self):
        """Writes *.data.log file to output containing info on data files used.
        """
        log_file = io.open(
            os.path.join(self.WORK_DIR, self.obj.name+".data.log"),
            'w', encoding='utf-8'
        )
        if isinstance(self, HTMLPodOutputManager):
            str_1 = f"POD {self.obj.name}"
        elif isinstance(self, HTMLOutputManager):
            str_1 = ""
            for case_name in self.obj.multicase_dict['CASE_LIST'].keys():
                str_1 += f"case {case_name} \n"
        else:
            raise AssertionError("self is not an instance of HTMLPodOutputManager or HTMLOutputManager")

        log_file.write(f"# Input model data files used in this run of {str_1}:\n")
        assert hasattr(self.obj, '_in_file_log'), "could not find obj attribute _in_file_log"
        log_file.write(self.obj._in_file_log.buffer_contents())

        log_file.write(f"\n# Preprocessed files used as input to {str_1}:\n")
        log_file.write(("# (Depending on CLI flags, these will have been deleted "
                        "if the package exited successfully.)\n"))
        assert hasattr(self.obj, '_out_file_log'), "could not find obj attribute _out_file_log"
        log_file.write(self.obj._out_file_log.buffer_contents())
        log_file.close()


class HTMLPodOutputManager(HTMLSourceFileMixin):
    """Performs cleanup tasks specific to a single POD when that POD has
    finished running.
    """
    save_ps: bool = True
    save_nc: bool = True
    save_non_nc: bool = False
    CODE_ROOT: str = ""
    CODE_DIR: str = ""
    WORK_DIR: str = ""

    def __init__(self, pod, config, output_mgr):
        """Copy configuration info from :class:`~src.diagnostic.Diagnostic`
        object *pod*.

        Args:
            pod (:class:`~src.diagnostic.Diagnostic`): POD which generated the
                output files being processed.
            output_mgr: Parent OutputManager handling the overall processing of
                output files from all PODs.
        """
        try:
            self.save_ps = config.get('save_ps', True)
            self.save_nc = config.get('save_pp_data', True)
            self.save_non_nc = config.get('save_pp_data', False)
        except KeyError as exc:
            pod.deactivate(exc)
            raise
        self.CODE_ROOT = output_mgr.CODE_ROOT
        self.CODE_DIR = pod.paths.POD_CODE_DIR
        self.WORK_DIR = pod.paths.POD_WORK_DIR
        self.obj = pod

    def make_pod_html(self):
        """Perform templating on POD's html results page(s).

        Wraps :func:`~util.append_html_template`. Looks for all
        html files in ``$POD_CODE_DIR``, templates them, and copies them to
        ``$POD_WORK_DIR``, respecting subdirectory structure (see
        :func:`~util.recursive_copy`).
        """
        html_template_path = os.path.join(
            self.obj.paths.POD_CODE_DIR, self.pod_header_html_template_file_name(self.obj)
        )
        if not os.path.isfile(html_template_path):
            # POD's top-level html template needs to exist
            raise util.MDTFFileNotFoundError(html_template_path)

        template_d = html_templating_dict(self.obj)
        # copy and template all .html files, since PODs can make sub-pages
        source_files = util.find_files(self.CODE_DIR, '*.html')
        # optional html_plots_template_path for PODs that generate 1 plot for each case
        util.recursive_copy(
            source_files,
            self.CODE_DIR,
            self.WORK_DIR,
            copy_function=(
                lambda src, dest: util.append_html_template(
                    src, dest, template_dict=template_d, append=False
                )),
            overwrite=True
        )

    def convert_pod_figures(self, src_subdir: str, dest_subdir: str):
        """Convert all vector graphics in ``$POD_WORK_DIR/`` *src_subdir* to .png
        files using `ghostscript <https://www.ghostscript.com/>`__ (included in
        the _MDTF_base conda environment).

        All vector graphics files (identified by extension) in any subdirectory
        of ``$POD_WORK_DIR/`` *src_subdir* are converted to .png files by running
        ghostscript in a subprocess. Afterward, any bitmap files (identified by
        extension) in any subdirectory of ``$POD_WORK_DIR/`` *src_subdir* are
        moved to ``$POD_WORK_DIR/`` *dest_subdir*, preserving subdirectories (via
        :func:`~util.recursive_copy`.)

        Args:
            src_subdir: Subdirectory tree of ``$POD_WORK_DIR`` to search for vector
                graphics files.
            dest_subdir: Subdirectory tree of ``$POD_WOR_DIR`` to move converted
                bitmap files to.
        """
        # Flags to pass to ghostscript for PS -> PNG conversion (in particular
        # bitmap resolution.)
        eps_convert_flags = ("-dSAFER -dBATCH -dNOPAUSE -dEPSCrop -r150 "
                             "-sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4")

        abs_src_subdir = os.path.join(self.WORK_DIR, src_subdir)
        abs_dest_subdir = os.path.join(self.WORK_DIR, dest_subdir)

        files = util.find_files(
            abs_src_subdir,
            ['*.ps', '*.PS', '*.eps', '*.EPS', '*.pdf', '*.PDF']
        )
        for f in files:
            f_stem, _ = os.path.splitext(f)
            # Append "_MDTF_TEMP" + page number to output files ("%d" = ghostscript's
            # template for multi-page output). If input .ps/.pdf file has multiple
            # pages, this will generate 1 png per page, counting from 1.
            f_out = f_stem + '_MDTF_TEMP_%d.png'
            cmd = f'gs {eps_convert_flags} -sOutputFile="{f_out}" {f}'
            try:
                util.run_shell_command(cmd)
            except Exception as exc:
                self.obj.log.error("%s produced malformed plot: %s",
                                   self.obj.full_name, f[len(abs_src_subdir):])
                if isinstance(exc, util.MDTFCalledProcessError):
                    self.obj.log.debug(
                        "gs error encountered when converting %s for %s:\n%s",
                        self.obj.full_name, f[len(abs_src_subdir):],
                        getattr(exc, "output", "")
                    )
                continue
            # gs ran successfully; check how many files it created:
            out_files = glob.glob(f_stem + '_MDTF_TEMP_?.png')
            if not out_files:
                raise util.MDTFFileNotFoundError(f"No .png generated from {f}.")
            elif len(out_files) == 1:
                # got one .png, so remove suffix.
                os.rename(out_files[0], f_stem + '.png')
            else:
                # Multiple .pngs. Drop the MDTF_TEMP suffix and renumber starting
                # from zero (forget which POD requires this.)
                for n in range(len(out_files)):
                    os.rename(
                        f_stem + f'_MDTF_TEMP_{n+1}.png',
                        f_stem + f'-{n}.png'
                    )
        # move converted figures and any figures that were saved directly as bitmaps
        files = util.find_files(
            abs_src_subdir, ['*.png', '*.gif', '*.jpg', '*.jpeg']
        )
        util.recursive_copy(
            files, abs_src_subdir, abs_dest_subdir,
            copy_function=shutil.move, overwrite=True
        )

    def cleanup_pod_files(self):
        """Copy and remove remaining files to ``$POD_WORK_DIR``.

        In order, this 1) copies any bitmap figures in any subdirectory of
        ``$POD_OBS_DATA`` to ``$POD_WORK_DIR/obs`` (needed for legacy PODs without
        digested observational data), 2) removes vector graphics if requested,
        3) removes netCDF scratch files in ``$POD_WORK_DIR`` if requested.
        """
        # copy premade figures (if any) to output
        files = util.find_files(
            self.obj.paths.POD_OBS_DATA, ['*.gif', '*.png', '*.jpg', '*.jpeg']
        )
        for f in files:
            shutil.copy2(f, os.path.join(self.WORK_DIR, 'obs'))

        # remove .eps files if requested (actually, contents of any 'PS' subdirs)
        if not self.save_ps:
            for d in util.find_files(self.WORK_DIR, 'obs/PS'):
                shutil.rmtree(d)
            for d in util.find_files(self.WORK_DIR, 'model/PS'):
                shutil.rmtree(d)
        # delete all generated data
        # actually deletes contents of any 'netCDF' subdirs
        elif not self.save_nc:
            for d in util.find_files(self.WORK_DIR, 'model/netCDF'+os.sep):
                shutil.rmtree(d)
            for f in util.find_files(self.WORK_DIR, 'model/netCDF/*.nc'):
                os.remove(f)

    def cleanup_pp_data(self):
        """Removes nc files found in catalog if the ``save_pp_data`` data 
        is set to false.

        This is done by looping through the ``case_info.yml`` file found in each 
        POD. If the .nc file exists, it is then deleted.
        """
        if not self.save_nc:
            for f in util.find_files(self.WORK_DIR, 'case_info.yml'):
                case_info_yml = yaml.safe_load(open(f))
                for case in case_info_yml['CASE_LIST']:
                    for k in case_info_yml['CASE_LIST'][case]:
                        if k.endswith('FILE') or k.endswith('FILES'):
                            v = case_info_yml['CASE_LIST'][case][k]
                            if v != '' and os.path.exists(v) and v.endswith('.nc'):
                                os.remove(v)

    def make_output(self, config: util.NameSpace):
        """Top-level method to make POD-specific output, post-init. Split off
        into its own method to make subclassing easier.

        In order, this 1) creates the POD's html output page from its included
        template, replacing ``CASENAME`` and other template variables with their
        current values, and adds a link to the POD's page from the top-level html
        report; 2) converts the POD's output plots (in PS or EPS vector format)
        to a bitmap format for webpage display; 3) copies all requested files to
        the output directory and deletes temporary files.
        """
        self.write_data_log_file()
        if not self.obj.failed:
            self.make_pod_html()
            self.convert_pod_figures(os.path.join('model', 'PS'), 'model')
            self.convert_pod_figures(os.path.join('obs', 'PS'), 'obs')
            self.cleanup_pod_files()
            self.cleanup_pp_data()


class HTMLOutputManager(AbstractOutputManager,
                        HTMLSourceFileMixin):
    """OutputManager that collects the output of all PODs run in multirun mode
    as html pages.

    Instantiates :class:`HTMLPodOutputManager` objects to handle processing the
    output of each POD.
    """
    _PodOutputManagerClass = HTMLPodOutputManager
    _html_file_name = 'index.html'
    multi_case_figure: bool = False
    make_variab_tar: bool = False
    overwrite: bool = False
    file_overwrite: bool = False
    WORK_DIR: str = ""
    CODE_ROOT: str = ""
    OUT_DIR: str = ""

    def __init__(self, pod, config):
        try:
            if hasattr(config, 'make_variab_tar'):
                self.make_variab_tar = config['make_variab_tar']
            else:
                self.make_variab_tar = False
            if hasattr(config, 'overwrite'):
                self.overwrite = config['overwrite']
            else:
                self.overwrite = False
            self.file_overwrite = self.overwrite  # overwrite both config and .tar
            if config.get('make_multicase_figure_html', False):
                self.multi_case_figure = config['make_multicase_figure_html']
            else:
                self.multi_case_figure = False
        except KeyError as exc:
            self.log.exception("Caught %r", exc)

        self.CODE_ROOT = config.CODE_ROOT
        self.WORK_DIR = pod.paths.WORK_DIR
        self.OUT_DIR = pod.paths.OUTPUT_DIR
        self.obj = pod

    @property
    def _tarball_file_path(self) -> str:
        paths = self.obj.paths
        assert hasattr(self, 'WORK_DIR')
        file_name = self.WORK_DIR + '.tar'
        return os.path.join(paths.OUTPUT_DIR, file_name)

    def append_result_link(self, pod, config):
        """Update the top level index.html page with a link to *pod*'s results.

        This simply appends one of two html fragments to index.html:
        ``src/html/pod_result_snippet.html`` if the *pod* completed successfully,
        or ``src/html/pod_error_snippet.html`` if an exception was raised during
        *pod*'s setup or execution.
        """
        template_d = html_templating_dict(pod)
        # add a warning banner if needed
        assert(hasattr(pod, '_banner_log'))
        banner_str = pod._banner_log.buffer_contents()
        if banner_str:
            banner_str = banner_str.replace('\n', '<br>\n')
            src = self.html_src_file('warning_snippet.html')
            template_d['MDTF_WARNING_BANNER_TEXT'] = banner_str
            util.append_html_template(src, self.CASE_TEMP_HTML, template_d)

        # put in the link to results
        if pod.failed:
            # report error
            src = self.html_src_file('pod_error_snippet.html')
            # template_d['error_text'] = pod.format_log(children=True)
        else:
            # normal exit
            src = self.html_src_file('pod_result_snippet.html')
        util.append_html_template(src, self.CASE_TEMP_HTML, template_d)

    def make_output(self, pod, config: util.NameSpace):
        """Top-level method for doing all output activity post-init. Spun into a
        separate method to make subclassing easier.
        """
        # create empty text file for PODs to append to; equivalent of 'touch'
        open(self.CASE_TEMP_HTML, 'w').close()
        try:
            pod_output = self._PodOutputManagerClass(pod, config, self)
            pod_output.make_output(config)
            if not pod.failed:
                self.verify_pod_links(pod)
        except Exception as exc:
            pod.deactivate(exc)
        try:
            self.append_result_link(pod, config)  # problems here
        except Exception as exc:
            # won't go into the html output, but will be present in the
            # summary for the case
            pod.deactivate(exc)
        pod.close_log_file(log=True)
        if not pod.failed:
            pod.status = util.ObjectStatus.SUCCEEDED

        self.make_html(self._html_file_name)
        self.backup_config_files(config)
        self.write_data_log_file()
        if self.make_variab_tar:
            _ = self.make_tar_file()
        self.copy_to_output()
        if not self.obj.failed:
            self.obj.status = util.ObjectStatus.SUCCEEDED

    def generate_html_file_case_loop(self, case_info: dict, template_dict: dict, dest_file_handle: io.TextIOWrapper):
        """generate_html_file: append case figures to the POD html template

        Arguments: case_info (nested dict): dictionary with information for each case
                   template_dict (dict): dictionary with template environment variables
                   dest_file_handle (io.TextIOWrapper): Output html file io stream

        """

        case_template = "<TR><TD><TD><TD><TD style='width:100%' align=left>"\
                        "<A href={{PODNAME}}_model_plot_{{CASENAME}}.png>{{CASENAME}}\n</A>"
        for case_name, case_settings in case_info.items():
            case_settings['PODNAME'] = template_dict['PODNAME']
            case_settings['CASENAME'] = template_dict['CASENAME']
            output_template = util._DoubleBraceTemplate(case_template).safe_substitute(case_settings)
            dest_file_handle.write(output_template)

    def append_case_info_html(self, case_info: dict, dest_file_handle: io.TextIOWrapper):
        """append_case_info_html: append case figures to the POD html template

        Arguments: case_info (nested dict): dictionary with information for each case
                   dest_file_handle (io.TextIO): output html file io stream
        """

        case_settings_header_html_template = """<TABLE><TR><TD style='font-weight:bold'>Case Settings
        """

        dest_file_handle.write(case_settings_header_html_template)

        # write the settings per case. First header.
        # This prints the whole html_template = str(case_dict)

        case_settings_template = """
        <TR><TD align=left>{{CASENAME}}\n
        <TR><TD align=left>Date Range: {{startdate}} - {{enddate}}\n
        <TR><TD align=left>Data Convention: {{convention}}\n
        """

        for case_name, case_settings in case_info.items():
            output_template = util._DoubleBraceTemplate(case_settings_template).safe_substitute(case_settings)
            dest_file_handle.write(output_template)


    def make_html(self, html_file_name: str, cleanup=True):
        """Add header and footer to the temporary output file at CASE_TEMP_HTML.
        """
        append_header = True
        append_footer = True
        append_case_info = True
        dest = os.path.join(self.obj.paths.WORK_DIR, html_file_name)
        if os.path.isfile(dest):
            append_header = False
            append_footer = False
            append_case_info = False
        else:
            shutil.copy2(self.html_src_file('mdtf_diag_banner.png'), self.obj.paths.WORK_DIR)

        template_dict = self.obj.pod_env_vars.copy()
        template_dict['DATE_TIME'] = \
            datetime.datetime.now().strftime("%A, %d %B %Y %I:%M%p (UTC)")
        template_dict['PODNAME'] = self.obj.name
        template_dict['WORK_DIR'] = self.obj.paths.POD_WORK_DIR
        template_dict['OUTPUT_DIR'] = self.obj.paths.POD_OUTPUT_DIR
        main_log = util.find_files(self.WORK_DIR, "MDTF_main*log")
        assert os.path.isfile(main_log[0]), f"Could not find main log file in {self.WORK_DIR}"
        template_dict['MAIN_LOG'] = main_log[0]
        if append_header:
            util.append_html_template(
                self.html_src_file('mdtf_header.html'), dest, template_dict
            )
        with io.open(dest, 'a', encoding='utf-8') as f:
            if self.multi_case_figure:
                self.generate_html_file_case_loop(self.obj.multicase_dict['CASE_LIST'], template_dict, f)
            if append_case_info:
                self.append_case_info_html(self.obj.multicase_dict['CASE_LIST'], f)
        f.close()
        util.append_html_template(self.CASE_TEMP_HTML, dest, {})
        if append_footer:
            util.append_html_template(
                self.html_src_file('mdtf_footer.html'), dest, template_dict
            )
        if cleanup:
            os.remove(self.CASE_TEMP_HTML)

    def backup_config_files(self, config):
        """Record user input configuration in a file named ``config_save.json``
        for rerunning.
        """
        for config_tup in config._configs.values():
            if config_tup.backup_filename is None:
                continue
            out_file = os.path.join(self.WORK_DIR, config_tup.backup_filename)
            if not self.file_overwrite:
                out_file, _ = util.bump_version(out_file)
            elif os.path.exists(out_file):
                self.obj.log.info("%s: Overwriting '%s'.",
                                  self.obj.full_name, out_file)
            util.write_json(config_tup.contents, out_file, log=self.obj.log)

    def make_tar_file(self):
        """Make tar file of web/bitmap output.
        """
        out_path = self._tarball_file_path
        if not self.file_overwrite:
            out_path, _ = util.bump_version(out_path)
            self.obj.log.info("%s: Creating '%s'.", self.obj.full_name, out_path)
        elif os.path.exists(out_path):
            self.obj.log.info("%s: Overwriting '%s'.", self.obj.full_name, out_path)
        tar_flags = [f"--exclude=.{s}" for s in ('netCDF', 'nc', 'ps', 'PS', 'eps')]
        tar_flags = ' '.join(tar_flags)
        util.run_shell_command(
            [f'tar {tar_flags} -czf {out_path} -C {self.WORK_DIR} .']
        )
        return out_path

    def copy_to_output(self):
        """Copy all files to the user-specified output directory (``$OUTPUT_DIR``).
        """
        if self.WORK_DIR == self.OUT_DIR:
            return  # no copying needed
        self.obj.log.debug("%s: Copy '%s' to '%s'.", self.obj.full_name,
                           self.WORK_DIR, self.OUT_DIR)
        try:
            if os.path.exists(self.OUT_DIR):
                if self.overwrite:
                    # if overwrite flag is true, replace OUT_DIR contents with WORK_DIR
                    self.obj.log.error("%s: '%s' exists, overwriting.",
                                       self.obj.full_name, self.OUT_DIR)
                    shutil.rmtree(self.OUT_DIR)
                    shutil.move(self.WORK_DIR, self.OUT_DIR)
                    return
                elif not self.overwrite:
                    # if ovewrite flag is false, find the next suitable 'MDTF_output.v#' dir to write to
                    if not os.path.exists(os.path.join(self.OUT_DIR, 'index.html')):
                        # this will catch the majority of cases
                        shutil.rmtree(self.OUT_DIR)
                        shutil.move(self.WORK_DIR, self.OUT_DIR)
                        return
                    # the rest of this if statement is not strictly necessary, but may be useful for fringe edge cases
                    # if some reason a index.html already exists in self.OUT_DIR, it will move to the next .v#
                    out_main_dir = os.path.abspath(os.path.join(self.OUT_DIR, ".."))
                    v_dirs = [d for d in os.listdir(out_main_dir) if 'MDTF_output.v' in d]
                    if not v_dirs:
                        NEW_BASE = 'MDTF_output.v1'
                    v_nums = sorted([int(''.join(filter(str.isdigit, d))) for d in v_dirs], reverse=True)
                    NEW_BASE = f'MDTF_output.v{v_nums[0]+1}'
                    self.OUT_DIR = os.path.join(out_main_dir, NEW_BASE)
                    if os.path.isdir(self.OUT_DIR):
                        shutil.rmtree(self.OUT_DIR)
                    shutil.move(self.WORK_DIR, self.OUT_DIR)
                    return
        except Exception:
            raise

    def verify_pod_links(self, pod):
        """Check for missing files linked to from POD's html page.

        See documentation for :class:`~src.verify_links.LinkVerifier`. This method
        calls :class:`~src.verify_links.LinkVerifier` to check existence of all
        files linked to from the POD's own top-level html page (after templating).
        If any files are missing, an error message listing them is written to
        the run's ``index.html`` page (located in ``src/html/pod_missing_snippet.html``).
        """
        pod.log.info('Checking linked output files for %s.', pod.full_name)
        verifier = verify_links.LinkVerifier(
            self.pod_html(pod),  # root html file to start search at
            self.WORK_DIR,         # root directory to resolve relative paths
            verbose=False,
            log=pod.log
        )
        missing_out = verifier.verify_pod_links(pod.name)
        if missing_out:
            pod.deactivate(
                util.MDTFFileNotFoundError(f'Missing {len(missing_out)} files.')
            )
        else:
            pod.log.info('\tNo files are missing.')
