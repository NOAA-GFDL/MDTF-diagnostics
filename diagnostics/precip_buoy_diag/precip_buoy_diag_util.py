'''
This file is part of the precip_buoy_diag module of the MDTF code
package (see mdtf/MDTF-diagnostics/LICENSE.txt).


DESCRIPTION: Provides functions used by precip_buoy_diag_main.py

REQUIRED MODULES:

AUTHORS: Fiaz Ahmed

'''

import numpy as np
import numba
import glob
import os
from numba import jit, njit
import scipy.io
from scipy.interpolate import NearestNDInterpolator
from netCDF4 import Dataset
from vert_cython import find_closest_index_2D, compute_layer_thetae
import matplotlib
import matplotlib.pyplot as mp
from mpl_toolkits.mplot3d import Axes3D
import networkx
import datetime as dt
from sys import exit, stdout
import seaborn as sns
import xarray as xr
import matplotlib.rcsetup as rcsetup


# ======================================================================
# precipbuoy_binThetae
#  takes arguments and bins by subsat+ cape & bint

# @jit(nopython=True) 
# def precipbuoy_binThetae(lon_idx, REGION, PRECIP_THRESHOLD, NUMBER_CAPE_BIN, NUMBER_SUBSAT_BIN, 
# NUMBER_BINT_BIN, CAPE, SUBSAT, BINT, RAIN, p0, p1, p2, pe, q0, q1, q2, qe):
#  
#  
#     for lat_idx in np.arange(SUBSAT.shape[1]):
#         subsat_idx=SUBSAT[:,lat_idx,lon_idx]
#         cape_idx=CAPE[:,lat_idx,lon_idx]
#         bint_idx=BINT[:,lat_idx,lon_idx]
#         rain=RAIN[:,lat_idx,lon_idx]
#         reg=REGION[lon_idx,lat_idx]
#         
#         if reg>0:
#             for time_idx in np.arange(SUBSAT.shape[0]):
#                 if (cape_idx[time_idx]<NUMBER_CAPE_BIN and cape_idx[time_idx]>=0 
#                 and subsat_idx[time_idx]<NUMBER_SUBSAT_BIN and subsat_idx[time_idx]>=0
#                 and np.isfinite(rain[time_idx])):
#                     p0[subsat_idx[time_idx],cape_idx[time_idx]]+=1
#                     p1[subsat_idx[time_idx],cape_idx[time_idx]]+=rain[time_idx]
#                     p2[subsat_idx[time_idx],cape_idx[time_idx]]+=rain[time_idx]**2
#                     
#                     if (rain[time_idx]>PRECIP_THRESHOLD):
#                         pe[subsat_idx[time_idx],cape_idx[time_idx]]+=1
# 
#                     
#                 if (bint_idx[time_idx]<NUMBER_BINT_BIN and bint_idx[time_idx]>=0
#                 and np.isfinite(rain[time_idx])):
#                     q0[bint_idx[time_idx]]+=1
#                     q1[bint_idx[time_idx]]+=rain[time_idx]
#                     q2[bint_idx[time_idx]]+=rain[time_idx]**2
#                     if (rain[time_idx]>PRECIP_THRESHOLD):
#                         qe[bint_idx[time_idx]]+=1
#                         

class precipbuoy:

    def __init__(self, temp_file):
        ### read in the primary input variable paths
        
        ### temporary directory where the preprocessed output will be stored
        self.temp_file=temp_file

        ### flag to check if a pre-processed file exists
        if glob.glob(temp_file):
            self.preprocessed=True
        else:
            self.preprocessed=False  
            
    # #  takes in 3D tropospheric temperature and specific humidity fields on model levels, 
    # # and calculates: thetae_LFT, thetae_sat_LFT & thetae_BL.
    # # As in the convective transition statistics POD,
    ##  calculations will be broken up into chunks of time-period corresponding
    ##  to time_idx_delta with a default of 1000 time steps
# 
    def preprocess(self):
        ### LOAD temp. and q datasets ###
        ta_ds=xr.open_mfdataset(os.environ['ta_file'])
        hus_ds=xr.open_mfdataset(os.environ['hus_file'])
                                
        ### rename dimensions to internal names for ease of use
        LAT_VAR_NEW='lat'
        LON_VAR_NEW='lon'
        TIME_VAR_NEW='time'
        LEV_VAR_NEW='lev'
        
        ta_ds=ta_ds.rename({os.environ['time_coord']:TIME_VAR_NEW,os.environ['lat_coord']:LAT_VAR_NEW,os.environ['lon_coord']:LON_VAR_NEW,
        os.environ['lev_coord']:LEV_VAR_NEW})
        hus_ds=hus_ds.rename({os.environ['time_coord']:TIME_VAR_NEW,os.environ['lat_coord']:LAT_VAR_NEW,os.environ['lon_coord']:LON_VAR_NEW,
        os.environ['lev_coord']:LEV_VAR_NEW})
        
        ### set time and latitudinal slices for extraction ###
        
        strt_dt=dt.datetime.strptime(str(os.environ['FIRSTYR'])+'010100',"%Y%m%d%H")
        end_dt=dt.datetime.strptime(str(os.environ['LASTYR'])+'123123',"%Y%m%d%H")
        time_slice=slice(strt_dt, end_dt)  ## set time slice      
         
        lat_slice=slice(-20,20) ## set latitudinal slice

        ### Ensure that start and end dates span more than 1 day.
        if (time_slice.stop-time_slice.start).days<1:
            exit('Please set time range greater than 1 day. Exiting now')

        ### specify datetime format
        DATE_FORMAT='%Y%m%d'

        ### Ensure that times are in datetime format ###
        self._fix_datetime(ta_ds, DATE_FORMAT)
        self._fix_datetime(hus_ds, DATE_FORMAT)

        print("....SLICING DATA")
        ### select subset ###
        ta_ds_subset=ta_ds.sel(time=time_slice,lat=lat_slice)
        hus_ds_subset=hus_ds.sel(time=time_slice,lat=lat_slice)

        ### check to ensure that time subsets are non-zero ###
        assert ta_ds_subset.time.size>0 , 'specified time range is zero!!'
            
        ### Load arrays into memory ###
    
        lat=ta_ds_subset['lat']
        lon=ta_ds_subset['lon']
        ta=ta_ds_subset[os.environ['ta_var']]
        hus=hus_ds_subset[os.environ['qa_var']]
        lev=ta_ds_subset['lev']
        
        
        ### Is surface pressure is available, extract it
        ### if not set ps_ds to None
        if os.environ['ps_file']:
            ps_ds=xr.open_mfdataset(os.environ['ps_file'])
            ps_ds=ps_ds.rename({os.environ['time_coord']:TIME_VAR_NEW,os.environ['lat_coord']:LAT_VAR_NEW,os.environ['lon_coord']:LON_VAR_NEW})
            self._fix_datetime(ps_ds, DATE_FORMAT)
            ps_ds_subset=ps_ds.sel(time=time_slice,lat=lat_slice)

        else:
            ps_ds_subset=None

        ### extract pressure levels 
        pres,ps=self._return_pres_levels(lev,ta,ps_ds_subset)  
    
        assert(ta['time'].size==hus['time'].size)

        ### setting parameters for buoyancy calculations
    
        ## setting the pressure level at the top of a nominal boundary layer
        pbl_top=ps-100e2 ## The BL is 100 mb thick ##
        pbl_top=np.float_(pbl_top.values.flatten()) ### overwriting pbl top xarray with numpy array
        
        ## setting the pressure level at the top of a nominal lower free troposphere (LFT) 
        low_top=np.zeros_like(ps)
        low_top[:]=500e2  # the LFT top is fixed at 500 mb
        low_top=np.float_(low_top.flatten())

        ### LOAD data arrays into memory###
        print('...LOADING ARRAYS INTO MEMORY')
        ta=ta.transpose('lev','time','lat','lon')
        hus=hus.transpose('lev','time','lat','lon')
        pres=pres.transpose('lev','time','lat','lon')
        ps=ps.transpose('time','lat','lon')

        pres=pres.values   
        ta=np.asarray(ta.values,dtype='float')
        hus=np.asarray(hus.values,dtype='float')

        print('...DONE LOADING')

        ta_ds.close()
        hus_ds.close()
        
        ### Check if pressure array is descending 
        ### since this is an implicit assumption

        if (np.all(np.diff(pres,axis=0)<0)):
            print('     pressure levels strictly decreasing')
        elif (np.all(np.diff(pres,axis=0)>0)):
            print('     pressure levels strictly increasing')
            print('     reversing the pressure dimension')
            pres=pres[::-1,:,:,:]
            ta=ta[::-1,:,:,:]
            hus=hus[::-1,:,:,:]
        else:
            exit('......Check pressure level ordering. Exiting now..')

        ### Reshape arrays to 2D ###
        
        print('...COMPUTING THETAE VARIABLES')

        lev=pres.reshape(*lev.shape[:1],-1)
        ta_flat=ta.reshape(*ta.shape[:1],-1)
        hus_flat=hus.reshape(*hus.shape[:1],-1)

        pbl_ind=np.zeros(pbl_top.size,dtype=np.int64)
        low_ind=np.zeros(low_top.size,dtype=np.int64)

        ### Find the closest pressure level to pbl_top and low_top
        ### using a cython routine 'find_closest_index_2D'
        find_closest_index_2D(pbl_top,lev,pbl_ind)
        find_closest_index_2D(low_top,lev,low_ind)

        ### Declare empty arrays to hold thetae variables
        thetae_bl=np.zeros_like(pbl_top)
        thetae_lt=np.zeros_like(pbl_top)
        thetae_sat_lt=np.zeros_like(pbl_top)

        ### the fractional weighting of the boundary layer in 
        ### buoyancy computation
        wb=np.zeros_like(pbl_top)

        ### Use trapezoidal rule for approximating the vertical integral ###
        ### vert. integ.=(b-a)*(f(a)+f(b))/2
        ### using a cython routine 'compute_layer_thetae'
        compute_layer_thetae(ta_flat, hus_flat, lev, pbl_ind, low_ind, thetae_bl, thetae_lt, thetae_sat_lt, wb)

        ### if thetae_bl is zero set it to nan
        ### masking is an option.
        thetae_bl[thetae_bl==0]=np.nan
        thetae_lt[thetae_lt==0]=np.nan
        thetae_sat_lt[thetae_sat_lt==0]=np.nan
        
        ### Unflatten the space dimension to lat,lon ###
        thetae_bl=thetae_bl.reshape(ps.shape)
        thetae_lt=thetae_lt.reshape(ps.shape)
        thetae_sat_lt=thetae_sat_lt.reshape(ps.shape)

        print('.....'+os.environ['ta_file']+" & "+os.environ['hus_file']+" pre-processed!")

        ### SAVING INTERMEDIATE FILE TO DISK ###

        data_set=xr.Dataset(data_vars={"thetae_bl":(ta_ds_subset[os.environ['ta_var']].isel(lev=0).dims, thetae_bl),
                              "thetae_lt":(ta_ds_subset[os.environ['ta_var']].isel(lev=0).dims, thetae_lt),
                              "thetae_sat_lt":(ta_ds_subset[os.environ['ta_var']].isel(lev=0).dims, thetae_sat_lt),
                              "ps":(ta_ds_subset[os.environ['ta_var']].isel(lev=0).dims, ps)},
                   coords=ta_ds_subset[os.environ['ta_var']].isel(lev=0).drop('lev').coords)
        data_set.thetae_bl.attrs['long_name']="theta_e averaged in the BL (100 hPa above surface)"
        data_set.thetae_lt.attrs['long_name']="theta_e averaged in the LFT (100 hPa above surface to 500 hPa)"
        data_set.thetae_sat_lt.attrs['long_name']="theta_e_sat averaged in the LFT (100 hPa above surface to 500 hPa)"
        data_set.ps.attrs['long_name']="surface pressure"

        data_set.thetae_bl.attrs['units']="K"
        data_set.thetae_lt.attrs['units']="K"
        data_set.thetae_sat_lt.attrs['units']="K"
        data_set.ps.attrs['units']='Pa'

        data_set.attrs['source']="Precipiation Buoyancy Diagnostics \
        - as part of the NOAA Model Diagnostic Task Force (MDTF)"

        data_set.to_netcdf(os.environ["temp_file"],mode='w')
        print('...'+os.environ["temp_file"]+" saved!")



        

#     def preprocess(, ta_netcdf_filename, TA_VAR, hus_netcdf_filename, HUS_VAR,\
#                             LEV_VAR, PS_VAR, A_VAR, B_VAR, VERT_TYPE, MODEL_NAME, p_lev_mid, time_idx_delta,\
#                             START_DATE, END_DATE, DATE_FORMAT,\
#                             SAVE_THETAE,PREPROCESSING_OUTPUT_DIR, THETAE_OUT,\
#                             THETAE_LT_VAR,THETAE_SAT_LT_VAR,THETAE_BL_VAR,\
#                             TIME_VAR,LAT_VAR,LON_VAR):
# 

#         ### select subset ###
#         ta_ds_subset=ta_ds.sel(time=time_slice,lat=lat_slice)
#         hus_ds_subset=hus_ds.sel(time=time_slice,lat=lat_slice)
# 
#     
#         ### if the dataset falls within specified time range: ###
#         if(ta_ds_subset.time.size)>0:
#     
#             print("     pre-processing "+ta_netcdf_filename)
#  
#             print('LOADING ARRAYS')
#             ### Load arrays into memory ###
#         
#             lat=ta_ds_subset['lat']
#             lon=ta_ds_subset['lon']
#             ta=ta_ds_subset[TA_VAR]
#             hus=hus_ds_subset[HUS_VAR]
# 
#         #     time_arr=ta_ds_subset.[TIME_VAR]
#             lev=ta_ds_subset['lev']
#         
#             ### Check if pressure or sigma co-ordinates ###
#         
#             if VERT_TYPE=='pres':
# 
#                 pres=ta_ds_subset['lev']
#             
#                 ### Convert units ###
#                 if(pres.units=='hPa'):
#                     pres=pres*100
#                 ### Convert data type
#                 pres=pres.astype('float')
#             
#                 pres,dummy=xr.broadcast(pres,ta_ds_subset.isel(lev=0,drop=True))
# 
#             
#                 try:
#                     ps=ta_ds_subset[PS_VAR]
#                     if(ps.units=='hPa'):
#                         ps=ps*100
#                 except:        
#                     ps=pres.sel(lev=lev.max().values)
# 
#         
#             elif VERT_TYPE=='sigma':
#                 a=ta_ds_subset[A_VAR]
#                 b=ta_ds_subset[B_VAR] ## comment this if using F-GOALS
#                 ps=ta_ds_subset[PS_VAR]
# 
#             ### for IPSL SSP585, a and b have one extra dimension ###
#     #         a=a[:-1]
#     #         b=b[:-1]
# 
#             ### for CNRM-CM6-1-HR tackle with changed co-ordinate names###
#     #                         
#     #         a=a.rename({'ap':LEV_VAR_NEW})
#     #         a=a.assign_coords({LEV_VAR_NEW:lev})
#     #         
#     #         b=b.rename({'b':LEV_VAR_NEW})
#     #         b=b.assign_coords({LEV_VAR_NEW:lev})
#             
#             
#             ### Create pressure data ###
# 
#                 pres=b*ps+a     ### Comment for F-GOALS
#         #         pres=a+lev*(ps-a) ### Uncomment for F-GOALS
#                 ### Define the layers for averaging ###    
# 
#  
#             else:
#                 exit('     Please select either "pres" or "sigma" for vertical co-ordinate type. Exiting now')
# 
#         
#             assert(ta_ds_subset['time'].size==hus_ds_subset['time'].size)
#             
# 
#             pbl_top=ps-100e2 ## The BL is 100 mb thick ##
#             pbl_top=np.float_(pbl_top.values.flatten()) ### overwriting pbl top xarray with numpy array
#             low_top=np.zeros_like(ps)
#             low_top[:]=500e2  # the LFT top is fixed at 500 mb
# 
#             low_top=np.float_(low_top.flatten())
#         
# 
#             ### LOAD data arrays into memory###
#             print('LOADING VALUES')
#             ta=ta.transpose('lev','time','lat','lon')
#             hus=hus.transpose('lev','time','lat','lon')
#             pres=pres.transpose('lev','time','lat','lon')
#             ps=ps.transpose('time','lat','lon')
# 
#             pres=pres.values   
#             ta=np.asarray(ta.values,dtype='float')
#             hus=np.asarray(hus.values,dtype='float')
# 
# 
#             ### Snippet to find the closet pressure level to pbl_top and
#             ### the freezing level.
#     
#             ### Reshape arrays to 2D for more efficient search ###
#     
#             ### Check if pressure array is descending ###
#             ### since this is an implicit assumption
# 
#             if (np.all(np.diff(pres,axis=0)<0)):
#                 print('     pressure levels strictly decreasing')
#             elif (np.all(np.diff(pres,axis=0)>0)):
#                 print('     pressure levels strictly increasing')
#                 print('     reversing the pressure dimension')
#                 pres=pres[::-1,:,:,:]
#                 ta=ta[::-1,:,:,:]
#                 hus=hus[::-1,:,:,:]
#             else:
#                 exit('     Check pressure level ordering. Exiting now..')
#             
#             lev=pres.reshape(*lev.shape[:1],-1)
#             ta_flat=ta.reshape(*ta.shape[:1],-1)
#             hus_flat=hus.reshape(*hus.shape[:1],-1)
# 
#             pbl_ind=np.zeros(pbl_top.size,dtype=np.int64)
#             low_ind=np.zeros(low_top.size,dtype=np.int64)
# 
#             find_closest_index_2D(pbl_top,lev,pbl_ind)
#             find_closest_index_2D(low_top,lev,low_ind)
# 
#             stdout.flush()
#         
#             thetae_bl=np.zeros_like(pbl_top)
#             thetae_lt=np.zeros_like(pbl_top)
#             thetae_sat_lt=np.zeros_like(pbl_top)
#             wb=np.zeros_like(pbl_top)
# 
#             ### Use trapezoidal rule for approximating the vertical integral ###
#             ### vert. integ.=(b-a)*(f(a)+f(b))/2
#             compute_layer_thetae(ta_flat, hus_flat, lev, pbl_ind, low_ind, thetae_bl, thetae_lt, thetae_sat_lt, wb)
# 
#             thetae_bl[thetae_bl==0]=np.nan
#             thetae_lt[thetae_lt==0]=np.nan
#             thetae_sat_lt[thetae_sat_lt==0]=np.nan
#     
#             ### Reshape all arrays ###
#             thetae_bl=thetae_bl.reshape(ps.shape)
#             thetae_lt=thetae_lt.reshape(ps.shape)
#             thetae_sat_lt=thetae_sat_lt.reshape(ps.shape)
#     
#             print('      '+ta_netcdf_filename+" & "+hus_netcdf_filename+" pre-processed!")
# 
#         #     Save Pre-Processed tave & qsat_int Fields
#             if SAVE_THETAE==1:
#         #         Create PREPROCESSING_OUTPUT_DIR
#                 os.system("mkdir -p "+PREPROCESSING_OUTPUT_DIR)
#                 ## Create output file name
#                 thetae_output_filename=PREPROCESSING_OUTPUT_DIR+ta_netcdf_filename.split('/')[-1].replace(TA_VAR,THETAE_OUT)
# 
#                 data_set=xr.Dataset(data_vars={"thetae_bl":(ta_ds_subset[TA_VAR].isel(lev=0).dims, thetae_bl),
#                                       "thetae_lt":(ta_ds_subset[TA_VAR].isel(lev=0).dims, thetae_lt),
#                                       "thetae_sat_lt":(ta_ds_subset[TA_VAR].isel(lev=0).dims, thetae_sat_lt),
#                                       "ps":(ta_ds_subset[TA_VAR].isel(lev=0).dims, ps)},
#                            coords=ta_ds_subset[TA_VAR].isel(lev=0).drop('lev').coords)
#                 data_set.thetae_bl.attrs['long_name']="theta_e averaged in the BL (100 hPa above surface)"
#                 data_set.thetae_lt.attrs['long_name']="theta_e averaged in the LFT (100 hPa above surface to 500 hPa)"
#                 data_set.thetae_sat_lt.attrs['long_name']="theta_e_sat averaged in the LFT (100 hPa above surface to 500 hPa)"
#                 data_set.ps.attrs['long_name']="surface pressure"
# 
#                 data_set.thetae_bl.attrs['units']="K"
#                 data_set.thetae_lt.attrs['units']="K"
#                 data_set.thetae_sat_lt.attrs['units']="K"
#                 data_set.ps.attrs['units']='Pa'
#         
#                 data_set.attrs['source']="Convective Onset Statistics Diagnostic Package \
#                 - as part of the NOAA Model Diagnostic Task Force (MDTF) effort"
# 
#                 data_set.to_netcdf(thetae_output_filename,mode='w')
#                 print('      '+thetae_output_filename+" saved!")
# 
# 
# 

    ### function to fix datetime formats 
    def _fix_datetime(self, ds,date_format=None):
        try:      
            if ds.indexes['time'].dtype=='float64' or ds.indexes['time'].dtype=='int64':
                ds['time']=[dt.datetime.strptime(str(int(i.values)),date_format) for i in ds.time]
            else:
                datetimeindex = ds.indexes['time'].to_datetimeindex()
                ds['time'] = datetimeindex
        except:
            pass
    

    def _return_pres_levels(self, lev, da, ps_ds):
        
        '''
        Function to set pressure levels and surface pressure
        depending on whether incoming levels are on pressure or sigma co-ordinates.     
        '''
        
    ### Check if pressure or sigma co-ordinates ###

        if os.environ['VERT_TYPE']=='pres':

            pres=lev
            ### Check if units are in hPa (or mb)
            ### Convert units to Pa if required ###
            if(str(pres.units).lower() in [i.lower() for i in ['hPa','mb']]):
                pres=pres*100
                
            ### Convert data type
            pres=pres.astype('float')
            
            
            ## broadcast pressure to a 4D array to mimic sigma levels
            ## this step is computationally inefficient, but helps retain 
            ## portability between pressure and sigma level handling
            
            pres,dummy=xr.broadcast(pres,da.isel(lev=0,drop=True))             


            ### Read surface pressure values if available          
            if ps_ds:
                ps=ps_ds[os.environ['ps_var']]
                if(ps.units=='hPa'):
                    ps=ps*100
            ### if unavailable, set surface pressure to maximum pressure level
            else:        
                ps=pres.sel(lev=lev.max().values)

        
        elif os.environ['VERT_TYPE']=='sigma':
            ### currently written so that coefficients a and b are 
            ### stored in the surface pressure file
            a=ps_ds[os.environ['a_var']]
            b=ps_ds[os.environ['b_var']] 
            ps=ps_ds[os.environ['ps_var']]
            
            ### Create pressure data ###
            pres=b*ps+a     

        return pres, ps
 
            




# def precipbuoy_calcqT_ratio(Z,counts,cape_bin_center,subsat_bin_center):
#     '''
#     Function that takes the precipitation surface and produces an estimate of the 
#     temperature-to-moisture sensitivity. This metric measures the rate of precipitation
#     increase along the CAPE direction and compares to the corresponding increase along the
#     SUBSAT direction.
#     '''
# 
#     ### Find the location of max counts. This is generally near the precipitation
#     ### onset.
#     subsat_max_pop_ind,cape_max_pop_ind=np.where(counts==np.nanmax(counts))
# 
#     ### Create three copies of the 2D precipitation surface array.
#     ### Divide the precipitation surface into three portions: the CAPE, SUBSAT and
#     ### overlapping portions 
#     ### The CAPE portion is for SUBSAT values beyond the SUBSAT index of max counts
#     ### The SUBSAT portion is for CAPE values beyond the CAPE index of max counts
#     ### The overlapping portion contains the overlapping components of the CAPE and SUBSAT arrays.
#     
#     Z_subsat=np.copy(Z)
#     Z_subsat[:]=np.nan
#     Z_subsat[subsat_max_pop_ind[0]-1:,cape_max_pop_ind[0]:]=Z[subsat_max_pop_ind[0]-1:,cape_max_pop_ind[0]:]
# 
#     Z_cape=np.copy(Z)
#     Z_cape[:]=np.nan
#     Z_cape[:subsat_max_pop_ind[0],:cape_max_pop_ind[0]+1]=Z[:subsat_max_pop_ind[0],:cape_max_pop_ind[0]+1]
# 
#     Z_overlap=np.copy(Z)
#     Z_overlap[:]=np.nan
#     Z_overlap[:subsat_max_pop_ind[0],cape_max_pop_ind[0]:]=Z[:subsat_max_pop_ind[0],cape_max_pop_ind[0]:]
# 
# 
#     ### Get the average cape and subsat values for each of the three regions
#     fin0=(np.where(np.isfinite(Z_overlap)))
#     fin1=(np.where(np.isfinite(Z_cape)))
#     fin2=(np.where(np.isfinite(Z_subsat)))
# 
#     subsat_y0=subsat_bin_center[fin0[0]]
#     cape_x0=cape_bin_center[fin0[1]]
#     
#     subsat_y1=subsat_bin_center[fin1[0]]
#     cape_x1=cape_bin_center[fin1[1]]
# 
#     subsat_y2=subsat_bin_center[fin2[0]]
#     cape_x2=cape_bin_center[fin2[1]]
# 
#     
#     ### Get a distance measure between the overlapping region to the cape and subsat regions
# 
#     dcape=abs(cape_x0.mean()-cape_x1.mean())
#     dsubsat=abs(subsat_y0.mean()-subsat_y2.mean())
#         
#     ### Get a distance measure between the overlapping region to the cape and subsat regions
#     ### Compute the average precipitation within the CAPE and SUBSAT regions. 
# 
#     area_cape=np.nanmean(Z_cape)
#     area_subsat=np.nanmean(Z_subsat)
#     area_overlap=np.nanmean(Z_overlap)
#     darea_cape=abs(area_overlap-area_cape)
#     darea_subsat=abs(area_overlap-area_subsat)
#     ratio=darea_cape*dsubsat/(dcape*darea_subsat)
#     
#     return ratio
# 
# 
# def nearest(items, pivot,greater=True):
#     '''
#     Simple function adapted from SO. 
#     Returns the closest date to given date (pivot).
#     Keyword greater returns closest date greater/equal tp pivot,
#     setting it to False returns closest date less/equal than pivot
#     '''
#     if greater:
#         return min(items, key=lambda x: x-pivot if x>=pivot else x-dt.datetime(1,1,1)) 
#     else:
#         return min(items, key=lambda x: pivot-x if x<=pivot else pivot-dt.datetime(1,1,1))    
# 
# 
# ### Compute the saturation vapor pressure for a given temperature ###
# 
# def es_calc(temp):
# 
#     #This function gives sat. vap. pressure (in Pa) for a temp value (in K)
#     
# 	#get some constants:
# 	tmelt  = 273.15
# 
# 	#convert inputs to proper units, forms
# 	tempc = temp - tmelt # in C
# 	tempcorig = tempc
# 	c=np.array((0.6105851e+03,0.4440316e+02,0.1430341e+01,0.2641412e-01,0.2995057e-03,0.2031998e-05,0.6936113e-08,0.2564861e-11,-.3704404e-13))
# 
# 	#calc. es in hPa (!!!)
# 	#es = 6.112*EXP(17.67*tempc/(243.5+tempc))
# 	es=c[0]+tempc*(c[1]+tempc*(c[2]+tempc*(c[3]+tempc*(c[4]+tempc*(c[5]+tempc*(c[6]+tempc*(c[7]+tempc*c[8])))))))
# 	return es
# 
# 
# # ======================================================================
# # generate_region_mask
# #  generates a map of integer values that correspond to regions using
# #  the file region_0.25x0.25_costal2.5degExcluded.mat 
# #  in var_data/convective_transition_diag
# # Currently, there are 4 regions corresponding to ocean-only grid points
# #  in the Western Pacific (WPac), Eastern Pacific (EPac),
# #  Atlantic (Atl), and Indian (Ind) Ocean basins
# # Coastal regions (within 2.5 degree with respect to sup-norm) are excluded
# 
# def generate_region_mask(region_mask_filename, model_netcdf_filename, lat_var, lon_var):
#     
#     print("   Generating region mask..."),
# 
#     # Load & Pre-process Region Mask
#     matfile=scipy.io.loadmat(region_mask_filename)
#     lat_m=matfile["lat"]
#     lon_m=matfile["lon"] # 0.125~359.875 deg
#     region=matfile["region"]
#     lon_m=np.append(lon_m,np.reshape(lon_m[0,:],(-1,1))+360,0)
#     lon_m=np.append(np.reshape(lon_m[-2,:],(-1,1))-360,lon_m,0)
#     region=np.append(region,np.reshape(region[0,:],(-1,lat_m.size)),0)
#     region=np.append(np.reshape(region[-2,:],(-1,lat_m.size)),region,0)
# 
#     LAT,LON=np.meshgrid(lat_m,lon_m,sparse=False,indexing="xy")
#     LAT=np.reshape(LAT,(-1,1))
#     LON=np.reshape(LON,(-1,1))
#     REGION=np.reshape(region,(-1,1))
# 
#     LATLON=np.squeeze(np.array((LAT,LON)))
#     LATLON=LATLON.transpose()
# 
#     regMaskInterpolator=NearestNDInterpolator(LATLON,REGION)
# 
#     # Interpolate Region Mask onto Model Grid using Nearest Grid Value
#     pr_netcdf=Dataset(model_netcdf_filename,"r")
#     lon=np.asarray(pr_netcdf.variables[lon_var][:],dtype="float")
#     lat=np.asarray(pr_netcdf.variables[lat_var][:],dtype="float")
#     pr_netcdf.close()
#     if lon[lon<0.0].size>0:
#         lon[lon[lon<0.0]]+=360.0
#     lat=lat[np.logical_and(lat>=-20.0,lat<=20.0)]
# 
#     LAT,LON=np.meshgrid(lat,lon,sparse=False,indexing="xy")
#     LAT=np.reshape(LAT,(-1,1))
#     LON=np.reshape(LON,(-1,1))
#     LATLON=np.squeeze(np.array((LAT,LON)))
#     LATLON=LATLON.transpose()
#     REGION=np.zeros(LAT.size)
#     for latlon_idx in np.arange(REGION.shape[0]):
#         REGION[latlon_idx]=regMaskInterpolator(LATLON[latlon_idx,:])
#     REGION=np.reshape(REGION.astype(int),(-1,lat.size))
#     
#     print("...Generated!")
# 
#     return REGION
# 
# 

# # =====================
# # =================================================

#     
#     
# def precipbuoy_matchpcpta(ta_netcdf_filename, TA_VAR, pr_list, PR_VAR,\
#     prc_list, PRC_VAR, MODEL_NAME, time_idx_delta,\
#     START_DATE, END_DATE, PRECIP_FACTOR, SAVE_PRECIP,\
#     PREPROCESSING_OUTPUT_DIR, TIME_VAR,LAT_VAR,LON_VAR):
#     
#     strt_dt=dt.datetime.strptime(str(START_DATE),"%Y%m%d%H")
#     end_dt=dt.datetime.strptime(str(END_DATE),"%Y%m%d%H")
# 
#     ### LOAD T & q ###
# 
#     ta_netcdf=Dataset(ta_netcdf_filename,"r")
#     time_arr=ta_netcdf.variables[TIME_VAR]
#     time=np.asarray(time_arr[:],dtype="float")
#     time_units=time_arr.units
# 
#     if MODEL_NAME in ['CESM']:
#     
#         ### CESM requires special handling because of trailing zeros in date ##
#         strt_date=dt.datetime.strptime(time_units.split('since')[-1].lstrip(" "),'%Y-%m-%d %H:%M:%S')
#         time_res=time_units.split('since')[0].strip(" ")
#         dates_ta=[strt_date+dt.timedelta(**{time_res: i}) for i in time]
#     else:    
#     
#         dates_ta=num2pydate(time, units=time_units)    
#     ta_netcdf.close()
#         
#     for i in pr_list:
#     
#         pr_netcdf=Dataset(i,"r")
#         time_arr=pr_netcdf.variables[TIME_VAR]
#         time_pr=np.asarray(time_arr[:],dtype="float")
#         
#         if MODEL_NAME in ['CESM']:
#             ### CESM requires special handling because of trailing zeros in date ##
#             strt_date=dt.datetime.strptime(time_arr.units.split('since')[-1].lstrip(" "),'%Y-%m-%d %H:%M:%S')
#             time_res=time_arr.units.split('since')[0].strip(" ")
#             dates_pr=[strt_date+dt.timedelta(**{time_res: i}) for i in time_pr]        
#         else:
#             dates_pr=num2pydate(time_pr, units=time_arr.units)    
#         
#         
#         lat=np.asarray(pr_netcdf.variables[LAT_VAR][:],dtype="float")
#         lon=np.asarray(pr_netcdf.variables[LON_VAR][:],dtype="float")
#     
#         ## Take latitudinal slice
#         ilatx=np.where(np.logical_and(lat>=-20.0,lat<=20.0))[0]
#         lat=lat[ilatx]
# 
#         pr_var=np.squeeze(np.asarray(pr_netcdf.variables[PR_VAR][:,ilatx,:],dtype="float"))*PRECIP_FACTOR
#         pr_units=pr_netcdf.variables[PR_VAR].units
# 
#         ### Extract time of closest approach ###
#         ## Choosing time so that the 3hrly avg. precip. is centered 1.5 hrs after the
#         ## T,q measurement.
# 
#         time_ind=([j for j,k in enumerate(dates_pr) for l in dates_ta 
#         if np.logical_and((k-l).total_seconds()/3600.<=1.5,(k-l).total_seconds()/3600.>0.0)])
# 
#         if len(time_ind)>0:
# 
#             time_ind_new=np.zeros((max(len(dates_ta),len(time_ind))))
#             ### time_ind_new ensures that any mismatch is size is accounted for
#             ### for now it specifically targets the case where time.size-len(time_ind)=1 
#             ### We can easily generalize this case to time.size-len(time_ind)=n
#         
#             diff=len(dates_ta)-len(time_ind)
#         
#             try:
#                 assert len(time_ind)==len(dates_ta)
#                 time_ind_new[:]=time_ind
#             except:
#                 time_ind_new[:-diff]=time_ind
#                 time_ind_new[-(diff+1):-1]=np.nan 
#                
#             time_ind_new_fin=(np.int_(time_ind_new[np.isfinite(time_ind_new)]))
#             time_ind_new_nan=np.isnan(np.int_(time_ind_new))
#             ### Assuming that time is index 0
#             pr_var_temp=np.zeros((time_ind_new.size,pr_var.shape[1],pr_var.shape[2]))
#         
#             assert diff>=0
#         
#             if diff==0:
#                 pr_var_temp[:,...]=pr_var[time_ind_new_fin,...]        
#             else:               
#                 pr_var_temp[:-diff,...]=pr_var[time_ind_new_fin,...]
#                 pr_var_temp[-(diff+1):-1,...]=np.nan
#     
#             pr_netcdf.close()
#                  
#             if SAVE_PRECIP==1:
# 
#         #         Create PREPROCESSING_OUTPUT_DIR
#                 os.system("mkdir -p "+PREPROCESSING_OUTPUT_DIR)
# 
#         #        Get necessary coordinates/variables for netCDF files
# 
#                 pr_filename=PREPROCESSING_OUTPUT_DIR+ta_netcdf_filename.split('/')[-1].replace(TA_VAR,PR_VAR)
#             
#                 pr_output_netcdf=Dataset(pr_filename,"w",format="NETCDF4",zlib='True')
#                 pr_output_netcdf.description="Precipitation extracted and matched to the nearest"\
#                                             +"thermodynamic variable"+MODEL_NAME
#                 pr_output_netcdf.source="Convective Onset Statistics Diagnostic Package \
#                 - as part of the NOAA Model Diagnostic Task Force (MDTF) effort"
# 
#                 lon_dim=pr_output_netcdf.createDimension(LON_VAR,len(lon))
#                 lon_val=pr_output_netcdf.createVariable(LON_VAR,np.float64,(LON_VAR,))
#                 lon_val.units="degree"
#                 lon_val[:]=lon
# 
#                 lat_dim=pr_output_netcdf.createDimension(LAT_VAR,len(lat))
#                 lat_val=pr_output_netcdf.createVariable(LAT_VAR,np.float64,(LAT_VAR,))
#                 lat_val.units="degree_north"
#                 lat_val[:]=lat
# 
#                 time_dim=pr_output_netcdf.createDimension(TIME_VAR,None)
#                 time_val=pr_output_netcdf.createVariable(TIME_VAR,np.float64,(TIME_VAR,))
#                 time_val.units=time_units
#                 time_val[:]=time
# 
#                 pr_val=pr_output_netcdf.createVariable(PR_VAR,np.float64,(TIME_VAR,LAT_VAR,LON_VAR))
#                 pr_val.units=pr_units
#                 pr_val[:]=pr_var_temp
#     #             prc_val=prc_output_netcdf.createVariable(PR_VAR,np.float64,(TIME_VAR,LAT_VAR,LON_VAR))
#     #             prc_val.units="mm/hr"
#     #             prc_val[:]=prc_var_temp
# 
#                 pr_output_netcdf.close()
# 
#                 print('      '+pr_filename+" saved!")
# 
#         
#         
#             print(' Precip time series matched to thermo time series')
#         
#         
#     
# 
# # ======================================================================
# # convecTransBasic_calc_model
# #  takes in ALL 2D pre-processed fields (precip, CWV, and EITHER tave or qsat_int),
# #  calculates the binned data, and save it as a netCDF file
# #  in the var_data/convective_transition_diag directory
# 
# def precipbuoy_preprocess(*argsv):
#     # ALLOCATE VARIABLES FOR EACH ARGUMENT
#                 
#     BINT_BIN_WIDTH,\
#     BINT_RANGE_MAX,\
#     BINT_RANGE_MIN,\
#     CAPE_RANGE_MIN,\
#     CAPE_RANGE_MAX,\
#     CAPE_BIN_WIDTH,\
#     SUBSAT_RANGE_MIN,\
#     SUBSAT_RANGE_MAX,\
#     SUBSAT_BIN_WIDTH,\
#     NUMBER_OF_REGIONS,\
#     START_DATE,\
#     END_DATE,\
#     DATE_FORMAT,\
#     pr_list,\
#     PR_VAR,\
#     prc_list,\
#     PRC_VAR,\
#     MODEL_OUTPUT_DIR,\
#     THETAE_OUT,\
#     thetae_list,\
#     LFT_THETAE_VAR,\
#     LFT_THETAE_SAT_VAR,\
#     BL_THETAE_VAR,\
#     ta_list,\
#     TA_VAR,\
#     hus_list,\
#     HUS_VAR,\
#     LEV_VAR,\
#     PS_VAR,\
#     A_VAR,\
#     B_VAR,\
#     VERT_TYPE,\
#     MODEL_NAME,\
#     p_lev_mid,\
#     time_idx_delta,\
#     SAVE_THETAE,\
#     PREPROCESSING_OUTPUT_DIR,\
#     PRECIP_THRESHOLD,\
#     PRECIP_FACTOR,\
#     BIN_OUTPUT_DIR,\
#     BIN_OUTPUT_FILENAME,\
#     TIME_VAR,\
#     LAT_VAR,\
#     LON_VAR=argsv[0]
# 
#     
#     print("   Start pre-processing atmospheric temperature & moisture fields...")
#     for li in np.arange(len(ta_list)):
#         precipbuoy_calcthetae_ML(ta_list[li], TA_VAR, hus_list[li], HUS_VAR,\
#                             LEV_VAR, PS_VAR, A_VAR, B_VAR, VERT_TYPE, MODEL_NAME, p_lev_mid, time_idx_delta,\
#                             START_DATE, END_DATE, DATE_FORMAT, \
#                             SAVE_THETAE, PREPROCESSING_OUTPUT_DIR, THETAE_OUT,\
#                             LFT_THETAE_VAR,LFT_THETAE_SAT_VAR,BL_THETAE_VAR,\
#                             TIME_VAR,LAT_VAR,LON_VAR)
#     
#                                 
#                                 
# def precipbuoy_extractprecip(*argsv):
#     # ALLOCATE VARIABLES FOR EACH ARGUMENT
#             
#     BINT_BIN_WIDTH,\
#     BINT_RANGE_MAX,\
#     BINT_RANGE_MIN,\
#     CAPE_RANGE_MIN,\
#     CAPE_RANGE_MAX,\
#     CAPE_BIN_WIDTH,\
#     SUBSAT_RANGE_MIN,\
#     SUBSAT_RANGE_MAX,\
#     SUBSAT_BIN_WIDTH,\
#     NUMBER_OF_REGIONS,\
#     START_DATE,\
#     END_DATE,\
#     pr_list,\
#     PR_VAR,\
#     prc_list,\
#     PRC_VAR,\
#     MODEL_OUTPUT_DIR,\
#     THETAE_OUT,\
#     thetae_list,\
#     LFT_THETAE_VAR,\
#     LFT_THETAE_SAT_VAR,\
#     BL_THETAE_VAR,\
#     ta_list,\
#     TA_VAR,\
#     hus_list,\
#     HUS_VAR,\
#     LEV_VAR,\
#     PS_VAR,\
#     A_VAR,\
#     B_VAR,\
#     MODEL_NAME,\
#     p_lev_mid,\
#     time_idx_delta,\
#     SAVE_THETAE,\
#     SAVE_PRECIP,\
#     PREPROCESSING_OUTPUT_DIR,\
#     PRECIP_THRESHOLD,\
#     PRECIP_FACTOR,\
#     BIN_OUTPUT_DIR,\
#     BIN_OUTPUT_FILENAME,\
#     TIME_VAR,\
#     LAT_VAR,\
#     LON_VAR=argsv[0]
#     
#     print("   Start pre-processing precipitation fields...")
#     for li in np.arange(len(ta_list)):
#         precipbuoy_matchpcpta(ta_list[li], TA_VAR, pr_list, PR_VAR,\
#         prc_list, PRC_VAR, MODEL_NAME, time_idx_delta,\
#         START_DATE, END_DATE, \
#         PRECIP_FACTOR, SAVE_PRECIP, PREPROCESSING_OUTPUT_DIR, TIME_VAR, LAT_VAR,LON_VAR)
#               
#                                             
# def precipbuoy_bin(REGION, *argsv):
#     # ALLOCATE VARIABLES FOR EACH ARGUMENT
#             
#     BINT_BIN_WIDTH,\
#     BINT_RANGE_MAX,\
#     BINT_RANGE_MIN,\
#     CAPE_RANGE_MIN,\
#     CAPE_RANGE_MAX,\
#     CAPE_BIN_WIDTH,\
#     SUBSAT_RANGE_MIN,\
#     SUBSAT_RANGE_MAX,\
#     SUBSAT_BIN_WIDTH,\
#     NUMBER_OF_REGIONS,\
#     START_DATE,\
#     END_DATE,\
#     DATE_FORMAT,\
#     pr_list,\
#     PR_VAR,\
#     prc_list,\
#     PRC_VAR,\
#     MODEL_OUTPUT_DIR,\
#     THETAE_OUT,\
#     thetae_list,\
#     LFT_THETAE_VAR,\
#     LFT_THETAE_SAT_VAR,\
#     BL_THETAE_VAR,\
#     ta_list,\
#     TA_VAR,\
#     hus_list,\
#     HUS_VAR,\
#     LEV_VAR,\
#     PS_VAR,\
#     A_VAR,\
#     B_VAR,\
#     VERT_TYPE,\
#     MODEL_NAME,\
#     p_lev_mid,\
#     time_idx_delta,\
#     SAVE_THETAE,\
#     PREPROCESSING_OUTPUT_DIR,\
#     PRECIP_THRESHOLD,\
#     PRECIP_FACTOR,\
#     BIN_OUTPUT_DIR,\
#     BIN_OUTPUT_FILENAME,\
#     TIME_VAR,\
#     LAT_VAR,\
#     LON_VAR=argsv[0]
#     
#     # Re-load file lists for thetae_ave & precip.
#     thetae_list=sorted(glob.glob(PREPROCESSING_OUTPUT_DIR+"/"+THETAE_OUT+'*'))
# #     pr_list=sorted(glob.glob(PREPROCESSING_OUTPUT_DIR+"/"+PR_VAR+'*'))
#              
#     # Define Bin Centers
#     cape_bin_center=np.arange(CAPE_RANGE_MIN,CAPE_RANGE_MAX+CAPE_BIN_WIDTH,CAPE_BIN_WIDTH)
#     subsat_bin_center=np.arange(SUBSAT_RANGE_MIN,SUBSAT_RANGE_MAX+SUBSAT_BIN_WIDTH,SUBSAT_BIN_WIDTH)
#     bint_bin_center=np.arange(BINT_RANGE_MIN,BINT_RANGE_MAX+BINT_BIN_WIDTH,BINT_BIN_WIDTH)
# 
#     NUMBER_CAPE_BIN=cape_bin_center.size
#     NUMBER_SUBSAT_BIN=subsat_bin_center.size
#     NUMBER_BINT_BIN=bint_bin_center.size
#     
#     # Allocate Memory for Arrays
#     P0=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#     P1=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#     P2=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#     PE=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#     
#     Q0=np.zeros((NUMBER_BINT_BIN))
#     Q1=np.zeros((NUMBER_BINT_BIN))
#     Q2=np.zeros((NUMBER_BINT_BIN))
#     QE=np.zeros((NUMBER_BINT_BIN))
#     
#     ### array to hold percentiles
#     precip_percentile=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#     precip_percentile_bint=np.zeros((NUMBER_BINT_BIN))
# 
#     ## function to return px percentile for non-empty values, else return nan
#     centile=lambda x,px: np.percentile(x,px) if x else np.nan  
# 
#         
#     ## create and initialize dictionary
#     R0={} 
#     for ncape in np.arange(NUMBER_CAPE_BIN):
#         for nsub in np.arange(NUMBER_SUBSAT_BIN):
#             R0[nsub,ncape]=[]  
# 
#     R1={} 
#     for nbint in np.arange(NUMBER_BINT_BIN):
#         R1[nbint]=[]  
#         
#     ### Internal constants ###
# 
#     ref_thetae=340 ## reference theta_e in K to convert buoy. to temp units
#     gravity=9.8 ### accl. due to gravity
#     thresh_pres=700 ## Filter all point below this surface pressure in hPa
# 
#     ## Open all available precip. data ###
#     pr_ds=xr.open_mfdataset(pr_list)
#     
#     ### rename dimensions to correct non-standard names
#     LAT_VAR_NEW='lat'
#     LON_VAR_NEW='lon'
#     TIME_VAR_NEW='time'
#     lat_slice=slice(-20,20) ## Set latitudinal slice
#     pr_ds=pr_ds.rename({TIME_VAR:TIME_VAR_NEW,LAT_VAR:LAT_VAR_NEW,LON_VAR:LON_VAR_NEW})
#     fix_datetime(pr_ds,DATE_FORMAT)
# 
#     
# 
#     for i,j in enumerate(thetae_list):
#         
#         print(j)
#         theta_ds=xr.open_mfdataset(j)
#         
#         pr_ds_sub=pr_ds.sel(time=theta_ds['time'],method='nearest',tolerance="1.5H")
#         pr_ds_sub=pr_ds_sub.sel(lat=lat_slice)
#         
#         print('LOADING thetae and pcp. values')
#         thetae_bl=theta_ds.thetae_bl.values
#         thetae_lt=theta_ds.thetae_lt.values
#         thetae_sat_lt=theta_ds.thetae_sat_lt.values
#         ps=theta_ds.ps.values        
#         pr=pr_ds_sub[PR_VAR].values*PRECIP_FACTOR        
#         
#         print("      "+j+" Loaded!")
# 
#     
#         ps=ps*1e-2 ## Convert surface pressure to hPa
#         
#         delta_pl=ps-100-500
#         delta_pb=100
#         wb=(delta_pb/delta_pl)*np.log((delta_pl+delta_pb)/delta_pb)
#         wb[:]=0.0 ## turning off the CAPE dependence in BL
#         wl=1-wb
#         
#         
#     
#         wb[ps<thresh_pres]=np.nan
#         wl[ps<thresh_pres]=np.nan
# 
#         cape=ref_thetae*(thetae_bl-thetae_sat_lt)/thetae_sat_lt
#         subsat=ref_thetae*(thetae_sat_lt-thetae_lt)/thetae_sat_lt
#         bint=gravity*(wb*(thetae_bl-thetae_sat_lt)/thetae_sat_lt-wl*(thetae_sat_lt-thetae_lt)/thetae_sat_lt)
# 
#         cape[ps<thresh_pres]=np.nan
#         subsat[ps<thresh_pres]=np.nan
#         bint[ps<thresh_pres]=np.nan
#         
#         print("      Binning...")
#         
#         ### Start binning
#         SUBSAT=(subsat-SUBSAT_RANGE_MIN)/SUBSAT_BIN_WIDTH-0.5
#         SUBSAT=SUBSAT.astype(int)
#         
#         CAPE=(cape-CAPE_RANGE_MIN)/CAPE_BIN_WIDTH-0.5
#         CAPE=CAPE.astype(int)
# 
#         BINT=(bint-BINT_RANGE_MIN)/(BINT_BIN_WIDTH)+0.5
#         BINT=BINT.astype(int)
# 
#         RAIN=pr        
#         RAIN[RAIN<0]=0 # Sometimes models produce negative rain rates
# 
#         # Binning is structured in the following way to avoid potential round-off issue
#         #  (an issue arise when the total number of events reaches about 1e+8)
#         p0=np.zeros((NUMBER_SUBSAT_BIN,NUMBER_CAPE_BIN))
#         p1=np.zeros_like(p0)
#         p2=np.zeros_like(p0)
#         pe=np.zeros_like(p0)
# #                         
#         q0=np.zeros((NUMBER_BINT_BIN))
#         q1=np.zeros((NUMBER_BINT_BIN))
#         q2=np.zeros((NUMBER_BINT_BIN))
#         qe=np.zeros((NUMBER_BINT_BIN))
#     
#         r0={}
#         for keys in R0.keys():
#                 r0[keys]=[]  
# 
#         r1={}
#         for keys in R1.keys():
#                 r1[keys]=[]  
# 
# 
#         for lon_idx in np.arange(SUBSAT.shape[2]):
#                     
#             precipbuoy_binThetae(lon_idx, REGION, PRECIP_THRESHOLD,
#             NUMBER_CAPE_BIN, NUMBER_SUBSAT_BIN, NUMBER_BINT_BIN, 
#             CAPE, SUBSAT, BINT, RAIN, p0, p1, p2, pe, q0, q1, q2, qe)
# 
#             P0+=p0
#             P1+=p1
#             P2+=p2
#             PE+=pe
#             
#             Q0+=q0
#             Q1+=q1
#             Q2+=q2
#             QE+=qe
#             
#             precipbuoy_percentile_binThetae(lon_idx, REGION, PRECIP_THRESHOLD, 
#             NUMBER_CAPE_BIN, NUMBER_SUBSAT_BIN, 
#             NUMBER_BINT_BIN, CAPE, SUBSAT, BINT, 
#             RAIN, r0, r1)
#             
#             ## append to list and reset r0 list size ###
#             for keys in R0.keys():
#                     R0[keys]+=r0[keys] 
#                     r0[keys]=[]
# 
#             for keys in R1.keys():
#                     R1[keys]+=r1[keys] 
#                     r1[keys]=[]
# 
#             ### Re-set the array values to zero ###
#             p0[:]=0
#             q0[:]=0
# 
#             p1[:]=0
#             q1[:]=0
# 
#             p2[:]=0
#             q2[:]=0
# 
#             pe[:]=0
#             qe[:]=0
# 
#         temp_prc=P1/P0
#     
#     print("   Total binning complete!")
#     print('computing percentile')
#     
#     px=90 ## get 90th percentile 
#     for keys in R0.keys():
#          precip_percentile[keys]=centile(R0[keys],px)
# 
#     for keys in R1.keys():
#          precip_percentile_bint[keys]=centile(R1[keys],px)
# 
#         
#     data_set=xr.Dataset(data_vars={'P0': (('subsat','cape'), P0),
#                                    'PE': (('subsat','cape'), PE),
#                                    'P1': (('subsat','cape'), P1),
#                                    'P2': (('subsat','cape'), P2),
#                                    'Q0': (('bint'),Q0),
#                                    'QE': (('bint'),QE),
#                                    'Q1': (('bint'),Q1),
#                                    'Q2': (('bint'),Q2),
#                                    'R0': (('subsat','cape'), precip_percentile),
#                                    'R1':(('bint'), precip_percentile_bint)},
#                         coords={'subsat':subsat_bin_center,
#                                 'cape':cape_bin_center,
#                                 'bint':bint_bin_center})
# 
#     data_set.subsat.attrs['units']="K"
#     data_set.cape.attrs['units']="K"
#     data_set.bint.attrs['units']="m/s^2"
#     
#     data_set.P1.attrs['units']="mm/hr"
#     data_set.P2.attrs['units']="mm^2/hr^2"
#     
#     data_set.Q1.attrs['units']="mm/hr"
#     data_set.Q2.attrs['units']="mm^2/hr^2"
# 
#     data_set.R0.attrs['long_name']="90th percentile of precip."
#     
#     data_set.attrs['source']="Convective Onset Statistics Diagnostic Package \
#     - as part of the NOAA Model Diagnostic Task Force (MDTF) effort"
# 
#     ### Manually clobbering since .to_netcdf throws permission errors ###
# 
#     try:
#         os.remove(BIN_OUTPUT_DIR+BIN_OUTPUT_FILENAME+".nc")
#     except:
#         pass
# 
#     data_set.to_netcdf(BIN_OUTPUT_DIR+BIN_OUTPUT_FILENAME+".nc",
#     mode='w',
#     engine='netcdf4')
#     
#     print("   Binned results saved as "+BIN_OUTPUT_DIR+BIN_OUTPUT_FILENAME+".nc!")
# 
#     return subsat_bin_center,cape_bin_center,bint_bin_center,P0,PE,P1,P2,Q0,QE,Q1,Q2
# 
#                    
# def precipbuoy_loadAnalyzedData(*argsv):
# 
#     print('Here:',argsv)
# 
#     bin_output_list=argsv[0]
#     if (len(bin_output_list)!=0):
# 
#         bin_output_filename=bin_output_list[0][0]    
#         if bin_output_filename.split('.')[-1]=='nc':
#             bin_output_netcdf=Dataset(bin_output_filename,"r")
#             print(bin_output_netcdf)
# 
#             P0=np.asarray(bin_output_netcdf.variables["P0"][:,:],dtype="float")
#             
#             ### If the second moments are not found, return zeroes ###
#             try:
#                 PE=np.asarray(bin_output_netcdf.variables["PE"][:,:],dtype="float")
#                 QE=np.asarray(bin_output_netcdf.variables["QE"][:],dtype="float")
#             except:
#                 PE=np.zeros_like(P0)
#                 QE=np.zeros_like(P0)
#                 
#             P1=np.asarray(bin_output_netcdf.variables["P1"][:,:],dtype="float")
#             P2=np.asarray(bin_output_netcdf.variables["P2"][:,:],dtype="float")
#             Q0=np.asarray(bin_output_netcdf.variables["Q0"][:],dtype="float")
#             Q1=np.asarray(bin_output_netcdf.variables["Q1"][:],dtype="float")
#             Q2=np.asarray(bin_output_netcdf.variables["Q2"][:],dtype="float")
# 
#             cape_bin_center=np.asarray(bin_output_netcdf.variables["cape"][:],dtype="float")
#             subsat_bin_center=np.asarray(bin_output_netcdf.variables["subsat"][:],dtype="float")
#             bint_bin_center=np.asarray(bin_output_netcdf.variables["bint"][:],dtype="float")
# 
#             bin_output_netcdf.close()
#             
#         # Return CWV_BIN_WIDTH & PRECIP_THRESHOLD to make sure that
#         #  user-specified parameters are consistent with existing data
# #         return subsat_bin_center,cape_bin_center,bint_bin_center,P0,PE,P1,P2,Q0,QE,Q1,Q2
# #         return subsat_bin_center,cape_bin_center,bint_bin_center,P0,P1,P2,Q0,Q1,Q2
#         return subsat_bin_center, cape_bin_center, bint_bin_center,P0, PE, P1, P2,\
#          Q0, QE, Q1, Q2
#     else: # If the binned model/obs data does not exist (in practice, for obs data only)   
#         return [],[],[],[],[],[],[],[],[]
# 
# 
# def precipbuoy_plot(ret,argsv1,argsv2,*argsv3):
# 
#     '''
#     Plotting precipitation surfaces in 3D
#     '''
# 
#     print("Plotting...")
# 
#     # Load binned model data with parameters
#     #  CBW:CWV_BIN_WIDTH, PT:PRECIP_THRESHOLD
#     subsat_bin_center,\
#     cape_bin_center,\
#     bint_bin_center,\
#     P0,\
#     PE,\
#     P1,\
#     P2,\
#     Q0,\
#     QE,\
#     Q1,\
#     Q2=ret
#         
#     # Load plotting parameters from convecTransBasic_usp_plot.py
#     fig_params=argsv1
# 
#     # Load parameters from convecTransBasic_usp_calc.py
#     #  Checking CWV_BIN_WIDTH & PRECIP_THRESHOLD 
#     #  against CBW & PT guarantees the detected binned result
#     #  is consistent with parameters defined in 
#     #  convecTransBasic_usp_calc.py
#     NUMBER_THRESHOLD,\
#     FIG_OUTPUT_DIR,\
#     FIG_OUTPUT_FILENAME,\
#     FIG_EXTENSION,\
#     OBS,\
#     FIG_OBS_DIR,\
#     FIG_OBS_FILENAME,\
#     USE_SAME_COLOR_MAP,\
#     OVERLAY_OBS_ON_TOP_OF_MODEL_FIG,\
#     MODEL_NAME=argsv3[0]
# 
# 
#     # Load binned OBS data (default: trmm3B42 + ERA-I)
#     subsat_bin_center_obs,\
#     cape_bin_center_obs,\
#     bint_bin_center_obs,\
#     P0_obs,\
#     PE_obs,\
#     P1_obs,\
#     P2_obs,\
#     Q0_obs,\
#     QE_obs,\
#     Q1_obs,\
#     Q2_obs=precipbuoy_loadAnalyzedData(argsv2)
# 
#     ### Create obs. binned precip. ###    
#     P0_obs[P0_obs==0.0]=np.nan
#     P_obs=P1_obs/P0_obs
#     P_obs[P0_obs<NUMBER_THRESHOLD]=np.nan
# 
#     ### Create model binned precip. ###    
#     P0[P0==0.0]=np.nan
#     P_model=P1/P0
#     P_model[P0<NUMBER_THRESHOLD]=np.nan
# 
#     ### Compute q-T ratio ###    
#     gamma_qT={}
#     gamma_qT['OBS']=precipbuoy_calcqT_ratio(P_obs,P0_obs,cape_bin_center_obs,subsat_bin_center_obs)
#     gamma_qT[MODEL_NAME]=precipbuoy_calcqT_ratio(P_model,PE,cape_bin_center,subsat_bin_center)
# 
#     ### Compute the qT ratio from model precipitation surfaces ###
#     ### Save the qT ratios in a pickle ###
#     import pickle
#     fname='gammaqT_'+FIG_OUTPUT_FILENAME+'.out'
#     with open(fname, 'wb') as fp:
#         pickle.dump(gamma_qT, fp, protocol=pickle.HIGHEST_PROTOCOL)    
#     #######
# 
#     axes_fontsize,axes_elev,axes_azim,figsize1,figsize2 = fig_params['f0']
#     print("   Plotting Surfaces..."),
#     # create figure canvas
#     
#     fig = mp.figure(figsize=(figsize1,figsize2))
#     ax = fig.add_subplot(121, projection='3d')
# #         ax = fig_obs.gca(projection='3d')
# 
#     X, Y = np.meshgrid(subsat_bin_center_obs,cape_bin_center_obs)
#             
#     # create colorbar
#     normed=matplotlib.colors.Normalize(vmin=fig_params['f1'][2][0],vmax=fig_params['f1'][2][1])
#     colors_obs=matplotlib.cm.nipy_spectral(normed(P_obs.T))
# 
#     ax.plot_wireframe(X,Y,P_obs.T,color='black')
#     ax.plot_surface(X,Y,P_obs.T,facecolors=colors_obs,alpha=0.5)#,cmap=mp.get_cmap('nipy_spectral'),alpha=0.5,
#     
#     ### Fix to avoid plotting error ###
#     for spine in ax.spines.values():
#         spine.set_visible(False)
# 
# #     ax.set_xlim(fig_params['f1'][0])
# #     ax.set_ylim(fig_params['f1'][1])
#     ax.set_zlim(fig_params['f1'][2])
# 
#     ### Set the x and y limits to span the union of both obs and model bins
#     ax.set_xlim(min(subsat_bin_center_obs.min(),subsat_bin_center.min()),
#     max(subsat_bin_center_obs.max(),subsat_bin_center.max()))
# 
#     ax.set_ylim(min(cape_bin_center_obs.min(),cape_bin_center.min()),
#     max(cape_bin_center_obs.max(),cape_bin_center.max()))
# 
#     ax.text2D(.6,.75,'$\gamma_{qT}$=%.2f'%(gamma_qT['OBS']),transform=ax.transAxes,fontsize=15)
# 
#     ax.set_xlabel(fig_params['f1'][3],fontsize=axes_fontsize)
#     ax.set_ylabel(fig_params['f1'][4],fontsize=axes_fontsize)
#     ax.set_zlabel(fig_params['f1'][5],fontsize=axes_fontsize)
#     ax.view_init(elev=axes_elev, azim=axes_azim)
#     ax.set_title('TRMM 3B42 + ERA-I',fontsize=axes_fontsize)
# 
#     ax1 = fig.add_subplot(122, projection='3d')
#     X, Y = np.meshgrid(subsat_bin_center_obs,cape_bin_center_obs)
#     ax1.plot_surface(X,Y,P_obs.T,color='black',zorder=50,alpha=0.25,vmax=5.,vmin=0.)
# 
# #     xind=np.where((subsat_bin_center_obs==10))[0]
# #     yind=np.where((cape_bin_center_obs==10))[0]
# # 
# #     print(P0[xind,yind])
# #     print(P1[xind,yind])
# #     exit()
# 
#     X, Y = np.meshgrid(subsat_bin_center,cape_bin_center)
#     colors_model=matplotlib.cm.nipy_spectral(normed(P_model.T))
# 
# 
#     ax1.plot_wireframe(X,Y,P_model.T,color='black')
#     ax1.plot_surface(X,Y,P_model.T,facecolors=colors_model,alpha=0.5)#,cmap=mp.get_cmap('nipy_spectral'),alpha=0.5,
# 
#     for spine in ax1.spines.values():
#         spine.set_visible(False)
#         
# #     ax1.set_xlim(fig_params['f1'][0])
# #     ax1.set_ylim(fig_params['f1'][1])
#     ax1.set_zlim(fig_params['f1'][2])
#     
#     ### Set the x and y limits to span the union of both obs and model bins
#     ax1.set_xlim(min(subsat_bin_center_obs.min(),subsat_bin_center.min()),
#     max(subsat_bin_center_obs.max(),subsat_bin_center.max()))
# 
#     ax1.set_ylim(min(cape_bin_center_obs.min(),cape_bin_center.min()),
#     max(cape_bin_center_obs.max(),cape_bin_center.max()))
# 
# 
#     ax1.set_xlabel(fig_params['f1'][3],fontsize=axes_fontsize)
#     ax1.set_ylabel(fig_params['f1'][4],fontsize=axes_fontsize)
#     ax1.set_zlabel(fig_params['f1'][5],fontsize=axes_fontsize)
#     ax1.view_init(elev=axes_elev, azim=axes_azim)
#     ax1.set_title(MODEL_NAME,fontsize=axes_fontsize)
#     ax1.text2D(1.7,.75,'$\gamma_{qT}$=%.2f'%(gamma_qT[MODEL_NAME]),transform=ax.transAxes,fontsize=15)
# 
#     
#     mp.tight_layout()
#     
#     mp.savefig(FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_surfaces'+'.'+FIG_EXTENSION, bbox_inches="tight")
#         
#     print("...Completed!")
#     print("      Surface plots saved as "+FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_surfaces'+'.'+FIG_EXTENSION+"!")
# 
#         
#     fig = mp.figure(figsize=(figsize1,figsize2))
# 
#     ax = fig.add_subplot(221)
# 
#     dx=abs(np.diff(subsat_bin_center)[0])
#     dy=abs(np.diff(cape_bin_center)[0])
#     pdf_obs=P0_obs/(np.nansum(P0_obs)*dx*dy)
# 
#     ax.contourf(subsat_bin_center_obs,cape_bin_center_obs,np.log10(pdf_obs).T)
#     ax.set_xlabel('SUBSAT (K)',fontsize=axes_fontsize)
#     ax.set_ylabel('CAPE (K)',fontsize=axes_fontsize)
#     ax.set_title('TRMM 3B42 + ERA-I',fontsize=axes_fontsize)
#     
#     ax.set_xlim(min(subsat_bin_center_obs.min(),subsat_bin_center.min()),
#     max(subsat_bin_center_obs.max(),subsat_bin_center.max()))
# 
#     ax.set_ylim(min(cape_bin_center_obs.min(),cape_bin_center.min()),
#     max(cape_bin_center_obs.max(),cape_bin_center.max()))
#     
#     ax2 = fig.add_subplot(222)
# 
#     dx=abs(np.diff(subsat_bin_center)[0])
#     dy=abs(np.diff(cape_bin_center)[0])
#     pdf_model=P0/(np.nansum(P0)*dx*dy)
# 
#     ax2.contourf(subsat_bin_center,cape_bin_center,np.log10(pdf_model).T)
#     ax2.set_xlabel('SUBSAT (K)',fontsize=axes_fontsize)
#     ax2.set_title(MODEL_NAME,fontsize=axes_fontsize)
# 
#     ax2.set_xlim(min(subsat_bin_center_obs.min(),subsat_bin_center.min()),
#     max(subsat_bin_center_obs.max(),subsat_bin_center.max()))
# 
#     ax2.set_ylim(min(cape_bin_center_obs.min(),cape_bin_center.min()),
#     max(cape_bin_center_obs.max(),cape_bin_center.max()))
#     
# 
# 
#     mp.tight_layout()
#     mp.savefig(FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_2d_pdf'+'.'+FIG_EXTENSION, bbox_inches="tight")
#         
#     print("...Completed!")
#     print("      2D pdfs saved as "+FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_2d_pdf'+'.'+FIG_EXTENSION+"!")
# 
# 
#     fig = mp.figure(figsize=(figsize1,figsize2))
# 
#     ax = fig.add_subplot(221)
# 
#     Q0[Q0==0.0]=np.nan
#     Q_model=Q1/Q0
#     Q_model[Q0<NUMBER_THRESHOLD]=np.nan
# 
#     Q0_obs[Q0_obs==0.0]=np.nan
#     Q_obs=Q1_obs/Q0_obs
#     Q_obs[Q0_obs<NUMBER_THRESHOLD]=np.nan
# 
#     ax.scatter(bint_bin_center,Q_obs,marker='D',c='grey',label=OBS,alpha=0.5)
#     ax.scatter(bint_bin_center,Q_model,marker='*',s=20,c='red',label=MODEL_NAME,alpha=0.5)
#     ax.set_xlabel('$B_L$',fontsize=axes_fontsize)
#     ax.set_title('P vs. $B_L$',fontsize=axes_fontsize)
# 
#     handles, labels = ax.get_legend_handles_labels()
#     num_handles=len(handles)
#     
#     leg = ax.legend(handles[0:num_handles], labels[0:num_handles], fontsize=axes_fontsize, bbox_to_anchor=(0.05,0.95), \
#                 bbox_transform=ax.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.1, \
#                 fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0, \
#                 handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
# 
#     ax.set_ylim(fig_params['f1'][2])
#     ax.set_ylabel(fig_params['f1'][5],fontsize=axes_fontsize)
# 
#     
# #     ax.set_title('TRMM 3B42 + ERA-I',fontsize=axes_fontsize)
#     
#     ax2 = fig.add_subplot(222)
# 
#     dx=abs(np.diff(bint_bin_center)[0])
#     pdf_obs=Q0_obs/(np.nansum(Q0_obs)*dx)
#     pdf_model=Q0/(np.nansum(Q0)*dx)
# 
#     ax2.scatter(bint_bin_center,np.log10(pdf_obs),marker='D',c='grey',label=OBS,alpha=0.5)
#     ax2.scatter(bint_bin_center,np.log10(pdf_model),marker='*',s=20,c='red',label=MODEL_NAME,alpha=0.5)
#     num_handles=len(handles)
#     
#     leg = ax2.legend(handles[0:num_handles], labels[0:num_handles], fontsize=axes_fontsize, bbox_to_anchor=(0.05,0.95), \
#                 bbox_transform=ax2.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.1, \
#                 fancybox=False, scatterpoints=1,  framealpha=1, borderpad=0, \
#                 handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
# 
#     ax2.set_xlabel('$B_L$',fontsize=axes_fontsize)
#     ax2.set_title('pdfs of $B_L$',fontsize=axes_fontsize)
# 
#     mp.tight_layout()
#     mp.savefig(FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_BL_stats'+'.'+FIG_EXTENSION, bbox_inches="tight")
#         
#     print("...Completed!")
#     print("      2D pdfs saved as "+FIG_OBS_DIR+"/"+FIG_OUTPUT_FILENAME+'.pcp_BL_stats'+'.'+FIG_EXTENSION+"!")
# 

