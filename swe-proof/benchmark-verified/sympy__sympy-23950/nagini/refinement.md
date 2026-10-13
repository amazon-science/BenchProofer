# refinement.md — sympy__sympy-23950

The operation-by-operation correspondence between `model.py`'s implementation
(the `solution_region` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**,
the proof uses the axiom's `Ensures`, or **A-reference**, a deep model validated
== the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `Contains.as_set()` (`sympy/sets/contains.py:47`)

Gold hunk:
```
     def as_set(self):
-        raise NotImplementedError()
+        return self.args[1]
```

`Contains(x, s)` is a `BooleanFunction`; its constructor stores the two operands
as `self.args == (x, s)` (operand order). `self.args[0]` is the asserted element
`x`; `self.args[1]` is the set `s` whose membership is asserted. The patch makes
`as_set()` return that second operand — the set — instead of raising.

| # | model.py impl op (`solution_region`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `self: MembershipAssertion` with components `self.element`, `self.region` | the `Contains` instance `self` with `self.args == (x, s)` | R | the rich `Contains`/`BooleanFunction` object is abstracted to a minimal class holding only the two touched operands: `self.element` ↔ `self.args[0]` (the element `x`, stored identically), `self.region` ↔ `self.args[1]` (the STORED set operand, equal to `s`). Object identity (`is`) on each field ↔ the same operand object stored under `args` (mapping.md §1–2). No other facet of `Contains` is touched by the change. |
| 2 | `return self.region` | `return self.args[1]` | I (under R on the field) | identical concrete operation: select and return the second stored operand object. Under the field bijection (`self.region` ↔ the stored `self.args[1]`) this is the same selection; the postcondition `Result() is self.region` ↔ "the returned object is the stored set operand `self.args[1]`", which is exactly what the real `as_set() is self.args[1]` does (confirmed in-container, axiom_check.py). |

The pre-patch operation `raise NotImplementedError()` is the deferral the change
removes; `model_prepatch.py` reproduces it (`raise ViewNotProduced()`) and
**fails** verification on the spec's normal-return obligation (the method must
return with `Result() is self.region`; an uncaught raise cannot establish it).
That is exactly the spec sensing the change (G-DIFF): the pre-patch declined to
produce the view, the gold returns the set operand.

## Why object identity is the tight discriminator

## Total correctness (termination)

The real `as_set` body is a single bounded component selection (`return
self.args[1]`): it always terminates. The spec carries this as
`Requires(MustTerminate(2))` — a total-correctness obligation. Without it, a
diverging implementation (e.g. `return self.as_set()`, infinite self-recursion,
or an endless loop before the return) satisfies the value postcondition
`Result() is self.region` only **vacuously** and would verify while its
faithful real patch hangs / hits `RecursionError` in `test_as_set` (this was
the recorded G-EQ/G-PANEL-1 counterexample `atk3_self_recursion.py`). Under
`MustTerminate(2)` a same-measure self-call and a measure-less loop both leak
the obligation, so Nagini rejects every diverging body; the obligation is not
too strong because the gold body is straight-line and trivially discharges it.

The F2P `test_as_set` asserts `Contains(x, FiniteSet(y)).as_set() == FiniteSet(y)`,
`Contains(x, S.Integers).as_set() == S.Integers`, and
`Contains(x, S.Reals).as_set() == S.Reals` — in every case the returned object is
**the set operand that was passed in** (the `args[1]` object), which compares
equal to itself. The postcondition `Result() is self.region` pins exactly this:
returning the element operand (`self.element` ↔ `args[0]`) does not satisfy it
(the two operand objects are distinct and not provably identical), and deferring
(raising) does not satisfy it (no normal return). These are precisely the two
ways a wrong implementation of this behaviour fails the F2P test, so
verify ⟹ resolved.

## No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The changed operation — selecting and returning the
second stored operand — is a direct concrete component selection, modelled
**deeply** (object-identity reasoning over the abstracted components). It is NOT
behind any consumed `@ContractOnly` axiom: there is no library/utility callee the
new code introduces. `axiom_check.py` carries the single **A-reference**-style
soundness witness for the type refinement (R step 1): it constructs real
`Contains(x, s)` objects in-container and asserts `Contains(x, s).args[1] == s`,
`Contains(x, s).args[0] is x`, and (post-gold) `Contains(x, s).as_set() is
Contains(x, s).args[1] == s`, confirming the model's field bijection
(`self.region` ↔ the stored `self.args[1]`) and the modeled return-by-identity
are faithful to the real object on which the gold patch operates.

## verify(model) ⇒ resolved

`solution_region` verifies only if it returns normally with `Result() is
self.region` (the set operand). By R (the `Contains` object ↔ the minimal class,
`self.region` ↔ `self.args[1]`, validated in-container by axiom_check.py) the
verified selection equals `return self.args[1]` on every `Contains(x, s)`.
Therefore an implementation satisfying this spec, refined by the map above, is
the gold patch up to the audited type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this document, G-EQ),
backed by the in-container field-bijection check (G-AX); there is no axiom
soundness obligation (no consumed axiom).
