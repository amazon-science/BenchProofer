# mapping.md — sympy__sympy-17655

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f5e965947af2410ded92cfad987aaf45262ea434`, states the type
abstraction, and gives the provenance of the deep model (callee source + the
exact behaviour the deep model encodes).

Repo file under change: `sympy/geometry/point.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `mul_left(factor, point)` | `Point.__rmul__(self, factor)` — `sympy/geometry/point.py` (inserted after `__mul__`, body line 279) | the modeled NEW changed function (left scalar multiplication) |
| `mul_right(point, factor)` | `Point.__mul__(self, factor)` — `sympy/geometry/point.py:250` (body lines 277-279) | the unchanged right scalar multiplication that `__rmul__` delegates to; modeled as its own contracted function (it is under spec, not an axiom) |
| `scaled(s, factor)` *(deep model — A-reference)* | the per-coordinate map `[simplify(x*factor) for x in self.args]` inside `__mul__` (`point.py:278`), wrapped by `Point(coords, evaluate=False)` (`point.py:279`) | pure spec: the per-coordinate scaling of a whole point; the deep model of the scaling operation, validated `scaled == real Point.__mul__/__rmul__` coordinates by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo state the change addresses (for the refinement audit, not
referenced from the consumer spec view): `Point` defines `__mul__` (right
multiplication) but has **no** `__rmul__`, so `factor * point` falls back to the
numeric factor's own `__mul__`, which returns `NotImplemented` for a plain int
(→ `TypeError`) or an unevaluated `Mul` for a SymPy factor — never a scaled
point.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `Point` / its `self.args` (`Tuple` of SymPy coordinate `Expr`) | `List[int]` of coordinate values | coordinate `k` ↔ `point[k]`; the point's dimension `len(self)` ↔ `len(point)`; the tested coordinates (`1,1` and `1,1,1`) are concrete integers |
| `factor` (a SymPy number, e.g. `Integer(5)` after `sympify`) | `int` | `factor` ↔ the integer factor; the F2P factor is `5` |
| `sympify(factor)` coercion (`point.py:277`) | identity on the int | `sympify(5)` is the integer `5`; observationally the identity on the tested factor |
| `simplify(x*factor)` (`point.py:278`) | integer multiplication `point[k] * factor` | for integer coordinates and an integer factor, `simplify(x*factor)` is exactly the integer product (`simplify(1*5) == 5`); the F2P inputs are integers |
| `Point(coords, evaluate=False)` constructor (`point.py:279`) | the `List[int]` `coords` itself | `Point(coords, evaluate=False)` is the point whose coordinate sequence is exactly `coords`; modeled as the identity on the coordinate list (dimension and values preserved) |

`Point` indexing / iteration over SymPy expressions is outside Nagini's
fragment, so the carrier is `List[int]` throughout; the specification is phrased
over `PSeq[int]` via `ToSeq`.

## 3. Callee / deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `scaled` deep model ↔ `Point.__mul__` / `Point.__rmul__` (A-reference)
**Callee:** `sympy.geometry.Point.__mul__` (the unchanged right multiplication)
and `sympy.geometry.Point.__rmul__` (the post-patch left multiplication, which
delegates: `return self.__mul__(factor)`). Source at base_commit
(`sympy/geometry/point.py`, `__mul__`):

```python
def __mul__(self, factor):
    factor = sympify(factor)
    coords = [simplify(x*factor) for x in self.args]
    return Point(coords, evaluate=False)
```

Gold-added `__rmul__`:

```python
def __rmul__(self, factor):
    """Multiply a factor by point's coordinates."""
    return self.__mul__(factor)
```

Because `__rmul__` delegates verbatim to `__mul__`, left multiplication
`factor * point` produces a `Point` whose i-th coordinate is `simplify(point[i]
* factor)`. On the integer carrier this is the per-coordinate integer product
`point[i] * factor`, which is exactly what the deep model `scaled` / the
verified `mul_right` loop encode. The dimension is preserved (the list
comprehension and `Point(coords, evaluate=False)` keep one coordinate per input
coordinate).

**Soundness check (G-AX):** `axiom_check.py` constructs real `Point` objects and
runs the real `point * factor` (`__mul__`) and `factor * point` (`__rmul__`) on
boundary cases (the 2D and 3D F2P cases `5 * Point(1,1)` / `5 * Point(1,1,1)`,
zero/unit/negative factors, negative and zero coordinates, dimensions 2-5) plus
2000 randomized fuzz inputs. It asserts the deep model `scaled(coords, factor)`
equals the coordinates of both the real right and the real left multiplication,
and that left == right (the commutativity property the gold patch establishes).
It imports only the public `sympy.geometry.Point`, the very class the gold patch
edits. Exit 0 iff sound.

There are **no `@ContractOnly` axioms** in this bundle: the `axioms` region of
`model.py` is empty (the scaling is modeled deeply, not axiomatized).
