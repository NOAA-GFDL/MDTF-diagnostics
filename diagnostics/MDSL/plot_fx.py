import numpy as np
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def make_regional_plots(modname,reginfo, ds_grid, tchgrids, model_reg_col, cnes_reg_col, dtu_reg_col, errs, cost_funcs, num_points, cost_threshold, outputdir, 
                        tg_lats, tg_lons, tgs_dtu_errs, tgs_cnes_errs, err_acs, data_flats, ds_bathy=None):

    # Color mapping for the three different types of plots.
    cmap1 ='Spectral_r' # Raw difference plots.
    cmap2 ='cividis'    # TCH error plots.
    cmap3 = 'binary'    # Number of points per TCH plot.
    # Font parameters.
    fsize1 = 10
    fsize2 = 14
    fweight = 'bold'

    data_dict = {modname:model_reg_col, 'CNES':cnes_reg_col, 'DTU':dtu_reg_col}

    bathy = False
    if ds_bathy != None:
        bathy=True
        # Get bathymetry information to add contour.
        x = np.array(ds_bathy.lon.values)
        y = np.array(ds_bathy.lat.values)
        z = np.array(ds_bathy.depth.values)
        X, Y = np.meshgrid(x,y)
        bathy_color = 'magenta'
    

    # Create diagnostic plot for each region. 
    for nreg in np.arange(len(reginfo)):

        fig = plt.figure(figsize=(12,18))

        log_error = np.log2(errs[nreg]*100) # Error on log scale. 
        cost_fnc = cost_funcs[nreg]
        pltgrid = tchgrids[nreg]
        nmpnts = num_points[nreg]
        lons, lats = np.meshgrid(pltgrid.lon, pltgrid.lat)
        buffer = 5 # Buffer in degrees to put around edges of TCH region

        labels1 = ["d", "a"]  # Labels for subplots
        labels2 = ["f", "b"]  # Labels for subplots
        
        # Create diagnostic plot for each observational (non-model) dataset.
        for nsp in range(len(cost_fnc)):
            
            # Dataset to compare DTU to for first two columns.
            comp_data = ['CNES', modname][nsp]

            # First column: MDSL differences
            #########################################################

            # Setup
            cmin, cmax = -50, 50
            ax = plt.subplot2grid((3,3), (-nsp+1, 0), colspan=1, rowspan=1, projection=ccrs.PlateCarree(), aspect="auto")
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
            ax.set_extent([reginfo.iloc[nreg].west_bound-buffer, reginfo.iloc[nreg].east_bound+buffer,
                                    reginfo.iloc[nreg].south_bound-buffer, reginfo.iloc[nreg].north_bound+buffer], 
                                    crs=ccrs.PlateCarree())
            title = f'{comp_data}-DTU MDSL diff [cm]'
            ax.set_title(title, loc='center', fontsize=fsize1)
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
            gl.left_labels = True #False
            gl.bottom_labels = True
            
            # MDSL difference to plot.
            mdsl_diff = (data_dict[comp_data][nreg] - dtu_reg_col[nreg])*100
                
            # Plot regridded differences.
            diff_plot = plt.pcolormesh(ds_grid.longitude,
                         ds_grid.latitude, 
                         mdsl_diff,
                         vmin=cmin, 
                         vmax=cmax, 
                         cmap=cmap1,
                         zorder=1,
                         shading='nearest',  
                         transform=ccrs.PlateCarree())
            if bathy:
                # Add bathymetry contour at 100m (continental shelf)
                lab = ax.contour(X,Y, z, [-100], colors=[bathy_color], transform=ccrs.PlateCarree(), zorder=5, linestyles=['solid'], linewidths=[0.5])

            ax.text(
                0.02, 0.95, labels1[nsp], transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )
                #ax.clabel(lab)


            # # Add shared colorbars outside the grid
            # cbar_ax_left = fig.add_axes([0.0, 0.1, 0.3, 0.02])  # Below bottom-left map
            # cbar_left = fig.colorbar(diff_plot, cax=cbar_ax_left, orientation="horizontal", extend="both")
            # cbar_left.set_label("Difference")
            
            # cbar_ax_center = fig.add_axes([0.35, 0.1, 0.3, 0.02])  # Below bottom-center map
            # cbar_center = fig.colorbar(p_center, cax=cbar_ax_center, orientation="horizontal", extend="both")
            # cbar_center.set_label("NCH Error")
        
            # Second row, 2nd+3rd column: log scale errors with stippled cost function. 
            #########################################################

            # Setup.
            cmin, cmax = 0, np.nanmax(log_error[2,:,:])
            ax = plt.subplot2grid((3,3), (-nsp+1, 2-nsp), colspan=1, rowspan=1, projection=ccrs.PlateCarree(), aspect="auto")
            title = f'{comp_data} Error (log$_2$ scale) [cm]'#refname + ' ' + label + ' ' + units
            ax.set_title(title, loc='center', fontsize=fsize1)
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
            ax.set_extent([reginfo.iloc[nreg].west_bound-buffer, reginfo.iloc[nreg].east_bound+buffer,
                            reginfo.iloc[nreg].south_bound-buffer, reginfo.iloc[nreg].north_bound+buffer], 
                            crs=ccrs.PlateCarree())
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
            gl.left_labels = False #False
            gl.bottom_labels = True

            # log_error has had order [CNES, DTU, model, optional: TG]
            if comp_data == modname:
                index = 2
            else: 
                index = 0

            # Create plot of error with shared for each sublot.
            p_center = plt.pcolormesh(pltgrid.lon,
                             pltgrid.lat, 
                             log_error[index,:,:].T,
                             vmin=cmin, 
                             vmax=cmax, 
                             cmap=cmap2,
                             zorder=1,
                             transform=ccrs.PlateCarree())

            # Add stippling in locations where cost function is below cost threshold.
            siglat = lats[cost_fnc[nsp, :, :].T < cost_threshold]
            siglon = lons[cost_fnc[nsp, :, :].T < cost_threshold]
            ax.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())
            
            if bathy:
                # Add bathymetry contour at 100m (continental shelf)
                lab = ax.contour(X,Y, z, [-100], colors=[bathy_color], transform=ccrs.PlateCarree(), zorder=5, linestyles=['solid'], linewidths=[0.5])
                #ax.clabel(lab)
            ax.text(
                0.02, 0.95, labels2[nsp], transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )
    
            # 1st row, 2nd column: log scale model error with stippled cost function. 
            #########################################################

            # Setup.
            ax = plt.subplot2grid((3,3), (1, 1), colspan=1, rowspan=1, projection=ccrs.PlateCarree(), aspect="auto")
            title = 'DTU Error (log$_2$ scale) [cm]'
            ax.set_title(title,loc='center',fontsize=fsize1)
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)
            ax.set_extent([reginfo.iloc[nreg].west_bound-buffer, reginfo.iloc[nreg].east_bound+buffer,
                                reginfo.iloc[nreg].south_bound-buffer, reginfo.iloc[nreg].north_bound+buffer], 
                            crs=ccrs.PlateCarree())
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
            gl.left_labels = False
            gl.bottom_labels = True

            # Create meshgrid of model errors.
            # Use cmin, cmax to ensure this uses the same colorbar as other error plots.
            plt.pcolormesh(pltgrid.lon, pltgrid.lat, log_error[1,:,:].T,
                                vmin=cmin,
                                vmax=cmax, 
                                cmap=cmap2,
                                zorder=1,
                                transform=ccrs.PlateCarree())

            siglat = lats[cost_fnc[nsp, :, :].T < cost_threshold]
            siglon = lons[cost_fnc[nsp, :, :].T < cost_threshold]
            ax.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())
            
            if bathy:
                # Add bathymetry contour at 100m (continental shelf)
                lab = ax.contour(X,Y, z, [-100], colors=[bathy_color], transform=ccrs.PlateCarree(), zorder=5, linestyles=['solid'], linewidths=[0.5])
                #ax.clabel(lab)

            ax.text(
                0.02, 0.95, "e", transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )

            # 1st row, 3rd column: Number of points in each TCH box
            #########################################################

            # Setup.
            cmin, cmax = 0, np.nanmax(nmpnts)
            ax = plt.subplot2grid((3,3), (0, 2), colspan=1, rowspan=1, projection=ccrs.PlateCarree(), aspect="auto")
            title = 'Number of points in NCH box'
            ax.set_title(title,loc='center',fontsize=fsize1)
            ax.set_extent([reginfo.iloc[nreg].west_bound-buffer, reginfo.iloc[nreg].east_bound+buffer,
                                reginfo.iloc[nreg].south_bound-buffer, reginfo.iloc[nreg].north_bound+buffer], 
                            crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4) 
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
            gl.left_labels = False
            gl.bottom_labels = True

            # Plot number of points per TCH box, with its own colorbar.
            p_right = plt.pcolormesh(pltgrid.lon, pltgrid.lat, nmpnts.T,
                                vmin=cmin,
                                vmax=cmax, 
                                cmap=cmap3,
                                zorder=1,
                                transform=ccrs.PlateCarree())

            if bathy:
                # Add bathymetry contour at 100m (continental shelf)
                lab = ax.contour(X,Y, z, [-100], colors=[bathy_color], transform=ccrs.PlateCarree(), zorder=5, linestyles=['solid'], linewidths=[0.5])
                #ax.clabel(lab)
            ax.text(
                0.02, 0.95, "c", transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )

    
            #cbar_ax_right = fig.add_axes([0.7, 0.95, 0.3, 0.02])  # Below bottom-right map
            #cbar_right = fig.colorbar(p_right, cax=cbar_ax_right, orientation="horizontal", extend="both")
            #cbar_right.set_label("Points per box")
    
            # 3rd row, 1st column: location of "tgs"
            #########################################################

            # Setup.
            ax = plt.subplot2grid((3,3), (2, 0), colspan=1, rowspan=1, projection=ccrs.PlateCarree(), aspect="auto")
            title = 'Coastal locations'
            ax.set_title(title,loc='center',fontsize=fsize1)
            ax.set_extent([reginfo.iloc[nreg].west_bound-buffer, reginfo.iloc[nreg].east_bound+buffer,
                                reginfo.iloc[nreg].south_bound-buffer, reginfo.iloc[nreg].north_bound+buffer], 
                            crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=1)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=1) 
            ax.scatter(tg_lons[nreg],tg_lats[nreg],100, 'k','*',zorder=2, transform=ccrs.PlateCarree())
            # print(tg_lons[nreg],tg_lats[nreg])
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=3)
            gl.left_labels = True
            gl.bottom_labels = True

            ax.text(
                0.02, 0.95, "g", transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )

            ax = plt.subplot2grid((3,3), (2, 1), colspan=1, rowspan=1, aspect="auto")
        
            ax.scatter(data_flats[nreg][modname],tg_lats[nreg], 100, color='k', marker='*',label=modname)
            ax.errorbar(data_flats[nreg]['DTU'], tg_lats[nreg], yerr=None, xerr=tgs_dtu_errs[nreg],color='C0' ,linewidth=2,label='DTU', alpha=0.5)
            ax.errorbar(data_flats[nreg]['CNES'], tg_lats[nreg], yerr=None, xerr=tgs_cnes_errs[nreg],color='C1' ,linewidth=2,label='CNES', alpha=0.5)
            # ax.errorbar(data_flats[nreg]['CNES'], tg_lats[nreg]-data_flats[nreg]['CNES'], yerr=None, xerr=tgs_cnes_errs[nreg],color='C1' ,linewidth=2,label='CNES', alpha=0.5)
        
            # ax.set_ylabel(tg_lats[nreg])
            ax.set_xlabel('Coastal MDSL (m, relative to alongcoast mean)')
        
            ax.legend(loc="upper right")
            ax.grid()
        
            ax.set_title('Data errorbars')
            x_limits = ax.get_xlim()

            ax.text(
                0.02, 0.95, "h", transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )

            

            ax = plt.subplot2grid((3,3), (2, 2), colspan=1, rowspan=1, aspect="auto")
        
            ax.errorbar(data_flats[nreg][modname], tg_lats[nreg], yerr=None, xerr=err_acs[nreg][2],color='k' ,linewidth=2,label=modname, alpha=0.5)
            ax.errorbar(data_flats[nreg]['DTU'], tg_lats[nreg], yerr=None, xerr=err_acs[nreg][0],color='C0' ,linewidth=2,label='DTU', alpha=0.5)
            ax.errorbar(data_flats[nreg]['CNES'], tg_lats[nreg], yerr=None, xerr=err_acs[nreg][1],color='C1' ,linewidth=2,label='CNES', alpha=0.5)
            if len(data_flats[nreg])>3:
                ax.errorbar(data_flats[nreg]['TG'], tg_lats[nreg], yerr=None, xerr=err_acs[nreg][3],color='C2' ,linewidth=2,label='TG', alpha=0.5)

            # ax.errorbar(data_flats[nreg]['CNES'], tg_lats[nreg]-data_flats[nreg]['CNES'], yerr=None, xerr=ac_errs[['CNES'],color='C1' ,linewidth=2,label='CNES', alpha=0.5)
        
            # ax.set_ylabel(tg_lats[nreg])
            ax.set_xlabel('Coastal MDSL (m, relative to alongcoast mean)')
        
            ax.legend(loc="upper right")
            ax.grid()
        
            ax.set_title('NCH errorbars')
            x_limits = ax.get_xlim()

            ax.text(
                0.02, 0.95, "i", transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none'),
                zorder=10
            )
        # Parameters for full function. 
        ##############################################################
        # plt.tight_layout()


        


        #Newly Added sections
            cbar_ax_left = fig.add_axes([0.05, 0.12, 0.28, 0.02])  # Below bottom-left map
            cbar_left = fig.colorbar(diff_plot, cax=cbar_ax_left, orientation="horizontal",
                                     extend="both")
            cbar_left.set_label("Difference")
        
            cbar_ax_center = fig.add_axes([0.37, 0.12, 0.28, 0.02])  # Below bottom-center map
            cbar_center = fig.colorbar(p_center, cax=cbar_ax_center, orientation="horizontal",
                                       extend="both")
            cbar_center.set_label("NCH Error")
    
            cbar_ax_right = fig.add_axes([0.7, 0.12, 0.28, 0.02])  # Below bottom-right map
            cbar_right = fig.colorbar(p_right, cax=cbar_ax_right, orientation="horizontal",
                                      extend="both")
            cbar_right.set_label("Points per box")
        ################################################

        plt.tight_layout(rect=[0, 0.15, 1, 1])
    
        plt.savefig(outputdir+modname+reginfo.iloc[nreg].RegionName + '_regional_TCH.png')
        plt.close(fig)

def make_global_plots(data_dict, err, cost_func, destgrid, num_points, cost_threshold, modname, outputdir):

    # Mask out latitudes outside [-70, 70]
    #lat_mask = (pltgrid.lat >= -70) & (pltgrid.lat <= 70)

    # Apply mask: Set values outside the range to NaN
    #masked_log_error = np.where(lat_mask[:, None], log_error[1, :, :].T, np.nan)
    
    #  Color mapping for the three different types of plots.
    cmap1 ='Spectral_r' # Raw difference plots.
    cmap2 ='cividis'    # TCH error plots.
    cmap3 = 'binary'    # Number of points per TCH plot.
    # Font parameters.
    fsize1 = 10
    fsize2 = 14
    fweight = 'bold'

    fig = plt.figure(figsize=(14,8))
        
    log_error = np.log2(err*100) # Error on log scale. 
    cost_fnc = cost_func
    pltgrid = destgrid
    nmpnts = num_points
    lons, lats = np.meshgrid(pltgrid.lon, pltgrid.lat)

    labels1 = ["d", "a"]  # Labels for subplots
    labels2 = ["f", "b"]  # Labels for subplots
    # Create diagnostic plot for each observational (non-model) dataset.
    for nsp in range(len(cost_fnc)):
        # Dataset to compare DTU to for first two columns.
        comp_data = ['CNES', modname][nsp]

        # Setup
        cmin, cmax = -50, 50
        #ax = plt.subplot2grid((2,3), (-nsp+1, 0), colspan=1, rowspan=1, projection=ccrs.Robinson(central_longitude=180), aspect="auto")
        ax = plt.subplot2grid((2,3), (-nsp+1, 0), colspan=1, rowspan=1, projection=ccrs.PlateCarree(central_longitude=180), aspect="auto")
        ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
        ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
        title = f'{comp_data}-DTU MDSL diff [cm]'
        ax.set_title(title, loc='center', fontsize=fsize1)
        ax.set_extent([0, 360, -70, 70], crs=ccrs.PlateCarree())
        gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        gl.left_labels = True #False
        if nsp == 0:
            gl.bottom_labels = True
                
        # MDSL difference to plot.
        if comp_data==modname:
            mdsl_diff = (data_dict[comp_data] - data_dict['DTU'].mdt)*100
        else:
            mdsl_diff = (data_dict[comp_data].mdt - data_dict['DTU'].mdt)*100

        # Plot regridded differences.
        diff_plot = plt.pcolormesh(data_dict['DTU'].lon,
                            data_dict['DTU'].lat, 
                            mdsl_diff,
                            vmin=cmin, 
                            vmax=cmax, 
                            cmap=cmap1,
                            zorder=1,
                            shading='nearest',  
                            transform=ccrs.PlateCarree())
        ax.text(
                0.02, 0.95, labels1[nsp], transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'),
                zorder=10
            )

        # Second row, 2nd+3rd column: log scale errors with stippled cost function. 
        #########################################################

        # Setup.
        cmin, cmax = 0, np.nanmax(log_error[2,:,:])
        ax = plt.subplot2grid((2,3), (-nsp+1, 2-nsp), colspan=1, rowspan=1, projection=ccrs.PlateCarree(central_longitude=180), aspect="auto")
        title = f'{comp_data} Error (log$_2$ scale) [cm]'#refname + ' ' + label + ' ' + units
        ax.set_title(title, loc='center', fontsize=fsize1)
        ax.set_extent([0, 360, -70, 70], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
        ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
        gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        gl.left_labels = False
        if nsp == 0:
            gl.bottom_labels = True

        # log_error has had order [CNES, DTU, model, optional: TG]
        if comp_data == modname:
            index = 2
        else: 
            index = 0

        # Create plot of error with shared for each sublot.
        p_center = plt.pcolormesh(pltgrid.lon,
                    pltgrid.lat, 
                    log_error[index,:,:].T,
                    vmin=cmin, 
                    vmax=cmax, 
                    cmap=cmap2,
                    zorder=1,
                    transform=ccrs.PlateCarree())

        # Add stippling in locations where cost function is below cost threshold.
        siglat = lats[cost_fnc[nsp, :, :].T < cost_threshold]
        siglon = lons[cost_fnc[nsp, :, :].T < cost_threshold]
        ax.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())

        ax.text(
            0.02, 0.95, labels2[nsp], transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top', ha='left',
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'),
            zorder=10
        )

        # 1st row, 2nd column: log scale model error with stippled cost function. 
        #########################################################

        # Setup.
        ax = plt.subplot2grid((2,3), (1, 1), colspan=1, rowspan=1, projection=ccrs.PlateCarree(central_longitude=180), aspect="auto")
        title = 'DTU Error (log$_2$ scale) [cm]'
        ax.set_title(title,loc='center',fontsize=fsize1)
        ax.set_extent([0, 360, -70, 70], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
        ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)
        gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        gl.left_labels = False
        gl.bottom_labels = True

        # Create meshgrid of model errors.
        # Use cmin, cmax to ensure this uses the same colorbar as other error plots.
        plt.pcolormesh(pltgrid.lon, pltgrid.lat, log_error[1,:,:].T,
                                    vmin=cmin,
                                    vmax=cmax, 
                                    cmap=cmap2,
                                    zorder=1,
                                    transform=ccrs.PlateCarree())
        
        siglat = lats[cost_fnc[nsp, :, :].T < cost_threshold]
        siglon = lons[cost_fnc[nsp, :, :].T < cost_threshold]
        ax.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())

        ax.text(
            0.02, 0.95, "e", transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top', ha='left',
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'),
            zorder=10
        )

    # 1st row, 3rd column: Number of points in each TCH box
    #########################################################

    # Setup.
    cmin, cmax = 0, np.nanmax(nmpnts) * 1.3
    ax = plt.subplot2grid((2,3), (0, 2), colspan=1, rowspan=1, projection=ccrs.PlateCarree(central_longitude=180), aspect="auto")
    title = 'Number of points in NCH box'
    ax.set_title(title,loc='center',fontsize=fsize1)
    ax.set_extent([0, 360, -70, 70], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
    ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4) 
    gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
    gl.left_labels = False
    gl.bottom_labels = False

    # Plot number of points per TCH box, with its own colorbar.
    p_right = plt.pcolormesh(pltgrid.lon, pltgrid.lat, nmpnts.T,
                                vmin=cmin,
                                vmax=cmax, 
                                cmap=cmap3,
                                zorder=1,
                                transform=ccrs.PlateCarree())

    ax.text(
        0.02, 0.95, "c", transform=ax.transAxes,
        fontsize=14, fontweight='bold', va='top', ha='left',
        bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'),
        zorder=10
    )

    # Parameters for full function. 
    ##############################################################
    
    # Add shared colorbars outside the grid
    cbar_ax_left = fig.add_axes([0.045, 0.12, 0.3, 0.02])  # Below bottom-left map
    cbar_left = fig.colorbar(diff_plot, cax=cbar_ax_left, orientation="horizontal", extend="both")
    cbar_left.set_label("Difference")
        
    cbar_ax_center = fig.add_axes([0.365, 0.12, 0.3, 0.02])  # Below bottom-center map
    cbar_center = fig.colorbar(p_center, cax=cbar_ax_center, orientation="horizontal", extend="both")
    cbar_center.set_label("NCH Error")
    
    cbar_ax_right = fig.add_axes([0.685, 0.12, 0.3, 0.02])  # Below bottom-right map
    cbar_right = fig.colorbar(p_right, cax=cbar_ax_right, orientation="horizontal", extend="both")
    cbar_right.set_label("Points per box")
    
    plt.tight_layout(rect=[0, 0.15, 1, 1])

    ############################################
    savename = str(modname)+'-global-diagnostic.png'
    plt.savefig(outputdir+savename)
    plt.close(fig)

