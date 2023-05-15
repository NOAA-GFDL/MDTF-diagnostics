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
    except FileExistsError:
        raise util.exceptions.MDTFFileExistsError(
            f"{config} not found")

    with open(config, 'r') as f:
        return yaml.safe_load(f.read())


def load_json_config(config: str) -> dict:
    try:
        os.path.exists(config)
    except FileExistsError:
        raise util.exceptions.MDTFFileExistsError(
            f"{config} not found")
    json_config = util.read_json(config, log=_log)
    return json_config


def parse_config_file(configfile: str) -> dict:
    """Command line interface"""
    ext = util.get_config_file_type(configfile)
    if ext == ".yml":
        config = load_yaml_config(configfile)
    elif ext in [".jsonc", ".json"]:
        config = load_json_config(configfile)
    return config
