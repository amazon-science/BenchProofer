# refinement.md — django__django-15368

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_wrap_flags` impl region and the deep `wrap_flags` fold) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`Ensures`, **A-reference** where a deep model is validated == a real callee /
real fact by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The classification site — `QuerySet.bulk_update` inner loop (`django/db/models/query.py:671-675`)

Gold hunk (the load-bearing one):
```
  for obj in batch_objs:
      attr = getattr(obj, field.attname)
-     if not isinstance(attr, Expression):
+     if not hasattr(attr, 'resolve_expression'):
          attr = Value(attr, output_field=field)
      when_statements.append(When(pk=obj.pk, then=attr))
```
(plus the companion hunk removing the now-unused `Expression` from the import
at `query.py:20` — a no-op for behaviour; see §C.)

| # | model.py impl op (`build_wrap_flags`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | iterate `i` over the per-object positions of the batch (the backward `while i > 0` loop) | `for obj in batch_objs:` | R | the batch's objects ↔ positions `0..len-1`; one loop iteration per object (mapping.md §2). Order is preserved; the backward walk is the standard front-recursive-fold pairing and is observationally the same multiset/order of decisions. |
| A2 | read `attr_resolvable = resolvable[i-1]` | `attr = getattr(obj, field.attname)` then form the predicate `hasattr(attr, 'resolve_expression')` | R | the model carries the only observed fact about `attr` directly as the boolean `resolvable[i]` = `hasattr(attr, 'resolve_expression')` (mapping.md §2). The other observable, `in_family[i]` = `isinstance(attr, Expression)`, is carried in parallel but unused by the fixed code. |
| A3 | decision `if not attr_resolvable: result = [True] + result else: result = [False] + result`, i.e. wrap-as-literal iff NOT resolvable | `if not hasattr(attr, 'resolve_expression'): attr = Value(attr, output_field=field)` | I (under R of A2) | identical boolean test on the same observed bit: "wrap iff not resolvable". `True`/`False` in the result list ↔ "wrapped in `Value`" / "carried through" (mapping.md §2). |
| A4 | the wrap decision is the produced element; `wrap_flags(ToSeq(resolvable))` is the whole-batch result | `when_statements.append(When(pk=obj.pk, then=attr))` — `attr` is either the wrapped `Value` or the original value | R | the model abstracts `When(...)`/`Case(...)`/`Cast(...)` downstream to identity (mapping.md §2); the only behaviour that changed is which `then=` value (wrapped vs original) each object contributes, captured exactly by the per-object boolean. |

The discriminating content of the change lives in step A3 paired with the
type-hierarchy precondition (§B): the predicate switches from `in_family`
(`isinstance(Expression)`) to `resolvable` (`hasattr(resolve_expression)`). For
a value with `in_family = False, resolvable = True` — an `F('...')` — the old
predicate wraps it as a literal (`Value(F(...))`, rendered as the string
`'F(note)'`) while the new predicate carries it through to resolve to the
column. `model_prepatch.py` reproduces the old predicate (`not in_family[i-1]`)
and **fails** the loop invariant
`ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i))` — exactly the spec
sensing the change (G-DIFF), on the apostrophe-analogue discriminating input.

## B. The type-hierarchy fact (A-reference, NOT A-consumed)

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | precondition / loop invariant `in_family[i] ==> resolvable[i]` | the unchanged class hierarchy `Expression` ⊂ {has `resolve_expression`} that both predicates observe | A-reference | this is a fact about an **unchanged** callee surface (`isinstance`/`hasattr` over Django's expression classes), modelled as an input constraint, not a `@ContractOnly` the proof consumes. It is validated against the real classes by `axiom_check.py` (G-AX): every `Expression`/`Value`/`Col` instance is resolvable; an `F` is resolvable but not an `Expression` (converse fails), so `hasattr(resolve_expression)` is a strict superset of `isinstance(Expression)` — which is precisely why the fix is correct and the old check too narrow. The proof never derives the result from this fact (the result depends only on `resolvable`); it is present so the prepatch's `in_family`-based impl is well-formed and fails on the postcondition rather than on a permission. |

There is **no consumed (`A-consumed`) axiom** in this bundle: the changed
operation — the classification predicate — is modelled **deeply** (the spelled-
out per-object decision in `wrap_flags` and the verified loop), and the only
external fact (the class hierarchy) is an A-reference checked by G-AX.

## C. The import hunk (`django/db/models/query.py:20`)

```
- from django.db.models.expressions import Case, Expression, F, Ref, Value, When
+ from django.db.models.expressions import Case, F, Ref, Value, When
```
Tag **I** (no-op): removing the now-unused `Expression` name has no runtime
behaviour; it is a hygiene change paired with A3 (the only remaining use of
`Expression` was the predicate A3 replaces). Not modelled (nothing observable).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the classification predicate (`isinstance(Expression)` →
`hasattr(resolve_expression)`) — is modelled **deeply** as the boolean decision
`wrap iff not resolvable` (step A3, consumed in `build_wrap_flags`), not hidden
behind an axiom about the function under change. The only external fact, the
class hierarchy, is the **A-reference** that G-AX validates the model against.

## E. verify(model) ⇒ resolved

`build_wrap_flags` verifies only if its output equals the per-object decision
"wrap as a literal iff NOT resolvable" (A3, the postcondition
`ToSeq(Result()) == wrap_flags(ToSeq(resolvable))`). By R (object ↔ the two
observed booleans; `When`/`Case`/`Cast` identity downstream) the verified
decision equals the fixed `bulk_update` inner loop on every batch. By G-AX the
type-hierarchy A-reference holds of the real Django classes, so a value with
`resolvable = True, in_family = False` (an `F`) is carried through unwrapped by
any spec-satisfying impl — which is exactly the F2P observation
(`test_f_expression`: `F('note')` resolves to the `note` column instead of
storing the literal `'F(note)'`). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited hierarchy fact — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
