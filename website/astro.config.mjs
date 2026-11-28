import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { siteOrigin, basePath } from './src/lib/links.mjs';

// GitHub Pages project site. Deployment is not configured.
export default defineConfig({
  site: siteOrigin,
  base: basePath,
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'AI-SDLC Lite',
      description:
        'An experimental open methodology and lightweight reference framework for governed, verifiable agentic software engineering.',
      logo: {
        dark: './brand/strata/wordmark-on-dark.svg',
        light: './brand/strata/wordmark-on-light.svg',
        replacesTitle: true,
      },
      favicon: '/favicon.svg',
      customCss: ['@fontsource-variable/inter', '@fontsource-variable/jetbrains-mono', './src/styles/theme.css'],
      components: {
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      // Search, pagination and edit dates have nothing to work on until documentation pages exist.
      pagefind: false,
      pagination: false,
      credits: false,
    }),
  ],
});
