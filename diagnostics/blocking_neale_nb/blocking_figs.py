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

import cartopy.crs as ccrs
import cartopy.feature as cfeature


import importlib
import sys
import pprint
import time


###################################################################################################### 
#  Plot 1D blocking %age for each longitude and for each ensemble set (which includes observations)
######################################################################################################



def block_plot_1d (block_meta,ens_block_1d,bseason,pshade='1',fig_out=False,dir_fig='',fig_name=None):

    fname = '-> block_plot_1d -> '

    
    tstart = time.time()

    lone_offset = 90. ; dlon = 30. # Offset to 'roll' the xarray, and lon deg. spacing

    ens_names = list(block_meta.index)
    
    # Fig stuff
    mp.rcParams.update({'font.size': 22})  # before the figure is made, so ticks/labels use it
    fig, ax = mp.subplots(figsize=(20,10))
    
   
    # Line styles (like the original NCL blocking_neale POD):
    #   obs            : black, solid/dashed/dotted
    #   model ensembles: colored, dashed, with shaded member spread
    #   MDTF case(s)   : colored, solid
    mod_cols  = ['blue','green','darkorange','purple','cyan'] ; imod = 0
    case_cols = ['magenta','red','saddlebrown','olive']        ; icase = 0
    obs_dash  = ['-','--',':','-.']                             ; iobs = 0

    ens_ystarts =  block_meta['Start Year'].values
    ens_yends =  block_meta['End Year'].values

  

    
    # Loop ensemble sets
    
    for iens,ens_name in enumerate(ens_names):
        
        print(fname,'Plotting for ensemble',ens_name)
        
        ens_type = block_meta.loc[ens_name]['Ensemble Type']
        ens_nruns = ens_block_1d[ens_name].sizes.get('name', 1)   # members actually in the data
        
        
        # Model vs. obs line settings.
        match ens_type:
            case 'model':
                ens_col = mod_cols[imod % len(mod_cols)]
                ens_dash = '--'
                imod += 1
            case 'mdtf':
                ens_col = case_cols[icase % len(case_cols)]
                ens_dash = '-'
                icase += 1
            case _:  # obs
                ens_col = 'black'
                ens_dash = obs_dash[iobs % len(obs_dash)]
                iobs += 1
        # Do a deep copy as rpeated invocation of this routine for fine turning messes the original data up if I don't.

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
        yrs = str(block_meta.loc[ens_name]['Start Year'])[:4] + '-' + str(block_meta.loc[ens_name]['End Year'])[:4]
        plabel = ens_name + ' ' + yrs + ('' if ens_nruns==1 else ' ('+str(ens_nruns)+' members)')
     
        ax.plot(da_iens_ave.lon, da_iens_ave,lw=4,color=ens_col,linestyle=ens_dash,label=plabel)   


        if (ens_nruns >1) : ax.fill_between(da_iens_ave.lon, da_iens_min, da_iens_max, color=ens_col, alpha=0.2, lw=0)


    
    

    ax.set_xlim([0,360]) 
    xticksn = np.arange(-lone_offset, 360-lone_offset+1, dlon)
    xticks = np.arange(0, 360+1, dlon)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f'{int(abs(tick))}°W' if tick < 0 else f'{int(tick)}°E' for tick in xticksn])
        
    ax.set_ylim(bottom=0)  # top set by the data (obs DJF peaks can exceed 35%)


    
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
    
    ax.legend(fontsize=18, frameon=False)


    
    # Output figure
    
    if fig_out: 
        fig_mid_text = '_' + ens_ystarts[0]+ '-' + ens_yends[1]
        fig_out_name = dir_fig + '/block_1d_freq_' + "_".join(ens_names) + fig_mid_text + '_' +bseason+'.png'
        if fig_name:  # fixed name, e.g. for linking from the POD html page
            fig_out_name = dir_fig + '/' + fig_name
        print(fname,'Saving figure to',fig_out_name)
        mp.savefig(fig_out_name,dpi=80,bbox_inches="tight")
    else:
        print(fname,'Figure output turned off. Not saving figure.')




#    mp.xticks(np.arange(-lone_offset, 271, 45), [f'{tick}°E' for tick in np.arange(-lone_offset, 271, 45)])


    print(fname,f'Duration: {time.time() - tstart}') ; print()

    return













###################################################################################################### 
#  Plot 2D blocking %age for each longitude and for each ensemble set (which includes observations)
######################################################################################################


def block_plot_2d(block_meta,ens_block_2d,block_season,fig_out=True,dir_fig='',ens_plot='0',fig_name=None):


    from cartopy.util import add_cyclic_point
    from matplotlib.colors import LinearSegmentedColormap, Normalize, BoundaryNorm
    
    fname = '-> block_plot_2d ->'


    ens_names = list(block_meta.index)
    nens = len(ens_names)
    ens_ystarts = block_meta['Start Year'].values  # used in the default figure file name
    ens_yends = block_meta['End Year'].values
    
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
    
            # Contour in the map's own (projected) coordinates. Letting cartopy
            # transform the filled contours (transform=PlateCarree) can invert a
            # polygon so one colour fills the whole map (seen for a 20-year ANN
            # case); projecting the grid first avoids that. The cyclic point
            # closes the seam at 0E.
            # (by hand: add_cyclic_point rejects the slightly uneven MERRA longitudes)
            vals_cyc = np.concatenate([da_iens_ave.values, da_iens_ave.values[:, :1]], axis=1)
            lon_cyc = np.append(iens_lon.values, iens_lon.values[0] + 360.)
            lon2d, lat2d = np.meshgrid(lon_cyc, iens_lat.values)
            xy = projection.transform_points(ccrs.PlateCarree(), lon2d, lat2d)
            ax_all = ax.contourf(xy[..., 0], xy[..., 1], vals_cyc, levels=bcontours, norm=norm,
                                 cmap=cmapb, extend='max')
    
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
    
    # Output figure
    
    if fig_out: 
        fig_mid_text = '_' + ens_ystarts[0]+ '-' + ens_yends[1]
        fig_out_name = dir_fig + '/block_2d_freq_' + "_".join(ens_names) + fig_mid_text + '_' +block_season+'.png'
        if fig_name:  # fixed name, e.g. for linking from the POD html page
            fig_out_name = dir_fig + '/' + fig_name
        print(fname,'Saving figure to',fig_out_name)
        mp.savefig(fig_out_name,dpi=80,bbox_inches="tight")
    else:
        print(fname,'Figure output turned off. Not saving figure.')
    
    tstart = time.time()

    return






###################################################################################################### 
#  Plot PDF of blocking strength for different longitudinal sectors
######################################################################################################



def smth9(data, p=0.5, q=0.5, wrap_x=True):
    """9-point smoother, same as NCL smth9 (2D array (y, x)).

    f0 = f + p/4*(sum of 4 side neighbours - 4f) + q/4*(sum of 4 corner neighbours - 4f).
    Wraps in x (longitude) when wrap_x; the first and last rows (y) are left
    unchanged, as in NCL.
    """
    f = np.asarray(data, dtype=float)
    if wrap_x:
        fe, fw = np.roll(f, -1, axis=1), np.roll(f, 1, axis=1)
    else:
        fe, fw = f.copy(), f.copy()
        fe[:, :-1] = f[:, 1:]; fw[:, 1:] = f[:, :-1]
    fn, fs = np.roll(f, -1, axis=0), np.roll(f, 1, axis=0)
    fne, fnw = np.roll(fe, -1, axis=0), np.roll(fw, -1, axis=0)
    fse, fsw = np.roll(fe, 1, axis=0), np.roll(fw, 1, axis=0)
    out = f + (p/4.)*(fe + fw + fn + fs - 4.*f) + (q/4.)*(fne + fnw + fse + fsw - 4.*f)
    out[0, :] = f[0, :]
    out[-1, :] = f[-1, :]
    return out


def block_plot_anncycle(block_meta, ens_block_ac, ens_list, fig_title='', fig_out=True,
                        dir_fig='', fig_name='block_freq_anncycle.png', n_smooth=20):
    """Hovmueller (longitude x day of year) of the 1D blocking frequency annual cycle,
    one panel per ensemble in *ens_list* (ensemble mean over members). Matches the
    annual-cycle figures of the original NCL blocking_neale POD (blocking.ncl):
    *n_smooth* passes of the 9-point smoother (smth9, p=q=0.5, wrapped in
    longitude), contour lines every 5%, fill: none below 10%, light grey 10-20%,
    dark grey from 20%.

    ens_block_ac[ens]: (name, dayofyear, lon) blocked fraction from
    block_utils.block_z500_freq(..., block_diag='1DAC').
    """
    fname = '-> block_plot_anncycle ->'
    lone_offset = 90. ; dlon = 30.
    levels = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]      # contour lines (NCL cnLevels)
    fill_levels = [10, 20, 1000]                            # NCL fill: none, light, dark grey
    fill_colors = ['#aaaaaa', '#555555']
    month_mid = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
    month_lab = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

    n = len(ens_list)
    # Square panels stacked vertically, like the NCL gsn_csm_hov page
    fig, axs = mp.subplots(n, 1, figsize=(7.5, 7.0*n + 0.8), squeeze=False, constrained_layout=True)
    cf = None
    for ax, ens_name in zip(axs.flat, ens_list):
        da = ens_block_ac[ens_name]
        nmem = da.sizes.get('name', 1)
        if 'name' in da.dims:
            da = da.mean('name')
        da = 100. * da.transpose('dayofyear', 'lon')
        # Roll so the plot starts at 90W, as in the 1D plot
        ilon_roll = int(lone_offset / float(da.lon[1] - da.lon[0]))
        data = np.roll(da.values, ilon_roll, axis=1)
        # Smooth as in the NCL POD: repeated 9-point smoother
        for _ in range(n_smooth):
            data = smth9(data, 0.5, 0.5, wrap_x=True)
        x = da.lon.values - float(da.lon[0])
        doy = da.dayofyear.values

        cf = ax.contourf(x, doy, data, levels=fill_levels, colors=fill_colors)
        cs = ax.contour(x, doy, data, levels=levels, colors='black', linewidths=0.8)
        ax.clabel(cs, [l for l in levels[::2] if l in cs.levels], fmt='%d', fontsize=10, inline_spacing=2)

        ax.set_box_aspect(1)   # square panel (NCL Hovmueller proportions)
        ax.set_xlim([0, 360])
        xticksn = np.arange(-lone_offset, 360-lone_offset+1, dlon)
        ax.set_xticks(np.arange(0, 360+1, dlon))
        ax.set_xticklabels([f'{int(abs(t))}°W' if t < 0 else f'{int(t)}°E' for t in xticksn], fontsize=9)
        ax.set_yticks(month_mid)
        ax.set_yticklabels(month_lab, fontsize=12)
        yrs = str(block_meta.loc[ens_name]['Start Year'])[:4] + '-' + str(block_meta.loc[ens_name]['End Year'])[:4]
        mem_txt = '' if nmem == 1 else f', {nmem} members'
        ax.set_title(f'{ens_name} ({yrs}{mem_txt})', fontsize=16)

    fig.suptitle(fig_title or 'Blocking frequency annual cycle', fontsize=16)
    fig.text(0.5, -0.01, 'Blocking frequency (%): contours every 5%, shaded 10-20% and above 20%',
             ha='center', va='top', fontsize=10)

    if fig_out:
        fig_out_name = dir_fig + '/' + fig_name
        print(fname, 'Saving figure to', fig_out_name)
        mp.savefig(fig_out_name, dpi=80, bbox_inches='tight')
    return fig


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
    









