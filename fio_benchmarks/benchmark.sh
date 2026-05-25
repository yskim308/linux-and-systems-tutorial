#!/bin/bash

TEST_SIZE="2G"
TEST_FILE="testfile.img"
QDS="1 2 4 8 16 32 64 128"

mkdir -p results/raw

clear_caches() {
    echo " -> Clearing OS RAM caches..."
    sync
    if [ "$EUID" -eq 0 ]; then
        echo 3 > /proc/sys/vm/drop_caches
    fi
    sleep 5
}

ssd_rest() {
    echo " -> Clearing OS caches AND resting SSD for Garbage Collection (60s)..."
    sync
    if [ "$EUID" -eq 0 ]; then
        echo 3 > /proc/sys/vm/drop_caches
    fi
    sleep 60
}

echo ""
echo ">>> PHASE 1: SYNCHRONOUS WORKLOADS <<<"

echo "Running: Sequential Write (Sync)..."
iostat -xyz 1 > results/raw/seq_write_sync_iostat.log &
MON_PID=$!
fio --name=seq_write_sync --rw=write --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_write_sync.json
sleep 1
kill $MON_PID
ssd_rest # Write test requires GC rest

echo "Running: Sequential Read (Sync)..."
iostat -xyz 1 > results/raw/seq_read_sync_iostat.log &
MON_PID=$!
fio --name=seq_read_sync --rw=read --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_read_sync.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Random Write (Sync)..."
iostat -xyz 1 > results/raw/rand_write_sync_iostat.log &
MON_PID=$!
fio --name=rand_write_sync --rw=randwrite --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_write_sync.json
sleep 1
kill $MON_PID
ssd_rest # Write test requires GC rest

echo "Running: Random Read (Sync)..."
iostat -xyz 1 > results/raw/rand_read_sync_iostat.log &
MON_PID=$!
fio --name=rand_read_sync --rw=randread --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_read_sync.json
sleep 1
kill $MON_PID
clear_caches


echo ""
echo ">>> PHASE 2: ASYNCHRONOUS WORKLOADS (io_uring) <<<"

for QD in $QDS; do
    echo "------------------------------------------"
    echo "--- Testing Queue Depth: $QD ---"

    echo "Running: Sequential Write (Async, QD=$QD)..."
    iostat -xyz 1 > results/raw/seq_write_async_qd${QD}_iostat.log &
    MON_PID=$!
    fio --name=seq_write_async_qd${QD} --rw=write --ioengine=io_uring --iodepth=$QD --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_write_async_qd${QD}.json
    sleep 1
    kill $MON_PID
    ssd_rest # Write test requires GC rest

    echo "Running: Sequential Read (Async, QD=$QD)..."
    iostat -xyz 1 > results/raw/seq_read_async_qd${QD}_iostat.log &
    MON_PID=$!
    fio --name=seq_read_async_qd${QD} --rw=read --ioengine=io_uring --iodepth=$QD --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_read_async_qd${QD}.json
    sleep 1
    kill $MON_PID
    clear_caches

    echo "Running: Random Write (Async, QD=$QD)..."
    iostat -xyz 1 > results/raw/rand_write_async_qd${QD}_iostat.log &
    MON_PID=$!
    fio --name=rand_write_async_qd${QD} --rw=randwrite --ioengine=io_uring --iodepth=$QD --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_write_async_qd${QD}.json
    sleep 1
    kill $MON_PID
    ssd_rest # Write test requires GC rest

    echo "Running: Random Read (Async, QD=$QD)..."
    iostat -xyz 1 > results/raw/rand_read_async_qd${QD}_iostat.log &
    MON_PID=$!
    fio --name=rand_read_async_qd${QD} --rw=randread --ioengine=io_uring --iodepth=$QD --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_read_async_qd${QD}.json
    sleep 1
    kill $MON_PID
    clear_caches
done


echo ""
echo ">>> PHASE 3: MIXED WORKLOADS <<<"

echo "Prepping file for mixed test: Sequential Write Pass..."
fio --name=seq_prep --rw=write --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output=/dev/null
ssd_rest # Prep was a write, requires GC rest

for QD in $QDS; do
    echo "Running: Seq-Prepped Random Read (Async, QD=$QD)..."
    iostat -xyz 1 > results/raw/seq_to_rand_qd${QD}_iostat.log &
    MON_PID=$!
    fio --name=seq_to_rand_qd${QD} --rw=randread --ioengine=io_uring --iodepth=$QD --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_to_rand_qd${QD}.json
    sleep 1
    kill $MON_PID
    clear_caches
done

rm -f $TEST_FILE
echo ""
echo " All done! Clean raw data is in results/raw/"
