"""Common functions and classes used in multiple places in the MDTF code. 
"""
from __future__ import print_function
import os
import glob
import shutil
import tempfile
import util

class PathManager(util.Singleton):
    """:class:`~util.Singleton` holding root paths for the MDTF code. These are
    set in the ``paths`` section of ``mdtf_settings.json``.
    """
    _root_pathnames = [
        'CODE_ROOT', 'OBS_DATA_ROOT', 'MODEL_DATA_ROOT',
        'WORKING_DIR', 'OUTPUT_DIR'
    ]

    def __init__(self, arg_dict={}, unittest_flag=False):
        for var in self._root_pathnames:
            if unittest_flag: # use in unit testing only
                self.__setattr__(var, 'TEST_'+var)
            else:
                assert var in arg_dict, \
                    'Error: {} not initialized.'.format(var)
                self.__setattr__(var, arg_dict[var])

        self._temp_dirs = []

    def modelPaths(self, case):
        # pylint: disable=maybe-no-member
        d = {}
        if isinstance(case, dict):
            name = case['CASENAME']
            yr1 = case['FIRSTYR']
            yr2 = case['LASTYR']
        else:
            name = case.case_name
            yr1 = case.firstyr
            yr2 = case.lastyr
        case_wk_dir = 'MDTF_{}_{}_{}'.format(name, yr1, yr2)
        d['MODEL_DATA_DIR'] = os.path.join(self.MODEL_DATA_ROOT, name)
        d['MODEL_WK_DIR'] = os.path.join(self.WORKING_DIR, case_wk_dir)
        d['MODEL_OUT_DIR'] = os.path.join(self.OUTPUT_DIR, case_wk_dir)
        return d

    def podPaths(self, pod):
        # pylint: disable=maybe-no-member
        d = {}
        d['POD_CODE_DIR'] = os.path.join(self.CODE_ROOT, 'diagnostics', pod.name)
        d['POD_OBS_DATA'] = os.path.join(self.OBS_DATA_ROOT, pod.name)
        if 'MODEL_WK_DIR' in pod.__dict__:
            d['POD_WK_DIR'] = os.path.join(pod.MODEL_WK_DIR, pod.name)
        if 'MODEL_OUT_DIR' in pod.__dict__:
            d['POD_OUT_DIR'] = os.path.join(pod.MODEL_OUT_DIR, pod.name)
        return d

    def make_tempdir(self, hash_obj=None):
        tempdir_prefix = 'MDTF_temp_'

        temp_root = tempfile.gettempdir()
        if hash_obj is None:
            new_dir = tempfile.mkdtemp(prefix=tempdir_prefix, dir=temp_root)
        elif isinstance(hash_obj, basestring):
            new_dir = os.path.join(temp_root, tempdir_prefix+hash_obj)
        else:
            # nicer-looking hash representation
            hash_ = hex(hash(hash_obj))
            if hash_ < 0:
                new_dir = 'Y'+str(hash_)[3:]
            else:
                new_dir = 'X'+str(hash_)[3:]
            new_dir = os.path.join(temp_root, tempdir_prefix+new_dir)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        assert new_dir not in self._temp_dirs
        self._temp_dirs.append(new_dir)
        return new_dir

    def rm_tempdir(self, path):
        assert path in self._temp_dirs
        self._temp_dirs.remove(path)
        shutil.rmtree(path)

    def cleanup(self):
        for d in self._temp_dirs:
            self.rm_tempdir(d)


class VariableTranslator(util.Singleton):
    def __init__(self, unittest_flag=False, verbose=0):
        # pylint: disable=maybe-no-member
        if unittest_flag:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            config_files = ['dummy_filename']
        else:
            paths = PathManager()
            glob_pattern = os.path.join(paths.CODE_ROOT, 'src', 'fieldlist_*.json')
            config_files = glob.glob(glob_pattern)


        # always have CF-compliant option, which does no translation
        self.axes = {
            'CF': {
                "lon" : {"axis" : "X", "MDTF_envvar" : "lon_coord"},
                "lat" : {"axis" : "Y", "MDTF_envvar" : "lat_coord"},
                "lev" : {"axis" : "Z", "MDTF_envvar" : "lev_coord"},
                "time" : {"axis" : "T", "MDTF_envvar" : "time_coord"}
        }}
        self.variables = {'CF': dict()}
        self.units = {'CF': dict()}
        for filename in config_files:
            d = util.read_json(filename)
            for conv in util.coerce_to_iter(d['convention_name']):
                if verbose > 0: 
                    print('XXX found ', conv)
                self.axes[conv] = d.get('axes', dict())
                self.variables[conv] = util.MultiMap(d.get('var_names', dict()))
                self.units[conv] = util.MultiMap(d.get('units', dict()))

    def toCF(self, convention, varname_in):
        if convention == 'CF': 
            return varname_in
        assert convention in self.variables, \
            "Variable name translation doesn't recognize {}.".format(convention)
        return self.variables[convention].inverse_get_(varname_in)
    
    def fromCF(self, convention, varname_in):
        if convention == 'CF': 
            return varname_in
        assert convention in self.variables, \
            "Variable name translation doesn't recognize {}.".format(convention)
        return self.variables[convention].get_(varname_in)


def get_available_programs(verbose=0):
    return {'py': 'python', 'ncl': 'ncl', 'R': 'Rscript'}
    #return {'py': sys.executable, 'ncl': 'ncl'}  

def is_in_config(key, config, section='settings'):
    # Ugly - should replace with cleaner solution/explicit defaults
    if (section in config) and (key in config[section]):
        if isinstance(config[section][key], bool):
            return True
        else:
            if (config[section][key]): # is not empty
                return True
            else:
                return False
    else:
        return False

def get_from_config(key, config, section='settings', default=None):
    # Ugly - should replace with cleaner solution/explicit defaults
    if is_in_config(key, config, section=section):
        return config[section][key]
    else:
        return default

def setenv(varname,varvalue,env_dict,verbose=0,overwrite=True):
    """Wrapper to set environment variables.

    Args:
        varname (:obj:`str`): Variable name to define
        varvalue: Value to assign. Coerced to type :obj:`str` before being set.
        env_dict (:obj:`dict`): Copy of 
        verbose (:obj:`int`, optional): Logging verbosity level. Default 0.
        overwrite (:obj:`bool`): If set to `False`, do not overwrite the values
            of previously-set variables. 
    """
    if (not overwrite) and (varname in env_dict): 
        if (verbose > 0): 
            print("Not overwriting ENV {}={}".format(varname,env_dict[varname]))
    else:
        if ('varname' in env_dict) \
            and (env_dict[varname] != varvalue) and (verbose > 0): 
            print("WARNING: setenv {}={} overriding previous setting {}".format(
                varname, varvalue, env_dict[varname]
            ))
        env_dict[varname] = varvalue

        # environment variables must be strings
        if isinstance(varvalue, bool):
            if varvalue == True:
                varvalue = '1'
            else:
                varvalue = '0'
        elif not isinstance(varvalue, basestring):
            varvalue = str(varvalue)
        os.environ[varname] = varvalue

        if (verbose > 0): print("ENV ",varname," = ",env_dict[varname])
    if ( verbose > 2) : print("Check ",varname," ",env_dict[varname])

def check_required_envvar(*varlist):
    verbose=0
    varlist = varlist[0]   #unpack tuple
    for n in range(len(varlist)):
        if ( verbose > 2):
            print("checking envvar ", n, varlist[n], str(varlist[n]))
        try:
            _ = os.environ[varlist[n]]
        except:
            print("ERROR: Required environment variable {} not found.".format(
                varlist[n]
            ))
            exit()

def check_required_dirs(already_exist =[], create_if_nec = [], verbose=1):
    # arguments can be envvar name or just the paths
    filestr = __file__+":check_required_dirs: "
    errstr = "ERROR "+filestr
    if verbose > 1: filestr +" starting"
    for dir_in in already_exist + create_if_nec : 
        if verbose > 1: "\t looking at "+dir_in
 
        if dir_in in os.environ:  
            dir = os.environ[dir_in]
        else:
            if verbose>2: print(" envvar "+dir_in+" not defined")    
            dir = dir_in

        if not os.path.exists(dir):
            if not dir_in in create_if_nec:
                if (verbose>0): 
                    print(errstr+dir_in+" = "+dir+" directory does not exist")
                raise OSError(dir+" directory does not exist")
            else:
                print(dir_in+" = "+dir+" created")
                os.makedirs(dir)
        else:
            print("Found "+dir)

def append_html_template(template_file, target_file, template_dict={}, 
    create=True):
    assert os.path.exists(template_file)
    with open(template_file, 'r') as f:
        html_str = f.read()
        html_str = html_str.format(**template_dict)
    if not os.path.exists(target_file):
        if create:
            print("\tDEBUG: write {} to new {}".format(template_file, target_file))
            mode = 'w'
        else:
            raise OSError("Can't find {}".format(target_file))
    else:
        print("\tDEBUG: append {} to {}".format(template_file, target_file))
        mode = 'a'
    with open(target_file, mode) as f:
        f.write(html_str)
