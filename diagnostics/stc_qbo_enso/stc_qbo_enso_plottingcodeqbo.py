'''
This module contains functions used in the Stratospheric QBO and ENSO POD.

Contains:
	qbo_slp: plots sea level pressure response to QBO as a function of month and QBO phase
	qbo_uzm: plots the zonal-mean zonal wind response to QBO as a function of month and QBO phase
	qbo_vt: plots the zonally averaged eddy heat flux response to the QBO as a function of month and QBO phase
'''



import os
import xarray as xr
import numpy as np
import xesmf as xe

import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.path as mpath
from cartopy.util import add_cyclic_point

from scipy.fft import fft,fftfreq,ifft
from scipy import interpolate,stats
from scipy.optimize import curve_fit

##################################################################################################
##################################################################################################
##################################################################################################

def qbo_uzm(uzm,negative_indices,positive_indices,isobar,hemisphere):

	r""" Load the zonal mean zonal wind data and subsample it by QBO 
	phase or by ENSO phase. The plot will show the responses from
	October through March. Statistical significance testing is 
	done using a two-sided student's t-test and anomalies 
	corresponding to p-values <= 0.05 are deemed statistically 
	significant and stippled on the figures."""
	
	if hemisphere == 'NH':
		titles = ['October','November','December','January','February']
		plot_months = [10,11,12,1,2]
	if hemisphere == 'SH':
		titles = ['July','August','September','October','November']
		plot_months = [7,8,9,10,11]

	# Check to see if the pressure levels are in hPa or Pa
	if np.nanmax(uzm.lev.values) > 2000:
		uzm.lev.values[:] = np.true_divide(uzm.lev.values,100)

	eqbo_out = []
	wqbo_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = uzm.sel(time=uzm.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').values)

		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")

		# For NH, QBO index is based on Oct-Nov year. The plot will show Oct-Feb. Note that Jan-Feb are selected using QBO index year + 1
		# For SH, QBO index is based on Jul-Aug year. The plot will show Jul-Nov. 

		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)

		eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(eqbo_tmp.values,wqbo_tmp.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(eqbo_tmp.mean('time').values,wqbo_tmp.mean('time').values))
		eqbo_out.append(eqbo_tmp.mean('time').values)
		wqbo_out.append(wqbo_tmp.mean('time').values)

		clim.close()
		anom.close()
		eqbo_tmp.close()
		wqbo_tmp.close()
	uzm.close()

	eqbo_out = np.array(eqbo_out)
	wqbo_out = np.array(wqbo_out)
	diff_out = np.array(diff_out)
	sigs_out = np.array(sigs_out)
	clim_out = np.array(clim_out)

	############# Begin the plotting ############

	fig, ax = plt.subplots()

	mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

	vmin = -10
	vmax = 10
	vlevs = np.linspace(vmin,vmax,num=21)
	vlevs = [v for v in vlevs if v != 0]
	ticks = [vmin,vmin/2,0,vmax/2,vmax]

	cmin = -200
	cmax = 200
	clevs = np.linspace(cmin,cmax,num=41)
	clevs = [v for v in clevs if v != 0]

	plt.suptitle('QBO (5S-5N index @ %s hPa) zonal-mean zonal wind (m/s)' % int(isobar),fontsize=12,fontweight='normal')

	# Add colormap #
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()

	x, y = np.meshgrid(uzm.lat.values,uzm.lev.values)

	cols = [0,1,2,3,4]

	for i in cols:

		# eqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]))
		plt.title('%s' % titles[i],fontsize=10,y=0.93,fontweight='normal')

		cs = plt.contourf(x,y,eqbo_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')

		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)),fontsize=10)

		# wqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]))

		cs = plt.contourf(x,y,wqbo_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')
		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)),fontsize=10)

		# Diff: eqbo minus wqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]))

		cs = plt.contourf(x,y,diff_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')	
		plt.xlabel('Latitude',fontsize=8,fontweight='normal')

		sig_levs = [0.95,1]
		mpl.rcParams['hatch.linewidth'] = 0.2
		hatching = plt.contourf(x,y,sigs_out[i],colors='black',vmin=0.95,vmax=1,levels=sig_levs,hatches=['......','......'],alpha=0.0)

		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo - wqbo',fontsize=10)

	# Add colorbar #

	cb_ax = fig.add_axes([0.365, 0.04, 0.30, 0.015])
	cbar = fig.colorbar(cs, cax=cb_ax, ticks=ticks,orientation='horizontal')
	cbar.ax.tick_params(labelsize=8, width=1)
	cbar.ax.set_xticklabels(ticks,weight='normal')
	
	plt.subplots_adjust(top=0.86,bottom=0.16,hspace=0.5,wspace=0.55,left=0.08,right=0.95)
	return fig, ax

##################################################################################################
##################################################################################################
##################################################################################################

def qbo_vt(var,negative_indices,positive_indices,isobar,hemisphere):

	r""" Load the eddy heat flux data and subsample it by QBO 
	phase or by ENSO phase. The plot will show the responses from
	October through March. Statistical significance testing is 
	done using a two-sided student's t-test and anomalies 
	corresponding to p-values <= 0.05 are deemed statistically 
	significant and stippled on the figure."""

	if hemisphere == 'NH':
		titles = ['October','November','December','January','February']
		plot_months = [10,11,12,1,2]
	if hemisphere == 'SH':
		titles = ['July','August','September','October','November']
		plot_months = [7,8,9,10,11]

	# Check to see if the pressure levels are in hPa or Pa
	if np.nanmax(var.lev.values) > 2000:
		var.lev.values[:] = np.true_divide(var.lev.values,100)

	eqbo_out = []
	wqbo_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = var.sel(time=var.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').values)

		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")

		# For NH, QBO index is based on Oct-Nov year. The plot will show Oct-Feb. Note that Jan-Feb are selected using QBO index year + 1
		# For SH, QBO index is based on Jul-Aug year. The plot will show Jul-Nov. 

		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)

		eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(eqbo_tmp.values,wqbo_tmp.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(eqbo_tmp.mean('time').values,wqbo_tmp.mean('time').values))
		eqbo_out.append(eqbo_tmp.mean('time').values)
		wqbo_out.append(wqbo_tmp.mean('time').values)

		clim.close()
		anom.close()
		eqbo_tmp.close()
		wqbo_tmp.close()
	var.close()

	eqbo_out = np.array(eqbo_out)
	wqbo_out = np.array(wqbo_out)
	diff_out = np.array(diff_out)
	sigs_out = np.array(sigs_out)
	clim_out = np.array(clim_out)

	############# Begin the plotting ############

	fig, ax = plt.subplots()

	mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

	vmin = -50
	vmax = 50
	vlevs = np.linspace(vmin,vmax,num=21)
	vlevs = [v for v in vlevs if v != 0]

	vthesh = 250

	blevs = []

	blevs.append(-2)
	blevs.append(-6)
	blevs.append(-10)
	blevs.append(-25)
	blevs.append(-50)
	blevs.append(-100)

	blevs.append(2)
	blevs.append(6)
	blevs.append(10)
	blevs.append(25)
	blevs.append(50)
	blevs.append(100)

	blevs = np.sort(blevs)
	print (blevs)

	cmin = -200
	cmax = 200
	clevs = np.linspace(cmin,cmax,num=41)
	clevs = [v for v in clevs if v != 0]

	plt.suptitle('QBO (5S-5N index @ %s hPa) zonal-mean eddy heat flux (Km/s)' % int(isobar),fontsize=12,fontweight='normal')

	# Add colormap #
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()

	x, y = np.meshgrid(var.lat.values,var.lev.values)

	cols = [0,1,2,3,4]

	for i in cols:

		print (i)

		# eqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]))
		plt.title('%s' % titles[i],fontsize=10,y=0.93,fontweight='normal')

		cs = plt.contourf(x,y,eqbo_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')

		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)),fontsize=10)

		# wqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]))

		cs = plt.contourf(x,y,wqbo_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')
		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)),fontsize=10)

		# Diff: eqbo minus wqbo #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]))

		cs = plt.contourf(x,y,diff_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,5,10,100,1000]
		plt.yticks(yticks,yticks,fontsize=6,fontweight='normal')
		xticks = [-90,-60,-30,0,30,60,90]
		plt.xticks(xticks,xticks,fontsize=6,fontweight='normal')
		plt.gca().invert_yaxis()
		if hemisphere == 'NH':
			plt.axis([0,90,1000,1])
		if hemisphere == 'SH':
			plt.axis([-90,0,1000,1])
		if i == 0:
			plt.ylabel('Pressure (hPa)',fontsize=8,fontweight='normal')	
		plt.xlabel('Latitude',fontsize=8,fontweight='normal')

		sig_levs = [0.95,1]
		mpl.rcParams['hatch.linewidth'] = 0.2
		hatching = plt.contourf(x,y,sigs_out[i],colors='black',vmin=0.95,vmax=1,levels=sig_levs,hatches=['......','......'],alpha=0.0)

		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo - wqbo',fontsize=10)

	# Add colorbar #

	oticks = [-100,-50,-25,-10,-6,-2,2,6,10,25,50,100]
	cb_ax = fig.add_axes([0.365, 0.04, 0.30, 0.015])
	cbar = fig.colorbar(cs, cax=cb_ax, ticks=oticks,orientation='horizontal')
	cbar.ax.tick_params(labelsize=8, width=1)
	cbar.ax.set_xticklabels(oticks,weight='normal')

	plt.subplots_adjust(top=0.86,bottom=0.16,hspace=0.5,wspace=0.55,left=0.08,right=0.95)
	
	return fig, ax

##################################################################################################
##################################################################################################
##################################################################################################

def qbo_slp(var,negative_indices,positive_indices,isobar,hemisphere):

	if hemisphere == 'NH':
		titles = ['October','November','December','January','February']
		plot_months = [10,11,12,1,2]
	if hemisphere == 'SH':
		titles = ['July','August','September','October','November']
		plot_months = [7,8,9,10,11]
	
	if getattr(var.psl,'units') == 'Pa':
		print(f'**Converting pressure levels to hPa')
		var.psl.attrs['units'] = 'hPa'
		var.psl.values[:] = var.psl.values/100.
		
	print (np.nanmin(var.psl.values))
	print (np.nanmedian(var.psl.values))
	print (np.nanmean(var.psl.values))
	print (np.nanmax(var.psl.values))
	
	eqbo_out = []
	wqbo_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = var.sel(time=var.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').psl.values)
	
		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")
	
		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)
		
		eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(eqbo_tmp.psl.values,wqbo_tmp.psl.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(eqbo_tmp.mean('time').psl.values,wqbo_tmp.mean('time').psl.values))
		eqbo_out.append(eqbo_tmp.mean('time').psl.values)
		wqbo_out.append(wqbo_tmp.mean('time').psl.values)

		clim.close()
		anom.close()
		eqbo_tmp.close()
		wqbo_tmp.close()
	var.close()

	eqbo_out = np.array(eqbo_out)
	wqbo_out = np.array(wqbo_out)
	diff_out = np.array(diff_out)
	sigs_out = np.array(sigs_out)
	clim_out = np.array(clim_out)
	
	############# Begin the plotting ############
	
	fig, ax = plt.subplots()
	
	mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

	vmin = -10
	vmax = 10
	vlevs = np.linspace(vmin,vmax,num=21)
	vlevs = [v for v in vlevs if v != 0]
	ticks = [vmin,vmin/2,0,vmax/2,vmax]
	
	cmin = 900
	cmax = 1100
	clevs = np.linspace(cmin,cmax,num=21)

	plt.suptitle('QBO (5S-5N index @ %s hPa) sea level pressure (hPa)' % isobar,fontsize=12,fontweight='normal')

	# Add colormap #
	
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()
	
	lons = var.lon.values
	lats = var.lat.values
	
	cols = [0,1,2,3,4]

	for i in cols:
	
		print (i)

		########
		# eqbo #
		########
		
		if hemisphere == 'NH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]), projection=ccrs.NorthPolarStereo())
			ax1.set_extent([-180, 180, 20, 90], ccrs.PlateCarree())
		if hemisphere == 'SH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]), projection=ccrs.SouthPolarStereo())
			ax1.set_extent([-180, 180, -90, -20], ccrs.PlateCarree())
			
		plt.title('%s' % titles[i],fontsize=10,y=0.93,fontweight='normal')
		
		# Plot style features #
		
		ax1.coastlines(linewidth=0.25)
		theta = np.linspace(0, 2*np.pi, 100)
		center, radius = [0.5, 0.5], 0.5
		verts = np.vstack([np.sin(theta), np.cos(theta)]).T
		circle = mpath.Path(verts * radius + center)
		ax1.set_boundary(circle, transform=ax1.transAxes)
		pos1 = ax1.get_position()
		plt.title("%s" % titles[i], fontsize=10,fontweight='normal',y=0.98)
		cyclic_z, cyclic_lon = add_cyclic_point(eqbo_out[i], coord=lons)
		
		# Plot anomalies #
		
		contourf = ax1.contourf(cyclic_lon, lats, cyclic_z,transform=ccrs.PlateCarree(),cmap=cmap1,vmin=vmin,vmax=vmax,levels=vlevs,extend='both',zorder=1)

		# Overlay the climatology #
		
		cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
		cs = ax1.contour(cyclic_lon, lats, cyclic_clim,transform=ccrs.PlateCarree(),colors='k',linewidths=0.5,vmin=cmin,vmax=cmax,levels=clevs,extend='both',zorder=3)
		
		plt.rc('font',weight='normal')
		plt.clabel(cs,cs.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)
		plt.rc('font',weight='normal')
		
		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)),fontsize=10)
			ax2.spines['top'].set_visible(False)
			ax2.spines['right'].set_visible(False)
			ax2.spines['bottom'].set_visible(False)
			ax2.spines['left'].set_visible(False)
			ax2.get_yaxis().set_ticks([])
		
		########
		# wqbo #
		########
		
		if hemisphere == 'NH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]), projection=ccrs.NorthPolarStereo())
			ax1.set_extent([-180, 180, 20, 90], ccrs.PlateCarree())
		if hemisphere == 'SH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]), projection=ccrs.SouthPolarStereo())
			ax1.set_extent([-180, 180, -90, -20], ccrs.PlateCarree())
		
		# Plot style features #
		
		ax1.coastlines(linewidth=0.25)
		theta = np.linspace(0, 2*np.pi, 100)
		center, radius = [0.5, 0.5], 0.5
		verts = np.vstack([np.sin(theta), np.cos(theta)]).T
		circle = mpath.Path(verts * radius + center)
		ax1.set_boundary(circle, transform=ax1.transAxes)
		pos1 = ax1.get_position()
		plt.title("%s" % titles[i], fontsize=10,fontweight='normal',y=0.98)
		cyclic_z, cyclic_lon = add_cyclic_point(wqbo_out[i], coord=lons)
		
		# Plot anomalies #
		
		contourf = ax1.contourf(cyclic_lon, lats, cyclic_z,transform=ccrs.PlateCarree(),cmap=cmap1,vmin=vmin,vmax=vmax,levels=vlevs,extend='both',zorder=1)

		# Overlay the climatology #
		
		cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
		cs = ax1.contour(cyclic_lon, lats, cyclic_clim,transform=ccrs.PlateCarree(),colors='k',linewidths=0.5,vmin=cmin,vmax=cmax,levels=clevs,extend='both',zorder=3)
		
		plt.rc('font',weight='normal')
		plt.clabel(cs,cs.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)
		plt.rc('font',weight='normal')
		
		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)),fontsize=10)
			ax2.spines['top'].set_visible(False)
			ax2.spines['right'].set_visible(False)
			ax2.spines['bottom'].set_visible(False)
			ax2.spines['left'].set_visible(False)
			ax2.get_yaxis().set_ticks([])
		
		##############
		# Difference #
		##############
		
		if hemisphere == 'NH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]), projection=ccrs.NorthPolarStereo())
			ax1.set_extent([-180, 180, 20, 90], ccrs.PlateCarree())
		if hemisphere == 'SH':
			ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]), projection=ccrs.SouthPolarStereo())
			ax1.set_extent([-180, 180, -90, -20], ccrs.PlateCarree())
		
		# Plot style features #
		
		ax1.coastlines(linewidth=0.25)
		theta = np.linspace(0, 2*np.pi, 100)
		center, radius = [0.5, 0.5], 0.5
		verts = np.vstack([np.sin(theta), np.cos(theta)]).T
		circle = mpath.Path(verts * radius + center)
		ax1.set_boundary(circle, transform=ax1.transAxes)
		pos1 = ax1.get_position()
		plt.title("%s" % titles[i], fontsize=10,fontweight='normal',y=0.98)
		cyclic_z, cyclic_lon = add_cyclic_point(diff_out[i], coord=lons)
		
		# Plot anomalies #
		
		contourf = ax1.contourf(cyclic_lon, lats, cyclic_z,transform=ccrs.PlateCarree(),cmap=cmap1,vmin=vmin,vmax=vmax,levels=vlevs,extend='both',zorder=1)

		# Statistical significance #

		sig_levs = [0.95,1]
		mpl.rcParams['hatch.linewidth'] = 0.2
		cyclic_sig, cyclic_lontmp = add_cyclic_point(sigs_out[i], coord=lons)
		hatching = ax1.contourf(cyclic_lon, lats, cyclic_sig,transform=ccrs.PlateCarree(),colors='black',vmin=0.95,vmax=1,levels=sig_levs,hatches=['......','......'],alpha=0.0,zorder=2)

		# Overlay the climatology #
		
		cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
		cs = ax1.contour(cyclic_lon, lats, cyclic_clim,transform=ccrs.PlateCarree(),colors='k',linewidths=0.5,vmin=cmin,vmax=cmax,levels=clevs,extend='both',zorder=3)
		
		plt.rc('font',weight='normal')
		plt.clabel(cs,cs.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)
		plt.rc('font',weight='normal')
		
		if i == 4:
			ax2 = ax1.twinx()
			yticks = [0,0.5,1.0]
			ylabels = ['','','']
			ax2.set_yticks(yticks)
			ax2.set_yticklabels(ylabels, fontsize=8, fontweight = 'normal')
			ax2.set_ylabel('eqbo - wqbo',fontsize=10)
			ax2.spines['top'].set_visible(False)
			ax2.spines['right'].set_visible(False)
			ax2.spines['bottom'].set_visible(False)
			ax2.spines['left'].set_visible(False)
			ax2.get_yaxis().set_ticks([])

	# Add colorbar #
	
	cb_ax = fig.add_axes([0.35, 0.05, 0.30, 0.015])
	cbar = fig.colorbar(contourf, cax=cb_ax, ticks=ticks,orientation='horizontal')
	cbar.ax.tick_params(labelsize=8, width=1)
	cbar.ax.set_xticklabels(ticks,weight='normal')
	
	
	plt.subplots_adjust(top=0.86,bottom=0.09,hspace=0.3,wspace=0.0,left=0.02,right=0.94)
	
	return fig, ax