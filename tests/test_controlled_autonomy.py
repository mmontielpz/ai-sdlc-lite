"""Configuration safety tests; simulated approval references are not human decisions."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup_installer', SOURCE / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ControlledAutonomyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-lite-autonomy-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '--quiet', str(self.repo)], check=True)
        self.home = Path(self.temp.name) / 'isolated-home'
        self.home.mkdir()
        self.package = self.repo / 'package.json'
        self.package.write_text(json.dumps({'scripts': {'lint': 'node --check check.cjs',
                                                      'build': 'node check.cjs', 'test': 'node check.cjs'}}))
        (self.repo / 'check.cjs').write_text('console.log("synthetic check");\n')
        (self.repo / 'TASK.md').write_text('Plan approval: PENDING\n')
        (self.repo / 'RESULT.md').write_text('Human delivery acceptance: PENDING\n')
        self.plan = {'approval_reference': 'SYNTHETIC FIXTURE ONLY: approved plan',
                     'scripts': ['lint', 'build', 'test', 'preview', 'visual', 'cleanup'],
                     'read_files': ['check.cjs'], 'edit_files': ['check.cjs'],
                     'production_exposure': 'NONE_DECLARED', 'credential_exposure': 'NONE_DECLARED',
                     'network_access': 'NONE_DECLARED', 'risks': ['script effects need review'],
                     'reviewed_package_sha256': hashlib.sha256(self.package.read_bytes()).hexdigest()}
        self.plan_path = self.repo / 'plan.json'
        self.save_plan()
        self.real_run = installer.run
        self.env = patch.dict(os.environ, {'COPILOT_HOME': str(self.home), 'COPILOT_ALLOW_ALL': '',
                                           'COPILOT_ASSISTED_APPROVAL': ''})
        self.env.start()
        self.addCleanup(self.env.stop)

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def run_tool(self, args, cwd):
        if '--version' in args and 'copilot' in str(args[0]):
            return 'GitHub Copilot CLI 1.0.109.'
        if 'permissions' in args:
            return '--allow-tool read(path?) write(path?)'
        return self.real_run(args, cwd)

    def invoke(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), patch.object(installer, 'preflight'), \
                patch.object(installer, 'run', side_effect=self.run_tool), \
                patch.object(installer.shutil, 'which', return_value='/synthetic/copilot'):
            code = installer.main(['--target', str(self.repo), '--copilot-home', str(self.home), *args])
        return code, output.getvalue()

    def preview(self):
        code, output = self.invoke('--configure-copilot', '--permission-plan', 'plan.json', '--dry-run')
        self.assertEqual(code, 0, output)
        token = re.search(r'CONSENT TOKEN: ([0-9a-f]{64})', output).group(1)
        return token, output

    def apply(self, token=None):
        if token is None:
            token, _ = self.preview()
        return self.invoke('--configure-copilot', '--permission-plan', 'plan.json', '--consent-config', token)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.home.iterdir() if p.is_file()}

    def test_preview_without_consent_never_writes(self):
        before = self.snapshot()
        code, output = self.invoke('--configure-copilot', '--permission-plan', 'plan.json')
        self.assertEqual(code, 0)
        self.assertIn('preview only', output)
        self.assertEqual(before, self.snapshot())

    def test_exact_commands_session_files_and_omitted_capabilities(self):
        token, output = self.preview()
        self.assertIn('UNGRANTED: preview', output)
        self.assertIn('UNGRANTED: visual', output)
        self.assertIn('UNGRANTED: cleanup', output)
        self.assertEqual(self.apply(token)[0], 0)
        permissions = json.loads((self.home / 'permissions-config.json').read_text())
        self.assertEqual(set(permissions['locations']), {str(self.repo)})
        self.assertEqual(permissions['locations'][str(self.repo)], {'tool_approvals': [
            {'kind': 'commands', 'commandIdentifiers': ['npm run build', 'npm run lint', 'npm run test']}]})
        self.assertIn(f'write({self.repo / "check.cjs"})', output)
        self.assertNotIn('write', permissions['locations'][str(self.repo)])
        self.assertIn('Delivery acceptance: PENDING', output)

    def test_python_unittest_is_not_approximated_by_interpreter_grant(self):
        self.plan['scripts'] = ['python3 -m unittest discover']
        self.save_plan()
        token, output = self.preview()
        self.assertIn('UNGRANTED: python3 -m unittest discover', output)
        self.assertIn('no automatic task expiry', output)
        self.assertIn('Native permission prompt count: UNKNOWN', output)
        self.assertEqual(self.apply(token)[0], 0)
        permissions = json.loads((self.home / 'permissions-config.json').read_text())
        self.assertFalse(permissions['locations'][str(self.repo)].get('tool_approvals'))

    def test_outside_file_rule_refuses_without_settings_changes(self):
        outside = self.repo.parent / 'outside.txt'
        outside.write_text('Preserve outside task.\n')
        self.plan['edit_files'] = ['../outside.txt']
        self.save_plan()
        before = self.snapshot()
        self.assertEqual(self.invoke('--configure-copilot', '--permission-plan', 'plan.json', '--dry-run')[0], 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(outside.read_text(), 'Preserve outside task.\n')

    def test_consent_binds_current_state(self):
        token, _ = self.preview()
        (self.repo / 'check.cjs').write_text('console.log("changed");\n')
        self.assertEqual(self.apply(token)[0], 1)
        self.assertEqual(self.snapshot(), {})

    def test_unapproved_plan_cannot_apply(self):
        self.plan.pop('approval_reference')
        self.save_plan()
        self.assertEqual(self.apply()[0], 1)
        self.assertEqual(self.snapshot(), {})

    def test_review_hash_and_exposure_required(self):
        for field, value in [('reviewed_package_sha256', 'incorrect'), ('production_exposure', 'UNKNOWN'),
                             ('credential_exposure', 'REQUIRED')]:
            with self.subTest(field=field):
                original = self.plan[field]
                self.plan[field] = value
                self.save_plan()
                self.assertEqual(self.apply()[0], 1)
                self.assertEqual(self.snapshot(), {})
                self.plan[field] = original

    def test_settings_preserved_and_exact_rollback(self):
        settings = self.home / 'settings.json'
        permissions = self.home / 'permissions-config.json'
        original_settings = b'{ "theme": "dark", "model": "existing model" }\n'
        original_permissions = b'{"locations": {"/other/repository": {"tool_approvals": []}}}\n'
        settings.write_bytes(original_settings)
        permissions.write_bytes(original_permissions)
        self.assertEqual(self.apply()[0], 0)
        self.assertEqual(json.loads(settings.read_text())['model'], 'existing model')
        self.assertIn('/other/repository', json.loads(permissions.read_text())['locations'])
        self.assertEqual(self.invoke('--rollback-config')[0], 0)
        self.assertEqual(settings.read_bytes(), original_settings)
        self.assertEqual(permissions.read_bytes(), original_permissions)

    def test_later_user_edit_blocks_all_rollback(self):
        self.assertEqual(self.apply()[0], 0)
        (self.home / 'settings.json').write_text('{"theme":"later edit"}\n')
        before = self.snapshot()
        self.assertEqual(self.invoke('--rollback-config')[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_legacy_configuration_cannot_overlap_permission_transaction(self):
        self.assertEqual(self.apply()[0], 0)
        before = self.snapshot()
        self.assertEqual(self.invoke('--configure-copilot')[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_existing_broad_target_grants_are_preserved_and_refused(self):
        (self.home / 'permissions-config.json').write_text(json.dumps({'locations': {
            str(self.repo): {'tool_approvals': [{'kind': 'commands', 'commandIdentifiers': ['npm:*']}]}}}))
        before = self.snapshot()
        self.assertEqual(self.invoke('--configure-copilot', '--permission-plan', 'plan.json')[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_security_files_and_glob_paths_are_refused(self):
        for name in ['.env', 'package.json', 'AGENTS.md', 'check*.cjs']:
            with self.subTest(name=name):
                self.plan['edit_files'] = [name]
                self.save_plan()
                self.assertEqual(self.invoke('--configure-copilot', '--permission-plan', 'plan.json')[0], 1)
                self.assertEqual(self.snapshot(), {})

    def test_unknown_version_is_refused(self):
        with patch.object(self, 'run_tool', return_value='unsupported'):
            self.assertEqual(self.invoke('--configure-copilot', '--permission-plan', 'plan.json')[0], 1)
        self.assertEqual(self.snapshot(), {})

    def test_setup_does_not_change_bov_decisions(self):
        before = {name: (self.repo / name).read_bytes() for name in ('TASK.md', 'RESULT.md')}
        self.assertEqual(self.apply()[0], 0)
        self.assertEqual(before, {name: (self.repo / name).read_bytes() for name in before})

    def test_later_configuration_change_invalidates_consent(self):
        token, _ = self.preview()
        (self.home / 'settings.json').write_text('{"theme":"new choice"}')
        before = self.snapshot()
        self.assertEqual(self.apply(token)[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_consent_without_plan_cannot_fall_through_to_legacy(self):
        self.assertEqual(self.invoke('--configure-copilot', '--consent-config', 'wrong')[0], 1)
        self.assertEqual(self.snapshot(), {})

    def test_inherited_unrestricted_mode_is_refused(self):
        with patch.dict(os.environ, {'COPILOT_ALLOW_ALL': 'true'}):
            self.assertEqual(self.invoke('--configure-copilot', '--permission-plan', 'plan.json')[0], 1)
        self.assertEqual(self.snapshot(), {})

    def test_preflight_reports_unknown_exposure(self):
        output = io.StringIO()
        with redirect_stdout(output), patch.object(installer.shutil, 'which', return_value=None):
            installer.preflight(self.repo)
        self.assertIn('Production/credential exposure: UNKNOWN', output.getvalue())
        self.assertIn('none executed by preflight', output.getvalue())


if __name__ == '__main__':
    unittest.main()
