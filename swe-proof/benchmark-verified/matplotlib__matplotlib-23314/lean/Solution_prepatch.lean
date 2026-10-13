import Mathlib
-- imports-end

/-!
A drawable plotting component is rendered by a procedure that carries out drawing
work and returns nothing. The component carries a visibility flag. The desired
behavior: a component that is hidden must contribute nothing to the output — it
must carry out no drawing at all — while a shown component renders its full
contents.
-/

-- axioms-start
/-- A drawable component. Only the field the behavior depends on is modeled:
whether the component is currently shown. -/
structure Drawable where
  visible : Bool
-- axioms-end

-- pure-start
-- pure-end

-- post-conditions-start
/-- Rendering is a PROCEDURE, not a function of the output: it returns nothing,
and all it can be observed doing is the drawing it carries out. So the behavior
is modeled as the ACTION performed — in an ARBITRARY effect monad `m`, built from
an ARBITRARY contents-rendering action `renderContents`. `m` offers nothing else:
there is no way to read the output back and no way to undo an action once it has
been carried out. Carrying out `renderContents` is therefore observable, and the
only way to contribute nothing to the output is not to carry it out.

A hidden component's action is doing nothing at all; a shown component's action
is rendering its full contents. Both cases pin the entire action to the inputs. -/
def problem_spec_render {m : Type → Type} [Monad m] (renderContents : m Unit)
    (self : Drawable) (result : m Unit) : Prop :=
  (self.visible = false → result = pure ()) ∧
  (self.visible = true  → result = renderContents)
-- post-conditions-end

-- impl-start
def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
    (self : Drawable) : m Unit := do
  renderContents
-- impl-end

-- proof-start
theorem correct_render : ∀ {m : Type → Type} [Monad m] [LawfulMonad m]
    (renderContents : m Unit) (self : Drawable),
    problem_spec_render renderContents self
      (implementation_render renderContents self) := by
  intro m _ _ renderContents self
  unfold problem_spec_render implementation_render
  refine ⟨?_, ?_⟩
  · intro h; simp
  · intro h; simp
-- proof-end
