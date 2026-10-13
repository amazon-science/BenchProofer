# mapping.md — sympy__sympy-11618

## Symbol binding (file:line @ base_commit 360290c4c401e386db60723ddb0109ed499c9f6e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_sqSeparation` / `problem_spec_sqSeparation` / `correct_sqSeparation` | `Point.distance(self, p)` | `sympy/geometry/point.py:237-270` (patched branch inserted at 267) |
| `sqSep (sameKind) (a b)` (pure helper) | the radicand `sum([(a - b)**2 for a, b in zip(...)])` inside the returned `sqrt(...)`, over the compared dimension | `point.py:267-281` (post-patch) |
| `commonLen (sameKind) (a b)` | the compared dimension: `min` via the truncating `zip` on the same-kind (and equal-length different-kind) paths, `max(len(p), len(self))` on the different-kind unequal branch | `point.py:267-281` |
| `sameKind : Bool` | `type(p) is type(self)` (the patch's discriminator) | `point.py:267` |
| `a : List Rat` | `self.args` (the coordinate tuple of `self`) | `point.py` `Point.args` |
| `b : List Rat` | `p.args` (the coordinate tuple of the other point `p`) | `point.py` `Point.args` |

The modeled function is `Point.distance`, the Euclidean distance between two
points. It is the only behavior the patch changes and the only behavior the
FAIL_TO_PASS test (`test_issue_11617`) observes.

### What the function does (base_commit — the buggy version)

```python
def distance(self, p):
    return sqrt(sum([(a - b)**2 for a, b in zip(
        self.args, p.args if isinstance(p, Point) else p)]))
```

`zip(self.args, p.args)` pairs coordinates index-by-index but STOPS at the
shorter of the two tuples. When the two points have different dimension (e.g. a
3-D point and a 2-D point) the trailing coordinates of the longer point are
silently dropped, so the contribution of the extra dimension is lost. For
`self.args = (1, 0, 2)` and `p.args = (2, 0)` it computes `(1-2)**2 + (0-0)**2 =
1` and returns `sqrt(1) = 1` instead of the correct `(1-2)**2 + (0-0)**2 +
(2-0)**2 = 5`, `sqrt(5)`.

### What the function does (post-patch — the fix)

```python
def distance(self, p):
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

The fix is guarded by the **kind discriminator** `type(p) is type(self)`:

* **Same kind** (fallthrough): the plain truncating `zip(self.args, p.args)`,
  which stops at the shorter tuple — compared dimension `min(len(self), len(p))`.
  Two same-kind points of differing coordinate count are NOT padded; the surplus
  is dropped exactly as before. (This is the behavior an earlier
  unconditional-`max` model got wrong.)
* **Different kind, equal length**: the same truncating `zip` (`min = max`).
* **Different kind, unequal length**: build `p1 = [0]*max(len(p),len(self))`,
  copy the SHORTER point's coordinates into its leading entries, pair against the
  LONGER point `p2`. I.e. zero-pad the shorter tuple up to `max(...)` and sum
  squared differences over all `max` dimensions — the surplus coordinate(s) of
  the longer point are paired against `0`, not dropped.

### Lean modeling

- A point's coordinate tuple is modeled as `a b : List Rat` (numeric
  coordinates; SymPy `sympify`s/`nsimplify`s float coordinates to exact
  rationals). Coordinate order is preserved, so `List` is the carrier.
- `sameKind : Bool` models `type(p) is type(self)`.
- `commonLen sameKind a b = if sameKind then min a.length b.length else
  max a.length b.length` is the compared dimension: `min` on the same-kind path
  (the truncating `zip`, which also covers the equal-length different-kind path
  since there `min = max`), `max` on the different-kind unequal branch.
- The function returns `sqrt(<radicand>)`. `sqrt` is an UNCHANGED outer wrapper,
  applied identically before and after the patch, injective and monotone on the
  non-negative reals; the entire behavioral difference lives in the radicand. We
  model the observable result as that radicand, `result : Rat`, and treat `sqrt`
  as a type-only outer refinement (refinement.md A7, tag R). Pinning the radicand
  pins the distance.
- `sqSep sameKind a b` is the radicand: sum `(aᵢ - bᵢ)²` over
  `i ∈ [0 : commonLen sameKind a b)`, reading an out-of-range coordinate as `0`
  (`getD i 0`) — the `[0]*max(...)` zero-embedding of the shorter tuple on the
  padded branch; on the `min` branch no read is out of range, matching the
  truncating `zip`.
- The pre-patch impl loops to `min a.length b.length` UNCONDITIONALLY (the buggy
  `zip`, which ignores the kind), so trailing coordinates of the longer tuple are
  dropped even when `sameKind = false`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.args` (numeric coordinate tuple) | `a : List Rat` | coordinate list, order-preserving |
| `p.args` (numeric coordinate tuple) | `b : List Rat` | coordinate list, order-preserving |
| `type(p) is type(self)` | `sameKind : Bool` | `True` ↔ same concrete class; `False` ↔ different class |
| `len(self)` / `len(p)` | `a.length` / `b.length` | dimension |
| the compared dimension | `commonLen sameKind a b` | `if sameKind then min else max`; `min` = truncating `zip`, `max` = the padded different-kind branch |
| `[0]*max(...)` zero-pad / out-of-range read | index `i ∈ [0 : commonLen …)` reading `getD i 0` | out-of-range coordinate = 0 |
| `(a - b)**2` | `(a.getD i 0 - b.getD i 0)^2` | squared coordinate difference (exact `Rat`) |
| `sum([...])` | the fold of the per-index squares | radicand |
| `sqrt(<radicand>)` | (outer wrapper, modeled away) | injective/monotone on ℚ≥0; result = radicand |

The kind discriminator is load-bearing: two points of the **same** class with
different coordinate counts are compared in the `min` (truncating) dimension —
the gold code does NOT pad them; only the **different-kind** unequal path pads to
`max`. A model that padded to `max` unconditionally would diverge from the gold
on same-kind differing-dimension bare `Point`s (e.g. spec `25` vs gold `0`).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — which coordinate
  pairs enter the sum-of-squares, keyed on the kind discriminator — is modeled
  DEEPLY and structurally over the two coordinate lists and `sameKind`; one must
  not axiomatize a deeply-modeled changed decision. The `axioms` region is empty
  and **G-AX skips**.
- `sqrt`, `sum`, `zip`, `(·)**2`, `len`, `type(...)`, `isinstance(...)` are all
  UNCHANGED operations. Arithmetic and aggregation are modeled concretely (`^2`,
  the fold); `sqrt` is the injective outer wrapper modeled away. None constrains
  an output component the spec leaves free — `result` is the radicand, fully
  pinned to `sqSep sameKind a b`.
- Flag dependency: `distance` reads the two coordinate tuples, their lengths, and
  the kind discriminator `type(p) is type(self)`. The `type(p) is not type(self)`
  / `len(p) == len(self)` branch structure is captured by `sameKind` +
  `commonLen`'s `if sameKind then min else max`.

## G-CONF fuzz seed

Pinned LCG seed: **11618** (see `conformance_check.py` `SEED`). Corpus: random
coordinate lists of varying (often unequal) lengths over a bounded rational
range, paired as both same-kind and different-kind, plus hand-picked edge cases
pinning the discriminating clause — different-kind unequal-length inputs where
the shorter tuple must be zero-padded to the larger dimension (e.g. `[1,0,2]` vs
`[2,0]` with `sameKind = false` → radicand `5`, not `1`) and same-kind
unequal-length inputs where it must truncate (→ `min` dimension, no padding).
The R/I shadow of `implementation_sqSeparation` (squared separation) is diffed
against an in-process replica of the POST-PATCH `distance` radicand over ≥1e5
fuzzed inputs.
