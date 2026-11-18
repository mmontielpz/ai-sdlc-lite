> **Product-planning artifact (PB-003), stored 2026-11-18.** Owner-approved inputs are limited to: Claude Code as the only targeted provider for V1–V3 (amends D6); preserve existing adapters; project configuration under `.ai-sdlc-lite/`; the Product Baseline track is additive and supersedes no historical decision; G1–G10 and D1–D14 intact; Godot/FOB/Studio off the V1 critical path; Linux first; planning artifacts under `docs/product/`. **Everything else in this document is a proposal, not an approved decision**, and nothing here is a capability unless stated as existing. Content below is the original text, with one local-environment reference generalized; see [README](README.md).

> **Implemented by mission AI-SDLC-LITE-R0-TRUTH-RESET-001 (PR targeting `develop`); this brief's SHA-256 (original text, before this banner) began `027c124e4b5bf287`.**

# R0_IMPLEMENTATION_BRIEF — Truth reset and decision record (PROPOSED task contract; NOT approved; nothing executed)

Per AGENTS.md this brief is the **Bound** step. Blank fields grant no authority. Implementation starts only after the owner approves **this revision** (identify it by the SHA-256 of this file) and the plan below.

- **Task id:** AI-SDLC-LITE-PB-R0 · **Baseline:** develop @ 6430dca (re-confirm at start; stop if changed) · **Branch/worktree:** new `feat/pb-r0-truth-reset` worktree from `origin/develop`; never the primary checkout.
- **Mode:** documentation-only. No code, no tests added, no metadata (pyproject) edits, no schema/contract changes, no adapter changes, no behaviour change.

## 1. Objective
Make the repository's own documents say the same true thing, and record owner decisions OD-01…OD-05 (including the D6 amendment) without deleting history: Claude Code is the only targeted provider; existing adapters and historical evidence stay, labelled "not verified (not in committed scope)"; no gate is changed.

## 2. Pre-conditions (owner)
1. Approve R0 scope/revision (Gate 1).
2. Confirm the D6 amendment wording (OWNER_DECISION_AMENDMENTS §2) may be written into ROADMAP.
3. Confirm "PB track" is added as an **additive banner**, not a supersession of the owner-approved sequence (PB-01).
4. Decide whether the planning artifacts (PB-001/002/003 documents) are committed in this PR under `docs/product/` (recommended) or stay external (P-7). If not approved, R0 omits them.

## 3. Scope (files; edits are additive or corrective, never deletions of dated evidence)
| File | Change |
|---|---|
| `README.md` | (a) status line: remove the stale "68 tests" and the "23 project files / 34 files" paragraph; point to CI for test status; (b) add one paragraph "Strategy: Claude Code first; agent-neutral core; other agents not verified (not in committed scope)"; (c) make the primary onboarding the `python3 -m ai_sdlc` path (D1), keep Copilot sections intact but relabelled "Copilot (historical evidence; not in committed scope)"; (d) state tested platform/Python: Linux, 3.9 and 3.14 in CI; macOS/Windows not verified; (e) no "universal/supports" claims; (f) `master` raw-URL install line: **do not change the URL** (branch policy RG-1 unresolved); add a dated note that `master` trails `develop` |
| `ROADMAP.md` | banner at top (additive): PB track + link to the decision record; D6 row annotated "**Amended 2026-11-18 by owner decision OD-01**" with the amended text (original text kept); CODEX-003/004 annotated "not committed (OD-01)"; GQ-RUNTIME annotated "dependency on CODEX-004 unresolved — owner decision pending"; DX-002/003 and the first DX-005 component marked **implemented** where code exists (no completion claims for the rest); D2 note "directory `.ai-sdlc-lite/` per OD-04 (confirmation pending)"; "Universal V1.0" headings annotated; **no renumbering, no gate edits** |
| `ARCHITECTURE.md` | agent-adapter row and Layering rule annotated for Claude-first (adapter data + one target mapping; core provider-neutral); `.ai-sdlc/` → `.ai-sdlc-lite/` annotation (pending confirmation); "Universal Skill" wording annotated |
| `DX_ARCHITECTURE.md` | status note: DX-002/003 and first DX-005 component implemented; Codex-specific proposals not committed (OD-01) |
| `QUALIFICATION_MATRIX.md` | add a dated note (do **not** edit past rows; rule 1): Claude Code is the only targeted agent; others "not verified (not in committed scope)"; clarify README's owner-observed Copilot run vs matrix smoke NOT RUN; add observed fact "Claude Code 2.1.327 present on the author's host, read-only `--version`, no smoke run" |
| `docs/DELIVERY_EXECUTOR.md` | fix "There is no execution CLI" (`delivery execute` exists; see CLI help); no behaviour description beyond what `--help`/existing docs state |
| `CHANGELOG.md` | one entry under Unreleased |
| `docs/product/*` (optional, pre-condition 4) | the planning artifacts, verbatim, with a banner "PROPOSED — not approved unless stated" |
**Not touched:** any `.py`, tests, `pyproject.toml`, schemas, adapters/*, golden files, RESULT_CONTRACT.md, SECURITY.md, QUALIFICATION.md, CI workflow, G1–G10 text, task evidence directories.

## 4. Steps
1. Re-confirm baseline and clean state; create the worktree; record SHA.
2. Make the edits above; one focused commit (commit and push authorized separately).
3. Run the verification commands (§5); fix only R0-caused failures.
4. Inspect the full diff for scope (only listed files), no secrets, no generated artifacts.
5. Report; stop for review. Commit/push/PR only with explicit authorization.

## 5. Verification (exact commands; Linux, Python 3.14, fake HOME; plus CI 3.9/3.14 after push)
```
cd <worktree> && git status --short && git diff --stat            # only §3 files
PYTHONDONTWRITEBYTECODE=1 HOME=<tmp> python3 -m unittest discover -s tests   # exit 0; count recorded
python3 -B -m ai_sdlc --help ; python3 -B -m ai_sdlc doctor               # exit 0 / READY, unchanged
grep -n "68 tests\|23 project files\|no execution CLI" README.md docs/DELIVERY_EXECUTOR.md   # no matches
```
Expected: same test count as develop (548 at 6430dca), exit 0. Note: README/ARCHITECTURE/ROADMAP/DX docs are inside the installer's link-closure bundle; if a test pins bundle contents or hashes it must pass unchanged or the failing assumption is reported (do not weaken tests).

## 6. Acceptance criteria
1. Only the listed files changed; no code/metadata/schema/adapter/test changes.
2. No doc contradicts `--help`, the observed suite, or the matrix; the three stale statements are gone.
3. D6 amendment recorded verbatim-compatible with OWNER_DECISION_AMENDMENTS §2; original D6 text preserved.
4. G1–G10 text byte-identical (verify with `git diff` showing no hunk in the gate table).
5. Past qualification rows and task evidence untouched; additions dated.
6. No new claim of support/qualification/independence; macOS/Windows/other agents stated "not verified".
7. Full suite exit 0 with unchanged count; CI 3.9, 3.14 and ci-gate pass on the final commit (after authorized push).
8. Every decision not given in OD-01…05 is labelled "pending owner decision".

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Doc edits change installer bundle bytes and break pinned tests | run full suite first on the baseline, then after; report any failing assertion |
| Over-claiming (writing proposals as decisions) | only OD-01…05 appear as decisions; everything else "proposed/pending" |
| Rewriting history in ROADMAP | annotate, never delete; no renumbering |
| README install URL mismatch (`master`) | leave the URL; add a dated note; branch policy is RG-1 |
| Scope creep into pyproject/code | explicitly excluded; list in the PR |
| Same-assistant authorship | independent human review before merge |

## 8. Out of scope / stop conditions
Stop and report if: baseline changed; a listed file has uncommitted or unexpected changes; a test fails because of a doc change that cannot be fixed within the listed files; the owner has not confirmed the D6 wording; any edit would require touching a gate, schema or code. No push, merge, tag, release, dependency, paid agent run or global-config change is authorized by this brief.

## 9. Evidence to record (RESULT.md in the worktree or external)
Commands, cwd, environment, exit codes, test counts (local vs CI separate), diff stat, list of statements changed with before/after, open decisions list, limitations; human acceptance PENDING.

## 10. Estimated effort
5–9 engineer-hours (judgment; low confidence).

## 11. Approval request
Owner to state, identifying this brief by its SHA-256: approve / change scope; confirm pre-conditions 2–4. **No work starts until then.**
