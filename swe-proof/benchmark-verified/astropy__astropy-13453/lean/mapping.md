# mapping.md — symbol binding & type bijection

Instance: `astropy__astropy-13453`
base_commit: `19cc80471739bcb67b7e8099246b391c355023ee`

## Symbols (file:line @ base_commit)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_formattedCells` | `HTML.write` (the format-honoring cell-rendering path) | astropy/io/ascii/html.py:342 |
| `applyFormat` / the format-override loop | `BaseData._set_col_formats` | astropy/io/ascii/core.py:934 |
| `lookupFormat formats name` | `name in self.formats` / `self.formats[name]` | astropy/io/ascii/core.py:937–938 |
| `renderCell` (opaque) | per-column value rendering `col.info.iter_str_vals()` driven by `col.info.format` | astropy/io/ascii/core.py:910; column info formatting |
| `Column.name` | `col.info.name` | astropy column info |
| `Column.format` | `col.info.format` | astropy column info |
| `Column.values` | the column's stored values | astropy column data |
| `formats : List (String × String)` | `self.data.formats` (the user `formats={}` kwarg) | astropy/io/ascii/core.py:776 |

## Type bijection (used by G-CONF + G-AX)

| Lean | Python | bridge |
|---|---|---|
| `List Column` | `list[astropy.table.Column]` (a `Table`'s columns) | column order preserved |
| `Column.name : String` | `col.info.name : str` | identity |
| `Column.format : Option String` | `col.info.format : str | None` | `none ↔ None`, `some s ↔ s` |
| `Column.values : List CellValue` | column cell values (ints/floats) | per-row order preserved |
| `formats : List (String × String)` | `formats : dict[str, str]` (format-string values) | assoc list ↔ dict; first match wins (names unique in a Table) |
| `renderCell fmt v : String` | the value's `iter_str_vals` rendering under `info.format = fmt` | per-value, deterministic |
| result `List (List String)` | `col_str_iters` (per-column lists of cell strings) | column-major |

Notes:
- The dict→assoc-list bridge assumes unique column names (true for an astropy
  `Table`); `lookupFormat` uses `find?` (first match) consistent with dict
  lookup under uniqueness.
- `formats` values are format **strings** (e.g. `"04d"`, `".2e"`). The
  problem_statement's lambda-callable form is out of scope for the modeled
  string-format path; the F2P test uses string formats (`{"C1": "04d",
  "C2": ".2e"}`), which is what is modeled.

## Callee provenance & flag deps

- `renderCell` ← unchanged value→string formatting (`Column.info.iter_str_vals`
  / pprint format machinery). **Not** modified by the patch. A-reference.
  No flag dependency: rendering depends only on `info.format` and the value.
- `_set_col_formats` is itself part of the modeled (R) logic, NOT axiomatized.

## G-CONF fuzz seed

Pinned seed: `13453`. Inputs fuzzed: column names, presence/absence of a
requested format per column, integer/float values, and format strings drawn
from a small valid set (`"04d"`, `".2e"`, `".3f"`, `"+d"`, `"e"`).
