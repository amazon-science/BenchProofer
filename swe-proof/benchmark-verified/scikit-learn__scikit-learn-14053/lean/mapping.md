# mapping.md — symbol binding & type bijection (scikit-learn__scikit-learn-14053)

## Modeled function
- **Lean** `implementation_featureNamesByNode : List String → List Int → List (Option String)`
- **Python** the per-node feature-label list built inside `export_text`
  (`sklearn/tree/export.py:892-894 @ 6ab8c86c`, the `if feature_names:` branch):
  ```
  feature_names_ = [feature_names[i] if i != _tree.TREE_UNDEFINED
                    else None for i in tree_.feature]
  ```
  The modeled operation is exactly this list comprehension: map the per-node
  feature-index array `tree_.feature` to a list of labels, emitting `None` for a
  node that does not split on any feature (a leaf). The comprehension's element
  type is therefore string-or-None.

## The sentinel
`tree_.feature[node]` holds a valid feature index `>= 0` for an internal
(splitting) node, and the constant `_tree.TREE_UNDEFINED = -2` for a leaf node
(verified: `sklearn/tree/_tree.pyx:64 TREE_UNDEFINED = -2`). The leaf sentinel is
modeled as the neutral Lean constant `leafFeatureSentinel : Int := -2`.

## Type bijection (used by G-CONF; G-AX is a skip — no consumed callee axiom)
| Python | Lean | notes |
|---|---|---|
| `feature_names` (list of str) | `List String` | the user-supplied names |
| `tree_.feature` (int array, values `>=0` or `-2`) | `List Int` | per-node feature index; `-2` marks a leaf |
| comprehension element `feature_names[i]` (str) | `featureNames[i.toNat]?` → `some name` | for a valid internal-node index `i >= 0`, `i.toNat = i` and the lookup is in range, so it is `some (the name)` |
| comprehension element `None` (leaf) | `none : Option String` | leaf node yields no label |
| output `feature_names_` (list str-or-None) | `List (Option String)` | `none` at leaf positions, `some name` at internal-node positions |

`feature_names[i]` is total in Python only because internal-node indices are
valid (`0 <= i < len(feature_names)` once the earlier
`len(feature_names) != tree_.n_features` ValueError guard has passed); leaf
nodes never reach the lookup post-patch. The Lean model uses the total
`List.get?` (`xs[·]?`), so it is well-defined on every input without a
precondition; for an in-range internal index it returns `some`.

## Callee provenance
No UNCHANGED callee is consumed. The changed operation is the comprehension
itself, modeled DEEPLY as `featureNameAt` mapped over the index list (refinement
row 2/3). The axioms region is empty; `axiom_check.py` is a skip stub.

## G-CONF fuzz seed
Pinned seed: **14053**. >=10^5 fuzzed inputs over index lists that oversample the
leaf sentinel `-2` and valid in-range indices, with `feature_names` lengths from
0 up.
