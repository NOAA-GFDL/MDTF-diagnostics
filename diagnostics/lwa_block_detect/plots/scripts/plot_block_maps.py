#!/usr/bin/env python3
"""Draw horizontal maps of detected blocking events at their peak dates."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import xarray as xr


BOUNDARY_COLOR = "#2166ac"


def _select_events(
    event_file: Path,
    max_events: int,
    event_ids: list[int] | None,
    representative_types: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    events = pd.read_csv(event_file)
    if event_ids:
        indexed = events.set_index("event_id", drop=False)
        return pd.DataFrame([indexed.loc[event_id] for event_id in event_ids if event_id in indexed.index])
    if representative_types:
        selected = []
        for block_type in representative_types:
            subset = events[events.block_type == block_type]
            if not subset.empty:
                selected.append(subset.sort_values("peak_lwa", ascending=False).iloc[0])
        return pd.DataFrame(selected)
    return events.sort_values("peak_lwa", ascending=False).head(max_events)


def _draw_event(
    axis,
    blocks: xr.Dataset,
    lwa: xr.Dataset,
    row,
    z500: xr.DataArray | None = None,
    add_colorbar: bool = True,
    example_title: bool = False,
) -> None:
    """Draw one detected event on a longitude-latitude horizontal map."""
    time_index = int(row.peak_time_index)
    peak_date = str(row.peak_date).split()[0]
    field = lwa["LWA"].isel(time=time_index).sel(lat=blocks.lat).load()
    mask = blocks["blocking_event_id"].isel(time=time_index).values == int(row.event_id)
    finite = np.asarray(field.values)[np.isfinite(field.values)]
    vmax = float(np.nanpercentile(finite, 98)) if finite.size else 1.0
    image = axis.pcolormesh(
        field.lon,
        field.lat,
        field,
        shading="auto",
        cmap="YlOrRd",
        vmin=0,
        vmax=max(vmax, 1.0),
    )
    legend_handles = []
    legend_labels = []
    if z500 is not None:
        height = z500.isel(time=time_index).sel(lat=blocks.lat, lon=blocks.lon).load()
        finite_height = np.asarray(height.values)[np.isfinite(height.values)]
        if finite_height.size:
            low, high = np.nanpercentile(finite_height, [5, 95])
            spacing = 100.0 if high - low < 2000.0 else 200.0
            levels = np.arange(np.floor(low / spacing) * spacing, high + spacing, spacing)
            axis.contour(
                height.lon,
                height.lat,
                height,
                levels=levels,
                colors="#303030",
                linewidths=0.65,
                alpha=0.85,
            )
            legend_handles.append(Line2D([0], [0], color="#303030", linewidth=0.8))
            legend_labels.append(f"Z500 ({height.attrs.get('units', 'm')})")
    if np.any(mask):
        axis.contour(
            blocks.lon,
            blocks.lat,
            mask.astype(float),
            levels=[0.5],
            colors=[BOUNDARY_COLOR],
            linewidths=2.0,
        )
        legend_handles.append(Line2D([0], [0], color=BOUNDARY_COLOR, linewidth=2.0))
        legend_labels.append("detected event boundary")
    if legend_handles:
        axis.legend(legend_handles, legend_labels, loc="upper right", fontsize=8, framealpha=0.85)
    axis.scatter(
        row.peak_lon_degrees_east,
        row.peak_lat_degrees_north,
        marker="*",
        s=95,
        color=BOUNDARY_COLOR,
        edgecolor="black",
        linewidth=0.45,
        zorder=4,
    )
    axis.set(
        xlabel="Longitude (°E)",
        ylabel="Latitude (°N)",
        xlim=(float(blocks.lon.min()), float(blocks.lon.max())),
        ylim=(float(blocks.lat.min()), float(blocks.lat.max())),
        title=(
            f"{row.block_type.capitalize()} blocking ({peak_date})"
            if example_title
            else (
                f"Event {row.event_id}: {row.block_type}; {peak_date}\n"
                f"{row.duration_days} days; {row.peak_area_km2 / 1.0e6:.2f} million km²"
            )
        ),
    )
    axis.grid(alpha=0.2)
    if add_colorbar:
        axis.figure.colorbar(image, ax=axis, label="Total local wave activity")


def plot_event_summary(
    blocking_file: Path,
    lwa_file: Path,
    event_file: Path,
    output_file: Path,
    max_events: int = 6,
    event_ids: list[int] | None = None,
    z500: xr.DataArray | None = None,
) -> None:
    """Write a browser-ready 2-by-1 ridge and dipole example figure."""
    events = _select_events(
        event_file, max_events, event_ids,
        representative_types=None if event_ids else ("ridge", "dipole"),
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    ncols = 1
    nrows = max(1, len(events))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.5, 4.5 * nrows), squeeze=False)
    flat_axes = axes.ravel()
    hemisphere = ""
    with xr.open_dataset(blocking_file) as blocks, xr.open_dataset(lwa_file) as lwa:
        hemisphere = str(blocks.attrs.get("hemisphere", ""))
        if events.empty:
            flat_axes[0].text(
                0.5, 0.5, "No blocking events met the detection criteria",
                ha="center", va="center", transform=flat_axes[0].transAxes,
            )
            flat_axes[0].set_axis_off()
        else:
            for axis, row in zip(flat_axes, events.itertuples(index=False)):
                _draw_event(axis, blocks, lwa, row, z500=z500, add_colorbar=True, example_title=True)
        for axis in flat_axes[len(events) if len(events) else 1:]:
            axis.set_axis_off()
    if not hemisphere and not events.empty:
        hemisphere = str(events.iloc[0].hemisphere)
    fig.suptitle("Example blocking events", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_atlas(
    blocking_file: Path,
    lwa_file: Path,
    event_file: Path,
    output_file: Path,
    max_events: int = 12,
    event_ids: list[int] | None = None,
    z500: xr.DataArray | None = None,
) -> None:
    """Write one peak-date horizontal map per selected blocking event."""
    events = _select_events(event_file, max_events, event_ids)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with xr.open_dataset(blocking_file) as blocks, xr.open_dataset(lwa_file) as lwa, PdfPages(output_file) as pdf:
        if events.empty:
            fig, axis = plt.subplots(figsize=(9, 4.8))
            axis.text(0.5, 0.5, "No blocking events selected", ha="center", va="center")
            axis.set_axis_off()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            return
        for row in events.itertuples(index=False):
            fig, axis = plt.subplots(figsize=(10, 5.2))
            _draw_event(axis, blocks, lwa, row, z500=z500, add_colorbar=True)
            fig.tight_layout()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking-file", type=Path, required=True)
    parser.add_argument("--lwa-file", type=Path, required=True)
    parser.add_argument("--z500-file", type=Path)
    parser.add_argument("--z500-variable", default="Z500")
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-events", type=int, default=12, help="Strongest events to draw when IDs are omitted")
    parser.add_argument(
        "--event-id", type=int, action="append", dest="event_ids",
        help="Specific event ID; repeat as needed",
    )
    args = parser.parse_args()
    if args.z500_file:
        with xr.open_dataset(args.z500_file) as z500_source:
            plot_event_atlas(
                args.blocking_file,
                args.lwa_file,
                args.events,
                args.output,
                max_events=args.max_events,
                event_ids=args.event_ids,
                z500=z500_source[args.z500_variable],
            )
    else:
        plot_event_atlas(
            args.blocking_file,
            args.lwa_file,
            args.events,
            args.output,
            max_events=args.max_events,
            event_ids=args.event_ids,
        )


if __name__ == "__main__":
    main()
