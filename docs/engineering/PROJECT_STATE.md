# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (M01-CLOSE-AND-PILOT-READY in progress; custody pending). Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** product version `2.0.0.dev1` (EXPERIMENTAL, OD-10). Canonical trunk `main`. Frozen legacy tips: `develop` `d1cdf851bac17d84147e7509a63cb0bbe6581cef`, `master` `7f925cd0c45b6501d743d09ebd8c9569edced40e`. The current tip is read from Git, not recorded here. No tag is authorized.
- **Last verified base:** `2ecc8db711c837d8b0a07afe383515447a29e115` (M-02 slice and M064-A preparation integrated, post-merge CI passed).
- **Active mission:** M01-CLOSE-AND-PILOT-READY. S0 to S7 and S9a complete; S8 preparation partial. The private evidence repository holds a scaffold only; no evidence is uploaded. Seven held packages have proposed sanitized derivatives (OD-35). Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** mission Gate 1 approved; Gate 2 approved and integrated for the M-02 and M064-A pull request; Gate 2 for S9b not yet requested. Independent-person qualification (G3/G10) remains NOT_MET. Lifecycle and closure semantics: `WORKFLOW.md`.
- **Authorization boundary:** the mission covers routine in-scope local and pull-request work. Evidence upload needs owner security confirmation; restricted-storage locations, legacy branch changes, tags, releases and live provider execution are not authorized. Public visibility is not publication authorization.
- **Blockers:** none for code. M-01 closure is NOT_MET (see `ROADMAP.md`, M-01 closure criteria): owner security confirmation, derivative approval, a confidentiality decision on existing content, upload, restore and restricted-storage verification are pending. Direct-push, force-push and deletion rejection are NOT_TESTED. WSL2-001 remains suspended and deferred (OD-31).
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, RG-8, D1, D3, D8, P-6, P-8, P-9. W01 scope is pending M064-A (OD-07). Also pending: restricted-storage locations and private repository creation (OD-29).
- **Next action:** owner security and eligibility decisions and restricted copies; then upload, restore verification and the final S9b change for Gate 2. W01 and W02 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
