# Project state (maintainer operational checkpoint)

Replace-in-place pointer file, 50 lines at most. It holds pointers only: no decision text, no qualification results, no history (history lives in Git). It is not distributed to consumer repositories. It never grants authorization: Git is authoritative for technical repository state; `TASK.md` and explicit approval evidence are authoritative for scope and gate decisions. Update it at a gate decision, an interruption or hand-off, and when a blocker or pending decision changes, inside an approved task scope. Gate states below are copies of approval evidence.

## State

- **As of:** 2026-11-27 (S9b submitted for Gate 2). M-01 closes when that change is accepted, integrated and synchronized. Branch and HEAD: run `ai-sdlc status`; they are not copied here.
- **Pinned baselines:** product version `2.0.0.dev1` (EXPERIMENTAL, OD-10). Canonical trunk `main`. Frozen legacy tips: `develop` `d1cdf851bac17d84147e7509a63cb0bbe6581cef`, `master` `7f925cd0c45b6501d743d09ebd8c9569edced40e`. The current tip is read from Git, not recorded here. No tag is authorized.
- **Last verified base:** `2ecc8db711c837d8b0a07afe383515447a29e115` (M-02 slice and M064-A preparation integrated, post-merge CI passed).
- **Active mission:** M01-CLOSE-AND-PILOT-READY. Essential evidence is in the private companion repository and was restored from it; restricted originals are in a local encrypted package under a time-limited exception (OD-36). Task text and evidence are kept in the external mission evidence directory (path withheld, D12).
- **Gates:** mission Gate 1 approved; Gate 2 approved and integrated for the M-02 and M064-A pull request; Gate 2 for S9b is requested on its pull request. Independent-person qualification (G3/G10) remains NOT_MET. Lifecycle and closure semantics: `WORKFLOW.md`.
- **Authorization boundary:** further evidence uploads, legacy branch changes, tags, releases and live provider execution are not authorized. Public visibility is not publication authorization.
- **Blockers:** none for code. Open: offline and remote restricted copies due 2026-12-27 (OD-36); follow-up content review (separate Gate 1). Direct-push, force-push and deletion rejection are NOT_TESTED. Public-release blockers stay in force: `ROADMAP.md`. WSL2-001 remains suspended and deferred (OD-31).
- **Pending decisions** (register IDs only): RG-1, RG-2 (permanent versioning and tagging policy; OD-10 preserves `2.0.0.dev1` and authorizes no tag or release), RG-3, RG-4, RG-5, RG-6, RG-8, D1, D3, D8, P-6, P-8, P-9. Also pending: W01 pilot repository, content, environment, agent version and tools (see `tasks/AI-SDLC-LITE-M064A/TASK.md`).
- **Next action:** Gate 2 on S9b, merge and synchronization; then W01 owner inputs and preflight. W01 and W02 are not started.

## References

- Decisions: `docs/product/OWNER_DECISION_AMENDMENTS.md` (Decision register); authority map: `docs/product/README.md`.
- Roadmap (current sequence at the top): `ROADMAP.md`. Qualification status and claims: `QUALIFICATION_MATRIX.md`.
- Workflow, context and checkpoint rules: `WORKFLOW.md` (Authority, context and checkpoint).
- Findings and metrics: `docs/engineering/FINDINGS_REGISTER.csv`, `docs/engineering/METRICS_CATALOG.csv`; pilot measurement: `docs/research/BENCHMARK_PROTOCOL.md` section 5.
