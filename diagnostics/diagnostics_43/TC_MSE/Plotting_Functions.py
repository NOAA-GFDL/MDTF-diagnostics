# Import modules
import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from scipy import interpolate

# Input of the specific model's lat/lon resolution or grid spacing (degrees) and name of model being run
modelname = str(os.getenv("modelname"))
latres = float(os.getenv("latres"))
lonres = float(os.getenv("lonres"))

# ############## PLOTTING OF MODEL AND REANALYSIS COMPOSITES TOGETHER #################

# open up the files that have gone through the binning and compositing step
Model_mean_binned_data = xr.open_dataset(os.environ['WORK_DIR'] + '/model/Model_Binned_Composites.nc')
Model_std_binned_data = xr.open_dataset(os.environ['WORK_DIR'] + '/model/Model_Binned_STDEVS_of_BoxAvgs.nc')
ERAINT_mean_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/ERAINT_Binned_Composites_with_normFeedbacks.nc')
ERAINT_std_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/ERAINT_Binned_STDEVS_of_BoxAvgs.nc')
ERA5_mean_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/ERA5_Binned_Composites_with_normFeedbacks.nc')
ERA5_std_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/ERA5_Binned_STDEVS_of_BoxAvgs.nc')
MERRA2_mean_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/MERRA2_Binned_Composites_with_normFeedbacks.nc')
MERRA2_std_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/MERRA2_Binned_STDEVS_of_BoxAvgs.nc')
CFSR_mean_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/CFSR_Binned_Composites_with_normFeedbacks.nc')
CFSR_std_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/CFSR_Binned_STDEVS_of_BoxAvgs.nc')
JRA55_mean_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/JRA55_Binned_Composites_with_normFeedbacks.nc')
JRA55_std_binned_data = xr.open_dataset(os.environ['OBS_DATA'] + '/JRA55_Binned_STDEVS_of_BoxAvgs.nc')


# SPATIAL COMPOSITE PLOTTING ################################################################


def SpatialCompositePanels():
    # Need to loop through the different bins to generate all the plots
    allbins = [16.5, 19.5, 22.5, 25.5, 28.5]
    # Bin we want to look at and setting for main title/save name of plots
    for b in allbins:
        bup = str(int(b + 1.5))
        blow = str(int(b - 1.5))
        # Now plot the composite boxes as a grid where the rows are the model/reanalyses, columns as feedback variables
        plt.rcParams["font.weight"] = "bold"
        plt.rcParams["axes.labelweight"] = "bold"
        fig, axs = plt.subplots(6, 4, figsize=(23, 28), sharex='row', sharey='row')
        for col in range(4):
            for row in range(6):
                ax = axs[row, col]
                if row == 0:
                    if col == 0:
                        im0 = ax.imshow(Model_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(Model_mean_binned_data.lon), max(Model_mean_binned_data.lon),
                                                min(Model_mean_binned_data.lat), max(Model_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel(modelname, fontsize=15)
                        ax.set_title("h' [$J/m^2$]", fontweight='bold', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(Model_mean_binned_data.hanom_SEFanom.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(Model_mean_binned_data.lon),
                                                            max(Model_mean_binned_data.lon),
                                                            min(Model_mean_binned_data.lat),
                                                            max(Model_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_title("h'SEF' [$J^2/m^4s$]", fontweight='bold', fontsize=15)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 2:
                        im1 = ax.imshow(Model_mean_binned_data.hanom_LWanom.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(Model_mean_binned_data.lon),
                                                            max(Model_mean_binned_data.lon),
                                                            min(Model_mean_binned_data.lat),
                                                            max(Model_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_title("h'LW' [$J^2/m^4s$]", fontweight='bold', fontsize=15)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(Model_mean_binned_data.hanom_SWanom.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(Model_mean_binned_data.lon),
                                                            max(Model_mean_binned_data.lon),
                                                            min(Model_mean_binned_data.lat),
                                                            max(Model_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_title("h'SW' [$J^2/m^4s$]", fontweight='bold', fontsize=15)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                elif row == 1:
                    if col == 0:
                        im0 = ax.imshow(JRA55_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(JRA55_mean_binned_data.lon),
                                                max(JRA55_mean_binned_data.lon),
                                                min(JRA55_mean_binned_data.lat),
                                                max(JRA55_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel('JRA-55', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(JRA55_mean_binned_data.hSEF_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(JRA55_mean_binned_data.lon),
                                                            max(JRA55_mean_binned_data.lon),
                                                            min(JRA55_mean_binned_data.lat),
                                                            max(JRA55_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 2:
                        im1 = ax.imshow(JRA55_mean_binned_data.hLW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(JRA55_mean_binned_data.lon),
                                                            max(JRA55_mean_binned_data.lon),
                                                            min(JRA55_mean_binned_data.lat),
                                                            max(JRA55_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(JRA55_mean_binned_data.hSW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(JRA55_mean_binned_data.lon),
                                                            max(JRA55_mean_binned_data.lon),
                                                            min(JRA55_mean_binned_data.lat),
                                                            max(JRA55_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                elif row == 2:
                    if col == 0:
                        im0 = ax.imshow(MERRA2_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(MERRA2_mean_binned_data.lon),
                                                max(MERRA2_mean_binned_data.lon),
                                                min(MERRA2_mean_binned_data.lat),
                                                max(MERRA2_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel('MERRA-2', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(MERRA2_mean_binned_data.hSEF_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(MERRA2_mean_binned_data.lon),
                                                            max(MERRA2_mean_binned_data.lon),
                                                            min(MERRA2_mean_binned_data.lat),
                                                            max(MERRA2_mean_binned_data.lat)],

                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 2:
                        im1 = ax.imshow(MERRA2_mean_binned_data.hLW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(MERRA2_mean_binned_data.lon),
                                                            max(MERRA2_mean_binned_data.lon),
                                                            min(MERRA2_mean_binned_data.lat),
                                                            max(MERRA2_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(MERRA2_mean_binned_data.hSW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr', extent=[min(MERRA2_mean_binned_data.lon),
                                                            max(MERRA2_mean_binned_data.lon),
                                                            min(MERRA2_mean_binned_data.lat),
                                                            max(MERRA2_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                elif row == 3:
                    if col == 0:
                        im0 = ax.imshow(CFSR_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(CFSR_mean_binned_data.lon), max(CFSR_mean_binned_data.lon),
                                                min(CFSR_mean_binned_data.lat), max(CFSR_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel('CFSR', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(CFSR_mean_binned_data.hSEF_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(CFSR_mean_binned_data.lon), max(CFSR_mean_binned_data.lon),
                                                min(CFSR_mean_binned_data.lat), max(CFSR_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 2:
                        im1 = ax.imshow(CFSR_mean_binned_data.hLW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(CFSR_mean_binned_data.lon), max(CFSR_mean_binned_data.lon),
                                                min(CFSR_mean_binned_data.lat), max(CFSR_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(CFSR_mean_binned_data.hSW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(CFSR_mean_binned_data.lon), max(CFSR_mean_binned_data.lon),
                                                min(CFSR_mean_binned_data.lat), max(CFSR_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                elif row == 4:
                    if col == 0:
                        im0 = ax.imshow(ERAINT_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(ERAINT_mean_binned_data.lon), max(ERAINT_mean_binned_data.lon),
                                                min(ERAINT_mean_binned_data.lat), max(ERAINT_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel('ERA-Int', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(ERAINT_mean_binned_data.hSEF_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr',
                                        extent=[min(ERAINT_mean_binned_data.lon), max(ERAINT_mean_binned_data.lon),
                                                min(ERAINT_mean_binned_data.lat), max(ERAINT_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 2:
                        im1 = ax.imshow(ERAINT_mean_binned_data.hLW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr',
                                        extent=[min(ERAINT_mean_binned_data.lon), max(ERAINT_mean_binned_data.lon),
                                                min(ERAINT_mean_binned_data.lat), max(ERAINT_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(ERAINT_mean_binned_data.hSW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9,
                                        cmap='bwr',
                                        extent=[min(ERAINT_mean_binned_data.lon), max(ERAINT_mean_binned_data.lon),
                                                min(ERAINT_mean_binned_data.lat), max(ERAINT_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                elif row == 5:
                    if col == 0:
                        im0 = ax.imshow(ERA5_mean_binned_data.hanom.sel(bin=b), cmap='bwr', vmin=-5e+7, vmax=5e+7,
                                        extent=[min(ERA5_mean_binned_data.lon), max(ERA5_mean_binned_data.lon),
                                                min(ERA5_mean_binned_data.lat), max(ERA5_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        ax.set_ylabel('ERA-5', fontsize=15)
                        ax.set_xticks(np.arange(-4.5, 6, 1.5))
                        ax.set_yticks(np.arange(-4.5, 6, 1.5))
                        cbar = fig.colorbar(im0, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif col == 1:
                        im1 = ax.imshow(ERA5_mean_binned_data.hSEF_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(ERA5_mean_binned_data.lon), max(ERA5_mean_binned_data.lon),
                                                min(ERA5_mean_binned_data.lat), max(ERA5_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    elif (col == 2):
                        im1 = ax.imshow(ERA5_mean_binned_data.hLW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(ERA5_mean_binned_data.lon), max(ERA5_mean_binned_data.lon),
                                                min(ERA5_mean_binned_data.lat), max(ERA5_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)
                    else:
                        im1 = ax.imshow(ERA5_mean_binned_data.hSW_concat.sel(bin=b), vmin=-2e+9, vmax=2e+9, cmap='bwr',
                                        extent=[min(ERA5_mean_binned_data.lon), max(ERA5_mean_binned_data.lon),
                                                min(ERA5_mean_binned_data.lat), max(ERA5_mean_binned_data.lat)],
                                        origin='lower')
                        ax.autoscale(False)
                        cbar = fig.colorbar(im1, ax=ax)
                        cbar.ax.tick_params(labelsize=15)
                        cbar.ax.yaxis.get_offset_text().set_fontsize(15)
                        ax.tick_params(labelsize=12)

        # Final plot adjustments
        plt.suptitle(blow + '-' + bup + ' m/s Bin Composites', fontweight='bold', fontsize=40)
        plt.savefig(os.environ['WORK_DIR'] + '/Panel_Composites_' + blow + '_' + bup + '_Bin.pdf')
        plt.close()


# ########################################## AZIMUTHAL MEAN FUNCTION #####################
def azmean(xord, yord, data, xcen, ycen, r):
    nr = r.shape[1]  # Size of radius array. Right now it's 2D so I am selecting the correct dimension
    nslice = 1000  # Number of theta slices

    # pre allocate the data
    datai = np.empty((nslice, nr))  # Create empty array for the second function

    # 360 degrees around the circle 
    dtheta = 360 / nslice
    theta = np.atleast_2d(np.linspace(0, 360 - dtheta, num=nslice))  # Array from 0 to 360 with dtheta steps
    # The atleast_2d creates a 2D, with 1,1000 dimension. I am doing that to do the dot product
    # and broadcast the operation.

    # interp2 outputs another function F where you can call xcircle and ycircle
    F = interpolate.interp2d(xord, yord, data)  # Use the function to interpolate the data

    # Because I have the 2D arrays, and they have one dimension in common (1), I can do
    # the "dot" product. The important thing is to get the right order and transpose order
    # it took me a couple of tries.
    xcircle = xcen + (np.cos(np.deg2rad(theta.transpose())) * r)  # xcenter is 0
    ycircle = ycen + (np.sin(np.deg2rad(theta.transpose())) * r)  # ycenter is 0

    # When you pass the whole F(xcircle[:,ix],ycircle[:,ix])
    # you get a 1000x1000 array, and diagonal or firstrow or firstcolumn won't work. so need to loop
    for ix in range(0, nr):
        for i_nslice in range(0, nslice):
            datai[i_nslice, ix] = F(xcircle[i_nslice, ix], ycircle[i_nslice, ix])

    # take azimuthal mean
    azmean = np.nanmean(datai, axis=0)

    return azmean


# ########################################## AZIMUTHAL MEAN PLOTTING ######################################
def AzmeanPlotting():
    # Create azimuthal mean of bin mean profile, first create an array of radii
    # (Use corresponding res. when setting up r's)
    # Use the model's lowest resolution for the radius for azmean calculations
    minres = min(latres, lonres)
    Modelr = np.arange(0, 5 + minres, minres)
    CFSRr = np.arange(0, 5.5, 0.5)
    JRA55r = np.arange(0, 5.56162167, 0.56162167)
    MERRA2r = np.arange(0, 5.5, 0.5)
    ERAINTr = np.arange(0, 5.612136, 0.701517)
    ERA5r = np.arange(0, 5.25, 0.25)

    # Get the r array 2D for use in azmean function
    Modelrr = np.atleast_2d(np.arange(0, 5 + minres, minres))
    CFSRrr = np.atleast_2d(np.arange(0, 5.5, 0.5))
    JRA55rr = np.atleast_2d(np.arange(0, 5.56162167, 0.56162167))
    MERRA2rr = np.atleast_2d(np.arange(0, 5.5, 0.5))
    ERAINTrr = np.atleast_2d(np.arange(0, 5.612136, 0.701517))
    ERA5rr = np.atleast_2d(np.arange(0, 5.25, 0.25))

    # Use each dataset's lats,lons
    # Model
    Modellons = Model_mean_binned_data.lon
    Modellats = Model_mean_binned_data.lat
    # CFSR
    CFSRlons = CFSR_mean_binned_data.lon
    CFSRlats = CFSR_mean_binned_data.lat
    # JRA55
    JRA55lons = JRA55_mean_binned_data.lon
    JRA55lats = JRA55_mean_binned_data.lat
    # ERAINT
    ERAINTlons = ERAINT_mean_binned_data.lon
    ERAINTlats = ERAINT_mean_binned_data.lat
    # ERA5
    ERA5lons = ERA5_mean_binned_data.lon
    ERA5lats = ERA5_mean_binned_data.lat
    # MERRA2
    MERRA2lons = MERRA2_mean_binned_data.lon
    MERRA2lats = MERRA2_mean_binned_data.lat

    # Need to loop through the different variables to generate all the plots
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig, axs = plt.subplots(ncols=3, figsize=(30, 10))
    for r in range(0, 3):
        ax = axs[r]
        if r == 0:
            Reanalysis_var = 'hSEF_concat'
            model_var = 'hanom_SEFanom'
            title_var = "h'SEF'"
        elif r == 2:
            Reanalysis_var = 'hSW_concat'
            model_var = 'hanom_SWanom'
            title_var = "h'SW'"
        elif r == 1:
            Reanalysis_var = 'hLW_concat'
            model_var = 'hanom_LWanom'
            title_var = "h'LW'"
        # Take the different bin azmeans
        # az0 is 15-18 m/s bin
        Model_azmean0 = azmean(Modellons, Modellats, Model_mean_binned_data[model_var].sel(bin=16.5), 0, 0,
                               Modelrr)
        CFSR_azmean0 = azmean(CFSRlons, CFSRlats, CFSR_mean_binned_data[Reanalysis_var].sel(bin=16.5), 0, 0,
                              CFSRrr)
        MERRA2_azmean0 = azmean(MERRA2lons, MERRA2lats, MERRA2_mean_binned_data[Reanalysis_var].sel(bin=16.5), 0,
                                0,
                                MERRA2rr)
        JRA55_azmean0 = azmean(JRA55lons, JRA55lats, JRA55_mean_binned_data[Reanalysis_var].sel(bin=16.5), 0,
                               0, JRA55rr)
        ERA5_azmean0 = azmean(ERA5lons, ERA5lats, ERA5_mean_binned_data[Reanalysis_var].sel(bin=16.5), 0, 0,
                              ERA5rr)
        ERAINT_azmean0 = azmean(ERAINTlons, ERAINTlats, ERAINT_mean_binned_data[Reanalysis_var].sel(bin=16.5), 0,
                                0, ERAINTrr)

        # az1 is 18-21 m/s bin
        Model_azmean1 = azmean(Modellons, Modellats, Model_mean_binned_data[model_var].sel(bin=19.5), 0, 0,
                               Modelrr)
        CFSR_azmean1 = azmean(CFSRlons, CFSRlats, CFSR_mean_binned_data[Reanalysis_var].sel(bin=19.5), 0, 0,
                              CFSRrr)
        MERRA2_azmean1 = azmean(MERRA2lons, MERRA2lats, MERRA2_mean_binned_data[Reanalysis_var].sel(bin=19.5), 0,
                                0,
                                MERRA2rr)
        JRA55_azmean1 = azmean(JRA55lons, JRA55lats, JRA55_mean_binned_data[Reanalysis_var].sel(bin=19.5), 0,
                               0,
                               JRA55rr)
        ERA5_azmean1 = azmean(ERA5lons, ERA5lats, ERA5_mean_binned_data[Reanalysis_var].sel(bin=19.5), 0, 0,
                              ERA5rr)
        ERAINT_azmean1 = azmean(ERAINTlons, ERAINTlats, ERAINT_mean_binned_data[Reanalysis_var].sel(bin=19.5), 0,
                                0,
                                ERAINTrr)

        # az2 is 21-24 m/s bin
        Model_azmean2 = azmean(Modellons, Modellats, Model_mean_binned_data[model_var].sel(bin=22.5), 0, 0,
                               Modelrr)
        CFSR_azmean2 = azmean(CFSRlons, CFSRlats, CFSR_mean_binned_data[Reanalysis_var].sel(bin=22.5), 0, 0,
                              CFSRrr)
        MERRA2_azmean2 = azmean(MERRA2lons, MERRA2lats, MERRA2_mean_binned_data[Reanalysis_var].sel(bin=22.5), 0,
                                0,
                                MERRA2rr)
        JRA55_azmean2 = azmean(JRA55lons, JRA55lats, JRA55_mean_binned_data[Reanalysis_var].sel(bin=22.5), 0,
                               0,
                               JRA55rr)
        ERA5_azmean2 = azmean(ERA5lons, ERA5lats, ERA5_mean_binned_data[Reanalysis_var].sel(bin=22.5), 0, 0,
                              ERA5rr)
        ERAINT_azmean2 = azmean(ERAINTlons, ERAINTlats, ERAINT_mean_binned_data[Reanalysis_var].sel(bin=22.5), 0,
                                0,
                                ERAINTrr)

        # az3 is 24-27 m/s bin
        Model_azmean3 = azmean(Modellons, Modellats, Model_mean_binned_data[model_var].sel(bin=25.5), 0, 0,
                               Modelrr)
        CFSR_azmean3 = azmean(CFSRlons, CFSRlats, CFSR_mean_binned_data[Reanalysis_var].sel(bin=25.5), 0, 0,
                              CFSRrr)
        MERRA2_azmean3 = azmean(MERRA2lons, MERRA2lats, MERRA2_mean_binned_data[Reanalysis_var].sel(bin=25.5), 0,
                                0,
                                MERRA2rr)
        JRA55_azmean3 = azmean(JRA55lons, JRA55lats, JRA55_mean_binned_data[Reanalysis_var].sel(bin=25.5), 0,
                               0,
                               JRA55rr)
        ERA5_azmean3 = azmean(ERA5lons, ERA5lats, ERA5_mean_binned_data[Reanalysis_var].sel(bin=25.5), 0, 0,
                              ERA5rr)
        ERAINT_azmean3 = azmean(ERAINTlons, ERAINTlats, ERAINT_mean_binned_data[Reanalysis_var].sel(bin=25.5), 0,
                                0,
                                ERAINTrr)

        # az4 is 27-30 m/s bin
        Model_azmean4 = azmean(Modellons, Modellats, Model_mean_binned_data[model_var].sel(bin=28.5), 0, 0,
                               Modelrr)
        CFSR_azmean4 = azmean(CFSRlons, CFSRlats, CFSR_mean_binned_data[Reanalysis_var].sel(bin=28.5), 0, 0,
                              CFSRrr)
        MERRA2_azmean4 = azmean(MERRA2lons, MERRA2lats, MERRA2_mean_binned_data[Reanalysis_var].sel(bin=28.5), 0,
                                0,
                                MERRA2rr)
        JRA55_azmean4 = azmean(JRA55lons, JRA55lats, JRA55_mean_binned_data[Reanalysis_var].sel(bin=28.5), 0,
                               0,
                               JRA55rr)
        ERA5_azmean4 = azmean(ERA5lons, ERA5lats, ERA5_mean_binned_data[Reanalysis_var].sel(bin=28.5), 0, 0,
                              ERA5rr)
        ERAINT_azmean4 = azmean(ERAINTlons, ERAINTlats, ERAINT_mean_binned_data[Reanalysis_var].sel(bin=28.5), 0,
                                0,
                                ERAINTrr)

        # Plotting all the different bin azmeans and adjusting their linewidths by 0.6 each bin increase
        # Create variables to get the thickness legend
        line15_18, = ax.plot(CFSRr, CFSR_azmean0, color='black', linewidth=1)
        line18_21, = ax.plot(CFSRr, CFSR_azmean1, color='black', linewidth=1.6)
        line21_24, = ax.plot(CFSRr, CFSR_azmean2, color='black', linewidth=2.2)
        line24_27, = ax.plot(CFSRr, CFSR_azmean3, color='black', linewidth=2.8)
        line27_30, = ax.plot(CFSRr, CFSR_azmean4, color='black', linewidth=3.4)

        # az0
        ax.plot(CFSRr, CFSR_azmean0, color='black', label='CFSR', linewidth=1)
        ax.plot(ERAINTr, ERAINT_azmean0, color='dimgrey', label='ERA-Int', linewidth=1)
        ax.plot(ERA5r, ERA5_azmean0, color='grey', label='ERA-5', linewidth=1)
        ax.plot(JRA55r, JRA55_azmean0, color='darkgrey', label='JRA-55', linewidth=1)
        ax.plot(MERRA2r, MERRA2_azmean0, color='lightgrey', label='MERRA-2', linewidth=1)
        ax.plot(Modelr, Model_azmean0, color='red', label=modelname, linewidth=1)

        # az1
        ax.plot(CFSRr, CFSR_azmean1, color='black', linewidth=1.6)
        ax.plot(ERAINTr, ERAINT_azmean1, color='dimgrey', linewidth=1.6)
        ax.plot(ERA5r, ERA5_azmean1, color='grey', linewidth=1.6)
        ax.plot(JRA55r, JRA55_azmean1, color='darkgrey', linewidth=1.6)
        ax.plot(MERRA2r, MERRA2_azmean1, color='lightgrey', linewidth=1.6)
        ax.plot(Modelr, Model_azmean1, color='red', linewidth=1.6)

        # az2
        ax.plot(CFSRr, CFSR_azmean2, color='black', linewidth=2.2)
        ax.plot(ERAINTr, ERAINT_azmean2, color='dimgrey', linewidth=2.2)
        ax.plot(ERA5r, ERA5_azmean2, color='grey', linewidth=2.2)
        ax.plot(JRA55r, JRA55_azmean2, color='darkgrey', linewidth=2.2)
        ax.plot(MERRA2r, MERRA2_azmean2, color='lightgrey', linewidth=2.2)
        ax.plot(Modelr, Model_azmean2, color='red', linewidth=2.2)

        # az3
        ax.plot(CFSRr, CFSR_azmean3, color='black', linewidth=2.8)
        ax.plot(ERAINTr, ERAINT_azmean3, color='dimgrey', linewidth=2.8)
        ax.plot(ERA5r, ERA5_azmean3, color='grey', linewidth=2.8)
        ax.plot(JRA55r, JRA55_azmean3, color='darkgrey', linewidth=2.8)
        ax.plot(MERRA2r, MERRA2_azmean3, color='lightgrey', linewidth=2.8)
        ax.plot(Modelr, Model_azmean3, color='red', linewidth=2.8)

        # az4
        ax.plot(CFSRr, CFSR_azmean4, color='black', linewidth=3.4)
        ax.plot(ERAINTr, ERAINT_azmean4, color='dimgrey', linewidth=3.4)
        ax.plot(ERA5r, ERA5_azmean4, color='grey', linewidth=3.4)
        ax.plot(JRA55r, JRA55_azmean4, color='darkgrey', linewidth=3.4)
        ax.plot(MERRA2r, MERRA2_azmean4, color='lightgrey', linewidth=3.4)
        ax.plot(Modelr, Model_azmean4, color='red', linewidth=3.4)

        # Specific plot title
        ax.set_title(title_var, fontweight='bold', fontsize=20)
        ax.set_xlabel('Degrees from Center', fontweight='bold', fontsize=20)
        ax.set_ylabel('Feedback [$J/m^2$]', fontweight='bold', fontsize=20)
        legend1 = ax.legend(fontsize=15, loc='upper center')
        legend2 = ax.legend([line15_18, line18_21, line21_24, line24_27, line27_30],
                            ["15-18 m/s", "18-21 m/s", "21-24 m/s", "24-27 m/s", "27-30 m/s"], loc='upper right',
                            fontsize=15)
        ax.add_artist(legend1)
        ax.add_artist(legend2)
        ax.tick_params(labelsize=15)
        ax.yaxis.get_offset_text().set_fontsize(15)

    # Final plot adjustments
    plt.suptitle('Multi-Bin Azimuthal Mean of Feedback Terms', fontweight='bold', fontsize=30)
    plt.savefig(os.environ['WK_DIR'] + '/Multibin_Azmean_Plots.pdf')
    plt.close()


# ####################### BOX AVERAGE LINE PLOTTING (NON-NORMALIZED AND NORMALIZED) ############
def BoxAvLinePlotting():
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(22, 27))
    for c in range(0, 2):
        for r in range(0, 2):
            ax = axs[r, c]
            if r == 0 and c == 0:
                modelvar = 'new_boxav_hanom_SEFanom'
                reanalysisvar = 'new_boxav_hSEF_concat'
                titlevar = "h'SEF'"
                units = '[$J^2/m^4s$]'
            elif r == 0 and c == 1:
                modelvar = 'new_boxav_hanom_LWanom'
                reanalysisvar = 'new_boxav_hLW_concat'
                titlevar = "h'LW'"
                units = '[$J^2/m^4s$]'
            elif r == 1 and c == 0:
                modelvar = 'new_boxav_hanom_SWanom'
                reanalysisvar = 'new_boxav_hSW_concat'
                titlevar = "h'SW'"
                units = '[$J^2/m^4s$]'
            elif r == 1 and c == 1:
                modelvar = 'new_boxav_hvar'
                reanalysisvar = 'new_boxav_varh_concat'
                titlevar = "Variance of h"
                units = '[$J^2/m^4$]'
            else:
                continue

            Model_bins = []
            ERAINT_bins = []
            ERA5_bins = []
            CFSR_bins = []
            MERRA2_bins = []
            JRA55_bins = []

            Modelboxavgvars = []
            Modelstderrorbars = []
            ERAINTboxavgvars = []
            ERAINTstderrorbars = []
            ERA5boxavgvars = []
            ERA5stderrorbars = []
            CFSRboxavgvars = []
            CFSRstderrorbars = []
            JRA55boxavgvars = []
            JRA55stderrorbars = []
            MERRA2boxavgvars = []
            MERRA2stderrorbars = []

            for b in Model_mean_binned_data.bin[2:]:
                if (Model_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    Model_bins.append(b)
                    # Box avgs of variables
                    Modelboxavgvars.append((Model_mean_binned_data[modelvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    Modelstderrorbars.append((Model_std_binned_data[modelvar].sel(bin=b)) * 1.96 / (
                                (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))
                if (ERAINT_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    ERAINT_bins.append(b)
                    # Box avgs of variables
                    ERAINTboxavgvars.append((ERAINT_mean_binned_data[reanalysisvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    ERAINTstderrorbars.append((ERAINT_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                                (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))
                if (ERA5_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    ERA5_bins.append(b)
                    # Box avgs of variables
                    ERA5boxavgvars.append((ERA5_mean_binned_data[reanalysisvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    ERA5stderrorbars.append((ERA5_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                                (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))
                if (CFSR_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    CFSR_bins.append(b)
                    # Box avgs of variables
                    CFSRboxavgvars.append((CFSR_mean_binned_data[reanalysisvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    CFSRstderrorbars.append((CFSR_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                                (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))
                if (MERRA2_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    MERRA2_bins.append(b)
                    # Box avgs of variables
                    MERRA2boxavgvars.append((MERRA2_mean_binned_data[reanalysisvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    MERRA2stderrorbars.append((MERRA2_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                                (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))
                if (JRA55_mean_binned_data.bincounts.sel(bin=b) > 2):
                    # Append the bins that are >2
                    JRA55_bins.append(b)
                    # Box avgs of variables
                    JRA55boxavgvars.append((JRA55_mean_binned_data[reanalysisvar].sel(bin=b)))
                    # Gets the range of error bar for 5 to 95% confidence interval at each bin
                    JRA55stderrorbars.append((JRA55_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                                (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)))

            # CFSR
            ax.plot(CFSR_bins, CFSRboxavgvars, color='black', label='CFSR', linewidth=4)
            ax.errorbar(CFSR_bins, CFSRboxavgvars, yerr=CFSRstderrorbars, color='black', linewidth=4)
            # ERA-Int
            ax.plot(ERAINT_bins, ERAINTboxavgvars, color='dimgrey', label='ERA-Int', linewidth=4)
            ax.errorbar(ERAINT_bins, ERAINTboxavgvars, yerr=ERAINTstderrorbars, color='dimgrey', linewidth=4)
            # ERA-5
            ax.plot(ERA5_bins, ERA5boxavgvars, color='grey', label='ERA-5', linewidth=4)
            ax.errorbar(ERA5_bins, ERA5boxavgvars, yerr=ERA5stderrorbars, color='grey', linewidth=4)
            # JRA-55
            ax.plot(JRA55_bins, JRA55boxavgvars, color='darkgrey', label='JRA-55', linewidth=4)
            ax.errorbar(JRA55_bins, JRA55boxavgvars, yerr=JRA55stderrorbars, color='darkgrey', linewidth=4)
            # MERRA-2
            ax.plot(MERRA2_bins, MERRA2boxavgvars, color='lightgrey', label='MERRA-2', linewidth=4)
            ax.errorbar(MERRA2_bins, MERRA2boxavgvars, yerr=MERRA2stderrorbars, color='lightgrey', linewidth=4)
            # Model
            ax.plot(Model_bins, Modelboxavgvars, color='red', label=modelname, linewidth=4)
            ax.errorbar(Model_bins, Modelboxavgvars, yerr=Modelstderrorbars, color='red', linewidth=4)
            # Title and legend
            ax.legend(fontsize=15, loc='upper left')
            ax.set_title(titlevar, fontweight='bold', fontsize=25)
            ax.set_ylabel(units, fontweight='bold', fontsize=25)
            ax.set_xlabel('Mean Wind Speed [m/s]', fontweight='bold', fontsize=25)
            if (titlevar == "Variance of h"):
                ax.set_ylim(0, 1.5e+15)
            ax.tick_params(labelsize=25)
            ax.yaxis.get_offset_text().set_fontsize(25)

    # Final plot adjustments
    plt.suptitle('Box Average of Bin Composite for Feedback Terms', fontweight='bold', fontsize=40)
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    plt.savefig(os.environ['WK_DIR'] + '/Box_Average_Plots.pdf')
    plt.close()

    # Now do the normalized version
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig, axs = plt.subplots(ncols=3, figsize=(30, 10))
    for r in range(0, 3):
        ax = axs[r]
        if (r == 0):
            modelvar = 'new_boxav_norm_hanom_SEFanom'
            reanalysisvar = 'new_boxav_norm_hSEF_concat'
            titlevar = "h'SEF'"
        elif (r == 1):
            modelvar = 'new_boxav_norm_hanom_LWanom'
            reanalysisvar = 'new_boxav_norm_hLW_concat'
            titlevar = "h'LW'"
        elif (r == 2):
            modelvar = 'new_boxav_norm_hanom_SWanom'
            reanalysisvar = 'new_boxav_norm_hSW_concat'
            titlevar = "h'SW'"
        else:
            continue

        Model_bins = []
        ERAINT_bins = []
        ERA5_bins = []
        CFSR_bins = []
        MERRA2_bins = []
        JRA55_bins = []

        Modelboxavgnormvars = []
        Modelnormstderrorbars = []
        ERAINTboxavgnormvars = []
        ERAINTnormstderrorbars = []
        ERA5boxavgnormvars = []
        ERA5normstderrorbars = []
        CFSRboxavgnormvars = []
        CFSRnormstderrorbars = []
        JRA55boxavgnormvars = []
        JRA55normstderrorbars = []
        MERRA2boxavgnormvars = []
        MERRA2normstderrorbars = []

        for b in Model_mean_binned_data.bin[2:]:
            if (Model_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >2
                Model_bins.append(b)
                # Box avgs of variables
                Modelboxavgnormvars.append((Model_mean_binned_data[modelvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                Modelnormstderrorbars.append((Model_std_binned_data[modelvar].sel(bin=b)) * 1.96 / (
                            (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)
            if (ERAINT_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >2
                ERAINT_bins.append(b)
                # Box avgs of variables
                ERAINTboxavgnormvars.append((ERAINT_mean_binned_data[reanalysisvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                ERAINTnormstderrorbars.append((ERAINT_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                            (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)
            if (ERA5_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >2
                ERA5_bins.append(b)
                # Box avgs of variables
                ERA5boxavgnormvars.append((ERA5_mean_binned_data[reanalysisvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                ERA5normstderrorbars.append((ERA5_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                            (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)
            if (CFSR_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >2
                CFSR_bins.append(b)
                # Box avgs of variables
                CFSRboxavgnormvars.append((CFSR_mean_binned_data[reanalysisvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                CFSRnormstderrorbars.append((CFSR_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                            (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)
            if (MERRA2_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >2
                MERRA2_bins.append(b)
                # Box avgs of variables
                MERRA2boxavgnormvars.append((MERRA2_mean_binned_data[reanalysisvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                MERRA2normstderrorbars.append((MERRA2_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                            (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)
            if (JRA55_mean_binned_data.bincounts.sel(bin=b) > 2):
                # Append the bins that are >0
                JRA55_bins.append(b)
                # Box avgs of variables
                JRA55boxavgnormvars.append((JRA55_mean_binned_data[reanalysisvar].sel(bin=b)) * 86400)
                # Gets the range of error bar for 5 to 95% confidence interval at each bin
                JRA55normstderrorbars.append((JRA55_std_binned_data[reanalysisvar].sel(bin=b)) * 1.96 / (
                            (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400)

        # CFSR
        ax.plot(CFSR_bins, CFSRboxavgnormvars, color='black', label='CFSR', linewidth=4)
        ax.errorbar(CFSR_bins, CFSRboxavgnormvars, yerr=CFSRnormstderrorbars, color='black', linewidth=4)
        # ERA-Int
        ax.plot(ERAINT_bins, ERAINTboxavgnormvars, color='dimgrey', label='ERA-Int', linewidth=4)
        ax.errorbar(ERAINT_bins, ERAINTboxavgnormvars, yerr=ERAINTnormstderrorbars, color='dimgrey', linewidth=4)
        # ERA-5
        ax.plot(ERA5_bins, ERA5boxavgnormvars, color='grey', label='ERA-5', linewidth=4)
        ax.errorbar(ERA5_bins, ERA5boxavgnormvars, yerr=ERA5normstderrorbars, color='grey', linewidth=4)
        # JRA-55
        ax.plot(JRA55_bins, JRA55boxavgnormvars, color='darkgrey', label='JRA-55', linewidth=4)
        ax.errorbar(JRA55_bins, JRA55boxavgnormvars, yerr=JRA55normstderrorbars, color='darkgrey', linewidth=4)
        # MERRA-2
        ax.plot(MERRA2_bins, MERRA2boxavgnormvars, color='lightgrey', label='MERRA-2', linewidth=4)
        ax.errorbar(MERRA2_bins, MERRA2boxavgnormvars, yerr=MERRA2normstderrorbars, color='lightgrey', linewidth=4)
        # Model
        ax.plot(Model_bins, Modelboxavgnormvars, color='red', label=modelname, linewidth=4)
        ax.errorbar(Model_bins, Modelboxavgnormvars, yerr=Modelnormstderrorbars, color='red', linewidth=4)
        # Title and legend
        ax.legend(fontsize=15)
        ax.set_title(titlevar, fontweight='bold', fontsize=22)
        ax.set_ylabel('Growth Rate [$d^-1$]', fontweight='bold', fontsize=18)
        ax.set_xlabel('Mean Wind Speed [m/s]', fontweight='bold', fontsize=18)
        ax.tick_params(labelsize=18)
        ax.yaxis.get_offset_text().set_fontsize(18)

    # Final plot adjustments
    plt.suptitle('Normalized Box Average of Bin Composites for Feedback Terms', fontweight='bold', fontsize=40)
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    plt.savefig(os.environ['WK_DIR'] + '/Normalized_Box_Average_Plots.pdf')
    plt.close()


########################################### BOX AVERAGE SCATTERING WITH % INTENSIFYING STORMS ###################################################
def BoxAvScatter():
    # Marker size
    size = 150
    # Need to set the different bins to generate all the plots
    allbins = [16.5, 19.5, 22.5, 25.5]
    # Get the LMI of each storm for each dataset
    Model_LMIs = np.amax(Model_mean_binned_data.maxwind, axis=1)
    ERA5_LMIs = np.amax(ERA5_mean_binned_data.maxwind, axis=1)
    ERAINT_LMIs = np.amax(ERAINT_mean_binned_data.maxwind, axis=1)
    MERRA2_LMIs = np.amax(MERRA2_mean_binned_data.maxwind, axis=1)
    CFSR_LMIs = np.amax(CFSR_mean_binned_data.maxwind, axis=1)
    JRA55_LMIs = np.amax(JRA55_mean_binned_data.maxwind, axis=1)
    # Now set up the plotting settings
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    fig, axs = plt.subplots(4, 2, figsize=(33, 30))
    for row in range(4):
        b = allbins[row]
        # Get the vupper and vlower
        vupper = b + 1.5
        vlower = b - 1.5
        # Setting string bin range for main title/save name of plots
        bup = str(int(vupper))
        blow = str(int(vlower))
        # Get the % storms intensifying based on the bin range of the current row
        Model_percent = len(np.where(Model_LMIs > vupper)[0]) / len(np.where(Model_LMIs > vlower)[0]) * 100
        ERA5_percent = len(np.where(ERA5_LMIs > vupper)[0]) / len(np.where(ERA5_LMIs > vlower)[0]) * 100
        ERAINT_percent = len(np.where(ERAINT_LMIs > vupper)[0]) / len(np.where(ERAINT_LMIs > vlower)[0]) * 100
        JRA55_percent = len(np.where(JRA55_LMIs > vupper)[0]) / len(np.where(JRA55_LMIs > vlower)[0]) * 100
        CFSR_percent = len(np.where(CFSR_LMIs > vupper)[0]) / len(np.where(CFSR_LMIs > vlower)[0]) * 100
        MERRA2_percent = len(np.where(MERRA2_LMIs > vupper)[0]) / len(np.where(MERRA2_LMIs > vlower)[0]) * 100
        # Get the box average feedbacks associated with the current bin
        Model_SEF = Model_mean_binned_data['new_boxav_hanom_SEFanom'].sel(bin=b)
        Model_LW = Model_mean_binned_data['new_boxav_hanom_LWanom'].sel(bin=b)
        Model_SW = Model_mean_binned_data['new_boxav_hanom_SWanom'].sel(bin=b)

        ERA5_SEF = ERA5_mean_binned_data['new_boxav_hSEF_concat'].sel(bin=b)
        ERA5_LW = ERA5_mean_binned_data['new_boxav_hLW_concat'].sel(bin=b)
        ERA5_SW = ERA5_mean_binned_data['new_boxav_hSW_concat'].sel(bin=b)

        ERAINT_SEF = ERAINT_mean_binned_data['new_boxav_hSEF_concat'].sel(bin=b)
        ERAINT_LW = ERAINT_mean_binned_data['new_boxav_hLW_concat'].sel(bin=b)
        ERAINT_SW = ERAINT_mean_binned_data['new_boxav_hSW_concat'].sel(bin=b)

        JRA55_SEF = JRA55_mean_binned_data['new_boxav_hSEF_concat'].sel(bin=b)
        JRA55_LW = JRA55_mean_binned_data['new_boxav_hLW_concat'].sel(bin=b)
        JRA55_SW = JRA55_mean_binned_data['new_boxav_hSW_concat'].sel(bin=b)

        CFSR_SEF = CFSR_mean_binned_data['new_boxav_hSEF_concat'].sel(bin=b)
        CFSR_LW = CFSR_mean_binned_data['new_boxav_hLW_concat'].sel(bin=b)
        CFSR_SW = CFSR_mean_binned_data['new_boxav_hSW_concat'].sel(bin=b)

        MERRA2_SEF = MERRA2_mean_binned_data['new_boxav_hSEF_concat'].sel(bin=b)
        MERRA2_LW = MERRA2_mean_binned_data['new_boxav_hLW_concat'].sel(bin=b)
        MERRA2_SW = MERRA2_mean_binned_data['new_boxav_hSW_concat'].sel(bin=b)
        # Get the errorbars of each box average above
        Model_SEF_bars = Model_std_binned_data['new_boxav_hanom_SEFanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        Model_LW_bars = Model_std_binned_data['new_boxav_hanom_LWanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        Model_SW_bars = Model_std_binned_data['new_boxav_hanom_SWanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        ERA5_SEF_bars = ERA5_std_binned_data['new_boxav_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        ERA5_LW_bars = ERA5_std_binned_data['new_boxav_hLW_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        ERA5_SW_bars = ERA5_std_binned_data['new_boxav_hSW_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        ERAINT_SEF_bars = ERAINT_std_binned_data['new_boxav_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        ERAINT_LW_bars = ERAINT_std_binned_data['new_boxav_hLW_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        ERAINT_SW_bars = ERAINT_std_binned_data['new_boxav_hSW_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        JRA55_SEF_bars = JRA55_std_binned_data['new_boxav_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        JRA55_LW_bars = JRA55_std_binned_data['new_boxav_hLW_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        JRA55_SW_bars = JRA55_std_binned_data['new_boxav_hSW_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        CFSR_SEF_bars = CFSR_std_binned_data['new_boxav_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        CFSR_LW_bars = CFSR_std_binned_data['new_boxav_hLW_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        CFSR_SW_bars = CFSR_std_binned_data['new_boxav_hSW_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        MERRA2_SEF_bars = MERRA2_std_binned_data['new_boxav_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        MERRA2_LW_bars = MERRA2_std_binned_data['new_boxav_hLW_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))
        MERRA2_SW_bars = MERRA2_std_binned_data['new_boxav_hSW_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2))

        # Get the normalized box average feedbacks associated with the current bin
        Model_normSEF = Model_mean_binned_data['new_boxav_norm_hanom_SEFanom'].sel(bin=b) * 86400
        Model_normLW = Model_mean_binned_data['new_boxav_norm_hanom_LWanom'].sel(bin=b) * 86400
        Model_normSW = Model_mean_binned_data['new_boxav_norm_hanom_SWanom'].sel(bin=b) * 86400

        ERA5_normSEF = ERA5_mean_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 86400
        ERA5_normLW = ERA5_mean_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 86400
        ERA5_normSW = ERA5_mean_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 86400

        ERAINT_normSEF = ERAINT_mean_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 86400
        ERAINT_normLW = ERAINT_mean_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 86400
        ERAINT_normSW = ERAINT_mean_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 86400

        JRA55_normSEF = JRA55_mean_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 86400
        JRA55_normLW = JRA55_mean_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 86400
        JRA55_normSW = JRA55_mean_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 86400

        CFSR_normSEF = CFSR_mean_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 86400
        CFSR_normLW = CFSR_mean_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 86400
        CFSR_normSW = CFSR_mean_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 86400

        MERRA2_normSEF = MERRA2_mean_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 86400
        MERRA2_normLW = MERRA2_mean_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 86400
        MERRA2_normSW = MERRA2_mean_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 86400
        # Get the errorbars of each box average above
        Model_normSEF_bars = Model_std_binned_data['new_boxav_norm_hanom_SEFanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        Model_normLW_bars = Model_std_binned_data['new_boxav_norm_hanom_LWanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        Model_normSW_bars = Model_std_binned_data['new_boxav_norm_hanom_SWanom'].sel(bin=b) * 1.96 / (
                    (Model_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        ERA5_normSEF_bars = ERA5_std_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        ERA5_normLW_bars = ERA5_std_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        ERA5_normSW_bars = ERA5_std_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 1.96 / (
                    (ERA5_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        ERAINT_normSEF_bars = ERAINT_std_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        ERAINT_normLW_bars = ERAINT_std_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        ERAINT_normSW_bars = ERAINT_std_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 1.96 / (
                    (ERAINT_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        JRA55_normSEF_bars = JRA55_std_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        JRA55_normLW_bars = JRA55_std_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        JRA55_normSW_bars = JRA55_std_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 1.96 / (
                    (JRA55_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        CFSR_normSEF_bars = CFSR_std_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        CFSR_normLW_bars = CFSR_std_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        CFSR_normSW_bars = CFSR_std_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 1.96 / (
                    (CFSR_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        MERRA2_normSEF_bars = MERRA2_std_binned_data['new_boxav_norm_hSEF_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        MERRA2_normLW_bars = MERRA2_std_binned_data['new_boxav_norm_hLW_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400
        MERRA2_normSW_bars = MERRA2_std_binned_data['new_boxav_norm_hSW_concat'].sel(bin=b) * 1.96 / (
                    (MERRA2_mean_binned_data.bincounts.sel(bin=b)) ** (1 / 2)) * 86400

        for col in range(2):
            ax = axs[row, col]
            if col == 0:
                # Plot the scatter points of non-normalized box average feedbacks and their errorbars
                # Scatter for symbol legends
                SEFfeedbackleg = ax.scatter(CFSR_SEF, CFSR_percent, marker='*', color='black')
                LWfeedbackleg = ax.scatter(CFSR_LW, CFSR_percent, marker='o', facecolors='white', edgecolor='black')
                SWfeedbackleg = ax.scatter(CFSR_SW, CFSR_percent, marker='o', color='black')
                # CFSR Scattering
                ax.scatter(CFSR_SEF, CFSR_percent, marker='*', color='black', label='CFSR', s=size)
                ax.errorbar(CFSR_SEF, CFSR_percent, xerr=CFSR_SEF_bars, fmt='*', color='black')
                ax.errorbar(CFSR_LW, CFSR_percent, xerr=CFSR_LW_bars, fmt='-', color='black')
                ax.scatter(CFSR_LW, CFSR_percent, marker='o', facecolors='white', edgecolors='black', s=size)
                ax.scatter(CFSR_SW, CFSR_percent, marker='o', color='black', s=size)
                ax.errorbar(CFSR_SW, CFSR_percent, xerr=CFSR_SW_bars, fmt='o', color='black')
                # ERA-Int Scattering
                ax.scatter(ERAINT_SEF, ERAINT_percent, marker='*', color='dimgrey', label='ERA-Int', s=size)
                ax.errorbar(ERAINT_SEF, ERAINT_percent, xerr=ERAINT_SEF_bars, fmt='*', color='dimgrey')
                ax.errorbar(ERAINT_LW, ERAINT_percent, xerr=ERAINT_LW_bars, fmt='-', color='dimgrey')
                ax.scatter(ERAINT_LW, ERAINT_percent, marker='o', facecolors='white', edgecolors='dimgrey', s=size)
                ax.scatter(ERAINT_SW, ERAINT_percent, marker='o', color='dimgrey', s=size)
                ax.errorbar(ERAINT_SW, ERAINT_percent, xerr=ERAINT_SW_bars, fmt='o', color='dimgrey')
                # ERA-5 Scattering
                ax.scatter(ERA5_SEF, ERA5_percent, marker='*', color='grey', label='ERA-5', s=size)
                ax.errorbar(ERA5_SEF, ERA5_percent, xerr=ERA5_SEF_bars, fmt='*', color='grey')
                ax.errorbar(ERA5_LW, ERA5_percent, xerr=ERA5_LW_bars, fmt='-', color='grey')
                ax.scatter(ERA5_LW, ERA5_percent, marker='o', facecolors='white', edgecolors='grey', s=size)
                ax.scatter(ERA5_SW, ERA5_percent, marker='o', color='grey', s=size)
                ax.errorbar(ERA5_SW, ERA5_percent, xerr=ERA5_SW_bars, fmt='o', color='grey')
                # JRA-55 Scattering
                ax.scatter(JRA55_SEF, JRA55_percent, marker='*', color='darkgrey', label='JRA-55', s=size)
                ax.errorbar(JRA55_SEF, JRA55_percent, xerr=JRA55_SEF_bars, fmt='*', color='darkgrey')
                ax.errorbar(JRA55_LW, JRA55_percent, xerr=JRA55_LW_bars, fmt='-', color='darkgrey')
                ax.scatter(JRA55_LW, JRA55_percent, marker='o', facecolors='white', edgecolors='darkgrey', s=size)
                ax.scatter(JRA55_SW, JRA55_percent, marker='o', color='darkgrey', s=size)
                ax.errorbar(JRA55_SW, JRA55_percent, xerr=JRA55_SW_bars, fmt='o', color='darkgrey')
                # MERRA2 Scattering
                ax.scatter(MERRA2_SEF, MERRA2_percent, marker='*', color='lightgrey', label='MERRA-2', s=size)
                ax.errorbar(MERRA2_SEF, MERRA2_percent, xerr=MERRA2_SEF_bars, fmt='*', color='lightgrey')
                ax.errorbar(MERRA2_LW, MERRA2_percent, xerr=MERRA2_LW_bars, fmt='-', color='lightgrey')
                ax.scatter(MERRA2_LW, MERRA2_percent, marker='o', facecolors='white', edgecolors='lightgrey', s=size)
                ax.scatter(MERRA2_SW, MERRA2_percent, marker='o', color='lightgrey', s=size)
                ax.errorbar(MERRA2_SW, MERRA2_percent, xerr=MERRA2_SW_bars, fmt='o', color='lightgrey')
                # Model Scattering
                ax.scatter(Model_SEF, Model_percent, marker='*', color='red', label=modelname, s=size)
                ax.errorbar(Model_SEF, Model_percent, xerr=Model_SEF_bars, fmt='*', color='red')
                ax.errorbar(Model_LW, Model_percent, xerr=Model_LW_bars, fmt='-', color='red')
                ax.scatter(Model_LW, Model_percent, marker='o', facecolors='white', edgecolors='red', s=size)
                ax.scatter(Model_SW, Model_percent, marker='o', color='red', s=size)
                ax.errorbar(Model_SW, Model_percent, xerr=Model_SW_bars, fmt='o', color='red')
                # Plot Features
                ax.set_title('Box Average Feedbacks ' + blow + '-' + bup + ' m/s Bin', fontweight='bold', fontsize=20)
                ax.set_xlabel('[$J^2/m^4s$]', fontweight='bold', fontsize=20)
                ax.set_ylabel('Percent of Storms [%]', fontweight='bold', fontsize=20)
                leg1 = ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=16)
                leg2 = ax.legend([SEFfeedbackleg, LWfeedbackleg, SWfeedbackleg], ["h'SEF'", "h'LW'", "h'SW'"],
                                 loc='center left', bbox_to_anchor=(1, 0.4), fontsize=16)
                ax.add_artist(leg1)
                ax.add_artist(leg2)
                ax.tick_params(labelsize=20)
                ax.xaxis.get_offset_text().set_fontsize(20)

            elif col == 1:
                # Plot the scatter points of normalized box average feedbacks and their errorbars
                # Scatter for symbol legends
                SEFfeedbackleg = ax.scatter(CFSR_normSEF, CFSR_percent, marker='*', color='black')
                LWfeedbackleg = ax.scatter(CFSR_normLW, CFSR_percent, marker='o', facecolors='white', edgecolor='black')
                SWfeedbackleg = ax.scatter(CFSR_normSW, CFSR_percent, marker='o', color='black')
                # CFSR Scattering
                ax.scatter(CFSR_normSEF, CFSR_percent, marker='*', color='black', label='CFSR', s=size)
                ax.errorbar(CFSR_normSEF, CFSR_percent, xerr=CFSR_normSEF_bars, fmt='*', color='black')
                ax.errorbar(CFSR_normLW, CFSR_percent, xerr=CFSR_normLW_bars, fmt='-', color='black')
                ax.scatter(CFSR_normLW, CFSR_percent, marker='o', facecolors='white', edgecolors='black', s=size)
                ax.scatter(CFSR_normSW, CFSR_percent, marker='o', color='black', s=size)
                ax.errorbar(CFSR_normSW, CFSR_percent, xerr=CFSR_normSW_bars, fmt='o', color='black')
                # ERA-Int Scattering
                ax.scatter(ERAINT_normSEF, ERAINT_percent, marker='*', color='dimgrey', label='ERA-Int', s=size)
                ax.errorbar(ERAINT_normSEF, ERAINT_percent, xerr=ERAINT_normSEF_bars, fmt='*', color='dimgrey')
                ax.errorbar(ERAINT_normLW, ERAINT_percent, xerr=ERAINT_normLW_bars, fmt='-', color='dimgrey')
                ax.scatter(ERAINT_normLW, ERAINT_percent, marker='o', facecolors='white', edgecolors='dimgrey', s=size)
                ax.scatter(ERAINT_normSW, ERAINT_percent, marker='o', color='dimgrey', s=size)
                ax.errorbar(ERAINT_normSW, ERAINT_percent, xerr=ERAINT_normSW_bars, fmt='o', color='dimgrey')
                # ERA-5 Scattering
                ax.scatter(ERA5_normSEF, ERA5_percent, marker='*', color='grey', label='ERA-5', s=size)
                ax.errorbar(ERA5_normSEF, ERA5_percent, xerr=ERA5_normSEF_bars, fmt='*', color='grey')
                ax.errorbar(ERA5_normLW, ERA5_percent, xerr=ERA5_normLW_bars, fmt='-', color='grey')
                ax.scatter(ERA5_normLW, ERA5_percent, marker='o', facecolors='white', edgecolors='grey', s=size)
                ax.scatter(ERA5_normSW, ERA5_percent, marker='o', color='grey', s=size)
                ax.errorbar(ERA5_normSW, ERA5_percent, xerr=ERA5_normSW_bars, fmt='o', color='grey')
                # JRA-55 Scattering
                ax.scatter(JRA55_normSEF, JRA55_percent, marker='*', color='darkgrey', label='JRA-55', s=size)
                ax.errorbar(JRA55_normSEF, JRA55_percent, xerr=JRA55_normSEF_bars, fmt='*', color='darkgrey')
                ax.errorbar(JRA55_normLW, JRA55_percent, xerr=JRA55_normLW_bars, fmt='-', color='darkgrey')
                ax.scatter(JRA55_normLW, JRA55_percent, marker='o', facecolors='white', edgecolors='darkgrey', s=size)
                ax.scatter(JRA55_normSW, JRA55_percent, marker='o', color='darkgrey', s=size)
                ax.errorbar(JRA55_normSW, JRA55_percent, xerr=JRA55_normSW_bars, fmt='o', color='darkgrey')
                # MERRA2 Scattering
                ax.scatter(MERRA2_normSEF, MERRA2_percent, marker='*', color='lightgrey', label='MERRA-2', s=size)
                ax.errorbar(MERRA2_normSEF, MERRA2_percent, xerr=MERRA2_normSEF_bars, fmt='*', color='lightgrey')
                ax.errorbar(MERRA2_normLW, MERRA2_percent, xerr=MERRA2_normLW_bars, fmt='-', color='lightgrey')
                ax.scatter(MERRA2_normLW, MERRA2_percent, marker='o', facecolors='white', edgecolors='lightgrey',
                           s=size)
                ax.scatter(MERRA2_normSW, MERRA2_percent, marker='o', color='lightgrey', s=size)
                ax.errorbar(MERRA2_normSW, MERRA2_percent, xerr=MERRA2_normSW_bars, fmt='o', color='lightgrey')
                # Model Scattering
                ax.scatter(Model_normSEF, Model_percent, marker='*', color='red', label=modelname, s=size)
                ax.errorbar(Model_normSEF, Model_percent, xerr=Model_normSEF_bars, fmt='*', color='red')
                ax.errorbar(Model_normLW, Model_percent, xerr=Model_normLW_bars, fmt='-', color='red')
                ax.scatter(Model_normLW, Model_percent, marker='o', facecolors='white', edgecolors='red', s=size)
                ax.scatter(Model_normSW, Model_percent, marker='o', color='red', s=size)
                ax.errorbar(Model_normSW, Model_percent, xerr=Model_normSW_bars, fmt='o', color='red')
                # Plot Features
                ax.set_title('Normalized Box Average Feedbacks ' + blow + '-' + bup + ' m/s Bin', fontweight='bold',
                             fontsize=20)
                ax.set_xlabel('[$d^-1$]', fontweight='bold', fontsize=20)
                ax.set_ylabel('Percent of Storms [%]', fontweight='bold', fontsize=20)
                leg1 = ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=16)
                leg2 = ax.legend([SEFfeedbackleg, LWfeedbackleg, SWfeedbackleg], ["h'SEF'", "h'LW'", "h'SW'"],
                                 loc='center left', bbox_to_anchor=(1, 0.4), fontsize=16)
                ax.add_artist(leg1)
                ax.add_artist(leg2)
                ax.tick_params(labelsize=20)
                ax.xaxis.get_offset_text().set_fontsize(20)

    plt.suptitle('Scatter Plots of Percent of Storms Intensifying as Function of Box-Averaged Feedback',
                 fontweight='bold', fontsize=35)
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    plt.savefig(os.environ['WORK_DIR'] + '/Scattered_Feedbacks.pdf')
    plt.close()
