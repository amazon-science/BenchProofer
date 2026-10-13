import Velvet.Std
-- imports-end

-- Total-correctness semantics: the desired behavior is that pipeline assembly
-- COMPLETES (the real assembler is a finite pass over the configured stages),
-- so the spec must also rule out implementations that diverge (under partial
-- correctness a non-terminating body would vacuously satisfy every
-- postcondition).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is consumed as an opaque axiom for this bundle. The
   behaviour under spec is a pure control/data-flow that assembles a processing
   pipeline stage by stage, threading two coupled facts about the
   partially-assembled pipeline: the execution mode it was RECORDED to run in,
   and the execution mode it ACTUALLY runs in. The two unchanged primitives a
   stage uses — the mode it is wired under (`stageMode`) and the mode-coercion it
   applies to the running pipeline (`adaptedMode`) — are modeled DIRECTLY below as
   deep models, validated value-for-value against the real environment by G-AX
   (mapping.md §3). They are deep-model references, not consumed axioms; every
   observable is computed from the read-only input list of stages. -/
-- axioms-end

-- pure-start
/- One pipeline stage as declared by configuration. `canSync`/`canAsync` are the
   two execution-mode capabilities the stage advertises; `usable` records whether
   the stage actually installs itself when wired to the running pipeline (a stage
   may decline at wire-up time and be skipped). At least one capability is
   advertised — a stage advertising neither is rejected before assembly, so it
   never reaches this list (mapping.md §2). -/
structure Stage where
  canSync  : Bool
  canAsync : Bool
  usable   : Bool
deriving DecidableEq, Inhabited, Repr

/- The execution mode under which a stage is wired, given the mode the running
   pipeline is RECORDED to run in (`flag`). If the recorded mode is synchronous
   and the stage can run synchronously, the stage stays synchronous; otherwise it
   takes its asynchronous capability. (The configuration ladder of the assembler,
   modeled as a nested decision — no `elif`.) -/
def stageMode (flag : Bool) (s : Stage) : Bool :=
  if (flag = false ∧ s.canSync = true) then false else s.canAsync

/- The mode-coercion a stage applies to the running pipeline before wiring it in.
   The pipeline is left in its current actual mode when its RECORDED mode already
   matches the target the stage will run in; otherwise it is converted to that
   target mode. Modeling the unchanged adapter's effect on the running pipeline's
   actual execution mode. -/
def adaptedMode (hmode flag target : Bool) : Bool :=
  if flag = target then hmode else target

/- The state of the partially-assembled pipeline: `flag` is the execution mode it
   is RECORDED to run in (the belief the assembler carries forward); `hmode` is
   the mode it ACTUALLY runs in. The pipeline is CONSISTENT exactly when these
   agree — the recorded mode is not a lie about the real mode. A stage downstream
   trusts `flag` when deciding how to wire the pipeline, so an inconsistent state
   silently mis-wires every later stage. -/
structure Chain where
  flag  : Bool
  hmode : Bool
deriving DecidableEq, Inhabited, Repr

def Chain.consistent (c : Chain) : Prop := c.flag = c.hmode

/- Wire one stage onto the running pipeline. The target mode is chosen from the
   recorded mode; the pipeline is coerced to that target. If the stage installs
   itself (`usable`), it becomes the new running pipeline: BOTH the recorded mode
   and the actual mode advance to the target it was wired at (they advance
   together — the recorded mode is never set without the matching real coercion).
   If the stage declines, the running pipeline is left exactly as it was — the
   skipped stage leaves NO trace on either component (the read-only frame for a
   skipped stage). -/
def wireStage (c : Chain) (s : Stage) : Chain :=
  let target := stageMode c.flag s
  let amode  := adaptedMode c.hmode c.flag target
  if s.usable = true then { flag := target, hmode := amode } else c

/- The pipeline state after wiring a whole list of stages left to right from an
   initial state. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def assemble : Chain → List Stage → Chain
  | c, []      => c
  | c, s :: ss => assemble (wireStage c s) ss

@[grind] lemma assemble_nil (c : Chain) : assemble c [] = c := rfl
@[grind] lemma assemble_cons (c : Chain) (s : Stage) (ss : List Stage) :
    assemble c (s :: ss) = assemble (wireStage c s) ss := rfl

/- Key structural fact: wiring a stage onto a CONSISTENT pipeline yields a
   CONSISTENT pipeline. When the stage installs, recorded and actual modes both
   become the target (trivially equal); when it declines, the pipeline is
   unchanged and stays consistent. The skip branch is exactly where the assembler
   must NOT mutate the running pipeline — committing the target mode-coercion to
   the actual mode while leaving the recorded mode behind would break this. -/
@[grind] lemma wireStage_consistent (c : Chain) (s : Stage) :
    c.consistent → (wireStage c s).consistent := by
  intro h
  unfold wireStage Chain.consistent adaptedMode
  set t := stageMode c.flag s with ht_def
  by_cases hu : s.usable = true
  · simp only [hu, if_true]
    by_cases ht : c.flag = t
    · simp only [ht, if_true]; exact ht.symm.trans h
    · simp only [ht, if_false]
  · simp only [hu]; exact h

/- The whole-list assembly preserves consistency: assembling any number of stages
   onto a consistent initial pipeline yields a consistent pipeline. This is the
   property that pins the behaviour — the assembled pipeline's recorded execution
   mode never diverges from its actual execution mode, so no later stage is wired
   under a false belief about the running pipeline. -/
lemma assemble_consistent (ss : List Stage) :
    ∀ c : Chain, c.consistent → (assemble c ss).consistent := by
  induction ss with
  | nil => intro c h; simpa using h
  | cons s rest ih =>
    intro c h
    rw [assemble_cons]
    exact ih (wireStage c s) (wireStage_consistent c s h)

/- Forward-fold step: extending the consumed prefix by one stage wires that stage
   onto the state built from the shorter prefix. The single goal `loom_solve`
   leaves for the loop body (the Velvet forward-fold pattern). -/
lemma assemble_take_step (init : Chain) (ss : List Stage) (i : Nat) (hi : i < ss.length) :
    assemble init (ss.take (i + 1))
      = wireStage (assemble init (ss.take i)) ss[i]! := by
  have hcons : ss.take (i + 1) = ss.take i ++ [ss[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons]
  clear hcons hi
  -- assemble distributes over append: assemble c (a ++ b) = assemble (assemble c a) b
  induction ss.take i generalizing init with
  | nil => simp [assemble]
  | cons hd tl ih => simp only [List.cons_append, assemble_cons]; exact ih (wireStage init hd)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble a processing pipeline from a list of configured stages, starting from
   a base pipeline whose recorded execution mode matches its actual mode
   (`init.flag = init.hmode`). Stages are wired in order; each is wired under the
   mode the running pipeline is RECORDED to run in, and a stage that declines to
   install must leave the running pipeline untouched. The frozen guarantee: the
   fully-assembled pipeline is CONSISTENT — the mode it is recorded to run in is
   the mode it actually runs in — so that every stage was wired under a faithful
   view of the running pipeline and the finished pipeline runs in the mode it
   reports.

   `stages` is read-only: the method builds and returns a fresh pipeline state and
   never mutates its input. -/
method loadPipeline (init : Chain) (stages : List Stage) return (out : Chain)
  require init.flag = init.hmode
  ensures out = assemble init stages
  ensures out.flag = out.hmode
  do
    -- impl-start
    let mut chain : Chain := init
    let mut i := 0
    while i < stages.length
      invariant i ≤ stages.length
      invariant chain = assemble init (stages.take i)
      done_with i = stages.length
      decreasing stages.length - i
    do
      let s := stages[i]!
      let target := stageMode chain.flag s
      let amode  := adaptedMode chain.hmode chain.flag target
      chain := if s.usable = true then { flag := target, hmode := amode } else chain
      i := i + 1
    return chain
    -- impl-end

prove_correct loadPipeline by
  loom_solve
  case «invariant_2: chain = assemble init (stages.take i)» =>
    have hi : i < stages.length := by omega
    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
  case «ensures_1: out.flag = out.hmode» =>
    cases i_3
    have hlen : i = stages.length := by omega
    rw [invariant_2, hlen, List.take_length]
    exact assemble_consistent stages init require_1
