#!/usr/bin/env python3
"""Compute total, anticyclonic, and cyclonic Z500 LWA for one simulation file."""

from __future__ import annotations

import argparse
import os
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import xarray as xr
from netCDF4 import Dataset as NetCDFDataset

import lwa_z500


LWA_FLAGS = {
    "TOT": "all",
    "AC": "anticyclone",
    "C": "cyclone",
}

COORDINATE_ALIASES = {
    "time": ("time", "times", "date", "datetime", "t"),
    "latitude": ("lat", "latitude", "nav_lat", "y"),
    "longitude": ("lon", "longitude", "nav_lon", "x"),
    "pressure": ("plev", "lev_p", "level", "lev", "pressure", "isobaric", "isobaricinhpa"),
}

COORDINATE_STANDARD_NAMES = {
    "time": {"time"},
    "latitude": {"latitude"},
    "longitude": {"longitude"},
    "pressure": {"air_pressure"},
}

COORDINATE_AXES = {"time": "T", "latitude": "Y", "longitude": "X", "pressure": "Z"}


def _first_existing(names: list[str], candidates: tuple[str, ...], what: str) -> str:
    for candidate in candidates:
        if candidate in names:
            return candidate
    raise ValueError(f"Could not infer {what}. Available names: {names}")


def find_coordinate(ds: xr.Dataset, kind: str, explicit: str | None = None) -> str:
    """Find a one-dimensional coordinate from an explicit name or CF metadata."""
    if explicit:
        if explicit in ds.coords or explicit in ds.dims:
            return explicit
        matches = [name for name in set(ds.coords) | set(ds.dims) if name.lower() == explicit.lower()]
        if len(matches) == 1:
            return matches[0]
        raise ValueError(f"Requested {kind} coordinate {explicit!r} was not found")

    names = list(dict.fromkeys([*ds.coords, *ds.dims]))
    for name in names:
        attrs = ds[name].attrs if name in ds.variables else {}
        if str(attrs.get("standard_name", "")).lower() in COORDINATE_STANDARD_NAMES[kind]:
            return name
    for name in names:
        attrs = ds[name].attrs if name in ds.variables else {}
        if str(attrs.get("axis", "")).upper() == COORDINATE_AXES[kind]:
            return name
    for alias in COORDINATE_ALIASES[kind]:
        for name in names:
            if name.lower() == alias:
                return name
    raise ValueError(f"Could not infer {kind} coordinate. Available names: {names}")


def _find_z500_variable(ds: xr.Dataset, requested: str | None) -> str:
    if requested:
        if requested in ds.data_vars:
            return requested
        matches = [name for name in ds.data_vars if name.lower() == requested.lower()]
        if len(matches) == 1:
            return matches[0]
        raise ValueError(f"Requested variable {requested!r} was not found; data variables: {list(ds.data_vars)}")

    preferred_names = {"z500", "z", "zg", "hgt", "gh", "geopotential", "geopotential_height"}
    candidates = []
    for name, da in ds.data_vars.items():
        standard_name = str(da.attrs.get("standard_name", "")).lower()
        long_name = str(da.attrs.get("long_name", "")).lower()
        score = 0
        if name.lower() in preferred_names:
            score += 4
        if standard_name in {"geopotential", "geopotential_height"}:
            score += 5
        if "geopotential" in long_name or "500" in long_name and "height" in long_name:
            score += 2
        if da.ndim >= 3:
            score += 1
        if score:
            candidates.append((score, name))
    if not candidates:
        raise ValueError(f"Could not infer Z500 variable. Data variables: {list(ds.data_vars)}")
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        tied = [name for score, name in candidates if score == candidates[0][0]]
        raise ValueError(f"Ambiguous Z500 variables {tied}; select one with --variable")
    return candidates[0][1]


def _pressure_target(coordinate: xr.DataArray, level_hpa: float) -> float:
    units = str(coordinate.attrs.get("units", "")).lower().replace(" ", "")
    if units in {"pa", "pascal", "pascals"}:
        return level_hpa * 100.0
    if units in {"hpa", "mbar", "millibar", "millibars"}:
        return level_hpa
    values = np.asarray(coordinate.values, dtype=float)
    return level_hpa * 100.0 if np.nanmedian(np.abs(values)) > 2000 else level_hpa


def select_z500(
    ds: xr.Dataset,
    var_name: str | None,
    level_name: str | None,
    level_value: float,
) -> xr.DataArray:
    var_name = _find_z500_variable(ds, var_name)
    da = ds[var_name]
    if level_name is None:
        try:
            candidate = find_coordinate(ds, "pressure")
            if candidate in da.dims:
                level_name = candidate
        except ValueError:
            pass
    if level_name and level_name in da.dims:
        target = _pressure_target(ds[level_name], level_value)
        da = da.sel({level_name: target}, method="nearest")
        selected_level = float(da[level_name])
        if not np.isclose(selected_level, target, rtol=0.01, atol=0.0):
            raise ValueError(
                f"Nearest available pressure level is {selected_level:g}, "
                f"not the requested {level_value:g}-hPa target ({target:g} in coordinate units)"
            )
    da = da.squeeze(drop=True)
    if da.ndim != 3:
        raise ValueError(
            f"{var_name} has dimensions {da.dims} after pressure selection and singleton removal; "
            "select non-singleton ensemble or vertical dimensions before running the POD."
        )
    return da.astype(np.float32)


def _process_chunk(
    args: tuple[int, xr.DataArray, str, str, str, str, int],
) -> tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    start, da, lat_name, lon_name, time_name, flag, chunk_days = args
    chunk = da.isel({time_name: slice(start, start + chunk_days)}).load()
    lwa, lat, lon = lwa_z500.Cal(chunk, lat_name, lon_name, time_name, flag)
    return start, lwa.astype(np.float32), lat, lon


def compute_one_lwa(
    da: xr.DataArray,
    output_file: Path,
    flag: str,
    lat_name: str,
    lon_name: str,
    time_name: str,
    chunk_days: int,
    n_core: int,
    description: str,
) -> None:
    """Compute LWA by bounded chunks and write each chunk directly to NetCDF."""
    ndays = da.sizes[time_name]
    starts = list(range(0, ndays, chunk_days))
    lat = da[lat_name].values
    lon = da[lon_name].values
    # lwa_z500.Cal follows the original implementation and always returns its
    # latitude axis north-to-south, regardless of input order.
    output_lat = lat[::-1] if lat[0] < lat[-1] else lat

    args = [(start, da, lat_name, lon_name, time_name, flag, min(chunk_days, ndays - start)) for start in starts]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    skeleton = xr.Dataset(
        coords={"time": da[time_name].values, "lat": output_lat, "lon": lon},
        attrs={"description": description},
    )
    skeleton["lat"].attrs.update({"units": "degrees_north", "standard_name": "latitude"})
    skeleton["lon"].attrs.update({"units": "degrees_east", "standard_name": "longitude"})
    skeleton.to_netcdf(output_file)

    def write_results(results) -> None:
        with NetCDFDataset(output_file, "a") as nc:
            lwa_var = nc.createVariable(
                "LWA",
                "f4",
                ("time", "lat", "lon"),
                zlib=True,
                complevel=4,
                # Downstream detection and plotting commonly read one day at
                # a time; keep HDF5 chunks modest even when work chunks span a year.
                chunksizes=(1, len(lat), len(lon)),
                fill_value=np.float32(np.nan),
            )
            lwa_var.long_name = "local wave activity"
            for start, lwa_chunk, chunk_lat, chunk_lon in results:
                if not np.array_equal(chunk_lat, output_lat) or not np.array_equal(chunk_lon, lon):
                    raise ValueError("LWA chunk coordinates changed during calculation")
                lwa_var[start : start + lwa_chunk.shape[0], :, :] = lwa_chunk

    if n_core > 1 and len(args) > 1:
        with Pool(processes=min(n_core, len(args))) as pool:
            write_results(pool.imap_unordered(_process_chunk, args))
    else:
        write_results(_process_chunk(arg) for arg in args)
    print(f"Saved {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--sim-name", default=None)
    parser.add_argument("--var-name", default=None)
    parser.add_argument("--level-name", default=None)
    parser.add_argument("--level-value", type=float, default=500.0)
    parser.add_argument("--lat-name", default=None)
    parser.add_argument("--lon-name", default=None)
    parser.add_argument("--time-name", default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--chunk-days", type=int, default=366)
    parser.add_argument("--n-core", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    parser.add_argument("--no-divide-by-g", action="store_true")
    args = parser.parse_args()

    tic = time.time()
    sim_name = args.sim_name or args.input_file.stem
    ds = xr.open_dataset(args.input_file)
    try:
        lat_name = find_coordinate(ds, "latitude", args.lat_name)
        lon_name = find_coordinate(ds, "longitude", args.lon_name)
        time_name = find_coordinate(ds, "time", args.time_name)
        da = select_z500(ds, args.var_name, args.level_name, args.level_value)
        if not args.no_divide_by_g:
            da = da / np.float32(9.81)
            da.attrs["units"] = "m"
        da = da.rename({lat_name: "lat", lon_name: "lon", time_name: "time"})
        da = da.sortby("lat").sortby("lon")
        if args.start_date or args.end_date:
            da = da.sel(time=slice(args.start_date, args.end_date))
        for suffix, flag in LWA_FLAGS.items():
            output_file = args.output_dir / sim_name / "lwa" / f"LWA_Z500_{suffix}.nc"
            compute_one_lwa(
                da=da,
                output_file=output_file,
                flag=flag,
                lat_name="lat",
                lon_name="lon",
                time_name="time",
                chunk_days=args.chunk_days,
                n_core=max(1, args.n_core),
                description=f"Z500 LWA for {sim_name}; component={suffix}",
            )
    finally:
        ds.close()
    print(f"Finished LWA for {sim_name} in {time.time() - tic:.1f} s")


if __name__ == "__main__":
    main()
