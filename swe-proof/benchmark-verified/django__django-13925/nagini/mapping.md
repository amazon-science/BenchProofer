# mapping.md — django__django-13925

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0c42cdf0d2422f4c080e93594d5d15381d6e955e`, states the type
abstraction, and records the provenance of the one A-reference correspondence
(there are no consumed axioms).

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_default_pk(pk, setting_overridden, appconfig_overridden)` | `Model._check_default_pk(cls)` — `django/db/models/base.py:1298-1320` | the modeled changed classmethod (the auto-pk advisory check) |
| `PkField` (record) | `cls._meta.pk` — the model's primary-key field descriptor (`django/db/models/options.py`; the field instance) | minimal record of only the touched fields |
| `PkField.auto` | `cls._meta.pk.auto_created` (`base.py:1301`) | the key was created automatically (no explicit PK declared) |
| `PkField.reuses_ancestor_key_a` | `isinstance(cls._meta.pk, OneToOneField)` (`base.py` patched hunk; `OneToOneField` at `django/db/models/fields/related.py:1027`) | abstract reuse flag A (real-side: the key field is a one-to-one relation) |
| `PkField.reuses_ancestor_key_b` | `cls._meta.pk.remote_field.parent_link` (`base.py` patched hunk; flag set in `related.py:461,470`) | abstract reuse flag B (real-side: that relation is the link to a concrete ancestor); the conjunction A∧B means the key re-uses the ancestor's declared key |
| `setting_overridden` (param) | `settings.is_overridden('DEFAULT_AUTO_FIELD')` (`base.py:1302`) | project-wide default-auto-field setting was configured |
| `appconfig_overridden` (param) | `cls._meta.app_config._is_default_auto_field_overridden` (`base.py:1303`) | owning app's default-auto-field attribute was configured |
| return `int` (0/1) | the returned list `[]` / `[checks.Warning(... id='models.W042')]` (`base.py:1305-1320`) | the count of advisories emitted |
| `advisory_warranted(...)` *(pure spec)* | the full `if (...)` branch condition (`base.py:1300-1304`, post-patch) | pure spec: whether the advisory is emitted |
| `reuses_ancestor_declared_key(...)` *(pure spec)* | the added conjunct `isinstance(pk, OneToOneField) and pk.remote_field.parent_link` (post-patch hunk) | pure spec: the key re-uses a concrete ancestor's already-declared key |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `cls._meta.pk` (a `Field` instance) | `PkField` record with three booleans | only the three flags the check reads are modeled; all other field state is irrelevant to the observable outcome |
| `cls._meta.pk.auto_created : bool` | `pk.auto : bool` | identity on the boolean |
| `isinstance(cls._meta.pk, OneToOneField) : bool` | `pk.reuses_ancestor_key_a : bool` | the runtime type test reduced to its boolean result (A-reference §3) |
| `cls._meta.pk.remote_field.parent_link : bool` | `pk.reuses_ancestor_key_b : bool` | identity on the boolean (only meaningful when flag A holds; the conjunction `reuses_ancestor_key_a and reuses_ancestor_key_b` guards the read on the real side too) |
| `settings.is_overridden('DEFAULT_AUTO_FIELD') : bool` | `setting_overridden : bool` | identity; modeled as a parameter (global state read) |
| `cls._meta.app_config._is_default_auto_field_overridden : bool` | `appconfig_overridden : bool` | identity; modeled as a parameter |
| `return []` / `return [Warning(...)]` (singleton list, fixed content) | `return 0` / `return 1` | the list is either empty or a single `models.W042`; its content (message/hint/obj) is constant across the warning branch and identical between pre- and post-patch, so the only observable is the count |

`isinstance` and attribute reads on a rich `Field` object are reduced to the
boolean field record because the only behaviour the check (and the F2P tests)
observe is **whether** the single `models.W042` is produced. The advisory's
message, hint, obj, and id are byte-identical between the pre- and post-patch
code (the patch adds only a conjunct to the guard), so they carry no
discriminating information and are not modeled.

## 3. The A-reference correspondence (checked by G-AX / axiom_check.py)

There are **no consumed axioms** in this bundle: the modeled check is pure
boolean logic over field flags, spelled out directly in `model.py`.

The one correspondence the refinement rests on is structural, tagged
**A-reference** in refinement.md and validated by `axiom_check.py`:

  the model's pure predicate `advisory_warranted` equals the patched source's
  branch condition under the field bijection of §2.

Both sides are total boolean functions of the same five booleans, so
`axiom_check.py` enumerates the **entire** `2**5` truth table and asserts
equality on every assignment (the input domain is finite and fully covered —
boundary and fuzz coincide).

**Provenance of the field bijection.** The discriminating case — an
implicitly-created primary key that is the one-to-one parent link — is exactly
the auto-created `<parent>_ptr` field Django builds for a child of a concrete
model:

```python
# django/db/models/base.py:243-249  (@ base_commit)
field = OneToOneField(
    base,
    on_delete=CASCADE,
    name=attr_name,
    auto_created=True,     # -> pk.auto_created  == pk.auto              == True
    parent_link=True,      # -> remote_field.parent_link (reuses_ancestor_key_b) == True
)
```

That field is a `OneToOneField` (`related.py:1027`), so
`isinstance(pk, OneToOneField)` is `True` (reuses_ancestor_key_a). Hence for the
inherited key the triple `(auto, reuses_ancestor_key_a, reuses_ancestor_key_b)
== (True, True, True)` and the patched guard suppresses the advisory — the
behaviour the F2P tests `test_explicit_inherited_pk` and
`test_auto_created_inherited_pk` demand. A plain auto-created `AutoField` PK
(`options.py:286`, `pk_class(..., auto_created=True)`, not a `OneToOneField`)
gives `(True, False, False)` and the advisory IS emitted (the P2P
`test_auto_created_pk`). Docs / source: the patched hunk in
`django/db/models/base.py` and the field construction sites cited above.
