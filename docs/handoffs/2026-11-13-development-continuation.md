# AI-SDLC-Lite — Development handoff (2026-11-13)

Status: **handoff only; no implementation or merge authorized**.

## Objective
Develop **AI-SDLC-Lite as the framework**, with the private ITJ-Labs/6DOF-Robotic-Arm project as a real-world, software-only validation pilot. The Skill is a distribution/interface mechanism, **not** the primary deliverable. Framework should govern Bound → Observe → Verify, record reproducible evidence and improve from pilot findings. Respect project-specific instructions and hardware safety boundaries.

## Public consolidation
- Canonical repository: `mmontielpz/ai-sdlc-lite`, `master` at `d9f1ba3faa789a6fab4bd71777635108dab4e978`.
- PR #1 merged the sanitized consolidation commit `2a546317c6d9243bd946e148e31870be3367c237`; 52 paths (45 added, 7 modified).
- PR and master CI: Python 3.9 and 3.14 successful, 202 tests with 2 skips per CI job.
- The public G5 original commit `9e08e27` and the GitHub-generated merge commit `d9f1ba3` contain the owner's personal email in commit metadata. **Do not repeat or publish that address in reports.** No history rewrite approved. GitHub email privacy settings remain unverified.
- Public experimental branches `experiment/consolidation-g5-ci` and `experiment/consolidation-g5-identity-fixed` still exist; do not delete without explicit approval.

## Linux workstation
- **Active public checkout:** `~/Development/Open-Source/ai-sdlc-lite`, clean `master` at `d9f1ba3`, SSH origin `git@github.com:mmontielpz/ai-sdlc-lite.git`.
- **Additional public checkout:** `~/.copilot/repos/ai-sdlc-lite`, clean at `d9f1ba3`; HTTPS origin unchanged.
- **Legacy private checkout:** `~/repos/ai-sdlc-lite`, private `ai-sdlc-lite-dev`, `develop` at `1eac1f6`, **6 dirty entries**. Do not reset, clean, delete, re-point or overwrite.
- `~/.copilot/skills/ai-sdlc-lite/SKILL.md` was updated from public master and byte-compared to canonical Skill (SHA256 prefix `b1438234`); `copilot skill list` confirms registration only.
- `~/.copilot/config.json` now trusts the new public workspace; old trust entry retained. `permissions-config.json` **not migrated**; leave approval prompts intact. Live session trust and Skill activation are **not yet verified**.
- Local Python 3.14.9 unittest discovery ran 202 tests with zero skips, whereas CI skipped two because Copilot CLI unavailable there. Explain discrepancy using actual test conditions before treating it as a defect.

## Private retirement and backups
- Legacy private 77 tracked paths all accounted for in G5 (62 identical, 15 reviewed); no missing framework implementation. Some Codex adapter README local compatibility evidence could be restored later as a separate sanitized change.
- Verified private Git bundle plus six dirty/untracked file backups at `/home/mike/ai-sdlc-lite-retirement-private/RETIRE-006-20261114T021226Z/`; bundle SHA256 `3eeeea9108e8fd526778a06e302577bbb3a54af05ca4edc4208c9c388e70dc4a`. Bundle restore, refs, 13 commits and dirty-file checksums passed.
- Backup remains on same workstation only; **second independent/off-machine verified copy pending**.
- Private history scan was regex-based only, not scanner-grade. GitHub email privacy configuration unverified. Do **not** archive/delete private repo yet.
- Keep backups and private evidence out of public Git.

## Immediate next mission: LIVE-QUALIFICATION-009
Run in an interactive Copilot CLI session from the **Linux public checkout**, not the Mac or private checkout.

1. Confirm working directory, clean tree and expected public HEAD.
2. Verify Copilot recognizes the new trusted folder without overriding approval prompts.
3. Confirm Skill registration and explicitly invoke its documented activation method.
4. Gather **observable evidence** of Skill loading (not merely agent self-report).
5. Execute one read-only BOV task: declare bounds, inspect relevant files/tests, verify evidence and report status/limitations.
6. Confirm no file/Git changes. Classify any gap as framework, adapter, project-specific or documentation/DevEx.
7. Report `STATUS=PASS|PARTIAL|BLOCKED`, `SKILL_DISCOVERY`, `SKILL_ACTIVATION`, `ACTIVATION_EVIDENCE`, `BOUND`, `OBSERVE`, `VERIFY`, `WORKTREE_UNCHANGED`, `FRAMEWORK_GAPS`.

**Restrictions:** no writes, commits, pushes, merges, permission escalation, paid inference beyond the authorized session, or hardware/BLE/firmware/servo operations.

## Next after live qualification
- Validate backup on an independent device, check GitHub email privacy, and decide legacy private archival and experimental branch cleanup with owner approval.
- On Mac, use public framework checkout and the existing **dirty** private `ITJ-Labs/6DOF-Robotic-Arm` project; locate and verify paths rather than assuming Linux paths. Do not modify the robotic repo until a read-only baseline audit.
- Pilot progression: E01 discovery/instruction hierarchy; E02 bounded execution and dirty-tree preservation; E03 existing test/CI and evidence; E04 feedback to framework; E05 Claude Code/Codex portability.
- Never actuate physical hardware, flash firmware, connect BLE/serial or weaken physical safety controls without separate explicit authorization.

## Handoff integrity
This PR contains documentation only. It is intentionally **draft** and must **not be merged** until the owner reviews it. The public repository is the only active source of truth; no second development repository should be created.
