# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (after the local fast-forward integration of STRATEGIC-DOCS-ALIGNMENT-001). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** executable baseline `329c4a0157a4b3a508b7096bc7775c796c849e3a` (product version `2.0.0.dev1`, EXPERIMENTAL, OD-10); previous accepted baseline `bfd7ef133d03bdee62aeb241ad9672714266db81`; accepted strategic documentation candidate `d71b9441c94f187cbc1ab60adcade1ba87357fbf` (tree `db9ea23d32fe5fbf5877e73de81439237a842a69`, five commits). One checkpoint-only commit follows it; its own hash is deliberately not recorded here. No tag is authorized.
- **Last verified base:** `d71b9441c94f187cbc1ab60adcade1ba87357fbf`, for the checkpoint task of STRATEGIC-BASELINE-INTEGRATION-001.
- **Active mission:** none. STRATEGIC-DOCS-ALIGNMENT-001 is accepted with limitations and integrated locally by fast-forward only (BASELINE-INTEGRATION precedent); STRATEGIC-BASELINE-INTEGRATION-001 ends with this checkpoint. Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** STRATEGIC-DOCS-ALIGNMENT-001: human acceptance approved with limitations (owner Gate 2, 2026-11-27); independent agent review completed (PASS); independent-person qualification (G3/G10) remains NOT_MET. Accepted limitations (retrospective verifier baseline, unlocated earlier packages, agent-reported regression/packaging/installer results, hosted GitHub state UNKNOWN): see the mission evidence. Decisions OD-12 to OD-19: `docs/product/OWNER_DECISION_AMENDMENTS.md`.
- **Authorization boundary:** remote changes are prohibited (no fetch, pull, push, tag, release or publication); live provider execution is prohibited.
- **Blockers:** none for the local state. Public-release blockers and open owner decisions stay in force: `ROADMAP.md` (owner direction, mission index). Public distribution is not authorized; WSL2-001 remains suspended.
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; non-blocking for Website First under the approved experimental scope; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Live preflight authorization is pending (RG-6).
- **Next planned activity** (not authorized to start): External Open Source Benchmarking, then M-01 Repository Governance. Each needs its own owner authorization; M-01 to M-03, M064-A, W01 and W02 are not started. Wait for further owner authorization.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
