# Codex adapter and reusable delivery reference

This is a technical description of the source interfaces, not an execution report.
No private task report, transcript, commit history or machine-specific evidence is
included. Runtime execution, fresh-session discovery and unattended operation
remain unqualified.

## Declarative Codex adapter

The [schema](../../adapters/agents/codex/codex-adapter.schema.json),
[validator](../../adapters/agents/codex/validate_adapter.py) and
[example](../../adapters/agents/codex/examples/declaration.json) describe a narrow
Codex CLI 0.167.2 configuration profile. The validator is read-only and uses the
Python standard library. It does not launch Codex or grant execution authority.

Run configuration validation from the repository root:

```bash
python3 -B adapters/agents/codex/validate_adapter.py --config adapters/agents/codex/examples/declaration.json --project .
```

CODEX_ADAPTER_READY indicates declaration consistency only. Native effective
permissions, sandbox enforcement, independent evidence custody and human
acceptance are separate. See [qualification limits](../../adapters/agents/codex/README.md).

## Reusable result delivery

[templates/RESULT.md](../../templates/RESULT.md) supplies reusable task results.
Root execution reports must be preserved and are not template sources.
The canonical Skill points to this reusable source. The installer rebases that
source link to its compatible framework/RESULT.md namespace in installed bundles.
It never packages a mutable root execution report as a template.

The installer tests cover source/bundle link coordination, mutable-report
independence, template absence, repeat-install identity, existing target history
and guarded uninstall. Test results for a particular candidate belong in its
separate reviewed evidence record; this reference makes no runtime claim.

## Boundaries

No private source Git ancestry is needed for these files. Installation does not
authorize a task or publication. Native Copilot discovery and Codex runtime
qualification must not be conflated. Retain master installation compatibility
until a separately reviewed canonical branch transition.
