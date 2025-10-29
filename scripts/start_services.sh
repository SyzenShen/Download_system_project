#!/usr/bin/env bash
set -euo pipefail

# 一键启动前端(Vite)与后端(Django)开发服务，常驻后台运行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 允许通过环境变量覆盖默认端口
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

LOG_DIR="$REPO_ROOT/logs"
PID_DIR="$REPO_ROOT/.pids"
FRONTEND_DIR="$REPO_ROOT/frontend"
BACKEND_DIR="$REPO_ROOT"
NODE_BIN="$REPO_ROOT/.node/bin/node"
VITE_BIN="$REPO_ROOT/frontend/node_modules/vite/bin/vite.js"

mkdir -p "$LOG_DIR" "$PID_DIR"

is_port_up() {
  local port="$1"
  curl -sSfI "http://localhost:${port}" --max-time 1 >/dev/null 2>&1
}

wait_for_port() {
  local name="$1"; local port="$2"; local timeout="${3:-20}"
  echo "等待 ${name} 在端口 ${port} 上线..."
  for ((i=0; i<timeout; i++)); do
    if is_port_up "$port"; then
      echo "${name} 已在 http://localhost:${port}/ 就绪"
      return 0
    fi
    sleep 1
  done
  echo "警告: ${name} 在 ${timeout}s 内未就绪，请检查日志。"
  return 1
}

start_frontend() {
  echo "启动前端服务 (Vite) ..."
  # 若端口已被占用，认为已有服务在运行，直接跳过启动
  if is_port_up "$FRONTEND_PORT"; then
    echo "前端端口 ${FRONTEND_PORT} 已有服务，就绪，跳过启动。"
    return 0
  fi
  if [[ ! -x "$NODE_BIN" ]]; then
    echo "错误: Node 未找到：$NODE_BIN"
    exit 1
  fi
  if [[ ! -f "$VITE_BIN" ]]; then
    echo "错误: Vite 未安装：$VITE_BIN 不存在。请在 frontend 目录安装依赖。"
    exit 1
  fi
  # 若 PID 文件存在且进程仍在运行，也跳过
  if [[ -f "$PID_DIR/frontend.pid" ]]; then
    local pid
    pid="$(cat "$PID_DIR/frontend.pid" || true)"
    if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "前端已在运行 (PID ${pid})，跳过启动。"
      return 0
    fi
  fi
  (
    cd "$FRONTEND_DIR"
    nohup "$NODE_BIN" "$VITE_BIN" --host --port "$FRONTEND_PORT" --strictPort \
      > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
  )
  wait_for_port "前端" "$FRONTEND_PORT" 20
}

start_backend() {
  echo "启动后端服务 (Django) ..."
  # 若端口已被占用，认为已有服务在运行，直接跳过启动
  if is_port_up "$BACKEND_PORT"; then
    echo "后端端口 ${BACKEND_PORT} 已有服务，就绪，跳过启动。"
    return 0
  fi
  if [[ -f "$PID_DIR/backend.pid" ]]; then
    local pid
    pid="$(cat "$PID_DIR/backend.pid" || true)"
    if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "后端已在运行 (PID ${pid})，跳过启动。"
      return 0
    fi
  fi
  (
    cd "$BACKEND_DIR"
    nohup python3 manage.py runserver 0.0.0.0:"$BACKEND_PORT" \
      > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
  )
  wait_for_port "后端" "$BACKEND_PORT" 20
}

start_frontend
start_backend

echo "已尝试启动：前端 http://localhost:${FRONTEND_PORT}/，后端 http://localhost:${BACKEND_PORT}/"
echo "日志: $LOG_DIR/frontend.log, $LOG_DIR/backend.log"
echo "PID 文件: $PID_DIR/frontend.pid, $PID_DIR/backend.pid"