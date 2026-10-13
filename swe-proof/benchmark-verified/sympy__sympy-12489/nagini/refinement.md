# refinement.md — sympy__sympy-12489

The operation-by-operation correspondence between `model.py`'s implementation
(the `make` and `combine` impl regions and the `Arrangement` class) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, the proof uses the
axiom's `Ensures`, and **A-reference**, a deep model validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Site 1 — the internal builder `Permutation._af_new`

Gold hunk (`sympy/combinatorics/permutations.py`):
```
- @staticmethod
- def _af_new(perm):
+ @classmethod
+ def _af_new(cls, perm):
      ...
-     p = Basic.__new__(Perm, perm)
+     p = Basic.__new__(cls, perm)
```

| # | model.py impl op (`make`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `kind: int`, `array: List[int]` | the classmethod's `cls` and `perm` | R | `cls` (the family the builder is reached through) ↔ `kind` (mapping.md §2: `Permutation`↔0, subclass↔nonzero); `perm` (the finished array) ↔ `array: List[int]`. |
| A2 | `result = Arrangement(kind, array)` — minting a value whose family identifier is exactly `kind` and whose content is exactly `array` | `p = Basic.__new__(cls, perm)` — constructing an instance of exactly `cls` with array form `perm` | A-reference | the changed construction is modelled **deeply**: `Arrangement(kind, array)` IS "a value of family `kind` carrying `array`", and the postcondition `Result().kind == kind ∧ Result().array is array` pins it. There is no consumed `af_new` axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `Cls._af_new(perm)` and asserts `type(result) is Cls` and the array form is preserved, over exhaustive sizes 0..5 + fuzz (mapping.md §3.1). `Basic.__new__(cls, perm)` constructs exactly `cls` (CPython object creation), so the model and the real callee compute the same family-and-content map. |
| A3 | `return result` (an `Arrangement`) | `p._array_form = perm; p._size = len(perm); return p` | R + I | the `Arrangement` carries the array directly (R: `array` field ↔ `_array_form`); `_size` is `len(perm)`, an unchanged derived field the F2P test does not discriminate on. |

`model_prepatch.py` reverts site 1: `make` mints onto the fixed base family
(`Arrangement(0, array)`), mirroring the pre-patch `Basic.__new__(Perm, perm)`.
It **fails** the postcondition `Result().kind == kind` (verified:
`model_prepatch.py:73 … Assertion (Result().kind == kind) might not hold`) — the
spec sensing the change (G-DIFF).

## B. Site 2 — the binary combination `Permutation.__mul__`

Gold hunk (`sympy/combinatorics/permutations.py`):
```
      else:
          b.extend(list(range(len(b), len(a))))
          perm = [b[i] for i in a] + b[len(a):]
-     return _af_new(perm)
+     return self._af_new(perm)
```
(`_af_new` at module scope is `Perm._af_new`, i.e. bound to the base class, so
the pre-patch call discarded `self`'s class.)

| # | model.py impl op (`combine`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `self: Arrangement`, `other: Arrangement`, `product: List[int]` | `self`, `other` (the two operands) and the computed `perm` | R | `type(self)`↔`self.kind`, `type(other)`↔`other.kind` (mapping.md §2); the numeric product `[b[i] for i in a] + b[len(a):]` ↔ `product` — the product computation is **identical pre/post-patch** (the patch touches only the wrapping class), so it is carried through as the unchanged `product` carrier rather than recomputed. |
| B2 | `result = make(self.kind, product)` — reach the builder THROUGH `self`'s family | `return self._af_new(perm)` — reach `_af_new` through `type(self)` | I (the call edge) + A-reference (the builder it calls) | the modeled change is "reach the builder through the left operand's family instead of a fixed family": `make(self.kind, …)` ↔ `self._af_new(…)`. `make` is under spec (site 1, not an axiom — the caller uses its `Ensures`), so the result family is `self.kind` (postcondition `Result().kind == self.kind`). G-AX validates `type(left*right) is type(left)` on the real `__mul__`. |
| B3 | `return result`; content is `product` | the returned `Permutation`'s `_array_form` is `perm` | R | array form ↔ `array` field; the F2P test compares both class (`type(p*q)`) and value (array form). |

`model_prepatch_2.py` reverts site 2: `combine` reaches the builder through the
fixed base family (`make(0, product)`), mirroring the pre-patch module-level
`_af_new(perm)` == `Perm._af_new(perm)`. It **fails** the postcondition
`Result().kind == self.kind` (verified: `model_prepatch_2.py:99 … Assertion
(Result().kind == self.kind) might not hold`) — the spec sensing the second,
independently-fixed behavior (G-DIFF). This is the headline F2P discriminator
`type(p * q) == CustomPermutation`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
changed — minting a value of the family the construction was reached through
(rather than a fixed family) — is modelled **deeply** (the `Arrangement(kind,
…)` construction in `make`, step A2, an **A-reference**; and the call edge
`make(self.kind, …)` in `combine`, step B2), not hidden behind an axiom about
the function under change. There is **no consumed axiom** at all: the unchanged
numeric machinery (`_af_rmul`, `Cycle`, range padding) appears only inside the
`product`/`array` carriers it produces, which the patch does not touch.

The patch additionally rewrites the SAME pattern (`_af_new(…)` →
`self._af_new(…)`/`cls._af_new(…)`; `Perm(…)` → `cls(…)`/`self.unrank_lex`/…) at
~20 further call sites (`__new__` arms, `__pow__`, `__xor__`, `__invert__`,
`next_lex`, `_unrank1`, `commutator`, `unrank_lex`, `unrank_trotterjohnson`,
`josephus`, `from_inversion_vector`, `random`, `rmul_with_af`, `mul_inv`,
`__rmul__`, `__add__`). Every one is the identical family-propagation edit (call
the builder through `cls`/`self` instead of the fixed base) — the same A2/B2
correspondence. The two modeled sites (`make`, `combine`) are the two
**independently-observable** behaviors the F2P test pins (the builder honouring
its family; a combination keeping the left family — `type(p*q) ==
CustomPermutation`); the remaining sites are instances of the same modeled edit
and add no new correspondence kind. (Per SPEC_GUIDE §3, modeling each
distinct site as its own function is preferred; the repeated sites collapse onto
the two modeled correspondences and are exercised collectively by the F2P
`wrapped_test_Permutation()` re-run of the whole suite under the subclass, which
G-AX's exhaustive construction sweep covers.)

## D. verify(model) ⇒ resolved

`make` verifies only if its result's family identifier equals the family it was
reached through (`Result().kind == kind`, A2); `combine` verifies only if its
result is of the left operand's family (`Result().kind == self.kind`, B2). By R
(`type ↔ kind`, array form ↔ `array`, the unchanged product ↔ `product`) the
verified construction equals `Basic.__new__(cls, perm)` / `self._af_new(perm)`
on the tested inputs; by G-AX the deep model equals the real `_af_new`/`__mul__`
family-propagation (A-reference) over exhaustive + fuzz constructions, including
the F2P witnesses `type(p*q) is CustomPermutation` and `type(q*p) is
Permutation`. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited deep-model reference —
and the gold patch resolves (G-RESOLVE). The trust points are exactly those of
PLAN §1.1: the A-reference soundness (G-AX) and refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because no axiom is
consumed.
