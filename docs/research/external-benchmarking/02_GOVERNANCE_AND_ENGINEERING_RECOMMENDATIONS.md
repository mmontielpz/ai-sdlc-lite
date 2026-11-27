# 02 Governance and engineering recommendations (accepted research record; recommendations are not authorizations)

**Canonical record, accepted 2026-11-27 (owner Gate 2).** Owner refinements EB-F01 to EB-F06 are applied below; decisions are recorded in the register as OD-20 to OD-25. The original review package is kept unchanged outside the repository.

Baseline `28274c1b65b1af11ff48b5c0694be6454b8d218e`. Inputs: `01_EXTERNAL_BENCHMARKING.md` (source ids `[id]`, hosted observations H-1 etc.), the accepted Deep Audit (`DA-*`) and the strategic alignment (OD-12..OD-19, H1-H6). Recommendations are INTERPRETATION built on observed practice; expected benefits are **expected, not measured**. Cross-cutting codes per row: **E** enforceability (M mechanically enforced, V mechanically verified, H human-reviewed, A advisory), **F** expected efficiency (+ fewer prompts/rework/maintenance, 0 neutral, - cost), **I** interoperability across agents and Git platforms (H/M/L), **R** recoverability from a clean environment (H/M/L). "Block" = proposed release-blocking for public distribution; others are maturity improvements. Owner direction (Repository-First Governance, O2 direction, secure-by-default) is applied, not re-decided.

## 1. Recommendations (ADOPT, ADAPT, DEFER, REJECT)

| ID | Recommendation | Sources | Finding | Mission | Disp | Block | E/F/I/R | Value, security, cost, context |
|---|---|---|---|---|---|---|---|---|
| R-01 | Ruleset on the trunk: PR required, `ci-gate` required, force-push and deletion blocked, **no bypass for administrators** (observed state binds non-admins only) | gh_doc_protected, gh_doc_rulesets, sc_checks | DA-D08-04, DA-D09-02 | M-01 | ADOPT | yes | M/+/M/H | closes the sole-maintainer bypass; minutes of settings; zero context; needs owner-side verification of plan features |
| R-02 | Single trunk `main` (O2) done once, **before the first tag**; first verify what a hosted rename does to protection and open PRs | none reviewed on rename behaviour (UNKNOWN) | DA-D09-01 | M-01 | ADAPT | yes | H/0/M/M | convention and one story; about 17 tracked files and CI filters change; no authorization given by this text |
| R-03 | Do not require approving reviews (one maintainer cannot approve own PR); require PR + CI and a PR checklist recording Gate 2 and the independent agent review; revisit with a second maintainer | gh_doc_protected, sc_checks | DA-D09-02 | M-01 | ADAPT | no | H/+/H/M | keeps accountability visible without a bypass habit; Scorecard Code-Review will score low (disclosed) |
| R-04 | One PR template: mission id, Gate 1 and Gate 2 references, sanitized evidence reference, exception flag | gh_doc_templates | DA-D11-01 | M-01 | ADOPT | no | A/+/H/H | traceability at near-zero cost; advisory unless CI checks the title (DEFER) |
| R-05 | Backlog: GitHub Issues only for authorized missions, linked from the PR; no project boards | gh_doc_templates | DA-D01-02 | M-01 | ADAPT | no | H/0/H/H | one authoritative place for task state; avoids duplicating ROADMAP.md |
| R-06 | Initial synchronization by feature-branch PR with a **merge commit** is the preferred candidate (not unconditional): approve the method only after verifying GitHub behaviour, ancestry and branch protection, so accepted commit identities and evidence references stay reachable | none reviewed on merge methods (Git general knowledge) | H-1 | M-01 | ADAPT | yes | V/0/H/H | squash and rebase would rewrite SHAs cited by accepted evidence; cost one merge commit |
| R-07 | Evidence index (evidence id, classification, integrity reference, custody status, store reference, retention, custodian) in the repository, plus authorized remote private storage for restricted evidence (private companion repository is the preferred candidate to evaluate; not created) | internal | DA-D08-05 | M-01 | ADOPT | yes | H/0/M/H | integrity references without publishing; permanent local-only custody is not the target |
| R-08 | CODEOWNERS, signed commits, merge queue, required linear history | gh_doc_codeowners | n/a | M-01 | DEFER | no | -/-/-/- | no value with one maintainer; revisit at the second contributor |
| R-09 | Separate ADR directory, standing governance bodies, chat channels as a record | bm_contrib, internal register | n/a | M-01 | REJECT | no | -/-/-/- | the register already records decisions; chat is not recoverable |
| R-10 | `SECURITY.md`: document accurate known limitations and security boundaries (untracked-content reading; detection after execution versus prevention); do **not** classify DA-D08-01 as harmless or "by design" | uv_security (pattern of publishing boundaries) | DA-D08-01 R1 | M-02 | ADAPT | yes | A/+/H/H | honesty before reach; docs only |
| R-11 | Private vulnerability reporting: **confirmed enabled** by the owner-side read of 2026-11-27; date the observation in `SECURITY.md` | gh_doc_pvr, gh_doc_secpolicy | DA-D08-04 (G9) | M-02 | ADAPT | no | V/0/L/H | residual work is documentation only |
| R-12 | PGP key, security mailing list, bounty programme | ng_security | n/a | M-02 | REJECT | no | -/-/-/- | vendor-scale; GitHub private reporting is sufficient |
| R-13 | Add a short code of conduct with a named contact | sk_contrib, bp_criteria | DA-D11-01 | M-05 | ADOPT | no | A/0/H/M | needs an owner contact decision |
| R-14 | Verifier untracked-content design: no external source answers it, so the internal design is **decision-gated** and its resolution remains a **candidate release blocker**; it is not deferred for lack of an external reference | none | DA-D08-01 | M-03 | ADAPT (decision-gated) | yes (owner direction) | V/0/M/M | scope integrity versus confidentiality stays an owner decision; do not weaken deterministic verification |
| R-15 | Document that the verifier detects after execution and name OS-level sandboxing (user-side, optional) as complementary hardening | cc_doc_sandbox, cc_doc_permissions2 | DA-D08-01 | M-02, M-08 | ADAPT | no | A/0/M/H | honest limits at no code cost; sandbox adoption in ASL tooling DEFER |
| R-16 | Tag-triggered release workflow that rejects a non-matching tag, top-level `permissions: {}` with per-job grants; keep actions pinned by SHA | sk_release, uv_release, gh_doc_hardening | DA-D10-01..03 | M-04 | ADOPT | yes | M/+/M/H | repeatable and auditable; about one workflow file; no new dependency |
| R-17 | GitHub release carries a SHA-256 checksum file and release notes; keep a Keep-a-Changelog layout in `CHANGELOG.md` | kac_web, bp_criteria | DA-D10-02 | M-04 | ADOPT | yes | V/+/H/H | users can verify bytes; checksum shows integrity only, not origin |
| R-18 | Use GitHub-native build-provenance attestation; **claim no SLSA level** until verified | gh_doc_attest, slsa_levels_web | DA-D10-03 | M-04 | ADAPT | no | V/0/M/H | adds token permissions to one job; verification step required |
| R-19 | Enable immutable releases before the first release | gh_doc_immutable | DA-D10-03 | M-04 | ADOPT | yes | M/0/M/H | blocks tag and asset swapping; owner setting; the setting exists and is currently disabled (authenticated read, 2026-11-27); not enabled by this record |
| R-20 | One-page versioning and compatibility policy: how PEP 440 `.devN` maps to SemVer (UNKNOWN in sources), what is stable, deprecation steps | semver, pt_backcompat, uv_versioning | DA-D02-05, DA-D09-05/06 | M-04 | ADAPT | yes | A/+/H/M | answers RG-2; fold into M-04 |
| R-21 | PyPI trusted publishing, protected release environments with signing keys | uv_release | RG-3 | M-04 | DEFER | no | -/-/-/- | heavy for a first preview; revisit with RG-3 |
| R-22 | Run OpenSSF Scorecard and treat Best Practices "passing" as a checklist; no badge chase | sc_checks, bp_criteria | DA-D11 | M-05 | DEFER | no | V/0/H/M | running it needs separate authorization; expect low Code-Review score |
| R-23 | Platform page with exact tested versions; list WSL2 prerequisites only as observed | cc_doc_sandbox | DA-D06-01 | M-06 | ADAPT | no | A/0/M/H | claims follow observation, never development use |
| R-24 | M-07 matrix: `AGENTS.md` only, `CLAUDE.md` only, both, `CLAUDE.md` importing `AGENTS.md`; document the import line for Claude Code users (AGENTS.md is **not** read when a `CLAUDE.md` exists) | cc_doc_memory | DA-D04-02 | M-07 | ADOPT | yes | V/+/M/H | evidence-backed fix to the precedence gap; one doc line |
| R-25 | Observe whether Claude Code loads `.agents/skills`; if not, make the `claude-code` target the documented default for Claude users | cc_doc_skills, cx_doc_skills | DA-D04-01 | M-07 | ADAPT | yes | V/+/M/H | needs live budget (RG-6); source does not state it (UNKNOWN) |
| R-26 | Keep entry files small (Claude guidance under 200 lines; Codex 32 KiB chain cap); keep progressive disclosure | cc_doc_memory, cx_doc_agentsmd, cx_doc_skills | DA-D03-01 | M-08 | ADOPT | no | V/+/H/M | context efficiency is expected, not measured |
| R-27 | Intent-based README front table (build, install, verify, contribute) merged into the single M-08 rewrite | sk_readme | DA-D01-01 | M-08 | ADAPT | no | A/+/H/M | one README rewrite; do not copy another project's structure |
| R-28 | Measure time to first verified task in W01 and the first preview users | none (no external data) | DA-D13-02 | M-08 | ADAPT | no | V/0/H/M | internal metric; no published baseline exists |
| R-29 | Docs website now; community chat channels | bm_readme | DA-D14-01 | M-08 | DEFER | no | -/-/-/- | W02 follows W01 (owner decision) |
| R-30 | Adopt another project's benchmark claims or methodology as evidence | none found | DA-D13-01 | research | REJECT | no | -/-/-/- | no outcome data in sources read; EB-07 stays internal |

Release-blocking summary: R-01, R-02, R-06, R-07 (governance), R-10, R-11 (security text), R-14 (owner direction), R-16, R-17, R-19, R-20 (release), R-24, R-25 (agent evidence). Everything else is a maturity improvement.

## 2. Repository-first governance: one authoritative location per information class

| Class | Authority (existing structure) | Not authoritative |
|---|---|---|
| Source code | trunk branch on GitHub | any clone, worktree or local branch |
| Vision, roadmap, architecture | `VISION.md`, `ROADMAP.md`, `ARCHITECTURE.md` | issue text, chat |
| Governance, contribution, security | `CONTRIBUTING.md`, `SECURITY.md` (+ code of conduct) | wiki |
| Decisions and exceptions | decision register `docs/product/OWNER_DECISION_AMENDMENTS.md` | PR comments (link only) |
| Tasks and backlog | GitHub Issue per authorized mission; task contract file `TASK.md` pattern | project boards |
| Reviews and acceptance | PR (mission id in the title) with a sanitized result summary and Gate 2 reference; summary file at `tasks/<MISSION>/RESULT.md` per the existing convention | local `RESULT.md` copies |
| Agent instructions and skills | `AGENTS.md`, `.agents/skills`, installer sources in the repository | personal `~/.claude` or `~/.codex` files |
| Research protocols and accepted results | `docs/research/` (this research: `docs/research/external-benchmarking/`) | scratch directories |
| Reproducible verification | `.github/workflows/ci.yml` (`ci-gate`) | agent-reported runs |
| Releases | GitHub tag and release with checksums | ad-hoc wheels |
| Operational state | `docs/engineering/PROJECT_STATE.md` (pointers only) | conversation history |
| Restricted evidence | owner-chosen restricted store; **index and SHA-256 in the repository** | the repository itself |

Temporary clones, worktrees, caches and test outputs stay local and are never authority.

## 3. Governance enforcement matrix

The Enforcement column states the **target** mechanism that the approved design (OD-24) intends to use. It is not a description of what GitHub enforces today. Applied and verified on 2026-11-27 (authenticated read-only, see `01` section 1a): classic branch protection on `master` and `develop` (pull request required with 0 approving reviews, required check `ci-gate` with strict status, administrators not enforced, no force-push or deletion); no rulesets; all merge methods allowed; secret scanning, push protection and vulnerability alerts disabled; private vulnerability reporting enabled; immutable releases disabled; Actions allow all actions, SHA pinning not required, default token read-only. No target control below is applied except where the row says so; `main` does not exist yet. Rows marked **target** become verified only after the owner-approved synchronization steps and a dated read-back.

| Requirement | Authoritative record | Enforcement | Verification | Role | Exception path | Mission |
|---|---|---|---|---|---|---|
| Accepted source is version-controlled and published | trunk | **target:** ruleset on `main` (PR required, no admin bypass), not yet applied. **Applied today:** classic protection on `master` and `develop` (PR required, 0 approvals, administrators not enforced) | `git rev-list origin/<trunk>..<trunk>` is 0; CI green | maintainer | register row + dated PR label | M-01 |
| Quality gates reproducible | `ci.yml` `ci-gate` | **applied today** as required check `ci-gate` (strict) on `master` and `develop`; **target:** same on `main` | CI rerun from a clean clone | maintainer | register row | M-01 |
| No force-push or deletion of trunk and release tags | rulesets | **applied today** on `master` and `develop` (classic protection: no force-push, no deletion); **target:** ruleset on `main` and release tags, not applied; tag protection not verified (UNKNOWN) | hosted settings read-back, dated | maintainer | register row | M-01 |
| Work traceable to authorized tasks | issue and PR title | **advisory** (template) | optional CI title check (DEFER) | agent, maintainer | note in PR | M-01 |
| Decisions and exceptions recorded | register | **human-reviewed** | register integrity script (can be run in CI later) | owner | none: required | M-01 |
| Reviews preserve accountability | PR record | **human-reviewed**; no approving-review requirement (R-03) | PR checklist present | owner | register row | M-01 |
| Vision, roadmap, architecture canonical | one file each | **human-reviewed** | doc consistency checks | maintainer | register row | M-08 |
| Skills and contracts versioned | repo + bundle inventory | **verified** by existing tests (bundle 44 entries, wheel 72 members) | CI | maintainer | register row | M-07 |
| Agent follows instructions | `AGENTS.md` | **advisory only** (sources: instruction files are context, not enforced) | post-execution `verify` detects scope drift; ruleset and CI enforce integration | owner | n/a | M-07 |
| Handoffs independent of conversation | `PROJECT_STATE.md`, PR | **human-reviewed** | clean-clone recovery check (section 5, step 11) | maintainer | register row | M-01 |
| No accepted state local-only | trunk ahead-count | **verified** at closure (OD-25; automation DEFER) | ahead-count 0 recorded in the PR | maintainer | time-boxed register row | M-01 |
| Sensitive material never published | `SECURITY.md`, evidence index | secret scanning and push protection are **disabled today** (read 2026-11-27); enabling them is a **target** requiring owner action; until then **advisory** plus pre-sync pattern scan (not proof of absence) | owner-side hosted read-back; names-and-counts-only scan | owner | none | M-01, M-02 |
| Governance changes authorized | register | **human-reviewed** (CODEOWNERS DEFER) | PR touching governance files cites a register row | owner | none | M-01 |

## 4. Restricted evidence policy (OD-21, OD-22)

Classes: public canonical records; sanitized evidence summaries; reproducible CI evidence; restricted evidence; temporary artifacts; credentials and secrets; personal information; vulnerability evidence; private third-party material.

| Class | Home | Integrity reference | Retention |
|---|---|---|---|
| Public canonical, sanitized summary | repository | Git history | permanent |
| Reproducible CI evidence | CI logs plus rebuild from the tagged commit; Actions artifacts are short-lived and **not** a durable record | commit SHA | reproduce on demand |
| Restricted (raw mission logs, evidence packages, bundles with history, hosted-state snapshots) | **authorized remote private storage** (target); never the public repository | SHA-256 in `docs/engineering/EVIDENCE_INDEX.csv` | proposed: life of the project (not yet authorized) |
| Credentials and secrets, personal information, vulnerability evidence, private third-party IP | never committed; vulnerability evidence only through private reporting | none public | minimum necessary |
| Temporary | local | none | delete freely |

Target custody (OD-21): accepted recovery records and restricted evidence must not remain exclusively local indefinitely; existing evidence mechanisms are preserved during the transition. A **private companion repository** is the preferred candidate to evaluate. It is not created and nothing is uploaded; it must not hold a second authoritative copy of the framework, roadmap or product state, and never credentials. A store is acceptable only with a named custodian, access control, restore instructions and a periodic restore test. Index custody statuses: `REMOTE_AVAILABLE`, `LOCAL_PENDING_MIGRATION`, `MISSING_OR_UNKNOWN`, `TEMPORARY_NOT_REQUIRED`; no remote location is recorded until one exists.

## 5. Migration to repository-first (conditional plan; the repository is already public, but publishing additional commits, branches, packages, tags, releases or evidence stays unauthorized until explicitly approved; EB-F06)

1. **Hosted state.** Anonymous evidence is in `01` section 1; the authenticated read-only check dated 2026-11-27 is in `01` section 1a (protection details, administrator enforcement, required reviews, private vulnerability reporting, Actions permissions, secret scanning, push protection, immutable-release setting). Still UNKNOWN: rename behaviour for protection and open PRs, merge-method behaviour under the target ruleset, tag protection. Repeat the read immediately before each hosted change.
2. **Branch strategy (O2).** After step 1 and the exposure decision, choose how to reach a single `main` (rename the content trunk and retire the stale default); verify protection and PR behaviour afterwards; before any tag.
3. **12-commit divergence.** Local `develop` is 12 commits ahead of public `develop` `329c4a0` (6 earlier plus the six strategic-alignment and integration commits). Publish only by feature-branch PR with a merge commit (R-06), CI required, no direct push, no force.
4. **History and metadata (H-1).** Owner decision (OD-23): forward-only hygiene for classified low-impact metadata, no rewrite or force-push, current visibility intended and maintained conditionally; credentials or confidential third-party material would stop work and escalate. Forward-only means new commits (the nine account-specific path occurrences in eight historical task records get neutral placeholders in the current tree); Git history still contains the originals and the existing exposure is not removed. Publishing the 12 unpublished commits adds instances of the owner's non-noreply address and needs separate explicit owner acceptance.
5. **Pre-sync scan.** Three stages, kept distinct. (a) Original research stage: the unpublished commits were not scanned. (b) The later 12-commit preflight, 2026-11-27: names-and-counts-only pattern scan, no pattern hits in added lines, 12 more commits carrying the existing non-noreply identity class. (c) An independent review of all 17 unpublished commits, reported by the owner as part of the Phase 1 review; its method is not restated here. All are pattern-based inspections: absence of matches does not prove absence of secrets or sensitive content. Repeat on the final range before any publication.
6. **Records.** Sanitized acceptance summaries go to `tasks/<MISSION>/RESULT.md` (existing convention) with no absolute paths or personal data; research results to `docs/research/external-benchmarking/` (verified below); decisions to the register.
7. **Amendments** (section 6) approved by the owner, then recorded under M-01.
8. **Protection and checks.** R-01 and R-16: required `ci-gate`, unique job names, tag ruleset for `v*`, immutable releases.
9. **Controlled initial synchronization.** Prerequisites: steps 1, 4, 5 done and an owner decision recorded; PR from a dedicated branch; merge commit; after merge confirm trunk equals the accepted SHA lineage.
10. **Prevent future local-only accepted state (OD-25).** Lifecycle: authorized task or issue, Gate 1, scoped implementation, verification and PR review, Gate 2, integration, remote synchronization and closure. Gate 2 does not require an already merged PR; closure is an operational postcondition, not a third gate; locally accepted but unsynchronized work is not remotely closed and any temporary exception is recorded. A later option is an `ai-sdlc status` warning (code change, DEFER).
11. **Clean-environment recovery check.** In an empty directory: clone from GitHub, check out the tagged or trunk commit, read `PROJECT_STATE.md`, run the CI-policy suite offline, compare the result with the recorded one. Repeat per release and after any storage change. Success means no local file was needed.
12. **Exceptions.** Only the owner; a register row with scope, reason, expiry date and the PR; applied no longer than one mission.

**Packaging check (actual inventory, not grep).** `pyproject.toml` package-data globs touching `docs/` are `docs/*.md`, `docs/product/*.md` and `docs/qualification/*.md`; the 2.0.0.dev1 wheel (72 members) and consumer bundle (44 entries) contain no `docs/research/*` member. So `docs/research/external-benchmarking/` is excluded from both **unless** a bundled document links to it; keep it unlinked from bundled files (`README.md`, `ROADMAP.md`, the register) or re-run the inventory comparison when linking.

## 6. Decision-register amendment (recorded; see the register)

The owner decisions of 2026-11-27 are recorded as OD-20 (Repository-First Governance, approved), OD-21 (narrows OD-08; custody target, approved with refinement), OD-22 (narrows D12 for AI-SDLC Lite only), OD-23 (visibility, history, identity and publication policy), OD-24 (single trunk `main` and target hosted controls, approved as targets, not enforced) and OD-25 (lifecycle semantics) in `docs/product/OWNER_DECISION_AMENDMENTS.md`. Existing rows, including OD-08 and D12, are unchanged. The register is the single source for their wording; it is not repeated here.

## 7. Owner decisions (status at acceptance)
Decided 2026-11-27: Repository-First Governance (OD-20); custody target and private-storage evaluation (OD-21); D12 narrowing (OD-22); visibility intended, forward-only hygiene, noreply identity (OD-23); single trunk `main` created from the verified tip, merge commit only and protection objectives as targets, no routine administrator bypass with a controlled emergency procedure (OD-24); lifecycle and closure (OD-25); live agent qualification deferred to M-07.
Pending: owner acceptance of publishing the 12 unpublished commits (personal commit metadata); each hosted change, branch creation, publication, private-repository creation and evidence upload needs its own approved execution plan.

## 8. Evidence limits
Anonymous access shows only public data (UNKNOWN items in `01`). Vendor and GitHub documentation is unversioned. EB-07 and part of EB-03 found no external method. No benchmark ran, so every efficiency statement is expected, not measured. Distribution-safety scanning is staged (section 5, step 5): this research stage did not scan the unpublished commits; the later 12-commit preflight and the independent review of 17 commits did, by pattern-based inspection only, which cannot prove absence of secrets. Product qualification is unchanged.
