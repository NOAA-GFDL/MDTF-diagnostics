import numpy as np
import xarray as xr
import warnings
from scipy import stats




def bin_2d(ds,bin1_var,bin2_var,target_var,bin1=10,bin2=10,stTconfint=0.99,bin1_range=None,bin2_range=None):
    """
    The function is written to bin the variable (target_var) in a xr.Dataset
    based on two other variables (bin1_var, bin2_var) in the same xr.Dataset. 
    The function calculate the mean, std, and count values of the target_var 
    after binning.
    
    Input:
    - ds (xr.Dataset) : the dataset includes all needed variables 
    - bin1_var (string) : variable name in the dataset used as the first
                          binning dimension
    - bin2_var (string) : variable name in the dataset used as the second
                          binning dimension
    - target_var (string/list of string) : variable name in the dataset that will be binned
                            based on the bin1_var and bin2_var. The mean, std,
                            and count values of the target_var will be calculated.
    - bin1 (int) : number of bins (equal interval) in bin1_var
    - bin2 (int) : number of bins in bin2_var
    - stTconfint (float) : default is 0.99, it is the confidence interval of the bin mean value
                        this is depend on the standard error of the variabilities of the values 
                        used to determined the mean value of the bin
    - bin1_range (array, optional) : the array is in the format of [min,max] values of bin1_var
                                     one desired to set the bin range. If not set, the min max 
                                     is default as the min max of the bin1_var itself.
    - bin2_range (array, optional) : the array is in the format of [min,max] values of bin2_var
                                     one desired to set the bin range. If not set, the min max 
                                     is default as the min max of the bin2_var itself.

    

    Output:
    - ds_bin (xr.Dataset) : the dataset with the mean, std,
                            and count values of the target_var based on
                            2 coordinates (bin1_var & bin2_var)
                          
    
    """
    warnings.simplefilter("ignore")
    

    if (bin1_range is not None) and (bin2_range is not None):
        bin1_interval = np.linspace(np.min(bin1_range),np.max(bin1_range),bin1+1)
        bin2_interval = np.linspace(np.min(bin2_range),np.max(bin2_range),bin2+1)
    else:
        bin1_interval = np.linspace(ds[bin1_var].min(),ds[bin1_var].max(),bin1+1)
        bin2_interval = np.linspace(ds[bin2_var].min(),ds[bin2_var].max(),bin2+1)
    bin1_val = np.convolve(bin1_interval, np.ones(2), 'valid') / 2.
    bin2_val = np.convolve(bin2_interval, np.ones(2), 'valid') / 2.

    
    ds_bin = xr.Dataset()
    for tvar in target_var:
        bin_matrix = np.zeros([bin1,bin2])
        std_matrix = np.zeros([bin1,bin2])
        count_matrix = np.zeros([bin1,bin2])
        print(tvar)
        for nbin1 in range(bin1):
            for nbin2 in range(bin2):
                da_temp = ds[tvar]\
                         .where((ds[bin1_var]>=bin1_interval[nbin1])&
                                (ds[bin1_var]<bin1_interval[nbin1+1])&
                                (ds[bin2_var]>=bin2_interval[nbin2])&
                                (ds[bin2_var]<bin2_interval[nbin2+1]),
                                drop=True)

                bin_matrix[nbin1,nbin2] = da_temp.mean(skipna=True).values
                std_matrix[nbin1,nbin2] = da_temp.std(skipna=True).values
                count_matrix[nbin1,nbin2] = da_temp.count().values

        da_bin = xr.DataArray(bin_matrix, coords=[(bin1_var, bin1_val), (bin2_var, bin2_val)])
        da_std = xr.DataArray(std_matrix, coords=[(bin1_var, bin1_val), (bin2_var, bin2_val)])
        da_count = xr.DataArray(count_matrix, coords=[(bin1_var, bin1_val), (bin2_var, bin2_val)])
        
        ### calculate confidence interval 
        # calculate the error bar base on the number of standard error
        # the number related to dist. percentage is derived base on Students's T
        # distribution
        da_dof = da_count-1
        alpha = 1.0-stTconfint
        da_nst = stats.t.ppf(1.0-(alpha/2.0),da_dof)  # 2-side
        da_stderr = da_std/np.sqrt(da_count)
        da_conf = da_nst*da_stderr

        
        ds_bin[tvar] = da_bin 
        ds_bin['%s_std'%tvar] = da_std 
        ds_bin['%s_count'%tvar] = da_count
        ds_bin['%s_conf_%0.2f'%(tvar,stTconfint)] = da_conf
        

    return ds_bin

