import numpy as np 
import matplotlib.pyplot as plt 
import xarray as xr 
import os 

os.environ['OBS_DATA'] = '/localdrive/drive10/jj/mdtf/inputdata/obs_data/etc_composites'
os.environ['WK_DIR'] = '/localdrive/drive10/jj/mdtf/wkdir/MDTF_QBOi.EXP1.AMIP.001_1979_1981/etc_composites'
os.environ['CASENAME'] = 'QBOi.EXP1.AMIP.001'

def plot_area_fig(x,y,data,title,out_file):
  plt.figure()
  plt.contourf(x, y, data)
  plt.colorbar()
  plt.title(title)
  plt.ylabel('Distance [km]')
  plt.xlabel('Distance [km]')
  plt.savefig(out_file)
  plt.close('all')

##################################

###################################################
##### Creating plots from obs/merra and era-interim
###################################################

# load in the netcdf files 
obs_file = f"{os.environ['OBS_DATA']}/modis_merra.nc"
era_file = f"{os.environ['OBS_DATA']}/era_interim.nc"

# reading in the observation file
ds = xr.open_dataset(obs_file)
x = ds['X'].values
y = ds['Y'].values
modis_cld = ds['modis_cld'].values
merra_pw = ds['merra_pw'].values
merra_omega = ds['merra_omega'].values
ds.close()

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_modis_cld_SH_ocean_WARM.png"
title = 'MODIS Cloud Cover [SH-Ocean-WARM]'
plot_area_fig(x,y,modis_cld,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_pw_SH_ocean_WARM.png"
title = 'MERRA Precipitation [SH-Ocean-WARM]'
plot_area_fig(x,y,merra_pw,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_omega_SH_ocean_WARM.png"
title = 'MERRA Omega @ 500 hPa [SH-Ocean-WARM]'
plot_area_fig(x,y,merra_omega,title,out_file)

# reading in the re-analysis file
ds = xr.open_dataset(era_file)
x = ds['X'].values
y = ds['Y'].values
pr_nh_ocean_warm = ds['pr_nh_ocean_warm'].values
prw_nh_ocean_warm = ds['prw_nh_ocean_warm'].values
ws_nh_ocean_warm = ds['ws_nh_ocean_warm'].values
pr_sh_ocean_warm = ds['pr_sh_ocean_warm'].values
prw_sh_ocean_warm = ds['prw_sh_ocean_warm'].values
ws_sh_ocean_warm = ds['ws_sh_ocean_warm'].values
ds.close()

# SH - Ocean - WARM
out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_pr_SH_ocean_WARM.png"
title = 'Era-I PR [SH-Ocean-WARM]'
plot_area_fig(x,y,pr_sh_ocean_warm,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
title = 'Era-I PRW [SH-Ocean-WARM]'
plot_area_fig(x,y,prw_sh_ocean_warm,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_ws_SH_ocean_WARM.png"
title = 'Era-I Wind Speed [SH-Ocean-WARM]'
plot_area_fig(x,y,ws_sh_ocean_warm,title,out_file)

# NH - Ocean - WARM

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_pr_NH_ocean_WARM.png"
title = 'Era-I PR [NH-Ocean-WARM]'
plot_area_fig(x,y,pr_nh_ocean_warm,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
title = 'Era-I PRW [NH-Ocean-WARM]'
plot_area_fig(x,y,prw_nh_ocean_warm,title,out_file)

out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_ws_NH_ocean_WARM.png"
title = 'Era-I Wind Speed [NH-Ocean-WARM]'
plot_area_fig(x,y,ws_nh_ocean_warm,title,out_file)

print('Done Completing ETC-composites driver code.')
