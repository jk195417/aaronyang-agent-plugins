---
name: aaronyang-writing-rules
description: Write, review, or relocate agent instructions — CLAUDE.md, AGENTS.md, Copilot instructions, memories, skills, hooks — so they stay lean and actually change behavior. Use when adding or editing a rule, auditing an instruction file, or deciding where a piece of guidance belongs.
---

# Writing agent rules

## Principles

- Less is more: keep only what changes behavior (KISS, YAGNI).
- State what to do; positive rules beat a growing list of don'ts.
- Write the principle, not examples or numbers that drift.
- Name known concepts instead of explaining them; state only the delta from the standard meaning. Pair the name with the action, e.g. "optimize only the bottleneck (Theory of Constraints)".
- Disambiguate a term with several meanings; link a term the model may not know (new, niche, internal).
- Pointers, not copies (SSOT): record where knowledge lives and load details on demand.

## Where guidance belongs

| Put it in | Loaded | Holds | Test |
|---|---|---|---|
| Always-on instructions (CLAUDE.md, AGENTS.md, Copilot instructions) | Every session | Short principles and preferences that apply to every task | Needed in every task? |
| Skill | Description always; body on demand | Procedures, formats, domain know-how for one kind of task | Needed only for some tasks, with many steps? |
| Hook | Runs deterministically at a fixed event | Rules that must never be skipped | Would one miss cause harm? |
| Tool / MCP | When called | New capabilities: external systems, actions | Is it a new ability rather than new knowledge? |
| Memory | Index always; entries on demand | Facts learned along the way | Is it a fact rather than an instruction? |
| Knowledge base (Notion, docs) | When looked up | Knowledge written for people | Is it mainly for humans to read? |

Scope follows audience: personal (user level), team (repo level, shared through git), wider (plugin through a marketplace).

When a plugin's content changes, bump its `version` in `plugin.json`: installs are pinned to the version, so an unchanged version never reaches people who already installed it. Once a skill ships in a plugin, remove any local copy of it (single source of truth).

## Process

1. Name the behavior gap: what goes wrong today without the rule? No gap, no rule.
2. Search existing instruction files and memories for overlap; update the existing line instead of adding a new one.
3. Draft the smallest change, one line where possible, and show it to the user before writing.
4. Keep shared method and personal configuration apart: the method goes in shared files, the user's own paths, accounts, and preferences stay in the user's own file.

## Verifying a rule (evals)

Run the same fixed tasks with and without the rule, several times each (ablation), then read the result:

| Result | Meaning | Action |
|---|---|---|
| Passes both with and without | The model already does it; the rule is noise | Delete it |
| Fails even with the rule | The rule does not work | Rewrite it, or move it to a hook |
| Other checks get worse | The rule interferes with others | Catch it with regression tasks |

Tools: `claude plugin eval`, Microsoft Vally, ablate, promptfoo.
