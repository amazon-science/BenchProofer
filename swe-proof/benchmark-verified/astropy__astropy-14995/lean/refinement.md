# refinement.md — astropy__astropy-14995

Operation-by-operation correspondence between `implementation_maskPropagation`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_arithmetic_mask`
decision). Tags: **R** type refinement, **A-consumed** proof uses an axiom,
**A-reference** deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match handleMask with \| none => return .ok none` | `if ... or handle_mask is None: return None` (the `handle_mask is None` disjunct) | R |
| 2 | `\| none, none => return .ok none` | `if (self.mask is None and operand is not None and operand.mask is None) ...: return None` | R |
| 3 | `\| none, some om => return .ok (some om)` | `elif self.mask is None and operand is not None: return deepcopy(operand.mask)` | R |
| 4 | `\| some sm, none => return .ok (some sm)` | `elif operand.mask is None: return deepcopy(self.mask)` (the FIXED branch condition) | R |
| 5 | `\| some sm, some om => return .ok (some (hm sm om))` | `else: return handle_mask(self.mask, operand.mask, **kwds)` | R |

Notes:

- **Every step is R — no A, no I-deletion.** The mask-propagation decision is
  modeled DEEPLY over the observable inputs (each operand's mask present/absent,
  the combining function supplied/not). SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed decision. The `axioms` region is empty; **G-AX skips**.
- The R tag captures the carried-observation refinement: Python's `self.mask` /
  `operand.mask` (numpy arrays or `None`) ↔ `Option Mask` (a `none`/`some grid`
  presence + flattened int grid); the `handle_mask` callable ↔ `Option Combine`
  (an input function the spec quantifies over); the returned `result_mask` /
  raised `TypeError` ↔ `Except Unit (Option Mask)`. The bijection is in
  mapping.md. `deepcopy` is a value-level identity for the result-mask
  observation and adds no op.
- **The fix itself** is op #4: changing the branch condition from `operand is
  None` to `operand.mask is None`. In the modeled two-operand domain `operand is
  None` is dead (operand always present), so the gold condition is exactly "the
  operand carries no mask" — modeled as the `some sm, none` match arm returning
  `.ok (some sm)` (copy `self`'s mask over). The pre-patch impl
  (`Solution_prepatch.lean`) makes this arm `.error ()`: since `operand is None`
  never fires, a self-only mask falls through to the merge op #5, which is asked
  to combine `self.mask` with a missing `operand.mask` — the issue's
  `TypeError: unsupported operand type(s) for |: 'int' and 'NoneType'`.
- The two unchanged arms #2/#3 (`none,none` → no mask; `none,some` → copy
  operand's mask) are identical pre- and post-patch — they are the PASS_TO_PASS
  invariants the fix must not disturb. The discriminating arm is #4.
- **G-CONF** mechanically refutes the R legs (no A legs): the Python shadow of
  the impl is diffed against the post-patch `_arithmetic_mask` decision over ≥1e5
  fuzzed `(selfMask, operandMask, handleMask)` triples.
