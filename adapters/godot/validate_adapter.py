#!/usr/bin/env python3
"""Godot adapter configuration validator for AI-SDLC Lite (stdlib only, read-only).

Reads a declarative adapter configuration (`ai-sdlc-godot-adapter/1`) and a Godot project directory, and reports
whether the CONFIGURATION is consistent and safe to declare. It is configuration-level evidence only:

  * It NEVER executes anything: no subprocess, no Godot, no runner script, no shell. It imports neither `subprocess`
    nor any process-spawning API (a test enforces this), and it writes no files.
  * Command declarations are DATA, not authorization. `execution_authorized` is always false in the report; any
    approval is a recorded human decision that this tool neither grants nor acts on.
  * A path or isolation declaration is NOT proof of OS-level isolation. That needs runtime qualification (Q7).
  * The best state it can report is ADAPTER_READY. It never reports RUNTIME_QUALIFIED or DEVELOPMENT_QUALIFIED.

The universal core (scripts/verify_scope.py) is not imported or modified. `--emit-contract-fields` prints values a task
author can paste into a result contract.

Exit codes: 0 ADAPTER_READY (warnings allowed), 2 NOT_READY (any error, or any unexpected failure: fail closed).
"""

import argparse
import json
import re
import sys
from pathlib import Path

CONFIG_SCHEMA = 'ai-sdlc-godot-adapter/1'
REPORT_SCHEMA = 'ai-sdlc-godot-adapter-report/1'
MAX_BYTES = 1 << 20
PROJECT_GODOT = 'project.godot'
DEFAULT_PROTECTED = ('project.godot', 'export_presets.cfg')       # project configuration; changeable only explicitly
ROLES = ('import', 'test', 'gui')
GENERATED_POLICIES = ('ignored', 'tracked', 'project-decides')
ISOLATION_PROFILES = ('private-home-xdg', 'project-managed')
USER_DATA_LOCATIONS = ('linux-xdg-data', 'linux-xdg-config', 'linux-xdg-cache', 'macos-app-support', 'windows-appdata')
EVIDENCE_KINDS = ('exit_code', 'output_log', 'result_line')
STATES = ('ADAPTER_READY', 'NOT_READY')

# Stable finding codes: code -> (level, meaning). Documented in adapters/godot/README.md and checked by tests.
FINDING_CODES = {
    'validation_error': ('ERROR', 'unexpected failure while validating (fail closed)'),
    'config_unreadable': ('ERROR', 'configuration file missing, a symlink, too large or not valid UTF-8'),
    'config_not_json': ('ERROR', 'configuration is not a JSON object'),
    'config_schema_invalid': ('ERROR', 'schema id is not ai-sdlc-godot-adapter/1'),
    'config_unknown_key': ('ERROR', 'unknown key (typos and self-asserted qualification are refused)'),
    'config_field_missing': ('ERROR', 'a required field is missing'),
    'config_type_invalid': ('ERROR', 'a field has the wrong type or value'),
    'unsafe_path': ('ERROR', 'path or glob is absolute, traverses upward, uses a scheme, drive, variable or backslash'),
    'project_root_invalid': ('ERROR', 'project root or working directory is missing, outside the project, or a symlink'),
    'project_godot_missing': ('ERROR', 'project.godot is missing, not a regular file, or a symlink'),
    'project_godot_malformed': ('ERROR', 'project.godot is unreadable or has no config_version'),
    'godot_version_constraint_invalid': ('ERROR', 'the version constraint is malformed or empty'),
    'godot_version_unsupported': ('ERROR', 'the project targets a Godot version outside the constraint'),
    'godot_version_unknown': ('WARNING', 'project.godot declares no engine version; the constraint was not checked'),
    'runner_kind_unsupported': ('ERROR', 'only project-owned wrappers are supported, never a global Godot executable'),
    'runner_missing': ('ERROR', 'a declared runner file does not exist as a regular file'),
    'runner_unsafe': ('ERROR', 'a runner path is bare, absolute, outside the project or reached through a symlink'),
    'runner_isolation_unasserted': ('ERROR', 'a runner used by a command does not assert that it isolates user data'),
    'runner_not_approved': ('WARNING', 'a runner is declared but not approved; declarations never authorize execution'),
    'unknown_runner': ('ERROR', 'a command references a runner that is not declared'),
    'duplicate_id': ('ERROR', 'a runner or command id is repeated'),
    'command_invalid': ('ERROR', 'a command declaration is malformed'),
    'user_data_reference': ('ERROR', 'a command argument references user:// or a real user-data location'),
    'protected_path_conflict': ('ERROR', 'an allowed or written path lies inside a protected path'),
    'project_config_unprotected': ('ERROR', 'project configuration is neither protected nor explicitly allowed'),
    'unscoped_write': ('ERROR', 'a command declares a write that no generated, ignorable or allowed path covers'),
    'generated_not_ignored': ('WARNING', "policy 'ignored' but the project's .gitignore does not mention .godot"),
    'isolation_not_required': ('ERROR', 'isolation must be required and the workspace disposable'),
    'evidence_inside_repository': ('ERROR', 'evidence must be stored outside the repository'),
    'evidence_incomplete': ('ERROR', 'evidence must at least require exit_code and output_log'),
    'execution_not_authorized': ('WARNING', 'no execution approval is recorded; nothing may be run'),
}

GATES = {   # configuration-level states only; runtime and gameplay gates are never marked PASS here
    'Q1': 'project detection',
    'Q2': 'configuration validation',
    'Q3': 'approved runner compatibility',
    'Q4': 'safe import in disposable workspace',
    'Q5': 'headless test execution',
    'Q6': 'scope enforcement',
    'Q7': 'save and profile isolation',
    'Q8': 'failure and interrupted-run reporting',
    'Q9': 'evidence integrity and result verification',
    'Q10': 'functional gameplay and GUI acceptance',
}

TOP_KEYS = {'schema', 'project', 'godot', 'runners', 'commands', 'paths', 'generated', 'isolation', 'evidence', 'approvals'}
SECTION_KEYS = {
    'project': {'root', 'working_directory', 'detect'},
    'godot': {'min_version', 'max_version_exclusive'},
    'runner': {'id', 'kind', 'path', 'approved', 'isolation_by_runner'},
    'command': {'id', 'role', 'runner', 'args', 'timeout_seconds', 'writes', 'optional', 'requires_display'},
    'paths': {'protected', 'allowed', 'sensitive_allowed', 'generated', 'ignorable'},
    'generated': {'policy'},
    'isolation': {'required', 'profile', 'disposable_workspace', 'protected_user_data'},
    'evidence': {'required', 'store', 'result_line_pattern'},
    'approvals': {'execution_approved_by', 'approved_revision'},
}


class Findings:
    def __init__(self):
        self.items = []

    def add(self, code, detail):
        if code not in FINDING_CODES:
            raise RuntimeError(f'unregistered finding code {code}')
        self.items.append({'level': FINDING_CODES[code][0], 'code': code, 'detail': detail})

    def errors(self):
        return [f for f in self.items if f['level'] == 'ERROR']


def check_pattern(value, label, findings, allow_dot=False):
    """A repository-relative path or glob. Returns True when safe."""
    ok = (isinstance(value, str) and value and len(value) <= 512 and '\0' not in value and '\\' not in value
          and not value.startswith(('/', '~', './')) and '://' not in value and ':' not in value
          and '$' not in value and '%' not in value and '..' not in value.split('/') and '' not in value.split('/')[:-1])
    if ok and value == '.' and not allow_dot:
        ok = False
    if not ok:
        findings.add('unsafe_path', f'{label}: {value!r}')
    return ok


def expect(obj, key, kind, label, findings, required=True):
    if key not in obj:
        if required:
            findings.add('config_field_missing', f'{label}.{key}')
        return None
    value = obj[key]
    if kind is bool and isinstance(value, bool) or kind is not bool and isinstance(value, kind) and not isinstance(value, bool):
        return value
    findings.add('config_type_invalid', f'{label}.{key} must be {kind.__name__}')
    return None


def strict_keys(obj, allowed, label, findings):
    for key in sorted(set(obj) - allowed):
        findings.add('config_unknown_key', f'{label}.{key}')


def string_list(obj, key, label, findings, required=True, path=False):
    value = expect(obj, key, list, label, findings, required)
    if value is None:
        return []
    good = []
    for item in value:
        if not isinstance(item, str) or not item:
            findings.add('config_type_invalid', f'{label}.{key} must contain non-empty strings')
        elif not path or check_pattern(item, f'{label}.{key}', findings):
            good.append(item)
    return good


def literal_prefix(pattern):
    cut = len(pattern)
    for char in '*?[':
        if char in pattern:
            cut = min(cut, pattern.index(char))
    return pattern[:cut]


def glob_regex(pattern):
    if pattern.endswith('/'):
        pattern += '**'
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith('**/', i):
            out.append('(?:.*/)?')
            i += 3
        elif pattern.startswith('**', i):
            out.append('.*')
            i += 2
        elif pattern[i] == '*':
            out.append('[^/]*')
            i += 1
        elif pattern[i] == '?':
            out.append('[^/]')
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile(''.join(out) + r'\Z')


def covered(pattern, by):
    """Conservative: a write is covered when a sample path under its literal prefix matches a covering pattern."""
    sample = literal_prefix(pattern) + 'x'
    return any(glob_regex(c).match(sample) for c in by)


def inside(inner, outer):
    """True when the literal prefix of `inner` lies within (or equals) the literal prefix of `outer`."""
    a, b = literal_prefix(inner), literal_prefix(outer)
    return a.startswith(b) if b else False


def overlaps(a, b):
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def no_symlink(base, path):
    current = path
    while current != base and base in current.parents:
        if current.is_symlink():
            return False
        current = current.parent
    return not path.is_symlink()


def parse_version(text):
    found = re.fullmatch(r'(\d+)\.(\d+)(?:\.(\d+))?', text) if isinstance(text, str) else None
    return tuple(int(x or 0) for x in found.groups()) if found else None


def read_project_godot(project, findings):
    path = project / PROJECT_GODOT
    if path.is_symlink() or not path.is_file():
        findings.add('project_godot_missing', f'{PROJECT_GODOT} is not a regular file in the project root')
        return None
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('too large')
        text = path.read_text('utf-8')
    except (OSError, ValueError):
        findings.add('project_godot_malformed', f'{PROJECT_GODOT} is unreadable, too large or not UTF-8')
        return None
    if not re.search(r'^config_version\s*=\s*\d+\s*$', text, re.M):
        findings.add('project_godot_malformed', f'{PROJECT_GODOT} has no config_version line')
        return None
    features = re.search(r'^config/features\s*=\s*PackedStringArray\((.*)\)\s*$', text, re.M)
    version = None
    if features:
        for item in re.findall(r'"([^"]*)"', features.group(1)):
            if parse_version(item):
                version = parse_version(item)
                break
    return {'engine_version': version}


def validate(config_path, project_dir):
    findings = Findings()
    report = {'schema': REPORT_SCHEMA, 'adapter_state': 'NOT_READY', 'execution_authorized': False,
              'approval_recorded': False, 'isolation_proof': 'none: a declaration is not OS-level isolation (gate Q7)',
              'findings': findings.items, 'gates': {}, 'limitations': [
                  'Configuration-level evidence only: nothing was executed, imported, run or tested.',
                  'Command and runner declarations are data, not authorization.',
                  'Path and isolation declarations are not proof of isolation or of enforcement.']}
    try:
        _validate(Path(config_path), Path(project_dir), findings, report)
    except Exception as error:   # fail closed
        findings.add('validation_error', f'{type(error).__name__}: {error}')
    ready = not findings.errors()
    report['adapter_state'] = 'ADAPTER_READY' if ready else 'NOT_READY'
    report['gates'] = gates(findings, report, ready)
    if not ready:
        report.pop('contract_fields', None)
    return report


def gates(findings, report, ready):
    bad = {f['code'] for f in findings.errors()}
    q1 = bool(report.get('_q1')) and not bad & {'project_godot_missing', 'project_godot_malformed', 'project_root_invalid',
                                                'godot_version_unsupported'}
    report.pop('_q1', None)
    result = {gate: 'NOT_RUN' for gate in GATES}
    result['Q1'] = 'PASS' if q1 else 'FAIL'
    result['Q2'] = 'PASS' if ready else 'FAIL'
    if ready:
        result.update({'Q3': 'DECLARED', 'Q6': 'DECLARED', 'Q7': 'DECLARED', 'Q9': 'DECLARED'})
    return result


def _validate(config_path, project_dir, findings, report):
    if config_path.is_symlink() or not config_path.is_file() or config_path.stat().st_size > MAX_BYTES:
        findings.add('config_unreadable', 'configuration file missing, a symlink or too large')
        return
    try:
        config = json.loads(config_path.read_text('utf-8'))
    except (OSError, ValueError):
        findings.add('config_unreadable', 'configuration is not readable UTF-8 JSON')
        return
    if not isinstance(config, dict):
        findings.add('config_not_json', 'top level must be a JSON object')
        return
    if config.get('schema') != CONFIG_SCHEMA:
        findings.add('config_schema_invalid', f'schema must be {CONFIG_SCHEMA}')
        return
    strict_keys(config, TOP_KEYS, 'config', findings)
    if not project_dir.is_dir():
        findings.add('project_root_invalid', 'project directory does not exist')
        return
    project_dir = project_dir.resolve()

    # ---- project
    section = expect(config, 'project', dict, 'project', findings) or {}
    strict_keys(section, SECTION_KEYS['project'], 'project', findings)
    root_value = expect(section, 'root', str, 'project', findings)
    workdir_value = expect(section, 'working_directory', str, 'project', findings)
    if section.get('detect') != PROJECT_GODOT:
        findings.add('config_type_invalid', f'project.detect must be {PROJECT_GODOT!r}')
    project = None
    for label, value in (('project.root', root_value), ('project.working_directory', workdir_value)):
        if value is None:
            continue
        if value != '.' and not check_pattern(value, label, findings):
            continue
        candidate = (project_dir / value).resolve() if label == 'project.root' else None
        if label == 'project.root':
            if project_dir != candidate and project_dir not in candidate.parents or not candidate.is_dir() \
                    or not no_symlink(project_dir, project_dir / value):
                findings.add('project_root_invalid', f'{label} {value!r} is outside, missing or reached through a symlink')
            else:
                project = candidate
    if project is not None:
        if workdir_value not in (None, '.'):
            target = project / workdir_value
            if not target.is_dir() or not no_symlink(project, target):
                findings.add('project_root_invalid', f'working_directory {workdir_value!r} is missing or a symlink')
        meta = read_project_godot(project, findings)
        report['_q1'] = meta is not None
        report['project'] = {'root': root_value, 'working_directory': workdir_value}
    else:
        meta = None

    # ---- godot version
    godot = expect(config, 'godot', dict, 'godot', findings) or {}
    strict_keys(godot, SECTION_KEYS['godot'], 'godot', findings)
    low = parse_version(godot.get('min_version')) if 'min_version' in godot else None
    high = parse_version(godot.get('max_version_exclusive')) if godot.get('max_version_exclusive') is not None else None
    if low is None or ('max_version_exclusive' in godot and high is None) or (low and high and low >= high):
        findings.add('godot_version_constraint_invalid', 'min_version (X.Y[.Z]) is required; max_version_exclusive must be greater')
    elif meta is not None:
        engine = meta['engine_version']
        if engine is None:
            findings.add('godot_version_unknown', 'project.godot config/features has no version')
        elif engine < low or (high and engine >= high):
            findings.add('godot_version_unsupported', f'project targets {".".join(map(str, engine))}, outside the constraint')

    # ---- paths
    paths = expect(config, 'paths', dict, 'paths', findings) or {}
    strict_keys(paths, SECTION_KEYS['paths'], 'paths', findings)
    protected = string_list(paths, 'protected', 'paths', findings, path=True)
    allowed = string_list(paths, 'allowed', 'paths', findings, path=True)
    sensitive = string_list(paths, 'sensitive_allowed', 'paths', findings, required=False, path=True)
    generated = string_list(paths, 'generated', 'paths', findings, path=True)
    ignorable = string_list(paths, 'ignorable', 'paths', findings, required=False, path=True)
    for default in DEFAULT_PROTECTED:
        if default not in protected and default not in sensitive:
            findings.add('project_config_unprotected', f'{default} must be protected or listed in sensitive_allowed')
    for path in allowed:
        for guard in protected:
            if inside(path, guard) and not any(path == s for s in sensitive):
                findings.add('protected_path_conflict', f'allowed {path!r} lies inside protected {guard!r}')
    gen = expect(config, 'generated', dict, 'generated', findings) or {}
    strict_keys(gen, SECTION_KEYS['generated'], 'generated', findings)
    if gen.get('policy') not in GENERATED_POLICIES:
        findings.add('config_type_invalid', f'generated.policy must be one of {GENERATED_POLICIES}')
    elif gen['policy'] == 'ignored' and project is not None:
        ignore = project / '.gitignore'
        text = ignore.read_text('utf-8', 'replace') if ignore.is_file() and not ignore.is_symlink() else ''
        if '.godot' not in text:
            findings.add('generated_not_ignored', ".gitignore does not mention .godot (policy 'ignored')")

    # ---- runners
    runners, runner_ids = {}, set()
    for index, runner in enumerate(expect(config, 'runners', list, 'runners', findings) or []):
        label = f'runners[{index}]'
        if not isinstance(runner, dict):
            findings.add('config_type_invalid', f'{label} must be an object')
            continue
        strict_keys(runner, SECTION_KEYS['runner'], label, findings)
        rid = expect(runner, 'id', str, label, findings)
        if rid in runner_ids:
            findings.add('duplicate_id', f'runner id {rid!r}')
        runner_ids.add(rid)
        if runner.get('kind') != 'project-wrapper':
            findings.add('runner_kind_unsupported', f'{label}.kind must be "project-wrapper"')
        path = expect(runner, 'path', str, label, findings)
        approved = expect(runner, 'approved', bool, label, findings)
        isolated = expect(runner, 'isolation_by_runner', bool, label, findings)
        if path is not None:
            if '/' not in path or not check_pattern(path, f'{label}.path', findings) or any(c in path for c in '*?['):
                findings.add('runner_unsafe', f'{label}.path must be a project-relative file path containing a directory, not a bare or global executable')
            elif project is not None:
                target = project / path
                if not no_symlink(project, target) or (project != target.resolve() and project not in target.resolve().parents):
                    findings.add('runner_unsafe', f'{label}.path is a symlink or leaves the project')
                elif not target.is_file():
                    findings.add('runner_missing', f'{label}.path {path!r} does not exist as a regular file (it is never executed)')
        if approved is False:
            findings.add('runner_not_approved', f'runner {rid!r} is declared but not approved')
        runners[rid] = {'approved': approved, 'isolated': isolated}
    report['approval_recorded'] = False

    # ---- commands
    seen = set()
    writes_all = []
    for index, command in enumerate(expect(config, 'commands', list, 'commands', findings) or []):
        label = f'commands[{index}]'
        if not isinstance(command, dict):
            findings.add('config_type_invalid', f'{label} must be an object')
            continue
        strict_keys(command, SECTION_KEYS['command'], label, findings)
        cid = expect(command, 'id', str, label, findings)
        if cid in seen:
            findings.add('duplicate_id', f'command id {cid!r}')
        seen.add(cid)
        if command.get('role') not in ROLES:
            findings.add('command_invalid', f'{label}.role must be one of {ROLES}')
        if command.get('runner') not in runners:
            findings.add('unknown_runner', f'{label}.runner {command.get("runner")!r} is not declared')
        elif not runners[command['runner']]['isolated']:
            findings.add('runner_isolation_unasserted', f'{label}: runner {command["runner"]!r} must set isolation_by_runner true')
        timeout = command.get('timeout_seconds')
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            findings.add('command_invalid', f'{label}.timeout_seconds must be an integer from 1 to 3600')
        if command.get('role') == 'gui' and command.get('requires_display') is not True:
            findings.add('command_invalid', f'{label}: gui commands must set requires_display true')
        for key in ('optional', 'requires_display'):
            if key in command and not isinstance(command[key], bool):
                findings.add('config_type_invalid', f'{label}.{key} must be boolean')
        args = expect(command, 'args', list, label, findings)
        for arg in args or []:
            if not isinstance(arg, str) or '\0' in arg or '\n' in arg or len(arg) > 512:
                findings.add('command_invalid', f'{label}.args must be single-line strings')
            elif 'user://' in arg or re.search(r'(\.local/share/godot|\.config/godot|\.cache/godot|Application Support/Godot|AppData)', arg):
                findings.add('user_data_reference', f'{label}.args {arg!r} references user data')
            elif arg.startswith(('/', '~')) or '..' in arg.split('/') or '\\' in arg or '$' in arg:
                findings.add('unsafe_path', f'{label}.args {arg!r} is absolute, traverses upward or expands a variable')
        for write in string_list(command, 'writes', label, findings, path=True):
            writes_all.append((label, write))
    cover = generated + ignorable + allowed
    for label, write in writes_all:
        if any(overlaps(write, guard) for guard in protected if guard not in sensitive):
            findings.add('protected_path_conflict', f'{label} writes {write!r}, which overlaps a protected path')
        elif not covered(write, cover):
            findings.add('unscoped_write', f'{label} writes {write!r}, not covered by generated, ignorable or allowed paths')

    # ---- isolation, evidence, approvals
    isolation = expect(config, 'isolation', dict, 'isolation', findings) or {}
    strict_keys(isolation, SECTION_KEYS['isolation'], 'isolation', findings)
    if isolation.get('required') is not True or isolation.get('disposable_workspace') is not True:
        findings.add('isolation_not_required', 'isolation.required and isolation.disposable_workspace must be true')
    if isolation.get('profile') not in ISOLATION_PROFILES:
        findings.add('config_type_invalid', f'isolation.profile must be one of {ISOLATION_PROFILES}')
    for item in string_list(isolation, 'protected_user_data', 'isolation', findings):
        if item not in USER_DATA_LOCATIONS:
            findings.add('config_type_invalid', f'isolation.protected_user_data entry {item!r} is not one of {USER_DATA_LOCATIONS}')
    evidence = expect(config, 'evidence', dict, 'evidence', findings) or {}
    strict_keys(evidence, SECTION_KEYS['evidence'], 'evidence', findings)
    if evidence.get('store') != 'outside-repository':
        findings.add('evidence_inside_repository', 'evidence.store must be "outside-repository"')
    kinds = string_list(evidence, 'required', 'evidence', findings)
    if not {'exit_code', 'output_log'} <= set(kinds) or not set(kinds) <= set(EVIDENCE_KINDS):
        findings.add('evidence_incomplete', f'evidence.required must include exit_code and output_log and only use {EVIDENCE_KINDS}')
    pattern = evidence.get('result_line_pattern')
    if pattern is not None:
        try:
            if not isinstance(pattern, str) or len(pattern) > 200:
                raise ValueError
            re.compile(pattern)
        except (ValueError, re.error):
            findings.add('config_type_invalid', 'evidence.result_line_pattern must be a valid regular expression of at most 200 characters')
    approvals = expect(config, 'approvals', dict, 'approvals', findings) or {}
    strict_keys(approvals, SECTION_KEYS['approvals'], 'approvals', findings)
    who, rev = approvals.get('execution_approved_by'), approvals.get('approved_revision')
    for key in ('execution_approved_by', 'approved_revision'):
        if key not in approvals:
            findings.add('config_field_missing', f'approvals.{key} (use null when nothing is approved)')
        elif approvals[key] is not None and not (isinstance(approvals[key], str) and approvals[key].strip()):
            findings.add('config_type_invalid', f'approvals.{key} must be null or a non-empty string')
    report['approval_recorded'] = bool(isinstance(who, str) and who.strip() and isinstance(rev, str) and rev.strip()
                                       and bool(runners) and all(r['approved'] is True for r in runners.values()))
    if not report['approval_recorded']:
        findings.add('execution_not_authorized', 'no complete execution approval is recorded; nothing may be run')

    # ---- core contract fields (data for a task author; the core is not imported or changed)
    prefix = '' if root_value in (None, '.') else root_value.rstrip('/') + '/'
    effective_protected = [p for p in DEFAULT_PROTECTED if p not in sensitive] + protected
    unique = lambda items: list(dict.fromkeys(prefix + i for i in items))
    report['contract_fields'] = {'protected_paths': unique(effective_protected), 'allowed_paths': unique(allowed),
                                 'allowed_sensitive_paths': unique(sensitive),
                                 'ignorable_paths': unique(generated + ignorable)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--config', required=True, help='adapter configuration JSON')
    parser.add_argument('--project', required=True, help='directory containing the Godot project (read-only)')
    parser.add_argument('--emit-contract-fields', action='store_true',
                        help='print only protected/allowed/sensitive/ignorable fields for a result contract')
    parser.add_argument('--codes', action='store_true', help='print the finding-code registry and exit')
    args = parser.parse_args(argv)
    if args.codes:
        print(json.dumps({c: {'level': v[0], 'meaning': v[1]} for c, v in sorted(FINDING_CODES.items())}, indent=2))
        return 0
    report = validate(args.config, args.project)
    if args.emit_contract_fields and report['adapter_state'] == 'ADAPTER_READY':
        print(json.dumps(report['contract_fields'], indent=2))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['adapter_state'] == 'ADAPTER_READY' else 2


if __name__ == '__main__':
    sys.exit(main())
