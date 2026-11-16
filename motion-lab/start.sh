#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-18765}"
FPS="${FPS:-24}"
QUALITY="${QUALITY:-78}"
PID_FILE="${PID_FILE:-$APP_DIR/.motion-lab.pid}"
LOG_FILE="${LOG_FILE:-$APP_DIR/.motion-lab.log}"
DISPLAY_HOST="$HOST"
if [ "$DISPLAY_HOST" = "0.0.0.0" ]; then
  DISPLAY_HOST="127.0.0.1"
fi
URL="http://${DISPLAY_HOST}:${PORT}/"

open_ui() {
  if [ "${NO_OPEN:-0}" = "1" ]; then
    echo "NO_OPEN=1: skipping automatic browser launch."
    return 0
  fi

  case "$(uname -s)" in
    Darwin)
      if command -v open >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 &
        return 0
      fi
      ;;
    Linux)
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 &
        return 0
      fi
      ;;
  esac

  echo "Could not find a browser launcher. Open this URL manually: $URL"
}

running_pid() {
  [ -f "$PID_FILE" ] || return 1
  local pid
  pid="$(tr -d '[:space:]' < "$PID_FILE" 2>/dev/null || true)"
  case "$pid" in
    ''|*[!0-9]*) return 1 ;;
  esac
  kill -0 "$pid" 2>/dev/null || return 1
  local cmd
  cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  case "$cmd" in
    *server.py*) printf '%s\n' "$pid"; return 0 ;;
    *) return 1 ;;
  esac
}

find_python() {
  local py candidate
  if [ -n "${MOTION_LAB_PYTHON:-}" ]; then
    if "$MOTION_LAB_PYTHON" -c 'import mujoco, onnxruntime, numpy, PIL' >/dev/null 2>&1; then
      printf '%s\n' "$MOTION_LAB_PYTHON"
      return 0
    fi
    echo "MOTION_LAB_PYTHON is set but missing mujoco/onnxruntime/numpy/Pillow: $MOTION_LAB_PYTHON" >&2
    return 1
  fi

  for candidate in \
    "$APP_DIR/.venv/bin/python" \
    python3 \
    python3.12 python3.11 python3.10 python3.9; do
    if [ -x "$candidate" ]; then
      py="$candidate"
    elif command -v "$candidate" >/dev/null 2>&1; then
      py="$(command -v "$candidate")"
    else
      continue
    fi
    if "$py" -c 'import mujoco, onnxruntime, numpy, PIL' >/dev/null 2>&1; then
      printf '%s\n' "$py"
      return 0
    fi
  done
  return 1
}

if pid="$(running_pid)"; then
  echo "Motion Lab is already running: PID $pid"
  echo "URL: $URL"
  open_ui
  exit 0
fi

if [ -f "$PID_FILE" ]; then
  rm -f "$PID_FILE"
fi

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is in use by another process:" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  exit 1
fi

PYTHON="$(find_python)" || {
  echo "Could not find Python with mujoco / onnxruntime / numpy / Pillow installed." >&2
  echo "Run ./setup.sh first, or use MOTION_LAB_PYTHON=/path/to/python ./start.sh" >&2
  exit 1
}

echo "Using Python: $PYTHON"
nohup "$PYTHON" server.py --host "$HOST" --port "$PORT" --fps "$FPS" --quality "$QUALITY" \
  >"$LOG_FILE" 2>&1 &
PID=$!
printf '%s\n' "$PID" > "$PID_FILE"

for _ in $(seq 1 40); do
  if curl -fsS --max-time 1 "$URL/api/state" >/dev/null 2>&1; then
    echo "Motion Lab started"
    echo "URL:  $URL"
    echo "PID:  $PID"
    echo "Log: $LOG_FILE"
    open_ui
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    break
  fi
  sleep 0.25
done

echo "Motion Lab failed to start. Recent log output:" >&2
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
tail -n 30 "$LOG_FILE" >&2 || true
exit 1
