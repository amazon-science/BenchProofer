# mapping.md — astropy__astropy-14995

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b16c7d12ccbc7b2d20364b89fb44285bcbfede54`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `astropy/nddata/mixins/ndarithmetic.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `result_mask(self_has_mask, self_mask, operand, handle_mask_present)` | `NDArithmeticMixin._arithmetic_mask(self, operation, operand, handle_mask, axis=None, **kwds)` — `astropy/nddata/mixins/ndarithmetic.py:485` (body lines 516-527) | the modeled changed function (the result-mask decision) |
| `self_has_mask` / `self_mask` | `self.mask is None` (absence) / `self.mask` (the array) | first operand's mask presence + content |
| `operand` (`Operand.has_mask`, `Operand.mask`) | the wrapped second operand and `operand.mask is None` / `operand.mask` | second operand's mask presence + content |
| `handle_mask_present` | `handle_mask is None` (absence) / a callable | whether a combiner callable was supplied |
| `MaskResult.present` / `MaskResult.data` | the `Optional` return: `None` (no mask) vs a returned mask array | the decided result mask |
| `combine_masks(a, b)` *(axiom — A-consumed)* | `handle_mask(self.mask, operand.mask, **kwds)` — the combiner callable, default-and-tested `numpy.bitwise_or` (`ndarithmetic.py:527` post-patch) | unchanged callee invoked only when BOTH masks present (case 4) |
| `apply_combiner(a, b)` *(axiom — A-consumed)* | same `handle_mask(self.mask, operand.mask, **kwds)` call, list-producing face | the materialized combiner call inside the impl |

The pre-patch repo symbol the change fixes (for the refinement audit, not
referenced from the consumer spec view): the third decision branch guard at
`ndarithmetic.py:523`, `elif operand is None:` (the bug), which the gold patch
replaces with `elif operand.mask is None:`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.mask` : `numpy.ndarray` or `None` | `self_has_mask: bool` + `self_mask: List[int]` | `self.mask is None` ↔ `not self_has_mask`; a present mask's flattened bitmask values ↔ `self_mask` (`List[int]`); the F2P test compares per-element integer flag values, which the flat `List[int]` carries exactly |
| `operand` (a wrapped `NDData`-like) | `Operand` (fields `has_mask`, `mask`) | `operand.mask is None` ↔ `not operand.has_mask`; `operand.mask` ↔ `operand.mask` (`List[int]`). The operand object is always present at this decision (scalars are wrapped to a flag-less `NDData` before the `handle_mask` path; see §2.1), so `operand is None` is not in the modelled domain |
| `deepcopy(x)` of a mask array | `copy_seq(x)` (a fresh `List[int]` with the same contents) | `deepcopy` produces a new array equal in content; modelled as a content-preserving copy (`ToSeq(Result()) == ToSeq(x)`). The result mask is read-only downstream, so a `1/2`-permission read-only copy suffices |
| the returned `Optional[mask]` | `MaskResult` (`present` + `data`) | `None` ↔ `present == False`; a returned array ↔ `present == True and data == array` |
| `numpy.ndarray` element-wise shapes | `len(ToSeq(·))` equal-length precondition | both operands wrap co-shaped data ⇒ their masks share shape; modelled as `len(ToSeq(self_mask)) == len(ToSeq(operand.mask))` |

`numpy` array indexing/iteration is not in Nagini's fragment, so masks are
carried as flat `List[int]` of their integer flag values; the specification is
phrased over `PSeq[int]` via `ToSeq`. The bug and its fix are about *branch
selection*, not array element arithmetic, so the flat carrier is faithful.

### 2.1 Why `operand is None` is outside the modelled domain
`_arithmetic_mask`'s `handle_mask` decision is reached (caller `_arithmetic`,
`ndarithmetic.py:335`) only on the path where the result is NOT a masked array.
A bare scalar second argument (`nref.multiply(1.0, …)`) is wrapped to an
`NDData` with `mask=None` by `_prepare_then_do_arithmetic` (`ndarithmetic.py:704,
718,728`) before `_arithmetic` runs, so the `operand` reaching `_arithmetic_mask`
on this path is a present object with `operand.mask is None` — exactly the
modelled `operand.has_mask == False`. The genuine `operand is None` case
(collapse operations) is handled earlier by the masked-array branch
(`ndarithmetic.py:325`, `hasattr(result, "mask")`) and does not call
`_arithmetic_mask`. The FAIL_TO_PASS test exercises only wrapped operands.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `combine_masks` / `apply_combiner` ↔ `handle_mask` (`numpy.bitwise_or`)
**Callee:** the `handle_mask` callable invoked at `ndarithmetic.py:527`
(post-patch line) as `handle_mask(self.mask, operand.mask, **kwds)`. The issue
and the FAIL_TO_PASS test call arithmetic with `handle_mask=np.bitwise_or`, and
`np.bitwise_or` is the element-wise bitwise-or numpy ufunc. This callee is
**unchanged** by the patch (it is invoked identically in both pre- and
post-patch code in the both-masks-present branch); the patch only changes which
*branch* runs.

**Axiom (weakest sufficient):** the proof needs only that the combiner is a
deterministic, shape-preserving function of its two equal-length array inputs:

  `len(combine_masks(a, b)) == len(a)` when `len(a) == len(b)`.

It does NOT pin the element values (the bug does not depend on them; the
combiner is never called in cases 1-3). `apply_combiner` is the same callee's
list-producing face used in the impl's case-4 branch; its `Ensures` ties the
returned array's content to the opaque `combine_masks(a, b)`, i.e. "the result
of the real combiner", grounding case 4 in the actual callee rather than an
echoable constant.

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy.bitwise_or`
on the F2P bitmask rows, boundary bitmask vectors, all-zero/no-op cases, and
20 000 randomized fuzz pairs, asserting shape preservation
(`len(out) == len(a)`) and determinism. It imports only `numpy` — the dependency
the gold patch's `handle_mask=np.bitwise_or` invocation uses. Docs:
https://numpy.org/doc/stable/reference/generated/numpy.bitwise_or.html. Exit 0
iff sound.
