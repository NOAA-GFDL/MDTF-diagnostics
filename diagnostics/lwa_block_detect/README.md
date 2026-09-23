# LWA-Based Blocking Detection and Classification

`lwa_block_detect` identifies persistent atmospheric blocking events from
local finite-amplitude wave activity (LWA) derived directly from daily
500-hPa geopotential height (Z500). It calculates total, anticyclonic, and
cyclonic LWA; tracks connected regions through time; and classifies retained
events as ridge, trough, or dipole blocking.

The primary products are event catalogs, daily tracks, gridded event masks,
and horizontal maps at peak intensity. The POD does not calculate annual or
seasonal blocking statistics.

- Scientific PI: Lei Wang, wanglei@purdue.edu
- Developer: Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com
- Version: 1.2.0, September 2026

## Required model output

| Property | Requirement |
|---|---|
| Variable | Geopotential height (`geopotential_height`) |
| Units | `m` |
| Frequency | Daily mean |
| Level | 500 hPa |
| Realm | Atmosphere |
| Dimensions | Time, latitude, and longitude |
| Grid | Global rectilinear latitude-longitude grid reaching both poles |

In an MDTF run, the framework requests the internal variable `zg500`. The
preprocessor can extract 500 hPa from a four-dimensional pressure-level `zg`
field or translate a native three-dimensional Z500 field before the driver
runs.

The standalone reader accepts arbitrary dimension order, ascending or
descending latitude, either common longitude convention, Pa or hPa pressure
coordinates, singleton extra dimensions, common model variable names, and
standard or nonstandard CF calendars. It accepts geopotential height or
geopotential when the units identify the quantity.

Longitude must cover one complete cycle, and latitude must reach both polar
regions. Regional domains, missing dates, subdaily records, duplicate
longitudes, curvilinear grids, staggered grids, unstructured meshes, and
unselected non-singleton ensemble dimensions are rejected.

## Method

Equivalent-latitude contours of Z500 define total, anticyclonic, and cyclonic
LWA for each day. For each model case and hemisphere, the default blocking
boundary is the 85th percentile over time and longitude of the meridional
maximum total LWA. This upper-tail threshold prevents ordinary wave activity
from joining distinct blocking cores into unrealistically broad regions while
retaining adaptation to the analyzed case.

Regions above the threshold are connected across the cyclic longitude
boundary and associated between consecutive days. A retained track must
remain poleward of 30 degrees, satisfy the displacement and width criteria,
and last at least five consecutive days by default.

Integrated anticyclonic and cyclonic LWA within the peak-date event mask
determine the event class:

- ridge: anticyclonic LWA exceeds ten times cyclonic LWA;
- trough: cyclonic LWA exceeds twice anticyclonic LWA;
- dipole: neither component meets the ridge or trough criterion.

## Quick start with a NetCDF file

From the `lwa_block_detect` directory, analyze one year in both hemispheres
with the default p85 threshold:

```bash
python src/lwa_block_detect.py \
  --input <model-daily-z500.nc> \
  --output-dir output \
  --start-date 2000-01-01 \
  --end-date 2000-12-31 \
  --hemisphere both \
  --threshold-method percentile_max \
  --threshold-percentile 85
```

Variable and coordinate names are inferred from CF metadata and common model
names. Supply them explicitly when the file is not self-describing:

```bash
python src/lwa_block_detect.py \
  --input <model-daily-z500.nc> \
  --output-dir output \
  --variable zg \
  --time-name time \
  --latitude-name latitude \
  --longitude-name longitude \
  --level-name plev \
  --level 500 \
  --input-kind auto
```

Use `--input-kind geopotential` when the source field is geopotential in
`m2 s-2`. Display every command-line option with:

```bash
python src/lwa_block_detect.py --help
```

## Detection controls

| Option | Default | Description |
|---|---:|---|
| `--hemisphere` | `both` | Analyze `NH`, `SH`, or both hemispheres |
| `--duration` | `5` | Minimum event duration in consecutive days |
| `--threshold-method` | `percentile_max` | Use `percentile_max`, `median_max`, or `absolute` |
| `--threshold-percentile` | `85` | Percentile used by `percentile_max` |
| `--threshold-value` | none | Fixed LWA contour used by `absolute` |
| `--chunk-days` | `366` | Number of days in each LWA calculation work unit |
| `--n-core` | `1` | Number of worker processes unless supplied by the scheduler |
| `--keep-lwa` | on | Retain component-LWA intermediates in a direct run |
| `--plot` | on | Create PNG summaries and PDF event atlases |
| `--dry-run` | off | Validate input discovery and selection without calculation |

The `median_max` method reproduces the threshold used by the original
implementation. The `absolute` method should be used only with a
scientifically calibrated `--threshold-value`.

## Running through MDTF

Install the directory as `diagnostics/lwa_block_detect` in the MDTF source
tree and include the POD in the runtime configuration:

```json
"pod_list": ["lwa_block_detect"]
```

Run MDTF from the framework source directory:

```bash
./mdtf -f <runtime-configuration.jsonc>
```

The runtime configuration supplies the model cases, dates, intake-ESM data
catalog, working directory, and output directory. MDTF preprocesses `zg500`,
writes case metadata, and invokes `src/lwa_block_detect.py`; users do not need
to select catalog rows or call the driver separately during a normal
framework run.

The framework defaults are defined by the `LWA_BLOCK_DETECT_*` entries in
`settings.jsonc`. Both hemispheres are analyzed in one invocation, with a
separate threshold and separate output products for each hemisphere.

## Output

In an MDTF run, products are written below `$WORK_DIR/model`. A standalone run
writes the same relative structure below `--output-dir`.

| Product | Contents |
|---|---|
| `netCDF/lwa_block_detect_<HEMISPHERE>.nc` | Daily `blocking_event_id` and `blocking_type` fields |
| `events/<HEMISPHERE>/blocking_events_<HEMISPHERE>.csv` | One row per retained event |
| `events/<HEMISPHERE>/blocking_tracks_<HEMISPHERE>.csv` | Daily position, intensity, width, and area along each track |
| `lwa_block_detect_<HEMISPHERE>.png` | Two-panel ridge and dipole summary |
| `lwa_block_detect_<HEMISPHERE>_maps.pdf` | Event map atlas |
| `lwa_block_detect_cases.html` | Case index linking figures and numerical products |

The event catalog reports start and end dates and positions, duration, mean
and peak position, peak date, circular longitude width, grid-cell and physical
area, mean and peak LWA, translation speed, component LWA sums, and event
class. `event_id` joins the event and track tables to the gridded mask.

In the maps, total LWA is shaded, Z500 is contoured, the blue line marks the
detected event boundary, and the star marks the peak location.

![Northern Hemisphere ridge and dipole examples](doc/lwa_block_detect_NH_example.png)

## Interpretation

The threshold is diagnosed independently for each model case and hemisphere,
so LWA strength and event counts are relative to the analyzed run. Threshold
and resolution sensitivity should be evaluated before comparing models with
substantially different grids. A one-year interval is useful for software and
cross-format testing but is too short to establish a blocking climatology.

The strongest-event panels provide examples and links into the event-level
products; they are not frequency climatologies. Use the event catalog for
selection, the track table for lifecycle analysis, and the gridded event ID
for composites with other model fields.

## Software requirements

The POD requires Python 3.12 or newer with NumPy, SciPy, pandas, xarray,
netCDF4, matplotlib, intake-ESM, and PyYAML. These packages are available in
the standard MDTF Python environment. The POD requires no separate Conda
environment, observational dataset, or network access.

## Package contents

- `src/lwa_block_detect.py`: main MDTF and standalone driver.
- `src/compute_lwa.py` and `src/lwa_z500.py`: input normalization and
  Z500-based LWA calculation.
- `src/process_blocking.py`: event detection, tracking, classification, and
  numerical output.
- `plots/scripts/plot_block_maps.py`: summary and event-atlas plotting.
- `doc/lwa_block_detect.rst`: Diagnostics Reference source.
- `settings.jsonc`: MDTF variable request, dependencies, and defaults.
- `lwa_block_detect.html`: MDTF results-page template.

Generated NetCDF, CSV, PNG, and PDF products should be written to the MDTF
working directory, `output/`, or another data workspace rather than committed
to the source tree.

## References

- Chen, G., J. Lu, D. A. Burrows, and L. R. Leung, 2015: Local
  finite-amplitude wave activity as an objective diagnostic of midlatitude
  extreme weather. *Geophysical Research Letters*, **42**, 10,952–10,960.
  [doi:10.1002/2015GL066959](https://doi.org/10.1002/2015GL066959)
- Huang, C. S. Y., and N. Nakamura, 2016: Local finite-amplitude wave activity
  as a diagnostic of anomalous weather events. *Journal of the Atmospheric
  Sciences*, **73**, 211–229.
  [doi:10.1175/JAS-D-15-0194.1](https://doi.org/10.1175/JAS-D-15-0194.1)
- Liu, Z., and L. Wang, 2025: Blocking diversity causes distinct roles of
  diabatic heating in the Northern Hemisphere. *Nature Communications*,
  **16**, 5613.
  [doi:10.1038/s41467-025-60811-4](https://doi.org/10.1038/s41467-025-60811-4)
