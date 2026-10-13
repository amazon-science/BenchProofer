# refinement.md — django__django-15280

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`linkChildrenToParents` `do` block, the deep `resolveOne`/`resolvedSeq` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/deep-modelled callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reverse-relation linking loop — `get_prefetch_queryset`

Gold hunk (`django/db/models/fields/related_descriptors.py:646-648`, inside the
reverse-FK / reverse-O2O prefetch manager):
```
  for rel_obj in queryset:
-     instance = instances_dict[rel_obj_attr(rel_obj)]
-     setattr(rel_obj, self.field.name, instance)
+     if not self.field.is_cached(rel_obj):
+         instance = instances_dict[rel_obj_attr(rel_obj)]
+         setattr(rel_obj, self.field.name, instance)
```

| # | Solution.lean impl op (`linkChildrenToParents`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `children : List Child` | `queryset` (the prefetched child rows, in iteration order) | R | each child row ↔ a `Child`; iteration order ↔ list order (mapping.md §2). G-CONF bridges the two observed projections. |
| A2 | `Child.key`, consulted via `lookup c.key` | `rel_obj_attr(rel_obj)` then `instances_dict[...]` | R + I | `rel_obj_attr` is the unchanged local-related-value getter; `instances_dict` is the unchanged `{instance_attr(inst): inst}` map. Both fold into `lookup : Nat → Nat` (mapping.md §2,§3). The dict-lookup op itself is **I** (concrete `lookup c.key`). |
| A3 | `Child.existingParent`, tested by the `match … some p / none` | `self.field.is_cached(rel_obj)` (the **added guard**) | R + I | `is_cached(rel_obj) == True` (with cached parent `p`) ↔ `existingParent = some p`; `== False` ↔ `none` (mapping.md §2). The guard `if not is_cached` is the **I** op: it selects, per child, between keeping the cached parent and writing the looked-up one. |
| A4 | per child, `parent := match existingParent with some p => p | none => lookup key`; `result := parent :: result` | `setattr(rel_obj, self.field.name, instance)` executed only when `not is_cached` | I | the deep model `resolveOne` IS the patched loop body: a cached child keeps its parent (no setattr), an uncached child is set to the looked-up instance. The backward `while` fold accumulates these in batch order (`resolvedSeq`). |
| A5 | `out` returned (`List Nat`) | the post-loop reverse relation `getattr(rel_obj, field.name)` of each child | R | the observable the F2P test checks: which parent each child points at after the loop (and hence whether `is_cached` stays `True` and no DB query fires). mapping.md §2. |

Discriminating content of the change — a child that ALREADY carries a parent
association keeps it, rather than being overwritten by the grouping-key lookup —
lives in `resolveOne`'s `some p => p` branch (model) ⇔ the `if not is_cached`
guard skipping `setattr` (real). The pre-patch loop wrote `lookup c.key` onto
EVERY child unconditionally; `Solution_prepatch.lean` reproduces that
(`parent := lookup c.key`) and **fails** `out = resolvedSeq lookup children` at
exactly the goal
`lookup c.key = match c.existingParent with | some p => p | none => lookup c.key`
— i.e. it diverges precisely on a child whose `existingParent = some p` with
`p ≠ lookup c.key`, the nested-prefetch case the issue reports (G-DIFF).

## B. No axioms / no A-reference / no G-AX

The patch adds a control-flow guard and introduces no new external computation
whose contract the proof must assume. `is_cached`, `rel_obj_attr`/`get_local_related_value`,
and the `instances_dict` map are all UNCHANGED by the patch and enter as the free
inputs `children.existingParent`, `children.key`, and `lookup`. The spec is
universally quantified over them and claims nothing about how any is computed, so
there is nothing to validate against a real callee: no consumed axiom, no
A-reference deep model of an external callee, no `axiom_check.py`, no G-AX
(precedent: django__django-16631). mapping.md §3.

## B2. Termination semantics (spec-strengthening, audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`), not
`"partial"`. A prior audit (G-EQ / G-PANEL-1) exhibited a same-spec
counterexample under partial correctness: a diverging implementation (a
non-terminating loop inserted into the linking loop) verified vacuously,
because partial correctness constrains only terminating executions — and its
translated patch hangs the real test suite (nonterm-capture run: test timed out
after 120 s), so it does not resolve (verify ⇏ correct). The real patched loop
(`for rel_obj in queryset: …`) is a bounded iteration over the fetched batch
that always terminates, so total correctness is the faithful semantics: it
rejects every diverging impl (a loop without a provable `decreasing` measure is
unprovable under total semantics), while the verified impl here carries the
measure `decreasing i` (the backward index strictly decreases each step). The
`set_option`/`open` lines are part of the frozen spec view shared byte-identical
by both twins.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — adding the
"keep a pre-existing association" guard to the per-child link — is modeled
**deeply** (`resolveOne`'s `match existingParent`, step A4), not hidden behind an
axiom about the function under change. There is no consumed axiom anywhere in the
bundle.

## D. verify(Solution) ⇒ resolved

`linkChildrenToParents` verifies only if its output equals, per child, the cached
parent when one is present and the looked-up parent otherwise (A4), in batch
order (`resolvedSeq`). By R (`queryset ↔ List Child`, `is_cached ↔ Option`,
`instances_dict ↔ lookup`, the resulting relation ↔ `out`) the verified routine
equals the patched loop's per-child outcome on the modeled inputs; by G-CONF the
R/I transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed `(children, lookup)` batches. There are no A legs (B). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point of
plan §1.1 reduces here to refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point because there are no axioms.
