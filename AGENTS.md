# Agent operating contract

Use this process with one bounded task at a time. The human owns approvals; the agent owns accurate execution and reporting. See [README.md](README.md) for BOV (Bound → Observe → Verify), lifecycle concepts, and outcome definitions.

## Before implementation: Bound

1. Start with read-only inspection. Identify the repository root, baseline revision, existing changes, and applicable project and directory instructions. Preserve existing work. Report instruction conflicts rather than guessing which project rule to discard.
2. Read the active task contract, normally [TASK.md](TASK.md), and relevant files. For an existing project, integrate with its instructions rather than replacing them. For a new repository, record that no commit or checks exist yet.
3. Propose a design, small implementation steps, exact verification commands, expected outcomes, and risks. Agree on a repeatable check if none exists. Baseline checks must respect task constraints; report checks that cannot safely run.
4. Stop before implementation until explicit human approval identifies the task revision and plan. An explicit mission brief may serve as the active contract and approval; cite it in the result. Blank template fields grant no authority. Do not require the human to repeat authorization already covering the work.

## During work: Observe

- Stay within approved scope and constraints. Stop the affected work for scope growth, material approach changes, conflicting instructions, unexpected changes in files you need to edit, or a required action outside authorization. Explain the issue and request a revised decision; do not expand scope yourself.
- Stop when agreed verification cannot be completed or a failure cannot be resolved within the approved plan. Preserve the evidence and report the obstacle. Never weaken checks merely to obtain PASS.
- Do not push, merge, deploy, publish, tag, use paid services, add dependencies, or perform destructive operations without explicit authorization for that action. Technical PASS and human acceptance do not grant it.
- Record actual changes, check attempts, failures, and limitations in [RESULT.md](RESULT.md). Keep secrets and private transcripts out of evidence.

## Before handoff: Verify

- Run the agreed deterministic checks against the final changed state; record exact commands, working directory, environment, exit codes, and relevant output. Distinguish baseline, final, reused, and not-run checks. Recheck affected evidence after further changes.
- Map evidence to every acceptance criterion. Use PASS, PARTIAL, or BLOCKED as defined in README; use UNKNOWN for unavailable facts and measurements. Do not claim compatibility, visual correctness, or checks you did not exercise.
- Keep measured tokens, billed units, elapsed time, retries, and monetary cost separate using the result fields. Do not derive charges from token counts or fill missing data with zero.
- Inspect the final diff and repository status. Use [CHECKLIST.md](CHECKLIST.md) for handoff. Leave human acceptance pending until an explicit decision identifies the reviewed revision, and stop at the authorized boundary.
