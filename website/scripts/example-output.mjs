// Runs examples/first-five-minutes in a temporary repository with this checkout's verifier and
// returns the two `verify --format summary` outputs. `node scripts/example-output.mjs --write` updates src/data/.
import { execFileSync, spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const repo = resolve(import.meta.dirname, '../..');
const verifier = join(repo, 'scripts/verify_scope.py');

export function exampleOutput() {
  const tmp = mkdtempSync(join(tmpdir(), 'ai-sdlc-example-'));
  try {
    const work = join(tmp, 'repo');
    const env = { ...process.env, PYTHONDONTWRITEBYTECODE: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1' };
    const run = (command, args, options = {}) => execFileSync(command, args, { env, encoding: 'utf8', ...options });
    const git = (...args) => run('git', ['-C', work, '-c', 'user.name=Example User', '-c', 'user.email=example@example.invalid', ...args]);
    cpSync(join(repo, 'examples/first-five-minutes'), work, { recursive: true, filter: (p) => !p.includes('__pycache__') });
    git('init', '-q');
    git('add', '.');
    git('commit', '-q', '-m', 'Initial baseline');
    const record = join(tmp, 'baseline.json');
    run('python3', ['-B', verifier, 'baseline', '--repo', work, '--out', record]);
    const greeter = join(work, 'src/greeter.py');
    writeFileSync(greeter, readFileSync(greeter, 'utf8').replace('name.strip()', '(name or "").strip()'));
    const tests = spawnSync('python3', ['-B', '-m', 'unittest', 'discover', '-s', 'tests'], { cwd: work, env, encoding: 'utf8' });
    if (tests.status !== 0) throw new Error(`example tests failed: ${tests.stderr}`);
    writeFileSync(join(tmp, 'out.txt'), tests.stdout + tests.stderr);
    const sha = JSON.parse(readFileSync(record, 'utf8')).baseline_sha;
    return Object.fromEntries(['pass', 'blocked'].map((name) => {
      const result = JSON.parse(readFileSync(join(work, `result.${name}.json`), 'utf8'));
      const target = join(tmp, `result.${name}.json`);
      writeFileSync(target, JSON.stringify({ ...result, baseline_sha: sha }));
      const done = spawnSync('python3', ['-B', verifier, 'verify', '--repo', work, '--result', target, '--baseline-record', record, '--format', 'summary'],
        { env, encoding: 'utf8' });
      const expected = name === 'pass' ? 0 : 2;
      if (done.status !== expected) throw new Error(`example ${name}: exit ${done.status}\n${done.stdout}${done.stderr}`);
      return [name, done.stdout];
    }));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

if (process.argv.includes('--write')) {
  for (const [name, output] of Object.entries(exampleOutput())) writeFileSync(join(repo, `website/src/data/verify-${name}.txt`), output);
}
