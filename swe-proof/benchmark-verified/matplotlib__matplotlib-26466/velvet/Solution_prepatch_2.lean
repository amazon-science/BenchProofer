import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No unchanged opaque callee is consumed: the modeled behaviour is the
--  constructors' own coordinate storage, modeled deeply below. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- A coordinate pair retained by an object, viewed through the lens of *what
   happens when the source container is mutated afterwards*. There are exactly
   two retention behaviours an object can exhibit:

   * `snapshot x y` — the pair is detached from the source: observing it always
     yields the captured `(x, y)`, no matter what the source container holds
     now.
   * `reference` — the pair stays bound to the source container: observing it
     yields the source's CURRENT contents.

   The issue describes a coordinate pair that tracks later edits to the input
   container ("the same array is kept instead of a copy"); the desired
   behaviour is the `snapshot` one. The two behaviours are observationally
   distinguishable exactly when the source is changed after the pair is
   retained — which is the public reproduction. -/
inductive StoredCoord where
  | snapshot (x y : Int)
  | reference
  deriving Repr

/- Observe a retained coordinate pair given the source container's CURRENT
   contents `(a, b)`. A snapshot ignores them; a reference reflects them. -/
@[grind, simp]
def observe : StoredCoord → Int → Int → Int × Int
  | .snapshot x y, _, _ => (x, y)
  | .reference,    a, b => (a, b)
-- pure-end

-- pre-conditions-start
-- (captureCoordA: a two-component coordinate container.)
-- pre-conditions-end

-- post-conditions-start
-- (captureCoordA: the retained pair equals the container's components at
--  capture time, for every possible later state of the container.)
-- post-conditions-end

/- First coordinate-retaining site. The container `coords` is a two-component
   coordinate (the input pair). The retained pair must reflect the components
   AS THEY ARE AT CAPTURE TIME, independent of any later mutation of `coords`
   (universally quantified over the container's future contents `a b`). -/
method captureCoordA (coords : Array Int) return (out : StoredCoord)
  require coords.size = 2
  ensures ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)
  do
    -- impl-start
    let x := coords[0]!
    let y := coords[1]!
    return StoredCoord.snapshot x y
    -- impl-end

prove_correct captureCoordA by
  loom_solve

-- pre-conditions-start
-- (captureCoordB: a two-component coordinate container.)
-- pre-conditions-end

-- post-conditions-start
-- (captureCoordB: same detachment guarantee as captureCoordA, at the second
--  independent retaining site.)
-- post-conditions-end

/- Second, independent coordinate-retaining site with the same obligation: the
   retained pair must be detached from later mutation of its source container.
   Modeled separately because it is observed independently of the first site. -/
method captureCoordB (coords : Array Int) return (out : StoredCoord)
  require coords.size = 2
  ensures ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)
  do
    -- impl-start
    -- Pre-patch skeleton: the second site retains the input container directly
    -- without detaching its components. The frozen spec demands detachment, so
    -- prove_correct MUST fail here.
    return StoredCoord.reference
    -- impl-end

prove_correct captureCoordB by
  loom_solve
