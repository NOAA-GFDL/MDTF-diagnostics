# ================================================================================
# MDTF Diagnostic POD
# ================================================================================
# 
# Runoff sensitivities Diagnostic POD
# 
#   Last update: 12/02/2024
# 
#   Synopsis
#
#   Runoff projections are essential for future water security. 
#   The Earth System Models (ESMs) are increasingly being utilized for future water resource risk assessment. 
#   However, the runoff projections based on ESMs are highly uncertain, in part due to differences in the land process representation among ESMs.
#
#   In this diagnostics, we try to measure the land process biases in ESMs. 
#   First, the land processes related to runoff projections in each ESM can be statistically emulated by 
#   quantifying the inter-decadal sensitivity of runoff to temperature (temperature sensitivity) and
#   precipitation (precipitation sensitivity) using multiple linear regression (Lehner et al. 2019; Kim et al. 2024). 
#   To represent the land process biases, the runoff senstivities for each ESM are compared to 
#   observational estimations, which is pre-calculated using same regression method.
#   For the observational estimation, we used the GRUN-ENSEMBLE data 
#   - global reanalysis of monthly runoff using the machine learning technique (Ghiggi et al. 2021). 
#   The runoff sensitivities from CMIP5/6 models are also prepared to facilitate the comparison for new model development. 
#   The uncertainty ranges from internal variability, observational uncertainty, and inter-moel spread 
#   are provided for specific river basins to assess the significance of ESM biases.
#   
#   Version & Contact info
# 
#    - Version/revision information: version 3 (12/02/2024)
#    - PI: Flavio Lehner, Cornell University, flavio.lehner@cornell.edu
#    - Developer/point of contact: Hanjun Kim, Cornell University, hk764@cornell.edu
#    - Other contributors: 
# 
#   Open source copyright agreement
# 
#    The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
# 
#   Functionality
#
#    The main driver code (runoff_sensitivities_diag.py) include all functions, codes for calculations and figures.
#    0) Functions are pre-defined for further analysis.
#    1) The codes will load data and do area average for 131 global river basins for each water year (Mask source - GRDC Major River Basins of the World).
#    2) Water budget clousre (precipitaton - evapotranspiration == runoff) in long term average is checked.
#    3) Using the pre-defined function "runoff_sens_reg", runoff sensitivities are calculated.
#    4) Calculated runoff sensitivities for target models are saved as .nc file.
#    5) The diagnostic figures will be plotted with the pre-calculated OBS and CMIP data.
#
#   Programm language summary
#
#    Python 3 is used to calculate and draw the figures.
#    All libraries used in this diagnostic are available in MDTF conda environment "_MDTF_python3_base".
#    - Used libraries: "scipy", "numpy", "matplotlib", "netCDF4", "cartopy", "sklearn"    
#    - To deal with the shapefile, "cartopy.io.shapereader" and "matplotlib.path" is utilized.
#    - For multi-linear regression, "sklearn.linear_model" is utilized.    
# 
#   Required model output variables
#  
#    - The monthly historical simulations including period 1940-2014 are needed (Model outputs are assumed to be same with CMIP6 output).
#    - Target variables
#        - tas (surface air temperature, K), [time, lat, lon]
#        - pr (precipitaiton, kg m-2 s-1), [time, lat, lon] 
#        - hfls (latent heat flux, W m-2), [time, lat, lon]
#        - mrro (runoff, kg m-2 s-1), [time, lat, lon]
#    - lon-lat grids for 4 variables have to be same 
#      (In CMIP, there are some cases where grids are slightly different between land and atm variables. Checking/interpolation is recommended)
#    
#
#   References
# 
#    Lehner, F., Wood, A. W., Vano, J. A., Lawrence, D. M., Clark, M. P., & Mankin, J. S. (2019). 
#    The potential to reduce uncertainty in regional runoff projections from climate models. Nature Climate Change, 9(12), 926-933.
#    doi: 10.1038/s41558-019-0639-x
#
#    Kim, H., Lehner, F., Dagon, K., Lawrence, D. M., Swenson, S., & Wood, A. W. (2024).
#    Constraining climate model projections with observations amplifies future runoff declines. In preparation
#
#    Ghiggi, G., Humphrey, V., Seneviratne, S. I., & Gudmundsson, L. (2021). 
#    G‐RUN ENSEMBLE: A multi‐forcing observation‐based global runoff reanalysis. Water Resources Research, 57(5), e2020WR028787.
#    doi:10.1029/2020WR028787
# ================================================================================

import os
import warnings
import time as time
import numpy as np # python library for dealing with data array
import cartopy.io.shapereader as shpreader # cartopy library for loading with shapefiles
import matplotlib
# matplotlib.use('Agg') # non-X windows backend
import matplotlib.pyplot as plt    # python library we use to make plots
import matplotlib.patches as patches # python library for filling the polygons in plots
import matplotlib.colors as colors # python library for customizing colormaps
import matplotlib.path as mpltPath # matplotlib library to deal with polygons
from sklearn.linear_model import LinearRegression # python library we use to do multi-linear regression
import netCDF4 as nc # python library for handling nc files
import scipy.stats as stats # python library we use to do  basic statistics

##############################################################################################
### 0) pre-defined functions for calculations: ###############################################
##############################################################################################
## function to get area weight
def area_weight(lat, lon):
    a = 6371 * 1e3
    nlat = len(lat)
    nlon = len(lon)
    lon2d, lat2d = np.meshgrid(lon, lat)
    dx = a * np.outer(np.cos(np.deg2rad(lat)), np.gradient(np.deg2rad(lon)))
    dy = np.tile(a * np.gradient(np.deg2rad(lat)), (nlon, 1)).T
    aw = dx * dy
    return aw

################################################################
## function for runoff sensitivity calculation (least square) ##
################################################################
from sklearn.linear_model import LinearRegression
import scipy.stats as stats
import numpy as np
def runoff_sens_reg(r, p, t, mw=1, alpha=0.1):
    nan_val=np.mean(np.isnan(r))+np.mean(np.isnan(p))+np.mean(np.isnan(t))
    if nan_val == 0:
        # Ensure input vectors are column vectors
        if r.ndim == 1:
            r = r[:, np.newaxis]
        if p.ndim == 1:
            p = p[:, np.newaxis]
        if t.ndim == 1:
            t = t[:, np.newaxis]

        # Create the regression matrix and do normalization
        Xraw = np.column_stack((p, t, p * t))
        Xstd = np.nanstd(Xraw,axis=0)
        rstd = np.nanstd(r,axis=0)
        Xnorm = (Xraw - np.nanmean(Xraw,axis=0)) / Xstd
        rnorm = (r - np.nanmean(r,axis=0)) / rstd

        # Perform linear regression
        model = LinearRegression()
        model.fit(Xnorm, rnorm)

        # Get regression coefficients
        a1 = np.squeeze(model.coef_[0][0] * rstd / Xstd[0])
        b1 = np.squeeze(model.coef_[0][1] * rstd / Xstd[1])
        c1 = np.squeeze(model.coef_[0][2] * rstd / Xstd[2])
        
        # Calculate the standard errors for coefficients
        y_pred = a1*Xraw[:,0] + b1*Xraw[:,1] + c1*Xraw[:,2]
        residuals = r - y_pred[:,np.newaxis]
        n, k = Xraw.shape
        # autocorr=get_autocorr(r,1);
        # dof2 = (n-k)*(1-autocorr)/(1+autocorr)
        dof=np.ceil((n-k)/mw)
        mse = np.sum(residuals ** 2) / (dof)
        var_b = mse * np.linalg.pinv(np.dot(Xraw.T, Xraw))
        se_a1 = np.sqrt(var_b[0, 0])
        se_b1 = np.sqrt(var_b[1, 1])
        se_c1 = np.sqrt(var_b[2, 2])

        # Calculate the t-statistic for a given confidence level (e.g., alpha = 0.05)
        t_critical = stats.t.ppf(1 - alpha / 2, dof)

        # Calculate the confidence intervals
        a2 = np.array([a1 - t_critical * se_a1, a1 + t_critical * se_a1])
        b2 = np.array([b1 - t_critical * se_b1, b1 + t_critical * se_b1])
        c2 = np.array([c1 - t_critical * se_c1, c1 + t_critical * se_c1])
        
        # R-squared value
        corr, _ = stats.pearsonr(np.squeeze(r), np.squeeze(y_pred))
        r2 = corr**2
        
        return a1, a2, b1, b2, c1, c2, r2
    else:
        a1=np.nan; a2=np.nan; b1=np.nan; b2=np.nan; c1=np.nan; c2=np.nan; r2=np.nan;
        return a1, a2, b1, b2, c1, c2, r2

## function for calculate moving average!
def moving_avg(x_1d,n_mw):
    nt=len(x_1d)
    weight = np.ones((n_mw))/n_mw
    n_delete=int((n_mw)/2);
    smoothed=np.convolve(x_1d,weight,mode='same')
    if n_delete != 0:
        del_ind=np.concatenate((np.arange(n_delete),np.arange(nt-n_delete,nt)))
        smoothed_final=np.delete(smoothed,del_ind)
    return smoothed_final

## function for ignoring NaN value for correlation
def corr_nan(temp1,temp2):
    indnan=np.nanmean(temp1)+np.nanmean(temp2)
    if ~np.isnan(indnan):
        tempind=np.nonzero(np.isnan(temp1)|np.isnan(temp2))
        temp1=np.delete(temp1,tempind)
        temp2=np.delete(temp2,tempind)
        corr,_=stats.pearsonr(temp1,temp2)
        return corr
    else:
        return np.nan

## Calculate confidence interval of the data by t-test
def get_confidence_interval(data,alpha):
    # alpha=0.9 --> 5%-95% confidence interval
    # data is assumed to be not containing nan-value
    mean = np.mean(data)
    std_dev = np.std(data, ddof=1)  # ddof=1 for sample standard deviation
    # Number of samples
    n = len(data)
    # dof for t-distributions
    dof = n - 1    
    # Calculate the standard error of the mean
    se = std_dev / np.sqrt(n)
    # Calculate the t-score for the confidence level
    t_score = stats.t.ppf((1 + alpha) / 2, dof)
    # Calculate the margin of error
    margin_of_error = t_score * se
    return margin_of_error

## find statistically significant r, given n
import numpy as np
import scipy.stats as stats
def significant_pearsonr(n,alpha):
    # Degrees of freedom
    df = n - 2
    # Critical t-value (two-tailed)
    t_critical = stats.t.ppf(1 - alpha/2, df)
    # Calculate critical r
    r_critical = t_critical / np.sqrt(df + t_critical**2)
    r_critical = np.abs(r_critical)  # Consider absolute value for significance
    return r_critical

################################################################################
### 1) Loading model data files and doing area average for each water-year #####
################################################################################
#
# The framework copies model data to a regular directory structure of the form
# <DATADIR>/<frequency>/<CASENAME>.<variable_name>.<frequency>.nc
# Here <variable_name> and frequency are requested in the "varlist" part of 
# settings.json.

# The following command sets input_path to the value of the shell environment
# variable called TAS_FILE. This variable is set by the framework to let the 
# script know where the locally downloaded copy of the data for this variable
# (which we called "tas") is.

## load model deta
# data path from framework
pr_path = os.environ["PR_FILE"]
tas_path = os.environ["TAS_FILE"]
hfls_path = os.environ["HFLS_FILE"]
mrro_path = os.environ["MRRO_FILE"]

# model grids (pr,tas,hfls,mrro must have same lon,lat grids)
lat_coor_name = os.environ["lat_coord"]
lon_coor_name = os.environ["lon_coord"]
time_coord_name = os.environ["time_coord"]
latm = nc.Dataset(pr_path).variables[lat_coor_name][:]
lonm = nc.Dataset(pr_path).variables[lon_coor_name][:]
time = nc.Dataset(pr_path).variables[time_coord_name][:]
nlat = len(latm)
nlon = len(lonm)
nt = len(time)
nyr = int(nt/12)
syr_model = int(os.environ["FIRSTYR"])
eyr_model = int(os.environ["LASTYR"])

# variables
pr_var_name = os.environ["pr_var"]
tas_var_name = os.environ["tas_var"]
hfls_var_name = os.environ["hfls_var"]
mrro_var_name = os.environ["mrro_var"]
prm = nc.Dataset(pr_path).variables[pr_var_name][:,:,:].filled(fill_value=np.nan)
tasm = nc.Dataset(tas_path).variables[tas_var_name][:,:,:].filled(fill_value=np.nan)
hflsm = nc.Dataset(hfls_path).variables[hfls_var_name][:,:,:].filled(fill_value=np.nan)
mrrom = nc.Dataset(mrro_path).variables[mrro_var_name][:,:,:].filled(fill_value=np.nan)

## change lon & variables to western degree, since the basin mask is not closed in eastern degree.
if np.mean(lonm) > 100:
    # change lon to western degree
    lonw = lonm - 180
    lonw[lonw < 0] = 1000
    ind180 = np.argmin(lonw)
    lonwm = np.concatenate((lonm[ind180:] - 360, lonm[0:ind180]))
    western_ind=np.concatenate((range(ind180, nlon), range(0, ind180)))
    prm = prm[:, :, western_ind]
    tasm = tasm[:, :, western_ind]
    mrrom = mrrom[:, :, western_ind]
    hflsm = hflsm[:, :, western_ind]

## water year average (Oct-Sep water year for every basin)
## do time average and then do basin average (save computation time a lot)
syr_sens=1945
eyr_sens=2014
nyr = eyr_sens - syr_sens
inds=(syr_sens-syr_model)*12 + 10 - 1
inde=inds + (nyr)*12
prm_wy = np.nanmean(np.reshape(prm[inds:inde,:,:],(12,nyr,nlat,nlon),order="F"), axis=0)
tasm_wy = np.nanmean(np.reshape(tasm[inds:inde,:,:],(12,nyr,nlat,nlon),order="F"), axis=0)
mrrom_wy = np.nanmean(np.reshape(mrrom[inds:inde,:,:],(12,nyr,nlat,nlon),order="F"), axis=0)
hflsm_wy = np.nanmean(np.reshape(hflsm[inds:inde,:,:],(12,nyr,nlat,nlon),order="F"), axis=0)

## area average for specific river basins
# load basin masks from shapefile provided by GRDC
shapefile_path = "{OBS_DATA}/mrb_basins.shp".format(**os.environ)
records=list(list(shpreader.Reader(shapefile_path).records()))

# Select large basins based on the pre-defined indices (this reduces computation time)
bind = np.array([9, 12, 14, 19, 28, 29, 33, 34, 39, 42, 46, 54, 55, 62, 64, 65, 66, 71, 72, 73, 76, 79, 82, 83, 84, 85, 89, 90, 91, \
    92, 94, 95, 99, 100, 101, 102, 103, 106, 110, 111, 113, 114, 116, 117, 119, 123, 124, 128, 129, 130, 138, 144, 148, 153, 160, 161, 163, 164, \
    166, 169, 170, 172, 173, 174, 176, 178, 179, 181, 187, 194, 196, 211, 216, 218, 222, 223, 227, 229, 231, 232, 270, 276, 280, 283, 284, 293, 297, \
    298, 299, 300, 306, 307, 312, 318, 328, 329, 340, 347, 358, 363, 364, 368, 372, 383, 393, 394, 399, 403, 409, 415, 416, 439, 443, 445, 452, 454, \
    461, 463, 465, 467, 470, 485, 494, 495, 500, 501, 517, 519, 520, 379, 381])

# get basin masks/names for the slected ones
bind = bind - 1;
basin_points=[]
basin_names=[]
for i in bind:
    geom = records[i].geometry
    if geom.geom_type == 'Polygon':
        coords = list(geom.exterior.coords)
        basin_points.append(coords[0::10])
    elif geom.geom_type == 'MultiPolygon':
        npoly=len(geom.geoms)
        coords = list(geom.geoms[npoly-1].exterior.coords)
        basin_points.append(coords[0::10])
    basin_names.append(records[i].attributes['RIVER_BASI'])

nb=len(basin_points)

# basin mask for each basin
basin_maskm = np.zeros((nlat, nlon, nb))
lon2d, lat2d = np.meshgrid(lonwm, latm)
lon_points=np.reshape(lon2d,(nlat*nlon,1),order='F')
lat_points=np.reshape(lat2d,(nlat*nlon,1),order='F')
for b in range(nb):
    path = mpltPath.Path(basin_points[b])
    inside=path.contains_points(np.column_stack([lon_points,lat_points]))
    inside2d=np.reshape(inside,(nlat,nlon),order='F')
    basin_maskm[:, :, b] = inside2d

# area weight for each basin
aw = area_weight(latm, lonwm)
aw_basins = np.tile(aw[:,:,np.newaxis], (1, 1, nb)) * basin_maskm
# print(np.nansum(np.nansum(aw_basins,axis=1),axis=0))
## note that basin 114 (PECHORA) is not captured by CESM2 grid -> area is 0

# basin average
awm = np.transpose(np.tile(aw_basins[:,:,:,np.newaxis],(1,1,1,nyr)),(3,0,1,2))

prb_wy = np.nansum(np.nansum( \
                        np.tile(prm_wy[:, :, :, np.newaxis], (1, 1, 1, nb)) * awm \
                            , axis=1), axis=1) / np.nansum(np.nansum(awm, axis=1), axis=1)

tasb_wy = np.nansum(np.nansum( \
                        np.tile(tasm_wy[:, :, :, np.newaxis], (1, 1, 1, nb)) * awm \
                            , axis=1), axis=1) / np.nansum(np.nansum(awm, axis=1), axis=1)

mrrob_wy = np.nansum(np.nansum( \
                        np.tile(mrrom_wy[:, :, :, np.newaxis], (1, 1, 1, nb)) * awm \
                            , axis=1), axis=1) / np.nansum(np.nansum(awm, axis=1), axis=1)

hflsb_wy = np.nansum(np.nansum( \
                        np.tile(hflsm_wy[:, :, :, np.newaxis], (1, 1, 1, nb)) * awm \
                            , axis=1), axis=1) / np.nansum(np.nansum(awm, axis=1), axis=1)



################################################################################
### 2) check water budget closure, negative values, consistent values: #############################################
################################################################################
## sanity check to ensure that runoff output is not strange

## Note that CESM is almost free from this problem when we analyzed CEMS1 and CESM2

## some CMIP model's mrro (runoff) shows some erronous behaviour for some basins
# 1. water budget is not closed; P(precip)-E(evap) is way different from Q(runoff)
# 2. runoff is negative in some basins, leading to negative or very small climatological runoff
# 3. same and small runoff value is repeated for long times in some dry basins

## 1. check the water budget closure
pmeb_model = np.nanmean(prb_wy - hflsb_wy/(2.5*1e6), axis=0)
error_val = (pmeb_model - np.nanmean(mrrob_wy, axis=0)) / np.nanmean(mrrob_wy, axis=0)
pval = 0.05
closed_fraction=np.nansum( np.abs(error_val)<0.05 ,axis=0) / nb
if closed_fraction<0.8:
    raise ValueError('water budget is not closed more than 80% of ' + str(nb) + 'basins')

 

##############################################################################
##  3) calculate runoff sensitivities  ##########
##############################################################################
# initialization
psens_model = np.full((nb, 3),np.nan)
tsens_model = np.full((nb, 3),np.nan)
intsens_model = np.full((nb, 3),np.nan)
r2_mrro_wy_int = np.full((nb),np.nan)
r2_model_int = np.full((nb),np.nan)
r2_model_pred = np.full((nb),np.nan)
r2_model_pred_int = np.full((nb),np.nan)

# water year average (Oct-Sep water year for every basin)
# after 5-year average, the definition of differnet water year for each basin does not matter much
mw=5 # 5-year moving window
for b in range(nb):
    # specify start and end indices

    # smoothing (5-year moving average)
    mrrobym = moving_avg(mrrob_wy[:,b],mw)
    prbym = moving_avg(prb_wy[:,b],mw)
    tasbym = moving_avg(tasb_wy[:,b],mw)

    # get anomalies
    amrrobym = mrrobym - np.nanmean(mrrobym)
    aprbym = prbym - np.nanmean(prbym)
    atasbym = tasbym - np.nanmean(tasbym)

    # get % anomalies
    amrrobym_pct = amrrobym / np.nanmean(mrrobym) * 100
    aprbym_pct = aprbym / np.nanmean(prbym) * 100

    # calculate runoff sensitivities using def runoff_sens_reg(r, p, t):
    a1, a2, b1, b2, c1, c2, r2 = runoff_sens_reg(amrrobym_pct, aprbym_pct, atasbym, mw=5, alpha=0.1)
    psens_model[b,0] = a1
    psens_model[b,1:3] = a2
    tsens_model[b,0] = b1
    tsens_model[b,1:3] = b2
    intsens_model[b,0] = c1
    intsens_model[b,1:3] = c2
    r2_mrro_wy_int[b] = r2

    # prediction and resulting R2 (training accuracy)
    amrrobym_pct_pred_model = a1 * aprbym_pct + b1 * atasbym
    amrrobym_pct_pred_int_model = a1 * aprbym_pct + b1 * atasbym + c1 * atasbym * aprbym_pct
    corr = corr_nan(amrrobym_pct_pred_model, amrrobym_pct_pred_int_model)
    r2_model_int[b] = corr**2
    corr = corr_nan(amrrobym_pct_pred_model, amrrobym_pct)
    r2_model_pred[b] = corr**2
    corr = corr_nan(amrrobym_pct_pred_int_model, amrrobym_pct)
    r2_model_pred_int[b] = corr**2

# display warning if the interaction term is affecting the regression models
# role of interaction term (P*T) is usually negligible, consistent to Lehner et al. 2019
condition=np.asarray(r2_model_int<0.8)
# condition=np.asarray(np.abs(r2_model_pred_int-r2_model_pred)>0.2)
for b in range(b):
    if condition[b]:
        warning_message = f'Warning: Interaction term may matter for model + basin #{b+1} (r={r2_model_int[b]:.2f})'
        warnings.warn(warning_message)



#####################################################
### 4) Saving output data: ##########################
#####################################################
## save runoff sensitivity data in netCDF4 file
out_path = "{WK_DIR}/model/netCDF/runoff_sensitivities_{CASENAME}.nc".format(**os.environ)
# Create a NetCDF dataset
dataset = nc.Dataset(out_path, 'w')
# Create dimensions
basin_dim = tsens_model.shape[0]
sens_dim = tsens_model.shape[1]
dataset.createDimension("basin", basin_dim)
dataset.createDimension("sens_type", sens_dim)
string_length = 45
dataset.createDimension("string_len", string_length)
# Create variables
basin_var = dataset.createVariable('basin', 'S1', ('basin', 'string_len'))
tsens_model_var = dataset.createVariable('tsens_model', np.float64, ('basin', 'sens_type'), fill_value=-9999)
psens_model_var = dataset.createVariable('psens_model', np.float64, ('basin', 'sens_type'), fill_value=-9999)
r2_model_pred_var = dataset.createVariable('r2_model_pred', np.float64, ('basin'), fill_value=-9999)
# assign attributes
basin_var.long_name = 'target basins'
basin_var.reference = 'ref: https://grdc.bafg.de/GRDC/EN/02_srvcs/22_gslrs/221_MRB/riverbasins_node.html'
tsens_model_var.long_name = f'temperature sensitivity ({syr_sens}-{eyr_sens})'
tsens_model_var.units = '%/K'
tsens_model_var.sens_type_index = '1: sensitivity value / 2,3: 95% confidence interval'
psens_model_var.long_name = f'precipitation sensitivity ({syr_sens}-{eyr_sens})'
psens_model_var.units = '%/%'
psens_model_var.sens_type_index = '1: sensitivity value / 2,3: 95% confidence interval'
r2_model_pred_var.long_name = f'regression model accuracy (R^2) ({syr_sens}-{eyr_sens})'
r2_model_pred_var.units = 'no units'
# assign variables
for i, s in enumerate(basin_names):
    basin_var[i, :len(s)] = np.array(list(s), dtype='S1')
tsens_model_var[:] = tsens_model
psens_model_var[:] = psens_model
r2_model_pred_var[:] = r2_model_pred
# close and save
dataset.close()


################################################################################
### 5) Loading digested data  & plotting obs figures: ##########################
################################################################################
## load pre-calculated obs and cmip data
# load obs
obs_path = "{OBS_DATA}/runoff_sensitivity_obs.nc".format(**os.environ)
tsens_obs = nc.Dataset(obs_path)['tsens_obs'][:,:,0:nb,:]
psens_obs = nc.Dataset(obs_path)['psens_obs'][:,:,0:nb,:]
r2_obs_pred = nc.Dataset(obs_path)['r2_obs_pred'][:,:,0:nb]
# load cmip5
hist5_path = "{OBS_DATA}/runoff_sensitivity_hist5.nc".format(**os.environ)
tsens_hist5 = nc.Dataset(hist5_path)['tsens_hist5'][:,0:nb,:]
psens_hist5 = nc.Dataset(hist5_path)['psens_hist5'][:,0:nb,:]
r2_hist5_pred = nc.Dataset(hist5_path)['r2_hist5_pred'][:,0:nb]
# load cmip6
hist6_path = "{OBS_DATA}/runoff_sensitivity_hist6.nc".format(**os.environ)
tsens_hist6 = nc.Dataset(hist6_path)['tsens_hist6'][:,0:nb,:]
psens_hist6 = nc.Dataset(hist6_path)['psens_hist6'][:,0:nb,:]
r2_hist6_pred = nc.Dataset(hist6_path)['r2_hist6_pred'][:,0:nb]


#############################################
## draw maps with filled river basins #######
#############################################
def plot_and_save_basin_filled(values, basin_points, color_bins, color_bins2, plt_colormap, plt_unit, plt_title, plt_path, coast_path):
    ## data needed for plotting
    # assign color index to each values
    values_ind=np.digitize(values, color_bins2)-1
    # make colormap
    custom_cmap=colors.LinearSegmentedColormap.from_list('custom_colormap',plt_colormap, N=len(color_bins)-1)
    # load coastline
    lonmap = nc.Dataset(coast_path)['lonmap'][0:9850]
    latmap = nc.Dataset(coast_path)['latmap'][0:9850]
    ## draw figure
    fig, ax = plt.subplots(figsize=(12, 4.8))
    plt.rcParams.update({'font.size': 12})
    # coastline
    ax.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
    ax.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
    # fill basins with colors corresponding to target values
    for b in range(nb):
        X = [item[0] for item in basin_points[b]]
        Y = [item[1] for item in basin_points[b]]
        X = X[0:-int(np.floor(len(X)/100))]
        Y = Y[0:-int(np.floor(len(Y)/100))]
        if not np.isnan(values_ind[b]):
            ax.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=custom_cmap(values_ind[b]), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
        else:
            ax.plot(X, Y, color=(0.5, 0.5, 0.5), linewidth=0.5)
    # Set colormap and colorbar
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0, 1), cmap=custom_cmap))
    cb.set_ticks(np.linspace(0, 1, len(color_bins)))
    clabels = [str(b) for b in color_bins]
    cb.set_ticklabels(clabels)
    cb.set_label(plt_unit, fontsize=12)
    # Customize the ticks and labels
    ax.set_xticks(range(-180, 181, 30))
    ax.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
    ax.set_yticks(range(-90, 91, 15))
    ax.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
    ax.set_xlim([-180, 180])
    ax.set_ylim([-60, 80])
    # Set title
    ax.set_title(plt_title, fontsize=17)
    # Save the figure as a eps
    plt.savefig(plt_path, bbox_inches='tight')
    plt.close()



## figures for T sensitivity ##
bins = [-30,-15,-12,-9,-6,-3,0,3,6,9,12,15,30]
bins2 = [-60,-15,-12,-9,-6,-3,0,3,6,9,12,15,60]
plot_colormap = [(0.4000, 0, 0, 1),(0.7706, 0, 0, 1),(0.9945, 0.0685, 0.0173, 1),(0.9799, 0.2483, 0.0627, 1),(0.9715, 0.4442, 0.0890, 1),(0.9845, 0.6961, 0.0487, 1),(0.9973, 0.9480, 0.0083, 1),(1.0000, 1.0000, 0.3676, 1),(1.0000, 1.0000, 1.0000, 1),(1.0000, 1.0000, 1.0000, 1),(0.6975, 0.8475, 0.9306, 1),(0.4759, 0.7358, 0.8797, 1),(0.2542, 0.6240, 0.8289, 1),(0.0436, 0.5130, 0.7774, 1),(0.0533, 0.4172, 0.7138, 1),(0.0630, 0.3215, 0.6503, 1),(0.0411, 0.1760, 0.5397, 1),(0, 0, 0.4000, 1)]
plot_unit='[%/K]'
coast_path = "{OBS_DATA}/coastline.nc".format(**os.environ)

# OBS
obs_val=np.nanmean(np.nanmean(tsens_obs[:,:,:,0],axis=0),axis=0)
plot_title='T sensitivity: OBS'
plot_path = "{WK_DIR}/obs/PS/tsens_obs.eps".format(**os.environ)
plot_and_save_basin_filled(obs_val, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# model
values=tsens_model[:,0]
plot_title=f'T sensitivity: MODEL (WBC={closed_fraction:0.2f})'
plot_path= "{WK_DIR}/model/PS/tsens_model.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# model bias
values=tsens_model[:,0]-obs_val
plot_title='T sensitivity bias: MODEL - OBS'
plot_path= "{WK_DIR}/model/PS/tsens_model_bias.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# hist6 bias
values=np.nanmean(tsens_hist6[:,:,0],axis=0)-obs_val
plot_title='T sensitivity bias: CMIP6 - OBS'
plot_path= "{WK_DIR}/obs/PS/tsens_hist6_bias.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)


## figures for P sensitivity ##
bins=[-3.5, -3, -2.5, -2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2, 2.5, 3, 3.5];
bins2=[-100, -3, -2.5, -2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2, 2.5, 3, 100];
plot_colormap = [(0.4000, 0, 0, 1), (0.7316, 0, 0, 1), (0.9975, 0.0306, 0.0078, 1), (0.9845, 0.1915, 0.0484, 1), (0.9715, 0.3525, 0.0890, 1), (0.9776, 0.5636, 0.0700, 1), (0.9891, 0.7889, 0.0338, 1), (1.0000, 1.0000, 0.0263, 1), (1.0000, 1.0000, 0.4408, 1), (1.0000, 1.0000, 1.0000, 1), (1.0000, 1.0000, 1.0000, 1), (0.7325, 0.8651, 0.9386, 1), (0.5342, 0.7652, 0.8931, 1), (0.3359, 0.6652, 0.8476, 1), (0.1375, 0.5652, 0.8020, 1), (0.0477, 0.4727, 0.7506, 1), (0.0563, 0.3870, 0.6938, 1), (0.0651, 0.3013, 0.6370, 1), (0.0368, 0.1575, 0.5250, 1), (0, 0, 0.4000, 1)]
plot_colormap = [(0.4000, 0, 0, 1), (0.7316, 0, 0, 1), (0.9975, 0.0306, 0.0078, 1), (0.9845, 0.1915, 0.0484, 1), (0.9715, 0.3525, 0.0890, 1), (0.9776, 0.5636, 0.0700, 1), (0.9891, 0.7889, 0.0338, 1), (1.0000, 1.0000, 0.0263, 1), (1.0000, 1.0000, 0.4408, 1), (1.0000, 1.0000, 1.0000, 1), (1.0000, 1.0000, 1.0000, 1), (0.7325, 0.8651, 0.9386, 1), (0.5342, 0.7652, 0.8931, 1), (0.3359, 0.6652, 0.8476, 1), (0.1375, 0.5652, 0.8020, 1), (0.0477, 0.4727, 0.7506, 1), (0.0563, 0.3870, 0.6938, 1), (0.0651, 0.3013, 0.6370, 1), (0.0368, 0.1575, 0.5250, 1), (0, 0, 0.4000, 1)]
plot_unit='[%/%]'

# OBS
obs_val=np.nanmean(np.nanmean(psens_obs[:,:,:,0],axis=0),axis=0)
plot_title='P sensitivity: OBS'
plot_path= "{WK_DIR}/obs/PS/psens_obs.eps".format(**os.environ)
plot_and_save_basin_filled(obs_val, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# model
values=psens_model[:,0]
plot_title=f'P sensitivity: MODEL (WBC={closed_fraction:0.2f})'
plot_path= "{WK_DIR}/model/PS/psens_model.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# model bias
values=psens_model[:,0]-obs_val
plot_title='P sensitivity bias: MODEL - OBS'
plot_path= "{WK_DIR}/model/PS/psens_model_bias.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)

# hist6 bias
values=np.nanmean(psens_hist6[:,:,0],axis=0)-obs_val
plot_title='P sensitivity bias: CMIP6 - OBS'
plot_path= "{WK_DIR}/obs/PS/psens_hist6_bias.eps".format(**os.environ)
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)


###########################################
## summary figures for target variables  ##
###########################################
def plot_and_save_basin_filled_summary(values_obs, values_model, values_hist5, values_hist6, basin_points, color_bins, color_bins2, plt_colormap, plt_unit, plt_title, plt_path, coast_path, closed_fraction):
    # load coastline
    lonmap = nc.Dataset(coast_path)['lonmap'][0:9850]
    latmap = nc.Dataset(coast_path)['latmap'][0:9850]
    # colormap
    custom_cmap=colors.LinearSegmentedColormap.from_list('custom_colormap',plt_colormap, N=len(bins)-1)
    
    ## draw figure
    fig = plt.figure(figsize=(17, 10))
    plt.rcParams.update({'font.size': 12})  # Change the font size to 12
    # OBS
    values_ind=np.digitize(values_obs,color_bins2)-1
    h1 = fig.add_axes([0.06, 0.58, 0.43, 0.32])
    h1.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
    h1.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
    for b in range(nb):
        X = [item[0] for item in basin_points[b]]
        Y = [item[1] for item in basin_points[b]]
        X = X[0:-int(np.floor(len(X)/100))]
        Y = Y[0:-int(np.floor(len(Y)/100))]
        if not np.isnan(values_ind[b]):
            h1.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=custom_cmap(values_ind[b]), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
        else:
            h1.plot(X, Y, color=(0.5, 0.5, 0.5), linewidth=0.5)
    h1.set_xticks(range(-180, 181, 30))
    h1.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
    h1.set_yticks(range(-90, 91, 15))
    h1.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
    h1.set_xlim([-180, 180])
    h1.set_ylim([-60, 80])
    h1.set_title('OBS', fontsize=17)
    plt.text(195,105,plt_title, fontsize=20, ha='center', fontweight='bold')
    # model
    values_ind=np.digitize(values_model,color_bins2)-1
    h2 = fig.add_axes([0.54, 0.58, 0.43, 0.32])
    h2.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
    h2.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
    for b in range(nb):
        X = [item[0] for item in basin_points[b]]
        Y = [item[1] for item in basin_points[b]]
        X = X[0:-int(np.floor(len(X)/100))]
        Y = Y[0:-int(np.floor(len(Y)/100))]
        if not np.isnan(values_ind[b]):
            h2.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=custom_cmap(values_ind[b]), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
        else:
            h2.plot(X, Y, color=(0.5, 0.5, 0.5), linewidth=0.5)
    h2.set_xticks(range(-180, 181, 30))
    h2.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
    h2.set_yticks(range(-90, 91, 15))
    h2.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
    h2.set_xlim([-180, 180])
    h2.set_ylim([-60, 80])
    h2.set_title(f'MODEL (WBC={closed_fraction:0.2f})', fontsize=17)
    # hist5
    values_ind=np.digitize(values_hist5,color_bins2)-1
    h3 = fig.add_axes([0.06, 0.17, 0.43, 0.32])
    h3.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
    h3.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
    for b in range(nb):
        X = [item[0] for item in basin_points[b]]
        Y = [item[1] for item in basin_points[b]]
        X = X[0:-int(np.floor(len(X)/100))]
        Y = Y[0:-int(np.floor(len(Y)/100))]
        if not np.isnan(values_ind[b]):
            h3.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=custom_cmap(values_ind[b]), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
        else:
            h3.plot(X, Y, color=(0.5, 0.5, 0.5), linewidth=0.5)
    h3.set_xticks(range(-180, 181, 30))
    h3.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
    h3.set_yticks(range(-90, 91, 15))
    h3.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
    h3.set_xlim([-180, 180])
    h3.set_ylim([-60, 80])
    h3.set_title('CMIP5 MMM (21 models)', fontsize=17)
    # hist6
    values_ind=np.digitize(values_hist6,color_bins2)-1
    h4 = fig.add_axes([0.54, 0.17, 0.43, 0.32])
    h4.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
    h4.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
    for b in range(nb):
        X = [item[0] for item in basin_points[b]]
        Y = [item[1] for item in basin_points[b]]
        X = X[0:-int(np.floor(len(X)/100))]
        Y = Y[0:-int(np.floor(len(Y)/100))]
        if not np.isnan(values_ind[b]):
            h4.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=custom_cmap(values_ind[b]), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
        else:
            h4.plot(X, Y, color=(0.5, 0.5, 0.5), linewidth=0.5)
    h4.set_xticks(range(-180, 181, 30))
    h4.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
    h4.set_yticks(range(-90, 91, 15))
    h4.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
    h4.set_xlim([-180, 180])
    h4.set_ylim([-60, 80])
    h4.set_title('CMIP6 MMM (26 models)', fontsize=17)
    # Colorbar
    cax = fig.add_axes([0.06, 0.085, 0.91, 0.025])
    sm=plt.cm.ScalarMappable(norm=plt.Normalize(0, 1), cmap=custom_cmap)
    cb = plt.colorbar(sm,cax=cax, cmap=custom_cmap, orientation='horizontal')
    cb.set_ticks(np.linspace(0, 1, len(color_bins)))
    cb.set_ticklabels([str(b) for b in color_bins])
    cb.ax.set_xlabel(plt_unit, fontsize=12)
    # Save the figure
    plt.savefig(plt_path)
    plt.close()

# summary for training accuracy
bins=[0, 0.16, 0.36, 0.49, 0.64, 0.81, 1]
bins2=[0, 0.16, 0.36, 0.49, 0.64, 0.81, 1]
plt_colormap=[(1.0000, 1.0000, 1.0000), (0.9961, 0.9020, 0), (1.0000, 0.6980, 0), (1.0000, 0.2980, 0.0039), (0.8471, 0, 0.0039), (0.5882, 0.0196, 0.0196)]
values_obs=np.nanmean(np.nanmean(r2_obs_pred[:,:,:], axis=0), axis=0)
values_model=r2_model_pred[:]
values_hist5=np.nanmean(r2_hist5_pred[:,:], axis=0)
values_hist6=np.nanmean(r2_hist6_pred[:,:], axis=0)
plt_title='Summary: training accuracy'
plt_unit='[R$^2$]'
plt_path="{WK_DIR}/model/PS/summary_prediction_accuracy.eps".format(**os.environ)
plot_and_save_basin_filled_summary(values_obs, values_model, values_hist5, values_hist6, \
                                   basin_points, bins, bins2, plt_colormap, plt_unit, plt_title, plt_path,\
                                   coast_path, closed_fraction)

# summary for T sensitivity
bins = [-30,-15,-12,-9,-6,-3,0,3,6,9,12,15,30]
bins2 = [-60,-15,-12,-9,-6,-3,0,3,6,9,12,15,60]
plt_colormap=[(0.4000, 0, 0, 1),(0.7706, 0, 0, 1),(0.9945, 0.0685, 0.0173, 1),(0.9799, 0.2483, 0.0627, 1),(0.9715, 0.4442, 0.0890, 1),(0.9845, 0.6961, 0.0487, 1),(0.9973, 0.9480, 0.0083, 1),(1.0000, 1.0000, 0.3676, 1),(1.0000, 1.0000, 1.0000, 1),(1.0000, 1.0000, 1.0000, 1),(0.6975, 0.8475, 0.9306, 1),(0.4759, 0.7358, 0.8797, 1),(0.2542, 0.6240, 0.8289, 1),(0.0436, 0.5130, 0.7774, 1),(0.0533, 0.4172, 0.7138, 1),(0.0630, 0.3215, 0.6503, 1),(0.0411, 0.1760, 0.5397, 1),(0, 0, 0.4000, 1)]
values_obs=np.nanmean(np.nanmean(tsens_obs[:, :, :, 0], axis=0), axis=0)
values_model=tsens_model[:, 0]
values_hist5=np.nanmean(tsens_hist5[:, :, 0], axis=0)
values_hist6=np.nanmean(tsens_hist6[:, :, 0], axis=0)
plt_title='Summary: T sensitivity'
plt_unit='[%/K]'
plt_path="{WK_DIR}/model/PS/summary_tsens.eps".format(**os.environ)
plot_and_save_basin_filled_summary(values_obs, values_model, values_hist5, values_hist6, \
                                   basin_points, bins, bins2, plt_colormap, plt_unit, plt_title, plt_path,\
                                   coast_path, closed_fraction)

# summary for P sensitivity
bins=[-3.5, -3, -2.5, -2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2, 2.5, 3, 3.5];
bins2=[-100, -3, -2.5, -2, -1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6, 2, 2.5, 3, 100];
plt_colormap=[(0.4000, 0, 0, 1), (0.7316, 0, 0, 1), (0.9975, 0.0306, 0.0078, 1), (0.9845, 0.1915, 0.0484, 1), (0.9715, 0.3525, 0.0890, 1), (0.9776, 0.5636, 0.0700, 1), (0.9891, 0.7889, 0.0338, 1), (1.0000, 1.0000, 0.0263, 1), (1.0000, 1.0000, 0.4408, 1), (1.0000, 1.0000, 1.0000, 1), (1.0000, 1.0000, 1.0000, 1), (0.7325, 0.8651, 0.9386, 1), (0.5342, 0.7652, 0.8931, 1), (0.3359, 0.6652, 0.8476, 1), (0.1375, 0.5652, 0.8020, 1), (0.0477, 0.4727, 0.7506, 1), (0.0563, 0.3870, 0.6938, 1), (0.0651, 0.3013, 0.6370, 1), (0.0368, 0.1575, 0.5250, 1), (0, 0, 0.4000, 1)]
values_obs=np.nanmean(np.nanmean(psens_obs[:, :, :, 0], axis=0), axis=0)
values_model=psens_model[:, 0]
values_hist5=np.nanmean(psens_hist5[:, :, 0], axis=0)
values_hist6=np.nanmean(psens_hist6[:, :, 0], axis=0)
plt_title='Summary: P sensitivity'
plt_unit='[%/%]'
plt_path="{WK_DIR}/model/PS/summary_psens.eps".format(**os.environ)
plot_and_save_basin_filled_summary(values_obs, values_model, values_hist5, values_hist6, \
                                   basin_points, bins, bins2, plt_colormap, plt_unit, plt_title, plt_path,\
                                   coast_path, closed_fraction)




###########################################
## significant test ##
###########################################
## Are the runoff sensitivities reliable? (Prediction skill of the regression model itself)
# observations, CMIP6 models, target model
nfoc=r2_obs_pred.shape[0]; nens=r2_obs_pred.shape[1];
hval_r2_ia_gobs=np.full(nb,False);
hval_r2_ia_hist6=np.full(nb,False);
hval_r2_ia_model=np.full(nb,False);
r2_ia_sig=significant_pearsonr(np.floor(70/5),0.05)**2
hval_r2_ia_gobs = np.sum(np.reshape(r2_obs_pred,(nfoc*nens,nb),order='F')>r2_ia_sig,axis=0)==nfoc*nens
nmodel6=r2_hist6_pred.shape[0]
for b in range(nb):
    hval_r2_ia_hist6[b] = np.sum(r2_hist6_pred[:,b]>r2_ia_sig,axis=0) == np.nansum(~np.isnan(r2_hist6_pred[:,b]))
hval_r2_ia_model = r2_model_pred > r2_ia_sig
hval_r2_ia = hval_r2_ia_gobs & hval_r2_ia_hist6 & hval_r2_ia_model
ind_r2_sig = np.nonzero(hval_r2_ia)[0]

## Are the runoff sensitivity bias large enough to overcome the uncertainty?
# confidence interval of observational uncertainty
pct90_tsens_obs=np.full((nb,2),np.nan)
pct90_psens_obs=np.full((nb,2),np.nan)
nobs=nfoc*nens
for b in range(nb):
    tsens=np.reshape(tsens_obs[:,:,b,0],(nobs),order='F')
    pct90_tsens_obs[b,:] = (np.percentile(tsens,5),np.percentile(tsens,95))
    psens=np.reshape(psens_obs[:,:,b,0],(nobs),order='F')
    pct90_psens_obs[b,:] = (np.percentile(psens,5),np.percentile(psens,95))

# compare the observational uncertainty to the pre-calculated uncertainty in regression coefficient
def range_difference(a1,a2,b1,b2):
    return (a2<b1) | (b2<a1)
obs=np.nanmean(np.nanmean(tsens_obs[:,:,:,:],axis=0),axis=0)
model=tsens_model
# ind_diff_tsens=np.nonzero(range_difference(obs[:,0],obs[:,0],model[:,1],model[:,2]))[0]
ind_diff_tsens=np.nonzero(range_difference(pct90_tsens_obs[:,0],pct90_tsens_obs[:,1],model[:,1],model[:,2]))[0]
obs=np.nanmean(np.nanmean(psens_obs[:,:,:,:],axis=0),axis=0)
model=psens_model
# ind_diff_psens=np.nonzero(range_difference(obs[:,0],obs[:,0],model[:,1],model[:,2]))[0]
ind_diff_psens=np.nonzero(range_difference(pct90_psens_obs[:,0],pct90_psens_obs[:,1],model[:,1],model[:,2]))[0]


#########################
##  basin information  ##
#########################
fig = plt.figure(figsize=(14, 14))
plt.rcParams.update({'font.size': 12})
h = fig.add_axes([0.05, 0.585, 0.9, 0.38])
# load coastline
lonmap = nc.Dataset(coast_path)['lonmap'][:]
latmap = nc.Dataset(coast_path)['latmap'][:]
h.plot(lonmap, latmap, color=[0.8, 0.8, 0.8, 0], linewidth=0.5)
h.add_patch(patches.Polygon(np.column_stack([lonmap, latmap]), closed=True, facecolor=(0.8, 0.8, 0.8), edgecolor=(0.5, 0.5, 0.5), linestyle='none'))
# Plot basins with basin numbers
for b in range(nb):
    X = [item[0] for item in basin_points[b]]
    Y = [item[1] for item in basin_points[b]]
    # X = X[0:-int(np.floor(len(X)/50))]
    # Y = Y[0:-int(np.floor(len(Y)/50))]
    h.add_patch(patches.Polygon(np.column_stack([X, Y]), closed=True, facecolor=(1, 1, 1), edgecolor=(0.5, 0.5, 0.5), linewidth=0.5))
    center_x = (max(X) + min(X)) / 2
    center_y = (max(Y) + min(Y)) / 2
    h.text(center_x, center_y, str(b+1), color='gray', fontsize=8, horizontalalignment='center', fontweight='bold')
    if b not in ind_r2_sig:
        h.add_patch(patches.Polygon(np.column_stack([X, Y]),closed=True,fill=False, hatch='//', edgecolor=(0.5,0.5,0.5), linewidth=0.1))

if len(ind_diff_tsens) != 0:
    for b in range(len(ind_diff_tsens)):
        X = [item[0] for item in basin_points[ind_diff_tsens[b]]]
        Y = [item[1] for item in basin_points[ind_diff_tsens[b]]]
        center_x = (max(X) + min(X)) / 2
        center_y = (max(Y) + min(Y)) / 2
        h.text(center_x, center_y, str(ind_diff_tsens[b]+1), color='black', fontsize=8, horizontalalignment='center', fontweight='bold')
        h.plot(X, Y, color=(0,0,0), linewidth=1.5)

if len(ind_diff_psens) != 0:
    for b in range(len(ind_diff_psens)):
        X = [item[0] for item in basin_points[ind_diff_psens[b]]]
        Y = [item[1] for item in basin_points[ind_diff_psens[b]]]
        center_x = (max(X) + min(X)) / 2
        center_y = (max(Y) + min(Y)) / 2
        h.text(center_x, center_y, str(ind_diff_psens[b]+1), color='black', fontsize=8, horizontalalignment='center', fontweight='bold')

h.text(-175,-40,'Hatchings: unreliable sensitivity')
h.text(-175,-48,'Black outlines: sig. model bias in T sens.')
h.text(-175,-56,'Black numbers: sig. model bias in P or T sens.')

for b in range(1,34):
    h.text(-180, -70-(b*6), '#' + str(b) + ': ' + str(basin_names[b-1]), color='black', fontsize=12, horizontalalignment='left')
for b in range(34,67):
    h.text(-85, -70-(b-33)*6, '#' + str(b) + ': ' + str(basin_names[b-1]), color='black', fontsize=12, horizontalalignment='left')
for b in range(67,100):
    h.text(0, -70-(b-66)*6, '#' + str(b) + ': ' + str(basin_names[b-1]), color='black', fontsize=12, horizontalalignment='left')
for b in range(100,nb):
    h.text(100, -70-(b-99)*6, '#' + str(b) + ': ' + str(basin_names[b-1]), color='black', fontsize=12, horizontalalignment='left')

h.set_xticks(range(-180, 181, 30))
h.set_xticklabels(['', '', '120°W', '', '60°W', '', '0°', '', '60°E', '', '120°E', '', ''])
h.set_yticks(range(-90, 91, 15))
h.set_yticklabels(['', '', '60°S', '', '30°S', '', '0°', '', '30°N', '', '60°N', '', ''])
h.set_xlim([-180, 180])
h.set_ylim([-60, 80])
# Set title
h.set_title('River basin info. (GRDC Major River Basin of the World)', fontsize=17)
plt_path="{WK_DIR}/obs/PS/basin_info.eps".format(**os.environ)
plt.savefig(plt_path,dpi=300)
plt.close()


########################################################
##  basin specific sensitivities including errorbars  ##
########################################################
nobs=tsens_obs.shape[0]*tsens_obs.shape[1]

# stdt_obs=np.empty((nb,1))
# stdt_hist5=np.empty((nb,1))
# stdt_hist6=np.empty((nb,1))
# stdp_obs=np.empty((nb,1))
# stdp_hist5=np.empty((nb,1))
# stdp_hist6=np.empty((nb,1))
# for b in range(nb):
#     stdt_obs[b]=np.std(np.reshape(tsens_obs[:,:,b,0],(nobs),order='F'))
#     stdt_hist5[b]=np.std(tsens_hist5[:,b,0])
#     stdt_hist6[b]=np.std(tsens_hist6[:,b,0])
#     stdp_obs[b]=np.std(np.reshape(psens_obs[:,:,b,0],(nobs),order='F'))
#     stdp_hist5[b]=np.std(psens_hist5[:,b,0])
#     stdp_hist6[b]=np.std(psens_hist6[:,b,0])

cit_obs=np.empty((nb,1))
cit_hist5=np.empty((nb,1))
cit_hist6=np.empty((nb,1))
cip_obs=np.empty((nb,1))
cip_hist5=np.empty((nb,1))
cip_hist6=np.empty((nb,1))
for b in range(nb):
    cit_obs[b]=get_confidence_interval(np.reshape(tsens_obs[:,:,b,0],(nobs),order='F'),alpha=0.9)
    cit_hist5[b]=get_confidence_interval(tsens_hist5[:,b,0],alpha=0.9)
    cit_hist6[b]=get_confidence_interval(tsens_hist6[:,b,0],alpha=0.9)
    cip_obs[b]=get_confidence_interval(np.reshape(psens_obs[:,:,b,0],(nobs),order='F'),alpha=0.9)
    cip_hist5[b]=get_confidence_interval(psens_hist5[:,b,0],alpha=0.9)
    cip_hist6[b]=get_confidence_interval(psens_hist6[:,b,0],alpha=0.9)

pct50_tsens_obs=np.full((nb),np.nan)
pct90_tsens_obs_err=np.full((nb,2),np.nan)
pct50_psens_obs=np.full((nb),np.nan)
pct90_psens_obs_err=np.full((nb,2),np.nan)
nobs=nfoc*nens
for b in range(nb):
    tsens=np.reshape(tsens_obs[:,:,b,0],(nobs),order='F')
    pct90_tsens_obs_err[b,:] = (np.percentile(tsens,50)-np.percentile(tsens,5), np.percentile(tsens,95)-np.percentile(tsens,50))
    pct50_tsens_obs[b] = np.percentile(tsens,50)
    psens=np.reshape(psens_obs[:,:,b,0],(nobs),order='F')
    pct90_psens_obs_err[b,:] = (np.percentile(psens,50)-np.percentile(psens,5),np.percentile(psens,95)-np.percentile(psens,50))
    pct50_psens_obs[b] = np.percentile(psens,50)

Black=(0.1,0.1,0.1,1);
Orange=(1.0000,0.2695,0,1);
Green=(0.2,0.55,0.2,1);
Blue=(0.1172,0.5625,1.0000,1);
blist = np.arange(0,nb)


# for bi in blist:
for bi in blist:
    print(bi)
    fig = plt.figure(figsize=(9.5, 5))
    plt.rcParams.update({'font.size': 12})

    h1 = fig.add_axes([0.07, 0.1, 0.31, 0.7])
    h1.plot(1, np.nanmean(np.nanmean(tsens_obs[:, :, bi, 0], axis=0), axis=0), 'o', color=Black, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.plot(2, tsens_model[bi, 0], 'o', color=Orange, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.plot(3, np.nanmean(tsens_hist5[:, bi, 0], axis=0), 'o', color=Green, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.plot(4, np.nanmean(tsens_hist6[:, bi, 0], axis=0), 'o', color=Blue, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    legend_labels = ['GRUN', 'MODEL', 'CMIP5 hist', 'CMIP6 hist']
    hl = fig.legend(legend_labels, loc='upper right', fontsize=11, bbox_to_anchor=(0.86, 0.75, 0.0875, 0.0475))
    h1.plot([0, 5],[0, 0], ':k', linewidth=1)
    error=np.nanmean(np.nanmean(tsens_obs[:,:,bi,2] - tsens_obs[:,:,bi,0], axis=0), axis=0)
    h1.errorbar(1, np.nanmean(np.nanmean(tsens_obs[:, :, bi, 0], axis=0), axis=0), error, color=Black, capsize=5)
    # h1.errorbar(1, np.nanmean(np.nanmean(tsens_obs[:, :, bi, 0], axis=0), axis=0), cit_obs[bi], color=Black, capsize=5)
    h1.plot(np.ones((tsens_obs.shape[0], 1)), tsens_obs[:, :, bi, 0], 'o', color=Black, markersize=2, markerfacecolor=Black)
    h1.plot(1, np.nanmean(np.nanmean(tsens_obs[:, :, bi, 0], axis=0), axis=0), 'o', color=Black, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.errorbar(1.2, pct50_tsens_obs[bi], [[pct90_tsens_obs_err[bi,0]], [pct90_tsens_obs_err[bi,1]]], color=(0.5,0.5,0.5,1), capsize=5, linestyle='')
    h1.errorbar(2, tsens_model[bi, 0], tsens_model[bi, 2] - tsens_model[bi, 0], color=Orange, capsize=5)
    h1.plot(2, tsens_model[bi, 0], 'o', color=Orange, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.errorbar(3, np.nanmean(tsens_hist5[:, bi, 0], axis=0), cit_hist5[bi], color=Green, capsize=5)
    h1.plot(np.ones((tsens_hist5.shape[0], 1))*3, tsens_hist5[:, bi, 0], 'o', color=Green, markersize=2, markerfacecolor=Green)
    h1.plot(3, np.nanmean(tsens_hist5[:, bi, 0], axis=0), 'o', color=Green, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.errorbar(4, np.nanmean(tsens_hist6[:, bi, 0], axis=0), cit_hist6[bi], color=Blue, capsize=5)
    h1.plot(np.ones((tsens_hist6.shape[0], 1))*4, tsens_hist6[:, bi, 0], 'o', color=Blue, markersize=2, markerfacecolor=Blue)
    h1.plot(4, np.nanmean(tsens_hist6[:, bi, 0], axis=0), 'o', color=Blue, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h1.set_xlim(0, 5)
    h1.set_xticks([1, 2, 3, 4])
    h1.set_xticklabels(['OBS', 'MODEL', 'CMIP5', 'CMIP6'],fontsize=11)
    h1.set_ylabel('[%/K]', fontsize=12)
    h1.set_title('T sensitivity', fontsize=16)
    ymax = max(h1.get_ylim())
    ymin = min(h1.get_ylim())
    h1.text(6, ymax + (ymax - ymin) * 0.19, f'Basin {bi+1}: {basin_names[bi]} ({syr_sens}-{eyr_sens})', fontsize=17, ha='center')

    h2 = fig.add_axes([0.47, 0.1, 0.31, 0.7])
    # h2.plot([0, 5],[0, 0], ':k', linewidth=1)
    error=np.nanmean(np.nanmean(psens_obs[:,:,bi,2] - psens_obs[:,:,bi,0], axis=0), axis=0)
    h2.errorbar(1, np.nanmean(np.nanmean(psens_obs[:, :, bi, 0], axis=0), axis=0), error, color=Black, capsize=5)
    # h2.errorbar(1, np.nanmean(np.nanmean(psens_obs[:, :, bi, 0], axis=0), axis=0), cip_obs[bi], color=Black, capsize=5)
    h2.plot(np.ones((psens_obs.shape[0], 1)), psens_obs[:, :, bi, 0], 'o', color=Black, markersize=2, markerfacecolor=Black)
    h2.plot(1, np.nanmean(np.nanmean(psens_obs[:, :, bi, 0], axis=0), axis=0), 'o', color=Black, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h2.errorbar(1.2, pct50_psens_obs[bi], [[pct90_psens_obs_err[bi,0]], [pct90_psens_obs_err[bi,1]]], color=(0.5,0.5,0.5,1), capsize=5, linestyle='')
    h2.plot(np.ones((psens_obs.shape[0], 1)), psens_obs[:, :, bi, 0], 'o', color=Black, markersize=2, markerfacecolor=Black)
    h2.plot(1, np.nanmean(np.nanmean(psens_obs[:, :, bi, 0], axis=0), axis=0), 'o', color=Black, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h2.errorbar(2, psens_model[bi, 0], psens_model[bi, 2] - psens_model[bi, 0], color=Orange, capsize=5)
    h2.plot(2, psens_model[bi, 0], 'o', color=Orange, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h2.errorbar(3, np.nanmean(psens_hist5[:, bi, 0], axis=0), cip_hist5[bi], color=Green, capsize=5)
    h2.plot(np.ones((psens_hist5.shape[0], 1))*3, psens_hist5[:, bi, 0], 'o', color=Green, markersize=2, markerfacecolor=Green)
    h2.plot(3, np.nanmean(psens_hist5[:, bi, 0], axis=0), 'o', color=Green, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h2.errorbar(4, np.nanmean(psens_hist6[:, bi, 0], axis=0), cip_hist6[bi], color=Blue, capsize=5)
    h2.plot(np.ones((psens_hist6.shape[0], 1))*4, psens_hist6[:, bi, 0], 'o', color=Blue, markersize=2, markerfacecolor=Blue)
    h2.plot(4, np.nanmean(psens_hist6[:, bi, 0], axis=0), 'o', color=Blue, markersize=9, markeredgewidth=2, markerfacecolor=(1, 1, 1, 1))
    h2.set_xlim(0, 5)
    h2.set_xticks([1, 2, 3, 4])
    h2.set_xticklabels(['OBS', 'MODEL', 'CMIP5', 'CMIP6'],fontsize=11)
    h2.set_ylabel('[%/%]', fontsize=12)
    h2.set_title('P sensitivity', fontsize=16)
    basin_number=bi+1;
    plt_path=os.environ["WK_DIR"] + "/model/PS/basin_specific" + str(basin_number) + ".eps"
    plt.savefig(plt_path)
    plt.close()




