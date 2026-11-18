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

**Status vocabulary.** *Implemented* means code exists. *Tested* means deterministic checks ran on a named snapshot. *Not tested* means no evidence. *Deferred* means intentionally later. *Experimental* means published without a release or qualification. Claude Code has **not** passed any qualification.

**Not decided here** (open owner decisions): branch policy and release mechanics (D1/D8), tagging, publication, platform support beyond Linux, Claude Code support window, authorization and budget for live agent runs (D3), the fate of the GQ/FOB/Studio sequence whose listed dependency on CODEX-004 is unresolved, and command naming.
