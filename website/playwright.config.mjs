import { defineConfig } from '@playwright/test';
import { basePath } from './src/lib/links.mjs';

const url = `http://127.0.0.1:4321${basePath}/`;
export default defineConfig({
  testDir: './tests',
  testMatch: '*.spec.mjs',
  forbidOnly: !!process.env.CI,
  reporter: 'list',
  use: { baseURL: url, ...(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}) },
  projects: [360, 768, 1280].map((width) => ({ name: `${width}px`, use: { viewport: { width, height: 800 } } })),
  webServer: { command: 'npm run preview', url, reuseExistingServer: false },
});
