# refinement.md — django__django-15863

One changed coercion site, one Lean triple. Tags: **R** type-refinement,
**A-consumed** proof uses axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

## Site — `implementation_coerceDecimal` ↔ the `text → Decimal d` coercion (defaultfilters.py:153-159)

patch.diff hunk:
```
     try:
-        input_val = repr(text)
+        input_val = str(text)
         d = Decimal(input_val)
     except InvalidOperation:
         try:
             d = Decimal(str(float(text)))
         except (ValueError, InvalidOperation, TypeError):
             return ""
```

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `let primaryReadSucceeds : Bool := true` | `input_val = str(text); d = Decimal(input_val)` does not raise `InvalidOperation` for a finite Decimal `text` (post-patch behavior) | R (`str(text)` is a valid Decimal literal ⇒ the `try` arm succeeds ⇔ `primaryReadSucceeds = true`) |
| `if primaryReadSucceeds then return text` | `d = Decimal(str(text))` recovers the exact value of `text` | R (`Decimal(str(text)) == text` for a finite Decimal ↔ `result = text`; exact-rational denotation) |
| `return floatFallback text` (fallback arm) | `d = Decimal(str(float(text)))` | A-consumed (`floatFallback`: lossy binary64 round-trip; the proof consumes only that this arm is unreachable for the modeled input, never a value claim about it) |

The post-patch primary read always succeeds for the modeled input (finite
Decimal), so the working decimal equals the input value exactly and the fallback
is dead — the `floatFallback` opaque is present so the impl skeleton keeps the
real two-stage control flow, but its value is never observed on the live path.

## Axioms

`floatFallback` is declared `opaque` with **no** `_prop` axiom: the proof needs
nothing about its result value (the post-patch primary branch is always taken).
It is A-consumed in the sense that the proof relies on the structural fact that
the fallback branch is not reached, not on any property of the callee's output.
G-AX therefore has no callee property to validate → `axiom_check.py` is a skip
stub. The single R/I leg (primary branch returns `text` exactly) is validated by
G-CONF against the real patched `floatformat` coercion.

`conf_skip = false` (the impl has an R/I leg to differential-test).

## How the spec sees the bug (G-DIFF)

The discriminator is an exact Decimal whose value cannot be represented in
binary64 — e.g. `Decimal("123456.123456789012345678901")` (the F2P case, 21
fractional digits).

- `Solution.lean` (post-patch): the primary read succeeds
  (`primaryReadSucceeds = true`), so `result = text` exactly; `correct_coerceDecimal`
  closes.
- `Solution_prepatch.lean` (pre-patch, `input_val = repr(text)`): for a Decimal,
  `repr(text)` is `"Decimal('…')"`, never a valid Decimal literal, so the primary
  read fails (`primaryReadSucceeds = false`) and the value is forced through
  `floatFallback`. The spec demands `result = text`, but the skeleton returns
  `floatFallback text`, leaving the goal `floatFallback text = text` unprovable
  (no value property is assumed of the lossy fallback) — exactly the dropped
  precision in the F2P assertion
  `floatformat(Decimal("123456.123456789012345678901"), 21) == "123456.123456789012345678901"`.

## Design altitude (why `result = text`, why a boolean branch constant)

The changed operation is a string-rendering choice (`repr(text)` vs `str(text)`)
that decides whether the primary `Decimal(...)` read parses. Two routes were
considered for tying G-DIFF to that decision:

1. *Deep-model* `render`/`parseDecimal` over decimal string syntax. Rejected:
   it requires encoding Python's `Decimal('…')` repr wrapper and a parse grammar
   into the spec view — i.e. narrating the bug→fix MECHANISM, which directive 6
   forbids — and it is a heavy formalization of arbitrary-precision decimal I/O.
2. *Axiomatize* `parseDecimal (render text)`. Rejected: that axiom would be a
   property of the operation the patch CHANGED, which directive 7 forbids.

So the modeled behavior is the abstract contract the fix establishes — exact
value preservation — pinned structurally on the actual input carrier
(`result = text`, grounded per directive 8, framed per directive 5). The
two-stage `if primaryReadSucceeds then … else floatFallback …` skeleton mirrors
the patch's try/except control flow; the branch constant is FAITHFUL, not
degenerate: for the modeled input domain (finite Decimals) the post-patch primary
read always succeeds (`true`) and the pre-patch one always fails (`false`).
`verify ⟹ resolved` holds tightly — the only way to prove `result = text` is to
return the exact value, and any such impl refines to a patch whose working
decimal `d` equals the input exactly, which is exactly what the F2P assertion
checks.

## Domain

`text : Rat` models a FINITE (non-NaN, non-infinite) `Decimal` value via its
exact-rational denotation (mapping.md). The theorem quantifies over all `Rat`
(the identity impl satisfies the spec for every rational, so no precondition is
needed); the conformance check restricts fuzzing to genuine finite decimals,
which are the only inputs the issue and the F2P case concern. Decimal specials
(NaN/∞) and the locale/grouping/precision-suffix branches are outside the modeled
coercion step and unchanged by the patch.

PASS_TO_PASS is preserved: for float / short-Decimal / NaN / infinity inputs the
final rendered string is unchanged because those values survive the binary64
round-trip (or the integer / non-finite branches handle them), so only the
exact-high-precision-Decimal behavior is newly pinned.
