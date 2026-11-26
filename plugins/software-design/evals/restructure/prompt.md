---
description: Restructure a tangled 6k-line Python project
tags: [structure]
runs: 3
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

I have a Python project (about 6,000 lines) that turns YouTube songs into lead sheets. Files:
- process.py (799 lines): download, stem separation, analysis, transcription, orchestration
- fallback.py: beat grid, MIDI I/O, note cleanup; named "fallback" but the main flow uses it
- tools/keyboard.py: detects chords from instrument MIDI, melody similarity
- tools/leadsheet.py: per-beat chords, sections
- tools/full_score.py (621 lines): melody, lyrics, dedup sections, piano accompaniment, drums, PDF
- tools/lyric_sheet.py: lyric timing alignment plus drawing the chart
- tools/jianpu.py: parses a hand-typed numbered-notation text into a score
- tools/render_pdf.py

Modules import each other with sys.path.insert, and tools/add_lyrics imports process, which imports tools. A pitch-class helper `_pc` is copied in 4 files. Functions pass state through function attributes (melody_score.spans). Models (Demucs, MuScriptor, VocalParse) are swappable through models.toml. The maintainers are one engineer and a musician who edits through Claude.

How should I restructure this? Any naming changes, readability, and should I introduce some architecture or design patterns? No code changes yet, just the design.
