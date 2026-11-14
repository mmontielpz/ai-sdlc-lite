# Result record

Template: record actual evidence for one task. Replace placeholders; do not turn planned or illustrative checks into measured results. Use [README.md](../README.md) outcome definitions.

## Identity and changes — Observe

- **Task ID / approved task revision:** <ID, revision, link or brief reference>
- **Plan approval reference:** <explicit human decision; UNKNOWN if unavailable>
- **Baseline revision:** <commit SHA, or NO COMMIT>
- **Code revision checked:** <commit SHA plus precise uncommitted diff or file snapshot reference; for a new repository, identify the file snapshot>
- **Environment:** <working environment and relevant tool versions; UNKNOWN where unavailable>
- **Changes:** <files and resulting behavior>
- **Final repository status / diff review:** <actual status, scope review, and preserved existing changes>

Identify the implementation snapshot separately from this evolving result record. Further implementation changes invalidate affected evidence until rechecked.

## Acceptance evidence — Verify

| Criterion ID | Met / unmet / unverified | Evidence reference and explanation |
| --- | --- | --- |
| AC-1 | unverified | <verification row or review evidence> |

| Check / phase | Exact command or human review procedure | Working directory | Exit code | Actual outcome and evidence |
| --- | --- | --- | --- | --- |
| V-1 / <baseline or final> | <literal command or review steps> | <directory> | UNKNOWN | <relevant output or durable sanitized evidence reference> |

Add a row per attempt, retaining failures and retries. For a check not run, state why and leave its exit code UNKNOWN. For human review, use `N/A — human review` for exit code and identify the reviewer and observation. Label reused evidence and its source revision.

## Observations

Missing measurements are UNKNOWN, never zero. A measured zero needs a source. Record units, source, and covered window for each metric; preserve the provider's category definitions. Do not add overlapping or cumulative counters as if they were independent.

| Metric | Value | Units | Source / method | Covered window |
| --- | --- | --- | --- | --- |
| Elapsed wall time | UNKNOWN | seconds | UNKNOWN | UNKNOWN |
| Retries (additional attempts of a named operation) | UNKNOWN | attempts | UNKNOWN | UNKNOWN |
| Observed tokens (separate rows per reported category) | UNKNOWN | tokens | UNKNOWN | UNKNOWN |
| Provider-reported billed units | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Monetary cost (actual charges) | UNKNOWN | UNKNOWN currency | UNKNOWN billing evidence | UNKNOWN |

Elapsed time includes waiting unless separately measured; record start/end timestamps with timezone in its source. Identify the operation counted for retries. Token counts do not establish charges. If a cost estimate is useful, add a separate row labeled ESTIMATE with currency, price source, assumptions, and window; do not replace actual charges with it.

Use these same fields for observed active execution and human waiting intervals, each with its own boundaries and source; leave unobserved intervals UNKNOWN. Count native CLI permission prompts separately from BOV plan-approval prompts, naming categories and the observation window. Report zero only with complete observation, otherwise UNKNOWN. Do not infer active time from wall time or assume the agent observes every operational prompt.

A zero native-permission count requires a complete operator-maintained count or CLI trace covering the permission UI. Tool results or no prompts visible to the agent are insufficient. Label partial operator observations as partial; keep the complete count UNKNOWN and separate from BOV approvals. Reference sanitized evidence rather than raw transcripts.

## Outcome and lifecycle

- **Technical outcome:** <PASS / PARTIAL / BLOCKED; select only after verification>
- **Limitations / unmet criteria / obstacles:** <details, or NONE with supporting review>
- **Plan / Design:** <task and approval reference>
- **Build / Test:** <implementation and verification references above>
- **Deploy:** NOT PERFORMED — no release action authorized by this template. <If performed, record separate authorization, target revision, verification, and rollback evidence.>
- **Maintain:** <remaining issues, owner, next action; or not applicable with reason>

## Human acceptance — separate gate

- **Decision:** PENDING
- **Reviewed code revision / snapshot:** UNKNOWN
- **Human / date / explicit decision reference:** UNKNOWN
- **Reason or follow-up:** <human review notes>

Technical PASS cannot fill this decision. Record acceptance or rejection only from an explicit human decision for the reviewed revision. Acceptance does not authorize push, merge, deployment, publication, or paid operations. Stop for owner review unless the active task explicitly authorizes further action.

Default handoff: report evidence and stop with this decision PENDING, without an interactive acceptance prompt. Retain an explicit acceptance checkpoint when requested by the owner or required by project policy for high-risk delivery.
