# AI-SDLC-LITE-020B — Controlled Autonomy Setup

## Identity and changes — Observe

- **Authorization:** owner mission AI-SDLC-LITE-020B, IMPLEMENT → VERIFY → OWNER REVIEW. The mission supplies this implementation's approval; it does not supply missing approvals for another coding task.
- **Baseline:** 019D installer plus 020A documentation, 28 project files, on `e90cb86caaa23d2ef5a184233a909fd192555333`. Existing uncommitted work was preserved.
- **Changed:** scripts/install_skill.py and README.md.
- **Added:** tests/test_controlled_autonomy.py and this result record. Final inventory: 30 project files.
- **Protected:** all 26 other starting files, including the existing tests/test_install_skill.py, native Skill, canonical contracts and historical evidence.
- **Environment:** Linux x86_64, Python 3.14.9, Copilot CLI 1.0.109. Mutation tests use disposable Git repositories and isolated Copilot home/cache directories. No field-experiment repository was accessed.

## Implemented behavior

Preflight reports Git root/cwd, existing changes, installed Skill/task paths, available Copilot/Node/npm versions, PATH browser discovery and declared test scripts. It executes no project scripts. Production and credential exposure are UNKNOWN within the declared metadata/package inspection scope. It identifies filesystem/network review and separately authorized operations; it does not infer safety from a local repository or script name.

The existing sandbox-only configuration workflow is retained. The new opt-in is selected with `--configure-copilot --permission-plan <repository-relative JSON> --copilot-home <explicit dedicated directory>`:

1. Detect CLI 1.0.109 and expected permission help. Refuse other versions, default global home, linked-worktree scoping, inherited unrestricted/assisted modes, unsafe paths and pre-existing target grants.
2. Read existing settings without printing their values. Preview exact target command identifiers, session file flags, changed sandbox keys, destinations and resulting hashes. Unrelated settings/locations are preserved.
3. Print one execution-plan proposal with scope/operations and owner-declared exposure, access and risks. Missing facts remain UNKNOWN. A supplied approval reference is caller information, not independently authenticated human approval.
4. Without `--consent-config TOKEN`, preview only. A token binds the target, CLI version, plan bytes, declared file/package hashes and both configuration states. A changed plan, declared file or setting invalidates it.
5. Apply only with matching consent and a nonblank actual plan-approval reference. Command grants additionally require a matching reviewed package.json hash and explicit no-production/no-credential declarations. Those declarations are not a proof that the environment contains no secrets.
6. Back up exact original settings/permission bytes privately. `--rollback-config` restores previous bytes or absence only when both files match the installed state. Later changes preserve both files and the backup. Reconfiguration requires rollback/review rather than silently accumulating grants.

The profile stores literal `npm run lint`, `npm run build` and `npm run test` identifiers under the target repository location in permissions-config.json. It adds no generic interpreter, wildcard command, write-tool or directory grants. Approved file read/edit rules use absolute literal paths in a printed invocation-scoped command. Known secret/security/dependency-control paths and glob/pattern paths are refused. These added rules do not constrain shell effects or replace the CLI's defaults and organization policy.

Sandbox enabled/bypass-disabled settings are shown explicitly. Host support and enforcement remain unverified. Script code, lifecycle hooks and transitive configuration can have broader effects than a command name; review them and recheck changed scope. Consent fingerprints are setup-time checks, not continuous runtime integrity enforcement. No automatic production, credential, dependency, deployment, publication or security-change authority is inferred.

## Permission compatibility

| Capability | Configuration evidence | Runtime qualification |
| --- | --- | --- |
| Repository-local reads | Absolute invocation read rules accepted by real CLI parser; reads normally already allowed subject to policy | Authenticated tool behavior UNVERIFIED |
| Explicit approved edits | Absolute invocation write rules accepted; sensitive/control files refused by setup | Authenticated edits/negative variants UNVERIFIED |
| Exact lint/build/test | Supported literal saved identifiers; only target location changed | Real Copilot matching/denial UNVERIFIED |
| Loopback preview | UNGRANTED; a command name does not constrain binding/network | Not qualified |
| Browser verification | UNGRANTED; reviewed execution/network effects not established here | Not qualified |
| Owned temporary cleanup | UNGRANTED; ownership/effects cannot be inferred from the name | No generic rm grant |
| Parent directory access | No directory grant added | Existing operational prompts may remain |
| Source Skill refinement | BLOCKED by read-only .agents mount; no write attempted | Existing Skill preserved |

[GitHub's configuration reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) documents location-scoped literal command identifiers and distinguishes settings from saved permissions. [The CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) documents invocation tool rules and their limits. Local help and metadata invocations were checked for the installed version; documentation support is not represented as observed command enforcement.

## Verification evidence

Commands from the framework root:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .agents/skills/ai-sdlc-lite
git diff --check
git status --short --untracked-files=all
```

The original 29 tests are unchanged. Sixteen new tests cover preview/no consent, exact stored grants, omitted capabilities, stale file/settings tokens, absent approval, review hash/exposure requirements, backup and exact rollback, preservation of later edits, refusal of existing broad grants, sensitive/glob paths, unknown versions, inherited unrestricted modes, unchanged BOV decisions, UNKNOWN preflight exposure, and refusal to overlap sandbox-only and permission transactions. Compatibility decisions in these unit tests use controlled CLI responses; actual metadata/configuration checks below are separate.

| Verification | Evidence/status |
| --- | --- |
| Full suite before invocation fix | 44/44 PASS, exit 0 |
| Full suite after invocation fix | 44/44 PASS, exit 0 |
| Suite after preview disclosures | 44/44 PASS, exit 0 |
| Final suite with transaction-overlap regression | 45/45 PASS, no skips, exit 0; Ran 45 tests in 35.302s |
| Native source Skill validation | Skill is valid!, exit 0 |
| Original test preservation | Existing test file retained at baseline SHA-256; protected comparison in handoff |
| New/default installation and check | Real CLI exits 0 in disposable repository; enabled project Skill found |
| Consent preview/apply | Preview left settings unchanged and permissions absent; apply stored the reviewed target profile |
| Native invocation parsing | Corrected equals-form absolute read/write flags accepted by real CLI alongside skill list --json |
| Settings compatibility | Native config read reports sandbox.enabled=true |
| Direct synthetic operation controls | npm run lint, npm run build, npm run test each exit 0; these are direct operator controls, not Copilot autonomy |
| Rollback after UI | Exit 0; exact original settings bytes restored and previously absent permissions file removed |
| Preservation | All original synthetic source/task/result hashes and global configuration hashes match |
| Final framework scope | 26/26 protected hashes MATCH; exact 30-file inventory; HEAD unchanged; nothing staged; 99 local links/anchors and four-file whitespace checks PASS, exit 0 |

One integration attempt failed with exit 1: space-separated variadic `--allow-tool` arguments consumed the following metadata subcommand. The generated form was corrected to `--allow-tool=...`. The failed invocation and successful retry remain in local operations evidence. No check was weakened. Unit suites had no failing tests.

## Measured UI window and new-risk stop

The generated invocation used explicit `copilot -C`, the dedicated home/cache, exact file flags and default manual approval mode. Known GitHub token environment variables were removed without reading their values. No credentials were copied and no login or model task was submitted.

| Category | Actual observation |
| --- | --- |
| Folder trust | 1 dialog; selected Yes for this disposable session only |
| Authentication | 1 sign-in notice; no /login performed |
| Environment-secret warning | 1 warning reporting 2 possible environment secrets; values were not reviewed or copied |
| Read/edit/shell/external-path prompts | NOT REACHED / UNKNOWN; no authenticated task |
| Autonomous Copilot operations | UNVERIFIED |
| Unauthorized runtime denial | UNVERIFIED; configuration refusals are not runtime-denial tests |
| Prompt reduction | UNKNOWN; no comparable authenticated baseline |

The environment-secret warning was treated as a new risk. The UI was exited immediately without opening the secret review, requesting a model response or executing a Copilot command. No sensitive content was encountered beyond the sanitized warning. The sandbox-enabled UI label is a configuration indicator, not evidence of OS enforcement; the known missing slirp4netns prerequisite remains unresolved.

An authenticated isolated configuration path was requested from the owner. None was available during these checks. R1 observations remain partial historical evidence; no full prompt total or reduction was reconstructed.

## Snapshot, measurements and limits

| Implementation file | SHA-256 |
| --- | --- |
| README.md | `54a43dba272246a9c97d172c05bb0cd722bccfd428f8d87709f0b4f790429921` |
| scripts/install_skill.py | `38349bbf2adf88211ef0b088106ecd407c1f989c678f895d5ba3eabe1e8bb4c3` |
| tests/test_controlled_autonomy.py | `fe9d613ae55e273f4cbc9add090329a55f917e3f67410e865eef4d5689923a83` |

The evidence record's own final hash is supplied in the handoff. Local operations evidence records exact argv, cwd, stdout/stderr, UTC boundaries, exit codes and the retained failed attempt. Logs contain no credential values. Private settings backups stay outside public evidence.

Full task elapsed time, active agent time, task tokens, provider-billed units and monetary cost remain UNKNOWN. Local test/operation durations cover only their named invocations. No model task was submitted; that is not a measured zero token/cost claim.

This is a configuration helper, not an orchestrator or sandbox. It does not continuously enforce plan scope, validate arbitrary script side effects, authenticate approval references or automatically accept delivery. Runtime file/command matching, changed argument rejection, actual shell confinement and prompt reduction require a separately authorized authenticated test. Do not run concurrent settings writers; an interrupted multi-file update can require owner review of the retained backup. JSONC and unknown modes/versions are refused rather than reinterpreted.

## Outcome and next action

**Overall: PARTIAL.** Configuration/preflight/consent/preservation behavior was demonstrated. The source Skill change is BLOCKED. Authenticated task execution, runtime negative cases and prompt reduction remain unverified, so end-to-end controlled autonomy is not qualified.

No AI Summit/Touchline access, global grants, dependencies, commits, pushes, tags or releases occurred. Canonical BOV contracts and historical records remain unchanged. New workflow consent is operational configuration consent, not an extra per-operation BOV gate. Delivery acceptance stays separate.

Owner review should precede reliance on the new profile. An authenticated isolated test with reviewed environment exposure and working sandbox support is still required for a PASS on the complete objective.

**Human delivery acceptance: PENDING.**
