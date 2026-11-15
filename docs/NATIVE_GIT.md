# Native Git adapter and execution journal (V2-04G)

`ai_sdlc/native_git.py` is an opt-in, provider-neutral library for **local** Git
operations. It adds no CLI, no remote operation and no dependency, and it leaves the
`ai-sdlc-delivery/1` planner and the V2-04F executor unchanged. Approval, journal
storage and exclusive repository access are host responsibilities; the library does
not treat any file or argument as authority.

## Operations

| Operation | Git template (fixed) | Authorization binds |
| --- | --- | --- |
| `create_branch(operation_id, name, start_sha)` | `switch --no-guess -c NAME SHA` | name, start SHA, current branch/HEAD, empty index |
| `stage(operation_id, files)` | `add -- PATH...` | each path, SHA-256 and executable bit; empty index |
| `commit(operation_id, message, files)` | `commit --no-verify --no-gpg-sign --cleanup=verbatim -m MESSAGE` | message, exact staged set, HEAD |

`observe()` is read-only. `execute(name, operation_id, **params)` accepts only these
names; push, fetch, reset, clean, merge, tag and branch deletion do not exist.
`files` is `{path: {"sha256": hex, "executable": bool}}`.

## Safety model

- **Deny by default.** A mutation needs the operation in `allow`, an `authorizer`,
  and an authorizer result that is a valid identity string. `authorizer(intent)` is
  called once per mutable operation with the exact intent (including the commit
  message); approval is never cached or shared between operations.
- **No shell, no argument forwarding.** `subprocess.run` receives a list, `shell=False`,
  an absolute Git path and fixed templates. Callers supply validated values only
  (refs, relative paths without `..`, `.git`, leading `-` or `.gitattributes`,
  printable-ASCII single-line messages). `_run` rejects any subcommand outside
  a small allowlist. Pass `git=` an absolute path; the default uses `shutil.which`.
- **Minimal child environment.** `PATH=/bin:/usr/bin`, `HOME=/dev/null`, global and
  system Git config disabled, prompts disabled, no inherited `GIT_*`, no credentials;
  hooks, fsmonitor, autocrlf and attribute/exclude files are neutralized.
- **Repository validation on every observation.** Real path (no symlink components),
  `.git` is a directory (no gitdir files, worktrees, alternates, shallow, grafts, replace
  refs, in-progress merge states), only sample hooks, local config restricted to an
  allowlist (no filters, aliases, includes, hooks path, ssh command), no `.gitattributes`,
  top level equals the bound path, HEAD on the bound branch.
- **State and file integrity.** The state is `{branch, head_sha, staged}`; staged blobs are
  compared by SHA-256 and mode. State is re-observed after approval and again after
  the Git call; any drift or unexpected result is rejected or journaled as failed.

## Journal

`Journal(path, repository, root)` is an append-only, hash-chained JSONL file, bound to
one repository, opened with an exclusive lock, mode 0600, `O_NOFOLLOW`, outside the
checkout, with `fsync` after each entry. Events:

| Event | Records |
| --- | --- |
| `header` | repository identity, root, contract |
| `denied` | operation id, reason code, authorization id if any |
| `begin` | operation id and intent digest, authorization identity, expected state, expected result |
| `end` | `applied`/`failed`, observed state, detail code |
| `recovery` | `RECONCILED_APPLIED`, `RECONCILED_NOT_APPLIED` or `AMBIGUOUS`, observed state |

Only allowlisted, bounded fields are stored. Commit messages are stored as a SHA-256
and length. No environment, credentials, Git output or error text is journaled.
`verify()` revalidates every line (canonical form, schema, sequence, chain, state
machine). A torn final line is refused until an explicit `repair_torn_tail=True`.

## Duplicates and recovery

`operation_id` is the idempotency key. Same id and same intent after `applied` returns
`REPLAYED` without calling the authorizer or Git; a different intent is
`OPERATION_ID_CONFLICT`; failed, not-applied and ambiguous ids are retired. After a crash,
`recover()` observes Git and never re-executes: applied, not applied, or ambiguous.
Pending or ambiguous operations block new mutations (`JOURNAL_UNRESOLVED`).

If Git reports an error (timeout, I/O error, nonzero exit) the adapter re-observes the
repository: a change that did apply is journaled `applied` (`APPLIED_AFTER_ERROR`), and
one proven not to have applied is journaled `failed`. If the state cannot be observed at
all, no result is recorded: the call raises `GIT_OUTCOME_UNKNOWN` and the operation stays
`pending` until `recover()` reconciles it. It is never recorded as a confirmed failure.

Git output that is not valid UTF-8 (for example a commit written with a raw non-UTF-8
message, or a branch name with such bytes) is rejected as `GIT_OUTPUT_INVALID`. It is never
decoded lossily and never escapes as an exception. In `recover()` it leaves the operation
`AMBIGUOUS` (unresolved, never replayed) and the state that could be observed is kept in the
`recovery` entry; the executor's commit-identity proof rejects it the same way.

## Limitations

- The hash chain is tamper-evident, not authenticated: a writer with file access can
  forge a valid chain or drop trailing entries. Anchor the head hash externally if that
  matters. The authorization identity is a host-asserted string.
- Single writer: the journal lock does not lock the repository. Concurrent external Git
  use between the final check and the Git call is detected afterwards, not prevented.
- A failed postcondition after `git add`/`commit` is journaled, but the library never
  unstages, resets or deletes; a human resolves the state.
- The `GIT_OUTPUT_INVALID` guarantee covers decoding of **Git command output**. Repository
  files that the planner or executor read directly (such as `.git/HEAD` or a ref file) are
  not covered by it.
- ASCII-only paths and messages; no deletions, renames, submodules, LFS, signing,
  unborn HEAD, linked worktrees or nonlocal operations. Linux/POSIX only (`fcntl`).
- Tested on Python 3.14 and AST-checked for 3.9 grammar; 3.9 runtime NOT_RUN locally.
