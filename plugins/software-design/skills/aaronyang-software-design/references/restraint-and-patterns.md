# Restraint and patterns

Restraint principles decide whether to build something at all; patterns name the shape once you build it.

## KISS

- Means here: the simplest design that meets today's need, readable by the next maintainer (including an agent).
- Check: what is the plainest way to do this with functions, data and dicts?
- Signs: abstractions with one user; a reader must open several files to follow one call.
- Do: start plain; add structure only when a concrete need appears.

## YAGNI

- Means here: do not build for a future case until it exists or is committed.
- Check: is there a second caller, implementation or requirement today?
- Signs: options nobody sets; interfaces with one implementation; "in case we need it" code.
- Do: build for the case at hand; keep the code easy to change instead.

## DRY

- Means here: one piece of *knowledge* (a rule, a fact, a definition) has one home. Code that merely looks alike is not a DRY violation.
- Check: is this the same knowledge, or two things that happen to look alike today?
- Signs: a rule fixed in one place but not its copy; the same table in two files.
- Do: extract shared knowledge at once; leave look-alike code alone until it proves to be the same knowledge.

## Rule of three

- Means here: tolerate duplication twice; extract on the third occurrence, or at once when it is the same knowledge (DRY).
- Check: how many real occurrences are there?

## Patterns worth knowing here

| Pattern | Use when | Not when | Plain form |
| --- | --- | --- | --- |
| Adapter | An external system must be fitted to your interface; two or more implementations | Only one implementation and no external system | A function that calls the vendor and returns domain types |
| Strategy | Behavior is chosen by configuration at run time | The choice never changes | A dict from name to function, picked at the composition root |
| Pipes and Filters | Work is a chain of transformations whose intermediate results are worth keeping or inspecting | A single short computation | A list of stages, each declaring inputs and an output file; a runner that skips up-to-date stages and writes a manifest |
| Result object | A function produces several outputs or diagnostics | One return value suffices | A frozen dataclass returned instead of mutating globals or function attributes |
| Parser and printer (round trip) | Humans edit a text format the program also writes | Read-only input | `parse(text) -> model` and `format(model) -> text`, tested so that `format(parse(x)) == x` |
| Linter-style rules | Many independent checks over one model | One or two checks | A list of rule functions, each with an id, returning issues |

## Usually not needed

| Pattern | Needed only when |
| --- | --- |
| Bridge | Two independent class hierarchies must vary separately. If the two sides already meet through data (an intermediate format), it does not apply |
| DI container | Many services with lifetimes and scopes; a composition root with plain parameters covers small and medium systems |
| Inheritance hierarchy | Subtypes truly share behavior and are substitutable; prefer composition and interfaces |
| Plugin auto-discovery or registries | Third parties add implementations you cannot list; otherwise list them in one dict |
| Event bus | Many producers and consumers that must not know each other; a pipeline of function calls is clearer otherwise |

A pattern earns its place when it names a structure the code already has, so readers recognize it. It does not earn its place by being correct in general.
