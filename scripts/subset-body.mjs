import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Fontmin from 'fontmin';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const postsDir = path.join(root, 'src/content/posts');
const baseline = path.join(process.env.HOME, 'fonts/LXGWWenKai-Regular.ttf');
const outDir = path.join(root, 'public/fonts');
const woff2Out = path.join(outDir, 'lxgw-body.woff2');

const chars = new Set('西园陆西园'.split(''));
const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
for (const f of files) {
  const content = fs.readFileSync(path.join(postsDir, f), 'utf8');
  const parts = content.split('---');
  const body = parts.length >= 3 ? parts.slice(2).join('---') : content;
  for (const ch of body) if (ch.trim()) chars.add(ch);
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
