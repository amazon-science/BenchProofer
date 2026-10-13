# mapping.md — scikit-learn__scikit-learn-13328

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 37b0e66c871e8fb032a9c7086b2a1d5419838154`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `sklearn/linear_model/huber.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validatedElementType (orig : DType)` | `HuberRegressor.fit(self, X, y, sample_weight)` — `sklearn/linear_model/huber.py:234` (changed input-validation call at body line 253) | the modeled changed function — specifically its training-matrix input-validation step, whose element-type contract is what the change tightens |
| `resolveElemType (orig : DType)` *(deep model — A-reference)* | the element-type resolution performed by `check_array` (called via `check_X_y`) — `sklearn/utils/validation.py:331` (`check_array`), resolution logic at lines 452–466, conversion at line 496 (`np.asarray(array, dtype=dtype, ...)`) | pure spec: the validated element type produced for a given input element type, under the request from the changed call; deep model of the unchanged callee, validated `resolveElemType == check_array`'s resolution by axiom_check.py (G-AX), NOT consumed as an axiom |
| `DType.isFloating` | `np.dtype.kind in 'fc'` floating test (the downstream requirement: signed arithmetic in `_huber_loss_and_gradient`, `huber.py:93`, is defined only on floating element types) | pure spec: whether an element type is floating |
| `DType.isAccepted` | membership of the input element type in the requested accept-list `[np.float64, np.float32]` (`check_array` line 460, `dtype_orig in dtype`) | pure spec: whether an element type is carried through unchanged |
| `DType` | `numpy` array element type (`array.dtype`) abstracted to the categories the resolution distinguishes | type carrier (see §2) |

The change itself (refinement audit only, not in the consumer spec view):
`check_X_y(...)` at `huber.py:253` gains the argument `dtype=[np.float64,
np.float32]`, replacing the default `dtype="numeric"`. `check_X_y`
(`validation.py:600`) forwards `dtype` to `check_array` for `X` unchanged
(`validation.py:113–115`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. The rich training matrix `X` is
abstracted to its **element type** alone: the change touches only how the
element type is resolved, and the F2P behavior (no crash on a truth-valued
matrix) is fully determined by the resolved element type being floating. Shape
and values are irrelevant to the modeled decision and are dropped.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `X.dtype` of the input matrix, the categories validation distinguishes | `DType` | `np.dtype('float64')` ↔ `f64`; `np.dtype('float32')` ↔ `f32`; `np.dtype('float16')` ↔ `f16`; `np.dtype('bool')` ↔ `boolean`; any signed/unsigned integer `np.dtype` ↔ `integer`; `np.dtype('O')` ↔ `object` |
| resolved/validated `array.dtype` after `check_array` returns | `DType` | same bijection applied to the output element type |
| `np.dtype.kind in 'fc'` (floating/complex numeric) restricted to the real element types in scope | `DType.isFloating` | `f64,f32,f16 ↦ true`; `boolean,integer,object ↦ false` (no complex element type is reachable here — `check_array` rejects complex via `_ensure_no_complex_data`) |
| `dtype_orig in [np.float64, np.float32]` (`validation.py:460`) | `DType.isAccepted` | `f64,f32 ↦ true`; all others ↦ false |

The model deliberately includes `f16` (an accepted-list **miss** that is still
floating) and `integer` (a non-floating miss) as distinct categories so the
deep model `resolveElemType` is exercised on both legs of its `if` and so the
prepatch's wrong "numeric" policy is discriminated on more than the bool case.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveElemType` deep model ↔ `check_array` element-type resolution (A-reference)
**Callee:** `sklearn.utils.check_array` (unchanged by the patch), invoked through
`check_X_y`. The changed function does NOT change `check_array`; it changes the
*argument* it passes. The element-type resolution is modeled **deeply** by
`resolveElemType` in the `pure` region; there is **no consumed axiom**.

The resolution, when the requested `dtype` is the list `[np.float64,
np.float32]` (`validation.py:459–466`):

```python
if isinstance(dtype, (list, tuple)):
    if dtype_orig is not None and dtype_orig in dtype:
        dtype = None          # input already accepted -> preserved
    else:
        dtype = dtype[0]      # otherwise convert to first listed type (float64)
# ... later: array = np.asarray(array, dtype=dtype, order=order)   # line 496
```

So an input whose element type is in `{float64, float32}` is preserved
(`dtype=None` ⇒ `np.asarray` keeps it), and every other element type — `bool`,
integer, `float16`, `object`, … — is converted to `float64` (`dtype[0]`). This
is exactly `resolveElemType`: `if orig.isAccepted then orig else f64`. The
guarantee `resolveElemType_isFloating` (every result is floating) is the
property that prevents the downstream signed-arithmetic crash.

**Flag dependency:** the resolution branch above is reached only when `dtype` is
a list/tuple (the changed argument). The pre-patch default `dtype="numeric"`
takes a *different* branch (`validation.py:452–457`): preserve unless the input
is `object`. That branch is modeled by the prepatch skeleton. G-AX fuzzes the
**list** configuration `[np.float64, np.float32]` (the post-patch argument).

**Soundness check (G-AX):** `axiom_check.py` runs the real `check_array` with
`dtype=[np.float64, np.float32]` on every `DType` category (boundary) plus
randomized fuzz matrices, and asserts the resolved `array.dtype` equals
`resolveElemType(orig)` under the §2 bijection. Imports only `numpy` and
`sklearn.utils.check_array`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`13328`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `if orig.isAccepted then orig else f64` decision to Python and bridges it to
the behaviour of `patch.diff` (the real `check_X_y(..., dtype=[np.float64,
np.float32])` element-type resolution) over fuzzed input element types,
asserting zero disagreements.
