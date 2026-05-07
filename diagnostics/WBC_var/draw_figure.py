import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import xarray as xr
import warnings

# Import necessary info from calculate_index
from calculate_index import current_name, alias_name, region_define

# =============================================================================
#  Plotting Functions
# =============================================================================

def spatial_plot(lon, lat, data, bthy_data=None, x_gsi=None, y_gsi=None, 
                 add_gsi=False, add_bathy=False, title='', levels=None, ax=None):
    """
    Standard spatial plot (Used in FIG1)
    """
    if ax is None:
        ax = plt.axes(projection=ccrs.PlateCarree())

    ax.coastlines(resolution='50m', color='k', linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='k', zorder=100)
    
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.5, color='gray', alpha=0.3, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False 
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}

    if levels is None:
        levels = np.linspace(0, 40, 41)
        
    cf = ax.contourf(lon, lat, data, levels=levels, cmap='Spectral_r', 
                     extend='both', transform=ccrs.PlateCarree())
    
    if add_bathy and bthy_data is not None:
        if hasattr(bthy_data, 'values'):
            bthy_val = bthy_data.values
        else:
            bthy_val = bthy_data
        
        vmin_b = np.nanmin(bthy_val)
        vmax_b = np.nanmax(bthy_val)
        start_lev = np.floor(vmin_b / 10) * 10
        end_lev = np.ceil(vmax_b / 10) * 10
        bthy_levels = np.arange(start_lev, end_lev + 10, 10)
        
        ax.contour(lon, lat, bthy_val, levels=bthy_levels, 
                   colors='black', linewidths=0.6, alpha=0.7, 
                   transform=ccrs.PlateCarree())

    if add_gsi and x_gsi is not None and y_gsi is not None:
        if len(x_gsi) > 0:
            ax.scatter(x_gsi, y_gsi, color='black', s=12, zorder=101, 
                       transform=ccrs.PlateCarree(), label='GSI Path')

    ax.set_title(title, fontsize=11, fontweight='bold')
    return cf

def ts_plot(time, data, label1='', x_data_2=None, y_data_2=None, label2='', xlab='', ylab='', ax=None):
    if ax is None:
        ax = plt.gca()
        
    ax.plot(time, data, color='gray', linewidth=0.8, label=label1)
    
    if x_data_2 is not None and y_data_2 is not None:
        ax.plot(x_data_2, y_data_2, color='red', linewidth=1.5, label=label2)
        
    ax.set_xlabel(xlab, fontsize=9)
    ax.set_ylabel(ylab, fontsize=9)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)

def spatial_scatter(lon, lat, data, title='', levels=None, ax=None, map_extent=None, gsi_lon_range=None):
    """
    Spatial Scatter Plot for FIG3
    """
    if ax is None:
        ax = plt.axes(projection=ccrs.PlateCarree())
        
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='k', zorder=100)
    
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    
    if map_extent:
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())
    else:
        valid_lon = lon[~np.isnan(lon)]
        valid_lat = lat[~np.isnan(lat)]
        if len(valid_lon) > 0 and len(valid_lat) > 0:
            xlim = (np.min(valid_lon) - 2, np.max(valid_lon) + 2)
            ylim = (np.min(valid_lat) - 2, np.max(valid_lat) + 2)
            ax.set_extent([xlim[0], xlim[1], ylim[0], ylim[1]], crs=ccrs.PlateCarree())
    
    if levels is None:
        abs_max = np.nanmax(np.abs(data))
        vmin, vmax = -abs_max, abs_max
    else:
        vmin, vmax = levels[0], levels[-1]

    if gsi_lon_range:
        lon_min, lon_max = gsi_lon_range
        mask = (lon >= lon_min) & (lon <= lon_max)
        lon = lon[mask]
        lat = lat[mask]
        data = data[mask]

    if len(lon) > 0:
        sc = ax.scatter(lon, lat, c=data, cmap='RdBu_r', s=15, 
                        vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree(), zorder=101)
    else:
        sc = ax.scatter([], [], c=[], cmap='RdBu_r', vmin=vmin, vmax=vmax)
    
    ax.set_title(title, fontsize=10)
    return sc

# =============================================================================
# Functions for Data Processing
# =============================================================================

def merge_dataset_dict(ds_obs, data_model_dict):
    """Dictionary to list for Histogram"""
    bar_colors = ["#2196F3", "#FF5722", "#009688", "#673AB7", "#F44336", "#E91E63", 
                  "#9C27B0", "#3F51B5", "#00BCD4", "#4CAF50", "#CDDC39", "#FFEB3B"]
    
    data_filled = []
    colors_filled = []
    labels_filled = []

    # OBS
    obs_val = ds_obs.values.flatten()
    data_filled.append(obs_val[~np.isnan(obs_val)])
    labels_filled.append('Obs')
    colors_filled.append('black')
    
    # Models
    for idx, (name, ds) in enumerate(data_model_dict.items()):
        color = bar_colors[idx % len(bar_colors)]
        if 'ensemble' in ds.dims:
            n_ens = ds.sizes['ensemble']
        else:
            n_ens = 1
            
        for i in range(n_ens):
            if n_ens > 1:
                val = ds.isel(ensemble=i).values.flatten()
            else:
                val = ds.values.flatten()
                
            data_filled.append(val[~np.isnan(val)])
            colors_filled.append(mcolors.to_rgba(color, alpha=0.7))
            labels_filled.append(f'{name}' if i == 0 else "")

    return data_filled, colors_filled, labels_filled

def find_bins_dict(ds_obs, data_model_dict):
    """
    Calculate bins for histogram.
    """
    vals = [ds_obs.values.flatten()]
    for ds in data_model_dict.values():
        vals.append(ds.values.flatten())
    all_data = np.concatenate(vals)
    all_data = all_data[~np.isnan(all_data)]
    
    if len(all_data) == 0:
        return np.linspace(0, 10, 11)
        
    x_max = np.nanmax(all_data)
    actual_max = max(x_max * 1.1, 10) 
    
    bins = np.linspace(0, actual_max, 31)
    return bins

# =============================================================================
# Main Figure Functions
# =============================================================================

def FIG1(ds_obs, data_model_dict, save_path, save_name):
    # (FIG1 Code - Same as before)
    model_names = list(data_model_dict.keys())
    n_models = len(model_names)
    n_rows = 1 + n_models
    n_ens_obs = ds_obs.sizes.get('ensemble', 1)
    max_ens_models = 0
    for ds in data_model_dict.values():
        ens = ds.sizes.get('ensemble', 1)
        if ens > max_ens_models: max_ens_models = ens
    n_cols = max(n_ens_obs, max_ens_models)
    
    fig = plt.figure(figsize=(6 * n_cols, 4.8 * n_rows))
    fig.suptitle(f'{current_name(save_name)} Index ({alias_name(save_name)})', x=0.5, y=0.92, fontsize=18)
    
    gs = fig.add_gridspec(n_rows, n_cols, hspace=0.6, wspace=0.3) 
    
    local_max = np.nanmax(ds_obs['sla_std'].values)
    for ds in data_model_dict.values():
        m = np.nanmax(ds['sla_std'].values)
        if m > local_max: local_max = m
    if local_max > 30: level = np.linspace(0, 40, 41)
    elif local_max > 20: level = np.linspace(0, 30, 31)
    else: level = np.linspace(0, 15, 16)
    gsi_filter_range = (290, 305) if save_name == 'gulf' else None

    # (1) OBS
    for j in range(n_cols):
        ax = fig.add_subplot(gs[0, j], projection=ccrs.PlateCarree())
        if j < n_ens_obs:
            ds_curr = ds_obs.isel(ensemble=j) if n_ens_obs > 1 else ds_obs.isel(ensemble=0)
            valid = np.isfinite(ds_curr['gsi_lat'].values)
            x_gsi = ds_curr['gsi_lon'].values[valid]
            y_gsi = ds_curr['gsi_lat'].values[valid]
            msl_data = ds_curr['msl'] if 'msl' in ds_curr else None
            cf = spatial_plot(ds_curr.coords['lon'], ds_curr.coords['lat'], ds_curr['sla_std'],
                              bthy_data=msl_data, x_gsi=x_gsi, y_gsi=y_gsi, add_gsi=True, add_bathy=True,
                              title=f'OBS ({alias_name(save_name)})', levels=level, ax=ax)
            cbar = fig.colorbar(cf, ax=ax, orientation='vertical', fraction=0.02, pad=0.03)
            cbar.set_label('Sea Level Std (cm)', fontsize=8)
            inset_ax = ax.inset_axes([0.0, -0.65, 1.0, 0.4]) 
            ts_plot(ds_curr['gsi_norm'].coords['time'], ds_curr['gsi_norm'], label1='Mon', 
                    x_data_2=ds_curr['gsi_norm'].coords['time'], y_data_2=ds_curr['gsi_annual'],
                    label2='Ann', xlab='Year', ylab='Index', ax=inset_ax)
        else:
            ax.set_visible(False)
            
    # (2) Models
    for i, name in enumerate(model_names):
        ds_mod = data_model_dict[name]
        n_ens = ds_mod.sizes.get('ensemble', 1)
        for j in range(n_cols):
            ax = fig.add_subplot(gs[i+1, j], projection=ccrs.PlateCarree())
            if j < n_ens:
                ds_curr = ds_mod.isel(ensemble=j) if n_ens > 1 else ds_mod.isel(ensemble=0)
                valid = np.isfinite(ds_curr['gsi_lat'].values)
                x_gsi = ds_curr['gsi_lon'].values[valid]
                y_gsi = ds_curr['gsi_lat'].values[valid]
                msl_data = ds_curr['msl'] if 'msl' in ds_curr else None
                cf = spatial_plot(ds_curr.coords['lon'], ds_curr.coords['lat'], ds_curr['sla_std'],
                                  bthy_data=msl_data, x_gsi=x_gsi, y_gsi=y_gsi, add_gsi=True, add_bathy=True,
                                  title=f'{name} ({alias_name(save_name)})', levels=level, ax=ax)
                cbar = fig.colorbar(cf, ax=ax, orientation='vertical', fraction=0.02, pad=0.03)
                cbar.set_label('Sea Level Std (cm)', fontsize=8)
                inset_ax = ax.inset_axes([0.0, -0.65, 1.0, 0.4])
                ts_plot(ds_curr['gsi_norm'].coords['time'], ds_curr['gsi_norm'], label1='Mon', 
                        x_data_2=ds_curr['gsi_norm'].coords['time'], y_data_2=ds_curr['gsi_annual'],
                        label2='Ann', xlab='Year', ylab='Index', ax=inset_ax)
            else:
                ax.set_visible(False)
    
    plt.savefig(save_path + 'WBCI.' + save_name + '.png', dpi=300, bbox_inches='tight')
    #plt.show()
    plt.close(fig)

def FIG2(ds_obs, data_model_dict, save_path, save_name):
    # (FIG2 Code - Same as before)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 16))
    plt.subplots_adjust(hspace=0.5)
    obs_var = ds_obs['alt_gsi_sd']
    mod_vars = {k: v['alt_gsi_sd'] for k, v in data_model_dict.items()}
    data, colors, labels = merge_dataset_dict(obs_var, mod_vars)
    bins = find_bins_dict(obs_var, mod_vars)
    ax1.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, label=labels, edgecolor='none')
    ax1.set_title(f'Amplitudes of {alias_name(save_name)} variability')
    handles, lbls = ax1.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax1.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)

    acf_obs = ds_obs['acf'].mean(dim='ensemble', skipna=True) if 'ensemble' in ds_obs.dims else ds_obs['acf']
    if acf_obs.ndim > 1: acf_obs = acf_obs.values[0]
    y_obs = acf_obs.values.flatten()
    ax2.plot(np.arange(len(y_obs)), y_obs, color='black', label='Obs', linewidth=2)
    color_idx = 0
    bar_colors = ["#2196F3", "#FF5722", "#009688", "#673AB7"]
    for name, ds in data_model_dict.items():
        c = bar_colors[color_idx % len(bar_colors)]
        acf_mod = ds['acf']
        n_ens = acf_mod.sizes.get('ensemble', 1)
        for i in range(n_ens):
            if n_ens > 1: y = acf_mod.isel(ensemble=i).values
            else: y = acf_mod.values
            y = y.flatten()
            if np.isnan(y).all(): continue
            lbl = name if i == 0 else ""
            ax2.plot(np.arange(len(y)), y, color=c, label=lbl, alpha=0.7)
        color_idx += 1
    ax2.set_title('Auto-correlation')
    ax2.axhline(0, color='k', linestyle='--', linewidth=0.5)
    handles, lbls = ax2.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax2.legend(by_label.values(), by_label.keys())

    obs_var = ds_obs['alt_damp_t']
    mod_vars = {k: v['alt_damp_t'] for k, v in data_model_dict.items()}
    data, colors, labels = merge_dataset_dict(obs_var, mod_vars)
    bins = find_bins_dict(obs_var, mod_vars)
    ax3.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, label=labels, edgecolor='none')
    ax3.set_title('e-folding time scales')
    handles, lbls = ax3.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax3.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)
    
    if save_path:
        plt.savefig(save_path + 'Amplitude_path_variability.' + str(save_name) + '.png', dpi=300)
    #plt.show()
    plt.close(fig)

def FIG3(ds_obs, data_model_dict, save_path, save_name):
    """
    Updated FIG3: Spatial Scatter (Maps) + Stats (Histograms & ACF)
    Modifications:
    1. Increase map vertical spacing (gs_spatial hspace=0.5) to fix overlap.
    2. Reduce spacing between Map and Stats panels (gs0 hspace=0.2) to move bottom plots up.
    3. Increase figure height (4.5 per row) to accommodate larger map spacing.
    """
    model_names = list(data_model_dict.keys())
    n_models = len(model_names)
    
    n_ens_obs = ds_obs.sizes.get('ensemble', 1)
    max_ens_models = 0
    for ds in data_model_dict.values():
        ens = ds.sizes.get('ensemble', 1)
        if ens > max_ens_models: max_ens_models = ens
    
    n_cols = max(n_ens_obs, max_ens_models)
    n_rows_map = 1 + n_models
    
    fig = plt.figure(figsize=(6 * n_cols, 4.5 * n_rows_map + 6))
    
    gs0 = gridspec.GridSpec(2, 1, height_ratios=[n_rows_map * 2, 4], hspace=0.1)
    
    reg_bounds = region_define(save_name)
    map_extent = [reg_bounds['lon'].start, reg_bounds['lon'].stop,
                  reg_bounds['lat'].start, reg_bounds['lat'].stop]
    gsi_filter_range = (290, 305) if save_name == 'gulf' else None
    pc_to_plot = 0 

    # === (A) Spatial Scatter Panel (Maps) ===
    gs_spatial = gridspec.GridSpecFromSubplotSpec(n_rows_map, n_cols, subplot_spec=gs0[0],
                                                  wspace=0.3, hspace=0.5)
    
    # A-1. OBS Maps
    for j in range(n_cols):
        ax = plt.subplot(gs_spatial[0, j], projection=ccrs.PlateCarree())
        if j < n_ens_obs:
            ds_curr = ds_obs.isel(ensemble=j)
            eof_pat = ds_curr['eofs_gsi'].isel(mode=pc_to_plot).values
            var_pct = ds_curr['per_var_gsi'].isel(mode=pc_to_plot).values * 100
            sc = spatial_scatter(ds_curr['gsi_lon'].values, ds_curr['gsi_lat'].values, eof_pat,
                                 title=f'Obs EOF{pc_to_plot+1}\n(% Var = {var_pct:.1f})',
                                 ax=ax, map_extent=map_extent, gsi_lon_range=gsi_filter_range)
            cbar = fig.colorbar(sc, ax=ax, orientation='vertical', fraction=0.02, pad=0.03)
            cbar.set_label('', fontsize=8)
        else:
            ax.set_visible(False)

    # A-2. Model Maps
    for i, name in enumerate(model_names):
        ds_mod = data_model_dict[name]
        n_ens = ds_mod.sizes.get('ensemble', 1)
        for j in range(n_cols):
            ax = plt.subplot(gs_spatial[i+1, j], projection=ccrs.PlateCarree())
            if j < n_ens:
                ds_curr = ds_mod.isel(ensemble=j)
                eof_pat = ds_curr['eofs_gsi'].isel(mode=pc_to_plot).values
                var_pct = ds_curr['per_var_gsi'].isel(mode=pc_to_plot).values * 100
                sc = spatial_scatter(ds_curr['gsi_lon'].values, ds_curr['gsi_lat'].values, eof_pat,
                                     title=f'{name} EOF{pc_to_plot+1}\n(% Var = {var_pct:.1f})',
                                     ax=ax, map_extent=map_extent, gsi_lon_range=gsi_filter_range)
                cbar = fig.colorbar(sc, ax=ax, orientation='vertical', fraction=0.02, pad=0.03)
                cbar.set_label('', fontsize=8)
            else:
                ax.set_visible(False)

    # === (B) Stats Panel (Histograms & ACF) ===
    gs_hist = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs0[1],
                                               wspace=0.4, hspace=0.6)
    
    bar_colors = ["#2196F3", "#FF5722", "#009688", "#673AB7", "#F44336"]
    
    # B-1
    ax1 = plt.subplot(gs_hist[0, 0])
    obs_var = ds_obs['per_var_gsi'].isel(mode=pc_to_plot) * 100
    mod_vars = {name: ds['per_var_gsi'].isel(mode=pc_to_plot) * 100 for name, ds in data_model_dict.items()}
    data, colors, labels = merge_dataset_dict(obs_var, mod_vars)
    bins = find_bins_dict(obs_var, mod_vars)
    ax1.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, label=labels, edgecolor='none')
    ax1.set_title(f'Variance Explained (EOF{pc_to_plot+1})', fontsize=10)
    ax1.set_xlabel('% Variance', fontsize=8)
    handles, lbls = ax1.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax1.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=6)

    # B-2
    ax2 = plt.subplot(gs_hist[0, 1])
    obs_var = ds_obs['alt_cross'].isel(mode=pc_to_plot)
    if 'ensemble' in obs_var.dims: obs_var = obs_var.isel(ensemble=0)
    mod_vars = {}
    for name, ds in data_model_dict.items():
        var = ds['alt_cross'].isel(mode=pc_to_plot)
        if 'ensemble' in var.dims: var = var.isel(ensemble=0)
        mod_vars[name] = var
    data, colors, labels = merge_dataset_dict(obs_var, mod_vars)
    bins = find_bins_dict(obs_var, mod_vars)
    ax2.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, label=labels, edgecolor='none')
    ax2.set_title(f'Zero Crossings (EOF{pc_to_plot+1})', fontsize=10)
    ax2.set_xlabel('Count', fontsize=8)
    handles, lbls = ax2.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax2.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=6)

    # B-3
    ax3 = plt.subplot(gs_hist[1, 0])
    obs_var = ds_obs['alt_damp_s']
    mod_vars = {name: ds['alt_damp_s'] for name, ds in data_model_dict.items()}
    data, colors, labels = merge_dataset_dict(obs_var, mod_vars)
    bins = find_bins_dict(obs_var, mod_vars)
    ax3.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, label=labels, edgecolor='none')
    ax3.set_title('Spatial e-folding scales', fontsize=10)
    ax3.set_xlabel('Scale (points)', fontsize=8)
    handles, lbls = ax3.get_legend_handles_labels()
    by_label = dict(zip(lbls, handles))
    if "" in by_label: del by_label[""]
    ax3.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=6)

    # B-4
    ax4 = plt.subplot(gs_hist[1, 1])
    acf_s_obs = ds_obs['acf_spatial']
    if 'ensemble' in acf_s_obs.dims: acf_s_obs = acf_s_obs.mean(dim='ensemble', skipna=True)
    y_obs = acf_s_obs.values.flatten()
    ax4.plot(np.arange(len(y_obs)), y_obs, color='black', label='Obs')
    col_idx = 0
    for idx, (name, ds) in enumerate(data_model_dict.items()):
        c = bar_colors[idx % len(bar_colors)]
        acf_mod = ds['acf_spatial']
        n_ens = acf_mod.sizes.get('ensemble', 1)
        for i in range(n_ens):
            if n_ens > 1: y = acf_mod.isel(ensemble=i).values
            else: y = acf_mod.values
            y = y.flatten()
            lbl = name if i == 0 else ""
            ax4.plot(np.arange(len(y)), y, color=c, label=lbl, alpha=0.7)
    ax4.set_title(f'Spatial Auto-correlation ({alias_name(save_name)})', fontsize=10)
    ax4.set_xlabel('Lag', fontsize=8)
    ax4.axhline(0, color='k', linestyle='--', linewidth=0.5)
    ax4.legend(loc='upper right', fontsize=6)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path + 'EOF_path_variability.' + str(save_name) + '.png', dpi=300)
    #plt.show()
    plt.close(fig)
