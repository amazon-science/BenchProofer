# refinement.md — django__django-15572

Modeled function: `get_template_directories()` → `collectTemplateDirs`.

Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

| # | `implementation_collectTemplateDirs` op | `patch.diff` / source counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut items : List String := []` | `items = set()` | R | a Python set ↔ a `List String` characterized by membership only; accumulation order/duplication is unobservable in the spec (`p ∈ result ↔ …`). |
| 2 | `for dir in dirs do …` | `for dir in backend.engine.dirs` (flattened over the `for backend in engines.all()` loop, DjangoTemplates only) | R | the nested per-backend iteration is flattened into one `dirs : List String`; each iteration contributes via `items.update(…)`. |
| 3 | `if dir ≠ ""` | `... for dir in backend.engine.dirs if dir` | I | the added truthiness guard. For a directory `str`, `if dir` ⇔ `dir != ""` (non-empty). This is the first hunk of the fix. |
| 4 | `items := items ++ [resolveDir dir]` | `items.update(cwd / to_path(dir) for dir in …)` | A-reference | `resolveDir : String → String` models `cwd / to_path(dir)`. It is a universally-quantified parameter (passthrough); the proof consumes NO property of it, so it is an A-reference, not A-consumed. (G-AX skips — no `_prop` axiom.) |
| 5 | `for directory in loaderDirs do …` | `for loader in backend.engine.template_loaders … for directory in loader.get_dirs()` | R | the nested per-backend / per-loader iteration (loaders exposing `get_dirs`) is flattened into one `loaderDirs : List String`. |
| 6 | `if directory ≠ "" ∧ isFrameworkPath directory = false` | `... if directory and not is_django_path(directory)` | I (guard) + A-reference (`isFrameworkPath`) | the added `directory and` is the second hunk of the fix; `not is_django_path(directory)` is the pre-existing exclusion. `isFrameworkPath : String → Bool` models `is_django_path` as a passthrough parameter (A-reference, no consumed property). |
| 7 | `items := items ++ [resolveDir directory]` | `items.update(cwd / to_path(directory) for directory in … if …)` | A-reference | same normalizer as #4. |
| 8 | `return items` | `return items` | I | returns the collected set. |

## Inexpressible ops
None. Every op is R, I, or A-reference. No changed op is axiomatized: the two
fix hunks (the `if dir` / `if directory and …` guards) are modeled DIRECTLY as
`≠ ""` conjuncts (I), exactly the discriminator G-DIFF needs.

## A-consumed axioms
None. Both callees (`resolveDir`, `isFrameworkPath`) are universally-quantified
parameters; the proof quantifies over them and consumes no property. Hence
`axiom_check.py` is a skip stub and G-AX skips.

## Conformance
`conf_skip = false`: the impl region has R/I content (the filtering + iteration
decision). `conformance_check.py` differential-tests the R/I shadow against an
in-process post-patch oracle over an exhaustive small space (lists of length
0..2 over an alphabet including `""` and framework markers) plus ≥1e5 fuzzed
points — 0 disagreements.
