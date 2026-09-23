#!/usr/bin/env python3
"""Plot six RWP fields at one time without recomputing the diagnostic."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr

_POD_DIR = Path(__file__).resolve().parents[2]
_SOURCE_DIR = _POD_DIR / "src"
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))

from rossby_wave_packet_core import RWPConfig, prepare_wind

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Raw model-wind NetCDF file")
    parser.add_argument("--diagnostic", type=Path, required=True, help="Existing RWP NetCDF result")
    parser.add_argument("--output", type=Path, default=Path("rossby_wave_packet_snapshot_6x1.png"))
    parser.add_argument("--plot-time", default="midpoint", help="midpoint or nearest date/time")
    parser.add_argument("--variable", help="Raw northward-wind variable name")
    parser.add_argument("--time-name", help="Raw time coordinate name")
    parser.add_argument("--latitude-name", help="Raw latitude coordinate name")
    parser.add_argument("--longitude-name", help="Raw longitude coordinate name")
    parser.add_argument("--level-name", help="Raw pressure coordinate name")
    parser.add_argument("--level", type=float, default=250.0, help="Pressure level in hPa")
    return parser


def _open_dataset(path: Path) -> xr.Dataset:
    try:
        coder = xr.coders.CFDatetimeCoder(use_cftime=True)
        return xr.open_dataset(path, decode_times=coder)
    except (AttributeError, TypeError):
        return xr.open_dataset(path, decode_times=True, use_cftime=True)


def _select_time(field: xr.DataArray, requested: str) -> xr.DataArray:
    if requested.lower() == "midpoint":
        return field.isel(time=field.sizes["time"] // 2)
    sample = np.asarray(field.time.values).flat[0]
    if isinstance(sample, np.datetime64):
        target: object = np.datetime64(requested)
    else:
        parsed = dt.datetime.fromisoformat(requested.replace("Z", "+00:00"))
        target = type(sample)(
            parsed.year,
            parsed.month,
            parsed.day,
            parsed.hour,
            parsed.minute,
            parsed.second,
        )
    return field.sel(time=target, method="nearest")


def _limits(field: xr.DataArray, positive: bool) -> tuple[float, float]:
    values = np.asarray(field.values)
    values = values[np.isfinite(values)]
    if not values.size:
        return (0.0, 1.0) if positive else (-1.0, 1.0)
    if positive:
        upper = float(np.nanpercentile(values, 98))
        return 0.0, upper if upper > 0 else 1.0
    bound = float(np.nanpercentile(np.abs(values), 98))
    return (-bound, bound) if bound > 0 else (-1.0, 1.0)


def plot_snapshot(
    raw_input: Path,
    diagnostic: Path,
    output: Path,
    plot_time: str = "midpoint",
    **coordinate_options: object,
) -> Path:
    """Create the requested six-panel snapshot from an existing RWP result."""

    with _open_dataset(diagnostic) as result, _open_dataset(raw_input) as source:
        phase_speed = _select_time(result["phase_speed"], plot_time).load()
        snapshot_time = phase_speed.time.values
        selected = {
            "Filtered v": result["filtered_wind"].sel(time=snapshot_time).load(),
            "Envelope": result["amplitude"].sel(time=snapshot_time).load(),
            "Phase speed": phase_speed,
            "Zonal group velocity": result["group_velocity_zonal"].sel(time=snapshot_time).load(),
            "Meridional group velocity": result["group_velocity_meridional"].sel(time=snapshot_time).load(),
        }
        config = RWPConfig(
            latitude_min=float(result.lat.min()),
            latitude_max=float(result.lat.max()),
            **coordinate_options,
        )
        raw = prepare_wind(source, config).sel(time=snapshot_time, method="nearest").load()

    panels = [
        ("Raw v", raw, False, "m s$^{-1}$"),
        ("Filtered v", selected["Filtered v"], False, "m s$^{-1}$"),
        ("Envelope", selected["Envelope"], True, "m s$^{-1}$"),
        ("Phase speed", selected["Phase speed"], False, "m s$^{-1}$"),
        ("Zonal group velocity", selected["Zonal group velocity"], False, "m s$^{-1}$"),
        ("Meridional group velocity", selected["Meridional group velocity"], False, "m s$^{-1}$"),
    ]
    stamp = str(snapshot_time)
    figure, axes = plt.subplots(6, 1, figsize=(13, 17), constrained_layout=True)
    for axis, (name, field, positive, units) in zip(axes, panels):
        vmin, vmax = _limits(field, positive)
        cmap = plt.get_cmap("RdBu_r").copy()
        cmap.set_bad("white")
        image = axis.pcolormesh(
            field.lon,
            field.lat,
            field,
            shading="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )
        axis.set_title(f"{name}. snapshot {stamp}")
        axis.set_xlabel("Longitude (degrees east)")
        axis.set_ylabel("Latitude (degrees north)")
        axis.set_xlim(float(field.lon.min()), float(field.lon.max()))
        figure.colorbar(image, ax=axis, pad=0.01, label=units)

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return output


def main() -> int:
    args = _parser().parse_args()
    target = plot_snapshot(
        args.input,
        args.diagnostic,
        args.output,
        args.plot_time,
        variable=args.variable,
        time_name=args.time_name,
        latitude_name=args.latitude_name,
        longitude_name=args.longitude_name,
        level_name=args.level_name,
        level=args.level,
    )
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
