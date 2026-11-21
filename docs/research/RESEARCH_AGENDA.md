# AI-SDLC Lite — Research Agenda

**Research Domain:** Efficient Agentic Software Engineering  
**Status:** `RESEARCH_PLAN` (conceptual research tracks and experimental protocols; **not** implemented runtime capabilities).

---

## 1. Primary Research Inspiration

- **Belcak et al. (2025)**, *"Small Language Models are the Future of Agentic AI"*, NVIDIA Research, `arXiv:2506.02153` ([arXiv](https://arxiv.org/abs/2506.02153) · [NVIDIA LPR](https://research.nvidia.com/labs/lpr/slm-agents/)).
  - *Core thesis:* Small Language Models (SLMs) are often sufficiently powerful, operationally suitable, and economically viable for modular agentic sub-tasks, motivating **heterogeneous agentic systems** that reserve larger frontier LLMs for genuinely open-ended reasoning.
  - *Boundary:* Cited strictly as **research inspiration**, not as evidence or proof of AI-SDLC Lite performance.

---

## 2. Eight Research Tracks (`R01`–`R08`)

| Track | Title | Core Question |
|---|---|---|
| **R01** | **Efficient AI-SDLC** | How minimal can governance and BOV workflows remain while preventing scope drift and unverified claims? |
| **R02** | **Multi-Objective & Pareto Optimization** | How do workflow, context, and model choices trade off quality, cost, latency, tokens, and human effort? |
| **R03** | **Small Language Models (SLMs)** | Which bounded SDLC sub-tasks (planning lint, template filling, small fixes, test authoring) can be solved reliably by SLMs? |
| **R04** | **Adaptive Model Routing** | When should a task escalate or route across deterministic tools, SLMs, efficient LLMs, and frontier LLMs? |
| **R05** | **Context Engineering & Optimization** | How does structured BOV context reduce wasted tokens and rework without sacrificing correctness? |
| **R06** | **Experience-Driven Learning** | How can validated outcome journals (`ai-sdlc-experience-event/1`) guide safer, cheaper execution across projects? |
| **R07** | **Deterministic Governance & Verification** | Which invariants belong in zero-inference deterministic code (`verify`, `seal`, `baseline`) vs model prompts? |
| **R08** | **Cross-Domain Generalization** | How do findings transfer across Website (`W01`–`W05`), CLI (`JACK`), `TAKO`, `FOB`, and `Physical AI`? |

---

## 3. Multi-Objective Formulation (Conceptual)

### Candidate Objectives (Subject to Mandatory Safety, Governance & Acceptance Constraints)
- **Maximize:** software quality (independent acceptance pass rate, defect-free delivery).
- **Minimize:** total delivery cost (USD), execution time, human intervention count, token/compute overhead, and residual risk.

### Conceptual Decision Space & Candidate Methods
- **Decision Variables:** model selection, context configuration, agent execution strategy, verification strategy, experience reuse strategy.
- **Candidate Methods (unselected; no premature algorithm commitment):** Pareto dominance analysis, NSGA-II, NSGA-III, multi-objective Bayesian optimization, and adaptive execution policies.

---

## 4. Conceptual Heterogeneous Execution Tiers (`L0`–`L4`)

> **Disclaimer:** `L0`–`L4` are **conceptual research tiers**, not implemented runtime routing capabilities. Today AI-SDLC Lite implements `L0` deterministic tools and supports `L4` human gates with a single external coding agent (`Claude Code`).

| Tier | Layer | Role |
|---|---|---|
| **L0** | Deterministic code & tools | `ai-sdlc` CLI (`baseline`, `verify`, `seal`, `result-template`, `experience`), linters, test runners |
| **L1** | Small Language Models (SLMs) | Conceptual future tier for narrow, structured, repetitive sub-tasks |
| **L2** | Efficient Language Models | Conceptual future tier for standard implementation slices |
| **L3** | Frontier Language Models | Complex architecture, ambiguous debugging, multi-file reasoning |
| **L4** | Human Judgment & Acceptance | Gate 1 plan approval, Gate 2 independent verification & acceptance |

```mermaid
flowchart TB
  REQ["Bounded Task (Gate 1 Approved)"] --> L0["L0: Deterministic CLI & Checks"]
  L0 -- "Needs inference (Conceptual)" --> ROUTE{"Future Adaptive Policy"}
  ROUTE -. "Simple / structured" .-> L1["L1: SLM (Conceptual)"]
  ROUTE -. "Standard slice" .-> L2["L2: Efficient LLM (Conceptual)"]
  ROUTE -. "Complex reasoning" .-> L3["L3: Frontier LLM (Conceptual)"]
  L1 & L2 & L3 --> VER["L0: ai-sdlc verify (Post-Execution)"]
  VER --> L4["L4: Human Independent Check & Gate 2"]
```

---

## 5. Benchmark Direction

- **Candidate Comparison Groups:** Native coding agents (baseline), GitHub Spec Kit, OpenSpec, BMAD Method, and other relevant OSS frameworks.
- **Mandatory Experimental Rigor:** Controlled conditions, equivalent task requirements, independent acceptance criteria, repeated runs, cost per accepted task, quality/success rate, human effort, failure & regression analysis, statistical uncertainty, Pareto frontier analysis, ablation studies, and full reproducibility. **Zero performance results are claimed or invented here.**

---

## 6. Scientific Publication Direction

- **Candidate Title:** *"AI-SDLC Lite: Towards Pareto-Efficient and Experience-Driven Agentic Software Engineering"*
- **Target Outputs:** arXiv preprint *(note: an arXiv preprint does not constitute peer-reviewed validation)*, open-source framework, reproducible experimental protocol, benchmark tasks, anonymized execution evidence, comparative results, ablation studies, and reproducibility package.

### Epistemic Classification
| Category | Meaning in This Project |
|---|---|
| **Implemented Capabilities** | Offline Python stdlib CLI (`ai-sdlc`), BOV Skill bundle, `verify`/`seal`/`baseline`, `delivery` local commit, `experience` JSONL capture/validate |
| **Observed Evidence** | `743` CI unit tests (`Q1` PASS); single operator-orchestrated Claude Code `2.1.329` Linux smoke (`Q2` PARTIAL; `G3`/`G10` PENDING) |
| **Research Hypotheses** | BOV + Minimum Sufficient Intelligence (`L0`–`L4`) + Experience feedback can improve Pareto efficiency |
| **Proposed Future Capabilities** | Adaptive routing, automated benchmarks, Experience export/analysis, `discover`/`govern check`/`task check` |
| **Demonstrated Scientific Contributions** | **None claimed yet** (pending controlled M064+ Website experiments & benchmarks) |

```mermaid
flowchart LR
  EXP["Real Projects (W01-W05, JACK, TAKO)"] --> J["Validated Experience Journals (T0-T2)"]
  J --> ANA["Pareto & Ablation Analysis"]
  ANA --> HYP["Updated Hypotheses & Framework Improvements"]
  HYP --> EXP
```
