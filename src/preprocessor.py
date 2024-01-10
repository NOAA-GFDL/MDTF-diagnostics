"""Functionality for transforming model data into the format expected by PODs
once it's been downloaded; see :doc:`fmwk_preprocess`.
"""
import os
import shutil
import abc
import dataclasses
import datetime
import functools
from src import util, core, varlistentry_util, diagnostic, xr_parser, units
import cftime
import numpy as np
import xarray as xr

import logging

_log = logging.getLogger(__name__)


def copy_as_alternate(old_v, data_mgr, **kwargs):
    """Wrapper for :py:func:`dataclasses.replace` that creates a copy of an
    existing variable (:class:`~src.diagnostic.VarlistEntry`) *old_v* and sets appropriate
    attributes to designate it as an alternate variable.
    """
    if 'coords' not in kwargs:
        # dims, scalar_coords are derived attributes set by __post_init__
        # if we aren't changing them, must use this syntax to pass them through
        kwargs['coords'] = (old_v.dims + old_v.scalar_coords)
    new_v = dataclasses.replace(
        old_v,
        _id=util.MDTF_ID(),  # assign distinct ID
        stage=varlistentry_util.VarlistEntryStage.INITED,  # reset state from old_v
        status=core.ObjectStatus.INACTIVE,  # new VE meant as an alternate
        requirement=varlistentry_util.VarlistEntryRequirement.ALTERNATE,
        # plus the specific replacements we want to make:
        **kwargs
    )
    return new_v


def edit_request_wrapper(wrapped_edit_request_func):
    """Decorator implementing the most typical use case for
    :meth:`~PreprocessorFunctionBase.edit_request` in preprocessor functions, in
    which we look at each variable request in the varlist separately and,
    optionally, insert a new alternate :class:`~src.diagnostic.VarlistEntry`
    after it, based on that variable.

    This decorator wraps a function (*wrapped_edit_request_func*) which either
    constructs and returns the desired new alternate
    :class:`~src.diagnostic.VarlistEntry`, or returns None if no alternates are
    to be added for the given variable request. It adds logic for updating the
    list of alternates for the pod's varlist.

    .. note::

       This decorator alters the signature of the decorated function, which is
       not in keeping with Python best practices. The expected signature of
       *wrapped_edit_request_func* is (:class:`~src.diagnostic.VarlistEntry` *v*,
       :class:`~src.diagnostic.Diagnostic` *pod*, *data_mgr*), while the
       signature of the returned function is that of
       :meth:`PreprocessorFunctionBase.edit_request`.
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
                new_v_t_name = (str(new_v.translation)
                                if getattr(new_v, 'translation', None) is not None
                                else "(not translated)")
                v_t_name = (str(v.translation) if getattr(v, 'translation', None)
                                                  is not None else "(not translated)")
                pod.log.debug("%s for %s: add translated %s as alternate for %s.",
                              self.__class__.__name__, v.full_name, new_v_t_name, v_t_name)
                new_varlist.append(v)
                new_varlist.append(new_v)
        pod.varlist = diagnostic.Varlist(contents=new_varlist)

    return wrapped_edit_request


def multirun_edit_request_wrapper(multirun_wrapped_edit_request_func):
    """Decorator implementing the most typical use case for
    :meth:`~PreprocessorFunctionBase.edit_request` in multirun preprocessor functions, in
    which we loop through each case, look at each variable request  in the varlist separately and,
    optionally, insert a new alternate :class:`~src.diagnostic.VarlistEntry`
    after it, based on that variable.

    This decorator wraps a function (*multirun_wrapped_edit_request_func*) which either
    constructs and returns the desired new alternate
    :class:`~src.diagnostic.VarlistEntry`, or returns None if no alternates are
    to be added for the given variable request. It adds logic for updating the
    list of alternates for each cases varlist.

    .. note::

       This decorator alters the signature of the decorated function, which is
       not in keeping with Python best practices. The expected signature of
       *wrapped_edit_request_func* is (:class:`~src.diagnostic.VarlistEntry` *v*,
       :class:`~src.diagnostic.MultirunDiagnostic` *data_mgr*), while the
       signature of the returned function is that of
       :meth:`PreprocessorFunctionBase.edit_request`.
    """

    @functools.wraps(multirun_wrapped_edit_request_func)
    def wrapped_edit_request(self, data_mgr):
        for case_name, case_d in data_mgr.cases.items():
            new_varlist = []
            for v in case_d.varlist.iter_contents():
                new_v = multirun_wrapped_edit_request_func(self, v, data_mgr)
                if new_v is None:
                    # no change, pass through VE unaltered
                    new_varlist.append(v)
                    continue
                else:
                    # insert new_v between v itself and v's old alternate sets
                    # in varlist query order
                    new_v.alternates = v.alternates
                    v.alternates = [[new_v]]
                    new_v_t_name = (str(new_v.translation)
                                    if getattr(new_v, 'translation', None) is not None
                                    else "(not translated)")
                    v_t_name = (str(v.translation) if getattr(v, 'translation', None)
                                                      is not None else "(not translated)")
                    case_d.log.debug("%s for %s: add translated %s as alternate for %s.",
                                     self.__class__.__name__, v.full_name, new_v_t_name, v_t_name)
                    new_varlist.append(v)
                    new_varlist.append(new_v)
            case_d.varlist = diagnostic.MultirunVarlist(contents=new_varlist)

    return wrapped_edit_request


class PreprocessorFunctionBase(abc.ABC):
    """Abstract interface for implementing a specific preprocessing functionality.
    As described in :doc:`fmwk_preprocess`, each preprocessing operation is
    implemented as a separate child class of this class and called sequentially
    by the preprocessor. It's up to individual Preprocessor child classes to
    select which functions to use, and in what order to perform them (via their
    ``functions`` property.)

    Each PreprocessorFunction needs to implement two methods:

    - :meth:`edit_request`, which inserts alternate
      :class:`~src.diagnostic.VarlistEntry` objects to the data request,
      describing additional potential types of data which the preprocessor
      function is capable of converting into the format requested by the POD.
    - :meth:`process`, which actually implements the data format conversion.
    """

    def __init__(self, data_mgr, *args):
        """Called during Preprocessor's init."""
        pass

    def edit_request(self, data_mgr, *args):
        """Edit the data requested in *pod*'s :class:`~src.diagnostic.Varlist`
        queue, based on the transformations the functionality can perform (in
        :meth:`process`). If the function can transform data in format *X* to
        format *Y* and the POD requests *X*, this method should insert an
        alternate variable request (:class:`~src.diagnostic.VarlistEntry`) for
        *Y*.

        Args:
            data_mgr: Parent data source instance, used read-only to obtain
                initialization information not available from individual PODs.
        """
        pass

    @abc.abstractmethod
    def process(self, var, dataset, *args):
        """Apply the format conversion implemented in this PreprocessorFunction
        to the input dataset *dataset*, according to the request made in *var*.

        Args:
            var (:class:`~src.diagnostic.VarlistEntry`): POD varlist entry
                instance describing POD's data request, which is the desired end
                result of the conversion implemented by this method.
            dataset: `xarray.Dataset
                <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__
                instance.

        Returns:
            Modified *dataset*.
        """
        return dataset


class CropDateRangeFunction(PreprocessorFunctionBase):
    """A PreprocessorFunction which truncates the date range (time axis) of
    the dataset to the user-requested analysis period.
    """

    @staticmethod
    def cast_to_cftime(dt: datetime.datetime, calendar):
        """Workaround to cast a python :py:class:`~datetime.datetime` object *dt*
        to a
        `cftime.datetime <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        object with a specified *calendar*. Python's standard library has no
        support for different calendars (all datetime objects use the proleptic
        Gregorian calendar.)
        """
        # NB "tm_mday" is not a typo
        t = dt.timetuple()
        tt = (getattr(t, attr_) for attr_ in
              ('tm_year', 'tm_mon', 'tm_mday', 'tm_hour', 'tm_min', 'tm_sec'))
        return cftime.datetime(*tt, calendar=calendar)

    def edit_request(self, data_mgr, pod):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass

    def process(self, var, ds, *args):
        """Parse quantities related to the calendar for time-dependent data and
        truncate the date range of model dataset *ds*.

        In particular, the *var*\'s ``date_range`` attribute was set from the
        user's input before we knew the calendar being used by the model. The
        workaround here to cast those values into `cftime.datetime
        <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        objects so they can be compared with the model data's time axis.
        """
        tv_name = var.name_in_model
        t_coord = ds.cf.dim_axes(tv_name).get('T', None)
        if t_coord is None:
            var.log.debug("Exit %s for %s: time-independent.",
                          self.__class__.__name__, var.full_name)
            return ds
        # time coordinate will be a list if variable has
        # multiple coordinates/coordinate attributes
        if isinstance(t_coord, list):
            cal = t_coord[0].attrs['calendar']
            t_start = t_coord[0].values[0]
            t_end = t_coord[0].values[-1]
            t_size = t_coord[0].size
        else:
            cal = t_coord.attrs['calendar']
            t_start = t_coord.values[0]
            t_end = t_coord.values[-1]
            t_size = t_coord.size
        dt_range = var.T.range
        # lower/upper are earliest/latest datetimes consistent with the date we
        # were given, up to the precision that was specified (eg lower for "2000"
        # would be Jan 1, 2000, and upper would be Dec 31).

        # match date range hours to dataset hours if necessary
        # this is a kluge to support the timeslice data and similar datasets that
        # do not begin at hour zero
        if dt_range.start.lower.hour != t_start.hour:
            var.log.info("Variable %s data starts at hour %s", var.full_name, t_start.hour)
            dt_start_upper_new = datetime.datetime(dt_range.start.upper.year,
                                                   dt_range.start.upper.month,
                                                   dt_range.start.upper.day,
                                                   t_start.hour,
                                                   t_start.minute,
                                                   t_start.second)
            dt_start_lower_new = datetime.datetime(dt_range.start.lower.year,
                                                   dt_range.start.lower.month,
                                                   dt_range.start.lower.day,
                                                   t_start.hour,
                                                   t_start.minute,
                                                   t_start.second)
            dt_start_lower = self.cast_to_cftime(dt_start_lower_new, cal)
            dt_start_upper = self.cast_to_cftime(dt_start_upper_new, cal)
        else:
            dt_start_lower = self.cast_to_cftime(dt_range.start.lower, cal)
            dt_start_upper = self.cast_to_cftime(dt_range.start.upper, cal)
        if dt_range.end.lower.hour != t_end.hour:
            var.log.info("Variable %s data ends at hour %s", var.full_name, t_end.hour)
            dt_end_lower_new = datetime.datetime(dt_range.end.lower.year,
                                                 dt_range.end.lower.month,
                                                 dt_range.end.lower.day,
                                                 t_end.hour,
                                                 t_end.minute,
                                                 t_end.second)
            dt_end_upper_new = datetime.datetime(dt_range.end.upper.year,
                                                 dt_range.end.upper.month,
                                                 dt_range.end.upper.day,
                                                 t_end.hour,
                                                 t_end.minute,
                                                 t_end.second)
            dt_end_lower = self.cast_to_cftime(dt_end_lower_new, cal)
            dt_end_upper = self.cast_to_cftime(dt_end_upper_new, cal)
        else:
            dt_end_lower = self.cast_to_cftime(dt_range.end.lower, cal)
            dt_end_upper = self.cast_to_cftime(dt_range.end.upper, cal)

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
        if isinstance(t_coord, list):
            ds = ds.sel({t_coord[0].name: slice(dt_start_lower, dt_end_upper)})
        else:
            ds = ds.sel({t_coord.name: slice(dt_start_lower, dt_end_upper)})
        new_t = ds.cf.dim_axes(tv_name).get('T')
        if isinstance(new_t, list):
            nt_size = new_t[0].size
            nt_values = new_t[0].values
        else:
            nt_size = new_t.size
            nt_values = new_t.values
        if t_size == nt_size:
            var.log.info(("Requested dates for %s coincide with range of dataset "
                          "'%s -- %s'; left unmodified."),
                         var.full_name,
                         nt_values[0].strftime('%Y-%m-%d'),
                         nt_values[-1].strftime('%Y-%m-%d'),
                         )
        else:
            var.log.info("Cropped date range of %s from '%s -- %s' to '%s -- %s'.",
                         var.full_name,
                         t_start.strftime('%Y-%m-%d'),
                         t_end.strftime('%Y-%m-%d'),
                         nt_values[0].strftime('%Y-%m-%d'),
                         nt_values[-1].strftime('%Y-%m-%d'),
                         tags=util.ObjectLogTag.NC_HISTORY
                         )
        return ds


class PrecipRateToFluxFunction(PreprocessorFunctionBase):
    """A PreprocessorFunction which converts the dependent variable's units, for
    the specific case of precipitation. Flux and precip rate differ by a factor
    of the density of water, so can't be handled by the udunits2 implementation
    provided by :class:`~src.units.Units`. Instead, they're handled here as a
    special case. The general case of unit conversion is handled by
    :class:`ConvertUnitsFunction`.

    CF ``standard_names`` recognized for the conversion are ``precipitation_flux``,
    ``convective_precipitation_flux``, ``large_scale_precipitation_flux``, and
    likewise for ``*_rate``.
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
    _rate_d = {tup[0]: tup[1] for tup in _std_name_tuples}
    _flux_d = {tup[1]: tup[0] for tup in _std_name_tuples}

    @edit_request_wrapper
    def edit_request(self, v, pod, data_mgr):
        """Edit *pod*\'s Varlist prior to query. If the
        :class:`~src.diagnostic.VarlistEntry` *v* has a ``standard_name`` in the
        recognized list, insert an alternate VarlistEntry whose translation
        requests the complementary type of variable (i.e., if given rate, add an
        entry for flux; if given flux, add an entry for rate.)

        The signature of this method is altered by the :func:`edit_request_wrapper`
        decorator.
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
                standard_name=self._rate_d[std_name],
                units=units.to_cfunits(v.units) * self._liquid_water_density
            )
        elif std_name in self._flux_d:
            # requested flux, so add alternate for rate
            v_to_translate = copy_as_alternate(
                v, data_mgr,
                standard_name=self._flux_d[std_name],
                units=units.to_cfunits(v.units) / self._liquid_water_density
            )

        translate = core.VariableTranslator()
        try:
            new_tv = translate.translate(data_mgr.attrs.convention, v_to_translate)
        except KeyError as exc:
            pod.log.debug(('%s edit_request on %s: caught %r when trying to '
                           'translate \'%s\'; varlist unaltered.'), self.__class__.__name__,
                          v.full_name, exc, v_to_translate.standard_name)
            return None
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v

    def process(self, var, ds, *args):
        """Convert units of dependent variable *ds* between precip rate and
        precip flux, as specified by the desired units given in *var*. If the
        ``standard_name`` of *ds* is not in the recognized list, return it
        unaltered.
        """
        std_name = getattr(var, 'standard_name', "")
        if std_name not in self._rate_d and std_name not in self._flux_d:
            # logic not applicable to this VE; do nothing
            return ds
        if units.units_equivalent(var.units, var.translation.units):
            # units can be converted by ConvertUnitsFunction; do nothing
            return ds

        # var.translation.units set by edit_request will have been overwritten by
        # DefaultDatasetParser to whatever they are in ds. Change them back.
        tv = var.translation  # abbreviate
        if std_name in self._rate_d:
            # requested rate, received alternate for flux
            new_units = tv.units / self._liquid_water_density
        elif std_name in self._flux_d:
            # requested flux, received alternate for rate
            new_units = tv.units * self._liquid_water_density

        var.log.debug(('Assumed implicit factor of water density in units for %s: '
                       'given %s, will convert as %s.'),
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
    attributes to what's requested in the :class:`~src.diagnostic.VarlistEntry`.

    Unit conversion is implemented by
    `cfunits <https://ncas-cms.github.io/cfunits/index.html>`__; see
    :doc:`src.units`.
    """

    def edit_request(self, data_mgr, pod):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass

    def process(self, var, ds, *args):
        """Convert units on the dependent variable and coordinates of var from
        what's specified in the dataset attributes to what's given in the
        VarlistEntry *var*. Units attributes are updated on the
        :class:`~src.core.TranslatedVarlistEntry`.
        """
        tv = var.translation  # abbreviate
        # convert dependent variable
        ds = units.convert_dataarray(
            ds, tv.name, src_unit=None, dest_unit=var.units, log=var.log
        )
        tv.units = var.units

        # convert coordinate dimensions and bounds
        for c in tv.dim_axes.values():
            if c.axis == 'T':
                continue  # TODO: separate function to handle calendar conversion
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
    """Renames dependent variables and coordinates to what's expected by the POD.
    """

    def edit_request(self, data_mgr, pod):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass

    def process(self, var, ds, *args):
        """Change the names of the DataArrays with Dataset *ds* to the names
        specified by the :class:`~src.diagnostic.VarlistEntry` *var*. Names of
        the dependent variable and all dimension coordinates and scalar
        coordinates (vertical levels) are changed in-place.
        """
        tv = var.translation  # abbreviate
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


class AssociatedVariablesFunction(PreprocessorFunctionBase):
    """Preprocessor class to copy associated variables to wkdir"""

    def process(self, var, ds, *args):

        try:
            # get string labels from variable object
            pod_wkdir = var._parent.POD_WK_DIR
            casename = var._parent._parent.name

            # iterate over active associated files and get current local paths
            associated_files = list(
                var.iter_associated_files_keys(status=core.ObjectStatus.ACTIVE)
            )
            associated_files = [d_key.local_data for d_key in associated_files]

            # flatten a list of nested lists
            associated_files = [
                d_key for sublist in associated_files for d_key in sublist
            ]

            # construct destination paths in wkdir
            associated_files_dst = [
                f"{pod_wkdir}/assoc/{casename}.{os.path.basename(x)}"
                for x in associated_files
            ]

            # create `assoc` directory and copy files
            os.makedirs(f"{pod_wkdir}/assoc/", exist_ok=True)
            _ = [
                shutil.copy(*x)
                for x in list(zip(associated_files, associated_files_dst))
            ]

            # Replace object attribute with CSV list of final paths in wkdir
            var.associated_files = str(",").join(associated_files_dst)

        except Exception as exc:
            var.log.debug(
                f"Error encountered with preprocessing associated files: {exc}"
            )

        return ds


class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a requested pressure level from a Dataset containing a 3D variable.

    .. note::

       Unit conversion on the vertical coordinate is implemented, but
       parametric vertical coordinates and coordinate interpolation are not.
       If a pressure level is requested that isn't present in the data,
       :meth:`process` raises a KeyError.
    """

    @edit_request_wrapper
    def edit_request(self, v, pod, data_mgr):
        """Edit the *pod*'s :class:`~src.diagnostic.Varlist` prior to data query.
        If given a :class:`~src.diagnostic.VarlistEntry` *v* has a
        ``scalar_coordinate`` for the Z axis (i.e., is requesting data on a
        pressure level), return a copy of *v* with that ``scalar_coordinate``
        removed (i.e., requesting a full 3D variable) to be used as an alternate
        variable for *v*.

        The signature of this method is altered by the :func:`edit_request_wrapper`
        decorator.
        """
        if not v.translation:
            # hit this if VE not defined for this model naming convention;
            # do nothing for this v
            return None
        elif v.translation.get_scalar('Z') is None:
            # hit this if VE didn't request Z level extraction; do nothing
            return None

        tv = v.translation  # abbreviate
        if len(tv.scalar_coords) == 0:
            raise AssertionError  # should never get here
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
            name=new_tv_name
        )
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v

    def process(self, var, ds, *args):
        """Determine if level extraction is needed (if *var* has a scalar Z
        coordinate and Dataset *ds* is 3D). If so, return the appropriate 2D
        slice of *ds*, otherwise pass through *ds* unaltered.
        """
        _atol = 1.0e-3  # absolute tolerance for floating-point equality

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
        if isinstance(ds_z, list) and len(ds_z) == 1:
            ds_z_units = ds_z[0].units
            ds_z_name = ds_z[0].name
            ds_z_values = ds_z[0].values
        else:
            ds_z_units = ds_z.units
            ds_z_name = ds_z.name
            ds_z_values = ds_z.values
        try:
            ds_z_value = units.convert_scalar_coord(our_z, ds_z_units, log=var.log)
            ds = ds.sel(
                {ds_z_name: ds_z_value},
                method='nearest',  # Allow for floating point roundoff in axis values
                tolerance=_atol,
                drop=False
            )
            var.log.info("Extracted %s %s level from Z axis ('%s') of %s.",
                         ds_z_value, ds_z_units, ds_z_name, var.full_name,
                         tags=util.ObjectLogTag.NC_HISTORY
                         )
            # rename translated var to reflect renaming we're going to do
            # recall POD variable name env vars are set on this attribute
            var.translation.name = var.name
            # rename dependent variable
            return ds.rename({tv_name: var.name})
        except KeyError:
            # ds.sel failed; level wasn't present in coordinate axis
            raise KeyError((f"Z axis '{ds_z_name}' of {var.full_name} didn't "
                            f"provide requested level ({our_z.value} {our_z.units}).\n"
                            f"(Axis values ({ds_z.units}): {ds_z_values})"))
        except Exception as exc:
            raise ValueError((f"Caught exception extracting {our_z.value} {our_z.units} "
                              f"level from '{ds_z_name}' coord of {var.full_name}.")) from exc


class ApplyScaleAndOffsetFunction(PreprocessorFunctionBase):
    """If the Dataset has ``scale_factor`` and ``add_offset`` attributes set,
    apply the corresponding constant linear transformation to the dependent
    variable's values and unset these attributes. See `CF convention documentation
    <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#attribute-appendix>`__
    on the ``scale_factor`` and ``add_offset`` attributes.

    .. note::

       By default this function is not applied. It's only provided to implement
       workarounds for running the package on data with metadata (i.e., units)
       that are known to be incorrect.
    """

    def edit_request(self, data_mgr, pod):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass

    def process(self, var, ds, *args):
        """Retrieve the ``scale_factor`` and ``add_offset`` attributes from the
        dependent variable of *ds*, and if set, apply the linear transformation
        to the dependent variable. If both are set, the scaling is applied first
        (as specified in the CF conventions). The attributes are unset on the
        variable's DataArray after being applied.
        """
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
    convert it into a format expected by PODs.

    Preprocessor objects are instantiated on a per-POD basis, by the data source,
    and stored in the ``preprocessor`` attribute of the
    :class:`~src.diagnostic.Diagnostic` object. Each object is responsible for
    the data format conversion for that POD, by loading the locally downloaded
    model data into an xarray Dataset, calling the :meth:`~PreprocessorFunctionBase.process`
    method on each PreprocessorFunction object to actually perform the data
    format conversion, and writing out the converted Dataset to a local file
    which will be the input to that POD.
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
        """Determine which PreprocessorFunctions are applicable to the current
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
                ExtractLevelFunction, RenameVariablesFunction,
                AssociatedVariablesFunction
            )

    def edit_request(self, data_mgr, pod):
        """Top-level method to edit *pod*\'s data request, based on the child
        class's functionality. Calls the :meth:`~PreprocessorFunctionBase.edit_request`
        method on all included PreprocessorFunctions.
        """
        for func in self.functions:
            func.edit_request(data_mgr, pod)

    def setup(self, data_mgr, pod):
        """Method to do additional configuration immediately before :meth:`process`
        is called on each variable for *pod*. Implements metadata cleaning via
        the :doc:`src.xr_parser` (class specified in the ``_XarrayParserClass``
        attribute, default :class:`~src.xr_parser.DefaultDatasetParser`).
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
            "decode_cf": False,  # all decoding done by DefaultDatasetParser
            "decode_coords": False,  # so disable it here
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
        """Wraps xarray `open_dataset()
        <https://xarray.pydata.org/en/stable/generated/xarray.open_dataset.html>`__
        to load a single netCDF file.
        """
        if len(path_list) != 1:
            raise ValueError(f"{var.full_name}: Expected one file, got {path_list}.")
        var.log.debug("Loaded '%s'.", path_list[0], tags=util.ObjectLogTag.IN_FILE)
        return xr.open_dataset(
            path_list[0],
            **self.open_dataset_kwargs
        )

    @abc.abstractmethod
    def read_dataset(self, var):
        """Abstract method to load downloaded model data into an xarray Dataset,
        to be implemented by child classes.

        Args:
            var (:class:`~src.diagnostic.VarlistEntry`): POD varlist entry
                instance describing POD's data request, which is the desired end
                result of the conversion implemented by this method.

        Returns:
            xarray Dataset containing the model data requested by *var*.
        """
        pass  # return ds

    def clean_nc_var_encoding(self, var, name, ds_obj):
        """Clean up the ``attrs`` and ``encoding`` dicts of *ds_obj*
        prior to writing to a netCDF file, as a workaround for the following
        known issues:

        - Missing attributes may be set to the sentinel value ``ATTR_NOT_FOUND``
          by :class:`xr_parser.DefaultDatasetParser`. Depending on context, this
          may not be an error, but attributes with this value need to be deleted
          before writing.
        - Delete the ``_FillValue`` attribute for all independent variables
          (coordinates and their bounds), which is specified in the CF conventions
          but isn't the xarray default; see
          `<https://github.com/pydata/xarray/issues/1598>`__.
        - 'NaN' is not recognized as a valid ``_FillValue`` by NCL (see
          `<https://www.ncl.ucar.edu/Support/talk_archives/2012/1689.html>`__),
          so unset the attribute for this case.
        - xarray `to_netcdf()
          <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__
          raises an error if attributes set on a variable have
          the same name as those used in its encoding, even if their values are
          the same. We delete these attributes prior to writing, after checking
          equality of values.
        """
        encoding = getattr(ds_obj, 'encoding', dict())
        attrs = getattr(ds_obj, 'attrs', dict())
        attrs_to_delete = set([])

        # mark attrs with sentinel value for deletion
        for k, v in attrs.items():
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
        for k, v in encoding.items():
            if k in attrs:
                if isinstance(attrs[k], bytes):
                    compare_ = False
                elif isinstance(attrs[k], str) and isinstance(v, str):
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
        """Calls :meth:`clean_nc_var_encoding` on all sets of attributes in the
        Dataset *ds*.
        """

        def _clean_dict(obj):
            name = getattr(obj, 'name', 'dataset')
            encoding = getattr(obj, 'encoding', dict())
            attrs = getattr(obj, 'attrs', dict())
            for k, v in encoding.items():
                if k in attrs:
                    if isinstance(attrs[k], bytes):
                        compare_ = False
                    elif isinstance(attrs[k], str) and isinstance(v, str):
                        compare_ = (attrs[k].lower() != v.lower())
                    elif not isinstance(attrs[k], np.ndarray) and not hasattr(attrs[k], '__iter__'):
                        compare_ = (attrs[k] != v)
                    elif hasattr(attrs[k], '__iter__') and not isinstance(attrs[k], str) \
                            and not isinstance(attrs[k], bytes):
                        compare_ = (attrs[k].any() != v)
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
        """Update the netCDF ``history`` attribute on xarray Dataset *ds* with
        log records of any metadata modifications logged to *var*'s
        ``_nc_history_log`` log handler by the PreprocessorFunctions. Out of
        simplicity, events are written in chronological order rather than
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
        """Writes processed Dataset *ds* to location specified by the
        ``dest_path`` attribute of *var*, using xarray `to_netcdf()
        <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__.
        May be overwritten by child classes.
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
        child classes can modify it. Calls the :meth:`read_dataset` method
        implemented by the child class.
        """
        try:
            ds = self.read_dataset(var)
        except Exception as exc:
            raise util.chain_exc(exc, (f"loading "
                                       f"dataset for {var.full_name}."), util.DataPreprocessEvent)
        var.log.debug("Read %d mb for %s.", ds.nbytes / (1024 * 1024), var.full_name)
        try:
            ds = self.parser.parse(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, (f"parsing file "
                                       f"metadata for {var.full_name}."), util.DataPreprocessEvent)
        return ds

    def process_ds(self, var, ds):
        """Top-level method to call the :meth:`~PreprocessorFunctionBase.process`
        of each included PreprocessorFunction on the Dataset *ds*. Spun out into
        its own method so that child classes can modify it.
        """
        for f in self.functions:
            try:
                var.log.debug("Calling %s on %s.", f.__class__.__name__,
                              var.full_name)
                ds = f.process(var, ds)
            except Exception as exc:
                raise util.chain_exc(exc, (f'Preprocessing on {var.full_name} '
                                           f'failed at {f.__class__.__name__}.'),
                                     util.DataPreprocessEvent
                                     )
        return ds

    def write_ds(self, var, ds):
        """Top-level method to write out processed dataset *ds*; spun out so
        that child classes can modify it. Calls the :meth:`write_dataset` method
        implemented by the child class.
        """
        path_str = util.abbreviate_path(var.dest_path, self.WK_DIR, '$WK_DIR')
        var.log.info("Writing %d mb to %s", ds.nbytes / (1024 * 1024), path_str)
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
        del ds  # shouldn't be necessary

    def process(self, var):
        """Top-level wrapper method for doing all preprocessing of data files
        associated with the POD variable *var*.
        """
        var.log.info("Preprocessing %s.", var)
        ds = self.load_ds(var)
        ds = self.process_ds(var, ds)
        self.write_ds(var, ds)
        var.log.debug("Successful preprocessor exit on %s.", var)


class SingleFilePreprocessor(MDTFPreprocessorBase):
    """A Preprocessor class for preprocessing model data that's provided as a
    single netCDF file per variable, for example the POD's sample model data.

    Implemented separately in the event that we (or the user) doesn't want to
    bring in dask as an external dependency.
    """

    def read_dataset(self, var):
        """Read a single file Dataset specified by the ``local_data`` attribute of
        *var*, using :meth:`read_one_file`.
        """
        return self.read_one_file(var, var.local_data)


class NullPreprocessor(MDTFPreprocessorBase):
    """A class that skips preprocessing and just symlinks files from the input dir to the wkdir
    """

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
        # dummy attribute--no pp functions to perform
        self.functions = []

    def edit_request(self, data_mgr, pod):
        """Dummy implementation of edit_request to meet abstract base class requirements
        """
        pass

    def read_dataset(self, var):
        """Dummy implementation of read_dataset to meet abstract base class requirements
        """
        pass

    def process(self, var):
        """Top-level wrapper method for doing all preprocessing of data files
        associated with the POD variable *var*.
        """
        var.log.debug("Skipping preprocessing for %s.", var)


class DaskMultiFilePreprocessor(MDTFPreprocessorBase):
    """A Preprocessor class that uses xarray's dask support to
    preprocess model data provided as one or multiple netcdf files per
    variable, using xarray `open_mfdataset()
    <https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.
    """
    _file_preproc_functions = util.abstract_attribute()
    """List of PreprocessorFunctions to be executed on a per-file basis as the
    multi-file Dataset is being loaded, rather than afterwards as part of the
    :meth:`process`. Note that such functions will not be able to rely on the
    metadata cleaning done by xr_parser."""

    def __init__(self, data_mgr, pod):
        super(DaskMultiFilePreprocessor, self).__init__(data_mgr, pod)
        # initialize PreprocessorFunctionBase objects
        self.file_preproc_functions = \
            [cls_(data_mgr, pod) for cls_ in self._file_preproc_functions]

    def edit_request(self, data_mgr, pod):
        """Edit *pod*\'s data request, based on the child class's functionality. If
        the child class has a function that can transform data in format *X* to
        format *Y* and the POD requests *X*, this method should insert a
        backup/fallback request for *Y*.
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
            assert not var.is_static  # just to be safe
            var.log.debug("Loaded multi-file dataset of %d files:\n%s",
                          len(var.local_data),
                          '\n'.join(4 * ' ' + f"'{f}'" for f in var.local_data),
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
                join="exact",  # raise ValueError if non-time dims conflict
                parallel=True,  # use dask
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


class MultirunDaskMultiFilePreprocessor(DaskMultiFilePreprocessor):
    """A Preprocessor class that uses xarray's dask support to
    preprocess model data provided as one or multiple netcdf files per
    variable, using xarray `open_mfdataset()
    <https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.
    """
    _file_preproc_functions = []

    def __init__(self, data_mgr):
        # initialize PreprocessorFunctionBase objects
        self.file_preproc_functions = \
            [cls_(data_mgr) for cls_ in self._file_preproc_functions]

    def edit_request(self, data_mgr, *args):
        """Edit *pod*\'s data request, based on the child class's functionality. If
        the child class has a function that can transform data in format *X* to
        format *Y* and the POD requests *X*, this method should insert a
        backup/fallback request for *Y*.
        """
        for func in self.file_preproc_functions:
            func.edit_request(data_mgr, *args)


class MultirunDefaultPreprocessor(MultirunDaskMultiFilePreprocessor):
    """Implementation class for :class:`MDTFPreprocessorBase` intended for use
    on sample model data distributed with the package. Assumes all data for each
    multirun case is in one netCDF file.
    """
    _XarrayParserClass = xr_parser.MultirunDefaultDatasetParser

    def __init__(self, data_mgr):
        super(MultirunDefaultPreprocessor, self).__init__(data_mgr)
        config = core.ConfigManager()
        self.overwrite_ds = config.get('overwrite_file_metadata', False)

        self.WK_DIR = data_mgr.MODEL_WK_DIR
        self.convention = data_mgr.convention
        self.pod_convention = self.convention

        if not data_mgr.nc_largefile:
            self.nc_format = "NETCDF4_CLASSIC"
        else:
            self.nc_format = "NETCDF4"
        # HACK only used for _FillValue workaround in clean_output_encoding
        self.output_to_ncl = ('ncl' in data_mgr.runtime_requirements)

        # initialize xarray parser
        self.parser = self._XarrayParserClass(data_mgr)
        # initialize PreprocessorFunctionBase objects
        self.functions = [cls_(data_mgr) for cls_ in self._functions]

    @property
    def _functions(self):
        """Determine which PreprocessorFunctions are applicable to the current
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
                MultirunCropDateRangeFunction, MultirunRenameVariablesFunction
            )
        else:
            # normal operation: run all functions
            return (
                MultirunCropDateRangeFunction,
                MultirunPrecipRateToFluxFunction, MultirunConvertUnitsFunction,
                MultirunExtractLevelFunction, MultirunRenameVariablesFunction,
                MultirunAssociatedVariablesFunction
            )

    # Same as MDTFPreprocessorBase: edit_request, but only need data_mgr arg
    def edit_request(self, data_mgr, *args):
        """Top-level method to edit each case's data request in the data_mgr, based on the child
        class's functionality. Calls the :meth:`~PreprocessorFunctionBase.edit_request`
        method on all included PreprocessorFunctions.
        """
        for func in self.functions:
            func.edit_request(data_mgr, *args)

    def process(self, var, casename: str):
        """Top-level wrapper method for doing all preprocessing of data files
        associated with the POD variable *var*.
        """
        var.log.info("Preprocessing %s.", var)
        ds = self.load_ds(var)
        ds = self.process_ds(var, ds, casename)
        self.write_ds(var, ds)
        var.log.debug("Successful preprocessor exit on %s.", var)

    def process_ds(self, var, ds, casename: str):
        """Top-level method to call the :meth:`~PreprocessorFunctionBase.process`
        of each included PreprocessorFunction on the Dataset *ds*. Spun out into
        its own method so that child classes can modify it.
        """
        for f in self.functions:
            try:
                var.log.debug("Calling %s on %s.", f.__class__.__name__,
                              var.full_name)
                ds = f.process(var, ds, casename)
            except Exception as exc:
                raise util.chain_exc(exc, (f'Preprocessing on {var.full_name} '
                                           f'failed at {f.__class__.__name__}.'),
                                     util.DataPreprocessEvent
                                     )
        return ds

    def write_ds(self, var, ds):
        """Top-level method to write out processed dataset *ds*; spun out so
        that child classes can modify it. Calls the :meth:`write_dataset` method
        implemented by the child class.
        """
        for casename, wkdir in self.WK_DIR.items():
            if wkdir in var.dest_path:
                break

        path_str = util.abbreviate_path(var.dest_path, wkdir, '$WK_DIR')
        var.log.info("Writing %d mb to %s", ds.nbytes / (1024 * 1024), path_str)
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
        del ds  # shouldn't be necessary


class MultirunCropDateRangeFunction(CropDateRangeFunction):

    # Same as CropDateRangeFunction: edit_request, but only need data_mgr arg
    def edit_request(self, data_mgr, *args):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass


class MultirunRenameVariablesFunction(RenameVariablesFunction):
    """Renames dependent variables and coordinates to what's expected by the POD.
    """

    # Same as RenameVariablesFunction: edit_request, but only need data_mgr arg
    def edit_request(self, data_mgr, *args):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass


class MultirunPrecipRateToFluxFunction(PrecipRateToFluxFunction):
    """A PreprocessorFunction which converts the dependent variable's units, for
    the specific case of precipitation. Flux and precip rate differ by a factor
    of the density of water, so can't be handled by the udunits2 implementation
    provided by :class:`~src.units.Units`. Instead, they're handled here as a
    special case. The general case of unit conversion is handled by
    :class:`ConvertUnitsFunction`.

    CF ``standard_names`` recognized for the conversion are ``precipitation_flux``,
    ``convective_precipitation_flux``, ``large_scale_precipitation_flux``, and
    likewise for ``*_rate``.
    """

    @multirun_edit_request_wrapper
    def edit_request(self, v, data_mgr, *args):
        """Edit *case*\'s Varlist prior to query. If the
        :class:`~src.MultirunDiagnostic.VarlistEntry` *v* has a ``standard_name`` in the
        recognized list, insert an alternate VarlistEntry whose translation
        requests the complementary type of variable (i.e., if given rate, add an
        entry for flux; if given flux, add an entry for rate.)

        The signature of this method is altered by the :func:`multirun_edit_request_wrapper`
        decorator.
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
                standard_name=self._rate_d[std_name],
                units=units.to_cfunits(v.units) * self._liquid_water_density
            )
        elif std_name in self._flux_d:
            # requested flux, so add alternate for rate
            v_to_translate = copy_as_alternate(
                v, data_mgr,
                standard_name=self._flux_d[std_name],
                units=units.to_cfunits(v.units) / self._liquid_water_density
            )

        translate = core.VariableTranslator()
        try:
            new_tv = translate.translate(data_mgr.attrs.convention, v_to_translate)
        except KeyError as exc:
            self.log.debug(('%s edit_request on %s: caught %r when trying to '
                            'translate \'%s\'; varlist unaltered.'), self.__class__.__name__,
                           v.full_name, exc, v_to_translate.standard_name)
            return None
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v


class MultirunConvertUnitsFunction(ConvertUnitsFunction):
    """Convert units on the dependent variable of var, as well as its
    (non-time) dimension coordinate axes, from what's specified in the dataset
    attributes to what's requested in the :class:`~src.diagnostic.VarlistEntry`.

    Unit conversion is implemented by
    `cfunits <https://ncas-cms.github.io/cfunits/index.html>`__; see
    :doc:`src.units`.
    """

    # Same as ConvertUnitsFunction: edit_request, but only need data_mgr arg
    def edit_request(self, data_mgr, *args):
        """No-op for this PreprocessorFunction, since no alternate data is needed.
        """
        pass


class MultirunExtractLevelFunction(ExtractLevelFunction):
    """Extract a requested pressure level from a Dataset containing a 3D variable.

    .. note::

       Unit conversion on the vertical coordinate is implemented, but
       parametric vertical coordinates and coordinate interpolation are not.
       If a pressure level is requested that isn't present in the data,
       :meth:`process` raises a KeyError.
       This class is identical to parent ExtractLevelFunction except that pod data is obtained
       from data_mgr parameter with information from the MultirunDiagnostic object
       rather than the pod parameter
    """

    @multirun_edit_request_wrapper
    def edit_request(self, v, data_mgr, *args):
        """Edit the *pod*'s :class:`~src.diagnostic.Varlist` prior to data query.
        If given a :class:`~src.MultirunDiagnostic.VarlistEntry` *v* has a
        ``scalar_coordinate`` for the Z axis (i.e., is requesting data on a
        pressure level), return a copy of *v* with that ``scalar_coordinate``
        removed (i.e., requesting a full 3D variable) to be used as an alternate
        variable for *v*.

        The signature of this method is altered by the :func:`multirun_edit_request_wrapper`
        decorator.
        """
        if not v.translation:
            # hit this if VE not defined for this model naming convention;
            # do nothing for this v
            return None
        elif v.translation.get_scalar('Z') is None:
            # hit this if VE didn't request Z level extraction; do nothing
            return None

        tv = v.translation  # abbreviate
        if len(tv.scalar_coords) == 0:
            raise AssertionError  # should never get here
        elif len(tv.scalar_coords) > 1:
            raise NotImplementedError()
        # wraps method in data_model; makes a modified copy of translated var
        # restore name to that of 4D data (eg. 'u500' -> 'ua')
        new_ax_set = set(v.axes_set).add('Z')
        if v.use_exact_name:
            new_tv_name = v.name
        else:
            new_tv_name = core.VariableTranslator().from_CF_name(
                data_mgr.convention, v.standard_name, new_ax_set
            )

        new_tv = tv.remove_scalar(
            tv.scalar_coords[0].axis,
            name=new_tv_name
        )
        new_v = copy_as_alternate(v, data_mgr)
        new_v.translation = new_tv
        return new_v

    class MultirunApplyScaleAndOffsetFunction(ApplyScaleAndOffsetFunction):
        """If the Dataset has ``scale_factor`` and ``add_offset`` attributes set,
        apply the corresponding constant linear transformation to the dependent
        variable's values and unset these attributes. See `CF convention documentation
        <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#attribute-appendix>`__
        on the ``scale_factor`` and ``add_offset`` attributes.

        .. note::

           By default this function is not applied. It's only provided to implement
           workarounds for running the package on data with metadata (i.e., units)
           that are known to be incorrect.
        """

        # Same as ApplyScaleAndOffsetFunction: edit_request, but only need data_mgr arg
        def edit_request(self, data_mgr, *args):
            """No-op for this PreprocessorFunction, since no alternate data is needed.
            Overrides ApplyScaleAndOffsetFunction: edit_request, and does not have pod parameter
            """
            pass


class MultirunAssociatedVariablesFunction(AssociatedVariablesFunction):
    """Preprocessor class to copy associated variables to wkdir"""

    def process(self, var, ds, casename: str):

        try:
            # get string labels from variable object
            pod_wkdir = var._parent.POD_WK_DIR

            # iterate over active associated files and get current local paths
            associated_files = list(
                var.iter_associated_files_keys(status=core.ObjectStatus.ACTIVE)
            )
            associated_files = [d_key.local_data for d_key in associated_files]

            # flatten a list of nested lists
            associated_files = [
                d_key for sublist in associated_files for d_key in sublist
            ]

            # construct destination paths in wkdir
            associated_files_dst = [
                f"{pod_wkdir}/assoc/{casename}.{os.path.basename(x)}"
                for x in associated_files
            ]

            # create `assoc` directory and copy files
            os.makedirs(f"{pod_wkdir}/assoc/", exist_ok=True)
            _ = [
                shutil.copy(*x)
                for x in list(zip(associated_files, associated_files_dst))
            ]

            # Replace object attribute with CSV list of final paths in wkdir
            var.associated_files = str(",").join(associated_files_dst)

        except Exception as exc:
            var.log.debug(
                f"Error encountered with preprocessing associated files: {exc}"
            )

        return ds


class MultirunNullPreprocessor(MultirunDefaultPreprocessor):
    """A class that skips preprocessing and just symlinks files from the input dir to the wkdir
    """

    _XarrayParserClass = xr_parser.MultirunDefaultDatasetParser

    def __init__(self, data_mgr):
        config = core.ConfigManager()
        self.overwrite_ds = config.get('overwrite_file_metadata', False)

        self.WK_DIR = data_mgr.MODEL_WK_DIR
        self.convention = data_mgr.convention
        self.pod_convention = self.convention

        if not data_mgr.nc_largefile:
            self.nc_format = "NETCDF4_CLASSIC"
        else:
            self.nc_format = "NETCDF4"
        # HACK only used for _FillValue workaround in clean_output_encoding
        self.output_to_ncl = ('ncl' in data_mgr.runtime_requirements)

        # initialize xarray parser
        self.parser = self._XarrayParserClass(data_mgr)
        # Empty set since there's nothing to preprocess
        self.functions = []

    def edit_request(self, data_mgr, *args):
        """Dummy implementation of edit_request to meet abstract base class requirements
        """
        pass

    def read_dataset(self, var):
        """Dummy implementation of read_dataset to meet abstract base class requirements
        """
        pass

    def process(self, var):
        """Top-level wrapper method for doing all preprocessing of data files
        associated with the POD variable *var*.
        """
        var.log.debug("Skipping preprocessing for %s.", var)
