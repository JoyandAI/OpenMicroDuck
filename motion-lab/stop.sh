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
  echo "停止 Motion Lab：PID $pid"
  kill -TERM "$pid" 2>/dev/null || true
  while [ "$i" -lt 20 ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 0.25
    i=$((i + 1))
  done
  echo "PID $pid 未在 5 秒内退出，强制结束" >&2
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
    ''|*[!0-9]*) echo "PID 文件无效，已删除：$PID_FILE" >&2; rm -f "$PID_FILE" ;;
    *)
      if server_pid "$pid"; then
        stop_one "$pid" || { echo "无法停止 PID $pid" >&2; exit 1; }
        found=1
      else
        echo "PID 文件已过期，已删除：$PID_FILE"
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
        stop_one "$pid" || { echo "无法停止 PID $pid" >&2; exit 1; }
        found=1
        ;;
      *)
        echo "端口 $PORT 被非 Motion Lab 进程占用，未处理：PID $pid" >&2
        ;;
    esac
  done
fi

rm -f "$PID_FILE"

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 $PORT 仍有监听，未继续处理：" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  exit 1
fi

if [ "$found" -eq 1 ]; then
  echo "Motion Lab 已停止，端口 $PORT 已释放。"
else
  echo "Motion Lab 当前没有运行，端口 $PORT 空闲。"
fi
