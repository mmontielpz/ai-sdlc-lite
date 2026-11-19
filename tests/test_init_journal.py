"""EXP-01B: `init --apply|--check --journal` (J-11..J-16, CP-04, CP-05) with unchanged primary behavior (B-1)."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experience_support as sup
from ai_sdlc import experience
from ai_sdlc import experience_events as ev
from ai_sdlc import experience_journal as jr
from ai_sdlc import initializer as init

ROOT = sup.ROOT
EXPECTED_REASONS = set(ev.INIT_REASONS)


class InitJournalCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-ij-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'project with spaces'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'AGENTS.md').write_text('Preserve project rules.\n')
        self.journal = self.base / 'journal' / 'j.jsonl'
        self.journal.parent.mkdir()
        self.installer = init._installer()
        self.content, _hashes = self.installer.bundle_content()
        self.destination = self.repo / self.installer.SKILL

    def invoke(self, *args, repo=None, journal=(), patches=()):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), mock.patch.object(ev, 'default_clock', sup.clock), \
                mock.patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')), \
                mock.patch('subprocess.Popen', side_effect=AssertionError('subprocess forbidden')), \
                mock.patch('os.system', side_effect=AssertionError('subprocess forbidden')), \
                mock.patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
            with contextlib_exit_stack(patches):
                code = init.main(['--repo', str(repo or self.repo), *args, *journal])
        return code, out.getvalue(), err.getvalue()

    def with_journal(self, path=None, classification='synthetic', extra=()):
        return ['--journal', str(path or self.journal), '--repo-classification', classification, *extra]

    def events(self):
        return jr.parse_journal(self.journal.read_bytes())[0]

    def reset_install(self):
        shutil.rmtree(self.repo / '.agents', ignore_errors=True)
        shutil.rmtree(self.repo / '.claude', ignore_errors=True)

    def manifest_digest(self, target='agents'):
        skill = self.installer.SKILL_TARGETS[target]
        return hashlib.sha256((self.repo / skill / self.installer.MANIFEST).read_bytes()).hexdigest()


class contextlib_exit_stack:
    """Enter a list of patchers together (kept local so the module needs no extra imports)."""

    def __init__(self, patchers):
        self.patchers, self.entered = list(patchers), []

    def __enter__(self):
        for patcher in self.patchers:
            patcher.start()
            self.entered.append(patcher)

    def __exit__(self, *exc):
        for patcher in reversed(self.entered):
            patcher.stop()
        return False


class SuccessEvents(InitJournalCase):
    def test_output_is_byte_identical_with_and_without_a_working_journal(self):  # J-11
        plain = self.invoke('--apply')
        before = sup.snapshot(self.repo)
        self.reset_install()
        journaled = self.invoke('--apply', journal=self.with_journal())
        self.assertEqual(plain, journaled)  # stdout, stderr and exit code
        self.assertEqual(plain[0], 0)
        self.assertEqual({k: v[:2] for k, v in before.items()}, {k: v[:2] for k, v in sup.snapshot(self.repo).items()})
        events = self.events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual((event['type'], event['method'], event['trust_level'], event['independence']),
                         ('install.completed', 'tool-checked-hash', 'T1', 'none'))
        self.assertEqual(event['subject'], {'kind': 'installation', 'repo_classification': 'synthetic'})
        self.assertEqual((event['actor'], event['observer']), ({'role': 'tool', 'name': 'ai-sdlc-lite'},) * 2)
        self.assertEqual(event['data'], {'target': 'agents', 'result': 'INITIALIZED',
                                         'file_count': len(self.content),
                                         'manifest_sha256': self.manifest_digest()})
        self.assertEqual(event['evidence'], [])
        self.assertEqual(event['environment'], ev.default_environment())

    def test_unchanged_and_check_results_chain_in_one_run(self):  # J-12
        self.assertEqual(self.invoke('--apply', journal=self.with_journal())[0], 0)
        self.assertEqual(self.invoke('--apply', journal=self.with_journal())[0], 0)
        self.assertEqual(self.invoke('--check', journal=self.with_journal())[0], 0)
        results = [(e['data']['result'], e['seq']) for e in self.events()]
        self.assertEqual(results, [('INITIALIZED', 1), ('UNCHANGED', 2), ('CHECK_OK', 3)])
        for event in self.events():
            self.assertEqual(event['data']['manifest_sha256'], self.manifest_digest())
            self.assertEqual(event['data']['file_count'], len(self.content))
        self.assertEqual(len({e['run_id'] for e in self.events()}), 1)
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 3)

    def test_claude_target_and_options(self):  # J-11 (target, run id, classification)
        code, out, err = self.invoke('--apply', '--target', 'claude-code',
                                     journal=self.with_journal(classification='private', extra=['--run-id', 'run-x']))
        self.assertEqual((code, err), (0, ''))
        event = self.events()[0]
        self.assertEqual((event['run_id'], event['data']['target'], event['subject']['repo_classification']),
                         ('run-x', 'claude-code', 'private'))
        self.assertEqual(event['data']['manifest_sha256'], self.manifest_digest('claude-code'))


class FailureEvents(InitJournalCase):
    def failed(self, *args, patches=(), repo=None):
        """Run init with --journal expecting a refusal; return (stderr reason, recorded data, exit code)."""
        code, out, err = self.invoke(*args, repo=repo, journal=self.with_journal(), patches=patches)
        self.assertEqual(err.count('JOURNAL:'), 0, err)
        reason = err.split('reason=')[1].strip()
        events = self.events()
        self.assertEqual(events[-1]['type'], 'install.failed')
        self.assertEqual(events[-1]['method'], 'tool-reported')
        self.assertEqual(events[-1]['trust_level'], 'T0')
        self.assertEqual(events[-1]['data']['reason_code'], reason)
        self.assertIn(reason, EXPECTED_REASONS)
        return reason, events[-1]['data'], code

    def installed(self):
        self.assertEqual(self.invoke('--apply')[0], 0)
        return self.destination

    def test_every_reachable_refusal_reason_is_recorded(self):  # J-13
        seen = {}

        def case(name, expected, *args, **kwargs):
            if self.journal.exists():
                self.journal.unlink()
            reason, data, code = self.failed(*args, **kwargs)
            self.assertEqual(reason, expected, name)
            self.assertEqual(data, {'target': 'agents', 'reason_code': expected, 'partial': False}, name)
            seen[expected] = code

        case('missing', 'installation_missing', '--check')
        case('unsafe path', 'unsafe_path', '--apply', repo='a/../b')
        case('framework overlap', 'framework_overlap', '--apply', repo=ROOT)
        case('framework unavailable', 'framework_unavailable', '--apply',
             patches=[mock.patch.object(init, '_installer', side_effect=init.Refused('framework_unavailable'))])
        case('primitives', 'unsupported_filesystem_primitives', '--apply',
             patches=[mock.patch.object(init, '_supported', return_value=False)])
        case('generic failure', 'validation_or_io_failure', '--apply',
             patches=[mock.patch.object(init, '_existing', side_effect=OSError(5, 'boom'))])
        git = self.repo / '.git'
        (git / 'commondir').write_text('../x\n')
        case('external git', 'external_git_metadata', '--apply')
        (git / 'commondir').unlink()
        head = (git / 'HEAD').read_text()
        (git / 'HEAD').write_text('garbage\n')
        case('git root', 'invalid_git_root', '--apply')
        (git / 'HEAD').write_text(head)
        skill = self.installed()
        case('inventory limit', 'inventory_limit', '--check', patches=[mock.patch.object(init, 'MAX_ENTRIES', 1)])
        manifest = skill / self.installer.MANIFEST
        original = manifest.read_bytes()
        (skill / 'extra.txt').write_text('x\n')
        case('inventory conflict', 'installation_inventory_conflict', '--check')
        (skill / 'extra.txt').unlink()
        record = json.loads(original)
        record['files'][sorted(record['files'])[0]] = 'f' * 64
        manifest.write_text(json.dumps(record))
        case('version conflict', 'installation_version_conflict', '--check')
        manifest.write_text('[]')
        case('invalid manifest', 'invalid_manifest', '--check')
        manifest.write_text('{"format": 1, "format": 1, "files": {}}')
        case('duplicate key', 'duplicate_manifest_key', '--check')
        manifest.write_bytes(b' ' * (init.MAX_MANIFEST + 1))
        case('oversized manifest', 'unsafe_file', '--check')
        manifest.write_bytes(original)
        case('oversized (growth race, injected)', 'oversized_file', '--check',
             patches=[mock.patch.object(init, '_existing', side_effect=init.Refused('oversized_file'))])
        victim = next(p for p in skill.rglob('*') if p.is_file() and p.name != self.installer.MANIFEST)
        saved = victim.read_bytes()
        victim.write_bytes(saved[:-1] + (b'X' if saved[-1:] != b'X' else b'Y'))  # same length, different bytes
        case('content conflict', 'installation_content_conflict', '--check')
        victim.write_bytes(saved)
        self.assertEqual(self.invoke('--check')[0], 0)  # the installation is intact again
        self.assertEqual(set(seen), EXPECTED_REASONS)  # all 16 shipped reasons were exercised
        self.assertTrue(all(code == 2 for code in seen.values()))

    def test_partial_failures_are_flagged(self):  # J-13 (partial)
        for name, patches, reason in (
                ('apply fails', [mock.patch.object(init, '_apply', side_effect=OSError(5, 'boom'))],
                 'validation_or_io_failure'),
                ('not installed afterwards', [mock.patch.object(init, '_existing', return_value=False)],
                 'installation_missing')):
            if self.journal.exists():
                self.journal.unlink()
            code, out, err = self.invoke('--apply', journal=self.with_journal(), patches=patches)
            self.assertEqual((code, err), (1, 'RESULT: PARTIAL reason=%s\n' % reason), name)
            self.assertEqual(self.events()[-1]['data'], {'target': 'agents', 'reason_code': reason, 'partial': True})
            self.reset_install()


class JournalFailuresDoNotChangeInit(InitJournalCase):
    def baseline(self, *args):
        return self.invoke(*args)

    def check_failure(self, journal_args, code, patches=(), args=('--check',)):
        plain = self.baseline(*args)
        failing = self.invoke(*args, journal=journal_args, patches=patches)
        self.assertEqual(failing[0], plain[0])  # exit code is the primary one (B-1)
        self.assertEqual(failing[1], plain[1])  # stdout
        self.assertEqual(failing[2], plain[2] + 'JOURNAL: %s\n' % code)  # exactly one added stderr line
        return failing

    def test_journal_failures_add_exactly_one_stderr_line(self):  # J-14, CP-04
        repo_journal = self.repo / 'j.jsonl'
        self.check_failure(self.with_journal(repo_journal), 'journal_in_repo')  # primary exit 2 (not installed)
        self.assertFalse(repo_journal.exists())
        self.assertEqual(self.invoke('--apply')[0], 0)
        self.check_failure(self.with_journal(repo_journal), 'journal_in_repo')  # primary exit 0 (UNCHANGED/CHECK_OK)
        self.assertFalse(repo_journal.exists())
        self.check_failure(self.with_journal(self.base / 'nodir' / 'j.jsonl'), 'journal_invalid_path')
        self.check_failure(self.with_journal(self.base / 'journal'), 'journal_invalid_path')
        self.check_failure(self.with_journal(self.journal), 'journal_io',
                           patches=[mock.patch.object(experience, 'record_install', side_effect=RuntimeError('x'))])
        self.check_failure(self.with_journal(self.journal), 'journal_io',
                           patches=[mock.patch.object(experience, 'record_install', side_effect=OSError(5, 'x'))])
        self.check_failure(self.with_journal(self.journal), 'chain_broken', patches=[mock.patch.object(
            experience, 'record_install', side_effect=ev.ExperienceError('chain_broken'))])
        odd = type('Odd', (Exception,), {'code': 'Not A Code!'})
        self.check_failure(self.with_journal(self.journal), 'journal_io',
                           patches=[mock.patch.object(experience, 'record_install', side_effect=odd())])
        self.assertFalse(self.journal.exists())

    def test_lock_timeout_full_and_corrupt_journals(self):  # J-14, SEC-03
        import fcntl
        self.assertEqual(self.invoke('--apply', journal=self.with_journal())[0], 0)
        handle = os.open(self.journal, os.O_RDWR)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
            with mock.patch.object(jr, 'LOCK_SECONDS', 0.05):
                self.check_failure(self.with_journal(), 'lock_failed')
        finally:
            os.close(handle)
        before = self.journal.read_bytes()
        with mock.patch.object(ev, 'MAX_JOURNAL_BYTES', len(before) + 10):
            self.check_failure(self.with_journal(), 'journal_full')
        self.assertEqual(before, self.journal.read_bytes())
        self.journal.write_bytes(b'not a journal\n')
        self.check_failure(self.with_journal(), 'malformed_json')  # a corrupt journal never affects init
        self.assertEqual(self.journal.read_bytes(), b'not a journal\n')

    def test_interrupts_are_not_swallowed_and_the_exit_code_is_kept(self):  # J-14
        with self.assertRaises(KeyboardInterrupt):
            self.invoke('--apply', journal=self.with_journal(),
                        patches=[mock.patch.object(experience, 'record_install', side_effect=KeyboardInterrupt())])
        self.assertTrue((self.destination / self.installer.MANIFEST).exists())  # the install had completed

    def test_primary_failures_keep_their_exit_codes(self):  # J-14
        patches = [mock.patch.object(init, '_apply', side_effect=OSError(5, 'boom'))]
        plain = self.invoke('--apply', patches=patches)
        self.assertEqual(plain[0], 1)
        self.reset_install()
        failing = self.invoke('--apply', journal=self.with_journal(self.repo / 'j.jsonl'), patches=patches)
        self.assertEqual(failing[0], 1)
        self.assertEqual(failing[2], plain[2] + 'JOURNAL: journal_in_repo\n')
        self.assertFalse((self.repo / 'j.jsonl').exists())

    def test_allow_in_repo_is_honored(self):  # J-14 (--allow-in-repo)
        path = self.repo / 'j.jsonl'
        code, out, err = self.invoke('--apply', journal=self.with_journal(path, extra=['--allow-in-repo']))
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(jr.validate_journal(str(path)).count, 1)


class UsageAndIsolation(InitJournalCase):
    def test_journal_option_usage_errors_do_nothing(self):  # J-15
        journal = ['--journal', str(self.journal)]
        classification = ['--repo-classification', 'synthetic']
        cases = [
            ['--dry-run'] + journal + classification, [] + journal + classification,
            ['--apply'] + journal, ['--apply'] + classification, ['--apply', '--run-id', 'run-a'],
            ['--apply', '--allow-in-repo'], ['--check'] + journal + ['--repo-classification', 'secret'],
            ['--apply'] + journal + ['--repo-classification', ''], ['--apply'] + journal + classification
            + ['--run-id', '-r'], ['--apply'] + journal + classification + ['--run-id', ''],
            ['--apply'] + journal + classification + journal, ['--apply'] + journal + classification
            + ['--allow-in-repo', '--allow-in-repo'], ['--apply', '--journal'],
            ['--apply'] + journal + ['--repo-classification'],
            ['--apply'] + journal + classification + ['--run-id', '--apply'],
        ]
        before = sup.snapshot(self.base)
        for args in cases:
            code, out, err = self.invoke(*args)
            self.assertEqual((code, out), (2, ''), args)
            self.assertTrue(err.startswith('BLOCKED: usage\n'), args)
        self.assertEqual(before, sup.snapshot(self.base))
        self.assertFalse((self.repo / '.agents').exists())
        self.assertFalse(self.journal.exists())

    def test_default_init_never_imports_the_experience_modules(self):  # J-16, CP-05
        script = ('import sys\nfrom ai_sdlc import cli\n'
                  'repo = sys.argv[1]\n'
                  'for argv in (["init", "--help"], ["init", "--repo", repo], ["init", "--repo", repo, "--check"],\n'
                  '             ["init", "--repo", repo, "--apply"], ["init", "--repo", repo, "--apply"]):\n'
                  '    cli.main(argv)\n'
                  'print(sorted(m for m in sys.modules if "experience" in m))\n')
        done = subprocess.run([sys.executable, '-B', '-c', script, str(self.repo)], capture_output=True, text=True,
                              cwd=str(ROOT), env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=60)
        self.assertEqual(done.stdout.strip().splitlines()[-1], '[]', done.stdout + done.stderr)
        self.assertTrue((self.destination / self.installer.MANIFEST).exists())
        used = subprocess.run([sys.executable, '-B', '-c',
                               'import sys\nfrom ai_sdlc import cli\n'
                               'cli.main(["init", "--repo", sys.argv[1], "--check", "--journal", sys.argv[2], '
                               '"--repo-classification", "synthetic"])\n'
                               'print(sorted(m for m in sys.modules if "experience" in m))\n',
                               str(self.repo), str(self.journal)],
                              capture_output=True, text=True, cwd=str(ROOT),
                              env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=60)
        self.assertIn('ai_sdlc.experience', used.stdout)
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 1)

    def test_bundle_is_unchanged_by_the_feature(self):  # J-16
        self.assertEqual(self.invoke('--apply')[0], 0)
        plain = {k: v for k, v in sup.snapshot(self.repo).items()}
        self.reset_install()
        self.assertEqual(self.invoke('--apply', journal=self.with_journal())[0], 0)
        journaled = {k: v for k, v in sup.snapshot(self.repo).items()}
        self.assertEqual({k: v[:2] for k, v in plain.items()}, {k: v[:2] for k, v in journaled.items()})

    def test_the_journal_is_never_read_by_init(self):  # SEC-03
        self.journal.write_bytes(b'\xff\xfe garbage')
        plain = self.invoke('--apply')
        self.reset_install()
        with_journal = self.invoke('--apply', journal=self.with_journal())
        self.assertEqual(plain[:2], with_journal[:2])
        self.assertEqual(with_journal[2], 'JOURNAL: truncated_journal\n')
        self.assertEqual(self.journal.read_bytes(), b'\xff\xfe garbage')

    def test_canaries_never_reach_the_journal(self):  # P-00, P-01
        canary = 'CANARY-SECRET-9f3a'
        os.environ['EXPERIENCE_CANARY'] = canary
        self.addCleanup(os.environ.pop, 'EXPERIENCE_CANARY', None)
        (self.repo / ('file-named-' + canary)).write_text(canary)
        (self.repo / 'TASK.md').write_text('secret task ' + canary + '\n')
        self.assertEqual(self.invoke('--apply', journal=self.with_journal())[0], 0)
        self.assertEqual(self.invoke('--check', journal=self.with_journal())[0], 0)
        self.reset_install()
        self.assertEqual(self.invoke('--check', journal=self.with_journal())[0], 2)
        data = self.journal.read_bytes()
        for forbidden in (canary.encode(), str(self.repo).encode(), str(self.base).encode(), str(ROOT).encode(),
                          b'/home', b'/tmp', b'AGENTS.md', os.environ.get('USER', 'nouser-x').encode(),
                          os.uname().nodename.encode()):
            self.assertNotIn(forbidden, data)
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 3)

    def test_determinism_three_runs(self):  # DT-05 (init)
        outputs = []
        for number in range(3):
            journal = self.base / 'journal' / ('d%d.jsonl' % number)
            self.reset_install()
            self.assertEqual(self.invoke('--apply', journal=self.with_journal(journal, extra=['--run-id', 'run-f']))[0], 0)
            self.assertEqual(self.invoke('--check', journal=self.with_journal(journal, extra=['--run-id', 'run-f']))[0], 0)
            outputs.append(journal.read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])
        for event in jr.parse_journal(outputs[0])[0]:
            self.assertEqual(event['event_id'], ev.compute_event_id(event))


if __name__ == '__main__':
    unittest.main()
