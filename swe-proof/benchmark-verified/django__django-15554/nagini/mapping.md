# mapping.md — django__django-15554

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 59ab3fd0e9e606d7f0f7ca26609c06ee679ece97`, states the type
abstraction, and gives the provenance of the equality semantics the model
encodes deeply.

Repo file under change: `django/db/models/sql/query.py` (the join-aliasing
decision). The equality semantics live in `django/db/models/sql/datastructures.py`
(the `Join` class), which the change does NOT edit but whose `__eq__` / `equals`
the change selects between.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `install_join(base, frel, reuse_all, reuse_mask, jb, jf, constrained)` | `Query.join(self, join, reuse=None, reuse_with_filtered_relation=False)` — `django/db/models/sql/query.py:1014` (body 1027-1040, the `reuse_aliases` computation + the reuse-vs-new-alias decision) | the modeled changed function (alias reuse decision) |
| `base[i]` (slot i base relation identity) | `j.identity[:-1]` of the join `j` in `self.alias_map` — `Join.identity` minus its last element, `datastructures.py:147-154` | the `equals`-comparable part of a join's identity (class, table_name, parent_alias, join_field) |
| `frel[i]` (slot i refinement tag) | `j.filtered_relation` — the last element of `Join.identity`, `datastructures.py:153` | the `filtered_relation` of slot i; tag 0 ≙ `None`, distinct positive tags ≙ distinct `FilteredRelation` instances |
| `jb` (incoming base identity) | `join.identity[:-1]` of the incoming `join` | incoming join's `equals`-comparable identity |
| `jf` (incoming refinement tag) | `join.filtered_relation` | incoming join's `filtered_relation` |
| `reuse_all` | `reuse is None` (all joins reusable) | the unconstrained reuse mode |
| `reuse_mask[i]` | `a in reuse` for slot alias `a` | membership of slot i's alias in the supplied `reuse` set |
| `constrained` | `reuse_with_filtered_relation and reuse` (the new constrained-reuse branch condition) — `query.py:1027` post-patch | selects the constrained branch (base-only match, masked slots only) |
| `Result()` (a fresh slot is needed) | `not reuse_aliases` — the decision to fall through to `self.table_alias(create=True)` and append a new alias (`query.py:1042-1053`) | True iff `join()` creates a new alias instead of reusing one |
| `matches_default(i,…)` | `j == join` — `Join.__eq__`, `datastructures.py:156-159` (full `identity` incl. `filtered_relation`) | default-branch match predicate (post-patch) |
| `matches_constrained(i,…)` | `j.equals(join)` — `Join.equals`, `datastructures.py:164-166` (`identity[:-1]`, ignores `filtered_relation`) | constrained-branch match predicate; ALSO the pre-patch default predicate |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.alias_map` (an ordered dict alias→`Join`) | parallel arrays `base: List[int]`, `frel: List[int]` indexed by slot position | slot i ≙ the i-th `(alias, j)` entry; `base[i]` ≙ `j.identity[:-1]` interned to an int; `frel[i]` ≙ `j.filtered_relation` interned to an int (0 for `None`) |
| `Join.identity[:-1]` (class, table_name, parent_alias, join_field) | a single `int` `base[i]` | equal identities ⇒ equal ints, distinct identities ⇒ distinct ints (a faithful interning; only equality is observed) |
| `Join.filtered_relation` (`None` or a `FilteredRelation`) | `int` `frel[i]` (0 = `None`, positive = a distinct refinement) | two joins share a refinement tag iff their `FilteredRelation`s are `==` (`query_utils.py:314-321`); distinct conditions ⇒ distinct tags |
| `reuse` (`None` or a set of aliases) | `reuse_all: bool` + `reuse_mask: List[bool]` | `reuse is None` ≙ `reuse_all=True`; otherwise `reuse_all=False` and `reuse_mask[i]` ≙ (slot i's alias ∈ `reuse`) |
| `j == join` (`Join.__eq__`) | `matches_default` (`base[i]==jb and frel[i]==jf`) | full-identity equality incl. `filtered_relation` |
| `j.equals(join)` (`Join.equals`) | `matches_constrained` (`base[i]==jb`) | identity-minus-`filtered_relation` equality |

`self.alias_map` is iterated in insertion order; only the existence of a
reuse-eligible match (not which one) determines whether a NEW alias is created,
which is the single observable this bundle pins. The downstream choice of *which*
matching alias to reuse (`table_alias` vs most-recent) is unchanged by the patch
and not modeled.

## 3. Callee provenance — no consumed axioms

This bundle consumes **no `@ContractOnly` axiom.** The operation the patch
changes is the *equality predicate* used to decide alias reuse, which is pure
integer/tuple equality over the `Join.identity` tuple — fully expressible in
Nagini. It is therefore modeled **deeply** (`matches_default` /
`matches_constrained`, the `Forall` over slots in `no_eligible_match`), not
behind an axiom.

The one external fact the deep model rests on is a **type-refinement (R)**, not
an axiom: that the real `Join.__eq__` compares the *full* identity tuple
(including `filtered_relation`) while `Join.equals` compares
`identity[:-1]` (excluding it). This is read directly off
`datastructures.py:147-166`:

```python
@property
def identity(self):
    return (self.__class__, self.table_name, self.parent_alias,
            self.join_field, self.filtered_relation)
def __eq__(self, other):
    return self.identity == other.identity          # includes filtered_relation
def equals(self, other):
    # Ignore filtered_relation in equality check.
    return self.identity[:-1] == other.identity[:-1]  # excludes it
```

`axiom_check.py` (G-AX) executes a faithful stand-in of this real `Join` class
and asserts, over boundary + fuzz join configurations, that
`(j == join)` ⇔ `matches_default` and `j.equals(join)` ⇔ `matches_constrained`
under the interning bijection of §2 — i.e. that the deep model's two predicates
agree with the real `Join` semantics. stdlib-only; exit 0 iff sound.

The pre-patch repo behaviour the change removes (for the refinement audit): in
`Query.join`, the default `reuse_aliases` comprehension used `j.equals(join)`
(`query.py:1027-1031`), which ignores `filtered_relation`; the patch switches the
default branch to `j == join` (full identity) and adds the constrained branch
gated by `reuse_with_filtered_relation`. The plumbing hunks
(`build_filter`, `build_filtered_relation_q`, `setup_joins` threading the
`reuse_with_filtered_relation` keyword) route a `FilteredRelation`'s own
sub-filter joins through the constrained branch; they are R-refinements of the
flag thread, covered in refinement.md §B.
