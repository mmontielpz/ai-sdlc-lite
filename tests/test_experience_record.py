"""EXP-01B: `ai-sdlc experience record` (X-rec-01..12) and its privacy, determinism and offline gates."""

from contextlib import redirect_stderr, redirect_stdout
import errno
import io
import os
from pathlib import Path
import re
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
USAGE_PREFIX = 'BLOCKED: usage\n'
OK = re.compile(r'experience recorded: seq=(\d+) type=([a-z._]+) event_id=(ev-[0-9a-f]{32})\n'
                r'authenticity: not verified \(integrity checks only\)\n')
INIT = ['--type', 'task.initialized', '--task-id', 'T1', '--skill-target', 'claude-code', '--context-written', 'yes']
APPROVAL = ['--type', 'task.approval_changed', '--task-id', 'T1', '--task-revision', 'r1', '--from', 'PENDING',
            '--to', 'APPROVED']
CHECK = ['--type', 'check.operator_run', '--task-id', 'T1', '--check-id', 'V-1', '--exit-code', '0', '--outcome',
         'pass', '--independence', 'same-actor-family', '--tests-total', '3', '--tests-failed', '0']
FEEDBACK = ['--type', 'human.feedback', '--task-id', 'T1', '--decision', 'NEEDS_CHANGES', '--friction', 'docs',
            '--friction', 'install']
BASES = {'task.initialized': INIT, 'task.approval_changed': APPROVAL, 'check.operator_run': CHECK,
         'human.feedback': FEEDBACK}


NOTICE = 'RECORD-NOTICE: recorded; success output could not be written\n'


class BrokenOut:
    """A stdout whose write fails (closed pipe)."""

    def write(self, text):
        raise OSError(errno.EPIPE, 'Broken pipe')

    def flush(self):
        pass

    def fileno(self):
        raise OSError('no descriptor')


class FlushFailsOut:
    """A stdout that buffers the write and fails when flushed."""

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


def code_for(value):
    """The shipped validator refuses non-printable-ASCII text as forbidden_content before any vocabulary check."""
    return 'schema_invalid' if re.fullmatch(r'[\x20-\x7e]*', value) else 'forbidden_content'


def swap(args, flag, value):
    args = list(args)
    args[args.index(flag) + 1] = value
    return args


class RecordCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-rec-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.journal = self.base / 'journal.jsonl'
        patches = [mock.patch.object(ev, 'default_clock', sup.clock)]
        for target, name in ((socket, 'socket'), (subprocess, 'run'), (subprocess, 'Popen'), (os, 'system')):
            patches.append(mock.patch.object(target, name, side_effect=AssertionError('forbidden: %s' % name)))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = experience.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def rec(self, args, classification='synthetic', journal=None, extra=()):
        return self.run_main('record', '--journal', str(journal or self.journal), '--repo-classification',
                             classification, *extra, *args)

    def events(self):
        return jr.parse_journal(self.journal.read_bytes())[0]

    def assert_refused(self, result, code):
        self.assertEqual((result[0], result[1], result[2]), (2, '', 'RECORD-REFUSED: %s\n' % code), result)

    def assert_usage(self, result):
        self.assertEqual(result[0], 2, result)
        self.assertEqual(result[1], '')
        self.assertTrue(result[2].startswith(USAGE_PREFIX), result[2])

    def assert_nothing_written(self, action):
        before = sup.snapshot(self.base)
        result = action()
        self.assertEqual(before, sup.snapshot(self.base))
        return result


class RecordEvents(RecordCase):
    def test_each_type_is_valid_with_exact_trust_and_method(self):  # X-rec-01
        expected = {
            'task.initialized': ('operator-recorded', 'none', 'operator', 'operator',
                                 {'skill_target': 'claude-code', 'context_written': True, 'approval': 'PENDING'}),
            'task.approval_changed': ('human-decision-reported', 'none', 'human', 'operator',
                                      {'from': 'PENDING', 'to': 'APPROVED', 'task_revision': 'r1'}),
            'check.operator_run': ('operator-ran', 'same-actor-family', 'operator', 'operator',
                                   {'check_id': 'V-1', 'exit_code': 0, 'outcome': 'pass', 'tests_total': 3,
                                    'tests_failed': 0}),
            'human.feedback': ('human-decision-reported', 'none', 'human', 'operator',
                               {'decision': 'NEEDS_CHANGES', 'friction': ['docs', 'install']}),
        }
        for number, (type_name, args) in enumerate(BASES.items(), 1):
            code, out, err = self.rec(args)
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(OK.fullmatch(out).group(1, 2), (str(number), type_name))
        for event, (type_name, want) in zip(self.events(), expected.items()):
            method, independence, actor, observer, data = want
            self.assertEqual((event['type'], event['method'], event['trust_level'], event['independence']),
                             (type_name, method, 'T0', independence))
            self.assertEqual((event['actor'], event['observer']), ({'role': actor}, {'role': observer}))
            self.assertEqual((event['evidence'], event['data']), ([], data))
            self.assertEqual(event['subject'], {'kind': 'task', 'task_id': 'T1', 'repo_classification': 'synthetic'})
            self.assertEqual(event['run_id'], 'run-20261118-1')
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 4)

    def test_other_types_are_refused(self):  # X-rec-02
        for bad in ('install.completed', 'install.failed', 'verify.completed', 'unknown', '', ' task.initialized',
                    'TASK.INITIALIZED', 'task.initialized\n'):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(swap(INIT, '--type', bad))),
                                'schema_invalid')  # an unknown --type is refused before any other check
        self.assertFalse(self.journal.exists())

    def test_no_trust_method_actor_or_confirmation_flag_exists(self):  # X-rec-03
        for flag in ('--trust-level', '--trust', '--method', '--actor', '--observer', '--yes', '--confirm', '--h',
                     '--independence-claim', '--event-id', '--seq', '--prev', '--recorded-at', '--comment'):
            self.assert_usage(self.assert_nothing_written(lambda: self.rec(INIT + [flag, 'T3'])))
        self.assert_usage(self.rec(INIT + ['--yes']))
        self.assertFalse(self.journal.exists())
        for type_name, args in BASES.items():
            self.assertEqual(self.rec(args)[0], 0)
        for event in self.events():
            self.assertEqual(event['trust_level'], 'T0')

    def test_closed_vocabularies(self):  # X-rec-04
        valid = {'--skill-target': ('agents', 'claude-code'), '--context-written': ('yes', 'no'),
                 '--from': ('PENDING', 'APPROVED', 'REVISED', 'REJECTED'),
                 '--to': ('PENDING', 'APPROVED', 'REVISED', 'REJECTED'),
                 '--outcome': ('pass', 'fail', 'error'),
                 '--independence': ('none', 'same-actor-family', 'separate-person', 'unknown'),
                 '--decision': ('ACCEPTED', 'REJECTED', 'NEEDS_CHANGES', 'NO_DECISION')}
        owner = {'--skill-target': INIT, '--context-written': INIT, '--from': APPROVAL, '--to': APPROVAL,
                 '--outcome': CHECK, '--independence': CHECK, '--decision': FEEDBACK}
        for flag, values in valid.items():
            for value in values:
                journal = self.base / ('v-%s-%s.jsonl' % (flag[2:], value))
                self.assertEqual(self.rec(swap(owner[flag], flag, value), journal=journal)[0], 0, (flag, value))
            for bad in ('', 'maybe', value.lower() + 'x', ' ' + value, value + '\n', 'H', 'T1'):
                if bad in values:
                    continue
                self.assert_refused(self.assert_nothing_written(lambda: self.rec(swap(owner[flag], flag, bad))),
                                    code_for(bad))
        for classification in ('synthetic', 'public-oss', 'internal', 'private'):
            self.assertEqual(self.rec(INIT, classification, self.base / ('c-' + classification))[0], 0)
        for bad in ('', 'Synthetic', 'secret', 'public'):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, bad)), code_for(bad))
        for flag, good, bad in (('--agent', 'codex', 'gpt'), ('--mode', 'interactive', 'auto'),
                                ('--agent-version', '1.2.3', '1.2.3.4.5')):
            self.assertEqual(self.rec(INIT, extra=[flag, good], journal=self.base / ('a-' + flag[2:]))[0], 0)
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, extra=[flag, bad])),
                                'schema_invalid')

    def test_identifier_boundaries(self):  # X-rec-05
        cases = (('--task-id', INIT, 80, 81), ('--check-id', CHECK, 32, 33), ('--task-revision', APPROVAL, 64, 65))
        for flag, args, limit, over in cases:
            journal = self.base / ('id-' + flag[2:])
            self.assertEqual(self.rec(swap(args, flag, 'a' * limit), journal=journal)[0], 0)
            leading = () if flag == '--task-revision' else ('-x',)  # REVISION may begin with '-' (shipped pattern)
            for bad in ('a' * over, '', 'x\n', '\xe9', 'a b', 'x\x00y', '/etc/passwd') + leading:
                self.assert_refused(self.assert_nothing_written(lambda: self.rec(swap(args, flag, bad))),
                                    code_for(bad))
        self.assertEqual(self.rec(swap(APPROVAL, '--task-revision', 'r1.2+build-3_x'),
                                  journal=self.base / 'rev')[0], 0)
        self.assertEqual(self.rec(INIT, extra=['--run-id', 'r' * 64], journal=self.base / 'run64')[0], 0)
        for bad in ('r' * 65, '-r', 'r\n', '', 'r r'):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, extra=['--run-id', bad])),
                                code_for(bad))

    def test_numbers_are_strict_decimal_ascii(self):  # X-rec-06
        for good in ('0', '1', '255'):
            self.assertEqual(self.rec(swap(CHECK, '--exit-code', good), journal=self.base / ('n' + good))[0], 0)
        for bad in ('256', '01', '+1', '-1', '1.5', ' 1', '1 ', '1\n', '１', '', '12345678', '0x10', '1e2'):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(swap(CHECK, '--exit-code', bad))),
                                code_for(bad))
        base = CHECK[:-4]  # without the optional test counts
        self.assertEqual(self.rec(base, journal=self.base / 'notests')[0], 0)
        self.assertEqual(self.rec(base + ['--tests-total', '1000000', '--tests-failed', '1000000'],
                                  journal=self.base / 'maxtests')[0], 0)
        for extra in (['--tests-total', '3'], ['--tests-failed', '0'], ['--tests-total', '1', '--tests-failed', '2'],
                      ['--tests-total', '1000001', '--tests-failed', '0']):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(base + extra)), 'schema_invalid')

    def test_friction_is_closed_unique_and_repeatable(self):  # X-rec-07
        every = ['install', 'discovery', 'task-contract', 'verification', 'recovery', 'docs', 'other']
        args = FEEDBACK[:6]
        self.assertEqual(self.rec(args + sum((['--friction', f] for f in every), []))[0], 0)
        self.assertEqual(self.events()[0]['data']['friction'], every)
        self.assertEqual(self.rec(args, journal=self.base / 'none')[0], 0)
        self.assertNotIn('friction', jr.parse_journal((self.base / 'none').read_bytes())[0][0]['data'])
        for bad in (['--friction', 'docs', '--friction', 'docs'], ['--friction', 'free text'], ['--friction', '']):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(args + bad, journal=self.base / 'x')),
                                'schema_invalid')

    def test_usage_errors_write_nothing(self):  # X-rec-08
        journal = ['--journal', str(self.journal)]
        classification = ['--repo-classification', 'synthetic']
        cases = [
            ['record'], ['record'] + classification + INIT, ['record'] + journal + INIT,
            ['record'] + journal + classification,
            ['record'] + journal + classification + [a for a in INIT if a not in ('--task-id', 'T1')],
            ['record'] + journal + classification + INIT + ['--task-id', 'T2'],
            ['record'] + journal + classification + journal + INIT,
            ['record'] + journal + classification + INIT + ['--unknown', 'x'],
            ['record'] + journal + classification + INIT[:2] + ['--task-id', '--skill-target'],
            ['record'] + journal + classification + INIT + ['positional'],
            ['record'] + journal + classification + INIT + ['--allow-in-repo', '--allow-in-repo'],
            ['record'] + journal + classification + INIT[:-1],
            ['record'] + journal + classification + FEEDBACK[:6] + ['--check-id', 'V-1'],
            ['record'] + journal + classification + CHECK[:2] + ['--task-id', 'T1'],
            ['record', 'validate'], ['record-verify'],
        ]
        for args in cases:
            self.assert_usage(self.assert_nothing_written(lambda: self.run_main(*args)))
        self.assertFalse(self.journal.exists())

    def test_journal_path_policy_through_the_cli(self):  # X-rec-09
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, journal=repo / 'j.jsonl')),
                            'journal_in_repo')
        self.assertEqual(self.rec(INIT, journal=repo / 'j.jsonl', extra=['--allow-in-repo'])[0], 0)
        real = self.base / 'real'
        real.mkdir()
        (self.base / 'link').symlink_to(real)
        (self.base / 'leaf').symlink_to(real / 'x.jsonl')
        (self.base / 'dir.jsonl').mkdir()
        (self.base / 'plain.txt').write_text('not a journal\n')
        for path in (self.base / 'link' / 'j.jsonl', self.base / 'leaf', self.base / 'dir.jsonl'):
            self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, journal=path)),
                                'journal_invalid_path')
        self.assert_refused(self.assert_nothing_written(lambda: self.rec(INIT, journal=self.base / 'plain.txt')),
                            'malformed_json')
        self.assertEqual((self.base / 'plain.txt').read_text(), 'not a journal\n')
        self.assert_refused(self.rec(INIT, journal='relative/../escape.jsonl'), 'journal_invalid_path')

    def test_run_id_rules(self):  # X-rec-10
        self.assertEqual(self.rec(INIT)[0], 0)
        self.assertEqual(self.rec(CHECK)[0], 0)
        self.assertEqual({e['run_id'] for e in self.events()}, {'run-20261118-1'})
        self.assert_refused(self.assert_nothing_written(lambda: self.rec(CHECK, extra=['--run-id', 'other'])),
                            'chain_broken')
        self.assertEqual(self.rec(CHECK, extra=['--run-id', 'run-20261118-1'])[0], 0)
        self.assertEqual(self.rec(INIT, journal=self.base / 'named', extra=['--run-id', 'my-run'])[0], 0)
        self.assertEqual(jr.parse_journal((self.base / 'named').read_bytes())[0][0]['run_id'], 'my-run')
        self.assertEqual([e['seq'] for e in self.events()], [1, 2, 3])
        self.assertEqual(jr.validate_journal(str(self.journal)).count, 3)

    def test_environment_is_derived_and_host_data_is_absent(self):  # X-rec-11
        os.environ['EXPERIENCE_CANARY'] = 'CANARY-ENV-77'
        self.addCleanup(os.environ.pop, 'EXPERIENCE_CANARY', None)
        self.assertEqual(self.rec(INIT)[0], 0)
        self.assertEqual(self.events()[0]['environment'], ev.default_environment())
        self.assertEqual(set(self.events()[0]['environment']), {'platform', 'lite_version', 'python'})
        self.assertEqual(self.rec(CHECK, extra=['--agent', 'claude-code', '--agent-version', '2.1', '--mode',
                                                 'noninteractive'])[0], 0)
        self.assertEqual(self.events()[1]['environment'],
                         dict(ev.default_environment(), agent_name='claude-code', agent_version='2.1',
                              mode='noninteractive'))
        data = self.journal.read_bytes()
        for forbidden in (b'CANARY-ENV-77', str(self.base).encode(), os.path.expanduser('~').encode(),
                          os.environ.get('USER', 'nouser-x').encode(), os.uname().nodename.encode()):
            self.assertNotIn(forbidden, data)

    def test_output_contract_and_no_echo(self):  # X-rec-12
        code, out, err = self.rec(INIT)
        self.assertEqual((code, err), (0, ''))
        match = OK.fullmatch(out)
        self.assertEqual(match.group(3), self.events()[0]['event_id'])
        canary = 'CANARY-ARG-4242'
        for args, want in ((swap(INIT, '--skill-target', canary), 'schema_invalid'),
                           (swap(INIT, '--task-id', canary + '\n'), 'forbidden_content'),
                           (swap(INIT, '--type', canary), 'schema_invalid')):
            code, out, err = self.rec(args, journal=self.base / 'refused')
            self.assertEqual((code, out, err), (2, '', 'RECORD-REFUSED: %s\n' % want))
        self.assertFalse((self.base / 'refused').exists())
        code, out, err = self.run_main('record', '--journal', str(self.journal), '--bogus', canary)
        self.assertNotIn(canary, out + err.replace(experience.USAGE, ''))
        with mock.patch.object(jr, 'append_event', side_effect=RuntimeError(canary)):
            self.assert_refused(self.rec(CHECK, journal=self.base / 'boom'), 'journal_io')

    def test_canaries_in_argv_never_reach_the_journal(self):  # P-00, P-01 (record)
        canary = 'CANARY-SECRET-9f3a'
        for flag, args in (('--skill-target', INIT), ('--decision', FEEDBACK), ('--outcome', CHECK),
                           ('--to', APPROVAL)):
            self.assertEqual(self.rec(swap(args, flag, canary), journal=self.base / 'c')[0], 2)
        self.assertFalse((self.base / 'c').exists())
        for args in BASES.values():
            self.assertEqual(self.rec(args)[0], 0)
        data = self.journal.read_bytes()
        for forbidden in (canary.encode(), str(self.base).encode(), str(ROOT).encode(), b'/home', b'/tmp'):
            self.assertNotIn(forbidden, data)

    def test_determinism_three_runs(self):  # DT-05 (record)
        outputs = []
        for number in range(3):
            journal = self.base / ('run%d.jsonl' % number)
            for args in BASES.values():
                self.assertEqual(self.rec(args, journal=journal, extra=['--run-id', 'run-fixed'])[0], 0)
            outputs.append(journal.read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])
        for event in jr.parse_journal(outputs[0])[0]:
            self.assertEqual(event['event_id'], ev.compute_event_id(event))


class PostAppendOutput(RecordCase):
    """The event is durable once appended: output failure is never a refusal and never retried (P1 fix)."""

    def run_broken(self, kind, args, journal=None):
        err = io.StringIO()
        with mock.patch.object(sys, 'stdout', BROKEN_STDOUTS[kind]()), redirect_stderr(err), \
                mock.patch.object(jr, 'append_event', wraps=jr.append_event) as spy:
            code = experience.main(['record', '--journal', str(journal or self.journal), '--repo-classification',
                                    'synthetic', *args])
        return code, err.getvalue(), spy.call_count

    def test_output_failure_after_a_successful_append_is_not_a_refusal(self):  # X-rec-12 (P1)
        for kind in BROKEN_STDOUTS:
            for number, (type_name, args) in enumerate(BASES.items(), 1):
                journal = self.base / ('%s-%s.jsonl' % (kind, type_name))
                code, err, appends = self.run_broken(kind, args, journal)
                self.assertEqual((code, err, appends), (0, NOTICE, 1), (kind, type_name))
                self.assertNotIn('RECORD-REFUSED', err)
                events = jr.parse_journal(journal.read_bytes())[0]  # exactly one valid event
                self.assertEqual([(e['seq'], e['type']) for e in events], [(1, type_name)])
                self.assertEqual(jr.validate_journal(str(journal)).count, 1)

    def test_a_retry_after_output_failure_is_a_new_distinct_event(self):  # at-most-once capture, no auto retry
        self.assertEqual(self.run_broken('write-fails', CHECK), (0, NOTICE, 1))
        self.assertEqual(self.run_broken('write-fails', CHECK), (0, NOTICE, 1))  # one append per invocation
        self.assertEqual([e['seq'] for e in self.events()], [1, 2])
        self.assertEqual(len({e['event_id'] for e in self.events()}), 2)

    def test_genuine_pre_append_failures_still_refuse_without_writing(self):  # X-rec-08/09 with broken stdout
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        for kind in BROKEN_STDOUTS:
            before = sup.snapshot(self.base)
            self.assertEqual(self.run_broken(kind, swap(INIT, '--skill-target', 'nope')),
                             (2, 'RECORD-REFUSED: schema_invalid\n', 0), kind)
            self.assertEqual(self.run_broken(kind, INIT, repo / 'j.jsonl'),
                             (2, 'RECORD-REFUSED: journal_in_repo\n', 1), kind)  # append attempted, refused, no write
            self.assertEqual(before, sup.snapshot(self.base))
            self.assertFalse(self.journal.exists())

    def test_working_stdout_is_unchanged(self):  # X-rec-12
        code, out, err = self.rec(INIT)
        self.assertEqual((code, err), (0, ''))
        self.assertRegex(out, r'^experience recorded: seq=1 type=task\.initialized event_id=ev-[0-9a-f]{32}\n'
                              r'authenticity: not verified \(integrity checks only\)\n$')


class RecordSpecialFiles(unittest.TestCase):
    """Real-process checks with hard timeouts (no mocks): special files never hang `record`."""

    def test_fifo_and_special_journals_are_refused(self):  # X-rec-09
        with tempfile.TemporaryDirectory(prefix='ai-sdlc-rec-') as temp:
            fifo = Path(temp) / 'fifo.jsonl'
            os.mkfifo(fifo)
            for path in (fifo, Path('/dev/null'), Path(temp)):
                command = [sys.executable, '-B', '-m', 'ai_sdlc', 'experience', 'record', '--journal', str(path),
                           '--repo-classification', 'synthetic', *INIT]
                try:
                    done = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=20,
                                          stdin=subprocess.DEVNULL)
                except subprocess.TimeoutExpired:
                    self.fail('record hung on %s' % path)
                self.assertEqual((done.returncode, done.stderr), (2, 'RECORD-REFUSED: journal_invalid_path\n'))


class RecordRealStdoutFailures(unittest.TestCase):
    """Real processes (no mocks): a closed or broken stdout after the append is not a refusal (P1 fix)."""

    def command(self, journal):
        return [sys.executable, '-B', '-m', 'ai_sdlc', 'experience', 'record', '--journal', str(journal),
                '--repo-classification', 'synthetic', *CHECK]

    def test_closed_stdout(self):
        with tempfile.TemporaryDirectory(prefix='ai-sdlc-rec-') as temp:
            journal = Path(temp) / 'j.jsonl'
            done = subprocess.run(['sh', '-c', 'exec "$@" >&-', 'sh', *self.command(journal)], cwd=str(ROOT),
                                  capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
            self.assertEqual((done.returncode, done.stderr), (0, NOTICE))
            self.assertEqual(jr.validate_journal(str(journal)).count, 1)

    def test_reader_closed_pipe(self):
        with tempfile.TemporaryDirectory(prefix='ai-sdlc-rec-') as temp:
            journal = Path(temp) / 'j.jsonl'
            proc = subprocess.Popen(self.command(journal), cwd=str(ROOT), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, stdin=subprocess.DEVNULL)
            proc.stdout.close()  # the reader goes away before the command writes
            _, err = proc.communicate(timeout=30)
            self.assertEqual(proc.returncode, 0, err)  # never 120 from a failed flush at shutdown
            self.assertIn(err, ('', NOTICE))
            self.assertNotIn('Exception ignored', err)
            self.assertEqual(jr.validate_journal(str(journal)).count, 1)


if __name__ == '__main__':
    unittest.main()
