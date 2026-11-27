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

---

## 5. Website First pilot measurement (M1-M5)

Manual recording in the `RESULT.md` Observations rows (no telemetry). Every task is recorded, including failed, blocked, abandoned and rejected ones, with a terminal status (accepted, rejected, blocked, abandoned, in progress) and its elapsed observation time. Only accepted tasks enter per-accepted-task ratios, and the number of non-accepted tasks is always reported beside them. Missing values are UNKNOWN with a reason, never zero or estimated.

| Metric | Definition (unit) | Start and stop | Evidence source | Limitations |
| --- | --- | --- | --- | --- |
| M1 time to accepted task (seconds) | wall time from the Gate 1 approval to the Gate 2 acceptance; human waiting time noted separately | timestamps with timezone | timestamps recorded in `RESULT.md`; shell or Git times as a cross-check | includes human thinking time; one run supports no generalization |
| M2 corrective interventions (count) | human messages after Gate 1 that correct, redirect or re-explain, or hand-made fixes, each listed with its reason. Governance interventions (Gate 1, Gate 2, plan-required permission approvals) are recorded separately and are never corrective | Gate 1 to terminal status | operator tally; native permission prompts counted separately; partial tallies labelled partial | operator-dependent |
| M3 rework cycles (count) | returns to a previously complete state because a stated requirement or acceptance criterion demonstrably failed, found by verify, Gate 2, a check, review or the agent's own check before formal verification. Planned iterations and approved scope revisions are not rework (scope revisions are recorded separately) | attempts on the task | `verify` reports, `experience record-verify` events (T2), `RESULT.md` rows | depends on honest attempt boundaries |
| M4 tokens and provider-reported cost | input, output and cache tokens and cost as separate rows, only as the provider reports them | task window | provider or CLI report when available | interactive subscription sessions may expose none; cost is not derived from tokens |
| M5 instruction-conflict encounters (count) | times the agent or the human finds an instruction that conflicts with another or is outdated, with file references | session | manual tally | subjective; not in the metrics catalog |

Interpretation: read efficiency figures only together with verification and acceptance outcomes; a reduction in time, tokens or interventions is not an improvement if correctness or required quality decreases; a single execution supports no causal claim. The remaining catalog metrics stay deferred.
