# Claude Code Skill discovery observation (C1B)

Dated 2026-11-18. This is an **observation, not a qualification**. It records what one bounded experiment showed; it does not claim that Claude Code is supported, compatible or qualified.

- Agent: Claude Code `2.1.327` (`claude --version`), Linux x86-64, non-interactive `-p` mode, project settings only (`--setting-sources project`), built-in tools disabled (`--tools ""`), `--permission-mode dontAsk`, runtime budget cap `--max-budget-usd 0.12` per call.
- Fixture: a disposable Git repository with two synthetic Skills, each with `name` and `description` frontmatter and a harmless one-line instruction: `probe-alpha-claude` under `.claude/skills/`, and `probe-beta-agents` under `.agents/skills/`.
- Calls: two, `/probe-alpha-claude` and `/probe-beta-agents`. Runtime-reported cost: USD 0.0144 and USD 0.0127. No tool use, no repository writes.

| | `.claude/skills/probe-alpha-claude` | `.agents/skills/probe-beta-agents` |
|---|---|---|
| In the session's reported `skills` list | yes | **no** |
| In the session's reported `slash_commands` list | yes | **no** |
| Command resolved | yes | no |
| Expected marker | appeared | absent |

The decision rests on the lists emitted by Claude Code itself at session start; the marker and the "not installed" reply are model text and only corroborate.

**Not established:** interactive mode, other versions or platforms, whether the full AI-SDLC Lite bundle (nested `framework/` directory) loads identically, auto-invocation by description, and any qualification outcome. Smoke and deep qualification remain NOT RUN.
