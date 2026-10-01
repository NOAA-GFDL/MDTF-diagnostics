# ==============================================================================
# MDTF Strat-Trop Coupling: Eddy Heat Fluxes POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Eddy Heat Fluxes POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC Eddy Heat Fluxes
# Last update: 2022-09-26
#
# This script performs calculations to assess the action of vertically
# propagating planetary-scale stationary waves on the polar wintertime
# stratosphere. This POD uses the zonal mean eddy heat flux, v'T', as a proxy
# for the vertical flux of waves, where v is the meridional wind, and T is the
# temperature. When eddy heat fluxes are above/below normal, the polar
# stratospheric circulation should be weaker/stronger than normal, with
# warmer/colder temperatures, respectively. Please see the references for the
# scientific foundations of this POD.
#
# ==============================================================================
#   Version, Contact Info, and License
# ==============================================================================
#   - Version/revision information: v1.0 (2022-04-27)
#   - PI: Zachary D. Lawrence, CIRES + CU Boulder / NOAA PSL
#   - Developer/point of contact: Zachary D. Lawrence, zachary.lawrence@noaa.gov
#   - Other contributors: Amy H. Butler, NOAA CSL, amy.butler@noaa.gov
#
#  The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
# ==============================================================================
#   Functionality
# ==============================================================================
#   This POD is completely contained within the script
#   stc_eddy_heat_fluxes.py. The script goes through three basic steps:
#   (1) Calculates eddy heat fluxes over a specified latitude band,
#       and polar cap temperatures and geopotential heights. The latitude band
#       for the eddy heat fluxes and the lower limit of the polar cap are all
#       able to be specified in the settings.jsonc, and are calculated for both
#       the northern and southern hemispheres.
#   (2) Creates two types of plots, one showing the correlation between
#       seasonal averaged eddy heat fluxes and polar cap temperatures, and
#       another showing the lag correlations between polar cap geopotential
#       heights and 100 hPa heat fluxes.
#   (3) Outputs the three diagnostics (lat-band averaged eddy heat fluxes,
#       polar cap temperatures, and polar cap geopotential heights)
#
# ==============================================================================
#   Required programming language and libraries
# ==============================================================================
#   This POD is done fully in python, and primarily makes use of numpy and
#   xarray to read, subset, and transform the data. It also makes use of xESMF
#   to perform regridding of fields in cases where, e.g., wind components are
#   provided at grid cell boundaries while temperatures/heights are provided at
#   grid cell centers.
#
# ==============================================================================
#   Required model input variables
# ==============================================================================
#   This POD requires monthly-mean fields of
#   - meridional wind velocity (va)
#   - air temperature (ta)
#   - geopotential height (zg)
#   which should all be provided with dimensions of (time, lev, lat, lon)
#
# ==============================================================================
#   References
# ==============================================================================
#   Newman, P. A., E. R. Nash, and J. E. Rosenfield, 2001: What controls the
#       temperature of the Arctic stratosphere during the spring? JGR: A,
#       106, 19999–20010, https://doi.org/10.1029/2000JD000061.
#   Furtado, J. C., J. L. Cohen, A. H. Butler, E. E. Riddle, and A. Kumar, 2015:
#       Eurasian snow cover variability and links to winter climate in the CMIP5
#       models. Clim Dyn, 45, 2591–2605, https://doi.org/10.1007/s00382-015-2494-4.
#   Kidston, J., A. Scaife, S. C. Hardiman, D. M. Mitchell, N. Butchart,
#       M. P. Baldwin, and L. J. Gray, 2015: Stratospheric influence on tropospheric
#       jet streams, storm tracks and surface weather. Nature Geosci 8,
#       433–440. https://doi.org/10.1038/ngeo2424

import os
import traceback

import numpy as np
import xarray as xr
import xesmf as xe
import matplotlib as mpl
from matplotlib import pyplot as plt
from scipy.stats import linregress

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12


def lat_avg(ds, lat_lo, lat_hi):
    r""" Calculate a meridional average of data. The average is done using 
        cosine-latitude weighting. 

    Parameters
    ----------
    ds : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset for which to calculate a meridional
        average between the given latitude limits.
    
    lat_lo : Numeric quantity 
        The lower latitude limit (inclusive) for performing the meridional average

    lat_hi : Numeric quantity
        The upper latitude limit (inclusive) for performing the meridional average

    Returns
    -------
    ds_wgt : `xarray.DataArray` or `xarray.Dataset`
         The cos(lat) weighted average of the data between lat_lo and lat_hi

    Notes
    -----
    The input xarray variable ds is assumed to have a dimension named "lat". 
    E.g., if your data has a dimension named "latitude", use the rename method: 
        ds.rename({'latitude':'lat'})

    """

    # Limit the latitude range without assuming the ordering of lats
    ds_tmp = ds.isel(lat = np.logical_and(ds.lat >= lat_lo, ds.lat <= lat_hi))

    # Define the cos(lat) weights
    wgts = np.cos(np.deg2rad(ds_tmp.lat))
    wgts.name = "weights"

    # Apply weighting and take average
    ds_wgt_avg = ds_tmp.weighted(wgts).mean('lat')
    return ds_wgt_avg


def compute_total_eddy_heat_flux(v, T):
    r""" Compute the total zonal mean eddy heat flux from meridonal winds 
    and temperatures. The eddy heat flux is calculated as: 
        ehf = zonal_mean( (v - zonal_mean(v)) * (T - zonal_mean(T)))

    Parameters
    ----------
    v : `xarray.DataArray`
        The meridional wind component. Assumed to have the same dimensions as T
    
    T : `xarray.DataArray`
        The air temperature. Assumed to have the same dimensions as v

    Returns
    -------
    ehf : `xarray.DataArray`
        The zonal mean eddy heat flux

    Notes
    -----
    The input fields v and T are assumed to have dimensions named "lat" 
    and "lon". E.g., if your data has dimensions "latitude" and/or "longitude",
    use the rename method:
        ds.rename({'latitude':'lat','longitude':'lon'})

    Ideally v and T would be provided on the same latitude/longitude grid. 
    In practice this is not necessarily the case as some models provide 
    different variables at cell-centers and cell-edges. If this is found 
    to be the case, this function will use xesmf to do bilinear regridding 
    of the meridional wind component to match the grid of the temperatures.

    """
   
    # Take the zonal means of v and T
    v_zm = v.mean('lon')
    T_zm = T.mean('lon')

    # If v and T are on same grid, can multiply the eddies and take zonal mean
    if (np.array_equal(v.lat,T.lat)) and (np.array_equal(v.lon, T.lon)):
        ehf = ((v - v_zm) * (T - T_zm)).mean('lon')

    # If v and T are on different grids, interpolate v to T's grid beforehand
    else:
        # Set up xESMF regridder with necessary grid-defining datasets
        print('*** Interpolating v to same grid as T')
        in_grid = xr.Dataset(
            {
                "lat": (["lat"], v.lat.values),
                "lon": (["lon"], v.lon.values),
            }
        )

        out_grid = xr.Dataset(
            {
                "lat": (["lat"], T.lat.values),
                "lon": (["lon"], T.lon.values),
            }
        )
        regridder = xe.Regridder(in_grid, out_grid, "bilinear")

        ehf = (regridder(v - v_zm)*(T - T_zm)).mean('lon')

    return ehf


def plot_ehf_tcap_corr(ehf, tpcap, hemi):
    r""" Create a scatterplot showing the relationship between seasonal-
    mean eddy heat flux and polar cap temperatures in the stratosphere. 


    Parameters
    ----------
    ehf : `xarray.DataArray`
        The 100 hPa eddy heat fluxes with units in K m s-1 
    
    tpcap : `xarray.DataArray` 
        The 50 hPa polar cap temperatures with units in K 

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 

    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    Notes
    -----
    Both ehf and tpcap are assumed to have dimensions of time. If 
    NH is given for hemi, this will do the correlation between DJF 
    100 hPa eddy heat flux and 50 hPa JFM polar cap temperatures. 
    If SH is given, this will do it for ASO heat flux and SON 
    polar cap temperatures.

    """
    
    fig, ax = plt.subplots()

    if (hemi == 'NH'):
        # Need DJF heat flux at 100 hPa
        xlab_str = f"100 hPa DJF v\'T\'"+\
                   f"({EHF_LO_LAT}-{EHF_HI_LAT}N), [K$\cdot$m / s]"
        ehf_seas = ehf.resample(time='QS-DEC').mean('time')
        ehf_seas = ehf_seas.where(ehf_seas.time.dt.month == 12, drop=True)

        # Need JFM polar cap T at 50 hPa
        ylab_str = f"50 hPa JFM {PCAP_LO_LAT}-90N T [K]"
        tpc_seas = tpcap.resample(time='QS-JAN').mean('time')
        tpc_seas = tpc_seas.where(tpc_seas.time.dt.month == 1, drop=True)

        # For NH data, need to ensure the years are appropriately handled
        ehf_seas = ehf_seas.where(ehf_seas.time.dt.year.isin(tpc_seas.time.dt.year-1),drop=True)
        tpc_seas = tpc_seas.where(tpc_seas.time.dt.year.isin(ehf_seas.time.dt.year+1),drop=True)

    elif (hemi == 'SH'):
        # Need ASO heat flux at 100 hPa
        xlab_str = f"100 hPa ASO v\'T\'"+\
                   f"({EHF_LO_LAT}-{EHF_HI_LAT}S), [K$\cdot$m / s]"
        ehf_seas = ehf.resample(time='QS-FEB').mean('time')
        ehf_seas = ehf_seas.where(ehf_seas.time.dt.month == 8, drop=True)

        # Need SON polar cap T at 50 hPa
        ylab_str = f"50 hPa SON {PCAP_LO_LAT}-90S T [K]"
        tpc_seas = tpcap.resample(time='QS-DEC').mean('time')
        tpc_seas = tpc_seas.where(tpc_seas.time.dt.month == 9, drop=True)

    else:
        msg = f'hemi must be one of NH or SH; entered {hemi}'
        raise ValueError(msg)

    ax.scatter(ehf_seas.values, tpc_seas.values, c='grey', alpha=0.5, s=16)

    # Determine plot axes from the data
    xlims = (np.round(ehf_seas.min())-2.5, np.round(ehf_seas.max())+2.5)
    ylims = (np.round(tpc_seas.min())-2.5, np.round(tpc_seas.max())+2.5)

    # Get the best-fit line and plot it
    m,b,r,p,std_err = linregress(ehf_seas.values, tpc_seas.values)
    x = np.linspace(xlims[0],xlims[1])
    plt.plot(x,m*x+b, color='black', linestyle='--', alpha=0.5, linewidth=0.66)

    # Set plot limits, add labels, and make axis square
    plt.xlim(xlims)
    plt.ylim(ylims)
    plt.xlabel(xlab_str, fontsize=18)
    plt.ylabel(ylab_str, fontsize=18)
    ax.set_aspect(1.0/ax.get_data_ratio(), adjustable='box')

    # Get the correlation and do bootstrapping to determine its 95% CI
    corr = np.corrcoef(ehf_seas.values, tpc_seas.values)[0,1]
    nbs = 1000
    corr_bs = []
    for n in range(nbs):
        ixs = np.random.choice(ehf_seas.size, size=ehf_seas.size)
        r = np.corrcoef(ehf_seas.isel(time=ixs).values,
                        tpc_seas.isel(time=ixs).values)[0,1]
        corr_bs.append(r)
    bs_lo,bs_hi = np.percentile(corr_bs, [2.5, 97.5])

    # display the correlation and 95% bootstrap CI
    plt.text(0.05,0.88, f'r={corr:.3f} ({bs_lo:.3f}, {bs_hi:.3f})',
             transform=ax.transAxes, fontsize=16, color='red',
             fontweight='semibold')

    fig.subplots_adjust(left=0.1,right=0.98)
    fig.set_size_inches(6.5,6.5)

    return (fig,ax)


def plot_ehf_zcap_lags(ehf, zpcap, hemi):
    r""" Creates a lag-correlation contour plot assessing the relationship 
    between eddy heat fluxes and polar cap geopotential heights for different 
    months when strat-trop coupling is most active. 

    Paramaeters
    -----------
    ehf : `xarray.DataArray`
        The 100 hPa eddy heat flux with units of K m s-1

    zpap : `xarray.DataArray` 
        The polar cap geopotential height across pressure levels

    hemi : string 
        Should be either 'NH' or 'SH' for northern/southern hemisphere, 
        respectively

    Returns
    -------
    (fig, ax) : tuple
        A tuple containing the matplotlib figure and axis handles 
 
    Notes
    -----
    Assumes that both ehf and zpcap have time dimensions, and that 
    zpcap additionally has a "lev" dimension for the pressure levels. 

    If NH is chosen, this function will create a plot correlating the 
    December 100 hPa eddy heat flux with polar cap heights for lags 
    between September and March. If SH is chosen, it will instead do 
    it for September 100 hPa eddy heat flux with polar cap heights 
    for lags between June and December.   

    """
    
    def _align_month_corrs(ehf, zpc, month, hemi):
        r""" Small utility function for aligning the time series correctly 
        so that the lag correlations are performed correctly. This is 
        particularly necessary when hemi is 'NH' because the correlations 
        span the year-boundary, so things have to be paired correctly.
        """
        
        # If the months we're correlating fall within the same year, then
        # we need only align the same years
        if ((hemi == 'NH') and (month in [9,10,11,12])) or (hemi == 'SH'):
            ehf = ehf.where(ehf.time.dt.year.isin(zpc.time.dt.year), drop=True)
            zpc = zpc.where(zpc.time.dt.year.isin(ehf.time.dt.year), drop=True)
        # If the months fall in different years (e.g., Dec with Feb), then
        # we need to align the 1-yr offset
        elif (hemi == 'NH') and (month in [1,2,3]):
            ehf = ehf.where(ehf.time.dt.year.isin(zpc.time.dt.year-1),drop=True)
            zpc = zpc.where(zpc.time.dt.year.isin(ehf.time.dt.year+1),drop=True)

        return (ehf, zpc)

    if (hemi == 'NH'):
        # Need Dec heat flux at 100 hPa
        mon_origin = 'Dec'
        ehf_early = ehf.where(ehf.time.dt.month == 12, drop=True)
        months = [9, 10, 11, 12, 1, 2, 3]
    elif (hemi == 'SH'):
        # Need Sep heat flux at 100 hPa
        mon_origin = 'Sep'
        ehf_early = ehf.where(ehf.time.dt.month == 9, drop=True)
        months = [6, 7, 8, 9, 10, 11, 12]
    else:
        msg = f'hemi must be one of NH or SH; entered {hemi}'
        raise ValueError(msg)

    # Find the correlations of 100 hPa eddy heat flux with polar cap Z at
    # all pressure levels, for each lag
    lag_corrs = []
    for mon in months:
        zpc_mon = zpcap.where(zpcap.time.dt.month == mon, drop=True)
        ehf_early,zpc_mon = _align_month_corrs(ehf_early, zpc_mon, mon, hemi)

        data_mat = np.concatenate([ehf_early.values[:,np.newaxis],
                                  zpc_mon.values], axis=1)
        corrs = np.corrcoef(data_mat.T)[0,1:]
        lag_corrs.append(corrs[np.newaxis,...])
    lag_corrs = np.concatenate(lag_corrs, axis=0)

    fig, ax = plt.subplots()

    xlab_str = "Month"
    ylab_str = "Pressure [hPa]"
    cbp = ax.contourf(np.arange(7), zpcap.lev.values, lag_corrs.T,
                     levels=np.linspace(-0.6,0.6,13),cmap='RdBu_r',extend='both')
    ax.set_yscale('log')
    ax.invert_yaxis()
    plt.xticks(np.arange(7), months)
    plt.xlabel(xlab_str, fontsize=18)
    plt.ylabel(ylab_str, fontsize=18)
    plt.title(f'Lag correlation of Polar Cap Z with {mon_origin} 100 hPa Eddy Heat Flux')
    plt.colorbar(cbp, label='Correlation', ax=[ax], location='bottom')

    fig.set_size_inches(10,6)

    return (fig,ax)


########################
# --- BEGIN SCRIPT --- #
########################
print('\n=======================================')
print('BEGIN stc_eddy_heat_fluxes.py ')
print('=======================================\n')

# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = os.environ['startdate']
LASTYR = os.environ['enddate']
WK_DIR = os.environ['WORK_DIR']
OBS_DATA = os.environ['OBS_DATA']

vfi = os.environ['V100_FILE']
zfi = os.environ['ZG_FILE']
tfi = os.environ['TA_FILE']
t50fi = os.environ['T50_FILE']
t100fi = os.environ['T100_FILE']

# Parse POD-specific environment variables
print('*** Parse POD-specific environment variables ...')
EHF_LO_LAT = int(os.environ['HEAT_FLUX_LO_LAT'])
EHF_HI_LAT = int(os.environ['HEAT_FLUX_HI_LAT'])
PCAP_LO_LAT = int(os.environ['PCAP_LO_LAT'])

# Do error-checking on these environment variables. Rather than trying to
# correct the values, we throw errors so that users can adjust their config
# files in the appropriate manner, and obtain expected results.
if EHF_LO_LAT >= EHF_HI_LAT:
    msg = 'EHF_LO_LAT must be less than EHF_HI_LAT, and both must be >= 30'
    raise ValueError(msg)

if EHF_LO_LAT < 30:
    msg = 'EHF_LO_LAT must be >= 30'
    raise ValueError(msg)

if PCAP_LO_LAT < 30:
    msg = 'PCAP_LO_LAT must be >= 30'
    raise ValueError(msg)

# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading variables ...')
print('    v100')
v100 = xr.open_dataset(vfi)['v100']
# this is a bit hackish right now to deal with temperatures
try:
    print('    t100')
    t100 = xr.open_dataset(t100fi)['t100']
    print('     t50')
    t50 = xr.open_dataset(t50fi)['t50']
    t_lev_fis = True
except Exception as exc:
    print('Unable to read individual prs level ta files; querying 4D fields')
    print('      ta')
    print(exc)
    ta = xr.open_dataset(tfi)['ta']
    t50 = ta.sel(lev=50)
    t100 = ta.sel(lev=100)
    t_lev_fis = False
print('      zg')
zg = xr.open_dataset(zfi)['zg']

# Compute the diagnostics
print('*** Computing zonal mean total eddy heat fluxes')
ehf = compute_total_eddy_heat_flux(v100,t100)

print(f'*** Computing {EHF_LO_LAT}-{EHF_HI_LAT}N and '+\
      f'{EHF_LO_LAT}-{EHF_HI_LAT}S lat averages of 100 hPa eddy heat fluxes')
ehf_band = {}
ehf_band['NH'] = lat_avg(ehf,  EHF_LO_LAT,  EHF_HI_LAT)
ehf_band['SH'] = lat_avg(ehf, -EHF_HI_LAT, -EHF_LO_LAT)

print('*** Computing polar cap averages of geopotential height')
zg_pcap = {}
zg_zm = zg.mean('lon')
zg_pcap['NH'] = lat_avg(zg_zm,  PCAP_LO_LAT,  90)
zg_pcap['SH'] = lat_avg(zg_zm, -90, -PCAP_LO_LAT)

print('*** Computing polar cap averages of 50 hPa temperature')
ta_pcap = {}
ta_zm_50 = t50.mean('lon')
ta_pcap['NH'] = lat_avg(ta_zm_50, PCAP_LO_LAT,  90)
ta_pcap['SH'] = lat_avg(ta_zm_50, -90, -PCAP_LO_LAT)

# At this point, no longer need the raw data

v100 = v100.close()
zg = zg.close()
if t_lev_fis:
    t100 = t100.close()
    t50 = t50.close()
else:
    ta = ta.close()

# Create the POD figures for both NH and SH cases
plot_dir = f'{WK_DIR}/model/PS'
for hemi in ['NH','SH']:
    print(f'*** Plotting {hemi} EHF vs polar cap T scatter plot')
    scatter_plot = f'{plot_dir}/{CASENAME}_{hemi}_EHF-Tpcap_Scatter.eps'
    fig, ax = plot_ehf_tcap_corr(ehf_band[hemi], ta_pcap[hemi], hemi)
    ax.set_title(f'{CASENAME}\n{hemi}, {FIRSTYR}-{LASTYR}', fontsize=20)
    fig.savefig(scatter_plot)

    print(f'*** Plotting {hemi} EHF vs polar cap Z lag correlations')
    levcorr_plot = f'{plot_dir}/{CASENAME}_{hemi}_EHF-Zpcap_LagCorr.eps'
    fig,ax = plot_ehf_zcap_lags(ehf_band[hemi], zg_pcap[hemi], hemi)
    plt.suptitle(f'{CASENAME}, {hemi}, {FIRSTYR}-{LASTYR}', fontsize=20)
    fig.savefig(levcorr_plot)

# Output data will have dimensions of [hemi, time, lev], where hemi
# corresponds to the Northern/Southern hemispheres
print('*** Preparing to save derived data')
data_dir = f'{WK_DIR}/model/netCDF'
outfile = data_dir+f'/{CASENAME}_eddy-heat-flux_diagnostics.nc'

# Prepare the output variables and their metadata
zg_pcap = xr.concat([zg_pcap['SH'], zg_pcap['NH']], dim='hemi')
zg_pcap.name = 'zg_pcap'
zg_pcap.attrs['units'] = 'm'
zg_pcap.attrs['long_name'] = f'{PCAP_LO_LAT}-90 polar cap geopotential height'

ta_pcap = xr.concat([ta_pcap['SH'], ta_pcap['NH']], dim='hemi')
ta_pcap.name = 'ta_pcap_50'
ta_pcap.attrs['units'] = 'K'
ta_pcap.attrs['long_name'] = f'50 hPa {PCAP_LO_LAT}-90 polar cap temperature'

ehf_band = xr.concat([ehf_band['SH'], ehf_band['NH']], dim='hemi')
ehf_band.name = 'ehf_band_100'
ehf_band.attrs['units'] = 'K m s-1'
ehf_band.attrs['long_name'] = f'100 hPa {EHF_LO_LAT}-{EHF_HI_LAT} lat band '+\
                               'eddy heat flux'

# Create merged dataset containing the individual variables
out_ds = xr.merge([zg_pcap, ta_pcap, ehf_band])
out_ds = out_ds.assign_coords({'hemi':[-1,1]})
out_ds.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

encoding = {'zg_pcap':     {'dtype':'float32'},
            'ta_pcap_50':  {'dtype':'float32'},
            'ehf_band_100':{'dtype':'float32'}}

print(f'*** Saving heat flux diagnostics to {outfile}')
out_ds.to_netcdf(outfile, encoding=encoding)

print(f'*** Now working on obs data\n------------------------------')
obs_file = OBS_DATA+'/stc_eddy_heat_fluxes_obs-data.nc'

try:
    print(f'*** Reading obs data from {obs_file}')
    obs = xr.open_dataset(obs_file)
    rean = obs.reanalysis
    obs_firstyr = obs.time.dt.year.values[0]
    obs_lastyr = obs.time.dt.year.values[-1]

    print(f'*** Computing {EHF_LO_LAT}-{EHF_HI_LAT}N and '+\
          f'{EHF_LO_LAT}-{EHF_HI_LAT}S lat averages of heat flux obs')
    ehf_band = {}
    ehf_band['NH'] = lat_avg(obs.ehf_100,  EHF_LO_LAT,  EHF_HI_LAT)
    ehf_band['SH'] = lat_avg(obs.ehf_100, -EHF_HI_LAT, -EHF_LO_LAT)

    print('*** Computing polar cap averages of 50 hPa temperature obs')
    ta_pcap = {}
    ta_pcap['NH'] = lat_avg(obs.ta_zm_50, PCAP_LO_LAT,   90)
    ta_pcap['SH'] = lat_avg(obs.ta_zm_50, -90, -PCAP_LO_LAT)

    print('*** Computing polar cap averages of geopotential height obs')
    zg_pcap = {}
    zg_pcap['NH'] = lat_avg(obs.zg_zm,  PCAP_LO_LAT,  90)
    zg_pcap['SH'] = lat_avg(obs.zg_zm, -90, -PCAP_LO_LAT)

    # Create the POD figures for both NH and SH cases
    plot_dir = f'{WK_DIR}/obs/PS'
    for hemi in ['NH','SH']:
        print(f'*** Plotting {hemi} EHF vs polar cap T scatter plot from obs')
        scatter_plot = f'{plot_dir}/obs_{hemi}_EHF-Tpcap_Scatter.eps'
        fig, ax = plot_ehf_tcap_corr(ehf_band[hemi], ta_pcap[hemi], hemi)
        ax.set_title(f'{rean}\n{hemi}, {obs_firstyr}-{obs_lastyr}', fontsize=20)
        fig.savefig(scatter_plot)

        print(f'*** Plotting {hemi} EHF vs polar cap Z lag correlations from obs')
        levcorr_plot = f'{plot_dir}/obs_{hemi}_EHF-Zpcap_LagCorr.eps'
        fig, ax = plot_ehf_zcap_lags(ehf_band[hemi], zg_pcap[hemi], hemi)
        plt.suptitle(f'{rean}, {hemi}, {obs_firstyr}-{obs_lastyr}', fontsize=20)
        fig.savefig(levcorr_plot)

except Exception as exc:
    print('*** Unable to create plots from the observational data: ')
    print(traceback.format_exc())
    print(exc)

print('\n=====================================')
print('END stc_eddy_heat_fluxes.py ')
print('=====================================\n')
