"""Functionality for transforming model data into the format expected by PODs
once it's been download to local storage.
"""
import os
import abc
import dataclasses
from src import util, core, diagnostic, xr_util
import cftime
import xarray as xr

import logging
_log = logging.getLogger(__name__)

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
        """Edit the data requested in the POD's Varlist queue, based on the 
        transformations the functionality can perform. If the function can
        transform data in format X to format Y and the POD requests X, this
        method should insert a backup/fallback request for Y.
        """
        pass

    @abc.abstractmethod
    def process(self, var, dataset):
        """Apply functionality to the input dataset.

        Args:
            var: :class:`~src.diagnostic.VarlistEntry` instance describing POD's
                data request: desired end result of preprocessing work.
            dataset: `xarray.Dataset 
                <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__ 
                instance.
        """
        return dataset

class CropDateRangeFunction(PreprocessorFunctionBase):
    """A :class:`PreprocessorFunctionBase` which trims the time axis of the
    dataset to the user-requested analysis period.
    """
    @staticmethod
    def cast_to_cftime(dt, calendar):
        """HACK to cast python datetime to cftime.datetime with given calendar.
        """
        # NB "tm_mday" is not a typo
        t = dt.timetuple()
        tt = (getattr(t, attr_) for attr_ in 
            ('tm_year', 'tm_mon', 'tm_mday', 'tm_hour', 'tm_min', 'tm_sec'))
        return cftime.datetime(*tt, calendar=calendar)

    def process(self, var, ds):
        """Parse quantities related to the calendar for time-dependent data.
        In particular, ``date_range`` was set from user input before we knew the 
        model's calendar. HACK here to cast those values into `cftime.datetime 
        <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        objects so they can be compared with the model data's time axis.
        """
        tv_name = var.name_in_model
        t_coord = ds.cf.dim_axes(tv_name).get('T', None)
        if t_coord is None:
            _log.debug("Exit %s for %s: time-independent.", 
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
            _log.error(err_str)
            raise IndexError(err_str)
        if t_end < dt_end_lower:
            err_str = (f"Error: dataset end ({t_end}) is before "
                f"requested date range end ({dt_end_lower}).")
            _log.error(err_str)
            raise IndexError(err_str)

        ds = ds.sel({t_coord.name: slice(dt_start_lower, dt_end_upper)})
        new_t = ds.cf.dim_axes(tv_name).get('T')
        if t_size == new_t.size:
            _log.info(("Requested dates for %s coincide with range of dataset "
                "'%s -- %s'; left unmodified."),
                var.full_name,
                new_t.values[0].strftime('%Y-%m-%d'), 
                new_t.values[-1].strftime('%Y-%m-%d'), 
            )
        else:
            _log.info("Cropped date range of %s from '%s -- %s' to '%s -- %s'.",
                    var.full_name,
                    t_start.strftime('%Y-%m-%d'), 
                    t_end.strftime('%Y-%m-%d'), 
                    new_t.values[0].strftime('%Y-%m-%d'), 
                    new_t.values[-1].strftime('%Y-%m-%d'), 
                )
        return ds

class ConvertUnitsFunction(PreprocessorFunctionBase):
    """Convert units on the dependent variable of var, as well as its
    (non-time) dimension coordinate axes, from what's specified in the dataset
    attributes to what's given in the VarlistEntry.
    """
    def process(self, var, ds):
        """Convert units on the dependent variable and coordinates of var from 
        what's specified in the dataset attributes to what's given in the 
        VarlistEntry. Units attributes are updated on the translated VarlistEntry.
        """
        tv = var.translation # abbreviate
        # convert dependent variable
        ds[tv.name] = util.convert_dataarray(ds[tv.name], var.units, allow_h2o=True)
        tv.units = var.units

        # convert coordinate dimensions and bounds
        for c in tv.dim_axes.values():
            if c.axis == 'T':
                continue # handle calendar stuff etc. in another function
            dest_c = var.axes[c.axis]
            ds[c.name] = util.convert_dataarray(ds[c.name], dest_c.units, 
                allow_h2o=False)
            if c.bounds and c.bounds in ds:
                ds[c.bounds] = util.convert_dataarray(ds[c.bounds], dest_c.units, 
                    allow_h2o=False)
            c.units = dest_c.units

        # convert scalar coordinates
        for c in tv.scalar_coords:
            if c.name in ds:
                dest_c = var.axes[c.axis]
                ds[c.name] = util.convert_dataarray(ds[c.name], dest_c.units, 
                    allow_h2o=False)
                c.units = dest_c.units
                c.value = ds[c.name].item()

        _log.info("Converted units on %s.", var.full_name)
        return ds

class RenameVariablesFunction(PreprocessorFunctionBase):
    def process(self, var, ds):
        tv = var.translation # abbreviate
        rename_d = dict()
        # rename var
        if tv.name != var.name:
            _log.debug("Rename '%s' variable in %s to '%s'.", 
                tv.name, var.full_name, var.name)
            rename_d[tv.name] = var.name
            tv.name = var.name

        # rename coords
        for c in tv.dim_axes.values():
            dest_c = var.axes[c.axis]
            if c.name != dest_c.name:
                _log.debug("Rename %s axis of %s from '%s' to '%s'.", 
                    c.axis, var.full_name, c.name, dest_c.name)
                rename_d[c.name] = dest_c.name
                c.name = dest_c.name
        # TODO: bounds??

        # rename scalar coords
        for c in tv.scalar_coords:
            if c.name in ds:
                dest_c = var.axes[c.axis]
                _log.debug("Rename %s scalar coordinate of %s from '%s' to '%s'.", 
                    c.axis, var.full_name, c.name, dest_c.name)
                rename_d[c.name] = dest_c.name
                c.name = dest_c.name

        return ds.rename(rename_d)

class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a single pressure level from a DataSet. Unit conversions of 
    pressure are handled by cfunits, but paramateric vertical coordinates are 
    **not** handled (interpolation is not implemented here.) If the exact level 
    is not provided by the data, KeyError is raised.
    """

    def remove_scalar_on_translation(self, v, data_mgr):
        """If a VarlistEntry has a scalar_coordinate defined, return a copy to 
        be used as an alternate variable with that scalar_coordinate removed.
        """
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
                data_mgr.convention, v.standard_name, new_ax_set
            )
        new_tv = tv.remove_scalar(
            tv.scalar_coords[0].axis,
            name = new_tv_name
        )
        new_v = dataclasses.replace(
            v,
            coords = (v.dims + v.scalar_coords),
            translation = new_tv,
            requirement = diagnostic.VarlistEntryRequirement.ALTERNATE,
            alternates = v.alternates
        )
        new_v._id = next(data_mgr.id_number)
        new_v.status = diagnostic.VarlistEntryStatus.INITED
        return new_v

    def edit_request(self, data_mgr, pod):
        """Edit the POD's Varlist prior to query. If any VarlistEntry specifies
        a scalar Z coordinate, insert a VarlistEntry for the full-dimensional 
        variable as an alternate for it, since this function can extract the 
        requested level from the latter to produce the former.
        """
        new_varlist = []
        for v in pod.varlist.iter_contents():
            z_level = v.translation.get_scalar('Z')
            if z_level is None:
                # pass through VE unaltered
                new_varlist.append(v)
                continue
            # existing VarlistEntry queries for 3D slice directly; add a new
            # VE to query for 4D data
            new_v = self.remove_scalar_on_translation(v, data_mgr)
            v.alternates = [[new_v]]

            for vv in v.iter_alternate_entries():
                _log.debug("%s for %s: add translated %s as alternate for %s", 
                    self.__class__.__name__, v.full_name, vv.translation, v.translation)
            new_varlist.append(v)
            new_varlist.append(new_v)
        pod.varlist = diagnostic.Varlist(contents=new_varlist)

    def process(self, var, ds):
        """Determine if level extraction is needed, and return appropriate slice 
        of Dataset if it is.
        """
        _atol = 1.0e-3 # absolute tolerance for floating-point equality

        tv_name = var.name_in_model
        our_z = var.get_scalar('Z')
        if not our_z or not our_z.value:
            _log.debug("Exit %s for %s: no level requested.", 
                self.__class__.__name__, var.full_name)
            return ds
        if 'Z' not in ds[tv_name].cf.dim_axes_set:
            # maybe the ds we received has this level extracted already
            ds_z = ds.cf.get_scalar('Z', tv_name) 
            if ds_z is None or isinstance(ds_z, xr_util.PlacholderScalarCoordinate):
                _log.debug(("Exit %s for %s: %s %s Z level requested but value not "
                    "provided in scalar coordinate information; assuming correct."), 
                    self.__class__.__name__, var.full_name, our_z.value, our_z.units)
                return ds
            else:
                # value (on var.translation) has already been checked by 
                # xr_util.DatasetParser
                _log.debug(("Exit %s for %s: %s %s Z level requested and provided "
                    "by dataset."), 
                    self.__class__.__name__, var.full_name, our_z.value, our_z.units)
                return ds

        # final case: Z coordinate present in data, so actually extract the level
        ds_z = ds.cf.dim_axes(tv_name)['Z']
        if ds_z is None:
            raise TypeError("No Z axis in dataset for %s.", var.full_name)
        try:
            ds_z_value = util.convert_scalar_coord(our_z, ds_z.units)
            ds = ds.sel(
                {ds_z.name: ds_z_value},
                method='nearest', # Allow for floating point roundoff in axis values
                tolerance=_atol,
                drop=False
            )
            _log.info("Extracted %s %s level from Z axis ('%s') of %s.", 
                ds_z_value, ds_z.units, ds_z.name, var.full_name)
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

# ==================================================

class MDTFPreprocessorBase(metaclass=util.MDTFABCMeta):
    """Base class for preprocessing data after it's been fetched, in order to 
    put it into a format expected by PODs. The only functionality implemented 
    here is parsing data axes and CF attributes; all other functionality is 
    provided by :class:`PreprocessorFunctionBase` functions.
    """
    _functions = util.abstract_attribute()

    def __init__(self, data_mgr, pod):
        self.WK_DIR = data_mgr.MODEL_WK_DIR
        self.convention = data_mgr.convention
        self.pod_convention = pod.convention

        # initialize PreprocessorFunctionBase objects
        self.functions = [cls_(data_mgr, pod) for cls_ in self._functions]

    def edit_request(self, data_mgr, pod):
        """Edit POD's data request, based on the child class's functionality. If
        the child class has a function that can transform data in format X to 
        format Y and the POD requests X, this method should insert a 
        backup/fallback request for Y.
        """
        for func in self.functions:
            func.edit_request(data_mgr, pod)

    # arguments passed to xr.open_dataset and xr.open_mfdataset
    open_dataset_kwargs = {
        "engine": "netcdf4",
        "decode_cf": False,     # all decoding done by xr_utils.parse_dataset
        "decode_coords": False, # so disable it here
        "decode_times": False,
        "use_cftime": False
    }
    # arguments passed to xr.to_netcdf
    save_dataset_kwargs = {
        "engine": "netcdf4",
        "format": "NETCDF4" # required by this choice of engine (?)
    }

    def read_one_file(self, var, path_list):
        if len(path_list) != 1:
            raise ValueError(f"{var.full_name}: Expected one file, got {path_list}.")
        _log.debug("xr.open_dataset on %s", path_list[0])
        return xr.open_dataset(
            path_list[0], 
            **self.open_dataset_kwargs
        )

    @abc.abstractmethod
    def read_dataset(self, var):
        pass # return ds

    def clean_encoding(self, ds):
        """Xarray .to_netcdf raises an error if attributes set on a variable have
        the same name as those used in its encoding, even if their values are the
        same. Delete these attributes from the attrs dict prior to writing, after
        checking equality of values.
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
            
        for var in ds.variables.values():
            _clean_dict(var)
        _clean_dict(ds)
        return ds

    def write_dataset(self, var, ds):
        # TODO: remove any netcdf Variables that were present in file (and ds) 
        # but not needed for request
        path_str = util.abbreviate_path(var.dest_path, self.WK_DIR, '$WK_DIR')
        _log.info("    Writing to %s", path_str)
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        _log.debug("xr.Dataset.to_netcdf on %s", var.dest_path)
        ds = self.clean_encoding(ds)
        ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs
            # Currently don't make time unlimited, since data might be static 
            # and we analyze a fixed date range
        )
        ds.close()

    def process(self, var):
        """Top-level wrapper for doing all preprocessing of data files.
        """
        # load dataset
        try:
            ds = self.read_dataset(var)
            ds = xr_util.DatasetParser().parse(ds, var)
        except Exception as exc:
            raise util.DataPreprocessError((f"Error in read/parse data for "
                f"{var.full_name}."), var) from exc
        # execute functions
        for f in self.functions:
            try:
                _log.debug("Preprocess %s: call %s", var.full_name, f.__class__.__name__)
                ds = f.process(var, ds)
            except Exception as exc:
                raise util.DataPreprocessError((f"Preprocessing on {var.full_name} "
                    f"failed at {f.__class__.__name__}."), var) from exc
        # write dataset
        try:
            self.write_dataset(var, ds)
        except Exception as exc:
            raise util.DataPreprocessError((f"Error in writing data for "
                f"{var.full_name}."), var) from exc
        del ds # shouldn't be necessary
        _log.debug("Successful preprocessor exit on %s.", var)


class SingleFilePreprocessor(MDTFPreprocessorBase):
    """A :class:`MDTFPreprocessorBase` for preprocessing model data that is 
    provided as a single netcdf file per variable, for example the sample model
    data.
    """
    def read_dataset(self, var):
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
            _log.debug("xr.open_mfdataset on %d files: %s", 
                len(var.local_data), var.local_data)
            return xr.open_mfdataset(
                var.local_data,
                combine="by_coords",
                # only time-dependent variables and coords are concat'ed:
                data_vars="minimal", coords="minimal",
                compat="identical",  # all non-concat'ed vars, attrs must be the same
                join="exact",        # raise ValueError if non-time dims conflict
                parallel=True,       # use dask
                preprocess=_file_preproc,
                **self.open_dataset_kwargs
            )


# -------------------------------------------------

class SampleDataPreprocessor(SingleFilePreprocessor):
    """A :class:`MDTFPreprocessorBase` intended for use on sample model data
    only. Assumes all data is in one netCDF file and only truncates the date
    range.
    """
    _functions = (
        CropDateRangeFunction, ConvertUnitsFunction, RenameVariablesFunction
    )

class MDTFDataPreprocessor(DaskMultiFilePreprocessor):
    """A :class:`MDTFPreprocessorBase` for general, multi-file data.
    """
    _file_preproc_functions = []
    _functions = (
        CropDateRangeFunction, ConvertUnitsFunction, 
        ExtractLevelFunction, RenameVariablesFunction
    )
