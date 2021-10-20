#!/usr/bin/env python
# coding: utf-8

import warnings
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from model_read import regional_var
from obs_data_read import tao_triton,rama
from groupby_variables import bin_2d





# 0-360
lon_lim = [30,180]
lat_lim = [-20,20]
year_lim = [1998,2014]


# need CMOR variables including
# 1. 'huss'    : Surface 2m Humidity (kg/kg)
# 2. 'ts'      : Skin Temperature (SST for open ocean; K)
# 3. 'sfcWind' : Near-Surface Wind Speed (10 meter; m/s)
# 4. 'psl'     : Sea Level Pressure (Pa)
# 5. 'hfls'    : Surface Upward Latent Heat Flux (W/m^2 and positive upward)
# 6. 'pr'      : Precipitation (kg/m^3)


warnings.simplefilter("ignore")


varlist = ['/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*huss.day.nc',
           '/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*ts.day.nc',
           '/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*psl.day.nc',
           '/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*sfcWind.day.nc',
           '/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*hfls.day.nc',
           '/home/joedhsu/mdtf/inputdata/model/NCAR.CESM2.hist.r1i1p1f1/day/*pr.day.nc']

obs_taotriton_dir = '/home/joedhsu/mdtf/inputdata/obs_data/tao_triton/'
obs_rama_dir = '/home/joedhsu/mdtf/inputdata/obs_data/rama/'

################## Main script start #############
# Read model
ds_cesm2 = regional_var(varlist, lon_lim, lat_lim, year_lim)

# Read tao/triton
ds_tao,location_pac = tao_triton(obs_taotriton_dir,lon_lim,lat_lim,year_lim)

# Read rama
ds_rama,location_ind = rama(obs_rama_dir,lon_lim,lat_lim,year_lim)

# combine two observational data
location = location_pac + location_ind
ds_stn = xr.concat([ds_tao,ds_rama],dim='allstn')



# # Binning the latent heat flux
stt = 0.99

nbin1 = 20
bin1_range = [0,20]

nbin2 = 16
bin2_range = [0,16]


ds_stn_bin = bin_2d(ds_stn,'sfcWind','del_q',['hfls'],
                          bin1=nbin1,bin2=nbin2,stTconfint=stt,
                          bin1_range=bin1_range,
                          bin2_range=bin2_range)

ds_cesm2_bin = bin_2d(ds_cesm2.load(),'sfcWind','del_q',['hfls','pr'],
                          bin1=nbin1,bin2=nbin2,stTconfint=stt,
                          bin1_range=bin1_range,
                          bin2_range=bin2_range)


# Unit change for precip CESM2
rho_w = 1000.                      # kg/m^3
m2mm = 1000.                       # mm/m
s2day = 60.*60.*24.                # s/day
pr_factor_cesm2 = 1./rho_w*m2mm*s2day    # kg/m^2/s => mm/day

# # Unit change for precip E3SM
# # rho_w = 1000.               # kg/m^3
# # latent_water = 2.4346e6   # J/kg
# m2mm = 1000.               # mm/m
# s2day = 60.*60.*24.        # s/day
# pr_factor_e3sm = m2mm*s2day     # m/s => mm/day

#################### plotting ###################

fig = plt.figure(1,figsize=(5,5))

qlat_level = np.linspace(0,400,11)
dqlat_level = np.linspace(-50,50,11)
qlatratio_level = np.linspace(-0.2,0.2,11)
ratiolevel = np.linspace(0.01,0.01,1)
pr_level = np.array([-0.1,5,10])


# ======== hlfs obs =========
ax1 = fig.add_axes([0,0,1,0.8])
im = ds_stn_bin['hfls'].plot.pcolormesh(x='sfcWind',
                                          y='del_q',
                                          ax=ax1,
                                          levels=qlat_level,
                                          extend='both',
                                          cmap='plasma_r',)
cb=im.colorbar
cb.remove()


cs = ((ds_stn_bin['hfls_count']/ds_stn_bin['hfls_count'].sum())
                            .plot.contour(x='sfcWind',
                                          y='del_q',
                                          ax=ax1,
                                          levels=ratiolevel,
                                          colors='w',linewidths=6)
     )
ax1.clabel(cs, ratiolevel, inline=True, fmt='%0.2f', fontsize=10)

# ========== hlfs model ===========
ax2 = fig.add_axes([1,0,1,0.8])
im = ds_cesm2_bin['hfls'].plot.pcolormesh(x='sfcWind',
                                          y='del_q',
                                          ax=ax2,
                                          levels=qlat_level,
                                          extend='both',
                                          cmap='plasma_r',)
cb=im.colorbar
cb.remove()
cbaxes=fig.add_axes([1.9,0,0.02,0.8])
cbar=fig.colorbar(im,cax=cbaxes,orientation='vertical')
cbar.set_ticks(qlat_level)
cbar.set_ticklabels(["%0.0f"%(n) for n in qlat_level])
cbar.ax.tick_params(labelsize=15,rotation=0)
cbar.set_label(label='Latent heat flux ($W/m^2$)',size=15, labelpad=15)


cs = ((ds_cesm2_bin['hfls_count']/ds_cesm2_bin['hfls_count'].sum())
                            .plot.contour(x='sfcWind',
                                          y='del_q',
                                          ax=ax2,
                                          levels=ratiolevel,
                                          colors='w',linewidths=6)
     )
ax2.clabel(cs, ratiolevel, inline=True, fmt='%0.2f', fontsize=10)



ax1.set_yticks(np.arange(bin2_range[0],bin2_range[1]+1,2))
ax1.set_xticks(np.arange(bin1_range[0],bin1_range[1]+1,2))
# ax1.set_yticklabels(np.arange(0,13,1), color='black',size=15)
ax1.set_xlim([bin1_range[0],bin1_range[1]])
ax1.set_ylim([bin2_range[0],bin2_range[1]])
ax1.tick_params(axis='y',labelsize=15,length=5,width=1)
ax1.tick_params(axis='x',labelsize=15,length=5,width=1)
# ax2.grid(linewidth=2, color='grey', alpha=0.3, linestyle='--')
ax1.set_ylabel('$\Delta$q ($g/kg$)',size=15)
ax1.set_xlabel('10m wind speed ($m/s$)',size=15)
ax1.set_title('Obs',color='black', weight='bold',size=22)
# ax2.legend(loc='lower left',fontsize=20,frameon=False)

ax2.set_yticks(np.arange(bin2_range[0],bin2_range[1]+1,2))
ax2.set_xticks(np.arange(bin1_range[0],bin1_range[1]+1,2))
# ax2.set_yticklabels(np.arange(0,13,1), color='black',size=15)
ax2.set_xlim([bin1_range[0],bin1_range[1]])
ax2.set_ylim([bin2_range[0],bin2_range[1]])
ax2.tick_params(axis='y',labelsize=15,length=5,width=1)
ax2.tick_params(axis='x',labelsize=15,length=5,width=1)
ax2.set_ylabel('',size=15)
ax2.set_xlabel('10m wind speed ($m/s$)',size=15)
ax2.set_title('CESM2',color='black', weight='bold',size=22)
# ax2.legend(loc='lower left',fontsize=20,frameon=False)



###############################################################################
dx=0.3

ds_cesm2bias_bin = ds_cesm2_bin-ds_stn_bin
ds_cesm2bias_bin_conf =  np.sqrt(ds_cesm2_bin**2+ds_stn_bin**2)
ds_cesm2bias_bin_ratio = (ds_cesm2_bin-ds_stn_bin)/ds_cesm2_bin



# ========== hfls bias ===========
ax2 = fig.add_axes([1*2+dx,0,1,0.8])
im = ds_cesm2bias_bin['hfls'].plot.pcolormesh(x='sfcWind',
                                          y='del_q',
                                          ax=ax2,
                                          levels=dqlat_level,
                                          extend='both',
                                          cmap='RdBu_r',)

cb=im.colorbar
cb.remove()

im2 = (ds_cesm2_bin['pr']*pr_factor_cesm2).plot.contour(x='sfcWind',
                                          y='del_q',
                                          ax=ax2,
                                          levels=pr_level,
                                          extend='max',
                                          cmap='summer',linewidths=4)

im2.clabel(pr_level, inline=True, fmt='%0.2f', fontsize=10)

cbaxes=fig.add_axes([1*3+dx-0.1,0,0.02,0.8])
cbar=fig.colorbar(im,cax=cbaxes,orientation='vertical')
cbar.set_ticks(dqlat_level)
cbar.set_ticklabels(["%0.0f"%(n) for n in dqlat_level])
cbar.ax.tick_params(labelsize=15,rotation=0)
cbar.set_label(label='Latent heat flux bias ($W/m^2$)',size=15, labelpad=15)

biases_conf = (ds_cesm2bias_bin_conf['hfls_conf_%0.2f'%(stt)]
              .where(ds_cesm2bias_bin_conf['hfls_conf_%0.2f'%(stt)]
                     <np.abs(ds_cesm2bias_bin['hfls']))
              )

y, x = np.meshgrid(np.linspace(bin2_range[0],bin2_range[1],nbin2+1),
                   np.linspace(bin1_range[0],bin1_range[1],nbin1+1))
ax2.pcolor(x,y,biases_conf,hatch='..',alpha=0)


cs = ((ds_cesm2_bin['hfls_count']/ds_cesm2_bin['hfls_count'].sum())
                            .plot.contour(x='sfcWind',
                                          y='del_q',
                                          ax=ax2,
                                          levels=ratiolevel,
                                          colors='w',linewidths=6)
     )



ax2.set_title('CESM2 bias',color='black', weight='bold',size=22)

ax2.set_yticks(np.arange(bin2_range[0],bin2_range[1]+1,2))
ax2.set_xticks(np.arange(bin1_range[0],bin1_range[1]+1,2))
# ax2.set_yticklabels(np.arange(0,13,1), color='black',size=15)
ax2.set_xlim([bin1_range[0],bin1_range[1]])
ax2.set_ylim([bin2_range[0],bin2_range[1]])
ax2.tick_params(axis='y',labelsize=15,length=5,width=1)
ax2.tick_params(axis='x',labelsize=15,length=5,width=1)
ax2.set_ylabel('',size=15)
ax2.set_xlabel('10m wind speed ($m/s$)',size=15)



fig.savefig('LHFLXmatrix.pdf', dpi=300, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches="tight", pad_inches=None,
                frameon=None)
