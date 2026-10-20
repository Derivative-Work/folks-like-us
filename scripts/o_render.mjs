// Render frames of overlays/folks.html to transparent PNGs (adapted from Ghost in the Machine's render_frames.mjs).
// The page exports window.renderFrame(t) and window.ready; every frame is a pure function of t, so ranges can run in
// any order. Frame f is rendered at t = (f + offset) / fps and written as <out_dir>/<f, 5 digits>.png.
// Usage: node scripts/o_render.mjs <out_dir> <start_frame> <end_frame> <w> <h> <query> [offset_frames=0] [fps=24]
//   e.g. node scripts/o_render.mjs takes/o/S05 0 100 1920 1056 "scene=surface&shot=S05"
//        node scripts/o_render.mjs takes/o/screen 0 3389 1920 1080 "scene=screen"
// Spot checks: <start_frame> = "t:" and a comma list of times in seconds; each frame is written as <t>.png.
// --no-sandbox: Ubuntu AppArmor blocks Chrome's user-namespace sandbox on this machine; only local files are loaded.
import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';

const [outDir, start, end, w, h, query, offset = '0', fps = '24'] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox', '--allow-file-access-from-files'] });
const page = await browser.newPage();
page.on('pageerror', (e) => { console.error('PAGE ERROR:', e.message); process.exitCode = 1; });
page.on('console', (m) => { if (m.type() === 'error') console.error('CONSOLE:', m.text()); });
await page.setViewport({ width: Number(w), height: Number(h) });
await page.goto(`file://${path.resolve('overlays/folks.html')}?${query}&w=${w}&h=${h}`, { waitUntil: 'load' });
await page.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
if (start.startsWith('t:')) {
  for (const t of start.slice(2).split(',').map(Number)) {
    await page.evaluate((x) => window.renderFrame(x), t);
    await page.screenshot({ path: path.join(outDir, `${t.toFixed(2)}.png`), omitBackground: true });
  }
} else {
  for (let f = Number(start); f < Number(end); f++) {
    await page.evaluate((t) => window.renderFrame(t), (f + Number(offset)) / Number(fps));
    await page.screenshot({ path: path.join(outDir, `${String(f).padStart(5, '0')}.png`), omitBackground: true });
  }
}
await browser.close();
