from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
from abc import ABCMeta, abstractmethod
from operator import attrgetter
from src import util
# must import these before xarray in order to register accessors
import cftime
import src.metpy_xr
from src.metpy_xr.units import units
import xarray as xr

@six.python_2_unicode_compatible
class DataPreprocessError(Exception):
    """Exception signaling an error in preprocessing data after it's been 
    fetched, but before any PODs run.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if hasattr(self.dataset, 'name'):
            return 'Data preprocessing error for {}: {}.'.format(
                self.dataset.name, self.msg)
        else:
            return 'Data preprocessing error: {}.'.format(self.msg)

class MDTFPreprocessorBase(six.with_metaclass(ABCMeta)):
    """Base class for preprocessing data after it's been fetched, in order to 
    put it into a format expected by PODs. Functionality implemented here is 
    parsing data axes and joining multiple-file chunked datasets.
    """
    def __init__(self, data_mgr, var):
        self.date_range = data_mgr.date_range
        self.data_freq = data_mgr.data_freq
        self.convention = data_mgr.convention

        self.axes = dict()
        self.v = var
        assert var.remote_data
        if len(var.remote_data) > 1:
            self.files = sorted(
                # should have sorted at end of data query?
                var.remote_data, key=attrgetter('date_range.start')
            )
        else:
            self.files = var.remote_data

    # arguments passed to open_dataset, open_mfdataset, to_netcdf
    netcdf_kwargs = {
        "engine": "netcdf4"
    }
    # arguments passed to open_dataset and open_mfdataset
    open_dataset_kwargs = {
        "decode_coords": True, # parse coords attr
        "decode_cf": False,    # don't decode CF on open: done in parse_cf_wrapper instead
        "decode_times": False, # don't decode time axis into default np.datetime64 objects
        "use_cftime": True     # use cftime library for dates/calendars instead
    }
    open_dataset_kwargs.update(netcdf_kwargs)

    @staticmethod
    def parse_cf_wrapper(ds):
        """Wrapper to pre-process netcdf attributes before calling xarray's
        `decode_cf <http://xarray.pydata.org/en/stable/generated/xarray.decode_cf.html>`__
        method and defining metpy's `accessors 
        <https://unidata.github.io/MetPy/latest/api/generated/metpy.xarray.html>`__.

        Args:
            ds: `xarray.Dataset 
                <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__ 
                instance.

        Returns xarray.Dataset instance with CF attributes parsed and defined.
        """
        def _strip(v):
            return (v.strip() if isinstance(v, str) else v)
        def _strip_dict(d):
            return {_strip(k): _strip(v) for k,v in d.items()}
    
        # Handle previously encountered case where model data attributes 
        # contained whitespace. Strip whitepsace from attrs before calling 
        # decode_cf, since malformed metadata will raise errors.
        ds.attrs = _strip_dict(ds.attrs)
        for var in ds.variables:
            ds[var].attrs = _strip_dict(ds[var].attrs)
        ds = xr.decode_cf(ds)
        return ds.metpy.parse_cf()

    def parse_axes(self, ds):
        """Examine one data file to verify variable and axis info before loading
        the dataset.

        Args:
            path: path to the first netcdf file of the dataset.
        """
        def _find_var_name(ds, expected_name):
            if expected_name in ds.data_vars:
                return expected_name
            # dependent variable wasn't found by its expected name; let's try to
            # find it assuming it's the variable with the largest dimensionality
            # in the file
            dim_lookup = util.MultiMap({var: ds[var].ndim for var in ds.data_vars})
            d_max = util.coerce_from_iter(
                max(dim_lookup.values(), key=util.coerce_from_iter)
            )
            var_name = dim_lookup.inverse_get_(d_max)
            if not isinstance(var_name, str): 
                # returned a set of (!=1) variables with same rank
                raise ValueError("Couldn't determine var")
            else:
                print("\tWarning: Expected {} not found in file, using {}".format(
                    expected_name, var_name))
                return var_name

        def _metpy_lookup(ds, var_name, metpy_attr):
            try:
                return getattr(ds[var_name].metpy, metpy_attr).name
            except AttributeError:
                # metpy couldn't find this axis, maybe because ds doesn't have it
                return None

        var_name = _find_var_name(ds, self.v.name_in_model)
        self.axes['var'] = var_name

        metpy_attrs = {'X':'x', 'Y':'y', 'Z':'vertical', 'T':'time'}
        for k,v in metpy_attrs.items():
            ax_name = _metpy_lookup(ds, var_name, v)
            if ax_name:
                self.axes[k] = ax_name
        # in case data has other axes (eg wavelength) that metpy doesn't handle
        # punt on it for now and label them as W0, W1, ...
        other_axes = set(ds[var_name].dims).difference(list(self.axes.values()))
        for i, ax_name in enumerate(other_axes):
            self.axes['W'+str(i)] = ax_name

    @property
    def time_ax_name(self):
        return self.axes['T']

    def preprocess(self):
        """Top-level wrapper for doing all preprocessing of data files. This is 
        the only user-facing method after instance has been init'ed.
        """
        ds = xr.open_dataset(
            self.files[0].local_path, **self.open_dataset_kwargs
        )
        ds = self.parse_cf_wrapper(ds)
        self.parse_axes(ds)
        self.parse(ds)
        ds.close() # save memory; shouldn't be necessary
        del ds

        if self.v.date_range.is_static:
            # skip date trimming logic for time-independent files
            assert len(self.files) == 1
            ds = xr.open_dataset(
                self.files[0].local_path, **self.open_dataset_kwargs
            )
            ds = self.parse_cf_wrapper(ds)
            ds = self.process_static_dataset(ds)
        else:
            def _preprocess_file(ds):
                ds = self.parse_cf_wrapper(ds)
                return self.process_file(ds)

            ds = xr.open_mfdataset(
                [f.local_path for f in self.files],
                concat_dim=self.time_ax_name,
                combine="by_coords",
                # all non-concat'ed vars, attrs must be the same:
                compat="identical",
                preprocess=_preprocess_file,
                # only time-dependent variables and coords are concat'ed:
                data_vars="minimal", coords="minimal",
                # use dask
                parallel=True,
                # raise ValueError if non-time dims conflict:
                join="exact",
                **self.open_dataset_kwargs
            )
            ds = self.process_dataset(ds)

        ds.to_netcdf(
            path=self.v.dest_path,
            mode='w',
            format="NETCDF3_64BIT",
            **self.netcdf_kwargs
            # don't make time unlimited, since data might be static and we 
            # analyze a fixed date range
        )
        ds.close() # save memory; shouldn't be necessary
        del ds
        # temp files cleaned up by data_manager.tearDown

    # -----------------------------------------------------------------
    # following to be implemented by child classes

    @abstractmethod
    def parse(self, xr_dataset):
        """Additional setup and parsing to be done based on attributes of first 
        file in dataset, before full dataset is processed.
        """
        pass

    @abstractmethod
    def process_static_dataset(self, xr_dataset):
        """Preprocessing to be done for time-independent datasets.
        """
        return xr_dataset

    @abstractmethod
    def process_file(self, xr_dataset):
        """Preprocessing to be done for each individual file of a time-dependent
        dataset, before :meth:`process_dataset` is called.
        """
        return xr_dataset

    @abstractmethod
    def process_dataset(self, xr_dataset):
        """Preprocessing to be done for time-dependent datasets.
        """
        return xr_dataset


class MDTFPreprocessor(MDTFPreprocessorBase):
    """Trims data to requested date range.
    """
    def __init__(self, data_mgr, var):
        super(MDTFPreprocessor, self).__init__(data_mgr, var)
        self.calendar = None
        # HACK for now, until we support cftime in date_range
        self.dt_start_lower = None
        self.dt_start_upper = None
        self.dt_end_upper = None
        self.dt_end_lower = None

    def parse_calendar(self, ds):
        """Parse quantities related to the calendar for time-dependent data.
        In particular, ``date_range`` was set from user input before we knew the 
        model's calendar. HACK here to cast those values into `cftime.datetime 
        <https://unidata.github.io/cftime/api.html#cftime.datetime>`__
        objects so they can be compared with the model data's time axis.

        Args:
            ds: `xarray.Dataset 
                <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__ 
                instance.
        """
        def _cast_to_cftime(dt):
            # HACK to cast python datetime to cftime.datetime with given calendar.
            # NB "tm_mday" is not a typo
            t = dt.timetuple()
            tt = (getattr(t, attr_) for attr_ in 
                ('tm_year', 'tm_mon', 'tm_mday', 'tm_hour', 'tm_min', 'tm_sec'))
            return cftime.datetime(*tt, calendar=self.calendar)

        if 'calendar' in ds.attrs:
            self.calendar = ds.attrs['calendar'].lower().strip()
        elif 'calendar' in self.convention:
            self.calendar = self.convention['calendar']
            print(('\tWarning: no calendar info in file, using convention default'
                ' {}.').format(self.calendar))
        else:
            self.calendar = 'noleap'
            print('\tWarning: no calendar info in file, defaulting to noleap')

        # lower/upper are earliest/latest datetimes consistent with the datetime 
        # we were given, to that precision (eg lower for "2000" would be 
        # jan 1, 2000, and upper would be dec 31).
        self.dt_start_lower = _cast_to_cftime(self.date_range.start.lower)
        self.dt_start_upper = _cast_to_cftime(self.date_range.start.upper)
        self.dt_end_upper = _cast_to_cftime(self.date_range.end.lower)
        self.dt_end_lower = _cast_to_cftime(self.date_range.end.upper)

    def crop_time_axis(self, ds):
        time_ax = ds[self.time_ax_name] # abbreviate
        if time_ax.values[0] > self.dt_start_upper:
            error_str = ("Error: dataset start ({}) is after requested date "
                "range start ({})").format(time_ax.values[0], self.dt_start_upper)
            print('\t' + error_str)
            raise DataPreprocessError(self.v, error_str)
        if time_ax.values[-1] < self.dt_end_lower:
            error_str = ("Error: dataset end ({}) is before requested date "
                "range end ({})").format(time_ax.values[-1], self.dt_end_lower)
            print('\t' + error_str)
            raise DataPreprocessError(self.v, error_str)
        
        print("\ttrimming '{}' of {} from {}-{} to {}".format(
                self.time_ax_name, self.axes['var'],
                time_ax.values[0], time_ax.values[-1], self.date_range
            ))
        kwargs = {
            self.time_ax_name: slice(self.dt_start_lower, self.dt_end_upper)
        }
        return ds.sel(**kwargs)

    # -----------------------------------------------------------------

    def parse(self, ds):
        if 'T' in self.axes:
            self.parse_calendar(ds)

    def process_static_dataset(self, ds):
        return ds

    def process_file(self, ds):
        return ds

    def process_dataset(self, ds):
        return self.crop_time_axis(ds)

