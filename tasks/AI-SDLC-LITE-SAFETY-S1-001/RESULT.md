# SAFETY-S1-001 result — Git failure classification and the D3 fix

## Bound and identity

- Active contract and approval: user mission `AI-SDLC-LITE-SAFETY-S1-001`, supplied 2026-11-15. It authorizes tests, the D3 fix, local commit, push of an isolated branch and one draft PR; it withholds readiness, merge, S2, S3, protection, tags and releases.
- Baseline: `develop` `512ea7489ea4ec17dcb5aaf5081c186ca50e360f`, `master` `7f925cd0c45b6501d743d09ebd8c9569edced40e`. Suite at baseline: 427 tests, 2 expected skips. CI: Python 3.9, 3.14 and `ci-gate`.
- Branch: `fix/s1-git-failure-classification`, created from the exact `develop` commit.
- Scope: native Git adapter failure classification only. D1 (packed refs), D2 (non-UTF-8 recovery) and D4 (recovery provenance) are explicitly out of scope.

## D3 — root cause and fix

`GitAdapter._mutate` re-observes the repository after a Git error. When that observation also failed, an `except d.Rejected` branch set `observed = None` and fell through to `journal.append('end', result='failed', ...)`. That recorded a *confirmed failure* with no evidence, although the change might have applied. The operation was then not `pending`, so `unresolved()` stayed empty, `recover()` skipped it, and only incidental preconditions (`INDEX_NOT_EMPTY`, `STAGED_FILES_MISMATCH`, `BRANCH_EXISTS`) prevented a follow-on mutation.

The existing journal schema already represents the required state, so **no new state, event or schema change was made**: `end` accepts only `applied` or `failed`, a `begin` without `end` derives `pending`, `unresolved()` includes `pending`, new mutations are blocked with `JOURNAL_UNRESOLVED`, and `recover()` reconciles pending operations by observation.

Fix (one behavioral line, `ai_sdlc/native_git.py`): when the outcome cannot be observed, record no result and raise `GIT_OUTCOME_UNKNOWN`, leaving the operation `pending`.

## Tests added (13)

`tests/test_native_git.py` (+12; 26 → 38), using disposable repositories and deterministic fault injection (an interceptor for the adapter's own Git calls, and a wrapper `git` executable); no sleeps, no real timeouts, no providers.

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | `add` applies, then `TimeoutExpired` | journaled `applied` / `APPLIED_AFTER_ERROR`; replay makes no second begin or authorization |
| 2 | `commit` applies, then `OSError` | `applied` / `APPLIED_AFTER_ERROR`; one commit |
| 3 | `commit` applies, wrapper exits 1 | `applied` / `APPLIED_AFTER_ERROR` |
| 4 | `switch -c` applies, then timeout | `applied`; adapter branch updated |
| 5 | timeout before Git runs | `failed` / `GIT_OUTCOME_UNKNOWN`, observed state equals expected; id retired; new id works |
| 6 | file changes just before `add` | `POSTCONDITION_FAILED`; later stage and commit fail closed |
| 7 | extra file staged just before `commit` | `POSTCONDITION_FAILED`; commit recorded, never reset |
| 8 | **D3** `add` applies, outcome unobservable | stays `pending`, `unresolved()` reports it, next mutation `JOURNAL_UNRESOLVED`, `recover()` → `RECONCILED_APPLIED`, replay without re-authorization |
| 9 | D3, not applied, unobservable | `recover()` → `RECONCILED_NOT_APPLIED`; id retired; new id works |
| 10 | D3, `commit` applied, unobservable | recover → applied, replay, still exactly one commit |
| 11 | D3, `switch -c` applied, unobservable | recover → applied and adapter branch updated |
| 12 | D3, unexplained state while unknown | `recover()` → `AMBIGUOUS`; mutations blocked |

`tests/test_delivery_native_integration.py` (+1; 18 → 19): a lost stage outcome is reconciled by the next executor, which resumes at commit without repeating the stage or its approvals.

## Red / green evidence

| Check | Result |
| --- | --- |
| New tests against the unmodified baseline `native_git.py` | 7 characterization tests pass; the 5 D3 adapter tests FAIL (`unresolved() == []`, journal `['header','begin','end']`, `recover() == {}`) |
| Integration test against the baseline source (scratch copy) | FAIL: `('failed', []) != ('pending', [...])` |
| Same tests with the fix | all pass (38 native, 19 integration) |
| Mutation checks (scratch copies) | never reclassify as applied → 4 tests fail; postcondition recorded as applied → 2 fail; timeout-before-Git left pending → 1 fails; D3 fix reverted → 6 fail; `recover()` ignoring state → 8 fail |

## Verification

Environment: Linux, Python 3.14.9, installed Git, standard library only; `copilot` excluded from `PATH` as in CI. No network, remote or credential in the tests.

| Command | Outcome |
| --- | --- |
| `python3.14 -B -m unittest -v tests.test_native_git` | PASS: 38 tests |
| `python3.14 -B -m unittest discover -s tests -p 'test_native*.py'` / `'test_delivery*.py'` | PASS: 38 / 82 tests |
| CI gate script extracted from `ci.yml`, full suite | PASS: `Discovered=440 Run=440 Skipped=2 Modules=16`, exactly the 2 expected skips, 0 failures |
| AST parse with `feature_version=(3, 9)` of the three changed Python files | PASS (3.9 runtime NOT_RUN locally; CI runs it) |
| `git diff --check` | PASS |

## Changed files

SHA-256 of the final files, this report excluded:

| File | Change | SHA-256 |
| --- | --- | --- |
| ai_sdlc/native_git.py | fix (+3/-1) | 96ee42927a998b2b5072ecd34de3fd230d3f1faa5777601b7527cc877a143d30 |
| tests/test_native_git.py | +215/-1 | f26610a6042f6ef7146354efc7db6fbef5733ce10215feb7a563ad39f18ea1b4 |
| tests/test_delivery_native_integration.py | +28 | ae3f9f8ddc8928b4e6b733c58f6dde1951b9ce0c16a519d71c04b185c3acef73 |
| docs/NATIVE_GIT.md | +6 | 6eb5e23b4d3af96e37313301e0731111c0d4c8f737efef3b3701bef8b97f93de |
| tasks/AI-SDLC-LITE-SAFETY-S1-001/RESULT.md | new | this record |

No product behavior other than the D3 path changed. CI configuration is untouched, so the test count is not asserted anywhere and needs no edit.

## Limitations and remaining risks

- **A Git error followed by a state that is observable but matches neither the expected pre-state nor the postcondition** is still journaled `failed` (existing behavior, not part of D3). A partially applied multi-file `git add` that exits non-zero is the realistic case; later preconditions block follow-on mutations, but the label is conservative only for the unobservable case.
- `GIT_OUTCOME_UNKNOWN` now also surfaces for a nonzero Git exit whose state cannot be observed, where the caller previously saw `GIT_FAILED`.
- D1, D2 and D4 remain open (S2 and S3 are not started). D2 can still leave an operation pending through an uncaught `UnicodeDecodeError`, which is fail-closed.
- Python 3.9 runtime of the new tests is verified only by CI.
- Human acceptance: PENDING. No readiness, merge, tag, release, protection or setting change was made.
