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
import math
import numpy as np
import xarray as xr
import collections
import re

# Import fieldlist_parser from util/utils package
try:
        from src.util import fieldlist_parser
except ImportError:
    try:
         from src.utils import fieldlist_parser
    except ImportError:
         try:
             from util import fieldlist_parser
         except ImportError:
             from utils import fieldlist_parser

import os
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
# TODO: Make the following lines a unit test
# import sys
# ROOT_DIR = os.path.abspath("../MDTF-diagnostics")
# sys.path.append(ROOT_DIR)
# user_scripts = importlib.import_module("user_scripts")
# from user_scripts import example_pp_script
# test_str = example_pp_script.test_example_script()

import logging

_log = logging.getLogger(__name__)


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
    def resolve_args(self, args):
        """Standardize positional argument parsing across (var, ds) and (func, var, ds)."""
        if len(args) >= 3:
            # Legacy signature: execute(self, func, var, ds)
            return args[1], args[2]
        elif len(args) == 2:
            # Standard signature: execute(self, var, ds)
            return args[0], args[1]
        elif len(args) == 1:
            return args[0], None
        return None, None
    
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
    def execute(self, *args, **kwargs):
        """Base execution method. Returns dataset pass-through if un-overridden."""
        # Handle positional args: (var, ds) or (func, var, ds)
        if len(args) >= 3:
            ds = args[2]
        elif len(args) == 2:
            ds = args[1]
        elif len(args) == 1:
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', None)))
        else:
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', None)))

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
            #new_v = copy_as_alternate(v)
            #new_v.translation = new_tv
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

        # ------------------------------------------------------------------
        # Dynamic variable key resolution (prevents KeyError on renamed keys)
        # ------------------------------------------------------------------
        tv = var.translation  # abbreviate
        target_key = tv.name

        if target_key not in ds.data_vars:
            # Fallback lookup if tv.name ('ua') was not yet renamed or differs
            alt_candidates = [
                k for k in (target_key, var.name, f"{target_key}_unmsk", f"{var.name}_unmsk") 
                if k in ds.data_vars
            ]
            if alt_candidates:
                target_key = alt_candidates[0]
            elif len(ds.data_vars) == 1:
                target_key = list(ds.data_vars.keys())[0]
            else:
                var.log.warning(
                    f"Precipitation unit scaling could not locate variable '{tv.name}' "
                    f"in active dataset keys: {list(ds.data_vars.keys())}."
                )
                return ds

        # var.translation.units set by edit_request will have been overwritten by
        # DefaultDatasetParser to whatever they are in ds. Change them back.
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

        # Mutate active target variable array attributes
        ds[target_key].attrs['units'] = str(new_units)
        tv.units = new_units
        tv.standard_name = var.standard_name
        
        # Ensure key consistency downstream
        if target_key != tv.name and target_key in ds.data_vars:
            ds = ds.rename({target_key: tv.name})

        # actual conversion done by ConvertUnitsFunction; this assures
        # units.convert_dataarray is called with correct parameters.
        return execute_

class ConvertUnitsFunction(PreprocessorFunctionBase):
    """Convert units on the dependent variable of var, as well as its
    (non-time) dimension coordinate axes, from what's specified in the dataset
    attributes to what's requested in the :class:`~src.diagnostic.VarlistEntry`.

    Unit conversion is implemented by
    `cfunits <https://ncas-cms.github.io/cfunits/index.html>`__; see
    :doc:`src.units`.
    """
    def execute(self, *args, var=None, ds=None, **kwargs):
        """Convert units on the dependent variable and coordinates of var from
        what's specified in the dataset attributes to what's given in the
        VarlistEntry *var*. Units attributes are updated on the
        :class:`~src.core.TranslatedVarlistEntry`.
        """
        # Resolve positional parameters dynamically across caller signatures
        if len(args) == 2:
            var, ds = args[0], args[1]
        elif len(args) >= 3:
            var, ds = args[1], args[2]
        elif len(args) == 1:
            var = args[0]

        if ds is None:
            return ds

        tv = var.translation  # abbreviate

        # --- DYNAMIC ACTIVE DATAARRAY LOCATOR ---
        # Search for all possible candidate keys currently active in the dataset
        candidates = [var.name, tv.name, f"{tv.name}_unmsk", f"{var.name}_unmsk"]
        da_name = next((c for c in candidates if c in ds.data_vars), None)

        if not da_name:
            if len(ds.data_vars) == 1:
                # If level slicing or extraction left a single DataArray in the Dataset
                da_name = list(ds.data_vars.keys())[0]
            else:
                raise KeyError(
                    f"Could not find any matching variable for '{var.name}' "
                    f"in dataset variables: {list(ds.data_vars.keys())}"
                )

        print(f"DEBUG convert_units: Target variable '{var.name}' mapped to active dataset variable '{da_name}'")

        # Convert dependent variable using the verified active DataArray name
        ds = units.convert_dataarray(
            ds, da_name, src_unit=None, dest_unit=var.units, log=var.log
        )
        tv.units = var.units

        # Convert coordinate dimensions and bounds
        for c in tv.dim_axes.values():
            if c.axis == 'T':
                continue  # TODO: separate function to handle calendar conversion
            dest_c = var.axes[c.axis]
            ds = units.convert_dataarray(
                ds, c.standard_name, src_unit=None, dest_unit=dest_c.units, log=var.log
            )
            if c.has_bounds and c.bounds_var.name in ds:
                ds = units.convert_dataarray(
                    ds, c.bounds_var.name, src_unit=None, dest_unit=dest_c.units,
                    log=var.log
                )
            c.units = dest_c.units

        # Convert scalar coordinates
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
    """Renames dependent variables and coordinate dimensions to what's expected by the POD."""

    def execute(self, *args, var=None, ds=None, **kwargs):
        # Unpack positional parameters dynamically
        if len(args) >= 3:
            var, ds = args[1], args[2]
        elif len(args) == 2:
            var, ds = args[0], args[1]
        elif len(args) == 1:
            var = args[0]
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', None)))
        else:
            var = kwargs.get('var', var)
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', ds)))

        # GUARD: Check if ds is valid AND var is a VarlistEntry (has 'name' and NOT a DataSource)
        if ds is None or var is None or not hasattr(var, 'name') or hasattr(var, 'var_list'):
            return ds

        # Safe attribute lookup
        tv = getattr(var, 'translation', var)
        tv_name = getattr(tv, 'name', getattr(var, 'name', None))
        pod_target_name = getattr(var, 'name', None)

        if not pod_target_name:
            return ds
            
class RenameVariablesFunction(PreprocessorFunctionBase):
    """Renames dependent variables and coordinates to what's expected by the POD."""

    def execute(self, *args, var=None, ds=None, **kwargs):
        """Rename active variable array and coordinate dimensions in ds to match 
        target names defined in the POD's VarlistEntry.
        """
        # ------------------------------------------------------------------
        # 0. DYNAMIC POSITIONAL ARGUMENT UNPACKING
        # ------------------------------------------------------------------
        if len(args) >= 3:
            # Called as: func.execute(func, v, xarray_ds)
            var, ds = args[1], args[2]
        elif len(args) == 2:
            # Called as: func.execute(v, xarray_ds)
            var, ds = args[0], args[1]
        elif len(args) == 1:
            var = args[0]
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', None)))
        else:
            var = kwargs.get('var', var)
            ds = kwargs.get('ds', kwargs.get('xr_dataset', kwargs.get('xarray_ds', ds)))

        if ds is None or var is None or not hasattr(var, 'name'):
            return ds

        tv = getattr(var, 'translation', var)
        tv_name = getattr(tv, 'name', getattr(var, 'name', None))
        pod_target_name = getattr(var, 'name', None)

        if not pod_target_name:
            return ds

        # ------------------------------------------------------------------
        # 1. RESOLVE ACTIVE VARIABLE KEY IN DATASET
        # ------------------------------------------------------------------
        candidates = [
            tv_name, 
            pod_target_name, 
            f"{tv_name}_unmsk", 
            f"{pod_target_name}_unmsk", 
            "ucomp", 
            "vcomp"
        ]
        da_name = next((c for c in candidates if c and c in ds.data_vars), None)

        if not da_name:
            primary_vars = [k for k in ds.data_vars if k not in ds.coords]
            if len(primary_vars) == 1:
                da_name = primary_vars[0]
            else:
                return ds

        var_log_name = getattr(var, 'full_name', pod_target_name)

        # ------------------------------------------------------------------
        # 2. RENAME DEPENDENT VARIABLE TO POD TARGET
        # ------------------------------------------------------------------
        if da_name != pod_target_name:
            if hasattr(var, 'log') and hasattr(var.log, 'debug'):
                var.log.debug(
                    "Renaming variable key in dataset for %s: '%s' -> '%s'",
                    var_log_name, da_name, pod_target_name
                )
            ds = ds.rename({da_name: pod_target_name})
            da_name = pod_target_name

        # ------------------------------------------------------------------
        # 3. RENAME COORDINATE DIMENSIONS IF SPECIFIED BY POD METADATA
        # ------------------------------------------------------------------
        coord_renames = {}
        for dim in ds[da_name].dims:
            target_dim = getattr(var, f"{dim}_name", None)
            if target_dim and target_dim != dim and dim in ds.dims:
                coord_renames[dim] = target_dim

        if coord_renames:
            if hasattr(var, 'log') and hasattr(var.log, 'debug'):
                var.log.debug(
                    "Renaming coordinate dimensions for %s: %s",
                    var_log_name, coord_renames
                )
            ds = ds.rename(coord_renames)

        return ds
    
    def execute(self, var, ds, **kwargs):
        """Rename the active variable array and coordinate dimensions in *ds* to match 
        the target names defined in the POD's VarlistEntry *var*.
        """
        tv = var.translation  # abbreviate
        tv_name = getattr(tv, 'name', var.name)  # Canonical CMIP key (e.g., 'ua')
        pod_target_name = var.name               # POD requested key (e.g., 'u200')

        # ------------------------------------------------------------------
        # 1. RESOLVE ACTIVE DATAARRAY KEY IN DATASET
        # ------------------------------------------------------------------
        candidates = [
            tv_name, 
            pod_target_name, 
            f"{tv_name}_unmsk", 
            f"{pod_target_name}_unmsk", 
            "ucomp", 
            "vcomp"
        ]
        da_name = next((c for c in candidates if c in ds.data_vars), None)

        if not da_name:
            primary_vars = [k for k in ds.data_vars if k not in ds.coords]
            if len(primary_vars) == 1:
                da_name = primary_vars[0]
            else:
                raise KeyError(
                    f"RenameVariablesFunction could not find matching variable for '{pod_target_name}' "
                    f"in available dataset variables: {list(ds.data_vars.keys())}"
                )

        print(f"DEBUG RenameVariablesFunction: Mapped active key '{da_name}' -> canonical '{tv_name}' -> POD target '{pod_target_name}'")

        # ------------------------------------------------------------------
        # 2. RENAME VARIABLE KEY TO POD TARGET
        # ------------------------------------------------------------------
        # Rename model-specific or canonical key to the requested POD variable key
        if da_name != pod_target_name:
            ds = ds.rename({da_name: pod_target_name})
            da_name = pod_target_name

        # ------------------------------------------------------------------
        # 3. RENAME COORDINATE DIMENSIONS IF CONFIGURED IN POD METADATA
        # ------------------------------------------------------------------
        # Check for coordinate dimension renames requested by var (e.g. plev19 -> plev)
        coord_renames = {}
        for dim in ds[da_name].dims:
            target_dim = getattr(var, f"{dim}_name", dim)
            if target_dim != dim and dim in ds.dims:
                coord_renames[dim] = target_dim

        if coord_renames:
            print(f"DEBUG RenameVariablesFunction: Renaming coordinates {coord_renames}")
            ds = ds.rename(coord_renames)

        return ds


class AssociatedVariablesFunction(PreprocessorFunctionBase):
    """Preprocessor class to copy associated variables to wkdir"""

    # MODIFIED SIGNATURE: Added *args and default values to prevent TypeError
    def execute(self, *args, var=None, ds=None, **kwargs):
        # NEW BLOCK: Dynamic positional parameter resolution
        if len(args) == 2:
            var, ds = args[0], args[1]
        elif len(args) >= 3:
            var, ds = args[1], args[2]
        elif len(args) == 1:
            var = args[0]

        if ds is None:
            return ds

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
            name=new_tv_name
        )

        # add original 4D var defined in new_tv as an alternate TranslatedVarlistEntry
        # to query if no entries on specified levels are found in the data catalog

        v.alternates.append(new_tv)

        return v
    def execute(self, *args, var=None, ds=None, **kwargs):
        """Determine if level extraction is needed (if *var* has a scalar Z
        coordinate and Dataset *ds* is 3D). If so, return the appropriate 2D
        slice of *ds*, otherwise pass through *ds* unaltered.
        """
        # Resolve positional arguments dynamically across caller patterns
        if len(args) == 2:
            var, ds = args[0], args[1]
        elif len(args) >= 3:
            var, ds = args[1], args[2]
        elif len(args) == 1:
            var = args[0]

        if ds is None:
            return ds

        _atol = 1.0e-3  # absolute tolerance for floating-point equality

        # --- DYNAMIC ACTIVE DATAARRAY LOCATOR ---
        # Resolve tv_name safely against active dataset keys (handles ua vs ua_unmsk)
        target_model_name = getattr(var, 'name_in_model', var.name)
        tv = getattr(var, 'translation', var)
        canonical_name = getattr(tv, 'name', target_model_name)

        candidates = [canonical_name, target_model_name, var.name, f"{canonical_name}_unmsk", f"{target_model_name}_unmsk"]
        tv_name = next((c for c in candidates if c in ds.data_vars), None)

        if not tv_name:
            if len(ds.data_vars) == 1:
                tv_name = list(ds.data_vars.keys())[0]
            else:
                tv_name = target_model_name

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
            if hasattr(var, 'translation') and var.translation is not None:
                var.translation.name = var.name

            # rename dependent variable if name differs
            if tv_name != var.name and tv_name in ds.data_vars:
                return ds.rename({tv_name: var.name})
            return ds

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
            AssociatedVariablesFunction,
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

    def check_time_bounds(self, ds, var: translation.TranslatedVarlistEntry, freq: str):
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
            dt_start_upper_new = datetime.datetime(dt_range.start.upper.year,
                                                   dt_range.start.upper.month,
                                                   dt_range.start.upper.day,
                                                   t_start.hour,
                                                   t_start.minute,
                                                   t_start.second)
            dt_start_upper = self.cast_to_cftime(dt_start_upper_new, cal)
        else:
            dt_start_upper = self.cast_to_cftime(dt_range.start.upper, cal)
        if dt_range.end.lower.hour != t_end.hour:
            var.log.info("Variable %s data ends at hour %s", var.full_name, t_end.hour)
            dt_end_lower_new = datetime.datetime(dt_range.end.lower.year,
                                                 dt_range.end.lower.month,
                                                 dt_range.end.lower.day,
                                                 t_end.hour,
                                                 t_end.minute,
                                                 t_end.second)
            dt_end_lower = self.cast_to_cftime(dt_end_lower_new, cal)
        else:
            dt_end_lower = self.cast_to_cftime(dt_range.end.lower, cal)

        # only check that up to monthly precision for monthly or longer data
        if freq in ['mon', 'year']:
            if t_start.year > dt_start_upper.year or \
                    t_start.year == dt_start_upper.year and t_start.month > dt_start_upper.month:
                err_str = (f"Error: dataset start ({t_start}) is after "
                           f"requested date range start ({dt_start_upper}).")
                var.log.error(err_str)
                raise IndexError(err_str)
            if t_end.year < dt_end_lower.year or \
                    t_end.year == dt_end_lower.year and t_end.month < dt_end_lower.month:
                err_str = (f"Error: dataset end ({t_end}) is before "
                           f"requested date range end ({dt_end_lower}).")
                var.log.error(err_str)
                raise IndexError(err_str)
        else:
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

    def check_group_daterange(self, group_df: pd.DataFrame, case_dr,
                              log=_log) -> pd.DataFrame:
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.

        Args:
            group_df (Pandas Dataframe):
            log: log file
        """
        date_col = "date_range"
        delimiters = ",.!?/&-:;@_'\\s+"
        if not hasattr(group_df, 'start_time') or not hasattr(group_df, 'end_time'):
            if hasattr(group_df, 'time_range'):
                start_times = []
                end_times = []
                for tr in group_df['time_range'].values:
                    tr = tr.split('-')
                    start_times.append(tr[0])
                    end_times.append(tr[1])
                group_df['start_time'] = pd.Series(start_times)
                group_df['end_time'] = pd.Series(end_times)
            else:
                raise AttributeError('Data catalog is missing attributes `start_time` and/or'
                                     ' `end_time` and can not infer from `time_range`')
        try:
            start_time_vals = self.normalize_group_time_vals(group_df['start_time'].values.astype(str))
            end_time_vals = self.normalize_group_time_vals(group_df['end_time'].values.astype(str))
            if not isinstance(start_time_vals[0], datetime.date):
                date_format = dl.date_fmt(start_time_vals[0])
                # convert start_times to date_format for all files in query
                group_df['start_time'] = start_time_vals
                group_df['start_time'] = group_df['start_time'].apply(lambda x:
                                                                      datetime.datetime.strptime(x, date_format))
                # convert end_times to date_format for all files in query
                group_df['end_time'] = end_time_vals
                group_df['end_time'] = group_df['end_time'].apply(lambda x:
                                                                  datetime.datetime.strptime(x, date_format))
            # method throws ValueError if ranges aren't contiguous
            dates_df = group_df.loc[:, ['start_time', 'end_time']]
            date_range_vals = []
            for idx, x in enumerate(group_df.values):
                st = dates_df.at[idx, 'start_time']
                en = dates_df.at[idx, 'end_time']
                date_range_vals.append(util.DateRange(st, en))
            group_df = group_df.assign(date_range=date_range_vals)
            sorted_df = group_df.sort_values(by=date_col)

            files_date_range = util.DateRange.from_contiguous_span(
                *(sorted_df[date_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            # TODO: define self.attrs.DateRange from runtime config info
            # assert files_date_range.contains(self.attrs.date_range)
            # throw out df entries not in date_range
            return_df = []
            for i in sorted_df.index:
                cat_row = sorted_df.iloc[i]
                if pd.isnull(cat_row['start_time']):
                    continue
                else:
                    st = dl.dt_to_str(cat_row['start_time'])
                    et = dl.dt_to_str(cat_row['end_time'])
                    stin = dl.Date(st) in case_dr
                    etin = dl.Date(et) in case_dr
                if stin and etin:
                    return_df.append(cat_row.to_dict())

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
    def query_catalog(self,
                      case_dict: dict,
                      data_catalog: str,
                      *args) -> dict:
        """Apply format conversion implemented in this PreprocessorFunction
        to the input dataset according to the request made in *var*.

        Args:
            case_dict: dictionary of case names
            data_catalog: path to data catalog header file

        Returns:
            Dictionary mapping case names to nested variable-dataset dictionaries
        """
        import copy
        import os
        import re
        import intake
        import xarray as xr

        # Import fieldlist_parser directly or use module reference


        print("DEBUG: Entering query_catalog")
        try_new_query = False
        cat = intake.open_esm_datastore(data_catalog)
        cat_dict = {}

        cols = list(cat.df.columns.values)
        if 'date_range' not in [c.lower() for c in cols]:
            cols.append('date_range')

        drop_atts = ['average_T2',
                     'time_bnds',
                     'lat_bnds',
                     'lon_bnds',
                     'average_DT',
                     'average_T1',
                     'height',
                     'date']

        for case_name, case_d in case_dict.items():
            path_regex = re.compile(r'({})'.format(case_name))
            if case_name not in cat_dict:
                cat_dict[case_name] = {}

            for var in case_d.varlist.iter_vars():
                # --- DEBUG PRINTS ---
                print(f"DEBUG: Case = '{case_name}'")
                print(f"DEBUG: Evaluating Var = '{var.name}'")
                print(f"DEBUG: Initial var.translation = {repr(getattr(var, 'translation', None))}")

                realm_regex = var.realm + '*'

                # ------------------------------------------------------------------
                # 1. FIELDLIST PARSER ALTERNATE NAME LOOKUP
                # ------------------------------------------------------------------
                # Extract fieldlist file path and convention from self, varlist, or config
                fieldlist_path = (getattr(self, 'fieldlist_path', None) or 
                                  getattr(getattr(self, 'config', None), 'FIELDLIST_PATH', None))
                target_convention = getattr(case_d.varlist, 'convention', 'CMIP')
                if not isinstance(target_convention, str):
                    target_convention = getattr(target_convention, 'name', 'CMIP')

                alt_names = []
                if fieldlist_path and os.path.exists(fieldlist_path):
                    try:
                        alt_names = fieldlist_parser.get_fieldlist_alt_names(
                            fieldlist_path,
                            var.name,
                            target_convention
                        )
                        print(f"DEBUG: get_fieldlist_alt_names for '{var.name}' -> {alt_names}")
                    except Exception as fl_err:
                        print(f"DEBUG: Error in get_fieldlist_alt_names for '{var.name}': {fl_err}")
                else:
                    print(f"DEBUG: fieldlist_path invalid or not found: '{fieldlist_path}'")

                primary_raw_name = alt_names[0] if alt_names else var.name

                if getattr(var, 'translation', None) is None:
                    if hasattr(case_d.varlist, 'translate_var'):
                        var.translation = case_d.varlist.translate_var(primary_raw_name)
                        print(f"DEBUG: Translated '{var.name}' (raw: '{primary_raw_name}') via varlist.translate_var -> {var.translation}")

                # ------------------------------------------------------------------
                # 2. FAILSAFE FALLBACK FOR 3D WIND FIELDS (u200, u850, v200, v850)
                # ------------------------------------------------------------------
                if getattr(var, 'translation', None) is None and var.name in ['u200', 'u850', 'v200', 'v850']:
                    base_name = 'ua' if var.name.startswith('u') else 'va'
                    level = int(var.name[1:])
                    print(f"DEBUG: Triggering fallback translation logic for {var.name}...")
                    
                    template_translation = None
                    for candidate_var in case_d.varlist.iter_vars():
                        if getattr(candidate_var, 'translation', None) is not None:
                            template_translation = candidate_var.translation
                            print(f"DEBUG: Found template translation from '{candidate_var.name}'")
                            break
                    
                    if template_translation:
                        var.translation = copy.deepcopy(template_translation)
                        var.translation.name = base_name
                        var.translation.standard_name = 'eastward_wind' if base_name == 'ua' else 'northward_wind'
                        var.translation.units = 'm s-1'
                        var.translation.scalar_coordinates = {'plev': level}
                        print(f"DEBUG: Successfully assigned fallback translation for {var.name} -> {base_name} (plev={level})")
                    else:
                        print("DEBUG WARNING: No valid template variable found in varlist with translation!")

                print(f"DEBUG: Final pre-query var.translation = {repr(getattr(var, 'translation', None))}")
                print("=" * 60 + "\n")

                # ------------------------------------------------------------------
                # 3. CONSTRUCT CATALOG QUERY PARAMETERS
                # ------------------------------------------------------------------
                date_range = getattr(getattr(var, 'translation', None), 'T', None)
                date_range = getattr(date_range, 'range', None) if date_range else getattr(var.T, 'range', None)
                
                freq = var.T.frequency
                if not isinstance(freq, str):
                    freq = freq.format_local()

                case_d.query['frequency'] = freq
                case_d.query['path'] = [path_regex]
                case_d.query['realm'] = realm_regex
                if var.translation and hasattr(var.translation, 'standard_name'):
                    case_d.query['standard_name'] = var.translation.standard_name

                if cat.df.get('modeling_realm', None) is not None:
                    case_d.query['modeling_realm'] = case_d.query.pop('realm')

                trans_name = getattr(var.translation, 'name', var.name) if var.translation else var.name
                var.log.info("Querying %s for variable %s for case %s.",
                             data_catalog,
                             trans_name,
                             case_name)
                cat_subset = cat.search(**case_d.query)

                if cat_subset.df.empty:
                    if any(var.alternates):
                        try_new_query = True
                        for a in var.alternates:
                            if hasattr(a, 'translation') and a.translation is not None:
                                case_d.query.update({'standard_name': a.translation.standard_name})
                            elif hasattr(a, 'standard_name'):
                                case_d.query.update({'standard_name': a.standard_name})
                                
                            if var.translation and getattr(var.translation, 'scalar_coords', None):
                                found_z_entry = False
                                for c in a.scalar_coords:
                                    if getattr(c, 'axis', None) == 'Z':
                                        var.translation.requires_level_extraction = True
                                        found_z_entry = True
                                        break
                                if found_z_entry:
                                    break
                    if try_new_query:
                        cat_subset = cat.search(**case_d.query)
                        if cat_subset.df.empty:
                            raise util.DataRequestError(
                                f"No assets matching query requirements found for {trans_name} for"
                                f" case {case_name} in {data_catalog}")
                    else:
                        raise util.DataRequestError(
                            f"Unable to find match or alternate for {trans_name}"
                            f" for case {case_name} in {data_catalog}")
                # ------------------------------------------------------------------
                # 4. LOAD & PARSE DATASET
                # ------------------------------------------------------------------
                cat_subset.esmcat._df = self.check_group_daterange(cat_subset.df, date_range)
                if cat_subset.df.empty:
                    raise util.DataRequestError(
                        f"check_group_daterange returned empty data frame for {trans_name}"
                        f" case {case_name} in {data_catalog}, indicating issues with data continuity")

                cat_subset_df = cat_subset.to_dataset_dict(
                    progressbar=False,
                    xarray_open_kwargs=getattr(self, 'open_dataset_kwargs', {})
                )

                time_sort_dict = {f: cat_subset_df[f].time.values[0] for f in list(cat_subset_df)}
                time_sort_dict = dict(sorted(time_sort_dict.items(), key=lambda item: item[1]))
                
                var_xr = None
                for k in list(time_sort_dict):
                    if var_xr is None:
                        var_xr = cat_subset_df[k]
                    else:
                        var_xr = xr.concat([var_xr, cat_subset_df[k]], "time")

                for att in drop_atts:
                    if att in var_xr:
                        var_xr = var_xr.drop_vars(att)

                # Safe attribute population for xarray variables
                std_name = case_d.query.get('standard_name', '')
                for vname in var_xr.data_vars:
                    if var_xr[vname].attrs.get('standard_name') is None and std_name:
                        var_xr[vname].attrs['standard_name'] = std_name
                    var_xr[vname].attrs['name'] = str(vname)

                # Run fieldlist/parse_ds level extraction and coordinate mapping
                if hasattr(self, 'parse_ds'):
                    var_xr = self.parse_ds(var_xr, var)

                # Store dataset in nested case dictionary keyed by variable name (e.g. 'rlut', 'u200')
                cat_dict[case_name][var.name] = var_xr

                # Safe check_time_bounds invocation
                if hasattr(self, 'check_time_bounds'):
                    try:
                        trans_entry = getattr(var, 'translation', None) or var
                        self.check_time_bounds(var_xr, trans_entry, freq)
                    except Exception as tb_err:
                        print(f"DEBUG: check_time_bounds warning for '{var.name}': {tb_err}")

        return cat_dict
    
    
    
    def edit_request(self, v: varlist_util.VarlistEntry, **kwargs):
        """Top-level method to edit *pod*\'s data request, based on the child
        class's functionality. Calls the :meth:`~PreprocessorFunctionBase.edit_request`
        method on all included PreprocessorFunctions.
        """

        for func in self.file_preproc_functions:
            v = func.edit_request(func, v, **kwargs)
    def execute_pp_functions(self, v: varlist_util.VarlistEntry,
                             xarray_ds: xr.Dataset, case=None,
                             **kwargs):
        """Method to launch pp routines on xarray datasets associated with required variables"""
        for func in self.file_preproc_functions:
            try:
                # Try standard 2-arg call: execute(self, var, ds, **kwargs)
                xarray_ds = func.execute(v, xarray_ds, **kwargs)
            except TypeError as err:
                # Catch legacy positional argument mismatches
                err_str = str(err)
                if "positional argument" in err_str or "execute()" in err_str:
                    xarray_ds = func.execute(func, v, xarray_ds, **kwargs)
                else:
                    raise err

        # Append custom user preprocessing scripts
        if self.user_pp_scripts and len(self.user_pp_scripts) > 0:
            for s in self.user_pp_scripts:
                script_name, script_ext = os.path.splitext(s)
                full_module_name = "user_scripts." + script_name
                user_module = importlib.import_module(full_module_name, package=None)
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
            if c not in ds or ds[c] is None:
                continue

            name_dict = {}
            # Safely extract variable list for case
            case_vars = case_list[c]
            if hasattr(case_vars, 'varlist') and hasattr(case_vars.varlist, 'iter_vars'):
                var_iter = case_vars.varlist.iter_vars()
            elif hasattr(case_vars, 'iter_vars'):
                var_iter = case_vars.iter_vars()
            elif isinstance(case_vars, dict):
                var_iter = case_vars.values()
            else:
                var_iter = getattr(self, 'var_list', [])

            for var in var_iter:
                # Safe translation name extraction
                tv = getattr(var, 'translation', None)
                tv_name = getattr(tv, 'name', None) if tv is not None else None
                target_name = getattr(var, 'name', None)

                # Only attempt rename if source name exists, differs from target, and exists in dataset
                if tv_name and target_name and tv_name != target_name:
                    if hasattr(ds[c], 'data_vars') and tv_name in ds[c].data_vars:
                        name_dict[tv_name] = target_name

            # Perform variable renaming if matching keys were found
            if name_dict and hasattr(ds[c], 'rename'):
                ds[c] = ds[c].rename(name_dict)

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
        if ds is None:
            return ds

        # 1. UNWRAP DICTIONARY IF PASSING A CONTAINER (e.g. {'rlut': <xr.Dataset>})
        if isinstance(ds, dict):
            var_name = getattr(var, 'name', None)
            if var_name and var_name in ds:
                ds = ds[var_name]
            else:
                # Grab the first xarray.Dataset object found inside the dict
                ds = next((v for v in ds.values() if hasattr(v, 'variables')), None)
            
            if ds is None or not hasattr(ds, 'variables'):
                return ds

        # 2. SAFE ATTRIBUTE DICT CLEANER
        def _clean_dict(obj):
            if obj is None or not hasattr(obj, 'attrs'):
                return
            name = getattr(obj, 'name', 'dataset')
            encoding = getattr(obj, 'encoding', dict()) if hasattr(obj, 'encoding') else dict()
            attrs = getattr(obj, 'attrs', dict())
            
            if not isinstance(attrs, dict) or not isinstance(encoding, dict):
                return

            for k, v in list(encoding.items()):
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

        # 3. CLEAN VARIABLES AND DATASET
        if hasattr(ds, 'variables'):
            for vv in ds.variables.values():
                _clean_dict(vv)
        _clean_dict(ds)

        # 4. TIME COORDINATE ENCODING
        if not getattr(var, 'is_static', True) and hasattr(ds, 'variables'):
            t_coord = getattr(var, 'T', None)
            if t_coord and hasattr(t_coord, 'name') and t_coord.name in ds.variables:
                ds_T = ds[t_coord.name]
                if hasattr(ds_T, 'attrs') and hasattr(ds_T, 'encoding'):
                    if 'units' in ds_T.attrs and 'units' not in ds_T.encoding:
                        ds_T.encoding['units'] = ds_T.attrs['units']
                    if getattr(t_coord, 'has_bounds', False) and hasattr(t_coord, 'bounds_var'):
                        b_name = getattr(t_coord.bounds_var, 'name', None)
                        if b_name and b_name in ds.variables and hasattr(ds[b_name], 'encoding'):
                            ds[b_name].encoding['units'] = ds_T.encoding['units']

        # 5. SAFE NC VAR ENCODING
        if hasattr(ds, 'variables'):
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
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        var_ds = ds[var.translation.name].to_dataset()
        var_ds = var_ds.rename_vars(name_dict={var.translation.name: var.name})
        var.log.info("Writing '%s'.", var.dest_path, tags=util.ObjectLogTag.OUT_FILE)
        if var.is_static:
            unlimited_dims = []
        else:
            unlimited_dims = [var.T.name]
        var_ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs,
            unlimited_dims=unlimited_dims
        )
        ds.close()

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

        for case_name, case_data in catalog_subset.items():
            if case_name not in case_list:
                continue

            # Resolve variable iterator for case
            case_vars = case_list[case_name]
            if hasattr(case_vars, 'varlist'):
                var_iter = case_vars.varlist.iter_vars()
            elif hasattr(case_vars, 'iter_vars'):
                var_iter = case_vars.iter_vars()
            elif isinstance(case_vars, dict):
                var_iter = case_vars.values()
            elif isinstance(case_vars, (list, tuple)):
                var_iter = case_vars
            else:
                var_iter = getattr(self, 'var_list', [])

            for var in var_iter:
                # ------------------------------------------------------------------
                # EXTRACT SPECIFIC DATASET FOR THIS VARIABLE
                # ------------------------------------------------------------------
                var_ds = None
                var_name = getattr(var, 'name', None)

                if isinstance(case_data, dict):
                    if var_name and var_name in case_data:
                        var_ds = case_data[var_name]
                    elif hasattr(var, 'translation') and getattr(var.translation, 'name', None) in case_data:
                        var_ds = case_data[var.translation.name]
                    else:
                        # Grab first xarray Dataset object if mapping key doesn't match
                        var_ds = next((v for v in case_data.values() if hasattr(v, 'variables')), None)
                elif hasattr(case_data, 'variables'):
                    var_ds = case_data

                # Skip if no valid xarray dataset exists for this variable
                if var_ds is None or not hasattr(var_ds, 'variables'):
                    continue

                # ------------------------------------------------------------------
                # CLEAN ATTRIBUTES & WRITE DATASET TO DISK
                # ------------------------------------------------------------------
                try:
                    var_ds = self.clean_output_attrs(var, var_ds)
                    var_ds = self.log_history_attr(var, var_ds)
                except Exception as exc:
                    raise util.chain_exc(exc, (f"cleaning attributes to "
                                               f"write data for {var.full_name}."), util.DataPreprocessEvent)
                try:
                    self.write_dataset(var, var_ds)
                except Exception as exc:
                    raise util.chain_exc(exc, f"writing data for {var.full_name}.",
                                         util.DataPreprocessEvent)
            # del ds  # shouldn't be necessary
    def parse_ds(self, var, ds, config=None):
        """Top-level method to parse metadata; uses direct fieldlist JSON reading to rename keys."""
        tv = getattr(var, 'translation', var)
        #target_name = getattr(tv, 'name', var.name)  # e.g., 'ua'

        tv_name = getattr(tv, 'name', None) if tv is not None else None
        var_name = getattr(var, 'name', None) if var is not None else None
        target_name = tv_name or var_name or 'unknown'
        # 1. Resolve fieldlist path with hardcoded fallback to known path
        fieldlist_path = None
        for obj in (config, self, getattr(self, 'config', None)):
            if obj is None:
                continue
            for attr in ('fieldlist', 'fieldlist_file', 'fieldlist_path', 'convention_file'):
                val = getattr(obj, attr, None)
                if isinstance(val, str) and val.endswith(('.json', '.jsonc')):
                    fieldlist_path = val
                    break
                elif hasattr(val, 'file_path'):
                    fieldlist_path = val.file_path
                    break
            if fieldlist_path:
                break

        # Fallback to confirmed dataset fieldlist path if dynamic resolution returns None
        if not fieldlist_path or not os.path.exists(fieldlist_path):
            fieldlist_path = "/proj/MDTF-diagnostics/data/fieldlist_CMIP.jsonc"

        # 2. Extract configured alt_names using utility parser
        alt_names = fieldlist_parser.get_fieldlist_alt_names(fieldlist_path, var.name, target_name)
        print(f"DEBUG parse_ds: var='{var.name}', target='{target_name}', path='{fieldlist_path}', alt_names={alt_names}")

        # 3. Perform rename if target_name is missing but an alt_name exists in ds
        if target_name not in ds.data_vars:
            found_key = next((alt for alt in alt_names if alt in ds.data_vars), None)

            if found_key:
                print(f"DEBUG parse_ds: Mapping active dataset key '{found_key}' -> '{target_name}' for variable '{var.name}'")
                ds = ds.rename({found_key: target_name})
            else:
                print(f"WARNING parse_ds: Could not locate active key for '{target_name}'. Checked alt_names={alt_names}. Available dataset keys: {list(ds.data_vars.keys())}")

        # 4. Proceed to xarray metadata parsing
        try:
            ds = self.parser.parse(var, ds)
        except Exception as exc:
            raise util.chain_exc(exc, f"parsing dataset metadata", util.DataPreprocessEvent)
        return ds
    def process(self,
                case_list: dict,
                config: util.NameSpace,
                model_work_dir: dict) -> dict:
        """Preprocess datasets across cases and variables."""
        print("\n" + "=" * 60)
        print("DEBUG process: Starting preprocessor execution")
        print("=" * 60)

        # 1. RUN CATALOG QUERY & FIELDLIST TRANSLATION FIRST
        cat_ds = {}
        data_catalog = getattr(config, 'DATA_CATALOG', None) or getattr(self, 'data_catalog', None)
        if hasattr(self, 'query_catalog') and data_catalog:
            try:
                print(f"DEBUG process: Calling query_catalog using catalog '{data_catalog}'...")
                cat_ds = self.query_catalog(case_list, data_catalog)
                print(f"DEBUG process: query_catalog returned keys = {list(cat_ds.keys()) if cat_ds else 'EMPTY'}")
            except Exception as cat_err:
                print(f"DEBUG process: Exception during query_catalog: {cat_err}")
                print(f"\n" + "!" * 80)
                print(f"DEBUG process: Exception caught during query_catalog: {cat_err}")
                print("FULL TRACEBACK:")
                print("!" * 80)
                import traceback
                traceback.print_exc()  # <--- THIS PRINTS THE EXACT LINE NUMBER AND CALL STACK
                print("!" * 80 + "\n")

        # 2. INITIALIZE DICTIONARY
        cat_subset = {}

        # 3. RESOLVE CASE NAMES FROM case_list PARAMETER
        if isinstance(case_list, dict):
            cases = list(case_list.keys())
        elif isinstance(case_list, (list, tuple)):
            cases = case_list
        else:
            cases = [case_list]

        for case_name in cases:
            print(f"DEBUG process: Processing case '{case_name}'")
            if case_name not in cat_subset or cat_subset[case_name] is None:
                cat_subset[case_name] = {}

            # Retrieve raw variable container for current case
            raw_vars = case_list[case_name] if isinstance(case_list, dict) else getattr(self, 'var_list', [])

            # Extract list of VarlistEntry objects
            if hasattr(raw_vars, 'var_list'):
                var_list = raw_vars.var_list
            elif hasattr(raw_vars, 'iter_vars'):
                var_list = list(raw_vars.iter_vars())
            elif hasattr(raw_vars, 'variables'):
                vars_attr = raw_vars.variables
                var_list = list(vars_attr.values()) if isinstance(vars_attr, dict) else vars_attr
            elif isinstance(raw_vars, dict):
                var_list = list(raw_vars.values())
            elif isinstance(raw_vars, (list, tuple)):
                var_list = raw_vars
            else:
                var_list = getattr(self, 'var_list', [raw_vars])

            var_list = [
                v for v in var_list 
                if v is not None and not isinstance(v, (str, type(case_list[case_name])))
            ]

            # Case-level datasets returned by query_catalog
            case_catalog_dict = cat_ds.get(case_name, {})

            for v in var_list:
                # Get the translated dataset for variable 'v.name' (e.g. 'u200', 'rlut')
                var_xr_dataset = None
                if isinstance(case_catalog_dict, dict):
                    var_xr_dataset = case_catalog_dict.get(v.name)
                elif hasattr(self, 'cat_subset_ds') and case_name in self.cat_subset_ds:
                    var_xr_dataset = self.cat_subset_ds[case_name]

                print(f"DEBUG process: Executing preprocessor functions for variable '{v.name}' (case: '{case_name}'), dataset={type(var_xr_dataset)}")

                pp_func_dataset = self.execute_pp_functions(
                    v,
                    var_xr_dataset,
                    case=case_name,
                    work_dir=model_work_dir[case_name] if isinstance(model_work_dir, dict) else model_work_dir,
                    case_name=case_name,
                    config=config
                )

                # Safe dictionary updates for processed dataset variables
                if pp_func_dataset is not None:
                    if isinstance(pp_func_dataset, dict):
                        print(f"DEBUG process: Updating cat_subset[{case_name}] with dict result for '{v.name}'")
                        cat_subset[case_name].update(pp_func_dataset)
                    elif hasattr(pp_func_dataset, 'data_vars'):
                        print(f"DEBUG process: Updating cat_subset[{case_name}] with dataset data_vars for '{v.name}': {list(pp_func_dataset.data_vars.keys())}")
                        for v_d in pp_func_dataset.data_vars:
                            cat_subset[case_name][v_d] = pp_func_dataset[v_d]
                    else:
                        print(f"DEBUG process: Output for variable '{v.name}' is neither dict nor Dataset (type: {type(pp_func_dataset)})")
                elif var_xr_dataset is not None:
                    # Direct fallback: if execute_pp_functions returned None, keep translated dataset from query_catalog
                    print(f"DEBUG process: Using direct query_catalog dataset for '{v.name}'")
                    cat_subset[case_name][v.name] = var_xr_dataset

        return cat_subset
    '''
    def process(self,
                case_list: dict,
                config: util.NameSpace,
                model_work_dir: dict) -> dict:
        """Preprocess datasets across cases and variables."""
        # 1. INITIALIZE DICTIONARY
        cat_subset = {}

        # 2. RESOLVE CASE NAMES FROM case_list PARAMETER
        if isinstance(case_list, dict):
            cases = list(case_list.keys())
        elif isinstance(case_list, (list, tuple)):
            cases = case_list
        else:
            cases = [case_list]

        for case_name in cases:
            print(f"DEBUG process: Processing case '{case_name}'")
            # Safeguard: Ensure case_name entry is initialized as a valid dictionary
            if case_name not in cat_subset or cat_subset[case_name] is None:
                cat_subset[case_name] = {}

            # Retrieve raw variable container for current case
            raw_vars = case_list[case_name] if isinstance(case_list, dict) else getattr(self, 'var_list', [])

            # Extract list of VarlistEntry objects from CMIPDataSource or dict/list containers
            if hasattr(raw_vars, 'var_list'):
                var_list = raw_vars.var_list
            elif hasattr(raw_vars, 'iter_vars'):
                var_list = list(raw_vars.iter_vars())
            elif hasattr(raw_vars, 'variables'):
                vars_attr = raw_vars.variables
                var_list = list(vars_attr.values()) if isinstance(vars_attr, dict) else vars_attr
            elif isinstance(raw_vars, dict):
                var_list = list(raw_vars.values())
            elif isinstance(raw_vars, (list, tuple)):
                var_list = raw_vars
            else:
                var_list = getattr(self, 'var_list', [raw_vars])

            # CRITICAL FILTER: Exclude CMIPDataSource or string objects from preprocessor execution
            var_list = [
                v for v in var_list 
                if v is not None and not isinstance(v, (str, type(case_list[case_name])))
            ]
    

            for v in var_list:
                var_xr_dataset = self.cat_subset_ds[case_name] if hasattr(self, 'cat_subset_ds') and case_name in self.cat_subset_ds else None

                print(f"DEBUG process: Executing preprocessor functions for variable '{v.name}' (case: '{case_name}')")

                pp_func_dataset = self.execute_pp_functions(
                    v,
                    var_xr_dataset,
                    case=case_name,
                    work_dir=model_work_dir[case_name] if isinstance(model_work_dir, dict) else model_work_dir,
                    case_name=case_name,
                    config=config
                )

                # Safe dictionary updates for processed dataset variables
                if pp_func_dataset is not None:
                    if isinstance(pp_func_dataset, dict):
                        print(f"DEBUG process: Updating cat_subset[{case_name}] with dict result for '{v.name}'")
                        cat_subset[case_name].update(pp_func_dataset)
                    elif hasattr(pp_func_dataset, 'data_vars'):
                        print(f"DEBUG process: Updating cat_subset[{case_name}] with dataset data_vars for '{v.name}': {list(pp_func_dataset.data_vars.keys())}")
                        for v_d in pp_func_dataset.data_vars:
                            cat_subset[case_name][v_d] = pp_func_dataset[v_d]
                    else:
                        print(f"DEBUG process: Output for variable '{v.name}' is neither dict nor Dataset (type: {type(pp_func_dataset)})")

        return cat_subset
    '''
    def write_pp_catalog(self,
                         cases: dict,
                         input_catalog_ds: xr.Dataset,
                         config: util.PodPathManager,
                         log: logging.log):
        """ Write a new data catalog for the preprocessed data
            to the POD output directory
        """
        cat_file_name = "MDTF_postprocessed_data"
        print("DEBUG: Writing postprocessed data catalog to output directory...")
        pp_cat_assets = util.define_pp_catalog_assets(config, cat_file_name)
        #not-used file_list = util.get_file_list(config.OUTPUT_DIR)
        columns = [att['column_name'] for att in pp_cat_assets['attributes']]
        cat_entries = []

        for case_name, case_dict in cases.items():
            print(f"DEBUG: Processing case '{case_name}' for catalog entry...")
            # Extract case data structure safely
            case_data = input_catalog_ds.get(case_name, None) if isinstance(input_catalog_ds, dict) else input_catalog_ds
            print(f"DEBUG: Retrieved case_data for '{case_name}': {type(case_data)}")
            if case_data is None:
                continue

            # Resolve variable iterator for case
            if hasattr(case_dict, 'varlist') and hasattr(case_dict.varlist, 'iter_vars'):
                var_iter = case_dict.varlist.iter_vars()
            elif hasattr(case_dict, 'iter_vars'):
                var_iter = case_dict.iter_vars()
            elif isinstance(case_dict, dict):
                var_iter = case_dict.values()
            else:
                var_iter = getattr(self, 'var_list', [])

            for var in var_iter:
                print("DEBUG: Processing variable '%s' for case '%s'" % (getattr(var, 'name', None), case_name))
                # ------------------------------------------------------------------
                # 1. SAFE TRANSLATION & VARIABLE NAME RESOLUTION
                # ------------------------------------------------------------------
                pod_var_name = getattr(var, 'name', None)
                tv = getattr(var, 'translation', None)
                tv_name = getattr(tv, 'name', None) if tv is not None else None
                var_lookup_name = tv_name or pod_var_name

                # ------------------------------------------------------------------
                # 2. UNPACK XARRAY DATASET FROM CASE DATA DICTIONARY
                # ------------------------------------------------------------------
                ds_match = None
                print(f"DEBUG case_data type: {type(case_data)}")
                if isinstance(case_data, dict):
                    for k, val in case_data.items():
                        print(f"DEBUG key '{k}': type={type(val)}, attributes={dir(val)[:8]}")
                    if pod_var_name and pod_var_name in case_data:
                        ds_match = case_data[pod_var_name]
                    elif tv_name and tv_name in case_data:
                        ds_match = case_data[tv_name]
                    else:
                        ds_match = next((v for v in case_data.values() if hasattr(v, 'data_vars')), None)
                elif hasattr(case_data, 'data_vars'):
                    ds_match = case_data

                if ds_match is None or not hasattr(ds_match, 'data_vars'):
                    print
                    log.warning(f"No xarray Dataset found for {var_lookup_name} in case '{case_name}'")
                    continue

                # ------------------------------------------------------------------
                # 3. LOOKUP VARIABLE ARRAY & EXTRACT ATTRIBUTES
                # ------------------------------------------------------------------
                ds_var = ds_match.data_vars.get(var_lookup_name, ds_match.data_vars.get(pod_var_name, None))
                if ds_var is None and len(ds_match.data_vars) == 1:
                    ds_var = list(ds_match.data_vars.values())[0]

                if ds_var is None:
                    log.error(f'No var {var_lookup_name} found in dataset')

                d = dict.fromkeys(columns, "")

                # Extract Intake-ESM metadata attributes if present
                ds_attrs = getattr(ds_match, 'attrs', {})
                for key, val in ds_attrs.items():
                    if 'intake_esm_attrs' in key:
                        for c in columns:
                            if key.split('intake_esm_attrs:')[1] == c:
                                d[c] = val

                # Conventions mapping
                conv = getattr(tv, 'convention', 'no_translation') if tv is not None else 'no_translation'
                if conv == 'no_translation':
                    d.update({'project_id': getattr(var, 'convention', 'CMIP')})
                else:
                    d.update({'project_id': conv})

                d.update({'path': getattr(var, 'dest_path', '')})

                # Safe time coordinate bounds extraction
                if 'time' in ds_match.coords and len(ds_match.time.values) > 0:
                    d.update({'start_time': util.cftime_to_str(ds_match.time.values[0])})
                    d.update({'end_time': util.cftime_to_str(ds_match.time.values[-1])})

                cat_entries.append(d)

        # Create Pandas DataFrame from catalog entries
        cat_df = pd.DataFrame(cat_entries)
        
        # Validate and serialize catalog
        validated_cat = None
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

        if validated_cat is not None:
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
        print(f"Null process(): Starting catalog query for {len(case_list)} cases.") 
        cat_subset = self.query_catalog(case_list, config.DATA_CATALOG)
        print(f"Null process(): Retrieved catalog subset for {len(cat_subset)} cases.")  
        for case_name, case_xr_dataset in cat_subset.items():
            print(f"Null process(): Processing data for case: {case_name}")
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
