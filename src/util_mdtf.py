"""Common functions and classes used in multiple places in the MDTF code. 
"""
import os
import io
import collections
import re
import glob
import shutil
import string
import tempfile
from src import util


class ConfigManager(util.Singleton):
    def __init__(self, cli_obj=None, pod_info_tuple=None, unittest=False):
        assert cli_obj # Singleton, so init should only ever be called once
        # set up paths
        self.paths = _PathManager(cli_obj.config, cli_obj.code_root, unittest)
        # load pod info
        self.pods = pod_info_tuple.pod_data
        self.all_realms = pod_info_tuple.sorted_lists.get('realms', [])
        self.pod_realms = pod_info_tuple.realm_data

        self.global_envvars = dict()
        # copy over all config settings
        self.config = util.NameSpace.fromDict(cli_obj.config)


class _PathManager(util.NameSpace):
    """:class:`~util.Singleton` holding root paths for the MDTF code. These are
    set in the ``paths`` section of ``defaults.jsonc``.
    """
    def __init__(self, d, code_root=None, unittest=False):
        self._unittest = unittest
        self.CODE_ROOT = code_root
        if not self._unittest:
            assert os.path.isdir(self.CODE_ROOT)

    def parse(self, d, paths_to_parse=[], env=None):
        # set by CLI settings that have "parse_type": "path" in JSON entry
        if not paths_to_parse:
            print("Warning: didn't get list of paths from CLI.")
        for key in paths_to_parse:
            self[key] = self._init_path(key, d, env=env)
            if key in d:
                d[key] = self[key]

        # set following explictly: redundant, but keeps linter from complaining
        self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', d, env=env)
        self.MODEL_DATA_ROOT = self._init_path('MODEL_DATA_ROOT', d, env=env)
        self.WORKING_DIR = self._init_path('WORKING_DIR', d, env=env)
        self.OUTPUT_DIR = self._init_path('OUTPUT_DIR', d, env=env)

        if not self.WORKING_DIR:
            self.WORKING_DIR = self.OUTPUT_DIR

    def _init_path(self, key, d, env=None):
        if self._unittest: # use in unit testing only
            return 'TEST_'+key
        else:
            # need to check existence in case we're being called directly
            assert key in d, 'Error: {} not initialized.'.format(key)
            return util.resolve_path(
                util.coerce_from_iter(d[key]), root_path=self.CODE_ROOT, env=env
            )

    def model_paths(self, case, overwrite=False):
        d = util.NameSpace()
        if isinstance(case, dict):
            name = case['CASENAME']
            yr1 = case['FIRSTYR']
            yr2 = case['LASTYR']
        else:
            name = case.case_name
            yr1 = case.firstyr
            yr2 = case.lastyr
        case_wk_dir = 'MDTF_{}_{}_{}'.format(name, yr1, yr2)
        d.MODEL_DATA_DIR = os.path.join(self.MODEL_DATA_ROOT, name)
        d.MODEL_WK_DIR = os.path.join(self.WORKING_DIR, case_wk_dir)
        d.MODEL_OUT_DIR = os.path.join(self.OUTPUT_DIR, case_wk_dir)
        if not overwrite:
            # bump both WK_DIR and OUT_DIR to same version because name of 
            # former may be preserved when we copy to latter, depending on 
            # copy method
            d.MODEL_WK_DIR, ver = bump_version(d.MODEL_WK_DIR, extra_dirs=[self.OUTPUT_DIR])
            d.MODEL_OUT_DIR, _ = bump_version(d.MODEL_OUT_DIR, new_v=ver)
        return d

    def pod_paths(self, pod, case):
        d = util.NameSpace()
        d.POD_CODE_DIR = os.path.join(self.CODE_ROOT, 'diagnostics', pod.name)
        d.POD_OBS_DATA = os.path.join(self.OBS_DATA_ROOT, pod.name)
        d.POD_WK_DIR = os.path.join(case.MODEL_WK_DIR, pod.name)
        d.POD_OUT_DIR = os.path.join(case.MODEL_OUT_DIR, pod.name)
        return d


class TempDirManager(util.Singleton):
    _prefix = 'MDTF_temp_'

    def __init__(self, temp_root=None):
        if not temp_root:
            temp_root = tempfile.gettempdir()
        assert os.path.isdir(temp_root)
        self._root = temp_root
        self._dirs = []

    def make_tempdir(self, hash_obj=None):
        if hash_obj is None:
            new_dir = tempfile.mkdtemp(prefix=self._prefix, dir=self._root)
        elif isinstance(hash_obj, str):
            new_dir = os.path.join(self._root, self._prefix+hash_obj)
        else:
            # nicer-looking hash representation
            hash_ = hex(hash(hash_obj))[2:]
            assert isinstance(hash_, str)
            new_dir = os.path.join(self._root, self._prefix+hash_)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        assert new_dir not in self._dirs
        self._dirs.append(new_dir)
        return new_dir

    def rm_tempdir(self, path):
        assert path in self._dirs
        self._dirs.remove(path)
        print("\tDEBUG: cleanup temp dir {}".format(path))
        shutil.rmtree(path)

    def cleanup(self):
        for d in self._dirs:
            self.rm_tempdir(d)

class ConventionError(Exception):
    pass

class VariableTranslator(util.Singleton):
    def __init__(self, unittest=False, verbose=0):
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            config_files = ['dummy_filename']
        else:
            config = ConfigManager()
            glob_pattern = os.path.join(
                config.paths.CODE_ROOT, 'src', 'fieldlist_*.jsonc'
            )
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
                if conv in self.variables:
                    print("ERROR: convention "+conv+" defined in "+filename+" already exists")
                    raise ConventionError

                self.axes[conv] = d.get('axes', dict())
                self.variables[conv] = util.MultiMap(d.get('var_names', dict()))
                self.units[conv] = util.MultiMap(d.get('units', dict()))



    def toCF(self, convention, varname_in):
        if convention == 'CF': 
            return varname_in
        assert convention in self.variables, \
            "Variable name translation doesn't recognize {}.".format(convention)
        inv_lookup = self.variables[convention].inverse()
        try:
            return util.coerce_from_iter(inv_lookup[varname_in])
        except KeyError:
            print("ERROR: name {} not defined for convention {}.".format(
                varname_in, convention))
            raise
    
    def fromCF(self, convention, varname_in):
        if convention == 'CF': 
            return varname_in
        assert convention in self.variables, \
            "Variable name translation doesn't recognize {}.".format(convention)
        try:
            return self.variables[convention].get_(varname_in)
        except KeyError:
            print("ERROR: name {} not defined for convention {}.".format(
                varname_in, convention))
            raise


def get_available_programs(verbose=0):
    return {'py': 'python', 'ncl': 'ncl', 'R': 'Rscript'}
    #return {'py': sys.executable, 'ncl': 'ncl'}  

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
        elif not isinstance(varvalue, str):
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
                print(dir+" created")
                os.makedirs(dir)
        else:
            print("Found "+dir)

def bump_version(path, new_v=None, extra_dirs=[]):
    # return a filename that doesn't conflict with existing files.
    # if extra_dirs supplied, make sure path doesn't conflict with pre-existing
    # files at those locations either.
    def _split_version(file_):
        match = re.match(r"""
            ^(?P<file_base>.*?)   # arbitrary characters (lazy match)
            (\.v(?P<version>\d+))  # literal '.v' followed by digits
            ?                      # previous group may occur 0 or 1 times
            $                      # end of string
            """, file_, re.VERBOSE)
        if match:
            return (match.group('file_base'), match.group('version'))
        else:
            return (file_, '')

    def _reassemble(dir_, file_, version, ext_, final_sep):
        if version:
            file_ = ''.join([file_, '.v', str(version), ext_])
        else:
            # get here for version == 0, '' or None
            file_ = ''.join([file_, ext_])
        return os.path.join(dir_, file_) + final_sep

    def _path_exists(dir_list, file_, new_v, ext_, sep):
        new_paths = [_reassemble(d, file_, new_v, ext_, sep) for d in dir_list]
        return any([os.path.exists(p) for p in new_paths])

    if path.endswith(os.sep):
        # remove any terminating slash on directory
        path = path.rstrip(os.sep)
        final_sep = os.sep
    else:
        final_sep = ''
    dir_, file_ = os.path.split(path)
    dir_list = util.coerce_to_iter(extra_dirs)
    dir_list.append(dir_)
    file_, old_v = _split_version(file_)
    if not old_v:
        # maybe it has an extension and then a version number
        file_, ext_ = os.path.splitext(file_)
        file_, old_v = _split_version(file_)
    else:
        ext_ = ''

    if new_v is not None:
        # removes version if new_v ==0
        new_path = _reassemble(dir_, file_, new_v, ext_, final_sep)
    else:
        if not old_v:
            new_v = 0
        else:
            new_v = int(old_v)
        while _path_exists(dir_list, file_, new_v, ext_, final_sep):
            new_v = new_v + 1
        new_path = _reassemble(dir_, file_, new_v, ext_, final_sep)
    return (new_path, new_v)

class _DoubleBraceTemplate(string.Template):
    """Private class used by :func:`~util_mdtf.append_html_template` to do 
    string templating with double curly brackets as delimiters, since single
    brackets are also used in css.

    See `https://docs.python.org/3.7/library/string.html#string.Template`_ and 
    `https://stackoverflow.com/a/34362892`__.
    """
    flags = re.VERBOSE # matching is case-sensitive, unlike default
    delimiter = '{{' # starting delimter is two braces, then apply
    pattern = r"""
        \{\{(?:                 # match delimiter itself, but don't include it
        # Alternatives for what to do with string following delimiter:
        # case 1) text is an escaped double bracket, written as '{{{{'.
        (?P<escaped>\{\{)|
        # case 2) text is the name of an env var, possibly followed by whitespace,
        # followed by closing double bracket. Match POSIX env var names,
        # case-sensitive (see https://stackoverflow.com/a/2821183), with the 
        # addition that hyphens are allowed.
        # Can't tell from docs what the distinction between <named> and <braced> is.
        \s*(?P<named>[a-zA-Z_][a-zA-Z0-9_-]*)\s*\}\}|
        \s*(?P<braced>[a-zA-Z_][a-zA-Z0-9_-]*)\s*\}\}|
        # case 3) none of the above: ignore & move on (when using safe_substitute)
        (?P<invalid>)
        )
    """

def append_html_template(template_file, target_file, template_dict={}, 
    create=True, append=True):
    """Perform subtitutions on template_file and write result to target_file.

    Variable substitutions are done with custom 
    `templating <https://docs.python.org/3.7/library/string.html#template-strings>`__,
    replacing *double* curly bracket-delimited keys with their values in template_dict.
    For example, if template_dict is {'A': 'foo'}, all occurrences of the string
    `{{A}}` in template_file are replaced with the string `foo`. Spaces between
    the braces and variable names are ignored.

    Double-curly-bracketed strings that don't correspond to keys in template_dict are
    ignored (instead of raising a KeyError.)

    Double curly brackets are chosen as the delimiter to match the default 
    syntax of, eg, django and jinja2. Using single curly braces leads to conflicts
    with CSS syntax.

    Args:
        template_file: Path to template file.
        target_file: Destination path for result. 
        template_dict: :py:obj:`dict` of variable name-value pairs. Both names
            and values must be strings.
        create: Boolean, default True. If true, create target_file if it doesn't
            exist, otherwise raise an OSError. 
        append: Boolean, default True. If target_file exists and this is true,
            append the substituted contents of template_file to it. If false,
            overwrite target_file with the substituted contents of template_file.
    """
    assert os.path.exists(template_file)
    with io.open(template_file, 'r', encoding='utf-8') as f:
        html_str = f.read()
        html_str = _DoubleBraceTemplate(html_str).safe_substitute(template_dict)
    if not os.path.exists(target_file):
        if create:
            # print("\tDEBUG: write {} to new {}".format(template_file, target_file))
            mode = 'w'
        else:
            raise OSError("Can't find {}".format(target_file))
    else:
        if append:
            # print("\tDEBUG: append {} to {}".format(template_file, target_file))
            mode = 'a'
        else:
            # print("\tDEBUG: overwrite {} with {}".format(target_file, template_file))
            os.remove(target_file)
            mode = 'w'
    with io.open(target_file, mode, encoding='utf-8') as f:
        f.write(html_str)
