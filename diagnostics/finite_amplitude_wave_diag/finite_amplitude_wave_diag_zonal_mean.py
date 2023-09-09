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
# 
#   In this section you should summarize the stages of the calculations your 
#   diagnostic performs, and how they translate to the individual source code files 
#   provided in your submission. This will, e.g., let maintainers fixing a bug or 
#   people with questions about how your code works know where to look.
# ================================================================================
#   Required programming language and libraries (not written yet)
# 
#   In this section you should summarize the programming languages and third-party 
#   libraries used by your diagnostic. You also provide this information in the 
#   ``settings.jsonc`` file, but here you can give helpful comments to human 
#   maintainers (eg, "We need at least version 1.5 of this library because we call
#   this function.")
# ================================================================================
#   Required model output variables (not written yet)
# 
#   In this section you should describe each variable in the input data your 
#   diagnostic uses. You also need to provide this in the ``settings.jsonc`` file, 
#   but here you should go into detail on the assumptions your diagnostic makes 
#   about the structure of the data.
# ================================================================================
#   References (not written yet)
# 
#   Here you should cite the journal articles providing the scientific basis for 
#   your diagnostic.
# 
#      Maloney, E. D, and Co-authors, 2019: Process-oriented evaluation of climate
#         and wether forcasting models. BAMS, 100(9), 1665-1686,
#         doi:10.1175/BAMS-D-18-0042.1.
# ================================================================================
import os
import matplotlib
from collections import namedtuple
import socket

from xarray import Dataset

if socket.gethostname() == 'otc':
    matplotlib.use('Agg')  # non-X windows backend
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import netCDF4
import numpy as np
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots
from cartopy import crs as ccrs
from diagnostics.finite_amplitude_wave_diag.gridfill_utils import gridfill_each_level
from hn2016_falwa.xarrayinterface import QGDataset
from hn2016_falwa.oopinterface import QGFieldNHN22, QGFieldNH18
from hn2016_falwa.constant import SCALE_HEIGHT, P_GROUND

# 1) Loading model data files:
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.
load_environ = True
if load_environ:
    uvt_path = os.environ["UVT_FILE"]
    u_var_name = os.environ["U_VAR"]
    v_var_name = os.environ["V_VAR"]
    t_var_name = os.environ["T_VAR"]
    time_coord_name = os.environ["TIME_COORD"]
    plev_name = os.environ["LEV_COORD"]
    lat_name = os.environ["LAT_COORD"]
    lon_name = os.environ["LON_COORD"]
    wk_dir = os.environ["WK_DIR"]
else:
    # iMac path
    uvt_path = f"{os.environ['HOME']}/Dropbox/GitHub/mdtf/MDTF-diagnostics/diagnostics/finite_amplitude_wave_diag/GFDL-CM3_historical_r1i1p1_20050101-20051231_10tslice.nc"
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


# === Define functions ===
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


def compute_from_sampled_data(sampled_dataset):
    # === 2.1) GRIDFILL: Check if any NaN exist. If yes, do gridfill. ===
    num_of_nan = sampled_dataset['ua'].isnull().sum().values
    do_gridfill = True if num_of_nan > 0 else False  # Boolean
    if do_gridfill:
        print("NaN detected in u/v/T field. Do gridfill with poisson solver.")
        gridfill_file_path = "gridfill_{var}.nc"
        args_tuple = [u_var_name, v_var_name, t_var_name]
        for var_name in args_tuple:
            field_at_all_level = xr.apply_ufunc(
                gridfill_each_level,
                *[sampled_dataset[var_name]],
                input_core_dims=(('lat', 'lon'),),
                output_core_dims=(('lat', 'lon'),),
                vectorize=True, dask="allowed")
            field_at_all_level.to_netcdf(gridfill_file_path.format(var=var_name))
            print(f"Finished outputing {var_name} to {gridfill_file_path.format(var=var_name)}")
        print("Finished gridfill")
        gridfill_file_path = gridfill_file_path.format(var="*")
    else:
        gridfill_file_path = uvt_path  # Original file
        print(f"No gridfill is necessary. Continue to work on {gridfill_file_path}")

    # === 2.2) INTERPOLATION: Interpolate onto regular grid for simplicity ===
    gridfilled_dataset = xr.open_mfdataset(gridfill_file_path)
    gridfilled_dataset = gridfilled_dataset.interp(
        coords={lat_name: ylat, lon_name: xlon}, method="linear", kwargs={"fill_value": "extrapolate"})

    # === 2.3) VERTICAL RESOLUTION: determine the maximum pseudo-height this calculation can handle ===
    dz = 1000  # TODO Variable to set earlier?
    hmax = -SCALE_HEIGHT * np.log(gridfilled_dataset[plev_name].min() / P_GROUND)
    kmax = int(hmax // dz) + 1

    # === 2.4) WAVE ACTIVITY COMPUTATION: Compute Uref, FAWA, barotropic components of u and LWA ===
    qgds = QGDataset(
        gridfilled_dataset,
        var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name},
        qgfield=QGFieldNH18,
        qgfield_kwargs={"dz": dz, "kmax": kmax})
    uvtinterp = qgds.interpolate_fields()[['interpolated_u']] \
        .interp(coords={
        "xlon": (lon_name, original_grid[lon_name].data),
        "ylat": (lat_name, original_grid[lat_name].data)})  # No variables needed from this dataset
    refstates = qgds.compute_reference_states()[['uref']].interp(coords={
        "ylat": (lat_name, original_grid[lat_name].data)})
    # TODO: determine whether to interpolate back to plev grid
    lwadiags = qgds.compute_lwa_and_barotropic_fluxes()[['lwa_baro', 'u_baro', 'lwa']] \
        .interp(coords={
        "xlon": (lon_name, original_grid[lon_name].data),
        "ylat": (lat_name, original_grid[lat_name].data)})
    output_dataset = xr.Dataset(data_vars={
        'zonal_mean_u': uvtinterp.interpolated_u.mean(axis=-1),
        'uref': refstates.uref,
        'zonal_mean_lwa': lwadiags.lwa.mean(axis=-1),
        'lwa_baro': lwadiags.lwa_baro,
        'u_baro': lwadiags.u_baro})
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


def plot_finite_amplitude_wave_diagnostics(seasonal_average_data, title_str, plot_path):
    cmap = "jet"
    fig = plt.figure(figsize=(9, 12))
    fig.suptitle(title_str)
    # *** Zonal mean U ***
    ax1 = fig.add_subplot(3, 2, 1)
    fig1 = ax1.contourf(
        original_grid['lat'], np.arange(0, 1000 * 33, 1000),
        seasonal_average_data.zonal_mean_u,
        30, cmap=cmap)
    fig.colorbar(fig1, ax=ax1)
    ax1.set_title('zonal mean U')
    ax1.set_xlim([-80, 80])

    # *** FAWA ***
    ax3 = fig.add_subplot(3, 2, 3)
    fig3 = ax3.contourf(
        original_grid['lat'], np.arange(0, 1000 * 33, 1000),
        seasonal_average_data.zonal_mean_lwa,
        30, cmap=cmap)
    fig.colorbar(fig3, ax=ax3)
    ax3.set_title('zonal mean LWA')
    ax3.set_xlim([-80, 80])

    # *** Uref ***
    ax2 = fig.add_subplot(3, 2, 5)
    fig2 = ax2.contourf(
        original_grid['lat'], np.arange(0, 1000 * 33, 1000),
        seasonal_average_data.uref,
        30, cmap=cmap)
    fig.colorbar(fig2, ax=ax2)
    ax2.set_title('zonal mean Uref')
    ax2.set_xlim([-80, 80])

    # *** U baro ***
    ax5 = fig.add_subplot(3, 2, 2, projection=ccrs.PlateCarree(180))
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
    ax4 = fig.add_subplot(3, 2, 4, projection=ccrs.PlateCarree(180))
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
    ax6 = fig.add_subplot(3, 2, 6, projection=ccrs.PlateCarree(180))
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
    # plt.show()
    plt.savefig(plot_path, bbox_inches='tight')


# === 3) Saving output data ===
# Diagnostics should write output data to disk to a) make relevant results
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the
# directory <WK_DIR>/model/netCDF (created by the framework).

# *** Produce data by season, daily ***
if __name__ == '__main__':
    season_dict = {"DJF": [1, 2, 12], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}
    # season_dict = {"DJF": [1, 2, 12]}
    out_paths = {key: f"{wk_dir}/intermediate_{key}.nc" for key, value in season_dict.items()}
    for season in season_dict:
        selected_months = season_dict.get(season)
        plot_path = f"FAWA_Diag_{season}.eps"
        # plot_path = "{WK_DIR}/{model_or_obs}/PS/example_{model_or_obs}_plot.eps"
        sampled_dataset = model_dataset.sel(
            time=model_dataset.time.dt.month.isin(selected_months)) \
            .resample(time="1D").mean(dim="time")
        intermediate_dataset: xr.Dataset = compute_from_sampled_data(sampled_dataset)
        out_path = out_paths[season]  # TODO set it
        intermediate_dataset.to_netcdf(out_path)
        print(f"Finished outputing intermediate dataset: {out_path}")
        seasonal_avg_data = time_average_processing(intermediate_dataset)
        plot_finite_amplitude_wave_diagnostics(
            seasonal_avg_data,
            title_str=f'Finite-amplitude diagnostic plots for {season}',
            plot_path=plot_path)
        print(f"Finishing outputting {plot_path}.")
    print("Finish the whole process")


    # === 4) Saving output plots (TODO not yet finished) ===
    #
    # Plots should be saved in EPS or PS format at <WK_DIR>/<model or obs>/PS
    # (created by the framework). Plots can be given any filename, but should have
    # the extension ".eps" or ".ps". To make the webpage output, the framework will
    # convert these to bitmaps with the same name but extension ".png".

    # Define a python function to make the plot, since we'll be doing it twice and
    # we don't want to repeat ourselves.

    def plot_and_save_figure(model_or_obs, title_string, final_dataset):
        """
        Args:
            model_or_obs(str): shall either be 'model' or 'obs_data'
            title_string(str): title of the main plot
            final_dataset: processed dataset (mean already taken)
        """
        # initialize the plot
        plt.figure(figsize=(12, 6))
        plot_axes = plt.subplot(1, 1, 1)
        # actually plot the data (makes a lat-lon colormap)
        final_dataset.plot(ax=plot_axes)
        plot_axes.set_title(title_string)
        # save the plot in the right location
        plot_path = "{WK_DIR}/{model_or_obs}/PS/example_{model_or_obs}_plot.eps".format(
            model_or_obs=model_or_obs, **os.environ
        )
        plt.savefig(plot_path, bbox_inches='tight')


    # end of function

    # set an informative title using info about the analysis set in env vars
    title_string = "{CASENAME}: mean {tas_var} ({FIRSTYR}-{LASTYR})".format(**os.environ)
    # Plot the model data:
    # plot_and_save_figure("model", title_string, model_dataset)

    # 6) Cleaning up:
    #
    # In addition to your language's normal housekeeping, don't forget to delete any
    # temporary/scratch files you created in step 4).
    #
    model_dataset.close()

### 7) Error/Exception-Handling Example ########################################
# nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
# try:
#     nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
# except IOError as error:
#     print(error)
#     print("This message is printed by the example POD because exception-handling is working!")

### 8) Confirm POD executed sucessfully ########################################
# print("Last log message by Example POD: finished successfully!")
