'''
    BLOCKING UTILITY ROUTINES (blocking_neale_nb)

    ens_setup / find_ens_info - table (block_meta) of the obs and model ensembles to compare against
    dataset_get               - opens daily Z500 for every dataset in block_meta
    EnsembleData              - the same, but opens each dataset only when it is first needed
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





def ens_setup(ens_name,ens_mem_num,ystart,yend,raw_catalog=None):

# Construct and display Settings

    ens_info = find_ens_info(ens_name,ens_mem_num,ystart,yend,raw_catalog)  
    pprint.pprint(ens_info)
    

    return ens_info




#################################################################################
#    Raw data of the comparison datasets (NCAR GLADE only)
#################################################################################
#
# The POD normally reads no raw comparison data: their blocking frequencies are
# shipped as digested data in its obs data directory ($OBS_DATA). Raw daily Z500
# is only needed to make those files again, or for a choice that is not shipped
# (other years, members, seasons or datasets). It is then read through an
# ESM-intake catalog, set with MDTF_BLOCKING_RAW_CATALOG.
#
# This table is only used to build that catalog (make_raw_catalog; see the end of
# this file). files: path template, {run} = member run name (lens_simulations.py
# for the ensembles). tested: used with the current version of this POD.
#
RAW_DATA = {
    'ERA5':  dict(type='obs', tested=True,
                  files='/glade/work/rneale/data/ERA5/Z500.day.mean.nc'),
    'MERRA': dict(type='obs', tested=True,
                  files='/glade/work/rneale/data/MERRA/Z500.day.mean.nc'),
    'ERAI':  dict(type='obs', tested=False,
                  files='/glade/work/rneale/data/ERAI/Z500.day.mean.nc'),
    # MDTF v3 timeslice CESM run (1995-2014), public archive; a one-member model ensemble
    'timeslice3': dict(type='model', tested=True,
                  files='/glade/campaign/cgd/amp/bundy/mdtf/cesm_mdtfv3_timeslice_public/atm/day/cesm_mdtfv3_timeslice.Z500.day.nc'),
    'CESM2': dict(type='model', tested=True,
                  files='/glade/campaign/cgd/cesm/CESM2-LE/atm/proc/tseries/day_1/Z500/{run}.cam.h1.Z500.*.nc'),
    'CESM1': dict(type='model', tested=False,
                  files='/glade/campaign/cesm/collections/cesmLE/CESM-CAM5-BGC-LE/atm/proc/tseries/daily/Z500/{run}.cam.h1.Z500.*.nc'),
    'E3SMv1': dict(type='model', tested=False,
                  files='/glade/campaign/cgd/amp/rneale/e3sm/{run}/tseries/{run}_dmeans_ts_Z500.nc'),
    'E3SMv2': dict(type='model', tested=False,
                  files='/glade/campaign/cgd/ccr/E3SMv2/FV_regridded/{run}/atm/proc/tseries/day_1/{run}.eam.h1.Z500.*.nc'),
    'EAMv2': dict(type='model', tested=False,
                  files='/glade/campaign/cgd/ccr/E3SMv2/FV_regridded/{run}/atm/proc/tseries/day_1/{run}.eam.h1.Z500.*.nc'),
    # Files not found on GLADE (Nov 2026); left for reference
    'CAM6': dict(type='model', tested=False,
                  files='/glade/campaign/cesm/development/cvcwg/cvwg/f.e21.FHIST_FSSP370_BGC.f09_f09.ersstv5.goga/{run}/atm/proc/tseries/day_1/{run}.cam.h1.Z500.*.nc'),
}
ENSEMBLE_SETS = ['CESM1', 'CESM2', 'E3SMv1', 'E3SMv2', 'EAMv2', 'CAM6']   # members in lens_simulations.py


############################################
# Set ensemble/single/obs case information #
############################################

def find_ens_info(ens_names,mem_num,ystart,yend,raw_catalog=None):
    """Table (one row per dataset) of the comparison datasets: type, members, years,
    run names, and where raw data would come from (the raw-data catalog)."""

    import lens_simulations as sim_names
    importlib.reload(sim_names)

    fname = '-> find_ens_info -> '
    all_ens_info = {}

    for iens,ens_name in enumerate(ens_names):
        if ens_name not in RAW_DATA:
            raise ValueError(f'{fname} Unknown ensemble or obs name {ens_name!r} in MDTF_BLOCKING_ENSEMBLES; '
                             f'known: {", ".join(RAW_DATA)}')
        info = RAW_DATA[ens_name]
        if not info['tested']:
            print(fname, f'*Warning* {ens_name} has not been tested with the current version of this POD')
        if ens_name in ENSEMBLE_SETS:
            run_names = sim_names.get_ens_set_names(ens_name,mem_num[iens])
        else:
            run_names = [ens_name]
        all_ens_info[ens_name] = [info['type'],mem_num[iens],ystart[iens],yend[iens],run_names,raw_catalog]

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
            # Raw data, through the raw-data catalog (run_files holds its path)
            print(fname,'Opening ensemble files',ens_name,' - ',num_runs,' ensemble(s) from catalog',run_files)
            print(fname+ 'Requested year range : ',year_start,'-',year_end)

            # Chunk sizes
            chunk_sizes = {'time': 365, 'latitude': 360, 'longitude': 180}

            ds_runs = []
            for irun,run_name in enumerate(run_names):
                files = raw_catalog_files(run_files, ens_name, run_name, var_name, year_start, year_end)
                print(fname,' Opening member',irun,run_name,':',len(files),'file(s)')
                ds_run = xr.open_mfdataset(files,combine="by_coords" if len(files) > 1 else "nested",
                                           parallel=True,chunks=chunk_sizes)
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


class EnsembleData(dict):
    """Daily Z500 for the datasets in block_meta, opened (with dataset_get) only
    when a dataset is first used. Datasets whose blocking frequencies are all
    cached, or shipped in the POD's obs data, are never opened."""

    def __init__(self, block_meta, var_name, season, diag_hem):
        super().__init__()
        self.block_meta, self.args = block_meta, (var_name, season, diag_hem)

    def __missing__(self, ens_name):
        try:
            ds = dataset_get(self.block_meta.loc[[ens_name]], *self.args)[ens_name]
        except OSError as e:
            row = self.block_meta.loc[ens_name]
            raise FileNotFoundError(
                f"No digested blocking frequencies for {ens_name} ({row['Ensemble Size']} members, "
                f"{str(row['Start Year'])[:4]}-{str(row['End Year'])[:4]}) in the POD's obs data "
                f"($OBS_DATA), and its raw daily Z500 could not be read ({e}). Use the years, members "
                f"and seasons shipped in $OBS_DATA, or run where the raw data are available.") from e
        self[ens_name] = ds
        return ds
    

























#####################################################################
# Calculate 2D blocking idex based on Z500 
# Davini et al., (2012) http://doi.org/10.1029/2012GL052315
#####################################################################

# To do
# - Some kwargs so that there are some assumptions (like nhem) can overridden and args don't always have to be passed.



def block_z500_freq(block_meta,ens_ds,fout_dir,bseason,block_diag=None,cache_dir=None,recompute=False,ref_dir=None):
    """Blocking frequency for every dataset in block_meta.

    block_diag: '1D' (season, by longitude), '2D' (season, lat x lon) or
        '1DAC' (annual cycle, day of year x longitude; bseason is a label only).

    Results are cached: each dataset's result is a netCDF file named by index,
    dataset, number of members, years and season, in cache_dir (default fout_dir).
    An existing file is read instead of recomputed, unless it was made with a
    different BLOCKING_CALC_VERSION or recompute asks for it:
        recompute: False (reuse), True (recompute all), or a list of dataset names.
    ref_dir: read-only directory of precomputed results shipped with the POD
        (its obs data directory, $OBS_DATA), looked in after cache_dir. A dataset
        found there is never opened, so its raw data need not be available.
    Every result is also written (or copied) to fout_dir, the POD output.
    ens_ds is only indexed for datasets that are computed (see EnsembleData).
    """

    fname = '-> block_z500_freq -> '
    print(fname,'Starting freq blocking calculation')

    ens_names = list(block_meta.index)


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
            if block_freq is None and ref_dir:
                ref_path = block_cache_file(ens_name, nens_mem, year_start, year_end, bseason, block_diag, ref_dir, create=False)
                block_freq = block_cache_read(ref_path, block_diag, quiet=True)
                if block_freq is not None:
                    cache_path = ref_path   # copied to the POD output below

        if block_freq is None:   # not cached (or stale, or recompute requested): calculate
            ds_this_ens = ens_ds[ens_name]   # opens the data now if ens_ds is an EnsembleData
            # Keep only the requested years (the case datasets are passed in whole)
            years = ds_this_ens['time'].dt.year
            ds_this_ens = ds_this_ens.isel(time=((years >= int(str(year_start)[:4])) &
                                                 (years <= int(str(year_end)[:4]))).values)
            if ds_this_ens.sizes['time'] == 0:
                raise ValueError(f"{ens_name}: no data for {year_start}-{year_end}")
            print(fname, f"{ens_name}: {ds_this_ens.sizes['time']} time steps, "
                  f"{str(ds_this_ens['time'].values[0])[:10]} to {str(ds_this_ens['time'].values[-1])[:10]}")
            if 'name' not in ds_this_ens['Z500'].dims:
                ds_this_ens['Z500'] = ds_this_ens['Z500'].expand_dims(name=[ens_name])
        
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


def block_cache_file(ens_name, nens, year_start, year_end, bseason, block_diag, cache_dir, create=True):
    """Path of the blocking frequency file for one dataset (creates cache_dir).
    Years are written as 4 digits (YYYY or a YYYYMMDD... date both give YYYY)."""
    if create:
        os.makedirs(cache_dir, exist_ok=True)
    name = f'block_{block_diag}_{ens_name}_nens.{nens}_{str(year_start)[:4]}-{str(year_end)[:4]}_{bseason}.nc'
    return os.path.join(cache_dir, name)


def block_cache_read(path, block_diag, quiet=False):
    """Cached result as a DataArray, or None if there is no file or it was made
    with another BLOCKING_CALC_VERSION."""
    fname = '--> block_cache_read -> '
    if not os.path.isfile(path):
        if not quiet:
            print(fname, 'Not cached:', path)
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


#################################################################################
#    Raw-data catalog (ESM-intake) for the comparison datasets
#################################################################################

RAW_CATALOG_COLUMNS = ['activity_id', 'institution_id', 'source_id', 'experiment_id', 'member_id',
                       'realm', 'variable_id', 'standard_name', 'units', 'frequency',
                       'time_range', 'path']


def raw_catalog_files(catalog, ens_name, run_name, var_name, year_start, year_end):
    """Files of one member (run_name) of a comparison dataset (ens_name), from the
    raw-data catalog, limited to those overlapping year_start-year_end."""
    import intake
    if not catalog:
        raise OSError(f'{ens_name}: raw data needed but MDTF_BLOCKING_RAW_CATALOG is not set')
    if not os.path.isfile(catalog):
        raise OSError(f'{ens_name}: raw-data catalog not found: {catalog}')
    cat = intake.open_esm_datastore(catalog)
    df = cat.search(source_id=ens_name, member_id=run_name, variable_id=var_name).df
    if df.empty:
        raise OSError(f'{ens_name}: no {var_name} files for member {run_name} in {catalog}')

    def overlaps(tr):
        tr = str(tr) if isinstance(tr, str) else ''
        if '-' not in tr:
            return True          # unknown range: keep the file
        a, b = tr.split('-', 1)
        return a[:4] <= str(year_end)[:4] and b[:4] >= str(year_start)[:4]

    files = sorted(df.loc[df['time_range'].apply(overlaps), 'path'])
    if not files:
        raise OSError(f'{ens_name}: no {var_name} files for {run_name} cover {year_start}-{year_end} in {catalog}')
    return files


def _file_time_range(path):
    """'YYYYMMDD-YYYYMMDD' from the file name, else from the file, else ''."""
    import re
    m = re.search(r'\.(\d{8})-(\d{8})\.nc$', path)
    if m:
        return f'{m.group(1)}-{m.group(2)}'
    try:
        with xr.open_dataset(path, decode_times=xr.coders.CFDatetimeCoder(use_cftime=True)) as ds:
            t = ds['time']
            return f'{t[0].dt.strftime("%Y%m%d").item()}-{t[-1].dt.strftime("%Y%m%d").item()}'
    except Exception:
        return ''   # e.g. MERRA/ERAI time in Julian days


def make_raw_catalog(json_path, names=None):
    """Write the ESM-intake catalog (json_path, plus a .csv beside it) of the raw daily
    Z500 of the comparison datasets in RAW_DATA (or only `names`). Lists every file that
    exists; datasets with no files are reported and left out. Run on NCAR GLADE:
        python blocking_utils.py --make-raw-catalog <catalog.json> [names...]
    """
    import glob, json, datetime
    import lens_simulations as sim_names
    rows = []
    for ens_name in (names or RAW_DATA):
        info = RAW_DATA[ens_name]
        runs = sim_names.get_ens_set_names(ens_name, 10000) if ens_name in ENSEMBLE_SETS else [ens_name]
        n0 = len(rows)
        for run in runs:
            for path in sorted(glob.glob(info['files'].format(run=run))):
                rows.append({'activity_id': 'blocking_neale_nb', 'institution_id': '',
                             'source_id': ens_name, 'experiment_id': info['type'], 'member_id': run,
                             'realm': 'atmos', 'variable_id': 'Z500', 'standard_name': 'geopotential_height',
                             'units': 'm', 'frequency': 'day', 'time_range': _file_time_range(path),
                             'path': path})
        print(f'{ens_name}: {len(rows) - n0} files' + ('' if len(rows) > n0 else '  (none found, left out)'))
    csv_path = os.path.splitext(json_path)[0] + '.csv'
    pd.DataFrame(rows, columns=RAW_CATALOG_COLUMNS).to_csv(csv_path, index=False)
    header = {
        'esmcat_version': '0.0.1',
        'id': os.path.splitext(os.path.basename(json_path))[0],
        'description': 'Raw daily Z500 of the blocking_neale_nb comparison datasets (made by '
                       'blocking_utils.make_raw_catalog)',
        'title': 'blocking_neale_nb raw comparison data',
        'last_updated': datetime.date.today().isoformat(),
        'catalog_file': os.path.basename(csv_path),
        'attributes': [{'column_name': c, 'vocabulary': ''} for c in RAW_CATALOG_COLUMNS[:-1]],
        'assets': {'column_name': 'path', 'format': 'netcdf'},
        'aggregation_control': {'variable_column_name': 'variable_id',
                                'groupby_attrs': ['source_id', 'member_id'],
                                'aggregations': []},
    }
    with open(json_path, 'w') as f:
        json.dump(header, f, indent=2)
    print('Wrote', json_path, 'and', csv_path, f'({len(rows)} files)')
    return json_path


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--make-raw-catalog':
        make_raw_catalog(sys.argv[2], sys.argv[3:] or None)
    else:
        print('usage: python blocking_utils.py --make-raw-catalog <catalog.json> [names...]')
