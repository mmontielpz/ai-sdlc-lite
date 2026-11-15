# Git Delivery Executor (V2-04F)

Reconstructed from V2-04E and mission AI-SDLC-LITE-V2-04F-CODEX-CLI-001;
this is not a recovery of isolated commit 29d98d0.

`ai_sdlc.delivery_executor.Executor(repo, plan, approve, journal, remote=None)`
consumes the unchanged `ai-sdlc-delivery/1` sealed plan. The existing offline
CLI remains read-only. There is no execution CLI and no provider-specific
transport, credential discovery, inference, automatic merge or retry loop.

The host invokes `commit()`, `push()` or `pull_request()`. Each mutable operation
(stage, commit, push, PR creation) requires a separate trusted approval callback
returning exactly True for an intent binding operation, plan digest, repository,
HEAD SHA and authorized files. A JSON authorization reference or digest is never
an approval. The digest binds all remote and PR metadata as well as local inputs.

## Trusted host boundary

The host must provide exclusive repository access, a trusted Git executable on
PATH, a human approval callback, and a durable journal. Its `read(key)` returns
None for absent entries; `write(key, value)` must persist atomically before
returning. Store the journal outside the sealed repository inventory, bind its
ownership to the operator, and retain it across process restarts. Do not use an
in-memory journal for actual delivery. Failure to persist must raise and prevent
the mutation. This library does not implement a journal storage service or locks.
Concurrent hostile writers are outside the supported model.

The optional trusted remote backend implements:

- `ref(destination, ref)`: exact SHA or None for verified absence; errors raise.
- `push(destination, ref, sha, expected)`: atomically check expected remote state,
  enforce a normal non-force fast-forward/create, perform at most one attempt.
- `find_pr(identity)`: None for verified absence or the exact identity dictionary;
  reject duplicates, authenticate repository identity, and raise on unknown state.
- `create_pr(identity)`: create the specified draft/title/body/base/head/HEAD SHA
  once, without retries; authenticate the repository and validate the result.

Identity includes repository, head branch, head SHA and all planned PR metadata.
The backend must prevent duplicates on concurrent creation, never merge, never
force push, never log credentials, and expose no raw credential-bearing errors.
This is a trusted capability boundary, not a sandbox for arbitrary backend code.
No live backend is shipped or qualified by these tests. Remote readiness and
production delivery remain unverified. Plans requiring signing or CI checks fail
closed (`SIGNING_UNSUPPORTED`, `CI_UNSUPPORTED`) rather than claiming evidence.

## Verification and recovery

Execution reuses planner configuration, environment, path and full inventory
checks. It rejects active Git operations, shallow repositories, replacement refs,
attributes and hooks. Child Git receives a minimal environment, disabled system
and global config, disabled hooks and prompts, and no inherited credentials.
Only literal authorized paths are staged; the index must initially be empty.
The staged path inventory must equal the authorized list, including deletions,
and staged blob SHA-256 and modes must match. Base must equal planned HEAD.
No unrelated staged changes can enter the commit. Every listed path must actually
change. Unsupported plans stop without relaxing these checks.

A fresh executor recovers a completed commit only after proving its single parent,
message, exact changed paths, authorized bytes/modes and clean working tree.
A pending staging journal permits inspection of an interrupted stage; approval
for the commit is still required. Local operation failures stop for inspection.

Before remote mutation the executor observes exact state, checks approval and
local inputs, and persists pending intent. The backend must check remote state
atomically when pushing. Any ambiguous mutation or failed readback stops without
automatic retries, regardless of the plan retry allowance. On restart, verified
remote HEAD or exact PR identity can reconcile success; otherwise a pending entry
blocks further mutation. Never delete pending evidence merely to retry.

## Repeatable checks

```sh
python3 -B -m unittest discover -s tests -p 'test_delivery*.py'
python3 -B -m unittest discover -s tests
python3.14 -B -m unittest discover -s tests
# Run the same suite with python3.9 when installed.
git diff --check
```

Tests use disposable local Git repositories and remote doubles. They establish
local behavior and interface orchestration, not live server behavior or authority
of a host-provided approval, journal or backend. CI retains the Python 3.9/3.14
matrix with an updated exact test inventory and existing skip policy.
