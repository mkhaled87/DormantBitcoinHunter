#!/bin/sh

# Detect local virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/python" ]; then
        exec .venv/bin/python hunt.py "$@"
    elif [ -f "venv/bin/python" ]; then
        exec venv/bin/python hunt.py "$@"
    fi
fi

exec python3 hunt.py "$@"
