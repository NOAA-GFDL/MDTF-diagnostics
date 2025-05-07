#!/usr/bin/env python
# coding: utf-8

# In[1]:


import netCDF4 as nc
import numpy as np
import xarray as xr
import warnings

import statsmodels.api as sm
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar
from eofs.xarray import Eof


# In[7]:


def smooth_data(t_series, window=12):
    """
    Smooth the input time series using a moving average window.
    Inputs:
    - t_series: Time series data (numpy array)
    - window: Size of the moving average window (default is 12)
    Outputs:
    - t_series_smoothed: Smoothed time series
    """
    t_series_smoothed = np.zeros(int(len(t_series) / window))
    for t in range(int(len(t_series) / window)):
        t_series_smoothed[t] = np.nanmean(t_series[t * window:t * window + window])
    return t_series_smoothed


# In[8]:


def gs_index(dataset, region):
    """
    Calculate Gulf Stream Index (GSI) based on input dataset.
    
    Inputs:
    - dataset: xarray dataset containing sea level anomaly (sla) and other variables,
               with dimensions (ensemble, time, lat, lon).
    - alt: Boolean flag to use an alternative contour value (default is False).
    
    Outputs:
    - dataset: Updated dataset with the following variables added:
        - gsi_lon: Longitudes of GSI locations (ensemble, gsi_points).
        - gsi_lat: Latitudes of GSI locations (ensemble, gsi_points).
        - sla_ts: Time series of SLA at GSI locations (ensemble, time).
        - sla_ts_std: Standard deviation of SLA over time at GSI locations (ensemble, time).
        - gsi_norm: Normalized GSI time series (ensemble, time).
        - gsi_annual: Smoothed annual GSI values (ensemble, year).
    """
    # Initialize lists to store results
    gsi_lon_list, gsi_lat_list = [], []
    sla_ts_list, sla_ts_std_list = [], []
    gsi_norm_list, gsi_annual_list = [], []

    # select the regional boundary for index
    region_bounds = regional_boundary(region)
    ds = dataset.sel(lon=region_bounds["lon"],lat=region_bounds["lat"])

    for ens in range(ds.sizes['ensemble']):
        ens_dataset = ds.isel(ensemble=ens)
        
        #gsi_lon, gsi_lat, _ = get_contour_info(ens_dataset, contour_to_get=max_contour)
        gsi_lat, gsi_lon = new_gsi_index(ens_dataset)
        
        # Calculate SLA time series and standard deviation at GSI locations
        temp = np.full((len(gsi_lon), ens_dataset.sizes['time']), np.nan)
        for t in range(ens_dataset.sizes['time']):
            for i, (lon, lat) in enumerate(zip(gsi_lon, gsi_lat)):
                temp[i, t] = ens_dataset['sla'][t,
                                                np.nanargmin(abs(ens_dataset.lat.data - lat)),
                                                np.nanargmin(abs(ens_dataset.lon.data - lon))]
        sla_ts = np.nanmean(temp, axis=0)
        sla_ts_std = np.nanstd(temp, axis=0)

        # Normalize SLA time series
        gsi_norm = (sla_ts - np.nanmean(sla_ts)) / np.nanstd(sla_ts)

        # Smooth GSI time series (e.g., annual smoothing)
        gsi_annual = smooth_data(gsi_norm)

        # Append results
        gsi_lon_list.append(gsi_lon)
        gsi_lat_list.append(gsi_lat)
        sla_ts_list.append(sla_ts)
        sla_ts_std_list.append(sla_ts_std)
        gsi_norm_list.append(gsi_norm)
        gsi_annual_list.append(gsi_annual)

    # Add calculated GSI variables to the dataset
    dataset['gsi_lon'] = (('ensemble', 'gsi_points'), np.array(gsi_lon_list))
    dataset['gsi_lat'] = (('ensemble', 'gsi_points'), np.array(gsi_lat_list))
    dataset['sla_ts'] = (('ensemble', 'time'), np.array(sla_ts_list))
    dataset['sla_ts_std'] = (('ensemble', 'time'), np.array(sla_ts_std_list))
    dataset['gsi_norm'] = (('ensemble', 'time'), np.array(gsi_norm_list))
    dataset['gsi_annual'] = (('ensemble', 'year'), np.array(gsi_annual_list))

    return dataset


# In[9]:


def new_gsi_index(ds):
# ===== 0. 데이터 불러오기 =====
# NetCDF 파일에 'ssh' 변수와 'time', 'lat', 'lon' 좌표가 있다고 가정합니다.
# 파일 경로와 변수명은 실제 데이터에 맞게 수정하세요.
#ds = xr.open_dataset('path_to_ssh_data.nc')
#data_obs_raw['ssh']= data_obs_raw['zos']

    ssh_raw = ds['zos']
    ssh = ssh_raw
# ===== 1. 월별 평균 SSH에서 기후학적 연주기(월별 평균)를 제거하여 anomaly 계산 =====
# 먼저 각 달(month)에 대한 기후평균을 구한 후 anomaly를 계산합니다.
    clim = ssh.groupby('time.month').mean('time')
    ssh_anom = ssh.groupby('time.month') - clim

# ===== 2. 경도 -70°W ~ -55°W 구간(55~70°W)에서 각 경도별로 시간에 따른 표준편차가 최대인 위도 찾기 =====
# (주의: 많은 자료가 경도를 음수로 표현하므로 -70 ~ -55로 지정합니다)
    std_ssh = ssh_anom.std(dim='time')

# 선택 구간: 경도 -70°W ~ -55°W
#lon_region = std_ssh.lon.where((std_ssh.lon >= -70) & (std_ssh.lon <= -55), drop=True)
#lat_region = std_ssh.lat.where((std_ssh.lat >= 33) & (std_ssh.lat <= 45), drop=True)
#lon_region = std_ssh.lon.where((std_ssh.lon >= 360-70) & (std_ssh.lon <= 360-55), drop=True)
    std_ssh_region = std_ssh
    lons = std_ssh_region.lon.values

    
# 각 경도별로 표준편차가 최대인 위도값을 찾습니다.
    L_max = []
    for lon in lons:
        col = std_ssh_region.sel(lon=lon)
    # argmax는 위도 좌표에 해당하는 인덱스를 반환합니다.
        idx = col.argmax(dim='lat')
        lat_max = float(col.lat[idx])
        L_max.append(lat_max)
    L_max = np.array(L_max)

    

# ===== 3. 기후평균 SSH 자료에서 isoline(동일 SSH 값을 갖는 곡선) 찾기 =====
# "전체적으로" L_max에 가장 가까운 기후평균 SSH isoline을 결정합니다.
# 먼저 전체 기간에 대한 기후평균 SSH를 계산합니다.
    clim_ssh = ssh.mean(dim='time')
    clim_ssh_region = clim_ssh

# 주어진 경도에서 기후평균 SSH의 위도-SSH 프로파일에서, isoline 값 C에 해당하는 위도를 보간으로 구하는 함수
    def get_isoline_lat(lon, C, target_lat=None):
        """
        주어진 경도에서 기후평균 SSH 프로파일(위도 vs SSH)로부터
        isoline 값 C에 해당하는 위도를 찾아 반환합니다.
        만약 여러 교차점이 존재하면, target_lat에 가장 가까운 교차점을 반환합니다.
        """
        
    # 해당 경도의 기후평균 SSH 수직 프로파일 (위도와 SSH 값)
        ssh_profile = clim_ssh_region.sel(lon=lon).values
        lat_profile = clim_ssh_region.lat.values

    # 위도 좌표가 내림차순인 경우 오름차순으로 변환
        if lat_profile[0] > lat_profile[-1]:
            ssh_profile = ssh_profile[::-1]
            lat_profile = lat_profile[::-1]
    
    # SSH 값과 isoline 값 C의 차이를 계산
        diff = ssh_profile - C
    # sign 변화가 있는 위치를 찾음: diff[i]와 diff[i+1]의 부호가 다르면 교차가 있다고 판단
        idxs = np.where(np.diff(np.sign(diff)))[0]
    
        if len(idxs) == 0:
        # 교차점이 없으면 NaN 반환
            return np.nan
    
        candidate_lats = []
        for idx in idxs:
        # 선형 보간을 통해 교차하는 위도 계산
            lat0, lat1 = lat_profile[idx], lat_profile[idx+1]
            diff0, diff1 = diff[idx], diff[idx+1]
            lat_cross = lat0 - diff0 * (lat1 - lat0) / (diff1 - diff0)
            candidate_lats.append(lat_cross)
        candidate_lats = np.array(candidate_lats)
    
        if target_lat is not None:
        # target_lat에 가장 가까운 교차점을 선택
            idx = np.argmin(np.abs(candidate_lats - target_lat))
            return candidate_lats[idx]
        else:
        # target_lat이 주어지지 않으면 첫번째 교차점을 반환
            return candidate_lats[0]
        
# 목적함수: 모든 경도에 대해 isoline에 해당하는 위도와 L_max 사이의 오차(제곱평균)를 최소화하는 isoline 값 C를 찾는다.
    def objective(C):
        errors = []
        for lon, L_m in zip(lons, L_max):
            L_iso = get_isoline_lat(lon, C)
            errors.append((L_iso - L_m) ** 2)
        return np.mean(errors)

# 최적화: isoline 값 C를 -70°W 구역 내 기후평균 SSH 범위 내에서 찾음.
    C_bounds = (np.nanmin(clim_ssh_region.values), np.nanmax(clim_ssh_region.values))
    res = minimize_scalar(objective, bounds=C_bounds, method='bounded')
    C_opt = res.x

# 최적 isoline 값 C_opt를 사용하여 각 경도별로 Mean Gulf Stream Path (위도)를 결정합니다.
    L_path = np.array([get_isoline_lat(lon, C_opt) for lon in lons])

    print("Optimal isoline SSH value (C_opt):", C_opt)
    print("Mean Gulf Stream Path latitudes (per longitude):", L_path)

# ===== 4. 각 월별로 anomaly 자료에서 Mean Gulf Stream Path를 따라 SSH anomaly를 보간하고 평균하여 Gulf Stream Index 계산 =====
# 각 시간(t)와 경도(lon)에 대해, L_path에서의 anomaly 값을 보간합니다.
    def interpolate_anomaly(time_val, lon, lat_target):
    # 주어진 시간와 경도에서의 anomaly 프로파일 (위도에 따른 값)
        profile = ssh_anom.sel(time=time_val, lon=lon).values
        lat_profile = ssh_anom.lat.values
        f = interp1d(lat_profile, profile, bounds_error=False, fill_value="extrapolate")
        return f(lat_target)

# 각 시간마다, 선택한 경도(lon_region)에서의 anomaly를 보간 후 평균합니다.
    gulf_stream_index = []
    times = ssh_anom.time.values
    for t in times:
        anomalies_along_path = []
        for lon, lat_val in zip(lons, L_path):
            anomaly_val = interpolate_anomaly(t, lon, lat_val)
            anomalies_along_path.append(anomaly_val)
        gulf_stream_index.append(np.mean(anomalies_along_path))
    gulf_stream_index = np.array(gulf_stream_index)

# 결과를 DataArray로 변환 (시간 좌표 유지)
    gulf_stream_index_da = xr.DataArray(gulf_stream_index, coords=[ssh_anom.time], dims=["time"])

    return L_path, lons


# In[10]:


def var_magnitude(dataset, gsi_lon, gsi_lat):
    ds = dataset
    std_gsi = np.zeros((len(gsi_lon)))
    std_cm  = np.nanstd(ds.sla,axis=0)
    for x in range(len(gsi_lon)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            #a= np.nanargmin(abs(ds.lat.data - gsi_lat[x]))
            #b= np.nanargmin(abs(ds.lon.data - gsi_lon[x]))
            #a= np.nanargmin(abs(ds.lat - gsi_lat[x]))
            #b= np.nanargmin(abs(ds.lon - gsi_lon[x]))
            #std_gsi[x] = std_cm[np.nanargmin(abs(ds.lat.data - gsi_lat[x])), np.nanargmin(abs(ds.lon.data - gsi_lon[x]))]
            std_gsi[x] = std_cm[np.nanargmin(abs(ds.lat - gsi_lat[x])), np.nanargmin(abs(ds.lon - gsi_lon[x]))]
    mn_std_gsi = np.nanmean(std_gsi)
    return(mn_std_gsi)

def damping_time_scale(acf):
    efold = 1/np.exp(1)
    find_crossing = acf - efold
    damping_t = np.where(np.diff(np.sign(find_crossing)))[0][0]+1
    return(damping_t)


    
def get_acf(t_series):
    """
    Calculate the autocorrelation function (ACF) of a time series.
    Inputs:
    - t_series: Time series data (numpy array)
    Outputs:
    - acf: Autocorrelation function values
    - n_eff: Effective sample size
    - confint: 95% confidence interval value
    """
    acf = sm.tsa.stattools.acf(t_series, adjusted=False, nlags=59)
    if len(np.argwhere(np.diff(np.sign(acf)))) == 0:
        tau = len(acf)
    else:
        tau = int(np.squeeze(np.argwhere(np.diff(np.sign(acf)))[0])) + 1

    confint = acf[1]  # 95% confidence interval

    n_eff = np.zeros(len(t_series))
    for t in range(len(t_series)):
        n_eff[t] = (len(t_series) - t) / tau
    return acf, n_eff, confint


# In[11]:


def gsp_index(dataset, region):
    """
    Calculate the Gulf Stream path variability
    Inputs:
    - dataset: xarray dataset containing sea level anomaly (sla) and other variables, with dimensions (ensemble, time, lat, lon)
    - alt: Boolean flag to use an alternative contour value (default is False).
    Outputs:
    - gsi_lon: Longitudes of the GSI locations, with ensemble as the first dimension.
    - gsi_lat: Latitudes of the GSI locations, with ensemble as the first dimension.
    - sla_ts: Time series of sea level anomalies at GSI locations, with ensemble as the first dimension.
    - sla_ts_std: Standard deviation of sea level anomalies over time at GSI locations, with ensemble as the first dimension.
    - gsi_norm: Normalized GSI time series, with ensemble as the first dimension.
    """

    # REGION에 따라 선택할 범위를 사전으로 정의
    region_bounds = regional_boundary(region)
    ds = dataset.sel(lon=region_bounds["lon"],lat=region_bounds["lat"])

    # Initialize arrays for storing GSI data with ensemble as the first dimension
    alt_gsi_sd_list, acf_list, n_eff_list, confint_list, alt_damp_t_list = [], [], [], [], [] 
    
    for ens in range(dataset.sizes['ensemble']):
        ens_dataset = dataset.isel(ensemble=ens)
        #Figure 3, var magnitude
        alt_gsi_sd = var_magnitude(ens_dataset,ens_dataset['gsi_lon'],ens_dataset['gsi_lat'])

        #Figure 4.  Calculate ACF, number of effective degrees of freedom
        acf, n_eff, confint = get_acf(ens_dataset['gsi_norm'])
        alt_damp_t  = damping_time_scale(acf)

        alt_gsi_sd_list.append(alt_gsi_sd)
        acf_list.append(acf)
        n_eff_list.append(n_eff)
        confint_list.append(confint)
        alt_damp_t_list.append(alt_damp_t)

    # Convert lists to arrays with ensemble as the first dimension
    dataset['alt_gsi_sd'] = (('ensemble'), np.array(alt_gsi_sd_list))
    dataset['acf'] = (('ensemble', 'n_lags'), np.array(acf_list))
    dataset['n_eff'] = (('ensemble', 'time'), np.array(n_eff_list))
    dataset['confint'] = (('ensemble'), np.array(confint_list))
    dataset['alt_damp_t'] = (('ensemble'), np.array(alt_damp_t_list))
    
    return dataset   


# In[12]:


def calc_eofs(array, num_modes=1):
    """
    Calculate Empirical Orthogonal Functions (EOFs) for the input array.
    Inputs:
    - array: xarray DataArray with dimensions (ensemble, time, lat, lon)
    - num_modes: Number of EOF modes to calculate (default is 1)
    Outputs:
    - eofs: EOF patterns
    - pcs: Principal components
    - per_var: Percentage of variance explained by each EOF mode
    """
    if 'lat' in array.dims:
        coslat = np.cos(np.deg2rad(array.coords['lat'].values))
        wgts = np.sqrt(coslat)[..., np.newaxis]
        solver = Eof(array, weights=wgts)
    else:
        solver = Eof(array)
    eofs = np.squeeze(solver.eofs(neofs=num_modes))
    pcs = np.squeeze(solver.pcs(npcs=num_modes, pcscaling=1))
    per_var = solver.varianceFraction()

    # If the total sum of eofs values is negative, flip the sign for both eofs and pcs
    for mode in range(eofs.shape[0]):
        if np.sum(eofs[mode, :]) < 0:
            eofs[mode, :] *= -1
            pcs[:, mode] *= -1
    
    return eofs, pcs, per_var


def lagged_corrs(var_one, var_two, nlags):
    """
    Calculate lagged correlation coefficients (Pearson Correlation)
    Inputs:
    - var_one: First variable in correlation [ensemble, time, lat, lon] of type xarray
    - var_two: Second variable in correlation [ensemble, time, lat, lon] of type xarray (must have same dimensions as var_one)
    - nlags: Number of lags to compute. Computes this number of positive and negative lags.
    Outputs:
    - corr_array: Matrix of correlation coefficients [2*nlags+1, lat, lon]
    """
    lags = np.arange(-nlags, nlags + 1, 1)
    corr_mat = np.zeros((len(lags), var_one.shape[2], var_one.shape[3]))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        for lag in lags:
            var_one_temp = var_one.shift(time=lag)
            corr_mat[lag + nlags, :, :] = xr.corr(var_one_temp, var_two, dim='time')
    corr_array = xr.DataArray(corr_mat, coords={'lag': lags, 'lat': var_one.lat, 'lon': var_two.lon}, dims=['lag', 'lat', 'lon'])
    return corr_array

def eof_crossings(eofs_gsi, per_var_gsi):
    mode_one = np.array([((eofs_gsi.data[0][:-1] * eofs_gsi.data[0][1:]) < 0).sum(),per_var_gsi[0]])
    mode_two = np.array([((eofs_gsi.data[1][:-1] * eofs_gsi.data[1][1:]) < 0).sum(),per_var_gsi[1]])
    mode_three = np.array([((eofs_gsi.data[2][:-1] * eofs_gsi.data[2][1:]) < 0).sum(),per_var_gsi[2]])
    crossings = np.array([mode_one[0],mode_two[0],mode_three[0]])
    vars      = np.array([mode_one[1],mode_two[1],mode_three[1]])
    return(crossings, vars)


def damping_spatial_scale(acf):
    efold = 1/np.exp(1)
    find_crossing = acf - efold
    damping_space = np.where(np.diff(np.sign(find_crossing)))[0][0]+1
    return(damping_space)


# In[13]:


def EOF_index(dataset, region):
    """
    Calculate the Gulf Stream path variability
    Inputs:
    - dataset: xarray dataset containing sea level anomaly (sla) and other variables, with dimensions (ensemble, time, lat, lon)
    - alt: Boolean flag to use an alternative contour value (default is False).
    Outputs:
    - gsi_lon: Longitudes of the GSI locations, with ensemble as the first dimension.
    - gsi_lat: Latitudes of the GSI locations, with ensemble as the first dimension.
    - sla_ts: Time series of sea level anomalies at GSI locations, with ensemble as the first dimension.
    - sla_ts_std: Standard deviation of sea level anomalies over time at GSI locations, with ensemble as the first dimension.
    - gsi_norm: Normalized GSI time series, with ensemble as the first dimension.
    """
    # REGION에 따라 선택할 범위를 사전으로 정의
    bounds = regional_boundary(region)
    ds = dataset.sel(lon=bounds["lon"],lat=bounds["lat"])
    
    # Initialize arrays for storing GSI data with ensemble as the first dimension
    eofs_gsi_list, pcs_gsi_list, per_var_gsi_list, alt_cross_list, alt_var_list, acf_spatial_list, n_eff_spatial_list, confint_spatial_list, alt_damp_s_list = [], [], [], [], [], [], [], [], []

    num_modes = 3
    
    for ens in range(dataset.sizes['ensemble']):
        ens_dataset = dataset.isel(ensemble=ens)
        
        # Calculate EOFS: At GSI array
        sla_gsi = np.zeros((len(ens_dataset.time),len(ens_dataset['gsi_lon'])))
        for t in range(len(ens_dataset.time)):
            for x in range(len(ens_dataset['gsi_lon'])):
                sla_gsi[t,x] = ens_dataset['sla'][t,np.nanargmin(abs(ens_dataset.lat - ens_dataset['gsi_lat'][x])), np.nanargmin(abs(ens_dataset.lon - ens_dataset['gsi_lon'][x]))]
        
        sla_gsi_array = xr.DataArray(sla_gsi,coords = {'time': ens_dataset.time,'lon': ens_dataset['gsi_lat']},dims = ['time', 'gsi_points'])

        eofs_gsi, pcs_gsi, per_var_gsi = calc_eofs(sla_gsi_array,num_modes)

#  Variance explained by the EOF1 along the Gulf Stream path (≃ Gulf Stream Index)
        alt_cross, alt_var   = eof_crossings(eofs_gsi, per_var_gsi)

# Spatial scale of the Gulf Stream path variability
        acf_spatial, n_eff_spatial, confint_spatial = get_acf(np.nanmean(sla_gsi,axis=0))
        alt_damp_s = damping_spatial_scale(acf_spatial)


        eofs_gsi_list.append(eofs_gsi)
        pcs_gsi_list.append(pcs_gsi)
        per_var_gsi_list.append(per_var_gsi)
        alt_cross_list.append(alt_cross)
        alt_var_list.append(alt_var)
        acf_spatial_list.append(acf_spatial)
        n_eff_spatial_list.append(n_eff_spatial)
        confint_spatial_list.append(confint_spatial)
        alt_damp_s_list.append(alt_damp_s)

        
        #print(alt_cross_list, alt_var_list, acf_spatial_list, n_eff_spatial_list, confint_spatial_list, alt_damp_s_list)
        
    # Convert lists to arrays with ensemble as the first dimension
    dataset['eofs_gsi'] = (('ensemble','mode','gsi_points'), np.array(eofs_gsi_list))
    dataset['pcs_gsi'] = (('ensemble','time','mode'), np.array(pcs_gsi_list))
    dataset['per_var_gsi'] = (('ensemble','gsi_points'), np.array(per_var_gsi_list))
    dataset['alt_cross'] = (('ensemble','mode'), np.array(alt_cross_list))
    dataset['alt_var'] = (('ensemble','mode'), np.array(alt_var_list))
    dataset['acf_spatial'] = (('ensemble','gsi_points'), np.array(acf_spatial_list))
    dataset['n_eff_spatial'] = (('ensemble','gsi_points'), np.array(n_eff_spatial_list))
    dataset['confint_spatial'] = (('ensemble'), np.array(confint_spatial_list))
    dataset['alt_damp_s'] = (('ensemble'), np.array(alt_damp_s_list))
    
    
    return dataset   


# In[14]:


def regional_boundary(region):
    # REGION에 따라 선택할 범위를 사전으로 정의
    region_bounds = {
        "gulf": {"lon": slice(360-70, 309),"lat": slice(33, 42)},
        "kuroshio": {"lon": slice(145, 157),"lat": slice(31, 45)},
        "australia": {"lon": slice(157, 168), "lat": slice(-40, -30)},
        "agulhas": {"lon": slice(25, 36), "lat": slice(-45, -37)},
        "brazil": {"lon": slice(360-45, 360-30),"lat": slice(-44, -33)},
        }

    return region_bounds[region]


# In[16]:


def region_define(region):
    region_bounds = {
        "gulf": {"lon": slice(270, 315), "lat": slice(32, 46)},
        "kuroshio": {"lon": slice(133, 160), "lat": slice(31, 43)},
        "australia": {"lon": slice(145, 180), "lat": slice(-38, -23)},
        "agulhas": {"lon": slice(18, 42), "lat": slice(-46, -35)},
        "brazil": {"lon": slice(360-60, 360-15), "lat": slice(-49, -32)},
    }
    return region_bounds[region]

def current_name(region):
    region_bounds = {
        "gulf": 'Gulf Stream',
        "kuroshio": 'Kuroshio Current',
        "australia": 'East Australia Current',
        "agulhas": 'Agulhas Current',
        "brazil": 'North Brazil Current',
    }
    return region_bounds[region]

def alias_name(region):
    region_bounds = {
        "gulf": 'GSI',
        "kuroshio": 'KCI',
        "australia": 'EACI',
        "agulhas": 'ACI',
        "brazil": 'NBCI',
     }
    return region_bounds[region]
   


# In[27]:


def model_resolution(region):
    region_bounds = {
        "CESM1": '~0.1°',
        "EC-Earth3P": '~0.25°',
        "ECMWF-IFS": '~0.25°',
        "HadGEM3-GC31": '~0.08°',
     }
    return region_bounds[region]

