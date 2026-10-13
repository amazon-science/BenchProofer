# refinement.md — django__django-13568

The operation-by-operation correspondence between `model.py`'s implementation
(the `username_field_diagnostic` impl region and the deep `any_covers` / `covers`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == a real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed guard — `check_user_model` (`django/contrib/auth/checks.py:55`)

Gold hunk:
```
- if not cls._meta.get_field(cls.USERNAME_FIELD).unique:
+ if not cls._meta.get_field(cls.USERNAME_FIELD).unique and not any(
+     constraint.fields == (cls.USERNAME_FIELD,)
+     for constraint in cls._meta.total_unique_constraints
+ ):
      ... append auth.E003 (default backend) / auth.W004 (otherwise) ...
```

The diagnostic is emitted exactly when the guard is true, i.e. when
`not field_unique AND not any(constraint covers USERNAME_FIELD)`. Equivalently,
NO diagnostic is emitted iff `field_unique OR any(...)`. The model's
`username_field_diagnostic` computes that decision and the severity.

| # | model.py impl op (`username_field_diagnostic`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `field_unique` (param read) | `cls._meta.get_field(cls.USERNAME_FIELD).unique` | R | the field's `bool` `.unique` attribute ↔ the `field_unique` bool (mapping.md §2); identity on the value. |
| A2 | `satisfied = field_unique` | the first conjunct `cls…unique` of the guard (negated in the guard, used positively here) | I | same boolean; the guard `not unique and not any(...)` is the negation of `unique or any(...)`. |
| A3 | the loop computing `found == any_covers(ToSeq(c_span), ToSeq(c_single), ToSeq(c_total), username_field)`, with `covers(sp,sg,tt,f) := tt==1 and sp==1 and sg==f` | `any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)` | R + I | **deep model.** `any_covers` is the spelled-out existential over the constraint list; the per-element test `c_span[k]==1 and c_single[k]==username_field` (with `c_total[k]==1`) is the type-refinement (R) of `constraint.fields == (cls.USERNAME_FIELD,)` (a 1-tuple equality on the unconditional constraints) — see mapping.md §2 for the `tuple`↔`(span,single)` and `condition is None`↔`total==1` bijections. The control flow (existential over the list, short-circuit OR) is identical (I) to Python's `any(...)`. No axiom is consumed: the search is fully expressible. |
| A4 | `satisfied = field_unique or found` (the two branches combine to this) | `field_unique or any(...)` = negation of the guard | I | boolean OR; the `if not satisfied:` short-circuit mirrors Python's lazy `and`/`any`. |
| A5 | `if satisfied: return NO_DIAGNOSTIC` | when the guard is false the `if`-body is skipped and nothing is appended | R | "no constraint appended" ↔ outcome code `0`; the F2P asserts the error list is empty here (mapping.md §2). |
| A6 | `if default_regime: return HARD_ERROR else: return WARNING` | inside the guard body: `if settings.AUTHENTICATION_BACKENDS == ['…ModelBackend']:` append `checks.Error(id='auth.E003')` `else:` append `checks.Warning(id='auth.W004')` | R | `default_regime` bool ↔ the backend-list equality (mapping.md §2); `HARD_ERROR(1)`↔`auth.E003`, `WARNING(2)`↔`auth.W004` (the `id` the F2P asserts). |

## B. The `total_unique_constraints` projection (input provenance)

The patch iterates `cls._meta.total_unique_constraints`, which is itself
`[c for c in cls._meta.constraints if isinstance(c, UniqueConstraint) and c.condition is None]`
(`django/db/models/options.py:837-841`). The model receives the constraint list
already as records but carries `c_total[k]` (unconditionality) **explicitly**, and
`covers` requires `c_total[k]==1`. This is a faithful refinement, not a weakening:
a conditional `UniqueConstraint` is absent from `total_unique_constraints` in the
repo, and in the model it has `c_total[k]==0` so `covers` is false — the same
observable effect (the constraint does not discharge the obligation). Modeling the
condition filter explicitly makes the **partial-constraint** behaviour a
first-class part of the spec rather than an opaque input pre-filter, so the spec
itself senses it.

## C. No kind-3 (unexpressible-changed-op) steps; no consumed/reference axioms

Every step above is R or I. The one operation the patch *introduces* — the
existential constraint search — is fully expressible (booleans, integer equality,
a list traversal) and is modeled **deeply** as `any_covers`/`covers` + the
verified loop; it is NOT hidden behind an axiom. The `axioms` region is therefore
empty: there is no A-consumed axiom and no A-reference deep-model-of-a-callee.
`axiom_check.py` independently confirms (against real Django) that the deep
predicate matches `UniqueConstraint` tuple-equality + `total_unique_constraints`
condition-filtering semantics, so the abstraction in mapping.md §2 is sound.

## D. The differential witness (G-DIFF)

`model_prepatch.py` keeps the spec byte-identical and reverts the impl to the
pre-patch skeleton: `satisfied = field_unique` only — the constraint list is never
consulted (the gold's *added* conjunct is removed). It **fails** the postcondition

```
Implies(field_unique or any_covers(...), Result() == NO_DIAGNOSTIC)
```

on exactly the discriminating input class: `field_unique == False` but a covering
unconditional single-field constraint exists (`any_covers` true). There the
pre-patch returns a diagnostic (`HARD_ERROR`/`WARNING`) while the spec requires
`NO_DIAGNOSTIC`. This is precisely the F2P
`test_username_unique_with_model_constraint` (an unconditional
`UniqueConstraint(fields=['username'])` ⇒ the check must produce no errors), and
the partial case `test_username_partially_unique` (a conditional constraint ⇒
`c_total==0` ⇒ still diagnostic) is sensed by the same `covers` definition.

## E. verify(model) ⇒ resolved

`username_field_diagnostic` verifies only if it returns `NO_DIAGNOSTIC` exactly
when `field_unique or any_covers(...)` and the regime-correct code otherwise (A2,
A3, A5, A6). By R (str↔int field codes, `tuple`↔`(span,single)`,
`condition is None`↔`total==1`, the diagnostic-code abstraction) the verified
decision equals the gold guard `not unique and not any(constraint.fields ==
(USERNAME_FIELD,) for constraint in total_unique_constraints)` and its
Error/Warning bodies on the tested inputs. The gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this document, G-EQ); there is no
axiom trust point for this instance.
