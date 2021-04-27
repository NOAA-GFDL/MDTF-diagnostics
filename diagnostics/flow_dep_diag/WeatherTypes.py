#Python packages/ modules imported for the diagnostic
import os
import xarray as xr
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import cartopy.crs as ccrs
from cartopy import feature
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
# The following are function scripts which the diagnostic calls to run specific calculations
# refer to PyWR.py and ClimAnom_func.py for details on imported functions
from PyWR import *
from ClimAnom_func import *

#Setting variables equal to environment variables set by the diagnostic
time_coord = os.environ["time_coord"]
lat_coord = os.environ["lat_coord"]
lon_coord = os.environ["lon_coord"]
Z250_var = os.environ["Z250_var"]
PRECT_var = os.environ["PRECT_var"]
tas_var = os.environ["T250_var"]

def weatherTypes(reanalysis_path, reanalysis_var, rainfall_path, rainfall_var, t2m_path, t2m_var):
    reanalysis = climAnom(var_path=reanalysis_path, var_name=reanalysis_var).stack(T=[time_coord], grid=[lat_coord, lon_coord])
    rainfall = climAnom(var_path=rainfall_path, var_name=rainfall_var).stack(T=[time_coord], grid=[lat_coord, lon_coord])
    t2m = climAnom(var_path=t2m_path, var_name=t2m_var).stack(T=[time_coord], grid=[lat_coord, lon_coord])
    reanalysis = reanalysis.to_dataset()
    rainfall = rainfall.to_dataset()
    t2m = t2m.to_dataset()
    print("Climatology anomaly calculations completed.")
#dimension reduction; projection of data onto leading EOFs for principle component time series
#PCA model saved for later use as reanalysis_pc
    n_eof = get_number_eof(X=reanalysis[Z250_var].values, var_to_explain=0.9, plot=True)
    pca_model = PCA(n_components=n_eof).fit(reanalysis[Z250_var].values)
    reanalysis_pc = pca_model.transform(reanalysis[Z250_var].values)
#perform clustering using manually specified number of clusters
    n_cluster = int(os.environ["NCLUSTER"])
    n_sim = int(os.environ["NSIM"])
    centroids, wtypes = loop_kmeans(X=reanalysis_pc, n_cluster=n_cluster, n_sim=n_sim)
    class_idx, best_part = get_classifiability_index(centroids)
    print('The classifiability index is {}'.format(class_idx))
#define KMeans object
    best_fit = KMeans(n_clusters=n_cluster, init=centroids[best_part, :, :], n_init=1, max_iter=1).fit(reanalysis_pc)
#start reanalysis
    reanalysis_composite = reanalysis.copy()
    model_clust = best_fit.fit_predict(reanalysis_pc) # get centroids
    weather_types = xr.DataArray(
        model_clust,
        coords = {'T': reanalysis_composite['T']},
        dims='T'
    )
    reanalysis_composite['WT'] = weather_types
    reanalysis_composite = reanalysis_composite.groupby('WT').mean(dim='T').unstack('grid')[Z250_var]
    reanalysis_composite['M'] = 0
    print("Reanalysis completed.")
    wt_anomalies = [] # initialize empty list
    wt_anomalies.append(reanalysis_composite)
    wt_anomalies = xr.concat(wt_anomalies, dim='M') # join together
    wt_anomalies['WT'] = wt_anomalies['WT'] + 1 # start from 1
#prepare a figure with rainfall and temperature composites
    X, Y = np.meshgrid(reanalysis[Z250_var].lon, reanalysis[Z250_var].lat)
    map_proj = ccrs.PlateCarree() #ccrs.Orthographic(-110, 10)
    data_proj = ccrs.PlateCarree()
    wt_unique = np.unique(wt_anomalies['WT'])
    figsize = (14, 8)
#WT proportions
    wt=weather_types.to_dataframe(name='WT')
    wt=wt+1
    wt_counts = wt.groupby('WT').size().div(wt['WT'].size)
    print("Beginning plotting..")
    #plotting
    xmin,xmax = reanalysis[lon_coord].min(), reanalysis[lon_coord].max()
    ymin,ymax = reanalysis[lat_coord].min(), reanalysis[lat_coord].max()
    plot_path = "{WK_DIR}/model/PS/model_plot.png".format(**os.environ)
    title_string = "{CASENAME}: Weather Types composite ({FIRSTYR}-{LASTYR})".format(**os.environ)
    # Set up the Figure
    plt.rcParams.update({'font.size': 12})
    fig, axes = plt.subplots(
            nrows=3, ncols=len(wt_unique), subplot_kw={'projection': map_proj},
            figsize=figsize, sharex=True, sharey=True
        )
    for i,w in enumerate(wt_unique):
        def selector(ds):
            times = wt.loc[wt['WT'] == w].index.get_level_values(time_coord)
            ds = ds.sel(T = np.in1d(ds.unstack('T')[time_coord], times))
            ds = ds.mean(dim = 'T')
            return(ds)
        # Top row: geopotential height anomalies
        ax = axes[0, i]
        ax.set_title('WT {}: {:.1%} of days'.format(w, wt_counts.values[i]))
        C0 = selector(reanalysis[Z250_var]).unstack('grid').plot.contourf(
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

        # Middle row: rainfall anomalies
        ax = axes[1, i]
        C1 = selector(rainfall[PRECT_var]).unstack('grid').plot.contourf(
            transform = data_proj,
            ax=ax,
            cmap = 'BrBG',
            extend="both",
            levels=np.linspace(-2, 2, 13),
            add_colorbar=False,
            add_labels=False
        )
        ax.coastlines()
        ax = axes[2, i]
        C2 = selector(t2m[tas_var]).unstack('grid').plot.contourf(
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
    cbar0.set_label('{Z250_var} anomaly [$m^2$/$s^2$]'.format(**os.environ), rotation=270)
    cbar0.ax.get_yaxis().labelpad = 20
    cbar1 = fig.colorbar(C1, cax=cax1)
    cbar1.set_label('{PRECT_var} anomaly [mm/d]'.format(**os.environ), rotation=270)
    cbar1.ax.get_yaxis().labelpad = 20
    cbar2 = fig.colorbar(C2, cax=cax2)
    cbar2.set_label('{T250_var} anomaly [$^o$C]'.format(**os.environ), rotation=270)
    cbar2.ax.get_yaxis().labelpad = 20
    fig = fig.savefig(plot_path, bbox_inches='tight')
    return fig

weatherTypes(os.environ["Z250_FILE"],os.environ["Z250_var"],os.environ["PRECT_FILE"],os.environ["PRECT_var"],os.environ["T250_FILE"],os.environ["T250_var"])
