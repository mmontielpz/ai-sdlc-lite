"""`ai-sdlc experience`: EXPERIMENTAL offline Experience journal commands (validate, record, record-verify).

No network, no subprocess, no model call, no implicit capture. Output never echoes event or report content.
Capture is explicit and opt-in: every command needs an explicit --journal path (there is no default).
"""

import os
import re
import sys

from . import experience_events as ev
from . import experience_journal as journal
from .experience_events import ExperienceError

USAGE = ('usage: python3 -B -m ai_sdlc experience validate --journal FILE\n'
         '       python3 -B -m ai_sdlc experience record --journal FILE --type T --repo-classification C [type fields]\n'
         '       python3 -B -m ai_sdlc experience record-verify --journal FILE --report FILE --repo-classification C\n'
         '  validate        read-only check of an Experience journal (schema, chain, limits); never repairs it\n'
         '  record          append one operator-reported event: task.initialized, task.approval_changed,\n'
         '                  check.operator_run or human.feedback (closed vocabularies; no free text)\n'
         '  record-verify   append one verify.completed event from a report written by `verify --out`\n'
         '  common options  [--run-id R] [--allow-in-repo] [--agent A] [--agent-version V] [--mode M]\n'
         'EXPERIMENTAL: offline, no telemetry; integrity is checked, authenticity is not.\n')

COMMON = ('--journal', '--repo-classification', '--run-id', '--allow-in-repo', '--agent', '--agent-version', '--mode')
BOOLEAN = ('--allow-in-repo',)
RECORD_TYPES = {
    # type: (required flags, optional flags)
    'task.initialized': (('--task-id', '--skill-target', '--context-written'), ()),
    'task.approval_changed': (('--task-id', '--task-revision', '--from', '--to'), ()),
    'check.operator_run': (('--task-id', '--check-id', '--exit-code', '--outcome', '--independence'),
                           ('--tests-total', '--tests-failed')),
    'human.feedback': (('--task-id', '--decision'), ('--friction',)),
}
REPEATABLE = ('--friction',)
NUMBER = re.compile(r'(0|[1-9][0-9]{0,6})')


class _Usage(Exception):
    pass


def _usage_error():
    sys.stderr.write('BLOCKED: usage\n' + USAGE)
    return 2


def _refused(code):
    sys.stderr.write('RECORD-REFUSED: %s\n' % code)
    return 2


def _parse(args, allowed):
    """Strict flag parser: known flags only, each at most once (--friction may repeat), a value for every
    non-boolean flag that is not itself a flag, no positionals. Raises _Usage."""
    values, rest = {}, list(args)
    while rest:
        flag = rest.pop(0)
        if flag not in allowed:
            raise _Usage()
        if flag in BOOLEAN:
            if flag in values:
                raise _Usage()
            values[flag] = True
            continue
        if not rest or rest[0].startswith('--'):
            raise _Usage()
        value = rest.pop(0)
        if flag in REPEATABLE:
            values.setdefault(flag, []).append(value)
        elif flag in values:
            raise _Usage()
        else:
            values[flag] = value
    return values


def _bad(text):
    """The refusal for a malformed value: non-printable-ASCII text is `forbidden_content` (as everywhere in the
    validator), anything else `schema_invalid`."""
    return ExperienceError('schema_invalid' if ev.PRINTABLE_ASCII.fullmatch(text) else 'forbidden_content')


def _number(text):
    if not NUMBER.fullmatch(text):
        raise _bad(text)
    return int(text)


def _environment(values):
    environment = ev.default_environment()
    for flag, key in (('--agent', 'agent_name'), ('--agent-version', 'agent_version'), ('--mode', 'mode')):
        if flag in values:
            environment[key] = values[flag]
    return environment


def _record_fields(type_name, values):
    subject = {'kind': 'task', 'task_id': values['--task-id'],
               'repo_classification': values['--repo-classification']}
    operator, human = {'role': 'operator'}, {'role': 'human'}
    base = {'type': type_name, 'subject': subject, 'trust_level': 'T0', 'independence': 'none', 'evidence': [],
            'environment': _environment(values)}
    if type_name == 'task.initialized':
        answer = values['--context-written']
        if answer not in ('yes', 'no'):
            raise _bad(answer)
        base.update(actor=operator, observer=operator, method='operator-recorded',
                    data={'skill_target': values['--skill-target'], 'context_written': answer == 'yes',
                          'approval': 'PENDING'})
    elif type_name == 'task.approval_changed':
        base.update(actor=human, observer=operator, method='human-decision-reported',
                    data={'from': values['--from'], 'to': values['--to'], 'task_revision': values['--task-revision']})
    elif type_name == 'check.operator_run':
        data = {'check_id': values['--check-id'], 'exit_code': _number(values['--exit-code']),
                'outcome': values['--outcome']}
        for flag, key in (('--tests-total', 'tests_total'), ('--tests-failed', 'tests_failed')):
            if flag in values:
                data[key] = _number(values[flag])
        base.update(actor=operator, observer=operator, method='operator-ran', independence=values['--independence'],
                    data=data)
    else:
        data = {'decision': values['--decision']}
        if '--friction' in values:
            data['friction'] = values['--friction']
        base.update(actor=human, observer=operator, method='human-decision-reported', data=data)
    return base


def _append(values, fields):
    run_id = values.get('--run-id')
    if run_id is not None and not ev.IDENT64.fullmatch(run_id):  # an explicit empty value is not "absent"
        raise _bad(run_id)
    ev.dry_validate(fields, run_id)  # a refusal here touches nothing
    event = journal.append_event(values['--journal'], fields, clock=ev.default_clock, run_id=run_id,
                                 allow_in_repo=bool(values.get('--allow-in-repo')))
    _announce(event)
    return 0


def _announce(event):
    """Report a persisted event. The event is already durable here: success output is best effort and its
    failure (closed or broken stdout, full pipe, no stdout at all) must never be reported as a refusal and the
    append is never retried. On failure: exit status stays 0, one best-effort stderr notice, and the broken
    stdout is replaced by /dev/null so interpreter shutdown cannot fail either."""
    try:
        sys.stdout.write('experience recorded: seq=%d type=%s event_id=%s\n' % (event['seq'], event['type'],
                                                                               event['event_id']))
        sys.stdout.write('authenticity: not verified (integrity checks only)\n')
        sys.stdout.flush()
    except Exception:
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except Exception:
            pass
        try:
            sys.stderr.write('RECORD-NOTICE: recorded; success output could not be written\n')
        except Exception:
            pass


def _record(args):
    allowed = set(COMMON) | {'--type'}
    for required, optional in RECORD_TYPES.values():
        allowed.update(required)
        allowed.update(optional)
    try:
        values = _parse(args, allowed)
        if any(flag not in values for flag in ('--journal', '--type', '--repo-classification')):
            raise _Usage()
        type_name = values['--type']
        if type_name not in RECORD_TYPES:
            return _refused('schema_invalid')
        required, optional = RECORD_TYPES[type_name]
        permitted = set(COMMON) | {'--type'} | set(required) | set(optional)
        if any(flag not in permitted for flag in values) or any(flag not in values for flag in required):
            raise _Usage()
    except _Usage:
        return _usage_error()
    try:
        return _append(values, _record_fields(type_name, values))
    except ExperienceError as error:
        return _refused(error.code)
    except Exception:  # fail closed on anything unexpected; never echo exception text
        return _refused('journal_io')


def _record_verify(args):
    try:
        values = _parse(args, set(COMMON) | {'--report'})
        if any(flag not in values for flag in ('--journal', '--report', '--repo-classification')):
            raise _Usage()
    except _Usage:
        return _usage_error()
    try:
        raw = journal.read_report(values['--report'])  # the report is fully validated before the journal is opened
        try:
            data = ev.loads_strict(raw)
        except ExperienceError:
            raise ExperienceError('report_invalid') from None
        fields = ev.report_to_fields(data, raw, _environment(values), values['--repo-classification'])
        return _append(values, fields)
    except ExperienceError as error:
        return _refused(error.code)
    except Exception:
        return _refused('journal_io')


def check_capture_args(classification, run_id):
    """Syntactic check used by `init --journal` before it does anything else."""
    return classification in ev.CLASSIFICATIONS and (run_id is None or bool(ev.IDENT64.fullmatch(run_id)))


def record_install(path, classification, run_id, allow_in_repo, target, outcome):
    """Append the one install event for a finished `init` (outcome comes from initializer)."""
    tool = {'role': 'tool', 'name': 'ai-sdlc-lite'}
    subject = {'kind': 'installation', 'repo_classification': classification}
    if outcome['ok']:
        fields = {'type': 'install.completed', 'method': 'tool-checked-hash', 'trust_level': 'T1',
                  'data': {'target': target, 'result': outcome['result'], 'file_count': outcome['file_count'],
                           'manifest_sha256': outcome['manifest_sha256']}}
    else:
        fields = {'type': 'install.failed', 'method': 'tool-reported', 'trust_level': 'T0',
                  'data': {'target': target, 'reason_code': outcome['reason'], 'partial': outcome['partial']}}
    fields.update(subject=subject, actor=tool, observer=tool, independence='none', evidence=[],
                  environment=ev.default_environment())
    return journal.append_event(path, fields, clock=ev.default_clock, run_id=run_id, allow_in_repo=allow_in_repo)


def main(argv):
    args = list(argv)
    if args in (['--help'], ['-h']) or args in (['validate', '--help'], ['validate', '-h']):
        sys.stdout.write(USAGE)
        return 0
    if args and args[0] == 'record':
        return _record(args[1:])
    if args and args[0] == 'record-verify':
        return _record_verify(args[1:])
    if not args or args[0] != 'validate':
        return _usage_error()
    rest, path = args[1:], None
    while rest:
        flag = rest.pop(0)
        if flag != '--journal' or path is not None or not rest or rest[0].startswith('--'):
            return _usage_error()
        path = rest.pop(0)
    if path is None:
        return _usage_error()
    try:
        summary = journal.validate_journal(path)
    except ExperienceError as error:
        where = '' if error.line is None else ' line %d' % error.line
        sys.stderr.write('JOURNAL-INVALID: %s%s\n' % (error.code, where))
        return 2
    except Exception:  # fail closed on anything unexpected; never echo exception text
        sys.stderr.write('JOURNAL-INVALID: validation_or_io_failure\n')
        return 2
    sys.stdout.write('experience journal ok: events=%d run_id=%s head=%s\n'
                     % (summary.count, summary.run_id or '-', summary.head or '-'))
    sys.stdout.write('authenticity: not verified (integrity checks only)\n')
    return 0
