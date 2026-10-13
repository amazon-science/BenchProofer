# refinement.md — sympy__sympy-11618

The operation-by-operation correspondence between `model.py`'s implementation
(the `point_distance` impl region, the deep `psum`/`coord`/`term` model, and the
live `root` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation).

The claim (precisely scoped — see §C): the spec encodes the
zero-padded squared-difference sum over the larger ambient dimension. The gold
patch computes exactly that sum on the inputs the correctness oracle exercises
— equal-dimension pairs (the original pairwise sum already covers every axis)
and **different-type** pairs (the patch's new dimension-aware branch). On those
inputs the spec is behaviourally equal to the gold patch, so any implementation
that verifies against this frozen spec, refined per the map below, resolves.
The spec is *deliberately stronger than the gold* on one region the gold does
NOT change (two SAME-type points of differing dimension), which the oracle
never enters; §C states why resolution is nonetheless guaranteed.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The distance site — `Point.distance(self, p)` (`sympy/geometry/point.py:269`)

Gold hunk (the new dimension-aware branch added before the original return):
```
+ if type(p) is not type(self):
+     if len(p) == len(self):
+         return sqrt(sum([(a - b)**2 for a, b in zip(
+             self.args, p.args if isinstance(p, Point) else p)]))
+     else:
+         p1 = [0] * max(len(p), len(self))
+         p2 = p.args if len(p.args) > len(self.args) else self.args
+         for i in range(min(len(p), len(self))):
+             p1[i] = p.args[i] if len(p) < len(self) else self.args[i]
+         return sqrt(sum([(a - b)**2 for a, b in zip(p1, p2)]))
  return sqrt(sum([(a - b)**2 for a, b in zip(
      self.args, p.args if isinstance(p, Point) else p)]))
```

| # | model.py impl op (`point_distance`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `u, v: List[int]` | `self.args`, `p.args` (or `p`) coordinate tuples | R | `Tuple` of coordinate values ↔ `List[int]`; `len`/index correspond (mapping.md §2). |
| A2 | `n = len(u); if len(v) > n: n = len(v)` (i.e. `n = max(len(u), len(v))`) | `max(len(p), len(self))` (the length of `p1`) | I | the larger ambient dimension; same integer max. |
| A3 | per axis `i < n`: `cu = u[i] if i < len(u) else 0`; `cv = v[i] if i < len(v) else 0` | the zero-padding `p1 = [0]*n` filled only at `i < min(...)` from the shorter side, with `p2` = the longer side, then `zip(p1, p2)` — **guarded by** `type(p) is not type(self) and len(p) != len(self)` in the gold; on the fall-through (same type, or equal length) the plain `zip(self.args, p)` over all common axes | R + I (scoped) | `coord(s, i)` (model) = the i-th coordinate, zero beyond the vector — exactly the gold's zero-padded `p1` slot vs the in-range `p2` slot **when the gold's padding branch fires** (mapping.md §3.1 case analysis). For equal dimensions the gold's plain `zip` already ranges over every axis, so it too equals `coord`-padding. The governing guard `type(p) is not type(self)` is carried explicitly here: the refinement holds on the modeled domain (equal dim, or distinct type), not on same-type differing-dim pairs (§C). |
| A4 | `acc += (cu - cv) * (cu - cv)` accumulated over all `n` axes; spec value `psum(ToSeq(u), ToSeq(v), max(len(u),len(v)))` | `sum([(a - b)**2 for a, b in zip(p1, p2)])` (padding branch) or `sum([(a - b)**2 for a, b in zip(self.args, p)])` (fall-through) | A-reference (scoped) | the changed string-free operation — the *summand set* — is modeled **deeply**: `psum`/`term`/`coord` (pure region) and the verified loop in `point_distance` ARE the padded sum of squared differences. There is no consumed `distance` axiom. The deep model is validated **== the real callee on the modeled domain** out-of-band: G-AX (axiom_check.py) asserts `P_u.distance(P_v) == sqrt(psum(u, v, max))` on boundary + fuzz integer points that are equal-dimension OR of distinct concrete type (the regime where the gold pads), and asserts the negative-control boundary (same-type differing-dim is NOT padded, hence out of scope). See mapping.md §3.1. |
| A5 | `return root(total)` where `total = psum(..., max)` | `return sqrt(<inner sum>)` | A-consumed | `root` is the weakest contract on the unchanged `sqrt` the spec needs: a deterministic non-negative function of its argument (mapping.md §3.2). The proof consumes its determinism (`Result()` is a function of the EXACT padded sum) and `Result() >= 0`. G-AX confirms it against the real `sqrt`. |

The discriminating content of the change — that axes present only in the LONGER
vector contribute `(coordinate - 0)**2` instead of being dropped — lives in
`n = max(len(u), len(v))` together with `coord` zero-padding the shorter vector
(model) ⇔ the `p1 = [0]*max(...)` / `p2 = longer` construction (real), which the
gold guards with `type(p) is not type(self) and len(p) != len(self)`. The
pre-patch behaviour walked the pair only to `min(len(u), len(v))` (the
truncating `zip`); `model_prepatch.py` reproduces that (`n = min(...)`) and
**fails** the postcondition
`Result() == root(psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v)))`,
which is exactly the spec sensing the change (G-DIFF). Because `root` is an
opaque deterministic function, `root(psum(..., min))` is not provably equal to
`root(psum(..., max))` whenever the longer vector has a non-zero tail (the
reported `Point(2,0).distance(Point(1,0,2))` witness: `min` gives `sqrt(1)`,
`max` gives `sqrt(5)`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, A-consumed, or I. The one operation that
genuinely *changed* — the set of axes summed over and the zero-padding of the
shorter coordinate vector — is modeled **deeply** (the spelled-out padded fold
`psum` with `coord`/`term`, consumed in `point_distance`, step A4, an
**A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `distance` axiom. The only consumed axiom, `root`
(**A-consumed**, step A5), covers an **unchanged** callee (`sqrt`) the code
invokes both before and after the patch; `sqrt` appears in the deep model only
as the **A-reference** wrapper that G-AX validates the whole distance against.

## C. verify(model) ⇒ resolved (with the scope made explicit)

`point_distance` verifies only if its returned distance is `root` applied to the
sum of squared coordinate differences over EVERY axis of the larger ambient
dimension with the shorter vector zero-padded (A2–A4), i.e. `psum(u, v, max)`.

**Modeled domain vs the gold's guard.** The gold pads only inside the branch
`type(p) is not type(self)` (and there only when `len(p) != len(self)`); on the
fall-through — two points of the SAME concrete type, or of equal length — it
takes the original plain pairwise sum. Define the **modeled domain** as the
inputs on which the gold's computed quantity equals `psum(u, v, max)`:
- **equal dimension** (`len(u) == len(v)`): the plain pairwise sum already
  ranges over every axis, so it equals `psum(u, v, max)`; and
- **distinct concrete type** (`type(p) is not type(self)`): the gold's
  dimension-aware branch builds the zero-padded `p1` / longer `p2` and sums over
  all `max` axes, again `psum(u, v, max)` (mapping.md §3.1 case analysis).

On this domain the verified quantity equals the gold patch's inner sum: by R
(`Tuple` ↔ `List[int]`, `coord` ↔ the gold zero-padding) and by G-AX, which runs
the REAL patched `Point.distance` with `apply_gold=True` and asserts
`P_u.distance(P_v) == sqrt(psum(u, v, max))` on 9 boundary + 3000 fuzz pairs
restricted to this domain (A-reference), and confirms the real `sqrt` meets the
`root` axiom (A-consumed).

**Off-domain (why the spec is stronger than the gold, and why that is sound
here).** The remaining region — two SAME-type points of differing dimension
(achievable only for the generic n-D `Point`) — the gold leaves on its
truncating pairwise path; there the spec asserts the padded sum, which is
*strictly stronger* than the gold (witness: `Point([0]).distance(Point([0,0,0,0,5]))`
is `0` from the real callee but `sqrt(25)` under the model). The bundle's entire
correctness oracle lies in the modeled domain: F2P `test_issue_11617` is
`Point3D(1,0,2).distance(Point2D(2,0))` (distinct type), and the P2P distance
tests `test_Point2D` / `test_point3D` / `test_issue_9214` / `test_transform` are
equal-dimension same-type pairs. No F2P/P2P input is a same-type differing-dim
pair. Therefore any implementation that verifies against this spec computes
`psum(u, v, max)` and so matches the gold on every oracle input, hence resolves
(G-RESOLVE). The spec being stronger off the oracle's domain does not threaten
`verify ⟹ resolved`: it only forbids implementations that would *also* pad
same-type differing-dim pairs, a superset-correct behaviour the frozen tests
never penalise.

The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX, run
in-container with `apply_gold=True`, RC=0) and refinement fidelity (this
document, G-EQ). The scoping above is the load-bearing fidelity statement: the
refinement carries the gold's governing guard `type(p) is not type(self)` (A3),
not merely the changed arithmetic.
