"""Classes to describe "abstract" properties of model data: aspects that are 
independent of any model, experiment, or hosting protocol.
"""
import abc
import collections
import dataclasses
import itertools
import typing
from src import util, datelabel

DMAxis = util.MDTFEnum(
    'DMAxis', 'X Y Z T OTHER', module=__name__
)
DMAxis.spatiotemporal_names = ('X', 'Y', 'Z', 'T')
DMAxis.__doc__ = """:py:class:`~enum.Enum` encoding the recognized axis types
(dimension coordinates with a distinguished role.)
"""

@util.mdtf_dataclass
class DMCoordinate(object):
    """Class to describe a single coordinate variable (in the sense used by the
    `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__).
    """
    name: str
    standard_name: str
    units: str
    axis: DMAxis = DMAxis.OTHER

@util.mdtf_dataclass
class DMLongitudeCoordinate(object):
    name: str
    
    standard_name = 'longitude'
    units = 'degrees_E'
    axis = DMAxis.X

@util.mdtf_dataclass
class DMLatitudeCoordinate(object):
    name: str

    standard_name = 'latitude'
    units = 'degrees_N'
    axis = DMAxis.Y

@util.mdtf_dataclass
class DMVerticalCoordinate(object):
    """Class to describe a non-parametric vertical coordinate (height or depth),
    following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#vertical-coordinate>`__.
    """
    name: str
    standard_name: str
    units: str = "1" # dimensionless vertical coords OK
    positive: str

    axis = DMAxis.Z

@util.mdtf_dataclass
class DMParametricVerticalCoordinate(DMVerticalCoordinate):
    """Class to describe `parametric vertical coordinates
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#parametric-vertical-coordinate>`__.
    Note that the variable names appearing in ``formula_terms`` aren't parsed 
    here, in order to keep the class hashable. 
    """
    name: str
    computed_standard_name: str = ""
    long_name: str = ""
    formula_terms: str = dataclasses.field(default=None, compare=False)
    # Don't include formula_terms in testing for equality, since this could 
    # reference different names for the aux coord variables.

@util.mdtf_dataclass
class DMTimeCoordinate(object):
    name: str
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
    def name(self):
        pass

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

@util.mdtf_dataclass
class DMScalarCoordinateMixin(object):
    """Agument definitions of coordinates with a specific value, as in the
    CF conventions treatment of `scalar coordinates 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__.
    """
    value: typing.Union[int, float] = None

@util.mdtf_dataclass
class DMScalarCoordinate(DMCoordinate, DMScalarCoordinateMixin):
    pass

@util.mdtf_dataclass
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
class DMDimensions(object):
    """Lookups for the dimensions, and associated dimension coordinates, 
    associated with an array (eg a variable or auxiliary coordinate.)
    """
    dims: tuple
    scalar_coords: set = dataclasses.field(default_factory=set)
    axes: dict = dataclasses.field(init=False)
    phys_axes: dict = dataclasses.field(init=False)

    def __post_init__(self):
        # validate that we don't have duplicate axes
        temp_d = dict()
        for c in itertools.chain(self.dims, self.scalar_coords):
            axis = getattr(c.axis, 'name', '')
            if axis != 'OTHER' and axis in temp_d:
                raise ValueError((f"Duplicate definition of {axis} axis:"
                        f"{str(c)}, {str(temp_d[axis])}"))
            temp_d[axis] = c

        self.axes = dict((x, None) for x in DMAxis.spatiotemporal_names)
        for c in self.dims:
            axis = getattr(c.axis, 'name', '')
            if axis in DMAxis.spatiotemporal_names:
                self.axes[axis] = c
        self.phys_axes = self.axes.copy()
        for c in self.scalar_coords:
            axis = getattr(c.axis, 'name', '')
            if axis in DMAxis.spatiotemporal_names:
                self.phys_axes[axis] = c

    @property
    def X(self):
        return self.axes['X']

    @property
    def Y(self):
        return self.axes['Y']

    @property
    def Z(self):
        return self.axes['Z']

    @property
    def T(self):
        return self.axes['T']

    @property
    def is_static(self):
        return (self.T is None) or (self.T.is_static)

    def replace_date_range(self, new_range):
        assert not self.is_static
        new_T = dataclasses.replace(self.T, range=new_range)
        self.T = new_T

@util.mdtf_dataclass
class DMAuxiliaryCoordinate(DMDimensions):
    """Class to describe `auxiliary coordinate variables 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__,
    as defined in the CF conventions. An example would be lat or lon for data 
    presented in a tripolar grid projection.
    """
    name: str
    standard_name: str
    units: str

@util.mdtf_dataclass
class DMVariable(DMDimensions):
    """Class to describe general properties of data (dependent) variables.
    """
    name: str
    standard_name: str
    units: str
