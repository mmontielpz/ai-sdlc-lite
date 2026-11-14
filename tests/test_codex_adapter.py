"""Synthetic declaration and delivery integration tests. No Codex/Godot inference."""
import ast
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'adapters/agents/codex'
spec = importlib.util.spec_from_file_location('codex_adapter', ADAPTER / 'validate_adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = json.loads((ADAPTER / 'examples/declaration.json').read_text())
        self.file = self.root / 'declaration.json'
        (self.root / 'AGENTS.md').write_text('Synthetic project instructions.')
        skill = self.root / adapter.SKILL_PATH
        skill.parent.mkdir(parents=True)
        shutil.copy2(ROOT / adapter.SKILL_PATH, skill)

    def check(self):
        self.file.write_text(json.dumps(self.config))
        return adapter.validate(self.file, self.root)

    def blocked(self):
        report = self.check()
        self.assertEqual(report['adapter_state'], 'NOT_READY', report)
        self.assertTrue(report['errors'])
        self.assertNotIn('contract_fields', report)
        self.assertFalse(report['execution_authorized'])

    def test_valid_declaration_is_only_adapter_ready(self):
        report = self.check()
        self.assertEqual(report['adapter_state'], 'CODEX_ADAPTER_READY', report)
        self.assertFalse(report['execution_authorized'])
        self.assertFalse(report['effective_permissions_verified'])
        self.assertEqual(report['qualification'], {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'})
        self.assertEqual(report['human_acceptance'], 'PENDING')
        self.assertEqual(report['contract_fields'], self.config['scope'])

    def test_supported_native_profiles_do_not_authorize(self):
        for sandbox in ('read-only', 'workspace-write'):
            for approval in ('on-request', 'never'):
                self.config['permissions'].update(sandbox=sandbox, approval_policy=approval)
                report = self.check()
                self.assertEqual(report['adapter_state'], 'CODEX_ADAPTER_READY')
                self.assertFalse(report['execution_authorized'])

    def test_unsupported_versions_fail_closed(self):
        for version in ('0.167.1', '0.167.3', 'latest', None, 0.1672):
            self.config['cli_version'] = version
            self.blocked()

    def test_unsafe_permissions_and_extra_flags_are_refused(self):
        original = copy.deepcopy(self.config)
        for key, value in (('sandbox', 'danger-full-access'), ('approval_policy', 'on-failure'),
                           ('bypass', True), ('bypass', 0), ('automatic_review', True),
                           ('additional_write_roots', ['/tmp']),
                           ('effective_config_review_required', False),
                           ('flags', ['--dangerously-bypass-hook-trust'])):
            with self.subTest(key=key, value=value):
                self.config = copy.deepcopy(original)
                self.config['permissions'][key] = value
                self.blocked()

    def test_unknown_missing_and_malformed_fields(self):
        original = copy.deepcopy(self.config)
        for key in original:
            self.config = copy.deepcopy(original)
            del self.config[key]
            self.blocked()
        for key, value in (('scope', []), ('instruction_paths', 'AGENTS.md'),
                           ('qualification', 'CODEX_DEEP_QUALIFIED'), ('schema', 'v2')):
            self.config = copy.deepcopy(original)
            self.config[key] = value
            self.blocked()

    def test_missing_and_empty_instructions(self):
        path = self.root / 'AGENTS.md'
        path.write_text('')
        self.blocked()
        path.unlink()
        self.blocked()

    def test_instruction_symlink_and_external_paths(self):
        (self.root / 'AGENTS.md').unlink()
        (self.root / 'AGENTS.md').symlink_to(ROOT / 'AGENTS.md')
        self.blocked()
        self.config['instruction_paths'] = ['../AGENTS.md']
        self.blocked()

    def test_canonical_skill_path_and_identity(self):
        original = self.config['skill_path']
        for path in ('SKILL.md', '/tmp/SKILL.md', '../SKILL.md'):
            self.config['skill_path'] = path
            self.blocked()
        self.config['skill_path'] = original
        skill = self.root / original
        skill.write_text('wrong skill')
        self.blocked()
        skill.unlink()
        self.blocked()

    def test_skill_parent_symlink_is_refused(self):
        shutil.rmtree(self.root / '.agents')
        (self.root / '.agents').symlink_to(ROOT / '.agents', target_is_directory=True)
        self.blocked()

    def test_unsafe_scope_and_broad_allowances(self):
        original = copy.deepcopy(self.config)
        for pattern in ('../x', '/tmp/x', '**', '$HOME/x', 'x//y', 'x/./y', 'x/../y',
                        'user://save', 'x\\y', 'line\nbreak', 'x\0y'):
            with self.subTest(pattern=pattern):
                self.config = copy.deepcopy(original)
                self.config['scope']['allowed_paths'] = [pattern]
                self.blocked()

    def test_protected_scope_conflict(self):
        self.config['scope']['allowed_paths'] = ['AGENTS.md']
        self.blocked()

    def test_sensitive_allowances_must_be_in_scope(self):
        self.config['scope']['allowed_sensitive_paths'] = ['tests/test_game.py']
        self.blocked()
        self.config['scope']['allowed_paths'].append('tests/test_game.py')
        self.assertEqual(self.check()['adapter_state'], 'CODEX_ADAPTER_READY')

    def test_instruction_and_skill_protection_is_required(self):
        self.config['scope']['protected_paths'] = ['assets/**']
        self.blocked()

    def test_evidence_is_required_outside_project(self):
        self.config['evidence']['store'] = 'inside-project'
        self.blocked()

    def test_duplicate_keys_non_json_and_oversized_config(self):
        for content in ('{"schema":1,"schema":2}', '[]', 'bad', ' ' * (adapter.MAX_BYTES + 1)):
            self.file.write_text(content)
            report = adapter.validate(self.file, self.root)
            self.assertEqual(report['adapter_state'], 'NOT_READY')
            self.assertTrue(report['errors'])

    def test_config_symlink_is_refused(self):
        self.file.symlink_to(ADAPTER / 'examples/declaration.json')
        self.assertEqual(adapter.validate(self.file, self.root)['adapter_state'], 'NOT_READY')

    def test_validation_does_not_spawn_or_mutate(self):
        self.file.write_text(json.dumps(self.config))
        def snapshot():
            return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                    for p in self.root.rglob('*') if p.is_file()}
        before = snapshot()
        import subprocess
        with mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('spawned')), \
                mock.patch.object(Path, 'write_bytes', side_effect=AssertionError('write')), \
                mock.patch.object(Path, 'write_text', side_effect=AssertionError('write')):
            self.assertEqual(adapter.validate(self.file, self.root)['adapter_state'], 'CODEX_ADAPTER_READY')
        self.assertEqual(snapshot(), before)
        tree = ast.parse((ADAPTER / 'validate_adapter.py').read_text())
        imports = {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertFalse(imports & {'subprocess', 'socket', 'os', 'multiprocessing', 'ctypes'})

    def test_unexpected_error_fails_closed(self):
        self.file.write_text(json.dumps(self.config))
        with mock.patch.object(adapter, 'check_shape', side_effect=RuntimeError('failure')):
            report = adapter.validate(self.file, self.root)
        self.assertEqual(report['adapter_state'], 'NOT_READY')
        self.assertTrue(report['errors'])

    def test_cli_exit_codes(self):
        self.file.write_text(json.dumps(self.config))
        args = ['--config', str(self.file), '--project', str(self.root)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(adapter.main(args), 0)
            self.file.write_text('{}')
            self.assertEqual(adapter.main(args), 2)

    def test_core_accepts_emitted_path_fields(self):
        spec = importlib.util.spec_from_file_location('codex_core_check', ROOT / 'scripts/verify_scope.py')
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        for patterns in self.check()['contract_fields'].values():
            for pattern in patterns:
                core.compile_glob(pattern)


if __name__ == '__main__':
    unittest.main()
