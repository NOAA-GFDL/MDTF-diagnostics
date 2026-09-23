#!/usr/bin/env python3
"""Create the standard Rossby wave packet POD summary figures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import xarray as xr

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _finite_values(fields: list[xr.DataArray]) -> np.ndarray:
    values = [np.asarray(field.values)[np.isfinite(field.values)] for field in fields]
    values = [value for value in values if value.size]
    return np.concatenate(values) if values else np.array([], dtype=float)


def _plot_scalar_cases(
    summaries: list[dict[str, Any]],
    field_name: str,
    title: str,
    color_label: str,
    target: Path,
) -> None:
    fields = [summary[field_name] for summary in summaries]
    values = _finite_values(fields)
    if field_name == "phase":
        cmap, vmin, vmax = "viridis", -np.pi, np.pi
    elif field_name == "amplitude":
        cmap = "RdBu_r"
        vmin = float(np.nanpercentile(values, 2)) if values.size else 0.0
        vmax = float(np.nanpercentile(values, 98)) if values.size else 1.0
    else:
        cmap = "RdBu_r"
        bound = float(np.nanpercentile(np.abs(values), 98)) if values.size else 1.0
        vmin, vmax = -bound, bound
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        vmin, vmax = (0.0, 1.0) if field_name == "amplitude" else (-1.0, 1.0)

    figure, axes = plt.subplots(
        len(summaries),
        1,
        figsize=(12.0, max(3.0, 2.7 * len(summaries))),
        squeeze=False,
        constrained_layout=True,
    )
    image = None
    for axis, summary, field in zip(axes[:, 0], summaries, fields):
        image = axis.pcolormesh(
            field.lon,
            field.lat,
            field,
            shading="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )
        subtitle = summary["label"]
        if field_name in {"phase", "phase_speed"}:
            subtitle += f"; snapshot {summary['phase_time']}"
        axis.set(
            title=subtitle,
            xlabel="Longitude (degrees east)",
            ylabel="Latitude (degrees north)",
        )
        axis.set_xlim(float(field.lon.min()), float(field.lon.max()))
    if image is not None:
        figure.colorbar(
            image,
            ax=axes[:, 0].tolist(),
            orientation="horizontal",
            shrink=0.78,
            pad=0.08,
            label=color_label,
        )
    figure.suptitle(title)
    figure.savefig(target, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _plot_group_velocity(summaries: list[dict[str, Any]], target: Path) -> None:
    available = [summary for summary in summaries if "cgx" in summary and "cgy" in summary]
    if not available:
        return
    magnitudes = [np.hypot(summary["cgx"], summary["cgy"]) for summary in available]
    values = _finite_values(magnitudes)
    vmax = float(np.nanpercentile(values, 98)) if values.size else 1.0
    if not np.isfinite(vmax) or vmax <= 0:
        vmax = 1.0

    figure, axes = plt.subplots(
        len(available),
        1,
        figsize=(12.0, max(3.0, 2.8 * len(available))),
        squeeze=False,
        constrained_layout=True,
    )
    image = None
    for axis, summary, magnitude in zip(axes[:, 0], available, magnitudes):
        image = axis.pcolormesh(
            magnitude.lon,
            magnitude.lat,
            magnitude,
            shading="auto",
            cmap="RdBu_r",
            vmin=0.0,
            vmax=vmax,
        )
        step_y = max(1, magnitude.sizes["lat"] // 12)
        step_x = max(1, magnitude.sizes["lon"] // 24)
        axis.quiver(
            magnitude.lon.values[::step_x],
            magnitude.lat.values[::step_y],
            summary["cgx"].values[::step_y, ::step_x],
            summary["cgy"].values[::step_y, ::step_x],
            color="black",
            alpha=0.55,
            pivot="middle",
            scale=700,
            width=0.002,
        )
        axis.set(
            title=f"{summary['label']}; snapshot {summary['phase_time']}",
            xlabel="Longitude (degrees east)",
            ylabel="Latitude (degrees north)",
        )
        axis.set_xlim(float(magnitude.lon.min()), float(magnitude.lon.max()))
    if image is not None:
        figure.colorbar(
            image,
            ax=axes[:, 0].tolist(),
            orientation="horizontal",
            shrink=0.78,
            pad=0.08,
            label="Group-speed magnitude (m s$^{-1}$)",
        )
    figure.suptitle("Rossby wave packet group velocity")
    figure.savefig(target, dpi=150, bbox_inches="tight")
    plt.close(figure)


def summary_plots(
    summaries: list[dict[str, Any]], target_dir: Path, prefix: str
) -> list[Path]:
    """Write the four fixed-name figures used by the POD output page."""

    target_dir.mkdir(parents=True, exist_ok=True)
    targets = {
        "amplitude": target_dir / f"{prefix}_amplitude.png",
        "phase": target_dir / f"{prefix}_phase.png",
        "phase_speed": target_dir / f"{prefix}_phase_speed.png",
        "group_velocity": target_dir / f"{prefix}_group_velocity.png",
    }
    _plot_scalar_cases(
        summaries,
        "amplitude",
        "Rossby wave packet envelope amplitude",
        "Amplitude (m s$^{-1}$)",
        targets["amplitude"],
    )
    _plot_scalar_cases(
        summaries,
        "phase",
        "Rossby wave phase",
        "Phase (radians)",
        targets["phase"],
    )
    _plot_scalar_cases(
        summaries,
        "phase_speed",
        "Rossby wave phase speed",
        "Phase speed (m s$^{-1}$)",
        targets["phase_speed"],
    )
    _plot_group_velocity(summaries, targets["group_velocity"])
    return [target for target in targets.values() if target.exists()]
