# refinement.md — scikit-learn__scikit-learn-25232

The operation-by-operation correspondence between `model.py`'s implementation
(the `initial_constant_fill` impl region and the live `constant_statistics`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`, or **A-reference**, a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural change — propagate the replacement value

The behaviour the FAIL_TO_PASS test observes is that the iterative imputer's
first-round constant initialization installs the user-requested replacement
value (`fill_value`) for every feature, instead of the neutral numeric default.
Two gold hunks carry this data flow:

Gold hunk (constructor stores the new parameter, `sklearn/impute/_iterative.py`):
```
  self.initial_strategy = initial_strategy
+ self.fill_value = fill_value
  self.imputation_order = imputation_order
```

Gold hunk (first-round initializer passes it to the inner single-pass imputer,
`sklearn/impute/_iterative.py:_initial_imputation`):
```
  self.initial_imputer_ = SimpleImputer(
      missing_values=self.missing_values,
      strategy=self.initial_strategy,
+     fill_value=self.fill_value,
      keep_empty_features=self.keep_empty_features,
  )
  X_filled = self.initial_imputer_.fit_transform(X)
```

| # | model.py impl op (`initial_constant_fill`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requested: Optional[int]` | the stored `self.fill_value` (gold `self.fill_value = fill_value`), carried into `_initial_imputation` | R | the user-supplied replacement value. `Optional[int]` ↔ `None`-or-numerical-value: the integral value the F2P observes exactly (`fill_value=100`); precision is not the behaviour, exact equality is (mapping.md §2). The store-on-`self` step is a pure rename of the carrier. |
| A2 | parameter `n_features: int` | `X.shape[1]` — the number of feature columns at fit time | R | feature count of the data the initializer fits (mapping.md §2). |
| A3 | `constant_statistics(requested, n_features)` axiom call | the inner `SimpleImputer(strategy="constant", fill_value=self.fill_value, ...).fit_transform(X)` and the resulting `initial_imputer_.statistics_` | A-consumed | the inner single-pass imputer is the **unchanged** callee. The gold change is purely *which value is propagated into it* (`fill_value=self.fill_value`). Its constant-strategy contract — `statistics_` has one entry per feature, each equal to the (default-resolved) requested value — is the `constant_statistics` axiom (mapping.md §3.1), the weakest sufficient contract. G-AX runs the real callee and checks it. The model passing `requested` (not `None`) into the axiom mirrors the gold passing `self.fill_value` (not omitting it). |
| A4 | `return statistics` (a `List[int]` of length `n_features`) | `self.initial_imputer_.statistics_` (an ndarray of length `X.shape[1]`) | R | the installed per-feature constant array. ndarray of numbers ↔ `List[int]`; element `j` ↔ index `j`; `.shape[0]` ↔ `len(...)` (mapping.md §2). The FAIL_TO_PASS test reads exactly this array (`imputer.initial_imputer_.statistics_`). |

The discriminating content of the change — the requested value is *carried
through* rather than dropped — lives in step A3: the post-patch impl passes
`requested` (gold: `fill_value=self.fill_value`); the pre-patch impl passes
`None` (gold: the parameter omitted, so the inner imputer defaults). With
`requested == 100`, the post-patch result is `[100,…]` and the pre-patch result
is `[0,…]` (the inner imputer's numeric default). `model_prepatch.py` reproduces
the pre-patch omission (`constant_statistics(None, n_features)`) and **fails**
the postcondition
`Forall j: Result()[j] == resolved_value(requested)` — exactly the spec sensing
the change (G-DIFF).

## B. The two enabling hunks (no observable behaviour of their own)

Gold also adds the parameter to the constructor signature and to the parameter
constraints, and a documentation paragraph:
```
+ fill_value=None,                       # __init__ signature
+ "fill_value": "no_validation",         # _parameter_constraints
+ fill_value : str or numerical value …  # docstring
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the `requested: Optional[int]` formal parameter accepts any optional value | `fill_value=None` added to `__init__`; `"fill_value": "no_validation"` in `_parameter_constraints` | R + I | adding the keyword and declaring it unvalidated is exactly "any optional value is accepted" — modelled by `requested` being a free `Optional[int]` with no `Requires` restricting it. No observable computation; it is a prerequisite for A1. No separate failing prepatch (a prepatch keeps the spec byte-identical, G-DIFF `same_spec`); the observable effect is captured entirely by site A. |
| B2 | (none) | the docstring paragraph | I | documentation only; no behaviour. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The only operation that genuinely *changed* —
propagating the requested replacement value into the unchanged single-pass
imputer — is an ordinary value flow (`Optional[int]` argument), modelled
directly (A1+A3), not behind an axiom about the function under change. The one
consumed axiom, `constant_statistics` (**A-consumed**, A3), covers the
**unchanged** single-pass imputer callee the changed code invokes; G-AX
validates it against the real callee, and also validates end-to-end that the
iterative imputer carries the value through (the A-reference observation).

## D. verify(model) ⇒ resolved

`initial_constant_fill` verifies only if its result is, per feature, the
user-requested replacement value `resolved_value(requested)` (A3+A4) — which
requires passing `requested` into the unchanged callee, not `None`. By R
(`Optional[int]` ↔ `fill_value`, `List[int]` ↔ `statistics_`, `n_features` ↔
`X.shape[1]`) the verified function equals the gold path: store `self.fill_value`
and pass it to `SimpleImputer(strategy="constant", fill_value=self.fill_value)`,
reading `initial_imputer_.statistics_`. By G-AX the `constant_statistics` axiom
holds of the real single-pass imputer and the iterative imputer carries the
value through. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
