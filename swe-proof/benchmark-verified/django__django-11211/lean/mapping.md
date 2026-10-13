# mapping.md — django__django-11211

## Instance
- repo: django/django
- base_commit: ba726067604ce5a8ca3919edf653496722b433ab
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The modeled function is `UUIDField.get_prep_value`
(django/db/models/fields/__init__.py, added at line ~2328 by the gold patch). At
base_commit `UUIDField` declares no `get_prep_value`, so it inherits the base
`Field.get_prep_value` (django/db/models/fields/__init__.py:771), which is an
identity pass-through (it only un-wraps a lazy `Promise`; for an ordinary value
it returns the value unchanged). The gold patch adds:

```python
def get_prep_value(self, value):
    value = super().get_prep_value(value)   # base pass-through
    return self.to_python(value)            # canonicalise to a uuid.UUID
```

`UUIDField.to_python` (same file, ~line 2348) maps a value to the `uuid.UUID` it
denotes: `None` → `None`; an existing `uuid.UUID` → itself; an `int` →
`uuid.UUID(int=value)`; otherwise (a text spelling) → `uuid.UUID(hex=value)`,
which decodes the hexadecimal digits of the spelling, ignoring the standard
separators (hyphens, optional `urn:uuid:` / brace wrappers).

### Why it matters (the bug)
Generic-foreign-key prefetch
(django/contrib/contenttypes/fields.py:198-206, `gfk_key`) builds a match key

```python
return (model._meta.pk.get_prep_value(getattr(obj, self.fk_field)), model)
```

and joins it against the related object's `(obj.pk, obj.__class__)`. When the
related model's primary key is a `UUIDField`, `obj.pk` is a `uuid.UUID` but the
stored foreign value (`self.fk_field`, a text column) is the *string* spelling of
that UUID. With the inherited identity `get_prep_value`, the key stays a string,
so `string-key != UUID-key` and the join finds no match — prefetch yields `None`.
Adding `get_prep_value` = `to_python(super())` canonicalises the string spelling
to the same `uuid.UUID`, so the two keys compare equal.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_normalizeKey` | `UUIDField.get_prep_value` (post-patch); = `self.to_python(super().get_prep_value(value))` (fields/__init__.py, added ~:2328) |
| `problem_spec_normalizeKey`   | the post-condition this prepared value must satisfy: it equals the canonical identifier the input denotes |
| `basePrep`   | `Field.get_prep_value` (fields/__init__.py:771) — base pass-through (identity for a non-`Promise` value) — deep-model A-reference |
| `canonicalValue` | `UUIDField.to_python` (fields/__init__.py ~:2348) — text→`uuid.UUID` conversion — deep-model A-reference |
| `decodeHex`  | `uuid.UUID(hex=…).int` for a textual spelling (hex digits accumulated, separators ignored) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `UuidValue.absent` | `None` | no value present (`fk_val is None` is filtered out upstream, but `to_python(None) = None`) |
| `UuidValue.canonical n` | `uuid.UUID(int=n)` | an already-parsed identifier object; `n = uuid.int` (0 ≤ n < 2¹²⁸) |
| `UuidValue.textual s` | a `str` spelling of the identifier (e.g. `str(uuid)`, the 32-hex form, hyphenated, or `urn:uuid:`/brace-wrapped) | the value carried in the text fk column |
| result `UuidValue.canonical n` | `uuid.UUID(int=n)` | the prepared key |
| `decodeHex s` | `uuid.UUID(hex=s).int` | hex digits of `s` accumulated left-to-right, non-hex separators ignored |

`List Char` ↔ Python `str` is the per-code-point bijection.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as a logical axiom. The two callees the
  patch composes — the base pass-through `Field.get_prep_value` and the
  `UUIDField.to_python` conversion — are modeled DEEPLY as `basePrep`
  (identity) and `canonicalValue` (text→identifier decode). They are A-references
  (validated == the real callees by G-CONF over the modeled domain), so there is
  no `opaque`/`axiom` in `Solution.lean` and `axiom_check.py` is a skip stub.
- Domain restriction: `to_python` raises `ValidationError` on a text spelling that
  is not a valid identifier. The modeled domain is the prefetch use case, where the
  textual fk value is always a valid spelling of a stored UUID (`object_pk =
  str(related.pk)`); G-CONF fuzzes only valid spellings + `uuid.UUID` objects +
  `None`, where the real `to_python` does not raise.
- No flag dependency: `get_prep_value` / `to_python` take no connection or flag
  argument.

## G-CONF fuzz seed
- pinned seed: `11211`
- ≥10⁵ fuzzed values drawn to exercise: `None`; freshly generated `uuid.UUID`
  objects; the canonical hyphenated string form `str(u)`; the bare 32-hex form
  `u.hex`; upper-cased hex; brace-wrapped spellings; and the all-zero / all-`f`
  boundary identifiers. Each is fed to the REAL patched
  `UUIDField().get_prep_value` (oracle) and to the R/I shadow — which is the LEAN
  deep model `canonicalValue`/`decodeHex` reimplemented from `Solution.lean`, NOT
  the real `to_python` — compared by the resulting `uuid.UUID.int` (or `None`).
  So G-CONF genuinely validates the deep model against Python rather than Python
  against itself.
- Modeled domain: `decodeHex` (accumulate hex digits, ignore separators) is
  faithful to `uuid.UUID(hex=s).int` exactly for spellings whose only non-hex
  characters are the standard separators `-`, `{`, `}` (hyphenated, bare,
  upper-cased, brace-wrapped). The `urn:uuid:` spellings are OUT of the modeled
  domain — their literal letters (`urn`, `uuid`) embed hex digits a digits-only
  decode cannot model — and are not fuzzed. The prefetch use case stores
  `object_pk = str(related.pk)` (the hyphenated form), which is in-domain.
