import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { basePath, nav } from '../src/lib/links.mjs';

const tags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'];

function watch(page) {
  const problems = [];
  page.on('pageerror', (error) => problems.push(`script error: ${error.message}`));
  page.on('console', (message) => { if (message.type() === 'error') problems.push(`console: ${message.text()}`); });
  page.on('requestfailed', (request) => problems.push(`failed: ${request.url()}`));
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.protocol === 'data:') return;
    if (url.hostname !== '127.0.0.1') problems.push(`external request: ${url}`);
    else if (!url.pathname.startsWith(`${basePath}/`)) problems.push(`outside base path: ${url.pathname}`);
  });
  page.on('response', (response) => { if (response.status() >= 400) problems.push(`${response.status()}: ${response.url()}`); });
  return problems;
}

for (const scheme of ['dark', 'light']) {
  test.describe(`${scheme} theme`, () => {
    test.use({ colorScheme: scheme });

    test('loads everything locally, under the base path, without errors', async ({ page }) => {
      const problems = watch(page);
      await page.goto('./', { waitUntil: 'networkidle' });
      await expect(page.locator('html')).toHaveAttribute('data-theme', scheme);
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.fonts.check('16px "Inter Variable"'))).toBe(true);
      expect(problems).toEqual([]);
    });

    test('has no accessibility violations', async ({ page }) => {
      await page.goto('./', { waitUntil: 'networkidle' });
      const result = await new AxeBuilder({ page }).withTags(tags).analyze();
      expect(result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
    });
  });
}

test('fits the viewport and keeps navigation usable', async ({ page }) => {
  await page.goto('./');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBe(0);
  const menu = page.getByRole('navigation', { name: 'Main' });
  for (const { label } of nav) {
    const link = menu.getByRole('link', { name: label, exact: true });
    await expect(link).toBeVisible();
    const box = await link.boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(page.viewportSize().width);
    expect(box.height).toBeGreaterThanOrEqual(24);
  }
  // The fixed header must contain its content and not cover the heading.
  const header = await page.locator('header.header').boundingBox();
  const bar = await menu.boundingBox();
  const title = await page.getByRole('heading', { level: 1 }).boundingBox();
  expect(bar.y + bar.height).toBeLessThanOrEqual(header.y + header.height);
  expect(title.y).toBeGreaterThan(header.y + header.height);
});

test('states its experimental status near the top and has one main heading', async ({ page }) => {
  await page.goto('./');
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
  await expect(page.getByText('Experimental', { exact: true }).first()).toBeInViewport();
});

test('theme can be chosen by the reader', async ({ page }) => {
  await page.goto('./');
  await page.locator('starlight-theme-select select').first().selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
});

test('shows the diagram variant that suits the width', async ({ page }) => {
  await page.goto('./');
  await expect(page.getByRole('img', { name: /^Diagram\./ })).toHaveCount(1);
});

test('unknown addresses show the 404 page', async ({ page }) => {
  const response = await page.goto('./no-such-page/');
  expect(response.status()).toBe(404);
  await expect(page.getByRole('navigation', { name: 'Main' })).toBeVisible();
});
