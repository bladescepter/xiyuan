---
name: to-wechat
description: 把博客文章发布到微信公众号草稿箱 — 自动传图、warm-orange 排版、直达草稿箱
---

## 触发词

用户说"发公众号"、"同步到微信"、"微信公众号"时，或发布博客后主动询问要不要同步到微信。

## 前提条件

- 微信公众号 AppID + AppSecret 已存在 `/opt/data/.env`（`WX_APPID` / `WX_APPSECRET`）
- VPS IP（119.28.143.201）已在公众号后台加入 IP 白名单
- 文章 Markdown 文件在本地笔记库 `C:\Obsidian\4_创作\Blog\` 目录下（发布时同步到服务器 Astro posts），含有完整 frontmatter（slug、title、author）

## 工作流

### 一键发布

```bash
bash /opt/data/scripts/to-wechat.sh <文章.md路径>
```

自动完成：
1. 提取文章标题、作者、摘要、slug
2. 下载所有图片 → 上传微信 CDN（`uploadimg` 接口，不占素材配额）
3. 第一张图设为封面（`add_material` 永久素材）
4. **warm-orange 温暖橙调**主题排版（背景 #fdf8f2，暖橙强调 #e58b3a）
5. 尾部自动添加"本文首发于 xiyuan.wiki"可点击链接
6. 「阅读原文」自动填入博客文章 URL（https://xiyuan.wiki/posts/{slug}/）
7. 创建草稿到公众号后台 → 输出 media_id

### 脚本路径

| 文件 | 说明 |
|------|------|
| `/opt/data/scripts/to-wechat.sh` | 入口 shell 脚本：下载图片 → 上传微信 → 调用 Python |
| `/opt/data/scripts/to-wechat.py` | Python 后端：Markdown→HTML 转换 + 草稿 API 调用 |

### API 端点

使用 `/cgi-bin/draft/add`（非 `/cgi-bin/draft/create`），个人订阅号也可用。

### 输出文件

| 文件 | 说明 |
|------|------|
| `{文章名}_wechat.html` | 本地微信版 HTML，可浏览器打开 → 全选复制 → 粘贴编辑器 |
| `{文章名}_wechat_draft.json` | 调试用，发送给微信 API 的完整请求体 |

### 发布后

用户登录 https://mp.weixin.qq.com/cgi-bin/appmsg → 草稿箱 → 预览/发布。

## 注意事项

- 个人订阅号（未认证）**无法**通过 API 自动群发，只能存草稿箱
- access_token 有效期 2 小时，脚本每次调用自动获取
- 封面图走 `add_material`，占用永久素材配额（5000 个上限）
- 正文图走 `uploadimg`，不占配额
- 微信编辑器不支持外部字体（`@font-face`），warm-orange 使用系统黑体

## 主题定制

当前固定使用 warm-orange 主题。如需更换，参考 [jiji262/wechat-publisher](https://github.com/jiji262/wechat-publisher) 的 `assets/themes/` 下的 15 套 JSON 主题文件，修改 `to-wechat.py` 中的 `md_to_wechat_html` 函数样式。
