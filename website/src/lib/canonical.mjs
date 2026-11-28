// Reads facts and commands from repository files at build time, so pages cannot silently drift from them.
// Every reader throws when the expected structure is missing, which fails the build.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const repoRoot = resolve(process.cwd(), '..');
const fail = (what) => { throw new Error(`canonical content not found: ${what}`); };
export const read = (path) => readFileSync(resolve(repoRoot, path), 'utf8');

export const version = () => read('pyproject.toml').match(/^version = "([^"]+)"/m)?.[1] ?? fail('pyproject version');

/** Inline Markdown to plain text. */
const plain = (text) => text.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/\*\*|`/g, '').trim();

/** Lines under the first heading whose text starts with `heading`, up to the next heading of the same or higher level. */
function section(path, heading) {
  const lines = read(path).split('\n');
  let fenced = false;
  const headings = lines.map((line) => {
    if (line.startsWith('```')) fenced = !fenced;
    return !fenced && /^#+ /.test(line) ? line.match(/^#+/)[0].length : 0;
  });
  const start = lines.findIndex((line, i) => headings[i] && line.replace(/^#+ /, '').startsWith(heading));
  if (start < 0) fail(`${path} heading "${heading}"`);
  const end = headings.findIndex((level, i) => i > start && level && level <= headings[start]);
  return lines.slice(start + 1, end < 0 ? undefined : end);
}

/** The n-th fenced code block under a heading, without trailing explanatory comments. */
export function codeBlock(path, heading, n = 0) {
  const blocks = [...section(path, heading).join('\n').matchAll(/^```\w*\n([\s\S]*?)^```/gm)].map((m) => m[1].trimEnd());
  return blocks[n]?.replace(/[ \t]{2,}# .*$/gm, '') ?? fail(`${path} code block ${n} under "${heading}"`);
}

/** Selected lines of a block; each prefix must match exactly one line. */
export function pick(block, ...prefixes) {
  return prefixes.map((prefix) => {
    const found = block.split('\n').filter((line) => line.startsWith(prefix));
    return found.length === 1 ? found[0] : fail(`one command starting "${prefix}"`);
  }).join('\n');
}

export function bullets(path, heading) {
  const found = section(path, heading).filter((l) => l.startsWith('- ')).map((l) => plain(l.slice(2)));
  return found.length ? found : fail(`${path} bullets under "${heading}"`);
}

export const paragraph = (path, heading) =>
  plain(section(path, heading).find((l) => l.trim() && !l.startsWith('-')) ?? fail(`${path} text under "${heading}"`));

const tableRows = (lines) =>
  lines.filter((l) => l.startsWith('|') && !/^\|[-| :]+\|$/.test(l)).map((l) => l.slice(1, -1).split('|').map(plain));

export function autonomy() {
  const rows = tableRows(section('VISION.md', 'Autonomy axis'))
    .filter((cells) => /^A\d$/.test(cells[0]))
    // The status cell is "label[; condition]"; decision-register references are internal and not shown.
    .map(([id, meaning, cell]) => ({ id, meaning, status: cell.replace(/\s*\(OD-\d+\)/g, '').split('; ')[0] }));
  return rows.length === 5 ? rows : fail('VISION autonomy table');
}

/** Research track identifiers and titles only. */
export function researchTracks() {
  const rows = tableRows(section('docs/research/RESEARCH_AGENDA.md', '2. Eight Research Tracks'))
    .filter((cells) => /^R0\d$/.test(cells[0])).map(([id, title]) => ({ id, title }));
  return rows.length === 8 ? rows : fail('research track table');
}
