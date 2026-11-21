# First Five Minutes with AI-SDLC Lite

This guide walks from installation to your first verified `PASS` and `BLOCKED` result using only Python 3.9+ stdlib and Git.

## 1. Install

The `ai-sdlc` command is installed separately from the Skill. Everything below is offline and uses only Python 3.9+ and Git; nothing is downloaded and no dependency is installed.

**Build the wheel once, from a reviewed checkout of `ai-sdlc-lite`** (needs `setuptools` already available to that Python):

```bash
python3 -m pip wheel --no-build-isolation --no-deps -w dist .
sha256sum dist/*.whl        # record or compare the digest before distributing the file
```

**Install it, in a Python 3.9+ virtual environment, wherever you work** (no checkout is needed from here on):

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --no-index --no-deps /path/to/ai_sdlc_lite-*.whl
ai-sdlc --version
ai-sdlc doctor
```

The wheel carries the CLI and the reviewed Skill bundle, so `ai-sdlc init --repo /path/to/repo --target claude-code --apply` (section 2) installs the matching Skill, and `ai-sdlc init --repo /path/to/repo --target claude-code --check` later confirms the installed Skill still matches the installed CLI. An agent that finds no `ai-sdlc` command must stop and ask you to install it; it never installs packages itself.

From a checkout you can still install in place with `pip install --no-build-isolation --no-deps .`, or run without installing:

```bash
python3 -B -m ai_sdlc --help
```

## 2. Initialize a Target Repository

Preview what `init` will install (no files are written):

```bash
ai-sdlc init --repo /path/to/repo
```

Apply the Skill bundle (`.agents/skills/ai-sdlc-lite/SKILL.md` and `framework/`, or `--target claude-code` for `.claude/skills/ai-sdlc-lite/`), verify integrity, upgrade an intact older bundle, or uninstall cleanly (standard repositories and linked Git worktrees supported):

```bash
ai-sdlc init --repo /path/to/repo --target claude-code --apply
ai-sdlc init --repo /path/to/repo --target claude-code --check
ai-sdlc init --repo /path/to/repo --target claude-code --upgrade
ai-sdlc init --repo /path/to/repo --target claude-code --uninstall
```

> **Runtime boundaries & limitations:** Post-execution verification is not runtime confinement, independent command execution is not automatic (re-run required checks at Gate 2), human approval remains required, macOS and Windows qualification is deferred (Linux only), and Experience schema `/1` refuses dotted/leading-symbol `task_id`s or `BLOCKED`/`PARTIAL` reports with empty `failure_reasons`.

## 3. Diagnose Environment and Repository State

```bash
ai-sdlc doctor
ai-sdlc status --repo /path/to/repo
```

`doctor` and `status` are read-only and never execute repository Git hooks or filters.

## 4. Run the Bounded Example

See [examples/first-five-minutes/README.md](../examples/first-five-minutes/README.md) for a self-contained disposable example that:

1. Initializes a temporary Git repository.
2. Makes one permitted change in `src/greeter.py`.
3. Runs `unittest` and records output to `out.txt`.
4. Verifies `result.pass.json` (`PASS`, exit `0`).
5. Verifies `result.blocked.json` (`BLOCKED`, exit `2`).

## 5. Deterministic Verification

Daily workflow: `Task -> Gate 1 -> Implementation -> External Evidence -> Verify -> Gate 2` (see [WORKFLOW.md](../WORKFLOW.md) and [RESULT_CONTRACT.md](../RESULT_CONTRACT.md)).

Store `baseline.json`, `result.json`, and test output (`out.txt`) outside the repository so they do not pollute workspace diffs:

```bash
ai-sdlc baseline --repo /path/to/repo --out /safe/place/baseline.json
ai-sdlc result-template --repo /path/to/repo --out /safe/place/result.json --baseline-record /safe/place/baseline.json
ai-sdlc verify --repo /path/to/repo --result /safe/place/result.json --baseline-record /safe/place/baseline.json
ai-sdlc verify --repo /path/to/repo --result /safe/place/result.json --baseline-record /safe/place/baseline.json --format summary
```

`result-template` populates repository-derived fields (`schema`, `baseline_sha`, `baseline_dirty_paths`, `modified_paths`, and `baseline_ignored_paths` when no `--baseline-record` is given; with a record the verifier reads the ignored list from the record, so the template stays small and prints a short summary of the ignored directories instead) and sets fail-closed defaults (`verification: []`, `claimed_status: "BLOCKED"`, `execution_state: "in_progress"`). Before running `verify`, the developer or agent must fill in `task_id`, `allowed_paths`, `modified_paths` (if further changes occurred), observed `verification` entries (`command`, `exit_code`, `evidence`), `claimed_status`, and `execution_state: "complete"`.

By default `verify` prints machine-readable JSON (`--format json`). Add `--format summary` for a concise human-readable terminal view (for example, `Status: PASS (computed: PASS, claimed: PASS)` with modified paths, evidence completeness, failure codes, and guidance) while preserving the exact same exit codes (`0`/`1`/`2`). The summary separates `Scope verification`, `Agent-reported checks` and `Independently executed checks` (`none` when the report states that independent execution is not verified, as in any completed `verify` run, since `verify` never runs commands; `unknown` when the report carries no trust information, for example when verification stopped early), so a `PASS` means no violation was detected in the supplied contract and evidence, not that the recorded checks ran or passed. Re-run the required checks yourself before accepting a result. The JSON output is unchanged.

If the repository is already dirty, capture `ai-sdlc baseline` before the task and pass it with `--baseline-record`. Pre-existing dirty files that stay exactly as recorded (content, index entry, executable bit, symlink target) keep the result at `PARTIAL` instead of `BLOCKED`; any change to them, an older baseline record without `baseline_dirty_state`, or no record at all is treated as before (`BLOCKED` unless the path is allowed). Re-take the baseline with the current tool if you want this behavior.

`result.json` (`ai-sdlc-lite-result/1`) is the machine-verifiable artifact (`schema`, `task_id`, `baseline_sha`, `baseline_dirty_paths`, `allowed_paths`, `modified_paths`, `verification`, `claimed_status` mandatory; `modified_paths` and `verification[].exit_code` must come from observed evidence). `RESULT.md` is optional human-readable documentation. Commands recorded in `result.json` are **never** executed by `verify`, and unverified claims never produce `PASS`.

## 6. Interpreting Outcomes

| Status | Exit Code | Meaning |
| --- | --- | --- |
| `PASS` | `0` | Clean baseline, all changes within `allowed_paths`, required checks recorded, no violations detected. |
| `PARTIAL` | `1` | Dirty baseline, unknown ignored baseline, or unsealed evidence when `--require-sealed` is set. |
| `BLOCKED` | `2` | Out-of-scope, protected, test, or governance modification, missing evidence, hash mismatch, or invalid contract. |
| `UNKNOWN` | `3` | Unreadable or invalid input (used by `delivery` preflight; `verify` fails closed as `BLOCKED` exit `2`). |

## 7. Controlled Local Delivery

After verification passes, create a sealed delivery plan (`operations: ["commit"]`), verify it, and execute a local-only commit with an external journal and interactive terminal confirmation:

```bash
ai-sdlc delivery plan --repo /path/to/repo --input /safe/place/delivery-request.json > /safe/place/delivery-plan.json
ai-sdlc delivery verify --repo /path/to/repo --input /safe/place/delivery-plan.json
ai-sdlc delivery execute --repo /path/to/repo --input /safe/place/delivery-plan.json \
  --journal /safe/place/delivery-journal.jsonl --author-name "Owner" --author-email "owner@example.com"
```

`delivery execute` only performs the bounded local commit (no push, pull request, or remote mutation), stores the hash-chained journal outside the repository, and requires typing `YES` in an interactive terminal. Non-interactive runs and JSON-only approvals fail closed with no repository mutation.

Interactive TTY confirmation is an operational safeguard, not cryptographic human authentication. A process with the same OS-user privileges may allocate a PTY and simulate interactive input.

To reconcile an interrupted local delivery from its external journal without re-running Git mutations or rolling back automatically:

```bash
ai-sdlc delivery recover --repo /path/to/repo --journal /safe/place/delivery-journal.jsonl \
  --repository https://example.invalid/owner/repo --branch feature/branch
```

`delivery recover` is observe-only with respect to Git (never commits, retries, or rolls back), may append reconciliation events to the external journal, and exits `0` (`RECONCILED`), `1` (`PARTIAL` when ambiguous/unresolved operations remain), `2` (`BLOCKED` on tampered, missing, or mismatched journal), or `3` (`UNKNOWN`).
