"""Example MDTF diagnostic

This script does a simple diagnostic calculation to illustrate how to adapt code
for use in the MDTF diagnostic framework. The main change is to set input/output
paths, variable names etc. from shell environment variables the framework 
provides, instead of hard-coding them.
"""
from __future__ import print_function
import os
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.json file.
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots


### 1) Loading model data files: ###############################################
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.

# The following command replaces the substrings "{DATADIR}", "{CASENAME}", etc.
# with the values of the corresponding environment variables:
input_path = "{DATADIR}/mon/{CASENAME}.{tas_var}.mon.nc".format(**os.environ)

# command to load the netcdf file
model_dataset = xr.open_dataset(input_path)


### 2) Loading observational data files: #######################################
#
# If your diagnostic uses any model-independent supporting data (eg. reference 
# or observational data) larger than a few kB of text, it should be provided via
# the observational data distribution instead of being included with the source
# code. This data can be in any format: the framework doesn't process it. The 
# environment variable OBS_DATA will be set to a path where the framework has
# copied a directory containing your supplied data.
#
input_path = "{OBS_DATA}/example_tas_means.nc".format(**os.environ)

# command to load the netcdf file
obs_dataset = xr.open_dataset(input_path)
obs_mean_tas = obs_dataset['mean_tas']


### 3) Doing computations: #####################################################
#
# Diagnostics in the framework are intended to work with native output from a
# variety of models. For this reason, variable names should not be hard-coded
# but instead set from environment variables. 
#
tas_var_name = os.environ["tas_var"]
# For safety, don't even assume that the time dimension of the input file is
# named "time":
time_coord_name = os.environ["time_coord"]

# The only computation done here: compute the time average of input data
tas_data = model_dataset[tas_var_name]
model_mean_tas = tas_data.mean(dim = time_coord_name)
# Note that we supplied the observational data as time averages, to save space
# and avoid having to repeat that calculation each time the diagnostic is run.

# Logging relevant debugging or progress information is a good idea. Anything
# your diagnostic prints to STDOUT will be saved to its own log file.
print("Computed time average of {tas_var} for {CASENAME}.".format(**os.environ))


### 4) Saving output data: #####################################################
#
# Diagnostics should write output data to disk to a) make relevant results 
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the 
# directory <WK_DIR>/model/netCDF (created by the framework).
#
out_path = "{WK_DIR}/model/netCDF/temp_means.nc".format(**os.environ)

# write out time averages as a netcdf file
model_mean_tas.to_netcdf(out_path)


### 5) Saving output plots: ####################################################
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
plot_and_save_figure("model", title_string, model_mean_tas)

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
print("Another log message: finished successfully!")
