import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "results" / "raw"
PROCESSED_DIR = BASE_DIR / "results" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "consolidated.json"

# Device and Column Constants
NVME_DEVICE = "nvme0n1"
QUEUE_DEPTH = 21  # aqu-sz index
UTIL_PERCENT = 22  # %util index
CPU_USER = 0  # avg-cpu %user index
CPU_SYS = 2  # avg-cpu %system index


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    runs = []
    # Dynamically find and process all fio json files in the raw directory
    for path in RAW_DIR.glob("*.json"):
        try:
            runs.append(build_run(path))
        except Exception as e:
            print(f"Skipping {path.name}: {e}")

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(RAW_DIR),
        "runs": runs,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Clean parsing complete. Saved to: {OUTPUT_PATH}")


def build_run(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    job = report["jobs"][0]
    operation, stats = active_stats(job)

    # Locate the corresponding iostat log
    iostat_path = RAW_DIR / f"{path.stem}_iostat.log"
    iostat_data = parse_iostat(iostat_path) if iostat_path.exists() else {}

    return {
        "test_name": job["jobname"],
        "operation": operation,
        "iodepth": int(job["job options"].get("iodepth", "1")),
        "fio": {
            "throughput_mib_per_sec": mib_from_bytes(stats["bw_bytes"]),
            "iops": round(stats["iops"], 3),
            "latency_usec": {
                "p50": usec(stats["clat_ns"]["percentile"]["50.000000"]),
                "p95": usec(stats["clat_ns"]["percentile"]["95.000000"]),
                "p99": usec(stats["clat_ns"]["percentile"]["99.000000"]),
                "p99_9": usec(stats["clat_ns"]["percentile"]["99.900000"]),
            },
            "usr_cpu": round(job.get("usr_cpu", 0.0), 3),
            "sys_cpu": round(job.get("sys_cpu", 0.0), 3),
        },
        "iostat": iostat_data,
    }


def active_stats(job):
    for name in ("read", "write", "trim"):
        if name in job and job[name]["io_bytes"] > 0:
            return name, job[name]
    raise ValueError(f"No active operation in {job['jobname']}")


def parse_iostat(path):
    cpu_samples = []
    nvme_samples = []
    expecting_cpu = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("avg-cpu:"):
            expecting_cpu = True
            continue

        if expecting_cpu:
            parts = line.split()
            cpu_samples.append(
                {"user": float(parts[CPU_USER]), "system": float(parts[CPU_SYS])}
            )
            expecting_cpu = False
            continue

        if line.startswith(NVME_DEVICE):
            parts = line.split()
            nvme_samples.append(
                {
                    "aqu_sz": float(parts[QUEUE_DEPTH]),
                    "util": float(parts[UTIL_PERCENT]),
                }
            )

    # Drop the first sample (usually the boot-time average, not test data)
    interval_cpu = cpu_samples[1:] if len(cpu_samples) > 1 else cpu_samples
    interval_nvme = nvme_samples[1:] if len(nvme_samples) > 1 else nvme_samples

    return {
        "system_cpu_percent": {
            "mean_user": mean(s["user"] for s in interval_cpu),
            "mean_system": mean(s["system"] for s in interval_cpu),
            "mean_total": mean(s["user"] + s["system"] for s in interval_cpu),
        },
        "device_stats": {
            "mean_aqu_sz": mean(s["aqu_sz"] for s in interval_nvme),
            "mean_util_percent": mean(s["util"] for s in interval_nvme),
        },
    }


def mib_from_bytes(value):
    return round(value / (1024 * 1024), 3)


def usec(value):
    return round(value / 1000, 3)


def mean(values):
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


if __name__ == "__main__":
    main()
