# mapping.md — astropy__astropy-14995

## Symbol binding (file:line @ base_commit b16c7d12ccbc7b2d20364b89fb44285bcbfede54)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_maskPropagation` / `problem_spec_maskPropagation` | `NDArithmeticMixin._arithmetic_mask` | `astropy/nddata/mixins/ndarithmetic.py:485-527` |
| `selfMask` | `self.mask` | `ndarithmetic.py:517-526` |
| `operandMask` | `operand.mask` | `ndarithmetic.py:517-526` |
| `handleMask` | the `handle_mask` parameter (a callable, or `None`) | `ndarithmetic.py:485` |
| `Mask` (`List Int`) | the operand's mask array (an integer bitmask grid, flattened) | — |
| `Combine` (`Mask → Mask → Mask`) | the `handle_mask` callable, e.g. `np.bitwise_or` | `ndarithmetic.py:526` |

The modeled function is `_arithmetic_mask`, which computes the result mask of an
arithmetic operation between `self` and `operand`. It is the only behavior the
patch changes and the only behavior the FAIL_TO_PASS test
(`test_nddata_bitmask_arithmetic`) observes (the test asserts the result mask of
`multiply` with `handle_mask=np.bitwise_or` for every present/absent mask
combination).

### What the function does (base_commit)

```python
def _arithmetic_mask(self, operation, operand, handle_mask, axis=None, **kwds):
    if (self.mask is None and operand is not None and operand.mask is None) \
            or handle_mask is None:
        return None
    elif self.mask is None and operand is not None:
        return deepcopy(operand.mask)
    elif operand is None:                       # <-- the buggy branch condition
        return deepcopy(self.mask)
    else:
        return handle_mask(self.mask, operand.mask, **kwds)   # crashes if operand.mask is None
```

In the two-operand arithmetic path (`add`/`subtract`/`multiply`/`divide` against
another `NDData`, or against a scalar wrapped into an operand of the same class —
see `_arithmetic`/`_prepare_then_do_arithmetic`), `operand` is **always a present
object**. So the `elif operand is None` branch is dead in this path, and when
`self` has a mask but `operand.mask is None` the code falls through to
`handle_mask(self.mask, None)`, which raises
`TypeError: unsupported operand type(s) for |: 'int' and 'NoneType'` (the issue's
crash). The gold fix changes the branch condition to `elif operand.mask is None:`
so the existing `self.mask` is copied over instead.

(The `operand is None` form is reached from the collapse path of `_arithmetic`,
where `_arithmetic_mask` is *not* called — collapse uses the Masked/np.ma module
directly — so it never exercised this code, which is why the `operand is None`
typo went unnoticed.)

### Lean modeling

- `selfMask`, `operandMask : Option Mask` record whether each operand carries a
  mask (`some grid`) or not (`none` ≡ Python `mask is None`). `Mask = List Int`
  is the flattened integer bitmask grid — bitmasks (the scientifically-required
  case in the issue), of which boolean masks (`0`/`1`) are a special case.
- `handleMask : Option Combine` is the `handle_mask` parameter: `none` ≡ Python
  `handle_mask is None`; `some hm` is the element-wise merge callback
  (`np.bitwise_or` in the F2P test). Modeled as an arbitrary
  `Mask → Mask → Mask`, so the spec/proof hold for ANY merge function.
- The **two-operand domain** (`operand` present) is the modeled domain: this is
  the path `_arithmetic_mask` is actually called from and the one the F2P test
  exercises. `operand is None` is dead here, so it is not a separate input; the
  decision is keyed purely on whether each mask is present.
- The result is `Except Unit (Option Mask)`: `.ok none` (no result mask),
  `.ok (some m)` (result mask `m`), or `.error ()` (the merge could not be
  performed — the `TypeError` crash). The post-patch impl never errors in this
  domain; the pre-patch impl errors on the `some sm, none` case, exactly the
  issue's `nref_mask.multiply(1.).mask` / `nref_mask.multiply(nref_nomask).mask`
  crash.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.mask` (array or `None`) | `selfMask : Option Mask` | `None ↔ none`; an array ↔ `some` of its flattened int grid |
| `operand.mask` (array or `None`) | `operandMask : Option Mask` | as above |
| `handle_mask` (callable or `None`) | `handleMask : Option Combine` | `None ↔ none`; a callable ↔ `some` of the element-wise function |
| the returned `result_mask` | `result : Except Unit (Option Mask)` | `None ↔ .ok none`; array `m` ↔ `.ok (some m)`; a raised `TypeError` ↔ `.error ()` |
| `np.bitwise_or(a, b)` | `hm a b` | element-wise bitwise-or of the two int grids |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The mask-propagation decision is
  modeled DEEPLY and structurally over the observable inputs (mask present /
  absent for each operand, combining function supplied / not). The combining
  function `handle_mask` is an explicit INPUT parameter of the modeled routine,
  not an axiomatized callee — the spec quantifies over all `Combine`, so its
  exact behavior is irrelevant to the decision the patch fixes. SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed decision. The `axioms` region is
  empty and **G-AX skips**.
- `deepcopy` (applied to the copied-over mask) is an identity at the value level
  for the modeled observation (the result mask equals the source mask); it does
  not change the mask value and is not separately modeled.
- The modeled routine is reached only from the two-operand arithmetic path; the
  `operand is None` collapse path does not call it (see above), so no flag gating
  beyond mask-presence is relevant.

## G-CONF fuzz seed

Pinned LCG seed: **14995** (see `conformance_check.py` `SEED`). Corpus:
randomized `(selfMask, operandMask, handleMask)` triples crossing every
present/absent combination of the two masks and the supplied/none state of the
combining function, with the combining function fuzzed as element-wise
bitwise-or over random int grids of matching length. The R/I shadow of
`implementation_maskPropagation` is diffed against an in-process replica of the
POST-PATCH `_arithmetic_mask` decision over ≥1e5 fuzzed inputs. Hand-picked edge
cases pin the discriminating category: `self` has a mask and `operand` has none
(must copy `self`'s mask, NOT crash), mirroring the F2P
`nref_masked.multiply(1.0)` / `nref_masked.multiply(nref_nomask)` cases.
