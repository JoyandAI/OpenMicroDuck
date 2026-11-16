#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

PORT="${PORT:-18765}"
PID_FILE="${PID_FILE:-$APP_DIR/.motion-lab.pid}"

server_pid() {
  local pid="$1" cmd
  kill -0 "$pid" 2>/dev/null || return 1
  cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  case "$cmd" in
    *server.py*) return 0 ;;
    *) return 1 ;;
  esac
}

stop_one() {
  local pid="$1" i=0
  if ! server_pid "$pid"; then
    return 1
  fi
  echo "Stopping Motion Lab: PID $pid"
  kill -TERM "$pid" 2>/dev/null || true
  while [ "$i" -lt 20 ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 0.25
    i=$((i + 1))
  done
  echo "PID $pid did not exit within 5 seconds; forcing termination" >&2
  kill -KILL "$pid" 2>/dev/null || true
  sleep 0.3
  if kill -0 "$pid" 2>/dev/null; then
    return 1
  fi
  return 0
}

found=0
if [ -f "$PID_FILE" ]; then
  pid="$(tr -d '[:space:]' < "$PID_FILE" 2>/dev/null || true)"
  case "$pid" in
    ''|*[!0-9]*) echo "Invalid PID file removed: $PID_FILE" >&2; rm -f "$PID_FILE" ;;
    *)
      if server_pid "$pid"; then
        stop_one "$pid" || { echo "Could not stop PID $pid" >&2; exit 1; }
        found=1
      else
        echo "Stale PID file removed: $PID_FILE"
        rm -f "$PID_FILE"
      fi
      ;;
  esac
fi

if [ "$found" -eq 0 ] && command -v lsof >/dev/null 2>&1; then
  for pid in $(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true); do
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$cmd" in
      *server.py*)
        stop_one "$pid" || { echo "Could not stop PID $pid" >&2; exit 1; }
        found=1
        ;;
      *)
        echo "Port $PORT is occupied by a non-Motion Lab process; leaving PID $pid alone" >&2
        ;;
    esac
  done
fi

rm -f "$PID_FILE"

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT still has a listener; leaving it alone:" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  exit 1
fi

if [ "$found" -eq 1 ]; then
  echo "Motion Lab stopped; port $PORT is free."
else
  echo "Motion Lab is not running; port $PORT is free."
fi
