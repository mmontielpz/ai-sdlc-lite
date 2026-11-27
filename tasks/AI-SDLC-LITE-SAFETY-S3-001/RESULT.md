# SAFETY-S3-001 result — D1: recovery after git pack-refs

## Bound and identity

- Mission: `AI-SDLC-LITE-SAFETY-S3-001`
- Baseline: `develop` `774fd69091143cbfaedef50c47325ac6afa6883b`
- Branch: `fix/s3-packed-refs-recovery` (isolated worktree `<HOME>/worktrees/ai-sdlc-lite-s3-d1`)

## Root cause and reproduction

`Executor._head_from_disk()` in `ai_sdlc/delivery_executor.py` checked only whether the loose branch ref file `.git/refs/heads/<expected_branch>` existed. When `git pack-refs --all` removed the loose ref and stored the branch head in `.git/packed-refs`, `_head_from_disk()` fell back to the stale `self.request['head_sha']` (`base`). After a committed delivery, `d.snapshot()` in `ai_sdlc/delivery.py` resolved the actual packed SHA and rejected recovery with `HEAD_CHANGED` instead of reconciling idempotently.

Reproduced before modifying production code: `test_commit_recovery_after_pack_refs_is_idempotent` raised `HEAD_CHANGED` on recovery after `git pack-refs --all`.

## Correction

- Extracted `resolve_ref(git, ref_name)` in `ai_sdlc/delivery.py` to resolve a branch ref from loose file first and `packed-refs` second, preserving Git's logical reference precedence and strict `decode_ref` validation.
- Updated `snapshot()` in `ai_sdlc/delivery.py` and `_head_from_disk()` in `ai_sdlc/delivery_executor.py` to use `resolve_ref` (`INVALID_SHA` mapped from `INVALID_REF` in `_head_from_disk`), failing closed when the ref is missing or malformed and never falling back to a stale `request['head_sha']`.

## Test evidence

- Added 5 D1 regression tests across `tests/test_delivery_executor.py` (2) and `tests/test_delivery_native_integration.py` (3) covering loose refs, packed refs, mixed loose/packed refs, detached HEAD, pending/ambiguous journal entries, idempotent repeated recovery, and zero duplicate commits or ref mutations.
- D1 + D2 + D2b + D3 + Native Git modules (`test_delivery`, `test_delivery_executor`, `test_delivery_native_integration`, `test_native_git`): 141/141 PASS.
- Full local deterministic suite: verified below.
- Python 3.9 AST parse check and `git diff --check`: PASS.

## Residual risks and rollback

- `D4` (commit provenance verification), `D2c` (non-ASCII branch names in `GitAdapter` journal `valid_state`), and `D6` (Git author identity) remain open out of scope.
- Rollback: revert the single commit on `fix/s3-packed-refs-recovery` (or revert PR merge commit on `develop` via PR).
