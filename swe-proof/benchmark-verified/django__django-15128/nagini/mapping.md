# mapping.md — django__django-15128

Binds every `model.py` symbol to its repository counterpart at
`base_commit = cb383753c0e0eb52306e1024d32a782549c27e61`, states the type
abstraction, and gives the provenance of the relabel-map construction the deep
model is validated against.

Repo file under change: `django/db/models/sql/query.py` (class `Query`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_relabel_map(aliases, new_ns, excluded)` | the relabel-map construction inside `Query.bump_prefix` — `django/db/models/sql/query.py:926-929` (the `self.change_aliases({...})` dict-comprehension) | the modeled changed behaviour: building the alias relabel map that `change_aliases` then applies |
| `aliases` (param) | `self.alias_map` keys, in order — `enumerate(self.alias_map)` (`query.py:928`) | the ordered list of current aliases |
| `new_ns` (param) | the bumped `self.alias_prefix` (`query.py:918,927`) — the fresh renaming namespace chosen so it does not clash | the new namespace fresh aliases are generated under |
| `excluded` (param) | the kept base alias — `initial_alias = self.get_initial_alias()` passed as `rhs.bump_prefix(self, exclude={initial_alias})` (`combine`, `query.py:575-583` post-patch); used as `if alias not in exclude` (`query.py:929` post-patch) | the shared base alias kept fixed so it stays common to both sides |
| `fresh_alias(new_ns, pos)` | `'%s%d' % (self.alias_prefix, pos)` (`query.py:927`) | the fresh alias generated for ordinal position `pos` |
| `Result()[0]` (targets) | the VALUES of the change map `{alias: '%s%d' % (prefix, pos) ...}` | the relabel targets |
| `Result()[1]` (is_source flags) | which aliases are KEYS of the change map (`alias not in exclude`) | source/kept marker |
| `floor_of(ns)`, `BASE()` | (modelling artefacts) | the integer encoding of "namespace n owns region [n*BASE, (n+1)*BASE)" (see §2) |
| `disjoint_by_floor(...)` | (proof lemma) | carries `set(change_map).isdisjoint(change_map.values())` from the namespace separation |

The safety property the construction must satisfy is asserted one call deeper,
in `Query.change_aliases` — `assert set(change_map).isdisjoint(change_map.values())`
(`query.py:849`). The gold patch documents that assertion with a comment and
guarantees it by the `combine`+`bump_prefix` changes; the model encodes the
disjointness as the `build_relabel_map` postcondition.

### Pre-patch symbols the change touches (for the refinement audit, not named in the spec view)
- `Query.bump_prefix(self, outer_query)` (`query.py:882`) → gains an `exclude`
  parameter and renames `outer_query`→`other_query`; the relabel comprehension
  gains `if alias not in exclude` (`query.py:926-929`).
- `Query.combine` (`query.py:557`) → adds, before building its change_map,
  `initial_alias = self.get_initial_alias(); rhs.bump_prefix(self, exclude={initial_alias})`
  and removes the later bare `self.get_initial_alias()` (`query.py:592-594`).
- `Query.change_aliases` (`query.py:843`) → comment-only (documents the
  `isdisjoint` assertion); no behavioural change.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| alias name `str` (e.g. `'T4'`, `'U5'`) | non-negative `int` encoding `(namespace, index)` as `namespace*BASE + index`, `0 <= index < BASE` | two aliases equal ⟺ encodings equal; an alias's namespace (its leading-letter "prefix" region) ⟺ `encoding // BASE`; `BASE = 1000 >> max aliases per query` so the region of one namespace never overflows into another |
| `self.alias_prefix` (a capital letter, the renaming namespace) | the namespace integer `ns`; its region floor is `floor_of(ns) = ns*BASE` | a fresh prefix letter distinct from the current one ⟺ a namespace integer `new_ns` whose floor is above every current alias (`aliases[k] < floor_of(new_ns)`) |
| ordered `self.alias_map` (dict; iteration = insertion order) | ordered `List[int]` `aliases` | `enumerate(self.alias_map)` ⟺ indexing `aliases` by ordinal position |
| `change_map` dict `{old_alias: new_alias}` | the pair of positionally-aligned `List[int]` `(targets, is_source)`: the map is `{aliases[k]: targets[k] for k if is_source[k]==1}` | a KEY ⟺ a position with `is_source==1`; the map's VALUES ⟺ `{targets[k] : is_source[k]==1}` |
| `'%s%d' % (prefix, pos)` | `fresh_alias(new_ns, pos) = new_ns*BASE + pos` | the new alias's namespace is `new_ns`; its ordinal is `pos`; distinct `pos` ⇒ distinct fresh aliases |
| `if alias not in exclude` (exclude = `{initial_alias}`) | `is_source[pos] = 1 iff aliases[pos] != excluded` | a single excluded base alias; absence-from-`exclude` ⟺ being a relabel source |

The "fresh prefix ⇒ fresh region above the old aliases" abstraction is exactly
why the real construction is safe: after `bump_prefix` picks a `self.alias_prefix`
not in `self.subq_aliases` and (in `combine`'s use) different from the lhs
prefix, every generated alias `'<new_prefix><pos>'` lies in the new prefix's
namespace, disjoint from the current aliases (which live in the old prefix's
namespace). Modelling aliases as integers with `new_ns`'s region strictly above
the current aliases captures that separation faithfully; it is the property the
F2P test depends on.

## 3. Provenance of the deep model (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `build_relabel_map` ↔ the real `bump_prefix` change-map construction (A-reference)
There is **no consumed `@ContractOnly` axiom**: the changed behaviour is the
relabel-map construction itself, modelled **deeply** in `build_relabel_map`'s
impl region (and proved disjoint via the `disjoint_by_floor` lemma). The deep
model is validated **equal to the real construction** out-of-band by
`axiom_check.py` (G-AX), which reproduces the gold patch's dict-comprehension
verbatim:

```python
# Query.bump_prefix, after the gold patch (django/db/models/sql/query.py):
if exclude is None:
    exclude = {}
self.change_aliases({
    alias: '%s%d' % (self.alias_prefix, pos)
    for pos, alias in enumerate(self.alias_map)
    if alias not in exclude
})
```

and asserts, over boundary + 20000 fuzz inputs (alias lists in a shared old
namespace, a fresh prefix letter, the base alias excluded):

  * **clause (1) — source-flag biconditional / excluded preservation:** a
    current alias is a KEY of the map IFF it is not the excluded alias (the
    excluded base alias is never a key). Checked at the index level (each alias
    individually), not via a value-membership proxy.
  * **clause (2) — disjointness:** `set(change_map).isdisjoint(change_map.values())`
    holds (the exact assertion `Query.change_aliases` makes at `query.py:849`),
    GIVEN the fresh prefix differs from the current aliases' prefix.
  * **clause (3) — per-ordinal value / injectivity:** the value assigned to the
    alias at ordinal position `pos` is exactly `'%s%d' % (new_prefix, pos)`
    (the model's `fresh_alias(new_ns, pos)`), so distinct positions get distinct
    values — the comprehension is injective and never collapses two source
    aliases onto one renamed value. Checked at the index level against the real
    construction (no value-membership proxy). This is the model's strengthened
    postcondition `Result()[0][j] == fresh_alias(new_ns, j)`.

It also checks the **discriminator**: the pre-patch construction (no `exclude`,
reproduced as `prepatch_change_map`) makes the excluded base alias a KEY,
violating clause (1) — confirming the behavioural delta the F2P test observes.

**Flag/precondition dependency:** the disjointness holds only when the fresh
namespace differs from the current aliases' namespace — the real code
guarantees this because `bump_prefix` selects a `self.alias_prefix` not already
used (and `combine` only ever calls it when lhs and rhs share a prefix, so the
bump always changes it relative to the current aliases). The axiom_check enforces
`new_prefix` ≠ every current alias's leading letter on every generated input, and
the model encodes it as the precondition `aliases[k] < floor_of(new_ns)`.
`axiom_check.py` imports only the standard library; nothing repo-specific.
