# refinement.md — sympy__sympy-14711

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`vectorAdd` `do` block, routed through the deep model `addSpec`/`asVector` and
the opaque `combine`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model / opaque validated == real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative by G-EQ; the A-reference callees by **G-AX**
(`axiom_check.py`). This bundle has **no consumed axiom and no `:|` stub** — the
two unchanged callees are A-reference.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

Gold hunk (`sympy/physics/vector/vector.py`):
```python
     def __add__(self, other):
         """The add operator for Vector. """
+        if other == 0:
+            return self
         other = _check_vector(other)
         return Vector(self.args + other.args)
```
A two-line guard inserted at the TOP of `__add__`: when the right operand is the
additive identity `0`, return `self` unchanged, BEFORE the unchanged
`_check_vector(other)` coercion that would otherwise raise
`TypeError('A Vector must be supplied')` on `0`. The two unchanged callees
(`_check_vector`, the `Vector(...)` combination) are untouched.

## vectorAdd — the add operator (`vector.py:58-60`)

| # | Solution.lean impl op (`vectorAdd`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `self : VecVal` | the `self` `Vector` | R | opaque handle ↔ a real `Vector`; not `mut`, unchanged (directive 5). mapping.md §2. |
| 2 | parameter `other : Operand` | the right operand `other` | R | 3-way classification `zero`/`vec`/`foreign` ↔ `other == 0` / `isinstance Vector` / else (mapping.md §2). |
| 3 | `if isZeroOperand other then return Except.ok self` | `if other == 0: return self` | I | the inserted guard, transliterated. `isZeroOperand other = true ↔ other == 0`; `Except.ok self ↔ return self`. mapping.md §2. This is the ADDED behaviour. |
| 4 | `else match asVector other with … Except.error e => Except.error e` | `other = _check_vector(other)` (which raises on a non-vector) | A-reference | the UNCHANGED coercion (`_check_vector`), modeled deeply; the error leg ↔ the raised `TypeError`. Validated == real callee by G-AX (mapping.md §3.1). |
| 5 | `… Except.ok v => Except.ok (combine self v)` | `return Vector(self.args + other.args)` | A-reference | the UNCHANGED combined-vector construction, modeled `opaque`; reached only when `other` is a genuine vector. Validated (returns a vector, never raises) by G-AX (mapping.md §3.2). |

## Discriminating content + prepatch

The single behavioural change `vectorAdd` observes is step 3 — the
identity-absorbing guard. With `other = .zero`:
- patched: `isZeroOperand .zero = true` ⇒ `Except.ok self` (F2P
  `test_Vector`: `A.x + 0 == A.x`; and `sum([N.x, 0*N.x])` no longer raises);
- pre-patch: no guard, so `asVector .zero = Except.error .notAVector` ⇒
  `Except.error .notAVector` (the reported `TypeError`).

`Solution_prepatch.lean` removes the guard (unconditional `match asVector other`).
`prove_correct` **fails** exactly on the discriminating clause —
`isZeroOperand other = true → (match asVector other …) = Except.ok self` — which
the buggy skeleton cannot satisfy (the unguarded coercion yields
`Except.error .notAVector`, not `Except.ok self`). One failing prepatch for the
one independently-fixed behaviour (G-DIFF). The frozen spec is byte-identical
across the two files.

The spec pins, on the absorbing branch, that the result is `self` **itself**
(`Except.ok self`), not merely "succeeds": F2P requires `A.x + 0 == A.x`, i.e.
the original vector returned verbatim. An impl that absorbed `0` but returned
some OTHER vector would satisfy a "no longer raises" spec yet fail F2P; the
`= self` clause rules it out (G-PANEL attacker-1 / SPEC_GUIDE §0.4, §0.8 —
grounded in the input `self`, not an oracle). On the non-identity branches the
spec pins genuine-vector ⇒ `combine self v` and foreign ⇒ the error, so an impl
cannot drop the coercion either.

## No kind-3 (inexpressible-changed-op) steps

Every step is R, I, or A-reference. The one thing that genuinely changed — the
guard — is step 3, an `I` op. The two callees it sits in front of are
**unchanged** and modeled as A-references (deep `asVector`, opaque `combine`),
validated by G-AX, never axiomatized as the function under spec.

## verify(Solution) ⇒ resolved

`vectorAdd` verifies only if, with `other = .zero`, it returns `Except.ok self`
(and otherwise coerces-then-combines exactly as `_check_vector`/`Vector(...)`
do). By R (`VecVal ↔ Vector`, `Operand ↔` operand type, error ↔ `TypeError`) and
the G-AX-validated A-references, the verified method equals the patched
`__add__` on every input; by G-CONF the R/I shadow agrees with `patch.diff`'s
behaviour on 100 000+ inputs and disagrees with the unpatched repo (the
discriminator — `__add__(vector, 0)` — is real). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The trust points are the two
A-reference callees, mechanized by G-AX, and refinement fidelity, mechanized by
G-CONF and audited by G-EQ.
