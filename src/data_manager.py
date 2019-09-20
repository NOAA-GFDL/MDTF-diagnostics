import os
import sys
import glob
import shutil
from abc import ABCMeta, abstractmethod
import util
import datelabel
from util import setenv # fix

class DataSet(dict):
    """Class to describe datasets.

    `https://stackoverflow.com/a/48806603`_ for implementation.
    """
    def __init__(self, **kwargs):
        super(DataSet, self).__init__()
        self.name = ''
        self.units = None # not implemented yet
        self.date_range = ''
        self.date_freq = ''
        self.__dict__.update(kwargs)
        if 'var_name' in kwargs and 'name' not in kwargs:
            self.name = kwargs['var_name']
        if 'freq' in kwargs and 'date_freq' not in kwargs:
            self.date_freq = datelabel.DateFrequency(kwargs['freq'])
        self.remote_resource = None
        self.local_resource = None

    def __setitem__(self, key, value):
        super(DataSet, self).__setitem__(key, value)
        self.__dict__[key] = value  # for code completion in editors
    __setattr__ = __setitem__

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __contains__(self, item):
        return (item in self.__dict__)

    def rename_copy(self, new_name=None):
        # shallow copy
        # https://stackoverflow.com/a/15774013
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        if new_name is not None:
            result.name = new_name
        return result  

    def copy(self):
        return self.rename_copy(new_name=None)
    __copy__ = copy

    def _freeze(self):
        """Return immutable representation of (current) attributes.

        We do this to enable comparison of two Datasets, which otherwise would 
        be done by the default method of testing if the two objects refer to the
        same location in memory.
        See `https://stackoverflow.com/a/45170549`_.
        """
        d = self.__dict__
        return tuple((k, repr(d[k])) for k in sorted(d.keys()))

    def __eq__(self, other):
        if type(other) is type(self):
            return self._freeze() == other._freeze()
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

    def __hash__(self):
        return hash(self._freeze())

class DataQueryFailure(Exception):
    """Exception signaling a failure to find requested data in the remote location. 
    
    Raised by :meth:`~data_manager.DataManager.queryData` to signal failure of a
    data query. Should be caught properly in :meth:`~data_manager.DataManager.planData`
    or :meth:`~data_manager.DataManager.fetchData`.
    """
    def __init__(self, dataset, msg=None):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if msg is not None:
            return 'Query failure for {}: {}.'.format(self.dataset.name, self.msg)
        else:
            return 'Query failure for {}.'.format(self.dataset.name)

class DataManager(object):
    # analogue of TestFixture in xUnit
    __metaclass__ = ABCMeta

    def __init__(self, case_dict, config={}, verbose=0):
        self.case_name = case_dict['CASENAME']
        self.model_name = case_dict['model']
        self.firstyr = datelabel.Date(case_dict['FIRSTYR'])
        self.lastyr = datelabel.Date(case_dict['LASTYR'])
        self.date_range = datelabel.DateRange(self.firstyr, self.lastyr)


        if 'variable_convention' in case_dict:
            self.convention = case_dict['variable_convention']
        else:
            self.convention = 'CF' # default to assuming CF-compliance
        if 'pod_list' in case_dict:
            # run a set of PODs specific to this model
            self.pod_list = case_dict['pod_list'] 
        else:
            self.pod_list = config['pod_list'] # use global list of PODs      
        self.pods = []

        paths = util.PathManager()
        self.__dict__.update(paths.modelPaths(self))

    # -------------------------------------

    def setUp(self, config):
        self._setup_model_paths()
        self._set_model_env_vars(config)
        self._setup_html()
        for pod in self.pods:
            self._setup_pod(pod)

    def _setup_model_paths(self, verbose=0):
        util.check_required_dirs(
            already_exist =[self.MODEL_DATA_DIR], 
            create_if_nec = [self.MODEL_WK_DIR], 
            verbose=verbose)

    def _set_model_env_vars(self, config, verbose=0):
        setenv("DATADIR", self.MODEL_DATA_DIR, config['envvars'],
            verbose=verbose)
        setenv("variab_dir", self.MODEL_WK_DIR, config['envvars'],
            verbose=verbose)

        setenv("CASENAME", self.case_name, config['envvars'],
            verbose=verbose)
        setenv("model", self.model_name, config['envvars'],
            verbose=verbose)
        setenv("FIRSTYR", self.firstyr, config['envvars'],
            verbose=verbose)
        setenv("LASTYR", self.lastyr, config['envvars'],
            verbose=verbose)

        translate = util.VariableTranslator()
        # todo: set/unset for multiple models
        # verify all vars requested by PODs have been set
        assert self.convention in translate.field_dict, \
            "Variable name translation doesn't recognize {}.".format(self.convention)
        for key, val in translate.field_dict[self.convention].items():
            setenv(key, val, config['envvars'], verbose=verbose)

    def _setup_html(self):
        if os.path.isfile(os.path.join(self.MODEL_WK_DIR, 'index.html')):
            print("WARNING: index.html exists, not re-creating.")
        else: 
            paths = util.PathManager()
            html_dir = os.path.join(paths.CODE_ROOT, 'src', 'html')
            shutil.copy2(
                os.path.join(html_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
            )
            shutil.copy2(
                os.path.join(html_dir, 'mdtf1.html'), 
                os.path.join(self.MODEL_WK_DIR, 'index.html')
            )

    def _setup_pod(self, pod):
        paths = util.PathManager()
        translate = util.VariableTranslator()
        pod.__dict__.update(paths.modelPaths(self))
        pod.__dict__.update(paths.podPaths(pod))

        # express varlist as DataSet objects
        ds_list = []
        for var in pod.varlist:
            cf_name = translate.toCF(pod.convention, var['var_name'])
            var['CF_name'] = cf_name
            var['name_in_model'] = translate.fromCF(self.convention, cf_name)
            if 'alternates' in var:
                var['alternates'] = [
                    translate.fromCF(self.convention, translate.toCF(pod.convention, var2)) \
                        for var2 in var['alternates']
                ] # only list of translated names, not full DataSets
            var['date_range'] = self.date_range
            ds_list.append(DataSet(**var))
        pod.varlist = ds_list

    # -------------------------------------

    def local_path(self, dataset):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local model data directory structure, which is
        `$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'`.
        Files not following this convention won't be found.
        """
        freq = dataset.date_freq.format_local()
        return os.path.join(
            self.MODEL_DATA_DIR, freq,
            "{}.{}.{}.nc".format(
                self.case_name, dataset.name_in_model, freq)
        )

    def fetch_data(self, verbose=0):
        data_to_fetch = plan_data()
        for var in data_to_fetch:
            self.fetch_dataset(var)
        # do translation/ transformations of data here
        for pod in self.pods:
            var_files = self._check_for_varlist_files(pod.varlist, verbose)
            if var_files['missing_files'] != []:
                print "WARNING: POD ",pod.name," missing required input files:"
                print var_files['missing_files']
            else:
                if (verbose > 0): print "No known missing required input files"

    def plan_data(self):
        data_to_fetch = []
        for pod in self.pods:
            for var in pod.varlist:
                try:
                    data_to_fetch.extend(self._query_dataset_and_alts(var))
                except DataQueryFailure as exc:
                    print "Data query failed on pod {}".format(pod.name)
        return self._optimize_data_fetching(data_to_fetch)


    def _query_dataset_and_alts(self, dataset):
        """Wrapper for queryDataset that attempts querying for alternate variables.
        """
        try:
            self.query_dataset(dataset)
            return dataset
        except DataQueryFailure:
            print "Couldn't find {}, trying alternates".format(dataset.name)
            if len(dataset.alternates) == 0:
                print "Couldn't find {}& no alternates".format(dataset.name)
                raise
            # check for all alternates
            alt_vars = [dataset.rename_copy(var_name) for var_name in dataset.alternates]
            for alt_data in alt_vars:
                try: 
                    self.query_dataset(alt_data)
                except DataQueryFailure:
                    print "Couldn't find alternate data {}".format(alt_data.name)
                    raise
            return alt_vars

    def _optimize_data_fetching(self, datasets):
        """Process list of requested data to make data fetching efficient.

        This is intended as a hook to be used by subclasses. Default behavior is
        to delete from the list duplicate datasets and datasets where a local
        copy of the data already exists and is current (as determined by 
        :meth:`~data_manager.DataManager.local_data_is_current`).

        Args:
            datasets: collection of :class:`~data_manager.DataManager.DataSet`
                objects.
        
        Returns: collection of :class:`~data_manager.DataManager.DataSet`
            objects.
        """
        return [d for d in set(datasets) if not self.local_data_is_current(d)]
    
    def local_data_is_current(self, dataset):
        """Determine if local copy of data needs to be refreshed.

        This is intended as a hook to be used by subclasses. Default is to always
        return `False`, ie always fetch remote data.

        Returns: `True` if local copy of data exists and remote copy hasn't been
            updated.
        """
        return False

    # following are specific details that must be implemented in child class 
    @abstractmethod
    def query_dataset(self, dataset):
        pass

    @abstractmethod
    def fetch_dataset(self, dataset):
        pass


    def _check_for_varlist_files(self, varlist, verbose=0):
        """Verify that all data files needed by a POD exist locally.
        
        Private method called by :meth:`~data_manager.DataManager.fetchData`.

        Args:
            varlist (:obj:`list` of :obj:`dict`): Contents of the varlist portion 
                of the POD's settings.yml file.
            verbose (:obj:`int`, optional): Logging verbosity level. Default 0.

        Returns:
            Dict with two entries, ``found_files`` and ``missing_files``, containing
                lists of paths to found and missing data files, respectively.
        """
        func_name = "\t \t check_for_varlist_files :"
        if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ", varlist
        found_list = []
        missing_list = []
        for ds in varlist:
            if (verbose > 2 ): print func_name +" "+ds.name
            filepath = self.local_path(ds)

            if (os.path.isfile(filepath)):
                print "found ",filepath
                found_list.append(filepath)
                continue
            if (not ds.required):
                print "WARNING: optional file not found ",filepath
                continue
            if not (('alternates' in ds.__dict__) and (len(ds.alternates)>0)):
                print "ERROR: missing required file ",filepath,". No alternatives found"
                missing_list.append(filepath)
            else:
                alt_list = ds.alternates
                print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
                for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
                    if (verbose > 1): print "\t \t examining alternative ",alt_item
                    new_ds = ds.copy()  # modifyable dict with all settings from original
                    new_ds.name_in_model = alt_item # translation done in DataManager._setup_pod()
                    del ds.alternates    # remove alternatives (could use this to implement multiple options)
                    if ( verbose > 2): print "created new_var for input to check_for_varlist_files"
                    new_files = self._check_for_varlist_files([new_ds],verbose=verbose)
                    found_list.extend(new_files['found_files'])
                    missing_list.extend(new_files['missing_files'])

        if (verbose > 2): print "check_for_varlist_files returning ",missing_list
        # remove empty list entries
        files = {}
        files['found_files'] = [x for x in found_list if x]
        files['missing_files'] = [x for x in missing_list if x]
        return files

    # -------------------------------------

    def tearDown(self, config):
        self._backup_config_file(config)
        self._make_tar_file()

    def _backup_config_file(self, config, verbose=0):
        # Record settings in file variab_dir/config_save.yml for rerunning
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.yml')
        if os.path.isfile(out_file):
            out_fileold = os.path.join(self.MODEL_WK_DIR, 'config_save.yml.old')
            if verbose > 1: 
                print "WARNING: moving existing namelist file to ", out_fileold
            shutil.move(out_file, out_fileold)
        util.write_yaml(config, out_file)

    def _make_tar_file(self):
        # Make tar file
        if os.environ["make_variab_tar"] == "0":
            print "Not making tar file because make_variab_tar = 0"
            return

        print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
        if os.path.isfile(self.MODEL_WK_DIR+'.tar'):
            print "Moving existing {0}.tar to {0}.tar.old".format(self.MODEL_WK_DIR)
            shutil.move(self.MODEL_WK_DIR+'.tar', self.MODEL_WK_DIR+'.tar.old')

        print "Creating {}.tar".format(self.MODEL_WK_DIR)
        tar_flags = ["--exclude='*.{}'".format(s) for s in ['netCDF','nc','ps','PS']]
        util.run_command(['tar', '-cf'] + tar_flags \
            + ['{}.tar'.format(self.MODEL_WK_DIR), self.MODEL_WK_DIR]
        )


class LocalfileDataManager(DataManager):
    # Assumes data files are already present in required directory structure 
    def query_dataset(self, dataset):
        path = self.local_path(dataset)
        if os.path.isfile(path):
            dataset.remote_resource = path
        else:
            raise DataQueryFailure(dataset, 'File not found at {}'.format(path))
    
    def local_data_is_current(self, dataset):
        return True 

    def fetch_dataset(self, dataset):
        dataset.local_resource = dataset.remote_resource