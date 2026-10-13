# mapping.md — django__django-15863

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 37c5b8c07be104fd5288cd87f101e48cb7a40298`, states the type
abstraction, and gives the provenance of the kind-A obligation (a deep-model
A-reference, validated by `axiom_check.py` / G-AX; there is no consumed axiom).

Repo file under change: `django/template/defaultfilters.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reconstruct_digits(text)` | the value-reconstruction step of `floatformat(text, arg)` — `django/template/defaultfilters.py:96` (the changed statements at lines 153-160) | the modeled changed behaviour: turn the input value into the exact-precision value `d` the rest of `floatformat` formats |
| `narrowed_to_significand(s)` / `narrowed_from(s, b)` *(deep model — A-reference)* | the lossy reconstruction `Decimal(str(float(text)))` reached when the input is NOT a decimal literal (`django/template/defaultfilters.py:158`); validated `==` the real binary round trip by axiom_check.py (G-AX), NOT consumed as an axiom | pure spec: the digit sequence a binary-significand reconstruction can retain |
| `significand_budget()` | the round-trip significant-digit capacity of CPython's `float` (IEEE-754 binary64) | pure spec constant (= 17) |

The single gold change at `defaultfilters.py:154`:

```
-        input_val = repr(text)
+        input_val = str(text)
```

with the surrounding control flow (`d = Decimal(input_val)` inside the `try`,
`except InvalidOperation: d = Decimal(str(float(text)))`) unchanged. The repo
symbol the change concerns is the local `input_val` / `d` reconstruction inside
`floatformat`; the model abstracts that reconstruction as `reconstruct_digits`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `Decimal` (or numeric) input `text`, and the reconstructed value `d` | `List[int]` of its exact significant decimal digits (`Decimal.as_tuple().digits`, each in 0..9) | `d.as_tuple().digits[k]` ↔ `text[k]`; `len(digits)` ↔ `len(text)`; equality of values with identical sign/exponent ↔ equality of the digit lists. Sign and exponent are positional metadata the bug does not touch and are omitted from the carrier. |
| a value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror sequence concat/prefix/suffix/length/index |
| `str(text)` → `Decimal(...)` (the fix path) | the IDENTITY on the digit list (`reconstruct_digits` returns `text` unchanged) | `str(Decimal)` is the canonical decimal string; `Decimal(canonical_string)` reproduces the value exactly, so the digit sequence is preserved element-for-element (axiom_check.py A-reference 1). |
| `repr(text)` → `Decimal(...)` raises → `Decimal(str(float(text)))` (the bug path) | `narrowed_to_significand` on the digit list | `repr(Decimal)` is `"Decimal('…')"`, not a decimal literal, so `Decimal(repr(text))` raises `InvalidOperation`; the fallback routes the value through `float`, whose binary significand retains at most `significand_budget()` significant digits (axiom_check.py A-reference 2). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: the changed operation is the
reconstruction itself, which is modeled DEEPLY (the verified identity loop in
`reconstruct_digits`, with the lossy alternative spelled out in
`narrowed_to_significand`). The kind-A obligation is therefore an **A-reference**
— the deep models validated `==` the real standard-library callees the patched
code uses.

### 3.1 Exact reconstruction (`reconstruct_digits` identity) ↔ `Decimal(str(value))` (A-reference)
**Callees:** CPython `str(Decimal)` and `decimal.Decimal(str)`. `str(Decimal)`
emits the canonical decimal character form of the value (no rounding); parsing
that string with `Decimal(...)` reproduces the value exactly. Hence the
significant-digit sequence is preserved at full length, which the model encodes
as the identity `ToSeq(Result()) == ToSeq(text)`. Docs:
https://docs.python.org/3/library/decimal.html (Decimal construction from a
string is exact). G-AX asserts `Decimal(str(value)) == value` and equal digit
tuples over 13 boundary + 20000 fuzz inputs (0 violations).

### 3.2 Lossy reconstruction (`narrowed_to_significand`) ↔ `Decimal(str(float(value)))` (A-reference)
**Callees:** CPython `repr(Decimal)`, `float(Decimal)`, `str(float)`,
`Decimal(str)`. `repr(Decimal)` returns `"Decimal('…')"`, which `Decimal(...)`
cannot parse (`InvalidOperation`), so the pre-patch code falls back to
`Decimal(str(float(text)))`. `float` is IEEE-754 binary64, whose significand
carries at most 17 significant decimal digits round-trip; a value with more
genuine precision than that is rounded to the nearest representable binary
fraction, dropping the surplus digits. `narrowed_to_significand` models exactly
this: keep the leading `significand_budget()` significant digits, lose the rest.
G-AX asserts the bug-path reconstruction has the same `float` image as the value
(it carries no more than significand precision) over the same boundary + fuzz
inputs, and exhibits ≥10 long-precision threshold inputs where the bug path
diverges from the value while the fix path is exact (the discriminating F2P
behaviour). Docs: https://docs.python.org/3/tutorial/floatingpoint.html.

**Flag dependency:** none. The behaviour relies only on CPython's default
`str`/`repr`/`float`/`Decimal` semantics (no locale, no decimal context tweak
in the reconstruction step). The `Decimal` import in the patched module is the
same `decimal` module `axiom_check.py` imports.
