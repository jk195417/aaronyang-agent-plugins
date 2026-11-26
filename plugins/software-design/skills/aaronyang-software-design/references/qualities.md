# Quality attributes

Each attribute is judged by a question you can answer by looking at the design.

| Attribute | Means here | Check | Signs of trouble | Do |
| --- | --- | --- | --- | --- |
| Maintainability | The next person (or agent) can find where to change and change it safely | For a typical request, how many places change, and can you find them from the names alone? | Misleading names; duplicated rules; changes needing tribal knowledge | Names that say what the code does; one home per rule; small modules by reason to change |
| Observability | When output is wrong, you can see which step went wrong without rerunning everything | Can you inspect each stage's output and know which version produced it? | Only the final artifact exists; logs without inputs; no record of model or config used | Keep stage outputs as files; write a run manifest (stage, implementation, version, config, duration); give humans a way to see or hear intermediate results |
| Extensibility | Adding a variant (model, source, output) is local | How many files change to add one more implementation? | Adding a model edits the core; `if` chains on type or name | Ports and adapters plus a strategy table; contract tests for the new variant |
| Testability | Core logic runs in tests without real external systems | Can the pipeline run with fakes on a machine without models, network or credentials? | Tests skipped on most machines; logic only tested end to end | Pure core; dependency injection; fixtures of stage outputs |
| Reversibility | A change or decision can be undone cheaply | If this turns out wrong, what does it cost to go back? | One-way migrations; data overwritten in place; big-bang rewrites | Small steps, versioned formats, keep the old path until the new one is proven |
