"""Classes which parse the framework's command line interface configuration files
and implement the dynamic CLI; see :doc:`fmwk_cli`.

Familiarity with the python :py:mod:`argparse` module is recommended.
"""
import os
import sys
import io
import click
import argparse
import collections
import dataclasses
import importlib
import itertools
import json
import operator
import shlex
import re
import textwrap
import typing
import yaml
import intake
from datetime import datetime,date
from src import util

import logging

_log = logging.getLogger(__name__)

_SCRIPT_NAME = 'mdtf.py'  # mimic argparse error message text


def canonical_arg_name(str_):
    """Convert a flag or other specification to a destination variable name.
    The destination variable name always has underscores, never hyphens, in
    accordance with PEP8.

    E.g., ``canonical_arg_name('--GNU-style-flag')`` returns "GNU_style_flag".
    """
    return str_.lstrip('-').rstrip().replace('-', '_')


def plugin_key(plugin_name):
    """Convert user input for plugin options to string used to lookup plugin
    value from options defined in cli_plugins.jsonc files.

    Ignores spaces and underscores in supplied choices for CLI plugins, and
    make matching of plugin names case-insensititve.
    """
    return re.sub(r"[\s_]+", "", plugin_name).lower()


def word_wrap(str_):
    """Clean whitespace and perform 80-column word wrapping for multi-line help
    and description strings. Explicit paragraph breaks must be encoded as a
    double newline \(``\\n\\n``\).
    """
    paragraphs = textwrap.dedent(str_).split('\n\n')
    paragraphs = [re.sub(r'\s+', ' ', s).strip() for s in paragraphs]
    paragraphs = [textwrap.fill(s, width=80) for s in paragraphs]
    return '\n\n'.join(paragraphs)


def read_config_files(code_root, file_name, site=""):
    """Utility function to read a pair of configuration files: one for the
    framework defaults, another optional one for site-specific configuration.

    Args:
        code_root (str): Code repo directory.
        file_name (str): Name of file to search for. We search for the file
            in all subdirectories of :meth:`CLIConfigManager.site_dir`
            and :meth:`CLIConfigManager.framework_dir`, respectively.
        site (str): Name of the site-specific directory (in ``/sites``) to search.

    Returns:
        A tuple of the two files' contents. First element is the
        site specific file (empty dict if that file isn't found) and second
        is the framework file (if not found, fatal error and exit immediately.)
    """
    src_dir = os.path.join(code_root, 'src')
    site_dir = os.path.join(code_root, 'sites', site)
    site_d = util.find_json(site_dir, file_name, exit_if_missing=False, log=_log)
    fmwk_d = util.find_json(src_dir, file_name, exit_if_missing=True, log=_log)
    return site_d, fmwk_d


def read_config_file(code_root, file_name, site=""):
    """Return the site's config file if present, else the framework's file. Wraps
    :func:`read_config_files`.

    Args:
        code_root (str): Code repo directory.
        file_name (str): Name of file to search for. We search for the file
            in all subdirectories of :meth:`CLIConfigManager.site_dir`
            and :meth:`CLIConfigManager.framework_dir`, respectively.
        site (str): Name of the site-specific directory (in ``/sites``) to search.

    Returns:
        Path to the configuration file.
    """
    site_d, fmwk_d = read_config_files(code_root, file_name, site=site)
    if not site_d:
        return fmwk_d
    return site_d


def load_yaml_config(config: str) -> dict:
    try:
        os.path.exists(config)
    except FileNotFoundError:
        raise util.exceptions.MDTFFileExistsError(
            f"{config} not found")

    with open(config, 'r') as f:
        return yaml.safe_load(f.read())


def load_json_config(config: str) -> dict:
    try:
        os.path.exists(config)
    except FileNotFoundError:
        raise util.exceptions.MDTFFileExistsError(
            f"{config} not found")
    json_config = util.read_json(config, log=_log)
    return json_config


def parse_config_file(configfile: str) -> dict:
    """Command line interface"""
    ext = util.get_config_file_type(configfile)
    if ext == ".yml":
        return load_yaml_config(configfile)
    elif ext in [".jsonc", ".json"]:
        return load_json_config(configfile)


def verify_pod_list(pod_list: list, code_root: str):
    pod_data_root = os.path.join(code_root, "diagnostics")
    for p in pod_list:
        pod_root = os.path.join(pod_data_root, p)
        try:
            not (not os.path.exists(os.path.join(pod_root, "settings.jsonc"))
                 and not os.path.exists(os.path.join(pod_root, "settings.yml")))
        except FileNotFoundError:
            raise util.exceptions.MDTFFileExistsError(
                f"settings file not found in {pod_root}")


def verify_catalog(catalog_path: str):
    # verify the catalog file path
    try:
        os.path.exists(catalog_path)
    except FileNotFoundError:
        raise util.exceptions.MDTFFileExistsError(
            f"{catalog_path} not found.")


def verify_workdir(workdir: str):
    if not os.path.exists(workdir):
        os.mkdir(os.path.join(workdir))


def verify_case_atts(case_list: dict):
    # required case attributes
    case_attrs = ['convention', 'startdate', 'enddate']
    conventions = ['cmip', 'gfdl', 'cesm']
    for name, att_dict in case_list.items():
        try:
            all(att in att_dict.keys() for att in case_attrs)
        except KeyError:
            raise util.exceptions.MDTFBaseException(
                f"Missing or incorrect convention, startdate, or enddate for case {name}"
            )
        try:
            att_dict['convention'].lower() in conventions
        except KeyError:
            raise util.exceptions.MDTFBaseException(
                f"Convention {att_dict['convention']} not supported"
            )
        try:
            st = datetime.strptime(att_dict['startdate'], 'yyyymmddhhmmss')
            ed = datetime.fromisoformat(att_dict['enddate'])
        except KeyError:
            raise util.exceptions.MDTFBaseException(
                f"{att_dict['startdate']} and {att_dict['enddate']} must have format yyyymmdd"
            )



def verify_config_options(config: dict):
    verify_pod_list(config['pod_list'], config['code_root'])
    verify_catalog(config['DATA_CATALOG'])
    verify_workdir(config['WORK_DIR'])
    verify_case_atts(config['case_list'])
