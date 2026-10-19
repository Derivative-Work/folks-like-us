// Convert a ComfyUI workflow saved in the editor's format (subgraphs, widgets) to the API format a script can queue.
// Loads the running ComfyUI frontend in headless Chrome and calls its own app.graphToPrompt(), the same code as
// the editor's "Export (API)", so subgraphs, primitives and switches resolve exactly as in the editor.
// Usage: node scripts/comfy_ui_to_api.mjs <workflow.json> <out_api.json> [http://127.0.0.1:8188]
// --no-sandbox: Ubuntu AppArmor blocks Chrome's user-namespace sandbox on this machine.
import fs from 'fs';
import puppeteer from 'puppeteer';

const [inPath, outPath, host = 'http://127.0.0.1:8188'] = process.argv.slice(2);
const workflow = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox'] });
const page = await browser.newPage();
page.on('pageerror', (e) => console.error('PAGE ERROR:', e.message));
await page.goto(host, { waitUntil: 'networkidle2', timeout: 120000 });
await page.waitForFunction(() => window.app && window.app.graph, { timeout: 120000 });
const api = await page.evaluate(async (wf) => {
  await window.app.loadGraphData(wf);
  const p = await window.app.graphToPrompt();
  return p.output;
}, workflow);
fs.writeFileSync(outPath, JSON.stringify(api, null, 1));
console.log(`${outPath}: ${Object.keys(api).length} nodes`);
await browser.close();
