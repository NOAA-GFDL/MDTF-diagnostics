#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This file is part of the Surface Albedo Feedback Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
#   Last update: 1/25/2021
# 
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point Lettie Roach, Aaron Donohoe, and Cecilia Bitz
#   - Lettie Roach, University of Washington, lroach@uw.edu
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
import xesmf as xe
import numpy as np
import pandas as pd


# reads in model data and computes stuff

# In[ ]:


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
    """Compute mean, std, trend, std of detrended, residuals

    Parameters
    ----------
    field : xarray.DataArray, dims must be time, space (space can be multidim)
    
    Returns
    -------
    themean, thestd, trend, detrendedstd: xarray.DataArray, dims of month, space
    residuals: xarray.DataArray, dims of year, month, space
    """
    
    NY=int(field['time'].sizes['time']/12)

    field=xr_reshape(field,'time',['year','month'],[np.arange(NY),np.arange(12)])
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

def readandclimo(vname,file):

    field = xr.open_dataset(file)
    field = field[vname]
    field = climatology(field)
    
    return field


# In[9]:


def process_data():

    FSDT_var = "{FSDT_var}".format(**os.environ)
    FSDS_var = "{FSDS_var}".format(**os.environ)
    FSUT_var = "{FSUT_var}".format(**os.environ)
    FSUS_var = "{FSUS_var}".format(**os.environ)
    TAS_var  = "{TAS_var}".format(**os.environ)

    podname='surface_albedo_feedback'

    wk_dir="{WK_DIR}".format(**os.environ)
    model="{model}".format(**os.environ)
    modelname = "{model}".format(**os.environ)
    # these yrs only refer to the hist period for comparing kernel of mod to CERES
    # this pod also uses piControl and 4XCO2 output, the years will differ with model
    firstyr = "{FIRSTYR}".format(**os.environ)
    lastyr = "{LASTYR}".format(**os.environ)

    obsdir="{OBS_DATA}/".format(**os.environ)
    output_dir = wk_dir+'/model/'

    ### model and obs data files and varnames: ###############################################

    # procesed output file names
    kernel_obs_file = obsdir+'CERES40_surface_albedo_kernel_2000-2018_MJJA.nc'
    sensitivity_obs_file = obsdir+'CERES40_ice_sensitivity_MJJA.nc'
    kernel_histmod_file=output_dir+'surface_albedo_kernel_'+firstyr+'-'+lastyr+'.nc'
    kernel_pimod_file=output_dir+'surface_albedo_kernel_piControl.nc'
    albedo_abmod_file=output_dir+'surface_albedo_abrupt-4xCO2.nc'
    IS_mod_file=output_dir+'surface_albedo_sensitivity_abrupt-4xCO2_minus_piControl.nc'


    # process model piControl data to compute kerel, albedo, and Tglob
    TAS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{TAS_var}.piControl.nc".format(**os.environ)
    area_input_file = "{DATADIR}/mon/areacella_fx_{model}_abrupt-4xCO2_r1i1p1f1_gn.nc".format(**os.environ)
    tas=xr.open_dataset(TAS_input_file)
    fx=xr.open_dataset(area_input_file)
    tas=tas[TAS_var]
    fx=fx['areacella']
    Tglob=globaltimemean(tas, fx)
    tas=None
    fx=None

    # process model piControl calc kernel and albedo
    piFSDT_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSDT_var}.piControl.nc".format(**os.environ)
    piFSDS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSDS_var}.piControl.nc".format(**os.environ)
    piFSUT_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSUT_var}.piControl.nc".format(**os.environ)
    piFSUS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSUS_var}.piControl.nc".format(**os.environ)

    dt = readandclimo(FSDT_var,piFSDT_input_file)
    ds = readandclimo(FSDS_var,piFSDS_input_file)
    ut = readandclimo(FSUT_var,piFSUT_input_file)
    us = readandclimo(FSUS_var,piFSUS_input_file)   

    kernel,albedo=kernelalbedo(dt, ds, ut, us)
    pimod=xr.merge([kernel,albedo,Tglob])
    pimod.to_netcdf(kernel_pimod_file)

    # process model abrupt-4xCO2 data to compute albedo, and Tglob
    TAS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{TAS_var}.abrupt-4xCO2.nc".format(**os.environ)
    area_input_file = "{DATADIR}/mon/areacella_fx_{model}_abrupt-4xCO2_r1i1p1f1_gn.nc".format(**os.environ)
    tas=xr.open_dataset(TAS_input_file)
    fx=xr.open_dataset(area_input_file)
    tas=tas[TAS_var]
    fx=fx['areacella']
    Tglob=globaltimemean(tas, fx)
    tas=None
    fx=None

    abFSDS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSDS_var}.abrupt-4xCO2.nc".format(**os.environ)
    abFSUS_input_file = "{DATADIR}/mon/{CASENAME}.mon.{FSUS_var}.abrupt-4xCO2.nc".format(**os.environ)
    ds = readandclimo(FSDS_var,abFSDS_input_file)
    us = readandclimo(FSUS_var,abFSUS_input_file)   
    albedo = us/ds
    albedo.name = 'albedo'
    abmod=xr.merge([albedo,Tglob])
    abmod.to_netcdf(albedo_abmod_file)

    # historical kernel and albedo from model and CERES
    FSDT_input_file = "{DATADIR}/mon/{CASENAME}.{FSDT_var}.mon.nc".format(**os.environ)
    FSDS_input_file = "{DATADIR}/mon/{CASENAME}.{FSDS_var}.mon.nc".format(**os.environ)
    FSUT_input_file = "{DATADIR}/mon/{CASENAME}.{FSUT_var}.mon.nc".format(**os.environ)
    FSUS_input_file = "{DATADIR}/mon/{CASENAME}.{FSUS_var}.mon.nc".format(**os.environ)

    dt = readandclimo(FSDT_var,FSDT_input_file)
    ds = readandclimo(FSDS_var,FSDS_input_file)
    ut = readandclimo(FSUT_var,FSUT_input_file)
    us = readandclimo(FSUS_var,FSUS_input_file)   

    kernel,albedo=kernelalbedo(dt, ds, ut, us)
    histmod=xr.merge([kernel,albedo])
    histmod.to_netcdf(kernel_histmod_file)

    processraw=False
    if processraw: # this is only here FYI, this calc is provided in file kernel_obs_file
        # obs raw input file name
        radiation_obs_file = obsdir+'CERES40_climatology_2000-2018.nc'
        cires = xr.open_dataset(radiation_obs_file) # climatology file
        dt=cires.CDT
        ds=cires.CDS
        ut=cires.CUT
        us=cires.CUS
        kernel,albedo=kernelalbedo(dt, ds, ut, us)
        obs=xr.merge([kernel,albedo])
        obs.to_netcdf(kernel_obs_file)

    dt=None
    ds=None
    ut=None
    us=None
    kernel=None
    albedo=None

    obs=None
    histmod=None
    abmod=None
    pimod=None

    cires=None
    
if __name__ == '__main__':

    process_data()


