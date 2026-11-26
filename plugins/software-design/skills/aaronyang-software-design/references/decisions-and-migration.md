# Decisions and migration

## Architecture decision record (ADR)

- Means here: a short record of one significant decision: context, options considered, decision, trade-offs accepted, and what would make us revisit it.
- Check: could someone a year from now understand why this was chosen, and when to change it?
- Signs: "why is it like this?" has no answer; the same debate repeats.
- Do: write one record per significant decision, in the project's design document or a `docs/decisions/` folder, following the project's existing convention. Keep it to a few lines; link it from the code or docs it affects.

## Strangler fig

- Means here: replace a system piece by piece. The new structure grows around the old one until the old one can be removed, and behavior stays the same at every step.
- Check: can each step be shipped and reverted on its own?
- Signs of the alternative going wrong: a long-lived rewrite branch; "it will work when everything is done".
- Do: keep old entry points delegating to the new code until callers move; remove the old path last.

## Spike

- Means here: a small, throwaway experiment that answers one question before committing to a direction (a new language, library or approach).
- Check: what single question does it answer, and what result decides it?
- Do: compare the spike's output against the current output on the same input; keep the finding, discard the code.

## Test first for refactoring

- Means here: before moving or renaming, pin current behavior with tests (or golden outputs); after the change, the same tests pass unchanged.
- Check: what tells you behavior did not change?
- Do: write characterization tests or save golden outputs first. Where the environment cannot run a part (missing models or hardware), move code without changing logic and have someone with that environment verify.
