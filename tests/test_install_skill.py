"""Isolated safety checks; no agent inference, installs, or global config writes."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_skill', SOURCE / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-lite-installer-test-')
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / 'target with spaces'
        self.target.mkdir()
        subprocess.run(['git', 'init', '--quiet', str(self.target)], check=True)
        (self.target / 'AGENTS.md').write_text('Keep existing project rules.\n')
        (self.target / 'TASK.md').write_text('Keep active task.\n')
        self.destination = self.target / installer.SKILL
        self.copilot_home = Path(self.temp.name) / 'copilot-home'
        self.copilot_home.mkdir()
        self.environment = patch.dict(os.environ, {'COPILOT_HOME': str(self.copilot_home),
                                                   'COPILOT_CACHE_HOME': str(Path(self.temp.name) / 'cache')})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def invoke(self, *args, target=None):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), patch.object(installer, 'readiness', return_value=0):
            code = installer.main(['--target', str(target or self.target), *args])
        return code, output.getvalue()

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.target.rglob('*') if p.is_file()}

    def test_install_and_preserve_project_files(self):
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 0)
        after = self.snapshot()
        self.assertTrue(set(before) <= set(after))
        for name in before:
            self.assertEqual(before[name], after[name])
        self.assertTrue(all(name in before or name.startswith(str(installer.SKILL) + '/')
                            for name in after))

    def test_six_references_and_canonical_bytes(self):
        self.assertEqual(self.invoke()[0], 0)
        entry = (self.destination / 'SKILL.md').read_text()
        self.assertEqual(len(installer.LINK.findall(entry)), 6)
        for link in installer.LINK.findall(entry):
            self.assertTrue((self.destination / link).is_file())
        for name in installer.DOCUMENTS:
            self.assertEqual((self.destination / 'framework' / name).read_bytes(),
                             installer.reference_bytes(name))
        for path in (self.destination / 'framework').rglob('*.md'):
            for link in installer.LINK.findall(path.read_text()):
                url = installer.urlsplit(link)
                if not url.scheme and not url.netloc and url.path:
                    self.assertTrue((path.parent / installer.unquote(url.path)).is_file(), link)

    def test_repeat_preserves_contents_and_mtimes(self):
        self.assertEqual(self.invoke()[0], 0)
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(before, self.snapshot())

    def test_dry_run_does_not_write(self):
        before = self.snapshot()
        code, output = self.invoke('--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('Exact installation preview', output)
        self.assertEqual(before, self.snapshot())

    def test_conflict_refused_before_writes(self):
        self.destination.mkdir(parents=True)
        (self.destination / 'SKILL.md').write_text('Existing Skill\n')
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_edited_installation_refuses_overwrite(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.destination / 'framework/TASK.md').write_text('User edit\n')
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_extra_file_refuses_reinstall(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.destination / 'notes.txt').write_text('User notes\n')
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_framework_target_refused(self):
        code, output = self.invoke(target=SOURCE)
        self.assertEqual(code, 1)
        self.assertIn('must be separate', output)

    def test_non_repository_refused(self):
        outside = Path(self.temp.name) / 'not a repo'
        outside.mkdir()
        self.assertEqual(self.invoke(target=outside)[0], 1)
        self.assertEqual(list(outside.iterdir()), [])

    def test_explicit_target_required(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            installer.main([])
        self.assertEqual(raised.exception.code, 2)

    def test_subdirectory_resolves_root(self):
        sub = self.target / 'nested'
        sub.mkdir()
        code, output = self.invoke(target=sub)
        self.assertEqual(code, 0)
        self.assertIn('Resolved target subdirectory', output)
        self.assertTrue((self.destination / 'SKILL.md').is_file())
        self.assertEqual(list(sub.iterdir()), [])

    def test_symlink_parent_refused(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.target / '.agents').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(list(outside.iterdir()), [])

    def test_rollback_unchanged_and_repeat(self):
        before = self.snapshot()
        self.assertEqual(self.invoke()[0], 0)
        installed = self.snapshot()
        self.assertEqual(self.invoke('--uninstall', '--dry-run')[0], 0)
        self.assertEqual(installed, self.snapshot())
        self.assertEqual(self.invoke('--uninstall')[0], 0)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke('--uninstall')[0], 0)
        self.assertEqual(self.invoke()[0], 0)

    def test_rollback_preserves_edited_and_unowned_files(self):
        self.assertEqual(self.invoke()[0], 0)
        edited = self.destination / 'framework/TASK.md'
        edited.write_text('Keep this edit\n')
        extra = self.destination / 'notes.txt'
        extra.write_text('Keep user notes\n')
        self.assertEqual(self.invoke('--uninstall')[0], 1)
        self.assertEqual(edited.read_text(), 'Keep this edit\n')
        self.assertEqual(extra.read_text(), 'Keep user notes\n')
        self.assertTrue((self.destination / installer.MANIFEST).is_file())
        self.assertFalse((self.destination / 'SKILL.md').exists())

    def test_manifest_escape_refused(self):
        self.assertEqual(self.invoke()[0], 0)
        manifest = self.destination / installer.MANIFEST
        record = installer.json.loads(manifest.read_text())
        record['files']['../../../../AGENTS.md'] = installer.digest((self.target / 'AGENTS.md').read_bytes())
        manifest.write_text(installer.json.dumps(record))
        before = self.snapshot()
        self.assertEqual(self.invoke('--uninstall')[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_manifest_symlink_refused_before_reading(self):
        self.assertEqual(self.invoke()[0], 0)
        manifest = self.destination / installer.MANIFEST
        outside = Path(self.temp.name) / 'outside-manifest.json'
        outside.write_bytes(manifest.read_bytes())
        manifest.unlink()
        manifest.symlink_to(outside)
        self.assertEqual(self.invoke('--uninstall')[0], 1)
        self.assertTrue((self.destination / 'SKILL.md').is_file())

    def test_missing_copilot_reports_blocked(self):
        with redirect_stdout(io.StringIO()), patch.object(installer.shutil, 'which', return_value=None), self.assertRaises(installer.Blocked):
            installer.readiness(self.target, self.destination)

    def test_invalid_manifest_reports_blocked(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.destination / installer.MANIFEST).write_text('[]\n')
        before = self.snapshot()
        code, output = self.invoke('--uninstall')
        self.assertEqual(code, 1)
        self.assertIn('Invalid installer manifest', output)
        self.assertEqual(before, self.snapshot())

    @unittest.skipUnless(shutil.which('copilot'), 'Copilot CLI unavailable; native discovery unverified')
    def test_native_cli_discovery_and_rollback(self):
        command = [installer.sys.executable, '-B', str(SOURCE / 'scripts/install_skill.py'),
                   '--target', str(self.target)]
        result = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('READY: Copilot discovers the enabled project Skill.', result.stdout)
        before = self.snapshot()
        repeat = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True, timeout=30)
        self.assertEqual(repeat.returncode, 0, repeat.stdout + repeat.stderr)
        self.assertEqual(before, self.snapshot())
        rollback = subprocess.run(command + ['--uninstall'], capture_output=True, text=True, timeout=30)
        self.assertEqual(rollback.returncode, 0, rollback.stdout + rollback.stderr)
        self.assertFalse(self.destination.exists())

    def test_parent_detection_does_not_read_or_modify(self):
        parent = self.target.parent / 'AGENTS.md'
        parent.write_text('Synthetic parent instructions.\n')
        before = parent.read_bytes(), parent.stat().st_mtime_ns
        code, output = self.invoke('--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('PARENT instructions detected (not read): ' + str(parent), output)
        self.assertEqual(before, (parent.read_bytes(), parent.stat().st_mtime_ns))
        self.assertNotIn('Synthetic parent instructions.', output)

    def test_zero_friction_defaults(self):
        code, output = self.invoke('--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('NOT INITIALIZED; non-blocking', output)
        self.assertIn('WRITE PREFLIGHT: PASS', output)
        with patch.object(installer.os, 'access', return_value=False):
            _, output = self.invoke('--dry-run')
        self.assertIn('WRITE PREFLIGHT: BLOCKED', output)

    def test_skill_source_bundle_consistency(self):
        source = (SOURCE / installer.SKILL / 'SKILL.md').read_text()
        entry = installer.payload()['SKILL.md'].decode()
        self.assertIn('](../../../templates/RESULT.md)', source)
        self.assertNotIn('](../../../RESULT.md)', source)
        self.assertIn('](framework/RESULT.md)', entry)
        self.assertEqual(installer.payload()['framework/RESULT.md'],
                         installer.reference_bytes('RESULT.md'))
        section = source[source.index('## Zero-friction defaults'):]
        self.assertEqual(entry.count('## Zero-friction defaults'), 1)
        self.assertIn(section, entry)  # single authoritative source, no installer copy
        self.assertNotIn('A plain developer request is enough', Path(installer.__file__).read_text())

    def test_initialize_pending_context_and_preserve_later_edits(self):
        self.assertEqual(self.invoke()[0], 0)
        before = self.snapshot()
        self.assertEqual(self.invoke('--init-task', 'DEMO', '--dry-run')[0], 0)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke('--init-task', 'DEMO')[0], 0)
        task = self.target / 'tasks/DEMO/TASK.md'
        self.assertIn('**Decision:** PENDING', task.read_text())
        self.assertIn('DEMO', task.read_text())
        task.write_text(task.read_text() + '\nOwner task details.\n')
        before = self.snapshot()
        self.assertEqual(self.invoke('--init-task', 'DEMO')[0], 0)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke('--init-task', 'OTHER')[0], 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke('--check')[0], 0)

    def test_reference_existing_contract_without_rewriting(self):
        self.assertEqual(self.invoke()[0], 0)
        task = self.target / 'TASK.md'
        before = task.read_bytes(), task.stat().st_mtime_ns
        self.assertEqual(self.invoke('--init-task', 'EXISTING', '--task-contract', 'TASK.md')[0], 0)
        self.assertEqual(before, (task.read_bytes(), task.stat().st_mtime_ns))
        context = installer.json.loads((self.target / installer.CONTEXT).read_text())
        self.assertEqual(context['contract'], 'TASK.md')
        checklist = self.target / context['checklist']
        self.assertIn('](../../TASK.md)', checklist.read_text())
        self.assertFalse((self.target / 'tasks/EXISTING/TASK.md').exists())

    def test_initialized_result_uses_template_and_preserves_root_history(self):
        history = self.target / 'RESULT.md'
        history.write_bytes(b'Historical execution evidence; preserve exactly.\n')
        before = history.read_bytes(), history.stat().st_mtime_ns
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(self.invoke('--init-task', 'DELIVERY')[0], 0)
        result = (self.target / 'tasks/DELIVERY/RESULT.md').read_text()
        self.assertIn('**Decision:** PENDING', result)
        self.assertIn('without an interactive acceptance prompt', result)
        self.assertNotIn('Historical execution evidence', result)
        self.assertEqual(before, (history.read_bytes(), history.stat().st_mtime_ns))

    def test_context_conflicts_and_unsafe_paths(self):
        self.assertEqual(self.invoke()[0], 0)
        for task_id, contract in [('../escape', None), ('DEMO', '../outside.md'),
                                  ('DEMO', '.agents/skills/ai-sdlc-lite/framework/TASK.md'),
                                  ('DEMO', 'missing.md')]:
            args = ['--init-task', task_id]
            if contract:
                args += ['--task-contract', contract]
            before = self.snapshot()
            self.assertEqual(self.invoke(*args)[0], 1)
            self.assertEqual(before, self.snapshot())
        folder = self.target / 'tasks/DEMO'
        folder.mkdir(parents=True)
        (folder / 'RESULT.md').write_text('Existing result.\n')
        before = self.snapshot()
        self.assertEqual(self.invoke('--init-task', 'DEMO')[0], 1)
        self.assertEqual(before, self.snapshot())

    def config(self, *extra):
        return self.invoke('--configure-copilot', '--copilot-home', str(self.copilot_home), *extra)

    def test_config_opt_in_preview_backup_repeat_and_exact_restore(self):
        settings = self.copilot_home / 'settings.json'
        original = b'{ "theme": "dark", "sandbox": {"userPolicy": {"filesystem": {"deniedPaths": ["/synthetic-secret"]}}}}\n'
        settings.write_bytes(original)
        self.assertEqual(self.config('--dry-run')[0], 0)
        self.assertEqual(settings.read_bytes(), original)
        self.assertFalse((self.copilot_home / installer.CONFIG_BACKUP).exists())
        self.assertEqual(self.config()[0], 0)
        document = installer.json.loads(settings.read_text())
        self.assertEqual(document['theme'], 'dark')
        self.assertTrue(document['sandbox']['enabled'])
        self.assertFalse(document['sandbox']['allowBypass'])
        self.assertEqual(document['sandbox']['userPolicy']['filesystem']['deniedPaths'], ['/synthetic-secret'])
        before = settings.read_bytes(), settings.stat().st_mtime_ns
        self.assertEqual(self.config()[0], 0)
        self.assertEqual(before, (settings.read_bytes(), settings.stat().st_mtime_ns))
        self.assertFalse((self.copilot_home / 'permissions-config.json').exists())
        args = ['--rollback-config', '--copilot-home', str(self.copilot_home)]
        self.assertEqual(self.invoke(*args, '--dry-run')[0], 0)
        self.assertEqual(before, (settings.read_bytes(), settings.stat().st_mtime_ns))
        self.assertEqual(self.invoke(*args)[0], 0)
        self.assertEqual(settings.read_bytes(), original)
        self.assertFalse((self.copilot_home / installer.CONFIG_BACKUP).exists())

    def test_config_rollback_preserves_later_changes(self):
        self.assertEqual(self.config()[0], 0)
        settings = self.copilot_home / 'settings.json'
        settings.write_text('{"theme":"user edit"}\n')
        before = settings.read_bytes()
        self.assertEqual(self.invoke('--rollback-config', '--copilot-home', str(self.copilot_home))[0], 1)
        self.assertEqual(settings.read_bytes(), before)
        self.assertTrue((self.copilot_home / installer.CONFIG_BACKUP).exists())

    def test_config_without_original_settings_rolls_back_to_absence(self):
        self.assertEqual(self.config()[0], 0)
        self.assertEqual(self.invoke('--rollback-config', '--copilot-home', str(self.copilot_home))[0], 0)
        self.assertFalse((self.copilot_home / 'settings.json').exists())

    def test_narrow_sandbox_path_does_not_grant_cli_permissions(self):
        parent = self.target.parent / 'AGENTS.md'
        parent.write_text('Synthetic parent rules.\n')
        self.assertEqual(self.config('--read-instruction', str(parent))[0], 0)
        settings = installer.json.loads((self.copilot_home / 'settings.json').read_text())
        self.assertEqual(settings['sandbox']['userPolicy']['filesystem']['readonlyPaths'], [str(parent)])
        self.assertNotIn('readwritePaths', settings['sandbox']['userPolicy']['filesystem'])
        self.assertNotIn('permissions', settings)
        self.assertFalse((self.copilot_home / 'permissions-config.json').exists())

    def test_config_refuses_broad_paths_jsonc_symlinks_and_missing_opt_in(self):
        self.assertEqual(self.invoke('--configure-copilot')[0], 1)
        self.assertEqual(self.config('--read-instruction', str(self.target.parent))[0], 1)
        self.assertEqual(self.invoke('--read-instruction', str(self.target.parent / 'AGENTS.md'))[0], 1)
        settings = self.copilot_home / 'settings.json'
        original = b'// JSONC settings require manual review\n{"theme":"dark"}\n'
        settings.write_bytes(original)
        self.assertEqual(self.config()[0], 1)
        self.assertEqual(settings.read_bytes(), original)
        settings.unlink()
        outside = Path(self.temp.name) / 'outside-settings.json'
        outside.write_text('{}\n')
        settings.symlink_to(outside)
        self.assertEqual(self.config()[0], 1)
        self.assertEqual(outside.read_text(), '{}\n')

    @unittest.skipUnless(shutil.which('copilot'), 'Copilot CLI unavailable')
    def test_native_cli_recognizes_isolated_sandbox_settings(self):
        parent = self.target.parent / 'AGENTS.md'
        parent.write_text('Synthetic parent rules.\n')
        self.assertEqual(self.config('--read-instruction', str(parent))[0], 0)
        for key, expected in [('sandbox.enabled', 'true'), ('sandbox.allowBypass', 'false'),
                              ('sandbox.userPolicy.filesystem.readonlyPaths', str(parent))]:
            r = subprocess.run(['copilot', '--no-auto-update', '-C', str(self.target), 'config', key],
                               capture_output=True, text=True, timeout=20)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(r.stdout.strip(), expected)


if __name__ == '__main__':
    unittest.main()
