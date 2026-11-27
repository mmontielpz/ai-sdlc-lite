# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (after the local integration of STRATEGIC-DOCS-ALIGNMENT-001). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** executable baseline `329c4a0157a4b3a508b7096bc7775c796c849e3a` (product version `2.0.0.dev1`, EXPERIMENTAL, OD-10; also the last published `develop` tip observed 2026-11-27); accepted local baseline `28274c1b65b1af11ff48b5c0694be6454b8d218e` (tree `6845ea94f3074489d719d5a4289df4e901dbbac5`, 12 commits ahead of it, unpublished). One checkpoint-only commit follows the candidate; its own hash is deliberately not recorded here. No tag is authorized.
- **Last verified base:** `28274c1b65b1af11ff48b5c0694be6454b8d218e`, for REPOSITORY-GOVERNANCE-001 Phase 1.
- **Active mission:** AI-SDLC-LITE-REPOSITORY-GOVERNANCE-001 (M-01), Phase 1 local implementation: a candidate exists in an isolated local clone and is **pending human acceptance, integration and remote synchronization**; it is not accepted, integrated or remotely closed. M-12 research is closed. Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** EXTERNAL-BENCHMARKING-001: human acceptance approved with limitations (owner Gate 2, 2026-11-27); OD-20 to OD-25 recorded in the register (2026-11-27). REPOSITORY-GOVERNANCE-001: Gate 1 approved with refinements (Phase 1 only); Gate 2 pending. Independent-person qualification (G3/G10) remains NOT_MET. Lifecycle and closure semantics: `WORKFLOW.md`. Accepted limitations are in the mission evidence.
- **Authorization boundary:** hosted changes, fetch, pull, push, branch changes, tags, releases and publication are prohibited; live provider execution is prohibited. Public visibility is not publication authorization.
- **Blockers:** none for the local state. M-01 remote closure is NOT_MET (hosted transition not done; hosted controls are targets, not enforced). Public-release blockers and open owner decisions stay in force: `ROADMAP.md`. WSL2-001 remains suspended.
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; non-blocking for Website First under the approved experimental scope; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Live preflight authorization is pending (RG-6). Also pending: owner acceptance of publishing the 12 unpublished commits that carry personal commit metadata (OD-23); each hosted change and publication step needs its own approved execution plan.
- **Next action:** wait for the owner Gate 2 decision on REPOSITORY-GOVERNANCE-001 Phase 1; the hosted transition, synchronization, M-02 to M-08, M064-A, W01 and W02 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
