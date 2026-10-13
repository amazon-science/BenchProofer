# mapping.md — scikit-learn__scikit-learn-13328

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 37b0e66c871e8fb032a9c7086b2a1d5419838154`, states the type
abstraction, and gives the provenance of each deep-model reference (the callee
source + the exact behaviour the deep model is validated against by G-AX).

Repo file under change: `sklearn/linear_model/huber.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fit_robust_regressor(input_rep, row_values)` | `HuberRegressor.fit(self, X, y, sample_weight=None)` — `sklearn/linear_model/huber.py:234` (the validation call at line 253-254) | the modeled changed function: validates the feature matrix, then (via the gradient step it drives) negates the selected rows; its contract demands the negation actually ran for every input |
| `validate_matrix(input_rep, request_floating)` *(A-consumed axiom)* | the **unchanged** validation callee `check_X_y`/`check_array` invoked by `fit` — `sklearn/utils/validation.py` (the call site `huber.py:253-254`) | the only way a matrix acquires a concrete post-validation representation. Its value clause pins `Result() == validated_rep(input_rep, request_floating)` (the deep model, §3.1), and it grants the `matrix_rep(input_rep, Result())` token (evidence the matrix ACTUALLY has that representation now). NOT the function under change: what changed is the ARGUMENT the caller passes it (modeled as `request_floating`, an impl-region choice). |
| `matrix_rep(input_rep, rep)` *(capability token — `@ContractOnly @Predicate`, no body)* | the **actual dtype kind of the validated array** flowing from validation into the gradient step | abstract, unforgeable, value-free token. Records which representation the matrix REALLY has, so a representation tag handed to the negation step cannot be fabricated (e.g. a constant floating tag with no validation call). Sole producer: `validate_matrix`'s postcondition, whose value clause ties the tag to the real validator's behaviour. Required by `negate_rows`'s precondition. |
| `negate_rows(input_rep, rep, row_values)` *(A-consumed axiom)* | the squared-loss gradient step `X_non_outliers = -axis0_safe_slice(X, ~outliers_mask, n_non_outliers)` in `_huber_loss_and_gradient` — `sklearn/linear_model/huber.py:93` | the **unchanged** downstream operation that negates a row-subset of the validated `X`; can only run when `X` ACTUALLY HAS (token-evidenced: `Requires(matrix_rep(input_rep, rep))`) a dtype that supports unary negation (`Requires(supports_negation(rep))`), returns the element-wise negation, and grants the `negation_performed(input_rep, row_values)` token (evidence the negation ran rather than raised). NOT the function under change. |
| `negation_performed(input_rep, row_values)` *(capability token — `@ContractOnly @Predicate`, no body)* | the **runtime success of the negation step** for an `X` originating from this dtype kind, on the very selected row-slice: in the gold, `-axis0_safe_slice(X, ...)` returns; pre-patch on `bool`, it raises `TypeError` | abstract, unforgeable, value-free token. Models the control-flow effect "the negation ran to completion on these rows" that no value abstraction can witness (the negated values are identical either way). Binding the row collection (by reference) prevents laundering the token through a stand-in collection. Sole producer: `negate_rows`'s postcondition. Required by `fit_robust_regressor`'s postcondition for its own rows, making the negation step mandatory/non-bypassable. |
| `validated_rep(input_rep, request_floating)` *(deep model — A-reference)* | the dtype-selection logic of `sklearn.utils.check_array` (called by `check_X_y`) — `sklearn/utils/validation.py:439-466, 496, 535` | pure spec: the element representation (numpy dtype kind) of the array produced by validation, as a function of the input dtype and whether a floating dtype list is requested |
| `supports_negation(rep)` *(deep model — A-reference)* | numpy's unary `-` operator on an ndarray (the `-` in `huber.py:93`) | pure spec: whether element-wise negation is defined for a dtype kind; numpy `-` is undefined for `bool` and defined for integral/floating |
| `negated(vals)` *(deep model — A-reference)* | numpy element-wise unary negation of the float row-slice (`-axis0_safe_slice(...)`, `huber.py:93`) | pure spec: the element-wise negation of the selected row values |

The pre-patch behaviour the change repairs (for the refinement audit, not
referenced from the consumer spec view): `fit` calls `check_X_y(X, y,
copy=False, accept_sparse=['csr'], y_numeric=True)` with no `dtype` argument
(`huber.py:253-254`). With the default `dtype="numeric"`, `check_array`
preserves a `bool` input array as `bool` (it converts only object-dtype to
float, `validation.py:452-457, 535`), so `_huber_loss_and_gradient` receives a
boolean `X` and `-axis0_safe_slice(X, ...)` raises
`TypeError: The numpy boolean negative, the - operator, is not supported`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| numpy dtype of `X` (the element representation) | integer tag `input_rep`/`rep` ∈ {`REP_LOGICAL=0`, `REP_INTEGRAL=1`, `REP_FLOATING=2`} | `bool` dtype ↔ `0`; integer dtype (`int*`/`uint*`, kind `i`/`u`) ↔ `1`; floating dtype (`float64`/`float32`, kind `f`) ↔ `2`. The F2P `test_huber_bool` supplies the logical (`bool`) representation, tag `0`. |
| the requested `dtype` argument to `check_X_y`/`check_array` | boolean `request_floating` | absent / `"numeric"` ↔ `False` (no floating request); `dtype=[np.float64, np.float32]` ↔ `True` (a floating representation is requested). Mirrors `validation.py:459-466`: a list dtype whose first element is `np.float64` is selected when the input dtype is not already in the list. |
| the selected non-outlier rows of `X` that are negated (`axis0_safe_slice(X, ~outliers_mask, n_non_outliers)`) | `List[int]` `row_values` of element values (row-major flattening of the selected slice) | `X[k]` ↔ `row_values[k]` as an element value; `len(slice)` ↔ `len(row_values)`; numpy unary `-` ↔ list-element unary `-`. The values are abstracted to `int` because the tested behaviour (negation being *defined*) is dtype-kind-driven, not value-driven; G-AX validates the value-level negation `negated` against numpy on float arrays. |
| numpy unary `-` on the validated matrix | `negate_rows` whose `Requires(supports_negation(rep))` | numpy `-` on a `bool` array raises; on integral/floating it returns the element-wise negation. The precondition models exactly that definedness. |

`str` indexing is irrelevant here; the carrier is `List[int]` for the negated
slice and integer tags for dtype kinds.

## 3. Axiom + deep-model provenance (checked by G-AX / axiom_check.py)

There are **two consumed `@ContractOnly` axioms** — `validate_matrix` (§3.0a)
about the **unchanged** validation callee, and `negate_rows` (§3.0) about the
**unchanged** downstream numpy negation callee — never the function under
change. Their precondition/value clauses are grounded entirely in the deep
A-reference models §3.1–§3.3, which are validated equal to the real callees
out-of-band by `axiom_check.py` (G-AX). Their remaining postconditions grant
the two capability tokens (§3.0a / §3.0), which have no runtime content to
fuzz (see below).

### 3.0a `validate_matrix` axiom + the `matrix_rep` capability token
**Callee:** the validation routine `check_X_y`/`check_array`
(`sklearn/utils/validation.py`, called at `huber.py:253-254`) — the unchanged
step that produces the concrete post-validation array. The axiom's contract:
- `Requires(0 <= input_rep <= 2)` — the modelled representation domain.
- `Ensures(Result() == validated_rep(input_rep, request_floating))` — the
  validated representation is exactly the deep model §3.1, i.e. exactly what
  the real validator produces; the axiom cannot hand out a representation the
  real callee would not.
- `Ensures(matrix_rep(input_rep, Result()))` — the capability token: an
  abstract `@ContractOnly @Predicate` with **no body** (un-`Fold`-able), whose
  ONLY producer is this postcondition. It records that the matrix ACTUALLY HAS
  the returned representation. Its role is to make the representation tag fed
  to the negation step **honest**: without it, an implementation could pass an
  arbitrary negation-supporting tag to the negation step while the matrix it
  negates still has an unsupporting representation — verifying while claiming
  a success the real operation would not deliver.
**Soundness:** the token's tag is pinned by the value clause to
`validated_rep` == the real validator's output (§3.1, G-AX-validated), so the
token can never assert a representation the real validation would not produce.

### 3.0 `negate_rows` axiom + the `negation_performed` capability token
**Callee:** the gradient negation `-axis0_safe_slice(X, ~outliers_mask, ...)`
(`huber.py:93`) — the unchanged numpy unary `-` on the validated row-slice.
The axiom is the **weakest** contract sufficient for the proof:
- `Requires(matrix_rep(input_rep, rep))` — token evidence that the matrix
  ACTUALLY has representation `rep` at this point (§3.0a); the tag cannot be
  fabricated, only obtained from the validation step.
- `Requires(supports_negation(rep))` — the negation can only run when that
  actual representation supports it (§3.2); never stronger than numpy.
- `Ensures(ToSeq(Result()) == negated(...))` — the element-wise negation (§3.3).
- `Ensures(negation_performed(input_rep, row_values))` — the capability token. It is an
  abstract `@ContractOnly @Predicate` with **no body**, so it carries no value
  and asserts nothing about the data; Nagini rejects `Fold` of it, so nothing
  but this axiom's postcondition can produce it. It models the *control-flow
  effect* "the negation actually ran (did not raise) for an `X` of this dtype
  kind, on this very row-slice" — the very property `test_huber_bool` observes
  (fit must not crash) and the only thing that distinguishes gold from the
  buggy impl, since the negated values are identical whether or not the
  negation raises. Binding `row_values` (the list reference) into the token
  ensures the negation that ran is the one on the caller's own rows — it
  cannot be earned on a stand-in collection.
**Soundness:** the token is granted ONLY on `negate_rows`'s success path, whose
preconditions demand real negation-definedness for the representation the
matrix ACTUALLY has (`matrix_rep` evidence + `supports_negation`); so the token
can never certify a negation that real numpy `-` would have refused. There is
nothing to fuzz at runtime (it is a proof-level capability); its soundness
reduces to §3.0a + §3.2 (the preconditions that gate it) plus the end-to-end
check in `axiom_check.py` (patched validation lets every input, incl. logical,
be negated; pre-patch logical cannot). This is the same capability-token idiom as
`combined_collection` in `tasks/pydata__xarray-4094/`.

### 3.1 `validated_rep` deep model ↔ `sklearn.utils.check_array` dtype logic
**Callee:** `sklearn.utils.check_array` (via `check_X_y`), `sklearn/utils/validation.py`.
Relevant source at base_commit:

```python
dtype_numeric = isinstance(dtype, str) and dtype == "numeric"   # 439
dtype_orig = getattr(array, "dtype", None)                      # 441
if dtype_numeric:
    if dtype_orig is not None and dtype_orig.kind == "O":       # 452-455
        dtype = np.float64
    else:
        dtype = None                                            # 457  (bool stays bool)
if isinstance(dtype, (list, tuple)):                            # 459
    if dtype_orig is not None and dtype_orig in dtype:          # 460-462
        dtype = None
    else:
        dtype = dtype[0]                                        # 466  (-> np.float64)
...
array = np.asarray(array, dtype=dtype, order=order)             # 496
if dtype_numeric and array.dtype.kind == "O":                   # 535
    array = array.astype(np.float64)
```

Hence: with the **default** (`dtype="numeric"`, i.e. `request_floating=False`),
a `bool`/`int`/`float` input is left at its own dtype (the object-only
conversion does not touch them) → the input representation is preserved. With
the gold patch's **`dtype=[np.float64, np.float32]`** (`request_floating=True`),
`dtype_orig` (bool/int) is not in the list so `dtype = np.float64`, and even a
`float32`/`float64` input is in the list and preserved as floating → the
validated representation is always floating. This is exactly what
`validated_rep` encodes. G-AX runs the real `check_array` over the three
representations × {request, no-request} and asserts equality.
Docs: https://scikit-learn.org/stable/modules/generated/sklearn.utils.check_array.html

### 3.2 `supports_negation` deep model ↔ numpy unary `-`
**Callee:** numpy's unary negation operator on an `ndarray` (the `-` in
`huber.py:93`). numpy raises
`TypeError: The numpy boolean negative, the - operator, is not supported` for a
`bool` array, and returns the element-wise negation for integral/floating
arrays. `supports_negation(rep) := rep != REP_LOGICAL` encodes exactly that.
G-AX attempts `-X` for each representation and asserts the match. (This holds in
the instance's numpy 1.16 and is unchanged through numpy 2.x.)

### 3.3 `negated` deep model ↔ numpy element-wise negation
**Callee:** numpy unary `-` producing the element-wise negation of the float
row-slice. `negated(vals)` is the element-wise negation. G-AX fuzzes 5000
random integer-valued float slices and asserts `negated == -X`.

**Soundness check (G-AX):** `axiom_check.py` imports only `numpy` and
`sklearn.utils.check_array` (the very validator the gold patch passes the new
dtype argument to). It validates §3.1–§3.3 and the end-to-end contract
(requesting a floating representation lets every input — including the logical
`bool` of `test_huber_bool` — be validated then negated; the pre-patch logical
case is un-negatable, reproducing the reported bug). The end-to-end check is
exactly the runtime image of the `negation_performed` token + its gating
precondition (§3.0): gold → the negation runs for every input (token grantable);
pre-patch logical → the negation raises (precondition unsatisfiable). Ran clean
on host python (sklearn 1.7.2 / numpy 2.3.5). Exit 0 iff sound.
