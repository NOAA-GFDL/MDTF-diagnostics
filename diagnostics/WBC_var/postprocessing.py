import numpy as np
import xarray as xr
import warnings

# =============================================================================
# Function: Normalize Metadata Only
# =============================================================================
def normalize_metadata_global(ds, target_var='zos'):
    """
    Renames coordinates and variables.
    [Fixed] Manually reconstructs datetime64 index to preserve data length (1872).
    """
    # 1. Rename Coordinates
    rename_dict = {}
    for old, new in [('latitude', 'lat'), ('longitude', 'lon'),
                     ('TLAT', 'lat'), ('TLONG', 'lon'),
                     ('nav_lat', 'lat'), ('nav_lon', 'lon')]:
        if old in ds.coords:
            rename_dict[old] = new

    if rename_dict:
        ds = ds.rename(rename_dict)

    # 2. Time Format (cftime -> datetime64[ns])
    if 'time' in ds.coords:
        # cftime 객체(Object)인지 확인
        if ds['time'].dtype == 'O' or isinstance(ds.indexes['time'], xr.CFTimeIndex):
            try:
                # print(f"  -> Converting time format manually... (Original len: {len(ds['time'])})")

                new_times = []
                for t in ds['time'].values:
                    year = t.year
                    if year == 0:
                        year = 1 # Year 0 -> Year 1 shift

                    new_times.append(pd.Timestamp(year=year, month=t.month, day=t.day, hour=t.hour))

                ds['time'] = np.array(new_times, dtype='datetime64[ns]')


            except Exception as e:
                print(f"  -> Warning: Manual time conversion failed: {e}")

    # 3. Rename Variable to target_var (zos)
    if target_var not in ds:
        if 'adt' in ds:
            print(f"  -> Global Metadata: Renaming 'adt' to '{target_var}'")
            ds = ds.rename({'adt': target_var})
        elif 'sla' in ds:
            print(f"  -> Global Metadata: Renaming 'sla' to '{target_var}'")
            ds = ds.rename({'sla': target_var})
        elif 'SSH' in ds:
            ds = ds.rename({'SSH': target_var})

    # 4. Add Ensemble dimension if missing
    if 'ensemble' not in ds.dims:
        ds = ds.expand_dims(dim={'ensemble': 1})
    #print(ds)
    return ds



def preprocess_data(ds, target_var='zos'):

    # 1. Variable name
    if target_var not in ds:
        if 'SSH' in ds: ds = ds.rename({'SSH': target_var})
        elif 'adt' in ds: ds = ds.rename({'adt': target_var})
        elif 'sla' in ds: pass

    # 2. Extract target variable
    if target_var in ds:
        ds_attrs = ds.attrs
        ds = ds[[target_var]] 
        ds.attrs = ds_attrs

    # 3. Remove time dimension
    if 'time' in ds.dims:
        try: ds = ds.drop_duplicates(dim="time")
        except: pass
        if ds.sizes['time'] > 1:
            _, index = np.unique(ds['time'], return_index=True)
            if len(index) < ds.sizes['time']:
                ds = ds.isel(time=np.sort(index))

    # 4. Remove boundary
    bnds_vars = [v for v in ds.variables if 'bnds' in v or 'bounds' in v]
    if bnds_vars: ds = ds.drop_vars(bnds_vars, errors='ignore')
    for dim_name in ['bnds', 'nbound', 'bounds_dim']:
        if dim_name in ds.dims: ds = ds.drop_dims(dim_name, errors='ignore')

    # 5. Unified coordiante
    rename_dict = {}
    for old, new in [('latitude', 'lat'), ('longitude', 'lon'), 
                     ('TLAT', 'lat'), ('TLONG', 'lon'),
                     ('nav_lat', 'lat'), ('nav_lon', 'lon')]:
        if old in ds.coords: rename_dict[old] = new
    if rename_dict: ds = ds.rename(rename_dict)

    # 6. Change units (m -> cm)
    # Check max value instead of mean to avoid near-zero anomalies
    if target_var in ds:
        units = ds[target_var].attrs.get('units', '')
        is_meter = False
        
        if units in ['m', 'meter', 'meters']:
            is_meter = True
        else:
            try:
                subset = ds[target_var].isel(time=0)
                max_val = np.nanmax(np.abs(subset.compute().values))
                if max_val < 10:
                    is_meter = True
            except:
                pass

        if is_meter:
            ds[target_var] = ds[target_var] * 100
            ds[target_var].attrs['units'] = 'cm'

    # 7. Calendar
    try:
        if hasattr(ds, "convert_calendar"):
            ds = ds.convert_calendar('standard', align_on='date')
    except: pass

    # 8. Anomaly & Trend
    if target_var in ds:
        if 'sla' not in ds:
            clim = ds[target_var].groupby("time.month").mean("time", skipna=True)
            ds['sla'] = ds[target_var].groupby("time.month") - clim
        
        ds['sla'] = remove_linear_trend_vectorized(ds['sla'])
        
    return ds

def remove_linear_trend_vectorized(da):
    if 'time' not in da.dims or da.sizes['time'] < 2: return da
    poly = da.polyfit(dim='time', deg=1, skipna=True)
    fit = xr.polyval(da['time'], poly.polyfit_coefficients)
    return da - fit
