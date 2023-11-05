# Finite-amplitude Rossby wave POD
# ================================================================================
# Calculate finite-amplitude wave diagnostics that quantifies wave-mean flow
# interactions.
#
# Last update: 09/07/2023
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
from typing import Tuple, Optional

import gridfill
import matplotlib
from matplotlib import gridspec
from collections import namedtuple

if socket.gethostname() == 'otc':
    matplotlib.use('Agg')  # non-X windows backend
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import numpy as np
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots
from cartopy import crs as ccrs
from hn2016_falwa.xarrayinterface import QGDataset
from hn2016_falwa.oopinterface import QGFieldNH18
from hn2016_falwa.constant import P_GROUND, SCALE_HEIGHT


def convert_pseudoheight_to_hPa(height_array):
    """
    Args:
        height_array(np.array): pseudoheight in [m]

    Returns:
        np.array which contains pressure levels in [hPa]
    """
    p_array = P_GROUND * np.exp(- height_array / SCALE_HEIGHT)
    return p_array


def convert_hPa_to_pseudoheight(p_array):
    """
    Args:
        height_array(np.array): pseudoheight in [m]

    Returns:
        np.array which contains pressure levels in [hPa]
    """
    height_array = - SCALE_HEIGHT * np.log(p_array / P_GROUND)
    return height_array




class DataPreprocessor:
    def __init__(
            self, wk_dir, xlon, ylat, u_var_name, v_var_name, t_var_name, plev_name, lat_name, lon_name, time_coord_name):

        self._wk_dir = wk_dir
        self._xlon: np.array = xlon  # user input
        self._ylat: np.array = ylat  # user input
        self._u_var_name: str = u_var_name
        self._v_var_name: str = v_var_name
        self._t_var_name: str = t_var_name
        self._plev_name: str = plev_name
        self._lat_name: str = lat_name
        self._lon_name: str = lon_name
        self._original_plev = None
        self._original_lat = None
        self._original_lon = None
        self._original_time_coord = None
        self._time_coord_name: str = time_coord_name
        self._new_time_coord_name: str = "day"
        self._sampled_dataset = None  # Shall be xarray. Set type later
        self._gridfill_needed: Optional[bool] = None
        self._yz_mask = None
        self._xy_mask = None

    def _save_original_coordinates(self, dataset):
        self._original_plev = dataset.coords[plev_name]
        self._original_lat = dataset.coords[lat_name]
        self._original_lon = dataset.coords[lon_name]

    def _check_if_gridfill_is_needed(self, sampled_dataset):
        num_of_nan = sampled_dataset[self._u_var_name].isnull().sum().values
        if num_of_nan > 0:
            self._gridfill_needed = True
            self._do_save_mask(sampled_dataset)
        else:
            self._gridfill_needed = False

    def _do_save_mask(self, dataset):
        self._yz_mask = dataset[self._u_var_name].isel({self._new_time_coord_name: 0})\
            .to_masked_array().mask.sum(axis=-1).astype(bool)
        self._xy_mask = dataset[self._u_var_name].isel({self._new_time_coord_name: 0})\
            .to_masked_array().mask.sum(axis=0).astype(bool)

    def _save_preprocessed_data(self, dataset, output_path):
        dataset.to_netcdf(output_path)
        dataset.close()
        print(f"Finished outputing preprocessed dataset: {output_path}")

    def _interpolate_onto_regular_grid(self, dataset):
        dataset = dataset.interp(
            coords={self._lat_name: self._ylat, self._lon_name: self._xlon},
            method="linear",
            kwargs={"fill_value": "extrapolate"})
        return dataset

    def _implement_gridfill(self, dataset: xr.Dataset):
        if not self._gridfill_needed:
            print("No NaN values detected. Gridfill not needed. Bypass DataPreprocessor._implement_gridfill.")
            return dataset
        # *** Implement gridfill procedure ***
        print(f"self._gridfill_needed = True. Do gridfill with poisson solver.")
        args_tuple = [self._u_var_name, self._v_var_name, self._t_var_name]
        gridfill_file_path = self._wk_dir + "/gridfill_{var}.nc"
        for var_name in args_tuple:
            field_at_all_level = xr.apply_ufunc(
                gridfill_each_level,
                *[sampled_dataset[var_name]],
                input_core_dims=((self._lat_name, self._lon_name),),
                output_core_dims=((self._lat_name, self._lon_name),),
                vectorize=True, dask="allowed")
            field_at_all_level.to_netcdf(gridfill_file_path.format(var=var_name))
            field_at_all_level.close()
            print(f"Finished outputing {var_name} to {gridfill_file_path.format(var=var_name)}")
        load_gridfill_path = gridfill_file_path.format(var="*")
        return load_gridfill_path

    def output_preprocess_data(self, sampled_dataset, output_path):
        """
        Main procedure executed by this class
        """
        self._save_original_coordinates(sampled_dataset)
        self._check_if_gridfill_is_needed(sampled_dataset)
        gridfill_path = self._implement_gridfill(sampled_dataset)
        gridfilled_dataset = xr.open_mfdataset(gridfill_path)
        dataset = self._interpolate_onto_regular_grid(gridfilled_dataset)  # Interpolate onto regular grid
        gridfilled_dataset.close()
        self._save_preprocessed_data(dataset, output_path)  # Save preprocessed data
        dataset.close()


def gridfill_each_level(lat_lon_field, itermax=1000, verbose=False):
    """
    Fill missing values in lat-lon grids with values derived by solving Poisson's equation
    using a relaxation scheme.

    Args:
        lat_lon_field(np.ndarray): 2D array to apply gridfill on
        itermax(int): maximum iteration for poisson solver
        verbose(bool): verbose level of poisson solver

    Returns:
        A 2D array of the same dimension with all nan filled.
    """
    if np.isnan(lat_lon_field).sum() == 0:
        return lat_lon_field

    lat_lon_filled, converged = gridfill.fill(
        grids=np.ma.masked_invalid(lat_lon_field), xdim=1, ydim=0, eps=0.01,
        cyclic=True, itermax=itermax, verbose=verbose)

    return lat_lon_filled



# 1) Loading model data files:
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.
already_done_gridfill = True
load_environ = (socket.gethostname() == 'otc')
if load_environ:  # otc path
    uvt_path = os.environ["UVT_FILE"]
    u_var_name = os.environ["U_VAR"]
    v_var_name = os.environ["V_VAR"]
    t_var_name = os.environ["T_VAR"]
    time_coord_name = os.environ["TIME_COORD"]
    plev_name = os.environ["LEV_COORD"]
    lat_name = os.environ["LAT_COORD"]
    lon_name = os.environ["LON_COORD"]
    wk_dir = os.environ["WK_DIR"]
else:  # iMac path
    uvt_path = f"{os.environ['HOME']}/Dropbox/GitHub/mdtf/MDTF-diagnostics/diagnostics/finite_amplitude_wave_diag/" + \
               "GFDL-CM3_historical_r1i1p1_20050101-20051231_10tslice.nc"
    u_var_name = "ua"
    v_var_name = "va"
    t_var_name = "ta"
    time_coord_name = "time"
    plev_name = "plev"
    lat_name = "lat"
    lon_name = "lon"
    wk_dir = "/Users/claresyhuang/Dropbox/GitHub/hn2016_falwa/github_data_storage"
# Regular grid defined by developer
xlon = np.arange(0, 361, 1.0)
ylat = np.arange(-90, 91, 1.0)
print(f"Use xlon: {xlon}")
print(f"Use ylat: {ylat}")


# 2) Doing computations:
model_dataset = xr.open_mfdataset(uvt_path)  # command to load the netcdf file
if model_dataset[plev_name].units == 'Pa':  # Pa shall be divided by 100 to become hPa
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
    # dataset.lwa_baro.data.shape # (10, 90, 144)
    # dataset.u_baro.data.shape # (10, 90, 144)
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


def plot_finite_amplitude_wave_diagnostics(seasonal_average_data, analysis_height_array, title_str, plot_path):
    cmap = "jet"
    fig = plt.figure(figsize=(9, 12))
    # create grid for different subplots
    spec = gridspec.GridSpec(
        ncols=2, nrows=3, width_ratios=[1, 2], wspace=0.3, hspace=0.3, height_ratios=[1, 1, 1])
    fig.suptitle(title_str)
    # *** Zonal mean U ***
    ax1 = fig.add_subplot(spec[0])
    fig1 = ax1.contourf(
        original_grid['lat'], analysis_height_array,
        seasonal_average_data.zonal_mean_u,
        30, cmap=cmap)
    fig.colorbar(fig1, ax=ax1)
    ax1.set_title('zonal mean U')
    ax1.set_xlim([-80, 80])

    # *** FAWA ***
    ax3 = fig.add_subplot(spec[2])
    fig3 = ax3.contourf(
        original_grid['lat'], analysis_height_array,
        seasonal_average_data.zonal_mean_lwa,
        30, cmap=cmap)
    fig.colorbar(fig3, ax=ax3)
    ax3.set_title('zonal mean LWA')
    ax3.set_xlim([-80, 80])

    # *** Uref ***
    ax2 = fig.add_subplot(spec[4])
    fig2 = ax2.contourf(
        original_grid['lat'], analysis_height_array,
        seasonal_average_data.uref,
        30, cmap=cmap)
    fig.colorbar(fig2, ax=ax2)
    ax2.set_title('zonal mean Uref')
    ax2.set_xlim([-80, 80])

    # *** U baro ***
    ax5 = fig.add_subplot(spec[1], projection=ccrs.PlateCarree(180))
    ax5.coastlines(color='black', alpha=0.7)
    ax5.set_aspect('auto', adjustable=None)
    fig5 = ax5.contourf(
        original_grid['lon'], original_grid['lat'],
        seasonal_average_data.u_baro,
        30, cmap=cmap)
    ax5.set_xticks(np.arange(0, 361, 60), crs=ccrs.PlateCarree())
    ax5.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    fig.colorbar(fig5, ax=ax5)
    ax5.set_title('U baro')

    # *** LWA baro ***
    ax4 = fig.add_subplot(spec[3], projection=ccrs.PlateCarree(180))
    ax4.coastlines(color='black', alpha=0.7)
    ax4.set_aspect('auto', adjustable=None)
    fig4 = ax4.contourf(
        original_grid['lon'], original_grid['lat'],
        seasonal_average_data.lwa_baro, 30, cmap=cmap)
    ax4.set_xticks(np.arange(0, 361, 60), crs=ccrs.PlateCarree())
    ax4.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    fig.colorbar(fig4, ax=ax4)
    ax4.set_title('LWA baro')

    # *** Covariance between LWA and U ***
    ax6 = fig.add_subplot(spec[5], projection=ccrs.PlateCarree(180))
    ax6.coastlines(color='black', alpha=0.7)
    ax6.set_aspect('auto', adjustable=None)
    fig6 = ax6.contourf(
        original_grid['lon'], original_grid['lat'],
        seasonal_average_data.covariance_lwa_u_baro,
        30, cmap="Purples_r")
    ax6.set_xticks(np.arange(0, 361, 60), crs=ccrs.PlateCarree())
    ax6.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    fig.colorbar(fig6, ax=ax6)
    ax6.set_title('Covariance between LWA and U(baro)')
    plt.tight_layout()
    plt.show()
    plt.savefig(plot_path, bbox_inches='tight')
    plt.savefig(plot_path.replace(".eps", ".png"), bbox_inches='tight')


# === 3) Saving output data ===
# Diagnostics should write output data to disk to a) make relevant results
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the
# directory <WK_DIR>/model/netCDF (created by the framework).

# *** Produce data by season, daily ***
if __name__ == '__main__':
    season_dict = {"DJF": [1, 2, 12], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}
    out_paths = {key: f"{wk_dir}/intermediate_{key}.nc" for key, value in season_dict.items()}

    for season in season_dict:
        # Construct data preprocessor
        data_preprocessor = DataPreprocessor(
            wk_dir=wk_dir, xlon=xlon, ylat=ylat, u_var_name=u_var_name, v_var_name=v_var_name, t_var_name=t_var_name,
            plev_name=plev_name, lat_name=lat_name, lon_name=lon_name, time_coord_name=time_coord_name)

        selected_months = season_dict.get(season)
        plot_path = f"FAWA_Diag_{season}_new.eps"
        # plot_path = "{WK_DIR}/{model_or_obs}/PS/example_{model_or_obs}_plot.eps".format(
        #     model_or_obs=model_or_obs, **os.environ)
        # plt.savefig(plot_path, bbox_inches='tight')

        # Do temporal sampling to reduce the data size
        sampled_dataset = model_dataset.where(
            model_dataset.time.dt.month.isin(selected_months), drop=True) \
            .groupby("time.day").mean("time")
        preprocessed_output_path = out_paths[season]  # TODO set it
        data_preprocessor.output_preprocess_data(
            sampled_dataset=sampled_dataset, output_path=preprocessed_output_path)
        intermediate_dataset = xr.open_mfdataset(preprocessed_output_path)
        fawa_diagnostics_dataset = compute_from_sampled_data(intermediate_dataset)
        analysis_height_array = fawa_diagnostics_dataset.coords['height'].data
        seasonal_avg_data = time_average_processing(fawa_diagnostics_dataset)
        plot_finite_amplitude_wave_diagnostics(
            seasonal_avg_data,
            analysis_height_array,
            title_str=f'Finite-amplitude diagnostic plots for {season}',
            plot_path=plot_path)
        print(f"Finishing outputting {plot_path}.")

        # Close xarray datasets
        sampled_dataset.close()
        intermediate_dataset.close()
        fawa_diagnostics_dataset.close()
        gc.collect()
    print("Finish the whole process")
    model_dataset.close()

    # === 4) Saving output plots (TODO not yet finished) ===
    #
    # Plots should be saved in EPS or PS format at <WK_DIR>/<model or obs>/PS
    # (created by the framework). Plots can be given any filename, but should have
    # the extension ".eps" or ".ps". To make the webpage output, the framework will
    # convert these to bitmaps with the same name but extension ".png".

    # Define a python function to make the plot, since we'll be doing it twice and
    # we don't want to repeat ourselves.

    # set an informative title using info about the analysis set in env vars
    # title_string = "{CASENAME}: mean {tas_var} ({FIRSTYR}-{LASTYR})".format(**os.environ)
    # Plot the model data:
    # plot_and_save_figure("model", title_string, model_dataset)

    # 6) Cleaning up:
    #
    # In addition to your language's normal housekeeping, don't forget to delete any
    # temporary/scratch files you created in step 4).



### 7) Error/Exception-Handling Example ########################################
# nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
# try:
#     nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
# except IOError as error:
#     print(error)
#     print("This message is printed by the example POD because exception-handling is working!")


### 8) Confirm POD executed sucessfully ########################################
# print("Last log message by Example POD: finished successfully!")

