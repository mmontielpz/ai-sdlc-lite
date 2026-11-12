# Task contract

Template: replace placeholders for one task. A blank approval is pending. An existing approved brief may be referenced instead of duplicating it. Preserve completed records before reuse.

## Plan — Bound

- **Task ID:** <unique ID>
- **Task revision:** <revision label; increment when the contract changes>
- **Repository and baseline:** <repository; commit SHA, or NO COMMIT for a new repository; existing changes>
- **Objective:** <problem and desired behavior>
- **In scope:** <allowed files or areas and changes>
- **Out of scope:** <excluded work>
- **Constraints:** <dependencies, environment, data, time, and prohibited actions>

## Design — Bound

- **Inspection findings:** <applicable instructions, relevant behavior, baseline checks, and unknowns>
- **Approach and risks:** <smallest useful change, affected files, trade-offs>
- **Implementation plan:** <ordered steps, including verification>
- **Stop conditions:** stop for scope growth or material approach changes and obtain renewed approval. Also stop for <task-specific conflicts, unexpected state, or obstacles to verification>.

## Test — Verify

Criteria must be observable. Add rows as needed. Define checks before implementation; do not leave verification as “run tests.” Include human review where automation cannot establish a criterion.

| Criterion ID | Acceptance criterion | Verification ID |
| --- | --- | --- |
| AC-1 | <observable outcome> | V-1 |

| Verification ID | Working directory and prerequisites | Exact command or human review procedure | Expected result |
| --- | --- | --- | --- |
| V-1 | <directory, environment, required tools> | <literal command; or repeatable review steps> | <expected exit code and behavior> |

## Plan approval — human gate before Build

- **Decision:** PENDING
- **Approved task revision:** <revision covering the design, plan, criteria, and constraints>
- **Human / date / decision reference:** <name, timestamp with timezone, explicit approval reference>

Scope expansion or material approach changes require a revised task and renewed approval before affected implementation. Record other contract changes; do not silently weaken approved criteria.

## Deploy and Maintain

- **Release actions authorized:** NONE by default. If applicable, name the action, target, approved revision, human authorization reference, verification, and rollback plan.
- **Maintenance / follow-up:** <owner and follow-up expectations; or not applicable with reason>

Build and Test evidence, lifecycle status, and the separate human acceptance decision belong in [RESULT.md](RESULT.md). Use [CHECKLIST.md](CHECKLIST.md) at both gates.
