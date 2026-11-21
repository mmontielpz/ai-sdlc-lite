"""Offline init behavior and security regressions in disposable ordinary Git roots."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ai_sdlc import initializer as init


def snapshot(root):
    result = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            info = path.lstat()
            value = None
            if stat.S_ISLNK(info.st_mode):
                value = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                value = (path.read_bytes(), info.st_mtime_ns)
            elif stat.S_ISDIR(info.st_mode):
                value = info.st_mtime_ns
            result[path.relative_to(root).as_posix()] = (stat.S_IFMT(info.st_mode), value)
    return result


class InitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-init-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'project with spaces'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.outside = self.base / 'outside'
        self.outside.mkdir()
        (self.outside / 'canary').write_bytes(b'OUTSIDE-CANARY')
        self.outside_before = snapshot(self.outside)
        self.installer = init._installer()
        self.content, self.hashes = self.installer.bundle_content()
        self.destination = self.repo / self.installer.SKILL
        (self.repo / 'AGENTS.md').write_text('Preserve project rules.\n')
        (self.repo / 'TASK.md').write_text('Preserve the authoritative task.\n')

    def invoke(self, *args, repo=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), \
                patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')), \
                patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
            code = init.main(['--repo', str(repo or self.repo), *args])
        self.assertEqual(self.outside_before, snapshot(self.outside))
        return code, out.getvalue(), err.getvalue()

    def install(self):
        code, out, err = self.invoke('--apply')
        self.assertEqual(code, 0, err)
        self.assertIn('RESULT: INITIALIZED', out)

    def reject_unchanged(self, *args, repo=None):
        before = snapshot(self.repo)
        code, out, err = self.invoke(*args, repo=repo)
        self.assertEqual(code, 2, (out, err))
        self.assertEqual(before, snapshot(self.repo))
        return out, err

    def test_default_and_explicit_preview_write_nothing(self):
        before = snapshot(self.repo)
        first = self.invoke()
        self.assertEqual(first[0], 0, first)
        self.assertEqual(first, self.invoke('--dry-run'))
        self.assertEqual(before, snapshot(self.repo))
        self.assertIn('RESULT: PREVIEW', first[1])
        self.assertFalse((self.repo / '.agents').exists())

    def test_apply_matches_every_preview_hash_and_preserves_project(self):
        before = snapshot(self.repo)
        _, preview, _ = self.invoke()
        lines = [line for line in preview.splitlines() if line.startswith('CREATE ')]
        self.assertEqual(len(lines), len(self.content))
        self.assertEqual(lines, sorted(lines))
        code, output, err = self.invoke('--apply')
        self.assertEqual(code, 0, err)
        self.assertEqual(output.split('RESULT:')[0], preview.split('RESULT:')[0])
        for line in lines:
            name, sha = line[7:].rsplit(' sha256=', 1)
            path = self.repo / json.loads(name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        after = snapshot(self.repo)
        self.assertTrue(all(after[name] == value for name, value in before.items()))
        self.assertTrue(all(name in before or name == '.agents' or name == '.agents/skills'
                            or name.startswith(self.installer.SKILL.as_posix()) for name in after))
        for name, data in self.content.items():
            self.assertEqual((self.destination / name).read_bytes(), data)

    def test_rerun_and_check_preserve_bytes_and_timestamps(self):
        self.install()
        before = snapshot(self.repo)
        for args in ((), ('--dry-run',), ('--apply',), ('--check',)):
            code, out, err = self.invoke(*args)
            self.assertEqual(code, 0, err)
            self.assertIn('CHECK_OK' if args == ('--check',) else 'UNCHANGED', out)
            self.assertEqual(before, snapshot(self.repo))

    def test_check_missing_installation_creates_nothing(self):
        self.reject_unchanged('--check')

    def test_existing_single_file_installation_refused(self):
        self.destination.mkdir(parents=True)
        (self.destination / 'SKILL.md').write_bytes(b'user skill')
        for args in ((), ('--apply',), ('--check',)):
            self.reject_unchanged(*args)

    def test_conflicting_files_missing_files_and_extra_directories(self):
        self.install()
        target = self.destination / 'SKILL.md'
        target.write_bytes(b'user edits')
        self.reject_unchanged('--apply')
        self.reject_unchanged('--check')
        target.unlink()
        self.reject_unchanged('--apply')
        target.write_bytes(self.content['SKILL.md'])
        extra = self.destination / 'unowned'
        extra.mkdir()
        self.reject_unchanged('--apply')
        (extra / 'user.txt').write_bytes(b'user data')
        self.reject_unchanged('--check')

    def test_untrusted_manifest_variants_preserved(self):
        self.install()
        original = json.loads(self.content[self.installer.MANIFEST])
        variants = [b'[]', b'{', b'{"format":1,"format":1,"files":{}}',
                    b'{"format":1,"files":{"a":0,"a":1}}', b'x' * (init.MAX_MANIFEST + 1)]
        for changes in ({'format': True}, {'format': 2}, {'unknown': 'value'}, {'files': []}):
            variants.append(json.dumps(dict(original, **changes)).encode())
        for name in ('../outside', '/outside', 'framework/../escape', 'framework//bad',
                     'framework/./bad', 'framework/back\\slash', 'framework/nul\x00', '',
                     'framework', 'framework/LICENSE/child'):
            record = dict(original, files=dict(original['files'], **{name: 'a' * 64}))
            variants.append(json.dumps(record).encode())
        for raw in variants:
            with self.subTest(raw=raw[:50]):
                (self.destination / self.installer.MANIFEST).write_bytes(raw)
                self.reject_unchanged('--apply')
                self.reject_unchanged('--check')

    def test_forged_manifest_does_not_authorize_edited_bundle(self):
        self.install()
        edited = b'edited skill'
        (self.destination / 'SKILL.md').write_bytes(edited)
        record = json.loads(self.content[self.installer.MANIFEST])
        record['files']['SKILL.md'] = self.installer.digest(edited)
        (self.destination / self.installer.MANIFEST).write_text(json.dumps(record))
        self.reject_unchanged('--apply')

    def test_symlink_destination_ancestors_and_dangling_links(self):
        for relative in ('.agents', '.agents/skills', self.installer.SKILL.as_posix()):
            link = self.repo / relative
            link.parent.mkdir(parents=True, exist_ok=True)
            for target in (self.outside, self.base / 'missing'):
                with self.subTest(relative=relative, target=str(target)):
                    link.symlink_to(target, target_is_directory=True)
                    self.reject_unchanged('--apply')
                    self.reject_unchanged('--check')
                    link.unlink()

    def test_root_and_root_ancestor_symlinks_refused(self):
        link = self.base / 'link'
        link.symlink_to(self.repo, target_is_directory=True)
        self.reject_unchanged('--apply', repo=link)
        parent = self.base / 'parent-link'
        parent.symlink_to(self.base, target_is_directory=True)
        self.reject_unchanged('--apply', repo=parent / self.repo.name)

    def test_leaf_symlink_and_hardlink_refused_without_reading(self):
        self.install()
        path = self.destination / 'SKILL.md'
        path.unlink()
        for kind in ('symlink', 'hardlink'):
            if kind == 'symlink':
                path.symlink_to(self.outside / 'canary')
            else:
                os.link(self.outside / 'canary', path)
            self.reject_unchanged('--check')
            path.unlink()

    def test_special_file_destination_and_leaf_refused(self):
        self.destination.parent.mkdir(parents=True)
        os.mkfifo(self.destination)
        self.reject_unchanged('--apply')
        self.destination.unlink()
        self.install()
        leaf = self.destination / 'SKILL.md'
        leaf.unlink()
        os.mkfifo(leaf)
        self.reject_unchanged('--check')

    def test_regular_file_ancestor_refused(self):
        (self.repo / '.agents').write_bytes(b'preserve me')
        self.reject_unchanged('--apply')

    def test_git_pointer_external_metadata_and_missing_git_refused(self):
        other = self.base / 'not-a-repo'
        other.mkdir()
        self.reject_unchanged('--apply', repo=other)
        dot = other / '.git'
        dot.write_text('gitdir: ' + str(self.repo / '.git'))
        self.reject_unchanged('--apply', repo=other)
        (self.repo / '.git/commondir').write_text(str(self.outside))
        self.reject_unchanged('--apply')

    def test_git_head_symlink_fifo_and_oversized_refused(self):
        head = self.repo / '.git/HEAD'
        head.unlink()
        head.symlink_to(self.outside / 'canary')
        self.reject_unchanged('--apply')
        head.unlink()
        os.mkfifo(head)
        self.reject_unchanged('--apply')
        head.unlink()
        head.write_bytes(b'x' * 513)
        self.reject_unchanged('--apply')

    def test_dirty_unborn_and_detached_repositories_supported(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.repo / 'untracked').write_text('dirty')
        (self.repo / '.git/HEAD').write_text('a' * 40 + '\n')
        self.install()

    def test_subdirectory_and_framework_overlap_refused(self):
        child = self.repo / 'child'
        child.mkdir()
        self.reject_unchanged('--apply', repo=child)
        for path in (ROOT, ROOT / 'tests', ROOT.parent):
            self.reject_unchanged('--apply', repo=path)

    def test_traversal_refused(self):
        self.reject_unchanged('--apply', repo=str(self.repo / '..' / self.repo.name))

    def test_no_provider_network_project_import_or_secret_output(self):
        canary = 'INIT-SECRET-CANARY'
        (self.repo / 'install_skill.py').write_text("raise RuntimeError('target code executed')")
        (self.repo / '.env').write_text(canary)
        (self.repo / 'package.json').write_text('{ malformed; never inspect me')
        context = self.repo / '.ai-sdlc-lite'
        context.mkdir()
        (context / 'task-context.json').write_text('{ malformed and nonblocking')
        with (self.repo / '.git/config').open('a') as stream:
            stream.write('\n[core]\n fsmonitor = ' + canary + '\n[filter "bad"]\n process = ' + canary)
        with patch.dict(os.environ, {'GIT_DIR': str(self.outside), 'GIT_CONFIG_COUNT': '999',
                                    'COPILOT_HOME': str(self.outside), 'API_KEY': canary}), \
                patch.object(init, '_installer', return_value=self.installer), \
                patch.object(self.installer, 'preflight', side_effect=AssertionError('preflight forbidden')), \
                patch.object(self.installer, 'readiness', side_effect=AssertionError('provider forbidden')), \
                patch.object(self.installer, 'workspace', side_effect=AssertionError('context forbidden')):
            for args in ((), ('--apply',), ('--check',)):
                code, out, err = self.invoke(*args)
                self.assertEqual(code, 0, err)
                self.assertNotIn(canary, out + err)

    def test_control_characters_in_paths_are_escaped(self):
        target = self.base / 'unsafe\x1b[31m\u202e'
        self.repo.rename(target)
        self.repo = target
        code, out, err = self.invoke()
        self.assertEqual(code, 0, err)
        self.assertNotIn('\x1b', out + err)
        self.assertNotIn('\u202e', out + err)
        self.assertIn('\\u001b', out)

    def test_interrupt_after_manifest_preserves_files_and_refuses_rerun(self):
        original = init._write_file
        calls = []

        def interrupted(fd, name, data):
            calls.append(name)
            if len(calls) == 2:
                raise OSError('PRIVATE-ERROR-CANARY')
            original(fd, name, data)

        with patch.object(init, '_write_file', side_effect=interrupted):
            code, out, err = self.invoke('--apply')
        self.assertEqual(code, 1)
        self.assertIn('PARTIAL', err)
        self.assertNotIn('PRIVATE-ERROR-CANARY', out + err)
        self.assertEqual(calls[0], self.installer.MANIFEST)
        self.assertEqual((self.destination / calls[0]).read_bytes(), self.content[calls[0]])
        self.reject_unchanged('--apply')
        self.reject_unchanged('--check')

    def test_interrupt_mid_file_preserves_partial_bytes(self):
        original = init._write_file

        def interrupted(fd, name, data):
            if name != self.installer.MANIFEST:
                original(fd, name, data[:7])
                raise OSError('interrupted')
            original(fd, name, data)

        with patch.object(init, '_write_file', side_effect=interrupted):
            self.assertEqual(self.invoke('--apply')[0], 1)
        self.reject_unchanged('--apply')

    def test_symlink_substitution_after_preview_cannot_escape(self):
        original = init._apply

        def swapped(fd, content, installer, skill):
            (self.repo / '.agents').symlink_to(self.outside, target_is_directory=True)
            original(fd, content, installer, skill)

        with patch.object(init, '_apply', side_effect=swapped):
            self.assertEqual(self.invoke('--apply')[0], 1)
        self.assertEqual(self.outside_before, snapshot(self.outside))

    def test_exclusive_create_preserves_racing_leaf(self):
        original = init._write_file

        def racing(fd, name, data):
            if name == self.installer.MANIFEST:
                original(fd, name, b'user-race')
            original(fd, name, data)

        with patch.object(init, '_write_file', side_effect=racing):
            self.assertEqual(self.invoke('--apply')[0], 1)
        self.assertEqual((self.destination / self.installer.MANIFEST).read_bytes(), b'user-race')

    def test_read_only_target_and_missing_primitives(self):
        self.repo.chmod(0o555)
        try:
            self.assertEqual(self.invoke('--apply')[0], 1)
            self.assertFalse((self.repo / '.agents').exists())
        finally:
            self.repo.chmod(0o755)
        with patch.object(init, '_supported', return_value=False):
            self.reject_unchanged('--apply')

    def test_inventory_limits_fail_closed(self):
        self.install()
        with patch.object(init, 'MAX_ENTRIES', 1):
            self.reject_unchanged('--check')

    def test_cli_dispatch_help_errors_and_foreign_cwd(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
        for args, expected in ((['--help'], 0), ([], 2), (['--repo', str(self.repo)], 0),
                               (['--repo', str(self.repo), '--apply', '--check'], 2),
                               (['--repo', str(self.repo), '--dry-run', '--dry-run'], 2),
                               (['--repo', str(self.repo), '--repo', str(self.repo)], 2),
                               (['--repo', str(self.repo), '--force'], 2)):
            before = snapshot(self.repo)
            result = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'init', *args],
                                    cwd=self.outside, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual(before, snapshot(self.repo))

    def test_linked_git_worktree_supported_and_spoofed_backlink_refused(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.name', 'Test'], env=env, check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.email', 'test@example.com'], env=env, check=True)
        (self.repo / 'README.md').write_text('hi\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', 'README.md'], env=env, check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-q', '-m', 'init'], env=env, check=True)
        wt = self.base / 'linked-wt'
        subprocess.run(['git', '-C', str(self.repo), 'worktree', 'add', '-q', str(wt), '-b', 'wt-branch'], env=env, check=True)
        code, out, err = self.invoke('--target', 'claude-code', '--apply', repo=wt)
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: INITIALIZED', out)
        code, out, err = self.invoke('--target', 'claude-code', '--check', repo=wt)
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: CHECK_OK', out)
        # Spoofed backlink must be rejected
        gitdir_meta = self.repo / '.git' / 'worktrees' / 'linked-wt' / 'gitdir'
        gitdir_meta.write_text(str(self.outside / '.git') + '\n')
        self.reject_unchanged('--check', repo=wt)

    def test_uninstall_and_upgrade_lifecycle_and_user_edit_protection(self):
        # Uninstall when absent succeeds cleanly
        code, out, err = self.invoke('--uninstall')
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: NOT_INSTALLED', out)
        # Upgrade when absent installs fresh
        code, out, err = self.invoke('--upgrade')
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: INITIALIZED', out)
        # Upgrade when current is UNCHANGED
        code, out, err = self.invoke('--upgrade')
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: UNCHANGED', out)
        # User-modified file blocks both --uninstall and --upgrade without touching files
        skill_md = self.destination / 'SKILL.md'
        original = skill_md.read_bytes()
        skill_md.write_bytes(original + b'\n# user edit\n')
        self.reject_unchanged('--uninstall')
        self.reject_unchanged('--upgrade')
        self.assertTrue(skill_md.is_file())
        # Extra file also blocks --uninstall and --upgrade
        skill_md.write_bytes(original)
        extra = self.destination / 'extra.txt'
        extra.write_text('keep')
        self.reject_unchanged('--uninstall')
        self.reject_unchanged('--upgrade')
        extra.unlink()
        # Simulate intact older managed bundle (valid manifest with older SKILL.md hash)
        import hashlib, json as _json
        older = b'# older skill\n'
        (self.destination / 'SKILL.md').write_bytes(older)
        manifest_path = self.destination / self.installer.MANIFEST
        manifest = _json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['files']['SKILL.md'] = hashlib.sha256(older).hexdigest()
        manifest_path.write_text(_json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        # --apply still refuses version conflict; --upgrade replaces cleanly
        self.reject_unchanged('--apply')
        code, out, err = self.invoke('--upgrade')
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: UPGRADED', out)
        code, out, err = self.invoke('--check')
        self.assertEqual(code, 0, out + err)
        # --uninstall removes intact bundle cleanly and leaves repo clean
        code, out, err = self.invoke('--uninstall')
        self.assertEqual(code, 0, out + err)
        self.assertIn('RESULT: UNINSTALLED', out)
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
