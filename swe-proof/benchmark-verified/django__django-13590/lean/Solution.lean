import Mathlib
-- imports-end

/-!
Resolving a value that may be a scalar, a resolvable expression, or a finite
sequence.

A value has one of three shapes:

  * a plain scalar, which carries no sub-structure;
  * a resolvable expression, which is replaced by its resolved form (the
    resolution of a single expression is supplied as a given operation
    `resolveExpr`, the SAME operation for every expression);
  * a finite sequence, which additionally carries a container kind drawn from a
    small enumeration of kinds.

Resolution is defined uniformly:

  * a scalar is returned unchanged;
  * an expression is replaced by `resolveExpr` of it;
  * a sequence is rebuilt from the independently-resolved images of its
    elements, in order — the rebuilt sequence has the SAME length and the SAME
    container kind as the original, and each element is the resolution of the
    corresponding original element.

Resolution is TOTAL: it produces a result for every input, including a sequence
of every container kind. The behavior pinned below records, for every input,
exactly which value the resolution yields.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a proof axiom. The resolution of a
-- single expression is modeled as an arbitrary parameter `resolveExpr : Nat →
-- Value`: the modeled behavior is solely HOW a composite value is rebuilt from
-- the resolutions of its parts, so the result is pinned for every possible
-- single-expression resolver. Hence the spec needs no `opaque`/`axiom` callee
-- contract; `resolveExpr` is universally quantified in `correct_resolveValue`.
-- axioms-end

/-- The container kind of a finite sequence. The kinds are distinguished because
the rebuilt sequence must preserve the original kind exactly; one of the kinds
(`special`) additionally requires its elements to be supplied individually to its
constructor rather than as a single bundle. -/
inductive Container where
  | plain
  | tupleLike
  | special
deriving DecidableEq

/-- A value to be resolved: a scalar, a single resolvable expression (identified
abstractly by a `Nat`), or a finite sequence carrying a container kind. -/
inductive Value where
  | scalar (n : Int)
  | expr (id : Nat)
  | seq (c : Container) (elems : List Value)

-- pure-start
/-- Reference resolution of a value. Scalars are unchanged; an expression is
replaced by `resolveExpr` of its identifier; a sequence is rebuilt from the
element-wise resolutions, preserving length and the container kind. This is a
structural recursion over the input value. -/
def resolveRef (resolveExpr : Nat → Value) : Value → Value
  | .scalar n => .scalar n
  | .expr id => resolveExpr id
  | .seq c elems => .seq c (elems.map (resolveRef resolveExpr))
-- pure-end

-- post-conditions-start
/-- The resolution result is fully pinned to the input value and the
single-expression resolver:

  * resolution always succeeds (`result = some _`);
  * the resolved value equals the structural, element-wise resolution of the
    input — a scalar maps to itself, an expression to its resolved form, and a
    sequence to a sequence of the SAME container kind and the SAME length whose
    elements are the resolutions of the originals.

No output component is left free: both the container kind and every element of
the result are determined for every input. -/
def problem_spec_resolveValue
    (resolveExpr : Nat → Value) (v : Value) (result : Option Value) : Prop :=
  result = some (resolveRef resolveExpr v)
-- post-conditions-end

-- impl-start
def implementation_resolveValue
    (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
  match v with
  | .expr id =>
      -- an expression is replaced by its resolved form
      return some (resolveExpr id)
  | .seq c elems =>
      -- the elements may themselves be values, so resolve each independently;
      -- then rebuild a sequence of the same container kind from the results
      let values := elems.map (resolveRef resolveExpr)
      match c with
      | .special =>
          -- this kind requires its elements supplied individually; rebuild it
          return some (.seq .special values)
      | .plain =>
          return some (.seq .plain values)
      | .tupleLike =>
          return some (.seq .tupleLike values)
  | .scalar n =>
      -- a plain scalar is returned unchanged
      return some (.scalar n)
-- impl-end

-- proof-start
theorem correct_resolveValue :
    ∀ (resolveExpr : Nat → Value) (v : Value),
      problem_spec_resolveValue resolveExpr v
        (implementation_resolveValue resolveExpr v) := by
  intro resolveExpr v
  cases v with
  | scalar n =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | expr id =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | seq c elems =>
      cases c <;>
        · simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
          rfl
-- proof-end
