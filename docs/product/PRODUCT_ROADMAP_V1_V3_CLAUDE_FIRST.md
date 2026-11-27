> **Product-planning artifact (PB-003), stored 2026-11-18.** Owner-approved inputs are limited to: Claude Code as the only targeted provider for V1–V3 (amends D6); preserve existing adapters; project configuration under `.ai-sdlc-lite/`; the Product Baseline track is additive and supersedes no historical decision; G1–G10 and D1–D14 intact; Godot/private-project off the V1 critical path; Linux first; planning artifacts under `docs/product/`. **Everything else in this document is a proposal, not an approved decision**, and nothing here is a capability unless stated as existing. Content below is the original text, with one local-environment reference generalized; see [README](README.md).

# PRODUCT_ROADMAP_V1_V3_CLAUDE_FIRST (PROPOSAL; replaces PB-002 R0–R9; nothing started)

Rules: additive PB track (does not renumber or complete ROADMAP N/GQ/S/DX items; owner decides its priority); one pillar per increment; one PR each; independently testable/revertible; stdlib; no network, command execution or model calls in new commands; human review before every merge; compatibility checklist is a PR gate; CI on Python 3.9 + 3.14. Effort = engineer-hours incl. tests/review; **judgment, low confidence**, re-base after C3.

## 1. Reduction versus PB-002
| Removed or reduced | Effect |
|---|---|
| Codex qualification, Codex discovery inspection (half of R1, half of R2) | gone from commitments |
| Copilot/Antigravity anything | not committed (existing adapters preserved) |
| Findings schema (merged into profile), task-contract JSON schema, recommendations/feature/run-receipt schemas | new schema ids in V1: **4 → 2** |
| Increments touching a live external agent: **2 → 1** (Claude Code smoke only) | less spend/risk |
| `status` Git inspection, installer bundle trimming | deferred (unchanged from PB-002) |
| Independent re-run (I8) | not in V1–V3 commitments (D5) |
| Added: Claude Code discovery inspection (C1) and conditional init target (C2) | the Claude-specific work that the strategy needs |
Hours: **not materially lower** (≈76–151 vs 79–143): scope and surface shrink, but Claude-specific increments and the Markdown task lint are added and the profile work is estimated more conservatively. Do not read this as a cost saving.

## 2. V1 (Preview → Stable)
| Inc | Title | OD-02 priority | Maps to (existing) | Depends | Deliverable and acceptance | Tests | Risk | Effort |
|---|---|---|---|---|---|---|---|---|
| **C0 (=R0)** | Truth reset and decision record | 7 | P0/P6 prep, A.8 drift, D6 | owner approval of R0 | see R0_IMPLEMENTATION_BRIEF.md | full suite; doc link/consistency tests | low | 5–9 h |
| **C1** | Claude Code discovery inspection (read-only, free) | 5 | N07 step 1 prep, S15 | C0 | for the owner's installed Claude Code (observed 2.1.327): where Skills, project instructions, commands, settings are discovered, from the installed version's own help/docs (no inference run, no paid usage); record facts with evidence in `adapters/agents/claude-code/` (UNKNOWN stays UNKNOWN); decide whether `.agents/skills` is discovered | adapter-contract validation | low | 3–6 h |
| **C2** | `init` target for Claude Code (**conditional on C1**) | 5 | S11/S14 | C1 | a single data-driven target entry; preview default; `--check`; install before baseline; no behaviour change for existing installs (manifest compatibility) | init/installer tests, old-manifest refusal/compat tests | medium (installer is security-sensitive) | 6–12 h (only if needed) |
| **C3** | Hardened Git reader + `discover` (profile, pinned ref) | 1 | S10 prep; new | C0 | reader reuses verifier hardening without changing it; `ai-sdlc-profile/1` facts at `--ref`; `unknowns` not guesses; caps; no symlinks; no content; `--out` only; schema doc + validator + ≥4 goldens | determinism ×3, adversarial (symlink loop, huge/binary file, hostile manifest, escape sequences, executable Git config refused), no-subprocess-except-git | medium | 20–34 h |
| **C4** | Audit findings (inside the profile) | 2 | new | C3 | 6–8 objective rules, stable ids, blob-oid evidence, no secret scanning; stable rerun diff | per-rule positive/negative, goldens | low-med | 8–14 h |
| **C5** | Governance declarations | 3 | S10, D2 | C0 (independent of C3/C4) | `.ai-sdlc-lite/project.json` + `govern check`; `result-template` pre-fills protected/ignorable/required checks; absent → byte-identical behaviour; agent copies never override | absent/malformed/hostile tests; goldens unchanged | medium (must not weaken verifier) | 8–16 h |
| **C6** | Requirements → task contract (Markdown + lint) | 4 | DX-004 part, TASK.md | C5 | documented structure; `task check` (structure, criterion ids each mapped to a required command or `human`, approval-digest freshness); `result-template --task`; no new JSON schema | lint, digest, derivation, invalidation tests | low-med | 8–14 h |
| **C7** | CLI recovery tests (G4) | 6 | S07, G4 | C0 | interrupted/rollback fixtures for CLI write paths; no partial/overwritten files | kill-mid-run fixtures | low | 6–10 h |
| **C8** | Claude Code smoke qualification | 5/7 | N07 step 1, G5, D3 | C1, (C2), C6, **owner authorization/budget** | disposable fixture; discovery; plan gate; PASS on correct change; planted violation BLOCKED; version/commands/exit codes/verify report; dated matrix row recorded by a human; deep NOT RUN | evidence record | medium (usage, permissions, variance) | 6–12 h + usage |
| **C9** | Dogfood + Preview release prep | 7 | S21, S22, G3, G9, G10 | C1–C8, release decisions | dogfood runs; independent clean-room run by a person; security route verified; gate checklist; Preview tag only if owner approves mechanics | evidence pack | medium | 12–24 h + human time |
Total ≈ **76–151 h** (C2 conditional ≈ 6–12 of it) plus agent usage and reviewer time.

**Stable** = Preview + remaining gates (G6 decisions, G7 four unlike use cases, G5 deep if "qualified" claimed) + V1 fixes from dogfood findings.

## 3. V2 — engineering workflows and traceability (directional; no estimates, no commitments)
Entry: Preview shipped and dogfood findings triaged. Candidates in OD-02 order: richer audit rules and recommendations contract + validator (evidence-backed, agent-written, schema-checked); feature decomposition contract and standalone Requirement artifact; **traceability** (requirement → task → check → evidence mapping, machine-checked) — this is where a task-contract JSON schema is re-evaluated against a concrete use case; run receipts (DX-004) for resumable sessions; deeper Claude Code integration (commands/hooks that call the CLI) **only** where C1 evidence and dogfood friction justify it; delivery executor in real use (DX-005); optional Strict-mode allowlisted re-run (D5, owner decision); `status` inspection and bundle trimming.

## 4. V3 — scale and release quality (directional)
Entry: V2 stable. Candidates: multi-repository model (D7); E2E qualification levels (task → feature → E2E); metrics and matched pilots (DX-006); CI snippet / team workflow (Strict mode); platform expansion (G6) if the owner approves; Stable hardening and maintenance policy (support window for Claude Code versions). Provider expansion is **not** a V3 item unless the owner reopens OD-01.

## 5. Dependency graph (simplified)
```
R0/C0 ─┬─ C1 ── (C2 if needed) ──────────────┐
       ├─ C3 ── C4                            ├─ C8 ─┐
       ├─ C5 ── C6 ───────────────────────────┘      ├─ C9
       └─ C7 ─────────────────────────────────────────┘
```
Lanes: {C1→C2}, {C3→C4}, {C5→C6}, {C7}. Recommended order for one developer: **C0 → C1 → C5 → C3 → C6 → C4 → C7 → (C2) → C8 → C9**. C1 is early because Connect and C8 depend on its facts; C8 runs last among live work so it exercises the final Skill/contracts.

## 6. Stop conditions
An increment that needs command execution, network, a database, a daemon, model calls, TOML/YAML dependencies, provider abstraction, or a change to verifier behaviour beyond additive options stops for a revised plan. Any need to touch GQ/private-project sequencing stops for the owner (P-1).

## 7. Owner decisions that gate work
D-gates: **C0** needs approval of R0 (Gate 1). **C1** none beyond C0 (read-only). **C3/C5** need the P-8 naming and D2 directory confirmation. **C8** needs D3 authorization/budget and the support-window policy (P-3). **C9** needs release mechanics (D1/D8/tag/publication/platforms) and the independent person. P-1 (GQ/private-project) blocks nothing in V1 but must be decided before anyone touches that track.
