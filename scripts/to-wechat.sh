#!/usr/bin/env bash
# 跨平台 Bash 启动器；主要逻辑由相邻的 Python 脚本完成。
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="$PYTHON"
elif [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* || "${OSTYPE:-}" == win32* ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  else
    echo "错误：找不到 Python 3。" >&2
    exit 1
  fi
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "错误：找不到 Python 3。" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/to-wechat.py" "$@"
