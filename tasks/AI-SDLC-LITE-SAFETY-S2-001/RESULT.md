# SAFETY-S2-001 result — D2: non-UTF-8 Git output during recovery

## Bound and identity

- Active contract and approval: user mission `AI-SDLC-LITE-SAFETY-S2-001`, supplied 2026-11-15. It authorizes the investigation, tests, a minimal fix, a local commit, a push of an isolated branch and one draft PR; it withholds merge, branch deletion, force-push, `master` changes and S3.
- Baseline: `develop` `1d832a5a550f623c9651108ddde14d64aed88eed`; `master` `7f925cd0c45b6501d743d09ebd8c9569edced40e`. Suite at baseline: 440 tests, 2 expected skips.
- Branch `fix/s2-recovery-non-utf8-output`, created in an isolated worktree from the exact `develop` commit.

## D2 — reproduction and failure path

Reproduced first, with production code untouched (5 new tests failed, 4 characterization tests passed, all existing tests passed). Each fixture proves Git really emits invalid UTF-8 before the code under test runs: `git commit` and `git commit-tree` silently re-encode a Latin-1 message to UTF-8, so the foreign commit object is written with `git hash-object --literally`.

| Path | Failure | Source |
| --- | --- | --- |
| `GitAdapter.recover()` with a foreign commit whose message is not UTF-8 | `UnicodeDecodeError` escapes | `_commit_matches` strict decode (`native_git.py`), outside the only `except d.Rejected` |
| `GitAdapter.observe()` with a branch name that is not UTF-8 | `UnicodeDecodeError` | strict decode in the branch check |
| `Executor.commit()` recovery identity proof | `UnicodeDecodeError` | strict decode of `git show` output (`delivery_executor.py`) |
| `Executor.commit()` with a pending adapter operation | same error through `_reconcile()` → `recover()` | as above |

Safety implications (all fail closed, none mutated Git):

- `recover()` aborted mid-loop: the operation stayed `pending`, **no `recovery` entry was written** (no evidence), and other pending operations in the same loop were left unreconciled.
- Every later mutation was blocked by `JOURNAL_UNRESOLVED`, and callers (including the executor) received an uncontrolled exception type instead of a structured code.
- A hostile or odd repository could therefore wedge recovery with no recorded reason.

## Fix

Smallest change that satisfies the recovery contract:

- New `decoded(raw, encoding)` helper in `ai_sdlc/native_git.py`: strict decode; undecodable bytes raise the existing `d.Rejected('GIT_OUTPUT_INVALID')` (the code `_raw` already used). Applied at each decode of Git **command output** in the adapter (toplevel, branch check, HEAD, observed branch, `rev-list` parents, commit message) and in the executor's recovery proof (`_names`, tree check, parents, message).
- `recover()` now keeps the state it managed to observe when a later check is rejected, so the `recovery` entry carries that evidence (previously discarded). An unverifiable state is `AMBIGUOUS`: unresolved, never replayed, never fabricated as applied or not applied.

No lossy decoding, no new journal state or schema change, no change to public error contracts apart from the new, structured outcome where an exception used to escape. The S1/D3 behavior is unchanged.

## Tests added (9; 440 → 449)

| Test | Result before → after |
| --- | --- |
| recovery with a non-UTF-8 foreign commit message is `AMBIGUOUS`, no mutation, no replay, journal chain intact, evidence kept | ERROR → pass |
| `observe()` with a non-UTF-8 branch name is `GIT_OUTPUT_INVALID`; a mutation is denied before anything begins | ERROR → pass |
| unknown outcome (D3) followed by undecodable state stays unresolved with no duplicate mutation | ERROR → pass |
| executor identity proof with a non-UTF-8 message is `GIT_OUTPUT_INVALID` | ERROR → pass |
| pending operation plus undecodable foreign commit blocks the executor (`RECOVERY_AMBIGUOUS`) | ERROR → pass |
| valid UTF-8 foreign message: recovery `AMBIGUOUS` | pass → pass |
| valid UTF-8 non-ASCII branch name: `BRANCH_CHANGED` | pass → pass |
| the adapter's own applied commit still reconciles as applied and replays | pass → pass |
| executor: valid UTF-8 foreign message is `COMMIT_IDENTITY_MISMATCH` | pass → pass |

## Verification

Environment: Linux, Python 3.14.9, installed Git, standard library only; `copilot` excluded from `PATH` as in CI. No network, remote or provider.

| Check | Result |
| --- | --- |
| New tests against unmodified production code | 5 ERROR (`UnicodeDecodeError`), 4 pass |
| Same tests with the fix | all pass (89 tests in the three affected modules) |
| Mutation checks on scratch copies | reverting the message decode: 3 tests fail; reverting the branch decode: 1; dropping observed evidence: 1; fabricating `NOT_APPLIED`: 3; lossy `errors='replace'` decoding: 2; reverting the executor decode: 1 |
| Full suite via the CI gate script (Python 3.14) | `Discovered=449 Run=449 Skipped=2 Modules=16`, exactly the 2 expected skips, 0 failures |
| S1 / D3 tests (6) | all still pass |
| AST parse with `feature_version=(3, 9)` of the five changed Python files | PASS (3.9 runtime NOT_RUN locally; CI runs it) |
| `git diff --check` | PASS |

## Changed files

SHA-256 of the final files, this report excluded:

| File | SHA-256 |
| --- | --- |
| ai_sdlc/native_git.py | 382ed79e4be8b172059689580a6e416735001167c8aa6aeb93f660865c225eac |
| ai_sdlc/delivery_executor.py | a76b94db370c9ac4daac99b45fdf38e98d8deacb8d8873507ca860c7707b51ff |
| tests/test_native_git.py | f997f2ddf71522ebb91fdb78a305bb3f9022193769f528eebdbdb7ac77408765 |
| tests/test_delivery_executor.py | 630354ebc29eb1829e42bcfd055ac9255ac36db7235b58190427e4a6474154a1 |
| tests/test_delivery_native_integration.py | d72397e54d2d26f5f15fcf5017c5b42c10d53f45755ffc6d7e6ff8addd85dc45 |
| docs/NATIVE_GIT.md | 3cde2d1c266a70fa15b6e37e00ff2957a83555a303c90755847f666ed41c6391 |
| tasks/AI-SDLC-LITE-SAFETY-S2-001/RESULT.md | new, this record |

CI configuration is untouched; the gate no longer asserts a test count.

## Limitations and remaining risks

- **D2b (not fixed, out of scope):** the planner reads `.git/HEAD` directly with a strict ASCII decode (`delivery.py`). A branch name with non-ASCII bytes makes `plan()` raise `UnicodeDecodeError` (confirmed with a probe). That is repository file content read by the V2-04E planner, not Git command output; the executor also reads a ref file directly (`_head_from_disk`). Documented in `docs/NATIVE_GIT.md` as outside the guarantee.
- D1 (replay after `git pack-refs`) and D4 (recovery does not verify authorship) remain open; S3 is not started.
- A foreign commit with the same parent, message and files as the pending commit is still accepted as `RECONCILED_APPLIED` (D4).
- Python 3.9 runtime of the new tests is verified only by CI.
- Human acceptance: PENDING. No merge, branch deletion or setting change was made.
