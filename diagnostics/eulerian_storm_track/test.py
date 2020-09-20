import plotter
import numpy as np 

lat = np.arange(-90, 90, 1)
lon = np.arange(-180, 180, 1)

lonGrid, latGrid = np.meshgrid(lon, lat)

plotter.plot(lonGrid, latGrid, lonGrid, show=True)
