#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON" admin/verify.py
