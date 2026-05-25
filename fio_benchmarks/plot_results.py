import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- Clean Relative Paths ---
INPUT_PATH = Path("results/processed/consolidated.json")
PLOTS_DIR = Path("results/plots")

# --- Styling Colors ---
SYNC_COLOR = "#4C78A8"  # Blue
ASYNC_COLOR = "#F58518"  # Orange
POS_CHANGE = "#54A24B"  # Green
NEG_CHANGE = "#E45756"  # Red


def main():
    if not INPUT_PATH.exists():
        print(f"Error: Could not find {INPUT_PATH}")
        return

    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    summary = {item["test_name"]: item for item in data.get("runs", [])}

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("ggplot")

    # Define the core workloads to extract
    workloads = [
        ("Seq Read", "seq_read_sync", "seq_read_async"),
        ("Seq Write", "seq_write_sync", "seq_write_async"),
        ("Rand Read", "rand_read_sync", "rand_read_async"),
        ("Rand Write", "rand_write_sync", "rand_write_async"),
    ]

    # Generate each plot independently
    plot_iops_baseline(summary, workloads)
    plot_throughput_baseline(summary, workloads)
    plot_iops_pct_change(summary, workloads)
    plot_throughput_pct_change(summary, workloads)


def save_plot(figure, filename):
    out_file = PLOTS_DIR / filename
    figure.tight_layout()
    figure.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved: {out_file}")


def add_v_value_labels(axis, bars, decimals=0):
    """Adds labels above vertical bars."""
    for bar in bars:
        height = bar.get_height()
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            height + (height * 0.02),
            f"{height:.{decimals}f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def add_v_pct_value_labels(axis, bars, decimals=1):
    """Adds percentage labels above/below vertical bars."""
    for bar in bars:
        height = bar.get_height()
        # Create dynamic padding based on the axis limits so text doesn't overlap the bar
        y_limit = max(abs(axis.get_ylim()[0]), abs(axis.get_ylim()[1]))
        padding = y_limit * 0.02

        y_pos = height + padding if height >= 0 else height - padding
        va = "bottom" if height >= 0 else "top"

        axis.text(
            bar.get_x() + bar.get_width() / 2,
            y_pos,
            f"{height:+.{decimals}f}%",
            ha="center",
            va=va,
            fontsize=10,
            fontweight="bold",
        )


def plot_iops_baseline(summary, workloads):
    figure, axis = plt.subplots(figsize=(8, 6))

    labels = [w[0] for w in workloads]
    x_pos = np.arange(len(labels))
    width = 0.35

    sync_iops = [summary[w[1]]["fio"]["iops"] for w in workloads]
    async_iops = [summary[w[2]]["fio"]["iops"] for w in workloads]

    bars_sync = axis.bar(
        x_pos - width / 2, sync_iops, width, label="Sync (QD=1)", color=SYNC_COLOR
    )
    bars_async = axis.bar(
        x_pos + width / 2, async_iops, width, label="Async (QD=32)", color=ASYNC_COLOR
    )

    axis.set_ylabel("IOPS")
    axis.set_xticks(x_pos)
    axis.set_xticklabels(labels)
    axis.legend()

    add_v_value_labels(axis, bars_sync, decimals=0)
    add_v_value_labels(axis, bars_async, decimals=0)

    # Pad top limit so labels don't clip
    axis.set_ylim(0, max(max(sync_iops), max(async_iops)) * 1.15)
    save_plot(figure, "01_iops_baseline.png")


def plot_throughput_baseline(summary, workloads):
    figure, axis = plt.subplots(figsize=(8, 6))

    labels = [w[0] for w in workloads]
    x_pos = np.arange(len(labels))
    width = 0.35

    sync_bw = [summary[w[1]]["fio"]["throughput_mib_per_sec"] for w in workloads]
    async_bw = [summary[w[2]]["fio"]["throughput_mib_per_sec"] for w in workloads]

    bars_sync = axis.bar(
        x_pos - width / 2, sync_bw, width, label="Sync (QD=1)", color=SYNC_COLOR
    )
    bars_async = axis.bar(
        x_pos + width / 2, async_bw, width, label="Async (QD=32)", color=ASYNC_COLOR
    )

    axis.set_ylabel("MiB/s")
    axis.set_xticks(x_pos)
    axis.set_xticklabels(labels)
    axis.legend()

    add_v_value_labels(axis, bars_sync, decimals=1)
    add_v_value_labels(axis, bars_async, decimals=1)

    axis.set_ylim(0, max(max(sync_bw), max(async_bw)) * 1.15)
    save_plot(figure, "02_throughput_baseline.png")


def plot_iops_pct_change(summary, workloads):
    figure, axis = plt.subplots(figsize=(8, 6))

    labels = [w[0] for w in workloads]
    x_pos = np.arange(len(labels))

    sync_iops = [summary[w[1]]["fio"]["iops"] for w in workloads]
    async_iops = [summary[w[2]]["fio"]["iops"] for w in workloads]
    pct_iops = [((a - s) / s) * 100 for s, a in zip(sync_iops, async_iops)]

    colors = [POS_CHANGE if val >= 0 else NEG_CHANGE for val in pct_iops]
    bars = axis.bar(x_pos, pct_iops, color=colors, width=0.6)

    axis.axhline(0, color="black", linewidth=1.2)
    axis.set_ylabel("Percentage Change (%)")
    axis.set_xticks(x_pos)
    axis.set_xticklabels(labels)

    max_abs = max([abs(x) for x in pct_iops] + [1])
    axis.set_ylim(-max_abs * 1.2, max_abs * 1.25)

    add_v_pct_value_labels(axis, bars, decimals=1)
    save_plot(figure, "03_iops_pct_change.png")


def plot_throughput_pct_change(summary, workloads):
    figure, axis = plt.subplots(figsize=(8, 6))

    labels = [w[0] for w in workloads]
    x_pos = np.arange(len(labels))

    sync_bw = [summary[w[1]]["fio"]["throughput_mib_per_sec"] for w in workloads]
    async_bw = [summary[w[2]]["fio"]["throughput_mib_per_sec"] for w in workloads]
    pct_bw = [((a - s) / s) * 100 for s, a in zip(sync_bw, async_bw)]

    colors = [POS_CHANGE if val >= 0 else NEG_CHANGE for val in pct_bw]
    bars = axis.bar(x_pos, pct_bw, color=colors, width=0.6)

    axis.axhline(0, color="black", linewidth=1.2)
    axis.set_ylabel("Percentage Change (%)")
    axis.set_xticks(x_pos)
    axis.set_xticklabels(labels)

    max_abs = max([abs(x) for x in pct_bw] + [1])
    axis.set_ylim(-max_abs * 1.2, max_abs * 1.25)

    add_v_pct_value_labels(axis, bars, decimals=1)
    save_plot(figure, "04_throughput_pct_change.png")


if __name__ == "__main__":
    main()
