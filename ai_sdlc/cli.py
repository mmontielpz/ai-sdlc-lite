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
"""

import json
import os
import subprocess
import sys
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
CONTEXT = Path('.ai-sdlc-lite') / 'task-context.json'
USAGE = (
    'usage: python3 -m ai_sdlc <command> [args]\n'
    '  verify|baseline|seal|codes   run scripts/verify_scope.py with the same arguments\n'
    '  doctor                       read-only environment and framework check\n'
    '  status [--repo PATH]         read-only HEAD and active-task report\n'
)


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


def _read_text(path, limit=4096):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as handle:
            return handle.read(limit)
    except OSError:
        return None


def _git_dir(repo):
    """Locate the git directory by reading plain files only (a directory, or a `gitdir:` pointer file)."""
    dot = repo / '.git'
    if dot.is_dir():
        return dot
    if dot.is_file():
        text = _read_text(dot) or ''
        if text.startswith('gitdir:'):
            target = Path(text[len('gitdir:'):].strip())
            return target if target.is_absolute() else (repo / target)
    return None


def _resolve_ref(git_dir, ref):
    text = _read_text(git_dir / ref)
    if text is None:
        common = _read_text(git_dir / 'commondir')
        if common:
            base = git_dir / common.strip()
            text = _read_text(base / ref)
            git_dir = base
    if text and text.strip():
        return text.strip().split()[0]
    packed = _read_text(git_dir / 'packed-refs', limit=1 << 20) or ''
    for line in packed.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == ref and not line.startswith('#'):
            return parts[0]
    return None


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
    lines = [f'repository: {repo}']
    git_dir = _git_dir(repo) if repo.is_dir() else None
    if git_dir is None:
        lines.append('git: UNKNOWN (no readable .git found; Git was not invoked)')
        branch = head = None
    else:
        text = (_read_text(git_dir / 'HEAD') or '').strip()
        if text.startswith('ref:'):
            ref = text[4:].strip()
            branch = ref[len('refs/heads/'):] if ref.startswith('refs/heads/') else ref
            head = _resolve_ref(git_dir, ref)
        elif len(text) in (40, 64) and all(c in '0123456789abcdef' for c in text):
            branch, head = '(detached)', text
        else:
            branch = head = None
        lines.append(f'branch: {branch if branch else "UNKNOWN"}')
        lines.append(f'head: {head if head else "UNKNOWN"}')
    lines.append('working tree state: UNKNOWN (not inspected; Git is not invoked)')
    context = repo / CONTEXT
    if any(part.is_symlink() for part in (repo / '.ai-sdlc-lite', context)):
        lines.append('active task: UNKNOWN (task-context path is a symlink; not read)')
    elif context.is_file():
        try:
            record = json.loads(_read_text(context, 1 << 16) or '')
        except ValueError:
            record = None
        if isinstance(record, dict):
            for key in ('contract', 'checklist', 'result'):
                value = record.get(key)
                lines.append(f'active task {key}: {value if isinstance(value, str) and value else "UNKNOWN"}')
            lines.append('task approval: UNVERIFIED (a pointer is not an approval)')
        else:
            lines.append('active task: UNKNOWN (task-context file is not a JSON object)')
    else:
        lines.append('active task: NOT INITIALIZED (non-blocking)')
    sys.stdout.write('\n'.join(lines) + '\n')
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
