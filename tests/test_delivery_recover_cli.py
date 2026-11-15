"""Focused CLI tests for `ai-sdlc delivery recover` (disposable repositories only)."""

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


class DeliveryRecoverCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.repo = self.base / 'repo'
        self.meta = self.base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir(mode=0o700)
        self._env = mock.patch.dict(os.environ, {'PATH': os.defpath, 'HOME': str(self.base)}, clear=True)
        self._env.start()
        self.addCleanup(self._env.stop)

        self.git('init', '-b', 'feature/recover')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', 'https://example.invalid/o/r.git')
        (self.repo / 'a.txt').write_text('before\n', encoding='utf-8')
        self.git('add', 'a.txt')
        self.git('commit', '-m', 'baseline')
        self.base_sha = self.git('rev-parse', 'HEAD').strip()

        self.repository_id = 'https://example.invalid/o/r'
        self.branch = 'feature/recover'
        self.journal_path = self.meta / 'journal.jsonl'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def snapshot_git(self):
        return {
            'head': self.git('rev-parse', 'HEAD').strip(),
            'branch': self.git('rev-parse', '--abbrev-ref', 'HEAD').strip(),
            'status': self.git('status', '--porcelain'),
            'count': self.git('rev-list', '--all', '--count').strip(),
        }

    def run_recover(self, journal=None, repository=None, branch=None, repo=None):
        argv = [
            'recover',
            '--repo', str(self.repo if repo is None else repo),
            '--journal', str(self.journal_path if journal is None else journal),
            '--repository', self.repository_id if repository is None else repository,
            '--branch', self.branch if branch is None else branch,
        ]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = d.main(argv)
        return code, json.loads(out.getvalue()), err.getvalue()

    def _file_entry(self, path):
        import hashlib
        digest = hashlib.sha256((self.repo / path).read_bytes()).hexdigest()
        return [path, digest, False]

    def _observed_staged(self):
        with ng.Journal(self.meta / 'obs.jsonl', self.repository_id, self.repo) as j:
            obs = ng.GitAdapter(self.repo, self.repository_id, self.branch, ('t', 't@example.invalid'), j).observe()
        (self.meta / 'obs.jsonl').unlink()
        return obs['staged']

    def _begin_commit_op(self, op_id='op-1', staged=(), message='Bounded change', expected_post=None):
        msg_sha = ng.sha(message)
        staged_list = list(staged)
        files = [self._file_entry('a.txt')]
        intent = {
            'operation': 'commit',
            'repository': self.repository_id,
            'params': {
                'message_sha256': msg_sha,
                'message_length': len(message),
                'files': files,
            },
        }
        expected = {
            'branch': self.branch,
            'head_sha': self.base_sha,
            'staged': staged_list,
        }
        if expected_post is None:
            expected_post = {
                'provenance': '0123456789abcdef' * 4,
                'parent': self.base_sha,
                'message_sha256': msg_sha,
                'files': files,
            }
        with ng.Journal(self.journal_path, self.repository_id, self.repo) as journal:
            journal.append(
                'begin',
                operation_id=op_id,
                operation='commit',
                intent=intent,
                intent_sha256=d.digest(intent),
                authorization_id='HUMAN-APPROVED',
                expected=expected,
                expected_post=expected_post,
            )

    def test_valid_completed_journal(self):
        (self.repo / 'a.txt').write_text('after\n', encoding='utf-8')
        request = {
            'repository': self.repository_id,
            'expected_branch': self.branch,
            'base_sha': self.base_sha,
            'head_sha': self.base_sha,
            'authorized_files': ['a.txt'],
            'operations': ['commit'],
            'commit': {'message': 'Bounded local change', 'signing': 'forbidden'},
            'remote': {
                'name': 'origin',
                'destination': 'https://example.invalid/o/r.git',
                'expected_ref': f'refs/heads/{self.branch}',
                'expected_sha': None,
            },
            'pull_request': {'title': 'Bounded local change', 'body': '', 'base': 'master', 'draft': True},
            'required_ci': [],
            'authorization_ref': 'HUMAN-APPROVED',
            'executor': 'cli',
            'retry': {'max_attempts': 1, 'backoff_seconds': 0},
        }
        plan, _ = d.plan(self.repo, request)
        plan_path = self.meta / 'plan.json'
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, 'stdin', _TtyInput('YES\n')), \
             contextlib.redirect_stdout(out), \
             contextlib.redirect_stderr(err):
            exec_code = d.main([
                'execute', '--repo', str(self.repo), '--input', str(plan_path),
                '--journal', str(self.journal_path), '--author-name', 'Owner',
                '--author-email', 'owner@example.invalid',
            ])
        self.assertEqual(exec_code, 0, err.getvalue())

        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 0)
        self.assertEqual(payload['status'], 'RECONCILED')
        self.assertEqual(payload['pending_before'], [])
        self.assertEqual(payload['reconciled'], {})
        self.assertEqual(payload['pending'], [])
        self.assertEqual(payload['unresolved'], [])
        self.assertFalse(payload['journal_appended'])
        self.assertEqual(payload['mutations'], 'NONE')
        self.assertEqual(self.snapshot_git(), before)

    def test_interrupted_stage_reconciled_as_applied(self):
        (self.repo / 'a.txt').write_text('staged\n', encoding='utf-8')
        self.git('add', 'a.txt')
        staged_obs = self._observed_staged()
        intent = {'operation': 'stage', 'repository': self.repository_id, 'params': {'files': [self._file_entry('a.txt')]}}
        with ng.Journal(self.journal_path, self.repository_id, self.repo) as journal:
            journal.append(
                'begin',
                operation_id='op-stage-1',
                operation='stage',
                intent=intent,
                intent_sha256=d.digest(intent),
                authorization_id='HUMAN-APPROVED',
                expected={'branch': self.branch, 'head_sha': self.base_sha, 'staged': []},
                expected_post={'branch': self.branch, 'head_sha': self.base_sha, 'staged': staged_obs},
            )
        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 0)
        self.assertEqual(payload['status'], 'RECONCILED')
        self.assertEqual(payload['pending_before'], ['op-stage-1'])
        self.assertEqual(payload['reconciled'], {'op-stage-1': 'RECONCILED_APPLIED'})
        self.assertEqual(payload['pending'], [])
        self.assertEqual(payload['unresolved'], [])
        self.assertTrue(payload['journal_appended'])
        self.assertEqual(payload['mutations'], 'NONE')
        self.assertEqual(self.snapshot_git(), before)

    def test_interrupted_commit_reconciled_as_not_applied(self):
        (self.repo / 'a.txt').write_text('staged\n', encoding='utf-8')
        self.git('add', 'a.txt')
        staged_obs = self._observed_staged()
        self._begin_commit_op(op_id='op-commit-not-applied', staged=staged_obs)
        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 0)
        self.assertEqual(payload['status'], 'RECONCILED')
        self.assertEqual(payload['reconciled'], {'op-commit-not-applied': 'RECONCILED_NOT_APPLIED'})
        self.assertEqual(payload['unresolved'], [])
        self.assertTrue(payload['journal_appended'])
        self.assertEqual(payload['mutations'], 'NONE')
        self.assertEqual(self.snapshot_git(), before)

    def test_ambiguous_operation_returns_partial_exit_1(self):
        # Expected staged entry, but working tree/index has nothing staged and HEAD unchanged.
        fake_staged = [['a.txt', '0' * 64, '100644']]
        self._begin_commit_op(op_id='op-ambig', staged=fake_staged)
        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 1)
        self.assertEqual(payload['status'], 'PARTIAL')
        self.assertEqual(payload['reconciled'], {'op-ambig': 'AMBIGUOUS'})
        self.assertEqual(payload['unresolved'], ['op-ambig'])
        self.assertTrue(payload['journal_appended'])
        self.assertEqual(payload['mutations'], 'NONE')
        self.assertEqual(self.snapshot_git(), before)

    def test_tampered_hash_chain_rejected(self):
        self._begin_commit_op(op_id='op-tamper')
        lines = self.journal_path.read_text(encoding='utf-8').splitlines()
        entry = json.loads(lines[-1])
        entry['operation_id'] = 'op-tampered'
        lines[-1] = json.dumps(entry, sort_keys=True)
        self.journal_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_INVALID'])
        self.assertEqual(payload['mutations'], 'NONE')
        self.assertEqual(self.snapshot_git(), before)

    def test_missing_journal_rejected_and_creates_no_file(self):
        missing = self.meta / 'missing-journal.jsonl'
        self.assertFalse(missing.exists())
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(journal=missing)
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_MISSING'])
        self.assertFalse(missing.exists())
        self.assertEqual(self.snapshot_git(), before)

    def test_empty_journal_rejected(self):
        empty = self.meta / 'empty.jsonl'
        empty.write_text('', encoding='utf-8')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(journal=empty)
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_INVALID'])
        self.assertEqual(self.snapshot_git(), before)

    def test_symlink_journal_rejected(self):
        self._begin_commit_op(op_id='op-sym')
        link = self.meta / 'journal-link.jsonl'
        link.symlink_to(self.journal_path)
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(journal=link)
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_PATH_INVALID'])
        self.assertEqual(self.snapshot_git(), before)

    def test_journal_inside_repository_rejected(self):
        inside = self.repo / 'journal.jsonl'
        inside.write_text('{"seq":0}\n', encoding='utf-8')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(journal=inside)
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_INSIDE_REPOSITORY'])
        self.assertEqual(self.snapshot_git(), before)

    def test_repository_identity_mismatch_rejected(self):
        self._begin_commit_op(op_id='op-repo-mismatch')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(repository='https://example.invalid/other/repo')
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_REPOSITORY_MISMATCH'])
        self.assertEqual(self.snapshot_git(), before)

    def test_branch_identity_and_observed_branch(self):
        (self.repo / 'a.txt').write_text('staged\n', encoding='utf-8')
        self.git('add', 'a.txt')
        self._begin_commit_op(op_id='op-branch')
        self.git('checkout', '-b', 'other/branch')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(branch=self.branch)
        self.assertEqual(code, 1)
        self.assertEqual(payload['status'], 'PARTIAL')
        self.assertEqual(payload['expected_branch'], self.branch)
        self.assertEqual(payload['observed_branch'], 'other/branch')
        self.assertEqual(payload['unresolved'], ['op-branch'])
        self.assertEqual(self.snapshot_git(), before)

        bad_code, bad_payload, _ = self.run_recover(branch='bad branch')
        self.assertEqual(bad_code, 2)
        self.assertEqual(bad_payload['status'], 'BLOCKED')
        self.assertEqual(bad_payload['reasons'], ['INVALID_BRANCH'])
        self.assertEqual(self.snapshot_git(), before)

    def test_head_changed_after_interruption(self):
        self._begin_commit_op(op_id='op-head-moved')
        (self.repo / 'b.txt').write_text('unrelated\n', encoding='utf-8')
        self.git('add', 'b.txt')
        self.git('commit', '-m', 'Unrelated commit')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover()
        self.assertEqual(code, 1)
        self.assertEqual(payload['status'], 'PARTIAL')
        self.assertEqual(payload['reconciled'], {'op-head-moved': 'AMBIGUOUS'})
        self.assertEqual(payload['unresolved'], ['op-head-moved'])
        self.assertEqual(payload['head_sha'], before['head'])
        self.assertEqual(self.snapshot_git(), before)

    def test_repeated_recovery_appends_no_redundant_events(self):
        (self.repo / 'a.txt').write_text('staged\n', encoding='utf-8')
        self.git('add', 'a.txt')
        self._begin_commit_op(op_id='op-repeat', staged=self._observed_staged())

        code1, payload1, _ = self.run_recover()
        self.assertEqual(code1, 0)
        self.assertTrue(payload1['journal_appended'])
        entries_after_first = len(self.journal_path.read_text(encoding='utf-8').splitlines())

        code2, payload2, _ = self.run_recover()
        self.assertEqual(code2, 0)
        self.assertEqual(payload2['status'], 'RECONCILED')
        self.assertEqual(payload2['reconciled'], {})
        self.assertFalse(payload2['journal_appended'])
        self.assertEqual(len(self.journal_path.read_text(encoding='utf-8').splitlines()), entries_after_first)

    def test_malformed_journal_rejected(self):
        malformed = self.meta / 'malformed.jsonl'
        malformed.write_text('{not-json\n', encoding='utf-8')
        before = self.snapshot_git()
        code, payload, _ = self.run_recover(journal=malformed)
        self.assertEqual(code, 2)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['reasons'], ['JOURNAL_INVALID'])
        self.assertEqual(self.snapshot_git(), before)

    def test_path_substitution_create_false_and_nofollow(self):
        missing = self.meta / 'never-created.jsonl'
        with self.assertRaises(d.Rejected) as ctx:
            ng.Journal(missing, self.repository_id, self.repo, create=False)
        self.assertEqual(str(ctx.exception), 'JOURNAL_MISSING')
        self.assertFalse(missing.exists())

        self._begin_commit_op(op_id='op-nofollow')
        link = self.meta / 'race-link.jsonl'
        link.symlink_to(self.journal_path)
        with self.assertRaises(d.Rejected) as ctx2:
            ng.Journal(link, self.repository_id, self.repo, create=False)
        self.assertEqual(str(ctx2.exception), 'JOURNAL_PATH_INVALID')

    def test_existing_delivery_commands_preserved(self):
        (self.repo / 'a.txt').write_text('after\n', encoding='utf-8')
        request = {
            'repository': self.repository_id,
            'expected_branch': self.branch,
            'base_sha': self.base_sha,
            'head_sha': self.base_sha,
            'authorized_files': ['a.txt'],
            'operations': ['commit'],
            'commit': {'message': 'Bounded local change', 'signing': 'forbidden'},
            'remote': {
                'name': 'origin',
                'destination': 'https://example.invalid/o/r.git',
                'expected_ref': f'refs/heads/{self.branch}',
                'expected_sha': None,
            },
            'pull_request': {'title': 'Bounded local change', 'body': '', 'base': 'master', 'draft': True},
            'required_ci': [],
            'authorization_ref': 'HUMAN-APPROVED',
            'executor': 'cli',
            'retry': {'max_attempts': 1, 'backoff_seconds': 0},
        }
        req_path = self.meta / 'request.json'
        req_path.write_text(json.dumps(request), encoding='utf-8')
        plan_path = self.meta / 'plan.json'
        for cmd in ('plan', 'verify', 'report'):
            inp = req_path if cmd == 'plan' else plan_path
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = d.main([cmd, '--repo', str(self.repo), '--input', str(inp)])
            self.assertEqual(code, 0, err.getvalue())
            if cmd == 'plan':
                plan_path.write_text(out.getvalue(), encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
