"""Utilities for Anaconda/Miniconda environments
"""
import os
import logging
_log = logging.getLogger(__name__)


def verify_conda_env(conda_env: str):
    try:
        assert conda_env in os.path.split(os.environ['CONDA_PREFIX'])
    except AssertionError as e:
        _log.debug(f"{e} {conda_env} not activated")
