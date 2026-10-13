# refinement.md — sympy__sympy-15809

The operation-by-operation correspondence between `model.py`'s implementation
(the `lattice_reduce` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The constructor — `MinMaxBase.__new__` (`sympy/functions/elementary/miscellaneous.py:341`)

Gold hunk (delete the empty-args guard):
```python
 class MinMaxBase(Expr, LatticeOp):
     def __new__(cls, *args, **assumptions):
-        if not args:
-            raise ValueError("The Max/Min functions must have arguments.")

         args = (sympify(arg) for arg in args)
```
After the deletion the empty collection flows to the pre-existing
`if not args: return cls.identity` branch (`:361-362`).

| # | model.py impl op (`lattice_reduce`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `operands: List[int]` | the variadic `*args` (after `sympify`) | R | the operand collection ↦ `List[int]`; only cardinality is observed (`not args` ↔ `len(operands) == 0`), mapping.md §2. Read-only ⇒ `Acc(list_pred(operands), 1/2)`. |
| A2 | parameters `identity`/`zero`/`single`/`aggregate` (pairwise distinct ints) | `cls.identity` / `cls.zero` / `list(args).pop()` / `Expr.__new__(cls, _args, ...)` | R | the four possible return values ↦ distinct sentinels (mapping.md §2). For `Min`: `identity = oo`, `zero = -oo`; for `Max`: `identity = -oo`, `zero = oo`. Distinctness lets each postcondition clause pin exactly one branch. |
| A3 | **(no node)** — there is no `if len(operands) == 0: raise` at the top of the impl | the **DELETED** guard `if not args: raise ValueError(...)` | R + I | **the fix.** The gold patch *removes* the empty-args rejection; the model's faithful skeleton therefore has *no* leading raise. The empty collection falls through to the empty-canonical-set branch (A6) exactly as the patched code falls through to `if not args: return cls.identity`. `model_prepatch.py` re-introduces the deleted `raise` (as `raise EmptyReductionRejected()`) and **fails** verification — the spec sensing the change (G-DIFF). |
| A3b | `if has_noncomparable_operand(operands): raise NonComparableOperand()` | the comparability guard inside `cls._new_args_filter` — `raise ValueError("...is not comparable.")` (`:521-523`), UNCAUGHT, propagating out of `__new__` | A-consumed | the comparability pre-filter is UNCHANGED by the patch. `has_noncomparable_operand` is the weakest contract the proof needs: an empty collection has no non-comparable operand (`Implies(len==0, not Result())`, mapping.md §3.0); the proof consumes it to discharge the empty→identity clause. The unchanged rejection is pinned by TWO clauses working together: `Exsures(NonComparableOperand, has_noncomparable_operand(operands))` admits the exception ONLY when an operand is non-comparable (it does not, by itself, OBLIGATE the raise — an Exsures grants permission, not obligation), and `Ensures(not has_noncomparable_operand(operands))` OBLIGATES it (a normal return is admissible only when no operand is non-comparable, so a non-comparable collection MUST raise — it can never silently return a value). The propagated builtin `ValueError` ↦ the user-defined `NonComparableOperand`. This is part of the F2P contract: `raises(ValueError, lambda: Min(I))`, `Max(S.ComplexInfinity, 1)`, `Min(cos(x), sin(x)).subs(x, I)`, etc. remain in `test_Min`/`test_Max`. G-AX confirms it against the real `Min`/`Max`. |
| A4 | `if has_absorbing_operand(operands): return zero` | `try: args = frozenset(cls._new_args_filter(args)) except ShortCircuit: return cls.zero` (`:349-352`) | A-consumed | `has_absorbing_operand` is the weakest contract on the unchanged `ShortCircuit` pre-filter the proof needs: an empty collection admits no absorbing operand (mapping.md §3.1). The proof consumes its `Ensures(Implies(len==0, not Result()))` to discharge the empty-collection clause (A6/A7). G-AX confirms it against the real `Min`/`Max`. |
| A4b | `if not canonical_reduction_defined(operands): raise ReductionUndefined()` | the same unchanged pair `cls._collapse_arguments(args, ...)` / `cls._find_localzeros(args, ...)` (`:356-359`) taken as a PARTIAL map: `_find_localzeros` asks `cls._is_connected(v, z)` (`:552`), whose `r = hit(x >= y, Max, Min)` (`:574`) evaluates `Expr.__ge__` (`sympy/core/expr.py:295`) and can propagate `TypeError("Invalid comparison of complex %s")` (or leave the relational undecided) instead of returning a set | A-consumed | this pass is a **DIFFERENT observation** from A3b's scan, and the model must carry both. The scan judges each operand ALONE (`:521-523`), so `x + I` (`is_real is None`, not a number) is passed over — yet `Min(x, x + I)` propagates `TypeError('Invalid comparison of complex I')`, and `Min(sign(x), Order(x))` propagates `NotImplementedError`. A spec with only A3b's predicate would predict a normal four-outcome return there, which the real callee does not do. The pass is UNCHANGED by the patch (base and patched agree on this whole class), so the leg is pinned, not conditioned away: `Exsures(ReductionUndefined, ...)` admits the failure only where the scan is clean, no absorbing operand collapsed the reduction, and the pass is undefined; `Ensures(has_absorbing_operand(operands) or canonical_reduction_defined(operands))` OBLIGATES it by forbidding a silent normal return there. The axiom's only consumed property is `Implies(len==0, Result())` — an empty collection leaves the pass nothing to compare (mapping.md §3.3) — which is what keeps A6 provable on the empty collection. G-AX confirms the predicate is non-trivial (18 real collections whose scan is clean and whose pass still fails) and vacuously true where the scan already decided. |
| A5 | `count = canonical_count(operands)` | `args = cls._collapse_arguments(args, ...); args = cls._find_localzeros(args, ...)` then reading `len(args)` (`:356-365`) | A-consumed | `canonical_count` is the weakest contract on the unchanged canonical-set reduction: count `>= 0`, and an empty collection reduces to count 0 (mapping.md §3.2). **PARTIAL**: `Requires(canonical_reduction_defined(operands))`, because where the pass propagated a comparison failure it produced no set and `len(args)` is never reached. The impl reads it only after the A4b guard, and every postcondition clause that mentions it carries the definedness antecedent, so the precondition is discharged at each use. |
| A6 | `if count == 0: return identity` | `if not args: return cls.identity` (`:361-362`) | A-consumed + I | the empty-canonical-set branch returns the identity element. Identical control flow; the test `not args` ↔ `count == 0` via A5. **This is the branch the deleted guard used to pre-empt for the empty input** — its reachability on the empty collection IS the fix. |
| A7 | `if count == 1: return single` | `if len(args) == 1: return list(args).pop()` (`:364-365`) | R + I | the single-survivor branch returns the sole operand. `len(args) == 1` ↔ `count == 1` via A5; `list(args).pop()` ↦ the `single` sentinel. Unchanged by the patch. |
| A8 | `return aggregate` | the base creation `Expr.__new__(cls, _args, ...); obj._argset = _args; return obj` (`:367-371`) | R | the ≥2-survivor branch assembles the aggregate. ↦ the `aggregate` sentinel. Unchanged by the patch. |

The discriminating content of the change — the EMPTY operand collection must
RETURN NORMALLY and yield the identity element, rather than be rejected — lives
in step A3 (the *absence* of the leading raise) realised through A6 (the empty
flows to `return cls.identity`). The pre-patch had the rejecting guard;
`model_prepatch.py` reproduces it (`if len(operands) == 0: raise
EmptyReductionRejected()`) and **fails** verification: on the empty collection it
raises an exception the spec does not admit (the permitted `Exsures` are
`NonComparableOperand` guarded by `has_noncomparable_operand(operands)` and
`ReductionUndefined` guarded by `not canonical_reduction_defined(operands)`, and
BOTH guards are False on the empty collection by their axioms), so the
postcondition "method only raises exceptions of types NonComparableOperand,
ReductionUndefined" cannot hold and
`Implies(len(operands) == 0, Result() == identity)` is unprovable. That is
exactly the spec sensing the change (G-DIFF), and the exact F2P observation:
`Min() == S.Infinity` and `Max() == S.NegativeInfinity` (no longer
`raises(ValueError)`).

The UNCHANGED comparability rejection is preserved by step A3b: a collection
containing a non-comparable operand STILL raises. This is pinned by the pair
`Exsures(NonComparableOperand, has_noncomparable_operand(operands))` (the
exception is *admissible* only when an operand is non-comparable) together with
`Ensures(not has_noncomparable_operand(operands))` (a normal return is
*admissible* only when NO operand is non-comparable). The `Exsures` alone grants
permission to raise but does NOT obligate it; the `Ensures` supplies the
obligation by forbidding the only alternative (silently returning a value). With
both, a non-comparable collection has no admissible normal outcome and must
raise. So the spec does NOT reject the gold impl — which continues to raise
`ValueError` on `Min(I)` / `Max(S.ComplexInfinity, 1)` / `Min(cos(x),
sin(x)).subs(x, I)` — and the four-outcome totality is correctly conditioned on
the absence of a non-comparable operand. Crucially, the spec now also REJECTS a
same-spec impl that drops the non-comparable raise (returning a normal outcome
instead): such an impl violates `Ensures(not has_noncomparable_operand(operands))`
on a non-comparable input, which is exactly the residual spec-too-weak hole the
re-audit caught (`atk_2`) and this clause closes.

The two predicates `has_noncomparable_operand` / `has_absorbing_operand` model
the two possible **first decisive events of the ONE ordered scan**
`_new_args_filter` (`:519-526`), which `raise`s and therefore terminates at the
first decisive operand. They are NOT containment tests over the collection, and
the model records their mutual exclusivity as
`Ensures(Implies(Result(), not has_noncomparable_operand(operands)))` on
`has_absorbing_operand`. This is load-bearing on the class
`{absorbing, non-comparable}`: `Min(-oo, I) == -oo` and `Max(oo, I) == oo` — the
scan collapses on the annihilator before it ever inspects the non-comparable
operand — while `Min(I, -oo)` and `Max(I, oo)` raise `ValueError`. A containment
reading would predict a rejection for all four and would therefore reject the
gold callee's own behaviour on the first two; the exclusivity clause is exactly
what makes the absorbing branch provable there. `axiom_check.py` checks it
against the real scan on both orders, and the `Exsures`/obligation pair pins the
rejection precisely on collections whose scan REACHES a non-comparable operand
first — which is what the F2P tests assert (`Min(I)`, `Min(I, x)`,
`Max(S.ComplexInfinity, 1)`, the `subs` path: none carries an absorbing operand
ahead of the non-comparable one).

The UNCHANGED canonical-set failure is preserved by step A4b, and it is a
SEPARATE class from A3b's — the two callees make different observations. The scan
asks of each operand alone "is this comparable?"; the canonical-set pass asks of
two survivors "can these be placed against one another?". A collection can pass
the first and fail the second: the scan passes `x + I` over (`is_real` is `None`,
not `False`, and it is not a number), yet `_find_localzeros` reaches
`_is_connected(x, x + I)` (`:552`), whose `x >= x + I` (`:574`) raises
`TypeError('Invalid comparison of complex I')` out of `Expr.__ge__`
(`sympy/core/expr.py:295`); `Min(sign(x), Order(x))` propagates
`NotImplementedError` the same way. That is behaviour of the real callee that a
scan-only spec would have contradicted, since it would have predicted one of the
four normal outcomes. So the leg is pinned the same way A3b's is — an `Exsures`
for admissibility plus
`Ensures(has_absorbing_operand(operands) or canonical_reduction_defined(operands))`
for the obligation — with the guard narrowing it to exactly the class where the
pass is REACHED (the scan clean, no absorbing operand) and undefined. Nothing
about the empty collection changes: its scan is clean and its pass has nothing to
compare, so by the two axioms both failure guards are False there and A6 still
discharges `Implies(len(operands) == 0, Result() == identity)`. The base and
patched constructors agree on the whole undefined-pass class, so the leg costs the
change-sensing nothing: `model_prepatch.py` still fails.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— removing the empty-args rejection so the empty collection returns the identity
element — is modeled **directly** by the absence of a leading raise in the impl
(A3) and the reachable empty-canonical-set branch (A6) over the integer cardinality.
The four consumed axioms (`has_noncomparable_operand`, `has_absorbing_operand`,
`canonical_reduction_defined`, `canonical_count`) cover **unchanged** callees
(`_new_args_filter`'s comparability `ValueError` and `ShortCircuit`, and
`_collapse_arguments` + `_find_localzeros` in BOTH its aspects — whether it yields
a set at all, and the cardinality it yields) the constructor invokes; none is the
operation that changed. There is **no A-reference deep model** (the change is a
control-flow deletion, not a string/numeric transform). The axioms encode only
their weakest empty-collection / non-negativity properties — never the full
reduction semantics — so they are not over-claimed; in particular the spec does
NOT assert unconditional totality (which would falsely reject the gold impl's
unchanged non-comparable raise, or its unchanged propagation of a comparison
failure out of the canonical-set pass) — it pins BOTH unchanged failures with
guarded `Exsures` clauses plus their return-forbidding obligations, and conditions
the four-outcome totality on the absence of a non-comparable first event AND the
definedness of the canonical-set pass.

## C. verify(model) ⇒ resolved

`lattice_reduce` verifies only if (a) it is TOTAL when no operand is
non-comparable and the canonical-set pass is defined — it returns one of the four
outcomes and raises ONLY `NonComparableOperand` (and that only when
`has_noncomparable_operand(operands)`) or `ReductionUndefined` (and that only on
the exact class where the pass is reached and undefined)
(this is what `model_prepatch.py` fails on, because its leading raise on the
empty collection — which is comparable and whose pass is defined — escapes as a
disallowed exception),
(b) the empty collection yields the identity element
(`Implies(len(operands) == 0, Result() == identity)`, discharged via the
A3b/A4/A4b/A5 axioms: no non-comparable operand + no absorbing operand + a defined
pass + count 0 ⇒ the A6 branch), (c) a non-comparable operand is REJECTED with
`NonComparableOperand` —
pinned by BOTH `Exsures(NonComparableOperand, has_noncomparable_operand(operands))`
(the exception is admissible only on a non-comparable collection) AND
`Ensures(not has_noncomparable_operand(operands))` (a normal return is admissible
only on a fully-comparable collection, so a non-comparable operand can never
silently return a value — it MUST raise); together these make the rejection an
obligation, not a mere permission, matching the unchanged comparability path the
F2P tests still assert as `raises(ValueError, ...)`, (c') a collection whose scan
is clean and uncollapsed but whose canonical-set pass cannot compare the survivors
FAILS with `ReductionUndefined` — pinned by BOTH
`Exsures(ReductionUndefined, not has_noncomparable_operand and not
has_absorbing_operand and not canonical_reduction_defined)` (admissible on exactly
that class) AND `Ensures(has_absorbing_operand(operands) or
canonical_reduction_defined(operands))` (a normal return is admissible only when
the scan decided or the pass is defined), matching the unchanged
`_find_localzeros`/`_is_connected`/`Expr.__ge__` path the real callee takes on
`Min(x, x + I)`, and (d) the absorbing/single/aggregate branches map to
`zero`/`single`/`aggregate`. By R (`*args` ↦ `List[int]` cardinality;
`cls.identity`/`cls.zero`/the survivor/the aggregate ↦ the four sentinels) and A
(the four unchanged pre-reduction callees), the verified function equals the
patched `MinMaxBase.__new__` on the tested inputs: on the empty collection the
patched code falls through to `return cls.identity` (= `oo` for `Min`, `-oo` for
`Max`) and the model returns `identity`; on a non-comparable operand the patched
code raises `ValueError` and the model raises `NonComparableOperand`; on a
collection whose canonical-set pass propagates its comparison failure the patched
code raises that failure and the model raises `ReductionUndefined`; the
pre-patch raised on the empty collection. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
four audited unchanged callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX, §3 of
mapping.md) and refinement fidelity (this document, G-EQ).
