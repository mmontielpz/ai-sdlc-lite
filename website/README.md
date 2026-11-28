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

- The homepage stays short. Documentation pages under `src/content/docs/docs/` summarise and link to canonical documents; do not copy those in full.
- Read at build time (`src/lib/canonical.mjs`): the version, install and verification commands from `docs/QUICKSTART.md`, example source and commands, autonomy levels, research track titles and the public roadmap. If their structure changes, the build fails.
- Other wording, including agent evidence on the installation selector and the use-case labels, is written by hand. Review it when the qualification matrix or project status changes.
- Verification excerpts come from `src/data/`. The static check reruns `examples/first-five-minutes` with this checkout's verifier and requires identical output; update with `node scripts/example-output.mjs --write` (needs Python 3 and Git).
- A copyable block must consist of lines from the quickstart or the examples. Add no command that the quickstart does not support.
- State only what the repository records. `tests/static.test.mjs` requires the limitation statements and rejects a list of unsupported claims; it cannot judge new wording.
- No operational records, analytics, external fonts or third-party requests. Add no empty pages.

## Motion

Motion is defined in `src/styles/motion.css` and started by `src/components/Motion.astro`: the mark's entrance, section reveals and one lifecycle sequence. Each runs once; nothing loops. With reduced motion, or without JavaScript, content shows in its final state.

## Checks and their limits

HTML validity uses the `html-validate:standard` preset (conformance, not style). On every page, in both themes at 360, 768 and 1280 pixels, the browser checks run axe-core (WCAG 2.x A and AA tags and best practices) and look for overflow, errors and requests outside the base path. They also exercise keyboard use of navigation, search, installation tabs and the outcome switch, copy buttons, reduced motion, the page without JavaScript, and that animations end. Performance is only bounded by a long-task limit in headless Chromium. Automated checks do not replace review with assistive technology, and other browsers are not tested.

## Hosting

Configured for a GitHub Pages project site under `/ai-sdlc-lite/`. Enabling Pages or adding a deployment needs separate authorization.
