import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

all_file = xr.open_dataset("refstates_2022Jan.nc")
plt.contourf(
    all_file.uref['ylat'],
    all_file.uref['height'],
    all_file.uref,
    np.arange(-50, 101, 10))
plt.colorbar()
plt.show()
