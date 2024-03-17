# Finite-amplitude Rossby wave POD
# ================================================================================
# Calculate finite-amplitude wave diagnostics that quantifies wave-mean flow
# interactions.
#
# Last update: 03/18/2024
# ================================================================================
#   Version & Contact info
# 
#   - Version/revision information: version 1 (09/07/2023)
#   - PI: Clare S. Y. Huang. The University of Chicago. csyhuang@uchicago.edu.
#   - Developer/point of contact (name, affiliation, email): (same as PI)
#   - Other contributors: Christopher Polster (JGU Mainz), Noboru Nakamura (UChicago)
# ================================================================================
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
# ================================================================================
#   Functionality (not written yet)
# ================================================================================
#   Required programming language and libraries (not written yet)
# ================================================================================
#   Required model output variables (not written yet)
# ================================================================================
#   References (not written yet)
# ================================================================================
import os
import gc
import socket
from collections import namedtuple
import matplotlib
from finite_amplitude_wave_diag_utils import convert_hPa_to_pseudoheight, DataPreprocessor, LatLonMapPlotter, \
    HeightLatPlotter

# Commands to load third-party libraries. Any code you don't include that's
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
from typing import Dict
import numpy as np
import xarray as xr  # python library we use to read netcdf files
from falwa.xarrayinterface import QGDataset
from falwa.oopinterface import QGFieldNH18
from falwa.constant import P_GROUND, SCALE_HEIGHT

if socket.gethostname() == 'otc':
    matplotlib.use('Agg')  # non-X windows backend

# 1) Loading model data files:
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.
already_done_gridfill: bool = True
load_environ: bool = (socket.gethostname() == 'otc')
frequency = "1hr"  # TODO: change later

if load_environ:  # otc path
    print(
        f"""
        Start running on OTC. Print out all environment variables:
        {os.environ}
        """)
    wk_dir = os.environ["WK_DIR"]
    uvt_path = f'{os.environ["DATADIR"]}/{os.environ["CASENAME"]}/{frequency}/{os.environ["CASENAME"]}.[uvt]a.{frequency}.nc'
    casename = os.environ["CASENAME"]
    # otc_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/GFDL-CM4.ta.1hr.nc"
else:  # iMac path
    wk_dir = "/Users/claresyhuang/Dropbox/GitHub/hn2016_falwa/github_data_storage"
    uvt_path = f"{os.environ['HOME']}/Dropbox/GitHub/mdtf/MDTF-diagnostics/diagnostics/finite_amplitude_wave_diag/" + \
               "GFDL-CM3_historical_r1i1p1_20050101-20051231_10tslice.nc"
    casename = "GFDL-CM3_historical_r1i1p1"

print(
    f"""
    wk_dir = {wk_dir}
    uvt_path = {uvt_path}
    casename = {casename}
    """
)

# *** Coordinates of input dataset ***
u_var_name = "ua"
v_var_name = "va"
t_var_name = "ta"
time_coord_name = "time"
plev_name = "level"
lat_name = "lat"
lon_name = "lon"

# *** Regular analysis grid defined by developer ***
xlon = np.arange(0, 361, 1.0)
ylat = np.arange(-90, 91, 1.0)
print(f"Use xlon: {xlon}")
print(f"Use ylat: {ylat}")


# 2) Doing computations:
model_dataset = xr.open_mfdataset(uvt_path)  # command to load the netcdf file
firstyr = model_dataset.coords['time'].values[0].year
lastyr = model_dataset.coords['time'].values[-1].year
if model_dataset[plev_name].units == 'Pa':  # Pa shall be divided by 100 to become hPa
    print("model_dataset[plev_name].units == 'Pa'. Convert it to hPa.")
    model_dataset = model_dataset.assign_coords({plev_name: model_dataset[plev_name] // 100})
    model_dataset[plev_name].attrs["units"] = 'hPa'

# === 2.0) Save original grid ===
original_grid = {
    time_coord_name: model_dataset.coords[time_coord_name],
    plev_name: model_dataset.coords[plev_name],
    lat_name: model_dataset.coords[lat_name],
    lon_name: model_dataset.coords[lon_name]}


def compute_from_sampled_data(gridfilled_dataset: xr.Dataset):

    # === 2.3) VERTICAL RESOLUTION: determine the maximum pseudo-height this calculation can handle ===
    dz = 1000  # TODO Variable to set earlier?
    hmax = -SCALE_HEIGHT * np.log(gridfilled_dataset[plev_name].min() / P_GROUND)
    kmax = int(hmax // dz) + 1
    original_pseudoheight = convert_hPa_to_pseudoheight(original_grid[plev_name]).rename("height")

    # === 2.4) WAVE ACTIVITY COMPUTATION: Compute Uref, FAWA, barotropic components of u and LWA ===
    qgds = QGDataset(
        gridfilled_dataset,
        var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name},
        qgfield=QGFieldNH18,
        qgfield_kwargs={"dz": dz, "kmax": kmax})
    gridfilled_dataset.close()
    # Compute reference states and LWA
    qgds.interpolate_fields(return_dataset=False)
    qgds.compute_reference_states(return_dataset=False)
    qgds.compute_lwa_and_barotropic_fluxes(return_dataset=False)
    output_dataset = xr.Dataset(data_vars={
        'uref': qgds.uref,
        'zonal_mean_u': qgds.interpolated_u.mean(axis=-1),
        'zonal_mean_lwa': qgds.lwa.mean(axis=-1),
        'lwa_baro': qgds.lwa_baro,
        'u_baro': qgds.u_baro}).interp(coords={
        "xlon": (lon_name, original_grid[lon_name].data),
        "ylat": (lat_name, original_grid[lat_name].data)})
    return output_dataset


def calculate_covariance(lwa_baro, u_baro):
    """
    Calculate covariance.
    Args:
        lwa_baro: dataset.lwa_baro
        u_baro: dataset.u_baro
    Returns:
        cov_map in dimension of (lat, lon)
    """
    baro_matrix_shape = lwa_baro.data.shape
    flatten_lwa_baro = lwa_baro.data.reshape(baro_matrix_shape[0], baro_matrix_shape[1] * baro_matrix_shape[2])
    flatten_u_baro = u_baro.data.reshape(baro_matrix_shape[0], baro_matrix_shape[1] * baro_matrix_shape[2])
    covv = np.cov(m=flatten_lwa_baro, y=flatten_u_baro, rowvar=False)
    row_cov = np.diagonal(covv, offset=baro_matrix_shape[1] * baro_matrix_shape[2])
    cov_map = row_cov.reshape(baro_matrix_shape[1], baro_matrix_shape[2])
    return cov_map


def time_average_processing(dataset: xr.Dataset):
    SeasonalAverage = namedtuple(
        "SeasonalAverage", [
            "zonal_mean_u",
            "uref",
            "zonal_mean_lwa",
            "lwa_baro",
            "u_baro",
            "covariance_lwa_u_baro"])

    seasonal_avg_zonal_mean_u = dataset.zonal_mean_u.mean(axis=0)
    seasonal_avg_zonal_mean_lwa = dataset.zonal_mean_lwa.mean(axis=0)
    seasonal_avg_uref = dataset.uref.mean(axis=0)
    seasonal_avg_lwa_baro = dataset.lwa_baro.mean(axis=0)
    seasonal_avg_u_baro = dataset.u_baro.mean(axis=0)
    seasonal_covariance_lwa_u_baro = calculate_covariance(lwa_baro=dataset.lwa_baro, u_baro=dataset.u_baro)
    seasonal_avg_data = SeasonalAverage(
        seasonal_avg_zonal_mean_u, seasonal_avg_uref, seasonal_avg_zonal_mean_lwa,
        seasonal_avg_lwa_baro, seasonal_avg_u_baro, seasonal_covariance_lwa_u_baro)
    return seasonal_avg_data


def plot_and_save_figure(seasonal_average_data, analysis_height_array, plot_dir, title_str, season,
                         xy_mask=None, yz_mask=None):
    if xy_mask is None:
        xy_mask = np.zeros_like(seasonal_average_data.u_baro)
        yland, xland = [], []
    else:
        yland, xland = np.where(xy_mask)
    if yz_mask is None:
        yz_mask = np.zeros_like(seasonal_average_data.zonal_mean_u)
    lon_range = np.arange(-180, 181, 60)
    lat_range = np.arange(-90, 91, 30)

    cmap = "jet"

    height_lat_plotter = HeightLatPlotter(figsize=(4, 4), title_str=title_str, xgrid=original_grid['lat'],
                                          ygrid=analysis_height_array, cmap=cmap, xlim=[-80, 80])
    height_lat_plotter.plot_and_save_variable(variable=seasonal_average_data.zonal_mean_u, cmap=cmap,
                                              var_title_str='zonal mean U',
                                              save_path=f"{plot_dir}{season}_zonal_mean_u.png", num_level=30)
    height_lat_plotter.plot_and_save_variable(variable=seasonal_average_data.zonal_mean_lwa, cmap=cmap,
                                              var_title_str='zonal mean LWA',
                                              save_path=f"{plot_dir}{season}_zonal_mean_lwa.png", num_level=30)
    height_lat_plotter.plot_and_save_variable(variable=seasonal_average_data.uref, cmap=cmap,
                                              var_title_str='zonal mean Uref',
                                              save_path=f"{plot_dir}{season}_zonal_mean_uref.png", num_level=30)
    height_lat_plotter.plot_and_save_variable(variable=seasonal_average_data.zonal_mean_u - seasonal_average_data.uref,
                                              cmap=cmap, var_title_str='zonal mean $\Delta$ U',
                                              save_path=f"{plot_dir}{season}_zonal_mean_delta_u.png", num_level=30)

    # Use encapsulated class to plot
    lat_lon_plotter = LatLonMapPlotter(figsize=(6, 3), title_str=title_str, xgrid=original_grid['lon'],
                                       ygrid=original_grid['lat'], cmap=cmap, xland=xland, yland=yland,
                                       lon_range=lon_range, lat_range=lat_range)
    lat_lon_plotter.plot_and_save_variable(variable=seasonal_average_data.u_baro, cmap=cmap, var_title_str='U baro',
                                           save_path=f"{plot_dir}{season}_u_baro.png", num_level=30)
    lat_lon_plotter.plot_and_save_variable(variable=seasonal_average_data.lwa_baro, cmap=cmap, var_title_str='LWA baro',
                                           save_path=f"{plot_dir}{season}_lwa_baro.png", num_level=30)
    lat_lon_plotter.plot_and_save_variable(variable=seasonal_average_data.covariance_lwa_u_baro, cmap="Purples_r",
                                           var_title_str='Covariance between LWA and U(baro)',
                                           save_path=f"{plot_dir}{season}_u_lwa_covariance.png", num_level=30)


# === 3) Saving output data ===
# Diagnostics should write output data to disk to a) make relevant results
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the
# directory <WK_DIR>/model/netCDF (created by the framework).

# *** MAIN PROCESS: Produce data by season, daily ***
model_or_obs: str = "model"  # It can be "model" or "obs"
season_to_months = [
    ("DJF", [1, 2, 12]), ("MAM", [3, 4, 5]), ("JJA", [6, 7, 8]), ("SON", [9, 10, 11])]
intermediate_output_paths: Dict[str, str] = {
    item[0]: f"{wk_dir}/{model_or_obs}/intermediate_{item[0]}.nc" for item in season_to_months}

for season in season_to_months[:1]:
    # Construct data preprocessor
    data_preprocessor = DataPreprocessor(
        wk_dir=wk_dir, xlon=xlon, ylat=ylat, u_var_name=u_var_name, v_var_name=v_var_name, t_var_name=t_var_name,
        plev_name=plev_name, lat_name=lat_name, lon_name=lon_name, time_coord_name=time_coord_name)

    selected_months = season[1]
    plot_dir = f"{wk_dir}/{model_or_obs}/"

    # Do temporal sampling to reduce the data size
    sampled_dataset = model_dataset.where(
        model_dataset.time.dt.month.isin(selected_months), drop=True) \
        .groupby("time.day").mean("time")
    preprocessed_output_path = intermediate_output_paths[season[0]]  # TODO set it
    data_preprocessor.output_preprocess_data(
        sampled_dataset=sampled_dataset, output_path=preprocessed_output_path)
    intermediate_dataset = xr.open_mfdataset(preprocessed_output_path)
    fawa_diagnostics_dataset = compute_from_sampled_data(intermediate_dataset)
    analysis_height_array = fawa_diagnostics_dataset.coords['height'].data
    seasonal_avg_data = time_average_processing(fawa_diagnostics_dataset)

    # === 4) Saving output plots ===
    #
    # Plots should be saved in EPS or PS format at <WK_DIR>/<model or obs>/PS
    # (created by the framework). Plots can be given any filename, but should have
    # the extension ".eps" or ".ps". To make the webpage output, the framework will
    # convert these to bitmaps with the same name but extension ".png".

    # Define a python function to make the plot, since we'll be doing it twice and
    # we don't want to repeat ourselves.

    # set an informative title using info about the analysis set in env vars
    title_string = f"{casename} ({firstyr}-{lastyr}) {season}"
    # Plot the model data:
    plot_and_save_figure(seasonal_avg_data, analysis_height_array, plot_dir=plot_dir, title_str=title_string,
                         season=season[0], xy_mask=data_preprocessor.xy_mask, yz_mask=data_preprocessor.yz_mask)
    print(f"Finishing outputting figures to {plot_dir}.")

    # Close xarray datasets
    sampled_dataset.close()
    intermediate_dataset.close()
    fawa_diagnostics_dataset.close()
    gc.collect()
print("Finish the whole process")
model_dataset.close()

# 6) Cleaning up:
#
# In addition to your language's normal housekeeping, don't forget to delete any
# temporary/scratch files you created in step 4).
# os.system(f"rm -f {wk_dir}/model/gridfill_*.nc")
# os.system(f"rm -f {wk_dir}/model/intermediate_*.nc")

### 7) Error/Exception-Handling Example ########################################
# nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
# try:
#     nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
# except IOError as error:
#     print(error)
#     print("This message is printed by the example POD because exception-handling is working!")

### 8) Confirm POD executed sucessfully ########################################
print("POD Finite-amplitude wave diagnostic (zonal mean) finished successfully!")

