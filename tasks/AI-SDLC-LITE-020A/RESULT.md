# AI-SDLC-LITE-020A — Low-Friction Copilot Developer Experience

## Identity and authorization

- **Active contract:** owner mission AI-SDLC-LITE-020A, AUDIT → MINIMAL IMPLEMENTATION → VERIFY, 30-minute timebox. Its explicit fallback permits retaining the implementation and reporting PARTIAL when safe friction reduction cannot be established.
- **Baseline:** existing uncommitted 019D snapshot on `e90cb86caaa23d2ef5a184233a909fd192555333`, 27 project files. Existing work and historical records were preserved.
- **Actual changes:** README.md plus this new result record. Final inventory: 28 project files. No installer, test, native Skill or canonical contract content changed.
- **Environment:** Linux x86_64, Python 3.14.9, Copilot CLI 1.0.109. Disposable Git repository, isolated COPILOT_HOME and COPILOT_CACHE_HOME. Known GitHub token environment variables were removed from the isolated UI launch without reading their values. No login or model task was submitted.

## Audit and implementation decision

The [official permission reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) supports location-scoped exact command identifiers, including named npm scripts. A literal command differs from a wildcard command prefix. These are tool permissions, not filesystem or side-effect confinement. [CLI security guidance](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) also distinguishes sandboxing and additional command warnings.

One isolated candidate contained exactly these identifiers for the disposable repository only: npm run lint, npm run build, npm run preview, npm run visual. It had no wildcard, interpreter, write, URL or extra-directory grants. No actual development command was requested through Copilot. Merely writing a valid documented profile does not prove command matching, denial behavior or fewer prompts.

Working sandbox qualification is blocked in this host: bwrap is present, but slirp4netns is missing. The isolated session requires login before a task can run. Existing credentials were not copied or inspected. Therefore no command profile was added to the installer, and no autonomous-development or security-blocking claim is made. The existing 019D sandbox-setting opt-in, backup and guarded rollback remain unchanged.

README now documents preflight scope, tools, script/hook risks, credentials, production exposure and temporary ownership; distinguishes task approval, CLI tool authorization, workspace access, sandbox enforcement and delivery acceptance; reuses approved routine operations without repeated BOV decisions; and states the explicit authorization requirements for production, credentials, dependencies, destructive actions, Git push/publication/release and scope expansion. Stable reviewed scripts are preferred over generated heredocs/compound commands. Cleanup is limited to task-owned files. This is document-based guidance, not newly enforced installer behavior.

### Skill edit rejected — no bypass

The patch tool rejected the proposed Skill/README patch with: “writing outside of the project; rejected by user approval settings.” Inspection then confirmed `.agents` is a read-only mount and its Skill file is not writable, while README is writable. Neither file changed in the rejected patch. No alternate write route, permissions change or mount repair was attempted. Only the independently authorized README documentation was subsequently updated. The native Skill refinement is **BLOCKED**, not delivered.

## Verification

Commands ran from the framework root unless stated otherwise:

```bash
copilot --no-auto-update help permissions
copilot --no-auto-update help config
python3 -B -m unittest discover -s tests -p 'test_install_skill.py' -v
python3 -B <codex-skills-dir>/.system/skill-creator/scripts/quick_validate.py .agents/skills/ai-sdlc-lite
git diff --check
git diff -- README.md
git status --short --untracked-files=all
```

| Check | Actual result | Exit |
| --- | --- | --- |
| Existing installer suite against changed README bundle | 29/29 PASS, no skips; Ran 29 tests in 5.159s | 0 |
| Native Skill structure | Skill is valid!; source hash unchanged | 0 |
| Existing backup/rollback and preservation cases | Rechecked by the 29-test suite; no new permission-profile rollback implementation claimed | 0 |
| Snapshot preservation | 26/26 protected hashes MATCH; exact 28-file inventory; no staging; README baseline reconstructed in memory and matched original hash | 0 |
| Markdown and whitespace | 99 local links/anchors PASS; both changed files PASS; tracked diff PASS | 0 |
| Proposed Skill patch | Tool policy rejection; no files changed | Rejected before write |
| Interactive UI | One session-only folder trust granted in synthetic repository, then /exit after login notice | 0 |

The suite exercises fresh/modified repositories, project discovery, confined configuration changes, task initialization, conflict refusal, idempotency, backup/rollback and later-edit preservation. It does not exercise a Copilot development command or prove model adherence to BOV. No tests failed. One final-audit tool call had a JavaScript syntax error before execution; the corrected audit passed without filesystem changes. Historical example tests were not rerun because their sources/tests are unchanged.

## New prompt observations

The UI launch used the isolated home/cache, explicit disposable target via `copilot -C`, default manual approval mode, no unrestricted options and no global grants. The exact candidate profile and sanitized terminal observation remain in local evidence supplied in the handoff.

| Category | Actual observation | Covered window |
| --- | --- | --- |
| Workspace folder trust | 1 dialog; selected Yes for this session only, not remember | Fresh launch through normal /exit |
| Authentication | 1 sign-in notice, not a permission-approval prompt; no /login performed | After session-only trust |
| External/parent paths | NOT REACHED / UNKNOWN | No task submitted |
| Read tool | NOT REACHED / UNKNOWN | No task submitted |
| Edit/write tool | NOT REACHED / UNKNOWN | No task submitted |
| Shell/external commands | NOT REACHED / UNKNOWN | No task submitted |
| Autonomous development operations | UNVERIFIED | No authenticated task |
| Unauthorized-operation blocking | UNVERIFIED | No attempted negative task execution |
| BOV plan and delivery behavior | Existing boundaries retained in documents; dynamic adherence UNVERIFIED | No development slice executed |

Prompt reduction is UNKNOWN. R1 screenshot observations are partial historical evidence, not a complete count or comparable task window. No historical total was invented, and the startup-only count is not treated as a development-task result.

Global config.json, permissions-config.json hashes and absence of settings.json matched before/after the isolated observation. No AI Summit or Touchline access, dependencies, global permission grants, commits, pushes, tags or releases occurred.

## Snapshot, measurements and handoff

- README SHA-256: `eed64ebd663ea5d84596e0d166ab3e17ac835ed892b94abe897394ade66f751b`.
- Preserved installer SHA-256: `38cf0308e2b1e36a827d0033f4898e781e3e9d59e57ce1b6c27db5ed93adb407`.
- Preserved tests SHA-256: `e571626e4d635b3a0df46d66d0687ce6eb04b95198c70b7531f5e6d74cd24ef2`.
- Preserved native Skill SHA-256: `7ac04089fb726f920396ba03448625c3995fa024674bbf74fe255fb621d54cf8`.
- This record's final hash is provided separately to avoid self-reference.
- Audit-start UTC boundary: `2026-11-12T15:40:09.241861+00:00`; scope-check boundary: `2026-11-12T15:47:20.064349+00:00` (430.822488 seconds, within the 30-minute timebox). This partial interval excludes completion of this record and the final response; full task elapsed time and active agent time are UNKNOWN.
- Task tokens, billed units and monetary cost: UNKNOWN. No model task was submitted; that is not a measured zero cost or token claim.

**Outcome: PARTIAL.** The measurable-reduction exit criterion is unmet. The permission mechanism is supported in principle; it is not rejected as universally unsafe or unsupported. This environment did not establish the execution, denial and confinement evidence needed to ship a profile safely.

**Next action:** owner reviews the two-file documentation delivery. Before a command profile is shipped, use an explicitly authorized authenticated isolated task on a sandbox-capable host, compare the same task with and without exact command grants, measure prompt categories and successful operations, and test unapproved commands/arguments and changed script definitions. Keep both BOV human decisions and separate privileged-action authorization. No broader access or new framework infrastructure is proposed.

**Human delivery acceptance: PENDING.** No public release authorization is inferred.
