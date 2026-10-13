# refinement.md — django__django-15128

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_relabel_map` impl region, plus the `disjoint_by_floor` proof lemma)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's `Ensures`;
**A-reference**, a deep model validated == the real operation by axiom_check.py
/ G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`,
confirmed with `git apply --check`, and is the real correctness oracle,
G-RESOLVE).

## A. The changed behaviour — building the alias relabel map

The gold patch's behavioural delta is concentrated in `Query.bump_prefix`'s
relabel step (driven by a new call in `Query.combine`). The relabel map maps
each current alias to a freshly generated alias; the safety invariant that map
must satisfy — asserted one call deeper in `Query.change_aliases` — is that the
map's KEY set and VALUE set are disjoint.

Gold hunks (`django/db/models/sql/query.py`):

```
# combine(): pre-bump the rhs into a fresh prefix, keeping the shared base alias
+        initial_alias = self.get_initial_alias()
+        rhs.bump_prefix(self, exclude={initial_alias})
         ...
-        # Base table must be present in the query - this is the same table ...
-        self.get_initial_alias()

# bump_prefix(): gains an `exclude` parameter; the change_map comprehension
# skips excluded aliases
-    def bump_prefix(self, outer_query):
+    def bump_prefix(self, other_query, exclude=None):
         ...
+        if exclude is None:
+            exclude = {}
         self.change_aliases({
             alias: '%s%d' % (self.alias_prefix, pos)
             for pos, alias in enumerate(self.alias_map)
+            if alias not in exclude
         })

# change_aliases(): comment-only, documenting the existing disjointness assert
         assert set(change_map).isdisjoint(change_map.values())
```

Model function: `build_relabel_map(aliases, new_ns, excluded)`.

| # | model.py impl op (`build_relabel_map`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `aliases: List[int]` | `enumerate(self.alias_map)` — the ordered alias keys | R | ordered `alias_map` (dict, insertion order) ↔ ordered `List[int]`; alias `str` ↔ `int` encoding (mapping.md §2). |
| A2 | param `new_ns: int`, with `aliases[k] < floor_of(new_ns)` required | the bumped `self.alias_prefix` (chosen not to clash) | R | a fresh prefix letter ↔ a namespace integer whose region floor is above every current alias; "prefix bumped so it differs" ↔ `new_ns` region disjoint from (above) the current aliases (mapping.md §2). |
| A3 | param `excluded: int` | `exclude={initial_alias}`, `initial_alias = self.get_initial_alias()` | R | the single kept base alias ↔ `excluded`; `alias not in exclude` (set of one) ↔ `aliases[pos] != excluded`. |
| A4 | loop `t = fresh_alias(new_ns, pos); targets.append(t)` | `'%s%d' % (self.alias_prefix, pos)` (the dict-comprehension VALUE) | R + I | `fresh_alias(new_ns, pos) = new_ns*BASE + pos` ↔ `'<new_prefix><pos>'`; `enumerate` ordinal `pos` is identical; the value's namespace is `new_ns` (mapping.md §2). |
| A4b | postcondition: `Forall j: targets[j] == fresh_alias(new_ns, j)` | the comprehension VALUE is `'%s%d' % (self.alias_prefix, pos)` keyed on the `enumerate` ordinal `pos` | R | pins each position's target to the per-ordinal fresh value, so distinct positions get distinct values — the comprehension is **injective** by construction (`enumerate` gives a distinct `pos` per alias). This forbids collapsing distinct source aliases onto one target value (which would silently merge joins / break the SQL even though key/value disjointness still held). `new_ns*BASE + j` is a grounded structural function of the input namespace + ordinal position (directive 8), not an opaque oracle. |
| A5 | `if aliases[pos] != excluded: is_source.append(1) else: is_source.append(0)` | `if alias not in exclude` (the comprehension guard selecting which aliases become KEYS) | R + I | comprehension key-membership ↔ `is_source==1`; `not in exclude` (single-element set) ↔ `!= excluded`. **This is the discriminating delta** the gold patch adds. |
| A6 | postcondition: `(is_source[k]==1) == (aliases[k] != excluded)` | the net effect of the `if alias not in exclude` guard: the excluded base alias is NOT a key (kept present and unchanged), every other alias IS a key | R | index-level biconditional faithful to the comprehension's membership filter. |
| A7 | postcondition: `Forall k,j: aliases[k] != targets[j]` (proved by `disjoint_by_floor`) | the obligation `assert set(change_map).isdisjoint(change_map.values())` in `change_aliases` (`query.py:849`) | R | sources are the current aliases (KEYS), targets the VALUES; `aliases[k] != targets[j]` for all k,j ⟹ KEY set ∩ VALUE set = ∅, i.e. `isdisjoint` (mapping.md §2). Holds because every source < `floor_of(new_ns)` ≤ every target. |

The discriminating content of the change — keep the shared base alias OUT of
the relabel map (`if alias not in exclude`) so the map's keys/values stay
disjoint and the base alias survives the merge — lives in step **A5/A6**. The
pre-patch `bump_prefix` had no `exclude` filter, so it relabelled EVERY alias
including the base; `model_prepatch.py` reproduces that (`is_source.append(1)`
unconditionally) and **fails** the postcondition/invariant
`(is_source[k]==1) == (aliases[k] != excluded)` whenever the excluded alias is
present — exactly the spec sensing the change (G-DIFF). The F2P
`test_conflicting_aliases_during_combine` is the matching observation: `qs1 | qs2`
must not raise the `AssertionError` and must yield the same rows as `qs2 | qs1`.

## B. The deep model is an A-reference, not a consumed axiom

The changed operation (the relabel-map construction) is modelled **deeply** —
spelled out in `build_relabel_map`'s impl region, with disjointness discharged
by the pure-arithmetic `disjoint_by_floor` lemma. There is **no `@ContractOnly`
axiom** the proof consumes (the `axioms` region is empty). Instead the deep
model is validated **== the real construction** out-of-band by `axiom_check.py`
(G-AX), which reproduces the gold dict-comprehension verbatim and checks both
clauses (source-flag biconditional + key/value disjointness) plus the pre-patch
discriminator on boundary + 20000 fuzz inputs (mapping.md §3.1). This bundle
ships **zero dead axioms** and **zero A-consumed** rows.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I (with the whole construction an **A-reference**
validated by G-AX). The operation that genuinely changed — adding the
`exclude` filter so the base alias is kept out of the relabel map — is modelled
deeply (A5/A6), not hidden behind an axiom about the function under change.

## D. verify(model) ⇒ resolved

`build_relabel_map` verifies only if (A6) the kept base alias is excluded from
the relabel sources while every other alias is a source, only if (A4b) each
position `j` maps to the per-ordinal fresh value `fresh_alias(new_ns, j)` (so
the map is injective — distinct aliases never collapse onto one value), and only
if (A7) the source and target sets are disjoint (the `change_aliases`
`isdisjoint` assertion). The A4b clause is load-bearing for `verify ⇒ resolved`:
without it a non-injective map (e.g. every value `floor_of(new_ns)`) would
satisfy disjointness yet collapse distinct joins and fail the F2P test
(`test_conflicting_aliases_during_combine`, which checks `qs1 | qs2` yields the
same rows as `qs2 | qs1`); pinning the value to `new_ns*BASE+j` — a grounded
structural function of the input position, not an oracle (directive 8) — forces
the gold's `enumerate`-keyed injective comprehension. By R (alias `str` ↔ `int`
encoding; ordered `alias_map` ↔ `List[int]`; fresh prefix ↔ a fresh namespace
above the current aliases; `not in exclude` ↔ `!= excluded`;
`'%s%d' % (prefix,pos)` ↔ `new_ns*BASE+pos`) the verified construction equals
the gold patch's
`{alias: '%s%d' % (prefix, pos) for pos, alias in enumerate(alias_map) if alias
not in exclude}` on the tested inputs; by G-AX the deep model equals the real
construction (A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The one trust point is refinement fidelity (this
document, G-EQ) plus the A-reference soundness check (G-AX); there is **no
consumed-axiom trust point**.
