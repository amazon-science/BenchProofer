# refinement.md — scikit-learn__scikit-learn-13328

Maps every operation in `implementation_prepareInput` to its `patch.diff`
counterpart in `sklearn/linear_model/huber.py` (and the unchanged callee in
`sklearn/utils/validation.py` whose behavior the patch's new argument triggers).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed/dependency op validated == real callee, **I**
identical concrete op.

## The modeled decision
`HuberRegressor.fit` validates `X` before numerical processing. The gold patch
adds `dtype=[np.float64, np.float32]` to the `check_X_y` call. That argument
selects the **list-dtype** branch of `check_array` (validation.py:459-466):

- if the array's original element type is already one of the accepted kinds
  (`float64`/`float32`), no conversion happens (`dtype = None`);
- otherwise the array is converted to the first accepted kind, `float64`.

Pre-patch the call used the default `dtype="numeric"`, whose resolution
(validation.py:452-457) converts ONLY an `object`-kind array to float and leaves
every other non-floating kind (in particular a **boolean** array) unconverted.
A boolean `X` then reaches `_huber_loss_and_gradient`, where unary `-X` raises
`TypeError` (numpy forbids `-` on a boolean array). The fix is exactly the
element-type normalization that forces boolean (and any non-float) input to
`float64`.

The element type is modeled as the inductive `NpKind`; the accepted set as
`acceptedKinds = [float64, float32]`; the conversion target as `defaultKind =
float64`. `implementation_prepareInput orig = if orig ∈ acceptedKinds then orig
else defaultKind` is the post-patch list-dtype resolution.

## Operation correspondence — `prepareInput`
| # | Lean op | patch.diff / callee op | tag | note |
|---|---|---|---|---|
| 1 | `let mut dt := orig` | `array.dtype` of the input `X` entering `check_X_y` | R | numpy element dtype ↔ `NpKind` (mapping.md bijection). |
| 2 | `if orig ∈ acceptedKinds then dt := orig` | list-dtype branch `if dtype_orig in dtype: dtype = None` → `np.asarray` keeps original | A-reference | the no-conversion case for an already-accepted floating kind; validated == real `check_array` by `axiom_check.py`. |
| 3 | `else dt := defaultKind` | `else: dtype = dtype[0]` (= `np.float64`) → `np.asarray(..., dtype=float64)` | A-reference | the conversion case: any non-accepted kind (incl. `bool`) → `float64`. This is the fix's observable effect; validated == real callee by G-AX. |
| 4 | `return dt` | the element type of the `X` returned by `check_X_y` and consumed downstream | I | the normalized element type. |

The patch itself (huber.py) is the single-line change of the requested `dtype`
argument; its entire observable effect is the element-type resolution performed by
the unchanged `check_array` callee, which is modeled deeply here as an
**A-reference** (no consumed axiom — the proof closes `by` case split + `rfl`,
using no property of an opaque callee). Hence there is **no A-consumed row** and
**no R/I arithmetic leg** independent of the callee model: `conformance_check.py`
(G-CONF) is a skip stub (`conf_skip=true`) and `axiom_check.py` (G-AX) carries the
soundness check by driving the real `check_X_y`.

## Prepatch (the real bug)
`Solution_prepatch.lean`: `prepareInput` converts ONLY an `object` kind to float
(`if orig = object then float64`), leaving every other non-floating kind
unconverted — exactly the pre-patch `dtype="numeric"` behavior, under which a
boolean `X` stays boolean and crashes downstream. The carried gold proof's `rfl`
steps no longer close (for `orig = bool`, the impl yields `bool` but the spec
demands `float64`), so it fails G-VERIFY — the signal G-DIFF wants. One prepatch:
the single changed behavior (the dtype normalization at the one changed call
site).
