# refinement.md — astropy__astropy-14182

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`surroundWithRuler`, `dataStartOffset`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** / **A-reference**
(axiomatized / deep-modeled callee — none here), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The framing site — `RST.write` (`astropy/io/ascii/rst.py:63`)

Gold hunk:
```
     def write(self, lines):
         lines = super().write(lines)
-        lines = [lines[1]] + lines + [lines[1]]
+        idx = len(self.header.header_rows)
+        lines = [lines[idx]] + lines + [lines[idx]]
         return lines
```

| # | Solution.lean impl op (`surroundWithRuler`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `lines : List (List Char)` | the local `lines` = `super().write(lines)` (the rendered table) | R | `list[str]` ↔ `List (List Char)` (mapping.md §2). The unchanged `super().write` that produces it is an R-refinement: the input already holds the rendering. |
| A2 | param `headerRowCount : Nat` | `idx = len(self.header.header_rows)` | R | `len(list)` ↔ `Nat` (mapping.md §2). The header-row list is abstracted to its length — the only thing `len(...)` reads. |
| A3 | `let ruler := lines[headerRowCount]!` | `lines[idx]` | I + R | positional pick; `lines[k]` ↔ `lines[k]!` under the `require` that the index is in range (mapping.md §2). |
| A4 | `[ruler] ++ lines ++ [ruler]` | `[lines[idx]] + lines + [lines[idx]]` | I | list construction by concatenation; `+` ↔ `++`, `[x]` ↔ `[x]`. |
| A5 | `return out` | `return lines` | I | the framed rendering is returned. |

Discriminating content: the framing line is `lines[headerRowCount]`, **not** the
hard-wired `lines[1]`. The pre-patch used `lines[1]` (correct only when exactly
one header row is requested, `len(header_rows)==1`). `Solution_prepatch.lean`
reproduces `lines[1]!` and **fails** `out = [lines[headerRowCount]!] ++ lines ++
[lines[headerRowCount]!]` (G-DIFF) — the goal `[lines[1]!] ++ … = [lines[headerRowCount]!] ++ …`
is unprovable for general `headerRowCount`.

## B. The data-start site — `RST.read` + removed `SimpleRSTData.start_line = 3`

Gold hunks:
```
 class SimpleRSTData(FixedWidthData):
-    start_line = 3
     end_line = -1
...
+    def read(self, table):
+        self.data.start_line = 2 + len(self.header.header_rows)
+        return super().read(table)
```

| # | Solution.lean impl op (`dataStartOffset`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `headerRowCount : Nat` | `len(self.header.header_rows)` | R | `len(list)` ↔ `Nat` (mapping.md §2). |
| B2 | `let out := 2 + headerRowCount` | `2 + len(self.header.header_rows)` | I | integer addition; `2 + n` ↔ `2 + headerRowCount`. The constant `2` is the two ruler lines bracketing the header block. |
| B3 | `return out` | `self.data.start_line = …; return super().read(table)` | R | the computed index is assigned to `self.data.start_line`, which the unchanged `super().read` consumes (an R-refinement: the index is the observable output; the consuming reader is unchanged). |

Discriminating content: the data start line is `2 + headerRowCount`, **not** the
hard-wired `3`. The pre-patch had `SimpleRSTData.start_line = 3` (a class
attribute; correct only when `len(header_rows)==1`: `2 + 1 == 3`).
`Solution_prepatch_2.lean` reproduces `3` and **fails** `out = 2 + headerRowCount`
(G-DIFF) — the goal `3 = 2 + headerRowCount` is unprovable for general
`headerRowCount`.

## C. The `__init__` plumbing edit — R/plumbing (not separately modeled)

```
-    def __init__(self):
-        super().__init__(delimiter_pad=None, bookend=False)
+    def __init__(self, header_rows=None):
+        super().__init__(delimiter_pad=None, bookend=False, header_rows=header_rows)
```

This threads the new `header_rows` keyword into the **already-existing**
`FixedWidth.__init__` parameter (`fixedwidth.py:345`), which stores it on
`self.header.header_rows` / `self.data.header_rows`. It introduces no new
observable computation: it only makes `len(self.header.header_rows)` — the
quantity both modeled functions key off of via `headerRowCount` — configurable
from the caller. Before the patch, passing `header_rows=` raised
`TypeError: RST.__init__() got an unexpected keyword argument 'header_rows'`
(the issue's traceback). This is an **R/plumbing** step: in the model, the
header-row count is simply an input (`headerRowCount`); the act of supplying it
is the unchanged `FixedWidth.__init__` storing a keyword. No separate prepatch:
the `TypeError` is not an *incorrect computed value* but an *absent parameter*,
and the resulting behaviour (a configurable count) is exercised through sites A
and B with `headerRowCount` ranging over the supported values. G-CONF drives the
real patched `RST` with `header_rows=[...]` of varying length, so the
thread-through is exercised end-to-end.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are **no axiomatized callees** (A-consumed) and **no
deep-model references** (A-reference): both changed operations are closed-form
expressions of integer/list inputs, modeled directly. The unchanged callees
(`super().write`, `super().read`, `FixedWidth.__init__`) supply/consume the
modeled inputs and are R-refinements, not consumed axioms — so no dead axioms.

## E. verify(Solution) ⇒ resolved

`surroundWithRuler` verifies only if its output equals `[lines[headerRowCount]!]
++ lines ++ [lines[headerRowCount]!]` (A3–A4), and `dataStartOffset` verifies
only if its output equals `2 + headerRowCount` (B2). By R (`list[str] ↔ List
(List Char)`, `len ↔ Nat`, `lines[k] ↔ lines[k]!`) the verified framing equals
the patched `RST.write`'s `[lines[idx]] + lines + [lines[idx]]` and the verified
offset equals the patched `RST.read`'s `2 + len(self.header.header_rows)` on
every supported header-row count; by G-CONF the R/I transliterations agree with
`patch.diff`'s behaviour on ≥10⁵ inputs (real renderings + real round-trips).
The two prepatches reproduce the two pre-patch constants (`lines[1]`, `3`) and
each fails its discriminating clause for `headerRowCount ≠ 1` — exactly the
behaviour the F2P test `test_rst_with_header_rows` (3 header rows) observes.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms to trust (G-AX skip).
