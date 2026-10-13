# refinement.md — sphinx-doc__sphinx-9230

Operation correspondence between `implementation_paramField` (Solution.lean) and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: the `:param type name:` decomposition

The patched statement is

```python
argtype, argname = fieldarg.rsplit(None, 1)   # was: fieldarg.split(None, 1)
```

wrapped in `try/except ValueError`. It decomposes the field-argument string into
a `(type, name)` pair; on failure the field is left as-is (no type recorded). The
fix changes `split` (first whitespace) to `rsplit` (last whitespace): a type with
interior whitespace such as `dict(str, str)` was being cut at its first space,
so the type was truncated to `dict(str,` and the leftover `str)` leaked into the
name. The last-whitespace split keeps the whole `dict(str, str)` as the type.

| # | `implementation_paramField` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | input `arg : List Char` | `fieldarg : str` | R | Python `str` (per code point) ↔ Lean `List Char` (mapping.md). |
| 2 | `let stripped := dropTrailingSpaces arg` | `rsplit(None, …)` ignoring trailing whitespace | R / A-reference | `str.rsplit` with `sep=None` strips trailing whitespace before splitting. Modeled DEEPLY (not axiomatized); G-AX validates against real `str.rsplit`. |
| 3 | `let nm := (revd.takeWhile (¬isSpace)).reverse` | `argname` — the final whitespace-delimited token | R / A-reference | the last token of the whitespace split = trailing maximal non-space run. Deep model; G-AX-validated. |
| 4 | `let ty := dropTrailingSpaces (revd.dropWhile (¬isSpace)).reverse` | `argtype` — the prefix before the final token | R / A-reference | the remaining prefix with its trailing whitespace removed (interior/leading whitespace preserved). Deep model; G-AX-validated. |
| 5 | `if ty.isEmpty then return none` | `except ValueError: pass` (fewer than 2 tokens → unpack fails) | R | `Option`/`none` ↔ the `ValueError` path (mapping.md). `ty` empty ⟺ `rsplit` yields < 2 parts ⟺ tuple unpack raises. |
| 6 | `return some (ty, nm)` | `argtype, argname = …` (the successful assignment) | I | ordered pair of the two computed pieces — identical concrete operation. The downstream `types.setdefault(...)[argname] = [Text(argtype)]; fieldarg = argname` consumes the pair verbatim (identity on the decomposition). |

No op in `implementation_paramField` is changed-inexpressible: the entire
last-whitespace split is modeled deeply via `extractTypeName`. There is **no
consumed axiom** and **no opaque callee** (the `axioms` region is empty); the
proof discharges by unfolding the impl's `Id.run do` and matching it to
`extractTypeName` (a definitional/structural equality, no induction needed since
both sides share the same `dropTrailingSpaces`/`takeWhile`/`dropWhile` skeleton).

The R/I legs are mechanically refuted by G-CONF (the shadow uses the REAL
`str.rsplit` for the A-reference ops 2–4); the A-reference contract is validated
by G-AX (`extractTypeName` == `str.rsplit(None, 1)`).

## Pre-patch behavior (Solution_prepatch.lean) — the bug

`implementation_paramField` in the prepatch uses the FIRST-whitespace split
(`split(None, 1)`): `dropLeadingSpaces`, then `takeWhile (¬isSpace)` for the
type and the lstripped remainder for the name. On `dict(str, str) opc_meta` it
returns `("dict(str,", "str) opc_meta")` instead of `("dict(str, str)",
"opc_meta")`, so `correct_paramField` is unclosable against the (unchanged) spec
— the discriminating clause is any field argument whose type contains interior
whitespace. This is the actual pre-patch behavior and the source of the
mis-rendering in the issue (G-DIFF).
