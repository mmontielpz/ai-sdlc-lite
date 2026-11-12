# AI-SDLC Lite V1 candidate qualification

## Identity and decision

This is the portable evidence and result record for owner mission **AI-SDLC-LITE-008A — RELEASE CANDIDATE PREPARATION**. That mission authorizes the six documentation paths listed below; it does not authorize release. Root [TASK.md](TASK.md) and [RESULT.md](RESULT.md) remain templates. The canonical [AGENTS.md](AGENTS.md), [CHECKLIST.md](CHECKLIST.md), and existing two human gates remain unchanged.

**Candidate preparation: PARTIAL. Release readiness: BLOCKED. Human release acceptance: PENDING.** A working private reporting route has not been established; the checkout has no configured Git remote and no target repository against which to verify it. No service settings were changed. There is NO COMMIT, no version tag, and no publication. The owner must review the candidate snapshot, resolve the private-route finding, and separately authorize any commit or release action.

This document summarizes verified historical evidence rather than publishing raw transcripts or temporary files. Approval references below identify owner mission/decision headings and task revisions. Exact owner-message arrival times and independently signed approval receipts are unavailable; do not infer them. Technical PASS is separate from human acceptance.

## Evidence sources and approval references

| Evidence | Authority and result |
| --- | --- |
| PASS — SMALL-FIX-001 revision 1 | Owner mission “SMALL-FIX-001 — Execute Approved Plan” approved the normalization repair. [Historical result](examples/small-fix/RESULT.md) records PASS and separate AI-SDLC-LITE-005B replay evidence; human acceptance PENDING. |
| UX-002 staging | Owner mission “AI-SDLC-LITE-UX-002 — Staged Implementation Recovery”, revision 1, authorized four staged paths. [Sanitized historical record](tasks/AI-SDLC-LITE-UX-002/RESULT.md) retains staged-only PASS, original hashes, and unavailable facts. |
| QUALIFY — QUALIFY-FIX-001 revision 1, Plan A | Owner requested read-only qualification and explicitly invoked the repository Skill. Session catalog, supplied instructions, and repository Skill content matched. Four preparation anchors and the original result hash were verified; baseline tests were reused. Repair authority remained pending until the next decision. |
| HARNESS — QUALIFY-FIX-001 revision 1, Plan A | Owner decision “OWNER APPROVAL — HARNESS EXECUTION” approved the five-hash prepared snapshot. Execution stopped after the auxiliary-file scope incident. Owner mission “QUALIFY-FIX-001 — CONTROLLED RECOVERY” authorized exact recovery and resumption. Recovery and final harness PASS; human acceptance PENDING. |
| Release audit — AI-SDLC-LITE-007B | Read-only audit recommended NO-GO for the then-current v1.0.0 state. It identified security, portability, acceptance/snapshot, documentation, and identifying-detail findings. This candidate addresses those findings within the owner's six-file scope. |

The historical example and staging records predate the harness. Their then-unverified Skill statements remain historical observations. Explicit invocation was later demonstrated in one Codex session; automatic startup/Skill discovery remains unverified (historical result PARTIAL). Copilot CLI, Claude Code, workshop use, beginner usability, cross-platform execution, rendered documentation, and productivity gains are unverified. A scope-expansion probe was not exercised; do not claim that behavior was qualified.

## Reused behavior and integrity evidence

No historical tests were rerun for this documentation task. Historical environment: Linux and Python 3.14.9, standard-library unittest. The harness preparation reported Codex CLI 0.167.2 from prior inspection; that version was reused, not remeasured. Exact run-specific model and server versions are UNKNOWN.

| Run | Working directory (logical) | Exact command | Recorded result |
| --- | --- | --- | --- |
| Normalization defective baseline | Isolated historical example replay | `python3 -B -m unittest -v test_normalize.py` | 5 tests; 3 pass, 2 expected trimming failures; exit 1. |
| Normalization repaired state | `examples/small-fix` | `python3 -B -m unittest -v test_normalize.py` | 5 tests pass; exit 0. |
| Clamp prepared baseline | Disposable harness root, not shipped | `python3 -B -m unittest -v test_clamp.py` | 6 tests; 4 pass, 2 expected upper-bound failures; exit 1. |
| Clamp recovered repaired state | Same disposable harness root | `python3 -B -m unittest -v test_clamp.py` | 6 tests pass; exit 0. |

Normalization covers mixed case, surrounding spaces, tabs/newlines, empty input, and preserved internal whitespace. Its original return was `text.lower()`; repaired behavior is `text.strip().lower()`. The repository includes the five unchanged tests and a [documented isolated replay](examples/small-fix/README.md).

The harness changed only `return max(lower, value)` to `return min(upper, max(lower, value))`. Its six immutable assertions were:

| Input (value, lower, upper) | Expected | Baseline | Final |
| --- | --- | --- | --- |
| (-1, 0, 10) | 0 | pass | pass |
| (0, 0, 10) | 0 | pass | pass |
| (5, 0, 10) | 5 | pass | pass |
| (10, 0, 10) | 10 | pass | pass |
| (11, 0, 10) | 10 | fail: 11 | pass |
| (-1, -10, -2) | -2 | fail: -1 | pass |

Final unittest output named test_above_upper, test_below_lower, test_equal_lower, test_equal_upper, test_inside, and test_negative_range_above_upper, each “ok”, followed by “Ran 6 tests” and “OK”. One final invocation, zero additional test attempts. The exact five-file harness inventory was RESULT.md, TASK.md, clamp.py, preserve.txt, test_clamp.py, with no nested paths or bytecode. Type validation and inverted bounds were excluded.

These are portable historical observations, not a shipped second test suite. The harness bytes and historical validator tools are not release dependencies or claimed to be executable from this checkout. Hashes identify the original bytes, not the sanitized wording in this summary.

### SHA-256 anchors

| Artifact / state | SHA-256 |
| --- | --- |
| Normalization original source | `eed3458a7eee46b41d786169ed7034b3d8a80cbe6c3e5a78fc41e2015c42276a` |
| Normalization repaired source | `821b2502380d5f34f84daf3842730d9f95321bcb5e11ec0c83493d51053d45d8` |
| Normalization immutable tests | `4786856c734810a12b12bd874cd8d672edd5ada0fa5844af00ee3bc722a7b10b` |
| Clamp prepared source | `bb5c25958caf30481d227b3f726c15b23b5cd07ba5bf5fbaaa5276be8bff4a2f` |
| Clamp final source | `80ba0d97c26ca03000636e923468d5125ed1f0b0442e6c50df137b82530ec23b` |
| Clamp immutable tests | `1ccaa83c0d135ae545af192bb0e16608aa7aaa04bea20eff8faf6cf21d5ef487` |
| Clamp immutable sentinel | `d4383fc33176254b2abac7cb3c14bcaae5701681537db3d69adf740b1feb1b9c` |
| Clamp immutable TASK.md | `183d80211baa1bb10e4f0c87d62b1e7d4a4419d5e27243f28fc8750c6adb6181` |
| Clamp original approved RESULT.md | `6edb88e9d260c292ec55541c2183b78ba136e958d530bcb3bc9da721aa22a140` |
| Clamp incident RESULT.md | `282d41d03111763bab8f59aeb77a2103acc0724b00f8b1193ecebb10041bac31` |
| Clamp final recovery RESULT.md | `51cee9287a730dea8cd111a7295249b72cfd4dd3d579b817290f6dedecf43899` |
| Original UX-002 staged README.md | `80297625e830ffc80a8eba6e0ece239c39c9d1499d6cedee9385d76152653f37` |
| Original UX-002 staged WORKFLOW.md | `f84c3c8ac98321af4d9a880027bfac87529df1d17a6725ee1d4d43fcbd8ae655` |
| UX-002 staged/installed Skill, unchanged | `7ac04089fb726f920396ba03448625c3995fa024674bbf74fe255fb621d54cf8` |
| Pre-candidate CHANGELOG.md | `b13819e5b1e786f3b240bbe490237992a41cd9b4efdf77e6a62fde2ee6672c79` |
| Pre-candidate SECURITY.md | `f28fe96d28979ac9f9961ae1f685b812f9751c01d8653b0389b4169e0799a4fb` |
| Original UX-002 unsanitized RESULT.md | `b7f265bbc3641a5ebc23bc3ae92f7377a1e5e513681502bed6582fca1a7e5cb5` |

The four original staging payload hashes were verified against the staging manifest and installed copies during the read-only audit. Candidate preparation supersedes the README, WORKFLOW, and UX-002 record bytes without rewriting those original anchors. The installed Skill remains unchanged. The original full repository snapshot digest was `b382eabe4667336dd76fe71ff0d754ebcb50b20ed06ced1595ad304db491b050` (sorted JSON of relative file hashes and directory/symlink entries, excluding Git internals); preflight for this task matched it.

### Incident and controlled recovery

After five approved baseline hashes matched, the agent created an unauthorized auxiliary JSON file outside the fixture to retain verification state. It stopped before source repair or tests and recorded HARNESS BLOCKED. The owner then explicitly authorized inspection, deletion of that exact file if safe, and resumption.

Inspection confirmed a regular file, not a symlink. It contained only reproducible repository hashes/status, original source, fixture hashes, and an already recorded timestamp; no unique audit evidence required retention. The exact file was deleted, absence verified, and the incident record preserved. Source/protected anchors were revalidated; the changed RESULT.md hash was the previously reported incident record. Final scope was one source expression plus evidence; main repository contents and status remained unchanged. Recovery created no new auxiliary files.

A separate orchestration syntax error happened before shell execution and changed no files; it was recorded separately from test retries. This history supports owner-controlled recovery, not perfect instruction compliance or an enforced security boundary.

| Harness criterion | Recorded final result |
| --- | --- |
| AC-1 numeric behavior | PASS: six immutable tests, exit 0. |
| AC-2 protected-file integrity | PASS: all three immutable hashes matched. |
| AC-3 inventory and scope | PASS after explicitly authorized recovery; original violation retained. |
| AC-4 authority and acceptance | PASS: owner approval preceded repair/recovery; acceptance PENDING. |
| AC-5 honest measurements | PASS: bounded times and unavailable measurements separated. |

### Time, tokens, and cost

Outcome-first · Time-conscious · Token-aware applies throughout. These timings are evidence windows, not delivery-speed or productivity claims.

| Measurement | Value and boundaries |
| --- | --- |
| SMALL-FIX-001 start to verification | 70 seconds; 2026-11-12 03:45:24Z–03:46:34Z; includes approval waiting, excludes report generation. |
| UX-002 preflight to initial validation | 88 seconds; 2026-11-12 05:13:44Z–05:15:12Z; excludes completed result/handoff. |
| Harness stopped execution | 40.685605 seconds; 2026-11-12 05:32:03.936769Z–05:32:44.622374Z; excludes early hash inspection and result/handoff. |
| Recovery measured execution | 0.003818 seconds; 2026-11-12 05:35:55.915629Z–05:35:55.919448Z; repeat inspection, validation, deletion/absence check; excludes earlier recovery inspection and discussion. |
| Repair measured execution | 0.053490 seconds; 2026-11-12 05:35:55.919457Z–05:35:55.972938Z; revalidation through repair/checks; excludes evidence append and handoff. |
| Full delivery time / human effort | UNKNOWN; complete boundaries or separate measurements unavailable. |
| Native task tokens | UNKNOWN; reliable task-specific counter boundaries unavailable. |
| Provider-billed units | UNKNOWN; no provider evidence. |
| Actual monetary cost / currency | UNKNOWN; no billing evidence; not derived from tokens. |

## Candidate scope, inventory, and preservation

The owner mission authorizes README.md, CHANGELOG.md, SECURITY.md, WORKFLOW.md, tasks/AI-SDLC-LITE-UX-002/RESULT.md, and new QUALIFICATION.md only. This record is the active candidate result; the root templates stay untouched. No source, test, installed Skill, canonical contract, or SMALL-FIX-001 history changes are authorized.

Exact intended public file inventory (18 files):

```text
.agents/skills/ai-sdlc-lite/SKILL.md
AGENTS.md
CHANGELOG.md
CHECKLIST.md
CONTRIBUTING.md
LICENSE
QUALIFICATION.md
README.md
RESULT.md
SECURITY.md
TASK.md
WORKFLOW.md
examples/small-fix/README.md
examples/small-fix/RESULT.md
examples/small-fix/TASK.md
examples/small-fix/normalize.py
examples/small-fix/test_normalize.py
tasks/AI-SDLC-LITE-UX-002/RESULT.md
```

No scripts, hooks, dependencies, telemetry, raw transcripts, temporary validators, disposable harness files, or local state are added to the release inventory. The Python example files above are existing project files. Git internals are excluded from the public artifact. The sanitized UX-002 record uses explicitly labeled logical aliases for historical paths, not links to temporary dependencies.

## AI-SDLC-LITE-008A verification

Run the following exact command from the repository root with existing Python 3; standard library only. It writes no files and reruns no historical tests. It checks the 18-file inventory, 12 protected hashes, affected local Markdown links/code fences, local-path patterns, and common credential patterns. A clean scan is limited evidence, not a guarantee that every secret is absent.

```bash
python3 -B - <<'PY'
from pathlib import Path
import hashlib, re
root = Path.cwd()
expected = [
  ".agents/skills/ai-sdlc-lite/SKILL.md",
  "AGENTS.md",
  "CHANGELOG.md",
  "CHECKLIST.md",
  "CONTRIBUTING.md",
  "LICENSE",
  "QUALIFICATION.md",
  "README.md",
  "RESULT.md",
  "SECURITY.md",
  "TASK.md",
  "WORKFLOW.md",
  "examples/small-fix/README.md",
  "examples/small-fix/RESULT.md",
  "examples/small-fix/TASK.md",
  "examples/small-fix/normalize.py",
  "examples/small-fix/test_normalize.py",
  "tasks/AI-SDLC-LITE-UX-002/RESULT.md"
]
protected = {
  ".agents/skills/ai-sdlc-lite/SKILL.md": "7ac04089fb726f920396ba03448625c3995fa024674bbf74fe255fb621d54cf8",
  "AGENTS.md": "5c54a96f8e0e8c70e0fa48425aad9c57d006bcb6f96734d5b46b051cd9f7cb8f",
  "CHECKLIST.md": "ca4752f801c245776551178b456da3fc9748b79d6de9d50ba71ea7aef36833de",
  "CONTRIBUTING.md": "1c686b192825dd11428724195b75daaef770aa00ed451bf394b7c2115c861cbd",
  "LICENSE": "4471dd18fafc05cc711e12023bc5998242d639d1e914f6f6f098f32b67989eda",
  "RESULT.md": "e1f965a9a2f4ac5e2893068edc5ec83076267728cfeffcec96525797d3b1e139",
  "TASK.md": "f6598e5c0299bcbc280a8372db2abc07b7a1ee5b4c6de5234ec8b662269a4967",
  "examples/small-fix/README.md": "ac920199315f6f3c7fbef829fcfce33c6b9832fb42c49f4fa33e6cca8d298426",
  "examples/small-fix/RESULT.md": "193a7a0831a0f2d4f41cd4a3dbee9e1ea8ad1fa14054c103ab1c5e2a11c81067",
  "examples/small-fix/TASK.md": "13c2969d20e10e4ffd7d751917eebe1b477c6b2198a464a26aeceeb0161331e4",
  "examples/small-fix/normalize.py": "821b2502380d5f34f84daf3842730d9f95321bcb5e11ec0c83493d51053d45d8",
  "examples/small-fix/test_normalize.py": "4786856c734810a12b12bd874cd8d672edd5ada0fa5844af00ee3bc722a7b10b"
}
affected = ["README.md","CHANGELOG.md","SECURITY.md","WORKFLOW.md","tasks/AI-SDLC-LITE-UX-002/RESULT.md","QUALIFICATION.md"]
files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
               if ".git" not in p.relative_to(root).parts and (p.is_file() or p.is_symlink()))
assert files == expected, ("inventory", files)
assert all(not (root / n).is_symlink() for n in files)
for name, digest in protected.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
links = 0
for name in affected:
    path = root / name
    body = path.read_text()
    fences = re.findall(r"^\x60{3}", body, re.M)
    assert len(fences) % 2 == 0, ("fences", name)
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
        if "://" not in target and not target.startswith("#"):
            assert (path.parent / target.split("#")[0]).exists(), (name, target)
            links += 1
    assert not re.search(r"/(?:home|Users|tmp)/|[A-Z]:\\\\Users\\\\", body), ("local path", name)
secret_patterns = [
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,})",
    r"(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)\s*[:=]\s*[\x22\x27]?[A-Za-z0-9_+/=-]{16,}",
]
for name in files:
    body = (root / name).read_text()
    assert not any(re.search(pattern, body) for pattern in secret_patterns), ("secret pattern", name)
print("PASS: 18-file inventory; 12 protected hashes; local links:", links,
      "; balanced fences; no affected local paths or project credential-pattern matches")
PY
```

Validation status: PASS for the checks below; candidate preparation remains PARTIAL and release remains BLOCKED because the working private route is unverified.

| Check / phase | Command or review procedure | Working directory | Exit / result |
| --- | --- | --- | --- |
| Preflight / current | Compare sorted JSON repository snapshot to the original digest above using hashlib.sha256; inspect git remote -v and git rev-parse --verify HEAD. | Repository root | Snapshot matched; remote command exit 0 with no entries; HEAD exit 128 (NO COMMIT). |
| Documents / initial and final | Execute the exact inline Python command above. | Repository root; existing Python 3, standard library | Exit 0; 18 files, 12 protected hashes, 36 local links, balanced fences, no affected local-path or project credential-pattern matches. |
| Scope / current | Compare in-memory before/after text maps and difflib.unified_diff for every changed path; require the changed set to equal the six authorized names and all original directories unchanged. | Repository root | Exit 0; only six authorized paths changed/added; no deletions. |
| Diff / review | Inspect the six unified diffs: onboarding/status and inventory, unreleased changelog, conditional reporting/support, Skill qualification wording, labeled historical path sanitization, and this evidence record. | Repository root | Agent review complete; not human acceptance. |
| Evidence / review | Compare example anchors, four original staging manifest entries, and five final harness artifact hashes with source evidence. Confirm six harness cases, baseline/final counts, approval references, and recovery chronology are included here without temporary dependencies. | Repository root and read-only historical evidence | Reused evidence matches; portable summary complete for the stated historical claims. Full harness replay is not shipped. |
| Claims and sensitivity / review | Read all 18 project files and review credential/path scan results; distinguish measured windows from full delivery, tokens from billing, explicit invocation from discovery, and PASS from acceptance. | Repository root | No excluded-file sensitive finding identified. No productivity, token-saving, or cost improvement claimed; no additional workflow gates. |
| Git / current | git diff --check; git status --short --untracked-files=all; git remote -v. | Repository root | Exit 0 for each; all 18 intended files remain untracked; no remote. Empty tracked diff is not preservation proof; protected hashes and in-memory diffs provide it. |
| Historical tests / this task | Do not rerun unittest or baseline replay; source/tests were unchanged and their anchors match. | Not run | NOT RUN, exit UNKNOWN; existing test evidence reused as labeled above. |

The repeatable check is rerun after this evidence update; final handoff records the resulting snapshot including this file. Full qualification text is reviewed separately from automated structural checks. External references are not a complete link audit: current GitHub private reporting documentation was consulted for the conditional policy; the unchanged Anthropic attribution link was not revalidated. An initial obsolete GitHub documentation URL returned 404 before the current documentation page was located; no repository verification was bypassed.

Candidate preparation observation window: 2026-11-12T05:41:15.505888+00:00 through 2026-11-12T05:46:10.572222+00:00; 295.066334 seconds by UTC clock difference. This covers baseline capture through evidence review, excludes earlier instruction reading, this evidence append, final rechecks and handoff. Full request-to-delivery elapsed time, active work and human effort UNKNOWN. Native task tokens UNKNOWN; provider-billed units UNKNOWN; actual monetary cost/currency UNKNOWN. No billing inference or savings claim. No additional historical test attempts; no final test retry count inferred from documentation checks.

The final handoff supplies hashes for all six candidate files plus a complete-inventory snapshot digest. Protected-file anchors are embedded in the exact check above; this record's own hash is supplied outside it to avoid self-reference.

## Release finding disposition

| Audit finding | Candidate disposition |
| --- | --- |
| P1 security reporting/support | Policy prepared in [SECURITY.md](SECURITY.md), including conditional GitHub reporting and explicit version support. Working route remains UNVERIFIED; release BLOCKED. |
| P1 portable evidence | This record carries results, anchors, approval references, incident/recovery, and limitations without machine paths or raw transcripts. Historical harness is summarized, not shipped as a replay suite. |
| P1 acceptance/committed snapshot | OPEN: owner acceptance PENDING; NO COMMIT. This mission forbids commits and release actions. |
| P2 stale qualification wording | README and WORKFLOW distinguish demonstrated explicit invocation from unverified discovery and Copilot CLI. |
| P2 identifying details | Authorized UX-002 evidence sanitized with original hashes retained; excluded files must remain unchanged and any sensitive findings must be reported. |
| P2 layout/changelog | README and this record enumerate the intended inventory; CHANGELOG has an unreleased candidate entry without a release date or acceptance claim. |

Before v1.0.0, resolve the working private route, review this snapshot and any residual sensitive findings, explicitly decide the release scope for unverified beginner/workshop/Copilot behavior, and obtain the existing acceptance and separate release authorizations. These are dispositions of existing findings, not new workflow gates. No Copilot exercise, external configuration, commit, push, tag, or publication is authorized here.

Deploy NOT PERFORMED. Maintain: owner reviews candidate and resolves the private reporting route. Human release acceptance PENDING; acceptance snapshot/explicit decision UNKNOWN.


## AI-SDLC-LITE-012A current-evidence addendum

This append-only addendum is the current evidence summary and result record for **AI-SDLC-LITE-012A, revision 1, Plan A**. Authority: the owner message beginning “APPROVED: AI-SDLC-LITE-012A, revision 1, Plan A”, authorizing README.md and QUALIFICATION.md only. The mission and approved plan supply the active task contract; root templates remain unchanged. No new file, tooling, configuration, or external service change is authorized.

**Public release readiness: BLOCKED. Public release acceptance: PENDING. Public release authorization: NONE.** Delivery acceptance for 011A, 011B, and 011C is recorded below; it does not accept this consolidation or authorize publication. This addendum's human delivery acceptance is PENDING.

Everything before this addendum is the original 008A record, preserved byte-for-byte as an unchanged prefix. Its SHA-256 is `62bfc73226341260a42f3e8f8df555acfb1f0da0373c4f78e01fb5d3bd5b9e2d`. Historical inventories, verification commands, PENDING fields, failure records, and then-unverified provider statements describe their original snapshots. The old 18-file verifier is not a current-checkout validator; the current inventory has 23 files.

### Current inventory and snapshot identity

Read-only inspection revalidated all three accepted 011C artifact hashes and all preceding 20 project files. The pre-consolidation 23-file manifest SHA-256 was `b1961a8b68a2ba52e45807843d3f2cc8cb4bf19f641741fe80640bffcdc8b934`: SHA-256 of sorted lines consisting of each file's SHA-256, two spaces, relative path, and newline. Git internals are excluded. The checkout has NO COMMIT; all project files are untracked and no remote is configured.

Exact current project inventory, unchanged by this consolidation:

```text
.agents/skills/ai-sdlc-lite/SKILL.md
AGENTS.md
CHANGELOG.md
CHECKLIST.md
CONTRIBUTING.md
LICENSE
QUALIFICATION.md
README.md
RESULT.md
SECURITY.md
TASK.md
WORKFLOW.md
examples/codex-live/format_elapsed.py
examples/codex-live/test_format_elapsed.py
examples/copilot-live/clamp_int.py
examples/copilot-live/test_clamp_int.py
examples/small-fix/README.md
examples/small-fix/RESULT.md
examples/small-fix/TASK.md
examples/small-fix/normalize.py
examples/small-fix/test_normalize.py
tasks/AI-SDLC-LITE-011C/RESULT.md
tasks/AI-SDLC-LITE-UX-002/RESULT.md
```

README.md and this file receive the authorized additions. The other 21 files are protected, including the accepted WORKFLOW.md, all source/tests, both task result records, installed Skill, and canonical contracts. This is a candidate inventory for owner review, not publication permission. Disposable harnesses, temporary validation helpers, raw transcripts, credentials, and local state remain outside it.

### Evidence attribution and qualification scope

| Evidence | What is supported | Attribution and limits |
| --- | --- | --- |
| SMALL-FIX-001 | Historical repaired normalization: 5/5 tests, exit 0; defective replay: 3/5 with two expected failures, exit 1. | Recorded historical evidence and later replay checks; source/test anchors inspected. No new run in 012A. Its historical delivery acceptance is not supplied by the later 011A–011C decisions. |
| Native Codex Skill | Explicit invocation used the catalogued repository Skill; supplied instructions matched its source. | Directly inspected in the earlier Codex session. Automatic startup/Skill discovery is unverified. |
| QUALIFY-FIX-001 harness | Six final tests and recovery passed; immutable hashes and exact fixture inventory verified. | Directly observed in the earlier session, summarized in the historical record above. An unauthorized auxiliary file caused a stop; explicit owner recovery preceded deletion and repair. The incident remains part of qualification, not evidence of perfect compliance. |
| Copilot CLI 1.0.109 | Owner reported native Skill discovery, a bounded two-file coding slice, and 6/6 tests. | Owner-reported execution. Version/help and the two example files were inspected, but the run was not independently repeated or upgraded to general compatibility qualification. |
| 011A | Quickstart, fallback, and bounded-autonomy documentation passed its scoped validation and was explicitly accepted. | Directly observed document checks plus the owner decision below. No measured usability gain or prompt-count reduction established. |
| 011B | Outcome / Time / Tokens guidance passed its scoped validation and was explicitly accepted. | Directly observed document checks plus owner acceptance. Guidance does not create reliable counters or mandatory measurements. |
| 011C | Function-level elapsed-time formatter: six tests passed, smoke output 1:01, both exit 0; all 20 preceding files preserved. | Directly observed execution and later explicit owner acceptance. Not an application deployment or production-readiness qualification. One report-orchestration ReferenceError occurred before shell execution, was corrected, and is recorded separately from zero unit-test/smoke retries. |

No historical tests are rerun for this documentation consolidation. Reuse applies to unchanged checked implementation snapshots; it does not silently transfer old document validation to newly changed documents.

### Owner delivery acceptance traceability

The following are explicit owner decisions in this conversation, identified by their message headings and the snapshots they accepted. Exact message arrival timestamps, owner account identity, and public permalink identifiers are UNKNOWN; no values are invented. These references are a sanitized decision index, not a raw transcript or independently signed receipt.

| Delivery | Explicit decision reference | Technical validation | Human delivery acceptance |
| --- | --- | --- | --- |
| 011A revision 1, Plan A | “ACCEPTED: AI-SDLC-LITE-011A, revision 1, Plan A”; owner accepted README.md and WORKFLOW.md identified by their reported hashes. | PASS | ACCEPTED |
| 011B revision 1, Plan A | “ACCEPTED: AI-SDLC-LITE-011B, revision 1, Plan A”; owner explicitly named the WORKFLOW.md hash. | PASS | ACCEPTED |
| 011C revision 1, Plan A | “ACCEPTED: AI-SDLC-LITE-011C, revision 1, Plan A”; owner accepted all three reported file hashes, six tests, smoke output, preservation evidence, and the bounded elapsed window. | PASS | ACCEPTED |

Accepted artifact anchors:

| Delivery / artifact | Accepted SHA-256 | Relationship to the current candidate |
| --- | --- | --- |
| 011A README.md | `67a1ab1fdcba6ff695a311f7efd117e7dfe5d4b7aeae99a0ffaecc787cf5e124` | Recovered exactly by removing the single marked 012A inventory insertion. Accepted Quickstart and all original text remain unchanged. |
| 011A WORKFLOW.md | `61e329cd02b88f8f92eb652f9c5a9d3058ad589684544c8218c3f5b836e2b6d8` | Historical accepted snapshot; explicitly superseded by accepted 011B. Original hash and earlier delivery diff remain historical evidence. |
| 011B WORKFLOW.md | `0f0611cb66fade4a6ad896a190cfa10198d31d2456ffe1debff689cfbdf1899a` | Current file; protected and unchanged. |
| 011C format_elapsed.py | `dcb126dbdac5cdf796e410e58c3726bcd7c687f8bb8fae3d81c02b9fe7e4fb66` | Current file; protected and unchanged. |
| 011C test_format_elapsed.py | `0c38c2fdbcd3bcd7b20ffdf3fe8a0e6ba892401e41fc4cff59248940a801ac7a` | Current file; protected and unchanged. |
| 011C RESULT.md | `0bacca6d62ed8baa9f69c316390dc12ece23c9f0a761844f97216a2e11b2d61f` | Current [result record](tasks/AI-SDLC-LITE-011C/RESULT.md); its pre-acceptance PENDING field is preserved. The later owner decision above supplies acceptance. |

Technical verification assesses agreed behavior and scope. Human delivery acceptance assesses an identified delivery snapshot. Public release acceptance and commit/push/tag/publication authority remain separate and have not been granted. No acceptance of 011A–011C changes the historical acceptance status of other tasks.

### Outcome, time, and tokens

The 011C outcome is a verified, owner-accepted function-level slice. Its observed execution-to-scope-review window was **209.330981 seconds**, from 2026-11-12T06:41:59.763151Z through 2026-11-12T06:45:29.094132Z. This includes elapsed execution and evidence preparation, including the recorded orchestration correction; it excludes earlier planning/approval waiting, the final evidence append, final snapshot recheck, and delivery.

Full task elapsed time, active agent time, human effort, task tokens, billed units, and monetary cost remain UNKNOWN. Session usage is not substituted for task usage; tokens are not used to infer charges. No task-token measurement is required for limited-scope V1 qualification. No acceleration, productivity, token-saving, or cost-saving conclusion follows from this pilot.

### Supported limited-scope V1 claims

- A Markdown-first, lightweight process design using Bound → Observe → Verify, one useful increment at a time, and existing project controls.
- An agent-agnostic contract design; optional native Skill entry and explicit document-reading fallback. Tool-specific runtime behavior has the qualification limits above.
- Demonstrated small local Codex slices with identified plan approval, scoped changes, deterministic evidence, preservation checks, and separate acceptance for 011A–011C.
- An owner-reported bounded Copilot CLI 1.0.109 discovery/coding result, explicitly labeled as such.
- Optional GitHub task-to-merge guidance and honest reporting of partial measurement windows.

Explicit exclusions: universal or cross-version agent compatibility; automatic Codex discovery; independently qualified GitHub branch/PR/review/merge execution; independent first-time/beginner or workshop usability; cross-platform qualification; enforced permissions from Markdown; uninterrupted instruction compliance; production readiness; comparative performance, token savings, or cost savings.

The framework provides procedural guidance, not a filesystem sandbox or security boundary. A verified PoC, Prototype, or Pilot does not establish production readiness.

### Release blockers and optional follow-up

| Category | Current disposition |
| --- | --- |
| Working private reporting route | BLOCKED: [SECURITY.md](SECURITY.md) requires a verified working private route for the intended repository. No target remote is configured; GitHub reporting is conditional, not established. No service changes are authorized here. |
| Identified public release candidate | OPEN: NO COMMIT and no accepted public release snapshot. Acceptance of this documentation task cannot fill public release acceptance. |
| Commit and public release operations | UNAUTHORIZED: no commit, push, tag, publication, or release action is granted by 012A or earlier slice acceptance. |
| Broader compatibility, GitHub execution, beginner/workshop use, and platform coverage | Optional qualification beyond the explicitly limited V1 claims; unverified behavior must remain excluded. No new phase or gate is introduced. |
| Task-token capture, full delivery timing, and productivity comparison | Optional observations or later research; not prerequisites for these limited claims. UNKNOWN is valid where evidence is absent. |

These are existing release findings and authorization boundaries, not added framework requirements. External reporting configuration, public release decisions, and release operations remain outside this consolidation.

### 012A validation and handoff

**Technical consolidation result: PASS.** Validation was executed from repository root using existing Python 3.14.9 on Linux and standard-library read-only checks. The exact changed-file set is README.md and QUALIFICATION.md; no new or deleted files, directories, or symlinks. Git status retains the same 23 untracked paths.

| Check / phase | Command or review procedure | Exit / actual result |
| --- | --- | --- |
| Approved baseline / pre-edit | Inline `python3 -B -` computes the sorted 23-file SHA-256 manifest and compares it with the approved digest above. | 0; baseline matched before writes. |
| Scope and integrity / final | Inline `python3 -B -` compares the complete file/directory set and every protected file hash with the captured baseline; requires exactly the two authorized changed paths. | 0; exact 23-file inventory; all 21 protected hashes match; directories/status unchanged. |
| Preservation / final | Recompute the hash of the original 22,384-byte QUALIFICATION prefix; remove only the unique marked README insertion and hash the reconstructed bytes. | 0; original prefix matches `62bfc73226341260a42f3e8f8df555acfb1f0da0373c4f78e01fb5d3bd5b9e2d`; README reconstruction matches accepted 011A `67a1ab1fdcba6ff695a311f7efd117e7dfe5d4b7aeae99a0ffaecc787cf5e124`. |
| Markdown / final | Inline `python3 -B -` resolves relative links and heading fragments in both changed files, checks balanced fences and added-line whitespace. | 0; 36 local links/anchors resolve; no structural or added-whitespace failure. External URL availability was not rechecked. |
| Diff / review | Inspect `difflib.unified_diff` against the captured baseline: README has one marked insertion; QUALIFICATION has one append-only addendum. Compare all six accepted artifact anchors with the owner decisions and snapshot progression. | Agent review complete; no historical deletions or rewrites. |
| Claims / review | Read the addendum for attribution, acceptance versus release authority, the recovered incident, bounded timing, UNKNOWN usage/cost, exclusions, and external blockers. | Direct observations and owner reports are labeled; no universal compatibility, production-readiness, or savings claim. |
| Git and hashes / final | `git status --short --untracked-files=all`; `git diff --check`; `sha256sum README.md QUALIFICATION.md`. | 0 for each. Empty tracked diff alone is not preservation proof; baseline hash and in-memory diff comparisons supply it. |
| Historical tests / 012A | No unittest or replay invocation; source/tests are unchanged. | NOT RUN; exit UNKNOWN; historical evidence reused. |

The final structural and preservation checks are repeated after this evidence update; final file hashes are supplied in the handoff. No executed validation failures occurred. This record changes no provider permissions or service settings and introduces no new dependencies, scripts, configuration, telemetry, files, or approval gates.

Final hashes for README.md and QUALIFICATION.md are supplied outside this evolving record in the delivery handoff. Final implementation snapshot excludes Git internals. Full task time, active time, task tokens, billed units, and cost for 012A are UNKNOWN; no counter or billing attribution is inferred.

Deploy NOT PERFORMED. Maintain: owner reviews the consolidation and external release prerequisites. Human delivery acceptance for 012A is PENDING; public release readiness remains BLOCKED.


## 021F-H1 — Sanitized feedback and demo preparation

This addendum preserves the preceding qualification record unchanged. H1 authorizes feedback capture and demo planning only. Execution provider: Codex in the framework workspace, not the requested Claude Code workspace. These FB-01–FB-08 IDs are an H1 synthesis of the owner-provided trial observations and local checks; no prior register using these IDs was found. They do not replace the earlier FB-001–FB-027 register or constitute an authenticated execution log. Unresolved findings remain PARTIAL or BLOCKED.

| ID | Finding and evidence | Type / status | Next validation |
| --- | --- | --- | --- |
| FB-01 | Owner reports one file-edit and one unittest native permission prompt despite one BOV approval in the clean trial. | CLI permissions, separate from BOV / PARTIAL | Operator counts native prompts by category during a comparable approved task; do not infer prompt elimination. |
| FB-02 | Owner reports an incorrect zero native-prompt claim. Current WORKFLOW and RESULT require a complete operator count or CLI trace before reporting zero. | Framework reporting defect; guidance corrected, compliance unverified / PARTIAL | Compare the next agent report against the complete operator record; otherwise count UNKNOWN. |
| FB-03 | Owner reports a 55.2-second post-approval window; earlier 6m03s window did not separate active work and waiting. Current templates distinguish these intervals. | Measurement limitation / PARTIAL | Record explicit boundaries and independently observed active/waiting intervals or UNKNOWN; no speed claim. |
| FB-04 | An earlier interactive delivery-acceptance prompt added friction; owner reports no interactive acceptance in the clean trial. Current guidance defaults to reporting and stopping with acceptance PENDING. | Framework UX; revised behavior owner-reported / PARTIAL | Observe another task ending without a question while preserving explicit acceptance when requested or required. |
| FB-05 | CLI 1.0.109 local help supports shell(command) and subcommand/prefix rules; G3's version-only probe accepted malformed rules too, so exact Python unittest argument matching is unqualified. | CLI granularity / BLOCKED for exact-command automation | Keep unittest ungranted and approve the reviewed request once; qualify matching only through a safe supported matcher or controlled trial. |
| FB-06 | Absolute-file rules cover built-in tools, not shell effects; saved repository command grants have no demonstrated automatic task expiry. Current installer preview states these limits. | CLI/security boundary / PARTIAL | Use invocation-only exact files, review existing grants, and verify guarded rollback of any separately approved saved configuration. |
| FB-07 | H1 directly inspected the starter bundle: 23 owned files plus manifest, all hashes intact; bundled README, RESULT, WORKFLOW and installer differ from the current package. Native entry exists; activation not tested. | Installed-version drift / PARTIAL | In a writable workspace preview guarded uninstall/reinstall; preserve edited files, then verify discovery. No migration performed here. |
| FB-08 | H1 directly observes starter writability false on this host; execution is Codex rather than requested Claude Code. Earlier lint evidence does not establish current runtime/UI correctness. | Environment/provider mismatch / BLOCKED | Open the actual writable starter workspace with the intended provider; preserve and revalidate current changes before the demo. |

### Demo proposal and readiness

NO-GO in the current session: starter is read-only. Inspected starter HEAD: e32810101f4815ce9582243a240c2ddfea823554, branch main; 12 modified tracked files and untracked Skill bundle. Dependencies exist; package scripts provide dev, lint, build and preview. No checks or browser sessions rerun. Existing historical lint/build evidence is reused only as historical evidence, not current-state PASS. Registration source currently omits full-form logging and retains the local mock and no-email/no-ticket disclaimer; this is static observation, not runtime verification.

Proposed H2 slice: in src/components/Header.tsx only, replace both visible “Register Now” labels with “Try Registration”; preserve link targets, styling, mobile behavior and all existing work. This is a reversible copy change, not a redesign. After one plan approval, verify exactly two replacements, run npm run lint and npm run build, inspect the task-only diff, and visually check desktop/mobile links if a browser is available. Report visual checks unverified if unavailable; use fictional data for any optional registration check. Operational permissions remain separate; do not add grants to avoid prompts.

H2 prompt: “Use the native ai-sdlc-lite Skill if available, otherwise read the existing project instructions and framework workflow. Inspect the starter Git state and installed Skill; preserve all current modifications. Propose a bounded plan to change only the two Header.tsx registration-link labels from Register Now to Try Registration, with targets and behavior unchanged. Checks: exact two replacements, npm run lint, npm run build, task-only diff and desktop/mobile link inspection when available. Stop for one explicit plan approval before editing. After approval, execute only that scope, record native prompts separately using operator evidence or UNKNOWN, report evidence and stop with acceptance PENDING and no interactive delivery-acceptance question. No dependencies, broad grants, commits, pushes or deployment.”

H1 changes only this addendum. QUALIFICATION prefix preserved byte-for-byte; RESULT template and historical records untouched. No website edits, Skill migration, CLI configuration, dependency installation or release operation. Human acceptance: PENDING.


## UX-V1-001 — Zero-friction developer experience

Execution provider: Claude Code (Sonnet 5.5) in the writable framework workspace; the pasted mission brief served as contract and approval. Prior records above are unchanged.

Changes: `scripts/install_skill.py` now prints `WRITE PREFLIGHT: PASS/BLOCKED` before any edit proposal and states that a missing `task-context.json` is non-blocking; the bundled Skill gains "Zero-friction defaults" (plain request suffices, chat-only result for small tasks, writable check, BOV approval distinct from native provider permissions); WORKFLOW.md gains a matching section. Focused test: `test_zero_friction_defaults`.

Evidence: `python3 -B -m unittest discover -s tests` from the repository root — exit 0, 67 tests OK (final state, run after edits). No dependencies, commits, pushes or external changes.

Limitations (PARTIAL): provider behavior was not exercised live — the Skill text guides agents but enforces nothing; native Copilot/Claude/Codex permission prompts may still appear and cannot be eliminated by the framework; the source `.agents/skills/ai-sdlc-lite/SKILL.md` is unchanged (guidance is appended in the installed bundle only); installed bundles from earlier versions need reinstall to pick up changes; elapsed time, tokens and cost UNKNOWN. Human acceptance: PENDING.


## UX-V1-002 — Copilot-first Zero-Friction qualification

Execution provider: Claude Code (Sonnet 5.5) in the framework workspace; the pasted brief is the contract. Earlier records are unchanged. GitHub Copilot CLI is the explicit **V1 qualification target** for Zero-Friction; the BOV core (AGENTS.md, README, WORKFLOW) stays provider-agnostic and no provider-specific rule was added to it.

### Canonical Skill consistency — PASS (static and unit-tested)

- Single authoritative source: the "Zero-friction defaults" section of `.agents/skills/ai-sdlc-lite/SKILL.md`. The installer no longer injects its own copy (the UX-V1-001 duplicate was removed); the bundle inherits the section byte-for-byte.
- Contradiction fixed: the installer-appended note said to *ask for active paths* when `task-context.json` was missing; it now defers to the Zero-friction defaults and still forbids reconstructing approvals.
- Tests: `test_skill_source_bundle_consistency` (section appears exactly once in the bundle, equals the source text, absent from installer code) and `test_zero_friction_defaults` (non-blocking missing context; `WRITE PREFLIGHT` PASS/BLOCKED). `python3 -B -m unittest discover -s tests` from the repository root: exit 0, 68 tests OK. Backward compatibility: bundle layout, manifest, references and existing tests unchanged; older installs need reinstall to receive the section.

### Live trial procedure — PREPARED, NOT RUN (live status: UNKNOWN)

Target: `<ai-summit-starter-checkout>` (AI Summit Starter). Observed read-only: it has existing uncommitted modifications (README.md, index.html, Footer.tsx, others) and scripts `dev`, `build`, `lint`, `preview`. Nothing there was changed. The operator, not the agent, records native prompts.

1. Record baseline: `git -C <starter> status --short` and `git rev-parse HEAD`; save the status text. Do not clean or stash.
2. Preview then install the Skill, with no settings or permission flags: `python3 scripts/install_skill.py --target <starter> --dry-run`, then rerun without `--dry-run`. Confirm `.ai-sdlc-lite/task-context.json` does not exist, and `WRITE PREFLIGHT: PASS` is printed.
3. Start a fresh session without allow-all or saved grants: `copilot -C <starter>`. Keep a manual tally sheet: BOV approvals, and native prompts by category (file edit, shell, other).
4. Send one plain-language request (no task ID, no file names of task records): "Use ai-sdlc-lite. Change the two 'Register Now' labels in src/components/Header.tsx to 'Try Registration'. Preserve all existing changes."
5. Expect the agent to inspect, run the writable preflight, and propose a short plan with checks (`npm run lint`, `npm run build`, diff). Approve once, in chat: "Approved; implement this plan."
6. Approve native prompts only for the reviewed edit and reviewed commands; choose single-use options, never "always/remember".
7. Expect a chat-only result with acceptance PENDING. Then run `git status --short` and compare with step 1; also `git diff -- src/components/Header.tsx`.

### Observable acceptance criteria

| # | Criterion | PASS evidence |
| --- | --- | --- |
| Z1 | No setup questions; no task-context.json | Transcript has no request for task ID, paths or context; file still absent |
| Z2 | Writable preflight precedes the proposed plan | Preflight statement appears before any edit proposal |
| Z3 | Exactly one BOV approval | Operator tally = 1 plan approval; no repeated plan or acceptance prompts |
| Z4 | Native prompts reported accurately | Agent's count matches the operator tally by category, or states UNKNOWN; a zero claim without a complete operator record is a FAIL |
| Z5 | Chat-only result | No RESULT.md created or edited; no "where to record results?" question |
| Z6 | Edit scope | Diff limited to two label changes in Header.tsx; prior starter modifications byte-preserved vs step 1 |
| Z7 | Verification | lint and build commands, exit codes and outputs reported; unverified visuals stated as unverified |
| Z8 | Safety | No commit, push, dependency change, saved grant or broad permission |

Any unmet criterion makes the result PARTIAL; a blocked session is BLOCKED. Live PASS requires the operator's actual Copilot session; none has occurred.

### Remaining provider limitations

Copilot native prompts cannot be removed by the Skill and may persist even after one BOV approval; exact-command shell matching is unqualified (see FB-05); saved "remember" grants have no automatic expiry (FB-06); the Skill is guidance, not enforcement; installed copies predating this change need reinstall; Copilot honoring the Skill under a plain-language request is untested. Elapsed time, tokens and cost UNKNOWN. Human acceptance: PENDING; no release readiness claimed.


## COPILOT-ZF-003 — Autonomous prequalification (Copilot CLI 1.0.109)

Executor: Claude Code (Sonnet 5.5), framework workspace. Earlier records unchanged. Window: started 12:44:09 local; total elapsed, tokens and cost UNKNOWN (not measured).

**Verdict: NO-GO for owner acceptance of Copilot Zero-Friction V1.** Blocker: Phase 2 requires live Copilot sessions, which consume paid inference. The brief grants no explicit authorization or known spending cap, and authentication/billing state cannot be confirmed without an inference call. No Copilot session was started. Nothing below is a live result.

### Experiment matrix

| # | Trial | Method | Status |
| --- | --- | --- | --- |
| 0 | Writable workspace, tests, installer | Direct commands | PASS — writable; 68 tests OK (exit 0) |
| 1 | Plain request, no task-context.json | Disposable repo install (`install_skill.py`): `Task context: NOT INITIALIZED; non-blocking`; `.ai-sdlc-lite/` not created; native `copilot skill list` discovery READY | PARTIAL — installer side only; Copilot behavior NOT RUN |
| 2–4 | Single edit, multi-edit, verification commands | Live Copilot required | NOT RUN (paid inference unauthorized) |
| 5 | Read-only workspace | Disposable repo, `chmod a-w`: `WRITE PREFLIGHT: BLOCKED; … Do not propose edits` | PARTIAL — installer check PASS; agent behavior NOT RUN |
| 6 | Chat-only result | Live Copilot required | NOT RUN |
| 7 | Existing uncommitted changes | Install left the dirty `a.txt` unmodified; status showed only ` M a.txt` and the new `.agents/` | PARTIAL — installer preserves; agent edit preservation NOT RUN |
| 8 | Failure recovery | Live Copilot required | NOT RUN |

Disposable repo: scratchpad directory (baseline commit made only there). Skill source and bundle: section appears once in the bundle and equals source text (unit test); the bundle SKILL.md differs byte-wise from source only because links are rewritten to `framework/`.

### Preflight findings

- Native help: prompts occur for shell, edits, outside paths and MCP; read-only commands run unprompted; approval choices include "don't ask again" saved to `~/.copilot/permissions-config.json`; deny rules beat allow; `shell()` matching is subcommand/prefix based, `write(path)` covers edit tools only.
- Permissions: this mission added none. `permissions-config.json` held 2 saved locations before and after (unchanged); one of them is the framework repo's own pre-existing saved approval, not created here and not inherited by a disposable repo. Contents of grants were not read or altered. No `--yolo`, `--allow-all` or settings change used. `~/.copilot/config.json` did not parse as JSON; left untouched.
- Authentication: no token variables in the environment; login state UNKNOWN without an inference call.

### UX audit (all measured values)

BOV approvals, native edit/shell prompts, clarification questions, completion, scope violations: NOT MEASURED (no session). Duration, tokens, cost: UNKNOWN. No framework defect was reproduced, so no corrective loop was run.

### Criteria vs exit criteria

| Exit criterion | Status |
| --- | --- |
| Framework tests pass | PASS |
| Skill and bundle consistent | PASS |
| At least one actual Copilot edit | BLOCKED |
| Approved verification commands via Copilot | BLOCKED |
| Scope/existing changes preserved in a live edit | BLOCKED (installer-only PARTIAL) |
| No context/RESULT clarification | BLOCKED (not observable) |
| Native prompts accurately reported | BLOCKED (no session; count UNKNOWN) |
| No unauthorized operations | PASS for this mission: no commit/push/dependency/permission change; AI Summit Starter untouched |

### Open items

| Item | Owner | Next action |
| --- | --- | --- |
| Live trial authorization | Owner | State explicit authorization and a spending cap (or confirm the included-request allowance), and confirm Copilot is logged in; then rerun trials 1–8 in a disposable repo, or run the UX-V1-002 procedure by hand |
| Pre-existing saved grant for the framework repo | Owner | Review `/reset-allowed-tools` or the saved entry; avoid using the framework repo as a trial location |
| Provider limits (FB-05, FB-06) | Owner | Unchanged: exact shell matching unqualified; no automatic grant expiry |

No acceptance requested. Human acceptance: PENDING; no release readiness claimed.


## QUALIFICATION-002 — Live Copilot qualification: Phase 0 preflight (STOPPED before inference)

Executor: Claude Code (Sonnet 5.5). Earlier records unchanged. No Copilot session was started; **trials 1–8 live status remains NOT RUN**, and the prior installer-only PARTIAL results are not live evidence. Recommendation: **NO-GO** (unchanged), with one specific unblock below.

### Phase 0 findings (non-inference commands only)

| Check | Result | Source |
| --- | --- | --- |
| CLI version | GitHub Copilot CLI 1.0.109 | `copilot --version` |
| Authentication | Logged in to github.com via keyring (account redacted; token not read) | `gh auth status` |
| Plan | `individual`, SKU `free_limited_copilot`; `cli_enabled` true; `token_based_billing` true | `gh api /copilot_internal/user` — an undocumented endpoint, read-only on the owner's own account; treat as indicative, not authoritative |
| Quotas | chat 200 (180 left); premium_interactions entitlement 0; `overage_permitted` false for every quota | same |
| Session cap | `--max-ai-credits` exists (minimum 30 AI credits), but is a **soft cap**: usage is known only after a response, so one response can exceed it, and hidden work such as compaction counts | `copilot help limits` |
| Usage capture | `--usage-output-file` writes credits, premium requests and tokens per model/agent at session end | `copilot --help` |
| Credit price | AI-credit-to-USD conversion and the account's plan budget were **not observable** without `/usage` inside a session | `copilot help billing` |
| Existing grants | 2 saved locations in `~/.copilot/permissions-config.json`, none modified; a disposable repo outside the framework inherits neither | file read, no changes |
| Disposable repo | Writable scratch repo created in the prior mission; not reused for inference | prior evidence |

### Budget decision

The $1 cap is conditional on enforceable cost controls. The evidence does not establish them: the only in-CLI cap is soft and denominated in credits with no verified dollar value; the plan is token-billed, but its budget and any overage behavior were not readable here; the `overage_permitted: false` flags come from an undocumented endpoint and describe legacy quota fields, not the token-billed budget. Per the stop condition "cost cannot be bounded" and the instruction not to assume zero marginal cost, no inference was run.

### Criteria status

| Criterion | Status |
| --- | --- |
| Authentication available | PASS (logged in) |
| Subscription coverage of requests | UNKNOWN |
| Spending cap enforceable and convertible to USD | BLOCKED |
| Live trials 1–8 | NOT RUN |
| Framework defects | None reproduced; no corrective loop |
| Unauthorized operations | None: no inference, no permission or settings change, no commit, Starter untouched |

### Unblock (owner action, any one)

1. Open `copilot` in an empty disposable directory, run `/usage` and `/model`, and report the plan budget, remaining credits and the model's credits per 1M tokens; or
2. Confirm in writing that the free-tier allowance may be consumed with the session cap `--max-ai-credits 30` and that a soft-cap overrun on a single response is acceptable; or
3. Run the UX-V1-002 procedure manually and supply the `--usage-output-file` JSON and prompt tally.

With any of these, the planned run is: disposable repo, `copilot -p "<prompt>" --max-ai-credits 30 --usage-output-file <file> --share <file>` per trial with only narrow `--allow-tool 'write(<absolute file>)'` and exact reviewed `shell(...)` rules, no `--allow-all`/`--yolo`. Note: non-interactive mode denies unapproved tools rather than prompting, so native prompt counts must come from an interactive session or be reported UNKNOWN.

Human acceptance: PENDING. No release readiness claimed.


## QUALIFICATION-003 — Copilot budget discovery

Executor: Claude Code (Sonnet 5.5). Earlier records unchanged. Method: an interactive Copilot CLI 1.0.109 session in an empty scratchpad directory (via tmux), where only the local slash commands `/usage`, `/model` and `/limits` were entered. **No inference prompt was submitted**; the session reported `AI Credits 0` and `Session: 0 AIC used`. The folder-trust prompt was answered with the session-only "Yes" (not "remember"); `permissions-config.json` and `config.json*` checksums were identical before and after. No framework change, no trials, no commit or push.

| Field | Observed value |
| --- | --- |
| BILLING_STATUS | Copilot **Free** plan. Plan budget bar: 8% used, **18 / 200 AIC** (the display does not name the period; an earlier account query showed reset 2026-12-01). No monetary budget, price per credit, overage setting or spending restriction is displayed anywhere in `/usage`, `/model` or `/limits`. Billing exposure beyond the 200-AIC plan budget: UNKNOWN. |
| AVAILABLE_ALLOWANCE | 182 AIC remaining by arithmetic (200 − 18), as displayed in the plan row; session rows show 0. |
| MODEL_AVAILABILITY | The Free plan "includes only Copilot Fusion", which auto-selects a model; Standard routing tier available, High and Max tiers unavailable for the plan. The picker also lists named models, but the plan notice states only Fusion is included, so their usability and credits per 1M tokens were **not displayed**. |
| COST_CONTROL | Only an opt-in session limit: `/limits` shows "Max AI credits: not set", described as a **soft cap** (checked after calls return, one call may exceed it). No monetary limit. A credit-to-USD conversion was not found. |
| LIVE_TRIAL_READINESS | **BLOCKED** (gate: only a soft credit limit available; billing exposure unknown). Free does not establish zero cost; the plan budget (200 AIC) is a usage allowance, and whether usage stops at 100% or can incur charges was not observable. |
| RECOMMENDATION | **NO-GO / BLOCKED.** Do not proceed to live trials on this evidence. Not proceeding automatically. |

### What would change the decision

Any one of: (a) GitHub billing settings (owner's account page, not read by the agent) showing a $0 budget/overage limit for Copilot, or a monetary cap of at most $1; (b) GitHub's documented statement that Free-plan usage cannot be billed beyond the plan allowance, supplied by the owner; (c) the owner's explicit written acceptance of a soft credit cap (`--max-ai-credits 30`) with the stated risk. Trials 1–8 remain NOT RUN; human acceptance PENDING; no release readiness claimed.
