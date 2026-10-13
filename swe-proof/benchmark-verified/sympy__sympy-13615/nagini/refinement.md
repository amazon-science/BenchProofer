# refinement.md — sympy__sympy-13615

The operation-by-operation correspondence between `model.py`'s implementation
(the `complement_finite` impl region, the deep `keep_out` / `keep_undecided`
selection folds, and the live `verdict` axiom) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The FiniteSet branch of `Set._complement` (`sympy/sets/sets.py:219`)

Gold hunk (replaces the single comprehension):
```python
- return FiniteSet(*[el for el in other if self.contains(el) != True])
+ from sympy.utilities.iterables import sift
+
+ def ternary_sift(el):
+     contains = self.contains(el)
+     return contains if contains in [True, False] else None
+
+ sifted = sift(other, ternary_sift)
+ # ignore those that are contained in self
+ return Union(FiniteSet(*(sifted[False])),
+     Complement(FiniteSet(*(sifted[None])), self, evaluate=False)
+     if sifted[None] else S.EmptySet)
```

| # | model.py impl op (`complement_finite`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `other: List[int]` of element handles | `other` (a `FiniteSet`, iterated element by element) | R | each element ↔ a distinct `int` handle; iteration order ↔ list order (mapping.md §2). The only operation on an element is the membership query, modeled by `verdict` (A3). |
| A2 | `e = other[i-1]` walked over every index (backward loop) | `for el in other` (inside `sift` and the `ternary_sift` it calls) | R/I | enumerate every element exactly once; order preserved (the backward walk + front-prepend reconstructs input order, matching `sift`'s order-preserving `defaultdict(list)`). |
| A3 | `v = verdict(e)` ∈ {0,1,2} | `contains = self.contains(el); ternary_sift -> {False, True, None}` | A-consumed | `verdict` is the weakest contract on `self.contains` (collapsed by `ternary_sift`) the partition needs: totality + the three-value range (mapping.md §3.1). The proof consumes only `Ensures(0 <= Result() <= 2)`. G-AX confirms it against the real `Set.contains`. `True`/`S.true` ↔ 1, `False`/`S.false` ↔ 0, `None`/unevaluated ↔ 2. |
| A4 | `if v == DEFINITELY_OUT: out = [e] + out` — accumulate the DEFINITELY-OUT elements in order (`ToSeq(out) == keep_out(...)`) | `sifted[False]` bucket → `FiniteSet(*(sifted[False]))` | R/I + A-reference | the `sifted[False]` bucket IS the order-preserving sub-selection of elements whose verdict is `False`; `keep_out` is that selection spelled out deeply (front-recursive fold over `verdict`). The deep fold is validated == the real bucketing by G-AX (the survivors collection of the gold `_complement` equals `keep_out`). `FiniteSet(*...)` over a list of distinct handles ↔ the concrete survivors collection (R). |
| A5 | `elif v == UNDECIDED: undecided = [e] + undecided` — accumulate the UNDECIDED elements in order (`ToSeq(undecided) == keep_undecided(...)`) | `sifted[None]` bucket → `FiniteSet(*(sifted[None]))` inside `Complement(..., self, evaluate=False)` | R/I + A-reference | the `sifted[None]` bucket IS the order-preserving sub-selection of elements whose verdict is undecidable; `keep_undecided` is that selection spelled out deeply. The deep fold is validated == the real bucketing by G-AX (the pending collection of the gold `_complement` equals `keep_undecided`). |
| A6 | the implicit third bucket: `v == DEFINITELY_IN` elements are appended to NEITHER list | `sifted[True]` is never read (only `sifted[False]` and `sifted[None]` are) | I | the DEFINITELY-IN elements are dropped from both collections (they are members of `self`, hence not in the complement). |
| A7 | `return out, undecided` (the two buckets) | `return Union(FiniteSet(*(sifted[False])), Complement(FiniteSet(*(sifted[None])), self, evaluate=False) if sifted[None] else S.EmptySet)` | R | the model returns the two buckets; assembling them into the `Union` of the concrete survivors and the unevaluated `Complement` of the pending collection (or `S.EmptySet` when none are pending) is UNCHANGED sympy set-algebra the patch does not modify (mapping.md §2 note). The empty-pending guard (`if sifted[None] else S.EmptySet`) ↔ the model's `undecided == []` case (then `keep_undecided` is empty and the pending term contributes nothing). |

The discriminating content of the change — an UNDECIDED element must be carried
in the **separate pending collection** (`Result()[1]`), never folded into the
concrete survivors (`Result()[0]`) — lives in the two postconditions
`ToSeq(Result()[0]) == keep_out(...)` and `ToSeq(Result()[1]) ==
keep_undecided(...)`, where `keep_out` selects ONLY verdict-0 elements and
`keep_undecided` selects ONLY verdict-2 elements. The pre-patch comprehension
`[el for el in other if self.contains(el) != True]` placed BOTH verdict-0 and
verdict-2 elements in one bucket and produced no pending collection;
`model_prepatch.py` reproduces that (`if v != DEFINITELY_IN: out = [e] + out`,
`undecided` left empty) and **fails** the postcondition `ToSeq(Result()[0]) ==
keep_out(ToSeq(other))` (it contains the verdict-2 elements `keep_out` excludes)
— exactly the spec sensing the change (G-DIFF).

## B. No consumed escape/oracle hole (directive 8)

The two postconditions pin the result to expressible **structural predicates on
the actual input carrier**: `Result()[0]` / `Result()[1]` must equal the
order-preserving sub-selections `keep_out` / `keep_undecided` of `ToSeq(other)`,
each defined by the per-element `verdict`. There is no answer-key oracle equated
to `Result()`: a wrong impl cannot echo a constant, because the result must be
*produced by* selecting the input elements whose `verdict` is 0 (resp. 2) — the
folds are over the input handles, with `verdict` the only opaque ingredient, and
`verdict` carries only a range (not a per-element value), so the partition is
forced to follow the real oracle. `verdict` is **A-consumed** (its `Ensures`
range is the only axiom the proof uses); `keep_out` / `keep_undecided` are the
deep models of the two `sift` buckets, validated **A-reference** against the
gold `_complement` by G-AX. Read-only `other` is held at `Acc(list_pred(other),
1/2)` (Required AND Ensured), so a wrong impl cannot satisfy the spec by
mutating the input (directive 5).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
three-way partition of elements by their membership verdict — is modeled
**deeply** (the spelled-out front-recursive selection folds `keep_out` /
`keep_undecided` consumed in `complement_finite`, an **A-reference** validated
== the gold partition by G-AX), not hidden behind an axiom about the function
under change. The only consumed axiom, `verdict` (**A-consumed**), covers the
**unchanged** callee `Set.contains` (collapsed by `ternary_sift`) the new code
invokes; it carries the weakest sufficient contract (totality + range {0,1,2}).

## D. verify(model) ⇒ resolved

`complement_finite` verifies only if its first output is exactly the
DEFINITELY-OUT sub-selection (A4) and its second output is exactly the UNDECIDED
sub-selection (A5), with DEFINITELY-IN elements in neither (A6). By R (element ↔
handle, iteration ↔ list order, `FiniteSet(*bucket)` ↔ concrete collection,
`Union`/`Complement` assembly = unchanged set-algebra, A1/A7) the verified
partition equals the gold patch's `sift`-driven `Union(FiniteSet(*(sifted[False
])), Complement(FiniteSet(*(sifted[None])), self, evaluate=False) if sifted[None]
else S.EmptySet)` on the tested inputs; by G-AX the deep models `keep_out` /
`keep_undecided` equal the real buckets (A-reference) and the real
`Set.contains` meets the `verdict` range axiom (A-consumed). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
