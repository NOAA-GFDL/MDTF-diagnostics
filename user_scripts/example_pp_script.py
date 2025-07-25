"""Example custom preprocessing script to include in framework workflow"""
import os
import sys
import io
import collections
import numpy as np
import pandas as pd
import xarray as xr
import logging
from src.util import datelabel
from src.util import NameSpace
import src.util.json_utils

# Define a log object for debugging
_log = logging.getLogger(__name__)

# check_group_daterange is a helper script used by the preprocessor
# and included in this example custom preprocessing script for testing


def check_group_daterange(group_df: pd.DataFrame) -> pd.DataFrame:
    """Sort the files found for each experiment by date, verify that
    the date ranges contained in the files are contiguous in time and that
    the date range of the files spans the query date range.

    Args:
        group_df (Pandas Dataframe):
        log: log file
    """
    date_col = "date_range"
    try:
        # method throws ValueError if ranges aren't contiguous
        dates_df = group_df.loc[:, ['start_time', 'end_time']]
        date_range_vals = []
        for idx, x in enumerate(group_df.values):
            st = dates_df.at[idx, 'start_time']
            en = dates_df.at[idx, 'end_time']
            date_range_vals.append(datelabel.DateRange(st, en))

        group_df = group_df.assign(date_range=date_range_vals)
        sorted_df = group_df.sort_values(by=date_col)

        # throws ValueError if we don't span the query range
        return sorted_df
    except ValueError:
        logging.error("Non-contiguous or malformed date range in files:", sorted_df["path"].values)
    return pd.DataFrame(columns=group_df.columns)

# rename_dataset_leus is a helper script used by the preprocessor
# and included in this example custom preprocessing script for testing


def rename_dataset_keys(ds: dict, case_list: dict) -> collections.OrderedDict:
    """Rename dataset keys output by ESM intake catalog query to case names`"""

    def rename_key(old_dict: dict, new_dict: collections.OrderedDict, old_key, new_key):
        """Credit:  https://stackoverflow.com/questions/16475384/rename-a-dictionary-key"""
        new_dict[new_key] = old_dict[old_key]

    new_dict = collections.OrderedDict()
    case_names = [c for c in case_list.keys()]
    for old_key, case_d in ds.items():
        (path, filename) = os.path.split(case_d.attrs['intake_esm_attrs:path'])
        rename_key(ds, new_dict, old_key, [c for c in case_names if c in filename][0])
    return new_dict


# unit test for basic functionality
def test_example_script() -> str:
    test_str = "Testing call to example_pp_script"
    print(test_str)
    return test_str


# Main script that works on the xarray dataset that the framework reads from the input data catalog
# The main script mirrors the preprocessor functions that operate separately on each variable in every case in an
# xarray dataset:
# for case_name, case_xr_dataset in cat_subset.items():
#     for v in case_list[case_name].varlist.keys():
#
# Functions adapted from albedofb_calcs.py


def main(xr_ds: xr.Dataset, var: str) -> xr.Dataset:
    # 1. Reshape the data array to convert dimensions to sub-dimensions defined by "coords" and "new_dims"
    # define coordinate and new_dims arrays
    ny = int(xr_ds['time'].sizes['time'] / 365)
    coords = [np.arange(ny), np.arange(365)]
    new_dims = ['year', 'day']

    # Create a pandas MultiIndex
    ind = pd.MultiIndex.from_product(coords, names=new_dims)

    # get the variable data array
    xr_dupe = xr_ds[var].copy()

    # Replace the time index in the DataArray by this new index
    xr_dupe.coords['time'] = ind

    # Convert multi-index to individual dims using DataArray.unstack().
    # This changes dimension order! The new dimensions are at the end.
    xr_dupe = xr_dupe.unstack('time')

    # Permute to restore dimensions
    i = xr_ds[var].dims.index('time')
    dims = list(xr_dupe.dims)

    # insert the new dimension names into the dataset
    for d in new_dims[::-1]:
        dims.insert(i, d)

    for d in new_dims:
        _ = dims.pop(-1)

    xr_dupe = xr_dupe.transpose(*dims)

    # 2. compute the annual mean for each day
    return xr_dupe.mean(dim='year')


# Anything in this block executes if the script is run on its own
# > python3 example_pp_script.py
# The following code reads a data catalog subset into an xarray dataset in a python dictionary
# and computes a time average on reshaped arrays of air temperature (tas) for each case defined in the input
# configuration file


if __name__ == '__main__':
    import intake

    # root directory of this script
    code_root = os.path.dirname(os.path.realpath(__file__))

    # full path to the runtime configuration file
    # config_file = "[path to configuration file]/runtime_config.jsons"
    config_file = "/Users/jess/mdtf/MDTF-diagnostics/templates/runtime_config.jsonc"

    # read the contents of the configuration file into a NameSpace (basically a dict with dot notation)
    with io.open(config_file, 'r', encoding='utf-8') as file_:
        str_ = file_.read()
    json_config = src.util.json_utils.parse_json(str_)
    config = NameSpace.fromDict({k: json_config[k] for k in json_config.keys()})

    # full path to the input data catalog json file
    # data_catalog = "[path_to_catalog]/[catalog_name].json"
    data_catalog = config.DATA_CATALOG

    # open the csv file using information provided by the catalog definition file
    cat = intake.open_esm_datastore(data_catalog)

    # dictionary to hold the data subset returned by the catalog query
    cat_dict = {}

    # create filter lists for POD variables
    cols = list(cat.df.columns.values)

    # Add a date_range column to the catalog dictionary if necessary
    if 'date_range' not in [c.lower() for c in cols]:
        cols.append('date_range')

    # define a variable dictionary with the name, standard_name, realm, output frequency, and any other attributes
    # you want to use in the catalog query
    # note that this example uses daily data
    var_list = {"tas":
                {
                    "standard_name": "air_temperature",
                    "freq": "day",
                    "realm": "atmos"
                }
    }

    # loop through the case list and read in the desired files
    for case_name, case_d in config.case_list.items():
        path_regex = case_name + '*'  # use wild cards to find the appropriate case

        # loop through the variables in the dictionary
        for k, v in var_list.items():
            cat_subset = cat.search(activity_id=case_d.convention,
                                    standard_name=v['standard_name'],
                                    frequency=v['freq'],
                                    realm=v['realm'],
                                    path=path_regex
                                    )
            if cat_subset.df.empty:
                logging.error(f"No assets found for {case_name} in {data_catalog}")

            # Get files in specified date range
            cat_subset.esmcat._df = check_group_daterange(cat_subset.df)

            # convert subset catalog to an xarray dataset dict
            # and concatenate the result with the final dict
            cat_dict = cat_dict | cat_subset.to_dataset_dict(
                progressbar=False,
                xarray_open_kwargs={"decode_times": True,
                                    "use_cftime": True
                                    }
            )

    # rename cat_subset case dict keys to case names
    new_cat = rename_dataset_keys(cat_dict, config.case_list)

    # run the main routine on the xarray dataset
    for case_name, case_xr_dataset in new_cat.items():
        for var_name in var_list.keys():
            xr_ds_new = main(case_xr_dataset, var_name)
            case_xr_dataset = xr_ds_new
    sys.exit(0)
