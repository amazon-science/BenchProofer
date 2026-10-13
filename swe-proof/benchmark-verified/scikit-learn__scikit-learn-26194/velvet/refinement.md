# refinement.md — scikit-learn__scikit-learn-26194

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`withLeadingSentinel` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. `patch.diff` is the gold patch
**verbatim** (G-RESOLVE).

This bundle has **no axioms** and **no deep-model references**: the changed
operation is a single concrete prepend, modeled directly. Every row below is R or
I.

## A. The threshold-anchoring site — `roc_curve` (`sklearn/metrics/_ranking.py:1086`)

Gold hunk (the behavioral line; the others are docstring/doctest edits):
```
- thresholds = np.r_[thresholds[0] + 1, thresholds]
+ # get dtype of `y_score` even if it is an array-like
+ thresholds = np.r_[np.inf, thresholds]
```

| # | Solution.lean impl op (`withLeadingSentinel`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base : List Rat` | the `thresholds` ndarray at line 1086 (post-`_binary_clf_curve`, post-drop) | R | finite-float ndarray ↔ `List Rat`, order + value preserved (mapping.md §2). G-CONF obtains `base` by running the real upstream pipeline. |
| A2 | `Threshold.top` (the leading element) | `np.inf` | R | `np.inf` ↔ the sentinel constructor `top` (mapping.md §2). The discriminating content of the change: the lead is the infinite sentinel, not a finite value. |
| A3 | `finiteSeq base` (the tail, each value lifted) | `thresholds` (the existing vector, unchanged) | R + I | `finiteSeq = List.map Threshold.value` is the identity on content; the tail is carried through unchanged and in order — concrete (I), under the finite-float ↔ `Rat` refinement (R). |
| A4 | `Threshold.top :: finiteSeq base` | `np.r_[np.inf, thresholds]` | I | `np.r_[a, xs]` (prepend one element) ↔ list `cons`; the whole impl is this single concrete prepend. |

Discriminating content of the change — the leading threshold is the **infinite
sentinel** (`np.inf` ↔ `Threshold.top`), categorically above every finite score,
rather than the **finite** `thresholds[0] + 1` (which exceeds 1 whenever the top
score does, e.g. probability estimates). This lives in `A2`/`A4`: `out.head =
Threshold.top`. The pre-patch built a finite lead `value (base.head! + 1)`;
`Solution_prepatch.lean` reproduces that and **fails** `out = Threshold.top ::
finiteSeq base` at the head (`value _ ≠ top`), which is G-DIFF on the exact
clause the F2P test `test_roc_curve_with_probablity_estimates` (`np.isinf(
thresholds[0])`) and `test_roc_curve_drop_intermediate` (`thresholds[0] == inf`)
observe.

## B. No axioms / no deep-model references

The upstream callee `_binary_clf_curve` (+ `drop_intermediate`) is **unchanged**
by the patch and only supplies the input `base`. It is the *input carrier*, NOT a
consumed axiom and NOT a deep-model reference: the spec models the changed op (the
prepend) directly, and the two structural facts about `base` it relies on
(non-empty → `require base ≠ []`; all-finite → the `Rat` carrier and the
"sentinel above all" reading) are discharged by **G-AX** running the real callee,
never by a Lean `axiom`. There is therefore no dead axiom and no A row.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely changed — replacing the
finite leading threshold with the infinite sentinel — is expressed **directly** as
the constructor `Threshold.top` rather than hidden behind an axiom. (Modeling it
as a literal Lean `Float` `np.inf` would be inexpressible for the verifier —
`loom`/cvc5 cannot reason about IEEE infinities — so the type is refined to an
inductive whose `top` constructor carries exactly the "infinite sentinel,
distinct from every finite score" property; that is an **R** refinement of the
value domain, mapping.md §2, not a kind-3 hole.)

## D. verify(Solution) ⇒ resolved

`withLeadingSentinel` verifies only if its output is `Threshold.top ::
finiteSeq base` — i.e. the leading element is the sentinel `top` and the tail is
the input thresholds unchanged in order (A2–A4). By R (`np.inf ↔ top`,
finite-float ndarray ↔ `List Rat` order/value-preserving) the verified result
equals `np.r_[np.inf, thresholds]` on every input — which is exactly the gold
patch's line 1086. By G-AX the real input carrier always yields a non-empty,
all-finite `base` (so `require` is met and the sentinel genuinely tops every
score); by G-CONF the R/I shadow `[np.inf, *thresholds]` agrees with the real
patched `roc_curve`'s `thresholds` on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
