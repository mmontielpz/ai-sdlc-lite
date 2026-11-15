"""Native local Git adapter and append-only execution journal (no remote operations).

Deny by default: a mutable operation runs only if it is allowlisted, the host
authorizer approves that exact operation, and the observed Git state still
matches after approval. Git is invoked without a shell, from fixed argument
templates; callers never supply Git arguments. Approval, journal storage outside
the checkout and exclusive repository access are trusted host responsibilities.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import time

from . import delivery as d

JOURNAL_CONTRACT = 'ai-sdlc-native-git-journal/1'
OPERATIONS = ('create_branch', 'stage', 'commit')
GENESIS = '0' * 64
LINE_LIMIT = 64 * 1024
JOURNAL_LIMIT = 64 * 1024 * 1024
MAX_FILES = 1000
MODES = ('100644', '100755')
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:@-]{0,127}')
HEX64 = re.compile(r'[0-9a-f]{64}')
REASON = re.compile(r'[A-Z][A-Z0-9_]{0,63}')
PROVENANCE_TRAILER = 'AI-SDLC-Provenance'
HEX32 = re.compile(r'[0-9a-f]{32}')


def provenance_token(value):
    return isinstance(value, str) and HEX32.fullmatch(value) is not None


def ident(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None


def hex64(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def decoded(raw, encoding='utf-8'):
    """Decode Git output strictly. Bytes that do not decode are a rejected observation, never an exception."""
    try:
        return raw.decode(encoding)
    except UnicodeError:
        raise d.Rejected('GIT_OUTPUT_INVALID') from None


def shape(value, names):
    d.require(isinstance(value, dict) and set(value) == set(names.split()), 'JOURNAL_INVALID')


def branch_name(value):
    return d.text(value) and not value.startswith('-') and d.ref('refs/heads/' + value)


def path_ok(value):
    return d.relative(value) and not value.startswith('-') and value.rsplit('/', 1)[-1] != '.gitattributes'


def clean(value, depth=0):
    """Journal values are plain bounded JSON; no free-form blobs, so no secret carriers."""
    d.require(depth < 8, 'JOURNAL_INVALID')
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        d.require(0 <= value < 2 ** 53, 'JOURNAL_INVALID')
    elif isinstance(value, str):
        d.require(d.text(value), 'JOURNAL_INVALID')
    elif isinstance(value, list):
        d.require(len(value) <= 2 * MAX_FILES, 'JOURNAL_INVALID')
        for item in value:
            clean(item, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            d.require(d.text(key), 'JOURNAL_INVALID')
            clean(item, depth + 1)
    else:
        raise d.Rejected('JOURNAL_INVALID')


def valid_state(state):
    shape(state, 'branch head_sha staged')
    d.require(branch_name(state['branch']) and d.oid(state['head_sha']) and isinstance(state['staged'], list)
              and len(state['staged']) <= MAX_FILES, 'JOURNAL_INVALID')
    for item in state['staged']:
        d.require(isinstance(item, list) and len(item) == 3 and path_ok(item[0]) and hex64(item[1])
                  and item[2] in MODES, 'JOURNAL_INVALID')
    d.require(state['staged'] == sorted(state['staged']), 'JOURNAL_INVALID')


def valid_files(files):
    d.require(isinstance(files, list) and 0 < len(files) <= MAX_FILES and files == sorted(files), 'JOURNAL_INVALID')
    for item in files:
        d.require(isinstance(item, list) and len(item) == 3 and path_ok(item[0]) and hex64(item[1])
                  and type(item[2]) is bool, 'JOURNAL_INVALID')
    d.require(len({item[0] for item in files}) == len(files), 'JOURNAL_INVALID')


def valid_params(operation, params):
    d.require(operation in OPERATIONS, 'JOURNAL_INVALID')
    if operation == 'create_branch':
        shape(params, 'name start_sha')
        d.require(branch_name(params['name']) and d.oid(params['start_sha']), 'JOURNAL_INVALID')
    elif operation == 'stage':
        shape(params, 'files')
        valid_files(params['files'])
    else:
        shape(params, 'message_sha256 message_length files')
        d.require(hex64(params['message_sha256']) and type(params['message_length']) is int
                  and 0 < params['message_length'] <= 4096, 'JOURNAL_INVALID')
        valid_files(params['files'])


def valid_intent(value):
    shape(value, 'operation repository params')
    d.require(d.text(value['repository']), 'JOURNAL_INVALID')
    valid_params(value['operation'], value['params'])


class Journal:
    """Single-writer, hash-chained, fsynced JSONL journal bound to one repository.

    Stores operation identity, authorization identity, expected and observed Git
    state, results and recovery status only. Commit messages are stored as digests.
    The file must live outside the checkout. Entries are never rewritten; the only
    mutation besides appending is the explicit truncation of an incomplete final line.
    """

    FIELDS = {
        'header': 'repository root contract',
        'denied': 'operation_id operation intent_sha256 reason authorization_id',
        'begin': 'operation_id operation intent intent_sha256 authorization_id expected expected_post',
        'end': 'operation_id result observed detail',
        'recovery': 'operation_id status observed',
    }
    RECOVERY = ('RECONCILED_APPLIED', 'RECONCILED_NOT_APPLIED', 'AMBIGUOUS')

    def __init__(self, path, repository, root, clock=None, repair_torn_tail=False):
        self.repository = repository
        self.root = str(Path(os.path.abspath(str(root))))
        d.require(d.text(repository) and d.text(self.root), 'JOURNAL_INVALID')
        self.clock = clock or (lambda: int(time.time()))
        path = Path(os.path.abspath(str(path)))
        try:
            d.safe_path(path.parent)
        except OSError:
            raise d.Rejected('JOURNAL_PATH_INVALID') from None
        d.require(path.parent.is_dir(), 'JOURNAL_PATH_INVALID')
        # Never store the journal where a checkout operation could rewrite it.
        d.require(os.path.commonpath([str(path), self.root]) != self.root, 'JOURNAL_INSIDE_REPOSITORY')
        self.path = path
        self.entries = []
        self.last = GENESIS
        self.repaired = False
        flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
        try:
            self.fd = os.open(str(path), flags, 0o600)
        except OSError:
            raise d.Rejected('JOURNAL_PATH_INVALID') from None
        try:
            info = os.fstat(self.fd)
            d.require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o022, 'JOURNAL_PATH_INVALID')
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise d.Rejected('JOURNAL_LOCKED') from None
            self._load(repair_torn_tail)
        except BaseException:
            self.close()
            raise

    def close(self):
        if getattr(self, 'fd', None) is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _load(self, repair):
        size = os.fstat(self.fd).st_size
        d.require(size <= JOURNAL_LIMIT, 'JOURNAL_INVALID')
        data = os.pread(self.fd, size, 0) if size else b''
        if data and not data.endswith(b'\n'):
            d.require(repair, 'JOURNAL_TORN_TAIL')
            keep = data.rfind(b'\n') + 1
            self._validate(data[:keep])
            os.ftruncate(self.fd, keep)
            os.fsync(self.fd)
            self.repaired = True
            data = data[:keep]
        self._validate(data)
        if not self.entries:
            self.append('header', repository=self.repository, root=self.root, contract=JOURNAL_CONTRACT)
        header = self.entries[0]
        d.require(header['repository'] == self.repository and header['root'] == self.root, 'JOURNAL_REPOSITORY_MISMATCH')

    def _validate(self, data):
        entries, previous, status = [], GENESIS, {}
        for index, line in enumerate(data.split(b'\n')[:-1]):
            d.require(0 < len(line) <= LINE_LIMIT, 'JOURNAL_INVALID')
            try:
                entry = json.loads(line.decode('ascii'), object_pairs_hook=d.object_pairs,
                                   parse_constant=lambda value: (_ for _ in ()).throw(d.Rejected('JOURNAL_INVALID')))
            except (ValueError, UnicodeError):
                raise d.Rejected('JOURNAL_INVALID') from None
            d.require(isinstance(entry, dict) and d.canonical(entry) == line, 'JOURNAL_INVALID')
            event = entry.get('event')
            d.require(event in self.FIELDS and set(entry) == set('v seq prev ts event hash'.split() + self.FIELDS[event].split()),
                      'JOURNAL_INVALID')
            d.require(entry['v'] == 1 and entry['seq'] == index and entry['prev'] == previous
                      and type(entry['ts']) is int and entry['ts'] >= 0, 'JOURNAL_CHAIN_BROKEN')
            body = {k: v for k, v in entry.items() if k != 'hash'}
            d.require(entry['hash'] == d.digest(body), 'JOURNAL_CHAIN_BROKEN')
            d.require((event == 'header') == (index == 0), 'JOURNAL_INVALID')
            self._check(entry, status)
            entries.append(entry)
            previous = entry['hash']
        self.entries, self.last = entries, previous

    def _check(self, entry, status):
        event = entry['event']
        clean(entry)
        if event == 'header':
            d.require(entry['contract'] == JOURNAL_CONTRACT and d.text(entry['repository']) and d.text(entry['root']),
                      'JOURNAL_INVALID')
            return
        op = entry['operation_id']
        d.require(ident(op), 'JOURNAL_INVALID')
        current = status.get(op)
        if event == 'denied':
            d.require(current in (None, 'denied') and entry['operation'] in OPERATIONS + ('unvalidated',)
                      and hex64(entry['intent_sha256']) and REASON.fullmatch(entry['reason'])
                      and (entry['authorization_id'] is None or ident(entry['authorization_id'])), 'JOURNAL_INVALID')
            status[op] = 'denied'
        elif event == 'begin':
            d.require(current in (None, 'denied') and ident(entry['authorization_id']), 'JOURNAL_INVALID')
            valid_intent(entry['intent'])
            d.require(entry['intent']['operation'] == entry['operation'] and entry['intent_sha256'] == d.digest(entry['intent']),
                      'JOURNAL_INVALID')
            valid_state(entry['expected'])
            d.require(isinstance(entry['expected_post'], dict), 'JOURNAL_INVALID')
            status[op] = 'pending'
        elif event == 'end':
            d.require(current == 'pending' and entry['result'] in ('applied', 'failed') and REASON.fullmatch(entry['detail'])
                      and (entry['observed'] is None or valid_state(entry['observed']) is None), 'JOURNAL_INVALID')
            status[op] = entry['result']
        else:
            d.require(current == 'pending' and entry['status'] in self.RECOVERY
                      and (entry['observed'] is None or valid_state(entry['observed']) is None), 'JOURNAL_INVALID')
            status[op] = {'RECONCILED_APPLIED': 'applied', 'RECONCILED_NOT_APPLIED': 'not_applied',
                          'AMBIGUOUS': 'ambiguous'}[entry['status']]

    def append(self, event, **fields):
        d.require(event in self.FIELDS and self.fd is not None, 'JOURNAL_INVALID')
        entry = {'v': 1, 'seq': len(self.entries), 'prev': self.last, 'ts': int(self.clock()), 'event': event}
        entry.update(fields)
        entry['hash'] = d.digest(entry)
        line = d.canonical(entry) + b'\n'
        # Validate the would-be journal state before touching the file.
        self._check(entry, self.statuses() if event != 'header' else {})
        d.require(len(line) <= LINE_LIMIT, 'JOURNAL_INVALID')
        written = 0
        while written < len(line):
            written += os.write(self.fd, line[written:])
        os.fsync(self.fd)
        self.entries.append(entry)
        self.last = entry['hash']
        return entry

    def statuses(self):
        status = {}
        for entry in self.entries[1:]:
            self._check(copy.deepcopy(entry), status)
        return status

    def operation(self, operation_id):
        """Return (status, begin entry or None) derived from the verified chain."""
        begin = None
        for entry in self.entries[1:]:
            if entry.get('operation_id') == operation_id and entry['event'] == 'begin':
                begin = entry
        return self.statuses().get(operation_id), begin

    def pending(self):
        return [op for op, value in self.statuses().items() if value == 'pending']

    def unresolved(self):
        return [op for op, value in self.statuses().items() if value in ('pending', 'ambiguous')]

    def verify(self):
        """Re-read the file and validate the complete chain; returns a summary."""
        size = os.fstat(self.fd).st_size
        data = os.pread(self.fd, size, 0) if size else b''
        d.require(data.endswith(b'\n'), 'JOURNAL_TORN_TAIL')
        saved = (self.entries, self.last)
        self._validate(data)
        d.require(self.entries == saved[0] and self.last == saved[1], 'JOURNAL_CHAIN_BROKEN')
        return {'entries': len(self.entries), 'head_hash': self.last}


class GitAdapter:
    """Provider-neutral local Git operations for one repository and one branch.

    authorizer(intent) is called once per mutable operation with the exact intent
    and must return an authorization identity (string) or a falsy value; it is never
    cached. Without an authorizer, or for operations outside `allow`, every mutation
    is denied. execute() is the only generic entry point and accepts allowlisted
    operation names only.
    """

    COMMANDS = frozenset(('rev-parse', 'symbolic-ref', 'diff', 'diff-tree', 'cat-file', 'rev-list', 'show',
                          'config', 'add', 'commit', 'switch'))
    CONFIG = re.compile(r'core\.(repositoryformatversion|filemode|bare|logallrefupdates|ignorecase|precomposeunicode)'
                        r'|user\.(name|email)|remote\.[A-Za-z0-9_-]+\.(url|fetch)|branch\.\S+\.(remote|merge)')

    def __init__(self, repo, repository, branch, identity, journal, authorizer=None, allow=(), git=None):
        self.repo = d.safe_path(Path(repo))
        d.require(self.repo.is_dir() and stat.S_ISDIR(self.repo.lstat().st_mode), 'UNSAFE_PATH')
        d.require(d.text(repository), 'INVALID_IDENTITY')
        d.require(branch_name(branch), 'INVALID_BRANCH')
        d.require(isinstance(identity, tuple) and len(identity) == 2 and all(d.text(v) and not set('<>\n') & set(v) for v in identity)
                  and '@' in identity[1], 'INVALID_IDENTITY')
        d.require(isinstance(journal, Journal) and journal.repository == repository and journal.root == str(self.repo),
                  'JOURNAL_REPOSITORY_MISMATCH')
        allow = tuple(allow)
        d.require(all(item in OPERATIONS for item in allow), 'OPERATION_NOT_SUPPORTED')
        self.repository, self.branch, self.identity, self.journal = repository, branch, identity, journal
        self.authorizer, self.allow = authorizer, frozenset(allow)
        self.git = git or shutil.which('git')
        d.require(self.git is not None and os.path.isabs(self.git), 'GIT_UNAVAILABLE')

    # ---- Git execution: fixed templates, no shell, minimal environment ----
    def _run(self, *argv, ok=(0,), commit=False):
        d.require(argv and argv[0] in self.COMMANDS, 'COMMAND_NOT_ALLOWED')
        env = {'PATH': os.defpath, 'HOME': '/dev/null', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
               'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1',
               'GIT_CEILING_DIRECTORIES': str(self.repo.parent)}
        if commit:
            env.update({'GIT_AUTHOR_NAME': self.identity[0], 'GIT_AUTHOR_EMAIL': self.identity[1],
                        'GIT_COMMITTER_NAME': self.identity[0], 'GIT_COMMITTER_EMAIL': self.identity[1]})
        cmd = [self.git, '--no-optional-locks', '--literal-pathspecs', '-c', 'core.hooksPath=/dev/null',
               '-c', 'core.fsmonitor=false', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false',
               '-c', 'core.attributesFile=/dev/null', '-c', 'core.excludesFile=/dev/null',
               '-c', 'commit.gpgsign=false', '-C', str(self.repo)]
        if argv[0] in ('add', 'commit', 'switch'):
            cmd.remove('--no-optional-locks')
        try:
            result = subprocess.run(cmd + list(argv), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=60, check=False, shell=False)
        except (OSError, subprocess.SubprocessError):
            raise d.Rejected('GIT_OUTCOME_UNKNOWN') from None
        d.require(result.returncode in ok, 'GIT_FAILED')
        d.require(len(result.stdout) <= d.LIMIT, 'GIT_OUTPUT_LIMIT')
        return result.returncode, result.stdout

    def _out(self, *argv, **kw):
        return self._run(*argv, **kw)[1]

    # ---- Repository validation ----
    def _check_repository(self, branch=True):
        try:
            self._check_layout(branch)
        except OSError:
            raise d.Rejected('UNSUPPORTED_GIT_LAYOUT') from None

    def _check_layout(self, branch):
        repo = d.safe_path(self.repo)
        git = d.safe_path(repo / '.git')
        d.require(stat.S_ISDIR(git.lstat().st_mode), 'UNSUPPORTED_GIT_LAYOUT')  # no gitdir files, worktrees or submodule links
        d.require(not d.present(git / 'commondir') and not d.present(git / 'config.worktree'), 'UNSUPPORTED_GIT_LAYOUT')
        d.require(stat.S_ISDIR(d.safe_path(git / 'objects').lstat().st_mode), 'UNSUPPORTED_GIT_LAYOUT')
        info = git / 'objects' / 'info'
        d.require(not any(d.present(info / name) for name in ('alternates', 'http-alternates')), 'UNSAFE_GIT_LAYOUT')
        hooks = git / 'hooks'
        if d.present(hooks):
            d.safe_path(hooks)
            d.require(all(p.name.endswith('.sample') and stat.S_ISREG(p.lstat().st_mode) for p in hooks.iterdir()),
                      'UNSAFE_GIT_HOOKS')
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'shallow',
                     'info/grafts', 'info/attributes', 'refs/replace', 'index.lock', 'HEAD.lock'):
            d.require(not d.present(git / name), 'UNSAFE_GIT_STATE')
        config = self._out('config', '--local', '--list', '-z')
        for item in config.split(b'\0'):
            if item:
                key = item.split(b'\n', 1)[0].decode('utf-8', 'replace')
                d.require(self.CONFIG.fullmatch(key), 'UNSAFE_GIT_CONFIG')
        d.require(self._out('config', '--local', '--bool', '--get', 'core.bare').strip() == b'false', 'UNSAFE_GIT_CONFIG')
        top = decoded(self._out('rev-parse', '--show-toplevel')).strip()
        d.require(os.path.realpath(top) == str(repo), 'REPOSITORY_MISMATCH')
        # Attributes can select executable filters and alter staged bytes.
        count = 0
        for folder, names, files in os.walk(str(repo)):
            names[:] = [n for n in names if not (folder == str(repo) and n == '.git')]
            for name in files:
                count += 1
                d.require(count <= d.MAX_FILES and name != '.gitattributes', 'ATTRIBUTES_UNSUPPORTED')
        if branch:
            code, value = self._run('symbolic-ref', '-q', '--short', 'HEAD', ok=(0, 1))
            d.require(code == 0 and decoded(value).strip() == self.branch, 'BRANCH_CHANGED')

    def _head(self):
        code, value = self._run('rev-parse', '--verify', '-q', 'HEAD', ok=(0, 1))
        head = decoded(value, 'ascii').strip()
        d.require(code == 0 and d.oid(head), 'UNBORN_HEAD')
        return head

    def _raw(self, *argv):
        tokens = self._out(*argv).split(b'\0')
        if tokens and tokens[-1] == b'':
            tokens.pop()
        d.require(len(tokens) % 2 == 0 and len(tokens) <= 2 * MAX_FILES, 'GIT_OUTPUT_INVALID')
        items = []
        for index in range(0, len(tokens), 2):
            try:
                meta = tokens[index].decode('ascii')
                path = tokens[index + 1].decode('utf-8')
            except UnicodeError:
                raise d.Rejected('GIT_OUTPUT_INVALID') from None
            fields = meta[1:].split(' ')
            d.require(meta.startswith(':') and len(fields) == 5 and fields[4] in ('A', 'M') and path_ok(path)
                      and fields[1] in MODES and d.oid(fields[3]), 'STAGED_UNSUPPORTED_CHANGE')
            blob = self._out('cat-file', 'blob', fields[3])
            items.append([path, hashlib.sha256(blob).hexdigest(), fields[1]])
        return sorted(items)

    def _staged(self):
        return self._raw('diff', '--cached', '--raw', '--no-abbrev', '--no-renames', '-z')

    def _observe(self, branch=True):
        self._check_repository(branch)
        code, value = self._run('symbolic-ref', '-q', '--short', 'HEAD', ok=(0, 1))
        d.require(code == 0, 'BRANCH_CHANGED')
        return {'branch': decoded(value).strip(), 'head_sha': self._head(), 'staged': self._staged()}

    def observe(self):
        """Read-only observed state; needs no authorization."""
        return self._observe()

    # ---- Argument validation (pure) ----
    @staticmethod
    def _files(files):
        d.require(isinstance(files, dict) and 0 < len(files) <= MAX_FILES, 'INVALID_FILES')
        result = []
        for path, state in files.items():
            d.require(path_ok(path) and isinstance(state, dict) and set(state) == {'sha256', 'executable'}
                      and hex64(state['sha256']) and type(state['executable']) is bool, 'INVALID_FILES')
            result.append([path, state['sha256'], state['executable']])
        return sorted(result)

    def _params(self, operation, params):
        """Return (journal-safe params, full params). Unknown or extra arguments are rejected."""
        d.require(isinstance(params, dict), 'INVALID_ARGUMENTS')
        if operation == 'create_branch':
            d.require(set(params) == {'name', 'start_sha'} and branch_name(params['name']) and d.oid(params['start_sha']),
                      'INVALID_ARGUMENTS')
            safe = {'name': params['name'], 'start_sha': params['start_sha']}
            return safe, dict(safe)
        if operation == 'stage':
            d.require(set(params) == {'files'}, 'INVALID_ARGUMENTS')
            safe = {'files': self._files(params['files'])}
            return safe, copy.deepcopy(safe)
        d.require(set(params) == {'message', 'files'} and d.text(params['message']) and params['message'] == params['message'].strip()
                  and PROVENANCE_TRAILER + ':' not in params['message'],
                  'INVALID_ARGUMENTS')
        files = self._files(params['files'])
        safe = {'message_sha256': sha(params['message']), 'message_length': len(params['message']), 'files': files}
        return safe, {'message': params['message'], 'files': files}

    # ---- Public mutable operations: each requires its own authorization ----
    def create_branch(self, operation_id, name, start_sha):
        return self._mutate('create_branch', operation_id, {'name': name, 'start_sha': start_sha})

    def stage(self, operation_id, files):
        return self._mutate('stage', operation_id, {'files': files})

    def commit(self, operation_id, message, files):
        return self._mutate('commit', operation_id, {'message': message, 'files': files})

    def execute(self, operation, operation_id, **params):
        d.require(operation in OPERATIONS, 'OPERATION_NOT_SUPPORTED')
        return self._mutate(operation, operation_id, params)

    # ---- Planning: stateful checks and fixed argument templates ----
    @staticmethod
    def _expected_staged(files):
        return [[p, s, '100755' if x else '100644'] for p, s, x in files]

    def _verify_files(self, files):
        try:
            for path, digest, executable in files:
                target = d.safe_path(self.repo / path)
                mode = target.lstat().st_mode
                d.require(stat.S_ISREG(mode) and bool(mode & 0o111) == executable, 'FILE_INTEGRITY_FAILED')
                d.require(hashlib.sha256(d.read(target)).hexdigest() == digest, 'FILE_INTEGRITY_FAILED')
        except OSError:
            raise d.Rejected('FILE_INTEGRITY_FAILED') from None

    def _plan(self, operation, safe, state):
        d.require(state['branch'] == self.branch, 'BRANCH_CHANGED')
        if operation == 'create_branch':
            d.require(safe['start_sha'] == state['head_sha'] and not state['staged'], 'STATE_MISMATCH')
            code, _ = self._run('rev-parse', '--verify', '-q', 'refs/heads/' + safe['name'], ok=(0, 1))
            d.require(code == 1 and safe['name'] != self.branch, 'BRANCH_EXISTS')
            argv = ('switch', '--no-guess', '-c', safe['name'], safe['start_sha'])
            post = {'branch': safe['name'], 'head_sha': safe['start_sha']}
        elif operation == 'stage':
            d.require(not state['staged'], 'INDEX_NOT_EMPTY')
            self._verify_files(safe['files'])
            argv = ('add', '--', *[item[0] for item in safe['files']])
            post = {'staged': self._expected_staged(safe['files'])}
        else:
            d.require(state['staged'] == self._expected_staged(safe['files']), 'STAGED_FILES_MISMATCH')
            argv = None  # message is supplied separately and never journaled
            post = {'parent': state['head_sha'], 'message_sha256': safe['message_sha256'],
                    'files': safe['files'], 'provenance': secrets.token_hex(16)}
        return argv, post

    def _post_holds(self, operation, post, observed, safe=None):
        if operation == 'create_branch':
            return observed['branch'] == post['branch'] and observed['head_sha'] == post['head_sha']
        if operation == 'stage':
            return observed['staged'] == post['staged']
        return self._commit_matches(post, observed)

    def _commit_matches(self, post, observed):
        token = post.get('provenance')
        if not provenance_token(token):
            return False
        head = observed['head_sha']
        parents = decoded(self._out('rev-list', '--parents', '-n', '1', 'HEAD'), 'ascii').split()
        if parents != [head, post['parent']] or observed['staged']:
            return False
        raw_msg = decoded(self._out('show', '-s', '--format=%B', 'HEAD')).rstrip('\n')
        body, sep, trailer_block = raw_msg.rpartition('\n\n')
        if sep != '\n\n' or PROVENANCE_TRAILER + ':' in body:
            return False
        if trailer_block != PROVENANCE_TRAILER + ': ' + token:
            return False
        if sha(body) != post['message_sha256']:
            return False
        changed = self._raw('diff-tree', '--no-commit-id', '--raw', '--no-abbrev', '--no-renames', '-r', '-z', 'HEAD')
        return changed == self._expected_staged(post['files'])

    # ---- Mutation protocol ----
    def _deny(self, operation_id, operation, intent_sha256, reason, authorization_id=None):
        self.journal.append('denied', operation_id=operation_id, operation=operation, intent_sha256=intent_sha256,
                            reason=reason, authorization_id=authorization_id)
        raise d.Rejected(reason)

    def _mutate(self, operation, operation_id, params):
        d.require(ident(operation_id), 'INVALID_OPERATION_ID')
        d.require(operation in OPERATIONS, 'OPERATION_NOT_SUPPORTED')
        status, begin = self.journal.operation(operation_id)
        unvalidated = d.digest({'operation': operation})
        if operation not in self.allow or self.authorizer is None:
            reason = 'OPERATION_NOT_ALLOWED' if operation not in self.allow else 'AUTHORIZATION_UNAVAILABLE'
            d.require(status in (None, 'denied'), 'OPERATION_ID_REUSED')
            self._deny(operation_id, 'unvalidated', unvalidated, reason)
        safe, full = self._params(operation, params)
        intent = {'operation': operation, 'repository': self.repository, 'params': safe}
        intent_sha = d.digest(intent)
        if status not in (None, 'denied'):
            d.require(begin is not None and begin['intent_sha256'] == intent_sha, 'OPERATION_ID_CONFLICT')
            if status == 'pending':
                self.recover()
                status, begin = self.journal.operation(operation_id)
            d.require(status == 'applied', 'OPERATION_NOT_APPLIED' if status == 'not_applied' else
                      'OPERATION_ID_REUSED' if status == 'failed' else 'OPERATION_AMBIGUOUS')
            if operation == 'create_branch':
                self.branch = safe['name']
            return {'operation_id': operation_id, 'operation': operation, 'status': 'REPLAYED',
                    'authorization_id': begin['authorization_id'], 'observed': self._final(operation_id)}
        d.require(not self.journal.unresolved(), 'JOURNAL_UNRESOLVED')
        try:
            state = self._observe()
            argv, post = self._plan(operation, safe, state)
        except d.Rejected as error:
            self._deny(operation_id, operation, intent_sha, str(error))
        shown = {'operation_id': operation_id, 'operation': operation, 'repository': self.repository,
                 'branch': self.branch, 'head_sha': state['head_sha'], 'params': full}
        try:
            authorization = self.authorizer(copy.deepcopy(shown))
        except Exception:
            self._deny(operation_id, operation, intent_sha, 'AUTHORIZATION_ERROR')
        if not ident(authorization):
            self._deny(operation_id, operation, intent_sha, 'AUTHORIZATION_DENIED')
        try:  # approval-time drift
            d.require(self._observe() == state, 'STATE_CHANGED_AFTER_AUTHORIZATION')
            if operation == 'stage':
                self._verify_files(safe['files'])
        except d.Rejected as error:
            self._deny(operation_id, operation, intent_sha, str(error), authorization)
        self.journal.append('begin', operation_id=operation_id, operation=operation, intent=intent,
                            intent_sha256=intent_sha, authorization_id=authorization, expected=state, expected_post=post)
        detail, result = 'GIT_FAILED', 'failed'
        try:
            if operation == 'commit':
                commit_message = full['message'] + '\n\n' + PROVENANCE_TRAILER + ': ' + post['provenance']
                self._run('commit', '--no-verify', '--no-gpg-sign', '--cleanup=verbatim', '-m', commit_message, commit=True)
            else:
                self._run(*argv)
            observed = self._observe(branch=False)
            if self._post_holds(operation, post, observed):
                detail, result = 'OK', 'applied'
            else:
                detail = 'POSTCONDITION_FAILED'
        except d.Rejected as error:
            # A failed or timed-out Git call may still have applied; classify from observation.
            detail = str(error) if REASON.fullmatch(str(error)) else 'GIT_FAILED'
            try:
                observed = self._observe(branch=False)
                if self._post_holds(operation, post, observed):
                    detail, result = 'APPLIED_AFTER_ERROR', 'applied'
            except d.Rejected:
                # Neither "applied" nor "failed" can be shown. Record no result: the operation stays pending, so
                # unresolved() reports it, new mutations are blocked, and recover() reconciles it by observation.
                raise d.Rejected('GIT_OUTCOME_UNKNOWN') from None
        self.journal.append('end', operation_id=operation_id, result=result, observed=observed, detail=detail)
        d.require(result == 'applied', detail)
        if operation == 'create_branch':
            self.branch = safe['name']
        return {'operation_id': operation_id, 'operation': operation, 'status': 'APPLIED',
                'authorization_id': authorization, 'observed': observed}

    def _final(self, operation_id):
        observed = None
        for entry in self.journal.entries[1:]:
            if entry.get('operation_id') == operation_id and entry['event'] in ('end', 'recovery'):
                observed = entry['observed']
        return observed

    # ---- Crash recovery: observe, never re-execute ----
    def recover(self):
        """Reconcile every pending operation against observed Git state. Nothing is re-run."""
        outcome = {}
        for operation_id in self.journal.pending():
            status, begin = self.journal.operation(operation_id)
            observed = None
            try:
                observed = self._observe(branch=False)
                if self._post_holds(begin['operation'], begin['expected_post'], observed):
                    result = 'RECONCILED_APPLIED'
                elif observed == begin['expected']:
                    result = 'RECONCILED_NOT_APPLIED'
                else:
                    result = 'AMBIGUOUS'
            except d.Rejected:
                # Unverifiable: stay unresolved, and keep whatever state could be observed as evidence.
                result = 'AMBIGUOUS'
            self.journal.append('recovery', operation_id=operation_id, status=result, observed=observed)
            if result == 'RECONCILED_APPLIED' and begin['operation'] == 'create_branch':
                self.branch = begin['expected_post']['branch']
            outcome[operation_id] = result
        return outcome
