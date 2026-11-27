# AI-SDLC Lite — Research TODO & R001 Closeout

**Status:** `PARTIAL` (Initial R001 preparation closed; transitioning to **M064 Website Development**)
**Current Documentation Baseline:** `c4796e0ecc5dd4cf848630a70fb046b2b9131a47` (`develop`, plus this closeout)
**Frozen Framework Source Baseline:** `5e67e4598af156cb3ee9f049b7a95060189ce37a` (`ai_sdlc/`, `scripts/`, `pyproject.toml` unchanged since `b2acffd4327b5912809b9832adb674a5dc79b982`)
**Empirical Benchmark Runs Executed:** `0`

---

## 1. R001 Research Package Preservation Record

An independent review archive (`AI-SDLC-Lite-R001-Research-Review.zip`) was exported read-only prior to closing R001 preparation:

| Field | Value |
|---|---|
| **Archive Filename** | `AI-SDLC-Lite-R001-Research-Review.zip` |
| **Archive SHA-256** | `335419fb26844eee690776d5dda2ac3941284535a83a5c880f19f76648295af5` |
| **Packaged Artifacts** | `27` (`17` external R001/M063F deliverables + `10` repository context snapshots; `30` zip entries including `MANIFEST.csv`, `MISSING_ARTIFACTS.md`, `RESEARCH_REVIEW_SUMMARY.md`) |
| **Missing Research Deliverables** | `4` (`STATE_OF_THE_ART.md`, `LITERATURE_MATRIX.csv`, `OSS_COMPETITIVE_MATRIX.csv`, `WEBSITE_EXPERIMENTAL_PLAN.md`) |
| **Canonical Findings Register** | [docs/engineering/FINDINGS_REGISTER.csv](../engineering/FINDINGS_REGISTER.csv) (`18` findings, valid CSV; supersedes the malformed pre-M063F3A external draft) |
| **R001 Status** | `PARTIAL` (Zero empirical benchmark runs executed; zero fabricated metrics) |

---

## 2. Consolidated Research Backlog (`DONE` / `PARTIAL` / `TODO` / `DEFERRED`)

Canonical engineering findings (`GF-01`–`GF-18`) and metrics (`20` metrics) remain in [FINDINGS_REGISTER.csv](../engineering/FINDINGS_REGISTER.csv) and [METRICS_CATALOG.csv](../engineering/METRICS_CATALOG.csv) and are referenced here rather than duplicated.

| Area | Status | Track / Refs | Current Evidence & Next Action |
|---|---|---|---|
| **1. Scientific literature** | `PARTIAL` | `R03`, `R04`, `R08` | Primary inspiration anchored on Belcak et al. (2025, `arXiv:2506.02153`) and `RESEARCH_AGENDA.md`. Formal `STATE_OF_THE_ART.md` and `LITERATURE_MATRIX.csv` remain `TODO`. |
| **2. Industry frameworks & playbooks** | `DONE` | `R01`, `R05`, `R07` | Synthesized across 12 industry references (Anthropic, OpenAI, Microsoft/GitHub, NVIDIA, AWS, Google/DORA/SRE, Fowler/Thoughtworks) in R001 review package. |
| **3. Standards applicability** | `DONE` | `GF-05`, `GF-06`, `GF-14` | Mapped 15 standards/frameworks (ISO/IEC 12207/15288/25010/42001/23894, SWEBOK, NIST AI RMF/600-1/SSDF, OWASP, SLSA, SPDX, OTEL, SPACE/DevEx, Lean/SRE) in R001 review package (`ALIGNMENT != CERTIFICATION`). |
| **4. Engineering patterns** | `DONE` | `GF-01`, `GF-03`, `GF-08` | Cataloged 15 software, reliability, governance, efficiency, and HAI patterns against Lite's stdlib core (`743` CI tests, `Q1` PASS). |
| **5. Competitive landscape** | `PARTIAL` | `R01`, `COMPARISON.md` | Qualitative differentiation recorded in [COMPARISON.md](COMPARISON.md); formal `OSS_COMPETITIVE_MATRIX.csv` and version-pinned verification remain `TODO`. |
| **6. Framework comparison matrix** | `PARTIAL` | `COMPARISON.md` | Preliminary qualitative comparison completed (`PRELIMINARY QUALITATIVE COMPARISON`); version-pinned matrix remains `TODO`. |
| **7. Advantages & disadvantages** | `PARTIAL` | `COMPARISON.md` | Qualitative trade-offs documented without superiority claims; empirical verification remains `TODO`. |
| **8. Benchmark methodology** | `PARTIAL` | `R01`, `R02`, `BENCHMARK_PROTOCOL.md` | Exploratory protocol defined in [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) (`0` runs); formal refinement deferred post-Website pilot. |
| **9. Empirical leaderboard** | `TODO` | `R01`, `R02`, `GF-11`, `GF-17` | Requires controlled repeated runs across Native, Spec Kit, OpenSpec, BMAD, and AI-SDLC Lite. |
| **10. Pareto fronts** | `TODO` | `R02`, `OPT-08` | Requires repeated-run quality/cost/latency/human-effort dataset (`N >= 3` exploratory, larger `N` for significance). |
| **11. Multi-objective optimization** | `DEFERRED` | `R02`, `OPT-08` | Candidate methods (Pareto dominance, NSGA-II/III, multi-objective Bayesian optimization) unselected until benchmark data exists. |
| **12. Token & context efficiency** | `TODO` | `R05`, `GF-09`, `OPT-03`, `OPT-06` | Capture token/cost telemetry during `W01`–`W05` (or `UNKNOWN` if unavailable); run context ablation post-pilot. |
| **13. Human-agent efficiency** | `TODO` | `R01`, `GF-09`, `OPT-03` | Measure `human_active_time`, `human_interventions`, and `rework_cycles` during `W01`–`W05` (`SPACE`/`DevEx`). |
| **14. Autonomy & micro-progress** | `PARTIAL` | `WORKFLOW.md`, `A1–A2` | `A1–A2` micro-cycles and `interrupted` state implemented; `A3–A5` progressive autonomy `DEFERRED` pending `W01`–`W05` evidence. |
| **15. SLM/LLM routing** | `DEFERRED` | `R03`, `R04`, `OPT-07`, `GF-18` | Conceptual `L0`–`L4` tiers only; no runtime routing until `W01`–`W05` baseline and multi-model benchmarks exist. |
| **16. Multi-agent architectures** | `DEFERRED` | `R01`, `R04` | Intentionally single-agent (`A1–A2`) per Anthropic/OpenAI "start simple" guidance; revisit only on demonstrated need. |
| **17. Experience capture & reuse** | `PARTIAL` | `R06`, `GF-04`, `OPT-05` | `ai-sdlc experience` JSONL capture/validate implemented (`EXP-01A/B`); cross-project reuse `DEFERRED`; schema `/2` (`GF-04`) evaluated post-pilot. |
| **18. Website experiments (`W01`–`W05`)** | `TODO` | `GF-07`, `GF-09`, `GF-10`, `OPT-03` | Transitioning immediately to **M064** (`W01` Static Website first). `WEBSITE_EXPERIMENTAL_PLAN.md` to be scoped inside M064. |
| **19. Cross-domain generalization** | `DEFERRED` | `R08`, `GF-16` | Deferred until post-Website (`JACK`, `TAKO`, `Private Project A`, `Physical AI`; cross-OS support `GF-16` if demand arises). |
| **20. Ablations** | `TODO` | `R05`, `OPT-06` | Planned: Skill-only vs Skill + `verify`, minimal `SKILL.md` vs full docs. Depends on Website task suite. |
| **21. Scientific reproducibility** | `TODO` | `GF-05`, `OPT-04` | Requires pinned SHAs, anonymized `experience` journals, external evidence logs, and SLSA-style release provenance (`OPT-04`). |
| **22. arXiv publication** | `DEFERRED` | `Stage 11` | Candidate preprint after `W01`–`W05`, controlled benchmarks, and ablations *(note: arXiv != peer-reviewed validation)*. |

---

## 3. Website Development Transition (`M064` Readiness & Boundaries)

**Research completion is not a prerequisite for supervised Website Development.** `W01` (Static Website) can begin immediately under supervised **Gate 1** and **Gate 2** execution using the frozen `2.0.0.dev1` framework and existing `ai-sdlc` telemetry / Experience tools (`baseline`, `result-template`, `verify`, `seal`, `experience`).

### Baseline & Artifact Provenance Distinction
- **Current documentation baseline:** `c4796e0ecc5dd4cf848630a70fb046b2b9131a47` (`develop`, plus this R001 closeout PR).
- **Frozen framework source baseline:** `5e67e4598af156cb3ee9f049b7a95060189ce37a` (`ai_sdlc/`, `scripts/`, `pyproject.toml` verified unchanged since `b2acffd4327b5912809b9832adb674a5dc79b982`).
- **Qualified wheel SHA-256:** `94bc0f9317a15a162820e44517186f554c36c0330868aa6d9170aa6a7793f991` (`ai_sdlc_lite-2.0.0.dev1-py3-none-any.whl`, built from `b2acffd4327b5912809b9832adb674a5dc79b982`; do **not** claim a wheel was built from a newer commit without fresh build provenance).

### Preserved Limitations & Release Blockers
- **Open Release Blockers:** `GF-05` (`develop` → `master` promotion pending) and `GF-06` (independent human clean-room qualification `G3`/`G10` `PENDING`, not waived).
- **Qualification State:** `Q1` `PASS` (`743` Linux CI tests), `Q2` `PARTIAL` (operator-orchestrated Claude Code `2.1.329` Linux smoke), `Q3` `NOT_MET` (pending `W01`–`W05`).
- **Safety & Platform Boundaries:** `ai-sdlc verify` is post-execution detection only (`GF-14`, not runtime confinement) and never executes checks (`GF-15`, `T3` absent); supported environment is Linux only (`GF-16`, `macOS`/`Windows` deferred).
