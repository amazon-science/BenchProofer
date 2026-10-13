import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: this bundle models the operation deeply over its actual numeric
-- inputs. Every offset is an exact arithmetic relation on that element's own
-- (height, descent) pair — there is no outside callee whose contract must be
-- assumed. (refinement.md: all rows are R or I; mapping.md §3 records "no
-- axioms / no A-reference callees".)
-- axioms-end

-- pure-start
/- The anchor of a box layout: which edge the boxes are aligned to within the
   common extent. Values mirror the public anchor names the layout accepts. -/
inductive Anchor where
  | baseline | left | top | right | bottom | center
  deriving DecidableEq

/- The result of aligning a list of boxes: the total extent, the descent of the
   packing, and the per-box offset along the aligned axis. -/
structure Aligned where
  extent  : Rat
  descent : Rat
  offsets : List Rat
  deriving DecidableEq

/- Maximum of a NON-EMPTY list of rationals: the head seeds the reduction and
   the tail is folded into it, so the fold contributes no bound of its own and a
   list whose entries are all negative has a negative maximum. The `[]` value is
   arbitrary and never consulted — the non-empty case does not recurse through
   it, and every use sits under `require hd ≠ []`. -/
def listMax : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/- The extent to align within: the caller may supply it explicitly, otherwise it
   is the largest box height. -/
def resolvedExtent (hd : List (Rat × Rat)) (extent : Option Rat) : Rat :=
  match extent with
  | some v => v
  | none   => listMax (hd.map (fun p => p.1))

/- Reference semantics, one branch per anchor.

   * `baseline` re-derives the extent from the boxes and leaves every box at
     offset 0.
   * the edge anchors place each box by an exact relation on its own
     `(height, descent) = (p.1, p.2)`:
       - aligning to the LEFT or BOTTOM edge offsets each box by its descent;
       - aligning to the RIGHT or TOP edge offsets each box by how far it falls
         short of the extent, plus its descent;
       - `center` places each box at half its shortfall plus its descent.

   This is the desired per-anchor placement; the implementation must reproduce
   it exactly. -/
def alignSpec (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor) : Aligned :=
  match anchor with
  | .baseline =>
      let hdesc := listMax (hd.map (fun p => p.1 - p.2))
      let desc  := listMax (hd.map (fun p => p.2))
      { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
  | .left | .bottom =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
  | .right | .top =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
  | .center =>
      let h := resolvedExtent hd extent
      { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method alignOffsets (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor)
    return (out : Aligned)
  require hd ≠ []
  ensures out = alignSpec hd extent anchor
  do
    -- impl-start
    let result : Aligned :=
      match anchor with
      | .baseline =>
          let hdesc := listMax (hd.map (fun p => p.1 - p.2))
          let desc  := listMax (hd.map (fun p => p.2))
          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }
      | .left | .bottom =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }
      | .right | .top =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }
      | .center =>
          let h := resolvedExtent hd extent
          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }
    return result
    -- impl-end

prove_correct alignOffsets by
  loom_solve
  cases anchor <;> rfl
