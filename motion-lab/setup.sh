#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "未找到 $PYTHON。请先安装 Python 3.9+。" >&2
  exit 1
fi

"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("需要 Python 3.9 或更新版本；当前为 %s" % sys.version.split()[0])
print("Python", sys.version.split()[0], "at", sys.executable)
PY

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip wheel
.venv/bin/python -m pip install -r requirements.txt

echo
echo "依赖已安装到 $(pwd)/.venv"
echo "启动：./run.sh"
