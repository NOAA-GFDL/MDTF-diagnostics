# ==============================================================================
# MDTF Strat-Trop Coupling: QBO and ENSO stratospheric teleconnections
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: QBO and ENSO stratospheric teleconnections
# POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC QBO and ENSO stratospheric teleconnections
# Last update: 2023-10-03
#
# This script and its helper scripts (“stc_qbo_enso_plottingcodeqbo.py” and “stc_qbo_enso_plottingcodeenso.py”) do 
# calculations to assess the representation of stratospheric telconnections associated with the Quasi-Biennial
# Oscillation (QBO) and the El Nino Southern Oscillation (ENSO). This POD uses monthly 4D (time x plev x lat x lon) 
# zonal wind, 4D meridional wind, 4D temperature, 3D (time x lat x lon) sea level pressure, and 3D sea surface 
# temperature data. Coupling between the QBO and the boreal polar stratosphere takes place during boreal fall and 
# winter whereas coupling between the QBO and the austral polar stratosphere takes place mainly during austral 
# spring and summer. By default, the POD defines the QBO for NH (SH) analyses using the Oct-Nov (Jul-Aug) 5S-5N 
# 30 hPa zonal winds. The QBO is thought to influence the polar stratospheres, the so-called “polar route,” by 
# modulating the lower stratospheric (~100-50 hPa) and middle stratospheric (~20-5 hPa) mid-latitude circulation. The  
# aforementioned lower stratospheric teleconnection is also associated with a change in the strength and position of 
# the tropospheric jet; the so-called “subtropical route.” In addition, evidence continues to show that the QBO directly 
# influences the underlying tropical tropospheric circulation, referred to as the “tropical route.” These three  
# teleconnections allow the QBO to elicit surface impacts globally. Said teleconnections are visualized herein by using 
# a metric of planetary wave propagation (eddy heat flux), circulation response (zonal wind), and surface impact (sea 
# level pressure). Additionally, metrics of model QBOs (e.g., amplitude, height, width) are produced. ENSO’s coupling 
# with the polar stratospheres takes place as the amplitude of ENSO maximizes during boreal fall and winter. By 
# default, the POD defines ENSO for NH (SH) analyses using the Nov-Mar (Sep-Jan) Nino3.4 SSTs. Though ENSO’s 
# teleconnections are truly global, it interacts with the stratosphere by stimulating tropical-extratropical Rossby waves 
# that constructively interfere with the climatological extratropical stationary wave, promoting enhanced upward 
# planetary wave propagation into the stratosphere. Similar to the QBO code, ENSO’s teleconnections are visualized 
# using the eddy heat flux, the zonal wind, and the sea level pressure.
#
# Please see the references for the scientific foundations of this POD.
#
# ==============================================================================
#   Version, Contact Info, and License
# ==============================================================================
#   - Version/revision information: v1.0 (2023-10-03)
#   - PIs: Amy H. Butler, NOAA CSL & Zachary D. Lawrence, CIRES + CU Boulder /NOAA PSL
#   - Developer/point of contact: Dillon Elsbury, dillon.elsbury@noaa.gov
#   - Other contributors: Zachary D. Lawrence, CIRES + CU Boulder / NOAA PSL, 
#     zachary.lawrence@noaa.gov; Amy H. Butler, NOAA CSL
#
#  The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
# ==============================================================================
#   Functionality
# ==============================================================================
#   This POD contains three scripts. The primary script is stc_qbo_enso.py. There
#   are two helper scripts with functions used by the primary script that are  
#   called stc_qbo_enso_plottingcodeqbo.py and stc_qbo_enso_plottingcodeenso.py.
#   The primary script stc_qbo_enso.py goes through these basic steps:
#   (1) Loads in the reanalysis data and restricts the time period to 1979-2014. 
#		The 1979-2014 period is the default period, but this can be altered by
#		modifying the FIRSTYR and LASTYR environment variables, which can be 
#		specified in config_file.jsonc and the settings.jsonc.
#	(2) Computes the reanalysis ENSO indices and composities the zonal-mean zonal wind,
#		zonal-mean eddy heat flux, and sea level pressure around the El Nino and 
#		La Nina years.
#	(3) Does the same as (2), but for the QBO. The POD then produces reanalysis
#		QBO metrics. By default, the QBO indexing and QBO metrics are calculated by
#		defining the QBO at 30 hPa. This can be altered using the QBOisobar environment
#		variable defined in config_file.jsonc and settings.jsonc.
#	(4) Loads in the model data and restrics the time period to 1979-2014 by default.
# 		The vertical ("plev") axis of the 4D fields (zonal wind, meridional wind, and
#		temperature) is then modified, if necessary, to have pressure levels 
#		denoted in hPa rather than Pa, which is used in some data sets.
#	(5) Computes the model ENSO indices and composites the zonal-mean zonal wind, zonal-
#		mean eddy heat flux, and sea level pressure around the model El Nino/La Nina years.
#	(6) Runs the QBO metric code using the default definition of the QBO at 30 hPa.
#		If a QBO is detected (some models cannot simulate one), proceeds to compute 
#		model QBO indices and composite the zonal-mean zonal wind, zonal-mean eddy heat
#		flux, and sea level pressure around easterly and westerly QBO years. string
#
# ==============================================================================
#   Required programming language and libraries
# ==============================================================================
#   This POD is done fully in python, and primarily makes use of numpy and
#   xarray to read, subset, and transform the data. It also makes use of scipy to
#   calculate the fast fourier transform (FFT) of the tropical stratospheric zonal
# 	winds to identify the QBO using its frequency spectrum (20-36 months in
#	observations). matplotlib and cartopy are used for general plotting and 
#	creating map plots.
#
# ==============================================================================
#   Required model input variables
# ==============================================================================
#   This POD requires monthly-mean fields of
#   - 4D (time x plev x lat x lon) zonal wind velocity (ua, units: m/s)
#	- 4D (time x plev x lat x lon) meridional wind velocity (va, units: m/s)
#	- 4D (time x plev x lat x lon)  temperature (ta, units: Kelvin)
#	- 3D (tmee x lat x lon) sea level pressure (psl, units: Pa)
#	- 3D (time x lat x lon) sea surface temperature (tos, units: Kelvin)
#
# ==============================================================================
#   References
# ==============================================================================
#	QBO metrics related papers:
#
#	Schenzinger, Verena, et al. "Defining metrics of the Quasi-Biennial Oscillation in
#		global climate models." Geoscientific Model Development 10.6 (2017): 2157-2168
#		doi.org/10.5194/gmd-10-2157-2017
#	Richter, Jadwiga H., et al. "Progress in simulating the quasi‐biennial oscillation 
#		in CMIP models." Journal of Geophysical Research: Atmospheres 125.8 (2020): 
#		e2019JD032362. doi.org/10.1029/2019JD032362
#	Pascoe, Charlotte L., et al. "The quasi‐biennial oscillation: Analysis using ERA‐40
#		data." Journal of Geophysical Research: Atmospheres 110.D8 (2005).
#		doi.org/10.1029/2004JD004941
#
#	QBO teleconnections, surface impacts, and indexing methods
#
#	Gray, Lesley J., et al. "Surface impacts of the quasi biennial oscillation." 
#		Atmospheric Chemistry and Physics 18.11 (2018): 8227-8247.
#		doi.org/10.5194/acp-18-8227-2018
#	Rao, Jian, et al. "Southern hemisphere response to the quasi-biennial oscillation
#		in the CMIP5/6 models." Journal of Climate 36.8 (2023): 2603-2623.
#		doi.org/10.1175/JCLI-D-22-0675.1
#
#	ENSO teleconnections, surface impacts, and indexing methods
#
#	Domeisen, Daniela IV, Chaim I. Garfinkel, and Amy H. Butler. "The teleconnection
#		of El Niño Southern Oscillation to the stratosphere." Reviews of Geophysics 57.1
#		(2019): 5-47. doi.org/10.1029/2018RG000596
#	Iza, Maddalen, Natalia Calvo, and Elisa Manzini. "The stratospheric pathway of 
#		La Niña." Journal of Climate 29.24 (2016): 8899-8914.
#		doi.org/10.1175/JCLI-D-16-0230.1

import os
import xarray as xr
import numpy as np
import xesmf as xe

import matplotlib as mpl
import matplotlib.pyplot as plt

from scipy.fft import fft,fftfreq
from scipy import interpolate

from stc_qbo_enso_plottingcodeqbo import qbo_uzm
from stc_qbo_enso_plottingcodeqbo import qbo_vt
from stc_qbo_enso_plottingcodeqbo import qbo_slp

from stc_qbo_enso_plottingcodeenso import enso_uzm
from stc_qbo_enso_plottingcodeenso import enso_vt
from stc_qbo_enso_plottingcodeenso import enso_slp

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12
mpl.rcParams['hatch.color']='gray'
	
#	 return period_min, period_mean, period_max, easterly_amp, westerly_amp, qbo_amp, lowest_lev, latitudinal_extent

def qbo_metrics(ds,qbo_isobar_in_hPa):

	r""" Calculates Quasi-Biennial Oscillation (QBO) metrics for the  an input
	zonal wind dataset (dimensions = time x level x latitude x longitude)

	Parameters
	----------
	ds : `xarray.DataArray` or `xarray.Dataset`
		The input DataArray or Dataset for which to calculate QBO diagnostics for

	Returns
	-------
	period_min: scalar
		The minimum number of months comprising a full QBO cycle (a period of easterlies [EQBO]
		and westerlies [WQBO])
	
	period_mean: scalar
		The average QBO cycle (EQBO + WQBO) duration in months
	
	period_max: scalar
		The maximum QBO cycle (EQBO + WQBO) duration in months
		
	easterly_amp: scalar
		The average easterly amplitude, arrived at by averaging together the minimum latitudinally
		averaged 5S-5N 10 hPa zonal wind observation (a single month) from each QBO cycle
		
	westerly_amp: scalar
		The average westerly amplitude, arrived at by averaging together the maximum latitudinally
		averaged 5S-5N 10 hPa zonal wind observation (a single month) from every QBO cycle
		
	qbo_amp: scalar
		The total QBO amplitude, which is estimated by adding half of the mean easterly amplitude
		(easterly_amp) to half of the mean westerly amplitude (westerly_amp)
		
	lowest_lev: scalar
		The lowermost pressure level at which the the latitudinally averaged 5S-5N QBO Fourier 
		amplitude is equal to 10% of its maximum value
		
	latitudinal_extent: scalar
		The full width at half maximum of a Gaussian fit to the 10 hPa portion of the QBO 
		Fourier amplitude pressure-latitude cross section 

	Notes
	-----
	The input xarray variable ds is assumed to have a dimension named "time x lev x lat x lon." 
	E.g., if your data differs in dimension name, e.g., "latitude", use the rename method: 
		ds.rename({'latitude':'lat'})
		ds.rename({'level':'lev'})
	
	period_min is required to be >= 14 months. This requirement is used because period_min and
	period_max are the time bounds that determine which frequencies are most "QBO-like." This 
	step is needed, because say e.g., period_min was allowed to be less than 14 months and ended
	up being equal to 12 months. Then the annual cycle zonal wind variability would be deemed
	"QBO-like" and annual cycle variability would be incorporated into the QBO Fourier amplitude
	calculations, rendering the Fourier amplitude and all of the QBO spatial metrics useless.

	"""
	
	print ("Running the QBO metrics function 'qbo_metrics'")
	print (ds)
	
	if ds.lev.values[-1] > ds.lev.values[0]:
		ds = ds.reindex(lev=list(reversed(ds.lev)))
	
	qbo_defined = qbo_isobar_in_hPa # hPa
	sfc = 1000 # hPa

	# Check to see if the latitudes are organized north to south or south to north
	lat_first = ds.lat.values[0]
	lat_end = ds.lat.values[-1]

	vt = ds.ua.values
	
	# Subset for 10 hPa #
	subset = ds.sel(lev=qbo_isobar_in_hPa)

	# Select 5S-5N winds #		
	tropical_subset = subset.isel(lat = np.logical_and(subset.lat >= -5, subset.lat <= 5))

	# Latitudinally weight and averaged betwteen 5S-5N
	
	qbo = tropical_subset.mean('lat')

	# Spatial averaging
	weights = np.cos(np.deg2rad(tropical_subset.lat.values))
	interim = np.multiply(tropical_subset.ua.values,weights[np.newaxis,:])
	interim = np.nansum(interim,axis=1)
	interim = np.true_divide(interim,np.sum(weights))

	qbo.ua.values[:] = interim[:]
	
	# Smooth with five month running mean #
	
	qbo = qbo.rolling(time=5, center=True).mean()
	
	# Identify the indices corresponding to QBO phase changes (e.g., + zonal wind (westerly) -> - zonal wind (easterly))
	zero_crossings = np.where(np.diff(np.sign(qbo.ua.values)))[0]

	# Using the phase change indices, identify QBO cycles: a set of easterlies and westerlies. By doing this, #
	# the minimum/maximum/average QBO cycle duration will be retrieved. The first phase change index from #
	# zero_crossings is excluded in the event that the QBO is close to making a phase change, which would bias #
	# the QBO duration statistics low. #
	store = []
	cycles = []
	periods = []

	for i,v in enumerate(zero_crossings):

		# Append pairs of easterly/westerly winds to "store" #
		if i != 0:
			tmp = qbo.ua.values[zero_crossings[i-1]+1:zero_crossings[i]+1]
			store.append(tmp)

		# Retrieve the most recent QBO cycle (easterlies + westerlies) from store. Loop looks for even number indices. #
		# E.g., if i == 2, one set of QBO easterlies and westerlies has been appended to store already. #
		if i != 0 and i % 2 == 0:
			concat = np.concatenate((store[-2],store[-1]))

			# Inserting requirement that each cycle must be at least 14 months. No observed QBO cycle has progressed #
			# this quickly, but cycles do in the models. This requirement is essential because the minimum and maximum QBO cycle 
			# durations are used to calculate the QBO Fourier amplitude. A minimum QBO cycle duration of, say, 12 months #
			# would lead to the QBO Fourier amplitude overlapping with the annual cycle Fourier amplitude. 
			if len(concat) >= 14:		
				cycles.append(concat)
				periods.append(len(concat))

	# Retrieve the minimum/maximum/average QBO cycle duration #
	period_min = np.round(np.nanmin(periods),1)
	period_max = np.round(np.nanmax(periods),1)
	period_mean = np.round(np.nanmean(periods),1)

	print (period_min, "minimum period (months)")
	print (period_mean, "mean period (months)")
	print (period_max, "maximum period (months)")

	# Retrieve the minimum/maximum zonal wind from each QBO cycle. Averaging the minima (maxima) gives us the #
	# easterly (westerly) amplitute #
	
	easterly_amp = np.round(np.nanmean([np.nanmin(v) for v in cycles]),1)
	westerly_amp = np.round(np.nanmean([np.nanmax(v) for v in cycles]),1)

	print (easterly_amp, 'easterly amplitude')
	print (westerly_amp, 'westerly amplitude')

	# Define the 10 hPa amplitude as in Richter et al. (2020)
	qbo_amp = np.abs(easterly_amp/2) + np.abs(westerly_amp/2)
	qbo_amp = np.round(qbo_amp,1)
	print (qbo_amp, '10 hPa amplitude')

	#################################################################################################################
	# Retrieve the QBO Fourier amplitude, defined as in Pascoe et al. (2005) as the ratio of the QBO power spectrum #
	# to the power spectrum of the entire zonal wind dataset, multiplied by a metric of the zonal wind variability, #
	# the standard deviation of the zonal wind dataset. #
	#################################################################################################################

	# Standard deviation across entire zonal wind dataset #
	std = np.nanstd(vt,axis=0)

	# Define Fourier frequencies comprising data and filter for frequencies between minimum/maximum QBO cycle duration #
	freq = 1/fftfreq(len(vt))
	arr = np.where((freq > period_min) & (freq < period_max))[0]

	# FFT of entire zonal wind dataset. Square and sum Fourier coefficients. np.abs applies unneeded square root, hence #
	# np.power to power 2 is used to undo this #
	y = fft(vt,axis=0)
	amplitudes = np.power(np.abs(y)[:len(y)//2],2)

	# Calculate ratio of QBO power spectrum to full zonal wind power spectrum #
	quotients = []
	for i,v in enumerate(ds.lev.values):
		qbodata = np.nansum(amplitudes[arr,i],axis=0)
		alldata = np.nansum(amplitudes[1:,i],axis=0)
		quot = np.true_divide(qbodata,alldata)
		quotients.append(quot)
	filtered = np.array(quotients)
	
	# Ratio of the QBO power spectrum to the power #
	# spectrum of the entire model dataset (units:%) #

	vmin = 0
	vmax = 100
	vlevs = np.linspace(vmin,vmax,num=21)

	from palettable.colorbrewer.diverging import RdBu_11
	x2,y2 = np.meshgrid(ds.lat.values,ds.lev.values)

	plt.title('Ratio of QBO power spectrum\n to zonal wind spectrum (%)')
	plt.contourf(x2,y2,filtered*100,vmin=vmin,vmax=vmax,levels=vlevs,cmap='coolwarm')
	plt.semilogy()
	plt.gca().invert_yaxis()
	if np.nanmax(ds.lev.values) > 2000:
		plt.ylabel('Pressure (Pa)')
	if np.nanmax(ds.lev.values) < 2000:
		plt.ylabel('Pressure (hPa)')
	plt.xlabel('Latitude')
	plt.colorbar()

	# Retrieve the Fourier amplitude by multiplying aforementioned ratio by standard deviation of zonal wind #
	fa = np.multiply(filtered,std)

	#################################################################################################################
	# Do the Fourier amplitude calculations between 5S and 5N to retrieve spatial metrics (e.g., latitudinal width) #
	# of the QBO #
	#################################################################################################################

	# hmax fixed at 10 hPa per Richter et al. (2020, JGR) #
	hmax = np.where(ds.lev.values == qbo.lev.values)[0]

	# Retreive the indices of lats between 5S and 5N #
	lat_hits = [i for i,v in enumerate(ds.lat.values) if v >= -5 and v <=5]

	# Retrieve the Fourier amplitude profile averaged latitudinally (w/weighting) between 5S and 5N #
	weights = np.cos(np.deg2rad(ds.lat.values[lat_hits]))
	interim = np.multiply(fa[:,lat_hits],weights[np.newaxis,:])
	interim2 = np.nansum(interim,axis=1)
	height_profile = np.true_divide(interim2,np.sum(weights))

	# Retrieve half the max Fourier amplitude and 10% of the max Fourier amplitude #
	half_max = np.max(height_profile)/2
	qbo_base = np.max(height_profile)*0.1

	# Interpolate the equatorial Fourier amplitude profile to have 10000 vertical grid points, enough #
	# points so that each isobar can be selected to a one tenth of a hPa accuracy #
	f = interpolate.interp1d(ds.lev.values,height_profile)
	xnew = np.linspace(ds.lev.values[0],ds.lev.values[-1],num=10000)
	ynew = f(xnew)

	# Of the 20,000 vertical grid points, find the one corresponding to hmax. #
	hmax_idx = (np.abs(xnew - ds.lev.values[hmax])).argmin()

	# The lower and upper portions of the fourier amplitude tropical wind height profile, #
	# which has been interpolated to 10000 grid points. #
	lower_portion = ynew[:hmax_idx]
	upper_portion = ynew[hmax_idx:]

	# Same as above, but these are lists of the isobars corresponding to the above fourier amplitudes. #
	lower_portion_isobar = xnew[:hmax_idx]
	upper_portion_isobar = xnew[hmax_idx:]

	# Retrieve the indices in the upper/lower portions corresponding to half the fourier max. #
	lower_vertical_extent = (np.abs(lower_portion - half_max)).argmin()
	upper_vertical_extent = (np.abs(upper_portion - half_max)).argmin()

	# Find the upper/lower portion isboars corresponding to the half fourier max values identified above. #
	bottom = lower_portion_isobar[lower_vertical_extent]
	top =  upper_portion_isobar[upper_vertical_extent]

	# Convert the isobars into altitudes in meters. #
	bottomz = np.log(bottom/sfc)*-7000
	topz = np.log(top/sfc)*-7000

	# Obtain the vertical extent by differencing the bottomz and topz. #
	vertical_extent = (topz - bottomz)/1000
	vertical_extent = np.round(vertical_extent,1)
	print (vertical_extent, "vertical_extent")

	# Retrieve the lowest lev the QBO extends to using 10% of the maximum Fourier amplitude #
	# "lower" for CMIP6 datasets and "upper" for ERA5 reanalysis
	lowest_lev = (lower_portion_isobar[(np.abs(lower_portion - qbo_base)).argmin()])
	lowest_lev = np.round(lowest_lev,1)
	print (lowest_lev, "lowest_lev")

	##############################################################################################
	##############################################################################################
	##############################################################################################

	# Retrieve the latitudinal extent #

	# https://www.geeksforgeeks.org/python-gaussian-fit/
	xdata = ds.lat.values
	ydata = fa[hmax][0]
	ydata[0] = 0
	ydata[-1] = 0

	# Recast xdata and ydata into numpy arrays so we can use their handy features
	xdata = np.array(xdata)
	ydata = np.array(ydata)

	from scipy.optimize import curve_fit

	def gauss(x, H, A, x0, sigma):
		return H + A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

	def gauss_fit(x, y):
		mean = sum(x * y) / sum(y)
		sigma = np.sqrt(sum(y * (x - mean) ** 2) / sum(y))
		popt, pcov = curve_fit(gauss, x, y, p0=[min(y), max(y), mean, sigma])
		return popt

	out = gauss(xdata, *gauss_fit(xdata, ydata))

	f = interpolate.interp1d(ds.lat.values,out)
	xnew = np.linspace(ds.lat.values[0],ds.lat.values[-1],num=10000)
	ynew = f(xnew)

	lower_portion = ynew[:5000]
	upper_portion = ynew[5000:]

	lower_portion_lat = xnew[:5000]
	upper_portion_lat = xnew[5000:]

	lat1 = lower_portion_lat[(np.abs(lower_portion - (np.max(out)/2))).argmin()]
	lat2 = upper_portion_lat[(np.abs(upper_portion - (np.max(out)/2))).argmin()]

	latitudinal_extent = np.abs(lat1) + np.abs(lat2)
	latitudinal_extent = np.round(latitudinal_extent,1)
	
	print (latitudinal_extent, "latitudinal_extent")
	

	if period_min != period_max:
		print ('Based on period statistics, dataset is likely to have a QBO')
		qbo_switch = 1
	else:
		print ('Persistent stratospheric easterlies detected - dataset likely does not have QBO')
		qbo_switch = 0
		
	metrics = ['minimum period: %s (months)' % period_min, 
			   'mean period: %s (months)' % period_mean,
			   'maximum period: %s (months)' % period_max,
			   'easterly amplitude: %s (m/s)' % easterly_amp,
			   'westerly amplitude: %s (m/s)' % westerly_amp,
			   'QBO amplitude: %s (m/s)' % qbo_amp,
			   'lowest QBO level: %s (hPa)' % lowest_lev,
			   'vertical extent: %s (kilometers)' % vertical_extent,
			   'latitudinal extent of QBO: %s (degrees)' % latitudinal_extent]

	return metrics, qbo_switch
	
	
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
		
##################################################################################################
##################################################################################################
##################################################################################################

def qbo_indexing(ds,qbo_isobar_in_hPa,hemisphere):

	# Check to see if the latitudes are organized north to south or south to north
	lat_first = ds.lat.values[0]
	lat_end = ds.lat.values[-1]

	# Subset for 10 hPa #
	subset = ds.sel(lev=qbo_isobar_in_hPa)

	# Select 5S-5N winds #
	if lat_first > lat_end:
		tropical_subset = subset.interp(lat=[5,2.5,0,-2.5,-5])
	if lat_end > lat_first:
		tropical_subset = subset.interp(lat=[-5,-2.5,0,2.5,5])
		
	qbo = tropical_subset.mean('lat')
	
	# Latitudinally weight and average #
	weights = np.cos(np.deg2rad(tropical_subset.lat.values))
	interim = np.multiply(tropical_subset.values,weights[np.newaxis,:])
	interim = np.nansum(interim,axis=1)
	interim = np.true_divide(interim,np.sum(weights))
	qbo.values[:] = interim[:]

	# Index QBO. Sets to October-November for N. Hemisphere focused results #
	# or sets to August-September for S. Hemisphere focused results. #

	if hemisphere == 'NH':
		seasonal = qbo.sel(time=qbo.time.dt.month.isin([10,11]))
		
		qbo_raw = seasonal.values
		a = len(qbo_raw)
		qbo_raw = np.reshape(qbo_raw,(int(a/2),2))
		day_in_month_weights = np.array([31/61,30/61])[np.newaxis,:]
		tmp = np.multiply(qbo_raw,day_in_month_weights)
		tmp = np.nanmean(tmp,axis=1)

		clim = np.nanmean(tmp)
		std = np.nanstd(tmp)

		anomraw = np.subtract(tmp,clim)
		anom = np.true_divide(anomraw,std)
		
	if hemisphere == 'SH':
		seasonal = qbo.sel(time=qbo.time.dt.month.isin([7,8]))
		
		qbo_raw = seasonal.values
		a = len(qbo_raw)
		qbo_raw = np.reshape(qbo_raw,(int(a/2),2))
		day_in_month_weights = np.array([31/62,31/62])[np.newaxis,:]
		tmp = np.multiply(qbo_raw,day_in_month_weights)
		tmp = np.nanmean(tmp,axis=1)

		clim = np.nanmean(tmp)
		std = np.nanstd(tmp)

		anomraw = np.subtract(tmp,clim)
		anom = np.true_divide(anomraw,std)

	# Get the unique years from "seasonal" #
	years = set(np.sort(seasonal.time.dt.year.values))
	years = [v for v in years]

	eqbo = [i for i,v in enumerate(anom) if v <= -1]
	wqbo = [i for i,v in enumerate(anom) if v >= 1]

	eqbo_years = [years[i] for i in eqbo]
	wqbo_years = [years[i] for i in wqbo]

	return eqbo_years, wqbo_years

########################
# --- BEGIN SCRIPT --- #
########################
print('\n=======================================')
print('BEGIN stc_qbo_enso.py ')
print('=======================================\n')

# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = os.environ['FIRSTYR']
LASTYR = os.environ['LASTYR']
WK_DIR = os.environ['WK_DIR']
OBS_DATA = os.environ['OBS_DATA']
QBOisobar = os.environ['QBOisobar']

print (QBOisobar, "QBOisobar")
print (' ')

###########################################################################
################################ observations #############################
###########################################################################

print(f'*** Now working on obs data\n------------------------------')
obs_file_atm = OBS_DATA+'/stc-qbo-enso-obs-atm.nc'
obs_file_ocn = OBS_DATA+'/stc-qbo-enso-obs-ocn.nc'

print(f'*** Reading obs data from {obs_file_atm}')
obs_atm = xr.open_dataset(obs_file_atm)

print (obs_atm, 'obs_atm')

print(f'*** Reading obs data from {obs_file_ocn}')
obs_sst = xr.open_dataset(obs_file_ocn)

print (obs_sst, 'obs_sst')

# Subset the data for the user defined first and last years #

obs_atm = obs_atm.sel(time=slice(str(FIRSTYR),str(LASTYR)))
obs_sst = obs_sst.sel(time=slice(str(FIRSTYR),str(LASTYR)))

# Create the POD figures directory

plot_dir = f'{WK_DIR}/obs/'

################################################
print ('*** Running the observed ENSO indexing')
################################################

# Extract the tropical domain #
ENSO = obs_sst.isel(lat = np.logical_and(obs_sst.lat >= -5, obs_sst.lat <= 5))

# Extract date and longitude info from ENSO dataset #
date_first = obs_sst.time[0]
date_last = obs_sst.time[-1]
lon_first = ENSO.lon.values[0]

# Identify the correct ENSO longitudinal grid #
if lon_first < 0:
	ENSO = ENSO.sel(lon=slice(-170,-120))
else:
	ENSO = ENSO.sel(lon=slice(190,240))

# Latitudinally average the ENSO data #
weighted_mean = ENSO.mean('lat')
weights = np.cos(np.deg2rad(ENSO.lat.values))
interim = np.multiply(ENSO.tos.values,weights[np.newaxis,:,np.newaxis])
interim = np.nansum(interim,axis=1)
interim = np.true_divide(interim,np.sum(weights))
weighted_mean.tos.values[:] = interim[:]

def enso_index(seasonal):

    # Create 5-month seasonally averaged standardized ENSO anomalies. Weight each month by number of days comprising month #
    day_in_month_weights = seasonal.time.dt.days_in_month.values[:5]/np.sum(seasonal.time.dt.days_in_month.values[:5])
    sstindex = np.reshape(seasonal.tos.values,(int(len(seasonal.tos.values)/5),5))
    sstindex = np.nanmean(np.multiply(sstindex,day_in_month_weights[np.newaxis,:]),axis=1)
    anom = np.subtract(sstindex,np.nanmean(sstindex))
    anom = np.true_divide(anom,np.nanstd(sstindex))

    # Get the unique years from "seasonal" and then remove the last one, which is not needed
    years = [v for v in set(np.sort(seasonal.time.dt.year.values))][:-1]
    nina_years = [years[i] for i,v in enumerate(anom) if v <= -1]
    nino_years = [years[i] for i,v in enumerate(anom) if v >= 1]
    
    return nina_years, nino_years

# Subsample ENSO data for NH #
seasonal = weighted_mean.sel(time=slice('%s-11-01' % date_first.dt.year.values, '%s-03-31' % date_last.dt.year.values))
seasonal = seasonal.sel(time=seasonal.time.dt.month.isin([11,12,1,2,3])).mean('lon')
nh_nina, nh_nino = enso_index(seasonal)
seasonal.close()

# Subsample ENSO data for SH #
seasonal = weighted_mean.sel(time=slice('%s-09-01' % date_first.dt.year.values, '%s-01-31' % date_last.dt.year.values))
seasonal = seasonal.sel(time=seasonal.time.dt.month.isin([9,10,11,12,1])).mean('lon')
sh_nina, sh_nino = enso_index(seasonal)
seasonal.close()

# Store the Nina/Nino years in a dictionary to call later #
enso_dict = {}
enso_dict['NH'] = nh_nina, nh_nino
enso_dict['SH'] = sh_nina, sh_nino

hemispheres = ['NH','SH']

for hemi in hemispheres:

	###############################################
	print ('*** Calling the observed ENSO indices')
	###############################################
	obs_nina, obs_nino = enso_dict[hemi]
	
	print (obs_nina,'obs_nina')
	print (obs_nino, 'obs_nino')

	###################################################################
	print ('*** Running the observed ENSO zonal mean zonal wind calcs')
	###################################################################

	obstos_plot = f'{plot_dir}/obs-enso34-uzm-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = enso_uzm(obs_atm.ua,obs_nina,obs_nino,hemi)
	out_fig.savefig(obstos_plot,dpi=700)

	print ('*** Running the observed ENSO eddy heat flux calcs')
	obsvt_plot = f'{plot_dir}/obs-enso34-vt-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = enso_vt(obs_atm.ehf,obs_nina,obs_nino,hemi)
	out_fig.savefig(obsvt_plot,dpi=700)

	print ('*** Running the observed ENSO sea level pressure')
	obsps_plot = f'{plot_dir}/obs-enso34-psl-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = enso_slp(obs_atm,obs_nina,obs_nino,hemi)
	out_fig.savefig(obsps_plot,dpi=700)
	
	print ('*** Running the observed QBO indexing')
	obs_eqbo,obs_wqbo = qbo_indexing(obs_atm.ua,QBOisobar,'NH')

	print ('*** Running the observed QBO zonal mean zonal wind plotting')
	uzm_plot = f'{plot_dir}/obs-qbo{QBOisobar}hPa-uzm-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = qbo_uzm(obs_atm.ua,obs_eqbo,obs_wqbo,QBOisobar,hemi)
	out_fig.savefig(uzm_plot,dpi=700)

	print ('*** Running the observed QBO zonal mean eddy heat flux plotting')
	vtzm_plot = f'{plot_dir}/obs-qbo{QBOisobar}hPa-vt-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = qbo_vt(obs_atm.ehf,obs_eqbo,obs_wqbo,QBOisobar,hemi)
	out_fig.savefig(vtzm_plot,dpi=700)
	
	print ('*** Running the observed QBO sea level pressure plotting')
	psl_plot = f'{plot_dir}/obs-qbo{QBOisobar}hPa-psl-{FIRSTYR}-{LASTYR}-%s.png' % hemi
	out_fig, out_ax = qbo_slp(obs_atm,obs_eqbo,obs_wqbo,QBOisobar,hemi)
	out_fig.savefig(psl_plot,dpi=700)
	

print('*** Running the observed QBO metrics')
metricsout, switch = qbo_metrics(obs_atm,QBOisobar)

filepath = f'{plot_dir}/obs-qbo{QBOisobar}hPa-metrics-{FIRSTYR}-{LASTYR}.txt'
with open(filepath, 'w') as file_handler:
	file_handler.write(f"{'QBO metrics: periodicity and spatial characteristics'}\n")
	file_handler.write(f"{' '}\n")
	for item in metricsout:
		file_handler.write(f"{item}\n")
		

###########################################################################
################################ model #############################
###########################################################################


plot_dir = f'{WK_DIR}/model/'

# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading variables ...')

sfi = os.environ['TOS_FILE']
pfi = os.environ['PSL_FILE']
ufi = os.environ['UA_FILE']
vfi = os.environ['VA_FILE']
tfi = os.environ['TA_FILE']

tos = xr.open_dataset(sfi)
psl = xr.open_dataset(pfi)
ua = xr.open_dataset(ufi)
va = xr.open_dataset(vfi)
ta = xr.open_dataset(tfi)

# Compute the diagnostics (note, here we assume that all model variables are the same length in time)
mod_firstyr = ua.time.dt.year.values[0]
mod_lastyr = ua.time.dt.year.values[-1]
print(mod_firstyr,mod_lastyr)
print (FIRSTYR,LASTYR)

ps = psl.sel(time=slice(str(FIRSTYR),str(LASTYR)))
uas = ua.sel(time=slice(str(FIRSTYR),str(LASTYR))).mean('lon')
vas = va.sel(time=slice(str(FIRSTYR),str(LASTYR)))
tas = ta.sel(time=slice(str(FIRSTYR),str(LASTYR)))
toss = tos.sel(time=slice(str(FIRSTYR),str(LASTYR)))

print(f'***Determine whether model pressure levels are in Pa or hPa, convert to hPa')
if getattr(uas.lev,'units') == 'Pa':
	print(f'**Converting pressure levels to hPa')
	uas = uas.assign_coords({"lev": (uas.lev/100.)})
	uas.lev.attrs['units'] = 'hPa'
	vas = vas.assign_coords({"lev": (vas.lev/100.)})
	vas.lev.attrs['units'] = 'hPa'
	tas = tas.assign_coords({"lev": (tas.lev/100.)})
	tas.lev.attrs['units'] = 'hPa'

if getattr(ps.psl,'units') == 'Pa':
	print(f'**Converting pressure levels to hPa')
	ps.psl.attrs['units'] = 'hPa'
	ps.psl.values[:] = ps.psl.values/100.

# Create the POD figures directory
plot_dir = f'{WK_DIR}/model/'

hemispheres = ['NH','SH']

for hemi in hemispheres:

	print ('*** Running the model ENSO indexing')
	model_nina, model_nino = enso_indexing(toss,hemi)
	
	###############
	
	print ('*** Running the model ENSO zonal mean zonal wind calcs')
	out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-enso34-uzm-%s.png' % hemi
	out_fig, out_ax = enso_uzm(uas.ua,model_nina,model_nino,hemi)
	out_fig.savefig(out_plot,dpi=700)
	
	print ('*** Doing the model eddy heat flux calculations')
	vt = compute_total_eddy_heat_flux(vas.va,tas.ta)

	print ('*** Running the observed ENSO eddy heat flux calcs')
	out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-enso34-vt-%s.png' % hemi
	out_fig, out_ax = enso_vt(vt,model_nina,model_nino,hemi)
	out_fig.savefig(out_plot,dpi=700)

	print ('*** Running the observed ENSO sea level pressure')
	out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-enso34-psl-%s.png' % hemi
	out_fig, out_ax = enso_slp(ps,model_nina,model_nino,hemi)
	out_fig.savefig(out_plot,dpi=700)

# Prepare the output dictionaries

vt_data = {}
uzm_data = {}
slp_data = {}

# Saving some of the data #

vt_data['NH'] = vt.sel(lat = np.logical_and(vt.lat >= 0, vt.lat <= 90))
vt_data['SH'] = vt.sel(lat = np.logical_and(vt.lat >= -90, vt.lat <= 0))
vt_out   = xr.concat([vt_data['SH'], vt_data['NH']], dim='hemi')
vt_out.name = 'vt_out'
vt_out.attrs['units'] = 'Km s**-1'
vt_out.attrs['long_name'] = 'Pole to equator zonal-mean eddy heat flux'

uzm_data['NH'] = uas.ua.sel(lat = np.logical_and(uas.lat >= 0, uas.lat <= 90))
uzm_data['SH'] = uas.ua.sel(lat = np.logical_and(uas.lat >= -90, uas.lat <= 0))
uzm_out   = xr.concat([uzm_data['SH'], uzm_data['NH']], dim='hemi')
uzm_out.name = 'uzm_out'
uzm_out.attrs['units'] = 'm s**-1'
uzm_out.attrs['long_name'] = 'Pole to equator zonal-mean zonal wind'

slp_data['NH'] = ps.psl.sel(lat = np.logical_and(ps.lat >= 20, ps.lat <= 90))
slp_data['SH'] = ps.psl.sel(lat = np.logical_and(ps.lat >= -90, ps.lat <= -20))
slp_out   = xr.concat([slp_data['SH'], slp_data['NH']], dim='hemi')
slp_out.name = 'slp_out'
slp_out.attrs['units'] = 'hPa'
slp_out.attrs['long_name'] = 'Pole to 20N/S sea level pressure'

qbo_out = uas.ua.interp(lat=[-5,-2.5,0,2.5,5]).sel(lev=QBOisobar)
qbo_out.name = 'qbo_out'
qbo_out.attrs['units'] = 'm s**-1'
qbo_out.attrs['long_name'] = f'5S to 5N {QBOisobar} hPa zonal-mean zonal wind'
print (qbo_out, 'qbo_out')

out_ds = xr.merge([vt_out,uzm_out,slp_out,qbo_out])
print ('OUT_DS')
print (out_ds)
print (' ')
print (' ')

print('*** Preparing to save derived data')
data_dir = f'{WK_DIR}/model/netCDF'
outfile = data_dir+f'/{CASENAME}_qbo-enso_diagnostics.nc'

encoding = {'vt_out':  {'dtype':'float32'},
            'uzm_out':  {'dtype':'float32'},
            'slp_out':  {'dtype':'float32'},
            'qbo_out': {'dtype':'float32'}}

print(f'*** Saving qbo-enso diagnostic data to {outfile}')
out_ds.to_netcdf(outfile, encoding=encoding)
	
print('*** Running the model QBO metrics')
metricsout, switch = qbo_metrics(uas,QBOisobar)

filepath = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-qbo{QBOisobar}hPa-metrics.txt'
with open(filepath, 'w') as file_handler:
	file_handler.write(f"{'QBO metrics: periodicity and spatial characteristics'}\n")
	file_handler.write(f"{' '}\n")
	for item in metricsout:
		file_handler.write(f"{item}\n")
		
if switch == 1:

	print ("QBO detected in the model data. Making QBO Ubar, v'T', ans SLP plots.")

	for hemi in hemispheres:
	
		###############
	
		print ('*** Running the model QBO indexing')
		model_eqbo,model_wqbo = qbo_indexing(uas.ua,QBOisobar,hemi)

		print ('*** Running the model QBO zonal mean zonal wind plotting')
		out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-qbo{QBOisobar}hPa-uzm-%s.png' % hemi
		out_fig, out_ax = qbo_uzm(uas.ua,model_eqbo,model_wqbo,QBOisobar,hemi)
		out_fig.savefig(out_plot,dpi=700)

		print ('*** Running the model QBO zonal mean eddy heat flux plotting')
		out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-qbo{QBOisobar}hPa-vt-%s.png' % hemi
		out_fig, out_ax = qbo_vt(vt,model_eqbo,model_wqbo,QBOisobar,hemi)
		out_fig.savefig(out_plot,dpi=700)
	
		print ('*** Running the model QBO sea level pressure plotting')
		out_plot = f'{plot_dir}/{CASENAME}-{FIRSTYR}-{LASTYR}-qbo{QBOisobar}hPa-psl-%s.png' % hemi
		out_fig, out_ax = qbo_slp(ps,model_eqbo,model_wqbo,QBOisobar,hemi)
		out_fig.savefig(out_plot,dpi=700)
		
if switch == 0:

	print ("No QBO detected in the model data. As a result, QBO Ubar, v'T', ans SLP plots were not made.")


print('\n=====================================')
print('END stc_qbo_enso.py ')
print('=====================================\n')