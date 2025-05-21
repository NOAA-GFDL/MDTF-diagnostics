'''
	BLOCKING FIGURE ROUTINES
'''




'''
    block_plot_1d - Line plot of 1D blocking Z500 metric      

'''

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.pyplot as mp

#import cartopy.crs as ccrs
#import cartopy.feature as cfeature


import importlib
import sys
import pprint
import time


###################################################################################################### 
#  Plot 1D blocking %age for each longitude and for each ensemble set (which includes observations)
######################################################################################################



def block_plot_1d (block_meta,ens_block_1d,bseason,pshade='1',fig_out=False,dir_fig=''):

    fname = '-> block_plot_1d -> '

    
    tstart = time.time()

    lone_offset = 90. ; dlon = 30. # Offset to 'roll' the xarray, and lon deg. spacing

    ens_names = list(block_meta.index)
    
    # Fig stuff
    fig, ax = mp.subplots(figsize=(20,10))
    
   
    # Plot line characteristicsf
    ens_cols = ['blue','red','green','purple'] ; imod=0
    obs_dash = ['-','--',':'] ; iobs =0
    obs_mark = ['o','s','+']  

    ens_ystarts =  block_meta['Start Year'].values
    ens_yends =  block_meta['End Year'].values

  

    
    # Loop ensemble sets
    
    for iens,ens_name in enumerate(ens_names):
        
        print(fname,'Plotting for ensemble',ens_name)
        
        ens_type = block_meta.loc[ens_name]['Ensemble Type']
        ens_nruns =  len(block_meta.loc[ens_name]['Run Name'])
        
        
        # Model vs. obs line settings.
        print(f"DRBDBG L74 {ens_type=}")
        match ens_type:
            case ('model', 'mdtf'):
                ens_col = ens_cols[imod]
                ens_dash = '-'
                ens_mark = None
                mark_size = None
                imod += 1
            case 'obs':
                ens_col = 'black'
                ens_dash = obs_dash[iobs]
                ens_mark = obs_mark[iobs]
                mark_size = 15
                iobs += 1
        # Do a deep copy as rpeated invocation of this routine for fine turning messes the original data up if I don't.
        print(f"DRBDBG {ens_block_1d[ens_name].dims=}")

        da_iens = ens_block_1d[ens_name]

        
        # Shift lon of data for better regional plotting
        ilon_roll =  int(lone_offset/(da_iens.lon[1]-da_iens.lon[0]))
        da_iens = da_iens.roll(lon=ilon_roll)
            
        
        # Set rolling smoothing for display.
        da_iens = da_iens.rolling(lon=3,center=True).mean()
        da_iens = 100.*da_iens # Scale to %age

        #  Set min/mean/max of each ensemble set
        da_iens_ave = da_iens.mean(dim='name')

        
        # Shade betweeen options min/max range of +/- 1 or 2 std.
        
        if pshade=='mm':
            shade_title = 'min/max range'
            
            da_iens_min = da_iens.min(dim='name') 
            da_iens_max = da_iens.max(dim='name')
        else:
            std_mag = int(pshade)
            shade_title = '-/+ '+pshade+' std'
                      
            da_iens_std = da_iens.std(dim='name')     
            da_iens_min = da_iens_ave-std_mag*da_iens_std         
            da_iens_max = da_iens_ave+std_mag*da_iens_std       
  
        # Plot line and fill between min/max within ensemble
        plabel = ens_name if ens_nruns==1 else ens_name+'('+str(ens_nruns)+')'
     
        ax.plot(da_iens_ave.lon, da_iens_ave,lw=4,color=ens_col,linestyle=ens_dash,
                marker=ens_mark, markersize = mark_size, markevery=10, mew=3, fillstyle='none', label=plabel)   


        if (ens_nruns >1) : ax.fill_between(da_iens_ave.lon, da_iens_min, da_iens_max, alpha=0.35)


    
    

    mp.rcParams.update({'font.size': 22})
    
    ax.set_xlim([1,365]) 
    xticksn = np.arange(-lone_offset, 360-lone_offset+1, dlon)
    xticks = np.arange(0, 360+1, dlon)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f'{int(abs(tick))}°W' if tick < 0 else f'{int(tick)}°E' for tick in xticksn])
        
    ax.set_ylim([0.01,35])


    
# Add years into title if common.
    
    if (min(ens_ystarts) == max(ens_ystarts) and min(ens_yends) == max(ens_yends)): 
        yr_title = ' (yrs: '+ens_ystarts[0]+' - '+ens_yends[0]+')  '
        fig_mid_text = '_' + ens_ystarts[0]+ '-' + ens_yends[0]        
    else:
        yr_title = ' '
        fig_mid_text = ' ' 

    
        
    ax.set_title(bseason+ ' '+yr_title+'  '+shade_title)
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Blocking Frequency (%)')

# Add year range into legend
    
    ax.legend()


    
    # Output figure
    
    if fig_out: 
        fig_mid_text = '_' + ens_ystarts[0]+ '-' + ens_yends[1]
        mp.savefig(dir_fig + 'block_1d_freq_' + "_".join(ens_names) + fig_mid_text + '_' +bseason+'.png',dpi=80,bbox_inches="tight")




#    mp.xticks(np.arange(-lone_offset, 271, 45), [f'{tick}°E' for tick in np.arange(-lone_offset, 271, 45)])


    print(fname,f'Duration: {time.time() - tstart}') ; print()

    return













###################################################################################################### 
#  Plot 2D blocking %age for each longitude and for each ensemble set (which includes observations)
######################################################################################################


def block_plot_2d(block_meta,ens_block_2d,block_season,fig_out=True,dir_fig='',ens_plot='0'):


    from cartopy.util import add_cyclic_point
    from matplotlib.colors import LinearSegmentedColormap, Normalize, BoundaryNorm
    
    fname = '-> block_plot_2d ->'


    ens_names = list(block_meta.index)
    nens = len(ens_names)
    
    # Createplot of a stereographic projection centered over the North Pole
    projection = ccrs.NorthPolarStereo()

    # Set up subplot paneling
    ncols = 3
    nrows,premain = divmod(nens, ncols)
    nrows = nrows+1

    figsize = (8*ncols,8*nrows)
    
    fig, ax0 = mp.subplots(nrows,ncols,subplot_kw={'projection': projection}, figsize=figsize,constrained_layout=True)

    

    # Flattedn and trikm aaxes if needed

    
    ax= ax0.flat
    
    

    bcontours = [0,2,4,6,8,10,12,14,16,18,20,25,30]
#    norm = Normalize(vmin=min(bcontours), vmax=max(bcontours))
    norm = BoundaryNorm(boundaries=bcontours, ncolors=256)
    
    colors = ['white', 'cyan', 'cornflowerblue','blue','green','darkgreen', 'yellow','gold', 'orange', 'red', 'darkred','lightpink','hotpink','magenta']
    cmapb = LinearSegmentedColormap.from_list('custom_colormap', colors, N=256)
    
    text_size_percentage = 2
    text_size = ncols*100.*text_size_percentage / fig.get_size_inches()[0]
  




    # LOOP OVER ENSEMBLE SETS #
    
    for iens,ax in enumerate(ax):

        if iens<=nens-1: # Active plots (ax)
           
            ens_name = ens_names[iens]
            print(fname,'Plotting for ensemble',ens_name)
            
            ens_type = block_meta.loc[ens_name]['Ensemble Type']
            ens_nruns = len(block_meta.loc[ens_name]['Run Name'])
            ens_name = ens_names[iens]
            
    
            # Do a deep copy as repeated invocation of this routine for fine turning messes the original data up if I don't.
            da_iens = ens_block_2d[ens_name]
            da_iens = 100.*da_iens # Scale to %age
            
            
            # Set min/mean/max of each ensemble set
            # Average plotting for now (ens_plot will control this in future).
    
            match(ens_plot):
                case 'av':
                    da_iens_ave = da_iens.mean(dim='name').squeeze()
                case '0':
                    da_iens_ave = da_iens.isel(name=0).squeeze()
            
            iens_lat = da_iens_ave.lat
            iens_lon = da_iens_ave.lon
    
            # Lon wrapping grid point for plotting
    
#            iens_ave_cyc, iens_lon_cyc = add_cyclic_point(da_iens_ave, iens_lon)
            iens_ave_cyc, iens_lon_cyc = da_iens_ave,iens_lon                                         
            
            # Have to recast as DataArrays - annoying.
            
            iens_lon_cyc = xr.DataArray(iens_lon_cyc,
                                  dims='lon',
                                  coords={'lon': iens_lon_cyc})
            
            iens_ave_cyc = xr.DataArray(iens_ave_cyc,
                                  dims=('lat', 'lon'),
                                  coords={'lat': iens_lat, 'lon': iens_lon_cyc})
    
      
         
            # Plot data with cyclic points including coasts, gridlines/labels and ens_name
    
            ax_all = ax.contourf(iens_lon_cyc,iens_lat, iens_ave_cyc, levels=bcontours,norm=norm,transform=ccrs.PlateCarree(),cmap=cmapb,extend='max')   
    
            ax.coastlines()
            gl = ax.gridlines(color='C7',lw=1,ls=':',draw_labels=True,rotate_labels=False,ylocs=[40,60,80])
            gl.xlabel_style = {'size': text_size*0.5}
            gl.ylabel_style = {'size': text_size*0.5}
    
           
            polarCentral_set_latlim((40,90),ax)
            
            ax.set_title(ens_name, fontsize=text_size)

        if iens>nens-1: # Inactivate plots
            fig.delaxes(ax)
    
    # Specify the position of the colorbar

    fig.suptitle('Blocking Frequency (%) - '+ block_season, fontsize=text_size,ha='center',va='bottom')
    
#    fig.subplots_adjust(right=0.93,wspace=0.2, hspace=5)
#    cbar_ax = fig.add_axes([0.95, 0.27, 0.03, 0.36])

#    cbar_ax.set_title('%',fontsize=text_size)
#    cbar_ax.tick_params(labelsize=text_size*0.5)


    
    cbar = fig.colorbar(ax_all, ax=ax0[:, ncols-1], ticks=bcontours,location='right', shrink=0.25)

#    fig.tight_layout()
    
    
    tstart = time.time()

    return






###################################################################################################### 
#  Plot PDF of blocking strength for different longitudinal sectors
######################################################################################################



def block_plot_1d_pdf(block_meta,ens_block_2d,block_season,fig_out=True):

    
    
    return

def jet_var_plot():
    return


'''
 Small figure functions
'''


# Add lon labels to stereographic plots.

def polarCentral_set_latlim(lat_lims, ax):

    import matplotlib.path as mpath
    
    ax.set_extent([-180, 180, lat_lims[0], lat_lims[1]], ccrs.PlateCarree())
    theta = np.linspace(0, 2*np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    ax.set_boundary(circle, transform=ax.transAxes)
    









