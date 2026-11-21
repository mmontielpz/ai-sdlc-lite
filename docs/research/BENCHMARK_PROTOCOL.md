# AI-SDLC Lite — Controlled Benchmark Protocol

**Status:** `PROTOCOL_DEFINED` (**`0` benchmark runs executed; zero fabricated or inferred measurements**)
**Baseline:** `mmontielpz/ai-sdlc-lite` `develop` @ `c4796e0ecc5dd4cf848630a70fb046b2b9131a47` (`2.0.0.dev1`, `EXPERIMENTAL`)

> **Scope & Epistemic Notice:** Formal benchmark refinement is **deferred** until Website Development (`W01`–`W05`, starting in **M064**) supplies concrete real-world tasks. A minimum of **three repetitions (`N >= 3`) is exploratory only** to observe variance—it is **not** proof of statistical significance.

---

## 1. Comparison Arms

1. **Arm A (Baseline):** Native coding agent (e.g., Claude Code) with identical model, permissions, and repository baseline, without an external SDLC framework.
2. **Arm B (AI-SDLC Lite):** Same agent + `ai-sdlc-lite` (`2.0.0.dev1` wheel + `SKILL.md` + BOV Gate 1 / Gate 2).
3. **Comparator Arms (where applicable):** **GitHub Spec Kit**, **OpenSpec**, **BMAD Method**, and **AWS AI-DLC** (version-pinned before execution).

---

## 2. Experimental Controls & Custody

Every comparative run must control and record:
- **Task:** Identical specification, starting Git SHA, and dirty/clean baseline state.
- **Model & Agent:** Identical pinned model identifier, reasoning settings, and agent CLI version.
- **Environment & Permissions:** Identical OS (`Linux`), Python/tool versions, sandbox/permission mode, and network policy.
- **Acceptance Criteria:** Fixed, independent acceptance test suite and review rubric established prior to execution (not modified by the agent).
- **Failed & Interrupted Runs:** All failed, timed-out, `PARTIAL`, `BLOCKED`, and interrupted runs **must be captured and reported**—never excluded from denominators.
- **Missing Telemetry (`UNKNOWN`):** Any unavailable measurement (e.g., unexposed provider tokens, missing USD billing, or unrecorded human wait time) must be recorded explicitly as **`UNKNOWN`**, never estimated or zero-filled.
- **No Fabricated Measurements:** Only directly observed tool outputs and external logs are valid evidence.

---

## 3. Planned Metrics (`METRICS_CATALOG.csv` Aligned)

| Metric | Definition / Purpose | Telemetry Source / Handling |
|---|---|---|
| **Acceptance rate** | Fraction of runs passing independent Gate 2 / test acceptance | Independent human check & test exit codes |
| **Software quality** | Defect/lint/test-pass outcomes and post-task review findings | Independent test suite, static checks, diff review |
| **Tokens** | Input, output, and cached tokens consumed per task | Provider/CLI telemetry if exposed; else `UNKNOWN` |
| **Cost per accepted task** | Total USD spent (including failed/rework attempts) divided by accepted tasks | Provider billing/CLI telemetry if exposed; else `UNKNOWN` |
| **Execution time** | End-to-end wall-clock duration and agent run duration | External timestamps / `experience` journal |
| **Human active time** | Active operator time spent on Gate 1, intervention, and Gate 2 | External operator log (or `UNKNOWN`) |
| **Framework overhead** | Extra tokens, time, and CLI/ceremony steps vs. Arm A baseline | Differential comparison (`verify` `L0` = `0` tokens) |
| **Rework** | Number of rework cycles or rejected Gate 2 attempts before acceptance | External run log / `experience` journal |
| **Regressions** | Previously passing checks broken or unintended files modified | Independent regression suite + `ai-sdlc verify` |
| **Governance compliance** | Adherence to `allowed_paths`, protected paths, and Gate 1/2 rules | `ai-sdlc verify` (`T1`/`T2`) + human audit |

---

## 4. Planned Analysis (Post-M064+ Data Collection)

- **Exploratory vs. Confirmatory Runs:** Initial `N >= 3` runs per arm/task characterize feasibility and variance; larger `N` and formal statistical testing are required before making significance or superiority claims.
- **Pareto & Ablation Studies:** Evaluate quality vs. cost/time/human effort (`R02`, `OPT-08`) and ablations such as `SKILL.md`-only vs. `SKILL.md` + `verify`, and minimal context vs. full docs (`R05`, `OPT-06`).
- **Reproducibility Package:** Publish pinned task SHAs, prompt/contract templates, tool versions, anonymized `experience` journals, and raw external run logs.
