# V2-04G result — native Git adapter and durable execution journal

## Bound and identity

- Active contract and approval: user mission `AI-SDLC-LITE-V2-04G-NATIVE-GIT-001`, supplied 2026-11-14. Root TASK.md is an unfilled template, so the mission is authoritative. It authorizes implementation, tests and documentation, and withholds commits, pushes, PRs, merges, tags, releases and branch deletion.
- Repository / cwd: `/home/mike/repos/ai-sdlc-lite-public-baseline`.
- Baseline: `b16b7e53fc6e9a5cfdab03d25e1ccf27f3911010` on `feature/v2-04f-git-delivery-executor`; working tree clean at start. At implementation time no branch or commit existed; local integration followed under mission `AI-SDLC-LITE-V2-04G-COMMIT-002` (see Human acceptance).
- Applicable controls: root AGENTS.md (Bound → Observe → Verify), README, CHECKLIST. No nested AGENTS.md.
- Preflight: existing V2-04F executor contract read (`ai_sdlc/delivery.py`, `delivery_executor.py`); focused delivery suite 63 tests PASS before and after. Existing modules unchanged.
- Scope growth: one file outside the strict implementation set was edited, `.github/workflows/ci.yml` (exact discovered-test count 383 → 409), because CI fails closed on the inventory. This follows the V2-04F precedent and is flagged for owner review.

## Implementation snapshot

SHA-256 of the final files (this report excluded):

| File | SHA-256 |
| --- | --- |
| .github/workflows/ci.yml | 4087d704686340657f4c885db7c02b1f70e2c4dc3178eacd0b81e8e4a4802ec2 |
| ai_sdlc/native_git.py | 7f801722408cafcff2b3e1942fbdbbf8920cfd6c265c0bb0e2c60792b604f432 |
| tests/test_native_git.py | 03aab553e6d110644045eecb4dcef6675c9ad4e53b3baba0c54f2428c9c82560 |
| docs/NATIVE_GIT.md | 2f6014528e46986e73061c715af397df4c436e63f77bfff37f43fa1dd981f138 |

Exact changed-file inventory (uncommitted): modified `.github/workflows/ci.yml`; new `ai_sdlc/native_git.py`, `tests/test_native_git.py`, `docs/NATIVE_GIT.md`, `tasks/AI-SDLC-LITE-V2-04G/RESULT.md`.

## Verification evidence

Environment: Linux, Python 3.14.9, installed Git, standard library only. Disposable repositories live under a per-test temporary directory. No network, remote or credential was used. All commands run from the repository cwd.

| Phase | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Preflight | `git rev-parse HEAD`; `git status --porcelain` | 0 | Baseline SHA matches; 0 changes |
| Focused (new) | `python3 -B -m unittest discover -s tests -p 'test_native*.py'` | 0 | PASS: 26 tests, ~1.1s. Two initial failures were mistakes in the new tests (an approving authorizer fixture, a non-matching tamper edit), corrected without weakening assertions; a third expectation was tightened to the stricter `UNSAFE_PATH`. |
| Focused (existing) | `python3 -B -m unittest discover -s tests -p 'test_delivery*.py'` | 0 | PASS: 63 tests |
| Discovery count | `python3 -B -c "...discover('tests').countTestCases()"` | 0 | 409 = 383 + 26; equals the CI constant |
| Full regression | `python3.14 -B -m unittest discover -s tests` | 0 | PASS: 409 tests, 53.7s, no failures |
| Mutation check | In-process scratch script, no source edits: disabled file-integrity check, recovery, authorization, state checks, chain validation, command allowlist | 0 | Each broken guard failed 2 to 11 intended tests |
| Whitespace | `git diff --check`; no-index check of the new files; tab/trailing-space grep | 0 | PASS |
| Source security review | grep for shell, eval, sockets, network, force/reset/push; read-through of argument validation, environment and journal fields | N/A | PASS within the stated boundary |
| Python 3.9 | AST parse with `feature_version=(3, 9)` inside the suite | 0 | Grammar PASS. Runtime NOT_RUN: 3.9 is not installed. |

## Acceptance mapping

| Mission requirement | Evidence / result |
| --- | --- |
| Structured operations, validated arguments, explicit allowlists | PASS: three fixed templates, subcommand allowlist, strict parameter schemas; tests for unknown keys, bad refs, paths and messages |
| No shell, no arbitrary argument forwarding | PASS: list argv, `shell=False`, spy test over every call, `_run` rejects push/reset |
| Exact repository and branch validation | PASS: real-path, layout, config allowlist, hooks, attributes, top-level and branch checks tested |
| SHA and file-integrity checks | PASS: content/mode checks before and after approval; staged blob digests and modes compared |
| Deny by default; separate authorization per mutable operation | PASS: tests for no authorizer, empty allowlist, falsy/invalid/raising authorizer, non-shared approval, approval-time drift |
| No remote operations | PASS: none implemented; source and command-set tests |
| Append-only journal with identity, authorization, expected/observed state, result, recovery, integrity | PASS: event schema, hash chain, tamper/torn-tail/lock/path tests |
| No credentials or sensitive environment stored | PASS: secrets in the parent environment and commit message absent from journal bytes; bounded schema |
| Branch creation, staging, local commits | PASS: full flow against disposable repositories |
| Crash recovery | PASS: crash after Git, before Git, during commit and during branch creation; ambiguous state blocks |
| Duplicate-operation prevention | PASS: replay, conflict, retired ids |
| Unauthorized-operation denial | PASS: journaled `denied` events, repository unchanged |
| Repository isolation | PASS: foreign journal/identity, ambient `GIT_DIR`, nested path, symlink, gitdir link |

## Security findings

1. Hash chain is tamper-evident, not authenticated. A writer with file access can forge a valid chain or drop trailing entries. Mitigation: anchor the head hash externally or sign it.
2. The authorization identity is a host-asserted string; the library cannot prove who approved.
3. Time-of-check/time-of-use gap remains between the final state check and the Git call. Drift is detected afterwards, not prevented. The host must hold exclusive access.
4. Default Git discovery uses `shutil.which` on the ambient PATH. Hosts should pass an absolute `git=` path.
5. A failed postcondition after `git add` or `git commit` leaves state as is. The library never unstages or resets, by design; a human resolves it.
6. Not defended: a hostile Git binary, a compromised host process, or filesystem races by a privileged local user.

## Limitations and not run

- ASCII-only paths and messages; no deletions, renames, submodules, LFS, signing, unborn HEAD or linked worktrees; Linux/POSIX only (`fcntl`).
- Python 3.9 runtime NOT_RUN. CI's 3.9 and skip-policy jobs NOT_RUN locally; CI shows 0 skips here, CI expects 2 on its runner.
- No execution CLI, no remote operations and no live Codex or provider integration were added or tested.
- Integration with the V2-04F executor (sharing the journal or authorization model) is not done.

## Measurements

Elapsed time, tokens, billed units and cost: UNKNOWN. Suite durations are unittest-reported only.

## Human acceptance

Decision: PENDING. Reviewed revision: UNKNOWN.

Local integration (mission `AI-SDLC-LITE-V2-04G-COMMIT-002`, owner authorized): the five inventory files were committed once on local branch `feature/v2-04g-native-git`, created from baseline `b16b7e53fc6e9a5cfdab03d25e1ccf27f3911010`, after the full suite (409 tests) passed again. The commit SHA is not recorded here (self-reference); obtain it with `git rev-parse HEAD`. No push, PR, merge, tag, release, branch deletion, force operation or paid service was used.
