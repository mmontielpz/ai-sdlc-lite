#!/usr/bin/env python3
"""Post-execution scope verifier for AI-SDLC Lite (stdlib only, no network).

DETECTION, NOT PREVENTION. Git is invoked in the target repository with execution-related
configuration neutralised (see HARDENING below); this is mitigation of listed vectors, not a sandbox. This tool inspects a Git working tree AFTER work
happened and compares it with a machine-readable result contract. It cannot
stop an action, cannot see ignored files, and cannot prove what the tree looked
like before work unless the contract recorded it. It never executes any
command named in the contract.

Subcommands:
  baseline --repo PATH [--out F]  capture a baseline record (SHA, dirty and ignored paths, digest); run before the task
  seal --out F FILE...            record evidence hashes in a manifest (hash integrity only, not authentication)
  codes                           print the stable failure-code registry
  verify --repo PATH --result F [--baseline-record F] [--evidence-manifest F] [--require-sealed]
                                  verify a result contract; exit 0 PASS, 1 PARTIAL, 2 BLOCKED

The verifier NEVER modifies the repository: no reset, clean, delete, checkout or write. Recovery is owner-controlled.

Fail closed: any missing, malformed or ambiguous critical evidence is BLOCKED.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CONTRACT_SCHEMA = 'ai-sdlc-lite-result/1'
BASELINE_SCHEMA = 'ai-sdlc-lite-baseline/1'
MANIFEST_SCHEMA = 'ai-sdlc-lite-evidence-manifest/1'
EXECUTION_STATES = ('complete', 'in_progress', 'interrupted')
REGISTRY_VERSION = 1

# Stable failure-code registry. Codes never change meaning or severity within registry_version 1; new codes may be
# added, removed codes are never reused. Value: (allowed severities, one-line meaning). `add()` refuses unregistered
# codes, and tests/test_verify_scope.py checks that every code is emitted somewhere, documented and has a golden report.
FAILURE_CODES = {
    'baseline_mismatch': (('BLOCKED',), 'baseline_sha is not an ancestor of HEAD (wrong branch or rewritten history)'),
    'baseline_record_mismatch': (('BLOCKED',), 'the contract disagrees with the operator-supplied baseline record'),
    'record_tampered': (('BLOCKED',), 'a baseline record or evidence manifest fails its own digest'),
    'dirty_baseline': (('PARTIAL',), 'work began on a dirty tree; attribution of those paths is ambiguous'),
    'declared_mismatch': (('BLOCKED',), 'modified_paths differs from the change set Git reports'),
    'out_of_scope_modification': (('BLOCKED',), 'a changed path is not covered by allowed_paths'),
    'protected_path_modified': (('BLOCKED',), 'a protected path changed (also for new ignored files)'),
    'test_path_modified_unapproved': (('BLOCKED',), 'a test file changed without allowed_sensitive_paths'),
    'governance_path_modified_unapproved': (('BLOCKED',), 'a governance file changed without allowed_sensitive_paths'),
    'special_file_change': (('BLOCKED',), 'a symlink, submodule or file-mode change without allowed_sensitive_paths'),
    'ignored_baseline_unknown': (('PARTIAL',), 'ignored files exist and no ignored baseline was recorded'),
    'ignored_path_unapproved': (('BLOCKED',), 'a new ignored file is outside ignorable_paths and allowed_paths'),
    'ignored_listing_truncated': (('PARTIAL',), 'the ignored-file set is too large or truncated and was not fully compared'),
    'missing_evidence': (('BLOCKED',), 'verification entry, exit code, hash pin or evidence file is missing or unusable'),
    'evidence_hash_mismatch': (('BLOCKED',), 'an evidence file differs from its sha256 pin in the contract'),
    'evidence_tampered': (('BLOCKED',), 'an evidence file differs from the supplied sealed manifest'),
    'evidence_not_sealed': (('PARTIAL',), '--require-sealed: evidence is not covered by a matching sealed manifest'),
    'check_failed': (('PARTIAL',), 'a recorded verification command reported a non-zero exit code'),
    'required_check_missing': (('BLOCKED',), 'a command listed in required_verification was not recorded'),
    'incomplete_execution': (('BLOCKED',), 'execution_state is not complete (interrupted or unfinished task)'),
    'false_pass': (('BLOCKED', 'PARTIAL'), 'the contract claims PASS but verification computed a lower status'),
    'executable_git_config': (('BLOCKED',), 'repository configuration defines a program Git would run'),
    'verification_error': (('BLOCKED',), 'malformed or ambiguous input, or an unexpected error (fail closed)'),
}
IGNORED_CAP = 20000
OUTPUT_SCHEMA = 'ai-sdlc-lite-verification/1'
STATUSES = ('PASS', 'PARTIAL', 'BLOCKED')
RANK = {name: index for index, name in enumerate(STATUSES)}
EXIT = {'PASS': 0, 'PARTIAL': 1, 'BLOCKED': 2}
MAX_JSON = 1 << 20
MAX_EVIDENCE = 10 << 20

# Changes here need an explicit allowed_sensitive_paths entry, never just allowed_paths.
TEST_PATTERNS = ('**/tests/**', '**/test/**', '**/__tests__/**', '**/test_*.py',
                 '**/*_test.py', '**/*.test.*', '**/*.spec.*', '**/conftest.py')
GOVERNANCE_PATTERNS = ('**/AGENTS.md', '**/CLAUDE.md', '**/GEMINI.md', 'SECURITY.md',
                       'CODEOWNERS', '.github/**', '.agents/**', '.claude/**',
                       '.githooks/**', '.gitignore', '.gitattributes')

LIMITATIONS = ['Post-execution detection only; does not prevent or sandbox any action.',
               'New ignored files are compared with a baseline set; content changes to already-ignored files and '
               'changes outside the repository are not seen.',
               'Without an operator-supplied baseline record, a contract that wrongly records a clean baseline cannot '
               'be disproved; the record itself is not authenticated.',
               'Commands are never run, so exit codes are agent-reported; a sha256 pin or manifest shows byte-identity '
               'only and does not authenticate evidence or prove execution.']


class Blocked(Exception):
    pass


def compile_glob(pattern):
    if not isinstance(pattern, str) or not pattern or pattern.startswith('/') \
            or '\\' in pattern or '\0' in pattern or '..' in pattern.split('/'):
        raise Blocked(f'invalid path pattern: {pattern!r}')
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


def matcher(patterns):
    compiled = [compile_glob(p) for p in patterns]
    return lambda path: any(rx.match(path) for rx in compiled)


# Git can run programs named in configuration. Mitigations, each covered by tests/test_verify_scope.py:
#  * every GIT_* environment variable is dropped (config injection, GIT_DIR redirection, external diff, pager);
#  * core.fsmonitor and hooks are force-disabled on every call (command-line -c overrides repo, global and system config);
#  * the index is never refreshed on disk (GIT_OPTIONAL_LOCKS=0), so index-change hooks have no trigger;
#  * diff is run with --no-ext-diff --no-textconv;
#  * filter and diff-driver programs cannot be switched off by -c without knowing their names, so a repository
#    whose NON-user configuration defines one is refused (BLOCKED) rather than trusted. See check_git_config().
# Not claimed: that Git's whole execution surface is covered, or that user-level (global/system) config is safe.
HARDENING = ('-c', 'core.quotepath=off', '-c', 'core.fsmonitor=false', '-c', f'core.hooksPath={os.devnull}')
EXECUTABLE_KEYS = (re.compile(r'filter\..+\.(clean|smudge|process)\Z', re.I),
                   re.compile(r'diff\..+\.(command|textconv)\Z', re.I),
                   re.compile(r'diff\.external\Z', re.I))


def run_git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        done = subprocess.run(['git', *HARDENING, *args], cwd=cwd, env=env, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        raise Blocked(f'git unavailable or timed out: {error}')
    return done.returncode, done.stdout


def git(root, *args):
    return run_git(root, *args)


def config_entries(root, *scope):
    """Parse `git config --list --show-origin -z` into (origin, key, value). Reading config runs nothing."""
    code, out = run_git(root, 'config', *scope, '--list', '--show-origin', '-z')
    if code != 0:
        return []
    parts = out.decode('utf-8', 'surrogateescape').split('\0')
    entries = []
    for origin, item in zip(parts[0::2], parts[1::2]):
        key, _, value = item.partition('\n')
        entries.append((origin, key, value))
    return entries


def check_git_config(root):
    """Fail closed when configuration outside the user's own global/system files can run a program."""
    trusted = {origin for scope in (('--global',), ('--system',)) for origin, _, _ in config_entries(root, *scope)}
    for origin, key, _ in config_entries(root):
        if origin not in trusted and any(rx.match(key) for rx in EXECUTABLE_KEYS):
            raise Blocked(f'repository configuration defines a program Git would run ({key} from {origin}); '
                          'refusing to inspect an untrusted repository (code: executable_git_config)')


def repo_root(path):
    start = Path(path).expanduser()
    if not start.is_dir():
        raise Blocked('repository path is not a directory')
    code, out = git(start, 'rev-parse', '--show-toplevel')
    if code != 0 or not out.strip():
        raise Blocked('not a Git repository')
    root = Path(out.decode().strip()).resolve()
    check_git_config(root)
    return root


def split_nul(data):
    return [item.decode('utf-8', 'surrogateescape') for item in data.split(b'\0') if item]


def current_dirty(root):
    """Paths differing from HEAD plus untracked (non-ignored) paths."""
    code, tracked = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z', '--no-renames', 'HEAD', '--')
    if code != 0:
        raise Blocked('cannot list tracked changes (no commits?)')
    code, untracked = git(root, 'ls-files', '-o', '--exclude-standard', '-z')
    if code != 0:
        raise Blocked('cannot list untracked files')
    return sorted(set(split_nul(tracked)) | set(split_nul(untracked)))


def changes_since(root, base):
    code, tracked = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z', '--no-renames', base, '--')
    if code != 0:
        raise Blocked('cannot diff against baseline')
    code, untracked = git(root, 'ls-files', '-o', '--exclude-standard', '-z')
    if code != 0:
        raise Blocked('cannot list untracked files')
    return sorted(set(split_nul(tracked)) | set(split_nul(untracked)))


def load_json(path, label):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON:
        raise Blocked(f'{label} missing, not a regular file, a symlink, or too large')
    try:
        data = json.loads(path.read_text('utf-8'))
    except (OSError, ValueError) as error:
        raise Blocked(f'{label} is not valid JSON: {error}')
    if not isinstance(data, dict):
        raise Blocked(f'{label} must be a JSON object')
    return data


def string_list(contract, key, required=True):
    if key not in contract:
        if required:
            raise Blocked(f'contract field missing: {key}')
        return []
    value = contract[key]
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise Blocked(f'contract field {key} must be a list of non-empty strings')
    return value


def canonical_digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def untracked_paths(root):
    code, out = git(root, 'ls-files', '-o', '--exclude-standard', '-z')
    if code != 0:
        raise Blocked('cannot list untracked files')
    return split_nul(out)


def ignored_paths(root):
    """Ignored, untracked files (sorted, capped). Content changes of already-ignored files are NOT detectable."""
    code, out = git(root, 'ls-files', '-o', '-i', '--exclude-standard', '-z')
    if code != 0:
        raise Blocked('cannot list ignored files')
    items = sorted(split_nul(out))
    return items[:IGNORED_CAP], len(items) > IGNORED_CAP


def path_digest(root, rel):
    path = root / rel
    if path.is_symlink():
        return 'symlink:' + os.readlink(path)
    if not path.exists():
        return None
    if not path.is_file():
        return 'not-a-regular-file'
    if path.stat().st_size > MAX_EVIDENCE:
        return 'too-large'
    return hashlib.sha256(path.read_bytes()).hexdigest()


def special_changes(root, base):
    """Paths whose change involves a symlink, submodule or file-mode change (needs explicit approval)."""
    code, out = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--raw', '-z', '--no-renames', base, '--')
    if code != 0:
        raise Blocked('cannot read change modes')
    parts = out.decode('utf-8', 'surrogateescape').split('\0')
    special, i = set(), 0
    while i < len(parts) - 1:
        if not parts[i].startswith(':'):
            i += 1
            continue
        fields = parts[i][1:].split(' ')
        old, new, path = fields[0], fields[1], parts[i + 1]
        i += 2
        if '120000' in (old, new) or '160000' in (old, new) or (old != new and '000000' not in (old, new)):
            special.add(path)
    for path in untracked_paths(root):
        if (root / path).is_symlink():
            special.add(path)
    return special


def make_baseline(root):
    """Independent baseline record. Run BEFORE the task, by a human or CI, and store it outside the repository."""
    code, head = git(root, 'rev-parse', 'HEAD')
    if code != 0:
        raise Blocked('cannot resolve HEAD')
    dirty = current_dirty(root)
    ignored, truncated = ignored_paths(root)
    record = {'schema': BASELINE_SCHEMA, 'baseline_sha': head.decode().strip(), 'baseline_dirty_paths': dirty,
              'baseline_dirty_sha256': {p: path_digest(root, p) for p in dirty},
              'baseline_ignored_paths': ignored, 'baseline_ignored_truncated': truncated}
    record['digest'] = canonical_digest(record)
    return record


def load_sealed(path, schema, label):
    """Load a baseline record or evidence manifest and recompute its digest (detects accidental or hand edits only)."""
    data = load_json(path, label)
    if data.get('schema') != schema:
        raise Blocked(f'{label} schema must be {schema}')
    claimed = data.get('digest')
    body = {k: v for k, v in data.items() if k != 'digest'}
    if not isinstance(claimed, str) or canonical_digest(body) != claimed:
        raise Blocked(f'{label} digest mismatch; the record was altered or is malformed (code: record_tampered)')
    return data


def write_new(path, text):
    """Create a new file, refusing to overwrite or follow a symlink."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags, 0o600), 'w') as stream:
        stream.write(text)


RECOVERY = {
    'default': 'Owner-controlled recovery: this tool never resets, cleans, deletes, checks out or overwrites anything. '
               'Review `git status` and `git diff <baseline_sha>`, then decide to keep, revert or archive the work '
               'yourself, preserving any changes you want. Re-verify with a new contract afterwards.',
    'missing_evidence': 'Evidence is missing or unusable: obtain it again from the task owner; do not accept PASS.',
    'evidence_tampered': 'Evidence differs from the sealed manifest: treat the run as untrustworthy; preserve both files.',
    'evidence_hash_mismatch': 'Evidence differs from its pinned hash: treat the run as untrustworthy; preserve the files.',
    'out_of_scope_modification': 'Out-of-scope changes: the owner reviews each path and decides whether to keep or revert it.',
    'protected_path_modified': 'Protected content changed: preserve the working tree, then restore from version control yourself.',
    'incomplete_execution': 'The task did not finish: inspect the partial changes before any further work; nothing is rolled back for you.',
    'required_check_missing': 'A required check was not recorded: the run is incomplete; do not accept PASS.',
    'baseline_mismatch': 'The baseline is not an ancestor of HEAD: confirm the branch and baseline before trusting any result.',
    'baseline_record_mismatch': 'The contract disagrees with the operator-supplied baseline record: preserve both and investigate.',
    'ignored_path_unapproved': 'New ignored files are present: review them; ignored files are not covered by version control.',
    'evidence_not_sealed': 'Evidence is not covered by a sealed manifest: seal it from trusted custody; a hash alone is not authentication.',
    'executable_git_config': 'The repository defines a program Git would run: inspect it with a trusted tool; verify inside a sandbox.',
}


def recovery_for(reasons):
    codes = {r['code'] for r in reasons}
    return [RECOVERY['default']] + [RECOVERY[c] for c in sorted(codes) if c in RECOVERY]


def hash_evidence(ref, bases):
    """Return sha256 of a regular, non-symlink evidence file inside an allowed base."""
    if not isinstance(ref, str) or not ref or '\0' in ref:
        raise Blocked('evidence reference must be a non-empty string')
    for base in bases:
        candidate = Path(ref) if os.path.isabs(ref) else base / ref
        if candidate.is_symlink() or any(p.is_symlink() for p in candidate.parents if base in p.parents):
            raise Blocked(f'evidence path uses a symlink: {ref}')
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if base != resolved and base not in resolved.parents:
            continue
        if resolved.stat().st_size > MAX_EVIDENCE:
            raise Blocked(f'evidence file too large: {ref}')
        return hashlib.sha256(resolved.read_bytes()).hexdigest()
    raise Blocked(f'evidence file missing or outside the repository/result directory: {ref}')


def verify(repo, result_path, out_path=None, baseline_record=None, evidence_manifest=None, require_sealed=False):
    reasons = []

    def add(severity, code, detail):
        if code not in FAILURE_CODES or severity not in FAILURE_CODES[code][0]:
            raise Blocked(f'internal error: unregistered failure code or severity {severity}/{code}')
        reasons.append({'severity': severity, 'code': code, 'detail': detail})

    report = {'schema': OUTPUT_SCHEMA, 'registry_version': REGISTRY_VERSION, 'limitations': LIMITATIONS}
    result_path = Path(result_path).expanduser().resolve()
    root = repo_root(repo)
    contract = load_json(result_path, 'result contract')
    if contract.get('schema') != CONTRACT_SCHEMA:
        raise Blocked(f'contract schema must be {CONTRACT_SCHEMA}')
    task_id = contract.get('task_id')
    if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,64}', task_id):
        raise Blocked('task_id missing or malformed')
    report['task_id'] = task_id
    claimed = contract.get('claimed_status')
    if claimed not in STATUSES:
        raise Blocked('claimed_status must be PASS, PARTIAL or BLOCKED')
    report['claimed_status'] = claimed
    state = contract.get('execution_state')
    if state is not None and state not in EXECUTION_STATES:
        raise Blocked('execution_state must be complete, in_progress or interrupted')

    allowed = string_list(contract, 'allowed_paths')
    allowed_sensitive = string_list(contract, 'allowed_sensitive_paths', required=False)
    protected = string_list(contract, 'protected_paths', required=False)
    ignorable = string_list(contract, 'ignorable_paths', required=False)
    required_checks = string_list(contract, 'required_verification', required=False)
    declared = string_list(contract, 'modified_paths')
    baseline_dirty = string_list(contract, 'baseline_dirty_paths')  # [] means "recorded clean"
    baseline_ignored = string_list(contract, 'baseline_ignored_paths') if 'baseline_ignored_paths' in contract else None
    evidence_refs = string_list(contract, 'evidence_refs', required=False)
    in_allowed, in_sensitive, in_protected = matcher(allowed), matcher(allowed_sensitive), matcher(protected)
    in_ignorable = matcher(ignorable)
    is_test, is_gov = matcher(TEST_PATTERNS), matcher(GOVERNANCE_PATTERNS)
    record = load_sealed(baseline_record, BASELINE_SCHEMA, 'baseline record') if baseline_record else None
    manifest = load_sealed(evidence_manifest, MANIFEST_SCHEMA, 'evidence manifest') if evidence_manifest else None
    sealed = {}
    if manifest is not None:
        entries = manifest.get('entries')
        if not isinstance(entries, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in entries.items()):
            raise Blocked('evidence manifest entries must map paths to sha256 strings')
        sealed = entries
    # Four distinct properties. Only hash integrity is ever checked; custody, execution and assertions never are.
    trust = {'baseline': 'agent-reported', 'hash_integrity': 'none',
             'custody': 'unauthenticated: an operator may supply records from a location the agent cannot write, '
                        'but the verifier cannot authenticate who wrote them',
             'independent_execution': 'not verified: the verifier never runs or observes commands',
             'agent_assertions': 'unverified: exit codes, claimed_status, modified_paths, failure_reasons'}
    report['trust'] = trust

    # Baseline: full-length SHA that resolves to a commit and is an ancestor of HEAD.
    base = contract.get('baseline_sha')
    if not isinstance(base, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', base):
        raise Blocked('baseline_sha must be a full lowercase hex commit id')
    code, resolved = git(root, 'rev-parse', '--verify', '--quiet', base + '^{commit}')
    if code != 0 or resolved.decode().strip() != base:
        raise Blocked('baseline_sha does not resolve to a commit in this repository')
    code, head = git(root, 'rev-parse', 'HEAD')
    if code != 0:
        raise Blocked('cannot resolve HEAD')
    report['baseline_sha'], report['head_sha'] = base, head.decode().strip()
    code, _ = git(root, 'merge-base', '--is-ancestor', base, 'HEAD')
    if code == 1:
        add('BLOCKED', 'baseline_mismatch', 'baseline_sha is not an ancestor of HEAD (wrong branch or rewritten history)')
    elif code != 0:
        raise Blocked('cannot determine baseline ancestry')

    # An operator-supplied baseline record overrides, and must agree with, the contract's own claims.
    if record is not None:
        trust['baseline'] = 'operator-supplied record (digest checked; custody and authenticity not verifiable)'
        rec_dirty = string_list(record, 'baseline_dirty_paths')
        rec_ignored = string_list(record, 'baseline_ignored_paths')
        if record.get('baseline_sha') != base:
            add('BLOCKED', 'baseline_record_mismatch', 'contract baseline_sha differs from the operator-supplied record')
        if sorted(rec_dirty) != sorted(baseline_dirty):
            add('BLOCKED', 'baseline_record_mismatch', 'contract baseline_dirty_paths differ from the operator-supplied record')
        if baseline_ignored is not None and sorted(rec_ignored) != sorted(baseline_ignored):
            add('BLOCKED', 'baseline_record_mismatch', 'contract baseline_ignored_paths differ from the operator-supplied record')
        if record.get('baseline_ignored_truncated'):
            add('PARTIAL', 'ignored_listing_truncated', 'the recorded ignored-file list was truncated')
        baseline_dirty, baseline_ignored = rec_dirty, rec_ignored
        hashes = record.get('baseline_dirty_sha256') if isinstance(record.get('baseline_dirty_sha256'), dict) else {}
        report['dirty_baseline_changed_since_record'] = sorted(
            p for p in rec_dirty if hashes.get(p) != path_digest(root, p))

    # Actual changes versus the baseline (committed, staged, unstaged, untracked).
    excluded = set()
    for extra in (result_path, Path(out_path).expanduser().resolve() if out_path else None):
        if extra and root in extra.parents:
            excluded.add(extra.relative_to(root).as_posix())
    actual = [p for p in changes_since(root, base) if p not in excluded]
    report['modified_paths'] = actual

    if baseline_dirty:
        add('PARTIAL', 'dirty_baseline', 'work began on a dirty tree; attribution of these paths is ambiguous: '
            + ', '.join(sorted(baseline_dirty)))
    if set(declared) != set(actual):
        add('BLOCKED', 'declared_mismatch',
            f'undeclared changes: {sorted(set(actual) - set(declared))}; declared but unchanged: {sorted(set(declared) - set(actual))}')

    for path in actual:
        if in_protected(path):
            add('BLOCKED', 'protected_path_modified', path)
        elif is_test(path) or is_gov(path):
            kind = 'governance' if is_gov(path) else 'test'
            if not in_sensitive(path):
                add('BLOCKED', f'{kind}_path_modified_unapproved', path)
        elif not in_allowed(path):
            add('BLOCKED', 'out_of_scope_modification', path)
    for path in sorted(special_changes(root, base) - excluded):
        if not in_sensitive(path):
            add('BLOCKED', 'special_file_change', f'{path}: symlink, submodule or file-mode change needs allowed_sensitive_paths')

    # Ignored files are invisible to the diff; compare the ignored set with the baseline's.
    ignored, truncated = ignored_paths(root)
    ignored = [p for p in ignored if p not in excluded]
    report['ignored_paths_count'] = len(ignored)
    if truncated:
        add('PARTIAL', 'ignored_listing_truncated', f'more than {IGNORED_CAP} ignored files; the ignored set was not compared')
    elif baseline_ignored is None:
        relevant = [p for p in ignored if not in_ignorable(p)]
        if relevant:
            add('PARTIAL', 'ignored_baseline_unknown',
                f'{len(relevant)} ignored file(s) present (first: {relevant[0]}) and no baseline_ignored_paths recorded; '
                'ignored files are not covered by version control')
    else:
        known = set(baseline_ignored)
        fresh = [p for p in ignored if p not in known]
        for path in fresh[:50]:
            if in_protected(path):
                add('BLOCKED', 'protected_path_modified', f'{path} (ignored file)')
            elif not (in_ignorable(path) or in_allowed(path)):
                add('BLOCKED', 'ignored_path_unapproved', path)
        if len(fresh) > 50:
            add('PARTIAL', 'ignored_listing_truncated', f'{len(fresh) - 50} further new ignored files were not individually checked')

    # Verification commands and evidence (commands are never executed here).
    checks = contract.get('verification')
    bases = [root, result_path.parent]
    report['evidence'] = []
    seen_commands = set()

    def record_evidence(ref, label, pin=None):
        try:
            digest = hash_evidence(ref, bases)
        except Blocked as error:
            add('BLOCKED', 'missing_evidence', f'{label}: {error}')
            return
        checked, mismatch = [], False
        if pin is not None:
            if pin == digest:
                checked.append('pinned')        # proves only agreement with a hash the agent itself supplied
            else:
                mismatch = True
                add('BLOCKED', 'evidence_hash_mismatch', f'{label}: file hash differs from the pinned sha256')
        if ref in sealed:
            if sealed[ref] == digest:
                checked.append('sealed')        # proves byte-identity with a manifest, nothing more
            else:
                mismatch = True
                add('BLOCKED', 'evidence_tampered', f'{label}: file differs from the sealed manifest')
        report['evidence'].append({'ref': ref, 'sha256': digest, 'origin': 'agent-reported',
                                   'integrity': 'mismatch' if mismatch else '+'.join(checked) or 'unchecked',
                                   'execution': 'not-verified'})

    if not isinstance(checks, list) or not checks:
        add('BLOCKED', 'missing_evidence', 'no verification commands recorded')
        checks = []
    for index, check in enumerate(checks):
        label = f'verification[{index}]'
        if not isinstance(check, dict) or not isinstance(check.get('command'), str) or not check['command'].strip():
            add('BLOCKED', 'missing_evidence', f'{label}: command missing'); continue
        exit_code = check.get('exit_code')
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            add('BLOCKED', 'missing_evidence', f'{label}: exit_code missing or not an integer'); continue
        pin = check.get('sha256')
        if pin is not None and not (isinstance(pin, str) and re.fullmatch(r'[0-9a-f]{64}', pin)):
            add('BLOCKED', 'missing_evidence', f'{label}: sha256 must be 64 lowercase hex characters'); continue
        seen_commands.add(check['command'])
        record_evidence(check.get('evidence'), label, pin)
        if exit_code != 0:
            add('PARTIAL', 'check_failed', f'{label}: `{check["command"]}` exited {exit_code}')
    for ref in evidence_refs:
        record_evidence(ref, 'evidence_refs')
    for command in required_checks:
        if command not in seen_commands:
            add('BLOCKED', 'required_check_missing', f'required verification not recorded: `{command}`')
    if state is not None and state != 'complete':
        add('BLOCKED', 'incomplete_execution', f'contract execution_state is {state!r}; the task did not complete')
    levels = [e['integrity'] for e in report['evidence']]
    trust['hash_integrity'] = ('none' if not levels or all(x == 'unchecked' for x in levels)
                               else 'all' if all(x not in ('unchecked', 'mismatch') for x in levels) else 'partial')
    if require_sealed and (not levels or any('sealed' not in x for x in levels)):
        add('PARTIAL', 'evidence_not_sealed',
            'every evidence file must match a sealed manifest (--evidence-manifest); a sealed hash still does not '
            'authenticate the evidence or prove that anything ran')

    computed = 'PASS'
    for reason in reasons:
        if RANK[reason['severity']] > RANK[computed]:
            computed = reason['severity']
    if claimed == 'PASS' and computed != 'PASS':
        add('BLOCKED' if computed == 'BLOCKED' else 'PARTIAL', 'false_pass',
            f'contract claims PASS but verification computed {computed}')
    # Never upgrade: the final status is the worse of the claim and the computed result.
    final = claimed if RANK[claimed] > RANK[computed] else computed
    report['computed_status'], report['status'] = computed, final
    report['failure_reasons'] = reasons
    report['agent_reported_failure_reasons'] = [r for r in contract.get('failure_reasons', []) if isinstance(r, str)][:50]
    report['recovery'] = {'automatic_recovery': 'none', 'guidance': recovery_for(reasons) if final != 'PASS' else []}
    return report


def blocked_code(error):
    found = re.search(r'\(code: (\w+)\)', str(error))
    return found.group(1) if found and found.group(1) in FAILURE_CODES else 'verification_error'


def blocked_report(error):
    return {'schema': OUTPUT_SCHEMA, 'registry_version': REGISTRY_VERSION, 'status': 'BLOCKED', 'computed_status': 'BLOCKED',
            'failure_reasons': [{'severity': 'BLOCKED', 'detail': str(error), 'code': blocked_code(error)}],
            'recovery': {'automatic_recovery': 'none', 'guidance': [RECOVERY['default']]},
            'limitations': LIMITATIONS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    base = sub.add_parser('baseline', help='capture a baseline record (run before the task)')
    base.add_argument('--repo', required=True)
    base.add_argument('--out', help='write the record to a NEW file outside the repository (never overwrites)')
    seal = sub.add_parser('seal', help='record evidence hashes in a manifest (hash integrity only)')
    seal.add_argument('--out', required=True, help='NEW manifest file (never overwrites)')
    seal.add_argument('files', nargs='+', help='evidence files; recorded exactly as spelled here')
    check = sub.add_parser('verify', help='verify a result contract')
    check.add_argument('--repo', required=True)
    check.add_argument('--result', required=True)
    check.add_argument('--out', help='also write the JSON report to a NEW file (never overwrites; excluded from the change set)')
    check.add_argument('--baseline-record', help='operator-supplied record from the baseline subcommand')
    check.add_argument('--evidence-manifest', help='sealed manifest from the seal subcommand')
    check.add_argument('--require-sealed', action='store_true',
                       help='PARTIAL unless every evidence file matches the sealed manifest (hash integrity only)')
    sub.add_parser('codes', help='print the stable failure-code registry (JSON)')
    args = parser.parse_args(argv)
    try:
        if args.command == 'codes':
            print(json.dumps({'registry_version': REGISTRY_VERSION,
                              'codes': {c: {'severities': list(v[0]), 'meaning': v[1]} for c, v in sorted(FAILURE_CODES.items())}},
                             indent=2, sort_keys=True))
            return 0
        if args.command == 'baseline':
            root = repo_root(args.repo)
            text = json.dumps(make_baseline(root), indent=2, sort_keys=True)
            if args.out:
                out = Path(args.out).expanduser().resolve()
                if root in out.parents:
                    raise Blocked('refusing to write the baseline record inside the repository being recorded')
                write_new(out, text + '\n')
            print(text)
            return 0
        if args.command == 'seal':
            entries = {}
            for ref in args.files:
                path = Path(ref)
                if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_EVIDENCE:
                    raise Blocked(f'cannot seal {ref}: not a regular, non-symlink file within the size limit')
                entries[ref] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = {'schema': MANIFEST_SCHEMA, 'entries': entries}
            manifest['digest'] = canonical_digest(manifest)
            text = json.dumps(manifest, indent=2, sort_keys=True)
            write_new(Path(args.out).expanduser(), text + '\n')
            print(text)
            return 0
        report = verify(args.repo, args.result, args.out, args.baseline_record,
                        args.evidence_manifest, args.require_sealed)
    except Blocked as error:
        report = blocked_report(error)
    except Exception as error:  # fail closed on anything unexpected
        report = blocked_report(f'unexpected error: {type(error).__name__}: {error}')
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if getattr(args, 'out', None) and args.command == 'verify':
        try:
            write_new(Path(args.out).expanduser(), text + '\n')
        except OSError as error:
            print(f'cannot write --out: {error}', file=sys.stderr)
            return 2
    return EXIT[report['status']]


if __name__ == '__main__':
    sys.exit(main())
