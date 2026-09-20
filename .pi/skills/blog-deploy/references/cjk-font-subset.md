# CJK 字体动态子集化（xiyuan.wiki 实战，2026-07）

## 背景：OG 图变成方框（tofu）的根因

2026-07-08 发布《设定：永生之鹊》后，文章 OG 分享图（/posts/NNN/index.png）所有中文变成 □。
用 vision 拉图确认 001/004 两篇都是方框，证明**不是本次发布引起，是一直存在的 bug**。

**根因（确定）**：`src/pages/posts/[...slug]/index.png.ts` 里 satori 的 `fonts` 数组**只有 Google Sans Code**
（拉丁等宽字体，不含任何 CJK 字形）。satori 与浏览器不同——它**不回退系统字体**，只渲染传进去的
`fonts` 数组里的字形。中文遇到无对应字形 → 全部 tofu（□）。

- 文章页 OG 走 `index.png.ts`（每篇文章生成 /posts/NNN/index.png），用 satori + sharp
- 首页 OG 走 `default-og.jpg`（public/ 下静态图），不涉及此 bug
- `astro.config.ts` 的 `fallbacks: [PingFang SC, Microsoft YaHei, Noto Sans SC, ...]` 只对**浏览器 CSS** 生效，
  satori 不参与浏览器渲染，fallback 链救不了 OG 图

## 修复路线：给 satori 真实 CJK 字体 ttf

satori 只支持 `.ttf` / `.otf`（**不支持 woff2**，会报 `Unsupported OpenType signature wOF2`）。
完整 CJK ttf 15–50MB，直接嵌进每张 OG（embedFont:true）体积爆炸、构建也慢。
正确做法 = **动态子集化**：只保留实际用到的字形，生成 KB 级 ttf。

### 方案 A（OG 图，必需）：纯动态子集
字符集 = 所有文章 frontmatter 的 `title` + `author` + `astro-paper.config.ts` 的 `site.title`。
发布前全已知，零风险。脚本扫 posts → 去重 → fontmin 从基线 ttf 提取子集 → 喂给 satori。

### 方案 B（正文，可选但推荐）：半静态子集 + 常用字兜底
正文是**开放集**（将来新文章、Waline 评论区都可能冒出生僻字），纯动态子集会漏字变方框。
子集字符集 = 所有已发布文章正文去重字 **∪ 3500 常用字表**。
- 3500 字表来源：《现代汉语常用字表》（1988 国家语委+教委，2500 常用+1000 次常用）或
  《通用规范汉字表》一级字表（2013，3500 字）。GitHub 有现成文本：
  `shengdoushi/common-standard-chinese-characters-table` 的 `level-1.txt`（可 curl 直接取）。
- 体积对比（实测量级）：纯动态 ~0.5–1MB；动态+3500 兜底 ~1–1.5MB；直接放 3500 全集 ~1–1.5MB。
  **一旦兜底 3500，动态子集的"更小"优势基本消失**——正文可改用"3500+文章字 半静态子集"，
  不每次发布重跑（除非冒出 3500 外生僻字再重跑）。
- 评论区靠 3500 兜底基本不漏。

### 选用字体：霞鹜文楷（LxgwWenkai）
西园 2026-07 决定全站（正文+Heti+OG）统一换霞鹜文楷，调性比 Noto 更贴"诗未成章夜未央"。
- 基线 ttf（一次性，存 VPS `~/fonts/`，不进 git 不污染仓库）：
  `LXGWWenKai-Regular.ttf` + `LXGWWenKai-Bold.ttf`
  GitHub release：`lxgw/LxgwWenkai`（执行前先查确切 release tag 避免 404）
- OG 需 Regular + Bold 两个都子集（标题用 bold，只子集 Regular 会让粗体中文仍 tofu）
- 正文 Lite 版（LxgwWenKaiLite，~7000 字裁剪）可作整体托管备选，但不如动态子集小

## 实施步骤（待西园批准执行，未实跑）

```bash
# 1. 装子集化工具（VPS blog-astro 项目内）
cd /home/ubuntu/blog-astro && pnpm add -D fontmin

# 2. 拉基线字体（VPS 在 HK 无墙）
mkdir -p ~/fonts
curl -L -o ~/fonts/LXGWWenKai-Regular.ttf "https://github.com/lxgw/LxgwWenkai/releases/download/v1.501/LXGWWenKai-Regular.ttf"
curl -L -o ~/fonts/LXGWWenKai-Bold.ttf    "https://github.com/lxgw/LxgwWenkai/releases/download/v1.501/LXGWWenKai-Bold.ttf"

# 3. 写 scripts/subset-og-font.mjs：扫 posts title/author + site.title → fontmin glyph 子集
#    → 输出 src/assets/fonts/og-subset.ttf (Regular) + og-subset-bold.ttf
# 4. 改 index.png.ts：读 og-subset*.ttf 为 arrayBuffer，satori fonts 加
#    { name: "LxgwWenkai", data, weight: 400/700 }，中文 div fontFamily 设 "LxgwWenkai", "Google Sans Code"
# 5. 正文：@font-face 指 public/fonts/lxgw-subset.woff2（3500+文章字子集），.heti 字体族改霞鹜
# 6. blog-deploy SKILL.md 构建步骤前加：node scripts/subset-og-font.mjs
# 7. 构建 + vision 验证：拉 /posts/NNN/index.png 确认中文正常；查子集 ttf 体积 < 500KB
```

## 决策记录（西园拍板要点）
- 全站换霞鹜文楷（正文 Heti + OG 图）
- OG 用纯动态子集（封闭集，零风险）；正文用 3500+文章字 半静态子集（不每次重跑）
- 字表兜底源用 GitHub `level-1.txt`（3500 字，可 curl，无墙）
- 基线 ttf 存 `~/fonts/`，子集 ttf 进 `src/assets/fonts/`（小，可 git 跟踪）
- 评论区并进 3500 字表兜底
