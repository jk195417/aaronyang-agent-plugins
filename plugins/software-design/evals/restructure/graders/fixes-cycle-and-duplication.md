---
type: llm
---

PASS if the answer (a) removes the import cycle and sys.path hacks by making a proper package with one-way dependencies, (b) gives the duplicated `_pc` helper a single home, and (c) replaces function-attribute state with return values or result objects.
FAIL if any of the three is missing.
