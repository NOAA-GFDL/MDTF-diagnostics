# Rossby Wave Packet Diagnostics

`rossby_wave_packet` calculates Rossby wave packet envelope amplitude, wrapped
phase, phase speed, and zonal and meridional group velocity from six-hourly
model northward wind at 250 hPa. It can run as an MDTF process-oriented
diagnostic (POD), as a command-line program on a NetCDF file, or as one Python
function.

- Scientific PI: Lei Wang, wanglei@purdue.edu
- Developer: Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com
- Version: 1.2.0, September 2026

## Required input

| Property | Requirement |
|---|---|
| Variable | Northward wind (`northward_wind`) |
| Units | `m s-1` |
| Frequency | Six-hourly |
| Level | 250 hPa |
| Grid | Regular, rectilinear latitude-longitude grid with global longitude coverage |
| Time | Monotonic and uniformly spaced |

Latitude may increase or decrease. Longitude may use either 0–360° or
−180–180°, with or without a repeated cyclic endpoint. Standard/Gregorian,
proleptic Gregorian, Julian, 365-day, 366-day, and 360-day calendars are
supported.

The input may contain a pressure dimension, or it may already contain only the
250-hPa field. Use `--level none` for single-level data. Curvilinear,
cubed-sphere, and regional grids must be regridded before running the
diagnostic.

## Quick start with a NetCDF file

Run the command from the `rossby_wave_packet` directory:

```bash
python src/rossby_wave_packet.py \
  --input <model-wind.nc> \
  --output-dir output \
  --start-date 1980-01-01 \
  --end-date 1980-12-31
```

The start and end dates are inclusive. For six-hourly input,
`--end-date 1980-12-31` includes all available records on December 31.

Variable and coordinate names are inferred from CF metadata and common model
names. Supply them explicitly when the file is not self-describing:

```bash
python src/rossby_wave_packet.py \
  --input <model-wind.nc> \
  --output-dir output \
  --variable V \
  --time-name Time \
  --latitude-name latitude \
  --longitude-name longitude \
  --level-name lev_p \
  --level 250
```

For data already reduced to 250 hPa:

```bash
python src/rossby_wave_packet.py \
  --input <model-v250.nc> \
  --output-dir output \
  --level none
```

## Preprocessing choices

The default calculation estimates and removes the annual cycle, then retains
zonal wavenumbers 4–15. Use at least one complete year of data for this mode.
A longer record generally gives a more representative seasonal climatology.

| Input condition | Option | Processing performed |
|---|---|---|
| At least one complete year | `--anomaly-method harmonic` | Removes the fitted annual cycle, then applies the zonal filter |
| Short record with negligible seasonal change | `--anomaly-method none` | Skips annual-cycle removal but still applies the zonal filter |
| Filtered anomaly supplied by the user | `--prefiltered-input` | Skips annual-cycle removal and zonal filtering |

Example for a short record:

```bash
python src/rossby_wave_packet.py \
  --input <short-model-wind.nc> \
  --output-dir output \
  --anomaly-method none
```

Example for an existing filtered anomaly:

```bash
python src/rossby_wave_packet.py \
  --input <filtered-v250.nc> \
  --output-dir output \
  --prefiltered-input \
  --level none
```

## Parameters and command help

Display the command generated from the driver’s help dictionary:

```bash
python src/rossby_wave_packet.py --help
```

The driver exposes the same descriptions through `DRIVER_HELP`:

```python
from src.rossby_wave_packet import DRIVER_HELP

print(DRIVER_HELP["amplitude_threshold"])
```

All command options are listed below.

| Option | Default | Description |
|---|---:|---|
| `--input` | none | NetCDF input for a direct run |
| `--catalog-file` | case metadata | Intake-ESM catalog header for framework use |
| `--case-info` | `case_env_file` | MDTF case-information file |
| `--case` | all selected cases | Process one named MDTF case |
| `--frequency` | `6hr` | Frequency used by catalog-only discovery |
| `--output-dir` | `output` | Output directory for a direct run |
| `--output-prefix` | `rossby_wave_packet` | Prefix for NetCDF and figure names |
| `--variable` | inferred | Wind variable name |
| `--time-name` | inferred | Time coordinate name |
| `--latitude-name` | inferred | Latitude coordinate name |
| `--longitude-name` | inferred | Longitude coordinate name |
| `--level-name` | inferred | Pressure coordinate name |
| `--level` | `250` | Pressure in hPa; use `none` for single-level input |
| `--latitude-min` | `25` | Southern latitude bound in degrees north |
| `--latitude-max` | `85` | Northern latitude bound in degrees north |
| `--start-date` | first record | First included date or datetime |
| `--end-date` | last record | Last included date or datetime |
| `--prefiltered-input` | off | Treat the input as a filtered anomaly |
| `--anomaly-method` | `harmonic` | `harmonic`, `time_mean`, or `none` |
| `--annual-harmonics` | `4` | Highest harmonic in the fitted annual cycle |
| `--wavenumber-min` | `4` | Lowest retained zonal wavenumber |
| `--wavenumber-max` | `15` | Highest retained zonal wavenumber |
| `--amplitude-threshold` | `25` | Envelope threshold for phase speed in `m s-1` |
| `--phase-speed-limit` | none | Optional absolute phase-speed limit in `m s-1` |
| `--group-velocity` | on | Calculate group velocity; disable with `--no-group-velocity` |
| `--group-amplitude-threshold` | `20` | Envelope threshold for group velocity in `m s-1` |
| `--minimum-zonal-extent` | `20` | Minimum zonal packet extent in degrees |
| `--minimum-meridional-extent` | `10` | Minimum meridional packet extent in degrees |
| `--smoothing-sigma-degrees` | `4` | Gaussian envelope smoothing scale in degrees |
| `--group-speed-limit` | `100` | Absolute limit for each group-velocity component in `m s-1` |
| `--chunks-time` | `32` | Input time chunk; `0` disables Dask chunking |
| `--plot` | on | Create summary figures; disable with `--no-plot` |
| `--plot-time` | `midpoint` | Figure time: `midpoint` or a date/datetime |
| `--dry-run` | off | Check input discovery and selection without calculating the diagnostic |

For an MDTF run, the corresponding defaults are defined by the
`ROSSBY_WAVE_PACKET_*` entries in `settings.jsonc`.

## Output

A direct run writes the following products to `--output-dir`:

| Product | Contents |
|---|---|
| `rossby_wave_packet.nc` | Filtered wind, envelope, phase, phase speed, and group-velocity components |
| `rossby_wave_packet_output_manifest.csv` | Input label, NetCDF filename, and plotted time |
| `rossby_wave_packet_amplitude.png` | Time-mean envelope amplitude |
| `rossby_wave_packet_phase.png` | Wrapped phase at `--plot-time` |
| `rossby_wave_packet_phase_speed.png` | Phase speed at `--plot-time` |
| `rossby_wave_packet_group_velocity.png` | Group-speed magnitude and velocity components at `--plot-time` |

For an MDTF run, the NetCDF products are placed in `$WORK_DIR/model/netCDF`
and the figures in `$WORK_DIR/model`. When several cases are selected, each
case receives a separate NetCDF file and one panel in each summary figure.

### Why speed plots contain blank regions

Phase speed is retained only where the envelope exceeds
`--amplitude-threshold` over the full derivative stencil. Group velocity is
retained only for packet segments that satisfy the group-amplitude and spatial
extent thresholds. Group velocity is undefined at the first and last times
because it uses centered time differences. Values exceeding the configured
speed limits are also masked. Blank regions therefore indicate that the
calculation did not meet its validity criteria; they are not missing plotting
colors.

## Six-panel snapshot

The packaged plotting script draws raw wind, filtered wind, envelope, phase
speed, zonal group velocity, and meridional group velocity from an existing
diagnostic file. It does not rerun the calculation and does not draw vectors.

```bash
python plots/scripts/plot_rossby_wave_packet_snapshot.py \
  --input <model-wind.nc> \
  --diagnostic <rossby-wave-packet.nc> \
  --output plots/output/rossby_wave_packet_snapshot_6x1.png \
  --plot-time midpoint
```

## Python interface

`run_rwp` performs the complete calculation and returns an `xarray.Dataset`:

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

Pass either keyword options as above or an `RWPConfig` object, but not both.

## Running through MDTF

Install this directory as `diagnostics/rossby_wave_packet` in the MDTF source
tree and add the POD name to the runtime configuration:

```json
"pod_list": ["rossby_wave_packet"]
```

Run MDTF from the framework source directory:

```bash
python mdtf_framework.py -f <runtime-configuration.jsonc>
```

MDTF prepares six-hourly northward wind at 250 hPa for each case named in the
runtime configuration. The POD then analyzes those prepared fields. Users do
not need to select catalog rows or call the driver separately during a normal
framework run.

The framework environment supplies NumPy, SciPy, xarray, netCDF4, cftime,
Dask, matplotlib, Intake-ESM, and PyYAML. These libraries are also required
for direct command-line use.

## Package contents

- `src/`: driver and scientific calculations.
- `plots/scripts/`: standard and six-panel plotting programs.
- `plots/output/`: retained example figure.
- `doc/rossby_wave_packet.rst`: Diagnostics Reference source.
- `settings.jsonc`: MDTF data request and defaults.
- `rossby_wave_packet.html`: MDTF results-page template.
- `rossby_wave_packet_runtime_config_template.yml`: runtime example.
- `tests/`: synthetic software tests.

Generated NetCDF files and figures from scientific runs should be written to
`output/` or another data workspace.

## Reference

Fragkoulidis, G., and V. Wirth, 2020: Local Rossby wave packet amplitude,
phase speed, and group velocity: Seasonal variability and their role in
temperature extremes. *Journal of Climate*, **33**, 8767–8787.
[doi:10.1175/JCLI-D-19-0377.1](https://doi.org/10.1175/JCLI-D-19-0377.1)
