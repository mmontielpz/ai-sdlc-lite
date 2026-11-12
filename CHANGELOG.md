# Changelog

This file records notable project changes. Entries under Unreleased are not released functionality.

## Unreleased

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
