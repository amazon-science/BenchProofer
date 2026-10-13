import Mathlib
-- imports-end

/-!
Assembling a request-processing pipeline from an ordered list of configured
stages, starting from a base pipeline whose recorded execution mode agrees with
its actual execution mode.

Each stage is wired onto the running pipeline in order. A stage is wired under
the execution mode the running pipeline is currently RECORDED to run in; before
wiring, the running pipeline is coerced to the target mode the stage will run
at. A stage may decline to install itself at wire-up time, in which case it is
skipped and must leave the running pipeline exactly as it was.

Two coupled facts about the partially-assembled pipeline are threaded through
the assembly: the execution mode it is RECORDED to run in, and the execution
mode it ACTUALLY runs in. The pipeline is CONSISTENT exactly when these agree.
The guarantee pinned here is that assembling stages onto a consistent base
pipeline yields a consistent pipeline: the mode the finished pipeline reports is
the mode it actually runs in, so every stage was wired under a faithful view of
the running pipeline.
-/

-- axioms-start
/- No unchanged outside callee is consumed as an opaque axiom for this bundle.
   The two primitives a stage uses — the mode it is wired under (`stageMode`) and
   the mode-coercion it applies to the running pipeline (`adaptedMode`) — are
   modeled DIRECTLY below as deep models (A-reference), validated value-for-value
   against the real environment by G-AX (mapping.md §3). Every observable is
   computed from the read-only input list of stages. -/
-- axioms-end

-- pure-start
/-- One pipeline stage as declared by configuration. `canSync`/`canAsync` are the
two execution-mode capabilities the stage advertises; `usable` records whether
the stage actually installs itself when wired to the running pipeline (a stage
may decline at wire-up time and be skipped). -/
structure Stage where
  canSync  : Bool
  canAsync : Bool
  usable   : Bool
deriving DecidableEq, Inhabited, Repr

/-- The execution mode under which a stage is wired, given the mode the running
pipeline is RECORDED to run in (`flag`). If the recorded mode is synchronous and
the stage can run synchronously, the stage stays synchronous; otherwise it takes
its asynchronous capability. -/
def stageMode (flag : Bool) (s : Stage) : Bool :=
  if (flag = false ∧ s.canSync = true) then false else s.canAsync

/-- The mode-coercion a stage applies to the running pipeline before wiring it
in. The pipeline is left in its current actual mode when its RECORDED mode
already matches the target the stage will run in; otherwise it is converted to
that target mode. -/
def adaptedMode (hmode flag target : Bool) : Bool :=
  if flag = target then hmode else target

/-- The state of the partially-assembled pipeline: `flag` is the execution mode
it is RECORDED to run in; `hmode` is the mode it ACTUALLY runs in. -/
structure Chain where
  flag  : Bool
  hmode : Bool
deriving DecidableEq, Inhabited, Repr

/-- A pipeline is CONSISTENT exactly when its recorded mode equals its actual
mode. -/
def Chain.consistent (c : Chain) : Prop := c.flag = c.hmode

/-- Wire one stage onto the running pipeline. The target mode is chosen from the
recorded mode; the pipeline is coerced to that target. If the stage installs
itself (`usable`), it becomes the new running pipeline: BOTH the recorded mode
and the actual mode advance to the target it was wired at. If the stage declines,
the running pipeline is left exactly as it was. -/
def wireStage (c : Chain) (s : Stage) : Chain :=
  let target := stageMode c.flag s
  let amode  := adaptedMode c.hmode c.flag target
  if s.usable = true then { flag := target, hmode := amode } else c

/-- The pipeline state after wiring a whole list of stages left to right from an
initial state. -/
def assemble : Chain → List Stage → Chain
  | c, []      => c
  | c, s :: ss => assemble (wireStage c s) ss

/-- Wiring a stage onto a CONSISTENT pipeline yields a CONSISTENT pipeline. When
the stage installs, recorded and actual modes both become the target; when it
declines, the pipeline is unchanged. -/
theorem wireStage_consistent (c : Chain) (s : Stage) :
    c.consistent → (wireStage c s).consistent := by
  intro h
  unfold wireStage Chain.consistent adaptedMode
  set t := stageMode c.flag s with ht_def
  by_cases hu : s.usable = true
  · simp only [hu, if_true]
    by_cases ht : c.flag = t
    · simp only [ht, if_true]; exact ht.symm.trans h
    · simp only [ht, if_false]
  · simp only [hu, if_false, Bool.false_eq_true]; exact h

/-- Whole-list assembly preserves consistency. -/
theorem assemble_consistent (ss : List Stage) :
    ∀ c : Chain, c.consistent → (assemble c ss).consistent := by
  induction ss with
  | nil => intro c h; simpa [assemble] using h
  | cons s rest ih =>
    intro c h
    simp only [assemble]
    exact ih (wireStage c s) (wireStage_consistent c s h)
-- pure-end

-- post-conditions-start
/-- The assembled pipeline is fully pinned: it is exactly the left-to-right fold
of `wireStage` over `stages` from `init`, and — given a consistent base — it is
itself consistent (recorded mode equals actual mode). No output component is left
free. -/
def problem_spec_loadPipeline (init : Chain) (stages : List Stage)
    (result : Chain) : Prop :=
  result = assemble init stages ∧
    (init.consistent → result.consistent)
-- post-conditions-end

-- impl-start
def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=
  Id.run do
    let mut chain : Chain := init
    for s in stages do
      let target := stageMode chain.flag s
      let amode  := adaptedMode chain.hmode chain.flag target
      -- A declined stage commits the adapter's coercion to the actual mode while
      -- leaving the recorded mode behind (the running pipeline is NOT left as it
      -- was), so a skipped stage can desync recorded mode from actual mode.
      chain := if s.usable = true then { flag := target, hmode := amode }
               else { flag := chain.flag, hmode := amode }
    return chain
-- impl-end

-- proof-start
/-- The desugared `forIn` accumulation, generalized over the running chain,
computes `assemble chain stages`. -/
theorem forIn_loadPipeline_helper (stages : List Stage) : ∀ chain : Chain,
    Id.run (forIn stages chain
      (fun s c => do
        pure PUnit.unit
        pure (ForInStep.yield
          (let target := stageMode c.flag s
           let amode  := adaptedMode c.hmode c.flag target
           if s.usable = true then { flag := target, hmode := amode } else c))))
      = assemble chain stages := by
  induction stages with
  | nil => intro chain; simp [assemble, Id.run, pure]
  | cons s ss ih =>
    intro chain
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp only [assemble, wireStage]

theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),
    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by
  intro init stages
  unfold problem_spec_loadPipeline implementation_loadPipeline
  have h := forIn_loadPipeline_helper stages init
  simp only [Id.run] at h ⊢
  rw [h]
  exact ⟨rfl, assemble_consistent stages init⟩
-- proof-end
