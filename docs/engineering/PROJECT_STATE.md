# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (after the default-branch switch to `main` and before the documentation PR of S5 merges). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** product version `2.0.0.dev1` (EXPERIMENTAL, OD-10). Canonical remote trunk `main` and legacy `develop` both pointed at `d1cdf851bac17d84147e7509a63cb0bbe6581cef` (tree `0e66776876f90fbc0fe8cb0759523a6086d311bc`, the merge of PR #36) when S5 began; legacy `master` is `7f925cd0c45b6501d743d09ebd8c9569edced40e`. The current tip is read from Git, not recorded here. No tag is authorized.
- **Last verified base:** `d1cdf851bac17d84147e7509a63cb0bbe6581cef`, for REPOSITORY-GOVERNANCE-001 Phase 2 S5.
- **Active mission:** AI-SDLC-LITE-REPOSITORY-GOVERNANCE-001 (M-01). Phase 1 accepted; Phase 2 steps S0 to S4 complete and S5 (default branch `main`, this documentation update) in progress. Remote evidence custody and legacy branch retirement are pending. Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** REPOSITORY-GOVERNANCE-001: Gate 1 approved per step; Gate 2 approved with limitations for Phase 1 and the CI correction (conditional acceptance for the final index correction); OD-20 to OD-26 recorded in the register. Independent-person qualification (G3/G10) remains NOT_MET. Lifecycle and closure semantics: `WORKFLOW.md`.
- **Authorization boundary:** each hosted change needs its own approved plan; legacy branch changes, tags, releases, private repositories and evidence uploads are not authorized; live provider execution is prohibited. Public visibility is not publication authorization.
- **Blockers:** none for code. M-01 remote closure is NOT_MET: legacy `master` and `develop` retirement and durable remote evidence custody are pending. Direct-push, force-push and deletion rejection are NOT_TESTED. Public-release blockers and open owner decisions stay in force: `ROADMAP.md`. WSL2-001 remains suspended.
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Live preflight authorization is pending (RG-6). Also pending, not implemented: information classification and privacy governance (M-02), local-to-hosted quality-gate parity, experience-driven learning from the PR #36 CI failure, bounded conditional acceptance, durable remote evidence custody, legacy branch retirement, and local canonical branch migration (S6).
- **Next action:** after this documentation PR merges, S6 (local branch migration, legacy-branch freeze and retirement decisions, final read-back); M-02 to M-08, M064-A, W01 and W02 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
