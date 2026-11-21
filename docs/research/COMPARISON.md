# AI-SDLC Lite — Preliminary Qualitative Comparison

> **PRELIMINARY QUALITATIVE COMPARISON**
> This document synthesizes publicly documented design choices from R001 industry research. **Zero empirical benchmarks (`0` runs) have been executed.** No superiority, token-saving, or acceleration claims are made. Any capability not directly verified from primary sources is marked `NOT_VERIFIED`.

**Baseline:** `mmontielpz/ai-sdlc-lite` `develop` @ `c4796e0ecc5dd4cf848630a70fb046b2b9131a47` (`2.0.0.dev1`, `EXPERIMENTAL`)

---

## 1. Summary Overview

| System | Primary Purpose | Ceremony | Runtime Footprint | Verification / Custody |
|---|---|---|---|---|
| **Native Coding Agents** | Fast interactive coding & tool use | Very Low | Agent CLI / IDE | Ad-hoc user inspection; no external digest contract |
| **GitHub Spec Kit** | Upstream spec-to-task decomposition | Medium | Python CLI + Markdown templates | Markdown specs & tasks; `NOT_VERIFIED` for post-exec scope checks |
| **OpenSpec** | Brownfield per-change spec folders | Low | Node/npm CLI + `openspec/` | Markdown proposal/tasks; `NOT_VERIFIED` for digest/Git verify |
| **BMAD Method** | Multi-persona agile simulation | High | Multi-role prompts/workflows | Role-based phase artifacts; `NOT_VERIFIED` for deterministic verify |
| **AWS AI-DLC** | Enterprise 33-stage AI-driven SDLC | High | Workflow definitions + human gates | Stage state & human approvals; `NOT_VERIFIED` offline CLI |
| **AI-SDLC Lite** | Bounded BOV workflow & offline verification | Low | Python `>=3.9` stdlib wheel (`0` runtime deps) + Git | Post-exec `verify` (`T0`–`T2`), `baseline`, `seal`, external `experience` JSONL |

---

## 2. Detailed Profiles

### 2.1 Native Coding Agents (e.g., Claude Code, Codex CLI, Copilot CLI)
- **Primary purpose:** Interactive code generation, editing, debugging, and command execution directly inside a developer workspace.
- **Methodology:** Conversational or loop-based tool execution without a mandated external SDLC gate structure.
- **Architecture:** Vendor-hosted LLM + local CLI/IDE harness with native filesystem/shell tools.
- **Advantages:** Lowest ceremony; minimal setup; immediate iteration speed on ad-hoc tasks.
- **Disadvantages:** No standardized pre-task dirty-baseline snapshot, no external scope/digest contract, and risk of silent scope drift or test/governance edits without manual `git diff` review.
- **Known limitations:** Verification depends on ad-hoc human inspection and agent self-reporting (`T0`). Exact internal telemetry/context management across vendors varies (`NOT_VERIFIED` across all versions).
- **Best-fit use cases:** Exploratory prototyping, one-off scripts, and baseline comparator (`Arm A`) in controlled benchmarks.
- **Source references:** Vendor tool ecosystems (Anthropic Claude Code, OpenAI Codex, GitHub Copilot); [README.md](../../README.md) (`Q2` Claude Code `2.1.329` Linux smoke).

### 2.2 GitHub Spec Kit (`github/spec-kit`)
- **Primary purpose:** Structured specification-driven development turning feature intent into specs, plans, and task lists for coding agents.
- **Methodology:** Sequential spec → plan → task Markdown workflow (`specify init`).
- **Architecture:** CLI scaffolding tool generating project Markdown templates and agent instructions.
- **Advantages:** Clear upstream requirements structure; helps align human and agent before coding begins.
- **Disadvantages:** Adds upstream template ceremony; focuses on spec authoring rather than deterministic post-execution scope/digest verification.
- **Known limitations:** Post-execution Git dirty-baseline preservation, symlink/submodule checks, and hash-chained outcome journals are `NOT_VERIFIED` / out of its primary scope.
- **Best-fit use cases:** Greenfield or feature-scoped projects needing structured specification authoring (potentially complementary upstream of AI-SDLC Lite Gate 1).
- **Source references:** `https://github.com/github/spec-kit`.

### 2.3 OpenSpec (`Fission-AI/OpenSpec`)
- **Primary purpose:** Lightweight spec-driven workflow tailored for brownfield repositories without heavy process overhaul.
- **Methodology:** Per-change modular proposal and task folders (`openspec/`).
- **Architecture:** Node/npm CLI managing change-scoped Markdown artifacts.
- **Advantages:** Low ceremony; well-suited to incremental brownfield changes alongside existing codebases.
- **Disadvantages:** Requires Node/npm runtime; focuses on change-folder spec organization rather than independent Git/digest verification.
- **Known limitations:** Deterministic post-execution `executable_git_config` hardening, external evidence custody, and non-Node environments are `NOT_VERIFIED` / outside design focus.
- **Best-fit use cases:** Teams already using Node/npm who want modular per-change Markdown specs in brownfield repos.
- **Source references:** `https://github.com/Fission-AI/OpenSpec`.

### 2.4 BMAD Method (`bmad-code-org/BMAD-METHOD`)
- **Primary purpose:** Multi-persona agile software development simulation using specialized AI roles (PM, Architect, Developer, QA, etc.).
- **Methodology:** Role-based multi-phase agile ceremonies and handoff artifacts.
- **Architecture:** Structured prompt/persona packs and workflow orchestration templates for AI coding environments.
- **Advantages:** Explicit separation of planning, architecture, and QA perspectives for complex multi-role projects.
- **Disadvantages:** High ceremony and context/token footprint; potential friction for small fixes or single-developer slices.
- **Known limitations:** Measured quality-vs-token efficiency and deterministic post-execution scope enforcement are `NOT_VERIFIED`.
- **Best-fit use cases:** Larger or exploratory projects where multi-persona role separation is desired over minimal context.
- **Source references:** `https://github.com/bmad-code-org/BMAD-METHOD`.

### 2.5 AWS AI-DLC (`awslabs/aidlc-workflows`)
- **Primary purpose:** Enterprise AI-Driven Development Lifecycle orchestrating end-to-end software delivery with human decision gates.
- **Methodology:** High-ceremony multi-stage lifecycle (~33 stages) following an "AI drives, human decides" model with persistent stage state.
- **Architecture:** Structured workflow definitions and stage templates integrated into developer/cloud workflows.
- **Advantages:** Explicit enterprise governance, persistent stage tracking, and human approval checkpoints across the full SDLC.
- **Disadvantages:** Heavy ceremony and stage overhead relative to small/medium tasks or single-repo CLI workflows.
- **Known limitations:** Offline stdlib portability without cloud/enterprise workflow assumptions is `NOT_VERIFIED`.
- **Best-fit use cases:** Enterprise teams seeking comprehensive multi-stage governance across complex organizational SDLCs.
- **Source references:** `https://github.com/awslabs/aidlc-workflows`.

### 2.6 AI-SDLC Lite (`mmontielpz/ai-sdlc-lite`)
- **Primary purpose:** Minimal, offline, deterministic governance and post-execution verification layer (`Bound → Observe → Verify`) for AI coding agents.
- **Methodology:** Single-agent bounded execution (`A1–A2`) with explicit Gate 1 (plan/scope approval) and Gate 2 (independent human check re-run & diff acceptance).
- **Architecture:** Python `>=3.9` stdlib-only CLI (`ai-sdlc`) + `agentskills.io` `SKILL.md` bundle + external JSONL `experience` journal (`0` external runtime dependencies).
- **Advantages:** Zero runtime dependencies; offline wheel distribution; dirty-baseline preservation; honest `T0`–`T2` trust separation; external evidence custody.
- **Disadvantages:** Post-execution detection only (not a runtime sandbox, `GF-14`); no automatic check execution (`T3` absent, `GF-15`); Linux-only (`GF-16`); Claude Code-only target for V1–V3.
- **Known limitations:** `Q2` `PARTIAL` (operator-orchestrated smoke only; `G3`/`G10` `PENDING`, `GF-06`), `Q3` `NOT_MET` (pending `W01`–`W05`), `0` comparative benchmarks executed, and `experience` schema `/1` refuses dotted `task_id`s and `BLOCKED` reports with empty `failure_reasons` (`GF-04`).
- **Best-fit use cases:** Bounded single-agent coding slices where deterministic scope/digest verification and low dependency overhead are prioritized.
- **Source references:** [README.md](../../README.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), [ENGINEERING_BASELINE.md](../engineering/ENGINEERING_BASELINE.md).

---

## 3. Future Comparative Research TODOs

- [ ] **Version-pinned comparison matrix:** Pin exact release tags/commits and CLI versions for Spec Kit, OpenSpec, BMAD Method, and AWS AI-DLC before testing (`OSS_COMPETITIVE_MATRIX.csv`).
- [ ] **Empirical leaderboard:** Execute controlled repeated runs per [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) (`R01`, `R02`, `GF-11`, `GF-17`).
- [ ] **Pareto analysis:** Evaluate quality vs. cost, execution time, tokens, and human active time (`R02`, `OPT-08`).
- [ ] **Independent comparative verification:** Ensure third-party or clean-room verification (`GF-06`) without self-certified superiority claims.
