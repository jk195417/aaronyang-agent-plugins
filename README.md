# aaronyang-agent-plugins

English | [繁體中文](README.zh-TW.md)

Aaron Yang's agent plugins. One marketplace that both Claude Code and GitHub Copilot can install from.

## Plugins

| Plugin | Skill | What it does |
|---|---|---|
| `writing-rules` | `aaronyang-writing-rules` | Write lean agent instructions that change behavior, decide where each rule belongs, verify rules with evals |
| `plain-explain` | `aaronyang-plain-explain` | Explain ideas to non-specialists: term, plain explanation, everyday analogy, numbered references |
| `gmail-tools` | `aaronyang-gmail-pdf-archive`, `aaronyang-gmail-filters`, `aaronyang-gmail-triage` | Archive statement and receipt PDFs from Gmail by month; manage Gmail filters from a TOML file with lint, backfill and audit; triage the inbox. Personal settings and data stay in a home folder outside the plugin |
| `file-archiving` | `aaronyang-file-archiving` | File personal documents safely: PARA structure, hash-verified moves, append-only evidence, yearly folders, manifests. Your own folder map stays in that folder's AGENTS.md |
| `orchestrating` | `aaronyang-orchestrating` | Shape long agent work: one goal per session, here vs. subagent vs. separate session, a visible detour stack, handoff briefs with provenance, and session close-out |
| `knowledge-notes` | `aaronyang-knowledge-notes` | Ingest knowledge into your own knowledge base by following its existing structure |

Install only what you need; each plugin works on its own. `knowledge-notes` uses `plain-explain` when it is installed and falls back to a built-in format when it is not.

Skill names carry the `aaronyang-` prefix because personal skill folders, claude.ai, and Copilot do not namespace skills, and two skills with the same name can shadow each other.

## Roadmap

Planned plugins are tracked as [issues labeled `roadmap`](https://github.com/jk195417/aaronyang-agent-plugins/issues?q=label%3Aroadmap), starting with an orchestrating plugin.

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

### Other Agent Plugins clients (Codex, Cursor, and others)

Each plugin folder also has a root `plugin.json` that follows [Agent Plugins 1.0](https://agent-plugins.org/specification). Install a plugin folder (`plugins/<plugin>`) the way your client installs Agent Plugins. Skills follow the [Agent Skills](https://agentskills.io/specification) format, so clients that only read skills can use the folders under `plugins/<plugin>/skills/` directly.

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

`plugins/<plugin>/.claude-plugin/plugin.json` is the source of truth. The root `plugin.json` is generated from it, so edit only the Claude Code manifest, then run the sync script. It also checks marketplace descriptions and skill names.

```bash
uv run tools/sync_manifests.py          # regenerate, then check
uv run tools/sync_manifests.py --check  # check only; exits 1 on any problem
uv run tests/test_gmail_filters.py      # offline tests for gmail-tools
claude plugin validate .
for p in plugins/*; do claude plugin validate "$p"; done
```

After merging, refresh each machine yourself; `autoUpdate` has been seen to leave the local marketplace clone on an old commit, so new plugins never install:

```bash
claude plugin marketplace update aaronyang-agent-plugins
claude plugin update <plugin>@aaronyang-agent-plugins    # each changed plugin
claude plugin install <plugin>@aaronyang-agent-plugins   # each new plugin
```

## License

[Apache License 2.0](LICENSE) © Aaron Yang. Use, modify and share freely, including commercially: keep the copyright and license notice, and mark files you change. Versions before this change were released under CC BY-SA 4.0.
