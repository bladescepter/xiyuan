# AstroPaper 第三方样式/脚本集成陷阱

> 引用方式：`skill_view(name='blog-deploy', file_path='references/astropaper-third-party-integration.md')`

## 前置说明

## 外部 CDN 脚本

Astro 默认把 `<script>` 当模块处理，外部 CDN URL 可能被丢弃。**必须加 `is:inline`**：

```astro
<!-- ✅ 正确 -->
<script is:inline src="https://cdn.jsdelivr.net/npm/heti/umd/heti-addon.min.js"></script>

<!-- ❌ 会被 Astro 处理掉 -->
<script src="https://cdn.jsdelivr.net/npm/heti/umd/heti-addon.min.js"></script>
```

## CSS 链接

外部 CSS 不需要特殊处理，直接引入 `<head>` 即可：

```astro
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/heti/umd/heti.min.css" />
```

## View Transitions 兼容

用 `data-astro-rerun` 让脚本在每次页面导航后重新执行：

```astro
<script is:inline data-astro-rerun>
  // 每次导航都重新运行
  try { new Heti('.heti').autoSpacing(); } catch(e) {}
</script>
```

## CSS 特异性冲突（Tailwind 关键）

Tailwind utility class 的特异性通常低于 `.third-party a` 类选择器。第三方 CSS 可能覆盖 Tailwind 的效果。

**典型案例**：Heti 的 `.heti a { text-decoration: none; }` 会覆盖卡片链接的 `hover:underline`。

**解决方式**：在 global.css 中用 `!important` 覆盖第三方样式，或给特定元素加排除 class。

```css
/* global.css */
.heti .post-card-link:hover {
  border-bottom: none !important;
  text-decoration: underline !important;
  text-decoration-style: dashed !important;
  text-underline-offset: 4px !important;
}
```

## autoSpacing 依赖 .heti 容器

Heti 的 `autoSpacing()` 只在 `.heti` 容器内生效。`new Heti(el)` 传 DOM 元素会报错，必须传 CSS 选择器字符串：

```js
// ✅ 正确
new Heti('.heti').autoSpacing()

// ❌ 会报错（el 是 DOM 元素）
new Heti(el).autoSpacing()
```

## Tailwind v4 的 global.css 结构

```css
@import "tailwindcss";
@import "./theme.css";
@import "./typography.css";

@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));

@layer base { ... }
@utility app-layout { ... }
```

没有 `tailwind.config.js` —— 配置在 `@theme inline {}` 块中。第三方 CSS 加在文件末尾。

## 编辑远程 VPS 文件的稳妥方式

SSH heredoc 和 `sed` 处理多行内容时容易出错。对于远程文件修改，优先用：

1. **Python 脚本** — 本地写好，scp 到 VPS 执行
2. **patch 工具**（仅本地文件）
3. **单行 sed** 只做简单替换（如改 class 名），不做多行插入

```bash
# 对远程 VPS 做多行替换的正确姿势
scp /opt/data/script.py ubuntu@172.17.0.1:/home/ubuntu/
ssh ubuntu@172.17.0.1 "python3 /home/ubuntu/script.py"
```
