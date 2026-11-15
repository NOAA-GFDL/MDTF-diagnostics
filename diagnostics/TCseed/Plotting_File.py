import numpy as np
import matplotlib.pyplot as plt

TITLES = ['6-9 m/s', '9-12 m/s', '12-15 m/s']
ROW_NAMES = ['Developing', 'Non-Developing', 'Dev \u2212 Non-Dev']


def _add_labels(fig, axes, cbar_1, cbar_2, cbar_3, suptitle):
    """Shared colorbars, seed-relative axis labels, row names and suptitle."""
    cbar1 = fig.colorbar(cbar_1, ax=axes[0, :], fraction=0.05, pad=0.05, orientation='vertical')
    cbar1.set_label('mm/hr', fontsize=12, fontweight='bold')
    cbar2 = fig.colorbar(cbar_2, ax=axes[1, :], fraction=0.05, pad=0.05, orientation='vertical')
    cbar2.set_label('mm/hr', fontsize=12, fontweight='bold')
    cbar3 = fig.colorbar(cbar_3, ax=axes[2, :], fraction=0.05, pad=0.05, orientation='vertical')
    cbar3.set_label('mm/hr', fontsize=12, fontweight='bold')

    # Left column: row name + latitude label
    for r in range(3):
        axes[r, 0].set_ylabel(f"{ROW_NAMES[r]}\nSeed-Relative Latitude (\u00b0)",
                              fontsize=12, fontweight='bold')

    # Center the title and the shared longitude label over the panels
    left = axes[0, 0].get_position().x0
    right = axes[0, -1].get_position().x1
    x_center = (left + right) / 2
    top = axes[0, 0].get_position().y1
    bottom = axes[-1, 0].get_position().y0

    #Longitude label under the bottom row
    fig.text(x_center, bottom - 0.045, 'Seed-Relative Longitude (\u00b0)',
             ha='center', va='top', fontsize=12, fontweight='bold')

    fig.suptitle(suptitle, x=x_center, y=top + 0.06, ha='center',
                 fontsize=16, fontweight='bold')


def Spatial_Map_Obs(Dev_Means, Non_Dev_Means, Percentile, suptitle='ERA5'):
    """3x3 panel plot for the observations (ERA5)"""
    fig, axes = plt.subplots(3, 3, figsize=(10, 10))
    tick_locations = [0, 10, 20, 30, 40]

    # Row 0: Developing
    for i, (data_1, title) in enumerate(zip(Dev_Means, TITLES)):
        ax = axes[0, i]
        cbar_1 = ax.imshow(data_1, cmap='jet', vmin=0, vmax=3)
        ax.contour(data_1, levels=[Percentile], colors='black', linewidths=2)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticklabels([])
        if i == 0:
            ax.set_yticks(tick_locations)
            ax.set_yticklabels(['5', '2.5', '0', '-2.5', '-5'], fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    # Row 1: Non-Developing
    for i, data_2 in enumerate(Non_Dev_Means):
        ax = axes[1, i]
        cbar_2 = ax.imshow(data_2, cmap='jet', vmin=0, vmax=3)
        ax.contour(data_2, levels=[Percentile], colors='black', linewidths=2)
        ax.set_xticklabels([])
        if i == 0:
            ax.set_yticks(tick_locations)
            ax.set_yticklabels(['5', '2.5', '0', '-2.5', '-5'], fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    # Row 2: Dev - Non-Dev
    differences = [Dev_Means[k] - Non_Dev_Means[k] for k in range(3)]
    for i, data_3 in enumerate(differences):
        ax = axes[2, i]
        cbar_3 = ax.imshow(data_3, cmap='seismic', vmin=-1, vmax=1)
        ax.set_xticks(tick_locations)
        ax.set_xticklabels(['-5', '-2.5', '0', '2.5', '5'], fontsize=12, fontweight='bold')
        if i == 0:
            ax.set_yticks(tick_locations)
            ax.set_yticklabels(['5', '2.5', '0', '-2.5', '-5'], fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    _add_labels(fig, axes, cbar_1, cbar_2, cbar_3, suptitle)
    return fig, axes


def Spatial_Map_Model(Dev_Means, Non_Dev_Means, Percentile, dlon=1.25, dlat=0.9424,
                      suptitle='Model'):
    """3x3 panel plot for the model output"""
    # Axes in degrees relative to storm center 
    n_lon, n_lat = Dev_Means[0].shape
    lon_half, lat_half = n_lon * dlon / 2, n_lat * dlat / 2
    extent = [-lon_half, lon_half, -lat_half, lat_half]

    lon_ticks = [-5, -2.5, 0, 2.5, 5]
    lon_labels = ['-5', '-2.5', '0', '2.5', '5']
    lat_ticks = [-5 * dlat, 0, 5 * dlat]
    lat_labels = [f'{t:.1f}' for t in lat_ticks]

    fig, axes = plt.subplots(3, 3, figsize=(10, 10))

    # Row 0: Developing
    for i, (data_1, title) in enumerate(zip(Dev_Means, TITLES)):
        ax = axes[0, i]
        cbar_1 = ax.imshow(data_1.T, cmap='jet', vmin=0, vmax=3, origin='lower', extent=extent)
        ax.contour(data_1.T, levels=[Percentile], colors='black', linewidths=2,
                   origin='lower', extent=extent)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(lon_ticks)
        ax.set_xticklabels([])
        ax.set_yticks(lat_ticks)
        if i == 0:
            ax.set_yticklabels(lat_labels, fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    # Row 1: Non-Developing
    for i, data_2 in enumerate(Non_Dev_Means):
        ax = axes[1, i]
        cbar_2 = ax.imshow(data_2.T, cmap='jet', vmin=0, vmax=3, origin='lower', extent=extent)
        ax.contour(data_2.T, levels=[Percentile], colors='black', linewidths=2,
                   origin='lower', extent=extent)
        ax.set_xticks(lon_ticks)
        ax.set_xticklabels([])
        ax.set_yticks(lat_ticks)
        if i == 0:
            ax.set_yticklabels(lat_labels, fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    # Row 2: Dev - Non-Dev
    differences = [Dev_Means[k] - Non_Dev_Means[k] for k in range(3)]
    for i, data_3 in enumerate(differences):
        ax = axes[2, i]
        cbar_3 = ax.imshow(data_3.T, cmap='seismic', vmin=-1, vmax=1, origin='lower', extent=extent)
        ax.set_xticks(lon_ticks)
        ax.set_xticklabels(lon_labels, fontsize=12, fontweight='bold')
        ax.set_yticks(lat_ticks)
        if i == 0:
            ax.set_yticklabels(lat_labels, fontsize=12, fontweight='bold')
        else:
            ax.set_yticklabels([])

    _add_labels(fig, axes, cbar_1, cbar_2, cbar_3, suptitle)
    return fig, axes