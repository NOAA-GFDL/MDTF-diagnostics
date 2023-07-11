"""Classes which parse the framework's command line interface configuration files
and implement the dynamic CLI; see :doc:`fmwk_cli`.

Familiarity with the python :py:mod:`argparse` module is recommended.
"""
import os
import sys
import io
import click
import pathlib
import collections
import dataclasses
import importlib
import itertools
import json
import operator

import typing
import yaml
import intake
from datetime import datetime, date
from src import util

import logging

_log = logging.getLogger(__name__)


def read_config_files(CODE_ROOT, file_name, site=""):
    """Utility function to read a pair of configuration files: one for the
    framework defaults, another optional one for site-specific configuration.

    Args:
        CODE_ROOT (str): Code repo directory.
        file_name (str): Name of file to search for. We search for the file
            in all subdirectories of :meth:`CLIConfigManager.site_dir`
            and :meth:`CLIConfigManager.framework_dir`, respectively.
        site (str): Name of the site-specific directory (in ``/sites``) to search.

    Returns:
        A tuple of the two files' contents. First element is the
        site specific file (empty dict if that file isn't found) and second
        is the framework file (if not found, fatal error and exit immediately.)
    """
    src_dir = os.path.join(CODE_ROOT, 'src')
    site_dir = os.path.join(CODE_ROOT, 'sites', site)
    site_d = util.find_json(site_dir, file_name, exit_if_missing=False, log=_log)
    fmwk_d = util.find_json(src_dir, file_name, exit_if_missing=True, log=_log)
    return site_d, fmwk_d


def read_config_file(code_root: str, file_name: str, site: str = ""):
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


def load_yaml_config(config: str) -> util.NameSpace:
    try:
        os.path.exists(config)
    except FileNotFoundError:
        exc = util.exceptions.MDTFFileExistsError(
            f"{config} not found")
        _log.exception(exc)

    with open(config, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())
        return util.NameSpace.fromDict({k: yaml_dict[k] for k in yaml_dict.keys()})


def load_json_config(config: str) -> util.NameSpace:
    try:
        os.path.exists(config)
    except FileNotFoundError:
        exc = util.exceptions.MDTFFileExistsError(
            f"{config} not found")
        _log.exception(exc)
    json_config = util.read_json(config, log=_log)
    return util.NameSpace.fromDict({k: json_config[k] for k in json_config.keys()})


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
            exc = util.exceptions.MDTFFileExistsError(
                f"settings file not found in {pod_root}")
            _log.exception(exc)


def verify_catalog(catalog_path: str):
    # verify the catalog file path
    try:
        os.path.exists(catalog_path)
    except FileNotFoundError:
        raise util.exceptions.MDTFFileExistsError(
            f"{catalog_path} not found.")


def verify_dirpath(dirpath: str, code_root: str) -> str:
    dirpath_parts = pathlib.Path(dirpath)
    # replace relative path with absolute working directory path
    if ".." in dirpath_parts.parts:
        new_dirpath = os.path.realpath(os.path.join(code_root, dirpath))
    else:
        new_dirpath = dirpath
    if not os.path.exists(new_dirpath):
        os.mkdir(new_dirpath)
        _log.debug(f"Created directory {new_dirpath}")
    try:
        os.path.isdir(new_dirpath)
    except FileNotFoundError:
        exc = util.exceptions.MDTFFileNotFoundError(
            f"{new_dirpath} not found")
        _log.exception(exc)

    return new_dirpath


def verify_case_atts(case_list: util.NameSpace):
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
            att_dict.convention.lower() in conventions
        except KeyError:
            raise util.exceptions.MDTFBaseException(
                f"Convention {att_dict['convention']} not supported"
            )
        if len(att_dict.startdate) == 8 and len(att_dict.enddate) == 8:
            try:
                st = datetime.strptime(att_dict.startdate, '%Y%m%d')
                ed = datetime.strptime(att_dict.enddate, '%Y%m%d')
            except KeyError:
                raise util.exceptions.MDTFBaseException(
                    f"Expected {att_dict.startdate} and {att_dict.enddate} to have yyyymmdd format"
                )
        else:
            try:
                st = datetime.strptime(att_dict.startdate, '%Y%m%d:%H%M%S')
                ed = datetime.strptime(att_dict.enddate, '%Y%m%d:%H%M%S')
            except KeyError:
                raise util.exceptions.MDTFBaseException(
                    f"{att_dict.startdate} and {att_dict.enddate} "
                    f"must have yyyymmdd or yyyymmdd:HHMMSS format."
                )


def update_config(config: util.NameSpace, key: str, new_value):
    config_dict = util.NameSpace.toDict(config)
    if config_dict[key] != new_value:
        config.update({key: new_value})


def verify_runtime_config_options(config: util.NameSpace):
    verify_pod_list(config.pod_list, config.CODE_ROOT)
    verify_catalog(config.DATA_CATALOG)
    new_workdir = verify_dirpath(config.WORK_DIR, config.CODE_ROOT)
    update_config(config, 'WORK_DIR', new_workdir)
    if any(config.OBS_DATA_ROOT):
        new_obs_data_path = verify_dirpath(config.OBS_DATA_ROOT, config.CODE_ROOT)
        update_config(config, 'OBS_DATA_ROOT', new_obs_data_path)
    if any(config.OUTPUT_DIR) and config.OUTPUT_DIR != config.WORK_DIR:
        new_output_dir = verify_dirpath(config.OUTPUT_DIR, config.CODE_ROOT)
        update_config(config, 'OUTPUT_DIR', new_output_dir)
    verify_case_atts(config.case_list)
