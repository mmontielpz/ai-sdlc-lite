# Task contract: M064-A, W01 personal website pilot preparation

## Plan — Bound

- **Task ID / revision:** AI-SDLC-LITE-M064A, r2 (brownfield revision, draft for Gate 2).
- **Authority:** preparation approved by OD-28 and the M01-CLOSE-AND-PILOT-READY Gate 1, 2026-11-27. Accepting this document does **not** authorize W01 execution, live provider runs, RG-6 spending, dependency installation or deployment.
- **Revision r2 (owner approval, 2026-11-27):** `W01` is a **brownfield** engineering pilot on an existing static website implementation. S1 changes from a greenfield scaffold to consolidation and characterization. Acceptance criteria, measurement fields, the research hypotheses and the qualification criteria are unchanged. `W01` is not greenfield evidence and alone meets neither `Q3` nor `G7`.
- **Objective:** define the first end-to-end pilot, `W01`, a static personal website, with criteria and measurements fixed before execution. The immediate product target is one functional version the owner can review visually before further design or architecture changes.
- **W02 (unchanged, after W01):** the official website of the AI-SDLC Lite methodology and framework ecosystem (OD-32). It is not part of this pilot.

## Baseline

| Item | Value |
|---|---|
| Pilot repository | a new private repository; the existing public website and its deployment stay untouched |
| Inputs | the `v2` directory at public commit `f58ebb2` of the existing site repository, and recovered local source not present in that history; both preserved as separate branches over their common ancestor `7b53375` |
| Architecture | existing Next.js, React, TypeScript static export with its dependency lockfile; changed only for a demonstrated blocker |
| Visual identity | preserved; no redesign |
| Excluded | local working materials, manuscript files, credentials, unapproved research assets, dependency caches and build output |
| Learning portal | source and reusable components preserved; not required in the first version; private lab links are not published; integration decided at visual review |

## W01 scope (proposed minimum)

| In scope | Out of scope |
|---|---|
| Static pages: home, work or projects, research, writing, about with experience, contact link; existing research pages kept subject to factual and asset-rights verification | Server code, databases, accounts, forms that collect data |
| Responsive layout, basic metadata, a documented local build | Analytics, cookies, advertising, third-party trackers |
| Content from an owner-approved content list | Unapproved personal data, private project content |
| README for the pilot repository | Paid services, domain or DNS changes, deployment or publication (separately authorized) |

Task slices, each with its own bounded contract:

- **S1, consolidate and characterize:** merge the two baseline inputs, resolve and record textual and behavioral conflicts, record existing behavior with checks before changing it, and make install, type check, lint, build and tests produce recorded results from a clean checkout. No new feature.
- **S2, complete:** supply approved professional content and the missing sections.
- **S3:** address a real defect, migrate existing published content, or perform a justified refactoring. Do not plant a defect and report it as organic.

Content follows a sourced-content rule: every factual statement traces to an owner-approved source or is visibly marked as a placeholder, with an automated check where practical; sections without approved content may be omitted.

## Acceptance criteria

Product (checked per slice where applicable; tools and versions are pinned at preflight: the existing lockfile for build and browser tests, plus a link checker, an HTML validator and an accessibility engine):

| ID | Criterion | Check |
|---|---|---|
| AC1 | Builds or serves from a clean checkout with the documented command | exit 0, recorded |
| AC2 | Every internal link and asset reference resolves | named link checker, exit 0 |
| AC3 | Pages pass the chosen HTML validity check | named validator, results recorded |
| AC4 | Accessibility check is run; every finding is fixed or accepted by the owner with a reason | named tool plus human review |
| AC5 | Layout is usable at 360 px and 1280 px widths | human review with screenshots |
| AC6 | Only approved content; no secrets or unapproved personal data; assets have recorded licences | scan plus human review |
| AC7 | Changes stay within the slice's allowed paths | `ai-sdlc verify` report and diff review |

Process: every attempt has a terminal status; both human gates are recorded against identified revisions; failures and deviations are retained; every measurement has a value or `UNKNOWN`. The pilot sets no performance target, supports no causal claim and alone meets neither `Q3` nor `G7`.

## Measurement sheet

One row per attempt, including failed, blocked, abandoned and rejected ones. Definitions of M1 to M5: `docs/research/BENCHMARK_PROTOCOL.md` section 5. Other fields follow the `RESULT.md` Observations rows.

```csv
attempt_id,slice,framework_commit,wheel_sha256,agent_version,model_id,gate1_time,terminal_time,terminal_status,m1_seconds,m2_corrective,governance_interventions,owner_prompts,approval_requests,preparation_only_rounds,m3_rework,m4_input_tokens,m4_output_tokens,m4_cache_tokens,m4_reported_cost,m5_instruction_conflicts,active_seconds,verify_outcome,accepted,escaped_defects,deviations,failures,scope_violations,evidence_id
```

- Governance overhead is reported as its parts (governance interventions, approval requests, preparation-only rounds, and time where observed); do not combine them into a score.
- Escaped defects are those found after acceptance, within a window the owner declares before the first slice (declared: 14 days from each slice's acceptance).
- Tokens and cost only as the provider reports them. Active time only where observed.

## Ubuntu 24.04 preflight (framework steps P4 to P9 NOT RUN)

Run in the owner-approved isolated Ubuntu 24.04 userland environment (a container on a different host kernel; record both). The site toolchain also needs Node and the browser used by the tests. Run before Gate 1 of the first slice. Any missing prerequisite stops the preflight; installing it needs authorization.

| Step | Command or action | Expected |
|---|---|---|
| P1 | `grep -e '^ID=' -e '^VERSION_ID=' /etc/os-release` | `ubuntu`, `24.04` |
| P2 | `python3 --version`; `git --version`; `python3 -c 'import setuptools'` | Python 3.9 or later; exit 0 |
| P3 | `claude --version` | exact version recorded |
| P4 | at the pinned commit: `python3 -m pip wheel --no-build-isolation --no-deps -w dist .`; `sha256sum dist/*.whl` | wheel built, digest recorded |
| P5 | in a new virtual environment: `pip install --no-index --no-deps <wheel>`; `ai-sdlc --version`; `ai-sdlc doctor` | version and doctor output recorded |
| P6 | only after the confidentiality remediation (OD-37) is merged, at a framework commit that includes it. In the pilot repository: `ai-sdlc init --repo <repo> --target claude-code`, then `--apply` and `--check` after approval; review and commit the installed files | preview matches; check passes |
| P7 | `git -C <repo> status --porcelain --untracked-files=all`, reviewed before any baseline (see `SECURITY.md`) | no sensitive files |
| P8 | `ai-sdlc baseline --repo <repo> --out <outside-repo>/baseline.json` | exit 0; record held as evidence |
| P9 | confirm the recorded RG-6 authorization and budget | present before any live run |

P1 to P8 request no model inference. A passing preflight is an observation, not agent or platform qualification.

## Stop conditions

Stop for scope growth, missing authorization or budget, sensitive data in the workspace, a version or digest mismatch, or verification that cannot be completed within the approved plan.

## Owner decisions required before W01

Decided 2026-11-27: pilot repository, baseline and brownfield classification, isolated Ubuntu 24.04 userland, minimum validation tools, 14-day window.

Open:

1. RG-6 live-run authorization and budget (**not authorized**).
2. Approved content list and verification of research claims and asset rights.
3. Learning portal integration, at visual review.
4. Hosting and deployment, if wanted at all.
5. Restricted-storage location for pilot evidence (OD-29).
