"""Classes to describe "abstract" properties of model data: aspects that are
independent of any model, experiment, or hosting protocol.

This is based on the `CF standard terminology
<https://cfconventions.org/Data/cf-conventions/cf-conventions-1.9/cf-conventions.html>`__.
"""
import abc
import dataclasses as dc
import itertools
import typing
import collections
from src import util
import src.units  # fully qualify name to reduce confusion with "units" attributes
import logging

_log = logging.getLogger(__name__)


class AbstractDMCoordinate(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMCoordinate` objects.
    """

    @property
    @abc.abstractmethod
    def name(self):
        """Coordinate name (str)."""
        pass

    @property
    @abc.abstractmethod
    def standard_name(self):
        """Coordinate CF standard name (str)."""
        pass

    @property
    @abc.abstractmethod
    def units(self):
        """Coordinate units (str, or :class:`~src.units.Units`)."""
        pass

    @property
    @abc.abstractmethod
    def axis(self):
        """Coordinate axis identifier (str, 'X', 'Y', 'Z', 'T')."""
        pass

    @property
    @abc.abstractmethod
    def bounds(self):
        """Associated bounds variable for the coordinate, if present (else None.)
        """
        pass

    @property
    @abc.abstractmethod
    def value(self):
        """If a `scalar coordinate
        <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__,
        value of the coordinate in units given by :meth:`units`.
        """
        pass

    @property
    @abc.abstractmethod
    def is_scalar(self):
        """Whether the coordinate is a `scalar coordinate
        <https://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__
        (bool).
        """
        pass

    @property
    @abc.abstractmethod
    def has_bounds(self):
        """Whether the coordinate has an associated bounds variable (bool).
        """
        pass


class AbstractDMDependentVariable(abc.ABC):
    """Defines interface (set of attributes) for "dependent variables" (data
    defined as a function of one or more dimension coordinates), which inherit
    from :class:`DMDimensions` in this implementation.
    """

    @property
    @abc.abstractmethod
    def name(self):
        """Variable name (str)."""
        pass

    @property
    @abc.abstractmethod
    def standard_name(self):
        """Variable CF standard name (str)."""
        pass

    @property
    @abc.abstractmethod
    def units(self):
        """Variable units (str, or :class:`~src.units.Units`)."""
        pass

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
    def is_static(self):
        """Whether the variable has time dependence (bool)."""
        pass

    @property
    @abc.abstractmethod
    def long_name(self):
        """Optional variable long_name used if standard_name attribute is not defined (str).
        """
        pass

    @property
    @abc.abstractmethod
    def alternate_standard_names(self):
        """Optional list of alternate variable standard_names to query"""
        pass


class AbstractDMCoordinateBounds(AbstractDMDependentVariable):
    """Defines interface (set of attributes) for :class:`DMCoordinateBounds`
    objects.
    """

    @property
    @abc.abstractmethod
    def coord(self):
        """DMCoordinate object which this object is the bounds of."""
        pass


# ------------------------------------------------------------------------------

# MOM6 grid coordinate docs: https://mom6-analysiscookbook.readthedocs.io/en/latest/notebooks/getting_started.html


_AXIS_NAMES = ('X', 'Y', 'Z', 'T', 'N')
_ALL_AXIS_NAMES = _AXIS_NAMES + ('BOUNDS', 'OTHER')


@util.mdtf_dataclass
class DMBoundsDimension(AbstractDMCoordinate):
    """Placeholder object to represent the bounds dimension of a
    :class:`DMCoordinateBounds` object. Not a dimension coordinate, and strictly
    speaking we should make another set of classes for dimensions.
    """
    name: str = util.MANDATORY

    standard_name = 'bounds'
    units = src.units.Units('1')
    axis = 'BOUNDS'
    bounds = None
    value = None

    @property
    def has_bounds(self):
        """Whether the coordinate has an associated bounds variable (bool).
        Always False for this class.
        """
        return False

    @property
    def is_scalar(self):
        """Whether the coordinate is a `scalar coordinate
        <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__
        (bool). Always False for this class.
        """
        return False


@util.mdtf_dataclass
class _DMCoordinateShared:
    """Fields common to all :class:`AbstractDMCoordinate` child classes which
    aren't fixed to particular values.

    ``value`` is our mechanism for implementing CF convention `scalar coordinates
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__.
    """
    standard_name: str = util.MANDATORY
    units: src.units.Units = util.MANDATORY
    axis: str = 'OTHER'
    bounds_var: AbstractDMCoordinateBounds = None
    value: typing.Union[int, float, str] = None
    need_bounds: bool = False

    def __init__(self):
        self._is_scalar = None

    @property
    def bounds(self):
        """The *bounds_var* attribute is stored as a pointer to the actual object
        representing the bounds variable for this coordinate, but in order to
        parallel xarray's syntax define 'bounds' to return the name of this
        variable, not the variable itself.
        """
        if not hasattr(self.bounds_var, 'name'):
            return None
        else:
            return self.bounds_var.name

    @property
    def has_bounds(self):
        """Whether the coordinate has an associated bounds variable (bool).
        """
        return self.bounds_var is not None

    @property
    def is_scalar(self):
        """Whether the coordinate is a `scalar coordinate
        <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__
        (bool).
        """
        if not isinstance(self.value, str):
            return self.value is not None
        else:
            return ''.join(self.value.split()) != ""

    @is_scalar.setter
    def is_scalar(self, value: bool):
        """Whether the coordinate is a `scalar coordinate
        <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__
        (bool).
        """
        self._is_scalar = value

    def make_scalar(self, new_value):
        """Returns a copy of the coordinate, converted to a scalar coordinate
        at value *new_value* (and coordinate's current ``units``.)
        """
        return dc.replace(self, value=new_value)


@util.mdtf_dataclass
class DMCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Class to describe a single coordinate variable (dimension coordinate or
    scalar coordinate, in the sense used by the `CF conventions
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__).
    """
    name: str = util.MANDATORY
    """Coordinate name."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int or float
    standard_name: str = util.MANDATORY
    """Coordinate CF standard name."""
    units: src.units.Units = util.MANDATORY
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'OTHER'
    long_name: str = ''


@util.mdtf_dataclass
class DMXCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Class to describe a longitude dimension coordinate.
    """
    name: str = util.MANDATORY
    """Coordinate name."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int, float, or str
    standard_name: str = util.MANDATORY
    """Coordinate CF standard name."""
    units: src.units.Units = 'degrees_east'
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'X'
    """Coordinate axis identifier. Always 'X' for this coordinate."""
    long_name: str = ''


@util.mdtf_dataclass
class DMYCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Class to describe a longitude dimension coordinate.
    """
    name: str = util.MANDATORY
    """Coordinate name."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int, float, or str
    standard_name: str = util.MANDATORY
    """Coordinate CF standard name."""
    units: src.units.Units = 'degrees_east'
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'Y'
    """Coordinate axis identifier. Always 'Y' for this coordinate."""
    long_name: str = ''


@util.mdtf_dataclass
class DMVerticalCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Class to describe a non-parametric vertical coordinate (height or depth),
    following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#vertical-coordinate>`__.
    """
    name: str = util.MANDATORY
    """Coordinate name."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int, float, or str
    standard_name: str = util.MANDATORY
    """Coordinate CF standard name."""
    units: src.units.Units = "1"  # dimensionless vertical coords OK
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'Z'
    """Coordinate axis identifier. Always 'Z' for this coordinate."""
    positive: str = util.MANDATORY
    long_name: str = ''


@util.mdtf_dataclass
class DMParametricVerticalCoordinate(DMVerticalCoordinate, AbstractDMCoordinate):
    """Class to describe `parametric vertical coordinates
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#parametric-vertical-coordinate>`__.
    Note that the variable names appearing in ``formula_terms`` aren't parsed
    here, in order to keep the class hashable.
    """
    computed_standard_name: str = ""
    """Coordinate CF standard name."""
    long_name: str = ""
    # Don't include formula_terms in testing for equality, since this could
    # reference different names for the aux coord variables.
    # TODO: resolve names in formula_terms to references to objects in the data
    # model.
    formula_terms: str = dc.field(default=None, compare=False)


@util.mdtf_dataclass
class DMGenericTimeCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Applies to collections of variables, which may be at different time
    frequencies (or other attributes).
    """
    name: str = 'time'
    """Coordinate name; defaults to 'time'."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int or float
    standard_name: str = 'time'
    """Coordinate CF standard name."""
    units: src.units.Units = ""
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'T'
    """Coordinate axis identifier. Always 'T' for this coordinate."""
    calendar: str = ""
    """Data frequency"""
    frequency: str = ""
    """CF standard calendar for time data."""
    range: typing.Any = None

    @property
    def is_static(self):
        """Check for time-independent data ('fx' in CMIP6 DRS.) Do the comparison
        by checking date_range against the placeholder value because that's
        unique -- we may be using a different DateFrequency depending on the
        data source.
        """
        return self.range == util.FXDateRange

    @classmethod
    def from_instances(cls, *t_coords):
        """Create new instance from "union" of attributes of one or more
        *t_coords*.
        """
        if not t_coords:
            raise ValueError()
        t_coords = [util.coerce_to_dataclass(t, cls) for t in t_coords]
        t0 = t_coords.pop(0)
        if any(t != t0 for t in t_coords):
            raise ValueError("mismatch")
        return t0


@util.mdtf_dataclass
class DMTimeCoordinate(DMGenericTimeCoordinate, AbstractDMCoordinate):
    name: str = util.MANDATORY
    """Coordinate name."""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int or float
    standard_name: str = 'time'
    """Coordinate CF standard name."""
    units: src.units.Units = util.MANDATORY
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'T'
    """Coordinate axis identifier. Always 'T' for this coordinate."""
    calendar: str = ""
    """CF standard calendar for time data."""
    range: util.AbstractDateRange = None
    """Date range of coordinate."""
    frequency: util.AbstractDateFrequency = None
    """Sampling frequency of coordinate."""

    @classmethod
    def from_instances(cls, *t_coords):
        raise NotImplementedError


@util.mdtf_dataclass
class DMGenericCoordinate(_DMCoordinateShared, AbstractDMCoordinate):
    """Applies to collections of variables with generic coordinates in other
       dimensions (e.g., soil layer, vertex number, radiation band)
    """
    name: str = ""
    """Coordinate name"""
    # bounds_var: AbstractDMCoordinateBounds
    # [scalar] value: int or float
    standard_name: str = ""
    """Coordinate CF standard name."""
    units: src.units.Units = ""
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = "N"
    """Coordinate long name"""
    long_name: str = ""


# Use the "register" method, instead of inheritance, to associate these classes
# with their corresponding abstract interfaces, because Python dataclass fields
# aren't recognized as implementing an abc.abstractmethod.
AbstractDMCoordinate.register(DMCoordinate)
AbstractDMCoordinate.register(DMXCoordinate)
AbstractDMCoordinate.register(DMYCoordinate)
AbstractDMCoordinate.register(DMVerticalCoordinate)
AbstractDMCoordinate.register(DMParametricVerticalCoordinate)
AbstractDMCoordinate.register(DMGenericTimeCoordinate)
AbstractDMCoordinate.register(DMGenericCoordinate)
AbstractDMCoordinate.register(DMTimeCoordinate)
AbstractDMCoordinate.register(DMBoundsDimension)


def coordinate_from_struct(d: collections.OrderedDict, class_dict=None, **kwargs):
    """Attempt to instantiate the correct :class:`DMCoordinate` class based on
    information in dict *d* (read from JSON file).

    *class_dict* is an optional dict mapping axes identifiers to the
    :class:`DMCoordinate` child classes to instantiate. Default is to use
    :class:`DMLongitudeCoordinate` for 'X', etc.

    TODO: implement full cf_xarray/MetPy heuristics.
    """
    if class_dict is None:
        class_dict = {
            'X': DMXCoordinate,
            'Y': DMYCoordinate,
            'Z': DMVerticalCoordinate,
            'T': DMGenericTimeCoordinate,
            'N': DMGenericCoordinate,
            'OTHER': DMCoordinate
        }
    try:
        ax = 'OTHER'
        if 'axis' in d and any(d['axis'].strip()):
            ax = d['axis']
        elif 'time' in d['standard_name'].lower():
            ax = 'T'
        return util.coerce_to_dataclass(d, class_dict[ax], **kwargs)
    except Exception:
        raise ValueError(f"Couldn't parse coordinate: {repr(d)}")


class _DMPlaceholderCoordinateBase:
    """Dummy base class for placeholder coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    pass


@util.mdtf_dataclass
class DMPlaceholderCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'OTHER'
    """Coordinate axis identifier ('X', 'Y', etc.)"""
    long_name: str = NotImplemented


@util.mdtf_dataclass
class DMPlaceholderXCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder X axis coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_X_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_X_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'X'
    """Coordinate axis identifier ('X', 'Y', etc.)"""
    long_name: str = NotImplemented


@util.mdtf_dataclass
class DMPlaceholderYCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder X axis coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_Y_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_Y_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'Y'
    """Coordinate axis identifier ('X', 'Y', etc.)"""
    long_name: str = NotImplemented


@util.mdtf_dataclass
class DMPlaceholderZCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder Z axis coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_Z_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_Z_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'Z'
    """Coordinate axis identifier ('X', 'Y', etc.)"""
    positive: str = NotImplemented

    long_name: str = NotImplemented


@util.mdtf_dataclass
class DMPlaceholderTCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder T axis coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_T_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_T_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'T'
    """Coordinate axis identifier ('X', 'Y', etc.)"""
    calendar: str = NotImplemented
    """CF standard calendar for time data."""
    range: typing.Any = None
    """Date range of coordinate."""


@util.mdtf_dataclass
class DMPlaceholderNCoordinate(_DMCoordinateShared, _DMPlaceholderCoordinateBase):
    """Dummy base class for placeholder N axis coordinates. Placeholder coordinates are
    only used in instantiating :class:`~src.core.FieldlistEntry` objects: they're
    replaced by the appropriate translated coordinates when that object is used
    to create a :class:`~src.core.TranslatedVarlistEntry` object.
    """
    name: str = 'PLACEHOLDER_N_COORD'
    """Coordinate name; defaults to 'PLACEHOLDER_Z_COORD' since this is a temporary
    object."""
    standard_name: str = NotImplemented
    """Coordinate CF standard name."""
    units: src.units.Units = NotImplemented
    """Coordinate units (str or :class:`~src.units.Units`)."""
    axis: str = 'N'
    """Coordinate long name"""
    long_name: str = NotImplemented

    @property
    def is_static(self):
        """Check for time-independent data ('fx' in CMIP6 DRS.) Do the comparison
        by checking date_range against the placeholder value because that's
        unique -- we may be using a different DateFrequency depending on the
        data source.
        """
        return self.range == util.FXDateRange


# ------------------------------------------------------------------------------

@util.mdtf_dataclass
class _DMDimensionsMixin:
    """Lookups for the dimensions, and associated dimension coordinates,
    associated with an array (eg a variable or auxiliary coordinate.) Needs to
    be included as a parent class of a dataclass.
    """
    coords: dc.InitVar = None
    dims: list = dc.field(init=False, default_factory=list)
    scalar_coords: list = dc.field(init=False, default_factory=list)

    def __init__(self):
        self._dim_axes = None

    def __post_init__(self, coords=None, verify_axes: bool = True):
        if coords is None:
            # if we're called to rebuild dicts, rather than after __init__
            assert (self.dims or self.scalar_coords), \
                f'dims and/or scalar_coords not defined for _DMDimensionsMixin instance'
            coords = self.dims + self.scalar_coords
        self.dims = []
        self.scalar_coords = []
        for c in coords:
            if c.is_scalar:
                self.scalar_coords.append(c)
            else:
                self.dims.append(c)
        # raises exceptions if axes are inconsistent
        _ = self.build_axes(self.dims, verify=verify_axes)

    @property
    def dim_axes(self):
        """Return dict mapping axes labels ('X', 'Y', etc.) to corresponding
        dimension coordinate objects.
        """
        return self.build_axes(self.dims, verify=False)

    @dim_axes.setter
    def dim_axes(self, value):
        self._dim_axes = value

    @property
    def X(self):
        """Return X axis dimension coordinate if defined, else None."""
        return self.dim_axes.get('X', None)

    @property
    def Y(self):
        """Return Y axis dimension coordinate if defined, else None."""
        return self.dim_axes.get('Y', None)

    @property
    def Z(self):
        """Return Z axis dimension coordinate if defined, else None."""
        return self.dim_axes.get('Z', None)

    @property
    def T(self):
        """Return T axis dimension coordinate if defined, else None."""
        return self.dim_axes.get('T', None)

    @property
    def N(self):
        """Return N axis dimension coordinate if defined, else None."""
        return self.dim_axes.get('N', None)

    @property
    def dim_axes_set(self):
        """Return frozenset of dimension coordinate axes labels."""
        return frozenset(self.dim_axes.keys())

    @dim_axes_set.setter
    def dim_axes_set(self, value):
        self._dim_axes_set = value

    @property
    def is_static(self):
        """Whether the variable has time dependence (bool)."""
        return (self.T is None) or self.T.is_static

    def get_scalar(self, ax_name: str):
        """If the axis label *ax_name* is a scalar coordinate, return the
        corresponding :class:`AbstractDMCoordinate` object, otherwise return None.
        """
        for c in self.scalar_coords:
            if c.axis == ax_name:
                return c
        return None

    def build_axes(self, *coords, verify=True):
        """Constructs a dict mapping axes labels to
        dimension coordinates (of type :class:`AbstractDMCoordinate`.)
        """
        if verify:
            # validate that we don't have duplicate axes
            d = util.WormDict()
            verify_d = util.WormDict()
            for c in itertools.chain(*coords):
                if c.axis != 'OTHER' and c.axis in verify_d:
                    err_name = getattr(self, 'name', self.__class__.__name__)
                    raise ValueError((f"Duplicate definition of {c.axis} axis in "
                                      f"{err_name}: {c}, {verify_d[c.axis]}"))
                try:
                    verify_d.get(c.axis)
                except Exception as exc:
                    self.log.error(f"{c.axis} already exists %s. Caught exception:", exc)
                verify_d[c.axis] = c
                if c.axis in _AXIS_NAMES:
                    d[c.axis] = c
            return d
        else:
            # assume we've already verified, so use a quicker version of same logic
            return {c.axis: c for c in itertools.chain(*coords)
                    if c.axis in _AXIS_NAMES}

    def change_coord(self, ax_name, new_class=None, **kwargs):
        """Replace attributes on a given coordinate, but also optionally cast
        them to new classes.

        Args:
            ax_name: Name of the coordinate to modify.
            new_class (optional): new class to cast the returned coordinate to.
            kwargs: Set of attribute names and values to replace on the returned
                copy.
        """
        # TODO: lookup by non-axis name
        old_coord = getattr(self, ax_name, None)
        if not old_coord:
            if ax_name == 'T' and not self.is_static:
                raise KeyError(f"{self.name} has no {ax_name} axis")

        if isinstance(new_class, dict):
            new_coord_class = new_class.pop('self', None)
        else:
            new_coord_class = new_class
        if new_coord_class is None and not isinstance(new_class, dict):
            # keep all classes
            new_coord = dc.replace(old_coord, **kwargs)
        else:
            if new_coord_class is None:
                new_coord_class = old_coord.__class__
                new_kwargs = dc.asdict(old_coord)
            else:
                new_kwargs = util.filter_dataclass(old_coord, new_coord_class)
            new_kwargs.update(kwargs)
            if isinstance(new_class, dict):
                for k, cls_ in new_class.items():
                    if k in new_kwargs and not isinstance(new_kwargs[k], cls_):
                        new_kwargs[k] = cls_(new_kwargs[k])
            new_coord = new_coord_class(**new_kwargs)
        self.dims[self.dims.index(old_coord)] = new_coord
        self.__post_init__(None)  # rebuild axes dicts


@util.mdtf_dataclass
class DMDependentVariable(_DMDimensionsMixin, AbstractDMDependentVariable):
    """Base class for any "dependent variable": all non-dimension-coordinate
    information that depends on one or more dimension coordinates.
    """
    name: str = util.MANDATORY
    standard_name: str = util.MANDATORY
    long_name: str = ""
    realm: str = ""
    units: src.units.Units = ""  # not MANDATORY since may be set later from var translation
    modifier: str = ""
    component: str = ""
    associated_files: str = ""
    rename_coords: bool = True
    alternate_standard_names: list

    # dims: from _DMDimensionsMixin
    # scalar_coords: from _DMDimensionsMixin

    def __post_init__(self, coords=None):
        """Call :meth:`build_axes` and deal with CF modifier, if any.
        """
        super(DMDependentVariable, self).__post_init__(coords)
        # raises exceptions if axes are inconsistent
        _ = self.build_axes(self.dims, self.scalar_coords, verify=True)

    @property
    def full_name(self):
        """Object's full name, to be used in logging and debugging. Preferred
        because it eliminates irrelevant information in repr(), which is lengthy.
        """
        return '<' + self.name + '>'  # synonym here; child classes override

    def __str__(self):
        """Condensed string representation.
        """
        if hasattr(self, 'name_in_model') and self.name_in_model:
            str_ = f"='{self.name_in_model}'"
        else:
            str_ = f"{self.standard_name}"
        attrs_ = []
        if not self.is_static and hasattr(self.T, 'frequency'):
            attrs_.append(str(self.T.frequency))
        if self.get_scalar('Z'):
            lev = self.get_scalar('Z')
            attrs_.append(f"{lev.value} {lev.units}")
        if attrs_:
            str_ += " @ "
            str_ += ", ".join(attrs_)
        return f"{self.full_name} ({str_})"

    @property
    def axes(self):
        """Superset of the :meth:`dim_axes` dict (whose values contain coordinate
        dimensions only) that includes axes corresponding to scalar coordinates.
        """
        return self.build_axes(self.dims, self.scalar_coords, verify=False)

    @axes.setter
    def axes(self, value):
        self._axes = value

    @property
    def axes_set(self):
        """Superset of the :meth:`dim_axes_set` frozenset (which contains axes labels
        corresponding to coordinate dimensions only) that includes axes labels
        corresponding to scalar coordinates.
        """
        return frozenset(self.axes.keys())

    @axes_set.setter
    def axes_set(self, value):
        self._axes_set = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def standard_name(self):
        return self._standard_name

    @standard_name.setter
    def standard_name(self, value: str):
        self._standard_name = value.lower()

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value):
        self._units = value

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, value: str):
        self._long_name = value

    @property
    def realm(self):
        return self._realm

    @realm.setter
    def realm(self, value: str | list):
        self._realm = value

    @property
    def alternate_standard_names(self):
        return self._alternate_standard_names

    @alternate_standard_names.setter
    def alternate_standard_names(self, value: list):
        self._alternate_standard_names = value

    def add_scalar(self, ax, ax_value, **kwargs):
        """Metadata operation corresponding to taking a slice of a higher-dimensional
        variable (extracting its values at axis *ax* = *ax_value*). The
        coordinate corresponding to *ax* is removed from the list of coordinate
        dimensions and added to the list of scalar coordinates.
        """
        assert ax in self.dim_axes
        dim = self.dim_axes[ax]
        new_dim = dc.replace(dim, value=ax_value)
        new_dims = self.dims.copy()
        new_dims.remove(dim)
        new_scalars = self.scalar_coords.copy()
        new_scalars.add(new_dim)
        return dc.replace(self,
                          coords=(new_dims + new_scalars),
                          **kwargs
                          )

    def remove_scalar(self, ax: str, position=-1, **kwargs):
        """Metadata operation that's the inverse of :meth:`add_scalar`. Given an
        axis label *ax* that's currently a scalar coordinate, remove the slice
        value and add it to the list of dimension coordinates at *position*
        (default end of the list.)
        """
        dim = self.get_scalar(ax)
        assert dim is not None, 'remove_scalar.get_scalar did not return dim information'
        new_dim = dc.replace(dim, value=None)
        new_dims = self.dims.copy()
        new_dims.insert(position, new_dim)
        new_scalars = self.scalar_coords.copy()
        new_scalars.remove(dim)
        return dc.replace(
            self,
            coords=(new_dims + new_scalars),
            **kwargs
        )

    def dims(self):
        pass

    def scalar_coords(self):
        pass


@util.mdtf_dataclass
class DMAuxiliaryCoordinate(DMDependentVariable, AbstractDMDependentVariable):
    """Class to describe `auxiliary coordinate variables
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#terminology>`__,
    as defined in the CF conventions. An example would be lat or lon for data
    presented in a tripolar grid projection.
    """
    pass


@util.mdtf_dataclass
class DMCoordinateBounds(DMAuxiliaryCoordinate, AbstractDMDependentVariable):
    """Class describing bounds on a dimension coordinate.
    """

    def __post_init__(self, coords=None):
        super(DMCoordinateBounds, self).__post_init__(coords)
        # validate dimensions
        if self.scalar_coords:
            raise ValueError(("Attempted to create DMCoordinateBounds "
                              f"{self.name} with scalar coordinates: {self.scalar_coords}."))
        if len(self.dims) != 2 or \
                'BOUNDS' not in {c.axis for c in self.dims}:
            raise ValueError(("Attempted to create DMCoordinateBounds "
                              f"{self.name} with improper dimensions: {self.dims}."))

    @property
    def coord(self):
        """CF dimension coordinate for which this is the bounds.
        """
        for c in self.dims:
            if c.axis != 'BOUNDS':
                return c
        raise ValueError()

    @classmethod
    def from_coordinate(cls, coord, bounds_dim):
        """Create instance from a coordinate object *coord*.
        """
        kwargs = {attr: getattr(coord, attr) for attr
                  in ('name', 'standard_name', 'units')}
        if not isinstance(bounds_dim, DMBoundsDimension):
            bounds_dim = DMBoundsDimension(name=bounds_dim)
        kwargs['coords'] = [coord, bounds_dim]
        coord_bounds = cls(**kwargs)
        coord.bounds_var = coord_bounds
        return coord_bounds


@util.mdtf_dataclass
class DMVariable(DMDependentVariable, AbstractDMDependentVariable):
    """Class to describe general properties of data variables.
    """
    # name: str             # fields inherited from DMDependentVariable
    # standard_name: str
    # modifier: str
    # units: src.units.Units
    # dims: list            # fields inherited from _DMDimensionsMixin
    # scalar_coords: list
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
    contents: dc.InitVar = util.MANDATORY
    """switch to use axis verification"""
    vars: list = dc.field(init=False, default_factory=list)
    """List of dependent variables in the collection."""
    coord_bounds: list = dc.field(init=False, default_factory=list)
    """List of bounds coordinates referenced by variables in the collection."""
    aux_coords: list = dc.field(init=False, default_factory=list)
    """List of `auxiliary coordinates
    <https://cfconventions.org/cf-conventions/cf-conventions.html#data-model-coordinates>`__
    referenced by variables in the collection.
    """
    verify_axes: dc.InitVar = bool

    def __post_init__(self, coords=None, contents=None, verify_axes: bool = True):
        """Populate shared ``vars``, ``coord_bounds``, ``aux_coords`` attributes
        from collection of input variables.
        """
        assert coords is None  # shouldn't be called with bare coordinates
        if contents is None:
            # if we're called to rebuild dicts, rather than after __init__
            assert (self.vars or self.coord_bounds or self.aux_coords)
            contents = self.vars + self.coord_bounds + self.aux_coords
        self.vars = []
        self.coord_bounds = []
        self.aux_coords = []
        for v in contents:
            self._classify(v).append(v)

        # dims, scalar_coords are a union of those in contents
        # axes must all be the same, except for time axis, which gets described
        # by a DMGenericTimeCoordinate
        t_axes = []
        coords = []
        for v in contents:
            v_dims = v.dims.copy()
            if not v.is_static:
                t_axes.append(v_dims.pop(v_dims.index(v.T)))
            for c in itertools.chain(v_dims, v.scalar_coords):
                if c not in coords:
                    coords.append(c)
        if t_axes:
            new_t = DMGenericTimeCoordinate.from_instances(*t_axes)
            coords.append(new_t)
        # can't have duplicate dims, but duplicate scalar_coords are OK.
        super(DMDataSet, self).__post_init__(coords, verify_axes)

    def iter_contents(self):
        """Generator iterating over the full contents of the DataSet (variables,
        auxiliary coordinates and coordinate bounds.)
        """
        yield from itertools.chain(self.vars, self.aux_coords, self.coord_bounds)

    def iter_vars(self):
        """Generator iterating over variables and auxiliary coordinates but
        excluding coordinate bounds.
        """
        yield from itertools.chain(self.vars, self.aux_coords)

    def iter_vars_only(self, active=None):
        """Generator iterating over variables
        """
        iter_ = yield from itertools.chain(self.vars)
        if active:
            iter_ = filter((lambda x: x.status == util.ObjectStatus.ACTIVE), self.vars)
            yield from list(iter_)
        else:
            return iter_

    def _classify(self, v):
        assert isinstance(v, DMDependentVariable)
        if isinstance(v, DMVariable):
            return self.vars
        elif isinstance(v, DMCoordinateBounds):
            return self.coord_bounds
        else:
            return self.aux_coords

    def add_contents(self, *vars_):
        raise NotImplementedError()

    def change_coord(self, ax_name, new_class=None, **kwargs):
        """Replace attributes on a given coordinate (*ax_name*), but also
        optionally cast them to new classes.

        Args:
            ax_name: Name of the coordinate to modify.
            new_class (optional): new class to cast the returned coordinate to.
            kwargs: Set of attribute names and values to replace on the returned
                copy.
        """
        for v in self.iter_contents():
            try:
                v.change_coord(ax_name, new_class, **kwargs)
            except ValueError:
                if v.is_static:
                    continue
                else:
                    raise
        # time coord for self derived from those for contents
        self.__post_init__(None, None)
