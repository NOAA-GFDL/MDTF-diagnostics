"""Functionality for transforming model data into the format expected by PODs
once it's been download to local storage.
"""
import os
import abc
import itertools
from src import util, core, data_model, diagnostic, xr_util
import cftime
import cfunits
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
        if 'T' not in ds.cf.axes:
            _log.debug("Skipping date range crop for <%s>: time-independent.", 
                var.full_name)
            return ds
        t_name = ds.cf.axes['T'][0]
        t_coord = ds[t_name]
        cal = t_coord.attrs['calendar']
        dt_range = var.T.range
        # lower/upper are earliest/latest datetimes consistent with the date we
        # were given, up to the precision that was specified (eg lower for "2000"
        # would be Jan 1, 2000, and upper would be Dec 31).
        dt_start_lower = self.cast_to_cftime(dt_range.start.lower, cal)
        dt_start_upper = self.cast_to_cftime(dt_range.start.upper, cal)
        dt_end_lower = self.cast_to_cftime(dt_range.end.lower, cal)
        dt_end_upper = self.cast_to_cftime(dt_range.end.upper, cal)

        if t_coord.values[0] > dt_start_upper:
            err_str = (f"Error: dataset start ({t_coord.values[0]}) is after "
                f"requested date range start ({dt_start_upper}).")
            _log.error(err_str)
            raise IndexError(var, err_str)
        if t_coord.values[-1] < dt_end_lower:
            err_str = (f"Error: dataset end ({t_coord.values[-1]}) is before "
                f"requested date range end ({dt_end_lower}).")
            _log.error(err_str)
            raise IndexError(var, err_str)
        
        _log.info("Crop date range of <%s> from '%s -- %s' to '%s'.",
                var.full_name,
                t_coord.values[0].strftime('%Y-%m-%d'), 
                t_coord.values[-1].strftime('%Y-%m-%d'), 
                dt_range
            )
        return ds.sel({t_name: slice(dt_start_lower, dt_end_upper)})

class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a single pressure level from a DataSet. Unit conversions of 
    pressure are handled by cfunits, but paramateric vertical coordinates are 
    **not** handled (interpolation is not implemented here.) If the exact level 
    is not provided by the data, KeyError is raised.
    """

    def remove_scalar(self, var):
        """If a VarlistEntry has a scalar_coordinate defined, return a copy to 
        be used as an alternate varaible with that scalar_coordinate removed.
        """
        if len(var.scalar_coords) == 0:
            return None
        elif len(var.scalar_coords) > 1:
            raise NotImplementedError()
        c = var.scalar_coords[0]
        # wraps method in data_model; makes a copy of var
        return var.remove_scalar(
            c.axis, 
            requirement = diagnostic.VarlistEntryRequirement.ALTERNATE,
            alternates=var.alternates
        )

    def edit_request(self, data_mgr, pod):
        new_varlist = []
        for v in pod.varlist.iter_contents():
            z_level = v.get_scalar('Z')
            if z_level is None:
                new_varlist.append(v)
                continue
            # existing VarlistEntry queries for 3D slice directly; add a new
            # VE to query for 4D data
            new_v = self.remove_scalar(v)
            data_mgr.setup_var(pod, new_v)
            v.alternates = [[new_v]]

            print(f'DEBUG: ### add alts for <{new_v.short_format()} {new_v.requirement}>:')
            for vv in new_v.iter_alternate_entries():
                print(f'DEBUG: ### <{vv.short_format()} {vv.requirement}>')
            new_varlist.append(v)
            new_varlist.append(new_v)
        pod.varlist = diagnostic.Varlist(contents=new_varlist)

    def process(self, var, ds):
        z_coord = var.get_scalar('Z')
        if not z_coord or not z_coord.value:
            _log.debug("Skipping level extraction for <%s>: no level requested.",
                var.full_name)
            return ds
        if 'Z' not in ds.cf.axes:
            raise TypeError("No Z axis in data (%s).", ds.cf.axes)
        z_name = ds.cf.axes['Z'][0]
        try:
            _log.info("Extracting %s %s level from Z axis (%s) of <%s>.", 
                z_coord.value, z_coord.units, z_name, var.full_name)
            ds = ds.sel(
                {z_name: z_coord.value},
                method='nearest', # Allow for floating point roundoff in axis values
                tolerance=1.0e-3,
                drop=False
            )
            # rename dependent variable
            return ds.rename({var.translation.name: var.name})
        except KeyError:
            # ds.sel failed; level wasn't present in coordinate axis
            raise KeyError((f"Z axis '{z_name}' of <{var.full_name}> didn't "
                f"provide requested level = {z_coord.value} {z_coord.units}."))

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
            raise ValueError(f"<{var.full_name}>: Expected one file, got {path_list}.")
        _log.debug("xr.open_dataset on %s", path_list[0])
        return xr.open_dataset(
            path_list[0], 
            **self.open_dataset_kwargs
        )

    @abc.abstractmethod
    def read_dataset(self, var):
        pass # return ds

    def write_dataset(self, var, ds):
        path_str = util.abbreviate_path(var.dest_path, self.WK_DIR, '$WK_DIR')
        _log.info("    Writing to %s", path_str)
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        _log.debug("xr.Dataset.to_netcdf on %s", var.dest_path)
        # need to clear units/calendar attrs on time coord when using cftime,
        # otherwise we throw a ValueError on .to_netcdf
        if 'T' in ds.cf.axes and ds.cf.axes['T']:
            t_coord = ds[ds.cf.axes['T'][0]]
            for attr in ('units', 'calendar'):
                if attr in t_coord.attrs:
                    del t_coord.attrs[attr]
        ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs
            # don't make time unlimited, since data might be static and we 
            # analyze a fixed date range
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
                f"<{var.full_name}>.")) from exc
        # execute functions
        for f in self.functions:
            try:
                _log.debug("Preprocess '%s': call %s", var.full_name, f.__class__.__name__)
                ds = f.process(var, ds)
            except Exception as exc:
                raise util.DataPreprocessError((f"Preprocessing on <{var.full_name}> "
                    f"failed at {f.__class__.__name__}.")) from exc
        # write dataset
        try:
            self.write_dataset(var, ds)
        except Exception as exc:
            raise util.DataPreprocessError((f"Error in writing data for "
                f"<{var.full_name}>.")) from exc
        del ds # shouldn't be necessary
        _log.debug("Successful preprocessor exit on <%s>.", var.short_format())


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
    _functions = (CropDateRangeFunction, )

class MDTFDataPreprocessor(DaskMultiFilePreprocessor):
    """A :class:`MDTFPreprocessorBase` for general, multi-file data.
    """
    _file_preproc_functions = []
    _functions = (CropDateRangeFunction, ExtractLevelFunction)
