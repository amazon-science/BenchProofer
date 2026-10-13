# refinement.md — django__django-11206

Maps every operation in `implementation_formatNumber` to its `patch.diff`
counterpart in `django/utils/numberformat.py:format`. Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real repo
callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (gold, verbatim)
```python
     # sign
     sign = ''
     if isinstance(number, Decimal):
+
+        if decimal_pos is not None:
+            # If the provided number is too small to affect any of the visible
+            # decimal places, consider it equal to '0'.
+            cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
+            if abs(number) < cutoff:
+                number = Decimal('0')
+
         # Format values with more than 200 digits ...
         _, digits, exponent = number.as_tuple()
         ...
```

The fix inserts a guard at the top of the `isinstance(number, Decimal)` branch
that, when `decimal_pos is not None`, replaces `number` with `Decimal('0')` if
its magnitude is below the smallest visible unit. Everything after the guard (the
scientific-notation cutoff, `'{:f}'` rendering, truncation/padding, sign,
grouping) is UNCHANGED and re-uses the (possibly zeroed) `number`.

## Modeling decision
- `number` is a `Decimal` = an exact rational → `ℚ` (the fix is an order/zero-only
  comparison `abs(number) < cutoff`; DECISIONS.md mandates exact `Rat`, never
  kernel `Float`, for order-only fixes).
- The inserted guard is modeled DEEPLY and concretely as `snapValue`/`cutoffOf`
  (R/I content), since it is exactly the changed behavior.
- `cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))`:
  - `decimal_pos = 0` → `'0.' + '1'` = `Decimal('0.1')`
  - `decimal_pos = d ≥ 1` → `'0.' + '1'.rjust(d,'0')` = `Decimal('0.0…01')` (d-1
    zeros) = `10^(-d)`.
  So `cutoff(d) = 10^(-max(d,1))`, modeled as `cutoffOf d = 1 / 10 ^ (max d 1)`.
- The unchanged rendering tail (from `_, digits, exponent = number.as_tuple()`
  onward) is `renderDecimal`, declared `opaque`. The fix does NOT touch it; the
  spec composes it with the snapped argument, and the impl computes precisely
  `renderDecimal (snapValue number decimalPos) …`. The proof consumes no property
  of `renderDecimal` (both sides of `problem_spec` apply the same `renderDecimal`
  to the same snapped argument), so it is an A-reference, not a consumed axiom.

## Operation correspondence
| # | Lean op (`implementation_formatNumber`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut n := number` | (the local `number` carried into the branch) | I | the value about to be rendered. |
| 2 | `match decimalPos with \| some d => … \| none => pure ()` | `if decimal_pos is not None:` | R | the guard fires only when a fixed precision is requested; `decimalPos : Option Nat` ↔ `decimal_pos` (`None`/non-negative int). |
| 3 | `let cutoff := cutoffOf d` | `cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))` | R | `cutoffOf d = 1/10^(max d 1)` = the exact rational value of the constructed `Decimal` (verified for `d=0` and `d≥1` above). |
| 4 | `if \|n\| < cutoff then n := 0` | `if abs(number) < cutoff: number = Decimal('0')` | R | magnitude comparison on exact rationals; `\| · \|` ↔ `abs`, `0 : ℚ` ↔ `Decimal('0')`, strict `<` ↔ Python `<`. |
| 5 | `return renderDecimal n decimalSep decimalPos grouping thousandSep forceGrouping useL10n` | the entire unchanged rendering tail of `format`, applied to the (possibly zeroed) `number` | A-reference | the standard value-to-string procedure (sci-notation cutoff, `'{:f}'`, truncation/padding, sign, grouping); unchanged by the fix, left opaque, bound to the REAL base-commit tail in G-CONF. |

The behavior-changing op is #2–#4 (the snap). The prepatch impl omits it
entirely (op 5 applied to the raw `number`), so on the F2P inputs (`1e-200`,
`9e-19`, `.00000000000099`, the 300-digit `0.0…01234`) it renders the value on
its own (scientific notation / non-zero digits) while the spec forces the
zero-rendering — exactly the FAIL_TO_PASS discrimination.

## R/I legs ⇒ G-CONF
Ops 1–4 (the snap: precision-gated magnitude-to-zero) are the R/I content;
`renderDecimal` (op 5) is the A-reference. G-CONF leaves `renderDecimal` bound to
the REAL base-commit rendering tail and differential-tests the shadow
`renderDecimal(snapValue(number, decimal_pos), …)` against the REAL patched
`format` over ≥10^5 fuzzed inputs. `conf_skip = false`: the impl region has
genuine R/I content (the snap is the fixed behavior).

## No A-consumed row
The proof consumes no property of `renderDecimal` (`problem_spec` and the impl
apply the SAME `renderDecimal` to the SAME snapped argument; correctness is the
structural identity of that argument). So `meta.json axioms = []`; `renderDecimal`
is recorded as an A-reference (deep_model_references) solely to document the
G-CONF binding. `axiom_check.py` is a skip stub.

## F2P alignment
- `test_decimal_numbers`: the changed fixture `('0.{}1234'.format('0'*299), 3,
  '0.000')` — `Decimal('0.0…01234')` (magnitude ~`1.234e-300`) with `decimal_pos=3`
  has magnitude below `cutoff(3)=1e-3`, so the spec forces the zero-rendering
  `'0.000'`; the prepatch renders `'1.234e-300'`. The unchanged fixtures
  (`1e-7`/`1e-8`/`1e-9`/`1e-10`/`1e-11` at 8 places, the `1e300` case, etc.) are
  reproduced because the snap fires iff below `cutoff` and is identity otherwise.
- `test_decimal_subclass`: `EuroDecimal('1.23')` with `nformat(price, ',')` —
  `decimal_pos is None`, so the snap never fires (`snapValue` is identity on the
  `none` branch) and the rendering is unchanged. This F2P passes because the
  added guard does not perturb the no-`decimal_pos` path; it is swept into
  FAIL_TO_PASS by the shared test module (the test asserts the `Decimal` subclass
  `__format__` still works through the unchanged tail).
`patch.diff` (gold verbatim) makes the harness resolve.
