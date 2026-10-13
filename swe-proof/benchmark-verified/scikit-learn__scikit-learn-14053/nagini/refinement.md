# refinement.md — scikit-learn__scikit-learn-14053

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_node_names` impl region and the deep `built_seq` / `in_domain`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed** / **A-reference**),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## The change site — `export_text`'s `feature_names_` construction

Gold hunk (`sklearn/tree/export.py:892-895`):
```
  if feature_names:
-     feature_names_ = [feature_names[i] for i in tree_.feature]
+     feature_names_ = [feature_names[i] if i != _tree.TREE_UNDEFINED
+                       else None for i in tree_.feature]
  else:
      feature_names_ = ["feature_{}".format(i) for i in tree_.feature]
```

The modeled function `resolve_node_names(names, feat)` is the
`if feature_names:` branch (the only branch the change touches and the only one
the F2P test exercises — it passes `feature_names=['first']`).

| # | model.py impl op (`resolve_node_names`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `names: List[int]` | `feature_names` (list of name strings) | R | name strings ↔ `List[int]` identifiers; the report observes only which entry is selected, not its spelling (mapping.md §3). |
| 2 | parameter `feat: List[int]`, precondition `in_domain(ToSeq(names), ToSeq(feat))` | `tree_.feature` (per-node selector array) | R | numpy int array ↔ `List[int]`; the precondition is the documented structural domain of `tree_.feature` (valid index or leaf marker `-2`), mapping.md §2 — not a weakening. |
| 3 | the loop building `result` so that `ToSeq(result) == built_seq(ToSeq(names), ToSeq(feat))`, where `built_seq` maps an internal-node selector `s` to `names[s]` and the leaf marker `-2` (or any non-position selector) to `None` | the comprehension `[feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in tree_.feature]` | I (under R on the carriers) | concrete, identical control/data flow: per node, `i != TREE_UNDEFINED` ↔ `fi != -2` selects `feature_names[i]` ↔ `names[fi]`; otherwise `None` ↔ `None`. `built_seq` is the deep model of that comprehension's *result value* (mapping.md §4); the loop computes it node-by-node. `_tree.TREE_UNDEFINED == -2` (`sklearn/tree/_tree.pyx:64`). |
| 4 | result `List[Optional[int]]` returned | `feature_names_` (list, name-or-None per node) | R | `feature_names_[j]` ↔ `Result()[j]`; `None` ↔ `None`. Read downstream only at internal nodes (`export.py:930-931`), so the leaf placeholder is never displayed. |

## The discriminating content — totality at the leaf marker

The single behavioural defect the change repairs is the **out-of-range read of
the name table at the leaf marker**. In the model this is the index `names[fi]`
inside `built_seq` / the loop, guarded by `fi != -2 and 0 <= fi and fi < len(names)`.
The pre-patch comprehension `[feature_names[i] for i in tree_.feature]` reads
`feature_names[i]` for **every** node, including the leaf marker `i == -2`;
`feature_names[-2]` is in range only for a table of ≥ 2 names and raises
`IndexError` for a single feature — exactly the reported bug.

`model_prepatch.py` reproduces the pre-patch transcription (drop the leaf guard;
do `nm = names[fi]` unconditionally) and **fails** verification on the
precondition of `names[fi]` (the index `fi == -2` cannot be proven `>= 0`),
which is precisely the spec sensing the change (G-DIFF). The post-condition
`ToSeq(Result()) == built_seq(...)` and `len(Result()) == len(feat)` additionally
pin that internal nodes select the *correct* table entry and that leaves carry
the placeholder, so a verifying impl cannot select the wrong name or drop/duplicate
nodes (spec strength, directives 3-4).

## No kind-3, no axioms

Every step above is R or I. The one operation that *changed* — the per-node
name resolution — is modeled **deeply** (`built_seq`, spelled out in the `pure`
region, consumed by the verified loop), not hidden behind an axiom. There is
**no `@ContractOnly` callee**: the patched code uses only list indexing and a
conditional expression, all expressible directly in Nagini's fragment over the
refined `List[int]` carriers. Consequently there are no A-consumed and no
A-reference rows, and `axiom_check.py` carries no soundness trust point — it is
a lightweight executable cross-check that the deep model `built_seq` matches the
patched comprehension and that the pre-patch comprehension raises `IndexError`
on the reported single-feature input.

## verify(model) ⇒ resolved

`resolve_node_names` verifies only if (a) it never reads the name table out of
range (totality at the leaf marker — the bug) and (b) its result equals the
exact per-node fold `built_seq` (internal nodes → selected name, leaves → None).
By R (name↔identifier, array↔List, None↔None) and I (the identical guarded
per-node selection) the verified resolver equals the patched comprehension
`[feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in tree_.feature]`
on the tested inputs. The patched `feature_names_` is then consumed unchanged by
`print_tree_recurse`, which reads it only at internal nodes — so the F2P test
(`export_text(reg, feature_names=['first'])`, a single feature) no longer raises
and prints the correct names. The gold patch resolves (G-RESOLVE). There are no
trust points beyond refinement fidelity (this document, G-EQ); there are no
axioms (so G-AX is vacuous).
