# Offline Git delivery contract: ai-sdlc-delivery/1

This first delivery component creates plans and checks their current local inputs. It performs no staging, commits, pushes, PRs, merges, inference, authentication, network requests, subprocess execution or file writes. Stdout is the only output destination; callers own storage. No adapter declarations are read or treated as permission. Dependencies are Python 3.9+ standard library only.

```sh
python3 -B -m ai_sdlc delivery plan --repo /absolute/repo --input /outside/repo/request.json
python3 -B -m ai_sdlc delivery verify --repo /absolute/repo --input /outside/repo/plan.json
python3 -B -m ai_sdlc delivery report --repo /absolute/repo --input /outside/repo/plan.json
```

Save plan stdout outside the target repository. Any added output file inside the repository changes the bound inventory. The commands never create their own output file. `verify` and `report` both revalidate live inputs; report never trusts an earlier receipt. Both accept plan stdout or its standalone `plan` member. Options have the exact order shown. Invalid usage produces sanitized structured evidence.

## Request

All keys below are required. Unknown keys and duplicate JSON keys are rejected at every object level. Strings use printable ASCII, at most 4096 characters; file paths and refs have additional constraints. No credentials, tokens or private content belong in requests. Public destination URLs are restricted to HTTPS without userinfo, port, query or fragment. Local remotes, SSH and remote helper syntax are unsupported in version 1.

```json
{
  "repository": "https://example.invalid/owner/project",
  "expected_branch": "feature/delivery",
  "base_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "head_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "authorized_files": ["README.md", "src/main.py"],
  "operations": ["commit", "push", "pull_request"],
  "commit": {"message": "Add delivery planner", "signing": "required"},
  "remote": {
    "name": "origin",
    "destination": "https://example.invalid/owner/project.git",
    "expected_ref": "refs/heads/feature/delivery",
    "expected_sha": null
  },
  "pull_request": {"title": "Add delivery planner", "body": "Offline validation complete.", "base": "master", "draft": true},
  "required_ci": ["deterministic (3.9)"],
  "authorization_ref": "MISSION=EXAMPLE revision 1",
  "executor": "operator-selected-agent",
  "retry": {"max_attempts": 3, "backoff_seconds": 1}
}
```

`repository` is the destination URL with one terminal `.git` removed. The named local remote must have exactly that destination in `.git/config`. This binds local identity declarations; it does not authenticate the server or establish repository ownership. Repository root and Git directory are absolute paths with no symlink ancestors. Version 1 supports ordinary `.git` directories only; Git pointer files, linked worktrees and external object alternates are blocked. Git configuration is read directly, never evaluated.

Branch and remote refs must be valid conservative `refs/heads/` names. SHA values are lowercase 40 or 64 hex digits with matching base/HEAD lengths. HEAD must be the expected symbolic branch; detached/unborn states are blocked. Loose and packed refs are supported. The base SHA is an expectation, not an asserted ancestor: ancestry is UNKNOWN when not independently established. A differing base places readiness at PARTIAL.

Authorized paths are a nonempty sorted unique list of repository-relative names. Absolute paths, traversal, backslashes, colon, `.git` components, special files and symlinks are refused. The plan's `authorized_state` maps each path to its exact SHA-256 and executable flag, or null for an absent path (an intended deletion). This is a declaration of intended final file state, not proof of a diff against the base. The full working-file inventory, including ignored and unrelated files, is also sealed to detect additions, removals and modifications outside the authorized set. Empty directories are not Git files and are excluded. Known credential store names (`.git-credentials`, `.netrc`, `.ssh`, `.aws`, `.gnupg`, `.azure`) block inventory before their contents are opened. Global/system Git configuration and authentication stores outside the repository are never read.

Operations must be exactly `commit`, `commit,push` or `commit,push,pull_request`, in that order. Commit signing is `required` or `forbidden`. PR metadata is required even for commit-only plans; body may be empty, base is a branch, draft is boolean. CI names are sorted and unique. Authorization reference and executor are nonempty claims. Retry attempts include the first attempt and range from 1 to 3; integer backoff is 0–60 seconds. No retries or operations are executed by these commands.

## Plan integrity

Plan stdout is `{"plan": PLAN, "evidence": EVIDENCE}`. PLAN has exactly these members:

| Member | Meaning |
| --- | --- |
| `contract` | `ai-sdlc-delivery/1` |
| `request` | Validated complete request |
| `snapshot` | Repository identity, canonical root/Git directory, branch, HEAD, local config hash, index hash or null, full regular-file inventory |
| `authorized_state` | Authorized paths mapped to final content hashes/modes or absence |
| `digest` | SHA-256 of canonical JSON of all preceding members |

Canonical JSON uses sorted object keys, separators `,` and `:`, ASCII escaping, no NaN/infinity, and no trailing newline before hashing. Lists retain order. No timestamps or random fields enter the digest. The digest proves integrity, **not authorization**: anyone can recompute it. Verification checks the digest, validates the request again, recomputes the snapshot and requires exact equality. Changed HEAD/branch, configuration, index, file bytes, executable bits or file inventory invalidate it. Write permission observations are deliberately live evidence and are not part of the deterministic digest.

## Evidence and exit codes

Evidence contains only fixed codes and validated structural identifiers, never exception messages or raw configuration. Successful inspection includes plan digest; rejected inputs need not. Evidence fields include `authorization`, `remote_ref`, `ci`, `signing`, `base_ancestry`, `future_write_success` and `mutations`. Unavailable facts are UNKNOWN. `mutations` is always NONE.

| Status | Exit | Meaning |
| --- | --- | --- |
| READY | 0 | Local inputs match; read-only write-access observations pass; no requested external prerequisite remains to be checked |
| PARTIAL | 1 | Local inspection completed but remote operations, CI, signing or a differing base need independent verification |
| BLOCKED | 2 | Known unsafe/changed/invalid inputs or unavailable Git write access |
| UNKNOWN | 3 | Inputs/metadata cannot be read or parsed safely; no readiness conclusion |

Authorization remains UNKNOWN even for READY. READY is local preflight only; it grants no permission. Remote ref expectations are never verified offline. A null expected remote SHA declares expected absence, not observed absence. Signing keys are never sought. Required signing always remains UNKNOWN.

Write observations combine mode write bits and `os.access(W_OK)` on Git directories, refs, HEAD and any existing index. Failure reports GIT_WRITE_BLOCKED, including when the managed sandbox exposes metadata as unwritable. No lock file is created to probe access; successful access observations cannot prove future writes or sandbox behavior, so `future_write_success` remains UNKNOWN. No privilege escalation, permission repairs or alternate write routes exist.

Configuration validation uses a conservative allowlist: ordinary core format/filemode/bare=false/logging/case/Unicode options, user name/email, remote URL/fetch and branch remote/merge. Unknown sections/options, includes, credential helpers, filters, executable configuration and worktree config are refused; active hook files are refused (regular `.sample` files may remain). Any `GIT_*` environment variable blocks preflight. User/global configuration and authentication state remain unexamined and must be independently checked before any future executor. This component does not qualify an execution environment.

Reads are limited to 16 MiB per file and 10,000 regular working files. Larger inputs fail closed. Inventory covers content and executable flags, not ACLs, ownership or every Git object. Concurrent hostile filesystem mutation is outside this snapshot preflight's guarantees; stop concurrent writers and reverify immediately before any separately authorized delivery action. No generic runner or execution handoff is implemented.
