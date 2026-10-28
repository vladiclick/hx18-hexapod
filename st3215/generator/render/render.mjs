// Render GLB files to PNG with three.js in headless Chrome.
// usage: node render.mjs <modules-dir> <model.glb> <out.png> [query-string]
//        node render.mjs <modules-dir> <jobs.json>        (jobs: [{glb, out, query}], one browser for all)
// <modules-dir> is a node_modules folder with three and playwright-core installed.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const [modules, first, out, query = ''] = process.argv.slice(2);
const jobs = first.endsWith('.json') ? JSON.parse(fs.readFileSync(first, 'utf8')) : [{ glb: first, out, query }];
const here = path.dirname(fileURLToPath(import.meta.url));
const { chromium } = await import(pathToFileURL(path.join(modules, 'playwright-core', 'index.mjs')).href);

const types = { '.js': 'text/javascript', '.html': 'text/html', '.glb': 'model/gltf-binary', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file;
  if (url === '/' || url === '/viewer.html') file = path.join(here, 'viewer.html');
  else if (url.startsWith('/model/')) file = path.resolve(jobs[parseInt(path.basename(url), 10)].glb);
  else if (url.startsWith('/labels/')) file = path.join(path.dirname(path.resolve(jobs[0].glb)), path.basename(url));
  else if (url.startsWith('/three/')) file = path.join(modules, 'three', url.slice(7));
  if (!file || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const browser = await chromium.launch({ channel: 'chrome', args: ['--use-angle=metal', '--enable-gpu'] });
for (const [n, job] of jobs.entries()) {
  const params = new URLSearchParams(job.query || '');
  const w = +(params.get('w') || 1800), h = +(params.get('h') || 1400);
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`http://127.0.0.1:${port}/viewer.html?model=/model/${n}.glb&${job.query || ''}`);
  await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
  await page.screenshot({ path: job.out });
  await page.close();
  console.log('wrote', job.out);
}
await browser.close();
server.close();
