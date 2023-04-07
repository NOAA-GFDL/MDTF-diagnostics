'''
	Program plots profiles of state variables and process tendencies at various locations and times of ENSO phase
	Level 1: Mean profiles of states and tendencies during ENSO phase (seasons: monthly means)
	Level 2: Time varying profiles during a season or seasonal transtion
	Level 3: Statistical reltiosnhips between vertical processes and ENSO/forcing/dynamical strength
	Level 4:
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


#from distributed import Client

''' Bring in function routines '''

importlib.reload(mypy) # Required because I am constantly the .py files
importlib.reload(mycases) 
importlib.reload(myfigs) 
importlib.reload(mysetup) 





'''

	Main Code 

'''




def main():

#	client = Client(cluster)
#	client

	''''' Which case(S) to use '''''

	case_desc,case_type,reanal_climo,pref_out = mysetup.vprof_setup()

	''''' Which nino SST region '''''
	nino_region = 'nino34'




	''' SEASON '''

	seas_mons = np.array(["Jan","Feb","Dec"])

	clim_anal = False

	''''' Years for the analysis '''''

	years_data = (1979,2005) # Year range of history files to read AND either 'climo' one file or 'tseries' many files


	''' REGIONAL SPECS (LAT/LON/LEV) '''

	lats_in = -45,45
	lonw_in = 0. ; lone_in = 360.
	ppmin = 50. ; ppmax = 1050.



	''''' Variable description '''''

	var_cam = 'OMEGA'
	ldiv = False # Calculate divergence from OMEGA if var_Cam = OMEGA
	l_pminmax_plev = True # PLot lat lon plot of climo/nino/nina ma/min levels of occurrence.
	l_pscatt_2d = True # Scatter plot of 2 2D fields.
	l_vprof = True
	
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
			files_ptr,var_name   = mypy.get_files_climo(sim_name,case_type[icase],var_cam,lats_in,p_levs,years_data) # Grab variable
		else :
			files_ptr,var_name   = mypy.get_files_tseries(sim_name,case_type[icase],var_cam,lats_in,p_levs,years_data) # Grab variable
			



		## TS FROM HISTORY FILES (just copy for h0 files if they are already read in)
		## Can still do this for lclimo as it will take observed if reanal

		print('-- Grabbing Sea Surface Temperature (SST) files --')

		if case_type[icase] in ['cam6_revert']: # I think this effectively acts as a pointer, I hope!
			tfiles_ptr = files_ptr 
			tvar_name = 'TS'
		else :   
			tfiles_ptr,tvar_name = mypy.get_files_tseries(sim_name,case_type[icase],'TS',lats_in,p_levs,years_data) # Grab TS for nino timeseries


		# Grabbing PS if needed

		print('-- Grabbing Surface Pressure (PS) files --')

		if case_type[icase] in ['cam6_revert']: # Grab the LENS time series or just use existing filse_ptr from h0 type output.
			pfiles_ptr = files_ptr 
		else:
			if not lclimo: # Don't need to read in PS for climos.
				pfiles_ptr,pvar_name = mypy.get_files_tseries(sim_name,case_type[icase],'PS',lats_in,p_levyears_data) # Grab TS for nino timeseries
			else :
				pfiles_ptr=None



		''' TRIM FOR SPECIFIED YEARS '''


		print('-- Calculating and plotting nino SST anomalies - this will never be climo currently')

		sst_data = tfiles_ptr[tvar_name]



		''' SST ANOMALY ROUTINE ARRAY '''

		sst_months =  sst_data.time.dt.strftime("%b")    
		inino_mons,inina_mons = mypy.nino_sst_anom(sim_name,sst_data,nino_region,dir_proot)

		print('-- NINO grab:  Done --')






		
		'''
			#############################################################    
			### FORK FOR CLIMO VERSUS h0/TSREIS INPUT FILE FORMAT ?
			#############################################################    
		'''     

		varp_in_lev,var_in_ps = mypy.derive_nino_vars(lclimo,var_name,var_cam,p_levs,files_ptr,pfiles_ptr,case_type,var_df,inino_mons,inina_mons,seas_mons)



		'''
			####################################    
			### Plot div/omega level ###
			####################################
		'''     

		if l_pminmax_plev:

			print('-- Plotting max/min pressure level of field --')
			
#			varp_in_lev = (var_in_seas,var_in_nino,var_in_nina) # Put in tuple for looping.
			pdiv_lev = myfigs.plot_div_pres(case_type[icase],case,var_cam,varp_in_lev,var_in_ps,files_ptr,dir_proot,ldiv)



		'''
			####################################    
			### Plot Scatter of 2 Quantities
			####################################
		'''     
		
		if l_pscatt_2d:
			
			print('-- Scatter Plots of ... ---')
			
#			myfigs.scat_plot(case_type[icase],case,var_in_seas,var_in_ps,reg_df,files_ptr,dir_proot)
#			myfigs.scat_plot(case_type[icase],case,var_in_nino,var_in_ps,reg_df,files_ptr,dir_proot)
			myfigs.scat_plot(case_type[icase],case,varp_in_lev,var_in_ps,reg_df,files_ptr,dir_proot)
	

	
		'''
			################################################    
			### Now Loop Regions For Vertical Profiles ###
			################################################ 
		''' 

		
		
		
		
		for ireg,reg in enumerate(reg_df.index):  ## 4 regions let's assume ##

		
		### Assign lat/lon region domain ###

			'''
				### Set regeion info and subset data ###
			'''
			
			varp_tavs,reg_name,reg_s,reg_n,reg_w,reg_e = mypy.vprof_set_region(ireg,reg_df,varp_in_lev)
				


			reg_a_str = '%d-%d\u00b0E %.1f-%d\u00b0N' % (reg_w,reg_e,reg_s,reg_n)
			reg_a_out = '%d-%dE_%.1f-%dN' % (reg_w,reg_e,reg_s,reg_n)  


			'''
			####################################    
			### Loop climo/nino/nina periods ###
			####################################
			'''     

		## LOOP: Seasonal/El Nino/La Nina plots for this region.


			for iplot,var_plot in enumerate(varp_tavs):

				print('    -- Period = '+nino_names[iplot])
				pxmin = xmin if iplot == 0 else axmin
				pxmax = xmax if iplot == 0 else axmax

		## Regional average (need to add guassian weights here).
				var_fig = var_plot.mean(dim=['lat','lon'],skipna = True)   

			# Differentiate for divergence, probably need to do tis for each GP then average.
				if ldiv and var_cam == 'OMEGA':
					var_fig = var_fig.differentiate("lev")

										
					
				''''' Set Figures '''''
		
				if iplot == 0 and icase == 0 and ireg == 0:
#					mp.figure(2)
					fign, axn = mp.subplots(nregions,3,figsize=(26, 26))  
					fign.patch.set_facecolor('white') # Sets the plot background outside the data area to be white. Remove to make it transparent.	
	
#				mp.figure(2)
			
				axn[ireg,iplot].plot(var_fig,var_fig.lev,lw=lwidth[icase],markersize=9,marker=pmark[icase],color=lcolor[icase],linestyle=lstyle[icase])  



				if (icase==0) :
					axn[ireg,iplot].set_title(nino_names[iplot],fontsize=20,color=nino_colors[iplot])
					axn[ireg,iplot].set_xlim([pxmin,pxmax])
					axn[ireg,iplot].set_ylim([ppmax,ppmin])
					axn[ireg,iplot].set_ylabel('mb',fontsize=16) 
					axn[ireg,iplot].set_xlabel(vunits,fontsize=16)      
					axn[ireg,iplot].set_yticks(p_levs)
					axn[ireg,iplot].set_yticklabels(p_levs,fontsize=14)
		###                axn[iplot].set_xticklabels(np.arange(xmin,xmax,0.1*(xmax-xmin)),fontsize=12)
					axn[ireg,iplot].tick_params(axis='both', which='major', labelsize=14)

					axn[ireg,iplot].grid(linestyle='--')  


				if ((pxmin < 0) and (pxmax > 0)) :
					axn[ireg,iplot].vlines(0., ppmax, ppmin, linestyle="--",lw=1, color='black')

					
	# Plot regions
	
					
					

	# Legend ### Perform a bit of logic for the  
	#rtypes, counts = np.unique(case_type, return_counts=True)


	lloc = 'lower right' if var_name in ['ZMDQ','STEND_CLUBB'] else 'lower left' 
	#axn[0].legend(leg_cases,fontsize=15,loc = lloc)
	
	mp.figure(2)
	axn[0,0].legend(leg_elements,leg_labels,fontsize=15,loc = lloc)

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








