"""Configuration-level tests for adapters/godot/validate_adapter.py. Synthetic, disposable fixtures only.

Nothing here runs Godot or any project command. Runtime and gameplay gates (Q4, Q5, Q8, Q10) are never PASS.
"""

import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'adapters' / 'godot'
SAMPLE = ADAPTER / 'examples' / 'disposable-sample'
spec = importlib.util.spec_from_file_location('validate_adapter', ADAPTER / 'validate_adapter.py')
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)
core_spec = importlib.util.spec_from_file_location('core_verify', ROOT / 'scripts' / 'verify_scope.py')
core = importlib.util.module_from_spec(core_spec)
core_spec.loader.exec_module(core)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name).resolve() / 'repo'
        shutil.copytree(SAMPLE, self.dir)
        self.config = json.loads((SAMPLE / 'godot-adapter.json').read_text())
        self.project = self.dir / 'project'

    def run_validate(self, config=None, project_dir=None):
        path = self.dir / 'adapter.json'
        path.write_text(json.dumps(self.config if config is None else config))
        return va.validate(path, project_dir or self.dir)

    def codes(self, report, level=None):
        return {f['code'] for f in report['findings'] if level in (None, f['level'])}

    def assertBlocked(self, report, code):
        self.assertEqual(report['adapter_state'], 'NOT_READY', report['findings'])
        self.assertIn(code, self.codes(report, 'ERROR'), report['findings'])
        self.assertNotIn('contract_fields', report)

    def mutate(self, **sections):
        for key, value in sections.items():
            self.config[key] = value


class ValidDeclarations(Base):
    def test_committed_sample_is_adapter_ready_and_never_authorizes_execution(self):
        report = va.validate(SAMPLE / 'godot-adapter.json', SAMPLE)
        self.assertEqual(report['adapter_state'], 'ADAPTER_READY', report['findings'])
        self.assertIs(report['execution_authorized'], False)
        self.assertIs(report['approval_recorded'], False)
        self.assertEqual(self.codes(report), {'runner_not_approved', 'execution_not_authorized'})
        self.assertTrue(report['isolation_proof'].startswith('none'))

    def test_gates_are_configuration_level_only(self):
        gates = self.run_validate()['gates']
        self.assertEqual((gates['Q1'], gates['Q2']), ('PASS', 'PASS'))
        self.assertEqual({gates[g] for g in ('Q3', 'Q6', 'Q7', 'Q9')}, {'DECLARED'})
        self.assertEqual({gates[g] for g in ('Q4', 'Q5', 'Q8', 'Q10')}, {'NOT_RUN'})   # never PASS without runtime evidence

    def test_recorded_approval_is_reported_but_still_not_authorization(self):
        self.config['runners'][0]['approved'] = True
        self.config['approvals'] = {'execution_approved_by': 'owner', 'approved_revision': 'abc123'}
        report = self.run_validate()
        self.assertEqual(report['adapter_state'], 'ADAPTER_READY')
        self.assertIs(report['approval_recorded'], True)
        self.assertIs(report['execution_authorized'], False)        # the tool never grants or acts on approval
        self.assertNotIn('execution_not_authorized', self.codes(report))

    def test_contract_fields_are_valid_for_the_core_and_prefixed_by_project_root(self):
        fields = self.run_validate()['contract_fields']
        self.assertEqual(set(fields), {'protected_paths', 'allowed_paths', 'allowed_sensitive_paths', 'ignorable_paths'})
        self.assertIn('project/project.godot', fields['protected_paths'])
        self.assertEqual(fields['ignorable_paths'], ['project/.godot/**'])
        for patterns in fields.values():
            for pattern in patterns:
                core.compile_glob(pattern)                          # accepted by the unchanged core
        self.assertTrue(core.matcher(fields['protected_paths'])('project/export_presets.cfg'))

    def test_explicit_sensitive_allowance_removes_default_protection(self):
        self.config['paths']['protected'] = ['assets/approved/**']
        self.config['paths']['sensitive_allowed'] = ['project.godot', 'export_presets.cfg']
        fields = self.run_validate()['contract_fields']
        self.assertNotIn('project/project.godot', fields['protected_paths'])
        self.assertEqual(fields['allowed_sensitive_paths'], ['project/project.godot', 'project/export_presets.cfg'])

    def test_cli_exit_codes_and_contract_field_output(self):
        path = self.dir / 'adapter.json'
        path.write_text(json.dumps(self.config))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(va.main(['--config', str(path), '--project', str(self.dir), '--emit-contract-fields']), 0)
        self.assertIn('protected_paths', json.loads(buffer.getvalue()))
        self.config['schema'] = 'nope'
        path.write_text(json.dumps(self.config))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(va.main(['--config', str(path), '--project', str(self.dir)]), 2)


class ProjectDetection(Base):
    def test_missing_project_godot(self):
        (self.project / 'project.godot').unlink()
        report = self.run_validate()
        self.assertBlocked(report, 'project_godot_missing')
        self.assertEqual((report['gates']['Q1'], report['gates']['Q2']), ('FAIL', 'FAIL'))

    def test_malformed_project_godot(self):
        for content in (b'\xff\xfe\x00garbage', b'no config version here\n', b'config_version=abc\n', b''):
            with self.subTest(content=content):
                (self.project / 'project.godot').write_bytes(content)
                self.assertBlocked(self.run_validate(), 'project_godot_malformed')

    def test_project_godot_symlink_and_directory_are_refused(self):
        target = self.dir / 'real.godot'
        (self.project / 'project.godot').rename(target)
        (self.project / 'project.godot').symlink_to(target)
        self.assertBlocked(self.run_validate(), 'project_godot_missing')
        (self.project / 'project.godot').unlink()
        (self.project / 'project.godot').mkdir()
        self.assertBlocked(self.run_validate(), 'project_godot_missing')

    def test_version_constraint(self):
        self.config['godot'] = {'min_version': '4.4', 'max_version_exclusive': '5.0'}
        self.assertBlocked(self.run_validate(), 'godot_version_unsupported')        # project targets 4.3
        self.config['godot'] = {'min_version': '4.0', 'max_version_exclusive': '4.3'}
        self.assertBlocked(self.run_validate(), 'godot_version_unsupported')        # upper bound is exclusive
        self.config['godot'] = {'min_version': '4.3'}
        self.assertEqual(self.run_validate()['adapter_state'], 'ADAPTER_READY')
        for bad in ({'min_version': 'four'}, {'min_version': '5.0', 'max_version_exclusive': '4.0'}, {}):
            self.config['godot'] = bad
            self.assertBlocked(self.run_validate(), 'godot_version_constraint_invalid')

    def test_unknown_engine_version_is_a_warning_not_a_pass_of_the_constraint(self):
        (self.project / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="x"\n')
        report = self.run_validate()
        self.assertEqual(report['adapter_state'], 'ADAPTER_READY')
        self.assertIn('godot_version_unknown', self.codes(report, 'WARNING'))

    def test_project_root_traversal_missing_and_symlink(self):
        for root in ('../outside', '/etc', 'nope', 'project/../project'):
            with self.subTest(root=root):
                self.config['project']['root'] = root
                report = self.run_validate()
                self.assertEqual(report['adapter_state'], 'NOT_READY')
        (self.dir / 'link').symlink_to(self.project)
        self.config['project']['root'] = 'link'
        self.assertBlocked(self.run_validate(), 'project_root_invalid')

    def test_working_directory_must_exist_inside_the_project(self):
        self.config['project']['working_directory'] = 'missing'
        self.assertBlocked(self.run_validate(), 'project_root_invalid')
        self.config['project']['working_directory'] = '../x'
        self.assertBlocked(self.run_validate(), 'unsafe_path')


class InvalidConfigurations(Base):
    def test_unreadable_or_non_object_configuration(self):
        path = self.dir / 'bad.json'
        for text, code in (('not json', 'config_unreadable'), ('[]', 'config_not_json'), ('', 'config_unreadable')):
            path.write_text(text)
            report = va.validate(path, self.dir)
            self.assertBlocked(report, code)
        self.assertBlocked(va.validate(self.dir / 'missing.json', self.dir), 'config_unreadable')
        link = self.dir / 'link.json'
        link.symlink_to(self.dir / 'bad.json')
        self.assertBlocked(va.validate(link, self.dir), 'config_unreadable')

    def test_wrong_schema_unknown_keys_and_self_asserted_qualification(self):
        self.config['schema'] = 'ai-sdlc-godot-adapter/2'
        self.assertBlocked(self.run_validate(), 'config_schema_invalid')
        self.config['schema'] = va.CONFIG_SCHEMA
        for extra in ({'qualification': 'RUNTIME_QUALIFIED'}, {'verified': True}, {'adapter_state': 'ADAPTER_READY'}):
            with self.subTest(extra=extra):
                self.assertBlocked(self.run_validate(dict(self.config, **extra)), 'config_unknown_key')
        self.config['commands'][0]['shell'] = 'rm -rf /'
        self.assertBlocked(self.run_validate(), 'config_unknown_key')

    def test_missing_fields_and_wrong_types(self):
        for key in ('project', 'godot', 'runners', 'commands', 'paths', 'generated', 'isolation', 'evidence', 'approvals'):
            with self.subTest(missing=key):
                broken = copy.deepcopy(self.config)
                del broken[key]
                self.assertEqual(self.run_validate(broken)['adapter_state'], 'NOT_READY')
        for patch in ({'commands': 'rm -rf /'}, {'runners': {}}, {'paths': []}, {'isolation': 'yes'}):
            with self.subTest(patch=patch):
                self.assertEqual(self.run_validate(dict(self.config, **patch))['adapter_state'], 'NOT_READY')

    def test_command_declaration_rules(self):
        cases = [('role', 'deploy', 'command_invalid'), ('timeout_seconds', 0, 'command_invalid'),
                 ('timeout_seconds', 99999, 'command_invalid'), ('timeout_seconds', True, 'command_invalid'),
                 ('timeout_seconds', '5', 'command_invalid'), ('args', ['ok\nrm -rf /'], 'command_invalid'),
                 ('args', 'string-not-list', 'config_type_invalid')]
        for key, value, code in cases:
            with self.subTest(key=key, value=value):
                broken = copy.deepcopy(self.config)
                broken['commands'][1][key] = value
                self.assertBlocked(self.run_validate(broken), code)
        self.config['commands'][2].pop('requires_display')
        self.assertBlocked(self.run_validate(), 'command_invalid')

    def test_duplicate_ids(self):
        self.config['commands'][1]['id'] = 'import'
        self.assertBlocked(self.run_validate(), 'duplicate_id')
        self.config['commands'][1]['id'] = 'smoke'
        self.config['runners'].append(copy.deepcopy(self.config['runners'][0]))
        self.assertBlocked(self.run_validate(), 'duplicate_id')

    def test_isolation_and_evidence_requirements(self):
        self.config['isolation']['required'] = False
        self.assertBlocked(self.run_validate(), 'isolation_not_required')
        self.config['isolation']['required'] = True
        self.config['isolation']['disposable_workspace'] = False
        self.assertBlocked(self.run_validate(), 'isolation_not_required')
        self.config['isolation']['disposable_workspace'] = True
        self.config['isolation']['protected_user_data'] = ['my-home']
        self.assertBlocked(self.run_validate(), 'config_type_invalid')
        self.config['isolation']['protected_user_data'] = ['linux-xdg-data']
        self.config['evidence']['store'] = 'repository'
        self.assertBlocked(self.run_validate(), 'evidence_inside_repository')
        self.config['evidence']['store'] = 'outside-repository'
        self.config['evidence']['required'] = ['result_line']
        self.assertBlocked(self.run_validate(), 'evidence_incomplete')
        self.config['evidence']['required'] = ['exit_code', 'output_log']
        self.config['evidence']['result_line_pattern'] = '(['
        self.assertBlocked(self.run_validate(), 'config_type_invalid')

    def test_approvals_must_be_explicit(self):
        del self.config['approvals']['approved_revision']
        self.assertBlocked(self.run_validate(), 'config_field_missing')
        self.config['approvals'] = {'execution_approved_by': '', 'approved_revision': None}
        self.assertBlocked(self.run_validate(), 'config_type_invalid')


class UnsafePathsAndRunners(Base):
    BAD_PATHS = ['/etc/passwd', '../escape', 'a/../../b', 'a\\b', '~/saves', '$HOME/x', '%APPDATA%/x', 'res://x',
                 'user://fob.cfg', 'C:/x', './x', 'a//b', '', 'bad\0name']

    def test_unsafe_patterns_are_refused_in_every_path_list(self):
        for section in ('protected', 'allowed', 'sensitive_allowed', 'generated', 'ignorable'):
            for bad in self.BAD_PATHS:
                with self.subTest(section=section, bad=bad):
                    broken = copy.deepcopy(self.config)
                    broken['paths'][section].append(bad)
                    self.assertEqual(self.run_validate(broken)['adapter_state'], 'NOT_READY')
        for bad in self.BAD_PATHS:
            with self.subTest(writes=bad):
                broken = copy.deepcopy(self.config)
                broken['commands'][0]['writes'].append(bad)
                self.assertEqual(self.run_validate(broken)['adapter_state'], 'NOT_READY')

    def test_runner_must_be_a_project_owned_file(self):
        for path in ('godot', 'run_godot.sh', '/usr/bin/godot', '../outside/run.sh', 'tools/*.sh', 'tools/missing.sh'):
            with self.subTest(path=path):
                broken = copy.deepcopy(self.config)
                broken['runners'][0]['path'] = path
                report = self.run_validate(broken)
                self.assertEqual(report['adapter_state'], 'NOT_READY')
                self.assertTrue(self.codes(report, 'ERROR') & {'runner_unsafe', 'runner_missing', 'unsafe_path'})

    def test_runner_symlink_out_of_the_project_is_refused(self):
        outside = self.dir / 'outside.sh'
        outside.write_text('#!/bin/sh\n')
        (self.project / 'tools' / 'run_godot.sh').unlink()
        (self.project / 'tools' / 'run_godot.sh').symlink_to(outside)
        self.assertBlocked(self.run_validate(), 'runner_unsafe')

    def test_global_godot_runner_kinds_are_unsupported(self):
        for kind in ('system-godot', 'godot', 'shell', None):
            with self.subTest(kind=kind):
                broken = copy.deepcopy(self.config)
                broken['runners'][0]['kind'] = kind
                self.assertBlocked(self.run_validate(broken), 'runner_kind_unsupported')

    def test_unapproved_and_undeclared_runners(self):
        self.assertIn('runner_not_approved', self.codes(self.run_validate(), 'WARNING'))   # declared, not approved: warning
        self.config['commands'][0]['runner'] = 'godot'
        self.assertBlocked(self.run_validate(), 'unknown_runner')                         # undeclared: error
        self.config['commands'][0]['runner'] = 'wrapper'
        self.config['runners'][0]['isolation_by_runner'] = False
        self.assertBlocked(self.run_validate(), 'runner_isolation_unasserted')

    def test_arguments_cannot_reach_user_data_or_leave_the_project(self):
        for arg in ('user://fob.cfg', '--user=/synthetic/.local/share/godot/app_userdata', '/etc/passwd', '../x', '$HOME',
                    '~/x', '--cfg=~/.config/godot/editor_settings'):
            with self.subTest(arg=arg):
                broken = copy.deepcopy(self.config)
                broken['commands'][1]['args'].append(arg)
                report = self.run_validate(broken)
                self.assertEqual(report['adapter_state'], 'NOT_READY')
                self.assertTrue(self.codes(report, 'ERROR') & {'user_data_reference', 'unsafe_path'})


class ProtectedAndGeneratedPaths(Base):
    def test_project_configuration_must_be_protected_or_explicitly_allowed(self):
        self.config['paths']['protected'] = ['assets/approved/**']
        self.assertBlocked(self.run_validate(), 'project_config_unprotected')

    def test_allowed_path_inside_protected_path_conflicts(self):
        for allowed in ('assets/approved/new.png', 'assets/approved/**', 'project.godot'):
            with self.subTest(allowed=allowed):
                broken = copy.deepcopy(self.config)
                broken['paths']['allowed'].append(allowed)
                self.assertBlocked(self.run_validate(broken), 'protected_path_conflict')
        self.config['paths']['allowed'] = ['**']                      # broad allowance is fine: protected still wins
        self.assertEqual(self.run_validate()['adapter_state'], 'ADAPTER_READY')

    def test_command_writes_cannot_overlap_protected_paths(self):
        for write in ('project.godot', 'assets/**', 'assets/approved/x.png', '**'):
            with self.subTest(write=write):
                broken = copy.deepcopy(self.config)
                broken['commands'][1]['writes'] = [write]
                self.assertBlocked(self.run_validate(broken), 'protected_path_conflict')

    def test_writes_must_be_covered_by_generated_ignorable_or_allowed_paths(self):
        self.config['commands'][1]['writes'] = ['build/out.pck']
        self.assertBlocked(self.run_validate(), 'unscoped_write')
        self.config['paths']['ignorable'] = ['build/**']
        self.assertEqual(self.run_validate()['adapter_state'], 'ADAPTER_READY')
        self.config['paths']['generated'] = []
        self.config['commands'][0]['writes'] = ['.godot/**']          # the import now has nowhere declared to write
        self.assertBlocked(self.run_validate(), 'unscoped_write')

    def test_generated_policy(self):
        self.config['generated']['policy'] = 'sometimes'
        self.assertBlocked(self.run_validate(), 'config_type_invalid')
        self.config['generated']['policy'] = 'ignored'
        (self.project / '.gitignore').write_text('*.tmp\n')
        report = self.run_validate()
        self.assertEqual(report['adapter_state'], 'ADAPTER_READY')
        self.assertIn('generated_not_ignored', self.codes(report, 'WARNING'))
        self.config['generated']['policy'] = 'tracked'
        self.assertNotIn('generated_not_ignored', self.codes(self.run_validate()))

    def test_validation_does_not_modify_the_project_tree(self):
        (self.project / 'scratch.tmp').write_text('dirty')       # an existing dirty file must be left alone
        self.run_validate()                                      # writes adapter.json (the test's own config) first
        def snapshot():
            return {p.relative_to(self.dir).as_posix(): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
                    for p in self.dir.rglob('*') if p.name != 'adapter.json'}   # the test helper's own config
        before = snapshot()
        self.run_validate()
        self.assertEqual(snapshot(), before)


class NoExecution(Base):
    def test_validator_cannot_spawn_processes(self):
        tree = ast.parse((ADAPTER / 'validate_adapter.py').read_text())
        imported = {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {'subprocess', 'multiprocessing', 'pty', 'ctypes', 'socket', 'urllib', 'http'}, imported)
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertFalse(calls & {'system', 'popen', 'execv', 'execvp', 'spawn', 'Popen', 'run', 'check_call', 'write_text',
                                  'write_bytes', 'unlink', 'rmdir', 'mkdir', 'rename', 'chmod'}, calls)

    def test_executable_runner_and_marker_are_never_run_during_validation(self):
        marker = self.dir / 'EXECUTED'
        runner = self.project / 'tools' / 'run_godot.sh'
        runner.write_text(f'#!/bin/sh\ntouch "{marker}"\n')
        runner.chmod(0o755)
        (self.project / 'tests' / 'run_smoke.gd').write_text('extends SceneTree\n')
        trap = mock.Mock(side_effect=AssertionError('process spawned during validation'))
        import subprocess
        with mock.patch.object(subprocess, 'Popen', trap), mock.patch.object(subprocess, 'run', trap), \
                mock.patch.object(os, 'system', trap), mock.patch.object(os, 'execv', trap), mock.patch.object(os, 'popen', trap):
            report = self.run_validate()
        self.assertEqual(report['adapter_state'], 'ADAPTER_READY')
        self.assertFalse(marker.exists())
        trap.assert_not_called()

    def test_malicious_looking_declarations_are_data_only(self):
        self.config['commands'][1]['args'] = ['--headless', ';touch', 'EXECUTED']
        self.config['runners'][0]['approved'] = True
        self.config['approvals'] = {'execution_approved_by': 'owner', 'approved_revision': 'r1'}
        self.run_validate()
        self.assertFalse((self.dir / 'EXECUTED').exists())

    def test_unexpected_failure_fails_closed(self):
        with mock.patch.object(va, '_validate', side_effect=RuntimeError('boom')):
            report = self.run_validate()
        self.assertBlocked(report, 'validation_error')


class DocumentationStaysInSync(unittest.TestCase):
    def test_schema_file_matches_the_validator(self):
        schema = json.loads((ADAPTER / 'godot-adapter.schema.json').read_text())
        self.assertEqual(set(schema['properties']), va.TOP_KEYS)
        self.assertEqual(set(schema['required']), va.TOP_KEYS)
        for section, keys in (('project', 'project'), ('godot', 'godot'), ('paths', 'paths'), ('generated', 'generated'),
                              ('isolation', 'isolation'), ('evidence', 'evidence'), ('approvals', 'approvals')):
            self.assertEqual(set(schema['properties'][section]['properties']), va.SECTION_KEYS[keys], section)
        self.assertEqual(set(schema['properties']['runners']['items']['properties']), va.SECTION_KEYS['runner'])
        self.assertEqual(set(schema['properties']['commands']['items']['properties']), va.SECTION_KEYS['command'])
        self.assertEqual(set(schema['properties']['commands']['items']['properties']['role']['enum']), set(va.ROLES))

    def test_readme_documents_every_finding_code_gate_and_state(self):
        text = (ADAPTER / 'README.md').read_text()
        for code in va.FINDING_CODES:
            self.assertIn(f'`{code}`', text, code)
        for gate in va.GATES:
            self.assertRegex(text, rf'\b{gate}\b')
        for state in ('ADAPTER_READY', 'RUNTIME_QUALIFIED', 'DEVELOPMENT_QUALIFIED'):
            self.assertIn(state, text)

    def test_codes_flag_lists_the_registry(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(va.main(['--config', 'x', '--project', 'y', '--codes']), 0)
        self.assertEqual(set(json.loads(buffer.getvalue())), set(va.FINDING_CODES))

    def test_adapter_has_no_fob_or_agent_specific_content(self):
        for path in ADAPTER.rglob('*'):
            if path.is_file() and path.suffix in {'.py', '.json', '.md', '.gd', '.sh', '.godot'}:
                text = path.read_text().lower()
                for word in ('fix one', 'fob', 'game studio', 'claude', 'codex', 'copilot'):
                    self.assertNotRegex(text, rf'\b{re.escape(word)}\b', f'{word} in {path.name}')


if __name__ == '__main__':
    unittest.main()
