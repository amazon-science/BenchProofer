# refinement.md — django__django-13158

Maps every operation in `implementation_makeEmpty` to its `patch.diff`
counterpart in `Query.set_empty` (`django/db/models/sql/query.py:1778`). Tags:
**R** type refinement, **A-consumed** proof uses a callee axiom, **A-reference**
op left as the real repo callee in G-CONF, **I** identical concrete op.

## Patch (the two gold hunks)
```python
# hunk 1 — Query.clone (query.py:308, post-patch): deep-copy the combined sub-queries
obj.combined_queries = tuple(query.clone() for query in self.combined_queries)

# hunk 2 — Query.set_empty (query.py:1778-1781, post-patch): recurse into them
def set_empty(self):
    self.where.add(NothingNode(), AND)
    for query in self.combined_queries:   # <-- the fix
        query.set_empty()
```
The headline behavior change is hunk 2: forcing a query empty must force every
combined sub-query empty too, or the combined result still returns those
sub-queries' rows ("`none()` on combined queries returns all results"). Hunk 1 is
the aliasing-safety prerequisite (see "Aliasing note").

## Modeling decision
The observable subject is a query TREE. `set_empty()` mutates `self` and, post-fix,
each node in `self.combined_queries`, recursively. We model a `Query` as the
inductive `Query.mk (selfEmpty : Bool) (combined : List Query)`, carrying the one
touched fact per node (`selfEmpty` — whether its own where is forced to match
nothing) plus its combined children.

The operation returns the rebuilt tree. The empty-result guarantee is
`YieldsNothing` (own where empty AND every combined sub-query yields nothing,
recursively) — exactly what makes `none()` on a combined query actually empty. The
frame component `toShape result = toShape q` pins that the operation flips markers
only; it neither adds nor drops a sub-query at any level.

## Aliasing note (hunk 1 — why it needs no separate impl op)
Hunk 1 deep-copies `combined_queries` in `clone()` so that forcing the CLONE
empty (the `none()` flow does `clone = self._chain(); clone.query.set_empty()`)
does not mutate the ORIGINAL queryset's shared sub-query objects. It is a fix to
Python's reference aliasing: pre-fix, the clone shared the same
`combined_queries` tuple *elements*, so `set_empty`'s new recursion would have
corrupted the source. Lean is referentially transparent — there is no aliasing
and `implementation_makeEmpty` returns a fresh tree by construction, so the
clone-deep-copy is automatically satisfied and needs no separate modeled op. The
behavior the F2P test observes (`qs3.none()` is empty AND `qs3` still returns its
four rows) is the conjunction of: recursion makes `.none()` empty (hunk 2,
modeled), and the source `qs3` is unharmed (hunk 1, automatic under no-aliasing).
This is recorded so the proof/EQ agents do not look for a missing op.

## Operation correspondence
| # | Lean op (`implementation_makeEmpty`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `\| .mk _ combined => … return Query.mk true subs` (set this node's `selfEmpty := true`) | `self.where.add(NothingNode(), AND)` | R | "force own where empty" ↔ `selfEmpty := true`; `where`/`NothingNode` machinery refined to the single boolean (mapping.md). |
| 2 | `for sub in combined do subs := subs ++ [implementation_makeEmpty sub]` | `for query in self.combined_queries: query.set_empty()` | R + I | the added recursion: I (the `for` loop over the children is the same control flow) over an R carrier (`combined_queries` tuple ↔ `List Query`); the self-call ↔ `query.set_empty()`. This IS the modeled fix — spelled out, never axiomatized (§3). |
| — | (deep-copy of `combined_queries` in `clone`) | hunk 1 | — | aliasing prerequisite; automatic under Lean's no-aliasing model (see note). Not a modeled op. |

## R/I legs ⇒ G-CONF
Both ops are R/I (no A-tagged callee). `conformance_check.py` builds the Python
R/I shadow (`shadow_make_empty`: rebuild the node with own-empty true and the
recursion mapped over `combined`) and diffs it over ≥10⁵ fuzzed random trees
against an oracle = the faithful post-patch `set_empty` semantics applied to the
same tree model, comparing the resulting "is the whole tree empty?" predicate AND
the preserved shape. `conf_skip = false`: the impl region has genuine R/I content
(the recursion is the fix).

## No A-consumed / A-reference row
The proof consumes no property of any unchanged callee (the per-node "force empty"
is modeled deeply as `selfEmpty := true`; the recursion is a self-call). So
`meta.json axioms = []` and `deep_model_references = []`. There is no
`opaque`/`axiom` in `Solution.lean`; `axiom_check.py` is a skip stub.

## F2P alignment
`test_union_none` builds `qs3 = qs1.union(qs2)` (a node with two combined
sub-queries) and asserts (a) `qs3.none()` is the empty sequence `[]` and (b)
`qs3` itself still returns `[0,1,8,9]`. Assertion (a) is the discriminating clause
`YieldsNothing result`: the prepatch impl flips only the top node's `selfEmpty`
and leaves the two combined sub-queries unmarked, so `YieldsNothing` cannot be
discharged for them — the real bug (the combined result still yields those rows).
Assertion (b) is the aliasing half (hunk 1), automatic under the model. `patch.diff`
(gold verbatim) makes the harness resolve.
