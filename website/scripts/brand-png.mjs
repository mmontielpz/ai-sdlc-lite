// Renders the PNG downloads, favicon sizes and social preview from the SVG files in public/brand/.
// Run after changing them (needs the Playwright Chromium used by the browser checks): node scripts/brand-png.mjs
import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const brand = `${root}/public/brand`;
const dataUri = (path, type) => `data:${type};base64,${readFileSync(path).toString('base64')}`;
const svg = (name) => dataUri(`${brand}/${name}.svg`, 'image/svg+xml');

const browser = await chromium.launch();
const page = await browser.newPage({ colorScheme: 'dark' });
async function render(file, width, height, body, transparent = true) {
  await page.setViewportSize({ width, height });
  await page.setContent(`<style>html,body{margin:0;background:transparent}img{display:block}</style>${body}`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  writeFileSync(file, await page.screenshot({ omitBackground: transparent }));
}

for (const name of ['on-dark', 'on-light', 'black', 'white']) {
  await render(`${brand}/symbol-${name}.png`, 512, 512, `<img src="${svg(`symbol-${name}`)}" width="512" height="512">`);
  const [, width] = readFileSync(`${brand}/wordmark-${name}.svg`, 'utf8').match(/viewBox="0 0 (\d+) 32"/);
  await render(`${brand}/wordmark-${name}.png`, Number(width) * 8, 256, `<img src="${svg(`wordmark-${name}`)}" height="256">`);
}
// Favicons sit on the canvas colour so they stay legible on any browser chrome.
for (const size of [16, 32, 180]) {
  const inner = size === 180 ? 132 : size;
  await render(`${brand}/favicon-${size}.png`, size, size,
    `<div style="width:${size}px;height:${size}px;display:grid;place-items:center;background:#0B1017"><img src="${svg('favicon')}" width="${inner}" height="${inner}"></div>`, false);
}
const font = dataUri(`${root}/node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2`, 'font/woff2');
await render(`${root}/public/social-card.png`, 1200, 630, `<style>@font-face{font-family:I;src:url(${font});font-weight:100 900}
  main{width:1200px;height:630px;box-sizing:border-box;padding:80px;display:flex;flex-direction:column;justify-content:space-between;background:#0B1017;font-family:I;color:#94A3B8}
  h1{margin:0;font-size:80px;line-height:1.08;letter-spacing:-.045em;font-weight:600;color:#F1F5F9}h1 span{display:block;color:#94A3B8}p{margin:0;font-size:28px}</style>
  <main><img src="${svg('wordmark-on-dark')}" height="56" style="align-self:flex-start"><h1>Engineer with agents.<span>Delegate with confidence.</span></h1>
  <p>Experimental open methodology and reference framework</p></main>`, false);
await browser.close();
console.log('rendered');
