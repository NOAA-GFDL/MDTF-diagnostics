import pickle
import numpy as np 
import matplotlib.pyplot as plt
import os

import sys
sys.path.append('/localdrive/drive10/mcms_tracker')
import defines
import matplotlib as mpl

# creating colorbar as per the paper
c_pal = ['rgb(255,255,216)','rgb(137,221,183)','rgb(0, 149, 195)','rgb(6, 40, 130)']
c_pal = [eval(color[3:]) for color in c_pal]
c_pal = [(color[0]/256., color[1]/256., color[2]/256.) for color in c_pal]
jj_cmap = mpl.colors.LinearSegmentedColormap.from_list('jj', c_pal, N=12)

# reading in the temporary pickle file to plot
file = os.path.join(defines.read_folder, 'tmp.pkl')

if (not os.path.exists(file)):
     print(f'File not found') 

transect = pickle.load(open(file, 'rb'))

# plotting the figures
for season in defines.transect_season_list:
  # Looping through all the 3d variables 
  for var_name in defines.transect_var_list:
    # Looping through the different hemispheres
    for hemis in defines.transect_hemis_list:
      plt.close('all')
      plt.figure(figsize=(12,8))

      if (var_name == 'T'):
        levels = np.arange(210, 290, 10);  cmap='default' # T
      elif (var_name in ['U', 'V']):
        levels = np.arange(-40, 40, 5); cmap='bwr' # U
      else: 
        levels = 20; cmap=jj_cmap
      plt.subplot(2,2,1)
      ftype = 'cf'
      lm_type = 'ocean'
      tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
      # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
      plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
      plt.colorbar(); 
      plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
      plt.xlim(-1500, 1500)

      plt.subplot(2,2,2)
      ftype = 'wf'
      lm_type = 'ocean'
      tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
      # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
      plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
      plt.colorbar(); 
      plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
      plt.xlim(-1500, 1500)

      plt.subplot(2,2,3)
      ftype = 'cf'
      lm_type = 'land'
      tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
      # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
      plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
      plt.colorbar(); 
      plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
      plt.xlim(-1500, 1500)

      plt.subplot(2,2,4)
      ftype = 'wf'
      lm_type = 'land'
      tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
      # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
      plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
      plt.colorbar(); 
      plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
      plt.xlim(-1500, 1500)

      plt.tight_layout()
      out_file = os.path.join(defines.images_folder, f'{defines.model}_{defines.transect_years[0]}_{defines.transect_years[1]}_transect_{hemis.upper()}_{var_name.upper()}_{season.upper()}.png')
      plt.savefig(out_file, dpi=300.) 


