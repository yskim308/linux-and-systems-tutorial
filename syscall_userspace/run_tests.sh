#!/bin/bash

echo "compiling C program"
gcc main.c -o monitor

echo "Starting Regular Tabs Test..."
./monitor regular.csv &  MONITOR_PID=$!
sleep 5
uv run run_browser_tests.py --type regular
sleep 10
kill $MONITOR_PID

sleep 45

echo "Starting Heavy JS Tabs Test..."
sleep 5
./monitor heavy.csv &
MONITOR_PID=$!
uv run run_browser_tests.py --type heavy
sleep 10
kill $MONITOR_PID

# --- Plot ---
uv run  plot.py
