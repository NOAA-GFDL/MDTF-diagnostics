# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# NonGaussTails_FreqDist_util.py
# 
#   Provide functions called by TempExtDistShape_FreqDist.py as part of temp_extremes_distshape.py
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Diagnostics Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
# Including:
#   (1) Seasonal_Anomalies
#   (2) Gaussfit_Params
#   (3) Gaussfit_Est
#   (4) Gaussfit_Plot
#  
# ======================================================================

# Import standard Python packages
import os
import numpy
from netCDF4 import Dataset,num2date
import cftime
import matplotlib.pyplot as mplt
import math
import scipy
from scipy import io
from scipy import signal
from scipy.optimize import curve_fit

# ======================================================================
### Seasonal_Anomalies
### Read in two-meter temperature variable from netcdf file and compute seasonal anomalies
# -----  model_netcdf_filename is string name of directory location of netcdf file to be opened
# -----  lon_var,lat_var,field_var,time_var are string names of longitude, latitude, variable, and time in netcdf file
# -----  monthsub is array of months (integers) for seasonal analysis
# -----  yearbeg and yearend of range of years for analysis
# -----  statind is city index from loop calling function for each specified city 
# ---------  Output is two-meter temperature seasonal anomalies, longitude, and latitude arrays
def Seasonal_Anomalies(model_netcdf_filename,lon_var,lat_var,field_var,time_var,monthsub,yearbeg,yearend,statind):
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
    leapstr = numpy.array(['{0.month:2d}-{0.day:2d}'.format(t) for t in list(datecf)])
    yearind = numpy.where(numpy.logical_and(yr>=yearbeg, yr<=yearend))[0]
    var_data=var_data[:,:,yearind]
    leapstr=leapstr[yearind]
    mo=mo[yearind]
    yr=yr[yearind]
    
    ### Subset temperature to season specified by "monthsub" vector
    moinds=numpy.in1d(mo,monthsub[statind])
    moinds=(numpy.where(moinds)[0])
    moinds=[numpy.int(indval) for indval in moinds]
    leapstr=leapstr[moinds]
    var_data=var_data[:,:,moinds]

    ### Remove leap days
    dateind=(leapstr != '02-29')
    leapstr=leapstr[dateind]
    var_data=var_data[:,:,dateind]

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
### Gaussfit_Params
### Function to fit Gaussian distribution using two degree polynomial
# -----  y=A*exp(-(x-mu)**2/(2*sigma**2)) is Gaussian fit equation
# -----  x is the array of bin centers from the histogram
# -----  y is the array of bin counts from the histogram
# -----  Threshold h is the fraction from the maximum y height of the data (0 < h < 1)
# ---------  Output is parameters sigma, mu, and A from Gaussian fit equation
def Gaussfit_Params(x,y,h):
    ymax=max(y)
    xnew=[]
    ynew=[]
    for i in numpy.arange(0,len(x)):
        if y[i]>ymax*h:
            xnew.append(x[i])
            ynew.append(y[i])
    ylog=[math.log(yval) for yval in ynew]
    A2,A1,A0=numpy.polyfit(xnew,ylog,2)
    sigma=math.sqrt(numpy.true_divide(-1,(2*A2)))
    mu=A1*sigma**2;
    A=math.exp(A0+numpy.true_divide(mu**2,(2*sigma**2)));
    return sigma,mu,A

# ======================================================================
### Gaussfit_Est
### Estimates the Gaussian fit to the histogram of the distribution of two-meter temperature anomalies at specified station/season
# -----  T2Manom_data is 2-meter temperature anomaly data output from Seasonal_Anomalies function above
# -----  lat and lon are latitude and longitude arrays output from Seasonal_Anomalies function above
# -----  statind is city index from loop calling function for each specified location 
# -----  statlats, statlons, and citynames are arrays of city name strings and associated coordinates
# -----  binwidth is for histogram binning of temperature anomalies at each city
# ---------  Output is centers and counts of histogram bins of temperature anomaly data, fixed bin centers if gaussian fit is too wide, gaussian fit, and detrended temperature anomaly array for location
def Gaussfit_Est(T2Manom_data,lat,lon,statind,statlats,statlons,citynames,binwidth):
    print("   Estimating Gaussian fit at "+citynames[statind]+"...")
    Tanom_data=signal.detrend(T2Manom_data,axis=2,type='linear')

    ### Determine grid cell closest to chosen location
    statlatind=numpy.argmin(numpy.abs(lat-statlats[statind]))
    statlonind=numpy.argmin(numpy.abs(lon-statlons[statind]))

    ### Subset temperature anomaly to this grid cell to compute tail days based on percentile threshold
    Tanom_stat=numpy.squeeze(Tanom_data[statlonind,statlatind,:])

    ### Compute histogram - numpy.histogram outputs bin edges but require bin centers so define edges here accordingly to match count between hist and bin_edges
    xx,bin_centers=numpy.histogram(Tanom_stat,bins=numpy.arange(min(Tanom_stat)+numpy.true_divide(binwidth,2),max(Tanom_stat)+numpy.true_divide(binwidth,2),binwidth))
    bin_counts,xx=numpy.histogram(Tanom_stat,bins=numpy.arange(min(Tanom_stat),max(Tanom_stat)+binwidth,binwidth))

    ### Compute Gaussian fit parameters using polynomial
    # -----  Normalize counts, and fit to core using 0.3 of the maximum value
    # -----  See Ruff and Neelin (2012) and Loikith and Neelin (2015)
    bin_counts=numpy.true_divide(bin_counts,max(bin_counts))
    sigma,mu,A=Gaussfit_Params(bin_centers,bin_counts,0.3)

    ### If the standard deviation of the fit to the core is greater than the SD of the entire distribution, use SD of entire distribution
    if sigma > numpy.std(Tanom_stat):
        sigma=numpy.std(Tanom_stat)
        
    ### Determine Gaussian fit using equation and parameters from gaussfit_params, and bin centers from histogram
    gauss_fit=[A*math.exp(numpy.true_divide(-(x-mu)**2,2*sigma**2)) for x in bin_centers]

    ### Gaussian fit often does not extend to zero. Extend bin_centers and recompute fit to facilitate plotting
    if gauss_fit[-1]<gauss_fit[0] or gauss_fit[0]<gauss_fit[-1]:
        bin_centers_gauss=numpy.arange(bin_centers[0]-100000,bin_centers[-1]+100000,binwidth)
        gauss_fit=[A*math.exp(numpy.true_divide(-(x-mu)**2,2*sigma**2)) for x in bin_centers_gauss]
    else:
        bin_centers_gauss=bin_centers

    print("...Completed!")
    return bin_centers_gauss,bin_centers,bin_counts,gauss_fit,Tanom_stat

# ======================================================================
### Gaussfit_Plot
### Plot Gaussian fit and histogram of binned two-meter temperature anomaly data at each location
# -----  fig is figure handle from plot specified prior to loop calling function
# -----  bin_centers and bin_counts are centers and counts of histogram bins of temperature anomaly data output from Gaussfit_Est function above
# -----  bin_centers_gauss are fixed bin centers if Gaussian fit was too wide, output from Gaussfit_Est function above
# -----  gauss-fit is Gaussian fit to 2-meter temperature anomaly distribution at specified location, output from Gaussfit_Est function above
# -----  Tanom_stat is detrended 2-meter temperature anomaly data output from SeGaussfit_Est function above
# -----  ptile is percentile to define tail of distribution of interest
# -----  citynames is array of location name strings
# -----  monthstr are seasons associated with each cityname
# -----  statind is city index from loop calling function for each specified location
# -----  plotrows and plotcols are rows and columns of subplots to figure
def Gaussfit_Plot(fig,bin_centers,bin_counts,bin_centers_gauss,gauss_fit,Tanom_stat,ptile,citynames,monthstr,statind,plotrows,plotcols):
    ax=fig.add_subplot(int(str(plotrows)+str(plotcols)+str(statind+1)))
    ax.scatter(bin_centers,bin_counts,color='blue',marker='o',facecolors='none',s=13)
    ax.plot(bin_centers_gauss,gauss_fit,color='blue',linewidth=1)
    mxval=max(abs(bin_centers))
    ax.set_xlim(-mxval-numpy.nanstd(Tanom_stat),mxval+numpy.nanstd(Tanom_stat))
    ax.set_ylim(bin_counts[0]-numpy.true_divide(bin_counts[0],10),1.05)
    ax.set_yscale('log')
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(11) 
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(11)
    ax.set_title(citynames[statind],fontdict={'fontsize': 14, 'fontweight': 'heavy'})
    ax.text(0.91, 0.92, monthstr[statind],fontsize=10,transform=ax.transAxes,weight='bold')

    ### Plot binned values exceeding the percentile threshold as open circles and the rest filled
    pthresh=numpy.nanpercentile(Tanom_stat,ptile,interpolation='midpoint')
    if ptile < 50:
        pthresh_bincenters=bin_centers[bin_centers>pthresh]
        pthresh_bincounts=bin_counts[bin_centers>pthresh]
    elif ptile > 50:
        pthresh_bincenters=bin_centers[bin_centers<pthresh]
        pthresh_bincounts=bin_counts[bin_centers<pthresh]
    ax.scatter(pthresh_bincenters,pthresh_bincounts,color='blue',marker='o',facecolors='blue',s=13)
    mplt.axvline(x=0,color='blue',linewidth=1,linestyle='dashed')
    mplt.axvline(x=pthresh,color='black',linewidth=1,linestyle='dashed')

# ======================================================================
