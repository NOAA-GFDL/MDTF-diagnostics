"""
Compute daily average from sample files
"""
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from hn2016_falwa.xarrayinterface import QGDataset

data_dir = "/home/clare/GitHub/mdtf/inputdata/obs_data/finite_amplitude_wave_diag/"
u_path = f"{data_dir}era5_2022_u_component_of_wind.nc"
v_path = f"{data_dir}era5_2022_v_component_of_wind.nc"
t_path = f"{data_dir}era5_2022_temperature.nc"
wk_dir = "/home/clare/GitHub/mdtf/wkdir/"
u_daily_mean_path = f"{wk_dir}u_daily_mean.nc"
v_daily_mean_path = f"{wk_dir}v_daily_mean.nc"
t_daily_mean_path = f"{wk_dir}t_daily_mean.nc"
u_daily_mean_3steps_path = f"{wk_dir}u_daily_mean_3steps.nc"
v_daily_mean_3steps_path = f"{wk_dir}v_daily_mean_3steps.nc"
t_daily_mean_3steps_path = f"{wk_dir}t_daily_mean_3steps.nc"


def output_daily_avg(input_path, output_file, varname="ua"):
    input_file = xr.open_dataset(input_path)  # xarray.Dataset
    print(input_file)
    print("================")
    daily_resampled = input_file[varname].resample(time="1D").mean()
    print(daily_resampled)
    print("================")
    print(f"daily_resampled.shape:\n{daily_resampled.shape}")
    output_path = f"{wk_dir}{output_file}"
    print(f"Start outputing file: {output_path}")
    daily_resampled.to_netcdf(output_path)
    print(f"Finished outputing file: {output_path}")
    return output_path


if __name__ == '__main__':
    qgds = xr.open_mfdataset(f"{data_dir}era5_2022_[tuv].nc").resample(time="1D").mean()  # get daily mean
    print("Start interpolating.")
    uvtinterp = qgds.interpolate_fields()
    print("Finished interpolating. State reference state computation")
    refstates = qgds.compute_reference_states()
    print("Finished full procedures")
