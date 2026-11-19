"""Offline, provider-neutral bundle initialization. No target code or Git is run.

Descriptor-relative traversal refuses symlinks at every component. The destination
must be quiescent: this is not confinement against privileged processes or hostile
concurrent directory renames. No repair, removal, overwrite or upgrade is offered.
"""

from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

from ._root import framework_root

ROOT = framework_root()
USAGE = ('usage: python3 -B -m ai_sdlc init --repo PATH [--target agents|claude-code] [--dry-run | --apply | --check]\n'
         'Default: read-only preview of the agents target (.agents/skills/ai-sdlc-lite).\n'
         '--target claude-code selects .claude/skills/ai-sdlc-lite; the bundle is identical.\n'
         '--apply creates only the offline Skill bundle.\n'
         '--check verifies local files only; no provider is probed or authorized.\n'
         'Optional EXPERIMENTAL capture (with --apply or --check only): --journal FILE --repo-classification C\n'
         '[--run-id R] [--allow-in-repo] appends one Experience event after the result is final; a journal\n'
         'failure adds one stderr line "JOURNAL: <code>" and never changes the exit code.\n')
MAX_MANIFEST = 1 << 20
MAX_ENTRIES = 20000


class Refused(Exception):
    """Stable reason identifiers only; never echo untrusted file contents."""


def _installer():
    # Absolute reviewed source, independent of cwd, PYTHONPATH and target contents.
    path = ROOT / 'scripts' / 'install_skill.py'
    if path.is_symlink() or not path.is_file():
        raise Refused('framework_unavailable')
    spec = importlib.util.spec_from_file_location('_ai_sdlc_init_installer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _supported():
    return (all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK'))
            and all(fn in os.supports_dir_fd for fn in (os.open, os.mkdir, os.stat))
            and os.listdir in os.supports_fd)


@contextmanager
def _directory(base, parts, create=False):
    """Open below a pinned directory; never follow a path component symlink."""
    fd = os.dup(base)
    try:
        for part in parts:
            if not part or part in ('.', '..') or '/' in part or '\\' in part or '\x00' in part:
                raise Refused('unsafe_path')
            if create:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _read(fd, name, limit):
    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
        raise Refused('unsafe_file')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    child = os.open(name, flags, dir_fd=fd)
    try:
        info = os.fstat(child)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise Refused('unsafe_file')
        chunks, remaining = [], limit + 1
        while remaining:
            chunk = os.read(child, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b''.join(chunks)
        if len(data) > limit:
            raise Refused('oversized_file')
        return data
    finally:
        os.close(child)


def _target(value):
    if not value or '\\' in value or '\x00' in value or '..' in value.split('/'):
        raise Refused('unsafe_path')
    root = Path(os.path.abspath(value))
    if root == ROOT or root.is_relative_to(ROOT) or ROOT.is_relative_to(root):
        raise Refused('framework_overlap')
    return root


def _validate_git(fd):
    # Deliberately exclude pointer files, worktrees, submodules and external metadata.
    with _directory(fd, ('.git',)) as git:
        with _directory(git, ('objects',)), _directory(git, ('refs',)):
            head = _read(git, 'HEAD', 512).decode('ascii').strip()
            if not (head.startswith('ref: refs/heads/') or
                    (len(head) in (40, 64) and all(c in '0123456789abcdef' for c in head))):
                raise Refused('invalid_git_root')
        if 'commondir' in os.listdir(git):
            raise Refused('external_git_metadata')


def _inventory(fd, prefix='', entries=None):
    if entries is None:
        entries = {}
    if prefix.count('/') > 32:
        raise Refused('inventory_limit')
    for name in sorted(os.listdir(fd)):
        if len(entries) >= MAX_ENTRIES:
            raise Refused('inventory_limit')
        rel = prefix + name
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            entries[rel + '/'] = None
            with _directory(fd, (name,)) as child:
                _inventory(child, rel + '/', entries)
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            entries[rel] = None
        else:
            raise Refused('unsafe_file')
    return entries


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused('duplicate_manifest_key')
        result[key] = value
    return result


def _validate_existing(fd, content, hashes, installer):
    actual = set(_inventory(fd))
    expected = set(content)
    for name in content:
        expected.update(p.as_posix() + '/' for p in Path(name).parents if p != Path('.'))
    if actual != expected:
        raise Refused('installation_inventory_conflict')
    raw = _read(fd, installer.MANIFEST, MAX_MANIFEST)
    record = json.loads(raw, object_pairs_hook=_unique)
    if (not isinstance(record, dict) or set(record) != {'format', 'files'}
            or type(record['format']) is not int):
        raise Refused('invalid_manifest')
    if installer.manifest_files(record) != hashes:
        raise Refused('installation_version_conflict')
    for name, data in sorted(content.items()):
        with _directory(fd, Path(name).parts[:-1]) as parent:
            if _read(parent, Path(name).name, max(len(data), MAX_MANIFEST if name == installer.MANIFEST else 0)) != data:
                raise Refused('installation_content_conflict')


def _existing(fd, content, hashes, installer, skill):
    try:
        # Probe ancestors separately, so a file disappearing during validation
        # cannot turn an incomplete installation into an absent destination.
        with _directory(fd, skill.parts[:-1]):
            pass
    except FileNotFoundError:
        return False
    with _directory(fd, skill.parts[:-1]) as parent:
        try:
            os.stat(skill.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        with _directory(parent, (skill.name,)) as destination:
            _validate_existing(destination, content, hashes, installer)
    return True


def _write_file(fd, name, data):
    parts = Path(name).parts
    with _directory(fd, parts[:-1], create=True) as parent:
        child = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o644, dir_fd=parent)
        with os.fdopen(child, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())


def _apply(fd, content, installer, skill):
    with _directory(fd, skill.parts[:-1], create=True) as parent:
        # A destination appearing after preview is a conflict, even if empty.
        os.mkdir(skill.name, mode=0o755, dir_fd=parent)
        with _directory(parent, (skill.name,)) as destination:
            installer.write_bundle(content, lambda name, data: _write_file(destination, name, data))


def _journal_code(error):
    code = getattr(error, 'code', None)
    if isinstance(code, str) and code and code.replace('_', '').isalpha() and code == code.lower():
        return code
    return 'journal_io'


def _record(journal, target, outcome):
    """Append one Experience event for a finished init. Any Exception becomes one stderr line; the exit code
    of init is never touched. The Experience modules are imported only here, only when --journal was given."""
    try:
        from . import experience
        experience.record_install(journal['path'], journal['classification'], journal['run_id'],
                                  journal['allow_in_repo'], target, outcome)
    except Exception as error:
        sys.stderr.write('JOURNAL: %s\n' % _journal_code(error))


def _parse(args):
    """Returns (repo, mode, target, journal) or None for a usage error. `journal` is None without --journal."""
    repo, mode, seen, target = None, 'preview', set(), 'agents'
    extra = {}
    while args:
        flag = args.pop(0)
        known = ('--repo', '--target', '--dry-run', '--apply', '--check',
                 '--journal', '--repo-classification', '--run-id', '--allow-in-repo')
        if flag in seen or flag not in known:
            return None
        seen.add(flag)
        if flag == '--repo':
            if not args or args[0].startswith('--'):
                return None
            repo = args.pop(0)
        elif flag == '--target':
            if not args or args[0] not in ('agents', 'claude-code'):
                return None
            target = args.pop(0)
        elif flag in ('--journal', '--repo-classification', '--run-id'):
            if not args or args[0].startswith('--'):
                return None
            extra[flag] = args.pop(0)
        elif flag == '--allow-in-repo':
            extra[flag] = True
        else:
            if len(seen & {'--dry-run', '--apply', '--check'}) > 1:
                return None
            mode = flag[2:]
    if repo is None:
        return None
    journal = None
    if extra:
        if '--journal' not in extra or '--repo-classification' not in extra or mode not in ('apply', 'check'):
            return None
        from . import experience  # lazy: only when a journal option was given
        if not experience.check_capture_args(extra['--repo-classification'], extra.get('--run-id')):
            return None
        journal = {'path': extra['--journal'], 'classification': extra['--repo-classification'],
                   'run_id': extra.get('--run-id'), 'allow_in_repo': bool(extra.get('--allow-in-repo'))}
    return repo, mode, target, journal


def _execute(repo, mode, target):
    """The unchanged init logic. Returns (exit code, outcome) where outcome describes the final result."""
    started = False
    outcome = None
    try:
        if not _supported():
            raise Refused('unsupported_filesystem_primitives')
        root = _target(repo)
        installer = _installer()
        skill = installer.SKILL_TARGETS[target]
        content, hashes = installer.bundle_content()
        anchor = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            with _directory(anchor, root.parts[1:]) as fd:
                _validate_git(fd)
                exists = _existing(fd, content, hashes, installer, skill)
                if mode == 'check' and not exists:
                    raise Refused('installation_missing')
                print('AI-SDLC INIT 1')
                print('repository: ' + json.dumps(str(root), ensure_ascii=True))
                print('working tree state: UNKNOWN (not inspected)')
                for name, data in sorted(content.items()):
                    rel = (skill / name).as_posix()
                    print('%s %s sha256=%s' % ('UNCHANGED' if exists else 'CREATE',
                                              json.dumps(rel, ensure_ascii=True), installer.digest(data)))
                print('Provider discovery, permissions and task approval: UNVERIFIED')
                sys.stdout.flush()
                result = 'PREVIEW'
                if mode == 'check':
                    print('RESULT: CHECK_OK')
                    result = 'CHECK_OK'
                elif exists:
                    print('RESULT: UNCHANGED')
                    result = 'UNCHANGED'
                elif mode == 'apply':
                    started = True
                    _apply(fd, content, installer, skill)
                    if not _existing(fd, content, hashes, installer, skill):
                        raise Refused('installation_missing')
                    print('RESULT: INITIALIZED')
                    result = 'INITIALIZED'
                else:
                    print('RESULT: PREVIEW')
                # Every success path above re-validated the installation byte for byte, manifest included.
                outcome = {'ok': True, 'result': result, 'file_count': len(content),
                           'manifest_sha256': installer.digest(content[installer.MANIFEST])}
        finally:
            os.close(anchor)
        return 0, outcome
    except Exception as error:
        # Never echo OS/JSON/installer messages: they may contain untrusted bytes.
        reason = str(error) if isinstance(error, Refused) else 'validation_or_io_failure'
        sys.stderr.write('RESULT: %s reason=%s\n' % ('PARTIAL' if started else 'BLOCKED', reason))
        return (1 if started else 2), {'ok': False, 'reason': reason, 'partial': started}


def main(argv):
    args = list(argv)
    if args in (['--help'], ['-h']):
        sys.stdout.write(USAGE)
        return 0
    parsed = _parse(args)
    if parsed is None:
        sys.stderr.write('BLOCKED: usage\n' + USAGE)
        return 2
    repo, mode, target, journal = parsed
    code, outcome = _execute(repo, mode, target)
    if journal is not None:
        _record(journal, target, outcome)
    return code
