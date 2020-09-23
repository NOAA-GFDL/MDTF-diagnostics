'''
Front Detection Algorithm

Adopted from Naud et al., 2016, based on Hewson at 1km, and Simmonds et al., 2012

Created by: Jeyavinoth Jeyaratnam
Created on: March 1st, 2019

Last Modified: Jan 22nd, 2020

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
import cartopy

# --------------------- PLOTTING CODES -----------------------
# should be deleted in final implementation 
# these are test codes to plot stuff
def plot(data, cmap='jet', equal=False,  **kwargs):
    '''Temporary code to plot figures quicky.'''
    plt.figure()

    if (equal):
      datamax = np.nanmax(np.abs(data))
      plt.pcolormesh(data, cmap='bwr', vmin=-datamax, vmax=datamax, **kwargs)
    else:
      plt.pcolormesh(data, cmap=cmap, **kwargs)
    plt.colorbar()
    plt.draw()
    plt.show(block=False)

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

# --------------------- MAIN PART OF THE CODE -----------------------------------
# --------------------- NECESSARY FUNCTIONS FOR FRONT DETECTION -----------------
def four_corner_shift(arr, shift_len=1):
    '''Shifts an array by the shift_len in all 4 directions'''
    up = np.pad(arr, ((shift_len, 0), (0, 0)), mode='constant', constant_values=np.nan)[:-shift_len, :]
    down = np.pad(arr, ((0, shift_len), (0, 0)), mode='constant', constant_values=np.nan)[shift_len:, :]
    left = np.roll(arr, -1, axis=1)
    right = np.roll(arr, 1, axis=1)

    return up, down, left, right

def theta_from_temp_pres(temp, pres):
    '''Computing theta given temperature and pressure values'''
    return temp * (1000./pres)**(2/7)

def hewson_1998(latGrid, lonGrid, theta, hgt_agt):
    '''Computing the fronts based on Hewson 1998 methodology.'''
    gx, gy = geo_gradient(latGrid, lonGrid, theta)
    gNorm = norm(gx, gy)
    mux, muy = geo_gradient(latGrid, lonGrid, gNorm)

    abs_mu = norm(mux, muy)
    grad_abs_mux, grad_abs_muy = geo_gradient(latGrid, lonGrid, abs_mu)

    product = (mux * gx + muy*gy)
    product_smooth = smooth_grid(product, iter=1, center_weight=1)
    m1 = -1*product_smooth/gNorm
    m2 = gNorm + (1/np.sqrt(2)) * 100 * 1000 * abs_mu

    k1 = 0.33 * 1e-10
    k2 = 1.49 * 1e-5

    m1_mask = m1 > k1
    m2_mask = m2 > k2
    
    # S five point mean
    mu_mag = np.copy(abs_mu)
    
    # getting the angle and computing betamean
    mu_ang = np.empty(abs_mu.shape)*np.nan
    mu_ang = np.arctan2(muy, mux)
    mu_ang[(mux == 0) & (muy > 0)] = np.pi/2.
    mu_ang[(mux == 0) & (muy < 0)] = 3*np.pi/2.
    mu_ang[(muy == 0)] = 0.
    
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

    betamean = np.arctan2(sumq, sump) * .5
    
    ## Resolve the four outer vectors into the positive s_hat [D_mean, B_mean]
    # shifting the mux and muy to get the 4 corners
    # this overlaps the neighbors to allow us to vector caculate
    up_mux, down_mux, left_mux, right_mux = four_corner_shift(mux, shift_len=1)
    up_muy, down_muy, left_muy, right_muy = four_corner_shift(muy, shift_len=1)

    up_lat, down_lat, left_lat, right_lat = four_corner_shift(latGrid, shift_len=1)
    up_lon, down_lon, left_lon, right_lon = four_corner_shift(lonGrid, shift_len=1)
    left_lon[:, -1] = left_lon[:, -1] + 360
    right_lon[:, 0] = right_lon[:, 0] - 360

    dy = dist_between_grids(up_lat, up_lon, down_lat, down_lon)
    dx = dist_between_grids(left_lat, left_lon, right_lat, right_lon)

    # computing the primes should be done as follows
    # down - up --> dy
    # left - right  --> dx
    down_prime = down_mux*np.cos(betamean) + down_muy*np.sin(betamean)
    up_prime = up_mux*np.cos(betamean) + up_muy*np.sin(betamean)

    left_prime = left_mux*np.cos(betamean) + left_muy*np.sin(betamean)
    right_prime = right_mux*np.cos(betamean) + right_muy*np.sin(betamean)

    tot_div = (down_prime - up_prime)*np.sin(betamean)/dy + (left_prime - right_prime)*np.cos(betamean)/dx

    eq6 = tot_div
    zc_6 = mask_zero_contour(latGrid, lonGrid, eq6)
    zc_6[~(m1_mask & m2_mask)] = 0.

    # ############### Method using equation 7 #############################
    eq7 = ((grad_abs_mux * mux) + (grad_abs_muy * muy))/(abs_mu)

    ########## Getting zero contour line using equation 7
    eq7_masked = np.copy(eq7)
    eq7_masked[~(m1_mask & m2_mask)] = np.nan

    zc_7 = mask_zero_contour(latGrid, lonGrid, eq7_masked)

    zc_7 = mask_zero_contour(latGrid, lonGrid, eq7)
    zc_7[~(m1_mask & m2_mask)] = np.nan


    ######### getting cold and warm fronts
    # first, have to compute geostrophic winds at 850 hPa

    grad_x, grad_y = geo_gradient(latGrid, lonGrid, hgt_agt)
    rot_param = 4.*np.pi/24./3600.  * np.sin(latGrid *np.pi/180.)

    ug = -(9.81/rot_param)*grad_y
    vg = (9.81/rot_param)*grad_x

    ug = smooth_grid(ug, iter=10, center_weight=4.)
    vg = smooth_grid(vg, iter=10, center_weight=4.)

    gta = -1*(ug*gx + vg*gy)
     
    # warm and cold front masks
    wf_mask = np.double(gta > 0)
    cf_mask = np.double(gta < 0)


    return {'wf': wf_mask*zc_6, 'cf': cf_mask*zc_6, 'temp_grad': gNorm}, np.double(gta)
    # return {'wf': zc_6, 'cf': zc_6}
    # return {'wf': wf_mask*zc_7, 'cf': cf_mask*zc_7}, np.double(eq7)
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

def compute_dist_from_cdt(lat, lon, centerLat, centerLon):
    '''computing the distance given the lat and lon grid'''

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
    
    # if lat is decreasing, we have to flip the lat_edges
    # also have to flip the output array
    flip_lat_dim = False
    if (lat_div < 0):
      lat_edges = np.flip(lat_edges)
      lat_div =  np.abs(lat_div)
      flip_lat_dim = True

    lat_edges = lat_edges - lat_div/2.
    lat_edges = np.append(lat_edges, lat_edges[-1]+lat_div/2.)

    lon_edges = lon_edges - lon_div/2.
    lon_edges = np.append(lon_edges, lon_edges[-1]+lon_div/2.)
    
    H, _, _ = np.histogram2d(cdt[:, 0], cdt[:, 1], bins=(lat_edges, lon_edges))
    out_array = np.double(H > 0)

    if (flip_lat_dim):
      out_array = np.flip(out_array, axis=0)

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
    
    # TODO: complete this code

    return topo
    
    # create the mask for a threhold height as mountains

    # return the mask 
    pass

def geostrophic_thermal_advection(gx,gy,u,v):
    return -(u * gx + v * gy)

def distance_in_deg(lon1, lat1, lon2, lat2):

    # dist = ((lon1-lon2)**2 + (lat1-lat2)**2)**.5

    # here we have to take care of round globe
    # logic here is that 
    # for one of the lon, in this case lon1, we shift all the values by +/- 360
    # then we compute the distances for the original values and the shifted lon values
    # then we pick the minimum distance as the value we must consider as our closest distance value
    dist_all = np.empty(lon1.shape)
    dist_all = np.repeat(dist_all[np.newaxis, :], 3, axis=0)
    tmp_lon = lon1
    dist_all[0,:] = ((tmp_lon-lon2)**2 + (lat1-lat2)**2)**.5
    tmp_lon = lon1 - 360
    dist_all[1,:] = ((tmp_lon-lon2)**2 + (lat1-lat2)**2)**.5
    tmp_lon = lon1 + 360
    dist_all[2,:] = ((tmp_lon-lon2)**2 + (lat1-lat2)**2)**.5

    dist = np.nanmin(dist_all, axis=0)

    return dist

def auto_derivative(data):

    # manually computing the derivative
    shift_len = 1
    data_right = np.pad(data, ((0, 0), (shift_len, 0)), mode='wrap')[:, :-shift_len]
    # shifting down mean technically shifting up, cuz latGrid is increasing from 1 to 0
    data_up = np.pad(data, ((shift_len, 0), (0, 0)), mode='constant', constant_values=np.nan)[:-shift_len, :]
    dx = (data - data_right)
    dy = (data - data_up)

    # # using the built in function to find the derivative
    # dy, dx = np.gradient(data)

    return dx, dy

def geo_gradient_old(lat, lon, data):
    '''getting the gradient given lat, lon and data'''

    # compute the gradient of data, in dx, and dy
    dx, dy = auto_derivative(data)

    # get the distance matrix for the given lat and lon
    distX, distY = compute_dist_grids(lat, lon)

    # # compute the d(data)/dx and d(data)/dy
    dx_distX = dx / distX
    dy_distY = dy / distY 

    # converting from per km to per 100 km 
    dx = dx_distX
    dy = dy_distY

    return dx, dy 

def geo_divergence(lat, lon, x, y):

    x_dx, x_dy = geo_gradient(lat, lon, x)
    y_dx, y_dy = geo_gradient(lat, lon, y)

    div = x_dx + y_dy

    return div

def dist_between_grids(lat0, lon0, lat1, lon1):
    ''' Dimensions here are lon x lat'''

    # R_earth = 6378206.4
    # cosc = np.sin(lat0*np.pi/180.) * np.sin(lat1*np.pi/180.)  + np.cos(lat0*np.pi/180.) * np.cos(lat1*np.pi/180.) * np.cos(np.pi/180.*(lon1 - lon0))
    # cosc[cosc < -1] = -1
    # cosc[cosc > 1] = 1
    # dist = np.arccos(cosc) * R_earth
   
    # in meters
    dist = ((lat0 - lat1)**2 + (lon0-lon1)**2)**.5 * 111.12 * np.cos(lat0*np.pi/180.) * 1000.

    # dist = compute_dist_from_cdt(lat0, lon0, lat1, lon1)*1000.

    return dist

def dist_transect(lat0, lon0, lat1, lon1):

    dist = dist_between_grids(lat0, lon0, lat1, lon1)/1000.

    return dist

def geo_gradient(lat, lon, data): 
    
  # shift data forward
  data_up, data_down, data_left, data_right = four_corner_shift(data)
  lat_up, lat_down, lat_left, lat_right = four_corner_shift(lat)
  lon_up, lon_down, lon_left, lon_right = four_corner_shift(lon)
  lon_left[:, -1] = lon_left[:, -1] + 360
  lon_right[:, 0] = lon_right[:, 0] - 360

  # lat_shift_distance
  dy1 = dist_between_grids(lat_down, lon_down, lat, lon)
  dy2 = dist_between_grids(lat_up, lon_up, lat, lon)
  dy1_data = (data_down - data)
  dy2_data = (data - data_up)
  dy = (dy2_data + dy1_data) / (dy1 + dy2)
  
  dx1 = dist_between_grids(lat_left, lon_left, lat, lon)
  dx2 = dist_between_grids(lat, lon, lat_right, lon_right)
  dx1_data = (data_left - data)
  dx2_data = (data - data_right)
  dx = (dx2_data + dx1_data) / (dx1 + dx2)

  return dx, dy

def compute_dist_grids(lat, lon):
    '''computing the distance given the lat and lon grid'''

    # km per degree value
    mean_radius_earth = 6371

    # compute the dx and dy using lat 
    dxLat, dyLat = auto_derivative(lat)
    dxLon, dyLon = auto_derivative(lon)

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

    return distX*1000., distY*1000.

def clean_up_fronts(wf, cf, lat, lon): 
  ##############################################################
  ###### Group Fronts and get rid of small clusters ############
  ##############################################################

  # Grouping clusters of fronts
  s = generate_binary_structure(2,2)
  w_label, w_num = label(wf, structure=s)
  c_label, c_num = label(cf, structure=s)

  # getting the mean lat and lon of the clusters
  w_lat = np.empty((w_num+1,))*np.nan
  w_lon = np.empty((w_num+1,))*np.nan
  
  c_lat = np.empty((c_num+1,))*np.nan
  c_lon = np.empty((c_num+1,))*np.nan

  # keeping only clusters with 3 or more 
  # also saving the mean lat and lon of the cluster
  for i_w in range(1, w_num+1):
    ind = (w_label == i_w)
    x_ind, y_ind = np.where(ind)
    if (len(x_ind) < 3):
      wf[w_label == i_w] = 0.
      w_label[w_label == i_w] = 0.
    else: 
      w_lat[i_w] = np.nanmean(lat[ind])
      w_lon[i_w] = np.nanmean(lon[ind])

    # get rid of cluster centers below 20 or above 70
    if (abs(w_lat[i_w]) < 20) | (abs(w_lat[i_w]) > 70):
      w_lat[i_w] = np.nan
      w_lon[i_w] = np.nan
      wf[w_label == i_w] = 0.
      w_label[w_label == i_w] = 0.


  # cleaning up the cold fronts and picking only the eastern most point
  for i_c in range(1, c_num+1):
    ind = (c_label == i_c)
    x_ind, y_ind = np.where(ind)

    # keeping only clusters of 3 or more
    # also saving the mean lat and lon of the cluster
    if (len(x_ind) < 3):
      cf[c_label == i_c] = 0.
      c_label[c_label == i_c] = 0.
      continue
    else: 
      c_lat[i_c] = np.nanmean(lat[ind])
      c_lon[i_c] = np.nanmean(lon[ind])
    
    # get rid of cluster centers below 20 or above 70
    if (abs(c_lat[i_c]) < 20) | (abs(c_lat[i_c]) > 70):
      c_lat[i_c] = np.nan
      c_lon[i_c] = np.nan
      cf[c_label == i_c] = 0.
      c_label[c_label == i_c] = 0.
      continue

    # quick scatched up way to keep only eastern most points
    # optimize this later
    # FIXME issues with the edges
    for uni_x in set(x_ind):
      y_for_uni_x = y_ind[(x_ind == uni_x)]
      remove_y = y_for_uni_x[y_for_uni_x != np.nanmax(y_for_uni_x)]
      if (remove_y.size > 0):
        for y in remove_y: 
          cf[uni_x, y] = 0.
          c_label[uni_x, y] = 0.

    # after keeping the eastern most point, we do a new check to see
    # if the number of points is less than 3
    # if so we remove this detected front
    if (np.sum(cf[x_ind, y_ind]) < 3):
      cf[c_label == i_c] = 0.
      c_label[c_label == i_c] = 0.

  return (wf, {'lat': w_lat, 'lon': w_lon, 'label': w_label}), \
      (cf, {'lat': c_lat, 'lon': c_lon, 'label': c_label}) 

# def extend_global_lon(var): # comment out
#   '''
#   Extend the logitude on both sides of the longitude by +/- 360 values and pad up and down with nans
#   '''
#
#   # extract the size of the input variable
#   boxlen = var.shape[1]
#   lat_size = var.shape[0]
#   lon_size = var.shape[1]
#
#   # extend the variable in both directions by boxlen
#   var_new = np.zeros((lat_size, lon_size*3))*np.nan
#
#   var_new[:, 0:lon_size] = var - 360
#   var_new[:, lon_size:lon_size*2] = var
#   var_new[:, lon_size*2:lon_size*3] = var + 360
#
#   return var_new

# def extend_global_lat(var): # comment out
#   '''
#   Extend the logitude on both sides of the longitude by +/- 360 values and pad up and down with nans
#   '''
#
#   # extract the size of the input variable
#   boxlen = var.shape[1]
#   lat_size = var.shape[0]
#   lon_size = var.shape[1]
#
#   # extend the variable in both directions by boxlen
#   var_new = np.zeros((lat_size, lon_size*3))*np.nan
#
#   var_new[:, 0:lon_size] = var
#   var_new[:, lon_size:lon_size*2] = var
#   var_new[:, lon_size*2:lon_size*3] = var
#
#   return var_new

# def dist_between_global_grids(lat0, lon0, lat1, lon1): #comment out
#     ''' 
#     Dimensions have to lat x lon. NOTE: REVERSE of other functions
#     Just used by transect code
#     '''
#
#     elat0 = extend_global_lat(lat0)
#     elat1 = extend_global_lat(lat1)
#     elon0 = extend_global_lat(lon0)
#     elon1 = extend_global_lat(lon1)
#    
#     # in meters
#     dist = ((elat0 - elat1)**2 + (elon0-elon1)**2)**.5 * 111.12 * np.cos(elat0*np.pi/180.)
#
#     lon_size = lat0.shape[1]
#     dist_3d = np.empty((3, lat0.shape[0], lat0.shape[1]))
#     dist_3d[0, :, :] = dist[:, 0:lon_size]
#     dist_3d[1, :, :] = dist[:, lon_size:lon_size*2]
#     dist_3d[2, :, :] = dist[:, lon_size*2:]
#
#     dist_min = np.nanmin(dist_3d, axis=0)
#     
#     pdb.set_trace()
#     plt.close('all')
#     plt.pcolormesh(dist)
#     plt.colorbar()
#     plt.show()
#     pdb.set_trace()
#
#     return dist_min

def storm_attribution(lat, lon, w_label, c_label, center, wf_temp_grad): 

  # Initialize the final grid that we keep for warm/cold fronts
  w_keep_grid = np.zeros(w_label.shape)
  c_keep_grid = np.zeros(c_label.shape)

  ################ Clean up warm fronts
  w_uni_labels = np.unique(w_label)
  w_uni_labels = w_uni_labels[w_uni_labels != 0]
  w_mean_lat = np.zeros(w_uni_labels.shape)*np.nan
  w_mean_lon = np.zeros(w_uni_labels.shape)*np.nan
  w_mean_grad = np.zeros(w_uni_labels.shape)*np.nan
    
  # plt.pcolormesh(lon, lat, w_label)
  # plt.plot(center.lon, center.lat, 'r*')
  # plt.show()
  # import pdb; pdb.set_trace()
  
  for i, i_label in enumerate(w_uni_labels): 
    w_mean_lat[i] = np.nanmean(lat[w_label == i_label])
    w_mean_lon[i] = np.nanmean(lon[w_label == i_label])
    w_mean_grad[i] = np.nanmean(wf_temp_grad[w_label == i_label])
    
  # unique identifier for the fronts detected per center
  front_identifier = 0

  # loop through the centers 
  for ic_lon, ic_lat in zip(center.lon, center.lat):

    # unique identifier for the fronts detected per center
    front_identifier += 1

    if (np.abs(ic_lat) > 60): 
      continue

    # check if the cluster is within 15 degrees from the center
    dist_deg = distance_in_deg(w_mean_lon, w_mean_lat, ic_lon, ic_lat) 
    cond_dist = (dist_deg < 15)
    # print(cond_dist)
    # import pdb; pdb.set_trace()
    
    # check if center_lat - mean_lat_cluster < 5
    cond_lat = np.abs(ic_lat - w_mean_lat) < 5

    # check if center_lon is east of the storm center
    # have to account for -180 to 180 and 0 to 360 ranges
    w_mean_lon_shift = np.copy(w_mean_lon)
    w_mean_lon_shift[w_mean_lon_shift < 0] += 360
    ic_lon_shift = np.copy(ic_lon)
    if (ic_lon < 0): 
      ic_lon_shift += 360

    # check if center_lon is east of the storm center
    # have to account for -180 to 180 and 0 to 360 ranges
    w_mean_lon_shift1 = np.copy(w_mean_lon)
    w_mean_lon_shift1[w_mean_lon_shift1 > 180] -= 360
    ic_lon_shift1 = np.copy(ic_lon)
    if (ic_lon > 180): 
      ic_lon_shift1 -= 360

    ic_lon_thres = 0
    cond_lon = ((w_mean_lon - ic_lon) > ic_lon_thres) & ((w_mean_lon - ic_lon) < 15) \
        & ((w_mean_lon_shift - ic_lon_shift) > ic_lon_thres) & ((w_mean_lon_shift - ic_lon_shift) < 15) \
        & ((w_mean_lon_shift1 - ic_lon_shift1) > ic_lon_thres) & ((w_mean_lon_shift1 - ic_lon_shift1) < 15)

    # check if there are two fronts that get associated with the same center 
    # if so we have to pick the one with the maximum gradient
    front_select = cond_dist & cond_lat & cond_lon

    if (np.sum(front_select) > 1): 
      # have to pick the front with the maximum mean gradient 
      final_front = w_uni_labels[w_mean_grad == np.nanmax(w_mean_grad[front_select])]
      keep = True
    elif (np.sum(front_select) == 1):
      # if there is only front, then keep this label
      final_front = w_uni_labels[front_select]
      keep = True
    else: 
      keep = False

    if (keep):
      # w_keep_grid[w_label == final_front[0]] = w_label[w_label == final_front[0]]
      # changed above line to use the custom front indentifier 
      w_keep_grid[w_label == final_front[0]] = front_identifier
  
  ################ Clean up cold fronts
  c_uni_labels = np.unique(c_label)
  c_uni_labels = c_uni_labels[c_uni_labels != 0]
  c_mean_lat = np.zeros(c_uni_labels.shape)*np.nan
  c_mean_lon = np.zeros(c_uni_labels.shape)*np.nan
  c_mean_grad = np.zeros(c_uni_labels.shape)*np.nan
    
  # plt.pcolormesh(lon, lat, w_label)
  # plt.plot(center.lon, center.lat, 'r*')
  # plt.show()
  # import pdb; pdb.set_trace()

  # getting the unique grouped up labels for cold fronts
  # and estimating the center lat/lon and gradient of the fronts
  for i, i_label in enumerate(c_uni_labels): 
    c_mean_lat[i] = np.nanmean(lat[c_label == i_label])
    c_mean_lon[i] = np.nanmean(lon[c_label == i_label])
    c_mean_grad[i] = np.nanmean(wf_temp_grad[c_label == i_label])
  
  # unique identifier for the fronts detected per center
  front_identifier = 0
    
  # loop through the centers 
  for ic_lon, ic_lat in zip(center.lon, center.lat):

    # unique identifier for the fronts detected per center
    front_identifier += 1

    if (np.abs(ic_lat) > 60): 
      continue

    # check if the cluster is within 15 degrees from the center
    dist_deg = distance_in_deg(c_mean_lon, c_mean_lat, ic_lon, ic_lat) 
    cond_dist = (dist_deg < 15)
    # print(cond_dist)
    # import pdb; pdb.set_trace()
    
    # check if center_lat - mean_lat_cluster < 5
    dist_lon = distance_in_deg(c_mean_lon, 0, ic_lon, 0)
    # cond_lon = dist_lon < 7.5  # change this to 15 degrees, this is too tight to be 7.5 
    cond_lon = dist_lon < 15

    # check if center_lat is equatorwards 
    if (ic_lat > 0): 
      cond_lat = (c_mean_lat - ic_lat) < 0
    elif (ic_lat <= 0):
      cond_lat = (c_mean_lat - ic_lat) > 0

    # find the front that matches the conditions
    front_select = cond_dist & cond_lat & cond_lon

    # labelling all the fronts that are associated with the current center
    tmp_keep_idx = np.zeros(c_label.shape)
    for final_front in c_uni_labels[front_select]:
      tmp_keep_idx[c_label == final_front] = 1 

    # getting the lons and lats of the labelled fronts
    tmp_lons, tmp_lats = lon[tmp_keep_idx == 1], lat[tmp_keep_idx == 1]

    # if there any fronts associated to a center, then we have to find the eastern most point from all the avlues 
    if (np.any(front_select)):
      # get the unique lat values, and find the eastern most lon for it
      for tmp_i_lat in np.unique(tmp_lats):
        # get the index from tmp_lats/lons for the current unique values
        tmp_i_idx = (tmp_lats == tmp_i_lat)
        if (np.sum(tmp_i_idx) > 1): 
          # get the lons for the same lat
          tmp_i_lons = tmp_lons[tmp_i_idx]

          # get the maximum value of the lons, to get the eastern most points
          tmp_i_lon = np.nanmax(tmp_i_lons)

          # if the lons falls on the edges of 0-360, then we have to account for this
          # i just randomly pick 300 and 60 as a good value for fronts not to overlap
          if (np.any(tmp_i_lons > 300)) & (np.any(tmp_i_lons < 60)):
            tmp_i_lons[tmp_i_lons < 180] += 360
            tmp_i_lon = np.nanmax(tmp_i_lons)
            if (tmp_i_lon > 360): 
              tmp_i_lon -= 360

          # if the lons falls on the edges of -180 to 180, then we have to account for this
          # i just randomly pick 120 and -120 as a good value for fronts not to overlap
          if (np.any(tmp_i_lons > 120)) & (np.any(tmp_i_lons < -120)):
            tmp_i_lons[tmp_i_lons < 0] += 360
            tmp_i_lon = np.nanmax(tmp_i_lons)
            if (tmp_i_lon > 180): 
              tmp_i_lon -= -360
          
          # find the indexes in the main array that match the lat/lon
          tmp_main_idx = (lat == tmp_i_lat) & (lon == tmp_i_lon)

          # c_keep_grid[tmp_main_idx] = c_label[tmp_main_idx]
          # here i changed above line to use the new front unique identifier
          c_keep_grid[tmp_main_idx] = front_identifier
        else:
          tmp_i_lon = tmp_lons[tmp_i_idx]
          tmp_main_idx = (lat == tmp_i_lat) & (lon == tmp_i_lon)
          # c_keep_grid[tmp_main_idx] = c_label[tmp_main_idx]
          # here i changed above line to use the new front unique identifier
          c_keep_grid[tmp_main_idx] = front_identifier
          
  return c_keep_grid, w_keep_grid

def row_get_east_point(lats): 
  pass
