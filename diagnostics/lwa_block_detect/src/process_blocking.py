#!/usr/bin/env python3
"""Detect, classify, and summarize blocking events for one simulation."""

from __future__ import annotations

import argparse
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage


BLOCK_TYPES = ("ridge", "trough", "dipole")

EVENT_COLUMNS = (
    "event_id", "hemisphere", "block_type", "start_date", "end_date", "duration_days",
    "start_lon_degrees_east", "start_lat_degrees_north", "end_lon_degrees_east",
    "end_lat_degrees_north", "mean_lon_degrees_east", "mean_lat_degrees_north",
    "peak_date", "peak_time_index", "peak_lon_degrees_east", "peak_lat_degrees_north",
    "peak_lwa", "mean_lwa", "peak_longitude_width_degrees", "mean_longitude_width_degrees",
    "peak_area_grid_cells", "mean_area_grid_cells", "peak_area_km2", "mean_area_km2",
    "translation_speed_km_per_day", "anticyclonic_lwa_sum", "cyclonic_lwa_sum",
)

TRACK_COLUMNS = (
    "event_id", "hemisphere", "block_type", "day_in_event", "time_index", "date",
    "core_lon_degrees_east", "core_lat_degrees_north", "core_lwa",
    "longitude_width_degrees", "area_grid_cells", "area_km2",
)


def time_values_to_timestamps(values) -> list[object]:
    try:
        return pd.to_datetime(values).to_list()
    except (TypeError, ValueError, OverflowError):
        # Preserve cftime objects. Converting dates such as 30 February from a
        # 360_day model calendar to Gregorian pandas timestamps is invalid.
        return list(values)


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371.0


def cyclic_lon_delta(lon2: float, lon1: float) -> float:
    delta = lon2 - lon1
    if delta > 180:
        delta -= 360
    if delta < -180:
        delta += 360
    return delta


def load_lwa(lwa_dir: Path, hemisphere: str, suffix: str) -> xr.Dataset:
    ds = xr.open_dataset(lwa_dir / f"LWA_Z500_{suffix}.nc")
    if hemisphere == "NH":
        mask = (ds.lat >= 0) & (ds.lat < 90)
    else:
        mask = (ds.lat > -90) & (ds.lat <= 0)
    return ds.sel(lat=ds.lat[mask]).sortby("lat")


def merge_dateline(labels: np.ndarray, num_labels: int) -> tuple[np.ndarray, int]:
    labels_new = labels.copy()
    if np.all(labels_new[:, 0] == 0) or np.all(labels_new[:, -1] == 0):
        return labels_new, num_labels
    for label_0 in np.unique(labels_new[:, 0][labels_new[:, 0] != 0]):
        for label_1 in np.unique(labels_new[:, -1][labels_new[:, -1] != 0]):
            if label_0 == label_1:
                continue
            if np.any((labels_new[:, 0] == label_0) & (labels_new[:, -1] == label_1)):
                keep, drop = sorted((label_0, label_1))
                labels_new[labels_new == drop] = keep
                labels_new[labels_new > drop] -= 1
                num_labels -= 1
    return labels_new, num_labels


def daily_wave_events(lwa: np.ndarray, lat: np.ndarray, lon: np.ndarray, threshold: float):
    nday, nlat, nlon = lwa.shape
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int8)
    labels_all = np.zeros((nday, nlat, nlon), dtype=np.int32)
    counts = np.zeros(nday, dtype=np.int32)
    lat_d, lon_d, lon_wide, area = [], [], [], []

    for day in range(nday):
        labels, num_features = ndimage.label(lwa[day] > threshold, structure=structure)
        labels, num_features = merge_dateline(labels, num_features)
        labels_all[day] = labels
        counts[day] = num_features + 1
        day_lat, day_lon, day_wide, day_area = [], [], [], []
        for label in range(1, num_features + 1):
            mask = labels == label
            if not np.any(mask):
                continue
            values = np.where(mask, lwa[day], -np.inf)
            lat_idx, lon_idx = np.unravel_index(np.argmax(values), values.shape)
            day_lat.append(float(lat[lat_idx]))
            day_lon.append(float(lon[lon_idx]))
            occupied_lon = np.where(mask.any(axis=0))[0]
            if len(occupied_lon) == 0:
                width = 0.0
            else:
                west = lon[occupied_lon[0]]
                east = lon[occupied_lon[-1]]
                width = east - west if east >= west else 360 + east - west
            day_wide.append(float(width))
            day_area.append(float(mask.sum()))
        if not day_lat:
            day_lat, day_lon, day_wide, day_area = [np.nan], [np.nan], [np.nan], [np.nan]
        lat_d.append(np.array(day_lat))
        lon_d.append(np.array(day_lon))
        lon_wide.append(np.array(day_wide))
        area.append(np.array(day_area))
    return labels_all, counts, lat_d, lon_d, lon_wide, area


def select_threshold(
    lwa: np.ndarray,
    method: str = "percentile_max",
    percentile: float = 85.0,
    absolute_value: float | None = None,
) -> float:
    """Select the scalar LWA contour used to define daily event patches.

    ``percentile_max`` raises the legacy median of meridional maxima to a
    configurable upper percentile. This retains adaptation to each model and
    hemisphere while preventing ordinary wave activity from joining otherwise
    distinct blocking cores into very broad patches.
    """
    meridional_maximum = np.nanmax(lwa, axis=1)
    if method == "median_max":
        return float(np.nanmedian(meridional_maximum))
    if method == "percentile_max":
        if not 50.0 <= percentile < 100.0:
            raise ValueError("threshold percentile must be in [50, 100)")
        return float(np.nanpercentile(meridional_maximum, percentile))
    if method == "absolute":
        if absolute_value is None or not np.isfinite(absolute_value) or absolute_value <= 0:
            raise ValueError("a positive --threshold-value is required for an absolute threshold")
        return float(absolute_value)
    raise ValueError(f"Unknown threshold method: {method}")


def detect_blocks(
    ds: xr.Dataset,
    hemisphere: str,
    duration: int,
    threshold_method: str = "percentile_max",
    threshold_percentile: float = 85.0,
    threshold_value: float | None = None,
):
    lwa = ds["LWA"].values.astype(np.float32)
    lat = ds.lat.values
    lon = ds.lon.values
    dates = time_values_to_timestamps(ds.time.values)
    nday, nlat, nlon = lwa.shape
    threshold = select_threshold(
        lwa, threshold_method, threshold_percentile, threshold_value
    )
    labels, _, lat_d, lon_d, lon_wide, area = daily_wave_events(lwa, lat, lon, threshold)
    min_lat_ok = (lambda value: value > 30) if hemisphere == "NH" else (lambda value: value < -30)

    blocks = {key: [] for key in ("date", "lon", "lat", "lon_wide", "area", "label")}
    for day0 in range(nday - 1):
        shift = np.full((len(lon_d[day0]), len(lon_d[day0 + 1])), np.inf)
        for i in range(shift.shape[0]):
            for j in range(shift.shape[1]):
                shift[i, j] = haversine(lon_d[day0][i], lat_d[day0][i], lon_d[day0 + 1][j], lat_d[day0 + 1][j])
        shift[np.isnan(shift)] = np.inf
        if np.all(np.isinf(shift)):
            continue

        for _ in range(min(shift.shape)):
            original_i, original_j = np.unravel_index(np.argmin(shift), shift.shape)
            i, j = original_i, original_j
            day = 0
            track = {key: [] for key in ("date", "lon", "lat", "lon_wide", "area", "label", "lon_index", "lat_index")}
            while True:
                label_mask = labels[day0 + day] == i + 1
                track["date"].append(dates[day0 + day])
                track["lon"].append(float(lon_d[day0 + day][i]))
                track["lat"].append(float(lat_d[day0 + day][i]))
                track["lon_wide"].append(float(lon_wide[day0 + day][i]))
                track["area"].append(float(area[day0 + day][i]))
                track["label"].append(label_mask)
                track["lon_index"].append(i)
                track["lat_index"].append(i)

                if day0 + day + 1 >= nday:
                    break
                lon_shift = cyclic_lon_delta(lon_d[day0 + day + 1][j], track["lon"][-1])
                lat_shift = lon_d[day0 + day + 1][j] * 0 + lat_d[day0 + day + 1][j] - track["lat"][-1]
                if not (
                    abs(lon_shift) < 18
                    and abs(lat_shift) < 13.5
                    and abs(lon_shift) + abs(lat_shift) < 31.5
                    and min_lat_ok(track["lat"][-1])
                ):
                    break
                day += 1
                if day0 + day + 1 >= nday:
                    i = j
                    continue
                next_shift = np.full((len(lon_d[day0 + day]), len(lon_d[day0 + day + 1])), np.inf)
                for ii in range(next_shift.shape[0]):
                    for jj in range(next_shift.shape[1]):
                        next_shift[ii, jj] = haversine(
                            lon_d[day0 + day][ii], lat_d[day0 + day][ii],
                            lon_d[day0 + day + 1][jj], lat_d[day0 + day + 1][jj],
                        )
                next_shift[np.isnan(next_shift)] = np.inf
                found = False
                for _ in range(min(next_shift.shape)):
                    ii, jj = np.unravel_index(np.argmin(next_shift), next_shift.shape)
                    if ii == j:
                        i, j = ii, jj
                        found = True
                        break
                    next_shift[ii, :] = np.inf
                    next_shift[:, jj] = np.inf
                if not found:
                    break

            if len(track["date"]) >= duration and sum(width > 15 for width in track["lon_wide"]) >= duration:
                for key in ("date", "lon", "lat", "lon_wide", "area", "label"):
                    blocks[key].append(track[key])
                shift[original_i, :] = np.inf
                shift[:, original_j] = np.inf
                for offset, idx in enumerate(track["lat_index"]):
                    lon_d[day0 + offset][idx] = np.nan
                    lat_d[day0 + offset][idx] = np.nan
            else:
                shift[original_i, :] = np.inf
                shift[:, original_j] = np.inf
    return blocks, threshold


def add_peak_metrics(blocks: dict, ds_tot: xr.Dataset) -> None:
    lwa = ds_tot["LWA"].values.astype(np.float32)
    lat = ds_tot.lat.values
    lon = ds_tot.lon.values
    date_index = {date: idx for idx, date in enumerate(time_values_to_timestamps(ds_tot.time.values))}
    for key in ("peak_date", "peak_lon", "peak_lat", "peak_LWA", "duration", "velocity", "peak_lon_wide", "peak_area"):
        blocks[key] = []
    for event_dates, event_lons, event_lats, event_widths, event_areas in zip(
        blocks["date"], blocks["lon"], blocks["lat"], blocks["lon_wide"], blocks["area"]
    ):
        values = []
        for date, event_lon, event_lat in zip(event_dates, event_lons, event_lats):
            values.append(lwa[date_index[date], np.argmin(np.abs(lat - event_lat)), np.argmin(np.abs(lon - event_lon))])
        peak_idx = int(np.argmax(values))
        blocks["peak_date"].append(event_dates[peak_idx])
        blocks["peak_lon"].append(event_lons[peak_idx])
        blocks["peak_lat"].append(event_lats[peak_idx])
        blocks["peak_LWA"].append(float(values[peak_idx]))
        blocks["duration"].append(len(event_dates))
        blocks["peak_lon_wide"].append(event_widths[peak_idx])
        blocks["peak_area"].append(event_areas[peak_idx])
        blocks["velocity"].append(
            haversine(event_lons[0], event_lats[0], event_lons[-1], event_lats[-1])
            / max(1, len(event_dates) - 1)
        )


def classify_blocks(blocks: dict, ds_tot: xr.Dataset, ds_ac: xr.Dataset, ds_c: xr.Dataset) -> dict:
    date_list = time_values_to_timestamps(ds_tot.time.values)
    date_index = {date: idx for idx, date in enumerate(date_list)}
    lat = ds_tot.lat.values
    lon = ds_tot.lon.values
    nlon = len(lon)
    dlon = abs(float(np.diff(lon).mean()))
    lon_range = int(31 / dlon) + 1
    regular_lon = np.allclose(np.diff(lon), np.diff(lon)[0], rtol=1.e-5, atol=1.e-8)
    sorted_blocks = {block_type: {key: [] for key in (
        "date", "lon", "lat", "lon_wide", "area", "lwa", "peak_date", "peak_lon", "peak_lat",
        "peak_area", "peak_lwa", "mean_lon", "mean_lat", "mean_area", "mean_lwa", "duration",
        "velocity", "AC_sum", "C_sum", "label"
    )} for block_type in BLOCK_TYPES}

    for n, event_dates in enumerate(blocks["date"]):
        day_ids = [date_index[d] for d in event_dates]
        # Keep the original float32 reduction semantics so event-mean LWA is
        # numerically identical while reading only the needed daily slices.
        point_lwa = [
            np.float32(ds_tot["LWA"].isel(time=day).values[
                np.argmin(np.abs(lat - event_lat)), np.argmin(np.abs(lon - event_lon))
            ])
            for day, event_lat, event_lon in zip(day_ids, blocks["lat"][n], blocks["lon"][n])
        ]
        peak_day = date_index[blocks["peak_date"][n]]
        peak_lon_idx = int(np.argmin(np.abs(lon - blocks["peak_lon"][n])))
        event_idx = event_dates.index(blocks["peak_date"][n])
        ac_peak = ds_ac["LWA"].isel(time=peak_day).values.astype(np.float32)
        c_peak = ds_c["LWA"].isel(time=peak_day).values.astype(np.float32)
        event_mask = blocks["label"][n][event_idx].astype(bool)
        if regular_lon:
            # Preserve the original index-window calculation exactly.
            shift = int(nlon / 2) - peak_lon_idx
            ac_shift = np.roll(ac_peak, shift, axis=1)
            c_shift = np.roll(c_peak, shift, axis=1)
            we_shift = np.roll(event_mask, shift, axis=1)
            lon_start = int(nlon / 2) - int(lon_range / 2)
            lon_end = int(nlon / 2) + int(lon_range / 2) + 1
            ac_sum = float(np.where(we_shift[:, lon_start:lon_end], ac_shift[:, lon_start:lon_end], 0).sum())
            c_sum = float(np.where(we_shift[:, lon_start:lon_end], c_shift[:, lon_start:lon_end], 0).sum())
        else:
            angular_distance = np.abs((lon - lon[peak_lon_idx] + 180.0) % 360.0 - 180.0)
            window_mask = event_mask & (angular_distance <= 15.5)[None, :]
            ac_sum = float(np.where(window_mask, ac_peak, 0).sum())
            c_sum = float(np.where(window_mask, c_peak, 0).sum())
        block_type = "ridge" if ac_sum > 10 * c_sum else "trough" if c_sum > 2 * ac_sum else "dipole"
        target = sorted_blocks[block_type]
        target["date"].append(event_dates)
        target["lon"].append(blocks["lon"][n])
        target["lat"].append(blocks["lat"][n])
        target["lon_wide"].append(blocks["lon_wide"][n])
        target["area"].append(blocks["area"][n])
        target["lwa"].append([float(value) for value in point_lwa])
        target["peak_date"].append(blocks["peak_date"][n])
        target["peak_lon"].append(blocks["peak_lon"][n])
        target["peak_lat"].append(blocks["peak_lat"][n])
        target["peak_area"].append(blocks["peak_area"][n])
        target["peak_lwa"].append(blocks["peak_LWA"][n])
        target["mean_lon"].append(float(np.mean(blocks["lon"][n])))
        target["mean_lat"].append(float(np.mean(blocks["lat"][n])))
        target["mean_area"].append(float(np.mean(blocks["area"][n])))
        target["mean_lwa"].append(float(np.mean(point_lwa)))
        target["duration"].append(blocks["duration"][n])
        target["velocity"].append(blocks["velocity"][n])
        target["AC_sum"].append(ac_sum)
        target["C_sum"].append(c_sum)
        target["label"].append(blocks["label"][n])
    return sorted_blocks


def _cell_area_km2(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Return spherical grid-cell area for a rectilinear latitude-longitude grid."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lat_edges = np.empty(len(lat) + 1)
    lat_edges[1:-1] = 0.5 * (lat[:-1] + lat[1:])
    lat_edges[0] = max(-90.0, lat[0] - 0.5 * (lat[1] - lat[0]))
    lat_edges[-1] = min(90.0, lat[-1] + 0.5 * (lat[-1] - lat[-2]))
    lon_gaps = np.concatenate([np.diff(lon), [360.0 - (lon[-1] - lon[0])]])
    lon_widths = np.deg2rad(0.5 * (np.roll(lon_gaps, 1) + lon_gaps))
    bands = (6371.0 ** 2) * (
        np.sin(np.deg2rad(lat_edges[1:])) - np.sin(np.deg2rad(lat_edges[:-1]))
    )
    return bands[:, None] * lon_widths[None, :]


def _circular_mean_longitude(values) -> float:
    radians_values = np.deg2rad(np.asarray(values, dtype=float))
    angle = np.arctan2(np.mean(np.sin(radians_values)), np.mean(np.cos(radians_values)))
    return float(np.rad2deg(angle) % 360.0)


def _circular_width_degrees(mask: np.ndarray, lon: np.ndarray) -> float:
    """Return the minimum longitude arc containing all occupied grid columns."""
    occupied = np.where(mask.any(axis=0))[0]
    if len(occupied) < 2:
        return 0.0
    angles = np.sort(np.asarray(lon[occupied], dtype=float) % 360.0)
    gaps = np.diff(np.concatenate([angles, angles[:1] + 360.0]))
    return float(360.0 - np.max(gaps))


def save_event_products(
    sorted_blocks: dict,
    ds_tot: xr.Dataset,
    hemisphere: str,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    """Write gridded event IDs/types and accessible event and track catalogs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dates = time_values_to_timestamps(ds_tot.time.values)
    date_index = {date: idx for idx, date in enumerate(dates)}
    block_type_grid = np.zeros(ds_tot["LWA"].shape, dtype=np.int8)
    event_id_grid = np.zeros(ds_tot["LWA"].shape, dtype=np.int32)
    cell_area = _cell_area_km2(ds_tot.lat.values, ds_tot.lon.values)
    event_rows = []
    track_rows = []
    event_id = 0

    for type_code, block_type in enumerate(BLOCK_TYPES, start=1):
        fields = sorted_blocks[block_type]
        for n, event_dates in enumerate(fields["date"]):
            event_id += 1
            day_ids = [date_index[date] for date in event_dates]
            peak_offset = event_dates.index(fields["peak_date"][n])
            areas_km2 = []
            circular_widths = []
            for offset, (date, label) in enumerate(zip(event_dates, fields["label"][n])):
                day_idx = day_ids[offset]
                mask = label.astype(bool)
                available = mask & (event_id_grid[day_idx] == 0)
                block_type_grid[day_idx][available] = type_code
                event_id_grid[day_idx][available] = event_id
                area_km2 = float(cell_area[mask].sum())
                areas_km2.append(area_km2)
                circular_width = _circular_width_degrees(mask, ds_tot.lon.values)
                circular_widths.append(circular_width)
                track_rows.append({
                    "event_id": event_id,
                    "hemisphere": hemisphere,
                    "block_type": block_type,
                    "day_in_event": offset + 1,
                    "time_index": day_idx,
                    "date": str(date),
                    "core_lon_degrees_east": float(fields["lon"][n][offset]) % 360.0,
                    "core_lat_degrees_north": float(fields["lat"][n][offset]),
                    "core_lwa": float(fields["lwa"][n][offset]),
                    "longitude_width_degrees": circular_width,
                    "area_grid_cells": int(fields["area"][n][offset]),
                    "area_km2": area_km2,
                })
            event_rows.append({
                "event_id": event_id,
                "hemisphere": hemisphere,
                "block_type": block_type,
                "start_date": str(event_dates[0]),
                "end_date": str(event_dates[-1]),
                "duration_days": int(fields["duration"][n]),
                "start_lon_degrees_east": float(fields["lon"][n][0]) % 360.0,
                "start_lat_degrees_north": float(fields["lat"][n][0]),
                "end_lon_degrees_east": float(fields["lon"][n][-1]) % 360.0,
                "end_lat_degrees_north": float(fields["lat"][n][-1]),
                "mean_lon_degrees_east": _circular_mean_longitude(fields["lon"][n]),
                "mean_lat_degrees_north": float(fields["mean_lat"][n]),
                "peak_date": str(fields["peak_date"][n]),
                "peak_time_index": day_ids[peak_offset],
                "peak_lon_degrees_east": float(fields["peak_lon"][n]) % 360.0,
                "peak_lat_degrees_north": float(fields["peak_lat"][n]),
                "peak_lwa": float(fields["peak_lwa"][n]),
                "mean_lwa": float(fields["mean_lwa"][n]),
                "peak_longitude_width_degrees": circular_widths[peak_offset],
                "mean_longitude_width_degrees": float(np.mean(circular_widths)),
                "peak_area_grid_cells": int(fields["peak_area"][n]),
                "mean_area_grid_cells": float(fields["mean_area"][n]),
                "peak_area_km2": areas_km2[peak_offset],
                "mean_area_km2": float(np.mean(areas_km2)),
                "translation_speed_km_per_day": float(fields["velocity"][n]),
                "anticyclonic_lwa_sum": float(fields["AC_sum"][n]),
                "cyclonic_lwa_sum": float(fields["C_sum"][n]),
            })

    events_path = output_dir / f"blocking_events_{hemisphere}.csv"
    tracks_path = output_dir / f"blocking_tracks_{hemisphere}.csv"
    pd.DataFrame(event_rows, columns=EVENT_COLUMNS).to_csv(events_path, index=False)
    pd.DataFrame(track_rows, columns=TRACK_COLUMNS).to_csv(tracks_path, index=False)
    ds_events = xr.Dataset(
        {
            "blocking_type": (["time", "lat", "lon"], block_type_grid),
            "blocking_event_id": (["time", "lat", "lon"], event_id_grid),
        },
        coords={"time": ds_tot.time.values, "lat": ds_tot.lat.values, "lon": ds_tot.lon.values},
        attrs={
            "description": "Detected atmospheric blocking events",
            "blocking_type_codes": "0 = none, 1 = ridge, 2 = trough, 3 = dipole",
            "event_catalog": events_path.name,
            "track_catalog": tracks_path.name,
        },
    )
    ds_events["blocking_type"].attrs.update(
        long_name="blocking classification",
        flag_values=[0, 1, 2, 3],
        flag_meanings="no_block ridge trough dipole",
    )
    ds_events["blocking_event_id"].attrs.update(long_name="event identifier", comment="0 means no detected event")
    ds_events["lat"].attrs.update({"units": "degrees_north", "standard_name": "latitude"})
    ds_events["lon"].attrs.update({"units": "degrees_east", "standard_name": "longitude"})
    grid_path = output_dir / f"blocking_events_{hemisphere}.nc"
    ds_events.to_netcdf(grid_path)
    return grid_path, events_path, tracks_path


def run_hemisphere(
    lwa_dir: Path,
    output_dir: Path,
    hemisphere: str,
    duration: int = 5,
    threshold_method: str = "percentile_max",
    threshold_percentile: float = 85.0,
    threshold_value: float | None = None,
) -> dict:
    """Run detection and classification for one hemisphere.

    This function is the reusable API used by both the standalone command and
    the MDTF driver. It writes event-focused catalogs and gridded masks.
    """
    ds_tot = load_lwa(lwa_dir, hemisphere, "TOT")
    ds_ac = load_lwa(lwa_dir, hemisphere, "AC")
    ds_c = load_lwa(lwa_dir, hemisphere, "C")
    try:
        blocks, threshold = detect_blocks(
            ds_tot,
            hemisphere,
            duration,
            threshold_method,
            threshold_percentile,
            threshold_value,
        )
        add_peak_metrics(blocks, ds_tot)
        sorted_blocks = classify_blocks(blocks, ds_tot, ds_ac, ds_c)
        grid_path, events_path, tracks_path = save_event_products(
            sorted_blocks, ds_tot, hemisphere, output_dir
        )
        with open(output_dir / "threshold.txt", "w") as fp:
            fp.write(f"{threshold}\n")
        event_counts = {kind: len(sorted_blocks[kind]["date"]) for kind in BLOCK_TYPES}
        return {
            "hemisphere": hemisphere,
            "threshold": threshold,
            "threshold_method": threshold_method,
            "threshold_percentile": threshold_percentile,
            "event_counts": event_counts,
            "grid_path": grid_path,
            "events_path": events_path,
            "tracks_path": tracks_path,
        }
    finally:
        ds_tot.close()
        ds_ac.close()
        ds_c.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim-dir", type=Path, required=True)
    parser.add_argument("--hemisphere", choices=("NH", "SH", "both"), default="both")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument(
        "--threshold-method",
        choices=("percentile_max", "median_max", "absolute"),
        default="percentile_max",
    )
    parser.add_argument("--threshold-percentile", type=float, default=85.0)
    parser.add_argument("--threshold-value", type=float)
    args = parser.parse_args()

    hemispheres = ("NH", "SH") if args.hemisphere == "both" else (args.hemisphere,)
    for hemisphere in hemispheres:
        lwa_dir = args.sim_dir / "lwa"
        out_dir = args.sim_dir / "blocking" / hemisphere
        result = run_hemisphere(
            lwa_dir,
            out_dir,
            hemisphere,
            args.duration,
            args.threshold_method,
            args.threshold_percentile,
            args.threshold_value,
        )
        total = sum(result["event_counts"].values())
        print(f"{args.sim_dir.name} {hemisphere}: {total} events, threshold={result['threshold']:.3g}")


if __name__ == "__main__":
    main()
