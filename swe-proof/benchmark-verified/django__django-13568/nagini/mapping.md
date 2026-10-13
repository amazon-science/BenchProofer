# mapping.md — django__django-13568

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ede9fac75807fe5810df66280a60e7068cc97e4a`, states the type
abstraction, and gives the provenance of each modeled callee.

Repo file under change: `django/contrib/auth/checks.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `username_field_diagnostic(...)` | the username-uniqueness block of `check_user_model(...)` — `django/contrib/auth/checks.py:55-77` (the `if not cls._meta.get_field(cls.USERNAME_FIELD).unique:` guard and its error/warning bodies) | the modeled changed function (the decision of whether to emit, and at what severity, the USERNAME_FIELD uniqueness diagnostic) |
| `field_unique` (param) | `cls._meta.get_field(cls.USERNAME_FIELD).unique` — `django/contrib/auth/checks.py:55` | whether the login field carries a direct uniqueness guarantee |
| `c_span` / `c_single` / `c_total` (params) | the records of `cls._meta.total_unique_constraints` — `django/db/models/options.py:831-841` (each a `UniqueConstraint`) — projected to `len(constraint.fields)`, the single `constraint.fields[0]`, and `1` (see note) | the model's declared unique constraints, in parallel-sequence form |
| `username_field` (param) | `cls.USERNAME_FIELD` (a field-name string) — `django/contrib/auth/checks.py:55` | the login field's identifier (modeled as an int code) |
| `default_regime` (param) | `settings.AUTHENTICATION_BACKENDS == ['django.contrib.auth.backends.ModelBackend']` — `django/contrib/auth/checks.py:56-57` | True iff the single default authentication backend is configured |
| `covers(span,single,total,field)` | the iteration body `constraint.fields == (cls.USERNAME_FIELD,)` over `total_unique_constraints` (the patched `any(...)` predicate) | pure spec: one constraint discharges the obligation |
| `any_covers(...)` *(deep model)* | the patched `any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)` — `django/contrib/auth/checks.py:55-58` (post-patch) | pure spec: some constraint discharges the obligation |
| `Result()` codes `0/1/2` | the appended diagnostic: nothing / `checks.Error(... id='auth.E003')` / `checks.Warning(... id='auth.W004')` — `django/contrib/auth/checks.py:58-66` (Error) and `:67-77` (Warning) | the diagnostic outcome the F2P tests assert |

Note on `c_total` / `total_unique_constraints`: the iterated collection
`cls._meta.total_unique_constraints` is itself the subset of `cls._meta.constraints`
that are `UniqueConstraint`s with `condition is None`
(`django/db/models/options.py:837-841`). The model carries the unconditionality
explicitly as `c_total[k] ∈ {0,1}` so the **partial-constraint** case is sensed by
the spec rather than silently filtered: a constraint with a row predicate is
`c_total[k] == 0` and never covers (model), exactly as a conditional
`UniqueConstraint` is absent from `total_unique_constraints` (repo). This makes the
distinction observable in the differential witness rather than hidden in the input
projection.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| field-name `str` (e.g. `'username'`) | `int` identifier | only operation is equality; `name_a == name_b` ↔ `code_a == code_b`. A faithful bijection because names are compared, never indexed or decomposed. |
| `constraint.fields` (a `tuple` of field-name strings) | `(c_span[k], c_single[k])` | `len(fields)` ↔ `c_span[k]`; `fields[0]` ↔ `c_single[k]` (meaningful only when `c_span[k] == 1`). `fields == (USERNAME_FIELD,)` ↔ `c_span[k] == 1 and c_single[k] == username_field`. A composite key (`len(fields) != 1`) never equals a 1-tuple, matching `c_span[k] != 1 ⇒ not covers`. |
| `constraint.condition is None` (unconditional) | `c_total[k] == 1` | total/unconditional constraint ↔ `1`; conditional ↔ `0`. |
| `cls._meta.total_unique_constraints` (a `list[UniqueConstraint]`) | three parallel `List[int]` of equal length | element k of the list ↔ index k of the three sequences; `len(list)` ↔ `len(c_span)`. |
| `settings.AUTHENTICATION_BACKENDS == ['…ModelBackend']` (a `bool`) | `default_regime: bool` | identity. |
| `.unique` attribute (a `bool`) | `field_unique: bool` | identity. |
| appended `checks.Error/Warning` / nothing | int code `1` / `2` / `0` | the F2P tests assert the diagnostic's `id` (`auth.E003` ↔ Error, `auth.W004` ↔ Warning) and that the list is empty when no diagnostic is emitted; the code abstracts exactly that observable. |

The model spans ONLY the username-uniqueness block of `check_user_model`; the
other checks in the function (REQUIRED_FIELDS, is_anonymous/is_authenticated) are
unchanged by the patch and outside the modeled behaviour.

## 3. Callee provenance

There are **no axiomatized callees** (the `axioms` region is empty). The only
operation the patch introduces — the existential search
`any(constraint.fields == (USERNAME_FIELD,) for constraint in total_unique_constraints)`
— is an expressible structural predicate over the constraint list, so it is
modeled **deeply** as the front-recursive `any_covers` (with `covers`) and the
verified loop in `username_field_diagnostic`. There is therefore nothing for
G-AX to execute against a real library callee; `axiom_check.py` instead checks
that the deep predicate reproduces real Django's `UniqueConstraint` /
`total_unique_constraints` tuple-equality semantics (the constructor stores
`self.fields = tuple(fields)` at `django/db/models/constraints.py:119` and
`total_unique_constraints` keeps only `condition is None` constraints at
`django/db/models/options.py:837-841`).
