"""
Attempt to work with daily mean data from daily_avg_model_notfinished.py
This runs on iMac
"""
import os
import xarray as xr
import numpy as np
from hn2016_falwa.xarrayinterface import QGDataset

from diagnostics.finite_amplitude_wave_diag.finite_amplitude_wave_diag_zonal_mean import gridfill_each_level

# These are local path to Clare's iMac
storage_path = f"{os.environ['HOME']}/Dropbox/GitHub/hn2016_falwa/github_data_storage/"
u_file = f"{storage_path}u_daily_mean_3steps.nc"
v_file = f"{storage_path}v_daily_mean_3steps.nc"
t_file = f"{storage_path}t_daily_mean_3steps.nc"

interp_u_file = f"{storage_path}u_daily_mean_interp_3steps.nc"
interp_v_file = f"{storage_path}v_daily_mean_interp_3steps.nc"
interp_t_file = f"{storage_path}t_daily_mean_interp_3steps.nc"
output_interp = True

coord_file = xr.open_dataset(u_file)
xlon = coord_file.coords['lon']
ylat = coord_file.coords['lat']
plev = coord_file.coords['level']

if output_interp:
    args_tuple = [(u_file, 'ua', interp_u_file), (v_file, 'va', interp_v_file), (t_file, 'ta', interp_t_file)]
    for original_file, var_name, interp_file in args_tuple:
        df = xr.open_dataset(original_file)
        field_of_interest = df[var_name]
        field_at_all_level = xr.apply_ufunc(
            gridfill_each_level,
            *[field_of_interest],
            input_core_dims=(('lat', 'lon'),),
            output_core_dims=(('lat', 'lon'),),
            vectorize=True)
        field_at_all_level = field_at_all_level.interp(
            lat=np.arange(-90, 91),
            kwargs={"fill_value": "extrapolate"})
        field_at_all_level.to_netcdf(interp_file)
        print(f"Finished outputing {interp_file}")

data = xr.open_mfdataset(f"{storage_path}[uvt]_daily_mean_interp_3steps.nc")
qgds = QGDataset(data, var_names={'u': 'ua', 'v': 'va', 't': 'ta'}, qgfield_kwargs={'northern_hemisphere_results_only': False})

uvtinterp = qgds.interpolate_fields()
refstates = qgds.compute_reference_states()
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()

# Problem encountered (2023/9/5)
# QGPV at k=0 are all 0
# Check temperature in original file:
# coord_file.variables['ta'].isel(time=0).max(axis=-1).max(axis=-1)
# array([274.72104, 277.33417, 280.6038 , 277.43634, 276.58832, 275.09503,
#        262.54962, 272.56357, 281.4019 , 284.82413, 289.1702 , 295.15497,
#        300.94907, 304.54556, 306.85352, 308.36664, 309.40552, 310.41824,
#        310.63425, 310.75208, 310.814  , 310.87076, 310.94513], dtype=float32)
# coord_file.coords['level'].values
# array([1000.,  925.,  850.,  775.,  700.,  600.,  500.,  400.,  300.,  250.,
#         200.,  150.,  100.,   70.,   50.,   30.,   20.,   10.,    7.,    5.,
#           3.,    2.,    1.], dtype=float32)
# Something went wrong...

