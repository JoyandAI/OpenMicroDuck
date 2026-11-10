#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

exec "$PYTHON" server.py --host 127.0.0.1 --port 18765 --open "$@"
