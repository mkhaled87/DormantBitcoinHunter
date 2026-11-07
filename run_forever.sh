#!/bin/sh

# Trap SIGINT and SIGTERM so the shell script exits immediately when interrupted
trap 'echo ""; echo "Shutting down runner..."; exit 0' INT TERM

# Detect local virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/python" ]; then
        PYTHON_EXEC=".venv/bin/python"
    elif [ -f "venv/bin/python" ]; then
        PYTHON_EXEC="venv/bin/python"
    else
        PYTHON_EXEC="python3"
    fi
else
    PYTHON_EXEC="python3"
fi

clear
echo "Starting Dormant Bitcoin Hunter loop..."
echo "Press [q] or [Ctrl+C] to stop."
echo ""

while true; do
    "$PYTHON_EXEC" hunt.py
    exit_code=$?

    # If hunt.py exited with a non-zero code (user pressed 'q' or Ctrl+C), stop looping
    if [ $exit_code -ne 0 ]; then
        echo "Hunter stopped by user."
        exit 0
    fi

    # Brief pause between cycles
    sleep 1
done
