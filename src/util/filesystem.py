"""Utility functions for interacting with the local filesystem and configuration
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
import signal
import string
import tempfile
from . import basic
from . import exceptions
from . import signal_logger
from . import Singleton

import logging
_log = logging.getLogger(__name__)


def abbreviate_path(path, old_base, new_base=None):
    """Express *path* as a path relative to *old_base*, optionally prepending
    *new_base*.
    """
    ps = tuple(os.path.abspath(p) for p in (path, old_base))
    str_ = os.path.relpath(ps[0], start=os.path.commonpath(ps))
    if new_base is not None:
        str_ = os.path.join(new_base, str_)
    return str_


def resolve_path(rel_path: str, root_path: str = "", env_vars: dict = None, log=_log):
    """Abbreviation to resolve relative paths, expanding environment variables
    if necessary.

    Args:
        rel_path (str): Path to resolve.
        root_path (str): Optional. Root path to resolve `path` with. If
            not given, resolves relative to :py:func:`os.getcwd`.
        env_vars (dict): global environment variables

    Returns:
        str: Absolute version of *path*.
    """
    def _expandvars(path_name: str, env_dict: dict):
        """Expand quoted variables of the form ``$key`` and ``${key}`` in *path*,
        where ``key`` is a key in *env_dict*, similar to
        :py:func:`os.path.expandvars`.

        See `<https://stackoverflow.com/a/30777398>`__; specialize to not skipping
        escaped characters and not changing unrecognized variables.
        """
        return re.sub(
            r'\$(\w+|\{([^}]*)\})',
            lambda m: env_dict.get(m.group(2) or m.group(1), m.group(0)),
            path_name
        )

    if rel_path == "":
        return rel_path  # default value set elsewhere
    rel_path = os.path.expanduser(rel_path)  # resolve '~' to home dir
    rel_path = os.path.expandvars(rel_path)  # expand $VAR or ${VAR} for shell env_vars
    if isinstance(env_vars, dict):
        rel_path = _expandvars(rel_path, env_vars)
    if '$' in rel_path:
        log.warning("Couldn't resolve all env vars in '%s'", rel_path)
        return rel_path
    if os.path.isabs(rel_path):
        return rel_path
    if root_path == "":
        root_path = os.getcwd()
    assert os.path.isabs(root_path)
    return os.path.normpath(os.path.join(root_path, rel_path))


def recursive_copy(src_files, src_root, dest_root, copy_function=None,
                   overwrite=False):
    """Copy *src_files* to *dest_root*, preserving relative subdirectory structure.

    Copies a subset of files in a directory subtree rooted at *src_root* to an
    identical subtree structure rooted at *dest_root*, creating any subdirectories
    as needed. For example, ``recursive_copy('/A/B/C.txt', '/A', '/D')`` will
    first create the destination subdirectory ``/D/B`` and copy ``/A/B/C.txt`` to
    ``/D/B/C.txt``.

    Args:
        src_files (str or iterable): Absolute path, or list of absolute paths,
            to files to copy.
        src_root (str): Root subtree of all files in *src_files*.
        dest_root (str): Destination directory in which to create the copied subtree.
        copy_function (function): Function to use to copy individual files. Must
            take two arguments, the source and destination paths, respectively.
            Defaults to :py:func:`shutil.copy2`.
        overwrite (bool): Optional, default False. Determines whether to raise
            error if files would be overwritten.

    Raises:
        :py:class:`ValueError`: If all files in *src_files* are not contained in
            the *src_root* directory.
        :py:class:`OSError`: If *overwrite* is False, raise if any destination
            files already exist, otherwise silently overwrite.
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
    """Tests if the executable *exec_name* is found on the current ``$PATH``.

    Args:
        exec_name (:py:obj:`str`): Name of the executable to search for.
    """
    return find_executable(exec_name) is not None


def get_config_file_type(file_path: str)->str:
    """Verify that configuration file is json or yaml"""
    ext = os.path.splitext(file_path)[-1].lower()

    supported_file_types = [".jsonc", ".json", ".yml"]
    if ext not in supported_file_types:
        raise exceptions.UnsupportedFileTypeError(
            f"Unsupported file type. {file_path} must be of type .json(c) or .yml")
    return ext


def find_files(src_dirs, filename_globs, n_files=None):
    """Return list of files in *src_dirs*, or any subdirectories, matching any
    of *filename_globs*. Wraps Python :py:class:`glob.glob`.

    Args:
        src_dirs: Directory, or a list of directories, to search for files in. The
            function will also search all subdirectories.
        filename_globs: Glob, or a list of globs, for filenames to match. This
            is a shell globbing pattern, not a full regex.
        n_files (int): Optional. Number of files expected to be found.

    Raises:
        :class:`~src.util.exceptions.MDTFFileNotFoundError`: If *n_files* is
            supplied and the number of files found is different than this
            number.

    Returns:
        List of paths to files matching any of the criteria. If no files are
        found, the list is empty.
    """
    src_dirs = basic.to_iter(src_dirs)
    filename_globs = basic.to_iter(filename_globs)
    files = set([])
    for d in src_dirs:
        for g in filename_globs:
            files.update(glob.glob(os.path.join(d, g)))
            files.update(glob.glob(os.path.join(d, '**', g), recursive=True))
    if n_files is not None and len(files) != n_files:
        # _log.debug('Expected to find %d files, instead found %d.', n_files, len(files))
        raise exceptions.MDTFFileNotFoundError(str(filename_globs))
    return list(files)


def check_dir(dir_path, attr_name="", create=False):
    """Check existence of directories. No action is taken for directories that
    already exist; nonexistent directories either raise a
    :class:`~util.MDTFFileNotFoundError` or cause the creation of that directory.

    Args:
        dir_path: If a string, the absolute path to check; otherwise, assume the
            path to check is given by the *attr_name* attribute on this object.
        attr_name: Name of the attribute being checked (used in log messages).
        create: (bool, default False): if True, nonexistent directories are
            created.
    """
    if not isinstance(dir_path, str):
        dir_path = getattr(dir_path, attr_name, None)
    if not isinstance(dir_path, str):
        raise ValueError(f"Expected string, received {repr(dir_path)}.")
    try:
        if not os.path.isdir(dir_path):
            if create:
                os.makedirs(dir_path, exist_ok=False)
            else:
                raise exceptions.MDTFFileNotFoundError(dir_path)
    except Exception as exc:
        if isinstance(exc, FileNotFoundError):
            path = getattr(exc, 'filename', '')
            if attr_name:
                if not os.path.exists(dir_path):
                    raise exceptions.MDTFFileNotFoundError(
                        f"{attr_name} not found at '{path}'.")
                else:
                    raise exceptions.MDTFFileNotFoundError(
                        f"{attr_name}: Path '{dir_path}' exists but is not a directory.")
            else:
                raise exceptions.MDTFFileNotFoundError(path)
        else:
            raise OSError(f"Caught exception when checking {attr_name}={dir_path}: {repr(exc)}") \
                from exc


def bump_version(path, new_v=None, extra_dirs=None):
    """Append a version number to *path*, if necessary, so that it doesn't
    conflict with existing files.

    Args:
        path (str): Path to test and append version number to.
        new_v (int): Optional. Version number to begin incrementing at.
        extra_dirs (str or iterable): Optional. If supplied, increment the version
            number of *path* so that it doesn't conflict with pre-existing files
            at these locations either.

    Returns:
        str: *path* with a version number appended to it, if *path* exists. For
        files, the version number is appended before the extension. For example,
        repeated application would create a series of files ``file.txt``,
        ``file.v1.txt``, ``file.v2.txt``, ...
    """
    def _split_version(file_):
        match = re.match(r"""
            ^(?P<file_base>.*?)   # arbitrary characters (lazy match)
            (\.v(?P<version>\d+))  # literal '.v' followed by digits
            ?                      # previous group may occur 0 or 1 times
            $                      # end of string
            """, file_, re.VERBOSE)
        if match:
            return match.group('file_base'), match.group('version')
        else:
            return file_, ''

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
    if not extra_dirs:
        dir_list = []
    else:
        dir_list = basic.to_iter(extra_dirs)
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
    return new_path, new_v

# ---------------------------------------------------------
# CONFIG FILE PARSING
# ---------------------------------------------------------


def strip_comments(str_, delimiter=None):
    """Remove comments from *str\_*. Comments are taken to start with an
    arbitrary *delimiter* and run to the end of the line.
    """
    # would be better to use shlex, but that doesn't support multi-character
    # comment delimiters like '//'
    ESCAPED_QUOTE_PLACEHOLDER = '\v' # no one uses vertical tab

    if not delimiter:
        return str_
    lines = str_.splitlines()
    for i in range(len(lines)):
        # get rid of lines starting with delimiter
        if lines[i].startswith(delimiter):
            lines[i] = ''
            continue
        # handle delimiters midway through a line:
        # If delimiter appears quoted in a string, don't want to treat it as
        # a comment. So for each occurrence of delimiter, count number of
        # "s to its left and only truncate when that's an even number.
        # First we get rid of \-escaped single "s.
        replaced_line = lines[i].replace('\\\"', ESCAPED_QUOTE_PLACEHOLDER)
        line_parts = replaced_line.split(delimiter)
        quote_counts = [s.count('"') for s in line_parts]
        j = 1
        while sum(quote_counts[:j]) % 2 != 0:
            if j >= len(quote_counts):
                raise ValueError(f"Couldn't parse line {i+1} of string.")
            j += 1
        replaced_line = delimiter.join(line_parts[:j])
        lines[i] = replaced_line.replace(ESCAPED_QUOTE_PLACEHOLDER, '\\\"')
    # make lookup table of correct line numbers, taking into account lines we
    # dropped
    line_nos = [i for i, s in enumerate(lines) if (s and not s.isspace())]
    # join lines, stripping blank lines
    new_str = '\n'.join([s for s in lines if (s and not s.isspace())])
    return new_str, line_nos


def parse_json(str_):
    """Parse JSONC (JSON with ``//``-comments) string *str\_* into a Python object.
    Comments are discarded. Wraps standard library :py:func:`json.loads`.

    Syntax errors in the input (:py:class:`~json.JSONDecodeError`) are passed
    through from the Python standard library parser. We correct the line numbers
    mentioned in the errors to refer to the original file (i.e., with comments.)
    """
    def _pos_from_lc(lineno, colno, str_):
        # fix line number, since we stripped commented-out lines. JSONDecodeError
        # computes line/col no. in error message from character position in string.
        lines = str_.splitlines()
        return (colno - 1) + sum((len(line) + 1) for line in lines[:lineno])

    (strip_str, line_nos) = strip_comments(str_, delimiter='//')
    try:
        parsed_json = json.loads(strip_str,
                                 object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as exc:
        # fix reported line number, since we stripped commented-out lines.
        assert exc.lineno <= len(line_nos)
        raise json.JSONDecodeError(
            msg=exc.msg, doc=str_,
            pos=_pos_from_lc(line_nos[exc.lineno-1], exc.colno, str_)
        )
    except UnicodeDecodeError as exc:
        raise json.JSONDecodeError(
            msg=f"parse_json received UnicodeDecodeError:\n{exc}",
            doc=strip_str, pos=0
        )

    return parsed_json


def read_json(file_path, log=_log):
    """Reads a struct from a JSONC file at *file_path*.

    Raises:
        :class:`~src.util.exceptions.MDTFFileNotFoundError`: If file not found at
            *file_path*.

    Returns:
        dict: data contained in the file, as parsed by :func:`parse_json`.

    Execution exits with error code 1 on all other exceptions.
    """
    log.debug('Reading file %s', file_path)
    try:
        with io.open(file_path, 'r', encoding='utf-8') as file_:
            str_ = file_.read()
    except Exception as exc:
        # something more serious than missing file
        _log.critical("Caught exception when trying to read %s: %r", file_path, exc)
        exit(1)
    return parse_json(str_)


def find_json(file_path, exit_if_missing=True, log=_log):
    """Reads a JSONC file

    Args:
        file_path (str): Filename to search for.
        exit_if_missing (bool): Optional, default True. Exit with error code 1
            if *file_name* not found.
        log: log file
    """
    try:
        os.path.isfile(file_path)
    except exceptions.MDTFFileNotFoundError:
        if exit_if_missing:
            _log.critical("Couldn't find file %s.", file_path)
            exit(1)
        else:
            log.debug("Couldn't find file %s; continuing.",
                      file_path)
            return dict()
    return read_json(file_path)


def write_json(struct, file_path, sort_keys=False, log=_log):
    """Serializes *struct* to a JSON file at *file_path*.

    Args:
        struct (dict): Object to serialize.
        file_path (str): path of the JSON file to write.
    """
    log.debug('Writing file %s', file_path)
    try:
        str_ = json.dumps(struct,
                          sort_keys=sort_keys,
                          indent=2,
                          separators=(',', ': '))
        with io.open(file_path, 'w', encoding='utf-8') as file_:
            file_.write(str_)
    except IOError:
        _log.critical(f'Fatal IOError when trying to write {file_path}. Exiting.')
        exit(1)


def pretty_print_json(struct, sort_keys=False):
    """Serialize *struct* to a pseudo-YAML string for human-readable debugging
    purposes only. Output is not valid JSON (or YAML).
    """
    str_ = json.dumps(struct, sort_keys=sort_keys, indent=2)
    for char in [',', '{', '}', '[', ']']:
        str_ = str_.replace(char, '')
    # remove isolated double quotes, but keep ""
    str_ = re.sub(r'(?<!\")\"(?!\")', "", str_)
    # remove lines containing only whitespace
    return os.linesep.join([s for s in str_.splitlines() if s.strip()])

# ---------------------------------------------------------
# HTML TEMPLATING
# ---------------------------------------------------------


class _DoubleBraceTemplate(string.Template):
    """Private class used by :func:`~util.append_html_template` to do
    string templating with double curly brackets as delimiters, since single
    brackets are also used in css.

    See `<https://docs.python.org/3.7/library/string.html#string.Template>`_ and
    `<https://stackoverflow.com/a/34362892>`__.
    """
    flags = re.VERBOSE  # matching is case-sensitive, unlike default
    delimiter = '{{'  # starting delimter is two braces, then apply
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
    """Perform substitutions on *template_file* and write result to *target_file*.

    Variable substitutions are done with custom
    `templating <https://docs.python.org/3.7/library/string.html#template-strings>`__,
    replacing *double* curly bracket-delimited keys with their values in *template_dict*.
    For example, if *template_dict* is ``{'A': 'foo'}``, all occurrences of the string
    ``{{A}}`` in *template_file* are replaced with the string ``foo``. Spaces between
    the braces and variable names are ignored.

    Double-curly-bracketed strings that don't correspond to keys in *template_dict*
    are ignored (instead of raising a KeyError.)

    Double curly brackets are chosen as the delimiter to match the default
    syntax of, e.g., jinja2. Using single curly braces would lead to conflicts
    with CSS syntax.

    Args:
        template_file (str): Path to template file.
        target_file (str): Destination path for result.
        template_dict (dict): Template name-value pairs. Both names
            and values must be strings.
        create (bool): Optional, default True. If True, create *target_file* if
            it doesn't exist, otherwise raise an ``OSError``.
        append (bool): Optional, default True. If *target_file* exists and this
            is True, append the substituted contents of *template_file* to it.
            If False, overwrite *target_file* with the substituted contents of
            *template_file*.
    """
    assert os.path.exists(template_file), f"Template file {template_file} not found"
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


class TempDirManager:
    _prefix = 'MDTF_temp_'
    keep_temp: bool = False
    temp_root: str = ""
    _dirs: list
    _root: str = ""
    _unittest: bool = False

    def __init__(self, config):
        self._unittest = config.unit_test
        if not hasattr(config, 'TEMP_DIR_ROOT'):
            temp_root = tempfile.gettempdir()
        else:
            temp_root = config.TEMP_DIR_ROOT
        if not self._unittest:
            assert os.path.isdir(temp_root), "Could not find temp_root directory"
        self._root = temp_root
        self._dirs = []
        self.keep_temp = config.get('keep_temp', False)

        # delete temp files if we're killed
        signal.signal(signal.SIGTERM, self.tempdir_cleanup_handler)
        signal.signal(signal.SIGINT, self.tempdir_cleanup_handler)

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
        _log.debug("Cleaning up temp dir %s", path)
        shutil.rmtree(path)

    def cleanup(self):
        if not self.keep_temp and any(self._dirs):
            for d in self._dirs:
                self.rm_tempdir(d)

    def tempdir_cleanup_handler(self, frame=None, signum=None):
        # delete temp files
        signal_logger(self.__class__.__name__, signum, frame, log=_log)
        self.cleanup()
