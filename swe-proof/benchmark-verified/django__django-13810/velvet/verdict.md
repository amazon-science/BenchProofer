# P2 adversarial audit — django__django-13810

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition `ensures out = assemble init stages` is FULLY FUNCTIONAL — it pins the returned Chain to exactly the frozen `assemble` fold, and the entire `pure` region (assemble/wireStage/stageMode/adaptedMode + lemmas) is part of the frozen spec signature (velvet spec_view elides only the impl region and prove_correct body). Therefore verify ⟹ output == model, and no behaviorally-wrong impl can verify. The only verifying same-spec impls are behavioral echoes of the gold model; their faithful refined patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -163,29 +163,9 @@
   ensures out.flag = out.hmode
   do
     -- impl-start
-    let mut chain : Chain := init
-    let mut i := 0
-    while i < stages.length
-      invariant i ≤ stages.length
-      invariant chain = assemble init (stages.take i)
-      done_with i = stages.length
-      decreasing stages.length - i
-    do
-      let s := stages[i]!
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-      i := i + 1
-    return chain
+    return assemble init stages
     -- impl-end
 
 prove_correct loadPipeline by
   loom_solve
-  case «invariant_2: chain = assemble init (stages.take i)» =>
-    have hi : i < stages.length := by omega
-    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
-  case «ensures_1: out.flag = out.hmode» =>
-    cases i_3
-    have hlen : i = stages.length := by omega
-    rw [invariant_2, hlen, List.take_length]
-    exact assemble_consistent stages init require_1
+  · exact assemble_consistent stages init require_1
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -163,29 +163,15 @@
   ensures out.flag = out.hmode
   do
     -- impl-start
-    let mut chain : Chain := init
-    let mut i := 0
-    while i < stages.length
-      invariant i ≤ stages.length
-      invariant chain = assemble init (stages.take i)
-      done_with i = stages.length
-      decreasing stages.length - i
-    do
-      let s := stages[i]!
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-      i := i + 1
-    return chain
+    return stages.foldl wireStage init
     -- impl-end
 
 prove_correct loadPipeline by
+  have h : ∀ (l : List Stage) (c : Chain), l.foldl wireStage c = assemble c l := by
+    intro l
+    induction l with
+    | nil => intro c; rfl
+    | cons hd tl ih => intro c; simp only [List.foldl_cons, assemble_cons]; exact ih (wireStage c hd)
+  simp only [h]
   loom_solve
-  case «invariant_2: chain = assemble init (stages.take i)» =>
-    have hi : i < stages.length := by omega
-    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
-  case «ensures_1: out.flag = out.hmode» =>
-    cases i_3
-    have hlen : i = stages.length := by omega
-    rw [invariant_2, hlen, List.take_length]
-    exact assemble_consistent stages init require_1
+  exact assemble_consistent stages init require_1
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -174,7 +174,8 @@
       let s := stages[i]!
       let target := stageMode chain.flag s
       let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+      chain := if s.usable = true then { flag := target, hmode := amode }
+                                   else { flag := target, hmode := chain.hmode }
       i := i + 1
     return chain
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -165,7 +165,7 @@
     -- impl-start
     let mut chain : Chain := init
     let mut i := 0
-    while i < stages.length
+    while i + 1 < stages.length
       invariant i ≤ stages.length
       invariant chain = assemble init (stages.take i)
       done_with i = stages.length
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -163,29 +163,9 @@
   ensures out.flag = out.hmode
   do
     -- impl-start
-    let mut chain : Chain := init
-    let mut i := 0
-    while i < stages.length
-      invariant i ≤ stages.length
-      invariant chain = assemble init (stages.take i)
-      done_with i = stages.length
-      decreasing stages.length - i
-    do
-      let s := stages[i]!
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-      i := i + 1
-    return chain
+    return init
     -- impl-end
 
 prove_correct loadPipeline by
   loom_solve
-  case «invariant_2: chain = assemble init (stages.take i)» =>
-    have hi : i < stages.length := by omega
-    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
-  case «ensures_1: out.flag = out.hmode» =>
-    cases i_3
-    have hlen : i = stages.length := by omega
-    rw [invariant_2, hlen, List.take_length]
-    exact assemble_consistent stages init require_1
+  · exact require_1
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -172,7 +172,7 @@
       decreasing stages.length - i
     do
       let s := stages[i]!
-      let target := stageMode chain.flag s
+      let target := s.canAsync
       let amode  := adaptedMode chain.hmode chain.flag target
       chain := if s.usable = true then { flag := target, hmode := amode } else chain
       i := i + 1
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -172,18 +172,18 @@
       decreasing stages.length - i
     do
       let s := stages[i]!
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+      -- distinct spelling: build the wired chain via wireStage directly
+      chain := wireStage chain s
       i := i + 1
-    return chain
+    let result := chain
+    return result
     -- impl-end
 
 prove_correct loadPipeline by
   loom_solve
   case «invariant_2: chain = assemble init (stages.take i)» =>
     have hi : i < stages.length := by omega
-    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
+    rw [assemble_take_step init stages i hi, ← invariant_2]
   case «ensures_1: out.flag = out.hmode» =>
     cases i_3
     have hlen : i = stages.length := by omega
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT — django__django-13810 velvet.

Protocol run from project root. same_spec confirmed True for ALL 7 attacks + pos_control + prepatch (velvet backend). Positive control verifies (exit 0); prepatch reproduced and FAILS (exit 1) at the fold-step invariant_2 because its skip-branch commits `hmode := amode` while leaving `flag` behind — exactly the pre-patch bug (handler overwritten before try knows outcome, poisoning the skip path).

Verify command (each): `bash scripts/lean_verify.sh <atk>.lean` (exit 0=verifies, 1=error, 3=sorry, 124=timeout). Ran concurrently in 2 batches of 4 background jobs.

### ATTACK RESULTS (all same_spec=True):
- atk_1 ungrounded-oracle echo `return assemble init stages` → exit 0 VERIFIES (behavioral echo of gold).
- atk_2 echo via `stages.foldl wireStage init` (distinct expression, proved == assemble) → exit 0 VERIFIES.
- atk_3 control-flow-effect: skip-branch sets `{flag:=target,hmode:=chain.hmode}` i.e. carries target forward on skip (prepatch-family bug) → exit 1 REJECTED (fold-step). Spec tightness confirmed.
- atk_4 boundary/off-by-one: loop guard `i+1 < len` stops one stage early → exit 1 REJECTED (done_with i=stages.length unsatisfiable). Spec tightness confirmed.
- atk_5 partial-domain: `return init` (ignores stages) → exit 1 REJECTED (postcondition out=assemble fails). Spec tightness confirmed.
- atk_6 ungrounded target: `target := s.canAsync` (ignores stageMode ladder) → exit 1 REJECTED (fold-step wireStage mismatch). Spec tightness confirmed.
- atk_7 echo via index-loop `wireStage chain s` with distinct return spelling → exit 0 VERIFIES (behavioral echo of gold).

MANDATORY RESOLVE STEP (step 2): the 3 verifying impls (atk_1/atk_2/atk_7) are behavioral echoes computing EXACTLY `assemble init stages` = the gold model behavior, so their faithful refined patch is the gold patch. Executed `run_resolve('django__django-13810', gold_patch, timeout=1800)` via official harness (swe_bench_verified, supports_docker_oracle=True, resolve_style=swebench) → RESOLVED: True, completed=True, note='resolved'. Patch text materialized at faithful_patch.diff. NO verifying wrong impl exists whose faithful patch fails to resolve.

A-LEG / MODEL↔PATCH AUDIT (refinement.md + mapping.md + axiom_check.py):
- No consumed axioms (axioms region is prose only). Two A-reference deep models, both validated by G-AX (axiom_check.py, in-container):
  * A-reference 1 `adaptedMode hmode flag target = if flag=target then hmode else target` == real `adapt_method_mode`'s actual-mode effect in the consistent regime (flag==actual). Checked all 4 (actual×target) combos; matches. Sound scope: the real asgiref adapter is only total in the consistent regime (outside it raises TypeError — the exact runtime poisoning the out.flag=out.hmode postcondition forbids). This regime restriction is the invariant the assembler maintains (Chain.consistent), so the deep model faithfully bounds the callee where the assembler actually calls it.
  * A-reference 2 `stageMode flag s = if (flag=false ∧ canSync) then false else canAsync` == the verbatim `if/elif/else` middleware_is_async ladder (base.py:43-51). Checked all 8 flag×canSync×canAsync combos + 2 RuntimeError neither-capable boundary cases (correctly excluded from the modeled stages list). Matches.
- refinement.md legs: every step is R / A-reference / I — NO kind-3 (inexpressible-changed-op). A4 (the discriminating leg) faithfully corresponds to the gold hunk: a USED stage advances BOTH flag (gold `handler_is_async=middleware_is_async`, base.py:89) and hmode (gold `else: handler=adapted_handler`); a SKIPPED stage (MiddlewareNotUsed→continue) leaves the chain untouched (gold moves the commit into the no-exception else). The skip-path frame is exactly the fixed behavior, and prepatch reproduces the bug and fails.

**CONCLUSION:** verify ⇒ correct holds for this bundle. The fully-functional postcondition makes the spec tight (4/4 wrong-behavior impls rejected); the only verifying same-spec impls are gold-equivalent echoes and their materialized faithful patch RESOLVES under the official harness. A-legs sound, model↔patch correspondence faithful, no kind-3 legs. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition `ensures out = assemble init stages` is FULLY FUNCTIONAL — it pins the returned Chain to exactly the frozen `assemble` fold, and the entire `pure` region (assemble/wireStage/stageMode/adaptedMode + lemmas) is part of the frozen spec signature (velvet spec_view elides only the impl region and prove_correct body). Therefore verify ⟹ output == model, and no behaviorally-wrong impl can verify. The only verifying same-spec impls are behavioral echoes of the gold model; their faithful refined patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT — django__django-13810 velvet.

Protocol run from project root. same_spec confirmed True for ALL 7 attacks + pos_control + prepatch (velvet backend). Positive control verifies (exit 0); prepatch reproduced and FAILS (exit 1) at the fold-step invariant_2 because its skip-branch commits `hmode := amode` while leaving `flag` behind — exactly the pre-patch bug (handler overwritten before try knows outcome, poisoning the skip path).

Verify command (each): `bash scripts/lean_verify.sh <atk>.lean` (exit 0=verifies, 1=error, 3=sorry, 124=timeout). Ran concurrently in 2 batches of 4 background jobs.

### ATTACK RESULTS (all same_spec=True):
- atk_1 ungrounded-oracle echo `return assemble init stages` → exit 0 VERIFIES (behavioral echo of gold).
- atk_2 echo via `stages.foldl wireStage init` (distinct expression, proved == assemble) → exit 0 VERIFIES.
- atk_3 control-flow-effect: skip-branch sets `{flag:=target,hmode:=chain.hmode}` i.e. carries target forward on skip (prepatch-family bug) → exit 1 REJECTED (fold-step). Spec tightness confirmed.
- atk_4 boundary/off-by-one: loop guard `i+1 < len` stops one stage early → exit 1 REJECTED (done_with i=stages.length unsatisfiable). Spec tightness confirmed.
- atk_5 partial-domain: `return init` (ignores stages) → exit 1 REJECTED (postcondition out=assemble fails). Spec tightness confirmed.
- atk_6 ungrounded target: `target := s.canAsync` (ignores stageMode ladder) → exit 1 REJECTED (fold-step wireStage mismatch). Spec tightness confirmed.
- atk_7 echo via index-loop `wireStage chain s` with distinct return spelling → exit 0 VERIFIES (behavioral echo of gold).

MANDATORY RESOLVE STEP (step 2): the 3 verifying impls (atk_1/atk_2/atk_7) are behavioral echoes computing EXACTLY `assemble init stages` = the gold model behavior, so their faithful refined patch is the gold patch. Executed `run_resolve('django__django-13810', gold_patch, timeout=1800)` via official harness (swe_bench_verified, supports_docker_oracle=True, resolve_style=swebench) → RESOLVED: True, completed=True, note='resolved'. Patch text materialized at faithful_patch.diff. NO verifying wrong impl exists whose faithful patch fails to resolve.

A-LEG / MODEL↔PATCH AUDIT (refinement.md + mapping.md + axiom_check.py):
- No consumed axioms (axioms region is prose only). Two A-reference deep models, both validated by G-AX (axiom_check.py, in-container):
  * A-reference 1 `adaptedMode hmode flag target = if flag=target then hmode else target` == real `adapt_method_mode`'s actual-mode effect in the consistent regime (flag==actual). Checked all 4 (actual×target) combos; matches. Sound scope: the real asgiref adapter is only total in the consistent regime (outside it raises TypeError — the exact runtime poisoning the out.flag=out.hmode postcondition forbids). This regime restriction is the invariant the assembler maintains (Chain.consistent), so the deep model faithfully bounds the callee where the assembler actually calls it.
  * A-reference 2 `stageMode flag s = if (flag=false ∧ canSync) then false else canAsync` == the verbatim `if/elif/else` middleware_is_async ladder (base.py:43-51). Checked all 8 flag×canSync×canAsync combos + 2 RuntimeError neither-capable boundary cases (correctly excluded from the modeled stages list). Matches.
- refinement.md legs: every step is R / A-reference / I — NO kind-3 (inexpressible-changed-op). A4 (the discriminating leg) faithfully corresponds to the gold hunk: a USED stage advances BOTH flag (gold `handler_is_async=middleware_is_async`, base.py:89) and hmode (gold `else: handler=adapted_handler`); a SKIPPED stage (MiddlewareNotUsed→continue) leaves the chain untouched (gold moves the commit into the no-exception else). The skip-path frame is exactly the fixed behavior, and prepatch reproduces the bug and fails.

**CONCLUSION:** verify ⇒ correct holds for this bundle. The fully-functional postcondition makes the spec tight (4/4 wrong-behavior impls rejected); the only verifying same-spec impls are gold-equivalent echoes and their materialized faithful patch RESOLVES under the official harness. A-legs sound, model↔patch correspondence faithful, no kind-3 legs. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True under VelvetBackend.language). Solution.lean verifies with lean_verify.sh (exit 0). Cross-checked the two deep-model callees against the real load_middleware/adapt_method_mode at base_commit 429d089d0a8fbd400e0c010708df4f0d16218970 (django/core/handlers/base.py):

(1) stageMode(flag,s) = if (flag=false ∧ canSync) then false else canAsync EXACTLY matches the base.py:43-51 middleware_is_async ladder over stages advertising ≥1 capability: `elif not handler_is_async and middleware_can_sync: False; else: middleware_can_async`.

(2) adaptedMode(hmode,flag,target) = if flag=target then hmode else target EXACTLY matches adapt_method_mode's actual-mode effect: method_is_async is passed explicitly as flag, so flag≠target ⇒ sync_to_async/async_to_sync wrap flips actual mode to target; flag=target ⇒ `return method` leaves actual mode = hmode. Verified all four flag×target combos.

(3) wireStage used-branch {flag:=target, hmode:=amode} matches the gold `else: handler = adapted_handler` + base.py:89 `handler_is_async = middleware_is_async`; in every reachable consistent (flag=hmode) case amode=target so flag=hmode is preserved. Skip-branch `else c` matches the gold MiddlewareNotUsed→continue frame (handler untouched); prepatch's hmode-only flip is caught by Solution_prepatch/G-DIFF.

The only apparent divergence is a Stage advertising NEITHER capability (canSync=canAsync=false): the real callee raises RuntimeError and aborts, whereas the model would fold it. This is a documented abstraction-domain restriction (mapping.md §2): such stages never reach the modeled `stages` list, the RuntimeError boundary is checked by G-AX, and G-CONF excludes them. It enlarges the modeled domain rather than strengthening the spec, and the consistency postcondition still holds. Within the faithful domain (require init.flag=init.hmode, stages with canSync∨canAsync) the model agrees with the real callee value-for-value. No spec-too-strong drift found. Mechanized gates (G-AX, G-CONF, G-EQ, G-DIFF, panels) all pass.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True with velvet backend — the frozen spec region is byte-identical; only impl/proof differ. Prepatch models the poisoned skip-path (else { flag := chain.flag, hmode := amode }) and fails G-DIFF as recorded.

**Leakage assessment:** the spec view (axioms comment + pure helpers stageMode/adaptedMode/wireStage/assemble + consistency lemmas + loadPipeline signature/require/ensures) is written entirely in domain-neutral vocabulary (pipeline/stages/wire/recorded-mode vs actual-mode/consistent). Lexical scan of the spec view finds NONE of the gold-patch or Django identifiers: adapt_method_mode, adapted_handler, MiddlewareNotUsed, load_middleware, handler, middleware, ASGI, coroutine, HttpResponse, settings, DEBUG. Only 'async' appears, inside the generic phrase 'asynchronous capability'.

The corrective behavior the spec pins — a stage that declines to install must leave the running pipeline untouched (wireStage else-branch), and the final chain is consistent (out.flag = out.hmode) — does not exceed what the PUBLIC problem_statement already states in concrete terms: it explicitly says MiddlewareNotUsed leaves 'handler variable overwritten with output of self.adapt_method_mode()', poisoning the chain. hints_text is trivial ('Many thanks for the detailed report.') and irrelevant. No spec-view line quotes gold-patch specifics or reconstructs the edit beyond the public problem_statement. Provenance is cold. G-PANEL-3: NO-LEAKAGE.

**Spec integrity:** same_spec(Solution.lean, Solution_prepatch.lean)=True with velvet backend — the frozen spec region is byte-identical; only impl/proof differ. Prepatch models the poisoned skip-path (else { flag := chain.flag, hmode := amode }) and fails G-DIFF as recorded.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
