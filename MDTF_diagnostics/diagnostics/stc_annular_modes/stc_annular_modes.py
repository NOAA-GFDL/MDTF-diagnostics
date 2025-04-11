# ==============================================================================
# MDTF Strat-Trop Coupling: Annular Modes POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Annular Modes POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC Annular Mode Coupling
# Last update: 2023-03-27
#
# This script computes annular mode indices and examines their interannual
# variability, persistence, and predictability as a function of day of year. 
# It uses EOF analsis on zonal mean geopotential height anomalies to 
# define the annular modes (assumed to be EOF1) and their PC time series. 
# Please see the POD documentation, as well as the references for the 
# scientific foundations of this POD.
#
# ==============================================================================
#   Version, Contact Info, and License
# ==============================================================================
#   - Version/revision information: v1.0 (2023-03-24)
#   - PI: Zachary D. Lawrence, CIRES + CU Boulder / NOAA PSL
#   - Developer/point of contact: Zachary D. Lawrence, zachary.lawrence@noaa.gov
#   - Other contributors: Amy H. Butler, NOAA CSL, amy.butler@noaa.gov
#
#  The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
# ==============================================================================
#   Functionality
# ==============================================================================
#   This POD is composed of three files, including the main driver script
#   (stc_annular_modes.py), functions that perform computations
#   (stc_annular_modes_calc.py), and functions that compile the specific
#   POD plots (stc_annular_modes_plot.py). The basic outline of how this
#   POD operates is as follows:
#   (1) Driver script parses environment variables, and reads in data
#   (2) Driver script calls calc functions to perform the EOF analysis
#       on the input zonal mean geopotential height fields.
#   (3) Driver script calls calc functions to derive further annular mode 
#       diagnostics, and sends these to the plotting functions
#   (4) Outputs the digested model fields into netcdf files.
#
# ==============================================================================
#   Required programming language and libraries
# ==============================================================================
#   This POD is done fully in python, and primarily makes use of numpy, xarray,
#   and pandas to read, subset, and transform the data. It also uses the eofs 
#   package to perform the EOF analysis. Plotting is done with matplotlib.
#
# ==============================================================================
#   Required model input variables
# ==============================================================================
#   This POD requires daily mean fields of
#   - zonal mean geopotential heights (time, lev, lat), ideally with pressure 
#     levels spanning between 1000 and 1 hPa. 
#   - nothing else!
#
# ==============================================================================
#   References
# ==============================================================================
#   Thompson, D. W. J., and J. M. Wallace, 2000: Annular Modes in the Extratropical 
#       Circulation. Part I: Month-to-Month Variability. J. Climate, 13, 
#       1000–1016, https://doi.org/10.1175/1520-0442(2000)013<1000:AMITEC>2.0.CO;2.
#   Baldwin, M.P. and Thompson, D.W.J. (2009), A critical comparison of 
#      stratosphere–troposphere coupling indices. Q.J.R. Meteorol. Soc., 
#      135: 1661-1672. https://doi.org/10.1002/qj.479
#   Gerber, E. P., et al. (2010), Stratosphere-troposphere coupling and annular mode 
#       variability in chemistry-climate models, J. Geophys. Res., 115, D00M06, 
#       doi:10.1029/2009JD013770.
#   Simpson, I. R., Hitchcock, P., Shepherd, T. G., and Scinocca, J. F. (2011), 
#      Stratospheric variability and tropospheric annular-mode timescales, 
#      Geophys. Res. Lett., 38, L20806, doi:10.1029/2011GL049304.
#   Kidston, J., Scaife, A., Hardiman, S. et al. Stratospheric influence on tropospheric 
#      jet streams, storm tracks and surface weather. Nature Geosci 8, 433–440 (2015). 
#      https://doi.org/10.1038/ngeo2424
#   Schenzinger, V., and Osprey, S. M. (2015), Interpreting the nature of Northern 
#      and Southern Annular Mode variability in CMIP5 Models, J. Geophys. Res. Atmos., 
#      120, 11,203– 11,214, doi:10.1002/2014JD022989.


import os
import traceback
import xarray as xr
import matplotlib as mpl

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

    # BEGIN MODEL DIAGNOSTIC CODEBLOCK ###
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
        finame = f"{data_name}_{hemi}AM_efolding-timescales.eps"
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
        finame = f"{data_name}_{hemi}AM_interann-stdv.eps"
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
        finame = f"{data_name}_{hemi}AM_predictability.eps"
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
FIRSTYR = int(os.environ["startdate"])
LASTYR = int(os.environ["enddate"])
WK_DIR = os.environ["WORK_DIR"]
OBS_DATA = os.environ["OBS_DATA"]

# Input and output files/directories
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

# how anomalies in the zonal mean geohgts will be found
if ANOM_METHOD not in ["gerber", "simple"]:
    msg = 'The anomaly method specified by the ANOM_METHOD env var must be either "gerber" or "simple"'
    raise ValueError(msg)

print(f"(SETTINGS) Will compute annular modes using the '{ANOM_METHOD}' method")
print(f"(SETTINGS) Will compute the annular mode predictability of the {PRED_LEV} hPa level")
print(f"(SETTINGS) Will use {FIRSTYR}-{LASTYR} for {CASENAME}")
print(f"(SETTINGS) Will use {OBS_FIRSTYR}-{OBS_LASTYR} for obs")

# Read the input model data
print(f"*** Now starting work on {CASENAME}\n------------------------------")
print("*** Reading model variables ...")
print("    zonal mean geohgts")
zzm = xr.open_dataset(zfi)["zg"]

# Check if the data has leapyears, and get rid of them if so
max_doy = int(zzm['time.dayofyear'].max())
if (max_doy == 366):
    print("*** Removing leapdays from data")
    zzm = zzm.convert_calendar('noleap', use_cftime=True)

# Read in the pre-digested obs data and subset the times
print("*** Now reading in pre-digested obs data")
try:
    obs_am = xr.open_dataarray(f"{OBS_DATA}/era5_annmodes_1979-2021.nc")
    obs_am = obs_am.sel(time=slice(f'{OBS_FIRSTYR}', f'{OBS_LASTYR}'))
    obs_nam_struc = xr.open_dataarray(f"{OBS_DATA}/era5_nam_lat-struc_1979-2021.nc")
    obs_sam_struc = xr.open_dataarray(f"{OBS_DATA}/era5_sam_lat-struc_1979-2021.nc")
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
print("*** Plotting the model annular mode EOF1 structures")
title_str = (
    f"{CASENAME} EOF1 Patterns of\n Zonal Mean Height Anoms ({FIRSTYR}-{LASTYR})"
)
fig = plot_annmode_eof_structure(sam_struc, nam_struc, title=title_str)
finame = f"{CASENAME}_annmode_structures.eps"
fig.savefig(plot_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

# Combine the annular mode PC time series into a single dataarray
annmodes = xr.concat((sam.assign_coords({"hemi": -1}), 
                      nam.assign_coords({"hemi": 1})), dim="hemi")

# Save the relevant digested data
if SAVE_DERIVED_DATA is True:
    print('*** Saving the model PC1 time series')
    annmodes.name = 'pc1'
    annmodes.attrs['long_name'] = 'PC1 time series of Zonal Mean Geohgt Anomalies'
    annmodes.attrs['units'] = 'unitless'
    annmodes.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

    outfile = f'{data_dir}/{CASENAME}_annmodes_{FIRSTYR}-{LASTYR}.nc'
    encoding = {'pc1': {'dtype': 'float32'}}
    annmodes.to_netcdf(outfile, encoding=encoding)

    print('*** Saving the model EOF1 structures for NH and SH')
    nam_struc.name = 'eof1'
    nam_struc.attrs['long_name'] = 'EOF1 of NH Zonal Mean Geohgt Anomalies'
    encoding = {'eof1': {'dtype': 'float32'}}
    outfile = f'{data_dir}/{CASENAME}_nam_lat-struc_{FIRSTYR}-{LASTYR}.nc'
    nam_struc.to_netcdf(outfile, encoding=encoding)

    sam_struc.name = 'eof1'
    sam_struc.attrs['long_name'] = 'EOF1 of SH Zonal Mean Geohgt Anomalies'
    outfile = f'{data_dir}/{CASENAME}_sam_lat-struc_{FIRSTYR}-{LASTYR}.nc'
    sam_struc.to_netcdf(outfile, encoding=encoding)


# Compute and plot the diagnostics for the model
make_tseries(annmodes, 'model', CASENAME, plot_dir, FIRSTYR, LASTYR)

# Compute and plot the diagnostics for the obs
if can_plot_obs is True:
    print("*** Plotting the obs annular mode EOF structures")
    title_str = (
        f"{obs_name} EOF1 Patterns of\n Zonal Mean Height Anoms ({OBS_FIRSTYR}-{OBS_LASTYR})"
    )
    fig = plot_annmode_eof_structure(obs_sam_struc, obs_nam_struc, title=title_str)
    finame = f"{obs_name}_annmode_structures.eps"
    fig.savefig(obs_plot_dir + finame, facecolor="white", dpi=150, bbox_inches="tight")

    make_tseries(obs_am, 'obs', obs_name, obs_plot_dir, OBS_FIRSTYR, OBS_LASTYR)

print('\n=====================================')
print('END stc_annular_modes.py ')
print('=====================================\n')
