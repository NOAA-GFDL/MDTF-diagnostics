import os
# non-X windows backend
# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import xarray as xr                # python library we use to read netcdf files
import xwmt
import numpy as np 

## insert function description ##

def wmt_calc(ds):
    lon = ds['lon']
    lon = lon.where(lon<180.,other=lon-360.)
    lat = ds['lat']
    SPNA = ds.where((lat>=40) & (lat<=80) & (lon>=-65.) & (lon<=15.))

    #2)Calculate WMT using xwmt
    wmt_init = xwmt.swmt(SPNA)
    wmt_spna = wmt_init.G('sigma2', bins=np.linspace(33.1,38))

    #time average of WMT
    time_coord_name = os.environ["time_coord"]
    wmt_spna_mean = wmt_spna.mean(time_coord_name)/1e6

    #wmt to dataset
    wmt_spna_mean_ds = wmt_spna_mean.to_dataset(name='wmt')
    return wmt_spna_mean_ds
