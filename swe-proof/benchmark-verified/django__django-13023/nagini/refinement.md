# refinement.md — django__django-13023

The operation-by-operation correspondence between `model.py`'s implementation
(the `coerce_to_numeric` impl region and the live `construct_numeric` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`/`Exsures`, and **A-reference**, where a deep model is validated
== the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The coercion site — `DecimalField.to_python` (`django/db/models/fields/__init__.py:1497`)

Gold hunk (line 1504):
```
-        except decimal.InvalidOperation:
+        except (decimal.InvalidOperation, TypeError, ValueError):
             raise exceptions.ValidationError(
                 self.error_messages['invalid'],
                 code='invalid',
                 params={'value': value},
             )
```

| # | model.py impl op (`coerce_to_numeric`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `kind: int` | `value` (arbitrary object) argument of `to_python` | R | `value` ↔ its *acceptance kind* (mapping.md §2): the only observable of the pinned behaviour is which outcome the coercion produces, which is a function of `value`'s kind. |
| A1b | `Requires(kind == value_kind())` on `coerce_to_numeric`, `convert_floating` and `construct_numeric` | the single `value` argument every callee at lines 1501/1503 is applied to | R | the real callees take no acceptance tag: each is applied to the value in scope, so its behaviour is a function of THAT value's shape (this is what the bundle's own `conformance_check.py` bridges implement — they ignore the `kind` parameter and call the real callee on the current value). The tie says the tag at every callee site IS the shape of the value in scope, so a call at a literal tag (`convert_floating(1)`, `construct_numeric(2)`) — which would read the axiom at one shape while denoting a real call on a value of another — denotes no step the coercion performs. Pure strengthening: `value_kind()` is nullary and abstract, so no input is excluded (the body is still verified at every kind 0..8) and the gold, which passes the coercion's own `kind` to each callee, is unaffected. mapping.md §3.4. |
| A2 | `if kind == 0: return None` | `if value is None: return value` (line 1498) | R + I | the absent-value fast path, unchanged by the patch; `None` ↔ kind 0, the null token is `value` itself. |
| A3 | `if kind == 1 or kind == 7 or kind == 8: return convert_floating(kind)` | `if isinstance(value, float): return self.context.create_decimal_from_float(value)` (lines 1500–1501) | R + A-consumed | the floating fast path, unchanged by the patch; it never reaches the constructor, and it is a SECOND callee invoked at line 1501, i.e. ABOVE and OUTSIDE the `try` that opens at line 1502. `convert_floating` is the A-consumed axiom for `create_decimal_from_float` as accept-or-refuse: it returns normally iff the conversion accepts the operand (kind 1), returning EXACTLY that callee's token (`Result() == from_floating()`, value abstract, mapping.md §3.2 — so the value is pinned to the callee, not to an arbitrary literal, G-MUT tightness), raises `ConstructorOperandError` on kind 7, and raises `ConversionRangeError` on kind 8. Kinds 7 and 8 are REAL, not hypothetical: line 1500 guards on `isinstance` while line 1501 type-checks exactly (C `_decimal`, no `__float__` call), so a value whose `__class__` is `float` without being a real float — e.g. `SimpleLazyObject(lambda: 1.5)` — takes the branch and is refused with `TypeError`, which escapes `to_python` unconverted because the call is outside the `try` (measured identically on the base and gold-patched trees, so not a patch delta). The callee has a SECOND, distinct refusal: it accepts `int` operands too (its exact check is `PyFloat`/`PyLong`), so an int SUBCLASS with `__class__ = float` passes both the guard and the type check and is then refused by the conversion context's `Overflow` trap once its magnitude exceeds `Emax` — `decimal.Overflow`, a class that is a subclass of none of `TypeError` / `ValueError` / `InvalidOperation` / `OverflowError`, so no handler catches it and it too escapes raw (kind 8). Witness `IntSpoofFloat(10**1000000)` → raw `decimal.Overflow` at line 1501, measured on the base AND gold-patched trees at `max_digits` in {1,4,28,50,None} and for `to_python`/`clean`/`get_prep_value` alike; the `Emax` = 999999 threshold is precision-independent, with `10**999999` still kind 1. Genuine floats, incl. `±inf`/`nan`/subclasses, are kind 1 and never reject (40018 measured inputs, 0 raises) — they cap near 1e308, far inside `Emax`, which is why only an int-payload spoofer reaches kind 8. mapping.md §3.2. Its precision-dependent Decimal content is unobserved by the exception-classification behaviour. |
| A4 | `construct_numeric(kind)` inside the `try` | `decimal.Decimal(value)` inside the `try` (line 1503) | A-consumed | `construct_numeric` is the WEAKEST contract on `decimal.Decimal` the proof needs: returns normally iff kind 2 — and the accepted return is EXACTLY the constructor's token `accepted_value(2)` (`Ensures(Implies(kind == 2, Result() == accepted_value(2)))`) — else raises one of three DISTINCT rejection classes (malformed-literal / wrong-typed-operand / out-of-domain) for kinds 3/4/5 (mapping.md §3.1, §3.3). The proof consumes its `Ensures(kind==2)`, the accepted-value pin, and all three `Exsures`. The accepted result therefore propagates to the coercion's kind-2 postcondition `Result() == accepted_value(kind)`, anchoring the accepted value to the constructor (symmetric with the float branch's `from_floating()`) — this pins the value P2P `test_to_python` observes (`f.to_python(3) == Decimal("3")`), which a `not None`-only postcondition would leave free. G-AX confirms `construct_numeric` and `accepted_value` against the real `decimal.Decimal`. |
| A5 | `except ConstructorMalformedError: raise ValidationFailure()` **and** `except ConstructorOperandError: raise ValidationFailure()` **and** `except ConstructorDomainError: raise ValidationFailure()` | `except (decimal.InvalidOperation, TypeError, ValueError): raise exceptions.ValidationError(...)` (lines 1504–1509) | R + I | the patched handler. The gold patch's three-class tuple `(InvalidOperation, TypeError, ValueError)` ↔ the three distinct stand-in classes; catching all three and re-raising the uniform `ValidationFailure` ↔ raising `exceptions.ValidationError` (mapping.md §1,§2). A single multi-class `except` and three single-class `except` clauses that all `raise ValidationFailure()` are observationally identical: every rejection becomes the validation failure. |

The discriminating content of the change — the constructor's wrong-typed-operand
(`TypeError`, kind 4) and out-of-domain (`ValueError`, kind 5) rejections must
ALSO become a validation failure, not just the malformed-literal rejection
(`InvalidOperation`, kind 3) — lives in `coerce_to_numeric` catching all three
stand-in classes (model) ⇔ the three-class `except` tuple (real). The pre-patch
caught only `decimal.InvalidOperation`; `model_prepatch.py` reproduces that
(catches only `ConstructorMalformedError`) and **fails** verification on the
postcondition *"method only raises exceptions of type ValidationFailure"* —
because on kinds 4 and 5 it lets the constructor's own `ConstructorOperandError`
/ `ConstructorDomainError` escape, an exception class the frozen spec never
declares. That is exactly the spec sensing the change (G-DIFF). It is also the
exact F2P observation: `field.clean({}, None)` / `field.clean((), None)` must
raise `ValidationError`, not a raw `TypeError` / `ValueError`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— widening the caught-exception set so EVERY constructor rejection is funneled to
the validation failure — is modeled **directly** by the three `except` clauses in
`coerce_to_numeric` over the three distinct rejection stand-ins (step A5), driven
by the `construct_numeric` axiom's three `Exsures` (step A4). The constructor
itself, `decimal.Decimal`, is UNCHANGED by the patch; it is an **A-consumed**
axiom whose rejection-class behaviour G-AX validates against the real callee. The
floating-path callee `create_decimal_from_float` is a second **A-consumed**
callee, unchanged by the patch, modeled by the axiom PAIR `convert_floating`
(accept-or-refuse) + `from_floating` (the accepted token's value accessor). It is
present both to pin the floating result to its callee and because that callee can
itself REFUSE: G-AX validates that it accepts every genuine float without raising
AND that its rejection classes on the values the branch's guard admits are
exactly TWO — the wrong-typed-operand class and the out-of-representable-range
class of its own context — both of which the coercion propagates because the call
sits outside the `try`. Enumerating only the first would make the axiom stronger
than the callee on the int-payload guard-satisfiers, whose magnitude the context
cannot represent. The accepted-value
accessor `accepted_value` is a fourth **A-consumed** axiom over the same unchanged
`decimal.Decimal(value)` return, present only to pin the kind-2 accepted result
to the constructor's own token (symmetric with `from_floating`), so the value
P2P `test_to_python` observes is anchored to the callee rather than left free
(G-AX validates the constructor returns a non-null `Decimal` on accepted inputs).
There is no axiom about the function under change (`to_python`), and no
A-reference deep model (the change is not a value computation but an
exception-classification widening, modeled directly).

## C. verify(model) ⇒ resolved

`coerce_to_numeric` verifies only if, for every CLASSIFIED rejection kind
(3, 4, 5), it raises the uniform `ValidationFailure`
(`Exsures(ValidationFailure, kind in {3,4,5})`), only if the three UNCLASSIFIED
rejection kinds instead let the invoked callee's own low-level error reach the
caller — kind 6 the constructor's out-of-representable-range class
(`Exsures(ConstructorRangeError, kind == 6)`), kind 7 the floating
conversion's wrong-typed-operand class
(`Exsures(ConstructorOperandError, kind == 7)`) and kind 8 the floating
conversion's out-of-representable-range class
(`Exsures(ConversionRangeError, kind == 8)`) — and only if nothing else
escapes on any kind (the "only raises exceptions of types ValidationFailure,
ConstructorRangeError, ConstructorOperandError, ConversionRangeError"
postcondition). It further
verifies only if the accepted kinds (0, 1, 2) return normally with the right
token: kind 0 the null token, kind 1 EXACTLY `from_floating()`, and kind 2
EXACTLY `accepted_value(kind)` (the constructor's own returned value, not an
arbitrary non-null literal — this is what P2P `test_to_python` asserts).

The four `Exsures` legs are TOTAL over the rejection space and mutually
exclusive: every rejection kind appears in exactly one of them, so the spec is
silent nowhere and does not admit both answers anywhere. Their combination is
what pins the classification boundary itself — an impl that converts too little
(the prepatch: kinds 4/5 escape) fails the first leg, and an impl that converts
too much (a blanket handler that also swallows kind 6, 7 or 8) fails both the
first leg (it raises `ValidationFailure` on a kind the leg excludes) and the
corresponding propagation leg.

The kind-7/kind-8 pair is a second sharp boundary, on the SAME callee: both are
refusals by `create_decimal_from_float` at line 1501 and both propagate, but they
are DISTINCT low-level classes with distinct causes (an operand type the callee
cannot take, versus an operand type it can take whose magnitude its context
cannot represent), so the caller can tell them apart. The spec pins each class to
its own kind, so an impl that swaps them, converts either into the validation
failure, or returns normally on either, fails.

The kind-4/kind-7 pair is the sharpest of these boundaries, because both raise
the SAME low-level class and the spec gives them OPPOSITE fates: kind 4 must be
converted to the validation failure (the constructor raised it, inside the `try`)
while kind 7 must propagate as `ConstructorOperandError` (the floating conversion
raised it, outside the `try`). An impl that moved the floating conversion inside
the `try` satisfies neither leg; so does one that returns normally on kind 7, and
so does one that lets kind 4 escape. Declaring kind 7 therefore opens no door for
kind 4 — the prepatch shape, whose defect is exactly a kind-4/kind-5 escape,
still fails.

By R (`value` ↔ acceptance kind; the five stand-in classes ↔
`decimal.InvalidOperation`/`TypeError`/`ValueError`/`OverflowError`/`decimal.Overflow`;
`ValidationFailure` ↔ `exceptions.ValidationError`) the verified coercion equals
`DecimalField.to_python` with the three-class `except` on the tested inputs.

**Why the kind-7 leg is required for faithfulness, not a weakening.** The
floating branch dispatches to a DIFFERENT callee than the constructor, and the
coercion's uniform-failure handling is placed around the constructor only: line
1501's `create_decimal_from_float` is called ABOVE the `try` that opens at line
1502, so nothing it raises can reach the handler at line 1504. That callee is not
rejection-free on the values the branch routes to it, because the guard and the
callee disagree about what a float is: line 1500 tests
`isinstance(value, float)` while the callee performs an EXACT `PyFloat`/`PyLong`
check in the C `_decimal` accelerator, not a duck-typed `__float__` call. A value
whose `__class__` is `float` without being a real float therefore takes the branch
and is refused with `TypeError` — and Django ships such a class itself
(`django.utils.functional.SimpleLazyObject`). Measured on both trees at
`base_commit` with `DecimalField(max_digits=4, decimal_places=2)`:
`f.to_python(SimpleLazyObject(lambda: 1.5))`, `f.clean(..., None)` and
`f.get_prep_value(...)` all raise a raw `TypeError` on the base tree AND on the
gold-patched tree, identically — so this is not part of the patch delta. A spec
asserting that the floating branch always returns normally would be strictly
STRONGER than the real function: an implementation faithful to the repo on that
input class would FAIL it (machine-checked — replacing only the floating branch's
body with the real outcome fails the "only raises exceptions of types ..."
postcondition against the pre-repair spec). Stating the refusal as a propagating
leg — rather than deleting the obligation, or narrowing the precondition to
exclude the guard-satisfying non-floats — is what makes `verify ⇒ correct` hold
on the whole input domain. The domain was WIDENED (to `0 <= kind <= 7` by this
leg, and to `0 <= kind <= 8` by the kind-8 leg below) rather than narrowed; no
real input class is excluded, and the genuine-float behaviour the F2P/P2P tests
exercise is untouched (kind 1: 40018 measured inputs, 0 raises).

**Why the kind-6 leg is required for faithfulness, not a weakening.** By G-AX
(A-consumed) the real `decimal.Decimal`'s rejections are exactly FOUR classes and
no others: `InvalidOperation`, `TypeError`, `ValueError`, and `OverflowError`
(the last on the `(sign, digits, exponent)` coordinate arm once a component
passes the C `ssize_t`/`long` boundary — mapping.md §3.1). `to_python` catches
the first three and not the fourth, on the base tree and on the gold-patched
tree alike (measured: `f.to_python((0,(1,),2**63))` raises `OverflowError` on
both). A spec asserting "every value either returns normally or raises the
validation failure" would therefore be strictly STRONGER than the real function,
and an implementation faithful to the repo would fail it. Stating the fourth kind
as a raw-propagating leg — rather than deleting the obligation, or narrowing the
precondition to exclude the coordinate forms that reach it — is what makes
`verify ⇒ correct` hold on the whole input domain. (Note the asymmetry with
kind 7: `to_python` does not catch `OverflowError` at all, whereas it DOES catch
`TypeError` — kind 7 escapes not because its class is uncaught but because the
call that raises it sits outside the `try`.) The domain was WIDENED
(`0 <= kind <= 8` with the kind-8 leg below) rather than narrowed; no real input
class is excluded.

**Why the kind-8 leg is required for faithfulness, not a weakening.** The floating
callee refuses in TWO ways, not one, and the second one is what a kind range
stopping at 7 mis-stated. Its exact operand check is `PyFloat`/`PyLong`, so it also
accepts `int`: an `int` SUBCLASS carrying `__class__ = float` satisfies BOTH the
branch guard at line 1500 and the callee's own type check at line 1501, and is then
refused by the conversion context's `Overflow` trap as soon as its magnitude passes
`Emax` = 999999. The escaping class is `decimal.Overflow`, whose MRO is
`Overflow → Inexact → Rounded → DecimalException → ArithmeticError`: it is a
subclass of NONE of `TypeError`, `ValueError`, `decimal.InvalidOperation` or
`OverflowError`, so even the gold-patched three-class handler at line 1504 does not
catch it — and the call that raises it sits outside the `try` in any case. Measured
on the base tree AND the gold-patched tree, for `to_python` / `clean(value, None)` /
`get_prep_value` alike and at `max_digits` in {1, 4, 28, 50, None}: an int-subclass
float-spoofer carrying `10**1000000` raises a raw `decimal.Overflow`, while
`10**999999` still converts normally (`1.000E+999999`). The threshold is `Emax`,
which is precision-independent, so this refusal is NOT part of the patch delta.

A spec whose kind range stopped at 7 was therefore strictly STRONGER than the real
function on a declared-in-domain input class, and no kind assignment could rescue
it: machine-checked kind by kind, an impl producing the real outcome (the
conversion-range class escaping raw) FAILS the pre-repair spec at EVERY one of
kinds 0..7, each time on the implicit `"method only raises exceptions of types
ValidationFailure, ConstructorRangeError, ConstructorOperandError"` postcondition.
The same real outcome VERIFIES under the current spec (16.9s). Stating the second
refusal as its own propagating leg — `ConversionRangeError` for kind 8, a class
distinct from the kind-7 operand one and from the constructor's kind-6
out-of-range one — is what makes `verify ⇒ correct` hold across the whole floating
branch: that branch has THREE outcomes, not two. The leg PINS the boundary rather
than relaxing it: an impl returning normally on kind 8 fails the
`kind == 0 or kind == 1 or kind == 2` leg, and one routing the kind-8 refusal into
the uniform validation failure fails the `kind == 3 or kind == 4 or kind == 5` leg
(both machine-checked). The domain was WIDENED (`0 <= kind <= 8`) rather than
narrowed; no real input class is excluded, and the genuine-float behaviour the
F2P/P2P tests exercise is untouched — genuine floats cap near 1e308, far inside
`Emax`, which is why only an int-payload spoofer reaches kind 8. `Assert(False)`
in the impl still FAILS to verify, so none of these rejections is vacuous.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
