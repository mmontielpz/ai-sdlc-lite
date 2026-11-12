# Working with AI-SDLC Lite

Use one bounded task at a time. This guide helps a human and an agent navigate the process; the canonical contracts remain [AGENTS.md](AGENTS.md), [TASK.md](TASK.md), [CHECKLIST.md](CHECKLIST.md), and [RESULT.md](RESULT.md). See [README.md](README.md) for BOV, lifecycle concepts, and outcome definitions. Preserve existing project instructions and work when adopting the process.

## Deliver one useful increment

With an AI Coding Agent, choose the smallest useful vertical slice: one observable outcome carried through the relevant behavior, implementation, and checks. Keep one authoritative task brief and one result record; link them from issues and reviews instead of copying their contents. Reuse relevant context and verification evidence when it still applies to the identified snapshot; recheck affected evidence after changes.

Apply Bound → Observe → Verify within each slice, then use user or reviewer feedback to choose the next slice. Keep checks proportionate to risk and maturity without weakening agreed criteria. Optimize for Outcome first, Time second, Tokens third; avoid infrastructure or documentation that does not help deliver or assess the slice.

A technically verified PoC, Prototype, or Pilot is not automatically production-ready. State the maturity and limits of the delivered increment. Production readiness is a separate decision about its intended use; technical PASS and human acceptance of the increment do not establish it or authorize deployment. This distinction adds no mandatory phase or approval gate.

## 1. Bound the task

The human states the objective, scope, exclusions, constraints, and observable acceptance criteria in the active task contract or an explicit mission brief. Identify its revision and the exact task/result paths. Blank template fields grant no authority.

Ask the agent to inspect instructions, repository status, baseline revision, relevant files, and existing checks without editing. The agent proposes a small design, implementation steps, exact verification commands with expected outcomes, risks, and stop conditions. If no suitable check exists, agree on a repeatable check first.

Suggested request:

> Read the applicable repository instructions and the named task contract. Inspect without editing, preserve existing changes, and report the baseline, proposed plan, exact checks, risks, and stop conditions. Stop before implementation unless this revision and plan already have explicit approval.

### Optional project and visual context

Use existing project instructions and the active task for project-specific context; the Skill and bundled framework documents provide process guidance, not product requirements. For UI work, optionally name approved brand guidelines, assets, screenshots or design references in that same task, with observable visual acceptance criteria. No new document or approval gate is required.

Inspect only authorized references and cite the source and revision for brand-specific claims. If references are unavailable or conflict, report the gap rather than inventing brand rules. Distinguish source observations and design inferences from runtime or visual verification; report viewport, checked behavior and evidence for visual checks, and leave untested appearance or usability claims unverified. Reuse already retrieved context and preserve project assets unless their modification is explicitly in scope.

### Read-only reconnaissance

Bound the questions, approved sources or paths, and exclusions before retrieving content. Read-only access can still expose sensitive information. Exclude credentials, production-derived personal information, data exports, raw transcripts, and sensitive historical handoffs; linked archives are not automatically in scope.

- Start with minimal revision and path metadata, then applicable project instructions and only the content needed for the approved questions. Do not execute project scripts or tests as part of inspection unless authorized.
- Reuse content already retrieved for the same repository, revision, path or endpoint. Filter that content before fetching it again. Batch independent approved reads; avoid broad recursive content dumps. Record a reason for a repeat read, such as a failed retrieval or changed revision.
- Integrate repository instructions and retain stricter project checks. A repository Git convention does not independently authorize a commit. Surface material conflicts and stop affected work instead of overriding requirements. BOV authorization defines task authority; repository instructions add project requirements; CLI permissions control tool prompts; sandbox or service restrictions constrain actual access. See [bounded autonomy](#bounded-autonomy-and-operational-permissions).
- If sensitive material appears, stop affected reading. Do not reopen, quote, or copy its contents into evidence. Report a sanitized incident category and request an owner decision before continuing that affected work.
- Label findings as source observations, inferences, or untested claims. Code inspection alone does not verify runtime behavior, UI appearance, responsiveness, or usability.

Reuse the existing [RESULT.md evidence fields](RESULT.md#acceptance-evidence--verify) for sanitized source/revision references, commands, retrieval justifications, permission observations, and limitations. State the counting window for prompts or repeated reads; incomplete screenshots are not a complete session count. Keep unavailable timing and usage UNKNOWN using the existing [measurement guidance](#outcome--time--tokens). These practices use the existing approval boundaries and stop conditions.

## 2. Approve the plan

The human explicitly approves the identified task revision and plan. Record the approval reference. An approved mission brief may serve as the contract; do not ask the human to repeat approval that already covers the work. Resolve instruction conflicts before affected implementation.

Suggested decision:

> I approve task <ID>, revision <revision>, and the proposed plan and checks. Implement within those boundaries, record actual evidence, and stop for human acceptance. No release action is authorized.

## 3. Observe implementation

The agent implements only the approved scope and records actual changes, check attempts, failures, and limitations in the named result record. Stop affected work for scope growth, material approach changes, conflicting instructions, unexpected changes to files needed for editing, unavailable required permissions, or verification that cannot be completed within the approved plan. Preserve evidence and obtain a revised decision instead of weakening checks.

Keep Outcome-first · Time-conscious · Token-aware: prioritize verified delivery, then end-to-end time and human effort, then available token observations. Use existing tools; do not add measurement infrastructure to chase missing counters.

### Timeboxed BOV micro-cycles

Break approved implementation into observable micro-slices. Each cycle has one concrete objective and one verification criterion. Default target: **3 minutes**; maximum budget: **5 minutes per cycle**. The approved task may choose a shorter target or maximum and states its total execution budget. If no total budget is given, declare the bounded execution window used rather than inventing owner authorization or claiming a full-task measurement. Finish early when the criterion is met; do not wait merely to fill a timebox.

One initial human plan approval covers all in-scope micro-slices. After approval, implement, inspect, test, correct and retest within those boundaries without repeated BOV approvals. Reuse existing context, scripts and still-valid evidence; prefer small verification steps over unnecessary repeated reads, whole-suite runs or browser sessions. CLI tool permissions, workspace access and sandbox restrictions remain separate and must not be bypassed.

After every cycle, report this checkpoint and proceed to the next approved action when safe:

```text
MICRO-SLICE: N
ELAPSED: measured / UNKNOWN
STATUS: PASS / PARTIAL / BLOCKED
CHANGES: files affected
VERIFICATION: evidence
NEXT: next bounded action
RISKS: new or unchanged
```

Measure elapsed wall time from recorded start/end boundaries, including work and waiting within that window; otherwise use UNKNOWN. Identify the measurement window separately from full task time and active agent time. Reuse the existing [RESULT.md evidence and observations fields](RESULT.md) for checkpoints, commands, outcomes, attempts and remaining budget; no new mandatory record is required.

Timing is **advisory**, not an enforced timeout, unless the execution tool provides and verifies that enforcement. State enforcement availability and never imply that a prompt, elapsed-time check or yielded tool call terminates a process. At the cycle or total-budget boundary, report a checkpoint and do not start more work under that expired budget. Keep outstanding work PARTIAL or BLOCKED. For an already running operation, report its state and use only a known safe completion/cancellation procedure; do not kill it in a way that corrupts files or leaves uncontrolled children. If no safe procedure is available, stop issuing work and report the enforcement limitation and pending process.

Stop after **two unsuccessful retries of the same failure**: the original failed attempt plus two failed retries is three failed attempts. Record each attempt; do not reset the count by crossing cycle boundaries or rerun an unchanged failing command without a reason. Also stop for scope expansion, new risks, dependencies, required permissions or privileged actions outside existing explicit authorization. Do not weaken agreed checks to fit a timebox. Checkpoints add visibility, not approval gates. Final human delivery acceptance remains separate and PENDING until explicitly given; no commit, push, deployment or release is implied.

## Zero-friction defaults for small tasks

A plain developer request can serve as the bounded task. A missing `.ai-sdlc-lite/task-context.json` never blocks work. Before proposing edits, confirm the workspace is writable (the installer reports `WRITE PREFLIGHT`); if read-only, report that instead of proposing edits. For small tasks, chat-only result reporting is the default; use RESULT.md when the user asks or the task needs a durable record. One BOV plan approval covers in-scope work; native provider permission prompts are a separate control and are not BOV approvals. Safety boundaries are unchanged.

## Bounded autonomy and operational permissions

Three controls are distinct: **BOV authorization** approves the task revision, scope, plan, and checks; **CLI permissions** determine which tool requests can run without another operational prompt; **sandbox enforcement** restricts actual filesystem, network, and command access. A prompt or Skill does not enforce those restrictions.

Within an approved plan, proceed with necessary inspection, allowed edits, agreed checks, diff review, and evidence recording without asking again for BOV approval. Preserve existing work and the stop conditions above. CLI permission prompts may still occur; granting a tool permission does not expand task scope, and blocked access does not authorize a bypass. Delivery acceptance remains the separate human decision below.

Use the narrowest supported permissions for the approved work. Operators may choose invocation-scoped options without changing global settings; the framework does not configure permissions automatically.

| Client | Operational controls and limits |
| --- | --- |
| Codex | For an operator-started local session, `--sandbox workspace-write --ask-for-approval on-request` retains sandboxing while supporting routine workspace work. It does not enforce a task's individual file allowlist or guarantee zero prompts. Managed host policies may override available choices. See the [official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli). |
| Copilot CLI | Narrow invocation-scoped `--allow-tool` rules can reduce repeated prompts. Version 1.0.109 help supports `write(absolute-path)` for individual edit-tool targets; these rules do not constrain shell commands. Broad shell or interpreter rules may permit more than the intended test. Repository “remember” choices can persist settings; avoid them when only session authority is intended. Tool permissions do not establish that an OS sandbox is enabled or available. See [tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/configure-copilot-cli) and [local sandboxing](https://docs.github.com/en/copilot/how-tos/cloud-and-local-sandboxes/using-local-sandboxing). |

Restrict opt-in rules to explicitly authorized files and exact reviewed verification commands for the approved task. Do not grant repository-wide writes, broad interpreter or shell access, use unrestricted allow-all modes, or disable sandboxing to remove prompts. Global settings changes require separate explicit authorization. Native CLI prompts may remain even with a narrow profile; do not claim they can always be eliminated. Required operational prompts are separate from the two BOV human decisions; no new workflow gate, global configuration, or mandatory tooling is introduced.

## 4. Verify and hand off

Run the agreed checks against the final implementation snapshot. Record exact commands, working directory, environment, exit codes, and relevant output. Distinguish baseline, final, reused, and not-run evidence. Recheck affected evidence after further implementation changes. Map evidence to every acceptance criterion, inspect the final diff and status, and use [CHECKLIST.md](CHECKLIST.md).

Report PASS, PARTIAL, or BLOCKED using the README definitions. Report unavailable facts and measurements as UNKNOWN. Keep elapsed time, retries, observed token categories, billed units, and actual monetary cost separate with sources and measurement windows. Do not infer charges from tokens.

By default, report the evidence and identified delivery snapshot, leave human acceptance PENDING, and stop without an interactive acceptance prompt. The human separately accepts or rejects the identified reviewed snapshot. Retain an explicit acceptance checkpoint when requested by the owner or required by project policy for high-risk delivery. This changes the reporting interaction, not who can accept the work; silence and technical PASS never imply acceptance. Technical PASS and acceptance do not authorize commits, pushes, merges, deployment, publication, tags, paid services, dependencies, or destructive operations beyond the active authorization. Record Deploy as not performed when unauthorized and identify remaining Maintain work or why none is needed.

## Outcome / Time / Tokens

Reuse the existing [RESULT.md fields](RESULT.md#observations). Measurement is optional; missing or unreliable attribution is UNKNOWN, never an assumed zero. Do not delay delivery to build collection infrastructure or add an approval gate.

- **Outcome first:** record delivered behavior, criterion evidence, technical result, and limitations against the checked snapshot. Reuse evidence that still applies and recheck affected evidence after changes. Human acceptance remains separate.
- **Time second:** define the window explicitly. Full task elapsed time runs from before the task prompt through completion of the final delivery response, including planning, approval waiting, implementation, checks, and reporting; exclude fixture preparation or label a different window. The operator captures boundaries outside the agent's response. If only part is observed, label that interval; full delivery time remains UNKNOWN. Elapsed time is not active agent time or human effort; report those only when separately measured.
- **Tokens third:** use reliable native observations with source, categories, session identity, and start/end boundaries. Label task usage separately from session totals. Subtract counters only when established as cumulative for the same uninterrupted session and task window; counter resets, mixed activity, or missing boundaries make task usage UNKNOWN. An agent cannot include its unfinished final response in a complete usage claim.

Record retries separately by named operation, retaining failed attempts. Keep provider-billed units and actual monetary cost separate from tokens, session totals, and retries; each needs its own source and covered window. Do not infer charges from tokens, reconstruct unavailable historical measurements, or claim development acceleration or savings from a single slice.

When observable, record wall-clock elapsed time, observed active execution intervals and human waiting intervals separately in the existing result fields. Name each interval and source; do not infer active execution by subtracting unknown waiting, or count unobserved work as active. Record native CLI permission prompts separately from BOV plan-approval prompts, with categories and counting boundaries. A complete observed window is required to report zero prompts; missing or partial observations are UNKNOWN. No extra instrumentation is required. Report checkpoints at micro-cycle boundaries, not as approval requests; reuse still-valid evidence and avoid redundant checks.

For native permission counts, cite a complete operator-maintained count or CLI trace that includes the permission UI. The agent's tool results or lack of visible prompts are not reliable evidence of zero: operational confirmations may occur outside its context. If only partial operator observations exist, label them as partial and leave the complete count UNKNOWN. Keep those observations separate from BOV approval counts; do not reproduce sensitive transcripts.

## Optional GitHub mapping

Use this mapping when the project works through GitHub. Local tasks use the same BOV controls without requiring an issue, branch, PR, or merge. Existing repository rules govern the collaboration steps and permissions.

| Step | BOV application |
| --- | --- |
| Task | Bound one slice with scope, criteria, checks, and an approved plan revision. An explicitly approved issue brief may supply the contract; a separate issue is optional. |
| Branch | Isolate the task from unrelated changes, identify the base revision, and preserve existing working changes. |
| Change | Implement the approved slice; record material decisions and stop for scope growth. |
| Tests | Run agreed checks against the final snapshot; record commands, outcomes, and limitations in the result record. |
| PR | Link the task and result; summarize the problem, resulting behavior, and remaining limitations. |
| Review | Inspect the diff and criterion evidence; the human explicitly accepts or rejects the identified snapshot. Recheck affected evidence after review changes. |
| Merge | Follow repository rules and explicit merge authorization for the target and reviewed revision. A merge does not authorize release or deployment. |

Permission to implement does not imply permission to commit, push, or create a PR. The approved brief can explicitly authorize those actions together within scope; do not ask again for authority already granted. Human acceptance and merge permission are distinct decisions that may be stated in one owner message. Repository permissions and required reviews/checks still apply; release authority remains separate. No GitHub CLI, CI, templates, or additional tooling is required by this mapping.

## Reuse and optional Skill

Preserve completed task/result records and evidence before reusing their paths. For task-specific paths, name them explicitly so the agent does not mistake root templates for the active task.

The optional [ai-sdlc-lite Skill](.agents/skills/ai-sdlc-lite/SKILL.md) points agents to these documents. Explicit Codex invocation with `$ai-sdlc-lite` was demonstrated in the inspected session; [QUALIFICATION.md](QUALIFICATION.md) records the historical evidence and recovered scope incident. Use the [README Quickstart](README.md#quickstart) for native invocation or the document-reading fallback and current provider qualification limits. The Skill adds no authority or enforcement. No global configuration is required by this guide. The two human gates above remain unchanged.
