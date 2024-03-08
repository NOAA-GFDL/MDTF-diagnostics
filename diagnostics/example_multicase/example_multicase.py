# MDTF Example Diagnostic POD for Multiple Cases / Experiments
# ================================================================================
#
# This file is part of the Multicase Example Diagnostic POD of the MDTF code
# package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# Example Diagnostic POD
#
#   Last update: Feb-2022
#
#   This example builds upon the single case `example` POD
#   and illustrates how to design and implement a POD that uses multiple
#   model source datasets. These can be the same experiment with different
#   models, two different experiments from the same model, or two different
#   time periods within the same simulation.
#
#   Version & Contact info
#
#   - Version/revision information: version 1.1 (Oct-2022)
#   - Model Development Task Force Framework Team
#
#   Open source copyright agreement
#
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
#   Functionality
#
#   Metadata associated with the different cases are passed from the
#   framework to the POD via a yaml file (case_info.yaml) that the POD reads into a dictionary.
#   The POD iterates over the case entries in the dictionary and opens the input datasets.
#   The `tas` variable is extracted for each case and the time average is taken over the dataset.
#   Anomalies are calculated relative to the global mean and then zonally-averaged. The resulting plot
#   contains one line for each case.
#
#   Required programming language and libraries
#
#     * Python >= 3.10
#     * xarray
#     * matplotlib
#     * intake
#     * yaml
#     * sys
#     * os
#     * numpy
#
#   Required model output variables
#
#     * tas - Surface (2-m) air temperature (CF: air_temperature)
#
#   References
#
#      Maloney, E. D, and Co-authors, 2019: Process-oriented evaluation of climate
#         and wether forcasting models. BAMS, 100(9), 1665-1686,
#         doi:10.1175/BAMS-D-18-0042.1.


# Import modules used in the POD
import os
import matplotlib

matplotlib.use("Agg")  # non-X windows backend

import matplotlib.pyplot as plt
import numpy as np
import intake
import sys
import yaml

# Part 1: Read in the model data
# ------------------------------
# Debugging: remove following line in final PR
# os.environ["WORK_DIR"] = "/Users/jess/mdtf/wkdir/MDTF_output/example_multicase"
work_dir = os.environ["WORK_DIR"]
# Receive a dictionary of case information from the framework
print("reading case_info")
# Remove following line final PR
# os.environ["case_env_file"] = os.path.join(work_dir, "case_info.yml")
case_env_file = os.environ["case_env_file"]
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

cat_def_file = case_info['CATALOG_FILE']
case_list = case_info['CASE_LIST']
# all cases share variable names and dimension coords, so just get first result for each
tas_var = [case['tas_var'] for case in case_list.values()][0]
time_coord = [case['time_coord'] for case in case_list.values()][0]
lat_coord = [case['lat_coord'] for case in case_list.values()][0]
lon_coord = [case['lon_coord'] for case in case_list.values()][0]
# open the csv file using information provided by the catalog definition file
cat = intake.open_esm_datastore(cat_def_file)
# filter catalog by desired variable and output frequency
tas_subset = cat.search(variable_id=tas_var, frequency="day")
# examine assets for a specific file
#tas_subset['CMIP.synthetic.day.r1i1p1f1.day.gr.atmos.r1i1p1f1.1980-01-01-1984-12-31'].df
# convert tas_subset catalog to an xarray dataset dict
tas_dict = tas_subset.to_dataset_dict(
    xarray_open_kwargs={"decode_times": True, "use_cftime": True}
)

# Part 2: Do some calculations (time and zonal means)
# ---------------------------------------------------

tas_arrays = {}

# Loop over cases
for k, v in tas_dict.items():
    # load the tas data for case k
    arr = tas_dict[k][tas_var]

    # take the time mean
    arr = arr.mean(dim=tas_dict[k][time_coord].name)

    # this block shuffles the data to make this single case look more
    # interesting.  ** DELETE THIS ** once we test with real data

    arr.load()
    values = arr.to_masked_array().flatten()
    np.random.shuffle(values)
    values = values.reshape(arr.shape)
    arr.values = values

    # convert to anomalies
    arr = arr - arr.mean()

    # take the zonal mean
    arr = arr.mean(dim=tas_dict[k][lon_coord].name)

    tas_arrays[k] = arr


# Part 3: Make a plot that contains results from each case
# --------------------------------------------------------

# set up the figure
fig = plt.figure(figsize=(12, 4))
ax = plt.subplot(1, 1, 1)

# loop over cases
for k, v in tas_arrays.items():
    v.plot(ax=ax, label=k)

# add legend
plt.legend()

# add title
plt.title("Zonal Mean Surface Air Temperature Anomaly")

# save the plot in the right location
assert os.path.isdir(f"{work_dir}/model/PS"), f'Assertion error: {work_dir}/model/PS not found'
plt.savefig(f"{work_dir}/model/PS/example_multicase_plot.eps", bbox_inches="tight")


# Part 4: Close the catalog files and
# release variable dict reference for garbage collection
# ------------------------------------------------------
cat.close()
tas_dict = None
# Part 5: Confirm POD executed successfully
# ----------------------------------------
print("Last log message by example_multicase POD: finished successfully!")
sys.exit(0)
