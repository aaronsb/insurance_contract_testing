#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python -m venv .venv
    .venv/bin/pip install -q pydantic pytest
fi

PYTHONPATH=. .venv/bin/pytest tests/ "$@"
