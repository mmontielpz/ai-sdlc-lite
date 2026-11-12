# Human checkpoints

Use this checklist with the active [task contract](TASK.md) and [result record](RESULT.md). Checkmarks record review; they do not replace an explicit human decision.

## Before implementation — Bound

- [ ] Read-only inspection identifies existing instructions, baseline, existing changes, and relevant risks.
- [ ] Plan and Design define scope, exclusions, constraints, acceptance criteria, stop conditions, and exact verification commands or review steps.
- [ ] A human explicitly approves the identified task revision and plan. Any scope growth or material approach change has renewed approval before affected work.

## After verification — Observe and Verify

- [ ] Review the final diff and repository status; Build stayed within the approved boundaries and preserved unrelated work.
- [ ] Test evidence identifies the checked revision, commands, exit codes, and outcomes for every criterion; failures, skipped checks, and limitations remain visible.
- [ ] Measurements include sources and units; missing values are UNKNOWN. Tokens, billed units, elapsed time, retries, and cost remain separate.
- [ ] Technical outcome is PASS, PARTIAL, or BLOCKED under the [README definitions](README.md). PASS does not imply human acceptance.
- [ ] A human separately records acceptance or rejection of the identified reviewed revision; otherwise acceptance remains PENDING.
- [ ] Deploy has explicit authorization before any release action, or is recorded as not performed with a reason. Human acceptance alone does not authorize release.
- [ ] Maintain records remaining issues and the next action or a reason no follow-up is needed. Preserve the completed task and result before reuse.
