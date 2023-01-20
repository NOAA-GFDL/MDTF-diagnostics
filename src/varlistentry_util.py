"""Definitions for statuses and other varlistentry attributes
"""
from src import util

# The definitions and classes in the varlistentry_util module are separate from the
# diagnostic module to prevent circular module imports
VarlistEntryRequirement = util.MDTFEnum(
    'VarlistEntryRequirement',
    'REQUIRED OPTIONAL ALTERNATE AUX_COORDINATE',
    module=__name__
)
VarlistEntryRequirement.__doc__ = """
:class:`util.MDTFEnum` used to track whether the DataSource is required to
provide data for the :class:`VarlistEntry`.
"""

VarlistEntryStage = util.MDTFIntEnum(
    'VarlistEntryStage',
    'NOTSET INITED QUERIED FETCHED PREPROCESSED',
    module=__name__
)
VarlistEntryStage.__doc__ = """
:class:`util.MDTFIntEnum` used to track the stages of processing of a
:class:`VarlistEntry` carried out by the DataSource.
"""
