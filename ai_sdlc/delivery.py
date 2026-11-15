"""Offline delivery preflight. No Git invocation, credentials, network or writes.

A digest binds bytes, not human authority. READY is a local preflight observation,
never a grant or a guarantee that a later write will succeed.
"""
import configparser
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

CONTRACT = 'ai-sdlc-delivery/1'
LIMIT = 16 * 1024 * 1024
MAX_FILES = 10000
USAGE = 'usage: python3 -B -m ai_sdlc delivery plan|verify|report --repo PATH --input FILE\n'


class Rejected(Exception):
    pass


def require(value, code):
    if not value:
        raise Rejected(code)


def decode_ref(raw, encoding='utf-8', code='INVALID_REF'):
    """Decode Git reference file bytes strictly without lossy replacement."""
    try:
        return raw.decode(encoding)
    except UnicodeError:
        raise Rejected(code) from None


def text(value):
    return isinstance(value, str) and 0 < len(value) <= 4096 and all(32 <= ord(c) < 127 for c in value)


def oid(value):
    return isinstance(value, str) and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value) is not None


def ref(value):
    return (text(value) and value.startswith('refs/heads/') and len(value) <= 256
            and not any(c in value for c in ' ~^:?*[\\') and '@{' not in value
            and all(p not in ('', '.', '..') and not p.startswith('.') and not p.endswith(('.', '.lock'))
                    for p in value.split('/')))


def relative(value):
    return (text(value) and '\\' not in value and ':' not in value and value == value.strip()
            and all(p not in ('', '.', '..', '.git') for p in value.split('/')))


def safe_path(path):
    """Reject symlinks in every existing component, including ancestors."""
    path = Path(os.path.abspath(str(path)))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        require(not stat.S_ISLNK(current.lstat().st_mode), 'UNSAFE_PATH')
    return path


def read(path):
    path = safe_path(path)
    require(stat.S_ISREG(path.lstat().st_mode), 'UNSAFE_FILE')
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    try:
        require(stat.S_ISREG(os.fstat(fd).st_mode), 'UNSAFE_FILE')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(LIMIT + 1)
        require(len(data) <= LIMIT, 'READ_LIMIT')
        return data
    finally:
        os.close(fd)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_KEY')
        result[key] = value
    return result


def load(path):
    return json.loads(read(path).decode('utf-8'), object_pairs_hook=object_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(Rejected('INVALID_JSON')))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected.split()), 'INVALID_CONTRACT')


def validate_request(request):
    keys(request, 'repository expected_branch base_sha head_sha authorized_files operations commit remote pull_request required_ci authorization_ref executor retry')
    require(text(request['repository']), 'INVALID_IDENTITY')
    require(ref('refs/heads/' + request['expected_branch']) if text(request['expected_branch']) else False, 'INVALID_BRANCH')
    require(oid(request['base_sha']) and oid(request['head_sha']) and len(request['base_sha']) == len(request['head_sha']), 'INVALID_SHA')
    files = request['authorized_files']
    require(isinstance(files, list) and 0 < len(files) <= MAX_FILES and all(relative(p) for p in files), 'INVALID_INVENTORY')
    require(files == sorted(set(files)), 'INVALID_INVENTORY')
    operations = request['operations']
    require(isinstance(operations, list) and operations in (["commit"], ["commit", "push"], ["commit", "push", "pull_request"]), 'INVALID_OPERATIONS')
    keys(request['commit'], 'message signing')
    require(text(request['commit']['message']) and request['commit']['signing'] in ('required', 'forbidden'), 'INVALID_COMMIT')
    keys(request['remote'], 'name destination expected_ref expected_sha')
    remote = request['remote']
    require(text(remote['name']) and re.fullmatch(r'[A-Za-z0-9_-]+', remote['name']), 'INVALID_REMOTE')
    # Deliberately exclude URL userinfo, tokens, query strings, local paths and remote helpers.
    require(isinstance(remote['destination'], str) and re.fullmatch(r'https://[A-Za-z0-9.-]+/[A-Za-z0-9_./-]+', remote['destination'])
            and '..' not in remote['destination'], 'INVALID_REMOTE')
    require(request['repository'] == remote['destination'].removesuffix('.git'), 'INVALID_IDENTITY')
    require(ref(remote['expected_ref']) and (remote['expected_sha'] is None or oid(remote['expected_sha'])), 'INVALID_REMOTE')
    keys(request['pull_request'], 'title body base draft')
    pr = request['pull_request']
    require(text(pr['title']) and isinstance(pr['body'], str) and (not pr['body'] or text(pr['body']))
            and text(pr['base']) and ref('refs/heads/' + pr['base']), 'INVALID_PR')
    require(type(pr['draft']) is bool, 'INVALID_PR')
    checks = request['required_ci']
    require(isinstance(checks, list) and all(text(c) for c in checks) and checks == sorted(set(checks)), 'INVALID_CI')
    require(text(request['authorization_ref']) and text(request['executor']), 'INVALID_AUTHORIZATION_REFERENCE')
    keys(request['retry'], 'max_attempts backoff_seconds')
    retry = request['retry']
    require(type(retry['max_attempts']) is int and 1 <= retry['max_attempts'] <= 3
            and type(retry['backoff_seconds']) is int and 0 <= retry['backoff_seconds'] <= 60, 'INVALID_RETRY')


def present(path):
    return path.exists() or path.is_symlink()


def configuration(git, request):
    """Conservative local allowlist; never follows includes or opens user config."""
    config = configparser.RawConfigParser(strict=True, interpolation=None)
    raw = read(git / 'config')
    config.read_string(raw.decode('utf-8'))
    safe = {'core': {'repositoryformatversion', 'filemode', 'bare', 'logallrefupdates', 'ignorecase', 'precomposeunicode'},
            'user': {'name', 'email'}, 'remote': {'url', 'fetch'}, 'branch': {'remote', 'merge'}}
    require(not config.defaults(), 'UNSAFE_GIT_CONFIG')
    for section in config.sections():
        match = re.fullmatch(r'(core|user|remote|branch)(?: "[^"\n]+")?', section)
        require(match and section.split(' ', 1)[0] in safe, 'UNSAFE_GIT_CONFIG')
        group = section.split(' ', 1)[0]
        for key, value in config.items(section):
            require(key in safe[group] and '\n' not in value, 'UNSAFE_GIT_CONFIG')
            if group == 'core':
                require(value.lower() in ('true', 'false', '0') and (key != 'bare' or value.lower() == 'false'), 'UNSAFE_GIT_CONFIG')
            if key == 'url':
                # Only public-form destinations; never emit config values.
                require(re.fullmatch(r'https://[A-Za-z0-9.-]+/[A-Za-z0-9_./-]+', value), 'UNSAFE_GIT_CONFIG')
    remote = request['remote']
    section = 'remote "' + remote['name'] + '"'
    require(config.has_option(section, 'url') and config.get(section, 'url') == remote['destination'], 'REMOTE_MISMATCH')
    require(not present(git / 'config.worktree'), 'UNSAFE_GIT_CONFIG')
    return hashlib.sha256(raw).hexdigest()


def inventory(repo):
    result = {}
    def visit(folder):
        for path in sorted(folder.iterdir()):
            require(path.name not in ('.git-credentials', '.netrc', '.ssh', '.aws', '.gnupg', '.azure'), 'CREDENTIAL_STORE_IN_INVENTORY')
            name = path.relative_to(repo).as_posix()
            if name == '.git':
                continue
            require(relative(name), 'UNSAFE_PATH')
            mode = path.lstat().st_mode
            require(not stat.S_ISLNK(mode), 'UNSAFE_PATH')
            if stat.S_ISDIR(mode):
                visit(path)
            else:
                require(stat.S_ISREG(mode), 'UNSAFE_FILE')
                require(len(result) < MAX_FILES, 'INVENTORY_LIMIT')
                result[name] = {'sha256': hashlib.sha256(read(path)).hexdigest(), 'executable': bool(mode & 0o111)}
    visit(repo)
    return result


def snapshot(repo, request):
    repo = safe_path(repo)
    git = safe_path(repo / '.git')
    require(stat.S_ISDIR(git.lstat().st_mode), 'UNSUPPORTED_GIT_LAYOUT')
    require(not present(git / 'commondir'), 'UNSUPPORTED_GIT_LAYOUT')
    require(stat.S_ISDIR(safe_path(git / 'objects').lstat().st_mode), 'UNSUPPORTED_GIT_LAYOUT')
    config_hash = configuration(git, request)
    hooks = git / 'hooks'
    if present(hooks):
        safe_path(hooks)
        require(all(p.name.endswith('.sample') and stat.S_ISREG(p.lstat().st_mode) for p in hooks.iterdir()), 'UNSAFE_GIT_HOOKS')
    info = git / 'objects' / 'info'
    if present(info):
        safe_path(info)
    require(not any(present(info / name) for name in ('alternates', 'http-alternates')), 'UNSAFE_GIT_LAYOUT')
    require(not any(k.startswith('GIT_') for k in os.environ), 'UNSAFE_GIT_ENVIRONMENT')
    head = decode_ref(read(git / 'HEAD')).strip('\n')
    require(head == 'ref: refs/heads/' + request['expected_branch'], 'BRANCH_CHANGED')
    target = git / ('refs/heads/' + request['expected_branch'])
    if target.exists() or target.is_symlink():
        sha = decode_ref(read(target), 'ascii').strip('\n')
    else:
        sha = None
        if (git / 'packed-refs').exists():
            for line in decode_ref(read(git / 'packed-refs')).splitlines():
                fields = line.split(' ')
                if len(fields) == 2 and fields[1] == head[5:]:
                    require(sha is None, 'INVALID_REF')
                    sha = fields[0]
    require(oid(sha) and sha == request['head_sha'], 'HEAD_CHANGED')
    # Read-only permission observation; no lock-file probes or mutation attempts.
    paths = [git, git / 'objects', git / 'refs', git / 'HEAD']
    if present(git / 'index'):
        paths.append(git / 'index')
    parent = target
    while not parent.exists() and not parent.is_symlink():
        parent = parent.parent
    paths.append(parent)
    ancestor = parent.parent
    while ancestor != git and git in ancestor.parents:
        paths.append(ancestor)
        ancestor = ancestor.parent
    writable = True
    for path in paths:
        safe_path(path)
        mode = path.stat().st_mode
        access_mode = os.W_OK | (os.X_OK if stat.S_ISDIR(mode) else 0)
        writable = writable and bool(mode & 0o222) and os.access(str(path), access_mode)
    return {'repository': request['repository'], 'root': str(repo), 'git_dir': str(git),
            'branch': request['expected_branch'], 'head_sha': sha, 'config_sha256': config_hash,
            'index_sha256': hashlib.sha256(read(git / 'index')).hexdigest() if present(git / 'index') else None,
            'files': inventory(repo)}, writable


def seal(request, observed):
    plan = {'contract': CONTRACT, 'request': request, 'snapshot': observed,
            'authorized_state': {p: observed['files'].get(p) for p in request['authorized_files']}}
    plan['digest'] = digest(plan)
    return plan


def evidence(plan, writable):
    request = plan['request']
    external = len(request['operations']) > 1 or request['commit']['signing'] == 'required' or bool(request['required_ci']) or request['base_sha'] != request['head_sha']
    status = 'BLOCKED' if not writable else ('PARTIAL' if external else 'READY')
    return {'contract': CONTRACT, 'status': status, 'plan_digest': plan['digest'],
            'reasons': ['GIT_WRITE_BLOCKED'] if not writable else (['EXTERNAL_PRECONDITIONS_UNVERIFIED'] if external else []),
            'git_write': 'ACCESS_CHECK_PASSED' if writable else 'GIT_WRITE_BLOCKED',
            'authorization': 'UNKNOWN', 'remote_ref': 'UNKNOWN', 'ci': 'UNKNOWN',
            'signing': 'UNKNOWN' if request['commit']['signing'] == 'required' else 'NOT_REQUESTED',
            'base_ancestry': 'UNKNOWN', 'future_write_success': 'UNKNOWN', 'mutations': 'NONE'}


def plan(repo, request):
    validate_request(request)
    observed, writable = snapshot(repo, request)
    result = seal(request, observed)
    return result, evidence(result, writable)


def verify(repo, value):
    keys(value, 'contract request snapshot authorized_state digest')
    require(value['contract'] == CONTRACT, 'UNSUPPORTED_CONTRACT')
    require(value['digest'] == digest({k: v for k, v in value.items() if k != 'digest'}), 'DIGEST_MISMATCH')
    expected, result = plan(repo, value['request'])
    require(expected == value, 'SNAPSHOT_CHANGED')
    return result


def main(argv):
    try:
        require(len(argv) == 5 and argv[0] in ('plan', 'verify', 'report')
                and argv[1] == '--repo' and argv[3] == '--input', 'USAGE')
        command, repo, source = argv[0], argv[2], argv[4]
        value = load(source)
        if command == 'plan':
            value, result = plan(repo, value)
            output = {'plan': value, 'evidence': result}
        else:
            # Accept the exact stdout of plan, or its standalone plan member.
            if isinstance(value, dict) and set(value) == {'plan', 'evidence'}:
                value = value['plan']
            result = verify(repo, value)
            output = result
        print(json.dumps(output, sort_keys=True, ensure_ascii=True, allow_nan=False))
        return {'READY': 0, 'PARTIAL': 1, 'BLOCKED': 2, 'UNKNOWN': 3}[result['status']]
    except Rejected as error:
        code = str(error)
        print(json.dumps({'contract': CONTRACT, 'status': 'BLOCKED', 'reasons': [code], 'mutations': 'NONE'}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, configparser.Error, RecursionError):
        print(json.dumps({'contract': CONTRACT, 'status': 'UNKNOWN', 'reasons': ['UNREADABLE_OR_INVALID_INPUT'], 'mutations': 'NONE'}))
        return 3
