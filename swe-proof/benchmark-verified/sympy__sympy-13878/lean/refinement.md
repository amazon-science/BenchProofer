# refinement.md — sympy__sympy-13878

Maps every op in `implementation_arcsinCdf` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed**, **A-reference**, **I** (identical).

`patch.diff` adds `ArcsinDistribution._cdf` (`crv_types.py:157`–`163`):

```python
def _cdf(self, x):
    from sympy import asin
    a, b = self.a, self.b
    return Piecewise(
        (S.Zero, x < a),
        (2*asin(sqrt((x - a)/(b - a)))/pi, x <= b),
        (S.One, True))
```

The impl builds the ORDERED case list the method submits, then hands it to the
carrier's case-split constructor. So the rows below are the three submitted
cases plus the submission itself.

The impl is written under `{T : Type} [Term T]`: it receives its operands as
elements of an arbitrary carrier of the term signature (mapping.md §2) and the
only thing it can do with them is apply the signature's operations. Each row
below is one such application, so the row-by-row correspondence covers the whole
impl and nothing in it is left to interpretation — see mapping.md §2.1 for what
falls OUTSIDE the correspondence and how such an implementation reads.

| # | Lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `cs ++ [{value := Term.lit 0, guard := Term.lt x a}]` | `(S.Zero, x < a)` | R | `Term.lit 0` ↔ `S.Zero`; `Term.lt x a` ↔ the STRICT relational `x < a`. Position 0 of the list, and the position is part of the answer. |
| 2 | `cs ++ [{value := arcsinProfile a b x, guard := Term.le x b}]` | `(2*asin(sqrt((x-a)/(b-a)))/pi, x <= b)` | R | `arcsinProfile` spells the value out node for node: `Term.arcsin`↔`asin`, `Term.sqrt`↔`sqrt`, `Term.pi`↔`pi`, `Term.div/mul/sub`↔ the sympy arithmetic. `Term.le x b` ↔ the NON-STRICT relational `x <= b`. Position 1. |
| 3 | `cs ++ [{value := Term.lit 1, guard := Term.always}]` | `(S.One, True)` | R | `Term.lit 1` ↔ `S.One`; `Term.always` ↔ `BooleanTrue`. Position 2, the fall-through. |
| 4 | `return CdfObject.caseSplit cs` | `Piecewise(...)` — the constructor call itself | A-reference | The algebra layer's case-split constructor (`piecewise.py:145`, `Piecewise.eval`) is UNCHANGED by the patch and is not the behavior under spec. `CdfObject.caseSplit` denotes "the object assembled from this list", so the model claims only what the real constructor honors: the list it is handed. Validated as the composition `_cdf(x) == Piecewise(*shadow_cases)` by `conformance_check.py`, structurally, on free AND ground operands — not asserted as a Lean `axiom`, so there is nothing for G-AX (`skip`). |

No A-consumed rows: the method body calls only `asin`/`sqrt`/`pi` for its
values, all modeled deeply, and the one A-reference row above is validated
executably rather than axiomatized. The impl region is NOT all-A-tagged →
`conf_skip = false`, G-CONF runs.

## Why row 4 is A-reference and not a weakening

The constructor applies a second, whole-container pass over the list it is
handed (mapping.md §1, step 3): it canonicalises the relationals, drops cases
whose guards decide, truncates after a literally-true guard, and returns a bare
expression rather than a case split when one case is all that survives. Which of
those shapes is OBSERVED depends only on whether the operands settle the guards
— never on which values or cutoffs the submitted list chose. So abstracting the
constructor while pinning its ARGUMENT exactly is the postcondition stating what
the callee guarantees: every wrong list still produces a wrong answer, and the
model does not have to predict which of the constructor's shapes a given operand
kind yields. Modelling the pruning in Lean instead was the alternative; it would
add a large unchanged-code model without pinning anything the current form
leaves open, since `problem_spec_arcsinCdf` determines the submitted list
completely: its five clauses fix the answer's kind, the case count, and each
position's value and guard, so any two answers satisfying it agree (checked by
the ten reject cases in `properties.py`, which between them attack all five
clauses and are each machine-refuted by a witness).

## The discriminating clause

Rows 1–3 together are the discriminating content: the pre-patch state supplies
NO precomputed case list for this family, so the cumulative distribution is
computed by symbolic integration instead (`crv.py:196`–`209`, reached from
`crv.py:211`–`220` when `_cdf` returns `None`), yielding for this family the
unevaluated non-convergent integral the issue reports — modeled as
`CdfObject.accumulateUpTo`. `problem_spec_arcsinCdf` admits only
`CdfObject.caseSplit` (the reject cases `weak-no-case-analysis` and
`weak-collapse-to-bare` in `properties.py` refute the other two shapes at a
concrete carrier), so `Solution_prepatch.lean` cannot close the obligation: its
`return CdfObject.accumulateUpTo x` fails the first conjunct. That is the G-DIFF
signal.

Each of rows 1–3 is independently load-bearing, and the carrier records terms
precisely so that they are: a rival that keeps the right regions but flips the
upper cutoff from non-strict to strict, or reorders the cases, or drops one, is
the SAME function of a real evaluation point and a DIFFERENT answer. The scored
assertion compares whole expression trees, so those rivals do not resolve, and
the spec rejects each of them (checked: the strictness flip, the reorder, the
dropped case, and the bare collapse all fail to verify).

## Why the impl's operands are elements of an ARBITRARY carrier

The rows above are the whole of what the impl does, and that is a property of
HOW it is stated, not a description of a particular file. The signature has no
eliminator and no laws, so an impl under `[Term T]` cannot ask anything about the
operands it is handed — it can only assemble them — and therefore every impl that
closes the obligation submits the same list, position for position, at every
carrier and every triple.

That is the refinement claim this bundle needs, and it is stronger than "the
frozen impl assembles the right list". The real method's operands live in sympy's
expression layer, which is one carrier of this signature and an EVALUATING one:
it identifies `Integer(2)/Integer(2)` with `Integer(1)`, `2*x` with `x*2`, and
`x - 0` with `x`. An impl that could interrogate its operands would be able to
branch on an identity that layer settles one way and a Lean datatype of trees
settles the other, and then the branch taken in Lean and the branch taken in
Python would differ while the Lean obligation still closed — a transliteration
that verifies and does not resolve. Stating the operands at an arbitrary carrier
removes the ability rather than forbidding the use of it: there is no proposition
about a `T`-element for an impl to decide, so this shape cannot be written at all,
and the refinement of rows 1–3 into the method body is the only reading available.

mapping.md §2.1(b) records the one construction this does not reach — an impl that
declares its OWN carrier and decides something about an element of that — together
with the reading the correspondence gives it (the branch it selects, since a
private Lean type has no Python counterpart) and why that reading keeps
"verifies" ⇒ "resolves": such a guard cannot mention `a`, `b` or `x`, so it
selects one branch for every input, and the frozen obligation holds of whatever
that branch returns.
