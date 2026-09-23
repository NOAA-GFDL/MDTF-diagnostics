# Rossby wave packet diagnostic

`rossby_wave_packet` is an MDTF process-oriented diagnostic (POD) for
six-hourly model northward wind at 250 hPa. It calculates filtered wind,
envelope amplitude, wrapped phase, phase speed, and zonal and meridional group
velocity. The scientific calculation is also available as one Python function.

- Scientific PI: Lei Wang, wanglei@purdue.edu
- Developer: Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com

The driver uses the model variable, coordinate names, calendar, dates, and
processed asset supplied by the MDTF data layer. It supports regular global
latitude-longitude data with standard/Gregorian, proleptic Gregorian, Julian,
365-day, 366-day, or 360-day calendars. A pressure coordinate is optional when
the input already represents one level.

## Package layout

- `src/rossby_wave_packet.py`: MDTF and standalone driver.
- `src/rossby_wave_packet_core.py`: reusable scientific calculation.
- `src/rossby_wave_packet_group_velocity.py`: packet-tracking group velocity.
- `plots/scripts/plot_rossby_wave_packet.py`: standard POD web figures.
- `plots/scripts/plot_rossby_wave_packet_snapshot.py`: six-panel snapshot from
  an existing result.
- `plots/output/rossby_wave_packet_snapshot_6x1.png`: retained example figure.
- `settings.jsonc`: MDTF data request, dependencies, and defaults.
- `rossby_wave_packet.html`: MDTF output-page template.
- `doc/rossby_wave_packet.rst`: Diagnostics Reference source.
- `rossby_wave_packet_runtime_config_template.yml`: framework run template.
- `tests/test_rossby_wave_packet.py`: synthetic unit tests.

Generated scientific data belong in `output/` or another data workspace, not
in this package.

## MDTF use

Place the directory at `diagnostics/rossby_wave_packet` in an MDTF checkout.
Add the diagnostic to the runtime configuration:

```yaml
pod_list:
  - rossby_wave_packet
```

Supply one or more model cases through a valid MDTF data catalog, then run:

```bash
python mdtf_framework.py -f <runtime-configuration.jsonc>
```

The framework selects and translates six-hourly `northward_wind` in `m s-1`
at 250 hPa, writes `case_info.yml` and the processed catalog, and invokes
`src/rossby_wave_packet.py`. The POD requests a rectilinear, regular, global
latitude-longitude grid. Regrid curvilinear, cubed-sphere, or regional fields
before running the diagnostic.

The model output directory contains:

- `rossby_wave_packet_amplitude.png`;
- `rossby_wave_packet_phase.png`;
- `rossby_wave_packet_phase_speed.png`;
- `rossby_wave_packet_group_velocity.png`;
- `netCDF/rossby_wave_packet_<case>.nc` for each model case;
- `netCDF/rossby_wave_packet_output_manifest.csv`.

## Driver examples

Run a regular latitude-longitude NetCDF file outside the framework:

```bash
python src/rossby_wave_packet.py \
  --input <model-wind.nc> \
  --output-dir output \
  --start-date 1980-01-01 \
  --end-date 1980-12-31T23:59:59
```

For a single-level field, use `--level none`. If metadata are incomplete,
provide all names explicitly:

```bash
python src/rossby_wave_packet.py \
  --input <model-wind.nc> \
  --variable V \
  --time-name Time \
  --latitude-name latitude \
  --longitude-name longitude \
  --level-name lev_p \
  --level 250 \
  --output-dir output
```

Print the generated command help with:

```bash
python src/rossby_wave_packet.py --help
```

The driver exports `DRIVER_HELP`, the dictionary used to build that interface.
This keeps programmatic help and command-line help synchronized:

```python
from src.rossby_wave_packet import DRIVER_HELP

print(DRIVER_HELP["amplitude_threshold"])
```

## Driver help dictionary

| Dictionary key | Command option | Default | Meaning |
|---|---|---:|---|
| `input` | `--input` | MDTF catalog | Standalone NetCDF input |
| `catalog_file` | `--catalog-file` | case metadata | Intake-ESM catalog header |
| `case_info` | `--case-info` | `case_env_file` | MDTF case-information YAML |
| `case` | `--case` | all | One MDTF case label |
| `frequency` | `--frequency` | `6hr` | Catalog-only search frequency |
| `output_dir` | `--output-dir` | `output` | Standalone output directory |
| `output_prefix` | `--output-prefix` | `rossby_wave_packet` | Product prefix |
| `variable` | `--variable` | inferred | Wind variable name |
| `time_name` | `--time-name` | inferred | Time coordinate name |
| `latitude_name` | `--latitude-name` | inferred | Latitude coordinate name |
| `longitude_name` | `--longitude-name` | inferred | Longitude coordinate name |
| `level_name` | `--level-name` | inferred | Pressure coordinate name |
| `level` | `--level` | `250` | Pressure in hPa, or `none` |
| `latitude_min` | `--latitude-min` | `25` | Southern latitude bound |
| `latitude_max` | `--latitude-max` | `85` | Northern latitude bound |
| `start_date` | `--start-date` | full period | First included date |
| `end_date` | `--end-date` | full period | Last included date |
| `prefiltered_input` | `--prefiltered-input` | off | Skip preprocessing and filtering |
| `anomaly_method` | `--anomaly-method` | `harmonic` | `harmonic`, `time_mean`, or `none` |
| `annual_harmonics` | `--annual-harmonics` | `4` | Highest annual harmonic |
| `wavenumber_min` | `--wavenumber-min` | `4` | Lowest zonal wavenumber |
| `wavenumber_max` | `--wavenumber-max` | `15` | Highest zonal wavenumber |
| `amplitude_threshold` | `--amplitude-threshold` | `25` | Phase-speed envelope threshold |
| `phase_speed_limit` | `--phase-speed-limit` | none | Absolute phase-speed mask |
| `group_velocity` | `--group-velocity` | on | Enable packet group velocity |
| `group_amplitude_threshold` | `--group-amplitude-threshold` | `20` | Group-velocity envelope threshold |
| `minimum_zonal_extent` | `--minimum-zonal-extent` | `20` | Minimum packet length in degrees |
| `minimum_meridional_extent` | `--minimum-meridional-extent` | `10` | Minimum packet width in degrees |
| `smoothing_sigma_degrees` | `--smoothing-sigma-degrees` | `4` | Gaussian sigma in degrees |
| `group_speed_limit` | `--group-speed-limit` | `100` | Absolute component mask in m s⁻¹ |
| `chunks_time` | `--chunks-time` | `32` | Input time chunk |
| `plot` | `--plot` | on | Create standard figures |
| `plot_time` | `--plot-time` | `midpoint` | Figure snapshot time |
| `dry_run` | `--dry-run` | off | Validate discovery without calculation |

Each scientific and execution setting has a matching
`ROSSBY_WAVE_PACKET_*` entry in `settings.jsonc` for framework runs.

## Python interface

```python
import xarray as xr

from src.rossby_wave_packet_core import run_rwp

source = xr.open_dataset("model_wind.nc", chunks={"time": 32})
result = run_rwp(
    source,
    level=250,
    latitude_min=25,
    latitude_max=85,
    wavenumber_min=4,
    wavenumber_max=15,
    amplitude_threshold=25,
    group_amplitude_threshold=20,
)
result.to_netcdf("rossby_wave_packet.nc")
```

## Preprocessing and record length

Use at least one complete year when `--anomaly-method harmonic` is selected,
because the annual cycle is estimated and removed from the supplied record. A
longer record generally gives a more representative seasonal climatology.

For a short record whose seasonal cycle is negligible, retain the zonal filter
but skip annual-cycle removal with `--anomaly-method none`. If the input is
already an anomaly filtered to the selected zonal wavenumbers, use
`--prefiltered-input` to start with amplitude and phase.

Phase-speed values are retained only where the derivative stencil meets the
amplitude threshold. Group velocity uses Gaussian-smoothed packet segments
that meet the amplitude and size thresholds. The first and last times are
undefined for centered group-velocity differences. Missing regions in speed
plots are therefore expected and should not be replaced by time-unioned masks.

## Six-panel example

Create the raw wind, filtered wind, envelope, phase speed, zonal group
velocity, and meridional group velocity panels from an existing diagnostic:

```bash
python plots/scripts/plot_rossby_wave_packet_snapshot.py \
  --input <model-wind.nc> \
  --diagnostic <rossby-wave-packet.nc> \
  --output plots/output/rossby_wave_packet_snapshot_6x1.png \
  --plot-time midpoint
```

This plotting command does not recompute the diagnostic and does not draw
vectors.

## Validation

Run the synthetic tests from the package directory:

```bash
python -m pytest -q
```

Before an upstream pull request, run at least one model case through the full
MDTF framework, build the Sphinx documentation, inspect the generated HTML and
NetCDF metadata, and compare a retained model case with the scientific method.

## Reference

Fragkoulidis, G., and V. Wirth, 2020: Local Rossby wave packet amplitude,
phase speed, and group velocity: Seasonal variability and their role in
temperature extremes. *Journal of Climate*, **33**, 8767–8787.
[doi:10.1175/JCLI-D-19-0377.1](https://doi.org/10.1175/JCLI-D-19-0377.1)
