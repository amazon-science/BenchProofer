# mapping.md — django__django-13023

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f83b44075dafa429d59e8755aa47e15577cc49f9`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `coerce_to_numeric(kind)` | `DecimalField.to_python(self, value)` — `django/db/models/fields/__init__.py:1497` (body lines 1498–1510) | the modeled changed function (value→Decimal coercion) |
| `construct_numeric(kind)` *(axiom — A-consumed)* | `decimal.Decimal(value)` — CPython stdlib `decimal` module, called at `django/db/models/fields/__init__.py:1503` | the unchanged numeric constructor the coercion invokes; whose rejection class the patch newly classifies |
| `from_floating()` *(axiom — A-consumed)* | `self.context.create_decimal_from_float(value)`'s returned `Decimal` on an operand it accepts — CPython stdlib `decimal.Context` method, called at `django/db/models/fields/__init__.py:1501` | the unchanged floating-path callee's accepted token; pins the floating-path result (its value left abstract) |
| `convert_floating(kind)` *(axiom — A-consumed)* | the same `self.context.create_decimal_from_float(value)` call at `django/db/models/fields/__init__.py:1501`, viewed as accept-or-refuse | the unchanged floating-path callee. **Called at line 1501, ABOVE and OUTSIDE the `try` that opens at line 1502**, so its own rejection is never converted by the handler at line 1504. Accepts a genuine `float` — and any `int` operand, since the callee's exact check is `PyFloat`/`PyLong` (kind 1); refuses with `TypeError` a value that satisfies the branch's `isinstance(value, float)` guard without being one of those two operand types (kind 7); and refuses with `decimal.Overflow` a value whose operand type it DOES accept but whose magnitude exceeds the context's `Emax` (kind 8). Three outcomes, not two. |
| `accepted_value(kind)` *(axiom — A-consumed)* | `decimal.Decimal(value)`'s returned `Decimal` on an accepted value — CPython stdlib `decimal` module, called at `django/db/models/fields/__init__.py:1503` | the value the unchanged constructor returns for an accepted value; pins the accepted-path result token (its value left abstract, symmetric with `from_floating`) |
| `value_kind()` *(axiom — A-consumed)* | the acceptance kind of the single `value` argument of `DecimalField.to_python` — `django/db/models/fields/__init__.py:1497` | the acceptance shape of THE value in scope, i.e. the one value each callee above is applied to at lines 1501/1503. It carries no repo call of its own: it names which shape the argument has, so a callee tag that is not this kind denotes no call the coercion makes (see §3.4). |
| `ValidationFailure` (exception) | `django.core.exceptions.ValidationError` raised at `django/db/models/fields/__init__.py:1505` (`exceptions.ValidationError(self.error_messages['invalid'], code='invalid', params={'value': value})`) | the uniform validation failure the coercion surfaces |
| `ConstructorMalformedError` (exception) | `decimal.InvalidOperation` (the class caught pre-patch at line 1504) | constructor rejection: malformed numeric literal (e.g. `'abc'`, `'non-numeric string'`) |
| `ConstructorOperandError` (exception) | builtin `TypeError` | wrong-typed-operand rejection. Raised by BOTH modeled callees, which is why ONE stand-in denotes it for both: from `decimal.Decimal(value)` at line 1503 (kind 4 — newly caught by the patch, so CONVERTED to the validation failure) and from `create_decimal_from_float(value)` at line 1501 (kind 7 — outside the `try`, so it PROPAGATES). Same class, opposite fates, decided by which callee raised it: `{}`, `set()`, `object()`, `complex()`, `b'...'` are kind 4; a value satisfying the floating-branch guard without being a real float is kind 7. |
| `ConstructorDomainError` (exception) | builtin `ValueError` (newly caught by the patch) | constructor rejection: out-of-domain argument (e.g. `()`, `[]`) |
| `ConversionRangeError` (exception) | `decimal.Overflow` — raised by `create_decimal_from_float(value)` at `django/db/models/fields/__init__.py:1501` when the operand's TYPE is accepted (the callee takes `int` as well as `float`) but its magnitude exceeds the conversion context's `Emax`. Caught by NEITHER the pre-patch nor the patched handler: `decimal.Overflow`'s MRO is `Overflow → Inexact → Rounded → DecimalException → ArithmeticError → Exception`, so it is a subclass of none of `decimal.InvalidOperation` / `TypeError` / `ValueError` / `OverflowError`. Because the call is outside the `try`, it propagates raw — identically on the base and patched trees. | the floating conversion's SECOND, distinct rejection: out of its context's representable range (kind 8). Distinct from `ConstructorRangeError` (the constructor's `OverflowError`, kind 6) — the two are unrelated classes. |
| `ConstructorRangeError` (exception) | builtin `OverflowError` (caught by NEITHER the pre-patch nor the patched code) | constructor rejection: a component of the value lies outside the internal range the representation can hold (e.g. `(0,(1,),2**63)`, `(0,(10**100,),0)`). The coercion does NOT classify this shape, so it propagates to the caller unchanged — identically on the base and patched trees. |

Pre-patch source under change (line 1502–1510):
```python
try:
    return decimal.Decimal(value)
except decimal.InvalidOperation:
    raise exceptions.ValidationError(
        self.error_messages['invalid'],
        code='invalid',
        params={'value': value},
    )
```
The gold patch changes line 1504 only:
`except decimal.InvalidOperation:` → `except (decimal.InvalidOperation, TypeError, ValueError):`.

The two branches above the `try` (line 1498 `if value is None: return value`;
line 1500 `if isinstance(value, float): return self.context.create_decimal_from_float(value)`)
are UNCHANGED by the patch and are modeled as the kind-0 / kind-1 / kind-7 fast
paths of `coerce_to_numeric`; they never reach the constructor and are included
so the coercion's normal-return surface is complete (directive:
skeleton-faithful).

**The floating branch dispatches to a SECOND callee, not the constructor, and
that call sits outside the `try`.** Line 1500 guards on
`isinstance(value, float)` while line 1501's `create_decimal_from_float`
performs an EXACT `PyFloat`/`PyLong` type check in the C `_decimal` accelerator
(no duck-typed `__float__` call). The guard therefore admits strictly more than
the conversion accepts: a value whose `__class__` is `float` without being a real
float — e.g. Django's own `django.utils.functional.SimpleLazyObject(lambda: 1.5)`,
or `unittest.mock.MagicMock(spec=float)` — passes line 1500 and is then refused
by line 1501 with `TypeError`. Because that call is ABOVE the `try` at line 1502,
the handler at line 1504 cannot see it and the `TypeError` escapes `to_python`
unchanged. Measured on both trees at `base_commit` with
`DecimalField(max_digits=4, decimal_places=2)`:
`f.to_python(SimpleLazyObject(lambda: 1.5))`, `f.clean(..., None)` and
`f.get_prep_value(...)` all raise a raw `TypeError` on the base tree AND on the
gold-patched tree — identically, so this is NOT part of the patch delta. It is
modeled as kind 7, with `Exsures(ConstructorOperandError, kind == 7)` on the
coercion. GENUINE floats are unaffected and remain kind 1: measured over 40018
float inputs across four field shapes (`max_digits` 1/4/50/None), including
`±0.0`, `±inf`, `nan`, `sys.float_info.max`/`min`, `5e-324` and `float`
SUBCLASSES, `create_decimal_from_float` raised ZERO times.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `value` argument (arbitrary Python object) | `int` *acceptance kind* | `value` ↦ `kind`: `None`↦0; `isinstance(value,float)` ↦ **1 if `create_decimal_from_float(value)` converts it, 7 if that call refuses it with `TypeError` (the operand's type is neither `float` nor `int`), 8 if that call refuses it with `decimal.Overflow` (the operand's type IS accepted but its magnitude exceeds the conversion context's `Emax`)** — the guard at line 1500 admits strictly more than the conversion at line 1501 converts, in TWO independent ways, and line 1501 sits outside the `try`; otherwise the kind among {2,3,4,5,6} that `decimal.Decimal(value)`'s behaviour exhibits (accept / InvalidOperation / TypeError / ValueError / OverflowError). The map is TOTAL over 0..8: a 40000-input cross-arm census (axiom_check.py) found no fifth constructor rejection class, and the floating callee's rejection classes on the values the guard admits are exactly `TypeError` and `decimal.Overflow` (probed over 10 guard-satisfying non-numeric-payload shapes plus int-payload spoofers on both sides of `Emax`), so every Python object whose `__class__` access is well-behaved lowers to some kind in 0..8 and no real input class is excluded from the model's domain. `conformance_check.py` now treats a value that lowers to NO kind as a hard FAILURE rather than a silent skip, so an undeclared escaping class cannot hide from G-CONF. The discriminating observable of the bug is purely WHICH outcome `to_python` produces, not the value's contents — so the value collapses to its acceptance kind. (Nagini bans `str` indexing and there is no per-character observable here.) |
| the produced `decimal.Decimal` | non-null `int` token (`accepted_value(2)`) | the coercion's accepted-path result IS observed directly by P2P `test_to_python` (`assertEqual(f.to_python(3), Decimal("3"))`, `assertEqual(f.to_python("3.14"), Decimal("3.14"))`), so its value is part of the pinned behaviour and must be pinned to the constructor's own returned token — NOT merely "not None". Modeled as the abstract token `accepted_value(2)` (the constructor's value, left abstract, never fabricated by the proof), symmetric with the float branch's `from_floating()`. The accepted branch must return EXACTLY this token (`Result() == accepted_value(kind)`); a constant or wrong token would verify under a `not None`-only spec yet break `test_to_python`. |
| `value is None` returned for absent input | the null token `None` (`Optional[int]`) | the absent value passes straight through unchanged. |
| `self.context.create_decimal_from_float(value)` (line 1501) | `convert_floating(kind)` — returning the non-null token `from_floating()` on kind 1, raising `ConstructorOperandError` on kind 7, raising `ConversionRangeError` on kind 8 | the floating path never reaches the constructor, but it is NOT rejection-free: it accepts every genuine float (incl. `±inf`/`nan`/subclasses — measured 40018 inputs, 0 raises) and refuses a non-float that satisfies the branch's `isinstance` guard, which escapes the coercion unconverted because the call is outside the `try`. Its accepted Decimal content is precision-dependent and unobserved by the pinned exception-classification behaviour, so the accepted token is left abstract. |
| `exceptions.ValidationError(...)` raise | `raise ValidationFailure()` | a builtin/Django exception in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so each repo exception class is a user-defined stand-in. The discriminating observable is the exception's *identity* (validation failure vs. raw constructor error), which the stand-ins preserve. |
| `decimal.InvalidOperation` / `TypeError` / `ValueError` / `OverflowError` / `decimal.Overflow` rejections | `ConstructorMalformedError` / `ConstructorOperandError` / `ConstructorDomainError` / `ConstructorRangeError` / `ConversionRangeError` | five distinct user-defined stand-ins. `ConversionRangeError` denotes `decimal.Overflow`, which the floating conversion raises at line 1501 for an operand whose type it accepts but whose magnitude exceeds the context's `Emax`; it is a subclass of NONE of the other four real classes, so no handler for them catches it and it escapes the coercion raw (kind 8). `ConstructorOperandError` denotes `TypeError` from EITHER modeled callee; WHICH callee raised it is carried by the kind (4 = the constructor inside the `try`, converted; 7 = the floating conversion outside it, propagates), so the single stand-in loses nothing. The distinctness of the first three is what lets the prepatch (catch only the first) leak the other two. The fourth is distinct from all of them in the real hierarchy too (`OverflowError`'s MRO is `OverflowError → ArithmeticError → Exception`; it is a subclass of neither `ValueError` nor `TypeError` nor `decimal.InvalidOperation`), so a handler for the first three does not catch it — which is precisely why the patched code still lets it escape. G-CONF compares a raw escape under this stand-in ↦ real-class binding. |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `construct_numeric` ↔ `decimal.Decimal` (A-consumed)
**Callee:** CPython `decimal.Decimal(value)` (the `decimal` standard-library
module). The coercion invokes it for every value that is neither `None` nor a
`float`. The axiom encodes the WEAKEST facts the proof needs — that the
constructor's outcome on such a value falls into exactly five mutually-exclusive
acceptance kinds, and which exception class each rejection kind raises:

- **kind 2 (accept):** valid numeric input (numeric `str`, `int`, `Decimal`)
  constructs without raising, and the constructed value is the constructor's own
  returned `Decimal`. (`Ensures(kind == 2)` — returns normally iff accepted —
  plus `Ensures(Implies(kind == 2, Result() == accepted_value(2)))`, pinning the
  returned token to the abstract accessor `accepted_value(2)` so the accepted
  result is anchored to the callee's value, not an arbitrary literal. This value
  IS observed by P2P `test_to_python` and so must be pinned, §3.3.)
- **kind 3 (InvalidOperation):** a `str`/`bytes`-like value that is not a valid
  numeric literal raises `decimal.InvalidOperation`
  (`Exsures(ConstructorMalformedError, kind == 3)`). Source: `decimal.Decimal`
  parses the literal via `_parser`; a non-matching literal triggers
  `self._raise_error(ConversionSyntax, ...)`, an `InvalidOperation` subclass.
- **kind 4 (TypeError):** a value whose type the constructor cannot accept at all
  (`dict`, `set`, `object`, `complex`, `bytes`/`bytearray`, etc.) raises
  `TypeError` (`Exsures(ConstructorOperandError, kind == 4)`). Source: the
  `Decimal.__new__` type dispatch falls through to
  `raise TypeError("conversion from %s to Decimal is not supported" ...)`.
- **kind 5 (ValueError):** a value the constructor begins to accept by shape but
  finds out of domain — notably an empty/non-empty *tuple* or *list* coordinate
  form — raises `ValueError` (`Exsures(ConstructorDomainError, kind == 5)`).
  Source: the tuple/list digit-coordinate path
  (`if isinstance(value, (list, tuple))`) validates the 3-element
  `(sign, digits, exponent)` shape and `raise ValueError(...)` on a bad shape;
  `()` and `[]` (0 elements) and `(1,2)`/`[1,2,3]` (wrong length) hit it, as do
  in-range but ill-formed components (`(2,(1,),0)` bad sign, `(0,(10,),0)` bad
  digit, `(0,(1,),'x')` bad exponent string).
- **kind 6 (OverflowError):** a value whose 3-element coordinate shape is
  well-formed but one of whose *components* cannot be lowered to a C integer
  raises `OverflowError` (`Exsures(ConstructorRangeError, kind == 6)`). Source:
  the C `_decimal` (libmpdec) accelerator — the implementation `import decimal`
  binds, hence the one django calls — converts the sign and each digit with
  `PyLong_AsLong` and the exponent with `PyLong_AsSsize_t`, and propagates the
  `OverflowError` those raise. Measured: `(0,(1,),2**63)` and `(0,(1,),-2**63-1)`
  overflow the exponent (`"Python int too large to convert to C ssize_t"`) while
  the boundary values `(0,(1,),2**63-1)` and `(0,(1,),-2**63)` still fit and are
  kind 3; `(0,(10**100,),0)` and `(10**100,(1,),0)` overflow a digit / the sign
  (`"...to C long"`).

  **This is the one rejection kind the coercion does NOT convert.** `to_python`
  catches `decimal.InvalidOperation` (pre-patch) or
  `(decimal.InvalidOperation, TypeError, ValueError)` (patched); `OverflowError`
  is in neither set and is a subclass of none of them, so it propagates to the
  caller unchanged. Verified end-to-end on both trees at `base_commit`, with the
  F2P call shape `DecimalField(max_digits=4, decimal_places=2)`:
  `f.to_python((0,(1,),2**63))` and `f.clean((0,(1,),2**63), None)` raise
  `OverflowError` on the base tree AND on the gold-patched tree — identically, so
  this is not part of the patch delta. The model therefore states this leg as
  `Exsures(ConstructorRangeError, kind == 6)` on `coerce_to_numeric`: modelling it
  as a validation failure would claim a guarantee the real function does not have,
  and omitting kind 6 from the domain would exclude a real, in-domain input class.
  (Note this is a property of the C accelerator: `_pydecimal` instead accepts
  `(0,(1,),2**63)`. The C accelerator is the shipped and tested configuration.)

**The axiom is the weakest sufficient contract**, not the full `decimal.Decimal`
semantics: it pins only that each of the five kinds returns/raises as stated. It
is NEVER stronger than the real callee — `axiom_check.py` (G-AX) executes the
REAL `decimal.Decimal` on boundary + 8000 fuzz inputs of every kind (and the 8
exact F2P `test_invalid_value` inputs) and asserts each rejection is EXACTLY the
declared class; a further 40000-input cross-arm census asserts that no rejection
escapes the FOUR declared classes, i.e. that there is no fifth class. The kind-6
fuzzer drives each of the three component positions past the C boundary — the
blind spot in the earlier small-int-only kind-5 fuzzer. Exit 0 iff sound.
Docs: https://docs.python.org/3/library/decimal.html#decimal.Decimal.

### 3.2 `from_floating` / `convert_floating` ↔ `decimal.Context.create_decimal_from_float` (A-consumed)
**Callee:** CPython `decimal.Context.create_decimal_from_float(value)`, invoked on
the float fast path (line 1501) as `self.context.create_decimal_from_float(value)`.
This callee is modeled by an axiom PAIR, because it both returns a value and can
reject:

- **`convert_floating(kind)`** — the call's accept-or-refuse behaviour:
  `Ensures(kind == 1)` (returns normally iff the conversion accepts the operand),
  `Ensures(Implies(kind == 1, Result() == from_floating()))` (the accepted return
  is EXACTLY this callee's token), and
  `Exsures(ConstructorOperandError, kind == 7)`.
- **`from_floating()`** — a `@Pure` VALUE accessor for that accepted token, left
  ABSTRACT and never fabricated by the proof, exactly analogous to
  `accepted_value` over the constructor (§3.3).

**Why the kind-7 AND kind-8 legs are required for faithfulness, not a weakening.**
The claim "this callee converts EVERY value the coercion routes to it, without
raising" is FALSE of the real callee, and so is the weaker claim that its only
refusal is a wrong-typed operand. There are TWO independent gaps: the mismatch
between the branch's guard and the callee's own type check, and the mismatch
between the operand types the callee accepts and the magnitudes its context can
represent. Line 1500 guards on
`isinstance(value, float)`; line 1501's `create_decimal_from_float` does an EXACT
`PyFloat`/`PyLong` check in the C `_decimal` accelerator, not a duck-typed
`__float__` call. So a value whose `__class__` is `float` without being a real
float takes the branch and is then refused with `TypeError`. Since line 1501 is
ABOVE the `try` at line 1502, the handler at line 1504 never sees it and the
`TypeError` escapes `to_python` raw — on the base tree and the gold-patched tree
alike, so this is not part of the patch delta. Witness, measured on both trees
with `DecimalField(max_digits=4, decimal_places=2)`:
`f.to_python(SimpleLazyObject(lambda: 1.5))` → raw
`TypeError: argument must be int or float`. An axiom with no `Exsures` would be
strictly STRONGER than the callee, so an implementation faithful to the repo on
that input class would fail the spec; stating the refusal as a propagating leg —
rather than deleting the obligation, or narrowing the precondition to exclude the
guard-satisfying non-floats — is what makes `verify ⇒ correct` hold on the whole
domain. The domain was WIDENED (`0 <= kind <= 8`), never narrowed.

**The kind-8 leg: the callee's SECOND refusal.** `create_decimal_from_float`
accepts `int` operands as well as `float` ones (its exact check is
`PyFloat`/`PyLong`), so an `int` SUBCLASS whose `__class__` is `float` — the same
`__class__`-spoofing species as the kind-7 shapes, with an int payload instead of
an object payload — satisfies the guard at line 1500 AND passes the callee's type
check, i.e. it is NOT a kind-7 case. It is then refused by the conversion
context's `Overflow` trap once its magnitude exceeds `Emax`. Witness, measured on
the base tree AND the gold-patched tree (so not a patch delta), with
`DecimalField(max_digits=4, decimal_places=2)` and identically for
`f.to_python` / `f.clean(W, None)` / `f.get_prep_value(W)` at `max_digits` in
{1, 4, 28, 50, None}:

```python
class IntSpoofFloat(int):
    __class__ = float
W = IntSpoofFloat(10 ** 1000000)
isinstance(W, float)     # True  -> the line-1500 branch IS taken
decimal.Decimal(W)       # ok    -> so NOT the kind-6 constructor arm
f.to_python(W)           # raw decimal.Overflow, traceback at line 1501
```

The threshold is the context's `Emax` = 999999 and is precision-INDEPENDENT
(`Context(prec=max_digits)` leaves `Emax` at its default for every `max_digits`
above): `10**999999` converts normally (kind 1) and `10**1000000` traps
(kind 8) — measured by bisection at every `max_digits` above. `decimal.Overflow`
matches NO other stand-in's real class (`isinstance(e, TypeError)`,
`isinstance(e, ValueError)`, `isinstance(e, decimal.InvalidOperation)` and
`isinstance(e, OverflowError)` are all `False`; its MRO is
`Overflow → Inexact → Rounded → DecimalException → ArithmeticError → Exception`),
so before this leg existed the value satisfied NO declared kind and an
implementation faithful to the repo violated the coercion's
"only raises ValidationFailure / ConstructorRangeError / ConstructorOperandError"
postcondition. Stating it as a fifth stand-in with a propagating leg is the same
widening the kind-6 and kind-7 legs already are. `decimal.Overflow` is exclusive
to the FLOATING arm: measured, `decimal.Decimal(value)` at line 1503 (called with
no `context=`, so trap-free) raises only `InvalidOperation` and `OverflowError`
on the coordinate arm and never `decimal.Overflow`, so kinds 6 and 8 are genuinely
different classes from different callees.

**Soundness of both legs, and the boundary between them.** `axiom_check.py`
(G-AX) runs the real `create_decimal_from_float` with a `prec=4` context (as the
F2P field uses) on boundary floats (0, ±0, large/small magnitudes, ±inf, nan,
`sys.float_info.max`/`min`, `5e-324`, and a genuine `float` SUBCLASS) plus 2000
fuzz floats and asserts a normal return every time — genuine floats are kind 1
and never reject. It then asserts that each of 10 guard-satisfying non-float
shapes (`SimpleLazyObject`, `MagicMock`/`Mock`/`NonCallableMock(spec=float)`, and
`__class__`-attribute / `__class__`-property spoofers) FIRST satisfies
`isinstance(v, float)` (so the branch is really taken — otherwise the probe would
be ineffective and the check fails loudly) and THEN is refused with EXACTLY
`TypeError`. It then asserts that int-payload `__class__ = float` spoofers straddling the
context's `Emax` split as the kind-1/kind-8 boundary declares: `10**Emax`
converts normally, while `10**(Emax+1)`, `-10**(Emax+1)` and `10**(Emax+5)` are
refused with a class that is neither `TypeError` (kind 7) nor `OverflowError`
(the constructor's kind 6). These are the two boundaries the earlier
genuine-floats-plus-TypeError-spoofers probe could not reach: "every genuine
float converts" is true, but the branch's guard admits strictly more than genuine
floats, and this callee refuses in TWO distinct ways there — a wrong-typed
operand and an out-of-range magnitude. Genuine floats cap near 1e308, far inside
`Emax`, so only an int-payload spoofer reaches the second one. Docs:
https://docs.python.org/3/library/decimal.html#decimal.Context.create_decimal_from_float.
The floating path never reaches the general constructor and is UNCHANGED by the
patch.

### 3.3 `accepted_value` ↔ `decimal.Decimal(value)`'s accepted return (A-consumed)
**Callee:** the same unchanged CPython `decimal.Decimal(value)` (line 1503),
viewed as a value accessor for the kind-2 (accepted) path. The axiom claims only
the WEAKEST fact the proof needs: on an accepted value the constructor returns a
constructed (non-null) `Decimal` token (`Requires(kind == 2)`,
`Ensures(Result() is not None)`; the token's value is left ABSTRACT, never
fabricated by the proof). The `construct_numeric` axiom ties the constructor's
accepted return to this accessor (`Implies(kind == 2, Result() == accepted_value(2))`),
and the `coerce_to_numeric` accepted branch returns EXACTLY this token
(`Result() == accepted_value(kind)`), so the accepted result is anchored to the
constructor's own value — symmetric with the float branch's `from_floating()`.
**Why this is needed (not over-modeling):** P2P `test_to_python` observes the
accepted value directly (`assertEqual(f.to_python(3), Decimal("3"))`,
`assertEqual(f.to_python("3.14"), Decimal("3.14"))`). A spec that pinned the
accepted result only to `Result() is not None` admits an impl returning a
constant or the wrong callee's token (e.g. `return 1`, `return from_floating()`)
that verifies yet breaks `test_to_python` — a real spec-too-weak hole. Pinning to
`accepted_value` closes it without rejecting the gold (the gold impl
`return decimal.Decimal(value)` returns exactly the constructor's token).
`axiom_check.py` (G-AX) confirms soundness: the real `decimal.Decimal(value)`
returns a non-null `Decimal` on every accepted input (it is the same returned
object whose `not None`-ness the existing kind-2 acceptance check already
exercises), so `accepted_value`'s `Ensures(Result() is not None)` never
over-claims. Docs:
https://docs.python.org/3/library/decimal.html#decimal.Decimal.

**Flag/configuration dependency:** none. `decimal.Decimal(value)` is called
with the single positional `value` (no `context=` argument — the local thread
context is irrelevant to *which exception class* a rejection raises; precision
context affects only accepted values' rounding, which is unobserved here). The
F2P `test_invalid_value` builds `DecimalField(max_digits=4, decimal_places=2)`
and calls `field.clean(value, None)`, which reaches `to_python(value)`; the
default decimal context never converts a rejection into a different class.

### 3.4 `value_kind` ↔ the acceptance shape of the `value` argument (A-consumed)
**Callee:** none of its own — this is the accessor for the acceptance kind of THE
single `value` argument `DecimalField.to_python` was handed (line 1497), i.e. the
one value both real callees are applied to (`create_decimal_from_float(value)` at
line 1501, `decimal.Decimal(value)` at line 1503). The axiom claims only the
weakest fact the proof needs: the value in scope HAS an acceptance shape, inside
the total kind range (`Ensures(0 <= Result() and Result() <= 8)`), which is
exactly §2's totality claim for the value↦kind map — the upper bound is 8, not 7,
because the floating callee has TWO refusals (§3.2): the wrong-typed-operand one
(kind 7) and the out-of-representable-range one (kind 8, `decimal.Overflow` once
the operand's magnitude passes the conversion context's `Emax`). Any bound that
stopped at 7 would FORCE a kind-8 value into a kind whose declared outcome it does
not have, which is the one way this nullary accessor could make the spec stronger
than the real function rather than weaker.
**Why this is needed (not over-modeling):** the axiomatized callees take `kind`
as a parameter, but the real calls they denote take no such argument — both apply
their call to the value in scope and are *functions of that value*. That is not a
reading of the prose; it is what the bundle's own executable refinement does
(`conformance_check.py`: each callee bridge ignores its `kind` parameter and
applies the real call to the value the coercion is running on). Without a clause
tying a callee's tag to the value's own shape, an impl may invoke a callee at a
LITERAL tag — `convert_floating(1)`, `construct_numeric(2)` — and read the axiom's
contract at that tag while the call it denotes is applied to a value of a
different shape. Those calls verify (the literal satisfies the axiom's `Ensures`,
so the call is proved non-raising) yet denote a real call that raises: e.g.
`convert_floating(1)` reached with a non-float value in scope denotes
`create_decimal_from_float(value)` on a `str`/`Decimal`, which raises
`TypeError: argument must be int or float` and escapes `to_python` unconverted;
`construct_numeric(2)` reached on the absent path denotes `decimal.Decimal(None)`,
which raises `TypeError: conversion from NoneType to Decimal is not supported`.
`Requires(kind == value_kind())` on `convert_floating` and `construct_numeric`
closes this without rejecting the gold: the gold impl passes the coercion's own
`kind` to every callee, and `coerce_to_numeric` carries the same tie, so each
call's tag IS the value's shape. It is a pure strengthening — it removes calls
that denote nothing the coercion can do, and constrains no input: `value_kind()`
is nullary and abstract, so the coercion's body is still verified at every kind in
0..8 (controls in verdict-independent probes: an impl returning normally on kind 7,
one returning normally on kind 8, one routing the kind-8 refusal into the uniform
validation failure, one letting the kind-4 operand rejection escape, one dropping
the kind-2 value pin, and an `Assert(False)` vacuity control all still FAIL to
verify).
**Flag/configuration dependency:** none.
