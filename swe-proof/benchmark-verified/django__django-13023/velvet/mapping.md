# mapping.md — django__django-13023

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f83b44075dafa429d59e8755aa47e15577cc49f9`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every modeled sub-step. There are **no axioms** and **no
A-reference deep models of library callees** in this bundle (see §3).

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `toDecimal (isNone) (isFloat) (floatRes) (conv)` | `DecimalField.to_python(self, value)` — `django/db/models/fields/__init__.py:1497` (body 1498–1509) | the modeled changed function |
| `isNone : Bool` | `value is None` test — body line 1498 | free abstraction of the null fast-path guard |
| `isFloat : Bool` | `isinstance(value, float)` test — body line 1500 | free abstraction of the float fast-path guard |
| `floatRes : DecimalVal` | `self.context.create_decimal_from_float(value)` — line 1501 | free abstraction of the float fast-path's produced value (unchanged callee) |
| `conv : ConvResult` | the outcome of `decimal.Decimal(value)` — line 1503 (`try` body) | free abstraction of the interpretation attempt's outcome |
| `ExcKind` | the kind of exception the interpretation attempt reports | `invalidOperation`↔`decimal.InvalidOperation`, `typeError`↔`TypeError`, `valueError`↔`ValueError`, `other`↔any other escaping exception |
| `PyResult` | the four observable outcomes of `to_python` | `ret`↔return a `Decimal`; `retNone`↔`return value` (None); `validationError`↔`raise exceptions.ValidationError(...)` (lines 1505–1509); `propagated e`↔an exception of kind `e` escaping uncaught |
| `isRecoverable` | the membership test of the `except (...)` tuple — line 1504 (gold) | which reported failures are caught and re-reported as the field error |
| `toDecimalResult` | the whole `to_python` body | deep model of the observable outcome |

The single line the gold patch changes is the `except` clause at body line 1504:
`except decimal.InvalidOperation:` → `except (decimal.InvalidOperation, TypeError, ValueError):`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `value is None` | `isNone : Bool` | `value is None` ↔ `isNone = true` |
| `isinstance(value, float)` | `isFloat : Bool` | type test ↔ `isFloat = true` |
| `create_decimal_from_float(value)` result | `floatRes : DecimalVal` | the produced `Decimal` ↔ the opaque `DecimalVal` (its content is never inspected; G-CONF compares the rendered `str` of the real value, which the spec leaves free, so the float leg agrees by construction) |
| outcome of `decimal.Decimal(value)` | `conv : ConvResult` | success ↔ `converted d`; `decimal.InvalidOperation`↔`raised invalidOperation`; `TypeError`↔`raised typeError`; `ValueError`↔`raised valueError`; any other exception ↔ `raised other` |
| `return <Decimal>` / `return value(None)` | `PyResult.ret d` / `PyResult.retNone` | observable return |
| `raise exceptions.ValidationError(..., code='invalid')` | `PyResult.validationError` | the field's invalid-value error (the F2P-observed outcome) |
| an exception escaping `to_python` uncaught | `PyResult.propagated e` | the pre-patch bug: a raw `TypeError`/`ValueError` reaching the caller |

`DecimalVal` is an opaque carrier (a single `payload : Int`) because the
operation under specification never inspects a produced decimal — it only
decides whether to surface it or to report a failure. Its concrete content is
modeled as free, exactly as `floatRes`/`conv.converted` are free.

## 3. Callee provenance — why there are NO axioms and NO A-references

The changed operation is an **exception-classification** decision, not a callee
swap. The two real callees the body invokes — `create_decimal_from_float`
(float path) and `decimal.Decimal` (interpretation attempt) — are **unchanged**,
and the spec does not pin any property of their *outputs*: their results are
free inputs (`floatRes`, `conv`) whose every value the postconditions tolerate
(directive 7: a free abstraction is strictly weaker than any real contract, so
it is owed none). The patched behaviour lives entirely in `isRecoverable` /
`toDecimalResult` — pure spec functions, modeled deeply in the `pure` region —
so there is no library callee to axiomatize or to validate as an A-reference.
Consequently `axiom_check.py` is absent and **G-AX auto-skips** (mirrors the
fully-green sibling bundle `django__django-13212`, also axiom-free).

The recoverable family `{InvalidOperation, TypeError, ValueError}` is grounded
in the gold patch's literal `except` tuple and confirmed against the real
`decimal.Decimal` by G-CONF (§4): every input in the F2P matrix that the real
function rejects is observed to produce exactly `validationError`, never an
escaping exception.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13023`** so the
consumer-side verdict is reproducible. The shadow transliterates
`toDecimalResult` to Python: it derives the free observations exactly as the
real code does (`value is None`, `isinstance(value, float)`,
`create_decimal_from_float` for the float leg, and `decimal.Decimal(value)`
with its exception classified into the `ExcKind` family for the interpretation
leg), then applies `isRecoverable`. It diffs the (kind, payload) outcome against
the REAL gold-patched `DecimalField.to_python` over the F2P matrix plus 100 000
fuzzed inputs (ints, floats, numeric/junk strings, bytes, lists, dicts, sets,
tuples, sentinels). Exit 0 iff zero disagreements.
