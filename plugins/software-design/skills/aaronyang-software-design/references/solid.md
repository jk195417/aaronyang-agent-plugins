# SOLID

Use SOLID as a set of checks, not as a reason to add classes. In a function-first codebase most letters apply to modules and interfaces.

| Principle | Check | Signs of violation | Do |
| --- | --- | --- | --- |
| Single responsibility (SRP) | Does this module have one owner and one reason to change? | A file doing six jobs; edits for unrelated requests land in the same file | Split by reason to change (see structure.md, Boundaries) |
| Open/closed (OCP) | Can a new variant be added without editing existing code? | A growing `if model == ...` chain | Add a new adapter and register it in the strategy table |
| Liskov substitution (LSP) | Can any implementation replace another without callers noticing? | Callers check which implementation they got; one adapter returns a different shape | Enforce with contract tests (see interfaces.md) |
| Interface segregation (ISP) | See interfaces.md | | |
| Dependency inversion (DIP) | See interfaces.md | | |
