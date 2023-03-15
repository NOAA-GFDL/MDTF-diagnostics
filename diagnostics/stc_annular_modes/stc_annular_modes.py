import os
import traceback

import numpy as np
import xarray as xr
import matplotlib as mpl
from matplotlib import pyplot as plt

from stc_annular_modes_calc import (
    eof_annular_mode,
    anomalize_geohgt,
    gauss_smooth_doy,
    acf,
    efolding_tscales,
    annmode_predictability,
)
from stc_annular_modes_plot import plot_annmode_eof_structure, plot_doy_timeseries

mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = "Roboto"
mpl.rcParams["font.size"] = 12

def make_tseries(am, which, data_name, out_dir, first, last):
    r""" A convenience function for running through the logic
    of the POD for each hemisphere given both NAM/SAM indices

    Parameters
    ----------
    am : `xarray.DataArray`
        The annular mode time series, with a hemi dimension

    which : str
        Which dataset are we using? gets displayed in output print
        messages (should be 'model' or 'obs')

    data_name : str
        The name of the data in use

    out_dir : str
        The location where figures get saved

    first : int
        The first year of the data

    last : int
        The last year of the data

    """

    # Iterate over each hemisphere
    hemis = {"S": -1, "N": 1}

    ### BEGIN MODEL DIAGNOSTIC CODEBLOCK ###
    for hemi, hn in hemis.items():
        # E-FOLDING TIMESCALES
        print(f"*** Computing the {which} {hemi}AM e-folding timescales")
        acfs = xr.apply_ufunc(
            gauss_smooth_doy,
            acf(am.sel(hemi=hn))
        )
        tscales = efolding_tscales(acfs)
        print(f"*** Plotting the {which} {hemi}AM e-folding timescales")
        title_str = f"{data_name}\n{hemi}AM Timescales ({first}-{last})"
        finame = f"{data_name}_{hemi}AM_{first}-{last}_efolding-timescales.eps"
        fig = plot_doy_timeseries(tscales, "eftscale", title=title_str)
        fig.savefig(out_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

        # INTERANN STDDEV
        print(f"*** Computing the {which} {hemi}AM interannual std dev")
        int_std = xr.apply_ufunc(
            gauss_smooth_doy,
            am.sel(hemi=hn).groupby("time.dayofyear").std("time")
        )
        print(f"*** Plotting the {which} {hemi}AM interannual std dev")
        title_str = f"{data_name}\n{hemi}AM Std. Deviation ({first}-{last})"
        finame = f"{data_name}_{hemi}AM_{first}-{last}_interann-stdv.eps"
        fig = plot_doy_timeseries(int_std, "interannstdv", title=title_str)
        fig.savefig(out_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

        # PREDICTABILITY
        print(f"*** Computing the {which} {hemi}AM predictability")
        pred = xr.apply_ufunc(
            gauss_smooth_doy,
            annmode_predictability(am.sel(hemi=hn), pred_lev=PRED_LEV),
        )
        print(f"*** Plotting the {which} {hemi}AM predictability")
        title_str = (
            f"{data_name}\n{PRED_LEV} hPa {hemi}AM Predictability ({first}-{last})"
        )
        finame = f"{data_name}_{hemi}AM_{first}-{last}_predictability.eps"
        fig = plot_doy_timeseries(pred, "predictability", title=title_str)
        fig.savefig(out_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

    return


########################
# --- BEGIN SCRIPT --- #
########################
print("\n=======================================")
print("BEGIN stc_annular_modes.py ")
print("=======================================")

# Parse MDTF-set environment variables
print("*** Parse MDTF-set environment variables ...")
CASENAME = os.environ["CASENAME"]
FIRSTYR = int(os.environ["FIRSTYR"])
LASTYR = int(os.environ["LASTYR"])
WK_DIR = os.environ["WK_DIR"]
OBS_DATA = os.environ["OBS_DATA"]

zfi = os.environ["ZG_FILE"]
data_dir = f"{WK_DIR}/model/netCDF"
plot_dir = f"{WK_DIR}/model/PS/"
obs_plot_dir = f"{WK_DIR}/obs/PS/"

# Parse POD-specific environment variables
print("*** Parsing POD-specific environment variables")
ANOM_METHOD = os.environ["ANOM_METHOD"]
PRED_LEV = int(os.environ["PRED_LEV"])
SAVE_DERIVED_DATA = bool(int(os.environ["SAVE_DERIVED_DATA"]))
USE_CONSISTENT_YEARS = bool(int(os.environ["USE_CONSISTENT_YEARS"]))
OBS_FIRSTYR = int(os.environ["OBS_FIRSTYR"])
OBS_LASTYR = int(os.environ["OBS_LASTYR"])

# user wishes to use same years as model inputdata
if USE_CONSISTENT_YEARS is True:
    OBS_FIRSTYR = FIRSTYR
    OBS_LASTYR = LASTYR

# data provided with POD only spans from 1979-2019
if (OBS_FIRSTYR < 1979) or (OBS_LASTYR > 2021):
    msg = "OBS_FIRSTYR and OBS_LASTYR must be between 1979-2021"
    raise ValueError(msg)

print(
    f"(SETTINGS) Will compute the annular mode predictability of the {PRED_LEV} hPa level"
)
print(f"(SETTINGS) Will use {FIRSTYR}-{LASTYR} for {CASENAME}")
print(f"(SETTINGS) Will use {OBS_FIRSTYR}-{OBS_LASTYR} for obs")

if ANOM_METHOD not in ["gerber", "simple"]:
    msg = 'The anomaly method specified by the ANOM_METHOD env var must be either "gerber" or "simple"'
    raise ValueError(msg)

# Read the input model data
print(f"*** Now starting work on {CASENAME}\n------------------------------")
print("*** Reading model variables ...")
print("    zonal mean geohgts")
zzm = xr.open_dataset(zfi)["zg"]

# Read in the pre-digested obs data and subset the times
print("*** Now reading in pre-digested obs data")
try:
    # geohgt fourier coefficients for +/- 60lat
    obs_am = xr.open_dataset(f"{OBS_DATA}/era5_annmodes_1979-2021.nc")
    obs_nam_struc = xr.open_dataset(f"{OBS_DATA}/era5_nam_lat-struc_1979-2021.nc")
    obs_sam_struc = xr.open_dataset(f"{OBS_DATA}/era5_sam_lat-struc_1979-2021.nc")
    can_plot_obs = True
    obs_name = 'ERA5'

except Exception:
    msg = (
        "*** Unable to read all of the pre-digested obs data. "
        + f"Please check that you have data in {OBS_DATA}"
    )
    print(msg)
    print(traceback.format_exc())
    can_plot_obs = False

# Compute the NAM and SAM indices
print("*** Computing the NAM and SAM loading patterns and PC time series")
nam, nam_struc = eof_annular_mode(anomalize_geohgt(zzm, "NH", anom=ANOM_METHOD))
sam, sam_struc = eof_annular_mode(anomalize_geohgt(zzm, "SH", anom=ANOM_METHOD))

# Plot the latitudinal structures
print("*** Plotting the model annular mode EOF structures")
title_str = (
    f"{CASENAME} EOF1 Patterns of\n Zonal Mean Height Anoms ({FIRSTYR}-{LASTYR})"
)
fig = plot_annmode_eof_structure(sam_struc, nam_struc, title=title_str)
finame = f"{CASENAME}_{FIRSTYR}-{LASTYR}_annmode_structures.eps"
fig.savefig(plot_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

nam.name = 'annular_mode'
sam.name = 'annular_mode'
annmodes = xr.concat(
    (sam.assign_coords({"hemi": -1}), nam.assign_coords({"hemi": 1})), dim="hemi"
)

# Save the relevant digested data
if SAVE_DERIVED_DATA is True:
    print('*** Saving the model annular modes')
    annmodes.attrs['long_name'] = 'Annular mode principal component time series'
    annmodes.attrs['units'] = 'unitless'

    outfile = f'{data_dir}/{CASENAME}_annmodes_{FIRSTYR}-{LASTYR}.nc'
    encoding = {'annular_mode': {'dtype': 'float32'}}
    annmodes.to_netcdf(outfile, encoding=encoding)

    outfile = f'{data_dir}/{CASENAME}_nam_lat-struc_{FIRSTYR}-{LASTYR}.nc'
    nam_struc.to_netcdf(outfile)

    outfile = f'{data_dir}/{CASENAME}_sam_lat-struc_{FIRSTYR}-{LASTYR}.nc'
    sam_struc.to_netcdf(outfile)


# Compute and plot the diagnostics for the model
make_tseries(annmodes, 'model', CASENAME, plot_dir, FIRSTYR, LASTYR)

# Compute and plot the diagnostics for the obs
if can_plot_obs is True:
    print("*** Plotting the obs annular mode EOF structures")
    title_str = (
        f"{obs_name} EOF1 Patterns of\n Zonal Mean Height Anoms ({OBS_FIRSTYR}-{OBS_LASTYR})"
    )
    fig = plot_annmode_eof_structure(obs_sam_struc, obs_nam_struc, title=title_str)
    finame = f"{obs_name}_{OBS_FIRSTYR}-{OBS_LASTYR}_annmode_structures.eps"
    fig.savefig(obs_plot_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

    make_tseries(obs_am, 'obs', obs_name, obs_plot_dir, OBS_FIRSTYR, OBS_LASTYR)

print('\n=====================================')
print('END stc_annular_modes.py ')
print('=====================================\n')
