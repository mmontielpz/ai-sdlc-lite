export const siteOrigin = 'https://mmontielpz.github.io';
export const basePath = '/ai-sdlc-lite';
export const repoUrl = 'https://github.com/mmontielpz/ai-sdlc-lite';
/** Canonical document on the default branch. The static check requires the file and anchor to exist. */
export const doc = (path) => `${repoUrl}/blob/main/${path}`;

// Dedicated pages are not implemented yet, so navigation goes to canonical documents.
export const nav = [
  { label: 'Docs', href: doc('README.md#documentation-map') },
  { label: 'Roadmap', href: doc('docs/PUBLIC_ROADMAP.md') },
  { label: 'GitHub', href: repoUrl },
];
