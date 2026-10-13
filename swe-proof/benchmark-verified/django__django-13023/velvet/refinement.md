# refinement.md — django__django-13023

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`toDecimal` `do` block + the deep `toDecimalResult` / `isRecoverable` models in
the `pure` region) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A** (axiomatized callee —
A-consumed / A-reference), or **I** (identical concrete op). EVERY step is R, A,
or I. There are **no A steps** in this bundle (mapping.md §3): the two real
callees are unchanged and their outputs are modeled as free inputs.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `DecimalField.to_python` (`django/db/models/fields/__init__.py:1504`)

Gold hunk:
```
  try:
      return decimal.Decimal(value)
- except decimal.InvalidOperation:
+ except (decimal.InvalidOperation, TypeError, ValueError):
      raise exceptions.ValidationError(
          self.error_messages['invalid'], code='invalid', params={'value': value})
```

| # | Solution.lean impl op (`toDecimal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `isNone : Bool` guard → `PyResult.retNone` | `if value is None: return value` (lines 1498–1499) | R + I | unchanged null fast path; `isNone` is the free abstraction of the guard (mapping.md §2). `return value` with `value is None` is observationally `retNone`. |
| A2 | `isFloat : Bool` guard → `PyResult.ret floatRes` | `if isinstance(value, float): return self.context.create_decimal_from_float(value)` (lines 1500–1501) | R + I | unchanged float fast path; both the guard and the produced value are free (`isFloat`, `floatRes`). G-CONF runs the real callee on the float leg, so the opaque `floatRes` agrees by construction. |
| A3 | `match conv with \| converted d => PyResult.ret d` | `return decimal.Decimal(value)` succeeds (line 1503) | R + I | the success leg of the interpretation attempt; `conv` is the free outcome of `decimal.Decimal(value)` (mapping.md §2). A produced value is surfaced unchanged. |
| A4 | `\| raised e => if isRecoverable e then PyResult.validationError else PyResult.propagated e` | `except (decimal.InvalidOperation, TypeError, ValueError): raise ValidationError(...)` (lines 1504–1509) | R + I | **the changed op.** `isRecoverable` = membership in the gold patch's `except` tuple: `{invalidOperation, typeError, valueError}` are caught and re-reported as the field's `validationError`; anything else propagates. The exception-classification decision is modeled DEEPLY (no axiom about a callee). The bijection `ExcKind ↔ Python exception type` is mapping.md §2. |

Discriminating content of the change — a `TypeError`/`ValueError` reported by
the interpretation attempt (e.g. a `dict`/`set`/`tuple`/`bytes` input, or an
empty `tuple`/`list`) must yield `PyResult.validationError`, not
`PyResult.propagated`. This lives in `isRecoverable typeError = true` /
`isRecoverable valueError = true` (model) ⇔ the added `TypeError, ValueError`
members of the `except` tuple (real). `Solution_prepatch.lean` reproduces the
pre-patch single-member `except decimal.InvalidOperation` (only
`invalidOperation` normalised) and **fails** the postcondition
`isRecoverable e = true → out = PyResult.validationError` for `e ∈
{typeError, valueError}` (G-DIFF) — exactly the F2P `test_invalid_value` bug.

## B. No additional change sites

The gold patch touches one line in one function; there is no second
independently-fixed behaviour, hence a single `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — which reported
interpretation failures are caught and normalised to the field error — is
modeled **deeply** (`isRecoverable`/`toDecimalResult` in the `pure` region, step
A4), not hidden behind an axiom about a callee. There are **no consumed axioms
and no A-reference deep models** (mapping.md §3): the only library callees
(`create_decimal_from_float`, `decimal.Decimal`) are unchanged and their outputs
are free inputs, owed no contract (directive 7).

## D. verify(Solution) ⇒ resolved

`toDecimal` verifies only if, on the non-null/non-float interpretation-failure
branch, EVERY recoverable failure kind maps to `PyResult.validationError` (A4)
and only a non-recoverable failure propagates. By R (the `ExcKind ↔ exception
type`, `PyResult ↔ outcome`, and free-abstraction bijections of mapping.md §2)
the verified outcome equals the gold-patched `to_python`'s outcome on every
input: the F2P `test_invalid_value` inputs (`(), [], {}, set(), object(),
complex(), 'non-numeric string', b'non-numeric byte-string'`) all raise
`TypeError`/`ValueError` from `decimal.Decimal`, which the broadened `except`
catches → `ValidationError`; the F2P `test_lookup_really_big_value` and the P2P
`test_to_python` numeric/None/float inputs are unaffected (they hit A1/A2/A3).
By G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour through
the real `to_python` on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms, so G-AX is vacuous.
