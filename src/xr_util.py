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
from src.util import basic, exceptions

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

def _coerce_to_cfunits(*args):
    """Coerce string-valued units to cfunits.Units objects. Also coerces 
    reference time units (eg 'days since 1970-01-01') to time units ('days'). 
    The reference date aspect isn't used in the code here and is handled by
    xarray parsing in the preprocessor.
    """
    def _coerce(u):
        if not isinstance(u, cfunits.Units):
            u = cfunits.Units(u)
        if u.isreftime:
            return cfunits.Units(u._units_since_reftime)
        return u

    if len(args) == 1:
        return _coerce(args[0])
    else:
        return [_coerce(arg) for arg in args]

def are_units_equivalent(*args):
    """Returns True if and only if all units in arguments are equivalent
    (represent the same physical quantity, up to a multiplicative conversion 
    factor.)
    """
    args = _coerce_to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.equivalent(unit) for unit in args)

def are_units_equal(*args):
    """Returns True if and only if all units in arguments are strictly equal
    (represent the same physical quantity *and* conversion factor = 1).
    """
    args = _coerce_to_cfunits(*args)
    ref_unit = args.pop()
    return all(ref_unit.equals(unit) for unit in args)

def _coerce_equivalent_units(*args):
    args = _coerce_to_cfunits(*args)
    ref_unit = args.pop()
    for unit in args:
        if not ref_unit.equivalent(unit):
            raise exceptions.UnitsError((f"Units {repr(ref_unit)} and "
                f"{repr(unit)} are inequivalent."))
    args.append(ref_unit)
    return args

def conversion_factor(source_unit, dest_unit):
    """Defined so that (conversion factor) * (quantity in source_units) = 
    (quantity in dest_units). 
    """
    source_unit, dest_unit = _coerce_equivalent_units(source_unit, dest_unit)
    return cfunits.Units.conform(1.0, dest_unit, source_unit)

def convert_array(array, source_unit, dest_unit):
    """Wrapper for cfunits.conform() that does unit conversion in-place on a
    numpy array.
    """
    source_unit, dest_unit = _coerce_equivalent_units(source_unit, dest_unit)
    cfunits.Units.conform(array, source_unit, dest_unit, inplace=True)

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

class MDTFCFDatasetAccessorMixin(MDTFCFAccessorMixin):
    """Methods we add for xarray Dataset objects.
    """
    pass

class MDTFDataArrayAccessorMixin(MDTFCFAccessorMixin):
    """Methods we add for xarray DataArray objects.
    """
    @property
    def axes_tuple(self):
        """Returns ordered tuple of DMAxis enums corresponding to dimensions.
        eg. var.dims = ('time', 'lat', 'lon') gives an axes_tuple of 
        (DMAxis.T, DMAxis.Y, DMAxis.X).
        """
        da = self._obj # abbreviate
        lookup_d = basic.WormDict()
        for ax in data_model.DMAxis.spatiotemporal:
            dim_names = cf_xarray.accessor._get_axis_coord(da, str(ax))
            lookup_d.update({name: ax for name in dim_names})
        return tuple(lookup_d[dim] for dim in da.dims)

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
        MDTFCFDatasetAccessorMixin, cf_xarray.accessor.CFDatasetAccessor
    ):
        pass
    
    @xr.register_dataarray_accessor("cf")
    class MDTFCFDataArrayAccessor(
        MDTFDataArrayAccessorMixin, cf_xarray.accessor.CFDataArrayAccessor
    ):
        pass

# ========================================================================

class DatasetParser():
    """Class which acts as a container for MDTF-specific dataset parsing logic.
    """
    def __init__(self):
        self.attrs_backup = dict()
        self.var_attrs_backup = dict()

    @staticmethod
    def guess_attr(name, expected_val, options, default=None, comparison_func=None):
        """Return element of options equal to expected_val. If none are equal, 
        try case-insensititve match. (All arguments expected to be strings.)
        """
        def str_munge(s):
            # comparison function: lowercase, drop non-alphanumeric chars
            return re.sub(r'[^a-z0-9]+', '', s.lower())

        if comparison_func is None:
            comparison_func = (lambda x,y: x == y)
        options = basic.to_iter(options)
        test_count = sum(comparison_func(opt, expected_val) for opt in options)
        if test_count > 1:
            _log.error("Found multiple values of '%s' set for '%s'.", 
                expected_val, name)
        if test_count >= 1:
            return expected_val
        # _log.warning("Expected value of '%s' for '%s' not found.", 
        #     expected_val, name)
        munged_opts = [
            (comparison_func(str_munge(opt), str_munge(expected_val)), opt) \
                for opt in options
        ]
        if sum(tup[0] for tup in munged_opts) == 1:
            guessed_val = [tup[1] for tup in munged_opts if tup[0]][0]
            _log.warning(("Guessing value '%s' was intended for '%s'."), 
                guessed_val, name)
            return guessed_val
        if default is None:
            _log.error("No string similar to '%s' in %s.", name, options)
            raise KeyError(expected_val)
        else:
            # _log.error("Failed to parse '%s'; using fallback value '%s'.", 
            #     name, default)
            return default

    def guess_key(self, key_name, key_startswith, d, default=None):
        """Attempts to return the (key, value) from dict d corresponding to
        key_name. If key_name is not in d, we check possible nonstandard
        representations of the key (eg case-insensitive match; whether the key
        starts with the string key_startswith.)
        """
        try:
            k = self.guess_attr(key_name, key_name, d.keys(), 
                default=None, comparison_func=None)
        except KeyError:
            k = self.guess_attr(key_name, key_startswith, d.keys(), 
                default=default, comparison_func=(lambda x,y: x.startswith(y)))
        return (k, d.get(k, None))

    def munge_ds_attrs(self, ds):
        """Initial munging of xarray Dataset attribute dicts, before any 
        decoding or parsing.
        """
        def strip_(v):
            return (v.strip() if isinstance(v, str) else v)
        def strip_attrs(obj):
            d = getattr(obj, 'attrs', dict())
            return {strip_(k): strip_(v) for k,v in d.items()}

        setattr(ds, 'attrs', strip_attrs(ds))
        self.attrs_backup = ds.attrs.copy()
        for var in ds.variables:
            setattr(ds[var], 'attrs', strip_attrs(ds[var]))
            self.var_attrs_backup[var] = ds[var].attrs.copy()

    def restore_attrs(self, ds):
        """decode_cf and other functions appear to un-set some of the attributes
        coming from the netcdf file. Restore them from the backups made in 
        munge_ds_attrs, but only if the attribute was deleted.
        """
        def _restore_one(name, backup_d, attrs_d):
            for k,v in backup_d.items():
                if k not in attrs_d:
                    # _log.debug("%s: restore attr '%s' = '%s'.", name, k, v)
                    attrs_d[k] = v
                if v != attrs_d[k]:
                    _log.debug("%s: discrepancy for attr '%s': '%s' != '%s'.",
                        name, k, v, attrs_d[k])
        
        _restore_one('Dataset', self.attrs_backup, ds.attrs)
        for var in ds.variables:
            _restore_one(var, self.var_attrs_backup[var], ds[var].attrs)

    def check_calendar(self, ds):
        """Parse the calendar for time-dependent data (assumes CF conventions).
        Sets the "calendar" attr on the time coordinate, if it exists, in order
        to be read by the calendar property. 
        """
        _default_cal = 'none'
        t_names = ds.cf.axes.get('T', [])
        if not t_names:
            return # assume static data
        elif len(t_names) > 1:
            _log.error("Found multiple time axes. Ignoring all but '%s'.", t_names[0])
        t_name = t_names[0]
        time_coord = ds.coords[t_name] # abbreviate

        # normal case: T axis has been parsed into cftime Datetime objects.
        cftime_cal = getattr(time_coord.values[0], 'calendar', None)
        if not cftime_cal:
            _log.warning("cftime calendar info parse failed on '%s'.", t_name)
            try:
                _, cftime_cal = self.guess_key('calendar', 'cal', time_coord.attrs)
            except KeyError:
                try:
                    _, cftime_cal = self.guess_key('calendar', 'cal', ds.attrs)
                except KeyError:
                    _log.error("No calendar associated with '%s' found; using '%s'.", 
                        t_name, _default_cal)
                    cftime_cal = _default_cal
        time_coord.attrs['calendar'] = self.guess_attr(
            'calendar', cftime_cal, _cf_calendars, _default_cal)

    @staticmethod
    def _compare_attr(our_attr, ds_attr, comparison_func=None):
        """Convenience function to compare two values. Returns tuple of updated
        values, or None if no update is needed.
        """
        if comparison_func is None:
            comparison_func = (lambda x,y: x == y)

        if not ds_attr:
            return (None, str(our_attr))
        elif not our_attr:
            return (ds_attr, None)
        elif not comparison_func(our_attr, ds_attr):
            return (ds_attr, ds_attr)
        else:
            return (None, None)

    def check_name(self, our_var, ds_var_name):
        """Reconcile the name of the variable between the 'ground truth' of the 
        dataset we downloaded (ds_var) and our expectations based on the model's
        convention (our_var).
        """
        our_attr_name = 'name'
        our_attr = getattr(our_var, our_attr_name, "")
        if our_attr.startswith('PLACEHOLDER'):
            our_attr = ""
        our_new_attr, ds_new_attr = self._compare_attr(our_attr, ds_var_name)

        if our_new_attr is not None and ds_new_attr is not None:
            setattr(our_var, our_attr_name, our_new_attr)
            raise TypeError((f"Found unexpected {our_attr_name} for variable "
                f"'{our_var.name}': '{our_new_attr}' (expected '{our_attr}'). "
                "Updating record according to info in dataset."))
        elif ds_new_attr is not None:
            # should never get here
            raise TypeError(f"No {our_attr_name} found in dataset for '{our_var.name}'.")
        elif our_new_attr is not None:
            _log.debug("Updating %s for '%s' to value '%s' from dataset.",
                our_attr_name, our_var.name, our_new_attr)
            setattr(our_var, our_attr_name, our_new_attr)
        else:
            return

    def check_attr(self, our_var, ds_var, our_attr_name, ds_attr_name=None, 
        comparison_func=None):
        """Compare attribute of a DMVariable (our_var) with what's set in the 
        xarray.Dataset (ds_var). If there's a discrepancy, log an error but 
        change the entry in our_var (ie take ds_var to be ground truth.)
        """
        if ds_attr_name is None:
            ds_attr_name = our_attr_name
        our_attr = getattr(our_var, our_attr_name)
        ds_attr = ds_var.attrs.get(ds_attr_name, "")
        our_new_attr, ds_new_attr = self._compare_attr(our_attr, ds_attr, 
            comparison_func=comparison_func)

        if our_new_attr is not None and ds_new_attr is not None:
            setattr(our_var, our_attr_name, our_new_attr)
            raise TypeError((f"Found unexpected {our_attr_name} for variable "
                f"'{our_var.name}': '{our_new_attr}' (expected '{our_attr}'). "
                "Updating record according to info in dataset."))
        elif ds_new_attr is not None:
            _log.warning("No %s found in dataset for '%s'; setting to '%s'.",
                ds_attr_name, our_var.name, str(ds_new_attr))
            ds_var.attrs[ds_attr_name] = str(ds_new_attr)
        elif our_new_attr is not None:
            _log.debug("Updating %s for '%s' to value '%s' from dataset.",
                our_attr_name, our_var.name, our_new_attr)
            setattr(our_var, our_attr_name, our_new_attr)
        else:
            return

    def check_names_and_units(self, our_var, ds, ds_var_name):
        """Reconcile the standard_name and units attributes between the
        'ground truth' of the dataset we downloaded (ds_var) and our expectations
        based on the model's convention (our_var).
        """
        if ds_var_name not in ds:
            raise ValueError(f"Variable name '{ds_var_name}' not found in dataset: "
                f"({list(ds.variables)}).")
        self.check_name(our_var, ds_var_name)
        ds_var = ds[ds_var_name] # abbreviate
        d = ds_var.attrs         # abbreviate
        try:
            # see if standard_name has been stored in a nonstandard attribute
            _, std_name = self.guess_key('standard_name', 'standard', d)
            d['standard_name'] = std_name
        except KeyError:
            pass
        self.check_attr(our_var, ds_var, 'standard_name')
        try:
            try:
                # see if units has been stored in a nonstandard attribute
                _, units = self.guess_key('units', 'unit', d, "")
                d['units'] = units
            except KeyError:
                pass
            self.check_attr(our_var, ds_var, 'units', 
                comparison_func=are_units_equivalent)
        except TypeError as exc:
            our_var.units = _coerce_to_cfunits(our_var.units)
            raise exc

    def check_variable(self, ds, translated_var):
        """Checks standard_name attribute of all variables and coordinates. If
        not set, attempts to set it according to ``convention``. If different 
        from ``convention``, raises a warning.
        """
        tv_name = translated_var.name            # abbreviate
        self.check_names_and_units(translated_var, ds, tv_name)

        # check XYZT axes all uniquely defined
        for ax, coord_list in ds.cf.axes.items():
            if len(coord_list) != 1:
                raise TypeError(f"More than one {ax} axis found for '{tv_name}': "
                    f"{coord_list}.")
        # check axes_set (array dimensionality) agrees
        our_axes = translated_var.axes_set
        ds_axes = frozenset(ds[tv_name].cf.axes_tuple)
        if our_axes != ds_axes:
            raise TypeError(f"Variable {tv_name} has unexpected dimensionality: "
                f" expected axes {set(our_axes)}, got {set(ds_axes)}.") 
        # check axis names, std_names, units, bounds
        for translated_coord in translated_var.axes.values():
            ax = translated_coord.axis
            ds_coord_name = ds.cf.axes[str(ax)][0]
            self.check_names_and_units(translated_coord, ds, ds_coord_name)
            try:
                bounds_name = ds.cf.get_bounds(ds_coord_name).name
                _log.debug("Updating %s for '%s' to value '%s' from dataset.",
                    'bounds', translated_coord.name, bounds_name)
                translated_coord.bounds = bounds_name
            except KeyError:
                continue

    def parse(self, ds, var=None):
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
        self.munge_ds_attrs(ds)
        ds = xr.decode_cf(ds,         
            decode_coords=True, # parse coords attr
            decode_times=True,
            use_cftime=True     # use cftime instead of np.datetime64
        )
        ds = ds.cf.guess_coord_axis()
        self.restore_attrs(ds)
        self.check_calendar(ds)
        if var is not None:
            self.check_variable(ds, var.translation)
        return ds
    
    @staticmethod
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
