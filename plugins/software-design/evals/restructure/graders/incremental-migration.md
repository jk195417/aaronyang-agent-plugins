---
type: llm
---

PASS if the answer proposes migrating in small steps with behavior unchanged per step, and pins current behavior first (tests, golden or characterization outputs).
FAIL if it proposes a big-bang rewrite or gives no way to check that behavior did not change.
