#!/usr/bin/env bash
set -euo pipefail

# 一键关闭前端(Vite)与后端(Django)开发服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$REPO_ROOT/.pids"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

kill_by_port() {
  local name="$1"; local port="$2"
  echo "${name}: 检查端口 ${port} 的遗留进程..."
  local killed=false
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -ti ":${port}" || true)
    if [[ -n "$pids" ]]; then
      echo "${name}: 发现进程 ${pids}，发送 SIGTERM"
      kill $pids || true
      killed=true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    echo "${name}: 使用 fuser 杀进程"
    fuser -k "${port}/tcp" || true
    killed=true
  else
    # 使用 ss 解析 PID
    local ss_out
    ss_out=$(ss -lptn "sport = :${port}" 2>/dev/null || true)
    if [[ -n "$ss_out" ]]; then
      local pid
      pid=$(echo "$ss_out" | sed -nE 's/.*pid=([0-9]+).*/\1/p' | head -n1)
      if [[ -n "$pid" ]]; then
        echo "${name}: ss 检测到 PID ${pid}，发送 SIGTERM"
        kill "$pid" || true
        killed=true
      fi
    fi
  fi
  if [[ "$killed" == true ]]; then
    echo "${name}: 已尝试清理端口 ${port} 的进程。"
  else
    echo "${name}: 未发现端口 ${port} 的活跃进程。"
  fi
}

stop_one() {
  local name="$1"; local pid_file="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "${name}: 未发现 PID 文件，可能未运行。"
    return 0
  fi
  local pid
  pid="$(cat "$pid_file" || true)"
  if [[ -z "$pid" ]]; then
    echo "${name}: PID 文件为空，跳过。"
    rm -f "$pid_file"
    return 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "${name}: 进程 ${pid} 不存在，清理 PID 文件。"
    rm -f "$pid_file"
    return 0
  fi
  echo "${name}: 正在终止 PID ${pid} ..."
  kill "$pid" || true
  # 等待退出
  for i in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "${name}: 已关闭。"
      rm -f "$pid_file"
      return 0
    fi
    sleep 0.5
  done
  echo "${name}: 进程未响应，发送 SIGKILL。"
  kill -9 "$pid" || true
  rm -f "$pid_file"
}

stop_one "前端" "$PID_DIR/frontend.pid"
stop_one "后端" "$PID_DIR/backend.pid"

kill_by_port "前端" "$FRONTEND_PORT"
kill_by_port "后端" "$BACKEND_PORT"

echo "已执行关闭操作；若仍存在端口占用，可手动检查进程。"