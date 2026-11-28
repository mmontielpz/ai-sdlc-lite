// Reads facts from the repository's canonical files at build time, so the site cannot silently drift from them.
// Every reader throws when the expected structure is missing, which fails the build.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export const repoRoot = resolve(process.cwd(), '..');
const read = (path) => readFileSync(resolve(repoRoot, path), 'utf8');
const fail = (what) => { throw new Error(`canonical content not found: ${what}`); };

/** Inline Markdown to plain text. */
export const plain = (text) =>
  text.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/\*\*|`|(?<![\w])_|_(?![\w])/g, '').trim();

function section(path, heading) {
  const lines = read(path).split('\n');
  const start = lines.findIndex((line) => /^#+ /.test(line) && line.replace(/^#+ /, '').startsWith(heading));
  if (start < 0) fail(`${path} heading "${heading}"`);
  const level = lines[start].match(/^#+/)[0].length;
  const end = lines.findIndex((line, i) => i > start && new RegExp(`^#{1,${level}} `).test(line));
  return lines.slice(start + 1, end < 0 ? undefined : end);
}

export function bullets(path, heading) {
  const found = section(path, heading).filter((l) => l.startsWith('- ')).map((l) => plain(l.slice(2)));
  return found.length ? found : fail(`${path} bullets under "${heading}"`);
}

export const version = () => read('pyproject.toml').match(/^version = "([^"]+)"/m)?.[1] ?? fail('pyproject version');

export const problem = () => {
  const line = read('README.md').split('\n').find((l) => l.startsWith('AI coding agents can ')) ?? fail('README problem');
  return plain(line.split('. ')[0]) + '.';
};

export const msi = () => {
  const line = read('VISION.md').split('\n').find((l) => l.startsWith('- **Engineering philosophy (MSI):**'));
  return plain((line ?? fail('VISION MSI')).split(':**')[1]);
};

const tableRows = (lines) =>
  lines.filter((l) => l.startsWith('|') && !/^\|[-| :]+\|$/.test(l)).map((l) => l.slice(1, -1).split('|').map(plain));

export function autonomy() {
  const rows = tableRows(section('VISION.md', 'Autonomy axis'))
    .filter((cells) => /^A\d$/.test(cells[0]))
    // The status cell is "label[; condition]"; decision-register references are internal and not shown.
    .map(([id, meaning, cell]) => {
      const [status, ...rest] = cell.replace(/\s*\(OD-\d+\)/g, '').split('; ');
      return { id, meaning, status, condition: rest.join('; ') };
    });
  return rows.length === 5 ? rows : fail('VISION autonomy table');
}

export function qualification() {
  const lines = section('README.md', 'Supported Agents & Observed Qualification');
  const asOf = plain(lines.find((l) => l.startsWith('_As of')) ?? fail('qualification date')).split('. Authority')[0];
  const [head, ...rows] = tableRows(lines);
  if (head?.[0] !== 'Target' || !rows.length) fail('qualification table');
  return { asOf, rows: rows.map(([target, status, evidence]) => ({ target, status, evidence })) };
}
