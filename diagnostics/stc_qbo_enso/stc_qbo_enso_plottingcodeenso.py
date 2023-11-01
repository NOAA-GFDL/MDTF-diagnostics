'''
This module contains functions used in the Stratospheric QBO and ENSO POD.

Contains:
	enso_slp: plots sea level pressure response to ENSO as a function of month and ENSO phase
	enso_uzm: plots the zonal-mean zonal wind response to ENSO as a function of month and ENSO phase
	enso_vt: plots the zonally averaged eddy heat flux response to the ENSO as a function of month and ENSO phase
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

def enso_uzm(UZM,negative_indices,positive_indices,hemisphere):

	date_first = UZM.time[0]
	date_last = UZM.time[-1]

	if hemisphere == 'NH':
		uzm = UZM.sel(time=slice('%s-11-01' % date_first.dt.year.values, '%s-03-31' % date_last.dt.year.values))
		titles = ['November','December','January','February','March']
		plot_months = [11,12,1,2,3]
	if hemisphere == 'SH':
		uzm = UZM.sel(time=slice('%s-09-01' % date_first.dt.year.values, '%s-01-31' % date_last.dt.year.values))
		titles = ['September','October','November','December','January']
		plot_months = [9,10,11,12,1]
		
	# Check to see if the pressure levels are in hPa or Pa
	if np.nanmax(uzm.lev.values) > 2000:
		uzm.lev.values[:] = np.true_divide(uzm.lev.values,100)
	
	nina_out = []
	nino_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = uzm.sel(time=uzm.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').values)
	
		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")
	
		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)
		
		nina_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		nino_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(nina_tmp.values,nino_tmp.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(nina_tmp.mean('time').values,nino_tmp.mean('time').values))
		nina_out.append(nina_tmp.mean('time').values)
		nino_out.append(nino_tmp.mean('time').values)

		clim.close()
		anom.close()
		nina_tmp.close()
		nino_tmp.close()
	uzm.close()

	nina_out = np.array(nina_out)
	nino_out = np.array(nino_out)
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

	plt.suptitle('ENSO zonal-mean zonal wind (m/s)',fontsize=12,fontweight='normal')

	# Add colormap #
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()

	x, y = np.meshgrid(UZM.lat.values,UZM.lev.values)
	UZM.close()

	cols = [0,1,2,3,4]

	for i in cols:
	
		print (i)

		# Nina #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]))
		plt.title('%s' % titles[i],fontsize=10,y=0.93,fontweight='normal')

		cs = plt.contourf(x,y,nina_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nina (%s seasons)' % int(len(negative_indices)),fontsize=10)

		# Nino #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]))

		cs = plt.contourf(x,y,nino_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nino (%s seasons)' % int(len(positive_indices)),fontsize=10)

		# Diff: Nina minus Nino #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]))

		cs = plt.contourf(x,y,diff_out[i],cmap=cmap1,levels=vlevs,extend="both",vmin=vmin,vmax=vmax,zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nina - Nino',fontsize=10)

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
	
def enso_vt(VT,negative_indices,positive_indices,hemisphere):

	date_first = VT.time[0]
	date_last = VT.time[-1]

	if hemisphere == 'NH':
		vt = VT.sel(time=slice('%s-11-01' % date_first.dt.year.values, '%s-03-31' % date_last.dt.year.values))
		titles = ['November','December','January','February','March']
		plot_months = [11,12,1,2,3]
	if hemisphere == 'SH':
		vt = VT.sel(time=slice('%s-09-01' % date_first.dt.year.values, '%s-01-31' % date_last.dt.year.values))
		titles = ['September','October','November','December','January']
		plot_months = [9,10,11,12,1]
		
	# Check to see if the pressure levels are in hPa or Pa
	if np.nanmax(vt.lev.values) > 2000:
		vt.lev.values[:] = np.true_divide(vt.lev.values,100)
	
	nina_out = []
	nino_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = vt.sel(time=vt.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').values)
	
		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")
	
		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)
		
		nina_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		nino_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(nina_tmp.values,nino_tmp.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(nina_tmp.mean('time').values,nino_tmp.mean('time').values))
		nina_out.append(nina_tmp.mean('time').values)
		nino_out.append(nino_tmp.mean('time').values)

		clim.close()
		anom.close()
		nina_tmp.close()
		nino_tmp.close()
	vt.close()

	nina_out = np.array(nina_out)
	nino_out = np.array(nino_out)
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
	ticks = [vmin,vmin/2,0,vmax/2,vmax]

	vthesh = 250

	blevs = []

	blevs.append(-2)
	blevs.append(-6)
	blevs.append(-10)
	blevs.append(-25)
	blevs.append(-50)
	blevs.append(-100)
	#blevs.append(-200)

	blevs.append(2)
	blevs.append(6)
	blevs.append(10)
	blevs.append(25)
	blevs.append(50)
	blevs.append(100)
	#blevs.append(200)


	blevs = np.sort(blevs)
	print (blevs)

	cmin = -200
	cmax = 200
	clevs = np.linspace(cmin,cmax,num=41)
	clevs = [v for v in clevs if v != 0]

	plt.suptitle('ENSO zonal-mean eddy heat flux (Km/s)',fontsize=12,fontweight='normal')

	# Add colormap #
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()

	x, y = np.meshgrid(VT.lat.values,VT.lev.values)

	cols = [0,1,2,3,4]

	for i in cols:
	
		print (i)

		# Nina #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(0,cols[i]))
		plt.title('%s' % titles[i],fontsize=10,y=0.93,fontweight='normal')

		cs = plt.contourf(x,y,nina_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nina (%s seasons)' % int(len(negative_indices)),fontsize=10)

		# Nino #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(1,cols[i]))

		cs = plt.contourf(x,y,nino_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nino (%s seasons)' % int(len(positive_indices)),fontsize=10)

		# Diff: Nina minus Nino #

		ax1 = plt.subplot2grid(shape=(3,5), loc=(2,cols[i]))

		cs = plt.contourf(x,y,diff_out[i],blevs,norm = mpl.colors.SymLogNorm(linthresh=2,linscale=1,vmin=-100,vmax=100),cmap=cmap1,extend="both",zorder=1)

		mpl.rcParams["lines.linewidth"] = 0.2
		mpl.rcParams["lines.dashed_pattern"] = 10, 3
		black = plt.contour(x,y,clim_out[i],colors='k',levels=clevs,extend="both",vmin=cmin,vmax=cmax,zorder=3)
		plt.clabel(black,black.levels[:],inline=1,fmt='%1.0f',fontsize=4,colors='k',inline_spacing=1)

		plt.semilogy()
		yticks = [1,10,100,1000]
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
			ax2.set_ylabel('Nina - Nino',fontsize=10)

	# Add colorbar #

	oticks = [-100,-50,-25,-10,-6,-2,2,6,10,25,50,100]
	cb_ax = fig.add_axes([0.365, 0.04, 0.30, 0.015])
	cbar = fig.colorbar(cs, cax=cb_ax, ticks=oticks,orientation='horizontal')
	cbar.ax.tick_params(labelsize=6, width=1)
	cbar.ax.set_xticklabels(oticks,weight='normal')

	plt.subplots_adjust(top=0.86,bottom=0.16,hspace=0.5,wspace=0.55,left=0.08,right=0.95)
	return fig, ax
	
##################################################################################################
##################################################################################################
##################################################################################################
	
	
def enso_slp(PS,negative_indices,positive_indices,hemisphere):

	date_first = PS.time[0]
	date_last = PS.time[-1]

	if hemisphere == 'NH':
		ps = PS.sel(time=slice('%s-11-01' % date_first.dt.year.values, '%s-03-31' % date_last.dt.year.values))
		titles = ['November','December','January','February','March']
		plot_months = [11,12,1,2,3]
	if hemisphere == 'SH':
		ps = PS.sel(time=slice('%s-09-01' % date_first.dt.year.values, '%s-01-31' % date_last.dt.year.values))
		titles = ['September','October','November','December','January']
		plot_months = [9,10,11,12,1]
	
	if getattr(ps.psl,'units') == 'Pa':
		print(f'**Converting pressure levels to hPa')
		ps.psl.attrs['units'] = 'hPa'
		ps.psl.values[:] = ps.psl.values/100.
		
	print (np.nanmin(ps.psl.values))
	print (np.nanmedian(ps.psl.values))
	print (np.nanmean(ps.psl.values))
	print (np.nanmax(ps.psl.values))
	
	nina_out = []
	nino_out = []
	diff_out = []
	sigs_out = []
	clim_out = []

	for mon in plot_months:

		clim = ps.sel(time=ps.time.dt.month.isin([mon]))
		clim_out.append(clim.mean('time').psl.values)
	
		anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")
	
		if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
			tmp_negative_indices = np.add(negative_indices,0)
			tmp_positive_indices = np.add(positive_indices,0)
		if mon == 1 or mon == 2 or mon == 3:
			tmp_negative_indices = np.add(negative_indices,1)
			tmp_positive_indices = np.add(positive_indices,1)
		
		nina_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
		nino_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

		t,p = stats.ttest_ind(nina_tmp.psl.values,nino_tmp.psl.values,axis=0,nan_policy='omit')

		sigs_out.append(np.subtract(1,p))
		diff_out.append(np.subtract(nina_tmp.mean('time').psl.values,nino_tmp.mean('time').psl.values))
		nina_out.append(nina_tmp.mean('time').psl.values)
		nino_out.append(nino_tmp.mean('time').psl.values)

		clim.close()
		anom.close()
		nina_tmp.close()
		nino_tmp.close()
	ps.close()

	nina_out = np.array(nina_out)
	nino_out = np.array(nino_out)
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

	plt.suptitle('Nina - Nino sea level pressure (hPa)',fontsize=12,fontweight='normal')

	# Add colormap #
	
	from palettable.colorbrewer.diverging import RdBu_11
	cmap1=RdBu_11.mpl_colormap.reversed()
	
	lons = ps.lon.values
	lats = ps.lat.values
	
	cols = [0,1,2,3,4]

	for i in cols:
	
		print (i)

		########
		# Nina #
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
		cyclic_z, cyclic_lon = add_cyclic_point(nina_out[i], coord=lons)
		
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
			ax2.set_ylabel('Nina (%s seasons)' % int(len(negative_indices)),fontsize=10)
			ax2.spines['top'].set_visible(False)
			ax2.spines['right'].set_visible(False)
			ax2.spines['bottom'].set_visible(False)
			ax2.spines['left'].set_visible(False)
			ax2.get_yaxis().set_ticks([])
		
		########
		# Nino #
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
		cyclic_z, cyclic_lon = add_cyclic_point(nino_out[i], coord=lons)
		
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
			ax2.set_ylabel('Nino (%s seasons)' % int(len(positive_indices)),fontsize=10)
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
			ax2.set_ylabel('Nina - Nino',fontsize=10)
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