"""Classes which parse the framework's command line interface configuration files
and implement the dynamic CLI.
"""
import os
import pathlib
import yaml
from datetime import datetime
from src import util

import logging

_log = logging.getLogger(__name__)


def read_config_file(code_root: str, file_dir: str, file_name: str) -> str:
    """Return the site's config file if present, else the framework's file. Wraps
    :func:`read_config_files`.

    Args:
        code_root (str): Code repo directory.
        file_dir (str): subdirectory name or path in code_root that contains target file
        file_name (str): Name of file to search for.

    Returns:
        Path to the configuration file.
    """
    file_dir = os.path.join(code_root, file_dir, file_name)
    return util.find_json(file_dir, exit_if_missing=True, log=_log)


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


def check_date_format(date_string: str):
    """ Check that the input start and end dates adhere to accepted formats
        Credit: https://stackoverflow.com/questions/23581128/how-to-format-date-string-via-multiple-formats-in-python
    """

    for fmt in ('%Y', '%Y%m', '%Y-%m', '%Y%m%d',
                '%Y-%m-%d', '%Y-%m-%d:%H:%M:%S', '%Y%m%d:%H%M%S',
                '%Y-%m-%d:%H-%M-%S', '%Y%m%d%H%M%S'):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    raise util.exceptions.MDTFBaseException(
                f"Input date string {date_string} does not match accepted formats: YYYY, YYYYmm,"
                f" YYYY-mm, YYYY-mm-dd, YYYYmmdd,"
                f"YYYYmmdd:HHMMSS, YYYY-mm-dd:HH:MM:SS, YYYY-mm-dd:HH-MM-SS"
            )


def verify_case_atts(case_list: util.NameSpace):
    # required case attributes
    required_case_attrs = {'convention', 'startdate', 'enddate'}
    optional_case_attrs = {'realm', 'model'}
    conventions = {'cmip', 'gfdl', 'cesm'}
    for name, att_dict in case_list.items():
        try:
            all(att in att_dict.keys() for att in required_case_attrs)
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
        try:
            {att for att in att_dict.keys()}.issubset(required_case_attrs.union(optional_case_attrs))
        except KeyError:
            raise util.exceptions.MDTFBaseException(f"Runtime case attribute is not a required or optional attribute. Check runtime config file for typo or unsupported entry.")

        st = check_date_format(att_dict.startdate)
        en = check_date_format(att_dict.enddate)


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

def verify_conda_envs(config: util.NameSpace, filename: str):
    m_exists = os.path.exists(config['micromamba_exe'])
    c_exists = os.path.exists(config['conda_root'])
    cenv_exists = os.path.exists(config['conda_env_root'])
    if not m_exists and not c_exists:
        raise util.exceptions.MDTFBaseException(
            f"Could not find conda or micromamba executable; please check the runtime config file: "
            f'{filename}'
        ) 
    if c_exists and not cenv_exists:
        new_env_root = os.path.join(config['conda_root'], "envs")
        if os.path.exists(new_env_root):
            config.update({'conda_env_root':new_env_root})
        else:
            raise util.exceptions.MDTFBaseException(
                f"Count not find conda enviroment directory; please check the runtime config file: "
                f'{filename}'
            )

    return config

