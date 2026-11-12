# AI-SDLC-LITE-019B — Minimal Copilot Skill Installer

## Identity and changes — Observe

- **Approval:** owner mission AI-SDLC-LITE-019B, APPROVED FOR IMPLEMENTATION. The approved mission is the active contract; no additional implementation approval was requested.
- **Baseline:** `e90cb86caaa23d2ef5a184233a909fd192555333`, initially clean, 23 tracked files.
- **Checked snapshot:** baseline plus the four paths listed below. No commit was created.
- **Environment:** Linux x86_64; Python 3.14.9; GitHub Copilot CLI 1.0.109. Commands ran from the framework root unless stated otherwise.
- **Changed:** README.md (installation and Quickstart instructions).
- **Added:** scripts/install_skill.py, tests/test_install_skill.py, this result record. Final project inventory: 26 files, excluding Git metadata.
- **Preserved:** all 22 other baseline files, including the native Skill, WORKFLOW, canonical BOV contracts, qualification records and historical evidence. Target instructions are not overwritten or merged automatically.

The installer uses only Python's standard library, existing Git and optional detection of existing Copilot CLI. The installed entry point adjusts six links to a local `framework/` bundle. Canonical source files remain byte-for-byte copies. Their local Markdown link closure is included, with the MIT license, to avoid introducing broken secondary links. No documents are fetched over the network.

The installed inventory is 24 files: one entry point, 22 dependency files and one ownership manifest. Dependency files include linked examples and historical evidence; they remain reference material. The original nested Skill is part of that link closure; actual CLI discovery verified one enabled project Skill, not two.

## Acceptance evidence — Verify

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. Successful installation | PASS | Native CLI integration installs into a synthetic Git repository with spaces in its path; installer exits 0 and reports READY. |
| 2. All Skill references resolve | PASS | Six entry links resolve; bundled local Markdown link destinations exist; six canonical documents match source bytes. Final Markdown audit also checks anchors. |
| 3. Explicit discovery | PASS | Installer invokes `copilot --no-auto-update skill list --json` with target Git root as cwd; exactly one enabled project entry resolves to the intended installation. No inference request is made. |
| 4. Repeat without unwanted changes | PASS | Unit and native integration checks compare bytes and nanosecond mtimes; second install exits 0 without rewriting files. |
| 5. Overwrite refusal | PASS | Unowned destination, changed installed file and extra file each refuse installation without writes. Expected refusal exit: 1. |
| 6. Project instructions preserved | PASS | Synthetic AGENTS.md and TASK.md retain contents and mtimes; original Git metadata is preserved. |
| 7. Incorrect target/workspace detected | PASS | Missing explicit target exits 2; framework and non-Git targets exit 1; target subdirectory resolves to its Git root. Tests launch from framework cwd but write only into the explicit target. No package/build/test commands are issued by the installer. |
| 8. Unchanged rollback | PASS | Preview changes nothing; uninstall removes unchanged owned files and empty installation directories; repeat uninstall and subsequent reinstall work. |
| 9. Edited files preserved | PASS | Edited and unowned files survive rollback, which exits 1 and retains the ownership manifest. Malformed, escaping and symlink manifests are refused. |
| 10. Scope confinement | PASS | Snapshot assertions cover synthetic project files and Git metadata. Symlink-parent test preserves an outside directory. Development integration also preserved an outside sentinel and hashes of existing Copilot configuration files. |

### Commands and outcomes

```bash
python3 -B -m unittest discover -s tests -p 'test_install_skill.py' -v
python3 -B <codex-skills-dir>/.system/skill-creator/scripts/quick_validate.py .agents/skills/ai-sdlc-lite
git diff --check
git diff -- README.md
git status --short --untracked-files=all
git diff --exit-code e90cb86caaa23d2ef5a184233a909fd192555333 -- . ':!README.md'
git ls-files --cached --others --exclude-standard
```

- Final installer suite: **19/19 PASS**, zero skips, exit 0 (`Ran 19 tests in 1.673s`). The native integration test uses the actual installed CLI; other readiness calls are mocked to isolate filesystem cases. Test fixture creation uses `git init --quiet` only in disposable repositories; no commits or configuration changes are needed.
- Interim suites: 16/16 and 17/17 PASS, exit 0. Later runs were justified by added manifest safety checks and native integration coverage. No failed test attempts occurred.
- One edit patch failed its context match and made no changes; a corrected patch succeeded. This was an editing retry, not a failed verification run.
- Existing native Skill validator: exit 0, `Skill is valid!`. The validator is already installed in this environment; it is not an installer dependency.
- Whitespace check: exit 0 for the tracked diff. New files are also checked for trailing whitespace in final scope validation. Historical whitespace is unchanged.
- Final scope and Markdown audits: **22/22 protected SHA-256 comparisons MATCH**, **exactly 26 project files**, no staging, and **99 local Markdown links/anchors PASS**. The audit compares every protected file against `git show HEAD:<path>`, enumerates tracked plus untracked project files, checks local Markdown paths and heading anchors, and inspects all four changed files. It completed with exit 0. The observed audit window was `2026-11-12T08:59:23.346378+00:00` to `2026-11-12T08:59:23.388314+00:00`; this is a scope-audit window, not task elapsed time. Subsequent edits only complete this evidence record and require its hash/whitespace/status recheck.
- Historical example suites were not rerun: no example code or tests changed. Their prior qualification is reused with its original limitations.

An additional development integration ran nine operations in a retained disposable fixture: preview, install, repeat install, explicit Skill listing, rollback preview, rollback, reinstall, refused overwrite, and edited-file-preserving rollback. Exit codes were `0,0,0,0,0,0,0,1,1`, all expected. Its local JSON includes commands, UTC start/end timestamps, stdout/stderr, environment, and configuration-integrity assertions. It predates the final additional error-handling tests and is supporting evidence only; the final native integration test independently rechecked the delivered installer. Local evidence location is supplied in the owner handoff, not required for public documentation.

## Snapshot hashes

| Implementation file | SHA-256 |
| --- | --- |
| README.md | `37f9d4ea2fe681767e1359b5a9eea534fbf542ac336aea3d3d728434ba76fe8f` |
| scripts/install_skill.py | `ef026385a30cc527c356d602a5076932daf088e2642bed1cad992ba3fb6ca524` |
| tests/test_install_skill.py | `9788b997291a5209d45f06e3591cf4bf91590aeb594b3a4aee17ee848f79764e` |

This evolving record's hash is supplied separately in the handoff. The ownership manifest in an actual installation records each installed file's hash; repeat installation requires exact inventory and byte matches.

## Observations and limitations

- **Outcome:** installation, reference resolution, metadata discovery and safe rollback were exercised. No coding-session behavior, prompt reduction, sandbox enforcement or productivity improvement is established.
- **Time:** full task elapsed time and active agent time are UNKNOWN. The 1.673-second reported test duration covers only the final unittest invocation; development integration records individual operation boundaries, not full task boundaries.
- **Usage:** task/session tokens, provider-billed units and monetary cost are UNKNOWN. No inference session or paid operation was requested. Missing usage is not reported as zero.
- **Retries:** zero failed test attempts; one failed edit-patch attempt. Repeated verification after added checks is identified above.
- Supported locally: Linux, Python 3.14.9, Copilot CLI 1.0.109. Python 3.9+ is the implementation prerequisite; other Python versions, operating systems, CLI versions and organization policies have not been exercised.
- Missing CLI or unverified discovery returns BLOCKED after installing files. Owners may inspect or roll back those files. Dry-run READY describes a preview only.
- No automatic upgrades, permission configuration, user-scope installation or instruction-file merging. Conflicts require an owner decision. The manifest must remain intact; manual manifest tampering is outside the ownership guarantee.
- Do not run concurrent writes against the installation. Symlink checks and exclusive file creation are safeguards, not a substitute for OS isolation against an adversarial concurrent process. Interrupted writes report BLOCKED; modified or partial files are preserved for review during rollback.
- Empty parent `.agents/skills` directories can remain after rollback. User-created files are preserved.
- Touchline and AI Summit Website were not accessed. No dependencies, telemetry, global settings, commits, branches, remotes, pushes, tags or releases were added or changed.
- Public release blockers and historical qualification limits remain unchanged.

## Outcome and human acceptance

- **Technical outcome:** PASS for the approved installer scope in the inspected environment.
- **Deploy:** NOT PERFORMED; no release action authorized.
- **Next action:** owner reviews the four-file snapshot and decides delivery acceptance. Any field retest requires its own bounded authorization.
- **Human delivery acceptance:** PENDING.
