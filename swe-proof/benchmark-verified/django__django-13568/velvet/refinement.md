# refinement.md — django__django-13568

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`usernameUniquenessVerdict` `do` block, plus the deep `totalUnique`/`coversField`
model it reads) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The uniqueness-check site — `check_user_model` (`django/contrib/auth/checks.py:54-77`)

Gold hunk:
```
- if not cls._meta.get_field(cls.USERNAME_FIELD).unique:
+ if not cls._meta.get_field(cls.USERNAME_FIELD).unique and not any(
+     constraint.fields == (cls.USERNAME_FIELD,)
+     for constraint in cls._meta.total_unique_constraints
+ ):
      if settings.AUTHENTICATION_BACKENDS == ['…ModelBackend']:
          errors.append(checks.Error(… id='auth.E003'))
      else:
          errors.append(checks.Warning(… id='auth.W004'))
```

| # | Solution.lean impl op (`usernameUniquenessVerdict`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `fieldUnique : Bool` | `cls._meta.get_field(cls.USERNAME_FIELD).unique` | R | Python `bool` ↔ Lean `Bool` (mapping.md §2). |
| A2 | param `constraints : List Constraint` | `cls._meta.constraints` (the model's declared constraints) | R | each constraint ↔ `{fields, isUnique, conditional}` (mapping.md §2). |
| A3 | param `usernameField : String` | `cls.USERNAME_FIELD` | R | field-name `str` ↔ `String`. |
| A4 | param `defaultBackendOnly : Bool` | `settings.AUTHENTICATION_BACKENDS == ['…ModelBackend']` | R | the only-default-backend predicate ↔ `Bool` (mapping.md §2). |
| A5 | `covered := (totalUnique constraints).any (· == [usernameField])` | the added conjunct `any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)` | A-reference + I | the metadata accessor `total_unique_constraints` (UNCHANGED) is modeled **deeply** by `totalUnique`; its field-tuple projection equals the real accessor (the **A-reference**, G-AX). The `.any (· == [usernameField])` membership test and the `(USERNAME_FIELD,)` ↔ `[usernameField]` length-one comparison are **I** (concrete, transliterated by G-CONF). mapping.md §3.1. |
| A6 | `if !fieldUnique && !covered then …` | `if not …unique and not any(…):` | I | the conjunction of the original guard with the new `not any(...)` conjunct, transliterated verbatim. |
| A7 | inner `if defaultBackendOnly then Verdict.error else Verdict.warning` | `if AUTHENTICATION_BACKENDS == [...]: Error(E003) else: Warning(W004)` | R + I | the severity split; `Error(id='auth.E003')` ↔ `Verdict.error`, `Warning(id='auth.W004')` ↔ `Verdict.warning` (mapping.md §2). |
| A8 | `else Verdict.ok` | no message appended | R | the acceptable branch emits nothing ↔ `Verdict.ok`. |

Discriminating content of the change — a field that is NOT declared
`unique=True` but IS covered by an unconditional single-field uniqueness
constraint must be **acquitted** (`Verdict.ok`), where pre-patch it was reported
(`auth.E003`/`auth.W004`). That lives in the `!coversField …` conjunct of the
post-condition. `Solution_prepatch.lean` drops the conjunct (consulting only
`fieldUnique`) and **fails** the post-condition on exactly the covered case
(G-DIFF); G-CONF confirms the shadow agrees with the patched oracle and diverges
from the unpatched one on precisely those cases.

## B. The deep-model reference — `total_unique_constraints`

Gold patch reads `cls._meta.total_unique_constraints` (`options.py:831-841`), an
UNCHANGED `@cached_property` returning the unconditional `UniqueConstraint`s.
Modeled deeply by `totalUnique` (front-recursive, keeps `c.fields` iff
`c.isUnique && !c.conditional`).

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `totalUnique` (pure region) + its `@[grind]` lemmas | `_meta.total_unique_constraints` (the comprehension over `constraints`) | A-reference | the deep model's field projection == the real accessor; validated by axiom_check.py over boundary + 4000 fuzz constraint lists (G-AX). NOT a consumed axiom — no `axiom` the proof uses. mapping.md §3.1. |

No separate failing prepatch for the accessor: it is unchanged by the gold patch
(only a caller is added). Its soundness is audited by G-AX; the changed *caller*
behavior is exercised by site-A's prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — adding the
"field is covered by a total uniqueness constraint" acquittal to the guard — is
modeled **directly** (`coversField` over the deep `totalUnique`, step A5, an
A-reference + I), not hidden behind an axiom about the function under change.
There is no consumed axiom: the unchanged accessor `total_unique_constraints` is
an A-reference (deep model, G-AX-validated), and everything else is computed from
the inputs.

## D. verify(Solution) ⇒ resolved

`usernameUniquenessVerdict` verifies only if its output equals the exact
three-valued decision: report (error/warning by backend) iff the field is neither
self-unique NOR covered by a total uniqueness constraint over exactly that field;
otherwise `ok` (A5–A8). By R (`bool`/`str`/tuple identities, the
`(uf,) ↔ [uf]` length-one comparison) the verified verdict equals the patched
`check_user_model`'s emitted message on the tested inputs; by G-AX the deep model
`totalUnique` equals the real `total_unique_constraints` accessor (A-reference);
by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on
≥10⁵ inputs (and diverges from the pre-patch behaviour on exactly the
constraint-covered cases). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited accessor — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: the A-reference soundness (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
