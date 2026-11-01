# aaronyang-agent-plugins

Aaron Yang's agent plugins. One marketplace that both Claude Code and GitHub Copilot can install from.

## Plugins

| Plugin | Skill | What it does |
|---|---|---|
| `writing-rules` | `aaronyang-writing-rules` | Write lean agent instructions that change behavior, decide where each rule belongs, verify rules with evals |
| `plain-explain` | `aaronyang-plain-explain` | Explain ideas to non-specialists: term, plain explanation, everyday analogy, numbered references |
| `knowledge-notes` | `aaronyang-knowledge-notes` | Ingest knowledge into your own knowledge base by following its existing structure |

Install only what you need; each plugin works on its own. `knowledge-notes` uses `plain-explain` when it is installed and falls back to a built-in format when it is not.

Skill names carry the `aaronyang-` prefix because personal skill folders, claude.ai, and Copilot do not namespace skills, and two skills with the same name can shadow each other.

## Install

### Claude Code

```bash
claude plugin marketplace add jk195417/aaronyang-agent-plugins
claude plugin install writing-rules@aaronyang-agent-plugins
claude plugin install plain-explain@aaronyang-agent-plugins
claude plugin install knowledge-notes@aaronyang-agent-plugins
```

### GitHub Copilot CLI

Copilot CLI also reads `.claude-plugin/marketplace.json`.

```bash
copilot plugin marketplace add jk195417/aaronyang-agent-plugins
copilot plugin install writing-rules@aaronyang-agent-plugins
```

### VS Code (Copilot agent plugins, preview)

Add `jk195417/aaronyang-agent-plugins` to `chat.plugins.marketplaces` in `settings.json`, then install from Extensions → Agent Plugins.

### claude.ai

Zip a skill folder under `plugins/<plugin>/skills/` and upload it in claude.ai's skills settings.

## Shared principles

Plugins do not load always-on instructions, so `principles.md` is imported separately. Clone the repo:

```bash
git clone https://github.com/jk195417/aaronyang-agent-plugins ~/code/aaronyang-agent-plugins
```

Then add one line to your `~/.claude/CLAUDE.md`:

```markdown
@~/code/aaronyang-agent-plugins/principles.md
```

Keep personal settings (knowledge-base location, communication habits, folder conventions) in your own file. The shared method lives here, so one edit updates everyone.

## Develop

```bash
claude plugin validate .
for p in plugins/*; do claude plugin validate "$p"; done
```
