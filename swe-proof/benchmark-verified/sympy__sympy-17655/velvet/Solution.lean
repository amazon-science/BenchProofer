import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Scaling a sequence of numeric coordinates by a single factor: each coordinate
   is multiplied by the factor, in place, preserving order and count. This is the
   deep model of the library's existing point-by-scalar scaling operation — the
   per-coordinate product. It is spelled out concretely (a transparent map), so
   the postcondition below is grounded in the actual coordinates and factor, not
   an opaque oracle. Provenance + executable soundness check (this deep model
   equals the real scaling callee): mapping.md / axiom_check.py (G-AX). -/
def scaleCoords (coords : List Rat) (factor : Rat) : List Rat :=
  coords.map (· * factor)

@[grind] lemma scaleCoords_length (coords : List Rat) (factor : Rat) :
    (scaleCoords coords factor).length = coords.length := by
  simp [scaleCoords]

/- The non-deterministic choice of the scaling callee's result is well-posed: for
   any target value `v`, the set of values equal to `v` is non-empty (`v` itself).
   This supplies the constructive existence witness so the `:|` choice elaborates.
   It does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows, here exactly the scaled
   coordinates. -/
noncomputable instance findableEqList (v : List Rat) (n : Lean.Name) :
    Findable (fun e : List Rat => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Multiplying a number by a point.

   The desired behavior: when a numeric factor is multiplied on the LEFT of a
   point, the result is the same scaled point you get by multiplying the point by
   that factor on the right — each coordinate of the point is multiplied by the
   factor. So `factor` applied to a point with coordinates `coords` yields the
   point whose coordinates are `coords` each scaled by `factor` (in the same
   order, same count). Multiplying a number by a point therefore produces a point,
   not an unevaluated product.

   `factor` (the scalar) and `coords` (the point's coordinates) are read-only
   inputs (not `mut`): the routine consumes them and never alters them
   (directive 5). Coordinates and factor are modeled as exact rationals (`Rat`):
   the demonstrated behavior is exact numeric scaling, and an exact ordered field
   is faithful for it (mapping.md §2). The result is a fresh coordinate sequence. -/
noncomputable section
method scalePoint (factor : Rat) (coords : List Rat) return (out : List Rat)
  ensures out = scaleCoords coords factor
  ensures out.length = coords.length
  do
    -- impl-start
    -- Delegate to the library's existing point-by-scalar scaling operation (the
    -- per-coordinate product), and return its result — so left-multiplication by
    -- a number matches right-multiplication by the same number.
    let out :| out = scaleCoords coords factor
    return out
    -- impl-end
end

prove_correct scalePoint by
  loom_solve
