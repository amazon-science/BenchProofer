# refinement.md — sympy__sympy-12481

The operation-by-operation correspondence between `model.py`'s implementation
(the `compose_cycles` impl region + the deep `swap_val` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, the proof uses the axiom's `Ensures`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `Permutation.__new__` cyclic-form guard

Gold hunk (`sympy/combinatorics/permutations.py`):
```
  temp = flatten(args)
- if has_dups(temp):
-     if is_cycle:
-         raise ValueError('there were repeated elements; to resolve '
-         'cycles use Cycle%s.' % ''.join([str(tuple(c)) for c in args]))
-     else:
-         raise ValueError('there were repeated elements.')
+ if has_dups(temp) and not is_cycle:
+     raise ValueError('there were repeated elements.')
  temp = set(temp)
```

The effect: for cyclic-form input (`is_cycle` true), duplicate (non-disjoint)
elements are NO LONGER rejected; control falls through to the existing cyclic
composition arm

```python
c = Cycle()
for ci in args:
    c = c(*ci)
aform = c.list()
```

which composes the cycles **left to right** into the array form — already the
behaviour for disjoint cycles, now reached for non-disjoint ones too.

| # | model.py impl op (`compose_cycles`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a, b, c, d : int` (two GENUINE two-element cycles, `a != b ∧ c != d` per `Requires`) and `n : int` (point count) | the cyclic-form `args = [[a,b],[c,d]]` and the resulting `size` | R | a cycle list ↔ point indices; the array length ↔ `n` (mapping.md §2). The model `Requires` domain `a != b ∧ c != d` is exactly the real callee's accepting set — the within-cycle uniqueness check (untouched by the change) rejects `[e,e]`, while only the cross-cycle non-disjoint rejection is removed; the two cycles MAY still share a point with each other. The smallest non-trivial cycles (genuine swaps) encode the F2P / problem witnesses `[[0,1],[0,2]]` and `[[0,1],[0,1]]`. The F2P-removed witness `[[1],[1,2]]` pairs a SINGLETON cycle `[1]` (the identity on point 1 — NOT the swap `(1 1)`, which raises) with the swap `(1 2)`; it lies OUTSIDE the two-genuine-swap domain and is validated separately by axiom_check.py's faithful `single_then_swap` model, not by `compose_cycles`. |
| A2 | the duplicate guard is ABSENT from `compose_cycles` — every `(a,b,c,d)` satisfying `Requires` produces a composed array (postcondition is total over the input domain) | `if has_dups(temp) and not is_cycle: raise` — the `is_cycle` arm of the raise is removed | I (the removed control edge) + the spec encodes its absence | the model has no rejection branch and the postcondition `Ensures` the composition for ALL in-range `(a,b,c,d)`, disjoint or not. This is exactly "the cyclic-form raise is gone": there is no input for which the construction is undefined. `model_prepatch.py` re-adds the rejection (skips the composition when the two cycles share a point) and FAILS this total postcondition — the spec sensing the change (G-DIFF). |
| A3 | build the identity array `0..n-1` (first loop), then apply `swap_val(·, a, b)` point-wise (second loop), then `swap_val(·, c, d)` (third loop); position `i` ends as `swap_val(swap_val(i, a, b), c, d)` | `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()` (the composition arm now reached) | A-reference | the changed-into-reachable operation is modelled **deeply**: `swap_val` (the pure region) and the verified loops in `compose_cycles` ARE the left-to-right cycle composition. There is no consumed composition axiom — the proof depends on none. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `Permutation([[a,b],[c,d]], size=n).array_form` (built from `Cycle` composition) on exhaustive (n≤6) + fuzz inputs and asserts equality with `swap_val(swap_val(i,a,b),c,d)`. `Cycle.__call__` composes left-to-right (mapping.md §3.1), so the model loop and the real callee compute the same function. |
| A4 | `result` (a `List[int]` of length `n`) returned | `aform` passed to `_af_new` / `Basic.__new__`, becoming the `Permutation`'s `_array_form` | R | a `Permutation` is identified by its array form (`_hashable_content == tuple(array_form)`, mapping.md §2); the F2P assertion compares `Permutation`s, i.e. compares array forms. `compose_cycles` returns exactly that array form. |

## B. The discriminator

The behavioural change the F2P test observes is that a cyclic-form input with
**repeated (non-disjoint) elements is accepted and composed** instead of
rejected:

- F2P added: `Permutation([[0, 1], [0, 2]]) == Permutation(0, 1, 2)`
  → array `[1, 2, 0]`. Model: `compose_cycles(3, 0, 1, 0, 2) == [1, 2, 0]` (two
  GENUINE swaps sharing point `0`, i.e. cross-cycle non-disjoint; both cycles
  satisfy `a != b`/`c != d`, so this is squarely in the model domain). Pre-patch
  this `raise`d. **This is the G-DIFF discriminator** the model proves and
  `model_prepatch.py` fails.
- Problem statement: `Permutation([[0, 1], [0, 1]])` builds the identity.
  Model: `compose_cycles(2, 0, 1, 0, 1) == [0, 1]` (two genuine swaps that
  coincide; in-domain).
- F2P removed: `raises(ValueError, lambda: Permutation([[1], [1, 2]]))`
  → now constructs to `[0, 2, 1]`. Here `[1]` is a SINGLETON cycle (the identity
  on point 1) sharing point 1 with the swap `(1 2)` — it is NOT a pair of genuine
  two-element swaps, so it lies OUTSIDE `compose_cycles`'s domain (`a != b`/`c != d`).
  It is validated by axiom_check.py's faithful `single_then_swap` model
  (singleton = identity, then swap): `single_then_swap(3, 1, 1, 2) == [0, 2, 1]`,
  and the real callee is asserted to construct it without raising. (Encoding it
  as `compose_cycles(3, 1, 1, 1, 2)` would be UNFAITHFUL: `[1,1]` is not a real
  cycle — the callee raises "All elements must be unique in a cycle".)

`model_prepatch.py` reproduces the bug by re-introducing the rejection (it
applies the second swap only when the cycles are disjoint, i.e. share no point);
its `compose_cycles` then leaves non-disjoint inputs uncomposed and **fails** the
total postcondition `ToSeq(Result())[i] == swap_val(swap_val(i, a, b), c, d)`,
which is exactly the spec sensing the change (G-DIFF). The disjoint P2P cases
(`test_Cycle`, `test_mul`, …) are unaffected — both patches compose disjoint
cycles identically.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that the change
makes reachable for new inputs — the left-to-right cycle composition — is
modelled **deeply** (`swap_val` + the verified composition loops, step A3, an
**A-reference**), not hidden behind an axiom about the function under change.
There is **no consumed axiom** at all: the `Cycle` machinery the branch calls is
unchanged and appears only as the A-reference that G-AX validates the deep model
against.

## D. verify(model) ⇒ resolved

`compose_cycles` verifies only if its output equals the exact left-to-right
composition `swap_val(swap_val(i, a, b), c, d)` for EVERY in-range `(a,b,c,d)`
(A2 + A3) — there is no rejected input. By R (cycle list ↔ point indices, array
form ↔ `_array_form`) the verified result equals the `aform` the gold patch's
cyclic arm produces; by G-AX the deep model equals the real `Cycle`/`Permutation`
construction (A-reference) on exhaustive + fuzz inputs including all non-disjoint
configurations. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited deep-model reference —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: the A-reference soundness (G-AX) and refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because no axiom is
consumed.
