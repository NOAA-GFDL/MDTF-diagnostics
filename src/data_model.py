"""Classes to describe "abstract" properties of model data: aspects that are 
independent of any model, experiment, or hosting protocol.
"""
import abc
import collections
import dataclasses
import itertools
import typing
from src import util, datelabel

class AbstractDMCoordinate(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMCoordinate` objects.
    """
    @property
    @abc.abstractmethod
    def name(self): pass

    @property
    @abc.abstractmethod
    def standard_name(self): pass

    @property
    @abc.abstractmethod
    def units(self): pass

    @property
    @abc.abstractmethod
    def axis(self): pass

    @property
    @abc.abstractmethod
    def bounds(self): pass

    @property
    @abc.abstractmethod
    def value(self): pass

    @property
    @abc.abstractmethod
    def is_scalar(self): pass

    @property
    @abc.abstractmethod
    def has_bounds(self): pass

class AbstractDMDependentVariable(abc.ABC):
    """Defines interface (set of attributes) for "dependent variables" (data 
    defined as a function of one or more dimension coordinates), which inherit 
    from :class:`DMDimensions` in this implementation.
    """
    @property
    @abc.abstractmethod
    def name(self): pass

    @property
    @abc.abstractmethod
    def standard_name(self): pass

    @property
    @abc.abstractmethod
    def units(self): pass

    @property
    @abc.abstractmethod
    def dims(self): pass

    @property
    @abc.abstractmethod
    def scalar_coords(self): pass

    @property
    @abc.abstractmethod
    def axes(self): pass

    @property
    @abc.abstractmethod
    def phys_axes(self): pass

    @property
    @abc.abstractmethod
    def X(self): pass

    @property
    @abc.abstractmethod
    def Y(self): pass

    @property
    @abc.abstractmethod
    def Z(self): pass

    @property
    @abc.abstractmethod
    def T(self): pass

    @property
    @abc.abstractmethod
    def is_static(self): pass

class AbstractDMCoordinateBounds(AbstractDMDependentVariable):
    """Defines interface (set of attributes) for :class:`DMCoordinateBounds` 
    objects.
    """
    @property
    @abc.abstractmethod
    def coord(self): pass

# ------------------------------------------------------------------------------

DMAxis = util.MDTFEnum(
    'DMAxis', 'X Y Z T BOUNDS OTHER', module=__name__
)
DMAxis.spatiotemporal_names = ('X', 'Y', 'Z', 'T')
DMAxis.__doc__ = """:py:class:`~enum.Enum` encoding the recognized axis types
(dimension coordinates with a distinguished role.)
"""

@util.mdtf_dataclass(frozen=True)
class DMBoundsDimension(object):
    """Placeholder object to represent the bounds dimension of a 
    :class:`DMCoordinateBounds` object. Not a dimension coordinate, and strictly
    speaking we should make another set of classes for dimensions.
    """
    name: str = util.MANDATORY
    
    standard_name = 'bounds'
    units = '1'
    axis = DMAxis.BOUNDS
    bounds = None
    value = None

    @property
    def has_bounds(self):
        return False

    @property
    def is_scalar(self):
        return False

@util.mdtf_dataclass(frozen=True)
class _DMCoordinateShared(object):
    """Fields common to all :class:`AbstractDMCoordinate` child classes which
    aren't fixed to particular values.

    ``value`` is our mechanism for implementing CF convention `scalar coordinates 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__.
    """
    name: str = util.MANDATORY
    bounds: AbstractDMCoordinateBounds = None
    value: typing.Union[int, float] = None

    @property
    def has_bounds(self):
        return (self.bounds is not None)

    @property
    def is_scalar(self):
        return (self.value is not None)

    def make_scalar(self, new_value):
        return dataclasses.replace(self, value=new_value)

@util.mdtf_dataclass(frozen=True)
class DMCoordinate(_DMCoordinateShared):
    """Class to describe a single coordinate variable (in the sense used by the
    `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__).
    """
    standard_name: str = util.MANDATORY
    units: str = util.MANDATORY
    axis: DMAxis = DMAxis.OTHER

@util.mdtf_dataclass(frozen=True)
class DMLongitudeCoordinate(_DMCoordinateShared):
    standard_name = 'longitude'
    units = 'degrees_E'
    axis = DMAxis.X

@util.mdtf_dataclass(frozen=True)
class DMLatitudeCoordinate(_DMCoordinateShared):
    standard_name = 'latitude'
    units = 'degrees_N'
    axis = DMAxis.Y

@util.mdtf_dataclass(frozen=True)
class DMVerticalCoordinate(_DMCoordinateShared):
    """Class to describe a non-parametric vertical coordinate (height or depth),
    following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#vertical-coordinate>`__.
    """
    standard_name: str = util.MANDATORY
    units: str = "1" # dimensionless vertical coords OK
    positive: str = util.MANDATORY

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
    # Don't include formula_terms in testing for equality, since this could 
    # reference different names for the aux coord variables.
    # TODO: resolve names in formula_terms to references to objects in the data
    # model.
    formula_terms: str = dataclasses.field(default=None, compare=False)

@util.mdtf_dataclass(frozen=True)
class DMTimeCoordinate(_DMCoordinateShared):
    units: str = util.MANDATORY
    calendar: str = util.MANDATORY
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

# Use the "register" method, instead of inheritance, to associate these classes
# with their corresponding abstract interfaces, because Python dataclass fields 
# aren't recognized as implementing an abc.abstractmethod.
AbstractDMCoordinate.register(DMCoordinate)
AbstractDMCoordinate.register(DMLongitudeCoordinate)
AbstractDMCoordinate.register(DMLatitudeCoordinate)
AbstractDMCoordinate.register(DMVerticalCoordinate)
AbstractDMCoordinate.register(DMParametricVerticalCoordinate)
AbstractDMCoordinate.register(DMTimeCoordinate)
AbstractDMCoordinate.register(DMBoundsDimension)


class _DMDimensionsMixin(object):
    """Lookups for the dimensions, and associated dimension coordinates, 
    associated with an array (eg a variable or auxiliary coordinate.) Needs to 
    be included as a parent class of a dataclass.
    """
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

    @classmethod
    def from_dimensions(cls, dm_dimensions, **kwargs):
        """Constructor for use by child classes. Preserves references to the
        shared set of dims and scalar_coords, since python is pass-by-reference.
        """
        kwargs.setdefault('dims', dm_dimensions.dims)
        kwargs.setdefault('scalar_coords', dm_dimensions.scalar_coords)
        return cls(**kwargs)

    def build_axes(self, *coords):
        # validate types
        for c in self.dims:
            if c.is_scalar:
                raise ValueError((f"Scalar coordinate {c} supplied as dimension "
                    f"to {self.name}."))
        for c in self.scalar_coords:
            if not c.is_scalar:
                raise ValueError((f"Non-scalar coordinate {c} supplied as scalar "
                    f"coordinate for {self.name}."))
        # validate that we don't have duplicate axes
        temp_d = dict()
        for c in itertools.chain(*coords):
            axis = getattr(c.axis, 'name', '')
            if axis != 'OTHER' and axis in temp_d:
                raise ValueError((f"Duplicate definition of {axis} axis in "
                    f"{self.name}: {str(c)}, {str(temp_d[axis])}"))
            temp_d[axis] = c
        # acutally make the dict
        d = dict((x, None) for x in DMAxis.spatiotemporal_names)
        for c in itertools.chain(*coords):
            axis = getattr(c.axis, 'name', '')
            if axis in DMAxis.spatiotemporal_names:
                d[axis] = c
        return d

    def replace_date_range(self, new_T):
        """Returns copy of self with date range on time coordinate changed to 
        new value.
        """
        assert not self.is_static
        old_T = self.T
        if not isinstance(new_T, DMTimeCoordinate):
            new_T = dataclasses.replace(old_T, range=new_T)
        new_dims = list(self.dims)
        new_dims[self.dims.index(old_T)] = new_T
        return dataclasses.replace(self, dims=tuple(new_dims))

@util.mdtf_dataclass
class DMDependentVariable(_DMDimensionsMixin):
    """Base class for any "dependent variable": all non-dimension-coordinate
    information that depends on one or more dimension coordinates.
    """
    name: str = util.MANDATORY
    standard_name: str = util.MANDATORY
    units: str = util.MANDATORY

    dims: tuple = util.MANDATORY
    scalar_coords: set = dataclasses.field(default_factory=set)
    axes: dict = dataclasses.field(init=False)
    phys_axes: dict = dataclasses.field(init=False)

    def __post_init__(self):
        self.axes = self.build_axes(self.dims)
        self.phys_axes = self.build_axes(self.dims, self.scalar_coords)

@util.mdtf_dataclass
class DMAuxiliaryCoordinate(DMDependentVariable):
    """Class to describe `auxiliary coordinate variables 
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__,
    as defined in the CF conventions. An example would be lat or lon for data 
    presented in a tripolar grid projection.
    """
    pass

@util.mdtf_dataclass
class DMCoordinateBounds(DMAuxiliaryCoordinate):
    """Class describing bounds on a dimension coordinate.
    """
    def __post_init__(self):
        super(DMCoordinateBounds, self).__post_init__()
        # validate dimensions
        if self.scalar_coords:
            raise ValueError(("Attempted to create DMCoordinateBounds "
                f"{self.name} with scalar coordinates: {self.scalar_coords}."))
        if len(self.dims) != 2 or \
            DMAxis.BOUNDS not in {c.axis for c in self.dims}:
            raise ValueError(("Attempted to create DMCoordinateBounds "
                f"{self.name} with improper dimensions: {self.dims}."))

    @property
    def coord(self):
        for c in self.dims:
            if c.axis != DMAxis.BOUNDS:
                return c
        raise ValueError

    @classmethod
    def from_coordinate(cls, coord, bounds_dim):
        kwargs = {attr: getattr(coord, attr) for attr \
            in ('name', 'standard_name', 'units')}
        if not isinstance(bounds_dim, DMBoundsDimension):
            bounds_dim = DMBoundsDimension(name=bounds_dim)
        kwargs['dims'] = (coord, bounds_dim)
        kwargs['scalar_coords'] = set([])
        coord_bounds = cls(**kwargs)
        coord.bounds = coord_bounds
        return coord_bounds

@util.mdtf_dataclass
class DMVariable(DMDependentVariable):
    """Class to describe general properties of data variables.
    """
    pass

# Use the "register" method, instead of inheritance, to associate these classes
# with their corresponding abstract interfaces, because Python dataclass fields 
# aren't recognized as implementing an abc.abstractmethod.
AbstractDMDependentVariable.register(DMDependentVariable)
AbstractDMDependentVariable.register(DMAuxiliaryCoordinate)
AbstractDMDependentVariable.register(DMVariable)
AbstractDMCoordinateBounds.register(DMCoordinateBounds)

@util.mdtf_dataclass
class DMDataSet(_DMDimensionsMixin):
    """Class to describe a collection of one or more variables sharing a set of
    common dimensions.
    """
    dims: set = dataclasses.field(default_factory=set)
    scalar_coords: set = dataclasses.field(default_factory=set)
    axes: dict = dataclasses.field(init=False)
    # vars = dependent variables -- includes all aux coords
    vars: list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        for v in self.vars:
            self.dims.update(v.dims)
            self.scalar_coords.update(v.scalar_coords)
        # can't have duplicate dims, but duplicate scalar_coords are OK.
        self.axes = self.build_axes(self.dims)

    def add_dependent_variables(self, *vars_):
        self.vars.extend(vars_)
        self.__post_init__()
