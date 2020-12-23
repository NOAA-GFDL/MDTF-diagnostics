import os
import abc
import datetime
import glob
import shutil
from src import util, core, verify_links

import logging
_log = logging.getLogger(__name__)

class AbstractOutputManager(abc.ABC):
    """Interface for any OutputManager."""
    def __init__(self, case): pass

def html_templating_dict(pod):
    """Get the dict of recognized substitutions to perform in HTML templates.
    """
    config = core.ConfigManager()
    template = config.global_env_vars.copy()
    template.update(pod.pod_env_vars)
    return {str(k): str(v) for k,v in template.items()}

class HTMLSourceFileMixin():
    """Convienience method to define location of HTML templates in one place.
    """
    @property
    def CASE_TEMP_HTML(self):
        """Temporary top-level html file for case that gets appended to as PODs
        finish.
        """
        return os.path.join(self.WK_DIR, '_MDTF_pod_output_temp.html')

    def html_src_file(self, file_name):
        """Get full path to a framework-supplied HTML template or other part of
        the output page.
        """
        return os.path.join(self.CODE_ROOT, 'src', 'html', file_name)

    @staticmethod
    def pod_html_template_file_name(pod):
        """Name of the POD's HTML template file."""
        return pod.name+'.html'

    def POD_HTML(self, pod):
        """Path to POD's HTML output file in the working directory."""
        return os.path.join(pod.POD_WK_DIR, self.pod_html_template_file_name(pod))

class HTMLPodOutputManager(HTMLSourceFileMixin):
    def __init__(self, pod, code_root, case_wk_dir):
        """Performs cleanup tasks when the POD has finished running.

        In order, this 1) creates the POD's HTML output page from its included
        template, replacing ``CASENAME`` and other template variables with their
        current values, and adds a link to the POD's page from the top-level HTML
        report; 2) converts the POD's output plots (in PS or EPS vector format) 
        to a bitmap format for webpage display; 3) Copies all requested files to
        the output directory and deletes temporary files.
        """
        config = core.ConfigManager()
        try:
            self.save_ps = config['save_ps']
            self.save_nc = config['save_nc']
            self.save_non_nc = config['save_non_nc']
        except KeyError as exc:
            _log.exception(f"Caught {repr(exc)}.")
            raise
        self.CODE_ROOT = code_root
        self.WK_DIR = case_wk_dir

        if pod.active:
            self.make_pod_html(pod)
            self.convert_pod_figures(pod, os.path.join('model', 'PS'), 'model')
            self.convert_pod_figures(pod, os.path.join('obs', 'PS'), 'obs')
            self.cleanup_pod_files(pod)

    def make_pod_html(self, pod):
        """Perform templating on POD's html results page(s).

        A wrapper for :func:`~util.append_html_template`. Looks for all 
        html files in POD_CODE_DIR, templates them, and copies them to 
        POD_WK_DIR, respecting subdirectory structure (see doc for
        :func:`~util.recursive_copy`).
        """
        test_path = os.path.join(
            pod.POD_CODE_DIR, self.pod_html_template_file_name(pod)
        )
        if not os.path.isfile(test_path):
            # POD's top-level HTML template needs to exist
            raise util.MDTFFileNotFoundError(test_path)
        template_d = html_templating_dict(pod)
        # copy and template all .html files, since PODs can make sub-pages
        source_files = util.find_files(pod.POD_CODE_DIR, '*.html')
        util.recursive_copy(
            source_files,
            pod.POD_CODE_DIR,
            pod.POD_WK_DIR,
            copy_function=(
                lambda src, dest: util.append_html_template(
                src, dest, template_dict=template_d, append=False
            )),
            overwrite=True
        )

    # Flags to pass to ghostscript PS -> PNG conversion in convert_pod_figures().
    _ghostscript_flags = ("-dSAFER -dBATCH -dNOPAUSE -dEPSCrop -r150 "
        "-sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4")

    def convert_pod_figures(self, pod, src_subdir, dest_subdir):
        """Convert all vector graphics in `POD_WK_DIR/subdir` to .png files using
        ghostscript.

        All vector graphics files (identified by extension) in any subdirectory 
        of `POD_WK_DIR/src_subdir` are converted to .png files by running 
        `ghostscript <https://www.ghostscript.com/>`__ in a subprocess.
        Ghostscript is included in the _MDTF_base conda environment. Afterwards,
        any bitmap files (identified by extension) in any subdirectory of
        `POD_WK_DIR/src_subdir` are moved to `POD_WK_DIR/dest_subdir`, preserving
        and subdirectories (see doc for :func:`~util.recursive_copy`.)

        Args:
            src_subdir: Subdirectory tree of `POD_WK_DIR` to search for vector
                graphics files.
            dest_subdir: Subdirectory tree of `POD_WK_DIR` to move converted 
                bitmap files to.
        """
        abs_src_subdir = os.path.join(pod.POD_WK_DIR, src_subdir)
        abs_dest_subdir = os.path.join(pod.POD_WK_DIR, dest_subdir)
        files = util.find_files(
            abs_src_subdir,
            ['*.ps', '*.PS', '*.eps', '*.EPS', '*.pdf', '*.PDF']
        )
        for f in files:
            f_stem, _  = os.path.splitext(f)
            gs_flags = self._ghostscript_flags
            # %d = ghostscript's template for multi-page output
            f_out = f_stem + '_MDTF_TEMP_%d.png' 
            util.run_shell_command(f'gs {gs_flags} -sOutputFile="{f_out}" {f}')
            # syntax for f_out above appends "_MDTF_TEMP" + page number to 
            # output files. If input .ps/.pdf file had multiple pages, this will
            # generate 1 png per page. Page numbering starts at 1. Now check 
            # how many files gs created:
            out_files = glob.glob(f_stem + '_MDTF_TEMP_?.png')
            if not out_files:
                raise OSError(f"Error: no png generated from {f}")
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
            copy_function=shutil.move, overwrite=False
        )

    def cleanup_pod_files(self, pod):
        """Copy and remove remaining files to `POD_WK_DIR`.

        In order, this 1) copies .pdf documentation (if any) from 
        `POD_CODE_DIR/doc`, 2) copies any bitmap figures in any subdirectory of
        `POD_OBS_DATA` to `POD_WK_DIR/obs` (needed for legacy PODs without 
        digested observational data), 3) removes vector graphics if requested,
        4) removes netCDF scratch files in `POD_WK_DIR` if requested.

        Settings are set at runtime, when :class:`~core.ConfigManager` is 
        initialized.
        """
        # copy PDF documentation (if any) to output
        files = util.find_files(os.path.join(pod.POD_CODE_DIR, 'doc'), '*.pdf')
        for f in files:
            shutil.copy2(f, pod.POD_WK_DIR)

        # copy premade figures (if any) to output 
        # NOTE this will not respect 
        files = util.find_files(
            pod.POD_OBS_DATA, ['*.gif', '*.png', '*.jpg', '*.jpeg']
        )
        for f in files:
            shutil.copy2(f, os.path.join(pod.POD_WK_DIR, 'obs'))

        # remove .eps files if requested (actually, contents of any 'PS' subdirs)
        if not self.save_ps:
            for d in util.find_files(pod.POD_WK_DIR, 'PS'+os.sep):
                shutil.rmtree(d)
        # delete netCDF files, keep everything else
        if self.save_non_nc:
            for f in util.find_files(pod.POD_WK_DIR, '*.nc'):
                os.remove(f)
        # delete all generated data
        # actually deletes contents of any 'netCDF' subdirs
        elif not self.save_nc:
            for d in util.find_files(pod.POD_WK_DIR, 'netCDF'+os.sep):
                shutil.rmtree(d)
            for f in util.find_files(pod.POD_WK_DIR, '*.nc'):
                os.remove(f)


class HTMLOutputManager(AbstractOutputManager, HTMLSourceFileMixin):
    """OutputManager that collects all the PODs' output as HTML pages.
    """
    _PodOutputManagerClass = HTMLPodOutputManager
    _html_file_name = 'index.html'
    _backup_config_file_name = 'config_save.json'

    def __init__(self, case):
        config = core.ConfigManager()
        try:
            self.make_variab_tar = config['make_variab_tar']
            self.dry_run = config['dry_run']
            self.overwrite = config['overwrite']
            self.file_overwrite = self.overwrite # overwrite both config and .tar
        except KeyError as exc:
            _log.exception(f"Caught {repr(exc)}.")
        self.CODE_ROOT = case.code_root
        self.WK_DIR = case.MODEL_WK_DIR       # abbreviate
        self.OUT_DIR = case.MODEL_OUT_DIR     # abbreviate

        # create empty text file for PODs to append to; equivalent of 'touch'
        open(self.CASE_TEMP_HTML, 'w').close()
        for pod in case.pods.values():
            try:
                self._PodOutputManagerClass(pod, self.CODE_ROOT, self.WK_DIR)
            except Exception as exc:
                # won't go into the HTML output, but will be present in the 
                # summary for the case
                _log.exception(f"Caught {repr(exc)}.")
                pod.exceptions.log(exc)
                continue
        for pod in case.pods.values():
            try:
                self.append_result_link(pod)
                if pod.active:
                    self.verify_pod_links(pod)
            except Exception as exc:
                # won't go into the HTML output, but will be present in the 
                # summary for the case
                _log.exception(f"Caught {repr(exc)}.")
                pod.exceptions.log(exc)
                continue

        self.make_html(case)
        self.backup_config_file(case)
        if self.make_variab_tar:
            _ = self.make_tar_file(case)
        self.copy_to_output(case)

    @property
    def _tarball_file_path(self):
        paths = core.PathManager()
        assert hasattr(self, 'WK_DIR')
        file_name = self.WK_DIR + '.tar'
        return os.path.join(paths.OUTPUT_DIR, file_name)

    def append_result_link(self, pod):
        """Update the top level index.html page with a link to this POD's results.

        This simply appends one of two html fragments to index.html: 
        pod_result_snippet.html if the POD completed successfully, or
        pod_error_snippet.html if an exception was raised during the POD's setup
        or execution.
        """
        template_d = html_templating_dict(pod)
        if pod.failed:
            # report error
            src = self.html_src_file('pod_error_snippet.html')
            template_d['error_text'] = pod.exceptions.format()
        else:
            # normal exit
            src = self.html_src_file('pod_result_snippet.html')
        util.append_html_template(src, self.CASE_TEMP_HTML, template_d)

    def verify_pod_links(self, pod):
        """Check for missing files linked to from POD's html page.

        See documentation for :class:`~verify_links.LinkVerifier`. This method
        calls LinkVerifier to check existence of all files linked to from the 
        POD's own top-level html page (after templating). If any files are
        missing, an error message listing them is written to the run's index.html 
        (located in src/html/pod_missing_snippet.html).
        """
        _log.info('Checking linked output files for %s', pod.name)
        verifier = verify_links.LinkVerifier(
            self.POD_HTML(pod),  # root HTML file to start search at
            self.WK_DIR,         # root directory to resolve relative paths
            verbose=False
        )
        missing_out = verifier.verify_pod_links(pod.name)
        if missing_out:
            _log.error('POD %s has missing output files.', pod.name)
            template_d = html_templating_dict(pod)
            template_d['missing_output'] = '<br>'.join(missing_out)
            util.append_html_template(
                self.html_src_file('pod_missing_snippet.html'),
                self.CASE_TEMP_HTML, 
                template_d
            )
            pod.exceptions.log(FileNotFoundError(f'Missing {len(missing_out)} files.'))
        else:
            _log.info('\tNo files are missing.')

    def make_html(self, case, cleanup=True):
        """Add header and footer to CASE_TEMP_HTML.
        """
        dest = os.path.join(self.WK_DIR, self._html_file_name)
        if os.path.isfile(dest):
            _log.warning("%s: %s exists, deleting.", 
                self._html_file_name, case.name)
            os.remove(dest)

        template_dict = case.env_vars.copy()
        template_dict['DATE_TIME'] = \
            datetime.datetime.utcnow().strftime("%A, %d %B %Y %I:%M%p (UTC)")
        util.append_html_template(
            self.html_src_file('mdtf_header.html'), dest, template_dict
        )
        util.append_html_template(self.CASE_TEMP_HTML, dest, {})
        util.append_html_template(
            self.html_src_file('mdtf_footer.html'), dest, template_dict
        )
        if cleanup:
            os.remove(self.CASE_TEMP_HTML)
        shutil.copy2(self.html_src_file('mdtf_diag_banner.png'), self.WK_DIR)

    def backup_config_file(self, case):
        """Record settings in file config_save.json for rerunning.
        """
        config = core.ConfigManager()
        out_file = os.path.join(self.WK_DIR, self._backup_config_file_name)
        if not self.file_overwrite:
            out_file, _ = util.bump_version(out_file)
        elif os.path.exists(out_file):
            _log.info("%s: Overwriting %s.", case.name, out_file)
        util.write_json(config.backup_config, out_file)

    def make_tar_file(self, case):
        """Make tar file of web/bitmap output.
        """
        out_path = self._tarball_file_path
        if not self.file_overwrite:
            out_path, _ = util.bump_version(out_path)
            _log.info("%s: Creating %s.", case.name, out_path)
        elif os.path.exists(out_path):
            _log.info("%s: Overwriting %s.", case.name, out_path)
        tar_flags = [f"--exclude=.{s}" for s in ('netCDF','nc','ps','PS','eps')]
        tar_flags = ' '.join(tar_flags)
        util.run_shell_command(
            f'tar {tar_flags} -czf {out_path} -C {self.WK_DIR} .',
            dry_run = self.dry_run
        )
        return out_path

    def copy_to_output(self, case):
        """Copy all files to the specified output directory.
        """
        if self.WK_DIR == self.OUT_DIR:
            return # no copying needed
        _log.debug("%s: Copy %s to %s.", 
            case.name, self.WK_DIR, self.OUT_DIR)
        try:
            if os.path.exists(self.OUT_DIR):
                if not self.overwrite:
                    _log.error("%s: %s exists, overwriting.", 
                        case.name, self.OUT_DIR)
                shutil.rmtree(self.OUT_DIR)
        except Exception:
            raise
        shutil.move(self.WK_DIR, self.OUT_DIR)
