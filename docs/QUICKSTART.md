# First Five Minutes with AI-SDLC Lite

This guide walks from installation to your first verified `PASS` and `BLOCKED` result using only Python 3.9+ stdlib and Git.

## 1. Install

From a checkout of `ai-sdlc-lite` inside a Python 3.9+ virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --no-build-isolation --no-deps .
ai-sdlc --help
```

Without installing, you can always run directly from the checkout:

```bash
python3 -B -m ai_sdlc --help
```

## 2. Initialize a Target Repository

Preview what `init` will install (no files are written):

```bash
ai-sdlc init --repo /path/to/repo
```

Apply the Skill bundle (`.agents/skills/ai-sdlc-lite/SKILL.md` and `framework/`) and verify integrity:

```bash
ai-sdlc init --repo /path/to/repo --apply
ai-sdlc init --repo /path/to/repo --check
```

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

`result-template` populates repository-derived fields (`schema`, `baseline_sha`, `baseline_dirty_paths`, `baseline_ignored_paths`, `modified_paths`) and sets fail-closed defaults (`verification: []`, `claimed_status: "BLOCKED"`, `execution_state: "in_progress"`). Before running `verify`, the developer or agent must fill in `task_id`, `allowed_paths`, `modified_paths` (if further changes occurred), observed `verification` entries (`command`, `exit_code`, `evidence`), `claimed_status`, and `execution_state: "complete"`.

By default `verify` prints machine-readable JSON (`--format json`). Add `--format summary` for a concise human-readable terminal view (for example, `Status: PASS (computed: PASS, claimed: PASS)` with modified paths, evidence completeness, failure codes, and guidance) while preserving the exact same exit codes (`0`/`1`/`2`).

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
