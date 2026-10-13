# mapping.md — scikit-learn__scikit-learn-14053

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6ab8c86c383dd847a1be7103ad115f174fe23ffd`, states the type
abstraction, and documents the provenance of the modeled domain.

Repo file under change: `sklearn/tree/export.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_node_names(names, feat)` | the per-node name-resolution that builds `feature_names_` in `export_text(...)` — `sklearn/tree/export.py:892-893` (the `if feature_names:` branch, body line 893) | the modeled changed code: resolves one display name per tree node from the caller's name table |
| `names` (param) | `feature_names` — the caller-supplied list of feature names (`export.py:893`, validated at `export.py:873-877` to have length `tree_.n_features`) | the name table indexed by selector |
| `feat` (param) | `tree_.feature` — the per-node split-feature array of the fitted tree (`sklearn/tree/_tree.pyx:540-541`; consumed at `export.py:893,930`) | the per-node feature selector array |
| `built_seq(names, feat)` *(deep model)* | the value of the comprehension `feature_names_` after the patched line `export.py:893-894` | pure spec: the resolved-name sequence (deep model, not an axiom) |
| `in_domain(names, feat)` | the structural invariant of `tree_.feature` (every entry is a valid feature index or the leaf marker `-2`) | pure spec: the genuine domain of the selector array |
| result element `None` (leaf) | the literal `None` the patch stores for a leaf (`export.py:894`) | placeholder displayed for no node |

## 2. The selector array's domain (`in_domain`) — provenance

`tree_.feature` is documented in the Cython tree structure
(`sklearn/tree/_tree.pyx:540-541`):

> `feature : array of int, shape [node_count]`
> `    feature[i] holds the feature to split on, for the internal node i.`

For a terminal (leaf) node the builder sets the node's feature to the reserved
marker `_TREE_UNDEFINED`:

```
# sklearn/tree/_tree.pyx
TREE_UNDEFINED = -2                       # line 64
...
node.feature = _TREE_UNDEFINED            # leaf nodes (lines 375, 757)
```

Hence every entry of `tree_.feature` is either a valid feature index in
`[0, n_features)` (internal node) or `-2` (leaf). `export_text` validates
`len(feature_names) == tree_.n_features` up front (`export.py:873-877`), so a
valid internal-node selector is a valid position in `feature_names`. This is
exactly the modeled precondition

  `in_domain(names, feat) := ∀ j. feat[j] == -2 ∨ 0 ≤ feat[j] < len(names)`.

It is the *genuine* domain of the input, not a spec weakening: the reported
crash arises precisely because the buggy code reads `feature_names[-2]` for leaf
nodes, which is in range only when the table is long enough (≥ 2 names) and out
of range for a single feature.

## 3. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| `feature_names` (list of name strings, length `n_features`) | `names: List[int]` of feature *identifiers* | the report observes only *which* table entry is selected per internal node, not the name spelling. Abstracting each name to a distinct int identifier preserves the selection function; `feature_names[k]` ↔ `names[k]`, `len(feature_names)` ↔ `len(names)`. |
| `tree_.feature` (numpy int array, one entry per node) | `feat: List[int]` | per-node selector; `tree_.feature[j]` ↔ `feat[j]`, entries in `[0, n_features) ∪ {-2}`. `len(tree_.feature)` ↔ `len(feat)` = node count. |
| the list comprehension result `feature_names_` (list, one entry per node; a name string for internal nodes, `None` for leaves post-patch) | `List[Optional[int]]` | `feature_names_[j]` ↔ `Result()[j]`: an identifier for an internal node, `None` for a leaf. The placeholder being literally `None` matches the patch (`else None`); its concrete value is never displayed (read only at internal nodes, `export.py:930-931`). |
| iteration `for i in tree_.feature` (numpy iteration, in order) | the `while` loop over `feat` (modeled backward; front-recursive `built_seq` makes one unfold available per step) | order-preserving 1:1 per-node fold |

`str` indexing/iteration is banned in Nagini, so names/arrays are carried as
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 4. Callee provenance (kind-A) — none

There is **no axiomatized callee**. The changed operation is the construction of
the resolved-name list itself; it is modeled **deeply** by the verified
`@Pure` fold `built_seq` (and its companion `in_domain`) in the `pure` region,
spelled out as the per-node substitution

  internal node `j` (selector `s = feat[j] ≠ -2`, `0 ≤ s < len(names)`) → `names[s]`;
  leaf node (selector `-2`, or any non-position selector) → `None`.

Both the patched code and the model are pure Python list/index operations
(no stdlib callee is involved beyond list indexing and the conditional
expression), so no soundness trust point and no `axiom_check.py` execution check
is needed. `axiom_check.py` is supplied only as a lightweight executable
demonstration that the deep model `built_seq` reproduces the patched
comprehension on the reported input shapes and that the pre-patch comprehension
raises exactly the reported `IndexError` for a single-feature table.
