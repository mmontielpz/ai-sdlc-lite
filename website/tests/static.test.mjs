// Checks on the built output and its claims. Run after `npm run build`.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';
import { basePath, docsPages, repoUrl, siteOrigin } from '../src/lib/links.mjs';
import { exampleOutput } from '../scripts/example-output.mjs';

const dist = resolve('dist');
const repo = resolve('..');
const walk = (dir) => readdirSync(dir, { withFileTypes: true })
  .flatMap((e) => (e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]));
const files = walk(dist);
const pages = files.filter((f) => f.endsWith('.html')).map((f) => ({ file: f, html: readFileSync(f, 'utf8') }));
const home = pages.find((p) => p.file === join(dist, 'index.html')).html;
const decode = (s) => s.replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16))).replaceAll('&amp;', '&').replaceAll('&#38;', '&').replaceAll('&#39;', "'").replaceAll('&quot;', '"');
const textOf = (html) => decode(html.replace(/<(script|style)[\s\S]*?<\/\1>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ');
const text = textOf(home);
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
      const anchor = value.split('#')[1];
      if (anchor) assert.ok(readFileSync(target, 'utf8').includes(`id="${anchor}"`), `${page.file}: missing anchor in ${value}`);
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
    'Not verified.',
    'There is no plugin or editor extension',
    'nothing is published to a package index',
    'Documented workflow · not qualified',
  ]) assert.ok(text.includes(statement), `missing: ${statement}`);
  // The detail behind these summaries lives in the canonical documents the page links to.
  for (const path of ['QUALIFICATION_MATRIX.md']) assert.ok(home.includes(`${repoUrl}/blob/main/${path}`), path);
});

test('the verification excerpts are the real output of the bounded example', () => {
  for (const [name, output] of Object.entries(exampleOutput())) {
    assert.equal(readFileSync(`src/data/verify-${name}.txt`, 'utf8'), output, `${name}: run node scripts/example-output.mjs --write`);
  }
});

test('every documentation page is built, linked from the homepage and searchable', () => {
  for (const { slug } of docsPages) {
    assert.ok(existsSync(join(dist, 'docs', slug, 'index.html')), slug);
    assert.ok(home.includes(`${basePath}/docs/${slug}/`), `homepage link to ${slug}`);
  }
  assert.ok(existsSync(join(dist, 'pagefind/pagefind.js')), 'search index');
});

test('every copyable command or file excerpt is made of lines from repository files', () => {
  const sources = [
    'docs/QUICKSTART.md', 'examples/small-fix/README.md', 'examples/small-fix/normalize.py',
  ].flatMap((path) => readFileSync(join(repo, path), 'utf8').split('\n'))
    .flatMap((l) => [l.trim(), l.replace(/[ \t]{2,}# .*$/, '').trim()]); // a trailing comment may be left out
  const copied = pages.flatMap((p) => [...p.html.matchAll(/data-code="([^"]*)"/g)].map((m) => decode(m[1])));
  assert.ok(copied.length >= 10);
  for (const block of copied) {
    for (const line of block.split('\n').map((l) => l.trim()).filter(Boolean)) assert.ok(sources.includes(line), `not in a repository file: ${line}`);
  }
});

test('operational records are not published', () => {
  for (const page of pages) assert.doesNotMatch(page.html, /docs\/(engineering|product)\/|EVIDENCE_INDEX|OWNER_DECISION|\bOD-\d+\b|TAKO|Private Project/, page.file);
});

test('unsupported claims are absent', () => {
  for (const claim of [
    /production[- ]ready/i, /\bguarantee/i, /\bproven\b/i, /fully autonomous/i, /\bindustry[- ]leading\b/i,
    /\btrusted by\b/i, /\btestimonial/i, /\bcertified\b/i, /\b(is|the) (open )?industry standard\b/i,
    /\d+(\.\d+)?\s?(x|×)\s(faster|cheaper|more)/i, /\d+\s?%\s(faster|fewer|less|more|reduction)/i,
  ]) for (const page of pages) assert.doesNotMatch(textOf(page.html), claim, page.file);
});

test('CI runs the website checks for every repository file the site links to', () => {
  const ci = readFileSync(join(repo, '.github/workflows/ci.yml'), 'utf8');
  const trigger = new RegExp(ci.match(/grep -qE '(\^\(website[^']+)'/)[1]);
  const linked = pages.flatMap((p) => attrs(p.html)).filter((a) => a.value.startsWith(`${repoUrl}/blob/main/`))
    .map((a) => a.value.slice(`${repoUrl}/blob/main/`.length).split('#')[0]);
  for (const path of [...linked, 'README.md', 'pyproject.toml', 'website/package.json', 'examples/small-fix/normalize.py', 'scripts/verify_scope.py']) assert.match(path, trigger);
});

test('brand files are complete and self-contained; the favicon is the provisional concept', () => {
  for (const concept of ['brackets', 'strata']) {
    for (const name of ['favicon', ...['symbol', 'wordmark'].flatMap((k) => ['on-dark', 'on-light', 'mono'].map((t) => `${k}-${t}`))]) {
      const svg = readFileSync(`brand/${concept}/${name}.svg`, 'utf8');
      assert.match(svg, /^<svg [^>]*viewBox=/);
      assert.doesNotMatch(svg, /<text|<image|<script|href=|url\(/, `${concept}/${name}`);
    }
  }
  assert.equal(readFileSync('public/favicon.svg', 'utf8'), readFileSync('brand/brackets/favicon.svg', 'utf8'));
});
