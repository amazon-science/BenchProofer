# mapping.md — sphinx-doc__sphinx-8056

## Symbol binding (file:line @ base_commit e188d56ed1248dead58f3f8018c0e9a3f99193f7)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_normalizeEntries` / `problem_spec_normalizeEntries` | `GoogleDocstring._consume_fields` (inherited by `NumpyDocstring`) | `sphinx/ext/napoleon/docstring.py:269-281` |
| `splitGrouped` flag | `multiple` parameter (patch-added); set by `_parse_parameters_section` | `sphinx/ext/napoleon/docstring.py:269`, `683-695` |
| `raws` input | entries produced by `_consume_field` in the `_consume_fields` loop | `sphinx/ext/napoleon/docstring.py:247-267` (`_consume_field`), `272-280` (loop) |
| `commaPieces` | `str.split(",")` (Python builtin) | applied at `docstring.py:277` post-patch |
| `trim` | `str.strip()` (Python builtin) | applied at `docstring.py:278` post-patch |

The changed function is `_consume_fields`; the call-site change in
`_parse_parameters_section` (passing `multiple=True` under `napoleon_use_param`)
is captured by the `splitGrouped` flag. The two `_parse_parameters_section`
branches both call `_consume_fields`; only the `napoleon_use_param` branch sets
`multiple=True` (and `_format_docutils_params` then renders one `:param:`/`:type:`
pair per split entry). The other call sites (`_parse_other_parameters_section`,
`_parse_keyword_arguments_section`, etc.) keep `multiple=False`, i.e.
`splitGrouped=False`, which is the unchanged behavior.

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Lean type | Python type | bijection |
|---|---|---|
| `List Char` | `str` | per-code-point; `xs.length` ↔ `len(s)` |
| `List (List Char)` | `list[str]` | description lines |
| `FieldEntry = List Char × List Char × List (List Char)` | `Tuple[str, str, List[str]]` | `(name, type, desc)` |
| `List FieldEntry` | `List[Tuple[str,str,List[str]]]` | ordered entry list |
| `Bool` | `bool` | `splitGrouped` ↔ `multiple` (and the `_name`/`_type`/`_desc` truthiness tests ↔ `!= []`) |

`expandEntry`/`commaPieces`/`trim` are pure; `commaPieces` is exactly
delimiter-split on `','` (always yields ≥1 piece, mirroring `str.split(",")`);
`trim` strips exactly Python `str.strip()`'s default removal set — the
`str.isspace()` code points U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0,
U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 — so
`trim` == `str.strip()` on ALL inputs, Unicode whitespace (e.g. NBSP) included.
The G-CONF fuzz corpus draws from an alphabet including these characters.

## Callee provenance + flag deps

- No `opaque` callee declared; no consumed `_prop` axiom. The behavioral delta is
  fully deep-modeled (comma-split + blank-trim), so both are **A-reference** rows
  validated by G-CONF, not consumed axioms (SPEC_GUIDE §3, §0.7).
- **Flag dependency:** the split behavior is active only when `multiple=True`,
  which `_parse_parameters_section` sets only under `self._config.napoleon_use_param`.
  G-CONF fuzzes both `splitGrouped ∈ {False, True}`.

## G-CONF fuzz seed

Pinned seed: **8056** (matches `conformance_check.py` `SEED`). N = 120000 fuzzed
inputs + curated edge cases.
