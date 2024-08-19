import numpy as np
import xarray as xr
import pandas as pd
from netCDF4 import Dataset
import glob
import os
import matplotlib.pyplot as plt
from scipy.ndimage import (
    label,
    find_objects,
    sum as ndi_sum,
    mean as ndi_mean,
    center_of_mass)
from scipy import stats
import scipy

def low_pass_weights(window, cutoff):
    """Calculate weights for a low pass Lanczos filter.
    Args:
    window: int
        The length of the filter window.
    cutoff: float
        The cutoff frequency in inverse time steps.
    From: https://github.com/liv0505/Lanczos-Filter/blob/master/lanczosbp.py
    """
    order = ((window - 1) // 2 ) + 1
    nwts  = 2 * order + 1
    w     = np.zeros([nwts])
    n     = nwts // 2
    w[n]  = 2 * cutoff
    k     = np.arange(1., n)
    sigma = np.sin(np.pi * k / n) * n / (np.pi * k)
    
    firstfactor = np.sin(2. * np.pi * cutoff * k) / (np.pi * k)
    w[n-1:0:-1] = firstfactor * sigma
    w[n+1:-1]   = firstfactor * sigma
    
    return w[1:-1]

def filter_data(data = None, nweights = 201, a = 5):
    weights = low_pass_weights(nweights, 1./a)
    
    weight_array  = xr.DataArray(weights, dims = ['window'])
    
    #apply the filters using the rolling methos with the weights
    filtered_data = data.rolling(time = len(weights), center = True).construct('window').dot(weight_array)
    
    return filtered_data

def land_mask_using_etopo(ds = None, topo_latgrid_1D = None, topo_longrid_1D = None,
                          topo_data1D = None, lf_cutoff = 10):
    
    half_xbin_size = float((ds.lon - np.roll(ds.lon, 1))[1:].mean()/2)
    half_ybin_size = float((ds.lat - np.roll(ds.lat, 1))[1:].mean()/2)

    first_xval = float((ds.lon[0]  - half_xbin_size).values)
    xbin_edges = np.asarray(ds.lon + half_xbin_size)
    xbin_edges = np.insert(xbin_edges, 0, first_xval)
    
    first_yval = float((ds.lat[0]  - half_ybin_size).values)
    ybin_edges = np.asarray(ds.lat + half_ybin_size)
    ybin_edges = np.insert(ybin_edges, 0, first_yval)

    bin_topo = stats.binned_statistic_2d(topo_latgrid_1D, topo_longrid_1D, topo_data1D, 
                                         statistic = lambda topo_data1D : np.count_nonzero(topo_data1D >= 0)/topo_data1D.size, 
                                         bins=[ybin_edges, xbin_edges], expand_binnumbers = True)

    lf_vals = bin_topo.statistic * 100.
    ls_mask = (lf_vals < lf_cutoff)*1
    
    return ls_mask  

def regridder_model2obs(lon_vals = None, lat_vals = None, in_data = None, type_name = 'bilinear', isperiodic = True):
    out_grid = xr.Dataset(
        {
            "lat": (["lat"], lat_vals),
            "lon": (["lon"], lon_vals)
        })

    regridder = xe.Regridder(in_data, out_grid, method = type_name, periodic = isperiodic)
    
    return regridder

#Used for removing the first n harmonics from the seasonal cycle
def nharm(x, N):
    if x.any()==0:
        print('here')
        return np.zeros(N)
    fft_output = scipy.fft.fft(x) 
    freq = scipy.fft.fftfreq(len(x), d = 1)
    filtered_fft_output = np.array([fft_output[i] if round(np.abs(1/f),2) in\
                                    [round(j,2) for j in [N, N/2, N/3]] else 0 for i, f in enumerate(freq)])
    #,N/2,N/3
    filtered_sig = scipy.fft.ifft(filtered_fft_output)
    filtered = filtered_sig.real
            
    return filtered

def calc_raw_and_smth_annual_cycle(raw_data = None, factor = 1, varname = 'tauu', in_units = 'Nm-2'):

    ds_rawAC = raw_data.groupby('time.dayofyear').mean(dim = ('time'), skipna = True)
    var_rawAC= ds_rawAC[varname]*factor
    
    var_climo_each_lon = var_rawAC.mean(dim = 'dayofyear')
    var_climo_each_lon = var_climo_each_lon.values

    #Info for removing harmonics
    N       = len(var_rawAC)
    tmpvals = var_rawAC.values
    filt    = np.zeros_like(tmpvals)
    
    #Find the frist 3 harmonics for each longitude
    for i in range(len(var_rawAC.lon)): filt[:, i] = nharm(tmpvals[:, i], N)

    var_smthAC = np.zeros_like(filt)
    for iday in range(len(var_rawAC.dayofyear)): var_smthAC[iday] = filt[iday] + var_climo_each_lon
        
    data_vars = dict(
        rawAC = (['dayofyear', 'lon'], var_rawAC, dict(units=in_units, lon_name = 'raw annual cycle for ' + varname)),
        smthAC= (['dayofyear', 'lon'], var_smthAC,dict(units=in_units, lon_name = 'smoothed (removed 1st 3 harmonics) annual cycle for ' + varname)))
    
    ds2save = xr.Dataset(data_vars=data_vars,
                         coords=dict(lon  = (['lon'], var_rawAC.lon),
                                   dayofyear = var_rawAC.dayofyear,),
                         attrs=dict(description='Raw and smoothed (removed 1st 3 harmonics) annual cycle for ' + varname, units = in_units,)
                        )     

    return ds2save


"""""
Explanation of bb_sizes used below:
followed - https://stackoverflow.com/questions/36200763/objects-sizes-along-dimension

"for object_slice in bb_slices" loops through each set of labeled_wwb slices
Example:
for object_slice in bb_slices:
    print(object_slice)

(slice(110, 112, None), slice(0, 1, None), slice(31, 35, None))
(slice(111, 114, None), slice(0, 1, None), slice(19, 27, None))
(slice(127, 130, None), slice(0, 1, None), slice(12, 21, None))
etc.

-----------------------------------------------------------------------
"s.stop-s.start for s in object_slice" 

Example:
for s in bb_slices[50]:
    print(s.stop - s.start)

3, 1, 13
since the bb_slices[50] = (slice(644, 647, None), slice(0, 1, None), slice(85, 98, None))

-----------------------------------------------------------------------
Note, for IWW:
The 0th blob (i.e., blob that has array index of 0) has 1 for a label. 
So, when indexing the labels need to add 1. (i.e., the slices for blob #17, 
which is the first blob that qualifies as a WWB, are 
(slice(295, 302, None), slice(0, 1, None), slice(15, 42, None)). These slices 
correspond to the blob labeled with and 18. print(labeled_blobs[bb_slices[iblob]]) 
returns values of 0 and 18 since the slice includes the bounding box of the blob

"""""
def isolate_WWEs(data = None, tauu_thresh = 0.04, mintime = 5, 
                 minlons = 10, xmin = 3, xmax = 3, ymin = 3,
                 ymax = 3, xtend_past_lon = 140):

    lon_array = np.asarray(data["lon"])
    
    # 1) Create mask for tauu > tauu_thresh (default is 0.04 following Puy et al. (2016))
    tauu_mask = data.where(data > tauu_thresh, 0)  #Assign elements with tauu < tauu_thresh zero 
    tauu_mask = tauu_mask.where(tauu_mask == 0, 1) #Assign elements with tauu > tauu_thresh one
    
    # 2) Find tauu blobs:
    #assign each contiguous region of tauu > 0.04 a unique number using the mask generated above
    labeled_blobs, n_blobs = label(tauu_mask)
    
    #Find the bounding box of each wwb feature
    bb_slices = find_objects(labeled_blobs)

    # 3) Find the size of the bounding box for each wwb feature, 
    #Explanation give above
    bb_sizes = np.array([[s.stop-s.start for s in object_slice] 
                         for object_slice in bb_slices])

    # 4) Find where blobs last at least X days and for X° of longitude
    time_index = np.where(np.asarray(data.dims) == 'time')
    lon_index  = np.where(np.asarray(data.dims) == 'lon')
    
    w_wwe = np.where((bb_sizes[:, time_index] >= mintime) & (bb_sizes[:, lon_index] >= minlons))
    n_wwe = np.count_nonzero((bb_sizes[:, time_index] >= mintime) & 
                             (bb_sizes[:, lon_index] >= minlons))
    #w_wwe_array = np.asarray(w_wwe)

    # 5) Make a mask of only the blobs that qualify as WWEs
    #Create wwe_mask array to be filled 
    wwe_mask = np.zeros_like(labeled_blobs) 

    #Loop through blobs that satisfiy intensity, duration, and zonal length criteria
    for i in range(len(w_wwe[0])):
        #w_temp                = np.where(flat_lab_blobs == w_wwe_array[0][i]+1)
        w_temp                = np.where(labeled_blobs == w_wwe[0][i]+1)
        wwe_mask[w_temp] = 1
 
    # 6) Label WWEs
    labeled_wwes, n_wwes = label(wwe_mask)

    # 7) Loop over all WWEs to see if any of them are close enough < 3 days and < 3° to count as same event
    wwes_after_merging = find_nearby_wwes_merge(n_wwes = n_wwes, labeled_wwes = labeled_wwes,
                                                xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax)

    # 8)Renumber the labels from 1 to nWWEs:
    #At this point some of the WWE labels have been eliminated because they were merged,
    #so need to renumber the labels from 1 to nWWEs
    new_wwe_labels = renumber_wwes(wwe_labels = wwes_after_merging)
    
    # 9) Check to see if the WWE extends beyond 140°E
    # Find the bounding box of each wwe feature
    bb_slices = find_objects(new_wwe_labels)

    #Find max longitudes for each WWE
    #The -1 for finding the indices is because the bb_slice gives the slice values and the stop value
    #is not inclusive in python (e.g., array[3:10] includes elements 3-9 and NOT 10)
    max_time_lon_ind = np.array([[s.stop for s in object_slice]
                                     for object_slice in bb_slices])
    max_lon_inds = max_time_lon_ind[:, lon_index[0][0]] -1
    max_lons     = lon_array[max_lon_inds]

    #Find min longitudes for each WWE
    min_time_lon_ind = np.array([[s.start for s in object_slice]
                                 for object_slice in bb_slices])
    min_lon_inds = min_time_lon_ind[:, lon_index[0][0]] -1
    min_lons     = lon_array[min_lon_inds]

    wwe_labels_count = np.unique(new_wwe_labels)[1:]
    wwe_maxlonsLTX   = np.where(max_lons < xtend_past_lon)
    n_wwe_maxlonsLTX = np.count_nonzero(max_lons < xtend_past_lon)

    # 10) Remove the WWE that isn't long enough
    if n_wwe_maxlonsLTX > 0:
        for i2remove in range(n_wwe_maxlonsLTX):
            wwe2remove = wwe_labels_count[wwe_maxlonsLTX[0][i2remove]]

            wwe_labels_afterRemoveX = np.where(new_wwe_labels == wwe2remove, 0, new_wwe_labels)

        min_lons = np.delete(min_lons, wwe_maxlonsLTX)
        max_lons = np.delete(max_lons, wwe_maxlonsLTX)

        # 11) Relabel WWE again becasue now more WWEs have potentially been removed
        wwe_labels_final = renumber_wwes(wwe_labels = wwe_labels_afterRemoveX)

        # 12) Final mask array
        wwe_mask_final = np.where(wwe_labels_final !=0, 1, 0)

    else:
        wwe_labels_final = new_wwe_labels
        wwe_mask_final   = wwe_mask
    
    return wwe_labels_final, wwe_mask_final

def find_nearby_wwes_merge(n_wwes = 0, labeled_wwes = None, xmin = 3, xmax = 3,
                            ymin = 3, ymax = 3):
    
    for i in range(1, n_wwes):
        wblob = np.where(labeled_wwes == i)
        npts  = np.asarray(wblob).shape[1]
        
        #Loop over each point in WWE and check surrounding 3 days and 3° for another labeled WWE
        for ipt in range(npts):
            if len(wblob) == 3:
                check_wwe_label = labeled_wwes[wblob[0][ipt] - xmin : wblob[0][ipt] + xmax + 1,
                                               0,
                                               wblob[2][ipt] - ymin : wblob[2][ipt] + ymax + 1]
            if len(wblob) == 2:
                check_wwe_label = labeled_wwes[wblob[0][ipt] - xmin : wblob[0][ipt] + xmax + 1,
                                               wblob[1][ipt] - ymin : wblob[1][ipt] + ymax + 1]
               
            n_diff_label    = np.count_nonzero((check_wwe_label != i) & (check_wwe_label != 0))
            
            #Replace nearby WWE label with earlier in time and/or space WWE, so the later WWE becomes 
            #a part of the smaller numbered WWE
            if n_diff_label > 0:
                w_diff_label            = np.where((check_wwe_label != i) & (check_wwe_label != 0))
                unique_overlapping_wwes = np.unique(check_wwe_label[w_diff_label])
                                
                for ioverlapwwe in range(unique_overlapping_wwes.size):
                    w_ioverlapwwe = np.where(labeled_wwes == unique_overlapping_wwes[ioverlapwwe])
                    labeled_wwes[w_ioverlapwwe] = i

    return labeled_wwes

def renumber_wwes(wwe_labels = None):
    uniq_labels0   = np.unique(wwe_labels)

    #Remove the 0 label as it's not a WWE
    uniq_labels    = uniq_labels0[~(uniq_labels0 == 0)]
    new_wwe_labels = np.zeros_like(wwe_labels)

    #Re-label wwes 0-nWWEs, so that find_object works correctly
    jj = 1

    for iwwe in range(len(uniq_labels)): 
        w_wwe_label    = np.where(wwe_labels == uniq_labels[iwwe])
        new_wwe_labels[w_wwe_label] = jj  
        jj += 1
        
    return new_wwe_labels

def WWE_characteristics(wwe_labels = None, data = None):
    
    #Find the bounding box of each WEE feature
    bb_slices = find_objects(wwe_labels)

    #Find the size of the bounding box for each wwb feature, 
    #Explanation give above
    object_sizes = np.array([[s.stop-s.start for s in object_slice] 
                              for object_slice in bb_slices])
    
    #Find the duration, length, and integrated wind work (IWW) of each WWE
    time_index         = np.where(np.asarray(data.dims) == 'time')
    lon_index          = np.where(np.asarray(data.dims) == 'lon')
    
    duration           = object_sizes[:, time_index[0][0]]
    zonal_extent       = object_sizes[:, lon_index[0][0]]
    
    array_label_values = np.arange(len(bb_slices))+1
    wwe_sum            = ndi_sum(np.asarray(data), wwe_labels, array_label_values)
    wwe_mean           = ndi_mean(np.asarray(data), wwe_labels, array_label_values)
    
    return duration, zonal_extent, wwe_sum, wwe_mean

def WWE_statistics(var2bin = None, cond_var1 = None, cond_var2 = None, 
                   min_bin = 5, max_bin = 27, bin_space = 2):
    
    bin_values = np.arange(min_bin, max_bin, bin_space)
    
    out_count, bin_edges, binnumber = stats.binned_statistic(var2bin, var2bin,
                                                                 'count', bins= bin_values)

    out_mean_cond1, bin_edges, binnumber = stats.binned_statistic(var2bin, cond_var1, 
                                                             'mean', bins= bin_values)
    
    out_mean_cond2, bin_edges, binnumber = stats.binned_statistic(var2bin, cond_var2, 
                                                             'mean', bins= bin_values)

    out_std_cond1, bin_edges, binnumber = stats.binned_statistic(var2bin, cond_var1, 
                                                             'std', bins= bin_values)
    
    out_std_cond2, bin_edges, binnumber = stats.binned_statistic(var2bin, cond_var2, 
                                                             'std', bins= bin_values)


    out_freq = out_count/out_count.sum()*100.
        
    return out_count, out_freq, out_mean_cond1, out_mean_cond2, out_std_cond1, out_std_cond2, bin_edges, binnumber

def find_WWE_time_lon(data = None, wwe_labels = None, lon = None, time_array = None):

    bb_slices = find_objects(wwe_labels)
    
    time_index = np.where(np.asarray(data.dims) == 'time')
    lon_index  = np.where(np.asarray(data.dims) == 'lon')

    uniq_labels     = np.unique(wwe_labels)[1:]
    time_lon_center = center_of_mass(np.asarray(data), wwe_labels, uniq_labels)

    #Use zip to extract the first & second element of 
    #each tuple in the time_lon_center list
    cent_time_ind = list(zip(*time_lon_center))[int(time_index[0])]
    cent_lon_ind  = np.asarray(list(zip(*time_lon_center))[int(lon_index[0])])

    #3/15/2023: round time to nearest day. I doubt the SSH data will 
    #be finer than a day, so rounding to a day seems sufficient. 
    cent_time_ind = np.round(cent_time_ind).astype("int")

    lower_lon_val = lon[np.floor(cent_lon_ind).astype("int")]
    upper_lon_val = lon[np.ceil(cent_lon_ind).astype("int")]
    
    #Make sure longitude delta is only 1degree
    delta_lon     = upper_lon_val - lower_lon_val
    if np.count_nonzero(delta_lon != 1) > 0: 
        print("Longitude delta GT 1degree")
    
    #Interpolate the longitude values using interpolation equation
    # y = y1 + (y2 - y1) * [(x - x1)/(x2 - x1)]
    # y(s) in this case are the lon values and x(s) are the lon indicies 
    # since the longitudes and indicies increment by one the euqtion 
    # reduces to y = y1 + (x - x1)
    center_lon_vals = lower_lon_val + (cent_lon_ind - np.floor(cent_lon_ind))
    center_time_vals= time_array[cent_time_ind]

    #Added 4/25/2024
    #Find max time for each WWE'
    #The -1 for finding the indices is because the bb_slice gives the slice values and the stop value
    #is not inclusive in python (e.g., array[3:10] includes elements 3-9 and NOT 10)
    max_time_lon_ind = np.array([[s.stop for s in object_slice]
                                 for object_slice in bb_slices])
    max_time_inds    = max_time_lon_ind[:, time_index[0][0]] - 1
    max_times        = time_array[max_time_inds]

    #Find min time for each WWE
    min_time_lon_ind = np.array([[s.start for s in object_slice]
                                 for object_slice in bb_slices])
    min_time_inds    = min_time_lon_ind[:, time_index[0][0]]
    min_times        = time_array[min_time_inds]
    
    #Find max longitudes for each WWE
    max_time_lon_ind = np.array([[s.stop for s in object_slice]
                                 for object_slice in bb_slices])
    max_lon_inds     = max_time_lon_ind[:, lon_index[0][0]] - 1
    max_lons         = lon[max_lon_inds]

    #Find min longitudes for each WWE
    min_time_lon_ind = np.array([[s.start for s in object_slice]
                                 for object_slice in bb_slices])
    min_lon_inds     = min_time_lon_ind[:, lon_index[0][0]]
    min_lons         = lon[min_lon_inds]
    
    return center_lon_vals, center_time_vals, min_times, max_times, min_lons, max_lons

#####################################################################
###PLOTTING CODE
#####################################################################
def plot_taux_wwe_hov(data = None, wwe_mask = None, st_year = 0, 
                      end_year = 0, save_name = '', taux_time = None,
                      center_lon_vals = None, center_time_vals = None,
                      do_center_marker = False, source_name = '', shade_choice = 'bwr'):
    
    #bp_data_subtime = data.sel(time = (data.time.dt.year == str(st_year)))
    wiyear          = np.where((np.asarray(taux_time.dt.year) == st_year) | 
                               (np.asarray(taux_time.dt.year) == end_year))
    
    #Plot details
    levs= np.linspace(-0.1, 0.1, 21)
    fig = pplt.figure(refwidth = 2.5, aspect = .7)
    ax  = fig.subplots(xlabel = 'longitude')

    #Make the plot
    cf = ax.contourf(np.asarray(data.lon), np.asarray(taux_time[wiyear[0]]),
                     np.asarray(data[wiyear[0], :]), levels = levs, 
                     cmap = shade_choice, extend = 'both')

    cl = ax.contour(np.asarray(data.lon), np.asarray(taux_time[wiyear[0]]),  
                    wwe_mask[wiyear[0], :], cmap = 'binary', linewidths = 1)
    
    if do_center_marker is True:
        cp = ax.plot(center_lon_vals, center_time_vals, 
                     marker="o", markersize=5, markeredgecolor="black", 
                     markerfacecolor="black", linestyle = 'None')

    ax.format(title = source_name, xlabel = 'Longitude', 
              ylabel = '', grid = True, xlim = [122, 270], xlocator = 'lon', 
              ylim = [np.asarray(taux_time[wiyear[0]]).min(), np.asarray(taux_time[wiyear[0]]).max()],
              ylocator = 'month', ytickminor = 0, fontsize = 11, titlesize = 12)

    ylim = [np.asarray(taux_time[wiyear[0]]).min(), np.asarray(taux_time[wiyear[0]]).max()]
    
    fig.colorbar(cf, label= 'Taux (N $m^{-2}$)', length=0.5, space = .7, labelsize = 10)

    if do_center_marker is True: 
        fig.save(save_name + '_CenterLabeled.png')
    else:
        fig.save(save_name + '.png')
        
    pplt.close()
    
    return cf

