"""Deterministic tests for the provider adapter contract (ai-sdlc-adapter/1) and the `adapter` CLI namespace.

Offline and read-only. No provider is executed, probed or installed; fixtures are synthetic.
"""

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_sdlc import adapters  # noqa: E402

PROVIDERS = ('claude-code', 'copilot', 'codex')
CAPABILITIES = ('version_detect', 'skill_install', 'skill_discovery', 'skill_invocation', 'instruction_file',
                'noninteractive_run', 'structured_output', 'resume', 'cancellation', 'timeout', 'native_sandbox',
                'native_approval', 'usage_reporting')
STATUSES = ('SUPPORTED', 'NOT_QUALIFIED', 'UNKNOWN', 'UNSUPPORTED')
NEEDED = ('AGENTS.md', '.agents/skills/ai-sdlc-lite/SKILL.md', 'QUALIFICATION.md', 'QUALIFICATION_MATRIX.md', 'README.md',
          'scripts/install_skill.py', 'adapters/agents/codex/README.md', 'adapters/agents/codex/examples/declaration.json')
S, N, U = 'SUPPORTED', 'NOT_QUALIFIED', 'UNKNOWN'
EXPECTED = {  # the locked classification; any change must be a deliberate, evidence-backed edit
    'claude-code': dict.fromkeys(CAPABILITIES, U),
    'copilot': {'version_detect': S, 'skill_install': S, 'skill_discovery': S, 'skill_invocation': N,
                'instruction_file': N, 'noninteractive_run': U, 'structured_output': U, 'resume': U, 'cancellation': U,
                'timeout': U, 'native_sandbox': N, 'native_approval': N, 'usage_reporting': U},
    'codex': {'version_detect': S, 'skill_install': N, 'skill_discovery': N, 'skill_invocation': S,
              'instruction_file': N, 'noninteractive_run': U, 'structured_output': U, 'resume': U, 'cancellation': U,
              'timeout': U, 'native_sandbox': N, 'native_approval': N, 'usage_reporting': U},
}
UNSAFE = ('\x1b', '\u009b', '\u0085', '\u2028', '\u202e', '\u200b', '\u00a0', '\u3000', '\ufffd', '\ue000')


def cli_env(**extra):
    env = dict(os.environ)
    env.update({'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1'})
    env.update(extra)
    return env


def run_cli(*args, cwd=None, env=None):
    done = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', *args], cwd=cwd, env=env or cli_env(), capture_output=True)
    return done.returncode, done.stdout.decode('utf-8', errors='replace'), done.stderr.decode('utf-8', errors='replace')


def tree_digest(root):
    digest = hashlib.sha256()
    for current, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(dirs):
            digest.update(('D:' + os.path.relpath(os.path.join(current, name), root) + '\n').encode())
        for name in sorted(files):
            path = os.path.join(current, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                digest.update(('L:' + rel + '>' + os.readlink(path) + '\n').encode())
                continue
            with open(path, 'rb') as handle:
                data = handle.read()
            digest.update(('F:' + rel + ':' + str(len(data)) + ':').encode() + hashlib.sha256(data).digest())
    return digest.hexdigest()


class Project(unittest.TestCase):
    """A disposable project holding just the evidence files the declarations cite."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.project = self.base / 'project'
        for rel in NEEDED:
            target = self.project / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)
        self.vocab, error = adapters.load_vocabulary()
        self.assertIsNone(error)
        self.good = json.loads((ROOT / 'adapters/agents/copilot/provider-adapter.json').read_text(encoding='utf-8'))

    def declaration(self):
        return copy.deepcopy(self.good)

    def write(self, data, name='decl.json'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding='utf-8')
        return path

    def check(self, data, name='decl.json'):
        report, _ = adapters.validate_declaration(self.write(data, name), self.project, self.vocab)
        return report

    def assert_valid(self, data):
        report = self.check(data)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['state'], 'ADAPTER_DECLARATION_VALID')
        return report

    def assert_invalid(self, data, fragment=None):
        report = self.check(data)
        self.assertEqual(report['state'], 'INVALID', 'declaration was accepted')
        self.assertTrue(report['errors'])
        if fragment:
            self.assertTrue(any(fragment in e for e in report['errors']), (fragment, report['errors']))
        for error in report['errors']:
            self.assertTrue(error.isascii() or not any(c in error for c in UNSAFE), error)
        return report


class ShippedDeclarations(Project):
    def test_all_three_providers_validate(self):
        for provider in PROVIDERS:
            with self.subTest(provider=provider):
                report, data = adapters.validate_declaration(ROOT / f'adapters/agents/{provider}/provider-adapter.json', ROOT)
                self.assertEqual((report['state'], report['errors'], report['provider']), ('ADAPTER_DECLARATION_VALID', [], provider))
                self.assertEqual(data['provider'], provider)

    def test_report_never_claims_execution_probing_or_qualification(self):
        report, _ = adapters.validate_declaration(ROOT / 'adapters/agents/codex/provider-adapter.json', ROOT)
        self.assertIs(report['execution_authorized'], False)
        self.assertIs(report['provider_executed'], False)
        self.assertIs(report['version_probed'], False)
        self.assertIs(report['effective_permissions_verified'], False)
        self.assertEqual(report['qualification'], {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'})

    def test_exact_vocabulary(self):
        self.assertEqual(tuple(self.vocab['providers']), PROVIDERS)
        self.assertEqual(tuple(self.vocab['statuses']), STATUSES)
        self.assertEqual(tuple(self.vocab['capabilities']), CAPABILITIES)
        self.assertEqual(tuple(self.vocab['bases']), ('observed', 'documented', 'configuration', 'none'))
        for provider in PROVIDERS:
            data = json.loads((ROOT / f'adapters/agents/{provider}/provider-adapter.json').read_text(encoding='utf-8'))
            self.assertEqual(tuple(data['capabilities']), CAPABILITIES, provider)

    def test_locked_classification_per_provider(self):
        for provider in PROVIDERS:
            data = json.loads((ROOT / f'adapters/agents/{provider}/provider-adapter.json').read_text(encoding='utf-8'))
            actual = {name: entry['status'] for name, entry in data['capabilities'].items()}
            self.assertEqual(actual, EXPECTED[provider], provider)

    def test_declarations_stay_inside_their_evidence(self):
        for provider in PROVIDERS:
            data = json.loads((ROOT / f'adapters/agents/{provider}/provider-adapter.json').read_text(encoding='utf-8'))
            self.assertIs(data['execution_authorized'], False)
            self.assertEqual(data['qualification'], {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'})
            self.assertEqual(data['provider_version']['compatibility_claim'], 'none')

    def test_versions_and_instructions_agree_with_existing_records(self):
        installer = (ROOT / 'scripts/install_skill.py').read_text(encoding='utf-8')
        copilot_version = re.search(r'restricted to CLI (\d+\.\d+\.\d+)', installer).group(1)
        schema = json.loads((ROOT / 'adapters/agents/codex/codex-adapter.schema.json').read_text(encoding='utf-8'))
        existing = json.loads((ROOT / 'adapters/agents/codex/examples/declaration.json').read_text(encoding='utf-8'))
        load = lambda p: json.loads((ROOT / f'adapters/agents/{p}/provider-adapter.json').read_text(encoding='utf-8'))
        self.assertEqual(load('copilot')['provider_version']['observed'], copilot_version)
        self.assertEqual(load('codex')['provider_version']['observed'], schema['properties']['cli_version']['const'])
        self.assertEqual(load('codex')['provider_version']['observed'], existing['cli_version'])
        self.assertEqual(load('codex')['instruction_files'], existing['instruction_paths'])
        self.assertEqual(load('codex')['skill']['source_path'], existing['skill_path'])
        self.assertIsNone(load('claude-code')['provider_version']['observed'])

    def test_declarations_do_not_exceed_the_qualification_matrix(self):
        text = (ROOT / 'QUALIFICATION_MATRIX.md').read_text(encoding='utf-8')
        rows = {name: next(line for line in text.splitlines() if line.startswith('| ' + name + ' |'))
                for name in ('GitHub Copilot CLI', 'OpenAI Codex', 'Claude Code')}
        cells = {name: [c.strip() for c in row.split('|')] for name, row in rows.items()}
        for name in rows:
            self.assertEqual(cells[name][6], 'NOT RUN', name)  # deep
        self.assertTrue(cells['Claude Code'][2].startswith('UNKNOWN'))
        self.assertTrue(cells['Claude Code'][5].startswith('NOT RUN'))
        self.assertIn('1.0.109', rows['GitHub Copilot CLI'])
        self.assertIn('0.167.2', rows['OpenAI Codex'])
        self.assertIn('UNVERIFIED', cells['OpenAI Codex'][4])
        claude = json.loads((ROOT / 'adapters/agents/claude-code/provider-adapter.json').read_text(encoding='utf-8'))
        self.assertEqual({e['status'] for e in claude['capabilities'].values()}, {'UNKNOWN'})


class StatusEvidenceConsistency(Project):
    def setCap(self, name, **changes):
        data = self.declaration()
        data['capabilities'][name].update(changes)
        return data

    def test_supported_requires_observed_basis_and_evidence(self):
        self.assert_invalid(self.setCap('skill_invocation', status='SUPPORTED', basis='documented'), 'SUPPORTED requires')
        self.assert_invalid(self.setCap('skill_invocation', status='SUPPORTED', basis='observed', evidence=[]), 'SUPPORTED requires')
        self.assert_invalid(self.setCap('skill_install', basis='configuration'), 'SUPPORTED requires')
        self.assert_invalid(self.setCap('skill_install', basis='none'), 'SUPPORTED requires')

    def test_not_qualified_requires_documentation_or_configuration_evidence(self):
        self.assert_invalid(self.setCap('instruction_file', basis='observed'), 'NOT_QUALIFIED requires')
        self.assert_invalid(self.setCap('instruction_file', basis='none'), 'NOT_QUALIFIED requires')
        self.assert_invalid(self.setCap('instruction_file', evidence=[]), 'NOT_QUALIFIED requires')
        self.assert_valid(self.setCap('instruction_file', basis='configuration'))

    def test_unknown_requires_no_basis_and_no_evidence(self):
        self.assert_invalid(self.setCap('resume', evidence=['README.md']), 'UNKNOWN requires')
        self.assert_invalid(self.setCap('resume', basis='observed'), 'UNKNOWN requires')
        self.assert_invalid(self.setCap('resume', basis='documented'), 'UNKNOWN requires')

    def test_unsupported_requires_evidence_of_absence(self):
        self.assert_invalid(self.setCap('resume', status='UNSUPPORTED'), 'UNSUPPORTED requires')
        self.assert_invalid(self.setCap('resume', status='UNSUPPORTED', basis='configuration', evidence=['README.md']), 'UNSUPPORTED requires')
        self.assert_valid(self.setCap('resume', status='UNSUPPORTED', basis='documented', evidence=['README.md']))
        self.assert_valid(self.setCap('resume', status='UNSUPPORTED', basis='observed', evidence=['QUALIFICATION.md']))

    def test_invalid_vocabulary_values(self):
        for value in ('supported', 'PASS', 'QUALIFIED', '', None, 7, ['SUPPORTED'], {'a': 1}):
            with self.subTest(status=value):
                self.assert_invalid(self.setCap('resume', status=value), 'invalid status')
        for value in ('guess', '', None, ['none']):
            with self.subTest(basis=value):
                self.assert_invalid(self.setCap('resume', basis=value), 'invalid basis')

    def test_missing_and_unknown_capabilities(self):
        data = self.declaration()
        del data['capabilities']['timeout']
        self.assert_invalid(data, 'missing capability timeout')
        data = self.declaration()
        data['capabilities']['telepathy'] = data['capabilities']['timeout']
        self.assert_invalid(data, 'unknown capability')
        data = self.declaration()
        data['capabilities']['timeout']['extra'] = 1
        self.assert_invalid(data, 'unknown field')
        data = self.declaration()
        del data['capabilities']['timeout']['note']
        self.assert_invalid(data, 'missing field note')

    def test_evidence_must_exist_and_be_unique_and_bounded(self):
        self.assert_invalid(self.setCap('skill_install', evidence=['no/such/file.md']), 'not a contained regular file')
        self.assert_invalid(self.setCap('skill_install', evidence=['README.md', 'README.md']), 'unique')
        self.assert_invalid(self.setCap('skill_install', evidence=['README.md'] * 1 + ['QUALIFICATION.md', 'AGENTS.md', 'scripts/install_skill.py', 'QUALIFICATION_MATRIX.md', '.agents/skills/ai-sdlc-lite/SKILL.md']), 'at most 5')
        self.assert_invalid(self.setCap('skill_install', evidence='README.md'), 'list')

    def test_instruction_files_agree_with_the_capability(self):
        data = self.declaration()
        data['instruction_files'] = []
        self.assert_invalid(data, 'instruction_files must be non-empty')
        data = json.loads((ROOT / 'adapters/agents/claude-code/provider-adapter.json').read_text(encoding='utf-8'))
        data['instruction_files'] = ['AGENTS.md']
        self.assert_invalid(data, 'instruction_files must be non-empty')


class VersionSchemaAndFixedFields(Project):
    def test_schema_and_provider(self):
        for value in ('ai-sdlc-adapter/2', '', None, 1):
            data = self.declaration()
            data['schema'] = value
            self.assert_invalid(data, 'schema must be')
        for value in ('gemini', 'Copilot', '', None, ['copilot']):
            data = self.declaration()
            data['provider'] = value
            self.assert_invalid(data, 'provider must be one of')

    def test_observed_version_is_numeric_or_null(self):
        for value in ('1.2.3', '1.0', '10.20.30.40', None):
            data = self.declaration()
            data['provider_version']['observed'] = value
            self.assert_valid(data)
        for value in ('v1.2.3', '1', '1.2.3-beta', 'latest', '^1.0.0', '1.2.3 ', '', 5, ['1.2.3'], '1..2'):
            with self.subTest(value=value):
                data = self.declaration()
                data['provider_version']['observed'] = value
                self.assert_invalid(data, 'observed must be null or a numeric version')

    def test_no_compatibility_claim_and_no_authority_and_no_qualification(self):
        for value in ('compatible', 'exact', True, None, ''):
            data = self.declaration()
            data['provider_version']['compatibility_claim'] = value
            self.assert_invalid(data, 'compatibility_claim')
        for value in (True, 'false', 0, None, 'no'):
            data = self.declaration()
            data['execution_authorized'] = value
            self.assert_invalid(data, 'execution_authorized must be false')
        data = self.declaration()
        del data['execution_authorized']
        self.assert_invalid(data, 'missing field execution_authorized')
        for key in ('smoke', 'deep'):
            for value in ('PASS', 'QUALIFIED', 'PARTIAL', 'SUPPORTED', None, False):
                data = self.declaration()
                data['qualification'][key] = value
                self.assert_invalid(data, 'must be NOT_RUN')
        data = self.declaration()
        data['qualification']['unattended'] = 'QUALIFIED'
        self.assert_invalid(data, 'unknown field')

    def test_unknown_and_missing_top_level_fields(self):
        data = self.declaration()
        data['qualified'] = True
        self.assert_invalid(data, 'unknown field')
        for key in list(self.good):
            data = self.declaration()
            del data[key]
            self.assert_invalid(data, 'missing field')

    def test_platforms_limitations_and_skill(self):
        for value in (['plan9'], ['linux', 'linux'], 'linux', [1]):
            data = self.declaration()
            data['platforms_observed'] = value
            self.assert_invalid(data, 'platforms_observed')
        for value in ([], ['x'] * 11, 'text', [1], ['']):
            data = self.declaration()
            data['limitations'] = value
            self.assert_invalid(data)
        data = self.declaration()
        data['skill']['source_path'] = 'README.md'
        self.assert_invalid(data, 'skill.source_path must be')
        (self.project / '.agents/skills/ai-sdlc-lite/SKILL.md').write_text('')
        self.assert_invalid(self.declaration(), 'is empty')


class HostileInputs(Project):
    def test_duplicate_keys_constants_encoding_size_and_shape(self):
        text = json.dumps(self.good)
        dup = text.replace('"provider": "copilot"', '"provider": "copilot", "provider": "codex"', 1)
        self.assertNotEqual(dup, text)
        cases = {'duplicate keys': dup, 'NaN': text[:-1] + ', "x": NaN}', 'Infinity': text[:-1] + ', "x": Infinity}',
                 'empty': '', 'list': '[1]', 'string': '"x"', 'truncated': text[: len(text) // 2],
                 'nesting': '{"a":' * 4000 + '1' + '}' * 4000, 'trailing garbage': text + ' x'}
        for label, content in cases.items():
            with self.subTest(case=label):
                report = self.check(content)
                self.assertEqual(report['state'], 'INVALID')
                self.assertTrue(report['errors'])
        path = self.project / 'binary.json'
        path.write_bytes(b'\xff\xfe\x00{')
        report, _ = adapters.validate_declaration(path, self.project, self.vocab)
        self.assertEqual(report['state'], 'INVALID')

    def test_oversized_files_are_rejected(self):
        padded = json.dumps(self.good)[:-1] + ',"pad": "' + 'a' * 70000 + '"}'
        report = self.check(padded)
        self.assertEqual(report['state'], 'INVALID')
        self.assertIn('larger than', report['errors'][0])
        data = self.declaration()
        data['capabilities']['resume']['note'] = 'n' * 241
        self.assert_invalid(data, 'note')
        data = self.declaration()
        data['limitations'] = ['l' * 401]
        self.assert_invalid(data)

    def test_deeply_nested_values_are_bounded(self):
        data = self.declaration()
        deep = 'x'
        for _ in range(20):
            deep = {'a': deep}
        data['limitations'] = [deep]
        self.assert_invalid(data, 'nested too deeply')

    def test_unsafe_unicode_is_rejected_everywhere_and_never_echoed(self):
        places = (('limitations', 0), ('note', None), ('evidence', None), ('provider', None), ('field name', None))
        for char in UNSAFE + ('\ud800',):
            for where, _ in places:
                with self.subTest(char=hex(ord(char)), where=where):
                    data = self.declaration()
                    value = 'a%sb' % char
                    if where == 'limitations':
                        data['limitations'] = [value]
                    elif where == 'note':
                        data['capabilities']['resume']['note'] = value
                    elif where == 'evidence':
                        data['capabilities']['skill_install']['evidence'] = [value]
                    elif where == 'provider':
                        data['provider'] = value
                    else:
                        data['capabilities'][value] = data['capabilities']['resume']
                    report = self.check(json.dumps(data))
                    self.assertEqual(report['state'], 'INVALID')
                    for error in report['errors']:
                        self.assertTrue(error.isascii(), error)
                        self.assertNotIn(char, error)

    def test_safe_unicode_text_is_accepted(self):
        data = self.declaration()
        data['capabilities']['resume']['note'] = 'Nota con acentos: caf\u00e9, \u65e5\u672c\u8a9e, \U0001f642'
        data['limitations'] = ['Limitaci\u00f3n con espacios normales y \u00fcn\u00efcode.']
        self.assert_valid(json.dumps(data, ensure_ascii=False))

    def test_non_ascii_space_variants_are_rejected(self):
        for char in ('\u00a0', '\u2003', '\u202f', '\u3000', '\u1680', '\u205f'):
            data = self.declaration()
            data['limitations'] = ['a%sb' % char]
            self.assert_invalid(json.dumps(data))


class PathContainment(Project):
    def test_unsafe_evidence_and_instruction_paths(self):
        bad = ['../README.md', 'a/../README.md', '/etc/passwd', '/tmp/x', 'README.md/', './README.md', 'a//b', '*', 'docs/*.md',
               'back\\slash', 'C:\\x', 'C:/x', '~/x', '$HOME/x', 'a/./b', '', '.', '..', 'x' * 300, 'weird[1].md', 'a{b}.md']
        for ref in bad:
            with self.subTest(ref=ref):
                data = self.declaration()
                data['capabilities']['skill_install']['evidence'] = [ref]
                self.assert_invalid(data, 'not a contained regular file')
                data = self.declaration()
                data['instruction_files'] = [ref]
                self.assert_invalid(data, 'instruction_files')

    def test_existing_files_with_glob_or_special_names_are_still_refused(self):
        names = ('weird[1].md', 'a{b}.md', 'star*.md', 'what?.md', '~tilde.md', '$dollar.md', 'back\\slash.md', 'colon:name.md')
        for name in names:
            try:
                (self.project / name).write_text('present\n')
            except OSError:
                continue
            with self.subTest(name=name):
                self.assertTrue((self.project / name).is_file())
                data = self.declaration()
                data['capabilities']['skill_install']['evidence'] = [name]
                self.assert_invalid(data, 'not a contained regular file')

    def test_directories_and_missing_files_are_not_evidence(self):
        for ref in ('scripts', 'adapters/agents', 'nothing.md'):
            data = self.declaration()
            data['capabilities']['skill_install']['evidence'] = [ref]
            self.assert_invalid(data, 'not a contained regular file')

    def test_symlinked_evidence_and_parent_directories_are_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'secret.md').write_text('CANARY-SECRET-5c1d\n')
        try:
            os.symlink(outside / 'secret.md', self.project / 'linked.md')
            os.symlink(outside, self.project / 'linkdir', target_is_directory=True)
            os.symlink(self.project / 'README.md', self.project / 'inside-link.md')
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        try:
            os.symlink(self.project / 'adapters', self.project / 'alias', target_is_directory=True)  # stays inside the project
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        for ref in ('linked.md', 'linkdir/secret.md', 'inside-link.md', 'alias/agents/codex/README.md'):
            with self.subTest(ref=ref):
                data = self.declaration()
                data['capabilities']['skill_install']['evidence'] = [ref]
                report = self.assert_invalid(data, 'not a contained regular file')
                self.assertNotIn('CANARY', json.dumps(report))

    def test_symlinked_declaration_files_are_rejected(self):
        real = self.write(self.good, 'real.json')
        outside = self.base / 'outside.json'
        outside.write_text(json.dumps(self.good))
        elsewhere = self.base / 'elsewhere'
        elsewhere.mkdir()
        (elsewhere / 'd.json').write_text(json.dumps(self.good))
        try:
            os.symlink(real, self.project / 'link.json')
            os.symlink(outside, self.base / 'outlink.json')
            os.symlink(elsewhere, self.project / 'sub', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        for config in (self.project / 'link.json', self.base / 'outlink.json', self.project / 'sub' / 'd.json'):
            with self.subTest(config=config.name):
                report, data = adapters.validate_declaration(config, self.project, self.vocab)
                self.assertEqual(report['state'], 'INVALID')
                self.assertIsNone(data)

    def test_project_and_config_outside_each_other_work_and_missing_files_fail(self):
        outside = self.base / 'outside.json'
        outside.write_text(json.dumps(self.good))
        report, _ = adapters.validate_declaration(outside, self.project, self.vocab)
        self.assertEqual(report['errors'], [])
        report, _ = adapters.validate_declaration(self.base / 'missing.json', self.project, self.vocab)
        self.assertEqual(report['state'], 'INVALID')
        empty = self.base / 'empty-project'
        empty.mkdir()
        report, _ = adapters.validate_declaration(outside, empty, self.vocab)
        self.assertEqual(report['state'], 'INVALID')
        self.assertTrue(any('instruction_files' in e or 'skill.source_path' in e or 'evidence' in e for e in report['errors']))


class VocabularyTamper(unittest.TestCase):
    def framework_copy(self, mutate=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        shutil.copytree(ROOT / 'adapters', base / 'adapters', ignore=shutil.ignore_patterns('godot', '__pycache__'))
        for rel in NEEDED:
            target = base / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(ROOT / rel, target)
        if mutate:
            mutate(base)
        return base

    def run_main(self, base, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(adapters, 'ROOT', base), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = adapters.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_untampered_copy_validates(self):
        code, out, _ = self.run_main(self.framework_copy(), 'validate')
        self.assertEqual(code, 0, out)

    def test_missing_or_malformed_schema_blocks_everything(self):
        def drop_schema(base):
            (base / 'adapters/adapter-contract.schema.json').unlink()

        def break_vocab(base):
            path = base / 'adapters/adapter-contract.schema.json'
            data = json.loads(path.read_text())
            data['x-vocabulary']['capabilities'].append('resume')
            path.write_text(json.dumps(data))

        def wrong_id(base):
            path = base / 'adapters/adapter-contract.schema.json'
            data = json.loads(path.read_text())
            data['$id'] = 'ai-sdlc-adapter/9'
            path.write_text(json.dumps(data))

        def extra_key(base):
            path = base / 'adapters/adapter-contract.schema.json'
            data = json.loads(path.read_text())
            data['x-vocabulary']['extra'] = ['x']
            path.write_text(json.dumps(data))

        for mutate in (drop_schema, break_vocab, wrong_id, extra_key):
            with self.subTest(mutate=mutate.__name__):
                for command in ('list', 'validate', 'matrix'):
                    code, out, err = self.run_main(self.framework_copy(mutate), command)
                    self.assertEqual(code, 2)
                    self.assertIn('BLOCKED', err)
                    self.assertEqual(out, '')

    def test_provider_must_match_its_directory(self):
        def swap(base):
            path = base / 'adapters/agents/codex/provider-adapter.json'
            data = json.loads(path.read_text())
            data['provider'] = 'copilot'
            path.write_text(json.dumps(data))

        code, out, _ = self.run_main(self.framework_copy(swap), 'validate')
        self.assertEqual(code, 2)
        self.assertIn('does not match its directory', out)
        code, out, err = self.run_main(self.framework_copy(swap), 'matrix')
        self.assertEqual((code, out), (2, ''))
        self.assertIn('codex', err)

    def test_missing_declaration_blocks_matrix(self):
        def drop(base):
            (base / 'adapters/agents/claude-code/provider-adapter.json').unlink()

        code, out, err = self.run_main(self.framework_copy(drop), 'matrix')
        self.assertEqual((code, out), (2, ''))
        self.assertIn('claude-code', err)


class MatrixAndCli(unittest.TestCase):
    def test_matrix_text_and_json_are_deterministic_and_match_the_classification(self):
        first = run_cli('adapter', 'matrix')
        with tempfile.TemporaryDirectory() as elsewhere:
            second = run_cli('adapter', 'matrix', cwd=elsewhere)
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertEqual(first[2], '')
        self.assertTrue(first[1].isascii())
        lines = first[1].splitlines()
        self.assertEqual(lines[0], 'AI-SDLC Lite provider adapter matrix (ai-sdlc-adapter/1)')
        self.assertEqual(lines[1].split(), ['capability', *PROVIDERS])
        for name, line in zip(CAPABILITIES, lines[2:2 + len(CAPABILITIES)]):
            self.assertEqual(line.split(), [name, *(EXPECTED[p][name] for p in PROVIDERS)])
        self.assertIn('observed version', lines[2 + len(CAPABILITIES)])
        self.assertIn('never authorizes execution', first[1])
        raw = run_cli('adapter', 'matrix', '--json')
        self.assertEqual(raw, run_cli('adapter', 'matrix', '--json'))
        document = json.loads(raw[1])
        self.assertEqual(list(document['providers']), list(PROVIDERS))
        self.assertEqual(document['capabilities'], list(CAPABILITIES))
        for provider in PROVIDERS:
            self.assertEqual(document['providers'][provider]['capabilities'], EXPECTED[provider])
            self.assertEqual(document['providers'][provider]['qualification'], {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'})
        self.assertIs(document['execution_authorized'], False)
        self.assertIs(document['version_probed'], False)
        self.assertEqual(document['providers']['claude-code']['observed_version'], None)

    def test_list_and_validate_succeed_from_anywhere(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            for args in (('adapter', 'list'), ('adapter', 'validate')):
                from_root, anywhere = run_cli(*args, cwd=ROOT), run_cli(*args, cwd=elsewhere)
                self.assertEqual(from_root, anywhere)
                self.assertEqual(from_root[0], 0, from_root)
                self.assertIn('RESULT: VALID', from_root[1])
                self.assertIn('no provider was executed or probed', from_root[1])
        out = run_cli('adapter', 'list')[1]
        self.assertIn('claude-code: ADAPTER_DECLARATION_VALID; observed version none', out)
        self.assertIn('copilot: ADAPTER_DECLARATION_VALID; observed version 1.0.109', out)
        self.assertIn('codex: ADAPTER_DECLARATION_VALID; observed version 0.167.2', out)

    def test_validate_a_single_config(self):
        good = ROOT / 'adapters/agents/copilot/provider-adapter.json'
        code, out, err = run_cli('adapter', 'validate', '--config', str(good), '--project', str(ROOT))
        self.assertEqual((code, err), (0, ''))
        self.assertIn('copilot: ADAPTER_DECLARATION_VALID', out)
        code, out, _ = run_cli('adapter', 'validate', '--project', str(ROOT), '--config', str(good))
        self.assertEqual(code, 0)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / 'bad.json'
            bad.write_text('{"schema": "ai-sdlc-adapter/1", "provider": "copilot", "execution_authorized": true}')
            code, out, err = run_cli('adapter', 'validate', '--config', str(bad), '--project', str(ROOT))
            self.assertEqual((code, err), (2, ''))
            self.assertIn('RESULT: INVALID', out)
            self.assertIn('execution_authorized must be false', out)

    def test_usage_errors_exit_2_and_never_echo_arguments(self):
        for args in ((), ('adapter',), ('adapter', 'frobnicate'), ('adapter', 'list', 'extra'), ('adapter', 'matrix', '--yaml'),
                     ('adapter', 'validate', '--config', 'x'), ('adapter', 'validate', '--project', 'x'),
                     ('adapter', 'validate', '--config', 'a', '--config', 'b', '--project', 'c'), ('adapter', 'validate', 'x')):
            with self.subTest(args=args):
                self.assertEqual(run_cli(*args)[0], 2)
        for hostile in ('bad\x1b[31m', 'x\u202ey', 'z\u009b0m'):
            code, out, err = run_cli('adapter', hostile)
            self.assertEqual((code, out), (2, ''))
            self.assertTrue(err.isascii() or all(c not in err for c in UNSAFE), err)
            self.assertFalse(any(c in err for c in ('\x1b', '\u202e', '\u009b')))
            code, out, err = run_cli('adapter', 'validate', '--config', hostile + '.json', '--project', str(ROOT))
            self.assertEqual(code, 2)
            self.assertFalse(any(c in out + err for c in ('\x1b', '\u202e', '\u009b')))
        self.assertEqual(run_cli('adapter', '--help')[0], 0)
        self.assertIn('adapter', run_cli('--help')[1])

    def test_unsafe_declaration_content_never_reaches_the_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads((ROOT / 'adapters/agents/copilot/provider-adapter.json').read_text(encoding='utf-8'))
            data['capabilities']['resume']['note'] = 'x\x1b[31mred\u202e'
            data['capabilities']['bad\x1b[2Jname'] = data['capabilities']['resume']
            data['limitations'] = ['a\u009b0m']
            data['extra\u2028field'] = 1
            path = Path(tmp) / 'hostile.json'
            path.write_text(json.dumps(data))
            code, out, err = run_cli('adapter', 'validate', '--config', str(path), '--project', str(ROOT))
        self.assertEqual(code, 2)
        for char in UNSAFE + ('\ud800',):
            self.assertNotIn(char, out + err)
        self.assertIn('\\x1b', out)  # shown escaped

    def test_existing_commands_are_unchanged(self):
        direct = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/verify_scope.py'), 'codes'], capture_output=True, env=cli_env())
        via = run_cli('codes')
        self.assertEqual((via[0], via[1]), (direct.returncode, direct.stdout.decode()))
        self.assertEqual(run_cli('doctor')[0], 0)
        self.assertEqual(run_cli('status')[0], 0)
        code, out, err = run_cli('frobnicate')
        self.assertEqual((code, out), (2, ''))
        self.assertIn('unknown command', err)
        self.assertEqual(run_cli()[0], 2)
        for command in ('verify', 'baseline', 'seal'):
            self.assertEqual(run_cli(command)[0], 2)


class ReadOnlyAndNoExecution(unittest.TestCase):
    def test_commands_write_nothing_and_spawn_nothing(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError('a subprocess, shell or network operation was attempted')

        before = tree_digest(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'c.json'
            config.write_text((ROOT / 'adapters/agents/codex/provider-adapter.json').read_text(encoding='utf-8'))
            empty_before = tree_digest(tmp)
            with mock.patch.object(subprocess, 'run', forbidden), mock.patch.object(subprocess, 'Popen', forbidden), \
                    mock.patch.object(os, 'system', forbidden), mock.patch.object(os, 'popen', forbidden), \
                    mock.patch.object(socket.socket, 'connect', forbidden), mock.patch.object(socket, 'create_connection', forbidden):
                for args in (['list'], ['validate'], ['matrix'], ['matrix', '--json'],
                             ['validate', '--config', str(config), '--project', str(ROOT)], ['validate', '--bogus'], ['nope']):
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        code = adapters.main(args)
                    self.assertIn(code, (0, 2), args)
            self.assertEqual(tree_digest(tmp), empty_before)
        self.assertEqual(tree_digest(ROOT), before)

    def test_no_provider_or_credential_or_config_access_in_the_source(self):
        source = (ROOT / 'ai_sdlc' / 'adapters.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imports, attrs = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imports.add((node.module or '').split('.')[0])
            elif isinstance(node, ast.Attribute):
                attrs.add(node.attr)
            elif isinstance(node, ast.Name):
                attrs.add(node.id)
        self.assertEqual(imports - {'json', 'os', 're', 'stat', 'sys', 'unicodedata', 'pathlib'}, set())
        for banned in ('subprocess', 'Popen', 'system', 'popen', 'environ', 'getenv', 'expanduser', 'which', 'connect',
                       'urlopen', 'socket', 'write_text', 'write_bytes', 'mkdir', 'unlink', 'rmdir', 'rename', 'replace', 'remove'):
            self.assertNotIn(banned, attrs, banned)
        for forbidden_open in ("'w'", '"w"', "'a'", '"a"', "'wb'", "'x'"):
            self.assertNotIn('open(' + forbidden_open, source)

    def test_python_39_syntax_and_standard_library_only(self):
        for name in ('adapters.py', 'cli.py'):
            path = ROOT / 'ai_sdlc' / name
            ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
        for rel in ('tests/test_adapter_contract.py',):
            ast.parse((ROOT / rel).read_text(encoding='utf-8'), feature_version=(3, 9))

    def test_display_rules_match_the_cli_implementation(self):
        from ai_sdlc import cli
        samples = ['plain', 'with space', 'caf\u00e9', '\u65e5\u672c\u8a9e', '\U0001f642', 'e\u0301'] + ['a%sb' % c for c in UNSAFE]
        samples += ['a\x00b', 'a\x7fb', 'a\ud800b', 'a\u2028b', 'a\u2029b', 'a\u200bb', 'a\u0085b', '']
        for text in samples:
            self.assertEqual(adapters._display_safe(text), cli._display_safe(text), repr(text))

    def test_hostile_project_content_is_never_executed(self):
        marker = Path(tempfile.mkdtemp()) / 'EXECUTED'
        self.addCleanup(shutil.rmtree, str(marker.parent), True)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for rel in NEEDED:
                target = project / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, target)
            (project / '.git').mkdir()
            (project / '.git' / 'config').write_text('[core]\n\tfsmonitor = touch %s\n' % marker)
            script = project / 'hook.sh'
            script.write_text('#!/bin/sh\ntouch %s\n' % marker)
            script.chmod(0o755)
            config = project / 'adapters' / 'agents' / 'copilot' / 'provider-adapter.json'
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text((ROOT / 'adapters/agents/copilot/provider-adapter.json').read_text(encoding='utf-8'))
            code, out, _ = run_cli('adapter', 'validate', '--config', str(config), '--project', str(project))
        self.assertEqual(code, 0, out)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
