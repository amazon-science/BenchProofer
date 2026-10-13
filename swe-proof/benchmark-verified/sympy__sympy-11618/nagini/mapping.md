# mapping.md — sympy__sympy-11618

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 360290c4c401e386db60723ddb0109ed499c9f6e`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/geometry/point.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `point_distance(u, v)` | `Point.distance(self, p)` — `sympy/geometry/point.py:237` (body line 269) | the modeled changed function (Euclidean distance between two points) |
| `u` (first vector) | `self.args` — the coordinate tuple of the receiver point (`sympy/geometry/point.py:432 __getitem__`, `:418 __len__`) | this point's coordinates |
| `v` (second vector) | `p.args` (when `p` is a `Point`) else `p` itself — `sympy/geometry/point.py:269-270` | the other point's coordinates |
| `root(x)` *(axiom — A-consumed)* | `sqrt` — `sympy.functions.elementary.miscellaneous.sqrt` (imported `point.py:18`, called `point.py:269`) | unchanged callee: the square root wrapping the squared-difference sum |
| `coord(s, i)` | the zero-padding of the shorter coordinate vector: `p1 = [0]*max(len(p), len(self))` then `p1[i] = ...` for `i < min(...)` (`point.py` gold hunk) | pure spec: i-th coordinate, zero beyond the vector's own dimension |
| `term(u, v, i)` | the summand `(a - b)**2` of the comprehension `sum([(a-b)**2 for a,b in zip(...)])` (`point.py:269`, gold hunk) | pure spec: squared coordinate difference on one axis |
| `psum(u, v, k)` *(deep model — A-reference)* | the whole inner quantity `sum([(a-b)**2 for a,b in zip(p1, p2)])` over the zero-padded pair (gold hunk, `point.py`) | pure spec: padded sum of squared differences; deep model of the changed summand set, validated `sqrt(psum(...)) == Point.distance(...)` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): the single line
`return sqrt(sum([(a - b)**2 for a, b in zip(self.args, p.args if isinstance(p, Point) else p)]))`
(`point.py:269-270`), whose `zip` truncates to the SHORTER vector — dropping
every axis present only in the longer vector.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.args` / `p.args` — a `Tuple` of symbolic coordinate expressions | `List[int]` of coordinate values | `args[k]` ↔ `u[k]`; `len(args)` ↔ `len(u)`. The F2P / P2P tests use integer / small-rational coordinates; the contract is about WHICH squared differences enter the sum, which is value-agnostic (R0 below). |
| coordinate value inside a specification | `int` (carried as `PSeq[int]` via `ToSeq`) | `PSeq` `[i]`/`len`/`drop`/`take` mirror tuple index/len/slice |
| `zip(p1, p2)` over two equal-length zero-padded vectors of length `n = max(len, len)` | iteration over axes `0 <= i < max(len(u), len(v))` reading `coord(u,i)`, `coord(v,i)` | the gold builds `p1` (zero-padded shorter) and `p2` (longer), both length `n`, then zips; `coord` is exactly that padding |
| `sqrt(S)` (`point.py:269`) | `root(S)` axiom (kind A) | the unchanged square root; modeled as a deterministic non-negative function (§3) |

### R0 — why `int` coordinates are faithful
The bug and the fix are entirely in the *summand set*: pre-patch the pairwise
`zip` truncates to `min(len(self), len(p))` axes; post-patch the shorter vector
is zero-padded so all `max(len(self), len(p))` axes contribute. Neither the bug
nor the fix touches the arithmetic of an individual summand — `(a - b)**2` is
unchanged — so the discriminating behaviour (which axes are summed and the
zero-padding) is independent of the coordinate domain. Modeling coordinates as
`int` and the sum as an `int` captures it exactly; `axiom_check.py` confirms the
full real (symbolic-`sqrt`) result agrees on integer coordinates.

`str` indexing is irrelevant here (no strings); the only Nagini constraint used
is `List[int]`/`PSeq[int]` for the coordinate sequences.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `psum` deep model ↔ the real distance summand (A-reference)
**Callee:** the patched `Point.distance` inner sum,
`sum([(a - b)**2 for a, b in zip(p1, p2)])`, where (gold patch, `point.py:266+`)

```python
if type(p) is not type(self):
    if len(p) == len(self):
        return sqrt(sum([(a - b)**2 for a, b in zip(
            self.args, p.args if isinstance(p, Point) else p)]))
    else:
        p1 = [0] * max(len(p), len(self))
        p2 = p.args if len(p.args) > len(self.args) else self.args
        for i in range(min(len(p), len(self))):
            p1[i] = p.args[i] if len(p) < len(self) else self.args[i]
        return sqrt(sum([(a - b)**2 for a, b in zip(p1, p2)]))
return sqrt(sum([(a - b)**2 for a, b in zip(
    self.args, p.args if isinstance(p, Point) else p)]))
```

Case analysis (let `du = len(self.args)`, `dv = len(p.args)`):
- **equal dimensions** (`du == dv`, includes same-type and the cross-type
  `len(p)==len(self)` branch and the fall-through): `zip` covers every axis;
  the sum is `sum_{i<du} (self_i - p_i)**2` = `psum(u, v, du) = psum(u, v, max)`.
- **different dimensions** (`du != dv`): `p1` is the SHORTER vector zero-padded
  up to length `n = max(du, dv)` (because `p1 = [0]*n` and only its first
  `min(du,dv)` slots are filled, from whichever side is shorter), and `p2` is
  the LONGER vector. `zip(p1, p2)` therefore ranges over all `n` axes, each
  contributing `(coord_shorter,i - coord_longer,i)**2` where the shorter side is
  zero beyond its dimension. That is exactly `sum_{i<n} (coord(u,i) -
  coord(v,i))**2 = psum(u, v, max(du, dv))`.

So in every case the inner quantity equals the model's
`psum(u, v, max(len(u), len(v)))`. The changed operation (the summand set / the
zero-padding) is modeled **deeply** by `psum`/`coord`/`term`; there is **no**
consumed `distance` axiom. The deep model is validated equal to the real callee
out-of-band by `axiom_check.py` (G-AX), which asserts
`Point(u).distance(Point(v)) == sqrt(psum(u, v, max(len(u),len(v))))` on boundary
+ 2000 fuzz integer-coordinate pairs of differing dimensions (host pre-check:
200 000 cases, 0 mismatch against the gold summand logic). The reported witness
`Point(2,0).distance(Point(1,0,2)) == sqrt(5)` and the F2P
`Point3D(1,0,2).distance(Point2D(2,0)) == sqrt(5)` are both covered.

### 3.2 `root` ↔ `sqrt` (A-consumed)
**Callee:** `sympy.sqrt` (`sympy.functions.elementary.miscellaneous.sqrt`),
unchanged by the patch; the distance is `sqrt(<non-negative squared sum>)`.
Docs: https://docs.sympy.org/latest/modules/functions/elementary.html#sqrt.

The axiom encodes only the obligations the proof consumes:
- **determinism** — `root` is a function (equal arguments give equal results),
  automatic for a `@Pure` declaration; this is what ties `Result()` to the EXACT
  padded sum, so a wrong impl that sums a different set of axes produces a
  different argument and cannot satisfy the postcondition.
- **non-negativity** — `Ensures(Result() >= 0)`, i.e. `sqrt(x) >= 0` for the
  non-negative `x` the proof feeds it (`psum` ensures `>= 0`).

It does NOT claim any exact value, monotonicity beyond non-negativity, or that
`sqrt` simplifies a perfect square — only the weakest contract the verification
needs. **Soundness check (G-AX):** `axiom_check.py` runs the real `sqrt` on
non-negative integers (boundary + 2000 fuzz) and asserts it is deterministic and
`is_nonnegative`. Exit 0 iff sound. It imports only `sympy` (the package whose
`Point.distance` the patch fixes) and the standard library.

## G-CONF — differential conformance (conformance_check.py)

**Shadow (direct).** The `# impl-start`/`# impl-end` region of `model.py` copied
VERBATIM with only the contract calls deleted (`Requires`, `Ensures`,
`Invariant`, `Assert` and the `# invariants-start/-end` markers), together with
the `@Pure` helpers it depends on (`coord`, `term`, `psum`) minus their
contracts. `lemma_psum_unfold` is not copied: its body is `return True` and it is
referenced only from a stripped `Assert`. `PSeq[int]` is realized by an
immutable-tuple shim (`len`/`[]`/`==`) and `ToSeq` materializes one. The
`@ContractOnly` `root` has no body to copy, so the shim CALLS the real callee it
axiomatizes (§3.2, `sympy.sqrt`) — the axiom is exercised, not assumed, and the
comparison is on the full distance rather than a squared surrogate.

**Oracle (called, not transliterated).** The REAL gold-patched
`sympy.geometry.point.Point.distance` (§1, `sympy/geometry/point.py:237`, body
line 269). Neither `Point2D` nor `Point3D` overrides `distance` (asserted at
run time), so that one function is the entire oracle. The script also asserts the
loaded source contains the gold hunk's `type(p) is not type(self)` guard and
exits 2 otherwise, so an unapplied patch cannot be reported as agreement.

**Type bridge (§2, inverted).** `List[int]` coordinate vector -> `Point(list)`,
whose constructor sympifies each `int` to an `Integer` and dispatches on length
(2 -> `Point2D`, 3 -> `Point3D`, else the generic n-D `Point`), so `len(u)` fixes
both `len(self.args)` and the concrete class. Integer coordinates keep every
comparison exact (R0).

**Inputs.** 20 boundary cases (empty/empty, either side empty, singletons, the
F2P `Point3D(1,0,2)` vs `Point2D(2,0)` and its mirror, equal-dimension same- and
cross-class pairs, dimension gaps on both sides, negatives, 1e6-magnitude
coordinates) + seeded fuzz to **100 000** modeled-domain inputs, plus **5 007**
same-class differing-dimension pairs at the scope boundary. Every impl branch is
taken: the `len(v) > n` update taken and not taken, `i < len(u)` / `i < len(v)`
false on either side (padding on each side), and `n == 0` (loop never entered).
**Pinned seed: `SEED = 11618`.**

**Both regimes of the Requires domain are checked, neither is avoided.** The
`Requires` is only `Acc(list_pred(u|v), 1/2)`, i.e. any two int lists, which
splits per refinement.md §C into (1) the modeled domain (equal dimension or
distinct concrete class) where shadow is diffed against the real function, and
(2) the scope boundary (same class, differing dimension — reachable only for the
generic `Point`), where the model is deliberately stronger. Region (2) is not
skipped: the script pins the real behaviour there POSITIVELY, asserting
`real == sqrt(psum(u, v, min(len u, len v)))` (the gold's untouched truncating
`zip` path) on every such pair, and asserts that the G-AX negative control
`[0]` vs `[0,0,0,0,5]` really does diverge (real `0`, model `5`) — if sympy ever
padded there, the documented scoping would be describing a boundary that does
not exist and the check fails.

**The copied loop is live.** `model.py` ties the accumulator to the returned
value with `Assert(acc == total)`, a contract call that is stripped. So the
driver replays the accumulation loop verbatim (`impl_loop_acc`) and checks
`acc == psum(..., max)` on every input, turning the stripped `Assert` into a
checked observation.

**Failure capability (verified out-of-band, not shipped).** Four mutants of the
shipped script were run in-container: truncating `n` to `min` in loop *and*
`psum` (the pre-patch bug) -> refuted at the first differing-dimension input;
`coord` padding with `1` instead of `0` -> refuted; `root` returning `x` instead
of `sqrt(x)` -> refuted; truncating ONLY the accumulation loop while leaving
`psum` at `max` -> refuted by the `acc == total` observation. Running the
unmutated script without the gold patch exits 2 with the guard message rather
than passing. Exit 0 iff zero disagreements; the final stdout line is a JSON
report.
