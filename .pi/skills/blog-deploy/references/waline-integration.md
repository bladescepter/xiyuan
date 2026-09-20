# Waline 评论系统集成（VPS Docker + SQLite）

**状态**：✅ 已上线 waline.xiyuan.wiki

## 部署结构

```
浏览器 → Cloudflare DNS（灰云）→ Caddy（自动 HTTPS）→ Waline 容器:8360 → SQLite 文件
```

## 环境

| 项目 | 值 |
|------|-----|
| 容器 | `lizheming/waline:latest`，名 `waline`，restart always |
| 内网 IP | `172.17.0.5:8360`（bridge 网络） |
| 数据卷 | `-v /opt/waline/data:/app/data` |
| SQLite 路径 | `/app/data`（自动生成 waline.sqlite） |
| Caddy 反代 | `waline.xiyuan.wiki` → `172.17.0.5:8360` |

## 关键环境变量

| 变量 | 值 | 说明 |
|------|-----|------|
| `SQLITE_PATH` | `/app/data` | SQLite 文件目录 |
| `JWT_TOKEN` | 随机 base64 | 登录 token，**不要用占位符，首次必须设置有效值** |
| `SITE_NAME` | `西园` | ⚠️ 用中文字面量，不要用 unicode 转义 |
| `SECURE_DOMAINS` | `xiyuan.wiki,waline.xiyuan.wiki` | CORS 白名单 |
| `AUTHOR_EMAIL` | bladescepter@gmail.com | 管理员邮箱 |

> ⚠️ **Docker ≥29.x 脱敏注意**：如果容器已经运行了一段时间，`JWT_TOKEN` 和 `AUTHOR_EMAIL` 的实际值会被 Docker 保护机制截断，从任何途径都读不出来（`docker inspect`、`docker exec env`、`/proc/<pid>/environ` 全部返回 `***`）。重建容器时必须用户提供或重新生成。详见 `references/docker-env-redaction.md`。

## Docker 命令

```bash
docker run -d \
  --name waline --restart always \
  -v /opt/waline/data:/app/data \
  -e TZ=Asia/Shanghai \
  -e SQLITE_PATH=/app/data \
  -e JWT_TOKEN='***' \
  -e SITE_NAME='西园' \
  -e SITE_URL='https://xiyuan.wiki' \
  -e SECURE_DOMAINS='xiyuan.wiki,waline.xiyuan.wiki' \
  -e AUTHOR_EMAIL='blades....com' \
  lizheming/waline:latest
```

## 前端组件：Comments.astro

### 核心模式：点击加载 + Toggle

首次加载时不初始化 Waline，用户点击"▼ 展开评论"后才动态 import + init。关键逻辑：

```js
// @ts-nocheck
// View Transitions 切换后重置加载状态
document.addEventListener("astro:after-swap", () => {
  const c = document.getElementById("waline");
  if (c) c.innerHTML = "";
  document.getElementById("comments-hr")?.classList.add("hidden");
  try { delete window['__walineLoaded']; } catch(e) { window['__walineLoaded'] = false; }
});

window['__walineToggle'] = async function () {
  const container = document.getElementById("waline");
  if (!container) return;

  if (!window['__walineLoaded']) {
    // 首次：加载 Waline 并显示
    window['__walineLoaded'] = true;
    container.classList.remove("hidden");
    document.getElementById("comments-hr")?.classList.remove("hidden");
    container.style.transition = "none";
    const btn = document.querySelector("[data-comment-toggle]");
    if (btn) btn.textContent = "▲ 收起评论";
    const { init } = await import("@waline/client");
    init({ ... });
  } else {
    // 后续：切换显示/隐藏
    container.style.transition = "";
    container.classList.toggle("hidden");
    document.getElementById("comments-hr")?.classList.toggle("hidden");
    const btn = document.querySelector("[data-comment-toggle]");
    if (btn) btn.textContent = container.classList.contains("hidden") ? "▼ 展开评论" : "▲ 收起评论";
  }
};
```

### View Transitions 兼容（关键）

Astro 的 View Transitions 会在页面切换时替换 DOM 但保留脚本上下文。Waline 的 `init()` 如果只在页面加载时执行一次，切换到新页面后 Waline 不会在新 `#waline` 元素上渲染。

**解决方案**：不使用 `data-astro-rerun`，不使用事件委托。唯一可靠的方式是**全局函数 + onclick 属性 + astro:after-swap**。

Waline 按钮需同时具备两个属性：`data-comment-toggle`（用于 JS 查找）和 `onclick="window.__walineToggle()"`（用于触发）。

**失败的方案（不要尝试）**：
| 方案 | 现象 | 原因 |
|------|------|------|
| `data-astro-rerun` | 刷新页面也无法渲染 | Astro 处理 data-astro-rerun 脚本的方式与 Waline 的动态 import 冲突 |
| 事件委托（`document.addEventListener("click", handler)`） | 所有点击无响应 | 脚本上下文加载时序问题导致 click handler 未正确绑定 |

**Waline 按钮**：
```html
<span data-comment-toggle onclick="window.__walineToggle()"
  class="cursor-pointer text-accent hover:text-accent border-b-2 border-dashed border-accent/40 hover:border-accent transition-all text-sm select-none">
  ▼ 展开评论
</span>
```

### 展开收起动画

用 CSS `max-height` + `opacity` 过渡实现滑入滑出效果，0.5s cubic-bezier 缓动曲线。

### 间距处理（重要）

评论折叠时 `<section class="mt-16">` 的 `mt-16`（4rem）仍然占据空白，导致分割线与"上一篇/下一篇"之间多余间距。

**修复**（SSH sed -i 直接改远程文件，不要拷贝本地文件）：
1. 去掉 `<section>` 的 `mt-16`
2. `#waline` 加 `margin-top: 1.5rem`（折叠时 `.hidden` 的 `margin: 0` 覆盖）
3. 评论区与下篇导航之间加 `<hr id="comments-hr">`，JS 同步 toggle hidden 类

## 管理后台

- 注册/登录：`https://waline.xiyuan.wiki/ui/register`
- 第一个注册的用户自动成为管理员

## Waline 配置选项

### init 配置

```js
init({
  el: "#waline",
  serverURL: "https://waline.xiyuan.wiki",
  lang: "zh",
  dark: "html.dark",
  noRss: true,
  noCopyright: true,
  imageUploader: false,
  commentSorting: "latest",
  reaction: false,
  emoji: ["https://unpkg.com/@waline/emojis@1.4.0/tw-emoji"],
  locale: { sofa: "", mail: "邮箱（选填）", link: "网址（选填）" },
  pageSize: 10,
});
```

### CSS 变量覆盖

**亮色模式（Kha-Yan）：**
```css
--waline-theme-color: #8b5cf6;
--waline-active-color: #7c3aed;
--waline-bg-color: #fffaf0;
--waline-bg-color-light: #fff5e6;
--waline-bg-color-hover: #f5ebe0;
--waline-border-color: #e8ddd0;
--waline-info-bg-color: #f5ebe0;
--waline-info-color: #8a8583;
--waline-badge-color: #8b5cf6;
```

**暗色模式（Paper Dark II）：**
```css
--waline-theme-color: #ff6b01;     /* 站点暗色 accent */
--waline-active-color: #e06000;
--waline-color: #c9c3bc;
--waline-bg-color: #1e2029;
--waline-bg-color-light: #242631;
--waline-bg-color-hover: #2a2d3a;
--waline-border-color: #333648;
--waline-info-bg-color: #2a2d3a;
--waline-info-color: #8b8882;
--waline-badge-color: #f59e0b;
--waline-white: #1e2029;
```

> 暗色 `--waline-theme-color` 从默认 `#f59e0b` 改为站点 accent `#ff6b01`。用 SSH sed -i 改，不要整体替换文件。

## 踩坑记录

1. **SECURE_DOMAINS 403**：管理后台域名必须包含在内。
2. **SQLite 初始化**：首次启动时如果 SQLite 文件不存在，需从官方仓库下载预置文件或让 Waline 自行初始化。
3. **JWT_TOKEN 设错**：必须用完整有效随机字符串。
4. **SITE_NAME 不能用 unicode 转义**：`\u897f\u56ed` 不行，直接写 `西园`。
5. **隐藏 section 的 mt-16 残留空白**：即使 `#waline` 被隐藏，外面的 `<section class="mt-16">` 仍然占据上边距。
