> **Product-planning artifact (PB-003), stored 2026-11-18.** Owner-approved inputs are limited to: Claude Code as the only targeted provider for V1–V3 (amends D6); preserve existing adapters; project configuration under `.ai-sdlc-lite/`; the Product Baseline track is additive and supersedes no historical decision; G1–G10 and D1–D14 intact; Godot/private-project off the V1 critical path; Linux first; planning artifacts under `docs/product/`. **Everything else in this document is a proposal, not an approved decision**, and nothing here is a capability unless stated as existing. Content below is the original text, with one local-environment reference generalized; see [README](README.md).

# PRODUCT_BASELINE_V1_CLAUDE_FIRST (PROPOSAL; supersedes PB-002's reconciled baseline as a proposal; nothing here is implemented unless labelled EXISTS)

Base: develop @ 6430dca. Owner decisions OD-01…05 (mission brief) are the only approved inputs; all else is proposed. Labels: **EXISTS** (observed earlier), **PROPOSED**, **DEFERRED**, **EXCLUDED**.

## 1. Strategy
**Claude Code first: one provider, excellent engineering experience.** V1–V3 invest in repository understanding, governance, requirements/task contracts, engineering workflow and verifiable outcomes for Claude Code users. No Codex/Copilot/Antigravity commitments (existing adapters preserved, maintenance only). No provider abstraction or SDK.

AI-SDLC Lite is a lightweight engineering layer above Claude Code: it understands a repository, governs work, structures requirements into task contracts, lets Claude Code execute, and verifies the outcome while keeping agent-reported evidence apart from what the tool itself observed. It is not a coding agent, an autonomous factory or an orchestration platform. CLI-first, offline and deterministic; the CLI never calls a model; stdlib Python + Git; no UI, daemon, database or custom agent runtime.

Pillars: UNDERSTAND → GOVERN → PLAN → EXECUTE → VERIFY. Investment order = OD-02: (1) onboarding/understanding, (2) evidence-backed audit, (3) governance/config, (4) requirements/task contracts, (5) Claude Code DX, (6) verification/traceability, (7) dogfooding/release quality. *Priority is not build order*: Claude Code discovery (#5) is inspected first because Connect depends on it (see roadmap).

## 2. Where Claude Code specifics live
| Layer | Provider-specific? | Rule |
|---|---|---|
| Verifier, result/baseline contracts, delivery, profile/audit, project declarations, task lint | **No** | no provider names or fields; behaviour identical for any agent |
| `adapters/agents/claude-code/` declaration | yes (data only) | records observed version, discovery paths, instruction-file behaviour with evidence; UNKNOWN until observed |
| Installer/init target mapping for Claude Code (where the Skill/instructions are placed) | yes (one mapping entry) | no provider logic; install before taking the baseline (verifier treats `CLAUDE.md`/`.claude/` as governance-sensitive paths) |
| Skill text instructing Claude Code how to use the CLI | yes (Markdown) | instruction-only; not enforcement |
Observed today: Claude Code **2.1.327** is installed on this host (read-only `claude --version`, no inference). Discovery locations and instruction behaviour are **UNVERIFIED in this repo** (the adapter declaration is all UNKNOWN); believed conventions (`CLAUDE.md`, `.claude/skills/`, `.claude/commands/`, `.claude/settings.json`) must be confirmed in increment C1 from the installed version/docs before any code depends on them.

## 3. Minimum complete Claude Code user journey
| # | Step | Mechanism | Deterministic? | Provider-specific? | Status |
|---|---|---|---|---|---|
| 0 | Install | tagged checkout/archive; `python3 -m ai_sdlc doctor` (D1: module first) | yes | no | PARTIAL (no tag) |
| 1 | Connect Repository | `ai-sdlc init --repo ABS` places the Skill/instructions where Claude Code finds them; `--check` | yes | **target path** | PARTIAL: `init` EXISTS for `.agents/skills`; Claude Code discovery UNKNOWN |
| 2 | Understand + Audit | `ai-sdlc discover --repo ABS --ref HEAD --out FILE` → `ai-sdlc-profile/1` (facts + findings) | yes | no | PROPOSED (name pending) |
| 3 | Govern | human edits `.ai-sdlc-lite/project.json` using the profile's suggestions; `ai-sdlc govern check` | yes | no | PROPOSED |
| 4 | Requirement → Task contract | in a Claude Code session the user states the requirement; Claude (guided by the Skill) drafts TASK.md in the **documented structure** (objective, acceptance criteria with ids, allowed/protected paths, required checks, risk); `ai-sdlc task check` lints it; human approves a named revision (Gate 1) | lint yes; drafting AI | Skill text only | PROPOSED |
| 5 | Agent Execution | Claude Code implements in a worktree, runs the required checks, fills result.json (`result-template --task` pre-fills) | AI | yes (the agent) | UNQUALIFIED |
| 6 | Verify | `ai-sdlc verify … --format summary` | yes | no | EXISTS |
| 7 | Review | human re-runs required checks, reads diff + summary, records Gate 2 | human | no | PARTIAL |
Only steps 1 and 5 touch the provider. Everything else works the same with any agent, which keeps the core clean without building an abstraction.

## 4. V1 scope
**In (PROPOSED):** everything EXISTS stays stable; Claude Code discovery inspection and adapter declaration with evidence; `init` target for Claude Code (only if C1 shows the current target is not discovered); hardened Git reader; `discover` (profile + findings, pinned ref, offline, no execution); governance declarations (`ai-sdlc-project/1`); task contract as Markdown structure + `task check` + `result-template --task`; CLI recovery tests (G4); docs truth reset (R0); Claude Code smoke qualification (needs authorization); dogfood and release preparation.
**New schema ids in V1: two** — `ai-sdlc-profile/1` (profile with embedded `findings[]`) and `ai-sdlc-project/1` (already designed in ARCHITECTURE). Justification (OD-04): profile/findings is the machine-readable output Claude Code and governance consume for priorities 1–2; project.json is the human-approved source for priority 3. A task-contract JSON schema is **not** justified in V1: Markdown structure + lint + the existing result contract meet priority 4; revisit in V2 if traceability needs machine-checked criteria→evidence links.
**DEFERRED (V2/V3):** recommendations contract, feature contract, standalone Requirement artifact, run receipts (DX-004), delivery in real use (DX-005), metrics (DX-006), status inspection, installer bundle trimming, Strict-mode check re-run (D5, owner decision), multi-repo (D7), E2E levels.
**EXCLUDED:** multi-provider integrations/abstractions, UI, daemon, database, custom runtime, orchestration/swarms, autonomous recovery, secret scanning, sandbox/permission-broker claims, push/merge/release automation, certification language, provider-specific logic in the core.

## 5. Trust model (unchanged from PB-002)
T0 agent-reported · T1 integrity-checked · T2 independently observed repository state · **T3 independently executed: not implemented, never implied** · H human approval. Rule: no document or output says "independently verified/executed" for T0–T2; Gate 2 includes a human-performed re-run of the required checks, recorded as such; with Claude Code as implementer and agent under test, G3 independence must come from a **person**.

## 6. Data contracts (PROPOSED; provisional)
Common rules: `schema` id `ai-sdlc-<kind>/1`; `tool`; `repo` {head_sha, ref, source: committed-tree|working-tree, dirty}; sorted keys; no timestamps in the digested body; paths repo-relative; blob oids not content; no content excerpts; unknown future fields ignored with a warning.
- **`ai-sdlc-profile/1`**: languages, manifests, ci, instruction_files (incl. `CLAUDE.md` presence), layout, `commands[]` (`declared` only from JSON manifests such as package.json; CI/Makefile line extraction `inferred`; never executed; Python 3.9 floor: no TOML/YAML), protected_path_candidates, unknowns, `findings[]` {id = rule+subject, rule, category, severity, title, evidence[{path, blob_oid, line?}], confidence}, digest. 6–8 objective rules; no secret scanning.
- **`ai-sdlc-project/1`** at `.ai-sdlc-lite/project.json`: commands, protected_paths, data_paths, network, recovery, optional default_risk; human-approved; never inferred automatically; agent copies never override it.
- **Task contract (Markdown)**: required headings/fields in TASK.md; approval line records the approved revision digest (computed over the file excluding the approval line); `task check` verifies structure, id-ed acceptance criteria each mapped to a required command or `human`, and digest freshness. Existing `.ai-sdlc-lite/task-context.json` (pointers: contract/checklist/result) is reused unchanged.

## 7. Compatibility (must hold for every increment)
Existing ids/schemas (`ai-sdlc-lite-result/1`, `-baseline/1`, `-verification/1`, `ai-sdlc-delivery/1`, `ai-sdlc-adapter/1`, installer manifest) unchanged; additive optional changes only; old records fail closed as before (PR #23 precedent); exit codes 0/1/2; statuses PASS/PARTIAL/BLOCKED/UNKNOWN; `Status:` first line; existing commands/flags; `python3 -B -m ai_sdlc` and `ai-sdlc`; goldens unchanged unless logged; stdlib; Python ≥3.9; no network; no command execution or model calls in new commands; `status` keeps not invoking Git; no writes in the target repo except human-approved `.ai-sdlc-lite/` and task files.

## 8. Security requirements for new commands
Refuse repos with executable Git config (as `verify`); hardened pinned-ref reads only; size/count/depth caps; no symlink following; secret-bearing names listed by path only, never read; no content excerpts; escaped output; outputs only to explicit `--out` outside the repo, exclusive create; three identical runs byte-identical.

## 9. Claims policy
Allowed (with its evidence): "scope verification and evidence-integrity checking; agent-reported checks are not re-run"; "smoke-tested with Claude Code <version> on <platform> on <date>"; "deterministic offline read-only discovery at a pinned ref". Forbidden: supported/compatible beyond tested Claude Code version and Linux; any other agent as supported; "independently executed"; certified/secure/universal/autonomous; productivity or cost claims (one N=1 pilot only).

## 10. Dogfooding
Claude Code is the agent for all runs. Order: self (worktrees) → another small real repository chosen by the owner → a software-only robotics repository if one is designated (preconditions in earlier planning notes) → plus the **independent clean-room run by a person** (G3/G10). Record time, interventions, tokens if reported (else UNKNOWN), BLOCKED/PARTIAL causes. Stable needs ≥4 unlike use cases incl. a brownfield (G7).
