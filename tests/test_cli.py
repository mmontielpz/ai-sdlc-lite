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


class CliSourceGuards(unittest.TestCase):
    FILES = ('__init__.py', '__main__.py', 'cli.py')
    STDLIB = {'json', 'os', 'subprocess', 'sys', 'pathlib', 'shutil', '__future__', 'ai_sdlc'}

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
