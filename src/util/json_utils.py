"""Utility functions for reading and manipulating json files
"""
import os
import io
import collections
import json
import re
from . import exceptions

import logging

_log = logging.getLogger(__name__)


def get_config_file_type(file_path: str)->str:
    """Verify that configuration file is json or yaml"""
    ext = os.path.splitext(file_path)[-1].lower()

    supported_file_types = [".jsonc", ".json", ".yml"]
    if ext not in supported_file_types:
        raise exceptions.UnsupportedFileTypeError(
            f"Unsupported file type. {file_path} must be of type .json(c) or .yml")
    return ext


def strip_comments(str_, delimiter=None):
    """Remove comments from *str\_*. Comments are taken to start with an
    arbitrary *delimiter* and run to the end of the line.
    """
    # would be better to use shlex, but that doesn't support multi-character
    # comment delimiters like '//'
    ESCAPED_QUOTE_PLACEHOLDER = '\v'  # no one uses vertical tab

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
        sort_keys (bool): parameter indicating whether to sort keys to pass to json.dumps
        log (logging.getlogger): log object
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
