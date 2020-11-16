"""Classes to describe "abstract" properties of model data: aspects that are 
independent of any model, experiment, or hosting protocol.
"""
import abc
import collections
import dataclasses
from src import util, util_mdtf, datelabel

DMAxis = util.MDTFEnum(
    'DMAxis', 'X Y Z T OTHER', module=__name__
)

@util.mdtf_dataclass(frozen=True)
class DMCoordinate(object):
    """Class to describe a single coordinate (in the netcdf data model sense)
    used by one or more variables.
    """
    standard_name: str
    units: str
    axis: DMAxis = DMAxis.OTHER

@util.mdtf_dataclass(frozen=True)
class DMLongitudeCoordinate(object):
    standard_name = 'longitude'
    units = 'degrees_E'
    axis = DMAxis.X

@util.mdtf_dataclass(frozen=True)
class DMLatitudeCoordinate(object):
    standard_name = 'latitude'
    units = 'degrees_N'
    axis = DMAxis.Y

@util.mdtf_dataclass(frozen=True)
class DMVerticalCoordinate(object):
    standard_name: str
    units: str
    positive: str

    axis = DMAxis.Z

@util.mdtf_dataclass(frozen=True)
class DMTimeCoordinate(object):
    units: str
    calendar: str
    range: datelabel.AbstractDateRange = None
    frequency: datelabel.AbstractDateFrequency = None

    standard_name = 'time'
    axis = DMAxis.T

    @property
    def is_static(self):
        """Check for time-independent data ('fx' in CMIP6 DRS.) Do the comparison
        by checking date_range against the placeholder value because that's
        unique -- we may be using a different DateFrequency depending on the
        data source.
        """
        return (self.range == datelabel.FXDateRange)

class AbstractDMCoordinate(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMCoordinate` objects.
    """
    @property
    @abc.abstractmethod
    def standard_name(self):
        pass

    @property
    @abc.abstractmethod
    def units(self):
        pass

    @property
    @abc.abstractmethod
    def axis(self):
        pass

# Use the "register" method, instead of inheritance, to identify the 
# DM*Coordinate classes as implementations of AbstractDMCoordinate, because 
# Python dataclass fields aren't recognized as implementing an abc.abstractmethod.
AbstractDMCoordinate.register(DMCoordinate)
AbstractDMCoordinate.register(DMLongitudeCoordinate)
AbstractDMCoordinate.register(DMLatitudeCoordinate)
AbstractDMCoordinate.register(DMVerticalCoordinate)
AbstractDMCoordinate.register(DMTimeCoordinate)

@util.mdtf_dataclass
class DMCoordinateSet(object):
    # stuff for map projections, non-lat-lon horiz bookkeeping
    # also areacello/volcello, hyam/hybm
    coords: tuple
    X: AbstractDMCoordinate = dataclasses.field(init=False, default=None)
    Y: AbstractDMCoordinate = dataclasses.field(init=False, default=None)
    Z: AbstractDMCoordinate = dataclasses.field(init=False, default=None)
    T: AbstractDMCoordinate = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        for d in self.coords:
            axis = getattr(d.axis, 'name', '')
            if axis in ('X', 'Y', 'Z', 'T'):
                setattr(self, axis, d)

    @property
    def is_static(self):
        return (self.T is None)

@util.mdtf_dataclass
class DMVariable(DMCoordinateSet):
    """Class to describe general properties of datasets.
    """
    standard_name: str
    units: str
    scalar_coordinates: dict = dataclasses.field(default_factory=dict)
