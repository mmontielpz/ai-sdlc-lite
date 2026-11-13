# Godot adapter (generic)

**State: ADAPTER_READY tooling only.** This adapter lets a Godot project *declare* how AI-SDLC Lite may work with it, and validates that declaration. It does not run Godot, does not authorize any command, and proves no isolation. No Godot project has been runtime-qualified.

It sits beside the universal core and depends on nothing in it (the dependency direction is adapter → core, never the reverse). It is generic: no project, studio or agent names. A project-specific declaration belongs under `examples/projects/` (see [ROADMAP.md](../../ROADMAP.md)), not here.

| File | Purpose |
|---|---|
| `godot-adapter.schema.json` | the declaration format (`ai-sdlc-godot-adapter/1`); a test keeps it in sync with the validator |
| `validate_adapter.py` | read-only, stdlib-only validator and contract-field emitter; the reference implementation of the rules |
| `examples/disposable-sample/` | a synthetic sample project, a placeholder runner that is **not executable**, and a valid declaration |

## What the adapter is, and is not

- **Is:** declarative JSON describing project detection, version constraint, working directory, **project-owned** runners, import/test/GUI command declarations, protected paths, allowed scope, generated files, isolation requirements and evidence requirements.
- **Is not:** an execution engine, a runner, an installer, a sandbox, or an authorization mechanism. Do not build one here. Existing project runners are *referenced*, never replaced or wrapped.
- **Command declarations are data, not execution authorization.** A runner entry with `approved: true` and a filled `approvals` block records a human decision; the validator reports it and **still reports `execution_authorized: false`**. Nothing is executed during configuration validation, import, test or sampling, and the validator contains no process-spawning code (a test enforces this).
- **A path or isolation declaration is not proof of isolation.** `isolation_proof` in every report says so; OS-level isolation must be demonstrated by gate Q7.

## Declaration reference

All keys are required unless marked optional. Unknown keys are errors, so a typo or a self-asserted `qualification` field is refused.

| Section | Fields |
|---|---|
| `schema` | `ai-sdlc-godot-adapter/1` |
| `project` | `root` (project-relative directory containing `project.godot`, `.` allowed), `working_directory` (relative to the root), `detect` (must be `project.godot`) |
| `godot` | `min_version` (`X.Y[.Z]`), `max_version_exclusive` (optional). Compared with the first version in `config/features` of `project.godot`; no version there is a warning, not a pass |
| `runners[]` | `id`, `kind` (only `project-wrapper`), `path` (project-relative file with a directory part; bare names, absolute paths, globs, symlinks and files outside the project are refused; the file must exist but is never run), `approved`, `isolation_by_runner` (the owner asserts the wrapper isolates user data; required by any command using it) |
| `commands[]` | `id`, `role` (`import`, `test`, `gui`), `runner` (a declared id; a global `godot` is never accepted), `args` (list of single-line strings; no `user://`, real user-data locations, absolute or `..` paths, variables), `timeout_seconds` (1 to 3600), `writes` (globs the command is expected to write; may be empty), optional `optional`, `requires_display` (required `true` for `gui`) |
| `paths` | `protected`, `allowed`, `generated` (required lists); `sensitive_allowed`, `ignorable` (optional). `project.godot` and `export_presets.cfg` must be protected or explicitly listed in `sensitive_allowed` |
| `generated` | `policy`: `ignored`, `tracked` or `project-decides`. With `ignored`, a `.gitignore` in the project that does not mention `.godot` is a warning |
| `isolation` | `required` (must be `true`), `profile` (`private-home-xdg`, `project-managed`), `disposable_workspace` (must be `true`), `protected_user_data` (names from `linux-xdg-data`, `linux-xdg-config`, `linux-xdg-cache`, `macos-app-support`, `windows-appdata`) |
| `evidence` | `required` (must include `exit_code` and `output_log`; may add `result_line`), `store` (must be `outside-repository`), optional `result_line_pattern` (regular expression, at most 200 characters) |
| `approvals` | `execution_approved_by`, `approved_revision` (each `null` or a non-empty string) |

Path patterns are repository-relative globs (`*` within a directory, `**` across). Rejected everywhere: absolute paths, `..`, backslashes, `~`, `$` or `%` expansion, any scheme or drive (`res://`, `user://`, `C:`), empty segments, a leading `./`, NUL.

## Safety model

| Protection | What the declaration says | Who enforces it | Status |
|---|---|---|---|
| Real saves (`user://`) | `isolation.protected_user_data` names real locations; commands may not reference them | The project's runner (private HOME/XDG profile); the verifier's post-run scope check does **not** see user data | **Declared only.** Needs Q7 |
| Project configuration | `project.godot` and `export_presets.cfg` protected by default | `verify_scope.py` (`protected_paths`), after the fact | Detection, not prevention |
| Protected assets | `paths.protected` | Same | Detection, not prevention |
| Generated `.godot/` | `paths.generated`, `generated.policy`; becomes `ignorable_paths` | The verifier's ignored-file comparison | Detection; content changes to already-ignored files are not seen |
| Temporary profiles and caches | `isolation.profile`, `disposable_workspace: true` | The project's runner and the operator | Declared only |
| Existing dirty repositories | Out of the adapter's scope | Core baseline record (`verify_scope.py baseline`) | Core feature |
| Unapproved filesystem writes | `commands[].writes` must be covered by generated, ignorable or allowed paths and must not overlap protected paths (conservative literal-prefix comparison) | Validator (declaration level) and the verifier (actual changes) | Declaration consistency only |

Run future executions only in a disposable workspace with an isolated HOME and XDG directories, through the project's own approved wrapper.

## Using it with an existing Godot repository

1. Copy `examples/disposable-sample/godot-adapter.json` next to your project (outside the engine's project tree if you prefer).
2. Set `project.root` and `working_directory`, the version constraint, and your **own** runner wrapper (`runners[].path`). Declare commands exactly as your project already runs them; add no new runner or test infrastructure.
3. List protected paths (approved assets, configuration), the allowed scope, and the generated paths.
4. Validate (read-only): `python3 -B adapters/godot/validate_adapter.py --config godot-adapter.json --project /path/to/repo`.
5. Print the fields for a task's result contract: add `--emit-contract-fields`. Paste them into the contract (`protected_paths`, `allowed_paths`, `allowed_sensitive_paths`, `ignorable_paths`); the core stays unchanged. Tests belong in `allowed_sensitive_paths` by explicit decision, as the core requires.
6. Recording an approval, running anything and qualification are separate human-approved steps.

`python3 -B adapters/godot/validate_adapter.py --codes` prints the finding codes below. Exit status: 0 for ADAPTER_READY (warnings allowed), 2 for NOT_READY.

## Qualification states and gates

| State | Meaning | Established by |
|---|---|---|
| `ADAPTER_READY` | The declaration is consistent and safe *as a declaration* | This validator (gates Q1 and Q2 at configuration level) |
| `RUNTIME_QUALIFIED` | Import and tests ran in a disposable, isolated workspace with recorded evidence | Gates Q3 to Q9, with real runs. **Not established by anything in this repository** |
| `DEVELOPMENT_QUALIFIED` | A real bounded development task was completed under the framework | Q10 plus an end-to-end task, with human acceptance. **Not established** |

| Gate | Requirement | Configuration-level result | Runtime result |
|---|---|---|---|
| Q1 | Project detection | PASS or FAIL (`project.godot` checks) | not applicable |
| Q2 | Configuration validation | PASS or FAIL | not applicable |
| Q3 | Approved runner compatibility | DECLARED (runner file exists, kind and isolation assertion declared) | NOT_RUN |
| Q4 | Safe import in a disposable workspace | NOT_RUN | NOT_RUN |
| Q5 | Headless test execution | NOT_RUN | NOT_RUN |
| Q6 | Scope enforcement | DECLARED (consistent scope) | NOT_RUN |
| Q7 | Save and profile isolation | DECLARED | NOT_RUN: must be demonstrated, not declared |
| Q8 | Failure and interrupted-run reporting | NOT_RUN | NOT_RUN |
| Q9 | Evidence integrity and result verification | DECLARED (evidence requirements) | NOT_RUN |
| Q10 | Functional gameplay and GUI acceptance | NOT_RUN | NOT_RUN; needs human acceptance |

The validator never reports PASS for Q4 to Q10.

## Finding codes

Reports use schema `ai-sdlc-godot-adapter-report/1`. Errors make the adapter NOT_READY; warnings do not.

| Code | Level | Meaning |
|---|---|---|
| `validation_error` | ERROR | unexpected failure while validating (fail closed) |
| `config_unreadable` | ERROR | configuration file missing, a symlink, too large or not valid UTF-8 |
| `config_not_json` | ERROR | configuration is not a JSON object |
| `config_schema_invalid` | ERROR | schema id is not ai-sdlc-godot-adapter/1 |
| `config_unknown_key` | ERROR | unknown key (typos and self-asserted qualification are refused) |
| `config_field_missing` | ERROR | a required field is missing |
| `config_type_invalid` | ERROR | a field has the wrong type or value |
| `unsafe_path` | ERROR | path or glob is absolute, traverses upward, uses a scheme, drive, variable or backslash |
| `project_root_invalid` | ERROR | project root or working directory is missing, outside the project, or a symlink |
| `project_godot_missing` | ERROR | project.godot is missing, not a regular file, or a symlink |
| `project_godot_malformed` | ERROR | project.godot is unreadable or has no config_version |
| `godot_version_constraint_invalid` | ERROR | the version constraint is malformed or empty |
| `godot_version_unsupported` | ERROR | the project targets a Godot version outside the constraint |
| `godot_version_unknown` | WARNING | project.godot declares no engine version; the constraint was not checked |
| `runner_kind_unsupported` | ERROR | only project-owned wrappers are supported, never a global Godot executable |
| `runner_missing` | ERROR | a declared runner file does not exist as a regular file |
| `runner_unsafe` | ERROR | a runner path is bare, absolute, outside the project or reached through a symlink |
| `runner_isolation_unasserted` | ERROR | a runner used by a command does not assert that it isolates user data |
| `runner_not_approved` | WARNING | a runner is declared but not approved; declarations never authorize execution |
| `unknown_runner` | ERROR | a command references a runner that is not declared |
| `duplicate_id` | ERROR | a runner or command id is repeated |
| `command_invalid` | ERROR | a command declaration is malformed |
| `user_data_reference` | ERROR | a command argument references user:// or a real user-data location |
| `protected_path_conflict` | ERROR | an allowed or written path lies inside a protected path |
| `project_config_unprotected` | ERROR | project configuration is neither protected nor explicitly allowed |
| `unscoped_write` | ERROR | a command declares a write that no generated, ignorable or allowed path covers |
| `generated_not_ignored` | WARNING | policy 'ignored' but the project's .gitignore does not mention .godot |
| `isolation_not_required` | ERROR | isolation must be required and the workspace disposable |
| `evidence_inside_repository` | ERROR | evidence must be stored outside the repository |
| `evidence_incomplete` | ERROR | evidence must at least require exit_code and output_log |
| `execution_not_authorized` | WARNING | no execution approval is recorded; nothing may be run |
