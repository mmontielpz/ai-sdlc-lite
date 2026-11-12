# Contributing

AI-SDLC Lite is in early development toward V1.0.0. Small documentation improvements and reports of confusing steps are useful. Keep the core beginner-friendly, tool-agnostic, and free of mandatory dependencies or services.

## Propose a bounded change

- Explain the problem, intended behavior, scope, and how the change will be checked.
- For new features, policy changes, or wider restructuring, agree on the plan with a maintainer before implementation. Use an issue or pull request when repository collaboration is available.
- Keep each change focused. Preserve existing work and avoid unrelated formatting or generated files.

Aim for one useful vertical slice with observable value, then use feedback to choose the next increment. Follow the [incremental delivery guidance](WORKFLOW.md#deliver-one-useful-increment); keep one authoritative task brief and one result record, reusing relevant context and still-valid evidence. Match checks to risk and maturity. A verified PoC, Prototype, or Pilot does not establish production readiness.

## Prepare for review

Read [README.md](README.md) and follow its two human gates and outcome definitions. AI assistance is welcome; the contributor remains responsible for accuracy, rights, and verification. Disclose material AI assistance in the change description without uploading private prompts or transcripts.

For documentation changes, check Markdown headings, code fences, local links, terminology, and consistency with the project status. Check external references when changing claims about them. For future code or examples, run the documented deterministic checks and report commands and actual results. State what was not tested and why. Do not claim compatibility based only on a tool's documentation.

Include the problem solved, resulting behavior, validation evidence, and remaining limitations in the review description. A maintainer must explicitly accept the reviewed revision. Acceptance does not independently authorize publication or release.

For GitHub contributions, follow the [optional task-to-merge mapping](WORKFLOW.md#optional-github-mapping). Link the task and result in the PR rather than duplicating them. PR and merge permissions follow repository rules and explicit authorization; an existing approval need not be repeated. Local contributions do not require GitHub.

## Rights and conduct

Submit original work or material you have permission to contribute under the [MIT License](LICENSE). Preserve applicable notices, attribute external ideas, and identify third-party material and its license before inclusion. Do not submit proprietary code, private data, secrets, or copied vendor documentation. Contributions to original project material use the same MIT license.

Be respectful, explain technical disagreements, and focus feedback on the work. Report security-sensitive concerns according to [SECURITY.md](SECURITY.md), rather than in public issues.

Versioning policy and unreleased changes are recorded in [CHANGELOG.md](CHANGELOG.md).
