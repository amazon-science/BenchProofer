# refinement.md — scikit-learn__scikit-learn-14053

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildLabels` `do` block and the deep `labelsOf`/`labelOne` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (empty) A set and this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — the `feature_names_` comprehension (`sklearn/tree/export.py:893`)

Gold hunk:
```
- feature_names_ = [feature_names[i] for i in tree_.feature]
+ feature_names_ = [feature_names[i] if i != _tree.TREE_UNDEFINED
+                   else None for i in tree_.feature]
```

| # | Solution.lean impl op (`buildLabels`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `names : List Name` | `feature_names` (the comprehension's name table) | R | `list[str]` ↔ `List Name` carried by slot index (mapping.md §2). G-CONF bridges `feature_names[k]` ↔ slot `k`. |
| 2 | param `refs : List Int` | `tree_.feature` (iterated `for i in tree_.feature`) | R | int array ↔ `List Int`; iteration order ↔ list order (mapping.md §2). |
| 3 | param `sentinel : Int` | `_tree.TREE_UNDEFINED` (`= -2`) | R | the module constant carried as a free `Int`; the proof holds for any sentinel, so no concrete magnitude is named (mapping.md §2, de-leak). |
| 4 | `labelOne names sentinel i = if i = sentinel then none else names[i.toNat]?` | the per-element body `feature_names[i] if i != _tree.TREE_UNDEFINED else None` | I | identical guarded resolution: sentinel ⇒ `None`/`none` WITHOUT indexing; otherwise index the table. `names[i.toNat]?` ↔ `feature_names[i]` under the precondition (step 6). Transliterated 1:1 by G-CONF. |
| 5 | `out = labelsOf names sentinel refs` — the per-reference resolution of each entry in order, computed by the backward `while` fold | the comprehension `[ … for i in tree_.feature]` | I | the comprehension is exactly the in-order map of the per-element body; the backward fold (`labelsOf` front-recursive, prepending) computes that same list. Concrete, transliterated by G-CONF. |
| 6 | `require ∀ i ∈ refs, i ≠ sentinel → 0 ≤ i ∧ i.toNat < names.length` | (implicit domain invariant of a fitted tree) | R | a non-sentinel `tree_.feature` entry is a real split-feature index, hence a valid `feature_names` position; this is the property that makes `names[i.toNat]? = some i` ↔ `feature_names[i]`. The sentinel carries NO index obligation — precisely why the fixed code must not index it (mapping.md §2.1). |

## Why the fix, and why the prepatch fails

Discriminating content of the change: a **sentinel** reference must resolve to
`none` **without indexing** the table. Pre-fix the comprehension indexed every
reference (`feature_names[i]` for all `i`), so a sentinel `-2` became
`feature_names[-2]` — `IndexError` when `len(feature_names) < 2` (the
single-feature case the issue reports), or a silently-wrong name otherwise.

`Solution_prepatch.lean` reproduces exactly that: its loop body computes
`names[i.toNat]?` for every reference with no sentinel guard. It **fails**
`out = labelsOf names sentinel refs` (G-DIFF) at the discriminating goal
`names[(refs[idx-1]).toNat]? = labelOne names sentinel (refs[idx-1])` — which is
false precisely when `refs[idx-1] = sentinel` (LHS indexes, RHS is `none`).

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the guarded
per-element resolution — is modeled **deeply and concretely** (`labelOne`'s
`if i = sentinel then none else names[i.toNat]?`, step 4), not hidden behind an
axiom. There is **no consumed axiom and no A-reference**: the comprehension
calls no unchanged repo function (mapping.md §3). `conf_skip = false`.

## verify(Solution) ⇒ resolved

`buildLabels` verifies only if its output equals the exact per-reference
resolution with sentinel ⇒ `none`-without-indexing (steps 4–5). By R
(`feature_names ↔ names` by slot, `tree_.feature ↔ refs`, `TREE_UNDEFINED ↔
sentinel`, `feature_names[i] ↔ names[i.toNat]?` under the step-6 domain
invariant) the verified resolver equals the patched comprehension on every
fitted-tree input; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs incl. the single-feature / leaf-node boundary.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points (the only plan-§1.1 trust point left is refinement
fidelity: this doc, G-EQ + G-CONF).
