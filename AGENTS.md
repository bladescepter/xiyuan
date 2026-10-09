# blog-deploy — 博客发布管线与运维知识库

管理 xiyuan.wiki（Astro / AstroPaper）博客的发布管线、部署脚本与运维知识。本项目文件夹即 `bladescepter/xiyuan` 仓库的本地工作副本：博客源码、部署工具、技能同仓。

## 发布管线（2026-08 起，git 流程）

```
本地 C:\Obsidian\4_创作\Blog（写作侧，唯一文章源）
  → 同步到本项目 src/content/posts（剥离数字前缀，git 自动记录增删）
    ＋ 0_About页.md → src/content/pages/about.md
  → git push → bladescepter/xiyuan 仓库
  → 服务器 /home/ubuntu/blog-astro git pull（同一仓库，即完成文章同步）
  → subset-body.mjs + subset-og.mjs 子集化
  → pnpm build（Caddy 只读挂载 dist，构建即上线）
  → 通过 Pi 的 cloudflare-api MCP 清理唯一字体 URL 缓存
```

- 一键发布：`bash C:/Users/blade/OneDrive/DEV/blog-deploy/scripts/build-and-publish-blog.sh`（本机 Git Bash；要求 Pi CLI 和 cloudflare-api MCP 已连接）
- 发布前置：服务器工作树必须干净（pull --ff-only）；任一步失败报错退出，不静默
- 文章变更经 git 流转，绕开 Windows→SSH 流式传输（tar/scp 曾挂起）
- VPS 侧 `/opt/data/obsidian_vault` 笔记副本**已废弃**，管线不再读取

## 访问方式

```bash
ssh -i "C:/Users/blade/.ssh/bladescepter.pem" ubuntu@119.28.143.201 "<命令>"
```

- 密钥路径必须正斜杠（本机 shell 会吞反斜杠）
- 旧容器内 `ssh ubuntu@172.17.0.1`、`-i /opt/data/.ssh/id_ed25519` 写法仅保留给容器内运维场景

## 基础设施拓扑

| 层 | 详情 |
|---|---|
| 域名 | xiyuan.wiki（Cloudflare CDN 边缘） |
| 框架 | Astro + AstroPaper（`src/` 源码） |
| Web 服务器 | Caddy 容器（独立容器，非 compose），只读挂载 `/home/ubuntu/blog-astro/dist` 为容器内 `/blog` |
| VPS | VMISS HK，`119.28.143.201`，用户 ubuntu，Node 22（nvm）+ pnpm |
| 仓库 | `bladescepter/xiyuan`（源码 + 工具 + 技能同仓，文章经此流转） |
| 凭据 | 微信公众号 AppID/Secret 在本地 `C:/Users/blade/OneDrive/DEV/setting-env/.env`；Cloudflare 缓存通过 Pi 用户级 `cloudflare-api` MCP OAuth 完成 |

## 目录结构

- `scripts/` — 发布与部署脚本（含 Astro 的 subset 脚本）
- `.pi/skills/` — 技能：`blog-deploy`（发布 + 主题定制）、`to-wechat`（微信公众号草稿）
- `src/` — Astro 博客源码（与服务器 blog-astro 同仓库同分支）

## 技能索引

| 技能 | 用途 |
|---|---|
| `blog-deploy` | 发布到 xiyuan.wiki：Obsidian 同步、子集化、构建、主题定制 |
| `to-wechat` | 博客文章转微信公众号草稿箱 |

## 脚本索引

| 文件 | 说明 |
|---|---|
| `scripts/build-and-publish-blog.sh` | 一键发布（本地 → GitHub → 服务器构建 → Cloudflare MCP 清理指定缓存），本机运行 |
| `scripts/backup-blog-astro.sh` | 服务器侧博客源码每日备份（cron 02:00） |
| `scripts/to-wechat.sh` / `to-wechat.py` | 微信公众号草稿（服务器侧 `/opt/data/scripts/`） |

## 工作约定

- 始终生效的硬规则见下方【硬规则】
- 先验证再行动：发布后 curl 确认线上实际生效，不只信构建日志
- 汇报风格：只答所问、只报新完成操作；数据/名单变更须具体列出


---

## 硬规则（始终生效）

# RULES.md — 始终生效的硬规则

每轮对话重新挂载。违反前先停下来。

- **重操作先确认**：完整发布（推送 GitHub + 服务器重建 + 清缓存）、重建容器、改 Caddy/DNS/密钥前，必须先获得用户明确确认。
- **凭据不泄露**：API token / 密钥不打印、不入日志、不进 git；普通凭据只存本地 `.env`（`C:/Users/blade/OneDrive/DEV/setting-env/.env`）。Cloudflare MCP OAuth 凭据仅由 Pi 保存在用户级 auth store 管理，不读取、复制或写入仓库，不发送到 Telegram/GitHub。
- **失败不静默**：脚本/任务失败必须告警、重试（≤3 次）或报错退出，严禁静默失败。
- **发布前确认本地文件**：用户说「改好了，发布」时，先确认 `C:\Obsidian\4_创作\Blog\` 下文件确实包含改动（读 frontmatter / 关键段落）；没看到就直接告知，停下等确认。**绝不替用户重写文件、绝不凭印象假设内容、绝不自己改 slug/正文去「补全」。**
- **修改方案先汇报再执行**：涉及模板/配置/样式修改（.astro、CSS、主题），先分析原因、给出方案（含替代方案），等用户确认后再动手。
- **编辑远程 .astro 文件用 SSH sed / Python+tempfile+SCP**：不拷贝本地文件覆盖远程（本地 `/opt/data/` 下可能是旧版本残影）。复杂内容本地写临时文件后 scp。
- **发布后验证**：curl 确认线上页面/字体实际生效（HTTP 200、`cf-cache-status`、md5sum），不只信构建日志。
- **文章源唯一**：文章只在本地 `C:\Obsidian\4_创作\Blog\` 写作；不在服务器或仓库直接改文章内容（frontmatter 缺失字段可按预处理规则自动补，如 `author` → 陆西园）。

