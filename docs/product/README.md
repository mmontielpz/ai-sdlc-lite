# Product planning artifacts

Planning documents for the **Product Baseline (PB) track**: a Claude Code–first, offline, deterministic engineering layer. They are additive to, and do not supersede, [ROADMAP.md](../../ROADMAP.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), release gates G1–G10 or decisions D1–D14, except the D6 amendment recorded in the roadmap.

| Document | Purpose |
| --- | --- |
| [PRODUCT_BASELINE_V1_CLAUDE_FIRST.md](PRODUCT_BASELINE_V1_CLAUDE_FIRST.md) | Product definition, minimum Claude Code journey, scope, contracts (proposed) |
| [PRODUCT_ROADMAP_V1_V3_CLAUDE_FIRST.md](PRODUCT_ROADMAP_V1_V3_CLAUDE_FIRST.md) | Increments C0–C9 for V1; V2/V3 directional |
| [OWNER_DECISION_AMENDMENTS.md](OWNER_DECISION_AMENDMENTS.md) | Owner decisions OD-01…OD-05, the D6 amendment, conflicts resolved and pending |
| [RELEASE_GATES_RECONCILED.md](RELEASE_GATES_RECONCILED.md) | G1–G10 preserved; Claude Code application; Preview vs Stable |
| [R0_IMPLEMENTATION_BRIEF.md](R0_IMPLEMENTATION_BRIEF.md) | The documentation-only truth-reset brief that produced this change |

**Note.** The repository has Claude Code, Codex and Copilot adapter declarations; there is no Antigravity adapter (it appears only in notes and the qualification matrix). Where these documents say adapters are preserved, that means the existing ones.

**Status vocabulary.** *Implemented* means code exists. *Tested* means deterministic checks ran on a named snapshot. *Not tested* means no evidence. *Deferred* means intentionally later. *Experimental* means published without a release or qualification. Claude Code qualification status is kept in `QUALIFICATION_MATRIX.md` (a smoke run was recorded on 2026-11-21; deep qualification and independent evidence are not done).

**Decisions.** The canonical decision register is the first section of `OWNER_DECISION_AMENDMENTS.md`; open and deferred items are tracked there by ID (this paragraph previously listed them). Open owner decisions include branch policy and release mechanics (D1, D8, RG-1, RG-3), platform support beyond Linux (RG-4), the Claude Code support window (RG-5), authorization and budget for live agent runs (D3, RG-6) and command naming (P-8). OD-10 preserves the current experimental version `2.0.0.dev1` and authorizes no tag or release for the current scope; the permanent versioning and tagging policy (RG-2) remains open. The GQ/FOB/Studio dependency question (P-1) is resolved by OD-09. `OWNER_DECISION_AMENDMENTS.md` remains the canonical decision authority.

## Documentation authority map (this repository)

One authority per concern. Dated views elsewhere (for example the README status tables) carry an as-of date and point to the authority.

| Concern | Authority | Owns | Does not duplicate |
| --- | --- | --- | --- |
| Vision and principles | `VISION.md` | principles, pillars, long-term direction | status counts, gate states, roadmap order |
| Strategy and roadmap | `ROADMAP.md` (the sequence at the top is current; the rest is the historical plan) | stage order, priorities | decisions, qualification status |
| Decisions | `OWNER_DECISION_AMENDMENTS.md` (Decision register) | IDs, status, provenance, supersession | roadmap or matrix copies of decisions |
| Release-gate requirements | `RELEASE_GATES_RECONCILED.md` | G1-G10 text, Preview and Stable definitions | gate status |
| Qualification status and claims | `QUALIFICATION_MATRIX.md` (evidence log: `QUALIFICATION.md`, append-only) | Q1-Q3, gate status, allowed claims | project state, decisions, roadmap |
| Operational project state | `docs/engineering/PROJECT_STATE.md` (maintainer pointers; 50 lines at most; replaced in place; not distributed to consumer repositories) | baseline, gate states, blockers, pending decision IDs, next action, references | decisions, qualification results, history |
| Authorized task | the task's `TASK.md` | scope, criteria, plan approval | state, decisions |
| Results and evidence | the task's `RESULT.md`, `result.json`, verify report | outcomes, evidence-state table, observations | scope, claims |
| Findings and metrics | `docs/engineering/FINDINGS_REGISTER.csv`, `METRICS_CATALOG.csv` | findings, metric definitions | decisions |
| History | Git history, pull requests, `tasks/`, `CHANGELOG.md`, `QUALIFICATION.md` | what happened | current state; read only on demand |

Git is authoritative for technical repository state. `TASK.md` and explicit approval evidence are authoritative for authorized scope and gate decisions. A checkpoint, a status output or a commit never grants authorization.
