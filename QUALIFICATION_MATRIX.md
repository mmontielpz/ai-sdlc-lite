# Qualification matrix (V1.0 plan)

**Status: PLAN with current evidence recorded honestly.** A cell is **VERIFIED** only when a dated record cites a command, environment and result. Otherwise it is PARTIAL, NOT RUN or UNKNOWN. An unlisted combination is NOT VERIFIED and must not be advertised as supported. Historical evidence lives in [QUALIFICATION.md](QUALIFICATION.md) (append-only); this file defines what V1.0 must still prove. See [ROADMAP.md](ROADMAP.md).

## Dated notes (prior rows are never edited)

**2026-11-26 (consolidation; no row edited).** This matrix owns qualification and release-gate **status** and the claims that status allows. It does not own project state, decisions (see the decision register, `docs/product/OWNER_DECISION_AMENDMENTS.md`) or the roadmap. The tables below are dated historical rows. The current Claude Code smoke status is note 2026-11-21 (2) below. The "Priority order" section (Codex x Linux first, 2026-11-12) is superseded by OD-01 (2026-11-18): only Claude Code carries a qualification commitment; Codex, Copilot and Antigravity rows remain historical evidence labelled "not verified (not in committed scope)".

**2026-11-21.** (1) **CI simplification (M063):** Regular PRs and pushes run one mandatory deterministic check on Linux (`ubuntu-24.04`) with Python 3.14 (`ci-gate` required); Python 3.9 compatibility is retained via manual `workflow_dispatch` (`python_39=true` default). (2) **Claude Code 2.1.329 (`claude-sonnet-5-5`) Linux smoke (operator-orchestrated, `2.0.0.dev1` wheel from `219496a` + M063 CI change):** native Skill discovery under `.claude/skills/ai-sdlc-lite/` (`PASS`), Bound stop at Gate 1 (`PASS`; `$0.093`, `13.9s`), Observe + Verify (`PASS`; `$0.215` cumulative, `25.1s`), independent `unittest` (`OK`), `experience record-verify` + `validate` (`events=1`), planted out-of-scope negative control (`BLOCKED` exit `2`), and `init --uninstall` (`RESULT: UNINSTALLED`). An earlier run on a fixture lacking `tests/__init__.py` demonstrated BOV stop-condition compliance when Claude Code refused to edit outside `allowed_paths`. (3) **Independent human clean-room qualification (G3/G10):** `PENDING` (agent-orchestrated runs do not satisfy G3/G10). (4) **macOS and Windows:** deferred (`NOT RUN`).

## Operational Qualification Model (Q1–Q3 mapping G1–G10)

| Tier | Scope | Mapped Gates | Current Status |
|---|---|---|---|
| **Q1: Automated verification** | Deterministic suite (`743` tests, `30` modules), wheel packaging (`BuiltWheelTests`), contracts, security/integrity regressions | **G1, G4, G8** | **PASS (Linux Python 3.14 & 3.9)** (`44925337695`) |
| **Q2: Functional qualification** | Clean wheel install, live Claude Code smoke, BOV, Experience capture, safety boundaries, independent clean-room | **G2, G3, G5, G6, G9, G10** | **PARTIAL** (Claude Code 2.1.329 Linux smoke recorded; G3/G10 independent human run `PENDING`; macOS/Windows deferred; G9 re-verification pending release) |
| **Q3: Product validation** | Real project application (JACK, etc.), human acceptance, measured outcomes | **G7** | **NOT MET** (pending M064/M065) |

**2026-11-18.** (1) Owner decision OD-01 amends D6: Claude Code is the only agent targeted for V1–V3; Copilot, Codex and Antigravity carry no qualification commitment and are "not verified (not in committed scope)". Their rows below remain as historical evidence. The "Codex × Linux first" priority text below predates this decision. (2) Claude Code: smoke NOT RUN, deep NOT RUN. A read-only `claude --version` on the author's workstation reported 2.1.327; this is an observed version string only, not discovery, install or qualification evidence. (3) The README's "one live Copilot CLI task observed to PASS" is an owner-observed single run; the Copilot row's smoke column (NOT RUN) records that no repeatable, recorded smoke exists. They describe different evidence and are both retained. (4) Platforms: Linux only (CI: Ubuntu 24.04, Python 3.9 and 3.14, unit tests); macOS and Windows NOT RUN. (5) Release gates G1–G10 and the reporting rules below are unchanged. (6) **2026-11-18, Claude Code 2.1.327 on Linux (`-p` mode):** a bounded discovery experiment with synthetic Skills observed that a Skill under `.claude/skills/` was listed and resolved and one under `.agents/skills/` was not; see `docs/qualification/CLAUDE-C1B-runtime-discovery.md` (in the source repository; not part of the installed bundle). This is an observation, not a smoke or deep run: the Claude Code row's smoke and deep stay NOT RUN, and the real bundle was not exercised.

## Smoke versus deep

| Level | Purpose | Cost | Pass means |
|---|---|---|---|
| **Smoke** | Does it install, get discovered and complete one trivial bounded task end to end? | Minutes; one tiny fixture repo; no paid inference without owner approval | Skill found, plan gate respected, `verify` returns PASS on a correct change and BLOCKED on a planted violation, uninstall is clean |
| **Deep** | Does it hold up under realistic and adversarial conditions? | Hours; real project; owner-approved budget | Smoke plus: dirty tree, wrong branch, an injection string in a repo file, an attempted test edit, an out-of-scope edit, interruption mid-task with recovery, and recorded time, token and permission observations (UNKNOWN where not measurable) |

Evidence required for every run: tool and OS versions, exact commands, exit codes, `verify` JSON report, sanitized transcript excerpt (no secrets). Executed by the agent under test or by a human, recorded by a human. Staged or simulated runs are labelled as such and do not count.

## Priority order (owner-approved current sequence)

The current [roadmap sequence](ROADMAP.md#current-execution-sequence--owner-approved-priorities), authorized for documentation reconciliation by mission AI-SDLC-LITE-CODEX-001B, targets **Codex × Linux first**: CODEX-002 adapter, CODEX-003 smoke, CODEX-004 deep after N04C consolidation. No paid run is authorized by this priority decision. Then GQ-RUNTIME, GQ-SAFETY, GQ-DEVELOPMENT (CREATE / EVOLVE / RECOVER), DOGFOOD-001, FOB-P0 and STUDIO-INTEGRATION follow their individual gates. Claude Code remains a long-term target under historical N07 / Part B; the historical Claude-first priority is superseded, not its milestone definition.

Each run needs owner approval of the exact version/platform, fixture, commands, permissions, evidence custody and budget. Codex CLI 0.167.2 help was inspected in CODEX-001; capabilities discovered in help are not runtime qualification. Smoke must precede deep; only verified deep evidence qualifies the agent. Godot runtime gates Q3–Q9 and development gate Q10 require actual evidence. No FOB or Studio access is authorized; future work requires owner-selected baselines, disposable workspaces and demonstrated isolation without real-save access.

### Qualification stages and gates

| Stage | Acceptance evidence | Current status |
|---|---|---|
| Implemented | Files present at a named snapshot | N03/N04 committed at baseline historical-development-snapshot; CODEX-002 adapter implemented, uncommitted |
| Unit-tested | Exact deterministic commands, snapshot and results | Handoff reports 178 total (138 prior + 40 Godot configuration); not rerun here |
| Adapter-ready | Consistent declaration; synthetic sample validates | N04 configuration level only; no execution authorization |
| CODEX-003 smoke | Discovery, BOV approval, bounded task/checks, verifier PASS and planted violation BLOCKED, clean uninstall where applicable; human-recorded evidence | NOT RUN under current qualification plan |
| CODEX-004 deep | Smoke plus dirty/wrong baseline, injection, protected/test/governance/scope violations, interruption/resume, owner-controlled recovery, demonstrated confinement with synthetic canaries and independent observation | NOT RUN; Codex not qualified |
| GQ-RUNTIME | Real import/headless tests through approved existing runner; Q3–Q9 scope, isolation, failure and evidence gates; external evidence | NOT RUN; Godot not runtime-qualified |
| GQ-SAFETY | Expanded N06 adversarial scenarios after runtime gates, with preservation and no automatic recovery | NOT RUN |
| GQ-DEVELOPMENT | CREATE / EVOLVE / RECOVER, regression evidence, Q10 gameplay/GUI and human acceptance | NOT RUN; Godot not development-qualified |

Declared isolation, private HOME/XDG and disposable workspaces do not prove OS confinement. Schema-valid output and sealed hashes do not prove authentic custody or independent execution. Record unavailable tokens, billed units, elapsed time and charges as UNKNOWN; keep them separate.

CODEX-002 adds deterministic declaration tests for CLI 0.167.2 and DELIVERY-001 regression checks. CODEX_ADAPTER_READY is not CODEX_SMOKE_QUALIFIED or CODEX_DEEP_QUALIFIED. These tests do not change any live-agent qualification row below; the source interfaces and limits are described in `docs/qualification/CODEX-002-summary.md`.

## 1. Agents

| Agent | Skill discovery / install | Instruction file | Native permissions | Smoke | Deep | Evidence today |
|---|---|---|---|---|---|---|
| GitHub Copilot CLI | PARTIAL: `copilot skill add --project` observed on CLI 1.0.109 (`QUALIFICATION.md`, README) | `AGENTS.md` | native prompts, optional sandbox setting UNVERIFIED | NOT RUN (live trials were stopped or staged) | NOT RUN | `examples/copilot-live`, `QUALIFICATION-003` |
| OpenAI Codex | PARTIAL: explicit invocation observed once; automatic discovery UNVERIFIED | `AGENTS.md` | CLI 0.167.2 help inspected (CODEX-001); effective approval/sandbox behavior UNVERIFIED | PARTIAL (011A–C slices, historical) | NOT RUN | `examples/codex-live`, `QUALIFICATION.md` |
| Claude Code | UNKNOWN: no Skill install or discovery evidence (long-term target; historical N07 retained) | UNKNOWN (instruction-file behaviour not recorded here) | UNKNOWN | NOT RUN | NOT RUN | acted as executor of missions only, not a tested target |
| Agy | **Product identity unverified** (see [ARCHITECTURE.md](ARCHITECTURE.md#agy-identity-local-evidence-only)) | UNKNOWN | UNKNOWN | NOT RUN | NOT RUN | local binaries exist; never executed or documented here |

Per-agent checks (same for all): discovery, instruction-file compatibility, tool-permission model, shell boundary, context handling, human-approval support, test execution, evidence reporting, recovery.

## 2. Platforms (installer, CLI, test suite; independent of any agent)

| Platform | Python / Git | Unit suite | CLI smoke | Symlink and permission semantics | Evidence |
|---|---|---|---|---|---|
| Linux | recorded Python 3.14.9 | Reported prior N04 result: 178 tests OK on this host, 2026-11-12 (68 existing + 43 verifier tests, including 8 Git-execution regression tests, + 27 contract tests: 19 golden-report scenarios and registry checks, + 40 Godot adapter configuration tests) | NOT RUN (no `ai-sdlc` entry point yet) | exercised by tests | N04 handoff; not independently rerun in CODEX-001/001B |
| macOS | UNKNOWN | NOT RUN | NOT RUN | NOT RUN | none |
| Windows (native) | UNKNOWN | NOT RUN | NOT RUN | NOT RUN: symlink creation, `0o600`, path separators, CRLF, long paths, `git` availability all differ | none |

Windows via WSL is Linux evidence only; it does not qualify native Windows. Minimum Python version must be stated and tested at the lowest claimed version (installer text says 3.9+; unverified).

## 3. Use cases (project adapter plus verification strategy)

| Use case | Adapter needs | Smoke fixture | Deep fixture | Status |
|---|---|---|---|---|
| Frontend / web | npm or pnpm test, lint, build; browser optional and off by default | tiny app, unit test only | real SPA with a lockfile and dependency-change attempt | NOT RUN |
| Backend / REST API | test runner, loopback-only server, DB isolation | endpoint plus unit test | integration test against a disposable DB; network rule | NOT RUN |
| Python automation | `unittest`/`pytest` | `examples/small-fix` and `examples/*-live` | script that touches files and env | PARTIAL (historical small slices) |
| AI / ML | seeded eval, dataset and model paths protected, cost cap | deterministic metric on a toy dataset | nondeterminism, GPU and paid-API budget | NOT RUN |
| Data engineering | dry-run, schema and row-count checks, prod isolation | CSV transform with a golden file | partitioned pipeline with protected data paths | NOT RUN |
| Godot / FOB | headless script runner, save and asset protection | minimal throwaway Godot project | FOB as a read-only brownfield case study, with an owner-approved isolated worktree | **ADAPTER_READY (configuration level only, disposable sample):** `adapters/godot/`, 40 tests. **RUNTIME_QUALIFIED: no. DEVELOPMENT_QUALIFIED: no.** Gates Q4, Q5, Q8, Q10 NOT RUN; Q3, Q6, Q7, Q9 DECLARED only (see `adapters/godot/README.md`) |
| Rust / C++ CLI | `cargo test`, `cmake`/`ctest`; build scripts count as untrusted code | one crate | crate with a `build.rs` and a dependency attempt | NOT RUN |
| Brownfield / legacy | characterization tests first; governance already present | repo with an existing `AGENTS.md` | legacy code with no tests; dirty tree; many branches | NOT RUN |
| Multi-repository | one contract per repo; cross-repo baseline list | two small repos | coordinated change with separate approvals | NOT RUN, and the multi-repo model itself is undecided |

## 4. Security scenarios (from QUALIFICATION-002, S01–S18)

Each release-candidate run must record, per scenario, whether the control is instruction-only, post-execution detection, technically enforced or native-sandbox-dependent, plus the test that demonstrates it. Present state: only S01, S11–S14 and S17 have post-execution detection (`tests/test_verify_scope.py`); For S18, the verifier's own Git invocation is mitigated for the listed vectors (`core.fsmonitor`, hooks, environment injection, filter and diff drivers; marker-file tests) but untrusted project scripts run by an agent are not. S02–S10, S15, S16 and the rest of S18 depend on the agent's native sandbox or remain instruction-only. See [SECURITY.md](SECURITY.md).

## 5. Reporting rules

1. One dated row per run; never edit a prior row. Supersede it with a new one.
2. Report PASS, PARTIAL, BLOCKED or NOT RUN. Never fill missing data with zero or an assumed result.
3. "Supported" in public documentation requires a VERIFIED **smoke** row for that exact agent, platform and version. "Qualified" requires a VERIFIED **deep** row. Otherwise write "not verified".
4. A passing unit suite proves installer and verifier logic only. It is not agent or runtime-safety evidence.

## Canonical import boundary

This candidate includes source and configuration tests, not private execution reports. The technical reference describes the interfaces; no imported history or summary qualifies runtime execution. Public README/QUALIFICATION corrections remain authoritative for their narrowly scoped historical public observations.
