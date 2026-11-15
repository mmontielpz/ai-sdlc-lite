"""Generate a fail-closed starting template for `ai-sdlc-lite-result/1` (stdlib only, no network)."""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

from ._root import framework_root

__all__ = ['build_template', 'main']

_SPEC = importlib.util.spec_from_file_location(
    'ai_sdlc_verify_scope',
    framework_root() / 'scripts' / 'verify_scope.py',
)
_vs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_vs)


def _validate_baseline_commit(root, base):
    if not isinstance(base, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', base):
        raise _vs.Blocked('baseline_sha must be a full lowercase hex commit id')
    code, resolved = _vs.git(root, 'rev-parse', '--verify', '--quiet', base + '^{commit}')
    if code != 0 or resolved.decode().strip() != base:
        raise _vs.Blocked('baseline_sha does not resolve to a commit in this repository')
    code, _ = _vs.git(root, 'merge-base', '--is-ancestor', base, 'HEAD')
    if code == 1:
        raise _vs.Blocked('baseline_sha is not an ancestor of HEAD (wrong branch or rewritten history)')
    if code != 0:
        raise _vs.Blocked('cannot determine baseline ancestry')


def _validate_out_path(root, out_arg):
    if not isinstance(out_arg, str) or not out_arg.strip() or '\0' in out_arg:
        raise _vs.Blocked('output path must be a non-empty path')
    raw = Path(out_arg).expanduser()
    if raw.is_symlink():
        raise _vs.Blocked(f'refusing to write through symlink: {out_arg}')
    resolved = raw.resolve()
    if resolved == root or root in resolved.parents:
        raise _vs.Blocked('refusing to write result template inside the repository being inspected')
    if not resolved.parent.is_dir():
        raise _vs.Blocked(f'output parent directory does not exist: {resolved.parent}')
    if resolved.exists():
        raise _vs.Blocked(f'refusing to overwrite existing output file: {resolved}')
    return resolved


def build_template(repo, baseline_record=None):
    """Build a fail-closed `ai-sdlc-lite-result/1` template from repository state or a baseline record."""
    root = _vs.repo_root(repo)
    if baseline_record is not None:
        record = _vs.load_sealed(baseline_record, _vs.BASELINE_SCHEMA, 'baseline record')
        base = record.get('baseline_sha')
        _validate_baseline_commit(root, base)
        dirty = _vs.string_list(record, 'baseline_dirty_paths')
        ignored = _vs.string_list(record, 'baseline_ignored_paths')
    else:
        current = _vs.make_baseline(root)
        base = current['baseline_sha']
        dirty = current['baseline_dirty_paths']
        ignored = current['baseline_ignored_paths']

    modified = _vs.changes_since(root, base)
    return root, {
        'schema': _vs.CONTRACT_SCHEMA,
        'task_id': 'REPLACE-WITH-TASK-ID',
        'baseline_sha': base,
        'baseline_dirty_paths': dirty,
        'baseline_ignored_paths': ignored,
        'allowed_paths': ['REPLACE-WITH-ALLOWED-GLOB'],
        'modified_paths': modified,
        'verification': [],
        'claimed_status': 'BLOCKED',
        'execution_state': 'in_progress',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='ai-sdlc result-template',
        description='Generate a fail-closed ai-sdlc-lite-result/1 starting template outside the repository.',
    )
    parser.add_argument('--repo', required=True, help='path to the target Git repository')
    parser.add_argument('--out', required=True, help='NEW output file outside the repository (never overwrites)')
    parser.add_argument('--baseline-record', help='optional operator-supplied baseline record from `ai-sdlc baseline`')
    args = parser.parse_args(argv)
    try:
        root, template = build_template(args.repo, args.baseline_record)
        out = _validate_out_path(root, args.out)
        text = json.dumps(template, indent=2, sort_keys=True) + '\n'
        _vs.write_new(out, text)
    except _vs.Blocked as error:
        sys.stderr.write(f'ai-sdlc result-template: BLOCKED: {error}\n')
        return 2
    except OSError as error:
        sys.stderr.write(f'ai-sdlc result-template: BLOCKED: cannot write --out: {error}\n')
        return 2
    except Exception as error:
        sys.stderr.write(f'ai-sdlc result-template: BLOCKED: unexpected error: {type(error).__name__}: {error}\n')
        return 2
    sys.stdout.write(f'wrote result template to {out}\n')
    return 0
