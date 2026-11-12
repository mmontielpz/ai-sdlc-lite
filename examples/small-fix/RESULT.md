# SMALL-FIX-001 execution evidence

Outcome-first · Time-conscious · Token-aware. Technical correctness is supported by tests and scope evidence; unavailable usage measurements do not become zero or claimed savings.

## Historical evidence — fixture preparation and repair

This section transcribes the actual AI-SDLC-LITE-004B preparation and AI-SDLC-LITE-004C / SMALL-FIX-001 execution evidence from the owner-agent conversation. It is reported historical evidence, not a new execution by an independent tester. The original repair allowed only source edits, so its conversation report is recorded here under the separate AI-SDLC-LITE-005B authorization.

- **Task / approved revision:** SMALL-FIX-001 / 1; [archived task](TASK.md).
- **Plan approval:** explicitly GRANTED by the owner in the message headed `MISSION: SMALL-FIX-001 — Execute Approved Plan`, with `TASK REVISION: 1`. It authorized `text.strip().lower()`, affected docstrings, existing tests, and hash verification only.
- **Repository baseline:** NO COMMIT; 14 existing project files were untracked. Scope was assessed using file hashes and source comparison, not an empty tracked diff.
- **Environment:** local Python 3.14.9, standard-library unittest. Exact model and run-specific client/server versions were not captured and are UNKNOWN.
- **Change:** only `examples/small-fix/normalize.py`; changed the return expression and affected docstrings. No files added or removed during repair; all other 13 project-file hashes were unchanged.
- **Technical outcome:** PASS. Human acceptance remains PENDING; later audit/correction authorization does not grant acceptance.

### SHA-256 anchors

| Artifact | Historical SHA-256 |
| --- | --- |
| Original defective source | `eed3458a7eee46b41d786169ed7034b3d8a80cbe6c3e5a78fc41e2015c42276a` |
| Verified repaired source | `821b2502380d5f34f84daf3842730d9f95321bcb5e11ec0c83493d51053d45d8` |
| Immutable tests, before and after | `4786856c734810a12b12bd874cd8d672edd5ada0fa5844af00ee3bc722a7b10b` |

### Deterministic checks

Test command: `python3 -B -m unittest -v test_normalize.py`, working directory `examples/small-fix/`.

| Historical execution | Outcome | Exit code |
| --- | --- | --- |
| 004B fixture preparation | Five tests; three passed, two failed | 1 |
| 004C read-only preflight baseline | Five tests; three passed, two failed | 1 |
| SMALL-FIX-001 after approved repair | Five tests; five passed | 0 |
| SHA-256 comparison of all 14 project files | Only normalize.py changed; no additions or deletions | 0 |
| `git status --short --untracked-files=all` and `sha256sum examples/small-fix/normalize.py examples/small-fix/test_normalize.py`, from repository root | Existing untracked paths preserved; hashes match the anchors | 0 |

| Behavior | Baseline | Final |
| --- | --- | --- |
| Mixed case | passed | passed |
| Surrounding spaces | failed: retained spaces | passed |
| Tabs/newlines | failed: retained surrounding whitespace | passed |
| Empty input | passed | passed |
| Preserved internal whitespace | passed | passed |

### Acceptance criteria

| Criterion | Historical result and evidence |
| --- | --- |
| AC-1: five behavior cases | Met; final unittest output reported five tests and OK, exit 0. |
| AC-2: immutable tests | Met; identical test SHA-256 before and after. |
| AC-3: source-only repair | Met; comparison of 14 project files found only normalize.py changed. |
| AC-4: approval and honest reporting | Met; read-only BOUND plan stopped before editing; owner's revision-1 approval preceded the patch; unknown measurements were disclosed. |

### Time and usage

All known timestamps below are system UTC clock observations on 2026-11-12, recorded in the execution conversation. They are not inferred message-arrival timestamps.

| Milestone | UTC time |
| --- | --- |
| First task-start clock observation | 03:45:24Z |
| Preflight / plan preparation clock observation | 03:45:35Z; exact plan-delivery time UNKNOWN |
| Approval first observed before implementation | 03:46:17Z; exact owner-message arrival time UNKNOWN |
| Implementation completed | 03:46:23Z |
| Five-test verification completed | 03:46:23Z |
| Hash/scope verification completed | 03:46:34Z |
| Final report fully delivered | UNKNOWN |

| Metric | Value | Units | Source / method and window |
| --- | --- | --- | --- |
| Start-to-verification wall time | 70 | seconds | Difference between system UTC observations 03:45:24Z and 03:46:34Z; includes approval waiting, excludes report-generation time. |
| Full delivery wall time | UNKNOWN | seconds | No reliable final-delivery boundary recorded. |
| Human effort / active work time | UNKNOWN | seconds | Not separately timed. |
| Retries of final test command after repair | 0 | additional attempts | Execution tool record contains one final unittest invocation; baseline checks are separate phases. |
| Observed input / output / cached tokens | UNKNOWN | tokens per category | Local session inspection did not establish a reliable task-specific starting counter; no valid task window. |
| Provider-reported billed units | UNKNOWN | UNKNOWN | No task-attributed provider billing evidence. |
| Monetary cost | UNKNOWN | UNKNOWN currency | No task-attributed charge evidence. |

Token counts do not establish monetary charges. No productivity or token optimization is demonstrated by this single run.

## New verification — AI-SDLC-LITE-005B

The current source and test hashes were rechecked against the repaired-source and immutable-test anchors before documentation edits. Reproducibility is checked using the exact commands in [README.md](README.md), including an isolated reconstruction of the historical defective source; it does not overwrite normalize.py or alter the tests.

- **Baseline replay:** executed the second Bash block in README verbatim from the example directory. Both SHA-256 assertions passed; the unchanged five tests produced three passes and the expected two trimming failures, exit 1. Temporary files were cleaned up.
- **Current repaired implementation:** `python3 -B -m unittest -v test_normalize.py`, from the example directory, produced five passes and exit 0. Repeating these checks was justified by validating the newly documented replay and current-state commands.
- **File integrity / links / scope:** repaired source and immutable tests retain their anchors. The four root contracts and unrelated files remain unchanged; correction scope is README.md, CHANGELOG.md, and the example README, TASK archive notice, and RESULT. Local links, Markdown structure, and final diffs were reviewed separately from the historical repair.

## Codex discovery and qualification limits

Automatic AGENTS.md startup discovery remains PARTIAL. Explicit reading of the root contract and subsequent behavior were demonstrated. Inspection of the existing matching session metadata found no independently identifiable startup discovery receipt; absence of that receipt does not prove discovery failed. No additional coding task was launched to test discovery.

One bounded run supports the demonstrated workflow, not general compatibility, beginner adoption, or improved delivery time. Full delivery time, human effort, and tokens remain unavailable. Framework instructions are procedural controls. Phase 05 — Codex Audit & Qualification remains mandatory before Phase 06 — Copilot CLI Compatibility; no Phase 06 execution is authorized here.

## Lifecycle and human decision

- **Plan / Design:** task revision 1 and explicit owner-approved BOUND plan.
- **Build / Test:** repaired source and historical criterion evidence above; later replay evidence is labeled separately.
- **Deploy:** NOT PERFORMED; no release action authorized.
- **Maintain:** owner reviews evidence closure and decides whether to authorize Phase 06. No code follow-up identified within these five cases.
- **Human acceptance:** PENDING. No explicit acceptance decision for the repaired snapshot is recorded.
- **Reviewed snapshot / human acceptance date / decision reference:** UNKNOWN until the owner explicitly accepts or rejects it.
