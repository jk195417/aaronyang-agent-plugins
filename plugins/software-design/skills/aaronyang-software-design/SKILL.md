---
name: aaronyang-software-design
description: Design or review a system, module, interface or tech decision — structure, naming, file layout, patterns, dependencies, language or library choice — and weigh the trade-offs explicitly. Use when the user asks how to structure, split or refactor code, whether to adopt a pattern, framework, language or dependency, how to design an interface or data format, or to review an architecture or design proposal.
license: Apache-2.0
---

# Software design

The always-on working principles (first principles, single source of truth, declarative, minimal side effects, established practice first) apply throughout. This skill is the procedure for design decisions. Each step names the concepts it uses and the reference file that defines them as checks. Read a reference file when its step applies to the decision at hand.

## Process

1. **Goal and bottleneck.** What must the system do, for whom, and what limits it now? A different split of the problem often makes the question unnecessary.
2. **Boundaries.** Group what changes together and has one owner. Make dependencies point one way, toward the core. Treat a cycle in imports or document references as a missing owner, and extract that piece. Read [references/structure.md](references/structure.md).
3. **Data and effects.** Find the single source of each fact and derive the rest. Make what people edit declarative data, computation pure functions, and side effects a thin shell. Wire dependencies at one composition root. Read [references/structure.md](references/structure.md).
4. **Interfaces and contracts.** Use domain language, one job per interface, and domain types in and out. Results carry provenance. Files that cross a boundary are versioned APIs. Every implementation passes one contract test suite. Read [references/interfaces.md](references/interfaces.md) and, for SOLID checks, [references/solid.md](references/solid.md).
5. **Restraint and patterns.** Ask what the plainest working design is (KISS), whether a second case exists today (YAGNI), and whether this is the same knowledge (DRY). Name a pattern only when the code already has its shape. Read [references/restraint-and-patterns.md](references/restraint-and-patterns.md).
6. **Dependencies and stack.** Decide between reusing and building, check supply-chain risk, and keep the language and framework unless a measured need says otherwise. Any stack change, even a partial one, is first proven by a spike whose output is compared against the current output. Read [references/dependencies.md](references/dependencies.md).
7. **Qualities.** Check maintainability, observability, extensibility, testability and reversibility by their questions. Read [references/qualities.md](references/qualities.md).
8. **Trade-offs.** For each decision, take the default from [references/tradeoffs.md](references/tradeoffs.md) unless a switch condition holds.
9. **Migration.** Change incrementally (strangler fig), pin behavior with tests first, and use a spike for uncertain directions. Record significant decisions as ADRs. Read [references/decisions-and-migration.md](references/decisions-and-migration.md).

Skip steps that do not apply; a naming question needs steps 1, 2 and 4, not all nine.

## Output

Lead with one table, one row per decision: recommendation, key reason, alternative rejected, and what would change it. Then expand only where the reader needs more. At the end, list once the claims that are inferred or unverified; do not label every line.

Show the target structure as a tree or table before changing code, and change code only after the user agrees.
