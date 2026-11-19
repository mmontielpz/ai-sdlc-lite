"""EXP-01B: `ai-sdlc experience record-verify` (R-01..R-14) against reports written by the real verifier."""

from contextlib import redirect_stderr, redirect_stdout
import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
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

ROOT = sup.ROOT
REFUSED = (2, '', 'RECORD-REFUSED: report_invalid\n')
spec = importlib.util.spec_from_file_location('verify_scope_for_experience_tests', ROOT / 'scripts/verify_scope.py')
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)
NOTICE = 'RECORD-NOTICE: recorded; success output could not be written\n'


class BrokenOut:
    def write(self, text):
        raise OSError(errno.EPIPE, 'Broken pipe')

    def flush(self):
        pass

    def fileno(self):
        raise OSError('no descriptor')


class FlushFailsOut:
    def write(self, text):
        return len(text)

    def flush(self):
        raise BrokenPipeError(errno.EPIPE, 'Broken pipe')

    def fileno(self):
        raise OSError('no descriptor')


def closed_stdout():
    stream = io.StringIO()
    stream.close()
    return stream


BROKEN_STDOUTS = {'none': lambda: None, 'write-fails': BrokenOut, 'flush-fails': FlushFailsOut,
                  'closed': closed_stdout}
ALL_PATHS = ['src/app.py', 'docs/a.md', 'docs/b.md', 'secrets/k.txt']


def _git(cwd, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


def _verifier(*args):
    with contextlib.redirect_stdout(io.StringIO()):
        return vs.main(list(args))


def build_reports(base):
    """Real verifier reports (written with `verify --out`) for a disposable synthetic repository."""
    repo, meta, out = base / 'repo', base / 'meta', base / 'reports'
    for directory in (repo, meta, out):
        directory.mkdir()
    _git(repo, 'init', '-q')
    for name in ALL_PATHS:
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text('1\n')
    _git(repo, 'add', '-A')
    _git(repo, 'commit', '-q', '-m', 'base')
    sha = _git(repo, 'rev-parse', 'HEAD')
    (meta / 'out.txt').write_text('ok\n')
    (meta / 'extra.txt').write_text('extra\n')
    _verifier('baseline', '--repo', str(repo), '--out', str(meta / 'baseline.json'))
    old = os.getcwd()
    os.chdir(meta)
    try:
        _verifier('seal', '--out', str(meta / 'manifest.json'), 'out.txt')
    finally:
        os.chdir(old)
    for name in ALL_PATHS:
        (repo / name).write_text('2\n')

    def contract(**over):
        data = {'schema': vs.CONTRACT_SCHEMA, 'task_id': 'T-1', 'baseline_sha': sha, 'baseline_dirty_paths': [],
                'allowed_paths': ['**'], 'protected_paths': [], 'modified_paths': ALL_PATHS,
                'claimed_status': 'PASS',
                'verification': [{'command': 'python -m unittest', 'exit_code': 0, 'evidence': 'out.txt'}]}
        data.update(over)
        return data

    def report(name, data, *extra):
        result = meta / (name + '.contract.json')
        result.write_text(json.dumps(data))
        _verifier('verify', '--repo', str(repo), '--result', str(result), '--out', str(out / (name + '.json')), *extra)

    report('pass', contract())
    report('partial', contract(baseline_dirty_paths=['src/app.py']))
    report('blocked_protected', contract(protected_paths=['secrets/**']))
    report('blocked_two', contract(allowed_paths=['src/**']))
    report('claimed_partial', contract(claimed_status='PARTIAL'))
    report('claimed_blocked', contract(claimed_status='BLOCKED'))
    report('dotted', contract(task_id='T.1_x'))
    report('sealed', contract(), '--evidence-manifest', str(meta / 'manifest.json'))
    report('partial_integrity', contract(verification=[
        {'command': 'a', 'exit_code': 0, 'evidence': 'out.txt'},
        {'command': 'b', 'exit_code': 0, 'evidence': 'extra.txt'}]), '--evidence-manifest', str(meta / 'manifest.json'))
    report('operator_baseline', contract(), '--baseline-record', str(meta / 'baseline.json'))
    _verifier('verify', '--repo', str(repo), '--result', str(meta / 'missing.json'), '--out',
              str(out / 'early_blocked.json'))
    (repo / 'src' / 'é.py').write_text('u\n')
    report('nonascii', contract(modified_paths=ALL_PATHS + ['src/é.py']))
    return out


class VerifyReportCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._shared = tempfile.TemporaryDirectory(prefix='ai-sdlc-rv-shared-')
        cls.addClassCleanup(cls._shared.cleanup)
        cls.reports = build_reports(Path(cls._shared.name))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-rv-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.journal = self.base / 'journal' / 'j.jsonl'
        self.journal.parent.mkdir()
        patches = [mock.patch.object(ev, 'default_clock', sup.clock)]
        for target, name in ((socket, 'socket'), (subprocess, 'run'), (subprocess, 'Popen'), (os, 'system')):
            patches.append(mock.patch.object(target, name, side_effect=AssertionError('forbidden: %s' % name)))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def report_path(self, name):
        return self.reports / (name + '.json')

    def data(self, name):
        return json.loads(self.report_path(name).read_text())

    def write(self, name, content):
        path = self.base / 'reports-in' / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else json.dumps(content).encode())
        return path

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = experience.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def verify(self, report, journal=None, classification='synthetic', extra=()):
        path = report if isinstance(report, Path) else self.report_path(report)
        return self.run_main('record-verify', '--journal', str(journal or self.journal), '--report', str(path),
                             '--repo-classification', classification, *extra)

    def events(self, journal=None):
        return jr.parse_journal(Path(journal or self.journal).read_bytes())[0]

    def refuse(self, report, **kwargs):
        before = sup.snapshot(self.base)
        result = self.verify(report, **kwargs)
        self.assertEqual(result, REFUSED, report)
        self.assertEqual(before, sup.snapshot(self.base))
        self.assertFalse(self.journal.exists())

    def mutated(self, name, change):
        data = self.data(name)
        change(data)
        return self.write('mutated.json', data)


class RecordVerifyAccepts(VerifyReportCase):
    def test_pass_report(self):  # R-01
        raw = self.report_path('pass').read_bytes()
        code, out, err = self.verify('pass')
        self.assertEqual((code, err), (0, ''))
        self.assertRegex(out, r'^experience recorded: seq=1 type=verify\.completed event_id=ev-[0-9a-f]{32}\n')
        event = self.events()[0]
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual((event['type'], event['method'], event['trust_level'], event['independence']),
                         ('verify.completed', 'tool-observed-git-state', 'T2', 'none'))
        self.assertEqual((event['actor'], event['observer']), ({'role': 'tool', 'name': 'ai-sdlc-lite'},) * 2)
        self.assertEqual(event['subject'], {'kind': 'task', 'task_id': 'T-1', 'repo_classification': 'synthetic'})
        self.assertEqual(event['evidence'], [{'kind': 'verification-report', 'ref': 'none', 'sha256': digest}])
        report = json.loads(raw)
        self.assertEqual(event['data'], {
            'status': 'PASS', 'exit_code': 0, 'failure_reason_codes': [], 'modified_path_count': len(ALL_PATHS),
            'report_sha256': digest, 'registry_version': 1, 'checks_origin': 'agent-reported',
            'facets': {'baseline': 'agent-reported', 'hash_integrity': 'none', 'custody': 'unauthenticated',
                       'independent_execution': 'not-verified', 'agent_assertions': 'unverified'}})
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 1)

    def test_partial_report(self):  # R-02
        report = self.data('partial')
        self.assertEqual(self.verify('partial')[0], 0)
        data = self.events()[0]['data']
        self.assertEqual((data['status'], data['exit_code']), ('PARTIAL', 1))
        self.assertEqual(data['failure_reason_codes'], sorted({r['code'] for r in report['failure_reasons']}))
        self.assertIn('dirty_baseline', data['failure_reason_codes'])

    def test_blocked_reports_and_duplicate_codes(self):  # R-03
        for number, name in enumerate(('blocked_protected', 'blocked_two'), 1):
            report = self.data(name)
            self.assertEqual(self.verify(name)[0], 0, name)
            data = self.events()[number - 1]['data']
            codes = [r['code'] for r in report['failure_reasons']]
            self.assertEqual((data['status'], data['exit_code']), ('BLOCKED', 2))
            self.assertEqual(data['failure_reason_codes'], sorted(set(codes)))
        duplicated = [r['code'] for r in self.data('blocked_two')['failure_reasons']]
        self.assertGreater(len(duplicated), len(set(duplicated)))  # the real verifier repeats a code per path
        self.assertIn('protected_path_modified', self.events()[0]['data']['failure_reason_codes'])

    def test_facets_are_mapped_to_enumerated_values_only(self):  # R-04
        expected = {'pass': ('agent-reported', 'none'), 'operator_baseline': ('operator-supplied-record', 'none'),
                    'sealed': ('agent-reported', 'all'), 'partial_integrity': ('agent-reported', 'partial')}
        for name, (baseline, integrity) in expected.items():
            report = self.data(name)
            self.assertEqual(report['trust']['hash_integrity'], integrity, name)
            self.assertEqual(self.verify(name)[0], 0, name)
        for event, (baseline, integrity) in zip(self.events(), expected.values()):
            self.assertEqual(event['data']['facets']['baseline'], baseline)
            self.assertEqual(event['data']['facets']['hash_integrity'], integrity)
        data = self.journal.read_bytes()
        for sentence in (self.data('pass')['trust']['custody'], self.data('operator_baseline')['trust']['baseline'],
                         self.data('pass')['trust']['independent_execution']):
            self.assertNotIn(sentence.encode(), data)  # the verifier's wording is never stored

    def test_run_id_agent_flags_and_chain(self):  # R-01 (chain)
        self.assertEqual(self.verify('pass', extra=['--run-id', 'run-a', '--agent', 'claude-code', '--mode',
                                                    'noninteractive'])[0], 0)
        self.assertEqual(self.verify('partial', extra=['--run-id', 'run-a'])[0], 0)
        self.assertEqual(self.events()[0]['environment']['agent_name'], 'claude-code')
        self.assertEqual([e['seq'] for e in self.events()], [1, 2])
        self.assertEqual(self.verify('pass', extra=['--run-id', 'other'])[2], 'RECORD-REFUSED: chain_broken\n')


class RecordVerifyRefuses(VerifyReportCase):
    def test_unrecognised_trust_wording(self):  # R-05
        for key, bad in (('baseline', 'bogus'), ('baseline', 'agent-reported x'), ('baseline', ''),
                         ('hash_integrity', 'some'), ('hash_integrity', 'ALL'), ('custody', 'authenticated'),
                         ('independent_execution', 'verified'), ('agent_assertions', 'asserted'),
                         ('custody', 7), ('custody', None)):
            self.refuse(self.mutated('pass', lambda d: d['trust'].__setitem__(key, bad)))
        for key in ('baseline', 'hash_integrity', 'custody', 'independent_execution', 'agent_assertions'):
            self.refuse(self.mutated('pass', lambda d: d['trust'].pop(key)))
        self.refuse(self.mutated('pass', lambda d: d.__setitem__('trust', 'agent-reported')))
        self.refuse(self.mutated('pass', lambda d: d.pop('trust')))

    def test_schema_and_registry_version(self):  # R-06
        for key, bad in (('schema', 'ai-sdlc-lite-verification/2'), ('schema', None), ('schema', ['x']),
                         ('registry_version', 0), ('registry_version', 2), ('registry_version', '1'),
                         ('registry_version', True), ('registry_version', None)):
            self.refuse(self.mutated('pass', lambda d: d.__setitem__(key, bad)))
        for key in ('schema', 'registry_version'):
            self.refuse(self.mutated('pass', lambda d: d.pop(key)))

    def test_status_and_code_consistency(self):  # R-07
        for bad in ('DONE', 'pass', 'PASS ', None, 0, ['PASS']):
            self.refuse(self.mutated('pass', lambda d: d.__setitem__('status', bad)))
        self.refuse('claimed_partial')  # status PARTIAL with no failure reasons (agent-claimed)
        self.refuse('claimed_blocked')  # status BLOCKED with no failure reasons (agent-claimed)
        reason = {'severity': 'BLOCKED', 'code': 'declared_mismatch', 'detail': 'x'}
        self.refuse(self.mutated('pass', lambda d: d.__setitem__('failure_reasons', [reason])))
        self.refuse(self.mutated('pass', lambda d: d.__setitem__('status', 'PARTIAL')))
        only_partial = {'severity': 'PARTIAL', 'code': 'dirty_baseline', 'detail': 'x'}
        self.refuse(self.mutated('partial', lambda d: (d.__setitem__('status', 'BLOCKED'),
                                                       d.__setitem__('failure_reasons', [only_partial]))))
        only_blocked = {'severity': 'BLOCKED', 'code': 'declared_mismatch', 'detail': 'x'}
        self.refuse(self.mutated('partial', lambda d: d.__setitem__('failure_reasons', [only_blocked])))
        self.refuse(self.mutated('pass', lambda d: d.pop('status')))

    def test_failure_code_registry(self):  # R-08
        good = {'severity': 'BLOCKED', 'code': 'declared_mismatch', 'detail': 'x'}
        for bad in ({'severity': 'BLOCKED', 'code': 'no_such_code', 'detail': 'x'},
                    {'severity': 'PARTIAL', 'code': 'declared_mismatch', 'detail': 'x'},  # severity not allowed
                    {'severity': 'FATAL', 'code': 'declared_mismatch', 'detail': 'x'},
                    {'severity': 7, 'code': 'declared_mismatch', 'detail': 'x'},
                    {'code': 'declared_mismatch', 'detail': 'x'}, {'severity': 'BLOCKED', 'detail': 'x'},
                    {'severity': 'BLOCKED', 'code': ['declared_mismatch'], 'detail': 'x'}, 'declared_mismatch', 7):
            self.refuse(self.mutated('blocked_protected',
                                     lambda d: d.__setitem__('failure_reasons', [good, bad])))
        self.refuse(self.mutated('blocked_protected', lambda d: d.__setitem__('failure_reasons', 'x')))
        self.refuse(self.mutated('blocked_protected', lambda d: d.pop('failure_reasons')))

    def test_task_id(self):  # R-09
        self.refuse('dotted')  # real verifier report with a verifier-valid ID the event schema does not allow
        for bad in ('-x', 'T.1', '_x', '', 'a' * 81, 'T\n1', 'T 1', None, 7, ['T-1'], '\xe9'):
            self.refuse(self.mutated('pass', lambda d: d.__setitem__('task_id', bad)))
        self.refuse(self.mutated('pass', lambda d: d.pop('task_id')))
        self.assertEqual(self.verify(self.mutated('pass', lambda d: d.__setitem__('task_id', 'a' * 64)))[0], 0)

    def test_incomplete_reports_and_early_blocked(self):  # R-14 (early BLOCKED), OD-2
        early = self.data('early_blocked')
        self.assertNotIn('task_id', early)
        self.assertNotIn('trust', early)
        self.refuse('early_blocked')
        for key in ('modified_paths', 'trust', 'task_id'):
            self.refuse(self.mutated('pass', lambda d: d.pop(key)))
        for bad in (None, 'x', {'a': 1}, 1):
            self.refuse(self.mutated('pass', lambda d: d.__setitem__('modified_paths', bad)))
        for bad in ([], [{}], 'x', {'a': 1}, [1]):
            self.refuse(self.mutated('pass', lambda d: d.__setitem__('failure_reasons', bad)
                                     if bad else d.__setitem__('status', 'BLOCKED')))
        self.refuse(self.write('list.json', [1, 2]))
        self.refuse(self.write('scalar.json', b'7'))

    def test_hostile_json(self):  # R-12
        text = self.report_path('pass').read_text()
        blocked = self.report_path('blocked_protected').read_text()
        cases = {
            'dup-top': '{"status": "PASS", ' + text.lstrip()[1:],
            'dup-trust': text.replace('"trust": {', '"trust": {"custody": "unauthenticated", ', 1),
            'dup-reason': blocked.replace('"severity": "BLOCKED"', '"severity": "BLOCKED", "severity": "BLOCKED"', 1),
            'nan': text.replace('"status": "PASS"', '"status": NaN'),
            'infinity': text.replace('"status": "PASS"', '"status": Infinity'),
            'float': text.replace('"registry_version": 1', '"registry_version": 1.5'),
            'huge-int': text.replace('"registry_version": 1', '"registry_version": 9007199254740993'),
            'lone-surrogate': text.replace('"PASS"', '"\\ud800"'),
            'control': text.replace('"PASS"', '"PA\\u0001SS"'),
            'newline': text.replace('"PASS"', '"PASS\\n"'),
            'non-ascii': text.replace('"modified_paths": [', '"modified_paths": ["\\u00e9", '),
            'deep': text.replace('"modified_paths": [', '"modified_paths": [[[[[[[[[1]]]]]]]]], ', 1),
            'very-deep': '[' * 100000,
            'empty': '', 'not-json': 'status=PASS', 'trailing': text + ' x',
        }
        parser_codes = {'dup-top': 'duplicate_key', 'dup-trust': 'duplicate_key', 'dup-reason': 'duplicate_key',
                        'nan': 'non_finite_number', 'infinity': 'non_finite_number', 'float': 'schema_invalid',
                        'huge-int': 'limit_exceeded', 'lone-surrogate': 'forbidden_content',
                        'control': 'forbidden_content', 'newline': 'forbidden_content',
                        'non-ascii': 'forbidden_content', 'deep': 'depth_exceeded', 'very-deep': 'depth_exceeded',
                        'empty': 'malformed_json', 'not-json': 'malformed_json', 'trailing': 'malformed_json'}
        for name, content in cases.items():
            with self.assertRaises(ev.ExperienceError, msg=name) as caught:  # each case fails for its own reason
                ev.loads_strict(content.encode('utf-8'))
            self.assertEqual(caught.exception.code, parser_codes[name], name)
            self.refuse(self.write(name + '.json', content.encode('utf-8')))
        self.refuse(self.write('bom.json', b'\xef\xbb\xbf' + text.encode()))
        self.refuse(self.write('bad-utf8.json', text.encode().replace(b'"PASS"', b'"\xff"')))
        self.refuse(self.write('nul.json', text.encode() + b'\x00'))
        nonascii = self.report_path('nonascii')
        self.assertIn(b'\\u00e9', nonascii.read_bytes())  # a real verifier report with a non-ASCII file name
        self.refuse(nonascii)  # UD-3: refused, fail closed

    def test_canaries_in_unused_fields_never_reach_the_journal(self):  # R-13, P-00, P-01 (record-verify)
        canary = 'CANARY-SECRET-9f3a'

        def change(data):
            for reason in data['failure_reasons']:
                reason['detail'] = canary + ' ' + str(self.base)
            data['modified_paths'] = ['src/%s.py' % canary]
            data['evidence'] = [{'ref': '/abs/%s' % canary, 'sha256': 'f' * 64}]
            data['limitations'] = [canary]
        path = self.mutated('blocked_protected', change)
        self.assertIn(canary.encode(), path.read_bytes())
        self.assertEqual(self.verify(path, classification='private')[0], 0)
        data = self.journal.read_bytes()
        for forbidden in (canary.encode(), str(self.base).encode(), str(path).encode(), b'/abs/', b'/home', b'/tmp',
                          b'secrets/k.txt', b'src/'):
            self.assertNotIn(forbidden, data)
        self.assertEqual(self.events()[0]['evidence'][0]['ref'], 'none')

    def test_report_is_validated_before_the_journal_is_touched(self):  # R-14
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        bad_journal = repo / 'j.jsonl'
        before = sup.snapshot(self.base)
        self.assertEqual(self.verify('early_blocked', journal=bad_journal), REFUSED)
        self.assertEqual(self.verify(self.base / 'nope.json', journal=bad_journal), REFUSED)
        self.assertEqual(before, sup.snapshot(self.base))
        self.assertEqual(self.verify('pass', journal=bad_journal)[2], 'RECORD-REFUSED: journal_in_repo\n')
        self.assertEqual(before, sup.snapshot(self.base))

    def test_existing_journal_is_unchanged_by_every_refusal(self):  # R-14
        self.assertEqual(self.verify('pass')[0], 0)
        before = sup.snapshot(self.base)
        for name in ('early_blocked', 'dotted', 'claimed_partial', 'claimed_blocked', 'nonascii'):
            self.assertEqual(self.verify(name), REFUSED, name)
        self.assertEqual(self.verify(self.base / 'missing.json'), REFUSED)
        self.assertEqual(before, sup.snapshot(self.base))
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 1)

    def test_usage_errors(self):  # R-14 / X-rec-08 for record-verify
        base = ['record-verify', '--journal', str(self.journal), '--report', str(self.report_path('pass')),
                '--repo-classification', 'synthetic']
        before = sup.snapshot(self.base)
        for args in (['record-verify'], base[:3], base[:1] + base[3:], base[:5], base + ['--report', 'x'],
                     base + ['--unknown', 'x'], base + ['positional'], base + ['--type', 'check.operator_run'],
                     base[:3] + ['--report', '--repo-classification', 'synthetic']):
            code, out, err = self.run_main(*args)
            self.assertEqual((code, out), (2, ''), args)
            self.assertTrue(err.startswith('BLOCKED: usage\n'), args)
        self.assertEqual(before, sup.snapshot(self.base))
        self.assertEqual(self.verify('pass', classification='secret')[2], 'RECORD-REFUSED: schema_invalid\n')
        self.assertFalse(self.journal.exists())


class PostAppendOutput(VerifyReportCase):
    """The event is durable once appended: output failure is never a refusal and never retried (P1 fix)."""

    def run_broken(self, kind, report, journal=None):
        err = io.StringIO()
        path = report if isinstance(report, Path) else self.report_path(report)
        with mock.patch.object(sys, 'stdout', BROKEN_STDOUTS[kind]()), redirect_stderr(err), \
                mock.patch.object(jr, 'append_event', wraps=jr.append_event) as spy:
            code = experience.main(['record-verify', '--journal', str(journal or self.journal), '--report', str(path),
                                    '--repo-classification', 'synthetic'])
        return code, err.getvalue(), spy.call_count

    def test_output_failure_after_a_successful_append_is_not_a_refusal(self):  # R-01 (P1)
        for kind in BROKEN_STDOUTS:
            for name in ('pass', 'partial', 'blocked_two'):
                journal = self.base / ('%s-%s.jsonl' % (kind, name))
                self.assertEqual(self.run_broken(kind, name, journal), (0, NOTICE, 1), (kind, name))
                events = self.events(journal)
                self.assertEqual([(e['seq'], e['type']) for e in events], [(1, 'verify.completed')])
                self.assertEqual(jr.validate_journal(str(journal)).count, 1)

    def test_no_automatic_retry_and_a_manual_retry_is_a_new_event(self):  # at-most-once capture
        self.assertEqual(self.run_broken('write-fails', 'pass'), (0, NOTICE, 1))
        self.assertEqual(self.run_broken('write-fails', 'pass'), (0, NOTICE, 1))
        self.assertEqual([e['seq'] for e in self.events()], [1, 2])

    def test_genuine_refusals_still_refuse_without_writing_even_with_broken_stdout(self):  # R-14
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        for kind in BROKEN_STDOUTS:
            before = sup.snapshot(self.base)
            self.assertEqual(self.run_broken(kind, 'early_blocked'),
                             (2, 'RECORD-REFUSED: report_invalid\n', 0), kind)  # refused before the journal
            self.assertEqual(self.run_broken(kind, 'pass', repo / 'j.jsonl'),
                             (2, 'RECORD-REFUSED: journal_in_repo\n', 1), kind)
            self.assertEqual(before, sup.snapshot(self.base))
            self.assertFalse(self.journal.exists())

    def test_working_stdout_is_unchanged(self):  # R-01
        code, out, err = self.verify('pass')
        self.assertEqual((code, err), (0, ''))
        self.assertRegex(out, r'^experience recorded: seq=1 type=verify\.completed event_id=ev-[0-9a-f]{32}\n'
                              r'authenticity: not verified \(integrity checks only\)\n$')


class ReportFileHandling(VerifyReportCase):
    def test_non_regular_and_linked_reports_are_refused(self):  # R-10 (in-process cases)
        real = self.report_path('pass')
        (self.base / 'link.json').symlink_to(real)
        os.link(real, self.base / 'hard.json')
        (self.base / 'dir.json').mkdir()
        (self.base / 'realdir').mkdir()
        (self.base / 'linkdir').symlink_to(self.base / 'realdir')
        (self.base / 'realdir' / 'r.json').write_bytes(real.read_bytes())
        for path in (self.base / 'link.json', self.base / 'hard.json', self.base / 'dir.json',
                     self.base / 'linkdir' / 'r.json', self.base / 'absent.json', Path('/dev/null'),
                     Path('/dev/zero'), Path('relative/../pass.json'), Path(''), self.base):
            self.refuse(path)
        self.assertEqual(self.verify(self.base / 'realdir' / 'r.json')[0], 0)  # a regular single-link file works

    def test_size_limits(self):  # R-11
        raw = self.report_path('pass').read_bytes()
        exact = self.write('exact.json', raw + b' ' * (ev.MAX_REPORT_BYTES - len(raw)))
        over = self.write('over.json', raw + b' ' * (ev.MAX_REPORT_BYTES + 1 - len(raw)))
        self.assertEqual(exact.stat().st_size, 1 << 20)
        self.assertEqual(self.verify(exact)[0], 0)
        self.assertEqual(self.events()[0]['data']['report_sha256'], hashlib.sha256(exact.read_bytes()).hexdigest())
        self.journal.unlink()
        self.refuse(over)

    def test_read_is_capped_even_if_the_file_grows(self):  # R-11 (growing file)
        big = self.write('big.json', b'x' * (2 << 20))
        real_fstat, total = os.fstat, []
        real_read = os.read

        def small(fd):
            info = real_fstat(fd)
            return os.stat_result((info.st_mode, info.st_ino, info.st_dev, info.st_nlink, info.st_uid, info.st_gid,
                                   10, 0, 0, 0))

        def counting(fd, size):
            data = real_read(fd, size)
            total.append(len(data))
            return data
        with mock.patch.object(os, 'fstat', small), mock.patch.object(os, 'read', counting):
            with self.assertRaises(ev.ExperienceError) as caught:
                jr.read_report(str(big))
        self.assertEqual(caught.exception.code, 'report_invalid')
        self.assertLessEqual(sum(total), ev.MAX_REPORT_BYTES + 1)

    def test_io_errors_are_report_invalid(self):  # R-10
        with mock.patch.object(os, 'read', side_effect=OSError(5, 'boom')):
            self.assertEqual(self.verify('pass'), REFUSED)
        self.assertFalse(self.journal.exists())

    def test_determinism_three_runs(self):  # DT-05 (record-verify)
        outputs = []
        for number in range(3):
            journal = self.base / ('d%d.jsonl' % number)
            for name in ('pass', 'partial', 'blocked_two'):
                self.assertEqual(self.verify(name, journal=journal, extra=['--run-id', 'run-fixed'])[0], 0)
            outputs.append(journal.read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])
        for event in jr.parse_journal(outputs[0])[0]:
            self.assertEqual(event['event_id'], ev.compute_event_id(event))


class RecordVerifySpecialFiles(unittest.TestCase):
    """Real processes with hard timeouts and no mocks: special report files never hang the command, and a
    closed stdout after the append is not a refusal (P1 fix)."""

    @classmethod
    def setUpClass(cls):
        cls._shared = tempfile.TemporaryDirectory(prefix='ai-sdlc-rv-shared-')
        cls.addClassCleanup(cls._shared.cleanup)
        cls.reports = build_reports(Path(cls._shared.name))

    def test_closed_stdout_and_closed_pipe_after_the_append(self):
        for mode in ('closed', 'pipe'):
            with tempfile.TemporaryDirectory(prefix='ai-sdlc-rv-') as temp:
                journal = Path(temp) / 'j.jsonl'
                command = [sys.executable, '-B', '-m', 'ai_sdlc', 'experience', 'record-verify', '--journal',
                           str(journal), '--report', str(self.reports / 'pass.json'), '--repo-classification',
                           'synthetic']
                if mode == 'closed':
                    done = subprocess.run(['sh', '-c', 'exec "$@" >&-', 'sh', *command], cwd=str(ROOT),
                                          capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
                    code, err = done.returncode, done.stderr
                else:
                    proc = subprocess.Popen(command, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True, stdin=subprocess.DEVNULL)
                    proc.stdout.close()
                    _, err = proc.communicate(timeout=30)
                    code = proc.returncode
                self.assertEqual(code, 0, (mode, err))
                self.assertIn(err, (NOTICE,) if mode == 'closed' else ('', NOTICE))
                self.assertNotIn('Exception ignored', err)
                self.assertEqual(jr.validate_journal(str(journal)).count, 1)

    def test_fifo_and_devices_do_not_hang(self):  # R-10
        with tempfile.TemporaryDirectory(prefix='ai-sdlc-rv-') as temp:
            fifo = Path(temp) / 'fifo.json'
            os.mkfifo(fifo)
            for path in (fifo, Path('/dev/zero'), Path('/dev/null'), Path(temp)):
                command = [sys.executable, '-B', '-m', 'ai_sdlc', 'experience', 'record-verify', '--journal',
                           str(Path(temp) / 'j.jsonl'), '--report', str(path), '--repo-classification', 'synthetic']
                try:
                    done = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=20,
                                          stdin=subprocess.DEVNULL)
                except subprocess.TimeoutExpired:
                    self.fail('record-verify hung on %s' % path)
                self.assertEqual((done.returncode, done.stderr), (2, 'RECORD-REFUSED: report_invalid\n'), str(path))
            self.assertFalse((Path(temp) / 'j.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
