import Mathlib
-- imports-end

/-!
Assembling a diagnostic frame report from a chain of related failures.

When a failure is reported, it is presented together with the chain of earlier
failures it arose from. The chain is walked in a set order (from the deepest
link outward), and each link contributes its own sequence of call frames to
the report.

The complete report is the in-order concatenation of every link's frames: each
link contributes exactly the frames it carries, and the contributions of the
links are laid end to end in chain order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-link
-- frame sequences are taken as the modeled input (their internal assembly is
-- identical across the behavior under study and is abstracted away), and the
-- combination of those sequences into the final report is modeled structurally
-- as a concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One assembled call frame of the report. Its concrete content is irrelevant
to the behavior modeled here — only which frames appear, and in what order,
matters — so a frame is carried as an opaque identifier. -/
abbrev Frame := Nat
-- pure-end

-- post-conditions-start
/-- `linkFrames` lists, for each link of the chain in walk order, the sequence of
frames that link contributes. The report is the in-order concatenation of all of
them, in chain order. -/
def problem_spec_gatherFrames
    (linkFrames : List (List Frame)) (result : List Frame) : Prop :=
  result = linkFrames.flatten
-- post-conditions-end

-- impl-start
def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
  Id.run do
    let mut frames : List Frame := []
    for tb in linkFrames do
      frames := frames ++ tb
    return frames
-- impl-end

-- proof-start
/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
      = init ++ xs.flatten := by
  induction xs generalizing init with
  | nil => simp; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_gatherFrames :
    ∀ (linkFrames : List (List Frame)),
      problem_spec_gatherFrames linkFrames
        (implementation_gatherFrames linkFrames) := by
  intro lf
  unfold problem_spec_gatherFrames implementation_gatherFrames
  simp only [Id.run, bind, pure]
  rw [gatherFrames_forIn]
  simp
-- proof-end
