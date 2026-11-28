import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { siteOrigin, basePath } from './src/lib/links.mjs';

// GitHub Pages project site. Publishing is manual (.github/workflows/pages.yml) and needs the owner to enable Pages.
const card = `${siteOrigin}${basePath}/social-card.png`;
const cardAlt = 'AI-SDLC Lite: Engineer with agents. Delegate with confidence. Experimental.';
export default defineConfig({
  site: siteOrigin,
  base: basePath,
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'AI-SDLC Lite',
      description:
        'An experimental open methodology and lightweight reference framework for governed, verifiable agentic software engineering.',
      favicon: '/brand/favicon.svg',
      head: [
        { tag: 'link', attrs: { rel: 'icon', type: 'image/png', sizes: '32x32', href: `${basePath}/brand/favicon-32.png` } },
        { tag: 'link', attrs: { rel: 'apple-touch-icon', sizes: '180x180', href: `${basePath}/brand/favicon-180.png` } },
        ...[
          ['property', 'og:image', card], ['property', 'og:image:width', '1200'], ['property', 'og:image:height', '630'],
          ['property', 'og:image:alt', cardAlt], ['name', 'twitter:image', card], ['name', 'twitter:image:alt', cardAlt],
        ].map(([key, name, content]) => ({ tag: 'meta', attrs: { [key]: name, content } })),
      ],
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
