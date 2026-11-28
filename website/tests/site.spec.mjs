import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { basePath, docsPages, nav } from '../src/lib/links.mjs';

const tags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'];
const routes = ['./', ...docsPages.map((d) => `./docs/${d.slug}/`)];
const overflow = (page) => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);

function watch(page) {
  const problems = [];
  page.on('pageerror', (error) => problems.push(`script error: ${error.message}`));
  page.on('console', (message) => { if (message.type() === 'error') problems.push(`console: ${message.text()}`); });
  page.on('requestfailed', (request) => problems.push(`failed: ${request.url()}`));
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.protocol === 'data:' || url.protocol === 'blob:') return;
    if (url.hostname !== '127.0.0.1') problems.push(`external request: ${url}`);
    else if (!url.pathname.startsWith(`${basePath}/`)) problems.push(`outside base path: ${url.pathname}`);
  });
  page.on('response', (response) => { if (response.status() >= 400) problems.push(`${response.status()}: ${response.url()}`); });
  return problems;
}

for (const scheme of ['dark', 'light']) {
  test.describe(`${scheme} theme`, () => {
    // Reduced motion shows the final state, so contrast is checked on the content as it settles.
    test.use({ colorScheme: scheme, reducedMotion: 'reduce' });

    for (const route of routes) {
      test(`${route} loads locally, fits and has no accessibility violations`, async ({ page }) => {
        const problems = watch(page);
        await page.goto(route, { waitUntil: 'networkidle' });
        await expect(page.locator('html')).toHaveAttribute('data-theme', scheme);
        await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
        expect(await overflow(page)).toBe(0);
        const result = await new AxeBuilder({ page }).withTags(tags).analyze();
        expect(result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
        expect(await page.evaluate(() => document.fonts.check('16px "Inter Variable"'))).toBe(true);
        expect(problems).toEqual([]);
      });
    }
  });
}

test('header navigation is visible and does not cover the heading', async ({ page }) => {
  for (const route of ['./', './docs/installation/']) {
    await page.goto(route);
    const menu = page.getByRole('navigation', { name: 'Site', exact: true });
    for (const { label, wide } of nav) {
      const link = menu.getByRole('link', { name: label, exact: true });
      if (wide && page.viewportSize().width < 480) continue;
      await expect(link).toBeVisible();
      const box = await link.boundingBox();
      expect(box.x + box.width).toBeLessThanOrEqual(page.viewportSize().width);
      expect(box.height).toBeGreaterThanOrEqual(24);
    }
    const header = await page.locator('header.header').boundingBox();
    const title = await page.getByRole('heading', { level: 1 }).boundingBox();
    expect(title.y).toBeGreaterThanOrEqual(header.y + header.height);
  }
});

test('states its experimental status near the top', async ({ page }) => {
  await page.goto('./');
  await expect(page.getByText('Experimental', { exact: true }).first()).toBeInViewport();
});

test('theme can be chosen by the reader', async ({ page }) => {
  await page.goto('./');
  await page.locator('footer starlight-theme-select select, .site-footer starlight-theme-select select').first().selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
});

test('keyboard: skip link, installation tabs and verification outcome', async ({ page }) => {
  await page.goto('./');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();

  const first = page.getByRole('tab', { name: 'Claude Code' });
  await first.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', { name: 'Codex' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('tabpanel')).toContainText('Not verified.');

  const blocked = page.getByRole('radio', { name: 'Blocked' });
  await expect(blocked).toBeChecked();
  await blocked.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('radio', { name: 'Pass' })).toBeChecked();
  await expect(page.getByText('Status: PASS (computed: PASS, claimed: PASS)')).toBeVisible();
  await expect(page.getByText('Status: BLOCKED', { exact: false })).toBeHidden();
});

test('copy buttons put the shown command on the clipboard', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('./docs/installation/');
  const claude = page.getByRole('tabpanel').getByRole('button', { name: 'Copy commands' });
  await claude.focus();
  await page.keyboard.press('Enter');
  await expect(claude).toHaveText('Copied');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    'ai-sdlc init --repo /path/to/repo --target claude-code --apply\nai-sdlc init --repo /path/to/repo --target claude-code --check');
  expect(await page.locator('.codeblock button[data-code]').count()).toBeGreaterThanOrEqual(7);
});

test('search finds a documentation page from the keyboard', async ({ page }) => {
  const problems = watch(page);
  await page.goto('./', { waitUntil: 'networkidle' });
  await page.keyboard.press('Control+k');
  const input = page.getByRole('searchbox').or(page.locator('dialog input[type="text"]')).first();
  await expect(input).toBeFocused();
  await page.keyboard.type('brownfield');
  const hit = page.locator(`dialog a[href^="${basePath}/docs/examples/"]`).first();
  await expect(hit).toBeVisible();
  await hit.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/docs\/examples\//);
  expect(problems).toEqual([]);
});

test('documentation navigation reaches every page', async ({ page }) => {
  await page.goto('./docs/getting-started/');
  if (page.viewportSize().width < 800) {
    const toggle = page.locator('button[popovertarget="starlight__sidebar"]');
    await toggle.focus();
    await page.keyboard.press('Enter');
  }
  for (const { label, slug } of docsPages) {
    const link = page.locator('#starlight__sidebar').getByRole('link', { name: label, exact: true });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', `${basePath}/docs/${slug}/`);
  }
});

const hiddenParts = (page) => page.evaluate(() =>
  [...document.querySelectorAll('.home [data-animate], .home [data-animate] *, .logo *')]
    .filter((e) => e.getClientRects().length && getComputedStyle(e).opacity === '0' && e.tagName !== 'INPUT').length);

test.describe('reduced motion', () => {
  test.use({ reducedMotion: 'reduce' });
  test('shows the final state at once, with no animation or replay control', async ({ page }) => {
    await page.goto('./', { waitUntil: 'networkidle' });
    expect(await page.evaluate(() => document.getAnimations().length)).toBe(0);
    expect(await page.locator('[data-motion]').count()).toBe(0);
    await expect(page.getByRole('button', { name: 'Replay' })).toBeHidden();
    expect(await hiddenParts(page)).toBe(0);
  });
});

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });
  test('all homepage content is visible', async ({ page }) => {
    await page.goto('./', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500); // the CSS-only logo entrance
    expect(await hiddenParts(page)).toBe(0);
  });
});

test('motion runs once, ends, replays and does not block the page', async ({ page }) => {
  await page.addInitScript(() => {
    window.longTasks = [];
    new PerformanceObserver((list) => window.longTasks.push(...list.getEntries().map((e) => e.duration))).observe({ type: 'longtask', buffered: true });
  });
  await page.goto('./', { waitUntil: 'networkidle' });
  const section = page.locator('[data-animate="sequence"]');
  await section.locator('h2').scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 400);
  await expect(section).toHaveAttribute('data-motion', 'play');
  const running = () => page.evaluate(() => document.getAnimations().filter((a) => a.playState === 'running').length);
  expect(await running()).toBeGreaterThan(0);
  await expect.poll(running, { timeout: 6000 }).toBe(0);
  const endless = () => page.evaluate(() => document.getAnimations().filter((a) => a.effect.getTiming().iterations === Infinity).length);
  expect(await endless()).toBe(0);
  await page.getByRole('button', { name: 'Replay' }).click();
  expect(await running()).toBeGreaterThan(0);
  await expect.poll(running, { timeout: 6000 }).toBe(0);
  // Scroll through the page; every section must end up visible.
  for (let y = 0; y < await page.evaluate(() => document.body.scrollHeight); y += 400) {
    await page.mouse.wheel(0, 400);
    await page.waitForTimeout(60);
  }
  await expect.poll(running, { timeout: 6000 }).toBe(0);
  expect(await hiddenParts(page)).toBe(0);
  expect(await page.evaluate(() => Math.max(0, ...window.longTasks))).toBeLessThan(200);
});

test('unknown addresses show the 404 page', async ({ page }) => {
  const response = await page.goto('./no-such-page/');
  expect(response.status()).toBe(404);
  await expect(page.getByRole('navigation', { name: 'Site', exact: true })).toBeVisible();
});
