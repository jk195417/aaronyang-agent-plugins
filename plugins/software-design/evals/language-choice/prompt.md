---
description: Whether to rewrite in a static language, OOP, DI container
tags: [dependencies]
runs: 3
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

I have a 6,000-line Python project that turns YouTube songs into lead sheets. All ML models (Demucs, MuScriptor, VocalParse) are PyTorch; notation uses music21 and Verovio. Models are swappable through models.toml. The code is tangled (sys.path hacks, an import cycle, a helper copied in four files). The maintainers are me (I know C# well) and a musician who edits through Claude.

Is Python the only good choice? Should we rewrite it in a statically typed compiled language like C#, Rust or Go, or in TypeScript? Should we use OOP and a DI container?
