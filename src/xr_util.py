"""Utility functions for working with xarray Datasets.
"""
import collections
import functools
import itertools
import re
import warnings

import cftime
import cf_xarray
import xarray as xr

from src import util

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

@util.mdtf_dataclass
class PlacholderScalarCoordinate():
    """Dummy object used to describe scalar coordinates referred to by name only
    in the 'coordinates' attribute of a variable or dataset. We do this so that
    the attributes match those of coordinates represented by real netcdf Variables.
    """
    name: str
    axis: str
    standard_name: str = util.NOTSET
    units: str = util.NOTSET

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
    def is_static(self):
        return bool(cf_xarray.accessor._get_axis_coord(self._obj, "T"))

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

    def _old_axes_dict(self, var_name=None):
        """cf_xarray accessor behavior: return dict mapping axes labels to lists
        of variable names.
        """
        if var_name is None:
            axes_obj = self._obj
        else:
            # filter Dataset on axes associated with a specific variable
            assert isinstance(self._obj, xr.core.dataset.Dataset)
            axes_obj = self._obj[var_name]
        vardict = {
            key: cf_xarray.accessor.apply_mapper(
                cf_xarray.accessor._get_axis_coord, axes_obj, key, error=False
            ) for key in cf_xarray.accessor._AXIS_NAMES
        }
        return {k: sorted(v) for k, v in vardict.items() if v}

class MDTFCFDatasetAccessorMixin(MDTFCFAccessorMixin):
    """Methods we add for xarray Dataset objects.
    """
    def scalar_coords(self, var_name=None):
        """Return a list of the Dataset variables corresponding to scalar coordinates.
        If coordinate was defined as an attribute only, store its name instead.
        """
        ds = self._obj
        axes_d = ds.cf._old_axes_dict(var_name=var_name)
        scalars = []
        for ax, coord_names in axes_d.items():
            for c in coord_names:
                if c in ds:
                    if (c not in ds.dims or ds[c].size == 1):
                        scalars.append(ds[c])
                else:
                    if c not in ds.dims:
                        # scalar coord set from Dataset attribute, so we only 
                        # have name and axis
                        dummy_coord = PlacholderScalarCoordinate(name=c, axis=ax)
                        scalars.append(dummy_coord)
        return scalars

    def get_scalar(self, ax_name, var_name=None):
        """If the axis label *ax_name* is a scalar coordinate, return the 
        corresponding xarray DataArray (or PlacholderScalarCoordinate), otherwise 
        return None.
        """
        for c in self.scalar_coords(var_name=var_name):
            if c.axis == ax_name:
                return c
        return None

    def axes(self, var_name=None, filter_set=None):
        """Override cf_xarray accessor behavior by having values of the 'axes'
        dict be the Dataset variables themselves, instead of their names.
        """
        ds = self._obj
        axes_d = ds.cf._old_axes_dict(var_name=var_name)
        d = dict()
        for ax, coord_names in axes_d.items():
            new_coords = []
            for c in coord_names:
                if not c or (filter_set is not None and c not in filter_set):
                    continue
                if c in ds:
                    new_coords.append(ds[c])
                else:
                    # scalar coord set from Dataset attribute, so we only 
                    # have name and axis
                    if var_name is not None:
                        assert c not in ds[var_name].dims
                    dummy_coord = PlacholderScalarCoordinate(name=c, axis=ax)
                    new_coords.append(dummy_coord)
            if new_coords:
                if var_name is not None:
                    # Verify that we only have one coordinate for each axis if
                    # we're getting axes for a single variable
                    if len(new_coords) != 1:
                        raise TypeError(f"More than one {ax} axis found for "
                            f"'{var_name}': {new_coords}.")
                    d[ax] = new_coords[0]
                else:
                    d[ax] = new_coords
        return d

    @property
    def axes_set(self):
        return frozenset(self.axes().keys())

    def dim_axes(self, var_name=None):
        """Override cf_xarray accessor behavior by having values of the 'axes'
        dict be the Dataset variables themselves, instead of their names.
        """
        return self.axes(var_name=var_name, filter_set=self._obj.dims)

    @property
    def dim_axes_set(self):
        return frozenset(self.dim_axes().keys())

class MDTFDataArrayAccessorMixin(MDTFCFAccessorMixin):
    """Methods we add for xarray DataArray objects.
    """
    @property
    def dim_axes(self):
        """Map axes labels to the (unique) coordinate variable name,
        instead of a list of names as in cf_xarray. Filter on dimension coordinates
        only (eliminating any scalar coordinates.)
        """
        return {k:v for k,v in self._obj.cf.axes.items() if v in self._obj.dims}

    @property
    def dim_axes_set(self):
        return frozenset(self._obj.cf.dim_axes.keys())

    @property
    def axes(self):
        """Map axes labels to the (unique) coordinate variable name,
        instead of a list of names as in cf_xarray.
        """
        d = self._obj.cf._old_axes_dict()
        if any(len(coord_list) != 1 for coord_list in d.values()):
            raise TypeError() # never get here; should have already been validated
        return {k: v[0] for k,v in d.items()}

    @property
    def axes_set(self):
        return frozenset(self._obj.cf.axes.keys())

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
        """Return element of *options* equal to *expected_val*. If none are equal, 
        try a looser, case-insensititve match. (All arguments expected to be strings.)
        """
        def str_munge(s):
            # comparison function: lowercase, drop non-alphanumeric chars
            return re.sub(r'[^a-z0-9]+', '', s.lower())

        if comparison_func is None:
            comparison_func = (lambda x,y: x == y)
        options = util.to_iter(options)
        test_count = sum(comparison_func(opt, expected_val) for opt in options)
        if test_count > 1:
            _log.debug("Found multiple values of '%s' set for '%s'.", 
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
            _log.debug(("Guessing value '%s' was intended for '%s'."), 
                guessed_val, name)
            return guessed_val
        if default is None:
            _log.debug("No string similar to '%s' in %s.", name, options)
            raise KeyError(expected_val)
        else:
            # _log.error("Failed to parse '%s'; using fallback value '%s'.", 
            #     name, default)
            return default

    def normalize_attr(self, key_name, key_startswith, d, default=None, update=True):
        """Attempts to obtain the value from dict *d* corresponding to the key 
        *key_name*. If *key_name* is not in *d*, we check possible nonstandard
        representations of the key (case-insensitive match via :meth:`guess_attr`
        and whether the key starts with the string *key_startswith*.) If lookup
        fails, return None.

        If *update* is True and the attribute name wasn't *key_name*, set 
        d[key_name] to the obtained value. Do not delete d[k].
        """
        try:
            k = self.guess_attr(key_name, key_name, d.keys(), 
                default=None, comparison_func=None)
        except KeyError:
            try:
                k = self.guess_attr(key_name, key_startswith, d.keys(), 
                    default=default, comparison_func=(lambda x,y: x.startswith(y)))
            except KeyError:
                return None
        value = d.get(k, None)
        if update and value is not None and (k != key_name):
            d[key_name] = value
        return value

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
            unit_str = self.normalize_attr('units', 'unit', ds[var].attrs)
            if unit_str is not None:
                ds[var].attrs['units'] = self.munge_unit(unit_str)
            self.var_attrs_backup[var] = ds[var].attrs.copy()

    def munge_unit(self, unit_str):
        """HACK to convert unit strings to values that are correctly parsed by
        cfunits/UDUnits2. Currently we handle the case where "mb" is interpreted
        as "millibarn", a unit of area (see UDUnits `mailing list 
        <https://www.unidata.ucar.edu/support/help/MailArchives/udunits/msg00721.html>`__.)
        """
        # regex matches "mb", case-insensitive, provided the preceding and following
        # characters aren't also letters; expression replaces "mb" with "millibar"
        unit_str = re.sub(
            r"(?<![^a-zA-Z])([mM][bB])(?![^a-zA-Z])", "millibar", unit_str
        )
        # insert other cases here as they're discovered
        return unit_str

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
        t_coords = ds.cf.axes().get('T', [])
        if not t_coords:
            return # assume static data
        elif len(t_coords) > 1:
            _log.error("Found multiple time axes. Ignoring all but '%s'.", t_coords[0].name)
        t_coord = t_coords[0]

        # normal case: T axis has been parsed into cftime Datetime objects.
        cftime_cal = getattr(t_coord.values[0], 'calendar', None)
        if not cftime_cal:
            _log.warning("cftime calendar info parse failed on '%s'.", t_coord.name)
            cftime_cal = self.normalize_attr('calendar', 'cal', 
                t_coord.encoding, update=False)
        if not cftime_cal:
            cftime_cal = self.normalize_attr('calendar', 'cal', 
                t_coord.attrs, update=False)
        if not cftime_cal:
            cftime_cal = self.normalize_attr('calendar', 'cal', 
                ds.attrs, update=False)
        if not cftime_cal:
            _log.error("No calendar associated with '%s' found; using '%s'.", 
                t_coord.name, _default_cal)
            cftime_cal = _default_cal
        t_coord.attrs['calendar'] = self.guess_attr(
            'calendar', cftime_cal, _cf_calendars, _default_cal)

    @staticmethod
    def _compare_attr(our_attr_tuple, ds_attr_tuple, comparison_func=None, 
        update_our_var=True, update_ds=False):
        """Convenience function to compare two values. Returns tuple of updated
        values, or None if no update is needed.
        """
        # unpack tuples
        our_var, our_attr_name, our_attr = our_attr_tuple
        ds_var, ds_attr_name, ds_attr = ds_attr_tuple

        if comparison_func is None:
            comparison_func = (lambda x,y: x == y)
        if ds_attr == util.NOTSET:
            # skip comparison & make no changes
            # Currently only used by PlacholderScalarCoordinate
            return

        if not ds_attr:
            # ds_attr wasn't defined
            if update_ds:
                # update ds with our value
                _log.warning("No %s found in dataset for '%s'; setting to '%s'.",
                    ds_attr_name, our_var.name, str(our_attr))
                ds_var.attrs[ds_attr_name] = str(our_attr)
            else:
                # don't update, raise exception
                raise TypeError((f"No {ds_attr_name} found in dataset for '{our_var.name}' "
                    f"(= {our_attr})."))
        elif not our_attr:
            # our_attr wasn't defined
            if update_our_var:
                # update our attrwith value from ds
                _log.debug("Updating %s for '%s' to value '%s' from dataset.",
                    our_attr_name, our_var.name, ds_attr)
                setattr(our_var, our_attr_name, ds_attr)
            else:
                # don't update, raise exception
                raise TypeError((f"'{our_var.name}' not set but {ds_attr_name} "
                    f"(= {ds_attr}) present in dataset."))
        elif not comparison_func(our_attr, ds_attr):
            # both attrs present, but different
            if update_our_var:
                # update our attr with value from ds, but raise error
                setattr(our_var, our_attr_name, ds_attr)
                log_str = "Updating our value according to dataset."
            else:
                # don't update, raise exception
                log_str = ""
            raise TypeError((f"Found unexpected {our_attr_name} for variable "
                f"'{our_var.name}': '{ds_attr}' (expected '{our_attr}'). {log_str}"))
        else:
            # comparison passed, no changes needed
            return

    def check_name(self, our_var, ds_var_name):
        """Reconcile the name of the variable between the 'ground truth' of the 
        dataset we downloaded (*ds_var*) and our expectations based on the model's
        convention (*our_var*).
        """
        attr_name = 'name'
        our_attr = getattr(our_var, attr_name, "")
        if our_attr.startswith('PLACEHOLDER'):
            our_attr = ""
        self._compare_attr(
            (our_var, attr_name, our_attr), (None, attr_name, ds_var_name),
            update_our_var=True, update_ds=False
        )

    def check_attr(self, our_var, ds_var, our_attr_name, ds_attr_name=None, 
        comparison_func=None, update_our_var=True, update_ds=False):
        """Compare attribute of a :class:`~src.data_model.DMVariable` (*our_var*) 
        with what's set in the xarray.Dataset (*ds_var*).
        """
        if ds_attr_name is None:
            ds_attr_name = our_attr_name
        our_attr = getattr(our_var, our_attr_name)
        ds_attr = ds_var.attrs.get(ds_attr_name, "")
        self._compare_attr(
            (our_var, our_attr_name, our_attr), (ds_var, ds_attr_name, ds_attr),
            comparison_func=comparison_func, 
            update_our_var=update_our_var, update_ds=update_ds
        )

    def check_scalar_coord_value(self, our_var, ds_var, equivalent=False):
        """Compare scalar coordinate value of a :class:`~src.data_model.DMVariable` 
        (*our_var*) with what's set in the xarray.Dataset (*ds_var*). If there's a 
        discrepancy, log an error but change the entry in *our_var*.
        """
        attr_name = '_scalar_coordinate_value' # placeholder

        def _cleanup_our_var(var_):
            if hasattr(var_, attr_name):
                # cleanup placeholder attr if our var was altered
                var_.value, new_units = getattr(var_, attr_name)
                var_.units = util.to_cfunits(new_units)
                _log.debug("Updated (value, units) of '%s' to (%s, %s).",
                    var_.name, var_.value, var_.units)
                delattr(var_, attr_name)

        assert ds_var.size == 1
        if equivalent:
            comparison_func = util.units_equivalent
        else:
            comparison_func = (lambda x,y: util.units_equal(x,y, rtol=1.0e-5))
        
        our_attr = (our_var.value, our_var.units)
        ds_attr = (float(ds_var), ds_var.attrs.get('units', ''))
        try:
            self._compare_attr(
                (our_var, attr_name, our_attr), (ds_var, attr_name, ds_attr),
                comparison_func=comparison_func,
                update_our_var=True, update_ds=False
            )
            _cleanup_our_var(our_var)
        except TypeError as exc:
            _cleanup_our_var(our_var)
            raise exc

    def check_names_and_units(self, our_var, ds, ds_var_name):
        """Reconcile the standard_name and units attributes between the
        'ground truth' of the dataset we downloaded (*ds_var*) and our expectations
        based on the model's convention (*our_var*).
        """
        # check name
        if ds_var_name not in ds:
            raise ValueError(f"Variable name '{ds_var_name}' not found in dataset: "
                f"({list(ds.variables)}).")
            # attempt to match on standard_name?
        self.check_name(our_var, ds_var_name)
        ds_var = ds[ds_var_name] # abbreviate

        # check CF standard_name
        # see if standard_name has been stored in a nonstandard attribute
        # check_attr will set missing attr on ds
        _ = self.normalize_attr('standard_name', 'standard', ds_var.attrs)
        self.check_attr(our_var, ds_var, 'standard_name',
            update_our_var=True, update_ds=True)

        # check units (and scalar coord value, if set)
        is_scalar = hasattr(our_var, 'is_scalar') and our_var.is_scalar
        # see if units has been stored in a nonstandard attribute
        # check_attr will set missing attr on ds
        _ = self.normalize_attr('units', 'unit', ds_var.attrs, "")
        # if units inequivalent, raise TypeError
        if is_scalar:
            self.check_scalar_coord_value(our_var, ds_var, equivalent=True)
        else:
            self.check_attr(our_var, ds_var, 'units', 
                comparison_func=util.units_equivalent,
                update_our_var=True, update_ds=True
        )
        # now check equality of units - not an error, since we can convert
        try:
            if is_scalar:
                # test equality of quantities+units
                self.check_scalar_coord_value(our_var, ds_var, equivalent=False)
            else:
                # test units only, not quantities+units
                self.check_attr(our_var, ds_var, 'units', 
                    comparison_func=util.units_equal, 
                    update_our_var=True, update_ds=True
                )
        except TypeError as exc:
            _log.warning(exc)
            our_var.units = util.to_cfunits(our_var.units)

    def check_variable(self, ds, translated_var):
        """Top-level method for the MDTF-specific dataset validation: attempts to
        reconcile name, standard_name and units attributes for the variable and
        coordinates in *translated_var* (our expectation, based on the DataSource's
        naming convention) with attributes actually present in the Dataset *ds*.
        """
        # check name, std_name, units on variable itself
        tv_name = translated_var.name # abbreviate
        self.check_names_and_units(translated_var, ds, tv_name)

        # check variable's dimension coordinates
        for coord in ds.cf.axes(tv_name).values():
            # .axes() will have thrown TypeError if XYZT axes not all uniquely defined
            assert isinstance(coord, xr.core.dataarray.DataArray)
        # check set of dimension coordinates (array dimensionality) agrees
        our_axes = translated_var.dim_axes_set
        ds_axes = ds[tv_name].cf.dim_axes_set
        if our_axes != ds_axes:
            raise TypeError(f"Variable {tv_name} has unexpected dimensionality: "
                f" expected axes {set(our_axes)}, got {set(ds_axes)}.") 
        # check dimension coordinate names, std_names, units, bounds
        for coord in translated_var.dim_axes.values():
            ds_coord_name = ds[tv_name].cf.dim_axes[coord.axis]
            self.check_names_and_units(coord, ds, ds_coord_name)
            try:
                bounds_name = ds.cf.get_bounds(ds_coord_name).name
                _log.debug("Updating %s for '%s' to value '%s' from dataset.",
                    'bounds', coord.name, bounds_name)
                coord.bounds = bounds_name
            except KeyError:
                coord.bounds = None
                continue
        for c_name in ds[tv_name].dims:
            if ds[c_name].size == 1:
                _log.warning(("Dataset has dimension coordinate '%s' of size 1 "
                    "not identified as scalar coord."), c_name)

        # check variable's scalar coords: names, std_names, units
        our_scalars = translated_var.scalar_coords
        our_names = [c.name for c in our_scalars]
        our_axes = [c.axis for c in our_scalars]
        ds_scalars = ds.cf.scalar_coords(tv_name)
        ds_names = [c.name for c in ds_scalars]
        ds_axes = [c.axis for c in ds_scalars]
        if len(our_axes) != 0 and len(ds_axes) == 0:
            # warning but not necessarily an error if coordinate dims agree
            _log.debug(("Dataset did not provide any scalar coordinate information, "
                "expected %s."), list(zip(our_names, our_axes)))
        elif our_axes != ds_axes:
            _log.warning(("Conflict in scalar coordinates for %s: expected %s; ",
                "dataset has %s."), 
                translated_var, 
                list(zip(our_names, our_axes)), list(zip(ds_names, ds_axes))
            )
        for coord in our_scalars:
            if coord.axis not in ds[tv_name].cf.axes:
                continue # already logged
            ds_coord_name = ds[tv_name].cf.axes[coord.axis]
            if ds_coord_name in ds:
                if ds[ds_coord_name].size != 1:
                    _log.error("Dataset has scalar coordinate '%s' of size %d != 1.",
                        ds_coord_name, ds[ds_coord_name].size)
                self.check_names_and_units(coord, ds, ds_coord_name)
            else:
                # placheholder object; only have name, assume everything else OK
                self.check_name(coord, ds_coord_name)

    def parse(self, ds, var=None):
        """Calls the above metadata parsing functions in the intended order; 
        intended to be called immediately after the Dataset is opened.

        - Strip whitespace from attributes as a precaution to avoid malformed metadata.
        - Call xarray's 
        `decode_cf <http://xarray.pydata.org/en/stable/generated/xarray.decode_cf.html>`__,
        using `cftime <https://unidata.github.io/cftime/>`__ to decode CF-compliant
        time axes. 
        - Assign axis labels to dimension coordinates using cf_xarray.
        - Verify that calendar is set correctly.
        - Verify that the name, standard_name and units for the variable and its
            coordinates are set correctly.

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
