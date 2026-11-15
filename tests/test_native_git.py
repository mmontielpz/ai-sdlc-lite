"""Native Git adapter and journal tests. Disposable local repositories only; no network or remotes."""
import ast
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ai_sdlc import delivery as d
from ai_sdlc import native_git as ng

ID = 'https://example.invalid/org/repo'
IDENTITY = ('Native Test', 'native@example.invalid')
OPS = ('create_branch', 'stage', 'commit')


class Auth:
    def __init__(self, answer=True):
        self.intents = []
        self.answer = answer

    def __call__(self, intent):
        self.intents.append(intent)
        if self.answer is True:
            return 'auth-%d' % len(self.intents)
        return self.answer


def entry(path, data, executable=False):
    return {path: {'sha256': hashlib.sha256(data).hexdigest(), 'executable': executable}}


class NativeGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        (root / 'journal').mkdir(mode=0o700)
        self.jpath = root / 'journal' / 'j.jsonl'
        env = patch.dict(os.environ, {'PATH': os.defpath, 'HOME': self.tmp.name}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.make_repo(self.repo)
        self.journals = []

    def make_repo(self, path):
        self.git('init', '-q', '-b', 'main', cwd=path)
        (path / 'README.md').write_bytes(b'base\n')
        (path / '.gitignore').write_bytes(b'ignored.txt\n')
        self.git('add', 'README.md', '.gitignore', cwd=path)
        self.git('commit', '-q', '-m', 'base', cwd=path)

    def git(self, *args, cwd=None):
        env = {'PATH': os.defpath, 'HOME': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
               'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
               'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        result = subprocess.run(['git', '-C', str(cwd or self.repo), *args], env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
        return result.stdout.decode().strip()

    def journal(self, path=None, root=None, **kw):
        journal = ng.Journal(path or self.jpath, ID, root or self.repo, **kw)
        self.journals.append(journal)
        self.addCleanup(journal.close)
        return journal

    def adapter(self, auth=None, allow=OPS, branch='main', journal=None, repo=None, git=None):
        auth = auth if auth is not None else Auth()
        return ng.GitAdapter(repo or self.repo, ID, branch, IDENTITY, journal or self.journal(), authorizer=auth,
                             allow=allow, git=git)

    def write(self, name, data=b'content\n', mode=None):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if mode is not None:
            path.chmod(mode)
        return entry(name, data, bool(mode and mode & 0o111))

    def code(self, call, *args, **kw):
        with self.assertRaises(d.Rejected) as caught:
            call(*args, **kw)
        return str(caught.exception)

    def head(self, repo=None):
        return self.git('rev-parse', 'HEAD', cwd=repo)

    def events(self, journal=None):
        return [e['event'] for e in (journal or self.journals[-1]).entries]

    # ---- Phase 4: successful local flow ----
    def test_branch_stage_commit_flow_with_separate_authorizations(self):
        auth = Auth()
        adapter = self.adapter(auth)
        base = self.head()
        created = adapter.create_branch('op-branch', 'feature/native', base)
        self.assertEqual((created['status'], adapter.branch), ('APPLIED', 'feature/native'))
        self.assertEqual(self.git('branch', '--show-current'), 'feature/native')
        files = self.write('src/a.py', b'print(1)\n')
        files.update(self.write('tool.sh', b'#!/bin/sh\n', 0o755))
        adapter.stage('op-stage', files)
        self.assertEqual(self.git('diff', '--cached', '--name-only').splitlines(), ['src/a.py', 'tool.sh'])
        done = adapter.commit('op-commit', 'add native files', files)
        self.assertEqual(done['status'], 'APPLIED')
        self.assertEqual(self.git('rev-parse', 'HEAD^'), base)
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'add native files')
        self.assertEqual(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines(), ['src/a.py', 'tool.sh'])
        self.assertEqual(self.git('ls-tree', 'HEAD', 'tool.sh').split()[0], '100755')
        self.assertEqual(self.git('status', '--porcelain'), '')
        # One authorizer call per mutable operation, each carrying the exact operation.
        self.assertEqual([i['operation'] for i in auth.intents], ['create_branch', 'stage', 'commit'])
        self.assertEqual(auth.intents[2]['params']['message'], 'add native files')
        self.assertEqual([created['authorization_id'], done['authorization_id']], ['auth-1', 'auth-3'])
        self.assertEqual(self.events(), ['header', 'begin', 'end', 'begin', 'end', 'begin', 'end'])
        self.assertEqual(self.journals[-1].verify()['entries'], 7)

    def test_branch_creation_rejects_existing_stale_and_dirty_index(self):
        adapter = self.adapter()
        base = self.head()
        self.assertEqual(self.code(adapter.create_branch, 'b1', 'main', base), 'BRANCH_EXISTS')
        self.assertEqual(self.code(adapter.create_branch, 'b2', 'feature/x', '0' * 40), 'STATE_MISMATCH')
        self.assertEqual(self.code(adapter.create_branch, 'b3', '-bad', base), 'INVALID_ARGUMENTS')
        self.assertEqual(self.code(adapter.create_branch, 'b4', 'has space', base), 'INVALID_ARGUMENTS')
        self.git('branch', '--list')
        self.assertEqual(self.git('branch', '--list', 'feature/x'), '')

    def test_failed_git_operation_is_journaled_and_id_not_reusable(self):
        adapter = self.adapter()
        files = self.write('ignored.txt', b'ignored\n')
        self.assertEqual(self.code(adapter.stage, 'op-fail', files), 'GIT_FAILED')
        end = self.journals[-1].entries[-1]
        self.assertEqual((end['event'], end['result'], end['detail']), ('end', 'failed', 'GIT_FAILED'))
        self.assertEqual(self.code(adapter.stage, 'op-fail', files), 'OPERATION_ID_REUSED')

    # ---- Safe staging and integrity ----
    def test_stage_integrity_and_scope_checks(self):
        adapter = self.adapter()
        good = self.write('a.txt', b'one\n')
        stale = {'a.txt': {'sha256': '0' * 64, 'executable': False}}
        self.assertEqual(self.code(adapter.stage, 's1', stale), 'FILE_INTEGRITY_FAILED')
        wrong_mode = {'a.txt': {'sha256': good['a.txt']['sha256'], 'executable': True}}
        self.assertEqual(self.code(adapter.stage, 's2', wrong_mode), 'FILE_INTEGRITY_FAILED')
        missing = entry('missing.txt', b'x')
        self.assertEqual(self.code(adapter.stage, 's3', missing), 'FILE_INTEGRITY_FAILED')
        os.symlink('a.txt', self.repo / 'link.txt')
        self.assertEqual(self.code(adapter.stage, 's4', entry('link.txt', b'one\n')), 'UNSAFE_PATH')
        for bad in ({'../x': {'sha256': '0' * 64, 'executable': False}}, {'.git/config': {'sha256': '0' * 64, 'executable': False}},
                    {'-n': {'sha256': '0' * 64, 'executable': False}}, {'.gitattributes': {'sha256': '0' * 64, 'executable': False}},
                    {'a.txt': {'sha256': 'short', 'executable': False}}, {}, {'a.txt': 'x'}):
            self.assertEqual(self.code(adapter.stage, 'bad', bad), 'INVALID_FILES')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        other = self.write('b.txt', b'two\n')
        self.git('add', 'b.txt')
        self.assertEqual(self.code(adapter.stage, 's5', good), 'INDEX_NOT_EMPTY')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'b.txt')
        self.assertIsNotNone(other)

    def test_commit_requires_exact_staged_set_and_message_rules(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'STAGED_FILES_MISMATCH')
        adapter.stage('s1', files)
        extra = dict(files)
        extra.update(self.write('b.txt', b'two\n'))
        self.assertEqual(self.code(adapter.commit, 'c2', 'msg', extra), 'STAGED_FILES_MISMATCH')
        for message in ('', ' padded ', 'multi\nline', 'x' * 5000, 'ünïcode'):
            self.assertEqual(self.code(adapter.commit, 'c3', message, files), 'INVALID_ARGUMENTS')
        self.assertEqual(self.head(), self.git('rev-parse', 'main'))
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '1')

    # ---- Deny by default ----
    def test_unauthorized_operations_are_denied_and_journaled(self):
        files = self.write('a.txt', b'one\n')
        auth = Auth()
        adapter = self.adapter(auth, allow=('stage',))
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'OPERATION_NOT_ALLOWED')
        self.assertEqual(self.code(adapter.create_branch, 'b1', 'x', self.head()), 'OPERATION_NOT_ALLOWED')
        self.assertEqual(auth.intents, [])
        none = self.adapter(allow=(), journal=self.journal(self.jpath.with_name('k.jsonl')))
        self.assertEqual(self.code(none.stage, 's1', files), 'OPERATION_NOT_ALLOWED')
        bare = ng.GitAdapter(self.repo, ID, 'main', IDENTITY, self.journals[0], allow=OPS)
        self.assertEqual(self.code(bare.stage, 's2', files), 'AUTHORIZATION_UNAVAILABLE')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        denied = [e for e in self.journals[0].entries if e['event'] == 'denied']
        self.assertEqual([e['reason'] for e in denied], ['OPERATION_NOT_ALLOWED', 'OPERATION_NOT_ALLOWED', 'AUTHORIZATION_UNAVAILABLE'])

    def test_authorizer_must_return_identity_and_failures_deny(self):
        files = self.write('a.txt', b'one\n')
        for index, answer in enumerate((False, None, '', 'bad id with spaces', 7, ['auth-1'])):
            adapter = self.adapter(Auth(answer), journal=self.journal(self.jpath.with_name('j%d.jsonl' % index)))
            self.assertEqual(self.code(adapter.stage, 's%d' % index, files), 'AUTHORIZATION_DENIED', answer)

        def boom(intent):
            raise RuntimeError('credential must not leak')
        adapter = ng.GitAdapter(self.repo, ID, 'main', IDENTITY, self.journal(self.jpath.with_name('boom.jsonl')),
                                authorizer=boom, allow=OPS)
        self.assertEqual(self.code(adapter.stage, 'sb', files), 'AUTHORIZATION_ERROR')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertNotIn(b'credential', self.jpath.with_name('boom.jsonl').read_bytes())

    def test_authorization_is_not_reused_across_operations(self):
        approvals = []

        def once(intent):
            approvals.append(intent['operation'])
            return 'auth-stage' if intent['operation'] == 'stage' else None
        adapter = ng.GitAdapter(self.repo, ID, 'main', IDENTITY, self.journal(), authorizer=once, allow=OPS)
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'AUTHORIZATION_DENIED')
        self.assertEqual(approvals, ['stage', 'commit'])
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '1')

    def test_remote_and_unlisted_operations_do_not_exist(self):
        adapter = self.adapter()
        for name in ('push', 'fetch', 'pull', 'reset', 'clean', 'branch_delete', 'merge', 'tag', 'checkout'):
            self.assertEqual(self.code(adapter.execute, name, 'op-x'), 'OPERATION_NOT_SUPPORTED')
            self.assertFalse(hasattr(adapter, name))
        self.assertEqual(self.code(adapter.execute, 'stage', 'op-y', files={}, extra=1), 'INVALID_ARGUMENTS')
        self.assertEqual(self.code(adapter.execute, 'stage', 'bad id'), 'INVALID_OPERATION_ID')
        with self.assertRaises(d.Rejected):
            ng.GitAdapter(self.repo, ID, 'main', IDENTITY, self.journal(), allow=('push',))
        self.assertFalse({'push', 'fetch', 'pull', 'clone', 'remote', 'reset', 'clean', 'checkout', 'branch', 'rebase', 'merge',
                          'tag', 'update-ref', 'filter-branch'} & set(ng.GitAdapter.COMMANDS))

    def test_state_changed_after_authorization_is_denied(self):
        files = self.write('a.txt', b'one\n')

        def drift(intent):
            (self.repo / 'a.txt').write_bytes(b'tampered\n')
            return 'auth-1'
        adapter = ng.GitAdapter(self.repo, ID, 'main', IDENTITY, self.journal(), authorizer=drift, allow=OPS)
        self.assertEqual(self.code(adapter.stage, 's1', files), 'FILE_INTEGRITY_FAILED')
        denied = self.journals[0].entries[-1]
        self.assertEqual((denied['event'], denied['authorization_id']), ('denied', 'auth-1'))
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        (self.repo / 'a.txt').write_bytes(b'one\n')
        adapter.authorizer = Auth()
        adapter.stage('s2', files)

        def sneak(intent):
            (self.repo / 'b.txt').write_bytes(b'x\n')
            self.git('add', 'b.txt')
            return 'auth-2'
        adapter.authorizer = sneak
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'STATE_CHANGED_AFTER_AUTHORIZATION')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '1')

    def test_head_or_branch_drift_is_rejected(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        self.git('checkout', '-q', '-b', 'other')
        self.assertEqual(self.code(adapter.stage, 's1', files), 'BRANCH_CHANGED')
        self.git('checkout', '-q', '--detach')
        self.assertEqual(self.code(adapter.stage, 's2', files), 'BRANCH_CHANGED')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    # ---- Journal ----
    def test_journal_persists_verifies_and_rejects_tampering(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        adapter.commit('c1', 'first', files)
        first = self.journals[0]
        summary = first.verify()
        first.close()
        reopened = ng.Journal(self.jpath, ID, self.repo)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.verify(), summary)
        self.assertEqual(reopened.operation('c1')[0], 'applied')
        begin = reopened.entries[3]
        self.assertEqual((begin['event'], begin['authorization_id']), ('begin', 'auth-2'))
        self.assertEqual(begin['expected']['head_sha'], begin['expected_post']['parent'])
        self.assertEqual(begin['intent']['params']['message_sha256'], hashlib.sha256(b'first').hexdigest())
        reopened.close()
        original = self.jpath.read_bytes()
        lines = original.split(b'\n')
        cases = {
            'edited': original.replace(b'"applied"', b'"failed"'),
            'deleted': b'\n'.join(lines[:2] + lines[3:]),
            'reordered': b'\n'.join([lines[0], lines[2], lines[1]] + lines[3:]),
            'garbage': original + b'not json\n',
            'extra-key': original.replace(b'{"contract"', b'{"a":1,"contract"', 1),
        }
        for name, data in cases.items():
            self.assertNotEqual(data, original, name)
            self.jpath.write_bytes(data)
            with self.assertRaises(d.Rejected, msg=name):
                ng.Journal(self.jpath, ID, self.repo)
        self.jpath.write_bytes(original)
        ng.Journal(self.jpath, ID, self.repo).close()

    def test_journal_torn_tail_requires_explicit_repair(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        self.journals[0].close()
        data = self.jpath.read_bytes()
        self.jpath.write_bytes(data[:-15])
        self.assertEqual(self.code(ng.Journal, self.jpath, ID, self.repo), 'JOURNAL_TORN_TAIL')
        repaired = ng.Journal(self.jpath, ID, self.repo, repair_torn_tail=True)
        self.addCleanup(repaired.close)
        self.assertTrue(repaired.repaired)
        self.assertEqual([e['event'] for e in repaired.entries], ['header', 'begin'])
        self.assertEqual(repaired.pending(), ['s1'])
        self.assertTrue(self.jpath.read_bytes().endswith(b'\n'))

    def test_journal_is_single_writer_outside_repository_and_not_a_symlink(self):
        self.journal()
        self.assertEqual(self.code(ng.Journal, self.jpath, ID, self.repo), 'JOURNAL_LOCKED')
        self.assertEqual(self.code(ng.Journal, self.repo / 'j.jsonl', ID, self.repo), 'JOURNAL_INSIDE_REPOSITORY')
        self.assertEqual(self.code(ng.Journal, self.repo / '.git' / 'j.jsonl', ID, self.repo), 'JOURNAL_INSIDE_REPOSITORY')
        link = self.jpath.with_name('link.jsonl')
        os.symlink(self.jpath, link)
        self.assertEqual(self.code(ng.Journal, link, ID, self.repo), 'JOURNAL_PATH_INVALID')
        loose = self.jpath.with_name('loose.jsonl')
        loose.write_bytes(b'')
        loose.chmod(0o666)
        self.assertEqual(self.code(ng.Journal, loose, ID, self.repo), 'JOURNAL_PATH_INVALID')
        self.assertEqual(self.code(ng.Journal, Path(self.tmp.name) / 'missing' / 'j', ID, self.repo), 'JOURNAL_PATH_INVALID')

    def test_journal_stores_no_secrets_or_free_text(self):
        secret = 'sk-live-0123456789abcdef'
        with patch.dict(os.environ, {'AWS_SECRET_ACCESS_KEY': secret, 'GITHUB_TOKEN': secret}):
            adapter = self.adapter()
            files = self.write('a.txt', b'one\n')
            adapter.stage('s1', files)
            adapter.commit('c1', 'message with password hunter2', files)
        data = self.jpath.read_bytes()
        for needle in (secret.encode(), b'hunter2', b'password', b'AWS_', b'GITHUB_TOKEN', IDENTITY[1].encode()):
            self.assertNotIn(needle, data)
        journal = self.journals[0]
        for event, fields in (('denied', dict(operation_id='x', operation='stage', intent_sha256='0' * 64, reason='lower',
                                              authorization_id=None)),
                              ('end', dict(operation_id='c1', result='applied', observed={'x': 1}, detail='OK'))):
            with self.assertRaises(d.Rejected):
                journal.append(event, **fields)
        self.assertEqual(journal.verify()['entries'], len(journal.entries))

    # ---- Crash recovery and duplicate prevention ----
    def crash_on(self, adapter, command):
        real = adapter._run

        def crash(*argv, **kw):
            if argv[0] == command:
                raise RuntimeError('simulated crash')
            return real(*argv, **kw)
        return patch.object(adapter, '_run', crash)

    def reopen(self, journal):
        journal.close()
        return self.adapter(journal=self.journal())

    def test_crash_after_git_before_result_recovers_as_applied_without_rerun(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        journal = self.journals[0]
        real = journal.append

        def lose_end(event, **kw):
            if event == 'end':
                raise RuntimeError('simulated crash')
            return real(event, **kw)
        with patch.object(journal, 'append', lose_end):
            with self.assertRaises(RuntimeError):
                adapter.stage('s1', files)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'a.txt')
        fresh = self.reopen(journal)
        self.assertEqual(self.journals[-1].operation('s1')[0], 'pending')
        self.assertEqual(self.code(fresh.stage, 's2', files), 'JOURNAL_UNRESOLVED')
        self.assertEqual(fresh.recover(), {'s1': 'RECONCILED_APPLIED'})
        replay = fresh.stage('s1', files)
        self.assertEqual(replay['status'], 'REPLAYED')
        self.assertEqual(fresh.authorizer.intents, [])
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'a.txt')

    def test_crash_before_git_recovers_as_not_applied_and_id_is_retired(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        with self.crash_on(adapter, 'add'):
            with self.assertRaises(RuntimeError):
                adapter.stage('s1', files)
        fresh = self.reopen(self.journals[0])
        self.assertEqual(fresh.recover(), {'s1': 'RECONCILED_NOT_APPLIED'})
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.code(fresh.stage, 's1', files), 'OPERATION_NOT_APPLIED')
        self.assertEqual(fresh.stage('s2', files)['status'], 'APPLIED')

    def test_crash_during_commit_recovers_from_observed_commit(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        journal = self.journals[0]
        real = journal.append

        def lose_end(event, **kw):
            if event == 'end':
                raise RuntimeError('simulated crash')
            return real(event, **kw)
        with patch.object(journal, 'append', lose_end):
            with self.assertRaises(RuntimeError):
                adapter.commit('c1', 'crashy', files)
        count = self.git('rev-list', '--count', 'HEAD')
        fresh = self.reopen(journal)
        self.assertEqual(fresh.recover(), {'c1': 'RECONCILED_APPLIED'})
        self.assertEqual(fresh.commit('c1', 'crashy', files)['status'], 'REPLAYED')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), count)

    def test_crash_during_branch_creation_recovers_and_updates_adapter(self):
        adapter = self.adapter()
        base = self.head()
        journal = self.journals[0]
        real = journal.append

        def lose_end(event, **kw):
            if event == 'end':
                raise RuntimeError('simulated crash')
            return real(event, **kw)
        with patch.object(journal, 'append', lose_end):
            with self.assertRaises(RuntimeError):
                adapter.create_branch('b1', 'feature/crash', base)
        fresh = self.reopen(journal)
        self.assertEqual(fresh.recover(), {'b1': 'RECONCILED_APPLIED'})
        self.assertEqual(fresh.branch, 'feature/crash')
        self.assertEqual(fresh.stage('s1', self.write('a.txt'))['status'], 'APPLIED')

    def test_unexplained_state_is_ambiguous_and_blocks_further_mutation(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        with self.crash_on(adapter, 'add'):
            with self.assertRaises(RuntimeError):
                adapter.stage('s1', files)
        self.write('other.txt', b'surprise\n')
        self.git('add', 'other.txt')
        fresh = self.reopen(self.journals[0])
        self.assertEqual(fresh.recover(), {'s1': 'AMBIGUOUS'})
        self.assertEqual(self.code(fresh.stage, 's2', files), 'JOURNAL_UNRESOLVED')
        self.assertEqual(self.code(fresh.stage, 's1', files), 'OPERATION_AMBIGUOUS')
        self.assertEqual(self.journals[-1].unresolved(), ['s1'])

    def test_duplicate_operations_are_prevented(self):
        auth = Auth()
        adapter = self.adapter(auth)
        files = self.write('a.txt', b'one\n')
        self.assertEqual(adapter.stage('s1', files)['status'], 'APPLIED')
        again = adapter.stage('s1', files)
        self.assertEqual(again['status'], 'REPLAYED')
        self.assertEqual(len(auth.intents), 1)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'a.txt')
        other = self.write('b.txt', b'two\n')
        self.assertEqual(self.code(adapter.stage, 's1', other), 'OPERATION_ID_CONFLICT')
        self.assertEqual(self.code(adapter.commit, 's1', 'msg', files), 'OPERATION_ID_CONFLICT')
        adapter.commit('c1', 'once', files)
        self.assertEqual(adapter.commit('c1', 'once', files)['status'], 'REPLAYED')
        self.assertEqual(self.code(adapter.commit, 'c1', 'different', files), 'OPERATION_ID_CONFLICT')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')

    def test_denied_operation_id_may_be_retried_with_new_authorization(self):
        files = self.write('a.txt', b'one\n')
        auth = Auth(False)
        adapter = self.adapter(auth)
        self.assertEqual(self.code(adapter.stage, 's1', files), 'AUTHORIZATION_DENIED')
        auth.answer = True
        self.assertEqual(adapter.stage('s1', files)['status'], 'APPLIED')

    # ---- Git failure classification (S1) ----
    # Deterministic fault injection: no sleeps and no real timeouts. Only calls made by the adapter are
    # intercepted (they carry the adapter's minimal environment); the test's own Git helper is untouched.
    def faulty_git(self, subcommand, after_apply=True, exc=None, blind=False):
        """First `subcommand` call fails with exc, after Git applied it when after_apply. blind=True makes every
        later adapter Git call fail too, so the resulting repository state cannot be observed."""
        real = subprocess.run
        state = {'fired': False}
        make = exc or (lambda cmd: subprocess.TimeoutExpired(cmd, 60))

        def run(cmd, **kw):
            adapter_call = 'GIT_TERMINAL_PROMPT' in (kw.get('env') or {}) and '-C' in cmd
            if adapter_call and blind and state['fired']:
                raise make(cmd)
            if adapter_call and not state['fired'] and cmd[cmd.index('-C') + 2] == subcommand:
                state['fired'] = True
                if after_apply:
                    real(cmd, **kw)
                raise make(cmd)
            return real(cmd, **kw)
        return patch('ai_sdlc.native_git.subprocess.run', run)

    def before_git(self, subcommand, action):
        """Run action() once, immediately before the adapter's first `subcommand` Git call."""
        real = subprocess.run
        state = {'done': False}

        def run(cmd, **kw):
            if ('GIT_TERMINAL_PROMPT' in (kw.get('env') or {}) and '-C' in cmd and not state['done']
                    and cmd[cmd.index('-C') + 2] == subcommand):
                state['done'] = True
                action()
            return real(cmd, **kw)
        return patch('ai_sdlc.native_git.subprocess.run', run)

    def wrapper_git(self, subcommand):
        """A git executable that performs the real command and then exits 1 (nonzero exit after the change)."""
        script = Path(self.tmp.name) / ('git-fails-after-' + subcommand)
        script.write_text('#!/bin/sh\n%s "$@"; rc=$?\ncase " $* " in *" %s "*) [ "$rc" = 0 ] && exit 1;; esac\nexit $rc\n'
                          % (shutil.which('git'), subcommand))
        script.chmod(0o755)
        return str(script)

    def end_event(self):
        return [e for e in self.journals[-1].entries if e['event'] == 'end'][-1]

    def test_add_applied_then_timeout_is_journaled_applied(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        with self.faulty_git('add'):
            result = adapter.stage('s1', files)
        self.assertEqual(result['status'], 'APPLIED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('applied', 'APPLIED_AFTER_ERROR'))
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'a.txt')
        asked = len(adapter.authorizer.intents)
        self.assertEqual(adapter.stage('s1', files)['status'], 'REPLAYED')  # no second add, no new authorization
        self.assertEqual((len(adapter.authorizer.intents), self.events().count('begin')), (asked, 1))
        self.assertEqual(self.journals[0].unresolved(), [])

    def test_commit_applied_then_oserror_is_journaled_applied(self):
        adapter = self.adapter()
        base = self.head()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        with self.faulty_git('commit', exc=lambda cmd: OSError('simulated I/O failure')):
            result = adapter.commit('c1', 'msg', files)
        self.assertEqual(result['status'], 'APPLIED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('applied', 'APPLIED_AFTER_ERROR'))
        self.assertEqual((self.git('rev-list', '--count', 'HEAD'), self.git('rev-parse', 'HEAD^')), ('2', base))

    def test_commit_applied_then_nonzero_exit_is_journaled_applied(self):
        adapter = self.adapter(git=self.wrapper_git('commit'))
        base = self.head()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        result = adapter.commit('c1', 'msg', files)  # the wrapper ran the real commit, then exited 1
        self.assertEqual(result['status'], 'APPLIED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('applied', 'APPLIED_AFTER_ERROR'))
        self.assertEqual((self.git('rev-list', '--count', 'HEAD'), self.git('rev-parse', 'HEAD^')), ('2', base))

    def test_branch_switch_applied_then_timeout_is_journaled_applied(self):
        adapter = self.adapter()
        base = self.head()
        with self.faulty_git('switch'):
            result = adapter.create_branch('b1', 'feature/x', base)
        self.assertEqual(result['status'], 'APPLIED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('applied', 'APPLIED_AFTER_ERROR'))
        self.assertEqual((adapter.branch, self.git('branch', '--show-current')), ('feature/x', 'feature/x'))

    def test_timeout_before_git_runs_is_a_confirmed_failure(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        with self.faulty_git('add', after_apply=False):
            self.assertEqual(self.code(adapter.stage, 's1', files), 'GIT_OUTCOME_UNKNOWN')
        begin = [e for e in self.journals[0].entries if e['event'] == 'begin'][-1]
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('failed', 'GIT_OUTCOME_UNKNOWN'))
        self.assertEqual(end['observed'], begin['expected'])  # observation proves nothing changed
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.journals[0].unresolved(), [])
        self.assertEqual(self.code(adapter.stage, 's1', files), 'OPERATION_ID_REUSED')
        self.assertEqual(adapter.stage('s2', files)['status'], 'APPLIED')

    def test_postcondition_failure_after_unexpected_file_change(self):
        adapter = self.adapter()
        base = self.head()
        files = self.write('a.txt', b'one\n')
        with self.before_git('add', lambda: (self.repo / 'a.txt').write_bytes(b'CHANGED\n')):
            self.assertEqual(self.code(adapter.stage, 's1', files), 'POSTCONDITION_FAILED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('failed', 'POSTCONDITION_FAILED'))
        staged = {item[0]: item[1] for item in end['observed']['staged']}
        self.assertEqual(staged, {'a.txt': hashlib.sha256(b'CHANGED\n').hexdigest()})  # the wrong bytes were staged
        self.assertNotEqual(staged['a.txt'], files['a.txt']['sha256'])
        self.assertEqual(self.journals[0].unresolved(), [])
        # Fail closed: nothing else can proceed on top of the unexpected index.
        self.assertEqual(self.code(adapter.stage, 's2', files), 'INDEX_NOT_EMPTY')
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'STAGED_FILES_MISMATCH')
        self.assertEqual(self.head(), base)

    def test_postcondition_failure_after_extra_staged_file(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)

        def stage_extra():
            (self.repo / 'extra.txt').write_bytes(b'extra\n')
            self.git('add', 'extra.txt')
        with self.before_git('commit', stage_extra):
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'POSTCONDITION_FAILED')
        end = self.end_event()
        self.assertEqual((end['result'], end['detail']), ('failed', 'POSTCONDITION_FAILED'))
        # The unauthorized file is in the commit; the library records it and never resets or amends.
        self.assertEqual(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').split(), ['a.txt', 'extra.txt'])
        self.assertEqual(self.journals[0].unresolved(), [])
        self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'OPERATION_ID_REUSED')

    # ---- D3: an outcome that cannot be observed is never recorded as a confirmed failure ----
    def test_unobservable_outcome_after_apply_stays_unresolved(self):
        adapter = self.adapter()
        journal = self.journals[0]
        files = self.write('a.txt', b'one\n')
        with self.faulty_git('add', blind=True):
            self.assertEqual(self.code(adapter.stage, 's1', files), 'GIT_OUTCOME_UNKNOWN')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'a.txt')  # it did apply
        self.assertEqual(self.events(), ['header', 'begin'])  # no confirmed result was recorded
        self.assertEqual(journal.operation('s1')[0], 'pending')
        self.assertEqual(journal.unresolved(), ['s1'])
        self.assertEqual(self.code(adapter.stage, 's2', self.write('b.txt', b'two\n')), 'JOURNAL_UNRESOLVED')
        self.assertEqual(adapter.recover(), {'s1': 'RECONCILED_APPLIED'})
        self.assertEqual(journal.unresolved(), [])
        asked = len(adapter.authorizer.intents)
        self.assertEqual(adapter.stage('s1', files)['status'], 'REPLAYED')
        self.assertEqual(len(adapter.authorizer.intents), asked)

    def test_unobservable_outcome_without_apply_recovers_as_not_applied(self):
        adapter = self.adapter()
        journal = self.journals[0]
        files = self.write('a.txt', b'one\n')
        with self.faulty_git('add', after_apply=False, blind=True):
            self.assertEqual(self.code(adapter.stage, 's1', files), 'GIT_OUTCOME_UNKNOWN')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual((journal.operation('s1')[0], journal.unresolved()), ('pending', ['s1']))
        self.assertEqual(adapter.recover(), {'s1': 'RECONCILED_NOT_APPLIED'})
        self.assertEqual(journal.unresolved(), [])
        self.assertEqual(self.code(adapter.stage, 's1', files), 'OPERATION_NOT_APPLIED')  # id is retired, not retried
        self.assertEqual(adapter.stage('s2', files)['status'], 'APPLIED')

    def test_unobservable_commit_outcome_recovers_without_a_second_commit(self):
        adapter = self.adapter()
        journal = self.journals[0]
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        with self.faulty_git('commit', blind=True):
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'GIT_OUTCOME_UNKNOWN')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')  # the commit did apply
        self.assertEqual(journal.unresolved(), ['c1'])
        self.assertEqual(self.code(adapter.commit, 'c2', 'other', files), 'JOURNAL_UNRESOLVED')
        self.assertEqual(adapter.recover(), {'c1': 'RECONCILED_APPLIED'})
        self.assertEqual(adapter.commit('c1', 'msg', files)['status'], 'REPLAYED')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')

    def test_unobservable_branch_switch_updates_the_adapter_on_recovery(self):
        adapter = self.adapter()
        journal = self.journals[0]
        base = self.head()
        with self.faulty_git('switch', blind=True):
            self.assertEqual(self.code(adapter.create_branch, 'b1', 'feature/x', base), 'GIT_OUTCOME_UNKNOWN')
        self.assertEqual((self.git('branch', '--show-current'), adapter.branch), ('feature/x', 'main'))
        self.assertEqual(journal.unresolved(), ['b1'])
        self.assertEqual(adapter.recover(), {'b1': 'RECONCILED_APPLIED'})
        self.assertEqual(adapter.branch, 'feature/x')

    def test_unobservable_outcome_with_unexplained_state_recovers_as_ambiguous(self):
        adapter = self.adapter()
        journal = self.journals[0]
        files = self.write('a.txt', b'one\n')
        with self.faulty_git('add', after_apply=False, blind=True):
            self.assertEqual(self.code(adapter.stage, 's1', files), 'GIT_OUTCOME_UNKNOWN')
        self.write('other.txt', b'surprise\n')
        self.git('add', 'other.txt')  # an unexplained change made while the outcome was unknown
        self.assertEqual(adapter.recover(), {'s1': 'AMBIGUOUS'})
        self.assertEqual(journal.unresolved(), ['s1'])
        self.assertEqual(self.code(adapter.stage, 's2', files), 'JOURNAL_UNRESOLVED')
        self.assertEqual(self.code(adapter.stage, 's1', files), 'OPERATION_AMBIGUOUS')

    # ---- D2: Git output that is not valid UTF-8 must never escape as an uncaught exception ----
    def git_bytes(self, *args, data=None):
        env = {'PATH': os.defpath, 'HOME': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
               'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
               'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        return subprocess.run(['git', '-C', str(self.repo), *args], env=env, input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True).stdout

    def foreign_commit(self, message):
        """Move main to a commit whose message is exactly these bytes. `git commit` re-encodes invalid UTF-8,
        so the object is written directly. Its tree is the index tree, so the index is clean afterwards."""
        body = (b'tree ' + self.git('write-tree').encode() + b'\nparent ' + self.head().encode()
                + b'\nauthor O <o@example.invalid> 1700000000 +0000\ncommitter O <o@example.invalid> 1700000000 +0000\n\n'
                + message)
        sha = self.git_bytes('hash-object', '-t', 'commit', '-w', '--stdin', '--literally', data=body).decode().strip()
        self.git('update-ref', 'refs/heads/main', sha)
        return sha

    def pending_commit(self):
        """A commit operation that crashed before Git ran, so it is pending; returns (adapter, files)."""
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        with self.crash_on(adapter, 'commit'):
            with self.assertRaises(RuntimeError):
                adapter.commit('c1', 'msg', files)
        return self.reopen(self.journals[0]), files

    def mutating_calls(self, adapter):
        calls = []
        real = adapter._run

        def spy(*argv, **kw):
            if argv[0] in ('add', 'commit', 'switch'):
                calls.append(argv[0])
            return real(*argv, **kw)
        return calls, patch.object(adapter, '_run', spy)

    def test_recovery_with_non_utf8_foreign_commit_message_is_ambiguous_not_an_exception(self):
        adapter, files = self.pending_commit()
        sha = self.foreign_commit(b'msg \xe9 not utf8\n')
        # Fixture guard: Git really emits bytes that are not valid UTF-8 for this commit.
        self.assertIn(b'\xe9', self.git_bytes('cat-file', 'commit', sha))
        with self.assertRaises(UnicodeDecodeError):
            self.git_bytes('show', '-s', '--format=%B', sha).decode('utf-8')
        calls, spy = self.mutating_calls(adapter)
        with spy:
            self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
            # Uncertain outcome: no replay, no new mutation, no new id accepted.
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'OPERATION_AMBIGUOUS')
            self.assertEqual(self.code(adapter.commit, 'c2', 'other', files), 'JOURNAL_UNRESOLVED')
        self.assertEqual(calls, [])
        journal = self.journals[-1]
        recovery = journal.entries[-1]
        self.assertEqual((recovery['event'], recovery['status']), ('recovery', 'AMBIGUOUS'))
        self.assertEqual(recovery['observed']['head_sha'], sha)  # what could be observed is preserved as evidence
        self.assertEqual(journal.unresolved(), ['c1'])
        self.assertEqual(journal.verify()['entries'], len(journal.entries))
        journal.close()
        reopened = ng.Journal(self.jpath, ID, self.repo)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.operation('c1')[0], 'ambiguous')  # the chain on disk is intact and still unresolved

    def test_recovery_with_valid_utf8_foreign_commit_message_is_ambiguous(self):
        adapter, files = self.pending_commit()
        sha = self.foreign_commit('msg café\n'.encode('utf-8'))
        self.git_bytes('show', '-s', '--format=%B', sha).decode('utf-8')  # fixture guard: valid UTF-8
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
        self.assertEqual(self.journals[-1].entries[-1]['observed']['head_sha'], sha)

    def test_recovery_of_the_adapters_own_applied_commit_still_reconciles(self):
        adapter, files = self.pending_commit()
        token = self.journals[-1].operation('c1')[1]['expected_post']['provenance']
        self.git('commit', '-q', '-m', 'msg\n\nAI-SDLC-Provenance: ' + token)  # the commit the crashed operation was about to make
        self.assertEqual(adapter.recover(), {'c1': 'RECONCILED_APPLIED'})
        self.assertEqual(adapter.commit('c1', 'msg', files)['status'], 'REPLAYED')

    def test_observe_with_non_utf8_branch_name_is_rejected_not_an_exception(self):
        adapter = self.adapter()
        name = b'refs/heads/caf\xe9'
        self.git_bytes('update-ref', name, 'HEAD')
        self.git_bytes('symbolic-ref', 'HEAD', name)
        with self.assertRaises(UnicodeDecodeError):  # fixture guard
            self.git_bytes('symbolic-ref', '--short', 'HEAD').decode('utf-8')
        self.assertEqual(self.code(adapter.observe), 'GIT_OUTPUT_INVALID')
        # A mutation is denied before anything begins; the denial is journaled.
        files = self.write('a.txt', b'one\n')
        self.assertEqual(self.code(adapter.stage, 's1', files), 'GIT_OUTPUT_INVALID')
        self.assertEqual(self.events(), ['header', 'denied'])
        self.assertEqual(self.journals[0].unresolved(), [])
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    def test_observe_with_utf8_non_ascii_branch_name_reports_branch_changed(self):
        adapter = self.adapter()
        name = 'refs/heads/café'.encode('utf-8')
        self.git_bytes('update-ref', name, 'HEAD')
        self.git_bytes('symbolic-ref', 'HEAD', name)
        self.git_bytes('symbolic-ref', '--short', 'HEAD').decode('utf-8')  # fixture guard: valid UTF-8
        self.assertEqual(self.code(adapter.observe), 'BRANCH_CHANGED')

    def test_unknown_outcome_then_undecodable_state_stays_unresolved_without_duplicate_mutation(self):
        adapter = self.adapter()
        journal = self.journals[0]
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        with self.faulty_git('commit', after_apply=False, blind=True):
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'GIT_OUTCOME_UNKNOWN')
        self.assertEqual(journal.unresolved(), ['c1'])  # D3: an unobservable outcome is unresolved, not failed
        self.foreign_commit(b'caf\xe9\n')
        calls, spy = self.mutating_calls(adapter)
        with spy:
            self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'OPERATION_AMBIGUOUS')
        self.assertEqual(calls, [])
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')  # base + the foreign commit, nothing from the adapter
        self.assertEqual(journal.unresolved(), ['c1'])

    # ---- D4: Commit provenance — never attribute a foreign commit by matching content alone ----
    def test_foreign_commit_with_identical_parent_message_and_tree_is_ambiguous(self):
        adapter, files = self.pending_commit()
        sha = self.foreign_commit(b'msg\n')
        calls, spy = self.mutating_calls(adapter)
        with spy:
            self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
            self.assertEqual(self.code(adapter.commit, 'c1', 'msg', files), 'OPERATION_AMBIGUOUS')
        self.assertEqual(calls, [])
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')
        self.assertEqual(self.journals[-1].entries[-1]['observed']['head_sha'], sha)
        self.assertEqual(self.journals[-1].unresolved(), ['c1'])

    def test_foreign_commit_with_identical_author_and_timestamp_is_ambiguous(self):
        adapter, files = self.pending_commit()
        ts = self.journals[-1].operation('c1')[1]['ts']
        env = {'PATH': os.defpath, 'HOME': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
               'GIT_AUTHOR_NAME': IDENTITY[0], 'GIT_AUTHOR_EMAIL': IDENTITY[1],
               'GIT_COMMITTER_NAME': IDENTITY[0], 'GIT_COMMITTER_EMAIL': IDENTITY[1],
               'GIT_AUTHOR_DATE': '%d +0000' % ts, 'GIT_COMMITTER_DATE': '%d +0000' % ts}
        subprocess.run(['git', '-C', str(self.repo), 'commit', '--no-verify', '--no-gpg-sign', '-q', '-m', 'msg'],
                       env=env, check=True)
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
        self.assertEqual(adapter.journal.unresolved(), ['c1'])

    def test_concurrent_same_identity_writer_is_ambiguous(self):
        adapter, files = self.pending_commit()
        other_jpath = self.jpath.with_name('other-writer.jsonl')
        other_journal = self.journal(other_jpath, self.repo)
        other = self.adapter(journal=other_journal)
        other.commit('c1', 'msg', files)
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
        self.assertEqual(adapter.journal.unresolved(), ['c1'])

    def test_legacy_pending_journal_without_provenance_fails_closed_as_ambiguous(self):
        adapter, files = self.pending_commit()
        journal = self.journals[-1]
        _, begin = journal.operation('c1')
        # Simulate a pre-D4 legacy journal entry where expected_post has no provenance field.
        begin['expected_post'].pop('provenance', None)
        self.git('commit', '-q', '-m', 'msg')
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})
        self.assertEqual(journal.unresolved(), ['c1'])

    def test_provenance_token_mentioned_only_in_body_or_duplicated_is_ambiguous(self):
        adapter, files = self.pending_commit()
        _, begin = self.journals[-1].operation('c1')
        token = begin['expected_post'].get('provenance', '0' * 32)
        # Body mention without reserved final trailer.
        self.foreign_commit(('msg\n\nAI-SDLC-Provenance: %s\n\nmore body\n' % token).encode('utf-8'))
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})

    def test_duplicated_provenance_trailer_is_ambiguous(self):
        adapter, files = self.pending_commit()
        _, begin = self.journals[-1].operation('c1')
        token = begin['expected_post'].get('provenance', '0' * 32)
        self.foreign_commit(('msg\n\nAI-SDLC-Provenance: %s\nAI-SDLC-Provenance: %s\n' % (token, token)).encode('utf-8'))
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})

    def test_mismatched_provenance_trailer_is_ambiguous(self):
        adapter, files = self.pending_commit()
        self.foreign_commit(('msg\n\nAI-SDLC-Provenance: %s\n' % ('f' * 32)).encode('utf-8'))
        self.assertEqual(adapter.recover(), {'c1': 'AMBIGUOUS'})

    def test_user_message_containing_reserved_trailer_prefix_is_rejected(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        self.assertEqual(self.code(adapter.commit, 'c1', 'AI-SDLC-Provenance: ' + 'a' * 32, files), 'INVALID_ARGUMENTS')

    def test_crash_after_commit_before_end_reconciles_with_provenance_and_packed_refs(self):
        adapter = self.adapter()
        files = self.write('a.txt', b'one\n')
        adapter.stage('s1', files)
        journal = self.journals[0]
        real = journal.append

        def lose_end(event, **kw):
            if event == 'end':
                raise RuntimeError('simulated crash')
            return real(event, **kw)

        with patch.object(journal, 'append', lose_end):
            with self.assertRaises(RuntimeError):
                adapter.commit('c1', 'crashy', files)
        self.git('pack-refs', '--all')
        fresh = self.reopen(journal)
        self.assertEqual(fresh.recover(), {'c1': 'RECONCILED_APPLIED'})
        self.assertEqual(fresh.recover(), {})
        self.assertEqual(fresh.commit('c1', 'crashy', files)['status'], 'REPLAYED')
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')

    # ---- Repository isolation and environment ----
    def test_repository_isolation(self):
        other = Path(self.tmp.name) / 'other'
        other.mkdir()
        self.make_repo(other)
        before = (self.head(other), self.git('for-each-ref', cwd=other), self.git('status', '--porcelain', cwd=other))
        # A journal for another repository or identity cannot be reused.
        foreign = self.journal(self.jpath.with_name('other.jsonl'), other)
        self.assertEqual(self.code(ng.GitAdapter, self.repo, ID, 'main', IDENTITY, foreign), 'JOURNAL_REPOSITORY_MISMATCH')
        foreign.close()
        self.assertEqual(self.code(ng.Journal, self.jpath.with_name('other.jsonl'), ID, self.repo), 'JOURNAL_REPOSITORY_MISMATCH')
        self.assertEqual(self.code(ng.Journal, self.jpath.with_name('other.jsonl'), 'https://example.invalid/x/y', other),
                         'JOURNAL_REPOSITORY_MISMATCH')
        # Ambient Git environment pointing at another repository is ignored.
        with patch.dict(os.environ, {'GIT_DIR': str(other / '.git'), 'GIT_WORK_TREE': str(other), 'GIT_INDEX_FILE': str(other / 'x')}):
            adapter = self.adapter()
            files = self.write('a.txt', b'one\n')
            adapter.create_branch('b1', 'feature/iso', self.head())
            adapter.stage('s1', files)
            adapter.commit('c1', 'isolated', files)
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'isolated')
        self.assertEqual((self.head(other), self.git('for-each-ref', cwd=other), self.git('status', '--porcelain', cwd=other)), before)
        # Nested directories, symlinked paths and gitdir links are not repositories for this adapter.
        sub = self.repo / 'sub'
        sub.mkdir()
        nested = ng.GitAdapter(sub, ID, 'feature/iso', IDENTITY, self.journal(self.jpath.with_name('sub.jsonl'), sub), allow=OPS)
        self.assertEqual(self.code(nested.observe), 'UNSUPPORTED_GIT_LAYOUT')
        link = Path(self.tmp.name) / 'link'
        os.symlink(self.repo, link)
        self.assertEqual(self.code(ng.GitAdapter, link, ID, 'main', IDENTITY, self.journal(self.jpath.with_name('l.jsonl'), link)),
                         'UNSAFE_PATH')
        pointer = Path(self.tmp.name) / 'pointer'
        pointer.mkdir()
        (pointer / '.git').write_text('gitdir: %s\n' % (other / '.git'))
        indirect = ng.GitAdapter(pointer, ID, 'main', IDENTITY, self.journal(self.jpath.with_name('p.jsonl'), pointer), allow=OPS)
        self.assertEqual(self.code(indirect.observe), 'UNSUPPORTED_GIT_LAYOUT')

    def test_unsafe_repository_configuration_is_rejected(self):
        adapter = self.adapter()
        self.assertEqual(adapter.observe()['branch'], 'main')
        hook = self.repo / '.git' / 'hooks' / 'pre-commit'
        hook.write_text('#!/bin/sh\necho ran > %s/hook-ran\n' % self.tmp.name)
        hook.chmod(0o755)
        self.assertEqual(self.code(adapter.observe), 'UNSAFE_GIT_HOOKS')
        files = self.write('a.txt', b'one\n')
        self.assertEqual(self.code(adapter.stage, 's1', files), 'UNSAFE_GIT_HOOKS')
        hook.unlink()
        for key, value in (('core.hooksPath', '/tmp/hooks'), ('alias.st', '!sh'), ('core.fsmonitor', 'x'),
                           ('filter.x.clean', 'x'), ('include.path', '/tmp/x'), ('core.sshCommand', 'x'),
                           ('extensions.worktreeConfig', 'true')):
            self.git('config', key, value)
            self.assertEqual(self.code(adapter.observe), 'UNSAFE_GIT_CONFIG', key)
            self.git('config', '--unset', key)
        (self.repo / '.gitattributes').write_text('* filter=x\n')
        self.assertEqual(self.code(adapter.observe), 'ATTRIBUTES_UNSUPPORTED')
        (self.repo / '.gitattributes').unlink()
        (self.repo / '.git' / 'MERGE_HEAD').write_text(self.head() + '\n')
        self.assertEqual(self.code(adapter.observe), 'UNSAFE_GIT_STATE')
        (self.repo / '.git' / 'MERGE_HEAD').unlink()
        self.assertFalse((Path(self.tmp.name) / 'hook-ran').exists())
        self.assertEqual(adapter.observe()['head_sha'], self.head())

    # ---- Execution hygiene ----
    def test_git_is_invoked_without_shell_arbitrary_arguments_or_ambient_environment(self):
        real = subprocess.run
        calls = []

        def spy(cmd, **kw):
            calls.append((cmd, kw))
            return real(cmd, **kw)
        secret = 'sk-live-0123456789abcdef'
        with patch.dict(os.environ, {'AWS_SECRET_ACCESS_KEY': secret, 'GIT_DIR': '/nonexistent', 'GIT_ASKPASS': '/bin/true',
                                     'SSH_AUTH_SOCK': '/x', 'GIT_EXTERNAL_DIFF': '/bin/true'}):
            adapter = self.adapter()
            with patch('ai_sdlc.native_git.subprocess.run', spy):
                files = self.write('a.txt', b'one\n')
                adapter.stage('s1', files)
                adapter.commit('c1', 'hygiene', files)
        self.assertTrue(calls)
        allowed = {'PATH', 'HOME', 'LC_ALL', 'GIT_CONFIG_NOSYSTEM', 'GIT_CONFIG_GLOBAL', 'GIT_TERMINAL_PROMPT',
                   'GIT_NO_REPLACE_OBJECTS', 'GIT_CEILING_DIRECTORIES', 'GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
                   'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL'}
        subcommands = set()
        for cmd, kw in calls:
            self.assertIsInstance(cmd, list)
            self.assertTrue(os.path.isabs(cmd[0]))
            self.assertIs(kw['shell'], False)
            self.assertLessEqual(set(kw['env']), allowed)
            self.assertNotIn(secret, kw['env'].values())
            self.assertEqual(kw['env']['GIT_TERMINAL_PROMPT'], '0')
            self.assertIn('core.hooksPath=/dev/null', cmd)
            subcommands.add(cmd[cmd.index(str(self.repo)) + 1])
        self.assertLessEqual(subcommands, ng.GitAdapter.COMMANDS)
        self.assertEqual(self.code(adapter._run, 'push', 'origin'), 'COMMAND_NOT_ALLOWED')
        self.assertEqual(self.code(adapter._run, 'reset', '--hard'), 'COMMAND_NOT_ALLOWED')

    def test_source_has_no_shell_network_or_remote_operations(self):
        source = Path(ng.__file__).read_text()
        for needle in ('shell=True', 'os.system', 'os.popen', 'socket', 'urllib', 'http.client', "'push'", "'fetch'", "'remote'",
                       "'--force'", "'reset'", "'clean'", "'--hard'", "'-D'"):
            self.assertNotIn(needle, source)
        ast.parse(source, feature_version=(3, 9))


if __name__ == '__main__':
    unittest.main()
