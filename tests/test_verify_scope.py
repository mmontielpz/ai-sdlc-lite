"""Controlled-fixture tests for scripts/verify_scope.py (detection, not prevention)."""

import contextlib
import importlib.util
import io
import os
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_scope', ROOT / 'scripts/verify_scope.py')
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


def cli(*args):
    with contextlib.redirect_stdout(io.StringIO()):
        return vs.main(list(args))


def run(cwd, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name).resolve()
        self.repo, self.meta = base / 'repo', base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir()
        run(self.repo, 'init', '-q')
        for name, text in {'src/app.py': 'x = 1\n', 'tests/test_app.py': 'pass\n',
                           'AGENTS.md': 'rules\n', 'docs/a.md': 'a\n', 'secrets/k.txt': 'k\n'}.items():
            self.write(name, text)
        run(self.repo, 'add', '-A')
        run(self.repo, 'commit', '-q', '-m', 'base')
        self.base = run(self.repo, 'rev-parse', 'HEAD')
        (self.meta / 'out.txt').write_text('ok\n')

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def contract(self, **over):
        data = {'schema': vs.CONTRACT_SCHEMA, 'task_id': 'T-1', 'baseline_sha': self.base,
                'baseline_dirty_paths': [], 'allowed_paths': ['src/**'], 'protected_paths': ['secrets/**'],
                'modified_paths': ['src/app.py'], 'claimed_status': 'PASS',
                'verification': [{'command': 'python -m unittest', 'exit_code': 0, 'evidence': 'out.txt'}]}
        data.update(over)
        return data

    def verify(self, data):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        return vs.verify(self.repo, path)

    def codes(self, report):
        return {r['code'] for r in report['failure_reasons']}


class VerifyScopeTests(Fixture):
    def test_valid_in_scope_change_passes_with_evidence_hash(self):
        self.write('src/app.py', 'x = 2\n')
        report = self.verify(self.contract())
        self.assertEqual((report['status'], report['failure_reasons']), ('PASS', []))
        self.assertEqual(len(report['evidence'][0]['sha256']), 64)
        self.assertTrue(any('does not prevent' in x for x in report['limitations']))

    def test_untracked_and_deleted_files_are_seen(self):
        self.write('src/new.py', 'n\n')
        (self.repo / 'docs/a.md').unlink()
        report = self.verify(self.contract(modified_paths=['src/new.py', 'docs/a.md']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual([r['detail'] for r in report['failure_reasons'] if r['code'] == 'out_of_scope_modification'],
                         ['docs/a.md'])

    def test_unauthorized_modification_blocked(self):
        self.write('src/app.py', 'x = 2\n')
        self.write('docs/a.md', 'changed\n')
        report = self.verify(self.contract(modified_paths=['src/app.py', 'docs/a.md']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('out_of_scope_modification', self.codes(report))

    def test_protected_file_blocked_even_if_allowed(self):
        self.write('secrets/k.txt', 'leak\n')
        report = self.verify(self.contract(allowed_paths=['**'], modified_paths=['secrets/k.txt']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('protected_path_modified', self.codes(report))

    def test_tests_need_explicit_sensitive_approval(self):
        self.write('tests/test_app.py', 'assert True\n')
        data = self.contract(allowed_paths=['**'], modified_paths=['tests/test_app.py'])
        self.assertIn('test_path_modified_unapproved', self.codes(self.verify(data)))
        data['allowed_sensitive_paths'] = ['tests/test_app.py']
        self.assertEqual(self.verify(data)['status'], 'PASS')

    def test_governance_files_need_explicit_sensitive_approval(self):
        self.write('AGENTS.md', 'weakened\n')
        self.write('.gitattributes', '* text\n')
        report = self.verify(self.contract(allowed_paths=['**'], modified_paths=['AGENTS.md', '.gitattributes']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual([r['detail'] for r in report['failure_reasons']
                          if r['code'] == 'governance_path_modified_unapproved'], ['.gitattributes', 'AGENTS.md'])

    def test_dirty_baseline_is_partial_never_pass(self):
        self.write('src/app.py', 'x = 2\n')
        report = self.verify(self.contract(baseline_dirty_paths=['src/app.py']))
        self.assertEqual(report['status'], 'PARTIAL')
        self.assertIn('dirty_baseline', self.codes(report))
        self.assertEqual(report['claimed_status'], 'PASS')
        self.assertIn('false_pass', self.codes(report))

    def test_baseline_subcommand_reports_current_dirty_paths(self):
        self.write('src/app.py', 'x = 3\n')
        self.write('scratch.txt', 's\n')
        self.assertEqual(vs.current_dirty(self.repo), ['scratch.txt', 'src/app.py'])

    def test_baseline_mismatch_and_ambiguity_block(self):
        self.write('src/app.py', 'x = 2\n')
        other = Path(self._tmp.name) / 'other'
        other.mkdir()
        run(other, 'init', '-q')
        (other / 'f').write_text('f')
        run(other, 'add', '-A')
        run(other, 'commit', '-q', '-m', 'unrelated')
        unrelated = run(other, 'rev-parse', 'HEAD')
        with self.assertRaises(vs.Blocked):
            self.verify(self.contract(baseline_sha=unrelated))          # not in this repo
        with self.assertRaises(vs.Blocked):
            self.verify(self.contract(baseline_sha=self.base[:10]))     # abbreviated = ambiguous
        run(self.repo, 'checkout', '-q', '--orphan', 'rewritten')
        run(self.repo, 'commit', '-q', '-m', 'rewritten', '--allow-empty')
        report = self.verify(self.contract())
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('baseline_mismatch', self.codes(report))

    def test_missing_evidence_blocks(self):
        self.write('src/app.py', 'x = 2\n')
        cases = [{'verification': []},
                 {'verification': [{'command': 'c', 'exit_code': 0, 'evidence': 'nope.txt'}]},
                 {'verification': [{'command': 'c', 'exit_code': 0}]},
                 {'verification': [{'command': 'c', 'evidence': 'out.txt'}]},
                 {'verification': [{'command': 'c', 'exit_code': True, 'evidence': 'out.txt'}]},
                 {'verification': [{'command': 'c', 'exit_code': 0, 'evidence': '../../../etc/hostname'}]}]
        for over in cases:
            with self.subTest(over=over):
                report = self.verify(self.contract(**over))
                self.assertEqual(report['status'], 'BLOCKED')
                self.assertIn('missing_evidence', self.codes(report))

    def test_evidence_symlink_is_refused(self):
        self.write('src/app.py', 'x = 2\n')
        (self.meta / 'link.txt').symlink_to(self.meta / 'out.txt')
        report = self.verify(self.contract(verification=[{'command': 'c', 'exit_code': 0, 'evidence': 'link.txt'}]))
        self.assertEqual(report['status'], 'BLOCKED')

    def test_false_pass_claims_are_downgraded(self):
        self.write('src/app.py', 'x = 2\n')
        failing = self.contract(verification=[{'command': 'pytest', 'exit_code': 1, 'evidence': 'out.txt'}])
        report = self.verify(failing)
        self.assertEqual((report['status'], report['claimed_status']), ('PARTIAL', 'PASS'))
        self.assertIn('check_failed', self.codes(report))
        self.assertIn('false_pass', self.codes(report))
        self.write('docs/a.md', 'x\n')                       # undeclared change hidden by the claim
        report = self.verify(self.contract())
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('declared_mismatch', self.codes(report))

    def test_claim_is_never_upgraded(self):
        self.write('src/app.py', 'x = 2\n')
        self.assertEqual(self.verify(self.contract(claimed_status='PARTIAL'))['status'], 'PARTIAL')
        self.assertEqual(self.verify(self.contract(claimed_status='BLOCKED'))['status'], 'BLOCKED')

    def test_malformed_contract_fails_closed_through_cli(self):
        path = self.meta / 'bad.json'
        for text in ('not json', '[]', json.dumps({'schema': 'x'})):
            path.write_text(text)
            self.assertEqual(cli('verify', '--repo', str(self.repo), '--result', str(path)), 2)
        self.assertEqual(cli('verify', '--repo', str(self.meta), '--result', str(path)), 2)

    def test_pattern_validation_rejects_escapes(self):
        for bad in ('/etc/passwd', '../x', 'a/../b', 'a\\b', ''):
            with self.assertRaises(vs.Blocked):
                vs.compile_glob(bad)
        self.assertTrue(vs.compile_glob('src/**').match('src/a/b.py'))
        self.assertFalse(vs.compile_glob('src/*').match('src/a/b.py'))

    def test_result_file_inside_repo_is_not_a_change_and_cli_exit_codes(self):
        self.write('src/app.py', 'x = 2\n')
        (self.repo / 'out.txt').write_text('ok\n')
        path = self.repo / 'result.json'
        path.write_text(json.dumps(self.contract(
            allowed_paths=['src/**', 'out.txt'], modified_paths=['src/app.py', 'out.txt'],
            verification=[{'command': 'c', 'exit_code': 0, 'evidence': 'out.txt'}])))
        self.assertEqual(cli('verify', '--repo', str(self.repo), '--result', str(path)), 0)


class EvidenceAndRecoveryTests(Fixture):
    """N03: ignored files, independent baseline, evidence trust, incomplete runs, special files, no-write recovery."""

    def commit_ignore(self, *patterns):
        self.write('.gitignore', ''.join(p + '\n' for p in patterns))
        run(self.repo, 'add', '.gitignore')
        run(self.repo, 'commit', '-q', '-m', 'ignore')
        self.base = run(self.repo, 'rev-parse', 'HEAD')

    def edit(self, **over):
        self.write('src/app.py', 'x = 2\n')
        return self.verify(self.contract(baseline_sha=self.base, **over))

    # --- ignored files
    def test_ignored_file_without_recorded_baseline_is_partial_not_pass(self):
        self.commit_ignore('hidden.txt')
        self.write('hidden.txt', 'unseen\n')
        report = self.verify(self.contract(baseline_sha=self.base, modified_paths=[]))
        self.assertEqual(report['status'], 'PARTIAL')
        self.assertIn('ignored_baseline_unknown', self.codes(report))
        self.assertEqual(report['ignored_paths_count'], 1)

    def test_new_ignored_files_need_approval_when_baseline_is_recorded(self):
        self.commit_ignore('hidden.txt', 'cache/')
        self.write('hidden.txt', 'unseen\n')
        self.write('cache/x.bin', 'c\n')
        base = dict(baseline_sha=self.base, modified_paths=[], baseline_ignored_paths=[])
        report = self.verify(self.contract(**base))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual({r['detail'] for r in report['failure_reasons'] if r['code'] == 'ignored_path_unapproved'},
                         {'hidden.txt', 'cache/x.bin'})
        approved = self.verify(self.contract(**base, ignorable_paths=['cache/**'], allowed_paths=['hidden.txt']))
        self.assertEqual(approved['status'], 'PASS')
        known = self.verify(self.contract(baseline_sha=self.base, modified_paths=[],
                                          baseline_ignored_paths=['hidden.txt', 'cache/x.bin']))
        self.assertEqual(known['status'], 'PASS')

    def test_ignored_protected_file_is_blocked_even_if_ignorable(self):
        self.commit_ignore('secrets/')
        self.write('secrets/new.txt', 'x\n')
        report = self.verify(self.contract(baseline_sha=self.base, modified_paths=[], baseline_ignored_paths=[],
                                           ignorable_paths=['**'], protected_paths=['secrets/**']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('protected_path_modified', self.codes(report))

    # --- independent baseline record
    def record(self, name='baseline.json'):
        path = self.meta / name
        self.assertEqual(cli('baseline', '--repo', str(self.repo), '--out', str(path)), 0)
        return path

    def run_with(self, data, **kwargs):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        return vs.verify(self.repo, path, **kwargs)

    def test_independent_record_matches_honest_contract(self):
        record = self.record()
        self.write('src/app.py', 'x = 2\n')
        report = self.run_with(self.contract(baseline_ignored_paths=[]), baseline_record=record)
        self.assertEqual(report['status'], 'PASS')
        self.assertIn('operator-supplied record', report['trust']['baseline'])
        self.assertIn('not verifiable', report['trust']['baseline'])

    def test_contract_cannot_claim_a_clean_baseline_the_record_contradicts(self):
        self.write('src/pre.py', 'pre-existing\n')               # dirty before the task
        record = self.record()
        self.write('src/app.py', 'x = 2\n')
        data = self.contract(allowed_paths=['src/**'], modified_paths=['src/app.py', 'src/pre.py'],
                             baseline_dirty_paths=[])             # the agent says "clean"
        report = self.run_with(data, baseline_record=record)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('baseline_record_mismatch', self.codes(report))
        honest = self.run_with(dict(data, baseline_dirty_paths=['src/pre.py']), baseline_record=record)
        self.assertEqual(honest['status'], 'PARTIAL')             # dirty baseline stays PARTIAL
        self.assertIn('dirty_baseline', self.codes(honest))

    def test_record_hides_nothing_and_reports_dirty_files_changed_since(self):
        self.write('src/pre.py', 'v1\n')
        record = self.record()
        self.write('src/pre.py', 'v2\n')
        data = self.contract(modified_paths=['src/pre.py'], baseline_dirty_paths=['src/pre.py'])
        report = self.run_with(data, baseline_record=record)
        self.assertEqual(report['dirty_baseline_changed_since_record'], ['src/pre.py'])

    def test_tampered_or_foreign_record_is_refused(self):
        record = self.record()
        data = json.loads(record.read_text())
        data['baseline_dirty_paths'] = ['x']                      # edit without recomputing the digest
        record.write_text(json.dumps(data))
        with self.assertRaises(vs.Blocked) as caught:
            self.run_with(self.contract(), baseline_record=record)
        self.assertIn('record_tampered', str(caught.exception))
        wrong = self.meta / 'wrong.json'
        wrong.write_text(json.dumps({'schema': 'other/1'}))
        with self.assertRaises(vs.Blocked):
            self.run_with(self.contract(), baseline_record=wrong)

    def test_baseline_record_is_never_written_inside_the_repo_or_over_a_file(self):
        self.assertEqual(cli('baseline', '--repo', str(self.repo), '--out', str(self.repo / 'rec.json')), 2)
        self.assertFalse((self.repo / 'rec.json').exists())
        existing = self.meta / 'keep.json'
        existing.write_text('keep')
        self.assertEqual(cli('baseline', '--repo', str(self.repo), '--out', str(existing)), 2)
        self.assertEqual(existing.read_text(), 'keep')

    # --- evidence trust
    def seal(self, *refs):
        out = self.meta / 'manifest.json'
        cwd = os.getcwd()
        os.chdir(self.meta)
        try:
            self.assertEqual(cli('seal', '--out', str(out), *refs), 0)
        finally:
            os.chdir(cwd)
        return out

    def test_pinned_hash_mismatch_blocks(self):
        self.write('src/app.py', 'x = 2\n')
        check = [{'command': 'c', 'exit_code': 0, 'evidence': 'out.txt', 'sha256': '0' * 64}]
        report = self.verify(self.contract(verification=check))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('evidence_hash_mismatch', self.codes(report))
        bad = [{'command': 'c', 'exit_code': 0, 'evidence': 'out.txt', 'sha256': 'zz'}]
        self.assertEqual(self.verify(self.contract(verification=bad))['status'], 'BLOCKED')

    def test_sealed_manifest_gives_hash_integrity_only(self):
        self.write('src/app.py', 'x = 2\n')
        plain = self.verify(self.contract())
        self.assertEqual((plain['status'], plain['evidence'][0]['integrity']), ('PASS', 'unchecked'))
        self.assertEqual(plain['trust']['hash_integrity'], 'none')
        manifest = self.seal('out.txt')
        sealed = self.run_with(self.contract(), evidence_manifest=manifest, require_sealed=True)
        entry = sealed['evidence'][0]
        self.assertEqual((sealed['status'], entry['integrity']), ('PASS', 'sealed'))
        # a sealed hash never upgrades origin, custody or execution
        self.assertEqual((entry['origin'], entry['execution']), ('agent-reported', 'not-verified'))
        self.assertEqual(sealed['trust']['hash_integrity'], 'all')
        self.assertTrue(sealed['trust']['custody'].startswith('unauthenticated'))
        self.assertTrue(sealed['trust']['independent_execution'].startswith('not verified'))
        unsealed = self.run_with(self.contract(), require_sealed=True)
        self.assertEqual(unsealed['status'], 'PARTIAL')
        self.assertIn('evidence_not_sealed', self.codes(unsealed))

    def test_a_pin_proves_only_agreement_with_the_agents_own_hash(self):
        self.write('src/app.py', 'x = 2\n')
        digest = vs.hashlib.sha256((self.meta / 'out.txt').read_bytes()).hexdigest()
        check = [{'command': 'c', 'exit_code': 0, 'evidence': 'out.txt', 'sha256': digest}]
        report = self.verify(self.contract(verification=check))
        self.assertEqual(report['evidence'][0]['integrity'], 'pinned')
        self.assertEqual(report['trust']['hash_integrity'], 'all')
        strict = self.run_with(self.contract(verification=check), require_sealed=True)   # pin alone is not sealing
        self.assertEqual(strict['status'], 'PARTIAL')

    def test_evidence_changed_after_sealing_is_tampered(self):
        self.write('src/app.py', 'x = 2\n')
        manifest = self.seal('out.txt')
        (self.meta / 'out.txt').write_text('edited after the fact\n')
        report = self.run_with(self.contract(), evidence_manifest=manifest)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('evidence_tampered', self.codes(report))

    def test_sealed_evidence_cannot_launder_a_scope_violation(self):
        self.write('src/app.py', 'x = 2\n')
        self.write('docs/a.md', 'sneaky\n')
        manifest = self.seal('out.txt')
        report = self.run_with(self.contract(modified_paths=['src/app.py', 'docs/a.md']),
                               evidence_manifest=manifest, require_sealed=True)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('out_of_scope_modification', self.codes(report))

    def test_seal_refuses_overwrite_symlink_and_missing_files(self):
        manifest = self.seal('out.txt')
        before = manifest.read_text()
        self.assertEqual(cli('seal', '--out', str(manifest), str(self.meta / 'out.txt')), 2)
        self.assertEqual(manifest.read_text(), before)
        (self.meta / 'link.txt').symlink_to(self.meta / 'out.txt')
        self.assertEqual(cli('seal', '--out', str(self.meta / 'm2.json'), str(self.meta / 'link.txt')), 2)
        self.assertEqual(cli('seal', '--out', str(self.meta / 'm3.json'), str(self.meta / 'nope.txt')), 2)

    # --- interrupted or incomplete runs
    def test_required_checks_and_execution_state(self):
        self.write('src/app.py', 'x = 2\n')
        report = self.verify(self.contract(required_verification=['python -m unittest', 'ruff check .']))
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual([r['detail'] for r in report['failure_reasons'] if r['code'] == 'required_check_missing'],
                         ['required verification not recorded: `ruff check .`'])
        self.assertEqual(self.verify(self.contract(required_verification=['python -m unittest']))['status'], 'PASS')
        for state in ('in_progress', 'interrupted'):
            report = self.verify(self.contract(execution_state=state))
            self.assertEqual(report['status'], 'BLOCKED')
            self.assertIn('incomplete_execution', self.codes(report))
        self.assertEqual(self.verify(self.contract(execution_state='complete'))['status'], 'PASS')
        with self.assertRaises(vs.Blocked):
            self.verify(self.contract(execution_state='done'))

    # --- symlinks, submodules and mode changes
    def test_symlink_and_mode_changes_need_explicit_approval(self):
        (self.repo / 'src/link.py').symlink_to('app.py')
        os.chmod(self.repo / 'src/app.py', 0o755)
        data = self.contract(allowed_paths=['src/**'], modified_paths=['src/link.py', 'src/app.py'])
        report = self.verify(data)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual({r['detail'].split(':')[0] for r in report['failure_reasons'] if r['code'] == 'special_file_change'},
                         {'src/link.py', 'src/app.py'})
        data['allowed_sensitive_paths'] = ['src/link.py', 'src/app.py']
        self.assertEqual(self.verify(data)['status'], 'PASS')

    # --- recovery contract: detection only, never a write
    def test_verifier_never_modifies_the_repository_and_never_overwrites_outputs(self):
        self.write('src/app.py', 'x = 2\n')
        self.write('docs/a.md', 'out of scope\n')
        (self.repo / 'tests/test_app.py').unlink()
        def snapshot():
            return (run(self.repo, 'rev-parse', 'HEAD'), run(self.repo, 'status', '--porcelain=v1', '--ignored'),
                    (self.repo / 'docs/a.md').read_text(), (self.repo / '.git' / 'index').read_bytes())
        before = snapshot()
        result = self.meta / 'result.json'
        result.write_text(json.dumps(self.contract(modified_paths=['src/app.py', 'docs/a.md', 'tests/test_app.py'])))
        out = self.meta / 'report.json'
        out.write_text('previous')
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = vs.main(['verify', '--repo', str(self.repo), '--result', str(result), '--out', str(out)])
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(), before)                         # nothing reset, cleaned, deleted or rewritten
        self.assertEqual(out.read_text(), 'previous')                # existing output is never overwritten
        report = json.loads(buffer.getvalue())
        self.assertEqual(report['recovery']['automatic_recovery'], 'none')
        self.assertTrue(any('never resets' in g for g in report['recovery']['guidance']))

    def test_pass_has_no_recovery_actions_and_blocked_errors_carry_guidance(self):
        self.write('src/app.py', 'x = 2\n')
        self.assertEqual(self.verify(self.contract())['recovery']['guidance'], [])
        self.assertIn('never resets', vs.blocked_report('x')['recovery']['guidance'][0])

    def test_git_execution_mitigations_still_hold_for_the_new_git_calls(self):
        marker = Path(self._tmp.name) / 'EXECUTED'
        payload = Path(self._tmp.name) / 'p.sh'
        payload.write_text(f'#!/bin/sh\ntouch "{marker}"\nprintf ""\n')
        payload.chmod(0o755)
        run(self.repo, 'config', 'core.fsmonitor', str(payload))
        (self.repo / 'src/link.py').symlink_to('app.py')
        record = self.record()
        self.write('src/app.py', 'x = 2\n')
        self.run_with(self.contract(), baseline_record=record)
        self.assertFalse(marker.exists())


class GitExecutionSurfaceTests(Fixture):
    """Adversarial fixtures: no repository- or environment-provided program may run.

    Every payload creates a marker file when executed; each test fails if it exists.
    Only throw-away repositories are used. This shows the listed vectors are
    neutralised, not that Git's whole execution surface is safe (see SECURITY.md).
    """

    def setUp(self):
        super().setUp()
        self.marker = Path(self._tmp.name) / 'EXECUTED'
        self.payload = Path(self._tmp.name) / 'payload.sh'
        self.payload.write_text(f'#!/bin/sh\ntouch "{self.marker}"\nprintf ""\n')
        self.payload.chmod(0o755)

    def cfg(self, key, value):
        run(self.repo, 'config', key, value)

    def assertNotExecuted(self):
        self.assertFalse(self.marker.exists(), 'a repository- or environment-provided program ran')

    def baseline_verify(self, **over):
        self.write('src/app.py', 'x = 2\n')
        return self.verify(self.contract(**over))

    def test_fsmonitor_hook_is_not_executed(self):
        self.cfg('core.fsmonitor', str(self.payload))
        report = self.baseline_verify()
        self.assertNotExecuted()
        self.assertEqual(report['status'], 'PASS')

    def test_repository_hooks_and_hooks_path_are_not_executed(self):
        hooks = self.repo / '.git' / 'hooks'
        evil = Path(self._tmp.name) / 'evilhooks'
        evil.mkdir()
        for directory in (hooks, evil):
            for name in ('pre-commit', 'post-checkout', 'post-index-change', 'reference-transaction', 'post-merge'):
                (directory / name).write_text(self.payload.read_text())
                (directory / name).chmod(0o755)
        self.cfg('core.hooksPath', str(evil))
        (self.repo / 'src/app.py').touch()          # stat-dirty without a content change
        self.baseline_verify()
        self.assertNotExecuted()

    def test_environment_injected_git_configuration_is_ignored(self):
        env = {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.fsmonitor',
               'GIT_CONFIG_VALUE_0': str(self.payload),
               'GIT_CONFIG_PARAMETERS': f"'core.fsmonitor={self.payload}'",
               'GIT_EXTERNAL_DIFF': str(self.payload), 'GIT_PAGER': str(self.payload),
               'GIT_CONFIG_GLOBAL': str(self.payload), 'GIT_DIR': str(Path(self._tmp.name) / 'nowhere')}
        with mock.patch.dict(os.environ, env):
            report = self.baseline_verify()
        self.assertNotExecuted()
        self.assertEqual(report['status'], 'PASS')

    def test_global_configuration_fsmonitor_is_overridden(self):
        home = Path(self._tmp.name) / 'home'
        home.mkdir()
        (home / '.gitconfig').write_text(f'[core]\n\tfsmonitor = {self.payload}\n')
        with mock.patch.dict(os.environ, {'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'xdg')}):
            report = self.baseline_verify()
        self.assertNotExecuted()
        self.assertEqual(report['status'], 'PASS')

    def test_repository_filter_and_diff_drivers_are_refused_not_run(self):
        cases = (('filter.evil.clean', 'clean'), ('filter.evil.smudge', 'smudge'), ('filter.evil.process', 'process'),
                 ('diff.evil.textconv', 'textconv'), ('diff.evil.command', 'command'), ('diff.external', 'external'))
        (self.repo / '.gitattributes').write_text('* filter=evil diff=evil\n')
        for key, label in cases:
            with self.subTest(key=key):
                self.cfg(key, str(self.payload))
                self.write('src/app.py', f'x = "{label}"\n')
                with self.assertRaises(vs.Blocked) as caught:
                    self.verify(self.contract())
                self.assertNotExecuted()
                self.assertIn('executable_git_config', str(caught.exception))
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):                      # CLI reports BLOCKED, exit 2
                    code = vs.main(['verify', '--repo', str(self.repo), '--result', str(self.meta / 'result.json')])
                report = json.loads(buffer.getvalue())
                self.assertEqual((code, report['status']), (2, 'BLOCKED'))
                self.assertEqual(report['failure_reasons'][0]['code'], 'executable_git_config')
                self.assertNotExecuted()
                run(self.repo, 'config', '--unset-all', key)

    def test_included_configuration_file_is_treated_as_untrusted(self):
        included = Path(self._tmp.name) / 'extra.cfg'
        included.write_text(f'[filter "evil"]\n\tclean = {self.payload}\n')
        (self.repo / '.gitattributes').write_text('* filter=evil\n')
        self.cfg('include.path', str(included))
        self.write('src/app.py', 'x = 2\n')
        with self.assertRaises(vs.Blocked):
            self.verify(self.contract())
        self.assertNotExecuted()

    def test_benign_configuration_does_not_change_results_and_git_still_works(self):
        self.cfg('core.autocrlf', 'false')
        self.cfg('user.name', 'someone')
        before = run(self.repo, 'rev-parse', 'HEAD')
        index = (self.repo / '.git' / 'index').read_bytes()
        report = self.baseline_verify()
        self.assertEqual((report['status'], report['modified_paths']), ('PASS', ['src/app.py']))
        self.assertEqual(run(self.repo, 'rev-parse', 'HEAD'), before)
        self.assertEqual((self.repo / '.git' / 'index').read_bytes(), index)   # no optional index write
        self.assertEqual(cli('verify', '--repo', str(self.repo), '--result', str(self.meta / 'result.json')), 0)

    def test_baseline_subcommand_uses_the_same_protection(self):
        self.cfg('core.fsmonitor', str(self.payload))
        self.cfg('filter.evil.clean', str(self.payload))
        self.assertEqual(cli('baseline', '--repo', str(self.repo)), 2)
        self.assertNotExecuted()


if __name__ == '__main__':
    unittest.main()
