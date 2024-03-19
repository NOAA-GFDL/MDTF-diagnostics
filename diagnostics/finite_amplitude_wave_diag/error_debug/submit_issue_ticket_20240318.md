

On branch `finite_amplitude_wave_diag`, when I execute:

```bash
./mdtf -f src/default_finite_amplitude_wave_diag.jsonc -v
```

The model data are located at:
```
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.ua.day.nc
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.va.day.nc
mdtf/inputdata/model/GFDL-CM3_historical_r1i1p1/day/GFDL-CM3_historical_r1i1p1.ta.day.nc
```

Which are downloaded from:
```
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/ua/ua_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/va/va_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
ftp://nomads.gfdl.noaa.gov/1/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/atmos/day/r1i1p1/v20120227/ta/ta_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc
```

This is the branch I am running MDTF from:
https://github.com/csyhuang/MDTF-diagnostics/tree/finite_amplitude_wave_diag/diagnostics/finite_amplitude_wave_diag

The python environment file:
https://github.com/csyhuang/MDTF-diagnostics/blob/finite_amplitude_wave_diag/src/conda/env_finite_amplitude_wave_diag.yml
