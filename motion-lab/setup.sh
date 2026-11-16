#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Could not find $PYTHON. Install Python 3.9+ first." >&2
  exit 1
fi

"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9 or newer is required; found %s" % sys.version.split()[0])
print("Python", sys.version.split()[0], "at", sys.executable)
PY

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip wheel
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Dependencies installed in $(pwd)/.venv"
echo "Start with: ./run.sh"
