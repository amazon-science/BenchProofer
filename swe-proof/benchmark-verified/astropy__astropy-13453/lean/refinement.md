# refinement.md — `implementation_formattedCells` ↔ `patch.diff`

Modeled function: `HTML.write` (astropy/io/ascii/html.py), restricted to the
behavior the fix touches: producing the per-column string cells while honoring
the user-supplied `formats` mapping.

The gold patch adds two statements to `HTML.write`:

```
+        self.data.cols = cols
...
+        self.data._set_col_formats()
```

`_set_col_formats` (astropy/io/ascii/core.py:934) is:

```python
def _set_col_formats(self):
    for col in self.cols:
        if col.info.name in self.formats:
            col.info.format = self.formats[col.info.name]
```

Then the writer renders each column's values via `col.info.iter_str_vals()`,
which honors `col.info.format`. The bug: pre-patch, the requested `formats`
were never copied onto the columns, so rendering used each column's prior
`info.format` only.

## Operation correspondence

| # | `implementation_formattedCells` op | `patch.diff` / repo counterpart | tag |
|---|---|---|---|
| 1 | `for c in cols do updated.push (applyFormat formats c)` — for each column, override its display format with the requested one when the column name has a requested format | `self.data.cols = cols` then `self.data._set_col_formats()` → `for col in self.cols: if col.info.name in self.formats: col.info.format = self.formats[col.info.name]` | **R** |
| 2 | `lookupFormat formats c.name` — membership test on the column name in the requested mapping, returning the requested format string | `if col.info.name in self.formats: … self.formats[col.info.name]` | **R** |
| 3 | `applyFormat` override `{ c with format := some f }` (override only when requested; else keep `c.format`) | `col.info.format = self.formats[col.info.name]` (else `info.format` unchanged) | **R** |
| 4 | `for c in updated do out.push (c.values.map (renderCell c.format))` — render each value with the column's (now effective) format | the writer's per-column rendering loop, `col.info.iter_str_vals()` driven by `col.info.format` | **A-reference** (`renderCell`) |
| 5 | result is `List (List String)`, one inner list per column, value order preserved, column order preserved | `col_str_iters` list, one entry per column, in column order | **I** (structural) |

- **R legs (1–3, 5):** the format-selection + framing logic — mechanically
  differential-tested by G-CONF against the patched repo's HTML cell output.
- **A-reference (4):** `renderCell` models the unchanged value→string rendering
  primitive (`col.info.iter_str_vals()` / `Column.info.format` formatting). It
  is modeled as an opaque signature; the proof of `correct_formattedCells` does
  NOT consume any property of it (it renders values pointwise, identically in
  spec and impl), so it is an A-reference, not a consumed axiom. G-AX validates
  that the real callee is a deterministic per-value rendering driven solely by
  `info.format` (so the impl's "set format, then render" composition matches the
  repo).

No changed op is left inexpressible; the format-selection logic is modeled
deeply (not axiomatized).
