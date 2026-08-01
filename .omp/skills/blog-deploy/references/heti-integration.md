# 赫蹏（Heti）中文排版增强集成

## 概述

[赫蹏](https://sivan.github.io/heti/) 一个简约的网页中文排版增强，对标中文出版规范：标点挤压、中西文混排间距、宋体/黑体/楷体字体层次、贴合网格的行距。

## 本次集成详情

| 项目 | 值 |
|------|-----|
| 博客框架 | Astro（AstroPaper 主题） |
| VPS | VMISS HK, ubuntu@172.17.0.1 |
| 项目路径 | `/home/ubuntu/blog-astro/` |
| 集成时间 | 2026 年 7 月 |
| Heti 版本 | 0.9.6 |
| CDN CSS | `https://cdn.jsdelivr.net/npm/heti/umd/heti.min.css` |
| CDN JS | `https://cdn.jsdelivr.net/npm/heti/umd/heti-addon.min.js` |

> ⚠️ JS 文件名是 `heti-addon.min.js`，不是 `heti.min.js`。后者在 CDN 上不存在。`/umd/` 目录下只有 `heti.min.css` 和 `heti-addon.min.js`。

## 改动清单

集成分为两层：CSS（全站基础样式）和 JS（增强脚本），都放在 `Layout.astro` 全局布局中。

### 1. Layout.astro — 全局 CSS + JS

`src/layouts/Layout.astro`，在 `<head>` 中的 Font 组件 `/>` 之后：

```html
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/heti/umd/heti.min.css" />
    <script is:inline src="https://cdn.jsdelivr.net/npm/heti/umd/heti-addon.min.js"></script>
```

在 `</body>` 之前（theme 模块脚本之后）加初始化脚本：

```html
  <script is:inline data-astro-rerun>
    try { new Heti('.heti').autoSpacing(); } catch(e) {}
  </script>
```

这样所有页面自动获得 Heti JS 能力，不需要每个页面组件单独引用。

### 2. 文章页 — `<article>` 添加 class

`src/pages/posts/[...slug]/index.astro` 的 `<article>` 元素：

```astro
<article id="article" class:list={[
  "mt-8 w-full",
  "app-prose max-w-app",
  "prose-pre:bg-(--shiki-light-bg) dark:prose-pre:bg-(--shiki-dark-bg)",
  "heti",                          // ← 默认模式：黑体正文
]}>
  <Content />
</article>
```

### 3. 关于页 — 内容区域加 Heti 容器

`src/pages/about.astro`，`<Content />` 外面加一层 `<div class="heti">`：

```astro
<div class="heti">
  <Content />
</div>
```

### 4. 首页 — Hero 区

`src/pages/index.astro`，Hero 区 `<section id="hero">` 加在现有 class 后面：

```astro
<section id="hero" class="border-border border-b pt-8 pb-6 heti">
```

**只套在 Hero 区**，不要套在整个 `<main>` 上——否则文章卡片链接的 underline-offset 会被 Heti 覆盖，鼠标悬停出现距离很远的奇怪下划线。

### 字体变体选择

| class | 正文 | 标题 | 引用 | 用户评价 |
|-------|------|------|------|----------|
| `"heti"`（**当前选用**） | 无衬线黑体（苹方/Helvetica） | 无衬线 | 楷体 | ✅ 易读 |
| `"heti heti--song"` | 宋体（衬线） | 宋体 | 楷体 | ❌ 正文难读 |
| `"heti heti--ancient"` | 楷体 | 楷体 | 楷体 | — |

> **⚠️ 经验教训**：不要默认用 `heti--song`。用户明确表示宋体正文难读。纯 CSS 下 `"heti"` 肉眼看到的变化主要是标点挤压等细节，字体效果因系统而异。

### 5. JS 时序与 View Transitions

脚本加载顺序（全在 `Layout.astro` 中）：

1. `<head>` 中 `heti-addon.min.js` 通过 `<script is:inline>` 同步加载 → `Heti` 全局可用
2. `</body>` 前 `data-astro-rerun` 脚本首次运行 → `new Heti('.heti').autoSpacing()` 生效
3. 页面切换（View Transitions）→ `data-astro-rerun` 自动重跑 → 新页面 DOM 也应用间距

**不需要额外的 `astro:after-swap` 监听**——`data-astro-rerun` 天然覆盖。

### 覆盖页面

| 页面 | 容器 | class |
|------|------|-------|
| 文章页 `/posts/*` | `<article id="article">` | `heti` |
| 关于页 `/about/` | `<div>` 包裹 `<Content />` | `heti` |
| 首页 `/` | `<section id="hero">` | `heti`（加在现有 class 后面） |

## 与 Tailwind Typography（prose 类）的兼容性

两套样式目标不重叠：
- `prose` — 基础排版骨架（行距、标题字号、代码高亮配色）
- `.heti` — 中文排版细节（字体族、标点处理、间距）

实测正文、标题、引用、代码块、暗黑模式均和谐共存，无需额外覆盖。

## 坑 & 注意事项

### 🚨 `new Heti()` 只接受 CSS 选择器字符串

**这是导致全站 JS 失效的根本原因。**

症状：`catch` 块吞掉错误，全站所有 `.heti` 容器的间距和标点挤压都不工作，没有任何控制台报错（被 `catch(e) {}` 吃了）。

```js
// ✅ 正确：传入 CSS 选择器字符串
new Heti('.heti').autoSpacing();

// ❌ 错误：传入 DOM 元素对象
const el = document.querySelector('.heti');
new Heti(el).autoSpacing();  // 静默报错，autoSpacing 不执行

// ❌ 错误：forEach 遍历
document.querySelectorAll('.heti').forEach(function(el) {
  try { new Heti(el).autoSpacing(); } catch(e) {}  // el 是 DOM 元素，不工作
});
```

**症状**：`catch` 块吞掉错误，全站所有 `.heti` 容器的间距和标点挤压都不工作，没有任何控制台报错（被 `catch(e) {}` 吃了）。

**补救方法**：需要覆盖多个容器时，分别传入字符串选择器：

```js
// 分别调用，每个传字符串
try { new Heti('.heti').autoSpacing(); } catch(e) {}
try { new Heti('#featured').autoSpacing(); } catch(e) {}
```

### 🚨 `autoSpacing()` 只在 `.heti` 容器内生效

`autoSpacing()` 需要处理 HTMLElement 上带 `heti` 类（`class="heti"`）的容器。如果容器没有 `.heti` class，即使 `new Heti('#id')` 没有报错，autoSpacing 也不会在容器内添加间距 `<span>`。

**症状**：`new Heti('#featured').autoSpacing()` 不报错但无效果，中英文依然紧贴。

**结论**：间距只能覆盖到已有 `.heti` class 的容器。如果卡片/列表区域不想引入 `.heti` 的排版样式，就无法获得 autoSpacing。这是设计权衡，不是 bug。

### 🚨 卡片链接与 Heti 的 link 样式冲突

**问题**：Heti 的 `.heti a` 使用 `border-bottom` 来做下划线效果，而 AstroPaper 的卡片链接（`Card.astro`）使用 Tailwind 的 `text-decoration: underline`。当 `<main>` 套了 `.heti` class 后，卡片链接的 hover 下划线变成距离很远的边框线。

**原因**：Heti 的 CSS：
```css
.heti a { text-decoration: none; }
.heti a:hover { border-bottom: 1px solid; }
```
覆盖了 Card 的 Tailwind 类 `hover:underline decoration-dashed underline-offset-4`。

**解决方案**（`post-card-link` 排除法）：
1. Card 链接加专属 class `post-card-link`
2. 在 `global.css` 中覆盖 Heti 的 link 样式：

```css
/* 卡片链接：排除 Heti 的 border-bottom 和 text-decoration 干扰 */
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

3. Card.astro 中的 `<a>` 加 class：
```astro
<a
  href={...}
  class:list={[
    "text-accent inline-block text-lg font-medium post-card-link",
    "decoration-dashed underline-offset-4 hover:underline",
    "focus-visible:no-underline focus-visible:underline-offset-0",
  ]}
>
```

### 远程文件编辑注意事项

博客项目在 VPS 上，编辑远程 `.astro` 文件有以下注意事项：

1. **路径转义**：`[...slug]` 的方括号在 bash 中是通配符，SSH 命令中必须用单引号包裹路径：
   ```bash
   ssh ubuntu@172.17.0.1 "sed -i 's/old/new/' '/home/ubuntu/blog-astro/src/pages/posts/[...slug]/index.astro'"
   ```

2. **sed 行号插入陷阱**：`sed 'Na\\...'` 在第 N 行**之后**插入新行（a=append）。如果目标行是多行标签的属性行（如 Font 的 `preload=...`），插入的内容会出现在属性和 `/>` **之间**，破坏 HTML 结构。**避免用行号，优先用精确模式匹配。**

3. **sed 多行追加中的 `\\n`**：在 sed 的 `a`（append）命令中，`\\n` 输出为**字面字符 `\\n`**，不是换行。如需多行插入，用 `c`（change）命令配合字面换行，或用 Python 脚本替代。

4. **sed 粘性匹配**：模式如 `^    \\/>$`（自闭合标签的 `/>`）可能匹配文件中**多个相同缩进的标签**（如 Font 的 `/>` 和 RSS link 的 `/>` 都是 4 空格缩进），导致重复插入。**改用更具体的上下文匹配**，或先 grep 确认唯一性。

5. **删除多行 CSS block 时模式匹配仅删匹配行**：`sed -i '/no-heti-link/d'` 只删除含 `no-heti-link` 的行，`{`、`border-bottom:...`、`}` 等不匹配的行会残留，造成 `Missing opening {` 构建错误。正确做法：用行号范围 `sed -i '42,46d'` 或匹配注释行 `sed -i '/卡片链接/,/^}/d'`。

6. **验证**：改完后先 `grep` 和 `sed -n` 看关键行确认结果，再构建。小改动也可能因为引号、转义问题产生混乱。

7. **稳妥方案**：复杂修改（多行、引号嵌套）不走 SSH sed，改为本地 `write_file` → `scp` 覆盖远程（先备份）。参见 `references/shell-escape-bypass.md`。

### 外部 CDN 脚本在 Astro 中必须加 `is:inline`

**这是最常见的陷阱。** Astro 默认将所有 `<script>` 标签作为**模块**处理（bundled + hashed），外部 CDN 脚本不会被原样注入 HTML。

**症状**：构建产物中 `<script src="...cdn...">` 标签完全消失，`typeof Heti` 返回 `'undefined'`。

**解决方案**：添加 `is:inline` 属性：

```html
<script is:inline src="https://cdn.jsdelivr.net/npm/heti/umd/heti-addon.min.js"></script>
```

这条适用于所有第三方 CDN 脚本（统计、评论增强、排版等）。

### Astro 中 `<script>` 类型速查

| 写法 | Astro 处理方式 | 适用于 |
|------|---------------|--------|
| `<script src="...">` | ES Module（bundled + hashed） | 本地模块、npm 包 |
| `<script is:inline src="...">` | 原样注入 HTML | 外部 CDN 脚本 |
| `<script is:inline>` | 原样注入 HTML | 初始化代码、配置注入 |
| `<script is:inline data-astro-rerun>` | 原样 + 每次 View Transitions 重跑 | 需要重新初始化的 DOM 操作 |

### View Transitions 兼容

`data-astro-rerun` 脚本在每次页面切换后重新执行，正好适配 Heti 的 DOM 修改型 JS（autoSpacing）。**不需要**额外的 `astro:after-swap` 监听——`data-astro-rerun` 天然覆盖。

⚠️ 但如果 Heti init 放在 `data-astro-rerun` 脚本的外部（如 Layout.astro 中不带 rerun 的 `<script>`），第一次加载能工作，页面导航后就不再生效。**必须用 `data-astro-rerun`**。

## 回滚方法

```bash
# 从 Layout.astro 移除 Heti CSS/JS 引用
ssh ubuntu@172.17.0.1 \
  "sed -i '/cdn.jsdelivr.net.*heti/d' /home/ubuntu/blog-astro/src/layouts/Layout.astro"

# 从 Layout.astro 移除 init 脚本
ssh ubuntu@172.17.0.1 \
  "sed -i '/new Heti/d' /home/ubuntu/blog-astro/src/layouts/Layout.astro"

# 从 article class 中移除
ssh ubuntu@172.17.0.1 \
  "sed -i 's/\"heti\"/\"\"/' '/home/ubuntu/blog-astro/src/pages/posts/[...slug]/index.astro'"

# 从 about 页移除外层 div
ssh ubuntu@172.17.0.1 \
  "sed -i '/<div class=\"heti\">/{N;d}' /home/ubuntu/blog-astro/src/pages/about.astro"

# 从首页 hero 区移除
ssh ubuntu@172.17.0.1 \
  "sed -i 's/ heti\"/\"/' /home/ubuntu/blog-astro/src/pages/index.astro"

# 从 global.css 移除 post-card-link override
ssh ubuntu@172.17.0.1 \
  "sed -i '/post-card-link/,/^}/d' /home/ubuntu/blog-astro/src/styles/global.css"

# 重建
```

## 项目主页

https://sivan.github.io/heti/
