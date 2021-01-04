"""Functions wrapping unit conversion methods from the third-party
`cfunits <https://ncas-cms.github.io/cfunits/index.html>`__ library.
"""
import cfunits
from . import exceptions

import logging
_log = logging.getLogger(__name__)

class Units(cfunits.Units):
    """Wrap `Units <https://ncas-cms.github.io/cfunits/cfunits.Units.html>`__
    class of cfunits to isolate dependence of the framework on cfunits to this
    module.
    """
    pass

def to_cfunits(*args):
    """Coerce string-valued units and (quantity, unit) tuples to cfunits.Units 
    objects. Also coerces reference time units (eg 'days since 1970-01-01') to 
    time units ('days'). The reference date aspect isn't used in the code here 
    and is handled by xarray parsing in the preprocessor.
    """
    def _coerce(u):
        if isinstance(u, tuple):
            # (quantity, unit) tuple
            assert len(u) == 2
            u = u[0] * cfunits.Units(u[1])
        if not isinstance(u, cfunits.Units):
            u = cfunits.Units(u)
        if u.isreftime:
            return cfunits.Units(u._units_since_reftime)
        return u

    if len(args) == 1:
        return _coerce(args[0])
    else:
        return [_coerce(arg) for arg in args]

def _coerce_equivalent_units(*args):
    """Same as to_cfunits, but raise TypeError if units of all
    quantities not equivalent.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    for unit in args:
        if not ref_unit.equivalent(unit):
            raise exceptions.UnitsError((f"Units {repr(ref_unit)} and "
                f"{repr(unit)} are inequivalent."))
    args.append(ref_unit)
    return args

def relative_tol(x, y):
    """HACK to return max(|x-y|/x, |x-y|/y) for unit-ful quantities x,y. 
    Vulnerable to underflow in principle.
    """
    x, y = _coerce_equivalent_units(x,y)
    tol_1 = cfunits.Units.conform(1.0, x, y) # = float(x/y)
    tol_2 = cfunits.Units.conform(1.0, y, x) # = float(y/x)
    return max(abs(tol_1 - 1.0), abs(tol_2 - 1.0))

def units_equivalent(*args):
    """Returns True if and only if all units in arguments are equivalent
    (represent the same physical quantity, up to a multiplicative conversion 
    factor.)
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.equivalent(unit) for unit in args)

def units_equal(*args, rtol=None):
    """Returns True if and only if all quantities in arguments are strictly equal
    (represent the same physical quantity *and* conversion factor = 1).

    .. note::
       rtol, atol tolerances on floating-point equality not currently implemented
       in cfunits, so we implement rtol in a hacky way here.
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
    """Defined so that (conversion factor) * (quantity in source_units) = 
    (quantity in dest_units). 
    """
    source_unit, dest_unit = _coerce_equivalent_units(source_unit, dest_unit)
    return cfunits.Units.conform(1.0, source_unit, dest_unit)

def convert_array(array, source_unit, dest_unit):
    """Wrapper for cfunits.conform() that does unit conversion in-place on a
    numpy array.
    """
    source_unit, dest_unit = _coerce_equivalent_units(source_unit, dest_unit)
    cfunits.Units.conform(array, source_unit, dest_unit, inplace=True)

# --------------------------------------------------------------------

def convert_scalar_coord(coord, dest_units):
    """Given scalar coordinate *coord*, return the appropriate scalar value in
    new units *dest_units*. 
    """
    assert hasattr(coord, 'is_scalar') and coord.is_scalar
    if not units_equal(coord.units, dest_units):
        # convert units of scalar value to convention's coordinate's units
        dest_value = coord.value * conversion_factor(coord.units, dest_units)
        _log.debug("Converted %s %s %s slice of '%s' to %s %s.",
            coord.value, coord.units, coord.axis, coord.name, 
            dest_value, dest_units)
    else:
        # identical units
        _log.debug("Copied value (=%s %s) of %s slice of '%s' (identical units).",
            coord.value, coord.units, coord.axis, coord.name)
        dest_value = coord.value
    return dest_value
