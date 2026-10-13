# refinement.md — astropy__astropy-13453

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `effectiveFormats` `do` block plus the deep `effFormats`/`effFmt`/
`lookupFormat` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the `while` fold
carries a `decreasing i` measure and a verifying impl must TERMINATE and
produce `effFormats formats cols`. (An earlier revision used partial
correctness, which a same-spec diverging impl — `while true` with a trivial
invariant — vacuously satisfied; the G-PANEL-1 audit found that counterexample,
and total semantics excludes the whole class. The real
`_set_col_formats` loop trivially terminates: it is a bounded `for` over
`self.cols`.)

## A. The column-format-selection site — `HTML.write` (`astropy/io/ascii/html.py:342`)

Gold hunk:
```
  self.data.header.cols = cols
+ self.data.cols = cols
  ...
  self.data._set_fill_values(cols)
+ self.data._set_col_formats()
```

The two added lines make the writer run the (pre-existing, unchanged)
`BaseData._set_col_formats` over the table's columns: each column whose name is a
key of the supplied `formats` dict has its display format overwritten; the rest
are unchanged. `effectiveFormats` models the per-column effective-format result
of that selection.

| # | Solution.lean impl op (`effectiveFormats`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `cols : List (String × Option String)`, `formats : List (String × String)` | `cols = list(table.columns.values())` (`html.py:351`) and `self.data.formats` (set by `_get_writer`, `core.py:1727`) | R | column ↔ `(name, info.format)`; dict ↔ `(name, fmt)` association (mapping.md §2). |
| A2 | result is `effFormats formats cols`: per-column `effFmt` = supplied-format-if-present-else-current, computed by the backward `while` fold | `self.data.cols = cols` then `self.data._set_col_formats()` (`html.py:352,358`) running the `for col in self.cols: if name in self.formats: col.info.format = self.formats[name]` loop (`core.py:934-938`) | A-reference + I | the changed behaviour is modeled **deeply**: `effFmt`/`effFormats`/`lookupFormat` (pure region) and the verified loop ARE the selection. No consumed axiom. The fold ops (`lookupFormat`, the override `match`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `_set_col_formats` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A3 | `result` returned (`List (Option String)`, per-column effective format) | the post-call `col.info.format` of each column, consumed downstream by `col.info.iter_str_vals()` (`html.py:433`) to render each `<td>` | R | each column's `info.format` after the in-place mutation ↔ the element of `out`; the renderer reads it to format the cell value (mapping.md §2). The F2P test observes the rendered `<td>` strings, which now reflect the overridden formats. |

Discriminating content of the change — a column whose name appears in `formats`
takes the SUPPLIED format, overriding its current one — lives in
`effFmt m col = match lookupFormat m col.1 with | some f => some f | none => col.2`.
The pre-patch writer never invoked the selection, so every column kept its
current format; `Solution_prepatch.lean` reproduces that (`result := c.2 :: …`)
and **fails** `out = effFormats formats cols` on the override clause
`(c.2 = effFmt formats c)` (G-DIFF).

## B. No consumed axioms

There are no A-consumed axioms in this bundle. The single kind-A construct is the
**A-reference** deep model `effFormats` (== `_set_col_formats`, §A2), G-AX-checked.
No `axiom` is declared, so none can be dead or load-bearing-but-unverified.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation the patch newly exercises — selecting
each column's effective format from the supplied per-column formats — is modeled
**deeply** (the spelled-out element-wise override `effFormats`, step A2, an
A-reference + I), not hidden behind an axiom about a changed function. The value
formatter `iter_str_vals`/`_pformat_col_iter` that consumes the chosen format is
unchanged by the patch and downstream of the modeled effect, so it is outside the
modeled behaviour (the patch changes *which format is selected*, not *how a value
is formatted*); the F2P test's observable difference is fully determined by the
selection (§A3).

## D. verify(Solution) ⇒ resolved

`effectiveFormats` verifies only if its output equals the exact element-wise
override `effFormats formats cols` (A2) — supplied-format-wins, else keep current.
By R (column ↔ `(name, format)`, dict ↔ association) the verified selection
equals the in-place effect of the patched `self.data._set_col_formats()` on the
real columns; by G-AX the deep model `effFormats` equals the real
`_set_col_formats` (A-reference); by G-CONF the R/I transliteration of the fold
agrees with `patch.diff`'s observable behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE). The
single trust point is the A-reference soundness (G-AX) plus refinement fidelity
(this doc, G-EQ + G-CONF).
