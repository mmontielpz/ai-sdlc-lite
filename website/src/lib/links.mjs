export const siteOrigin = 'https://mmontielpz.github.io';
export const basePath = '/ai-sdlc-lite';
export const repoUrl = 'https://github.com/mmontielpz/ai-sdlc-lite';
/** Canonical document on the default branch. The static check requires the file and anchor to exist. */
export const doc = (path) => `${repoUrl}/blob/main/${path}`;
/** A documentation page on this site. */
export const page = (slug) => `${basePath}/docs/${slug}/`;

export const docsPages = [
  { slug: 'getting-started', label: 'Getting started', summary: 'Your first bounded task' },
  { slug: 'installation', label: 'Installation', summary: 'Build, install, connect' },
  { slug: 'methodology', label: 'Methodology', summary: 'Bound, Observe, Verify' },
  { slug: 'framework', label: 'Framework', summary: 'CLI, Skill, contracts' },
  { slug: 'examples', label: 'Examples', summary: 'Evidence you can rerun' },
  { slug: 'research', label: 'Research', summary: 'Open questions' },
  { slug: 'roadmap', label: 'Roadmap', summary: 'Today and next' },
  { slug: 'contributing', label: 'Contributing', summary: 'Propose a change' },
];

export const nav = [
  { label: 'Docs', href: page('getting-started') },
  { label: 'Examples', href: page('examples'), wide: true },
  { label: 'GitHub', href: repoUrl },
];
