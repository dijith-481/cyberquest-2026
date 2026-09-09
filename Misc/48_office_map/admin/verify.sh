#!/bin/sh
# Verifies the Office Map handout without any browser.
set -e
cd "$(dirname "$0")/.."
python3 "$(dirname "$0")/validate.py" --check-only
echo "VERIFY OK"
