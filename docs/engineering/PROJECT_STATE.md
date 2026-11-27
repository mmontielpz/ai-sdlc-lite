# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (S9a documentation reconciliation prepared as a pull request; before its Gate 2 and merge). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** product version `2.0.0.dev1` (EXPERIMENTAL, OD-10). Canonical trunk `main`. Frozen legacy tips: `develop` `d1cdf851bac17d84147e7509a63cb0bbe6581cef`, `master` `7f925cd0c45b6501d743d09ebd8c9569edced40e`. The current tip is read from Git, not recorded here. No tag is authorized.
- **Last verified base:** `de46b50d6505d8ee163d364cbe895c59f59ef95e`, for REPOSITORY-GOVERNANCE-001 S9a.
- **Active mission:** AI-SDLC-LITE-REPOSITORY-GOVERNANCE-001 (M-01). S0 to S7 complete; S8 preparation partial; S9a in review. Remote evidence custody is pending. Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** S9a Gate 1 approved with clarifications; Gate 2 PENDING. OD-27 to OD-33 are recorded in the register by the S9a change. Independent-person qualification (G3/G10) remains NOT_MET. Lifecycle and closure semantics: `WORKFLOW.md`.
- **Authorization boundary:** each hosted change needs its own approved plan; legacy branch changes, tags, releases, private repositories, restricted-storage locations and evidence uploads are not authorized; live provider execution is prohibited. Public visibility is not publication authorization.
- **Blockers:** none for code. M-01 closure is NOT_MET: remote evidence custody, restore verification and S9b are pending. Direct-push, force-push and deletion rejection are NOT_TESTED. Public-release blockers and open owner decisions stay in force: `ROADMAP.md`. WSL2-001 remains suspended and deferred (OD-31).
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, RG-8, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Also pending: restricted-storage locations and private repository creation (OD-29).
- **Next action:** Gate 2 on the S9a pull request; after merge and synchronization, custody execution under its own Gate 1 (see `ROADMAP.md`, Sequence through W01). M-02, M064-A, W01 and W02 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
