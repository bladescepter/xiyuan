---
name: to-wechat
description: 把博客文章转换为微信公众号草稿；Python 主脚本支持 Linux、macOS、Windows
---

## 触发词

用户说“发公众号”“同步到微信”“微信公众号”时，或发布博客后主动询问要不要同步到微信。

## 能力边界

- 脚本调用微信 [`draft/add` 新增草稿接口](https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html)，只创建公众号草稿，不会自动群发；最终由用户在公众号后台预览、编辑并发布。
- 微信接口要求图文草稿提供永久素材 `thumb_media_id`；封面缺失或上传失败时停止创建草稿。
- 封面通过永久素材接口上传，会占用公众号永久素材配额；正文图片通过 `uploadimg` 上传。
- 新建草稿等写接口不自动重试，避免网络超时后重复创建。

## 跨平台要求

主逻辑为 `scripts/to-wechat.py`，使用 Python 3.8+、`curl` 和 OpenSSH（`ssh`），不依赖 Windows 盘符、Git Bash 专有路径、`cygpath` 或 `taskkill`。含 WebP 正文图时还需 Pillow：

```bash
python -m pip install Pillow
```

直接运行：

```bash
python3 scripts/to-wechat.py <slug>
```

也可用 Bash 启动器：

```bash
bash scripts/to-wechat.sh <slug>
```

在 Windows 上可用 Python Launcher，例如 `py -3 scripts/to-wechat.py <slug>`。脚本所在仓库目录自动决定文章源目录；也可用 `--posts-dir` 指定。

预览而不调用网络/API：

```bash
python3 scripts/to-wechat.py <slug> --dry-run --preview-html /tmp/wechat-preview.html
```

发布前脚本会检查文章 frontmatter 至少包含 `随笔`、`杜撰`、`打油`、`折腾` 中一个标签；缺失时停止，不创建草稿。

## 微信 API 凭据

1. 登录[微信开发者平台](https://developers.weixin.qq.com/platform/)，进入已关联的公众号开发配置；后台入口可能随平台调整。
2. 在公众号开发信息中查看 **AppID（开发者 ID）**；按页面提示生成或重置 **AppSecret（开发者密码）**。若需要接口权限，按平台提示完成开发者授权。
3. 在接口权限页确认账号具备获取 `access_token`、上传图片/素材及新增草稿所需权限。可用权限因公众号类型和账号状态而异。
4. 将实际发起 API 请求的出口公网 IP 加入相应 IP 白名单。本项目默认通过 SSH 隧道从 VPS `119.28.143.201` 出口访问；若改用其他 SSH 目标，白名单也须匹配该目标的实际公网出口。只有本机出口已在白名单时才用 `--direct`。
5. 将凭据保存到本机用户配置目录的 `.env`，不要提交仓库或发送到聊天：

```dotenv
WX_APPID=你的公众号AppID
WX_APPSECRET=你的公众号AppSecret
# 可选：覆盖默认 SSH 连接目标/私钥
WX_SSH_TARGET=ubuntu@119.28.143.201
WX_SSH_KEY=/你的/SSH私钥路径
```

默认凭据文件路径：

- Linux：`${XDG_CONFIG_HOME:-~/.config}/xiyuan/.env`
- macOS：`~/Library/Application Support/xiyuan/.env`
- Windows：`%APPDATA%\xiyuan\.env`

其他路径可用 `--env-file <路径>` 或环境变量 `WX_ENV_FILE` 指定。Linux/macOS 文件权限应限制为当前用户（例如 `chmod 600 <路径>`）。**不要把 AppSecret、access_token 或密钥贴到聊天里。**若 AppSecret 不再可用，在平台重置后更新本地 `.env`。

## 默认流程

1. 从 `src/content/posts/` 按 frontmatter `slug` 或文件名定位文章。
2. 校验标题、作者、摘要和分类标签。
3. 通过 OpenSSH 建立至配置 SSH 目标的本机 SOCKS5 隧道（默认 `ubuntu@119.28.143.201`）；也可设置 `WX_SSH_TARGET`、`WX_SSH_KEY`、`WX_SSH_PORT` 或相应命令行参数。
4. 使用本地 `.env` 获取短期 access token；凭据和 token 不打印、不写入日志或 Git。
5. 上传正文图片；WebP 转 PNG；用博客 OG 图作为公众号永久素材封面。
6. 按 business-navy 主题转换 Markdown，增加博客原文链接并调用新增草稿接口。
7. 报告草稿结果；用户在公众号后台检查草稿后自行发布。

正文图或必需封面上传失败会明确报错并停止创建草稿；封面上传使用永久素材，若之后新增草稿失败，永久素材可能仍已占用额度。不会在失败后静默继续。
