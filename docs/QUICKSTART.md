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

```bash
ai-sdlc verify --repo /path/to/repo --result result.json
```

Commands recorded in `result.json` are **never** executed by `verify`; the verifier checks repository scope, protected paths, baseline ancestry, and evidence hashes.

## 6. Interpreting Outcomes

| Status | Exit Code | Meaning |
| --- | --- | --- |
| `PASS` | `0` | Clean baseline, all changes within `allowed_paths`, required checks recorded, no violations detected. |
| `PARTIAL` | `1` | Dirty baseline, unknown ignored baseline, or unsealed evidence when `--require-sealed` is set. |
| `BLOCKED` | `2` | Out-of-scope, protected, test, or governance modification, missing evidence, hash mismatch, or invalid contract. |
| `UNKNOWN` | `3` | Unreadable or invalid input (used by `delivery` preflight; `verify` fails closed as `BLOCKED` exit `2`). |
