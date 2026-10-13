# refinement.md — scikit-learn__scikit-learn-10908

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`getFeatureInventory` `do` block, plus the deep `materializeIndex` /
`readinessGuard` / `featureList` models it calls) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs + this narrative are audited by **G-AX** / **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The single changed site — `get_feature_names` (`text.py:994`)

Gold hunk:
```
     def get_feature_names(self):
         """Array mapping from feature integer indices to feature name"""
+        if not hasattr(self, 'vocabulary_'):
+            self._validate_vocabulary()
+
         self._check_vocabulary()

         return [t for t, i in sorted(six.iteritems(self.vocabulary_),
                                      key=itemgetter(1))]
```

| # | Solution.lean impl op (`getFeatureInventory`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `mut st : InvState` (`index`, `explicit`) | `self` (its `vocabulary_` / `fixed_vocabulary_` attributes) | R | the touched estimator state ↔ `InvState` (mapping.md §2). `index = none` ↔ `not hasattr(self,'vocabulary_')`. |
| A2 | `supplied : Option (List String)` | the constructor `vocabulary` param read inside `_validate_vocabulary` | R | `None`/list ↔ `none`/`some terms` (mapping.md §2); `require` pins the well-formed-list domain. |
| A3 | `st := if st.index = none then materializeIndex supplied st else st` | `if not hasattr(self, 'vocabulary_'): self._validate_vocabulary()` | **I** (the `hasattr`-guard control flow) + **A-reference** (the callee body) | the **added** orchestration — establish only when not yet established — is the concrete control flow the patch introduces (I, transliterated by G-CONF). The establishment step it runs is the unchanged callee `_validate_vocabulary`, modeled deeply by `materializeIndex` and validated == the real callee by G-AX (mapping.md §3.1). |
| A4 | `match readinessGuard st with \| error e => error e \| ok _ => …` | `self._check_vocabulary()` (raises, else proceeds) | **A-reference** | the unchanged readiness guard, modeled deeply by `readinessGuard`; `notReady`/`emptyIndex`/`ok` ↔ `NotFittedError`/`ValueError("…empty")`/return. Validated == real callee by G-AX (mapping.md §3.2). |
| A5 | `Except.ok (featureList (st.index.getD []))` | `return [t for t,i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` | **I** | the unchanged return: index→term map sorted by index, terms projected. `featureList` is the order-by-index projection (mapping.md §3.3). G-CONF transliterates it directly. |

## B. The discriminating behavior (verify ⇒ correct, G-DIFF)

The change is observable in **two** ways the F2P `test_feature_names` checks,
both flowing from inserting `_validate_vocabulary` (A3) *before* the guard (A4):

1. **Explicit-but-untrained inventory is now read back.** When `st.index = none`
   and `supplied = some terms` (a `CountVectorizer(vocabulary=vocab)` never
   fitted), the post-patch path establishes the index then admits the request,
   returning the terms in index order and recording `explicit := some true`
   (`fixed_vocabulary_ == True`). The F2P asserts
   `assert_array_equal(vocab, cv.get_feature_names())` and
   `assert_true(cv.fixed_vocabulary_)`.
2. **The unfitted, no-vocabulary case still raises — but `fixed_vocabulary_` is
   now set first.** When `st.index = none` and `supplied = none`, the
   establishment step records `explicit := some false` (`fixed_vocabulary_ ==
   False`) and *then* the guard still rejects with `notReady`. The F2P asserts
   `assert_raises(ValueError, cv.get_feature_names)` **and**
   `assert_false(cv.fixed_vocabulary_)` immediately after — the latter is only
   true because `_validate_vocabulary` ran despite the subsequent raise.

`Solution_prepatch.lean` omits A3 (goes straight to the guard, state untouched).
It therefore fails `ensures (st, out) = featureNamesRun stOld supplied` on
exactly these clauses: for `index = none`, the buggy LHS is `(stOld, error
notReady)` regardless of `supplied`, while the spec RHS is `(established index,
ok terms)` when `supplied = some terms` and `({explicit := some false}, error
notReady)` when `supplied = none` — the post-state differs in BOTH branches
(the unset `explicit` is the side-effect clause #2 above) and the result differs
in the explicit branch (clause #1). G-DIFF confirms the prepatch fails on this
goal.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
control flow of `get_feature_names` — is modeled **concretely** (the
`hasattr`-guarded establishment, the guard, the projection; A3/A4/A5, I +
A-reference), not hidden behind an axiom about the function under change. There
is **no consumed axiom** and **no `axiom` declaration**: the two callees the
patch newly invokes are unchanged and modeled deeply (A-references, G-AX), and
the return projection is identical (I).

## D. verify(Solution) ⇒ resolved

`getFeatureInventory` verifies only if `(st, out) = featureNamesRun stOld
supplied` — i.e. the post-state and result equal the establish-then-guard-then-
project transition exactly (A3-A5), including the `explicit`/`fixed_vocabulary_`
side effect on the rejecting path (clause B2). By R (`InvState ↔ self`'s touched
attributes, `Option (List String) ↔ vocabulary`, the raise-kind bijection) the
verified transition equals the post-patch `get_feature_names` on the tested
inputs; by G-AX the deep models `materializeIndex` / `readinessGuard` equal the
real `_validate_vocabulary` / `_check_vocabulary` (A-references) and `featureList`
equals the return comprehension; by G-CONF the I-transliteration of the
orchestration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: deep-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
