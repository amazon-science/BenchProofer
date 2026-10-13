# mapping.md — django__django-15554

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 59ab3fd0e9e606d7f0f7ca26609c06ee679ece97`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the (only) callee semantics relied on.

Repo file under change: `django/db/models/sql/query.py` (and the comparison
semantics of `django/db/models/sql/datastructures.py`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `computeEligible (registry, req, allowed, restricted)` | the `reuse_aliases` candidate computation inside `Query.join` — `django/db/models/sql/query.py:1014` (body lines 1027-1031) | the modeled changed function: which existing entries the requested join may share |
| `JoinDesc.structKey` | `identity[:-1]` of a `Join`/`BaseTable` = `(class, table_name, parent_alias, join_field)` — `datastructures.py:147` (`Join.identity`), compared by `Join.equals` (`datastructures.py:164`) | the structural identity that `.equals(...)` compares |
| `JoinDesc.refineTag` | `identity[-1]` = the `filtered_relation` of a `Join` — `datastructures.py:153` | the trailing identity component that `==` (`__eq__`, `datastructures.py:156`) includes but `.equals(...)` drops |
| `matchesStructural a b` | `Join.equals(a, b)` = `a.identity[:-1] == b.identity[:-1]` — `datastructures.py:164` | structural match (refinement tag ignored) |
| `matchesExact a b` | `Join.__eq__(a, b)` = `a.identity == b.identity` — `datastructures.py:156` | full match (refinement tag included) |
| `allowed : Option (List Nat)` | the `reuse` parameter of `Query.join` — `None` ⇒ all entries reusable, a set ⇒ only those aliases | the reuse set |
| `restricted : Bool` | the `reuse_with_filtered_relation` parameter of `Query.join` (added by the patch) — `query.py:1014` | restricted-reuse mode flag |

The unchanged downstream selection (`reuse_aliases[-1]` vs `join.table_alias`,
`ref_alias`, and new-alias creation via `table_alias(create=True)`,
`query.py:1032-1054`) is NOT modeled: it is identical pre/post-patch and operates
on the candidate list `computeEligible` produces; see refinement.md §B (tagged I).
The flag-threading sites `build_filter` / `setup_joins` /
`build_filtered_relation_q` (`query.py:1331,1730,1578,1843`) only pass the new
flag down and are R/I plumbing (refinement.md §B).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.alias_map` — an insertion-ordered dict `{alias: Join}` | `registry : List (Nat × JoinDesc)` | each `(alias, join)` ↔ `(id, desc)`; dict insertion order ↔ list order; the candidate list preserves that order (the real comprehension iterates `alias_map.items()`) |
| an alias string (dict key) | `Nat` (entry id) | distinct alias strings ↔ distinct `Nat`s; only equality/membership is observed |
| `Join.identity[:-1]` tuple | `JoinDesc.structKey : Nat` | distinct structural identities ↔ distinct `Nat`s; only equality is observed (`==` on the tuple ↔ `==` on the `Nat`) |
| `Join.filtered_relation` (a `FilteredRelation` or `None`) | `JoinDesc.refineTag : Nat` | `None` and each distinct `FilteredRelation` (by `FilteredRelation.__eq__`, `query_utils.py:314`) ↔ distinct `Nat`s; only equality is observed |
| `reuse` (`None` or a `set` of aliases) | `allowed : Option (List Nat)` | `None` ↔ `none`; a set `S` ↔ `some L` with `set(L) = {bijection(a) : a ∈ S}`; `a in reuse` ↔ `allowed`-membership; Python truthiness `and reuse` (empty set falsy) ↔ `restrictedMode` requiring a non-empty list |
| `reuse_with_filtered_relation` (`bool`) | `restricted : Bool` | identity |

Only equality and membership of the keys/ids are ever observed, so abstracting
each opaque identity to a `Nat` is faithful: any value distinction the real
`==`/`equals`/`in` can make is reproduced by `Nat` equality, and no other
property of these objects is read by the modeled computation.

## 3. Callee provenance — the comparison semantics (checked by G-AX)

There are **no axiomatized callees** and **no deep-model reference to an
unchanged callee**: the changed computation (`reuse_aliases`) is modeled
**deeply** by `eligibleEntries`, and the only repo semantics it leans on are the
two comparison methods `Join.equals` and `Join.__eq__`, modeled directly by
`matchesStructural` / `matchesExact`.

`axiom_check.py` (G-AX) validates the **type bijection of §2** against the real
`Join` objects: it builds real `Join`/`BaseTable` instances over fuzzed
`(table_name, parent_alias, join_field, filtered_relation)` tuples and asserts

* `Join.equals` agrees with `matchesStructural` (equal iff `structKey` equal,
  i.e. `filtered_relation` ignored), and
* `Join.__eq__` agrees with `matchesExact` (equal iff `structKey` **and**
  `refineTag` equal, i.e. `filtered_relation` included),

under the §2 mapping. This is the soundness obligation for the modeling: it
confirms `equals` drops the refinement tag while `==` keeps it (the property the
whole spec turns on). stdlib + django import only; exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15554`**. The R/I shadow
it builds transliterates `eligibleEntries`/`entryEligible` (R/I-tagged ops) to
Python and diffs against an ORACLE that is the **post-patch `reuse_aliases`
comprehension verbatim**, evaluated over **real `Join` objects** (so the
`j.equals(join)` / `j == join` comparisons are the genuine repo methods), across
≥10⁵ fuzzed registries × requests × reuse-sets × flag values. Exit 0 iff zero
disagreements.
