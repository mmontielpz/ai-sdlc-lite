"""Deterministic offline delivery contract and adversarial boundary tests."""
import ast
import copy
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from ai_sdlc import delivery as d


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.git = self.repo / '.git'
        (self.git / 'objects').mkdir(parents=True)
        (self.git / 'refs' / 'heads').mkdir(parents=True)
        (self.git / 'HEAD').write_text('ref: refs/heads/main\n')
        (self.git / 'refs' / 'heads' / 'main').write_text('a' * 40 + '\n')
        (self.git / 'config').write_text('[core]\nrepositoryformatversion = 0\nbare = false\n[remote "origin"]\nurl = https://example.invalid/owner/repo.git\n')
        (self.repo / 'a.txt').write_text('hello\n')
        self.request = dict(repository='https://example.invalid/owner/repo', expected_branch='main',
                            base_sha='a' * 40, head_sha='a' * 40, authorized_files=['a.txt'],
                            operations=['commit'], commit=dict(message='Fix a', signing='forbidden'),
                            remote=dict(name='origin', destination='https://example.invalid/owner/repo.git',
                                        expected_ref='refs/heads/main', expected_sha=None),
                            pull_request=dict(title='Fix a', body='', base='main', draft=True), required_ci=[],
                            authorization_ref='MISSION=test', executor='test-executor',
                            retry=dict(max_attempts=3, backoff_seconds=1))
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def make(self):
        return d.plan(self.repo, self.request)

    def rejected(self, action, code):
        with self.assertRaisesRegex(d.Rejected, '^' + code + '$'):
            action()

    def test_deterministic_digest_and_roundtrip(self):
        first, evidence = self.make()
        second, _ = self.make()
        self.assertEqual(first, second)
        self.assertEqual(evidence['status'], 'READY')
        self.assertEqual(d.verify(self.repo, first), evidence)
        self.assertEqual(evidence['authorization'], 'UNKNOWN')
        self.assertEqual(evidence['future_write_success'], 'UNKNOWN')
        self.assertEqual(first['authorized_state']['a.txt']['sha256'], first['snapshot']['files']['a.txt']['sha256'])

    def test_digest_is_not_authorization(self):
        value, _ = self.make()
        value['request']['authorization_ref'] = 'arbitrary claim'
        self.rejected(lambda: d.verify(self.repo, value), 'DIGEST_MISMATCH')
        value['digest'] = d.digest({k: v for k, v in value.items() if k != 'digest'})
        self.assertEqual(d.verify(self.repo, value)['authorization'], 'UNKNOWN')

    def test_changed_head(self):
        value, _ = self.make()
        (self.git / 'refs/heads/main').write_text('b' * 40)
        self.rejected(lambda: d.verify(self.repo, value), 'HEAD_CHANGED')

    def test_changed_branch(self):
        value, _ = self.make()
        (self.git / 'HEAD').write_text('ref: refs/heads/other\n')
        self.rejected(lambda: d.verify(self.repo, value), 'BRANCH_CHANGED')

    def test_content_drift(self):
        value, _ = self.make()
        (self.repo / 'a.txt').write_text('different')
        self.rejected(lambda: d.verify(self.repo, value), 'SNAPSHOT_CHANGED')

    def test_inventory_addition(self):
        value, _ = self.make()
        (self.repo / 'extra').write_text('new')
        self.rejected(lambda: d.verify(self.repo, value), 'SNAPSHOT_CHANGED')

    def test_inventory_deletion(self):
        value, _ = self.make()
        (self.repo / 'a.txt').unlink()
        self.rejected(lambda: d.verify(self.repo, value), 'SNAPSHOT_CHANGED')

    def test_executable_drift(self):
        value, _ = self.make()
        (self.repo / 'a.txt').chmod(0o755)
        self.rejected(lambda: d.verify(self.repo, value), 'SNAPSHOT_CHANGED')

    def test_authorized_deletion_is_explicit(self):
        self.request['authorized_files'] = ['deleted.txt']
        value, _ = self.make()
        self.assertEqual(value['authorized_state'], {'deleted.txt': None})

    def test_path_traversal_rejected(self):
        for path in ('../outside', '/tmp/a', 'a/../b', 'a//b', './a', '.git/config', 'a/.git/b', 'C:/a', 'a\\b', 'a\x1bb'):
            with self.subTest(path=path):
                self.request['authorized_files'] = [path]
                self.rejected(self.make, 'INVALID_INVENTORY')

    def test_symlink_file_escape(self):
        (self.repo / 'a.txt').unlink()
        (self.repo / 'a.txt').symlink_to('/etc/passwd')
        self.rejected(self.make, 'UNSAFE_PATH')

    def test_symlink_directory_escape(self):
        (self.repo / 'escape').symlink_to(self.repo.parent, target_is_directory=True)
        self.rejected(self.make, 'UNSAFE_PATH')

    def test_git_pointer_is_blocked(self):
        other = self.repo / 'other'
        self.git.rename(other)
        self.git.write_text('gitdir: other\n')
        self.rejected(self.make, 'UNSUPPORTED_GIT_LAYOUT')

    def test_git_ref_symlink_is_blocked(self):
        path = self.git / 'refs/heads/main'
        path.unlink()
        path.symlink_to('/etc/passwd')
        self.rejected(self.make, 'UNSAFE_PATH')

    def test_unsafe_configuration_matrix(self):
        initial = (self.git / 'config').read_text()
        for payload in ('[core]\nfsmonitor = evil', '[include]\npath = /etc/passwd',
                        '[includeIf "gitdir:*"]\npath = /etc/passwd', '[credential]\nhelper = evil',
                        '[filter "x"]\nclean = evil', '[core]\nhooksPath = /tmp/hooks',
                        '[gpg]\nprogram = evil', '[alias]\na = !evil', '[http]\nproxy = evil',
                        '[core]\nsshCommand = evil', '[extensions]\nworktreeConfig = true'):
            # Use an independent config to avoid duplicate-section parser failures.
            (self.git / 'config').write_text(payload)
            with self.subTest(payload=payload):
                self.rejected(self.make, 'UNSAFE_GIT_CONFIG')
        (self.git / 'config').write_text(initial)

    def test_active_hook_rejected(self):
        (self.git / 'hooks').mkdir()
        (self.git / 'hooks/pre-commit').write_text('#!/bin/sh\n')
        self.rejected(self.make, 'UNSAFE_GIT_HOOKS')

    def test_git_environment_rejected(self):
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1'}):
            self.rejected(self.make, 'UNSAFE_GIT_ENVIRONMENT')

    def test_remote_identity_mismatch(self):
        self.request['repository'] = 'https://example.invalid/other'
        self.rejected(self.make, 'INVALID_IDENTITY')

    def test_remote_configuration_mismatch(self):
        self.request['remote']['destination'] = 'https://example.invalid/other.git'
        self.request['repository'] = 'https://example.invalid/other'
        self.rejected(self.make, 'REMOTE_MISMATCH')

    def test_remote_credentials_and_helpers_rejected(self):
        for url in ('https://user:secret@example.invalid/a', 'ext::evil', '/tmp/remote', 'https://example.invalid/a?token=secret'):
            self.request['remote']['destination'] = url
            self.rejected(self.make, 'INVALID_REMOTE')

    def test_bounded_retry_and_operations(self):
        for attempts in (0, 4, True, '3'):
            self.request['retry']['max_attempts'] = attempts
            self.rejected(self.make, 'INVALID_RETRY')
        self.request['retry']['max_attempts'] = 3
        self.request['operations'] = ['merge']
        self.rejected(self.make, 'INVALID_OPERATIONS')

    def test_partial_external_preconditions(self):
        self.request['operations'] = ['commit', 'push', 'pull_request']
        self.request['commit']['signing'] = 'required'
        self.request['required_ci'] = ['tests']
        _, result = self.make()
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['remote_ref'], 'UNKNOWN')
        self.assertEqual(result['signing'], 'UNKNOWN')

    def test_write_access_blocked(self):
        with patch.object(d.os, 'access', return_value=False):
            value, result = self.make()
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertEqual(d.verify(self.repo, value)['reasons'], ['GIT_WRITE_BLOCKED'])

    def test_mode_read_only_detected_even_for_root(self):
        self.git.chmod(0o555)
        self.addCleanup(self.git.chmod, 0o755)
        self.assertEqual(self.make()[1]['git_write'], 'GIT_WRITE_BLOCKED')
        self.git.chmod(0o755)
        heads = self.git / 'refs/heads'
        heads.chmod(0o555)
        self.addCleanup(heads.chmod, 0o755)
        self.assertEqual(self.make()[1]['git_write'], 'GIT_WRITE_BLOCKED')

    def test_index_drift(self):
        value, _ = self.make()
        (self.git / 'index').write_bytes(b'changed')
        self.rejected(lambda: d.verify(self.repo, value), 'SNAPSHOT_CHANGED')

    def test_packed_ref(self):
        (self.git / 'refs/heads/main').unlink()
        (self.git / 'packed-refs').write_text('a' * 40 + ' refs/heads/main\n')
        self.assertEqual(self.make()[1]['status'], 'READY')

    def test_cli_all_commands_and_no_side_effects(self):
        source = self.repo.parent / 'request.json'
        source.write_text(json.dumps(self.request))
        def invoke(command):
            out = io.StringIO()
            with redirect_stdout(out):
                code = d.main([command, '--repo', str(self.repo), '--input', str(source)])
            return code, json.loads(out.getvalue())
        before = {str(p): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        original_open = os.open
        def read_only_open(path, flags, *args, **kwargs):
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            return original_open(path, flags, *args, **kwargs)
        import subprocess
        import socket
        from ai_sdlc import cli
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('subprocess')), \
             patch.object(socket, 'socket', side_effect=AssertionError('network')), \
             patch.object(os, 'open', side_effect=read_only_open), \
             patch.object(Path, 'write_text', side_effect=AssertionError('write')), \
             patch.object(Path, 'write_bytes', side_effect=AssertionError('write')):
            code, value = invoke('plan')
            self.assertEqual(code, 0)
            # Use a separate input file created before the guarded calls below.
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['delivery', 'plan', '--repo', str(self.repo), '--input', str(source)]), 0)
        source.write_text(json.dumps(value))
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('subprocess')), \
             patch.object(socket, 'socket', side_effect=AssertionError('network')), \
             patch.object(os, 'open', side_effect=read_only_open):
            verified = invoke('verify')
            self.assertEqual(invoke('report'), verified)
            self.assertEqual(verified[0], 0)
        after = {str(p): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_sanitized_errors_and_unknown(self):
        source = self.repo.parent / 'secret-name.json'
        source.write_text('{"secret":"\u001b"}')
        out = io.StringIO()
        with redirect_stdout(out):
            code = d.main(['plan', '--repo', str(self.repo), '--input', str(source)])
        self.assertEqual(code, 3)
        self.assertNotIn('secret', out.getvalue())
        self.assertNotIn('\x1b', out.getvalue())
        self.assertEqual(json.loads(out.getvalue())['status'], 'UNKNOWN')

    def test_duplicate_json_keys_rejected(self):
        source = self.repo.parent / 'input.json'
        source.write_text('{"a":1,"a":2}')
        self.rejected(lambda: d.load(source), 'DUPLICATE_KEY')

    def test_schema_rejects_unknown_provider_authority(self):
        self.request['provider_adapter'] = {'permission': True}
        self.rejected(self.make, 'INVALID_CONTRACT')

    def test_known_credential_store_not_opened(self):
        secret = self.repo / '.git-credentials'
        secret.write_text('do not read')
        original = d.read
        def guarded(path):
            self.assertNotEqual(Path(path), secret)
            return original(path)
        with patch.object(d, 'read', side_effect=guarded):
            self.rejected(self.make, 'CREDENTIAL_STORE_IN_INVENTORY')

    def test_fifo_is_rejected_without_opening(self):
        os.mkfifo(self.repo / 'fifo')
        self.rejected(self.make, 'UNSAFE_FILE')

    def test_broken_config_worktree_link_rejected(self):
        (self.git / 'config.worktree').symlink_to('/nonexistent/delivery-secret')
        self.rejected(self.make, 'UNSAFE_GIT_CONFIG')

    def test_python39_and_import_boundary(self):
        path = Path(d.__file__)
        tree = ast.parse(path.read_text(), feature_version=(3, 9))
        forbidden = {'subprocess', 'socket', 'urllib', 'http', 'ssl', 'requests', 'adapters'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(forbidden.intersection(a.name.split('.')[0] for a in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or '').split('.')[0], forbidden)


if __name__ == '__main__':
    unittest.main()
