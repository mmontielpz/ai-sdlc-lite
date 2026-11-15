"""Opt-in delivery execution for ai-sdlc-delivery/1.

Approval, durable journal and remote transport are trusted host capabilities.
There is deliberately no CLI that treats JSON authorization claims as authority.
"""
import copy
import os
from pathlib import Path
import shutil
import subprocess

from . import delivery as d
from .native_git import GitAdapter, decoded


class Executor:
    """Single-writer executor. Host must serialize repository and journal access.

    approve receives an exact intent and must return True from a trusted human
    decision. journal exposes read(key) and write(key, value), durably before
    returning. remote exposes ref(destination, ref), push(destination, ref, sha,
    expected), find_pr(identity), create_pr(identity). Read errors must raise;
    absence is None. Remote implementations must enforce non-force updates,
    avoid retries, redact errors and never invoke merge.

    Optional git_adapter (a native_git.GitAdapter) takes over local staging and
    committing: the executor then runs no mutating Git command itself. Its journal is
    the durable local record; both the executor's approve and the adapter's authorizer
    must approve each mutation. attempt (1-9) selects the operation-id generation; raise
    it only on an explicit owner decision to retry a retired (failed/not-applied) operation.
    """

    def __init__(self, repo, plan, approve, journal, remote=None, git_adapter=None, attempt=1):
        self.repo = Path(repo).absolute()
        self.plan = copy.deepcopy(plan)
        self.approve = approve
        self.journal = journal
        self.remote = remote
        self.git_adapter = git_adapter
        self.attempt = attempt
        d.keys(self.plan, 'contract request snapshot authorized_state digest')
        d.require(self.plan['contract'] == d.CONTRACT, 'UNSUPPORTED_CONTRACT')
        d.require(self.plan['digest'] == d.digest({k: v for k, v in self.plan.items() if k != 'digest'}), 'DIGEST_MISMATCH')
        d.validate_request(self.plan['request'])
        self.request = self.plan['request']
        d.require(self.plan['authorized_state'] == {p: self.plan['snapshot']['files'].get(p)
                  for p in self.request['authorized_files']}, 'INVALID_AUTHORIZED_STATE')
        self.git = shutil.which('git')
        d.require(self.git is not None, 'GIT_UNAVAILABLE')
        if git_adapter is not None:
            d.require(type(attempt) is int and 1 <= attempt <= 9, 'INVALID_ADAPTER')
            # The adapter has no deletion operation; never degrade silently.
            d.require(all(s is not None for s in self.plan['authorized_state'].values()), 'ADAPTER_UNSUPPORTED_DELETION')
            self._check_adapter()

    def _check_adapter(self):
        adapter = self.git_adapter
        d.require(isinstance(adapter, GitAdapter), 'INVALID_ADAPTER')
        d.require(os.path.abspath(str(self.repo)) == str(adapter.repo) and adapter.repository == self.request['repository']
                  and adapter.branch == self.request['expected_branch'], 'ADAPTER_MISMATCH')

    def _operation_id(self, operation):
        return '%s-%s-a%d' % (self.plan['digest'], operation, self.attempt)

    def _reconcile(self):
        """Verify the durable journal and reconcile interrupted operations; ambiguity blocks."""
        journal = self.git_adapter.journal
        journal.verify()
        if journal.pending():
            self.git_adapter.recover()
        d.require(not journal.unresolved(), 'RECOVERY_AMBIGUOUS')

    def _git(self, *args):
        # Exclude inherited Git, credentials, global config and executable hooks.
        env = {'PATH': os.defpath, 'HOME': '/dev/null', 'LC_ALL': 'C',
               'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
               'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1'}
        try:
            result = subprocess.run([self.git, '-c', 'core.hooksPath=/dev/null',
                                     '-c', 'core.fsmonitor=false', '-C', str(self.repo), *args],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=60, check=False)
        except (OSError, subprocess.SubprocessError):
            raise d.Rejected('GIT_OUTCOME_UNKNOWN') from None
        d.require(result.returncode == 0, 'GIT_FAILED')
        return result.stdout

    def _state(self):
        # Reuse all planner safety checks, allowing only our index/HEAD transition.
        request = copy.deepcopy(self.request)
        request['head_sha'] = self._head_from_disk()
        observed, writable = d.snapshot(self.repo, request)
        expected = copy.deepcopy(self.plan['snapshot'])
        expected['head_sha'] = observed['head_sha']
        expected['index_sha256'] = observed['index_sha256']
        d.require(observed == expected, 'SNAPSHOT_CHANGED')
        d.require(writable, 'GIT_WRITE_BLOCKED')
        # Attributes can select executable filters and affect staged bytes.
        d.require(not any(Path(p).name == '.gitattributes' for p in observed['files']), 'ATTRIBUTES_UNSUPPORTED')
        git = self.repo / '.git'
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'shallow', 'info/grafts', 'info/attributes', 'refs/replace'):
            d.require(not d.present(git / name), 'UNSAFE_GIT_STATE')
        return observed['head_sha']

    def _head_from_disk(self):
        # No Git execution until local config/environment has been validated.
        request = self.request
        target = self.repo / '.git' / ('refs/heads/' + request['expected_branch'])
        if d.present(target):
            value = d.read(target).decode('ascii').strip()
        else:
            value = request['head_sha']  # packed baseline handled by snapshot
        d.require(d.oid(value), 'INVALID_SHA')
        return value

    def _intent(self, operation, sha):
        intent = {'operation': operation, 'plan_digest': self.plan['digest'],
                  'repository': self.request['repository'], 'head_sha': sha,
                  'authorized_files': self.request['authorized_files']}
        d.require(self.approve(copy.deepcopy(intent)) is True, 'APPROVAL_REQUIRED')

    def _names(self, *args):
        return sorted(decoded(p) for p in self._git(*args).split(b'\0') if p)

    def _staged(self):
        return self._names('diff', '--cached', '--name-only', '--no-renames', '-z')

    def _verify_tree(self, tree):
        for path, state in self.plan['authorized_state'].items():
            entry = (self._git('--literal-pathspecs', 'ls-files', '--stage', '-z', '--', path) if tree is None
                     else self._git('--literal-pathspecs', 'ls-tree', '-z', tree, '--', path))
            if state is None:
                d.require(not entry, 'STAGED_STATE_CHANGED')
                continue
            fields = entry.split(b'\t', 1)[0].split()
            if tree is None and len(fields) == 3 and fields[2] == b'0':
                fields = [fields[0], b'blob', fields[1]]
            d.require(len(fields) == 3 and fields[0] == (b'100755' if state['executable'] else b'100644')
                      and fields[1] == b'blob', 'STAGED_STATE_CHANGED')
            import hashlib
            data = self._git('cat-file', 'blob', decoded(fields[2], 'ascii'))
            d.require(hashlib.sha256(data).hexdigest() == state['sha256'], 'STAGED_STATE_CHANGED')

    @staticmethod
    def _refuse_retired(status):
        # Failed, not-applied and ambiguous operations are never retried automatically,
        # and the refusal happens before any approval is requested.
        codes = {'failed': 'OPERATION_ID_REUSED', 'not_applied': 'OPERATION_NOT_APPLIED', 'ambiguous': 'OPERATION_AMBIGUOUS'}
        d.require(status not in codes, codes.get(status, ''))

    def _commit_native(self, head):
        """Stage and commit through the injected adapter. Never retries a retired operation."""
        base = self.request['head_sha']
        adapter = self.git_adapter
        files = {p: dict(s) for p, s in self.plan['authorized_state'].items()}
        stage_id, commit_id = self._operation_id('stage'), self._operation_id('commit')
        staged = self._staged()
        status = adapter.journal.operation(stage_id)[0]
        self._refuse_retired(status)
        if status == 'applied':
            pass  # resume after an interruption; the staged state is re-proven below
        else:
            d.require(not staged, 'INDEX_NOT_EMPTY')
            d.verify(self.repo, self.plan)
            self._intent('stage', head)
            d.require(self._state() == base, 'HEAD_CHANGED')
            adapter.stage(stage_id, files)
        d.require(self._staged() == self.request['authorized_files'], 'STAGED_FILES_MISMATCH')
        self._verify_tree(None)
        self._refuse_retired(adapter.journal.operation(commit_id)[0])
        self._intent('commit', head)
        d.require(self._state() == base, 'HEAD_CHANGED')
        adapter.commit(commit_id, self.request['commit']['message'], files)
        d.require(self._state() != base, 'COMMIT_NOT_OBSERVED')
        return self.commit()

    def commit(self):
        if self.git_adapter is not None:
            self._check_adapter()
            self._reconcile()
        head = self._state()
        base = self.request['head_sha']
        d.require(self.request['base_sha'] == base, 'BASE_MISMATCH')
        d.require(self.request['commit']['signing'] == 'forbidden', 'SIGNING_UNSUPPORTED')
        if head != base:
            # Recovery proves actual commit identity; never trusts a saved receipt.
            parent = decoded(self._git('rev-list', '--parents', '-n', '1', head), 'ascii').split()
            d.require(parent == [head, base], 'COMMIT_IDENTITY_MISMATCH')
            message = decoded(self._git('show', '-s', '--format=%B', head)).rstrip('\n')
            d.require(message == self.request['commit']['message'], 'COMMIT_IDENTITY_MISMATCH')
            d.require(self._names('diff-tree', '--no-commit-id', '--name-only', '--no-renames', '-r', '-z', head)
                      == self.request['authorized_files'], 'COMMIT_FILES_MISMATCH')
            self._verify_tree(head)
            d.require(not self._git('status', '--porcelain', '--untracked-files=all'), 'WORKTREE_CHANGED')
            return head
        if self.git_adapter is not None:
            return self._commit_native(head)
        staged = self._staged()
        key = self.plan['digest'] + ':stage'
        if staged:
            d.require(self.journal.read(key) == 'pending' and staged == self.request['authorized_files'], 'INDEX_NOT_EMPTY')
        else:
            d.verify(self.repo, self.plan)
            self._intent('stage', head)
            d.require(self._state() == base, 'HEAD_CHANGED')
            d.require(not self._staged(), 'INDEX_NOT_EMPTY')
            self.journal.write(key, 'pending')
            self._git('--literal-pathspecs', 'add', '-A', '--', *self.request['authorized_files'])
        d.require(self._staged() == self.request['authorized_files'], 'STAGED_FILES_MISMATCH')
        self._verify_tree(None)
        self._intent('commit', head)
        d.require(self._state() == base, 'HEAD_CHANGED')
        d.require(self._staged() == self.request['authorized_files'], 'STAGED_FILES_MISMATCH')
        self._verify_tree(None)
        self._git('commit', '--no-gpg-sign', '-m', self.request['commit']['message'])
        return self.commit()

    def _remote_step(self, operation, identity, observe, mutate, desired):
        d.require(operation in self.request['operations'] and self.remote is not None, 'REMOTE_UNAVAILABLE')
        key = self.plan['digest'] + ':' + operation
        try:
            actual = observe()
        except Exception:
            raise d.Rejected('REMOTE_STATE_UNKNOWN') from None
        if desired(actual):
            return actual
        d.require(self.journal.read(key) is None, 'REMOTE_OUTCOME_AMBIGUOUS')
        self._intent(operation, identity['head_sha'])
        d.require(self._state() == identity['head_sha'], 'HEAD_CHANGED')
        self.journal.write(key, 'pending')
        try:
            mutate(actual)
            actual = observe()
            d.require(desired(actual), 'REMOTE_IDENTITY_MISMATCH')
        except Exception:
            raise d.Rejected('REMOTE_OUTCOME_AMBIGUOUS') from None
        self.journal.write(key, 'complete')
        return actual

    def push(self):
        d.require('push' in self.request['operations'] and self.remote is not None, 'REMOTE_UNAVAILABLE')
        d.require(not self.request['required_ci'], 'CI_UNSUPPORTED')
        sha = self.commit()
        remote = self.request['remote']
        d.require(remote['expected_ref'] == 'refs/heads/' + self.request['expected_branch'], 'REMOTE_REF_MISMATCH')
        def mutate(actual):
            d.require(actual == remote['expected_sha'], 'REMOTE_CHANGED')
            # Backend must compare expected atomically and never force updates.
            self.remote.push(remote['destination'], remote['expected_ref'], sha, actual)
        return self._remote_step('push', {'head_sha': sha},
                                 lambda: self.remote.ref(remote['destination'], remote['expected_ref']),
                                 mutate, lambda actual: actual == sha)

    def pull_request(self):
        d.require('pull_request' in self.request['operations'] and self.remote is not None, 'REMOTE_UNAVAILABLE')
        sha = self.push()
        identity = dict(self.request['pull_request'], repository=self.request['repository'],
                        head=self.request['expected_branch'], head_sha=sha)
        def desired(actual):
            if actual is None:
                return False
            d.require(actual == identity, 'PR_IDENTITY_MISMATCH')
            return True
        return self._remote_step('pull_request', identity,
                                 lambda: self.remote.find_pr(copy.deepcopy(identity)),
                                 lambda actual: self.remote.create_pr(copy.deepcopy(identity)), desired)
