"""Code specific to the computing environment at NOAA's Geophysical Fluid 
Dynamics Laboratory (Princeton, NJ, USA).
"""
import os
import io
import abc
import collections
import operator as op
import re
import shutil
import subprocess
import typing
from src import datelabel, util, util_mdtf, cmip6, diagnostic, data_manager
from src import gfdl_util
import src.conflict_resolution as choose
from src.environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager

class GfdlDiagnostic(diagnostic.Diagnostic):
    """Wrapper for Diagnostic that adds writing a placeholder directory to the
    output as a lockfile if we're running in frepp cooperative mode.
    """
    _has_placeholder: bool = False
    _already_made_POD_OUT_DIR: bool = False

    def pre_run_setup(self):
        """Extra step needed for POD-specific output directory, which may be on
        a remote filesystem.
        """
        config = gfdl_util.GFDLConfigManager()

        super(GfdlDiagnostic, self).pre_run_setup()
        if self._already_made_POD_OUT_DIR:
            return
        try:
            gfdl_util.make_remote_dir(
                self.POD_OUT_DIR,
                timeout=config.get('file_transfer_timeout', 0),
                dry_run=config.get('dry_run', False)
            )
            self._has_placeholder = True
            self._already_made_POD_OUT_DIR = True
        except Exception as exc:
            try:
                raise diagnostic.PodRuntimeError(self, (f"Caught exception "
                    f"making output directory at {self.POD_OUT_DIR}.")) from exc
            except Exception as chained_exc:
                self.exceptions.log(chained_exc)    

    def tear_down(self, verbose=0):
        # only run teardown (including logging error on index.html) if POD ran
        if self._has_placeholder:
            super(GfdlDiagnostic, self).tear_down(verbose)

class GfdlvirtualenvEnvironmentManager(VirtualenvEnvironmentManager):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self):
        _ = gfdl_util.ModuleManager()
        super(GfdlvirtualenvEnvironmentManager, self).__init__()

    # manual-coded logic like this is not scalable
    def set_pod_env(self, pod):
        langs = [s.lower() for s in pod.runtime_requirements]
        if pod.name == 'convective_transition_diag':
            pod.env = 'py_convective_transition_diag'
        elif pod.name == 'MJO_suite':
            pod.env = 'ncl_MJO_suite'
        elif ('r' in langs) or ('rscript' in langs):
            pod.env = 'r_default'
        elif 'ncl' in langs:
            pod.env = 'ncl'
        else:
            pod.env = 'py_default'

    # this is totally not scalable
    _module_lookup = {
        'ncl': ['ncl'],
        'r_default': ['r'],
        'py_default': ['python'],
        'py_convective_transition_diag': ['python', 'ncl'],
        'ncl_MJO_suite': ['python', 'ncl']
    }

    def create_environment(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        modMgr.load(self._module_lookup[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_commands(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        mod_list = modMgr.load_commands(self._module_lookup[env_name])
        return ['source $MODULESHOME/init/bash'] \
            + mod_list \
            + super(GfdlvirtualenvEnvironmentManager, self).activate_env_commands(env_name)

    def deactivate_env_commands(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        mod_list = modMgr.unload_commands(self._module_lookup[env_name])
        return super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_commands(env_name) + mod_list

    def tear_down(self):
        super(GfdlvirtualenvEnvironmentManager, self).tear_down()
        modMgr = gfdl_util.ModuleManager()
        modMgr.revert_state()

class GfdlcondaEnvironmentManager(CondaEnvironmentManager):
    # Use mdteam's anaconda2
    def _call_conda_create(self, env_name):
        raise Exception(("Trying to create conda env {} "
            "in read-only mdteam account.").format(env_name)
        )


def GfdlautoDataManager(case_dict, pod_dict, PreprocessorClass):
    """Wrapper for dispatching DataManager based on inputs.
    """
    test_root = case_dict.get('CASE_ROOT_DIR', None)
    if not test_root:
        return Gfdludacmip6DataManager(case_dict, pod_dict, PreprocessorClass)
    test_root = os.path.normpath(test_root)
    if 'pp' in os.path.basename(test_root):
        return GfdlppDataManager(case_dict, pod_dict, PreprocessorClass)
    else:
        print(("ERROR: Couldn't determine data fetch method from input."
            "Please set '--data_manager GFDL_pp', 'GFDL_UDA_CMP6', or "
            "'GFDL_data_cmip6', depending on the source you want."))
        exit()


class GfdlarchiveDataManager(data_manager.DataManager, metaclass=abc.ABCMeta):
    def __init__(self, case_dict, pod_dict, PreprocessorClass):
        # load required modules
        modMgr = gfdl_util.ModuleManager()
        modMgr.load('gcp') # should refactor

        config = util_mdtf.ConfigManager()
        super(GfdlarchiveDataManager, self).__init__(case_dict, pod_dict, PreprocessorClass)

        assert ('CASE_ROOT_DIR' in case_dict)
        if not os.path.isdir(case_dict['CASE_ROOT_DIR']):
            raise data_manager.DataAccessError(None, 
                f"Can't access CASE_ROOT_DIR = '{case_dict['CASE_ROOT_DIR']}'.")
        self.data_root_dir = case_dict['CASE_ROOT_DIR']
        self.tape_filesystem = gfdl_util.is_on_tape_filesystem(self.data_root_dir)
        self._catalog = collections.defaultdict(
            lambda: collections.defaultdict(list)
        )

        self.frepp_mode = config.get('frepp', False)
        if self.frepp_mode:
            self.overwrite = True
            # flag to not overwrite config and .tar: want overwrite for frepp
            self.file_overwrite = True
            # if overwrite=False, WK_DIR & OUT_DIR will have been set to a 
            # unique name in parent's init. Set it back so it will be overwritten.
            d = paths.modelPaths(self, overwrite=True)
            self.MODEL_WK_DIR = d.MODEL_WK_DIR
            self.MODEL_OUT_DIR = d.MODEL_OUT_DIR

    _DataKeyClass = data_manager.DefaultDataKey
    _UndeterminedKeyClass = None

    def dataset_key(self, varlist_entry):
        return self._DataKeyClass.from_dataset(varlist_entry, self)

    # DATA QUERY -------------------------------------

    @abc.abstractmethod
    def parse_relative_path(self, subdir, filename):
        pass

    def _listdir(self, dir_):
        # print("\t\tDEBUG: listdir on ...{}".format(dir_[len(self.data_root_dir):]))
        return os.listdir(dir_)

    def list_filtered_subdirs(self, dirs_in, subdir_filter=None):
        subdir_filter = util.coerce_to_iter(subdir_filter)
        found_dirs = []
        for dir_ in dirs_in:
            found_subdirs = {d for d \
                in self._listdir(os.path.join(self.data_root_dir, dir_)) \
                if not (d.startswith('.') or d.endswith('.nc'))
            }
            if subdir_filter:
                found_subdirs = found_subdirs.intersection(subdir_filter)
            if not found_subdirs:
                print("\tCouldn't find subdirs (in {}) at {}, skipping".format(
                    subdir_filter, os.path.join(self.data_root_dir, dir_)
                ))
                continue
            found_dirs.extend([
                os.path.join(dir_, subdir_) for subdir_ in found_subdirs \
                if os.path.isdir(os.path.join(self.data_root_dir, dir_, subdir_))
            ])
        return found_dirs

    @abc.abstractmethod
    def subdirectory_filters(self):
        pass

    def pre_query_and_fetch_hook(self):
        """Build data catalog on the fly from crawling directory tree.
        """
        # match files ending in .nc only if they aren't of the form .tile#.nc
        # (negative lookback) 
        regex_no_tiles = re.compile(r".*(?<!\.tile\d)\.nc$")

        # generate data_keys for all files we might search for; will be wiped out
        # when build_data_dicts() is called
        for pod in self.iter_pods():
            for var in pod.iter_vars(all_vars=True):
                key = self.dataset_key(var)
                self.data_keys[key].append(var)

        print("keys dump:")
        for k1,v1 in self.data_keys.items():
            print(k1, len(v1))
            if k1.name_in_model == 'rlut':
                print('\t', repr(k1))

        # crawl directory tree rooted at self.data_root_dir
        pathlist = ['']
        for filter_ in self.subdirectory_filters():
            pathlist = self.list_filtered_subdirs(pathlist, filter_)
        for dir_ in pathlist:
            dir_contents = self._listdir(os.path.join(self.data_root_dir, dir_))
            dir_contents = list(filter(regex_no_tiles.search, dir_contents))
            files = [] # list of FileDataSets corresponding to files in this dir
            file_keys = collections.defaultdict(list) # DataKeys of those files
            for f in dir_contents:
                try:
                    files.append(self.parse_relative_path(dir_, f))
                except ValueError as exc:
                    # print('\tDEBUG:', exc)
                    #print('\t\tDEBUG: ', exc, '\n\t\t', os.path.join(self.data_root_dir, dir_), f)
                    continue
            for file_ds in files:
                data_key = self.dataset_key(file_ds)
                if data_key.name_in_model == 'rlut':
                    print('\t', repr(data_key))
                file_keys[data_key].append(file_ds)

                
            for data_key in self.data_keys:
                # in case data is chunked, only add files to _catalog if the
                # date_range can be spanned with files we've found in this dir_.
                # If yes, insert the list of files under a d_key with date_range

                if data_key not in file_keys:
                    continue
                files = file_keys[data_key]
                try:
                    # method throws ValueError if ranges aren't contiguous
                    files_date_range = datelabel.DateRange.from_contiguous_span(
                        *[f.date_range for f in files]
                    )
                except ValueError:
                    # Date range of remote files doesn't contain analysis range or 
                    # is noncontiguous; should probably log an error
                    continue
                if not files_date_range.contains(self.attrs.date_range):
                    # files we found don't span the query date range
                    continue
                for file_ds in files:
                    if file_ds.date_range in self.attrs.date_range:
                        d_key = file_ds.to_dataclass(self._DataKeyClass)
                        u_key = file_ds.to_dataclass(self._UndeterminedKeyClass)
                        self._catalog[d_key][u_key].append(file_ds)

        print("catalog dump:")
        for k1,v1 in self._catalog.items():
            print(k1, len(v1.keys()))

    def query_dataset(self, data_key):
        if data_key in self._catalog:
            return list(self._catalog[data_key].values())
        else:
            return None

    # FETCH REMOTE DATA -------------------------------------

    # specific details that must be implemented in child class 
    @abc.abstractmethod
    def select_undetermined(self):
        pass

    def pre_fetch_hook(self):
        """Make assignments to u_keys, or fail. Issue dmget for selected files.
        """
        d_to_u_dict = self.select_undetermined()
        for d_key in self.data_keys:
            u_key = d_to_u_dict[d_key]
            print(f"\tSelected {u_key} for {d_key}")
            # check we didn't eliminate everything:
            if not self._catalog[d_key][u_key]:
                raise data_manager.DataAccessError(
                    f'Choosing {d_key}, {u_key} eliminated all files.')
            self.data_files[d_key] = self._catalog[d_key][u_key]

        paths = set()
        for data_key in self.data_keys:
            paths.update([f.remote_path for f in self.data_files[data_key]])
        if self.tape_filesystem:
            print(f"start dmget of {len(paths)} files")
            util.run_command(['dmget','-t','-v'] + list(paths),
                timeout= len(paths) * self.file_transfer_timeout,
                dry_run=self.dry_run
            ) 
            print("end dmget")

    def determine_fetch_method(self, method='auto'):
        _methods = {
            'gcp': {'command': ['gcp', '--sync', '-v', '-cd'], 'site':'gfdl:'},
            'cp':  {'command': ['cp'], 'site':''},
            'ln':  {'command': ['ln', '-fs'], 'site':''}
        }
        if method not in _methods:
            if self.tape_filesystem:
                method = 'gcp' # use GCP for DMF filesystems
            else:
                method = 'ln' # symlink for local files
        return (_methods[method]['command'], _methods[method]['site'])

    def fetch_dataset(self, d_key, method='auto'):
        """Copy files to temporary directory.
        (GCP can't copy to home dir, so always copy to a temp dir)
        """
        tmpdirs = util_mdtf.TempDirManager()
        tmpdir = tmpdirs.make_tempdir(hash_obj = d_key)
        (cp_command, smartsite) = self.determine_fetch_method(method)
        # copy remote files
        # TODO: Do something intelligent with logging, caught OSErrors
        new_files = [] # file objects are immutable, must replace them
        for file_ds in self.data_files[d_key]:
            path = file_ds.remote_path
            local_path = os.path.join(tmpdir, os.path.basename(path))
            print("\tcopying ...{} to {}".format(
                path[len(self.data_root_dir):], tmpdir
            ))
            util.run_command(cp_command + [
                smartsite + path, 
                # gcp requires trailing slash, ln ignores it
                smartsite + tmpdir + os.sep
            ], 
                timeout=self.file_transfer_timeout, 
                dry_run=self.dry_run
            )
            new_files.append(file_ds.replace(local_path=local_path))
        self.data_files[d_key] = new_files

    # HTML & PLOT OUTPUT -------------------------------------

    def _make_html(self, cleanup=False):
        # never cleanup html if we're in frepp_mode, since framework may run 
        # later when another component finishes. Instead just append current
        # progress to TEMP_HTML.
        prev_html = os.path.join(self.MODEL_OUT_DIR, 'index.html')
        if self.frepp_mode and os.path.exists(prev_html):
            print("\tDEBUG: Appending previous index.html at {}".format(prev_html))
            with io.open(prev_html, 'r', encoding='utf-8') as f1:
                contents = f1.read()
            contents = contents.split('<!--CUT-->')
            assert len(contents) == 3
            contents = contents[1]

            if os.path.exists(self.TEMP_HTML):
                mode = 'a'
            else:
                print("\tWARNING: No file at {}.".format(self.TEMP_HTML))
                mode = 'w'
            with io.open(self.TEMP_HTML, mode, encoding='utf-8') as f2:
                f2.write(contents)
        super(GfdlarchiveDataManager, self)._make_html(
            cleanup=(not self.frepp_mode)
        )

    def _make_tar_file(self, tar_dest_dir):
        # make locally in WORKING_DIR and gcp to destination,
        # since OUTPUT_DIR might be mounted read-only
        config = util_mdtf.ConfigManager()
        out_file = super(GfdlarchiveDataManager, self)._make_tar_file(
            paths.WORKING_DIR
        )
        gfdl_util.gcp_wrapper(
            out_file, tar_dest_dir,
            timeout=self.file_transfer_timeout, dry_run=self.dry_run
        )
        _, file_ = os.path.split(out_file)
        return os.path.join(tar_dest_dir, file_)

    def _copy_to_output(self):
        # use gcp, since OUTPUT_DIR might be mounted read-only
        if self.MODEL_WK_DIR == self.MODEL_OUT_DIR:
            return # no copying needed
        if self.frepp_mode:
            # only copy PODs that ran, whether they succeeded or not
            for pod in self.pods:
                if pod._has_placeholder:
                    gfdl_util.gcp_wrapper(
                        pod.POD_WK_DIR, 
                        pod.POD_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
            # copy all case-level files
            print("\tDEBUG: files in {}".format(self.MODEL_WK_DIR))
            for f in os.listdir(self.MODEL_WK_DIR):
                print("\t\tDEBUG: found {}".format(f))
                if os.path.isfile(os.path.join(self.MODEL_WK_DIR, f)):
                    print("\t\tDEBUG: found {}".format(f))
                    gfdl_util.gcp_wrapper(
                        os.path.join(self.MODEL_WK_DIR, f), 
                        self.MODEL_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
        else:
            # copy everything at once
            if os.path.exists(self.MODEL_OUT_DIR):
                if self.overwrite:
                    try:
                        print('Error: {} exists, attempting to remove.'.format(
                            self.MODEL_OUT_DIR))
                        shutil.rmtree(self.MODEL_OUT_DIR)
                    except OSError:
                        # gcp will not overwrite dirs, so forced to save under
                        # a different name despite overwrite=True
                        print(("Error: couldn't remove {} (probably mounted read"
                            "-only); will rename new directory.").format(
                            self.MODEL_OUT_DIR))
                else:
                    print("Error: {} exists; will rename new directory.".format(
                        self.MODEL_OUT_DIR))
            try:
                if os.path.exists(self.MODEL_OUT_DIR):
                    # check again, since rmtree() might have succeeded
                    self.MODEL_OUT_DIR, version = \
                        util_mdtf.bump_version(self.MODEL_OUT_DIR)
                    new_wkdir, _ = \
                        util_mdtf.bump_version(self.MODEL_WK_DIR, new_v=version)
                    print("\tDEBUG: move {} to {}".format(self.MODEL_WK_DIR, new_wkdir))
                    shutil.move(self.MODEL_WK_DIR, new_wkdir)
                    self.MODEL_WK_DIR = new_wkdir
                gfdl_util.gcp_wrapper(
                    self.MODEL_WK_DIR, self.MODEL_OUT_DIR, 
                    timeout=self.file_transfer_timeout,
                    dry_run=self.dry_run
                )
            except Exception:
                raise # only delete MODEL_WK_DIR if copied successfully
            shutil.rmtree(self.MODEL_WK_DIR)


class GfdlppDataManager(GfdlarchiveDataManager):
    _DiagnosticClass = GfdlDiagnostic
    _DateRangeClass = datelabel.DateRange
    _DateFreqClass = datelabel.DateFrequency

    def __init__(self, case_dict, pod_dict, PreprocessorClass):
        # assign explicitly else linter complains
        self.component = None
        self.data_freq = None
        self.chunk_freq = None
        super(GfdlppDataManager, self).__init__(case_dict, pod_dict, PreprocessorClass)

    _DataKeyClass = data_manager.DefaultDataKey

    @util.mdtf_dataclass(frozen=True)
    class UndeterminedKey(object):
        component: str = ""
        chunk_freq: datelabel.DateFrequency = None

        def __str__(self):
            if (not self.chunk_freq) or self.chunk_freq.is_static:
                return f"{self.component} per {self.chunk_freq} chunks"
            else:
                return f"{self.component}"

    FileDataSet = data_manager.remote_file_dataset_factory(
        'FileDataSet', _DataKeyClass, UndeterminedKey
    )

    _pp_ts_regex = re.compile(r"""
            /?                      # maybe initial separator
            (?P<component>\w+)/     # component name
            ts/                     # timeseries;
            (?P<frequency>\w+)/     # ts freq
            (?P<chunk_freq>\w+)/    # data chunk length   
            (?P<component2>\w+)\.        # component name (again)
            (?P<start_date>\d+)-(?P<end_date>\d+)\.   # file's date range
            (?P<name_in_model>\w+)\.       # field name
            nc                      # netCDF file extension
        """, re.VERBOSE)
    _pp_static_regex = re.compile(r"""
            /?                      # maybe initial separator
            (?P<component>\w+)/     # component name 
            (?P<component2>\w+)     # component name (again)
            \.static\.nc             # static frequency, netCDF file extension                
        """, re.VERBOSE)
    
    def parse_relative_path(self, subdir, filename):
        rel_path = os.path.join(subdir, filename)
        path_d = {
            'case_name': self.case_name,
            'remote_path': os.path.join(self.data_root_dir, rel_path),
            'local_path': util.NOTSET
        }
        match = re.match(self._pp_ts_regex, rel_path)
        if match:
            md = match.groupdict()
            md['date_range'] = datelabel.DateRange(md['start_date'], md['end_date'])
            md = util.filter_dataclass(md, self.FileDataSet)
            return self.FileDataSet(**md, **path_d)
        # match failed, try static file regex instead
        match = re.match(self._pp_static_regex, rel_path)
        if match:
            md = match.groupdict()
            md['start_date'] = datelabel.FXDateMin
            md['end_date'] = datelabel.FXDateMax
            md['date_range'] = datelabel.FXDateRange
            # TODO: fix this: static vars combined in one file;
            # must extract them in preprocessor
            md['name_in_model'] = util.NOTSET 
            md = util.filter_dataclass(md, self.FileDataSet)
            return self.FileDataSet(**md, **path_d)
        raise ValueError("Can't parse {}, skipping.".format(rel_path))

    def subdirectory_filters(self):
        return [self.component, 'ts', gfdl_util.frepp_freq(self.data_freq), 
                gfdl_util.frepp_freq(self.chunk_freq)]
                
    @staticmethod
    def _heuristic_component_tiebreaker(str_list):
        """Determine experiment component(s) from heuristics.

        1. If we're passed multiple components, select those containing 'cmip'.

        2. If that selects multiple components, break the tie by selecting the 
            component with the fewest words (separated by '_'), or, failing that, 
            the shortest overall name.

        Args:
            str_list (:py:obj:`list` of :py:obj:`str`:): list of component names.

        Returns: :py:obj:`str`: name of component that breaks the tie.
        """
        def _heuristic_tiebreaker_sub(strs):
            min_len = min(len(s.split('_')) for s in strs)
            strs2 = [s for s in strs if (len(s.split('_')) == min_len)]
            if len(strs2) == 1:
                return strs2[0]
            else:
                return min(strs2, key=len)

        cmip_list = [s for s in str_list if ('cmip' in s.lower())]
        if cmip_list:
            return _heuristic_tiebreaker_sub(cmip_list)
        else:
            return _heuristic_tiebreaker_sub(str_list)

    def select_undetermined(self):
        d_to_u = dict.fromkeys(self.data_keys)
        for d_key in d_to_u:
            d_to_u[d_key] = {f.to_UndeterminedKey() for f in self.data_files[d_key]}
        choices = dict.fromkeys(self.data_keys)
        cmpt_choices = choose.minimum_cover(
            d_to_u,
            op.attrgetter('component'),
            self._heuristic_component_tiebreaker
        )
        for d_key, cmpt in iter(cmpt_choices.items()):
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(u_key.chunk_freq for u_key in d_to_u[d_key] \
                if u_key.component == cmpt)
            choices[d_key] = self.UndeterminedKey(
                component=cmpt, chunk_freq=str(chunk_freq))
        return choices

class Gfdlcmip6abcDataManager(GfdlarchiveDataManager, metaclass=abc.ABCMeta):
    _DiagnosticClass = GfdlDiagnostic
    _DateRangeClass = datelabel.DateRange
    _DateFreqClass = cmip6.CMIP6DateFrequency

    def __init__(self, case_dict, pod_dict, PreprocessorClass):
        # set data_root_dir
        # from experiment and model, determine institution and mip
        # set realization code = 'r1i1p1f1' unless specified
        cmip = cmip6.CMIP6_CVs()
        if 'activity_id' not in case_dict:
            if 'experiment_id' in case_dict:
                key = case_dict['experiment_id']
            elif 'experiment' in case_dict:
                key = case_dict['experiment']
            else:
                raise Exception("Can't determine experiment.")
        self.experiment_id = key
        self.activity_id = cmip.lookup(key, 'experiment_id', 'activity_id')
        if 'institution_id' not in case_dict:
            if 'source_id' in case_dict:
                key = case_dict['source_id']
            elif 'model' in case_dict:
                key = case_dict['model']
            else:
                raise Exception("Can't determine model/source.")
        self.source_id = key
        self.institution_id = cmip.lookup(key, 'source_id', 'institution_id')
        if 'member_id' not in case_dict:
            self.member_id = 'r1i1p1f1'
        case_dict['CASE_ROOT_DIR'] = os.path.join(
            self._cmip6_root, self.activity_id, self.institution_id, 
            self.source_id, self.experiment_id, self.member_id)
        # assign explicitly else linter complains
        self.data_freq = None
        self.table_id = None
        self.grid_label = None
        self.version_date = None
        super(Gfdlcmip6abcDataManager, self).__init__(case_dict, pod_dict, PreprocessorClass)
        if 'data_freq' in self.__dict__:
            self.table_id = cmip.table_id_from_freq(self.data_freq)

    @abc.abstractmethod # note: only using this as a property
    def _cmip6_root(self):
        pass

    @util.mdtf_dataclass(frozen=True)
    class CMIP6DataKey(data_manager.DefaultDataKey):
        frequency: cmip6.CMIP6DateFrequency = cmip6.CMIP6DateFrequency('fx')

    _DataKeyClass = CMIP6DataKey

    @util.mdtf_dataclass(frozen=True)
    class UndeterminedKey(object):
        table_id: str = ""
        grid_label: str = ""
        version_date: str = ""

        def __str__(self):
            return f"({self.table_id}, {self.grid_label}, v{self.version_date})"

    FileDataSet = data_manager.remote_file_dataset_factory(
        'FileDataSet', _DataKeyClass, UndeterminedKey
    )

    def parse_relative_path(self, subdir, filename):
        path_d = {
            'case_name': self.case_name,
            'remote_path': os.path.join(self.data_root_dir, subdir, filename),
            'local_path': util.NOTSET
        }
        d = cmip6.parse_DRS_path(
            os.path.join(self.data_root_dir, subdir)[len(self._cmip6_root):],
            filename
        )
        d['name_in_model'] = d['variable_id']
        d = util.filter_dataclass(d, self.FileDataSet)
        return self.FileDataSet(**d, **path_d)

    def subdirectory_filters(self):
        return [self.table_id, None, # variable_id
            self.grid_label, self.version_date]

    @staticmethod
    def _cmip6_table_tiebreaker(str_list):
        # no suffix or qualifier, if possible
        tbls = [cmip6.parse_mip_table_id(t) for t in str_list]
        tbls = [t for t in tbls if (not t['spatial_avg'] and not t['region'] \
            and t['temporal_avg'] == 'interval')]
        if not tbls:
            raise Exception('Need to refine table_id more carefully')
        tbls = min(tbls, key=lambda t: len(t['table_prefix']))
        return tbls['table_id']

    @staticmethod
    def _cmip6_grid_tiebreaker(str_list):
        # no suffix or qualifier, if possible
        grids = [cmip6.parse_grid_label(g) for g in str_list]
        grids = [g for g in grids if (
            not g['spatial_avg'] and not g['region']
        )]
        if not grids:
            raise Exception('Need to refine grid_label more carefully')
        grids = min(grids, key=op.itemgetter('grid_number'))
        return grids['grid_label']

    def select_undetermined(self):
        d_to_u = dict.fromkeys(self.data_keys)
        for d_key in d_to_u:
            d_to_u[d_key] = {f.to_UndeterminedKey() for f in self.data_files[d_key]}
        tables = choose.minimum_cover(
            d_to_u,
            op.attrgetter('table_id'), 
            self._cmip6_table_tiebreaker
        )
        dkeys_for_each_pod = list(self.data_pods.inverse().values())
        grid_lbl = choose.all_same_if_possible(
            d_to_u,
            dkeys_for_each_pod,
            op.attrgetter('grid_label'), 
            self._cmip6_grid_tiebreaker
            )
        version_date = choose.require_all_same(
            d_to_u,
            op.attrgetter('version_date'),
            lambda dates: str(max(datelabel.Date(dt) for dt in dates))
            )
        choices = dict.fromkeys(self.data_files)
        for data_key in choices:
            choices[data_key] = self.UndeterminedKey(
                table_id=str(tables[data_key]), 
                grid_label=grid_lbl[data_key], 
                version_date=version_date[data_key]
            )
        return choices

class Gfdludacmip6DataManager(Gfdlcmip6abcDataManager):
    _cmip6_root = os.sep + os.path.join('uda', 'CMIP6')

class Gfdldatacmip6DataManager(Gfdlcmip6abcDataManager):
    # Kris says /data_cmip6 used to stage pre-publication data, so shouldn't
    # be used as a data source unless explicitly requested by user
    _cmip6_root = os.sep + os.path.join('data_cmip6','CMIP6')

