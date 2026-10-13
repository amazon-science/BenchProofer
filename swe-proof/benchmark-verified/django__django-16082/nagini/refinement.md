# refinement.md — django__django-16082

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_combined_type` impl region + the deep `is_subtype` / `is_int_kind`
/ `is_date_kind` / `row` spec) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. What the gold patch changes

Gold hunk (`django/db/models/expressions.py`, in the **"Numeric operations -
operands of different type"** dict's connector tuple):
```
             Combinable.SUB,
             Combinable.MUL,
             Combinable.DIV,
+            Combinable.MOD,
         )
```

This registers the four mixed-type numeric rows — `(Integer, Decimal)->Decimal`,
`(Decimal, Integer)->Decimal`, `(Integer, Float)->Float`, `(Float, Integer)->
Float` — for the remainder connector `Combinable.MOD`, which previously had only
the same-type and with-NULL rows. Concretely it changes the contents of the
module-level registry `_connector_combinators[Combinable.MOD]`, which
`_resolve_combined_type` scans. There is no control-flow change — the scan loop
(`expressions.py:623-628`) is untouched; only the data it scans changes.

## B. model.py impl ↔ patch.diff

| # | model.py impl op (`resolve_combined_type`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | params `connector, lhs_type, rhs_type : int` | `_resolve_combined_type(connector, lhs_type, rhs_type)` (`expressions.py:621`) | R | connector string ↔ int code (every connector the registry is keyed by, plus codes standing for keys it has no entry for); field class ↔ int code, with the family below the integer field type carried by an OPEN band of codes and the classes below no recorded operand type by a second open band (mapping.md §2). |
| B2 | the family-grouped straight-line cascade of `row(clhs, crhs, lhs_type, rhs_type)` tests — the numeric same-type rows, then the numeric mixed-type rows, then the numeric-with-null rows, then the bitwise row, then the date/time rows recorded under addition and under subtraction — returning the recorded result type of the first that holds | `combinators = _connector_combinators.get(connector, ())` then `for (clhs, crhs, combined) in combinators: if issubclass(lhs_type, clhs) and issubclass(rhs_type, crhs): return combined` (`expressions.py:623-628`) | A-reference | the changed thing is the registry **data** for `Combinable.MOD`. It is modeled **deeply**: the cascade IS the recorded rows, per connector family, in registration order, with the mixed rows present for the remainder connector (the post-patch state). There is no consumed axiom about the registry; instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) drives the real `_resolve_combined_type` over every registered connector plus unregistered connector codes × the whole discovered field-class domain squared — 9375 observations at this commit — and asserts equality with this cascade (mapping.md §3.2). Returning the first matching row ⇔ the loop's first `return combined`. |
| B3 | each `row(c_l, c_r, lhs, rhs)` ≡ `is_subtype(lhs, c_l) and is_subtype(rhs, c_r)`, where `is_subtype(a, b)` is `is_int_kind(a)` when `b` is the integer type, `is_date_kind(a)` when `b` is the date type, and identity otherwise | `issubclass(lhs_type, combinator_lhs_type) and issubclass(rhs_type, combinator_rhs_type)` (`expressions.py:625-627`) | A-reference | the subtype test is an UNCHANGED primitive (`issubclass`); modeled deeply as `is_subtype`, whose integer arm ranges over an UNBOUNDED band of codes rather than a finite list of named narrower types, and whose date arm covers the date-time type. Validated `is_subtype == issubclass` by G-AX over every (discovered class, recorded class) pair — 200 pairs at this commit, spanning all 9 real members of the family below the integer field type (mapping.md §3.1). G-AX does not assume that hierarchy: it walks `Field.__subclasses__()` and asserts the family the carrier claims is the family the repo really has. |
| B4 | fall-through `return T_NONE` | `_resolve_combined_type` implicitly returns `None` after the loop finds no match | R | `None` ↔ `T_NONE = 0` (mapping.md §2); the F2P with-null/failure tests observe the `None`→`FieldError` path. |

## C. Why the deep model, not a consumed axiom

The operation the patch *changes* is the registry contents for `Combinable.MOD`.
Per SPEC_GUIDE §3, a changed operation is modeled **deeply**, never hidden
behind a `@ContractOnly` axiom of the function under change. So the whole
recorded-row cascade is spelled out in the impl, and the postconditions pin the
resolution outcomes directly. The only callees the deep model rests on —
`issubclass` and the registry-building helpers — are **unchanged** by the patch;
they are **A-reference** deep-model checks (G-AX), not consumed axioms. There is
no `@ContractOnly` in `model.py`, hence no A-consumed row and no dead axiom.

## D. The discriminating clause (G-DIFF)

The behaviour the issue + F2P demand: for the remainder connector, MIXED numeric
operands resolve to the wider type (integer-kind/decimal → decimal,
integer-kind/float → float), exactly as the other arithmetic connectors already
did. In `model.py` this lives in the four mixed-numeric postconditions, e.g.

```
Ensures(Implies(records_mixed_numeric(connector)
                and is_int_kind(lhs_type) and rhs_type == T_DEC,
                Result() == T_DEC))
```

which hold for every connector that records the mixed rows, the remainder
connector included, and — because the antecedent is `is_int_kind(lhs_type)`, a
predicate over the whole OPEN band — for every field type below the integer type,
not merely for the integer type itself and one named narrower alias.

The postconditions do not stop at the four mixed cells. They pin the result at
EVERY point of the (unbounded) precondition domain:

* **Totality.** `has_permitted_combination(connector, lhs_type, rhs_type) ==
  (Result() != T_NONE)` — the sentinel is returned exactly when no recorded row
  matches. This is a biconditional over the whole open domain, so an
  implementation cannot be silent anywhere: every admissible query is forced
  either to a specific type by the family clauses below or to the sentinel.
* **Result containment.** `is_result_type(Result())` — the result is one of the
  types the registry actually records as a combined type, or the sentinel. In
  particular the result can never be an echo of an operand's own code, which is
  what distinguishes "resolve via the recorded rows" from "compute a width".
* **Per-family clauses**, each quantified over the open bands where the real
  matching is by subtype: same-type numeric (integer-kind × integer-kind → the
  integer type, i.e. the recorded result type, NOT the narrower operand type);
  mixed numeric → the wider type for all five arithmetic connectors; the
  decimal/float mixes → the sentinel (no widening between them is recorded);
  exponentiation records the same-type and with-null rows but NOT the mixed rows;
  the null-literal type combines only with the float type; the five bitwise
  connectors resolve two integer-kind operands to the integer type and everything
  else to the sentinel; the asymmetry between the date/time rows recorded under
  addition and under subtraction; operands below no recorded operand type resolve
  to the sentinel; connector codes the registry has no entry for resolve to the
  sentinel.

Because the domain is OPEN on both axes — an unbounded band of field-type codes
below the integer type, and an unrestricted connector code — no finite
normalization table and no connector allowlist can discharge these clauses. An
implementation that folded the narrower integer codes onto the integer code by
exact enumeration, or that returned the sentinel outside the arithmetic
connectors, leaves points of the domain where the postconditions are violated.
Every clause is validated against the real post-patch callee by G-AX's exhaustive
run over the same domain, so none of them is an invention of the model.

`model_prepatch.py` reproduces the pre-patch registry construction: the four
mixed rows are recorded only when the connector is not the remainder connector.
It shares the spec byte-for-byte and **fails** verification — for a remainder-
connector query with integer-kind/decimal operands the prepatch cascade skips the
mixed rows and returns the sentinel, so both the totality biconditional and the
mixed-numeric clause are violated. That is exactly the spec sensing the change
(G-DIFF), and exactly the bug `test_resolve_output_field_number` exercises once
it iterates `Combinable.MOD`.

A single `model_prepatch.py` suffices: the patch fixes one behavior (mixed
numeric resolution under the remainder connector); the same-type and with-NULL
MOD rows were already present pre-patch, so they are not part of the fix and need
no separate failing variant.

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely *changed*
— the registry rows for the remainder connector — is modeled **deeply** (the
spelled-out family-grouped cascade, B2), validated == the real registry by G-AX,
not hidden behind an axiom about the function under change. The unchanged
primitives (`issubclass`, registry construction) are A-references, also
G-AX-validated.

## F. verify(model) ⇒ resolved

`resolve_combined_type` verifies only if, at every point of the open domain, its
result is exactly the recorded result type of the first matching row and the
sentinel where no row matches (the totality biconditional plus the per-family
clauses). By R (connector string ↔ code, field class ↔ code with open bands,
`None` ↔ `T_NONE`) and the A-reference validations (G-AX: `is_subtype ==
issubclass` over the discovered hierarchy; cascade == real
`_resolve_combined_type` over every registered connector plus unregistered codes
× the whole field-class domain squared), the verified resolver equals the real
post-patch `_resolve_combined_type` on every input the repo can present it with —
including the narrower integer field classes the P2P suite drives it with (a
model field declared as a positive integer field, combined with another operand,
must still resolve, and must resolve to the recorded integer type). The gold
patch is precisely what makes the real `_resolve_combined_type` exhibit the mixed
behaviour for `Combinable.MOD`, and the gold patch resolves (G-RESOLVE).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and G-AX-validated callees. The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
