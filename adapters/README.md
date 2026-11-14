# Provider adapter declarations

`ai-sdlc-adapter/1` is a small, provider-neutral description of what the repository's own records say about a
coding-agent provider. **A declaration is data. It never runs a provider, probes a version, reads credentials or
provider configuration, or authorizes anything.** It is not a qualification.

Provider-specific files stay authoritative for their own fields: the [Codex declaration](agents/codex/README.md)
and the [Godot adapter](godot/README.md) are unchanged. The BOV workflow, the
[result contract](../RESULT_CONTRACT.md) and the verifier are reused as they are.

## Files

| Path | Purpose |
| --- | --- |
| `adapter-contract.schema.json` | Field definitions and the single source of the allowed names (`x-vocabulary`) |
| `agents/<provider>/provider-adapter.json` | One declaration each for `claude-code`, `copilot` and `codex` |
| `../ai_sdlc/adapters.py` | Read-only validator and matrix renderer (standard library only) |

## Commands (read-only)

```bash
python3 -m ai_sdlc adapter list
python3 -m ai_sdlc adapter validate [--config FILE --project DIR]
python3 -m ai_sdlc adapter matrix [--json]
```

Exit 0 means every checked declaration is valid; exit 2 means at least one is invalid or the contract cannot be
loaded. No command executes a provider, shells out, uses the network, writes a file or probes a version.

## Capability states

| State | Meaning | Requires |
| --- | --- | --- |
| `SUPPORTED` | Previously observed with recorded evidence | basis `observed` and an evidence file |
| `NOT_QUALIFIED` | Documented or configured, but not exercised | basis `documented` or `configuration` and an evidence file |
| `UNKNOWN` | Insufficient evidence | basis `none`, no evidence |
| `UNSUPPORTED` | Evidence confirms absence | basis `observed` or `documented` and an evidence file |

Capabilities (exactly these): `version_detect`, `skill_install`, `skill_discovery`, `skill_invocation`,
`instruction_file`, `noninteractive_run`, `structured_output`, `resume`, `cancellation`, `timeout`,
`native_sandbox`, `native_approval`, `usage_reporting`. Providers do not expose identical features; an unrecorded
feature is `UNKNOWN`, never assumed.

## Rules the validator enforces

- `execution_authorized` is `false`; `qualification.smoke` and `qualification.deep` are `NOT_RUN`.
- `provider_version.observed` is a historical observation or `null`; `compatibility_claim` is `none`. No automatic
  version probing exists, and no compatibility with an installed version is claimed.
- Duplicate JSON keys, unknown fields, non-finite numbers, files over 64 KiB, symlinks and malformed JSON are rejected.
- Evidence and instruction paths are repository-relative regular files inside the project: no absolute paths,
  traversal, globs or symlinks.
- Text must be display-safe: control, format, surrogate, private-use, line/paragraph separator, replacement and
  non-ASCII space characters are rejected. Untrusted text in messages is shown ASCII-escaped.

## Limits

Declaration validity is configuration consistency only. It does not establish that a provider is installed, that a
version works, that a Skill is discovered, what a native sandbox or approval policy enforces, or that a task may run.
Live discovery, execution, cancellation and timeout behavior require separately approved qualification (CODEX-003,
CODEX-004 and the equivalent gates for other providers).
