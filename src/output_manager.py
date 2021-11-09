"""Implementation of the OutputManager plugin, which templates HTML and organizes
the PODs' output files.
"""
import os
import abc
import datetime
import glob
import io
import shutil
from src import util, core, verify_links

import logging
_log = logging.getLogger(__name__)

class AbstractOutputManager(abc.ABC):
    """Abstract interface for any OutputManager."""
    def __init__(self, case): pass

def html_templating_dict(pod):
    """Returns the dict of recognized substitutions to perform in HTML templating.
    """
    config = core.ConfigManager()
    template = config.global_env_vars.copy()
    template.update(pod.pod_env_vars)
    d = {str(k): str(v) for k,v in template.items()}
    for attr in ('name', 'long_name', 'description', 'convention', 'realm'):
        d[attr] = str(getattr(pod, attr, ""))
    return d

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
        """Returns full path to a framework-supplied HTML template *file_name*
        or other part of the output page.
        """
        return os.path.join(self.CODE_ROOT, 'src', 'html', file_name)

    @staticmethod
    def pod_html_template_file_name(pod):
        """Name of the HTML template file for POD *pod*."""
        return pod.name+'.html'

    def POD_HTML(self, pod):
        """Path to *pod*\'s HTML output file in the working directory."""
        return os.path.join(pod.POD_WK_DIR, self.pod_html_template_file_name(pod))

    def write_data_log_file(self):
        """Writes \*.data.log file to output containing info on data files used.
        """
        log_file = io.open(
            os.path.join(self.WK_DIR, self.obj.name+".data.log"),
            'w', encoding='utf-8'
        )
        if isinstance(self, HTMLPodOutputManager):
            str_1 = f"POD {self.obj.name}"
            str_2 = 'this POD'
        elif isinstance(self, HTMLOutputManager):
            str_1 = f"case {self.obj.name}"
            str_2 = 'PODs'
        else:
            raise AssertionError

        log_file.write(f"# Input model data files used in this run of {str_1}:\n")
        assert hasattr(self.obj, '_in_file_log')
        log_file.write(self.obj._in_file_log.buffer_contents())

        log_file.write(f"\n# Preprocessed files used as input to {str_2}:\n")
        log_file.write(("# (Depending on CLI flags, these will have been deleted "
            "if the package exited successfully.)\n"))
        assert hasattr(self.obj, '_out_file_log')
        log_file.write(self.obj._out_file_log.buffer_contents())
        log_file.close()

class HTMLPodOutputManager(HTMLSourceFileMixin):
    """Performs cleanup tasks when the POD has finished running.
    """
    def __init__(self, pod, output_mgr):
        """Copy configuration info from POD object.

        Args:
            pod (:class:`~src.diagnostic.Diagnostic): POD which generated the
                output files being processed.
            output_mgr: OutputManager plugin handling the overall processing of
                output files from all PODs.
        """
        config = core.ConfigManager()
        try:
            self.save_ps = config['save_ps']
            self.save_nc = config['save_nc']
            self.save_non_nc = config['save_non_nc']
        except KeyError as exc:
            pod.deactivate(exc)
            raise
        self.CODE_ROOT = output_mgr.CODE_ROOT
        self.CODE_DIR = pod.POD_CODE_DIR
        self.WK_DIR = pod.POD_WK_DIR
        self.obj = pod

    def make_pod_html(self):
        """Perform templating on POD's html results page(s).

        Wraps :func:`~util.append_html_template`. Looks for all
        html files in ``$POD_CODE_DIR``, templates them, and copies them to
        ``$POD_WK_DIR``, respecting subdirectory structure (see
        :func:`~util.recursive_copy`).
        """
        test_path = os.path.join(
            self.obj.POD_CODE_DIR, self.pod_html_template_file_name(self.obj)
        )
        if not os.path.isfile(test_path):
            # POD's top-level HTML template needs to exist
            raise util.MDTFFileNotFoundError(test_path)
        template_d = html_templating_dict(self.obj)
        # copy and template all .html files, since PODs can make sub-pages
        source_files = util.find_files(self.CODE_DIR, '*.html')
        util.recursive_copy(
            source_files,
            self.CODE_DIR,
            self.WK_DIR,
            copy_function=(
                lambda src, dest: util.append_html_template(
                src, dest, template_dict=template_d, append=False
            )),
            overwrite=True
        )

    def convert_pod_figures(self, src_subdir, dest_subdir):
        """Convert all vector graphics in ``$POD_WK_DIR/`` *src\_subdir* to .png
        files using `ghostscript <https://www.ghostscript.com/>`__ (included in
        the \_MDTF\_base conda environment).

        All vector graphics files (identified by extension) in any subdirectory
        of ``$POD_WK_DIR/`` *src\_subdir* are converted to .png files by running
        ghostscript in a subprocess. Afterwards, any bitmap files (identified by
        extension) in any subdirectory of ``$POD_WK_DIR/`` *src\_subdir* are
        moved to ``$POD_WK_DIR/`` *dest\_subdir*, preserving subdirectories (via
        :func:`~util.recursive_copy`.)

        Args:
            src_subdir: Subdirectory tree of ``$POD_WK_DIR`` to search for vector
                graphics files.
            dest_subdir: Subdirectory tree of ``$POD_WK_DIR`` to move converted
                bitmap files to.
        """
        # Flags to pass to ghostscript for PS -> PNG conversion (in particular
        # bitmap resolution.)
        eps_convert_flags = ("-dSAFER -dBATCH -dNOPAUSE -dEPSCrop -r150 "
        "-sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4")

        abs_src_subdir = os.path.join(self.WK_DIR, src_subdir)
        abs_dest_subdir = os.path.join(self.WK_DIR, dest_subdir)
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
            try:
                util.run_shell_command(
                    f'gs {eps_convert_flags} -sOutputFile="{f_out}" {f}'
                )
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
            copy_function=shutil.move, overwrite=False
        )

    def cleanup_pod_files(self):
        """Copy and remove remaining files to ``$POD_WK_DIR``.

        In order, this 1) copies any bitmap figures in any subdirectory of
        ``$POD_OBS_DATA`` to ``$POD_WK_DIR/obs`` (needed for legacy PODs without
        digested observational data), 2) removes vector graphics if requested,
        3) removes netCDF scratch files in ``$POD_WK_DIR`` if requested.

        Settings are set at runtime, when :class:`~core.ConfigManager` is
        initialized.
        """
        # copy premade figures (if any) to output
        files = util.find_files(
            self.obj.POD_OBS_DATA, ['*.gif', '*.png', '*.jpg', '*.jpeg']
        )
        for f in files:
            shutil.copy2(f, os.path.join(self.WK_DIR, 'obs'))

        # remove .eps files if requested (actually, contents of any 'PS' subdirs)
        if not self.save_ps:
            for d in util.find_files(self.WK_DIR, 'PS'+os.sep):
                shutil.rmtree(d)
        # delete netCDF files, keep everything else
        if self.save_non_nc:
            for f in util.find_files(self.WK_DIR, '*.nc'):
                os.remove(f)
        # delete all generated data
        # actually deletes contents of any 'netCDF' subdirs
        elif not self.save_nc:
            for d in util.find_files(self.WK_DIR, 'netCDF'+os.sep):
                shutil.rmtree(d)
            for f in util.find_files(self.WK_DIR, '*.nc'):
                os.remove(f)

    def make_output(self):
        """Top-level method to make POD-specific output, post-init. Split off
        into its own method to make subclassing easier.

        In order, this 1) creates the POD's HTML output page from its included
        template, replacing ``CASENAME`` and other template variables with their
        current values, and adds a link to the POD's page from the top-level HTML
        report; 2) converts the POD's output plots (in PS or EPS vector format)
        to a bitmap format for webpage display; 3) Copies all requested files to
        the output directory and deletes temporary files.
        """
        self.write_data_log_file()
        if not self.obj.failed:
            self.make_pod_html()
            self.convert_pod_figures(os.path.join('model', 'PS'), 'model')
            self.convert_pod_figures(os.path.join('obs', 'PS'), 'obs')
            self.cleanup_pod_files()

class HTMLOutputManager(AbstractOutputManager, HTMLSourceFileMixin):
    """OutputManager that collects all the PODs' output as HTML pages. Currently
    the only value for the OutputManager plugin, selected by default.

    Instantiates :class:`HTMLPodOutputManager` objects to handle output of
    each POD.
    """
    _PodOutputManagerClass = HTMLPodOutputManager
    _html_file_name = 'index.html'

    def __init__(self, case):
        config = core.ConfigManager()
        try:
            self.make_variab_tar = config['make_variab_tar']
            self.dry_run = config['dry_run']
            self.overwrite = config['overwrite']
            self.file_overwrite = self.overwrite # overwrite both config and .tar
        except KeyError as exc:
            case.log.exception("Caught %r", exc)
        self.CODE_ROOT = case.code_root
        self.WK_DIR = case.MODEL_WK_DIR       # abbreviate
        self.OUT_DIR = case.MODEL_OUT_DIR     # abbreviate
        self.obj = case

    @property
    def _tarball_file_path(self):
        paths = core.PathManager()
        assert hasattr(self, 'WK_DIR')
        file_name = self.WK_DIR + '.tar'
        return os.path.join(paths.OUTPUT_DIR, file_name)

    def append_result_link(self, pod):
        """Update the top level index.html page with a link to this POD's results.

        This simply appends one of two html fragments to index.html:
        ``src/html/pod_result_snippet.html`` if the POD completed successfully,
        or ``src/html/pod_error_snippet.html`` if an exception was raised during
        the POD's setup or execution.
        """
        template_d = html_templating_dict(pod)
        # add a warning banner if needed
        assert hasattr(pod, '_banner_log')
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
            self.POD_HTML(pod),  # root HTML file to start search at
            self.WK_DIR,         # root directory to resolve relative paths
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

    def make_html(self, cleanup=True):
        """Add header and footer to CASE_TEMP_HTML.
        """
        dest = os.path.join(self.WK_DIR, self._html_file_name)
        if os.path.isfile(dest):
            self.obj.log.warning("%s: '%s' exists, deleting.",
                self._html_file_name, self.obj.name)
            os.remove(dest)

        template_dict = self.obj.env_vars.copy()
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

    def backup_config_files(self):
        """Record user input configuration in a file named ``config_save.json``
        for rerunning.
        """
        config = core.ConfigManager()
        for config_tup in config._configs.values():
            if config_tup.backup_filename is None:
                continue
            out_file = os.path.join(self.WK_DIR, config_tup.backup_filename)
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
        tar_flags = [f"--exclude=.{s}" for s in ('netCDF','nc','ps','PS','eps')]
        tar_flags = ' '.join(tar_flags)
        util.run_shell_command(
            f'tar {tar_flags} -czf {out_path} -C {self.WK_DIR} .',
            dry_run = self.dry_run
        )
        return out_path

    def copy_to_output(self):
        """Copy all files to the specified output directory.
        """
        if self.WK_DIR == self.OUT_DIR:
            return # no copying needed
        self.obj.log.debug("%s: Copy '%s' to '%s'.", self.obj.full_name,
            self.WK_DIR, self.OUT_DIR)
        try:
            if os.path.exists(self.OUT_DIR):
                if not self.overwrite:
                    self.obj.log.error("%s: '%s' exists, overwriting.",
                        self.obj.full_name, self.OUT_DIR)
                shutil.rmtree(self.OUT_DIR)
        except Exception:
            raise
        shutil.move(self.WK_DIR, self.OUT_DIR)

    def make_output(self):
        """Top-level method for doing all output activity post-init. Spun into a
        separate method to make subclassing easier.
        """
        # create empty text file for PODs to append to; equivalent of 'touch'
        open(self.CASE_TEMP_HTML, 'w').close()
        for pod in self.obj.iter_children():
            try:
                pod_output = self._PodOutputManagerClass(pod, self)
                pod_output.make_output()
                if not pod.failed:
                    self.verify_pod_links(pod)
            except Exception as exc:
                pod.deactivate(exc)
                continue
        for pod in self.obj.iter_children():
            try:
                self.append_result_link(pod)
            except Exception as exc:
                # won't go into the HTML output, but will be present in the
                # summary for the case
                pod.deactivate(exc)
                continue
            pod.close_log_file(log=True)
            if not pod.failed:
                pod.status = core.ObjectStatus.SUCCEEDED

        self.make_html()
        self.backup_config_files()
        self.write_data_log_file()
        if self.make_variab_tar:
            _ = self.make_tar_file()
        self.copy_to_output()
        if not self.obj.failed \
            and not any(p.failed for p in self.obj.iter_children()):
            self.obj.status = core.ObjectStatus.SUCCEEDED

