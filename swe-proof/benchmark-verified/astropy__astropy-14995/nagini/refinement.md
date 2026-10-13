# refinement.md — astropy__astropy-14995

The operation-by-operation correspondence between `model.py`'s implementation
(the `result_mask` impl region + the `copy_seq` helper + the consumed combiner
axioms) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The decision site — `_arithmetic_mask` (`ndarithmetic.py:485`)

Gold hunk (`ndarithmetic.py:516-527`); the behavioural change is one branch
guard (the second hunk line is a comment typo fix, no behaviour):
```
- elif operand is None:
+ elif operand.mask is None:
      return deepcopy(self.mask)
```
Full decision (post-patch), with the model branches it refines to:
```
if (self.mask is None and operand is not None and operand.mask is None) or handle_mask is None:
    return None                                   # model branch 1
elif self.mask is None and operand is not None:
    return deepcopy(operand.mask)                 # model branch 2
elif operand.mask is None:                        # <- THE FIX
    return deepcopy(self.mask)                     # model branch 3
else:
    return handle_mask(self.mask, operand.mask, **kwds)   # model branch 4
```

| # | model.py impl op (`result_mask`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `self_has_mask: bool`, `self_mask: List[int]` | `self.mask` (`None` ⇔ absent; else a `numpy.ndarray`) | R | `self.mask is None` ↔ `not self_has_mask`; mask flag values ↔ `List[int]` (mapping.md §2) |
| A2 | param `operand: Operand` (`has_mask`, `mask`) | the wrapped second `operand`; `operand.mask is None` / `operand.mask` | R | `operand` is always present here (mapping.md §2.1); `operand.mask is None` ↔ `not operand.has_mask` |
| A3 | param `handle_mask_present: bool` | `handle_mask is None` (absent) vs a callable | R | presence of the combiner argument |
| A4 | `if (not self_has_mask and not operand.has_mask) or not handle_mask_present: return MaskResult(False, empty)` | `if (self.mask is None and operand is not None and operand.mask is None) or handle_mask is None: return None` | R + I | the `operand is not None` conjunct is constant-True in the modelled domain (mapping.md §2.1); the rest is identical boolean structure; `None` return ↔ `MaskResult(present=False)` (mapping.md §2) |
| A5 | `elif not self_has_mask: return MaskResult(True, copy_seq(operand.mask))` | `elif self.mask is None and operand is not None: return deepcopy(operand.mask)` | R + I | identical guard (the `operand is not None` conjunct constant-True); `deepcopy` ↔ `copy_seq` (content-preserving fresh copy, mapping.md §2) |
| A6 | `elif not operand.has_mask: return MaskResult(True, copy_seq(self_mask))` | `elif operand.mask is None: return deepcopy(self.mask)` | R + I | **the fixed branch.** `operand.mask is None` ↔ `not operand.has_mask`; `deepcopy(self.mask)` ↔ `copy_seq(self_mask)`. This is exactly the gold-patch line `+ elif operand.mask is None:` |
| A7 | `else: return MaskResult(True, apply_combiner(self_mask, operand.mask))` | `else: return handle_mask(self.mask, operand.mask, **kwds)` | A-consumed | the combiner is the UNCHANGED callee invoked only when both masks are present; modelled by the `apply_combiner` axiom whose value defers to the opaque `combine_masks` (= the real `np.bitwise_or`), G-AX-checked. The proof consumes `apply_combiner`'s `Ensures` to discharge case-4's postcondition |
| A8 | `copy_seq` loop (`List[int]` copy) | `deepcopy` of the mask array | R | a fresh equal-content array; the F2P test reads the result's flag values, which the content-preserving copy carries exactly |

## B. The consumed axioms (kind A)

| construct | repo op | tag | justification |
|---|---|---|---|
| `combine_masks(a, b)` `@Pure @ContractOnly`, `Ensures(Implies(len(a)==len(b), len(Result())==len(a)))` | `handle_mask` (`np.bitwise_or`) value | A-consumed | weakest contract: shape preservation. Used in case-4 postcondition. The combiner is never called in cases 1-3, so the bug is independent of its value semantics (mapping.md §3.1) |
| `apply_combiner(a, b)` `@ContractOnly`, `Ensures(ToSeq(Result()) == combine_masks(...))` | the `handle_mask(...)` call | A-consumed | the impure (list-producing) face of the same callee, consumed by the impl's else branch; grounds case 4 in the real combiner, not an echoable constant |

There is **no A-reference** (no deep model is validated against a callee): the
changed function's logic is modelled directly (branch selection over flag
presence), and the only opaque callee — the unchanged combiner — is consumed as
an axiom, not deeply modelled.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the third branch guard `operand is None` → `operand.mask is None` — is modelled
**directly** as the boolean branch `elif not operand.has_mask:` (step A6, an R+I
step), not hidden behind an axiom about the function under change. The only
consumed axioms (`combine_masks` / `apply_combiner`, step A7/B) cover the
**unchanged** combiner callable (`np.bitwise_or`) the both-masks branch invokes.

## D. verify(model) ⇒ resolved

`result_mask` verifies only if, in the masked-operand-meets-flag-less-operand
case (A6 / model case 3), it returns a copy of the present operand's flag array
rather than calling the combiner (model case 4). By R (mask↔`List[int]`,
`deepcopy`↔`copy_seq`, `None`↔`MaskResult(present=False)`, `operand is not None`
constant-True in domain) the verified decision equals the gold-patch decision on
the tested inputs; by A-consumed the case-4 deferral matches the unchanged
`np.bitwise_or` (G-AX). The pre-patch (`model_prepatch.py`) lacks the
`operand.mask is None` branch (its real guard `operand is None` never fires
here), so case-3 inputs fall through to the combiner and the result is
`combine_masks(self_mask, operand.mask)` — which the spec's case-3 postcondition
`ToSeq(Result().data) == ToSeq(self_mask)` cannot discharge (the combiner is
opaque), so the prepatch FAILS exactly where the bug is (G-DIFF). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited combiner axiom — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
