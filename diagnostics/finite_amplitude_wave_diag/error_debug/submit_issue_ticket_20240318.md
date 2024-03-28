When I tried testing my code by running `./mdtf`, I encountered error at the data preparation stage and wonder how I can debug this. I was running from my branch:

https://github.com/csyhuang/MDTF-diagnostics/tree/finite_amplitude_wave_diag

After I executed:

```bash
./mdtf -f src/default_finite_amplitude_wave_diag.jsonc -v
```

I encountered the following error at the data preparation stage:
```
Received event while preprocessing <#MKNN:finite_amplitude_wave_diag.ta>: DataPreprocessEvent("Caught exception while cleaning attributes to write data for <#MKNN:finite_amplitude_wave_diag.ta>: ValueError('The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()').")
```
The full log file can be found here: [GFDL-CM3_historical_r1i1p1.log](GFDL-CM3_historical_r1i1p1.log)

The config files can be found at:
- https://github.com/csyhuang/MDTF-diagnostics/blob/finite_amplitude_wave_diag/src/default_finite_amplitude_wave_diag.jsonc
- https://github.com/csyhuang/MDTF-diagnostics/blob/finite_amplitude_wave_diag/diagnostics/finite_amplitude_wave_diag/settings.jsonc

On my own linux machine, I put the model data at (below are the relative paths):
```
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.ua.day.nc
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.va.day.nc
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.ta.day.nc
```

which were downloaded from:
```
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/ua/ua_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/va/va_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/ta/ta_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
```

This is my python environment file:
https://github.com/csyhuang/MDTF-diagnostics/blob/finite_amplitude_wave_diag/src/conda/env_finite_amplitude_wave_diag.yml

May you advice how I can proceed? Thanks!

Clare