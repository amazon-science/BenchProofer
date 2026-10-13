# refinement.md — sympy__sympy-11618

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `distanceSq` `do` block and the deep `distSq`/`alignTo`/`sumSqZip` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The distance site — `Point.distance` (`sympy/geometry/point.py:237`)

Pre-patch body (`point.py:268-270`):
```
return sqrt(sum([(a - b)**2 for a, b in zip(
    self.args, p.args if isinstance(p, Point) else p)]))
```
Gold adds, before that fallthrough, a branch taken when `type(p) is not
type(self)`: when the lengths match it uses the same truncating `zip`; when they
differ it builds `p1 = [0]*max(len(p),len(self))`, copies the shorter vector's
coordinates into the front, and pairs against the longer vector `p2` — i.e. it
**zero-pads the shorter coordinate vector to the larger ambient dimension**
instead of silently dropping the surplus coordinates.

| # | Solution.lean impl op (`distanceSq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `s : List Int` | `self.args` (a coordinate `Tuple`) | R | `Tuple` of integer coords ↔ `List Int` (mapping.md §2). |
| A2 | param `q : List Int` | `p.args if isinstance(p, Point) else p` | R | the other point's coords ↔ `List Int`; G-CONF only fuzzes `Point` args, the isinstance branch is the identity carrier. |
| A3 | param `sameKind : Bool` | `type(p) is type(self)` (the patch's discriminator, negated) | R | `True` ↔ same concrete class; `False` ↔ different class (mapping.md §2). |
| A4 | `L := if sameKind then min .. else max ..` (`commonLen`) | the comparison dimension: truncating `zip` (= `min`) on the same-class / equal-length paths; `max(len(p), len(self))` on the different-class unequal path | I | `commonLen` reproduces exactly the dimension each gold path runs in. mapping.md §2. |
| A5 | `alignTo s L`, `alignTo q L` | `p1 = [0]*max(...)`; `p1[i] = (shorter)[i]`; `p2 = (longer)`; (and the plain `zip` truncation when equal) | I | take-then-zero-pad embeds the shorter vector at the origin in the extra dimensions — the patched branch's `p1`/`p2` construction; on equal lengths `alignTo x L = x`, matching the truncating `zip`. |
| A6 | `acc = sumSqZip (aligned s) (aligned q)`, computed by the backward `while` fold | `sum([(a-b)**2 for a,b in zip(...)])` | I | the spelled-out fold `sumSqZip` IS that sum of squared per-coordinate differences; the verified loop computes it. |
| A7 | result `out : Int` = `distSq sameKind s q` | the argument of `sqrt(...)` | R | the method models the **squared** distance; `distance = sqrt(out)` (mapping.md §2 "sqrt" row). `sqrt` is the identical concrete op applied to both sides and is injective on `[0,∞)`, so pinning the squared value pins the distance. |

Discriminating content of the change — when the two points have **different
ambient dimensions**, the surplus coordinate(s) of the longer vector are paired
against `0`, not dropped — lives in `alignTo` + `commonLen`'s `max` branch
(model) ⇔ the `p1 = [0]*max(...)` padding branch (real). The pre-patch ignores
the surplus (truncating `zip` = `min`); `Solution_prepatch.lean` reproduces that
(no alignment, `L := min`) and **fails** `out = distSq sameKind s q` on exactly
the unequal-length goal `s.length = q.length`, which is false (G-DIFF). On the
F2P input `Point3D(1,0,2)` vs `Point2D(2,0)`: pre-patch squared = `1`, spec
`distSq = 5` (= `sqrt(5)` after the shared `sqrt`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — pairing the
shorter vector against the origin in the extra dimensions rather than truncating
— is modeled **deeply** (`alignTo` + `commonLen`, steps A4-A5, I), not hidden
behind an axiom about the function under change. There are **no axioms** in this
bundle (mapping.md §3): no consumed axiom, no dead axiom, no A-reference.

## C. verify(Solution) ⇒ resolved

`distanceSq` verifies only if its output equals the exact aligned (zero-padded)
sum of squared per-coordinate differences (`distSq`, A4-A6). By R
(`Tuple ↔ List Int`, `distance = sqrt(out)` with `sqrt` injective on `[0,∞)`)
the verified squared distance equals the gold patch's squared distance on the
tested integer-coordinate inputs; by G-CONF the R/I transliteration of the fold
agrees with `patch.diff`'s real `Point.distance(...)**2` on ≥10⁵ inputs incl.
the F2P case. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point (no axioms) is refinement fidelity (this
doc, G-EQ + G-CONF).
