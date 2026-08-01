#!/bin/bash
# 博客发布 — 本地文章 → GitHub(xiyuan) → 服务器 git pull 构建 → 清缓存
# 用法: ./build-and-publish-blog.sh
# 说明: 本脚本在本机 Git Bash 运行。文章源为本地笔记库 C:\Obsidian（写作侧），
#       经 git 推送到 bladescepter/xiyuan 仓库，服务器 /home/ubuntu/blog-astro git pull 即完成同步。
set -euo pipefail

HOST="ubuntu@119.28.143.201"
KEY="C:/Users/blade/.ssh/bladescepter.pem"
REMOTE_DIR="/home/ubuntu/blog-astro"
DOTENV="C:/Users/blade/OneDrive/DEV/setting-env/.env"
BLOG_DIR="C:/Obsidian/4_创作/Blog"
POSTS_DIR="src/content/posts"
PAGES_DIR="src/content/pages"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o BatchMode=yes"

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

# ===== 第四步：清 CDN 缓存 =====
echo "🧹 4/4 清除 Cloudflare 缓存..."
source "$DOTENV"
PURGE_URLS='{"files":["https://xiyuan.wiki/fonts/lxgw-body.woff2"]}'
RESULT=$(curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PURGE_URLS")

if echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('success') else 1)" 2>/dev/null; then
  echo "✅ 缓存清除成功"
else
  echo "⚠️  缓存清除失败: $(echo "$RESULT" | python -c 'import sys,json; print(json.load(sys.stdin).get(\"errors\",[{}])[0].get(\"message\",\"unknown\"))' 2>/dev/null || echo 'unknown')"
fi

echo ""
echo "🎉 发布完成！"
echo "   访问 https://xiyuan.wiki 查看"
