# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_ShiftRatio_util.py
#
#   Provide functions called by TempExtDistShape_ShiftRatio.py as part of TempExtDistShape_MDTF.py
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
# Including:
#   (1) Region_Mask
#   (2) Seasonal_Anomalies
#   (3) ShiftRatio_Calc
#   (4) ShiftRatio_Plot
#
# ======================================================================

# Import standard Python packages
import os
import numpy
from netCDF4 import Dataset,num2date
import cftime
import matplotlib.pyplot as mplt
from matplotlib import cm
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.interpolate import NearestNDInterpolator
import scipy
import cartopy
from scipy import io
from scipy import signal

# ======================================================================
### Region_Mask
### Generate a map of values corresponding to land regions in the file MERRA2_landmask.mat
# -----  region_mask_filename and model_netcdf_filename are string names referring to directory locations of mask and model data
# -----  lon_var, lat_var are longitude and latitude variable names for reading in model data
# ---------  Output is mask of region

def Region_Mask(region_mask_filename,model_netcdf_filename,lon_var,lat_var):
    ### Load & pre-process region mask
    print("   Generating region mask...")
    matfile=scipy.io.loadmat(region_mask_filename)
    lat_m=matfile["lats"]
    lon_m=matfile["lons"]
    msk=matfile["mask"]
    lon_m=numpy.append(lon_m,numpy.reshape(lon_m[0,:],(-1,1))+360,0)
    lon_m=numpy.append(numpy.reshape(lon_m[-2,:],(-1,1))-360,lon_m,0)
    msk=numpy.append(msk,numpy.reshape(msk[0,:],(-1,lat_m.size)),0)
    msk=numpy.append(numpy.reshape(msk[-2,:],(-1,lat_m.size)),msk,0)
    LAT,LON=numpy.meshgrid(lat_m,lon_m,sparse=False,indexing="xy")
    LAT=numpy.reshape(LAT,(-1,1))
    LON=numpy.reshape(LON,(-1,1))
    mask_region=numpy.reshape(msk,(-1,1))
    LATLON=numpy.squeeze(numpy.array((LAT,LON)))
    LATLON=LATLON.transpose()
    regMaskInterpolator=NearestNDInterpolator(LATLON,mask_region)

    ### Interpolate Region Mask onto Model Grid using Nearest Grid Value
    t2m_netcdf=Dataset(model_netcdf_filename,"r")
    lon=numpy.asarray(t2m_netcdf.variables[lon_var][:],dtype="float")
    lat=numpy.asarray(t2m_netcdf.variables[lat_var][:],dtype="float")
    t2m_netcdf.close()

    ### Fix longitudes so values range from -180 to 180
    if lon[lon>180].size>0:
        lon[lon>180]=lon[lon>180]-360
    LAT,LON=numpy.meshgrid(lat,lon,sparse=False,indexing="xy")
    LAT=numpy.reshape(LAT,(-1,1))
    LON=numpy.reshape(LON,(-1,1))
    LATLON=numpy.squeeze(numpy.array((LAT,LON)))
    LATLON=LATLON.transpose()
    mask_region=numpy.zeros(LAT.size)
    for latlon_idx in numpy.arange(mask_region.shape[0]):
        mask_region[latlon_idx]=regMaskInterpolator(LATLON[latlon_idx,:])
    mask_region=numpy.reshape(mask_region,(-1,lat.size))
    mask_region[mask_region!=1]=numpy.nan
    print("...Generated!")
    return mask_region

# ======================================================================
### Seasonal_Anomalies
### Read in two-meter temperature variable from netcdf file and compute seasonal anomalies
# -----  model_netcdf_filename is string name of directory location of netcdf file to be opened
# -----  lon_var,lat_var,field_var,time_var are string names of longitude, latitude, variable, and time in netcdf file
# -----  monthsub is array of months (integers) for seasonal analysis
# -----  yearbeg and yearend of range of years for analysis
# ---------  Output is two-meter temperature seasonal anomalies, longitude, and latitude arrays
def Seasonal_Anomalies(model_netcdf_filename,lon_var,lat_var,field_var,time_var,monthsub,yearbeg,yearend):
    var_netcdf=Dataset(model_netcdf_filename,"r")
    lat=numpy.asarray(var_netcdf.variables[lat_var][:],dtype="float")
    lon=numpy.asarray(var_netcdf.variables[lon_var][:],dtype="float")
    var_data=numpy.asarray(var_netcdf.variables[field_var][:],dtype="float") #time, lat, lon
    datatime=numpy.asarray(var_netcdf.variables[time_var][:],dtype="float")
    timeunits=var_netcdf.variables[time_var].units
    varunits=var_netcdf.variables[field_var].units
    caltype=var_netcdf.variables[time_var].calendar
    var_netcdf.close()

    ### Fix longitudes so values range from -180 to 180
    if lon[lon>180].size>0:
        lon[lon>180]=lon[lon>180]-360

    ### Reshape data to [lon, lat, time] dimensions for code to run properly
    if len(var_data.shape) == 4:
        var_data=numpy.squeeze(var_data)
    if var_data.shape == (len(lon),len(lat),len(datatime)):
        var_data=var_data
    elif var_data.shape == (len(lat),len(datatime),len(lon)):
        var_data=numpy.transpose(var_data,(2,0,1))
    elif var_data.shape == (len(lon),len(datatime),len(lat)):
        var_data=numpy.transpose(var_data,(0,2,1))
    elif var_data.shape == (len(datatime),len(lon),len(lat)):
        var_data=numpy.transpose(var_data,(1,2,0))
    elif var_data.shape == (len(lat),len(lon),len(datatime)):
        var_data=numpy.transpose(var_data,(1,0,2))
    elif var_data.shape == (len(datatime),len(lat),len(lon)):
        var_data=numpy.transpose(var_data,(2,1,0))

    ### Subset temperature to time range specified by "yearbeg,yearend" values
    datecf=[cftime.num2date(t,units=timeunits,calendar=caltype) for t in datatime]
    date= numpy.array([T.strftime('%Y-%m-%d') for T in list(datecf)]) #this converts the arrays of timesteps output above to a more readable string format
    mo=numpy.array([int('{0.month:02d}'.format(t)) for t in list(datecf)])
    yr=numpy.array([int('{0.year:04d}'.format(t)) for t in list(datecf)])
    leapstr = numpy.array(['{0.month:2d}-{0.day:2d}'.format(t) for t in list(datecf)])
    yearind = numpy.where(numpy.logical_and(yr>=yearbeg, yr<=yearend))[0]
    var_data=var_data[:,:,yearind]
    datecf=numpy.array(datecf)
    datecf=datecf[yearind]
    leapstr=leapstr[yearind]
    mo=mo[yearind]
    yr=yr[yearind]

    ### Subset temperature to season specified by "monthsub" vector
    moinds=numpy.in1d(mo,monthsub)
    moinds=(numpy.where(moinds)[0])
    moinds=[numpy.int(indval) for indval in moinds]
    leapstr=leapstr[moinds]
    var_data=var_data[:,:,moinds]
    datecf=datecf[moinds]

    ### Remove leap days
    dateind=(leapstr != '02-29')
    leapstr=leapstr[dateind]
    var_data=var_data[:,:,dateind]
    datecf=datecf[dateind]

    ### Compute temperature anomaly
    days_uniq=numpy.unique(leapstr)
    var_anom=numpy.empty(var_data.shape)
    dayinds=[numpy.where(leapstr==dd)[0] for dd in days_uniq]
    for begval in numpy.arange(0,len(dayinds)):
        temp_clim=numpy.mean(var_data[:,:,dayinds[begval]],axis=2)
        temp_clim=temp_clim.reshape(temp_clim.shape[0],temp_clim.shape[1], 1)
        var_anom[:,:,dayinds[begval]]=var_data[:,:,dayinds[begval]]-temp_clim
    return var_anom,lon,lat

# ======================================================================
### ShiftRatio_Calc
### Compute shift ratio of Non-Gaussian to Gaussian distribution tails specified using "ptile" percentile
# -----  ptile is percentile to define tail of distribution of interest
# -----  shift is the value used to shift the distribution as a warming scenario
# -----  msk is output from Region_Mask function, masking to land grid cells
# -----  T2Manom_data is two-meter temperature anomaly data output from Seasonal_Anomalies function above
# -----  lon and lat are longitude and latitude arrays output from Seasonal_Anomalies function above
# ---------  Output is global shift ratio array
def ShiftRatio_Calc(ptile,shift,msk,T2Manom_data,lon,lat):
    print("   Computing underlying-to-Gaussian distribution shift ratio...")

    ### Detrend temperature anomaly data output from Seasonal_Anomalies function
    T2Manom_data=signal.detrend(T2Manom_data,axis=2,type='linear')

    ### Mask temperature array by cloning 2D lon-lat mask array output from Mask_Region function to size of temperature array in time dimension
    masked_T2M_anom = T2Manom_data*(numpy.repeat(msk[:,:,numpy.newaxis], T2Manom_data.shape[2], axis=2))

    ### Extract the "ptile" percentile of the temperature anomaly distribution
    pthresh=numpy.percentile(masked_T2M_anom,ptile,axis=2,interpolation='midpoint') #size lon-lat; midpoint to match matlab percentile function interpolation scheme

    ### Compute number of days exceeding pthresh after shift
    # -----  Loop through each grid cell where 'thrshold[iloncell,ilatcell]' is the percentile threshold 'pthresh' of the two-meter temperature anomaly distribution at grid cell defined by its longitude-latitude coordinate
    if ptile < 50:
        exceedances=numpy.array([[len(numpy.where((masked_T2M_anom[iloncell,ilatcell,:]+shift*numpy.std(masked_T2M_anom[iloncell,ilatcell,:],ddof=1))<pthresh[iloncell,ilatcell])[0]) if ~numpy.isnan(pthresh[iloncell,ilatcell]) else numpy.nan for ilatcell in numpy.arange(0,len(lat))] for iloncell in numpy.arange(0,len(lon))])
    elif ptile > 50:
        exceedances=numpy.array([[len(numpy.where((masked_T2M_anom[iloncell,ilatcell,:]+shift*numpy.std(masked_T2M_anom[iloncell,ilatcell,:],ddof=1))>pthresh[iloncell,ilatcell])[0]) if ~numpy.isnan(pthresh[iloncell,ilatcell]) else numpy.nan for ilatcell in numpy.arange(0,len(lat))] for iloncell in numpy.arange(0,len(lon))])

    ### Convert exceedances into percentages by dividing by total number of days and multiplying by 100
    exceedances=numpy.divide(exceedances,masked_T2M_anom.shape[2])*100

    ### Set zeros to NaNs
    exceedances=exceedances.astype(float)
    exceedances[exceedances==0]=numpy.nan

    ### Draw random samples from Gaussian distribution the length of the time dimension, and repeat 10000 times
    # -----  Compute 5th & 95th percentiles of random gaussian distribution shift to determine statistical significance of shift ratio
    gauss_exceedances=[]
    for reps in numpy.arange(0,10000):
        randsamp=numpy.random.randn(masked_T2M_anom.shape[2])
        randsamp_shift=randsamp+(numpy.std(randsamp,ddof=1)*shift)
        gauss_pthresh=numpy.percentile(randsamp,ptile,interpolation='midpoint')
        if ptile < 50:
                excd_inds=randsamp_shift[randsamp_shift<gauss_pthresh]
        elif ptile > 50:
                excd_inds=randsamp_shift[randsamp_shift>gauss_pthresh]
        gauss_exceedances.append(numpy.true_divide(len(excd_inds),len(randsamp)))
    gaussp5=numpy.percentile(gauss_exceedances,5,interpolation='midpoint')*100
    gaussp95=numpy.percentile(gauss_exceedances,95,interpolation='midpoint')*100
    gaussp50=numpy.percentile(gauss_exceedances,50,interpolation='midpoint')*100

    ### Find where exceedance percentiles are outside the 5th and 95th percentile of the random gaussian distribution
    # -----  Where values are not outside the 5th/95th percentiles, set to NaN
    # -----  Remaining grid cells are statistically significantly different from a Gaussian shift
    print("### DEBUG ShiftRatio_util")
    print("### gaussp5: {}, gaussp95: {}".format(gaussp5,gaussp95))
    print("### exceedances: {} {}; {} bytes".format(exceedances.dtype, exceedances.shape, exceedances.nbytes))

    exceedances[(exceedances>gaussp5)&(exceedances<gaussp95)]=numpy.nan

    print("### exceedances: {} {}; {} bytes".format(exceedances.dtype, exceedances.shape, exceedances.nbytes))

    ### Compute ratio of exceedances from non-Gaussian shift to median (50th percentile) of shifts from randomly generated Gaussian distributions
    shiftratio=numpy.true_divide(exceedances,numpy.ones_like(exceedances)*gaussp50).transpose(1,0)
    print("...Computed!")
    return shiftratio

# ======================================================================
### ShiftRatio_Plot
### Plot shift ratio of underlying-to-Gaussian distribution tails
# -----  model_netcdf_filename is data filename and lon_var is longitude string to read in longitude array
# -----  colormap_file is Matlab file specifying colormap for plotting
# -----  lat is latitude array output from Seasonal_Anomalies function above
# -----  shiftratio is computed from ShiftRatio_Calc function above
# -----  monthstr is string referring to months of seasonal analysis
# -----  ptile is percentile to define tail of distribution of interest
# -----  fig_dir and fig_name are location to save figure output
def ShiftRatio_Plot(model_netcdf_filename,lon_var,colormap_file,lat,shiftratio,monthstr,ptile,fig_dir,fig_name):
    print("   Plotting shift ratio...")
    if ptile < 50:
        cmap_name='ShiftRatio_cold'
    elif ptile > 50:
        cmap_name='ShiftRatio_warm'
    colormaps=scipy.io.loadmat(colormap_file)
    mycmap=mcolors.LinearSegmentedColormap.from_list('my_colormap', colormaps[cmap_name])
    fig=mplt.figure(figsize=(10,10))
    ax=mplt.axes(projection=cartopy.crs.PlateCarree())
    ax.set_extent([-180,180,-60,90], crs=ax.projection)

    ### Read in longitude directly from model and use shiftdata function to avoid wrapping while plotting (and align latitudes with land borders)
    var_netcdf=Dataset(model_netcdf_filename,"r")
    lon=numpy.asarray(var_netcdf.variables[lon_var][:],dtype="float")
    if lon[lon>180].size>0: #0 to 360 grid
         shiftratio,lon = shiftgrid(180.,shiftratio,lon,start=False)
    lat=lat - numpy.true_divide((lat[2]-lat[1]),2)
    lon=lon - numpy.true_divide((lon[2]-lon[1]),2)
    if ptile < 50:
        p1=mplt.pcolormesh(lon,lat,numpy.log10(shiftratio),cmap=mycmap,vmin=numpy.log10(0.125),vmax=numpy.log10(2),transform=ax.projection)
    elif ptile > 50:
        p1=mplt.pcolormesh(lon,lat,numpy.log10(shiftratio),cmap=mycmap,vmin=numpy.log10(0.5),vmax=numpy.log10(2),transform=ax.projection)

    ### Add coastlines and lake boundaries
    ax.add_feature(cartopy.feature.COASTLINE,zorder=1,linewidth=0.7)
    ax.add_feature(cartopy.feature.LAKES,zorder=1,linewidth=0.7,edgecolor='k',facecolor='none')

    ### Create individual colorbars per subplot
    ax.set_aspect('equal')
    cax2 = inset_axes(ax,width="100%", height="15%",loc='lower center',bbox_to_anchor=(0,-0.05,1,0.3),bbox_transform=ax.transAxes,borderpad=0)
    if ptile < 50:
        cbar=mplt.colorbar(p1,cax=cax2,orientation='horizontal',ticks=[numpy.log10(0.125),numpy.log10(0.25),numpy.log10(0.5),numpy.log10(1),numpy.log10(2)])
        cbar.ax.set_xticklabels(['1/8','1/4','1/2','1','2'])
    elif ptile > 50:
        cbar=mplt.colorbar(p1,cax=cax2,orientation='horizontal',ticks=[numpy.log10(0.5),numpy.log10(1),numpy.log10(2)])
        cbar.ax.set_xticklabels(['1/2','1','2'])
    cbar.ax.tick_params(labelsize=20)
    ax.text(0.02, 0.02, monthstr,fontsize=14,transform=ax.transAxes,weight='bold')
    fig.savefig(fig_dir+'/'+fig_name, bbox_inches="tight")

    print("...Completed!")
    print("      Figure saved as "+fig_dir+'/'+fig_name+"!")

# ======================================================================
### shiftgrid
### Shift global lat/lon grid east or west. Taken from Python 2 Basemap function
def shiftgrid(lon0,datain,lonsin,start=True,cyclic=360.0):

    #.. tabularcolumns:: |l|L|
    #==============   ====================================================
    #Arguments        Description
    #==============   ====================================================
    #lon0             starting longitude for shifted grid
    #                 (ending longitude if start=False). lon0 must be on
    #                 input grid (within the range of lonsin).
    #datain           original data with longitude the right-most
    #                 dimension.
    #lonsin           original longitudes.
    #==============   ====================================================
    #.. tabularcolumns:: |l|L|
    #==============   ====================================================
    #Keywords         Description
    #==============   ====================================================
    #start            if True, lon0 represents the starting longitude
    #                 of the new grid. if False, lon0 is the ending
    #                 longitude. Default True.
    #cyclic           width of periodic domain (default 360)
    #==============   ====================================================
    #returns ``dataout,lonsout`` (data and longitudes on shifted grid).

    if numpy.fabs(lonsin[-1]-lonsin[0]-cyclic) > 1.e-4:
        # Use all data instead of raise ValueError, 'cyclic point not included'
        start_idx = 0
    else:
        # If cyclic, remove the duplicate point
        start_idx = 1
    if lon0 < lonsin[0] or lon0 > lonsin[-1]:
        raise ValueError('lon0 outside of range of lonsin')
    i0 = numpy.argmin(numpy.fabs(lonsin-lon0))
    i0_shift = len(lonsin)-i0
    if numpy.ma.isMA(datain):
        dataout  = numpy.ma.zeros(datain.shape,datain.dtype)
    else:
        dataout  = numpy.zeros(datain.shape,datain.dtype)
    if numpy.ma.isMA(lonsin):
        lonsout = numpy.ma.zeros(lonsin.shape,lonsin.dtype)
    else:
        lonsout = numpy.zeros(lonsin.shape,lonsin.dtype)
    if start:
        lonsout[0:i0_shift] = lonsin[i0:]
    else:
        lonsout[0:i0_shift] = lonsin[i0:]-cyclic
    dataout[...,0:i0_shift] = datain[...,i0:]
    if start:
        lonsout[i0_shift:] = lonsin[start_idx:i0+start_idx]+cyclic
    else:
        lonsout[i0_shift:] = lonsin[start_idx:i0+start_idx]
    dataout[...,i0_shift:] = datain[...,start_idx:i0+start_idx]
    return dataout,lonsout

# ======================================================================
