# mapping.md — astropy__astropy-14508

## Symbol binding (file:line @ base_commit a3f4ae6cd24d5ecdf49f213d77b3513dd509a06c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_formatFloat` / `problem_spec_formatFloat` | `_format_float(value)` | `astropy/io/fits/card.py:1300-1327` |
| `FmtInput.reprStr` | `str(value)` (the value's shortest standard textual form) | `card.py:1302 (post-patch)` |
| `FmtInput.fixedStr` | `f"{value:.16G}"` (fixed-precision form, pre-patch carrier) | `card.py:1302 (pre-patch)` |
| `normE` | `.replace("e", "E")` | `card.py:1302 (post-patch)` |
| `truncate20` (pure helper) | the 20-character limiting block | `card.py:1316-1325` |

The modeled function is `_format_float`, the only behavior the patch changes and
the only behavior the FAIL_TO_PASS test observes
(`test_floating_point_string_representation_card`: `fits.Card("HIERARCH ABC DEF
GH IJKLMN", 0.009125, com)` must render the value as `0.009125`, not
`0.009124999999999999`, so the comment is not truncated; likewise `8.95` and
`-99.9`).

### What the function does

**Pre-patch (base_commit):**
```python
def _format_float(value):
    value_str = f"{value:.16G}"
    if "." not in value_str and "E" not in value_str:
        value_str += ".0"
    elif "E" in value_str:
        significand, exponent = value_str.split("E")
        sign = exponent[0] if exponent[0] in ("+","-") else ""
        exponent = exponent[1:] if sign else exponent
        value_str = f"{significand}E{sign}{int(exponent):02d}"
    str_len = len(value_str)
    if str_len > 20:
        idx = value_str.find("E")
        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]
    return value_str
```

**Post-patch (patch.diff):**
```python
def _format_float(value):
    value_str = str(value).replace("e", "E")
    # Limit the value string to at most 20 characters.
    if (str_len := len(value_str)) > 20:
        idx = value_str.find("E")
        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]
    return value_str
```

The patch REPLACES the initial `value_str` construction: instead of a
fixed-precision `f"{value:.16G}"` (plus exponent-padding normalization and a
`".0"` append), the value is rendered with `str(value)` — Python's shortest
round-tripping repr — and any lower-case `e` exponent marker is upper-cased.
The 20-character limiting block is UNCHANGED except the cosmetic walrus rewrite
of `str_len`. `str(value)` of a float ALWAYS contains a `.` or an `e`/`E`, so the
pre-patch `".0"`-append branch (`"." not in value_str and "E" not in value_str`)
is dead under the new carrier and is correctly dropped.

### Lean modeling

- A float's two textual forms are carried as the grounded inputs `reprStr =
  str(value)` and `fixedStr = f"{value:.16G}"` (both pure functions of the
  value). The model does NOT re-derive float→string formatting (kernel `Float`
  printing is opaque to tactics, DECISIONS.md); it pins the rule's choice of
  *which* form feeds the truncation. This is exactly what the patch changes.
- `normE` upper-cases the exponent marker (`.replace("e","E")`). For a numeric
  repr the only `e` is the exponent marker, so per-character mapping == single
  substring replace.
- `truncate20` transliterates the unchanged 20-char block: `value_str.find("E")`
  → `findIdx? (· = 'E')` (the `-1` sentinel ⇔ `none`); the two slice formulas are
  copied verbatim (`take`/`drop`).
- The post-patch `implementation_formatFloat` consumes `reprStr`; the pre-patch
  `Solution_prepatch.lean` consumes `fixedStr` — the single discriminating
  difference. (The prepatch model folds the entire pre-patch construction —
  `%.16G` + exponent normalization + `.0` append — into the single grounded
  observation `fixedStr`, since for the F2P inputs the result of that whole block
  is the fixed-precision string; the discriminator the spec/test observes is
  "short form vs expanded form", which `reprStr` vs `fixedStr` captures faithfully.)

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a value string (`str`) | `List Char` | per-code-point; Lean indexing total |
| `str(value)` | `reprStr : List Char` | shortest standard textual form |
| `f"{value:.16G}"` | `fixedStr : List Char` | fixed-precision form |
| `value_str.replace("e","E")` | `normE` | per-char `e↦E` map |
| `len(value_str)` | `valueStr.length` | identity |
| `value_str.find("E")` | `findIdx? (· = 'E')` | `-1 ↔ none`, `k ↔ some k` |
| `value_str[:n]` | `valueStr.take n` | identity |
| `value_str[idx:]` | `valueStr.drop idx` | identity |
| `a[:n] + b` | `take n ++ ...` | identity |
| `_format_float`'s return | `result : List Char` | the rendered value string |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The rule is modeled DEEPLY. The two callees that
  produce the textual carriers — `str(value)` and `f"{value:.16G}"` — are not
  axiomatized; they are the grounded inputs (`reprStr`, `fixedStr`). The patch
  CHANGES which carrier is used, so per SPEC_GUIDE §3 it must be modeled deeply,
  not axiomatized. The `axioms` region is empty and **G-AX skips**.
- No flag dependencies: `_format_float` reads no configuration flags.

## G-CONF fuzz seed

Pinned LCG seed: **14508** (see `conformance_check.py` `SEED`). Corpus: random
`(reprStr, fixedStr)` pairs — including the real `str(float)` outputs of randomly
generated floats (small, large, scientific-notation, negative, sub-normal) so the
truncation branches (no-`E`, with-`E`, ≤20, >20) are all exercised — plus
hand-picked edge cases: the F2P values (`0.009125`, `8.95`, `-99.9`), a long
mantissa with an exponent that triggers the significand truncation, and a long
non-scientific string that triggers the `[:20]` branch. The R/I shadow of
`implementation_formatFloat` is diffed against an in-process replica of the
POST-PATCH `_format_float`.
