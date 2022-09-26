#!/usr/bin/env python
# coding: utf-8



# This file is part of the Surface Albedo Feedback Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
#   Last update: 9/1/2022
# 
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point of contact Aaron Donohoe, U. Washington adonohoe@uw.edu
#   - Other contributors Ed Blanchardd, Lettie Roach, Wei Cheng
# 
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
# 
#   Functionality
# 
#   Code to input many years of monthly TOA and Surface shortwave radiative fluxes
#     and compute spatial maps of the surface albedo kernel from an isotropic model 
#     and surface albedo 
# 
#   Required programming language and libraries
# 
#      Python3 
# 
#   Required model output variables
# 
#      TOA and Surface shortwave radiative fluxes and surface temperature
#      ideally for 1996-2014 and 50 yrs of piControl and abrupt-4XCO2
# 
#   References
# 
#      Donohoe, A., E. Blanchard-Wrigglesworth, A. Schweiger, and P.J. Rasch, 2020:
#          The Effect of Atmospheric Transmissivity on Model and Observational Estimates 
#          of the Sea Ice Albedo Feedback, J. Climate, https://doi.org/10.1175/JCLI-D-19-0674.1
#

import os

# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import xarray as xr                # python library we use to read netcdf files
import numpy as np
import pandas as pd


def xr_reshape(A, dim, newdims, coords):
    """ Reshape DataArray A to convert its dimension dim into sub-dimensions given by
    newdims and the corresponding coords.
    Example: Ar = xr_reshape(A, 'time', ['year', 'month'], [(2017, 2018), np.arange(12)]) """

    # Create a pandas MultiIndex from these labels
    ind = pd.MultiIndex.from_product(coords, names=newdims)

    # Replace the time index in the DataArray by this new index,
    A1 = A.copy()

    A1.coords[dim] = ind

    # Convert multiindex to individual dims using DataArray.unstack().
    # This changes dimension order! The new dimensions are at the end.
    A1 = A1.unstack(dim)

    # Permute to restore dimensions
    i = A.dims.index(dim)
    dims = list(A1.dims)

    for d in newdims[::-1]:
        dims.insert(i, d)

    for d in newdims:
        _ = dims.pop(-1)

    return A1.transpose(*dims)

def climatology(field=None):
    """Compute climotological mean of residuals

    Parameters
    ----------
    field : xarray.DataArray, dims must be time, space (space can be multidim)
    
    Returns
    -------
    themean, thestd, trend, detrendedstd: xarray.DataArray, dims of month, space
    residuals: xarray.DataArray, dims of year, month, space
    """
    
    NY = int(field['time'].sizes['time']/12)

    field = xr_reshape(field,'time',['year','month'],[np.arange(NY),np.arange(12)])
    themean = field.mean(dim='year')

    return themean

def kernelalbedo(dt, ds, ut, us):
    # solve for single layer reflections under Taylor '07 assumptions

    alb = us/ds #surface albedo
    absorb=(dt-ut-ds+us)/dt #atmospheric absorption (assumed first pass only)
    R = (1-absorb-ds/dt)/(1-absorb-ds*alb/dt) #anayltitcally solution for single layer atmospheric reflection

    kernel = (1./100.)*(dt*((1.-R)*(1.-R))*(1.-absorb)*(1.-alb*R+R))/((1.-R*alb)*(1.-R*alb)) #derivative of upwelling solar at TOA with respect to surface albedo --  in units of W m^-2 per .01 change in surface albedo
    kernel.name = 'kernel'
    
    albedo = us/ds
    albedo.name = 'albedo'

    return kernel, albedo

def globaltimemean(tas, fx):
    t=tas.mean(dim='time')
    glob=t*fx
    glob=glob.sum()/fx.sum()
    glob.name='Tglob'
    
    return glob

def globalmean(tas, fx):
    glob=tas*fx
    glob=glob.sum(dim=["lat", "lon"])/fx.sum(dim=["lat", "lon"])
    glob.name='Tglob'
    
    return glob

def readandclimo(vname,file):
    field = xr.open_dataset(file)
    field = field[vname]
    field = climatology(field)
    
    return field

def linear_trend(x):
    yrs=np.arange(0,len(x))
    pf = np.polyfit(yrs, x, 1)
    
    return xr.DataArray(pf[0])     # need to return an xr.DataArray


def process_data(kernel_file, sensitivity_file):
    # the same function was used to compute the kernel and albedo 
    # from a climatology constructed from 2000-2018 of CERES40
    # it has been saved to kernel_obs_file
    # and is provided with this POD

    FSDT_var = "{rsdt_var}".format(**os.environ)
    FSDS_var = "{rsds_var}".format(**os.environ)
    FSUT_var = "{rsut_var}".format(**os.environ)
    FSUS_var = "{rsus_var}".format(**os.environ)
    TAS_var = "{tas_var}".format(**os.environ)
    
    # set up files for input data 
    FSDT_input_file = "{DATADIR}/mon/{CASENAME}.{rsdt_var}.mon.nc".format(**os.environ)
    FSDS_input_file = "{DATADIR}/mon/{CASENAME}.{rsds_var}.mon.nc".format(**os.environ)
    FSUT_input_file = "{DATADIR}/mon/{CASENAME}.{rsut_var}.mon.nc".format(**os.environ)
    FSUS_input_file = "{DATADIR}/mon/{CASENAME}.{rsus_var}.mon.nc".format(**os.environ)
    TAS_input_file  = "{DATADIR}/mon/{CASENAME}.{tas_var}.mon.nc".format(**os.environ)
    #area_input_file = "{DATADIR}/mon/areacella_fx_{model}_r1i1p1f1_gn.nc".format(**os.environ)
    area_input_file = "{DATADIR}/{CASENAME}.areacella.static.nc".format(**os.environ)
    print("area input file", area_input_file)
    # read in flux data, compute climatologies
    dt = readandclimo(FSDT_var, FSDT_input_file)
    ds = readandclimo(FSDS_var, FSDS_input_file)
    ut = readandclimo(FSUT_var, FSUT_input_file)
    us = readandclimo(FSUS_var, FSUS_input_file)

    kernel, albedo = kernelalbedo(dt, ds, ut, us)
    histmod = xr.merge([kernel, albedo])
    histmod.to_netcdf(kernel_file)

    # get timeseries needed to compute trends
    tas = xr.open_dataset(TAS_input_file)
    tas = tas[TAS_var]
    fx = xr.open_dataset(area_input_file)
    fx = fx['areacella']
    Tglob = globalmean(tas, fx)
    Tglobtrend = Tglob.groupby('time.month').apply(linear_trend)

    ds = xr.open_dataset(FSDS_input_file)
    us = xr.open_dataset(FSUS_input_file)  
    # must get rid of cftime since lack of leap day messes up divide below
    ds=ds['rsds'].assign_coords(month=('time',ds.time.dt.month)).swap_dims({'time':'month'}).drop('time')
    us=us['rsus'].assign_coords(month=('time',us.time.dt.month)).swap_dims({'time':'month'}).drop('time')
    albedo = us/ds
    stacked=albedo.stack(allpoints=['lat','lon']) # reduce to 2D array before computing trend
    albedo_trend=stacked.groupby(('month')).apply(linear_trend) # loses coord to unstack somewhere here
    tmp=stacked.isel(month=slice(0,12))           # use this to put back stack coord
    tmp[:,:]=albedo_trend
    albedo_trend = tmp.unstack('allpoints')
    albedo_trend=albedo_trend.fillna(0)
    albedo_per_Tglobtrend=albedo_trend/Tglobtrend
    albedo_per_Tglobtrend.name = 'sensitivity'
    albedo_per_Tglobtrend.to_netcdf(sensitivity_file)
    
    return
    
if __name__ == '__main__':
    process_data(kernel_file, sensitivity_file)


