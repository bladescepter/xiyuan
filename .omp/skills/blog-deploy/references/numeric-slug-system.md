# 文章编号 URL 系统

URL 格式：`/posts/001/`、`/posts/002/`、`/posts/003/`……

## 原理

通过在 frontmatter 中加 `slug` 字段，路由优先使用自定义 slug 而非文件名。

## 改动的文件

| 文件 | 改动 |
|---|---|
| `src/content.config.ts` | 在 Zod schema 中加 `slug: z.string().optional()` |
| `src/utils/getPostPaths.ts` | `getPostSlug()` 和 `getPostUrl()` 新增 `customSlug?` 可选参数，有值则优先使用 |
| `src/pages/posts/[...slug]/index.astro` | `getStaticPaths` 传 `post.data.slug`；canonical URL 传 `post.data.slug` |
| `src/pages/posts/[...slug]/index.png.ts` | OG 图路由传 `post.data.slug` |
| `src/components/Card.astro` | 文章卡片链接传 `data.slug` |
| `src/pages/posts/[...slug]/_components/AdjacentPostNav.astro` | 类型加 `slug?: string`，prev/next 链接传 `post.slug` |
| `src/pages/rss.xml.ts` | RSS 条目链接传 `data.slug` |
| `src/pages/posts/[...slug]/index.astro`（props） | prevPost/nextPost 对象加 `slug` 字段 |

## 计数器

文件：`/home/ubuntu/blog-astro/.slug-counter`

- 只存下一个可用编号（纯数字，如 `3`）
- 发布时 Agent 读取 → `str(i).zfill(3)` 补零 → 写入 frontmatter → 写回计数器 +1
- 写入时 YAML 必须加引号：`slug: "003"`，否则 YAML 将前导零解析为八进制数

## 发布时自动填充规则

Agent 在 `blog-deploy` skill 的 frontmatter 预处理步骤中：

1. 读取 VPS 上的 `.slug-counter`
2. 对新文章（无 `slug` 字段的）分配编号
3. 写入 `slug: "NNN"`
4. 计数器 +1
