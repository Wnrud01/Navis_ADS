"""
Waymo Open Dataset (WOMD) 20-Second Scenario Renderer
====================================================
Extracts and visualizes vector roadmaps (lanes, road lines, edges, crosswalks, stop signs)
and dynamic track states (Ego vehicle, surrounding vehicles, pedestrians, cyclists) directly
from Waymo Scenario TFRecord files into high-quality GIF animations.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
import tensorflow as tf

# Default scenario TFRecord file and output GIF path inside Navis_ADS repo
DEFAULT_TFRECORD = Path("data/uncompressed_scenario_training_20s_training_20s.tfrecord-00001-of-01000")
DEFAULT_OUTPUT_GIF = Path("outputs/waymo_scenario_rendering.gif")

# Color Palette for Object Types
TYPE_COLORS = {
    1: "#f59e0b",  # Vehicle (Amber/Orange)
    2: "#ef4444",  # Pedestrian (Red)
    3: "#22c55e",  # Cyclist (Green)
    4: "#a855f7",  # Other (Purple)
}


def resolve_path(path_str: str) -> str:
    """
    Converts Windows paths (e.g. C:/Users/...) to Linux/WSL paths (/mnt/c/Users/...) if running on POSIX.
    """
    if os.name == 'posix' and (path_str.startswith('C:') or path_str.startswith('c:')):
        clean = path_str.replace('\\', '/')
        return '/mnt/c' + clean[2:]
    return path_str


def load_first_scenario_proto(tfrecord_path: str):
    """
    Loads and parses the first serialized Scenario proto from a Waymo TFRecord file.
    """
    resolved_path = resolve_path(tfrecord_path)
    if not Path(resolved_path).is_file():
        raise FileNotFoundError(f"TFRecord file not found at: {resolved_path}")

    from waymo_open_dataset.protos import scenario_pb2

    serialized = next(iter(tf.data.TFRecordDataset(resolved_path)))
    scenario = scenario_pb2.Scenario()
    scenario.ParseFromString(serialized.numpy())
    return scenario


def calculate_scenario_bounds(scenario) -> tuple[float, float, float, float]:
    """
    Calculates a square global-coordinate bounding viewport covering the map and object tracks.
    """
    xs: list[float] = []
    ys: list[float] = []

    # Collect map geometry points
    for feature in scenario.map_features:
        kind = feature.WhichOneof("feature_data")
        if kind in ("lane", "road_line", "road_edge"):
            for p in getattr(feature, kind).polyline:
                xs.append(p.x)
                ys.append(p.y)
        elif kind in ("crosswalk", "speed_bump", "driveway"):
            for p in getattr(feature, kind).polygon:
                xs.append(p.x)
                ys.append(p.y)
        elif kind == "stop_sign":
            xs.append(feature.stop_sign.position.x)
            ys.append(feature.stop_sign.position.y)

    # Collect valid object track positions
    for track in scenario.tracks:
        for state in track.states:
            if state.valid:
                xs.append(state.center_x)
                ys.append(state.center_y)

    if not xs or not ys:
        return (-50.0, 50.0, -50.0, 50.0)

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    side = max(max_x - min_x, max_y - min_y, 20.0) * 1.08
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    half_side = side / 2.0

    return (
        center_x - half_side,
        center_x + half_side,
        center_y - half_side,
        center_y + half_side,
    )


def draw_vector_map(ax, scenario) -> None:
    """
    Draws static vector-map layers: lanes, road lines, road edges, crosswalks, stop signs.
    """
    for feature in scenario.map_features:
        kind = feature.WhichOneof("feature_data")
        if kind == "lane":
            points = feature.lane.polyline
            color, width, style = "#6b7280", 0.7, "-"
        elif kind == "road_line":
            points = feature.road_line.polyline
            color, width, style = "#9ca3af", 0.55, "-"
        elif kind == "road_edge":
            points = feature.road_edge.polyline
            color, width, style = "#374151", 0.8, "-"
        elif kind in ("crosswalk", "speed_bump", "driveway"):
            points = getattr(feature, kind).polygon
            color, width, style = "#d1d5db", 0.55, "-"
        elif kind == "stop_sign":
            ax.scatter(
                feature.stop_sign.position.x,
                feature.stop_sign.position.y,
                s=12,
                c="#dc2626",
                marker="o",
                zorder=2,
            )
            continue
        else:
            continue

        if len(points) >= 2:
            xy = np.array([(p.x, p.y) for p in points])
            ax.plot(
                xy[:, 0], xy[:, 1], color=color, linewidth=width,
                linestyle=style, alpha=0.9, zorder=1,
            )


def get_vehicle_corners(state) -> np.ndarray:
    """
    Computes the 4 oriented 2D bounding box corners of an object given its length, width, heading, and center.
    """
    half_length = max(float(state.length), 0.5) / 2.0
    half_width = max(float(state.width), 0.3) / 2.0
    corners = np.array([
        [half_length, half_width],
        [half_length, -half_width],
        [-half_length, -half_width],
        [-half_length, half_width],
    ])
    cos_h = np.cos(state.heading)
    sin_h = np.sin(state.heading)
    rot = np.array([[cos_h, -sin_h], [sin_h, cos_h]])
    return corners @ rot.T + np.array([state.center_x, state.center_y])


def draw_object_tracks(ax, scenario, timestep: int) -> None:
    """
    Draws object bounding box polygons and recent motion trails up to the current timestep.
    """
    history_start = max(0, timestep - 10)
    for track_idx, track in enumerate(scenario.tracks):
        if timestep >= len(track.states):
            continue
        state = track.states[timestep]
        if not state.valid:
            continue

        # Color: Cyan for SDC (Ego vehicle), TYPE_COLORS for others
        is_sdc = (track_idx == scenario.sdc_track_index)
        color = "#06b6d4" if is_sdc else TYPE_COLORS.get(track.object_type, "#94a3b8")

        # Motion trail
        history = [s for s in track.states[history_start : timestep + 1] if s.valid]
        if len(history) >= 2:
            ax.plot(
                [s.center_x for s in history],
                [s.center_y for s in history],
                color=color,
                linewidth=1.2 if is_sdc else 0.8,
                alpha=0.6,
                zorder=3,
            )

        # Bounding Box Polygon
        patch = Polygon(
            get_vehicle_corners(state),
            closed=True,
            facecolor=color,
            edgecolor="#111827",
            linewidth=0.5 if is_sdc else 0.35,
            alpha=0.95 if is_sdc else 0.85,
            zorder=4,
        )
        ax.add_patch(patch)


def render_scenario_frame(scenario, timestep: int, bounds: tuple[float, float, float, float], fig_size=(6, 6), dpi=100) -> np.ndarray:
    """
    Renders a single frame at the given timestep into an RGB numpy array.
    """
    fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")

    draw_vector_map(ax, scenario)
    draw_object_tracks(ax, scenario, timestep)

    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_aspect("equal", adjustable="box")

    timestamp = scenario.timestamps_seconds[timestep]
    ax.set_title(
        f"Waymo Scenario {scenario.scenario_id}  |  t = {timestamp:.1f}s (Step {timestep+1}/{len(scenario.timestamps_seconds)})",
        fontsize=9,
        fontweight="bold"
    )
    ax.set_xlabel("Global X (m)", fontsize=8)
    ax.set_ylabel("Global Y (m)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(True, linestyle=":", color="#cbd5e1", alpha=0.5)

    fig.tight_layout(pad=0.8)
    fig.canvas.draw()
    image = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return image


def render_scenario_to_gif(
    tfrecord_path: str,
    output_gif_path: str,
    fps: int = 10,
    max_frames: int | None = None
) -> str:
    """
    Full pipeline to parse scenario TFRecord, render all timesteps, and export as GIF.
    """
    print(f"[Scenario Renderer] Loading TFRecord: {tfrecord_path}")
    scenario = load_first_scenario_proto(tfrecord_path)
    bounds = calculate_scenario_bounds(scenario)

    total_timesteps = len(scenario.timestamps_seconds)
    if max_frames is not None:
        total_timesteps = min(total_timesteps, max_frames)

    print(f"[Scenario Renderer] Scenario ID: {scenario.scenario_id}")
    print(f"[Scenario Renderer] Total Tracks: {len(scenario.tracks)}, Map Features: {len(scenario.map_features)}")
    print(f"[Scenario Renderer] Rendering {total_timesteps} frames at {fps} FPS...")

    frames = []
    for t in range(total_timesteps):
        frame_img = render_scenario_frame(scenario, t, bounds)
        frames.append(frame_img)
        if (t + 1) % 20 == 0 or t == total_timesteps - 1:
            print(f"  Processed frame {t + 1} / {total_timesteps}")

    output_path = Path(resolve_path(output_gif_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gif_images = [Image.fromarray(f) for f in frames]
    gif_images[0].save(
        output_path,
        save_all=True,
        append_images=gif_images[1:],
        duration=1000 // fps,
        loop=0,
        optimize=False
    )
    print(f"[Scenario Renderer] GIF successfully saved to: {output_path.resolve()}")
    return str(output_path.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Navis ADS - Waymo Scenario TFRecord Renderer")
    parser.add_argument("--tfrecord_path", type=str, default=str(DEFAULT_TFRECORD), help="Path to Waymo scenario TFRecord")
    parser.add_argument("--output_gif", type=str, default=str(DEFAULT_OUTPUT_GIF), help="Output path for the generated GIF")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second")
    parser.add_argument("--max_frames", type=int, default=None, help="Maximum number of frames to render")

    args = parser.parse_args()
    render_scenario_to_gif(args.tfrecord_path, args.output_gif, args.fps, args.max_frames)
