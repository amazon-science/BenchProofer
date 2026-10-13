# mapping.md — symbol binding & type bijection (django__django-14672)

## Modeled function
- **Lean** `implementation_m2mIdentity : List HVal → HVal → FieldSeq → HVal → List HVal`
- **Python** `ManyToManyRel.identity` (a `@property`) —
  `django/db/models/fields/reverse_related.py:309-315 @ 00ea883`
  (post-patch:
  `return super().identity + (self.through, make_hashable(self.through_fields), self.db_constraint)`).

The function under spec is the `identity` property of the many-to-many reverse
relation. It returns a tuple used as the relation's comparison/hash key
(`__eq__`/`__hash__` derive from it). The patch wraps the field-name sequence
component in the standard-library hashable-canonicalisation routine so the whole
key is hashable even when that component was supplied as a list.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| identity tuple | `List HVal` | ordered sequence of key components; tuple ↔ list at this level (we only model membership/order/shape, not Python tuple identity) |
| `super().identity` (the inherited prefix) | `base : List HVal` | unchanged components carried verbatim; opaque to this fix |
| `self.through` (a model class or `None`) | `through : HVal` | one opaque key component, carried verbatim |
| `self.through_fields` | `throughFields : FieldSeq` | `None` ↔ `.absent`; a `tuple(...)` of names ↔ `.astuple`; a `list[...]` of names ↔ `.aslist` |
| `self.db_constraint` (a bool) | `dbConstraint : HVal` | one opaque key component, carried verbatim |
| a field-name string | `HVal.hstr` | one element of the sequence |
| `make_hashable(seq)` result | `canonTF throughFields` | list/tuple → tuple-of-names (`HVal.htuple`); `None` → `HVal.hnone` |

`through_fields` in real Django is either `None`, a `tuple` of field-name
strings, or a `list` of field-name strings (it is normalised from the
`ManyToManyField(through_fields=...)` argument; the test patch uses both
`('event','invitee')` and `['parent','model']`). `FieldSeq` captures exactly
these three shapes. The names themselves are opaque strings.

## Callee provenance
- `make_hashable` — `django/utils/hashable.py:4-24 @ 00ea883`, UNCHANGED by this
  patch but newly CALLED by it. Its behavior on the `through_fields` domain (a
  list/tuple of already-hashable strings, or `None`) is modeled DEEPLY as
  `canonTF`: `None` is returned unchanged; a list/tuple of strings is mapped to a
  tuple of those same strings (order preserved). This is an **A-reference**
  (refinement.md row 3), validated by G-AX against the real `make_hashable` over
  the `through_fields` domain — NOT a consumed axiom.
- `super().identity` is the inherited `ForeignObjectRel.identity` /
  `ManyToManyRel`'s prefix; it is unchanged and carried as the opaque `base`
  prefix (I-tagged). `self.through` and `self.db_constraint` are read verbatim
  (I-tagged).
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Domain note (G-AX / G-CONF restriction)
`make_hashable` is general (it also handles dicts and arbitrary iterables), but
the fix only ever feeds it `self.through_fields`, whose real domain is
`None | tuple[str,...] | list[str,...]`. G-AX therefore validates `canonTF`
against `make_hashable` on exactly that domain (the configuration the fix uses).

## G-CONF fuzz seed
Pinned seed: **14672**. ≥10^5 fuzzed inputs over field-name sequences sampling
`None`, tuples, and lists of varying length with assorted name strings, plus
the test-patch boundary cases (`['event','invitee']`, `['parent','model']`,
`('event','invitee')`, `[]`, `()`).
