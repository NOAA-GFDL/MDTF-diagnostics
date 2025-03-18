"""Functionality for transforming model data into the format expected by PODs
once it's been downloaded`.
"""
import os
import shutil
import abc
import dataclasses
import datetime
import importlib
import pandas as pd
from src import util, varlist_util, translation, xr_parser, units
from src.util import datelabel as dl
import cftime
import intake
import numpy as np
import xarray as xr
import collections
import re


# TODO: Make the following lines a unit test
# import sys
# ROOT_DIR = os.path.abspath("../MDTF-diagnostics")
# sys.path.append(ROOT_DIR)
# user_scripts = importlib.import_module("user_scripts")
# from user_scripts import example_pp_script
# test_str = example_pp_script.test_example_script()

import logging

_log = logging.getLogger(__name__)
write_times = []


def copy_as_alternate(old_v, **kwargs):
    """Wrapper for :py:func:`dataclasses.replace` that creates a copy of an
    existing variable (:class:`~src.varlist.VarlistEntry`) *old_v* and sets appropriate
    attributes to designate it as an alternate variable.
    """
    if 'coords' not in kwargs:
        # dims, scalar_coords are derived attributes set by __post_init__
        # if we aren't changing them, must use this syntax to pass them through
        kwargs['coords'] = (old_v.dims + old_v.scalar_coords)
    new_v = dataclasses.replace(
        old_v,
        _id=util.MDTF_ID(),  # assign distinct ID
        status=util.ObjectStatus.INACTIVE,  # new VE meant as an alternate
        requirement=varlist_util.VarlistEntryRequirement.ALTERNATE,
        # plus the specific replacements we want to make:
        **kwargs
    )
    return new_v


class PreprocessorFunctionBase(abc.ABC):
    """Abstract interface for implementing a specific preprocessing functionality.
    Each preprocessing operation is
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

    def __init__(self, *args):
        """Called during Preprocessor's init."""
        pass

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """Edit the data requested in *pod*'s :class:`~src.diagnostic.Varlist`
        queue, based on the transformations the functionality can perform (in
        :meth:`process`). If the function can transform data in format *X* to
        format *Y* and the POD requests *X*, this method should insert an
        alternate variable request (:class:`~src.diagnostic.VarlistEntry`) for
        *Y*.
        """
        return v

    @abc.abstractmethod
    def execute(self, var: varlist_util.VarlistEntry,
                xr_dataset,
                **kwargs):
        """Apply the format conversion implemented in this PreprocessorFunction
        to the input dataset *dataset*, according to the request made in *var*.

        Args:
            var: dictionary of variable information
            xr_dataset: xarray dataset with information from ESM intake catalog

        Returns:
            Modified *dataset*.
        """
        pass


class PercentConversionFunction(PreprocessorFunctionBase):
    """A PreprocessorFunction which convers the dependent variable's units and values,
    for the specific case of percentages. ``0-1`` are not defined in the UDUNITS-2
    library. So, this function handles the case where we have to convert from
    ``0-1`` to ``%``.
    """

    _std_name_tuple = ('0-1', '%')

    def execute(self, var, ds, **kwargs):
        var_unit = getattr(var, "units", "")
        tv = var.translation  # abbreviate
        tv_unit = getattr(tv, "units", "")
        # 0-1 to %
        if str(tv_unit) == self._std_name_tuple[0] and str(var_unit) == self._std_name_tuple[1]:
            ds[tv.name].attrs['units'] = '%'
            ds[tv.name].values = ds[tv.name].values * 100
            return ds
        # % to 0-1
        if str(tv_unit) == self._std_name_tuple[1] and str(var_unit) == self._std_name_tuple[0]:
            ds[tv.name].attrs['units'] = '0-1'
            # sometimes % is [0,1] already
            if ds[tv.name].values[:, :, 3].max() < 1.5:
                return ds
            else:
                ds[tv.name].values = ds[tv.name].values / 100
                return ds

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
    # list of recognized standard_names for which transformation is applicable
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

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """Edit *pod*'s Varlist prior to query. If the
        :class:`~src.diagnostic.VarlistEntry` *v* has a ``standard_name`` in the
        recognized list, insert an alternate VarlistEntry whose translation
        requests the complementary type of variable (i.e., if given rate, add an
        entry for flux; if given flux, add an entry for rate.)

        The signature of this method is altered by the :func:`edit_request_wrapper`
        decorator.
        """

        # check non-translated variable entry to determine if POD expects flux/rate
        # then apply units conversion to variable.translation if necessary
        std_name = getattr(v, 'standard_name', "")
        if std_name not in self._rate_d and std_name not in self._flux_d:
            # logic not applicable to this VE; do nothing and return varlistEntry for
            # next function to run edit_request on
            return v
        # construct dummy var to translate (rather than modifying std_name & units)
        # on v's translation) because v may not have a translation
        if std_name in self._rate_d:
            # requested rate, so add alternate for flux
            v_to_translate = copy_as_alternate(
                v,
                standard_name=self._rate_d[std_name],
                units=units.to_cfunits(v.units) * self._liquid_water_density
            )
        elif std_name in self._flux_d:
            # requested flux, so add alternate for rate
            v_to_translate = copy_as_alternate(
                v,
                standard_name=self._flux_d[std_name],
                units=units.to_cfunits(v.units) / self._liquid_water_density
            )

        translate = translation.VariableTranslator()
        to_convention = None
        for key, val in kwargs.items():
            if 'to_convention' in key:
                to_convention = val.lower()
        # check if pod variable standard name is the same as translation standard name
        if std_name != v.translation.standard_name:
            try:
                # current varlist.translation object is already in to_convention format
                # so from_convention arg = to_convention arg in this translation call
                new_tv = translate.translate(v_to_translate, to_convention, to_convention)
            except KeyError as exc:
                v.log.debug(('%s edit_request on %s: caught %r when trying to '
                             'translate \'%s\'; varlist unaltered.'), self.__class__.__name__,
                            v.full_name, exc, v_to_translate.standard_name)
                return None
            v.alternates.append(v.translation)
            # new_v = copy_as_alternate(v)
            # new_v.translation = new_tv
            v.translation.name = new_tv.name
            v.translation.standard_name = new_tv.standard_name
            v.translation.units = new_tv.units
            v.translation.long_name = new_tv.long_name
        return v

    def execute(self, var, ds, **kwargs):
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
        tv.standard_name = var.standard_name
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

    def execute(self, var, ds, **kwargs):
        """Convert units on the dependent variable and coordinates of var from
        what's specified in the dataset attributes to what's given in the
        VarlistEntry *var*. Units attributes are updated on the
        :class:`~src.core.TranslatedVarlistEntry`.
        """
        tv = var.translation  # abbreviate
        # convert dependent variable
        # Note: may need to define src_unit = ds[tv.name].units or similar
        ds = units.convert_dataarray(
            ds, tv.name, src_unit=None, dest_unit=var.units.units, log=var.log
        )
        tv.units = var.units

        # convert coordinate dimensions and bounds
        for c in tv.dim_axes.values():
            if c.axis == 'T':
                continue  # TODO: separate function to handle calendar conversion
            dest_c = var.axes[c.axis]
            src_units = None
            for v in ds.variables:
                if hasattr(ds[v], 'standard_name'):
                    if ds[v].standard_name == dest_c.standard_name:
                        src_units = ds[v].units
            ds = units.convert_dataarray(
                ds, c.standard_name, src_unit=src_units, dest_unit=dest_c.units, log=var.log
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
                c.value = None
                if len(ds[c.name]) > 1:
                    for v in ds[c.name].values:
                        if int(v) / dest_c.value == 100:  # v = dest_c in Pa
                            c.value = dest_c.value
                        elif int(v) == dest_c.value:
                            c.value = v
                else:
                    c.value = ds[c.name].item()
                c.units = dest_c.units

        var.log.info("Converted units on %s.", var.full_name)
        return ds


class RenameVariablesFunction(PreprocessorFunctionBase):
    """Renames dependent variables and coordinates to what's expected by the POD.
    """

    def execute(self, var, ds, **kwargs):
        """Change the names of the DataArrays with Dataset *ds* to the names
        specified by the :class:`~src.varlist_util.VarlistEntry` *var*. Names of
        the dependent variable and all dimension coordinates and scalar
        coordinates (vertical levels) are changed in-place.
        """
        tv = var.translation  # abbreviate
        rename_d = dict()
        # rename var
        # if tv.name != var.name:
        #    var.log.debug("Rename '%s' variable in %s to '%s'.",
        #                  tv.name, var.full_name, var.name,
        #                  tags=util.ObjectLogTag.NC_HISTORY
        #                  )
        #    rename_d[tv.name] = var.name
        #    tv.name = var.name

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

        # check to see if coord has already been translated
        translated = []
        for dname, tname in rename_d.items():
            # will raise an exception if translated coord exists
            try:
                if ds[tname] is not None:
                    translated.append(dname)
            except:
                pass
        [rename_d.pop(t) for t in translated]

        return ds.rename(rename_d)


class AssociatedVariablesFunction(PreprocessorFunctionBase):
    """Preprocessor class to copy associated variables to wkdir"""

    def execute(self, var, ds, **kwargs):
        casename = ""
        pod_wkdir = ""
        query_associated_files = False
        for k, v in kwargs.items():
            if 'work_dir' in k:
                pod_wkdir = v
            elif 'case_name' in k:
                casename = v
            elif 'query_associated_files' in k:
                query_associated_files = v

        if not query_associated_files or not var.associated_files:
            return ds

        try:

            # iterate over active associated files and get current local paths
            associated_files = list(
                var.iter_associated_files_keys(status=util.ObjectStatus.ACTIVE)
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
            pass

        return ds


class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a requested pressure level from a Dataset containing a 3D variable.

    . note::

       Unit conversion on the vertical coordinate is implemented, but
       parametric vertical coordinates and coordinate interpolation are not.
       If a pressure level is requested that isn't present in the data,
       :meth:`process` raises a KeyError.
    """

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """ Create an 4-D alternate for a scalar variable.
        If given a :class:`~src.varlist_util.VarlistEntry` *v* has a
        ``scalar_coordinate`` for the Z axis (i.e., is requesting data on a
        pressure level), return a copy of *v* with that ``scalar_coordinate``
        removed (i.e., requesting a full 4D variable) to be used as an alternate
        variable for *v*.

        """
        data_convention = 'CMIP'
        for key, val in kwargs.items():
            if 'convention' in key:
                data_convention = val

        if not v.translation:
            # hit this if VE not defined for this model naming convention;
            # do nothing for this v and return for next pp function edit_request
            return v
        elif v.translation.get_scalar('Z') is None:
            # hit this if VE didn't request Z level extraction; do nothing
            return v

        tv = v.translation
        if len(tv.scalar_coords) == 0:
            raise AssertionError  # should never get here assuming that all translated vars at least
            # have a time dimension
        elif len(tv.scalar_coords) > 1:
            _log.debug(f'scalar_coords attribute for {v.name} has more than one entry; using first entry in list')
        # wraps method in data_model; makes a modified copy of translated var
        # restore name to that of 4D data (eg. 'u500' -> 'ua')

        new_tv_name = ""
        if v.use_exact_name:
            new_tv_name = v.name
        else:
            new_tv_dict = translation.VariableTranslator().from_CF_name(
                data_convention, v.standard_name, v.realm, v.modifier
            )
            # CMIP CV will return multiple values for same standard name (e.g., ua250, ua10, ua)
            # so choose the 4-D value (assumes that 4-D vars from same realm do not share the same standard name)
            for var_dict in new_tv_dict.values():
                if var_dict['ndim'] == 4:
                    new_tv_name = var_dict['name']
        new_tv = tv.remove_scalar(
            'Z',
            name=new_tv_name,
            long_name=""
        )

        # add original 4D var defined in new_tv as an alternate TranslatedVarlistEntry
        # to query if no entries on specified levels are found in the data catalog

        v.alternates.append(new_tv)

        return v

    def execute(self, var, ds, **kwargs):
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
    <https://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#attribute-appendix>`__
    on the ``scale_factor`` and ``add_offset`` attributes.

    . note::

       By default, this function is not applied. It's only provided to implement
       workarounds for running the package on data with metadata (i.e., units)
       that are known to be incorrect.
    """

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """Edit the *pod*'s :class:`~src.varlist_util.VarlistEntry.Varlist` prior to data query.
        If given a :class:`~src.varlist_util.VarlistEntry` *v* has a
        ``scalar_coordinate`` for the Z axis (i.e., is requesting data on a
        pressure level), return a copy of *v* with that ``scalar_coordinate``
        removed (i.e., requesting a full 3D variable) to be used as an alternate
        variable for *v*.

        The signature of this method is altered by the :func:`multirun_edit_request_wrapper`
        decorator.
        """
        for key, val in kwargs.items():
            if 'convention' in key:
                data_convention = val
            else:
                data_convention = None
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
            new_tv_name = translation.VariableTranslator().from_CF_name(
                data_convention, v.standard_name, v.realm, new_ax_set
            )
        new_tv = tv.remove_scalar(
            tv.scalar_coords[0].axis,
            name=new_tv_name
        )
        new_v = copy_as_alternate(v)
        new_v.translation = new_tv
        return new_v

    def execute(self, var, ds, **kwargs):
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


class UserDefinedPreprocessorFunction(PreprocessorFunctionBase):
    """Class to hold user-defined preprocessor functions"""
    user_defined_script: str

    def __init__(self, pp_script: str):
        """Called during Preprocessor's init."""
        self.user_defined_script = pp_script

    def edit_request(self, v, **kwargs):
        """Dummy implementation of edit_request to meet abstract base class requirements
        """
        return v

    def execute(self, var, ds, **kwargs):
        pass


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
    WORK_DIR: dict
    """List of PreprocessorFunctions to be executed on a per-file basis as the
        multi-file Dataset is being loaded, rather than afterwards as part of the
        :meth:`process`. Note that such functions will not be able to rely on the
        metadata cleaning done by xr_parser.
    """
    file_preproc_functions = util.abstract_attribute()
    output_to_ncl: bool = False
    nc_format: str
    user_pp_scripts: list

    def __init__(self,
                 model_paths: util.ModelDataPathManager,
                 config: util.NameSpace):
        self.WORK_DIR = model_paths.MODEL_WORK_DIR
        # initialize PreprocessorFunctionBase objects
        self.file_preproc_functions = []
        # initialize xarray parser
        self.parser = self._XarrayParserClass(config)
        if config.large_file:
            self.nc_format = "NETCDF4_CLASSIC"
        else:
            self.nc_format = "NETCDF4"

    @property
    def _functions(self):
        """Determine which PreprocessorFunctions are applicable to the current
        package run, defaulting to all of them.

        Returns:
            tuple of classes (inheriting from :class:`PreprocessorFunctionBase`)
            listing the preprocessing functions to be called, in order.
        """
        # normal operation: run all functions
        return [
            AssociatedVariablesFunction, PercentConversionFunction,
            PrecipRateToFluxFunction, ConvertUnitsFunction,
            ExtractLevelFunction, RenameVariablesFunction
        ]

    def cast_to_cftime(self, dt: datetime.datetime, calendar):
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

    def check_time_bounds(self, ds: xr.Dataset,
                          var: translation.TranslatedVarlistEntry,
                          freq: str):
        """Parse quantities related to the calendar for time-dependent data and
        truncate the date range of model dataset *ds*.

        In particular, the *var*\'s ``date_range`` attribute was set from the
        user's input before we knew the calendar being used by the model. The
        workaround here to cast those values into `cftime.datetime
        <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        objects so that they can be compared with the model data's time axis.
        """

        dt_range = var.T.range
        ds_decode = xr.decode_cf(ds, use_cftime=True)
        t_coord = ds_decode[var.T.name]
        # time coordinate will be a list if variable has
        # multiple coordinates/coordinate attributes
        if hasattr(t_coord, 'calendar'):
            cal = t_coord.calendar
        elif 'calendar' in t_coord.encoding:
            cal = t_coord.encoding['calendar']
        else:
            raise ValueError(f'calendar attribute not found for catalog time coord')
        t_start = t_coord.values[0]
        t_end = t_coord.values[-1]
        # lower/upper are earliest/latest datetimes consistent with the date we
        # were given, up to the precision that was specified (eg lower for "2000"
        # would be Jan 1, 2000, and upper would be Dec 31).

        # match date range hours to dataset hours if necessary
        # to accommodate timeslice data and other datasets that
        # do not begin at hour zero
        if dt_range.start.lower.hour != t_start.hour:
            var.log.info("Variable %s data starts at hour %s", var.full_name, t_start.hour)
            dt_start_lower_new = datetime.datetime(t_start.year,
                                                   t_start.month,
                                                   t_start.day,
                                                   t_start.hour,
                                                   t_start.minute,
                                                   t_start.second)
            dt_start_lower = self.cast_to_cftime(dt_start_lower_new, cal)
        else:
            dt_start_lower = self.cast_to_cftime(dt_range.start.lower, cal)
        if dt_range.end.lower.hour != t_end.hour:
            var.log.info("Variable %s data ends at hour %s", var.full_name, t_end.hour)
            dt_end_lower_new = datetime.datetime(t_end.year,
                                                 t_end.month,
                                                 t_end.day,
                                                 t_end.hour,
                                                 t_end.minute,
                                                 t_end.second)
            dt_end_lower = self.cast_to_cftime(dt_end_lower_new, cal)
        else:
            dt_end_lower = self.cast_to_cftime(dt_range.end.lower, cal)

        # only check that up to monthly precision for monthly or longer data
        if freq in ['mon', 'year']:
            if t_start.year > dt_start_lower.year or \
                    t_start.year == dt_start_lower.year and t_start.month > dt_start_lower.month:
                err_str = (f"Error: dataset start ({t_start}) is after "
                           f"requested date range start ({dt_start_lower}).")
                var.log.error(err_str)
                raise IndexError(err_str)
            if t_end.year < dt_end_lower.year or \
                    t_end.year == dt_end_lower.year and t_end.month < dt_end_lower.month:
                err_str = (f"Error: dataset end ({t_end}) is before "
                           f"requested date range end ({dt_end_lower}).")
                var.log.error(err_str)
                raise IndexError(err_str)
        else:
            if t_start > dt_start_lower:
                err_str = (f"Error: dataset start ({t_start}) is after "
                           f"requested date range start ({dt_start_lower}).")
                var.log.error(err_str)
                raise IndexError(err_str)
            if t_end < dt_end_lower:
                err_str = (f"Error: dataset end ({t_end}) is before "
                           f"requested date range end ({dt_end_lower}).")
                var.log.error(err_str)
                raise IndexError(err_str)

    def normalize_group_time_vals(self, time_vals: np.ndarray) -> np.ndarray:
        """Apply logic to format time_vals lists found in
        check_group_daterange and convert them into str type.
        This function also handles missing leading zeros
        """
        poss_digits = list(range(4, 15, 2))
        for i in range(len(time_vals)):
            if isinstance(time_vals[i], str):
                time_vals[i] = time_vals[i].replace(' ', '').replace('-', '').replace(':', '')
                while len(time_vals[i]) not in poss_digits:
                    time_vals[i] = '0' + time_vals[i]
        return time_vals

    def drop_attributes(self, xr_ds: xr.Dataset) -> xr.Dataset:
        """ Drop attributes that cause conflicts with xarray dataset merge"""
        drop_atts = ['average_T2',
                     'average_DT',
                     'average_T1',
                     'height',
                     'date'
                     ]
        # TODO: find a suitable answer to conflicts in xarray merging (i.e. nctoolkit)
        for att in drop_atts:
            if xr_ds.get(att, None) is not None:
                # save attribute to restore to xarray written to pp file after xr_parser checks
                self.parser.vars_backup[att] = xr_ds[att].copy()
                xr_ds = xr_ds.drop_vars(att)
                for coord in xr_ds.coords:
                    if 'bounds' in xr_ds[coord].attrs:
                        if xr_ds[coord].attrs['bounds'] == att:
                            self.parser.attrs_backup[coord] = xr_ds[coord].attrs.copy()
                            del xr_ds[coord].attrs['bounds']

        return xr_ds


    def check_multichunk(self, group_df: pd.DataFrame, case_dr, log) -> pd.DataFrame:
        """Sort the files found by date, grabs the files whose 'chunk_freq' is the
        largest number where endyr-startyr modulo 'chunk_freq' is zero and throws out
        the rest.

        Args:
            group_df (Pandas Dataframe):
            case_dr: requested daterange of POD
            log: log file
        """
        chunks = group_df['chunk_freq'].unique()
        if len(chunks) > 1:
            for i, c in enumerate(chunks):
                chunks[i] = int(c.replace('yr', ''))
            chunks = -np.sort(-chunks)
            case_dt = int(str(case_dr.end)[:4]) - int(str(case_dr.start)[:4]) + 1
            for c in chunks:
                if case_dt % c == 0:
                    grabbed_chunk = str(c) + 'yr'
                    log.warning("Multiple values for 'chunk_freq' found in dataset "
                                "only grabbing data with 'chunk_freq': %s", grabbed_chunk)
                    break
            group_df = group_df[group_df['chunk_freq'] == grabbed_chunk]
        return pd.DataFrame.from_dict(group_df).reset_index()

    def crop_date_range(self, case_date_range: util.DateRange, xr_ds, time_coord) -> xr.Dataset:
        xr_ds = self.drop_attributes(xr_ds)
        xr_ds = xr.decode_cf(xr_ds,
                             decode_coords=True,  # parse coords attr
                             decode_times=True,
                             use_cftime=True  # use cftime instead of np.datetime6
                             )
        cal = 'noleap'
        if 'calendar' in xr_ds[time_coord.name].attrs:
            cal = xr_ds[time_coord.name].attrs['calendar']
        elif 'calendar' in xr_ds[time_coord.name].encoding:
            cal = xr_ds[time_coord.name].encoding['calendar']

        ds_date_time = xr_ds[time_coord.name].values
        ds_start_time = ds_date_time[0]
        ds_end_time = ds_date_time[-1]
        # force hours in dataset to match date range if frequency is daily, monthly, annual
        if ds_start_time.hour != case_date_range.start_datetime.hour and case_date_range.precision < 4:
            dt_start_new = datetime.datetime(ds_start_time.year,
                                             ds_start_time.month,
                                             ds_start_time.day,
                                             ds_start_time.hour,
                                             ds_start_time.minute,
                                             ds_start_time.second)
            ds_start = self.cast_to_cftime(dt_start_new, cal)
        else:
            ds_start = self.cast_to_cftime(ds_start_time, cal)
        if ds_end_time.hour != case_date_range.end_datetime.hour and case_date_range.precision < 4:
            dt_end_new = datetime.datetime(ds_end_time.year,
                                           ds_end_time.month,
                                           ds_end_time.day,
                                           ds_end_time.hour,
                                           ds_end_time.minute,
                                           ds_end_time.second)
            ds_end = self.cast_to_cftime(dt_end_new, cal)
        else:
            ds_end = self.cast_to_cftime(ds_end_time, cal)
        date_range_cf_start = self.cast_to_cftime(case_date_range.start.lower, cal)
        date_range_cf_end = self.cast_to_cftime(case_date_range.end.lower, cal)

        # dataset has no overlap with the user-specified date range
        if ds_start < date_range_cf_start and ds_end < date_range_cf_start or \
                ds_end > date_range_cf_end and ds_start > date_range_cf_end:
            new_xr_ds = None
        # dataset falls entirely within user-specified date range
        elif ds_start >= date_range_cf_start and ds_end <= date_range_cf_end:
            new_xr_ds = xr_ds.sel({time_coord.name: slice(ds_start, ds_end)})
        # dataset overlaps user-specified date range start (corrected)
        elif ds_start <= date_range_cf_start <= ds_end <= date_range_cf_end:
            new_xr_ds = xr_ds.sel({time_coord.name: slice(date_range_cf_start, ds_end)})
        # dataset overlaps user-specified date range start (orig)
        elif date_range_cf_start < ds_start and \
                date_range_cf_start <= ds_end <= date_range_cf_end:
            new_xr_ds = xr_ds.sel({time_coord.name: slice(date_range_cf_start, ds_end)})
        # dataset overlaps user-specified date range end
        elif date_range_cf_start < ds_start <= date_range_cf_end <= ds_end:
            new_xr_ds = xr_ds.sel({time_coord.name: slice(ds_start, date_range_cf_end)})
        # dataset contains all of requested date range
        elif date_range_cf_start >= ds_start and date_range_cf_end <= ds_end:
            new_xr_ds = xr_ds.sel({time_coord.name: slice(date_range_cf_start, date_range_cf_end)})
        else:
            print(f'ERROR: new_xr_ds is unset because of incompatibility of time:')
            print(f'       Dataset   start: {ds_start=}')
            print(f'       Dataset   end  : {ds_end=}')
            print(f'       Requested start: {date_range_cf_start=}')
            print(f'       Requested end  : {date_range_cf_end=}')

        return new_xr_ds

    def check_group_daterange(self, df: pd.DataFrame, date_range: util.DateRange,
                              log=_log) -> pd.DataFrame:
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.

        Args:
            df (Pandas Dataframe):
            date_range: requested daterange of POD
            log: log file
        """
        date_col = "date_range"
        if hasattr(df, 'time_range'):
            start_times = []
            end_times = []
            for tr in df['time_range'].values:
                tr = tr.replace(' ', '').replace('-', '').replace(':', '')
                start_times.append(tr[0:len(tr) // 2])
                end_times.append(tr[len(tr) // 2:])
            df['start_time'] = pd.Series(start_times)
            df['end_time'] = pd.Series(end_times)
        else:
            raise AttributeError('Data catalog is missing the attribute `time_range`;'
                                 ' this is a required entry.')
        try:
            start_time_vals = self.normalize_group_time_vals(df['start_time'].values.astype(str))
            end_time_vals = self.normalize_group_time_vals(df['end_time'].values.astype(str))
            if not isinstance(start_time_vals[0], datetime.date):
                date_format = dl.date_fmt(start_time_vals[0])
                # convert start_times to date_format for all files in query
                df['start_time'] = start_time_vals
                df['start_time'] = df['start_time'].apply(lambda x:
                                                          datetime.datetime.strptime(x, date_format))
                # convert end_times to date_format for all files in query
                df['end_time'] = end_time_vals
                df['end_time'] = df['end_time'].apply(lambda x:
                                                      datetime.datetime.strptime(x, date_format))
            # method throws ValueError if ranges aren't contiguous
            dates_df = df.loc[:, ['start_time', 'end_time']]
            date_range_vals = []
            for idx, x in enumerate(df.values):
                st = dates_df.at[idx, 'start_time']
                en = dates_df.at[idx, 'end_time']
                date_range_vals.append(util.DateRange(st, en))
            group_df = df.assign(date_range=date_range_vals)
            sorted_df = group_df.sort_values(by=date_col)

            files_date_range = util.DateRange.from_contiguous_span(
                *(sorted_df[date_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            # assert files_date_range.contains(self.attrs.date_range)
            # throw out df entries not in date_range
            return_df = []
            for i in sorted_df.index:
                cat_row = sorted_df.iloc[i]
                if pd.isnull(cat_row['start_time']):
                    continue
                else:
                    ds_st = cat_row['start_time']
                    ds_et = cat_row['end_time']
                # date range includes entire or part of dataset
                if ds_st >= date_range.start.lower and ds_et < date_range.end.upper or \
                        ds_st < date_range.end.lower and ds_et >= date_range.start.lower or \
                        ds_st <= date_range.end.lower < ds_et:
                    return_df.append(cat_row)

            return pd.DataFrame.from_dict(return_df)
        except ValueError:
            log.error("Non-contiguous or malformed date range in files:", group_df["path"].values)
        except AssertionError:
            log.debug(("Eliminating expt_key since date range of files (%s) doesn't "
                       "span query range (%s)."), files_date_range, self.attrs.date_range)
        except Exception as exc:
            log.warning(f"Caught exception {repr(exc)}")
        # hit an exception; return empty DataFrame to signify failure
        return pd.DataFrame(columns=group_df.columns)

    def normalize_time_units(self, subset_dict: dict, time_coord, log=_log) -> dict:
        """
        Some datasets will have the time units that are different in each individual file.
        This function updates each time unit to rely on the earliest year grabbed in the
        query stage.

        This function assumes the time coord units attr will be of the form "{unit} since ????".
        """

        time_units = np.sort([subset_dict[f].time.units for f in list(subset_dict)])
        tn = time_coord.name  # abbreviate

        # assumes each dataset has the same calendar
        cal = 'noleap'
        if 'calendar' in subset_dict[list(subset_dict)[0]][tn].attrs:
            cal = subset_dict[list(subset_dict)[0]][tn].attrs['calendar']
        elif 'calendar' in subset_dict[list(subset_dict)[0]][tn].encoding:
            cal = subset_dict[list(subset_dict)[0]][tn].encoding['calendar']

        if len(set(time_units)) > 1:  # check if each dataset has the different time coord units
            # check if time coord units are in the form "{unit} since {date}"
            # they can be different units as this function converts to the earliest case
            if all(["since" in u for u in time_units]):
                start_unit = time_units[0].split(" ")[0]
                start_str = " ".join(time_units[0].split(" ")[2:])
                start_cft = dl.str_to_cftime(
                    start_str.replace(" ", "").replace(":", "").replace("-", ""),
                    calendar=cal
                )
                new_unit_str = f"{start_unit} since {start_str}"

                # dictionary of how many seconds are in each time unit
                seconds_in = {
                    "seconds": 1.0,
                    "minutes": 60.0,
                    "hours": 3600.0,
                    "days": 86400.0,
                    "weeks": 604800.0,  # these are rarer and vague cases (they could be problematic)
                    "months": 2628000.0,  # seconds in common year (365 days) / 12
                    "years": 31536000.0  # common year (365 days)
                }

                for f in list(subset_dict):
                    current_unit = subset_dict[f][time_coord.name].units.split(" ")[0].lower()
                    current_str = " ".join(subset_dict[f][tn].units.split(" ")[2:])
                    current_cft = dl.str_to_cftime(
                        current_str.replace(" ", "").replace(":", "").replace("-", ""),
                        calendar=cal
                    )

                    # TODO: add logic to add year values for different calendars

                    if current_cft > start_cft:
                        # get difference between current files unit reference point and earliest found
                        diff = ((current_cft - start_cft).total_seconds()) / seconds_in[start_unit]

                        subset_dict[f].coords['time'] = subset_dict[f][tn].assign_attrs(
                            units=new_unit_str
                        )

                        # convert current unit if it is not the same as the earliest reference
                        if current_unit != start_unit:
                            factor = seconds_in[current_unit] / seconds_in[start_unit]
                        else:
                            factor = 1.0

                        # change the values in the dataset
                        for i, v in enumerate(subset_dict[f][tn].values):
                            subset_dict[f].coords[tn].values[i] = factor * v + diff
            else:
                raise AttributeError("Different units were found for time coord in each file. "
                                     "We were unable to normalize due to the units not being in '{unit} since ' format")

        return subset_dict

    def query_catalog(self,
                      case_dict: dict,
                      data_catalog: str,
                      *args) -> dict:
        """Apply the format conversion implemented in this PreprocessorFunction
        to the input dataset *dataset*, according to the request made in *var*.

        Args:
            case_dict: dictionary of case names
            data_catalog: path to data catalog header file

        Returns:
            Dictionary of xarray datasets with catalog information for each case
        """

        try_new_query = False
        # open the csv file using information provided by the catalog definition file
        cat = intake.open_esm_datastore(data_catalog)
        # create filter lists for POD variables
        cat_dict = {}
        # Instantiate dataframe to hold catalog subset information
        cols = list(cat.df.columns.values)
        if 'date_range' not in [c.lower() for c in cols]:
            cols.append('date_range')

        for case_name, case_d in case_dict.items():
            # path_regex = re.compile(r'(?i)(?<!\\S){}(?!\\S+)'.format(case_name))
            path_regex = [re.compile(r'({})'.format(case_name))]

            for var in case_d.varlist.iter_vars():
                if not var.is_static:
                    date_range = var.T.range

                # define initial query dictionary with variable settings requirements that do not change if
                # the variable is translated
                case_d.set_query(var, path_regex)

                # change realm key name if necessary
                if cat.df.get('modeling_realm', None) is not None:
                    case_d.query['modeling_realm'] = case_d.query.pop('realm')

                # search catalog for convention specific query object
                var.log.info("Querying %s for variable %s for case %s.",
                             data_catalog,
                             var.name,
                             case_name)
                cat_subset = cat.search(**case_d.query)
                if cat_subset.df.empty:
                    # check whether there is an alternate variable to substitute
                    if any(var.alternates):
                        try_new_query = True
                        for a in var.alternates:
                            if hasattr(a, 'translation'):
                                if a.translation is not None:
                                    case_d.query.update({'variable_id': a.translation.name})
                                    case_d.query.update({'standard_name': a.translation.standard_name})
                            else:
                                case_d.query.update({'variable_id': a.name})
                                case_d.query.update({'standard_name': a.standard_name})
                            if any(var.translation.scalar_coords):
                                found_z_entry = False
                                # check for vertical coordinate to determine if level extraction is needed
                                for c in a.scalar_coords:
                                    if c.axis == 'Z':
                                        var.translation.requires_level_extraction = True
                                        found_z_entry = True
                                        break
                                    else:
                                        continue
                                if found_z_entry:
                                    break
                    if try_new_query:
                        # search catalog for convention specific query object
                        cat_subset = cat.search(**case_d.query)
                        if cat_subset.df.empty:
                            raise util.DataRequestError(
                                f"No assets matching query requirements found for {var.translation.name} for"
                                f" case {case_name} in {data_catalog}. The input catalog may missing entries for the"
                                f"following required fields: standard_name, variable_id, units, realm."
                                f"Check that the target file paths contain the case_name(s) defined in the runtime"
                                f"configuration file.")
                    else:
                        raise util.DataRequestError(
                            f"Unable to find match or alternate for {var.translation.name}"
                            f" for case {case_name} in {data_catalog}")

                # if multiple entries exist, refine with variable_id
                # this will solve issues where standard_id is not enough to uniquely ID a variable
                # e.g. for catalogs with variables defined at individual levels
                if len(cat_subset.df.variable_id) > 1:
                    var.log.info(f"Query for case {case_name} variable {var.name} in {data_catalog} returned multiple"
                                 f"entries. Refining query using variable_id")
                    if var.translation is not None:
                        case_d.query.update({'variable_id': var.translation.name})
                    else:
                        case_d.query.update({'variable_id': var.name})
                    cat_subset = cat.search(**case_d.query)
                    if len(cat_subset.df.variable_id) > 1:
                        raise util.DataRequestError(
                            f"Unable to find unique entry for {case_d.query['variable_id']}"
                            f" for case {case_name} in {data_catalog}")
                    case_d.query.pop('variable_id', None)
                # Get files in specified date range
                # https://intake-esm.readthedocs.io/en/stable/how-to/modify-catalog.html
                if not var.is_static:
                    if "chunk_freq" in cat_subset.df:
                        cat_subset.esmcat._df = self.check_multichunk(cat_subset.df, date_range, var.log)
                    cat_subset.esmcat._df = self.check_group_daterange(cat_subset.df, date_range, var.log)
                if cat_subset.df.empty:
                    raise util.DataRequestError(
                        f"check_group_daterange returned empty data frame for {var.name}"
                        f" case {case_name} in {data_catalog}, indicating issues with data continuity")
                var.log.info(f"Converting {var.name} catalog subset to dataset dictionary")
                # convert subset catalog to an xarray dataset dict
                # and concatenate the result with the final dict
                cat_subset_dict = cat_subset.to_dataset_dict(
                    progressbar=False,
                    xarray_open_kwargs=self.open_dataset_kwargs,
                    aggregate=False
                )
                # NOTE: The time_range of each file in cat_subset_df must be in a specific
                # order in order for xr.concat() to work correctly. In the current implementation,
                # we sort by the first value of the time coordinate of each file.
                # This assumes the unit of said coordinate is homogeneous for each file, which could
                # easily be problematic in the future.
                # tl;dr hic sunt dracones
                var_xr = []
                if not var.is_static:
                    cat_subset_dict = self.normalize_time_units(cat_subset_dict, var.T)
                    time_sort_dict = {f: cat_subset_dict[f].time.values[0]
                                      for f in list(cat_subset_dict)}
                    time_sort_dict = dict(sorted(time_sort_dict.items(), key=lambda item: item[1]))

                    for k in list(time_sort_dict):
                        cat_subset_dict[k] = self.crop_date_range(date_range,
                                                                  cat_subset_dict[k],
                                                                  var.T)
                        if cat_subset_dict[k] is None:
                            continue
                        else:
                            if not var_xr:
                                var_xr = cat_subset_dict[k]
                            else:
                                var_xr = xr.concat([var_xr, cat_subset_dict[k]], var.T.name)
                else:
                    # get xarray dataset for static variable
                    cat_index = [k for k in cat_subset_dict.keys()][0]
                    if not var_xr:
                        var_xr = cat_subset_dict[cat_index]
                    else:
                        if var.Y is not None:
                            var_xr = xr.concat([var_xr, cat_subset_dict[cat_index]], var.Y.name)
                        elif var.X is not None:
                            var_xr = xr.concat([var_xr, cat_subset_dict[cat_index]], var.X.name)
                        else:
                            var_xr = xr.concat([var_xr, cat_subset_dict.values[cat_index]], var.N.name)
                var_xr = self.drop_attributes(var_xr)
                # add standard_name to the variable xarray dataset if it is not defined
                for vname in var_xr.variables:
                    if (not isinstance(var_xr.variables[vname], xr.IndexVariable)
                            and var_xr[vname].attrs.get('standard_name', None) is None):
                        case_query_standard_name = case_d.query.get('standard_name')
                        if isinstance(case_query_standard_name, list):
                            new_standard_name = \
                            [name for name in case_query_standard_name if name == var.translation.standard_name][0]
                        else:
                            new_standard_name = case_query_standard_name
                        var_xr[vname].attrs['standard_name'] = new_standard_name
                        var_xr[vname].attrs['name'] = vname

                var.log.info(f'Merging {var.name}')
                if case_name not in cat_dict:
                    cat_dict[case_name] = var_xr
                else:
                    cat_dict[case_name] = xr.merge([cat_dict[case_name], var_xr], compat='no_conflicts')
                # check that the trimmed variable data in the merged dataset matches the desired date range
                if not var.is_static:
                    try:
                        var.log.info(f'Calling check_time_bounds for {var.name}')
                        self.check_time_bounds(cat_dict[case_name], var.translation, var.T.frequency)
                    except LookupError:
                        var.log.error(f'Time bounds in trimmed dataset for {var.name} in case {case_name} do not match'
                                      f'requested date_range.')
                        raise SystemExit("Terminating program")
        return cat_dict

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """Top-level method to edit *pod*\'s data request, based on the child
        class's functionality. Calls the :meth:`~PreprocessorFunctionBase.edit_request`
        method on all included PreprocessorFunctions.
        """

        for func in self.file_preproc_functions:
            v = func.edit_request(func, v, **kwargs)

    def execute_pp_functions(self, v: varlist_util.VarlistEntry,
                             xarray_ds: xr.Dataset,
                             **kwargs):
        """Method to launch pp routines on xarray datasets associated with required variables"""
        for func in self.file_preproc_functions:
            xarray_ds = func.execute(func, v, xarray_ds, **kwargs)
            # append custom preprocessing scripts

            if hasattr(self, 'user_pp_scripts'):
                if self.user_pp_scripts and len(self.user_pp_scripts) > 0:
                    for s in self.user_pp_scripts:
                        script_name, script_ext = os.path.splitext(s)
                        full_module_name = "user_scripts." + script_name
                        user_module = importlib.import_module(full_module_name, package=None)
                        # Call function with the arguments
                        # user_scripts.example_pp_script.main(xarray_ds, v)
                        xarray_ds = user_module.main(xarray_ds, v.name)

        return xarray_ds

    def setup(self, pod):
        """Method to do additional configuration immediately before :meth:`process`
        is called on each variable for *pod*. Implements metadata cleaning via
        the :doc:`src.xr_parser` (class specified in the ``_XarrayParserClass``
        attribute, default :class:`~src.xr_parser.DefaultDatasetParser`).
        """
        self.parser.setup(pod)

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
            "use_cftime": False,
            "chunks": "auto"

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

    def rename_dataset_keys(self, ds: dict, case_list: dict) -> collections.OrderedDict:
        """Rename dataset keys output by ESM intake catalog query to case names`"""

        def rename_key(old_dict: dict, new_dict: collections.OrderedDict, old_key, new_key):
            """Credit:  https://stackoverflow.com/questions/16475384/rename-a-dictionary-key"""
            new_dict[new_key] = old_dict[old_key]

        new_dict = collections.OrderedDict()
        case_names = [c for c in case_list.keys()]
        for old_key, case_d in ds.items():
            (path, filename) = os.path.split(case_d.attrs['intake_esm_attrs:path'])
            rename_key(ds, new_dict, old_key, [c for c in case_names if c in filename][0])
        return new_dict

    def rename_dataset_vars(self, ds: dict, case_list: dict) -> collections.OrderedDict:
        """Rename variables in dataset to conform with variable names requested by the POD"""
        case_names = [c for c in case_list.keys()]
        for c in case_names:
            name_dict = {}
            for var in case_list[c].varlist.iter_vars():
                name_dict[var.translation.name] = var.name
            ds[c] = ds[c].rename_vars(name_dict=name_dict)
        return ds

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
        for key, val in attrs.items():
            if val == xr_parser.ATTR_NOT_FOUND:
                var.log.debug("Caught unset attribute '%s' of '%s'.", key, name)
                attrs_to_delete.add(key)
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

    def clean_output_attrs(self,
                           var: varlist_util.VarlistEntry,
                           ds: xr.Dataset):
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

    def write_dataset(self, var: varlist_util.VarlistEntry, ds: xr.Dataset):
        """Writes processed Dataset *ds* to location specified by the
        ``dest_path`` attribute of *var*, using xarray `to_netcdf()
        <https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__.
        May be overwritten by child classes.
        """
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        var_ds = ds[var.translation.name].to_dataset()
        var_ds = var_ds.rename_vars(name_dict={var.translation.name: var.name})
        if var.is_static:
            unlimited_dims = []
        else:
            unlimited_dims = [var.T.name]
        # append other grid types here as needed
        irregular_grids = {'tripolar'}
        if ds.attrs.get('grid', None) is not None:
            # search for irregular grid types
            for g in irregular_grids:
                grid_search = re.compile(g, re.IGNORECASE)
                grid_regex_result = grid_search.search(ds.attrs.get('grid'))
                if grid_regex_result is not None:
                    # add variables not included in xarray dataset if dims correspond to vertices and bounds
                    append_vars =\
                        (list(set([v for v in ds.variables
                                   if 'vertices' in ds[v].dims
                                   or 'bnds' in ds[v].dims]).difference([v for v in var_ds.variables])))
                    for v in append_vars:
                        v_dataset = ds[v].to_dataset()
                        var_ds = xr.merge([var_ds, v_dataset])


        # The following block is retained for time comparison with dask delayed write procedure
        # var_ds.to_netcdf(
        #    path=var.dest_path,
        #    mode='w',
        #    **self.save_dataset_kwargs,
        #    unlimited_dims=unlimited_dims
        # )
        # ds.close()

        # Uncomment the timing lines and log calls if desired
        # start_time = time.monotonic()
        var.log.info("Writing '%s'.", var.dest_path, tags=util.ObjectLogTag.OUT_FILE)
        delayed_write = var_ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs,
            unlimited_dims=unlimited_dims,
            compute=False
        )
        delayed_write.compute()
        delayed_write.close()
        # end_time = time.monotonic()
        # var.log.info(f'Time to write file {var.dest_path}: {str(datetime.timedelta(seconds=end_time - start_time))}')
        # dt = datetime.timedelta(seconds=end_time - start_time)
        # write_times.append(dt.total_seconds())
        # var.log.info(f'Total write time: {str(sum(write_times))} s')

    def write_ds(self, case_list: dict,
                 catalog_subset: collections.OrderedDict,
                 pod_reqs: dict):
        """Top-level method to write out processed dataset *ds*; spun out so
        that child classes can modify it. Calls the :meth:`write_dataset` method
        implemented by the child class.
        """
        for k, v in pod_reqs.items():
            if 'ncl' in v:
                self.output_to_ncl = True
        for case_name, ds in catalog_subset.items():
            for var in case_list[case_name].varlist.iter_vars():
                # var.log.info("Writing %d mb to %s", ds[var.name].variable.nbytes / (1024 * 1024), var.dest_path)
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


            # del ds  # shouldn't be necessary

    def parse_ds(self,
                 var: varlist_util.VarlistEntry,
                 ds: xr.Dataset) -> xr.Dataset:
        """Top-level method to parse metadata; spun out so that child classes can modify it.
        """
        try:
            ds = self.parser.parse(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, f"parsing dataset metadata", util.DataPreprocessEvent)
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

    def process(self,
                case_list: dict,
                config: util.NameSpace,
                model_work_dir: dict) -> dict:
        """Top-level wrapper method for doing all preprocessing of data files
        associated with each case in the case_list dictionary
        """
        for case_name, case_dict in case_list.items():
            for v in case_dict.varlist.iter_vars():
                self.edit_request(v, to_convention=case_dict.convention)
        # get the initial model data subset from the ESM-intake catalog
        cat_subset = self.query_catalog(case_list, config.DATA_CATALOG)
        for case_name, case_xr_dataset in cat_subset.items():
            for v in case_list[case_name].varlist.iter_vars():
                tv_name = v.translation.name
                # todo: maybe skip this if no standard_name attribute for v in case_xr_dataset
                v.log.info(f'Calling parse_ds for {v.name}')
                var_xr_dataset = self.parse_ds(v, case_xr_dataset)
                varlist_ex = [v_l.translation.name for v_l in case_list[case_name].varlist.iter_vars()
                              if v_l.translation is not None]
                if tv_name in varlist_ex:
                    varlist_ex.remove(tv_name)
                for v_d in var_xr_dataset.variables:
                    if v_d not in varlist_ex:
                        cat_subset[case_name].update({v_d: var_xr_dataset[v_d]})
                v.log.info(f'Calling preprocessing functions for {v.name}')
                pp_func_dataset = self.execute_pp_functions(v,
                                                            cat_subset[case_name],
                                                            work_dir=model_work_dir[case_name],
                                                            case_name=case_name)
                cat_subset[case_name] = pp_func_dataset
        return cat_subset

    def write_pp_catalog(self,
                         cases: dict,
                         input_catalog_ds: xr.Dataset,
                         config: util.PodPathManager,
                         log: logging.log):
        """ Write a new data catalog for the preprocessed data
            to the POD output directory
        """
        cat_file_name = "MDTF_postprocessed_data"
        pp_cat_assets = util.define_pp_catalog_assets(config, cat_file_name)
        file_list = util.get_file_list(config.OUTPUT_DIR)
        # fill in catalog information from pp file name
        # append columns defined in assets
        columns = [att['column_name'] for att in pp_cat_assets['attributes']]
        cat_entries = []
        # each key is a case
        for case_name, case_dict in cases.items():
            ds_match = input_catalog_ds[case_name]
            ds_match.time.values.sort()
            for var in case_dict.varlist.iter_vars():
                var_name = var.translation.name
                ds_var = ds_match.data_vars.get(var_name, None)
                if ds_var is None:
                    log.error(f'No var {var_name}')
                d = dict.fromkeys(columns, "")
                for key, val in ds_match.attrs.items():
                    if 'intake_esm_attrs' in key:
                        for c in columns:
                            if key.split('intake_esm_attrs:')[1] == c:
                                d[c] = val

                d.update({'project_id': var.translation.convention})
                d.update({'path': var.dest_path})
                d.update({'time_range': f'{util.cftime_to_str(ds_match.time.values[0]).replace('-', ':')}-'
                                        f'{util.cftime_to_str(ds_match.time.values[-1]).replace('-', ':')}'})
                d.update({'standard_name': ds_match[var.name].attrs['standard_name']})
                d.update({'variable_id': var_name})
                if 'frequency' in ds_match[var.name].attrs:
                    d.update({'frequency': ds_match[var.name].attrs['frequency']})
                elif not var.is_static:
                    d.update({'frequency': var.T.frequency.unit})
                cat_entries.append(d)
        # create a Pandas dataframe from the catalog entries

        cat_df = pd.DataFrame(cat_entries)
        cat_df.head()
        # validate the catalog
        try:
            log.debug('Validating pp data catalog')
            validated_cat = intake.open_esm_datastore(
                obj=dict(
                    df=cat_df,
                    esmcat=pp_cat_assets
                )
            )
        except Exception as exc:
            log.error(f'Error validating ESM intake catalog for pp data: {exc}')
        try:
            log.debug(f'Writing pp data catalog {cat_file_name} csv and json files to {config.OUTPUT_DIR}')
            validated_cat.serialize(cat_file_name,
                                    directory=config.OUTPUT_DIR,
                                    catalog_type="file")
        except Exception as exc:
            log.error(f'Unable to save esm intake catalog for pp data: {exc}')


class NullPreprocessor(MDTFPreprocessorBase):
    """A class that skips preprocessing and just symlinks files from the input dir to the work dir
    """

    def __init__(self,
                 model_paths: util.ModelDataPathManager,
                 config: util.NameSpace):
        # initialize PreprocessorFunctionBase objects
        super().__init__(model_paths, config)
        self.file_preproc_functions = []

    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs) -> varlist_util.VarlistEntry:
        """Dummy implementation of edit_request to meet abstract base class requirements
        """
        return v

    def process(self, case_list: dict,
                config: util.NameSpace,
                model_work_dir: dict) -> dict:
        """Top-level wrapper method for doing all preprocessing of data files
        associated with each case in the caselist dictionary
        """
        # get the initial model data subset from the ESM-intake catalog
        cat_subset = self.query_catalog(case_list, config.DATA_CATALOG)
        for case_name, case_xr_dataset in cat_subset.items():
            for v in case_list[case_name].varlist.iter_vars():
                # reset the variable dest_paths to point to input catalog paths
                ds = cat_subset[case_name].get(v.name)
                if ds.encoding.get('source', None) is not None:
                    v.dest_path = ds.encoding.get('source')
                for a in v.alternates:
                    if cat_subset[case_name].get(a.name, None) is not None:
                        ds = cat_subset[case_name].get(a.name)
                        a.dest_path = ds.encoding.get('source')

        return cat_subset

    def write_ds(self, case_list: dict,
                 catalog_subset: collections.OrderedDict,
                 pod_reqs: dict):
        """Dummy method that just sets class attribute
        """
        for k, v in pod_reqs.items():
            if 'ncl' in v:
                self.output_to_ncl = True

    def write_pp_catalog(self,
                         cases: dict,
                         input_catalog_ds: xr.Dataset,
                         config: util.PodPathManager,
                         log: logging.log):
        """Dummy method; Same catalog specified at runtime is passed to POD(s)
        """
        log.info(f"Using data catalog specified at runtime")

    def rename_dataset_vars(self, ds: dict, case_list: dict) -> dict:
        """Dummy method for NullPreprocessor """
        return ds


class DaskMultiFilePreprocessor(MDTFPreprocessorBase):
    """A Preprocessor class that uses xarray's dask support to
    preprocess model data provided as one or multiple netcdf files per
    variable, using xarray `open_mfdataset()
    <https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.
    """
    module_root: str = ""
    user_pp_scripts: list

    def __init__(self,
                 model_paths: util.ModelDataPathManager,
                 config: util.NameSpace):
        # initialize PreprocessorFunctionBase objects
        super().__init__(model_paths, config)
        self.file_preproc_functions = [f for f in self._functions]
        if hasattr(config, 'user_pp_scripts'):
            if any([s for s in config.user_pp_scripts]):
                self.add_user_pp_scripts(config)
                self.module_root = os.path.join(config.CODE_ROOT, "user_scripts")
            else:
                self.user_pp_scripts = None

    def add_user_pp_scripts(self, runtime_config: util.NameSpace):
        self.user_pp_scripts = [s for s in runtime_config.user_pp_scripts]
        for s in self.user_pp_scripts:
            try:
                os.path.exists(s)
            except util.MDTFFileExistsError:
                self.log.error(f"User-defined post-processing file {s} not found")


def init_preprocessor(model_paths: util.ModelDataPathManager,
                      config: util.NameSpace,
                      run_pp: bool = True):
    """Initialize the data preprocessor class using runtime configuration specs
    """
    if not run_pp:
        return NullPreprocessor(model_paths, config)
    else:
        return DaskMultiFilePreprocessor(model_paths, config)
