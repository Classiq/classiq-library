#!/usr/bin/env python3
"""
Plot aggregated cluster benchmark results using sinter.plot_error_rate.

Loads aggregated_results.csv, converts to sinter.TaskStats, and produces
the qubit-scaling plot (error rate per round vs qubits) with proper
uncertainty bands and styling.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, MultipleLocator
import pandas as pd
import sinter

try:
    from adjustText import adjust_text

    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Point label styling
POINT_LABEL_FONTSIZE = 14  # slightly larger than default
POINT_LABEL_PATTERN = re.compile(r"^d=(\d+)$")


def compute_qubit_count(d: int, circuit_type: str) -> int:
    """Total qubits for triangular color code: data + aux_per_plaquette * num_plaquettes."""
    data_qubits = (3 * d * d + 1) // 4
    num_plaquettes = 3 * (d * d - 1) // 8
    if circuit_type == "superdense":
        aux_per_plaquette = 2
    elif circuit_type in ("tri_optimal", "optimized_parallel"):
        aux_per_plaquette = 1
    elif circuit_type == "midout":
        aux_per_plaquette = 0
    else:
        aux_per_plaquette = 1
    return data_qubits + aux_per_plaquette * num_plaquettes


def df_to_task_stats(df: pd.DataFrame) -> list:
    """Convert aggregated DataFrame rows to sinter.TaskStats for plotting."""
    stats = []
    for _, row in df.iterrows():
        d, r = int(row["distance"]), int(row["rounds"])
        ct = row["circuit_type"]
        num_qubits = compute_qubit_count(d, ct)
        meta = {
            "d": d,
            "r": r,
            "p": float(row["p_cnot"]),
            "circuit_type": ct,
            "num_qubits": num_qubits,
        }
        stat = sinter.TaskStats(
            strong_id=f"{d}_{ct}_{row['p_cnot']}_{row['decoder']}",
            decoder=row["decoder"],
            json_metadata=meta,
            shots=int(row["shots_used"]),
            errors=int(row["errors"]),
            discards=0,
            seconds=(
                float(row["decode_time"]) if pd.notna(row.get("decode_time")) else 0
            ),
        )
        stats.append(stat)
    return stats


# Circuit type styling (match benchmark_circuits.plot_error_vs_qubits)
CIRCUIT_COLORS = {
    "optimized_parallel": "#2ecc71",
    "tri_optimal": "#3498db",
    "midout": "#e74c3c",
    "superdense": "#9b59b6",
}
CIRCUIT_MARKERS = {
    "optimized_parallel": "o",
    "tri_optimal": "s",
    "midout": "^",
    "superdense": "D",
}
CIRCUIT_LABELS = {
    "midout": "middle-out (0 aux. per plaq.)",
    "superdense": "superdense (2 aux. per plaq.)",
    "tri_optimal": "tri-optimal (1 aux. per plaq.)",
    "optimized_parallel": "color-dependent (1 aux. per plaq.)",
}
# Label to show in bold in the legend (optimized_parallel)
LEGEND_BOLD_LABEL = CIRCUIT_LABELS["optimized_parallel"]
LEGEND_ORDER = ["midout", "superdense", "tri_optimal", "optimized_parallel"]


def _get_legend_handles_labels(axes):
    """Get legend handles/labels from axis labeled artists, or from existing legend, or proxy artists."""
    # Try labeled artists on first axis (works even if no legend was created)
    if axes.size > 0:
        ax = axes.flat[0]
        handles, labels = ax.get_legend_handles_labels()
        if handles and labels:
            return handles, labels
        # Fallback: from first existing legend
        leg = ax.get_legend()
        if leg is not None:
            return list(leg.legend_handles), [t.get_text() for t in leg.get_texts()]
    # Fallback: proxy artists so legend always appears
    handles = [
        Line2D(
            [0],
            [0],
            color=CIRCUIT_COLORS.get(ct, "#333333"),
            marker=CIRCUIT_MARKERS.get(ct, "o"),
            linestyle="",
            markersize=10,
            label=CIRCUIT_LABELS.get(ct, ct),
        )
        for ct in LEGEND_ORDER
    ]
    return handles, [CIRCUIT_LABELS.get(ct, ct) for ct in LEGEND_ORDER]


def group_func(stat: sinter.TaskStats) -> dict:
    """Return curve styling dict for sinter.plot_error_rate (label, color, marker, sort)."""
    ct = stat.json_metadata["circuit_type"]
    sort_idx = LEGEND_ORDER.index(ct) if ct in LEGEND_ORDER else 99
    return {
        "label": CIRCUIT_LABELS.get(ct, ct),
        "color": CIRCUIT_COLORS.get(ct, "#333333"),
        "marker": CIRCUIT_MARKERS.get(ct, "o"),
        "sort": sort_idx,
    }


def style_point_labels(
    ax,
    subset: list,
    x_func,
    group_func,
    font_size: int = POINT_LABEL_FONTSIZE,
) -> None:
    """
    After sinter.plot_error_rate: color 'd=N' labels by curve, increase font size,
    and adjust positions to avoid overlap (if adjustText is available).
    Match by creation order: sinter plots curves in LEGEND_ORDER, points sorted by x.
    """
    # Build list of (color, x, y) in the exact order sinter creates annotations:
    # group by circuit_type, sort groups by LEGEND_ORDER, within group sort by x_func
    by_circuit = {}
    for s in subset:
        ct = s.json_metadata["circuit_type"]
        by_circuit.setdefault(ct, []).append(s)
    ordered_colors_and_xy = []
    for ct in LEGEND_ORDER:
        if ct not in by_circuit:
            continue
        for s in sorted(by_circuit[ct], key=x_func):
            g = group_func(s)
            color = g.get("color", "#333333") if isinstance(g, dict) else "#333333"
            x_val = float(x_func(s))
            # y for label position (best estimate; sinter uses fit.best or similar)
            err = (
                (s.errors + 0.5) / (s.shots * s.json_metadata["r"])
                if s.shots and s.json_metadata.get("r")
                else 1e-10
            )
            ordered_colors_and_xy.append((color, x_val, err))

    # Annotations are in creation order (ax.texts = order added)
    point_label_texts = []
    label_xy = []
    texts = [
        t for t in ax.texts if POINT_LABEL_PATTERN.match((t.get_text() or "").strip())
    ]
    n = min(len(texts), len(ordered_colors_and_xy))
    for i in range(n):
        obj = texts[i]
        color, x_val, y_val = ordered_colors_and_xy[i]
        obj.set_color(color)
        obj.set_fontsize(font_size)
        obj.set_fontweight("bold")
        point_label_texts.append(obj)
        label_xy.append((x_val, y_val))

    if point_label_texts and HAS_ADJUST_TEXT and len(point_label_texts) > 1:
        ax.figure.canvas.draw_idle()
        xs = np.array([p[0] for p in label_xy])
        ys = np.array([p[1] for p in label_xy])
        adjust_text(
            point_label_texts,
            x=xs,
            y=ys,
            ax=ax,
            expand_points=(1.2, 1.2),
            expand_text=(1.2, 1.2),
            force_text=(0.5, 0.5),
            force_points=(0.2, 0.2),
            arrowprops=dict(arrowstyle="-", color="none", lw=0),  # no visible arrows
        )


def fit_and_extrapolate(
    stats_by_circuit: dict,
    target_log_err: float = -12 * np.log(10),
) -> dict:
    """
    For each circuit_type, fit y = log(phys_err_rate) vs x = sqrt(qubits) using the two
    highest-distance points (or one point with fallback slope from other curves). Uses
    (errors+0.5)/(shots*r) when errors=0 so 0-error points can be fitted. Returns
    dict ct -> {a, b, x_at_target, xs}.
    """
    # Pass 1: all curves with >= 2 valid points
    result = {}
    for ct, points in stats_by_circuit.items():
        sorted_pts = sorted(
            points,
            key=lambda s: (s.json_metadata["num_qubits"], s.json_metadata["d"]),
            reverse=True,
        )
        if len(sorted_pts) < 2:
            continue
        top2 = sorted_pts[:2]
        xs = np.array([np.sqrt(s.json_metadata["num_qubits"]) for s in top2])
        err_per_round = [
            (s.errors + 0.5) / (s.shots * s.json_metadata["r"])
            for s in top2
            if s.shots > 0 and s.json_metadata["r"] > 0
        ]
        if len(err_per_round) < 2:
            continue
        ys = np.log(err_per_round)
        a = (ys[1] - ys[0]) / (xs[1] - xs[0]) if xs[1] != xs[0] else 0
        b = ys[0] - a * xs[0]
        x_at_target = (target_log_err - b) / a if a != 0 else None
        result[ct] = {"a": a, "b": b, "x_at_target": x_at_target, "xs": xs}
    # Fallback slope from 2-point fits (for 1-point curves)
    fallback_slope = np.mean([f["a"] for f in result.values()]) if result else None
    # Pass 2: 1-point curves
    for ct, points in stats_by_circuit.items():
        if ct in result:
            continue
        sorted_pts = sorted(
            points,
            key=lambda s: (s.json_metadata["num_qubits"], s.json_metadata["d"]),
            reverse=True,
        )
        if len(sorted_pts) < 1 or fallback_slope is None:
            continue
        s0 = sorted_pts[0]
        if s0.shots <= 0 or s0.json_metadata["r"] <= 0:
            continue
        x0 = np.sqrt(s0.json_metadata["num_qubits"])
        err0 = (s0.errors + 0.5) / (s0.shots * s0.json_metadata["r"])
        y0 = np.log(err0)
        a, b = fallback_slope, y0 - fallback_slope * x0
        x_at_target = (target_log_err - b) / a if a != 0 else None
        result[ct] = {"a": a, "b": b, "x_at_target": x_at_target, "xs": np.array([x0])}
    return result


def _sanitize_noise_model_for_path(name: str) -> str:
    """Make noise_model safe for use in filenames."""
    if name is None:
        return "all"
    return re.sub(r"[^\w\-.]", "_", str(name))


def _plot_one_noise_model(
    df: pd.DataFrame,
    plot_opts: dict,
    output_path: str | None,
    show_after: bool,
) -> None:
    """Build and optionally save/show the two figures for one dataframe subset."""
    stats = df_to_task_stats(df)
    error_rates = sorted(df["p_cnot"].unique())
    n_plots = len(error_rates)
    if n_plots == 0:
        return

    fig_simple, axes_simple = plt.subplots(
        1, n_plots, figsize=(10 * n_plots, 10), squeeze=False
    )
    axes_simple = axes_simple.flatten()
    fig_full, axes_full = plt.subplots(
        1, n_plots, figsize=(10 * n_plots, 10), squeeze=False
    )
    axes_full = axes_full.flatten()

    for ax_idx, p_cnot in enumerate(error_rates):
        subset = [s for s in stats if s.json_metadata["p"] == p_cnot]
        if not subset:
            continue

        x_vals = [s.json_metadata["num_qubits"] for s in subset]
        x_min_data = min(x_vals)
        x_max_data = max(x_vals)
        y_vals_approx = [
            s.errors / (s.shots * s.json_metadata["r"])
            for s in subset
            if s.shots > 0 and s.json_metadata["r"] > 0
        ]
        y_min_data = min(y_vals_approx) if y_vals_approx else 1e-5
        y_max_data = max(y_vals_approx) if y_vals_approx else 1e-2

        # ---- Figure 1: data only (no fit, original limits and ticks) ----
        ax = axes_simple[ax_idx]
        sinter.plot_error_rate(ax=ax, stats=subset, **plot_opts)
        ax.set_title(f"p={p_cnot}", fontsize=22)
        ax.set_xscale("function", functions=(np.sqrt, np.square))
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=[1.0], numticks=50))
        all_qubits = sorted({s.json_metadata["num_qubits"] for s in subset})
        ax.set_xticks(all_qubits)
        ax.set_xticklabels([str(int(q)) for q in all_qubits])
        ax.set_xlabel("Total Qubits (sqrt scale)", fontsize=22)
        if ax_idx == 0:
            ax.set_ylabel("Logical Error Rate (per round)", fontsize=22)
        else:
            ax.set_ylabel("")
        ax.tick_params(axis="both", which="major", labelsize=20)
        ax.tick_params(axis="both", which="minor", labelsize=20)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(x_min_data * 0.8, x_max_data * 1.1)
        # ax.set_xlim(0., x_max_data * 1.1)
        ax.set_ylim(y_min_data * 0.5, y_max_data * 2)
        style_point_labels(ax, subset, plot_opts["x_func"], group_func)

        # ---- Figure 2: with fit, extrapolation, extended limits, custom ticks ----
        ax = axes_full[ax_idx]
        sinter.plot_error_rate(ax=ax, stats=subset, **plot_opts)
        ax.set_title(f"p={p_cnot}", fontsize=22)
        ax.set_xscale("function", functions=(np.sqrt, np.square))
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=[1.0], numticks=50))

        by_circuit = defaultdict(list)
        for s in subset:
            by_circuit[s.json_metadata["circuit_type"]].append(s)
        fits = fit_and_extrapolate(by_circuit, target_log_err=np.log(1e-12))

        TARGET_ERR = 1e-12
        x_max_plot = x_max_data
        for fit in fits.values():
            x_at_target = fit.get("x_at_target")
            if x_at_target is not None and x_at_target > 0:
                qubits_at_target = x_at_target**2
                x_max_plot = max(x_max_plot, qubits_at_target * 1.0)

        for ct, fit in fits.items():
            a, b = fit["a"], fit["b"]
            x_at_target = fit.get("x_at_target")
            x_sqrt_min = np.sqrt(x_min_data) * 0.95
            x_sqrt_max = np.sqrt(x_max_plot)
            if x_at_target is not None and x_at_target > np.sqrt(x_min_data):
                x_sqrt_max = max(x_sqrt_max, x_at_target * 1.05)
            x_sqrt_line = np.linspace(x_sqrt_min, x_sqrt_max, 200)
            y_log_line = a * x_sqrt_line + b
            err_line = np.exp(y_log_line)
            color = CIRCUIT_COLORS.get(ct, "#333333")
            ax.plot(
                x_sqrt_line**2,
                np.maximum(err_line, 1e-20),
                color=color,
                linestyle=":",
                alpha=0.5,
                linewidth=1.25,
                zorder=0.5,
            )

        ax.xaxis.set_minor_locator(MultipleLocator(10))
        ax.xaxis.set_major_locator(MultipleLocator(100))

        def _x_label_formatter(x, _pos):
            if x <= 500 and x % 100 == 0:
                return str(int(x))
            if x > 500 and (x - 500) % 200 == 0:
                return str(int(x))
            return ""

        ax.xaxis.set_major_formatter(FuncFormatter(_x_label_formatter))
        ax.set_xlabel("Total Qubits (sqrt scale)", fontsize=22)
        if ax_idx == 0:
            ax.set_ylabel("Logical Error Rate (per round)", fontsize=22)
        else:
            ax.set_ylabel("")
        ax.tick_params(axis="both", which="major", labelsize=20)
        ax.tick_params(axis="both", which="minor", labelsize=20)
        ax.grid(True, alpha=0.3)
        x_min = x_min_data * 0.8
        ax.set_xlim(x_min, x_max_plot)
        y_max = y_max_data * 2
        ax.set_ylim(TARGET_ERR, y_max)
        ax.axhline(
            TARGET_ERR, color="gray", linestyle=":", alpha=0.6, linewidth=1, zorder=0.3
        )
        style_point_labels(ax, subset, plot_opts["x_func"], group_func)

    # Shared legend in a single line along the bottom (in the margin left by rect)
    legend_kw = dict(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.06),  # slightly closer to subplots
        fontsize=22,
        framealpha=0.9,
    )

    fig_simple.set_dpi(150)
    plt.figure(fig_simple.number)
    handles_simple, labels_simple = _get_legend_handles_labels(axes_simple)
    for ax in axes_simple:
        if ax.get_legend() is not None:
            ax.get_legend().remove()
    plt.tight_layout(rect=[0, 0.08, 1, 1])  # leave bottom margin for shared legend
    leg_simple = None
    if handles_simple and labels_simple:
        leg_simple = fig_simple.legend(
            handles=handles_simple,
            labels=labels_simple,
            ncol=len(labels_simple),
            **legend_kw,
        )
        for t in leg_simple.get_texts():
            if t.get_text() == LEGEND_BOLD_LABEL:
                t.set_fontweight("bold")

    fig_full.set_dpi(150)
    plt.figure(fig_full.number)
    handles_full, labels_full = _get_legend_handles_labels(axes_full)
    for ax in axes_full:
        if ax.get_legend() is not None:
            ax.get_legend().remove()
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    leg_full = None
    if handles_full and labels_full:
        leg_full = fig_full.legend(
            handles=handles_full,
            labels=labels_full,
            ncol=len(labels_full),
            **legend_kw,
        )
        for t in leg_full.get_texts():
            if t.get_text() == LEGEND_BOLD_LABEL:
                t.set_fontweight("bold")

    if output_path:
        base, ext = os.path.splitext(output_path)
        out_simple = f"{base}_data_only{ext}"
        extra_simple = [leg_simple] if leg_simple is not None else []
        fig_simple.savefig(
            out_simple, dpi=150, bbox_inches="tight", bbox_extra_artists=extra_simple
        )
        print(f"Saved data-only plot to {out_simple}")
        extra_full = [leg_full] if leg_full is not None else []
        fig_full.savefig(
            output_path, dpi=150, bbox_inches="tight", bbox_extra_artists=extra_full
        )
        print(f"Saved plot (with fit/extrapolation) to {output_path}")

    if show_after:
        plt.figure(fig_full.number)
        plt.show()
    else:
        plt.close(fig_simple)
        plt.close(fig_full)


def main():
    parser = argparse.ArgumentParser(
        description="Plot aggregated benchmark results (error vs qubits)."
    )
    parser.add_argument(
        "csv",
        nargs="?",
        default=os.path.join(SCRIPT_DIR, "output", "aggregated_results.csv"),
        help="Path to aggregated_results.csv",
    )
    parser.add_argument(
        "--decoder",
        type=str,
        default=None,
        help="Decoder to plot (default: first in data)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to save the plot (default: show only). With noise_model column, one PDF per noise model: base_noise_model.pdf",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        print(f"Error: CSV not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.csv)
    if df.empty:
        print("Error: CSV is empty.", file=sys.stderr)
        sys.exit(1)

    if args.decoder is not None:
        df = df[df["decoder"] == args.decoder].copy()
    else:
        args.decoder = df["decoder"].iloc[0] if "decoder" in df.columns else "unknown"
    if df.empty:
        print(f"No data for decoder: {args.decoder}", file=sys.stderr)
        sys.exit(1)

    # One plot group per noise_model if column present; otherwise single group
    if "noise_model" in df.columns:
        noise_models = sorted(df["noise_model"].dropna().unique().tolist())
        if not noise_models:
            noise_models = [None]
    else:
        noise_models = [None]

    plot_opts = dict(
        x_func=lambda s: s.json_metadata["num_qubits"],
        failure_units_per_shot_func=lambda s: s.json_metadata["r"],
        group_func=group_func,
        filter_func=lambda _: True,
        highlight_max_likelihood_factor=1000.0,
        point_label_func=lambda s: f"d={s.json_metadata['d']}",
        plot_args_func=lambda k, g, _: (
            {"color": g["color"]} if isinstance(g, dict) and "color" in g else {}
        ),
    )

    for i, noise_model in enumerate(noise_models):
        if noise_model is not None:
            df_sub = df[df["noise_model"] == noise_model].copy()
            label = noise_model
        else:
            df_sub = df
            label = "all"
        if df_sub.empty:
            print(f"Skipping empty subset: {label}", file=sys.stderr)
            continue

        if args.output:
            base, ext = os.path.splitext(args.output)
            safe = _sanitize_noise_model_for_path(noise_model)
            out_path = f"{base}_{safe}{ext}"
        else:
            out_path = None

        show_after = not args.output and (i == len(noise_models) - 1)
        _plot_one_noise_model(df_sub, plot_opts, out_path, show_after)

    # Print qubit counts for reference (from full df after decoder filter)
    print("\nQubit counts by circuit type and distance:")
    for circuit_type in df["circuit_type"].unique():
        print(f"  {circuit_type}:")
        for d in sorted(df["distance"].unique()):
            qubits = compute_qubit_count(int(d), circuit_type)
            print(f"    d={d}: {qubits} qubits (sqrt={np.sqrt(qubits):.2f})")


if __name__ == "__main__":
    main()
