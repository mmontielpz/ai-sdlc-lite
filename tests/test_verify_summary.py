"""Targeted tests for `ai-sdlc verify --format summary|json` and summary formatting."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_scope', ROOT / 'scripts' / 'verify_scope.py')
vs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vs)


def git(cwd, *args):
    return subprocess.run(
        ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_ai_sdlc(*args):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT)
    return subprocess.run(
        [sys.executable, '-B', '-m', 'ai_sdlc', *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class VerifySummaryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name).resolve()
        self.repo = base / 'repo'
        self.meta = base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir()
        git(self.repo, 'init', '-q')
        for rel, content in {
            'src/app.py': 'x = 1\n',
            'secrets/k.txt': 'k\n',
        }.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', 'base')
        self.base = git(self.repo, 'rev-parse', 'HEAD')
        (self.meta / 'out.txt').write_text('ok\n', encoding='utf-8')

    def write_repo(self, rel, content):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def write_result(self, payload, name='result.json'):
        path = self.meta / name
        path.write_text(json.dumps(payload), encoding='utf-8')
        return path

    def base_contract(self, **overrides):
        data = {
            'schema': vs.CONTRACT_SCHEMA,
            'task_id': 'SUMMARY-1',
            'baseline_sha': self.base,
            'baseline_dirty_paths': [],
            'allowed_paths': ['src/**'],
            'protected_paths': ['secrets/**'],
            'modified_paths': ['src/app.py'],
            'claimed_status': 'PASS',
            'verification': [{'command': 'python3 -m unittest', 'exit_code': 0, 'evidence': 'out.txt'}],
        }
        data.update(overrides)
        return data

    def test_default_and_explicit_json_output_unchanged_and_pass_summary(self):
        self.write_repo('src/app.py', 'x = 2\n')
        result_path = self.write_result(self.base_contract())
        out_path = self.meta / 'report.json'

        default_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path))
        explicit_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path), '--format', 'json')
        summary_res = run_ai_sdlc(
            'verify', '--repo', str(self.repo), '--result', str(result_path),
            '--format', 'summary', '--out', str(out_path),
        )

        self.assertEqual(default_res.returncode, 0)
        self.assertEqual(explicit_res.returncode, 0)
        self.assertEqual(summary_res.returncode, 0)
        self.assertEqual(default_res.stdout, explicit_res.stdout)

        parsed = json.loads(default_res.stdout)
        self.assertEqual(parsed['status'], 'PASS')
        self.assertEqual(out_path.read_text(encoding='utf-8'), default_res.stdout)

        self.assertIn('Status: PASS (computed: PASS, claimed: PASS)', summary_res.stdout)
        self.assertIn('Task: SUMMARY-1', summary_res.stdout)
        self.assertIn('src/app.py', summary_res.stdout)
        self.assertIn('Evidence: 1 file(s)', summary_res.stdout)
        self.assertIn('Failure reasons: none', summary_res.stdout)
        self.assertIn('Guidance: none', summary_res.stdout)

    def test_partial_summary_and_exit_code(self):
        self.write_repo('src/app.py', 'x = 2\n')
        result_path = self.write_result(
            self.base_contract(
                claimed_status='PARTIAL',
                verification=[{'command': 'python3 -m unittest', 'exit_code': 1, 'evidence': 'out.txt'}],
            )
        )
        default_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path))
        summary_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path), '--format', 'summary')

        self.assertEqual(default_res.returncode, 1)
        self.assertEqual(summary_res.returncode, 1)
        self.assertIn('Status: PARTIAL (computed: PARTIAL, claimed: PARTIAL)', summary_res.stdout)
        self.assertIn('[PARTIAL] check_failed:', summary_res.stdout)
        self.assertIn('Guidance:', summary_res.stdout)

    def test_blocked_out_of_scope_and_protected_path(self):
        self.write_repo('secrets/k.txt', 'changed\n')
        result_path = self.write_result(self.base_contract(modified_paths=['secrets/k.txt']))
        default_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path))
        summary_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path), '--format', 'summary')

        self.assertEqual(default_res.returncode, 2)
        self.assertEqual(summary_res.returncode, 2)
        self.assertIn('Status: BLOCKED (computed: BLOCKED, claimed: PASS)', summary_res.stdout)
        self.assertIn('secrets/k.txt', summary_res.stdout)
        self.assertIn('[BLOCKED] protected_path_modified:', summary_res.stdout)
        self.assertIn('[BLOCKED] false_pass:', summary_res.stdout)

    def test_missing_evidence_summary(self):
        self.write_repo('src/app.py', 'x = 2\n')
        result_path = self.write_result(
            self.base_contract(
                verification=[{'command': 'python3 -m unittest', 'exit_code': 0, 'evidence': 'missing.txt'}],
            )
        )
        summary_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(result_path), '--format', 'summary')

        self.assertEqual(summary_res.returncode, 2)
        self.assertIn('Status: BLOCKED', summary_res.stdout)
        self.assertIn('[BLOCKED] missing_evidence:', summary_res.stdout)
        self.assertIn('Evidence: 0 file(s)', summary_res.stdout)

    def test_invalid_result_contract_and_unknown_claimed_status(self):
        bad_json = self.meta / 'bad.json'
        bad_json.write_text('{not valid json', encoding='utf-8')
        bad_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(bad_json), '--format', 'summary')
        self.assertEqual(bad_res.returncode, 2)
        self.assertIn('Status: BLOCKED', bad_res.stdout)
        self.assertIn('[BLOCKED] verification_error:', bad_res.stdout)
        self.assertIn('Modified paths: unavailable', bad_res.stdout)
        self.assertIn('Evidence: unavailable', bad_res.stdout)

        unknown_claim = self.write_result(self.base_contract(claimed_status='UNKNOWN'), name='unknown_claim.json')
        claim_res = run_ai_sdlc('verify', '--repo', str(self.repo), '--result', str(unknown_claim), '--format', 'summary')
        self.assertEqual(claim_res.returncode, 2)
        self.assertIn('Status: BLOCKED', claim_res.stdout)
        self.assertIn('[BLOCKED] verification_error:', claim_res.stdout)

    def test_unknown_report_status_never_downgraded_or_upgraded(self):
        unknown_summary = vs.format_summary({'status': 'UNKNOWN', 'failure_reasons': []})
        self.assertIn('Status: UNKNOWN', unknown_summary)
        self.assertNotIn('Status: PASS', unknown_summary)
        self.assertIn('Guidance:', unknown_summary)

        missing_summary = vs.format_summary({})
        self.assertIn('Status: UNKNOWN', missing_summary)
        self.assertNotIn('Status: PASS', missing_summary)

    def test_untrusted_output_escaping(self):
        evil_report = {
            'status': 'BLOCKED',
            'computed_status': 'BLOCKED',
            'claimed_status': 'PASS',
            'task_id': 'T\x1b[31m1\nFAKE',
            'modified_paths': ['src/\x1b[31mevil\u202efile.py', 'src/line\nbreak.py'],
            'evidence': [{'ref': 'out\r\n.txt', 'integrity': 'unchecked'}],
            'trust': {'hash_integrity': 'none'},
            'failure_reasons': [{
                'severity': 'BLOCKED',
                'code': 'out_of_scope_modification',
                'detail': 'bad\x1b[2Jpath\u202e\nStatus: PASS',
            }],
            'recovery': {'guidance': ['Fix\x1b[0m path\nnow']},
        }
        rendered = vs.format_summary(evil_report)
        self.assertNotIn('\x1b', rendered)
        self.assertNotIn('\r', rendered)
        self.assertNotIn('\u202e', rendered)
        self.assertTrue(rendered.startswith('Status: BLOCKED'))
        self.assertNotIn('\nStatus: PASS', rendered)
        self.assertIn('\\x1b[31mevil\\u202efile.py', rendered)
        self.assertIn('src/line\\nbreak.py', rendered)
        self.assertIn('bad\\x1b[2Jpath\\u202e\\nStatus: PASS', rendered)


if __name__ == '__main__':
    unittest.main()
