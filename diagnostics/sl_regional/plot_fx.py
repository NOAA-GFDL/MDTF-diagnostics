import numpy as np
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
##delete the following?
# from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def make_regional_plots(modname,reginfo, ds_grid, tchgrids, model_reg_col, cnes_reg_col, dtu_reg_col, errs, cost_funcs, num_pointss,cost_threshold, outputdir):
    cmap1='Spectral_r'
    cmap2='cividis'
    cmap3 = 'binary'
    fsize1=10
    fsize2=14
    fweight='bold'
    
    for nreg in np.arange(len(reginfo)):
        fig = plt.figure(figsize=(12,12))
        rotated_crs = ccrs.RotatedPole(pole_longitude=reginfo.iloc[nreg].proj_longitude, 
                                       pole_latitude=reginfo.iloc[nreg].proj_latitude)
        var=np.log2(errs[nreg]*100)
        cost_fnc = cost_funcs[nreg]
        pltgrid=tchgrids[nreg]
        nmpnts=num_pointss[nreg]
        lons, lats = np.meshgrid(pltgrid.lon, pltgrid.lat)
                        
        for nsp in range(len(cost_fnc)):
    
            label = 'MDSL diff'
            units = '(cm)'    
            
            if nsp<1:
                diff=model_reg_col[nreg] - dtu_reg_col[nreg]
                titstr= (modname) + ' - DTU' + ' ' + label + ' ' + units
            else:
                diff=cnes_reg_col[nreg] - dtu_reg_col[nreg]
                titstr= 'CNES - DTU' + ' ' + label + ' ' + units
                
            diff=diff*100
            cmin=-50; cmax=-cmin
            ax = plt.subplot2grid((2,3), (nsp, 0), colspan=1, rowspan=1, projection=rotated_crs, aspect="auto")
            p_l2=plt.pcolormesh(ds_grid.lon,
                         ds_grid.lat, 
                         diff,
                         vmin=cmin, 
                         vmax=cmax, 
                         cmap=cmap1,
                         zorder=1,
                         shading='nearest',  
                         transform=ccrs.PlateCarree())
            ax.set_extent([reginfo.iloc[nreg].west_bound, reginfo.iloc[nreg].east_bound,
                           reginfo.iloc[nreg].south_bound, reginfo.iloc[nreg].north_bound], 
                          crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
            pos = ax.get_position()  # get the original position
            ax.set_title(titstr,loc='center',fontsize=fsize1)
    
            label = 'error (log$_2$ scale)'
            
            cmin=0; cmax = np.nanmax(var[2,:,:])
            
            ax = plt.subplot2grid((2,3), (1, nsp+1), colspan=1, rowspan=1, projection=rotated_crs, aspect="auto")
            
            if nsp<1:
                cost=cost_fnc[1, :, :].T
                plotvar=var[1,:,:].T
                refname='DTU'
            else:
                cost=cost_fnc[0, :, :].T
                plotvar=var[0,:,:].T  
                refname='CNES'
                
            titstr= refname + ' ' + label + ' ' + units
               
            p=plt.pcolormesh(pltgrid.lon,
                             pltgrid.lat, 
                             plotvar,
                             vmin=cmin, 
                             vmax=cmax, 
                             cmap=cmap2,
                             zorder=1,
                             transform=ccrs.PlateCarree())
            ax.set_extent([reginfo.iloc[nreg].west_bound, reginfo.iloc[nreg].east_bound,
                           reginfo.iloc[nreg].south_bound, reginfo.iloc[nreg].north_bound], 
                          crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
            ax.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
            pos = ax.get_position()  # get the original position
            
            siglat = lats[cost<cost_threshold]
            siglon = lons[cost<cost_threshold]
            plt.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())
            
            gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
            if nsp<1:
                gl.left_labels = True
                if nreg>(len(reginfo)-2):
                    gl.bottom_labels = True
    
            # ax.set_title('Stippling: cost <' + str(int(cost_threshold)) + ' relative to ' + refname,loc='center',fontsize=fsize1)
            ax.set_title(titstr,loc='center',fontsize=fsize1)
    
    
        titstr= modname + ' ' + label + ' ' + units

        ax1 = plt.subplot2grid((2,3), (0, 1), colspan=1, rowspan=1, projection=rotated_crs, aspect="auto")
        p_left=plt.pcolormesh(pltgrid.lon,pltgrid.lat, var[2,:,:].T,
                              vmin=cmin,
                              vmax=cmax, 
                              cmap=cmap2,
                              zorder=1,
                              transform=ccrs.PlateCarree())
        ax1.set_extent([reginfo.iloc[nreg].west_bound, reginfo.iloc[nreg].east_bound,
                        reginfo.iloc[nreg].south_bound, reginfo.iloc[nreg].north_bound], 
                       crs=ccrs.PlateCarree())
        ax1.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
        ax1.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)
        ax1.set_title(modname,loc='center',fontsize=fsize1)
    
        gl = ax1.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        gl.left_labels = False
        gl.bottom_labels = True
        
        cost=cost_fnc[1, :, :].T
        siglat = lats[cost<cost_threshold]
        siglon = lons[cost<cost_threshold]
        plt.scatter(siglon, siglat, color="w", marker=".", s=4, zorder=2, transform=ccrs.PlateCarree())
        
        gl = ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        if nsp<1:
            gl.left_labels = True
            if nreg>(len(reginfo)-2):
                gl.bottom_labels = True
    
        # ax1.set_title('Stippling: cost <' + str(int(cost_threshold)) + ' relative to ' + 'DTU',loc='center',fontsize=fsize1)
        ax1.set_title(titstr,loc='center',fontsize=fsize1)
    
        cmin=0; cmax=np.nanmax(nmpnts)
        ax2 = plt.subplot2grid((2,3), 
                               (0, 2), 
                               colspan=1, 
                               rowspan=1, 
                               projection=rotated_crs, 
                               aspect="auto")
        
        p_right=plt.pcolormesh(pltgrid.lon,
                               pltgrid.lat, 
                               nmpnts.T,
                               vmin=cmin,
                               vmax=cmax, 
                               cmap=cmap3,
                               zorder=1,
                               transform=ccrs.PlateCarree())
        
        ax2.set_extent([reginfo.iloc[nreg].west_bound, reginfo.iloc[nreg].east_bound,
                        reginfo.iloc[nreg].south_bound, reginfo.iloc[nreg].north_bound], 
                       crs=ccrs.PlateCarree())
        ax2.add_feature(cfeature.LAND.with_scale('110m'),zorder=4)
        ax2.add_feature(cfeature.COASTLINE, edgecolor="black",zorder=4)  
        # ax2.set_title(modname,loc='center',fontsize=fsize1)
        ax2.set_title('PTS/TCH box',loc='center',fontsize=fsize1)
    
        gl = ax2.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False,zorder=6)
        gl.left_labels = False
        gl.bottom_labels = True
    
        plt.tight_layout()
    
        # Add shared colorbars outside the grid
        cbar_ax_left2 = fig.add_axes([0.0, 0.1, 0.3, 0.02])  # Below bottom-left map
        cbar_left2 = fig.colorbar(p_l2, cax=cbar_ax_left2, orientation="horizontal", extend="both")
        cbar_left2.set_label("Difference")
        
        cbar_ax_left = fig.add_axes([0.35, 0.1, 0.3, 0.02])  # Below bottom-left map
        cbar_left = fig.colorbar(p_left, cax=cbar_ax_left, orientation="horizontal", extend="both")
        cbar_left.set_label("TCH Error")
    
        cbar_ax_right = fig.add_axes([0.7, 0.1, 0.3, 0.02])  # Below bottom-right map
        cbar_right = fig.colorbar(p_right, cax=cbar_ax_right, orientation="horizontal", extend="both")
        cbar_right.set_label("PTS/TCH box")
    
        plt.tight_layout(rect=[0, 0.15, 1, 1])
    
       # plt.savefig(outputdir+modname+reginfo.iloc[nreg].RegionName + '_regional_TCH.png')
        #plt.close(fig)
        import os
        filepath = os.path.join(outputdir, f"{modname}{reginfo.iloc[nreg].RegionName}_regional_TCH.png")
        plt.savefig(filepath)
        plt.close(fig)