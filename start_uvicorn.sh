#!/bin/bash

# Calculate the number of workers based on the CPU count
CPU_COUNT=$(nproc)
WORKER_COUNT=$((CPU_COUNT * 2 + 1))

# Start Uvicorn with the calculated number of workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $WORKER_COUNT