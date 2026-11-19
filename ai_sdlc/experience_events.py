"""Experience event contract `ai-sdlc-experience-event/1`: canonical JSON, identity and validation.

EXPERIMENTAL. Offline, stdlib only. Events are inert, closed-vocabulary records of observable Lite
outcomes: no paths, no content, no free text, no T3 and (in this increment) no human `H` claims.
Validation never executes, evaluates, opens or interprets anything found in an event.
See docs/EXPERIENCE_CONTRACT.md. Integrity checks here detect accidental or naive modification;
they do not authenticate who produced an event.
"""

import datetime
import hashlib
import importlib.util
import json
import re
import sys
import time

from ._root import framework_root

SCHEMA = 'ai-sdlc-experience-event/1'
MAX_EVENTS = 5000
MAX_JOURNAL_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 8
MAX_INT = 2 ** 53

TYPES = ('install.completed', 'install.failed', 'task.initialized', 'task.approval_changed',
         'verify.completed', 'check.operator_run', 'human.feedback')
METHOD_CEILING = {
    'tool-observed-git-state': 'T2', 'tool-checked-hash': 'T1', 'tool-reported': 'T0', 'operator-ran': 'T0',
    'operator-recorded': 'T0', 'human-decision-reported': 'T0', 'agent-reported': 'T0', 'ci-run': 'T0',
    'unknown': 'T0',
}
TRUST_RANK = {'T0': 0, 'T1': 1, 'T2': 2}
INDEPENDENCE = ('none', 'same-actor-family', 'separate-person', 'ci-attested', 'unknown')
ROLES = ('agent', 'operator', 'human', 'tool', 'ci')
PARTY_NAMES = ('claude-code', 'ai-sdlc-lite', 'unknown')
PLATFORMS = ('linux', 'macos', 'windows', 'unknown')
AGENTS = ('claude-code', 'codex', 'copilot', 'none', 'unknown')
MODES = ('noninteractive', 'interactive', 'unknown')
CLASSIFICATIONS = ('synthetic', 'public-oss', 'internal', 'private')
TARGETS = ('agents', 'claude-code')
INIT_REASONS = (
    'duplicate_manifest_key', 'external_git_metadata', 'framework_overlap', 'framework_unavailable',
    'installation_content_conflict', 'installation_inventory_conflict', 'installation_missing',
    'installation_version_conflict', 'invalid_git_root', 'invalid_manifest', 'inventory_limit', 'oversized_file',
    'unsafe_file', 'unsafe_path', 'unsupported_filesystem_primitives', 'validation_or_io_failure',
)
APPROVAL = ('PENDING', 'APPROVED', 'REVISED', 'REJECTED')
DECISIONS = ('ACCEPTED', 'REJECTED', 'NEEDS_CHANGES', 'NO_DECISION')
FRICTION = ('install', 'discovery', 'task-contract', 'verification', 'recovery', 'docs', 'other')
STATUSES = ('PASS', 'PARTIAL', 'BLOCKED')
EXIT_FOR_STATUS = {'PASS': 0, 'PARTIAL': 1, 'BLOCKED': 2}

SHA256 = re.compile(r'[0-9a-f]{64}')
EVENT_ID = re.compile(r'ev-[0-9a-f]{32}')
IDENT64 = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')
TASK_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}')
CHECK_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,31}')
REVISION = re.compile(r'[A-Za-z0-9._+-]{1,64}')
LITE_VERSION = re.compile(r'[0-9A-Za-z.+-]{1,32}')
PYTHON = re.compile(r'3\.[0-9]{1,2}')
AGENT_VERSION = re.compile(r'[0-9]{1,3}(\.[0-9]{1,3}){0,3}')
LITE_COMMIT = re.compile(r'[0-9a-f]{40}')
TIMESTAMP = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z')
PRINTABLE_ASCII = re.compile(r'[\x20-\x7e]*')
REASON_CODE = re.compile(r'[a-z][a-z0-9_]{0,63}')

# Per-type rules: (methods, required trust level, actor roles, observer roles, independence values).
TYPE_RULES = {
    'install.completed': (('tool-checked-hash',), 'T1', ('tool',), ('tool',), ('none',)),
    'install.failed': (('tool-reported',), 'T0', ('tool',), ('tool',), ('none',)),
    'task.initialized': (('operator-recorded',), 'T0', ('operator',), ('operator',), ('none', 'unknown')),
    'task.approval_changed': (('human-decision-reported',), 'T0', ('human',), ('operator',), ('none',)),
    'verify.completed': (('tool-observed-git-state',), 'T2', ('tool',), ('tool',), ('none',)),
    'check.operator_run': (('operator-ran',), 'T0', ('operator', 'agent'), ('operator',),
                           ('none', 'same-actor-family', 'separate-person', 'unknown')),
    'human.feedback': (('human-decision-reported',), 'T0', ('human',), ('operator',), ('none',)),
}
SUBJECT_KIND = {'install.completed': 'installation', 'install.failed': 'installation'}


class ExperienceError(Exception):
    """A refusal with a stable code. Messages never contain event or file content."""

    def __init__(self, code, line=None, field=None):
        super().__init__(code)
        self.code = code
        self.line = line
        self.field = field


# ---------------------------------------------------------------------------------------------
# Canonical JSON, identity, strict loading
# ---------------------------------------------------------------------------------------------

def canonical_json(value):
    """Canonical bytes: sorted keys, compact separators, ASCII-escaped, no NaN/Infinity."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def compute_event_id(event):
    body = {key: value for key, value in event.items() if key != 'event_id'}
    return 'ev-' + sha256_hex(canonical_json(body))[:32]


def _scan_depth(text, limit):
    depth, in_string, escaped = 0, False, False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in '[{':
            depth += 1
            if depth > limit:
                raise ExperienceError('depth_exceeded')
        elif char in ']}':
            depth -= 1


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ExperienceError('duplicate_key')
        result[key] = value
    return result


def _constant(_name):
    raise ExperienceError('non_finite_number')


def _float(text):
    value = float(text)
    if value != value or value in (float('inf'), float('-inf')):
        raise ExperienceError('non_finite_number')
    raise ExperienceError('schema_invalid')  # the contract has no floating-point numbers


def _int(text):
    value = int(text)
    if abs(value) > MAX_INT:
        raise ExperienceError('limit_exceeded')
    return value


def _check_strings(value, depth=0):
    if depth > MAX_DEPTH:
        raise ExperienceError('depth_exceeded')
    if isinstance(value, str):
        if not PRINTABLE_ASCII.fullmatch(value):
            raise ExperienceError('forbidden_content')
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_strings(key, depth + 1)
            _check_strings(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_strings(item, depth + 1)


def loads_strict(raw):
    """Parse one JSON document from bytes: strict UTF-8 (no BOM), bounded depth, no duplicate keys,
    no NaN/Infinity/floats, bounded integers, printable-ASCII strings only."""
    if raw.startswith(b'\xef\xbb\xbf'):
        raise ExperienceError('bad_encoding')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise ExperienceError('bad_encoding') from None
    _scan_depth(text, MAX_DEPTH)
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant,
                           parse_float=_float, parse_int=_int)
    except RecursionError:
        raise ExperienceError('depth_exceeded') from None
    except ValueError:
        raise ExperienceError('malformed_json') from None
    _check_strings(value)
    return value


# ---------------------------------------------------------------------------------------------
# Verifier registry (read from the reviewed verifier source; never modified, never executed as a command)
# ---------------------------------------------------------------------------------------------

_REGISTRY = None


def load_registry():
    """Return (registry_version, {code: allowed severities}) from scripts/verify_scope.py."""
    global _REGISTRY
    if _REGISTRY is None:
        path = framework_root() / 'scripts' / 'verify_scope.py'
        if path.is_symlink() or not path.is_file():
            raise ExperienceError('registry_unavailable')
        spec = importlib.util.spec_from_file_location('_ai_sdlc_experience_verifier_registry', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        codes = {code: tuple(value[0]) for code, value in module.FAILURE_CODES.items()}
        _REGISTRY = (int(module.REGISTRY_VERSION), codes)
    return _REGISTRY


# ---------------------------------------------------------------------------------------------
# Structural validation (closed schema)
# ---------------------------------------------------------------------------------------------

def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _obj(value, field, required, properties):
    if not isinstance(value, dict):
        raise ExperienceError('schema_invalid', field=field)
    for key in value:
        if key not in properties:
            raise ExperienceError('schema_invalid', field=field + '.' + 'unknown-key')
    for key in required:
        if key not in value:
            raise ExperienceError('schema_invalid', field=field + '.' + key)
    for key, check in properties.items():
        if key in value:
            check(value[key], field + '.' + key)


def _enum(*allowed):
    def check(value, field):
        if not isinstance(value, str) or value not in allowed:
            raise ExperienceError('schema_invalid', field=field)
    return check


def _const(expected):
    def check(value, field):
        if value != expected or type(value) is not type(expected):
            raise ExperienceError('schema_invalid', field=field)
    return check


def _regex(pattern):
    def check(value, field):
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ExperienceError('schema_invalid', field=field)
    return check


def _integer(low, high):
    def check(value, field):
        if not _is_int(value) or not low <= value <= high:
            raise ExperienceError('schema_invalid', field=field)
    return check


def _boolean(value, field):
    if not isinstance(value, bool):
        raise ExperienceError('schema_invalid', field=field)


def _array(item, limit, unique=True):
    def check(value, field):
        if not isinstance(value, list) or len(value) > limit:
            raise ExperienceError('schema_invalid', field=field)
        for entry in value:
            item(entry, field + '[]')
        if unique and len({json.dumps(entry, sort_keys=True) for entry in value}) != len(value):
            raise ExperienceError('schema_invalid', field=field)
    return check


def _party(value, field):
    _obj(value, field, ('role',), {'role': _enum(*ROLES), 'name': _enum(*PARTY_NAMES)})


def _subject(value, field):
    _obj(value, field, ('kind',), {
        'kind': _enum('task', 'installation'), 'task_id': _regex(TASK_ID), 'revision': _regex(REVISION),
        'repo_classification': _enum(*CLASSIFICATIONS)})


def _environment(value, field):
    _obj(value, field, ('platform', 'lite_version'), {
        'platform': _enum(*PLATFORMS), 'lite_version': _regex(LITE_VERSION), 'bundle_digest': _regex(SHA256),
        'lite_commit': _regex(LITE_COMMIT), 'python': _regex(PYTHON), 'agent_name': _enum(*AGENTS),
        'agent_version': _regex(AGENT_VERSION), 'mode': _enum(*MODES)})


def _evidence_item(value, field):
    _obj(value, field, ('kind', 'ref'), {
        'kind': _enum('verification-report'), 'ref': _const('none'), 'sha256': _regex(SHA256)})


_FACETS = {
    'baseline': _enum('agent-reported', 'operator-supplied-record'),
    'hash_integrity': _enum('none', 'partial', 'all'),
    'custody': _const('unauthenticated'),
    'independent_execution': _const('not-verified'),
    'agent_assertions': _const('unverified'),
}


def _facets(value, field):
    _obj(value, field, tuple(_FACETS), _FACETS)


def _exit_code(value, field):
    if not _is_int(value) or value not in (0, 1, 2):
        raise ExperienceError('schema_invalid', field=field)


def _reason_codes(value, field):
    # Membership in the live verifier registry is checked in _check_verify; here: closed array shape.
    if not isinstance(value, list) or len(value) > 32:
        raise ExperienceError('schema_invalid', field=field)
    for code in value:
        if not isinstance(code, str) or not REASON_CODE.fullmatch(code):
            raise ExperienceError('schema_invalid', field=field + '[]')
    if value != sorted(set(value)):
        raise ExperienceError('schema_invalid', field=field)


DATA_SPECS = {
    'install.completed': (('target', 'result', 'file_count', 'manifest_sha256'), {
        'target': _enum(*TARGETS), 'result': _enum('INITIALIZED', 'UNCHANGED', 'CHECK_OK'),
        'file_count': _integer(1, 20000), 'manifest_sha256': _regex(SHA256)}),
    'install.failed': (('target', 'reason_code', 'partial'), {
        'target': _enum(*TARGETS), 'reason_code': _enum(*INIT_REASONS), 'partial': _boolean}),
    'task.initialized': (('skill_target', 'context_written', 'approval'), {
        'skill_target': _enum(*TARGETS), 'context_written': _boolean, 'approval': _const('PENDING')}),
    'task.approval_changed': (('from', 'to', 'task_revision'), {
        'from': _enum(*APPROVAL), 'to': _enum(*APPROVAL), 'task_revision': _regex(REVISION)}),
    'verify.completed': (('status', 'exit_code', 'failure_reason_codes', 'modified_path_count', 'report_sha256',
                          'registry_version', 'facets', 'checks_origin'), {
        'status': _enum(*STATUSES), 'exit_code': _exit_code,
        'failure_reason_codes': _reason_codes, 'modified_path_count': _integer(0, 1000000),
        'report_sha256': _regex(SHA256), 'registry_version': _const(1), 'facets': _facets,
        'checks_origin': _const('agent-reported')}),
    'check.operator_run': (('check_id', 'exit_code', 'outcome'), {
        'check_id': _regex(CHECK_ID), 'exit_code': _integer(0, 255), 'outcome': _enum('pass', 'fail', 'error'),
        'tests_total': _integer(0, 1000000), 'tests_failed': _integer(0, 1000000)}),
    'human.feedback': (('decision',), {
        'decision': _enum(*DECISIONS), 'friction': _array(_enum(*FRICTION), 8)}),
}


TOP_REQUIRED = ('schema', 'event_id', 'run_id', 'seq', 'type', 'recorded_at', 'subject', 'actor', 'observer',
                'method', 'trust_level', 'independence', 'environment', 'evidence', 'data', 'prev')
TOP_PROPERTIES = {
    'schema': _const(SCHEMA), 'event_id': _regex(EVENT_ID), 'run_id': _regex(IDENT64),
    'seq': _integer(1, MAX_EVENTS), 'type': _enum(*TYPES), 'recorded_at': _regex(TIMESTAMP),
    'subject': _subject, 'actor': _party, 'observer': _party, 'method': _enum(*METHOD_CEILING),
    'trust_level': _enum('T0', 'T1', 'T2', 'H'), 'independence': _enum(*INDEPENDENCE),
    'environment': _environment, 'evidence': _array(_evidence_item, 1, unique=False),
    'data': lambda value, field: None,  # per-type, below
    'prev': lambda value, field: None,  # checked below
}


def _check_timestamp(value):
    try:
        moment = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        raise ExperienceError('schema_invalid', field='event.recorded_at') from None
    if not 2000 <= moment.year <= 2999:
        raise ExperienceError('schema_invalid', field='event.recorded_at')


def _check_verify(event):
    data = event['data']
    version, registry = load_registry()
    if data['registry_version'] != version:
        raise ExperienceError('schema_invalid', field='event.data.registry_version')
    codes, status = data['failure_reason_codes'], data['status']
    if any(code not in registry for code in codes):
        raise ExperienceError('schema_invalid', field='event.data.failure_reason_codes')
    if data['exit_code'] != EXIT_FOR_STATUS[status]:
        raise ExperienceError('schema_invalid', field='event.data.exit_code')
    if status == 'PASS' and codes:
        raise ExperienceError('schema_invalid', field='event.data.failure_reason_codes')
    if status == 'PARTIAL' and (not codes or any('PARTIAL' not in registry[code] for code in codes)):
        raise ExperienceError('schema_invalid', field='event.data.failure_reason_codes')
    if status == 'BLOCKED' and not any('BLOCKED' in registry[code] for code in codes):
        raise ExperienceError('schema_invalid', field='event.data.failure_reason_codes')
    evidence = event['evidence']
    if len(evidence) != 1 or evidence[0].get('sha256') != data['report_sha256']:
        raise ExperienceError('schema_invalid', field='event.evidence')


def validate_event(event, *, expected_seq=None, previous_id=None, run_id=None):
    """Validate one event (and, when expected_seq is given, its position in a chain).

    Raises ExperienceError(code). Never returns event content in an error.
    """
    if not isinstance(event, dict):
        raise ExperienceError('schema_invalid', field='event')
    trust = event.get('trust_level')
    if trust == 'T3':
        raise ExperienceError('trust_inflation', field='event.trust_level')
    if trust == 'H':
        raise ExperienceError('h_not_enabled', field='event.trust_level')
    _check_strings(event)  # identical printable-ASCII rule for in-memory and serialized events
    _obj(event, 'event', TOP_REQUIRED, TOP_PROPERTIES)
    type_name = event['type']
    required, properties = DATA_SPECS[type_name]
    _obj(event['data'], 'event.data', required, properties)
    prev = event['prev']
    if prev is not None and (not isinstance(prev, str) or not EVENT_ID.fullmatch(prev)):
        raise ExperienceError('schema_invalid', field='event.prev')
    _check_timestamp(event['recorded_at'])

    methods, wanted_trust, actors, observers, independences = TYPE_RULES[type_name]
    if TRUST_RANK[trust] > TRUST_RANK[METHOD_CEILING[event['method']]]:
        raise ExperienceError('trust_inflation', field='event.trust_level')
    if event['method'] not in methods or trust != wanted_trust:
        raise ExperienceError('trust_inflation' if TRUST_RANK[trust] > TRUST_RANK[wanted_trust] else 'schema_invalid',
                              field='event.method')
    if event['independence'] == 'ci-attested':
        raise ExperienceError('trust_inflation', field='event.independence')
    if (event['actor']['role'] not in actors or event['observer']['role'] not in observers
            or event['independence'] not in independences):
        raise ExperienceError('schema_invalid', field='event.actor')
    subject = event['subject']
    kind = SUBJECT_KIND.get(type_name, 'task')
    if subject['kind'] != kind or (kind == 'task' and 'task_id' not in subject):
        raise ExperienceError('schema_invalid', field='event.subject')
    if kind == 'installation' and 'task_id' in subject:
        raise ExperienceError('schema_invalid', field='event.subject')
    if type_name != 'verify.completed' and event['evidence']:
        raise ExperienceError('schema_invalid', field='event.evidence')
    if type_name == 'verify.completed':
        _check_verify(event)
    if type_name == 'check.operator_run':
        data = event['data']
        if ('tests_failed' in data) != ('tests_total' in data) or (
                'tests_total' in data and data['tests_failed'] > data['tests_total']):
            raise ExperienceError('schema_invalid', field='event.data.tests_total')

    if event['event_id'] != compute_event_id(event):
        raise ExperienceError('id_mismatch', field='event.event_id')
    if expected_seq is not None:
        if event['seq'] != expected_seq or prev != previous_id:
            raise ExperienceError('chain_broken', field='event.seq')
        if run_id is not None and event['run_id'] != run_id:
            raise ExperienceError('chain_broken', field='event.run_id')


def build_event(fields, *, run_id, seq, prev, recorded_at):
    """Assemble an event from caller fields, add identity, and validate it as the next chain entry."""
    event = {'schema': SCHEMA, 'run_id': run_id, 'seq': seq, 'prev': prev, 'recorded_at': recorded_at}
    for key in ('type', 'subject', 'actor', 'observer', 'method', 'trust_level', 'independence', 'environment',
                'evidence', 'data'):
        if key not in fields:
            raise ExperienceError('schema_invalid', field='event.' + key)
        event[key] = fields[key]
    extra = set(fields) - set(event)
    if extra:
        raise ExperienceError('schema_invalid', field='event.unknown-key')
    # Identity is computed after the trust/H/T3 gates so a refused event never needs an id.
    if event['trust_level'] in ('T3', 'H'):
        validate_event(event)
    event['event_id'] = compute_event_id(event)
    validate_event(event, expected_seq=seq, previous_id=prev, run_id=run_id)
    return event


def default_environment():
    """Facts Lite can derive locally. Nothing about the host beyond platform class and versions."""
    from . import __version__
    platform = ('linux' if sys.platform.startswith('linux') else 'macos' if sys.platform == 'darwin'
                else 'windows' if sys.platform.startswith('win') else 'unknown')
    return {'platform': platform, 'lite_version': __version__,
            'python': '%d.%d' % (sys.version_info[0], sys.version_info[1])}


def default_clock():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
