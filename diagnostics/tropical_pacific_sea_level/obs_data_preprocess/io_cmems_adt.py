#!/usr/bin/env python

""" CMEMS Sea Level data IO

Data is downloaded from CMEMS (the original AVISO dataset)

Ftp server is the fastest way to manage download

http://marine.copernicus.eu/services-portfolio/access-to-products/

search for product ID :
SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047 

Need to download the daily data with adt (absolute dynamic topography) available 

The daily data is preprocessed to monthly data in this script

"""

import xarray as xr
import numpy as np
import os


def scantree(path):
    """Recursively yield DirEntry objects for given directory.
    From: https://bit.ly/3b3wxAW
    """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry


def annual_to_monthly(basedir, year):

    # construct the path for each year
    path = os.path.join(basedir, "%0.4i" % year)
    print(path)

    # obtain a list of files for each year
    #files = list(scantree(path))
    files = [x.path for x in list(scantree(path)) if x.path.endswith(".nc")]

    # open a multi-file dataset and extract the variable
    da = xr.open_mfdataset(files, combine="by_coords", use_cftime=True)[var]

    # save variable attributes for use later
    attrs = da.attrs

    # calculate monthly mean of each year
    da = da.resample(time="1M")

    return (da, attrs)


def main(basedir, dataname_begin, var, start_year, end_year):

    # use list comprehension to loop over years
    arr = [
        annual_to_monthly(basedir, year) for year in np.arange(start_year, end_year + 1)
    ]

    # separate attribute dictionary from the data arrays
    attrs = arr[0][1]
    arr = [x[0] for x in arr]

    # concatenate along existing time dimension
    arr = xr.concat([x.mean(dim="time") for x in arr], dim="time")

    arr = arr.assign_attrs(attrs)

    # create an empty dataset to hold the new array
    ds_total = xr.Dataset()

    # associate variable with new dataset and set fill value
    ds_total[var] = xr.where(arr.isnull(), 1.0e20, arr)
    ds_total[var] = arr.astype(np.float32)
    ds_total[var].encoding["_FillValue"] = 1.0e20

    # output file to netcdf
    outputname = dataname_begin + "monthly_%s.nc" % var
    ds_total.to_netcdf(os.path.join(basedir, outputname))


if __name__ == "__main__":
    # absolute path to the data directory
    basedir = "/storage1/home1/chiaweih/Research/proj3_omip_sl/data/CMEMS/"

    # data file name starts with
    dataname_begin = "dt_global_allsat_phy_l4_"

    # variable name
    var = "adt"

    # time period for processing the daily output
    #  this can be changed based on used download period

    start_year = 1993
    end_year = 2018

    result = main(basedir, dataname_begin, var, start_year, end_year)
