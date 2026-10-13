# refinement.md — sympy__sympy-20590

Operation-by-operation correspondence between `model.py`'s implementation and
`patch.diff` (the gold patch, verbatim). Each step is tagged **R** (type
refinement), **A-consumed** (proof consumes an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee / runtime behaviour by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single gold hunk — `Printable` gains a fixed layout

Gold hunk (`sympy/core/_print_helpers.py`, class `Printable` body):
```
+    __slots__ = ()
```
This pins a fixed (empty) instance layout on the printing-behaviour mixin, so
that mixing it into `Basic` no longer re-opens the subclass instance layout.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `trait_pins_closed_layout()` returns `True` | `Printable.__slots__ = ()` | I/R | declaring `__slots__` on a class is exactly "this class pins a fixed instance layout / contributes no per-instance `__dict__`". The boolean `True` is the type-refined (R) image of the class-level `__slots__` declaration (mapping.md §2); the value (it IS declared) is identical (I) to the gold edit. The empty tuple `()` adds no named slots, which is why this is a *fixed* layout flag and not a slot-name list. |
| A2 | `chain = PSeq(True, True, trait)` — the `Basic` instance's type chain | `Basic`'s MRO (`Basic`, its slotted abstract bases, `Printable`), root `object` excluded | R | the MRO (a sequence of classes) ↔ `PSeq[bool]` of fixed-layout flags (mapping.md §2). `Basic` and its abstract bases already declared `__slots__` at `base_commit` (`sympy/core/basic.py:72`, `Atom.__slots__` line 1825), hence the two leading `True`s; the only flag the patch changes is `Printable`'s, carried by `trait`. Chain length is immaterial: the rule (A3) quantifies over every entry. |
| A3 | `instance_admits_namespace(chain) == not all_closed_layout(chain)`; `bind_undeclared_attribute` raises iff `all_closed_layout(chain)` | CPython's object-model rule that an instance has a `__dict__` (and accepts undeclared-attribute assignment) iff some MRO class (≠ `object`) omits `__slots__`, and raises `AttributeError` on undeclared assignment otherwise | A-reference | the *runtime rule* relating `__slots__` to `__dict__`/`AttributeError` is modelled **deeply** (the front-recursive conjunction `all_closed_layout` and the binding decision derived from it), NOT axiomatized as a callee. There is no `@ContractOnly`. The deep model is validated **== the real interpreter** out-of-band by `axiom_check.py` (G-AX): it builds classes with every slotted/un-slotted layer combination and asserts `hasattr(inst,'__dict__')` and the assignment-`AttributeError` behaviour agree with `instance_admits_namespace` / `all_closed_layout` on the matching boolean chain. (mapping.md §3.) |

## B. The tested observations

| # | model.py construct | tested behaviour | tag | justification |
|---|---|---|---|---|
| B1 | `core_expression_instance_admits_namespace()` ensures `Result() is False` | `assert not hasattr(b1, '__dict__')` on `b1 = Basic()` | A-reference + I | `instance_admits_namespace(chain) == hasattr(inst,'__dict__')` (A3, G-AX-validated). With the gold patch every flag is `True`, so the result is `False`, matching `not hasattr` ⇒ no `__dict__`. |
| B2 | `core_expression_bind_undeclared_attribute()` ensures `Ensures(False)` (never returns normally) + `Exsures(AttributeBindingRefused, True)` | `with raises(AttributeError): b1.x = 1` | A-reference + I | binding an undeclared attribute on a no-`__dict__` instance raises `AttributeError` (A3). `AttributeBindingRefused` ↔ `AttributeError` (mapping.md §2). The gold chain is all-`True` ⇒ the binding always raises. |
| B3 | every modelled function carries a `Requires(MustTerminate(n))` obligation (measures 1/2/3 along the call chain: `bind_undeclared_attribute` 1, `trait_pins_closed_layout` 2, the two `core_expression_*` observations 3) | the real operations always COMPLETE: attribute binding either stores or raises immediately; reading a class-level `__slots__` declaration is immediate; the F2P observations only pass if they return / raise (a hang times the test out) | I | Nagini verifies partial correctness by default, so without a termination obligation a diverging body satisfies every `Ensures` — including `Ensures(False)` — vacuously while never delivering the behaviour the F2P observes. `MustTerminate` pins totality, exactly matching the bounded loop-free runtime steps; a callee's strictly smaller measure discharges its caller's obligation without leaking. |

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, A-reference, or I. The one operation that *changed* — a
class declaring fixed slots, and the runtime consequence for `__dict__` /
attribute binding — is modelled **deeply** (the `all_closed_layout` fold and the
binding decision), not hidden behind an axiom about the function under change.
There is **no consumed axiom** (`# axioms` region is empty) and **no
`@ContractOnly` callee**: the bundle has zero A-consumed rows. The single
A-reference (A3/B1/B2) is the CPython object-model rule, validated against the
real interpreter by `axiom_check.py` (G-AX), not consumed as a contract.

## D. verify(model) ⇒ resolved

**Where discrimination lives.** The load-bearing discriminating clause is
`trait_pins_closed_layout`'s constant postcondition `Ensures(Result() is True)`
(A1): it verifies ONLY for an impl that returns the fixed-layout flag, which is
exactly the gold edit (`__slots__ = ()`). The two `core_expression_*` functions
are **F2P-observation pins, not load-bearing for discrimination.** Strictly,
`core_expression_instance_admits_namespace` verifies for *any* all-closed chain
(it constructs `PSeq(True, True, trait)` and any all-`True` chain — including an
empty or shorter chain — yields `Result() is False`); it does not, by itself,
force the chain to model `Basic`'s exact MRO. Likewise
`core_expression_bind_undeclared_attribute` verifies whenever the chain it builds
is all-closed. What makes the prepatch fail is that `trait` is supplied by
`trait_pins_closed_layout()`, so once the trait flag is forced `True` (A1) every
derived observation follows; the prepatch flips that flag to `False` and all
three clauses fail (G-DIFF). The observation functions are faithful F2P pins
(B1/B2) but the soundness anchor is A1.

**Totality (P1 repair).** An earlier audit exhibited a same-spec implementation
that verified by DIVERGING (an `Invariant(True)` infinite loop before the
correct tail): under Nagini's partial-correctness semantics every postcondition
held vacuously, yet the faithful real patch (a binding step / class
declaration that hangs) never delivers the observation `test_immutable` needs,
so it does not resolve. The spec now carries `MustTerminate` obligations on all
four modelled functions (B3), which reject that implementation class (Nagini's
obligation-leak check fails on any measureless loop). The two diverging rivals
are pinned as PBT uniqueness cases (`reject-diverge-bind`,
`reject-diverge-trait` in properties.py).

By R (MRO ↔ flag chain; `__slots__` ↔ fixed-layout flag) the verified facts are
exactly the gold patch's effect, and by the A-reference (G-AX) the deep
`__slots__`→`__dict__`/`AttributeError` rule equals the real interpreter's.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the interpreter-validated runtime rule — and the
gold patch resolves (`test_immutable` passes; G-RESOLVE). The single failing
`model_prepatch` (the contributing type leaving its layout open) is exactly the
pre-#19425 bug the issue reports, failing all three discriminating clauses
(G-DIFF). The trust points are PLAN §1.1's two: there are no consumed axioms, so
only the A-reference (G-AX, the object-model rule) and refinement fidelity (this
document, G-EQ) apply.
