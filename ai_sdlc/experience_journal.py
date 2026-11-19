"""Local append-only Experience journal (JSONL, one canonical event per line).

EXPERIMENTAL, offline, stdlib only. The journal is written only to an explicit path chosen by the caller;
there is no default location, nothing is captured implicitly, and no Lite command reads it.

Safety properties: every path component is opened without following symlinks (descriptor-relative, like
ai_sdlc/initializer.py); a journal inside a Git work tree is refused unless explicitly allowed; appends
take an exclusive advisory lock, fully validate the existing journal, then write exactly one line; any
malformed, truncated, oversized or chain-broken journal is refused and never repaired or rewritten.
Integrity checks detect accidental or naive modification; they do not authenticate authorship.
"""

from collections import namedtuple
import errno
import os
import stat
import time

from . import experience_events as ev
from .experience_events import ExperienceError

Summary = namedtuple('Summary', 'count run_id head')
LOCK_SECONDS = 2.0
_O_NOFOLLOW = getattr(os, 'O_NOFOLLOW', 0)
_O_DIRECTORY = getattr(os, 'O_DIRECTORY', 0)
_O_NONBLOCK = getattr(os, 'O_NONBLOCK', 0)  # never block opening a FIFO; the type check follows the open


def _supported():
    return bool(_O_NOFOLLOW and _O_DIRECTORY and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
                and os.unlink in os.supports_dir_fd)


def _fcntl():
    try:
        import fcntl
    except ImportError:
        raise ExperienceError('unsupported_platform') from None
    return fcntl


def _lock(fd, shared):
    fcntl = _fcntl()
    flag = (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB
    deadline = time.monotonic() + LOCK_SECONDS
    while True:
        try:
            fcntl.flock(fd, flag)
            return
        except OSError as error:
            if error.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK) or time.monotonic() >= deadline:
                raise ExperienceError('lock_failed') from None
            time.sleep(0.002)


def _unlock(fd):
    try:
        _fcntl().flock(fd, _fcntl().LOCK_UN)
    except (OSError, ExperienceError):
        pass


def _split(path):
    if not isinstance(path, str) or not path or '\x00' in path or '\\' in path:
        raise ExperienceError('journal_invalid_path')
    if '..' in path.split('/'):
        raise ExperienceError('journal_invalid_path')
    absolute = os.path.abspath(path)
    parts = [part for part in absolute.split('/') if part]
    if not parts or parts[-1] in ('.', '..'):
        raise ExperienceError('journal_invalid_path')
    return parts[:-1], parts[-1]


def _has_git(fd):
    try:
        os.stat('.git', dir_fd=fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def _open_parent(path, *, allow_in_repo, enforce_repo):
    """Open the journal's parent directory without following any symlink; refuse a Git work tree."""
    directories, leaf = _split(path)
    fd = os.open('/', os.O_RDONLY | _O_DIRECTORY)
    try:
        in_repo = _has_git(fd)
        for part in directories:
            try:
                child = os.open(part, os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW, dir_fd=fd)
            except OSError:
                raise ExperienceError('journal_invalid_path') from None
            os.close(fd)
            fd = child
            in_repo = in_repo or _has_git(fd)
        if enforce_repo and in_repo and not allow_in_repo:
            raise ExperienceError('journal_in_repo')
        return fd, leaf
    except BaseException:
        os.close(fd)
        raise


def _check_regular(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ExperienceError('journal_invalid_path')
    return info


def _read_all(fd):
    size = os.fstat(fd).st_size
    if size > ev.MAX_JOURNAL_BYTES:
        raise ExperienceError('journal_full')
    chunks, remaining = [], ev.MAX_JOURNAL_BYTES + 1
    while remaining:
        chunk = os.read(fd, min(remaining, 65536))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    data = b''.join(chunks)
    if len(data) > ev.MAX_JOURNAL_BYTES:
        raise ExperienceError('journal_full')
    return data


def parse_journal(data):
    """Validate a whole journal. Returns (events, Summary). Raises ExperienceError(code, line=n)."""
    if not data:
        return [], Summary(0, None, None)
    if not data.endswith(b'\n'):
        raise ExperienceError('truncated_journal', line=data.count(b'\n') + 1)
    lines = data[:-1].split(b'\n')
    if len(lines) > ev.MAX_EVENTS:
        raise ExperienceError('journal_full')
    events, run_id, previous, seen = [], None, None, set()
    for number, raw in enumerate(lines, 1):
        try:
            if not raw:
                raise ExperienceError('malformed_json')
            event = ev.loads_strict(raw)
            if run_id is None and isinstance(event, dict):
                run_id = event.get('run_id')
            ev.validate_event(event, expected_seq=number, previous_id=previous, run_id=run_id)
            if ev.canonical_json(event) != raw:
                raise ExperienceError('schema_invalid', field='event.canonical-form')
            if event['event_id'] in seen:
                raise ExperienceError('chain_broken', field='event.event_id')
        except ExperienceError as error:
            error.line = number
            raise
        seen.add(event['event_id'])
        events.append(event)
        previous = event['event_id']
    return events, Summary(len(events), events[0]['run_id'], events[-1]['event_id'])


def validate_journal(path):
    """Read-only validation under a shared lock. Never writes, repairs or returns event content."""
    if not _supported():
        raise ExperienceError('unsupported_platform')
    parent, leaf = _open_parent(path, allow_in_repo=True, enforce_repo=False)
    try:
        try:
            fd = os.open(leaf, os.O_RDONLY | _O_NOFOLLOW | _O_NONBLOCK, dir_fd=parent)
        except FileNotFoundError:
            raise ExperienceError('journal_missing') from None
        except OSError:
            raise ExperienceError('journal_invalid_path') from None
        try:
            _check_regular(fd)
            _lock(fd, shared=True)
            try:
                return parse_journal(_read_all(fd))[1]
            except OSError:
                raise ExperienceError('journal_io') from None
            finally:
                _unlock(fd)
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def _default_run_id(recorded_at):
    return 'run-' + recorded_at[:10].replace('-', '') + '-1'


class _Stale(Exception):
    """Internal: the file we locked is no longer the one the path names; reopen and retry."""


def _same_file(parent, leaf, fd):
    try:
        named = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return False
    held = os.fstat(fd)
    return (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino)


def _remove_if_still_empty(parent, leaf, fd):
    """Remove a journal this call created, but only while holding its exclusive lock (so no other writer
    can be using it), while it is still empty, and while the path still names this very file."""
    fcntl = _fcntl()
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return  # someone else is using it: leave the (valid, empty) file alone
    try:
        if os.fstat(fd).st_size == 0 and _same_file(parent, leaf, fd):
            os.unlink(leaf, dir_fd=parent)
    except OSError:
        pass


def _open_for_append(parent, leaf, fields, run_id, recorded_at):
    """Open the journal for append, creating it (exclusively, 0600) only after the first event validated."""
    for _attempt in range(3):
        try:
            return os.open(leaf, os.O_RDWR | os.O_APPEND | _O_NOFOLLOW | _O_NONBLOCK, dir_fd=parent), False
        except FileNotFoundError:
            ev.build_event(fields, run_id=run_id or _default_run_id(recorded_at), seq=1, prev=None,
                           recorded_at=recorded_at)
            try:
                return os.open(leaf, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW, 0o600,
                               dir_fd=parent), True
            except FileExistsError:
                continue
        except OSError:
            raise ExperienceError('journal_invalid_path') from None
    raise ExperienceError('journal_invalid_path')


def _append_locked(parent, leaf, fd, created, fields, run_id, recorded_at):
    _check_regular(fd)
    _lock(fd, shared=False)
    if not _same_file(parent, leaf, fd):
        raise _Stale()  # unlinked or replaced while we waited: never write to an orphaned file
    if created:
        os.fsync(parent)  # make the new directory entry durable
    data = _read_all(fd)
    events, summary = parse_journal(data)
    if len(events) >= ev.MAX_EVENTS:
        raise ExperienceError('journal_full')
    if events and run_id is not None and run_id != summary.run_id:
        raise ExperienceError('chain_broken', field='event.run_id')
    chosen = summary.run_id if events else (run_id or _default_run_id(recorded_at))
    event = ev.build_event(fields, run_id=chosen, seq=len(events) + 1, prev=summary.head, recorded_at=recorded_at)
    line = ev.canonical_json(event) + b'\n'
    if len(data) + len(line) > ev.MAX_JOURNAL_BYTES:
        raise ExperienceError('journal_full')
    try:
        written = os.write(fd, line)
        if written != len(line):
            raise OSError(errno.EIO, 'short write')
        os.fsync(fd)
    except OSError:
        try:  # undo only our own partial write
            os.ftruncate(fd, len(data))
            os.fsync(fd)
        except OSError:
            pass
        raise ExperienceError('journal_io') from None
    return event


def append_event(path, fields, *, clock=ev.default_clock, run_id=None, allow_in_repo=False):
    """Append one validated event. Returns the event. On any refusal nothing is appended; a journal file
    created by this call is removed again only if it is still empty and no other writer holds it."""
    if not _supported():
        raise ExperienceError('unsupported_platform')
    _fcntl()
    recorded_at = clock()  # read exactly once per append
    if not isinstance(recorded_at, str) or not ev.TIMESTAMP.fullmatch(recorded_at):
        raise ExperienceError('schema_invalid', field='event.recorded_at')  # before any path or run_id derivation
    parent, leaf = _open_parent(path, allow_in_repo=allow_in_repo, enforce_repo=True)
    try:
        for _attempt in range(4):
            fd, created = _open_for_append(parent, leaf, fields, run_id, recorded_at)
            try:
                try:
                    return _append_locked(parent, leaf, fd, created, fields, run_id, recorded_at)
                except _Stale:
                    continue
                except BaseException:
                    if created:
                        _remove_if_still_empty(parent, leaf, fd)
                    raise
                finally:
                    _unlock(fd)
            except OSError:
                raise ExperienceError('journal_io') from None
            finally:
                os.close(fd)
        raise ExperienceError('journal_io')  # the path kept changing under us
    finally:
        os.close(parent)
