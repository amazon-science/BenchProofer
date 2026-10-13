# mapping.md — sympy__sympy-13615

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 50d8a102f0735da8e165a0369bbb994c7d0592a6`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `sympy/sets/sets.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `complement_finite(other)` | the `elif isinstance(other, FiniteSet):` branch of `Set._complement(self, other)` — `sympy/sets/sets.py:188` (branch body line 219-220) | the modeled changed function: the set-minus of a finite collection of elements when membership cannot always be decided |
| `verdict(el)` *(axiom — A-consumed)* | `Set.contains(self, el)` — `sympy/sets/sets.py:291`, collapsed by the patch's local `ternary_sift` (`contains if contains in [True, False] else None`) to the three buckets the partition reads | unchanged membership oracle the branch consults for each element |
| `keep_out(s)` | the `sifted[False]` bucket fed to `FiniteSet(*(sifted[False]))` | pure spec: the order-preserving sub-selection of DEFINITELY-OUT elements |
| `keep_undecided(s)` | the `sifted[None]` bucket fed to `FiniteSet(*(sifted[None]))` inside `Complement(..., self, evaluate=False)` | pure spec: the order-preserving sub-selection of UNDECIDED elements |
| `DEFINITELY_OUT / DEFINITELY_IN / UNDECIDED = 0/1/2` | the three `ternary_sift` outcomes `False / True / None` | the three membership verdicts |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the single comprehension
`FiniteSet(*[el for el in other if self.contains(el) != True])`
(`sympy/sets/sets.py:220` @ base_commit) — it keeps every element whose
membership is not definitely `True` in ONE concrete `FiniteSet`, conflating the
DEFINITELY-OUT and UNDECIDED buckets.

The unchanged helper the patch introduces a call to,
`sympy.utilities.iterables.sift` (`sympy/utilities/iterables.py:624`), is a pure
bucketing utility (`defaultdict(list)` keyed by `keyfunc(i)`, preserving input
order within each bucket); it is the standard "group by key" fold and carries no
behaviour beyond order-preserving grouping. It is modeled implicitly by the two
order-preserving selection folds `keep_out` / `keep_undecided` (one per bucket
the patch reads), not as a separate axiom.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a sympy element (`Symbol`, `Integer`, `Rational`, …) inside the finite collection `other` | an opaque `int` handle | each distinct element ↔ a distinct handle; the only operation performed on an element is the membership query `self.contains(el)`, modeled by `verdict(handle)` |
| the finite collection `other` (a `FiniteSet`, iterated) | `List[int]` of handles, in iteration order | `other` ↔ the list; `sift`'s per-bucket order preservation ↔ list order; specification carried by `PSeq[int]` via `ToSeq` |
| the `FiniteSet(*(sifted[False]))` survivors | `Result()[0]` (`List[int]`) | the concrete collection of DEFINITELY-OUT elements |
| the `FiniteSet(*(sifted[None]))` carried inside `Complement(..., self, evaluate=False)` | `Result()[1]` (`List[int]`) | the still-pending collection of UNDECIDED elements |
| `self.contains(el)` ∈ {`S.true`, `S.false`, unevaluated `Contains`} collapsed by `ternary_sift` to {`True`, `False`, `None`} | `verdict(el)` ∈ {1, 0, 2} | `True`/`S.true` ↔ 1 (IN); `False`/`S.false` ↔ 0 (OUT); `None`/unevaluated ↔ 2 (UNDECIDED) |
| the outer `Union(FiniteSet(out), Complement(FiniteSet(undecided), self, evaluate=False) if undecided else S.EmptySet)` | the pair `(Result()[0], Result()[1])` | the model returns the two buckets; assembling them into the `Union`/`Complement` is unchanged set-algebra (see §3 note) |

The model deliberately stops at the two buckets. Assembling them into
`Union(FiniteSet(...), Complement(FiniteSet(...), self, evaluate=False))` and the
subsequent set-algebra simplifications (`Union` flattening, the
`Complement(FiniteSet, FiniteSet)` subtrahend pruning, `S.EmptySet` absorption)
are UNCHANGED sympy machinery the patch does not touch; the fix is exactly the
three-way partition that decides which bucket each element lands in.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `verdict` ↔ `Set.contains` collapsed by `ternary_sift` (A-consumed)
**Callee:** `Set.contains(self, other)` (`sympy/sets/sets.py:291`):

```python
def contains(self, other):
    other = sympify(other, strict=True)
    ret = sympify(self._contains(other))
    if ret is None:
        ret = Contains(other, self, evaluate=False)
    return ret
```

`contains` returns sympy's `S.true` / `S.false` when membership is decidable and
an unevaluated `Contains(...)` object otherwise. The patch's local closure

```python
def ternary_sift(el):
    contains = self.contains(el)
    return contains if contains in [True, False] else None
```

collapses this to exactly three keys: `True` (== `S.true`), `False`
(== `S.false`), and `None` (every unevaluated / undecidable case). The proof
relies on ONE property only: **totality with a three-value range** — every
element receives exactly one of {0, 1, 2}. No particular verdict is asserted for
any element; the partition is whatever the oracle says, and the impl reads the
SAME verdict the spec folds read (determinism of `contains`, which is a pure
query — `Set` is an immutable `Basic`). This is the **weakest** contract the
partition needs; the axiom does NOT claim termination of any other behaviour,
exact membership of any element, or a non-raising guarantee beyond returning one
of the three buckets (`contains` is total on sympified inputs).

`contains` is an UNCHANGED callee — the patch does not modify `contains` or
`_contains`; it only changes how the three verdicts are *partitioned*. (The
`hints_text` notes `contains` itself is imperfect for some sets, e.g.
`ComplexRegion`; that is a separate, out-of-scope defect — the verdict axiom
only claims the range {0,1,2}, which holds regardless, so it stays sound.)

**Flag dependency:** none. `contains` takes no keyword arguments here.

**Soundness check (G-AX):** `axiom_check.py` runs the real `Set.contains`
(collapsed exactly as `ternary_sift` does) over a grid of removal sets
(intervals, finite sets, `S.Naturals/Integers/Reals`) × a pool of symbols,
integers, rationals and compound expressions (112 (set, element) pairs) plus
400 randomized fuzz cases, asserting every collapsed verdict is in {0, 1, 2}
(the axiom's `Ensures` range). It then validates the end-to-end PARTITION:
on the removal sets for which the partition is the whole observable result
(intervals + unbounded sets), the gold-patched `_complement` equals the model's
`Union(FiniteSet(out), Complement(FiniteSet(undecided), self, evaluate=False)
if undecided else S.EmptySet)`, i.e. survivors == DEFINITELY-OUT and pending ==
UNDECIDED in input order (54 boundary + 400 fuzz cases). The instance
FAIL_TO_PASS witness `Complement(FiniteSet(x, y, 2), Interval(-10, 10)) ==
Complement(FiniteSet(x, y), Interval(-10, 10))` is asserted directly, and the
pre-patch single-bucket behaviour is confirmed to give a DIFFERENT result on
that witness (so the spec discriminates). FiniteSet-vs-FiniteSet removal is
range-checked but excluded from the structural comparison because it additionally
triggers the unchanged downstream `Complement(FiniteSet, FiniteSet)` reduction
(orthogonal to the partition). Imports only `sympy` (the package whose
`_complement` the patch fixes) and the standard library. Exit 0 iff sound.
