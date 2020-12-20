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
        if 'T' not in ax_names or var.is_static:
            _log.warning('Tried to crop time axis of time-independent variable.')
            return ds
        dt_range = var.T.range
        # lower/upper are earliest/latest datetimes consistent with the datetime 
        # we were given, to that precision (eg lower for "2000" would be 
        # jan 1, 2000, and upper would be dec 31).
        dt_start_lower = self.cast_to_cftime(dt_range.start.lower, calendar)
        dt_start_upper = self.cast_to_cftime(dt_range.start.upper, calendar)
        dt_end_lower = self.cast_to_cftime(dt_range.end.lower, calendar)
        dt_end_upper = self.cast_to_cftime(dt_range.end.upper, calendar)

        t_name = ax_names['T'] # abbreviate
        time_ax = ds[t_name]  # abbreviate
        if time_ax.values[0] > dt_start_upper:
            error_str = ("Error: dataset start ({}) is after requested date "
                "range start ({})").format(time_ax.values[0], dt_start_upper)
            _log.error(error_str)
            raise util.DataPreprocessError(var, error_str)
        if time_ax.values[-1] < dt_end_lower:
            error_str = ("Error: dataset end ({}) is before requested date "
                "range end ({})").format(time_ax.values[-1], dt_end_lower)
            _log.error(error_str)
            raise util.DataPreprocessError(var, error_str)
        
        _log.info("Crop date range of %s from '%s -- %s' to '%s'.",
                var.name,
                time_ax.values[0].strftime('%Y-%m-%d'), 
                time_ax.values[-1].strftime('%Y-%m-%d'), 
                dt_range
            )
        return ds.sel(**({t_name: slice(dt_start_lower, dt_end_upper)}))

class ExtractLevelFunction(PreprocessorFunctionBase):
    """Extract a single pressure level from a DataSet. Unit conversions of 
    pressure are handled by metpy, but paramateric vertical coordinates are not
    handled (since that would require interpolation.) If the exact level is not
    provided by the data, DataPreprocessError is raised.  

    Args:
        ds: `xarray.Dataset 
            <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__ 
            instance.

    TODO: Properly translate vertical coordinate name and units. If passed 3D
    data, verify that it's for the requested level. Rename variable according to
    convention POD expects.
    """
    def edit_request(self, data_mgr, pod):
        # WARNING: the following is a HACK until we get proper CF conventions
        # implemented in the fieldlist_* files for model definition.
        # HACK is: 
        # name = u_var (4D); should be standard_name
        # standard_name = "u200_var", should be env_var's name
        # "query for 3D slice before 4D" means replace [u_var] -> {alts}
        # with [u200_var] -> [u_var] -> {alts}.
        name_suffix = '_var'
        new_vars = []
        for v in pod.varlist.iter_contents():
            z_level = v.get_scalar('Z')
            if z_level is None:
                new_vars.append(v)
                continue
            # make new VarlistEntry to query for 3D slice directly
            new_name = util.remove_suffix(v.standard_name, name_suffix)
            new_name += str(int(z_level.value))  # TODO: proper units
            if v.standard_name.endswith(name_suffix):
                new_name += name_suffix
            new_v = v.remove_scalar('Z', 
                name=new_name, 
                standard_name=new_name, 
                alternates=[[v]]
            )
            data_mgr.setup_var(pod, new_v)
            v.requirement = diagnostic.VarlistEntryRequirement.ALTERNATE
            v.active = False

            print(f'DEBUG: ### add alts for <{new_v.short_format()} {new_v.requirement}>:')
            for vv in new_v.iter_alternate_entries():
                print(f'DEBUG: ### <{vv.short_format()} {vv.requirement}>')
            new_vars.append(new_v)
            new_vars.append(v)
        pod.varlist = diagnostic.Varlist(contents=new_vars)

    def process(self, var, ds):
        z_coord = var.get_scalar('Z')
        if not z_coord or not z_coord.value:
            return ds
        if 'Z' not in ax_names:
            raise util.DataPreprocessError(("Tried to extract level from data "
                "with no Z axis."))
        z_level = int(z_coord.value)
        try:
            _log.info("Extracting %s hPa level from %s", z_level, ax_names['var'])
            ds = ds.metpy.sel(**({ax_names['Z']: z_level * units.hPa}))
            # rename dependent variable
            return ds.rename({ax_names['var']: ax_names['var']+str(z_level)})
        except KeyError:
            # level wasn't present in coordinate axis
            raise util.DataPreprocessError(("Pressure axis of file didn't provide "
                f"requested level {z_level}."))

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
        self.ax_names = dict()
        self.calendar = None

        self.pod_name = pod.name
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
            raise ValueError(f"{var.name}: Expected one file, got {path_list}.")
        return xr.open_dataset(
            path_list[0], 
            **self.open_dataset_kwargs
        )

    @abc.abstractmethod
    def read_dataset(self, var):
        pass # return ds

    def process_dataset(self, var, ds):
        for f in self.functions:
            ds = f.process(var, ds)
        return ds

    def write_dataset(self, var, ds):
        path_str = util.abbreviate_path(var.dest_path, self.WK_DIR, '$WK_DIR')
        _log.info("    Writing to %s", path_str)
        os.makedirs(os.path.dirname(var.dest_path), exist_ok=True)
        ds.to_netcdf(
            path=var.dest_path,
            mode='w',
            **self.save_dataset_kwargs
            # don't make time unlimited, since data might be static and we 
            # analyze a fixed date range
        )
        ds.close() # save memory; shouldn't be necessary

    def process(self, var, local_files):
        """Top-level wrapper for doing all preprocessing of data files.
        """
        _log.info("    Processing %s", var.name)
        ds = self.read_dataset(var)
        ds = xr_util.parse_dataset(ds)
        ds = self.process_dataset(var, ds)
        self.write_dataset(var, ds)
        del ds # save memory; shouldn't be necessary


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
    _file_preproc_functions = (,)
    _functions = (CropDateRangeFunction, ExtractLevelFunction)
