# mapping.md — django__django-15863

## Symbol binding

| Lean symbol | Python | file:line @ base_commit |
|---|---|---|
| `implementation_coerceDecimal` / `problem_spec_coerceDecimal` / `correct_coerceDecimal` | the coercion of `text` into the working `Decimal d` inside `floatformat(text, arg)` | `django/template/defaultfilters.py:153-159` @ `37c5b8c07be104fd5288cd87f101e48cb7a40298` |
| `floatFallback` (opaque callee) | `Decimal(str(float(text)))` — the binary64 fallback coercion in the `except InvalidOperation` arm | `django/template/defaultfilters.py:156-157` |

The changed line is:
```
-        input_val = repr(text)
+        input_val = str(text)
         d = Decimal(input_val)
```
The modeled function is the whole try/except coercion block (lines 153-159):
build a textual form of `text`, attempt `Decimal(text_form)`; on
`InvalidOperation` fall back to `Decimal(str(float(text)))`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| an exact `decimal.Decimal` value `text` | `text : Rat` | `Decimal(sign, digits, exp)` ↔ the exact rational it denotes; every finite Decimal is an exact rational. The model is restricted to finite (non-NaN, non-infinite) Decimals — the only inputs the F2P precision case and the issue concern. |
| the working `Decimal d` (result of the coercion) | `result : Rat` | same exact-rational denotation |
| `Decimal(str(float(text)))` | `floatFallback text : Rat` | the rational denoted by the Decimal obtained after a binary64 round-trip of `text` (lossy in general) |
| primary read `Decimal(text_form)` succeeds (no `InvalidOperation`) | `primaryReadSucceeds : Bool` | post-patch `text_form = str(text)` is always a valid Decimal literal for a finite Decimal ⇒ `true`; pre-patch `text_form = repr(text) = "Decimal('…')"` is never a valid Decimal literal ⇒ `false` |

## Callee provenance + flag deps

- `str(text)` / `repr(text)` on a `Decimal`: stdlib `decimal.Decimal.__str__`
  emits a plain decimal numeral (e.g. `"123456.123456789012345678901"`), which
  `Decimal(...)` parses back to the identical value; `__repr__` emits
  `"Decimal('123456.123456789012345678901')"`, which `Decimal(...)` rejects with
  `InvalidOperation`. Provenance: CPython `Lib/decimal.py` `__str__`/`__repr__`
  and the `Decimal` constructor grammar. No flag dependency.
- `Decimal(str(float(text)))` (`floatFallback`): goes through Python `float`
  (binary64), so it is only an approximation of an exact Decimal whose
  significand exceeds 53 bits. Modeled as an opaque callee with NO
  value-preservation property (it is exactly the lossy path the bug used).

## G-CONF fuzz seed

`SEED = 15863` (pinned; also in conformance_check.py).
