# mapping.md — astropy__astropy-13453

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 19cc80471739bcb67b7e8099246b391c355023ee`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-model reference.

Repo file under change: `astropy/io/ascii/html.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effectiveFormats (cols) (formats)` | the column-format-selection step the HTML writer was MISSING: `HTML.write` (`astropy/io/ascii/html.py:342`) now wires `self.data.cols = cols` + `self.data._set_col_formats()` (gold hunk, lines 352/358) | the modeled changed behaviour: produce each column's effective display format |
| `effFmt (m) (col)` | the per-column body of `BaseData._set_col_formats` — `if col.info.name in self.formats: col.info.format = self.formats[col.info.name]` (`astropy/io/ascii/core.py:934-938`) | pure spec: one column's effective format (override-or-keep) |
| `effFormats (m) (cols)` *(deep model — A-reference)* | `BaseData._set_col_formats` over all `self.cols` (`astropy/io/ascii/core.py:934-938`) | pure spec: effective formats of all columns; deep model of the unchanged callee `_set_col_formats`, validated `effFormats == _set_col_formats` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `lookupFormat (m) (nm)` | the `col.info.name in self.formats` / `self.formats[name]` dict probe (`core.py:937-938`) | pure spec: look the supplied format up by column name |

`self.data.formats` is the user's `formats={...}` keyword: `_get_writer`
(`core.py:1726-1727`) executes `writer.data.formats = kwargs['formats']` before
`write` runs. The HTML writer omitted both `self.data.cols = cols` and
`self.data._set_col_formats()`, so the supplied formats were never applied — the
bug. The fix adds exactly those two lines (`html.py:352,358`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a table column `col` (only `col.info.name`, `col.info.format` are touched) | `String × Option String` | `(col.info.name, col.info.format)`; an unset format (`None`) ↔ `none`; a set format string ↔ `some s` |
| the column sequence `cols = list(table.columns.values())` (`html.py:351`) | `List (String × Option String)` | element-wise, order-preserving; `len(cols)` ↔ `cols.length` |
| the supplied `formats` dict (`self.data.formats : dict[str,str]`) | `List (String × String)` | `d` ↔ its `(name, fmt)` association; keys unique, so `name in d` / `d[name]` ↔ `lookupFormat`; absence ↔ `none` |
| the EFFECT of `_set_col_formats`: each `col.info.format` after the call | `List (Option String)` (the `out` of `effectiveFormats`) | the post-call value of `col.info.format`, per column, in order |

Only the `name` and `format` fields of a column are observable by this change;
every other column attribute (data, dtype, unit, …) is untouched by
`_set_col_formats` and by the gold hunk, so the structure-with-touched-fields
modeling (SPEC_GUIDE §2) is exact. Lean `List` indexing is total and sound.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `effFormats` deep model ↔ `_set_col_formats` (A-reference)
**Callee:** `astropy.io.ascii.core.BaseData._set_col_formats` (unchanged by the
patch — it already existed; the bug was that the HTML writer never *called* it).
Source at base_commit (`core.py:934-938`):

```python
def _set_col_formats(self):
    """WRITE: set column formats."""
    for col in self.cols:
        if col.info.name in self.formats:
            col.info.format = self.formats[col.info.name]
```

This mutates each column in place: a column whose name is a key of `self.formats`
gets its `info.format` OVERWRITTEN by the supplied format string; every other
column keeps its current `info.format`. That is exactly the element-wise
`effFmt`/`effFormats` of the pure region (override-or-keep), so the deep model is
an A-reference, NOT a consumed axiom. The changed behaviour (the HTML writer now
applying user formats) is the *observable effect* of running this selection over
the table's columns.

**Soundness check (G-AX):** `axiom_check.py` constructs real astropy columns
with assorted pre-existing `info.format` values, real supplied `formats` dicts
(overlapping and disjoint key sets, boundary and fuzz), runs the REAL
`_set_col_formats`, and asserts the resulting per-column `info.format` equals
`effFormats` over the same inputs. Imports only `astropy` (the module the gold
patch calls). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13453`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `lookupFormat`/`effFmt`/`effFormats` (R/I-tagged ops) to Python
over the real `dict`/`Column` types and compares against `patch.diff`'s
behaviour — the patched `_set_col_formats` selection run over real columns.
There are no A-tagged callees inside the computed `out`, so the shadow is pure
R/I.
