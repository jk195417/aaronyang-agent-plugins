# Trade-offs

Concepts are defined in the other reference files; this file only says how to choose between them. For each decision, state the default, the reason, and what would switch it.

| Tension | Default | Switch when | Concepts |
| --- | --- | --- | --- |
| DRY vs YAGNI | Duplicate until it is the same knowledge, or the third occurrence | A change had to be made twice, or the duplicate is the same rule or fact | restraint-and-patterns.md |
| Pattern vs KISS | Plain functions, immutable data, dicts | A pattern names structure the code already has (Adapter for two implementations, Strategy for a config choice) | restraint-and-patterns.md |
| Interface vs concrete function | Concrete function | A second implementation exists or is committed, or tests need a fake for an external system | interfaces.md |
| Library vs own code | A well-known, maintained library for standards and hard problems | The need is narrow, the library is heavy, unmaintained, or a supply-chain risk | dependencies.md |
| Few deps vs features | Fewer dependencies | The feature is core and the library is well maintained; isolate it behind an adapter | dependencies.md |
| Keep stack vs change language or framework | Keep the current stack | A measured bottleneck or a concrete goal it cannot meet, proven by a spike | dependencies.md, decisions-and-migration.md |
| Declarative vs imperative | Declarative for what people read or edit | The logic is a genuine algorithm; keep it imperative but pure | structure.md |
| Copy vs derive | Derive from the single source | Derivation is too slow; then cache with a rebuild path and mark it derived | structure.md |
| Composition vs inheritance | Composition; interfaces only at adapters | Subtypes truly share behavior and are substitutable | restraint-and-patterns.md, solid.md |
| Big rewrite vs incremental | Incremental (strangler fig), behavior unchanged per step | The old system cannot be run or tested at all | decisions-and-migration.md |
| Static typing strictness | The strictest checker the language offers, in CI | Generated or third-party code; exclude it, do not loosen the rule | qualities.md |
| Observability vs simplicity | Keep stage outputs and a run manifest | The step is trivial and cheap to rerun | qualities.md |

When two principles conflict, go back to the goal and the bottleneck: choose the option that serves the real goal at the bottleneck, and record the choice as an ADR when it is significant.
