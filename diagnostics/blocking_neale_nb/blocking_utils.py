'''
    BLOCKING UTILITY ROUTINES (blocking_neale_nb)

    ens_setup / find_ens_info - table (block_meta) of the obs and model ensembles to compare against
    dataset_get               - opens daily Z500 for every dataset in block_meta
    block_z500_freq           - blocking frequency, with block_diag:
                                  '1D'   by longitude, for a season (D'Andrea et al. 1998)
                                  '2D'   by latitude and longitude, for a season (Davini et al. 2012)
                                  '1DAC' annual cycle (day of year x longitude) of the 1D index
                                Results are cached as netCDF (see block_z500_freq).
'''

import xarray as xr
import pandas as pd
import numpy as np

import importlib
import os
import shutil
import sys
import pprint
import time

# Version of the blocking calculation. It is saved in every blocking frequency
# file, and a file with another version (or none) is recomputed instead of reused.
# Bump it whenever a change alters the results (e.g. 2: Z500 read over 20-90N).
BLOCKING_CALC_VERSION = 2





def ens_setup(ens_name,ens_mem_num,ystart,yend):

# Construct and display Settings

    ens_info = find_ens_info(ens_name,ens_mem_num,ystart,yend)  
    pprint.pprint(ens_info)
    

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


            case 'timeslice3':  # MDTF v3 timeslice CESM run (1995-2014), public archive; a reference like the obs

                ens_type = 'obs'
                dir_ens0 = '/glade/campaign/cgd/amp/bundy/mdtf/cesm_mdtfv3_timeslice_public/atm/day/'
                file_templates = [dir_ens0+'cesm_mdtfv3_timeslice.VAR_TBD.day.nc']

            case ens_name if ens_name in obs_sources:
                
                ens_type='obs'
                dir_ens0 = '/glade/work/rneale/data/'+ens_name+'/'  
                file_templates = [dir_ens0+'VAR_TBD.day.mean.nc']
                
            case _  :
                raise ValueError(f'{fname} Unknown ensemble or obs name {ens_name!r} in MDTF_BLOCKING_ENSEMBLES')
            #    print(ens_name+' is not a recognized case or ensemble set')
            #    sys.exit(0)       

# Loop over ensembles to get the file to be read in.

            
        all_ens_info[ens_name] = [ens_type,mem_num[iens],ystart[iens],yend[iens],run_names,file_templates]  

    
    df_info = pd.DataFrame.from_dict(all_ens_info, orient='index',columns=['Ensemble Type','Ensemble Size','Start Year','End Year','Run Name','Run File'])

    
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

     # MDTF cases might be already opened as xarray datasets. But need to add 'name' dimension.
        if not isinstance(run_names, list):
            run_names = [run_names]
        if isinstance(run_files, xr.Dataset):
            print(fname,'Run file is already an xarray dataset, trying to use it as such')
            ds_run = run_files.sel(time=slice(year_start,year_end))
            ds_this_ens = ds_run.expand_dims(name=run_names)  # Add 'name' dimension
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
            ds_runs = []
            for irun,run_file in enumerate(run_files):    
                print(fname,' Opening file: ',irun,run_file, 'ensemble: ',ens_name)
                match(ens_name):
                    
                    case 'ERA5':
                        ds_run = xr.open_mfdataset(run_file,parallel=True,chunks=chunk_sizes)
                        
                    case 'CESM2': 
                        # Just concatonate all files for now. (after changing DATE to *)
                        run_file = run_file.replace('DATE_RANGE', '*')
                        ds_run = xr.open_mfdataset(run_file,parallel=True,chunks=chunk_sizes)
                        
                    case _ :
                            ds_run = xr.open_mfdataset(run_file,combine="nested",parallel=True,chunks=chunk_sizes)
                            print(fname,'Finished opening',ds_run)
                            
                            if ens_name in ['ERAI','MERRA']:  #Change from Julian days to gregorian calendar
                                    ds_run['time'] = pd.to_datetime(ds_run['time'], origin='julian', unit='D')
                            if ens_name in ['ERAI']:          # Re-index lat dim
                                    ds_run = ds_run.reindex(lat=ds_run.lat[::-1])
                            
                # Subset for years (inside the run loop, so every member is used)
                ds_run = ds_run.sel(time=slice(year_start,year_end))
                ds_runs.append(ds_run)

            # Stack the members of this ensemble along a new 'name' dimension.
            # Members share one grid, so use the first member's coordinates
            # (avoids an outer join on tiny lat/lon differences).
            ds_runs = [d.drop_dims('name') if 'name' in d.dims else d for d in ds_runs]
            ds_this_ens = xr.concat(ds_runs, 'name', join='override', coords='minimal', compat='override')
            ds_this_ens = ds_this_ens.assign_coords(name = ("name", run_names))

        ds_ens[ens_name] = ds_this_ens 

# End of isinstance xr.dataset logic    
    # Year range check
        ystart_data = ds_run['time'].dt.year.min().item()
        yend_data = ds_run['time'].dt.year.max().item()
        
        if (ystart_data != int(year_start) or yend_data != int(year_end)): 
            print(fname,'   *Warning* ',ens_name,' ensemble data years do not match requested years',ystart_data,'-',yend_data)  
    

    
    print(fname,f'Duration: {time.time() - tstart}') ; print()
    
    return ds_ens
    

























#####################################################################
# Calculate 2D blocking idex based on Z500 
# Davini et al., (2012) http://doi.org/10.1029/2012GL052315
#####################################################################

# To do
# - Some kwargs so that there are some assumptions (like nhem) can overridden and args don't always have to be passed.



def block_z500_freq(block_meta,ens_ds,fout_dir,bseason,block_diag=None,cache_dir=None,recompute=False):
    """Blocking frequency for every dataset in block_meta.

    block_diag: '1D' (season, by longitude), '2D' (season, lat x lon) or
        '1DAC' (annual cycle, day of year x longitude; bseason is a label only).

    Results are cached: each dataset's result is a netCDF file named by index,
    dataset, number of members, years and season, in cache_dir (default fout_dir).
    An existing file is read instead of recomputed, unless it was made with a
    different BLOCKING_CALC_VERSION or recompute asks for it:
        recompute: False (reuse), True (recompute all), or a list of dataset names.
    Every result is also written (or copied) to fout_dir, the POD output.
    """

    fname = '-> block_z500_freq -> '
    print(fname,'Starting freq blocking calculation')

    ens_names = list(block_meta.index)

    for i in range(len(ens_names)):
        ens_name = ens_names[i]
        if 'name' not in ens_ds[ens_name]['Z500'].dims:
            ens_ds[ens_name]['Z500'] = ens_ds[ens_name]['Z500'].expand_dims(name=[ens_name])


    block_freq_ens = {}  # Dictionary for ensemble specific block freq.


    
    #### Loop if we need to write or just calculate.    

    ghgn_thresh = -5.
    ghgs_thresh = 0.
    
    # Latitude range to read in. Must cover every latitude used below: the 1D
    # index uses up to 78.85+3.75 = 82.6N and down to 41.25-3.75 = 37.5N; the 2D
    # index uses 15 deg north and south of its 35-75N band (20-90N). (Was 35-75N,
    # which clamped those latitudes to 35N/75N. The NCL POD read 20-85N.)
    lat_s_in = 20.
    lat_n_in = 90.

    # Central latitudes of the 2D index (Davini et al. 2012)
    lat_s_2d = 35.
    lat_n_2d = 75.

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
        
        # Reuse a cached result unless asked to recompute it
        cache_path = block_cache_file(ens_name, nens_mem, year_start, year_end, bseason, block_diag, cache_dir or fout_dir)
        out_path = block_cache_file(ens_name, nens_mem, year_start, year_end, bseason, block_diag, fout_dir)
        if wants_recompute(recompute, ens_name):
            print(fname, 'Recomputing (requested):', cache_path)
        else:
            block_freq = block_cache_read(cache_path, block_diag)

        if block_freq is None:   # not cached (or stale, or recompute requested): calculate
            ds_this_ens = ens_ds[ens_name]
        
            #  Grab data and variable        
            ens_z500 = ds_this_ens['Z500']   
    
            # Subset required latitude limits (latitude ascending, whatever the input order).
            ens_z500 = ens_z500.sortby('lat').sel(lat=slice(lat_s_in,lat_n_in))
    
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
               
                case '1D' | '1DAC':

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


                    # For each central latitude phi0 in the 35-75N band, the heights at
                    # phi0+15 and phi0-15 (nearest grid latitudes) give the north and
                    # south gradients; a point is blocked when GHGS > 0 and GHGN < -5.
                    z500_0 = ens_z500.sel(lat=slice(lat_s_2d, lat_n_2d))
                    lat0 = z500_0.lat.values
                    z500_n = ens_z500.sel(lat=lat0 + dlat_2d, method="nearest").assign_coords(lat=lat0)
                    z500_s = ens_z500.sel(lat=lat0 - dlat_2d, method="nearest").assign_coords(lat=lat0)
                    ghgn = (z500_n - z500_0) / dlat_2d
                    ghgs = (z500_0 - z500_s) / dlat_2d

                    # Boolean for saying whether a time, lat and lon point is blocked or not 
                    is_blocked =  xr.where((ghgs > ghgs_thresh) & (ghgn < ghgn_thresh),True,False)
                case _ :
                    raise ValueError(f'{fname} No such blocking diagnostic: {block_diag}')
            
            # Determine frequency
            if block_diag == '1DAC':
                # Annual cycle: daily climatology of the 1D blocked flag (all seasons), day 1-365
                block_freq = is_blocked.astype('float32').groupby('time.dayofyear').mean('time')
                block_freq = block_freq.sel(dayofyear=slice(1, 365))
            else:
                # Keep only the requested season (ANN = all days)
                if bseason != 'ANN':
                    in_season = (is_blocked['time.season'] == bseason).values
                    is_blocked = is_blocked.isel(time=in_season)
                block_days = is_blocked.sum(dim='time')
                block_freq = block_days / is_blocked.sizes['time']

            block_freq = block_freq.compute()   # once, here (writing and plotting both need it)
            block_cache_write(block_freq, cache_path, block_diag)

        # The POD output gets a copy of every result used
        if os.path.abspath(out_path) != os.path.abspath(cache_path):
            shutil.copy2(cache_path, out_path)


        bmin = 100.*(block_freq.min()) ; bmax = 100.*(block_freq.max())
        print(fname,'Min/max blocking frequency for ensemble ',ens_name,' = ',bmin.values,',',bmax.values,
              f'({time.time()-tstart:.0f} s)')

        block_freq_ens[ens_name] = block_freq

    return block_freq_ens






#################################################################################
#    Cache of blocking frequency results (one netCDF file per dataset and index)
#################################################################################

def wants_recompute(recompute, ens_name):
    """recompute: True/False, or a list of dataset names to recompute."""
    if isinstance(recompute, (list, tuple, set)):
        return ens_name in recompute
    return bool(recompute)


def parse_recompute(text):
    """MDTF_BLOCKING_RECOMPUTE setting -> False, True or a list of dataset names."""
    text = str(text).strip()
    if text.lower() in ('', 'false', 'no', '0'):
        return False
    if text.lower() in ('true', 'yes', '1', 'all'):
        return True
    return [s.strip() for s in text.split(',') if s.strip()]


def block_cache_file(ens_name, nens, year_start, year_end, bseason, block_diag, cache_dir):
    """Path of the blocking frequency file for one dataset (creates cache_dir)."""
    os.makedirs(cache_dir, exist_ok=True)
    name = f'block_{block_diag}_{ens_name}_nens.{nens}_{year_start}-{year_end}_{bseason}.nc'
    return os.path.join(cache_dir, name)


def block_cache_read(path, block_diag):
    """Cached result as a DataArray, or None if there is no file or it was made
    with another BLOCKING_CALC_VERSION."""
    fname = '--> block_cache_read -> '
    if not os.path.isfile(path):
        print(fname, 'Not cached, calculating:', path)
        return None
    with xr.open_dataset(path) as ds:
        version = ds.attrs.get('blocking_calc_version')
        if version is None or int(version) != BLOCKING_CALC_VERSION:
            print(fname, f'Cached file has calc version {version}, not {BLOCKING_CALC_VERSION}; recalculating:', path)
            return None
        print(fname, 'Reading cached result:', path)
        return ds['BLOCK_'+block_diag].load()


def block_cache_write(block_freq, path, block_diag):
    """Write one result, with the calc version, via a temporary file so a shared
    cache never holds a half-written file."""
    ds = block_freq.rename('BLOCK_'+block_diag).to_dataset()
    ds.attrs['blocking_calc_version'] = BLOCKING_CALC_VERSION
    tmp = f'{path}.tmp{os.getpid()}'
    ds.to_netcdf(tmp)
    os.replace(tmp, path)
    print('--> block_cache_write -> Wrote', path)
