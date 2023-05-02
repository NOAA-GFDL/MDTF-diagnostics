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

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import intake
import pandas as pd
import sys
import yaml

# Part 1: Read in the model data
# ------------------------------

# Receive a dictionary of case information from the framework. For now, we will
# "fake" a dictionary now with information we are getting from the single case
# POD that is processed by the framework
print("reading case_info")
#os.environ["case_env_file"] = "/Users/jessica/mdtf/MDTF-diagnostics/diagnostics/example_multicase/case_info.yaml"
os.environ["case_env_file"] = "/local2/home/mdtf/MDTF-diagnostics/diagnostics/example_multicase/case_info.yaml"
case_env_file = os.environ["case_env_file"]
assert(os.path.isfile(case_env_file))
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Sample case_info template ingested from yaml file ('case_info.yaml')
# case_info = {
#    "CASENAME": {
#        "NAME": os.environ["CASENAME"],
#        "TAS_FILE": os.environ["TAS_FILE"],
#        "tas_var": os.environ["tas_var"],
#        "time_coord": os.environ["time_coord"],
#        "lon_coord": os.environ["lon_coord"],
#    },
#    "CASENAME1": {
#        "NAME": os.environ["CASENAME"],
#        "TAS_FILE": os.environ["TAS_FILE"],
#        "tas_var": os.environ["tas_var"],
#        "time_coord": os.environ["time_coord"],
#        "lon_coord": os.environ["lon_coord"],
#    },
# }

#os.environ['CATALOG_FILE'] = \
#    '/Users/jessica/mdtf/MDTF-diagnostics/tools/catalog_builder/examples/cmip/esm_catalog_IPSL-CM5A2-INCA_historical_r1i1p1f1.csv'
os.environ['CATALOG_FILE'] = '/nbhome/jml/esm_catalog_IPSL-CM5A2-INCA_historical_r1i1p1f1.csv'
os.environ['CATALOG_DEF_FILE'] = '/nbhome/jml/esm_catalog_IPSL-CM5A2-INCA_historical_r1i1p1f1.json'
cat_file = os.environ['CATALOG_FILE']
cat_def_file = os.environ['CATALOG_DEF_FILE']
# open the csv file using information provided by the catalog definition file
cat = intake.open_esm_datastore(cat_def_file)

#for case_dict in case_info.values():
#    date_range.append(pd.datetime(case_dict['ENDDATE'])-case_dict['STARTDATE'])
tas_files = [case_dict["TAS_FILE"] for case_dict in case_info.values()]
# all cases share variable names, so just get first entry
tas_var = [case_dict["tas_var"] for case_dict in case_info.values()][0]
# filter data by variable and frequency
data_subset = cat.search(
    frequency="day",
    variable_id=tas_var
)

# Loop over cases and load datasets into a separate dict
model_datasets = dict()
    #ds = xr.open_dataset(case_dict["TAS_FILE"], use_cftime=True)
   # model_datasets[case_name] = ds
    #print(ds)

# Part 2: Do some calculations (time and zonal means)
# ---------------------------------------------------

tas_arrays = {}

# Loop over cases

for k, v in case_info.items():
    # take the time mean
    arr = model_datasets[k][case_info[k]["tas_var"]]
    arr = arr.mean(dim=case_info[k]["time_coord"])

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
    arr = arr.mean(dim=case_info[k]["lon_coord"])

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
work_dir = os.environ["WK_DIR"]
assert os.path.isdir(f"{work_dir}/model/PS")
plt.savefig(f"{work_dir}/model/PS/example_model_plot.eps", bbox_inches="tight")


# Part 4: Clean up and close open file handles
# --------------------------------------------

_ = [x.close() for x in model_datasets.values()]


# Part 5: Confirm POD executed sucessfully
# ----------------------------------------
print("Last log message by example_multicase POD: finished successfully!")
sys.exit(0)
