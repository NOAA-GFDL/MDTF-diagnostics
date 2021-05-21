#Python packages/ modules imported for the diagnostic
# the sample data is from ERA5 over the JAS period from 2000 to 2019 
import os
import xarray as xr
import numpy as np
from scipy import integrate
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


#Setting variables equal to environment variables set by the diagnostic
time_coord = os.environ["time_coord"]
lat_coord = os.environ["lat_coord"]
lon_coord = os.environ["lon_coord"]
lev_coord = os.environ["lev_coord"]
omega_var = os.environ["omega_var"] 


def top_heaviness_ratio_calculation(reanalysis_path, reanalysis_var):
    # read omega and land-sea fraction data
    ds= xr.open_dataset(reanalysis_path)
    lev_era5=ds[lev].values
    lat_era5=ds[lat].values
    lon_era5=ds[lon].values
    lsm_erai=ds[lsm].values
    isort=np.argsort(lev_era5)[::-1] # descending
    mid_omega_era5=ds[reanalysis_var].values # mon x lev x lat x lon; for the sample data (JAS over 2000-2019) 
    mid_omega_era5=mid_omega_era5[:,isort]
    #======================deriving O1 and O2=======================
    # construct Q1_era5 as half a sine wave and Q2_era5 as a full sine wave
    # two base functions; Q1: idealized deep convection profile; Q2: Deep stratiform profile (Back et al. 2017)
    Q1_era5=np.zeros(len(lev_era5))
    Q2_era5=np.zeros(len(lev_era5))
    for i in range(len(lev_era5)):
        Q1_era5[i]=-np.sin(np.pi*(lev_era5[i]-lev_era5[0])/dp)
        Q2_era5[i]=np.sin(2*np.pi*(lev_era5[i]-lev_era5[0])/dp)
    #Normalize 
    factor=integrate.trapz(Q1_era5*Q1_era5,lev_era5)/(lev_era5[-1]-lev_era5[0])
    Q1_era5=Q1_era5/np.sqrt(factor)
    factor=integrate.trapz(Q2_era5*Q2_era5,lev_era5)/(lev_era5[-1]-lev_era5[0])
    Q2_era5=Q2_era5/np.sqrt(factor)
    # deriving O1 and O2; O1 and O2 are coefs of Q1 and Q2
    O1_era5=integrate.trapz(mid_omega_era5*Q1_era5[None,None,:,None,None],lev_era5,axis=2)/-(lev_era5[0]-lev_era5[-1])
    O2_era5=integrate.trapz(mid_omega_era5*Q2_era5[None,None,:,None,None],lev_era5,axis=2)/-(lev_era5[0]-lev_era5[-1]) 
    #======================calculate explained variance over the globe=======================
    # Often times, the pres level is not equally distributed. People tend to increase density in the 
    # ... upper and lower atmopshere, leaving a less dense distribution in the mid atmosphere. 
    # ... Thus, it is important to weight Q1 and Q2 before we calculate explained variance
    # Remember, we already take weights into account when calculating O1 and O2
    dlev=np.zeros(len(lev_era5)) # dlev is the weighting array
    dlev[0]=(lev_era5[0]-lev_era5[1])/2.
    dlev[-1]=(lev_era5[-2]-lev_era5[-1])/2.
    mid_dlev=(lev_era5[:-1]-lev_era5[1:])/2.
    dlev[1:-1]=(mid_dlev[1:]+mid_dlev[:-1])
    mid_Q1_era5=Q1_era5*dlev
    mid_Q2_era5=Q2_era5*dlev
    mid_Q1_era5=mid_Q1_era5/np.sqrt(np.sum(mid_Q1_era5**2)) # weighted Q1
    mid_Q2_era5=mid_Q2_era5/np.sqrt(np.sum(mid_Q2_era5**2)) # weighted Q2
    OQ1_era5=np.nansum(mid_Q1_era5[None,:,None,None]*mid_omega_era5,axis=1)
    OQ2_era5=np.nansum(mid_Q2_era5[None,:,None,None]*mid_omega_era5,axis=1)
    total_variance_era5=np.nansum(np.nanvar(mid_omega_era5,axis=0),axis=0)
    Q1_explained_era5=np.nanvar(OQ1_era5,axis=0)
    Q2_explained_era5=np.nanvar(OQ2_era5,axis=0)
    total_explained_era5=Q1_explained_era5+Q2_explained_era5
    #====================== set up figures =======================
    #====================== O1 =======================
    fig, axes = plt.subplots(figsize=(8,4))
    ilat=np.argsort(lat_era5)
    ilon=np.argsort(lon_era5)
    mid1=np.nanmean(O1_era5,axis=0)
    x,y = np.meshgrid(lon_era5,lat_era5) 
    m = basemap(projection="cyl",llcrnrlat=lat_era5[ilat][0],urcrnrlat=lat_era5[ilat][-1],\
            llcrnrlon=lon_era5[ilon][0],urcrnrlon=lon_era5[ilon][0],ax=axes,resolution='c')
    m.drawcoastlines(linewidth=1, color="k")
    m.drawparallels(np.arange(lat_era5[ilat][0],lat_era5[ilat][-1],30),labels=[1,0,0,0],linewidth=0.,fontsize=16)
    m.drawmeridians(np.arange(lon_era5[ilon][0],lon_era5[ilon][-1],60),labels=[0,0,0,1],linewidth=0.,fontsize=16)
    X,Y = m(x,y)
    clevs=np.arange(-0.06,0.07,0.01)
    im0 = m.contourf(X,Y,mid1,clevs,cmap = plt.get_cmap('RdBu_r'),extend='both')
    cbar = fig.colorbar(im0, ax=axes, orientation="horizontal", pad=0.15,shrink=.9,aspect=45)
    axes.set_title('O1 [Pa/s] ERA5 ',loc='center',fontsize=16)
    fig.tight_layout() 
    fig = fig.savefig("{WK_DIR}/model/Long term mean of O1.pdf", format='pdf',bbox_inches='tight')
    #====================== O2 =======================
    fig, axes = plt.subplots(figsize=(8,4))
    mid1=np.nanmean(O2_era5,axis=0)
    x,y = np.meshgrid(lon_era5,lat_era5) 
    m = basemap(projection="cyl",llcrnrlat=lat_era5[ilat][0],urcrnrlat=lat_era5[ilat][-1],\
            llcrnrlon=lon_era5[ilon][0],urcrnrlon=lon_era5[ilon][0],ax=axes,resolution='c')
    m.drawcoastlines(linewidth=1, color="k")
    m.drawparallels(np.arange(lat_era5[ilat][0],lat_era5[ilat][-1],30),labels=[1,0,0,0],linewidth=0.,fontsize=16)
    m.drawmeridians(np.arange(lon_era5[ilon][0],lon_era5[ilon][-1],60),labels=[0,0,0,1],linewidth=0.,fontsize=16)
    X,Y = m(x,y)
    clevs=np.arange(-0.06,0.07,0.01)
    im0 = m.contourf(X,Y,mid1,clevs,cmap = plt.get_cmap('RdBu_r'),extend='both') 
    cbar = fig.colorbar(im0, ax=axes, orientation="horizontal", pad=0.15,shrink=.9,aspect=45)
    axes.set_title('O2 [Pa/s] ERA5 ',loc='center',fontsize=16)
    fig.tight_layout()
    fig = fig.savefig("{WK_DIR}/model/Long term mean of O2.pdf", format='pdf',bbox_inches='tight')    
    #====================== O2/O1 top-heaviness ratio =======================
    fig, axes = plt.subplots(figsize=(8,4))
    mmid1=np.nanmean(O2_era5,axis=0)/np.nanmean(O1_era5,axis=0)
    midi=np.nanmean(O1_era5,axis=0)<0.01
    mmid1[midi]=np.nan
    x,y = np.meshgrid(lon,lat)
    m = basemap(projection="cyl",llcrnrlat=lat_era5[ilat][0],urcrnrlat=lat_era5[ilat][-1],\
            llcrnrlon=lon_era5[ilon][0],urcrnrlon=lon_era5[ilon][0],ax=axes,resolution='c')
    m.drawcoastlines(linewidth=1, color="k")
    m.drawparallels(np.arange(lat_era5[ilat][0],lat_era5[ilat][-1],30),labels=[1,0,0,0],linewidth=0.,fontsize=16)
    m.drawmeridians(np.arange(lon_era5[ilon][0],lon_era5[ilon][-1],60),labels=[0,0,0,1],linewidth=0.,fontsize=16)
    X,Y = m(x,y)
    clevs=np.arange(-0.6,0.7,0.1)
    im0 = m.contourf(X,Y,mmid1,clevs,cmap = plt.get_cmap('RdBu_r'),extend='both') 
    cbar = fig.colorbar(im0, ax=axes, orientation="horizontal", pad=0.15,shrink=.9,aspect=45)
    axes.set_title('O2/O1 ERA5 ',loc='center',fontsize=18)
    fig = fig.savefig("{WK_DIR}/model/Top-Heaviness Ratio ERA5.pdf", format='pdf',bbox_inches='tight')    
    #====================== O2/O1 top-heaviness ratio =======================
    fig, axes = plt.subplots(figsize=(8,4))
    mmid=(Q2_explained_era5+Q1_explained_era5)/total_variance_era5
    lons, lats = np.meshgrid(lon_GEFS, lat_GEFS)
    m = basemap(projection="cyl",llcrnrlat=lat_era5[ilat][0],urcrnrlat=lat_era5[ilat][-1],\
            llcrnrlon=lon_era5[ilon][0],urcrnrlon=lon_era5[ilon][0],ax=axes,resolution='c')
    m.drawcoastlines(linewidth=0.5, color="black")
    m.drawparallels(np.arange(lat_era5[ilat][0],lat_era5[ilat][-1],30),labels=[1,0,0,0],linewidth=0.,fontsize=16)
    m.drawmeridians(np.arange(lon_era5[ilon][0],lon_era5[ilon][-1],60),labels=[0,0,0,1],linewidth=0.,fontsize=16)
    X,Y = m(x,y)
    cmap = plt.get_cmap('RdBu_r')
    clevs=np.arange(0,1,.05)
    im = m.contourf(X,Y,mmid,20,cmap=cmap,extend='both')
    axes.set_title('Explained Var. by Q1 & Q2 July',loc='center',fontsize=16,y=1.02)
    plt.colorbar(im,orientation='horizontal', pad=0.15,shrink=.9,aspect=45)
    fig = fig.savefig("{WK_DIR}/model/Explained Var ERA5.pdf", format='pdf',bbox_inches='tight')    

    print("Plotting Completed")
    

top_heaviness_ratio_calculation(os.environ["OMEGA_FILE"],os.environ["OMEGA_var"])




