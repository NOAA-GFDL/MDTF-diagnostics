import numpy as np 
import defines
import os

import matplotlib.pyplot as plt
import scipy.io as sio
import cartopy

year = 2000
mat_file = os.path.join(defines.read_folder, '%s_%d.mat'%(defines.model, year))
print(mat_file)

if (not os.path.exists(mat_file)): 
  raise Exception ('.mat file does not exist.')

data = sio.loadmat(mat_file)
cyc = data['cyc'][0]

data_crs = cartopy.crs.PlateCarree()
ax = plt.axes(projection=cartopy.crs.NorthPolarStereo())
ax.coastlines()
ax.set_extent([-180, 180, 30, 90], crs=cartopy.crs.PlateCarree())

for i, track in enumerate(cyc): 
  lat = np.squeeze(track['fulllat'])  
  lon = np.squeeze(track['fulllon'])  
  lon[lon > 180] -= 360
  ax.plot(lon, lat, 'b-*', transform=data_crs)
  if(i > 100): 
    break

plt.show()



