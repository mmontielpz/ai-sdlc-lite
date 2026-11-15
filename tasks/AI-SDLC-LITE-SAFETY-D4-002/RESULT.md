# SAFETY-D4-002 result — D4: operation-bound commit provenance

## Bound and identity

- Mission: `AI-SDLC-LITE-SAFETY-D4-002`
- Baseline: `develop` `26472d169ed124e401c8f3d08bd541c308763076`
- Branch: `fix/d4-commit-provenance` (isolated worktree `/home/mike/worktrees/ai-sdlc-lite-d4`)

## Root cause and reproduction

`GitAdapter._commit_matches()` in `ai_sdlc/native_git.py` attributed `HEAD` to a pending `commit` operation using only parent SHA, message hash, and `diff-tree` file state. Before modifying production code, 3 false-attribution tests reproduced `RECONCILED_APPLIED` on foreign commits (identical parent/message/tree, identical author/timestamp, and legacy pending journal without provenance), and user messages containing the reserved trailer prefix were accepted.

## Provenance contract

- Before `begin` is appended, `GitAdapter._plan()` generates a unique 32-hex-char token (`secrets.token_hex(16)`) persisted in `expected_post['provenance']` (no `Journal` schema change).
- `GitAdapter._mutate()` binds the token to the commit via the reserved final trailer `AI-SDLC-Provenance: <token>`, separated from the user body by `\n\n`.
- `message_sha256` hashes the user-supplied body (without the trailer). `GitAdapter._params()` rejects user messages containing `AI-SDLC-Provenance:`.
- `GitAdapter._commit_matches()` requires a valid `provenance` token in `expected_post`, rejects body-only/duplicated/missing/mismatched trailers, and verifies `sha(body) == post['message_sha256']`.
- `Executor.commit()` in `ai_sdlc/delivery_executor.py` verifies the exact `AI-SDLC-Provenance: <token>` trailer when `git_adapter` is present.
- Legacy pending commit entries without `provenance` fail closed as `AMBIGUOUS`; already-completed legacy entries remain valid.

## Trust boundary and limitations

- Provenance tokens distinguish operations and prevent accidental/concurrent content-only attribution, but do **not** authenticate against a writer with direct access to both the unauthenticated journal and the Git repository.
- `D2c` (non-ASCII branch names in `GitAdapter` journal `valid_state`) and `D6` (Git author identity) remain open out of scope.

## Verification

- Added 9 D4 regression tests in `tests/test_native_git.py` (467 -> 476 tests).
- Targeted D4 + D1 + D2 + D2b + D3 + Native Git modules: 150/150 PASS.
- Full local deterministic suite and CI (Python 3.9, 3.14, `ci-gate`): verified below.
