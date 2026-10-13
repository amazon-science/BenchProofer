# refinement.md — django__django-16662

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `orderImportLines` `do` block, the deep `sortImports`/`keyLe` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-AX** / G-EQ.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The import-ordering site — `MigrationWriter.as_string` (`writer.py:178`)

Gold hunk:
```
- sorted_imports = sorted(imports, key=lambda i: i.split()[1])
+ sorted_imports = sorted(
+     imports, key=lambda i: (i.split()[0] == "from", i.split()[1])
+ )
```

| # | Solution.lean impl op (`orderImportLines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `imports : List (List Char)` | `imports` (a `set[str]` of import lines) | R | `set[str]` ↔ `List (List Char)`; each `str` ↔ `List Char` (mapping.md §2). Input order is immaterial (the result is fully determined by the key); the `out ~ imports` postcondition (`List.Perm`) pins membership/multiplicity exactly. |
| A2 | `firstTok` / `moduleTok` (token split) | `i.split()[0]`, `i.split()[1]` | A-reference + I | the whitespace token split is modeled **deeply** (`firstTok`/`afterFirst`/`moduleTok`); the fold ops are **I** (concrete, transliterated by G-CONF), and the equality of the deep model to the real builtin `str.split` is the **A-reference** G-AX validates (mapping.md §3.1). |
| A3 | `isQualified l = (firstTok l == "from".toList)` | `i.split()[0] == "from"` (the first key component) | I | identical concrete predicate: leading token equals the literal word `from`. The discriminating component of the changed key. |
| A4 | `keyLe x y` — group `isQualified=false` ahead of `isQualified=true`, then `lcharLe` on `moduleTok` | the composite key `(i.split()[0]=="from", i.split()[1])` under tuple lexicographic order | I | identical concrete comparison: `False < True` groups whole-module lines first; the second component orders by module token. **This is the CHANGED behavior**, modeled concretely (no axiom); G-CONF differential-tests it against the gold expression. |
| A5 | `imports.mergeSort keyLe` (stable sort) | `sorted(imports, key=…)` (stable sort) | A-reference + I | the stable-sort *primitive* `sorted` is unchanged; `mergeSort` is its stable analogue — the equality `mergeSort keyLe == sorted(key)` is the **A-reference** G-AX validates over tied-key lists (mapping.md §3.2). The application of the comparator is **I**. |
| A6 | `out` returned (`List (List Char)`); `out ~ imports` | `sorted_imports`, later `"\n".join(sorted_imports)` | R | the rendered file joins the ordered lines with `"\n"` (`writer.py:179`, unchanged); the F2P test asserts the exact joined substring `"import datetime\nimport time\nfrom django.db import migrations, models\n"`. The ordering pinned by A4 produces exactly that order; `out ~ imports` (R: `List.Perm`) guarantees no line is dropped/added (directive-5 frame). |

Discriminating content of the change — whole-module (`import …`) lines grouped
BEFORE qualified (`from … import …`) lines — lives in `keyLe`'s flag component
(`isQualified` false sorts first). The pre-patch keyed on the module token only
(`i.split()[1]`), interleaving the two kinds; `Solution_prepatch.lean`
reproduces that (sort by `moduleTok` alone) and **fails** `out = sortImports
imports` (G-DIFF). On the F2P scenario the bug is directly observable:
pre-patch yields `import datetime / from django.db … / import time`, gold yields
`import datetime / import time / from django.db …`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the sort key gaining its grouping component — is modeled **concretely** in
`keyLe`/`isQualified` (steps A3–A4, pure I ops differential-tested by G-CONF),
not hidden behind an axiom. The only A-reference legs (A2 token split, A5 stable
sort primitive) cover **unchanged** standard-library builtins (`str.split`,
`sorted`), each validated against the real callee by G-AX. There are **no
consumed axioms**.

## C. verify(Solution) ⇒ resolved

`orderImportLines` verifies only if its output equals `sortImports imports`
(A4/A5: the stable sort under the composite grouping key) and is a permutation
of the input (A6 frame). By R (`set[str] ↔ List (List Char)`, `"\n".join`
rendering) the verified ordering equals the gold
`sorted(imports, key=lambda i: (i.split()[0]=="from", i.split()[1]))` on the
import lines the writer emits; by G-AX the deep models `firstTok`/`moduleTok`
equal the real `str.split` (A-reference) and `mergeSort keyLe` equals the real
stable `sorted` under the same key (A-reference); by G-CONF the R/I
transliteration of the composite-key logic agrees with `patch.diff`'s behaviour
on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited primitives — and the
gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
