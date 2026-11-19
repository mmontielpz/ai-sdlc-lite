# Changelog

This file records notable project changes. Entries under Unreleased are not released functionality.

## Unreleased

- Distribution (AI-SDLC-LITE-DISTRIBUTION-058, resolves finding B-1; no schema, trust or verifier change): the supported CLI is distributed as the existing `ai-sdlc-lite` wheel (offline, no dependencies, Python 3.9+) and the Skill instructs agents to use `ai-sdlc doctor`, to stop and tell the human (with the offline install command inline, because QUICKSTART is not in the bundle) when the command is missing, and never to install packages. Fixes a packaging defect: the wheel omitted `docs/product/*.md`, so `ai-sdlc init` from an installed wheel failed with `validation_or_io_failure`. Adds `ai-sdlc --version`, a SKILL.md "Command-line tool" section (the bundled Skill hash changes accordingly, so `init --check` of older installations reports a difference and they must be re-applied), a QUICKSTART offline wheel install section, and tests that check the packaged files against the Skill bundle's link closure and install a built wheel without the checkout.
- Experience System V1, increment EXP-01B (AI-SDLC-LITE-EXP-01B-001 r1; EXPERIMENTAL, outside the release gates, no qualification claim): opt-in local capture on top of EXP-01A. Adds `ai-sdlc experience record` (four closed-vocabulary operator/human-reported event types, T0), `ai-sdlc experience record-verify --report FILE` (one `verify.completed` event from a `verify --out` report: strict bounded read, trust-preserving facet mapping, sorted unique failure codes, only `report_sha256` stored, new stable code `report_invalid`), and `init --apply|--check --journal FILE --repo-classification C [--run-id R] [--allow-in-repo]` (one `install.completed`/`install.failed` event after the result is final; `init`'s stdout, exit code and other stderr are unchanged, a journal failure adds exactly one `JOURNAL: <code>` stderr line; `init` without `--journal` imports no Experience module). Explicit journal path only, no default location, no free text, no path data, no `H` events, no network or subprocess; schema `/1`, event IDs, the verifier, the Skill, the installer and the CI workflow are unchanged. Documented limitations: early-BLOCKED reports, agent-claimed PARTIAL/BLOCKED without failure reasons, task IDs outside the event pattern and non-ASCII report text are refused as `report_invalid`; journal failures during `init` are silent to scripts (strict mode deferred). Contract: `docs/EXPERIENCE_CONTRACT.md`.
- Experience System V1, increment EXP-01A (AI-SDLC-LITE-EXP-01A-001; EXPERIMENTAL, outside the release gates, no qualification claim): add the closed `ai-sdlc-experience-event/1` schema and validator (`ai_sdlc/experience_events.py`), a local append-only JSONL journal with locked, fully-validated, fail-closed appends and a 4 MiB / 5,000-event cap (`ai_sdlc/experience_journal.py`), and `ai-sdlc experience validate --journal FILE` (read-only). Offline, stdlib only, explicit journal path (refused inside a Git work tree by default), no content/path/free-text capture, T3 unrepresentable and human `H` events disabled. No capture commands, export, import or analysis yet (EXP-01B and later). The verifier, the Skill, existing schemas, exit codes and outputs are unchanged apart from one added usage line. Review corrections: identifier and digest fields are now matched as whole strings (a trailing newline was previously accepted); appends re-check that the locked file is still the one the path names, never remove a journal another writer holds, read the clock once, and map OS errors to `journal_io`. Contract: `docs/EXPERIENCE_CONTRACT.md`. Remediation (PR #27 review): `validate` no longer blocks on a FIFO (non-blocking open, then regular-file check); invalid injected clock values are refused as `schema_invalid` before any path or run_id derivation; the documentation-only schema now carries the `revision`/`task_revision` patterns; the failed-rollback limitation is documented.
- Claude-only task initialization (AI-SDLC-LITE-F1-CLAUDE-TASK-INIT-001): `install_skill.py --init-task` now resolves the installed Skill among the fixed destinations (`.agents/skills/ai-sdlc-lite/`, `.claude/skills/ai-sdlc-lite/`), requires every present destination to be an intact manifest-owned install, prefers the legacy target when both are intact, and fails closed when none is, or any present one is partial, edited or symlinked. Fixes the Claude Code target being rejected (found in E2E-SMOKE-001). Re-running over an existing matching task context also requires intact installations (no repair, no writes on refusal), and `preflight` now reports per-target SKILL.md existence only (PRESENT/ABSENT, integrity not validated). No change to task approval, schemas, the verifier or evidence levels.
- Claude Code install target (AI-SDLC-LITE-C2-CLAUDE-INSTALL-TARGET-001): add `init --target claude-code`, installing the same offline Skill bundle under `.claude/skills/ai-sdlc-lite/`, based on a bounded runtime observation that Claude Code 2.1.327 lists `.claude/skills/` Skills and not `.agents/skills/` ones. The default target remains `.agents/skills/ai-sdlc-lite/`; `scripts/install_skill.py --uninstall --skill-target claude-code` removes the new target; no `CLAUDE.md` is written; schemas, manifest format, verifier and exit codes are unchanged. The Claude Code adapter declaration records the observed version and discovery. No qualification is claimed.
- Documentation truth reset (AI-SDLC-LITE-R0-TRUTH-RESET-001): record the Product Baseline track and owner decisions of 2026-11-18 (Claude Code only provider for V1–V3, D6 amendment, `.ai-sdlc-lite/` directory, Linux first); correct stale README counts and install wording, the delivery executor CLI statement and DX status; add dated qualification notes; add `docs/product/`. Documentation only: no code, schema, adapter, test or gate change.
- Dirty baseline: baseline records add optional `baseline_dirty_state` (Git index entry and working-tree kind per dirty path). With `--baseline-record`, a pre-existing dirty file that is unchanged in content, index entry, executable bit and symlink target is preserved (`PARTIAL`, not `BLOCKED`) when outside `allowed_paths`; any change, unmerged state, missing/malformed state or protected path fails closed. Records without the field behave as before; the baseline schema stays `/1` (AI-SDLC-LITE-G2-DIRTY-BASELINE-004).
- Verify summary: add `Scope verification`, `Agent-reported checks` and `Independently executed checks` lines so a PASS is not read as proof that checks ran or passed. Presentation only; JSON output, statuses, exit codes and the trust model are unchanged (AI-SDLC-LITE-G2-TRUST-SEMANTICS-001).

### V1 release candidate preparation — AI-SDLC-LITE-008A

This is candidate documentation, not a published version or release date. Human release acceptance is PENDING; release readiness is BLOCKED until a working private reporting route is verified. The checkout has NO COMMIT and no version tag.

- Add QUALIFICATION.md with portable historical results, immutable hashes, owner approval references, the harness scope incident and controlled recovery, and the exact intended public inventory.
- Update onboarding and inventory for WORKFLOW.md and the optional Skill. Explicit Codex Skill invocation was demonstrated; automatic discovery and Copilot CLI remain unverified.
- Sanitize the authorized UX-002 historical staging record while retaining original snapshot hashes and results. Canonical contracts, installed Skill, example source/tests, and SMALL-FIX-001 historical evidence remain unchanged.
- Define conditional GitHub private reporting and a supported-version policy without claiming that reporting is enabled. No service configuration is changed.
- Reuse historical tests; candidate validation covers document links, scope, protected hashes, sensitive patterns, evidence completeness, and diffs. No productivity, token-saving, or cost improvement is established.

### Added

- Foundation overview: Bound → Observe → Verify, six lifecycle concepts, two human approval gates, and an adoption walkthrough.
- Consistent outcome definitions and separate reporting of tokens, billed units, elapsed time, and monetary cost.
- MIT license for original project material, contribution guidance, security disclosure limitations, and versioning policy.
- Four operating contracts and a small standard-library Python example with immutable tests.
- Outcome-first · Time-conscious · Token-aware product direction and an evidence record for SMALL-FIX-001.

### Corrected

- SMALL-FIX-001 normalization: trims surrounding whitespace and lowercases while preserving internal whitespace; five existing tests passed in the recorded Codex run.
- Example instructions now distinguish the repaired state from an isolated replay of the original defective baseline. Historical start-to-verification time is distinct from unknown full delivery time.

### Pending

- Owner acceptance of the identified candidate, a verified working private reporting route, and an authorized committed release snapshot before V1.0.0. Beginner usability, workshop use, and overhead remain unverified and require an explicit owner decision on release scope. Token measurement is optional; no productivity or token savings are established.
- Phase 05 — Codex Audit & Qualification is the mandatory gate before Phase 06 — Copilot CLI Compatibility. Explicit Codex Skill invocation is demonstrated; automatic startup discovery remains unverified (historically PARTIAL). Phase 06 remains unverified and requires explicit owner authorization.

## Versioning policy

The target first stable release is `1.0.0`; no release or version tag exists yet. Use `0.x.y` for any published development versions and label pre-release versions explicitly, such as `1.0.0-rc.1`.

From `1.0.0`, use `MAJOR.MINOR.PATCH`:

- **MAJOR:** incompatible changes to required task/result fields, approval rules, outcome meanings, or adoption steps.
- **MINOR:** backward-compatible additions, including optional guidance or examples.
- **PATCH:** corrections and clarifications that preserve the documented contracts.

The public contract is the documented workflow and required template fields once released. Agent product behavior is outside that contract. Maintainers review compatibility impact before release, move completed entries into a dated version section, and keep planned work under Unreleased. Publishing and tagging require explicit owner authorization.
