# Structure: boundaries, dependencies, data and effects

Each entry: what it means here (the delta from the textbook meaning), the question to ask, signs it is violated, and what to do.

## Cohesion and coupling

- Means here: things that change together live together (high cohesion); a change in one module should not force changes in others (low coupling).
- Check: when one requirement changes, how many files or modules must change?
- Signs: one feature edit touches many folders; a module imports internals of another; a file named for an output (`keyboard.py`) does unrelated jobs.
- Do: regroup by reason to change; expose a small surface and keep the rest private.

## Boundaries by owner and reason to change

- Means here: draw a boundary where the owner or the reason for change differs (a musician owns the style spec, an engineer owns the algorithm). Same idea as Conway's law and SRP, applied to modules, files and documents.
- Check: who decides this, and what event makes it change?
- Signs: one file mixes rules set by different people; a spec section says "this is really about another part".
- Do: give each rule one owner and one home; other parts point to it.

## Dependency direction and no cycles

- Means here: dependencies point one way, toward the stable core (Acyclic Dependencies Principle, Stable Dependencies Principle). This applies to code imports and to document references alike.
- Check: draw the import or reference graph; does every arrow point toward the core, and is it free of cycles?
- Signs: `sys.path` hacks, A imports B imports A, two skills referencing each other's files.
- Do: a cycle means a shared piece has no owner. Extract it into its own module or document, or connect the two sides through data (a file) instead of through each other. Never route around it.

## Single source of truth and derivation

- Means here: every fact has one authoritative place; everything else is derived on demand or generated from it, never copied by hand.
- Check: is this data the source or a copy? Could it be computed from something that already exists?
- Signs: the same constant, table or rule in two files; a cache with no rebuild path; docs restating what code or another doc already says.
- Do: keep the source, derive the rest (generate, compute, or link). When a copy is needed for speed, make it rebuildable and mark it as derived.

## Side effects at the edge (functional core, imperative shell)

- Means here: computation is pure functions over immutable data; reading files, calling models, network and printing happen in a thin outer layer.
- Check: can this function be tested with plain values, without files, network or models?
- Signs: a helper reads config or writes files deep inside; function attributes or globals pass state between calls; results depend on call order.
- Do: pass data in, return data out; collect effects in the shell (CLI, adapters, pipeline runner).

## Declarative vs imperative

- Means here: what people need to read or edit (content, specs, rules, pipeline layout, settings) is declarative data; how something is computed is code. Algorithms stay imperative but pure.
- Check: will a non-engineer read or change this? Is it a description of *what*, or a procedure of *how*?
- Signs: rules buried in `if` chains; the pipeline order hard-coded in a long function; settings as constants in code.
- Do: express it as data (text format, table, TOML, a list of stages with inputs and outputs) and let a small engine interpret it. Do not turn genuine algorithms into a rule language.

## Immutable data

- Means here: once built, a value is not changed; a change produces a new value.
- Check: after creation, does anything mutate this object? Who?
- Signs: functions that both return a value and modify their input; bugs that depend on call order.
- Do: frozen dataclasses or records; transform by returning new values.

## Dependency injection and the composition root

- Means here: a function receives its collaborators as parameters; one place (the CLI entry point) reads config and wires concrete implementations. No DI container.
- Check: does this code find its own dependencies (read config, import a concrete model, use a global)?
- Signs: config reads scattered across modules; tests need real models or the network; a singleton.
- Do: pass dependencies in; build them once at the entry point; in tests, pass fakes.
