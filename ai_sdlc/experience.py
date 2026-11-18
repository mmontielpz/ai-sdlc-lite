"""`ai-sdlc experience`: EXPERIMENTAL offline Experience journal commands (EXP-01A: validate only).

No network, no subprocess, no model call, no implicit capture. Output never echoes event content.
"""

import sys

from . import experience_journal as journal
from .experience_events import ExperienceError

USAGE = ('usage: python3 -B -m ai_sdlc experience validate --journal FILE\n'
         '  validate  read-only check of an Experience journal (schema, chain, limits); never repairs it\n'
         'EXPERIMENTAL: offline, no telemetry; integrity is checked, authenticity is not.\n')


def _usage_error():
    sys.stderr.write('BLOCKED: usage\n' + USAGE)
    return 2


def main(argv):
    args = list(argv)
    if args in (['--help'], ['-h']) or args == ['validate', '--help'] or args == ['validate', '-h']:
        sys.stdout.write(USAGE)
        return 0
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
