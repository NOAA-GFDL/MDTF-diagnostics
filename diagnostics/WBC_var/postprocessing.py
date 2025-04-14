import numpy as np
import xarray as xr
import cftime
import datetime
import xesmf as xe
import warnings
import os
import pandas as pd
from scipy.stats import linregress
from scipy.signal import detrend

def read_file(file):
    """
    Read data from netCDF into xarray for analysis
    Inputs:
    - file: Path to netCDF file containing data
    Outputs:
    - dataset: Dataset from file in xarray format
    """
    # 1. Read data
    ds = xr.open_dataset(file)  # Read netcdf data into xarray
    #ds = ds.convert_calendar('standard')
    ds = ds.convert_calendar('standard', align_on='date')
    # 2. Change variable name to 'zos'
    if 'SSH' in ds:
        ds = ds.rename({'SSH': 'zos'})
    if 'adt' in ds:
        ds = ds.rename({'adt': 'zos'})

    # 3. Unit change m -> cm
    if ds['zos'].attrs['units'] in ['m', 'meter', 'meters']:
        ds['zos'] = ds['zos'] * 100
        ds['zos'].attrs['units'] = 'cm'

    # 4. coordinate change lat/lon
    if 'latitude' in ds.coords and 'longitude' in ds.coords:
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})
    if 'TLAT' in ds.coords or 'TLONG' in ds.coords:
        ds = ds.rename({'TLAT': 'lat', 'TLONG': 'lon'})
    #print(ds.zos)
    return ds

def read_ensemble_file(input_path):
    """
    Read and combine multiple ensemble NetCDF files from a directory
    Inputs:
    - input_path: Directory path containing NetCDF files
    Outputs:
    - final_combined_dataset: Combined dataset with an ensemble dimension
    """
    # List all NetCDF files in the specified directory and sort them
    files = sorted([os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.nc')])
    ensemble_size = len(files)
    
    combined_results, dataset= [], []
    
    for i, file in enumerate(files):
        # Step 1: Read each file
        result = read_file(file)
        print(f"Processing file {i+1}/{ensemble_size}: {file}")

        #result = result.assign_coords(time=result.time.dt.to_period('M'))
        result = result.assign_coords(time=result.time.dt.strftime('%Y-%m'))
        # Step 2: Extract zos
        zos_only = result[['zos']]
        
        # Step 3: time 좌표 조정
        # 각 time 값의 day가 16이면 1일 빼서 15일로 변경
        #adjusted_time = xr.where(zos_only['time'].dt.day == 16,
        #                         zos_only['time'] - np.timedelta64(1, 'D'),
        #                         zos_only['time'])
        #zos_only = zos_only.assign_coords(time=adjusted_time)
        
        # ensemble 차원 추가 (각 파일을 ensemble의 한 멤버로 지정)
        zos_only = zos_only.expand_dims(dim={'ensemble': [i]}, axis=0)
        
        # 결과 리스트에 추가
        combined_results.append(zos_only)
        # Step 2: Extract only 'zos' variable and add the ensemble dimension
        #zos_only = result[['zos']].expand_dims(dim={'ensemble': [i]}, axis=0)
        # Step 3: Append the modified zos dataset to the results list
        #combined_results.append(zos_only)
        #print(zos_only)   
    final_combined_dataset = xr.concat(combined_results, dim='ensemble')
    return final_combined_dataset  

def read_ensemble_file2(input_path):
    """
    Read and combine multiple ensemble NetCDF files from a directory
    Inputs:
    - input_path: Directory path containing NetCDF files
    Outputs:
    - final_combined_dataset: Combined dataset with an ensemble dimension
    """
    # List all NetCDF files in the specified directory and sort them
    files = sorted([os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.nc')])
    ensemble_size = len(files)
    
    combined_results, dataset= [], []
    
    for i, file in enumerate(files):
        # Step 1: Read each file
        result = read_file(file)
        print(f"Processing file {i+1}/{ensemble_size}: {file}")
        
        # Step 2: Extract only 'zos' variable and add the ensemble dimension
        #zos_only = result[['zos']].expand_dims(dim={'ensemble': [i]}, axis=0)
        zos_only = result[['zos']]
        # Step 3: Append the modified zos dataset to the results list
        combined_results.append(zos_only)

    
    # Concatenate only the 'zos' variable along the 'ensemble' dimension
    
    final_combined_dataset = xr.concat(combined_results, dim='ensemble')
    #print(final_combined_dataset)
    return final_combined_dataset  

    
    # Now concatenate along 'ensemble' dimension
    #dataset = xr.concat(data_arrays, dim='ensemble')
    
    #dataset = (('ensemble', 'time','lat','lon'), np.array(combined_results))
    #return dataset
    # type of time dimension to datetime type
    #final_combined_dataset['time'] = np.array([np.datetime64(t) for t in final_combined_dataset['time'].values])
    #final_combined_dataset['time'] = np.array([np.datetime64(t, 'ns') for t in final_combined_dataset['time'].values])
    #final_combined_dataset['time'] = pd.to_datetime(final_combined_dataset['time'].values)
    #

def regrid(dataset):
    """
    Regrid the dataset to a 1x1 degree grid using bilinear interpolation
    Inputs:
    - dataset: xarray dataset to be regridded
    Outputs:
    - ds_out: Regridded dataset
    """
    ds = dataset.copy()
    

    
    dr = ds['zos']
    
    #ds_out = xr.Dataset(
    #{
    #    "lat": ("lat", np.arange(-90, 90, 1.0), {"units": "degrees_north"}),
    #    "lon": ("lon", np.arange(0, 360, 1.0), {"units": "degrees_east"}),
    #}
    #)   
    
    #regridder = xe.Regridder(ds, ds_out, "bilinear")
    
    #ds_out = regridder(ds, keep_attrs=True)
    #dr_out = regridder(dr, keep_attrs=True)
    
    #ds_out['zos'] = dr_out

    #return ds_out
    return ds

def remove_climatology(dataset):
    """
    Remove climatological mean (i.e., long-term average) from the dataset
    Inputs:
    - dataset: xarray dataset with dimensions (time, lat, lon)
    Outputs:
    - dataset: xarray dataset with long-term mean removed
    """
    ds = dataset.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
    
    # Calculate sea level anomaly
    ds['sla'] = ds['zos'] - ds['zos'].mean(dim='time', skipna=True)
    return ds

def remove_linear_trend(data):
    """
    Remove linear trend from the dataset along the time dimension
    Inputs:
    - data: xarray DataArray with dimensions (ensemble, time, lat, lon)
    Outputs:
    - trend_removed_data: DataArray with the linear trend removed
    """
    time_num = np.arange(len(data['time']))
    trend_removed_data = xr.full_like(data, fill_value=np.nan)

    # ensemble dimension이 없으면 1로 처리합니다.
    n_ens = data.sizes.get('ensemble', 1)
    
    for ens in range(n_ens):
        for lat in range(data.sizes['lat']):
            for lon in range(data.sizes['lon']):
                # ensemble dimension이 있는 경우와 없는 경우를 분기
                if 'ensemble' in data.dims:
                    y = data.isel(ensemble=ens, lat=lat, lon=lon).values
                else:
                    y = data[:, lat, lon].values

                # 유효한 (NaN이 아닌) 값들의 mask
                mask = np.isfinite(y)
                # 충분한 데이터 포인트(예를 들어 2개 이상)가 없으면 건너뜁니다.
                if mask.sum() < 2:
                    continue

                # 유효한 값들에 대해서만 회귀분석 수행
                slope, intercept, _, _, _ = linregress(time_num[mask], y[mask])
                
                # 회귀추세(기울기와 절편) 제거. (원래는 intercept도 제거하는게 맞습니다.)
                #trend = slope * time_num + intercept
                trend = slope * time_num #+ intercept
                
                # 유효한 값이 있는 위치만 갱신하고, 나머지는 그대로 NaN으로 남김
                y_detrended = np.full_like(y, np.nan)
                y_detrended[mask] = y[mask] - trend[mask]

                if 'ensemble' in data.dims:
                    trend_removed_data[ens, :, lat, lon] = y_detrended
                else:
                    trend_removed_data[:, lat, lon] = y_detrended

    return trend_removed_data
def remove_linear_trend2(data):
    """
    Remove linear trend from the dataset along the time dimension
    Inputs:
    - data: xarray DataArray with dimensions (ensemble, time, lat, lon)
    Outputs:
    - trend_removed_data: DataArray with the linear trend removed
    """
    time_num = np.arange(len(data['time']))
    trend_removed_data = xr.full_like(data, fill_value=np.nan)

    for ens in range(data.sizes.get('ensemble', 1)):
        for lat in range(data.sizes['lat']):
            for lon in range(data.sizes['lon']):
                y = data.isel(ensemble=ens, lat=lat, lon=lon).values if 'ensemble' in data.dims else data[:, lat, lon].values
                if np.isnan(y).all():
                    continue
                slope, intercept, _, _, _ = linregress(time_num, y)
                #trend_removed_data[ens, :, lat, lon] = y - (slope * time_num + intercept) if 'ensemble' in data.dims else trend_removed_data[:, lat, lon]
                trend_removed_data[ens, :, lat, lon] = y - (slope * time_num) if 'ensemble' in data.dims else trend_removed_data[:, lat, lon]
    
    return trend_removed_data

def remove_seasonal_and_trend(dataset, var='sla'):
    """
    Remove monthly climatology (seasonal cycle) and linear trend from the specified variable.
    Inputs:
    - dataset: xarray dataset with dimensions (ensemble, time, lat, lon)
    - var: name of the variable to process (default is 'sla')
    Outputs:
    - xarray dataset with seasonal cycle and trend removed from the specified variable
    """
    ds = dataset.copy()
    #ds = ds.assign_coords(month=pd.to_datetime(ds.temp_time.values).strftime('%m'))
    # 1. 만약 ds.time이 datetime이 아니라면 변환 (예: 문자열일 경우)
    if not np.issubdtype(ds.time.dtype, np.datetime64):
        ds['time'] = pd.to_datetime(ds.time.values)
    
    
    # Step 1: Remove the seasonal cycle (monthly climatology)
    monthly_climatology = ds[var].groupby("time.month").mean("time", skipna=True)
    deseasoned = ds[var].groupby("time.month") - monthly_climatology

    # Step 2: Remove the linear trend along the time dimension
    ds[var] = remove_linear_trend(deseasoned)

    ds['zos'] = remove_linear_trend(ds['zos'])
    return ds

def calculate_time_std(dataset):
    """
    Calculate the standard deviation over the time dimension for the 'sla' variable
    Inputs:
    - dataset: xarray dataset with the 'sla' variable
    Outputs:7
    - dataset: xarray dataset with the standard deviation added as 'sla_std'
    """
    ds = dataset.copy()
    ds['sla_std'] = ds['sla'].std(dim='time', skipna=True)
    
    return ds

def make_msl(dataset):
    """
    Calculate mean sea level over the time dimension
    Inputs:
    - dataset: xarray dataset with dimensions (time, lat, lon)
    Outputs:
    - dataset: xarray dataset with mean sea level added as 'msl'
    """
    ds = dataset.copy()
    ds['msl'] = ds['zos'].mean(dim='time', skipna=True)
    ds['msl_dtrend'] = ds['zos_dtrend'].mean(dim='time', skipna=True)
    return ds

def read_data(data_paths):
    # Read and process ensemble files
    ds = read_ensemble_file(data_paths)
    #ds = regrid(ds)
    ds = remove_climatology(ds)
    ds = remove_seasonal_and_trend(ds)
    #ds = calculate_time_std(ds)
    #ds = make_msl(ds)
    return ds

