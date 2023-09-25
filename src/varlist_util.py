"""Classes that define varlist coordinates and other attributes
"""
import dataclasses as dc
import typing
from abc import ABC
from src import util, data_model

# The definitions and classes in the varlist_util module are separate from the
# diagnostic module to prevent circular module imports

PodDataFileFormat = util.MDTFEnum(
    'PodDataFileFormat',
    ("ANY_NETCDF ANY_NETCDF_CLASSIC "
     "ANY_NETCDF3 NETCDF3_CLASSIC NETCDF_64BIT_OFFSET NETCDF_64BIT_DATA "
     "ANY_NETCDF4 NETCDF4_CLASSIC NETCDF4"),
    module=__name__
)


@util.mdtf_dataclass
class _VarlistGlobalSettings(object):
    format: PodDataFileFormat = \
        dc.field(default=PodDataFileFormat.ANY_NETCDF_CLASSIC, metadata={'query': True})
    rename_variables: bool = False
    multi_file_ok: bool = False
    dimensions_ordered: bool = False


@util.mdtf_dataclass
class _VarlistTimeSettings(object):
    frequency:     util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    max_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_duration: str = util.NOTSET
    max_duration: str = util.NOTSET


@util.mdtf_dataclass
class VarlistSettings(_VarlistGlobalSettings, _VarlistTimeSettings):
    """Class to describe options affecting all variables requested by this POD.
    Corresponds to the "data" section of the POD's settings.jsonc file.
    """
    @property
    def global_settings(self):
        return util.filter_dataclass(self, _VarlistGlobalSettings)

    @property
    def time_settings(self):
        return util.filter_dataclass(self, _VarlistTimeSettings)


@util.mdtf_dataclass
class VarlistCoordinateMixin(object):
    """Base class to describe a single dimension (in the netcdf data model sense)
    used by one or more variables. Corresponds to list entries in the
    "dimensions" section of the POD's settings.jsonc file.
    """
    need_bounds: bool = False


@util.mdtf_dataclass
class VarlistCoordinate(data_model.DMCoordinate, VarlistCoordinateMixin):
    # name: str              # fields from data_model.DMCoordinate
    # standard_name: str
    # units: units.Units
    # axis: str
    # bounds: AbstractDMCoordinateBounds
    # value: typing.Union[int, float] # for scalar coordinates only
    # need_bounds: bool      # fields from VarlistCoordinateMixin
    # name_in_model: str
    # bounds_in_model: str
    pass


@util.mdtf_dataclass
class VarlistLongitudeCoordinate(data_model.DMLongitudeCoordinate,
                                 VarlistCoordinateMixin):
    range: tuple = None


@util.mdtf_dataclass
class VarlistLatitudeCoordinate(data_model.DMLatitudeCoordinate,
                                VarlistCoordinateMixin):
    range: tuple = None


@util.mdtf_dataclass
class VarlistVerticalCoordinate(data_model.DMVerticalCoordinate,
                                VarlistCoordinateMixin):
    pass


@util.mdtf_dataclass
class VarlistPlaceholderTimeCoordinate(data_model.DMGenericTimeCoordinate,
                                       VarlistCoordinateMixin):
    frequency: typing.Any = ""
    min_frequency: typing.Any = ""
    max_frequency: typing.Any = ""
    min_duration: typing.Any = 'any'
    max_duration: typing.Any = 'any'

    standard_name = 'time'
    axis = 'T'


@util.mdtf_dataclass
class VarlistTimeCoordinate(_VarlistTimeSettings, data_model.DMTimeCoordinate,
                            VarlistCoordinateMixin, ABC):
    pass
