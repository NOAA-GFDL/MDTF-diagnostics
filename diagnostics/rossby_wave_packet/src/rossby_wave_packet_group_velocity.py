"""Packet-tracking group velocity used by the RWP diagnostic."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import hilbert


EARTH_RADIUS_M = 6_371_000.0


def smooth_envelope(values: np.ndarray, sigma_lat: float, sigma_lon: float) -> np.ndarray:
    """Match the legacy Gaussian filter: nearest latitude and cyclic longitude."""

    pad_lat = int(4.0 * sigma_lat + 0.5)
    pad_lon = int(4.0 * sigma_lon + 0.5)
    padded = np.pad(
        np.asarray(values, dtype=float),
        ((0, 0), (pad_lat, pad_lat), (pad_lon, pad_lon)),
        mode="wrap",
    )
    if pad_lat:
        padded[:, :pad_lat, :] = padded[:, pad_lat : pad_lat + 1, :]
        padded[:, -pad_lat:, :] = padded[:, -pad_lat - 1 : -pad_lat, :]
    filtered = gaussian_filter(
        padded,
        sigma=(0.0, sigma_lat, sigma_lon),
        mode="nearest",
    )
    return filtered[:, pad_lat : pad_lat + values.shape[1], pad_lon : pad_lon + values.shape[2]]


def _zonal_segments(field: np.ndarray, threshold: float, extent: float, spacing: float) -> list[tuple[int, int, float, int]]:
    ny, nx = field.shape
    segments: list[tuple[int, int, float, int]] = []
    for j in range(ny):
        row: list[tuple[int, int, float, int]] = []
        i = 0
        while i < nx:
            if field[j, i] > threshold:
                start = i
                while i < nx - 1 and field[j, i + 1] > threshold:
                    i += 1
                row.append((start, i, (i - start) * spacing, j))
                i += 1
            else:
                i += 1
        if len(row) > 1 and row[0][0] == 0 and row[-1][1] == nx - 1:
            first, last = row[0], row[-1]
            combined = (last[0] - nx, first[1], last[2] + first[2] + spacing, j)
            row = row[1:-1] + [combined]
        segments.extend(segment for segment in row if segment[2] >= extent)
    return segments


def _meridional_segments(field: np.ndarray, threshold: float, extent: float, spacing: float) -> list[tuple[int, int, float, int]]:
    ny, nx = field.shape
    segments: list[tuple[int, int, float, int]] = []
    for i in range(nx):
        j = 0
        while j < ny:
            if field[j, i] > threshold:
                start = j
                while j < ny - 1 and field[j + 1, i] > threshold:
                    j += 1
                length = (j - start) * spacing
                if length >= extent:
                    segments.append((start, j, length, i))
                j += 1
            else:
                j += 1
    return segments


def _periodic_values(values: np.ndarray, start: int, end: int) -> np.ndarray:
    if start < 0:
        return np.concatenate((values[start:], values[: end + 1]))
    if end > values.size - 1:
        return np.concatenate((values[start:], values[: end - values.size + 1]))
    return values[start : end + 1]


def _segment_signal(values: np.ndarray, start: int, end: int, periodic: bool) -> tuple[np.ndarray, np.ndarray]:
    segment = _periodic_values(values, start, end) if periodic else values[start : end + 1]
    analytic = hilbert(segment - segment.mean())
    return np.abs(analytic), np.angle(analytic)


def _track_zonal(
    values: np.ndarray,
    search_start: int,
    search_end: int,
    points: int,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    search = _periodic_values(values, search_start, search_end)
    averages = np.convolve(search, np.ones(points) / points, mode="valid")
    start = search_start + int(np.argmax(averages))
    end = start + points - 1
    amplitude, phase = _segment_signal(values, start, end, periodic=True)
    return amplitude, phase, start, end


def _track_meridional(
    values: np.ndarray,
    search_start: int,
    search_end: int,
    points: int,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    search = values[search_start : search_end + 1]
    averages = np.convolve(search, np.ones(points) / points, mode="valid")
    start = search_start + int(np.argmax(averages))
    end = start + points - 1
    amplitude, phase = _segment_signal(values, start, end, periodic=False)
    return amplitude, phase, start, end


def _put_periodic(target: np.ndarray, row: int, start: int, values: np.ndarray) -> None:
    target[row, (start + np.arange(values.size)) % target.shape[1]] = values


def _one_time(
    previous: np.ndarray,
    current: np.ndarray,
    following: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    threshold: float,
    zonal_extent: float,
    meridional_extent: float,
    timestep_seconds: float,
    speed_limit: float,
) -> tuple[np.ndarray, np.ndarray]:
    ny, nx = current.shape
    dlon = abs(float(np.mean(np.diff(longitude))))
    dlat = abs(float(np.mean(np.diff(latitude))))

    phase_now = np.full_like(current, np.nan)
    phase_previous = np.full_like(current, np.nan)
    phase_following = np.full_like(current, np.nan)
    for start, end, length, row in _zonal_segments(current, threshold, zonal_extent, dlon):
        points = int(length / dlon) + 1
        _, phase = _segment_signal(current[row], start, end, periodic=True)
        _put_periodic(phase_now, row, start, phase)
        search_range = int((360.0 - length) / (2.0 * dlon)) if length + 2.0 * zonal_extent > 360.0 else int(zonal_extent / dlon)
        search_start = start - search_range
        search_end = end + search_range
        _, phase, tracked_start, _ = _track_zonal(previous[row], search_start, search_end, points)
        _put_periodic(phase_previous, row, tracked_start, phase)
        _, phase, tracked_start, _ = _track_zonal(following[row], search_start, search_end, points)
        _put_periodic(phase_following, row, tracked_start, phase)

    difference = phase_following - phase_previous
    omega_x = np.where(
        difference > np.pi,
        (phase_previous + 2.0 * np.pi - phase_following) / (2.0 * timestep_seconds),
        np.where(
            difference < -np.pi,
            (phase_previous - 2.0 * np.pi - phase_following) / (2.0 * timestep_seconds),
            (phase_previous - phase_following) / (2.0 * timestep_seconds),
        ),
    )
    east = np.roll(phase_now, -1, axis=1)
    west = np.roll(phase_now, 1, axis=1)
    delta_x = dlon * np.pi * EARTH_RADIUS_M / 180.0
    dx = 2.0 * delta_x * np.cos(np.deg2rad(latitude))[:, None]
    difference = west - east
    kx = np.where(
        difference > np.pi,
        (east + 2.0 * np.pi - west) / dx,
        np.where(
            difference < -np.pi,
            (east - 2.0 * np.pi - west) / dx,
            (east - west) / dx,
        ),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        cgx = omega_x / kx
    cgx[~np.isfinite(cgx) | (np.abs(cgx) > speed_limit)] = np.nan

    phase_now.fill(np.nan)
    phase_previous.fill(np.nan)
    phase_following.fill(np.nan)
    for start, end, length, column in _meridional_segments(current, threshold, meridional_extent, dlat):
        points = int(length / dlat) + 1
        _, phase = _segment_signal(current[:, column], start, end, periodic=False)
        phase_now[start : end + 1, column] = phase
        search_range = int(meridional_extent / dlat)
        search_start = max(0, start - search_range)
        search_end = min(ny - 1, end + search_range)
        _, phase, tracked_start, tracked_end = _track_meridional(previous[:, column], search_start, search_end, points)
        phase_previous[tracked_start : tracked_end + 1, column] = phase
        _, phase, tracked_start, tracked_end = _track_meridional(following[:, column], search_start, search_end, points)
        phase_following[tracked_start : tracked_end + 1, column] = phase

    difference = phase_following - phase_previous
    omega_y = np.where(
        difference > np.pi,
        (phase_previous + 2.0 * np.pi - phase_following) / (2.0 * timestep_seconds),
        np.where(
            difference < -np.pi,
            (phase_previous - 2.0 * np.pi - phase_following) / (2.0 * timestep_seconds),
            (phase_previous - phase_following) / (2.0 * timestep_seconds),
        ),
    )
    north = np.full_like(phase_now, np.nan)
    south = np.full_like(phase_now, np.nan)
    north[:-1] = phase_now[1:]
    south[1:] = phase_now[:-1]
    difference = south - north
    delta_y = dlat * np.pi * EARTH_RADIUS_M / 180.0
    dy = 2.0 * delta_y
    ky = np.where(
        difference > np.pi,
        (north + 2.0 * np.pi - south) / dy,
        np.where(
            difference < -np.pi,
            (north - 2.0 * np.pi - south) / dy,
            (north - south) / dy,
        ),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        cgy = omega_y / ky
    cgy[~np.isfinite(cgy) | (np.abs(cgy) > speed_limit)] = np.nan
    return cgx, cgy


def tracked_group_velocity(
    amplitude: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    threshold: float,
    zonal_extent: float,
    meridional_extent: float,
    smoothing_sigma_degrees: float,
    timestep_seconds: float,
    speed_limit: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce the legacy packet-segment group-velocity calculation."""

    dlat = abs(float(np.mean(np.diff(latitude))))
    dlon = abs(float(np.mean(np.diff(longitude))))
    amplitude = np.asarray(amplitude)
    smoothed = np.empty_like(amplitude, dtype=float)
    sigma_lat = smoothing_sigma_degrees / dlat
    sigma_lon = smoothing_sigma_degrees / dlon
    for index in range(amplitude.shape[0]):
        smoothed[index] = smooth_envelope(
            amplitude[index : index + 1],
            sigma_lat,
            sigma_lon,
        )[0]
    cgx = np.full_like(smoothed, np.nan, dtype=float)
    cgy = np.full_like(smoothed, np.nan, dtype=float)
    for index in range(1, smoothed.shape[0] - 1):
        cgx[index], cgy[index] = _one_time(
            smoothed[index - 1],
            smoothed[index],
            smoothed[index + 1],
            latitude,
            longitude,
            threshold,
            zonal_extent,
            meridional_extent,
            timestep_seconds,
            speed_limit,
        )
    return cgx, cgy
