# Architecture (V1.0 target)

**Status: PLAN.** Nothing here is released. Sections marked *exists* describe code in this checkout; everything else is a target. Roadmap: [ROADMAP.md](ROADMAP.md). Test matrix: [QUALIFICATION_MATRIX.md](QUALIFICATION_MATRIX.md).

**Product:** a Universal Coding Agent Skill plus a lightweight verification CLI. Stdlib Python 3 and Git only. No browser, container, database, server or orchestrator is required or planned.

## One canonical source

The canonical definition is the Markdown contract set (`AGENTS.md`, `WORKFLOW.md`, `TASK.md`, `CHECKLIST.md`, `RESULT.md`, `RESULT_CONTRACT.md`) plus the single-file Skill `.agents/skills/ai-sdlc-lite/SKILL.md`. Agent adapters and project adapters are **derived or referenced, never separately maintained**. A drift test (the existing `test_skill_source_bundle_consistency` is the model) must fail if an adapter diverges from the canonical text.

## Components

| # | Component | Role | State in this checkout |
|---|---|---|---|
| 1 | **Universal Skill** | Bound → Observe → Verify, two human gates, controlled autonomy, honest PASS/PARTIAL/BLOCKED/UNKNOWN | *Exists* (documents plus `SKILL.md`). Instruction-only. |
| 2 | **CLI** `ai-sdlc` | `init`, `doctor`, `verify` | `verify` ≈ `scripts/verify_scope.py` (*exists*, committed at `historical-development-snapshot`). `init` ≈ `scripts/install_skill.py` (*exists*, Copilot-oriented). `doctor`: **missing** (`install_skill.py` has a partial `preflight`/`readiness`). No single `ai-sdlc` entry point yet. |
| 3 | **Agent adapters** (Claude Code, Codex, Copilot, Agy) | A few lines each: where the Skill is found, which instruction file the agent reads, which native permission or sandbox features apply | Copilot: install path *exists* and was observed live. Codex: dedicated adapter **implemented** at `adapters/agents/codex/`; first targeted qualification agent under CODEX-002–004. **ADAPTER_READY** (`CODEX_ADAPTER_READY`) means declaration validation, **not RUNTIME_QUALIFIED**; smoke/deep qualification remains NOT_RUN. Historical explicit invocation is not runtime qualification. Claude Code: **none** (it has acted as an executor, not a qualified target). Agy: **identity unverified**, see below. |
| 4 | **Project adapters** | Declarative description of one project: build, test and lint commands, data and network rules, protected paths, recovery command | Generic Godot adapter implemented and uncommitted under `adapters/godot/` (reported configuration-level ADAPTER_READY only). General project-schema loading and FOB declaration remain planned; core path fields already exist. |

### Agy identity (local evidence only)

Facts: an Antigravity package and a separate `agy` executable were observed on the author's machine (local package query and file listing, not published). Not established: whether `agy` is the Antigravity CLI, its instruction-file convention, Skill discovery, permission model or sandbox. Neither executable was run. **Treat Agy as UNKNOWN until the owner approves a read-only `--help` / documentation check and the result is recorded.** Do not write Agy-specific logic before that.

## Layering rule (FOB-first MVP)

Project-specific behaviour lives only in adapters. Dependency direction: agent adapter and project adapter → core, never the reverse. A **Godot adapter** (generic conventions for `project.godot`, headless runs, `user://` and `.godot/`) sits beside the core and contains no FOB names. **FOB** is a project instance (declared commands that point at FOB's own existing runners, protected paths, recovery note); its declaration is planned under `examples/projects/fob/` in this repository (D10 in [ROADMAP.md](ROADMAP.md)), the generic adapter in `adapters/godot/`, and nothing is changed inside FOB. The core verifier must not change for Godot or FOB except for generic hardening reviewed on its own. No second test runner and no copy of FOB's workflow are created: FOB's `AGENTS.md`, `.ai/` and `tests/` remain the authority and are referenced, not duplicated.

**N04 status:** the generic Godot adapter now exists in `adapters/godot/` (declaration schema, read-only stdlib validator, disposable sample, safety model, qualification gates). Its rules: command and runner declarations are data, not authorization; nothing is executed, written or imported during validation; only project-owned runner wrappers are accepted, never a global Godot; path and isolation declarations are not proof of isolation; only ADAPTER_READY can be reported, never RUNTIME_QUALIFIED or DEVELOPMENT_QUALIFIED. It emits `protected_paths`, `allowed_paths`, `allowed_sensitive_paths` and `ignorable_paths` for a result contract without importing or changing the core, and has no project, studio or agent names (tests enforce both).

## Current qualification and execution status

The [current roadmap sequence](ROADMAP.md#current-execution-sequence--owner-approved-priorities) governs: N04C → CODEX-002 → CODEX-003 → CODEX-004 → GQ-RUNTIME → GQ-SAFETY → GQ-DEVELOPMENT → DOGFOOD-001 → FOB-P0 → STUDIO-INTEGRATION. Historical N01–N09 retain their meanings. Claude Code remains a long-term target; Codex is first targeted, not qualified.

Implemented means files exist; unit-tested means checks exercised a named snapshot; adapter-ready means only configuration validation. N03 is committed. N04 is implemented, with 40 reported configuration tests (178 total including prior tests), not rerun by this documentation mission. Godot is not runtime-qualified or development-qualified. Runtime qualification requires Q3–Q9 evidence; development qualification additionally requires CREATE/EVOLVE/RECOVER experiments, Q10 and human acceptance. Agent qualification requires a verified deep matrix row for the exact version/platform.

Codex and Godot adapters independently reference the same BOV contracts and verifier. Neither grants execution authority or effective isolation. Native CLI approvals, human BOV decisions, and OS confinement remain separate. No second execution engine or verifier changes are introduced. Private HOME/XDG and disposable workspaces need demonstrated filesystem confinement before real Godot runs; declarations and evidence hashes alone cannot prove it.

**CODEX-002:** `adapters/agents/codex/` supplies a declarative schema, read-only stdlib validator, synthetic declaration and qualification notes for CLI 0.167.2. CODEX_ADAPTER_READY is configuration evidence only; smoke and deep qualification remain NOT_RUN. DELIVERY-001 separates the reusable `templates/RESULT.md` from mutable root reports; the installer preserves its `framework/RESULT.md` interface and initializes results from the template. The verifier and Godot implementation are unchanged. The consolidated canonical [Skill](.agents/skills/ai-sdlc-lite/SKILL.md) now references the [reusable result template](templates/RESULT.md), while the installer keeps the compatible `framework/RESULT.md` namespace. Earlier root RESULT.md references describe historical source snapshots; mutable root execution reports remain preserved.

## Interfaces

**Result contract** (`ai-sdlc-lite-result/1`, *exists*, see [RESULT_CONTRACT.md](RESULT_CONTRACT.md)): task id, baseline SHA, allowed, sensitive and protected paths, declared changes, verification commands with exit codes and evidence, claimed status. Verification output is `ai-sdlc-lite-verification/1` with exit codes 0 PASS, 1 PARTIAL, 2 BLOCKED. Both schemas carry a version string; any breaking change needs a new version and a migration note.

**Project adapter** (target): one optional JSON file, `.ai-sdlc/project.json` (path is a decision, see ROADMAP), consumed by `init`, `doctor` and `verify`:

```json
{ "schema": "ai-sdlc-project/1",
  "commands": {"build": [], "test": [], "lint": []},
  "protected_paths": [], "data_paths": [], "network": "none|loopback|declared",
  "recovery": "git restore ... / project-specific note" }
```

Commands are *declared*, never run by `verify` in the Quick and Standard profiles. Running them (Strict) executes project code and is an owner decision (S18).

## Security boundary (honest)

| Class | Source of the control |
|---|---|
| Instruction-only | The Skill and contracts |
| Post-execution detection | `verify`: scope, protected, test and governance paths, symlink/submodule/mode changes, baseline ancestry, dirty baseline (optionally cross-checked against an operator-supplied baseline record), new ignored files, declared-vs-actual, evidence presence, hash pins and sealed-manifest matches, required checks and execution state. Hash integrity is checked; custody, independent execution and agent assertions are not (exit codes stay agent-reported). Failure codes are a stable registry pinned by golden reports |
| Technically enforced | Installer writes only (symlink, traversal and consent checks); the verifier's own Git invocation is hardened against the listed configuration vectors (tested with marker-file payloads); no agent-level enforcement |
| Native agent or OS sandbox | Anything that must be *prevented*: shell, network, secrets, Git pushes, spend, time |

Recovery is owner-controlled: no component ever resets, cleans, deletes, checks out or overwrites anything. Principles: fail closed on missing evidence; never raise a claimed status; no network in the CLI; the CLI never executes commands declared in a contract, but it does invoke Git, so Git's own execution surface is hardened (all `GIT_*` variables dropped, `core.fsmonitor` and hooks disabled, no index refresh, `--no-ext-diff --no-textconv`, repositories with local filter or diff-driver programs refused; see [SECURITY.md](SECURITY.md)) and not claimed to be complete; `init` previews unless told to apply, writes only files it owns, and refuses symlinks and protected targets (reuse the installer's logic, do not rewrite it); every generated file records a hash for exact uninstall.

## Profiles (behaviour, not separate products)

| Profile | Intent | Generated files | `verify` | Dirty baseline | Commands re-run |
|---|---|---|---|---|---|
| **Quick** | Try it in seconds | none beyond the Skill; no project adapter | optional, advisory exit codes | warn | no |
| **Standard** (default) | Normal project work | Skill plus optional `project.json`; per-task result JSON on request | expected before handoff; BLOCKED on missing evidence | PARTIAL | no |
| **Strict** | Shared or production-adjacent repos | Standard plus protected defaults, CI snippet | required; run in CI | BLOCKED | only an owner-approved allowlist (decision D5) |

## Non-goals

An orchestrator or scheduler, agent swarms, a database or service, mandatory CI vendor, mandatory browser or Playwright, secret scanning engines, a permission broker, anything that claims to sandbox an agent, language-specific logic in the core.

## Additive DX proposal — DX-001 (2026-11-13)

[DX_ARCHITECTURE.md](DX_ARCHITECTURE.md) proposes a minimal local CLI and one-request Skill workflow, with an audit, permission intent profiles, E2E states, metrics and acceptance gates. It is design only, requiring owner approval before implementation. The existing verifier stays offline and never executes recorded commands. Authorized GitHub delivery remains in the agent's native tool/approval boundary; the CLI does not broker permissions or perform network delivery. Historical architecture text above is preserved; no previous qualification is upgraded.

## Canonical import context

This uncommitted candidate preserves the public history. Historical development snapshot aliases are not resolvable public revisions or execution evidence. Private reports and ancestry are excluded. See [technical interfaces](docs/qualification/CODEX-002-summary.md); qualification remains subject to its explicit gates.
