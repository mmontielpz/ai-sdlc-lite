"""AI-SDLC Lite V2 command line (stdlib only, no network).

Commands:
  verify | baseline | seal | codes   pass straight through to scripts/verify_scope.py (same stdout, stderr, exit codes)
  doctor                              read-only environment and framework check; unknown facts are UNKNOWN
  status [--repo PATH]                read-only description of a repository's HEAD and active task pointer

Boundaries (honest):
  * This CLI wraps the verifier; it adds no verification logic. The verifier detects after the fact and
    prevents nothing. This CLI does not sandbox, authorize or stop an agent, and claims no native enforcement.
  * Passthrough never executes commands named in a result contract (the verifier does not either).
  * doctor and status write nothing and use no network. status never invokes Git, because Git configuration
    can name programs to run; it reads a few plain files instead.
  * status treats every byte of the target repository's Git metadata as untrusted. It prints only a branch name
    that passed strict ref-name validation and an object id that is 40 or 64 lowercase hex digits. Anything else
    is reported as UNKNOWN, and file contents are never echoed. Reads are limited to regular, non-symlink files
    below a validated Git directory. Externally sourced display text (branch names, task pointers) containing
    control, format, surrogate, private-use, line or paragraph separator, replacement or non-ASCII space characters
    is never printed; look-alike letters from different scripts are not detected.
"""

import json
import os
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path

__all__ = ['main', 'ROOT', 'VERIFIER']

# Resolved from this module's location, never from the current working directory.
ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / 'scripts' / 'verify_scope.py'
PASSTHROUGH = ('verify', 'baseline', 'seal', 'codes')
REQUIRED_FILES = (
    'scripts/verify_scope.py',
    'RESULT_CONTRACT.md',
    'AGENTS.md',
    'WORKFLOW.md',
    'templates/RESULT.md',
    '.agents/skills/ai-sdlc-lite/SKILL.md',
)
MIN_PYTHON = (3, 9)
USAGE = (
    'usage: python3 -m ai_sdlc <command> [args]\n'
    '  verify|baseline|seal|codes   run scripts/verify_scope.py with the same arguments\n'
    '  doctor                       read-only environment and framework check\n'
    '  status [--repo PATH]         read-only HEAD and active-task report\n'
)
HEX = frozenset('0123456789abcdef')
BAD_REF_CHARS = frozenset(' \\:?[^~*\x7f')
# Unicode general categories that can drive a terminal or spoof output: control, format (zero-width, bidi, tags),
# surrogate, private use, line and paragraph separators, and space separators (checked separately for U+0020).
UNSAFE_CATEGORIES = frozenset(('Cc', 'Cf', 'Cs', 'Co', 'Zl', 'Zp', 'Zs'))


def _err(text):
    sys.stderr.write(text + '\n')


def _passthrough(command, rest):
    """Run the existing verifier unchanged; stdout and stderr are inherited, so nothing is rewritten."""
    if not sys.executable:
        _err('ai_sdlc: BLOCKED: no Python interpreter path is available (sys.executable is empty).')
        return 2
    if VERIFIER.is_symlink() or not VERIFIER.is_file():
        _err(f'ai_sdlc: BLOCKED: verifier not found as a regular file: {VERIFIER}')
        return 2
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        completed = subprocess.run([sys.executable, '-B', str(VERIFIER), command, *rest])
    except OSError as exc:
        _err(f'ai_sdlc: BLOCKED: could not start the verifier: {exc.__class__.__name__}')
        return 2
    if completed.returncode < 0:
        _err(f'ai_sdlc: BLOCKED: verifier ended by signal {-completed.returncode}.')
        return 2
    return completed.returncode


def _git_version():
    """Return the first line of `git --version`, or None. Reads no repository, so no repository config can run."""
    import shutil
    exe = shutil.which('git')
    if not exe:
        return None
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    try:
        out = subprocess.run([exe, '--version'], capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    line = out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout.strip() else ''
    return line or None


def _doctor():
    failed = False
    lines = []

    def row(label, state, detail=''):
        lines.append(f'{label}: {state}' + (f' ({detail})' if detail else ''))

    version = '.'.join(str(part) for part in sys.version_info[:3])
    if sys.version_info[:2] >= MIN_PYTHON:
        row('python', 'OK', f'{version}; minimum {MIN_PYTHON[0]}.{MIN_PYTHON[1]}')
    else:
        failed = True
        row('python', 'FAIL', f'{version}; minimum {MIN_PYTHON[0]}.{MIN_PYTHON[1]}')
    git = _git_version()
    if git:
        row('git', 'OK', git)
    else:
        failed = True
        row('git', 'FAIL', 'not found or not runnable')
    for name in REQUIRED_FILES:
        path = ROOT / name
        if path.is_symlink():
            failed = True
            row(f'file {name}', 'FAIL', 'is a symlink')
        elif path.is_file():
            row(f'file {name}', 'OK')
        else:
            failed = True
            row(f'file {name}', 'FAIL', 'missing')
    row('framework root', 'INFO', str(ROOT))
    for label in ('native agent sandbox and permissions', 'agent skill discovery', 'network policy',
                  'platform qualification (macOS, Windows)', 'live agent qualification'):
        row(label, 'UNKNOWN', 'not inspected; this tool does not establish it')
    lines.append('note: doctor reads files and runs `git --version` only. It enforces nothing and grants no authority.')
    lines.append('RESULT: ' + ('BLOCKED' if failed else 'READY (required checks only; UNKNOWN items remain UNKNOWN)'))
    sys.stdout.write('\n'.join(lines) + '\n')
    return 2 if failed else 0


# ---- untrusted Git metadata: strict validation and contained reads ---------------------------------------------

def _oid_ok(text):
    """A Git object id: exactly 40 (SHA-1) or 64 (SHA-256) lowercase hexadecimal characters, nothing else."""
    return isinstance(text, str) and len(text) in (40, 64) and all(c in HEX for c in text)


def _ref_ok(ref):
    """A safe full ref name such as refs/heads/main. Rejects absolute, traversal and malformed names."""
    if not isinstance(ref, str) or not ref.startswith('refs/') or len(ref) > 256 or '@{' in ref:
        return False
    for part in ref.split('/'):
        if part in ('', '.', '..') or part.startswith('.') or part.endswith('.lock'):
            return False
        if any(ord(c) < 32 or c in BAD_REF_CHARS for c in part) or not _display_safe(part):
            return False
    return True


def _display_safe(text):
    """True if `text` may be printed: no control, format, surrogate, private-use, separator or replacement
    characters. Ordinary text in any script is allowed, and so is the plain ASCII space (other spaces are not)."""
    if not isinstance(text, str):
        return False
    for char in text:
        if char == ' ':
            continue
        if char == '\ufffd' or unicodedata.category(char) in UNSAFE_CATEGORIES:
            return False
    return True


def _safe_dir(path):
    """A real directory that is not a symlink (checked with lstat, never following links)."""
    try:
        return stat.S_ISDIR(os.lstat(str(path)).st_mode)
    except OSError:
        return False


def _read_regular(base, *parts, limit=4096):
    """Read up to `limit` bytes (decoded) of the regular file base/parts, or None.

    Every component below `base` must be a real directory or, for the last one, a regular file: symlinks are
    refused at every level, FIFOs and devices are refused, and the resolved path must stay inside `base`.
    `parts` must be plain names (never separators, '.' or '..').
    """
    if not parts or any((not p) or p in ('.', '..') or '/' in p or '\\' in p or '\x00' in p for p in parts):
        return None
    try:
        current = Path(base)
        for part in parts[:-1]:
            current = current / part
            if not _safe_dir(current):
                return None
        target = current / parts[-1]
        if not stat.S_ISREG(os.lstat(str(target)).st_mode):
            return None
        real_base = os.path.realpath(str(base))
        real_target = os.path.realpath(str(target))
        if os.path.commonpath([real_base, real_target]) != real_base:
            return None
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(str(target), flags)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return None
            data = os.read(fd, limit)
        finally:
            os.close(fd)
    except (OSError, ValueError):
        return None
    return data.decode('utf-8', errors='replace')


def _first_line(text):
    """First line, split on LF only and trimmed of ASCII blanks only. str.splitlines()/strip() would treat Unicode
    separators (U+0085, U+2028, U+3000 ...) as line breaks or padding and silently shorten an unsafe name."""
    return (text or '').split('\n', 1)[0].strip(' \t\r')


def _norm(path):
    return Path(os.path.normpath(str(path)))


def _locate_git(repo):
    """Return (git_dir, common_dir) after structural validation, or None (UNKNOWN). Never invokes Git.

    Accepts a `.git` directory, or a `.git` pointer file (`gitdir: PATH`, as used by linked worktrees and
    submodules). The target must itself be a real directory that looks like a Git directory. A `commondir` file is
    honoured only for the exact linked-worktree layout <common>/worktrees/<name> with a matching back-link.
    """
    dot = repo / '.git'
    try:
        mode = os.lstat(str(dot)).st_mode
    except OSError:
        return None
    if stat.S_ISDIR(mode):
        git_dir = dot
    elif stat.S_ISREG(mode):
        line = _first_line(_read_regular(repo, '.git', limit=1024))
        if not line.startswith('gitdir:'):
            return None
        target = line[len('gitdir:'):].strip(' ')
        if not target or any(ord(c) < 32 or ord(c) == 127 for c in target):
            return None
        pointed = Path(target)
        git_dir = _norm(pointed if pointed.is_absolute() else repo / pointed)
    else:
        return None
    if not _safe_dir(git_dir) or _read_regular(git_dir, 'HEAD', limit=1) is None:
        return None
    common_text = _read_regular(git_dir, 'commondir', limit=1024)
    if common_text is None:
        return (git_dir, git_dir) if _safe_dir(git_dir / 'objects') else None
    common = _norm(git_dir / _first_line(common_text))
    if (git_dir.parent.name != 'worktrees' or common != _norm(git_dir.parent.parent) or not _safe_dir(common)
            or not _safe_dir(common / 'objects')):
        return None
    backlink = _first_line(_read_regular(git_dir, 'gitdir', limit=1024))
    if not backlink or os.path.realpath(backlink) != os.path.realpath(str(repo / '.git')):
        return None
    return git_dir, common


def _resolve_ref(git_dir, common, ref):
    """Resolve a validated ref to a validated object id using loose files, then packed-refs; else None."""
    parts = ref.split('/')
    for base in (git_dir, common) if git_dir != common else (git_dir,):
        text = _read_regular(base, *parts, limit=256)
        if text is not None:
            value = _first_line(text)
            return value if _oid_ok(value) else None
    packed = _read_regular(common, 'packed-refs', limit=1 << 20) or ''
    for line in packed.split('\n'):
        if line.startswith(('#', '^')):
            continue
        fields = line.rstrip('\r').split(' ')
        if len(fields) == 2 and fields[1] == ref and _oid_ok(fields[0]):
            return fields[0]
    return None


def _safe_pointer(value):
    """A repository-relative path text that is safe to print: no absolute form, traversal or control characters."""
    if not isinstance(value, str) or not value or len(value) > 512:
        return None
    if value[0] in '/\\' or (len(value) > 1 and value[1] == ':'):
        return None
    if not _display_safe(value) or value != value.strip(' '):
        return None
    if any(part in ('', '.', '..') for part in value.replace('\\', '/').split('/')):
        return None
    return value


def _emit(text):
    """Write to stdout; if the stream cannot encode the (already validated) text, write an ASCII-escaped form.
    Never raises with the text in an error message."""
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode('ascii', 'backslashreplace').decode('ascii'))


def _status(rest):
    repo = ROOT
    args = list(rest)
    if args:
        if len(args) == 2 and args[0] == '--repo':
            repo = Path(args[1])
        else:
            _err('usage: python3 -m ai_sdlc status [--repo PATH]')
            return 2
    repo = repo.resolve()
    shown = str(repo) if _display_safe(str(repo)) else str(repo).encode('unicode_escape').decode('ascii')
    lines = [f'repository: {shown}']
    located = _locate_git(repo) if repo.is_dir() else None
    if located is None:
        lines.append('git: UNKNOWN (no safely readable Git directory; Git was not invoked)')
    else:
        git_dir, common = located
        line = _first_line(_read_regular(git_dir, 'HEAD', limit=512))
        branch = head = None
        if line.startswith('ref:'):
            ref = line[len('ref:'):].strip(' ')
            if _ref_ok(ref):
                branch = ref[len('refs/heads/'):] if ref.startswith('refs/heads/') else ref
                head = _resolve_ref(git_dir, common, ref)
        elif _oid_ok(line):
            branch, head = '(detached)', line
        lines.append(f'branch: {branch if branch else "UNKNOWN (HEAD is malformed or not safe to follow)"}')
        lines.append(f'head: {head if head else "UNKNOWN"}')
    lines.append('working tree state: UNKNOWN (not inspected; Git is not invoked)')
    folder, context = repo / '.ai-sdlc-lite', repo / '.ai-sdlc-lite' / 'task-context.json'
    if folder.is_symlink() or context.is_symlink():
        lines.append('active task: UNKNOWN (task-context path is a symlink; not read)')
    elif context.is_file():
        text = _read_regular(repo, '.ai-sdlc-lite', 'task-context.json', limit=1 << 16)
        try:
            record = json.loads(text) if text is not None else None
        except ValueError:
            record = None
        if isinstance(record, dict):
            for key in ('contract', 'checklist', 'result'):
                value = _safe_pointer(record.get(key))
                lines.append(f'active task {key}: {value if value else "UNKNOWN"}')
            lines.append('task approval: UNVERIFIED (a pointer is not an approval)')
        else:
            lines.append('active task: UNKNOWN (task-context file is not a JSON object)')
    else:
        lines.append('active task: NOT INITIALIZED (non-blocking)')
    _emit('\n'.join(lines) + '\n')
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.stderr.write(USAGE)
        return 2
    command, rest = args[0], args[1:]
    if command in ('-h', '--help', 'help'):
        sys.stdout.write(USAGE)
        return 0
    if command in PASSTHROUGH:
        return _passthrough(command, rest)
    if command == 'doctor':
        if rest:
            _err('usage: python3 -m ai_sdlc doctor')
            return 2
        return _doctor()
    if command == 'status':
        return _status(rest)
    _err(f'ai_sdlc: unknown command {command!r}')
    sys.stderr.write(USAGE)
    return 2
