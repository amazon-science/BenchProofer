# refinement.md — scikit-learn__scikit-learn-13328

The operation-by-operation correspondence between `model.py`'s implementation
(the `fit_robust_regressor` impl region) and the consumed/deeply-modelled
callees (`negate_rows`, the deep `@Pure` models `validated_rep` /
`supports_negation` / `negated`, and the capability token `negation_performed`)
versus `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized/deeply-modelled callee — **A-consumed** where
the proof uses an axiom's `Ensures`; **A-reference** where a deep model is
validated == the real callee by `axiom_check.py` / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## 0. The discriminator is a CONTROL-FLOW EFFECT, not a value

The F2P test `test_huber_bool` only checks that `HuberRegressor().fit(X_bool, y)`
**does not raise** — it does not check the fitted output value. The bug is that
the pre-patch `fit` leaves a `bool` `X` as `bool`, so the gradient step
`-axis0_safe_slice(X, ...)` raises `TypeError` (numpy refuses unary `-` on a
bool array). The negated *values* the gradient would produce are identical
whether `X` is `bool`-coerced-to-float or `float` to begin with; the difference
is purely **whether the negation runs or raises**. Therefore NO value-level
postcondition (`ToSeq(Result()) == negated(...)`) can separate the gold from a
wrong impl — both produce the same value abstraction. (This is exactly the hole
the prior bundle had: the value postcondition was discharged by inlining a total
`negated` over the `List[int]` carrier, bypassing the only definedness guard.)

The effect is modelled explicitly with **two unforgeable capability tokens**,
both `@ContractOnly @Predicate`s with no body (Nagini rejects `Fold` of a
body-less abstract predicate, so neither can be fabricated):

- `matrix_rep(input_rep, rep)` — "the matrix ACTUALLY has representation
  `rep`". Sole producer: the validation step `validate_matrix`, whose value
  clause pins the tag to the deeply-modelled (G-AX-validated) `validated_rep`.
  This makes the representation tag fed downstream **honest**: an impl cannot
  simply pass a constant negation-supporting tag to the negation step while
  the matrix it negates still has an unsupporting representation.
- `negation_performed(input_rep, row_values)` — "the negation step actually ran". Sole
  producer: the negation step `negate_rows`, whose preconditions
  `matrix_rep(input_rep, rep)` and `supports_negation(rep)` gate entry, and
  whose postcondition grants the token.

`fit_robust_regressor`'s own postcondition `Ensures(
negation_performed(input_rep, row_values))` makes the token mandatory **for every input**,
so a verifying impl must have actually reached a successful `negate_rows` on a
matrix whose token-evidenced ACTUAL representation supports negation — i.e.
must have coerced the (possibly logical) input to a negation-supporting
representation via validation first. (Same idiom as `combined_collection` in
`tasks/pydata__xarray-4094/`.)

## A. The validation site — `HuberRegressor.fit` (`sklearn/linear_model/huber.py:253`)

Gold hunk:
```
- X, y = check_X_y(
-     X, y, copy=False, accept_sparse=['csr'], y_numeric=True)
+ X, y = check_X_y(
+     X, y, copy=False, accept_sparse=['csr'], y_numeric=True,
+     dtype=[np.float64, np.float32])
```

| # | model.py impl op (`fit_robust_regressor`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `input_rep: int` ∈ {0,1,2} | the dtype of the input array `X` passed to `fit` | R | numpy dtype kind ↔ representation tag (mapping.md §2): `bool`↔0, integral↔1, floating↔2. The F2P `test_huber_bool` corresponds to `input_rep=0`. |
| A2 | parameter `row_values: List[int]` | the non-outlier rows of `X` later negated by `_huber_loss_and_gradient` (`axis0_safe_slice(X, ~outliers_mask, ...)`) | R | numpy slice element values ↔ list element values (mapping.md §2). |
| A3 | `rep = validate_matrix(input_rep, True)` | `check_X_y(..., dtype=[np.float64, np.float32])` | A-consumed (+ A-reference) | the validation step is consumed as an axiom about the **unchanged** validator callee; the changed **argument** is the impl-region literal `True` ⇔ the gold's `dtype=[np.float64, np.float32]` (the pre-patch absence of the argument ⇔ `False`, `model_prepatch.py`). The axiom's value clause pins `Result() == validated_rep(input_rep, True)` — the deep model returning the floating representation for every input, exactly as the real `check_array` does when the floating dtype list is requested (mapping.md §3.1; G-AX validates `validated_rep == real check_array` over all representations × request flags) — and grants `matrix_rep(input_rep, Result())`, the unforgeable evidence of the representation the matrix ACTUALLY has after validation (mapping.md §3.0a). |
| A4 | `result = negate_rows(input_rep, rep, row_values)` | `X_non_outliers = -axis0_safe_slice(X, ~outliers_mask, n_non_outliers)` (`huber.py:93`), the downstream gradient step that negates the validated `X` | A-consumed (+ R) | the negation step is the consumer of the validated dtype. As an axiom about the **unchanged** numpy `-` callee, `negate_rows` `Requires(matrix_rep(input_rep, rep))` (token evidence the matrix ACTUALLY has representation `rep` — only the validation step grants it, so the tag cannot be fabricated — mapping.md §3.0a), `Requires(supports_negation(rep))` (numpy `-` raises on a logical representation, succeeds otherwise — mapping.md §3.2), `Ensures(ToSeq(Result()) == negated(...))` (the element-wise negation — mapping.md §3.3), AND `Ensures(negation_performed(input_rep, row_values))` (the token = the negation actually ran). The proof CONSUMES all of these. Both deep models inside the contract (`supports_negation`, `negated`) are G-AX-validated == numpy. `input_rep` is threaded in so the token names the input the negation actually serviced. |
| A5 | `return result` | the gradient computation proceeds with `X_non_outliers` and `fit` returns `self` (no raise) | R/I | the negated slice flows into the rest of the (unchanged) gradient/loss arithmetic; the modelled observable is that the negation **succeeds** (the token) and equals the element-wise negation. |

The discriminating content of the change — for the logical (`bool`) input
`input_rep=0`, validation must yield a representation that supports negation —
lives in `rep = validate_matrix(input_rep, True)` (model, always floating ⇒
`supports_negation` holds for the token-evidenced tag) ⇔ the new
`dtype=[np.float64, np.float32]` argument (real, coerces `bool`→`float64`).
The pre-patch `fit` used the default `dtype="numeric"`, which leaves `bool` as
`bool`; `model_prepatch.py` reproduces that (`validate_matrix(input_rep,
False)` ⇒ `rep=input_rep=0` for the logical input) and **fails** the
precondition of `negate_rows` (`supports_negation(rep)`) — exactly the spec
sensing the change (G-DIFF). The real pre-patch raises `TypeError` at
`huber.py:93`; the model's failed `supports_negation` precondition is the
verification-level image of that runtime `TypeError`, for impls that route
through the negation step, AND — via the mandatory tokens — for impls that try
to bypass it or to fabricate the representation tag (see §B).

## B. Why the spec admits NO wrong implementation (the soundness fix)

Two prior holes, both closed by capability tokens:

1. The definedness guard `supports_negation(rep)` was a precondition on a
   **separately-modelled helper** (`negate_rows`), while the
   function-under-change's postcondition asked only for the value
   `negated(...)`. Because `negated` is total over the `List[int]` carrier, an
   impl could **inline** the negation and never invoke the guarded helper —
   verifying yet refining to the unpatched base code. The guard was
   **severable** from the result-producing obligation. Closed by the
   `negation_performed` token (below).
2. The representation tag fed to `negate_rows` was a **free integer**: an impl
   could skip validation entirely and pass a constant negation-supporting tag
   (e.g. `negate_rows(input_rep, 2, ...)`), earning the `negation_performed`
   token while the matrix it stands for still has the input's own
   representation — verifying yet refining to code whose real negation raises
   on the logical input. Closed by the `matrix_rep` token: the tag must carry
   unforgeable evidence from the validation step, whose value clause pins it
   to the real validator's output.

The fix makes the negation step **mandatory, non-bypassable and honest** by
carrying the control-flow effect on the result via the capability tokens:

- The token `negation_performed(input_rep, row_values)` is a body-less abstract predicate;
  Nagini rejects `Fold` of it, so it cannot be conjured. The **only** producer is
  `negate_rows`'s postcondition, which grants it for the very row collection it
  negated (the reference, not merely equal contents).
- `fit_robust_regressor`'s postcondition `Ensures(negation_performed(input_rep, row_values))`
  requires the token for the impl's own `input_rep` AND its own row collection,
  for **every** input — so the negation cannot be laundered through a stand-in
  collection (an empty dummy, a copy) while the caller's rows take another route.
- `negate_rows` demands `matrix_rep(input_rep, rep)` — itself body-less and
  un-`Fold`-able, produced ONLY by `validate_matrix`, whose value clause pins
  `rep == validated_rep(input_rep, request_floating)`. So the `rep` argument is
  necessarily the representation the (modelled) matrix ACTUALLY has after a
  real validation choice.
- Hence any verifying impl must reach a successful `negate_rows(input_rep, ...)`
  with an honestly-obtained `rep` satisfying `supports_negation(rep)` — which,
  for a logical input (`input_rep=0`), is only obtainable by the coercing
  validation (`validate_matrix(0, True)` yields `2`). The pre-patch routing
  (`validate_matrix(0, False)` yields `0`) cannot discharge
  `supports_negation(0)`, and no fabricated tag can substitute (no
  `matrix_rep` evidence).

Re-checked against ten same-spec attacks (all FAIL to verify; re-verified
with the shipped verifier after the `matrix_rep` + rows-binding
strengthenings):
- prepatch validation + inline negation: fails *"insufficient permission to
  access negation_performed(input_rep, row_values)"* (no token).
- floating validation but inline negation, never calling `negate_rows`: fails
  the same way (no token).
- routes through `negate_rows` but passes a CONSTANT `input_rep=1` to grant
  `negation_performed(1, row_values)`: fails the postcondition for `input_rep != 1`
  (wrong token).
- coerces+negates for non-logical inputs but takes the inline shortcut for the
  logical one: fails the token on the logical branch.
- pre-patch routing through `negate_rows` (`validate_matrix(_, False)`): fails
  `supports_negation(rep)` for the logical input (the TypeError image).
- returns the rows unnegated: fails value + token.
- NO validation call, constant floating tag `negate_rows(input_rep, 2, ...)`
  (the prior audit's admitted shape, likewise with constant tag `1`): fails
  *"insufficient permission to access matrix_rep(input_rep, rep)"* (no
  evidence the matrix actually has that representation).
- pre-patch validation (`validate_matrix(input_rep, False)`) followed by a
  claimed floating tag `negate_rows(input_rep, 2, ...)`: fails the same
  `matrix_rep` precondition (the held evidence names the preserved
  representation, not the claimed one).
- token laundering through a STAND-IN collection: validates (floating), calls
  `negate_rows` on an empty dummy list to earn a token, then computes the
  caller's value inline: fails the caller's postcondition — the token held is
  for the dummy, not `row_values` (the token binds the row collection).
- the same laundering through a COPY of `row_values`: fails identically — the
  token names the copy reference, not the caller's own collection.

A structurally-different **correct** positive control (`pos_control`, an explicit
branch that always requests floating and threads the genuine `input_rep`) still
VERIFIES (non-vacuity). The tokens are **capabilities**, not answer-key oracles:
they carry no value the impl can echo (directive 8), and they are about the
**unchanged** validation / numpy `-` callees, not the function under change
(directive 7).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A (consumed or reference), or I. The operation that
genuinely *changed* — the dtype requested of the validator and its consequence
for the negation step — is captured by the impl-region argument to the
`validate_matrix` axiom, whose value clause is the deep model `validated_rep`
(A3, A-reference), and by the `negate_rows` axiom's preconditions `matrix_rep`
+ `supports_negation` (A4, A-consumed, with `supports_negation` an A-reference
deep model). `validate_matrix` and `negate_rows` axiomatize the **unchanged**
validation and downstream numpy negation callees, NOT the function under
change. No step is a changed operation that Nagini cannot express.

## D. verify(model) ⇒ resolved

`fit_robust_regressor` verifies only if, for EVERY input representation including
the logical one (`input_rep=0`), it reaches a successful `negate_rows` — with
honest `matrix_rep(input_rep, rep)` evidence from a real `validate_matrix` call
(A3) and `supports_negation(rep)` for that actual representation (so the
negation does not raise) — and returns its output, carrying the
`negation_performed(input_rep, row_values)` token (A4) and the exact element-wise negation
(A4 value clause). Because the only `matrix_rep`-evidenced tag satisfying
`supports_negation` for the logical input is `validate_matrix(0, True) = 2`,
the verified routine necessarily makes the coercing validation choice. By R
(numpy dtype ↔ representation tag, numpy slice/negate ↔ list negate) it equals
`fit` with `check_X_y(..., dtype=[np.float64, np.float32])` followed by the
unchanged gradient negation, which **runs without raising** on the tested inputs;
by G-AX the deep models `validated_rep` / `supports_negation` / `negated` equal
the real `check_array` + numpy negation (A-references), and the `validate_matrix`
/ `negate_rows` axioms are the weakest contracts sound for those callees.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and G-AX-validated deep models — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
deep-model/axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
