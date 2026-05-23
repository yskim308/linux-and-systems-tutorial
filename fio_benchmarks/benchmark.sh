#!/bin/bash

TEST_SIZE="5G"
TEST_FILE="testfile.img"

# Setup clean folders
mkdir -p results/raw

clear_caches() {
    sync
    if [ "$EUID" -eq 0 ]; then
        echo 3 > /proc/sys/vm/drop_caches
    fi
    sleep 5
}

echo "Running: Sequential Write (Sync)..."
iostat -xyz 1 > results/raw/seq_write_sync_iostat.log &
MON_PID=$!
fio --name=seq_write_sync --rw=write --ioengine=sync --direct=1 --bs=128k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_write_sync.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Sequential Write (Async)..."
iostat -xyz 1 > results/raw/seq_write_async_iostat.log &
MON_PID=$!
fio --name=seq_write_async --rw=write --ioengine=io_uring --iodepth=32 --direct=1 --bs=128k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_write_async.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Sequential Read (Sync)..."
iostat -xyz 1 > results/raw/seq_read_sync_iostat.log &
MON_PID=$!
fio --name=seq_read_sync --rw=read --ioengine=sync --direct=1 --bs=128k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_read_sync.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Sequential Read (Async)..."
iostat -xyz 1 > results/raw/seq_read_async_iostat.log &
MON_PID=$!
fio --name=seq_read_async --rw=read --ioengine=io_uring --iodepth=32 --direct=1 --bs=128k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_read_async.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Random Write (Sync)..."
iostat -xyz 1 > results/raw/rand_write_sync_iostat.log &
MON_PID=$!
fio --name=rand_write_sync --rw=randwrite --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_write_sync.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Random Write (Async)..."
iostat -xyz 1 > results/raw/rand_write_async_iostat.log &
MON_PID=$!
fio --name=rand_write_async --rw=randwrite --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_write_async.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Random Read (Sync)..."
iostat -xyz 1 > results/raw/rand_read_sync_iostat.log &
MON_PID=$!
fio --name=rand_read_sync --rw=randread --ioengine=sync --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_read_sync.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Random Read (Async)..."
iostat -xyz 1 > results/raw/rand_read_async_iostat.log &
MON_PID=$!
fio --name=rand_read_async --rw=randread --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/rand_read_async.json
sleep 1
kill $MON_PID
clear_caches

echo "Running: Seq Write then 4k Random Read..."
fio --name=seq_prep --rw=write --ioengine=sync --direct=1 --bs=128k --size=$TEST_SIZE --filename=$TEST_FILE --output=/dev/null
clear_caches
iostat -xyz 1 > results/raw/seq_to_rand_iostat.log &
MON_PID=$!
fio --name=seq_to_rand --rw=randread --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=$TEST_SIZE --filename=$TEST_FILE --output-format=json --output=results/raw/seq_to_rand.json
sleep 1
kill $MON_PID

rm -f $TEST_FILE
echo "All done! Clean raw data is in results/raw/"
