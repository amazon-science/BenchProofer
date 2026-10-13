# mapping.md — django__django-15128

## Symbol binding (file:line @ base_commit cb383753c0e0eb52306e1024d32a782549c27e61)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_renumberAliases` / `problem_spec_renumberAliases` | the change-map construction inside `django.db.models.sql.query.Query.bump_prefix` | `django/db/models/sql/query.py:891-933` (the changed method) |
| `aliases` argument | `self.alias_map` (its keys, in iteration order) consumed by `enumerate(self.alias_map)` | `django/db/models/sql/query.py:932` |
| `reserved` argument | the `exclude` parameter (a set of alias keys to leave untouched) | `django/db/models/sql/query.py:888,931-933` (the added parameter + guard) |
| `pfx` argument | `self.alias_prefix` (already bumped to a fresh, non-conflicting letter before the map is built) | `django/db/models/sql/query.py:917-929` |

The modeled function is the relabeling-map construction performed by
`bump_prefix`. It is the only function whose behavior the patch changes and the
operation whose effect the FAIL_TO_PASS test observes (combining two query sets
that share an alias prefix; the base/initial table alias must be preserved on
both sides for the merge to succeed).

### What the function does (base_commit)

```python
def bump_prefix(self, outer_query):
    ...
    # pick a fresh, non-conflicting alias_prefix (self.alias_prefix), then:
    self.change_aliases({
        alias: '%s%d' % (self.alias_prefix, pos)
        for pos, alias in enumerate(self.alias_map)
    })
```

It builds a *change map* old-alias → new-alias. Each current alias (the keys of
`self.alias_map`, in iteration order) is paired with a freshly numbered name
`'<prefix><pos>'`, where `pos` is the alias's 0-based position in the
enumeration and `<prefix>` is the freshly chosen, conflict-free alias prefix.
That change map is then handed to `change_aliases`, which renames every alias
accordingly.

The post-fix version adds an `exclude` parameter:

```python
def bump_prefix(self, other_query, exclude=None):
    ...
    if exclude is None:
        exclude = {}
    self.change_aliases({
        alias: '%s%d' % (self.alias_prefix, pos)
        for pos, alias in enumerate(self.alias_map)
        if alias not in exclude                     # <-- the fix
    })
```

The selection (`pos`) is still drawn from enumerating the **entire** alias_map —
an excluded alias still consumes its position number — but excluded aliases are
omitted from the change map, so they are NOT renamed. The caller (`combine`)
passes `exclude={initial_alias}` so the base-table alias, which must be present
identically on both sides of a query combination, is left untouched while every
other alias is renumbered under the fresh prefix.

### Argument ↔ Python expression bijection

| Lean input | Python meaning | notes |
|---|---|---|
| `pfx : String` | `self.alias_prefix` after bumping | the fresh prefix letter(s); a single value reused for every produced name. Unchanged by the patch. |
| `reserved : List Nat` | the `exclude` set (`{initial_alias}` from `combine`; `{}`/`None` ⇒ `[]`) | the aliases to leave unrenamed; membership-tested only. `None`/empty ⇒ `[]` (nothing reserved). |
| `aliases : List Nat` | `list(self.alias_map)` — the alias keys in enumeration order | each element ↔ one current alias; modeled as a `Nat` identity (an injective encoding of the distinct alias-name strings; only equality/membership and position are observed). |
| `result : List (Nat × String)` | the change-map dict `{old_alias: new_name}` | insertion-ordered `(old, new)` pairs; alias keys are distinct ⇒ the ordered association list is a lossless model of the dict. |

`pos` (the produced number) is the alias's index in the FULL enumeration of
`aliases`, regardless of whether it is reserved — modeled as the second
component of `aliases.zipIdx`.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `self.alias_prefix` (a string) | `String` | identity. |
| `exclude` (`None` / set of alias keys) | `List Nat` (`reserved`) | `None`/`set()` ↔ `[]`; a supplied set ↔ the encoded alias keys. Distinguishing `None` from empty is unobservable (both reserve nothing). |
| `self.alias_map` keys (insertion-ordered) | `List Nat` (`aliases`) | each key ↔ one encoded alias; iteration order ↔ list order. |
| produced new name `'%s%d' % (prefix, pos)` | `pfx ++ toString pos` (`String`) | identity: prefix concatenated with the decimal position. |
| the change-map `dict` `{old: new}` | `List (Nat × String)` (insertion-ordered) | distinct keys ⇒ ordered association list is a faithful, lossless model of the dict. |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — which aliases
  appear in the change map and the position each gets — is modeled DEEPLY over
  the alias list and the `reserved` membership test (SPEC_GUIDE §3: a
  deeply-modeled changed decision is never axiomatized). `change_aliases` (which
  consumes the map) is downstream of the changed construction and unchanged by
  the patch; its effect (applying the renaming) is not part of the modeled
  value — the modeled value is the change map itself, exactly what the patch
  alters.
- **`enumerate(self.alias_map)`** is modeled as `aliases.zipIdx`: the position is
  the index in the full list, so an excluded alias still consumes its index
  (faithful to `enumerate` running over the whole `alias_map` with the `if`
  filtering only which entries are emitted).
- **No flag dependency.** The only relevant configuration is whether an alias is
  reserved, carried by the `reserved` list.

## G-CONF fuzz seed

Pinned LCG seed: **15128** (see `conformance_check.py` `SEED`). Corpus: randomized
alias lists (length 0–8; alias identities drawn from a small pool so reservation
membership actually bites; distinct within a list) crossed with `reserved ∈
{[]} ∪ {random sublists incl. the empty list and the base alias}` and a small set
of prefix strings, over ≥1e5 fuzzed inputs, diffed against an in-process replica
of the post-patch change-map comprehension (`{alias: '%s%d' % (prefix, pos) for
pos, alias in enumerate(aliases) if alias not in exclude}`). Hand-picked edge
cases pin the discriminating "reserve the base alias" clause.
