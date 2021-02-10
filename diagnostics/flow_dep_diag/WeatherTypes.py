#Load libraries
import os
import xarray as xr
import numpy as np
import pandas as pd
#import eccodes
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import cartopy.crs as ccrs
from cartopy import feature
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
# key PyWR functions are imported here
from PyWR import *


#The data used in this diagnostic was downloaded from the IRI:
#https://iridl.ldeo.columbia.edu/?Set-Language=en
#If data of a similar nature is desired, refer to the prep_data.py file for instructions on how to download anomaly data from the http server


#HOW WOULD THE DATA FILE BE INPUT IN THIS NAME FORMAT
hgt_input_path = "{DATADIR}/day/{CASENAME}.{hgt_var}.day.nc".format(**os.environ)
t2m_input_path = "{DATADIR}/day/{CASENAME}.{t2m_var}.day.nc".format(**os.environ)
pr_input_path = "{DATADIR}/day/{CASENAME}.{pr_var}.day.nc".format(**os.environ)

#Trying to write the open_ds using environment variables here for a single variable; the other variables are kept as original code for now

reanalysis = xr.open_dataset(hgt_input_path, decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])
#reanalysis = xr.open_dataset('WUS/data/hgt_NNRP_rean.nc', decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])

#old code still retained
rainfall = xr.open_dataset('WUS/data/rainfall_cpc.nc', decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])
t2m = xr.open_dataset('WUS/data/t2m_cpc.nc', decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])
uwnd = xr.open_dataset('WUS/data/u_NNRP_rean.nc', decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])
vwnd = xr.open_dataset('WUS/data/v_NNRP_rean.nc', decode_cf = True, decode_times = True).stack(time=['T'], grid=['Y', 'X'])


#get rid of dummy pressure coordinate
reanalysis=reanalysis.isel(P=0) 
uwnd=uwnd.isel(P=0)
vwnd=vwnd.isel(P=0)


#viewing the data
print(reanalysis)
print(rainfall)
print(t2m)
print(vwnd)
print(uwnd)


#DIMENSION REDUCTION: choose a percentage of variance explained that we will require
n_eof = get_number_eof(X=reanalysis['adif'].values, var_to_explain=0.9, plot=True)

#project the data onto the leading EOFs to get the principal component time series
#We will retain the PCA model for use later. The reanalysis_pc variable is now indexed [time, EOF]
pca_model = PCA(n_components=n_eof).fit(reanalysis['adif'].values)
reanalysis_pc = pca_model.transform(reanalysis['adif'].values)


#REANALYSIS WEATHER TYPING: perform the clustering. We will manually specify the number of clusters we want to create and the number of simulations we want to run
ncluster = 6 # use 6 WTs
n_sim = 50 # typically 25-50 -- try 25 for quick preliminary computation only

centroids, wtypes = loop_kmeans(X=reanalysis_pc, n_cluster=ncluster, n_sim=n_sim)
class_idx, best_part = get_classifiability_index(centroids)
print('The classifiability index is {}'.format(class_idx))


#Now that we have identified a suitable partition, we can use it to keep only the corresponding centroid and set of weather type labels. Use centroids to define KMeans object
best_fit = KMeans(n_clusters=ncluster, init=centroids[best_part, :, :], n_init=1, max_iter=1).fit(reanalysis_pc)

# start with reanalysis
reanalysis_composite = reanalysis.copy()
model_clust = best_fit.fit_predict(reanalysis_pc) # get centroids
weather_types = xr.DataArray(
    model_clust, 
    coords = {'time': reanalysis_composite['time']},
    dims='time'
)
reanalysis_composite['WT'] = weather_types
reanalysis_composite = reanalysis_composite.groupby('WT').mean(dim='time').unstack('grid')['adif']
reanalysis_composite['M'] = 0

wt_anomalies = [] # initialize empty list
wt_anomalies.append(reanalysis_composite)

wt_anomalies = xr.concat(wt_anomalies, dim='M') # join together
wt_anomalies['WT'] = wt_anomalies['WT'] + 1 # start from 1


#FIGURE: prepare a figure with rainfall and temperature composites
#Hashed out options for adding wind arrows, and additional plot labels

X, Y = np.meshgrid(reanalysis['adif'].X, reanalysis['adif'].Y)
map_proj = ccrs.PlateCarree() #ccrs.Orthographic(-110, 10)
data_proj = ccrs.PlateCarree()
wt_unique = np.unique(wt_anomalies['WT'])
figsize = (14, 8)

#WT proportions
wt=weather_types.to_dataframe(name='WT')
wt=wt+1
#wt.to_netcdf('data/t2m_cpc.nc', format="NETCDF4")
wt_counts = wt.groupby('WT').size().div(wt['WT'].size)
wt_counts

xmin,xmax = reanalysis['X'].min(), reanalysis['X'].max()
ymin,ymax = reanalysis['Y'].min(), reanalysis['Y'].max()

# Set up the Figure
plt.rcParams.update({'font.size': 12})
fig, axes = plt.subplots(
        nrows=3, ncols=len(wt_unique), subplot_kw={'projection': map_proj}, 
        figsize=figsize, sharex=True, sharey=True
    )

# Loop through
for i,w in enumerate(wt_unique):
    def selector(ds):
        times = wt.loc[wt['WT'] == w].index
        ds = ds.sel(time = np.in1d(ds.unstack('time')['T'], times))
        ds = ds.mean(dim = 'time')
        return(ds)

    # Top row: geopotential height anomalies
    ax = axes[0, i]
    ax.set_title('WT {}: {:.1%} of days'.format(w, wt_counts.values[i]))
    C0 = selector(reanalysis['adif']).unstack('grid').plot.contourf(
        transform = data_proj,
        ax=ax,
        cmap='PuOr',
        extend="both",
        levels=np.linspace(-2e2, 2e2, 21),
        add_colorbar=False,
        add_labels=False
    )
    ax.coastlines()
    ax.add_feature(feature.BORDERS)
    #ax.set_extent([-95, -65, -12, 12])

#     # add wind arrows
#     U = selector(uwnd).adif.values  
#     V = selector(vwnd).adif.values
#     magnitude = np.sqrt(U**2 + V**2)
#     strongest = magnitude > np.percentile(magnitude, 50)
#     Q = ax.quiver(
#         X[strongest], Y[strongest], U[strongest], V[strongest], 
#         transform=data_proj, 
#         width=0.001, scale=0.8,units='xy'
#     )

    # Middle row: rainfall anomalies
    ax = axes[1, i]
    C1 = selector(rainfall['adif']).unstack('grid').plot.contourf(
        transform = data_proj,
        ax=ax,
        cmap = 'BrBG',
        extend="both",
        levels=np.linspace(-2, 2, 13),
        add_colorbar=False,
        add_labels=False
    )
    ax.coastlines()
    ax.add_feature(feature.BORDERS)
    #ax.set_extent([-95, -75, -9, 5])

    # Bottom row: tepmperature anomalies
    ax = axes[2, i]
    C2 = selector(t2m['asum']).unstack('grid').plot.contourf(
        transform = data_proj,
        ax=ax,
        cmap = 'RdBu_r',
        extend="both",
        levels=np.linspace(-2, 2, 13),
        add_colorbar=False,
        add_labels=False
    )
    ax.coastlines()
    ax.add_feature(feature.BORDERS)
    #ax.set_extent([-95, -70, -9, 5])
    ax.tick_params(colors='b')

# # Add Colorbar
plt.tight_layout()
fig.subplots_adjust(right=0.94)
cax0 = fig.add_axes([0.97, 0.65, 0.0075, 0.3])
cax1 = fig.add_axes([0.97, 0.33, 0.0075, 0.3])
cax2 = fig.add_axes([0.97, 0.01, 0.0075, 0.3])
cbar0 = fig.colorbar(C0, cax = cax0)
cbar0.formatter.set_powerlimits((4, 4))
cbar0.update_ticks()
cbar0.set_label(r'$zg_{500}$ anomaly [$m^2$/$s^2$]', rotation=270)
cbar0.ax.get_yaxis().labelpad = 20
cbar1 = fig.colorbar(C1, cax=cax1)
cbar1.set_label('Precip. anomaly [mm/d]', rotation=270)
cbar1.ax.get_yaxis().labelpad = 20
cbar2 = fig.colorbar(C2, cax=cax2)
cbar2.set_label('T2m anomaly [$^o$C]', rotation=270)
cbar2.ax.get_yaxis().labelpad = 20

# Format these axes


#Add plot labels
# letters = string.ascii_lowercase
# for i, ax in enumerate(axes.flat):
#    label = '({})'.format(letters[i])
#    t = ax.text(0.05, 0.9, label, fontsize=11, transform=ax.transAxes)
#    t.set_bbox(dict(facecolor='white', edgecolor='gray'))

# Add a quiver key
#k = plt.quiverkey(Q, 0.9, 0.7, 1, '1 m/s', labelpos='E', coordinates='figure')

fig.savefig('figs/wt_composite.pdf', bbox_inches='tight') #this needs to be changed to appropriate folder in framework
plt.show()