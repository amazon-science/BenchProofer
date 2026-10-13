# P2 adversarial audit — django__django-13810

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,7 +126,8 @@
     for s in stages do
       let target := stageMode chain.flag s
       let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+      chain := if s.usable = true then { flag := target, hmode := amode }
+               else { flag := chain.flag, hmode := amode }
     return chain
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,10 +123,8 @@
 def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=
   Id.run do
     let mut chain : Chain := init
-    for s in stages do
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+    for _s in stages do
+      chain := chain
     return chain
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,7 +126,7 @@
     for s in stages do
       let target := stageMode chain.flag s
       let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+      chain := { flag := target, hmode := amode }
     return chain
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,8 +125,7 @@
     let mut chain : Chain := init
     for s in stages do
       let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
+      chain := if s.usable = true then { flag := target, hmode := target } else chain
     return chain
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,7 +124,7 @@
   Id.run do
     let mut chain : Chain := init
     for s in stages do
-      let target := stageMode chain.flag s
+      let target := stageMode chain.hmode s
       let amode  := adaptedMode chain.hmode chain.flag target
       chain := if s.usable = true then { flag := target, hmode := amode } else chain
     return chain
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,13 +121,7 @@
 
 -- impl-start
 def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=
-  Id.run do
-    let mut chain : Chain := init
-    for s in stages do
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-    return chain
+  { flag := init.flag, hmode := init.flag }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,13 +121,7 @@
 
 -- impl-start
 def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=
-  Id.run do
-    let mut chain : Chain := init
-    for s in stages do
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-    return chain
+  assemble init stages.reverse
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,13 +121,9 @@
 
 -- impl-start
 def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=
-  Id.run do
-    let mut chain : Chain := init
-    for s in stages do
-      let target := stageMode chain.flag s
-      let amode  := adaptedMode chain.hmode chain.flag target
-      chain := if s.usable = true then { flag := target, hmode := amode } else chain
-    return chain
+  match stages with
+  | []      => init
+  | _ :: ss => assemble init ss
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
  assemble init stages
-- impl-end

-- proof-start
theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),
    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by
  intro init stages
  unfold problem_spec_loadPipeline implementation_loadPipeline
  exact ⟨rfl, assemble_consistent stages init⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec's postcondition FULLY PINS the result: problem_spec_loadPipeline := result = assemble init stages AND (init.consistent -> result.consistent), where assemble/wireStage/stageMode/adaptedMode are concrete defs in the pure region (NO axioms, no opaque). Any verifying impl is therefore extensionally equal to the modeled gold on all inputs, so behaviorally-wrong impls cannot verify.

Protocol executed (all; all 8 attacks + pos confirmed same_spec=True via swebench_unified.markers.same_spec on lean backend).

Command per file: bash scripts/lean_verify.sh <path> (run concurrently, <=4 at a time).

Results:
- pos.lean (assemble init stages): exit 0 (VERIFIES, no sorry). #print axioms correct_loadPipeline => depends on axioms: [propext] (clean).
- atk_1 (PREPATCH BUG: declined stage commits amode to hmode, recorded mode left behind): exit 1 (fails at rewrite 'assemble init stages' — result != assemble). prepatch data-flow reproduced.
- atk_2 (partial-domain: never install, return init): exit 1.
- atk_3 (boundary: install ignoring usable): exit 1.
- atk_4 (control-flow-effect: on install set hmode := target): exit 1.
- atk_5 (wrong wiring mode: stageMode chain.hmode instead of chain.flag): exit 1.
- atk_6 (ungrounded-oracle echo: return fixed consistent {init.flag,init.flag}, consistent-by-construction but wrong value): exit 1.
- atk_7 (reversed fold: assemble init stages.reverse): exit 1.
- atk_8 (off-by-one: drop first stage): exit 1.

All 8 wrong impls fail at exactly the proof step tying result to `assemble init stages` (verified via error logs: 'rewrite failed: Did not find an occurrence of the pattern assemble init stages'), i.e. genuine spec rejection, not spurious syntax/type errors. NO wrong impl closed with a clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) has NO candidates — patches={}.

A-leg audit (the focus): axiom_check.py (G-AX) PASS exit 0 — exhaustive over all boolean combinations: stageMode == real base.py:43-51 mode-selection ladder (incl. RuntimeError neither-capable boundary), adaptedMode == adapt_method_mode's actual-mode effect (base.py:97-122). Verified value-for-value against the REAL repo source at base_commit 429d089d (checked base.py load_middleware + adapt_method_mode). conformance_check.py (G-CONF) PASS exit 0 — 150,006 inputs, 0 disagreements shadow-vs-postpatch, seed 13810, skip_path_exercised=True.

refinement.md audit: every leg is R / A-reference / I; §C explicitly asserts no kind-3 and it holds — the two called-but-unchanged callees (mode-selection ladder, adapt_method_mode) are deep-modeled as pure defs and G-AX-validated == the real callees, not hidden behind axioms. A-legs' correspondence to the real callees holds (confirmed against repo source). mapping.md §1-4 bindings consistent with base.py.

No path to verify AND-NOT-correct found across 8 distinct wrong impls (partial-domain, boundary, control-flow-effect, off-by-one/order, ungrounded echo, prepatch bug).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
  assemble init stages
-- impl-end

-- proof-start
theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),
    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by
  intro init stages
  unfold problem_spec_loadPipeline implementation_loadPipeline
  exact ⟨rfl, assemble_consistent stages init⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec's postcondition FULLY PINS the result: problem_spec_loadPipeline := result = assemble init stages AND (init.consistent -> result.consistent), where assemble/wireStage/stageMode/adaptedMode are concrete defs in the pure region (NO axioms, no opaque). Any verifying impl is therefore extensionally equal to the modeled gold on all inputs, so behaviorally-wrong impls cannot verify.

Protocol executed (all; all 8 attacks + pos confirmed same_spec=True via swebench_unified.markers.same_spec on lean backend).

Command per file: bash scripts/lean_verify.sh <path> (run concurrently, <=4 at a time).

Results:
- pos.lean (assemble init stages): exit 0 (VERIFIES, no sorry). #print axioms correct_loadPipeline => depends on axioms: [propext] (clean).
- atk_1 (PREPATCH BUG: declined stage commits amode to hmode, recorded mode left behind): exit 1 (fails at rewrite 'assemble init stages' — result != assemble). prepatch data-flow reproduced.
- atk_2 (partial-domain: never install, return init): exit 1.
- atk_3 (boundary: install ignoring usable): exit 1.
- atk_4 (control-flow-effect: on install set hmode := target): exit 1.
- atk_5 (wrong wiring mode: stageMode chain.hmode instead of chain.flag): exit 1.
- atk_6 (ungrounded-oracle echo: return fixed consistent {init.flag,init.flag}, consistent-by-construction but wrong value): exit 1.
- atk_7 (reversed fold: assemble init stages.reverse): exit 1.
- atk_8 (off-by-one: drop first stage): exit 1.

All 8 wrong impls fail at exactly the proof step tying result to `assemble init stages` (verified via error logs: 'rewrite failed: Did not find an occurrence of the pattern assemble init stages'), i.e. genuine spec rejection, not spurious syntax/type errors. NO wrong impl closed with a clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) has NO candidates — patches={}.

A-leg audit (the focus): axiom_check.py (G-AX) PASS exit 0 — exhaustive over all boolean combinations: stageMode == real base.py:43-51 mode-selection ladder (incl. RuntimeError neither-capable boundary), adaptedMode == adapt_method_mode's actual-mode effect (base.py:97-122). Verified value-for-value against the REAL repo source at base_commit 429d089d (checked base.py load_middleware + adapt_method_mode). conformance_check.py (G-CONF) PASS exit 0 — 150,006 inputs, 0 disagreements shadow-vs-postpatch, seed 13810, skip_path_exercised=True.

refinement.md audit: every leg is R / A-reference / I; §C explicitly asserts no kind-3 and it holds — the two called-but-unchanged callees (mode-selection ladder, adapt_method_mode) are deep-modeled as pure defs and G-AX-validated == the real callees, not hidden behind axioms. A-legs' correspondence to the real callees holds (confirmed against repo source). mapping.md §1-4 bindings consistent with base.py.

No path to verify AND-NOT-correct found across 8 distinct wrong impls (partial-domain, boundary, control-flow-effect, off-by-one/order, ungrounded echo, prepatch bug).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO reachable divergence between the modeled function and the real callee. Technical gates pass: lean_verify exit 0, no sorry; #print axioms correct_loadPipeline = [propext, Quot.sound] (clean, no sorryAx); spec_view renders the axioms/pure/post-conditions regions self-containedly.

Modeled callees: stageMode (the middleware_is_async selection ladder base.py:43-51) and adaptedMode (actual-mode effect of adapt_method_mode base.py:97-134), plus wireStage/assemble modeling the post-patch load_middleware loop. I built a faithful executable reference of real load_middleware tracking (handler_is_async=recorded, iscoroutinefunction(handler)=actual) using adapt_method_mode's real control flow and Django's post-install invariant (mw_instance runs in middleware_is_async mode). Exhaustive comparison over the FULL reachable domain — consistent bases (init.flag=init.hmode, always true in the real repo since the base handler is built and recorded in the same is_async mode), capable stages (canSync∨canAsync), stage lists len<=4 — yielded 0 divergences.

Out-of-domain boundaries the model doesn't mirror are genuinely unreachable and therefore NOT defects: (1) inconsistent base — never occurs; and the postcondition's consistency conjunct is guarded by init.consistent, so the spec is not over-strong. (2) neither-capable stage (canSync=canAsync=false) — real repo raises RuntimeError and aborts before the fold, so such stages never enter `stages` (mapping §2). Declined-stage frame (usable=false -> chain unchanged) matches the gold's MiddlewareNotUsed continue leaving handler/handler_is_async untouched. On a usable stage in the consistent regime, adaptedMode(hmode,flag,target)=target always, matching the real post-install actual mode = target. The spec is faithful to the real callee on every reachable input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for django__django-13810 (lean). The consumer spec view (markers.spec_view over Solution.lean) elides impl+proof to placeholders and exposes only: the docstring, an empty axioms note, the pure region (Stage/Chain structures, stageMode, adaptedMode, wireStage, assemble, Chain.consistent, and the two consistency theorems), and the postcondition problem_spec_loadPipeline. VERIFICATION PERFORMED: (1) leakage.screen(Solution, lean, patch, problem_statement) => passed=True, hard_failures=[], warnings=[]; recorded meta G-LEAK status=pass, not relaxed. (2) Manual symbol-echo check: NONE of the gold/repo identifiers appear in the spec view (adapt_method_mode, adapted_handler, MiddlewareNotUsed, load_middleware, handler_is_async, base.py, sync_capable, async_capable, iscoroutinefunction, handler, middleware). Modeling vocabulary is fully abstracted (pipeline/stage/wired/recorded-mode/actual-mode/usable). No diff markers, no patched file path, no bug/fix narration in the view. (3) same_spec(Solution, Solution_prepatch)=True — the discriminating gold behaviour lives in the ELIDED impl/proof, not in the frozen spec view; the prepatch shares the identical spec view and fails only on the hidden impl. SEMANTIC JUDGMENT: The gold edit's observable fixed behaviour — a stage that declines (raises MiddlewareNotUsed) must leave the running handler/pipeline untouched, and the assembled chain must remain mode-consistent — is ALREADY stated explicitly in the PUBLIC problem_statement (it narrates that the skip path 'leaves handler variable overwritten', 'poisons' the chain, and yields an HttpResponse instead of the expected coroutine). The spec view's abstract postcondition (result = assemble init stages ∧ consistent base ⇒ consistent result) and the 'declined stage leaves the pipeline exactly as it was' prose describe CORRECT behaviour without disclosing the gold's mechanism (rename adapt output to a fresh local + commit to the loop-carried handler only in the no-exception else: branch). It reveals nothing about the gold patch beyond what the public problem_statement already provides. CONCLUSION: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
