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
      favicon: '/favicon.svg',
      customCss: [
        '@fontsource-variable/inter', '@fontsource-variable/jetbrains-mono', './src/styles/theme.css', './src/styles/motion.css',
      ],
      components: {
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      sidebar: [
        { label: 'Start', items: ['docs/getting-started', 'docs/installation'] },
        { label: 'Concepts', items: ['docs/methodology', 'docs/framework', 'docs/examples'] },
        { label: 'Project', items: ['docs/research', 'docs/roadmap', 'docs/contributing'] },
      ],
      // Code blocks use src/components/CodeBlock.astro: conforming markup and no extra renderer.
      expressiveCode: false,
      credits: false,
    }),
  ],
});
