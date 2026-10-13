# mapping.md — django__django-11206

## Instance
- repo: django/django
- base_commit: 571ab44e8a8936014c22e7eebe4948d9611fd7ce
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`django/utils/numberformat.py` defines `format(number, decimal_sep,
decimal_pos=None, grouping=0, thousand_sep='', force_grouping=False,
use_l10n=None)` (line 7 @ base_commit). When `number` is a `Decimal`, the
function decides between scientific notation and fixed-point `'{:f}'` rendering
based on a hardcoded 200-digit cutoff on `abs(exponent) + len(digits)` (lines
29-43). For a `Decimal` of very small magnitude (e.g. `Decimal('1e-200')`) the
digit/exponent count exceeds 200, so the value is rendered in scientific
notation even though a `decimal_pos` was supplied and the value is far smaller
than the smallest representable unit at that precision — yielding e.g.
`'1.00e-200'` instead of `'0.00'`.

The gold patch inserts, at the top of the `isinstance(number, Decimal)` branch
(after `numberformat.py:29`), a guard that runs only when `decimal_pos is not
None`:

```python
+        if decimal_pos is not None:
+            # If the provided number is too small to affect any of the visible
+            # decimal places, consider it equal to '0'.
+            cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
+            if abs(number) < cutoff:
+                number = Decimal('0')
```

`cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))` is the smallest magnitude
that still affects a visible decimal place:
- `decimal_pos = 0` → `Decimal('0.1')`
- `decimal_pos = 1` → `Decimal('0.1')`
- `decimal_pos = d ≥ 1` → `Decimal('1e-d')` = `10^(-d)`

i.e. `cutoff(d) = 10^(-max(d, 1))`. When `abs(number) < cutoff`, `number` is
replaced by `Decimal('0')` *before* the unchanged rendering tail runs, so the
unchanged tail formats `0` and produces the all-zeros string (`'0.00…0'` or
`'0'`). The rest of `format` — scientific-notation cutoff, `'{:f}'` rendering,
decimal truncation/padding, sign handling, grouping — is UNCHANGED.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_formatNumber` | `django/utils/numberformat.py:format`, restricted to the `isinstance(number, Decimal)` input path (the only path the fix touches) — i.e. the `Decimal`-input behavior of `format` |
| `problem_spec_formatNumber` | the post-condition that `Decimal`-input behavior must satisfy |
| `snapValue` (pure helper) | the inserted guard: `number = Decimal('0')` when `decimal_pos is not None and abs(number) < cutoff`, else `number` unchanged |
| `cutoffOf` (pure helper) | `Decimal('0.' + '1'.rjust(decimal_pos, '0'))` as an exact rational |
| `renderDecimal` (opaque A-reference) | the UNCHANGED rendering tail of `format` for a `Decimal` value: everything from `_, digits, exponent = number.as_tuple()` (numberformat.py:32) onward — the pre-existing decimal-to-string algorithm. Not changed by the fix; left opaque (the proof consumes no property of it) and bound to the real base-commit algorithm in G-CONF. |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `number : ℚ` | the `Decimal` value `number` | every `Decimal` is an exact rational; the fix compares magnitudes (`abs(number) < cutoff`) and tests equality-to-zero, an order/zero-only operation → exact `ℚ` (DECISIONS.md: float order-only fix → exact `Rat`, never kernel `Float`) |
| `decimalSep : String` | `decimal_sep` | pass-through to the rendering tail |
| `decimalPos : Option Nat` | `decimal_pos` (`None`, or a non-negative count) | `none ↔ None`; `some d ↔ d` |
| `grouping : Int` | `grouping` (single value; default `0`) | the non-uniform-sequence form of `grouping` is unchanged and outside the fix's path; modeled as the common single-`int` case |
| `thousandSep : String` | `thousand_sep` | pass-through |
| `forceGrouping : Bool` | `force_grouping` | pass-through |
| `useL10n : Option Bool` | `use_l10n` (`None`/`True`/`False`) | `none ↔ None`, `some true ↔ True`, `some false ↔ False` |
| result `: String` | the returned string | the rendered representation |

`number : ℚ` ↔ Python `Decimal` is the exact value bijection (G-CONF builds the
`ℚ` from the same decimal string fed to the real `Decimal`).

## Callee provenance / flag deps
- `renderDecimal` is the only modeled callee. It is the UNCHANGED rendering tail
  of `format`, declared `opaque` so it can appear in the executable impl. The
  proof consumes NO property of it (the spec states `result = renderDecimal
  (snapValue number decimalPos) …` and the impl computes exactly that, so
  correctness is the structural identity of the snapped argument — no contract on
  `renderDecimal` is needed). Hence there is no `axiom renderDecimal_prop` and
  `axiom_check.py` is a skip stub. `renderDecimal` is recorded as an A-reference:
  in G-CONF it is bound to the REAL base-commit rendering algorithm (the
  unchanged tail), so the differential test validates that the modeled snap,
  composed with the real renderer, reproduces the real patched `format`.
- No flag-dependent callee. The snap fires solely on `decimal_pos is not None`
  and the magnitude comparison; both are modeled concretely.

## G-CONF fuzz seed
- pinned seed: `11206`
- ≥10^5 fuzzed `(decimal_string, decimal_pos, grouping, thousand_sep,
  force_grouping, use_l10n)` tuples, drawn to exercise: tiny magnitudes straddling
  the cutoff (`10^(-d)` ± ε, including the exact boundary), `decimal_pos ∈ {None,
  0, 1, 2, 8, large}`, negative values, zero, ordinary mid-range decimals, very
  large magnitudes (scientific-notation path, snap never fires), and the F2P
  fixtures (`1e-200`, `1e-199`, `9e-19`, `.00000000000099`, the 300-digit cases).
  Oracle = the REAL patched `format`; shadow = `renderDecimal(snapValue(n))` with
  `renderDecimal` bound to the real base-commit rendering tail.
