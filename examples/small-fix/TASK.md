# Task: repair name normalization

Archived pre-execution contract, revision 1. The pending fields below preserve the preparation state; they are not the current execution status. The owner subsequently approved revision 1 and the repair was executed, as recorded in [RESULT.md](RESULT.md). This archive grants no new repair authorization; use the [README](README.md) for baseline replay.

## Plan — Bound

- **Task ID:** SMALL-FIX-001
- **Task revision:** 1
- **Status:** PREPARED; repair authorization and plan approval PENDING.
- **Baseline:** intentionally defective `normalize.py`; preparation hashes and observed tests are in [RESULT.md](RESULT.md). At execution, record the actual commit or NO COMMIT, source/test hashes, and existing changes. Stop if the fixture no longer matches its prepared baseline.
- **Objective:** lowercase string input and remove surrounding whitespace while preserving internal whitespace.
- **In scope:** the later repair may modify only `examples/small-fix/normalize.py`.
- **Out of scope:** test edits, documentation edits, additional files, input-type validation, broader normalization features, and root contract changes.
- **Constraints:** existing Python 3 standard library only; no dependencies, external services, telemetry infrastructure, commits, pushes, tags, deployments, or publication. All other existing work must remain unchanged.

## Design — proposed; not approved

Inspect the root instructions and fixture read-only. Reproduce the baseline failure, explain the smallest function change, and propose a plan. After explicit approval, change only the function implementation, verify, and hand off. No new abstraction is needed.

Stop for a changed baseline/test hash, instruction conflict, required scope growth, material approach change, unexpected source changes, or inability to run the agreed checks. Obtain renewed approval before affected work if scope or approach changes. Do not change tests to improve results.

## Test — Verify

Working directory for all commands below: `examples/small-fix/`.

| ID | Criterion | Exact check and expected result |
| --- | --- | --- |
| AC-1 | Mixed case, surrounding spaces, tabs/newlines, empty input, and internal whitespace behave as intended. | `python3 -B -m unittest -v test_normalize.py`: baseline has two failures; repaired state has five passes, exit code 0. |
| AC-2 | Immutable tests are unchanged. | `sha256sum test_normalize.py`: matches the preparation hash in RESULT.md before and after repair, exit code 0. |
| AC-3 | Only normalize.py changes during repair. | `git status --short --untracked-files=all` plus before/after file hashes and source diff; record command exit codes. Existing untracked files are baseline work, not new repair changes. |
| AC-4 | Human plan approval precedes changes; evidence and unknowns are truthful. | Review timestamped approval and milestones, command results, and observation fields in the conversation handoff; human review has no command exit code. |

For a repository without commits, `git diff` alone omits untracked files. Preserve a read-only baseline source snapshot in the conversation and compare it with final source content; record SHA-256 hashes. Use `sha256sum normalize.py test_normalize.py` to identify both states.

## Plan approval — before Build

- **Decision:** PENDING
- **Approved task revision and proposed plan reference:** UNKNOWN
- **Human / timestamp with timezone / explicit approval reference:** UNKNOWN

AI-SDLC-LITE-004B authorizes fixture preparation only. It does not approve this repair. Record approval and evidence in the conversation so documentation remains immutable during repair.

## Deploy and Maintain

Deploy is not performed: no release action is authorized. Maintain records any unresolved issue or explains why no follow-up is needed. Use [RESULT.md](RESULT.md) as the reporting structure, delivered in the conversation. Human acceptance of the final code snapshot remains separate and pending until explicitly recorded.
