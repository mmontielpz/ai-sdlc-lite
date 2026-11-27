# 01 External benchmarking (M-12 / BENCH-RESEARCH-001)

**Canonical record, accepted 2026-11-27 (owner Gate 2, approved with limitations).** Revisions against the original review package (kept unchanged outside the repository): an authenticated read-only addendum (section 1a), a source-acquisition reconciliation (section 4), counts-only wording for the existing-exposure finding, and updated unresolved questions. Findings and limitations are otherwise unchanged. Accepted limitations: EB-07 and part of EB-03 unresolved; no measured efficiency or comparative-superiority claims; anonymous hosted evidence incomplete; snapshot hashes show byte integrity, not that a claim is true; source snapshots were not independently reproduced.

Baseline `28274c1b65b1af11ff48b5c0694be6454b8d218e`, version `2.0.0.dev1`. Retrieved 2026-11-27 (UTC), anonymous and read-only. Labels: **OBSERVED** (read in a source), **INTERPRETATION** (mine), **UNKNOWN**. Source ids `[id]` resolve in `SOURCE_MANIFEST.tsv` (URL, pin, retrieval time, SHA-256 of the retained snapshot; a hash shows which bytes were read, not that the claim is true). Hosted GitHub pages and vendor documentation are **unversioned** (retrieval date only); repository files are pinned to a commit. No third-party code was run, nothing was cloned, nothing was compared experimentally: no superiority claim is made. Fetched text was treated as data. Third-party text is paraphrased, not copied.

## 1. Hosted state of the project repository (public, anonymous; distinct evidence activity)

Source: public REST endpoints and pages of `github.com/mmontielpz/ai-sdlc-lite` (`gh_*`, `gh2_*`, `gh_html_*`).

| Item | Observation | Status |
|---|---|---|
| Accessibility | repository is **public** (visibility public, not archived, MIT licence, created 2026-11-12, last push 2026-11-21, 0 forks, 0 stars, no topics) | OBSERVED |
| Default branch | `master` | OBSERVED |
| Branch tips | `develop` = `329c4a0157a4b3a508b7096bc7775c796c849e3a`; `master` = `7f925cd0c45b6501d743d09ebd8c9569edced40e`; no other branch | OBSERVED |
| Relation to local refs | both equal the local `refs/remotes/origin/develop` and `master` values: no drift since the last local fetch. Local `develop` is **12 commits ahead** (unpublished). Public `develop` is 72 commits ahead of `master` (the audit's 78 = 72 + 6 unpublished) | OBSERVED |
| Branch protection | both branches report `protected: true` with required status check `ci-gate` (GitHub Actions app), enforcement level `non_admins` (administrators are not bound by this setting). Reviews, force-push, deletion, signed commits, linear history, conversation rules: detail endpoint needs authentication (401) | partly OBSERVED; rest UNKNOWN |
| Rulesets | public ruleset list is empty | OBSERVED (empty list) |
| CI | one workflow (`CI`, active); tip of `develop` shows check runs `ci-gate` and `deterministic (3.14)` both success; 90 runs recorded; sampled latest runs: push success, a PR run failure then success | OBSERVED |
| Pull-request practice | PRs #31 to #35 (closed, base `develop`, 2026-11-21); 5 listed | OBSERVED |
| Contribution and security files | `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `README.md` present; no code of conduct, no issue or PR templates (community health 71 %); `SECURITY.md` rendered on the public security-policy page | OBSERVED |
| Tags, releases | none (empty lists) | OBSERVED |
| Private vulnerability reporting | anonymous view cannot show it (the advisory form redirects to sign-in). `SECURITY.md` records an authenticated observation of 2026-11-12 (HISTORICALLY_REPORTED) | UNKNOWN anonymously |
| Actions permissions, secret scanning, push protection, Dependabot, required reviews, admin bypass rules, signing | not publicly observable | UNKNOWN |

**Finding H-1 (material).** The project is already **public**, with history up to `329c4a0`. A local, names-only and counts-only check of that commit finds account-specific home paths in 8 historical task records (`tasks/*/RESULT.md`, 9 occurrences), and commit metadata at both public tips contains at least one non-noreply address (counts only). Audit finding DA-D08-05 therefore concerns content that is **already published**; "public distribution not authorized" describes releases, packages and further publication, not source visibility. Owner decisions of 2026-11-27 (register OD-23): current visibility is intended and maintained conditionally, history is handled forward-only, no rewrite or force-push is authorized, and existing exposure does not authorize additional disclosure.

### 1a. Authenticated addendum (2026-11-27, owner-side, read-only; `gh` session, GET only, no token read)
| Item | Observation | Status |
|---|---|---|
| Protection on `develop` and `master` | classic protection: pull request required with 0 approving reviews; required check `ci-gate`, strict; **administrators not enforced**; force-push, deletion, signed commits, linear history, conversation resolution not required; no push restrictions; no rulesets | OBSERVED |
| Merge methods | merge commit, squash and rebase all allowed; auto-merge and delete-branch-on-merge off | OBSERVED |
| Actions | all actions allowed; SHA pinning not required; default token read-only; workflows cannot approve PRs; no environments | OBSERVED |
| Security features | secret scanning, push protection, Dependabot security updates and vulnerability alerts **disabled** | OBSERVED |
| Private vulnerability reporting | **enabled** (confirms the dated `SECURITY.md` statement) | OBSERVED |
| Immutable releases | the setting exists and is **disabled**; no tags or releases | OBSERVED |
| Plan tier, tag-protection rules, webhooks, deploy keys, Actions secrets, code scanning, pending reports | not inspected or not available | UNKNOWN |

## 2. Reference findings by dimension

Disposition column is from 02. Applicability to AI-SDLC Lite (ASL) is INTERPRETATION.

### EB-01 Repository governance
| Source | Observed practice | Applicability and limits |
|---|---|---|
| GitHub docs `[gh_doc_protected]` | branch-protection restrictions do **not** apply to administrators by default unless "do not allow bypassing" is set; required status checks must succeed, skipped or neutral; job names must be unique across workflows; one rule per branch | the `non_admins` observation in §1 means the sole maintainer can bypass; matters for a one-maintainer repo |
| GitHub docs `[gh_doc_rulesets]` | rulesets are viewable by anyone with read access; multiple can layer; bypass is an explicit list; available for public repositories on the free plan; also cover tags | enables a verifiable, public control; rule coverage depends on plan features (UNKNOWN for this account) |
| GitHub docs `[gh_doc_codeowners]` | CODEOWNERS requests reviews and can be required by protection | adds nothing with one maintainer |
| OpenSSF Scorecard `[sc_checks]` | Branch-Protection and Code-Review checks; several settings are readable only with an admin token | explains why anonymous evidence stays UNKNOWN; usable as a checklist |
| pytest `[pt_contrib]`, `[pt_releasing]` | PR-based workflow; release prepared by a manually triggered workflow that opens a release PR | PR-gated releases fit a small project |
| Spec Kit `[sk_contrib]`, BMAD `[bm_contrib]` | contributions announced via issues or chat first for larger changes; Spec Kit links a code of conduct | cheap norm; BMAD relies on chat, not a repository record |
| GitHub docs `[gh_doc_templates]` | issue and PR templates are repository files | one PR template can carry task id, gate and evidence links |

### EB-02 Agent engineering
| Source | Observed practice | Applicability and limits |
|---|---|---|
| Claude Code docs `[cc_doc_memory]` | `CLAUDE.md` is context, not enforced configuration; hooks are named as the enforcing route; target under 200 lines; imports with `@path` (depth 4). `AGENTS.md` is read **only when no `CLAUDE.md` exists** in or above the working directory (v2.1.277 or later); with both, only `CLAUDE.md` is read unless it imports `AGENTS.md` | direct input to DA-D04-02: consumer repos with a `CLAUDE.md` would not load `AGENTS.md` by default. ASL's smoke used 2.1.329 (later than 2.1.277) |
| Claude Code docs `[cc_doc_skills]` | skills live in `.claude/skills/<name>/SKILL.md` (project), personal, nested and enterprise locations; project skills load from the start directory up to the repository root; description is the trigger text | the installer's `claude-code` target matches; the `agents` target (`.agents/skills`) is not a documented Claude Code location in this source (INTERPRETATION) |
| Codex docs `[cx_doc_agentsmd]`, `[cx_doc_skills]` | instruction chain is root-to-cwd concatenation with later files overriding, 32 KiB default cap; skills use progressive disclosure (name and description first, body on use) with a startup description budget; `.agents/skills` mentioned | confirms progressive disclosure as common practice; byte caps argue for small entry files |
| Claude Code docs `[cc_doc_permissions2]` | rule order is deny, then ask, then allow; first match wins; permission modes include bypass | approval controls are agent-side; ASL's gates remain procedural, not enforced by the agent |
| Claude Code docs `[cc_doc_sandbox]` | on Linux and WSL2 the sandbox needs `bubblewrap` and `socat`; OS-level filesystem isolation | relevant to M-06 prerequisites; a preventive control ASL lacks (DEFER) |
| Spec Kit `[sk_readme]`, OpenSpec `[os_readme]`, BMAD `[bm_readme]` | per-agent integrations; Spec Kit needs Python 3.11+ and `uv`; BMAD needs Node 20.12+ and Python 3.10+; OpenSpec ships as an npm package | none of these is a stdlib-only Python 3.9 tool; a positioning contrast, not evidence of better results |

### EB-03 Methodology and lifecycle
Spec Kit `[sk_spec_driven]` argues that specifications should drive code; BMAD `[bm_readme]` offers role personas and staged workflows; OpenSpec `[os_readme]` describes a spec-first change flow (README read only). OBSERVED: these are claims by their authors about their own methods. No outcome data was found in the files read. ASL's differentiator (post-execution deterministic verification and two human gates) was not found in these READMEs (INTERPRETATION: BOV is complementary to spec-first approaches; their artifacts could be task inputs).

### EB-04 Security and trust
| Source | Observed practice | Applicability and limits |
|---|---|---|
| uv `[uv_security]` | policy lists behaviours that are **not** vulnerabilities by design (it can run arbitrary code through builds) | model for stating ASL's known limits (untracked-file reading, post-execution detection) |
| GitHub docs `[gh_doc_secpolicy]`, `[gh_doc_pvr]` | `SECURITY.md` plus an owner-enabled private reporting feature shows a "Report a vulnerability" button | enablement is a repository setting only the owner can confirm |
| GitHub docs `[gh_doc_hardening]` | least-privilege `GITHUB_TOKEN`; caution with `pull_request_target` and `workflow_run` | ASL's `ci.yml` already sets read-only contents permission and pinned actions (internal file) |
| OpenSSF Scorecard `[sc_checks]` | Token-Permissions, Pinned-Dependencies, Signed-Releases, Security-Policy, Code-Review checks | ready-made, executable rubric; running it is a later, separately authorized step |
| NeMo Guardrails `[ng_security]` | security reports go to a vendor channel, "not through GitHub" | corporate model; not applicable to a one-maintainer repository |
| No source found | practice for reading or hashing untracked content in a verifier | DA-D08-01 gets **no external answer** from this research |

### EB-05 Developer experience
Spec Kit installs with `uv` and `specify init` `[sk_readme]`; BMAD with `npx` `[bm_readme]`; Claude Code documents sandbox prerequisites for Linux and WSL2 `[cc_doc_sandbox]`. No time-to-first-task data was published in the sources read. INTERPRETATION: a stdlib-only, offline wheel install is a real simplicity advantage; time to first verified task must be measured by ASL itself.

### EB-06 CI/CD and release engineering
| Source | Observed practice | Applicability and limits |
|---|---|---|
| Spec Kit `[sk_release]` | release workflow runs on a tag push and rejects a tag that is not `vX.Y.Z` | small and enforceable; fits ASL's planned tag path |
| uv `[uv_release]`, `[uv_versioning]` | top-level `permissions: {}` with job-level grants; a protected environment gates publishing and dry runs use real signing keys; custom versioning (minor bumps mark breaking changes) | the permission pattern is cheap to adopt; environment approval and signing keys are heavier |
| pytest `[pt_backcompat]`, `[pt_releasing]` | written deprecation and backward-compatibility policy; releases via a workflow-created release PR | a policy statement costs one page |
| SemVer `[semver]`, Keep a Changelog `[kac_web]` | `0.y.z` means initial development; pre-release labels; changelog sections Added, Changed, Deprecated, Removed, Fixed, Security | ASL's `2.0.0.dev1` is a PEP 440 string; its mapping to SemVer is not covered by these sources (UNKNOWN) |
| SLSA `[slsa_levels_web]`, GitHub docs `[gh_doc_attest]`, `[gh_doc_immutable]` | Build L1 asks for provenance; L2 a hosted build platform that signs it; GitHub generates attestations from a workflow with extra token permissions; "immutable releases" lock assets and the tag | attestations are native to the host; a level may be claimed only after verification |
| OpenSSF Best Practices `[bp_criteria]` | passing criteria include unique versions, release notes and a documented vulnerability route | use as a checklist; the badge itself is optional |

### EB-07 Research and reproducibility
No external benchmark protocol, native-control design or pre-registration guidance was found in the files read (Spec Kit, OpenSpec, BMAD, NeMo READMEs and contribution files); NeMo's evaluation documentation was **not reviewed**. Unresolved: external methodology references for failure-inclusive reporting and multi-agent evaluation remain unsourced. ASL's own `BENCHMARK_PROTOCOL.md` stays the authority.

### EB-08 Documentation and adoption
Spec Kit's README opens with a task-to-page table `[sk_readme]`; BMAD pairs install steps with a discussion channel `[bm_readme]`; OpenSSF criteria require contribution and feedback routes `[bp_criteria]`. INTERPRETATION: an intent-based front page is the transferable pattern (M-08); community channels beyond GitHub are not needed at this size.

## 3. Unresolved questions
1. Resolved by the authenticated addendum (section 1a): reviews, administrator bypass, private reporting, Actions permissions, secret scanning. Still UNKNOWN: plan tier, tag protection, what a branch rename does to hosted settings.
2. Whether `claude-code` skill discovery honours `.agents/skills` is not stated in the source read; M-07 must observe it.
3. NeMo evaluation material and the uv platform policy were not reviewed; seven requests returned 404 (section 4).

## 4. Source acquisition reconciliation (correction recorded 2026-11-27)
`SOURCE_MANIFEST.tsv` (copied byte-identically from the original package) has 91 data rows, 1 header line and 18 comment or blank lines. Data rows by HTTP status: **81 x 200, 7 x 404, 3 x 401** (91 requests; the earlier summary wrongly called all 91 "retrieved items" and listed five 404s). The 17 comment lines are notes, not source records. The 404s are `cx_agents`, `ng_sec_guide`, `slsa_levels`, `kac` (two attempts), `os_agents` and `slsa_levels2`; the three 401s are the intentionally anonymous branch-protection endpoints.
Limitation: the identifier `gh2_commits_329c4a0157a4b3a508b7096bc7775c79` names two different URLs (check-runs and status). The first retained snapshot was overwritten by the second, so that row's recorded hash does not match the retained bytes. Both were fetched again under distinct identifiers (`gh2_checkruns_develop_tip`, `gh2_status_develop_tip`); those later re-fetches are separate from the original retrieval and the original hash is not replaced. Snapshot hashes identify the bytes read; they do not authenticate the claims, and the retained snapshots were not independently reproduced.
