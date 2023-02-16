
######################################################
## PYTHON FUNCTIONS FOR VERTICAL PROCESSES NOTEBOOK ##
######################################################

import numpy as np
import xarray as xr
# import datetime as dt
# import pandas as pd
# import pygrib as pyg # Read in grib for analyses (ECMWF)

# import monthdelta 
#from dateutil.relativedelta import relativedelta

# Plotting modules

import cartopy as cart
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import cartopy.mpl.ticker as cticker

import matplotlib.pyplot as mp
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import matplotlib.patches as mpatches


#import geocat.comp as gcat
from geocat.comp import interp_hybrid_to_pressure


#import warnings
#warnings.filterwarnings("ignore", category=DeprecationWarning) 

#from shapely import geometry
#from collections import namedtuple
#from shapely.geometry.polygon import LinearRing

#from nc_time_axis import CalendarDateTime
import subprocess as sp
import os 





#####################################################



"""
        Nino/Nina SST information
        
        Input: Timseries of SST over global region
        Output: Timseries of SST-anomalies for different nino regions.
                Classification of nino/neutral/nina based on SST anomalies

"""


def nino_sst_anom(run_case,sst_data,nino,dir_proot):



	# Nino regions (S/N/W/E) 
	nino_reg = {}
    
	nino_reg['nino12']  = [-10.,0.,270.,280.]
	nino_reg['nino3']   = [-5.,5.,210.,270.]
	nino_reg['nino34']  = [-5.,5.,190.,240.]   
	nino_reg['nino4']   = [-5.,5.,160.,210.]
	nino_reg['nino5']   = [-5.,5.,120.,140.]
	nino_reg['nino6']   = [8.,16.,140.,160.]
    

	print('    > Calculating for SST anomalies ',nino,' region')

    
# Set nino averaging domain
	nino_s = nino_reg[nino][0] ; nino_n = nino_reg[nino][1]
	nino_w = nino_reg[nino][2] ; nino_e = nino_reg[nino][3]

 
    
## Be careful as the time a coordinate is 1 month off FEB actually = JAN as detrmined by the cftime coordinate.
    
# Read in TS (SSTs) from inputdata HadISST for now.  

	sst_ts = sst_data.loc[:,nino_s:nino_n,nino_w:nino_e].mean(dim=['lat','lon']) 
#    print(sst_ts.resample())
	sst_ts = sst_ts.compute()
   
#    sst_ts = h0_month_fix(sst_ts)
   

## If TS/SST data comes from history files may need to check that first file should be Jan and Not Feb    
## Remove average for each month of year (annual cycle)
#    sst_data.time = sst_data.time + dt.timedelta(month=1)
#    sst_sata.time = sst_data.time + relativedelta(-1)

    
	mnames_all = sst_ts.time.dt.strftime("%b") 
	year_all = sst_ts.time.dt.strftime("%Y") 
	time_axis = np.arange(0,year_all.size)
    

	if mnames_all[0] != 'Jan':
		print('First month is ',mnames_all[0],' not Jan: Exiting - should check it is not the h0 time stamp problem if CAM data')
       
    
# Find unique months for removal of annual cycle.

	mnames = np.unique(mnames_all)

	''' RESET FEB->JAN h0 FILE TIMESTAMP (CESM1) '''
	#    sst_ts = sst_ts.resample('M')

	''' FIND AND REMOVE ANNUAL CYCLE '''

	print('    > Removing SST Annual Cycles --')
	for imname in mnames :
		imon_ts = mnames_all == imname
		sstm = sst_ts[imon_ts].mean()
		sst_ts[imon_ts] = sst_ts[imon_ts] - sstm    

	''' SET INDICES OF NINO/NINA MONTHS BASED ON SPECIFIED CRITERIA AND THE SEASON '''

	ssta_thresh = np.std(sst_ts)    
	lclimo_months = np.in1d(mnames_all, ['Dec','Jan','Feb'])
	# Find the indices of those months
	iclimo_months = np.where(lclimo_months)[0]


	inino_mons = np.where((sst_ts > ssta_thresh) & lclimo_months)
	inina_mons = np.where((sst_ts < -ssta_thresh) & lclimo_months)

    
	 
    
    
    
    
    


	lplot_sst = True

	''' PLOTTING '''

	if lplot_sst:

		print('    > Setup SST Plotting --')

		mp.figure(1)
		
		tcart_proj = ccrs.PlateCarree(central_longitude=180)
		cart_proj = ccrs.PlateCarree()

		fig = mp.figure(figsize=(22,7))

		axs1 = fig.add_subplot(1,2,1)
		axs2 = fig.add_subplot(2,2,2,projection=tcart_proj)
		axs3 = fig.add_subplot(2,2,4,projection=tcart_proj)
		#    fig, axs = mp.subplots(1,2,figsize=(25, 5))



		it_ticks = np.arange(0,len(year_all),12)    # Time axis arrays



		axs1.plot(time_axis,sst_ts,color='black')
		axs1.set_title(nino+' SSTA for '+run_case,fontsize=20)




		''' TIME AXIS GYMNASTICS '''

		axs1.set_xlabel("Year",fontsize=15) 
		axs1.set_ylabel("K",fontsize=15) 
		axs1.set_xticks(it_ticks+6)
		axs1.set_xticks(it_ticks,minor=True)
		axs1.set_xticklabels(year_all[it_ticks].values,rotation=90.)
		axs1.tick_params(axis = "x", bottom = False) ; axs1.tick_params(which='minor', length=10)

	# Fill above/below zero or +/- 1 std

		fill_min = ssta_thresh

		''' FiLL nino/nina MONTHS THAT ARE USED FOR COMPOSTIING '''

		axs1.fill_between(time_axis,sst_ts,fill_min, where=sst_ts > fill_min,  facecolor='red', interpolate=True)
		axs1.fill_between(time_axis,sst_ts,-fill_min, where=sst_ts < -fill_min,  facecolor='blue', interpolate=True)


		''' PLOT SST THRESHOLD CRITERI LINES FR EVENT (e.g., +/- 1 standard deviation) '''
		axs1.hlines(0., min(time_axis), max(time_axis), color='black',linestyle="solid",lw=1)
		axs1.hlines([-ssta_thresh,ssta_thresh], min(time_axis), max(time_axis), color='black',linestyle="dashed",lw=1)






		''' PLOT REGIONAL DISTRIBUTION OF SSTA '''    

		print('    > Calculating local plotting arrays --')
		

		nino_sst_plot = sst_data[inino_mons[0],:,:].mean(dim=['time'])
		nina_sst_plot = sst_data[inina_mons[0],:,:].mean(dim=['time'])

		climo_sst_plot = sst_data[iclimo_months,:,:].mean(dim=['time'])

		nino_asst_plot = nino_sst_plot-climo_sst_plot
		nina_asst_plot = nina_sst_plot-climo_sst_plot

		# Contour level settings.
		cmin = -3. ; cmax = 3. ; dcont = 0.25
		plevels =  np.arange(cmin,cmax+dcont,dcont,dtype=np.float)



		# Add cyclic point to data
		nino_asst_plot_cycl,lons_cycl= add_cyclic_point(nino_asst_plot, coord=sst_data['lon'])
		nina_asst_plot_cycl,lons_cycl = add_cyclic_point(nina_asst_plot, coord=sst_data['lon'])


		print('    > Plotting SST data --')


		  # Plot nino/nina SSTA data.
		ninop = axs2.contourf(lons_cycl, sst_data.lat, nino_asst_plot_cycl,levels = plevels,cmap='bwr',extend='both',transform=cart_proj)
		ninop = axs3.contourf(lons_cycl, sst_data.lat, nina_asst_plot_cycl,levels = plevels,cmap='bwr',extend='both',transform=cart_proj)
		#    fig.colorbar(ninop,ax=(axs2,axs3),location = 'right',orientation='vertical', pad=0.5)   


		axs2.contour(lons_cycl, sst_data.lat,nino_asst_plot_cycl,levels=plevels,colors='black',linewidths=0.5,transform=cart_proj)
		axs3.contour(lons_cycl, sst_data.lat,nina_asst_plot_cycl,levels=plevels,colors='black',linewidths=0.5,transform=cart_proj)



		 # Data extent?
		axs2.set_extent((-10, 360, -45., 45.),crs=tcart_proj)  
		axs2.set_title('El Nino '+nino+' SST anomalies',fontsize=20) 

		# Define the xticks for longitude

		x_tik = np.arange(0,360.+30.,30.)
		x_tik[-1] =  x_tik[-1]-1.e-9   # Needed to see the cyclic 0 deg label.
		axs2.set_xticks(x_tik, crs=cart_proj)

		lon_formatter = cticker.LongitudeFormatter()
		axs2.xaxis.set_major_formatter(lon_formatter)

		# Define the yticks for latitude

		axs2.set_yticks(np.arange(-45.,45.+15,15.), crs=cart_proj)
		lat_formatter = cticker.LatitudeFormatter()
		axs2.yaxis.set_major_formatter(lat_formatter)

		# Axis label sizes
		axs2.tick_params(labelsize=8) 

		# Mask out land
		axs2.add_feature(cart.feature.LAND, zorder=100, color='black')

		# Add coastlines
		axs2.coastlines()



		# Grab axs2 attributes.
		axs3.set_title('La Nina '+nino+' SST anomalies',fontsize=20) 

		axs3.set_extent(axs2.get_extent())
		axs3.set_xticks(axs2.get_xticks())
		axs3.xaxis.set_major_formatter(axs2.xaxis.get_major_formatter())
		axs3.set_yticks(axs2.get_yticks())
		axs3.yaxis.set_major_formatter(axs2.yaxis.get_major_formatter())


		axs3.tick_params(labelsize=8) 

		# Mask out land
		axs3.add_feature(cart.feature.LAND, zorder=100, color='black')

		# Add coastlines
		axs3.coastlines()


		# Add nino boxes       

		print('    > Adding nino boxes --')

		ys = nino_reg[nino][0]
		yn = nino_reg[nino][1]
		xw = nino_reg[nino][2]
		xe = nino_reg[nino][3]


		nbox = mpatches.Rectangle(xy=[xw, ys], width=xe-xw, height=yn-ys,
										facecolor='gray',
										fill=True,
										alpha=0.7,
										edgecolor = 'black',
										transform=ccrs.PlateCarree())

		nbox1 = mpatches.Rectangle(xy=[xw, ys], width=xe-xw, height=yn-ys,
										facecolor='gray',
										fill=True,
										alpha=0.7,
										edgecolor = 'black',
										transform=ccrs.PlateCarree())

		axs2.add_patch(nbox)
		axs3.add_patch(nbox1)
    
    
    
		print('    > Saving figure --')

		
		fig.savefig(dir_proot+run_case+'_'+nino+'_ssta.png', dpi=100)

	return inino_mons[0],inina_mons[0]











'''
#################################### 
###### CORRECT h0 FILES MONTH ######
#################################### 
'''

def h0_month_fix(hist_tseries_var):
    
    year = hist_tseries_var.time.dt.year
    month = hist_tseries_var.time.dt.month
    
    print(hist_tseries_var.time.time)
    
    hist_tseries_var.time.dt.year[0] = cftime.DatetimeNoLeap(1979, 1, 1, 0, 0, 0, 0)
    
    return hist_tseries_var







'''
#####################################################
##########  GET CORRECT TENDENCY VARIABLES ##########
#####################################################
'''


def cam_tend_var_get(files_ptr,var_name):

# Determining CAM5/CAM6 based on levels.

    nlevs = files_ptr.lev.size
    fvers = files_ptr.variables
#

#    if var_name not in ['STEND_CLUBB','RVMTEND_CLUBB']
#    if var_name in fvers: print
#    if nlevs in [32,30]: 
        
        
    print(np.any(np.isin(files_ptr.variables,var_name)))
# Variable read in and time averaging (with special cases).

#    if var_name == 'DTCOND' and : 
#            var_in = files_ptr['DTCOND'].mean(dim=['time'])+files_ptr['DTV'].mean(dim=['time'])

    if var_name == 'DCQ' and case in ['rC5','rUW']: 
            var_in = files_ptr['DCQ'].mean(dim=['time'])+files_ptr['VD01'].mean(dim=['time'])
    
    if var_name == 'STEND_CLUBB':
       
            var_in = 1005.*(files_ptr['DTV'].mean(dim=['time'])
            +files_ptr['MACPDT'].mean(dim=['time'])/1000.
            +files_ptr['CMFDT'].mean(dim=['time']))
    else :
            var_in = files_ptr[var_name].mean(dim=['time'])           
    
    if var_name == 'DIV':  
            var_in = -files_ptr['OMEGA'].mean(dim=['time']).differentiate("lev")
   
    if var_name in ['OMEGA','ZMDT','ZMDQ']:
            var_in = files_ptr[var_name].mean(dim=['time'])

    return var_in
            
    
  









'''
#########################################################
    COMMON ROUTINE FOR SETTING UP FILES (CAM/Analyses)
#########################################################
'''

## Should get month means of analyses, CAM (h0 and ts files)    
## > ERA5 CISL-RDA ds633.1 : /glade/collections/rda/data/ds633.1/e5.moda.an.pl
## - 1 netcdf file/year (1979=2018)
## > MERRA2  CISL-RDA ds313.3 : /glade/collections/rda/data/ds613.3/1.9x2.5/
## Res. files (not clear where monthly means are) - GRIB!!!   
## >ERA-interim CISL-RDA ds627.1 : /glade/collections/rda/data/
##
## >JRA-55 CISL-RDA ds628.9 : /glade/collections/rda/data/ds628.9/
##
    
def get_files_tseries(case_name,case_type,var_cam,years) :

    
    type_desc = {}
    type_desc['cam'] = ['/glade/p/rneale']


    allowed_types = ['cam','reanal','lens1','lens2','cam6_revert']

    if case_type not in allowed_types : print('-- case_type'+ ' files - type not allowed')
    if case_type     in allowed_types : print('-- case_type'+ ' files - type allowed') 

    print('    -- Grabbing data type/case -- '+case_type+' '+case_name)
 

    yr0 = years[0]
    yr1 = years[1]
    

   
    
## GRAB ANALYSIS ##

    lat_rev = False
    lcoord_names = False

    
## Decode times: Start off = True, set to False if single avarge files)

    decode_times = True

        
    ''' ANALYSIS/OBSERVED '''
        
        
    if case_type=='reanal' :
            
            
        if var_cam != 'TS':
            
            
            # FILES on RDA CISL files
            dir_rda = '/glade/collections/rda/data/'
                
            # FILES on my work dir.
            dir_mydata = '/glade/work/rneale/data/'
            
            # Select correct root directory.
            lfiles_rda = True if case_name in ['ERA5','ERAI','CFSR','ERAI','MERRA2','JRA25'] else False
            
            
         
            
            
            if case_name == 'ERA5' :    # This works but is incredibly slow because it is 0.25 deg.



                rda_cat = 'ds633.1'

                var_anal_fmap = {'T': '130_t',   'Q':'133_q',  'OMEGA':'135_w'}
                var_anal_vmap = {'T': 'T',       'Q':'Q',  'OMEGA':'W'}

                var_vname = var_anal_vmap[var_cam] ; var_fname = var_anal_fmap[var_cam] 

                var_ftype = 'uv' if var_cam in ['U','V'] else 'sc' 


                dir_glade = dir_rda+rda_cat+'/'
                files_glade  = np.array([dir_rda+rda_cat+"/e5.moda.an.pl/%03d/e5.moda.an.pl.128_%s.ll025%s.%03d010100_%03d120100.nc"%(y,var_fname,var_ftype,y,y) for y in range(yr0,yr1+1)])

                lat_rev = True
                lcoord_names = True




            if case_name=='ERAI' :  ## UNFINSHED FOR RDA


                var_anal_fmap = {'T': 't',   'Q':'q' , 'OMEGA':'w'}
                var_anal_vmap = {'T': 'T',   'Q':'Q',  'OMEGA':'w'}
                var_vname = var_anal_vmap[var_cam] ; var_fname = var_anal_fmap[var_cam] 


                if lfiles_rda :

                    rda_cat = 'ds627.1'


                    if var_cam in ['T'] : var_fname = 'sc'
                    if var_cam in ['U','V','OMEGA'] : var_fname = 'uv' 


                    dir_glade = dir_rda+rda_cat+'/'
                    files_glade  = np.array([dir_rda+rda_cat+"/ei.moda.an.pl/ei.moda.an.pl.regn128%s.%03d%02d0100.nc"%(var_fname,y,m) for y in range(yr0,yr1+1) for m in range(1,12)])

                    
                else :

                    files_glade  = np.array([dir_mydata+case_name+"/"+var_fname+".mon.mean.nc"])
                    print(files_glade)
                  

            if case_name=='ERA40' :  ## UNFINSHED
                var_anal_fmap = {'T': 't',   'Q':'q'}
                var_anal_vmap = {'T': 'T',   'Q':'Q'}
                var_vname = var_anal_vmap[var_cam] ; var_fname = var_anal_fmap[var_cam] 
                if var_cam in ['T'] : var_fname = 'sc'
                if var_cam in ['U','V'] : var_fname = 'uv' 
                rda_cat = 'ds627.1'

                dir_glade = dir_rda+rda_cat+'/'
                files_glade  = np.array([dir_rda+rda_cat+"/ei.moda.an.pl/ei.moda.an.pl.regn128%s.%03d%02d0100.nc"%(var_fname,y,m) for y in range(yr0,yr1+1) for m in range(1,12)])
                print(files_glade)


            if case_name=='MERRA2' : #### NOT CLEAR MMEAN DATA AVAILABLE FROM RDA
                resn = '1.9x2.5'
#            var_anal_fmap = {'T': '',   'Q':'q'}
                var_anal_vmap = {'T': 'T',   'Q':'Q'}
                var_vname = var_anal_vmap[var_cam] 
                rda_cat = 'ds313.3'

                dir_glade = dir_rda+rda_cat+'/'
                files_glade  = np.array([dir_rda+rda_cat+"/%s/%03d/MERRA2%03d010100_%03d120100.nc"%(resn,y,y,y) for y in range(yr0,yr1+1)])
                print(files_glade)


            if case_name=='JRA55' : #### NOT CLEAR MMEAN DATA AVAILABLE FROM RDA
                resn = '1.9x2.5'
#            var_anal_fmap = {'T': '',   'Q':'q'}
                var_anal_vmap = {'T': 'T', 'Q':'Q'}
                var_vname = var_anal_vmap[var_cam] 
                rda_cat = 'ds628.3'

                dir_glade = dir_rda+rda_cat+'/'
                files_glade  = np.array([dir_rda+rda_cat+"/anl_p25/%03d/anl_p25.%03d0.nc"%(y,var_fname,y,y) for y in range(yr0,yr1+1) for m in range(1,12)])
                print(files_glade)

            if case_name=='JRA25' : #### Old but nc monthly data available from RDA (1979-2005)
                resn = '1.9x2.5'
#            var_anal_fmap = {'T': '',   'Q':'q'}
                var_anal_vmap = {'T': 'TMP_PRS',   'Q':'Q', 'OMEGA':'W'}


                var_vname = var_anal_vmap[var_cam] 
                rda_cat = 'ds625.1'

                dir_glade = dir_rda+rda_cat+'/'
                files_glade  = np.array([dir_rda+rda_cat+"/anl_p25/anl_p25.%03d%02d.nc"%(y,m) for y in range(yr0,yr1+1) for m in range(1,12)])


 



                
        
#### GRAB CAM SST AMIP DATASET FOR NOW FOR ANALYSES
       
        if (var_cam=='TS') :
            print('-- Grabbing SST file(s) for AMIP and REANALYSES from CESM inputdata -')
            dir_inputdata = '/glade/p/cesmdata/cseg/inputdata/atm/cam/sst/'
            hadisst_file = 'sst_HadOIBl_bc_0.9x1.25_1850_2020_c210521.nc'
            files_glade = dir_inputdata+hadisst_file
            var_vname = 'SST_cpl'

   
    ''' MODEL OUTPUT '''

#### Common CAM->CF variable mapping

    vars_cf = {'TS' : 'ts', 'T': 'ta',   'Q':'hus' , 'Z3': 'hgt',   'U':'ua', 'V':'va',  'OMEGA':'wap'}
   
    
   








    if case_type =='lens1': ## LARGE ENSEMBLE WITH CESM1 ##
 
        dir_lens = '/glade/campaign/cesm/collections/cesmLE/CESM-CAM5-BGC-LE/atm/proc/tseries/monthly/'
 
        print('    -- Grabbing file(s) for LENS1(CESM1) - Variable = ',var_cam)

        dir_files_stub = dir_lens+var_cam+'/'+case_name+'.cam.h0' # Need OS call here
        
        files_glade = sp.getoutput('ls '+dir_files_stub+'*nc')
       
        var_vname = var_cam

        
        
   
        
        
    
    if case_type =='lens2':   ## LARGE ENSEMBLE WITH CESM2 ##
        
# Complex ensembles structures. Multiple files need to be trimmed forom directory listing.
        
 
        dir_lens = '/glade/campaign/cgd/cesm/CESM2-LE/timeseries/atm/proc/tseries/month_1/'
        
        print('    -- Grabbing file(s) for LENS2(CESM2) - Variable = ',var_cam)

        # Directory with input files.
        dir_files = dir_lens+var_cam+"/"
        
        # Iritated os call, cannot do wild cards and it does a local list and not an absolute path!!!
        files_glade_all = np.array(os.listdir(dir_lens+var_cam))  # List all files in variable directory
             

        # Have to trim file list according to the case_name
        files_in_list = np.array([case_name in each_file for each_file in files_glade_all])

        # Now I have to sort to get the numerical ordering of years right.
        files_glade = np.array(files_glade_all[files_in_list])
        files_glade = np.sort(files_glade)

        # Add the absolute path 
        files_glade = np.array([dir_files+file_string for file_string in files_glade])
     
                               
        var_vname = var_cam
  







        
    if case_type =='c6_amip':     ## ENSEMBLE OF AMIP CAM6 RUNS FROM CMIP6 ##
       
        dir_lens = '/glade/collections/cdg/data/CMIP6/CMIP/NCAR/CESM2/amip/'
        var_cf = vars_cf[var_cam]

        print('    -- Grabbing file(s) for CAM5-AMIP - Variable = ',var_cam)

        dir_files_stub = dir_lens+case_name+'/Amon/'+var_cf+'/gn/latest/' 
        
        
        files_glade = np.array(os.listdir(dir_files_stub))  # List all files in variable directory
#        files_glade = sp.getoutput('ls '+dir_files_stub+'*nc')
        files_glade = np.array([dir_files_stub+file_string for file_string in files_glade])
        var_vname = var_cf   
        
        lcoord_names = True
        
        
        

        
    if case_type =='cam6_revert': # Complex ensembles structures
    
    
        dir2_cam = '/glade/campaign/cgd/amp/rneale/revert/' # Some output is here
        dir_cam = '/glade/p/cgd/amp/amwg/runs/' # Run firectories with history files  	
	
        
        dir_files = dir_cam+case_name+'/atm/hist/'

#		# If directory empty, try location #
#		if len(os.listdir(dir_files)) == 0:	dir_files = dir_cam2+case_name+'/atm/hist/'


        files_stub = case_name+''+'.cam.h0.'
        
        
        # Iritated os call, cannot do wild cards and it does a local list and not an absolute path!!!
        files_glade_all = np.array(os.listdir(dir_files))  # List all files in variable directory
        
        # Have to trim file list according to the case_name
        files_in_list = np.array([files_stub in each_file for each_file in files_glade_all])
        
         # Now I have to sort to get the numerical ordering of years right.
        files_glade = np.array(files_glade_all[files_in_list])
     
        files_glade = np.sort(files_glade)
    
        
        # Grab yr0 to yr1 range (by finding Jan y0 file and Dec yr1 files - now that they are sorted.
        iyr0_jan = list(files_glade).index(files_stub+str(yr0)+'-01.nc')
        iyr1_dec = list(files_glade).index(files_stub+str(yr1)+'-12.nc')
        
     
        
        # Subset files for required yearly/month range
        # NOT SURE WHY THIS NEEDS TO BE +1 BUT IT DOES OTHERWIS EWE MISS THE LAST DECEMBER
        files_glade = files_glade[iyr0_jan:iyr1_dec+1]
     
        
        # Add the absolute path 
        files_glade = np.array([dir_files+file_string for file_string in files_glade])
        
        var_vname = var_cam
        
        
        
        
        
        
        
        
        
        
    print('    -- PROCESSING FILE(S) ->>')

#    if  not isinstance(files_glade,(str,list)) :   
#        files_glade = list(files_glade)
        
    
    if not isinstance(files_glade,(str,list)) :
        print('    --> First/Last (',len(files_glade),' total number of files)')
        print('    -',files_glade[0])
        print('    -',files_glade[-1])
    else:
        print('    --> Single file')
        print('    -',files_glade)

   
            
## POINT TO FILES ##

  
#    data_files = xr.open_mfdataset(files_glade,parallel=True,chunks={"time": 100})  ; 2.52mins (ERA5: 1979-1990)
    data_files = xr.open_mfdataset(files_glade, decode_cf=True, decode_times=True, parallel=True,chunks={"time": 12}) # 3 mins ERA5: 1979-1990
    

    if lcoord_names : data_files = change_coords(data_files,var_cam,case_type,case_name)

#    if lcoord_names : data_files = data_files.rename({'latitude':'lat', 'longitude':'lon', 'level':'lev'})
    
# Reverse lat array to get S->N if needed
    if lat_rev : data_files = data_files.reindex(lat=list(reversed(data_files.lat)))


# Datset info.
  
    print('    -- FILE(S) AVAILABLE TIME RANGE - > ',min(data_files.time.dt.year.values),' to' ,max(data_files.time.dt.year.values))
    print('')
    print('Dataset required memory =',data_files.nbytes)        
    
    return data_files,var_vname















''' 
#########################################################
    CHANGE COORD NAMES IF NEEDED 
#########################################################

-Read in data files and change coord names if needed


'''

def change_coords(data_files_in,var_cam_in,case_type_in,case_name_in) :
    
    data_files_out = data_files_in
    
      
    if var_cam_in != 'TS' :
        if case_name_in in ['ERA5'] :
            data_files_out = data_files_in.rename({'latitude':'lat', 'longitude':'lon', 'level':'lev'})
    
        if case_type_in in ['c6_amip'] :
            data_files_out = data_files_in.rename({'plev':'lev'})
            data_files_out['lev'] = 0.01*data_files_out.lev  # pa->mb
            

                
# Return modified files with new coord. names.
    return data_files_out



















'''
#########################################################
    GRAB CLIMOS OF TIME MEAN NINO AND NINA
#########################################################
'''



def get_files_climo(case_name,case_type,var_cam,years) :


#### Just GRAB the single files for climo, nino and nina.
           
	print('-- File time type is climatological --')

	# FILES on my work dir.
	dir_mydata = '/glade/work/rneale/data/'

	var_anal_map  = {'T': 'ta',   'Q':'hus' , 'Z3': 'hgt',   'U':'ua', 'V':'va',  'OMEGA':'omega'}
	var_vname = var_anal_map[var_cam]

	case_glade0 = dir_mydata+case_name+'/'+case_name+'_'

	# Grab named climo/nino/nina files
	files_glade = case_glade0+np.char.array(['climo_DJF.nc','nino_DJF.nc','nina_DJF.nc'])

	# Read files onto same dataset, but don't decdode times.
	print('    -- CLIMO FILE SET')
	print(files_glade)
	data_files = xr.open_mfdataset(files_glade, decode_cf=True, decode_times = False,concat_dim='time', combine='nested') # 3 mins ERA5: 1979-1990
#	data_files = data_files.isel(time=slice([1,2,12])).mean(dim='time')



	return data_files,var_vname












	
	


	





	
	
	
	
	
	
	
	




