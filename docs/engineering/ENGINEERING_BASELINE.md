# AI-SDLC Lite — Engineering Baseline

**Audited Repository SHA:** `5e67e4598af156cb3ee9f049b7a95060189ce37a` (`develop`)
**Assessment Date:** 2026-11-21
**Product Version / Status:** `2.0.0.dev1` (`EXPERIMENTAL`)
**R001 Research Status:** `NOT_EXECUTED` (handoff prepared; research agenda exists, empirical benchmarks not yet run) **Superseded:** R001 preparation closed as `PARTIAL` on 2026-11-21 (PR #35; `docs/research/RESEARCH_TODO.md`). This baseline is a dated audit of `5e67e45`.

---

## 1. Engineering & Architecture Snapshot

- **Maturity:** `SOLID_EXPERIMENTAL_CORE` — deterministic `L0` verification, descriptor-safe filesystem traversal, and offline wheel distribution are unit-tested (`743` CI tests across `30` modules on Linux); live-agent qualification is `PARTIAL` (`Q2`) and real-project validation is `NOT_MET` (`Q3`).
- **Codebase Size (Static AST at `5e67e45`):**
  - Core (`ai_sdlc/` + `scripts/`): `15` Python files, `5,837` lines, `306` functions (largest: `scripts/verify_scope.py:verify`, `238` lines).
  - Tests (`tests/`): `31` Python files, `11,876` lines, `1,091` functions. *(Note: test line count is a codebase size metric, not a statement of branch/line coverage or runtime safety.)*
- **Runtime Dependencies:** `0` external runtime dependencies (Python `>=3.9` stdlib + Git only; `setuptools` required only at wheel-build time).
- **Architecture & Patterns:** CLI (`ai_sdlc/cli.py`), verifier (`scripts/verify_scope.py`), descriptor-safe initializer (`ai_sdlc/initializer.py`), local-only delivery executor/recover (`ai_sdlc/delivery.py`, `native_git.py`), experimental JSONL Experience journal (`ai_sdlc/experience*.py`), and declarative provider/engine adapters (`adapters/`).
- **Current Autonomy (`A1–A2`):** Human-approved single-agent bounded execution (`A1`) and in-scope micro-cycles (`A2`). Conceptual `A3–A5` tiers are future research only.

---

## 2. Verification, Environment & Distribution Boundaries

- **Verification Boundaries:** Post-execution detection only (`verify` never confines or stops edits during execution and never executes project commands — `T3` absent). Human **Gate 1** (plan approval) and **Gate 2** (independent check re-run & diff acceptance) are mandatory.
- **Supported Environments:** Linux (`ubuntu-24.04`, Python `3.14` primary PR CI; Python `3.9` via manual `workflow_dispatch`). `macOS` and `Windows` are deferred/unqualified.
- **Distribution Readiness:** Offline wheel (`286,724` bytes, `0.752s` build time) installs cleanly without a source checkout (`ai-sdlc --version`, `doctor`, `init --apply|--check|--upgrade|--uninstall`).

---

## 3. Technical Debt, Risks & Intentional Limitations

- **Technical & Architecture Debt (`GF-01`–`GF-04`):** `verify()` monolith (`238` LOC) and `importlib.util` script loading (`GF-01`); preserved local `g2-*` branches and local WIP worktree awaiting owner triage (`GF-02`); 4 separate Git-root validation paths (`GF-03`); Experience schema `/1` refusal on dotted `task_id`s and `BLOCKED` reports with empty `failure_reasons` (`GF-04`).
- **Operational Risks (`GF-12`, `GF-13`):** Prompt injection and untrusted project scripts rely on the agent's native sandbox and human pre-run inspection; local `flock`/TTY confirmation assume a quiescent local filesystem and trusted same-OS-user.
- **Intentional Limitations (`GF-14`–`GF-16`):** Post-execution detection only, no `T3` check execution, and Linux-only support.

---

## 4. Risk & Priority Governance (`GF-05` vs `GF-06`)

- **`GF-05` (`P0`, Operational Release Preparation):** `origin/master` (`7f925cd`) is 69+ commits behind `origin/develop` (`5e67e45`). Promoting `develop` → `master` is required before public experimental distribution.
- **`GF-06` (`P0`, Full Qualification Requirement):** Independent human clean-room qualification (`G3`/`G10`) remains `PENDING` (agent-orchestrated smoke does not satisfy `G3`/`G10`). `G3`/`G10` must **not** be silently waived; any experimental pre-release before `G3`/`G10` requires an explicit owner exception disclosing `G3/G10 PENDING`.

---

## 5. Lightweight Tracking Policy

- **Single Source of Truth:** `docs/engineering/FINDINGS_REGISTER.csv` (`18` findings) and `docs/engineering/METRICS_CATALOG.csv` (`20` metrics). No extra dashboards, databases, or duplicate backlogs.
- **Maintenance Cadence:**
  - *After each material product iteration (e.g., `W01`–`W05`):* update affected finding statuses, record new evidence, add genuinely new findings, update measured metrics, and reassess priority only when justified.
  - *Before each release:* review unresolved `P0` blockers, accepted limitations, and current qualification claims (`Q1`–`Q3`, `G1`–`G10`). Avoid recurring full-project audits unless triggered by a major regression.
