# mapping.md — django__django-13925

## Modeled function

| Lean | Python |
|---|---|
| `implementation_checkDefaultPk` / `problem_spec_checkDefaultPk` / `correct_checkDefaultPk` | `Model._check_default_pk` (`django/db/models/base.py`, `@classmethod`, def at line 1298 @ base_commit `0c42cdf0d2422f4c080e93594d5d15381d6e955e`; the modeled guard is the `if (...)` at lines 1299–1303 post-patch) |

The function is a system check: it returns either an empty list (no issue) or a
one-element list holding a single `checks.Warning` with id `models.W042`. The
fix changes only the boolean GUARD that decides between the two; the warning's
content is unchanged.

## Type bijection (used by G-CONF / G-AX)

The modeled value is a pure decision over a handful of metadata observables of
the model class `cls`, plus the (unchanged) warning payload carried verbatim.
We do NOT stand up a Django model; we carry exactly the observables the real
guard reads.

| Lean (`CheckInput` field) | Python source expression @ base_commit | type |
|---|---|---|
| `autoCreated`               | `cls._meta.pk.auto_created` | `bool` |
| `pkIsOneToOne`              | `isinstance(cls._meta.pk, OneToOneField)` | `bool` |
| `pkParentLink`              | `cls._meta.pk.remote_field.parent_link` (only read when `pkIsOneToOne`; `OneToOneField.remote_field` always exposes `parent_link`) | `bool` |
| `defaultAutoFieldOverridden`| `settings.is_overridden('DEFAULT_AUTO_FIELD')` | `bool` |
| `appConfigOverridden`       | `cls._meta.app_config._is_default_auto_field_overridden` | `bool` |
| `modelObj`                  | `cls` (the model class the warning is `obj=` ed to) — modeled as a `Nat` identity | object id |
| `warnMsg`                   | the formatted `f"Auto-created primary key…'{settings.DEFAULT_AUTO_FIELD}'."` message | `str` |
| `warnHint`                  | the formatted `f"Configure the DEFAULT_AUTO_FIELD setting or the {…}.default_auto_field…"` hint | `str` |

| Lean (`Warning` field) | Python | type |
|---|---|---|
| `id`   | `id='models.W042'` (literal) | `str` |
| `obj`  | `obj=cls` | object id (`Nat`) |
| `msg`  | first positional arg of `checks.Warning(...)` | `str` |
| `hint` | `hint=...` kwarg | `str` |

Result `List Warning`: `checks.run_checks` collects each check's returned list;
`_check_default_pk` contributes `[]` or `[Warning(...)]`.

## Callee provenance + flag deps

- `settings.is_overridden`, `app_config._is_default_auto_field_overridden`,
  `pk.auto_created`, `isinstance(...OneToOneField)`,
  `pk.remote_field.parent_link` are all UNCHANGED observables the guard reads.
  Each yields a plain `bool`/identity and is carried into `CheckInput` as input
  data (exactly as `f.value_from_object` is carried in django__django-11163).
  None is modeled as an `opaque` callee, so the bundle declares **no** callee
  `opaque`/`axiom` (no dead axioms; axioms region empty).
- Short-circuit: Python evaluates `pk.remote_field.parent_link` only when
  `isinstance(pk, OneToOneField)` is true. `OneToOneField` always carries a
  `remote_field` with a `parent_link` attribute, so reading it never raises;
  modeling `pkParentLink` as an always-present `Bool` is sound (the `&&` in the
  guard short-circuits identically).

## G-CONF fuzz seed

Pinned seed: **13925** (also in `conformance_check.py`).
