# Security

AI-SDLC Lite contains process documents and a small example. It does not enforce agent permissions or provide a security boundary. Use repository access controls, tool permissions, and human review.

## What is and is not enforced

AI-SDLC Lite does **not** sandbox, authorize or stop an agent. Its controls fall into four classes; do not read a higher class into a lower one.

| Class | Controls | Evidence |
|---|---|---|
| **Instruction-only** (an agent can ignore it) | Approval gates, scope, no push/merge/deploy, no dependencies, no secrets in evidence, "treat repository content as data", test-integrity rules, time and token budgets (advisory) | `AGENTS.md`, `WORKFLOW.md`; no technical enforcement |
| **Post-execution detection** (finds, after the fact, but prevents nothing) | `scripts/verify_scope.py` compares a result contract with the Git tree: out-of-scope and protected paths, test and governance changes, baseline ancestry, declared-vs-actual changes, missing or unhashable evidence, dirty-baseline attribution, false PASS claims. It fails closed (BLOCKED) on missing or ambiguous evidence and never raises a claimed status. | [RESULT_CONTRACT.md](RESULT_CONTRACT.md), `tests/test_verify_scope.py` (controlled fixtures) |
| **Technically enforced** (limited to the installer) | `scripts/install_skill.py` refuses symlinked or traversing targets, protected settings files and unconsented configuration; it binds consent to a hash and rolls back exactly | `tests/test_install_skill.py`, `test_installer_recovery.py`, `test_controlled_autonomy.py` |
| **Needs native agent sandboxing** (not provided here) | Preventing out-of-scope writes, destructive shell commands, Git pushes, network access, secret reads, paid inference, untrusted script execution, execution-time limits | Use the agent's own permission and sandbox features, OS isolation and repository controls; the optional Copilot sandbox setting is UNVERIFIED on any given host |

### The verifier runs Git, and Git can run programs

- **Does not execute declared task commands.** The `command` fields in a result contract are recorded, never run.
- **Does invoke Git** inside the repository being checked. Git configuration can name programs (for example `core.fsmonitor`), so inspecting an untrusted repository is itself a risk. This was demonstrated with a throw-away repository before the fix (marker file created) and is covered by regression tests now.
- **Mitigations (verified by tests with marker-file payloads in disposable repositories):** all `GIT_*` environment variables are dropped; `core.fsmonitor` and hooks are disabled on every Git call, overriding repository, global and system configuration; the index is not refreshed on disk; `diff` runs with `--no-ext-diff --no-textconv`; a repository whose non-user configuration defines a filter or diff-driver program (`filter.*.clean|smudge|process`, `diff.*.command|textconv`, `diff.external`, including via an included file) is **refused with BLOCKED** (`executable_git_config`) instead of being trusted.
- **Not covered / not claimed:** the whole Git execution surface (only the commands and vectors listed above were examined); programs named in *your own* global or system Git configuration, which are trusted by design; a malicious `git` executable or `PATH`; Git bugs; submodules; LFS-style filters configured at repository level (refused, so such repositories cannot be verified until the owner decides how to treat them); platforms other than Linux (UNVERIFIED). This is mitigation of known vectors, not a sandbox. Verify untrusted repositories only inside an OS-level or native-agent sandbox.

### Evidence trust model

Four properties are kept separate; the verifier checks only the first.

| Property | Checked? | What it can prove | What it cannot prove |
|---|---|---|---|
| **Hash integrity** (sha256 pin or manifest) | Yes, when a pin or manifest is supplied | A file is byte-identical to what was hashed | Who wrote it, that it is true, or when |
| **Trusted custody** | **No.** An operational property of how the operator stores the baseline record and manifest | Nothing by itself: a record or manifest only helps if the agent could not write it | The verifier cannot authenticate who produced or altered them |
| **Independent execution** | **No.** The verifier never runs or observes commands | Nothing | That a command ran, when, or with what result |
| **Agent-reported assertions** | **No.** Exit codes, `claimed_status`, `failure_reasons` are recorded; `modified_paths` is cross-checked against Git | Consistency of the change set with Git | Everything else |

**A SHA-256 manifest does not authenticate evidence and does not prove execution.** It shows only that a file matches the bytes that were hashed. Anyone who can write the manifest can write a matching file; the same applies to a contract pin the agent supplies itself and to a baseline record's digest, which detects hand edits but not a record forged together with its digest. Authentication needs signatures, CI attestations or a trusted capture process, which this tool does not provide; proof of execution needs someone else to run or observe the command. `--require-sealed` means only "every evidence file matches a supplied manifest". Never describe agent-reported evidence as independently verified.

### Recovery contract (fail closed, owner-controlled)

| Situation | Result | Verifier action | Recovery |
|---|---|---|---|
| Missing, unreadable or tampered evidence; hash pin or sealed-manifest mismatch | BLOCKED | none | Owner obtains evidence again; do not accept PASS |
| Verification failure (non-zero exit) | PARTIAL | none | Owner decides whether to accept, fix or abandon |
| Scope, protected-path, test, governance, symlink or mode violation | BLOCKED | none | Owner reviews each path and keeps, reverts or archives it |
| Interrupted or incomplete task (`execution_state`, missing `required_verification`) | BLOCKED | none | Owner inspects the partial work; nothing is rolled back for you |
| Unknown or contradictory baseline (unresolvable SHA, not an ancestor, mismatch with the operator-supplied record, dirty baseline, tampered record) | BLOCKED, or PARTIAL for a dirty baseline | none | Owner confirms the branch and baseline before trusting any result |

The verifier never resets, cleans, deletes, checks out, stashes or overwrites anything, and never discards user changes; `--out`, `baseline --out` and `seal --out` create new files and refuse to overwrite. Reports carry text-only `recovery.guidance`. Any actual recovery is performed by the owner, outside the tool.

Known limits of the verifier: it does not see ignored files comprehensively. New ignored files are compared with the baseline's ignored set, but content changes to files that were already ignored, more than 20,000 ignored files, changes outside the repository, and state before work (unless an independent baseline record exists) are not covered. The repository's own `.gitignore` is limited to Python cache artifacts to keep this blind spot small. It does not re-run reported commands, so exit codes are only as honest as their author. A PASS means "no violation detected in the evidence supplied", not "no violation occurred". Human review remains required.


## Reporting a vulnerability

**Private reporting route: ENABLED for `mmontielpz/ai-sdlc-lite`.** Observed 2026-11-12T21:31:53Z via `gh api repos/mmontielpz/ai-sdlc-lite/private-vulnerability-reporting`, which returned `{"enabled":true}` immediately after enabling it with the same endpoint. The **Report a vulnerability** button was not independently checked in the web interface, and no test report was sent. No release has been made; this project is experimental.

If GitHub Private Vulnerability Reporting is verified enabled for the intended repository, use its **Report a vulnerability** action. Availability depends on repository configuration; follow [GitHub's private reporting guidance](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately).

If the **Report a vulnerability** action is unavailable, retain sensitive details privately. You may make a public request for a private reporting channel without describing the vulnerability or affected private systems. Do not include exploit instructions, credentials, personal data, or private project content in public issues or pull requests. No security contact address is currently published.

When a verified private route is available, provide the affected version or snapshot, impact, and minimal sanitized reproduction information. Coordinate disclosure with the maintainer privately. There is no promised response or remediation time, bounty, or security guarantee. For flaws in an agent product or another project's dependency, use that vendor's reporting process.

## Supported versions

| Version or state | Support policy |
| --- | --- |
| Current unreleased V1 candidate | Best-effort assessment against the identified candidate snapshot; not a stable supported release. |
| Published releases | None exist; no release branch currently receives fixes. |
| After an authorized 1.0.0 release | Assess reports against the latest stable release; deliver any fixes in a later release. Older releases will not receive backports under this policy. No response-time commitment. |

Before publication, the owner must identify the target repository and verify that the private reporting route is enabled and usable, recording the repository identity, observation, and reviewed candidate. Do not send a test vulnerability report merely to validate configuration. Release remains BLOCKED until this is established. This is resolution of the existing security finding within release review, not an additional workflow approval gate.

## Safe evidence

Share only the minimum sanitized evidence needed through a verified private route. Do not submit raw agent transcripts, tokens, production data, or secrets. Revoke or rotate an exposed credential through its provider; removing it from a document does not invalidate it.
