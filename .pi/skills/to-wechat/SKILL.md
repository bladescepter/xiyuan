---
name: to-wechat
description: 把博客文章发布到微信公众号草稿箱 — 自动传图、business-navy 排版、直达草稿箱
---

## 触发词

用户说"发公众号"、"同步到微信"、"微信公众号"时，或发布博客后主动询问要不要同步到微信。

## 前提条件

- 微信公众号 AppID + AppSecret 在本地 `C:/Users/blade/OneDrive/DEV/setting-env/.env`（`WX_APPID` / `WX_APPSECRET`）
- 公众号 IP 白名单只认 **VPS IP 119.28.143.201**（本地 IP 不在白名单）→ 脚本自动起 SSH 动态隧道（`ssh -N -D 1089`），微信 API 请求经 VPS 出口
- 文章 Markdown 在本地 `C:\Obsidian\4_创作\Blog\`（发布时同步到本仓库 `src/content/posts/`），含完整 frontmatter（slug、title、author）

## 工作流

### 一键发布（本地 Git Bash 运行）

```bash
bash C:/Users/blade/OneDrive/DEV/blog-deploy/scripts/to-wechat.sh <slug>
```

自动完成：
1. 从本地 `src/content/posts/` 读文章，提取标题、作者、摘要、slug
2. 起 SSH 隧道（经 VPS 出口满足 IP 白名单，退出时自动清理）
3. 下载所有图片 → webp 转 png（PIL + cygpath 转 Windows 路径）→ 上传微信 CDN（`uploadimg`，不占素材配额）
4. 第一张 OG 图（`/posts/{slug}/index.png`）设封面（`add_material` 永久素材）
5. **business-navy 深蓝+金**主题排版（白底 #ffffff / 深蓝 #0b2445 / 金色 #c9a74a），保留开头 `(ㅅ˘ㅂ˘) Hi~` / 结尾 `( ´ ω ` )ノﾞ Bye~Bye~` 表情装饰
6. 尾部自动添加"本文首发于 xiyuan.wiki"可点击链接；「阅读原文」= https://xiyuan.wiki/posts/{slug}/
7. 创建草稿到公众号后台 → 输出 media_id

### 脚本路径（本地运行，2026-08 起不再依赖旧容器）

| 文件 | 说明 |
|------|------|
| `C:/Users/blade/OneDrive/DEV/blog-deploy/scripts/to-wechat.sh` | 入口：读文章 → SSH 隧道 → 传图 → 调 Python |
| `C:/Users/blade/OneDrive/DEV/blog-deploy/scripts/to-wechat.py` | 后端：Markdown→HTML 转换（business-navy 样式）+ 草稿 API |

> 旧路径 `/opt/data/scripts/`（容器内）与 `HOST=ubuntu@172.17.0.1`（容器 IP）已废弃，2026-08 本地化改造时移除。

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
- 微信编辑器不支持外部字体（`@font-face`），business-navy 使用系统黑体
- 深色模式：business-navy 是白底深蓝字（接近标准色），微信深色模式可可靠自动反转（此前 warm-orange 米色底 `#fdf8f2` 深色模式下白字压浅底看不清）
- 本地运行踩坑（2026-08 修复）：
  - Git Bash 的 `python3` 是 Windows Store 假 shim（退出码 49），必须用 `python`
  - Windows Python 不认 Git Bash `/tmp` 路径，文件路径用 `cygpath -w` 转换
  - `add_material` 上传在 Git Bash `/tmp` 路径下 curl 报 26，同样用 cygpath 转 Windows 路径解决
  - Windows GBK 控制台打印 emoji 会 UnicodeEncodeError，`sys.stdout.reconfigure(encoding='utf-8')` 兜底
  - SSH 隧道清理：`pkill` 杀不掉 Windows ssh.exe，用 `kill $SSH_PID` + `taskkill //F //PID`

## 主题定制

当前固定使用 business-navy 主题（白底 #ffffff / 深蓝 #0b2445 / 金色 #c9a74a，li 前缀 ◆）。如需更换，参考 [jiji262/wechat-publisher](https://github.com/jiji262/wechat-publisher) 的 `assets/themes/` 下的 15 套 JSON 主题文件（在线预览：https://linghucong.js.org/wechat-publisher/），修改 `to-wechat.py` 中的 `STYLES` 字典色值。
