# refinement.md — sympy__sympy-15017

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `arrayLength` `do` block + the `prodSeq` pure model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none in this bundle), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (mapping.md §3). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the element-count observable, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The fixed site — `ImmutableDenseNDimArray._new` (`dense_ndim_array.py:152`)

Gold hunk (the Immutable `_new`; the byte-identical Mutable line at `:177` is
left unchanged by the gold patch and is not exercised by the issue/F2P —
mapping.md §1):
```
- self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0
+ self._loop_size = functools.reduce(lambda x,y: x*y, shape, 1)
```

`_loop_size` is the element count; `__len__` returns it verbatim
(`ndim_array.py:178`). The model computes that count as the product of the
shape's dimension sizes.

| # | Solution.lean impl op (`arrayLength`) | patch.diff / branch op | tag | justification |
|---|---|---|---|---|
| A1 | param `dims : List Nat` | the array's `shape` (a `Tuple` of non-negative ints) at the point `_loop_size` is computed | R | shape `Tuple` ↔ `List Nat`, each dimension ↔ `Nat` (mapping.md §2). G-CONF bridges via `shape ↔ dims`. |
| A2 | `let mut result : Nat := 1` (seed the running product with the multiplicative identity) | the `reduce` **initializer `1`** introduced by the patch (`functools.reduce(..., shape, 1)`) | I | the empty-fold value: with no factors the product is `1`. This is exactly the discriminating content of the fix — the pre-patch `if shape else 0` instead yields `0` for the empty shape. |
| A3 | the backward `while` loop `result := dims[i-1]! * result`, `i := i - 1` | `functools.reduce(lambda x,y: x*y, shape, 1)` — left-to-right product accumulation over the shape | I + R | `reduce(mul, shape, 1)` accumulates the product of all dimension sizes; the backward `while` computes the same product (`*` is associative & commutative), and the invariant `result = prodSeq (dims.drop i)` pins it to the full product at exit. Transliterated by G-CONF. |
| A4 | `return result`, `ensures n = prodSeq dims` | `self._loop_size = …`, surfaced by `__len__` as `len(array)` | I + R | the returned element count ↔ `len(array)` (mapping.md §2). `prodSeq dims` = `reduce(mul, dims, 1)`. |

Discriminating content of the change — the empty product is **one**, not
**zero** — lives in the seed `result := 1` (model, A2) ⇔ the `reduce`
initializer `1` (real). The pre-patch `… if shape else 0` returns `0` for the
empty (rank-0) shape; `Solution_prepatch.lean` reproduces it
(`result := if dims.length > 0 then 1 else 0`) and **fails** the postcondition
`n = prodSeq dims` on the empty shape — `0 ≠ prodSeq [] = 1`, the exact rank-0
scalar case the issue reports and the new F2P assertion
(`len(ImmutableDenseNDimArray(x)) == 1`) checks. For every non-empty shape both
old and new code compute the identical product, so the model and prepatch agree
there — faithful to the gold patch's behavioral footprint.

## B. No kind-A (axiomatized-callee) steps; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — folding the
shape into a product with the empty-product value `1` rather than a `0`
special-case — is modeled **concretely** (the spelled-out `prodSeq` fold +
the `result := 1` seed, steps A2/A3), not behind an axiom about the function
under change. There is no consumed axiom and no A-reference (mapping.md §3):
the changed expression uses only `functools.reduce` over the already-built
shape, so `conf_skip=false` and G-CONF carries the full mechanical weight.

## C. verify(Solution) ⇒ resolved

`arrayLength` verifies only if its output equals the exact product
`prodSeq dims`, whose empty fold is `1` (A2/A4) — not `0`. By R
(`shape Tuple ↔ List Nat`, `dimension ↔ Nat`) the verified product equals
`functools.reduce(lambda x,y: x*y, shape, 1)`, i.e. the patched `_loop_size`,
on every shape; surfaced by `__len__` it equals `len(array)`. By G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour (`len` at base_commit
with the gold patch applied) on ≥10⁵ inputs (seed 15017), 0 disagreements.
There are no axioms to trust (mapping.md §3). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The only trust point of plan §1.1 that
applies is refinement fidelity (this doc + G-CONF); axiom soundness (G-AX) is
vacuous here.
