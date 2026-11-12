# Security

AI-SDLC Lite contains process documents and a small example. It does not enforce agent permissions or provide a security boundary. Use repository access controls, tool permissions, and human review.

## Reporting a vulnerability

**Private reporting route: ENABLED for `mmontielpz/ai-sdlc-lite`.** Observed 2026-11-12T21:31:53Z via `gh api repos/mmontielpz/ai-sdlc-lite/private-vulnerability-reporting`, which returned `{"enabled":true}` immediately after enabling it with the same endpoint. The **Report a vulnerability** button was not independently checked in the web interface, and no test report was sent. No release has been made; this project is experimental.

If GitHub Private Vulnerability Reporting is verified enabled for the intended repository, use its **Report a vulnerability** action. Availability depends on repository configuration; follow [GitHub's private reporting guidance](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately).

If the **Report a vulnerability** action is unavailable, retain sensitive details privately. You may make a public request for a private reporting channel without describing the vulnerability or affected private systems. Do not include exploit instructions, credentials, personal data, or private project content in public issues or pull requests. No security contact address is currently published.

When a verified private route is available, provide the affected version or snapshot, impact, and minimal sanitized reproduction information. Coordinate disclosure with the maintainer privately. There is no promised response or remediation time, bounty, or security guarantee. For flaws in an agent product or another project's dependency, use that vendor's reporting process.

## Supported versions

| Version or state | Support policy |
| --- | --- |
| Current unreleased V1 candidate | Best-effort assessment against the identified candidate snapshot; not a stable supported release. |
| Published releases | None exist; no release branch currently receives fixes. |
| After an authorized 1.0.0 release | Assess reports against the latest stable release; deliver any fixes in a later release. Older releases will not receive backports under this policy. No response-time commitment. |

Before publication, the owner must identify the target repository and verify that the private reporting route is enabled and usable, recording the repository identity, observation, and reviewed candidate. Do not send a test vulnerability report merely to validate configuration. Release remains BLOCKED until this is established. This is resolution of the existing security finding within release review, not an additional workflow approval gate.

## Safe evidence

Share only the minimum sanitized evidence needed through a verified private route. Do not submit raw agent transcripts, tokens, production data, or secrets. Revoke or rotate an exposed credential through its provider; removing it from a document does not invalidate it.
