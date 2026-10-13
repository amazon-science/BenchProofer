# mapping.md — django__django-13568

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ede9fac75807fe5810df66280a60e7068cc97e4a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo file under change: `django/contrib/auth/checks.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `usernameUniquenessVerdict (fieldUnique, constraints, usernameField, defaultBackendOnly)` | the username-uniqueness block of `check_user_model` — `django/contrib/auth/checks.py:54-77` | the modeled changed function (the system check's identity-field uniqueness decision) |
| `Constraint {fields, isUnique, conditional}` | a declared model constraint — `UniqueConstraint`/`CheckConstraint` in `Model._meta.constraints` (`django/db/models/constraints.py`) | record of the three constraint attributes the decision reads |
| `totalUnique (cs : List Constraint)` *(deep model — A-reference)* | `Options.total_unique_constraints` — `django/db/models/options.py:831-841` | pure spec: the field tuples of the unconditional uniqueness constraints; deep model of the metadata accessor, validated `totalUnique == _meta.total_unique_constraints` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `coversField (cs, uf)` | `any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)` — the new conjunct added at `checks.py:55-58` (post-patch) | pure spec: some total uniqueness constraint ranges over exactly the single identity field |
| `Verdict {ok, error, warning}` | the emitted check messages: `ok` = none; `error` = `checks.Error(id='auth.E003')`; `warning` = `checks.Warning(id='auth.W004')` (`checks.py:58-77`) | the three observable outcomes of the block |

The inputs decompose the real expression as follows:
- `fieldUnique` ↔ `cls._meta.get_field(cls.USERNAME_FIELD).unique` (`checks.py:55`);
- `constraints` ↔ `cls._meta.constraints` (the model's declared constraints);
- `usernameField` ↔ `cls.USERNAME_FIELD`;
- `defaultBackendOnly` ↔ `settings.AUTHENTICATION_BACKENDS == ['django.contrib.auth.backends.ModelBackend']` (`checks.py:56-57`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the real Django types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `cls.USERNAME_FIELD` / a field name (Python `str`) | Lean `String` | identity on field-name strings |
| a constraint's `fields` (Python `tuple[str, ...]`, e.g. `('username',)`) | `List String` | `tuple(fields)` ↔ `fields` as a `List String`, order-preserving; `len` ↔ `.length`; `(uf,)` ↔ `[uf]` |
| `UniqueConstraint(fields=…, condition=None)` | `Constraint {fields, isUnique := true,  conditional := false}` | an unconditional uniqueness constraint |
| `UniqueConstraint(fields=…, condition=Q(...))` | `Constraint {fields, isUnique := true,  conditional := true}` | a partial (conditioned) uniqueness constraint — applies to a subset of rows |
| `CheckConstraint(check=Q(...))` (or any non-`UniqueConstraint`) | `Constraint {isUnique := false, conditional := false}` | not a uniqueness constraint |
| `cls._meta.get_field(USERNAME_FIELD).unique` (Python `bool`) | `fieldUnique : Bool` | identity |
| `settings.AUTHENTICATION_BACKENDS == ['…ModelBackend']` (Python `bool`) | `defaultBackendOnly : Bool` | identity (the only-default-backend predicate) |
| `checks.Error(id='auth.E003')` / `checks.Warning(id='auth.W004')` / no message | `Verdict.error` / `Verdict.warning` / `Verdict.ok` | the block emits at most one of E003/W004; reduced to the three-valued verdict |

Note the real accessor `total_unique_constraints` keeps a constraint iff
`isinstance(c, UniqueConstraint) and c.condition is None`, which is precisely the
Lean predicate `c.isUnique && !c.conditional`. The new patch conjunct compares
`constraint.fields == (cls.USERNAME_FIELD,)` — a tuple of length one — which maps
to `fs == [usernameField]` in `coversField`.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `totalUnique` deep model ↔ `Options.total_unique_constraints` (A-reference)
**Accessor:** `django.db.models.options.Options.total_unique_constraints`
(`options.py:831-841`), a `@cached_property`:

```python
@cached_property
def total_unique_constraints(self):
    return [
        constraint
        for constraint in self.constraints
        if isinstance(constraint, UniqueConstraint) and constraint.condition is None
    ]
```

This accessor is **UNCHANGED** by the gold patch (the patch only adds a *caller*
in `checks.py`); it is therefore an A-reference, not the function under change.
`totalUnique` (Solution.lean `pure` region) models its field-tuple projection
front-recursively: keep `c.fields` iff `c.isUnique && !c.conditional`. The patch
then tests `constraint.fields == (USERNAME_FIELD,)` over that list — modeled by
`coversField cs uf = (totalUnique cs).any (· == [uf])`.

**Soundness check (G-AX):** `axiom_check.py` builds real Django models from
fuzzed constraint descriptors (unconditional `UniqueConstraint`, conditioned
`UniqueConstraint`, `CheckConstraint`, single- and multi-field) and asserts
`totalUnique(specs) == [list(c.fields) for c in M._meta.total_unique_constraints]`
on 8 boundary shapes + 4000 fuzz lists. Imports only Django (the repo under test)
+ stdlib. Runs on the **unpatched** repo (the accessor is unchanged). Exit 0 iff
sound.

No axiom is consumed by the proof: the decision is computed entirely from the
inputs (`coversField` over `totalUnique`, the field flag, and the backend flag).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13568`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`totalUnique`/`coversField` and the `do`-block verdict to Python (all R/I ops);
the oracle is the patched `check_user_model` run in-container with the gold
applied, its emitted `auth.E003`/`auth.W004` reduced to the `Verdict`. To avoid
rebuilding a Django model per input (and growing the app registry unboundedly), it
prebuilds a pool of 600 model shapes once and fuzzes pool × {default, custom}
backend over ≥10⁵ scenarios.
