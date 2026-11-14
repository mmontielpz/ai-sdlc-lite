# AI-SDLC Lite: roadmap

**Status: PLAN with an owner-approved current execution sequence (2026-11-12, mission AI-SDLC-LITE-CODEX-001B).** Approval covers this documentation reconciliation and execution priorities; it does not authorize implementation, commits, runtime runs or spending. The earlier FOB-first plan is preserved as historical context. Nothing below is released or qualified unless it cites evidence. See [ARCHITECTURE.md](ARCHITECTURE.md) for design and [QUALIFICATION_MATRIX.md](QUALIFICATION_MATRIX.md) for the test matrix.

**Two roadmaps, one product.** The current execution sequence below governs priority. **Part A** preserves the historical **FOB-first MVP**: AI-SDLC-Lite → Godot → FOB → FOB Game Studio. **Part B** is the long-term **Universal V1.0** (the original P0–P6 phases and backlog S01–S22, preserved below and reclassified, not discarded). Later: Website pilot → independent-evaluator evaluation → Universal V1.0. Part A may not weaken Part B: the core stays project-agnostic and FOB-specific material lives only in adapters or in FOB's own repositories.

**Product:** a Universal Coding Agent Skill plus a lightweight verification CLI (`ai-sdlc init | doctor | verify`). It must stay light, open-source friendly, agent-agnostic, platform-independent and project-agnostic. No mandatory browser, container, database or orchestration server. FOB and any other project are validation cases, never the architecture.

## 0. Canonical candidate baseline

This sanitized roadmap preserves milestone definitions and dependencies.
Original execution reports and private Git provenance remain private.
The source interface includes the offline verifier and declarative adapters;
live agent, engine, project and install qualification require their named gates.
No milestone is completed by importing this document.

## Current execution sequence — owner-approved priorities

Authority: mission **AI-SDLC-LITE-CODEX-001B-ROADMAP-RECONCILIATION**. This additive sequence supersedes the earlier execution order and Claude-first priority, without renumbering or redefining historical N01–N09, S01–S22, or decisions D1–D14. Historical dependencies remain attached to those milestones; mappings below reuse relevant work and do not declare them complete.

**Candidate context:** the canonical integration is an uncommitted local import. Earlier status/count wording below is planning context, not evidence for this tree. Use current independent checks and the technical reference; no private report is required.

| Milestone | Dependencies | Acceptance gates | Owner approval required |
|---|---|---|---|
| N04C | N03 and existing N04 implementation; this reconciliation | Review only N04 files; reproduce 178 tests with bytecode disabled; whitespace check; core and golden reports unchanged; inspect final diff | Approve reviewed revision and any local commit under the applicable N04C contract; no push implied |
| CODEX-002 | N04C | Thin adapter under `adapters/agents/codex/`; version-specific discovery, instructions, permissions and evidence notes; deterministic validation/drift checks; existing BOV/verifier reused; core unchanged | Approve bounded adapter task and checks; no live inference implied |
| CODEX-003 | CODEX-002 | Real Codex smoke in a disposable fixture: skill discovery, approved change, checks, PASS for correct scope and BLOCKED for planted violation; human-recorded evidence; clean uninstall where installed | Approve exact CLI version, fixture, commands, permissions and inference budget |
| CODEX-004 | CODEX-003 | Deep matrix: dirty/wrong baseline, injection, test/governance/scope violations, interruption and resume, owner-controlled recovery, confinement probes using synthetic canaries, independent observation; honest usage/time UNKNOWNs | Approve each run, threat model, evidence custody and budget; accept reviewed qualification record |
| GQ-RUNTIME | N04C and CODEX-004 | Disposable Godot fixture and existing project-owned runner; real import and headless tests; Q3–Q9 evidence for scope, isolation, failures and integrity; no real-save access | Approve fixture, engine/runner, exact commands and demonstrated isolation boundary before execution |
| GQ-SAFETY | GQ-RUNTIME | Expand adversarial runtime coverage using N06 scenarios; protected paths, dirty baseline, ignored files, failure/interruption and controlled recovery; preserve baseline and external evidence | Approve safety scenarios and any owner-directed cleanup; no automatic recovery |
| GQ-DEVELOPMENT | GQ-SAFETY | Small CREATE / EVOLVE / RECOVER experiments; begin GQ-01, GQ-04, GQ-05; regression and scope checks, Q10 gameplay/GUI evidence and human acceptance; original or licensed assets | Approve each experiment, asset scope, budget and functional acceptance procedure |
| DOGFOOD-001 | GQ-DEVELOPMENT | Multiple unlike projects using the same core; per-project acceptance and regression evidence, interventions/time/usage recorded or UNKNOWN; findings become separately approved slices | Approve selected projects, access and runs; no blanket multi-repository authority |
| FOB-P0 | DOGFOOD-001 and owner-owned game safety/baseline decisions | Preserve existing work and saves; owner selects canonical baseline; disposable worktree; existing save-schema protections verified through approved isolated tests; reconcile rather than replace | Separate FOB authorization, baseline/worktree selection and save-protection decision |
| STUDIO-INTEGRATION | FOB-P0 | Map existing Studio workflow to BOV and verifier with evidence from one approved slice; preserve Studio work; reference existing runners | Separate Game Studio authorization and acceptance; no implicit game or Studio writes |

Codex is the **first targeted AI Coding Agent for qualification**, not yet qualified. Claude Code remains a long-term target under historical N07 and Part B; Copilot and Agy remain on the agent roadmap. CODEX-003 smoke alone establishes no deep qualification. GQ-RUNTIME requires evidence of every applicable Q3–Q9 gate before promotion; GQ-SAFETY expands that evidence rather than supplying missing prerequisites after promotion.

**Historical mappings:** N05 remains FOB runner integration, deferred until FOB-P0 and separate approval; it is not renamed to fixture qualification. GQ-SAFETY reuses N06 scenarios. N07 remains Claude Code qualification and is no longer the first agent target. STUDIO-INTEGRATION relates to historical N08, whose original dependencies still apply if N08 is executed. N09 remains the Claude/FOB end-to-end demonstration; GQ-DEVELOPMENT uses disposable games and does not close N09. DOGFOOD-001 advances portability before FOB; the historical A.7 website-pilot dependency on N09 remains attached to that specific pilot.

### Implementation and qualification vocabulary

| Label | Meaning | Current evidence boundary |
|---|---|---|
| Implemented | Files implementing behavior exist; says nothing about checks or acceptance | Historical pre-adapter snapshot: N03 committed; N04 present, uncommitted; Codex adapter not implemented. Superseded for this candidate: the Codex adapter is implemented; milestone definitions and priorities are unchanged. |
| Unit-tested | Deterministic tests exercised a named snapshot | Handoff reports 138 core/contract + 40 Godot configuration tests; not rerun here |
| Adapter-ready (`ADAPTER_READY`) | Declaration validation succeeds for the synthetic sample | Reported N04 configuration-level state only; not runtime evidence |
| Runtime-qualified (`RUNTIME_QUALIFIED`) | Real Godot import/tests and all applicable Q3–Q9 gates demonstrated | NOT QUALIFIED; runtime gates not demonstrated |
| Development-qualified (`DEVELOPMENT_QUALIFIED`) | Runtime/safety qualification plus CREATE/EVOLVE/RECOVER evidence, Q10 and human acceptance | NOT QUALIFIED |

Qualification of an agent is separate: the matrix requires verified deep evidence for the exact agent/platform/version. Codex remains historical PARTIAL smoke and deep NOT RUN. Neither implementation, unit tests, declarations nor this reconciliation promote Codex or Godot.

**Execution boundaries:** every future slice needs a bounded approved contract. Technical PASS is separate from human acceptance and never authorizes push, merge, deployment, dependencies or paid inference. A disposable worktree and private HOME/XDG profile alone do not establish OS filesystem isolation. Demonstrate denied real-profile access using synthetic canaries and an approved threat model without reading real saves. Historical references to save hashing grant no access in this sequence. Hash integrity does not prove authentic custody or independent execution; capture evidence outside the project with operator-controlled custody.

## Part A — Historical FOB-first MVP (milestones preserved)

**Historical goal (current priorities above take precedence):** a Claude Code (the owner's primary agent) can do one real, bounded Godot slice on FOB using BOV, with existing FOB tests and governance, with deterministic post-execution verification, with no loss of FOB work and no touch of a real save. FOB is the *validation case and first customer*; the core and verifier are unchanged by FOB.

### A.1 Principles
Skill-first. CLI-assisted (today `scripts/verify_scope.py`; the `ai-sdlc` entry point is Part B). Project-agnostic core. Small adapters. Evidence-driven. Minimal dependencies. No mandatory browser or orchestration platform. **No duplicated project workflows:** FOB's `AGENTS.md`, `.ai/WORKFLOW.md`, `tests/run_*.gd`, `tests/gui_*.gd`, `.ai/ci_headless.sh` and `.ai/qualify.py` stay the authority; the Lite layer only *references* them and records their exit codes and evidence. It must not add a second test runner.

### A.2 Layering (what may know about what)

| Layer | Owns | Must not contain |
|---|---|---|
| Core (this repo: Skill, contracts, `verify_scope.py`) | BOV, approval gates, result contract, verifier | Godot, FOB, any agent name |
| Godot adapter (this repo, new directory, e.g. `adapters/godot/`) | Generic Godot conventions: how to detect `project.godot`, headless invocation pattern, `user://` and `.godot/` handling, `.uid`/`.import` noise | FOB paths, FOB mission names |
| FOB project declaration (**D10, decided**: `examples/projects/fob/` in this repository; nothing is changed inside FOB) | FOB's declared commands (pointing at FOB's own scripts), protected paths (from `studio.json`: approved assets, `.claude/`, `.githooks/`, `tests/harness/`, `tools/run_godot.sh`, `save_schema.gd`, the real save path), recovery note | A copy of FOB's workflow |
| Agent adapter (Codex first under the current sequence; Claude Code retained) | Discovery, instruction-file and permission notes | Logic the core depends on |

### A.3 Alignment with the approved FOB roadmap (unchanged by this plan)

| FOB roadmap step (owner-owned) | AI-SDLC-Lite role | Boundary |
|---|---|---|
| 1. P0: save schema v2 protection; recover Evolved without losing Harness V1 | Read-only support only: baseline evidence and a protected-path declaration. **No agent writes to FOB before this step's save protection is verified by FOB's own tests.** | Lite does not decide recovery |
| 2. Product baseline consolidation | Records dirty state and SHAs per worktree (evidence only) | **Lite does not select or change the canonical baseline**; the owner does |
| 3. Engineering Expedition (10–15 min vertical slice) | First realistic slices for the demonstration (N09) | Slice choice is FOB's |
| 4. Family Demo | No Lite work required | none |
| 5. FOB Game Studio V1 | Workflow integration (N08); later a read-only "verify report" view | Studio's own code and `AGENTS.md` stay owner-controlled; its AI remains simulated until the owner says otherwise |

### A.4 Historical FOB-first slices (identifiers and original meaning preserved)

The rows and their original snapshot wording are retained verbatim. In particular, N03's former uncommitted status is historical: it is now committed at `historical-development-snapshot`. Use the current sequence for execution and current status, not these historical counts or priority notes.

"Maps to" shows the Part B slice it reuses or reclassifies. Every FOB-touching slice runs only in a **disposable worktree or copy** designated by the owner (D13), never a primary checkout, which may hold uncommitted work.

| ID | Slice | Depends on | Acceptance and evidence | Owner gate | Maps to |
|---|---|---|---|---|---|
| N01 | Review and commit HARDENING-003 and the planning documents on a branch | none | clean tree; all 93 tests OK with bytecode disabled | approve commit and PR | S01 |
| N02 | **Baseline consolidation support (read-only evidence).** One report of branches, worktrees, HEAD SHAs, dirty paths and `baseline` output per FOB worktree, written outside every FOB repository. States facts; recommends nothing | N01, D12 | report cites commands; FOB `git status`, refs and worktree list byte-identical before and after (hashes recorded); no baseline named | owner reviews; **owner alone selects the baseline** | new; uses existing `baseline` subcommand |
| N03 | **Core verifier hardening needed before any agent run** (*partly delivered, uncommitted*: symlink, submodule and mode-change detection, new-ignored-file detection, operator-supplied baseline record, hash-only evidence manifest with a four-property evidence contract, required-verification and execution-state checks, owner-controlled recovery contract, stable failure-code registry and golden-schema tests; *remaining*: submodule-aware Git review, other platforms); extend the Git execution-surface review (submodules, other platforms; the fsmonitor, hook, environment, filter and diff-driver vectors were mitigated and tested in N01B) | N01 | fixtures fail then pass; deterministic across three runs | approve contract changes | S03, S05 |
| N04 | **Godot adapter (generic)** *(delivered, uncommitted: `adapters/godot/`)*: declaration schema, read-only stdlib validator (no execution, no writes), disposable sample, safety model, qualification gates Q1-Q10, 40 configuration-level tests. Establishes **ADAPTER_READY tooling only**. *Still to do:* the FOB project declaration under `examples/projects/fob/` (separate, owner-approved) | N03, D10 | validator reports ADAPTER_READY for the sample and NOT_READY for each invalid fixture; adapter text has no FOB, studio or agent names; core unchanged (verified by test) | approve location (D10, decided) | S10 (reclassified), new |
| N05 | **Existing FOB test integration.** Map FOB's runners (`ci_headless.sh`, `run_*.gd`, `gui_*.gd`, `qualify.py`) into result-contract `verification` entries with exit codes and evidence references. **Run only in a disposable worktree with an isolated Godot user-data directory.** Isolation mechanism is **UNVERIFIED** (Godot's `app_userdata` location is believed to follow `XDG_DATA_HOME`; FOB's own isolation tests, e.g. E02C, must be read and confirmed first) | N02, N04, D13 | a recorded run of an existing suite; hashes of the real save path (never opened) unchanged before and after; no new test code | approve the isolation approach and the worktree | new |
| N06 | **Safety and recovery validation on fixtures** (before any live FOB agent run): adversarial fixtures for dirty tree, wrong baseline, protected path (asset and save-schema-like files), test edit, governance edit, `.gitignore` hiding, interrupted task with documented revert | N03 | scenario → report mapping test; fixture rollback leaves the tree identical | approve fixture scope | S04, S06, S07 |
| N07 | **Claude Code live qualification.** Step 1: Skill discovery and a smoke task in a throwaway fixture repo. Step 2: the same task in a disposable FOB worktree. Records versions, commands, exit codes, `verify` reports, token and time as measured or UNKNOWN. Deep scenarios only after smoke is recorded | N05, N06, D3 | QUALIFICATION_MATRIX rows; a planted violation is reported BLOCKED; recovery by discarding the worktree demonstrated | **authorize each run and budget; owner or a second person records the evidence** | S15, S16 (Claude only) |
| N08 | **Game Studio workflow integration.** Map Studio's slice templates to Lite's task and result contracts; the Studio workspace pins a Lite revision by reference. Optional later: a read-only "run verify, show report" action. No change to Studio's simulated AI | N07, D6; Studio roadmap items GS-006/007 | mapping document; one Studio slice recorded with the contract | approve any Studio or game-repo change (needs its own owner approval and PR, per Studio roadmap GS-006) | new |
| N09 | **End-to-end demonstration.** One real small FOB slice: Bound, plan approval, Claude Code implements in the disposable worktree, FOB tests run, `verify`, human acceptance, recovery shown | N07, N08, and FOB roadmap step 3 supplying the slice | full record: contract JSON, test output, report, diff, acceptance; FOB canonical baseline unmodified | owner accepts; any merge into FOB is a separate owner decision | new |

Notes: the order differs from the brief's list in one place: **safety and recovery validation on fixtures (N06) precedes the live Claude run (N07)** because an agent should not touch FOB before the controls are proven on a fixture; FOB-specific safety checks are repeated inside N07 and N09. Several steps can start only after the FOB-owned P0 and baseline decisions are made; Lite documents and fixtures (N03, N04, N06) do not touch FOB and can proceed first.

### A.4a Godot qualification states and gates (N04 onward)

Three states, never merged: **ADAPTER_READY** (the declaration validates; established by N04 at configuration level for the disposable sample only), **RUNTIME_QUALIFIED** (import and tests ran in a disposable, isolated workspace with recorded evidence; GQ-RUNTIME in the current sequence) and **DEVELOPMENT_QUALIFIED** (a real bounded task was completed under the framework with human acceptance; GQ-DEVELOPMENT in the current sequence, with N09 retained as the historical FOB demonstration). Gates Q1 to Q10 are defined in [adapters/godot/README.md](adapters/godot/README.md): detection (Q1), configuration validation (Q2), approved-runner compatibility (Q3), safe import (Q4), headless tests (Q5), scope enforcement (Q6), save and profile isolation (Q7), failure and interrupted-run reporting (Q8), evidence integrity (Q9), gameplay and GUI acceptance (Q10). Today: Q1 and Q2 PASS at configuration level for the sample; Q3, Q6, Q7 and Q9 are DECLARED only; Q4, Q5, Q8 and Q10 are NOT_RUN. Nothing is RUNTIME_QUALIFIED.

### A.5 Acceptance gates for the FOB-first MVP
Done only when every gate is evidenced:

| Gate | Requirement | Status |
|---|---|---|
| M1 | **FOB preservation:** before and after each FOB-touching run, branch refs, worktree list and primary-checkout status are identical, except in the disposable worktree | NOT MET |
| M2 | **No real save access:** real save path never opened or modified; only hash comparison, if authorized | NOT MET |
| M3 | **No baseline selection by Lite:** no document or tool names a canonical baseline | NOT MET (no baseline named so far) |
| M4 | **No duplicate infrastructure:** all test execution is by FOB's existing runners; Lite adds no runner | NOT MET |
| M5 | **Core unchanged by Godot/FOB:** diff of core files for N04 to N09 is only for generic hardening, reviewed | PARTIAL (N04 changed no core file; N05 to N09 pending) |
| M6 | **Claude Code smoke and one FOB slice recorded** with `verify` reports and honest UNKNOWNs | NOT MET |
| M7 | **Recovery shown:** a failed or abandoned run is reverted by discarding the disposable worktree, with identical hashes afterward | NOT MET |
| M8 | **Statement of limits:** documentation says detection, not prevention; the agent's native sandbox governs execution | PARTIAL (`SECURITY.md` committed at the current baseline; runtime enforcement remains unqualified) |

### A.6 Deferred under the current sequence
`ai-sdlc` CLI entry point, `init`/`doctor` and the three profiles (Part B P2); Copilot and Agy qualification (P3); Claude Code qualification remains historical N07 / Part B (Codex qualification is now CODEX-002–004); macOS and Windows (P4); other use cases (P5); multi-repository support; Game Studio chat or runtime AI execution; asset explorer or visual preview features; any FOB gameplay, art or save-schema change; a general public release; PyPI packaging; a CI matrix beyond Linux; verifier execution of project commands (D5); any container, browser, database or orchestrator.

### A.7 After the MVP: website pilot, then independent-evaluator, then Universal V1.0

**Website pilot (portability proof).** Pick one real website project (**D11:** candidate `website-pilot-candidate`, which appears from its directory listing to be a Vite/npm project; **selection pending inspection**, not yet evaluated). Objective: reuse the **same core contracts and verifier with only a project adapter** (build, test, lint, protected content and deployment paths). Acceptance: zero changes to core files (`git diff` of the core is empty); verification strategy recorded; build and dependency changes handled by the existing sensitive-path rules; no browser required (a browser check, if wanted, is optional and separately approved). Any core change required is recorded as a finding, not silently made. Depends on N09 and the generic adapter schema (N04).

**independent-evaluator read-only evaluation.** Identity and scope **UNKNOWN**: no local project or document defining independent-evaluator was found (D14). Future phase, not executed or granted here: a read-only assessment of a tagged snapshot of this repository plus its evidence records, covering architecture, security boundaries, agent portability, token and time efficiency, verification quality, developer experience, and simplification opportunities. Constraints: read-only access, no execution, no write grants, no secrets, an owner-approved evidence package. Output: findings with evidence; each becomes a slice only with owner approval. It can count as independent evidence (gate G3) only if the evaluator is independent of the implementing agent.

**Universal V1.0.** Resumes at Part B once the above is evidenced: the CLI, profiles, other agents, other platforms and the release gates G1-G10.

### A.8 Historical reclassification of the Part B backlog (S01-S22 preserved)

The table preserves the earlier mapping. Current exceptions: Codex adapter/smoke/deep work is CODEX-002–004 (advancing S14/S16); generic Godot qualification is GQ-RUNTIME/GQ-SAFETY/GQ-DEVELOPMENT before FOB integration; multi-project work is DOGFOOD-001. Earlier NEAR/LATER labels do not override the current sequence.

| Slice | Class | Where it lands |
|---|---|---|
| S01 commit HARDENING-003 | NEAR | N01 |
| S02 CI (Linux) | NEAR-optional | after N03 if D8 is decided; else deferred |
| S03 rename/symlink/mode detection | NEAR | N03 |
| S04 ignored-file listing | NEAR | N06 |
| S05 failure codes, schema golden test | NEAR | N03 |
| S06 adversarial fixtures | NEAR | N06 |
| S07 recovery tests | NEAR | N06 |
| S08 `ai-sdlc` entry point | LATER | Part B P2 (MVP calls `scripts/verify_scope.py` directly) |
| S09 `doctor` | LATER | P2 |
| S10 project-adapter schema | NEAR | N04 |
| S11 `init` preview/apply/uninstall | LATER | P2 |
| S12 profiles | LATER | P2 |
| S13 Agy identity record | LATER | P3 |
| S14 adapter pages: Copilot, Codex | LATER | P3 |
| S15 adapter pages: Claude Code, Agy | SPLIT | Claude Code page: NEAR (inside N07); Agy: LATER |
| S16 smoke: Copilot, Codex | SPLIT | Claude Code: N07; others LATER |
| S17 smoke: Claude Code, Agy | SPLIT | Claude Code: N07; Agy LATER |
| S18 macOS and Windows CI | LATER | P4 |
| S19 use-case smoke fixtures | SPLIT | website: pilot; Godot: N04-N05; the rest LATER (P5) |
| S20 deep qualification: brownfield, Godot/FOB | ABSORBED | N05-N09 (FOB as case study) |
| S21 security reporting route, second-reader docs validation | LATER | before any public release (G9, G10) |
| S22 release-candidate review | LATER | P6 |

### A.9 Owner decisions D10–D14 (recorded 2026-11-12; supersede the earlier "open" wording elsewhere in this file)

| ID | Decision | Status |
|---|---|---|
| D10 | **Generic Godot adapter under `adapters/godot/`; FOB project declaration under `examples/projects/fob/`.** No changes inside FOB yet. | DECIDED; generic Godot adapter directory exists uncommitted; FOB declaration remains pending |
| D11 | **Website pilot candidate: `website-pilot-candidate`.** Selection is pending inspection. | CANDIDATE; not yet inspected |
| D12 | **Evidence is stored outside FOB and Game Studio, in a dedicated local evidence directory** (path kept out of public documents). Nothing is created outside this repository until an evidence slice is approved. | DECIDED; directory not yet created |
| D13 | **A new disposable FOB worktree created from an owner-approved commit**, never a primary checkout. The commit is not yet named; **no worktree exists yet.** | DECIDED in principle; commit pending |
| D14 | **independent-evaluator is a future read-only evaluator of an approved snapshot, with no autonomous execution, no grants and no spending.** Its identity and access terms are defined before it is scheduled. | DECIDED in principle; nothing executed |

---

## Part B — Universal V1.0 roadmap (long term)

The phases below are the original plan, unchanged except for the cross-references in A.8. Their original ordering is retained for context; the current sequence advances Codex and Godot qualification plus multi-project work without requiring the planned single CLI entry point. Remaining Universal V1.0 work follows separately approved slices. "Owner decisions" D1-D9 at the end of this file still apply, alongside D10–D14 in A.9.

## Phases (Part B)

### P0 — Baseline and governance
- **Scope:** commit HARDENING-003 as reviewed work; make the repo's own governance coherent.
- **Deliverables:** reviewed commit(s) of the verifier, contract, `.gitignore`, SECURITY update, and these three planning docs; branch and PR convention; `CHANGELOG` entries; decision log for D1–D14 below.
- **Dependencies:** owner review of the uncommitted tree.
- **Acceptance:** `git status` clean on a named branch; baseline SHA recorded; all 93 tests pass with `PYTHONDONTWRITEBYTECODE=1`; no claims beyond evidence.
- **Test evidence:** unittest run output; `git diff --stat` mapped to approved scope.
- **Risks:** mixing hardening and docs in one commit; stale claims in README.
- **Owner gates:** approve roadmap; approve commit and PR (nothing is pushed or merged by an agent).
- **Out of scope:** new features, release, tags.

### P1 — Core hardening and deterministic verification
- **Scope:** make `verify` trustworthy and self-checking; add failure-injection tests; close verifier blind spots that can be closed.
- **Deliverables:** detection of renames, symlinks and mode changes; optional ignored-file listing mode; schema versioning plus a golden-file test; `verify` self-test for a corrupt Git state; failure classification codes (stable, documented); recovery tests (interrupted task leaves a recorded partial state and a documented revert); adversarial fixtures (injection string in a file, test edit, governance edit, `.gitignore` hiding).
- **Dependencies:** P0.
- **Acceptance:** every S01, S11–S14 and S17 scenario has a failing-then-passing fixture; verifier fails closed on each malformed-input case; no network calls (asserted by test).
- **Test evidence:** new tests listed by scenario; deterministic across three consecutive runs.
- **Risks:** false sense of security. Post-execution detection must never be described as prevention. Git edge cases (worktrees, submodules, sparse checkout).
- **Owner gates:** approve any change to exit codes or the schema; approve whether `verify` may ever re-run commands (D5).
- **Out of scope:** sandboxing, blocking agent actions, secret scanning, a network service.

### P2 — Developer experience and CLI
- **Scope:** the three commands and three profiles, with minimal files.
- **Deliverables:** `ai-sdlc` entry point (single stdlib module, runnable as `python -m` and installable without third-party packages); `doctor` (read-only checks of Python, Git, a clean baseline, agent CLIs on PATH, instruction files, sandbox settings reported UNKNOWN unless evidenced); `init` (preview by default, `--apply`, reusing installer logic, exact uninstall); `verify` wrapping `verify_scope.py`; profiles Quick, Standard, Strict; project-adapter schema and loader; `--json` output on all commands; documented exit codes.
- **Dependencies:** P1 (stable verify and schema), D1, D2.
- **Acceptance:** from a fresh clone, `init` plus one task reaches `verify` PASS in under 10 documented steps; Quick writes nothing; Standard writes at most the files listed in the profile table; existing installer tests still pass unchanged.
- **Test evidence:** CLI integration tests in temporary repos; a golden test of every generated file list; uninstall leaves the tree byte-identical.
- **Risks:** scope creep into a framework; duplicate source of truth between CLI text and the Skill.
- **Owner gates:** approve names, entry point and packaging (D1), profile defaults (D4).
- **Out of scope:** GUI, daemon, auto-update, telemetry, a plugin system.

### P3 — Multi-agent compatibility
- **Scope:** thin adapters and smoke qualification per agent.
- **Deliverables:** an adapter page per agent (Copilot, Codex, Claude Code, Agy), each with discovery, instruction-file, permission and recovery notes; drift test against the canonical Skill; **Agy identity record** (what it is, how it finds instructions) from approved read-only checks; a smoke run recorded for each agent that is available.
- **Dependencies:** P2 (CLI), D3 (budget for live runs), D6 (agent scope).
- **Acceptance:** each adapter states only what a VERIFIED smoke row supports; unsupported agents are listed "not verified"; no agent-specific logic enters the core.
- **Test evidence:** QUALIFICATION_MATRIX rows with versions, commands, exit codes and `verify` reports.
- **Risks:** agent products change quickly; permission models differ and cannot be unified; paid-inference cost; transcripts may hold sensitive data.
- **Owner gates:** authorize each live agent run and its budget; accept Agy's identity.
- **Out of scope:** deep qualification, agent-specific plugins, building a wrapper that drives agents.

### P4 — Multi-platform compatibility
- **Scope:** Linux, macOS, Windows (native).
- **Deliverables:** CI matrix (OS × minimum and latest Python); path, symlink, permission and newline handling fixes; documented install per OS; lowest supported Python version proven.
- **Dependencies:** P2; CI infrastructure (public repo target).
- **Acceptance:** the unit and CLI smoke suites pass on all three OSes in CI, or the unsupported OS is listed as not verified.
- **Test evidence:** CI logs linked from QUALIFICATION_MATRIX.
- **Risks:** Windows symlink and `0o600` behaviour; Git for Windows variance; CI cost.
- **Owner gates:** approve the CI provider and the supported-OS statement.
- **Out of scope:** other Unix variants, containers, WSL as a Windows substitute.

### P5 — Multi-use-case qualification
- **Scope:** prove the core and adapters across unlike projects.
- **Deliverables:** one smoke fixture per use case; deep runs for at least Python automation, one compiled-language CLI, one web project and one brownfield repo; FOB or Godot as a case study in an isolated worktree, run only with owner authorization; project-adapter examples for each.
- **Dependencies:** P2, P3; D7 (multi-repo model).
- **Acceptance:** zero core changes required for a new language (adapters only); each use case has a recorded verification strategy and protected-path list; failures feed back as new slices, not silent fixes.
- **Test evidence:** matrix rows with `verify` reports; adversarial scenarios per [QUALIFICATION_MATRIX.md](QUALIFICATION_MATRIX.md).
- **Risks:** adapter sprawl; per-language logic leaking into the core; real-project data safety (S09).
- **Owner gates:** authorize each project and data scope; FOB access is a separate explicit gate and no real saves are touched.
- **Out of scope:** FOB Game Studio features, unsupported languages, performance tuning.

### P6 — Release candidate and open-source distribution
- **Scope:** RC, then V1.0 only if every gate below is met.
- **Deliverables:** RC tag proposal; verified security reporting route; installation and documentation validation by someone other than the author; release notes with explicit "not verified" lists; versioning and support policy.
- **Dependencies:** P0–P5 evidence; owner decisions.
- **Acceptance:** every release gate (next section) is met, or the release is labelled a preview with a limitations statement.
- **Test evidence:** a gate checklist with a linked evidence record per gate; clean-room install transcript.
- **Risks:** over-claiming ("secure", "universal"); abandoned CI; unverified private reporting.
- **Owner gates:** approve the RC; approve every push, tag, publish or announcement (none is ever implied).
- **Out of scope:** package-registry publishing, marketing, commercial support.

## Release gates for V1.0

V1.0 must **not** be described as generally secure or universally compatible without all of these. Status today: **none met**.

| Gate | Requirement | Status |
|---|---|---|
| G1 Deterministic verification | `verify` is stable, versioned, fail-closed, and tested with fixtures | PARTIAL (verifier committed at `historical-development-snapshot`; blind spots documented) |
| G2 Honest security boundaries | Four-class statement in SECURITY.md; no enforcement claim without independent evidence | PARTIAL (security statement committed; independent runtime evidence still required) |
| G3 Independent evidence | Qualification run and recorded by someone other than the implementing agent | NOT MET |
| G4 Recovery tests | Interrupted-task and rollback fixtures for the CLI, not only the installer | NOT MET |
| G5 Agent qualification | Each agent named as supported has a VERIFIED smoke row; unlisted ones say "not verified" | NOT MET |
| G6 Platform qualification | Linux, macOS and Windows each VERIFIED or explicitly excluded | NOT MET (Linux unit suite only) |
| G7 Multi-project validation | At least four unlike use cases, one brownfield | NOT MET |
| G8 CI | Automated matrix on the public repository | NOT MET |
| G9 Security reporting route | Verified working private route (`SECURITY.md`) | NOT MET |
| G10 Docs and install validation | Clean-room install and first task by a new reader | NOT MET |

## Ordered implementation backlog (Part B; see A.8 for reclassification)

Each slice is independently testable and approved separately. "Test" is the evidence that closes it.

| # | Slice | Depends on | Test |
|---|---|---|---|
| S01 | Review and commit HARDENING-003 and these docs on a branch | none | clean tree; 93 tests OK |
| S02 | CI workflow: tests on Linux, bytecode off | S01, public repo | green run linked |
| S03 | Verify: rename, symlink and mode-change detection | S01 | new fixtures fail then pass |
| S04 | Verify: optional ignored-file listing (`--include-ignored`) | S03 | `.gitignore`-hiding fixture detected |
| S05 | Verify: stable failure codes and schema golden test | S03 | golden JSON test |
| S06 | Adversarial fixtures: injection string, test edit, governance edit, partial work | S05 | scenario → report mapping test |
| S07 | Recovery: interrupted-task record plus documented revert, tested | S05 | kill-mid-run fixture |
| S08 | `ai-sdlc` entry point wrapping `verify` | S05, D1 | CLI test; exit codes |
| S09 | `ai-sdlc doctor` (read-only) | S08 | fixture matrix, no writes asserted |
| S10 | Project-adapter schema, loader, Python example | S08, D2 | schema tests |
| S11 | `ai-sdlc init` preview/apply/uninstall reusing installer logic | S08, S10 | byte-identical uninstall; installer suite unchanged |
| S12 | Profiles Quick, Standard, Strict | S11, D4 | generated-file golden lists |
| S13 | Agy identity record (read-only) | D3 | recorded facts |
| S14 | Adapter pages and drift test: Copilot, Codex | S11 | drift test |
| S15 | Adapter pages: Claude Code, Agy | S13, S14 | drift test |
| S16 | Smoke qualification: Copilot and Codex | S14, budget approval | matrix rows |
| S17 | Smoke qualification: Claude Code, Agy | S15, budget approval | matrix rows |
| S18 | CI matrix: macOS and Windows, minimum Python | S02, S08 | green runs or documented exclusions |
| S19 | Use-case smoke fixtures: Python, Rust or C++, web, API, data | S12 | matrix rows |
| S20 | Deep qualification: brownfield and Godot/FOB case study | S19, project authorization | matrix rows; no save mutation |
| S21 | Verified security reporting route; docs install validation by a second reader | S01 | recorded observation |
| S22 | Release-candidate review against G1–G10 | all | gate checklist |

## Owner decisions required

| ID | Decision | Recommendation |
|---|---|---|
| D1 | CLI packaging: single stdlib file/zipapp and `python -m ai_sdlc` versus a PyPI package | single stdlib module first; decide on PyPI after P4 |
| D2 | Project-adapter location and format (`.ai-sdlc/project.json` versus root file) | one JSON file, one directory, nothing else generated |
| D3 | Authorization and budget for live agent runs; permission for read-only Agy identity checks | smoke only, small fixed budget per agent |
| D4 | Default profile and Strict behaviour (clean baseline required? CI snippet?) | Standard default |
| D5 | May `verify` ever execute declared commands (S18 risk)? | no in Quick and Standard; Strict only from an owner-approved allowlist |
| D6 | Which agents are in V1.0 scope; policy for unqualified ones | Copilot and Codex first; others "not verified" until evidenced |
| D7 | Multi-repository model (one contract per repository, or a manifest) | one contract per repo; revisit after P5 |
| D8 | Target public repository, branch policy, licence confirmation | decide before CI work (S02) |
| D9 | Who performs independent evidence (G3, G10) | a person other than the implementing agent |

## Out of scope for V1.0 (global)

Agent orchestration, swarms or schedulers; any hosted service, database or telemetry; mandatory browser, container or Playwright; sandboxing or preventing agent actions; secret scanning; language- or project-specific logic in the core; FOB Game Studio features.

## Additive developer experience track — DX-001 (2026-11-13)

Authority: mission AI-SDLC-LITE-DX-001 authorizes research and documentation only. [DX_ARCHITECTURE.md](DX_ARCHITECTURE.md) defines the proposal, friction inventory, permission profiles, lifecycle, metrics and implementation acceptance criteria. Historical N01–N09, S01–S22, P0–P6, D1–D14 and CODEX/GQ prerequisites above retain their definitions and evidence. This track does not mark them complete or grant execution authority.

| Slice | Additive scope | Gate |
| --- | --- | --- |
| DX-001 | Architecture and friction audit | Documentation checked; owner design acceptance pending |
| DX-002-LOCAL-CLI | Minimal stdlib entry point, offline doctor, verifier passthrough, read-only status; maps to S08/S09 | Owner approves files/interface; deterministic fixtures; existing verifier contract unchanged |
| DX-003-INSTALL | Existing installer integration and distinct Codex discovery evidence; maps to S11/S14 | Preserve target/history; CODEX-003 live qualification requires separate version/fixture/budget approval |
| DX-004-MISSION | Mission preparation, compact receipts, Skill integration and safe resume | One unchanged-scope BOV approval; native boundaries preserved; interruption/concurrency evidence |
| DX-005-DELIVERY | Agent-native Git delivery with separate local/remote receipts | Explicit destination/action approval; no force/protected overwrite; exact SHA confirmation |
| DX-006-MEASURE | Matched pilot, intervention/time/token attribution, separate CI follow-up | Complete windows/denominators or UNKNOWN; no unattended claim from design |

DX-002 is the proposed next deterministic development slice, subject to owner approval. Live execution still requires CODEX-003 and existing deeper qualification gates. Network delivery stays outside the offline CLI, through the agent's native tools. D5 remains unchanged: verification does not run declared commands. No new infrastructure, dependency, global configuration or automatic permission change is proposed.

NEXT=DX-002-LOCAL-CLI. OWNER_APPROVAL_REQUIRED=YES.

## Canonical import context

This uncommitted candidate preserves the public history. Historical development snapshot aliases are not resolvable public revisions or execution evidence. Private reports and ancestry are excluded. See [technical interfaces](docs/qualification/CODEX-002-summary.md); qualification remains subject to its explicit gates.
