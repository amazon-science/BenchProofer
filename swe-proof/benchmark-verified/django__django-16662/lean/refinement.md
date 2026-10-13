# refinement.md — django__django-16662

Maps every operation in `implementation_sortImportStatements` to its
`patch.diff` counterpart in `MigrationWriter.as_string`
(`django/db/migrations/writer.py`, the `sorted_imports = sorted(imports, key=…)`
line). Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch ordering)
```python
# First group the "import" statements, then "from ... import ...".
sorted_imports = sorted(
    imports, key=lambda i: (i.split()[0] == "from", i.split()[1])
)
items["imports"] = "\n".join(sorted_imports) + "\n" if imports else ""
```
The modeled value is `sorted_imports`: the collected import-statement strings
reordered by the composite key `(i.split()[0] == "from", i.split()[1])` under
Python tuple (lexicographic) order.

## Operation correspondence
| # | Lean op (`implementation_sortImportStatements`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut sortedStatements := imports` | the `imports` collection passed to `sorted(...)` | I | the accumulator starts as the assembled statement list. |
| 2 | `sortedStatements := sortedStatements.mergeSort importLe` | `sorted(imports, key=lambda i: (i.split()[0] == "from", i.split()[1]))` | R | `sorted(..., key=k)` ↔ `mergeSort` under the order induced by `k`; both are stable. The composite tuple key is refined to `importLe` (False<True on `split()[0]=="from"`, then `≤` on `split()[1]`). `split()[0]`/`split()[1]` ↔ `firstToken`/`moduleName` (`splitOn " "` indexing). Type bijection + composite-key note in mapping.md. |
| 3 | `return sortedStatements` | the `sorted_imports` value joined by `"\n".join(...)` into `items["imports"]` | I | return the ordered statement list (the subsequent `"\n".join` is a presentation step over the same ordering, not part of the modeled decision). |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — `str.split` and `sorted` are both modeled deeply).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow (`importLe` `mergeSort`) against `patch.diff` behavior (the real
`sorted(imports, key=lambda i: (i.split()[0] == "from", i.split()[1]))`) over
≥10⁵ fuzzed inputs, comparing exact list order. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the line is `sorted_imports = sorted(imports, key=lambda i:
i.split()[1])` — the statements are ordered by module name alone, independent of
whether they are plain `import` or `from ... import ...` statements. The prepatch
impl (`implementation_sortImportStatements := … .mergeSort (fun a b =>
decide (moduleName a ≤ moduleName b))`) is exactly this module-name-only sort.
It therefore cannot satisfy `problem_spec_sortImportStatements` on the sortedness
clause (`result.Pairwise importLe`) whenever a plain import has a module name
that sorts after a `from` import's module name — precisely the FAIL_TO_PASS case
`#24155` exercises: `["import datetime", "from django.db import migrations,
models", "import time"]` is left as-is by the module-name sort (so `import time`
follows `from django.db ...`), violating "every plain import precedes every
selective import". The carried gold proof (`mergeSort` over `importLe`) fails to
typecheck against the buggy `mergeSort` over the module-only key (G-DIFF), and
the resulting list is genuinely not `Pairwise importLe`.
