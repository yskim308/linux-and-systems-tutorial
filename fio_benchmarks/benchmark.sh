#!/bin/bash

# Setup clean folders
mkdir -p results/raw

echo "Running: Sequential Write (Sync)..."
iostat -xz 0.5 > results/raw/seq_write_sync_iostat.log &
MON_PID=$!
fio --name=seq_write_sync --rw=write --ioengine=sync --direct=1 --bs=128k --size=2G --filename=testfile.img --output-format=json --output=results/raw/seq_write_sync.json
kill $MON_PID
sleep 5

echo "Running: Sequential Write (Async)"
iostat -xz 0.5 > results/raw/seq_write_sync_iostat.log &
MON_PID=$!
fio --name=seq_write_async --rw=write --ioengine=io_uring --direct=1 --bs=128k --size=2G --filename=testfile.img --output-format=json --output=results/raw/seq_write_sync.json
kill $MON_PID
sleep 5

echo "Running: Sequential Read (Sync)..."
iostat -xz 0.5 > results/raw/seq_read_async_iostat.log &
MON_PID=$!
fio --name=seq_read_async --rw=read --ioengine=sync --iodepth=32 --direct=1 --bs=128k --size=2G --filename=testfile.img --output-format=json --output=results/raw/seq_read_async.json
kill $MON_PID
sleep 5

echo "Running: Sequential Read (Async)..."
iostat -xz 0.5 > results/raw/seq_read_async_iostat.log &
MON_PID=$!
fio --name=seq_read_async --rw=read --ioengine=io_uring --iodepth=32 --direct=1 --bs=128k --size=2G --filename=testfile.img --output-format=json --output=results/raw/seq_read_async.json
kill $MON_PID
sleep 5

echo "Running: Random Write (Async)..."
iostat -xz 0.5 > results/raw/rand_write_async_iostat.log &
MON_PID=$!
fio --name=rand_write_async --rw=randwrite --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=2G --filename=testfile.img --output-format=json --output=results/raw/rand_write_async.json
kill $MON_PID
sleep 5

echo "Running: Random Write (Sync)..."
iostat -xz 0.5 > results/raw/rand_write_async_iostat.log &
MON_PID=$!
fio --name=rand_write_async --rw=randwrite --ioengine=sync --iodepth=32 --direct=1 --bs=4k --size=2G --filename=testfile.img --output-format=json --output=results/raw/rand_write_async.json
kill $MON_PID
sleep 5

echo "Running: Random Read (Async)..."
iostat -xz 0.5 > results/raw/rand_read_async_iostat.log &
MON_PID=$!
fio --name=rand_read_async --rw=randread --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=2G --filename=testfile.img --output-format=json --output=results/raw/rand_read_async.json
kill $MON_PID
sleep 5

echo "Running: Random Read (Sync)..."
iostat -xz 0.5 > results/raw/rand_read_async_iostat.log &
MON_PID=$!
fio --name=rand_read_async --rw=randread --ioengine=sync --iodepth=32 --direct=1 --bs=4k --size=2G --filename=testfile.img --output-format=json --output=results/raw/rand_read_async.json
kill $MON_PID
sleep 5

echo "Running: Seq Write then 4k Random Read..."
fio --name=seq_prep --rw=write --ioengine=sync --direct=1 --bs=128k --size=2G --filename=testfile.img --output=/dev/null
sleep 5
iostat -xz 0.5 > results/raw/seq_to_rand_iostat.log &
MON_PID=$!
fio --name=seq_to_rand --rw=randread --ioengine=io_uring --iodepth=32 --direct=1 --bs=4k --size=2G --filename=testfile.img --output-format=json --output=results/raw/seq_to_rand.json
kill $MON_PID
rm -f testfile.img
echo "All done! Raw data is in results/raw/"
