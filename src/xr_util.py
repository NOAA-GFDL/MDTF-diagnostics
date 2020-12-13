import functools
import itertools
import re
import warnings
# 
import cftime
import cf_xarray
import xarray as xr

from src.core import VariableTranslator

import logging
_log = logging.getLogger(__name__)

# TODO: put together a proper CV for all CF convention attributes
_cf_calendars = (
    "gregorian",
    "standard", # synonym for gregorian
    "proleptic_gregorian",
    "julian",
    "noleap",
    "365_day", # synonym for noleap
    "all_leap",
    "366_day", # synonym for all_leap
    "360_day",
    "none"
)


def patch_cf_xarray_accessor(mod):
    """Monkey-patches ``_get_axis_coord``, a module-level function in cf_xarray,
    to obtain desired behavior.
    """
    _ax_to_coord = {
        "X": ("longitude", ),
        "Y": ("latitude", ),
        "Z": ("vertical", ),
        "T": ("time", )
    }
    func_name = "_get_axis_coord"
    old_get_axis_coord = getattr(mod, func_name, None)
    assert old_get_axis_coord is not None
    
    @functools.wraps(old_get_axis_coord)
    def new_get_axis_coord(var, key):
        """Modify cf_xarray behavior: If a variable has been recognized as one of 
        the coordinates in the dict above **and** no variable has been set as the
        corresponding axis, recognize the variable as that axis as well.
        See discussion at `https://github.com/xarray-contrib/cf-xarray/issues/23`__.
        
        Args:
            var: Dataset or DataArray to be queried
            key: axis or coordinate name.
            
        Returns list of variable names in var matching key.
        """
        var_names = old_get_axis_coord(var, key)
        if var_names or (key not in _ax_to_coord):
            # unchanged behavior:
            return var_names
        # remaining case: key is an axis name and no var_names
        for new_key in _ax_to_coord[key]:
            var_names.extend(old_get_axis_coord(var, new_key))
        return var_names
    
    setattr(mod, func_name, new_get_axis_coord)
    
patch_cf_xarray_accessor(cf_xarray.accessor)

class MDTFCFAccessorMixin(object):
    """Methods we add for both xarray Dataset and DataArray objects, although 
    intended use case will be to call them once per Dataset.
    """
    @property
    def calendar(self):
        """Reads 'calendar' attribute on time axis (intended to have been set
        by set_calendar()). Returns None if no time axis.
        """
        ds = self._obj # abbreviate
        t_names = cf_xarray._get_axis_coord(ds, "T")
        if not t_names:
            return None
        assert len(t_names) == 1
        return ds.coords[t_names[0]].attrs.get('calendar', None)

    @property
    def formula_terms(self):
        """Returns dict of (name in formula: name in dataset) pairs parsed from
        formula_terms attribute. If attribute not present, returns empty dict.
        """
        terms = dict()
        # NOTE: more permissive than munging used in cf_xarray
        formula_terms = self._obj.attrs.get('formula_terms', '')
        for mapping in re.sub(r"\s*:\s*", ":", formula_terms).split():
            key, value = mapping.split(":")
            terms[key] = value
        return terms


class MDTFCFDatasetAccessorMixin(object):
    """Methods we add for xarray Dataset objects only.
    """
    pass    
    
with warnings.catch_warnings():
    warnings.simplefilter(
        'ignore', category=xr.core.extensions.AccessorRegistrationWarning
    )

    @xr.register_dataset_accessor("cf")
    class MDTFCFDatasetAccessor(
        MDTFCFAccessorMixin, MDTFCFDatasetAccessorMixin,
        cf_xarray.accessor.CFDatasetAccessor
    ):
        pass
    
    @xr.register_dataarray_accessor("cf")
    class MDTFCFDataArrayAccessor(
        MDTFCFAccessorMixin,
        cf_xarray.accessor.CFDataArrayAccessor
    ):
        pass

# ========================================================================

def set_calendar(ds):
    """Parse the calendar for time-dependent data (assumes CF conventions).
    Sets the "calendar" attr on the time coordinate, if it exists, in order
    to be read by the calendar property. 
    """
    _fallback_value = 'none'

    def _validate_cal(cal_name):
        def _str_xform(s):
            # lowercase, drop non-alphanumeric
            return re.sub(r'[^a-z0-9]+', '', s.lower())

        if cal_name in _cf_calendars:
            return cal_name
        _log.warning("Calendar '%s' not a recognized CF name.", cal_name)
        for c in _cf_calendars:
            if _str_xform(c) == _str_xform(cal_name):
                _log.warning(("Guessing CF calendar '%s' was intended for "
                    "calendar '%s'."), c, cal_name)
                return c
        _log.error("Failed to parse calendar '%s'; using '%s'.", 
            cal_name, _fallback_value)
        return _fallback_value

    t_names = ds.cf.axes.get('T', [])
    if len(t_names) > 1:
        _log.error("Found multiple time axes. Ignoring all but '%s'.", t_names[0])
        t_names = t_names[:1]
    for t_name in t_names:
        time_coord = ds.coords[t_name] # abbreviate
        if hasattr(time_coord.values[0], 'calendar'):
            # normal path: should have been parsed as a cftime Datetime object.
            cftime_cal = getattr(time_coord.values[0], 'calendar')
            time_coord.attrs['calendar'] = _validate_cal(cftime_cal)
        else:
            _log.warning("cftime calendar info parse failed on '%s'.", t_name)
            if 'calendar' in time_coord.attrs:
                attr_cal = time_coord.attrs['calendar']
            elif 'calendar' in ds.attrs:
                attr_cal = ds.attrs['calendar']
            else:
                _log.error("No calendar associated with '%s' found; using '%s'.", 
                    t_name, _fallback_value)
                attr_cal = _fallback_value
            time_coord.attrs['calendar'] = _validate_cal(attr_cal)

def set_standard_names(ds, convention=None):
    """Checks standard_name attribute of all variables and coordinates. If
    not set, attempts to set it according to ``convention``. If different 
    from ``convention``, raises a warning.
    """
    translate = VariableTranslator()

    if isinstance(ds, xr.Dataset):
        variables = ds.variables
    elif isinstance(ds, xr.DataArray):
        variables = ds.coords

    for k, v in variables.items():
        try:
            our_std_name = translate.to_CF(convention, k)
        except KeyError:
            _log.warning("Convention '%s' doesn't recognize variable name '%s'.",
                convention, k)
            continue
        if "standard_name" not in v.attrs:
            v.attrs["standard_name"] = our_std_name
        elif v.attrs["standard_name"] != our_std_name:
            _log.warning(("Found unexpected standard name '%s' for variable "
                "'%s': expected '%s' according to convention '%s'."),
                v.attrs["standard_name"], k, our_std_name, convention
            )



# ---------------------------------------------------------------

def xr_open_dataset(path, **kwargs):
    """Wraps xarray's open_dataset, calling metadata parsing functions in the 
    intended order.

    Strips leading and trailing whitespace from attributes as a precaution.
    """
    def _strip(v):
        return (v.strip() if isinstance(v, str) else v)

    def _strip_dict(d):
        return {_strip(k): _strip(v) for k,v in d.items()}

    kwargs['decode_cf'] = False
    ds = xr.open_dataset(path, **kwargs)
    ds.attrs = _strip_dict(ds.attrs)
    for var in ds.variables:
        ds[var].attrs = _strip_dict(ds[var].attrs)
    ds = xr.decode_cf(ds)
    return ds.cf.guess_coord_axis()
        
def get_unmapped_names(ds):
    """Get a list of variable names referred to by variables in the dataset, but
    not present in the dataset itself.
    """
    # NOTE: will currently fail on CAM/CESM P0. Where do they store it?
    refs = set([])
    missing_refs = []
    for v_name in ds.variables:
        refs.update(itertools.chain.from_iterable(
            ds.cf.get_associated_variable_names(v_name).values()
        ))
        refs.update(ds[v_name].cf.formula_terms.values())
    for ref in refs:
        if ref in ds.variables or ref in ds.attrs:
            continue
        missing_refs.append(ref)
    return missing_refs
