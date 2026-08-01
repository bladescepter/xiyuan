---
name: blog-deploy
description: 发布博客到 xiyuan.wiki — 从 Obsidian 同步文章，执行 astro build，以及主题定制
---

## 触发词

用户说"发布"时执行部署。

## 博客栈

| 项目 | 详情 |
|------|------|
| 域名 | xiyuan.wiki |
| 框架 | **Astro**（AstroPaper 主题） |
| Web服务器 | Caddy（Docker 独立容器） |
| VPS | VMISS HK，用户 ubuntu |
| SSH | 本机直连 `ssh -i "C:/Users/blade/.ssh/bladescepter.pem" ubuntu@119.28.143.201`（VPS 公网 IP；旧容器内 `172.17.0.1` 写法已废弃） |
| Astro项目路径 | `/home/ubuntu/blog-astro/` |
| 构建输出目录 | `/home/ubuntu/blog-astro/dist/` |
| 本地笔记库（文章源） | `C:\Obsidian\`（2026-08 迁入；文章在 `C:\Obsidian\4_创作\Blog\`，发布脚本**直接读取此目录**） |
| ~~服务器同步副本~~（已废弃） | `/opt/data/obsidian_vault/4_创作/Blog/`（VPS 侧 vault 副本，2026-08 起管线不再读取） |
| 分类体系 | 随笔、杜撰、捣鼓、打油（以 tag 方式） |
| Caddy重启 | `docker restart caddy`（非 compose，是独立容器） |

> 🔑 **SSH key 注意事项**：发布脚本在本机 Git Bash 运行，SSH 一律用 `-i "C:/Users/blade/.ssh/bladescepter.pem" ubuntu@119.28.143.201`（密钥路径必须正斜杠，本机 shell 会吞反斜杠）。旧容器内 `ssh ubuntu@172.17.0.1`、`-i /opt/data/.ssh/id_ed25519` 等写法仅保留给容器内运维场景，已不用于发布流程。

## 发布流程 — 一键脚本（推荐）

用户说"发布"时，**在本机 Git Bash 执行自动化脚本**：

```bash
bash C:/Users/blade/OneDrive/DEV/blog-deploy/scripts/build-and-publish-blog.sh
```

该脚本自动完成：
0. **同步文章** — 直接读取本地笔记库 `C:\Obsidian\4_创作\Blog\`，同步到本仓库 `src/content/posts/`（剥离数字前缀；git 自动记录增删），About 页同步到 `src/content/pages/about.md`
1. **推送 GitHub** — commit + push 到 `bladescepter/xiyuan`（本项目文件夹即该仓库的本地工作副本，博客源码 + 部署工具 + 技能同仓）
2. **服务器拉取** — ssh 服务器 `/home/ubuntu/blog-astro` 执行 `git pull`（同一仓库），即完成文章同步，随后跑子集化（`subset-body.mjs` + `subset-og.mjs`）
3. **构建** — 服务器自动激活 nvm + Node 22 + pnpm build
4. 清除 Cloudflare 字体缓存（API 自动 purge）

**前提条件**（已配置完成）：
- Cloudflare API Token + Zone ID 存在本地 `C:/Users/blade/OneDrive/DEV/setting-env/.env`（仅 Cache Purge 权限）
- 本机 Git Bash 可用（ssh/scp/tar/curl/python）
- SSH 密钥 `C:/Users/blade/.ssh/bladescepter.pem` 可访问 `ubuntu@119.28.143.201`

> ⚠️ **VPS 侧 vault 已废弃**：不再从 `/opt/data/obsidian_vault` 读取/拉取（该副本 2026-08 起弃用）。文章源只有本地 `C:\Obsidian\4_创作\Blog\`。

> **如果脚本执行失败**，再回退到下方手动步骤分步排查。

### 部署后验证

脚本执行后，做两步快速确认：

```bash
# 1. 字体文件是最新的
curl -sI https://xiyuan.wiki/fonts/lxgw-body.woff2 | grep -E 'last-modified|cf-cache-status'
# 期望: last-modified 是刚刚构建的时间, cf-cache-status 为 MISS（首次从源站拉取）

# 2. 确认字体文件在服务器上正确
docker exec caddy sh -c "md5sum /blog/fonts/lxgw-body.woff2 /blog/fonts/LXGWWenKai-Regular.woff2"
# 两个文件 MD5 应一致（都是新版正确子集）
# 如果 MD5 不同说明有旧文件残留，需要重新清理 + 构建
```

## 手动发布流程（脚本失败时的备用方案）

### 0. frontmatter 预处理

在同步前，检查 Blog 目录下每篇新文章是否缺少以下字段，缺少则自动填充：

| 字段 | 自动填充规则 |
|------|-------------|
| `pubDatetime` | 当前时间 `YYYY-MM-DDTHH:mm:ss+08:00` |
| `description` | 正文第一段（截断到第一个句号，最长 150 字） |
| `tags` | 如果整个 tags 为空 → 默认 `["随笔"]` |
| `slug` | 从 VPS 读取 `.slug-counter`，取当前值补零三位（如 `"003"`），写入 frontmatter，计数器 +1 |
| `author` | 如果缺失 → `陆西园` |

> ⚠️ **slug 编号语义（防 off-by-one）**：`.slug-counter` 存的是「下一个可用编号」本身，不是「已用数量」。例如 counter=`4` 时，本篇 slug 就是 `"004"`（直接取当前值，**不要先 +1**），写完后 counter 才改成 `5`。2026-07 实测曾误把 counter=4 算成 005，导致编号错位。已有 slug 字段的文章（用户已指定）绝不覆盖。

已有值的字段不动。

## OG 图路由 & 部署生效机制（关键事实）

- **动态 OG 图真实访问路径**：AstroPaper 的 `src/pages/posts/[...slug]/index.png.ts` 经 Satori 生成的路由是 **`/posts/<slug>/index.png`**（不是 `/posts/<slug>.png`，也不是 `/posts/<slug>/og.png`）。验证线上 OG 图务必用真实路径，否则拿到 404 会误判「没部署」。默认站 OG 是 `/og.png`。
- **Caddy 只读 bind mount，`pnpm build` 即上线**：Caddy 容器把宿主 `/home/ubuntu/blog-astro/dist` 以 `ro` 挂载为容器内 `/blog`（`docker inspect caddy` 的 Mounts 可见），Caddyfile 写 `root * /blog`。因此**构建产物写进 dist 立刻对线上生效，无需重启 Caddy、无需手动拷贝**。若发现线上「没更新」，先核对：① 是否跑了 `pnpm build`；② curl 的 URL 路径对不对；③ 是否发了图片链接而非文章页链接（见下）。

## OG 图 vs Telegram 预览（别混淆两件事）

- **OG 图里画了什么字**（如文章 title + description）是 Satori 模板渲染的**图片内容**，只影响分享卡片缩略图长什么样。
- **Telegram 链接预览里那行灰字 description** 来自文章页 HTML 的 `<meta property="og:description">`，**不是从 OG 图读的**。Telegram 把纯图片链接（`.../index.png`）当图片处理，只显示图、不显示文字描述；发**文章页 URL**（`/posts/<slug>/`）才会抓 og:description 显示文字。
- 诊断「Telegram 里没有 description」时：**先 curl 文章页确认 `og:description` meta 是否非空**，再决定是 meta 问题还是发错链接。本次曾误判「004 的 og:description 是空的」但 curl 证明是满的——根因是发了图片链接而非文章页链接。
- 给 OG 图加 description（图内文字）的做法：`src/pages/posts/[...slug]/index.png.ts` 的 title `<p>` 下插入 description `<p>`（灰字 + 截断）；并同步把文章 frontmatter 的 `description` 纳入 `scripts/subset-og.mjs` 的收集循环（否则生僻字 tofu）。这两处改动都需先汇报再执行。

## OG 图片 & Telegram 预览

### 状态总览

| 页面 | OG 图源 | 问题 |
|------|---------|------|
| 文章页（/posts/001/） | 动态生成（Satori + Sharp），带文章标题 + 右下角站点名（作者行 `by 陆西园` 已删） | ✅ 中文正常（已换 LxgwWenkai 子集，见 references/font-subset-lxgw.md） |
| 首页（/） | `public/default-og.jpg`（AstroPaper 自带的通用图） | ❌ 默认图不好看 |
| About/归档/标签页 | 同首页，回退到 `default-og.jpg` | ❌ 同上 |

**原因**：`resolveDefaultOgImagePath()` 的逻辑——若 `public/default-og.jpg` 存在，优先用它；不存在才回退到动态 `/og.png`。

### Telegram 预览行为巨坑

Telegram 链接预览的显示行来自不同 meta 标签，且各终端行为略有不同。已踩过的坑：

| Telegram 显示行 | 来源 | 说明 |
|----------------|------|------|
| 第 1 行（粗体） | `<meta property="og:title">` 或 `<title>` | 正常 |
| 第 2 行（灰小字） | `<meta name="author">` **或** `og:site_name` | ⚠️ Telegram 会读取 author meta 作为第二行显示 |
| 第 3 行（灰小字） | `<meta property="og:description">` | 正常 |

**已采取的修复**：
1. 从 `src/layouts/Layout.astro` 中**删除了 `<meta name="author">`**——文章页的 author 信息仍在 JSON-LD 和 frontmatter 中，不影响 SEO
2. 首页（`index.astro`）给 `<Layout>` 传 `description="诗未成章夜未央"`，覆盖默认描述

### Telegram 刷新缓存方法

Telegram 对链接预览缓存极久（可能数天到数周）。每次修改 OG 信息后需要手动刷新：

1. 把链接发给 Telegram 的 **[@WebpageBot](https://t.me/WebpageBot)**，它会重新抓取
2. 或在分享时加不同 query 参数（如 `?v=1`）触发新缓存

### OG 图方案

- 删除 `public/default-og.jpg` → 所有页面统一使用动态 `/og.png`
- 或自定义 `/og.png.ts`（Satori 模板），改成匹配博客配色（Kha-Yan 暖米色背景 + Noto Serif SC 字体）
- 或直接用**用户提供的鸟图**制作自定义 OG 图（1200×630 JPEG）

动态 `/og.png` 目前只显示站点标题+描述，配色是白底，跟博客整体风格不一致。

## 字体配置

参见 `references/heti-integration.md`，核心要点：

- **CJK 字体（思源宋体等）单个 ttf 约 15MB**，是拉丁字体的 50–100 倍。AstroPaper 默认的 Google Sans Code（拉丁等宽）只有 ~500KB–1MB。
- **CJK 全覆盖空白**：Google Sans Code 不含 CJK 字形，中文完全靠系统回退，无排版控制。详见 `references/heti-integration.md`。
- satori（OG 图生成）**只支持 ttf/otf，不支持 woff2**，formats 中必须有 `"ttf"`。
- 中文无斜体，`styles: ["normal"]` 即可；只需 Regular + Bold 两个字重。
- 切换字体时**不要改 `cssVariable`**，保持 `--font-google-sans-code`，只改 `name` 和 `fallbacks`。
- 西园说"原始字体"时，要确认是**原始的思源宋体配置**（~34MB）还是**AstroPaper 默认的 Google Sans Code**（~500KB）——两者体积差两个数量级。

## 手动发布流程（脚本失败时的备用方案）

### 0. frontmatter 预处理

> **字体策略（2026-07 生效）**：霞鹜文楷（LxgwWenkai）动态子集，**仅作用于 `.heti` 容器**（文章正文 / about 页 / 首页 hero 诗句）；**导航/按钮/页脚等 UI 文字保持系统字体**（用户 2026-07 明确决定「只有正文用」，符合通用双字体系统：内容用性格字体、UI 用中性无衬线）。
> - OG 图（`index.png.ts` 走 satori）用 `og-subset.ttf`；正文 `.heti` 容器用 `lxgw-body.woff2`。
> - 基线字体存 VPS `~/fonts/LXGWWenKai-Regular.ttf`（项目外，不进 git）；子集结果进 git：`src/assets/fonts/og-subset.ttf`（OG 用）、`public/fonts/lxgw-body.woff2`（正文用）。
> - **每次发布前必须先跑两个子集脚本**，否则新文章出现的新字不在子集里（正文会 fallback 系统字体、OG 会 tofu）。
> - Waline 评论区不套霞鹜（保持默认字体），不进字符集。
- **不要在 blog-astro 装无关 npm 包调试**：曾误装 Node 版 `fonttools`（要的是 Python fonttools），pnpm supply-chain 策略拦截其 build script → 之后每次 `pnpm build` 都 `ERR_PNPM_IGNORED_BUILDS` 失败。调试用 VPS 本机 `python3` 或本地环境，别往项目里加包。`pnpm remove <pkg>` 解除。

> ⚠️ **旧字体文件干扰陷阱（2026-07 实测）**：`public/fonts/` 可能残留上一次构建的 `LXGWWenKai-Regular.woff2` 等旧文件。Astro 构建时 `Copying fonts` 会把这些旧文件一并复制到 `dist/fonts/`，虽然 CSS 正确引用 `lxgw-body.woff2`，但旧文件的存在可能导致 Cloudflare 缓存了旧版本的子集，或浏览器加载了错误的字体。**子集化前必须清理 `public/fonts/` 下除了 `lxgw-body.woff2` 以外的旧字体文件**（`.ttf` 和 `.woff2`），用以下命令：
> ```bash
> rm -f /home/ubuntu/blog-astro/public/fonts/LXGWWenKai-Regular.*
> ```
> 此清理已在 2026-07-17 的发布中实战验证——清理 + 重建后用户确认字体正确。若用户报告「部分字是霞鹜、部分字是系统字体」，且子集脚本日志显示字符集正常（如 1120 字），应先清理旧文件 + 重建，而非立即怀疑子集脚本漏字。\n> \n> ⚠️ **Cloudflare 缓存陷阱**：`public/fonts/lxgw-body.woff2` 的 `cache-control: max-age=14400`（4 小时）。重建后 Cloudflare 可能仍服务旧文件。
>
> **CDN 缓存 vs 浏览器缓存 — 关键诊断信号（2026-07-17 实战）：**
> - 用户说「**正常窗口正确，无痕/隐私窗口不正常**」→ 根因是 **Cloudflare CDN 缓存**，非浏览器缓存。正常窗口有浏览器本地缓存，无痕窗口纯新请求全走 CDN 边缘取到旧版本。两边都不正常才查部署或子集。
> - 用户说「**两个窗口都不正常**」→ 查部署是否成功或子集是否漏字。
>
确认 CDN 缓存后再按序验证（2026-07 实战诊断流程）：
  0a. **问用户窗口行为**：正常 vs 无痕窗口表现不同 → CDN 缓存；一样 → 部署/子集问题。
  0b. **再查 CDN 缓存**：`curl -sI https://xiyuan.wiki/fonts/lxgw-body.woff2 | grep -i 'cf-cache-status'`
> 返回 `HIT` 说明缓存未更新。用 `?v=N` 破缓存验证实际文件。
>
> **手动清除 Cloudflare 缓存（备份命令，当脚本的自动 purge 失败时使用）：**
> ```bash
> source /opt/data/.env
> curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache" \
>   -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
>   -H "Content-Type: application/json" \
>   -d '{"files":["https://xiyuan.wiki/fonts/lxgw-body.woff2"]}'
> ```
>
> **CI=true 不再需要（pnpm 11+）**：2026-07 升级到 Node 22 + pnpm 11.9 后，非 TTY 下 `pnpm build` 已不再弹出 `confirmModulesPurge` 确认。`CI=true` 前缀可以省略。如果未来 pnpm 版本变动导致构建挂起等待输入，再加回 `CI=true`。
>
> **2a. 跑子集脚本（每次发布必跑，必须先清理旧字体文件）：**

```bash
ssh -i "C:/Users/blade/.ssh/bladescepter.pem" ubuntu@119.28.143.201 \
  "export NVM_DIR=\"\$HOME/.nvm\" && \
   [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\" && \
   nvm use 22 --silent && \
   cd /home/ubuntu/blog-astro && \
   # 清理旧字体文件，防止干扰子集（2026-07-17 实战发现：残留的 LXGWWenKai-Regular.woff2 会导致部分字 fallback 系统字体）
   rm -f public/fonts/LXGWWenKai-Regular.* && \
   node scripts/subset-og.mjs && \
   node scripts/subset-body.mjs"
```

**2b. 构建：**

SSH 到服务器执行 pnpm build（先激活 nvm 切换到 Node 22）：

```bash
ssh -i "C:/Users/blade/.ssh/bladescepter.pem" ubuntu@119.28.143.201 \
  "export NVM_DIR=\"\$HOME/.nvm\" && \
   [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\" && \
   nvm use 22 --silent && \
   cd /home/ubuntu/blog-astro && CI=true pnpm build"
```

> 构建完成后 Caddy 自动服务新的 `dist/` 目录，通常**不需要重启 Caddy**（bind mount 实时同步文件系统变化）。
>
> ⚠️ 陷阱一：**非 TTY 下 pnpm build 需要 `CI=true`**。从容器 SSH 执行构建时无 TTY，pnpm 会因 `confirmModulesPurge` 提示而中断。设置 `CI=true` 可跳过此确认。
>
> ⚠️ 陷阱二：**绝对不要 `rm -rf dist/` 再重建**。Docker bind mount 在宿主机目录被删除后不会自动恢复——容器里的 `/blog` 会变成空目录，Caddy 返回 404。如果确实需要清空构建缓存，用 `rm -rf dist/*` 保留目录本身，或者重建后必须 `docker restart caddy` 恢复挂载。
>
> ⚠️ 注意：Caddy 是**独立容器**（`caddy:latest`，非 blog-astro compose.yaml 的一部分），重启命令是 `docker restart caddy`，不是 `docker compose restart caddy`。

### 3. 报告

告知用户发布完成，列出本次同步的文件变化（如有）。

## Callouts（在文章中使用）

AstroPaper（`rehype-callouts`）+ Obsidian **双端兼容**。在 Obsidian 写，发布到博客上自动渲染，无需额外处理。

### 基础语法

```markdown
> [!NOTE] 标题（可省略）
> 正文内容
```

类型不区分大小写。不支持的类型退化为 `note`。

### 可折叠

```
> [!TIP]- 默认折叠
> 展开才看到

> [!WARNING]+ 默认展开
> 但可以折叠
```

### 支持的全部类型

| 类型 | 别名 | 颜色 | 用途 |
|------|------|------|------|
| `NOTE` | — | 蓝 | 普通说明 |
| `ABSTRACT` | `SUMMARY`, `TLDR` | 青 | 摘要 |
| `INFO` | `TODO` | 青 | 补充信息 |
| `TIP` | `HINT`, `IMPORTANT` | 绿 | 提示 |
| `SUCCESS` | `CHECK`, `DONE` | 亮绿 | 确认 |
| `QUESTION` | `HELP`, `FAQ` | 亮绿 | 疑问 |
| `WARNING` | `CAUTION`, `ATTENTION` | 橙 | 警告 |
| `FAILURE` | `FAIL`, `MISSING` | 红 | 失败 |
| `DANGER` | `ERROR` | 粉红 | 危险 |
| `BUG` | — | 品红 | Bug 标记 |
| `EXAMPLE` | — | 紫 | 示例 |
| `QUOTE` | `CITE` | 灰 | 引用 |

### Windows 插入技巧

`Ctrl+P` 搜 "Insert callout"，但**必须在编辑模式/Live Preview 下**才行（阅读模式下此命令不出现）。

> 中文版 Obsidian 的命令名是 **"插入标注"**（搜 `cal` 或 `标注` 都能找到）。

### 设置快捷键（可选）

设置 → 快捷键 → 搜索 "insert callout" → 绑定 `Ctrl+Shift+C` 等一键插入。

## 工作原则

1. **动手改之前，先读文档** — AstroPaper 的模板/配置/组件都有既定设计，改之前先查官方文档或本技能的参考文件。贸然改容易踩坑。
2. **部署第三方服务，先查官方文档** — 涉及部署评论系统、数据库、CDN 等第三方服务时，必须先到该服务的**官方文档**查最新的推荐方案，不凭印象或二手信息给方案。这次 Waline 集成就走过弯路：凭印象用了 LeanCloud，实际上官方早已推荐 Vercel Storage + Neon。
3. **如无必要勿增实体** — 不推荐额外装插件/工具来解决本可通过 Agent 自动处理的问题（例如：不用 Templater 插件，发布时自动填充 frontmatter）。
4. **Astro View Transitions + 第三方 JS 组件**：Astro 的 View Transitions 会在页面切换时替换 DOM 但保留脚本上下文。嵌入第三方 JS 组件（如 Waline）时，`<script>` 中的初始化代码只在首次加载执行一次，切换页面后新 DOM 上没有组件实例。\n   - ❌ **`data-astro-rerun`**：会导致 Waline 在刷新页面时也无法渲染，完全不可用。\n   - ❌ **事件委托**（`document.addEventListener("click", handler)` 匹配 `[data-comment-toggle]`）：同样破坏 Waline 渲染，所有点击均无响应。\n   - ✅ **唯一可靠的方式**：**全局函数** + **`onclick` 属性** + **`astro:after-swap` 重置状态**。按钮需同时有 `data-comment-toggle`（用于 JS 查找）和 `onclick="window.__walineToggle()"`（用于触发）。`astro:after-swap` 仅重置 `__walineLoaded` 标志和清空容器，不做初始化。下次点击走首次加载分支重新 import + init。\n   - ✅ **点击加载模式**：让用户主动点击触发初始化，比自动加载更可靠（DOM 已稳定、脚本上下文已就绪）。
7. **编辑远程 .astro 文件用 SSH sed，不拷贝本地文件覆盖** — /opt/data/ 下的 .astro 文件可能是旧版本或残影，与博客服务器上的实际文件不同。需要单行修改（如颜色）时，直接在 SSH 命令中用 sed -i 改目标文件。整体文件修改先 scp 从远程拉下来再改再传回去，确保以远程版本为准。恢复文件用 git checkout 或 git checkout -- <file>。**不要从本地 /opt/data/ 拷贝 .astro 文件覆盖远程**——本地文件可能是残影，会覆盖线上有完整功能的版本。
   - **sed 行号追加陷阱**：`sed 'Na\...'` 在第 N 行之后插入。如果目标行是多行标签的中间属性行，插入会出现在属性和 `/>` 之间。优先用模式匹配而非行号。
   - **sed `\n` 是字面字符**：在 sed 的 `a`（append）命令中，`\n` 输出字面 `\n` 而非换行。多行插入用 `c`（change）或 Python 脚本。
   - **模式粘性匹配**：`^    \\/>$` 可能匹配多个自闭合标签。用更具体的上下文确认唯一性。
   - **模式删除只删含关键词的行**：`sed -i '/no-heti-link/d'` 只删除含 `no-heti-link` 的行，同属一个 CSS block 的 `{`、`border-bottom`、`}` 等无关键词行会残留成为碎片，造成 `Missing opening {` 构建报错。删除多行 block 用行号范围 `sed -i '42,46d'` 或匹配注释头 `sed -i '/注释/,/^}/d'`。
   - 复杂修改参见 `references/shell-escape-bypass.md`。
8. **Waline 暗色模式配色统一** — 站点暗色主题 accent（--accent: #ff6b01）与 Waline 默认暗色主题色（#f59e0b 暖黄）不一致，需覆盖 --waline-theme-color 和 --waline-active-color。在 Comments.astro 的 .dark .waline-container 中用 sed -i 改。亮色模式保留原配色。
9. **评论折叠时的空白区处理** — Comments.astro 的 `<section id="comments-section" class="mt-16">` 在评论折叠（`#waline` 有 `hidden` 类）时，`mt-16` 仍然占据 4rem 空白，导致文章底部与"上一篇/下一篇"之间形成 6rem+ 间距。解决：去掉 `<section>` 的 `mt-16`，改为给 `#waline` 加上 `margin-top: 1.5rem`（折叠时 `.hidden` 的 `margin: 0` 覆盖它）。
10. **评论区和下篇导航间加分割线** — 在 Comments.astro 的 `</section>` 之后加 `<hr id="comments-hr" class="my-8 border-dashed hidden" />`（不是 BackToTopButton 后面——BackToTopButton 在 index.astro 中，而 toggle JS 在 Comments.astro 内，跨文件会失效）。JS 同步 toggle `hidden` 类，`astro:after-swap` 重置时也加回。修改用 SSH sed -i 直接在服务器上改 Comments.astro，不要拷贝本地文件覆盖。
11. **Astro 中加载外部 CDN JS 必须加 `is:inline`** — 在 `.astro` 模板中写 `<script src="...cdn...">` 时，Astro 默认将其视作 ES Module 处理（bundled + hashed），外部 URL 会被丢弃，标签在构建产物中完全消失。必须显式添加 `is:inline` 属性：`<script is:inline src="...">`。这对所有第三方 CDN 脚本（统计、评论增强、排版等）都适用。详见 `references/heti-integration.md`。
12. **修改方案必须先汇报再执行** — 涉及文件修改、新建组件、主题定制等操作，必须先分析原因、给出方案（含替代方案），等用户确认后再动手。不允许直接执行。用户明确说过此要求，适用于本技能涉及的所有模板/配置/样式修改。
    - 错误示例：用户说「链接样式有点奇怪」→ 我直接改代码
    - 正确流程：用户说「链接样式有点奇怪」→ 我分析原因 → 给出 2-3 个方案 → 等用户选 → 执行

### ⚠️ 发布前文件确认（2026-08 流程变更）

发布脚本**直接读取本地 `C:\Obsidian\4_创作\Blog\` 的当前磁盘文件**，不再经过 git 拉取——本地保存即发布内容（无需 push 到 GitHub，未提交的文件也会被发布）。

- 用户说「我改好了，发布」时，**先确认本地文件确实包含改动**（读 frontmatter / 关键段落），再执行发布。
- 若本地文件仍是旧版，直接告诉用户「本地 `C:\Obsidian\4_创作\Blog\` 没看到你的修改，请确认已保存」，停下等确认。**绝不替用户重写文件、绝不凭印象假设内容、绝不自己改 slug/正文去「补全」。**
- 历史坑（2026-07）：旧流程经服务器 pull-only 拉取 GitHub，曾两度因用户未 push 而发布旧版。改读本地后此问题消失，但需注意**编辑器未保存的缓冲不生效**。

## GitHub 备份

| 项目 | 详情 |
|------|------|
| 远程仓库 | `git@github.com:bladescepter/xiyuan.git` |
| 本地路径 | `/home/ubuntu/blog-astro/`（VPS 上） |
| 自动备份 | 每天 02:00 BJT（cron job） — 在 blog-astro/ 目录执行 `git add -A && git commit && git push origin main` |
| 初次迁移 | 从 Hexo 迁移时用了 `git push -f` 覆盖旧仓库内容 |

> ⚠️ **备份脚本缺少 push 的坑（2026-07 已修复）**：`/opt/data/scripts/backup-blog-astro.sh` 最初只做 `git commit` 没有 `git push`，导致本地每日备份正常（commit 存在）但 GitHub 仓库数周不更新。根因：脚本 EOF 块写 `git commit -m "每日自动备份 $TODAY" >/dev/null` 后直接 `echo "博客源码已备份"` 结束，从未推送。修复：在 commit 行后加 `git push origin main >/dev/null 2>&1 || echo "push 失败"`。任何备份类脚本写了 commit 必须跟 push，否则本地积压的提交在 GitHub 上看不到。

## 日常维护

### Docker 容器更新

检查新镜像 → 重建容器（`docker restart` 无效）：

```bash
ssh ubuntu@172.17.0.1

# 1. 检查是否有更新可拉取
docker images | grep -E '(caddy|waline|hermes)'

# 2. 拉取最新镜像
docker pull caddy:latest
docker pull lizheming/waline:latest

# 3. 拉取后检查镜像 ID 是否变了
docker images | grep -E '(caddy|waline)'
```

⚠️ **关键陷阱：`docker restart` 不会使用新镜像**。`docker restart` 只是重启同一个容器（同一个 image layer），新拉取的镜像不会被使用。必须 `docker rm` + `docker run` 重建容器。

### Docker 29.x 敏感环境变量脱敏

**症状**：重建 waline 容器时，`JWT_TOKEN` 和 `AUTHOR_EMAIL` 的实际值在所有层面被 Docker 替换为 `***`，无法读出：

| 读取方式 | 结果 |
|---------|:----:|
| `docker inspect` | `***` |
| `docker exec env` | `***` |
| `/proc/<pid>/environ` | `***` |
| `config.v2.json`（磁盘） | `***` |

**根本原因**：Docker Engine ≥29.x 将名称匹配 `KEY/SECRET/TOKEN/PASSWORD` 模式的环境变量视为 secrets，在 daemon 层面截断并另存——任何 API 或文件读取均返回 `***`。

**影响**：无法通过已有容器反向推导这些值；重建 waline 容器时必须：
- 用户提供原始值，或
- 生成新的 JWT_TOKEN（注意这会失效所有现有评论管理会话），或
- 保持当前容器运行不动

**Waline 完整环境变量列表**（JWT_TOKEN 和 AUTHOR_EMAIL 需要用户提供）：

| 变量 | 值 |
|------|-----|
| `TZ` | `Asia/Shanghai` |
| `SQLITE_PATH` | `/app/data` |
| `JWT_TOKEN` | **用户提供** |
| `SITE_NAME` | `西园` |
| `SITE_URL` | `https://xiyuan.wiki` |
| `SECURE_DOMAINS` | `xiyuan.wiki,waline.xiyuan.wiki` |
| `AUTHOR_EMAIL` | **用户提供** |
| `NODE_ENV` | `production` |

### 博客依赖更新

检查和更新 Astro 项目依赖：

```bash
ssh ubuntu@172.17.0.1 \
  "export NVM_DIR=\"\$HOME/.nvm\" && \
   [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\" && \
   nvm use 22 --silent && \
   cd /home/ubuntu/blog-astro && \
   echo '=== 可更新包 ===' && \
   npm outdated 2>&1 | head -40"
```

更新全部可更新的包：

```bash
ssh ubuntu@172.17.0.1 \
  "export NVM_DIR=\"\$HOME/.nvm\" && \
   [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\" && \
   nvm use 22 --silent && \
   cd /home/ubuntu/blog-astro && \
   pnpm update && \
   echo '更新完成，开始构建...' && \
   CI=true pnpm build"
```

> ⚠️ 注意：`npm outdated` 中 `Latest` 列的值可能低于 `Current`（如 astro 6.4.2 → Latest 6.0.5），这是 npm registry 的版本标签问题。**以 `Wanted` 列为准**，那是符合 semver 范围的最新版本。`pnpm update` 也会按 `Wanted` 更新。

### 维护检查清单

| 事项 | 命令/方式 |
|------|----------|
| Docker 镜像更新 | `docker pull caddy:latest && docker pull lizheming/waline:latest` |
| 博客依赖更新 | `pnpm update && CI=true pnpm build` |
| Node 版本确认 | 默认 v20，构建前 `nvm use 22` |
| pnpm 版本 | `pnpm --version`（当前 11.9.0） |
| 容器重建 | `docker restart` 不换镜像，需 `docker rm + docker run` |
| 磁盘余量 | `df -h /`（已有 cron 每日 12:00 检查，低于 5G 告警） |

## 社媒链接配置

在 `astro-paper.config.ts` 的 `socials` 数组中添加：

```ts
socials: [
  { name: "x",        url: "https://x.com/bladescepter" },
  { name: "telegram", url: "https://t.me/bladescepter" },
  { name: "mail",     url: "mailto:bladescepter@gmail.com" },
],
```

`name` 必须匹配 `src/assets/icons/socials/` 下某个 SVG 文件名（不含 `.svg`）。

当前已配置：𝕏、Telegram、Gmail。

## 工作流补记

- Blog 目录在容器内，Astro 在宿主机，同步仍走 SSH 管道
- VPS 上 Node.js 通过 nvm 管理，默认 v20，构建前要用 `nvm use 22`
- pnpm 安装在 `~/.npm-global/bin/`
- **编辑远程文件用 Python+tempfile+SCP**，绝对不要用 SSH heredoc 写含 `${}` 或模板语法的 Astro 文件（会被 bash 展开破坏）。优先使用 `shell-escape-bypass.md` 中的方案 A。
- **复杂远程文件的新方案**：本地 `write_file` → `scp` 到 VPS。当文件内容复杂（含 Tailwind class list、模板插值、中文字符）时，SSH heredoc 和 `-c` 都会因多层嵌套引号而失败。改为本地写临时文件后 scp 过去：本地 `write_file` → `scp <local> ubuntu@172.17.0.1:<remote>`。
- **坑后恢复**：`git checkout -- <file>` 只恢复单个文件，不影响同项目的其他修改。但如果文件是新增的（未被 git 跟踪），需要用 SCP 重新上传旧版本。
- **组件移动**：`BackToTopButton.astro` 从 `src/pages/posts/[...slug]/_components/` 移到了 `src/components/`，因为 about 页等其他页面也需要使用。导入路径从相对路径改为 `@/components/BackToTopButton.astro`。
- **Footer 结构调整**：已移除 Socials 组件引用，footer 仅保留版权信息。社交链接仅在首页（`index.astro`）中保留。

## 赫蹏（Heti）中文排版增强

已集成到全站。详见 `references/heti-integration.md`。

### 改动文件

| 文件 | 改动 |
|------|------|
| `src/layouts/Layout.astro` | `<head>` 添加 Heti CSS + JS CDN 引用；`</body>` 前加 `data-astro-rerun` 初始化 |
| `src/pages/posts/[...slug]/index.astro` | `<article>` class 添加 `"heti"` |
| `src/pages/about.astro` | `<Content />` 外层加 `<div class="heti">` |
| `src/pages/index.astro` | `<section id="hero">` class 添加 `"heti"` |

> ⚠️ 字体变体偏好：用户尝试 `heti--song`（宋体正文）后觉得难读，改回默认 `heti`（正文无衬线黑体）。不要默认用 `heti--song`。

### 当前配置

- 字体变体：`heti`（默认模式：黑体正文 + 黑体标题 + 楷体引用）
- CSS 仅影响带 `heti` class 的容器，不干扰导航/侧栏/页脚
- JS 启用在所有带内容的容器（中西文自动间距 + 标点挤压）
- View Transitions 兼容：`data-astro-rerun` 在 Layout.astro 中全局初始化

### JS autoSpacing 覆盖策略

Layout.astro 底部的初始化脚本用 `new Heti('.heti')` 覆盖所有带 `.heti` class 的容器。`autoSpacing()` 只在 `.heti` 容器内生效，不依赖容器 class 的选择器无法工作。

```js\ntry { new Heti('.heti').autoSpacing(); } catch(e) {}\n```\n\n### 已知坑 & 解决方案

详见 `references/heti-integration.md` 的「坑 & 注意事项」章节，核心问题：

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `new Heti()` 传 DOM 元素全站失效 | 构造器只接受 CSS 选择器字符串 | 分别传字符串：`new Heti('.heti')` |
| 卡片链接下划线偏移异常远 | Heti 用 `border-bottom` 做下划线，Card 用 `text-decoration` | `post-card-link` class + CSS override（见下文） |
| CDN 脚本构建后消失 | Astro 视 `<script>` 为 ES Module | 加 `is:inline` 属性 |
| View Transitions 后 JS 不生效 | 内联脚本只在首次加载执行 | 加 `data-astro-rerun` 属性 |

### 卡片链接排除方案（post-card-link）

如果未来需要全站 `.heti` 覆盖，需配合 Card 链接排除：

**Card.astro**：链接 class 加 `post-card-link`
**global.css**：加覆盖块
```css
.heti .post-card-link {
  border-bottom: none !important;
}
.heti .post-card-link:hover {
  border-bottom: none !important;
  text-decoration: underline !important;
  text-decoration-style: dashed !important;
  text-underline-offset: 4px !important;
}
```

### 当前覆盖页面

| 页面 | CSS 排版 | JS 间距 |
|------|---------|---------|
| 文章页 `/posts/*` | ✅ `<article class="heti">` | ✅ |
| 关于页 `/about/` | ✅ `<div class="heti">` | ✅ |
| 首页 Hero `/#hero` | ✅ `<section class="... heti">` | ✅ |
| 首页卡片列表 | ❌ | ❌ |
| 标签页卡片列表 | ❌ | ❌ |

> 卡片和标签页列表不加 `.heti`，避免链接样式冲突。如需覆盖需配合 `post-card-link` 排除方案。

### 变更记录

| 日期 | 变更 |
|------|------|
| 2026-07 | 初始集成（CSS + JS + Layout.astro 全局加载） |
| 2026-07 | 收到反馈后从 `heti--song` 改回默认 `heti`（宋体难读） |
| 2026-07 | 从 `[...slug].astro` 局部加载改为 `Layout.astro` 全局加载 |
| 2026-07 | 发现 `new Heti()` 只接受字符串选择器，修复全站 JS 失效 |
| 2026-07 | 记录 `post-card-link` 排除方案，为全站覆盖预备案 |

- [x] 中文 i18n（UI 已中文化）
- [x] 配色方案（昼 Kha-Yan / 夜 Paper Dark II）
- [x] 首页 Hero 区块自定义
- [x] 社媒链接（𝕏、Telegram、Gmail）
- [x] 文章 URL 编号 slug（/posts/001/）\n- [x] 标签页按文章数量排序 + 显示计数\n- [x] Waline 评论系统集成（VPS Docker + SQLite 自部署，waline.xiyuan.wiki）
  - 点击加载 + Toggle 展开/收起\n  - View Transitions 兼容（astro:after-swap 重置状态 + onclick 全局函数，不能用 data-astro-rerun）\n  - 评论区位于 AdjacentPostNav（前后篇文章导航）之上
  - 自定义主题配色（Kha-Yan / Paper Dark II）
  - Twemoji 表情
- [x] 回到顶部按钮改造（plumz.me 风格：纯色小圆点，无进度环）
- [x] Footer 重构（移除社媒链接，仅保留版权信息）
- [x] 标题锚点 `#` 手机端隐藏
- [x] Heti（赫蹏）中文排版增强集成（全局 Layout + 默认 Hei 模式）
- [ ] 青碧色 #5a9e8f 改色
- [ ] 桌面/手机分类标签分流显示

## 参考文件

- `references/astropaper-customization.md` — Hero 区块 / 配色 / 日期格式 / 中文 i18n 改法
- `references/astropaper-frontmatter.md` — 文章 frontmatter 字段定义和自动填充规则
- `references/numeric-slug-system.md` — 文章编号 URL 系统（slug 代码改动全记录）
- `references/shell-escape-bypass.md` — 远程文件修改的 shell 转义避险方案（通用）
- `references/astropaper-fonts-pitfalls.md` — 自托管字体 / astro fonts 配置 / OG 图片 / satori 不兼容 woff2 等陷阱
- `references/cjk-font-subset.md` — OG 图中文变方框（tofu）根因分析
- `references/font-subset-lxgw.md` — **已执行的全站换霞鹜文楷方案**：子集脚本源码 + 构建期踩坑（Astro import.meta.url 路径、ttf2woff2 转换、stray 文件清理）
- `references/favicon.md` — 黑鸟黄喙圆形透明 favicon 设计说明与重建流程
- `references/heti-integration.md` — 赫蹏（Heti）中文排版增强集成：字体评估、集成步骤、冲突分析、坑与注意事项
- `references/waline-integration.md`
