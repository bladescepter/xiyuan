#!/bin/bash
# 博客发布 — 本地文章 → GitHub(xiyuan) → 服务器 git pull 构建 → Cloudflare MCP 清缓存
# 用法: ./build-and-publish-blog.sh
# 说明: 本脚本在本机 Git Bash 运行。文章源为本地笔记库 C:\Obsidian（写作侧），
#       经 git 推送到 bladescepter/xiyuan 仓库，服务器 /home/ubuntu/blog-astro git pull 即完成同步。
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

HOST="ubuntu@119.28.143.201"
KEY="C:/Users/blade/.ssh/bladescepter.pem"
REMOTE_DIR="/home/ubuntu/blog-astro"
BLOG_DIR="C:/Obsidian/4_创作/Blog"
POSTS_DIR="src/content/posts"
PAGES_DIR="src/content/pages"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o BatchMode=yes"
PURGE_URL="https://xiyuan.wiki/fonts/lxgw-body.woff2"

if ! command -v pi >/dev/null 2>&1; then
  echo "❌ 未找到 Pi CLI，无法通过 Cloudflare MCP 清除缓存。" >&2
  exit 1
fi
MCP_STATUS=$(pi mcp list 2>&1) || {
  echo "❌ 无法连接 Cloudflare MCP。请先完成 cloudflare-api 登录。" >&2
  printf '%s\n' "$MCP_STATUS" >&2
  exit 1
}
if ! printf '%s\n' "$MCP_STATUS" | grep -Fq 'cloudflare-api: connected'; then
  echo "❌ cloudflare-api MCP 未连接，停止发布。" >&2
  printf '%s\n' "$MCP_STATUS" >&2
  exit 1
fi
echo "🔌 Cloudflare MCP 已连接"

# ===== 第零步：同步文章（本地笔记 → 本仓库 src/content） =====
echo "📖 0/4 同步文章..."

# 清空 posts 重建（git add -A 会自动记录删除）
rm -f "$POSTS_DIR"/*.md
copied=0
for f in "$BLOG_DIR"/[1-9]*.md; do
  [ -f "$f" ] || continue
  newname=$(basename "$f" | sed 's/^[0-9][0-9]*_//')
  cp "$f" "$POSTS_DIR/$newname"
  copied=$((copied + 1))
done

# About 页 (0_*.md)
about_file=$(find "$BLOG_DIR" -maxdepth 1 -name '0_*.md' -print -quit)
if [ -n "$about_file" ]; then
  cp "$about_file" "$PAGES_DIR/about.md"
  echo "  ✅ About 页已更新"
fi
echo "  ✅ $copied 篇文章已同步"

# ===== 第一步：推送到 GitHub =====
echo "🚀 1/4 推送文章到 GitHub..."
git add -A "$POSTS_DIR" "$PAGES_DIR"
if git diff --cached --quiet; then
  echo "  ⚠️  文章无变化，跳过推送"
else
  git commit -m "发布博客 $(date +%Y-%m-%d)" >/dev/null
  git push origin main || {
    echo "❌ 推送失败"
    exit 1
  }
  echo "  ✅ 已推送"
fi

# ===== 第二步：服务器拉取并子集化 =====
echo "📦 2/4 服务器拉取 + 子集化..."
ssh $SSH_OPTS "$HOST" \
  "cd $REMOTE_DIR && git pull --ff-only origin main && \
   node scripts/subset-body.mjs && node scripts/subset-og.mjs" || {
    echo "❌ 拉取/子集化失败"
    exit 1
  }

# ===== 第三步：构建 =====
echo "🏗️  3/4 Astro 构建..."
ssh $SSH_OPTS "$HOST" \
  "cd $REMOTE_DIR && source ~/.nvm/nvm.sh && nvm use 22 --silent && pnpm build" || {
    echo "❌ 构建失败"
    exit 1
  }

# ===== 第四步：通过 Cloudflare MCP 清 CDN 缓存 =====
echo "🧹 4/4 通过 Cloudflare MCP 清除字体缓存..."
MCP_PROMPT=$(cat <<PROMPT
Use only the configured Cloudflare API MCP server cloudflare-api through codemode, with its search and execute tools. Do not use shell, direct HTTP, or any other integration.

Purge exactly one cached file URL: $PURGE_URL

Use the MCP search tool to confirm the Cloudflare API zone lookup and purge_cache endpoints. Then use the MCP execute tool to GET /zones with the exact name filter xiyuan.wiki. Continue only if exactly one returned zone has the exact name xiyuan.wiki. If not, do not make a purge call.

For exactly one match, use the MCP execute tool to POST /zones/{zone_id}/purge_cache with body {"files":["$PURGE_URL"]}. Do not purge all, prefixes, or any other URLs. Do not include account identifiers or credentials in your response.

Return exactly one JSON object on one line and nothing else. Return {"zone_matches":1,"purge_success":true} only when Cloudflare confirms success. On any failure return {"zone_matches":N,"purge_success":false}, where N is the exact match count if known, otherwise 0.
PROMPT
)
if ! MCP_RESULT=$(pi --print --no-session --no-context-files --tools +codemode "$MCP_PROMPT"); then
  echo "❌ Cloudflare MCP 缓存清理调用失败。" >&2
  exit 1
fi
if ! printf '%s\n' "$MCP_RESULT" | python -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("zone_matches") == 1 and d.get("purge_success") is True else 1)' 2>/dev/null; then
  echo "❌ Cloudflare MCP 未确认对唯一字体 URL 清理成功：" >&2
  printf '%s\n' "$MCP_RESULT" >&2
  exit 1
fi
echo "✅ Cloudflare MCP 已清理指定字体 URL"

echo ""
echo "🎉 发布完成！"
echo "   访问 https://xiyuan.wiki 查看"
