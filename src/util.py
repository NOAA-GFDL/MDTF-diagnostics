"""Common functions and classes used in multiple places in the MDTF code.
Specifically, util.py implements general functionality that's not MDTF-specific.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import io
from src import six
import re
import shlex
import glob
import shutil
import collections
from distutils.spawn import find_executable
if os.name == 'posix' and six.PY2:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
import signal
import threading
import errno
import json
from six.moves import getcwd, collections_abc

class _Singleton(type):
    """Private metaclass that creates a :class:`~util.Singleton` base class when
    called. This version is copied from `<https://stackoverflow.com/a/6798042>`__ and
    should be compatible with both Python 2 and 3.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton(six.ensure_str('SingletonMeta'), (object,), {})): 
    """Parent class defining the 
    `Singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`_ pattern. We
    use this as safer way to pass around global state.
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


class ExceptionPropagatingThread(threading.Thread):
    """Class to propagate exceptions raised in a child thread back to the caller
    thread when the child is join()ed. 
    Adapted from `<https://stackoverflow.com/a/31614591>`__.
    """
    def run(self):
        self.ret = None
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(ExceptionPropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret


class MultiMap(collections.defaultdict):
    """Extension of the :obj:`dict` class that allows doing dictionary lookups 
    from either keys or values. 
    
    Syntax for lookup from keys is unchanged, ``bd['key'] = 'val'``, while lookup
    from values is done on the `inverse` attribute and returns a set of matching
    keys if more than one match is present: ``bd.inverse['val'] = ['key1', 'key2']``.    
    See `<https://stackoverflow.com/a/21894086>`__.
    """
    def __init__(self, *args, **kwargs):
        """Initialize :class:`~util.MultiMap` by passing an ordinary :py:obj:`dict`.
        """
        super(MultiMap, self).__init__(set, *args, **kwargs)
        for key in iter(self.keys()):
            super(MultiMap, self).__setitem__(key, coerce_to_iter(self[key], set))

    def __setitem__(self, key, value):
        super(MultiMap, self).__setitem__(key, coerce_to_iter(value, set))

    def get_(self, key):
        if key not in list(self.keys()):
            raise KeyError(key)
        return coerce_from_iter(self[key])
    
    def to_dict(self):
        d = {}
        for key in iter(self.keys()):
            d[key] = self.get_(key)
        return d

    def inverse(self):
        d = collections.defaultdict(set)
        for key, val_set in iter(self.items()):
            for v in val_set:
                d[v].add(key)
        return dict(d)

    def inverse_get_(self, val):
        # don't raise keyerror if empty; could be appropriate result
        inv_lookup = self.inverse()
        return coerce_from_iter(inv_lookup[val])


class NameSpace(dict):
    """ A dictionary that provides attribute-style access.

    For example, `d['key'] = value` becomes `d.key = value`. All methods of 
    :py:obj:`dict` are supported.

    Note: recursive access (`d.key.subkey`, as in C-style languages) is not
        supported.

    Implementation is based on `<https://github.com/Infinidat/munch>`__.
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
            raised by set-item (only likely if you subclass NameSpace) will
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
        return list(self.keys())
    __members__ = __dir__  # for python2.x compatibility

    def __repr__(self):
        """ Invertible* string-form of a Munch.
            (*) Invertible so long as collection contents are each repr-invertible.
        """
        return '{0}({1})'.format(self.__class__.__name__, dict.__repr__(self))

    def __getstate__(self):
        """ Implement a serializable interface used for pickling.
        See `<https://docs.python.org/3.6/library/pickle.html>`__.
        """
        return {k: v for k, v in iter(self.items())}

    def __setstate__(self, state):
        """ Implement a serializable interface used for pickling.
        See `<https://docs.python.org/3.6/library/pickle.html>`__.
        """
        self.clear()
        self.update(state)

    def toDict(self):
        """ Recursively converts a NameSpace back into a dictionary.
        """
        return type(self)._toDict(self)

    @classmethod
    def _toDict(cls, x):
        """ Recursively converts a NameSpace back into a dictionary.
            nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
        """
        if isinstance(x, dict):
            return dict((k, cls._toDict(v)) for k, v in iter(x.items()))
        elif isinstance(x, (list, tuple)):
            return type(x)(cls._toDict(v) for v in x)
        else:
            return x

    @property
    def __dict__(self):
        return self.toDict()

    @classmethod
    def fromDict(cls, x):
        """ Recursively transforms a dictionary into a NameSpace via copy.
            nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
        """
        if isinstance(x, dict):
            return cls((k, cls.fromDict(v)) for k, v in iter(x.items()))
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
        See `<https://stackoverflow.com/a/45170549>`__.
        """
        d = self.toDict()
        d2 = {k: repr(d[k]) for k in d}
        FrozenNameSpace = collections.namedtuple(
            'FrozenNameSpace', sorted(list(d.keys()))
        )
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

def strip_comments(str_, delimiter=None):
    # would be better to use shlex, but that doesn't support multi-character
    # comment delimiters like '//'
    if not delimiter:
        return str_
    s = str_.splitlines()
    for i in list(range(len(s))):
        if s[i].startswith(delimiter):
            s[i] = ''
            continue
        # If delimiter appears quoted in a string, don't want to treat it as
        # a comment. So for each occurrence of delimiter, count number of 
        # "s to its left and only truncate when that's an even number.
        # TODO: handle ' as well as ", for non-JSON applications
        s_parts = s[i].split(delimiter)
        s_counts = [ss.count('"') for ss in s_parts]
        j = 1
        while sum(s_counts[:j]) % 2 != 0:
            j += 1
        s[i] = delimiter.join(s_parts[:j])
    # join lines, stripping blank lines
    return '\n'.join([ss for ss in s if (ss and not ss.isspace())])

def read_json(file_path):
    assert os.path.exists(file_path), \
        "Couldn't find JSON file {}.".format(file_path)
    try:    
        with io.open(file_path, 'r', encoding='utf-8') as file_:
            str_ = file_.read()
    except IOError:
        print('Fatal IOError when trying to read {}. Exiting.'.format(file_path))
        exit()
    return parse_json(str_)

def parse_json(str_):
    str_ = strip_comments(str_, delimiter= '//') # JSONC quasi-standard
    try:
        parsed_json = json.loads(str_, object_pairs_hook=collections.OrderedDict)
    except UnicodeDecodeError:
        print('{} contains non-ascii characters. Exiting.'.format(str_))
        exit()
    return parsed_json

def write_json(struct, file_path, verbose=0, sort_keys=False):
    """Wrapping file I/O simplifies unit testing.

    Args:
        struct (:py:obj:`dict`)
        file_path (:py:obj:`str`): path of the JSON file to write.
        verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.
    """
    try:
        str_ = json.dumps(struct, 
            sort_keys=sort_keys, indent=2, separators=(',', ': '))
        with io.open(file_path, 'w', encoding='utf-8') as file_:
            file_.write(six.ensure_text(str_, encoding='utf-8', errors='strict'))
    except IOError:
        print('Fatal IOError when trying to write {}. Exiting.'.format(file_path))
        exit()

def pretty_print_json(struct, sort_keys=False):
    """Pseudo-YAML output for human-readable debugging output only - 
    not valid JSON"""
    str_ = json.dumps(struct, sort_keys=sort_keys, indent=2)
    for char in ['"', ',', '}', '[', ']']:
        str_ = str_.replace(char, '')
    str_ = re.sub(r"{\s+", "- ", str_)
    # remove lines containing only whitespace
    return os.linesep.join([s for s in str_.splitlines() if s.strip()]) 

def find_files(src_dirs, filename_globs):
    """Return list of files in `src_dirs` matching any of `filename_globs`. 

    Wraps glob.glob for the use cases encountered in cleaning up POD output.

    Args:
        src_dirs: Directory, or a list of directories, to search for files in.
            The function will also search all subdirectories.
        filename_globs: Glob, or a list of globs, for filenames to match. This 
            is a shell globbing pattern, not a full regex.

    Returns: :py:obj:`list` of paths to files matching any of the criteria.
        If no files are found, the list is empty.
    """
    src_dirs = coerce_to_iter(src_dirs)
    filename_globs = coerce_to_iter(filename_globs)
    files = set([])
    for d in src_dirs:
        for g in filename_globs:
            files.update(glob.glob(os.path.join(d, g)))
            files.update(glob.glob(os.path.join(d, '**', g)))
    return list(files)

def recursive_copy(src_files, src_root, dest_root, copy_function=None, 
    overwrite=False):
    """Copy src_files to dest_root, preserving relative subdirectory structure.

    Copies a subset of files in a directory subtree rooted at src_root to an
    identical subtree structure rooted at dest_root, creating any subdirectories
    as needed. For example, `recursive_copy('/A/B/C.txt', '/A', '/D')` will 
    first create the destination subdirectory `/D/B` and copy '/A/B/C.txt` to 
    `/D/B/C.txt`.

    Args:
        src_files: Absolute path, or list of absolute paths, to files to copy.
        src_root: Root subtree of all files in src_files. Raises a ValueError
            if all files in src_files are not contained in the src_root directory.
        dest_root: Destination directory in which to create the copied subtree.
        copy_function: Function to use to copy individual files. Must take two 
            arguments, the source and destination paths, respectively. Defaults 
            to :py:meth:`shutil.copy2`.
        overwrite: Boolean, deafult False. If False, raise an OSError if
            any destination files already exist, otherwise silently overwrite.
    """
    if copy_function is None:
        copy_function = shutil.copy2
    src_files = coerce_to_iter(src_files)
    for f in src_files:
        if not f.startswith(src_root):
            raise ValueError('{} not a sub-path of {}'.format(f, src_root))
    dest_files = [
        os.path.join(dest_root, os.path.relpath(f, start=src_root)) \
        for f in src_files
    ]
    for f in dest_files:
        if not overwrite and os.path.exists(f):
            raise OSError('{} exists.'.format(f))
        os.makedirs(os.path.normpath(os.path.dirname(f)), exist_ok=True)
    for src, dest in zip(src_files, dest_files):
        copy_function(src, dest)

def resolve_path(path, root_path="", env=None):
    """Abbreviation to resolve relative paths.

    Args:
        path (:obj:`str`): path to resolve.
        root_path (:obj:`str`, optional): root path to resolve `path` with. If
            not given, resolves relative to `cwd`.

    Returns: Absolute version of `path`, relative to `root_path` if given, 
        otherwise relative to `os.getcwd`.
    """
    def _expandvars(path, env_dict):
        """Expand quoted variables of the form $key and ${key} in path,
        where key is a key in env_dict, similar to os.path.expandvars.

        See `<https://stackoverflow.com/a/30777398>`__; specialize to not skipping
        escaped characters and not changing unrecognized variables.
        """
        return re.sub(
            r'\$(\w+|\{([^}]*)\})', 
            lambda m: env_dict.get(m.group(2) or m.group(1), m.group(0)), 
            path
        )

    if path == '':
        return path # default value set elsewhere
    path = os.path.expanduser(path) # resolve '~' to home dir
    path = os.path.expandvars(path) # expand $VAR or ${VAR} for shell envvars
    if isinstance(env, dict):
        path = _expandvars(path, env)
    if '$' in path:
        print("Warning: couldn't resolve all env vars in '{}'".format(path))
        return path
    if os.path.isabs(path):
        return path
    if root_path == "":
        root_path = getcwd()
    assert os.path.isabs(root_path)
    return os.path.normpath(os.path.join(root_path, path))

def check_executable(exec_name):
    """Tests if <exec_name> is found on the current $PATH.

    Args:
        exec_name (:py:obj:`str`): Name of the executable to search for.

    Returns: :py:obj:`bool` True/false if executable was found on $PATH.
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
        shell (:py:obj:`bool`, optional): shell flag, passed to Popen, 
            default `False`.
        env (:py:obj:`dict`, optional): environment variables to set, passed to 
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
        command (list of :py:obj:`str`): List of commands to execute
        env (:py:obj:`dict`, optional): environment variables to set, passed to 
            `Popen`, default `None`.
        cwd (:py:obj:`str`, optional): child processes' working directory, passed
            to `Popen`. Default is `None`, which uses parent processes' directory.
        timeout (:py:obj:`int`, optional): Optionally, kill the command's subprocess
            and raise a CalledProcessError if the command doesn't finish in 
            `timeout` seconds.

    Returns:
        :py:obj:`list` of :py:obj:`str` containing output that was written to stdout  
        by each command. Note: this is split on newlines after the fact.

    Raises:
        CalledProcessError: If any commands return with nonzero exit code.
            Stderr for that command is stored in `output` attribute.
    """
    def _timeout_handler(signum, frame):
        raise TimeoutAlarm

    if isinstance(command, six.string_types):
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

def run_shell_command(command, env=None, cwd=None, dry_run=False):
    """Subprocess wrapper to facilitate running shell commands.

    See documentation for the Python2 `subprocess 
    <https://docs.python.org/2/library/subprocess.html>`_ module.

    Args:
        commands (list of :py:obj:`str`): List of commands to execute
        env (:py:obj:`dict`, optional): environment variables to set, passed to 
            `Popen`, default `None`.
        cwd (:py:obj:`str`, optional): child processes' working directory, passed
            to `Popen`. Default is `None`, which uses parent processes' directory.

    Returns:
        :py:obj:`list` of :py:obj:`str` containing output that was written to stdout  
        by each command. Note: this is split on newlines after the fact, so if 
        commands give != 1 lines of output this will not map to the list of commands
        given.

    Raises:
        CalledProcessError: If any commands return with nonzero exit code.
            Stderr for that command is stored in `output` attribute.
    """
    # shouldn't lookup on each invocation, but need abs path to bash in order
    # to pass as executable argument. Pass executable argument because we want
    # bash specifically (not default /bin/sh, and we save a bit of overhead by
    # starting bash directly instead of from sh.)
    bash_exec = find_executable('bash')

    if not isinstance(command, six.string_types):
        command = ' '.join(command)
    if dry_run:
        print('DRY_RUN: call {}'.format(command))
        return
    proc = None
    pid = None
    retcode = 1
    stderr = ''
    try:
        proc = subprocess.Popen(
            command,
            shell=True, executable=bash_exec,
            env=env, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=0
        )
        pid = proc.pid
        (stdout, stderr) = proc.communicate()
        retcode = proc.returncode
    except Exception as exc:
        if proc:
            proc.kill()
        stderr = stderr+"\nCaught exception {0}({1!r})".format(
            type(exc).__name__, exc.args)
    if retcode != 0:
        print('run_shell_command on {} (pid {}) exit status={}:{}\n'.format(
            command, pid, retcode, stderr
        ))
        raise subprocess.CalledProcessError(
            returncode=retcode, cmd=command, output=stderr)
    if '\0' in stdout:
        return stdout.split('\0')
    else:
        return stdout.splitlines()

def is_iterable(obj):
    return isinstance(obj, collections_abc.Iterable) \
        and not isinstance(obj, six.string_types) # py3 strings have __iter__

def coerce_to_iter(obj, coll_type=list):
    assert coll_type in [list, set, tuple] # only supported types for now
    if obj is None:
        return coll_type([])
    elif isinstance(obj, coll_type):
        return obj
    elif is_iterable(obj):
        return coll_type(obj)
    else:
        return coll_type([obj])

def coerce_from_iter(obj):
    if is_iterable(obj):
        if len(obj) == 1:
            return list(obj)[0]
        else:
            return list(obj)
    else:
        return obj

def filter_kwargs(kwarg_dict, function):
    """Given a dict of kwargs, return only those kwargs accepted by function.
    """
    named_args = set(six.get_function_code(function).co_varnames)
    # if 'kwargs' in named_args:
    #    return kwarg_dict # presumably can handle anything
    return dict((k, kwarg_dict[k]) for k in named_args \
        if k in kwarg_dict and k not in ['self', 'args', 'kwargs'])

def signal_logger(caller_name, signum=None, frame=None):
    """Lookup signal name from number; `<https://stackoverflow.com/a/2549950>`__.
    """
    if signum:
        sig_lookup = {
            k:v for v, k in reversed(sorted(list(signal.__dict__.items()))) \
                if v.startswith('SIG') and not v.startswith('SIG_')
        }
        print("\tDEBUG: {} caught signal {} ({})".format(
            caller_name, sig_lookup.get(signum, 'UNKNOWN'), signum
        ))
        print("\tDEBUG: {}".format(frame))
