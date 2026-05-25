#!/bin/bash
set -euo pipefail

echo "compiling C program"
gcc main.c -o monitor

run_monitor_test () {
    local csv=$1
    local type=$2

    echo "Starting $type Test..."

    ./monitor "$csv" &
    local pid=$!

    echo "monitor pid = $pid"

    sleep 5

    uv run run_browser_tests.py --type "$type"

    sleep 10

    echo "Stopping monitor..."

    kill -TERM "$pid"

    wait "$pid"

    echo "Monitor stopped."
}

run_monitor_test regular.csv regular

sleep 45

run_monitor_test heavy.csv heavy

uv run plot.py

rm -f monitor
