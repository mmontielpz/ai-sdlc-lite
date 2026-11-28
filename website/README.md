# Website

The official AI-SDLC Lite website: Astro with Starlight, static output. **Not deployed.** It is independent of the Python package.

## Run it

Node 24 (see `.nvmrc`).

```bash
cd website
npm ci
npm run dev                 # development server
npm run build && npm run preview   # http://127.0.0.1:4321/ai-sdlc-lite/
npm run check               # build, links and claims, HTML validity, accessibility and responsive checks
npx playwright install chromium    # once, before the browser checks
```

## Content rules

- Version, problem statement, principles, autonomy levels, roadmap status and qualification rows are read from the canonical documents at build time (`src/lib/canonical.mjs`). If their structure changes, the build fails.
- Pages that do not exist yet are linked to the canonical document on GitHub. Add no empty pages.
- State only what the repository records. `tests/static.test.mjs` requires the limitation statements and rejects a list of unsupported claims; it cannot judge new wording, so review it.
- No analytics, external fonts or third-party requests.

## Checks and their limits

HTML validity uses the `html-validate:standard` preset (conformance, not style). Accessibility uses axe-core (WCAG 2.x A and AA tags and best practices) in Chromium, in both themes, at 360, 768 and 1280 pixels. Automated checks do not replace review with assistive technology, and other browsers are not tested.

## Hosting

Configured for a GitHub Pages project site under `/ai-sdlc-lite/`. Enabling Pages or adding a deployment needs separate authorization.
