// S35: capture the real FEC pages for the closing bookend (config/fec.json): for each page, a full-page screenshot and
// the page's visible text, so every figure on screen can be checked against its URL.
// Writes takes/s35/fec/<name>.png (git-ignored) and docs/fec/<name>.txt (takes/s35/fec/ for "private" pages).
// Only www.fec.gov is loaded. --no-sandbox: Ubuntu AppArmor blocks Chrome's user-namespace sandbox on this machine
// (scripts/o_render.mjs); the allowlist below keeps this browser off every other site.
// Usage: node scripts/fec_capture.mjs [name ...]
import fs from 'fs';
import puppeteer from 'puppeteer';

const CFG = JSON.parse(fs.readFileSync('config/fec.json', 'utf8'));
const want = process.argv.slice(2);
fs.mkdirSync('takes/s35/fec', { recursive: true });
fs.mkdirSync('docs/fec', { recursive: true });
const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox'] });
for (const p of CFG.pages.filter((x) => !want.length || want.includes(x.name))) {
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on('request', (r) => {  // fec.gov and its own API only
    const host = new URL(r.url()).hostname;
    (host.endsWith('fec.gov') ? r.continue() : r.abort());
  });
  await page.setViewport({ width: CFG.width, height: CFG.height });
  await page.goto(p.url, { waitUntil: 'networkidle2', timeout: 120000 });
  if (p.wait) await page.waitForSelector(p.wait, { timeout: 60000 }).catch(() => console.error(`${p.name}: no ${p.wait}`));
  await new Promise((r) => setTimeout(r, 3000));  // the data tables fill after the API answers
  await page.evaluate(() => {  // the site's floating feedback button and panel sit over the tables
    for (const e of document.querySelectorAll('body *')) {
      const pos = getComputedStyle(e).position;
      if ((pos === 'fixed' || pos === 'absolute') && /Feedback|Help us improve/.test(e.innerText || '')
          && e.getBoundingClientRect().width < 900) e.style.display = 'none';
    }
  });
  await page.screenshot({ path: `takes/s35/fec/${p.name}.png`, fullPage: true });
  const text = await page.evaluate(() => document.querySelector('main')?.innerText || document.body.innerText);
  const dir = p.private ? 'takes/s35/fec' : 'docs/fec';  // receipts name private donors: kept out of the repo
  fs.writeFileSync(`${dir}/${p.name}.txt`, `${p.url}\ncaptured ${new Date().toISOString()}\n\n${text}\n`);
  console.log(`${p.name}: ${p.url}`);
  await page.close();
}
await browser.close();
