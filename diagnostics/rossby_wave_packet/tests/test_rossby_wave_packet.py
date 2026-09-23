"""Fast tests for coordinate discovery and diagnostic output."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rossby_wave_packet_core import RWPConfig, prepare_wind, remove_background, run_rwp
from rossby_wave_packet import (
    DRIVER_HELP,
    _case_configuration,
    _case_summary,
    _parser,
    _phase_snapshot,
)


def synthetic_wave() -> xr.Dataset:
    time = np.arange(np.datetime64("2001-03-01T00"), np.datetime64("2001-03-03T00"), np.timedelta64(6, "h"))
    latitude = np.arange(30.0, 71.0, 10.0)
    longitude = np.arange(-180.0, 180.0, 5.0)
    pressure = np.array([25_000.0])
    wave = 6
    target_speed = 20.0
    omega = wave * target_speed / (6_371_000.0 * np.cos(np.deg2rad(50.0)))
    elapsed = (time - time[0]) / np.timedelta64(1, "s")
    phase = wave * np.deg2rad(longitude)[None, None, None, :] - omega * elapsed[:, None, None, None]
    values = 12.0 * np.cos(phase) * np.ones((1, 1, latitude.size, 1))
    dataset = xr.Dataset(
        {"V": (("forecast_time", "pressure", "latitude", "longitude"), values.astype("float32"))},
        coords={"forecast_time": time, "pressure": pressure, "latitude": latitude[::-1], "longitude": longitude},
    )
    dataset.V.attrs.update(standard_name="northward_wind", units="m s-1")
    dataset.forecast_time.attrs.update(standard_name="time", axis="T")
    dataset.pressure.attrs.update(standard_name="air_pressure", units="Pa", axis="Z")
    dataset.latitude.attrs.update(standard_name="latitude", units="degrees_north", axis="Y")
    dataset.longitude.attrs.update(standard_name="longitude", units="degrees_east", axis="X")
    return dataset


def test_coordinate_discovery_and_pressure_conversion() -> None:
    selected = prepare_wind(synthetic_wave(), RWPConfig(latitude_min=30, latitude_max=70))
    assert selected.dims == ("time", "lat", "lon")
    assert np.all(np.diff(selected.lat) > 0)
    assert np.all((selected.lon >= 0) & (selected.lon < 360))


def test_level_coordinate_lev_p_without_metadata() -> None:
    """Recognize the pressure name used by CESM LENS-derived files."""

    source = synthetic_wave().rename({"pressure": "lev_p"})
    source["lev_p"].attrs.clear()
    source = xr.concat(
        [source.assign_coords(lev_p=[200.0]), source.assign_coords(lev_p=[250.0]), source.assign_coords(lev_p=[300.0])],
        dim="lev_p",
    )
    selected = prepare_wind(
        source,
        RWPConfig(variable="V", level=250.0, latitude_min=30, latitude_max=70),
    )
    assert selected.dims == ("time", "lat", "lon")
    assert "lev_p" not in selected.dims


def test_complete_diagnostic() -> None:
    output = run_rwp(
        synthetic_wave(),
        level=250,
        latitude_min=30,
        latitude_max=70,
        anomaly_method="none",
        wavenumber_min=4,
        wavenumber_max=8,
        amplitude_threshold=1,
        compute_group_velocity=False,
    )
    assert {"filtered_wind", "amplitude", "phase", "phase_speed"} <= set(output.data_vars)
    assert output.sizes == {"time": 8, "lat": 5, "lon": 72}
    speed = output.phase_speed.sel(lat=50).isel(time=slice(1, -1)).median(skipna=True).item()
    assert np.isclose(speed, 20.0, atol=1.0)


def test_updated_defaults() -> None:
    config = RWPConfig()
    assert config.amplitude_threshold == 25.0
    assert config.group_amplitude_threshold == 20.0
    assert config.phase_speed_limit is None
    assert config.group_speed_limit == 100.0


def test_prefiltered_input_is_not_filtered_again() -> None:
    source = synthetic_wave()
    output = run_rwp(
        source,
        variable="V",
        level=250,
        latitude_min=30,
        latitude_max=70,
        prefiltered_input=True,
        amplitude_threshold=1,
        compute_group_velocity=False,
    )
    expected = prepare_wind(
        source,
        RWPConfig(variable="V", level=250, latitude_min=30, latitude_max=70),
    )
    xr.testing.assert_allclose(output.filtered_wind, expected.rename("filtered_wind"))
    assert output.attrs["prefiltered_input"] == "true"
    assert output.attrs["anomaly_method"] == "skipped"


def test_harmonic_cycle_aligns_nonleap_years_after_february() -> None:
    time = np.arange(
        np.datetime64("1999-01-01T00"),
        np.datetime64("2001-01-01T00"),
        np.timedelta64(6, "h"),
    )
    years = time.astype("datetime64[Y]").astype(int) + 1970
    starts = time.astype("datetime64[Y]")
    day = ((time.astype("datetime64[D]") - starts.astype("datetime64[D]")) / np.timedelta64(1, "D")).astype(int) + 1
    month = time.astype("datetime64[M]").astype(int) % 12 + 1
    leap = (years % 4 == 0) & ((years % 100 != 0) | (years % 400 == 0))
    adjusted_day = day + ((~leap) & (month > 2))
    hour = ((time - time.astype("datetime64[D]")) / np.timedelta64(1, "h")).astype(float)
    signal = np.sin(2.0 * np.pi * ((adjusted_day - 1) + hour / 24.0) / 366.0)
    wind = xr.DataArray(
        signal[:, None, None] * np.ones((1, 3, 4)),
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": [30.0, 40.0, 50.0], "lon": [0.0, 90.0, 180.0, 270.0]},
    )
    anomaly = remove_background(wind, "harmonic", 4)
    assert float(np.abs(anomaly).max()) < 1.0e-10


def test_complete_noleap_year_harmonic_cycle() -> None:
    """A one-year 365-day calendar supplies every climatological time slot."""

    time = xr.date_range(
        "1501-01-01",
        periods=365 * 4,
        freq="6h",
        calendar="noleap",
        use_cftime=True,
    )
    slot = np.arange(time.size, dtype=float)
    signal = np.cos(2.0 * np.pi * slot / time.size)
    wind = xr.DataArray(
        signal[:, None, None] * np.ones((1, 3, 4)),
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": [30.0, 40.0, 50.0], "lon": [0.0, 90.0, 180.0, 270.0]},
    )
    anomaly = remove_background(wind, "harmonic", 4)
    assert float(np.abs(anomaly).max()) < 1.0e-10


def test_other_cf_calendars_harmonic_cycle() -> None:
    """Fixed and Julian CF calendars use their correct annual lengths."""

    for calendar, year, days in (
        ("360_day", 1501, 360),
        ("all_leap", 1501, 366),
        ("julian", 1501, 365),
        ("proleptic_gregorian", 2001, 365),
    ):
        time = xr.date_range(
            f"{year:04d}-01-01",
            periods=days * 4,
            freq="6h",
            calendar=calendar,
            use_cftime=True,
        )
        slot = np.arange(time.size, dtype=float)
        signal = np.cos(2.0 * np.pi * slot / time.size)
        wind = xr.DataArray(
            signal[:, None, None] * np.ones((1, 3, 4)),
            dims=("time", "lat", "lon"),
            coords={"time": time, "lat": [30.0, 40.0, 50.0], "lon": [0.0, 90.0, 180.0, 270.0]},
        )
        anomaly = remove_background(wind, "harmonic", 4)
        assert np.isfinite(anomaly).all()
        if calendar in {"360_day", "all_leap"}:
            assert float(np.abs(anomaly).max()) < 1.0e-10


def test_mdtf_case_metadata_sets_native_names_and_dates() -> None:
    args = Namespace(
        variable=None,
        time_name=None,
        latitude_name=None,
        longitude_name=None,
        level_name=None,
        start_date=None,
        end_date=None,
    )
    case = {
        "va250_var": "V250",
        "time_coord": "Time",
        "lat_coord": "latitude",
        "lon_coord": "longitude",
        "startdate": "15010101",
        "enddate": "15011231",
    }
    config = _case_configuration(RWPConfig(), args, case)
    assert config.variable == "V250"
    assert config.time_name == "Time"
    assert config.latitude_name == "latitude"
    assert config.longitude_name == "longitude"
    assert config.start_date == "1501-01-01"
    assert config.end_date == "1501-12-31"


def test_named_phase_snapshot_with_noleap_calendar() -> None:
    time = xr.date_range(
        "1501-01-01", periods=8, freq="6h", calendar="noleap", use_cftime=True
    )
    phase = xr.DataArray(
        np.arange(8 * 3 * 4).reshape(8, 3, 4),
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": [30.0, 40.0, 50.0], "lon": [0.0, 90.0, 180.0, 270.0]},
    )
    result = xr.Dataset({"phase": phase})
    selected = _phase_snapshot(result, "1501-01-01T12:00:00")
    assert selected.time.dt.hour.item() == 12


def test_speed_summaries_preserve_snapshot_masks() -> None:
    """Plot summaries must not union sparse masks across time."""

    time = np.arange(
        np.datetime64("2001-01-01T00"),
        np.datetime64("2001-01-01T18"),
        np.timedelta64(6, "h"),
    )
    coordinates = {"time": time, "lat": [40.0, 50.0], "lon": [0.0, 90.0]}
    shape = (3, 2, 2)
    phase_speed = np.full(shape, np.nan)
    cgx = np.full(shape, np.nan)
    cgy = np.full(shape, np.nan)
    phase_speed[0, 0, 0] = 5.0
    phase_speed[1, 1, 1] = 6.0
    phase_speed[2, 0, 1] = 7.0
    cgx[0, 0, 0] = cgy[0, 0, 0] = 2.0
    cgx[1, 1, 1] = cgy[1, 1, 1] = 3.0
    cgx[2, 0, 1] = cgy[2, 0, 1] = 4.0
    result = xr.Dataset(
        {
            "amplitude": (("time", "lat", "lon"), np.ones(shape)),
            "phase": (("time", "lat", "lon"), np.zeros(shape)),
            "phase_speed": (("time", "lat", "lon"), phase_speed),
            "group_velocity_zonal": (("time", "lat", "lon"), cgx),
            "group_velocity_meridional": (("time", "lat", "lon"), cgy),
        },
        coords=coordinates,
    )

    summary = _case_summary(result, "case", "midpoint")
    assert np.isfinite(summary["phase_speed"]).sum().item() == 1
    assert np.isfinite(summary["cgx"]).sum().item() == 1
    assert summary["phase_speed"].sel(lat=50.0, lon=90.0).item() == 6.0


def test_driver_help_dictionary_covers_every_option() -> None:
    option_keys = {
        action.dest
        for action in _parser()._actions
        if action.dest != "help"
    }
    assert option_keys == set(DRIVER_HELP)
