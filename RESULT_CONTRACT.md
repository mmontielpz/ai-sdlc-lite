# Machine-readable result contract

Optional companion to [RESULT.md](RESULT.md). `scripts/verify_scope.py` compares this JSON with the Git working tree **after** work. It is detection, not prevention. It **does not execute the commands recorded in the contract**, but it **does invoke Git** in the target repository, and Git configuration can introduce execution risks. Mitigations and remaining limits: [SECURITY.md](SECURITY.md#the-verifier-runs-git-and-git-can-run-programs). It is stdlib-only Python 3 plus Git, with no network.

```bash
# BEFORE the task, by a human or CI (not the agent); store the record OUTSIDE the repository:
python3 -B scripts/verify_scope.py baseline --repo /path/to/repo --out /safe/place/baseline.json
# AFTER the task, by a human or CI: record the evidence files' hashes in a manifest (refs are recorded as spelled):
python3 -B scripts/verify_scope.py seal --out /safe/place/manifest.json out.txt ...
# Verify (the optional inputs add hash-integrity checks only, see "Evidence contract" below):
python3 -B scripts/verify_scope.py verify --repo /path/to/repo --result result.json [--out report.json] \
    [--baseline-record /safe/place/baseline.json] [--evidence-manifest /safe/place/manifest.json] [--require-sealed]
python3 -B scripts/verify_scope.py codes      # print the stable failure-code registry
# exit 0 PASS, 1 PARTIAL, 2 BLOCKED (any error or ambiguity is BLOCKED, including a repository whose
# local Git configuration defines a filter or diff-driver program: code executable_git_config)
```

| Field | Required | Meaning |
|---|---|---|
| `schema` | yes | `ai-sdlc-lite-result/1` |
| `task_id` | yes | `[A-Za-z0-9._-]{1,64}` |
| `baseline_sha` | yes | full 40/64-hex commit id; must exist and be an ancestor of `HEAD` |
| `baseline_dirty_paths` | yes | paths already changed before work (`[]` = recorded clean); non-empty caps the result at PARTIAL |
| `allowed_paths` | yes | globs (`*` within a directory, `**` across); no absolute paths or `..` |
| `allowed_sensitive_paths` | no | explicit approval for test and governance files; `allowed_paths` alone never covers them |
| `protected_paths` | no | any change is BLOCKED, even if also allowed |
| `modified_paths` | yes | what the agent says it changed; must equal the actual change set |
| `verification` | yes | list of `{command, exit_code (int), evidence (file)}`; commands are recorded, not re-run |
| `evidence_refs` | no | extra evidence files, hashed (sha256) in the report |
| `claimed_status` | yes | `PASS`/`PARTIAL`/`BLOCKED`; the final status is the worse of this and the computed one, never better |
| `failure_reasons` | no | agent-reported strings, echoed separately and never trusted |
| `baseline_ignored_paths` | no | ignored, untracked files present before work (from `baseline`). When present, **new** ignored files outside `ignorable_paths` or `allowed_paths` are BLOCKED; when absent, any ignored file outside `ignorable_paths` caps the result at PARTIAL (`ignored_baseline_unknown`) |
| `ignorable_paths` | no | globs of ignored artifacts the task may create (for example `**/__pycache__/**`); never overrides `protected_paths` |
| `required_verification` | no | exact `command` strings from the approved plan; any not recorded is BLOCKED (`required_check_missing`), which exposes skipped or interrupted verification |
| `execution_state` | no | `complete`, `in_progress` or `interrupted`; anything but `complete` is BLOCKED (`incomplete_execution`). An agent should write `in_progress` first and `complete` last |
| `verification[].sha256` | no | pins an evidence file's hash; a different file is BLOCKED (`evidence_hash_mismatch`) |

Evidence files must be regular, non-symlink files inside the repository or next to the result file. A result or evidence file inside the repository counts as a change unless allowed (the result file and `--out` are excluded automatically).

Built-in sensitive patterns: tests (`tests/`, `test_*.py`, `*_test.py`, `*.test.*`, `*.spec.*`, `conftest.py`) and governance files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `SECURITY.md`, `CODEOWNERS`, `.github/`, `.agents/`, `.claude/`, `.githooks/`, `.gitignore`, `.gitattributes`).

Symlinks, submodules and file-mode changes (including an executable bit) are BLOCKED unless the path is in `allowed_sensitive_paths` (`special_file_change`).

**Ignored files.** New ignored files are detected by comparing the ignored set with the baseline's. Not detected: content changes to files that were already ignored, and more than 20,000 ignored files (PARTIAL, `ignored_listing_truncated`). Coverage is not comprehensive.

**Baseline record.** `baseline` writes a record with the SHA, dirty paths and their hashes, ignored paths and a digest, and refuses to write inside the repository or over an existing file. With `--baseline-record`, the contract's `baseline_sha`, `baseline_dirty_paths` and `baseline_ignored_paths` must equal the record (`baseline_record_mismatch`), so an agent cannot claim a clean baseline the record contradicts; the report lists dirty files that changed since the record. The digest detects hand edits only: a record forged together with its digest is not detectable, so store it where the agent cannot write.

## Evidence contract: four different things

The report keeps these apart (`trust` and `evidence[]`). Only the first is ever checked.

| Property | What the verifier does | Report value |
|---|---|---|
| **Hash integrity** | Compares each evidence file's sha256 with a contract pin and/or a manifest recorded by `seal`. Detects modification after hashing. | `evidence[].integrity`: `unchecked`, `pinned`, `sealed`, `pinned+sealed` or `mismatch`; `trust.hash_integrity`: `none`, `partial` or `all` |
| **Trusted custody** | Nothing. Custody is an operational property: the baseline record and manifest only mean something if they were produced and stored where the agent could not write. The verifier cannot authenticate who wrote them. | `trust.custody`: always `unauthenticated` |
| **Independent execution** | Nothing. The verifier never runs or observes any command, so it cannot know that a command ran, when, or with what result. | `trust.independent_execution`: always `not verified`; `evidence[].execution`: `not-verified` |
| **Agent-reported assertions** | Records them. `modified_paths` is cross-checked against Git; the rest is not checked. | `evidence[].origin`: `agent-reported`; `trust.agent_assertions`: `unverified` (exit codes, `claimed_status`, `failure_reasons`) |

**A SHA-256 manifest does not authenticate evidence and does not prove execution.** It proves only that a file is byte-identical to what was hashed. Whoever can write the manifest can write a matching file. The same holds for a pin, which the agent supplies itself, and for the baseline record's digest, which detects hand edits and not a record forged together with its digest. Real authentication needs something this tool does not provide (signatures, CI attestations or a trusted capture process), and proof of execution needs the command to be run or observed by someone else. `--require-sealed` therefore means "every evidence file matches a supplied manifest" (PARTIAL otherwise) and nothing stronger. A PASS means no violation was detected in the supplied evidence.

**Recovery is owner-controlled.** The verifier never resets, cleans, deletes, checks out or overwrites anything; `--out` creates a new file and refuses to overwrite. A non-PASS report includes `recovery.guidance` (text only) naming what to review, and `recovery.automatic_recovery` is always `none`.

## Failure-code registry (stable)

Reports carry `registry_version` (currently `1`). Within a registry version a code never changes meaning or its allowed severities; new codes may be added, and a removed code is never reused. The code list is `FAILURE_CODES` in `scripts/verify_scope.py` (`verify_scope.py codes` prints it); tests require every code to be emitted by the code, documented here, and shown in a golden report in `tests/golden/`.

| Code | Severity | Meaning |
|---|---|---|
| `baseline_mismatch` | BLOCKED | `baseline_sha` is not an ancestor of HEAD (wrong branch or rewritten history) |
| `baseline_record_mismatch` | BLOCKED | the contract disagrees with the operator-supplied baseline record |
| `record_tampered` | BLOCKED | a baseline record or manifest fails its own digest |
| `dirty_baseline` | PARTIAL | work began on a dirty tree; attribution of those paths is ambiguous |
| `declared_mismatch` | BLOCKED | `modified_paths` differs from the change set Git reports |
| `out_of_scope_modification` | BLOCKED | a changed path is not covered by `allowed_paths` |
| `protected_path_modified` | BLOCKED | a protected path changed (also for new ignored files) |
| `test_path_modified_unapproved` | BLOCKED | a test file changed without `allowed_sensitive_paths` |
| `governance_path_modified_unapproved` | BLOCKED | a governance file changed without `allowed_sensitive_paths` |
| `special_file_change` | BLOCKED | a symlink, submodule or file-mode change without `allowed_sensitive_paths` |
| `ignored_baseline_unknown` | PARTIAL | ignored files exist and no ignored baseline was recorded |
| `ignored_path_unapproved` | BLOCKED | a new ignored file is outside `ignorable_paths` and `allowed_paths` |
| `ignored_listing_truncated` | PARTIAL | the ignored-file set is too large or truncated and was not fully compared |
| `missing_evidence` | BLOCKED | a verification entry, exit code, pin or evidence file is missing or unusable |
| `evidence_hash_mismatch` | BLOCKED | an evidence file differs from its pin |
| `evidence_tampered` | BLOCKED | an evidence file differs from the supplied manifest |
| `evidence_not_sealed` | PARTIAL | `--require-sealed`: evidence is not covered by a matching manifest |
| `check_failed` | PARTIAL | a recorded command reported a non-zero exit code |
| `required_check_missing` | BLOCKED | a command in `required_verification` was not recorded |
| `incomplete_execution` | BLOCKED | `execution_state` is not `complete` |
| `false_pass` | BLOCKED or PARTIAL | the contract claims PASS but verification computed a lower status (severity mirrors the computed status) |
| `executable_git_config` | BLOCKED | repository configuration defines a program Git would run |
| `verification_error` | BLOCKED | malformed or ambiguous input, or an unexpected error (fail closed) |

## Compatibility and changes

The result contract (`ai-sdlc-lite-result/1`) and verification report (`ai-sdlc-lite-verification/1`) keep their schema ids. Relative to the committed verifier (`historical-development-snapshot`), changes are additive except where noted:

- Added report fields: `registry_version`, `trust`, `recovery`, `ignored_paths_count`, `evidence[].origin|integrity|execution`, optional `dirty_baseline_changed_since_record`; added optional contract fields and the `baseline`/`seal`/`codes` subcommands.
- **Behaviour changes (essential, documented):** (1) `--out` now creates a new file and refuses to overwrite one, because a verifier must not destroy user files; (2) ignored files are no longer silently ignored: without `baseline_ignored_paths` they cap the result at PARTIAL, and new ignored files outside `ignorable_paths` or `allowed_paths` are BLOCKED; (3) symlink, submodule and file-mode changes now need `allowed_sensitive_paths`.
- Names used in the uncommitted N03 draft (`--require-independent`, `no_independent_evidence`, evidence `trust: independent`) were never committed or released and were replaced by `--require-sealed`, `evidence_not_sealed` and `integrity: sealed`, because "independent" overstated what a hash proves.
- Golden reports in `tests/golden/` pin the report shape. Regenerate them only deliberately (`UPDATE_GOLDEN=1`), review the diff, and record the change here.

## Canonical import context

This uncommitted candidate preserves the public history. Historical development snapshot aliases are not resolvable public revisions or execution evidence. Private reports and ancestry are excluded. See [technical interfaces](docs/qualification/CODEX-002-summary.md); qualification remains subject to its explicit gates.
