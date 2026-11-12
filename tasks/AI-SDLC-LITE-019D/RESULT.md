# AI-SDLC-LITE-019D — Copilot Workspace Setup

## Identity and changes — Observe

- **Authorization:** owner mission AI-SDLC-LITE-019D, AUDIT → DESIGN → IMPLEMENT → VERIFY. The mission authorizes this bounded implementation; no missing R1 approval is inferred.
- **Baseline:** 019B working snapshot on `e90cb86caaa23d2ef5a184233a909fd192555333`, including its existing uncommitted README, installer, tests and historical result record.
- **Changed this slice:** README.md, scripts/install_skill.py, tests/test_install_skill.py; added this result record. Project inventory: 27 files.
- **Preserved:** 22 baseline tracked files outside README plus the original 019B result record (23 protected files). Canonical contracts and native source Skill remain unchanged. Installed entry points receive context-navigation guidance only.
- **Environment:** Linux x86_64, Python 3.14.9, GitHub Copilot CLI 1.0.109. All repository/configuration mutation tests used disposable repositories and isolated COPILOT_HOME and COPILOT_CACHE_HOME directories. Neither field-experiment repository was accessed.

## Configuration compatibility findings

| Capability | Finding | Evidence and boundary |
| --- | --- | --- |
| Workspace selection | PASS | `copilot -C` selects the target. Installer reports its Git root, changes, writability, task context and launch command. |
| Ancestor instruction detection | PASS | Root/ancestor AGENTS.md paths are reported without reading, moving or changing their contents. Detection does not establish native loading. |
| Parent file-only CLI path grant | BLOCKED | Saved `allowed_directories` accepts directories, not individual files. No parent-directory grant is created. File-tool rules do not independently satisfy the path gate. |
| Repository-local permission settings | BLOCKED | Actual CLI rejected `permissions.allow` and `sandbox.userPolicy.filesystem.readonlyPaths` with `config --local`, exit 1. No substitute fields were invented. |
| Additional instruction directories | UNVERIFIED / unused | CLI error output advertised `instructionDirectories` as overridable, but attempts to set/read it returned Unknown settings key, exit 1. It is not implemented. |
| Explicit sandbox profile opt-in | PASS for configuration | An explicit existing absolute Copilot home is required. Only sandbox.enabled, sandbox.allowBypass and optionally exact ancestor-file readonlyPaths are changed. Real CLI config reads recognize those values. |
| OS sandbox operation | BLOCKED for qualification here | bwrap is present, slirp4netns is missing. No sandbox command execution was attempted, no prerequisites installed, and no enforcement claim is made. Copilot may warn/fall back on unsupported unmanaged hosts; settings acceptance is not enforcement. |
| Automatic R1 approval recovery | BLOCKED without source | No original approved R1 brief was supplied. Initialization creates pending templates or references an explicitly named existing in-repository contract; it never reconstructs or approves one. |

The [official configuration reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) separates user settings, managed state and location-scoped permissions. Settings can be isolated with COPILOT_HOME. Saved directory grants are broader than a file and saved read approvals have no path field. [Instruction documentation](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions) describes native discovery locations; it does not guarantee arbitrary ancestors are loaded. These sources were cross-checked with local 1.0.109 help and isolated probes.

## Implemented behavior

- `--check` verifies workspace/task paths and the installed Skill's ownership inventory/hashes, then checks native enabled project Skill discovery.
- `--init-task ID` creates TASK, CHECKLIST and RESULT records using existing framework templates under tasks/ID, plus an explicit task-context pointer. Shared README links are rebased to bundled documentation. All new approvals remain PENDING.
- `--task-contract relative/path.md` references an existing target contract without changing it. Root records and project instructions remain untouched. Conflicts, escapes, bundled templates and missing contract files are refused. Repeat initialization preserves later record edits. Records remain after Skill uninstall.
- `--configure-copilot --copilot-home /explicit/path` opts in to sandbox settings, previews changed keys/destinations and backs up original settings in that selected home. Optional `--read-instruction /exact/parent/AGENTS.md` adds only that regular ancestor file as a sandbox read-only path.
- No tool, directory, write, shell or URL approvals are added. Configuration affects sessions using the selected Copilot home, not just one repository. Existing user grants/settings are preserved, not certified safe or reduced by this operation.
- `--rollback-config` restores exact previous bytes or prior absence only when settings still match the recorded installed hash. Later edits are retained with BLOCKED. Backups are private, remain local, and can contain sensitive settings; their contents are not included in evidence. JSONC, symlinks and conflicting backups are refused.
- Old 019B bundles are not silently upgraded. Owners review and uninstall unchanged bundles before reinstalling; active task records remain separate.

## Verification commands and results

Working directory: framework repository root.

```bash
python3 -B -m unittest discover -s tests -p 'test_install_skill.py' -v
python3 -B <codex-skills-dir>/.system/skill-creator/scripts/quick_validate.py .agents/skills/ai-sdlc-lite
git diff --check
git diff -- README.md
git status --short --untracked-files=all
```

| Check | Actual result | Exit |
| --- | --- | --- |
| Final installer suite | 29/29 PASS, no skips; Ran 29 tests in 5.513s | 0 |
| Existing native Skill validator | Skill is valid! | 0 |
| Changed-file whitespace and Markdown audit | Four changed files PASS; 99 local links/anchors PASS; exact 27-file inventory, no staging | 0 |
| Protected file comparison | 23/23 MATCH against baseline tracked bytes and original 019B result hash | 0 |
| Explicit Skill discovery | Real CLI discovers enabled project Skill in disposable repository | 0 |
| Settings compatibility | Real CLI config reads return true, false and the exact synthetic ancestor file path | 0 |
| Negative cases | Expected exit 1 for conflicts, unsafe paths, missing opt-in, JSONC, symlinks and changed-settings rollback; missing --target exits 2 | Expected |

The 29 tests include fresh installation, a modified repository, parent detection, native discovery, existing canonical bytes, file references, task initialization/reuse/conflicts, idempotency, configuration preview/backup/rollback, exact previous-byte restoration, rollback to absence, later-edit preservation, and no added tool/directory permissions. A first 29/29 run passed before README updates; the final rerun checked the changed dependency bundle. No test failure occurred.

Configuration probes intentionally received CLI rejection exit codes. One probe then tried to display the nonexistent rejected settings file, raising FileNotFoundError and exiting 1. It made no settings change; the unsupported option was discarded. This failure is retained rather than treated as successful configuration.

## Actual prompt observations

A fresh disposable Git repository and isolated Copilot home were used for one bounded interactive launch:

```bash
env COPILOT_HOME=<isolated-home> COPILOT_CACHE_HOME=<isolated-cache> copilot --no-auto-update -C <disposable-repository>
```

| Category | Observation | Counting window |
| --- | --- | --- |
| Folder trust | 1 displayed Confirm folder trust dialog | Launch through Escape cancellation |
| Parent/external path | NOT REACHED / UNKNOWN | No task started |
| Read-tool approval | NOT REACHED / UNKNOWN | No task started |
| Edit/write approval | NOT REACHED / UNKNOWN | No task started |
| Shell/external command approval | NOT REACHED / UNKNOWN | No task started |
| Authentication/model usage | NOT EXERCISED | No login or model prompt submitted |

Escape canceled the trust dialog; CLI exited 1 as expected. No trust decision or persistent permission was granted. The captured prompt is sanitized and retained locally; no full historical session log was opened. Global config.json, permissions-config.json hashes and absence of settings.json matched before/after this isolated UI window.

Prompt reduction is UNKNOWN. This short startup observation is not comparable with earlier screenshot-derived reconnaissance/coding observations. No zero-prompts claim is made.

## Snapshot and measurements

| Implementation file | SHA-256 |
| --- | --- |
| README.md | `1c706f82cfef4934ccd278fa454a5769700bf1936fcdb688ae2404b72a654f67` |
| scripts/install_skill.py | `38cf0308e2b1e36a827d0033f4898e781e3e9d59e57ce1b6c27db5ed93adb407` |
| tests/test_install_skill.py | `e571626e4d635b3a0df46d66d0687ce6eb04b95198c70b7531f5e6d74cd24ef2` |

This record's final hash and final scope audit are supplied in the handoff. Historical 019B evidence remains byte-for-byte unchanged and describes its earlier snapshot.

Full task elapsed time, active agent time, task tokens, billed units and monetary cost are UNKNOWN. The 5.513-second final test duration covers only that unittest invocation. Verification failures and deliberate negative cases are distinguished above; no inference task was submitted.

## Outcome and owner review

- **Overall:** PARTIAL. Supported workspace/context setup and configuration storage/rollback passed. Parent file-only CLI grants are BLOCKED; actual OS sandbox enforcement and end-to-end prompt reduction remain unqualified.
- **Constraints:** no field-repository access/edits, global permission grants, dependencies, commits, pushes, tags or releases. Canonical BOV contracts and both human decisions remain unchanged.
- **Next action:** owner review of this four-file slice. Supply the exact authoritative R1 contract path before any field resume. Host sandbox prerequisites and a separately bounded task session are needed to qualify enforcement or prompt behavior; broad parent access is not proposed.
- **Human delivery acceptance:** PENDING.
