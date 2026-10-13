import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The full body of work this routine performs when it
--  is enabled — adjusting the view, projecting and ordering the child elements,
--  and emitting them to the output target — is UNCHANGED, and its result is
--  observed only through the free input `renderedScene : Scene`. The spec makes
--  no behavioural claim about HOW that work composes the scene and holds for
--  EVERY value it could take, so there is nothing to check against a real callee,
--  hence no G-AX. The behaviour under spec — suppressing all of that work when
--  the element is hidden — is modeled deeply in the `pure`/`impl` regions, with
--  no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An opaque snapshot of what gets emitted to the output target. Only whether it
   is EMPTY (nothing emitted) vs. some concrete content is observed here, so a
   single opaque carrier suffices; its internal structure is irrelevant to the
   decision under spec. -/
abbrev Scene := Nat

/- The empty emission: nothing is placed on the output target. -/
def blank : Scene := 0

/- What a render step yields, recording BOTH observables that distinguish the
   desired behaviour:
   * `emitted` — whether ANY emission work was performed at all. `false` means
                 the routine returned immediately and touched the output target
                 not at all.
   * `scene`   — the content actually placed on the output target. -/
structure RenderResult where
  emitted : Bool
  scene   : Scene
  deriving DecidableEq, Inhabited

/- The desired behaviour of the render step.

   An element that has been marked hidden must not appear on the output target:
   the routine must perform NO emission work and place nothing there. Only when
   the element is visible does it carry out its full emission, whose content is
   `renderedScene`. The decision is taken on the element's own visibility flag
   alone, before any emission work begins. -/
def renderDecision (visible : Bool) (renderedScene : Scene) : RenderResult :=
  if visible then
    { emitted := true, scene := renderedScene }
  else
    { emitted := false, scene := blank }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A render step for one composite element of a figure. It is handed the
   element's own visibility flag (`visible`) and — as a read-only free input —
   the content its full emission would place on the output target were it
   carried out (`renderedScene`).

   It returns a `RenderResult` whose `emitted` flag records whether ANY emission
   work was performed and whose `scene` is what ended up on the output target.
   The desired behaviour is `renderDecision`: when the element is hidden, perform
   no emission work and leave the output target untouched (nothing is placed);
   only when it is visible does the routine carry out its full emission and place
   that content.

   `visible` and `renderedScene` are both read-only (neither is `mut`): the
   routine reads them and builds a fresh result, mutating nothing it is handed
   (directive 5). -/
method renderStep (visible : Bool) (renderedScene : Scene) return (out : RenderResult)
  ensures out = renderDecision visible renderedScene
  -- Discriminating clause: a hidden element places NOTHING and does NO work.
  ensures (visible = false) → (out.emitted = false ∧ out.scene = blank)
  do
    -- impl-start
    -- A hidden element is excluded before any emission work begins: the routine
    -- returns immediately, leaving the output target untouched. Only a visible
    -- element proceeds into its full emission, placing `renderedScene`.
    if visible = false then
      return { emitted := false, scene := blank }
    else
      return { emitted := true, scene := renderedScene }
    -- impl-end

prove_correct renderStep by
  loom_solve <;> simp_all [renderDecision]
