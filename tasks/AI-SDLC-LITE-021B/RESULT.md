# AI-SDLC-LITE-021B — Installer Recovery & Safe Uninstall

## Identity and authorization

- **Approval:** owner mission AI-SDLC-LITE-021B, IMPLEMENT → VERIFY → OWNER REVIEW. The mission authorizes these bounded changes and checks; no repeated BOV approval was requested.
- **Baseline:** 32-file working snapshot on e90cb86caaa23d2ef5a184233a909fd192555333, including existing uncommitted work. This task does not turn that work into a committed release baseline.
- **Changed:** scripts/install_skill.py, README.md.
- **Added:** tests/test_installer_recovery.py, this record. Final intended project inventory: 34 files.
- **Protected:** 30 other starting files, including existing tests, canonical BOV contracts, micro-cycle guidance, source Skill and historical evidence.
- **Environment:** Linux x86_64, Python 3.14.9; existing Copilot CLI 1.0.109 used only for installation/discovery metadata in isolated fixtures. No authenticated model task, field-repository access, dependency installation or permission repair occurred.

## Implementation

Recovery now validates the explicit Git target and applicable CLI arguments first. Uninstall validates its installation path and manifest; configuration rollback validates its original-state backup, target, symlinks and installed hashes. Both dispatch before task-context, package metadata or development-tool preflight. Normal installation still performs its existing workspace/preflight checks.

The existing format-1 ownership manifest remains authoritative. Structural validation now requires the entry point, six canonical document entries and license, and rejects paths that claim both a file and its descendant. Existing generated manifests already contain those entries. Absolute, traversal, malformed and symlink paths remain refused before removal.

Uninstall previews every removable file, retained entry, manifest action and empty owned directory. Only unchanged manifest-owned files are deleted. Changed files, extra files and unowned empty directories are preserved with BLOCKED and a retained manifest. Repeated partial uninstall makes no further changes to retained content; repeated uninstall of an absent installation succeeds. Project files and active task history outside the Skill are never removal candidates. Known parent .agents/skills directories remain.

Before deletion, the planned scope is checked for writable parent directories. An unwritable/read-only scope reports BLOCKED before removals; no chmod, shell deletion, remount or bypass is used. This check does not eliminate concurrent filesystem races. Stop other writers during installation/recovery.

Skill uninstall explicitly reports configuration restoration NOT PERFORMED. Separate configuration rollback still requires verified original-state evidence and matching current hashes. Missing backups or later user edits remain BLOCKED, without invented restoration or lost user settings.

## Acceptance evidence

| Criterion | Result | Evidence |
| --- | --- | --- |
| Recovery dispatch corrected | PASS | Stale task context and malformed package JSON no longer prevent uninstall or verified settings rollback; recovery tests assert preflight is not called |
| Ownership and path safety | PASS | Missing/corrupt/incomplete manifests, overlapping/traversal/absolute paths and symlinks refuse removal before writes |
| Later-edit protections | PASS | Modified installed files and later settings edits survive; manifests/backups retained when needed |
| Exact preview | PASS | Dry-run file removal list equals installed file inventory; owned-directory actions are shown; no writes occur |
| Repeated uninstall/reinstall | PASS | Absent uninstall succeeds repeatedly; partial uninstall preserves edits repeatedly; install → uninstall → reinstall succeeds |
| No unrelated changes | PASS | 30/30 protected hashes MATCH, exact 34-file inventory, HEAD unchanged, no staging; project/history and outside sentinel preserved; global configuration hashes unchanged in isolated integration |
| Existing installation/permission behavior | PASS | Full suite includes all 48 preceding tests unchanged plus 13 new tests |
| Human acceptance | PENDING | Separate explicit owner decision required |

## Commands and outcomes

Working directory: framework repository root.

```bash
python3 -B -m unittest discover -s tests -p 'test_installer_recovery.py' -v
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .agents/skills/ai-sdlc-lite
git diff --check
git status --short --untracked-files=all
```

- Focused recovery suite: **13/13 PASS**, exit 0, reported duration 0.305 seconds.
- Full suite: **61/61 PASS**, no skips, exit 0, reported duration 34.085 seconds. All existing test files retain their baseline bytes.
- Native source Skill structure validator: **Skill is valid!**, exit 0. Source Skill remains unchanged; read-only mounts were not bypassed.
- Final scope audit: 30/30 protected hashes MATCH, exactly 34 files, four intended changed/added paths, HEAD unchanged and nothing staged. All 100 local Markdown links/anchors and four-file whitespace checks passed, exit 0.
- No failed test attempts. Expected refusal return codes in negative tests are asserted outcomes, not unsuccessful retries.
- An initial read-result parser failed because its oversized command output was truncated. A bounded baseline-only read succeeded before edits; no files were changed by that orchestration failure.

## Isolated real-command demonstration

One retained disposable Git repository, private test Copilot home/cache, synthetic project file, package JSON, history record and outside sentinel were used. The driver records exact argv, cwd, UTC timestamps, stdout/stderr and exit codes in local integration evidence. No authentication or model task was requested.

| Invocation | Outcome / exit |
| --- | --- |
| Install | PASS / 0 |
| Uninstall preview with stale context and malformed package | PASS / 0; no change |
| Uninstall despite stale metadata | PASS / 0; Skill removed; project/history/metadata preserved |
| Repeat absent uninstall | PASS / 0; no change |
| Configuration rollback without backup | Expected BLOCKED / 1; settings unchanged |
| Normal install while task metadata remains stale | Expected BLOCKED / 1; normal validation preserved |
| Restore only synthetic fixture metadata, then reinstall | PASS / 0 |
| Modify an installed reference, then uninstall | Expected BLOCKED / 1; unchanged owned files removed, edited reference/manifest retained |
| Repeat partial uninstall | Expected BLOCKED / 1; retained content unchanged |

All nine observed codes were `0,0,0,0,1,1,0,1,1`, as expected. Original synthetic project and history bytes, outside sentinel, original test settings and global config/settings/permissions hashes were preserved. Final partial installation is retained for owner review. Configuration backups containing real secrets were not read or copied.

## Micro-cycle observations

The agent declared a 15-minute execution window; timing is advisory. No timeout controller, forced cancellation or uncontrolled service was introduced. Cycle checkpoints were reported without asking again for approval.

| Cycle | Measured boundaries UTC | Elapsed | Result |
| --- | --- | --- | --- |
| 1 — inspect/baseline | 17:07:38.163500 → 17:08:01.717687 on 2026-11-12 | 23.554187 seconds | PASS |
| 2 — code and focused tests | 17:08:01.717687 → 17:11:46.656188 | 224.938501 seconds | PASS |
| 3 — regressions and real fixture | 17:11:46.656188 → 17:15:16.500084 | 209.843896 seconds | PASS |
| 4 — scope/evidence/handoff | 17:15:16.500084 → 17:18:06.472364 | 169.972280 seconds | PASS |

Cycle targets are three minutes, with a five-minute maximum. Cycles 2/3 exceeded the target but stayed below the maximum. The start-to-final-verification window was 628.308864 seconds, inside the declared 15-minute execution budget. Checkpoint timing includes waiting and transition time within the observed window; later evidence-record completion/final response are excluded. Full task elapsed time, active agent time, tokens, billed units and monetary cost are UNKNOWN. No model call was made; this is not a measured zero-cost/token claim.

## Snapshot and limits

| Implementation file | SHA-256 |
| --- | --- |
| README.md | eb69810722c294530d93b33c3ecb336cf955fbef603eec69b6e3ef4f156c96bb |
| scripts/install_skill.py | ba29fba9cfea5f7f870a661da34940039237001c7399ffba89855a327839b473 |
| tests/test_installer_recovery.py | e0640de3f541e2161d50362cb147c1de43d7d901fa75a6929f7b37833f8589d4 |

The evolving result record's hash is supplied separately. No automatic cleanup outside installer-owned paths or configuration restoration without backup is claimed. A manifest is local ownership evidence, not a signed attestation; keep it intact. Unsupported permissions, filesystem races or interrupted operations can still require owner review. No promise of Copilot runtime confinement or prompt reduction is added.

**Technical outcome: PASS for this recovery/uninstall scope.** Public release blockers and prior unqualified autonomy behavior remain unchanged.

**Human delivery acceptance: PENDING.** No commits, pushes, tags, releases or deployment were performed or inferred as authorized.
