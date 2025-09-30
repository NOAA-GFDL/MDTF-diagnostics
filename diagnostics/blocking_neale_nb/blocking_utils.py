'''
	BLOCKING UTILIY ROUTINES
'''




'''
    block_data - Reads in and processes data beofre sending back to be operated on
    block_freq1d - Calculates 1D blocking frequencies (longitude) - D'Andrea et al. ƒ(1998)
    block_freq2d - Calculates 2D blocking frequencies (latitude/longitude) - 

'''

import xarray as xr
import pandas as pd
import numpy as np

import importlib
import sys
import pprint
import time





def ens_setup(ens_name,ens_mem_num,ystart,yend):

# Construct and display Settings

    ens_info = find_ens_info(ens_name,ens_mem_num,ystart,yend)  
   
    

    return ens_info




############################################
# Set ensemble/single/obs case information #
############################################

# TO DO 
# - Functionaity to read in existing, pre calculated datasets 
# - If just one ensemble mem print out single case name.

def find_ens_info(ens_names,mem_num,ystart,yend):

    
    import lens_simulations as sim_names
    importlib.reload(sim_names)

    obs_sources = ['ERA5','MERRA','ERAI']

    fname = '-> find_ens_info -> '
    
    all_ens_info = {}    

    
# Loop ensemble sets (ensembles/obs/singlecases)
    
    for iens,ens_name in enumerate(ens_names):

        print(fname,'L66 Ensemble name: ',ens_name)
        
        if ens_name in ['CESM1','CESM2','E3SMv1','E3SMv2','EAMv2','CAM6']:
            run_names = sim_names.get_ens_set_names(ens_name,mem_num[iens])
        else:
            run_names = [ens_name]
    
        
        match (ens_name):
            case 'CESM1':
                
                ens_type = 'model'
                dir_ens0 = '/glade/campaign/cesm/collections/cesmLE/CESM-CAM5-BGC-LE/atm/proc/tseries/' 
                dir_day_add = 'daily'

                file_templates = [(dir_ens0+dir_day_add+'/VAR_TBD/'+this_run+'.cam.h1.VAR_TBD.19200101-20051231.nc') for this_run in run_names]      
                
                # Need to modify start date for CESM1 ens# 1. 
                run_ens1 = 'b.e11.B20TRC5CNBDRD.f09_g16.001'
                if run_ens1 in run_names:
                    file_templates[run_names == run_ens1]=file_templates[run_names == run_ens1].replace('1920','1850',1)
                                
            case 'CESM2':
                
                # CESM2 is tricky for the files.
                # Place hold for now and grab the date specific files later.
                ens_type = 'model'
                dir_ens0 = '/glade/campaign/cgd/cesm/CESM2-LE/atm/proc/tseries/'
                dir_day_add = 'day_1'
                file_templates = [(dir_ens0+dir_day_add+'/VAR_TBD/'+this_run+'.cam.h1.VAR_TBD.DATE_RANGE.nc') for this_run in run_names]    

            case 'E3SMv1':
                
                ens_type = 'model'
                dir_ens0 = '/glade/campaign/cgd/amp/rneale/e3sm/'
                dir_day_add = 'day_1'
                file_templates = [(dir_ens0+this_run+'/tseries/'+this_run+'_dmeans_ts_VAR_TBD.nc') for this_run in run_names]
                
            case ens_name if ens_name in ['E3SMv2','EAMv2','CAM6']:
                
                ens_type = 'model'

                if ens_name == 'CAM6':   # CAM6 different locations
                    cmodel = 'cam'
                    dir_ens0 = '/glade/campaign/cesm/development/cvcwg/cvwg/f.e21.FHIST_FSSP370_BGC.f09_f09.ersstv5.goga/'
                else:
                    cmodel = 'eam'
                    dir_ens0 = '/glade/campaign/cgd/ccr/E3SMv2/FV_regridded/'

                
                dir_day_add = 'day_1'


                
                file_templates = [(dir_ens0+this_run+'/atm/proc/tseries/'+dir_day_add+'/'+this_run+'.'+cmodel+'.h1.VAR_TBD.DATE_RANGE.nc') for this_run in run_names]
                
               
                # Modify filename at range accordingly
                if ens_name=='EAMv2' : file_templates=[fl.replace('DATE_RANGE','19760101-20141231',1) for fl in file_templates]
                if ens_name=='E3SMv2': file_templates=[fl.replace('DATE_RANGE','18500101-20141231',1) for fl in file_templates]
                if ens_name=='CAM6'  : file_templates=[fl.replace('DATE_RANGE','18800101-20150101',1) for fl in file_templates]

            case ens_name if 'b.e23' in ens_name: # Individual CESM3 development run cases

                ens_type = 'model'
                dir_ens0 = '/glade/derecho/scratch/hannay/archive/'
                file_templates = [(dir_ens0+this_run+'/atm/hist/'+this_run+'.'+cmodel+'.h1..nc') for this_run in run_names]
        
        
            case ens_name if ens_name in obs_sources:
                
                ens_type='obs'
                dir_ens0 = '/glade/work/rneale/data/'+ens_name+'/'  
                file_templates = [dir_ens0+'VAR_TBD.day.mean.nc']
                
            case _  : 
                
                print(f'Looking for case {ens_name}, assuming it is an MDTF case')
                ens_type = 'model'
                file_templates
            #    print(ens_name+' is not a recognized case or ensemble set')
            #    sys.exit(0)       

# Loop over ensembles to get the file to be read in.

            
        all_ens_info[ens_name] = [ens_type,mem_num[iens],ystart[iens],yend[iens],run_names,file_templates]  

    
#    pprint.pprint(all_ens_info)
    print(fname,'Dict before DataFrame:',all_ens_info)
    df_info = pd.DataFrame.from_dict(all_ens_info, orient='index',columns=['Ensemble Type','Ensemble Size','Start Year','End Year','Run Name','Run File'])
#    df_info = pd.DataFrame(data=all_ens_info)
#    display(df_info)
    
    return df_info


###################################
# Read in data for analysis
###################################

# To do
# - Some kwargs so that there are some assumptions (like nhem) can overridden and args don't always have to be passed.

def dataset_get(block_meta,var_name,season,diag_hem):

    fname = '-> dataset_get -> '

    tstart = time.time()
    
    ens_names = list(block_meta.index)

    # Request info.

    print(fname+ 'Requested season     : ',season)

    # Final dataset dictionary
    ds_ens = {}
    
    # Loop ensemble sets to setup datasets
    for iens,ens_name in enumerate(ens_names):
                        
        run_files = block_meta.loc[ens_name]['Run File']
        print(fname,'== Starting ensemble: ',iens,ens_name,'Type:',type(run_files))

        run_names = block_meta.loc[ens_name]['Run Name']
        date_start = block_meta.loc[ens_name]['Start Year']
        date_end = block_meta.loc[ens_name]['End Year']

        num_runs = len(run_names)    
        # Shorten any dates to the first 4 digits (str needed for slicing)
        year_start = str(date_start)[:4]
        year_end   = str(date_end)[:4]

     # MDTF cases are already opened as xarray datasets
        type_run_file = type(run_files)
        if isinstance(run_files, xr.Dataset):
            print(fname,'Run file is already an xarray dataset, trying to use it as such')
            ds_run = run_files
            ds_run = ds_run.expand_dims(name=[ens_name])  # Add 'name' dimension
        else:  
            # Open the files specified in the run_files list
            print(fname,'Opening run_files:',run_files)
            # Replace VAR placeholder with actual var
            run_files = [sub.replace('VAR_TBD', var_name) for sub in run_files]

            print(fname,'Opening ensemble files',ens_name,' - ',num_runs,' ensemble(s)')
            print(fname+ 'Requested year range : ',year_start,'-',year_end)

            # Chunk sizes
            chunk_sizes = {'time': 365, 'latitude': 360, 'longitude': 180}
            
            
            # Grab each dataset separately (will require some work for CESM2 as they are in decadal files.)
            
            for irun,run_file in enumerate(run_files):    
                print(fname,'Opening file: ',irun,run_file, 'ensemble: ',ens_name)
                match(ens_name):
                    
                    case 'ERA5':
                        ds_run = xr.open_mfdataset(run_file,parallel=True,chunks=chunk_sizes)
                        
                    case 'CESM2': 
                        # Just concatonate all files for now. (after changing DATE to *)
                        run_file = run_file.replace('DATE_RANGE', '*')
                        ds_run = xr.open_mfdataset(run_file,parallel=True,chunks=chunk_sizes)
                        
                    case _ :

                        
                            ds_run = xr.open_mfdataset(run_file,combine="nested",parallel=True,chunks=chunk_sizes)
                            # Data on the file is in silly Julian days that need to be converted to gregorian
                            print(fname,'L243 Finished opening')
                            if ens_name in ['ERAI','MERRA']:
                                    ds_run['time'] = pd.to_datetime(ds_run['time'], origin='julian', unit='D')
                            if ens_name in ['ERAI']:
                                    ds_run = ds_run.reindex(lat=ds_run.lat[::-1])
                            
# Subset for years and season 
        
        ds_run = ds_run.sel(time=slice(year_start,year_end))    
        print(f'DRBDBG {irun=}')                 
        # Append datasets

        if irun==0 :
            ds_this_ens = ds_run
        else:
            # Add 'name' dimension so files to concat are the same
            if 'name' not in ds_run.dims:
                ds_run = ds_run.expand_dims({'name': [irun]})
            else:
                # if it already has 'name' dim but with wrong label/length, replace coord
                ds_run = ds_run.assign_coords(name=('name', [irun]))
            ds_this_ens = xr.concat([ds_this_ens, ds_run], 'name')
        
# Name the dataset dimension from from name
        if not isinstance(run_names, list):
            run_names = [run_names]
        ds_this_ens = ds_this_ens.assign_coords(name = ("name", run_names))

        if num_runs == 1:
            ds_this_ens[var_name] = ds_this_ens[var_name].expand_dims(name=run_names)
        
        ds_ens[ens_name] = ds_this_ens 

# End of isinstance xr.dataset logic    
    # Year range check
        ystart_data = ds_run['time'].dt.year.min().item()
        yend_data = ds_run['time'].dt.year.max().item()
        
        if (ystart_data != int(year_start) or yend_data != int(year_end)): 
            print(fname,'   *Warning* ',ens_name,' ensemble data years do not match requested years',ystart_data,'-',yend_data)  
            
        ds_run = ds_run.sel(time=ds_run['time.season'] == season)
    

    
    print(fname,f'Duration: {time.time() - tstart}') ; print()
    
    return ds_ens
    

























#####################################################################
# Calculate 2D blocking idex based on Z500 
# Davini et al., (2012) http://doi.org/10.1029/2012GL052315
#####################################################################

# To do
# - Some kwargs so that there are some assumptions (like nhem) can overridden and args don't always have to be passed.



def block_z500_freq(block_meta,ens_ds,fout_dir,bseason,block_diag=None,file_opts='x'):

    fname = '-> block_z500_freq -> '
    print(fname,'Starting freq blocking calculation')

    ens_names = list(block_meta.index)

    block_freq_ens = {}  # Dictionary for ensemble specific block freq.


    
    #### Loop if we need to write or just calculate.    

    ghgn_thresh = -5.
    ghgs_thresh = 0.
    
    # Latitude range to read in
    lat_s_in = 35.
    lat_n_in = 75.

    # Latitude range for moving 2D latitude ghg calculation.

    dlat_2d = 15.
    
    # Baseline latitudes for the block calculation.
    blat0 = 60. 
    blatn = 78.85
    blats = 41.25                                                                                                                                                                                                                                                                          
    # Nominal Block latitude ranges (with lat deltas)
    deltas = [-3.75,0.,3.75] 

    blats_0= [blat0+i for i in deltas]
    blats_n= [blatn+i for i in deltas]
    blats_s= [blats+i for i in deltas]

    
   
    
    # Loop over ensembles sets (read in write out if needed)
    
    for iens,ens_name in enumerate(ens_names):

        tstart = time.time()

        block_freq = None

        year_start = block_meta.loc[ens_name]['Start Year']
        year_end = block_meta.loc[ens_name]['End Year']
        nens_mem = block_meta.loc[ens_name]['Ensemble Size']
        
        # Check if the file exists and set the file options accordingly (promote 'x' to 'r' or 'w')
        file_opts_checked, file_path = set_file_name_and_check_existance(ens_name, nens_mem, year_start, year_end, bseason, file_opts, block_diag, fout_dir)

        if file_opts_checked in ['w']: # Do not calculate if just reading in. (No more 'x' since that is changed to 'w' or 'r' in set_file_name_and_check_existance)

            ds_this_ens = ens_ds[ens_name]
        
        # Grab data and variable        
            ens_z500 = ds_this_ens['Z500'] #DRBDBG sub varname here
    
        # Subset required latitude limits.
            ens_z500 = ens_z500.sel(lat=slice(lat_s_in,lat_n_in))
    
        # Grab actual latitudes nearest blats_x on the data grid
            blats_ng = ens_z500.lat.sel(lat=blats_n, method="nearest")
            blats_0g = ens_z500.lat.sel(lat=blats_0, method="nearest")
            blats_sg = ens_z500.lat.sel(lat=blats_s, method="nearest")
    
            
        # Calculate Z500 for on-grid N,S and central points for all longitudes.   
            
            z500_blats_n = ens_z500.sel(lat=blats_ng)
            z500_blats_0 = ens_z500.sel(lat=blats_0g)
            z500_blats_s = ens_z500.sel(lat=blats_sg)
    

            print(fname,' Calculating blocking statistics for ',ens_name)

            match(block_diag):
               
                case '1D':

                    #### 1D : :This code flags each day as 'blocked' if the thresholds are met, for the 3 lat bounds (deltas)
                
                    for idel in range(0,len(deltas)):

                         blat_ni = blats_ng[idel]
                         blat_0i = blats_0g[idel]
                         blat_si = blats_sg[idel]
            
                
                        # Tricky code: Basically it prevents duplicate lat being retained in a lat dimenstion. This happens if resolution of data is course.
                        # It trims the lat index to the first one identified (then if there are 2 values it goes to the first. Hence the min()) 
                        
                         z500_blat_ni = z500_blats_n.isel(lat=min(np.where(blats_ng == blat_ni))[0])
                         z500_blat_0i = z500_blats_0.isel(lat=min(np.where(blats_0g == blat_0i))[0])
                         z500_blat_si = z500_blats_s.isel(lat=min(np.where(blats_sg == blat_si))[0])
                                                   
                       
                         # Find local gradients for every ensemble, time and longitude (big) 
                         ghgn = (z500_blat_ni-z500_blat_0i) / (blat_ni-blat_0i)    
                         ghgs = (z500_blat_0i-z500_blat_si) / (blat_0i-blat_si)  
            
                        # Initialize blocked boolean to False
                         if idel == 0:
                            is_blocked = z500_blat_0i.astype('bool').rename('is_blocked')
                            is_blocked = xr.where(is_blocked, False, is_blocked)  # Initialize to False
                        
                         # Boolean for saying whether a time and longitude point is blocked or not 
                         is_blocked_idel =  xr.where((ghgs > ghgs_thresh) & (ghgn < ghgn_thresh),True,False)
                         is_blocked = np.logical_or(is_blocked_idel,is_blocked)

                case '2D':
                    
                ### 2D (loop latitudes)


                    # Initialize blocked boolean to False
                 
                    is_blocked = ens_z500.astype('bool').rename('is_blocked')
                    is_blocked = xr.where(is_blocked, False, is_blocked)  # Initialize to False

                    ghgn = xr.zeros_like(ens_z500)
                    ghgs = xr.zeros_like(ens_z500)
                    print(f"{fname} {ghgn.dims=} ")

              
                    for ilat,blat_0 in enumerate(ens_z500.lat.sel(lat=slice(lat_s_in,lat_n_in))):               


                        blat_n = blat_0+dlat_2d
                        blat_s = blat_0-dlat_2d
                        
                        z500_blat_n = ens_z500.sel(lat=blat_n, method="nearest")
                        z500_blat_0 = ens_z500.sel(lat=blat_0, method="nearest")
                        z500_blat_s = ens_z500.sel(lat=blat_s, method="nearest")
                        
                        # Use all times & all lons, choose lat = ilat
                        loc_dict = dict(time=slice(None), lat=ilat, lon=slice(None))
                        ghgn.loc[loc_dict] = (z500_blat_n-z500_blat_0) / (blat_n-blat_0)
                        ghgs.loc[loc_dict] = (z500_blat_0-z500_blat_s) / (blat_0-blat_s)  

                        
                        
                    # Boolean for saying whether a time, lat and lon point is blocked or not 
                    is_blocked =  xr.where((ghgs > ghgs_thresh) & (ghgn < ghgn_thresh),True,False)

                case _ :
                    print (fname,' No such blocking diagnostic - ',block_diag)
                    sys.errror(0)
            
        # Determine frequency
            
            block_days = is_blocked.sum(dim='time')
            block_freq = block_days / is_blocked.sizes['time']


            # Read or write file of block values
        block_freq = block_file_read_write(ens_name,nens_mem,year_start,year_end,bseason,block_freq,block_diag,file_opts_checked,file_path=file_path)  

       
        bmin = 100.*(block_freq.min()) ; bmax = 100.*(block_freq.max())
        
        print(fname,'Min/max blocking frequency for ensemble ',ens_name,' = ',bmin.values,',',bmax.values)

   


        
    # Push this ensemble to a dictionary, and bring in meemory so it in't repeatedly happening for the plotting routine.
    
        block_freq_ens[ens_name] = block_freq.compute()

    
    # To do: Write out and read in the blocking logical and or frequency data 
    # Turn into a dataframe?
        
        # ENS ENSEMBLE LOOP
    
    
    return block_freq_ens






#################################################################################
#    Logic for reading/writing files with block related values for this ensemble 
#################################################################################    
def block_file_read_write(ens_name,nens,year_start,year_end,bseason,block_array_ens,block_diag,file_opts,file_path='missing'):



    fname = '--> block_file_read_write -> '   
   

    match(file_opts):
    
        case 'w' : 
            print(fname,'Writing file ', file_path)  
            block_array_ens = block_array_ens.rename('BLOCK_'+block_diag)
            block_array_fout = block_array_ens.to_dataset()

            block_array_fout.to_netcdf(file_path)
            print(fname,'Done ...')
            
            return block_array_ens # Just for pass through back to main routine
            
        case 'r' : 
            print(fname,'Reading file ',file_path)
            block_ens_fin =  xr.open_dataset(file_path)['BLOCK_'+block_diag]
          

            print(fname,'Done ...')
            
            return block_ens_fin


            return block_array_ens # Just for pass through back to main routine

        case _ :
            
            print(fname,'Unknown read/write options - should be r or w by now ' ,file_path )
            sys.exit(0) 

def set_file_name_and_check_existance(ens_name, nens, year_start, year_end, bseason, file_opts, block_diag, fout_dir):
    # This function sets the file name and checks if it exists
    # and sets the file options accordingly.
    # It also creates the output directory if it does not exist.
    # It returns the file options, full file path 
 
    from pathlib import Path

    fname = '--> set_file_name_and_check_existance -> '   

    file_netcdf = 'block_' + block_diag +'_' + str(ens_name) + '_' + 'nens.'+ str(nens) +'_'+ year_start+ '-' + year_end + '_' +bseason+'.nc' 
    file_data = fout_dir+'/'+file_netcdf
  
    Path(fout_dir).mkdir(parents=True, exist_ok=True)

    # File_opts = 'x'  is used here to mean write out if file does not exist, and read in if it does.
    # Logic here determines if it is changed to 'r' or 'w' for the read/write options.
    if file_opts == 'x' :  
            print(fname,' called with file_opts = x, Checking if file is already written')
            if Path(file_data).is_file():
                print(fname,'File exists, reading in ...')
                file_opts = 'r'
            else:
                print(fname,'File does not exist, writing out ...')
                file_opts = 'w'
    return file_opts,file_data      

    



















































#####################################################################
# OLD ROUTINE - Calculate 1D blocking idex based on Z500 
# Following D'Andrea, 1998) https://doi.org/10.1007/s003820050230
#####################################################################

# To do
# - Some kwargs so that there are some assumptions (like nhem) can overridden and args don't always have to be passed.

def block_z500_1d(block_meta,ens_ds,bseason,file_opts='x'):

    fname = '-> block_z500_1d -> '
    print(fname,'Starting 1D blocking calculation')

    ens_names = list(block_meta.index)

    block_freq_ens = {}  # Dictionary for ensemble specific block freq.
    
    file_netcdf = 'block_1d_freq_test.nc' 


    #### Loop if wened to write or just calculate.    

    ghgn_thresh = -5.
    ghgs_thresh = 0.
    
    # Latitude range to read in
    lat_s_in = 10.
    lat_n_in = 80.

    # Basleline latitudes for the block calculation.
    blat0 = 60. 
    blatn = 78.85
    blats = 41.25                                                                                                                                                                                                                                                                          
    # Nominal Block latitude ranges (with lat deltas)
    deltas = [-3.75,0.,3.75] 

    blats_0= [blat0+i for i in deltas]
    blats_n= [blatn+i for i in deltas]
    blats_s= [blats+i for i in deltas]

    
   
    
    # Loop over ensembles sets (read in write out if needed)
    for iens,ens_name in enumerate(ens_names):

        tstart = time.time()

        block_freq = None

        year_start = block_meta.loc[ens_name]['Start Year']
        year_end = block_meta.loc[ens_name]['End Year']
        nens_mem = block_meta.loc[ens_name]['Ensemble Size']
        
                
        if file_opts in ['w','x']: # Do not calculated if just reading in.

        
            ds_this_ens = ens_ds[ens_name]
        
        # Grab data and variable        
            ens_z500 = ds_this_ens['Z500']
    
        # Subset required latitude limits.
            ens_z500 = ens_z500.sel(lat=slice(lat_s_in,lat_n_in))
    
        # Grab actual latitudes nearest blats_x on the data grid
            blats_ng = ens_z500.lat.sel(lat=blats_n, method="nearest")
            blats_0g = ens_z500.lat.sel(lat=blats_0, method="nearest")
            blats_sg = ens_z500.lat.sel(lat=blats_s, method="nearest")
    
            
        # Calculate Z500 for on-grid N,S and central points for all longitudes.   
            
            z500_blats_n = ens_z500.sel(lat=blats_ng)
            z500_blats_0 = ens_z500.sel(lat=blats_0g)
            z500_blats_s = ens_z500.sel(lat=blats_sg)
    
          
            
        # This code flags each day as 'blocked' if the thresholds are met, for the 3 lat bounds (deltas)
    
            for idel in range(0,len(deltas)):
                 blat_ni = blats_ng[idel]
                 blat_0i = blats_0g[idel]
                 blat_si = blats_sg[idel]
    
        
        # Tricky code: Basically it prevents duplicate lat being retained in a lat dimenstion. This happens if resolution of data is course.
        # It trims the lat index to the first one identified (then if there are 2 values it goes to the first. Hence the min()) 
                
                 z500_blat_ni = z500_blats_n.isel(lat=min(np.where(blats_ng == blat_ni))[0])
                 z500_blat_0i = z500_blats_0.isel(lat=min(np.where(blats_0g == blat_0i))[0])
                 z500_blat_si = z500_blats_s.isel(lat=min(np.where(blats_sg == blat_si))[0])
                
    
                 if idel==0 : 
                    is_blocked = z500_blat_0i.astype('bool')
                    is_blocked = xr.where(is_blocked, False, is_blocked)  # Initialize to False
               
                 # Find local gradients for every ensemble, time and longitude (big) 
                 ghgn = (z500_blat_ni-z500_blat_0i) / (blat_ni-blat_0i)    
                 ghgs = (z500_blat_0i-z500_blat_si) / (blat_0i-blat_si)  
    
    
                 # Boolean for saying whether a time point is blocked or not 
                 is_blocked_idel =  xr.where((ghgs > ghgs_thresh) & (ghgn < ghgn_thresh),True,False)
                 is_blocked = np.logical_or(is_blocked_idel,is_blocked)
    
            
        # Determine frequency
            
            block_days = is_blocked.sum(dim='time')
            block_freq = block_days / is_blocked.sizes['time']


            # Read or write file of block values
        block_freq = block_file_read_write(ens_name,nens_mem,year_start,year_end,bseason,block_freq,file_opts) 

       
        bmin = 100.*(block_freq.min(dim='lon')) ; bmax = 100.*(block_freq.max(dim='lon'))
        
        print(fname,'Min/max blocking frequency for ensemble ',ens_name,' = ',bmin.values,',',bmax.values)

   


        
    # Push this ensemble to a dictionary, and bring in meemory so it in't repeatedly happening for the plotting routine.
    
        block_freq_ens[ens_name] = block_freq.compute()

    
    # To do: Write out and read in the blocking logical and or frequency data 
    # Turn into a dataframe?
        
        # ENS ENSEMBLE LOOP
    
    
    return block_freq_ens


