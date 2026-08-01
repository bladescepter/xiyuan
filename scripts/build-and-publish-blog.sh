#!/bin/bash
# 博客发布 — 读取本地笔记文章 → 上传服务器 blog 文件夹 → 构建 → 清缓存
# 用法: ./build-and-publish-blog.sh
# 说明: 文章源为本地笔记库 C:\Obsidian（写作侧），服务器 /opt/data/obsidian_vault 副本已废弃不再读取
set -euo pipefail

HOST="ubuntu@119.28.143.201"
KEY="C:/Users/blade/.ssh/bladescepter.pem"
REMOTE_DIR="/home/ubuntu/blog-astro"
DOTENV="C:/Users/blade/OneDrive/DEV/setting-env/.env"
BLOG_DIR="C:/Obsidian/4_创作/Blog"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o BatchMode=yes"

# ===== 第零步：同步文章（本地笔记 → 服务器 posts） =====
echo "📖 0/4 同步文章..."

# About 页 (0_*.md)
about_file=$(find "$BLOG_DIR" -maxdepth 1 -name '0_*.md' -print -quit)
if [ -n "$about_file" ]; then
  scp $SSH_OPTS "$about_file" "$HOST:$REMOTE_DIR/src/content/pages/about.md"
  echo "  ✅ About 页已更新"
fi

# 文章同步
mkdir -p /tmp/blog_sync
rm -f /tmp/blog_sync/*.md
copied=0
for f in "$BLOG_DIR"/[1-9]*.md; do
  [ -f "$f" ] || continue
  basename=$(basename "$f")
  newname=$(echo "$basename" | sed 's/^[0-9][0-9]*_//')
  cp "$f" "/tmp/blog_sync/$newname"
  copied=$((copied + 1))
done

if [ "$copied" -gt 0 ]; then
  (cd /tmp/blog_sync && tar c *.md 2>/dev/null) | \
    ssh $SSH_OPTS "$HOST" "tar x -C $REMOTE_DIR/src/content/posts/"
  # 删除 Astro 中已不存在的文件
  ssh $SSH_OPTS "$HOST" \
    "cd $REMOTE_DIR/src/content/posts && ls *.md" > /tmp/remote_posts.txt
  while IFS= read -r remote_file; do
    [ -f "/tmp/blog_sync/$remote_file" ] || {
      ssh $SSH_OPTS "$HOST" "rm -f \"$REMOTE_DIR/src/content/posts/$remote_file\""
      echo "  🗑️  移除: $remote_file"
    }
  done < /tmp/remote_posts.txt
  echo "  ✅ $copied 篇文章已同步"
else
  echo "  ⚠️  没有找到文章"
fi
rm -rf /tmp/blog_sync /tmp/remote_posts.txt

# ===== 第一步：子集化（正文） =====
echo "📦 1/4 子集化字体（正文）..."
ssh $SSH_OPTS "$HOST" \
  "cd $REMOTE_DIR && node scripts/subset-body.mjs" || {
    echo "❌ 正文子集化失败"
    exit 1
  }

# ===== 第二步：子集化（OG） =====
echo "📦 2/4 子集化字体（OG）..."
ssh $SSH_OPTS "$HOST" \
  "cd $REMOTE_DIR && node scripts/subset-og.mjs" || {
    echo "❌ OG 子集化失败"
    exit 1
  }

# ===== 第三步：构建 =====
echo "🏗️  3/4 Astro 构建..."
ssh $SSH_OPTS "$HOST" \
  "cd $REMOTE_DIR && source ~/.nvm/nvm.sh && nvm use 22 && pnpm build" || {
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
