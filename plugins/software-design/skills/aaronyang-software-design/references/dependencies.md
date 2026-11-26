# Dependencies: build, buy and supply-chain safety

## Build vs reuse

- Means here: reusing a library saves building, but you inherit its maintenance, its dependencies and its risks. Building costs development plus promotion plus long-term maintenance; the last two are usually underestimated.
- Check: how narrow is the need? How much of the library would you use? Who maintains it, and what would replacing it cost?
- Signs of a bad reuse: a heavy framework for one function; an unmaintained package on the critical path. Signs of a bad build: re-implementing a standard (format, protocol, algorithm) that a well-known library already does correctly.
- Do: prefer well-known, maintained libraries for standards and hard problems; write small, narrow pieces yourself; wrap external libraries behind an adapter so replacing them is local.

## Supply-chain safety

- Means here: every dependency, and every dependency it pulls in, runs with your permissions.
- Check:
  - Is the version pinned with a lockfile?
  - Is it maintained (recent releases, responsive issues)?
  - How deep is the dependency tree it brings?
  - Is the source trustworthy (official registry, known publisher, signed or attested where available)?
  - Is the package name exactly right (no typosquat)?
- Signs: unpinned ranges; abandoned packages; installing from arbitrary URLs; many transitive dependencies for a small feature.
- Do: lock versions; keep the dependency list short; review new dependencies before adding them; update deliberately and run tests after; isolate heavy or risky dependencies (optional extras, separate environments).

## Language and framework choice

- Means here: the ecosystem decides more than the language. Libraries, the people who will maintain the code, and the tools agents write well all count.
- Check: where are the libraries this problem needs? Who maintains this code, and what do they know? What goal does the current choice fail to meet?
- Do: stay with the current stack unless a measured bottleneck or a concrete goal requires a change; prove a change with a spike whose output is compared against the current output.
