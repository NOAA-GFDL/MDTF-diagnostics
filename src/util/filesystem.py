"""Utility functions for interacting with the *local* filesystem and configuration
files.
"""
import os
import io
import collections
from distutils.spawn import find_executable
import glob
import json
import re
import shutil
from . import basic

def abbreviate_path(path, old_base, new_base=None):
    """Express path as a path relative to old_base, optionally prepending 
    new_base.
    """
    ps = tuple(os.path.abspath(p) for p in (path, old_base))
    str_ = os.path.relpath(ps[0], start=os.path.commonpath(ps))
    if new_base is not None:
        str_ = os.path.join(new_base, str_)
    return str_

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
    path = os.path.expandvars(path) # expand $VAR or ${VAR} for shell env_vars
    if isinstance(env, dict):
        path = _expandvars(path, env)
    if '$' in path:
        print("Warning: couldn't resolve all env vars in '{}'".format(path))
        return path
    if os.path.isabs(path):
        return path
    if root_path == "":
        root_path = os.getcwd()
    assert os.path.isabs(root_path)
    return os.path.normpath(os.path.join(root_path, path))

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
    src_files = basic.to_iter(src_files)
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

def check_executable(exec_name):
    """Tests if <exec_name> is found on the current $PATH.

    Args:
        exec_name (:py:obj:`str`): Name of the executable to search for.

    Returns: :py:obj:`bool` True/false if executable was found on $PATH.
    """
    return (find_executable(exec_name) is not None)

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
    src_dirs = basic.to_iter(src_dirs)
    filename_globs = basic.to_iter(filename_globs)
    files = set([])
    for d in src_dirs:
        for g in filename_globs:
            files.update(glob.glob(os.path.join(d, g)))
            files.update(glob.glob(os.path.join(d, '**', g), recursive=True))
    return list(files)

# ---------------------------------------------------------
# FILE I/O
# ---------------------------------------------------------

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
            file_.write(str_.encode(encoding='utf-8', errors='strict'))
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
