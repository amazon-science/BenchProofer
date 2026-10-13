# mapping.md — django__django-12273

Cold construction (`spec_provenance: cold`): spec derived from `problem_statement`
+ gold `patch` + repo source at `base_commit`
(`927c903f3cd25c817c21738328b53991c035b415`). No prior twin/solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | repo symbol | location | role |
|---|---|---|---|
| `implementation_setPrimaryKey` | `Model._set_pk_val(self, value)` | `django/db/models/base.py:571` | the changed function under spec |
| `primaryKeyName` | `self._meta.pk.attname` | base.py:572 (`self._meta.pk.attname`) | own primary-key attribute name |
| `store` (`String → Option Int`) | the instance attribute dict (`getattr`/`setattr` target) | — | per-attribute current value |
| `value : Option Int` | the `value` argument to `_set_pk_val` | base.py:571 | assigned primary-key value (`None` ⇒ `none`) |
| `ancestorLinks : List AncestorLink` | `self._meta.parents.values()` | base.py:572 (added line); `Options.parents` in `django/db/models/options.py` | the parent-link fields for each ancestor in multi-table inheritance |
| `AncestorLink.linked` | truthiness of `parent_link` (`if parent_link …`) | base.py:573 (added) | the link field is present (not `None`) |
| `AncestorLink.sameAsPrimaryKey` | `parent_link == self._meta.pk` | base.py:573 (added) | the link field IS the instance's own primary key |
| `AncestorLink.keyName` | `parent_link.target_field.attname` | base.py:574 (added) | ancestor key attribute the link writes to |

`Field.target_field` / `Field.attname` / `Options.parents` are UNCHANGED repo
metadata accessors. They are not computed callees here — they supply the
*inputs* (`keyName`, `primaryKeyName`, the link list). `getattr`/`setattr` are
the attribute-store reads/writes, modeled as the `store` function (I-tagged).
There are therefore **no opaque callees, no consumed axioms, no A-references** —
every impl op is a concrete dict/loop op (R/I). `axiom_check.py` is a skip stub.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| attribute dict `{attname: value}` | `store : String → Option Int` | `store name = some n` ↔ attr `name` holds int `n`; `none` ↔ holds `None` |
| `value` (`int` or `None`) | `value : Option Int` | `None ↔ none`, `int n ↔ some n` |
| `self._meta.pk.attname` (str) | `primaryKeyName : String` | identity on the attname string |
| ordered `self._meta.parents.values()` | `ancestorLinks : List AncestorLink` | order-preserving; `None` link ⇒ `linked = false` |
| `parent_link.target_field.attname` | `AncestorLink.keyName : String` | identity on the attname string |
| `parent_link == self._meta.pk` | `AncestorLink.sameAsPrimaryKey : Bool` | identity comparison ↦ Bool |

Only int / `None` primary-key values occur in the modeled domain (AutoField /
OneToOneField PKs and the `pk = None` reset); `Option Int` covers it. The store
is restricted to the pk-chain attributes the function reads or writes.

## Callee provenance + flag deps
None. The function calls only `getattr`/`setattr` (attribute store) and iterates
metadata. No flag-dependent callee.

## G-CONF fuzz seed
`SEED = 12273` (pinned; consumed by `conformance_check.py`).
