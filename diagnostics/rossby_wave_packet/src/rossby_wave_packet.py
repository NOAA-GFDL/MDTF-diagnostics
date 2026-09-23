#!/usr/bin/env python3
"""Rossby Wave Packet (RWP) diagnostic driver.

Synopsis
--------
This MDTF process-oriented diagnostic calculates the local envelope amplitude,
phase, phase speed, and horizontal group velocity of midlatitude Rossby wave
packets from six-hourly model northward wind at 250 hPa. The driver also has a
standalone NetCDF interface for development and scientific reuse.

Version and contact
-------------------
* Version 1.2.0 (September 2026)
* Scientific PI: Lei Wang, wanglei@purdue.edu
* Developer and email: Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com

License
-------
This file is distributed under the LGPLv3 license used by MDTF-diagnostics.

Functionality
-------------
Within MDTF, the driver reads ``case_env_file`` and uses Intake-ESM to open the
framework-produced model file associated with each case. It honors the native
variable, coordinate, calendar, and date metadata supplied for that case. The
scientific calculation removes a configurable background, applies a zonal
wavenumber filter, forms the analytic signal, and applies the packet-tracking
group-velocity method documented in the POD reference page.

Requirements
------------
Python 3.12 or newer with NumPy, SciPy, xarray, netCDF4, matplotlib, Dask,
Intake-ESM, and PyYAML. These are provided by MDTF's ``python3_base``
environment.

Required model variable
-----------------------
Six-hourly northward wind (CF ``northward_wind``; ``m s-1``) at 250 hPa on a
regular, global latitude-longitude grid.

Reference
---------
Fragkoulidis, G., and V. Wirth, 2020: Local Rossby wave packet amplitude,
phase speed, and group velocity: Seasonal variability and their role in
temperature extremes. Journal of Climate, 33, 8767-8787.
https://doi.org/10.1175/JCLI-D-19-0377.1
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import xarray as xr

try:
    from .rossby_wave_packet_core import RWPConfig, prepare_wind, run_rwp, write_netcdf
except ImportError:
    from rossby_wave_packet_core import RWPConfig, prepare_wind, run_rwp, write_netcdf

_POD_DIR = Path(__file__).resolve().parents[1]
_PLOT_SCRIPT_DIR = _POD_DIR / "plots" / "scripts"
if str(_PLOT_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_PLOT_SCRIPT_DIR))

from plot_rossby_wave_packet import summary_plots


DRIVER_HELP = {
    "input": "Standalone NetCDF input; omit inside MDTF",
    "catalog_file": "Intake-ESM catalog JSON header",
    "case_info": "MDTF case_info.yml; defaults to case_env_file",
    "case": "Only process the named MDTF case",
    "frequency": "Catalog frequency used by a catalog-only run",
    "output_dir": "Standalone output directory; defaults to output",
    "output_prefix": "Prefix for NetCDF and figure filenames",
    "variable": "Wind variable name; inferred from CF metadata by default",
    "time_name": "Time coordinate name",
    "latitude_name": "Latitude coordinate name",
    "longitude_name": "Longitude coordinate name",
    "level_name": "Pressure coordinate name",
    "level": "Pressure level in hPa, or 'none' for single-level input",
    "latitude_min": "Southern latitude bound in degrees north",
    "latitude_max": "Northern latitude bound in degrees north",
    "start_date": "First included date understood by xarray",
    "end_date": "Last included date understood by xarray",
    "prefiltered_input": "Skip background removal and zonal filtering",
    "anomaly_method": "Background treatment before zonal filtering",
    "annual_harmonics": "Annual-cycle harmonics to retain",
    "wavenumber_min": "Lowest retained zonal wavenumber",
    "wavenumber_max": "Highest retained zonal wavenumber",
    "amplitude_threshold": "Envelope threshold for phase speed (m/s)",
    "phase_speed_limit": "Maximum absolute phase speed (m/s), or 'none'",
    "group_velocity": "Calculate group velocity; disable with --no-group-velocity",
    "group_amplitude_threshold": "Envelope threshold for group velocity (m/s)",
    "minimum_zonal_extent": "Minimum zonal packet length (degrees)",
    "minimum_meridional_extent": "Minimum meridional packet width (degrees)",
    "smoothing_sigma_degrees": "Envelope Gaussian smoothing sigma (degrees)",
    "group_speed_limit": "Maximum absolute group-velocity component (m/s)",
    "chunks_time": "NetCDF time chunk; 0 disables Dask chunks",
    "plot": "Create the four PNG summary figures; disable with --no-plot",
    "plot_time": "Snapshot time: 'midpoint' or a date/time",
    "dry_run": "Discover and validate input without calculations",
}


def _optional_float(value: str) -> float | None:
    return None if value.lower() in {"none", "auto"} else float(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate Rossby wave packet amplitude, phase, phase speed, and group velocity.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = parser.add_argument_group("input and output")
    source.add_argument("--input", type=Path, help=DRIVER_HELP["input"])
    source.add_argument("--catalog-file", type=Path, help=DRIVER_HELP["catalog_file"])
    source.add_argument("--case-info", type=Path, help=DRIVER_HELP["case_info"])
    source.add_argument("--case", help=DRIVER_HELP["case"])
    source.add_argument("--frequency", default="6hr", help=DRIVER_HELP["frequency"])
    source.add_argument("--output-dir", type=Path, help=DRIVER_HELP["output_dir"])
    source.add_argument(
        "--output-prefix", default="rossby_wave_packet", help=DRIVER_HELP["output_prefix"]
    )

    discovery = parser.add_argument_group("data discovery and selection")
    discovery.add_argument("--variable", help=DRIVER_HELP["variable"])
    discovery.add_argument("--time-name", help=DRIVER_HELP["time_name"])
    discovery.add_argument("--latitude-name", help=DRIVER_HELP["latitude_name"])
    discovery.add_argument("--longitude-name", help=DRIVER_HELP["longitude_name"])
    discovery.add_argument("--level-name", help=DRIVER_HELP["level_name"])
    discovery.add_argument("--level", type=_optional_float, default=250.0, help=DRIVER_HELP["level"])
    discovery.add_argument("--latitude-min", type=float, default=25.0, help=DRIVER_HELP["latitude_min"])
    discovery.add_argument("--latitude-max", type=float, default=85.0, help=DRIVER_HELP["latitude_max"])
    discovery.add_argument("--start-date", help=DRIVER_HELP["start_date"])
    discovery.add_argument("--end-date", help=DRIVER_HELP["end_date"])

    calculation = parser.add_argument_group("diagnostic parameters")
    calculation.add_argument(
        "--prefiltered-input", action=argparse.BooleanOptionalAction, default=False,
        help=DRIVER_HELP["prefiltered_input"],
    )
    calculation.add_argument(
        "--anomaly-method",
        choices=("harmonic", "time_mean", "none"),
        default="harmonic",
        help=DRIVER_HELP["anomaly_method"],
    )
    calculation.add_argument("--annual-harmonics", type=int, default=4, help=DRIVER_HELP["annual_harmonics"])
    calculation.add_argument("--wavenumber-min", type=int, default=4, help=DRIVER_HELP["wavenumber_min"])
    calculation.add_argument("--wavenumber-max", type=int, default=15, help=DRIVER_HELP["wavenumber_max"])
    calculation.add_argument("--amplitude-threshold", type=float, default=25.0, help=DRIVER_HELP["amplitude_threshold"])
    calculation.add_argument("--phase-speed-limit", type=_optional_float, default=None, help=DRIVER_HELP["phase_speed_limit"])
    calculation.add_argument(
        "--group-velocity", action=argparse.BooleanOptionalAction, default=True,
        help=DRIVER_HELP["group_velocity"],
    )
    calculation.add_argument("--group-amplitude-threshold", type=float, default=20.0, help=DRIVER_HELP["group_amplitude_threshold"])
    calculation.add_argument("--minimum-zonal-extent", type=float, default=20.0, help=DRIVER_HELP["minimum_zonal_extent"])
    calculation.add_argument("--minimum-meridional-extent", type=float, default=10.0, help=DRIVER_HELP["minimum_meridional_extent"])
    calculation.add_argument("--smoothing-sigma-degrees", type=float, default=4.0, help=DRIVER_HELP["smoothing_sigma_degrees"])
    calculation.add_argument("--group-speed-limit", type=float, default=100.0, help=DRIVER_HELP["group_speed_limit"])

    execution = parser.add_argument_group("execution and summary figures")
    execution.add_argument("--chunks-time", type=int, default=32, help=DRIVER_HELP["chunks_time"])
    execution.add_argument(
        "--plot", action=argparse.BooleanOptionalAction, default=True,
        help=DRIVER_HELP["plot"],
    )
    execution.add_argument(
        "--plot-time", default="midpoint",
        help=DRIVER_HELP["plot_time"],
    )
    execution.add_argument("--dry-run", action="store_true", help=DRIVER_HELP["dry_run"])
    return parser


def _environment_default(args: argparse.Namespace, name: str, cast=str) -> None:
    env_name = f"ROSSBY_WAVE_PACKET_{name.upper()}"
    if env_name in os.environ:
        setattr(args, name, cast(os.environ[env_name]))


def _as_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def _apply_mdtf_options(args: argparse.Namespace) -> argparse.Namespace:
    casts = {
        "level": _optional_float,
        "latitude_min": float,
        "latitude_max": float,
        "annual_harmonics": int,
        "wavenumber_min": int,
        "wavenumber_max": int,
        "amplitude_threshold": float,
        "phase_speed_limit": _optional_float,
        "group_amplitude_threshold": float,
        "minimum_zonal_extent": float,
        "minimum_meridional_extent": float,
        "smoothing_sigma_degrees": float,
        "group_speed_limit": float,
        "chunks_time": int,
    }
    names = (
        "variable", "time_name", "latitude_name", "longitude_name", "level_name", "level",
        "latitude_min", "latitude_max", "start_date", "end_date", "anomaly_method", "annual_harmonics",
        "wavenumber_min", "wavenumber_max", "amplitude_threshold", "phase_speed_limit",
        "group_amplitude_threshold", "minimum_zonal_extent", "minimum_meridional_extent",
        "smoothing_sigma_degrees", "group_speed_limit", "frequency", "chunks_time", "plot_time",
    )
    for name in names:
        _environment_default(args, name, casts.get(name, str))
    for name in ("prefiltered_input", "group_velocity", "plot"):
        _environment_default(args, name, _as_bool)
    return args


def _configuration(args: argparse.Namespace) -> RWPConfig:
    return RWPConfig(
        variable=args.variable,
        time_name=args.time_name,
        latitude_name=args.latitude_name,
        longitude_name=args.longitude_name,
        level_name=args.level_name,
        level=args.level,
        latitude_min=args.latitude_min,
        latitude_max=args.latitude_max,
        start_date=args.start_date,
        end_date=args.end_date,
        prefiltered_input=args.prefiltered_input,
        anomaly_method=args.anomaly_method,
        annual_harmonics=args.annual_harmonics,
        wavenumber_min=args.wavenumber_min,
        wavenumber_max=args.wavenumber_max,
        amplitude_threshold=args.amplitude_threshold,
        phase_speed_limit=args.phase_speed_limit,
        compute_group_velocity=args.group_velocity,
        group_amplitude_threshold=args.group_amplitude_threshold,
        minimum_zonal_extent=args.minimum_zonal_extent,
        minimum_meridional_extent=args.minimum_meridional_extent,
        smoothing_sigma_degrees=args.smoothing_sigma_degrees,
        group_speed_limit=args.group_speed_limit,
    )


def _open_standalone(path: Path, chunks_time: int) -> list[tuple[str, xr.Dataset, dict[str, Any]]]:
    chunks = {} if chunks_time else None
    dataset = xr.open_dataset(path, decode_times=True, chunks=chunks)
    return [(path.stem, dataset, {})]


def _chunk_time(dataset: xr.Dataset, size: int) -> xr.Dataset:
    if not size:
        return dataset
    for name in dataset.dims:
        attrs = dataset[name].attrs if name in dataset.coords else {}
        if (
            name.lower() in {"time", "times", "date", "datetime", "t"}
            or str(attrs.get("axis", "")).upper() == "T"
            or attrs.get("standard_name") == "time"
        ):
            return dataset.chunk({name: size})
    return dataset


def _case_value(case: dict[str, Any], key: str) -> Any:
    """Return a case setting without depending on environment-variable case."""

    wanted = key.lower()
    for name, value in case.items():
        if str(name).lower() == wanted:
            return value
    return None


def _catalog_asset_column(catalog: Any) -> str:
    assets = getattr(catalog.esmcat, "assets", {})
    if hasattr(assets, "column_name"):
        return str(assets.column_name)
    if isinstance(assets, dict):
        return str(assets.get("column_name", "path"))
    return "path"


def _catalog_open_kwargs() -> dict[str, Any]:
    """Request calendar-aware decoding across supported xarray releases."""

    try:
        return {"decode_times": xr.coders.CFDatetimeCoder(use_cftime=True)}
    except AttributeError:
        return {"decode_times": True, "use_cftime": True}


def _open_catalog(args: argparse.Namespace) -> tuple[list[tuple[str, xr.Dataset, dict[str, Any]]], object]:
    """Open each MDTF case through its exact Intake-ESM catalog asset."""

    import intake
    import yaml

    case_path = args.case_info or (Path(os.environ["case_env_file"]) if "case_env_file" in os.environ else None)
    case_info: dict[str, Any] = {}
    if case_path:
        with case_path.open(encoding="utf-8") as stream:
            case_info = yaml.safe_load(stream) or {}
    catalog_file = args.catalog_file or case_info.get("CATALOG_FILE")
    if not catalog_file:
        raise ValueError("No input was supplied. Set --input, --catalog-file, or case_env_file")

    catalog = intake.open_esm_datastore(str(catalog_file))
    case_list = case_info.get("CASE_LIST", {})
    if not case_list:
        # This mode is useful for standalone catalog testing. It is not used by
        # MDTF, which always supplies CASE_LIST.
        search: dict[str, Any] = {"frequency": args.frequency}
        if args.variable:
            search["variable_id"] = args.variable
        dataset_dict = catalog.search(**search).to_dataset_dict(
            xarray_open_kwargs=_catalog_open_kwargs()
        )
        selected = [
            (key, dataset, {}) for key, dataset in dataset_dict.items()
            if not args.case or args.case == key or args.case in key
        ]
        if not selected:
            raise ValueError("The ESM-intake search returned no matching datasets")
        return selected, catalog

    asset_column = _catalog_asset_column(catalog)
    if asset_column not in catalog.df.columns:
        raise ValueError(f"The MDTF catalog has no asset column {asset_column!r}")

    selected: list[tuple[str, xr.Dataset, dict[str, Any]]] = []
    for case_name, case in case_list.items():
        if args.case and args.case != case_name:
            continue
        file_path = _case_value(case, "VA250_FILE")
        if not file_path:
            raise ValueError(f"MDTF case {case_name!r} did not provide VA250_FILE")

        requested = os.path.realpath(os.path.expandvars(str(file_path)))
        rows = catalog.df[catalog.df[asset_column].map(
            lambda value: os.path.realpath(os.path.expandvars(str(value))) == requested
        )]
        if rows.empty:
            raise ValueError(
                f"The processed file for MDTF case {case_name!r} is absent from CATALOG_FILE: {file_path}"
            )
        catalog_path = str(rows.iloc[0][asset_column])
        subset = catalog.search(**{asset_column: catalog_path})
        dataset_dict = subset.to_dataset_dict(
            xarray_open_kwargs=_catalog_open_kwargs()
        )
        if len(dataset_dict) != 1:
            keys = ", ".join(dataset_dict)
            raise ValueError(
                f"Expected one catalog dataset for case {case_name!r}, found {len(dataset_dict)}: {keys}"
            )
        selected.append((case_name, next(iter(dataset_dict.values())), dict(case)))

    if not selected:
        raise ValueError(f"No MDTF case matched --case={args.case!r}")
    return selected, catalog


def _safe_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_") or "case"


def _case_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value)
    match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})(?:(\d{2})(\d{2})(\d{2}))?", text)
    if not match:
        return text
    year, month, day, hour, minute, second = match.groups()
    date = f"{year}-{month}-{day}"
    return date if hour is None else f"{date}T{hour}:{minute}:{second}"


def _case_configuration(base: RWPConfig, args: argparse.Namespace, case: dict[str, Any]) -> RWPConfig:
    """Use MDTF-provided names and dates unless the caller explicitly overrides them."""

    return replace(
        base,
        variable=args.variable or _case_value(case, "va250_var") or base.variable,
        time_name=args.time_name or _case_value(case, "time_coord") or base.time_name,
        latitude_name=args.latitude_name or _case_value(case, "lat_coord") or base.latitude_name,
        longitude_name=args.longitude_name or _case_value(case, "lon_coord") or base.longitude_name,
        level_name=args.level_name or _case_value(case, "lev_coord") or base.level_name,
        start_date=args.start_date or _case_date(_case_value(case, "startdate")) or base.start_date,
        end_date=args.end_date or _case_date(_case_value(case, "enddate")) or base.end_date,
    )


def _phase_snapshot(result: xr.Dataset, plot_time: str) -> xr.DataArray:
    if plot_time.lower() == "midpoint":
        return result.phase.isel(time=result.sizes["time"] // 2).compute()
    sample = np.asarray(result.time.values).flat[0]
    if isinstance(sample, np.datetime64):
        target: Any = np.datetime64(plot_time)
    else:
        parsed = dt.datetime.fromisoformat(plot_time.replace("Z", "+00:00"))
        target = type(sample)(
            parsed.year, parsed.month, parsed.day,
            parsed.hour, parsed.minute, parsed.second,
        )
    return result.phase.sel(time=target, method="nearest").compute()


def _case_summary(result: xr.Dataset, label: str, plot_time: str) -> dict[str, Any]:
    phase = _phase_snapshot(result, plot_time)
    snapshot_time = phase.time
    summary: dict[str, Any] = {
        "label": label,
        "amplitude": result.amplitude.mean("time", skipna=True).compute(),
        "phase": phase,
        "phase_time": str(phase.time.values),
        # Keep the instantaneous threshold mask. A skip-na time mean would use
        # the union of all valid locations and make a sparse speed diagnostic
        # look nearly global.
        "phase_speed": result.phase_speed.sel(time=snapshot_time).compute(),
    }
    if "group_velocity_zonal" in result and "group_velocity_meridional" in result:
        summary["cgx"] = result.group_velocity_zonal.sel(time=snapshot_time).compute()
        summary["cgy"] = result.group_velocity_meridional.sel(time=snapshot_time).compute()
    return summary


def _write_manifest(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case", "netcdf_file", "phase_snapshot"))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.input is None:
        args = _apply_mdtf_options(args)
    base_config = _configuration(args)
    work_dir = Path(os.environ["WORK_DIR"]) if "WORK_DIR" in os.environ else None
    model_dir = work_dir / "model" if work_dir else (args.output_dir or Path("output"))
    netcdf_dir = model_dir / "netCDF" if work_dir else model_dir
    model_dir.mkdir(parents=True, exist_ok=True)
    netcdf_dir.mkdir(parents=True, exist_ok=True)

    catalog = None
    sources: list[tuple[str, xr.Dataset, dict[str, Any]]]
    if args.input:
        sources = _open_standalone(args.input, args.chunks_time)
    else:
        sources, catalog = _open_catalog(args)

    print("Rossby wave packet base configuration:")
    for key, value in asdict(base_config).items():
        print(f"  {key}: {value}")
    summaries: list[dict[str, Any]] = []
    manifest: list[dict[str, str]] = []
    try:
        for label, dataset, case in sources:
            config = _case_configuration(base_config, args, case)
            safe = _safe_label(label)
            print(f"Processing MDTF model case: {label}" if case else f"Processing input: {label}")
            dataset = _chunk_time(dataset, args.chunks_time)
            if args.dry_run:
                print(prepare_wind(dataset, config))
                continue
            result = run_rwp(dataset, config)
            result.attrs.update(case=label, diagnostic_version="1.2.0")
            suffix = f"_{safe}" if case or len(sources) > 1 else ""
            output = netcdf_dir / f"{args.output_prefix}{suffix}.nc"
            write_netcdf(result, output)
            print(f"Wrote {output}")
            summary = _case_summary(result, label, args.plot_time)
            summaries.append(summary)
            manifest.append(
                {"case": label, "netcdf_file": output.name, "phase_snapshot": summary["phase_time"]}
            )
            result.close()
        if manifest:
            manifest_path = netcdf_dir / f"{args.output_prefix}_output_manifest.csv"
            _write_manifest(manifest, manifest_path)
            print(f"Wrote {manifest_path}")
        if args.plot and summaries:
            for figure in summary_plots(summaries, model_dir, args.output_prefix):
                print(f"Wrote {figure}")
    finally:
        for _, dataset, _ in sources:
            dataset.close()
        if catalog is not None:
            catalog.close()
    print("Rossby wave packet diagnostic finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
