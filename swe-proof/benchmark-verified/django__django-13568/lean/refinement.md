# refinement.md — operation correspondence (django__django-13568)

Maps every op in `implementation_checkUserModel` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python (`check_user_model`) accumulates a list of system-check
diagnostics from several independent sub-checks, in source order:
required-fields-shape (E001), required-fields-membership (E002), login-field
uniqueness (E003 / W004), then the two anonymous / authenticated attribute
checks (C009 / C010). The patch changes ONLY the guard of the uniqueness
sub-check: pre-patch it fired whenever the field's own `unique` flag was false;
post-patch it ALSO requires that no unconditional unique constraint ranges over
exactly the login field.

| # | Lean impl op | patch.diff / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if reqFieldsBadShape then errors := errors ++ ["auth.E001"]` | `if not isinstance(cls.REQUIRED_FIELDS, (list, tuple)): errors.append(Error(..., id='auth.E001'))` | R | the `isinstance` outcome ↔ `Bool` (mapping.md). UNCHANGED sub-check; only its result is consumed. |
| 2 | `if usernameInRequired then errors := errors ++ ["auth.E002"]` | `if cls.USERNAME_FIELD in cls.REQUIRED_FIELDS: errors.append(Error(..., id='auth.E002'))` | R | the membership outcome ↔ `Bool`. UNCHANGED sub-check. |
| 3 | `if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then …` | `if not cls._meta.get_field(cls.USERNAME_FIELD).unique and not any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints):` | R + I | the CHANGED op. `…get_field(USERNAME_FIELD).unique` outcome ↔ `fieldUnique : Bool` (R, UNCHANGED first conjunct). The added second conjunct `not any(constraint.fields == (USERNAME_FIELD,) for constraint in total_unique_constraints)` is modeled DEEPLY as `!coveredByUnconditionalUniqueConstraint` (I): `total_unique_constraints` filters the declared constraints to the unconditional uniqueness ones (`isUnique && !isConditional`, see mapping.md), and `constraint.fields == (USERNAME_FIELD,)` is `c.fields == [usernameField]`. Spelled out concretely, delegating to no opaque callee. |
| 4 | `if usesDefaultBackend then errors := errors ++ ["auth.E003"] else errors := errors ++ ["auth.W004"]` | `if settings.AUTHENTICATION_BACKENDS == ['django.contrib.auth.backends.ModelBackend']: errors.append(Error(id='auth.E003')) else: errors.append(Warning(id='auth.W004'))` | R | the backend-equality outcome ↔ `usesDefaultBackend : Bool`. UNCHANGED severity selection inside the (now-guarded) branch. |
| 5 | `if isAnonymousMethod then errors := errors ++ ["auth.C009"]` | `if isinstance(cls().is_anonymous, MethodType): errors.append(Critical(id='auth.C009'))` | R | the `isinstance(..., MethodType)` outcome ↔ `Bool`. UNCHANGED sub-check. |
| 6 | `if isAuthenticatedMethod then errors := errors ++ ["auth.C010"]` | `if isinstance(cls().is_authenticated, MethodType): errors.append(Critical(id='auth.C010'))` | R | the `isinstance(..., MethodType)` outcome ↔ `Bool`. UNCHANGED sub-check. |

No A-consumed rows: the proof discharges the spec by case-splitting the booleans
and unfolding the deeply-modeled `coveredByUnconditionalUniqueConstraint`; no
UNCHANGED callee property is assumed (axioms region empty; `axiom_check.py` is a
skip stub). No A-reference rows: the changed op does not delegate to an opaque
real callee — `total_unique_constraints` + the tuple comparison is the filter
itself, spelled out concretely over the `ConstraintInfo` carrier (I-tagged), so
G-CONF (not G-AX) validates it. No changed-inexpressible op.

The discriminating clause is row 3: the added constraint guard. The prepatch
impl drops `coveredByUnconditionalUniqueConstraint` (it fires the uniqueness
diagnostic on `!fieldUnique` alone), so its `correct_checkUserModel` cannot close
against the frozen `problem_spec_checkUserModel` — on a model with a login field
that is not directly unique but IS covered by an unconditional unique constraint
over exactly that field, the spec demands no E003/W004 while the buggy impl emits
one. That is the G-DIFF signal and matches the F2P test
`test_username_unique_with_model_constraint`.

Each `checks.Error` / `checks.Warning` / `checks.Critical` is represented by its
stable `id` code string (`obj=` framing fields are unchanged and identical
across the branches, so not modeled — mapping.md). The accumulator
`errors.append(...)` in source order ↔ `errors := errors ++ [...]` in the
`Id.run do` loop.
