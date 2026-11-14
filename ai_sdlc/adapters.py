"""Provider adapter declarations for AI-SDLC Lite (contract ai-sdlc-adapter/1). Standard library only.

A declaration is DATA. It records what repository evidence says about a coding-agent provider; it never runs a
provider, probes a version, reads credentials or provider configuration, or grants authority. This module is
read-only: it writes nothing, uses no network, imports no subprocess machinery and executes nothing found in a
declaration or in the project it describes.

Capability states:
  SUPPORTED      previously observed, with recorded evidence
  NOT_QUALIFIED  documented or configured, but not exercised
  UNKNOWN        insufficient evidence
  UNSUPPORTED    evidence confirms absence

Declarations are untrusted input: duplicate JSON keys, unknown fields, oversized or symlinked files, evidence paths
that leave the project, unsafe Unicode, and any claim of qualification or execution authority are rejected, and
error messages quote untrusted text only in ASCII-escaped form.
"""

import json
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path

__all__ = ['main', 'ROOT', 'validate_declaration', 'load_vocabulary', 'render_matrix', 'render_matrix_json']

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PARTS = ('adapters', 'adapter-contract.schema.json')
SCHEMA_ID = 'ai-sdlc-adapter/1'
REPORT_SCHEMA = 'ai-sdlc-adapter-report/1'
MATRIX_SCHEMA = 'ai-sdlc-adapter-matrix/1'
SKILL_SOURCE = '.agents/skills/ai-sdlc-lite/SKILL.md'
MAX_BYTES = 65536
MAX_TEXT = 400
MAX_DEPTH = 8
UNSAFE_CATEGORIES = frozenset(('Cc', 'Cf', 'Cs', 'Co', 'Zl', 'Zp', 'Zs'))
VERSION_RE = re.compile(r'^[0-9]+(\.[0-9]+){1,3}$')
USAGE = ('usage: python3 -m ai_sdlc adapter <command>\n'
         '  list                                 provider declarations and their state\n'
         '  validate [--config FILE --project DIR]   validate declarations (all three by default)\n'
         '  matrix [--json]                      capability matrix from the declarations\n')
LEGEND = ('SUPPORTED = previously observed with recorded evidence; NOT_QUALIFIED = documented or configured, not exercised; '
          'UNKNOWN = insufficient evidence; UNSUPPORTED = evidence confirms absence.')
NOTICE = ('Declarations only: no provider was executed or probed, compatibility with an installed version is not claimed, '
          'and a declaration never authorizes execution.')


# ---- safe text, safe files -------------------------------------------------------------------------------------

def _q(value):
    """Quote untrusted text for messages: ASCII-escaped and truncated, so it can never carry terminal controls."""
    return ascii(str(value)[:60])


def _display_safe(text):
    """True if text may be printed: no control, format, surrogate, private-use, separator or replacement characters
    (the plain ASCII space is allowed)."""
    if not isinstance(text, str):
        return False
    for char in text:
        if char == ' ':
            continue
        if char == '�' or unicodedata.category(char) in UNSAFE_CATEGORIES:
            return False
    return True


def _emit(text):
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode('ascii', 'backslashreplace').decode('ascii'))


def _safe_parts(rel):
    """Split a repository-relative path into plain names, or None if it is absolute, traverses, has globs or is unsafe."""
    if not isinstance(rel, str) or not rel or len(rel) > 240 or not _display_safe(rel):
        return None
    if rel[0] == '/' or '\\' in rel or ':' in rel or any(c in rel for c in '*?[]{}~$'):
        return None
    parts = rel.split('/')
    if any(part in ('', '.', '..') for part in parts):
        return None
    return parts


def _regular_file(root, parts):
    """Absolute path of root/parts if every directory is a real directory and the file is a regular, non-symlink file
    whose resolved location stays inside root; otherwise None."""
    try:
        current = Path(root)
        for part in parts[:-1]:
            current = current / part
            if not stat.S_ISDIR(os.lstat(str(current)).st_mode):
                return None
        target = current / parts[-1]
        if not stat.S_ISREG(os.lstat(str(target)).st_mode):
            return None
        real_root, real_target = os.path.realpath(str(root)), os.path.realpath(str(target))
        if os.path.commonpath([real_root, real_target]) != real_root:
            return None
    except (OSError, ValueError):
        return None
    return target


def _read_limited(path):
    """Bytes of a regular file of at most MAX_BYTES, opened without following a final symlink; else None."""
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        fd = os.open(str(path), flags)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return None
            data = os.read(fd, MAX_BYTES + 1)
        finally:
            os.close(fd)
    except (OSError, ValueError):
        return None
    return data if len(data) <= MAX_BYTES else None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def _no_constant(_name):
    raise ValueError('non-finite constant')


def _parse(data):
    """Decode strictly and parse JSON rejecting duplicate keys and NaN/Infinity. Returns (object, error)."""
    try:
        text = data.decode('utf-8')
        value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_no_constant)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None, 'not valid JSON (malformed, duplicate keys, non-finite numbers, bad encoding or too deeply nested)'
    if not isinstance(value, dict):
        return None, 'top-level JSON value must be an object'
    return value, None


def _load_inside(root, rel):
    parts = _safe_parts(rel)
    target = _regular_file(root, parts) if parts else None
    data = _read_limited(target) if target else None
    if data is None:
        return None, 'file is missing, not a regular file, symlinked, outside the project or larger than %d bytes' % MAX_BYTES
    return _parse(data)


def _load_config(config, project):
    """Load a declaration given by the user: contained below project (components checked) or a plain outside file."""
    path = Path(os.path.abspath(str(config)))
    root = Path(os.path.abspath(str(project)))
    try:
        rel = path.relative_to(root)
    except ValueError:
        try:
            if not stat.S_ISREG(os.lstat(str(path)).st_mode):
                return None, 'config is not a regular file'
        except OSError:
            return None, 'config file not found'
        data = _read_limited(path)
        if data is None:
            return None, 'config is symlinked, unreadable or larger than %d bytes' % MAX_BYTES
        return _parse(data)
    return _load_inside(root, '/'.join(rel.parts))


def _walk_text(value, label, errors, depth=0):
    """Every key and string anywhere in the declaration must be display-safe and bounded; nesting is bounded."""
    if depth > MAX_DEPTH:
        errors.append('declaration is nested too deeply')
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 80 or not _display_safe(key):
                errors.append('a field name is unsafe or too long: %s' % _q(key))
            else:
                _walk_text(item, label, errors, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _walk_text(item, label, errors, depth + 1)
    elif isinstance(value, str):
        if len(value) > MAX_TEXT or not _display_safe(value):
            errors.append('unsafe or oversized text value: %s' % _q(value))


# ---- vocabulary and validation ----------------------------------------------------------------------------------

def load_vocabulary():
    """(vocabulary, error) from the framework's own schema file (single source of the allowed names)."""
    schema, error = _load_inside(ROOT, '/'.join(SCHEMA_PARTS))
    if error:
        return None, 'adapter contract schema unreadable: ' + error
    vocab = schema.get('x-vocabulary') if schema.get('$id') == SCHEMA_ID else None
    keys = ('providers', 'statuses', 'bases', 'platforms', 'capabilities')
    if not isinstance(vocab, dict) or set(vocab) != set(keys):
        return None, 'adapter contract schema has no valid x-vocabulary'
    for key in keys:
        names = vocab[key]
        if (not isinstance(names, list) or not names or len(set(names)) != len(names)
                or not all(isinstance(n, str) and n and _display_safe(n) and ' ' not in n for n in names)):
            return None, 'adapter contract vocabulary is malformed'
    return vocab, None


def _object(value, label, required, errors):
    if not isinstance(value, dict):
        errors.append('%s must be an object' % label)
        return False
    for key in sorted(k for k in value if k not in required):
        errors.append('%s has an unknown field %s' % (label, _q(key)))
    for key in required:
        if key not in value:
            errors.append('%s is missing field %s' % (label, key))
    return all(key in value for key in required) and set(value) == set(required)


def _text(value, label, errors, limit=MAX_TEXT):
    if not isinstance(value, str) or not value or len(value) > limit or not _display_safe(value):
        errors.append('%s must be non-empty display-safe text of at most %d characters' % (label, limit))
        return False
    return True


def _existing_files(root, refs, label, errors, nonempty=False, maximum=5):
    if not isinstance(refs, list) or len(refs) > maximum or len(set(map(str, refs))) != len(refs):
        errors.append('%s must be a list of at most %d unique paths' % (label, maximum))
        return
    for ref in refs:
        parts = _safe_parts(ref)
        target = _regular_file(root, parts) if parts else None
        if target is None:
            errors.append('%s: %s is not a contained regular file in the project' % (label, _q(ref)))
        elif nonempty and os.lstat(str(target)).st_size == 0:
            errors.append('%s: %s is empty' % (label, _q(ref)))


def _check_capability(root, name, entry, vocab, errors):
    label = 'capability ' + name
    if not _object(entry, label, ('status', 'basis', 'evidence', 'note'), errors):
        return None
    status, basis, evidence = entry['status'], entry['basis'], entry['evidence']
    if status not in vocab['statuses'] or not isinstance(status, str):
        errors.append('%s has an invalid status %s' % (label, _q(status)))
        return None
    if not isinstance(basis, str) or basis not in vocab['bases']:
        errors.append('%s has an invalid basis %s' % (label, _q(basis)))
        return None
    _text(entry['note'], label + ' note', errors, 240)
    _existing_files(root, evidence, label + ' evidence', errors)
    count = len(evidence) if isinstance(evidence, list) else 0
    if status == 'SUPPORTED' and not (basis == 'observed' and count):
        errors.append('%s: SUPPORTED requires basis observed and recorded evidence' % label)
    elif status == 'NOT_QUALIFIED' and not (basis in ('documented', 'configuration') and count):
        errors.append('%s: NOT_QUALIFIED requires basis documented or configuration and recorded evidence' % label)
    elif status == 'UNKNOWN' and (basis != 'none' or count):
        errors.append('%s: UNKNOWN requires basis none and no evidence' % label)
    elif status == 'UNSUPPORTED' and not (basis in ('observed', 'documented') and count):
        errors.append('%s: UNSUPPORTED requires basis observed or documented and recorded evidence' % label)
    return status


def validate_data(data, project_root, vocab):
    """Validate a parsed declaration against the contract. Returns (errors, provider, status_by_capability)."""
    errors = []
    _walk_text(data, 'declaration', errors)
    required = ('schema', 'provider', 'provider_version', 'platforms_observed', 'instruction_files', 'skill',
                'capabilities', 'qualification', 'limitations', 'execution_authorized')
    _object(data, 'declaration', required, errors)
    provider, statuses = None, {}
    if data.get('schema') != SCHEMA_ID:
        errors.append('schema must be %s' % SCHEMA_ID)
    value = data.get('provider')
    if isinstance(value, str) and value in vocab['providers']:
        provider = value
    else:
        errors.append('provider must be one of: ' + ', '.join(vocab['providers']))
    version = data.get('provider_version')
    if _object(version, 'provider_version', ('observed', 'compatibility_claim'), errors):
        observed = version['observed']
        if observed is not None and not (isinstance(observed, str) and VERSION_RE.match(observed)):
            errors.append('provider_version.observed must be null or a numeric version such as 1.2.3')
        if version['compatibility_claim'] != 'none':
            errors.append('provider_version.compatibility_claim must be "none": no compatibility is claimed')
    platforms = data.get('platforms_observed')
    if (not isinstance(platforms, list) or len(set(map(str, platforms))) != len(platforms)
            or not all(isinstance(p, str) and p in vocab['platforms'] for p in platforms)):
        errors.append('platforms_observed must be a list of unique values from: ' + ', '.join(vocab['platforms']))
    instruction_files = data.get('instruction_files')
    _existing_files(project_root, instruction_files, 'instruction_files', errors, nonempty=True)
    skill = data.get('skill')
    if _object(skill, 'skill', ('source_path',), errors):
        if skill['source_path'] != SKILL_SOURCE:
            errors.append('skill.source_path must be %s' % SKILL_SOURCE)
        else:
            _existing_files(project_root, [SKILL_SOURCE], 'skill.source_path', errors, nonempty=True)
    capabilities = data.get('capabilities')
    if isinstance(capabilities, dict):
        for name in sorted(k for k in capabilities if k not in vocab['capabilities']):
            errors.append('unknown capability %s' % _q(name))
        for name in vocab['capabilities']:
            if name not in capabilities:
                errors.append('missing capability %s' % name)
            else:
                status = _check_capability(project_root, name, capabilities[name], vocab, errors)
                if status:
                    statuses[name] = status
    else:
        errors.append('capabilities must be an object')
    if isinstance(instruction_files, list) and 'instruction_file' in statuses:
        declared = statuses['instruction_file'] in ('SUPPORTED', 'NOT_QUALIFIED')
        if bool(instruction_files) != declared:
            errors.append('instruction_files must be non-empty exactly when instruction_file is SUPPORTED or NOT_QUALIFIED')
    qualification = data.get('qualification')
    if _object(qualification, 'qualification', ('smoke', 'deep'), errors):
        if qualification['smoke'] != 'NOT_RUN' or qualification['deep'] != 'NOT_RUN':
            errors.append('qualification.smoke and qualification.deep must be NOT_RUN: a declaration cannot qualify a provider')
    limitations = data.get('limitations')
    if not isinstance(limitations, list) or not 1 <= len(limitations) <= 10:
        errors.append('limitations must be a list of 1 to 10 statements')
    else:
        for item in limitations:
            _text(item, 'a limitation', errors, 300)
    if data.get('execution_authorized') is not False:
        errors.append('execution_authorized must be false: a declaration never authorizes execution')
    return errors, provider, statuses


def _new_report():
    return {'schema': REPORT_SCHEMA, 'provider': None, 'state': 'INVALID', 'execution_authorized': False,
            'provider_executed': False, 'version_probed': False, 'effective_permissions_verified': False,
            'qualification': {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'}, 'errors': []}


def validate_declaration(config, project=None, vocab=None):
    """Validate one declaration file. Returns (report, data_or_None). Never executes anything."""
    report = _new_report()
    project = ROOT if project is None else project
    if vocab is None:
        vocab, error = load_vocabulary()
        if error:
            report['errors'].append(error)
            return report, None
    data, error = _load_config(config, project)
    if error:
        report['errors'].append('declaration: ' + error)
        return report, None
    errors, provider, statuses = validate_data(data, Path(os.path.abspath(str(project))), vocab)
    report['provider'] = provider
    report['errors'] = errors
    if not errors:
        report['state'] = 'ADAPTER_DECLARATION_VALID'
        report['status_counts'] = {name: sum(1 for s in statuses.values() if s == name) for name in vocab['statuses']}
        return report, data
    return report, None


def default_declaration(provider):
    return 'adapters/agents/%s/provider-adapter.json' % provider


def load_defaults(vocab):
    """Validate the three shipped declarations. Returns {provider: (report, data_or_None)} in vocabulary order."""
    results = {}
    for provider in vocab['providers']:
        report, data = validate_declaration(ROOT / default_declaration(provider), ROOT, vocab)
        if data is not None and report['provider'] != provider:
            report['errors'].append('declaration provider does not match its directory')
            report['state'], data = 'INVALID', None
        results[provider] = (report, data)
    return results


# ---- rendering ---------------------------------------------------------------------------------------------------

def render_matrix(vocab, results):
    columns = vocab['providers']
    rows = [['capability'] + columns]
    for name in vocab['capabilities']:
        rows.append([name] + [results[p][1]['capabilities'][name]['status'] for p in columns])
    rows.append(['observed version'] + [results[p][1]['provider_version']['observed'] or 'none' for p in columns])
    rows.append(['smoke / deep'] + ['%s / %s' % (results[p][1]['qualification']['smoke'],
                                                 results[p][1]['qualification']['deep']) for p in columns])
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = ['AI-SDLC Lite provider adapter matrix (ai-sdlc-adapter/1)']
    for row in rows:
        lines.append('  '.join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    lines += ['', LEGEND, NOTICE]
    return '\n'.join(lines) + '\n'


def render_matrix_json(vocab, results):
    providers = {}
    for provider in vocab['providers']:
        data = results[provider][1]
        providers[provider] = {
            'declaration': default_declaration(provider),
            'observed_version': data['provider_version']['observed'],
            'platforms_observed': list(data['platforms_observed']),
            'capabilities': {name: data['capabilities'][name]['status'] for name in vocab['capabilities']},
            'qualification': dict(data['qualification']),
        }
    document = {'schema': MATRIX_SCHEMA, 'statuses': list(vocab['statuses']), 'capabilities': list(vocab['capabilities']),
                'providers': providers, 'execution_authorized': False, 'version_probed': False, 'notice': NOTICE}
    return json.dumps(document, indent=2, ensure_ascii=True) + '\n'


def _counts_text(report):
    counts = report.get('status_counts', {})
    return ' '.join('%s=%d' % (name, counts[name]) for name in counts)


# ---- command line ------------------------------------------------------------------------------------------------

def _usage_error(message=None):
    if message:
        sys.stderr.write('ai_sdlc adapter: %s\n' % message)
    sys.stderr.write(USAGE)
    return 2


def _cmd_list(vocab):
    results = load_defaults(vocab)
    lines = []
    for provider, (report, data) in results.items():
        version = data['provider_version']['observed'] or 'none' if data else 'n/a'
        lines.append('%s: %s; observed version %s; %s' % (provider, report['state'], version, _counts_text(report) or 'no counts'))
    ok = all(report['state'] == 'ADAPTER_DECLARATION_VALID' for report, _ in results.values())
    lines.append('RESULT: ' + ('VALID' if ok else 'INVALID') + ' (declaration checks only; no provider was executed or probed)')
    _emit('\n'.join(lines) + '\n')
    return 0 if ok else 2


def _cmd_validate(vocab, args):
    config = project = None
    rest = list(args)
    while rest:
        flag = rest.pop(0)
        if flag in ('--config', '--project') and rest:
            value = rest.pop(0)
            if flag == '--config' and config is None:
                config = value
            elif flag == '--project' and project is None:
                project = value
            else:
                return _usage_error('a flag was given twice')
        else:
            return _usage_error('unknown or incomplete argument %s' % _q(flag))
    if (config is None) != (project is None):
        return _usage_error('--config and --project must be given together')
    if config is not None:
        items = [('config', validate_declaration(config, project, vocab)[0])]
    else:
        items = [(provider, report) for provider, (report, _) in load_defaults(vocab).items()]
    lines, ok = [], True
    for name, report in items:
        label = report['provider'] or name
        lines.append('%s: %s%s' % (label, report['state'], (' (' + _counts_text(report) + ')') if report['state'] != 'INVALID' else ''))
        for error in report['errors']:
            lines.append('  error: ' + error)
        ok = ok and report['state'] == 'ADAPTER_DECLARATION_VALID'
    lines.append('RESULT: ' + ('VALID' if ok else 'INVALID') + ' (declaration checks only; no provider was executed or probed; '
                 'execution_authorized stays false)')
    _emit('\n'.join(lines) + '\n')
    return 0 if ok else 2


def _cmd_matrix(vocab, args):
    if args not in ([], ['--json']):
        return _usage_error('matrix accepts only --json')
    results = load_defaults(vocab)
    bad = [p for p, (report, _) in results.items() if report['state'] != 'ADAPTER_DECLARATION_VALID']
    if bad:
        sys.stderr.write('ai_sdlc adapter: BLOCKED: invalid declaration(s): %s; run "adapter validate" for details.\n' % ', '.join(bad))
        return 2
    _emit(render_matrix_json(vocab, results) if args else render_matrix(vocab, results))
    return 0


def main(argv):
    args = list(argv)
    if not args:
        return _usage_error()
    if args[0] in ('-h', '--help', 'help'):
        sys.stdout.write(USAGE)
        return 0
    command, rest = args[0], args[1:]
    if command not in ('list', 'validate', 'matrix'):
        return _usage_error('unknown command %s' % _q(command))
    if command == 'list' and rest:
        return _usage_error('list takes no arguments')
    vocab, error = load_vocabulary()
    if error:
        sys.stderr.write('ai_sdlc adapter: BLOCKED: %s\n' % error)
        return 2
    if command == 'list':
        return _cmd_list(vocab)
    if command == 'validate':
        return _cmd_validate(vocab, rest)
    return _cmd_matrix(vocab, rest)
