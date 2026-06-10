####################################################################
## import libraries
import os
import numpy as np
import cartopy.io.shapereader as shpreader
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as colors
from sklearn.linear_model import LinearRegression
import scipy.stats as stats
import scipy.io as sio

####################################################################
## Define functions
## calculate moving average! (smoothing)
def moving_avg(x_1d,n_mw):
    nt=len(x_1d)
    weight = np.ones((n_mw))/n_mw
    n_delete=int((n_mw)/2);
    smoothed=np.convolve(x_1d,weight,mode='same')
    if n_delete != 0:
        smoothed[0:n_delete]=np.nan
        smoothed[-n_delete:nt]=np.nan
    return smoothed

####################################################################
## file path
dpath="C:/runoff_mrb_grdc3/"
figpath="C:/Users/reapr/내 드라이브/Research/runoff_project/MDTF/ver241202/runoff_sensitivities";
os.makedirs(figpath, exist_ok=True)

## load basin info
basin_path=dpath + 'basins_pp.mat'
matfile=sio.loadmat(basin_path)
basins=matfile['basins']
basin_names_raw=matfile['basin_names'][0]
nbasin=len(basins)-4
for b in range(nbasin):
    point=[(x,y) for x,y in zip(list(basins[b][0][2][0]),list(basins[b][0][3][0]))]
    if b==0:
        basin_points=[point[0::10]]
        basin_names=[basin_names_raw[0][0]]
    else:
        basin_points.extend([point[0::10]])
        basin_names.extend([basin_names_raw[b][0]])

## function for runoff sensitivity calculation
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
        a1=np.nan; a2=(np.nan,np.nan); b1=np.nan; b2=(np.nan,np.nan); c1=np.nan; c2=(np.nan,np.nan); r2=np.nan;
        return a1, a2, b1, b2, c1, c2, r2


######################################################################
# start and end year for sensitivity calculation
syr_sens_cri=1945
eyr_sens_cri=2014

######################################################################
# target moving windows
n_mw=[1,3,5,9]
tmw=2 # mw=5 year is target moving window

#####################
##      CMIP6      ##
#####################
##############################
##      HIST6 + SSP245      ##
##############################
## load variables
matfile = sio.loadmat(dpath + "tasb_wy_c2f6_cmip6.mat")
tasb_wy_c2f6 = matfile["tasb_wy_c2f6"][:,:,:]
matfile = sio.loadmat(dpath + "prb_wy_c2f6_cmip6.mat")
prb_wy_c2f6 = matfile["prb_wy_c2f6"][:,:,:]
matfile = sio.loadmat(dpath + "evspsblb_wy_c2f6_cmip6.mat")
evspsblb_wy_c2f6 = matfile["evspsblb_wy_c2f6"][:,:,:]
matfile = sio.loadmat(dpath + "mrrob_wy_c2f6_cmip6.mat")
mrrob_wy_c2f6 = matfile["mrrob_wy_c2f6"][:,:,:]
model_cmip6 = matfile["model_cmip6"][:][0]
syr_c2f6 = matfile["syr_c2f6"][0]
eyr_c2f6 = matfile["eyr_c2f6"][0]
nmodel_cmip6 = len(model_cmip6)
matfile = sio.loadmat(dpath + "prb_grun_1903_2012_intp.mat")
area_basins = np.squeeze(matfile["area_basins"])

################################################################
# water budget closure for historical period (picontrol is similar)
# use the model with all variables we need
hval_available=np.isnan(np.mean(mrrob_wy_c2f6[:,:,3],axis=1))|np.isnan(np.mean(prb_wy_c2f6[:,:,3],axis=1))|np.isnan(np.mean(evspsblb_wy_c2f6[:,:,3],axis=1))|np.isnan(np.mean(tasb_wy_c2f6[:,:,3],axis=1));
nanind_model_c2f6=np.nonzero(hval_available)
tasb_wy_c2f6[nanind_model_c2f6,:,:]=np.nan
prb_wy_c2f6[nanind_model_c2f6,:,:]=np.nan
evspsblb_wy_c2f6[nanind_model_c2f6,:,:]=np.nan
mrrob_wy_c2f6[nanind_model_c2f6,:,:]=np.nan

# check the errors
pmeb_model = np.mean(prb_wy_c2f6[:,0:165,0:nbasin] - evspsblb_wy_c2f6[:,0:165,0:nbasin], axis=1)
error_val_c2f6 = (pmeb_model - np.mean(mrrob_wy_c2f6[:,0:165,0:nbasin], axis=1)) / np.mean(mrrob_wy_c2f6[:,0:165,0:nbasin], axis=1)
error_val_c2f6[nanind_model_c2f6,:]=np.nan
pval = 0.1
closed_fraction_c2f6=np.nansum( np.abs(error_val_c2f6)<pval ,axis=1) / (nbasin)
a=np.tile(area_basins[0:nbasin][:,np.newaxis],(1,nmodel_cmip6)).T
closed_area_fraction_c2f6=np.nansum( (np.abs(error_val_c2f6)<pval)*a ,axis=1) / np.nansum( a ,axis=1)
closed_nmodel_c2f6=np.nansum(np.abs(error_val_c2f6)<pval,axis=0)
# basin/model with negative values
negative_fraction_c2f6=np.sum(mrrob_wy_c2f6[:,0:165,0:nbasin]<0,axis=1)/165

# indices info for unclosed/unavailable models
nanind_c2f6=np.nonzero(np.logical_or(hval_available,closed_area_fraction_c2f6<0.6))
mind_c2f6=np.arange(nmodel_cmip6)
mind_c2f6=np.delete(mind_c2f6,nanind_c2f6)
mind_c2f6_available=np.arange(nmodel_cmip6)
mind_c2f6_available=np.delete(mind_c2f6_available,nanind_model_c2f6)
mind_negative_c2f6=np.nonzero(np.nanmean(negative_fraction_c2f6[:,:],axis=1)>0.001)[0]
nmodel_c2f6_closed=len(mind_c2f6)
nmodel_c2f6_available=len(mind_c2f6_available)
print(f"c2f6: {nmodel_c2f6_closed}/{nmodel_c2f6_available}")
print(f"negative values in c2f6 closed: {len(np.intersect1d(mind_negative_c2f6,mind_c2f6))}")

# incorporate HIST/SSP model info
nanind_cmip6=nanind_c2f6
mind_cmip6_available=mind_c2f6_available
mind_cmip6=mind_c2f6
mind_cmip6=np.setdiff1d(mind_cmip6,69) # 69-TaiESM1's IA R2 is very low. P cannot explain R variability among 58/87 basins
mind_cmip6=np.setdiff1d(mind_cmip6,34) # 34-FGOALS-g3's IA R2 is very low. P cannot explain R variability among 29/87 basins, and R2 values are in generall too weak
mind_cmip6=np.setdiff1d(mind_cmip6,57) # 57-MIROC-ES2L has starnge value for northern sierras - due to low resolution, coastal regions have strange value
nmodel_cmip6_available=len(mind_cmip6_available)
nmodel_cmip6_closed=len(mind_cmip6)
print(f"HIST6/SSP245: {nmodel_cmip6_closed}/{nmodel_cmip6_available}")
closed_fraction_cmip6=closed_fraction_c2f6
closed_area_fraction_cmip6=closed_area_fraction_c2f6
closed_nmodel_cmip6=closed_nmodel_c2f6
############################################
temp2=negative_fraction_c2f6>0.1
ind_c2f6_nm=np.nonzero(temp2)[0]
ind_c2f6_nb=np.nonzero(temp2)[1]

for mind,bind in zip(ind_c2f6_nm,ind_c2f6_nb):
    # display(f'c2f6 {model_cmip6[mind]}({mind}); {basin_names[bind]}({bind})')
    # display(f'c2f6 mean Q: {np.nanmean(mrrob_wy_c2f6[mind,0:150,bind])}')
    tasb_wy_c2f6[mind,:,bind]=np.nan
    prb_wy_c2f6[mind,:,bind]=np.nan
    evspsblb_wy_c2f6[mind,:,bind]=np.nan
    mrrob_wy_c2f6[mind,:,bind]=np.nan

# assign nan to unclosed models
tasb_wy_c2f6[nanind_cmip6,:,:]=np.nan
prb_wy_c2f6[nanind_cmip6,:,:]=np.nan
evspsblb_wy_c2f6[nanind_cmip6,:,:]=np.nan
mrrob_wy_c2f6[nanind_cmip6,:,:]=np.nan


############################################################################
def duplicated_fraction(data):
    ndiff_frac=(len(data)-len(set(data)))/len(data)
    return ndiff_frac  # No duplicates found

s=0
for m in range(nmodel_cmip6):
    for b in range(nbasin):
        val=duplicated_fraction(mrrob_wy_c2f6[m,:,b])
        if val>0.1:
            tasb_wy_c2f6[m,:,b]=np.nan
            prb_wy_c2f6[m,:,b]=np.nan
            evspsblb_wy_c2f6[m,:,b]=np.nan
            mrrob_wy_c2f6[m,:,b]=np.nan
            s=s+1

############################################################################
## calculate sensitivity
# moving average
nmw=len(n_mw)
tasb_wym_c2f6 = np.full(tasb_wy_c2f6.shape+(len(n_mw),),np.nan);
prb_wym_c2f6 = np.full(prb_wy_c2f6.shape+(len(n_mw),),np.nan);
evspsblb_wym_c2f6 = np.full(evspsblb_wy_c2f6.shape+(len(n_mw),),np.nan);
mrrob_wym_c2f6 = np.full(mrrob_wy_c2f6.shape+(len(n_mw),),np.nan);
for m in mind_cmip6:
    for b in range(nbasin):
        for n in range(len(n_mw)):
            tasb_wym_c2f6[m,:,b,n] = moving_avg(tasb_wy_c2f6[m,:,b],n_mw[n])
            prb_wym_c2f6[m,:,b,n] = moving_avg(prb_wy_c2f6[m,:,b],n_mw[n])
            evspsblb_wym_c2f6[m,:,b,n] = moving_avg(evspsblb_wy_c2f6[m,:,b],n_mw[n])
            mrrob_wym_c2f6[m,:,b,n] = moving_avg(mrrob_wy_c2f6[m,:,b],n_mw[n])
yrs=np.arange(syr_c2f6,eyr_c2f6)
inds1=int(np.nonzero(yrs==syr_sens_cri)[0]); inde1=int(np.nonzero(yrs==eyr_sens_cri)[0])+1;

## get long-term average for % anomaly
prb_hist6_mw=np.mean(np.tile(prb_wy_c2f6[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
tasb_hist6_mw=np.mean(np.tile(tasb_wy_c2f6[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
mrrob_hist6_mw=np.mean(np.tile(mrrob_wy_c2f6[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
evspsblb_hist6_mw=np.mean(np.tile(evspsblb_wy_c2f6[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);

# yearly anomalies for regression analysis
nt=prb_wym_c2f6.shape[1]
aprb_wym_c2f6 = prb_wym_c2f6[:,:,:,:] - np.transpose(np.tile(prb_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
atasb_wym_c2f6 = tasb_wym_c2f6[:,:,:,:] - np.transpose(np.tile(tasb_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
amrrob_wym_c2f6 = mrrob_wym_c2f6[:,:,:,:] - np.transpose(np.tile(mrrob_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
aevspsblb_wym_c2f6 = evspsblb_wym_c2f6[:,:,:,:] - np.transpose(np.tile(evspsblb_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));

# percent anomaly
aprb_wym_c2f6_pct = aprb_wym_c2f6 / np.transpose(np.tile(prb_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;
amrrob_wym_c2f6_pct = amrrob_wym_c2f6 / np.transpose(np.tile(mrrob_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;
aevspsblb_wym_c2f6_pct = aevspsblb_wym_c2f6 / np.transpose(np.tile(evspsblb_hist6_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;

## get sensitivities
# initailizations
psens_hist6=np.full((len(mind_cmip6),nbasin,3),np.nan)
tsens_hist6=np.full((len(mind_cmip6),nbasin,3),np.nan)
intsens_hist6=np.full((len(mind_cmip6),nbasin,3),np.nan)
r2_ia_int_hist6=np.full((len(mind_cmip6),nbasin),np.nan)
r2_ia_hist6=np.full((len(mind_cmip6),nbasin),np.nan)
# calculate runoff sensitivity
yrs=np.arange(syr_c2f6,eyr_c2f6)
inds=int(np.nonzero(yrs==syr_sens_cri)[0]); inde=int(np.nonzero(yrs==eyr_sens_cri)[0])+1;
m2=0
for m in mind_cmip6:
    for b in range(nbasin):
        a1, a2, b1, b2, c1, c2, r2 = runoff_sens_reg(amrrob_wym_c2f6_pct[m,inds:inde,b,tmw], aprb_wym_c2f6_pct[m,inds:inde,b,tmw], atasb_wym_c2f6[m,inds:inde,b,tmw], mw=n_mw[tmw])

        psens_hist6[m2,b,0] = a1
        psens_hist6[m2,b,1:3] = a2
        tsens_hist6[m2,b,0] = b1
        tsens_hist6[m2,b,1:3] = b2
        intsens_hist6[m2,b,0] = c1
        intsens_hist6[m2,b,1:3] = c2
        r2_ia_int_hist6[m2,b] = r2

        if not np.isnan(a1):
            pred = a1*aprb_wym_c2f6_pct[m,inds:inde,b,tmw] + b1*atasb_wym_c2f6[m,inds:inde,b,tmw]
            corr, _ = stats.pearsonr(pred,amrrob_wym_c2f6_pct[m,inds:inde,b,tmw])
            r2_ia_hist6[m2,b]= corr**2
    m2=m2+1



######################################################################
# start and end year for sensitivity calculation
syr_sens_cri=1945
eyr_sens_cri=2014

#####################
##      CMIP5      ##
#####################
##############################
##      HIST5 + RCP45      ##
##############################
## load variables
matfile = sio.loadmat(dpath + "tasb_wy_c2f5_cmip5.mat")
tasb_wy_c2f5 = matfile["tasb_wy_c2f5"][:,:,:]
matfile = sio.loadmat(dpath + "prb_wy_c2f5_cmip5.mat")
prb_wy_c2f5 = matfile["prb_wy_c2f5"][:,:,:]
matfile = sio.loadmat(dpath + "evspsblb_wy_c2f5_cmip5.mat")
evspsblb_wy_c2f5 = matfile["evspsblb_wy_c2f5"][:,:,:]
matfile = sio.loadmat(dpath + "mrrob_wy_c2f5_cmip5.mat")
mrrob_wy_c2f5 = matfile["mrrob_wy_c2f5"][:,:,:]
model_cmip5 = matfile["model_cmip5"][:][0]
syr_c2f5 = matfile["syr_c2f5"][0]
eyr_c2f5 = matfile["eyr_c2f5"][0]
nmodel_cmip5 = len(model_cmip5)

################################################################
# water budget closure for historical period (picontrol is similar)
# use the model with all variables we need
hval_available=np.isnan(np.mean(mrrob_wy_c2f5[:,:,3],axis=1))|np.isnan(np.mean(prb_wy_c2f5[:,:,3],axis=1))|np.isnan(np.mean(evspsblb_wy_c2f5[:,:,3],axis=1))|np.isnan(np.mean(tasb_wy_c2f5[:,:,3],axis=1));
nanind_model_c2f5=np.nonzero(hval_available)
tasb_wy_c2f5[nanind_model_c2f5,:,:]=np.nan
prb_wy_c2f5[nanind_model_c2f5,:,:]=np.nan
evspsblb_wy_c2f5[nanind_model_c2f5,:,:]=np.nan
mrrob_wy_c2f5[nanind_model_c2f5,:,:]=np.nan

# check the errors
pmeb_model = np.mean(prb_wy_c2f5[:,0:165,0:nbasin] - evspsblb_wy_c2f5[:,0:165,0:nbasin], axis=1)
error_val_c2f5 = (pmeb_model - np.mean(mrrob_wy_c2f5[:,0:165,0:nbasin], axis=1)) / np.mean(mrrob_wy_c2f5[:,0:165,0:nbasin], axis=1)
error_val_c2f5[nanind_model_c2f5,:]=np.nan
pval = 0.1
closed_fraction_c2f5=np.nansum( np.abs(error_val_c2f5)<pval ,axis=1) / (nbasin)
a=np.tile(area_basins[0:nbasin][:,np.newaxis],(1,nmodel_cmip5)).T
closed_area_fraction_c2f5=np.nansum( (np.abs(error_val_c2f5)<pval)*a ,axis=1) / np.nansum( a ,axis=1)
closed_nmodel_c2f5=np.nansum(np.abs(error_val_c2f5)<pval,axis=0)
# basin/model with negative values
negative_fraction_c2f5=np.sum(mrrob_wy_c2f5[:,0:165,0:nbasin]<0,axis=1)/165

# indices info for unclosed/unavailable models
nanind_c2f5=np.nonzero(np.logical_or(hval_available,closed_area_fraction_c2f5<0.6))
mind_c2f5=np.arange(nmodel_cmip5)
mind_c2f5=np.delete(mind_c2f5,nanind_c2f5)
mind_c2f5_available=np.arange(nmodel_cmip5)
mind_c2f5_available=np.delete(mind_c2f5_available,nanind_model_c2f5)
mind_negative_c2f5=np.nonzero(np.nanmean(negative_fraction_c2f5[:,:],axis=1)>0.001)[0]
nmodel_c2f5_closed=len(mind_c2f5)
nmodel_c2f5_available=len(mind_c2f5_available)
print(f"c2f5: {nmodel_c2f5_closed}/{nmodel_c2f5_available}")
print(f"negative values in c2f5 closed: {len(np.intersect1d(mind_negative_c2f5,mind_c2f5))}")

# incorporate PI/HIST/SSP model info
nanind_cmip5=nanind_c2f5
mind_cmip5_available=mind_c2f5_available
mind_cmip5=mind_c2f5
mind_cmip5=np.setdiff1d(mind_cmip5,12) # 12-CSIRO-Mk3-6-0, continuous 0 values for many basins
nmodel_cmip5_available=len(mind_cmip5_available)
nmodel_cmip5_closed=len(mind_cmip5)
print(f"HIST6/SSP245: {nmodel_cmip5_closed}/{nmodel_cmip5_available}")
closed_fraction_cmip5=closed_fraction_c2f5
closed_area_fraction_cmip5=closed_area_fraction_c2f5
closed_nmodel_cmip5=closed_nmodel_c2f5
############################################
temp2=negative_fraction_c2f5>0.1
ind_c2f5_nm=np.nonzero(temp2)[0]
ind_c2f5_nb=np.nonzero(temp2)[1]
for mind,bind in zip(ind_c2f5_nm,ind_c2f5_nb):
    # display(f'c2f5 {model_cmip5[mind]}({mind}); {basin_names[bind]}({bind})')
    # display(f'c2f5 mean Q: {np.nanmean(mrrob_wy_c2f5[mind,0:150,bind])}')
    tasb_wy_c2f5[mind,:,bind]=np.nan
    prb_wy_c2f5[mind,:,bind]=np.nan
    evspsblb_wy_c2f5[mind,:,bind]=np.nan
    mrrob_wy_c2f5[mind,:,bind]=np.nan

# assign nan to unclosed models
tasb_wy_c2f5[nanind_cmip5,:,:]=np.nan
prb_wy_c2f5[nanind_cmip5,:,:]=np.nan
evspsblb_wy_c2f5[nanind_cmip5,:,:]=np.nan
mrrob_wy_c2f5[nanind_cmip5,:,:]=np.nan

############################################################################
def duplicated_fraction(data):
    ndiff_frac=(len(data)-len(set(data)))/len(data)
    return ndiff_frac  # No duplicates found

s=0
for m in range(nmodel_cmip5):
    for b in range(nbasin):
        val=duplicated_fraction(mrrob_wy_c2f5[m,:,b])
        if val>0.1:
            tasb_wy_c2f5[m,:,b]=np.nan
            prb_wy_c2f5[m,:,b]=np.nan
            evspsblb_wy_c2f5[m,:,b]=np.nan
            mrrob_wy_c2f5[m,:,b]=np.nan
            s=s+1

############################################################################
## calculate sensitivity
# moving average
nmw=len(n_mw)
tasb_wym_c2f5 = np.full(tasb_wy_c2f5.shape+(len(n_mw),),np.nan);
prb_wym_c2f5 = np.full(prb_wy_c2f5.shape+(len(n_mw),),np.nan);
evspsblb_wym_c2f5 = np.full(evspsblb_wy_c2f5.shape+(len(n_mw),),np.nan);
mrrob_wym_c2f5 = np.full(mrrob_wy_c2f5.shape+(len(n_mw),),np.nan);
for m in mind_cmip5:
    for b in range(nbasin):
        for n in range(len(n_mw)):
            tasb_wym_c2f5[m,:,b,n] = moving_avg(tasb_wy_c2f5[m,:,b],n_mw[n])
            prb_wym_c2f5[m,:,b,n] = moving_avg(prb_wy_c2f5[m,:,b],n_mw[n])
            evspsblb_wym_c2f5[m,:,b,n] = moving_avg(evspsblb_wy_c2f5[m,:,b],n_mw[n])
            mrrob_wym_c2f5[m,:,b,n] = moving_avg(mrrob_wy_c2f5[m,:,b],n_mw[n])
yrs=np.arange(syr_c2f5,eyr_c2f5)
inds1=int(np.nonzero(yrs==syr_sens_cri)[0]); inde1=int(np.nonzero(yrs==eyr_sens_cri)[0])+1;

## get long-term average for % anomaly
prb_hist5_mw=np.mean(np.tile(prb_wy_c2f5[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
tasb_hist5_mw=np.mean(np.tile(tasb_wy_c2f5[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
mrrob_hist5_mw=np.mean(np.tile(mrrob_wy_c2f5[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);
evspsblb_hist5_mw=np.mean(np.tile(evspsblb_wy_c2f5[:,inds1:inde1,:,np.newaxis],(1,1,1,nmw)),axis=1);

# yearly anomalies for regression analysis
nt=prb_wym_c2f5.shape[1]
aprb_wym_c2f5 = prb_wym_c2f5[:,:,:,:] - np.transpose(np.tile(prb_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
atasb_wym_c2f5 = tasb_wym_c2f5[:,:,:,:] - np.transpose(np.tile(tasb_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
amrrob_wym_c2f5 = mrrob_wym_c2f5[:,:,:,:] - np.transpose(np.tile(mrrob_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));
aevspsblb_wym_c2f5 = evspsblb_wym_c2f5[:,:,:,:] - np.transpose(np.tile(evspsblb_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2));

# percent anomaly
aprb_wym_c2f5_pct = aprb_wym_c2f5 / np.transpose(np.tile(prb_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;
amrrob_wym_c2f5_pct = amrrob_wym_c2f5 / np.transpose(np.tile(mrrob_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;
aevspsblb_wym_c2f5_pct = aevspsblb_wym_c2f5 / np.transpose(np.tile(evspsblb_hist5_mw[:,:,:,np.newaxis],(1,1,1,nt)),(0,3,1,2)) * 100;

## get sensitivities
# initailizations
psens_hist5=np.full((len(mind_cmip5),nbasin,3),np.nan)
tsens_hist5=np.full((len(mind_cmip5),nbasin,3),np.nan)
intsens_hist5=np.full((len(mind_cmip5),nbasin,3),np.nan)
r2_ia_int_hist5=np.full((len(mind_cmip5),nbasin),np.nan)
r2_ia_hist5=np.full((len(mind_cmip5),nbasin),np.nan)
# calculate runoff sensitivity
yrs=np.arange(syr_c2f5,eyr_c2f5)
inds=int(np.nonzero(yrs==syr_sens_cri)[0]); inde=int(np.nonzero(yrs==eyr_sens_cri)[0])+1;
m2=0
for m in mind_cmip5:
    for b in range(nbasin):
        a1, a2, b1, b2, c1, c2, r2 = runoff_sens_reg(amrrob_wym_c2f5_pct[m,inds:inde,b,tmw], aprb_wym_c2f5_pct[m,inds:inde,b,tmw], atasb_wym_c2f5[m,inds:inde,b,tmw], mw=n_mw[tmw])

        psens_hist5[m2,b,0] = a1
        psens_hist5[m2,b,1:3] = a2
        tsens_hist5[m2,b,0] = b1
        tsens_hist5[m2,b,1:3] = b2
        intsens_hist5[m2,b,0] = c1
        intsens_hist5[m2,b,1:3] = c2
        r2_ia_int_hist5[m2,b] = r2

        if not np.isnan(a1):
            pred = a1*aprb_wym_c2f5_pct[m,inds:inde,b,tmw] + b1*atasb_wym_c2f5[m,inds:inde,b,tmw]
            corr, _ = stats.pearsonr(pred,amrrob_wym_c2f5_pct[m,inds:inde,b,tmw])
            r2_ia_hist5[m2,b]= corr**2
    m2=m2+1


######################################################################
# start and end year for sensitivity calculation
syr_sens_cri=1945
eyr_sens_cri=2014

#####################################################
##      OBS (GRUN + [HADCRUT, GPCC, ERA5-land])    ##
#####################################################
## load data
filename=f'{dpath}tasb_wy_obs2.mat'
matfile=sio.loadmat(filename)
tasb_wy_obs2=matfile['tasb_wy_obs2'][0:5,:,:]
syr_obs=matfile['syr_obs'][0]
eyr_obs=matfile['eyr_obs'][0]

filename=f'{dpath}prb_wy_obs2.mat'
matfile=sio.loadmat(filename)
prb_wy_obs2=matfile['prb_wy_obs2'][0:5,:,:]

filename=f'{dpath}mrrob_wy_obs2_ens.mat'
matfile=sio.loadmat(filename)
mrrob_wy_obs2=matfile['mrrob_wy_obs2_ens'][0:5,:,:,:]
nfoc=mrrob_wy_obs2.shape[0]
nens=mrrob_wy_obs2.shape[1]

## do moving average
nmw=len(n_mw)
tasb_wym_obs2 = np.full(tasb_wy_obs2.shape+(len(n_mw),),np.nan);
prb_wym_obs2 = np.full(prb_wy_obs2.shape+(len(n_mw),),np.nan);
for f in range(nfoc):
    for b in range(nbasin):
        for w in range(len(n_mw)):
            tasb_wym_obs2[f,:,b,w] = moving_avg(tasb_wy_obs2[f,:,b],n_mw[w])
            prb_wym_obs2[f,:,b,w] = moving_avg(prb_wy_obs2[f,:,b],n_mw[w])

mrrob_wym_obs2 = np.full(mrrob_wy_obs2.shape+(len(n_mw),),np.nan);
for f in range(nfoc):
    for e in range(nens):
        for b in range(nbasin):
            for w in range(len(n_mw)):
                mrrob_wym_obs2[f,e,:,b,w] = moving_avg(mrrob_wy_obs2[f,e,:,b],n_mw[w])

## get % anomalies
nyr=prb_wy_obs2.shape[1]
yrs=np.arange(syr_obs,eyr_obs)
inds=int(np.nonzero(yrs==syr_sens_cri)[0]); inde=int(np.nonzero(yrs==eyr_sens_cri)[0])+1;

prb_wym_obs2_mean=np.tile(np.nanmean(prb_wy_obs2[:,inds:inde,:],axis=1)[:,:,np.newaxis],(1,1,nmw));
tasb_wym_obs2_mean=np.tile(np.nanmean(tasb_wy_obs2[:,inds:inde,:],axis=1)[:,:,np.newaxis],(1,1,nmw));
mrrob_wym_obs2_mean=np.tile(np.nanmean(mrrob_wy_obs2[:,:,inds:inde,:],axis=2)[:,:,:,np.newaxis],(1,1,nmw));

aprb_wym_gobs = prb_wym_obs2[:,:,:,:] - np.transpose(np.tile(prb_wym_obs2_mean[:,:,:,np.newaxis],(1,1,1,nyr)),(0,3,1,2));
atasb_wym_gobs = tasb_wym_obs2[:,:,:,:] - np.transpose(np.tile(tasb_wym_obs2_mean[:,:,:,np.newaxis],(1,1,1,nyr)),(0,3,1,2));
amrrob_wym_gobs = mrrob_wym_obs2[:,:,:,:,:] - np.transpose(np.tile(mrrob_wym_obs2_mean[:,:,:,:,np.newaxis],(1,1,1,1,nyr)),(0,1,4,2,3));
aprb_wym_gobs_pct = aprb_wym_gobs / np.transpose(np.tile(prb_wym_obs2_mean[:,:,:,np.newaxis],(1,1,1,nyr)),(0,3,1,2)) * 100;
amrrob_wym_gobs_pct = amrrob_wym_gobs / np.transpose(np.tile(mrrob_wym_obs2_mean[:,:,:,:,np.newaxis],(1,1,1,1,nyr)),(0,1,4,2,3)) * 100;


psens_obs=np.full((nfoc-1,nens,nbasin,3),np.nan)
tsens_obs=np.full((nfoc-1,nens,nbasin,3),np.nan)
intsens_obs=np.full((nfoc-1,nens,nbasin,3),np.nan)
r2_ia_int_obs=np.full((nfoc-1,nens,nbasin),np.nan)
r2_ia_obs=np.full((nfoc-1,nens,nbasin),np.nan)
# calculate runoff sensitivity
f2=0
for f in [0,1,3,4]: # skip GSWP3
    print(f'forcing: {f}')
    for e in range(nens):
        for b in range(nbasin):
            a1, a2, b1, b2, c1, c2, r2 = runoff_sens_reg(amrrob_wym_gobs_pct[f,e,inds:inde,b,tmw], aprb_wym_gobs_pct[f,inds:inde,b,tmw], atasb_wym_gobs[f,inds:inde,b,tmw], mw=n_mw[tmw])

            psens_obs[f2,e,b,0] = a1
            psens_obs[f2,e,b,1:3] = a2
            tsens_obs[f2,e,b,0] = b1
            tsens_obs[f2,e,b,1:3] = b2
            intsens_obs[f2,e,b,0] = c1
            intsens_obs[f2,e,b,1:3] = c2
            r2_ia_int_obs[f2,e,b] = r2

            if not np.isnan(a1):
                pred = a1*aprb_wym_gobs_pct[f,inds:inde,b,tmw] + b1*atasb_wym_gobs[f,inds:inde,b,tmw]
                corr, _ = stats.pearsonr(pred,amrrob_wym_gobs_pct[f,e,inds:inde,b,tmw])
                r2_ia_obs[f2,e,b]= corr**2
    f2=f2+1



################################################################
## save netcdf file #######
################################################################
import numpy as np
from netCDF4 import Dataset

# define the dimensions
nb = nbasin
nfoc = 4
nmodel6 = len(mind_cmip6)
nmodel5 = len(mind_cmip5)

# change name for r2 values (training accuracy)
r2_obs_pred = r2_ia_obs
r2_hist5_pred = r2_ia_hist5
r2_hist6_pred = r2_ia_hist6

sens_types = ['sensitivity value', 'lower bound (95% confidence interval of reg. coeff.)', 'upper bound (95% confidence interval of reg. coeff.)']
foc_names=['CRUTSv4.04', 'PGFv2', 'GSWP3-EWEMBI', 'GSWP3-W5E5']

## save OBS data
# Create a NetCDF file
fpath='C:/runoff_mdtf2/'
ncfile = Dataset(fpath + 'runoff_sensitivity_obs.nc', 'w', format='NETCDF4')
# Define the dimensions
ncfile.createDimension('foc', nfoc)
ncfile.createDimension('ens', nens)
ncfile.createDimension('basin', nb)
ncfile.createDimension('sens_type', 3)
ncfile.createDimension('string_length', max([len(name) for name in sens_types]))  # For basin_names
# Create variables
psens_obs_var = ncfile.createVariable('psens_obs', np.float32, ('foc', 'ens', 'basin', 'sens_type'))
tsens_obs_var = ncfile.createVariable('tsens_obs', np.float32, ('foc', 'ens', 'basin', 'sens_type'))
intsens_obs_var = ncfile.createVariable('intsens_obs', np.float32, ('foc', 'ens', 'basin', 'sens_type'))
r2_obs_pred_var = ncfile.createVariable('r2_obs_pred', np.float32, ('foc', 'ens', 'basin'))
basin_names_var = ncfile.createVariable('basin_names', 'S1', ('basin', 'string_length'))
sens_type_names_var = ncfile.createVariable('sens_type_names', 'S1', ('sens_type', 'string_length'))
foc_names_var = ncfile.createVariable('foc_names', 'S1', ('foc', 'string_length'))
# Write data to variables
psens_obs_var[:,:,:,:] = psens_obs
tsens_obs_var[:,:,:,:] = tsens_obs
intsens_obs_var[:,:,:,:] = intsens_obs
r2_obs_pred_var[:,:,:] = r2_obs_pred
for i, name in enumerate(basin_names):
    basin_names_var[i, :len(name)] = list(name)
for i, type in enumerate(sens_types):
    sens_type_names_var[i, :len(type)] = list(type)
for i, name in enumerate(foc_names):
    foc_names_var[i, :len(name)] = list(name)
# additional informations
ncfile.description = "Observational estimation of runoff sensitivity from GRUN dataset (ref: https://doi.org/10.1029/2020WR028787)."
ncfile.ensemble = "Different ensembles are results of different sub-sampling during the trianing of machine-learning algorithm. Refer to above publication for details."
ncfile.methods = "Sensitivities are estimated as lienar regression coefficients of runoff onto the precipitation and temperature, using 5-year averaged water-year anomalies in 1945-2014 period."
ncfile.contact = "Hanjun Kim (hanjunkim0617@gmail.com)"
psens_obs_var.units = "%/%"
tsens_obs_var.units = "%/K"
intsens_obs_var.description = "Sensitivity of interaction term, which often has negligible role compared to other two sensitivities."
r2_obs_pred_var.description = "R2 values between predictions (using psens and tsens) and original runoff variation, representing the singificance of the regression coefficients."
basin_names_var.description = "Names of major river basins. Masks used for basin-average are from GRDC (https://mrb.grdc.bafg.de/)."
sens_type_names_var.description = "Sensitivity value is provided with the lower and upper bounds of regression coefficients using t-test with 95% confidence interval."
foc_names_var.description = "The atmospheric forcings used to generate GRUN runoff dataset (ref: https://doi.org/10.1029/2020WR028787)."
# Close the NetCDF file
ncfile.close()

## save hist6 data
# Create a NetCDF file
fpath='C:/runoff_mdtf2/'
ncfile = Dataset(fpath + 'runoff_sensitivity_hist6.nc', 'w', format='NETCDF4')
# Define the dimensions
ncfile.createDimension('model', nmodel6)
ncfile.createDimension('basin', nb)
ncfile.createDimension('sens_type', 3)
# Create variables
psens_hist6_var = ncfile.createVariable('psens_hist6', np.float32, ('model', 'basin', 'sens_type'))
tsens_hist6_var = ncfile.createVariable('tsens_hist6', np.float32, ('model', 'basin', 'sens_type'))
intsens_hist6_var = ncfile.createVariable('intsens_hist6', np.float32, ('model', 'basin', 'sens_type'))
r2_hist6_pred_var = ncfile.createVariable('r2_hist6_pred', np.float32, ('model', 'basin'))
# Write data to variables
psens_hist6_var[:,:,:] = psens_hist6
tsens_hist6_var[:,:,:] = tsens_hist6
intsens_hist6_var[:,:,:] = intsens_hist6
r2_hist6_pred_var[:,:] = r2_hist6_pred
# Close the NetCDF file
ncfile.close()

## save hist5 data
# Create a NetCDF file
fpath='C:/runoff_mdtf2/'
ncfile = Dataset(fpath + 'runoff_sensitivity_hist5.nc', 'w', format='NETCDF4')
# Define the dimensions
ncfile.createDimension('model', nmodel5)
ncfile.createDimension('basin', nb)
ncfile.createDimension('sens_type', 3)
# Create variables
psens_hist5_var = ncfile.createVariable('psens_hist5', np.float32, ('model', 'basin', 'sens_type'))
tsens_hist5_var = ncfile.createVariable('tsens_hist5', np.float32, ('model', 'basin', 'sens_type'))
intsens_hist5_var = ncfile.createVariable('intsens_hist5', np.float32, ('model', 'basin', 'sens_type'))
r2_hist5_pred_var = ncfile.createVariable('r2_hist5_pred', np.float32, ('model', 'basin'))
# Write data to variables
psens_hist5_var[:,:,:] = psens_hist5
tsens_hist5_var[:,:,:] = tsens_hist5
intsens_hist5_var[:,:,:] = intsens_hist5
r2_hist5_pred_var[:,:] = r2_hist5_pred
# Close the NetCDF file
ncfile.close()




################################################################
## calculation check: draw maps with filled river basins #######
################################################################
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
    nb=len(values)
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
    # plt.close()

## figures for T sensitivity ##
bins = [-30,-15,-12,-9,-6,-3,0,3,6,9,12,15,30]
bins2 = [-60,-15,-12,-9,-6,-3,0,3,6,9,12,15,60]
plot_colormap = [(0.4000, 0, 0, 1),(0.7706, 0, 0, 1),(0.9945, 0.0685, 0.0173, 1),(0.9799, 0.2483, 0.0627, 1),(0.9715, 0.4442, 0.0890, 1),(0.9845, 0.6961, 0.0487, 1),(0.9973, 0.9480, 0.0083, 1),(1.0000, 1.0000, 0.3676, 1),(1.0000, 1.0000, 1.0000, 1),(1.0000, 1.0000, 1.0000, 1),(0.6975, 0.8475, 0.9306, 1),(0.4759, 0.7358, 0.8797, 1),(0.2542, 0.6240, 0.8289, 1),(0.0436, 0.5130, 0.7774, 1),(0.0533, 0.4172, 0.7138, 1),(0.0630, 0.3215, 0.6503, 1),(0.0411, 0.1760, 0.5397, 1),(0, 0, 0.4000, 1)]
plot_unit='[%/K]'
coast_path = dpath + "/coastline.nc"
# OBS
values=np.nanmean(np.nanmean(tsens_obs[:,:,:,0],axis=1),axis=0)
# values=np.nanmean(tsens_hist5[:,:,0],axis=0)
# values=np.nanmean(tsens_hist6[:,:,0],axis=0)
plot_title='T sensitivity'
plot_path = figpath + 'mdtf_check.png'
plot_and_save_basin_filled(values, basin_points, bins, bins2, \
    plot_colormap, plot_unit, plot_title, plot_path, coast_path)
