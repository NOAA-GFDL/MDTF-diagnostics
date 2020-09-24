#!/usr/bin/env python
'''
Front Detection Algorithm

Adopted from Naud et al., 2016, based on Hewson at 1km, and Simmonds et al., 2012

Created by: Jeyavinoth Jeyaratnam
Created on: March 1st, 2019

Last Modified: March 22nd, 2019

'''
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.ndimage import label, generate_binary_structure
from netCDF4 import Dataset
import pdb
from mpl_toolkits.basemap import Basemap
import matplotlib as mpl
import os
import glob

def four_corner_shift(arr, shift_len=1):
    up = np.pad(arr, ((shift_len, 0), (0, 0)), mode='constant', constant_values=np.nan)[:-shift_len, :]
    down = np.pad(arr, ((0, shift_len), (0, 0)), mode='constant', constant_values=np.nan)[shift_len:, :]
    left = np.roll(arr, -1, axis=1)
    right = np.roll(arr, 1, axis=1)

    return up, down, left, right

def theta_from_temp_pres(temp, pres):
  return temp * (1000./pres)**(2./7.)

def clean_fronts(wf, cf, cyc_lon, cyc_lat, cyc_center_lon, cyc_center_lat):

    w_label, w_num = label(wf)
    c_label, c_num = label(cf)

    wf_list = []

    for i_w in range(1, w_num+1):
      ind = np.argwhere(w_label == i_w)

      # gettin rid of clusters less than 2 pts
      if (ind.shape[0] <= 2):
        continue
      i_w_lat = [cyc_lat[i_ind[0], i_ind[1]] for i_ind in ind]
      i_w_lon = [cyc_lon[i_ind[0], i_ind[1]] for i_ind in ind]

      # storm attribution
      mean_lat = np.nanmean(i_w_lat)
      mean_lon = np.nanmean(i_w_lon)
      dist_deg = get_distance_deg(mean_lon, mean_lat, cyc_center_lon, cyc_center_lat)

      # strom attibution conditions
      if not ((mean_lon > cyc_center_lon) & (dist_deg < 15.) & (abs(cyc_center_lat - mean_lat) < 5.)):
        continue

      # final list of values 
      wf_list.append([i_w_lon, i_w_lat])

    cf_list = []
    # all_cf_list = []
    for i_c in range(1, c_num+1):
      ind = np.argwhere(c_label == i_c)
      if (ind.shape[0] <= 2):
        continue

      # keeping only the eastern most point on the front cluster
      i_c_lat = np.asarray([cyc_lat[i_ind[0], i_ind[1]] for i_ind in ind])
      i_c_lon = np.asarray([cyc_lon[i_ind[0], i_ind[1]] for i_ind in ind])
      i_c_ind = np.asarray([i_ind for i_ind in ind])
      # all_cf_list.append([i_c_lon, i_c_lat])

      f_lat = []
      f_lon = []
      for uni_lat in set(i_c_lat):
        uni_ind = (i_c_lat == uni_lat)
        f_lat.append(uni_lat)
        f_lon.append(np.nanmax(i_c_lon[uni_ind]))
    
      # strom attribution
      mean_lat = np.nanmean(f_lat)
      mean_lon = np.nanmean(f_lon)
      dist_deg = get_distance_deg(mean_lon, mean_lat, cyc_center_lon, cyc_center_lat)

      # storm attribution conditions
      if not ((dist_deg < 15) & (abs(mean_lon - cyc_center_lon) < 7.5) & (mean_lat < cyc_center_lat)):
        continue
      
      # addtiional conditions before selecting cold fronts
      if not ((np.any(np.abs(f_lon - cyc_center_lon) < 2.5)) & ((90 - np.abs(np.nanmax(f_lat))) < 5) & ((cyc_center_lon - np.median(f_lon)) > 15)):
        continue
      
      # for the remaining clusters I have to apply Haning filter that simmonds et al, 2012, allow more than one cluster
      cf_list.append([f_lon, f_lat])

    return wf_list, cf_list

def hewson_1998(latGrid, lonGrid, theta, u_wind, v_wind):

    # computing first derivative
    gx, gy = geo_gradient(latGrid, lonGrid, theta)
    gNorm = norm(gx, gy) 

    # computing the 2nd derivative using the first derivative
    # gNorm_gNorm = grad(abs(gNorm))
    gx_gNorm, gy_gNorm = geo_gradient(latGrid, lonGrid, gNorm)
    gNorm_gNorm = norm(gx_gNorm, gy_gNorm)
    
    # let mu = grad(abs(grad(theta)))
    mu_x = np.copy(gx_gNorm)
    mu_y = np.copy(gy_gNorm)
    abs_mu = norm(mu_x, mu_y) 

    grad_abs_mu_x, grad_abs_mu_y = geo_gradient(latGrid, lonGrid, abs_mu)
   
    ################### Computing M1 and M2 values ####################
    # compute m1, and m2, using k1, and k2 values
    sign_m1_val = gx * mu_x + gy * mu_y
    sign_m1_val = smooth_grid(sign_m1_val, center_weight=1., iter=1) #JJ
    sign_m1 = np.zeros(sign_m1_val.shape)
    sign_m1[sign_m1_val > 0.] = 1. 
    sign_m1[sign_m1_val < 0.] = -1. 

    m1 = abs_mu * sign_m1

    # calculating m1 using eq(9), hewson 1998
    # m1 = -1*(mu_x, mu_y) *dot* (gx/gNorm, gy/gNorm)
    # m1 = -1*(mu_x*gx/gNorm + mu_y*gy/gNorm)

    # computing m2
    # compute distance grid
    distX, distY = compute_dist_grids(latGrid, lonGrid)
    dist_avg = np.sqrt(distX**2 + distY**2)

    # m2 (Hewson 1998) 
    mconst = 1/math.sqrt(2)
    m2 = gNorm + mconst * dist_avg * gNorm_gNorm / 100
   
    k1 = 0.33 # degC per 100km per 100km; gridlength of 100km
    k2 = 1.49 # degC per 100km
    # all my gradients are calculated as per 100 km, so here I have to account that for m2 calculation, my gridlenght has to be converted as per 100km as well

    m1_mask = m1 > k1
    m2_mask = m2 > k2

    ########### Computing eq 6 from the Hewson

    # first I have to compute the positive direciton s vector using appendix 2 
    # s is the five point mean axis (appendix 2)
    # then project the 4 outer vectors in the positive s direction vector 
    # compute total divergence of the resolved vectors using simple first order finite differencing (p 46, Hewson 1998)

    # S five point mean
    mu_mag = np.copy(abs_mu)

    # I take care of division by zero in the arctan2 function, also I force the beta to tbe [0, np.pi]
    # I think Catherine does not account for this
    valid_ind = (~(mu_x == 0))

    mu_ang = np.empty(abs_mu.shape)*np.nan
    mu_ang[~valid_ind] = np.pi/2.
    mu_ang[valid_ind] = np.arctan(mu_y[valid_ind]/mu_x[valid_ind])
    mu_ang[mu_ang < 0] = mu_ang[mu_ang < 0] + np.pi
   
    # shift to get the 4 corners 
    up_shift_ang, down_shift_ang, left_shift_ang, right_shift_ang = four_corner_shift(mu_ang, shift_len=1)
    up_shift_mag, down_shift_mag, left_shift_mag, right_shift_mag = four_corner_shift(mu_mag, shift_len=1)
    
    # stacking the 5 nearest neighbors for the calculation
    ang_stack = np.dstack((mu_ang, up_shift_ang, down_shift_ang, right_shift_ang, left_shift_ang))
    mag_stack = np.dstack((mu_mag, up_shift_mag, down_shift_mag, right_shift_mag, left_shift_mag))

    # computing the P, Q and n from appendix 2.1
    n = np.nansum(np.double(~np.isnan(ang_stack) & ~np.isnan(mag_stack)))
    sump = np.nansum(mag_stack * np.cos(2*ang_stack), 2)
    sumq = np.nansum(mag_stack * np.sin(2*ang_stack), 2)

    # from P, Q and n, we have to compute the D and beta mean values
    # again here we make sure B mean is in the range [0, pi], and also take care of division by zero
    # this will give us the 5 mean axis of the "s" vector, in polar cdts
    valid_ind = ~(sump == 0)
    beta_mean = np.empty(sump.shape)*np.nan
    beta_mean[~valid_ind] = np.pi/2.
    beta_mean[valid_ind] = .5 * np.arctan(sumq[valid_ind]/sump[valid_ind])
    beta_mean[beta_mean < 0] = beta_mean[beta_mean < 0] + np.pi
    D_mean = (1/n) * np.sqrt(sump**2 + sumq**2)

    ## Resolve the four outer vectors into the positive s_hat [D_mean, B_mean]
    # shifting the mu_x and mu_y to get the 4 corners
    # this overlaps the neighbors to allow us to vector caculate
    up_shift_mu_x, down_shift_mu_x, left_shift_mu_x, right_shift_mu_x = four_corner_shift(mu_x, shift_len=1)
    up_shift_mu_y, down_shift_mu_y, left_shift_mu_y, right_shift_mu_y = four_corner_shift(mu_y, shift_len=1)

    # resolve the 4 outer x,y vectors onto the center postiive s_hat
    resolve_up = up_shift_mu_x * np.cos(beta_mean) + up_shift_mu_y * np.sin(beta_mean)
    resolve_down = down_shift_mu_x * np.cos(beta_mean) + down_shift_mu_y * np.sin(beta_mean)
    resolve_left = left_shift_mu_x * np.cos(beta_mean) + left_shift_mu_y * np.sin(beta_mean)
    resolve_right = right_shift_mu_x * np.cos(beta_mean) + right_shift_mu_y * np.sin(beta_mean)

    # computing the total divergence of the resolved vectors, using simple first order diffferentiating
    # have to find the distance between the two grid points, at each grid point
    distX, distY = compute_dist_grids(latGrid, lonGrid)

    # # this is not how you find the total divergence of the resolved vectors
    # tot_divergence = ((resolve_up * np.cos(beta_mean))/distX) + ((resolve_up * np.sin(beta_mean))/distY) \
    #     + ((resolve_down * np.cos(beta_mean))/distX) + ((resolve_down * np.sin(beta_mean))/distY) \
    #     + ((resolve_left * np.cos(beta_mean))/distX) + ((resolve_left * np.sin(beta_mean))/distY) \
    #     + ((resolve_right * np.cos(beta_mean))/distX) + ((resolve_right * np.sin(beta_mean))/distY)

    tot_divergence = (100*(resolve_right - resolve_left)/(2*distX)) + (100*(resolve_up - resolve_down)/(2*distY))

    # tot_divergence = geo_divergence(latGrid, lonGrid, resolve_up*np.cos(beta_mean), resolve_up*np.sin(beta_mean)) \
    #     + geo_divergence(latGrid, lonGrid, resolve_down*np.cos(beta_mean), resolve_down*np.sin(beta_mean)) \
    #     + geo_divergence(latGrid, lonGrid, resolve_right*np.cos(beta_mean), resolve_right*np.sin(beta_mean)) \
    #     + geo_divergence(latGrid, lonGrid, resolve_left*np.cos(beta_mean), resolve_left*np.sin(beta_mean))

    eq6 = tot_divergence
    eq6_masked = np.copy(eq6)
    eq6_masked[~(m1_mask & m2_mask)] = np.nan
    
    zc_6 = mask_zero_contour(latGrid, lonGrid, tot_divergence)
    zc_6[~(m1_mask & m2_mask)] = np.nan
   
    ########## Getting zero contour line using equation 6
    # zc_6 = mask_zero_contour(latGrid, lonGrid, eq6_masked)

    ############### Method using equation 7 #############################
    eq7 = ((grad_abs_mu_x * mu_x) + (grad_abs_mu_y * mu_y))/(abs_mu)

    ########## Getting zero contour line using equation 7
    eq7_masked = np.copy(eq7)
    eq7_masked[~(m1_mask & m2_mask)] = np.nan
    
    zc_7 = mask_zero_contour(latGrid, lonGrid, eq7_masked)
    
    zc_7 = mask_zero_contour(latGrid, lonGrid, eq7)
    zc_7[~(m1_mask & m2_mask)] = np.nan
    
    # getting cold and warm fronts
    a_gt = geostrophic_thermal_advection(gx, gy, u_wind, v_wind)
    wf_mask = np.double(a_gt > 0)
    cf_mask = np.double(a_gt < 0)
   
    # return {'wf': wf_mask*zc_6, 'cf': cf_mask*zc_6}
    return {'wf': wf_mask*zc_7, 'cf': cf_mask*zc_7}
    # return zc_6, zc_7
    
def simmonds_et_al_2012(latGrid, lonGrid, u_prior, v_prior, u, v):
  # At 850 hPa

  # meridional wind change has to be greater than 2. m/s
  wind_thres = 2.
  mag_diff = np.abs(np.abs(v) - np.abs(v_prior))

  # Condition that satisfies directional change
  cond = (u > 0) & (u_prior > 0) & (((v > 0) & (latGrid < 0)) | ((v < 0) & (latGrid > 0))) & (v * v_prior < 0) & (mag_diff > wind_thres) & (np.abs(latGrid) < 80)
  fronts = np.double(cond)

  ######### MY CODE TO FIND THE FRONTS ########### 
  # # getting the angle of the prior and current time step winds
  # angle_prior = np.arctan2(v_prior, u_prior) * 180 / np.pi
  # angle = np.arctan2(v, u) * 180 / np.pi
  #
  # # getting the northern hemisphere change in wind directions
  # n_ang_prior = (angle_prior > 0) & (angle_prior < 90) & (~np.isnan(angle_prior)) & (latGrid > 0)
  # n_ang = (angle > -90) & (angle < 0) & (~np.isnan(angle)) & (latGrid > 0)
  #
  # # getting the sourthern hemisphere change in wind directions
  # s_ang_prior = (angle_prior > -90) & (angle_prior < 0) & (~np.isnan(angle_prior)) & (latGrid < 0)
  # s_ang = (angle > 0) & (angle < 90) & (~np.isnan(angle)) & (latGrid < 0)
  #
  # fronts_2 = np.double(((n_ang_prior & n_ang) | (s_ang_prior & s_ang)) & (mag_diff > wind_thres))
  ######################

  return {'cf': fronts}

#################### OLD CODE ###################

# input files needed are: 
# topo_file = '/mnt/drive1/jj/cameron/data/MERRA2_101.const_2d_ctm_Nx.00000000.nc4'
# which is the topographic information from merra2

def expand_fronts(fronts, num_pixels):
    
    row_len = fronts.shape[0]
    for i in np.arange(0, row_len):
        ind = np.argwhere(fronts[i,:] == -10)
        if (ind.size == 0):
            continue
        # if (ind.size > 1):
        #     print ind.size

        # ind = ind[0,0]
        max_ind = np.nanmax(ind)
        min_ind = np.nanmin(ind)

        if (min_ind == 0):
            for j in np.arange(max_ind, max_ind+num_pixels):
                fronts[i, j+1] = -10
        elif(max_ind == fronts.shape[1]):
            for j in np.arange(min_ind-num_pixels, min_ind):
                fronts[i, j] = -10
        else:
            for j in np.arange(min_ind-num_pixels, max_ind+num_pixels+1):
                if (j < 0):
                    continue
                if (j >= fronts.shape[1]):
                    continue
                fronts[i, j] = -10

    return fronts

def catherine_fronts_for_date(latGrid, lonGrid, year, month, day, hour):
    #################### CATHERINE FRONTS ###############
    # get list of files in the folder
    c_folder = '/mnt/drive1/processed_data/MERRA2fronts/%04d%02d/'%(year, month)

    selectDate = '%04d%02d%02d'%(year, month, hour)

    wf = np.zeros(latGrid.shape)
    cf = np.zeros(latGrid.shape)

    search_string = os.path.join(c_folder, '*%s_%02d*.ncdf'%(selectDate, hour))
    c_files = glob.glob(search_string)
    
    if (not c_files):
        print ("Catherine's front file not found.")
        return wf, cf
    
    cf_lon = []
    cf_lat = []
    wf_lat = []
    wf_lon = []
    for c_file in c_files:
      dataset = Dataset(c_file)
      dataset.set_auto_mask(False)
      c_lat = dataset.variables['latitude'][:]
      c_lon = dataset.variables['longitude'][:]
      c_slp = dataset.variables['MERRA2SLP'][:]
      c_info = dataset.variables['storm_info'][:]

      # CF_combined, CF_simmonds850, CF_hewson1km
      # c_cf = dataset.variables['CF_combined'][:]
      # c_cf = dataset.variables['CF_simmonds850'][:]
      c_cf = dataset.variables['CF_hewson1km'][:]
      c_cf_lon = c_cf[:,0]
      c_cf_lat = c_cf[:,1]

      cf_lat.extend(c_cf_lat.tolist())
      cf_lon.extend(c_cf_lon.tolist())

      # WF_Hewson850, WF_Hewson1Km, WF_HewsonWB
      c_wf = dataset.variables['WF_Hewson1km'][:] 
      # c_wf = dataset.variables['WF_Hewson850'][:] 
      c_wf_lon = c_wf[:,0]
      c_wf_lat = c_wf[:,1]
      
      wf_lat.extend(c_wf_lat.tolist())
      wf_lon.extend(c_wf_lon.tolist())

      dataset.close()

    wf_lat = np.asarray(wf_lat)
    wf_lon = np.asarray(wf_lon)
    
    cf_lat = np.asarray(cf_lat)
    cf_lon = np.asarray(cf_lon)

    lat_edges = np.asarray(latGrid[:,0])
    lon_edges = np.asarray(lonGrid[0,:])

    lat_div = lat_edges[1] - lat_edges[0]
    lon_div = lon_edges[1] - lon_edges[0]

    lat_edges = lat_edges - lat_div/2.
    lat_edges = np.append(lat_edges, lat_edges[-1]+lat_div/2.)

    lon_edges = lon_edges - lon_div/2.
    lon_edges = np.append(lon_edges, lon_edges[-1]+lon_div/2.)
    
    wf, _, _ = np.histogram2d(wf_lat, wf_lon, bins=(lat_edges, lon_edges))
    wf = np.double(wf > 0)
    
    cf, _, _ = np.histogram2d(cf_lat, cf_lon, bins=(lat_edges, lon_edges))
    cf = np.double(cf > 0)
    
    return wf, cf
        

'''
def detect_fronts_catherine(latGrid, lonGrid, selectLat, selectLon, selectDate, selectHH):
    """ Code to read in catherine fronts given lat, lon and date"""
    #################### CATHERINE FRONTS ###############
   
    selectYY = int(selectDate[0:4])
    selectMM = int(selectDate[4:6]) 
    selectDD = int(selectDate[6:8]) 

    print (selectYY, selectMM, selectDD, latGrid.shape)
    c_fronts = np.zeros(latGrid.shape)

    # get list of files in the folder
    c_folder = '/mnt/drive1/processed_data/MERRA2fronts/%04d%02d/'%(selectYY, selectMM)

    c_file = ''
    for dirpath, dirname, filenames in os.walk(c_folder):
        for filename in filenames:
            if (filename.endswith(".ncdf")):
                fs = filename.split("_")
                c_date = int(fs[1])
                c_hr = float(fs[2])
                c_lat = float(fs[3])
                c_lon = float(fs[4])
                if (c_lon < 0): 
                    c_lon = c_lon + 360.

                c_lat_str = '%.2f'%(c_lat)
                c_lon_str = '%.2f'%(c_lon)

                if ((c_date == int(selectDate)) & (c_hr == selectHH) & (c_lat_str == selectLat) & (c_lon_str == selectLon)):
                    c_file = os.path.join(dirpath, filename)
                    break
  
    if (not c_file):
        print ("Catherine's front file not found.")
        return {'fronts':c_fronts, 'cf_lon':[], 'cf_lat':[],'wf_lon':[],'wf_lat':[]}

    dataset = Dataset(c_file)
    c_lat = dataset.variables['latitude'][:]
    c_lon = dataset.variables['longitude'][:]
    c_slp = dataset.variables['MERRA2SLP'][:]
    c_info = dataset.variables['storm_info'][:]

    # CF_combined, CF_simmonds850, CF_hewson1km
    c_cf = dataset.variables['CF_combined'][:]
    # c_cf = dataset.variables['CF_simmonds850'][:]
    c_cf_lon = c_cf[:,0]
    c_cf_lon[c_cf_lon < 0] = c_cf_lon[c_cf_lon < 0] + 360.
    c_cf_lat = c_cf[:,1]
    # WF_Hewson850, WF_Hewson1Km, WF_HewsonWB
    c_wf = dataset.variables['WF_Hewson1km'][:] 
    # c_wf = dataset.variables['WF_Hewson850'][:] 
    c_wf_lon = c_wf[:,0]
    c_wf_lon[c_wf_lon < 0] = c_wf_lon[c_wf_lon < 0] + 360.
    c_wf_lat = c_wf[:,1]


    f_sim = dataset.variables['CF_simmonds850'][:]
    f_com = c_cf
    f_hew = c_wf

    dataset.close()

    # overlay catherine fronts on the input grid
    if (not (c_cf_lon.size == 0)):
        for i_lon, i_lat in zip(c_cf_lon, c_cf_lat):
            dist = compute_dist_from_cdt(latGrid, lonGrid, i_lat, i_lon)
            ind = np.nanargmin(dist)
            ind_x, ind_y = np.unravel_index(ind,latGrid.shape)
            c_fronts[ind_x, ind_y] = -10
    
    if (not (c_wf_lon.size == 0)): 
        for i_lon, i_lat in zip(c_wf_lon, c_wf_lat):
            dist = compute_dist_from_cdt(latGrid, lonGrid, i_lat, i_lon)
            ind = np.nanargmin(dist)
            ind_x, ind_y = np.unravel_index(ind,latGrid.shape)
            c_fronts[ind_x, ind_y] = 10

    return {'fronts':c_fronts, 'cf_lon':c_cf_lon, 'cf_lat':c_cf_lat,'wf_lon':c_wf_lon,'wf_lat':c_wf_lat}
'''
# computing the distance given the lat and lon grid
def compute_dist_from_cdt(lat, lon, centerLat, centerLon):

    # km per degree value
    mean_radius_earth = 6371

    # Haversine function to find distances between lat and lon
    lat1 = lat * math.pi / 180; 
    lat2 = centerLat * math.pi / 180; 
    
    lon1 = lon * math.pi / 180; 
    lon2 = centerLon * math.pi / 180; 
    
    # convert dx and dy to radians as well
    dLat = lat1 - lat2
    dLon = lon1 - lon2

    R = mean_radius_earth

    # computing distance in X direction
    a = np.sin(dLat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2)**2
    c = np.arctan2(np.sqrt(a), np.sqrt(1-a)); 
    dist = 2 * R * c; 

    return dist
   
def compute_center_mask(lat, lon, centerLat, centerLon):
    ''' not used right now, was added here to mimic jimmy's matlab code of applying a center mask '''

    dist = compute_dist_from_cdt(lat, lon, centerLat, centerLon)
    rCenter, cCenter = np.unravel_index(dist.argmin(), dist.shape)

    out = np.zeros(lat.shape)

    # dist = compute_dist_from_cdt(lat, lon, centerLat, centerLon)
    # x = dist
    # y = dist
    # x[0:rCenter,:] = x[0:rCenter,:] * -1
    # y[:,0:cCenter] = y[:,0:cCenter] * -1
    # xdLeft = -18 * 24
    # xdRight = 45 * 24
    # ydTop = 5 * 24
    # ydBot = -45 * 24
    # x = (x > xdLeft) & (x < xdRight)
    # y = (y > ydBot) & (y < ydTop)

    xdLeft = 8 
    xdRight = 11
    ydTop = 2 
    ydBot = 16
    
    numR, numC = lat.shape 

    rMin = max(0,rCenter-ydBot)
    cMin = max(0,cCenter-xdLeft)
    
    rMax = min(numR,rCenter+ydTop)
    cMax = min(numC,cCenter+xdRight)
    

    out[rMin:rMax,cMin:cMax] = 1

    return (out == 1)


def norm(x,y):
    return np.sqrt(x**2 + y**2)

def smooth_grid(inGrid, iter=1, center_weight=4):
    
    outGrid = np.copy(inGrid)
    shift_len = 1
    
    for iter_loop in range(iter):

      up_shift = np.pad(outGrid, ((shift_len, 0), (0, 0)), mode='constant', constant_values=np.nan)[:-shift_len, :]
      down_shift = np.pad(outGrid, ((0, shift_len), (0, 0)), mode='constant', constant_values=np.nan)[shift_len:, :]
      right_shift = np.roll(outGrid, 1, axis=1)
      left_shift = np.roll(outGrid, -1, axis=1)
      # right_shift = np.pad(outGrid, ((0, 0), (shift_len, 0)), mode='constant', constant_values=np.nan)[:, :-shift_len]
      # left_shift = np.pad(outGrid, ((0, 0), (0, shift_len)), mode='constant', constant_values=np.nan)[:, shift_len:]
     
      cnts = np.double(~np.isnan(right_shift)) + np.double(~np.isnan(left_shift)) + \
          np.double(~np.isnan(up_shift)) + np.double(~np.isnan(down_shift)) + np.double(~np.isnan(outGrid))*center_weight

      # outGrid_num = np.nansum(np.dstack((outGrid*center_weight, right_shift, left_shift, up_shift, down_shift)), 2)
      # outGrid = outGrid_num/cnts

      outGrid_num = np.nansum(np.dstack((outGrid*center_weight, right_shift, left_shift, up_shift, down_shift)), 2)
      cnt_ind = ~(cnts == 0)
      outGrid[cnt_ind] = outGrid_num[cnt_ind]/cnts[cnt_ind]
      
    return outGrid

def mask_zero_contour(latGrid, lonGrid, data):
    
    plt.figure() 
    cs = plt.contour(latGrid, lonGrid, data, levels=[0]) 
    plt.close()
    zc = np.zeros(data.shape)

    cdt = np.asarray([])
    for line in cs.collections[0].get_paths():
        cdt_line = np.asarray(line.vertices)
        if (cdt.size == 0):
          cdt = cdt_line
        else:
          cdt = np.vstack((cdt, cdt_line))

    lat_edges = np.asarray(latGrid[:,0])
    lon_edges = np.asarray(lonGrid[0,:])

    lat_div = lat_edges[1] - lat_edges[0]
    lon_div = lon_edges[1] - lon_edges[0]

    lat_edges = lat_edges - lat_div/2.
    lat_edges = np.append(lat_edges, lat_edges[-1]+lat_div/2.)

    lon_edges = lon_edges - lon_div/2.
    lon_edges = np.append(lon_edges, lon_edges[-1]+lon_div/2.)
    
    H, _, _ = np.histogram2d(cdt[:, 0], cdt[:, 1], bins=(lat_edges, lon_edges))
    out_array = np.double(H > 0)

    return out_array

def mountain_mask(inLat, inLon):

    topo_file = '/mnt/drive1/jj/cameron/data/MERRA2_101.const_2d_ctm_Nx.00000000.nc4'

    # read in the topographic data
    dataset = Dataset(topo_file)

    # dsearchn the lat and lon from the grid
    lat = dataset.variables['lat'][:]
    lon = dataset.variables['lon'][:]
    phis = dataset.variables['PHIS'][:]
    phis = phis[1,:,:]/9.8

    lonGrid, latGrid = np.meshgrid(lon, lat)

    ul_lon = inLon[0,0]
    ul_lat = inLat[0,0]
    
    lr_lon = inLon[-1,-1]
    lr_lat = inLat[-1,-1]

    ul_ind = np.argwhere((lonGrid == ul_lon) & (latGrid == ul_lat))
    lr_ind = np.argwhere((lonGrid == lr_lon) & (latGrid == lr_lat))
    
    topo = phis[ul_ind[0][0]:lr_ind[0][0]+1, ul_ind[0][1]:lr_ind[0][1]+1]

    return topo
    
    # create the mask for a threhold height as mountains

    # return the mask 
    pass

def geostrophic_thermal_advection(gx,gy,u,v):
    return -(u * gx + v * gy)

def auto_derivative(data):
    return np.gradient(data)

def show(latGrid, lonGrid, data):

    plt.figure()

    ll_lon = np.nanmin(lonGrid)
    ll_lat = np.nanmin(latGrid)
    ur_lon = np.nanmax(lonGrid)
    ur_lat = np.nanmax(latGrid)

    cmap = mpl.cm.get_cmap('jet',16);

    m = Basemap(projection='lcc',resolution='l',llcrnrlon=ll_lon,llcrnrlat=ll_lat,urcrnrlon=ur_lon,urcrnrlat=ur_lat,lat_1=ll_lat,lat_2=ur_lat,lat_0=50,lon_0=-107.)
    m.drawmapboundary()
    m.drawcoastlines()
    x, y = m(lonGrid, latGrid)
    vmin_val = np.nanmin(data)
    vmax_val = np.nanmax(data)
    m.pcolormesh(x, y, data,vmin=vmin_val,vmax=vmax_val,cmap=cmap)
    plt.colorbar()
    plt.show()


def distance_in_deg(lon1, lat1, lon2, lat2):

    dist = ((lon1-lon2)**2 + (lat1-lat2)**2)**.5

    return dist

# getting the gradient given lat, lon and data
def geo_gradient(lat, lon, data):

    # compute the gradient of data, in dx, and dy
    dx, dy = auto_derivative(data)

    # get the distance matrix for the given lat and lon
    distX, distY = compute_dist_grids(lat, lon)

    # # compute the d(data)/dx and d(data)/dy
    dx = dx / distX 
    dy = dy / distY 

    # converting from per km to per 100 km 
    dx = 100 * dx
    dy = 100 * dy

    return dx, dy 

def geo_divergence(lat, lon, x, y):

    x_dx, x_dy = geo_gradient(lat, lon, x)
    y_dx, y_dy = geo_gradient(lat, lon, y)

    div = x_dx + y_dy

    return div

# computing the distance given the lat and lon grid
def compute_dist_grids(lat, lon):

    # km per degree value
    mean_radius_earth = 6371

    # compute the dx and dy using lat 
    dxLat, dyLat = np.gradient(lat)
    dxLon, dyLon = np.gradient(lon)

    # Haversine function to find distances between lat and lon
    lat1_x = lat * math.pi / 180; 
    lat2_x = (lat + dxLat) * math.pi / 180; 
    
    lat1_y = lat * math.pi / 180; 
    lat2_y = (lat + dyLat) * math.pi / 180; 

    lon1_x = lon * math.pi / 180; 
    lon2_x = (lon + dxLon) * math.pi / 180; 
    
    lon1_y = lon * math.pi / 180; 
    lon2_y = (lon + dyLon) * math.pi / 180; 

    # convert dx and dy to radians as well
    dLat_x = dxLat * math.pi / 180; 
    dLat_y = dyLat * math.pi / 180; 

    dLon_x = dxLon * math.pi / 180; 
    dLon_y = dyLon * math.pi / 180; 

    R = mean_radius_earth

    # computing distance in X direction
    a_x = np.sin(dLat_x/2)**2 + np.cos(lat1_x) * np.cos(lat2_x) * np.sin(dLon_x/2)**2
    c_x = np.arctan2(np.sqrt(a_x), np.sqrt(1-a_x)); 
    # c_x = np.arcsin(np.sqrt(a_x))
    distX = 2 * R * c_x; 
    
    # computing distance in Y direction
    a_y = np.sin(dLat_y/2)**2 + np.cos(lat1_y) * np.cos(lat2_y) * np.sin(dLon_y/2)**2
    c_y = np.arctan2(np.sqrt(a_y), np.sqrt(1-a_y)); 
    # c_y = np.arcsin(np.sqrt(a_y))
    distY = 2 * R * c_y; 

    return distX, distY


'''
def detect_fronts(latGrid, lonGrid, data, u850, v850, centerLat, centerLon):

    # creating empty fronts data array
    fronts = np.zeros(data.shape) * np.nan
    fronts_2 = np.zeros(data.shape) * np.nan
    fronts_3 = np.zeros(data.shape) * np.nan
    out_theta_e = np.zeros(data.shape) * np.nan
    out_t850 = np.zeros(data.shape) * np.nan
    out_center_mask = np.zeros(data.shape) * np.nan
    out_topo = np.zeros(data.shape) * np.nan

    # computing first derivative
    gx, gy = geo_gradient(latGrid, lonGrid, data)
    gNorm = norm(gx, gy) 

    # computing the 2nd derivative using the first derivative
    gx_gNorm, gy_gNorm = geo_gradient(latGrid, lonGrid, gNorm)
    gNorm_gNorm = norm(gx_gNorm, gy_gNorm)

    # compute distance grid
    distX, distY = compute_dist_grids(latGrid, lonGrid)
    dist_avg = np.sqrt(distX**2 + distY**2)

    # sign test
    sign_test = (gx + gx_gNorm) + (gy + gy_gNorm)
    sign_test[sign_test > 0] = 1
    sign_test[sign_test < 0] = -1

    # m1 (Hewson 1998)
    m1_eq_10 = gNorm_gNorm * sign_test

    # or m1 computed using this 
    m1 = -1 * (gx_gNorm * gx/gNorm + gy_gNorm * gy/gNorm)

    # m2 (Hewson 1998) 
    mconst = 1/math.sqrt(2)
    m2 = gNorm + mconst * dist_avg * gNorm_gNorm / 100

    # computing TFP, as per Sebastian paper
    tfp = -1 * (gx_gNorm * gx/gNorm + gy_gNorm * gy/gNorm)
    gx_tfp, gy_tfp = geo_gradient(latGrid, lonGrid, tfp)
    gNorm_tfp = norm(gx_tfp, gy_tfp)

    # get zero contour line 
    tfp_filtered = np.copy(tfp)
    tfp_filtered[gNorm < 3] = np.nan
    cs = plt.contour(latGrid, lonGrid, tfp_filtered,levels=[0]) 
    zc = np.zeros(tfp_filtered.shape)
    for line in cs.collections[0].get_paths():
        for line_lat, line_lon in line.vertices:
            dist = compute_dist_from_cdt(latGrid, lonGrid, line_lat, line_lon)
            ind = np.nanargmin(dist)
            ind_x, ind_y = np.unravel_index(ind,latGrid.shape)
            zc[ind_x, ind_y] = 1
    
    # getting cold and warm fronts (Sebastian Schemm et al 2015)
    vf = u850*gx_tfp/gNorm_tfp + v850*gy_tfp/gNorm_tfp
    vf_mask = np.zeros(vf.shape)
    vf_mask[vf > 0] = 1
    vf_mask[vf < 0] = -1

    # getting divergence as per schem et al 2015
    div = geo_divergence(latGrid, lonGrid, gx_gNorm, gy_gNorm)
    div_mask = div < 0
    
    # # getting cold and warm fronts (Hewson 1998)
    # vf = u850*gx_gNorm/gNorm_gNorm + v850*gy_gNorm/gNorm_gNorm
    # vf_mask = np.zeros(vf.shape)
    # vf_mask[vf > 0] = 1 # warm fronts
    # vf_mask[vf < 0] = -1 # cold fronts

    # # getting cold and warm fronts (My Method)
    # # have to change back to the old method
    # vf = u850*gx/gNorm + v850*gy/gNorm
    # vf_x = u850 * gx
    # vf_y = v850 * gy
    # vf_x_norm = vf_x/gNorm
    # vf_y_norm = vf_y/gNorm
    # vf_mask = np.zeros(vf.shape)
    # vf_mask[vf_x_norm > vf_y_norm] = -1 # cold fronts
    # vf_mask[vf_y_norm > vf_x_norm] = 1 # warm fronts

    # # masking out the data
    # k1 = 0.45 #0.33 #/100/100 # converting from deg/100km/100km to deg/km/km
    # k2 = 2 #1.49 #/100

    k1 = 0.33 #0.33 #/100/100 # converting from deg/100km/100km to deg/km/km
    k2 = 1.49 #1.49 #/100

    m1_mask = m1 > k1
    m2_mask = m2 > k2

    # additional condition to exclude priori regions of weak thermal graidents form the data
    # m3_mask = gNorm > 4
    m3_mask = gNorm > 3 

    # additional condition to remove quasi-stationary fronts from mobile fronts
    m4_mask = (vf > 3)  | (vf < -3)

    # center masking
    dist_from_center = compute_dist_from_cdt(latGrid, lonGrid, centerLat, centerLon)
    # center_mask = compute_center_mask(latGrid, lonGrid, centerLat, centerLon)
    center_mask = dist_from_center < 2000
    out_center_mask = dist_from_center
    
    # topographic masking  
    topo = get_mountain_mask(latGrid, lonGrid)
    topo_mask = topo <= 500
    out_topo = topo
 
    # combining all the masks
    combined_mask = m1_mask & m2_mask & m3_mask & m4_mask & center_mask & topo_mask

    # filtered_mask = filter_connected(combined_mask * 1 * vf_mask)
    filtered_mask = np.copy(combined_mask)

    final_mask = (filtered_mask * 1) * vf_mask * 10

    # saving the final_mask for the fronts
    fronts = final_mask


    # a different font masking criteria as per Sebasitian's paper
    combined_mask_2 = m1_mask & m2_mask & (gNorm > 4) & m4_mask & center_mask & topo_mask
    filtered_mask_2 = np.copy(combined_mask_2)
    final_mask_2 = (filtered_mask_2 * 1) * vf_mask * 10
    fronts_2 = final_mask_2
   
    # method for Sebastian masking
    combined_mask_3 = (zc == 1) & div_mask & center_mask & topo_mask & m4_mask
    final_mask_pre_filter = (combined_mask_3 * 1) * vf_mask * 10

    # final_mask_3 = np.copy(final_mask_pre_filter)
    # final_mask_3 = filter_connected(final_mask_pre_filter)

    fronts_2 = final_mask_pre_filter
    final_mask_3 = filter_fronts(latGrid, lonGrid, centerLat, centerLon, final_mask_pre_filter)
    fronts_3 = final_mask_3

    out_theta_e = data

    return {'fronts':fronts_3,'fronts_1': fronts, 'fronts_2':fronts_2,'fronts_3':fronts_3,'theta_e':out_theta_e,'center_mask':out_center_mask,'zc':zc,'tfp':tfp,'topo':out_topo}
    
def filter_fronts(latGrid, lonGrid, centerLat, centerLon, in_mask):
    # """ this function requires the input mask to be 10 for warm fronts, -10 for cold fronts and 0 for no front """

    # first flag everything below and right as cold front
    intermediate_mask = filter_by_center(latGrid, lonGrid, centerLat, centerLon, in_mask)

    # then flag everything connected by more than 3 grid points, as the majority of the flagging
    final_mask = filter_connected(intermediate_mask)

    return final_mask

def filter_connected(in_mask):
    
    out_array = np.zeros(in_mask.shape)
    s = generate_binary_structure(2,2)

    mask = (in_mask)*1
    # labeled_array, num_features = label(mask)
    labeled_array, num_features = label(mask,structure=s) # diagonal connection

    for i in np.arange(1,num_features):
        temp = in_mask[labeled_array == i]
        if (temp.size > 3):
            if (np.nanmean(temp) < 0):
                out_array[labeled_array == i] = -10
            elif (np.nanmean(temp) >= 0):
                out_array[labeled_array == i] = 10

    return out_array

def filter_by_center(latGrid, lonGrid, centerLat, centerLon, in_mask): 
        # flagging any front that is below the center as cold front
        #
        # find the low pressure center x and y 
        # then anything below, and right of the center, flag it as cold front, if connected object then make entire object as cold front
        #
        # this function has to be run before filter_connected, because this flags all the values below the center as cold fronts, so grouping connected should be done after
    
    # compute distance from the center
    dist = compute_dist_from_cdt(latGrid, lonGrid, centerLat, centerLon)

    # get index of the minimum distance value
    ind = np.nanargmin(dist)
    ind_x, ind_y = np.unravel_index(ind,latGrid.shape)

    # change all the cold fronts below and right of center as cold fronts
    for r in np.arange(0,ind_x):
        for c in np.arange(ind_y, lonGrid.shape[1]):
            if (in_mask[r,c] == 10):
                in_mask[r,c] = -10
        
    return in_mask

def group_warm_cold_fronts(in_mask):

    # mask = (in_mask < 0)*1
    # # labeled_array, num_features = label(mask)
    # labeled_array, num_features = label(mask,structure=s) # diagonal connection

    # for i in np.arange(1,num_features):
    #     temp = labeled_array[labeled_array == i]
    #     if (temp.size > 3):
    #         out_array[labeled_array == i] = 1

    out_array = in_mask

    return out_array
'''
