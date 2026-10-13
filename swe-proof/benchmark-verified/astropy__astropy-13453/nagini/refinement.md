# refinement.md — astropy__astropy-13453

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_column_formats` impl region + the deep `resolved_format` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fix site — `HTML.write` (`astropy/io/ascii/html.py:342`)

Gold hunk:
```
         self.data.header.cols = cols
+        self.data.cols = cols
 ...
         self.data._set_fill_values(cols)
+        self.data._set_col_formats()
```

The patch makes the HTML writer (a) expose the output columns to `self.data` as
`self.data.cols`, and (b) call the inherited `BaseData._set_col_formats()`
(`core.py:934-938`) — the very step the other writers already perform via
`BaseData.str_vals` (`core.py:907-908`). The net behaviour the test observes is:
each output column's effective format becomes the supplied `formats[name]` when
its name is in the mapping, and is otherwise left unchanged — after which the
already-present rendering path (`col.info.iter_str_vals()`, `html.py:434/440`)
emits values honouring that format.

`model.py`'s `resolve_column_formats` models exactly this resolution.

| # | model.py impl op (`resolve_column_formats`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `names: List[int]`, `prior_formats: List[int]` | the ordered output columns `cols` (each `col.info.name`, `col.info.format`) that `self.data.cols = cols` exposes | R | column ↔ `(names[i], prior_formats[i])` over `int` identity tokens; `len(cols)` ↔ `len(names) == len(prior_formats)` (mapping.md §2). |
| A2 | param `formats: Dict[int, int]` | `self.data.formats` (the per-name `formats={}` write kwarg) | R | `Dict[str, spec]` ↔ `Dict[int, int]`; membership/lookup are name-token-keyed (mapping.md §2). |
| A3 | the loop body `if name in formats: result.append(formats[name]) else: result.append(prior_formats[i])`, i.e. `resolved_format(names[i], prior_formats[i], formats)` per column | `self.data._set_col_formats()` → `for col in self.cols: if col.info.name in self.formats: col.info.format = self.formats[col.info.name]` (`core.py:934-938`) | A-reference | the changed behaviour is modeled **deeply**: `resolved_format` (pure region) and the verified loop ARE the per-column resolution. There is **no consumed axiom** — dict membership/lookup over `int` keys is native Nagini semantics, not opaque. The deep model is validated **equal to the real `_set_col_formats` on format/dtype-compatible inputs** (a *guarded*, not total, equality — see the partiality note below) out-of-band: G-AX (axiom_check.py) runs a faithful reimplementation of `core.py:934-938` (and, in-container, the genuine `BaseData._set_col_formats` on real int and float `Column`s) and asserts equality on the compatible boundary + fuzz, plus a positive probe that the real `_set_col_formats` *raises* at assignment (the validating `Column.format` setter rejects a dtype-incompatible selected spec). |

**Partiality note (A3 — scope of the A-reference equality).** The deep model
is *total*: for every name/prior/formats it returns the resolved token. The real
callee's *selection* step is faithfully captured by the model, but the callee
writes the selected spec onto a real `Column` through the **validating
`Column.format` setter** (`astropy/table/column.py:740`); a spec incompatible
with the column's dtype (e.g. an integer format `"04d"` on a float column) is
rejected by that setter, so `_set_col_formats` **raises `ValueError` at the
assignment** (`core.py:938`) — not later at `iter_str_vals()` render time. The
modeled region is the resolution *decision* (which spec each column is bound to),
which is dtype-agnostic; the format/dtype compatibility check is performed by the
validating setter, downstream of and outside that decision. The A-reference
equality therefore holds **on format/dtype-compatible inputs** — exactly the
domain F2P/P2P exercise (`"04d"` on an int column, `".2e"` on a float column,
untouched columns) — and is *not* claimed to be total. axiom_check.py asserts the
equality on that domain and positively asserts the raise boundary outside it
(SPEC_GUIDE §0.7), so the check covers the boundary rather than hiding it.
| A4 | `Result()` is the per-column resolved-format list, index-aligned, `len(Result()) == len(names)` | the in-place effect on `cols[i].info.format`, columns kept in order | R | modelling the in-place `col.info.format = ...` as a pure function returning the resolved token per column is observationally equal: the i-th column's final `info.format` is `Result()[i]`; order and count are preserved (mapping.md §2). The downstream `iter_str_vals()` renders with whichever spec the column then carries. |

The discriminating content of the change — a column whose name is in the
mapping is bound to the **supplied** spec rather than its prior one — lives in
the `name in formats` branch of `resolved_format` / the loop (model) ⇔ the
`if col.info.name in self.formats: col.info.format = self.formats[...]` step
(real). The pre-patch HTML writer never reaches that step (it sets only
`self.data.header.cols` and never calls `_set_col_formats`), so every column
keeps its prior format; `model_prepatch.py` reproduces exactly that (always
`result.append(prior_formats[i])`) and **fails** the postcondition
`Result()[i] == resolved_format(names[i], prior_formats[i], formats)` /
`Result()[i] == formats[names[i]]` on any column whose name is in the mapping —
which is precisely the spec sensing the change (G-DIFF). This is exactly the
behaviour F2P `test_write_table_formatted_columns` observes (`"C1":"04d"` →
`0001`, `"C2":".2e"` → `1.23e-11`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — wiring the per-name format resolution into the HTML writer — is
modeled **deeply** (the spelled-out per-column resolution `resolved_format`
consumed in `resolve_column_formats`, step A3, an **A-reference**), not hidden behind
an axiom about the function under change. There is **no A-consumed axiom** in
this bundle: the resolution composes only native dict membership/lookup, which
Nagini expresses directly. The single A-reference (`_set_col_formats`) covers
the **unchanged** loop the patch newly invokes, and G-AX validates the deep
model against it.

## C. verify(model) ⇒ resolved

`resolve_column_formats` verifies only if its output is, per column, exactly the
supplied spec when the column's name is present and the prior spec otherwise
(A3, the three postcondition `Forall`s). By R (column ↔ token list,
`self.data.cols = cols` exposing the columns, in-place `info.format` ↔ resolved
token) the verified resolution equals what `self.data._set_col_formats()`
computes on the real columns; by G-AX the deep model `resolved_format` / the
loop equals the real `_set_col_formats` **on format/dtype-compatible inputs**
(A-reference — a *guarded* equality, per the §A3 partiality note: the modeled
*resolution decision* is total and dtype-agnostic, whereas the real callee's
selected spec is rejected at assignment by the validating `Column.format` setter
when incompatible with the column's dtype; axiom_check.py asserts equality on the
compatible domain and positively asserts the raise boundary outside it). The
tested domain
(F2P/P2P) lies entirely within the compatible region, so the resolution the
spec pins is exactly the one the resolved cases observe. The downstream
rendering (`iter_str_vals`, unchanged) then emits each column with the resolved
format. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited (guarded) A-reference — and the
gold patch resolves (G-RESOLVE). The trust point is exactly one of PLAN §1.1: refinement
fidelity (this document, G-EQ), with the A-reference soundness carried by G-AX;
there is no consumed-axiom trust point here.
