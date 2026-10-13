# refinement.md — django__django-14373

Maps every operation in `implementation_renderYear` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `renderYear` (`DateFormat.Y`)

Post-patch repo code (`patch.diff`):
```python
def Y(self):
    """Year, 4 digits with leading zeros; e.g. '1999'."""
    return '%04d' % self.data.year
```

Lean impl (`implementation_renderYear`):
```lean
def implementation_renderYear (year : Nat) : String := Id.run do
  return padZeros 4 (toString year)
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `year : Nat` | `self.data.year` | **R** | the date's year. A `datetime` year is an `int` in `1..9999`; modeled as `Nat`, a superset preserving the decimal-rendering semantics. mapping.md gives the bijection. |
| 2 | `toString year` | the `%d` (decimal) conversion inside `'%04d' % self.data.year` | **I** | base-ten numeral of the year, no sign (year ≥ 0), no separators. `toString` on a `Nat` is exactly the decimal digit string, identical to Python's `%d` for non-negative ints. |
| 3 | `padZeros 4 (…)` | the `04` field-width-and-zero-flag part of `'%04d'` | **I** (deep model of the rendering) | **the operation the fix introduces.** `%04d` left-pads the decimal numeral with `'0'` to a minimum width of 4, never truncating a longer numeral. `padZeros 4` does exactly this: prepends `4 - len` zero chars (natural subtraction clamps to 0 when len ≥ 4). Modeled deeply (concrete string construction), NOT axiomatized — it is the changed behavior (§3, §0.7). |
| 4 | `return padZeros 4 (toString year)` | the method's return value, as appended by `Formatter.format` via `str(...)` | **I** | the function's observable effect is the rendered year text. `Formatter.format` wraps the return in `str(...)`; post-patch the method already returns a `str`, so that wrapper is the identity. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `Y()` rendering (incl. the `str(...)` wrapper the formatter applies).

## Soundness check (verify ⟹ correct)

- `problem_spec_renderYear year result := result = padZeros 4 (toString year)`
  pins the result EXACTLY (full string equality to an input-grounded expression)
  — directive 5 (frame): the output is fully determined by `year`. No component
  is left unconstrained; no ungrounded oracle (directive 8) — the result must be
  the actually-constructed padded numeral, dischargeable only by performing the
  decimal conversion and the leading-zero padding.
- The prepatch impl (`return toString year`, the bare numeral with no padding)
  reproduces the pre-patch `return self.data.year` whose `str(...)` form omits
  leading zeros. It violates the spec on every year whose numeral is shorter than
  four digits: for `year = 1` it returns `"1"` but the spec requires `"0001"`;
  for `year = 999` it returns `"999"` vs `"0999"`. Its carried gold proof cannot
  close (G-DIFF / G-PANEL); the failing case is any year `< 1000`.
- This discriminating case is precisely what the FAIL_TO_PASS test
  (`test_Y_format_year_before_1000`) exercises: `format(datetime(1,1,1), 'Y')`
  must be `'0001'` and `format(datetime(999,1,1), 'Y')` must be `'0999'`.
  Pre-patch these rendered as `'1'` / `'999'`.
- G-CONF confirms the R/I shadow == the in-process replica of the patched `Y()`
  (`('%04d' %% year)`, then the formatter's `str(...)`) over hand-picked edge
  cases (years 1, 9, 10, 99, 100, 999, 1000, 1999, 9999, and the full datetime
  range) plus ≥1e5 fuzzed years.
