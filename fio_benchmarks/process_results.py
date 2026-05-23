import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "results" / "raw"
PROCESSED_DIR = BASE_DIR / "results" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "consolidated.json"
NVME_DEVICE = "nvme0n1"
RKB_PER_SEC = 2
READ_AWAIT_MS = 5
WKB_PER_SEC = 8
WRITE_AWAIT_MS = 11
QUEUE_DEPTH = 21
UTIL_PERCENT = 22

PERCENTILES = {
    "p50": "50.000000",
    "p95": "95.000000",
    "p99": "99.000000",
    "p99_9": "99.900000",
}


def main():
    seq_write_sync = build_run("seq_write_sync", "Sequential Write (Sync)")
    seq_write_async = build_run("seq_write_async", "Sequential Write (Async)")

    seq_read_sync = build_run("seq_read_sync", "Sequential Read (Sync)")
    seq_read_async = build_run("seq_read_async", "Sequential Read (Async)")

    rand_write_sync = build_run("rand_write_sync", "Random Write (Sync)")
    rand_write_async = build_run("rand_write_async", "Random Write (Async)")

    rand_read_sync = build_run("rand_read_sync", "Random Read (Sync)")
    rand_read_async = build_run("rand_read_async", "Random Read (Async)")

    seq_to_rand = build_run("seq_to_rand", "Random Read After Sequential Write")

    runs = [
        seq_write_sync,
        seq_write_async,
        seq_read_sync,
        seq_read_async,
        rand_write_async,
        rand_write_sync,
        rand_read_async,
        rand_read_sync,
        seq_to_rand,
    ]

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(RAW_DIR),
        "summary": [
            summary(seq_write_sync),
            summary(seq_write_async),
            summary(seq_read_sync),
            summary(seq_read_async),
            summary(rand_write_sync),
            summary(rand_write_async),
            summary(rand_read_sync),
            summary(rand_read_async),
            summary(seq_to_rand),
        ],
        "runs": runs,
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def build_run(name, label):
    path = RAW_DIR / f"{name}.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    job = report["jobs"][0]
    operation, stats = active_stats(job)
    options = job["job options"]
    iostat_path = RAW_DIR / f"{path.stem}_iostat.log"

    return {
        "name": job["jobname"],
        "label": label,
        "operation": operation,
        "config": {
            "rw": options["rw"],
            "ioengine": options["ioengine"],
            "iodepth": int(options.get("iodepth", "1")),
            "direct": options.get("direct") == "1",
            "block_size_bytes": parse_size(options["bs"]),
            "size_bytes": parse_size(options["size"]),
            "filename": options["filename"],
        },
        "fio": {
            "runtime_seconds": round(job["job_runtime"] / 1000, 3),
            "bytes_transferred": stats["io_bytes"],
            "throughput_mib_per_sec": mib_from_bytes(stats["bw_bytes"]),
            "iops": round(stats["iops"], 3),
            "latency_usec": {
                "mean": usec(stats["clat_ns"]["mean"]),
                "p50": percentile(stats["clat_ns"], "p50"),
                "p95": percentile(stats["clat_ns"], "p95"),
                "p99": percentile(stats["clat_ns"], "p99"),
                "p99_9": percentile(stats["clat_ns"], "p99_9"),
            },
            "cpu_percent": {
                "user": round(job["usr_cpu"], 3),
                "system": round(job["sys_cpu"], 3),
                "total": round(job["usr_cpu"] + job["sys_cpu"], 3),
            },
        },
        "iostat": parse_iostat(iostat_path) if iostat_path.exists() else None,
    }


def active_stats(job):
    for name in ("read", "write", "trim"):
        stats = job[name]
        if stats["io_bytes"] > 0:
            return name, stats
    raise ValueError(f"No active operation in {job['jobname']}")


def parse_iostat(path):
    cpu_iowaits = []
    nvme_rows = []
    expecting_cpu_values = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("avg-cpu:"):
            expecting_cpu_values = True
            continue

        if expecting_cpu_values:
            cpu_iowaits.append(float(line.split()[3]))
            expecting_cpu_values = False
            continue

        if not line.startswith(NVME_DEVICE):
            continue

        nvme_rows.append(line.split())

    samples = []

    for iowait, row in zip(cpu_iowaits, nvme_rows):
        samples.append(
            {
                "iowait_percent": iowait,
                "util_percent": float(row[UTIL_PERCENT]),
                "queue_depth": float(row[QUEUE_DEPTH]),
                "read_await_ms": float(row[READ_AWAIT_MS]),
                "write_await_ms": float(row[WRITE_AWAIT_MS]),
                "read_mib_per_sec": kib_to_mib(float(row[RKB_PER_SEC])),
                "write_mib_per_sec": kib_to_mib(float(row[WKB_PER_SEC])),
            }
        )

    interval_samples = samples[1:] if len(samples) > 1 else samples

    return {
        "device": NVME_DEVICE,
        "sample_count": len(interval_samples),
        "cpu": {
            "mean_iowait_percent": mean(
                sample["iowait_percent"] for sample in interval_samples
            ),
            "max_iowait_percent": max_value(
                sample["iowait_percent"] for sample in interval_samples
            ),
        },
        "device_stats": {
            "mean_util_percent": mean(
                sample["util_percent"] for sample in interval_samples
            ),
            "max_util_percent": max_value(
                sample["util_percent"] for sample in interval_samples
            ),
            "mean_queue_depth": mean(
                sample["queue_depth"] for sample in interval_samples
            ),
            "max_queue_depth": max_value(
                sample["queue_depth"] for sample in interval_samples
            ),
            "mean_read_await_ms": mean(
                sample["read_await_ms"] for sample in interval_samples
            ),
            "mean_write_await_ms": mean(
                sample["write_await_ms"] for sample in interval_samples
            ),
            "mean_read_mib_per_sec": mean(
                sample["read_mib_per_sec"] for sample in interval_samples
            ),
            "mean_write_mib_per_sec": mean(
                sample["write_mib_per_sec"] for sample in interval_samples
            ),
        },
    }


def summary(run):
    fio = run["fio"]
    iostat = run["iostat"] or {}
    device_stats = iostat.get("device_stats", {})
    cpu = iostat.get("cpu", {})

    return {
        "name": run["name"],
        "label": run["label"],
        "operation": run["operation"],
        "block_size_bytes": run["config"]["block_size_bytes"],
        "iodepth": run["config"]["iodepth"],
        "throughput_mib_per_sec": fio["throughput_mib_per_sec"],
        "iops": fio["iops"],
        "latency_mean_usec": fio["latency_usec"]["mean"],
        "latency_p95_usec": fio["latency_usec"]["p95"],
        "latency_p99_usec": fio["latency_usec"]["p99"],
        "fio_cpu_total_percent": fio["cpu_percent"]["total"],
        "mean_iowait_percent": cpu.get("mean_iowait_percent"),
        "mean_util_percent": device_stats.get("mean_util_percent"),
        "mean_queue_depth": device_stats.get("mean_queue_depth"),
    }


def percentile(latency, name):
    key = PERCENTILES[name]
    return usec(latency["percentile"][key])


def parse_size(value):
    units = {
        "k": 1024,
        "m": 1024**2,
        "g": 1024**3,
        "t": 1024**4,
    }
    suffix = value[-1].lower()

    if suffix.isdigit():
        return int(value)

    return int(float(value[:-1]) * units[suffix])


def mib_from_bytes(value):
    return round(value / (1024 * 1024), 3)


def kib_to_mib(value):
    return round(value / 1024, 3)


def usec(value):
    return round(value / 1000, 3)


def mean(values):
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def max_value(values):
    values = list(values)
    if not values:
        return 0.0
    return round(max(values), 3)


if __name__ == "__main__":
    main()
