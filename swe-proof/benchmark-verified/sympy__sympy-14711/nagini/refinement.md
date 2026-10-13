# refinement.md — sympy__sympy-14711

The operation-by-operation correspondence between `model.py`'s implementation
(the `vec_add` impl region and the `vector_guard` axiom) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `Ensures`/`Exsures`,
**A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The add site — `Vector.__add__` (`sympy/physics/vector/vector.py:58`)

Gold hunk:
```
  def __add__(self, other):
      """The add operator for Vector. """
+     if other == 0:
+         return self
      other = _check_vector(other)
      return Vector(self.args + other.args)
```

Pre-patch body (no short-circuit):
```
  def __add__(self, other):
      other = _check_vector(other)
      return Vector(self.args + other.args)
```

| # | model.py impl op (`vec_add`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `self: Vec`, `other: Operand` | `self`, `other` of `__add__` | R | `Vector` ↔ `Vec` (`.args` ↔ `.terms`, `List[int]` of opaque component-family tags; the addition observes only the list length); the operand object ↔ `Operand` with kind discriminators (mapping.md §2). |
| A2 | `if other.is_scalar_zero: return self` | `if other == 0: return self` | R + I | **the added hunk.** `other == 0` ↔ `other.is_scalar_zero` (the additive-identity test, R); `return self` is the identical control-flow operation (I). This is modeled DEEPLY (spelled out), not axiomatized — it is the operation the patch CHANGES, so it must not hide behind an axiom. The discriminating clause `Implies(other.is_scalar_zero, ToSeq(Result().terms) == ToSeq(self.terms))` pins it. |
| A3 | `checked = vector_guard(other)` | `other = _check_vector(other)` | A-consumed | `_check_vector` is unchanged by the patch; the axiom is its weakest sufficient contract: returns the operand unchanged when it is a vector, signals `NotAVector` otherwise (mapping.md §3.1). The proof consumes its `Ensures` (`ToSeq(Result().terms) == ToSeq(other.terms)`, `other.is_vector`) and its `Exsures` (the not-a-vector raise → clause (3)). G-AX confirms it against the real `_check_vector`. |
| A4a | the loop building `combined == self.terms + checked.terms` (the constructor's *argument*) | the list concatenation `self.args + other.args` passed to `Vector(...)` | R | list concatenation `self.args + other.args` ↔ the append loop establishing `ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms)` (a front/index fold giving one unfold per step). This is the **raw, pre-normalisation** argument list; order/multiplicity preserved here. The merge happens *inside* the constructor (A4b), not in this concatenation. |
| A4b | `result = Vec(combined)` (the normalising constructor, modeled by the `normal_form` function via the `normalise` callee) | `Vector(self.args + other.args)` — the `Vector.__init__` constructor | **A-reference** | `Vector.__init__` is a **merging/normalising constructor**: it builds a dict keyed by reference frame, sums the measure-number matrices of same-frame terms, and drops zero-contribution frames (`sympy/physics/vector/vector.py:26-53`). It is NOT element-/length-preserving — empirically `(x*A.x + y*A.y + z*A.z).args` has length **1**, and `x*A.x + (-x)*A.x` collapses to length **0**. It IS a **deterministic function of its whole argument list** (same arg list → same `.args`), modeled as the `@Pure normal_form` callee. Its **content-bearing faithful** contract is twofold: (i) `len(result) <= len(input)` ("never invents a component"), and (ii) it is a function — equal inputs give equal normal forms, and inputs that differ are NOT provably equal. The post pins `ToSeq(Result().terms) == normal_form(ToSeq(self.terms) + ToSeq(other.terms))`: the result is the normal form of the **concatenation of BOTH operands' carriers** — grounded entirely in the two modeled inputs, not an opaque answer-key. An impl that drops `other` (`return self`, `Vec(self.terms)`, `Vec([])`) produces `normal_form(ToSeq(self.terms))` (or `normal_form(empty)`), which is NOT provably equal to `normal_form(self ++ other)` for an arbitrary `other` — so the post rejects it. This is unchanged by the patch (patch-invariant) and is validated == the real constructor by `axiom_check.py` / G-AX (both the length bound and the determinism/distinguisher, mapping.md §3.2). It is tagged **A-reference**, NOT R: collapsing several list elements into one (or zero) is a changed *operation* on the carrier, not a carrier-type refinement, so it must be modeled shallowly and audited against the real callee, not declared an identity. |

Clause (3)'s reject is made MANDATORY (not merely permitted) by clause (3a)
`Ensures(other.is_scalar_zero or other.is_vector)`: a NORMAL return is only
possible when the operand is the scalar zero or a genuine vector, so an impl
that silently accepts a neither-operand (e.g. `return self` on `A.x + 5`
instead of `_check_vector`'s `TypeError`) violates the postcondition. Without
(3a) both `Implies` postconditions are vacuous on the neither-operand state and
an `Exsures` alone never *obliges* a raise — the exact spec-too-weak hole the
G-PANEL-1 audit exhibited (its atk_2: gold zero/vector branches plus a
swallowing `return self` for everything else verified). The real `__add__`
reaches `_check_vector(other)` unconditionally for any non-zero operand, and
`_check_vector` raises on a non-`Vector` (G-AX validates this), so (3a) is a
faithful strengthening, not an over-claim.

The discriminating content of the change — adding `0` to a vector RETURNS the
vector (normally) instead of raising — lives in clause (1)
`Implies(other.is_scalar_zero, ToSeq(Result().terms) == ToSeq(self.terms))`,
together with the absence of any `Exsures` admitting a raise on the
scalar-zero state (the `Exsures` is guarded by `not other.is_scalar_zero and
not other.is_vector`). `model_prepatch.py` reproduces the pre-patch body (no
short-circuit → `_check_vector`/`vector_guard` reached unconditionally) and
**fails verification** at the point where it can no longer establish
`not other.is_scalar_zero` after the guard — i.e. the guard was reached with a
possibly-scalar-zero operand, which (by the `vector_guard` `Exsures`) raises
`NotAVector` on `other.is_scalar_zero`, contradicting clause (1)'s requirement
of a normal `self`-returning result. That is exactly the spec sensing the
change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or A-reference. The one operation that
genuinely *changed* — the `other == 0` additive-identity short-circuit — is
modeled **deeply** (step A2: spelled out as the `if other.is_scalar_zero: return
self` branch and pinned by clause (1)), not hidden behind an axiom. Two callees
are modeled shallowly and audited by G-AX rather than refined as identities:
- `vector_guard` (**A-consumed**, step A3) covers the **unchanged** callee
  `_check_vector` the code already invoked before and still invokes after the
  patch; the proof consumes its `Ensures`/`Exsures`.
- `normal_form` / `normalise` (**A-reference**, step A4b) covers the
  **unchanged** merging constructor `Vector.__init__`. It is NOT a carrier-type
  refinement: the constructor folds same-frame components and drops cancelling
  frames, changing the element count, so it cannot be tagged R. Its
  content-bearing faithful contract — (i) `len(result) <= len(input)` and (ii)
  it is a deterministic function of its whole argument list — is validated ==
  the real `Vector.__init__` by `axiom_check.py` / G-AX (the never-grows bound,
  the determinism, and the F2P distinguisher that `normal_form(self ++ other) !=
  normal_form(self)`). No step is a forbidden kind-3 (unexpressible changed
  operation): the changed op (the short-circuit) is deep, and every callee is a
  patch-invariant library call modeled at the faithful, audited contract. Note
  `normal_form` is NOT an ungrounded answer-key oracle: the post applies it to
  `ToSeq(self.terms) + ToSeq(other.terms)`, the genuine concatenation of the two
  modeled input carriers, so an impl cannot echo the result without actually
  combining both operands' components.

## C. verify(model) ⇒ resolved

`vec_add` verifies only if (1) the scalar-zero operand returns the left vector's
component list unchanged WITHOUT raising (clause 1 + the guarded `Exsures`), and
(2) a vector operand yields the **normal form of BOTH operands' components
concatenated** (clause 2: `ToSeq(Result().terms) == normal_form(ToSeq(self.terms)
+ ToSeq(other.terms))` — the **content-bearing faithful** property of the merging
constructor; NOT verbatim concatenation, and NOT a mere length bound). By R
(`Vector` ↔ `Vec`, `.args` ↔ `.terms`, `other == 0` ↔ `is_scalar_zero`, list `+`
↔ append loop building the constructor *argument*) and the two audited callees the
verified body equals `if other == 0: return self; other = _check_vector(other);
return Vector(self.args + other.args)` on the tested inputs; by G-AX the real
`_check_vector` meets the `vector_guard` axiom (A-consumed) and the real
`Vector.__init__` meets the `normal_form` contract (A-reference: the never-grows
length bound AND its determinism as a function of the whole argument list).
Clause (2) deliberately does NOT assert verbatim concatenation: the F2P
`test_Vector` exercises the same-frame merge (`v1 = x*A.x + y*A.y + z*A.z` and
`v2 = x**2*A.x + …`, both entirely in frame A; `v3 = v1 + v2`; `dot(v3, A.x) ==
x**2 + x` holds only because same-frame terms merge — `v1.args` itself has length
1). A literal-concatenation post would be unfaithful; but a length-only bound is
too weak (it admits `return self` / `Vec([])` / `Vec(self.terms)`, all of which
DROP the other operand yet satisfy `len <= len + len` — a verify⟹correct break
the prior refinement shipped). Pinning the result to `normal_form(self ++ other)`
closes that hole: dropping `other` yields `normal_form(self)` (or `normal_form(
empty)`), provably distinct from `normal_form(self ++ other)` for an arbitrary
`other` (G-AX exhibits the F2P distinguisher), so those impls fail clause (2).
The discriminating content of the *fix itself* lives in clause (1) (G-DIFF: the
prepatch fails at `Assert(not other.is_scalar_zero)` after the unconditional
guard), while clause (2) is what makes the spec strong enough that no
other-dropping impl verifies. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the two audited
callees — and the gold patch resolves (G-RESOLVE; `A.x + 0 == A.x` returns `A.x`
normally, and `v3 = v1 + v2` genuinely combines both operands). The trust points
are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
