"""Functions wrapping unit conversion methods from the third-party
`cfunits <https://ncas-cms.github.io/cfunits/index.html>`__ library.
"""
import cfunits

import logging
_log = logging.getLogger(__name__)

class Units(cfunits.Units):
    """Wrap `Units <https://ncas-cms.github.io/cfunits/cfunits.Units.html>`__
    class of cfunits to isolate dependence of the framework on cfunits to this
    module.
    """
    @classmethod
    def _h2o_equivalent_unit(cls, from_units, to_units, verbose=False, allow_h2o=False):
        """Extend *equivalent* method on parent class to allow equivalence up to
        the density of water; eg. if allow_h2o=True, 'kg m-2 s-1' and 'mm day-1'
        will be reported as equivalent.

        Returns equivalent Units object corresponding to *second* argument, or None.
        """
        def _make_quantity(u):
            # workaround for cfunits implementation of arithmetic
            if not str(u)[0].isdigit():
                return cls('1.0 '+ str(u))
            return u

        bool_ = super(Units, from_units).equivalent(to_units, verbose=verbose)
        if bool_ or not allow_h2o:
            return (to_units if bool_ else None)
        else:
            # HACK: throw in factor of _water_density to attempt to get unit
            # agreement. We assume calling function will have raised a warning
            # that we're doing this.

            # Value is incorrect but matches convention for this conversion.
            _water_density = cls('1000.0 kg m-3')

            from_units = _make_quantity(from_units)
            to_units = _make_quantity(to_units)
            _method = super(Units, from_units).equivalent

            if _method(from_units, to_units * _water_density):
                return to_units * _water_density
            if _method(from_units, to_units / _water_density):
                return to_units / _water_density
            return None

    def equivalent(self, other, verbose=False, allow_h2o=False):
        """Extend *equivalent* method on parent class to allow equivalence up to
        the density of water; eg. if allow_h2o=True, 'kg m-2 s-1' and 'mm day-1'
        will be reported as equivalent.
        """
        return (self._h2o_equivalent_unit(self, other, 
            verbose=verbose, allow_h2o=allow_h2o) is not None)

    @classmethod
    def conform(cls, x, from_units, to_units, inplace=False, allow_h2o=False):
        """Extend *conform* method on parent class to allow equivalence up to
        the density of water; eg. if allow_h2o=True, converting '1.0 kg m-2 s-1' 
        to 'mm day-1' will not raise a ValueError and instead return 86400.0.
        """
        equiv_to_units = cls._h2o_equivalent_unit(from_units, to_units, 
            verbose=False, allow_h2o=allow_h2o)
        return super(Units, cls).conform(x, from_units, equiv_to_units, inplace=inplace)

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
            u = u[0] * Units(u[1])
        if not isinstance(u, Units):
            u = Units(u)
        if u.isreftime:
            return Units(u._units_since_reftime)
        return u

    if len(args) == 1:
        return _coerce(args[0])
    else:
        return [_coerce(arg) for arg in args]

def to_equivalent_units(*args, allow_h2o=False):
    """Same as to_cfunits, but raise TypeError if units of all
    quantities not equivalent.
    """
    args = to_cfunits(*args)
    ref_unit = args.pop() # last entry in list
    new_args = []
    for unit in args:
        new_unit = Units._h2o_equivalent_unit(ref_unit, unit, allow_h2o=allow_h2o)
        if new_unit is None:
            raise TypeError((f"Units {repr(ref_unit)} and {repr(unit)} are "
                "inequivalent."))
        new_args.append(new_unit)
    new_args.append(ref_unit)
    return new_args

def relative_tol(x, y):
    """HACK to return max(|x-y|/x, |x-y|/y) for unit-ful quantities x,y. 
    Vulnerable to underflow in principle.
    """
    x, y = to_equivalent_units(x,y)
    tol_1 = Units.conform(1.0, x, y) # = float(x/y)
    tol_2 = Units.conform(1.0, y, x) # = float(y/x)
    return max(abs(tol_1 - 1.0), abs(tol_2 - 1.0))

def units_equivalent(*args, allow_h2o=False):
    """Returns True if and only if all units in arguments are equivalent
    (represent the same physical quantity, up to a multiplicative conversion 
    factor.)
    """
    args = to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.equivalent(unit, allow_h2o=allow_h2o) for unit in args)

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

def conversion_factor(source_unit, dest_unit, allow_h2o=False):
    """Defined so that (conversion factor) * (quantity in source_units) = 
    (quantity in dest_units). 
    """
    source_unit, dest_unit = to_equivalent_units(
        source_unit, dest_unit, allow_h2o=allow_h2o
    )
    return Units.conform(1.0, source_unit, dest_unit, allow_h2o=allow_h2o)

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

def convert_dataarray(da, dest_unit, allow_h2o=False):
    """Wrapper for cfunits.conform() that does unit conversion in-place on an
    xarray DataArray, updating its units attribute.
    """
    da_unit = da.attrs.get('units', "")
    assert da_unit
    if 'standard_name' in da.attrs:
        std_name = f" ({da.attrs['standard_name']})"
    else:
        std_name = ""
    if units_equal(da_unit, dest_unit):
        _log.debug(("Source, dest units of '%s'%s identical (%s); no conversion "
            "done."), da.name, std_name, dest_unit)
        return da

    try:
        source_unit, dest_unit = to_equivalent_units(
            da_unit, dest_unit, allow_h2o=False)
    except TypeError as exc:
        if not allow_h2o:
            raise exc
        # modification is done on the first unit
        source_unit, dest_unit = to_equivalent_units(
            da_unit, dest_unit, allow_h2o=True)
        _log.warning(("Assumed implicit factor of water density in units for '%s'%s: "
            "given %s, assuming %s."), da.name, std_name, da_unit, source_unit)

    _log.debug("Convert units of '%s'%s from '%s' to '%s'.", 
        da.name, std_name, source_unit, dest_unit)
    Units.conform(da.values, source_unit, dest_unit, inplace=True, allow_h2o=False)
    da.attrs['units'] = str(dest_unit)
    return da
