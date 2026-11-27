# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (baseline `bfd7ef133d03bdee62aeb241ad9672714266db81`; the accepted local integration of DOCS-CONSOLIDATION-001 r3). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** executable baseline `329c4a0157a4b3a508b7096bc7775c796c849e3a` (product version `2.0.0.dev1`, OD-10); accepted implementation `00ef2d87d35da8b62271c723606d6627334b2da2` (DOCS-CONSOLIDATION-001 r3, five commits). One checkpoint-only commit follows the accepted implementation; its own hash is deliberately not recorded here. No tag is authorized.
- **Last verified base:** `bfd7ef133d03bdee62aeb241ad9672714266db81` (accepted local baseline; tree `cb67d3a84f37189143fe704edd293fc22dd15a9f`), for STRATEGIC-DOCS-ALIGNMENT-001.
- **Active mission:** AI-SDLC-LITE-STRATEGIC-DOCS-ALIGNMENT-001 (docs only): an implementation candidate exists in an isolated local clone and is **pending human acceptance and integration**; it is neither accepted nor integrated. Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** BASELINE-INTEGRATION-001 accepted with limitations (accepted baseline above). STRATEGIC-ALIGNMENT-001: Gate 2 approved with refinements (2026-11-27; OD-12 to OD-19 recorded in the register). STRATEGIC-DOCS-ALIGNMENT-001: Gate 1 approved with refinements (2026-11-27); Gate 2 pending; integration requires a separate approval.
- **Authorization boundary:** remote changes are prohibited (no fetch, pull, push, tag, release or publication); live provider execution is prohibited.
- **Blockers:** none known.
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; non-blocking for Website First under the approved experimental scope; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Live preflight authorization is pending (RG-6).
- **Next authorized action:** wait for the owner Gate 2 decision on STRATEGIC-DOCS-ALIGNMENT-001; WSL2-001 (suspended), M064-A, W01, W02 and M-01 to M-14 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
