# refinement.md — django__django-13925

Maps every operation in `implementation_checkDefaultPk` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `_check_default_pk` (`Model._check_default_pk`)

Post-patch repo code (`patch.diff`, `django/db/models/base.py`):
```python
@classmethod
def _check_default_pk(cls):
    if (
        cls._meta.pk.auto_created and
        # Inherited PKs are checked in parents models.
        not (
            isinstance(cls._meta.pk, OneToOneField) and
            cls._meta.pk.remote_field.parent_link
        ) and
        not settings.is_overridden('DEFAULT_AUTO_FIELD') and
        not cls._meta.app_config._is_default_auto_field_overridden
    ):
        return [
            checks.Warning(
                f"Auto-created primary key used when not defining a "
                f"primary key type, by default "
                f"'{settings.DEFAULT_AUTO_FIELD}'.",
                hint=( ... ),
                obj=cls,
                id='models.W042',
            ),
        ]
    return []
```

Lean impl (`implementation_checkDefaultPk`):
```lean
def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
  if c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden then
    return [{ id := "models.W042", obj := c.modelObj,
              msg := c.warnMsg, hint := c.warnHint }]
  return []
```

## Operation correspondence

| # | Lean op | patch.diff / repo op | tag | note |
|---|---------|----------------------|-----|------|
| 1 | `c.autoCreated` | `cls._meta.pk.auto_created` | R | `bool` ↔ `Bool`; the value is read as input data (mapping.md). Identical short-circuit position (first conjunct). |
| 2 | `!(c.pkIsToOneRelation && c.pkRelationIsParentLink)` | `not (isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link)` | R | The fix's added guard. `isinstance(pk, OneToOneField)` ↔ `pkIsToOneRelation : Bool`; `pk.remote_field.parent_link` ↔ `pkRelationIsParentLink : Bool`. Python's `and` short-circuits the `.remote_field.parent_link` read; modeled as a total `Bool && Bool` whose left operand gates the right identically (mapping.md: `remote_field.parent_link` is always present on a `OneToOneField`, never raises). |
| 3 | `!c.defaultAutoFieldOverridden` | `not settings.is_overridden('DEFAULT_AUTO_FIELD')` | R | `bool` ↔ `Bool`, read as input data. |
| 4 | `!c.appConfigOverridden` | `not cls._meta.app_config._is_default_auto_field_overridden` | R | `bool` ↔ `Bool`, read as input data. |
| 5 | `&&` chaining of 1–4, `if … then … else` | the `if (... and ... and ... and ...)` guard | I | Boolean conjunction → list-or-empty branch; identical control flow. |
| 6 | `return [{ id := "models.W042", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint }]` | `return [checks.Warning(<msg>, hint=<hint>, obj=cls, id='models.W042')]` | R | One-element list of an advisory record. `id` literal `'models.W042'` ↔ `"models.W042"` (I within the record). `obj=cls` ↔ `modelObj : Nat` identity (R). `msg`/`hint` are the formatted strings carried through verbatim as input data (R) — the patch does not change their content, only whether they are emitted. |
| 7 | `return []` | `return []` | I | empty contribution. |

No changed op is inexpressible; no op is axiomatized. The added parent-link
guard (#2) is modeled DEEPLY as a boolean over the two observables, not as a
consumed axiom — hence the axioms region is empty and there are no A rows. The
R/I legs are mechanically refuted by G-CONF (`conformance_check.py`).

## Prepatch (the bug)

`Solution_prepatch.lean` omits conjunct #2 (the parent-link guard) entirely:
```lean
if c.autoCreated && !c.defaultAutoFieldOverridden && !c.appConfigOverridden then ...
```
This is exactly the pre-patch repo code. On a model whose auto-created primary
key is a parent-linking to-one relation with no default opted into
(`autoCreated=true, pkIsToOneRelation=true, pkRelationIsParentLink=true,
defaultAutoFieldOverridden=false, appConfigOverridden=false`), the prepatch emits
`models.W042` while the spec suppresses it — the discriminating clause. G-DIFF
requires the carried gold proof to fail to close against this impl.
