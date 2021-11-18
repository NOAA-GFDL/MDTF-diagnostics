# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_CircComps_util.py
#
#    Provide functions called by TempExtDistShape_CircComps.py as part of temp_extremes_distshape.py
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape  Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
# Including:
#   (1) Seasonal_Subset
#   (2) Variable_Anomaly
#   (3) Labfunc
#   (4) Circ_Comp_Lag
#   (5) Plot_Circ_Comp_Lags
#   (6) Set_Colorbars
#   (7) shiftgrid
#   (8) Lag_Correct
#
# ======================================================================

# Import standard Python packages
import os
import numpy
from netCDF4 import Dataset,num2date
from datetime import datetime, timedelta
import cftime
import matplotlib
import matplotlib.pyplot as mplt
from matplotlib import cm
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy
import cartopy.crs as ccrs
from scipy import signal
from mpl_toolkits.axes_grid1 import make_axes_locatable

# ======================================================================
### Seasonal_Subset
### For reading in variables from netcdf file and computing seasonal subset
# -----  model_netcdf_file is string name of directory location of netcdf file to read in data
# -----  lon_var,lat_var,field_var,time_var are string names of longitude, latitude, variable, and time in netcdf file
# -----  monthsub is array of months (integers) for seasonal analysis
# -----  yearbeg and yearend are range of years for analysis
# ---------  Output is variable subset to season specified, units, longitude and latitude arrays, and time array
def Seasonal_Subset(model_netcdf_filename,lon_var,lat_var,field_var,time_var,monthsub,yearbeg,yearend):
    var_netcdf=Dataset(model_netcdf_filename,"r")
    lon=numpy.asarray(var_netcdf.variables[lon_var][:],dtype="float")
    lat=numpy.asarray(var_netcdf.variables[lat_var][:],dtype="float")
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
    leapstr = numpy.array([t.strftime('%m-%d') for t in list(datecf)])
    yearind = numpy.where(numpy.logical_and(yr>=yearbeg, yr<=yearend))[0]

    print("### DEBUG CircComps_util")
    print("### yearbeg: {}, yearend: {}, yearind: {}".format(yearbeg,yearend,yearind))
    print("### var_data: {} {}; {} bytes".format(var_data.dtype, var_data.shape, var_data.nbytes))
    var_data=var_data[:,:,yearind]
    print("### var_data: {} {}; {} bytes".format(var_data.dtype, var_data.shape, var_data.nbytes))
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
    return var_data,lon,lat,leapstr,varunits

# ======================================================================
### Variable_Anomaly
### For computing variable anomaly by removing daily climatology
# -----  var_data, lon, lat, datearrstr are variable, longitude, latitude, and date arrays output from Seasonal_Subset function above
# ---------  Output is variable anomaly array
def Variable_Anomaly(var_data,lon,lat,datearrstr):
    days_uniq=numpy.unique(datearrstr)
    var_anom=numpy.empty(var_data.shape)
    dayinds=[numpy.where(datearrstr==dd)[0] for dd in days_uniq]
    for begval in numpy.arange(0,len(dayinds)):
        var_clim=numpy.mean(var_data[:,:,dayinds[begval]],axis=2)
        var_clim=var_clim.reshape(var_clim.shape[0],var_clim.shape[1], 1)
        var_anom[:,:,dayinds[begval]]=var_data[:,:,dayinds[begval]]-var_clim
    return var_anom

# ======================================================================
### Labfunc
### For plotting contour labels with decimal places when warranted, otherwise integers
def Labfunc(x):
    labfmt="%.4f" % x
    stript=labfmt.rstrip('0').rstrip('.')
    labfmt_fin=('%s' % (stript))
    return labfmt_fin

# ======================================================================
### Circ_Comp_Lag
### For computing circulation composites at time lags from day identified in tail of Non-Gaussian distribution
# -----  T2Manom_data, T2M_data are two-meter temperature data subset to season specified
# -----  SLP_data is sea level pressure data subset to season specified
# -----  Z500_data, Z500anom_data are 500hPa geopotential height data subset to season specified
# -----  T2M_units, SLP_units, Z500_units are units of variables as string
# -----  lat and lon are latitude longitude arrays output from Seasonal_Subset function above
# -----  ptile is percentile to define tail of distribution of interest
# -----  statlat and statlon are coordinates for station specified
# -----  lagtot and lagstep are for looping over the lags (in days) prior to t=0: days identified in tail of distribution
# ---------  Output is adjusted data and units for T2M, SLP, and Z500, index of lon/lat coordinate of station, and index of days in the tail for lag times specified
def Circ_Comp_Lags(T2Manom_data,T2M_data,T2M_units,SLP_data,SLP_units,Z500_data,Z500_units,lat,lon,ptile,statlat,statlon,lagtot,lagstep):
    ### Convert sea level pressure to units of hPa (mb) and two-meter temperature to units of degrees Celsius
    if SLP_units == 'Pa':
        SLP_data=numpy.true_divide(SLP_data,100)
    if T2M_units == 'K':
        T2M_data=T2M_data-273
    SLP_units='hPa'
    T2M_units=u"\u00b0"+'C'
    Z500_units='m'

    ### Detrend just two-meter temperature anomaly
    T2Manom_data=signal.detrend(T2Manom_data,axis=2,type='linear')

    ### Determine grid cell closest to chosen station
    statlatind=numpy.argmin(numpy.abs(lat-statlat))
    statlonind=numpy.argmin(numpy.abs(lon-statlon))

    ### Subset temperature anomaly to this grid cell to compute tail days based on percentile threshold
    Tanom_stat=numpy.squeeze(T2Manom_data[statlonind,statlatind,:])

    ### Compute percentile to focus on chosen tail (ptile) of temperature anomaly distribution
    pthresh=numpy.nanpercentile(Tanom_stat,ptile,interpolation='midpoint')

    ### Find days above/below percentile threshold
    # -----  Loop over lags (in days) from t=0, the day of a temperature anomaly above/below threshold at station
    tail_days_lags=[]
    for lag in numpy.arange(0,lagtot+lagstep,lagstep):
        figstep=lag/2
        if ptile < 50:
            tail_days=numpy.where(Tanom_stat<pthresh)[0]
        elif ptile > 50:
            tail_days=numpy.where(Tanom_stat>pthresh)[0]
        tail_days_lag=tail_days-lag
        tail_days_lag[tail_days_lag>=0] #in case lag index values are negative indicating a 'tail_day' is the first day in the record
        tail_days_lags.append(tail_days_lag)
    return tail_days_lags,statlonind,statlatind,T2M_data,SLP_data,Z500_data,Z500_units,SLP_units,T2M_units

# ======================================================================
### Plot_Circ_Comp_Lags
### For plotting composite circulation maps on specific days based on non-Gaussian tail of temperature anomaly distribution. Inputs are as follows:
# -----  model_netcdf_filename is data filename and lon_var is longitude string to read in longitude array
# -----  figstep is the subplot, plotcol is the column (one per variable)
# -----  lon, lat are longitude & latitude arrays output from Seasonal_Subset function above
# -----  tail_days_lags are days in the tail at lag times output from Circ_Comp_Lags function above
# -----  var_data and var_anomdata are variable data and anomaly
# -----  var_name is the string name of the variable
# -----  minval, maxval, and step are for plotting levels
# -----  lag is the number of days prior to t=0
# -----  anomminval, anommaxval, and anomrangestep are contour levels of anomalies
# -----  statlonind and statlatind are indices for coordinates of location
# -----  axes is provided as figure handle, defined prior to loop that calls function
# ---------  Output is plotted variable handle for input to Set_Colorbars function below
def Plot_Circ_Comp_Lags(model_netcdf_filename,lon_var,figstep,plotcol,lon,lat,tail_days_lag,var_data,varanom_data,var_name,minval,maxval,step,lag,anomminval,anommaxval,anomrangestep,statlonind,statlatind,axes,fig):
    ### Subset variables to only days in tail for lag time specified
    var_lag=numpy.mean(var_data[:,:,tail_days_lag],axis=2).transpose(1,0)

    ### For setting plotting bounds below, centered on location/grid point ###
    lonloc=lon[statlonind]
    latloc=lat[statlatind]
    pltlonmin=lonloc-60 if (lonloc-60>-180) else -180
    pltlonmax=lonloc+60 if (lonloc+60<180) else 180
    pltlatmax=latloc+30 if (latloc+30<90) else 90
    pltlatmin=latloc-30 if (latloc-30>-90) else -90
    axes[figstep,plotcol].set_extent([pltlonmin,pltlonmax,pltlatmin,pltlatmax])

    ### Read in lons directly from model and use shiftdata function to avoid wrapping while plotting (and align latitudes with land borders)
    var_netcdf=Dataset(model_netcdf_filename,"r")
    lon_shift=numpy.asarray(var_netcdf.variables[lon_var][:],dtype="float")
    lon_shift=lon_shift - numpy.true_divide((lon_shift[2]-lon_shift[1]),2)
    lat=lat - numpy.true_divide((lat[2]-lat[1]),2)

    if plotcol % 2 == 0:
        ### Standardize and subset temperature and geopotential height anomalies to only lag days
        anom_std=numpy.std(varanom_data,axis=2,ddof=1)
        anom_stand=numpy.true_divide(varanom_data,anom_std.reshape(anom_std.shape[0],anom_std.shape[1],1))
        var_laganom=numpy.mean(anom_stand[:,:,tail_days_lag],axis=2).transpose(1,0)

        ### Shiftdata for wrapping problem
        if lon_shift[lon_shift>180].size>0: #0 to 360 grid
            var_lag,xx = shiftgrid(180.,var_lag,lon_shift,start=False)
            var_laganom,lon_shift = shiftgrid(180.,var_laganom,lon_shift,start=False)

        ### Plot data
        lonmesh,latmesh = numpy.meshgrid(lon_shift,lat)
        t1 = axes[figstep,plotcol].pcolormesh(lonmesh,latmesh,var_lag,vmin=minval,vmax=maxval,linewidth=0,rasterized=True,zorder=1,transform=cartopy.crs.PlateCarree())
        t3 = axes[figstep,plotcol].contour(lonmesh,latmesh,var_laganom,levels=numpy.arange(anomminval,anommaxval+anomrangestep,anomrangestep),colors='red',zorder=2,transform=cartopy.crs.PlateCarree())
        cls = mplt.clabel(t3,t3.levels[:],fmt=Labfunc,colors='red')
        if cls is None:
            cls = []
        [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=0)) for txt in cls]
    else:
        ### Shiftdata for wrapping problem
        if lon_shift[lon_shift>180].size>0: #0 to 360 grid
            var_lag,lon_shift = shiftgrid(180.,var_lag,lon_shift,start=False)

        ### Plot data
        lonmesh,latmesh = numpy.meshgrid(lon_shift,lat)
        t1 = axes[figstep,plotcol].contour(lonmesh,latmesh,var_lag,levels=numpy.arange(minval,maxval+step,step),zorder=2,transform=cartopy.crs.PlateCarree())

    ### Star location and add text boxes for variable and lag day strings
    t2 = axes[figstep,plotcol].plot(lonloc,latloc,marker='*',color='m',linewidth=40,markersize=10,zorder=4,transform=cartopy.crs.PlateCarree())

    ### Add coastlines and lake boundaries
    axes[figstep,plotcol].add_feature(cartopy.feature.COASTLINE,zorder=1,linewidth=1)
    axes[figstep,plotcol].add_feature(cartopy.feature.LAKES,zorder=1,linewidth=1,edgecolor='k',facecolor='none')

    axes[figstep,plotcol].text(0.02, 0.92, var_name, bbox=dict(facecolor='white', alpha=0.8),fontsize=14,transform=axes[figstep,plotcol].transAxes,zorder=5)
    if lag == 0:
        axes[figstep,plotcol].text(0.93, 0.92,'t='+str(lag), bbox=dict(facecolor='white', alpha=0.8),fontsize=14,style='italic',transform=axes[figstep,plotcol].transAxes,zorder=6)
    else:
        axes[figstep,plotcol].text(0.92, 0.92,'t=-'+str(lag), bbox=dict(facecolor='white', alpha=0.8),fontsize=14,style='italic',transform=axes[figstep,plotcol].transAxes,zorder=6)

    ### Adjust for inserting colorbar
    divider2 = make_axes_locatable(axes[figstep,plotcol])
    cax2 = divider2.append_axes(position="bottom",size="3%",pad=0.1,map_projection=cartopy.crs.PlateCarree())
    cax2.outline_patch.set_visible(False)
    axes[figstep,plotcol].set_aspect('equal')
    return t1


# ======================================================================
### Set_Colorbars
### For formatting colorbars in figure
# -----  minval,  maxval, and cbarstep are colorbar range & step for variable plotted
# -----  t is the handle for the plotted data from Plot_Circ_Comp_Lags function above
# -----  figstep is the subplot, and plotcol is the column (one per variable)
# -----  var_units is colorbar unit string for variable plotted
# -----  axes and fig are figure handles, defined prior to loop that calls function
def Set_Colorbars(minval,maxval,cbarstep,t,figstep,plotcol,var_units,axes,fig):
    norm=mcolors.Normalize(vmin=minval, vmax=maxval)
    sm=cm.ScalarMappable(norm=norm, cmap=t.cmap)
    sm.set_array([])
    cax2 = inset_axes(axes[figstep,plotcol],width="90%",height="5%",loc='lower center',bbox_to_anchor=(0, -0.1, 1, 1),bbox_transform=axes[figstep,plotcol].transAxes,borderpad=0,)
    cbar=fig.colorbar(sm,label=var_units,orientation='horizontal',cax=cax2,pad=0.1,ticks=numpy.arange(int(minval),int(maxval)+cbarstep,cbarstep))
    cbar.ax.set_xticklabels(numpy.arange(int(minval),int(maxval)+cbarstep,cbarstep))

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
### Lag_Correct
### For removing days that fall outside the specified season
# -----  lag, figstep specified by for loop
# -----  tail_days_lags is the indices for finding the days in the tail at each lag step
# -----  datearrstr is the array of date strings
# -----  lagstep is the user-specified step in days (default=2)
# -----  monthsub is the array of months associated with the season
def Lag_Correct(lag,figstep,tail_days_lags,datearrstr,lagstep,monthsub):
    ### Correct for lags outside season
    if lag == 0:
        newtailinds=tail_days_lags[figstep]
    else:
        datelag=datearrstr[tail_days_lags[figstep-1]]
        realdate=[(datetime.strptime(dd,'%m-%d') - timedelta(days=lagstep)) for dd in datelag]
        realdatefix=[rr.replace(2000) for rr in realdate]
        realmonths=numpy.array([t.strftime('%m') for t in list(realdatefix)])
        badmonth=monthsub[0]-1
        badmonth='{0:02d}'.format(badmonth)
        badinds=numpy.where(realmonths==str(badmonth))
        newtailinds=numpy.delete(tail_days_lags[figstep],badinds)
    return newtailinds
