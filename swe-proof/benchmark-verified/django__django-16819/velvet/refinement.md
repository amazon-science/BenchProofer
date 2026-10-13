# refinement.md — django__django-16819

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reduceAddIndex` `do` block plus the pure `removesAddedIndex` predicate and the
`Reduction` / `NextOp` carriers) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** /
**A-reference** (none in this bundle), or **I** (identical concrete op). EVERY
step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The added combination rule — `AddIndex.reduce` (`models.py:864`)

Gold hunk (added method):
```
+    def reduce(self, operation, app_label):
+        if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
+            return []
+        return super().reduce(operation, app_label)
```

| # | Solution.lean impl op (`reduceAddIndex`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `addedName : List Char` | `self.index.name` (the added index's name) | R | `str` ↔ `List Char` (mapping.md §2). The only attribute of `self` the new branch reads. |
| A2 | param `next : NextOp` | the `operation` argument | R | the following operation projected to exactly what the guard consults: `NextOp.removesIndex name` ↔ `isinstance(operation, RemoveIndex)` with `operation.name = name`; `NextOp.other` ↔ a non-`RemoveIndex` (mapping.md §2). |
| A3 | `removesAddedIndex addedName next` | `isinstance(operation, RemoveIndex) and self.index.name == operation.name` | I | the guard is modeled **deeply**: the `match` on `NextOp` IS the `isinstance` test, and `decide (name = addedName)` IS the `self.index.name == operation.name` string equality. Note the gold guard compares **only the index name** (not the model name); `removesAddedIndex` faithfully does likewise. |
| A4 | `if removesAddedIndex … then return Reduction.cancel` | `if …: return []` | R + I | the taken branch returns the empty replacement; `[]` ↔ `Reduction.cancel` (mapping.md §2). Concrete control flow identical. |
| A5 | `else return inheritedOutcome` | `return super().reduce(operation, app_label)` | R + I | the fall-through returns the ordinary inherited decision; `super().reduce` (`Operation.reduce`, UNCHANGED) ↔ free input `inheritedOutcome` (mapping.md §2/§3). No claim is made about its value, so the clause holds for every `inheritedOutcome`. |

## B. The discriminating content — what the spec senses

The bug: pre-patch, `AddIndex` had **no** `reduce` override, so combining an
`AddIndex` with a following operation always fell through to the base
`Operation.reduce` decision — even when that following operation removes the very
index just added. Hence an `AddIndex(idx)` immediately followed by
`RemoveIndex(idx)` was **not** optimized away; the redundant add/remove pair
survived in the migration plan. Post-patch, that exact pairing cancels and the
plan keeps nothing in its place.

The frozen spec pins the result to
`if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome`.
`Solution_prepatch.lean` reproduces the pre-patch skeleton (always
`return inheritedOutcome`, the inherited fall-through) and **fails** verification
on exactly the clause

```
⊢ inheritedOutcome = if removesAddedIndex addedName next = true
                     then Reduction.cancel else inheritedOutcome
```

(G-DIFF, unsolved goal at `ensures_1`). The two states diverge precisely when
`removesAddedIndex addedName next = true` (the following op removes the added
index) **and** `inheritedOutcome ≠ Reduction.cancel` — the redundant-pair case
the F2P `test_add_remove_index` exercises (it asserts `[AddIndex, RemoveIndex]`
optimizes to `[]`). When `inheritedOutcome` happens to be `cancel` the two
coincide; the `inherited tag` carrier keeps the inherited outcomes an open domain
so this coincidence is genuinely partial, not forced.

This is one independently-fixed behaviour at a single site; one
`Solution_prepatch.lean` suffices.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — adding the
special-case cancellation rule — is modeled **deeply** (the `removesAddedIndex`
predicate over the explicit `NextOp` carrier and the `if … then cancel else …`
decision, A3/A4/A5), not hidden behind an axiom about a function under change.
There are **no consumed axioms and no A-references**: the only callee
(`super().reduce` / `Operation.reduce`) is UNCHANGED by the patch and is
abstracted as a free input with no relied-on property (mapping.md §3), so nothing
requires G-AX validation.

## D. verify(Solution) ⇒ resolved

`reduceAddIndex` verifies only if its result equals the exact modeled decision:
`cancel` when the following operation removes the added index (A3/A4) and the
unchanged inherited decision otherwise (A5). By R (the `str ↔ List Char`,
`RemoveIndex`-test ↔ `NextOp`, `[]` ↔ `cancel`, `super().reduce` ↔
`inheritedOutcome` bijections, mapping.md §2) the verified method equals the
gold-patched `AddIndex.reduce` on every input, and by G-CONF the R/I
transliteration of the guard + decision agrees with the real patched
`AddIndex.reduce` on ≥10⁵ fuzzed pairings (seed 16819, 0 disagreements).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The sole
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms
(G-AX skips).
