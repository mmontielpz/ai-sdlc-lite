# V2-04F result — reconstructed Git delivery executor

## Bound and identity

- Active contract and approval: user mission `AI-SDLC-LITE-V2-04F-CODEX-CLI-001`, supplied 2026-11-14. It explicitly authorizes reconstruction, validation, target branch creation and one local commit after local gates. Root TASK.md is an unfilled template; this mission is authoritative. This task-local record preserves the historical root RESULT.md.
- Repository / verification cwd: `<HOME>/repos/ai-sdlc-lite-public-baseline`.
- Baseline: `c97cd3a306bdbc6033f6ef039ae4033bd8e7c472`, initial branch `feature/v2-04e-delivery-planner`, clean index/worktree. No divergence. Origin is the expected GitHub repository; no remote calls were made. PR #6 state is user-supplied, not independently verified.
- Recovery: `git cat-file -t 29d98d0b2a4c4bdba7c82497d868f84f248d2457` exited 128 (object unavailable). Local branches, reflogs, unreachable-object inspection and matching local artifact filenames yielded no V2-04F implementation. This implementation is reconstructed, not the original isolated commit.
- Applicable controls: root AGENTS.md, WORKFLOW.md, CHECKLIST.md, README.md and ai-sdlc-lite skill; no nested AGENTS.md in affected directories. Mission supplies approval; no additional approval is inferred from blank templates.
- Plan: preserve ai-sdlc-delivery/1; add a separately opt-in execution library, disposable Git tests, explicit host capability boundary, documentation and CI inventory update. Validate focused and full suites, available interpreter versions, whitespace and exact inventory, then integrate locally. No dependencies or release actions.
- Advisory execution window: mission turn through local handoff, with inspection, implementation and final verification checkpoints. No enforced timing budget; elapsed time UNKNOWN.

## Final implementation snapshot

SHA-256 before this evolving report; no implementation changes after these checks:

| File | SHA-256 |
| --- | --- |
| .github/workflows/ci.yml | aba8c0da49da75aba453b7ec6e2690126904090a557ea58fd38409ce639fa260 |
| ai_sdlc/delivery_executor.py | e611bdb8aa84fcb4cf505e418f53addde79940398fec211aee40703b90320c38 |
| tests/test_delivery_executor.py | 257dac97f893ddee55e46ba28f1844d5abd10b47222eb6d965b72c98bea9031b |
| docs/DELIVERY_EXECUTOR.md | 20b58f985204a87ed9771b3e141643fb9d7e095eac02112dd58f87d6b81a165c |

Authorized changed-file inventory is exactly those four paths plus this result record.
CI changes only the exact discovered-test count from 360 to 383; Python matrix and skip policy remain intact.

## Verification evidence

Environment: Linux, Python/Python 3.14.9, standard library and installed Git; tests use disposable repositories. Commands below run from the repository cwd above. Logs in /tmp are transient, not committed evidence. No live remote transport is exercised.

| Phase | Exact command / procedure | Exit | Outcome |
| --- | --- | --- | --- |
| Baseline | `python3 -B -m unittest discover -s tests` | 0 | PASS: 360 tests, 55.354s, no skips reported |
| Implementation attempt 1 | `python3 -B -m unittest discover -s tests -p 'test_delivery*.py'` | 1 (unittest; enclosing shell tail returned 0) | FAIL: 57 tests, 4 failures and 5 errors; index entry parsing used tree-field ordering |
| Corrected attempt 2 | same focused command | 0 | PASS: 57 tests; corrected index parsing, not weakened assertions |
| Final focused | `python3 -B -m unittest discover -s tests -p 'test_delivery*.py'` | 0 | PASS: 63 tests in 0.851s, including 23 new executor/security tests |
| Final regression / Python 3.14 | `python3.14 -B -m unittest discover -s tests` | 0 | PASS: all 383 tests in 55.843s, no skips reported; expected negative-path report-file collision diagnostic appeared |
| Python 3.9 availability | `command -v python3.9` | 1 | NOT_RUN: interpreter unavailable; Python 3.9 AST syntax check passed within focused suite, not runtime compatibility proof |
| Python 3.14 availability | `command -v python3.14`; `python3.14 --version` | 0 | `/usr/bin/python3.14`, Python 3.14.9 |
| Codex declaration | `python3 -B adapters/agents/codex/validate_adapter.py --config adapters/agents/codex/examples/declaration.json --project .` | 0 | PASS: CODEX_ADAPTER_READY; runtime/permission qualification NOT_RUN |
| Godot declaration | `python3 -B adapters/godot/validate_adapter.py --config adapters/godot/examples/disposable-sample/godot-adapter.json --project adapters/godot/examples/disposable-sample` | 0 | PASS: ADAPTER_READY, execution not authorized |
| Whitespace | `git diff --check` | 0 | PASS before integration; staged new files also checked at integration |
| Source security review | Inspect executor commands, child environment, approvals, exact blobs/modes/paths, remote interface and pending-journal recovery; review docs against implementation | N/A (agent review) | PASS within documented trusted-host/single-writer boundary; no production qualification claimed |

## Acceptance mapping and security limits

| Mission criterion | Evidence / result |
| --- | --- |
| Exact baseline, preserve existing work | PASS: clean baseline exactly matches mission; no existing modifications to overwrite |
| Recover or honestly reconstruct | PASS: original object unavailable; reconstruction explicitly identified |
| Explicit approval for each mutation | PASS: independent stage/commit/push/PR intents; tests deny each operation, bind SHA/files/repository/digest and exercise approval-time drift |
| Exact SHA and authorized file boundaries | PASS: full sealed file/config checks, exact index paths, SHA-256 blobs and modes, parent/message/diff proof on recovery; tests cover extra staging, deletion, literal paths and content drift |
| Safe Git environment | PASS: planner allowlist reused, hooks/attributes/unsafe Git state rejected, minimal child environment with global/system config and prompts disabled |
| Remote state / PR identity | PASS for orchestration with doubles; exact destination/ref/SHA and PR identity checked, mismatches stop; live backend qualification NOT_RUN |
| Idempotence / ambiguous outcomes | PASS: new executor recovers exact commit; pending remote intents persist through supplied durable journal; exact observed identity reconciles success, otherwise no retry |
| No force, automatic retry, credentials, merge | PASS: no force/merge/credential command or retry loop; remote errors sanitized; command-recording and ambiguity tests pass |
| Provider neutrality / contract compatibility | PASS: original planner/CLI unchanged, existing delivery tests pass; host capabilities are provider neutral |
| Python versions | 3.14 result below; 3.9 runtime NOT_RUN, AST grammar check PASS; CI matrix retained |

The host must provide a trusted approval callback, durable journal outside the
checkout, exclusive writer access, trusted Git executable and qualified remote
backend. The library does not implement those services. A backend must atomically
check expected remote state, use non-force updates and prevent duplicate PRs.
Tests validate orchestration using doubles, not an actual remote implementation.
No production Git execution took place. Required signing and CI fail closed;
the executor does not claim to satisfy them. No execution CLI was added.

## Local integration and handoff

Technical outcome: PASS for local gates. Integration was first BLOCKED (see the
historical failure evidence below), then completed in recovery mission
`AI-SDLC-LITE-V2-04F-RECOVERY-CODEX-READINESS-001` from a context where `.git`
was writable. Recovery re-verified the four implementation hashes above
unchanged, focused suite (63 tests, exit 0), full `python3.14 -B -m unittest
discover -s tests` (383 tests, exit 0, 52.5s) and `git diff --check` (exit 0).
Python 3.9 runtime remains NOT_RUN (interpreter unavailable).

Branch `feature/v2-04f-git-delivery-executor` created from baseline
`c97cd3a306bdbc6033f6ef039ae4033bd8e7c472`; exactly the five authorized paths
were staged and committed locally. The commit SHA is not recorded in this file
(self-reference); obtain it with `git rev-parse HEAD`. No push, PR, merge, tag,
release, branch deletion, force operation or paid service was used.
Human acceptance remains PENDING. Qualify a durable host journal/remote backend
separately before any live use.

## Integration failure evidence (historical, prior mission run)

- `git switch -c feature/v2-04f-git-delivery-executor`: exit 128, unable to create branch `.lock`, read-only filesystem.
- `git add -- ai_sdlc/delivery_executor.py tests/test_delivery_executor.py docs/DELIVERY_EXECUTOR.md tasks/AI-SDLC-LITE-V2-04F/RESULT.md .github/workflows/ci.yml`: exit 128, unable to create `.git/index.lock`, read-only filesystem.
- The enclosing shell continued into staged diff checks; they returned no diff because staging failed, so they are NOT evidence of a staged implementation. The exact staged inventory assertion failed (exit 1, empty inventory). No commit command was attempted.
- No permission escalation, alternate index/ref storage, permission repair or sandbox bypass was attempted. No Git lock persisted. Required integration and clean-worktree gates are BLOCKED, not waived.
- Final read-only verification: `git branch --show-current` returned `feature/v2-04e-delivery-planner`; `git rev-parse HEAD` returned the baseline SHA (both exit 0). `git status --porcelain=v1 --untracked-files=all` returned exactly the five authorized paths; `git diff --cached --name-only` was empty (both exit 0). `git diff --check` exited 0. For each of the four untracked paths, `git diff --no-index --check -- /dev/null PATH` returned 1 with empty stdout/stderr (normal no-index difference status, no whitespace findings). A read-only Python check found no persisted `*.lock` under `.git`. The report itself remains an authorized untracked file.

## Measurements

Elapsed wall time, active execution time, human waiting, observed tokens,
provider billed units, monetary cost and complete native-permission prompt counts:
UNKNOWN. Suite durations above are unittest-reported suite durations, not mission
time. Additional attempts for the initial focused failure: one successful fix
and rerun; later focused run covers added tests. No remote retry was performed.

## Human acceptance

Decision: PENDING. Reviewed revision / human decision reference: UNKNOWN.
Technical evidence does not authorize any remote or release action.
