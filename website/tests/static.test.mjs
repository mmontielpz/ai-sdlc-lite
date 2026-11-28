// Checks on the built output and its claims. Run after `npm run build`.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';
import { basePath, repoUrl, siteOrigin } from '../src/lib/links.mjs';

const dist = resolve('dist');
const repo = resolve('..');
const walk = (dir) => readdirSync(dir, { withFileTypes: true })
  .flatMap((e) => (e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]));
const files = walk(dist);
const pages = files.filter((f) => f.endsWith('.html')).map((f) => ({ file: f, html: readFileSync(f, 'utf8') }));
const home = pages.find((p) => p.file === join(dist, 'index.html')).html;
const decode = (s) => s.replaceAll('&amp;', '&').replaceAll('&#38;', '&').replaceAll('&#39;', "'").replaceAll('&quot;', '"');
const text = decode(home.replace(/<(script|style)[\s\S]*?<\/\1>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ');
const attrs = (html) => [...html.matchAll(/<(\w+)[^>]*?\s(href|src)="([^"]*)"/g)].map((m) => ({ tag: m[1], attr: m[2], value: decode(m[3]) }));
const slug = (heading) => heading.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, '').trim().replace(/\s/g, '-');

test('local links and assets carry the base path and exist', () => {
  let checked = 0;
  for (const page of pages) {
    for (const { value } of attrs(page.html)) {
      if (/^(https?:|mailto:|data:)/.test(value)) continue;
      if (value.startsWith('#')) {
        assert.ok(page.html.includes(`id="${value.slice(1)}"`), `${page.file}: missing anchor ${value}`);
        continue;
      }
      assert.ok(value.startsWith(`${basePath}/`), `${page.file}: ${value} lacks the base path`);
      const path = join(dist, value.slice(basePath.length).split(/[?#]/)[0]);
      const target = existsSync(path) && statSync(path).isDirectory() ? join(path, 'index.html') : path;
      assert.ok(existsSync(target), `${page.file}: ${value} does not exist`);
      checked += 1;
    }
  }
  assert.ok(checked > 5);
});

test('stylesheet asset references carry the base path', () => {
  for (const file of files.filter((f) => f.endsWith('.css'))) {
    for (const [, url] of readFileSync(file, 'utf8').matchAll(/url\(["']?([^"')]+)/g)) {
      if (url.startsWith('data:')) continue;
      assert.ok(url.startsWith(`${basePath}/`), `${file}: ${url}`);
      assert.ok(existsSync(join(dist, url.slice(basePath.length))), `${file}: ${url} does not exist`);
    }
  }
});

test('repository links point to existing files and headings', () => {
  const links = pages.flatMap((p) => attrs(p.html)).filter((a) => a.value.startsWith(`${repoUrl}/blob/main/`));
  assert.ok(links.length >= 8);
  for (const { value } of links) {
    const [path, anchor] = value.slice(`${repoUrl}/blob/main/`.length).split('#');
    assert.ok(existsSync(join(repo, path)), `missing repository file ${path}`);
    if (anchor) {
      const slugs = readFileSync(join(repo, path), 'utf8').split('\n').filter((l) => /^#+ /.test(l)).map((l) => slug(l.replace(/^#+ /, '')));
      assert.ok(slugs.includes(anchor), `missing heading #${anchor} in ${path}`);
    }
  }
});

test('nothing is loaded from another origin and there is no analytics', () => {
  for (const page of pages) {
    for (const { tag, value } of attrs(page.html)) {
      if (tag !== 'a' && /^https?:/.test(value)) assert.ok(value.startsWith(siteOrigin), `${page.file}: external ${tag} ${value}`);
    }
    assert.doesNotMatch(page.html, /googletagmanager|google-analytics|plausible|fonts\.googleapis/);
  }
});

test('version and status come from the repository', () => {
  const version = readFileSync(join(repo, 'pyproject.toml'), 'utf8').match(/^version = "([^"]+)"/m)[1];
  assert.ok(text.includes(version));
  assert.match(text, /Experimental/);
  assert.match(text, /no release published/);
});

test('required limitations are stated', () => {
  for (const statement of [
    'No benchmark has been run',
    'does not sandbox or confine an agent',
    'Today, work is human-supervised',
    'Verified agent support is narrower',
  ]) assert.ok(text.includes(statement), `missing: ${statement}`);
  // The detail behind these summaries lives in the canonical documents the page links to.
  for (const path of ['QUALIFICATION_MATRIX.md', 'docs/PUBLIC_ROADMAP.md']) assert.ok(home.includes(`${repoUrl}/blob/main/${path}`), path);
});

test('the example output uses codes and files that exist in the repository', () => {
  const verifier = readFileSync(join(repo, 'scripts/verify_scope.py'), 'utf8');
  for (const code of ['out_of_scope_modification', 'false_pass']) {
    assert.ok(text.includes(code) && verifier.includes(code), code);
  }
  for (const path of ['src/greeter.py', 'result.blocked.json']) {
    assert.ok(text.includes(path) && existsSync(join(repo, 'examples/first-five-minutes', path)), path);
  }
});

test('unsupported claims are absent', () => {
  for (const claim of [
    /production[- ]ready/i, /\bguarantee/i, /\bproven\b/i, /fully autonomous/i, /\bindustry[- ]leading\b/i,
    /\btrusted by\b/i, /\btestimonial/i, /\bcertified\b/i, /\b(is|the) (open )?industry standard\b/i,
    /\d+(\.\d+)?\s?(x|×)\s(faster|cheaper|more)/i, /\d+\s?%\s(faster|fewer|less|more|reduction)/i,
  ]) assert.doesNotMatch(text, claim);
});

test('CI runs the website checks for every repository file the site links to', () => {
  const ci = readFileSync(join(repo, '.github/workflows/ci.yml'), 'utf8');
  const trigger = new RegExp(ci.match(/grep -qE '(\^\(website[^']+)'/)[1]);
  const linked = pages.flatMap((p) => attrs(p.html)).filter((a) => a.value.startsWith(`${repoUrl}/blob/main/`))
    .map((a) => a.value.slice(`${repoUrl}/blob/main/`.length).split('#')[0]);
  for (const path of [...linked, 'README.md', 'pyproject.toml', 'website/package.json']) assert.match(path, trigger);
});

test('brand files are complete and self-contained; the favicon is the provisional concept', () => {
  for (const concept of ['strata', 'threshold', 'trace']) {
    for (const name of ['favicon', ...['symbol', 'wordmark'].flatMap((k) => ['on-dark', 'on-light', 'mono'].map((t) => `${k}-${t}`))]) {
      const svg = readFileSync(`brand/${concept}/${name}.svg`, 'utf8');
      assert.match(svg, /^<svg [^>]*viewBox=/);
      assert.doesNotMatch(svg, /<text|<image|<script|href=|url\(/, `${concept}/${name}`);
    }
  }
  assert.equal(readFileSync('public/favicon.svg', 'utf8'), readFileSync('brand/strata/favicon.svg', 'utf8'));
});
