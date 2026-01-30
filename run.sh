#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ -d .venv ]; then
    # shellcheck source=/dev/null
    . .venv/bin/activate
fi
exec uvicorn src.main:app --reload
