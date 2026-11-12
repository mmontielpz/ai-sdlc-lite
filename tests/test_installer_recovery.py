"""Recovery safety in disposable repositories; no real Copilot configuration."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery_installer', ROOT / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-lite-recovery-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '--quiet', str(self.repo)], check=True)
        self.home = Path(self.temp.name) / 'isolated-home'
        self.home.mkdir()
        self.outside = Path(self.temp.name) / 'outside.txt'
        self.outside.write_text('Preserve outside scope.\n')
        (self.repo / 'app.txt').write_text('Preserve project code.\n')
        (self.repo / 'tasks/history').mkdir(parents=True)
        (self.repo / 'tasks/history/RESULT.md').write_text('Preserve task history.\n')
        self.destination = self.repo / installer.SKILL

    def invoke(self, *args, recovery=False):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), \
                patch.object(installer, 'preflight', side_effect=AssertionError('Recovery ran preflight') if recovery else None), \
                patch.object(installer, 'readiness', return_value=0):
            return_code = installer.main(['--target', str(self.repo), *args])
        self.assertEqual(self.outside.read_text(), 'Preserve outside scope.\n')
        return return_code, output.getvalue()

    def snapshot(self):
        return {p.relative_to(self.repo).as_posix(): p.read_bytes()
                for p in self.repo.rglob('*') if p.is_file() and not p.is_symlink()}

    def install(self):
        code, output = self.invoke()
        self.assertEqual(code, 0, output)

    def stale_context(self):
        marker = self.repo / installer.CONTEXT
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('{"contract":"missing.md"}\n')

    def test_stale_context_and_malformed_package_do_not_block_uninstall(self):
        self.install()
        self.stale_context()
        (self.repo / 'package.json').write_text('{ malformed package metadata\n')
        before = {p: data for p, data in self.snapshot().items()
                  if not p.startswith(installer.SKILL.as_posix() + '/')}
        code, output = self.invoke('--uninstall', recovery=True)
        self.assertEqual(code, 0, output)
        self.assertFalse(self.destination.exists())
        self.assertEqual(before, self.snapshot())

    def test_stale_context_does_not_block_verified_config_rollback(self):
        settings = self.home / 'settings.json'
        original = b'{ "theme": "dark" }\n'
        settings.write_bytes(original)
        self.assertEqual(self.invoke('--configure-copilot', '--copilot-home', str(self.home))[0], 0)
        self.stale_context()
        (self.repo / 'package.json').write_text('{ invalid\n')
        self.assertEqual(self.invoke('--rollback-config', '--copilot-home', str(self.home), recovery=True)[0], 0)
        self.assertEqual(settings.read_bytes(), original)

    def test_stale_context_does_not_weaken_later_edit_guard(self):
        self.assertEqual(self.invoke('--configure-copilot', '--copilot-home', str(self.home))[0], 0)
        self.stale_context()
        settings = self.home / 'settings.json'
        settings.write_text('{"theme":"later user edit"}\n')
        before = settings.read_bytes()
        self.assertEqual(self.invoke('--rollback-config', '--copilot-home', str(self.home), recovery=True)[0], 1)
        self.assertEqual(settings.read_bytes(), before)
        self.assertTrue((self.home / installer.CONFIG_BACKUP).is_file())

    def test_missing_backup_never_claims_configuration_restoration(self):
        self.stale_context()
        code, output = self.invoke('--rollback-config', '--copilot-home', str(self.home), recovery=True)
        self.assertEqual(code, 1)
        self.assertIn('No configuration backup exists', output)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_preview_lists_exact_files_and_owned_directories_without_writing(self):
        self.install()
        before = self.snapshot()
        code, output = self.invoke('--uninstall', '--dry-run', recovery=True)
        self.assertEqual(code, 0, output)
        removal_lines = [line.strip() for line in output.splitlines() if line.startswith('  REMOVE ')]
        actual_paths = {line.removeprefix('REMOVE ') for line in removal_lines}
        self.assertEqual(actual_paths, {str(p) for p in self.destination.rglob('*') if p.is_file()})
        self.assertIn('RMDIR ' + str(self.destination), output)
        self.assertEqual(before, self.snapshot())

    def test_modified_and_unowned_files_survive_repeated_uninstall(self):
        self.install()
        edited = self.destination / 'framework/TASK.md'
        edited.write_text('User modification\n')
        notes = self.destination / 'notes.txt'
        notes.write_text('User notes\n')
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
        self.assertEqual(edited.read_text(), 'User modification\n')
        self.assertEqual(notes.read_text(), 'User notes\n')
        self.assertTrue((self.destination / installer.MANIFEST).is_file())
        after = self.snapshot()
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
        self.assertEqual(after, self.snapshot())

    def test_unowned_empty_directory_is_preserved(self):
        self.install()
        directory = self.destination / 'user-empty-directory'
        directory.mkdir()
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
        self.assertTrue(directory.is_dir())
        self.assertTrue((self.destination / installer.MANIFEST).is_file())

    def test_missing_corrupt_or_incomplete_manifest_refuses_all_removal(self):
        self.install()
        manifest = self.destination / installer.MANIFEST
        original = manifest.read_bytes()
        for data in [None, b'{bad json', b'[]', b'{"format":1,"files":{}}',
                     json.dumps({'format': 1, 'files': {'SKILL.md': '0' * 64}}).encode()]:
            with self.subTest(data=data):
                if data is None:
                    manifest.unlink()
                else:
                    manifest.write_bytes(data)
                before = self.snapshot()
                self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
                self.assertEqual(before, self.snapshot())
                manifest.write_bytes(original)

    def test_traversal_absolute_and_overlapping_manifest_paths_are_refused(self):
        self.install()
        manifest = self.destination / installer.MANIFEST
        original = json.loads(manifest.read_text())
        variants = [{'../../outside.txt': '0' * 64}, {str(self.outside): '0' * 64},
                    {'framework/user': '0' * 64, 'framework/user/child': '0' * 64}]
        for extra in variants:
            with self.subTest(extra=extra):
                record = {**original, 'files': {**original['files'], **extra}}
                manifest.write_text(json.dumps(record))
                before = self.snapshot()
                self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
                self.assertEqual(before, self.snapshot())

    def test_owned_file_symlink_is_refused_before_any_removal(self):
        self.install()
        entry = self.destination / 'SKILL.md'
        entry.unlink()
        entry.symlink_to(self.outside)
        before = self.snapshot()
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
        self.assertTrue(entry.is_symlink())
        self.assertEqual(before, self.snapshot())

    def test_destination_symlink_is_refused(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.symlink_to(self.outside.parent, target_is_directory=True)
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 1)
        self.assertTrue(self.destination.is_symlink())

    def test_unwritable_removal_scope_is_blocked_before_writes(self):
        self.install()
        before = self.snapshot()
        with patch.object(installer.os, 'access', return_value=False):
            code, output = self.invoke('--uninstall', recovery=True)
        self.assertEqual(code, 1)
        self.assertIn('no removals attempted', output)
        self.assertEqual(before, self.snapshot())

    def test_install_uninstall_repeat_and_reinstall_preserve_project_and_history(self):
        before = self.snapshot()
        self.install()
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.invoke('--uninstall', recovery=True)[0], 0)
        self.assertEqual(self.snapshot(), before)
        self.install()
        self.assertTrue((self.destination / 'SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
