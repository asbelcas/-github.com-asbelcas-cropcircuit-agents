#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/runtime/ops_watchdog.pid"
LOG_FILE="$ROOT_DIR/logs/ops_watchdog.log"
ROLLUP_FILE="$ROOT_DIR/logs/status_rollup.log"

cmd="${1:-status}"

running_pid() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "${pid:-}" ]] && ps -p "$pid" >/dev/null 2>&1; then
      echo "$pid"
      return 0
    fi
  fi
  return 1
}

do_start() {
  if pid="$(running_pid)"; then
    echo "ops_watchdog already running (pid=$pid)"
    return 0
  fi
  cd "$ROOT_DIR"
  nohup bash -lc 'bash bin/ops_watchdog.sh' >/dev/null 2>&1 & disown
  sleep 1
  if pid="$(running_pid)"; then
    echo "ops_watchdog started (pid=$pid)"
  else
    echo "ops_watchdog start attempted, but pid not confirmed" >&2
    return 1
  fi
}

do_stop() {
  if pid="$(running_pid)"; then
    kill "$pid" || true
    sleep 1
    if ps -p "$pid" >/dev/null 2>&1; then
      echo "ops_watchdog still running (pid=$pid), sending SIGKILL"
      kill -9 "$pid" || true
    fi
    rm -f "$PID_FILE"
    echo "ops_watchdog stopped"
  else
    echo "ops_watchdog not running"
  fi
}

do_status() {
  if pid="$(running_pid)"; then
    echo "status=running pid=$pid"
  else
    echo "status=stopped"
  fi
  [[ -f "$LOG_FILE" ]] && tail -n 5 "$LOG_FILE" || true
  [[ -f "$ROLLUP_FILE" ]] && tail -n 5 "$ROLLUP_FILE" || true
}

case "$cmd" in
start) do_start ;;
stop) do_stop ;;
restart)
  do_stop
  do_start
  ;;
status) do_status ;;
logs)
  echo "--- $LOG_FILE ---"
  [[ -f "$LOG_FILE" ]] && tail -n 40 "$LOG_FILE" || echo "missing"
  echo "--- $ROLLUP_FILE ---"
  [[ -f "$ROLLUP_FILE" ]] && tail -n 40 "$ROLLUP_FILE" || echo "missing"
  ;;
*)
  echo "usage: $0 {status|start|stop|restart|logs}" >&2
  exit 2
  ;;
esac

