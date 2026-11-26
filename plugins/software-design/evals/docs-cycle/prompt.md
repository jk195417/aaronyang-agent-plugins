---
description: Review two skills that reference each other's documents
tags: [structure]
runs: 3
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

A plugin has two skills: score-to-sheet (typesets a numbered-notation text into a PDF following a style spec written by a musician) and music-to-sheet (turns a recording into a numbered-notation draft). The style spec file STYLE.md has layout rules plus a section "how to read chords from a recording". The plan has music-to-sheet's SKILL.md reference STYLE.md inside score-to-sheet's folder, and score-to-sheet's SKILL.md reference music-to-sheet's model notes.

Review this skill and document structure. Is anything wrong, and what should change?
