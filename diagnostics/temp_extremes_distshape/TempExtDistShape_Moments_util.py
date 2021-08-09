# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_Moments_util.py
#
#   Provide functions called by TempExtDistShape_Moments.py as part of temp_extremes_distshape.py
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
# Including:
#   (1) Region_Mask
#   (2) Seasonal_Moments
#   (3) Moments_Plot
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
import cartopy
import scipy
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
### Seasonal_Moments
### Read in two-meter temperature variable from netcdf file and compute seasonal subset
# -----  model_netcdf_filename is string name of directory location of netcdf file to be opened
# -----  lon_var,lat_var,field_var,time_var are string names of longitude, latitude, variable, and time in netcdf file
# -----  monthsub is array of months (integers) for seasonal analysis
# -----  yearbeg and yearend of range of years for analysis
# ---------  Output is two-meter temperature seasonal data arrays, and longitude and latitude arrays
def Seasonal_Moments(model_netcdf_filename,lon_var,lat_var,field_var,time_var,monthsub,yearbeg,yearend,mask_region):
    print("   Computing seasonal temperature moments...")
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
    leapstr=leapstr[yearind]
    mo=mo[yearind]
    yr=yr[yearind]

    ### Subset temperature to season specified by "monthsub" vector
    moinds=numpy.in1d(mo,monthsub)
    moinds=(numpy.where(moinds)[0])
    moinds=[numpy.int(indval) for indval in moinds]
    leapstr=leapstr[moinds]
    var_data=var_data[:,:,moinds]

    ### Remove leap days
    dateind=(leapstr != '02-29')
    leapstr=leapstr[dateind]
    var_data=var_data[:,:,dateind]
    if varunits == 'K' or varunits == 'Kelvin':
        var_data=var_data-273

    ### Mask temperature array by cloning 2D lon-lat mask array output from Mask_Region function to size of temperature array in time dimension
    masked_T2M = var_data*(numpy.repeat(mask_region[:,:,numpy.newaxis], var_data.shape[2], axis=2))
    seas_mean=numpy.transpose(numpy.nanmean(masked_T2M,2))
    seas_std=numpy.transpose(numpy.nanstd(masked_T2M,axis=2,ddof=1))
    seas_skew=numpy.transpose(scipy.stats.skew(masked_T2M,axis=2))
    print("...Computed!")
    return seas_mean,seas_std,seas_skew,lon,lat

# ======================================================================
### Moments_Plot
### Plot mathematical moments of temperature distribution
# -----  model_netcdf_filename is data filename and lon_var is longitude string to read in longitude array
# -----  lat is latitude array output from Seasonal_Moments function above
# -----  monthstr is string referring to months of seasonal analysis
# -----  cmaps is Matlab file specifying colormap for plotting
# -----  titles and data are arrays of moments being plotted, computed from Seasonal_Moments function above
# -----  tickrange and var_units are plotting parameters specified in usp.py file
# -----  fig_dir and fig_name are location to save figure output
def Moments_Plot(model_netcdf_filename,lon_var,lat,monthstr,cmaps,titles,data,tickrange,var_units,fig_dir,fig_name):
    print("   Plotting seasonal temperature moments...")
    fig=mplt.figure(figsize=(11,13))

    ### Align latitudes with land borders
    lat=lat - numpy.true_divide((lat[2]-lat[1]),2)
    for idata in numpy.arange(0,len(cmaps)):
        ax=fig.add_subplot(int('31'+str(idata+1)),projection=cartopy.crs.PlateCarree())
        ax.set_extent([-180,180,-60,90], crs=ax.projection)

        ### Read in longitude directly from model and use shiftdata function to avoid wrapping while plotting
        var_netcdf=Dataset(model_netcdf_filename,"r")
        lon=numpy.asarray(var_netcdf.variables[lon_var][:],dtype="float")
        if lon[lon>180].size>0: #0 to 360 grid
            data_plt,lon = shiftgrid(180.,data[idata],lon,start=False)
        else:
            data_plt=data[idata]
        lon=lon - numpy.true_divide((lon[2]-lon[1]),2)

        p1=ax.pcolormesh(lon,lat,data_plt,cmap=cmaps[idata],vmin=numpy.min(tickrange[idata]),vmax=numpy.max(tickrange[idata]),linewidth=0,rasterized=True,transform=ax.projection)
        ax.add_feature(cartopy.feature.COASTLINE,zorder=10,linewidth=0.7)
        ax.add_feature(cartopy.feature.LAKES,zorder=11,linewidth=0.7,edgecolor='k',facecolor='none')
        ax.set_title(titles[idata],fontdict={'fontsize': 15, 'fontweight': 'medium'})
        ax.set_aspect('equal')

        ### Create individual colorbars per subplot
        axpos = ax.get_position()
        axpos0 = axpos.x0
        pos_x = axpos0 + axpos.width - 0.05
        cax = inset_axes(ax,width="7%", height="100%",loc='right',bbox_to_anchor=(pos_x,0,0.3,1),bbox_transform=ax.transAxes,borderpad=0)
        if idata != 2:
            cbar=fig.colorbar(p1,cax=cax,label=var_units,orientation='vertical',ticks=tickrange[idata])
        else:
            cbar=fig.colorbar(p1,cax=cax,orientation='vertical',ticks=tickrange[idata])
        cbar.set_ticklabels(tickrange[idata])
        cbar.ax.tick_params(labelsize=14)
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
