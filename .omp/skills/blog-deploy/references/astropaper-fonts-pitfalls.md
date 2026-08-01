# Astro 字体配置陷阱（xiyuan.wiki 实战记录）

## ⚠️ 核心认知：拉丁 vs CJK 字体体积差数十倍

AstroPaper 默认字体 **Google Sans Code** 是拉丁等宽字体，只有几百个字符，5×2=10 个 woff 文件合计仅 **~500KB–1MB**。

切换到 **Noto Serif SC（思源宋体）** 这类 CJK 字体后，每个字重包含数万个汉字字形，单个 ttf 文件 **~15MB**，就算精简到 2 个字重也达 **~30MB**。

| 字体 | 类型 | 字符数 | 硬刷新下载量 |
|------|------|--------|------------|
| Google Sans Code（AstroPaper 默认） | 拉丁等宽 | ~几百 | **~500KB–1MB** |
| Noto Serif SC 精简（2字重 ttf） | CJK 宋体 | ~数万 | **~30MB** |
| Noto Serif SC 原始（5×2×2） | CJK 宋体 | ~数万 | **~34MB** |

**关键教训**：问题的根源不是配置模式（5 字重 × 2 样式 × 2 格式），而是**字体类型本身**。CJK 字体体积是拉丁字体的 50–100 倍。Google Fonts 在线 CDN 轻是因为按需子集化 + woff2 压缩，但自托管或 Astro 构建期下载时劣势明显。

**提问时注意区分**：西园说的"原始字体"可能指向两个不同概念：
- "原始的思源宋体"（后来改的 Noto Serif SC 的原始配置）→ ~34MB
- "AstroPaper 默认字体"（主题自带的 Google Sans Code）→ ~500KB

两者体积差两个数量级，理解他问的是哪一个至关重要。

## 背景

2026-06-28 尝试从 Google Sans Code 切换到自托管霞鹜文楷，踩了一串坑，记录如下。

## Astro 的字体两层系统

1. **`astro.config.ts` 的 `fonts` 数组**——由 `astro:assets` 的 `fontProviders` 管理，构建期处理
2. **`@font-face` / `<Font>` 组件**——运行时加载

两者必须配合。仅加 `@font-face` 不够——OG 图片生成（satori）依赖 `fonts` 配置来获取字体文件路径。

## 坑 1：删除 `fonts` 数组会炸 OG 图片

`src/pages/og.png.ts` 和 `src/pages/posts/[...slug]/index.png.ts` 硬编码了：

```ts
const fonts = fontData["--font-google-sans-code"];
```

如果对应的 CSS 变量不存在，`fontData["--font-xxx"]` 返回 `undefined`，`getFontPathByWeight` 无法迭代。

**修复**：要么沿用 Google Fonts，要么用 `fontProviders.local()` 配置自托管字体，且 CSS 变量名要保持一致。

### 关键教训：切换 Google 字体只需改 1 处

**不要改变 `cssVariable`**。只改 `astro.config.ts` 的 `name` 和 `fallbacks`：

```ts
// 原来
name: "Google Sans Code",
cssVariable: "--font-google-sans-code",  // ← 不动
fallbacks: ["monospace"],

// 改成
name: "Noto Serif SC",                   // ← 只改这里
cssVariable: "--font-google-sans-code",  // ← 不动
fallbacks: ["serif"],                    // ← 改 fallback
```

因为 `theme.css` 的 `--font-app: var(--font-google-sans-code)`、`Layout.astro` 的 `<Font cssVariable="--font-google-sans-code">`、以及 OG 图片文件中的 `fontData["--font-google-sans-code"]` 都引用的是 **CSS 变量名**，不是字体名。变量名不变，其他文件都不用动。

## 坑 2：satori 不支持 woff2

satori（OG 图片渲染引擎）底层用 `@shuding/opentype.js`，只支持 `.ttf` / `.otf` 格式。提供 `.woff2` 会报：
```
Error: Unsupported OpenType signature wOF2
```

**修复**：提供 TTF 版本给 Astro 的 `fonts` 配置。不能仅配 woff2。

### 坑 2a：字体文件过多导致加载缓慢

Noto Serif SC（CJK 字体）每个字重约 8MB。如果配置不当，会同时下载 20 个文件（5 字重 × 2 样式 × 2 格式 ≈ 80MB）。

| 配置项 | 错误配置 | 正确配置 |
|--------|---------|---------|
| `weights` | `[300, 400, 500, 600, 700]` | `[400, 700]` |
| `styles` | `["normal", "italic"]` | `["normal"]` — 中文无斜体 |
| `formats` | `["woff", "ttf"]` 或 `["woff2", "ttf"]` | `["ttf"]` — satori 不支持 woff2，必须提供 ttf |

**经验法则**：
- 中文博客不需要 italic 字形（CJK 无斜体概念）
- 只需 Regular(400) + Bold(700)，不需要 300/500/600
- satori 必须有 ttf，所以 formats 至少包含 "ttf"
- 如果浏览器想用 woff2，需额外配置（当前项目未采用，因为 ttf × 2 = 16MB 对个人博客已可接受）

## 坑 3：`getFontPathByWeight` 默认 format 是 "truetype"

`src/utils/getFontPathByWeight.ts` 中：

```ts
const format = options?.format ?? "truetype";
```

如果不传 `options`，它找 `format === "truetype"` 的 src。如果字体只有 `"woff2"` 格式会匹配不到最后的 fallback `font.src[0]` ——但 fallback 逻辑其实能兜住（详见源码：`font.src.find(file => file.format === format) ?? font.src[0]`）。问题往往出在其他条件先失败（权重不匹配等）。

## 自托管字体的正确配置（Astro 5 + AstroPaper）

```ts
// astro.config.ts
import { defineConfig, fontProviders } from "astro/config";

export default defineConfig({
  fonts: [
    {
      provider: fontProviders.local(),
      name: "My Font Name",
      cssVariable: "--font-my-font",
      fallbacks: ["serif"],
      options: {
        variants: [
          {
            src: ["./src/assets/fonts/MyFont-Regular.ttf"],
            weight: 400,
            style: "normal",
          },
        ],
      },
    },
  ],
  // ...
});
```

关键点：
- 字体文件必须放在 `src/` 目录下（如 `src/assets/fonts/`），不能放 `public/`
- OG 图片文件（`og.png.ts` 和 `index.png.ts`）中硬编码的 CSS 变量名和 font-family 也要同步改
- satori 需要 TTF，浏览器用 woff2——有两个方案：
  - 只在 `fonts` 配 TTF，浏览器用 `@font-face` 单独加载 woff2
  - `variants` 配多个 src（但 satori 层面只认 TTF）

## 中文读者的字体回退链最佳实践

如果使用拉丁字体（如 Google Sans Code，仅含几百个拉丁字符），中文博客必须设置合适的中文回退字体，否则中文内容会回退到浏览器默认的等宽字（通常很丑）。

正确的 `fallbacks` 配置（在 `astro.config.ts` 的字体配置中）：

```ts
fallbacks: ["PingFang SC", "Microsoft YaHei", "Noto Sans SC", "sans-serif"],
```

| 用户系统 | 命中字体 |
|---------|---------|
| macOS | PingFang SC（苹方） |
| Windows | Microsoft YaHei（微软雅黑） |
| Linux | Noto Sans CJK |
| 其他/自定义 | `sans-serif` 浏览器默认无衬线体 |

**效果**：拉丁/数字字符走 Google Sans Code，中文走系统最优字体，零额外下载。

**不要用 `["monospace"]`**——中文等宽体不是为正文阅读设计的，视觉割裂感强。

## 性能分析检查清单

当用户反馈页面加载慢时，按此顺序排查：

1. **浏览器 Performance API**：通过 `browser_console` 执行 `performance.getEntriesByType('resource')` 查看每个资源的加载耗时和大小
2. **建产物检查**：SSH 到 VPS，`ls -lh /home/ubuntu/blog-astro/dist/_astro/fonts/` 查看实际字体文件大小
3. **对比基准**：
   - Google Sans Code（AstroPaper 默认）：~500KB–1MB，每个 ~62KB
   - CJK 字体 ttf：每个 ~15MB
4. **修复路径**：从 CJK 换回默认字体时，只改 `name` 和 `fallbacks`，不动 `cssVariable`

## 方案 A：彻底移除自托管 Google Sans Code（UI 改用系统字体栈）

2026-07 实战：AstroPaper 默认通过 `Layout.astro` 的 `<Font cssVariable="--font-google-sans-code">` 组件（来自 `astro:assets`，**不是** `@astrojs/fonts` integration）把 Google Sans Code 整族 self-host 到 `dist/_astro/fonts/`（21 个 woff/ttf 变体，合计 **~884KB**），首页强制预加载。若 UI 决定用系统字体，可整体移除：

1. **`src/layouts/Layout.astro`**：删 `import { Font } from "astro:assets"` + 删 `<Font .../>` 块。`_astro/fonts/` 目录随之消失。
2. **`src/styles/theme.css`**：`--font-app: var(--font-google-sans-code)` 改为系统字体栈：
   ```css
   --font-app: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, -apple-system, "Segoe UI", sans-serif;
   ```
   导航/按钮/页脚/搜索框等 UI 文字改用系统字体，零下载。
3. **代码块不受影响**：heti 的 `.heti pre/code` 用 `"SFMono-Regular", consolas, monospace`（系统栈），不依赖 `--font-app`。

**效果**：首页本地资源从 ~1.2MB 降到 **322KB**（HTML+CSS+JS+霞鹜子集 219KB），省 ~880KB。

**⚠️ 致命陷阱：`og.png.ts` 会跟着炸**。默认 OG 路由 `src/pages/og.png.ts`（全站分享图，显示 site.title + description + hostname）原本也 `const fonts = fontData["--font-google-sans-code"]`，移除 `<Font>` 后 `fontData` 为空 → 访问 `/og.png` 直接 throw。修复：把 `og.png.ts` 也改成读 `src/assets/fonts/og-subset.ttf`（与文章 OG 的 `index.png.ts` 一致），satori `fonts` 数组用 `{ name: "LxgwWenkai", data: regularData, weight: 400 }`，`fontFamily` 改 `"LxgwWenkai"`。同时 `subset-og.mjs` 必须把 `site.description` + hostname（从 `config.site.url` 解析）+ 社交链接域名也纳入字符集（见 `references/font-subset-lxgw.md`），否则默认 OG 的描述/hostname 出现方框。

> 这与旧「坑 1：删除 fonts 数组会炸 OG」不矛盾——旧结论是「要保留 fonts 数组」，本方案是「移除 `<Font>` 但同步改 `og.png.ts` 脱离 `fontData` 依赖」，二者择一。本博客 2026-07 采用后者（UI 留系统字体 + 霞鹜仅用于 `.heti` 正文 + OG）。

## 远程 VPS 文件编辑注意事项

- 优先用 Python 脚本文件上传执行（`scp + ssh python3`），避免 inline heredoc 的转义地狱
- 修改完用 `git status` 检查是否产生了脏文件（如路径错误写出的 `src/theme.css`、`src/Layout.astro` 等）
- 回退用 `git checkout -- <file>` 最干净
