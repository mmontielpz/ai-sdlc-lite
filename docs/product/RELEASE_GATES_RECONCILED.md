> **Product-planning artifact (PB-003), stored 2026-11-18.** Owner-approved inputs are limited to: Claude Code as the only targeted provider for V1–V3 (amends D6); preserve existing adapters; project configuration under `.ai-sdlc-lite/`; the Product Baseline track is additive and supersedes no historical decision; G1–G10 and D1–D14 intact; Godot/FOB/Studio off the V1 critical path; Linux first; planning artifacts under `docs/product/`. **Everything else in this document is a proposal, not an approved decision**, and nothing here is a capability unless stated as existing. Content below is the original text, with one local-environment reference generalized; see [README](README.md).

# RELEASE_GATES_RECONCILED (G1–G10 preserved verbatim; Claude-first application; Preview vs Stable)

OD-03: existing gates are preserved; none is weakened, replaced or bypassed. Gate text below is the ROADMAP's own wording. "Application" says how it is met under OD-01; it never lowers the bar. Status = develop @ 6430dca unless noted. Proposed additions (PB criteria) are labelled and **do not replace** G-gates.

**As of note (2026-11-26).** Statuses in this document are as of develop @ 6430dca (2026-11-18). Current gate and qualification status is kept in `QUALIFICATION_MATRIX.md` (Q1-Q3 model, 2026-11-21); this document owns the gate requirements and the Preview / Stable definitions.

## 1. The ten gates
| Gate | ROADMAP requirement (unchanged) | Claude-first impact | Application / evidence | Preview | Stable | Status today |
|---|---|---|---|---|---|---|
| **G1** Deterministic verification | `verify` is stable, versioned, fail-closed, tested with fixtures | none | suite green on Python 3.9 and 3.14 in CI; goldens unchanged unless logged; compatibility checklist per increment | required | required | PARTIAL → effectively met by 548 tests/CI; formal gate record absent |
| **G2** Honest security boundaries | four-class statement in SECURITY.md; no enforcement claim without independent evidence | none | new commands add no execution surface; claims policy; Claude-specific installs documented as instruction-only/detection, not sandbox | required | required | PARTIAL |
| **G3** Independent evidence | qualification run and recorded by someone other than the implementing agent (D9: a person) | **clarify**: Claude Code is likely both implementer and agent under test → same-family risk | unchanged: a **person** other than the implementing agent runs/records the qualification and the clean-room procedure; agent self-reports never count | required (≥1 independent run) | required (independent evidence for each stable claim) | NOT MET |
| **G4** Recovery tests | interrupted-task and rollback fixtures for the CLI, not only the installer | none | CLI fixtures (init, result-template, baseline, new commands' `--out`) | required | required | NOT MET |
| **G5** Agent qualification | each agent named supported has a VERIFIED smoke row; unlisted ones say "not verified" | **none in text; narrows the set**: only Claude Code can be named supported | Claude Code: dated VERIFIED smoke row for exact agent+platform+version (matrix rule 3). Copilot/Codex/Antigravity: "not verified (not in committed scope)" — existing PARTIAL history stays recorded, never promoted | required (Claude Code smoke) | required (Claude Code smoke; deep only if "qualified" is claimed) | NOT MET (Claude Code: no row) |
| **G6** Platform qualification | Linux, macOS, Windows each VERIFIED or explicitly excluded | none (platform support **not approved**, OD-05) | Preview: Linux VERIFIED, macOS/Windows **explicitly excluded** in release notes; Stable: owner decides per platform | required (exclusion statement) | required (verified or excluded, owner-decided) | NOT MET (Linux suite only) |
| **G7** Multi-project validation | ≥4 unlike use cases, one brownfield | none (all runs with Claude Code) | Public Preview and Stable: ≥4 unlike use cases incl. one brownfield, matrix rows. Internal V1 Experimental dogfood runs count as evidence but do not by themselves meet G7 | required in full (see §3) | required in full | NOT MET |
| **G8** CI | automated matrix on the public repository | none | CI runs deterministic tests (3.9, 3.14) — live agents cannot run in CI (paid/auth), so agent evidence is human-recorded (G3/G5) | required (Linux matrix) | required (+ any platforms the owner includes) | PARTIAL (Linux 3.9/3.14 observed passing) |
| **G9** Security reporting route | verified working private route (`SECURITY.md`) | none | re-verify at release time; record the observation | required | required | NOT MET (reported enabled earlier; must be re-verified) |
| **G10** Docs and install validation | clean-room install and first task by a new reader | **clarify**: first task is performed with Claude Code | a person other than the implementing agent follows the docs from a clean directory to a verified result with Claude Code; transcript recorded | required | required | NOT MET |

**Gates unchanged in text: all ten.** No gate dropped, no threshold lowered. The only "narrowing" is that G5 now applies to one agent because only one is named.

## 2. Conflicts between G1–G10 and the Claude-only strategy
| # | Candidate conflict | Verdict |
|---|---|---|
| 1 | G5 vs Claude-only | **No conflict**; satisfied by naming only Claude Code supported |
| 2 | G3 independence vs same model family | **No conflict**, **risk noted**: requires a person; I recommend the independent run use a different Claude Code *session and user* at minimum, but the gate (person) is the controlling text |
| 3 | G7 breadth with one provider | **No conflict**; breadth is projects, not providers |
| 4 | G6 vs unapproved platform support | **No conflict**; "explicitly excluded" is permitted by the gate; the exclusion needs owner approval |
| 5 | G8 vs live agent runs | **No conflict**; agent evidence is manual by design |
| 6 | ROADMAP P3/P5 deliverables (adapter pages and smoke for Copilot, Codex, Agy) | **Roadmap deliverables, not gates**; no longer committed (OD-01) — recorded as scope reduction, not as a gate change |
| 7 | Matrix/README statements about Copilot/Codex | **Wording only**: keep as dated historical evidence, never "supported"; avoid the contradiction between "owner-observed live Copilot PASS" in README and "smoke NOT RUN" in the matrix by adding a clarifying dated note (matrix rule 1 forbids editing prior rows) |
| 8 | GQ-RUNTIME dependency on CODEX-004 | **Not a gate**; sequence conflict pending (OWNER_DECISION_AMENDMENTS P-1) |
No conflict requires weakening, replacing or bypassing a gate.

## 3. Preview vs Stable (separate qualification targets, OD-05)
| | **Preview** | **Stable** |
|---|---|---|
| Purpose | first public tagged release with an explicit limitations statement (ROADMAP P6 allows this) | meets every gate without a limitations carve-out for gates |
| Gates | G1, G2, G3 (≥1 independent run), G4, G5 (Claude Code smoke), G6 (exclusion statement), G7 **in full** (≥4 unlike use cases incl. one brownfield), G8 (Linux), G9, G10 | G1–G10 all fully |
| G7 meaning | original requirement, unchanged: ≥4 unlike use cases incl. one brownfield | same |
| Claude Code claim | "smoke-tested with Claude Code <version> on Linux on <date>" | same, plus deep qualification only if "qualified" is claimed |
| Must say | not verified: macOS/Windows, other agents, independent execution, OS isolation, delivery executor in real use | the remaining not-verified list, if any |
| Forbidden in both | "certified", "secure", "universal", "supports <agent/platform/version>" without its row, productivity/cost claims, "independently executed" for anything not run by a tool |

### 3.1 Release tiers and what each claims
| Tier | What it is | G1–G10 release compliance claimed? |
|---|---|---|
| **V1 Experimental** | internal, controlled dogfood and the minimum Claude Code qualification work (ROADMAP/PB track); not a public release | **No.** It claims no G1–G10 release compliance. Evidence gathered (dogfood runs, smoke rows) is recorded and may later count toward gates, but the tier itself is not gate-compliant. |
| **Public Preview** | first public tagged release (ROADMAP P6) | Only when every Preview-required row in §1 is evidenced, **including G7 in full**. A partial G7 is not sufficient for a gate-compliant Preview. |
| **Stable** | all gates fully | Yes, when G1–G10 are all met. |

The original G7 requirement (at least four unlike use cases, including one brownfield) is preserved for both Preview and Stable. An earlier draft proposed treating G7 as "partial" for Preview. That idea is **withdrawn from this document** and is not part of the current release policy. Any future proposal to relax a Preview gate is **unapproved, outside the current release policy**, and would require a separate explicit owner decision recorded in ROADMAP; until then no document may describe a release with partial G7 as gate-compliant. A release that does not meet every Preview-required row may be published only under a different name (such as V1 Experimental) and must not claim G1–G10 compliance.

### 3.2 Professional experimental release objective (OD-32): readiness checklist and capability maturity

This subsection adds no gate and changes none: sections 1 to 3.1 govern, including `G7` in full for any gate-compliant Preview. **Professional public repository presentation** (documentation, hygiene, branding and contribution experience in the public repository) is distinct from **formal tagged release qualification**. Presentation work claims no gate, and nothing here authorizes a tag, publication or release.

Qualification status stays in `QUALIFICATION_MATRIX.md`. "Ready" in this checklist never stands in for missing gate evidence.

| Area | Ready when | Existing reference |
|---|---|---|
| Repository and branch hygiene | M-01 closed | M-01 |
| Security and privacy | disclosure accepted, verifier blocker resolved, reporting route verified | M-02, M-03, G2, G9 |
| CI and tests | required matrix and recovery fixtures evidenced | G1, G4, G8 |
| Packaging and installation | versioned artifact with digest; clean-room install | M-04, G10 |
| Developer experience and presentation | README, contribution path, branding and release notes accepted | M-05, M-08 |
| Methodology and harness engineering | BOV and harness boundaries documented and tied to checks | G1, G2 |
| Agent and platform | dated rows; exclusions stated; independent run | G3, G5, G6; M-07, M-11 |
| Product validation | `W01` and further use cases recorded | G7 |
| Benchmarking and official website | results or an explicit "not run"; `W02` published when authorized | M-13, M-10 |
| Publication | release policy resolved and owner authorization | RG-1 to RG-3 |

**Capability maturity method.** Rate each capability by the highest step that has evidence; each step requires the earlier ones. There are no scores or averages.

| Step | Evidence required |
|---|---|
| Documented | accepted description only |
| Implemented | files at a pinned revision |
| Tested | deterministic checks recorded at that revision |
| Observed | dated run with agent, platform and version |
| Qualified | `QUALIFICATION_MATRIX.md` reporting rules: smoke for "supported", deep for "qualified" |
| Pilot-used | accepted real task, with failures included in the record |

Independent verification (`G3`) is a separate evidence dimension, recorded beside the step. Record revision, evidence ID and limitations. A changed revision makes a rating stale until rechecked; missing evidence is `UNKNOWN`. No capability is rated here.

## 4. Proposed PB acceptance criteria (additions, not replacements)
Independent of G1–G10, the product acceptance criteria from PB-002 (determinism of discovery, adversarial fixtures, no execution/network/model calls, schema validators + goldens, governance override rules, task lint, trust wording, compatibility checklist, docs truth) remain **proposed** criteria supporting G1/G2/G10. They are additive evidence for the gates above, not owner-approved gates.

## 5. Unresolved decisions (nothing assumed approved, OD-05)
| ID | Decision | Notes |
|---|---|---|
| RG-1 | **Branch policy** (D8): release from `develop`? promote to `master`? (`master` is 34+ commits behind; README install URLs point at it) | owner |
| RG-2 | **Tagging scheme and version** (pyproject said 0.1.0 on 2026-11-18; the version is now `2.0.0.dev1`, preserved by OD-10; no release or tag is authorized) | owner |
| RG-3 | **Publication** (GitHub release only? PyPI?) — D1 says module/`python -m` first, PyPI after platform work | owner |
| RG-4 | **Platform support** (G6) per OS | owner |
| RG-5 | **Claude Code support window** (tested version only vs range) | P-3 |
| RG-6 | **Authorization/budget for live smoke runs** (D3) | owner |
| RG-7 | *Closed in this document:* Preview requires full G7. Any relaxation is a separate, unapproved proposal and not current policy | owner only, if ever raised |
| RG-8 | Who is the independent person for G3/G10 and when | owner |

## 6. Go / no-go
Preview ships only when every Preview-required gate row is evidenced and the owner accepts the exact revision; a failing row is never reworded to pass. Stable additionally needs all Stable rows. Evidence handling: dated rows never edited; CI vs local counts separate; UNKNOWN never zero; evidence outside the repo with hashes until the owner chooses a home (P-7).
