"""Utility functions for working with xarray Datasets.
"""
import collections
import functools
import itertools
import re
import warnings
# 
import cfunits
import cftime
import cf_xarray
import xarray as xr

from src import data_model
from src.util import exceptions

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

# ========================================================================
# Customize behavior of cf_xarray accessor 
# (https://github.com/xarray-contrib/cf-xarray, https://cf-xarray.readthedocs.io/en/latest/)

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
        t_names = cf_xarray.accessor._get_axis_coord(ds, "T")
        if not t_names:
            return None
        assert len(t_names) == 1
        return ds.coords[t_names[0]].attrs.get('calendar', None)

class MDTFCFDatasetAccessorMixin(object):
    """Methods we add for xarray Dataset objects only.
    """
    pass

class MDTFDataArrayAccessorMixin(object):
    """Methods we add for xarray DataArray objects only.
    """
    @property
    def axes_tuple(self):
        """Returns ordered tuple of DMAxis enums corresponding to dimensions.
        eg. var.dims = ('time', 'lat', 'lon') gives an axes_tuple of ('T', 'Y', 'X').
        """
        def _lookup(dim_name):
            for ax, dim_names in self.cf.axes.items():
                if dim_name in dim_names:
                    return data_model.DMAxis.from_struct(ax)
            raise ValueError(dim_name)

        return tuple(_lookup(dim) for dim in self.dims)

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
    
with warnings.catch_warnings():
    # cf_xarray registered its accessors under "cf". Re-registering our versions
    # will work correctly, but raises the following warning, which we suppress.
    warnings.simplefilter(
        'ignore', category=xr.core.extensions.AccessorRegistrationWarning
    )

    @xr.register_dataset_accessor("cf")
    class MDTFCFDatasetAccessor(
        MDTFCFDatasetAccessorMixin, MDTFCFAccessorMixin,
        cf_xarray.accessor.CFDatasetAccessor
    ):
        pass
    
    @xr.register_dataarray_accessor("cf")
    class MDTFCFDataArrayAccessor(
        MDTFDataArrayAccessorMixin, MDTFCFAccessorMixin,
        cf_xarray.accessor.CFDataArrayAccessor
    ):
        pass

# ========================================================================

def verify_calendar(ds):
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
    if not t_names:
        return # assume static data
    elif len(t_names) > 1:
        _log.error("Found multiple time axes. Ignoring all but '%s'.", t_names[0])
        t_names = t_names[:1]
    
    for t_name in t_names:
        time_coord = ds.coords[t_name] # abbreviate
        if hasattr(time_coord.values[0], 'calendar'):
            # normal case: T axis has been parsed into cftime Datetime objects.
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

def parse_dataset(ds):
    """Calls the above metadata parsing functions in the intended order; 
    intended to be called immediately after the Dataset is opened.

    - Strip whitespace from attributes as a precaution to avoid malformed metadata.
    - Call xarray's 
      `decode_cf <http://xarray.pydata.org/en/stable/generated/xarray.decode_cf.html>`__,
      using `cftime <https://unidata.github.io/cftime/>`__ to decode CF-compliant
      time axes. 
    - Assign axis labels to dimension coordinates using cf_xarray.
    - Verify that calendar and standard names are set correctly.

    .. note::
       ``decode_cf=False`` should be passed to the xarray open_dataset command,
       since that parsing is done here instead.
    """
    def _strip(v):
        return (v.strip() if isinstance(v, str) else v)
    def _strip_dict(d):
        return {_strip(k): _strip(v) for k,v in d.items()}

    ds.attrs = _strip_dict(ds.attrs)
    for var in ds.variables:
        ds[var].attrs = _strip_dict(ds[var].attrs)
    ds = xr.decode_cf(ds,         
        decode_coords=True, # parse coords attr
        decode_times=False, # don't decode time axis into default np.datetime64 objects
        use_cftime=True     # use cftime library for dates/calendars instead
    ) # 
    ds = ds.cf.guess_coord_axis()
    verify_calendar(ds)
    return ds

# ---------------------------------------------------------------

def conversion_factor(source_unit, dest_unit):
    """Defined so that (conversion factor) * (quantity in source_units) = 
    (quantity in dest_units). 
    """
    if not source_unit.equivalent(dest_unit):
        raise exceptions.UnitsError((f"Units {repr(source_unit)} and "
            f"{repr(dest_unit)} are inequivalent."))
    return cfunits.conform(1.0, dest_unit, source_unit)

def convert_array(array, source_unit, dest_unit):
    """Wrapper for cfunits.conform() that does unit conversion in-place on a
    numpy array.
    """
    if not source_unit.equivalent(dest_unit):
        raise exceptions.UnitsError((f"Units {repr(source_unit)} and "
            f"{repr(dest_unit)} are inequivalent."))
    cfunits.conform(array, source_unit, dest_unit, inplace=True)


def verify_variable(ds, translated_var):
    """Checks standard_name attribute of all variables and coordinates. If
    not set, attempts to set it according to ``convention``. If different 
    from ``convention``, raises a warning.
    """
    tv_name = translated_var.name          # abbreviate
    convention = translated_var.convention # abbreviate
    if tv_name not in ds:
        raise exceptions.DataPreprocessError(translated_var, 
            f"Variable name '{tv_name}' not found in dataset.")
        # fallback -- try to match on standard name?
    v = ds[tv_name].attrs # abbreviate

    # check standard names agree
    our_std_name = translated_var.standard_name
    if "standard_name" not in v:
        _log.warning("No standard name for '%s' in dataset, setting to '%s'.",
            tv_name, our_std_name)
        v["standard_name"] = our_std_name
    elif v["standard_name"] != our_std_name:
        _log.error(("Found unexpected standard name '%s' for variable "
            "'%s': expected '%s' according to convention '%s'. Leaving "
            "unchanged."),
            v["standard_name"], tv_name, our_std_name, convention
        )

    # check units agree
    our_units = translated_var.units
    if "units" not in v:
        _log.warning("No units for '%s' in dataset, setting to '%s'.",
            tv_name, our_units)
        v["units"] = str(our_units)
    else:
        ds_units = cfunits.Unit(v["units"])
        if not our_units.equivalent(ds_units):
            _log.error(("Found inequivalent units '%s' for variable "
                "'%s': expected '%s' according to convention '%s'. Leaving "
                "unchanged."),
                ds_units, tv_name, our_units, convention
            )

    # check axes (array dimensionality) agree
    our_axes = translated_var.axes_set
    ds_axes = frozenset(ds[tv_name].axes_tuple)
    if our_axes != ds_axes:
        _log.error() 


        
def get_unmapped_names(ds):
    """Get a dict whose keys are variable or attribute names referred to by 
    variables in the dataset, but not present in the dataset itself. Values of 
    the dict are sets of names of variables in the dataset that referred to the
    missing name.
    """
    all_arr_names = set(ds.dims).union(ds.variables)
    all_attr_names = set(getattr(ds, 'attrs', []))
    for name in all_arr_names:
        all_attr_names.update(getattr(ds[name], 'attrs', []))

    # NOTE: will currently fail on CAM/CESM P0. Where do they store it?
    missing_refs = dict()
    lookup = collections.defaultdict(set)
    for name in all_arr_names:
        refs = set(getattr(ds[name], 'dims', []))
        refs.update(itertools.chain.from_iterable(
            ds.cf.get_associated_variable_names(name).values()
        ))
        refs.update(ds[name].cf.formula_terms.values())
        for ref in refs:
            lookup[ref].add(name)
    for ref in lookup:
        if (ref not in all_arr_names) and (ref not in all_attr_names):
            missing_refs[ref] = lookup[ref]
    return missing_refs
