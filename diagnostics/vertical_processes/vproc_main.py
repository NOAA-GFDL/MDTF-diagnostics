'''
	Program plots profiles of state variables and process tendencies at various locations and times of ENSO phase
	Level 1: Mean profiles of states and tendencies during ENSO phase (seasons: monthly means)
	Level 2: Time varying profiles during a season or seasonal transtion
	Level 3: Statistical reltiosnhips between vertical processes and ENSO/forcing/dynamical strength
'''




import numpy as np
import matplotlib.pyplot as mp
import xarray as xr
import datetime as dt
#from dateutil.relativedelta import relativedelta


import cartopy.crs as ccrs
import pandas as pd
import dask as ds

import sys
import warnings
warnings.filterwarnings("ignore", message="FutureWarning")



# To Import My Functions ###
import vproc_func as mypy
import vproc_figs as myfigs
import vproc_case_desc as mycases
import vproc_setup as mysetup

import importlib

''' Bring in function routines '''

importlib.reload(mypy) # Required because I am constantly the .py files
importlib.reload(mycases) 
importlib.reload(myfigs) 
importlib.reload(mysetup) 





'''

	Main Code 

'''




def main():



	''''' Which case(S) to use '''''

	case_desc,case_type,reanal_climo,pref_out = mysetup.vprof_setup()

	''''' Which nino SST region '''''
	nino_region = 'nino34'




	''' SEASON '''

	seas_mons = np.array(["Jan","Feb","Dec"])

	clim_anal = False

	''''' Years for the analysis '''''

	years_data = (1979,1983) # Year range of history files to read AND either 'climo' one file or 'tseries' many files


	''' REGIONAL SPECS (LAT/LON/LEV) '''

	lats_in = -45. ; latn_in = 45.
	lonw_in = 0. ; lone_in = 360.
	ppmin = 50. ; ppmax = 1050.



	''''' Variable description '''''

	var_cam = 'OMEGA'
	ldiv = True # Calculate divergence from OMEGA if var_Cam = OMEGA
	l_pminmax_plev = False # PLot lat lon plot of climo/nino/nina ma/min levels of occurrence.
	l_pscatt_2d = True # Scatter plot of 2 2D fields.

	''''' Named Regions '''''

	reg_df = mysetup.vprof_set_regions()
	



	''''' Directory Information '''''

#	dir_croot = '/glade/p/cgd/amp/people/hannay/amwg/climo/' # Directories with climo files
#	dir_hroot = '/glade/p/cgd/amp/amwg/runs/' # Run firectories with history files

	dir_proot = '/glade/u/home/rneale/python/python-figs/vert_proc/'
#	dir_obs = '/glade/p/cesm/amwg/amwg_data/obs_data/'


	''''' Variable Meta Info. '''''
	
	var_df = mysetup.vprof_set_vars()
	




	# Pressure range info.

	p_levs = np.arange(ppmin,ppmax,50.)


# Map simulation names to case names
	
	sim_names = mycases.mdtf_case_list()

	

	display(reg_df)
	display(var_df)

#	reg = list(reg_names.keys())[0]

	reg = reg_df.index.values.tolist()[0]

	print(reg)
	
#	reg_s = reg_df.loc[reg]['lat_s'] ; reg_n = reg_df.loc[reg]['lat_n']
#	reg_w = reg_df.loc[reg]['lon_w'] ; reg_e = reg_df.loc[reg]['lon_e']

#	sys.exit("Test exit")

	nmnths = seas_mons.size
	ncases = case_desc.size
	nregions = reg_df.index.size

	xmin = var_df.loc[var_cam]['xmin'] ; xmax=var_df.loc[var_cam]['xmax']
	axmin = var_df.loc[var_cam]['axmin'] ; axmax=var_df.loc[var_cam]['axmax']                     
	vunits = var_df.loc[var_cam]['vunits'] 
	var_text = var_df.loc[var_cam]['long_name']   
	var_pname = var_cam

	if ldiv and var_cam == 'OMEGA':
		var_pname = 'DIV'
		var_text = var_df.loc[var_pname]['long_name']     
		vunits = var_df.loc[var_pname]['vunits'] 
		xmin = var_df.loc[var_pname]['xmin'] ; xmax=var_df.loc[var_pname]['xmax']
		axmin = var_df.loc[var_pname]['axmin'] ; axmax=var_df.loc[var_pname]['axmax']                




	yr0 = years_data[0]
	yr1 = years_data[1]


	nino_names = ['Climatology ('+str(yr0)+'-'+str(yr1)+')','El Nino','La Nina']
	nino_colors = ['black','red','blue']


	''''' Figure Out Legend and Line Colors based '''''
	
	leg_elements,leg_labels,pmark,lcolor,lwidth,lstyle = myfigs.leg_vprof(case_desc,case_type)



	''''' Set Figures '''''
	
	mp.figure(3)
	
	fign, axn = mp.subplots(1,3,figsize=(26, 11))  
	fign.patch.set_facecolor('white') # Sets the plot background outside the data area to be white. Remove to make it transparent.


	
	
	
	
	
	
	

	'''
	########################
	##### LOOP CASES  ######
	########################
	'''


	for icase,case in enumerate(case_desc): # Do first so don't have to do a read mutliple times

		# Grab run name 

		sim_name = sim_names.loc[case]['run name']

		lclimo = True if reanal_climo and case_type[icase] == 'reanal' else False


		print('')
		print('')
		print('')
		print('**** **** **** **** **** **** **** **** **** ')
		print('**** CASE # ',icase+1,' OF ',ncases,' ****')
		print('**** **** **** **** **** **** **** **** **** ')
		print('- Name = ',case,' ->',sim_name)
		print('**** **** **** **** **** **** **** **** **** ')
		print('')   


		## Read data in from files ##


		print('-- SET TIME RANGE OF TIMESERIES DATA -- ',yr0,' to ',yr1)
		print('')
		print('-- Grabbing variable files --')

		if lclimo:  # Read in tseries based files here for the analysis variable
			files_ptr,var_name   = mypy.get_files_climo(sim_name,case_type[icase],var_cam,years_data) # Grab variable
		else :
			files_ptr,var_name   = mypy.get_files_tseries(sim_name,case_type[icase],var_cam,years_data) # Grab variable



		## TS FROM HISTORY FILES (just copy for h0 files if they are already read in)
		## Can still do this for lclimo as it will take observed if reanal

		print('-- Grabbing SST files --')

		if case_type[icase] in ['cam6_revert']: # I think this effectively acts as a pointer, I hope!
			tfiles_ptr = files_ptr 
			tvar_name = 'TS'
		else :   
			tfiles_ptr,tvar_name = mypy.get_files_tseries(sim_name,case_type[icase],'TS',years_data) # Grab TS for nino timeseries


		# Grabbing PS if needed

		print('-- Grabbing PS files --')

		if case_type[icase] in ['cam6_revert']: # Grab the LENS time series or just use existing file_ptr from h0 type output.
			pfiles_ptr = files_ptr 
		else:
			if not lclimo: # Don't need to read in PS for climos.
				pfiles_ptr,pvar_name = mypy.get_files_tseries(sim_name,case_type[icase],'PS',years_data) # Grab TS for nino timeseries



		''' TRIM FOR SPECIFIED YEARS '''


		print('-- Calculating and plotting nino SST anomalies - this will never be climo currently')

		sst_data = tfiles_ptr[tvar_name].sel(lat=slice(lats_in,latn_in),time=slice(str(yr0), str(yr1)))



		''' SST ANOMALY ROUTINE ARRAY '''

		sst_months =  sst_data.time.dt.strftime("%b")    
		inino_mons,inina_mons = mypy.nino_sst_anom(sim_name,sst_data,nino_region,dir_proot)

		print('-- NINO grab:  Done --')






		''''' FORK FOR CLIMO VERSUS h0/TSREIS INPUT FILE FORMAT '''''


		if not lclimo:



			''' Trim datasets for lev/lat/time for simplicity '''

		# Grab time/lev coord.

			lev = files_ptr['lev'].sel(lev=slice(min(p_levs),max(p_levs)))

		# Trimming as much as possible time/lat/lev        

			files_ptr=files_ptr.sel(lat=slice(lats_in,latn_in),time=slice(str(yr0),str(yr1)),lev=slice(min(p_levs),max(p_levs)))
			pfiles_ptr=pfiles_ptr.sel(lat=slice(lats_in,latn_in),time=slice(str(yr0),str(yr1)))       


		# Grab variables
			var_in = files_ptr[var_name]
			ps_in = pfiles_ptr['PS']
			time_in = files_ptr.time

		# Calculate dp        
			dp_lev = np.diff(lev)


		# Array accessing based on type of case.    
			if case_type[icase] in ['lens1','lens2','c6_amip']:
				print('-- "Compute" the variable array now (bring it up from lazy array) if != ANALYSES')
		#            %time var_in = var_in.compute()






		# Check SST size with Variable size

			if sst_data.time.size != time_in.size : print('SST and VARIABLE sizes DO NOT MATCH - ',sst_data.time.size,' and ',time_in.size) 

			month_nums = time_in.dt.month   
			hmonths = time_in.dt.strftime("%b")



			lmon_seas = np.isin(hmonths,seas_mons) # Logical for season months in all months
			imon_seas = np.argwhere(lmon_seas)[:,0] # Indices
			hmon_seas = hmonths[imon_seas] # Subsetting full months.



		## Much easier than above but doing the intersections of months and nino months.
			inino_seas,inino_ind,imon_nino_ind = np.intersect1d(inino_mons, imon_seas, return_indices=True)
			inina_seas,inina_ind,imon_nina_ind = np.intersect1d(inina_mons, imon_seas, return_indices=True)


		## Could speed up below by reading in var_in for the season months then subsetting that for nino/nina    
		## Remember: It is reading in a subset of seaonal months and then nino/nina are a subset of those. 

			var_in_inseas = var_df.loc[var_cam]['vscale']*var_in[imon_seas,:,:,:] # Pull only the months we need
			var_ps_inseas = ps_in[imon_seas,:,:] 

			if case_type[icase] in ['reanal','cam6_revert']:
				print('-- "Compute" the variable array now (bring it up front lazy array) if == ANALYSES')
#				%time var_in_inseas = var_in_inseas.compute()

			var_in_seas = var_in_inseas.mean(dim=['time'])  # Perform seasonal average
			var_ps_seas = var_ps_inseas.mean(dim=['time'])  # 

		# Nino/nina averages
			var_in_nino = var_in_inseas[imon_nino_ind,:,:,:].mean(dim=['time'])  # Take nino/nina months from the seasonal timeseries months
			var_in_nina = var_in_inseas[imon_nina_ind,:,:,:].mean(dim=['time']) 

		# Nino/nina anomalies
			var_in_nino = var_in_nino-var_in_seas
			var_in_nina = var_in_nina-var_in_seas

			var_ps_nino = var_ps_inseas[imon_nino_ind,:,:].mean(dim=['time'])  # Take nino/nina months from the seasonal timeseries months
			var_ps_nina = var_ps_inseas[imon_nina_ind,:,:].mean(dim=['time']) 

			varp_in_ps = (var_ps_seas,var_ps_nino,var_ps_nina) 



		else :    ### Just grab separate data from climo, nino and nina files.

			var_in_seas =  files_ptr[var_name].isel(time=0).sel(lat=slice(lats_in,latn_in))
			var_in_nino =  files_ptr[var_name].isel(time=1).sel(lat=slice(lats_in,latn_in))
			var_in_nina =  files_ptr[var_name].isel(time=2).sel(lat=slice(lats_in,latn_in))


			lev_in = var_in_seas.lev
			ilevs = np.where(lev_in >= min(p_levs))

			lev = lev_in[ilevs]


			var_in_seas =  var_df.loc[var_cam]['ovscale']*var_in_seas.loc[lev[0]:lev[-1]]
			var_in_nino =  var_df.loc[var_cam]['ovscale']*var_in_nino.loc[lev[0]:lev[-1]]
			var_in_nina =  var_df.loc[var_cam]['ovscale']*var_in_nina.loc[lev[0]:lev[-1]]


			varp_in_ps = None






		'''
			####################################    
			### Plot div/omega level ###
			####################################
		'''     

		if l_pminmax_plev:
			
			print('-- Plotting max/min pressure level of field --')
			mp.figure(2)
			varp_in_lev = (var_in_seas,var_in_nino,var_in_nina) # Put in tuple for looping.
			pdiv_lev = myfigs.plot_div_pres(case_type[icase],case,var_cam,varp_in_lev,varp_in_ps,files_ptr,dir_proot,ldiv)



		'''
			####################################    
			### Plot Scatter of 2 Quantities
			####################################
		'''     
		
		if l_pscatt_2d:
			
			print('-- Scatter Plots of ... ---')
#			myfigs.scat_plot(case_type[icase],case,var_in_seas,varp_in_ps,reg_df,files_ptr)
#			myfigs.scat_plot(case_type[icase],case,var_in_nino,varp_in_ps,reg_df,files_ptr)
			myfigs.scat_plot(case_type[icase],case,var_in_nino,varp_in_ps,reg_df,files_ptr)
	

		'''
			########################    
			### Now Loop Regions ###
			########################
		''' 

		mp.figure(3)

		for ireg,reg in enumerate(reg_df.index):  ## 4 regions let's assume ##

		### Assign lat/lon region domain ###

			reg_name = reg_df.loc[reg]['long_name'] 

			reg_s = reg_df.loc[reg]['lat_s'] ; reg_n = reg_df.loc[reg]['lat_n']
			reg_w = reg_df.loc[reg]['lon_w'] ; reg_e = reg_df.loc[reg]['lon_e']

			print()
			print('-- Region = ',reg_name,' - ',reg_s,reg_n,reg_w,reg_e)

			reg_a_str = '%d-%d\u00b0E %.1f-%d\u00b0N' % (reg_w,reg_e,reg_s,reg_n)
			reg_a_out = '%d-%dE_%.1f-%dN' % (reg_w,reg_e,reg_s,reg_n)  

			print('-- Averaging for region - ',reg_a_str)




		### Compute Seasonal/El Nino/La Nina profiles ###

			varp_seas = var_in_seas.loc[:,reg_s:reg_n,reg_w:reg_e]

		#        if lclimo :

			varp_nino = var_in_nino.loc[:,reg_s:reg_n,reg_w:reg_e]
			varp_nina = var_in_nina.loc[:,reg_s:reg_n,reg_w:reg_e]

		#        else :

		#         varp_nino = var_in_nino.loc[:,reg_s:reg_n,reg_w:reg_e]-varp_seas
		#         varp_nina = var_in_nina.loc[:,reg_s:reg_n,reg_w:reg_e]-varp_seas

			varp_all = (varp_seas,varp_nino,varp_nina) # Put in tuple for looping.






			'''
			####################################    
			### Loop climo/nino/nina periods ###
			####################################
			'''     

		## LOOP: Seasonal/El Nino/La Nina plots for this region.


			for iplot,var_plot in enumerate(varp_all):

				print('    -- Period = '+nino_names[iplot])
				pxmin = xmin if iplot == 0 else axmin
				pxmax = xmax if iplot == 0 else axmax

		# Regional average
				var_fig = var_plot.mean(dim=['lat','lon'],skipna = True)   




				if ldiv and var_cam == 'OMEGA':
					var_fig = var_fig.differentiate("lev")


				axn[iplot].plot(var_fig,lev,lw=lwidth[icase],markersize=9,marker=pmark[icase],color=lcolor[icase],linestyle=lstyle[icase])  



				if (icase==0) :
					axn[iplot].set_title(nino_names[iplot],fontsize=20,color=nino_colors[iplot])
					axn[iplot].set_xlim([pxmin,pxmax])
					axn[iplot].set_ylim([ppmax,ppmin])
					axn[iplot].set_ylabel('mb',fontsize=16) 
					axn[iplot].set_xlabel(vunits,fontsize=16)      
					axn[iplot].set_yticks(p_levs)
					axn[iplot].set_yticklabels(p_levs,fontsize=14)
		###                axn[iplot].set_xticklabels(np.arange(xmin,xmax,0.1*(xmax-xmin)),fontsize=12)
					axn[iplot].tick_params(axis='both', which='major', labelsize=14)

					axn[iplot].grid(linestyle='--')  


				if ((pxmin < 0) and (pxmax > 0)) :
					axn[iplot].vlines(0., ppmax, ppmin, linestyle="--",lw=1, color='black')



	# Legend ### Perform a bit of logic for the  
	#rtypes, counts = np.unique(case_type, return_counts=True)


	lloc = 'lower right' if var_name in ['ZMDQ','STEND_CLUBB'] else 'lower left' 
	#axn[0].legend(leg_cases,fontsize=15,loc = lloc)

	axn[0].legend(leg_elements,leg_labels,fontsize=15,loc = lloc)

	# Main title
	fign.suptitle('ENSO Anomalies - '+reg_name+' -- '+reg_a_str+' - '+var_text,fontsize=20)

	mp.rcParams['xtick.labelsize'] = 15 # Global set of xtick label size    


	#    mp.show()





	# Hard copy  
	fign.savefig(dir_proot+pref_out+'_nino_vprof_'+var_pname+'_'+reg_a_out+'_'+str(yr0)+'_to_'+str(yr1)+'.png', dpi=80)

	#mp.show()   

	print()
	print()
	print('-- End Timing --')








