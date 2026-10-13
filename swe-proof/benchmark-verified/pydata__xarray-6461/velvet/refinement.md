# refinement.md — pydata__xarray-6461

The operation-by-operation correspondence between `Solution.lean`'s `impl`
region (the `attrsToKeep` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** / **A-reference**
(axiomatized / deep-model callee), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviorally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The selection site — the `keep_attrs` callback in `where()`

Gold hunk (`xarray/core/computation.py`, inside `where`, `keep_attrs is True`):
```
- keep_attrs = lambda attrs, context: attrs[1]
+ keep_attrs = lambda attrs, context: getattr(x, "attrs", {})
```

| # | Solution.lean impl op (`attrsToKeep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `present : List Int` | the lambda parameter `attrs` (built by the caller as `[a.attrs for a in objs]`) | R | a list of attribute mappings ↔ a `List Int` of mapping identities (mapping.md §2). The old body's `attrs[1]` ↔ `present[1]!` (the prepatch). |
| A2 | parameter `xAttrs : Int` | `getattr(x, "attrs", {})` | R | `x`'s own attribute mapping ↔ its identity; the empty mapping (scalar `x`) ↔ identity `0` (mapping.md §2). The closure variable `x` of the real lambda is the second positional argument of `where`. |
| A3 | parameter `xPos : Int` + the `require` clauses tying it to `present`/`xAttrs` | the structural fact that `objs = _all_of_type(args, DataArray)` contains `x` (at the count-of-leading-DataArrays offset) iff `x` is a `DataArray`, else `x` is absent | R | encodes, as preconditions, how `attrs` relates to `x`: a present mapping equals its owning argument's mapping (`∀ k, (xPos = k ∧ k < present.length) → present[k]! = xAttrs`); a scalar contributes none and carries `{}` (`xPos = -1 → xAttrs = 0`). No operation — pure framing of the inputs (mapping.md §2). |
| A4 | `return xAttrs` | `return getattr(x, "attrs", {})` | I (under R of A2) | the body returns the second argument's OWN mapping — the identical concrete operation, modulo the dict↔int identity refinement of A2. |
| A5 | the unused real lambda parameter `context` | (omitted) | R | unreferenced by both old and new bodies; abstracted away (mapping.md §1). |

The discriminating content of the change — return `x`'s own attrs
(`getattr(x, "attrs", {})`) rather than the positional list entry `attrs[1]` —
lives in step A4. The pre-patch body `attrs[1]` is reproduced by
`Solution_prepatch.lean` (`return present[1]!`): it **fails verification** on the
postcondition `out = xAttrs`, with the unsolved goal `present[1]! = xAttrs`. The
spec only constrains the entry at `xPos` (`present[xPos] = xAttrs`), so the
constant-offset read at index 1 is provably the wrong mapping whenever
`xPos ≠ 1` — and is unconstrained / out of range in the scalar case
(`xPos = -1`, `present` of length 1), precisely the `IndexError: list index out
of range` the issue reports. This single prepatch witnesses both faces of the
defect: the out-of-range read (the crash) and the wrong-mapping selection (the
semantic error). G-DIFF sees the bug; G-EQ sees that the only verifying body is
one returning `xAttrs`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The changed operation is an ordinary
positional-vs-identity selection, fully expressible in Velvet; it is modeled
deeply (the `attrsToKeep` body and its preconditions). There is therefore:
- **no consumed axiom** (`A-consumed`): nothing the proof depends on is an opaque
  callee contract;
- **no A-reference**: there is no deep model validated against a real callee —
  `getattr(x, "attrs", {})` is the elementary "object's own attrs, else `{}`"
  fact, captured by the `xAttrs` parameter, not a library function whose behavior
  requires G-AX validation.
Hence no `axiom_check.py` is shipped for this instance.

## C. verify(Solution) ⇒ resolved

`attrsToKeep` verifies only if it returns `xAttrs` — the second argument's own
attribute mapping (`0`/`{}` for a scalar) — for ALL admissible configurations,
including the scalar one (`xPos = -1`, `xAttrs = 0`) where a positional read
`present[1]!` is out of bounds or wrong. By the R-refinement of A1–A3 and A5 and
the identity of A4, the verified body equals `getattr(x, "attrs", {})` on the
inputs the F2P test exercises (all-DataArray and scalar-second-argument,
mapping.md §4). G-CONF mechanically confirms the R/I leg: the shadow `getattr(x,
"attrs", {})` agrees with the patched `xr.where(...).attrs` over 10⁵ fuzzed
configurations (seed 6461). The gold `patch.diff` is exactly that body and
resolves the harness (G-RESOLVE). The only trust point reduces to refinement
fidelity (this document, G-EQ + G-CONF); there is no axiom-soundness trust point
because no axiom is consumed.
