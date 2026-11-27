# Human checkpoints

Use this checklist with the active [task contract](TASK.md) and [result record](RESULT.md). Checkmarks record review; they do not replace an explicit human decision.

## Before implementation — Bound

- [ ] Read-only inspection identifies existing instructions, baseline, existing changes, and relevant risks.
- [ ] Plan and Design define scope, exclusions, constraints, acceptance criteria, stop conditions, and exact verification commands or review steps.
- [ ] The plan states which evidence dimensions apply and lists any checkpoint file that will be updated among the allowed paths.
- [ ] A human explicitly approves the identified task revision and plan. Any scope growth or material approach change has renewed approval before affected work.

## After verification — Observe and Verify

- [ ] Review the final diff and repository status; Build stayed within the approved boundaries and preserved unrelated work.
- [ ] Test evidence identifies the checked revision, commands, exit codes, and outcomes for every criterion; failures, skipped checks, and limitations remain visible.
- [ ] Each applicable evidence dimension has an outcome with its evidence and who ran it; NOT APPLICABLE dimensions state a reason. For pilot tasks, rework cycles, corrective and governance interventions and instruction conflicts are recorded, including for unsuccessful tasks.
- [ ] Measurements include sources and units; missing values are UNKNOWN. Tokens, billed units, elapsed time, retries, and cost remain separate.
- [ ] Technical outcome is PASS, PARTIAL, or BLOCKED under the [README definitions](README.md). PASS does not imply human acceptance.
- [ ] A human separately records acceptance or rejection of the identified reviewed revision; otherwise acceptance remains PENDING.
- [ ] Deploy has explicit authorization before any release action, or is recorded as not performed with a reason. Human acceptance alone does not authorize release.
- [ ] Maintain records remaining issues and the next action or a reason no follow-up is needed. Preserve the completed task and result before reuse.
- [ ] Closure (an operational postcondition, not a third gate): after integration, canonical remote synchronization is recorded, or a temporary exception states its reason and expiry. Work accepted locally but not synchronized is not remotely closed.
- [ ] Handoff check: verify local links, status vocabulary (`PASS`/`PARTIAL`/`BLOCKED`/`UNKNOWN`), open-gaps register, and whether commits are runtime-qualified or docs-only.
