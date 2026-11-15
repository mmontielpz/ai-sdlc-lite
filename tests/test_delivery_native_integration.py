"""Delivery executor + native Git adapter integration. Disposable local repositories only."""
import copy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ai_sdlc import delivery as d
from ai_sdlc import native_git as ng
from ai_sdlc.delivery_executor import Executor

IDENTITY = ('Native Test', 'native@example.invalid')
OPS = ('create_branch', 'stage', 'commit')


class SimpleJournal:
    def __init__(self):
        self.values = {}

    def read(self, key):
        return self.values.get(key)

    def write(self, key, value):
        self.values[key] = value


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        (root / 'journal').mkdir(mode=0o700)
        self.jpath = root / 'journal' / 'native.jsonl'
        env = patch.dict(os.environ, {'PATH': os.defpath, 'HOME': self.tmp.name}, clear=True)
        env.start()
        self.addCleanup(env.stop)
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
        self.native = []
        self.native_answer = True
        self.journals = []

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def approve(self, intent):
        self.approvals.append(intent)
        return intent['operation'] not in self.denied

    def authorize(self, intent):
        self.native.append(intent)
        return 'native-auth-%d' % len(self.native) if self.native_answer is True else self.native_answer

    def journal(self):
        # One open writer at a time (the journal is exclusively locked); reopen after close.
        if self.journals and self.journals[-1].fd is not None:
            return self.journals[-1]
        journal = ng.Journal(self.jpath, self.request['repository'], self.repo)
        self.journals.append(journal)
        self.addCleanup(journal.close)
        return journal

    def adapter(self, journal=None, allow=OPS, authorizer='default', branch='feature/test'):
        authorizer = self.authorize if authorizer == 'default' else authorizer
        return ng.GitAdapter(self.repo, self.request['repository'], branch, IDENTITY, journal or self.journal(),
                             authorizer=authorizer, allow=allow)

    def executor(self, adapter=None, plan=None, attempt=1, approve=None):
        return Executor(self.repo, plan or self.plan, approve or self.approve, SimpleJournal(), None,
                        git_adapter=adapter or self.adapter(), attempt=attempt)

    def rejected(self, call, code):
        with self.assertRaisesRegex(d.Rejected, '^' + code + '$'):
            call()

    def reopen(self):
        self.journals[-1].close()
        return self.adapter(journal=self.journal())

    def lose_end(self, journal, operation):
        real = journal.append

        def append(event, **kw):
            if event == 'end' and kw['operation_id'].endswith(operation + '-a1'):
                raise RuntimeError('simulated crash')
            return real(event, **kw)
        return patch.object(journal, 'append', append)

    def crash_before(self, adapter, command):
        real = adapter._run

        def run(*argv, **kw):
            if argv[0] == command:
                raise RuntimeError('simulated crash')
            return real(*argv, **kw)
        return patch.object(adapter, '_run', run)

    def foreign_commit(self, message):
        """Move the branch to a commit with exactly these message bytes (`git commit` would re-encode invalid UTF-8)."""
        body = (b'tree ' + self.git('write-tree').strip().encode() + b'\nparent ' + self.base.encode()
                + b'\nauthor O <o@example.invalid> 1700000000 +0000\ncommitter O <o@example.invalid> 1700000000 +0000\n\n'
                + message)
        sha = subprocess.run(['git', '-C', str(self.repo), 'hash-object', '-t', 'commit', '-w', '--stdin', '--literally'],
                             input=body, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout.decode().strip()
        self.git('update-ref', 'refs/heads/feature/test', sha)
        return sha

    def test_pending_commit_with_undecodable_foreign_commit_blocks_the_executor(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'commit'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()  # the stage applied; the commit never ran
        commit_id = self.plan['digest'] + '-commit-a1'
        sha = self.foreign_commit(b'Change a \xe9\n')
        fresh = self.reopen()
        approvals, intents = len(self.approvals), len(self.native)
        self.rejected(self.executor(fresh).commit, 'RECOVERY_AMBIGUOUS')
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))  # nothing asked, nothing replayed
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        self.assertEqual(self.journals[-1].unresolved(), [commit_id])
        self.assertEqual(self.journals[-1].verify()['entries'], len(self.journals[-1].entries))

    def test_unresolved_journal_with_malformed_head_preserves_journal_and_makes_no_mutations(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'commit'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        commit_id = self.plan['digest'] + '-commit-a1'
        (self.repo / '.git' / 'HEAD').write_bytes(b'ref: refs/heads/caf\xe9\n')
        fresh = self.reopen()
        approvals, intents = len(self.approvals), len(self.native)
        self.rejected(self.executor(fresh).commit, 'RECOVERY_AMBIGUOUS')
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(self.git('rev-parse', 'refs/heads/feature/test').strip(), self.base)
        self.assertEqual(self.git('diff', '--cached', '--name-only').strip(), 'a.txt')
        self.assertEqual(self.journals[-1].unresolved(), [commit_id])
        self.assertEqual(self.journals[-1].verify()['entries'], len(self.journals[-1].entries))

    def test_unresolved_journal_with_valid_utf8_non_ascii_head_preserves_journal_and_makes_no_mutations(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'commit'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        commit_id = self.plan['digest'] + '-commit-a1'
        ref = 'refs/heads/café'.encode('utf-8')
        subprocess.run(['git', '-C', str(self.repo), 'update-ref', ref, self.base], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'symbolic-ref', 'HEAD', ref], check=True)
        fresh = self.reopen()
        approvals, intents = len(self.approvals), len(self.native)
        self.rejected(self.executor(fresh).commit, 'JOURNAL_INVALID')
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(self.git('rev-parse', 'refs/heads/feature/test').strip(), self.base)
        self.assertEqual(self.git('diff', '--cached', '--name-only').strip(), 'a.txt')
        self.assertEqual(self.journals[-1].unresolved(), [commit_id])
        self.assertEqual(self.journals[-1].verify()['entries'], len(self.journals[-1].entries))

    def test_unresolved_journal_with_malformed_ref_file_rejects_without_mutation(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'commit'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        commit_id = self.plan['digest'] + '-commit-a1'
        ref = self.repo / '.git' / 'refs' / 'heads' / 'feature' / 'test'
        index_before = (self.repo / '.git' / 'index').read_bytes()
        ref.write_bytes(b'bad\xe9\n')
        fresh = self.reopen()
        approvals, intents = len(self.approvals), len(self.native)
        self.rejected(self.executor(fresh).commit, 'RECOVERY_AMBIGUOUS')
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(ref.read_bytes(), b'bad\xe9\n')
        self.assertEqual((self.repo / '.git' / 'index').read_bytes(), index_before)
        self.assertEqual(self.journals[-1].unresolved(), [commit_id])
        self.assertEqual(self.journals[-1].verify()['entries'], len(self.journals[-1].entries))

    # ---- Approved operations ----
    def test_approved_stage_and_commit_run_through_the_adapter(self):
        sha = self.executor().commit()
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        self.assertEqual(self.git('rev-parse', 'HEAD^').strip(), self.base)
        self.assertEqual(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').split(), ['a.txt'])
        self.assertEqual(self.git('log', '-1', '--format=%s').strip(), 'Change a')
        self.assertEqual(self.git('log', '-1', '--format=%an <%ae>').strip(), 'Native Test <native@example.invalid>')
        self.assertEqual(self.git('status', '--porcelain'), '')
        # Both layers authorize each mutation independently, bound to the plan and the exact operation.
        self.assertEqual([a['operation'] for a in self.approvals], ['stage', 'commit'])
        self.assertTrue(all(a['plan_digest'] == self.plan['digest'] for a in self.approvals))
        self.assertEqual([i['operation'] for i in self.native], ['stage', 'commit'])
        self.assertEqual(self.native[1]['params']['message'], 'Change a')
        digest = self.plan['digest']
        journal = self.journals[0]
        self.assertEqual([e['operation_id'] for e in journal.entries if e['event'] == 'begin'],
                         [digest + '-stage-a1', digest + '-commit-a1'])
        self.assertEqual([e['authorization_id'] for e in journal.entries if e['event'] == 'begin'],
                         ['native-auth-1', 'native-auth-2'])
        self.assertEqual([e['event'] for e in journal.entries], ['header', 'begin', 'end', 'begin', 'end'])
        self.assertEqual(journal.verify()['entries'], 5)

    def test_approved_branch_creation_then_delivery_on_the_new_branch(self):
        adapter = self.adapter()
        created = adapter.create_branch('host-branch-1', 'feature/native', self.base)
        self.assertEqual(created['status'], 'APPLIED')
        request = copy.deepcopy(self.request)
        request.update(expected_branch='feature/native')
        request['remote']['expected_ref'] = 'refs/heads/feature/native'
        plan, _ = d.plan(self.repo, request)
        sha = self.executor(adapter, plan).commit()
        self.assertEqual(self.git('branch', '--show-current').strip(), 'feature/native')
        self.assertEqual(self.git('rev-parse', 'feature/native').strip(), sha)
        self.assertEqual(self.git('rev-parse', 'feature/test').strip(), self.base)
        self.assertEqual([e['event'] for e in self.journals[0].entries], ['header'] + ['begin', 'end'] * 3)

    # ---- Authorization ----
    def test_executor_approval_denial_never_reaches_the_adapter(self):
        for operation in ('stage', 'commit'):
            self.denied = {operation}
            self.rejected(self.executor(self.adapter(journal=self.reuse())).commit, 'APPROVAL_REQUIRED')
        # The commit-denied run staged under approval; the stage-denied run did not.
        self.assertEqual([i['operation'] for i in self.native], ['stage'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def reuse(self):
        if self.journals:
            self.journals[-1].close()
        return self.journal()

    def test_adapter_authorization_is_independent_and_not_implied(self):
        self.native_answer = None
        self.rejected(self.executor().commit, 'AUTHORIZATION_DENIED')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual([a['operation'] for a in self.approvals], ['stage'])  # executor approval did not authorize the adapter
        self.assertEqual([e['reason'] for e in self.journals[0].entries if e['event'] == 'denied'], ['AUTHORIZATION_DENIED'])
        silent = ng.GitAdapter(self.repo, self.request['repository'], 'feature/test', IDENTITY, self.reuse(), allow=OPS)
        self.rejected(self.executor(silent).commit, 'AUTHORIZATION_UNAVAILABLE')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    def test_adapter_allowlist_denial_after_stage_allows_explicit_resume(self):
        self.rejected(self.executor(self.adapter(allow=('stage',))).commit, 'OPERATION_NOT_ALLOWED')
        self.assertEqual(self.git('diff', '--cached', '--name-only').split(), ['a.txt'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        fresh = self.adapter(journal=self.reuse())
        sha = self.executor(fresh).commit()
        self.assertEqual(self.git('rev-parse', 'HEAD^').strip(), self.base)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        # Stage was already applied: resumed without a second stage approval or authorization.
        self.assertEqual([i['operation'] for i in self.native], ['stage', 'commit'])
        # The executor re-approved the commit it had already approved; stage was not re-approved.
        self.assertEqual([a['operation'] for a in self.approvals], ['stage', 'commit', 'commit'])

    # ---- Idempotence and recovery ----
    def test_duplicate_execution_replays_without_new_effects(self):
        sha = self.executor().commit()
        approvals, intents = len(self.approvals), len(self.native)
        fresh = self.reopen()
        self.assertEqual(self.executor(fresh).commit(), sha)
        self.assertEqual(self.executor(fresh).commit(), sha)
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(self.git('rev-list', '--count', 'HEAD').strip(), '2')
        self.assertEqual(len([e for e in self.journals[-1].entries if e['event'] == 'begin']), 2)

    def test_interrupted_commit_is_reconciled_not_repeated(self):
        adapter = self.adapter()
        with self.lose_end(adapter.journal, 'commit'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        crashed = self.git('rev-parse', 'HEAD').strip()
        self.assertNotEqual(crashed, self.base)
        approvals, intents = len(self.approvals), len(self.native)
        fresh = self.reopen()
        self.assertEqual(self.executor(fresh).commit(), crashed)
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(self.git('rev-list', '--count', 'HEAD').strip(), '2')
        self.assertEqual(self.journals[-1].entries[-1]['status'], 'RECONCILED_APPLIED')
        self.assertEqual(self.journals[-1].unresolved(), [])

    def test_interrupted_stage_recovers_then_needs_explicit_new_attempt(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'add'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        fresh = self.reopen()
        self.rejected(self.executor(fresh).commit, 'OPERATION_NOT_APPLIED')
        self.assertEqual(self.journals[-1].entries[-1]['status'], 'RECONCILED_NOT_APPLIED')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        # No automatic retry; an owner-chosen new attempt uses new operation ids and fresh approvals.
        sha = self.executor(fresh, attempt=2).commit()
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        ids = [e['operation_id'] for e in self.journals[-1].entries if e['event'] == 'begin']
        self.assertEqual(ids[-2:], [self.plan['digest'] + '-stage-a2', self.plan['digest'] + '-commit-a2'])

    def test_ambiguous_recovery_blocks_everything(self):
        adapter = self.adapter()
        with self.crash_before(adapter, 'add'):
            with self.assertRaises(RuntimeError):
                self.executor(adapter).commit()
        (self.repo / 'surprise.txt').write_text('x')
        self.git('add', 'surprise.txt')
        fresh = self.reopen()
        approvals, intents = len(self.approvals), len(self.native)
        self.rejected(self.executor(fresh).commit, 'RECOVERY_AMBIGUOUS')
        self.rejected(self.executor(fresh, attempt=2).commit, 'RECOVERY_AMBIGUOUS')
        self.assertEqual((len(self.approvals), len(self.native)), (approvals, intents))
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        self.assertEqual(self.git('diff', '--cached', '--name-only').split(), ['surprise.txt'])

    def test_unobservable_stage_outcome_is_reconciled_then_delivery_resumes(self):
        adapter = self.adapter()
        real = adapter._run
        state = {'lost': False}

        def run(*argv, **kw):
            if state['lost']:
                raise d.Rejected('GIT_OUTCOME_UNKNOWN')  # Git can no longer be observed
            if argv[0] == 'add':
                real(*argv, **kw)  # the add applies ...
                state['lost'] = True
                raise d.Rejected('GIT_OUTCOME_UNKNOWN')  # ... but its outcome is lost
            return real(*argv, **kw)
        with patch.object(adapter, '_run', run):
            self.rejected(self.executor(adapter).commit, 'GIT_OUTCOME_UNKNOWN')
        journal = self.journals[0]
        stage_id = self.plan['digest'] + '-stage-a1'
        self.assertEqual((journal.operation(stage_id)[0], journal.unresolved()), ('pending', [stage_id]))
        self.assertEqual(self.git('diff', '--cached', '--name-only').split(), ['a.txt'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        # A later executor reconciles by observation, resumes at commit and never repeats the stage.
        sha = self.executor(adapter).commit()
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        self.assertEqual(self.git('rev-parse', 'HEAD^').strip(), self.base)
        self.assertEqual([a['operation'] for a in self.approvals], ['stage', 'commit'])
        self.assertEqual([i['operation'] for i in self.native], ['stage', 'commit'])
        self.assertEqual(journal.unresolved(), [])

    def test_failed_git_operation_is_not_retried(self):
        # An untracked, ignored file makes `git add` fail after approval.
        self.git('checkout', '--', 'a.txt')
        (self.repo / '.gitignore').write_text('ignored.txt\n')
        self.git('add', '.gitignore')
        self.git('commit', '-m', 'ignore rules')
        (self.repo / 'ignored.txt').write_text('x')
        head = self.git('rev-parse', 'HEAD').strip()
        request = copy.deepcopy(self.request)
        request.update(base_sha=head, head_sha=head, authorized_files=['ignored.txt'])
        plan, _ = d.plan(self.repo, request)
        calls = []
        adapter = self.adapter()
        real = adapter._run

        def spy(*argv, **kw):
            calls.append(argv[0])
            return real(*argv, **kw)
        with patch.object(adapter, '_run', spy):
            self.rejected(self.executor(adapter, plan).commit, 'GIT_FAILED')
            adds, approvals = calls.count('add'), len(self.approvals)
            self.rejected(self.executor(adapter, plan).commit, 'OPERATION_ID_REUSED')
        self.assertEqual((adds, calls.count('add')), (1, 1))
        self.assertEqual(len(self.approvals), approvals)  # refused before any new approval
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), head)
        end = [e for e in self.journals[0].entries if e['event'] == 'end'][-1]
        self.assertEqual((end['result'], end['detail']), ('failed', 'GIT_FAILED'))

    # ---- Corruption and drift ----
    def test_journal_corruption_is_detected_before_any_mutation(self):
        executor = self.executor()
        with open(self.jpath, 'ab') as stream:
            stream.write(b'{"forged":true}\n')
        self.rejected(executor.commit, 'JOURNAL_INVALID')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual((self.approvals, self.native), ([], []))

    def test_tampered_journal_cannot_be_reopened(self):
        self.executor().commit()
        self.journals[0].close()
        data = self.jpath.read_bytes()
        self.jpath.write_bytes(data.replace(b'"applied"', b'"failed"', 1))
        with self.assertRaises(d.Rejected):
            ng.Journal(self.jpath, self.request['repository'], self.repo)

    def test_repository_drift_is_rejected_before_and_between_approvals(self):
        (self.repo / 'a.txt').write_text('drift')
        self.rejected(self.executor().commit, 'SNAPSHOT_CHANGED')
        self.assertEqual((self.approvals, self.native), ([], []))
        (self.repo / 'a.txt').write_text('after')

        def drift(intent):
            self.approvals.append(intent)
            (self.repo / 'a.txt').write_text('changed during approval')
            return True
        self.rejected(self.executor(self.reuse_adapter(), approve=drift).commit, 'SNAPSHOT_CHANGED')
        self.assertEqual(self.native, [])
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        (self.repo / 'a.txt').write_text('after')

        def native_drift(intent):
            self.native.append(intent)
            (self.repo / 'a.txt').write_text('changed during native approval')
            return 'native-auth-x'
        adapter = self.adapter(journal=self.reuse(), authorizer=native_drift)
        self.rejected(self.executor(adapter).commit, 'FILE_INTEGRITY_FAILED')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def reuse_adapter(self):
        return self.adapter(journal=self.reuse())

    def test_staged_drift_between_stage_and_commit_is_rejected(self):
        def approve(intent):
            self.approvals.append(intent)
            if intent['operation'] == 'commit':
                (self.repo / 'x.txt').write_text('x')
                self.git('add', 'x.txt')
            return True
        self.rejected(self.executor(approve=approve).commit, 'SNAPSHOT_CHANGED')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    # ---- Wiring and boundaries ----
    def test_adapter_must_match_repository_branch_and_type(self):
        other = Path(self.tmp.name) / 'other'
        other.mkdir()
        mismatches = (
            ng.GitAdapter(self.repo, 'https://example.invalid/x/y', 'feature/test', IDENTITY,
                          ng.Journal(self.jpath.with_name('a.jsonl'), 'https://example.invalid/x/y', self.repo), allow=OPS),
            ng.GitAdapter(self.repo, self.request['repository'], 'other-branch', IDENTITY,
                          ng.Journal(self.jpath.with_name('b.jsonl'), self.request['repository'], self.repo), allow=OPS),
            ng.GitAdapter(other, self.request['repository'], 'feature/test', IDENTITY,
                          ng.Journal(self.jpath.with_name('c.jsonl'), self.request['repository'], other), allow=OPS),
        )
        for adapter in mismatches:
            adapter.journal.close()
            self.rejected(lambda a=adapter: self.executor(a), 'ADAPTER_MISMATCH')

        class Fake:
            repo, repository, branch = self.repo, self.request['repository'], 'feature/test'
        self.rejected(lambda: self.executor(Fake()), 'INVALID_ADAPTER')
        for attempt in (0, 10, '1', 1.0, True):
            self.rejected(lambda a=attempt: self.executor(self.reuse_adapter(), attempt=a), 'INVALID_ADAPTER')
        # A planned deletion cannot be executed by the adapter and must not degrade silently.
        (self.repo / 'a.txt').unlink()
        deleting, _ = d.plan(self.repo, self.request)
        self.assertIsNone(deleting['authorized_state']['a.txt'])
        self.rejected(lambda: self.executor(self.reuse_adapter(), deleting), 'ADAPTER_UNSUPPORTED_DELETION')

    def test_executor_runs_no_mutating_git_itself_when_an_adapter_is_injected(self):
        seen = []
        real = Executor._git

        def spy(self, *args):
            seen.append(args[0])
            return real(self, *args)
        with patch.object(Executor, '_git', spy):
            self.executor().commit()
        self.assertTrue(seen)
        self.assertFalse({'add', 'commit', 'switch', 'checkout', 'reset', 'push', 'fetch', 'update-ref'} & set(seen))

    def test_no_remote_effects_without_a_remote_double(self):
        self.rejected(self.executor().push, 'REMOTE_UNAVAILABLE')
        self.rejected(self.executor().pull_request, 'REMOTE_UNAVAILABLE')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        self.assertEqual((self.approvals, self.native), ([], []))

    def test_default_path_without_adapter_is_unchanged(self):
        executor = Executor(self.repo, self.plan, self.approve, SimpleJournal())
        self.assertIsNone(executor.git_adapter)
        sha = executor.commit()
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), sha)
        self.assertEqual([a['operation'] for a in self.approvals], ['stage', 'commit'])


if __name__ == '__main__':
    unittest.main()
