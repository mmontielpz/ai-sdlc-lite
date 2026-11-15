"""Focused CLI tests for `ai-sdlc delivery execute` (disposable repositories only)."""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_sdlc import delivery as d
from ai_sdlc import native_git as ng

ROOT = Path(__file__).resolve().parents[1]


class _TtyInput(io.StringIO):
    def isatty(self):
        return True


class DeliveryExecuteCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name).resolve()
        self.repo = base / 'repo'
        self.meta = base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir(mode=0o700)
        self._env = mock.patch.dict(os.environ, {'PATH': os.defpath, 'HOME': str(base)}, clear=True)
        self._env.start()
        self.addCleanup(self._env.stop)

        self.git('init', '-b', 'feature/exec')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', 'https://example.invalid/o/r.git')
        (self.repo / 'a.txt').write_text('before\n', encoding='utf-8')
        self.git('add', 'a.txt')
        self.git('commit', '-m', 'baseline')
        self.base_sha = self.git('rev-parse', 'HEAD').strip()

        (self.repo / 'a.txt').write_text('after\n', encoding='utf-8')
        self.request = {
            'repository': 'https://example.invalid/o/r',
            'expected_branch': 'feature/exec',
            'base_sha': self.base_sha,
            'head_sha': self.base_sha,
            'authorized_files': ['a.txt'],
            'operations': ['commit'],
            'commit': {'message': 'Bounded local change', 'signing': 'forbidden'},
            'remote': {
                'name': 'origin',
                'destination': 'https://example.invalid/o/r.git',
                'expected_ref': 'refs/heads/feature/exec',
                'expected_sha': None,
            },
            'pull_request': {'title': 'Bounded local change', 'body': '', 'base': 'master', 'draft': True},
            'required_ci': [],
            'authorization_ref': 'HUMAN-APPROVED',
            'executor': 'cli',
            'retry': {'max_attempts': 1, 'backoff_seconds': 0},
        }
        self.req_path = self.meta / 'request.json'
        self.req_path.write_text(json.dumps(self.request), encoding='utf-8')
        plan, _ = d.plan(self.repo, self.request)
        self.plan = plan
        self.plan_path = self.meta / 'plan.json'
        self.plan_path.write_text(json.dumps(plan), encoding='utf-8')
        self.journal_path = self.meta / 'journal.jsonl'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def run_execute(self, stdin_obj=None, extra=(), journal=None, plan=None, author='Owner', email='owner@example.invalid'):
        jpath = str(self.journal_path if journal is None else journal)
        ppath = str(self.plan_path if plan is None else plan)
        argv = [
            'execute',
            '--repo', str(self.repo),
            '--input', ppath,
            '--journal', jpath,
            '--author-name', author,
            '--author-email', email,
            *extra,
        ]
        out, err = io.StringIO(), io.StringIO()
        in_stream = stdin_obj if stdin_obj is not None else io.StringIO('YES\n')
        with mock.patch.object(sys, 'stdin', in_stream), \
             contextlib.redirect_stdout(out), \
             contextlib.redirect_stderr(err):
            code = d.main(argv)
        return code, json.loads(out.getvalue()), err.getvalue()

    def test_valid_approved_local_commit_and_journal(self):
        code, payload, err = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload['status'], 'COMMITTED')
        self.assertEqual(payload['mutations'], 'LOCAL_COMMIT_ONLY')
        self.assertIn('Type YES to approve local commit:', err)
        head = self.git('rev-parse', 'HEAD').strip()
        self.assertEqual(payload['commit_sha'], head)
        self.assertNotEqual(head, self.base_sha)
        msg = self.git('show', '-s', '--format=%B', head)
        self.assertIn('Bounded local change', msg)
        self.assertIn(ng.PROVENANCE_TRAILER + ':', msg)
        self.assertTrue(self.journal_path.is_file())
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_noninteractive_missing_negative_and_json_only_rejected(self):
        # Non-interactive stdin even with YES\n
        code, payload, _ = self.run_execute(io.StringIO('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['NON_INTERACTIVE_APPROVAL_REQUIRED'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)
        self.assertFalse(self.journal_path.exists())

        # Empty / EOF on TTY
        code, payload, _ = self.run_execute(_TtyInput(''))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['APPROVAL_DENIED'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)

        # Negative or lowercase confirmation on TTY
        for reply in ('no\n', 'yes\n', 'y\n'):
            code, payload, _ = self.run_execute(_TtyInput(reply))
            self.assertEqual(code, 2)
            self.assertEqual(payload['reasons'], ['APPROVAL_DENIED'])
            self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)

    def test_missing_or_invalid_sealed_plan_and_remote_ops_rejected(self):
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), plan=self.meta / 'missing.json')
        self.assertEqual(code, 3)

        bad_plan = dict(self.plan, digest='0' * 64)
        bad_path = self.meta / 'bad_plan.json'
        bad_path.write_text(json.dumps(bad_plan), encoding='utf-8')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), plan=bad_path)
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['DIGEST_MISMATCH'])

        remote_req = dict(self.request, operations=['commit', 'push'])
        remote_plan, _ = d.plan(self.repo, remote_req)
        remote_path = self.meta / 'remote_plan.json'
        remote_path.write_text(json.dumps(remote_plan), encoding='utf-8')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), plan=remote_path)
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['PREFLIGHT_NOT_READY'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)

    def test_journal_custody_and_collision_rejected(self):
        # Inside repo
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), journal=self.repo / 'j.jsonl')
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['JOURNAL_INSIDE_REPOSITORY'])

        # Missing parent directory
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), journal=self.meta / 'missing' / 'j.jsonl')
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['JOURNAL_PATH_INVALID'])

        # Symlink journal
        sym = self.meta / 'sym.jsonl'
        sym.symlink_to(self.meta / 'real.jsonl')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), journal=sym)
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['JOURNAL_PATH_INVALID'])

        # Existing journal from a different repository
        other_repo = self.meta / 'other_repo'
        other_repo.mkdir()
        with ng.Journal(self.journal_path, 'https://example.invalid/other/repo', other_repo):
            pass
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['JOURNAL_REPOSITORY_MISMATCH'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)

    def test_head_branch_dirty_and_protected_path_changes_rejected(self):
        # Dirty/unrelated file added after plan
        (self.repo / 'unrelated.txt').write_text('oops\n', encoding='utf-8')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['SNAPSHOT_CHANGED'])
        (self.repo / 'unrelated.txt').unlink()

        # Protected .gitattributes added
        (self.repo / '.gitattributes').write_text('* text=auto\n', encoding='utf-8')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertIn(payload['reasons'][0], ('ATTRIBUTES_UNSUPPORTED', 'SNAPSHOT_CHANGED'))
        (self.repo / '.gitattributes').unlink()

        # Branch changed
        self.git('checkout', '-q', '-b', 'feature/other')
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['BRANCH_CHANGED'])
        self.git('checkout', '-q', 'feature/exec')

        # HEAD changed
        (self.repo / 'b.txt').write_text('other\n', encoding='utf-8')
        self.git('add', 'b.txt')
        self.git('commit', '-m', 'advance')
        head_after = self.git('rev-parse', 'HEAD').strip()
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['HEAD_CHANGED'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), head_after)

    def test_invalid_author_attempt_and_ambiguous_interrupted_operation(self):
        code, payload, _ = self.run_execute(_TtyInput('YES\n'), email='not-an-email')
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['INVALID_IDENTITY'])

        code, payload, _ = self.run_execute(_TtyInput('YES\n'), extra=('--attempt', '0'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['INVALID_ATTEMPT'])

        # Simulate an interrupted/ambiguous stage operation in the external journal
        intent = {
            'operation': 'stage',
            'repository': self.request['repository'],
            'params': {'files': [['a.txt', '0' * 64, False]]},
        }
        with ng.Journal(self.journal_path, self.request['repository'], self.repo) as j:
            j.append(
                'begin',
                operation_id=f"{self.plan['digest']}-stage-a1",
                operation='stage',
                intent=intent,
                intent_sha256=d.digest(intent),
                authorization_id='auth-1',
                expected={'branch': 'feature/exec', 'head_sha': self.base_sha, 'staged': []},
                expected_post={'branch': 'feature/exec', 'head_sha': self.base_sha, 'staged': [['a.txt', '0' * 64, '100644']]},
            )
        code, payload, _ = self.run_execute(_TtyInput('YES\n'))
        self.assertEqual(code, 2)
        self.assertEqual(payload['reasons'], ['OPERATION_NOT_APPLIED'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base_sha)

    def test_existing_delivery_plan_verify_report_preserved(self):
        for cmd, inp in (('plan', self.req_path), ('verify', self.plan_path), ('report', self.plan_path)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = d.main([cmd, '--repo', str(self.repo), '--input', str(inp)])
            self.assertEqual(code, 0, out.getvalue())


if __name__ == '__main__':
    unittest.main()
