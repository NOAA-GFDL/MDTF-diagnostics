"""Functions wrapping unit conversion methods from the third-party
`cfunits <https://ncas-cms.github.io/cfunits/index.html>`__ library.
"""
import cfunits
from src import util

import logging
_log = logging.getLogger(__name__)

class Units(cfunits.Units):
    """Wrap `Units <https://ncas-cms.github.io/cfunits/cfunits.Units.html>`__
    class of `cfunits <https://ncas-cms.github.io/cfunits/>`__ to isolate this
    third-party dependency to the code in this module.
    """
    def reftime_base_eq(self, other):
        """Comparison function that recognizes reference time units (e.g.,
        'days since 1970-01-01') as being equal to unqualified time units
        of the same base unit ('days'). The cfunits `equivalent()
        <https://ncas-cms.github.io/cfunits/generated/cfunits.Units.equivalent.html>`__
        method returns False on these cases.
        """
        cls = type(self)
        if self.isreftime and other.isreftime:
            return self.equals(other)
        self_2 = (cls(self._units_since_reftime) if self.isreftime else self)
        other_2 = (cls(other._units_since_reftime) if other.isreftime else other)
        return self_2.equals(other_2)

def to_cfunits(*args):
    """Coerce string-valued units and (quantity, unit) tuples to :class:`Units`
    objects.

    If more than one such argument is given in *args*, return a list containing
    the results of coercing each argument.
    """
    def _coerce(u):
        if isinstance(u, tuple):
            # (quantity, unit) tuple
            assert len(u) == 2
            u = u[0] * Units(u[1])
        if not isinstance(u, Units):
            u = Units(u)
        return u

    if len(args) == 1:
        return _coerce(args[0])
    else:
        return [_coerce(arg) for arg in args]

def to_equivalent_units(*args):
    """Same as :func:`to_cfunits`, but raises TypeError if units of all
    quantities in *args* are not equivalent after coercion.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop() # last entry in list
    for unit in args:
        if not ref_unit.equivalent(unit):
            raise TypeError((f"Units {repr(ref_unit)} and "
                f"{repr(unit)} are inequivalent."))
    args.append(ref_unit)
    return args

def relative_tol(x, y):
    """HACK to return ``max(|x-y|/x, |x-y|/y)`` for unit-ful quantities *x*, *y*
    with equivalent units. Vulnerable to underflow in principle.

    *x* and *y* are coerced to :class:`Units` objects via :func:`to_cfunits`.
    """
    x, y = to_equivalent_units(x,y)
    tol_1 = Units.conform(1.0, x, y) # = float(x/y)
    tol_2 = Units.conform(1.0, y, x) # = float(y/x)
    return max(abs(tol_1 - 1.0), abs(tol_2 - 1.0))

def units_equivalent(*args):
    """Returns True if and only if all unit-ful quantities in *args* are physically
    equivalent: they represent the same physical quantity, up to a multiplicative
    conversion factor.

    *args* are coerced to :class:`Units` objects via :func:`to_cfunits`.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.equivalent(unit) for unit in args)

def units_reftime_base_eq(*args):
    """Returns True if and only if all unit-ful quantities in *args* are physically
    equivalent: they represent the same physical quantity, up to a multiplicative
    conversion factor.

    *args* are coerced to :class:`Units` objects via :func:`to_cfunits`.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.reftime_base_eq(unit) for unit in args)

def units_equal(*args, rtol=None):
    """Returns True if and only if all unit-ful quantities in *args* are strictly
    equal (:func:`units_equivalent` is True and :func:`conversion_factor` = 1).

    .. note::
       rtol, atol tolerances on floating-point equality are not currently
       implemented in cfunits, so we use :func:`relative_tol`.

    *args* are coerced to :class:`Units` objects via :func:`to_cfunits`.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    if rtol is None:
        # no tolerances: comparing units w/o quantities (or integer quantities)
        return all(ref_unit.equals(unit) for unit in args)
    else:
        for unit in args:
            try:
                if not (relative_tol(ref_unit, unit) <= rtol):
                    return False # outside tolerance
            except TypeError:
                return False # inequivalent units
        return True

def conversion_factor(source_unit, dest_unit):
    """Return floating point factor which implements a given unit conversion.
    Defined so that (conversion factor) * (quantity in *source_units*) =
    (quantity in *dest_units*).

    *source_unit*, *dest_unit* are coerced to :class:`Units` objects via
    :func:`to_cfunits`.
    """
    source_unit, dest_unit = to_equivalent_units(source_unit, dest_unit)
    return Units.conform(1.0, source_unit, dest_unit)

# --------------------------------------------------------------------

def convert_scalar_coord(coord, dest_units, log=_log):
    """Given scalar coordinate *coord*, return the appropriate scalar value in
    new units *dest_units*.
    """
    assert hasattr(coord, 'is_scalar') and coord.is_scalar
    if not units_equal(coord.units, dest_units):
        # convert units of scalar value to convention's coordinate's units
        dest_value = coord.value * conversion_factor(coord.units, dest_units)
        log.debug("Converted %s %s %s slice of '%s' to %s %s.",
            coord.value, coord.units, coord.axis, coord.name,
            dest_value, dest_units,
            tags=util.ObjectLogTag.NC_HISTORY
        )
    else:
        # identical units
        log.debug("Copied value of %s slice (=%s %s) of '%s' (identical units).",
            coord.axis, coord.value, coord.units, coord.name
        )
        dest_value = coord.value
    return dest_value

def convert_dataarray(ds, da_name, src_unit=None, dest_unit=None, log=_log):
    """Wrapper for cfunits `conform()
    <https://ncas-cms.github.io/cfunits/generated/cfunits.Units.conform.html#cfunits.Units.conform>`__
    that does unit conversion in-place on a member of an xarray Dataset,
    updating its units attribute.

    Args:
        ds (Dataset): xarray Dataset containing the DataArray to convert.
        da_name (str): Name of the DataArray to do the unit conversion on.
        src_unit: Current units of *da_name*. Coerced to a :class:`Units` object
            via :func:`to_cfunits`. Optional; if not given this is populated from
            the ``units`` attribute of *da_name*, if it exists.
        dest_unit: Desired units for *da_name*. Coerced to a :class:`Units` object
            via :func:`to_cfunits`.

    Raises:
        ValueError: if *da_name* not in *ds*.
        TypeError: if *src_unit* or *dest_unit* not correctly defined, or if
            *da_name* lacks units metadata.

    Returns:
        Dataset *ds*, with *da_name* modified in-place.
    """
    da = ds.get(da_name, None)
    if da is None:
        raise ValueError(f"convert_dataarray: '{da_name}' not found in dataset.")
    if src_unit is None:
        try:
            src_unit = da.attrs['units']
        except KeyError:
            raise TypeError((f"convert_dataarray: 'units' attribute not defined "
                f"on {da.name}."))
    if dest_unit is None:
        raise TypeError((f"convert_dataarray: dest_unit not given for unit "
            "conversion on {da.name}."))

    if 'standard_name' in da.attrs:
        std_name = f" ({da.attrs['standard_name']})"
    else:
        std_name = ""
    if units_equal(src_unit, dest_unit):
        log.debug(("Source, dest units of '%s'%s identical (%s); no conversion "
            "done."), da.name, std_name, dest_unit)
        return ds

    log.debug("Convert units of '%s'%s from '%s' to '%s'.",
        da.name, std_name, src_unit, dest_unit,
        tags=util.ObjectLogTag.NC_HISTORY
    )
    da_attrs = da.attrs.copy()
    fac = conversion_factor(src_unit, dest_unit)
    ds = ds.assign({da_name: fac * ds[da_name]})
    ds[da_name].attrs = da_attrs
    ds[da_name].attrs['units'] = str(dest_unit)
    return ds
