#!/usr/env/bin/python3
# test script for read_json utility
import os
import io
import sys
import collections
import json
import re
from src.util import strip_comments


# jsonc reading and parsing routines from util.filesystem
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
        return (colno - 1) + sum( (len(line) + 1) for line in lines[:lineno])

    (strip_str, line_nos) = strip_comments(str_, delimiter= '//')
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


def read_json(file_path):
    """Reads a struct from a JSONC file at *file_path*.

    Raises:
        :class:`~src.util.exceptions.MDTFFileNotFoundError`: If file not found at
            *file_path*.

    Returns:
        dict: data contained in the file, as parsed by :func:`parse_json`.

    Execution exits with error code 1 on all other exceptions.
    """
    print('Reading file %s', file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    try:
        with io.open(file_path, 'r', encoding='utf-8') as file_:
            str_ = file_.read()
    except Exception as exc:
        # something more serious than missing file
        print("Caught exception when trying to read %s: %r", file_path, exc)
        exit(1)
    return parse_json(str_)


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


def main():
    code_root = "/home/jessica.liptak/mdtf/MDTF-diagnostics"
    file_name = "src/multirun_config_template.jsonc"
    file_name_og = "src/default_tests.jsonc"
    json_obj_og = read_json(os.path.join(code_root, file_name_og))

    if json_obj_og.get('case_list') is None:
        print("ERROR: case_list not present in", json_obj_og)
        sys.exit(1)
    if json_obj_og.get('pod_list') is None:
        print('pod_list not present; framework will run in non-multirun mode')
    else:
        print('Found pod list separate from case list. Framework will use multirun mode. ')
    json_obj = read_json(os.path.join(code_root, file_name))
    case_list = json_obj.get('case_list')
    pod_list = json_obj_og.get('pod_list')
    num_cases = len(case_list)

    # example of accessing known key name in first case_list element
    print(case_list[0].get('CASENAME'))
    # access each case dictionary in case_list
    for cl in case_list:
        # dict for each case/ensemble member
        for key, val in cl.items():
            # case keys and values
            print(key, val)
    return case_list
if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
