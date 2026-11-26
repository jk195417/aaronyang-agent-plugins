# Interfaces and contracts

Each entry: what it means here, the question to ask, signs it is violated, and what to do.

## Domain language (ubiquitous language)

- Means here: names and interfaces use the words of the problem domain and its people, not of a vendor, model or library.
- Check: would a domain expert recognize these names? Would they survive swapping the library?
- Signs: interfaces returning a library's raw types; names like `fallback`, `utils`, `process`; abbreviations only the author reads.
- Do: name by what it does in domain terms; translate vendor terms inside the adapter.

## Interface segregation (ISP)

- Means here: an interface does one job; callers never depend on capabilities they do not use.
- Check: does every caller use every method or field?
- Signs: one `Analyzer` doing beats, key and chords; callers passing dummy arguments.
- Do: split into small interfaces, one per job.

## Dependency inversion (DIP)

- Means here: the side that uses a capability defines its interface; implementations conform to it.
- Check: who owns this interface: the caller or the provider?
- Signs: core code shaped around one vendor's API; changing a model forces changes in the core.
- Do: define the port next to its consumer; adapters depend on it, not the reverse.

## Ports and adapters (hexagonal architecture)

- Means here: the core talks only to ports (interfaces); each external system (model, API, file format, service) sits behind an adapter that translates. Module boundaries are enough; no class hierarchy needed.
- Check: can an external system be replaced by changing only its adapter?
- Signs: vendor calls or vendor data shapes inside the core.
- Do: one adapter per external system, returning domain types.

## Interface design rules

- One job per interface; inputs and outputs are domain types, not file paths or vendor objects.
- One unit per quantity across all interfaces (for example seconds for time), converted in one place.
- Results carry provenance: source, version, confidence.
- Implementation-specific parameters live in configuration, not in the signature.
- "Cannot do it" is a normal result (empty or partial), not an exception that stops the pipeline.
- Open an interface only when a second implementation exists or is committed (see tradeoffs.md, Interface vs concrete).

## Files across a boundary are APIs

- Means here: a file one stage writes and another reads (or another language, tool or person reads) is a public contract.
- Check: if this format changes, who breaks?
- Signs: readers guessing fields; silent breakage after a rename; types defined separately on each side.
- Do: put a schema name and version in the file; keep the schema as the single source and generate types from it; add optional fields freely; bump the version for renames or unit changes.

## Provenance

- Means here: every piece of produced content records who or what produced it, with which version, and how sure it is.
- Check: given a wrong result, can you tell where it came from?
- Signs: mixed human and machine content with no marks; "which model made this?" has no answer.
- Do: attach provenance to results and to stage outputs (a run manifest).

## Contract tests

- Means here: one shared test suite that every implementation of an interface must pass. It checks shape and invariants; accuracy belongs to benchmarks.
- Check: does a new implementation have to pass the same tests as the old ones?
- Signs: each adapter tested differently or not at all; a new adapter breaks the pipeline in production.
- Do: parametrize one suite over all implementations; use fakes so the pipeline runs without real systems.
