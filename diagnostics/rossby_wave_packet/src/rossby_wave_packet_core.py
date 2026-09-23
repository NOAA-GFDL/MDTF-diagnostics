"""Core calculations for the Rossby wave packet diagnostic.

The public :func:`run_rwp` function is independent of the MDTF framework.  It
accepts an xarray Dataset or DataArray, discovers coordinate names from CF
metadata, and returns all diagnostic fields in one Dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr
from scipy.fft import fft, fftfreq, ifft
from scipy.signal import hilbert

try:
    from .rossby_wave_packet_group_velocity import tracked_group_velocity
except ImportError:
    from rossby_wave_packet_group_velocity import tracked_group_velocity


EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class RWPConfig:
    """Numerical and data-selection options for :func:`run_rwp`."""

    variable: str | None = None
    time_name: str | None = None
    latitude_name: str | None = None
    longitude_name: str | None = None
    level_name: str | None = None
    level: float | None = 250.0
    latitude_min: float = 25.0
    latitude_max: float = 85.0
    start_date: str | None = None
    end_date: str | None = None
    prefiltered_input: bool = False
    anomaly_method: str = "harmonic"
    annual_harmonics: int = 4
    wavenumber_min: int = 4
    wavenumber_max: int = 15
    amplitude_threshold: float = 25.0
    phase_speed_limit: float | None = None
    compute_group_velocity: bool = True
    group_amplitude_threshold: float = 20.0
    minimum_zonal_extent: float = 20.0
    minimum_meridional_extent: float = 10.0
    smoothing_sigma_degrees: float = 4.0
    group_speed_limit: float = 100.0


_COORD_ALIASES = {
    "time": ("time", "times", "date", "datetime", "t"),
    "latitude": ("lat", "latitude", "nav_lat", "y"),
    "longitude": ("lon", "longitude", "nav_lon", "x"),
    "level": (
        "lev",
        "lev_p",
        "level",
        "plev",
        "plev8",
        "pressure",
        "pressure_level",
        "isobaric",
        "isobaricinhpa",
    ),
}


def _find_coordinate(ds: xr.Dataset, kind: str, requested: str | None) -> str | None:
    if requested:
        if requested not in ds.coords and requested not in ds.dims:
            raise ValueError(f"Requested {kind} coordinate {requested!r} was not found")
        return requested

    standard_name = {"time": "time", "latitude": "latitude", "longitude": "longitude", "level": "air_pressure"}[kind]
    axis = {"time": "T", "latitude": "Y", "longitude": "X", "level": "Z"}[kind]
    candidates: list[str] = []
    for name in dict.fromkeys((*ds.coords, *ds.dims)):
        coord = ds[name]
        attrs = {str(k).lower(): str(v).lower() for k, v in coord.attrs.items()}
        score = 0
        if attrs.get("standard_name") == standard_name:
            score += 8
        if attrs.get("axis", "").upper() == axis:
            score += 4
        if name.lower() in _COORD_ALIASES[kind]:
            score += 2
        units = attrs.get("units", "")
        if kind == "latitude" and "degrees_north" in units:
            score += 2
        if kind == "longitude" and "degrees_east" in units:
            score += 2
        if kind == "time" and np.issubdtype(coord.dtype, np.datetime64):
            score += 2
        if score:
            candidates.append((score, name))
    if not candidates:
        return None
    return max(candidates)[1]


def _find_variable(ds: xr.Dataset, requested: str | None) -> str:
    if requested:
        if requested not in ds.data_vars:
            raise ValueError(f"Requested data variable {requested!r} was not found")
        return requested
    ranked: list[tuple[int, str]] = []
    aliases = {"v", "va", "vwind", "northward_wind", "meridional_wind"}
    for name, var in ds.data_vars.items():
        score = 0
        if str(var.attrs.get("standard_name", "")).lower() == "northward_wind":
            score += 10
        if name.lower() in aliases:
            score += 5
        if var.ndim >= 3:
            score += 1
        if score:
            ranked.append((score, name))
    if not ranked:
        available = ", ".join(ds.data_vars)
        raise ValueError(
            "Could not identify northward wind. Set variable explicitly; "
            f"available data variables are: {available}"
        )
    return max(ranked)[1]


def _pressure_target(coord: xr.DataArray, level_hpa: float) -> float:
    units = str(coord.attrs.get("units", "")).lower().replace(" ", "")
    if units in {"pa", "pascal", "pascals"} or float(np.nanmedian(np.abs(coord.values))) > 2_000:
        return level_hpa * 100.0
    return level_hpa


def prepare_wind(data: xr.Dataset | xr.DataArray, config: RWPConfig) -> xr.DataArray:
    """Discover, select, and normalize a northward-wind field."""

    ds = data.to_dataset(name=data.name or "northward_wind") if isinstance(data, xr.DataArray) else data
    variable = _find_variable(ds, config.variable)
    time_name = _find_coordinate(ds, "time", config.time_name)
    lat_name = _find_coordinate(ds, "latitude", config.latitude_name)
    lon_name = _find_coordinate(ds, "longitude", config.longitude_name)
    level_name = _find_coordinate(ds, "level", config.level_name)
    missing = [name for name, value in (("time", time_name), ("latitude", lat_name), ("longitude", lon_name)) if value is None]
    if missing:
        raise ValueError(f"Could not infer coordinate(s): {', '.join(missing)}")

    wind = ds[variable]
    if level_name and level_name in wind.dims:
        if config.level is None:
            if wind.sizes[level_name] != 1:
                raise ValueError("A multi-level input requires level to be set")
            wind = wind.isel({level_name: 0}, drop=True)
        else:
            target = _pressure_target(ds[level_name], config.level)
            wind = wind.sel({level_name: target}, method="nearest", drop=True)

    extra = [d for d in wind.dims if d not in {time_name, lat_name, lon_name}]
    for dim in extra:
        if wind.sizes[dim] != 1:
            raise ValueError(f"Unsupported non-singleton dimension {dim!r}; select it before calling run_rwp")
        wind = wind.isel({dim: 0}, drop=True)

    rename = {
        source: target
        for source, target in ((time_name, "time"), (lat_name, "lat"), (lon_name, "lon"))
        if source != target
    }
    if rename:
        wind = wind.rename(rename)
    if config.start_date or config.end_date:
        wind = wind.sel(time=slice(config.start_date, config.end_date))
    low, high = sorted((config.latitude_min, config.latitude_max))
    wind = wind.where((wind.lat >= low) & (wind.lat <= high), drop=True)
    if min(wind.sizes.get("time", 0), wind.sizes.get("lat", 0), wind.sizes.get("lon", 0)) < 3:
        raise ValueError("The selected field needs at least three time, latitude, and longitude points")

    lon = np.mod(np.asarray(wind.lon, dtype=float), 360.0)
    wind = wind.assign_coords(lon=("lon", lon)).sortby("lon").sortby("lat").sortby("time")
    _, unique = np.unique(np.round(wind.lon.values, 10), return_index=True)
    if len(unique) != wind.sizes["lon"]:
        wind = wind.isel(lon=np.sort(unique))
    spacing = np.diff(wind.lon.values)
    if not np.allclose(spacing, spacing.mean(), rtol=1e-5, atol=1e-6):
        raise ValueError("Longitude must be uniformly spaced for the zonal Fourier filter")
    circumference = spacing.mean() * wind.sizes["lon"]
    if not np.isclose(circumference, 360.0, rtol=1e-4, atol=1e-3):
        raise ValueError("Longitude must cover a complete 360-degree cyclic grid")
    wind = wind.transpose("time", "lat", "lon")
    wind.name = "northward_wind"
    wind.attrs.update({"standard_name": "northward_wind", "units": wind.attrs.get("units", "m s-1")})
    return wind


def _calendar_name(time: xr.DataArray) -> str:
    """Return a normalized CF calendar name for a decoded time coordinate."""

    calendar = str(time.encoding.get("calendar", time.attrs.get("calendar", ""))).lower()
    if calendar:
        return calendar
    values = np.asarray(time.values)
    if np.issubdtype(values.dtype, np.datetime64):
        return "proleptic_gregorian"
    return str(getattr(values.flat[0], "calendar", "standard")).lower()


def _cycle_index(time: xr.DataArray) -> tuple[xr.DataArray, int, int]:
    """Map each timestamp to a common climatological year."""

    values = np.asarray(time.values)
    deltas = np.diff(values)
    if np.issubdtype(deltas.dtype, np.timedelta64):
        hours = deltas / np.timedelta64(1, "h")
    else:
        hours = np.asarray([delta.total_seconds() / 3600.0 for delta in deltas], dtype=float)
    if np.any(hours <= 0):
        raise ValueError("Time must be strictly increasing")
    step_hours = float(np.min(hours))
    steps_per_day = int(round(24.0 / step_hours))
    multiples = hours / step_hours
    if not np.allclose(multiples, np.rint(multiples), rtol=1e-8, atol=1e-6):
        raise ValueError("Time gaps must be integer multiples of the base timestep")
    if not np.isclose(steps_per_day * step_hours, 24.0, atol=1e-6):
        raise ValueError("The harmonic annual cycle requires a timestep that divides 24 hours")

    calendar = _calendar_name(time)
    if calendar in {"360_day"}:
        days_per_year = 360
        adjusted_day = time.dt.dayofyear.astype(int)
    elif calendar in {"noleap", "365_day"}:
        days_per_year = 365
        adjusted_day = time.dt.dayofyear.astype(int)
    elif calendar in {"all_leap", "366_day"}:
        days_per_year = 366
        adjusted_day = time.dt.dayofyear.astype(int)
    elif calendar in {"standard", "gregorian", "proleptic_gregorian", "julian", ""}:
        days_per_year = 366
        year = time.dt.year.astype(int)
        if calendar == "julian":
            leap = year % 4 == 0
        else:
            leap = (year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0))
        adjusted_day = time.dt.dayofyear.astype(int) + ((~leap) & (time.dt.month > 2))
    else:
        raise ValueError(
            f"Calendar {calendar!r} is not supported by harmonic annual-cycle removal; "
            "use a CF Gregorian, Julian, 365-day, 366-day, or 360-day calendar, "
            "or select anomaly_method='time_mean' or 'none'"
        )

    seconds_of_day = (
        time.dt.hour.astype(float) * 3600.0
        + time.dt.minute.astype(float) * 60.0
        + time.dt.second.astype(float)
    )
    slot = xr.apply_ufunc(np.rint, seconds_of_day / (step_hours * 3600.0)).astype(int)
    index = ((adjusted_day - 1) * steps_per_day + slot).rename("cycle_step")
    return index, days_per_year, steps_per_day


def _retain_cycle_harmonics(values: np.ndarray, harmonics: int, steps_per_day: int) -> np.ndarray:
    points = values.shape[-1]
    spectrum = fft(values, axis=-1) / points
    frequency_daily = fftfreq(points, d=1.0 / steps_per_day)
    frequency_yearly = frequency_daily * (points / steps_per_day)
    spectrum[..., np.abs(frequency_yearly) > harmonics] = 0.0
    return ifft(spectrum * points, axis=-1).real


def _harmonic_annual_cycle(wind: xr.DataArray, harmonics: int) -> xr.DataArray:
    """Build the updated leap-aligned climatology and retain low harmonics."""

    if harmonics < 0:
        raise ValueError("annual_harmonics must be non-negative")
    cycle_index, days_per_year, steps_per_day = _cycle_index(wind.time)
    cycle_length = days_per_year * steps_per_day
    climatology = wind.assign_coords(cycle_step=cycle_index).groupby("cycle_step").mean("time")
    climatology = climatology.reindex(cycle_step=np.arange(cycle_length))
    missing = climatology.isnull().all(("lat", "lon"))
    missing_steps = np.flatnonzero(np.asarray(missing.compute() if hasattr(missing.data, "compute") else missing))
    leap_day_steps = np.arange(59 * steps_per_day, 60 * steps_per_day)
    if days_per_year == 366 and np.array_equal(missing_steps, leap_day_steps):
        # A record containing only non-leap Gregorian/Julian years has no
        # samples for 29 February in the common 366-day climatology. Fill
        # those slots from the same UTC times on the adjacent days. Records
        # containing a leap year are unchanged, preserving legacy results.
        previous = climatology.sel(cycle_step=leap_day_steps - steps_per_day).assign_coords(
            cycle_step=leap_day_steps
        )
        following = climatology.sel(cycle_step=leap_day_steps + steps_per_day).assign_coords(
            cycle_step=leap_day_steps
        )
        leap_day = 0.5 * (previous + following)
        climatology = xr.concat(
            [climatology.drop_sel(cycle_step=leap_day_steps), leap_day],
            dim="cycle_step",
        ).sortby("cycle_step")
        missing_steps = np.array([], dtype=int)
    if missing_steps.size:
        raise ValueError(
            "The harmonic annual cycle has no samples for climatological step(s) "
            f"{missing_steps[:8].tolist()}; use complete years or another anomaly method"
        )
    filtered = xr.apply_ufunc(
        _retain_cycle_harmonics,
        climatology,
        kwargs={"harmonics": harmonics, "steps_per_day": steps_per_day},
        input_core_dims=[["cycle_step"]],
        output_core_dims=[["cycle_step"]],
        dask="parallelized",
        output_dtypes=[float],
        dask_gufunc_kwargs={"allow_rechunk": True},
    )
    expanded = filtered.isel(cycle_step=cycle_index).drop_vars("cycle_step")
    return expanded.transpose(*wind.dims).assign_coords(time=wind.time)


def remove_background(wind: xr.DataArray, method: str, harmonics: int) -> xr.DataArray:
    """Remove a leap-aligned harmonic annual cycle, time mean, or no background."""

    method = method.lower()
    if method == "none":
        result = wind
    elif method == "time_mean":
        result = wind - wind.mean("time")
    elif method == "harmonic":
        result = wind - _harmonic_annual_cycle(wind, harmonics)
    else:
        raise ValueError("anomaly_method must be one of: harmonic, time_mean, none")
    result.name = "wind_anomaly"
    return result


def zonal_filter(data: xr.DataArray, wavenumber_min: int, wavenumber_max: int) -> xr.DataArray:
    """Retain the requested integer zonal wavenumbers."""

    nlon = data.sizes["lon"]
    if not 0 <= wavenumber_min <= wavenumber_max <= nlon // 2:
        raise ValueError(f"Wavenumbers must satisfy 0 <= min <= max <= {nlon // 2}")

    def _filter(values: np.ndarray) -> np.ndarray:
        spacing = abs(float(np.mean(np.diff(data.lon.values))))
        spectrum = fft(values, axis=-1) / nlon
        wave = np.abs(fftfreq(nlon, d=spacing) * 360.0)
        spectrum[..., (wave < wavenumber_min) | (wave > wavenumber_max)] = 0.0
        return ifft(spectrum * nlon, axis=-1).real

    result = xr.apply_ufunc(
        _filter,
        data,
        input_core_dims=[["lon"]],
        output_core_dims=[["lon"]],
        dask="parallelized",
        output_dtypes=[float],
        dask_gufunc_kwargs={"allow_rechunk": True},
    ).transpose(*data.dims)
    result.name = "filtered_wind"
    return result


def analytic_fields(filtered: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    """Return local envelope amplitude and phase along cyclic longitude."""

    transformed = xr.apply_ufunc(
        hilbert,
        filtered,
        input_core_dims=[["lon"]],
        output_core_dims=[["lon"]],
        dask="parallelized",
        output_dtypes=[complex],
        dask_gufunc_kwargs={"allow_rechunk": True},
    ).transpose(*filtered.dims)
    amplitude = np.abs(transformed).rename("amplitude")
    phase = xr.apply_ufunc(np.angle, transformed, dask="allowed").rename("phase")
    amplitude.attrs.update({"long_name": "local Rossby wave packet envelope", "units": filtered.attrs.get("units", "m s-1")})
    phase.attrs.update({"long_name": "local Rossby wave phase", "units": "rad"})
    return amplitude, phase


def _wrapped_delta(a: xr.DataArray, b: xr.DataArray) -> xr.DataArray:
    return xr.apply_ufunc(np.angle, np.exp(1j * (a - b)), dask="allowed")


def _infer_timestep_seconds(time: xr.DataArray) -> float:
    values = np.asarray(time.values)
    deltas = np.diff(values)
    if np.issubdtype(deltas.dtype, np.timedelta64):
        seconds = deltas / np.timedelta64(1, "s")
    else:
        seconds = np.asarray([delta.total_seconds() for delta in deltas], dtype=float)
    step = float(np.median(seconds))
    if step <= 0 or not np.allclose(seconds, step, rtol=1e-5, atol=1e-3):
        raise ValueError("Time must be strictly increasing and uniformly spaced")
    return step


def phase_speed(
    phase: xr.DataArray,
    amplitude: xr.DataArray,
    threshold: float,
    speed_limit: float | None,
) -> xr.DataArray:
    """Calculate phase speed using the legacy wrapped-difference sequence."""

    phase_values = np.asarray(phase.compute().values)
    amplitude_values = np.asarray(amplitude.compute().values)
    nt, ny, nx = phase_values.shape
    dt = _infer_timestep_seconds(phase.time)
    dlon = np.deg2rad(abs(float(np.mean(np.diff(phase.lon.values)))))

    inverse_radius = 1.0 / (
        EARTH_RADIUS_M * np.cos(np.deg2rad(np.asarray(phase.lat, dtype=float)))
    )
    values = np.full_like(phase_values, np.nan, dtype=float)

    # Work one time plane at a time. The legacy arithmetic is unchanged, but
    # this avoids several record-sized derivative and padding arrays.
    for index in range(nt):
        if index == 0:
            before = phase_values[0]
            after = phase_values[1]
            difference = after - before
            phase_dt = np.where(
                difference > np.pi,
                (before + 2.0 * np.pi - after) / dt,
                np.where(
                    difference < -np.pi,
                    (before - 2.0 * np.pi - after) / dt,
                    (before - after) / dt,
                ),
            )
            amplitude_before = amplitude_values[0]
            amplitude_after = amplitude_values[1]
        elif index == nt - 1:
            before = phase_values[-2]
            after = phase_values[-1]
            difference = before - after
            phase_dt = np.where(
                difference > np.pi,
                (before + 2.0 * np.pi - after) / dt,
                np.where(
                    difference < -np.pi,
                    (before - 2.0 * np.pi - after) / dt,
                    (before - after) / dt,
                ),
            )
            amplitude_before = amplitude_values[-2]
            amplitude_after = amplitude_values[-1]
        else:
            before = phase_values[index - 1]
            after = phase_values[index + 1]
            difference = after - before
            phase_dt = np.where(
                difference > np.pi,
                (before + 2.0 * np.pi - after) / (2.0 * dt),
                np.where(
                    difference < -np.pi,
                    (before - 2.0 * np.pi - after) / (2.0 * dt),
                    (before - after) / (2.0 * dt),
                ),
            )
            amplitude_before = amplitude_values[index - 1]
            amplitude_after = amplitude_values[index + 1]

        phase_now = phase_values[index]
        west = np.roll(phase_now, 1, axis=1)
        east = np.roll(phase_now, -1, axis=1)
        difference = west - east
        phase_dlambda = np.where(
            difference > np.pi,
            (east + 2.0 * np.pi - west) / (2.0 * dlon),
            np.where(
                difference < -np.pi,
                (east - 2.0 * np.pi - west) / (2.0 * dlon),
                (east - west) / (2.0 * dlon),
            ),
        )
        wavenumber = inverse_radius[:, None] * phase_dlambda
        with np.errstate(divide="ignore", invalid="ignore"):
            speed = phase_dt / wavenumber

        amplitude_now = amplitude_values[index]
        valid = (
            (amplitude_now >= threshold)
            & (amplitude_before >= threshold)
            & (amplitude_after >= threshold)
            & (np.roll(amplitude_now, 1, axis=1) >= threshold)
            & (np.roll(amplitude_now, -1, axis=1) >= threshold)
        )
        speed[~valid] = np.nan
        if speed_limit is not None:
            speed[np.abs(speed) > speed_limit] = np.nan
        values[index] = speed
    coordinates = {name: phase[name] for name in phase.dims}
    result = xr.DataArray(values, dims=phase.dims, coords=coordinates, name="phase_speed")
    result.attrs.update({"long_name": "Rossby wave phase speed", "units": "m s-1"})
    return result


def group_velocity(
    amplitude: xr.DataArray,
    threshold: float,
    zonal_extent: float,
    meridional_extent: float,
    smoothing_sigma_degrees: float,
    speed_limit: float,
) -> tuple[xr.DataArray, xr.DataArray]:
    """Calculate cg with the legacy packet-segment tracking algorithm."""

    values = np.asarray(amplitude.compute().values)
    cgx_values, cgy_values = tracked_group_velocity(
        values,
        np.asarray(amplitude.lat, dtype=float),
        np.asarray(amplitude.lon, dtype=float),
        threshold,
        zonal_extent,
        meridional_extent,
        smoothing_sigma_degrees,
        _infer_timestep_seconds(amplitude.time),
        speed_limit,
    )
    coordinates = {name: amplitude[name] for name in amplitude.dims}
    cgx = xr.DataArray(cgx_values, dims=amplitude.dims, coords=coordinates, name="group_velocity_zonal")
    cgy = xr.DataArray(cgy_values, dims=amplitude.dims, coords=coordinates, name="group_velocity_meridional")
    cgx.attrs.update({"long_name": "zonal Rossby wave packet group velocity", "units": "m s-1"})
    cgy.attrs.update({"long_name": "meridional Rossby wave packet group velocity", "units": "m s-1"})
    return cgx, cgy


def run_rwp(data: xr.Dataset | xr.DataArray, config: RWPConfig | None = None, **options: Any) -> xr.Dataset:
    """Run the complete RWP diagnostic as one reusable function.

    Parameters may be supplied through ``RWPConfig`` or as keyword arguments,
    but not both.  Coordinate and variable names are inferred unless explicit
    names are supplied.
    """

    if config is not None and options:
        raise TypeError("Pass either config or keyword options, not both")
    cfg = config or RWPConfig(**options)
    wind = prepare_wind(data, cfg)
    # Phase speed and the legacy packet tracker both require the complete
    # selected record. Load after coordinate, level, latitude, and date
    # selection so Dask cannot build simultaneous full-time and full-longitude
    # rechunks for the two Fourier transforms.
    if hasattr(wind.data, "compute"):
        wind = wind.compute()
    if cfg.prefiltered_input:
        filtered = wind.rename("filtered_wind")
    else:
        anomaly = remove_background(wind, cfg.anomaly_method, cfg.annual_harmonics)
        # Time and longitude are core dimensions of consecutive transforms.
        # Materializing between them prevents Dask from combining both
        # rechunks into a single, high-memory task.
        if hasattr(anomaly.data, "compute"):
            anomaly = anomaly.compute()
        filtered = zonal_filter(anomaly, cfg.wavenumber_min, cfg.wavenumber_max)
    if hasattr(filtered.data, "compute"):
        filtered = filtered.compute()
    amplitude, phase = analytic_fields(filtered)
    cp = phase_speed(amplitude=amplitude, phase=phase, threshold=cfg.amplitude_threshold, speed_limit=cfg.phase_speed_limit)
    output = xr.Dataset({"filtered_wind": filtered, "amplitude": amplitude, "phase": phase, "phase_speed": cp})
    if cfg.compute_group_velocity:
        cgx, cgy = group_velocity(
            amplitude,
            cfg.group_amplitude_threshold,
            cfg.minimum_zonal_extent,
            cfg.minimum_meridional_extent,
            cfg.smoothing_sigma_degrees,
            cfg.group_speed_limit,
        )
        output["group_velocity_zonal"] = cgx
        output["group_velocity_meridional"] = cgy
    output.attrs.update(
        {
            "title": "Rossby wave packet diagnostic",
            "references": "doi:10.1175/JCLI-D-19-0377.1",
            "input_variable": wind.name,
            "prefiltered_input": str(cfg.prefiltered_input).lower(),
            "anomaly_method": "skipped" if cfg.prefiltered_input else cfg.anomaly_method,
            "annual_harmonics": cfg.annual_harmonics,
            "zonal_wavenumber_range": "input supplied prefiltered" if cfg.prefiltered_input else f"{cfg.wavenumber_min}-{cfg.wavenumber_max}",
            "phase_speed_envelope_threshold": cfg.amplitude_threshold,
            "group_velocity_envelope_threshold": cfg.group_amplitude_threshold,
            "group_velocity_smoothing_sigma_degrees": cfg.smoothing_sigma_degrees,
            "phase_speed_absolute_limit": "none" if cfg.phase_speed_limit is None else cfg.phase_speed_limit,
            "group_speed_absolute_limit": cfg.group_speed_limit,
            "latitude_range_degrees_north": f"{cfg.latitude_min}-{cfg.latitude_max}",
        }
    )
    return output


def write_netcdf(dataset: xr.Dataset, path: str | Path) -> Path:
    """Write compressed float32 diagnostic fields to NetCDF."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoding = {name: {"dtype": "float32", "zlib": True, "complevel": 2} for name in dataset.data_vars}
    dataset.to_netcdf(target, encoding=encoding)
    return target
