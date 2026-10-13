# mapping.md — django__django-12325

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 29c126bb349526b5f1cd78facbe9f25906f18563`, states the type
abstraction, and gives the provenance of the unchanged callees the modeled code
relies on (none is axiomatized — they are type-refined into the int carrier).

Repo files under change:
  * `django/db/models/base.py` — `ModelBase.__new__` (the parent-link
    collection loop).
  * `django/db/models/options.py` — `Options._prepare` (the now-redundant
    configuration guard, plus its import).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_inheritance_links(is_parent_link, related_key)` | the parent-link collection loop in `ModelBase.__new__` — `django/db/models/base.py:194-207` (the `# Collect the parent links for multi-table inheritance.` block building the local `parent_links` dict) | the modeled changed function: build the per-related-model record from the scanned one-to-one relations |
| `is_parent_link[i]` | `field.remote_field.parent_link` for the i-th scanned `OneToOneField` (`base.py:205`, the new conjunct at `base.py:205` post-patch; also read at `options.py:254` pre-patch) | per-relation designation flag |
| `related_key[i]` | `make_model_tuple(resolve_relation(new_class, field.remote_field.model))` for the i-th scanned `OneToOneField` (`base.py:206`) | per-relation related-model token (the dict key) |
| `result` (`Dict[int, int]`) | the local `parent_links` dict (`base.py:195`, `:207`) | the per-related-model record; model value = relation POSITION, repo value = the `OneToOneField` object |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view):
  * `base.py:205` pre-patch: `if isinstance(field, OneToOneField):` — records
    EVERY one-to-one field, no parent-link filter.
  * `options.py:254-257`: `if not field.remote_field.parent_link: raise
    ImproperlyConfigured('Add parent_link=True to %s.' % field)` — the guard
    that fired when the promoted relation was not a parent link.
  * `options.py:8`: the `ImproperlyConfigured` import, dropped because the only
    use is removed.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the iterable `base._meta.local_fields`, restricted to `OneToOneField` instances, scanned in order | two parallel lists `is_parent_link: List[bool]`, `related_key: List[int]` indexed by scan position | the i-th scanned one-to-one relation ↔ index `i`; `len` ↔ number of scanned relations. Non-`OneToOneField` locals are not scanned in either world (the `isinstance` gate is unchanged by the patch and is the same on both sides). |
| `field.remote_field.parent_link` (a `bool`) | `is_parent_link[i]` (`bool`) | identity |
| `make_model_tuple(resolve_relation(new_class, field.remote_field.model))` — an `(app_label, model_name)` string tuple | `related_key[i]` (`int` identity token) | the UNCHANGED key-derivation callee produces a hashable key used purely as a dict key; equality of derived keys ↔ equality of int tokens. The patch does not change this derivation; it is the same expression before and after, so it is a type refinement of the key, not a behaviour under test. (`resolve_relation` — `django/db/models/fields/related.py:37`; `make_model_tuple` — `django/db/models/utils.py:1`.) |
| `parent_links[key] = field` (dict value is the `OneToOneField` object) | `result[k] = i` (dict value is the relation POSITION) | the position `i` uniquely identifies the relation object; recording the position keeps the chosen relation's `parent_link` designation observable in the carrier (so the post-condition "every recorded relation is a parent link" is expressible). The downstream consumer reads only `field.remote_field.parent_link` of the chosen field (`options.py:254` pre-patch), which the position recovers as `is_parent_link[result[k]]`. |
| `iter(...).values()` insertion order / last-writer-wins per key | the loop's `result[related_key[i]] = i` last-writer-wins per key | Python dict assignment is last-writer-wins per key in both worlds; the model loop mirrors this exactly. Post-condition clause (4) (`Result()[related_key[i]] >= i` for every parent-link position `i`) PINS this in the spec: together with clause (1) the recorded position is exactly the LAST parent-link position per key, so a first-writer-wins rival (which still satisfies clauses (1) and (3)) is rejected. |

No callee is axiomatized: the only callees the loop invokes (`isinstance`,
`make_model_tuple`, `resolve_relation`) are UNCHANGED by the patch and are
absorbed into the int/bool carrier as type refinements (R), not contracted
inside any `Requires`/`Ensures`. There is therefore no kind-A axiom and no
`axiom_check.py` to run (G-AX is vacuous for this bundle).

## 3. Why the two repo hunks are one behaviour

The `base.py` hunk adds the eligibility filter `and field.remote_field.parent_link`
to the recording loop; the `options.py` hunk removes the guard `if not
field.remote_field.parent_link: raise ImproperlyConfigured(...)`. These are a
single behaviour: once the loop records ONLY parent links (clause (1) of the
model post-condition), the relation `_prepare` promotes — `next(iter(
self.parents.values()))` — is necessarily a parent link, so the guard can never
fire and is dead code. The guard's predicate `not field.remote_field.parent_link`
is exactly the negation of the model post-condition `is_parent_link[Result()[k]]`.
Removing a guard that is provably never taken (given clause (1)) preserves
behaviour; the model post-condition (1) is the invariant that makes the removal
sound. See refinement.md §B.
