"""Golden-schema and failure-code registry tests for scripts/verify_scope.py.

Golden files in tests/golden/ pin the exact report shape for each scenario. Volatile values (commit and file hashes)
are normalised. To accept an intentional contract change, review the diff, then regenerate with
`UPDATE_GOLDEN=1 python3 -B -m unittest tests.test_verify_contract` and document the change in RESULT_CONTRACT.md.
"""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / 'tests' / 'golden'


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vs = load('verify_scope_contract', 'scripts/verify_scope.py')
base_tests = load('verify_scope_base_tests', 'tests/test_verify_scope.py')
run, cli = base_tests.run, base_tests.cli

TOP_LEVEL = {'schema', 'registry_version', 'status', 'computed_status', 'failure_reasons', 'recovery', 'limitations'}
FULL = TOP_LEVEL | {'task_id', 'claimed_status', 'baseline_sha', 'head_sha', 'modified_paths', 'evidence', 'trust',
                    'agent_reported_failure_reasons', 'ignored_paths_count'}
OPTIONAL = {'dirty_baseline_changed_since_record'}
EVIDENCE_KEYS = {'ref', 'sha256', 'origin', 'integrity', 'execution'}
TRUST_KEYS = {'baseline', 'hash_integrity', 'custody', 'independent_execution', 'agent_assertions'}


def normalise(value):
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'\b[0-9a-f]{64}\b', '<sha256>', value)
        return re.sub(r'\b[0-9a-f]{40}\b', '<sha1>', value)
    return value


class Scenarios(base_tests.Fixture):
    def golden(self, name, report):
        text = json.dumps(normalise(report), indent=2, sort_keys=True) + '\n'
        path = GOLDEN / f'{name}.json'
        if os.environ.get('UPDATE_GOLDEN') == '1':
            GOLDEN.mkdir(exist_ok=True)
            path.write_text(text)
        self.assertTrue(path.is_file(), f'missing golden file {path.name}; run with UPDATE_GOLDEN=1 and review it')
        self.assertEqual(text, path.read_text(), f'report for {name} no longer matches tests/golden/{name}.json')

    def run_with(self, data, **kwargs):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        return vs.verify(self.repo, path, **kwargs)

    def edit(self):
        self.write('src/app.py', 'x = 2\n')

    def seal(self, *refs):
        out = self.meta / 'manifest.json'
        cwd = os.getcwd()
        os.chdir(self.meta)
        try:
            self.assertEqual(cli('seal', '--out', str(out), *refs), 0)
        finally:
            os.chdir(cwd)
        return out

    def commit_ignore(self, *patterns):
        self.write('.gitignore', ''.join(p + '\n' for p in patterns))
        run(self.repo, 'add', '.gitignore')
        run(self.repo, 'commit', '-q', '-m', 'ignore')
        self.base = run(self.repo, 'rev-parse', 'HEAD')

    # --- statuses
    def test_golden_pass(self):
        self.edit()
        self.golden('pass', self.verify(self.contract()))

    def test_golden_partial_dirty_baseline(self):
        self.edit()
        self.golden('partial_dirty_baseline', self.verify(self.contract(baseline_dirty_paths=['src/app.py'])))

    def test_golden_partial_failed_check_false_pass(self):
        self.edit()
        failing = [{'command': 'pytest', 'exit_code': 1, 'evidence': 'out.txt'}]
        self.golden('partial_failed_check_false_pass', self.verify(self.contract(verification=failing)))

    # --- scope
    def test_golden_blocked_scope_violations(self):
        self.edit()
        self.write('docs/a.md', 'x\n')
        self.write('secrets/k.txt', 'x\n')
        self.write('AGENTS.md', 'x\n')
        self.write('tests/test_app.py', 'x\n')
        (self.repo / 'src/link.py').symlink_to('app.py')
        paths = ['src/app.py', 'docs/a.md', 'secrets/k.txt', 'AGENTS.md', 'tests/test_app.py', 'src/link.py']
        self.golden('blocked_scope_violations', self.verify(self.contract(modified_paths=paths[:-1])))  # also undeclared link

    # --- baseline integrity
    def test_golden_blocked_baseline_not_ancestor(self):
        self.edit()
        run(self.repo, 'checkout', '-q', '--orphan', 'rewritten')
        run(self.repo, 'commit', '-q', '-m', 'rewritten', '--allow-empty')
        self.golden('blocked_baseline_not_ancestor', self.verify(self.contract()))

    def test_golden_blocked_baseline_record_mismatch(self):
        self.write('src/pre.py', 'pre\n')
        record = self.meta / 'baseline.json'
        self.assertEqual(cli('baseline', '--repo', str(self.repo), '--out', str(record)), 0)
        self.edit()
        data = self.contract(modified_paths=['src/app.py', 'src/pre.py'], baseline_dirty_paths=[])
        self.golden('blocked_baseline_record_mismatch', self.run_with(data, baseline_record=record))

    def test_golden_blocked_record_tampered(self):
        record = self.meta / 'baseline.json'
        self.assertEqual(cli('baseline', '--repo', str(self.repo), '--out', str(record)), 0)
        body = json.loads(record.read_text())
        body['baseline_dirty_paths'] = ['x']
        record.write_text(json.dumps(body))
        self.golden('blocked_record_tampered', self.error_report(self.contract(), '--baseline-record', str(record)))

    # --- evidence trust
    def test_golden_pass_sealed_evidence(self):
        self.edit()
        report = self.run_with(self.contract(), evidence_manifest=self.seal('out.txt'), require_sealed=True)
        self.golden('pass_sealed_evidence', report)

    def test_golden_partial_evidence_not_sealed(self):
        self.edit()
        self.golden('partial_evidence_not_sealed', self.run_with(self.contract(), require_sealed=True))

    def test_golden_blocked_evidence_tampered(self):
        self.edit()
        manifest = self.seal('out.txt')
        (self.meta / 'out.txt').write_text('edited later\n')
        self.golden('blocked_evidence_tampered', self.run_with(self.contract(), evidence_manifest=manifest))

    def test_golden_blocked_evidence_pin_mismatch(self):
        self.edit()
        pinned = [{'command': 'c', 'exit_code': 0, 'evidence': 'out.txt', 'sha256': 'a' * 64}]
        self.golden('blocked_evidence_pin_mismatch', self.verify(self.contract(verification=pinned)))

    # --- unknown or missing evidence, interrupted execution
    def test_golden_blocked_missing_evidence(self):
        self.edit()
        missing = [{'command': 'c', 'exit_code': 0, 'evidence': 'nope.txt'}]
        self.golden('blocked_missing_evidence', self.verify(self.contract(verification=missing)))

    def test_golden_blocked_no_evidence_at_all(self):
        self.edit()
        self.golden('blocked_no_evidence_at_all', self.verify(self.contract(verification=[])))

    def test_golden_blocked_interrupted_execution(self):
        self.edit()
        data = self.contract(execution_state='interrupted', required_verification=['python -m unittest', 'ruff check .'])
        self.golden('blocked_interrupted_execution', self.verify(data))

    # --- ignored files
    def test_golden_partial_ignored_baseline_unknown(self):
        self.commit_ignore('hidden.txt')
        self.write('hidden.txt', 'x\n')
        self.golden('partial_ignored_baseline_unknown', self.verify(self.contract(baseline_sha=self.base, modified_paths=[])))

    def test_golden_blocked_ignored_unapproved(self):
        self.commit_ignore('hidden.txt')
        self.write('hidden.txt', 'x\n')
        data = self.contract(baseline_sha=self.base, modified_paths=[], baseline_ignored_paths=[])
        self.golden('blocked_ignored_unapproved', self.verify(data))

    def test_golden_partial_ignored_truncated(self):
        self.commit_ignore('*.log')
        self.write('a.log', 'x\n')
        self.write('b.log', 'x\n')
        with mock.patch.object(base_tests.vs, 'IGNORED_CAP', 1):
            report = self.verify(self.contract(baseline_sha=self.base, modified_paths=[], baseline_ignored_paths=[]))
        self.golden('partial_ignored_truncated', report)

    # --- error reports (fail closed before a normal report exists)
    def error_report(self, data, *extra):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = vs.main(['verify', '--repo', str(self.repo), '--result', str(path), *extra])
        self.assertEqual(code, 2)
        return json.loads(buffer.getvalue())

    def test_golden_blocked_malformed_contract(self):
        self.golden('blocked_malformed_contract', self.error_report({'schema': 'wrong/1'}))

    def test_golden_blocked_executable_git_config(self):
        run(self.repo, 'config', 'filter.evil.clean', '/bin/true')
        self.golden('blocked_executable_git_config', self.error_report(self.contract()))


class ContractStabilityTests(unittest.TestCase):
    def golden_reports(self):
        files = sorted(GOLDEN.glob('*.json'))
        self.assertTrue(files, 'no golden files found')
        return {f.name: json.loads(f.read_text()) for f in files}

    def test_registry_is_well_formed_and_versioned(self):
        self.assertEqual(vs.REGISTRY_VERSION, 1)
        for code, (severities, meaning) in vs.FAILURE_CODES.items():
            self.assertRegex(code, r'^[a-z][a-z_]*$')
            self.assertTrue(set(severities) <= {'PARTIAL', 'BLOCKED'} and severities, code)
            self.assertTrue(meaning.strip(), code)

    def test_codes_subcommand_prints_the_registry(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(vs.main(['codes']), 0)
        printed = json.loads(buffer.getvalue())
        self.assertEqual(set(printed['codes']), set(vs.FAILURE_CODES))
        self.assertEqual(printed['registry_version'], vs.REGISTRY_VERSION)

    def test_every_emitted_code_is_registered_and_every_registered_code_is_emitted(self):
        source = (ROOT / 'scripts/verify_scope.py').read_text()
        emitted = set(re.findall(r"add\('(?:BLOCKED|PARTIAL)',\s*'([a-z_]+)'", source))
        emitted |= {f'{kind}_path_modified_unapproved' for kind in ('test', 'governance')
                    if "f'{kind}_path_modified_unapproved'" in source}
        emitted |= set(re.findall(r'\(code: ([a-z_]+)\)', source))
        emitted |= {'false_pass', 'verification_error'} & set(re.findall(r"'(false_pass|verification_error)'", source))
        self.assertEqual(emitted, set(vs.FAILURE_CODES))

    def test_recovery_guidance_only_references_registered_codes(self):
        self.assertLessEqual(set(vs.RECOVERY) - {'default'}, set(vs.FAILURE_CODES))

    def test_every_code_is_documented(self):
        text = (ROOT / 'RESULT_CONTRACT.md').read_text()
        for code in vs.FAILURE_CODES:
            self.assertIn(f'`{code}`', text, f'{code} is missing from RESULT_CONTRACT.md')

    def test_every_registered_code_appears_in_a_golden_report(self):
        seen = {r['code'] for report in self.golden_reports().values() for r in report['failure_reasons']}
        self.assertEqual(set(vs.FAILURE_CODES) - seen, set(), 'add a golden scenario for each registered code')
        self.assertEqual(seen - set(vs.FAILURE_CODES), set())

    def test_golden_reports_follow_the_schema(self):
        statuses = set()
        for name, report in self.golden_reports().items():
            with self.subTest(report=name):
                self.assertEqual(report['schema'], 'ai-sdlc-lite-verification/1')
                self.assertEqual(report['registry_version'], vs.REGISTRY_VERSION)
                self.assertIn(report['status'], vs.STATUSES)
                statuses.add(report['status'])
                keys = set(report)
                self.assertTrue(TOP_LEVEL <= keys <= FULL | OPTIONAL, sorted(keys ^ FULL))
                worst = 'PASS'
                for reason in report['failure_reasons']:
                    self.assertEqual(set(reason), {'severity', 'code', 'detail'})
                    self.assertIn(reason['severity'], vs.FAILURE_CODES[reason['code']][0])
                    if vs.RANK[reason['severity']] > vs.RANK[worst]:
                        worst = reason['severity']
                self.assertEqual(report['computed_status'], worst)
                self.assertGreaterEqual(vs.RANK[report['status']], vs.RANK[worst])   # never better than computed
                self.assertEqual(set(report['recovery']), {'automatic_recovery', 'guidance'})
                self.assertEqual(report['recovery']['automatic_recovery'], 'none')
                if report['status'] == 'PASS':
                    self.assertEqual((report['failure_reasons'], report['recovery']['guidance']), ([], []))
                else:
                    self.assertTrue(report['recovery']['guidance'][0].startswith('Owner-controlled recovery'))
                if 'trust' in report:
                    self.assertEqual(set(report['trust']), TRUST_KEYS)
                    self.assertTrue(report['trust']['independent_execution'].startswith('not verified'))
                    self.assertTrue(report['trust']['custody'].startswith('unauthenticated'))
                    self.assertTrue(report['trust']['agent_assertions'].startswith('unverified'))
                    for entry in report['evidence']:
                        self.assertEqual(set(entry), EVIDENCE_KEYS)
                        self.assertEqual((entry['origin'], entry['execution']), ('agent-reported', 'not-verified'))
                        self.assertIn(entry['integrity'], {'unchecked', 'pinned', 'sealed', 'pinned+sealed', 'mismatch'})
                    self.assertGreaterEqual(len(report['limitations']), 4)
        self.assertEqual(statuses, {'PASS', 'PARTIAL', 'BLOCKED'})

    def test_no_golden_report_claims_independent_verification(self):
        for name, report in self.golden_reports().items():
            blob = json.dumps(report).lower()
            self.assertNotIn('independently verified', blob, name)
            self.assertNotIn('"independent"', blob, name)


if __name__ == '__main__':
    unittest.main()
