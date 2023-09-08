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
matplotlib.use('Agg') # non-X windows backend
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import netCDF4
import numpy as np
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from diagnostics.finite_amplitude_wave_diag.gridfill_utils import gridfill_each_level
from hn2016_falwa.xarrayinterface import QGDataset
from hn2016_falwa.oopinterface import QGFieldNHN22, QGFieldNH18
from hn2016_falwa.constant import SCALE_HEIGHT, P_GROUND
from hn2016_falwa.xarrayinterface import hemisphere_to_globe


# 1) Loading model data files:
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.
load_environ = False
if load_environ:
    uvt_path = os.environ["UVT_FILE"]
    u_var_name = os.environ["U_VAR"]
    v_var_name = os.environ["V_VAR"]
    t_var_name = os.environ["T_VAR"]
    time_coord_name = os.environ["TIME_COORD"]
    plev_name = os.environ["LEV_COORD"]
    lat_name = os.environ["LAT_COORD"]
    lon_name = os.environ["LON_COORD"]
else:
    # iMac path
    uvt_path = f"{os.environ['HOME']}/Dropbox/GitHub/mdtf/MDTF-diagnostics/diagnostics/finite_amplitude_wave_diag/GFDL-CM3_historical_r1i1p1_20050101-20051231_1tslice.nc"
    u_var_name = "ua"
    v_var_name = "va"
    t_var_name = "ta"
    time_coord_name = "time"
    plev_name = "plev"
    lat_name = "lat"
    lon_name = "lon"
# Regular grid
xlon = np.arange(0, 361, 1.5)
ylat = np.arange(-90, 91, 1.5)

# 2) Doing computations:
model_dataset = xr.open_mfdataset(uvt_path)  # command to load the netcdf file

# === 2.0) Save original grid ===
original_grid = {
    time_coord_name: model_dataset.coords[time_coord_name],
    plev_name: model_dataset.coords[plev_name],
    lat_name: model_dataset.coords[lat_name],
    lon_name: model_dataset.coords[lon_name]}

# === 2.1) GRIDFILL: Check if any NaN exist. If yes, do gridfill. ===
num_of_nan = model_dataset['ua'].isnull().sum().values
do_gridfill = True if num_of_nan > 0 else False  # Boolean
if do_gridfill:
    print("NaN detected in u/v/T field. Do gridfill with poisson solver.")
    gridfill_file_path = "gridfill_{var}.nc"
    args_tuple = [u_var_name, v_var_name, t_var_name]
    field_list = []
    for var_name in args_tuple:
        field_at_all_level = xr.apply_ufunc(
            gridfill_each_level,
            *[model_dataset[var_name]],
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
model_dataset.close()

# === 2.2) INTERPOLATION: Interpolate onto regular grid for simplicity ===
gridfilled_dataset = xr.open_mfdataset(gridfill_file_path)
gridfilled_dataset = gridfilled_dataset.interp(
    coords={lat_name: ylat, lon_name: xlon}, method="linear", kwargs={"fill_value": "extrapolate"})
if gridfilled_dataset[plev_name].units == 'Pa':  # Shall divide by 100
    gridfilled_dataset = gridfilled_dataset.assign_coords({plev_name: gridfilled_dataset[plev_name] // 100})
    gridfilled_dataset[plev_name].attrs["units"] = 'hPa'

# === 2.3) VERTICAL RESOLUTION: determine the maximum pseudo-height this calculation can handle ===
dz = 1000  # TODO Variable to set earlier?
hmax = -SCALE_HEIGHT*np.log(gridfilled_dataset[plev_name].min()/P_GROUND)
kmax = int(hmax//dz)+1

# === 2.3) WAVE ACTIVITY COMPUTATION: Compute Uref, FAWA, barotropic components of u and LWA ===
qgds = QGDataset(
    gridfilled_dataset,
    var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name},
    qgfield=QGFieldNH18,
    qgfield_kwargs={"dz": dz, "kmax": kmax})
qgds.interpolate_fields()  # No need to retrieve variables
refstates = qgds.compute_reference_states()['uref']
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()['lwa_baro', 'u_baro']
# TODO:
# RefState has to be interpolated back onto plev-lat grid
# lwadiags has to be interpolated back onto lat-lon grid

"""
New coordinate can also be attached to an existing dimension:

lon_2 = np.array([300, 289, 0, 1])
da.assign_coords(lon_2=("lon", lon_2))
<xarray.DataArray (lon: 4)>
array([0.5488135 , 0.71518937, 0.60276338, 0.54488318])
Coordinates:
  * lon      (lon) int64 358 359 0 1
    lon_2    (lon) int64 300 289 0 1
"""

# === 3) Saving output data (TODO not yet finished) ===
# Diagnostics should write output data to disk to a) make relevant results
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the 
# directory <WK_DIR>/model/netCDF (created by the framework).
out_path = "{WK_DIR}/model/netCDF/temp_means.nc".format(**os.environ)  # TODO set it
lwadiags.to_netcdf(out_path)  # (not done) write out time averages as a netcdf file

# === 4) Saving output plots (TODO not yet finished) ===
#
# Plots should be saved in EPS or PS format at <WK_DIR>/<model or obs>/PS 
# (created by the framework). Plots can be given any filename, but should have 
# the extension ".eps" or ".ps". To make the webpage output, the framework will 
# convert these to bitmaps with the same name but extension ".png".

# Define a python function to make the plot, since we'll be doing it twice and
# we don't want to repeat ourselves.
def plot_and_save_figure(model_or_obs, title_string, dataset):
    # initialize the plot
    plt.figure(figsize=(12,6))
    plot_axes = plt.subplot(1,1,1)
    # actually plot the data (makes a lat-lon colormap)
    dataset.plot(ax = plot_axes)
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
plot_and_save_figure("model", title_string, model_dataset)


### 5) Loading obs data files & plotting obs figures: ##########################
#
# If your diagnostic uses any model-independent supporting data (eg. reference 
# or observational data) larger than a few kB of text, it should be provided via
# the observational data distribution instead of being included with the source
# code. This data can be in any format: the framework doesn't process it. The 
# environment variable OBS_DATA will be set to a path where the framework has
# copied a directory containing your supplied data.
#
# The following command replaces the substring "{OBS_DATA}" with the value of 
# the OBS_DATA environment variable.
input_path = "{OBS_DATA}/example_tas_means.nc".format(**os.environ)

# command to load the netcdf file
obs_dataset = xr.open_dataset(input_path)
obs_mean_tas = obs_dataset['mean_tas']

# Plot the observational data:
title_string = "Observations: mean {tas_var}".format(**os.environ)
plot_and_save_figure("obs", title_string, obs_mean_tas)


### 6) Cleaning up: ############################################################
#
# In addition to your language's normal housekeeping, don't forget to delete any
# temporary/scratch files you created in step 4).
#
model_dataset.close()
obs_dataset.close()


### 7) Error/Exception-Handling Example ########################################
nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
try:
    nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
except IOError as error:
    print(error)
    print("This message is printed by the example POD because exception-handling is working!")


### 8) Confirm POD executed sucessfully ########################################
print("Last log message by Example POD: finished successfully!")
