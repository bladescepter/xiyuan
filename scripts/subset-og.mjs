import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Fontmin from 'fontmin';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const postsDir = path.join(root, 'src/content/posts');
const baseline = path.join(process.env.HOME, 'fonts/LXGWWenKai-Regular.ttf');
const outDir = path.join(root, 'src/assets/fonts');
const outFile = path.join(outDir, 'og-subset.ttf');

// 收集字符: 所有 posts 的 title + author + 站点名
const chars = new Set('西园'.split(''));
const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
for (const f of files) {
  const content = fs.readFileSync(path.join(postsDir, f), 'utf8');
  const fm = content.split('---')[1] || '';
  for (const key of ['title', 'author']) {
    const m = fm.match(new RegExp('^' + key + ':\s*(.+)', 'm'));
    if (m) for (const ch of m[1].trim()) chars.add(ch);
  }
}
const text = [...chars].join('');
console.log('[subset-og] 字符集 ' + text.length + ' 字');

if (!fs.existsSync(baseline)) { console.error('baseline missing: ' + baseline); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
new Fontmin()
  .src(baseline)
  .use(Fontmin.glyph({ text, hinting: false }))
  .dest(outDir)
  .run((err, files) => {
    if (err) { console.error(err); process.exit(1); }
    // fontmin 输出文件名沿用源名, 重命名为 og-subset.ttf
    const generated = path.join(outDir, 'LXGWWenKai-Regular.ttf');
    if (fs.existsSync(generated)) fs.renameSync(generated, outFile);
    console.log('[subset-og] -> ' + outFile + ' (' + fs.statSync(outFile).size + ' bytes)');
  });
