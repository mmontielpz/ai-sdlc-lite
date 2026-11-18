# Experience System contract (EXPERIMENTAL)

> **Status: experimental; not part of any release gate; no qualification claim.** This document describes the Experience System V1 contract. **Implemented in this increment (EXP-01A): the event schema, event validation, the local journal library and `ai-sdlc experience validate`.** Capture commands (`experience record`, `experience record-verify`, `init --journal`), export, import and analysis are **planned and not implemented**.

AI-SDLC Lite governs and verifies. Experience records *observable outcomes* as inert data. Nothing here changes the verifier, the Skill, any existing schema, exit code or output (except one added line in the top-level usage text).

## Invariants
1. No Lite command reads a journal. 2. Offline: no network, subprocess, model call, daemon or hook; stdlib only. 3. Capture is opt-in and explicit: there is no default journal location and nothing is captured implicitly. 4. Existing commands are unchanged. 5. Trust levels T0/T1/T2/H as Lite defines them; **T3 is not representable**; **`H` (human) events are disabled in V1** and rejected with `h_not_enabled`. 6. No content capture: no source, diffs, prompts, transcripts, environment values, configuration, paths, path digests or free text. 7. Integrity only: every report states `authenticity: not verified`.

## Event `ai-sdlc-experience-event/1`
Closed schema (see [experience-event.schema.json](experience-event.schema.json), documentation only; the code is the validator). Any added or changed field or enum value requires a new schema id (`/2`); readers accept only the ids they implement.
Seven types: `install.completed`, `install.failed`, `task.initialized`, `task.approval_changed`, `verify.completed`, `check.operator_run`, `human.feedback`.

| Type | method | trust | notes |
|---|---|---|---|
| `install.completed` | `tool-checked-hash` | T1 | manifest digest verified by the initializer |
| `install.failed` | `tool-reported` | T0 | closed initializer reason ids |
| `task.initialized` | `operator-recorded` | T0 | operator-typed fact |
| `task.approval_changed` | `human-decision-reported` | T0 | a report that a human decided; never `H` |
| `verify.completed` | `tool-observed-git-state` | T2 | primary claim: repository-state verdict; carries `facets` and `checks_origin: agent-reported` so PASS is never read as executed checks |
| `check.operator_run` | `operator-ran` | T0 | **operator-run evidence is never T1/T2/T3**; `independence` is a recorder claim Lite does not verify |
| `human.feedback` | `human-decision-reported` | T0 | closed decision/friction vocabularies |

Method ceilings: tool-observed-git-state T2; tool-checked-hash T1; all other methods T0. A human decision or acceptance never changes the trust or independence of any other event.

**Identity and order.** `event_id = "ev-" + sha256(canonical JSON of the event without event_id)[:32]` (canonical JSON: sorted keys, compact separators, ASCII-escaped, no floats). `seq` starts at 1 and increases by 1; `prev` is the previous `event_id` (null at 1). Ordering authority is `seq`/`prev`, never `recorded_at` (producer clock, untrusted). The chain detects accidental or naive modification, reordering and deletion; it does not authenticate authorship.

## Journal
UTF-8 JSONL, one canonical event per line ending `\n`, at most 4 MiB and 5,000 events. The path is explicit; every path component is opened without following symlinks; a journal inside a Git work tree is refused unless explicitly allowed; the file is created exclusively with mode 0600. Appends take an exclusive `flock`, fully validate the existing journal, then write exactly one line and `fsync`; on any refusal nothing is written. A malformed, truncated, oversized or chain-broken journal is refused with a stable code and is **never repaired, truncated or rewritten**. Capture is at-most-once: a crash between an action and its append loses that event, and a retry appends a new distinct event. Advisory locks protect cooperating writers only and are meant for local filesystems.

Stable codes: `schema_invalid`, `forbidden_content`, `bad_encoding`, `malformed_json`, `duplicate_key`, `non_finite_number`, `depth_exceeded`, `limit_exceeded`, `trust_inflation`, `h_not_enabled`, `id_mismatch`, `chain_broken`, `truncated_journal`, `journal_full`, `journal_invalid_path`, `journal_in_repo`, `journal_missing`, `journal_io`, `lock_failed`, `unsupported_platform`, `registry_unavailable`.

## `ai-sdlc experience validate --journal FILE`
Read-only (shared lock). Exit 0: prints `experience journal ok: events=N run_id=R head=ev-...` and `authenticity: not verified`. Exit 2: prints `JOURNAL-INVALID: <code>[ line N]` on stderr; event content is never echoed.

## Known limitations (this increment)
No capture commands yet (EXP-01B); journals can only be produced through the library API. Digests and chains are not authentication: a local attacker with write access can rewrite a journal consistently. Metadata (counts, versions, dates, reason codes) can still identify activity. `flock` behaviour on network filesystems is not specified. `independence` and human decisions are recorder claims. Identifier fields (`task_id`, `task_revision`, `check_id`, `run_id`) are operator-chosen bounded strings and appear verbatim; choose non-sensitive names. Under heavy write contention a writer waits at most 2 seconds for the lock and is then refused with `lock_failed` (never a forked or corrupted chain). Linux first; Windows has no `fcntl` and is refused with `unsupported_platform`.
