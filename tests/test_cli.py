"""Tests for the V2 command line (ai_sdlc): verifier parity, golden regression, fail-closed and no-write gates.

Everything here is deterministic and offline. The CLI is exercised in subprocesses ("python3 -B -m ai_sdlc") so that
real stdout, stderr and exit codes are compared with the existing verifier run directly.
"""

import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / 'tests' / 'golden'
VERIFIER = ROOT / 'scripts' / 'verify_scope.py'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_tests = load('verify_scope_base_tests_for_cli', 'tests/test_verify_scope.py')
vs = base_tests.vs
git = base_tests.run


def normalise(value):
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'\b[0-9a-f]{64}\b', '<sha256>', value)
        return re.sub(r'\b[0-9a-f]{40}\b', '<sha1>', value)
    return value


def cli_env(**extra):
    env = dict(os.environ)
    env.update({'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1'})
    env.update(extra)
    return env


def run_cli(*args, cwd=None, env=None):
    done = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', *args], cwd=cwd, env=env or cli_env(),
                          capture_output=True)
    return done.returncode, done.stdout, done.stderr


def run_direct(*args, cwd=None):
    done = subprocess.run([sys.executable, '-B', str(VERIFIER), *args], cwd=cwd, env=cli_env(), capture_output=True)
    return done.returncode, done.stdout, done.stderr


def tree_digest(root):
    """Hash every file (path, size, content) and every directory name below root; detects any write or creation."""
    digest = hashlib.sha256()
    for current, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(dirs):
            digest.update(('D:' + os.path.relpath(os.path.join(current, name), root) + '\n').encode())
        for name in sorted(files):
            path = os.path.join(current, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                digest.update(('L:' + rel + '>' + os.readlink(path) + '\n').encode())
                continue
            with open(path, 'rb') as handle:
                data = handle.read()
            digest.update(('F:' + rel + ':' + str(len(data)) + ':').encode() + hashlib.sha256(data).digest())
    return digest.hexdigest()


class CliParity(base_tests.Fixture):
    def write_result(self, data):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        return path

    def both(self, *args, cwd=None):
        direct = run_direct(*args, cwd=cwd)
        via = run_cli(*args, cwd=cwd)
        self.assertEqual(via, direct, 'CLI output or exit code differs from the verifier run directly')
        return via

    def verify_args(self, data):
        return ('verify', '--repo', str(self.repo), '--result', str(self.write_result(data)))

    def test_pass_parity_exit_0(self):
        self.write('src/app.py', 'x = 2\n')
        code, out, _ = self.both(*self.verify_args(self.contract()))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['status'], 'PASS')

    def test_partial_parity_exit_1(self):
        self.write('src/app.py', 'x = 2\n')
        failing = [{'command': 'pytest', 'exit_code': 1, 'evidence': 'out.txt'}]
        code, out, _ = self.both(*self.verify_args(self.contract(verification=failing)))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)['status'], 'PARTIAL')

    def test_blocked_parity_exit_2(self):
        self.write('src/app.py', 'x = 2\n')
        self.write('docs/a.md', 'changed\n')
        code, out, _ = self.both(*self.verify_args(self.contract(modified_paths=['src/app.py', 'docs/a.md'])))
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)['status'], 'BLOCKED')

    def test_malformed_contract_and_missing_file_parity(self):
        code, _, _ = self.both(*self.verify_args({'schema': 'wrong/1'}))
        self.assertEqual(code, 2)
        code, _, _ = self.both('verify', '--repo', str(self.repo), '--result', str(self.meta / 'absent.json'))
        self.assertEqual(code, 2)

    def test_argument_errors_keep_stderr_and_exit_code(self):
        code, out, err = self.both('verify')
        self.assertEqual(code, 2)
        self.assertTrue(err)
        self.assertEqual(out, b'')

    def test_codes_parity_and_registry_shape(self):
        code, out, _ = self.both('codes')
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out))

    def test_baseline_parity_on_stdout_and_out_file(self):
        self.both('baseline', '--repo', str(self.repo))
        first, second = self.meta / 'cli.json', self.meta / 'direct.json'
        self.assertEqual(run_cli('baseline', '--repo', str(self.repo), '--out', str(first))[0], 0)
        self.assertEqual(run_direct('baseline', '--repo', str(self.repo), '--out', str(second))[0], 0)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        # an existing output file is refused, exactly like the verifier
        again = run_cli('baseline', '--repo', str(self.repo), '--out', str(first))
        self.assertEqual(again, run_direct('baseline', '--repo', str(self.repo), '--out', str(first)))
        self.assertEqual(again[0], 2)

    def test_seal_parity_uses_the_callers_working_directory(self):
        first, second = self.meta / 'm1.json', self.meta / 'm2.json'
        self.assertEqual(run_cli('seal', '--out', str(first), 'out.txt', cwd=self.meta)[0], 0)
        self.assertEqual(run_direct('seal', '--out', str(second), 'out.txt', cwd=self.meta)[0], 0)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(run_cli('seal', '--out', str(self.meta / 'm3.json'), 'nope.txt', cwd=self.meta)[0], 2)

    def test_golden_reports_through_the_cli(self):
        def report_of(args):
            code, out, _ = run_cli(*args)
            return code, normalise(json.loads(out))

        def golden(name):
            return json.loads((GOLDEN / f'{name}.json').read_text())

        self.write('src/app.py', 'x = 2\n')
        code, report = report_of(self.verify_args(self.contract()))
        self.assertEqual((code, report), (0, golden('pass')))
        failing = [{'command': 'pytest', 'exit_code': 1, 'evidence': 'out.txt'}]
        code, report = report_of(self.verify_args(self.contract(verification=failing)))
        self.assertEqual((code, report), (1, golden('partial_failed_check_false_pass')))
        code, report = report_of(self.verify_args({'schema': 'wrong/1'}))
        self.assertEqual((code, report), (2, golden('blocked_malformed_contract')))
        self.write('docs/a.md', 'x\n')
        self.write('secrets/k.txt', 'x\n')
        self.write('AGENTS.md', 'x\n')
        self.write('tests/test_app.py', 'x\n')
        (self.repo / 'src/link.py').symlink_to('app.py')
        paths = ['src/app.py', 'docs/a.md', 'secrets/k.txt', 'AGENTS.md', 'tests/test_app.py']
        code, report = report_of(self.verify_args(self.contract(modified_paths=paths)))
        self.assertEqual((code, report), (2, golden('blocked_scope_violations')))


class CliPaths(unittest.TestCase):
    def test_runs_from_outside_the_repository_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in (('codes',), ('doctor',), ('status',)):
                from_root = run_cli(*args, cwd=ROOT)
                elsewhere = run_cli(*args, cwd=tmp)
                self.assertEqual(elsewhere, from_root, args)
                self.assertEqual(elsewhere[0], 0, args)
            self.assertEqual(run_cli('codes', cwd=tmp), run_direct('codes', cwd=tmp))

    def test_missing_verifier_fails_closed_even_if_cwd_has_one(self):
        # a copy of the package whose parent has no scripts/verify_scope.py; the cwd holds a decoy verifier that
        # would print DECOY if the CLI resolved the verifier from the working directory instead of the module
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as decoy:
            shutil.copytree(ROOT / 'ai_sdlc', Path(tmp) / 'ai_sdlc', ignore=shutil.ignore_patterns('__pycache__'))
            (Path(decoy) / 'scripts').mkdir()
            (Path(decoy) / 'scripts' / 'verify_scope.py').write_text('print("DECOY")\n')
            code, out, err = run_cli('codes', cwd=decoy, env=cli_env(PYTHONPATH=tmp))
        self.assertEqual((code, out), (2, b''))
        self.assertIn(b'BLOCKED', err)
        self.assertIn(b'verifier', err)

    def test_in_process_missing_or_symlinked_verifier_is_blocked(self):
        from ai_sdlc import cli
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / 'absent.py'
            link = Path(tmp) / 'link.py'
            try:
                link.symlink_to(VERIFIER)
            except (OSError, NotImplementedError):
                link = None
            for target in (missing, link):
                if target is None:
                    continue
                err = io.StringIO()
                with mock.patch.object(cli, 'VERIFIER', target), mock.patch.object(sys, 'stderr', err):
                    self.assertEqual(cli.main(['codes']), 2)
                self.assertIn('BLOCKED', err.getvalue())

    def test_signal_or_start_failure_is_blocked(self):
        from ai_sdlc import cli
        err = io.StringIO()
        with mock.patch.object(cli.subprocess, 'run', side_effect=OSError('x')), mock.patch.object(sys, 'stderr', err):
            self.assertEqual(cli.main(['codes']), 2)
        done = subprocess.CompletedProcess([], -9)
        with mock.patch.object(cli.subprocess, 'run', return_value=done), mock.patch.object(sys, 'stderr', err):
            self.assertEqual(cli.main(['codes']), 2)

    def test_usage_and_unknown_commands(self):
        self.assertEqual(run_cli()[0], 2)
        self.assertEqual(run_cli('--help')[0], 0)
        code, out, err = run_cli('frobnicate')
        self.assertEqual((code, out), (2, b''))
        self.assertIn(b'unknown command', err)
        self.assertEqual(run_cli('doctor', 'extra')[0], 2)
        self.assertEqual(run_cli('status', '--bogus')[0], 2)


class CliDoctorAndStatus(base_tests.Fixture):
    def test_doctor_reports_unknowns_and_claims_no_enforcement(self):
        code, out, _ = run_cli('doctor')
        text = out.decode()
        self.assertEqual(code, 0)
        self.assertIn('RESULT: READY', text)
        self.assertGreaterEqual(text.count(': UNKNOWN'), 5)
        self.assertIn('sandbox and permissions: UNKNOWN', text)
        self.assertIn('enforces nothing', text)
        self.assertNotRegex(text, r'sandbox[^\n]*: OK')

    def test_doctor_without_git_is_blocked(self):
        with tempfile.TemporaryDirectory() as empty:
            code, out, _ = run_cli('doctor', env=cli_env(PATH=empty))
        self.assertEqual(code, 2)
        self.assertIn('git: FAIL', out.decode())
        self.assertIn('RESULT: BLOCKED', out.decode())

    def test_doctor_and_status_write_nothing(self):
        before = tree_digest(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            empty_before = tree_digest(tmp)
            for args in (('doctor',), ('status',), ('status', '--repo', str(self.repo))):
                run_cli(*args, cwd=tmp)
            self.assertEqual(tree_digest(tmp), empty_before)
        before_repo = tree_digest(self.repo)
        run_cli('status', '--repo', str(self.repo))
        self.assertEqual(tree_digest(self.repo), before_repo)
        self.assertEqual(tree_digest(ROOT), before)

    def test_status_reads_head_without_git(self):
        with tempfile.TemporaryDirectory() as empty:  # no git on PATH: proves Git is not invoked
            code, out, _ = run_cli('status', '--repo', str(self.repo), env=cli_env(PATH=empty))
        text = out.decode()
        self.assertEqual(code, 0)
        self.assertIn(f'head: {self.base}', text)
        self.assertRegex(text, r'branch: (master|main)')
        self.assertIn('working tree state: UNKNOWN', text)
        self.assertIn('active task: NOT INITIALIZED', text)

    def test_status_packed_refs_detached_and_worktree(self):
        git(self.repo, 'pack-refs', '--all')
        text = run_cli('status', '--repo', str(self.repo))[1].decode()
        self.assertIn(f'head: {self.base}', text)
        git(self.repo, 'checkout', '-q', '--detach')
        text = run_cli('status', '--repo', str(self.repo))[1].decode()
        self.assertIn('branch: (detached)', text)
        self.assertIn(f'head: {self.base}', text)
        linked = self.repo.parent / 'linked'
        git(self.repo, 'worktree', 'add', '-q', '-b', 'side', str(linked))
        text = run_cli('status', '--repo', str(linked))[1].decode()
        self.assertIn('branch: side', text)
        self.assertIn(f'head: {self.base}', text)

    def test_status_not_a_repository_is_unknown_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run_cli('status', '--repo', tmp)
        self.assertEqual(code, 0)
        self.assertIn('git: UNKNOWN', out.decode())

    def test_status_task_context_pointer_and_symlink_refusal(self):
        folder = self.repo / '.ai-sdlc-lite'
        folder.mkdir()
        (folder / 'task-context.json').write_text(json.dumps(
            {'contract': 'tasks/T/TASK.md', 'checklist': 'tasks/T/CHECKLIST.md', 'result': 'tasks/T/RESULT.md'}))
        text = run_cli('status', '--repo', str(self.repo))[1].decode()
        self.assertIn('active task contract: tasks/T/TASK.md', text)
        self.assertIn('task approval: UNVERIFIED', text)
        (folder / 'task-context.json').write_text('[1]')
        self.assertIn('not a JSON object', run_cli('status', '--repo', str(self.repo))[1].decode())
        (folder / 'task-context.json').unlink()
        (folder / 'target.json').write_text('{}')
        try:
            (folder / 'task-context.json').symlink_to('target.json')
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        self.assertIn('symlink; not read', run_cli('status', '--repo', str(self.repo))[1].decode())


CANARY = 'CANARY-SECRET-7f3a91'


class CliGitMetadata(base_tests.Fixture):
    """Repository Git metadata is untrusted: crafted HEAD, refs, pointer files and commondir must never make
    `status` read or print anything outside the validated Git directory. Synthetic fixtures, harmless canaries."""

    def setUp(self):
        super().setUp()
        self.sandbox = self.meta / 'sandbox'
        self.sandbox.mkdir()
        # canaries at every location a traversal could plausibly reach
        self.canary_files = []
        for place in (self.sandbox, self.sandbox / 'evil', self.sandbox / 'evil' / '.git',
                      self.sandbox / 'evil' / '.git' / 'refs', self.sandbox / 'outside'):
            place.mkdir(parents=True, exist_ok=True)
            for name in ('canary.txt', 'HEAD', 'packed-refs', 'main'):
                path = place / name
                if not path.exists():
                    path.write_text(f'{CANARY} more words\n')
                    self.canary_files.append(path)
        self.evil = self.sandbox / 'evil'
        (self.evil / '.git' / 'objects').mkdir(exist_ok=True)  # structurally a Git directory; HEAD is set per test

    def status(self, repo, **env):
        return run_cli('status', '--repo', str(repo), env=cli_env(**env) if env else None)

    def assert_contained(self, repo, expect=None, **env):
        before = tree_digest(self.sandbox)
        code, out, err = self.status(repo, **env)
        self.assertEqual(code, 0, err)
        text = (out + err).decode()
        self.assertNotIn(CANARY, text, 'file contents leaked')
        self.assertNotIn('more words', text)
        self.assertEqual(tree_digest(self.sandbox), before, 'status wrote something')
        for needle in expect or ():
            self.assertIn(needle, text)
        return text

    def head(self, text, ref_file_text=None):
        (self.evil / '.git' / 'HEAD').write_text(text)

    def test_the_original_traversal_exploit_is_contained(self):
        self.head('ref: ../../canary.txt\n')
        text = self.assert_contained(self.evil, expect=['branch: UNKNOWN', 'head: UNKNOWN'])
        self.assertNotIn('canary.txt', text)

    def test_unsafe_symbolic_refs_are_rejected(self):
        bad = ['../../canary.txt', '/etc/passwd', '/tmp/x', 'refs/../../../canary.txt', 'refs/heads/../../../canary.txt',
               'refs//heads/main', 'refs/heads/', 'refs/heads/./main', 'refs/heads/.hidden', 'refs\\heads\\main',
               'refs/heads/a b', 'refs/heads/a:b', 'refs/heads/a*b', 'refs/heads/a?b', 'refs/heads/a[b', 'refs/heads/a^b',
               'refs/heads/a~1', 'refs/heads/main.lock', 'refs/heads/a@{1}', 'heads/main', 'main', 'refs', 'refs/',
               'refs/heads/\x01evil', 'refs/heads/' + 'a' * 300, 'C:\\canary.txt', '~/canary.txt', '$HOME/x']
        for ref in bad:
            with self.subTest(ref=ref):
                self.head(f'ref: {ref}\n')
                text = self.assert_contained(self.evil, expect=['branch: UNKNOWN', 'head: UNKNOWN'])
                self.assertNotIn('canary', text.lower())

    def test_malformed_head_contents_are_unknown(self):
        for content in ('', '\n', 'ref:', 'ref: ', 'ref:\n', f'{CANARY}\n', f'ref {CANARY}\n', 'garbage here\n',
                        'ref: refs/heads/main extra\n', 'ref: refs/heads/ma\x00in\n', '\x00\x01\x02', '"quoted"',
                        'gitdir: ../canary.txt\n'):
            with self.subTest(content=content):
                self.head(content)
                self.assert_contained(self.evil, expect=['branch: UNKNOWN', 'head: UNKNOWN'])

    def test_non_hex_and_wrong_length_object_ids_are_unknown(self):
        refs = self.evil / '.git' / 'refs' / 'heads'
        refs.mkdir(parents=True)
        self.head('ref: refs/heads/main\n')
        for content in ('z' * 40, 'g' * 64, 'A' * 40, 'a' * 39, 'a' * 41, 'a' * 63, 'a' * 65, ('a' * 40) + ' ' + CANARY,
                        CANARY, 'ref: refs/heads/other', '../../canary.txt', ''):
            with self.subTest(content=content):
                (refs / 'main').write_text(content + '\n')
                self.assert_contained(self.evil, expect=['branch: main', 'head: UNKNOWN'])
        for content in ('z' * 40, 'a' * 39, ('a' * 40) + 'x'):
            with self.subTest(detached=content):
                self.head(content + '\n')
                self.assert_contained(self.evil, expect=['branch: UNKNOWN', 'head: UNKNOWN'])
        (refs / 'main').unlink()
        (self.evil / '.git' / 'packed-refs').write_text(f'# pack-refs\n{"z" * 40} refs/heads/main\n')
        self.head('ref: refs/heads/main\n')
        self.assert_contained(self.evil, expect=['head: UNKNOWN'])
        (self.evil / '.git' / 'packed-refs').write_text(f'{CANARY} refs/heads/main\n{"a" * 40} refs/heads/main extra\n')
        self.assert_contained(self.evil, expect=['head: UNKNOWN'])

    def test_valid_detached_head_and_loose_and_packed_refs_still_work(self):
        good, other = 'a' * 40, 'b' * 64
        self.head(good + '\n')
        self.assert_contained(self.evil, expect=['branch: (detached)', f'head: {good}'])
        self.head(other + '\n')
        self.assert_contained(self.evil, expect=['branch: (detached)', f'head: {other}'])
        self.head('ref: refs/heads/feature/x-1\n')
        loose = self.evil / '.git' / 'refs' / 'heads' / 'feature'
        loose.mkdir(parents=True)
        (loose / 'x-1').write_text(good + '\n')
        self.assert_contained(self.evil, expect=['branch: feature/x-1', f'head: {good}'])
        (loose / 'x-1').unlink()
        (self.evil / '.git' / 'packed-refs').write_text(f'# pack-refs with: peeled\n{other} refs/heads/feature/x-1\n^{good}\n')
        self.assert_contained(self.evil, expect=['branch: feature/x-1', f'head: {other}'])

    def test_symlink_escapes_are_not_followed(self):
        canary = self.sandbox / 'outside' / 'canary.txt'
        git_dir = self.evil / '.git'
        (git_dir / 'refs' / 'heads').mkdir(parents=True)
        # final component symlink
        self.head('ref: refs/heads/main\n')
        link = git_dir / 'refs' / 'heads' / 'main'
        try:
            link.symlink_to(canary)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        self.assert_contained(self.evil, expect=['head: UNKNOWN'])
        link.unlink()
        # intermediate directory symlink
        (git_dir / 'refs' / 'heads').rmdir()
        (git_dir / 'refs' / 'heads').symlink_to(self.sandbox / 'outside', target_is_directory=True)
        (self.sandbox / 'outside' / 'main').write_text(f'{CANARY}\n')
        self.assert_contained(self.evil, expect=['head: UNKNOWN'])
        (git_dir / 'refs' / 'heads').unlink()
        # HEAD itself a symlink
        (git_dir / 'HEAD').unlink()
        (git_dir / 'HEAD').symlink_to(canary)
        self.assert_contained(self.evil, expect=['git: UNKNOWN'])
        (git_dir / 'HEAD').unlink()
        (git_dir / 'HEAD').write_text('ref: refs/heads/main\n')
        # packed-refs symlink
        (git_dir / 'packed-refs').unlink()
        (git_dir / 'packed-refs').symlink_to(canary)
        self.assert_contained(self.evil, expect=['head: UNKNOWN'])

    def test_symlinked_git_directory_and_task_context_are_refused(self):
        real = self.sandbox / 'realgit'
        real.mkdir()
        (real / 'HEAD').write_text('ref: refs/heads/main\n')
        (real / 'objects').mkdir()
        repo = self.sandbox / 'viasymlink'
        repo.mkdir()
        try:
            (repo / '.git').symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        self.assert_contained(repo, expect=['git: UNKNOWN'])
        folder = self.evil / '.ai-sdlc-lite'
        folder.mkdir()
        (folder / 'task-context.json').symlink_to(self.sandbox / 'outside' / 'canary.txt')
        self.assert_contained(self.evil, expect=['symlink; not read'])

    def test_malicious_git_pointer_files_are_rejected(self):
        repo = self.sandbox / 'pointer'
        repo.mkdir()
        target_dir = self.sandbox / 'outside'
        (target_dir / 'HEAD').write_text('ref: refs/heads/main\n')  # a HEAD, but not a Git directory (no objects/)
        for content in ('gitdir: ../outside\n', f'gitdir: {target_dir}\n', 'gitdir: /\n', 'gitdir: /etc\n',
                        f'gitdir: {self.sandbox}/outside/canary.txt\n', 'gitdir:\n', 'gitdir: \n', 'garbage\n',
                        f'{CANARY}\n', 'gitdir: ../outside\x00x\n', 'gitdir: ../out\x1bside\n', '\x00\x00', ''):
            with self.subTest(content=content):
                (repo / '.git').write_text(content)
                self.assert_contained(repo, expect=['git: UNKNOWN'])

    def test_legitimate_git_pointer_separate_git_dir_works(self):
        outside = self.sandbox / 'separate-git'
        repo = self.sandbox / 'work'
        git(self.sandbox, 'init', '-q', '--separate-git-dir', str(outside), str(repo))
        git(repo, 'commit', '-q', '--allow-empty', '-m', 'c')
        oid = git(repo, 'rev-parse', 'HEAD')
        self.assertTrue((repo / '.git').is_file())
        self.assert_contained(repo, expect=[f'head: {oid}'])

    def test_malicious_commondir_is_rejected(self):
        main = self.sandbox / 'mainrepo'
        git(self.sandbox, 'init', '-q', str(main))
        git(main, 'commit', '-q', '--allow-empty', '-m', 'c')
        linked = self.sandbox / 'linked'
        git(main, 'worktree', 'add', '-q', '-b', 'side', str(linked))
        entry = main / '.git' / 'worktrees' / 'linked'
        victim = self.sandbox / 'outside'
        (victim / 'objects').mkdir(exist_ok=True)
        (victim / 'refs' / 'heads').mkdir(parents=True, exist_ok=True)
        (victim / 'refs' / 'heads' / 'side').write_text(f'{CANARY}\n')
        (victim / 'packed-refs').write_text(f'{CANARY} refs/heads/side\n')
        original = (entry / 'commondir').read_text()
        for content in ('../../../outside\n', f'{victim}\n', '/\n', '..\n', '.\n', '../..//x\n', f'{CANARY}\n', ''):
            with self.subTest(commondir=content):
                (entry / 'commondir').write_text(content)
                self.assert_contained(linked, expect=['git: UNKNOWN'])
        (entry / 'commondir').write_text(original)
        # a back-link that does not name this worktree is also refused
        original_back = (entry / 'gitdir').read_text()
        (entry / 'gitdir').write_text(str(victim / '.git') + '\n')
        self.assert_contained(linked, expect=['git: UNKNOWN'])
        (entry / 'gitdir').write_text(original_back)
        # and the untouched layout works
        self.assert_contained(linked, expect=['branch: side', 'head: ' + git(main, 'rev-parse', 'HEAD')])

    def test_commondir_in_a_plain_git_directory_is_refused(self):
        self.head('ref: refs/heads/main\n')
        (self.evil / '.git' / 'commondir').write_text('../../outside\n')
        self.assert_contained(self.evil, expect=['git: UNKNOWN'])

    def test_valid_repository_outside_the_framework_checkout_and_linked_worktree(self):
        repo = self.sandbox / 'real'
        git(self.sandbox, 'init', '-q', str(repo))
        git(repo, 'commit', '-q', '--allow-empty', '-m', 'c')
        oid = git(repo, 'rev-parse', 'HEAD')
        self.assertFalse(str(repo).startswith(str(ROOT)))
        self.assert_contained(repo, expect=[f'head: {oid}', 'working tree state: UNKNOWN'])
        git(repo, 'pack-refs', '--all')
        self.assert_contained(repo, expect=[f'head: {oid}'])
        git(repo, 'worktree', 'add', '-q', '-b', 'wt', str(self.sandbox / 'wt'))
        self.assert_contained(self.sandbox / 'wt', expect=['branch: wt', f'head: {oid}'])
        git(repo, 'checkout', '-q', '--detach')
        self.assert_contained(repo, expect=['branch: (detached)', f'head: {oid}'])

    def test_untrusted_task_context_values_are_not_echoed_unsafely(self):
        folder = self.evil / '.ai-sdlc-lite'
        folder.mkdir()
        (self.evil / '.git' / 'HEAD').write_text('ref: refs/heads/main\n')
        record = {'contract': '../../canary.txt', 'checklist': '/etc/passwd', 'result': 'a/\x1b[31mred'}
        (folder / 'task-context.json').write_text(json.dumps(record))
        text = self.assert_contained(self.evil)
        self.assertNotIn('\x1b', text)
        self.assertNotIn('/etc/passwd', text)
        self.assertEqual(text.count('active task contract: UNKNOWN'), 1)
        self.assertIn('active task checklist: UNKNOWN', text)
        self.assertIn('active task result: UNKNOWN', text)

    def test_status_executes_no_repository_defined_program(self):
        marker = self.sandbox / 'EXECUTED'
        script = self.sandbox / 'hook.sh'
        script.write_text(f'#!/bin/sh\ntouch {marker}\n')
        script.chmod(0o755)
        repo = self.sandbox / 'hostile'
        git(self.sandbox, 'init', '-q', str(repo))
        git(repo, 'commit', '-q', '--allow-empty', '-m', 'c')
        config = repo / '.git' / 'config'
        config.write_text(config.read_text() + f'[core]\n\tfsmonitor = {script}\n\thooksPath = {self.sandbox}\n')
        hooks = repo / '.git' / 'hooks'
        hooks.mkdir(exist_ok=True)
        (hooks / 'reference-transaction').write_text(f'#!/bin/sh\ntouch {marker}\n')
        (hooks / 'reference-transaction').chmod(0o755)
        with tempfile.TemporaryDirectory() as empty:  # no git on PATH at all
            self.assert_contained(repo, expect=['head: '], PATH=empty)
        self.assertFalse(marker.exists(), 'a repository-defined program ran')

    def test_validators_unit_table(self):
        from ai_sdlc import cli
        self.assertTrue(cli._oid_ok('0' * 40) and cli._oid_ok('f' * 64))
        for bad in ('', 'F' * 40, 'f' * 41, 'g' * 40, None, 5, ' ' + 'a' * 39, 'a' * 39 + '\n'):
            self.assertFalse(cli._oid_ok(bad), repr(bad))
        for good in ('refs/heads/main', 'refs/heads/feature/x-1', 'refs/tags/v1.0', 'refs/remotes/origin/main'):
            self.assertTrue(cli._ref_ok(good), good)
        for bad in ('', None, 'refs', '/refs/heads/x', 'refs/heads/../x', 'refs/heads//x', 'refs/heads/x/'):
            self.assertFalse(cli._ref_ok(bad), repr(bad))
        self.assertIsNone(cli._read_regular(self.sandbox, '..', 'x'))
        self.assertIsNone(cli._read_regular(self.sandbox, 'a/b'))
        self.assertIsNone(cli._read_regular(self.sandbox, 'evil'))  # a directory, not a regular file
        self.assertIsNone(cli._read_regular(self.sandbox))


class CliSourceGuards(unittest.TestCase):
    FILES = ('__init__.py', '__main__.py', 'cli.py')
    STDLIB = {'json', 'os', 'stat', 'subprocess', 'sys', 'pathlib', 'shutil', '__future__', 'ai_sdlc'}

    def trees(self, **kwargs):
        for name in self.FILES:
            path = ROOT / 'ai_sdlc' / name
            yield name, ast.parse(path.read_text(encoding='utf-8'), filename=str(path), **kwargs)

    def test_python_39_syntax(self):
        for _, tree in self.trees(feature_version=(3, 9)):
            self.assertIsNotNone(tree)

    def test_standard_library_only_and_no_network_modules(self):
        for name, tree in self.trees():
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name.split('.')[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    modules = [(node.module or '').split('.')[0]]
                for module in modules:
                    self.assertIn(module, self.STDLIB, f'{name} imports {module}')
        text = (ROOT / 'ai_sdlc' / 'cli.py').read_text(encoding='utf-8')
        for banned in ('socket', 'urllib', 'http', 'ssl'):
            self.assertNotRegex(text, rf'^\s*(import|from)\s+{banned}\b', banned)

    def test_verifier_is_invoked_with_current_interpreter_and_bytecode_off(self):
        text = (ROOT / 'ai_sdlc' / 'cli.py').read_text(encoding='utf-8')
        self.assertIn("[sys.executable, '-B', str(VERIFIER), command, *rest]", text)

    def test_verifier_logic_is_not_duplicated(self):
        text = (ROOT / 'ai_sdlc' / 'cli.py').read_text(encoding='utf-8')
        for marker in ('ai-sdlc-lite-result/1', 'out_of_scope_modification', 'allowed_paths'):
            self.assertNotIn(marker, text)


if __name__ == '__main__':
    unittest.main()
