#!/usr/bin/env python3
"""LWA-Based Blocking Detection and Classification diagnostic.

The driver accepts daily 500-hPa geopotential height from either an MDTF
ESM-intake catalog or a standalone NetCDF file. It calculates local wave
activity (LWA), tracks persistent events in both hemispheres, classifies them
as ridge, trough, or dipole blocks, and writes gridded event masks, event and
daily-track catalogs, and horizontal maps of detected blocks.

Version and contact
-------------------
* Version 1.2.0 (September 2026)
* Scientific PI: Lei Wang, wanglei@purdue.edu
* Developer and email: Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com

Open-source agreement
---------------------
This POD is intended for inclusion in MDTF-diagnostics, which is distributed
under the GNU Lesser General Public License v3.0 (see the framework's
``LICENSE.txt``).

Functionality
-------------
``compute_lwa.py`` selects and transforms model Z500 and calculates total,
anticyclonic, and cyclonic LWA in bounded time chunks. ``process_blocking.py``
detects, tracks, classifies, and records events. ``plot_block_maps.py`` writes
fixed-name PNG summaries for the MDTF web report and an optional PDF atlas.

Required software and model output
----------------------------------
Python >= 3.12 with NumPy, SciPy, pandas, xarray, netCDF4, matplotlib,
intake-esm, and PyYAML. Input is daily global geopotential height at 500 hPa
on a rectilinear latitude-longitude grid, requested through ``settings.jsonc``.

Scientific references
---------------------
Huang and Nakamura (2016), J. Atmos. Sci., doi:10.1175/JAS-D-15-0194.1;
Liu and Wang (2025), Nature Communications, doi:10.1038/s41467-025-60811-4.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import xarray as xr

# The plotting code is retained separately from the numerical implementation.
# Add its POD-relative location so the driver works regardless of the current
# working directory used by MDTF.
_PLOT_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "plots" / "scripts"
if str(_PLOT_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_PLOT_SCRIPT_DIR))

from compute_lwa import LWA_FLAGS, compute_one_lwa, find_coordinate, select_z500
from plot_block_maps import plot_event_atlas, plot_event_summary
from process_blocking import run_hemisphere


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = parser.add_argument_group("input and output")
    source.add_argument("--input", type=Path, help="Standalone NetCDF input; omit inside MDTF")
    source.add_argument("--catalog-file", type=Path, help="ESM-intake catalog JSON header")
    source.add_argument("--case-info", type=Path, help="MDTF case_info.yml; defaults to case_env_file")
    source.add_argument("--case", help="Only process catalog entries containing this label")
    source.add_argument("--frequency", default="day", help="Catalog frequency to search")
    source.add_argument("--output-dir", type=Path, help="Standalone output directory")
    source.add_argument("--output-prefix", default="lwa_block_detect", help="Output filename prefix")

    discovery = parser.add_argument_group("data discovery and selection")
    discovery.add_argument("--variable", help="Z500 variable name; inferred by default")
    discovery.add_argument("--time-name", help="Time coordinate name")
    discovery.add_argument("--latitude-name", help="Latitude coordinate name")
    discovery.add_argument("--longitude-name", help="Longitude coordinate name")
    discovery.add_argument("--level-name", help="Pressure coordinate name")
    discovery.add_argument("--level", type=float, default=500.0, help="Pressure level in hPa")
    discovery.add_argument("--start-date", help="First included date understood by xarray")
    discovery.add_argument("--end-date", help="Last included date understood by xarray")
    discovery.add_argument(
        "--input-kind", choices=("auto", "height", "geopotential"), default="auto",
        help="Interpret input as geopotential height (m) or geopotential (m2 s-2)",
    )

    calculation = parser.add_argument_group("diagnostic parameters")
    calculation.add_argument("--hemisphere", choices=("NH", "SH", "both"), default="both")
    calculation.add_argument("--duration", type=int, default=5, help="Minimum event duration in days")
    calculation.add_argument(
        "--threshold-method",
        choices=("percentile_max", "median_max", "absolute"),
        default="percentile_max",
        help="LWA contour selection; percentile_max is the recommended default",
    )
    calculation.add_argument(
        "--threshold-percentile", type=float, default=85.0,
        help="Percentile of meridional-maximum LWA used by percentile_max",
    )
    calculation.add_argument(
        "--threshold-value", type=float,
        help="Fixed LWA contour required when threshold-method is absolute",
    )
    calculation.add_argument("--chunk-days", type=int, default=366, help="LWA work-unit length")
    calculation.add_argument("--n-core", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    calculation.add_argument("--keep-lwa", action=argparse.BooleanOptionalAction, default=True)
    calculation.add_argument("--plot", action=argparse.BooleanOptionalAction, default=True)
    calculation.add_argument("--dry-run", action="store_true", help="Discover and validate input only")
    return parser


def _safe_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_") or "case"


def _sort_coordinate_if_needed(da: xr.DataArray, name: str) -> xr.DataArray:
    """Keep already ordered coordinates sliceable without advanced indexing."""
    values = np.asarray(da[name].values)
    if values.ndim != 1 or len(values) != len(np.unique(values)):
        raise ValueError(f"{name} must be a unique one-dimensional coordinate")
    if len(values) < 2 or np.all(values[1:] > values[:-1]):
        return da
    if np.all(values[1:] < values[:-1]):
        return da.isel({name: slice(None, None, -1)})
    return da.isel({name: np.argsort(values)})


def _environment_defaults(args: argparse.Namespace) -> argparse.Namespace:
    casts = {
        "level": float, "duration": int, "chunk_days": int, "n_core": int,
        "threshold_percentile": float, "threshold_value": float,
    }
    for name in (
        "variable", "time_name", "latitude_name", "longitude_name", "level_name", "level",
        "start_date", "end_date", "input_kind", "hemisphere", "duration", "chunk_days", "n_core",
        "threshold_method", "threshold_percentile", "threshold_value",
    ):
        key = f"LWA_BLOCK_DETECT_{name.upper()}"
        if key in os.environ:
            setattr(args, name, casts.get(name, str)(os.environ[key]))
    for name in ("keep_lwa", "plot"):
        key = f"LWA_BLOCK_DETECT_{name.upper()}"
        if key in os.environ:
            setattr(args, name, os.environ[key].lower() in {"1", "true", "yes", "on"})
    return args


def _time_decode_kwargs() -> dict:
    """Use cftime without emitting xarray's post-2025 deprecation warning."""
    try:
        return {"decode_times": xr.coders.CFDatetimeCoder(use_cftime=True)}
    except AttributeError:
        return {"decode_times": True, "use_cftime": True}


def _open_catalog(args: argparse.Namespace) -> tuple[list[tuple[str, xr.Dataset]], object]:
    import intake
    import yaml

    case_path = args.case_info or (Path(os.environ["case_env_file"]) if "case_env_file" in os.environ else None)
    case_info = {}
    if case_path:
        with case_path.open(encoding="utf-8") as stream:
            case_info = yaml.safe_load(stream) or {}
    catalog_file = args.catalog_file or case_info.get("CATALOG_FILE")
    if not catalog_file:
        raise ValueError("No input supplied. Set --input, --catalog-file, or case_env_file")
    case_list = case_info.get("CASE_LIST", {})
    variable_ids = [case.get("zg500_var") for case in case_list.values() if case.get("zg500_var")]
    variable_id = args.variable or (variable_ids[0] if variable_ids else None)
    catalog = intake.open_esm_datastore(str(catalog_file))
    search = {"frequency": args.frequency}
    if variable_id:
        search["variable_id"] = variable_id
    subset = catalog.search(**search)
    if subset.df.empty and variable_id:
        # A no-preprocessing catalog may identify the requested field by CF
        # standard name but retain a model-native variable_id.
        subset = catalog.search(
            standard_name="geopotential_height", frequency=args.frequency
        )
    datasets = subset.to_dataset_dict(
        xarray_open_kwargs=_time_decode_kwargs()
    )
    case_names = list(case_list)
    selected = []
    for key, ds in datasets.items():
        label = key
        if len(case_names) == 1:
            label = case_names[0]
        elif case_names:
            searchable = " ".join(
                [key, str(ds.attrs.get("intake_esm_attrs:path", "")), str(ds.encoding.get("source", ""))]
            )
            matches = [name for name in case_names if name in searchable]
            if len(matches) == 1:
                label = matches[0]
        if not args.case or args.case in label or args.case in key:
            selected.append((label, ds))
    if not selected:
        raise ValueError("The ESM-intake search returned no matching datasets")
    return selected, catalog


def _open_legacy_mdtf_file(args: argparse.Namespace) -> list[tuple[str, xr.Dataset]] | None:
    """Open the v3-compatible file environment variable when no catalog exists."""
    path = os.environ.get("ZG500_FILE") or os.environ.get("ZG_FILE")
    if not path:
        return None
    label = os.environ.get("CASENAME", Path(path).stem)
    if args.variable is None:
        args.variable = os.environ.get("zg500_var") or os.environ.get("zg_var")
    return [(label, xr.open_dataset(path, **_time_decode_kwargs()))]


def _validate_daily_time(time: xr.DataArray) -> None:
    """Reject duplicate, missing, or subdaily records before event tracking."""
    values = np.asarray(time.values)
    if values.size < 2:
        return
    deltas = np.diff(values)
    days = []
    for delta in deltas:
        if isinstance(delta, np.timedelta64):
            days.append(float(delta / np.timedelta64(1, "D")))
        elif hasattr(delta, "total_seconds"):
            days.append(float(delta.total_seconds() / 86400.0))
        else:
            # Numeric time coordinates are accepted only when one unit is one day.
            days.append(float(delta))
    if not np.allclose(days, 1.0, rtol=0.0, atol=1.0e-6):
        first_bad = int(np.flatnonzero(~np.isclose(days, 1.0, rtol=0.0, atol=1.0e-6))[0])
        raise ValueError(
            "Blocking tracking requires consecutive daily means; "
            f"time interval {first_bad}->{first_bad + 1} is {days[first_bad]:g} days"
        )


def _prepare_height(dataset: xr.Dataset, args: argparse.Namespace, load: bool = False) -> xr.DataArray:
    lat_name = find_coordinate(dataset, "latitude", args.latitude_name)
    lon_name = find_coordinate(dataset, "longitude", args.longitude_name)
    time_name = find_coordinate(dataset, "time", args.time_name)
    da = select_z500(dataset, args.variable, args.level_name, args.level)
    da = da.rename({lat_name: "lat", lon_name: "lon", time_name: "time"})
    if set(da.dims) != {"time", "lat", "lon"}:
        raise ValueError(f"Selected Z500 dimensions must resolve to time, latitude, longitude; got {da.dims}")
    for name in ("time", "lat", "lon"):
        da = _sort_coordinate_if_needed(da, name)
    if da.sizes["lat"] < 5 or da.sizes["lon"] < 8:
        raise ValueError("The LWA calculation requires at least 5 latitudes and 8 longitudes")
    lon = np.asarray(da.lon.values, dtype=float)
    if lon.size > 2 and np.isclose((lon[-1] - lon[0]), 360.0):
        da = da.isel(lon=slice(0, -1))
        lon = np.asarray(da.lon.values, dtype=float)
    cyclic_gaps = np.concatenate([np.diff(lon), [360.0 - (lon[-1] - lon[0])]])
    if np.any(cyclic_gaps <= 0.0) or not np.isclose(cyclic_gaps.sum(), 360.0):
        raise ValueError("Longitude must be monotonic and cover one complete, nonduplicated cycle")
    if np.max(cyclic_gaps) > 4.0 * np.median(cyclic_gaps):
        raise ValueError("Longitude has a gap too large for cyclic blocking detection")
    if float(da.lat.min()) > -85.0 or float(da.lat.max()) < 85.0:
        raise ValueError("The equivalent-latitude calculation requires a global grid reaching both poles")
    if args.start_date or args.end_date:
        da = da.sel(time=slice(args.start_date, args.end_date))
    if da.sizes.get("time", 0) < args.duration:
        raise ValueError(f"At least {args.duration} daily records are required")
    _validate_daily_time(da.time)
    units = str(da.attrs.get("units", "")).lower().replace("**", "^").replace(" ", "")
    geopotential_units = "s-2" in units or "s^-2" in units or "m2" in units or "m^2" in units
    inferred_from_magnitude = False
    if args.input_kind == "auto" and not units:
        sample = np.asarray(da.isel(time=0).values)
        finite = np.abs(sample[np.isfinite(sample)])
        geopotential_units = bool(finite.size and np.nanmedian(finite) > 20000.0)
        inferred_from_magnitude = True
    if args.input_kind == "geopotential" or (args.input_kind == "auto" and geopotential_units):
        da = da / np.float32(9.80665)
    da.attrs.update({"standard_name": "geopotential_height", "units": "m"})
    if inferred_from_magnitude:
        da.attrs["input_kind_inference"] = "magnitude fallback used because input units were missing"
    da = da.astype(np.float32)
    if load:
        da = da.load()
    return da.transpose("time", "lat", "lon")


def _publish_netcdf(result: dict, target: Path, case: str) -> None:
    with xr.open_dataset(result["grid_path"]) as source:
        output = source.load()
    output.attrs.update({
        "title": "LWA-Based Blocking Detection and Classification",
        "Conventions": "CF-1.8",
        "case": case,
        "hemisphere": result["hemisphere"],
        "lwa_threshold": result["threshold"],
        "lwa_threshold_method": result["threshold_method"],
        "lwa_threshold_percentile": result["threshold_percentile"],
        "event_catalog": f"../events/{result['hemisphere']}/{Path(result['events_path']).name}",
        "track_catalog": f"../events/{result['hemisphere']}/{Path(result['tracks_path']).name}",
        "references": (
            "Huang and Nakamura (2016), doi:10.1175/JAS-D-15-0194.1; "
            "Liu and Wang (2025), doi:10.1038/s41467-025-60811-4"
        ),
        "ridge_events": result["event_counts"]["ridge"],
        "trough_events": result["event_counts"]["trough"],
        "dipole_events": result["event_counts"]["dipole"],
    })
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_netcdf(target)


def _run_case(dataset: xr.Dataset, label: str, args: argparse.Namespace, model_dir: Path, multi: bool) -> dict:
    safe = _safe_label(label)
    da = _prepare_height(dataset, args, load=False)
    print(f"Input {label}: {da.sizes}, units={da.attrs.get('units')}")
    if args.dry_run:
        return {"label": label, "relative_root": None, "hemispheres": []}
    case_root = model_dir / safe if multi else model_dir
    lwa_dir = case_root / "netCDF" / "lwa"
    for suffix, flag in LWA_FLAGS.items():
        compute_one_lwa(
            da, lwa_dir / f"LWA_Z500_{suffix}.nc", flag, "lat", "lon", "time",
            args.chunk_days, max(1, args.n_core), f"Z500 LWA for {label}; component={suffix}",
        )
    hemispheres = ("NH", "SH") if args.hemisphere == "both" else (args.hemisphere,)
    case_results = []
    for hemisphere in hemispheres:
        detail_dir = case_root / "events" / hemisphere
        result = run_hemisphere(
            lwa_dir,
            detail_dir,
            hemisphere,
            args.duration,
            args.threshold_method,
            args.threshold_percentile,
            args.threshold_value,
        )
        netcdf = case_root / "netCDF" / f"{args.output_prefix}_{hemisphere}.nc"
        _publish_netcdf(result, netcdf, label)
        total = sum(result["event_counts"].values())
        case_results.append({"hemisphere": hemisphere, "events": total})
        print(f"{label} {hemisphere}: {total} events; wrote {netcdf}")
        if args.plot:
            summary_plot = case_root / f"{args.output_prefix}_{hemisphere}.png"
            plot_event_summary(
                netcdf,
                lwa_dir / "LWA_Z500_TOT.nc",
                result["events_path"],
                summary_plot,
                max_events=6,
                z500=da,
            )
            plot = case_root / f"{args.output_prefix}_{hemisphere}_maps.pdf"
            plot_event_atlas(
                netcdf,
                lwa_dir / "LWA_Z500_TOT.nc",
                result["events_path"],
                plot,
                max_events=12,
                z500=da,
            )
            print(f"Wrote {summary_plot}")
            print(f"Wrote {plot}")
    if not args.keep_lwa:
        shutil.rmtree(lwa_dir)
    return {
        "label": label,
        "relative_root": safe if multi else ".",
        "hemispheres": case_results,
    }


def _write_case_index(model_dir: Path, results: list[dict], prefix: str, mdtf_mode: bool) -> None:
    """Write a runtime index because an MDTF catalog may contain many cases."""
    parts = [
        "<html><head><title>Blocking event results</title></head><body>",
        "<h3>LWA-Based Blocking Detection and Classification: model cases</h3>",
        "<p>Each panel shows the strongest detected events at peak intensity. "
        "The CSV catalogs contain the complete event and daily-track information.</p>",
    ]
    if mdtf_mode:
        parts.insert(1, '<img src="../mdtf_diag_banner.png" alt="MDTF Diagnostics">')
    for case in results:
        root = case["relative_root"]
        if root is None:
            continue
        parts.append(f"<h4>{html.escape(str(case['label']))}</h4><TABLE>")
        parts.append("<TR><TH align=left>Hemisphere<TH align=center>Map<TH align=center>Event data")
        for item in case["hemispheres"]:
            hemi = item["hemisphere"]
            base = "" if root == "." else f"{root}/"
            parts.append(
                f'<TR><TD>{hemi} ({item["events"]} events)'
                f'<TD><A href="{base}{prefix}_{hemi}.png">'
                f'<img src="{base}{prefix}_{hemi}.png" width="520" alt="{hemi} blocking maps"></A>'
                f'<TD><A href="{base}events/{hemi}/blocking_events_{hemi}.csv">events CSV</A><br>'
                f'<A href="{base}events/{hemi}/blocking_tracks_{hemi}.csv">daily tracks CSV</A><br>'
                f'<A href="{base}netCDF/{prefix}_{hemi}.nc">gridded NetCDF</A><br>'
                f'<A href="{base}{prefix}_{hemi}_maps.pdf">map atlas (PDF)</A>'
            )
        parts.append("</TABLE>")
    parts.append("</body></html>")
    (model_dir / f"{prefix}_cases.html").write_text("\n".join(parts), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.input is None:
        args = _environment_defaults(args)
    work_dir = Path(os.environ["WORK_DIR"]) if "WORK_DIR" in os.environ else None
    model_dir = work_dir / "model" if work_dir else (args.output_dir or Path("output"))
    model_dir.mkdir(parents=True, exist_ok=True)
    catalog = None
    if args.input:
        sources = [(args.input.stem, xr.open_dataset(args.input, decode_times=True))]
    else:
        legacy_sources = (
            _open_legacy_mdtf_file(args)
            if "case_env_file" not in os.environ and not args.catalog_file
            else None
        )
        if legacy_sources is not None:
            sources = legacy_sources
        else:
            sources, catalog = _open_catalog(args)
    try:
        if len(sources) > 1:
            safe_labels = [_safe_label(label) for label, _ in sources]
            if len(set(safe_labels)) != len(safe_labels):
                raise ValueError("Model case labels are not unique after filename sanitization")
        results = []
        for label, dataset in sources:
            results.append(_run_case(dataset, label, args, model_dir, len(sources) > 1))
        if not args.dry_run and args.plot:
            _write_case_index(model_dir, results, args.output_prefix, work_dir is not None)
    finally:
        for _, dataset in sources:
            dataset.close()
        if catalog is not None:
            catalog.close()
    print("Blocking diagnostic finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
