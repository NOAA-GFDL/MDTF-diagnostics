"""Classes to describe "abstract" properties of model data: aspects that are 
independent of any model, experiment, or hosting protocol.
"""
import abc
import collections
import dataclasses
import typing
from src import util, util_mdtf, datelabel

DMAxis = util.MDTFEnum(
    'DMAxis', 'X Y Z T OTHER', module=__name__
)

@util.mdtf_dataclass(frozen=True)
class DMCoordinate(object):
    """Class to describe a single coordinate variable (in the sense used by the
    `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__).
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
    """Class to describe a non-parametric vertical coordinate (height or depth),
    following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#vertical-coordinate>`__.
    """
    standard_name: str
    units: str = "1" # dimensionless vertical coords OK
    positive: str

    axis = DMAxis.Z

@util.mdtf_dataclass(frozen=True)
class DMParametricVerticalCoordinate(DMVerticalCoordinate):
    """Class to describe `parametric vertical coordinates
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#parametric-vertical-coordinate>`__.
    Note that the variable names appearing in ``formula_terms`` aren't parsed 
    here, in order to keep the class hashable. 
    """
    computed_standard_name: str = ""
    long_name: str = ""
    formula_terms: str = dataclasses.field(default=None, compare=False)
    # Don't include formula_terms in testing for equality, since this could 
    # reference different names for the aux coord variables.

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

# Use the "register" method, instead of inheritance, to identify these classes
# as implementations of AbstractDMCoordinate, because Python dataclass 
# fields aren't recognized as implementing an abc.abstractmethod.
AbstractDMCoordinate.register(DMCoordinate)
AbstractDMCoordinate.register(DMLongitudeCoordinate)
AbstractDMCoordinate.register(DMLatitudeCoordinate)
AbstractDMCoordinate.register(DMVerticalCoordinate)
AbstractDMCoordinate.register(DMParametricVerticalCoordinate)
AbstractDMCoordinate.register(DMTimeCoordinate)

class DMScalarCoordinateMixin(object):
    """Agument definitions of coordinates with a specific value, as in the
    CF conventions treatment of `scalar coordinates 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__.
    """
    value: typing.Union[int, float] = None

@util.mdtf_dataclass(frozen=True)
class DMScalarCoordinate(DMCoordinate, DMScalarCoordinateMixin):
    pass

@util.mdtf_dataclass(frozen=True)
class DMScalarVerticalCoordinate(DMVerticalCoordinate, DMScalarCoordinateMixin):
    pass

class AbstractDMScalarCoordinate(AbstractDMCoordinate):
    """Defines interface (set of attributes) for :class:`DMScalarCoordinate` 
    objects.
    """
    @property
    @abc.abstractmethod
    def value(self):
        pass

# Use the "register" method, instead of inheritance, to identify these classes
# as implementations of AbstractDMScalarCoordinate, because Python dataclass 
# fields aren't recognized as implementing an abc.abstractmethod.
AbstractDMScalarCoordinate.register(DMScalarCoordinate)
AbstractDMScalarCoordinate.register(DMScalarVerticalCoordinate)

@util.mdtf_dataclass
class DMCoordinateSet(object):
    # stuff for map projections, non-lat-lon horiz bookkeeping
    # also areacello/volcello, hyam/hybm
    dims: tuple
    scalar_coordinates: list
    aux_coordinates: list
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
        return (self.T is None) or (self.T.is_static)

    def replace_date_range(self, new_range):
        assert not self.is_static
        new_T = dataclasses.replace(self.T, range=new_range)
        self.T = new_T
        # still need to replace in dims


@util.mdtf_dataclass
class DMAuxiliaryCoordinate(DMCoordinateSet):
    """Class to describe `auxiliary coordinate variables 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__,
    as defined in the CF conventions. An example would be lat or lon for data 
    presented in a tripolar or other grid projection.
    """
    standard_name: str
    units: str

@util.mdtf_dataclass
class DMVariable(DMCoordinateSet):
    """Class to describe general properties of dependent (data) variables.
    """
    standard_name: str
    units: str
