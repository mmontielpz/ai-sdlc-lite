#!/usr/bin/env python3
"""Read-only declaration validation; never launches Codex or grants authorization."""
import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name('codex-adapter.schema.json')
MAX_BYTES = 65536
SKILL_PATH = '.agents/skills/ai-sdlc-lite/SKILL.md'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def regular_file(path):
    # Reject symlinks in every component before reading.
    return not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file()


def read_json(path):
    if not regular_file(path) or path.stat().st_size > MAX_BYTES:
        raise ValueError('JSON file missing, symlinked or oversized')
    return json.loads(path.read_text('utf-8'), object_pairs_hook=unique_object)


def check_shape(value, rule, label, errors):
    """Enforce the vocabulary used by this bundled schema, not arbitrary JSON Schema."""
    if 'const' in rule and (type(value) is not type(rule['const']) or value != rule['const']):
        errors.append(label + ': invalid constant')
    if 'enum' in rule and value not in rule['enum']:
        errors.append(label + ': unsupported value')
    kind = rule.get('type')
    types = {'object': dict, 'array': list, 'string': str}
    if kind and not isinstance(value, types[kind]):
        errors.append(label + ': invalid type')
        return
    if kind == 'object':
        props = rule['properties']
        if set(value) - set(props):
            errors.append(label + ': unknown fields')
        if set(rule.get('required', [])) - set(value):
            errors.append(label + ': missing fields')
        for key in value.keys() & props.keys():
            check_shape(value[key], props[key], label + '.' + key, errors)
    elif kind == 'array':
        if len(value) < rule.get('minItems', 0):
            errors.append(label + ': too few items')
        for item in value:
            check_shape(item, rule['items'], label + '[]', errors)
    elif kind == 'string':
        if not rule.get('minLength', 0) <= len(value) <= rule.get('maxLength', MAX_BYTES):
            errors.append(label + ': invalid length')


def safe_pattern(value):
    return (isinstance(value, str) and bool(value) and
            not any(ord(c) in (0, 10, 13, 92) or c in ':$%~' for c in value) and
            not value.startswith(('/', './')) and
            all(part not in ('', '.', '..') for part in value.split('/')))


def prefix(pattern):
    return re.split(r'[*?\[]', pattern, maxsplit=1)[0]


def validate(config_path, project_dir):
    report = {'schema': 'ai-sdlc-codex-adapter-report/1', 'adapter_state': 'NOT_READY',
              'execution_authorized': False, 'effective_permissions_verified': False,
              'bov_approval': 'not verified', 'project_authorization': 'not verified',
              'evidence_verification': 'not performed', 'human_acceptance': 'PENDING',
              'qualification': {'smoke': 'NOT_RUN', 'deep': 'NOT_RUN'},
              'errors': []}
    errors = report['errors']
    try:
        config = read_json(Path(config_path).absolute())
        schema = read_json(SCHEMA_FILE.absolute())
        check_shape(config, schema, 'config', errors)
        if errors:
            return report
        root = Path(project_dir).absolute()
        if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
            errors.append('project root missing or symlinked')
            return report
        paths = config['instruction_paths']
        if 'AGENTS.md' not in paths or len(paths) != len(set(paths)):
            errors.append('instruction_paths must include root AGENTS.md without duplicates')
        for name in [config['skill_path'], *paths]:
            if not safe_pattern(name) or any(c in name for c in '*?['):
                errors.append('unsafe instruction/skill path')
                continue
            target = root / name
            if not regular_file(target) or target.stat().st_size == 0 or target.stat().st_size > MAX_BYTES:
                errors.append('instruction/skill file missing, empty, oversized or symlinked: ' + name)
        skill = root / SKILL_PATH
        if regular_file(skill) and skill.stat().st_size <= MAX_BYTES:
            text = skill.read_text('utf-8')
            if not text.startswith('---\n') or not re.search(r'^name: ["\']?ai-sdlc-lite["\']?\s*$', text, re.M):
                errors.append('canonical ai-sdlc-lite skill identity missing')
        scope = config['scope']
        for patterns in scope.values():
            if len(patterns) != len(set(patterns)) or any(not safe_pattern(p) for p in patterns):
                errors.append('unsafe or duplicate scope patterns')
        # Intentionally conservative overlap check; not a filesystem enforcement boundary.
        for allowed in scope['allowed_paths']:
            if not prefix(allowed):
                errors.append('repository-wide wildcard allowance refused')
            for protected in scope['protected_paths']:
                x, y = prefix(allowed), prefix(protected)
                if x.startswith(y) or y.startswith(x):
                    errors.append('allowed/protected scope overlap')
        if not set(scope['allowed_sensitive_paths']) <= set(scope['allowed_paths']):
            errors.append('sensitive allowances must also be explicit allowed_paths entries')
        if not set(paths + [SKILL_PATH]) <= set(scope['protected_paths']):
            errors.append('instruction and skill files must be explicitly protected')
        if not errors:
            report['adapter_state'] = 'CODEX_ADAPTER_READY'
            report['contract_fields'] = scope
    except Exception as error:
        errors.append('validation failed closed: ' + type(error).__name__)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--project', required=True)
    args = parser.parse_args(argv)
    report = validate(args.config, args.project)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['adapter_state'] == 'CODEX_ADAPTER_READY' else 2


if __name__ == '__main__':
    sys.exit(main())
