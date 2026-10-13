# refinement.md — operation correspondence (scikit-learn__scikit-learn-14053)

Maps every op in `implementation_featureNamesByNode` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python is the list comprehension
```
feature_names_ = [feature_names[i] if i != _tree.TREE_UNDEFINED
                  else None for i in tree_.feature]
```
modeled deeply: map each index `i` of `tree_.feature` to a label, emitting the
neutral `none` when `i` is the leaf sentinel and the in-range lookup otherwise.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut acc := []` | the comprehension building its output list | I | concrete empty-output init |
| 2 | `for i in features do` | `for i in tree_.feature` | I | per-entry iteration over the index list (`tree_.feature` ↔ `List Int`, mapping.md) |
| 3 | `if i ≠ sentinelIndex then acc ++ [featureNames[i.toNat]?] else acc ++ [none]` | `feature_names[i] if i != _tree.TREE_UNDEFINED else None` | R | the changed conditional. `_tree.TREE_UNDEFINED = -2` ↔ `sentinelIndex = -2`. `feature_names[i]` (valid only for in-range internal indices) ↔ total `featureNames[i.toNat]?` returning `some name`; `None` ↔ `none`. The R bijection is exact on every in-range/sentinel input (G-CONF). |
| 4 | `return acc` | the comprehension result `feature_names_` | I | identity return of the built list |

No A-consumed or A-reference rows: the changed conditional is modeled directly
in the impl and pinned by `problem_spec` via `featureNamesSpec`; the proof
discharges it structurally. No UNCHANGED callee property is assumed (axioms
region empty → `axiom_check.py` is a skip stub). No changed-inexpressible op.

## Discriminating clause / G-DIFF
The discriminator is row 3: the sentinel guard. The prepatch impl drops the
guard (`acc := acc ++ [featureNames[i.toNat]?]` unconditionally) — the actual
pre-patch bug (the unconditional `feature_names[i]` that raises `IndexError`
on a leaf and, in the total Lean model, wrongly resolves a leaf entry `-2` to
`featureNames[0]?` instead of `none`). Its `correct_featureNamesByNode` cannot
close against the frozen `problem_spec_featureNamesByNode` (which pins
`featureNamesSpec`, i.e. `none` at sentinel entries): on input
`featureNames=["first"], features=[0,-2,-2]` the buggy impl yields
`[some "first", some "first", some "first"]` while the spec demands
`[some "first", none, none]`. That is the G-DIFF signal.

## Python total-ness note (R soundness)
`feature_names[i]` is total in Python only because the earlier
`len(feature_names) != tree_.n_features` ValueError guard ensures every
internal-node index is in range, and (post-patch) leaf entries never reach the
lookup. The Lean R model uses the total `xs[·]?`, which is well-defined on every
input with no precondition; on an in-range internal index it returns `some`,
faithfully refining the Python lookup. G-CONF restricts fuzz to the realistic
shape (in-range internal indices + `-2` sentinels) per mapping.md.
