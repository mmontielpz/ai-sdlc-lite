# Codex CLI adapter

**CODEX_ADAPTER_READY means declaration validation only. Codex is not qualified.**
This is a thin, read-only standard-library adapter for **Codex CLI 0.167.2 on Linux**.
It reuses the canonical [Skill](../../../.agents/skills/ai-sdlc-lite/SKILL.md),
[BOV workflow](../../../WORKFLOW.md), [result contract](../../../RESULT_CONTRACT.md)
and [verifier](../../../scripts/verify_scope.py). It never runs Codex, Git, a shell,
Godot, project commands, or a second execution engine, and writes no files.

## Declared compatibility

The schema is intentionally restricted to Codex CLI 0.167.2 on Linux.
Validation describes configuration consistency, not installed-version discovery
or runtime qualification. Review effective native settings separately before
any live run. No bypass, automatic review or added write roots are granted.

## Validate a declaration

From this repository root:

```bash
python3 -B adapters/agents/codex/validate_adapter.py --config adapters/agents/codex/examples/declaration.json --project .
```

The example references existing repository instructions and the canonical Skill;
tests copy that Skill into disposable synthetic projects. The validator uses its
bundled `codex-adapter.schema.json` as the field definition and enforces the
schema vocabulary used there plus path, file, scope and protection checks. It is
not a general JSON Schema implementation. Unknown/missing fields, unsupported
versions, duplicate JSON keys, symlinked files/parents, traversal and unsafe
scope declarations fail closed. Files are size-bounded; no CLI probing occurs.
Exit 0: CODEX_ADAPTER_READY. Exit 2: NOT_READY. Valid reports emit existing
allowed/protected/sensitive result-contract fields; declarations grant no scope.

`instruction_paths` must include root AGENTS.md. `skill_path` is fixed to
`.agents/skills/ai-sdlc-lite/SKILL.md`. Both must exist as nonempty regular files
and be explicitly protected. Sensitive allowances must also appear verbatim in
allowed_paths. Repository-wide wildcard allowances are refused; overlap checks
use conservative literal prefixes and may reject otherwise valid scopes.

## Skill and delivery integration

Reuse the canonical Skill and [technical delivery reference](../../../docs/qualification/CODEX-002-summary.md).
The source Skill links [templates/RESULT.md](../../../templates/RESULT.md);
the installer preserves framework/RESULT.md in installed bundles. Mutable root
reports are not reusable sources. No private execution report is required.

Installed references, manifest integrity and native agent discovery are separate.
The existing installer checks Copilot discovery; fresh Codex discovery and
effective policy enforcement remain unqualified. No source-file presence or
declaration can replace those runtime checks.

## Separate authority and evidence

| Layer | Meaning | Validator result |
| --- | --- | --- |
| Native Codex permissions | What a particular CLI session may attempt or prompt for | Effective permissions unverified; `never` does not grant unrestricted access |
| Human BOV approval | Explicit approval of the bounded task revision and plan | Not verified; never supplied by native permissions |
| Project scope authorization | Owner-approved paths and operations | Declaration only, no grant |
| Evidence verification | Existing verifier checks supplied scope/evidence | Not performed here; JSONL and hashes do not authenticate custody or prove independent execution |
| Human acceptance | Separate explicit decision for reviewed work | PENDING |

`execution_authorized` is always false. Effective-config review is required by
declaration and is not performed by this validator. A worktree or private
HOME/XDG alone does not prove filesystem confinement; sandbox flags do not prove
enforcement. Evidence must be captured outside the project under an approved
custody plan. Usage categories and accounting boundaries remain unqualified;
tokens, billed units, elapsed time and monetary cost stay separate or UNKNOWN.

No global settings, credentials or sessions are read or changed by validation.
This profile is independent of the Godot adapter and does not authorize its
runner declarations. Godot remains configuration-level ADAPTER_READY only.

## Qualification matrix

| Gate | Required evidence | Status |
| --- | --- | --- |
| Configuration | Declaration, paths, canonical Skill and safe profile checks | Deterministic synthetic tests only |
| CODEX-003 smoke / CODEX_SMOKE_QUALIFIED | Separately approved live discovery, BOV gate, bounded task, independent checks, planted violation and human-recorded evidence | NOT_RUN |
| CODEX-004 deep / CODEX_DEEP_QUALIFIED | Separately approved adversarial scope, test/governance protection, configuration precedence, confinement canaries, interruption/resume and owner-controlled recovery | NOT_RUN |

No live qualification, automatic recovery, inference session or paid run is
authorized by this adapter. See the repository qualification matrix for the
policy distinguishing smoke support from deep qualification.
