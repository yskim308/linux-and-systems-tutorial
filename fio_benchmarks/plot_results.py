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
    plot_qd_vs_latency_workload(summary, "seq_read_async_qd", "05_seq_read_async_latency.png")
    plot_qd_vs_latency_workload(summary, "seq_write_async_qd", "06_seq_write_async_latency.png")
    plot_qd_vs_latency_workload(summary, "rand_read_async_qd", "07_rand_read_async_latency.png")
    plot_qd_vs_latency_workload(summary, "rand_write_async_qd", "08_rand_write_async_latency.png")
    plot_qd_vs_iops_workload(summary, "seq_read_async_qd", "09_seq_read_async_iops.png", SYNC_COLOR)
    plot_qd_vs_iops_workload(summary, "seq_write_async_qd", "10_seq_write_async_iops.png", POS_CHANGE)
    plot_qd_vs_iops_workload(summary, "rand_read_async_qd", "11_rand_read_async_iops.png", ASYNC_COLOR)
    plot_qd_vs_iops_workload(summary, "rand_write_async_qd", "12_rand_write_async_iops.png", NEG_CHANGE)
    plot_requested_vs_actual_aqu(summary)
    plot_resource_saturation(summary, "seq_read_async_qd", "14_seq_read_async_saturation.png")
    plot_resource_saturation(summary, "seq_write_async_qd", "15_seq_write_async_saturation.png")
    plot_resource_saturation(summary, "rand_read_async_qd", "16_rand_read_async_saturation.png")
    plot_resource_saturation(summary, "rand_write_async_qd", "17_rand_write_async_saturation.png")


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


def plot_qd_vs_latency_workload(summary, prefix, filename):
    figure, axis = plt.subplots(figsize=(8, 6))

    qds = [1, 2, 4, 8, 16, 32, 64, 128]
    p50_latencies = []
    p99_latencies = []

    for qd in qds:
        run_key = f"{prefix}{qd}"
        if run_key in summary:
            p50_latencies.append(summary[run_key]["fio"]["latency_usec"]["p50"])
            p99_latencies.append(summary[run_key]["fio"]["latency_usec"]["p99"])
        else:
            p50_latencies.append(0.0)
            p99_latencies.append(0.0)

    axis.plot(qds, p50_latencies, marker="o", linewidth=2.0, label="p50 Latency", color=SYNC_COLOR)
    axis.plot(qds, p99_latencies, marker="s", linewidth=2.0, label="p99 Latency", color=NEG_CHANGE)

    axis.set_xlabel("Queue Depth (QD)", fontsize=11)
    axis.set_ylabel("Latency (μs)", fontsize=11)
    axis.set_xscale("log", base=2)
    axis.set_xticks(qds)
    axis.set_xticklabels([str(qd) for qd in qds])
    axis.grid(True, which="both", linestyle="--", alpha=0.5)
    axis.legend(fontsize=10)

    save_plot(figure, filename)


def plot_qd_vs_iops_workload(summary, prefix, filename, color):
    figure, axis1 = plt.subplots(figsize=(8, 6))

    qds = [1, 2, 4, 8, 16, 32, 64, 128]
    iops_vals = []
    p99_latencies = []

    for qd in qds:
        run_key = f"{prefix}{qd}"
        if run_key in summary:
            iops_vals.append(summary[run_key]["fio"]["iops"])
            p99_latencies.append(summary[run_key]["fio"]["latency_usec"]["p99"])
        else:
            iops_vals.append(0.0)
            p99_latencies.append(0.0)

    # Plot IOPS on the left y-axis (linear scale starting at 0)
    line1 = axis1.plot(qds, iops_vals, marker="o", linewidth=2.0, label="IOPS (Left)", color=color)
    axis1.set_xlabel("Queue Depth (QD)", fontsize=11)
    axis1.set_ylabel("IOPS", fontsize=11)
    axis1.set_xscale("log", base=2)
    axis1.set_xticks(qds)
    axis1.set_xticklabels([str(qd) for qd in qds])
    axis1.set_ylim(bottom=0)
    axis1.grid(True, which="both", linestyle="--", alpha=0.5)

    # Create twin axis for p99 Latency on the right y-axis (log scale)
    axis2 = axis1.twinx()
    line2 = axis2.plot(qds, p99_latencies, marker="s", linestyle="--", linewidth=2.0, label="p99 Latency (Right)", color="#7F7F7F")
    axis2.set_ylabel("p99 Latency (μs)", fontsize=11)
    axis2.set_yscale("log")
    axis2.grid(False)  # Avoid overlapping grid lines

    # Combine legends from both axes
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    axis1.legend(lines, labels, loc="upper left", fontsize=10)

    save_plot(figure, filename)


def plot_requested_vs_actual_aqu(summary):
    figure, axis = plt.subplots(figsize=(8, 6))

    qds = [1, 2, 4, 8, 16, 32, 64, 128]
    workloads = [
        ("Seq Read Async", "seq_read_async_qd", SYNC_COLOR),
        ("Seq Write Async", "seq_write_async_qd", POS_CHANGE),
        ("Rand Read Async", "rand_read_async_qd", ASYNC_COLOR),
        ("Rand Write Async", "rand_write_async_qd", NEG_CHANGE),
    ]

    for label, prefix, color in workloads:
        actual_aqus = []
        for qd in qds:
            run_key = f"{prefix}{qd}"
            if run_key in summary:
                iostat_data = summary[run_key].get("iostat", {})
                device_stats = iostat_data.get("device_stats", {})
                aqu = device_stats.get("mean_aqu_sz", 0.0)
                actual_aqus.append(aqu)
            else:
                actual_aqus.append(0.0)

        axis.plot(qds, actual_aqus, marker="o", linewidth=2.0, label=label, color=color)

    # Plot diagonal reference line showing Requested = Actual (y = x)
    axis.plot(qds, qds, linestyle="--", color="#7F7F7F", alpha=0.7, label="Perfect 1:1 Scale (y = x)")

    axis.set_xlabel("Requested Queue Depth (FIO QD)", fontsize=11)
    axis.set_ylabel("Actual Queue Size (iostat aqu-sz)", fontsize=11)
    axis.set_xscale("log", base=2)
    axis.set_yscale("log", base=2)
    axis.set_xticks(qds)
    axis.set_xticklabels([str(qd) for qd in qds])
    axis.set_yticks(qds)
    axis.set_yticklabels([str(qd) for qd in qds])
    axis.grid(True, which="both", linestyle="--", alpha=0.5)
    axis.legend(fontsize=10)

    save_plot(figure, "13_requested_vs_actual_aqu.png")


def plot_resource_saturation(summary, prefix, filename):
    figure, axis = plt.subplots(figsize=(8, 6))

    qds = [1, 2, 4, 8, 16, 32, 64, 128]
    cpu_utils = []
    nvme_utils = []

    for qd in qds:
        run_key = f"{prefix}{qd}"
        if run_key in summary:
            fio_data = summary[run_key]["fio"]
            total_cpu = fio_data.get("usr_cpu", 0.0) + fio_data.get("sys_cpu", 0.0)
            
            iostat_data = summary[run_key].get("iostat", {})
            device_stats = iostat_data.get("device_stats", {})
            nvme_util = device_stats.get("mean_util_percent", 0.0)
            
            cpu_utils.append(total_cpu)
            nvme_utils.append(nvme_util)
        else:
            cpu_utils.append(0.0)
            nvme_utils.append(0.0)

    # Plot NVMe Disk Util (Orange, solid)
    axis.plot(qds, nvme_utils, marker="o", linewidth=2.5, label="NVMe Disk Utilization (%)", color=ASYNC_COLOR)
    # Plot CPU Util (Blue, dashed)
    axis.plot(qds, cpu_utils, marker="s", linestyle="--", linewidth=2.5, label="Total CPU Utilization (%)", color=SYNC_COLOR)

    axis.set_xlabel("Queue Depth (QD)", fontsize=11)
    axis.set_ylabel("Resource Utilization (%)", fontsize=11)
    axis.set_xscale("log", base=2)
    axis.set_xticks(qds)
    axis.set_xticklabels([str(qd) for qd in qds])
    axis.set_ylim(0, 105)
    axis.grid(True, which="both", linestyle="--", alpha=0.5)
    axis.legend(fontsize=10)

    save_plot(figure, filename)


if __name__ == "__main__":
    main()
