# Small fix: repaired example and baseline replay

This original example preserves the repaired `normalize.py` and five immutable tests. SMALL-FIX-001, revision 1, was executed after explicit owner plan approval: baseline 3/5 passed, final 5/5 passed. Human acceptance remains PENDING. [RESULT.md](RESULT.md) distinguishes historical evidence from the later reproducibility checks.

The correct behavior is to lowercase a string and remove surrounding whitespace while preserving internal whitespace. Inputs are strings; validation of other input types is outside this exercise.

## Verify the repaired implementation

Use an existing Python 3 installation; only the standard library is needed. From the repository root:

```bash
cd examples/small-fix
python3 -B -m unittest -v test_normalize.py
```

Expected: five tests pass, exit code `0`. This command does not recreate the defect.

## Reproduce the original defective baseline separately

Run this command from `examples/small-fix/`. It creates the original six-line source and a copy of the unchanged tests in a temporary directory, runs the same tests there, and cleans up automatically. The validated implementation is never overwritten. Only the existing Python standard library is used.

```bash
python3 -B - <<'PY'
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile

baseline = '''"""Intentionally defective fixture: surrounding whitespace is not removed."""


def normalize_name(text):
    """Lowercase a name; trimming is intentionally missing for the exercise."""
    return text.lower()
'''
assert hashlib.sha256(baseline.encode()).hexdigest() == "eed3458a7eee46b41d786169ed7034b3d8a80cbe6c3e5a78fc41e2015c42276a"
tests = Path("test_normalize.py")
assert hashlib.sha256(tests.read_bytes()).hexdigest() == "4786856c734810a12b12bd874cd8d672edd5ada0fa5844af00ee3bc722a7b10b"
with tempfile.TemporaryDirectory(prefix="small-fix-baseline-") as directory:
    target = Path(directory)
    (target / "normalize.py").write_bytes(baseline.encode())
    shutil.copyfile(tests, target / tests.name)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "-v", "test_normalize.py"],
        cwd=target,
    )
raise SystemExit(result.returncode)
PY
```

Expected: five tests run, three pass, and surrounding spaces and tabs/newlines fail; exit code `1`. The source and test hash assertions verify that the replay uses the historical baseline bytes and immutable tests. This expected failure is evidence of the planted defect, not a failed repaired delivery.

## Bound → Observe → Verify

The archived [TASK.md](TASK.md) records the repair boundaries; the root [AGENTS.md](../../AGENTS.md) and [CHECKLIST.md](../../CHECKLIST.md) define execution and review. The recorded run stopped for plan approval, modified only `normalize.py`, verified all five cases and file hashes, and left human acceptance pending. Its result was delivered in the conversation because documentation edits were outside the repair scope.

A future exercise needs a separately authorized task and explicit plan approval for its own workspace. Replaying the baseline here grants no editing or release authority. Preserve these tests and the validated implementation.

## Observation protocol for future authorized runs

Apply Outcome-first · Time-conscious · Token-aware: establish correct delivery first, record time and human effort where practical, and collect tokens only when reliable native data exists. Learn from context, prompts, iterations, and session boundaries without adding measurement infrastructure or delaying delivery to chase unavailable counters.

- Record task revision, session ID, reported model, and Codex client/server versions where available. Do not launch another agent or install a collector.
- Capture UTC timestamps at task start, preflight/plan delivery, human approval, implementation completion, verification completion, and final delivery. Elapsed seconds run from task start to final delivery and include waiting. Report active work or human review time only if separately measured.
- At the start boundary, before the task prompt, and after the completed delivery response, the operator should capture Codex `/status` usage if available. Preserve the displayed categories, units, precision, session ID, and capture times. Use a difference only for counters established as cumulative for the same session; label rounded readings as approximate.
- If status lacks usable counters, an operator may inspect only the matching local session's usage events, without exporting private transcript content. Capture cumulative `total_token_usage` boundary records and their timestamps if available; do not sum cumulative events or add overlapping categories. Record the observed schema and version. Incomplete boundaries, counter resets, or uncertain semantics make task usage UNKNOWN.
- If usage collection is unavailable, retain UNKNOWN; do not interrupt the coding task to build telemetry. The measured window includes planning and result generation, excludes fixture preparation, and must state any extra interaction included. Collect the ending usage after delivery so the agent does not claim to measure its own unfinished response.
- Keep elapsed time (seconds), retries (additional attempts of a named operation), observed tokens (per category), provider-reported billed units, and actual monetary cost (currency) separate. Each needs a source and covered window. Missing values are UNKNOWN, never zero; tokens do not establish charges.

The code and tests run offline. The chosen Codex access may require connectivity and incur usage; a later authorized session must use existing access. This fixture does not establish general agent compatibility, beginner usability, or performance gains.
