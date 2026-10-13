# refinement.md — sympy__sympy-13615

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`complementFinite` `do` block, the pure selections `definiteOut`/`symbolicUnknown`,
and the opaque `contains` oracle) and `patch.diff` (the gold patch, applied at
`base_commit`). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses this opaque symbol's contract), **A-reference** (deep
model validated == real callee by G-AX), or **I** (identical concrete op). Every
step is R, A, or I; no kind-3 (changed-but-inexpressible) step.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. `patch.diff` is the
gold patch **verbatim** (G-RESOLVE).

## A. The changed branch — `Set._complement`'s `FiniteSet` case (`sympy/sets/sets.py:218–220`)

Gold hunk:
```
-            return FiniteSet(*[el for el in other if self.contains(el) != True])
+            from sympy.utilities.iterables import sift
+            def ternary_sift(el):
+                contains = self.contains(el)
+                return contains if contains in [True, False] else None
+            sifted = sift(other, ternary_sift)
+            # ignore those that are contained in self
+            return Union(FiniteSet(*(sifted[False])),
+                Complement(FiniteSet(*(sifted[None])), self, evaluate=False)
+                if sifted[None] else S.EmptySet)
```

| # | Solution.lean impl op (`complementFinite`) | patch.diff / repo op (post-patch) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elems : List Int` | `other` (a `FiniteSet`), iterated `for el in other` | R | `FiniteSet` of distinct elements ↔ `List Int` of distinct opaque handles (mapping.md §2). `elems.length` ↔ `len(other.args)`. |
| A2 | `let v := contains el` (read the trit) | `contains = self.contains(el)` | A-consumed + R | `contains` is the `opaque` model of the unchanged `Set.contains` callee; its verdict refines to `Trit` via `S.true↔inside`, `S.false↔outside`, symbolic↔`unknown` (mapping.md §2). The proof consumes only determinism (one handle → one verdict). |
| A3 | `ternary_sift` classification `contains in [True,False] else None` | `contains if contains in [True, False] else None` | R + I | the three-way key. `= Trit.outside` ↔ `contains is False`; `= Trit.unknown` ↔ `contains not in [True,False]`; `= Trit.inside` (dropped) ↔ `contains is True`. The boolean comparisons are concrete (I); the verdict-carrier is R. |
| A4 | `definiteOut elems` collects the `outside`-verdict elements (the `def_` accumulator) | `sifted[False]` → `FiniteSet(*(sifted[False]))` | R + I | the order-preserving selection on key `outside`; built by the backward `while` fold (concrete ops, I). `FiniteSet(*xs)` is order/dup-insensitive so list↔set is an R abstraction (mapping.md §2). |
| A5 | `symbolicUnknown elems` collects the `unknown`-verdict elements (the `sym` accumulator) | `sifted[None]` → `Complement(FiniteSet(*(sifted[None])), self, evaluate=False) if sifted[None] else S.EmptySet` | R + I | the order-preserving selection on key `unknown`. These elements are RETAINED for symbolic handling — wrapped in an unevaluated `Complement` against `self` — never asserted to be members. Modeled as the separate `symbolic` field; the `if … else S.EmptySet` is the (observationally inert) empty-case shortcut. |
| A6 | drop the `inside`-verdict elements (absent from both fields) | "ignore those that are contained in self" — `sifted[True]` is never used | I | the `inside` verdict appears in neither `definiteOut` nor `symbolicUnknown`; identical to the gold dropping `sifted[True]`. |
| A7 | `return { definite := def_, symbolic := sym }` | `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, …))` | R | the two-part result. The outer `Union` of "definite members" with "the symbolic-complement of the undetermined" ↔ the `Partition` of `definite` (members asserted in the result) and `symbolic` (held for symbolic handling). mapping.md §1. |

## B. The discriminating content of the change

Pre-patch, the single comprehension `[el for el in other if self.contains(el) != True]`
keeps **every** element whose membership is not decided-positive — i.e. it lumps
the `outside` AND the `unknown` elements together into one plain `FiniteSet`,
**asserting the undetermined elements ARE members of the complement**. That is the
bug: `Complement(FiniteSet(x,y,2), Interval(-10,10))` returned `{x, y}` —
asserting `x, y` (symbols of unknown membership) as definite members — instead of
keeping them symbolic.

`Solution_prepatch.lean` reproduces exactly this: its `def_` keeps `contains el ≠
inside` (i.e. `outside ∪ unknown`) and its `sym` stays empty. It therefore **fails
both** frozen postconditions:
- `out.definite = definiteOut elems` — diverges on any `unknown`-verdict element
  (prepatch puts it in `definite`; the spec's `definiteOut` keys on `outside`);
- `out.symbolic = symbolicUnknown elems` — unprovable, since the prepatch leaves
  `symbolic` empty while the spec pins it to the `unknown` elements.

The post-image (`Solution.lean`) keys `definite` on `outside` ONLY and routes the
`unknown` elements to the `symbolic` field — the gold behavior. (G-DIFF confirmed:
prepatch fails on `invariant_2` (definite) and `invariant_3` (symbolic).)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
re-routing of each element by a three-valued membership verdict — is modeled
**directly** (the `definiteOut`/`symbolicUnknown` selections and the verified
two-accumulator loop ARE that re-routing); it is NOT hidden behind an axiom about
the function under change. The only opaque symbol, `contains`, models an
**UNCHANGED** callee (`Set.contains`) and carries no value contract — only
determinism (A-consumed). There is no A-reference deep model (no changed op is
hidden behind an `==`-validated callee).

## D. verify(Solution) ⇒ resolved

`complementFinite` verifies only if `definite` is exactly the `outside`-verdict
selection (A4) and `symbolic` is exactly the `unknown`-verdict selection (A5),
with the `inside` elements dropped (A6) and the undetermined elements NEVER
asserted as members. By R (`FiniteSet ↔ List`, `Set.contains` verdict ↔ `Trit`,
`Union`/`Complement` assembly ↔ `Partition`) the verified routine equals the gold
`Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, …))`
on the modeled inputs; by G-AX the opaque `contains` is the deterministic real
`Set.contains` trichotomy; by G-CONF the R/I transliteration of the two selections
agrees with `patch.diff`'s `sifted[False]`/`sifted[None]` behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined per the map above, is the
gold patch up to type refinement and the audited unchanged callee — and the gold
patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: opaque
callee soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
