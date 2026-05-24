import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MPLCONFIGDIR = BASE_DIR / ".matplotlib"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIGDIR)

XDG_CACHE_HOME = BASE_DIR / ".cache"
XDG_CACHE_HOME.mkdir(parents=True, exist_ok=True)
os.environ["XDG_CACHE_HOME"] = str(XDG_CACHE_HOME)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INPUT_PATH = BASE_DIR / "results" / "processed" / "consolidated.json"
RAW_DIR = BASE_DIR / "results" / "raw"
PLOTS_DIR = BASE_DIR / "results" / "plots"

SYNC_COLOR = "#4C78A8"
ASYNC_COLOR = "#E45756"
SEQ_COLOR = "#72B7B2"
RAND_COLOR = "#F58518"
MEAN_COLOR = "#4C78A8"
P95_COLOR = "#F58518"
P99_COLOR = "#E45756"
CPU_COLOR = "#E45756"
UTIL_COLOR = "#54A24B"
STATE_COLOR = "#B279A2"


def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    summary = {item["name"]: item for item in data["summary"]}
    runs = {item["name"]: item for item in data["runs"]}

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("ggplot")

    plot_seq_bandwidth(summary)
    plot_random_iops(summary)
    plot_throughput_illusion(summary)
    plot_processing_reality(summary)
    plot_resource_overhead(summary)
    plot_latency_distribution(runs)
    plot_state_penalty(summary)


def save_plot(figure, filename):
    figure.tight_layout()
    figure.savefig(PLOTS_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close(figure)


def add_value_labels(axis, bars, decimals=1):
    for bar in bars:
        height = bar.get_height()
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.{decimals}f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def add_point_labels(axis, x_positions, values, decimals=1, y_offset=6):
    for x_pos, value in zip(x_positions, values):
        axis.annotate(
            f"{value:.{decimals}f}",
            (x_pos, value),
            textcoords="offset points",
            xytext=(0, y_offset),
            ha="center",
            fontsize=9,
        )


def async_workloads():
    return [
        ("seq_write_async", "Seq Write"),
        ("seq_read_async", "Seq Read"),
        ("rand_write_async", "Rand Write"),
        ("rand_read_async", "Rand Read"),
        ("seq_to_rand", "Seq->Rand Read"),
    ]


def fio_disk_util_percent(name):
    raw_report = json.loads((RAW_DIR / f"{name}.json").read_text(encoding="utf-8"))
    disk_util = raw_report.get("disk_util") or []

    if not disk_util:
        return 0.0

    return round(float(disk_util[0].get("util", 0.0)), 3)


def effective_device_util(summary_item):
    util = summary_item.get("mean_util_percent")

    if util is not None and util > 0:
        return util

    return fio_disk_util_percent(summary_item["name"])


def draw_seq_bandwidth(axis, summary):
    labels = ["Read", "Write"]
    sync_values = [
        summary["seq_read_sync"]["throughput_mib_per_sec"],
        summary["seq_write_sync"]["throughput_mib_per_sec"],
    ]
    async_values = [
        summary["seq_read_async"]["throughput_mib_per_sec"],
        summary["seq_write_async"]["throughput_mib_per_sec"],
    ]

    positions = [0, 1]
    width = 0.35

    sync_bars = axis.bar(
        [x - width / 2 for x in positions],
        sync_values,
        width=width,
        label="Sync (QD=1)",
        color=SYNC_COLOR,
    )
    async_bars = axis.bar(
        [x + width / 2 for x in positions],
        async_values,
        width=width,
        label="Async io_uring (QD=32)",
        color=ASYNC_COLOR,
    )

    axis.set_ylabel("MiB/s")
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.legend()
    add_value_labels(axis, sync_bars)
    add_value_labels(axis, async_bars)


def draw_throughput_illusion(axis, summary):
    labels = ["Async Seq Read\n128K", "Async Rand Read\n4K"]
    values = [
        summary["seq_read_async"]["throughput_mib_per_sec"],
        summary["rand_read_async"]["throughput_mib_per_sec"],
    ]

    bars = axis.bar(labels, values, color=[SEQ_COLOR, RAND_COLOR])
    axis.set_ylabel("MiB/s")
    add_value_labels(axis, bars)


def draw_random_iops(axis, summary):
    labels = ["Read", "Write"]
    sync_values = [
        summary["rand_read_sync"]["iops"],
        summary["rand_write_sync"]["iops"],
    ]
    async_values = [
        summary["rand_read_async"]["iops"],
        summary["rand_write_async"]["iops"],
    ]

    positions = [0, 1]
    width = 0.35

    sync_bars = axis.bar(
        [x - width / 2 for x in positions],
        sync_values,
        width=width,
        label="Sync (QD=1)",
        color=SYNC_COLOR,
    )
    async_bars = axis.bar(
        [x + width / 2 for x in positions],
        async_values,
        width=width,
        label="Async io_uring (QD=32)",
        color=ASYNC_COLOR,
    )

    axis.set_ylabel("IOPS")
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.legend()
    add_value_labels(axis, sync_bars, decimals=0)
    add_value_labels(axis, async_bars, decimals=0)


def draw_processing_reality(axis, summary):
    labels = ["Async Seq Read\n128K", "Async Rand Read\n4K"]
    values = [
        summary["seq_read_async"]["iops"],
        summary["rand_read_async"]["iops"],
    ]

    bars = axis.bar(labels, values, color=[SEQ_COLOR, RAND_COLOR])
    axis.set_ylabel("IOPS")
    add_value_labels(axis, bars, decimals=0)


def draw_latency_distribution(axis, runs):
    workloads = async_workloads()
    labels = [label for _, label in workloads]
    mean_values = [runs[name]["fio"]["latency_usec"]["mean"] for name, _ in workloads]
    p95_values = [runs[name]["fio"]["latency_usec"]["p95"] for name, _ in workloads]
    p99_values = [runs[name]["fio"]["latency_usec"]["p99"] for name, _ in workloads]

    positions = list(range(len(labels)))
    width = 0.24

    mean_bars = axis.bar(
        [x - width for x in positions],
        mean_values,
        width=width,
        label="Mean",
        color=MEAN_COLOR,
    )
    p95_bars = axis.bar(
        positions,
        p95_values,
        width=width,
        label="P95",
        color=P95_COLOR,
    )
    p99_bars = axis.bar(
        [x + width for x in positions],
        p99_values,
        width=width,
        label="P99",
        color=P99_COLOR,
    )

    axis.set_ylabel("Latency (us)")
    axis.set_yscale("log")
    axis.set_xticks(positions)
    axis.set_xticklabels(labels, rotation=15)
    axis.legend()
    add_value_labels(axis, mean_bars)
    add_value_labels(axis, p95_bars)
    add_value_labels(axis, p99_bars)


def draw_system_overhead(axis, summary):
    workloads = async_workloads()
    labels = [label for _, label in workloads]
    cpu_values = [summary[name]["fio_cpu_total_percent"] for name, _ in workloads]
    util_values = [effective_device_util(summary[name]) for name, _ in workloads]
    positions = list(range(len(labels)))

    bars = axis.bar(
        positions,
        cpu_values,
        width=0.55,
        color=CPU_COLOR,
        alpha=0.8,
        label="fio CPU Usage",
    )
    axis.set_ylabel("fio CPU Usage (%)", color=CPU_COLOR)
    axis.set_xticks(positions)
    axis.set_xticklabels(labels, rotation=15)
    axis.tick_params(axis="y", labelcolor=CPU_COLOR)

    util_axis = axis.twinx()
    util_axis.plot(
        positions,
        util_values,
        color=UTIL_COLOR,
        marker="o",
        linewidth=2,
        label="NVMe Utilization",
    )
    util_axis.set_ylabel("NVMe Device Utilization (%)", color=UTIL_COLOR)
    util_axis.tick_params(axis="y", labelcolor=UTIL_COLOR)

    add_value_labels(axis, bars)
    add_point_labels(util_axis, positions, util_values)

    handles_1, labels_1 = axis.get_legend_handles_labels()
    handles_2, labels_2 = util_axis.get_legend_handles_labels()
    axis.legend(handles_1 + handles_2, labels_1 + labels_2, loc="upper left")


def draw_mixed_state_penalty(axis, summary):
    labels = ["Clean Rand Read", "After Seq Write"]
    iops_values = [
        summary["rand_read_async"]["iops"],
        summary["seq_to_rand"]["iops"],
    ]
    latency_values = [
        summary["rand_read_async"]["latency_p99_usec"],
        summary["seq_to_rand"]["latency_p99_usec"],
    ]
    positions = [0, 1]

    bars = axis.bar(
        positions,
        iops_values,
        width=0.55,
        color=RAND_COLOR,
        alpha=0.85,
        label="IOPS",
    )
    axis.set_ylabel("IOPS", color=RAND_COLOR)
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.tick_params(axis="y", labelcolor=RAND_COLOR)

    latency_axis = axis.twinx()
    latency_axis.plot(
        positions,
        latency_values,
        color=STATE_COLOR,
        marker="o",
        linewidth=2,
        label="P99 Latency",
    )
    latency_axis.set_ylabel("P99 Latency (us)", color=STATE_COLOR)
    latency_axis.tick_params(axis="y", labelcolor=STATE_COLOR)

    add_value_labels(axis, bars, decimals=0)
    add_point_labels(latency_axis, positions, latency_values)

    handles_1, labels_1 = axis.get_legend_handles_labels()
    handles_2, labels_2 = latency_axis.get_legend_handles_labels()
    axis.legend(handles_1 + handles_2, labels_1 + labels_2, loc="upper right")


def plot_seq_bandwidth(summary):
    figure, axis = plt.subplots(figsize=(8, 5.5))
    draw_seq_bandwidth(axis, summary)
    save_plot(figure, "01_seq_bandwidth.png")


def plot_random_iops(summary):
    figure, axis = plt.subplots(figsize=(8, 5.5))
    draw_random_iops(axis, summary)
    save_plot(figure, "02_random_iops.png")


def plot_throughput_illusion(summary):
    figure, axis = plt.subplots(figsize=(8, 5.5))
    draw_throughput_illusion(axis, summary)
    save_plot(figure, "03_throughput_illusion.png")


def plot_processing_reality(summary):
    figure, axis = plt.subplots(figsize=(8, 5.5))
    draw_processing_reality(axis, summary)
    save_plot(figure, "04_processing_reality.png")


def plot_resource_overhead(summary):
    figure, axis = plt.subplots(figsize=(11, 5.5))
    draw_system_overhead(axis, summary)
    save_plot(figure, "05_resource_overhead.png")


def plot_latency_distribution(runs):
    figure, axis = plt.subplots(figsize=(12, 5.5))
    draw_latency_distribution(axis, runs)
    save_plot(figure, "06_latency_distribution.png")


def plot_state_penalty(summary):
    figure, axis = plt.subplots(figsize=(9, 5.5))
    draw_mixed_state_penalty(axis, summary)
    save_plot(figure, "07_state_penalty.png")


if __name__ == "__main__":
    main()
