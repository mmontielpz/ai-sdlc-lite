> **Product-planning artifact (PB-003), stored 2026-11-18.** Owner-approved inputs are limited to: Claude Code as the only targeted provider for V1–V3 (amends D6); preserve existing adapters; project configuration under `.ai-sdlc-lite/`; the Product Baseline track is additive and supersedes no historical decision; G1–G10 and D1–D14 intact; Godot/FOB/Studio off the V1 critical path; Linux first; planning artifacts under `docs/product/`. **Everything else in this document is a proposal, not an approved decision**, and nothing here is a capability unless stated as existing. Content below is the original text, with one local-environment reference generalized; see [README](README.md).

# OWNER_DECISION_AMENDMENTS (PB-003; develop @ 6430dca; read-only)

**Authority boundary.** The only decisions treated as *owner-approved* here are OD-01…OD-05 exactly as listed in the PB-003 mission brief. Everything else in this document is a **proposal** or a **consequence I derived and the owner must confirm**. Nothing is recorded in the repository by this document; recording it is part of R0 and needs the owner's Gate-1 approval of R0.

## 1. Approved decisions (as given)
| ID | Decision (owner wording, condensed) |
|---|---|
| OD-01 | Claude Code is the only targeted provider for V1–V3. No Codex/Copilot/Antigravity qualification commitments. Existing adapters preserved unless removal is separately approved. No universal SDKs or speculative provider abstractions. **Record an explicit amendment to D6.** |
| OD-02 | Priorities in order: (1) repository onboarding/understanding, (2) evidence-backed engineering audit, (3) governance and project configuration, (4) requirements and task contracts, (5) Claude Code development experience, (6) verification and traceability, (7) real-world dogfooding and release quality. |
| OD-03 | Preserve existing security requirements and release gates G1–G10; identify conflicts with the Claude-only strategy; do not silently weaken, replace or bypass. |
| OD-04 | CLI-first; offline deterministic repository inspection; no mandatory AI calls from the CLI; reuse existing `.ai-sdlc-lite/` conventions; preserve schemas and compatibility; no UI/daemon/database/custom agent runtime; no new schema unless justified by a concrete V1 use case. |
| OD-05 | Retain **Preview** and **Stable** as separate qualification targets. Branch, tagging, publication and platform-support decisions are **not** assumed approved; unresolved decisions are documented. |

## 2. Amendment to D6 (explicit, as OD-01 requires)
**Original (ROADMAP "Owner decisions required" D6):** "Which agents are in V1.0 scope; policy for unqualified ones. Recommendation: Copilot and Codex first; others 'not verified' until evidenced."
**Amended text (proposed wording for the repository record):**
> **D6 (amended 2026-11-18 by owner decision OD-01).** For V1–V3 the only targeted agent is **Claude Code**. Copilot, Codex and Antigravity carry **no qualification commitment**; existing adapters, declarations and historical evidence are preserved and are described as "not verified (not in committed scope)". An agent is named "supported" only with a dated VERIFIED smoke row for that exact agent, platform and version (QUALIFICATION_MATRIX rule 3, release gate G5). No universal provider SDK or abstraction is built. Removal of an existing adapter requires a separate owner decision.
The "not verified until evidenced" policy is **kept**; only the scope list changes.

## 3. Consequences of OD-01 for existing records (derived; owner to confirm)
| Existing item | Source | Effect of OD-01 | Class |
|---|---|---|---|
| CODEX-002 adapter (declaration, validator) | ROADMAP current sequence | exists; **preserved**, maintenance only (keep tests green) | preserved |
| CODEX-003 smoke, CODEX-004 deep | ROADMAP, QUALIFICATION_MATRIX | no longer committed; remain NOT RUN | parked |
| **GQ-RUNTIME "Depends on N04C and CODEX-004"** | ROADMAP | **dependency chain breaks**: the Godot/FOB/Studio track (GQ-*, FOB-P0, STUDIO-INTEGRATION) hangs on CODEX-004. OD-01 does not say what happens to it | **CONFLICT PENDING** (§5) |
| N07 Claude Code live qualification (Step 1 smoke; Step 2 FOB worktree) | ROADMAP Part A | **retained and promoted** to the primary qualification item; its Step 2 (FOB) stays tied to the FOB track | retained |
| S13 Agy identity, S14/S16 Copilot+Codex pages/smoke, S15/S17 Claude Code+Agy pages/smoke | ROADMAP S-slices | Copilot/Codex/Agy parts not committed; Claude Code parts retained | reduced |
| P3 "Multi-agent compatibility" | ROADMAP Part B | reduced to "Claude Code adapter + smoke"; drift test for non-Claude adapters not committed | reduced |
| README Copilot-centric install and one live Copilot run | README, QUALIFICATION | preserved as historical, labelled "not in committed scope"; stops being the primary onboarding | docs (R0) |
| Controlled-autonomy installer (Copilot sandbox configuration, 732-line `install_skill.py`) | code | **preserved**; maintenance only | preserved |
| `adapters/agents/{codex,copilot}`, Godot adapter | code | preserved (OD-01); Godot is a *project* adapter, not a provider | preserved |
| "Universal Coding Agent Skill" wording (ARCHITECTURE, ROADMAP, pyproject description) | docs/metadata | conflicts in tone with OD-01; claims policy already forbids "universal". Wording update proposed in R0 (docs) ; pyproject text is a metadata decision (§5 C-8) | docs |

## 4. Consequences of OD-04 (derived)
| Topic | Derived effect | Owner confirmation |
|---|---|---|
| Directory/path | `.ai-sdlc-lite/` is reused for project declarations (`.ai-sdlc-lite/project.json`); the code already uses `.ai-sdlc-lite/task-context.json`. This replaces PB-002's open path question (O-06) and the `.ai-sdlc/` wording in ARCHITECTURE/D2 | confirm that D2's directory is amended from `.ai-sdlc/` to `.ai-sdlc-lite/` (D2 text unchanged otherwise) |
| New schemas | PB-002 proposed four new ids (profile, findings, task, project) + deferred ones. Under "justified by a concrete V1 use case" the reconciled baseline keeps **two**: `ai-sdlc-profile/1` (profile **with an embedded findings section**: onboarding + audit) and `ai-sdlc-project/1` (already designed in ARCHITECTURE: governance). **No task-contract JSON schema in V1**: task contracts are a documented Markdown structure over existing TASK.md plus a deterministic lint, deriving the existing result contract. Recommendations, feature contract, run receipts: not in V1 | confirm |
| No AI calls from the CLI | unchanged from PB-03 | — |
| Preserve schemas/compatibility | PB-002 §8 compatibility checklist stands | — |

## 5. Conflicts
### 5.1 Resolved (by wording/design, no gate weakened)
| # | Conflict | Resolution |
|---|---|---|
| C-1 | D6 (Copilot+Codex first) vs OD-01 | amended text in §2 |
| C-2 | G5 "each agent named supported has a VERIFIED smoke row; unlisted say not verified" vs Claude-only | **no conflict**: G5 is satisfied by naming only Claude Code as supported and labelling the rest "not verified"; text unchanged (RELEASE_GATES_RECONCILED) |
| C-3 | Layering rule "core must not name any agent" (ARCHITECTURE) vs "excellent Claude Code experience" | Claude-specific material is confined to `adapters/agents/claude-code/` (declaration data) and one installer target mapping; verifier, contracts, schemas and profile/audit stay provider-neutral by construction (no provider field). This is a **thin adapter, not a provider abstraction**, so OD-01 is respected |
| C-4 | "Agent-agnostic" principle vs Claude-first | restated as "agent-neutral core, Claude Code first, no abstraction for other providers" |
| C-5 | Verifier treats `CLAUDE.md` and `.claude/` as governance paths | consistent and useful: integration files are governance-sensitive; install them **before** taking the baseline or declare them in `allowed_sensitive_paths` |
| C-6 | G3 independent evidence (person ≠ implementing agent) when Claude Code both implements and is the agent under test | gate unchanged; same-family risk recorded; requires a **person** (D9) |
| C-7 | PB-07 "NEEDS_HUMAN_DECISION" | superseded by OD-01 (decided) |
| C-8 (part) | O-06 path | OD-04 (`.ai-sdlc-lite/`) |

### 5.2 Pending (require explicit owner approval; nothing assumed)
| # | Conflict / open item | Why it matters | Recommendation |
|---|---|---|---|
| P-1 | **Fate of the GQ/FOB/Studio track** after CODEX-004 is no longer committed (GQ-RUNTIME depends on it) | owner-approved sequence now has a broken dependency | re-point GQ-RUNTIME's agent prerequisite to a Claude Code smoke (N07) or park the track; either is an owner decision |
| P-2 | **Platform support** (G6 needs Linux/macOS/Windows VERIFIED or explicitly excluded) | OD-05 says do not assume | Preview excludes macOS/Windows explicitly; Stable decision later |
| P-3 | **Support-window policy for Claude Code versions** (fast-moving, auto-updating; G5 wants exact version) | a smoke row is true only for the tested version | claim support only for the tested version string; record observed (`claude --version` = 2.1.327 on this host, observed read-only today) |
| P-4 | **Authorization and budget for live Claude Code runs** (D3 unchanged) | no paid smoke may run without it | authorize per run with stated limit |
| P-5 | **Release mechanics (D1 packaging, D8 branch policy, tag, publication)** | OD-05: not approved | see RELEASE_GATES_RECONCILED §5 |
| P-6 | **Where Claude-specific installation lives** (`init --agent claude-code` vs a separate script) and whether `ai_sdlc/` may hold a small Claude Code target table | OD-01 forbids speculative abstraction; a mapping table is the minimum | recommend a single data-driven target entry, no provider logic |
| P-7 | **Durable home for planning artifacts** (previous O-10) | artifacts live only on an external SSD | commit under `docs/` via PR, if approved |
| P-8 | **CLI command/term naming** ("profile" collides with verification modes and permission intents) | usability | owner picks at R0 review; default proposal: command `discover`, term "Project Profile" |
| P-9 | **pyproject `description`** ("Universal Coding Agent Skill…") | metadata change is outside docs-only R0 | change in a later increment if approved |
| P-10 | Fate of D10–D14 (Godot/FOB, website pilot candidate, evidence dir, evaluator) | not addressed by OD-01…05 | **preserved unchanged**; not part of V1–V3 commitments unless the owner says so |
| P-11 | OD-02 priority order vs dependency order | Claude Code discovery (#5) must be *inspected* early to define Connect | sequence by dependency (C1 read-only inspection early), invest by OD-02 priority |

## 6. Previous proposal dispositions after OD-01…05
| Item | New status |
|---|---|
| PB-01 additive track | still NEEDS_HUMAN_DECISION (not covered by OD-01…05); used here as the vehicle for R0, **pending approval of R0** |
| PB-04, PB-09 | modified by OD-04 (see §4) |
| PB-05 (D5) | unchanged; OD-04 "no mandatory AI calls" compatible; independent execution not in V1–V3 commitments |
| PB-07 | decided by OD-01 |
| PB-11 (D1 install) | pending (P-5) |
| PB-14 dogfood | modified: Claude Code is the agent for all dogfood; G3 person run retained |
| O-03, O-05 | pending |
| O-04 | narrowed to Claude Code (P-3, P-4) |
| O-07 | separate subcommands (accepted earlier), naming P-8 |
| O-08, O-09 | deferred |
| O-10 | P-7 |

## 7. What is *not* approved by this document
R0 itself, any command/path/term naming, release tier contents, tag/publication, platforms, budgets, version policy, removal of any adapter, any change to G1–G10, D1/D2/D3/D5/D7/D8 resolution, the GQ/FOB disposition.
