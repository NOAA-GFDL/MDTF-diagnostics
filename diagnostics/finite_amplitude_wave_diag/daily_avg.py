"""
Compute daily average from sample files
"""
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots


u_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ua.nc"
v_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.va.nc"
t_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ta.nc"
wk_dir = "/home/clare/GitHub/mdtf/wkdir/"


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
    # u_output_path = output_daily_avg(u_path, "u_daily_mean.nc", varname="ua")
    v_output_path = output_daily_avg(v_path, "v_daily_mean.nc", varname="va")
    t_output_path = output_daily_avg(t_path, "t_daily_mean.nc", varname="ta")
    print("Finished full procedures")
