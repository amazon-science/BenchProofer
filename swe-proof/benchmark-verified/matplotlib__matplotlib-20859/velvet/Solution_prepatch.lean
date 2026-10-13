import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   runtime type-membership test that selects the dispatch branch — is modeled
   DEEPLY in the `pure` region (the `isRegion` / `isCanvas` / `isTopCanvas`
   predicates, with the structural invariant that the narrow canvas kind is a
   special case of the broad one) and validated == the real test by G-AX (an
   A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A parent container that a child object may be anchored to. There are exactly
   three observable shapes:
   * `region`  — a plotting region; it carries an owning canvas, recorded as the
     identity of that canvas;
   * `canvas`  — a figure-like drawing canvas. There are two kinds, distinguished
     by `topLevel`: a top-level canvas (`topLevel = true`) and a nested
     sub-canvas (`topLevel = false`). Its `id` is its own identity.
   * `other`   — anything else, which is not a valid parent.
   A nested sub-canvas is just as much a figure-like canvas as a top-level one
   (`isTopCanvas → isCanvas`, lemma below): both are accepted. -/
inductive Container where
  | region (canvas : Nat)
  | canvas (id : Nat) (topLevel : Bool)
  | other
  deriving DecidableEq

/- The parent is a plotting region. -/
@[grind] def isRegion : Container → Bool
  | .region _ => true
  | _         => false

/- The parent is a figure-like canvas of EITHER kind (top-level or nested). This
   is the broad membership test the desired behavior keys on. -/
@[grind] def isCanvas : Container → Bool
  | .canvas _ _ => true
  | _           => false

/- The parent is specifically a top-level canvas — the narrow membership test
   that a nested sub-canvas does NOT satisfy. -/
@[grind] def isTopCanvas : Container → Bool
  | .canvas _ t => t
  | _           => false

/- The owning canvas of a plotting region (0 elsewhere — never consulted off the
   region shape). -/
@[grind] def regionCanvas : Container → Nat
  | .region c => c
  | _         => 0

/- The identity of a figure-like canvas (0 elsewhere — never consulted off the
   canvas shape). -/
@[grind] def canvasId : Container → Nat
  | .canvas i _ => i
  | _           => 0

/- The narrow canvas kind is a special case of the broad one: anything that
   passes the narrow membership test also passes the broad test. This is the
   structural fact about the container kinds that G-AX validates against the
   real runtime type hierarchy (mapping.md §3.1). -/
@[grind] lemma isTopCanvas_imp_isCanvas (p : Container) :
    isTopCanvas p = true → isCanvas p = true := by
  cases p <;> simp [isTopCanvas, isCanvas]

/- Failure of anchoring: the parent is neither a plotting region nor a
   figure-like canvas. -/
inductive AnchorErr where
  | unsupportedParent
  deriving DecidableEq

/- The result of anchoring a child to its parent: a flag recording whether the
   parent was a plotting region, and the identity of the canvas the child is
   bound to. -/
structure Anchor where
  fromRegion : Bool
  canvas : Nat
  deriving DecidableEq

/- The intended anchoring: a plotting region binds the child to that region's
   owning canvas (and records that it came from a region); a figure-like canvas
   of EITHER kind binds the child directly to that canvas; any other parent is
   rejected. -/
def anchorSpec : Container → Except AnchorErr Anchor
  | .region c   => Except.ok { fromRegion := true,  canvas := c }
  | .canvas i _ => Except.ok { fromRegion := false, canvas := i }
  | .other      => Except.error .unsupportedParent

@[grind] lemma anchorSpec_region (c : Nat) :
    anchorSpec (.region c) = Except.ok { fromRegion := true, canvas := c } := rfl
@[grind] lemma anchorSpec_canvas (i : Nat) (t : Bool) :
    anchorSpec (.canvas i t) = Except.ok { fromRegion := false, canvas := i } := rfl
@[grind] lemma anchorSpec_other :
    anchorSpec .other = Except.error .unsupportedParent := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method anchorToParent (parent : Container) return (out : Except AnchorErr Anchor)
  ensures out = anchorSpec parent
  do
    -- impl-start
    -- Pre-image skeleton: the second test is the NARROW top-level-canvas
    -- membership test, so a nested sub-canvas fails it and is rejected as an
    -- unsupported parent. The frozen spec accepts any figure-like canvas
    -- (isCanvas), so prove_correct MUST fail on the nested sub-canvas case.
    let parentIsRegion : Bool := isRegion parent
    let parentIsCanvas : Bool := isTopCanvas parent
    let out : Except AnchorErr Anchor :=
      if parentIsRegion then
        Except.ok { fromRegion := true, canvas := regionCanvas parent }
      else
        if parentIsCanvas then
          Except.ok { fromRegion := false, canvas := canvasId parent }
        else
          Except.error .unsupportedParent
    return out
    -- impl-end

prove_correct anchorToParent by
  loom_solve
  cases parent <;>
    simp_all [anchorSpec, isRegion, isTopCanvas, regionCanvas, canvasId]
