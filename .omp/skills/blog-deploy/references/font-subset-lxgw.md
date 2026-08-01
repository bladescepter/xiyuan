# 全站换霞鹜文楷（LxgwWenkai）动态子集方案

> 状态：2026-07 已执行并验证。OG 图 + 正文均换 LxgwWenkai，动态子集，体积最小化。
> 配套 SKILL.md 构建步骤 2a 已固化「每次发布必跑两个子集脚本」。

## 为什么动态子集

- 完整 CJK ttf 约 15–50MB，塞进 satori 又 `embedFont:true` 会撑大每张 OG PNG，且构建要加载整本字库。
- 动态子集只含**实际用到的字**：OG 图仅标题/作者/站点名（~54 字，20KB），正文仅文章正文去重字（~841 字，woff2 178KB）。
- 用户约束：最小化、每次发布动态子集、Waline 评论区不纳入（保持默认字体）。

## 文件布局

| 文件 | 作用 | 进 git？ |
|------|------|---------|
| `~/fonts/LXGWWenKai-Regular.ttf` (v1.522) | 子集化基线（完整字库） | 否（项目外，VPS 本地） |
| `scripts/subset-og.mjs` | 扫 posts frontmatter → `src/assets/fonts/og-subset.ttf` | 是 |
| `scripts/subset-body.mjs` | 扫 posts 正文 → `public/fonts/lxgw-body.woff2` | 是 |
| `src/assets/fonts/og-subset.ttf` | satori (OG 图) 用 | 是 |
| `public/fonts/lxgw-body.woff2` | 正文 `.heti` 容器用 | 是 |

依赖：`fontmin`（devDependency）。`ttf2woff2` 用 fontmin 自带插件 `Fontmin.ttf2woff2()`，不要单独装 CLI（pnpm 下 CLI 不在 PATH）。

## 子集脚本源码（已验证可跑）

### scripts/subset-og.mjs

> ⚠️ **必须覆盖默认 OG 用到的全部字符**：文章 OG（`index.png.ts`）只用 title/author，但默认 OG（`og.png.ts`）还显示 `site.description` + hostname + 社交域名。漏扫这些 → 默认 OG 出现方框（tofu）。下方版本已含 `astro-paper.config.ts` 的 `description` / `url` hostname / 所有社交链接域名。

```js
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Fontmin from 'fontmin';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const postsDir = path.join(root, 'src/content/posts');
const cfgPath = path.join(root, 'astro-paper.config.ts');
const baseline = path.join(process.env.HOME, 'fonts/LXGWWenKai-Regular.ttf');
const outDir = path.join(root, 'src/assets/fonts');
const outFile = path.join(outDir, 'og-subset.ttf');

const chars = new Set('西园'.split(''));

const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
for (const f of files) {
  const content = fs.readFileSync(path.join(postsDir, f), 'utf8');
  const fm = content.split('---')[1] || '';
  for (const key of ['title', 'author']) {
    const m = fm.match(new RegExp('^' + key + ':\\s*(.+)', 'm'));
    if (m) for (const ch of m[1].trim()) chars.add(ch);
  }
}

// 站点配置: astro-paper.config.ts
const cfg = fs.readFileSync(cfgPath, 'utf8');
const descM = cfg.match(/description:\s*"([^"]*)"/);
if (descM) for (const ch of descM[1]) chars.add(ch);
const urlM = cfg.match(/url:\s*"([^"]*)"/);
if (urlM) {
  try {
    const host = new URL(urlM[1]).hostname; // xiyuan.wiki
    for (const ch of host) chars.add(ch);
  } catch {}
}
// 社交链接域名 (x.com / t.me / gmail)
for (const m of cfg.matchAll(/url:\s*"([^"]*)"/g)) {
  try { const h = new URL(m[1]).hostname; for (const ch of h) chars.add(ch); } catch {}
}

const text = [...chars].join('');
console.log('[subset-og] 字符集 ' + text.length + ' 字');

if (!fs.existsSync(baseline)) { console.error('baseline missing: ' + baseline); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
new Fontmin()
  .src(baseline)
  .use(Fontmin.glyph({ text, hinting: false }))
  .dest(outDir)
  .run((err, outFiles) => {
    if (err) { console.error(err); process.exit(1); }
    const generated = path.join(outDir, 'LXGWWenKai-Regular.ttf');
    if (fs.existsSync(generated)) fs.renameSync(generated, outFile);
    console.log('[subset-og] -> ' + outFile + ' (' + fs.statSync(outFile).size + ' bytes)');
  });
```

### scripts/subset-body.mjs
```js
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Fontmin from 'fontmin';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const postsDir = path.join(root, 'src/content/posts');
const pagesDir = path.join(root, 'src/content/pages');
const indexAstro = path.join(root, 'src/pages/index.astro');
const baseline = path.join(process.env.HOME, 'fonts/LXGWWenKai-Regular.ttf');
const outDir = path.join(root, 'public/fonts');
const woff2Out = path.join(outDir, 'lxgw-body.woff2');

const chars = new Set('西园陆西园'.split(''));

// 1. posts 正文
const postFiles = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
for (const f of postFiles) {
  const content = fs.readFileSync(path.join(postsDir, f), 'utf8');
  const parts = content.split('---');
  const body = parts.length >= 3 ? parts.slice(2).join('---') : content;
  for (const ch of body) if (ch.trim()) chars.add(ch);
}

// 2. about.md 全文 (About 页正文, 用 .heti)
if (fs.existsSync(path.join(pagesDir, 'about.md'))) {
  const about = fs.readFileSync(path.join(pagesDir, 'about.md'), 'utf8');
  for (const ch of about) if (ch.trim()) chars.add(ch);
}

// 3. index.astro 硬编码中文 (hero 诗句 + 简介 + 导航)
if (fs.existsSync(indexAstro)) {
  const idx = fs.readFileSync(indexAstro, 'utf8');
  for (const ch of idx) if (/[一-鿿]/.test(ch)) chars.add(ch);
}

const text = [...chars].join('');
console.log('[subset-body] 字符集 ' + text.length + ' 字');

if (!fs.existsSync(baseline)) { console.error('baseline missing: ' + baseline); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
new Fontmin()
  .src(baseline)
  .use(Fontmin.glyph({ text, hinting: false }))
  .use(Fontmin.ttf2woff2())
  .dest(outDir)
  .run((err, outFiles) => {
    if (err) { console.error(err); process.exit(1); }
    const gen = outFiles.find(f => f.path.endsWith('.woff2'));
    if (!gen) { console.error('未生成 woff2'); process.exit(1); }
    fs.writeFileSync(woff2Out, gen.contents);
    console.log('[subset-body] -> ' + woff2Out + ' (' + fs.statSync(woff2Out).size + ' bytes)');
  });
```
> ⚠️ **子集字符集必须覆盖所有 `.heti` 渲染源**：posts 正文 + `about.md` + `index.astro` 硬编码中文（hero 诗句"天高苍岭近 风远暮云低" + 简介 + 导航）。漏扫任一源 → 该处文字 fallback 系统字体，与霞鹜混排。用户初报"字体混杂"时方向之一即字符集未覆盖 hero/about。`scripts/subset-og.mjs` 同理需覆盖 `index.png.ts` 用到的一切中文。

## 代码改动点

- **`src/pages/posts/[...slug]/index.png.ts`**（OG 图 satori）：
  - import 加 `fs`/`path`；删 `fontData`/`experimental_getFontFileURL`/`getFontPathByWeight` 用法。
  - GET 内改为 `const ogFontPath = path.resolve(process.cwd(), "src/assets/fonts/og-subset.ttf"); const regularData = fs.readFileSync(ogFontPath);`
  - satori `fonts` 数组只留一项 `{ name: "LxgwWenkai", data: regularData, weight: 400 }`（正文不必粗体，OG 标题 bold 靠 satori 请求无对应字重时 fallback 到 Regular，能正常显示中文不方框）。
  - 最外层容器 style 加 `fontFamily: "LxgwWenkai, sans-serif"`。
- **`src/styles/global.css`** 末尾追加：
  ```css
  @font-face {
    font-family: "LxgwWenkai";
    src: url("/fonts/lxgw-body.woff2") format("woff2");
    font-weight: 400; font-style: normal; font-display: swap;
  }
  .heti { font-family: "LxgwWenkai", "PingFang SC", "Microsoft YaHei", serif; }
  ```
  Waline 容器无 `.heti` class，自然不套霞鹜（保持默认字体）。

## ⚠️ 构建期踩坑（本次实战，必看）

1. **Astro `import.meta.url` 在预渲染时是 BUILT CHUNK 路径，不是源码路径。**
   最初用 `path.resolve(__ogDir, "../../../../assets/fonts/og-subset.ttf")` 相对 `index.png.ts` 源码位置算路径，构建报错 `ENOENT /home/ubuntu/assets/fonts/og-subset.ttf`（少一层 `blog-astro`），改 `../../../` 后又变成 `/home/ubuntu/blog-astro/assets/...`（多一层）。根因：satori 在 `dist/.prerender/chunks/` 里跑，`import.meta.url` 指向 chunk。
   **正确做法**：用 `path.resolve(process.cwd(), "src/assets/fonts/og-subset.ttf")`——`pnpm build` 时 cwd 是项目根，稳定可靠。**不要依赖 `import.meta.url` 定位子集字体。**

2. **`ttf2woff2` 独立 CLI 在 pnpm 下 `ENOENT`。**
   先试 `execFileSync('ttf2woff2', ...)` 报 spawn 找不到。改用 **fontmin 自带插件** `Fontmin.ttf2woff2()`（在 `.use()` 链里），无需独立二进制，干净出 woff2。

3. **fontmin `.dest()` 默认用源文件名 `LXGWWenKai-Regular.ttf` 写出。**
   脚本崩溃于后续步骤时，会留下 `public/fonts/LXGWWenKai-Regular.ttf`（及 woff2 版）stray 文件，被 `public/` → `dist/` 复制带入线上。本次第一版脚本在 `execFileSync` 前已写出 ttf，崩溃后残留，导致 `dist/fonts/` 多出无用文件。
   **清理**：`rm public/fonts/LXGWWenKai-Regular.*` 后重构建。终版脚本直接 `fs.writeFileSync(woff2Out, gen.contents)` 不落默认名，无残留。

4. **pnpm 在 VPS 需先激活 nvm**：远程跑任何 `pnpm`/`node` 前必须
   `export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 22 --silent`，否则 `pnpm: command not found`。

5. **正文 `.heti` 容器确认**：`grep class="heti` 在构建 HTML 里可能匹配不到（class 属性含多个值如 `class="heti ..."`），但 `heti` 字样出现即说明类已套上。字体生效看 CSS 里的 `@font-face` + `.heti{font-family}` 是否在 `dist/_astro/*.css` 中（确认 `grep LxgwWenkai dist/_astro/*.css`）。

## 验证清单

- OG 图：拉 `dist/posts/XXX/index.png` 用 vision 确认中文非方框（本次 004 从 21KB→37KB，中文正常）。
- 正文：`curl -sI https://xiyuan.wiki/fonts/lxgw-body.woff2` 应 `200 font/woff2`；`grep LxgwWenkai dist/_astro/*.css` 应有 `@font-face`。
- 构建命令见 SKILL.md 步骤 2a + 2b（先跑子集脚本再 build）。

## 风险与权衡

- **开放字符集**：正文子集只扫「已发布文章正文」，不含 3500 字表兜底、不含评论。未来某篇冒出子集外生僻字 → 该字正文 fallback 系统字体（可能风格略差但不方框），OG 图会 tofu。出现时重跑子集脚本即可。
- **每次发布必跑子集脚本**：漏跑 = 新字不进字体。已固化进发布流程。

## OG 图 `by 陆西园` 已删除（2026-07）

用户要求去掉 OG 图左下角的 `by 陆西园`（"by" 渲染异常，且右下角已有站点名标识来源）。`src/pages/posts/[...slug]/index.png.ts` 底部一行原为 `[by , 透明引号 span, author span] + [site.title span]`；已删除左侧 `by` + 作者 span，仅保留右侧 `config.site.title`（"西园"）。改动后 OG PNG 体积略降，中文正常非方框。

## ⚠️ Cloudflare 缓存导致字体更新不生效（2026-07 实测坑）

博客使用 Cloudflare CDN，字体文件 `/fonts/lxgw-body.woff2` 的 `cache-control` 为 `max-age=14400`（4 小时）。Cloudflare 会缓存此文件，即使重新生成了子集并构建，CDN 仍可能返回旧版本。

**现象**：用户硬刷新浏览器后，正文仍显示旧字体或部分字 fallback。服务端文件已更新（md5 确认），curl 直接请求也返回新文件，但 `cf-cache-status: HIT` 说明 CDN 缓存未失效。

**排查方法**：
```bash
# 检查 CDN 状态
curl -sI https://xiyuan.wiki/fonts/lxgw-body.woff2 | grep -i 'cf-cache-status'
# HIT = CDN 缓存旧版；MISS = 已刷新

# 加查询参数绕过 CDN 缓存（仅用于验证实际文件）
curl -sI 'https://xiyuan.wiki/fonts/lxgw-body.woff2?v=2' | grep -i 'cf-cache-status'
```

**解决方案**：
1. **等缓存过期**（最长 4 小时）—— Cloudflare 会自动回源拉新
2. **手动在 Cloudflare Dashboard 清除缓存**：Cache → Purge → Custom URL，输入 `/fonts/lxgw-body.woff2`
3. **给字体文件加版本号**（长期方案）：修改 `global.css` 的 `@font-face` 中 `src` 为 `/fonts/lxgw-body.woff2?v=<hash>`，或在构建时自动给字体名加 hash。但需要谨慎评估，因为改了 CSS 后 CSS 本身有 Astro hash 可破缓存，但字体 URL 不变。
4. **降低 `cache-control`**：在 Caddyfile 中为字体文件设置更短的 max-age，或加 `must-revalidate` 指令。

> ⚠️ 注意：`dist/fonts/LXGWWenKai-Regular.ttf`（451KB，完整字库）和 `dist/fonts/LXGWWenKai-Regular.woff2`（243KB）是 `public/` 中旧残留文件被 Astro 复制到 `dist/` 的结果，**不是 CSS 加载的字体**。CSS 始终加载 `/fonts/lxgw-body.woff2`（子集版）。两个 woff2 文件 md5 相同说明它们实际是同一文件。残留文件无害但浪费空间，清理方法：`rm public/fonts/LXGWWenKai-Regular.*` 后重构建。

## 诊断「字体混杂 / 部分字不是霞鹜」的权威方法（浏览器内实测）

用户反馈"hero/about 部分字是霞鹜、部分不是"时，**不要靠猜字符集是否覆盖**。用浏览器工具（browser_navigate + browser_console）跑以下实测，区分三种真因：

```js
// 1) 逐字检查某容器内中文是否真的在 LxgwWenkai 子集内
const el = document.querySelector('.heti');  // 或 nav / button / body
const missing = [];
for (const ch of new Set(el.innerText.split(''))) {
  if (!ch.trim() || !/[一-鿿]/.test(ch)) continue;
  if (!document.fonts.check('16px "LxgwWenkai"', ch)) missing.push(ch);
}
console.log('缺字:', missing.join('') || '无(全在子集)');

// 2) 对比不同元素的 computed font-family，确认字体作用域
const g = el => getComputedStyle(el).fontFamily;
console.log('body:', g(document.body), '| nav:', g(document.querySelector('nav')), '| .heti:', g(document.querySelector('.heti')));
```

三种真因及对策：
- **`missing` 非空** → 子集字符集真漏字（扫源不全）。修正 `subset-body.mjs` 的扫描范围（见上方脚本，必须含 posts + about.md + index.astro 硬编码中文），重跑子集 + 重建。
- **`missing` 为空但视觉仍"部分不是霞鹜"** → 字体已正确应用，问题是**该元素不在 `.heti` 作用域内**（如 nav/button/页脚走 body 的系统字体）。这是设计选择：本博客即采用「仅 `.heti` 用霞鹜、UI 留系统字体」的双字体系统，符合用户 2026-07 决定。若想全站统一，需在 `global.css` 给 `body` 也设 `font-family: "LxgwWenkai", ...`（但代码块保留等宽）。
- **`document.fonts.check` 全通过但 `cf-cache-status: HIT`** → CDN 缓存问题，参见上方 ⚠️ Cloudflare 缓存节。

> ⚠️ **vision 模型对中文书法风格辨别不准**：霞鹜文楷笔画较均匀，常被误判为"黑体/微软雅黑"。判断字体是否生效**以 `document.fonts.check` + `getComputedStyle` 的实测为准**，不要只信截图视觉描述。本次曾因过度依赖 vision 判断而误判"没变化"，实际 LxgwWenkai 已 `status: loaded` 且全部中文在子集内——真因是 UI 文字本就不在 `.heti` 作用域。
