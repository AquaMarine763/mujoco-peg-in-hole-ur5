from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from math import asin, cos, pi, sin
from pathlib import Path
from typing import Callable

import numpy as np


DEFAULT_PROFILES = ("rectangular_key", "square_square", "triangle_triangle", "hex_hex")
DEFAULT_YAW_DEG = (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0)
DEFAULT_CLEARANCE_MM = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
PEG_RADIUS = 0.012
KEY_PEG_TAB_HALF_WIDTH = 0.005
KEY_PEG_TAB_LENGTH = 0.0065


@dataclass(frozen=True)
class ShapeSpec:
    profile: str
    peg_boundary: np.ndarray
    hole_score: Callable[[np.ndarray, float], np.ndarray]
    period_deg: float
    clearance_reference: str


def regular_polygon_points(*, apothem: float, sides: int) -> np.ndarray:
    radius = float(apothem) / cos(pi / float(sides))
    points = []
    for index in range(sides):
        angle = 0.5 * pi + pi / float(sides) + 2.0 * pi * index / float(sides)
        points.append((radius * cos(angle), radius * sin(angle)))
    return np.asarray(points, dtype=np.float64)


def keyhole_points(
    *,
    radius: float,
    tab_half_width: float,
    tab_length: float,
    arc_segments: int,
) -> np.ndarray:
    theta = float(asin(max(-1.0, min(1.0, tab_half_width / radius))))
    x_join = (radius * radius - tab_half_width * tab_half_width) ** 0.5
    front_x = radius + tab_length
    points = [(front_x, tab_half_width), (x_join, tab_half_width)]
    arc_span = 2.0 * pi - 2.0 * theta
    for index in range(1, arc_segments):
        angle = theta + arc_span * index / float(arc_segments)
        points.append((radius * cos(angle), radius * sin(angle)))
    points.extend([(x_join, -tab_half_width), (front_x, -tab_half_width)])
    return np.asarray(points, dtype=np.float64)


def densify_closed_polyline(points: np.ndarray, samples_per_edge: int) -> np.ndarray:
    samples: list[np.ndarray] = []
    count = len(points)
    for index in range(count):
        start = points[index]
        end = points[(index + 1) % count]
        for step in range(samples_per_edge):
            alpha = float(step) / float(samples_per_edge)
            samples.append((1.0 - alpha) * start + alpha * end)
    return np.asarray(samples, dtype=np.float64)


def rotate_points(points: np.ndarray, yaw_rad: float) -> np.ndarray:
    c = cos(yaw_rad)
    s = sin(yaw_rad)
    rot = np.asarray([[c, -s], [s, c]], dtype=np.float64)
    return points @ rot.T


def polygon_inside_score(points: np.ndarray, polygon: np.ndarray) -> np.ndarray:
    scores = []
    signed_area = 0.5 * float(
        np.sum(
            polygon[:, 0] * np.roll(polygon[:, 1], -1)
            - np.roll(polygon[:, 0], -1) * polygon[:, 1]
        )
    )
    ccw = signed_area > 0.0
    for index in range(len(polygon)):
        start = polygon[index]
        end = polygon[(index + 1) % len(polygon)]
        edge = end - start
        length = max(float(np.linalg.norm(edge)), 1e-12)
        rel = points - start
        cross = edge[0] * rel[:, 1] - edge[1] * rel[:, 0]
        signed_distance = cross / length if ccw else -cross / length
        scores.append(signed_distance)
    return np.min(np.vstack(scores), axis=0)


def square_score(points: np.ndarray, clearance: float) -> np.ndarray:
    half = PEG_RADIUS + clearance
    return half - np.max(np.abs(points), axis=1)


def regular_polygon_score(points: np.ndarray, *, peg_apothem: float, sides: int, clearance: float) -> np.ndarray:
    hole = regular_polygon_points(apothem=peg_apothem + clearance, sides=sides)
    return polygon_inside_score(points, hole)


def keyhole_score(points: np.ndarray, clearance: float) -> np.ndarray:
    radius = PEG_RADIUS + clearance
    tab_half_width = KEY_PEG_TAB_HALF_WIDTH + clearance
    tab_length = KEY_PEG_TAB_LENGTH + clearance
    x_join = (radius * radius - tab_half_width * tab_half_width) ** 0.5
    front_x = radius + tab_length

    circle_score = radius - np.linalg.norm(points, axis=1)
    tab_score = np.minimum.reduce(
        [
            points[:, 0] - x_join,
            front_x - points[:, 0],
            tab_half_width - np.abs(points[:, 1]),
        ]
    )
    return np.maximum(circle_score, tab_score)


def build_shape_specs(samples_per_edge: int) -> dict[str, ShapeSpec]:
    square = np.asarray(
        [
            (PEG_RADIUS, PEG_RADIUS),
            (-PEG_RADIUS, PEG_RADIUS),
            (-PEG_RADIUS, -PEG_RADIUS),
            (PEG_RADIUS, -PEG_RADIUS),
        ],
        dtype=np.float64,
    )
    hex_apothem = PEG_RADIUS * cos(pi / 6.0)
    triangle_apothem = PEG_RADIUS * cos(pi / 3.0)
    hexagon = regular_polygon_points(apothem=hex_apothem, sides=6)
    triangle = regular_polygon_points(apothem=triangle_apothem, sides=3)
    keyhole = keyhole_points(
        radius=PEG_RADIUS,
        tab_half_width=KEY_PEG_TAB_HALF_WIDTH,
        tab_length=KEY_PEG_TAB_LENGTH,
        arc_segments=48,
    )

    return {
        "square_square": ShapeSpec(
            profile="square_square",
            peg_boundary=densify_closed_polyline(square, samples_per_edge),
            hole_score=square_score,
            period_deg=90.0,
            clearance_reference="hole half-size - peg half-size",
        ),
        "hex_hex": ShapeSpec(
            profile="hex_hex",
            peg_boundary=densify_closed_polyline(hexagon, samples_per_edge),
            hole_score=lambda points, clearance: regular_polygon_score(
                points,
                peg_apothem=hex_apothem,
                sides=6,
                clearance=clearance,
            ),
            period_deg=60.0,
            clearance_reference="hole apothem - peg apothem",
        ),
        "triangle_triangle": ShapeSpec(
            profile="triangle_triangle",
            peg_boundary=densify_closed_polyline(triangle, samples_per_edge),
            hole_score=lambda points, clearance: regular_polygon_score(
                points,
                peg_apothem=triangle_apothem,
                sides=3,
                clearance=clearance,
            ),
            period_deg=120.0,
            clearance_reference="hole apothem - peg apothem",
        ),
        "rectangular_key": ShapeSpec(
            profile="rectangular_key",
            peg_boundary=densify_closed_polyline(keyhole, samples_per_edge),
            hole_score=keyhole_score,
            period_deg=360.0,
            clearance_reference="uniform 2D offset of keyhole radius/tab dimensions",
        ),
    }


def parse_float_list(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analytically scan same-shape peg/hole yaw sensitivity. "
            "This isolates whether a proposed clearance makes yaw alignment necessary."
        )
    )
    parser.add_argument("--profiles", default=",".join(DEFAULT_PROFILES))
    parser.add_argument("--yaw-deg", default=",".join(str(v) for v in DEFAULT_YAW_DEG))
    parser.add_argument(
        "--clearance-mm",
        default=",".join(str(v) for v in DEFAULT_CLEARANCE_MM),
    )
    parser.add_argument("--samples-per-edge", type=int, default=80)
    parser.add_argument("--good-yaw-deg", type=float, default=2.0)
    parser.add_argument("--bad-yaw-deg", type=float, default=8.0)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/shape_yaw_sensitivity_scan.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/shape_yaw_sensitivity_scan.md"),
    )
    return parser.parse_args()


def scan(args: argparse.Namespace) -> list[dict[str, object]]:
    specs = build_shape_specs(samples_per_edge=args.samples_per_edge)
    profiles = tuple(item.strip() for item in args.profiles.split(",") if item.strip())
    yaws_deg = parse_float_list(args.yaw_deg)
    clearances_m = tuple(value / 1000.0 for value in parse_float_list(args.clearance_mm))

    rows: list[dict[str, object]] = []
    for profile in profiles:
        if profile not in specs:
            raise ValueError(f"unsupported profile: {profile}")
        spec = specs[profile]
        for clearance in clearances_m:
            for yaw_deg in yaws_deg:
                canonical_yaw_deg = abs(((yaw_deg + 0.5 * spec.period_deg) % spec.period_deg) - 0.5 * spec.period_deg)
                rotated = rotate_points(spec.peg_boundary, np.deg2rad(canonical_yaw_deg))
                scores = spec.hole_score(rotated, clearance)
                min_margin = float(np.min(scores))
                rows.append(
                    {
                        "profile": profile,
                        "clearance_mm": clearance * 1000.0,
                        "yaw_error_deg": yaw_deg,
                        "canonical_yaw_error_deg": canonical_yaw_deg,
                        "period_deg": spec.period_deg,
                        "passes_geometry": bool(min_margin >= -1e-7),
                        "min_margin_mm": min_margin * 1000.0,
                        "clearance_reference": spec.clearance_reference,
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]], *, good_yaw_deg: float, bad_yaw_deg: float) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["profile"]), float(row["clearance_mm"]))
        grouped.setdefault(key, []).append(row)

    summary = []
    for (profile, clearance_mm), group in sorted(grouped.items()):
        good_rows = [row for row in group if float(row["yaw_error_deg"]) <= good_yaw_deg]
        bad_rows = [row for row in group if float(row["yaw_error_deg"]) >= bad_yaw_deg]
        all_good_pass = bool(good_rows) and all(bool(row["passes_geometry"]) for row in good_rows)
        any_bad_pass = any(bool(row["passes_geometry"]) for row in bad_rows)
        max_passing_yaw = max(
            (float(row["yaw_error_deg"]) for row in group if bool(row["passes_geometry"])),
            default=float("nan"),
        )
        min_failing_yaw = min(
            (float(row["yaw_error_deg"]) for row in group if not bool(row["passes_geometry"])),
            default=float("nan"),
        )
        summary.append(
            {
                "profile": profile,
                "clearance_mm": clearance_mm,
                "good_yaw_deg": good_yaw_deg,
                "bad_yaw_deg": bad_yaw_deg,
                "all_good_yaw_pass": all_good_pass,
                "any_bad_yaw_pass": any_bad_pass,
                "discriminative": all_good_pass and not any_bad_pass,
                "max_passing_yaw_deg": max_passing_yaw,
                "min_failing_yaw_deg": min_failing_yaw,
            }
        )
    return summary


def write_markdown(path: Path, rows: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shape Yaw Sensitivity Scan",
        "",
        "This is an analytic 2D cross-section scan. It does not use visual-only debug highlights",
        "and does not run the policy. The purpose is to pick clearances where yaw alignment",
        "becomes necessary before building the visual yaw estimator and guarded yaw-align phase.",
        "",
        "A `discriminative` clearance means all tested small yaw errors pass while all tested",
        "large yaw errors fail under the configured good/bad yaw thresholds.",
        "",
        "## Summary",
        "",
        "| profile | clearance mm | discriminative | max passing yaw deg | min failing yaw deg |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {profile} | {clearance_mm:.2f} | {discriminative} | {max_passing_yaw_deg:.2f} | {min_failing_yaw_deg:.2f} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Detailed Rows",
            "",
            "| profile | clearance mm | yaw error deg | pass | min margin mm | period deg |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            "| {profile} | {clearance_mm:.2f} | {yaw_error_deg:.2f} | {passes_geometry} | {min_margin_mm:.3f} | {period_deg:.0f} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.samples_per_edge < 4:
        raise ValueError("--samples-per-edge must be at least 4")
    rows = scan(args)
    summary = summarize(rows, good_yaw_deg=args.good_yaw_deg, bad_yaw_deg=args.bad_yaw_deg)
    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, rows, summary)
    print(f"saved CSV report to {args.output_csv}")
    print(f"saved Markdown report to {args.output_md}")
    for row in summary:
        if row["discriminative"]:
            print(
                "candidate {profile}: clearance={clearance_mm:.2f}mm max_pass={max_passing_yaw_deg:.2f}deg min_fail={min_failing_yaw_deg:.2f}deg".format(
                    **row
                )
            )


if __name__ == "__main__":
    main()
