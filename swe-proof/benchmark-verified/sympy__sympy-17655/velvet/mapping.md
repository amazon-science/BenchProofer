# mapping.md — sympy__sympy-17655

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f5e965947af2410ded92cfad987aaf45262ea434`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `sympy/geometry/point.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `scalePoint (factor : Rat) (coords : List Rat)` | the newly-added reflected-multiplication operator on `Point` — `Point.__rmul__(self, factor)` (added by `patch.diff` right after `Point.__mul__`, `sympy/geometry/point.py:280`) | the modeled changed function (multiply a number, on the left, by a point) |
| `scaleCoords (coords : List Rat) (factor : Rat)` *(deep model — A-reference)* | `Point.__mul__(self, factor)` — `sympy/geometry/point.py:250` (body `coords = [simplify(x*factor) for x in self.args]; return Point(coords, evaluate=False)`) | pure spec: the per-coordinate product; the deep model of the UNCHANGED point-by-scalar scaling callee that the new operator delegates to, validated `scaleCoords == Point.__mul__` by axiom_check.py (G-AX), NOT consumed as an axiom |

The patch adds `__rmul__` and changes nothing else; `__mul__` (the callee it
delegates to) is unchanged. There is no removed pre-patch symbol — the pre-patch
behavior is simply the *absence* of a left-multiplication hook, so Python falls
back to building an unevaluated product (and `Point.__add__` then raises). The
spec view never names `__rmul__`/`__mul__`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (and, were it not skipped, G-CONF) uses to translate
values between the Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a point's coordinate tuple `self.args` (each coord an exact SymPy number) | `List Rat` | `args` ↔ `coords`; `len(self) = self.ambient_dimension` ↔ `coords.length`; ordered element-wise |
| the left scalar `factor` (a Python-native exact number — `int` / `Fraction`, as the issue/F2P use it: `5 * p4`) | `Rat` | Python `int`/`Fraction` `f` ↔ the exact rational `factor`; `sympify(f)` is the SymPy coercion, exact on the rationals |
| `simplify(x*factor)` per coordinate | exact `Rat` product `x * factor` | `simplify` is observationally the identity on an exact rational product (no symbolic simplification occurs for numeric coords); F2P compares exact `Point` equality |
| `Point(coords, evaluate=False)` constructor wrapper | identity on the `List Rat` (the coordinate carrier) | the constructor only re-wraps the scaled coordinate sequence; the F2P `==` compares coordinate tuples |

**Why a Python-native scalar (not a SymPy object) is the modeled left operand.**
The fix is `__rmul__`, Python's *reflected* multiplication hook: it fires only
when the left operand's own `__mul__` returns `NotImplemented` (Python `int` /
`float` / `Fraction` against a `Point`). A SymPy left operand (e.g.
`sympify(2.0)`) is instead consumed by SymPy's `Mul`, building an unevaluated
product — a different operation outside the modeled behavior, and NOT what the
F2P tests exercise (`5 * p4`, a Python `int`). The `Rat` carrier models the
Python-native exact-scalar case. (Floats are exact-order-modeled as `Rat` too;
see directive on float modeling — only the exact scaling relation is pinned, and
for the F2P integer cases this is exact.)

Lean `List` indexing/`map` is total and sound; the carrier is `List Rat` because
the operation is per-coordinate exact arithmetic.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `scaleCoords` deep model ↔ `Point.__mul__` (A-reference)
**Callee:** `Point.__mul__(self, factor)` (`sympy/geometry/point.py:250`),
UNCHANGED by the patch. The new `__rmul__` is a one-line delegation
(`return self.__mul__(factor)`), so its entire numeric content IS this callee.
We model that callee **deeply** as `scaleCoords coords factor =
coords.map (· * factor)` (the `pure` region) — there is **no consumed axiom**
about the function under change. `__mul__`'s body is the per-coordinate product
`[simplify(x*factor) for x in self.args]`; for exact rational coordinates and an
exact rational factor, `simplify(x*factor) = x*factor`, so the deep model is
exact.

**Soundness check (G-AX):** `axiom_check.py` runs the real `Point.__mul__`
(right-multiplication `p * factor`) on boundary inputs (the F2P 2-D/3-D points
and factors, plus zero/negative/fractional) and 20000 randomized fuzz
point/factor pairs over dimensions 2..4, asserting `scaleCoords ==` the real
UNCHANGED callee coordinate-for-coordinate and dimension-preserving
(A-reference). Imports only `sympy`. Exit 0 iff sound. Seed `17655`.

G-AX runs at **base_commit (unpatched)**, so it does NOT exercise the new
`__rmul__` reflected-multiply path (`factor * point`) — that hook does not yet
exist, and per SPEC_GUIDE directive 7 a deep-model check validates only the
UNCHANGED callee, never the function under change. The delegation behaviour the
F2P tests demand (`factor * point == point * factor`, a `Point` not an
unevaluated product) is the *patched* behaviour, validated by **G-RESOLVE** (the
official harness runs `5 * p4 == Point(5, 5)` / `5 * p4 == Point3D(5, 5, 5)`
against the patched repo).

## 4. G-CONF fuzz seed

G-CONF is **skipped** for this bundle (`meta.json conf_skip=true`): the impl
region of `scalePoint` is a single A-tagged delegation to the deep-modeled
scaling callee (`scaleCoords`, an A-reference) with no R/I-tagged computed ops to
differential-test. `conformance_check.py` is a skip stub (status=skip). The
soundness G-CONF would provide is discharged by G-AX (§3.1). The G-AX fuzz seed
is pinned to **`17655`** for a deterministic verdict.
