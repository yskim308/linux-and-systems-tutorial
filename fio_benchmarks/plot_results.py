import json
import os
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
MPLCONFIGDIR = BASE_DIR / ".matplotlib"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIGDIR)


matplotlib.use("Agg")

INPUT_PATH = BASE_DIR / "results" / "processed" / "consolidated.json"
PLOTS_DIR = BASE_DIR / "results" / "plots"


def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    summary = data["summary"]
    runs = data["runs"]

    seq_write_sync = find_by_name(summary, "seq_write_sync")
    seq_read_async = find_by_name(summary, "seq_read_async")
    rand_write_async = find_by_name(summary, "rand_write_async")
    rand_read_async = find_by_name(summary, "rand_read_async")
    seq_to_rand = find_by_name(summary, "seq_to_rand")

    rand_write_async_run = find_by_name(runs, "rand_write_async")
    rand_read_async_run = find_by_name(runs, "rand_read_async")
    seq_to_rand_run = find_by_name(runs, "seq_to_rand")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.style.use("ggplot")

    plot_throughput(
        seq_write_sync,
        seq_read_async,
        rand_write_async,
        rand_read_async,
        seq_to_rand,
    )
    plot_random_iops(rand_write_async, rand_read_async, seq_to_rand)
    plot_random_latency(rand_write_async_run, rand_read_async_run, seq_to_rand_run)
    plot_device_pressure(
        seq_write_sync,
        seq_read_async,
        rand_write_async,
        rand_read_async,
        seq_to_rand,
    )
    plot_cpu_and_iowait(
        seq_write_sync,
        seq_read_async,
        rand_write_async,
        rand_read_async,
        seq_to_rand,
    )
    plot_random_read_comparison(
        rand_read_async, seq_to_rand, rand_read_async_run, seq_to_rand_run
    )


def find_by_name(items, name):
    for item in items:
        if item["name"] == name:
            return item
    raise ValueError(f"Missing data for {name}")


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


def plot_throughput(
    seq_write_sync, seq_read_async, rand_write_async, rand_read_async, seq_to_rand
):
    labels = [
        "Seq Write",
        "Seq Read",
        "Rand Write",
        "Rand Read",
        "Seq->Rand",
    ]
    values = [
        seq_write_sync["throughput_mib_per_sec"],
        seq_read_async["throughput_mib_per_sec"],
        rand_write_async["throughput_mib_per_sec"],
        rand_read_async["throughput_mib_per_sec"],
        seq_to_rand["throughput_mib_per_sec"],
    ]

    figure, axis = plt.subplots(figsize=(10, 5))
    bars = axis.bar(
        labels, values, color=["#4C78A8", "#72B7B2", "#E45756", "#54A24B", "#F58518"]
    )
    axis.set_title("Throughput by Workload")
    axis.set_ylabel("MiB/s")
    add_value_labels(axis, bars)
    save_plot(figure, "01_throughput.png")


def plot_random_iops(rand_write_async, rand_read_async, seq_to_rand):
    labels = [
        "Rand Write",
        "Rand Read",
        "Seq->Rand Read",
    ]
    values = [
        rand_write_async["iops"],
        rand_read_async["iops"],
        seq_to_rand["iops"],
    ]

    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar(labels, values, color=["#E45756", "#54A24B", "#F58518"])
    axis.set_title("4K Random IOPS")
    axis.set_ylabel("IOPS")
    add_value_labels(axis, bars, decimals=0)
    save_plot(figure, "02_random_iops.png")


def plot_random_latency(rand_write_async_run, rand_read_async_run, seq_to_rand_run):
    labels = ["Rand Write", "Rand Read", "Seq->Rand Read"]
    p50 = [
        rand_write_async_run["fio"]["latency_usec"]["p50"],
        rand_read_async_run["fio"]["latency_usec"]["p50"],
        seq_to_rand_run["fio"]["latency_usec"]["p50"],
    ]
    p95 = [
        rand_write_async_run["fio"]["latency_usec"]["p95"],
        rand_read_async_run["fio"]["latency_usec"]["p95"],
        seq_to_rand_run["fio"]["latency_usec"]["p95"],
    ]
    p99 = [
        rand_write_async_run["fio"]["latency_usec"]["p99"],
        rand_read_async_run["fio"]["latency_usec"]["p99"],
        seq_to_rand_run["fio"]["latency_usec"]["p99"],
    ]

    positions = [0, 1, 2]
    width = 0.25

    figure, axis = plt.subplots(figsize=(9, 5))
    bars1 = axis.bar(
        [x - width for x in positions], p50, width=width, label="p50", color="#4C78A8"
    )
    bars2 = axis.bar(positions, p95, width=width, label="p95", color="#F58518")
    bars3 = axis.bar(
        [x + width for x in positions], p99, width=width, label="p99", color="#E45756"
    )
    axis.set_title("4K Random Read/Write Latency")
    axis.set_ylabel("Latency (usec)")
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.legend()
    add_value_labels(axis, bars1)
    add_value_labels(axis, bars2)
    add_value_labels(axis, bars3)
    save_plot(figure, "03_random_latency.png")


def plot_device_pressure(
    seq_write_sync, seq_read_async, rand_write_async, rand_read_async, seq_to_rand
):
    labels = [
        "Seq Write",
        "Seq Read",
        "Rand Write",
        "Rand Read",
        "Seq->Rand",
    ]
    util_values = [
        seq_write_sync["mean_util_percent"],
        seq_read_async["mean_util_percent"],
        rand_write_async["mean_util_percent"],
        rand_read_async["mean_util_percent"],
        seq_to_rand["mean_util_percent"],
    ]
    queue_values = [
        seq_write_sync["mean_queue_depth"],
        seq_read_async["mean_queue_depth"],
        rand_write_async["mean_queue_depth"],
        rand_read_async["mean_queue_depth"],
        seq_to_rand["mean_queue_depth"],
    ]

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))

    util_bars = axes[0].bar(labels, util_values, color="#4C78A8")
    axes[0].set_title("Mean Device Utilization")
    axes[0].set_ylabel("%util")
    axes[0].tick_params(axis="x", rotation=20)
    add_value_labels(axes[0], util_bars)

    queue_bars = axes[1].bar(labels, queue_values, color="#72B7B2")
    axes[1].set_title("Mean Device Queue Depth")
    axes[1].set_ylabel("aqu-sz")
    axes[1].tick_params(axis="x", rotation=20)
    add_value_labels(axes[1], queue_bars)

    save_plot(figure, "04_device_pressure.png")


def plot_cpu_and_iowait(
    seq_write_sync, seq_read_async, rand_write_async, rand_read_async, seq_to_rand
):
    labels = [
        "Seq Write",
        "Seq Read",
        "Rand Write",
        "Rand Read",
        "Seq->Rand",
    ]
    cpu_values = [
        seq_write_sync["fio_cpu_total_percent"],
        seq_read_async["fio_cpu_total_percent"],
        rand_write_async["fio_cpu_total_percent"],
        rand_read_async["fio_cpu_total_percent"],
        seq_to_rand["fio_cpu_total_percent"],
    ]
    iowait_values = [
        seq_write_sync["mean_iowait_percent"],
        seq_read_async["mean_iowait_percent"],
        rand_write_async["mean_iowait_percent"],
        rand_read_async["mean_iowait_percent"],
        seq_to_rand["mean_iowait_percent"],
    ]

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))

    cpu_bars = axes[0].bar(labels, cpu_values, color="#E45756")
    axes[0].set_title("fio CPU Usage")
    axes[0].set_ylabel("CPU (%)")
    axes[0].tick_params(axis="x", rotation=20)
    add_value_labels(axes[0], cpu_bars)

    iowait_bars = axes[1].bar(labels, iowait_values, color="#54A24B")
    axes[1].set_title("System iowait")
    axes[1].set_ylabel("iowait (%)")
    axes[1].tick_params(axis="x", rotation=20)
    add_value_labels(axes[1], iowait_bars)

    save_plot(figure, "05_cpu_iowait.png")


def plot_random_read_comparison(
    rand_read_async, seq_to_rand, rand_read_async_run, seq_to_rand_run
):
    labels = ["Rand Read", "Seq->Rand Read"]
    iops = [
        rand_read_async["iops"],
        seq_to_rand["iops"],
    ]
    p95 = [
        rand_read_async_run["fio"]["latency_usec"]["p95"],
        seq_to_rand_run["fio"]["latency_usec"]["p95"],
    ]
    p99 = [
        rand_read_async_run["fio"]["latency_usec"]["p99"],
        seq_to_rand_run["fio"]["latency_usec"]["p99"],
    ]
    util = [
        rand_read_async["mean_util_percent"],
        seq_to_rand["mean_util_percent"],
    ]

    figure, axes = plt.subplots(1, 4, figsize=(16, 4))

    iops_bars = axes[0].bar(labels, iops, color="#4C78A8")
    axes[0].set_title("IOPS")
    add_value_labels(axes[0], iops_bars, decimals=0)

    p95_bars = axes[1].bar(labels, p95, color="#F58518")
    axes[1].set_title("p95 Latency")
    axes[1].set_ylabel("usec")
    add_value_labels(axes[1], p95_bars)

    p99_bars = axes[2].bar(labels, p99, color="#E45756")
    axes[2].set_title("p99 Latency")
    axes[2].set_ylabel("usec")
    add_value_labels(axes[2], p99_bars)

    util_bars = axes[3].bar(labels, util, color="#54A24B")
    axes[3].set_title("Mean %util")
    add_value_labels(axes[3], util_bars)

    save_plot(figure, "06_rand_read_vs_seq_to_rand.png")


if __name__ == "__main__":
    main()
