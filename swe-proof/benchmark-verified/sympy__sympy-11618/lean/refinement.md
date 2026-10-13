# refinement.md — sympy__sympy-11618

Operation-by-operation correspondence between `implementation_sqSeparation`
(Solution.lean impl region, together with the deep `sqSep`/`commonLen` model)
and `patch.diff` (the POST-PATCH `Point.distance`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**/**G-PANEL**. `patch.diff` is the gold patch
**verbatim** (G-RESOLVE).

## A. The distance site — `Point.distance` (`sympy/geometry/point.py:237`)

Pre-patch body (`point.py:268-270`):
```
return sqrt(sum([(a - b)**2 for a, b in zip(
    self.args, p.args if isinstance(p, Point) else p)]))
```
The gold patch inserts, **before** that fallthrough, a branch taken only when
`type(p) is not type(self)`:
```
if type(p) is not type(self):
    if len(p) == len(self):
        return sqrt(sum([(a - b)**2 for a, b in zip(self.args, p.args ...)]))
    else:
        p1 = [0] * max(len(p), len(self))
        p2 = p.args if len(p.args) > len(self.args) else self.args
        for i in range(min(len(p), len(self))):
            p1[i] = p.args[i] if len(p) < len(self) else self.args[i]
        return sqrt(sum([(a - b)**2 for a, b in zip(p1, p2)]))
```
So the behavior splits on the **kind discriminator** `type(p) is type(self)`:

* **Same kind** (`type(p) is type(self)`, i.e. the fallthrough): the plain
  truncating `zip(self.args, p.args)` — pairs coordinate-by-coordinate and STOPS
  at the shorter tuple. The compared dimension is `min(len(self), len(p))`.
* **Different kind, equal length**: the same truncating `zip` (here `min = max`).
* **Different kind, unequal length**: build `p1 = [0]*max(...)`, copy the
  SHORTER vector's coordinates into its front, pair against the LONGER vector.
  I.e. zero-pad the shorter vector to `max(len(self), len(p))` — the surplus
  coordinate(s) of the longer vector are paired against `0`, not dropped.

The single Boolean `commonLen sameKind = if sameKind then min else max` captures
all three paths exactly: same-kind ⇒ `min`; different-kind ⇒ `max` (which
degenerates to `min` when the lengths already agree). This is the correction
over an earlier model that padded to `max` UNCONDITIONALLY: that would wrongly
pad two same-kind bare `Point`s of differing dimension, which the gold code
truncates.

| # | Solution.lean impl op | patch.diff / post-patch op | tag | justification |
|---|---|---|---|---|
| A1 | param `a : List Rat` | `self.args` (coordinate `Tuple`) | R | `Tuple` of numeric coords ↔ `List Rat` (mapping.md §2). |
| A2 | param `b : List Rat` | `p.args if isinstance(p, Point) else p` | R | the other point's coords ↔ `List Rat`; the isinstance branch is the identity carrier. |
| A3 | param `sameKind : Bool` | `type(p) is type(self)` (the patch's discriminator) | R | `True` ↔ same concrete class; `False` ↔ different class (mapping.md §2). |
| A4 | `n := if sameKind then min .. else max ..` (`commonLen`) | the compared dimension: truncating `zip` (= `min`) on the same-kind / equal-length paths; `max(len(p), len(self))` on the different-kind unequal path | I | `commonLen` reproduces exactly the dimension each gold path runs in. |
| A5 | `a.getD i 0`, `b.getD i 0` over `i ∈ [0:n)` | `p1 = [0]*max(...)` with the shorter vector copied into its front, paired against `p2`; the plain `zip` truncation elsewhere | I | reading a missing coordinate as `0` embeds the shorter vector at the origin — the patched branch's `p1` construction; when `n = min` no read is ever out of range, matching the truncating `zip`. |
| A6 | `acc + (a.getD i 0 - b.getD i 0)^2` folded over `[0:n)` | `sum([(a-b)**2 for a,b in zip(...)])` | I | the fold IS that sum of squared per-coordinate differences; the loop computes it. |
| A7 | result `: Rat` = `sqSep sameKind a b` | the argument of `sqrt(...)` | R | the method models the **squared** distance; `distance = sqrt(result)`. `sqrt` is injective / order-preserving on `[0,∞)`, so pinning the squared value pins the distance. |

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — pairing the
shorter vector against the origin in the extra dimensions **only when the points
are of different kinds**, rather than always truncating — is modeled **deeply**
(`sqSep` + `commonLen`, steps A4-A5, I), not hidden behind an axiom about the
function under change. There are **no axioms** in this bundle (mapping.md §3):
no consumed axiom, no dead axiom, no A-reference. So **G-AX skips**.

## C. verify(Solution) ⇒ resolved

`implementation_sqSeparation` verifies only if its output equals
`sqSep sameKind a b`: the sum of squared per-coordinate differences over the
compared dimension `commonLen sameKind a b` (A4-A6), with missing coordinates
read as `0`. By R (`Tuple ↔ List Rat`, `distance = sqrt(result)` with `sqrt`
injective on `[0,∞)`) the verified squared distance equals the gold patch's
squared distance on the tested coordinate inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s real `Point.distance(...)**2` over
≥10⁵ fuzzed inputs incl. the F2P case. Therefore a model satisfying this spec,
refined per the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE).

The discriminating content of the change — for two points of **different kind**
with **different ambient dimensions**, the surplus coordinate(s) of the longer
vector are paired against `0`, not dropped — lives in `commonLen`'s `max` branch.
`Solution_prepatch.lean` re-introduces the truncation as `n := min a.length
b.length` UNCONDITIONALLY (the base_commit `zip`, which ignores the kind); it
satisfies the spec when `sameKind = true` (spec is also `min`) but **fails**
`result = sqSep sameKind a b` whenever `sameKind = false` and the lengths differ
(spec is then `max`), so its `correct_sqSeparation` is unclosable (G-DIFF). On
the F2P input `Point3D(1,0,2)` vs `Point2D(2,0)` (different kinds, dims 3≠2):
pre-patch squared = `1`, spec `sqSep false = 5` (= `sqrt(5)` after the shared
`sqrt`).
