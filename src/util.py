"""Common functions and classes used in multiple places in the MDTF code.
"""
from __future__ import print_function
import os
import sys
import re
import glob
import shlex
import shutil
import tempfile
from collections import defaultdict, namedtuple
from distutils.spawn import find_executable
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
import signal
import errno
import json
import datelabel

class _Singleton(type):
    """Private metaclass that creates a :class:`~util.Singleton` base class when
    called. This version is copied from <https://stackoverflow.com/a/6798042>_ and
    should be compatible with both Python 2 and 3.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})): 
    """Parent class defining the 
    `Singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`_ pattern. We
    use this as safer way to pass around global state.

    Note:
        All child classes, :class:`~util.PathManager` and :class:`~util.VariableTranslator`,
        are read-only, although this is not enforced. This eliminates most of the
        danger in using Singletons or global state in general.
    """
    @classmethod
    def _reset(cls):
        """Private method of all :class:`~util.Singleton`-derived classes added
        for use in unit testing only. Calling this method on test teardown 
        deletes the instance, so that tests coming afterward will initialize the 
        :class:`~util.Singleton` correctly, instead of getting the state set 
        during previous tests.
        """
        # pylint: disable=maybe-no-member
        if cls in cls._instances:
            del cls._instances[cls]


class PathManager(Singleton):
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
        elif isinstance(hash_obj, str):
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

class MultiMap(defaultdict):
    """Extension of the :obj:`dict` class that allows doing dictionary lookups 
    from either keys or values. 
    
    Syntax for lookup from keys is unchanged, ``bd['key'] = 'val'``, while lookup
    from values is done on the `inverse` attribute and returns a set of matching
    keys if more than one match is present: ``bd.inverse['val'] = ['key1', 'key2']``.    
    See <https://stackoverflow.com/a/21894086>_.
    """
    def __init__(self, *args, **kwargs):
        """Initialize :class:`~util.MultiMap` by passing an ordinary :obj:`dict`.
        """
        super(MultiMap, self).__init__(set, *args, **kwargs)
        for key in self.keys():
            super(MultiMap, self).__setitem__(key, coerce_to_iter(self[key], set))

    def __setitem__(self, key, value):
        super(MultiMap, self).__setitem__(key, coerce_to_iter(value, set))

    def get_(self, key):
        if key not in self.keys():
            raise KeyError(key)
        return coerce_from_iter(self[key])
    
    def to_dict(self):
        d = {}
        for key in self.keys():
            d[key] = self.get_(key)
        return d

    def inverse(self):
        d = defaultdict(set)
        for key, val_set in self.iteritems():
            for v in val_set:
                d[v].add(key)
        return dict(d)

    def inverse_get_(self, val):
        # if val not in self.values():
        #     raise KeyError(val)
        temp = self.inverse()
        return coerce_from_iter(temp[val])

class VariableTranslator(Singleton):
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
            d = read_json(filename)
            for conv in coerce_to_iter(d['convention_name'], list):
                if verbose > 0: 
                    print('XXX found ', conv)
                self.axes[conv] = d.get('axes', dict())
                self.variables[conv] = MultiMap(d.get('var_names', dict()))
                self.units[conv] = MultiMap(d.get('units', dict()))

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

class Namespace(dict):
    """ A dictionary that provides attribute-style access.

    For example, `d['key'] = value` becomes `d.key = value`. All methods of 
    :obj:`dict` are supported.

    Note: recursive access (`d.key.subkey`, as in C-style languages) is not
        supported.

    Implementation is based on `https://github.com/Infinidat/munch`_.
    """

    # only called if k not found in normal places
    def __getattr__(self, k):
        """ Gets key if it exists, otherwise throws AttributeError.
            nb. __getattr__ is only called if key is not found in normal places.
        """
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError:
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)

    def __setattr__(self, k, v):
        """ Sets attribute k if it exists, otherwise sets key k. A KeyError
            raised by set-item (only likely if you subclass Namespace) will
            propagate as an AttributeError instead.
        """
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                self[k] = v
            except:
                raise AttributeError(k)
        else:
            object.__setattr__(self, k, v)

    def __delattr__(self, k):
        """ Deletes attribute k if it exists, otherwise deletes key k. A KeyError
            raised by deleting the key--such as when the key is missing--will
            propagate as an AttributeError instead.
        """
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)

    def __dir__(self):
        return self.keys()
    __members__ = __dir__  # for python2.x compatibility

    def __repr__(self):
        """ Invertible* string-form of a Munch.
            (*) Invertible so long as collection contents are each repr-invertible.
        """
        return '{0}({1})'.format(self.__class__.__name__, dict.__repr__(self))

    def __getstate__(self):
        """ Implement a serializable interface used for pickling.
        See https://docs.python.org/3.6/library/pickle.html.
        """
        return {k: v for k, v in self.items()}

    def __setstate__(self, state):
        """ Implement a serializable interface used for pickling.
        See https://docs.python.org/3.6/library/pickle.html.
        """
        self.clear()
        self.update(state)

    def toDict(self):
        """ Recursively converts a Namespace back into a dictionary.
        """
        return type(self)._toDict(self)

    @classmethod
    def _toDict(cls, x):
        """ Recursively converts a Namespace back into a dictionary.
            nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
        """
        if isinstance(x, dict):
            return dict((k, cls._toDict(v)) for k, v in x.iteritems())
        elif isinstance(x, (list, tuple)):
            return type(x)(cls._toDict(v) for v in x)
        else:
            return x

    @property
    def __dict__(self):
        return self.toDict()

    @classmethod
    def fromDict(cls, x):
        """ Recursively transforms a dictionary into a Namespace via copy.
            nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
        """
        if isinstance(x, dict):
            return cls((k, cls.fromDict(v)) for k, v in x.iteritems())
        elif isinstance(x, (list, tuple)):
            return type(x)(cls.fromDict(v) for v in x)
        else:
            return x

    def copy(self):
        return type(self).fromDict(self)
    __copy__ = copy

    def _freeze(self):
        """Return immutable representation of (current) attributes.

        We do this to enable comparison of two Namespaces, which otherwise would 
        be done by the default method of testing if the two objects refer to the
        same location in memory.
        See `https://stackoverflow.com/a/45170549`_.
        """
        d = self.toDict()
        d2 = {k: repr(d[k]) for k in d}
        FrozenNameSpace = namedtuple('FrozenNameSpace', sorted(d.keys()))
        return FrozenNameSpace(**d2)

    def __eq__(self, other):
        if type(other) is type(self):
            return (self._freeze() == other._freeze())
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

    def __hash__(self):
        return hash(self._freeze())

# ------------------------------------

def read_json(file_path):
    assert os.path.exists(file_path), \
        "Couldn't find JSON file {}.".format(file_path)
    try:    
        with open(file_path, 'r') as file_:
            str_ = file_.read()
    except IOError:
        print('Fatal IOError when trying to read {}. Exiting.'.format(file_path))
        exit()
    return parse_json(str_)

def parse_json(str_):
    def _utf8_to_ascii(data, ignore_dicts=False):
        # json returns UTF-8 encoded strings by default, but we're in py2 where 
        # everything is ascii. Convert strings to ascii using this solution:
        # https://stackoverflow.com/a/33571117
        # Also drop any elements beginning with a '#' (convention for comments.)

        # if this is a unicode string, return its string representation
        if isinstance(data, unicode):
            # raise UnicodeDecodeError if file contains non-ascii characters
            return data.encode('ascii', 'strict')
        # if this is a list of values, return list of byteified values
        if isinstance(data, list):
            ascii_ = [_utf8_to_ascii(item, ignore_dicts=True) for item in data]
            return [item for item in ascii_ if not (
                hasattr(item, 'startswith') and item.startswith('#'))]
        # if this is a dictionary, return dictionary of byteified keys and values
        # but only if we haven't already byteified it
        if isinstance(data, dict) and not ignore_dicts:
            ascii_ = {
                _utf8_to_ascii(key, ignore_dicts=True): _utf8_to_ascii(value, ignore_dicts=True)
                for key, value in data.iteritems()
            }
            return {key: ascii_[key] for key in ascii_ if not (
                hasattr(key, 'startswith') and key.startswith('#'))}
        # if it's anything else, return it in its original form
        return data

    try:
        parsed_json = _utf8_to_ascii(
            json.loads(str_, object_hook=_utf8_to_ascii), ignore_dicts=True
        )
    except UnicodeDecodeError:
        print('{} contains non-ascii characters. Exiting.'.format(str_))
        exit()
    return parsed_json

def write_json(struct, file_path, verbose=0):
    """Wrapping file I/O simplifies unit testing.

    Args:
        struct (:obj:`dict`)
        file_path (:obj:`str`): path of the JSON file to write.
        verbose (:obj:`int`, optional): Logging verbosity level. Default 0.
    """
    try:
        with open(file_path, 'w') as file_obj:
            json.dump(struct, file_obj, 
                sort_keys=True, indent=2, separators=(',', ': '))
    except IOError:
        print('Fatal IOError when trying to write {}. Exiting.'.format(file_path))
        exit()

def pretty_print_json(struct):
    """Pseudo-YAML output for human-readbale debugging output only - 
    not valid JSON"""
    str_ = json.dumps(struct, sort_keys=True, indent=2)
    for char in ['"', ',', '{', '}', '[', ']']:
        str_ = str_.replace(char, '')
    # remove lines containing only whitespace
    return os.linesep.join([s for s in str_.splitlines() if s.strip()]) 

def resolve_path(in_path, root_path=''):
    """Abbreviation to resolve relative paths.

    Args:
        path (:obj:`str`): path to resolve.
        root_path (:obj:`str`, optional): root path to resolve `path` with. If
            not given, resolves relative to `cwd`.

    Returns: Absolute version of `path`, relative to `root_path` if given, 
        otherwise relative to `os.getcwd`.
    """
    path = in_path
    for key, val in os.environ.iteritems():
        path = re.sub(r"\$"+key, val, path)
    if os.path.isabs(path):
        return path
    else:
        if root_path == '':
            root_path = os.getcwd()
        else:
            assert os.path.isabs(root_path)
        return os.path.normpath(os.path.join(root_path, path))

def find_files(root_dir, pattern):
    """Return list of files in `root_dir` matching `pattern`. 

    Wraps the unix `find` command (`locate` would be much faster but there's no
    way to query if its DB is current). 

    Args:
        root_dir (:obj:`str`): Directory to search for files in.
        pattern (:obj:`str`): Patterrn to match. This is a shell globbing pattern,
            not a full regex. Default is to match filenames only, unless the
            pattern contains a directory separator, in which case the match will
            be done on the entire path relative to `root_dir`.

    Returns: :obj:`list` of relative paths to files matching `pattern`. Paths are
        relative to `root_dir`. If no files are found, the list is empty.
    """
    if os.sep in pattern:
        pattern_flag = '-path' # searching whole path
    else:
        pattern_flag = '-name' # search filename only 
    paths = run_command([
        'find', os.path.normpath(root_dir), '-depth', '-type', 'f', 
        pattern_flag, pattern
        ])
    # strip out root_dir part of path: get # of chars in root_dir (plus terminating
    # separator) and return remainder. Could do this with '-printf %P' in GNU find
    # but BSD find (mac os) doesn't have that.
    prefix_length = len(os.path.normpath(root_dir)) + 1 
    return [p[prefix_length:] for p in paths]

def check_executable(exec_name):
    """Tests if <exec_name> is found on the current $PATH.

    Args:
        exec_name (:obj:`str`): Name of the executable to search for.

    Returns: :obj:`bool` True/false if executable was found on $PATH.
    """
    return (find_executable(exec_name) is not None)

def poll_command(command, shell=False, env=None):
    """Runs a shell command and prints stdout in real-time.
    
    Optional ability to pass a different environment to the subprocess. See
    documentation for the Python2 `subprocess 
    <https://docs.python.org/2/library/subprocess.html>`_ module.

    Args:
        command: list of command + arguments, or the same as a single string. 
            See `subprocess` syntax. Note this interacts with the `shell` setting.
        shell (:obj:`bool`, optional): shell flag, passed to Popen, 
            default `False`.
        env (:obj:`dict`, optional): environment variables to set, passed to 
            Popen, default `None`.
    """
    process = subprocess.Popen(
        command, shell=shell, env=env, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc

class TimeoutAlarm(Exception):
    # dummy exception for signal handling in run_command
    pass

def run_command(command, env=None, cwd=None, timeout=0, dry_run=False):
    """Subprocess wrapper to facilitate running single command without starting
    a shell.

    Note:
        We hope to save some process overhead by not running the command in a
        shell, but this means the command can't use piping, quoting, environment 
        variables, or filename globbing etc.

    See documentation for the Python2 `subprocess 
    <https://docs.python.org/2/library/subprocess.html>`_ module.

    Args:
        command (list of :obj:`str`): List of commands to execute
        env (:obj:`dict`, optional): environment variables to set, passed to 
            `Popen`, default `None`.
        cwd (:obj:`str`, optional): child processes' working directory, passed
            to `Popen`. Default is `None`, which uses parent processes' directory.
        timeout (:obj:`int`, optional): Optionally, kill the command's subprocess
            and raise a CalledProcessError if the command doesn't finish in 
            `timeout` seconds.

    Returns:
        :obj:`list` of :obj:`str` containing output that was written to stdout  
        by each command. Note: this is split on newlines after the fact.

    Raises:
        CalledProcessError: If any commands return with nonzero exit code.
            Stderr for that command is stored in `output` attribute.
    """
    def _timeout_handler(signum, frame):
        raise TimeoutAlarm

    if type(command) == str:
        command = shlex.split(command)
    cmd_str = ' '.join(command)
    if dry_run:
        print('DRY_RUN: call {}'.format(cmd_str))
        return
    proc = None
    pid = None
    retcode = 1
    stderr = ''
    try:
        proc = subprocess.Popen(
            command, shell=False, env=env, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=0
        )
        pid = proc.pid
        # py3 has timeout built into subprocess; this is a workaround
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(int(timeout))
        (stdout, stderr) = proc.communicate()
        signal.alarm(0)  # cancel the alarm
        retcode = proc.returncode
    except TimeoutAlarm:
        if proc:
            proc.kill()
        retcode = errno.ETIME
        stderr = stderr+"\nKilled by timeout (>{}sec).".format(timeout)
    except Exception as exc:
        if proc:
            proc.kill()
        stderr = stderr+"\nCaught exception {0}({1!r})".format(
            type(exc).__name__, exc.args)
    if retcode != 0:
        print('run_command on {} (pid {}) exit status={}:{}\n'.format(
            cmd_str, pid, retcode, stderr
        ))
        raise subprocess.CalledProcessError(
            returncode=retcode, cmd=cmd_str, output=stderr)
    if '\0' in stdout:
        return stdout.split('\0')
    else:
        return stdout.splitlines()

def run_shell_commands(commands, env=None, cwd=None):
    """Subprocess wrapper to facilitate running multiple shell commands.

    See documentation for the Python2 `subprocess 
    <https://docs.python.org/2/library/subprocess.html>`_ module.

    Args:
        commands (list of :obj:`str`): List of commands to execute
        env (:obj:`dict`, optional): environment variables to set, passed to 
            `Popen`, default `None`.
        cwd (:obj:`str`, optional): child processes' working directory, passed
            to `Popen`. Default is `None`, which uses parent processes' directory.

    Returns:
        :obj:`list` of :obj:`str` containing output that was written to stdout  
        by each command. Note: this is split on newlines after the fact, so if 
        commands give != 1 lines of output this will not map to the list of commands
        given.

    Raises:
        CalledProcessError: If any commands return with nonzero exit code.
            Stderr for that command is stored in `output` attribute.
    """
    proc = subprocess.Popen(
        ['/usr/bin/env', 'bash'],
        shell=False, env=env, cwd=cwd,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, bufsize=0
    )
    if type(commands) == str:
        commands = [commands]
    # Tried many scenarios for executing commands sequentially 
    # (eg with stdin.write()) but couldn't find a solution that wasn't 
    # susceptible to deadlocks. Instead just hand over all commands at once.
    # Only disadvantage is that we lose the ability to assign output to a specfic
    # command.
    (stdout, stderr) = proc.communicate(' && '.join(commands))
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode, cmd=' && '.join(commands), output=stderr)
    return stdout.splitlines()

def get_available_programs(verbose=0):
    return {'py': 'python', 'ncl': 'ncl', 'R': 'Rscript'}
    #return {'py': sys.executable, 'ncl': 'ncl'}  

def coerce_to_iter(obj, coll_type):
    assert coll_type in [list, set] # only supported types for now
    if obj is None:
        return coll_type([])
    elif isinstance(obj, coll_type):
        return obj
    elif hasattr(obj, '__iter__'):
        return coll_type(obj)
    else:
        return coll_type([obj])

def coerce_from_iter(obj):
    if hasattr(obj, '__iter__'):
        if len(obj) == 1:
            return list(obj)[0]
        else:
            return list(obj)
    else:
        return obj

def is_in_config(key, config, section='settings'):
    # Ugly - should replace with cleaner solution/explicit defaults
    if (section in config) and (key in config[section]):
        if type(config[section][key] is bool):
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
        if type(varvalue) is bool:
            if varvalue == True:
                varvalue = '1'
            else:
                varvalue = '0'
        elif type(varvalue) is not str:
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
