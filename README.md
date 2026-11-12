# AI-SDLC Lite

**A lightweight, Markdown-first workflow for bounded development with AI coding agents.**

For software engineers and maintainers making bug fixes and small feature increments in existing repositories. AI-generated changes can solve the wrong problem or appear complete without evidence. AI-SDLC Lite makes the scope, human decisions, and verification explicit so each useful increment can be reviewed and accepted.

Use your existing agent, project tools, and checks. Start with a short request, agree on a bounded plan, implement one end-to-end slice, and use feedback to choose the next.

[Getting Started](#quickstart) · [Workflow](WORKFLOW.md) · [Examples](#examples) · [Qualification](QUALIFICATION.md#ai-sdlc-lite-012a-current-evidence-addendum) · [Limitations](#supported-agent-approach-and-limitations) · [Contributing](CONTRIBUTING.md)

**Status: EXPERIMENTAL — Pre-release.** AI-SDLC Lite is under active validation. Static checks and installer-level tests pass (68 tests), but live GitHub Copilot task qualification has NOT RUN. No production-readiness or token-efficiency claims are established. Human release acceptance is PENDING. Private vulnerability reporting must be enabled and verified before declaring publication readiness.

## Quickstart

Open your project with its AI-SDLC Lite documents available. For first-time setup, follow [Adopt in an existing repository](#adopt-in-an-existing-repository), preserving existing instructions and work.

If the native Skill is available, invoke it using your client's supported selection. In Codex:

> Use $ai-sdlc-lite. Fix [observable problem]. Inspect first and propose the smallest useful slice, allowed changes, and exact checks. Stop for plan approval.

For Copilot CLI, first use the [project Skill installer](#install-for-copilot-cli), launch in the target repository with `copilot -C /absolute/path/to/target-repository`, then request:

> Use the /ai-sdlc-lite skill. Inspect [problem], propose a bounded plan and exact checks, and stop for plan approval.

If the Skill is unavailable:

> Read the project instructions and WORKFLOW.md. Use BOV to inspect [problem] and propose a bounded plan. Stop before implementation.

The agent proposes the task brief and result location; you approve the identified revision and plan once. It implements, verifies, and reports, then you separately accept or reject the delivered snapshot. Use feedback to choose the next slice. The Skill supplies framework guidance; your repository instructions and active task supply project context. For UI work, optionally name existing [design references and visual criteria](WORKFLOW.md#optional-project-and-visual-context). See [bounded autonomy](WORKFLOW.md#bounded-autonomy-and-operational-permissions) for CLI prompts and permission limits.

**Outcome-first · Time-conscious · Token-aware.** Prioritize verified delivery, then elapsed time and human effort, then reliable native token observations. Keep engineering and documentation proportionate to the slice. Token measurement is optional; unavailable values remain UNKNOWN. No productivity, token-saving, or cost improvement is established by the recorded runs.

With AI Coding Agents, deliver the smallest useful end-to-end increment, verify its observable value, and use feedback to choose the next slice. Follow the [incremental delivery guidance](WORKFLOW.md#deliver-one-useful-increment). A technically verified PoC, Prototype, or Pilot is not automatically production-ready; functional delivery and production readiness are separate decisions.

## Bound → Observe → Verify (BOV)

- **Bound:** define the objective, allowed scope, exclusions, constraints, acceptance criteria, and conditions that require stopping.
- **Observe:** record what changed, which checks ran, what happened, and what remains unknown.
- **Verify:** compare evidence with the agreed criteria, report the delivered snapshot, and stop for human review.

Apply all three controls throughout the lifecycle. BOV is AI-SDLC Lite's organizing model.

## Six lifecycle concepts

| Concept | Smallest useful action |
| --- | --- |
| Plan | State the problem, scope, constraints, and observable acceptance criteria. |
| Design | Inspect the repository and propose an approach, affected files, risks, and checks. |
| Build | Implement the approved change within its boundaries. |
| Test | Run the agreed deterministic checks and record actual outcomes. |
| Deploy | If authorized, release the reviewed change with a verification and rollback plan. |
| Maintain | Record remaining issues and use operational feedback to define the next task. |

These concepts form a repeatable loop. A small task can cover several together. Record a reason for any stage that is not applicable or not performed.

## Two human approval gates

1. **Before implementation:** a human approves the written task and proposed plan after read-only inspection. Record the approver, date, and task revision. Material changes to scope or approach require renewed approval.
2. **Delivery acceptance:** by default, report the diff, verification evidence and unresolved issues, leave acceptance PENDING, and stop without an interactive acceptance prompt. A human may separately accept or reject the identified snapshot. Retain an explicit acceptance checkpoint when requested by the owner or required by project policy for high-risk delivery; do not infer acceptance from silence or technical PASS.

A passing check does not grant human acceptance. Acceptance does not authorize a push, merge, deployment, publication, or paid operation; those actions need explicit authorization within the task or separately. An agent must not invent human approval.

## Adopt in an existing repository

### Native Copilot Skill install (no Python)

`copilot skill add` takes a file, directory, or a URL to a **single SKILL.md** over HTTPS; a GitHub `/tree/...` page URL is not a SKILL.md and is not supported. Once this repository is public, from the target repository:

```bash
copilot skill add --project https://raw.githubusercontent.com/mmontielpz/ai-sdlc-lite/master/.agents/skills/ai-sdlc-lite/SKILL.md
```

`--project` writes `.github/skills/ai-sdlc-lite/SKILL.md` in the current project; omit it for `~/.copilot/skills/`. Verify with `copilot skill list` (expect `ai-sdlc-lite`, enabled). Remove with `copilot skill remove ai-sdlc-lite`.

**Evidence and limits:** installing the local file with `--project` into a disposable repository was observed to create only that one file, which `copilot skill list` reported as an enabled project Skill (Copilot CLI 1.0.109). Installing from the public raw URL was **not tested** because the repository is not yet public. A single-file install does not include `framework/`; the Skill points to the canonical documents by URL. For a self-contained offline bundle, use the Python installer below (optional fallback). Native installation does not grant permissions; Copilot may still prompt for tool use, and live Copilot task qualification is **NOT RUN**.

### Install for Copilot CLI

From a reviewed AI-SDLC Lite checkout, use Python 3.9+ and Git to install into an explicit target repository:

```bash
python3 /absolute/path/to/ai-sdlc-lite/scripts/install_skill.py --target /absolute/path/to/target-repository
python3 /absolute/path/to/ai-sdlc-lite/scripts/install_skill.py --target /absolute/path/to/target-repository --check
copilot -C /absolute/path/to/target-repository
```

Then use the copy-ready request in [Quickstart](#quickstart). Task initialization and permission configuration below are optional; an existing authoritative task needs no duplicate record. See [safe uninstall](#safe-uninstall) when removing or replacing the bundle.

The [installer](scripts/install_skill.py) resolves the target Git root, reports existing changes, previews every destination and SHA-256, and writes only inside `.agents/skills/ai-sdlc-lite/`. Add `--dry-run` to preview without writing. A framework target, conflicting installation, or symlink in the installation path is refused. Matching repeat installations do not rewrite files; automatic upgrades are not supported.

The installed entry point links to `framework/`, containing byte-preserved canonical documents, their local link dependencies, and the MIT license. Linked examples and historical evidence are reference material, not additional instructions to execute. Existing target instructions and active records remain untouched. Agree on task/result paths outside the bundle; the manual adoption steps below remain available when adapting templates.

`READY` after installation means the references are present and the installed Copilot CLI discovers this enabled project Skill. It does not establish task approval, sandbox enforcement, successful coding, or zero permission prompts. Missing CLI or failed discovery reports `BLOCKED` and leaves installed files available for inspection or rollback. Use `--check` for a non-writing workspace and installed-manifest check, and `/skills info ai-sdlc-lite` in the target session. The installer reports root and parent `AGENTS.md` locations without reading or changing their contents, target writability, task-context paths and the launch command. Detection does not establish that Copilot loads an ancestor file. CLI behavior depends on version and policy. Default installation changes no permissions or global configuration and runs no packages, builds, tests or inference.

`--init-task MY-TASK` creates pending TASK, CHECKLIST and RESULT records under `tasks/MY-TASK/`, plus `.ai-sdlc-lite/task-context.json` naming the active paths. It preserves root records and existing project instructions. If an authoritative task already exists, add `--task-contract tasks/R1/TASK.md` with its actual repository-relative path; that file is referenced without alteration. Existing conflicting records are refused. Repeat initialization preserves subsequent record edits. The installed Skill asks the agent to read this context; it does not guarantee compliance or reconstruct a missing approved R1 brief. New templates remain PENDING; existing approvals require the original contract and explicit owner decision. Task records and the context pointer survive Skill uninstall.

### Optional Copilot sandbox settings

Copilot CLI 1.0.109 supports user sandbox settings in an explicitly selected `COPILOT_HOME`. After reviewing a preview, opt in with:

```bash
python3 /absolute/path/to/ai-sdlc-lite/scripts/install_skill.py --target /absolute/path/to/target-repository --configure-copilot --copilot-home /absolute/path/to/copilot-home --dry-run
```

The Copilot home must already exist. Remove `--dry-run` to set only `sandbox.enabled=true` and `sandbox.allowBypass=false`, preserving unrelated settings. Add `--read-instruction /exact/ancestor/AGENTS.md` only for a detected regular parent instruction file: this appends its exact path to the sandbox's `readonlyPaths`, not a directory or write grant. Configuration affects every session using that Copilot home; it is not repository-scoped. Launch with `COPILOT_HOME=/absolute/path/to/copilot-home copilot -C /absolute/path/to/target-repository`. An isolated home does not inherit another home's authentication or settings. The installer never copies credentials or performs login.

The installer previews changed keys and destinations, backs up original settings privately inside the selected home, and refuses conflicting backups, symlinks or non-JSON settings (including JSONC). Use `--rollback-config --copilot-home /absolute/path/to/copilot-home` to restore exact original bytes, or remove installer-created settings when none existed. Add `--dry-run` for rollback preview. Later settings edits block rollback and preserve both settings and backup. Do not run concurrent configuration writers.

**Parent-file CLI path approval remains BLOCKED for automatic setup.** The supported saved path gate grants directories, while a sandbox read-only file rule does not independently satisfy that gate. No parent-directory access, persistent tool grants or external-command approvals are added. OS sandbox support and actual enforcement must be verified on the host; accepted configuration does not prove enforcement. See [Copilot configuration](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) and [instruction discovery](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions). Interactive prompt counts and any reduction remain UNKNOWN until a comparable measured session is run.

For development preflight, ask the agent to report the target snapshot, allowed files, exact project scripts and available tools, expected writes/network use, risks, credential requirements, production exposure and task-owned temporary paths. Inspect script definitions and lifecycle hooks without reading secret values. Prefer reviewed project scripts for lint, build, loopback-only preview and visual tests over generated heredocs or compound commands. A command rule does not confine a script's effects; recheck affected authorization after script changes. Keep artifacts isolated and clean up only explicitly task-owned files.

Keep task approval, CLI tool authorization, workspace access, sandbox enforcement and delivery acceptance distinct. Within the approved plan, proceed with supported routine operations without repeated BOV approvals; respect operational prompts and restrictions. Production access/deployment, secrets or credentials, new dependencies, destructive work outside task-owned temporary paths, Git push, publication/release and scope expansion need explicit authorization for that action. Routine plan approval does not imply it.

An optional narrow permission setup is available for Copilot CLI 1.0.109. Its configuration behavior is tested; authenticated command matching, runtime confinement and prompt reduction remain unqualified. The native Skill is unchanged because `.agents` is read-only in the inspected environment; use the document-based guidance above. No filesystem restriction is bypassed.

### Opt in to reviewed development operations

First install the Skill and identify the active task as above. The installer preflight reports workspace changes, tools, declared test scripts, risks and UNKNOWN production/credential exposure within its metadata/package inspection scope. It executes no project checks. Agree on one concise task plan with exact operations and observable checks; keep its explicit owner approval reference separate from configuration consent and final delivery acceptance.

Prepare a repository-relative JSON plan, for example `tasks/MY-TASK/copilot-plan.json`:

```json
{
  "approval_reference": "",
  "scripts": ["lint", "build", "test"],
  "read_files": ["src/example.ts"],
  "edit_files": ["src/example.ts"],
  "reviewed_package_sha256": "",
  "production_exposure": "UNKNOWN",
  "credential_exposure": "UNKNOWN",
  "filesystem_access": "Describe allowed files and artifact paths",
  "network_access": "UNKNOWN",
  "risks": ["Review scripts, lifecycle hooks and their side effects"]
}
```

Use real existing file paths. Leave approvals/exposure unknown until established; never put secrets in this plan. For command grants, review package.json and lifecycle hooks, record the package hash shown by preview, supply the actual owner approval reference, and use `NONE_DECLARED` exposure values only when supported by the bounded review. These are owner declarations, not verified absence of production or credentials.

```bash
python3 /absolute/path/to/ai-sdlc-lite/scripts/install_skill.py --target /absolute/path/to/target-repository --configure-copilot --copilot-home /absolute/path/to/dedicated-copilot-home --permission-plan tasks/MY-TASK/copilot-plan.json --dry-run
```

Review the exact destinations, grants, hashes and consent token. Repeat with `--consent-config TOKEN` instead of `--dry-run` to apply that exact proposal. Omitting consent previews without writing. Changing the plan, declared files or existing settings invalidates the token. Default global Copilot home, unknown CLI versions, inherited unrestricted modes, linked worktrees and pre-existing target grants are refused. Other repositories' settings remain unchanged. Use a dedicated existing Copilot home; authentication is not copied or performed by the installer.

Only literal `npm run lint`, `npm run build` and `npm run test` identifiers are stored for the target repository. Exact read/edit file rules appear in the printed invocation command and apply only when that command is used. There are no generic interpreter, shell, write or extra-directory grants. The setup enables sandbox settings and disables bypass, but this does not prove host support or enforcement. A command grant authorizes the script's code and hooks; it cannot confine their effects. File rules do not constrain shell commands. Recheck source/config changes and stop for changed scope or risks; do not treat the profile as task authorization.

This profile is not an exact-command or task-expiry security boundary. Saved repository command approvals remain until guarded rollback; use a dedicated Copilot home for the approved trial and roll back afterward. Absolute-file rules avoid a repository-wide write grant for built-in tools, but do not narrow the CLI's default workspace access or constrain shell effects. CLI 1.0.109 help does not establish safe exact-argument matching for Python unittest; leave that command ungranted and approve the reviewed request once if needed. Do not substitute a generic Python grant. New files and other unsupported operations may still prompt. The owner must separately consent to the permission preview; BOV plan approval alone does not apply it.

Preview, browser verification and cleanup remain ungranted because their effects and ownership cannot be established from command names. Such requests may require operational approval; use reviewed loopback-only/owned-artifact scripts in the task plan without broad grants. Production, credentials, dependencies, security changes and publication are never inferred from routine development approval. After plan approval, implement, check, fix and retest within scope without repeated BOV decisions; reuse context and stop at new risks, permissions or final acceptance.

The printed launch command uses `COPILOT_HOME=... copilot --no-auto-update -C /absolute/path/to/target-repository` plus exact file rules. Keep sessions stopped while changing configuration. `--rollback-config --copilot-home ...` restores exact original permission/settings bytes or absence, only if both files remain unchanged; later edits preserve both files and the private backup. Reconfiguration requires rollback/review first. The older sandbox-only opt-in still works without a permission plan.

### Safe uninstall

Preview removal from the explicit target:

```bash
python3 /absolute/path/to/ai-sdlc-lite/scripts/install_skill.py --target /absolute/path/to/target-repository --uninstall --dry-run
```

Review the exact files and empty installation directories, then omit `--dry-run` to remove them. Only manifest-listed files with unchanged hashes are removed. Edited files, additional files and unowned empty directories are preserved and reported as `BLOCKED`; the manifest remains for review. Missing, corrupt, incomplete or unsafe manifests and symlinks are refused before removal. Repeated uninstall of an absent installation succeeds; a partial uninstall keeps preserving retained content. Parent `.agents/skills` directories, project code and active task history remain untouched.

Uninstall and configuration rollback validate the target and their own ownership/backup evidence before task/package preflight, so stale task context or malformed package.json cannot prevent recovery. Uninstall restores no Copilot configuration. Use `--rollback-config --copilot-home ...` separately; without verified original-state evidence, or after later settings edits, restoration is blocked. Read-only/unwritable removal scope is reported as `BLOCKED`, with no permission repair or bypass. Keep manifests/backups intact and stop concurrent writers. An older 019B installation is not silently upgraded: review and uninstall its unchanged bundle before reinstalling; task records remain intact.

### Manual document adoption

1. Open the target repository and review its existing instructions and working changes. Copy or adapt [TASK.md](TASK.md), [CHECKLIST.md](CHECKLIST.md), and [RESULT.md](RESULT.md) into its root, preserving any existing files with those names. Use another agreed location if needed, and tell the agent the exact paths.
2. Review [AGENTS.md](AGENTS.md). If the target already has agent instructions, merge the relevant guidance into them; never overwrite existing AGENTS.md instructions. Resolve conflicts with the project owner. If none exists, adapt this AGENTS.md to the project. Keep applicable license notices when copying project material; examples and other foundation documents are not required for adoption.
3. Keep one active task/result pair. Before reusing it, preserve the completed pair and its evidence under a task-specific directory, such as `tasks/SMALL-FIX-001/`, or in version history. Retain approval references, checked revisions, and verification evidence together; do not overwrite prior results or commit secrets.

Use the [Quickstart](#quickstart) in the target repository. The agent inspects the applicable instructions and proposes the bounded task before approval; you do not need to complete every template field manually first. Explicit reading was demonstrated in the bounded runs described in [QUALIFICATION.md](QUALIFICATION.md).

## Workflow guide and optional Skill

For a guided task from read-only inspection through human acceptance, use [WORKFLOW.md](WORKFLOW.md). The four BOV contracts remain canonical. Name task-specific contract and result paths explicitly and retain existing approvals and project instructions.

The [optional GitHub mapping](WORKFLOW.md#optional-github-mapping) connects Task → Branch → Change → Tests → PR → Review → Merge under repository rules. Local tasks need no GitHub, and both existing human approval boundaries remain in place. See [CONTRIBUTING.md](CONTRIBUTING.md) for concise contribution guidance.

An optional repository [ai-sdlc-lite Skill](.agents/skills/ai-sdlc-lite/SKILL.md) provides a small entry point to the same documents. Explicit invocation with `$ai-sdlc-lite` was demonstrated in the inspected Codex session: the available Skill and supplied instructions matched the repository source. Copying task/result templates does not install or expose the Skill; use the document-reading fallback if your client cannot find it. See [qualification limits](#supported-agent-approach-and-limitations) for provider-specific evidence.

## Detailed workflow

Follow [WORKFLOW.md](WORKFLOW.md) for inspection, plan approval, scoped execution, verification, and delivery acceptance. Keep one authoritative task brief and one result record; link them rather than copying their contents. If no suitable automated check exists, agree on a repeatable check before implementation. Visual and usability claims need appropriate human review.

## Expected repository structure

The committed baseline contains 23 project files. The current working tree has 34 files, including the installer, four framework test files and results for 019B, 019D, 020A, 020B, 020C micro-cycles and 021B. Root task/result files are reusable templates; example and task records preserve execution evidence.

```text
README.md
AGENTS.md          # durable agent operating rules
TASK.md            # one bounded task, plan, and approval
CHECKLIST.md       # human checkpoints and verification
RESULT.md          # evidence, outcomes, and acceptance
LICENSE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
WORKFLOW.md        # navigation through the existing controls
QUALIFICATION.md   # portable evidence, limits, release blockers, full inventory
.agents/skills/ai-sdlc-lite/SKILL.md
examples/small-fix/   # repaired normalization and isolated baseline replay
examples/copilot-live/ # owner-reported clamp slice
examples/codex-live/   # verified elapsed-time formatter
tasks/AI-SDLC-LITE-UX-002/RESULT.md # historical staging record
tasks/AI-SDLC-LITE-011C/RESULT.md   # formatter verification and measurements
```

The [current-evidence addendum](QUALIFICATION.md#current-inventory-and-snapshot-identity) lists all 23 paths. Historical 18-file and 20-file inventories describe earlier snapshots; their records and hashes remain unchanged. Temporary harnesses, raw transcripts, credentials, and local state are outside the project inventory.

When adopting the process, adapt the task records to your repository. Merge guidance into existing instruction files after review; do not overwrite project rules or create competing sources of truth.

## Examples

These small, standard-library Python examples show observable behavior and bounded verification:

| Example | Behavior | Evidence |
| --- | --- | --- |
| [Name normalization](examples/small-fix/README.md) | Trim surrounding whitespace and lowercase, preserving internal whitespace. | Five passing tests recorded, with a separate replay of the original two-failure baseline. |
| [Integer clamp](examples/copilot-live/clamp_int.py) | Limit an integer to inclusive bounds. | [Six tests](examples/copilot-live/test_clamp_int.py); passing execution reported by the owner for Copilot CLI 1.0.109. |
| [Elapsed-time display](examples/codex-live/format_elapsed.py) | Format nonnegative integer seconds as M:SS without a minute cap. | [Six tests](examples/codex-live/test_format_elapsed.py) and smoke check passed in the directly observed Codex pilot; [result and measurement boundaries](tasks/AI-SDLC-LITE-011C/RESULT.md). |

The [qualification record](QUALIFICATION.md#evidence-attribution-and-qualification-scope) distinguishes recorded, directly observed, and owner-reported evidence. These examples do not establish production readiness.

## Supported agent approach and limitations

The methodology is the task, controls, approvals, and evidence. Codex, GitHub Copilot CLI, and Claude Code are separate products that can act as development agents. This project intends to use Codex for development and Copilot CLI for workshop execution; neither is a dependency of the core process. Claude Code is another possible execution tool.

Start with one agent. Discovery, permissions, and usage reporting depend on the client, version, and environment.

| Capability | Qualification |
| --- | --- |
| Explicit Codex Skill invocation and bounded local delivery | Demonstrated in the inspected environment; includes a recovered scope incident and the accepted formatter pilot. |
| Copilot CLI 1.0.109 Skill discovery and coding slice | Owner-reported success; not an independently repeated compatibility qualification. |
| GitHub task-to-merge workflow | Documented optional mapping; execution not qualified. Local tasks require no GitHub. |
| Automatic Codex discovery, broader agent/platform compatibility, first-time usability, and workshop use | Unverified. |
| Full task timing, active agent time, task tokens, billed units, and monetary cost | No complete attribution established for the pilot; the recorded 209.330981-second window is partial. |

See [supported claims and exclusions](QUALIFICATION.md#supported-limited-scope-v1-claims) and the [incident record](QUALIFICATION.md#incident-and-controlled-recovery). The evidence does not establish universal compliance, development acceleration, or savings.

Markdown instructions and checklists are procedural controls. They do not enforce permissions, sandbox commands, prevent destructive actions, or guarantee agent compliance. Use the repository's existing access controls and review process. The core Markdown workflow adds no runtime, CLI, SDK, telemetry, backend, cloud service, or paid API requirement; the optional installer uses existing Python and Git. Your chosen agent and project may have their own requirements and costs.

## Outcomes and honest measurement

| Value | Meaning |
| --- | --- |
| PASS | All agreed acceptance criteria are met and supported by recorded verification evidence. Human acceptance is recorded separately. |
| PARTIAL | Some work is complete, but at least one criterion is unmet or unverified. List the gaps. |
| BLOCKED | An obstacle prevents meaningful progress within the approved boundaries. Record the obstacle and the input or action needed. |
| UNKNOWN | A fact or measurement is unavailable or cannot be established. This is a field value, not a successful task outcome. |

Record checks as passed, failed, or not run, with commands, exit codes, relevant output, environment, and the code revision checked. Label reused or illustrative evidence. Do not hide failures through retries, substitute confidence for evidence, or describe unperformed checks as passed.

Keep these measurements separate, with a source, units, and measurement window:

- **Measured tokens:** counts reported by a tool, retaining its categories and definitions.
- **Billed units:** provider-reported charging units, which may use a different basis from token counts.
- **Elapsed time:** start-to-end wall time, including waiting unless separately measured. It is not active work time.
- **Monetary cost:** actual charges only when supported by billing evidence, with currency and covered period. Any estimate must be labeled separately with assumptions and price source.

Token counts do not establish monetary charges. Missing measurements are `UNKNOWN`, not zero. Do not infer comparable usage or savings across tools from incompatible counters.

## Contributing, security, and versioning

See [CONTRIBUTING.md](CONTRIBUTING.md) for change and review guidance, [SECURITY.md](SECURITY.md) for disclosure limitations, and [CHANGELOG.md](CHANGELOG.md) for project history and the versioning policy. No V1.0.0 release has been made.

## Attribution and license

AI-SDLC Lite is an independent adaptation informed by [Anthropic's AI-Native SDLC Playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook). It retains the six lifecycle concepts while using original wording and a smaller, manual process. It is not affiliated with, certified by, or endorsed by Anthropic, OpenAI, or GitHub.

Design lessons also came from the local FOB (Fix One, Break One) AI-SDLC handoff: bounded work, human checkpoints, and evidence-based reporting. No FOB files or implementation code are included. Findings from that single project do not establish general productivity benefits.

Original AI-SDLC Lite project material is available under the [MIT License](LICENSE). Referenced third-party material and trademarks remain subject to their respective owners' rights; the project license does not relicense them.
