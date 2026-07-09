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

// 收集字符: posts title/author + 站点配置(description/url/社交链接)
const chars = new Set('西园'.split(''));

const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
for (const f of files) {
  const content = fs.readFileSync(path.join(postsDir, f), 'utf8');
  const fm = content.split('---')[1] || '';
  for (const key of ['title', 'author', 'description']) {
    const m = fm.match(new RegExp('^' + key + ':\s*(.+)', 'm'));
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
