# refinement.md — sympy__sympy-20590

Operation-by-operation correspondence between `Solution.lean`'s implementation
and `patch.diff` (the gold patch, verbatim). Each step is tagged **R** (type
refinement), **A-consumed** (proof consumes an axiom's postcondition),
**A-reference** (a deep model validated == a real runtime behaviour by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim: any
implementation that verifies against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single gold hunk — the printing-behavior contributor gains a closed layout

Gold hunk (`sympy/core/_print_helpers.py`, class `Printable` body):
```
+    __slots__ = ()
```
This pins a fixed (empty) instance layout on the shared printing-behavior
contributor, so that mixing it into the value type no longer re-opens the value
type's instance layout.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `mixinPinsClosedLayout` returns `true` | `Printable.__slots__ = ()` | I/R | declaring a closed slot set on a class is exactly "this class pins a fixed instance layout / contributes no open per-instance namespace". The boolean `true` is the type-refined (R) image of the class-level slot declaration (mapping.md §2); the value (it IS declared) is identical (I) to the gold edit. The empty slot set adds no named slots, which is why this is a *fixed-layout* flag and not a slot-name list. |
| A2 | `chain := others ++ [trait]` — the value type's contributing-type chain, with `others` a universally quantified method input (the non-printing contributors' flags) and `trait` the printing contributor's flag appended | the value type's resolution order (the type itself, its slotted abstract bases, the printing contributor), the universal root excluded | R | a resolution order (a sequence of types) ↔ `List Bool` of closed-layout flags (mapping.md §2). The value type and its abstract bases already declared closed slot sets at `base_commit`, so the actual repo shape is the instantiation `allClosedLayout others = true` (pinned by each `core*` method's second `ensures`); the only flag the patch changes is the printing contributor's, carried by `trait`. Quantifying `others` makes the spec pin the runtime rule on EVERY chain, so a constant-returning impl cannot satisfy it (mapping.md §2, chain-shape note). |
| A3 | `instanceAdmitsNamespace chain = !allClosedLayout chain`; `bindUndeclared chain` refuses (error) iff `allClosedLayout chain` | the runtime rule that an instance carries an open per-instance namespace (and accepts binding an undeclared attribute name) iff some contributing type (≠ the universal root) omits a closed slot declaration, and refuses such a binding with an attribute error otherwise | A-reference | the *runtime rule* relating closed slot declarations to an open namespace / refusal is modelled **deeply** (the front-recursive conjunction `allClosedLayout` and the binding decision derived from it), NOT axiomatized as a callee. There is no consumed axiom. The deep model is validated **== the real interpreter** out of band by `axiom_check.py` (G-AX): it builds type chains with every closed/open layer combination and asserts `hasattr(inst,'__dict__')` and the binding-refusal behaviour agree with `instanceAdmitsNamespace` / `allClosedLayout` on the matching boolean chain. (mapping.md §3.) |

## B. The tested observations

| # | Solution.lean construct | tested behaviour | tag | justification |
|---|---|---|---|---|
| B1 | `coreInstanceAdmitsNamespace others` ensures `out = instanceAdmitsNamespace (others ++ [true])` and (`allClosedLayout others = true → out = false`) | `assert not hasattr(b1, '__dict__')` on `b1 = Basic()` | A-reference + I | `instanceAdmitsNamespace chain == hasattr(inst,'__dict__')` (A3, G-AX-validated). The primary clause pins the rule on EVERY chain; the second clause is the F2P instantiation: with the gold patch the appended trait flag is `true` and `Basic`'s own flags are all `true`, so the result is `false`, matching `not hasattr` ⇒ no open namespace. |
| B2 | `coreBindUndeclared others` ensures `out = bindUndeclared (others ++ [true])` and (`allClosedLayout others = true → out = Except.error AttrError.bindingRefused`) | `with raises(AttributeError): b1.x = 1` | A-reference + I | binding an undeclared attribute name on a no-namespace instance is refused with an attribute error (A3). `AttrError.bindingRefused` ↔ the attribute error (mapping.md §2). The primary clause pins the rule on EVERY chain; the F2P instantiation: the gold chain is all-`true` ⇒ the binding refuses. |

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, A-reference, or I. The one operation that *changed* — a
type declaring a closed slot set, and the runtime consequence for the open
namespace / attribute binding — is modelled **deeply** (the `allClosedLayout`
fold and the binding decision), not hidden behind an axiom about the function
under change. There is **no consumed axiom** (the `axioms` region is empty) and
**no `:|`-stub callee**: the bundle has zero A-consumed rows. The single
A-reference (A3/B1/B2) is the runtime object-model rule, validated against the
real interpreter by `axiom_check.py` (G-AX), not consumed as a contract.

## D. verify(Solution) ⇒ resolved

**Where discrimination lives.** The load-bearing discriminating clause is
`mixinPinsClosedLayout`'s postcondition `ensures out = true` (A1): it verifies
ONLY for an impl that returns the closed-layout flag, which is exactly the gold
edit (the empty closed slot set on the printing contributor). The two `core*`
methods pin the runtime rule and the F2P observations (B1/B2): each takes the
other contributors' flags `others` as a universally quantified input, builds
the chain `others ++ [trait]` with the trait flag fixed `true`, and must equal
the model function on `others ++ [true]` for EVERY `others` — so a hardcoded
constant impl fails the primary clause on some `others` (e.g. `[false]`), and
an impl appending `trait = false` fails both clauses. What makes the prepatch
fail is that the prepatch flips the trait flag to `false`:
`mixinPinsClosedLayout` then returns `false` (fails A1), and the two `core*`
methods build an open chain, so `coreInstanceAdmitsNamespace` disagrees with
`instanceAdmitsNamespace (others ++ [true])` on all-closed `others` (and its
F2P clause yields `true ≠ false`) and `coreBindUndeclared` yields `ok true ≠
error` — all discriminating clauses fail (G-DIFF). This is exactly the
pre-edit defect the issue reports: the printing contributor left its layout
open, re-opening the value type's instance namespace.

By R (resolution order ↔ flag chain; closed slot declaration ↔ closed-layout
flag) the verified facts are exactly the gold patch's effect, and by the
A-reference (G-AX) the deep closed-layout → open-namespace / refusal rule equals
the real interpreter's. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the interpreter-validated
runtime rule — and the gold patch resolves (`test_immutable` passes; G-RESOLVE).
The trust point is the single A-reference (G-AX, the object-model rule) plus
refinement fidelity (this document, G-EQ).
