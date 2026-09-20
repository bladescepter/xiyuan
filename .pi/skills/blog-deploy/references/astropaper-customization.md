# AstroPaper 自定义改法（xiyuan.wiki）

本博客已完成的自定义项目和操作方式。

## 配置全景图（astro-paper.config.ts）

来源：https://astro-paper.pages.dev/posts/how-to-configure-astropaper-theme/

所有站点配置集中在项目根目录 `astro-paper.config.ts`。当前配置：

### site

| 字段 | 当前值 | 说明 |
|------|--------|------|
| `url` | `https://xiyuan.wiki` | 规范 URL，影响 OG/RSS/Sitemap |
| `title` | `西园` | 站点名 |
| `description` | `陆西园的博客` | SEO 描述 |
| `author` | `陆西园` | 默认文章作者 |
| `profile` | `https://xiyuan.wiki` | 个人站 URL（结构化数据） |
| `lang` | `zh` | HTML lang |
| `timezone` | `Asia/Shanghai` | IANA 时区 |
| `dir` | `ltr` | 文字方向 |
| `ogImage` | ❌ 未配置 | 默认 OG 图（dynamicOgImage=true 时不用） |
| `googleVerification` | ❌ 未配置 | Google Search Console 验证 |

### posts

| 字段 | 当前值 | 默认值 |
|------|--------|--------|
| `perPage` | `10` | 4 |
| `perIndex` | `10` | 4 |
| `scheduledPostMargin` | 15min | 15min |

### features

| 字段 | 当前值 | 默认值 | 说明 |
|------|--------|--------|------|
| `lightAndDarkMode` | `true` | true | 亮暗切换 |
| `dynamicOgImage` | `true` | true | 自动生成每篇 OG 图 |
| `showArchives` | `true` | true | 归档页 |
| `showBackButton` | `true` | true | 返回按钮 |
| `editPost` | ❌ 未配置 | — | 文章下 "Edit this page" 链接 |
| `search` | `"pagefind"` | pagefind | 搜索 |

### 社交 & 分享

- **socials**（顶部导航）：𝕏、Telegram、Email
- **shareLinks**（文章底部分享）→ **当前为空数组**，可加 Telegram / X / 邮件
- 🔜 可用 `github`（图标已有），挂 tracylu8890

### 布局宽度

`src/styles/global.css` 中的 `@utility max-w-app` 控制全站最大宽度。当前 `max-w-3xl`（768px）。改法：

```css
@utility max-w-app {
  @apply max-w-4xl;       /* 896px */
  /* 或 @apply max-w-4xl xl:max-w-5xl; 大屏更宽 */
}
```

### 字体

**astro.config.ts** 中配置，通过 Astro Fonts API 自托管：

```ts
fonts: [{
  name: "Noto Serif SC",
  cssVariable: "--font-google-sans-code",
  provider: fontProviders.google(),
  fallbacks: ["serif"],
  weights: [300, 400, 500, 600, 700],
  styles: ["normal", "italic"],
  formats: ["woff", "ttf"],
}],
```

注意：OG 图片生成（Satori）**不兼容 woff2**，必须包含 `woff` 或 `ttf` 格式。同时 Satori 需要 400 和 700 两个字重。见 `astropaper-fonts-pitfalls.md`。

### Google Search Console

如要添加，在 `astro-paper.config.ts` 加一行：

```ts
site: {
  // ...
  googleVerification: "你的验证码",
},
```

或通过环境变量 `PUBLIC_GOOGLE_SITE_VERIFICATION`。

## 配色方案

**文件位置**：`src/styles/theme.css`

当前使用 AstroPaper 预定义方案：
- 昼：**Kha-Yan**（暖米底 #fefaec + 紫强调 #6e10cf）
- 夜：**Paper Dark II**（深蓝底 #212737 + 橙强调 #ff6b01）

改法：替换 `:root, [data-theme="light"]` 和 `[data-theme="dark"]` 下的 CSS 变量值。
色值见 https://astro-paper.pages.dev/posts/predefined-color-schemes/

## 中文 i18n

**文件位置**：`src/i18n/lang/zh.ts`（自建）

1. 创建 `src/i18n/lang/zh.ts`，基于 `en.ts` 翻译所有字段
2. 修改 `astro.config.ts` 的 i18n 段：
   ```ts
   i18n: {
     locales: ["en", "zh"],
     defaultLocale: "zh",
     routing: { prefixDefaultLocale: false },
   }
   ```
3. 修改 `astro-paper.config.ts` 的 `site.lang` 为 `"zh"`
4. 重建即可

注意：`defaultLocale` 必须设为 `"zh"`，否则 `Astro.currentLocale` 返回 `"en"`，中文翻译不会生效。

## 日期格式

**文件位置**：`src/components/Datetime.astro`

第 39 行，dayjs format 字符串：
```ts
// 原版
const date = datetime.format("D MMM, YYYY");  // → "26 Jun, 2026"
// 改成
const date = datetime.format("YYYY年M月D日");  // → "2026年6月26日"
```

使用 `M` 和 `D`（无前导零）以获得自然中文格式。

## 首页 Hero 区块

**文件位置**：`src/pages/index.astro`

英雄区（第 ~34-60 行）是硬编码的 HTML，需要直接编辑该文件：
- `<h1>` — 大标题文字
- `<p>` — 简介段落
- RSS 图标 — 保留
- 社媒链接区 — 用 `socials.length > 0 && (... <Socials />)` 条件渲染
- README 链接 — 可删掉（不是你的 repo）

社媒渲染需要：
1. 导入 `Socials` 组件：`import Socials from "@/components/Socials.astro"`
2. 从 `config` 解构 `socials`：`const { socials, posts: postsConfig } = config;`

> ⚠️ **编辑远程 Astro 文件务必用 Python+tempfile+SCP 方案**，不要用 bash heredoc。含有 `${}` 模板语法（如 `${import.meta.env.BASE_URL}`）的行会被 bash 展开破坏，导致文件损坏。见 `references/shell-escape-bypass.md`。

## 首页 OG 元信息覆盖

AstroPaper 的 Layout 默认使用 `site.title` 和 `site.description` 作为 OG 标题/描述。首页可以通过给 `<Layout>` 传 props 覆盖：

```astro
<!-- index.astro -->
<Layout description="诗未成章夜未央">
```

Telegram 预览的显示行：

| 行 | 来源 | 改法 |
|---|------|------|
| 第 1 行（标题） | `og:title` = `title` prop → 默认 = `site.title` | 传 `title` prop |
| 第 2 行（灰小字） | ⚠️ `<meta name="author">` | 从 Layout.astro 删除即可 |
| 第 3 行（灰小字） | `og:description` = `description` prop → 默认 = `site.description` | 传 `description` prop |

⚠️ `<meta name="author">` 会被 Telegram 取作第二行显示，如果不想让作者名出现在分享卡片里，从 `src/layouts/Layout.astro` 中删除该行。文章页的 author 信息仍在 JSON-LD 和 frontmatter 中，不受影响。

## 社媒链接配置

**文件位置**：`astro-paper.config.ts`

```ts
socials: [
  { name: "x", url: "https://x.com/bladescepter" },
  { name: "telegram", url: "https://t.me/bladescepter" },
  { name: "mail", url: "mailto:bladescepter@gmail.com" },
],
```

`name` 必须匹配 `src/assets/icons/socials/` 下某个 SVG 文件名，可用：`facebook`, `github`, `linkedin`, `mail`, `pinterest`, `telegram`, `whatsapp`, `x`。

## About 页

**文件位置**：`src/content/pages/about.md`

页面模板在 `src/pages/about.astro`，通过 Astro Content Collections 读取 `src/content/pages/about.md`。

### 可用的 frontmatter 字段

| 字段 | 必须 | 用途 |
|------|------|------|
| `title` | ✅ | 页面 `<title>` + 正文标题 |
| `description` | ✅ | meta 描述 |
| `ogImage` | ❌ | 社交分享图 |
| `canonicalURL` | ❌ | 规范 URL |

内容直接写 markdown 正文。发布时 `0_About页.md` 自动复制到此路径（见 blog-deploy SKILL.md 的文件名约定）。

## 博客图片管理

AstroPaper 官方文档推荐两种方式：

### 方式 A：`src/assets/`（推荐，自动优化）

图片放 `src/assets/images/`，markdown 中用别名或相对路径引用：

```markdown
![描述](@/assets/images/example.jpg)
```

Astro 自动压缩、转格式、响应式处理。

### 方式 B：`public/`（须手动压缩）

图片放 `public/assets/images/`，用绝对路径引用：

```markdown
![描述](/assets/images/example.jpg)
```

⚠️ 官方警告：`public/` 下的图片不会自动优化，**必须先压缩**，否则严重拖慢页面性能。推荐工具：TinyPNG、Squoosh。

### 方式 C：外部图床（R2 等，本站实际方案）

- 不占仓库体积，不拖慢构建
- Astro 不做任何优化——上传前先压缩/转 WebP
- 文章内用完整 URL：`![](https://img.xiyuan.wiki/xxx.webp)`
