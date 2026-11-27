# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-26 (candidate of mission AI-SDLC-LITE-DOCS-CONSOLIDATION-001, before Gate 2). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baseline:** `329c4a0157a4b3a508b7096bc7775c796c849e3a` (`develop`, product version `2.0.0.dev1`, OD-10). The candidate is pinned by Git SHA only, recorded after owner acceptance in a separate scoped update; no tag is authorized.
- **Last verified base:** `329c4a0157a4b3a508b7096bc7775c796c849e3a`, for task DOCS-CONSOLIDATION-001 (the hash of the commit containing this file is deliberately not recorded).
- **Active mission:** AI-SDLC-LITE-DOCS-CONSOLIDATION-001, task revision r3 (r1 and r2 evidence preserved); task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** Gate 1 approved (owner message, 2026-11-26). Gate 2 pending.
- **Blockers:** none known.
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; non-blocking for Website First under the approved experimental scope; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Live preflight authorization is pending (RG-6).
- **Next authorized action:** wait for the owner's Gate 2 decision on the candidate; no integration, push, tag or release is authorized.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
