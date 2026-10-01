# MDTF Example Diagnostic POD
# ================================================================================
# This script does a simple diagnostic calculation to illustrate how to adapt code
# for use in the MDTF diagnostic framework. The main change is to set input/output
# paths, variable names etc. from shell environment variables the framework 
# provides, instead of hard-coding them.
#
# Below, this script consists of 2 parts: (1) a template of comprehensive header POD
# developers must include in their POD's main driver script, (2) actual code, and 
# (3) extensive in-line comments.
# ================================================================================
# 
# This file is part of the Example Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
# Example Diagnostic POD
# 
#   Last update: 8/1/2020
# 
#   This is a example POD that you can use as a template for your diagnostics.
#  If this were a real POD, you'd place a one-paragraph synopsis of your 
#   diagnostic here (like an abstract). 
# 
#   Version & Contact info
# 
#   Here you should describe who contributed to the diagnostic, and who should be
#   contacted for further information:
# 
#   - Version/revision information: version 1 (5/06/2020)
#   - PI (name, affiliation, email)
#   - Developer/point of contact (name, affiliation, email)
#   - Other contributors
# 
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
# 
#   Functionality
# 
#   In this section you should summarize the stages of the calculations your 
#   diagnostic performs, and how they translate to the individual source code files 
#   provided in your submission. This will, e.g., let maintainers fixing a bug or 
#   people with questions about how your code works know where to look.
# 
#   Required programming language and libraries
# 
#   In this section you should summarize the programming languages and third-party 
#   libraries used by your diagnostic. You also provide this information in the 
#   ``settings.jsonc`` file, but here you can give helpful comments to human 
#   maintainers (eg, "We need at least version 1.5 of this library because we call
#   this function.")
# 
#   Required model output variables
# 
#   In this section you should describe each variable in the input data your 
#   diagnostic uses. You also need to provide this in the ``settings.jsonc`` file, 
#   but here you should go into detail on the assumptions your diagnostic makes 
#   about the structure of the data.
# 
#   References
# 
#   Here you should cite the journal articles providing the scientific basis for 
#   your diagnostic.
# 
#      Maloney, E. D, and Co-authors, 2019: Process-oriented evaluation of climate
#         and wether forcasting models. BAMS, 100(9), 1665-1686,
#         doi:10.1175/BAMS-D-18-0042.1.
#
import os
import matplotlib
matplotlib.use('Agg')  # non-X windows backend
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
import sys

# 1) Loading model data files: ###############################################
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.

# The following command sets input_path to the value of the shell environment
# variable called TAS_FILE. This variable is set by the framework to let the 
# script know where the locally downloaded copy of the data for this variable
# (which we called "tas") is.
input_path = os.environ["TAS_FILE"]
print('TAS_FILE is:', input_path)

# command to load the netcdf file
model_dataset = xr.open_dataset(input_path)

# 2) Doing computations: #####################################################
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
model_mean_tas = tas_data.mean(dim=time_coord_name)
# Note that we supplied the observational data as time averages, to save space
# and avoid having to repeat that calculation each time the diagnostic is run.

# Logging relevant debugging or progress information is a good idea. Anything
# your diagnostic prints to STDOUT will be saved to its own log file.
print("Computed time average of {tas_var} for {CASENAME}.".format(**os.environ))

# 3) Saving output data: #####################################################
#
# Diagnostics should write output data to disk to a) make relevant results 
# available to the user for further use or b) to pass large amounts of data
# between stages of a calculation run as different sub-scripts. Data can be in
# any format (as long as it's documented) and should be written to the 
# directory <WORK_DIR>/model/netCDF (created by the framework).
#
WORK_DIR = os.environ['WORK_DIR']
out_dir = os.path.join(WORK_DIR, "model")
assert os.path.isdir(out_dir), f'{out_dir} not found'
out_path = os.path.join(out_dir, "temp_means.nc")

# write out time averages as a netcdf file
model_mean_tas.to_netcdf(out_path)

# 4) Saving output plots: ####################################################
#
# Plots should be saved in EPS or PS format at <WK_DIR>/<model or obs>/PS 
# (created by the framework). Plots can be given any filename, but should have 
# the extension ".eps" or ".ps". To make the webpage output, the framework will 
# convert these to bitmaps with the same name but extension ".png".

# Define a python function to make the plot, since we'll be doing it twice and
# we don't want to repeat ourselves.


def plot_and_save_figure(model_or_obs, title_string, dataset):
    # initialize the plot
    plt.figure(figsize=(12, 6))
    plot_axes = plt.subplot(1, 1, 1)
    # actually plot the data (makes a lat-lon colormap)
    dataset.plot(ax=plot_axes)
    plot_axes.set_title(title_string)
    # save the plot in the right location
    plot_path = "{WORK_DIR}/{model_or_obs}/PS/example_{model_or_obs}_plot.eps".format(
        model_or_obs=model_or_obs, **os.environ
    )
    plt.savefig(plot_path, bbox_inches='tight')
# end of function

# set an informative title using info about the analysis set in env vars


title_string = "{CASENAME}: mean {tas_var} ({startdate}-{enddate})".format(**os.environ)
# Plot the model data:
plot_and_save_figure("model", title_string, model_mean_tas)

# 5) Loading obs data files & plotting obs figures: ##########################
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
print(input_path)
# command to load the netcdf file
obs_dataset = xr.open_dataset(input_path)
obs_mean_tas = obs_dataset['mean_tas']

# Plot the observational data:
title_string = "Observations: mean {tas_var}".format(**os.environ)
plot_and_save_figure("obs", title_string, obs_mean_tas)


# 6) Cleaning up: ############################################################
#
# In addition to your language's normal housekeeping, don't forget to delete any
# temporary/scratch files you created in step 4).
#
model_dataset.close()
obs_dataset.close()

# 7) Error/Exception-Handling Example ########################################
nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
try:
    nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
except IOError as error:
    print(error)
    print("This message is printed by the example POD because exception-handling is working!")

# 8) Confirm POD executed successfully ########################################
print("Last log message by Example POD: finished successfully!")
sys.exit(0)
