"""Functionality for transforming model data into the format expected by PODs
once it's been downloaded; see :doc:`fmwk_preprocess`.
"""
import os
import abc
import dataclasses
import functools
from src import util, core, diagnostic, xr_parser, units
import cftime
import numpy as np
import xarray as xr

import logging
_log = logging.getLogger(__name__)

def copy_as_alternate(old_v, data_mgr, **kwargs):
    """Wrapper for :py:func:`~dataclasses.replace` that creates a copy of an
    existing :class:`~src.diagnostic.VarlistEntry` *old_v* and sets appropriate
    attributes to designate it as an alternate variable.
    """
    if 'coords' not in kwargs:
        # dims, scalar_coords are derived attributes set by __post_init__
        # if we aren't changing them, must use this syntax to pass them through
        kwargs['coords'] = (old_v.dims + old_v.scalar_coords)
    new_v = dataclasses.replace(
        old_v,
        _id = util.MDTF_ID(),                           # assign distinct ID
        stage = diagnostic.VarlistEntryStage.INITED,    # reset state from old_v
        status = core.ObjectStatus.INACTIVE,      # new VE meant as an alternate
        requirement = diagnostic.VarlistEntryRequirement.ALTERNATE,
        # plus the specific replacements we want to make:
        **kwargs
    )
    return new_v

def edit_request_wrapper(wrapped_edit_request_func):
    """Decorator implementing the most typical (so far) use case for
    :meth:`PreprocessorFunctionBase.edit_request`, in which we look at each
    variable request in the varlist separately and, optionally, add a new
    alternate :class:`~src.diagnostic.VarlistEntry` based on that request.

    This decorator wraps a function which either constructs and returns the
    desired new alternate :class:`~src.diagnostic.VarlistEntry`, or returns None
    if no alternates are to be added for the given variable request. It adds
    logic for updating the list of alternates for the pod's varlist.
    """
    @functools.wraps(wrapped_edit_request_func)
    def wrapped_edit_request(self, data_mgr, pod):
        new_varlist = []
        for v in pod.varlist.iter_contents():
            new_v = wrapped_edit_request_func(self, v, pod, data_mgr)
            if new_v is None:
                # no change, pass through VE unaltered
                new_varlist.append(v)
                continue
            else:
                # insert new_v between v itself and v's old alternate sets
                # in varlist query order
                new_v.alternates = v.alternates
                v.alternates = [[new_v]]
                new_v_t_name = (str(new_v.translation) \
                    if getattr(new_v, 'translation', None) is not None \
                    else "(not translated)")
                v_t_name = (str(v.translation) if getattr(v, 'translation', None) \
                    is not None else "(not translated)")
                pod.log.debug("%s for %s: add translated %s as alternate for %s.",
                    self.__class__.__name__, v.full_name, new_v_t_name, v_t_name)
                new_varlist.append(v)
                new_varlist.append(new_v)
        pod.varlist = diagnostic.Varlist(contents=new_varlist)

    return wrapped_edit_request

class PreprocessorFunctionBase(abc.ABC):
    """Abstract interface for implementing a specific preprocessing functionality.
    We prefer to put each set of operations in its own child class, rather than
    dumping everything into a general Preprocessor class, in order to keep the
    logic easier to follow.

    It's up to individual Preprocessor child classes to select which functions
    to use, and in what order to perform them.
    """
    def __init__(self, data_mgr, pod):
        """Called during Preprocessor's init."""
        pass

    def edit_request(self, data_mgr, pod):
        """Edit the data requested in *pod*'s :class:`~src.diagnostic.Varlist`
        queue, based on the transformations the functionality can perform. If
        the function can transform data in format X to format Y and the POD
        requests X, this method should insert a backup/fallback request for Y.
        """
        pass

    @abc.abstractmethod
    def process(self, var, dataset):
        """Apply functionality to the input dataset.

        Args:
            var (:class:`~src.diagnostic.VarlistEntry`): POD varlist entry
                instance describing POD's data request, which is the desired end
                result of preprocessing work.
            dataset: `xarray.Dataset
                <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__
                instance.
        """
        return dataset

class CropDateRangeFunction(PreprocessorFunctionBase):
    """A :class:`PreprocessorFunctionBase` class which trims the time axis of
    the dataset to the user-requested analysis period.
    """
    @staticmethod
    def cast_to_cftime(dt, calendar):
        """Workaround to cast python :py:class:`~datetime.datetime` *dt* to
        `cftime.datetime <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        with given *calendar*. Python stdlib datetime has no support for different
        calendars.
        """
        # NB "tm_mday" is not a typo
        t = dt.timetuple()
        tt = (getattr(t, attr_) for attr_ in
            ('tm_year', 'tm_mon', 'tm_mday', 'tm_hour', 'tm_min', 'tm_sec'))
        return cftime.datetime(*tt, calendar=calendar)

    def process(self, var, ds):
        """Parse quantities related to the calendar for time-dependent data.
        In particular, ``date_range`` was set from user input before we knew the
        model's calendar. Workaround here to cast those values into `cftime.datetime
        <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        objects so they can be compared with the model data's time axis.
        """
        tv_name = var.name_in_model
        t_coord = ds.cf.dim_axes(tv_name).get('T', None)
        if t_coord is None:
            var.log.debug("Exit %s for %s: time-independent.",
                self.__class__.__name__, var.full_name)
            return ds
        cal = t_coord.attrs['calendar']
        dt_range = var.T.range
        # lower/upper are earliest/latest datetimes consistent with the date we
        # were given, up to the precision that was specified (eg lower for "2000"
        # would be Jan 1, 2000, and upper would be Dec 31).
        dt_start_lower = self.cast_to_cftime(dt_range.start.lower, cal)
        dt_start_upper = self.cast_to_cftime(dt_range.start.upper, cal)
        dt_end_lower = self.cast_to_cftime(dt_range.end.lower, cal)
        dt_end_upper = self.cast_to_cftime(dt_range.end.upper, cal)
        t_start = t_coord.values[0]
        t_end = t_coord.values[-1]
        t_size = t_coord.size

        if t_start > dt_start_upper:
            err_str = (f"Error: dataset start ({t_start}) is after "
                f"requested date range start ({dt_start_upper}).")
            var.log.error(err_str)
            raise IndexError(err_str)
        if t_end < dt_end_lower:
            err_str = (f"Error: dataset end ({t_end}) is before "
                f"requested date range end ({dt_end_lower}).")
            var.log.error(err_str)
            raise IndexError(err_str)

        ds = ds.sel({t_coord.name: slice(dt_start_lower, dt_end_upper)})
        new_t = ds.cf.dim_axes(tv_name).get('T')
        if t_size == new_t.size:
            var.log.info(("Requested dates for %s coincide with range of dataset "
                "'%s -- %s'; left unmodified."),
                var.full_name,
                new_t.values[0].strftime('%Y-%m-%d'),
                new_t.values[-1].strftime('%Y-%m-%d'),
            )
        else:
            var.log.info("Cropped date range of %s from '%s -- %s' to '%s -- %s'.",
                var.full_name,
                t_start.strftime('%Y-%m-%d'),
                t_end.strftime('%Y-%m-%d'),
                new_t.values[0].strftime('%Y-%m-%d'),
                new_t.values[-1].strftime('%Y-%m-%d'),
                tags=util.ObjectLogTag.NC_HISTORY
            )
        return ds

class PrecipRateToFluxFunction(PreprocessorFunctionBase):
    """Convert units on the dependent variable of var, as well as its
    (non-time) dimension coordinate axes, from what's specified in the dataset
    attributes to what's given in the :class:`~src.diagnostic.VarlistEntry`.
    """
    # Incorrect but matches convention for this conversion.
    _liquid_water_density = units.Units('1000.0 kg m-3')
    # list of regcognized standard_names for which transformation is applicable
    # NOTE: not exhaustive
    _std_name_tuples = [
        # flux in CF, rate is not
        ("precipitation_rate", "precipitation_flux"),
        # both in CF
        ("convective_precipitation_rate", "convective_precipitation_flux"),
        # not in CF; here for compatibility with NCAR-CAM
        ("large_scale_precipitation_rate", "large_scale_precipitation_flux")
    ]
    _rate_d = {tup[0]:tup[1] for tup in _std_name_tuples}
    _flux_d = {tup[1]:tup[0] for tup in _std_name_tuples}

    @edit_request_wrapper
    def edit_request(self, v, pod, data_mgr):
        """Edit the POD's Varlist prior to query. If v has a standard_name in the
        list above, insert an alternate varlist entry whose translation requests
        the complementary type of variable (ie, if given rate, add an entry for
        flux; if given flux, add an entry for rate.)
        """
        std_name = getattr(v, 'standard_name', "")
        if std_name not in self._rate_d and std_name not in self._flux_d:
            # logic not applicable to this VE; do nothing
            return None
        # construct dummy var to translate (rather than modifying std_name & units)
        # on v's translation) because v may not have a translation
        if std_name in self._rate_d:
            # requested rate, so add alternate for flux
            v_to_translate = copy_as_alternate(
                v, data_mgr,
                standard_name = self._rate_d[std_name],
                units = units.to_cfunits(v.units) * self._liquid_water_density
            )
        elif std_name in self._flux_d:
            # requested flux, so add alternate for rate
            v_to_translate = copy_as_alternate(
                v, data_mgr,
                standard_name = self._flux_d[std_name],
                units = units.to_cfunits(v.units) / self._liquid_water_density
            )

        translate = core.VariableTranslator()
        try:
            new_tv = translate.translate(data_mgr.attrs.convention, v_to_translate)
        except KeyError as exc:
            pod.log.debug(("%s edit_request on %s: caught %r when trying to "
                "translate '%s'; varlist unaltered."), self.__class__.__name__,
                v.full_name, exc, v_to_translate.standard_name)
            return None
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v

    def process(self, var, ds):
        std_name = getattr(var, 'standard_name', "")
        if std_name not in self._rate_d and std_name not in self._flux_d:
            # logic not applicable to this VE; do nothing
            return ds
        if units.units_equivalent(var.units, var.translation.units):
            # units can be converted by ConvertUnitsFunction; do nothing
            return ds

        # var.translation.units set by edit_request will have been overwritten by
        # DefaultDatasetParser to whatever they are in ds. Change them back.
        tv = var.translation # abbreviate
        if std_name in self._rate_d:
            # requested rate, received alternate for flux
            new_units = tv.units / self._liquid_water_density
        elif std_name in self._flux_d:
            # requested flux, received alternate for rate
            new_units = tv.units * self._liquid_water_density

        var.log.debug(("Assumed implicit factor of water density in units for %s: "
            "given %s, will convert as %s."),
            var.full_name, tv.units, new_units,
            tags=util.ObjectLogTag.NC_HISTORY
        )
        ds[tv.name].attrs['units'] = str(new_units)
        tv.units = new_units
        # actual conversion done by ConvertUnitsFunction; this assures
        # units.convert_dataarray is called with correct parameters.
        return ds

class ConvertUnitsFunction(PreprocessorFunctionBase):
    """Convert units on the dependent variable of var, as well as its
    (non-time) dimension coordinate axes, from what's specified in the dataset
    attributes to what's given in the :class:`~src.diagnostic.VarlistEntry`.
    """
    def process(self, var, ds):
        """Convert units on the dependent variable and coordinates of var from
        what's specified in the dataset attributes to what's given in the
        VarlistEntry *var*. Units attributes are updated on the
        :class:`~src.core.TranslatedVarlistEntry`.
        """
        tv = var.translation # abbreviate
        # convert dependent variable
        ds = units.convert_dataarray(
            ds, tv.name, src_unit=None, dest_unit=var.units, log=var.log
        )
        tv.units = var.units

        # convert coordinate dimensions and bounds
        for c in tv.dim_axes.values():
            if c.axis == 'T':
                continue # TODO: separate function to handle calendar conversion
            dest_c = var.axes[c.axis]
            ds = units.convert_dataarray(
                ds, c.name, src_unit=None, dest_unit=dest_c.units, log=var.log
            )
            if c.has_bounds and c.bounds_var.name in ds:
                ds = units.convert_dataarray(
                    ds, c.bounds_var.name, src_unit=None, dest_unit=dest_c.units,
                    log=var.log
                )
            c.units = dest_c.units

        # convert scalar coordinates
        for c in tv.scalar_coords:
            if c.name in ds:
                dest_c = var.axes[c.axis]
                ds = units.convert_dataarray(
                    ds, c.name, src_unit=None, dest_unit=dest_c.units,
                    log=var.log
                )
                c.units = dest_c.units
                c.value = ds[c.name].item()

        var.log.info("Converted units on %s.", var.full_name)
        return ds

class RenameVariablesFunction(PreprocessorFunctionBase):
    def process(self, var, ds):
        tv = var.translation # abbreviate
        rename_d = dict()
        # rename var
        if tv.name != var.name:
            var.log.debug("Rename '%s' variable in %s to '%s'.",
                tv.name, var.full_name, var.name,
                tags=util.ObjectLogTag.NC_HISTORY
            )
            rename_d[tv.name] = var.name
            tv.name = var.name

        # rename coords
        for c in tv.dim_axes.values():
            dest_c = var.axes[c.axis]
            if c.name != dest_c.name:
                var.log.debug("Rename %s axis of %s from '%s' to '%s'.",
                    c.axis, var.full_name, c.name, dest_c.name,
                    tags=util.ObjectLogTag.NC_HISTORY
                )
                rename_d[c.name] = dest_c.name
                c.name = dest_c.name
        # TODO: bounds??

        # rename scalar coords
        for c in tv.scalar_coords:
            if c.name in ds:
                dest_c = var.axes[c.axis]
                var.log.debug("Rename %s scalar coordinate of %s from '%s' to '%s'.",
                    c.axis, var.full_name, c.name, dest_c.name,
                    tags=util.ObjectLogTag.NC_HISTORY
                )
                rename_d[c.name] = dest_c.name
                c.name = dest_c.name

        return ds.rename(rename_d)

class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a single pressure level from a Dataset. Unit conversions of
    pressure are handled by `cfunits <https://ncas-cms.github.io/cfunits/index.html>`__,
    (see :doc:`src.units`) but paramateric vertical coordinates are
    *not* handled: interpolation is not implemented here. If the exact level
    is not provided by the data, KeyError is raised.
    """
    @edit_request_wrapper
    def edit_request(self, v, pod, data_mgr):
        """Edit the *pod*'s :class:`~src.diagnostic.Varlist` prior to data query.
        If given a :class:`~src.diagnostic.VarlistEntry` *v* which specifies a
        scalar Z coordinate, return a copy with that scalar_coordinate removed
        to be used as an alternate variable for *v*.
        """
        if not v.translation:
            # hit this if VE not defined for this model naming convention;
            # do nothing for this v
            return None
        elif v.translation.get_scalar('Z') is None:
            # hit this if VE didn't request Z level extraction; do nothing
            return None

        tv = v.translation # abbreviate
        if len(tv.scalar_coords) == 0:
            raise AssertionError # should never get here
        elif len(tv.scalar_coords) > 1:
            raise NotImplementedError()
        # wraps method in data_model; makes a modified copy of translated var
        # restore name to that of 4D data (eg. 'u500' -> 'ua')
        new_ax_set = set(v.axes_set).add('Z')
        if v.use_exact_name:
            new_tv_name = v.name
        else:
            new_tv_name = core.VariableTranslator().from_CF_name(
                data_mgr.attrs.convention, v.standard_name, new_ax_set
            )
        new_tv = tv.remove_scalar(
            tv.scalar_coords[0].axis,
            name = new_tv_name
        )
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v

    def process(self, var, ds):
        """Determine if level extraction is needed, and return appropriate slice
        of Dataset if it is.
        """
        _atol = 1.0e-3 # absolute tolerance for floating-point equality

        tv_name = var.name_in_model
        our_z = var.get_scalar('Z')
        if not our_z or not our_z.value:
            var.log.debug("Exit %s for %s: no level requested.",
                self.__class__.__name__, var.full_name)
            return ds
        if 'Z' not in ds[tv_name].cf.dim_axes_set:
            # maybe the ds we received has this level extracted already
            ds_z = ds.cf.get_scalar('Z', tv_name)
            if ds_z is None or isinstance(ds_z, xr_parser.PlaceholderScalarCoordinate):
                var.log.debug(("Exit %s for %s: %s %s Z level requested but value not "
                    "provided in scalar coordinate information; assuming correct."),
                    self.__class__.__name__, var.full_name, our_z.value, our_z.units)
                return ds
            else:
                # value (on var.translation) has already been checked by
                # xr_parser.DefaultDatasetParser
                var.log.debug(("Exit %s for %s: %s %s Z level requested and provided "
                    "by dataset."),
                    self.__class__.__name__, var.full_name, our_z.value, our_z.units)
                return ds

        # final case: Z coordinate present in data, so actually extract the level
        ds_z = ds.cf.dim_axes(tv_name)['Z']
        if ds_z is None:
            raise TypeError("No Z axis in dataset for %s.", var.full_name)
        try:
            ds_z_value = units.convert_scalar_coord(our_z, ds_z.units, log=var.log)
            ds = ds.sel(
                {ds_z.name: ds_z_value},
                method='nearest', # Allow for floating point roundoff in axis values
                tolerance=_atol,
                drop=False
            )
            var.log.info("Extracted %s %s level from Z axis ('%s') of %s.",
                ds_z_value, ds_z.units, ds_z.name, var.full_name,
                tags=util.ObjectLogTag.NC_HISTORY
            )
            # rename translated var to reflect renaming we're going to do
            # recall POD variable name env vars are set on this attribute
            var.translation.name = var.name
            # rename dependent variable
            return ds.rename({tv_name: var.name})
        except KeyError:
            # ds.sel failed; level wasn't present in coordinate axis
            raise KeyError((f"Z axis '{ds_z.name}' of {var.full_name} didn't "
                f"provide requested level ({our_z.value} {our_z.units}).\n"
                f"(Axis values ({ds_z.units}): {ds_z.values})"))
        except Exception as exc:
            raise ValueError((f"Caught exception extracting {our_z.value} {our_z.units} "
                f"level from '{ds_z.name}' coord of {var.full_name}.")) from exc

class ApplyScaleAndOffsetFunction(PreprocessorFunctionBase):
    """If the variable has ``scale_factor`` and ``add_offset`` attributes set,
    apply the corresponding constant linear transformation to the variable's
    values and unset these attributes. By default this function is not applied.

    See `CF convention documentation
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#attribute-appendix>`__
    on the ``scale_factor`` and ``add_offset`` attributes.
    """
    def process(self, var, ds):
        tv_name = var.translation.name
        ds_var = ds[tv_name]
        # CF standard says to scale first
        if ds_var.attrs.get('scale_factor', ''):
            scale_factor = float(ds_var.attrs['scale_factor'])
            ds_var *= scale_factor
            del ds_var.attrs['scale_factor']
            var.log.info("Scaled values of '%s' variable in %s by a factor of %f.",
                tv_name, var.full_name, scale_factor,
                tags=(util.ObjectLogTag.NC_HISTORY, util.ObjectLogTag.BANNER)
            )

        if ds_var.attrs.get('add_offset', ''):
            add_offset = float(ds_var.attrs['add_offset'])
            ds_var += add_offset
            del ds_var.attrs['add_offset']
            var.log.info("Added an offset of %f to values of '%s' variable in %s.",
                add_offset, tv_name, var.full_name,
                tags=(util.ObjectLogTag.NC_HISTORY, util.ObjectLogTag.BANNER)
            )

        return ds

# ==================================================

class MDTFPreprocessorBase(metaclass=util.MDTFABCMeta):
    """Base class for preprocessing data after it's been fetched, in order to
    put it into a format expected by PODs. The only functionality implemented
    here is parsing data axes and CF attributes; all other functionality is
    provided by :class:`PreprocessorFunctionBase` functions, which are called in
    order.
    """
    _XarrayParserClass = xr_parser.DefaultDatasetParser

    def __init__(self, data_mgr, pod):
        config = core.ConfigManager()
        self.overwrite_ds = config.get('overwrite_file_metadata', False)

        self.WK_DIR = data_mgr.MODEL_WK_DIR
        self.convention = data_mgr.attrs.convention
        self.pod_convention = pod.convention

        if getattr(pod, 'nc_largefile', False):
            self.nc_format = "NETCDF4_CLASSIC"
        else:
            self.nc_format = "NETCDF4"
        # HACK only used for _FillValue workaround in clean_output_encoding
        self.output_to_ncl = ('ncl' in pod.runtime_requirements)

        # initialize xarray parser
        self.parser = self._XarrayParserClass(data_mgr, pod)
        # initialize PreprocessorFunctionBase objects
        self.functions = [cls_(data_mgr, pod) for cls_ in self._functions]

    @property
    def _functions(self):
        """Determine which preprocessor functions are applicable to the current
        package run, defaulting to all of them.

        Returns:
            tuple of classes (inheriting from :class:`PreprocessorFunctionBase`)
            listing the preprocessing functions to be called, in order.
        """
        config = core.ConfigManager()
        if config.get('disable_preprocessor', False):
            # omit unit conversion functions; following two functions necessary
            # in all cases to obtain correct output
            return (
                CropDateRangeFunction, RenameVariablesFunction
            )
        else:
            # normal operation: run all functions
            return (
                CropDateRangeFunction,
                PrecipRateToFluxFunction, ConvertUnitsFunction,
                ExtractLevelFunction, RenameVariablesFunction
            )

    def edit_request(self, data_mgr, pod):
        """Edit *pod*'s data request, based on the child class's functionality. If
        the child class has a function that can transform data in format X to
        format Y and the POD requests X, this method should insert a
        backup/fallback request for Y.
        """
        for func in self.functions:
            func.edit_request(data_mgr, pod)

    def setup(self, data_mgr, pod):
        """Method to do additional configuration immediately before :meth:`process`
        is called on each variable for *pod*.
        """
        self.parser.setup(data_mgr, pod)

    @property
    def open_dataset_kwargs(self):
        """Arguments passed to xarray `open_dataset()
        <https://xarray.pydata.org/en/stable/generated/xarray.open_dataset.html>`__
        and `open_mfdataset()
        <https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.
        """
        return {
            "engine": "netcdf4",
            "decode_cf": False,     # all decoding done by DefaultDatasetParser
            "decode_coords": False, # so disable it here
            "decode_times": False,
            "use_cftime": False
        }

    @property
    def save_dataset_kwargs(self):
        """Arguments passed to xarray `to_netcdf()
        <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__.
        """
        return {
            "engine": "netcdf4",
            "format": self.nc_format
        }

    def read_one_file(self, var, path_list):
        if len(path_list) != 1:
            raise ValueError(f"{var.full_name}: Expected one file, got {path_list}.")
        var.log.debug("Loaded '%s'.", path_list[0], tags=util.ObjectLogTag.IN_FILE)
        return xr.open_dataset(
            path_list[0],
            **self.open_dataset_kwargs
        )

    @abc.abstractmethod
    def read_dataset(self, var):
        pass # return ds

    def clean_nc_var_encoding(self, var, name, ds_obj):
        """Clean up the ``attrs`` and ``encoding`` dicts of *obj* prior to
        writing to a netCDF file, as a workaround for the following known issues:

        - Missing attributes may be set to the sentinel value ``ATTR_NOT_FOUND``
          by :class:`xr_parser.DefaultDatasetParser`. Depending on context, this may not
          be an error, but attributes with this value need to be deleted before
          writing.
        - Delete the ``_FillValue`` attribute for all independent variables
          (coordinates and their bounds), which is specified in the CF conventions
          but isn't the xarray default; see
          `<https://github.com/pydata/xarray/issues/1598>`__.
        - 'NaN' is not recognized as a valid ``_FillValue`` by NCL (see
          `<https://www.ncl.ucar.edu/Support/talk_archives/2012/1689.html>`__),
          so unset the attribute for this case.
        - xarray `to_netcdf() <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__
          raises an error if attributes set on a variable have
          the same name as those used in its encoding, even if their values are
          the same. We delete these attributes prior to writing, after checking
          equality of values.
        """
        encoding = getattr(ds_obj, 'encoding', dict())
        attrs = getattr(ds_obj, 'attrs', dict())
        attrs_to_delete = set([])

        # mark attrs with sentinel value for deletion
        for k,v in attrs.items():
            if v == xr_parser.ATTR_NOT_FOUND:
                var.log.debug("Caught unset attribute '%s' of '%s'.", k, name)
                attrs_to_delete.add(k)
        # clean up _FillValue
        old_fillvalue = encoding.get('_FillValue', np.nan)
        if name != var.translation.name \
            or (self.output_to_ncl and np.isnan(old_fillvalue)):
            encoding['_FillValue'] = None
            attrs['_FillValue'] = None
            attrs_to_delete.add('_FillValue')
        # mark attrs duplicating values in encoding for deletion
        for k,v in encoding.items():
            if k in attrs:
                if isinstance(attrs[k], str) and isinstance(v, str):
                    compare_ = (attrs[k].lower() != v.lower())
                else:
                    compare_ = (attrs[k] != v)
                if compare_ and k.lower() != 'source':
                    var.log.warning(
                        "Conflict in '%s' attribute of '%s': '%s' != '%s'.",
                        k, name, v, attrs[k], tags=util.ObjectLogTag.NC_HISTORY
                    )
                attrs_to_delete.add(k)

        for k in attrs_to_delete:
            if k in attrs:
                del attrs[k]

    def clean_output_attrs(self, var, ds):
        """Call :meth:`clean_nc_var_encoding` on all sets of attributes in the
        Dataset *ds*.
        """
        def _clean_dict(obj):
            name = getattr(obj, 'name', 'dataset')
            encoding = getattr(obj, 'encoding', dict())
            attrs = getattr(obj, 'attrs', dict())
            for k,v in encoding.items():
                if k in attrs:
                    if isinstance(attrs[k], str) and isinstance(v, str):
                        compare_ = (attrs[k].lower() != v.lower())
                    else:
                        compare_ = (attrs[k] != v)
                    if compare_ and k.lower() != 'source':
                        _log.warning("Conflict in '%s' attribute of %s: %s != %s.",
                            k, name, v, attrs[k])
                    del attrs[k]

        for vv in ds.variables.values():
            _clean_dict(vv)
        _clean_dict(ds)

        if not getattr(var, 'is_static', True):
            t_coord = var.T
            ds_T = ds[t_coord.name]
            # ensure we set time units in as many places as possible
            if 'units' in ds_T.attrs and 'units' not in ds_T.encoding:
                ds_T.encoding['units'] = ds_T.attrs['units']
            if t_coord.has_bounds:
                ds[t_coord.bounds_var.name].encoding['units'] = ds_T.encoding['units']

        for v_name, ds_v in ds.variables.items():
            self.clean_nc_var_encoding(var, v_name, ds_v)
        self.clean_nc_var_encoding(var, 'dataset', ds)
        return ds

    def log_history_attr(self, var, ds):
        """Update ``history`` attribute on xarray Dataset *ds* with log records
        of any metadata modifications logged to *var*'s \_nc_history_log log handler.
        Out of simplicity, events are written in chronological rather than
        reverse chronological order.
        """
        attrs = getattr(ds, 'attrs', dict())
        hist = attrs.get('history', "")
        var._nc_history_log.flush()
        hist += '\n' + var._nc_history_log.buffer_contents()
        var._nc_history_log.close()
        ds.attrs['history'] = hist
        return ds

    def write_dataset(self, var, ds):
        """Writes processed Dataset *ds* to location specified by ``dest_path``
        attribute of *var*, using xarray `to_netcdf()
        <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__
        """
        # TODO: remove any netCDF Variables that were present in the input file
        # (and ds) but not needed for PODs' data request
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        var.log.debug("Writing '%s'.", var.dest_path, tags=util.ObjectLogTag.OUT_FILE)
        if var.is_static:
            unlimited_dims = []
        else:
            unlimited_dims = [var.T.name]
        ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs,
            unlimited_dims=unlimited_dims
        )
        ds.close()

    def load_ds(self, var):
        """Top-level method to load dataset and parse metadata; spun out so that
        child classes can modify it. Calls child class :meth:`read_dataset`.
        """
        try:
            ds = self.read_dataset(var)
        except Exception as exc:
            raise util.chain_exc(exc, (f"loading "
                f"dataset for {var.full_name}."), util.DataPreprocessEvent)
        var.log.debug("Read %d mb for %s.", ds.nbytes / (1024*1024), var.full_name)
        try:
            ds = self.parser.parse(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, (f"parsing file "
                f"metadata for {var.full_name}."), util.DataPreprocessEvent)
        return ds

    def process_ds(self, var, ds):
        """Top-level method to apply selected functions to dataset; spun out so
        that child classes can modify it.
        """
        for f in self.functions:
            try:
                var.log.debug("Calling %s on %s.", f.__class__.__name__,
                    var.full_name)
                ds = f.process(var, ds)
            except Exception as exc:
                raise util.chain_exc(exc, (f"Preprocessing on {var.full_name} "
                    f"failed at {f.__class__.__name__}."),
                    util.DataPreprocessEvent
                )
        return ds

    def write_ds(self, var, ds):
        """Top-level method to write out processed dataset; spun out so
        that child classes can modify it. Calls child class :meth:`write_dataset`.
        """
        path_str = util.abbreviate_path(var.dest_path, self.WK_DIR, '$WK_DIR')
        var.log.info("Writing %d mb to %s", ds.nbytes / (1024*1024), path_str)
        try:
            ds = self.clean_output_attrs(var, ds)
            ds = self.log_history_attr(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, (f"cleaning attributes to "
                f"write data for {var.full_name}."), util.DataPreprocessEvent)
        try:
            self.write_dataset(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, f"writing data for {var.full_name}.",
                util.DataPreprocessEvent)
        del ds # shouldn't be necessary

    def process(self, var):
        """Top-level wrapper for doing all preprocessing of data files.
        """
        ds = self.load_ds(var)
        ds = self.process_ds(var, ds)
        self.write_ds(var, ds)
        var.log.debug("Successful preprocessor exit on %s.", var)


class SingleFilePreprocessor(MDTFPreprocessorBase):
    """A :class:`MDTFPreprocessorBase` for preprocessing model data that is
    provided as a single netcdf file per variable, for example the sample model
    data.
    """
    def read_dataset(self, var):
        """Read a single file Dataset specified by the ``local_data`` attribute of
        *var*, using :meth:`read_one_file`.
        """
        return self.read_one_file(var, var.local_data)

class DaskMultiFilePreprocessor(MDTFPreprocessorBase):
    """A :class:`MDTFPreprocessorBase` that uses xarray's dask support to
    preprocessing model data provided as one or several netcdf files per
    variable.
    """
    _file_preproc_functions = util.abstract_attribute()

    def __init__(self, data_mgr, pod):
        super(DaskMultiFilePreprocessor, self).__init__(data_mgr, pod)
        # initialize PreprocessorFunctionBase objects
        self.file_preproc_functions = \
            [cls_(data_mgr, pod) for cls_ in self._file_preproc_functions]

    def edit_request(self, data_mgr, pod):
        """Edit POD's data request, based on the child class's functionality. If
        the child class has a function that can transform data in format X to
        format Y and the POD requests X, this method should insert a
        backup/fallback request for Y.
        """
        for func in self.file_preproc_functions:
            func.edit_request(data_mgr, pod)
        super(DaskMultiFilePreprocessor, self).edit_request(data_mgr, pod)

    def read_dataset(self, var):
        """Open multi-file Dataset specified by the ``local_data`` attribute of
        *var*, wrapping xarray `open_mfdataset()
        <https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.
        """
        def _file_preproc(ds):
            for f in self.file_preproc_functions:
                ds = f.process(var, ds)
            return ds

        assert var.local_data
        if len(var.local_data) == 1:
            ds = self.read_one_file(var, var.local_data)
            return _file_preproc(ds)
        else:
            assert not var.is_static # just to be safe
            var.log.debug("Loaded multi-file dataset of %d files:\n%s",
                len(var.local_data),
                '\n'.join(4*' ' + f"'{f}'" for f in var.local_data),
                tags=util.ObjectLogTag.IN_FILE
            )
            return xr.open_mfdataset(
                var.local_data,
                combine="by_coords",
                # only time-dependent variables and coords are concat'ed:
                data_vars="minimal", coords="minimal",
                # all non-concat'ed vars must be the same; global attrs can differ
                # from file to file; values in ds are taken from first file
                compat="equals",
                join="exact",        # raise ValueError if non-time dims conflict
                parallel=True,       # use dask
                preprocess=_file_preproc,
                **self.open_dataset_kwargs
            )


# -------------------------------------------------

class SampleDataPreprocessor(SingleFilePreprocessor):
    """Implementation class for :class:`MDTFPreprocessorBase` intended for use
    on sample model data distributed with the package. Assumes all data is in
    one netCDF file.
    """
    # Need to include all functions; ExtractLevelFunction needed for
    # NCAR-CAM5.timeslice for Travis CI
    pass

class DefaultPreprocessor(DaskMultiFilePreprocessor):
    """Implementation class for :class:`MDTFPreprocessorBase` for the general
    use case. Includes all implemented functionality and handles multi-file data.
    """
    _file_preproc_functions = []
