---
name: ai-sdlc-lite
description: Guide a bounded AI-SDLC Lite task through its canonical repository contracts when the user requests this workflow.
---

# AI-SDLC Lite

Locate the target repository and read its applicable instructions. Read [WORKFLOW.md](../../../WORKFLOW.md) for navigation and [README.md](../../../README.md) for BOV and outcome definitions.

Use the active task and result paths named by the human. The canonical [AGENTS.md](../../../AGENTS.md), [TASK.md](../../../TASK.md), [CHECKLIST.md](../../../CHECKLIST.md), and [RESULT.md](../../../RESULT.md) define the controls; root task/result files may be templates. Preserve existing project instructions and resolve conflicts before affected work.

Begin with read-only inspection and a bounded plan with exact checks. Implement only an explicitly approved revision and plan; an approved mission brief may supply both. Preserve existing authorization without asking for it again. Stop affected work when the canonical stop conditions apply.

Record actual evidence against the final implementation snapshot and every acceptance criterion. Keep unavailable measurements UNKNOWN and human acceptance PENDING until an explicit human decision identifies the reviewed snapshot. This optional Skill grants no additional execution or release authority and does not enforce permissions.

## If installed as a single file

`copilot skill add` installs only this SKILL.md, so the relative links above may not resolve. The canonical documents are at https://github.com/mmontielpz/ai-sdlc-lite-public (WORKFLOW.md, README.md, AGENTS.md, TASK.md, CHECKLIST.md, RESULT.md on the default branch). Read the target repository's own instructions first; fetch these only when needed and never treat them as approval.

## Zero-friction defaults

- A plain developer request is enough; do not ask setup questions. A missing `task-context.json` never blocks work: use the request as the bounded task.
- Before proposing edits, check the workspace is writable; if read-only, report it instead of proposing edits.
- For small tasks report the result in chat; create RESULT.md only if the user asks or the task requires a durable record.
- One BOV plan approval covers in-scope work. Native provider permission prompts are separate, never BOV approvals, and are not bypassed. Report prompts only from operator evidence; otherwise UNKNOWN.
