#!/bin/bash
# 每日备份博客源码（blog-astro）到 GitHub
# 纯脚本模式（no_agent）：直接 SSH 到宿主机执行 git 提交，不依赖模型
set -euo pipefail

HOST="ubuntu@172.17.0.1"
KEY="/opt/data/.ssh/id_ed25519"
REMOTE_DIR="/home/ubuntu/blog-astro"
TODAY=$(date +%Y-%m-%d)

ssh -i "$KEY" -o StrictHostKeyChecking=no -o BatchMode=yes "$HOST" bash -s <<EOF
set -e
cd "$REMOTE_DIR"
git add -A
if git diff --cached --quiet; then
  echo "[SILENT]"
else
  git commit -m "每日自动备份 $TODAY" >/dev/null
  git push origin main >/dev/null 2>&1 || echo "push 失败"
  echo "博客源码已备份 ($TODAY)"
fi
EOF
