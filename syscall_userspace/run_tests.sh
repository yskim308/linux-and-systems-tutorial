#!/bin/bash

echo "Starting Regular Tabs Test..."
./monitor > regular.csv &  MONITOR_PID=$!
python3 run_browser_tests.py --type regular
kill $MONITOR_PID

sleep(45)

echo "Starting Heavy JS Tabs Test..."
./monitor > heavy.csv &
MONITOR_PID=$!
python3 run_browser_tests.py --type heavy
kill $MONITOR_PID

# --- Plot ---
python3 plot.py
