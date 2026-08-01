#!/usr/bin/env bash
# to-wechat.sh — 将博客文章转为微信公众号草稿
# 用法: to-wechat.sh <slug>
# 示例: to-wechat.sh 007
#       to-wechat.sh 怎样同步Blog文章到公众号

set -euo pipefail

source /opt/data/.env
HOST="ubuntu@172.17.0.1"
ASTRO_POSTS="/home/ubuntu/blog-astro/src/content/posts"
SLUG="${1:?用法: to-wechat.sh <slug>}"

# 从 Astro posts 目录获取文章
echo "📖 读取博客文章..."
# 先按 slug 找（frontmatter 里 slug 字段匹配）
# 再按文件名找（文件名不含数字前缀）
POST_FILE=$(ssh "$HOST" \
  "grep -rl 'slug: *\"${SLUG}\"' \"$ASTRO_POSTS/\" 2>/dev/null | head -1; \
   [ -z \"$(grep -rl 'slug: *\"${SLUG}\"' \"$ASTRO_POSTS/\" 2>/dev/null)\" ] && \
   ls \"$ASTRO_POSTS/${SLUG}.md\" 2>/dev/null; \
   [ -z \"$(ls \"$ASTRO_POSTS/${SLUG}.md\" 2>/dev/null)\" ] && \
   ls \"$ASTRO_POSTS/\"*\"${SLUG}\"*.md 2>/dev/null | head -1" || true)

[ -z "$POST_FILE" ] && { echo "❌ 未找到文章: $SLUG"; exit 1; }

POST_CONTENT=$(ssh "$HOST" "cat \"$POST_FILE\"")

# 提取 frontmatter
TITLE=$(echo "$POST_CONTENT" | sed -n '/^title:/s/^title: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' | head -1 | sed 's/^ *//;s/ *$//')
[ -z "$TITLE" ] && TITLE="未命名文章"

AUTHOR=$(echo "$POST_CONTENT" | sed -n '/^author:/s/^author: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' | head -1 | sed 's/^ *//;s/ *$//')
[ -z "$AUTHOR" ] && AUTHOR="陆西园"

DIGEST=$(echo "$POST_CONTENT" | sed -n '/^description:/s/^description: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' | head -1 | sed 's/^ *//;s/ *$//')

# 优先用 frontmatter slug，没有则用文件名（Astro会自动用文件名做路径）
FULL_SLUG=$(echo "$POST_CONTENT" | sed -n '/^slug:/s/^slug: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' | head -1 | sed 's/^ *//;s/ *$//')
if [ -z "$FULL_SLUG" ]; then
  POST_BASENAME=$(ssh "$HOST" "basename \"$POST_FILE\" .md")
  FULL_SLUG="$POST_BASENAME"
fi

# 提取正文（去掉 frontmatter）
BODY=$(echo "$POST_CONTENT" | sed '1,/^---$/d' | sed '/^---$/,$d')

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
echo "$BODY" > "$TMPDIR/body.md"

IMAGES=$(echo "$BODY" | grep -oP '!\[.*?\]\(\Khttps?://[^)]+' || true)

echo "📝 $TITLE"
echo "🖼️  $(echo "$IMAGES" | grep -c . || echo 0) 张图片"

# 获取 access_token
TOKEN_JSON=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${WX_APPID}&secret=${WX_APPSECRET}")
TOKEN=$(echo "$TOKEN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -z "$TOKEN" ] && { echo "❌ token 失败: $TOKEN_JSON"; exit 1; }

# 上传正文图片
echo ""
cp "$TMPDIR/body.md" "$TMPDIR/body_updated.md"
IMG_COUNT=0

for url in $IMAGES; do
  [ -z "$url" ] && continue
  IMG_COUNT=$((IMG_COUNT + 1))
  echo -n "  [$IMG_COUNT] 上传..."

  EXT="${url##*.}"; EXT="${EXT%%\?*}"; [ -z "$EXT" ] && EXT="png"
  curl -sL -o "$TMPDIR/img.$EXT" "$url"

  # webp 转 png
  if [ "$EXT" = "webp" ]; then
    PYTHONPATH=/opt/data/pylib python3 -c "from PIL import Image; Image.open('$TMPDIR/img.webp').save('$TMPDIR/img.png')" 2>/dev/null || true
    EXT="png"
  fi

  RESP=$(curl -s -F "media=@$TMPDIR/img.$EXT" \
    "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${TOKEN}")
  WX_URL=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null)

  if [ -n "$WX_URL" ]; then
    echo " ✅"
    sed -i "s|$url|$WX_URL|g" "$TMPDIR/body_updated.md"
  else
    echo " ❌ $RESP"
  fi
done

# OG 图做封面
echo "  [封面] 下载 OG 图..."
OG_URL="https://xiyuan.wiki/posts/${FULL_SLUG}/index.png"
echo "       ${OG_URL}"
THUMB_MEDIA_ID=""
curl -sL -o "$TMPDIR/og_cover.png" "$OG_URL" || true
if [ -s "$TMPDIR/og_cover.png" ]; then
  THUMB_RESP=$(curl -s -F "media=@$TMPDIR/og_cover.png;type=image;filename=cover.png" \
    "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=image")
  THUMB_MEDIA_ID=$(echo "$THUMB_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('media_id',''))" 2>/dev/null)
  if [ -n "$THUMB_MEDIA_ID" ]; then
    echo "       → 封面 media_id: $THUMB_MEDIA_ID"
  else
    echo "       ⚠️  封面上传失败: $THUMB_RESP"
  fi
else
  echo "       ⚠️  OG 图下载失败（博客还没部署？）"
fi

[ -z "$THUMB_MEDIA_ID" ] && echo "       ⚠️  无封面图（草稿可能失败）"

# 调用Python处理HTML并创建草稿
SOURCE_URL="https://xiyuan.wiki/posts/${FULL_SLUG}/"
echo "🔗 原文链接: $SOURCE_URL"

python3 /opt/data/scripts/to-wechat.py \
  "$TMPDIR/body_updated.md" \
  "$TITLE" "$AUTHOR" "$TOKEN" \
  "${TMPDIR}/output.html" \
  "$DIGEST" "$THUMB_MEDIA_ID" "$SOURCE_URL"
