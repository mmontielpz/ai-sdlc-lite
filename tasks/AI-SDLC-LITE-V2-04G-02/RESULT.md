# V2-04G-02 result — delivery executor integrated with the native Git adapter

## Bound and identity

- Active contract and approval: user mission `AI-SDLC-LITE-V2-04G-02`, supplied 2026-11-14. Root TASK.md is an unfilled template, so the mission is authoritative. It authorizes integration, tests, documentation and evidence. It withholds any branch creation, commit, push, pull, merge, PR, tag, release, branch deletion and Codex profile change.
- Repository / cwd: `<HOME>/repos/ai-sdlc-lite-public-baseline`.
- Baseline: required and observed `da95809e2aad339c56bea2d9b0d70aa93b161e27` on `feature/v2-04g-native-git`; working tree clean; no lock files. HEAD, branch and branch list (7) are unchanged at handoff. Regression baseline 409 tests was confirmed before changes.
- Applicable controls: root AGENTS.md, README, CHECKLIST. No nested AGENTS.md.
- Preflight read: `ai_sdlc/delivery.py`, `delivery_executor.py` (V2-04F contract) and `native_git.py` (V2-04G adapter and journal semantics).

## Integration architecture

`Executor(repo, plan, approve, journal, remote=None, git_adapter=None, attempt=1)`. The adapter is injected; there is no global state, shell or implicit authorization. With `git_adapter=None` the V2-04F path is unchanged.

| Concern | Design |
| --- | --- |
| Operation mapping | stage → `GitAdapter.stage`; commit → `GitAdapter.commit`. No second Git write path: the executor's own `add`/`commit` calls are unreachable when an adapter is present (spy test). |
| Authorization | Executor `approve` (bound to plan digest, head and files) and adapter `authorizer` plus `allow` entry are independent; both are required for each mutation. |
| Idempotency | Deterministic IDs `<plan digest>-stage-a<n>` and `<plan digest>-commit-a<n>`. An applied stage resumes at commit; an applied commit replays; the V2-04F recovery proof still verifies the commit identity. |
| Durable evidence | Adapter journal: expected state and authorization before the Git call, observed state after. The chain is verified before every commit attempt. |
| Ambiguity | `_reconcile()` observes pending operations (never re-runs them); ambiguous state stops with `RECOVERY_AMBIGUOUS` before any approval. |
| Retry | None automatic. Failed, not-applied and ambiguous IDs are refused before any approval is requested. Only an explicit owner-chosen `attempt` (1-9) creates new IDs. |
| Binding | Adapter type, path, repository identity and branch must match the plan. Planned deletions are refused. |
| Not added | Executor-level branch creation (a host step through the adapter), new remote behavior, a CLI. Push/PR orchestration is unchanged. |

## Implementation snapshot

SHA-256 of the final files, this report excluded:

| File | SHA-256 |
| --- | --- |
| .github/workflows/ci.yml | 9ab86f6de6cc06390f54a29de9845929e26637758c7bd08e6834e6bda16b12e3 |
| ai_sdlc/delivery_executor.py | 2c59de3c99167acfd8a5ff7408a275bb49c5a2244f6f6124f7e8e4e0092b78bf |
| tests/test_delivery_native_integration.py | 908c5c46f8a2416cdf85d1bee1c9e9872ef99274d0f71dc49c1561d42a175b28 |
| docs/DELIVERY_EXECUTOR.md | 7f88b99177a5357365e2de9c7ae3e0b158dfeedd8e2c7d250cb892fbd4e071c9 |

Changed-file inventory (all uncommitted): modified `.github/workflows/ci.yml` (exact count 409 → 427 only), `ai_sdlc/delivery_executor.py` (+71/-1), `docs/DELIVERY_EXECUTOR.md` (+32, additions only); new `tests/test_delivery_native_integration.py` (18 tests) and `tasks/AI-SDLC-LITE-V2-04G-02/RESULT.md`. `ai_sdlc/native_git.py`, `delivery.py` and the existing executor tests are unchanged.

## Verification evidence

Environment: Linux, Python 3.14.9, installed Git, standard library only. Tests use disposable repositories under a temporary directory. No network, remote or credential. Commands run from the repository cwd.

| Phase | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Preflight | `git rev-parse HEAD`; `git status --porcelain` | 0 | Baseline SHA matches; 0 changes |
| Focused (new) | `python3 -B -m unittest tests.test_delivery_native_integration` | 0 | PASS: 18 tests, first run |
| Focused (delivery) | `python3 -B -m unittest discover -s tests -p 'test_delivery*.py'` | 0 | PASS: 81 tests (63 existing + 18 new) |
| Focused (native) | `python3 -B -m unittest discover -s tests -p 'test_native*.py'` | 0 | PASS: 26 tests |
| Discovery count | `python3 -B -c "...discover('tests').countTestCases()"` | 0 | 427 = 409 + 18; equals the CI constant |
| Full regression | `python3.14 -B -m unittest discover -s tests` | 0 | PASS: 427 tests, 54.1s |
| Mutation check | In-process scratch script, no source edits: disabled reconcile, retired-ID refusal, adapter binding, journal verify, executor approval, adapter recovery | 0 | Each broken guard failed 1 to 7 intended tests |
| Python 3.9 | AST parse, `feature_version=(3, 9)`, on the three code files | 0 | Grammar PASS. Runtime NOT_RUN (3.9 not installed). |
| Whitespace | `git diff --check`; no-index check of new test; tab/trailing-space grep | 0 | PASS |

The new tests passed on the first run, so the mutation check was run to confirm they are not vacuous.

## Acceptance mapping

| Mission requirement | Evidence |
| --- | --- |
| Approved branch creation | PASS: adapter `create_branch`, then plan and delivery on the new branch, all in one journal |
| Approved staging and local commit | PASS: parent, files, message, author, clean tree, both approval layers and journal events asserted |
| Authorization denial | PASS: executor denial never reaches the adapter; adapter denial, missing authorizer and disallowed operation stop with the repository unchanged |
| Duplicate operation replay | PASS: fresh executor and adapter replay with no approvals, authorizer calls or new commits |
| Interrupted execution recovery | PASS: crash before and after Git for stage and commit; reconciled applied or not applied; new attempt needed after not applied |
| Ambiguous recovery blocked | PASS: unexplained staged state blocks all attempts with no approvals |
| Journal corruption detection | PASS: appended forgery detected before any mutation; edited journal cannot be reopened |
| Repository drift | PASS: drift before approval, during executor approval and during adapter authorization |
| Existing executor compatibility | PASS: 63 unchanged tests plus explicit no-adapter test |
| No second Git implementation / no shell / no remote / no implicit authorization / no auto-retry / no rollback | PASS: spy and source checks; failed operation not retried; no unstage or reset anywhere |

## Security findings

1. Two approvals are required per mutation by design. A host that wires both to the same human decision gets one prompt, but the library does not merge them.
2. `attempt` is an integer chosen by the host. The library cannot verify that raising it reflects an owner decision; it only guarantees that fresh approvals and authorizations are then required.
3. Reconciliation writes `recovery` entries to the journal without authorization. It changes no repository state and only records observation.
4. The executor's key/value journal is still used for remote steps. Local state is durable only in the adapter journal, so a host must retain both.
5. Behavior differs when an adapter is present: commit messages must be printable ASCII without leading or trailing space, and the commit author is the adapter identity, not repository config.
6. Inherited from V2-04G and unchanged: the hash chain is tamper-evident but not authenticated, and dropped trailing entries are undetectable. The authorization identity is host-asserted. A time-of-check/time-of-use gap remains before the Git call. A hostile Git binary or compromised host process is out of scope.

## Limitations and not run

- Python 3.9 runtime and CI's two-skip policy NOT_RUN locally (0 skips observed here).
- No live remote, push or pull-request path was exercised or added; no real provider or Codex session was involved.
- Deletions, renames, non-ASCII input and unborn HEAD are unsupported through the adapter.
- Executor-level branch creation does not exist; the host must create branches through the adapter first.

## Measurements

Elapsed time, tokens, billed units and cost: UNKNOWN. Suite durations are unittest-reported only.

## Human acceptance

Decision: PENDING. Reviewed revision: UNKNOWN.

At verification time no branch or commit was created. Local integration then followed under mission `AI-SDLC-LITE-V2-04G-02-COMMIT` (owner authorized, including acceptance of the CI count change 409 → 427): the five inventory files were committed once on the existing local branch `feature/v2-04g-native-git`, from baseline `da95809e2aad339c56bea2d9b0d70aa93b161e27`, after the 18 integration, 26 native and full 427-test suites passed again. The commit SHA is not recorded here (self-reference); obtain it with `git rev-parse HEAD`. No other branch was created. No push, pull, merge, PR, tag, release, branch deletion, force operation or paid service was used, and the Codex sandbox profile was not modified.
