#!/usr/bin/env python
# coding: utf-8

# In[1]:


import netCDF4 as nc
import numpy as np
import xarray as xr
import warnings
    
    
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import cmocean as cmo

from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

#from postprocessing import *
from calculate_index import *


# In[24]:


def spatial_plot(x_data, y_data, z_data, bthy_data=None, levels=None, x_gsi=None, y_gsi=None, 
                 add_bathy=False, add_gsi=False, save=False, sv_pth=None, sv_name=None, ax=None, title=None):

    bbox = [x_data.min().values, x_data.max().values, y_data.min().values, y_data.max().values]
    
    ax.set_extent(bbox, crs=ccrs.PlateCarree())

    # Add features to the map
    ax.add_feature(cfeature.COASTLINE, zorder=1)
    ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', linestyle=':')
    gl.top_labels = gl.right_labels = False
    gl.xformatter = LongitudeFormatter(degree_symbol='')
    gl.yformatter = LatitudeFormatter(degree_symbol='')
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}


    # xarray 데이터를 numpy 배열로 변환
    z_data = z_data.values if isinstance(z_data, xr.DataArray) else z_data
    z_data = np.nan_to_num(z_data, nan=0.0)
    
    
    # Define color levels if not provided

    # Contour plot
    colorplot = ax.contourf(x_data, y_data, z_data, levels=levels, cmap='Spectral_r', zorder=0, transform=ccrs.PlateCarree())

    # Bathymetry contours
    if add_bathy and bthy_data is not None:
        levels_bathy = np.arange(-100, 101, 10)
        #contours = ax.contour(x_data, y_data, abs(bthy_data), levels=levels_bathy, colors='k', linewidths=0.75, zorder=2)
        contours = ax.contour(x_data, y_data, (bthy_data), levels=levels_bathy, colors='k', linewidths=0.5, zorder=2)
        ax.clabel(contours, inline=True, fontsize=6)

    # Add Gulf Stream Index points
    if add_gsi and x_gsi is not None and y_gsi is not None:
        ax.scatter(x_gsi, y_gsi, s=3, color='black', label='Points', zorder=3)

    # Set labels and title
    ax.set_xlabel('Longitude', fontsize=8)
    ax.set_ylabel('Latitude', fontsize=8)

    ax.set_title(title, fontsize=6)

    # Add colorbar
    cbar = plt.colorbar(colorplot, ax=ax, fraction=0.02, pad=0.04, ticks=np.linspace(levels[0], levels[-1], 5))
    cbar.set_label('STD [cm]', size=8)
    cbar.ax.tick_params(labelsize=8)

    
    return ax

def ts_plot(x_data, y_data, label1='', x_data_2=None, y_data_2=None, label2='', xlab='', ylab='', title=None, 
            save=False, sv_pth=None, sv_name=None, ax=None):
    # ax가 없으면 새 figure와 ax를 생성
    #if ax is None:
    #    fig, ax = plt.subplots(figsize=(10, 6))
    #else:
    #    fig = None  # 외부에서 ax를 전달받은 경우 fig는 None으로 설정
    """
    # x_data_2와 y_data_2가 None이 아니면 빈 배열인지 확인
    if x_data_2 is not None and y_data_2 is not None:
        if isinstance(x_data_2, np.ndarray) and isinstance(y_data_2, np.ndarray):
            if x_data_2.size > 0 and y_data_2.size > 0:
                min_length = min(len(x_data_2), len(y_data_2))
                x_data_2 = x_data_2[:min_length]
                y_data_2 = y_data_2[:min_length]
        else:
            if len(x_data_2) > 0 and len(y_data_2) > 0:
                min_length = min(len(x_data_2), len(y_data_2))
                x_data_2 = x_data_2[:min_length]
                y_data_2 = y_data_2[:min_length]
    """
    #print(x_data,y_data,x_data_2,y_data_2)
    # 기준선 (y=0)
    ax.axhline(0, color='k', linewidth=1)

    # 첫 번째 데이터 플롯
    ax.plot(x_data, y_data, color='k', linewidth=1, label=label1)
    
    # 두 번째 데이터가 있을 경우 플롯
    if x_data_2 is not None and y_data_2 is not None:
        ax.plot(x_data_2, y_data_2, color='r', linewidth=1, label=label2)

    # 범례, 축 레이블, 제목 설정
    ax.legend(fontsize=3)
    ax.set_xlabel(xlab, fontsize=3)
    ax.set_ylabel(ylab, fontsize=3)
    ax.tick_params(axis='x', labelsize=3)
    ax.tick_params(axis='y', labelsize=3)
    #ax.set_xticks(fontsize=18)
    #ax.set_yticks(fontsize=18)
    
    # y_data_2가 비어 있지 않은 경우 처리
    if y_data_2 is not None and y_data_2.size > 0:
        max_y = max(np.max(np.abs(y_data)), np.max(np.abs(y_data_2)))
        ax.set_ylim([-max_y - 0.1, max_y + 0.1])
    else:
        max_y = np.max(np.abs(y_data))
        ax.set_ylim([-max_y - 0.1, max_y + 0.1])

    # 제목 설정
    #ax.set_title(title, fontsize=10)
    
    return ax


def FIG1(ds_obs, ds_low, ds_high, MODEL_NAME, save_path, save_name):
    # 각 데이터셋별 ensemble size (없으면 1)
    n_ens_obs  = ds_obs.sizes.get('ensemble', 1)
    n_ens_low  = ds_low.sizes.get('ensemble', 1)
    n_ens_high = ds_high.sizes.get('ensemble', 1)
    # 전체 열 개수는 최대 ensemble size로
    n_max = max(n_ens_obs, n_ens_low, n_ens_high)
    
    # 총 3행(obs, low, high), n_max열의 GridSpec
    fig = plt.figure(figsize=(3 * n_max, 12))
    fig.suptitle(f'{current_name(save_name)} Index ({alias_name(save_name)})',x=0.5, y=0.8, fontsize=16)
    gs = fig.add_gridspec(3, n_max, hspace=-0.7, wspace=0.6)

    # 전체 제목 추가 (맨 위에)
    
    
    # Set levels based on the maximum level value
    # Calculate the maximum level from the three datasets
    max_level = max(ds_obs['sla_std'].max().item() , ds_low['sla_std'].max().item() , ds_high['sla_std'].max().item() )
    if max_level > 40:
        level = np.linspace(0, 50, 51)
    elif max_level > 30:
        level = np.linspace(0, 40, 31)
    elif max_level > 20:
        level = np.linspace(0, 30, 31)
    elif max_level > 10:
        level = np.linspace(0, 20, 31)
    else:
    # Default case if max_level is 10 or below
        level = np.linspace(0, 10, 11)

    
    # ========== (1) 관측 (OBS) - 첫 번째 행 ========== 
    for j in range(n_max):
        # j번째 열
        ax = fig.add_subplot(gs[0, j], projection=ccrs.PlateCarree())
        if j < n_ens_obs:
            # --- Spatial Plot (지도) ---
            spatial_plot(
                ds_obs['sla'].isel(ensemble=j).coords['lon'],
                ds_obs['sla'].isel(ensemble=j).coords['lat'],
                ds_obs['sla_std'].isel(ensemble=j),
                bthy_data=ds_obs['msl'].isel(ensemble=j),
                x_gsi=ds_obs['gsi_lon'].isel(ensemble=j),
                y_gsi=ds_obs['gsi_lat'].isel(ensemble=j),
                add_gsi=True, add_bathy=True,
                save=False, 
                title=f'{alias_name(save_name)} (Altimetry, OBS ~0.25°)', levels=level,
                ax=ax
            )
            
            # --- Time Series Plot을 위한 Inset Axes ---
            # (지도 아래쪽에 0.1, 0.05부터 width=0.8, height=0.3 영역)
            #inset_ax = ax.inset_axes([0.1, 0.05, 0.8, 0.3])
            inset_ax = ax.inset_axes([0.0, -1.2, 1.0, 0.7],transform=ax.transAxes, clip_on=False)
            ts_plot(
                ds_obs['gsi_norm'].isel(ensemble=j).coords['time'],
                ds_obs['gsi_norm'].isel(ensemble=j), 
                label1='Monthly Index',
                x_data_2=ds_obs['time'][::12],
                y_data_2=ds_obs['gsi_annual'].isel(ensemble=j),
                label2='Annual Index',
                xlab='Year', ylab=alias_name(save_name), 
                title='',  # 필요하면 타이틀 생략 or 짧게
                save=False, sv_pth=False, sv_name='alt_gsi_monthly_annual',
                ax=inset_ax
            )
        else:
            # ensemble 범위를 벗어나면 subplot 숨김
            ax.set_visible(False)
    
    # ========== (2) Low-resolution 모델 - 두 번째 행 ========== 
    for j in range(n_max):
        ax = fig.add_subplot(gs[1, j], projection=ccrs.PlateCarree())
        if j < n_ens_low:
            # --- Spatial Plot ---
            spatial_plot(
                ds_low['sla'].isel(ensemble=j).coords['lon'],
                ds_low['sla'].isel(ensemble=j).coords['lat'],
                ds_low['sla_std'].isel(ensemble=j),
                bthy_data=ds_low['msl'].isel(ensemble=j),
                x_gsi=ds_low['gsi_lon'].isel(ensemble=j),
                y_gsi=ds_low['gsi_lat'].isel(ensemble=j),
                add_gsi=True, add_bathy=True,
                save=False, 
                title=f'{alias_name(save_name)} ({MODEL_NAME[j]}, low-res ~1.0°)', levels=level,
                ax=ax
            )
            
            # --- Inset Axes for TS ---
            #inset_ax = ax.inset_axes([0.1, 0.05, 1.0, 0.5])
            inset_ax = ax.inset_axes([0.0, -1.2, 1.0, 0.7],transform=ax.transAxes, clip_on=False)
            ts_plot(
                ds_low['gsi_norm'].isel(ensemble=j).coords['time'],
                ds_low['gsi_norm'].isel(ensemble=j), 
                label1='Monthly Index',
                x_data_2=ds_low['time'][::12],
                y_data_2=ds_low['gsi_annual'].isel(ensemble=j),
                label2='Annual Index',
                xlab='Year', ylab=alias_name(save_name), 
                title='',  
                save=False, sv_pth=False, sv_name='alt_gsi_monthly_annual',
                ax=inset_ax
            )
        else:
            ax.set_visible(False)
    
    # ========== (3) High-resolution 모델 - 세 번째 행 ========== 
    for j in range(n_max):
        ax = fig.add_subplot(gs[2, j], projection=ccrs.PlateCarree())
        if j < n_ens_high:
            # --- Spatial Plot ---
            spatial_plot(
                ds_high['sla'].isel(ensemble=j).coords['lon'],
                ds_high['sla'].isel(ensemble=j).coords['lat'],
                ds_high['sla_std'].isel(ensemble=j),
                bthy_data=ds_high['msl'].isel(ensemble=j),
                x_gsi=ds_high['gsi_lon'].isel(ensemble=j),
                y_gsi=ds_high['gsi_lat'].isel(ensemble=j),
                add_gsi=True, add_bathy=True,
                save=False, 
                title=f'{alias_name(save_name)} ({MODEL_NAME[j]}, high-res {model_resolution(MODEL_NAME[j])})', levels=level,
                ax=ax
            )
            
            # --- Inset Axes for TS ---
            #inset_ax = ax.inset_axes([0.1, 0.05, 0.8, 0.3])
            inset_ax = ax.inset_axes([0.0, -1.2, 1.0, 0.7],transform=ax.transAxes, clip_on=False)
            ts_plot(
                ds_high['gsi_norm'].isel(ensemble=j).coords['time'],
                ds_high['gsi_norm'].isel(ensemble=j), 
                label1='Monthly Index',
                x_data_2=ds_high['time'][::12],
                y_data_2=ds_high['gsi_annual'].isel(ensemble=j),
                label2='Annual Index',
                xlab='Year', ylab=alias_name(save_name), 
                title='',
                save=False, sv_pth=False, sv_name='alt_gsi_monthly_annual',
                ax=inset_ax
            )
        else:
            ax.set_visible(False)
    
    # 전체 레이아웃 여백 조정
    
    plt.subplots_adjust(left=0.06, right=0.94, top=0.95, bottom=0.05)
    
    plt.savefig(save_path + 'WBCI.' + save_name + '.png', dpi=900)
    #plt.show()
    plt.close(fig)


# In[25]:


def merge_dataset(ds_obs,ds_low,ds_hi,MODEL_NAME):
    

    
    # ensemble 수 (모델 수)
    n_ens_obs  = ds_obs.sizes.get('ensemble', 1)
    n_ens_low  = ds_low.sizes.get('ensemble', 1)
    n_ens_hi   = ds_hi.sizes.get('ensemble', 1)   

    # FIG2와 동일한 색상 지정
    #bar_colors = ['yellow', 'orange', 'green', 'purple', 'brown', 'gray', 'brown', 'blue', 'red']
    """bar_colors = [
    '#2196F3',  # Blue
    '#FF9800',  # Vivid Orange
    '#F44336',  # Red
    '#9C27B0',  # Vivid Purple
    '#795548',  # Brown
    '#607D8B',  # Blue Grey
    '#00BCD4',  # Cyan
    '#FFC107',  # Amber
    '#8BC34A'  # Vivid Green
    ]"""
    bar_colors = [
    "#2196F3",  # Blue
    "#FF5722",  # Deep Orange
    "#009688",  # Teal
    "#673AB7",  # Deep Purple
    "#F44336",  # Red
    "#E91E63",  # Pink
    "#9C27B0",  # Purple
    "#3F51B5",  # Indigo
    "#00BCD4",  # Cyan
    "#4CAF50",  # Green
    "#CDDC39",  # Lime
    "#FFEB3B",  # Yellow
    "#FFC107",  # Amber
    "#FF9800",  # Orange
    "#795548",  # Brown
    "#607D8B"   # Blue Grey
    ]
    
    data_filled = []
    colors_filled = []
    labels_filled = []

    data_filled.append(np.atleast_1d(ds_obs.values))
    labels_filled.append('Altimetry-res ~0.25°')
    colors_filled.append('black')
    
    for i in range(n_ens_low):
        data_filled.append(np.atleast_1d(ds_low.isel(ensemble=i).values))
        colors_filled.append(mcolors.to_rgba(bar_colors[i], alpha=0.5))
        labels_filled.append(f'Low-res ~1.0°: {MODEL_NAME[i]}')
    
    for i in range(n_ens_hi):
        data_filled.append(np.atleast_1d(ds_hi.isel(ensemble=i).values))
        colors_filled.append(bar_colors[i])
        labels_filled.append(f'High-res {model_resolution(MODEL_NAME[i])}: {MODEL_NAME[i]}')

    return data_filled, colors_filled, labels_filled


def find_bins(ds_obs,ds_low,ds_hi):
    # x축 bin 범위를 ds_obs, ds_low, ds_hi 의 alt_gsi_sd 최대값+3 로 지정
    all_data = np.concatenate([
        ds_obs.values.ravel(),
        ds_low.values.ravel(),
        ds_hi.values.ravel()
    ])
    x_max = np.nanmax(all_data) + 3
    bins = np.linspace(0, x_max, 31)  # ax1과 동일한 bin 설정

    return bins


def FIG2(ds_obs, ds_low, ds_hi, MODEL_NAME, save_path=False, save_name=False):
    
    # ensemble 수 (모델 수)
    n_ens_obs  = ds_obs.sizes.get('ensemble', 1)
    n_ens_low  = ds_low.sizes.get('ensemble', 1)
    n_ens_hi   = ds_hi.sizes.get('ensemble', 1)
    n_models = len(MODEL_NAME)
    
  
    
    # Figure 및 서브플롯 생성 (3행 1열, 세로로 배치)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 16))
    plt.subplots_adjust(hspace=0.5)  # 서브플롯 사이 간격 추가

    # merge dataset
    data, colors, labels = merge_dataset(ds_obs['alt_gsi_sd'],ds_low['alt_gsi_sd'],ds_hi['alt_gsi_sd'],MODEL_NAME)
    bins = find_bins(ds_obs['alt_gsi_sd'],ds_low['alt_gsi_sd'],ds_hi['alt_gsi_sd'])
    
    ax1.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, linewidth=1, label=labels)

    ax1.set_title('Amplitudes of the ' + alias_name(save_name) + ' variability', fontsize=15)
    ax1.set_xlabel('Mean Standard Deviation at '+alias_name(save_name)+' Locations [cm]', fontsize=15)
    ax1.yaxis.set_visible(False)
    ax1.set_ylim(0, 7)
    
    # custom legend 생성 (ax1)
    legend_handles_ax1 = []
    
    for i, label in enumerate(labels):
        legend_handles_ax1.append(mpatches.Patch(facecolor=colors[i], edgecolor=colors[i], 
                                             label=label, linewidth=1))
    
    ax1.legend(handles=legend_handles_ax1, fontsize=8, loc='upper right')
    ax1.xaxis.set_tick_params(labelsize=8)

    
    # --- (2) Time scales: ACF Plot (ax2) ---
    
    ax2.plot(np.arange(len(ds_obs['acf'][0])), np.mean(ds_obs['acf'], axis=0), color=colors[0], label=labels[0])
    
    for i, model in enumerate(MODEL_NAME):
        ax2.plot(np.arange(len(ds_low['acf'].isel(ensemble=i))), ds_low['acf'].isel(ensemble=i).values, color=colors[i+1],
                 label=labels[i+1], linestyle=':')
        ax2.plot(np.arange(len(ds_hi['acf'].isel(ensemble=i))), ds_hi['acf'].isel(ensemble=i).values, color=colors[i+n_ens_low+1],
                 label=labels[i+n_ens_low+1])

    
    ax2.set_title('Auto-correlation of ' + alias_name(save_name), fontsize=15)
    ax2.set_xlabel('Lag (Months)', fontsize=15)
    ax2.set_ylabel('ACF', fontsize=15)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.yaxis.set_tick_params(labelsize=8)
    ax2.xaxis.set_tick_params(labelsize=8)

    
    # --- (3) e-folding time scales Histogram (ax3) ---

    # merge dataset
    data, colors, labels = merge_dataset(ds_obs['alt_damp_t'],ds_low['alt_damp_t'],ds_hi['alt_damp_t'],MODEL_NAME)
    bins = find_bins(ds_obs['alt_damp_t'],ds_low['alt_damp_t'],ds_hi['alt_damp_t'])
    
    ax3.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, linewidth=1, label=labels)

    ax3.set_title('e-folding time scales', fontsize=15)
    ax3.set_xlabel('e-folding Scale of ACF (Months)', fontsize=15)
    
    # custom legend 생성 (ax1)
    legend_handles_ax3 = []
    
    for i, label in enumerate(labels):
        legend_handles_ax3.append(mpatches.Patch(facecolor=colors[i], edgecolor=colors[i], 
                                             label=label, linewidth=1))
    
    ax3.legend(handles=legend_handles_ax3, fontsize=8, loc='upper right')
        
    ax3.xaxis.set_tick_params(labelsize=8)
    ax3.yaxis.set_visible(False)
    ax3.set_ylim(0, 7)

    #plt.tight_layout()
    if save_path and save_name:
        region_str = save_name if isinstance(save_name, str) else str(save_name)
        plt.savefig(save_path + 'Amplitude_path_variability.' + region_str + '.png', dpi=900)
    #plt.show()
    plt.close(fig)


# In[26]:


def spatial_scatter(x_data, y_data, z_data, title='', label='EOF', save=False, sv_pth=None, sv_name=None, ax=None):
    
    # Choose region to plot

    bounds = region_define(sv_name)
    bbox = [bounds['lon'].start, bounds['lon'].stop, bounds['lat'].start, bounds['lat'].stop]
    # ax가 없을 경우 새 figure와 ax 생성
    if ax is None:
        fig = plt.figure(figsize=(14, 8))
        crs = ccrs.PlateCarree()
        ax = plt.subplot(1, 1, 1, projection=crs)
    else:
        fig = None  # 외부에서 ax를 전달받은 경우 fig는 None으로 설정

    ax.set_extent(bbox, ccrs.PlateCarree())

    # Add Filled Coastline
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, facecolor='k', zorder=1)

    # Add Gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', linestyle=':')
    gl.top_labels = gl.right_labels = False
    gl.xformatter = LongitudeFormatter(degree_symbol='')
    gl.yformatter = LatitudeFormatter(degree_symbol='')

    # Add labels
    ax.set_xlabel('Latitude', fontsize=8)
    ax.set_ylabel('Longitude', fontsize=8)
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    # Scatter plot
    max_data = 0.40
    scat = ax.scatter(x_data, y_data, s=abs(z_data * 30), c=z_data, vmin=-max_data, vmax=max_data, cmap='cmo.balance')

    # Title
    ax.set_title(title, fontsize=10)

    # Add a background map (white background)
    ax.imshow(np.tile(np.array([[[255, 255, 255]]], dtype=np.uint8), [2, 2, 1]),
              origin='upper', transform=ccrs.PlateCarree(), extent=[-180, 180, -90, 90])

    # Colorbar (label을 빈 문자열로 설정하여 "EOF1" 제거)
    cbar = plt.colorbar(scat, fraction=0.02, pad=0.04, ticks=np.linspace(-max_data, max_data, 9))
    ticks = cbar.get_ticks()
    ticklabels = [f'{tick:.{2}f}' for tick in ticks]
    cbar.set_ticklabels(ticklabels)
    cbar.set_label('', size='10', labelpad=15)  # label을 ''로 변경
    cbar.ax.tick_params(labelsize=8)
    
    # 저장 또는 출력
    if save and sv_pth:
        plt.savefig(sv_pth + sv_name + '.png', format='png', bbox_inches="tight", dpi=900)

    if fig is not None:
        plt.close(fig)



def FIG3(ds_obs, ds_low, ds_hi, MODEL_NAME, save_path=False, save_name=False):


    # 각 데이터셋별 ensemble 수
    n_ens_obs  = ds_obs.sizes.get('ensemble', 1)
    n_ens_low  = ds_low.sizes.get('ensemble', 1)
    n_ens_hi   = ds_hi.sizes.get('ensemble', 1)
    n_max = max(n_ens_obs, n_ens_low, n_ens_hi)
    n_models = len(MODEL_NAME)
    # FIG2와 동일한 색상 지정
    low_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:n_models]
    high_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:n_models]

    # EOF mode 선택 (예: 첫 번째 EOF)
    pc_to_plot = 1

    # 전체 figure (spatial scatter 3행, histogram 2행)
    fig = plt.figure(figsize=(3*n_max, 15))
    gs0 = gridspec.GridSpec(2, 1, height_ratios=[3, 2], hspace=0.1)
    
    # === (A) Spatial Scatter Panel (3 rows × n_max columns) ===
    gs_spatial = gridspec.GridSpecFromSubplotSpec(3, n_max, subplot_spec=gs0[0],
                                                  wspace=0.5, hspace=0.0)
    # OBS spatial scatter (row 0)
    for j in range(n_max):
        if n_max == 1:
            ax = plt.subplot(gs_spatial[j], projection=ccrs.PlateCarree())
        else:
            ax = plt.subplot(gs_spatial[0, j], projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.tick_params(labelsize=8)
        if j < n_ens_obs:
            spatial_scatter(
                ds_obs['gsi_lon'].isel(ensemble=j),
                ds_obs['gsi_lat'].isel(ensemble=j),
                ds_obs['eofs_gsi'].isel(ensemble=j)[pc_to_plot-1],
                label='EOF' + str(pc_to_plot),
                title=('Obs EOF' + str(pc_to_plot) + " - Altimetry " + 
                       "\n(% Var = " + '%1.2f' % (ds_obs['per_var_gsi'].isel(ensemble=j)[pc_to_plot-1]*100) + ")"),
                save=False, sv_pth=False, sv_name=save_name,
                ax=ax,
            )
            ax.title.set_fontsize(8)
        else:
            ax.set_visible(False)

    # Low-resolution spatial scatter (row 1) → 제목에 MODEL_NAME 사용
    for j in range(n_max):
        ax = plt.subplot(gs_spatial[1, j], projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.tick_params(labelsize=8)
        if j < n_ens_low:
            spatial_scatter(
                ds_low['gsi_lon'].isel(ensemble=j),
                ds_low['gsi_lat'].isel(ensemble=j),
                ds_low['eofs_gsi'].isel(ensemble=j)[pc_to_plot-1],
                label='EOF' + str(pc_to_plot),
                title=('Low-res EOF' + str(pc_to_plot) + " - " + MODEL_NAME[j] +
                       "\n(% Var = " + '%1.2f' % (ds_low['per_var_gsi'].isel(ensemble=j)[pc_to_plot-1]*100) + ")"),
                save=False, sv_pth=False, sv_name=save_name,
                ax=ax,
            )
            ax.title.set_fontsize(8)
        else:
            ax.set_visible(False)

    # High-resolution spatial scatter (row 2) → 제목에 MODEL_NAME 사용
    for j in range(n_max):
        ax = plt.subplot(gs_spatial[2, j], projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.tick_params(labelsize=8)
        if j < n_ens_hi:
            spatial_scatter(
                ds_hi['gsi_lon'].isel(ensemble=j),
                ds_hi['gsi_lat'].isel(ensemble=j),
                ds_hi['eofs_gsi'].isel(ensemble=j)[pc_to_plot-1],
                label='EOF' + str(pc_to_plot),
                title=('High-res EOF' + str(pc_to_plot) + " - " + MODEL_NAME[j] +
                       "\n(% Var = " + '%1.2f' % (ds_hi['per_var_gsi'].isel(ensemble=j)[pc_to_plot-1]*100) + ")"),
                save=False, sv_pth=False, sv_name=save_name,
                ax=ax,
            )
            ax.title.set_fontsize(8)
        else:
            ax.set_visible(False)

    
    # === (B) Histogram Panel (2 x 2 grid) ===
    gs_hist = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs0[1],
                                               wspace=0.3, hspace=0.3)
    # (B1) Percent Variance Explained: First EOF of GSI
    ax1 = plt.subplot(gs_hist[0, 0])
    
    # merge dataset
    data, colors, labels = merge_dataset(ds_obs['alt_var'][:,0]*100,ds_low['alt_var'][:,0]*100,ds_hi['alt_var'][:,0]*100,MODEL_NAME)
    bins = find_bins(ds_obs['alt_var'][:,0]*100,ds_low['alt_var'][:,0]*100,ds_hi['alt_var'][:,0]*100)
    
    ax1.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, linewidth=1, label=labels)

    ax1.set_title('Percent Variance Explained: First EOF of '+alias_name(save_name), fontsize=10)
    ax1.set_xlabel('Percent Variance', fontsize=8)

    ax1.yaxis.set_visible(False)
    ax1.set_ylim(0, 7)
    
    # custom legend 생성 (ax1)
    legend_handles_ax1 = []
    
    for i, label in enumerate(labels):
        legend_handles_ax1.append(mpatches.Patch(facecolor=colors[i], edgecolor=colors[i], 
                                             label=label, linewidth=1))
    
    ax1.legend(handles=legend_handles_ax1, fontsize=6, loc='upper right')
    ax1.xaxis.set_tick_params(labelsize=8)

   
    # (B2) Number of Zero Crossings: First EOF of GSI
    ax2 = plt.subplot(gs_hist[0, 1])

    # merge dataset
    data, colors, labels = merge_dataset(ds_obs['alt_cross'][:,0],ds_low['alt_cross'][:,0],ds_hi['alt_cross'][:,0],MODEL_NAME)
    bins = find_bins(ds_obs['alt_cross'][:,0],ds_low['alt_cross'][:,0],ds_hi['alt_cross'][:,0])
    
    ax2.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, linewidth=1, label=labels)

    ax2.set_title('Number of Zero Crossings: First EOF of '+alias_name(save_name), fontsize=10)
    ax2.set_xlabel('Number of Zero Crossings', fontsize=8)
    
    ax2.yaxis.set_visible(False)
    ax2.set_ylim(0, 7)
    
    # custom legend 생성 (ax1)
    legend_handles_ax2 = []
    
    for i, label in enumerate(labels):
        legend_handles_ax2.append(mpatches.Patch(facecolor=colors[i], edgecolor=colors[i], 
                                             label=label, linewidth=1))
    
    ax2.legend(handles=legend_handles_ax2, fontsize=6, loc='upper right')
    ax2.xaxis.set_tick_params(labelsize=8)
    
    
    
    # (B3) e-folding spatial scales
    ax3 = plt.subplot(gs_hist[1, 0])
        
    data, colors, labels = merge_dataset(ds_obs['alt_damp_s'],ds_low['alt_damp_s'],ds_hi['alt_damp_s'],MODEL_NAME)
    bins = find_bins(ds_obs['alt_damp_s'],ds_low['alt_damp_s'],ds_hi['alt_damp_s'])
    
    ax3.hist(data, stacked=True, color=colors, bins=bins, rwidth=0.8, linewidth=1, label=labels)

    ax3.set_title('e-folding spatial scales', fontsize=10)
    ax3.set_xlabel('e-folding Scale (° longitude)', fontsize=8)

    ax3.yaxis.set_visible(False)
    ax3.set_ylim(0, 7)
    
    # custom legend 생성 (ax1)
    legend_handles_ax3 = []
    
    for i, label in enumerate(labels):
        legend_handles_ax3.append(mpatches.Patch(facecolor=colors[i], edgecolor=colors[i], 
                                             label=label, linewidth=1))
    
    ax3.legend(handles=legend_handles_ax3, fontsize=6, loc='upper right')
    ax3.xaxis.set_tick_params(labelsize=8)



    # (B4) Auto-correlation of Gulf Stream path (ACF)
    ax4 = plt.subplot(gs_hist[1, 1])

    ax4.plot(np.arange(len(ds_obs['acf_spatial'][0])), np.mean(ds_obs['acf_spatial'], axis=0), color=colors[0], label=labels[0])
    
    for i, model in enumerate(MODEL_NAME):
        ax4.plot(np.arange(len(ds_low['acf_spatial'].isel(ensemble=i))), ds_low['acf_spatial'].isel(ensemble=i).values, color=colors[i+1],
                 label=labels[i+1], linestyle=':')
        ax4.plot(np.arange(len(ds_hi['acf_spatial'].isel(ensemble=i))), ds_hi['acf_spatial'].isel(ensemble=i).values, color=colors[i+n_ens_low+1],
                 label=labels[i+n_ens_low+1])
    
    ax4.set_title('Auto-correlation of '+current_name(save_name)+' path', fontsize=10)
    ax4.set_xlabel('Lag (Months)', fontsize=8)
    ax4.set_ylabel('ACF', fontsize=8)
    ax4.legend(loc='upper right', fontsize=5)
    ax4.yaxis.set_tick_params(labelsize=5)
    ax4.xaxis.set_tick_params(labelsize=5)

    plt.subplots_adjust(left=0.00, right=0.95, top=0.95, bottom=0.05)
    if save_path and save_name:
        region_str = save_name if isinstance(save_name, str) else str(save_name)
        plt.savefig(save_path + 'EOF_path_variability.' + region_str + '.png', dpi=900)
    #plt.show()
    plt.close(fig)

