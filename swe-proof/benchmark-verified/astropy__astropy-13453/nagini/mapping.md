# mapping.md — astropy__astropy-13453

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 19cc80471739bcb67b7e8099246b391c355023ee`, states the type
abstraction, and gives the provenance of the single deep-model reference
(A-reference) the bundle validates against the real callee.

Repo files in scope: `astropy/io/ascii/html.py` (the changed writer) and
`astropy/io/ascii/core.py` (the unchanged format-resolution loop the patch
wires in).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_column_formats(names, prior_formats, formats)` | the column-format-resolution step the writer must perform before rendering: `HTML.write` (`astropy/io/ascii/html.py:342`) sets `self.data.cols = cols` and calls `self.data._set_col_formats()` (post-patch), driving `BaseData._set_col_formats` (`astropy/io/ascii/core.py:934-938`) | the modeled changed behaviour — resolving each output column's effective format from the supplied per-name mapping |
| `resolved_format(name, prior, formats)` *(deep model — A-reference)* | the per-column body of `BaseData._set_col_formats` (`core.py:936-938`): `if col.info.name in self.formats: col.info.format = self.formats[col.info.name]` | pure spec: the format token one column ends up bound to |
| `formats` (the `Dict[int, int]` argument) | `self.data.formats` (`BaseData.formats`, `core.py:768`, populated from the `formats={}` write kwarg) | the supplied per-name format mapping |
| `names[i]` | `cols[i].info.name` (`col.info.name`) | the i-th output column's name |
| `prior_formats[i]` | `cols[i].info.format` as carried into `_set_col_formats` | the i-th column's pre-existing format spec |
| `Result()[i]` | `cols[i].info.format` after `_set_col_formats` runs | the i-th column's resolved (effective) format spec |

The pre-patch defect (for the refinement audit, not referenced from the
consumer spec view): in `HTML.write` at base_commit only
`self.data.header.cols = cols` is set (`html.py:351`); `self.data.cols` is never
set and `self.data._set_col_formats()` is never called, so the per-name
`formats` mapping never reaches the columns and every column renders with the
format it already carried. `BaseData.str_vals` (`core.py:907-908`, the path the
other writers use) does call `_set_col_formats`, which is why CSV/RST honour
`formats` while HTML does not.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an output column's name (`col.info.name`, a `str`) | `int` identity token (`names[i]`) | distinct names ↔ distinct ints; the resolution only tests name equality / dict membership, never inspects name *content*, so opaque integer identity is faithful (no `str` indexing, which Nagini bans) |
| a format specification (`col.info.format`, a format string or callable, or `None`) | `int` identity token (`prior_formats[i]`, `formats[...]`, `Result()[i]`) | distinct specs ↔ distinct ints; the resolution only decides WHICH spec object each column is bound to (assignment of `col.info.format`), never interprets the spec, so opaque integer identity is faithful. The downstream `iter_str_vals()` then renders with whichever spec the column carries — observed by the F2P test, but the *resolution* step is spec-content-agnostic. |
| the per-name mapping `self.data.formats` (`Dict[str, spec]`) | `Dict[int, int]` | name token ↦ spec token; membership `name in self.formats` ↔ `name in formats`; lookup `self.formats[name]` ↔ `formats[name]` |
| the ordered list of output columns | two index-aligned `List[int]` (`names`, `prior_formats`) | column `i` ↔ `(names[i], prior_formats[i])`; `len(cols)` ↔ `len(names) == len(prior_formats)` |
| the effect "`col.info.format = ...` in place" | a fresh `List[int]` of resolved tokens, index-aligned | modelling the per-column resolution as a pure function of the inputs is observationally equal to the in-place mutation: each column's final `info.format` is exactly the resolved token; ordering and count are preserved (`len(Result()) == len(names)`) |

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolved_format` / the `resolve_column_formats` loop ↔ `BaseData._set_col_formats`

**Callee:** `astropy.io.ascii.core.BaseData._set_col_formats`
(`astropy/io/ascii/core.py:934-938`), unchanged by the patch:

```python
def _set_col_formats(self):
    """WRITE: set column formats."""
    for col in self.cols:
        if col.info.name in self.formats:
            col.info.format = self.formats[col.info.name]
```

The changed *behaviour* (a writer that honours the supplied `formats`) is
modeled **deeply**: `resolved_format` (the pure region) and the verified loop in
`resolve_column_formats` ARE the per-column resolution `format := formats[name] if
name in formats else prior`. There is **no consumed `@ContractOnly` axiom** —
the proof depends on nothing opaque; dictionary membership/lookup over `int`
keys is native Nagini `Dict` semantics.

**Scope of the A-reference equality (guarded, NOT total).** The deep model is a
*total* function: for every name/prior/formats it returns the resolved token.
The real callee is **partial** in its observable effect. `_set_col_formats`
performs the *selection* (`col.info.format = self.formats[name]`) the model
captures exactly, but it writes the chosen spec onto a real `Column` through the
**validating `Column.format` setter** (`astropy/table/column.py:740`). A format
spec that is incompatible with the column's dtype (e.g. an integer format
`"04d"` applied to a float column) is rejected by that setter, so
`_set_col_formats` **raises `ValueError` at the assignment**
(`core.py:938`, `col.info.format = self.formats[name]`) — not later at
`iter_str_vals()` render time. The modeled region is the *resolution decision*
(which spec each column is bound to); the dtype/format compatibility check is
performed by the validating setter, downstream of and outside that decision. The
equality therefore holds **on format/dtype-compatible inputs** (exactly the
domain the F2P/P2P tests exercise — `"04d"` on an int column, `".2e"` on a float
column, unset-format columns left untouched); on dtype-incompatible specs the
model still returns the selected token while the real assignment is rejected.
This is a deliberately documented partiality, not an over-claim of totality.

The deep model is validated against the real callee out-of-band by
`axiom_check.py` (G-AX):

* a dependency-free reimplementation of the `core.py:934-938` loop
  (`reference_set_col_formats`) over opaque tokens, asserted equal to the model
  on 12 boundary cases + 50 000 randomized fuzz inputs; and
* when astropy is importable (the evaluation container), the **genuine**
  `BaseData._set_col_formats` driven on real `astropy.table.Column` objects
  (both int and float columns) with real `info.format` specs, asserting each
  column's resolved `info.format` matches the model over the
  format/dtype-compatible cases; and
* a **positive raise-boundary probe**: a float column with a dtype-incompatible
  spec (`"04d"`) selected by the mapping is driven through the real
  `_set_col_formats`, asserting it **raises** `ValueError` at the assignment (the
  validating `Column.format` setter rejects the incompatible spec) while the
  model returns the selected token — exercising, rather than hiding, the
  partiality boundary (SPEC_GUIDE §0.7).

**Flag/semantics dependencies fuzzed:** name present vs absent; mapping keys
disjoint from / overlapping the column names; supplied spec equal to the prior
spec (idempotent) and overriding it; duplicate column names; empty mapping;
empty column set; "no format" (`None`/empty) prior specs; **dtype-heterogeneous
columns (int and float) with both dtype-compatible and dtype-incompatible
specs**. These are exactly the cases the resolution must get right; the F2P test
`test_write_table_formatted_columns` observes the present-name override
(`"C1": "04d"` on an int column, `"C2": ".2e"` on a float column), and the P2P
fill-value tests observe that absent-name columns are left untouched. The
raise-boundary probe documents that the modeled equality is guarded to
format/dtype-compatible inputs (the tested domain), not total.
