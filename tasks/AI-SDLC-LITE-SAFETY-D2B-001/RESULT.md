# SAFETY-D2B-001 result — D2b: non-ASCII and malformed Git reference files

## Bound and identity

- Mission: `AI-SDLC-LITE-SAFETY-D2B-001`
- Baseline: `develop` `d82f1a7e42c81d610e64e8d9ff74a8e6d725e291`
- Branch: `fix/d2b-non-ascii-git-refs` (isolated worktree `<HOME>/worktrees/ai-sdlc-lite-d2b`)

## Root cause and reproduction

Direct reads of Git repository reference files in `ai_sdlc/delivery.py` (`snapshot()`) and `ai_sdlc/delivery_executor.py` (`_head_from_disk()`) used `.decode('ascii')`:

- `ai_sdlc/delivery.py`: `.git/HEAD`, `.git/refs/heads/<branch>`, and `.git/packed-refs`
- `ai_sdlc/delivery_executor.py`: `.git/refs/heads/<branch>` in `_head_from_disk()`

Reproduced before production changes: 8 new tests raised `UnicodeDecodeError` when `.git/HEAD`, a loose ref file, or `.git/packed-refs` contained valid UTF-8 non-ASCII branch names (e.g. `café`) or malformed non-UTF-8 bytes (e.g. `b'caf\xe9'`).

## Correction

- Added `decode_ref(raw, encoding='utf-8', code='INVALID_REF')` in `ai_sdlc/delivery.py` to decode Git reference files strictly without lossy replacement, raising `Rejected(code)` on `UnicodeError`.
- Applied `decode_ref` to `.git/HEAD` (UTF-8), loose ref files (ASCII OID, `INVALID_REF`), and `.git/packed-refs` (UTF-8, allowing valid UTF-8 non-ASCII branch names in other refs without crashing).
- Applied `d.decode_ref(..., 'ascii', 'INVALID_SHA')` in `Executor._head_from_disk()`.
- Valid UTF-8 non-ASCII branch names in `.git/HEAD` now fail closed with `BRANCH_CHANGED`, detached `HEAD` fails closed with `BRANCH_CHANGED`, and malformed reference bytes fail closed with `INVALID_REF` / `INVALID_SHA` without Git mutations or journal corruption.

## Test evidence

- 13 new tests added across `tests/test_delivery.py` (6), `tests/test_delivery_executor.py` (4), and `tests/test_delivery_native_integration.py` (3).
- Targeted D2b + D2 + D3 suite (`test_delivery`, `test_delivery_executor`, `test_delivery_native_integration`, `test_native_git`): 136/136 PASS.
- Full local deterministic suite (`python3 -B -m unittest discover -s tests`): 462/462 PASS.
- Python 3.9 AST parse check and `git diff --check`: PASS.

## Residual risks

- `GitAdapter` journal `valid_state` still enforces ASCII-only branch names (`JOURNAL_INVALID` when `recover()` attempts to record a non-ASCII observed branch name); unresolved journal operations remain preserved without mutation.
- `D1` (packed refs replay), `D4` (recovery provenance), and `D6` (Git author identity) remain open out of scope.
