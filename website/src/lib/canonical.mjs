// Reads facts from the repository at build time. The reader throws when the structure is missing, which fails the build.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const repoRoot = resolve(process.cwd(), '..');
const fail = (what) => { throw new Error(`canonical content not found: ${what}`); };

export const version = () =>
  readFileSync(resolve(repoRoot, 'pyproject.toml'), 'utf8').match(/^version = "([^"]+)"/m)?.[1] ?? fail('pyproject version');
