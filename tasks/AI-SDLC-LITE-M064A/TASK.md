# Task contract: M064-A, W01 personal website pilot preparation

## Plan — Bound

- **Task ID / revision:** AI-SDLC-LITE-M064A, r1 (draft for Gate 2).
- **Authority:** preparation approved by OD-28 and the M01-CLOSE-AND-PILOT-READY Gate 1, 2026-11-27. Accepting this document does **not** authorize W01 execution, live provider runs, RG-6 spending, dependency installation or deployment.
- **Objective:** define the first end-to-end pilot, `W01`, a static personal website, with criteria and measurements fixed before execution.
- **W02 (unchanged, after W01):** the official website of the AI-SDLC Lite methodology and framework ecosystem (OD-32). It is not part of this pilot.

## W01 scope (proposed minimum)

| In scope | Out of scope |
|---|---|
| Static pages: home, about, projects, contact link | Server code, databases, accounts, forms that collect data |
| Responsive layout, basic metadata, a documented local build | Analytics, cookies, advertising, third-party trackers |
| Content from an owner-approved content list | Unapproved personal data, private project content |
| README for the pilot repository | Paid services, domain or DNS changes, deployment or publication (separately authorized) |

Task slices, each with its own bounded contract: S1 greenfield scaffold; S2 one incremental change; S3 one defect fix or refactoring. If no real defect exists, S3 is a refactoring; do not plant one and report it as organic.

## Acceptance criteria

Product (checked per slice where applicable; tools and versions are pinned at preflight):

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
- Escaped defects are those found after acceptance, within a window the owner declares before the first slice (proposed: 14 days).
- Tokens and cost only as the provider reports them. Active time only where observed.

## Ubuntu 24.04 preflight (planned; NOT RUN)

Run on the owner-designated Ubuntu 24.04 environment before Gate 1 of the first slice. Any missing prerequisite stops the preflight; installing it needs authorization.

| Step | Command or action | Expected |
|---|---|---|
| P1 | `grep -e '^ID=' -e '^VERSION_ID=' /etc/os-release` | `ubuntu`, `24.04` |
| P2 | `python3 --version`; `git --version`; `python3 -c 'import setuptools'` | Python 3.9 or later; exit 0 |
| P3 | `claude --version` | exact version recorded |
| P4 | at the pinned commit: `python3 -m pip wheel --no-build-isolation --no-deps -w dist .`; `sha256sum dist/*.whl` | wheel built, digest recorded |
| P5 | in a new virtual environment: `pip install --no-index --no-deps <wheel>`; `ai-sdlc --version`; `ai-sdlc doctor` | version and doctor output recorded |
| P6 | in the pilot repository: `ai-sdlc init --repo <repo> --target claude-code`, then `--apply` and `--check` after approval; review and commit the installed files | preview matches; check passes |
| P7 | `git -C <repo> status --porcelain --untracked-files=all`, reviewed before any baseline (see `SECURITY.md`) | no sensitive files |
| P8 | `ai-sdlc baseline --repo <repo> --out <outside-repo>/baseline.json` | exit 0; record held as evidence |
| P9 | confirm the recorded RG-6 authorization and budget | present before any live run |

P1 to P8 request no model inference. A passing preflight is an observation, not agent or platform qualification.

## Stop conditions

Stop for scope growth, missing authorization or budget, sensitive data in the workspace, a version or digest mismatch, or verification that cannot be completed within the approved plan.

## Owner decisions required before W01

1. Pilot repository (D11 candidate selection) and approved content list.
2. Ubuntu 24.04 environment and the exact Claude Code version.
3. RG-6 live-run authorization and budget.
4. Validator, link and accessibility tools, and any dependency installation.
5. Escaped-defect window; hosting and deployment, if wanted at all.
6. Restricted-storage locations for pilot evidence (OD-29).
