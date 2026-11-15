"""Disposable real Git repositories; remote effects use an in-memory double."""
import ast
import copy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ai_sdlc import delivery as d
from ai_sdlc.delivery_executor import Executor


class Journal:
    def __init__(self):
        self.values = {}

    def read(self, key):
        return self.values.get(key)

    def write(self, key, value):
        self.values[key] = value


class Remote:
    def __init__(self):
        self.sha = None
        self.pr = None
        self.calls = []
        self.fail = False

    def ref(self, destination, ref):
        return self.sha

    def push(self, destination, ref, sha, expected):
        self.calls.append('push')
        if self.fail:
            raise RuntimeError('credential must never escape')
        assert self.sha == expected
        self.sha = sha

    def find_pr(self, identity):
        return self.pr

    def create_pr(self, identity):
        self.calls.append('pull_request')
        self.pr = identity


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.env = patch.dict(os.environ, {'PATH': os.defpath, 'HOME': self.tmp.name}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.git('init', '-b', 'feature/test')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', 'https://example.invalid/o/r.git')
        (self.repo / 'a.txt').write_text('before')
        self.git('add', 'a.txt')
        self.git('commit', '-m', 'baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'a.txt').write_text('after')
        self.request = dict(repository='https://example.invalid/o/r', expected_branch='feature/test',
                            base_sha=self.base, head_sha=self.base, authorized_files=['a.txt'],
                            operations=['commit', 'push', 'pull_request'],
                            commit=dict(message='Change a', signing='forbidden'),
                            remote=dict(name='origin', destination='https://example.invalid/o/r.git',
                                        expected_ref='refs/heads/feature/test', expected_sha=None),
                            pull_request=dict(title='Change a', body='', base='master', draft=True),
                            required_ci=[], authorization_ref='MISSION=test', executor='test',
                            retry=dict(max_attempts=3, backoff_seconds=0))
        self.plan, _ = d.plan(self.repo, self.request)
        self.approvals = []
        self.denied = set()
        self.journal = Journal()
        self.remote = Remote()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def approve(self, intent):
        self.approvals.append(intent)
        return intent['operation'] not in self.denied

    def executor(self):
        return Executor(self.repo, self.plan, self.approve, self.journal, self.remote)

    def rejected(self, call, code):
        with self.assertRaisesRegex(d.Rejected, '^' + code + '$'):
            call()

    def foreign_commit(self, message):
        """Move the branch to a commit with exactly these message bytes (`git commit` would re-encode invalid UTF-8)."""
        self.git('add', 'a.txt')
        body = (b'tree ' + self.git('write-tree').strip().encode() + b'\nparent ' + self.base.encode()
                + b'\nauthor O <o@example.invalid> 1700000000 +0000\ncommitter O <o@example.invalid> 1700000000 +0000\n\n'
                + message)
        sha = subprocess.run(['git', '-C', str(self.repo), 'hash-object', '-t', 'commit', '-w', '--stdin', '--literally'],
                             input=body, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout.decode().strip()
        self.git('update-ref', 'refs/heads/feature/test', sha)
        return sha

    def test_recovery_proof_with_non_utf8_commit_message_is_rejected_not_an_exception(self):
        sha = self.foreign_commit(b'Change a \xe9\n')
        shown = subprocess.run(['git', '-C', str(self.repo), 'show', '-s', '--format=%B', sha],
                               stdout=subprocess.PIPE, check=True).stdout
        with self.assertRaises(UnicodeDecodeError):  # fixture guard: Git really emits invalid UTF-8 here
            shown.decode('utf-8')
        self.rejected(self.executor().commit, 'GIT_OUTPUT_INVALID')
        self.assertEqual(self.approvals, [])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)  # nothing was changed

    def test_recovery_proof_with_valid_utf8_foreign_message_is_an_identity_mismatch(self):
        self.foreign_commit('Change a café\n'.encode('utf-8'))
        self.rejected(self.executor().commit, 'COMMIT_IDENTITY_MISMATCH')
        self.assertEqual(self.approvals, [])

    def test_malformed_ref_file_in_head_from_disk_is_rejected(self):
        ref = self.repo / '.git' / 'refs' / 'heads' / 'feature' / 'test'
        index_before = (self.repo / '.git' / 'index').read_bytes()
        ref.write_bytes(b'bad\xe9\n')
        self.rejected(self.executor().commit, 'INVALID_SHA')
        self.assertEqual(self.approvals, [])
        self.assertEqual(ref.read_bytes(), b'bad\xe9\n')
        self.assertEqual((self.repo / '.git' / 'index').read_bytes(), index_before)

    def test_valid_utf8_non_ascii_branch_in_head_rejects_commit_without_mutation(self):
        (self.repo / '.git' / 'HEAD').write_bytes('ref: refs/heads/café\n'.encode('utf-8'))
        self.rejected(self.executor().commit, 'BRANCH_CHANGED')
        self.assertEqual(self.approvals, [])
        self.assertEqual(self.git('rev-parse', 'refs/heads/feature/test').strip(), self.base)

    def test_malformed_non_utf8_head_rejects_commit_without_mutation(self):
        (self.repo / '.git' / 'HEAD').write_bytes(b'ref: refs/heads/caf\xe9\n')
        self.rejected(self.executor().commit, 'INVALID_REF')
        self.assertEqual(self.approvals, [])
        self.assertEqual(self.git('rev-parse', 'refs/heads/feature/test').strip(), self.base)

    def test_detached_head_rejects_commit_without_mutation(self):
        self.git('checkout', '--detach', self.base)
        self.rejected(self.executor().commit, 'BRANCH_CHANGED')
        self.assertEqual(self.approvals, [])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_commit_and_fresh_instance_recovery(self):
        sha = self.executor().commit()
        self.assertEqual(self.git('rev-parse', 'HEAD^').strip(), self.base)
        self.assertEqual(self.executor().commit(), sha)
        self.assertEqual([a['operation'] for a in self.approvals], ['stage', 'commit'])
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_commit_recovery_after_pack_refs_is_idempotent(self):
        sha = self.executor().commit()
        self.git('pack-refs', '--all')
        self.assertFalse((self.repo / '.git' / 'refs' / 'heads' / 'feature' / 'test').exists())
        approvals = len(self.approvals)
        self.assertEqual(self.executor().commit(), sha)
        self.assertEqual(len(self.approvals), approvals)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD').strip(), '2')

    def test_commit_recovery_with_mixed_loose_and_packed_refs_uses_loose_ref(self):
        sha = self.executor().commit()
        self.git('pack-refs', '--all')
        # Simulate a newer loose ref alongside an older packed-refs entry.
        ref = self.repo / '.git' / 'refs' / 'heads' / 'feature' / 'test'
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(sha + '\n')
        self.assertEqual(self.executor().commit(), sha)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD').strip(), '2')

    def test_each_mutation_requires_approval(self):
        for operation in ('stage', 'commit', 'push', 'pull_request'):
            self.denied = {operation}
            call = getattr(self.executor(), 'pull_request')
            self.rejected(call, 'APPROVAL_REQUIRED')
        self.assertEqual(self.remote.calls, ['push'])
        self.assertIsNone(self.remote.pr)

    def test_approval_binds_plan_sha_files_and_repository(self):
        self.executor().commit()
        for intent in self.approvals:
            self.assertEqual(intent['head_sha'], self.base)
            self.assertEqual(intent['authorized_files'], ['a.txt'])
            self.assertEqual(intent['plan_digest'], self.plan['digest'])
            self.assertEqual(intent['repository'], self.request['repository'])

    def test_snapshot_drift(self):
        (self.repo / 'a.txt').write_text('drift')
        self.rejected(self.executor().commit, 'SNAPSHOT_CHANGED')
        self.assertEqual(self.approvals, [])

    def test_unrelated_staging_refused(self):
        (self.repo / 'extra').write_text('extra')
        self.plan, _ = d.plan(self.repo, self.request)
        self.git('add', 'extra')
        self.rejected(self.executor().commit, 'INDEX_NOT_EMPTY')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_staged_bytes_rechecked_after_approval(self):
        def approve(intent):
            if intent['operation'] == 'commit':
                (self.repo / 'a.txt').write_text('evil')
                self.git('add', 'a.txt')
                (self.repo / 'a.txt').write_text('after')
            return True
        executor = Executor(self.repo, self.plan, approve, self.journal)
        self.rejected(executor.commit, 'STAGED_STATE_CHANGED')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_no_remote_retry_on_ambiguous_outcome(self):
        self.remote.fail = True
        self.rejected(self.executor().push, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.remote.fail = False
        self.rejected(self.executor().push, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.assertEqual(self.remote.calls, ['push'])

    def test_ambiguous_push_reconciles_by_exact_sha(self):
        self.remote.fail = True
        self.rejected(self.executor().push, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.remote.sha = self.git('rev-parse', 'HEAD').strip()
        self.assertEqual(self.executor().push(), self.remote.sha)
        self.assertEqual(self.remote.calls, ['push'])

    def test_remote_changed_never_pushed(self):
        self.remote.sha = 'a' * 40
        self.rejected(self.executor().push, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.assertEqual(self.remote.calls, [])

    def test_pr_identity_and_idempotence(self):
        identity = self.executor().pull_request()
        self.assertEqual(identity['head_sha'], self.git('rev-parse', 'HEAD').strip())
        self.assertEqual(self.executor().pull_request(), identity)
        self.assertEqual(self.remote.calls, ['push', 'pull_request'])
        self.remote.pr['repository'] = 'https://example.invalid/other'
        self.rejected(self.executor().pull_request, 'PR_IDENTITY_MISMATCH')

    def test_changed_head_is_not_reused(self):
        self.executor().commit()
        self.git('commit', '--allow-empty', '-m', 'other')
        self.rejected(self.executor().commit, 'COMMIT_IDENTITY_MISMATCH')

    def test_active_hooks_and_environment_blocked(self):
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text('exit 1')
        self.rejected(self.executor().commit, 'UNSAFE_GIT_HOOKS')
        hook.unlink()
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1'}):
            self.rejected(self.executor().commit, 'UNSAFE_GIT_ENVIRONMENT')

    def test_signing_and_ci_fail_closed(self):
        self.request['commit']['signing'] = 'required'
        self.plan, _ = d.plan(self.repo, self.request)
        self.rejected(self.executor().commit, 'SIGNING_UNSUPPORTED')
        self.request['commit']['signing'] = 'forbidden'
        self.request['required_ci'] = ['tests']
        self.plan, _ = d.plan(self.repo, self.request)
        self.rejected(self.executor().push, 'CI_UNSUPPORTED')

    def test_deletion_and_literal_filename(self):
        (self.repo / 'a.txt').unlink()
        (self.repo / '[new]').write_text('literal')
        self.request['authorized_files'] = ['[new]', 'a.txt']
        self.plan, _ = d.plan(self.repo, self.request)
        self.executor().commit()
        self.assertEqual(self.git('ls-files').splitlines(), ['[new]'])

    def test_attributes_blocked(self):
        (self.repo / '.gitattributes').write_text('* filter=evil')
        self.plan, _ = d.plan(self.repo, self.request)
        self.rejected(self.executor().commit, 'ATTRIBUTES_UNSUPPORTED')

    def test_plan_digest_and_authorized_state(self):
        self.plan['authorized_state']['a.txt'] = None
        self.rejected(self.executor, 'DIGEST_MISMATCH')
        self.plan['digest'] = d.digest({k: v for k, v in self.plan.items() if k != 'digest'})
        self.rejected(self.executor, 'INVALID_AUTHORIZED_STATE')

    def test_stage_approval_cannot_add_unrelated_index_entries(self):
        (self.repo / 'extra').write_text('extra')
        self.plan, _ = d.plan(self.repo, self.request)
        def approve(intent):
            self.git('add', 'extra')
            return True
        executor = Executor(self.repo, self.plan, approve, self.journal)
        self.rejected(executor.commit, 'INDEX_NOT_EMPTY')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_base_mismatch(self):
        self.request['base_sha'] = 'a' * 40
        self.plan, _ = d.plan(self.repo, self.request)
        self.rejected(self.executor().commit, 'BASE_MISMATCH')

    def test_remote_observation_error_is_sanitized(self):
        self.executor().commit()
        with patch.object(self.remote, 'ref', side_effect=RuntimeError('secret')):
            self.rejected(self.executor().push, 'REMOTE_STATE_UNKNOWN')
        self.assertEqual(self.remote.calls, [])

    def test_ambiguous_pr_is_never_recreated(self):
        with patch.object(self.remote, 'create_pr', side_effect=RuntimeError('secret')):
            self.rejected(self.executor().pull_request, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.rejected(self.executor().pull_request, 'REMOTE_OUTCOME_AMBIGUOUS')
        self.assertEqual(self.remote.calls, ['push'])

    def test_required_remote_branch_identity(self):
        self.request['remote']['expected_ref'] = 'refs/heads/other'
        self.plan, _ = d.plan(self.repo, self.request)
        self.rejected(self.executor().push, 'REMOTE_REF_MISMATCH')
        self.assertEqual(self.remote.calls, [])

    def test_no_force_merge_or_credential_command(self):
        commands = []
        executor = self.executor()
        original = executor._git
        def record(*args):
            commands.append(args)
            return original(*args)
        with patch.object(executor, '_git', side_effect=record):
            executor.pull_request()
        self.assertFalse(any(x in ('--force', '--force-with-lease', 'merge', 'credential', 'push')
                             for command in commands for x in command))

    def test_python39_syntax(self):
        ast.parse(Path(__import__('ai_sdlc.delivery_executor', fromlist=['']).__file__).read_text(), feature_version=(3, 9))


if __name__ == '__main__':
    unittest.main()
