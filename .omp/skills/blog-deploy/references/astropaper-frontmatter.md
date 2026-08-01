# AstroPaper 文章 frontmatter 字段

## 字段定义

来源：`src/content.config.ts` 的 Zod schema。

| 字段 | 类型 | 必须？ | 说明 |
|---|---|---|---|
| `title` | string | ✅ 必填 | 文章标题 |
| `description` | string | ✅ 必填 | 文章摘要/SEO 描述 |
| `pubDatetime` | ISO 8601 | ✅ 必填 | 格式 `2026-06-26T00:00:00+08:00` |
| `author` | string | 可选 | 默认 `site.author` |
| `modDatetime` | ISO 8601 | 可选 | 修改时间 |
| `featured` | boolean | 可选 | `true` 则首页精选区显示 |
| `draft` | boolean | 可选 | `true` 则不发布 |
| `tags` | string[] | 可选 | 默认 `["others"]` |
| `ogImage` | path/URL | 可选 | 社交媒体分享图 |
| `canonicalURL` | string | 可选 | 规范 URL |
| `hideEditPost` | boolean | 可选 | 隐藏"编辑此页"按钮 |
| `timezone` | string | 可选 | IANA 时区 |
| `slug` | string | 可选 | 自定义 URL 编号，如 `"001"`。通过修改 schema + getPostPaths 实现，见 `references/numeric-slug-system.md` |

## Slug 系统

文章 URL 使用三位编号：`/posts/001/`、`/posts/002/`……

- 用户在 frontmatter 里不写 `slug`，由发布流程自动分配
- 计数器文件：VPS 上 `/home/ubuntu/blog-astro/.slug-counter`
- 值写入时为带引号的字符串（`slug: "003"`），防止 YAML 解析为八进制数
- 旧文章已有值不动

详见 `references/numeric-slug-system.md`。

## 用户的工作流

用户在 Obsidian 中只写 `title`，其他字段自动处理：

| 字段 | 处理方式 |
|---|---|
| `pubDatetime` | 发布时 Agent 自动填入当前时间 `+08:00` |
| `description` | 发布时 Agent 从正文取第一段（截到第一个句号，最长 150 字） |
| `tags` | 如果为空 → 默认 `["随笔"]` |
| `author` | 如果为空 → `陆西园` |

规则依据：**如无必要勿增实体** — 不用 Templater 等插件，一切由 Agent 在发布时自动填充。
