# mapping.md — symbol binding & type bijection (django__django-13568)

## Modeled function
- **Lean** `implementation_checkUserModel :
  String → Bool → Bool → Bool → Bool → Bool → Bool → List ConstraintInfo → List String`
- **Python** `check_user_model(app_configs=None, **kwargs)`
  — `django/contrib/auth/checks.py:11-99 @ ede9fac758` (base_commit); patch hunk @52-66.

The function runs the user-model system checks and returns the accumulated list
of diagnostics (each a `checks.Error` / `Warning` / `Critical`). The patch
changes ONLY the guard on the login-field (`USERNAME_FIELD`) uniqueness
diagnostic: post-patch the diagnostic is skipped not only when the field's own
`unique` flag is set, but also when a *total* (unconditional) unique constraint
ranges over exactly that one field.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `cls.USERNAME_FIELD` (`str`) | `usernameField : String` | the configured login field name |
| `not isinstance(cls.REQUIRED_FIELDS, (list, tuple))` | `reqFieldsBadShape : Bool` | UNCHANGED sub-check (R) → E001 |
| `cls.USERNAME_FIELD in cls.REQUIRED_FIELDS` | `usernameInRequired : Bool` | UNCHANGED sub-check (R) → E002 |
| `cls._meta.get_field(cls.USERNAME_FIELD).unique` | `fieldUnique : Bool` | UNCHANGED first conjunct of the changed guard (R) |
| `settings.AUTHENTICATION_BACKENDS == ['django.contrib.auth.backends.ModelBackend']` | `usesDefaultBackend : Bool` | UNCHANGED severity selector (R) → E003 vs W004 |
| `isinstance(cls().is_anonymous, MethodType)` | `isAnonymousMethod : Bool` | UNCHANGED sub-check (R) → C009 |
| `isinstance(cls().is_authenticated, MethodType)` | `isAuthenticatedMethod : Bool` | UNCHANGED sub-check (R) → C010 |
| `cls._meta.constraints` (list of `BaseConstraint`) | `constraints : List ConstraintInfo` | declared model constraints; only the three observed attributes are carried |
| `isinstance(constraint, UniqueConstraint)` | `ConstraintInfo.isUnique : Bool` | filter predicate in `total_unique_constraints` |
| `constraint.condition is not None` | `ConstraintInfo.isConditional : Bool` | filter predicate in `total_unique_constraints` (kept iff `condition is None`) |
| `constraint.fields` (`tuple[str, ...]`) | `ConstraintInfo.fields : List String` | the constrained field tuple |
| `checks.Error/Warning/Critical(id=code)` | `String` (the `id` code) | each diagnostic represented by its stable code; `obj=`/`hint=` framing not modeled |
| accumulated `errors` (`list`) | `List String` | in-order concatenation; length = number of fired diagnostics |

`cls._meta.total_unique_constraints` (django/db/models/options.py:831-841) is a
`cached_property` returning
`[c for c in self.constraints if isinstance(c, UniqueConstraint) and c.condition is None]`.
It is modeled DEEPLY inside `coveredByUnconditionalUniqueConstraint` as the
filter `c.isUnique && !c.isConditional`, followed by the patch's
`constraint.fields == (USERNAME_FIELD,)` comparison rendered as
`c.fields == [usernameField]`. This is the change spelled out concretely; it
delegates to no opaque callee, so it is I-tagged (G-CONF), NOT an A-reference.

`checks.Error(...)` / `checks.Warning(...)` / `checks.Critical(...)` are framing
wrappers: their `obj=`, `hint=`, and message-text fields are unchanged by the
patch and identical between the empty / non-empty paths, so they are not
modeled; the observable, patched control decision is *whether* each diagnostic
fires, represented by its `id` code in the result list.

## Callee provenance
- The five boolean sub-check outcomes (`isinstance REQUIRED_FIELDS`, `in
  REQUIRED_FIELDS`, `get_field(...).unique`, backend equality, two `isinstance
  MethodType`) are UNCHANGED Python builtins / Django internals. The patch does
  not touch them; their boolean OUTCOMES are taken as refined inputs (R) — they
  are NOT axiomatized (no `_prop`), so there is no A-consumed callee and
  `axiom_check.py` is a skip stub.
- The changed operation is the constraint filter `total_unique_constraints` +
  the `fields == (USERNAME_FIELD,)` comparison. It is modeled DEEPLY as
  `coveredByUnconditionalUniqueConstraint` over the `ConstraintInfo` carrier
  (I-tagged) — the change spelled out concretely, delegating to no opaque callee,
  so it is NOT an A-reference either.

## Flag dependency
A constraint contributes to `total_unique_constraints` only when it is a
`UniqueConstraint` AND `condition is None` (unconditional / total). This flag
dependency is modeled by `ConstraintInfo.isUnique` and `ConstraintInfo.isConditional`
and is fuzzed in both `axiom_check.py` (skip stub) and `conformance_check.py`
(conditional constraints, non-unique constraints, and field-tuple mismatches are
all generated so the guard is exercised on every branch).

## G-CONF fuzz seed
Pinned seed: **13568**. ≥10^5 fuzzed inputs over the six booleans, the
`usernameField` string, and a randomly-shaped `constraints` list (varying
`isUnique`, `isConditional`, and `fields`), oversampling the case where the
field is not directly unique so the changed constraint-guard branch is hit hard.
