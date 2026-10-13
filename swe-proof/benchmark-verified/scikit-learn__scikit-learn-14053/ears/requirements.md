# Requirements: robust textual export of a fitted decision tree

## Introduction

The text-export helper `export_text` in `sklearn/tree/export.py` renders a
fitted decision tree (`DecisionTreeClassifier` or `DecisionTreeRegressor`) as an
indented, human-readable rule listing. The caller may supply a `feature_names`
list so that internal split nodes are labeled with meaningful feature names
instead of the generic `feature_{i}` placeholders.

A fitted tree stores, in `decision_tree.tree_.feature`, one entry per node: an
internal (splitting) node holds the non-negative index of the feature it splits
on, while a leaf node holds the reserved out-of-band sentinel value
(`sklearn.tree._tree.TREE_UNDEFINED`, whose value is `-2`) because a leaf splits
on no feature. When building the per-node label list from `feature_names`, the
helper must only look a name up for nodes that actually split on a feature; leaf
nodes carry no feature and must not be used to index `feature_names`.

The observed defect: when `feature_names` is supplied and the sentinel value is
used as an index into `feature_names`, the lookup can address a position outside
the list and raise `IndexError: list index out of range`. This is triggered
whenever the sentinel (a negative index) selects a position that does not exist
in the supplied list — most reliably when the tree has few features, e.g. a
single-feature tree with a one-element `feature_names`. The goal is that
per-node name resolution be total: it must succeed for any fitted tree and any
correctly sized `feature_names`, producing the same labeled output as before for
all previously working cases.

## Requirement 1: Total per-node feature-name resolution

**User story:** As a user rendering a fitted decision tree as text with custom
feature names, I want `export_text` to succeed regardless of how many features
the tree has, so that I get the rule listing instead of an exception.

**Acceptance criteria**

1. WHEN `export_text` is called on a fitted decision tree with a `feature_names`
   list whose length equals the tree's feature count, THEN `export_text` SHALL
   return a text report and SHALL NOT raise `IndexError`.
2. WHEN the fitted tree contains leaf nodes (nodes whose stored per-node feature
   entry is the reserved sentinel value that marks "splits on no feature"), THEN
   `export_text` SHALL resolve those leaf nodes to a non-name placeholder rather
   than using the sentinel value to index the supplied `feature_names` list.
3. WHEN the fitted tree has a single feature and `feature_names` is a one-element
   list, THEN `export_text` SHALL still return the full text report without
   raising an exception.
4. IF a node splits on a feature (its stored per-node feature entry is a valid
   non-negative index into `feature_names`), THEN `export_text` SHALL label that
   node with the `feature_names` entry at that index.
5. The system SHALL produce exactly one resolved per-node label entry for each
   node of the tree, in node order, whether or not `feature_names` is supplied.

## Requirement 2: Rendered output content is preserved

**User story:** As a user who already relies on the textual layout, I want the
rendered rules, thresholds, and leaf values to be exactly as before for cases
that already worked, so that the fix does not change any correct output.

**Acceptance criteria**

1. WHEN `export_text` renders an internal split node, THEN the system SHALL emit
   the two comparison lines for that node using the resolved feature label and
   the node's threshold formatted to the requested number of decimals.
2. WHEN `export_text` renders a leaf node, THEN the system SHALL emit that leaf's
   value (for a regressor) or class information (for a classifier) and SHALL NOT
   emit any feature label for the leaf.
3. WHEN `feature_names` is not supplied, THEN `export_text` SHALL label internal
   split nodes with the generic `feature_{index}` names exactly as before.
4. The system SHALL produce byte-for-byte identical output for a given fitted
   tree and set of formatting arguments whether or not `show_weights` changes the
   leaf-value rendering, matching the pre-existing behavior for each setting.

## Requirement 3: Existing argument validation is unchanged

**User story:** As a caller passing invalid arguments, I want the same explicit
error messages as before, so that argument validation behavior is not regressed
by the resolution fix.

**Acceptance criteria**

1. IF `feature_names` is supplied and its length does not equal the tree's
   feature count, THEN `export_text` SHALL raise `ValueError` reporting the
   required and received element counts, before attempting any name resolution.
2. IF `max_depth` is negative, THEN `export_text` SHALL raise `ValueError`.
3. IF `decimals` is negative, THEN `export_text` SHALL raise `ValueError`.
4. IF `spacing` is not strictly positive, THEN `export_text` SHALL raise
   `ValueError`.
5. The system SHALL keep the behavior that no `IndexError` from name resolution
   masks or precedes these validation errors.
