# P2 adversarial audit — astropy__astropy-13977

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_dispatchOp is a TOTAL FUNCTIONAL EQUALITY: `result = (match inner with | completes r => value r | fails => if operands.all (·.defersToDefault) then surfacedError else unhandled)`. Because it pins `result` by equality to a complete total function of the inputs, ANY implementation that closes correct_dispatchOp is provably pointwise-identical to the gold I/O relation on every input. Therefore no same-spec wrong impl can close the proof, and there is no verifying impl whose faithful patch could fail to resolve. Discriminating input for the prepatch bug: inner=fails, operands=[⟨false⟩] (some operand overrides) — spec demands `unhandled`, the always-surfacedError impl gives `surfacedError`; goal is false and rfl/simp fail.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,12 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
       return Result.value r
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
-      let mut allDefer := true
-      for o in operands do
-        allDefer := allDefer && o.defersToDefault
-      if allDefer then
-        return Result.surfacedError
-      else
-        return Result.unhandled
+      return Result.surfacedError
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +96,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,18 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
       return Result.value r
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
       let mut allDefer := true
       for o in operands do
         allDefer := allDefer && o.defersToDefault
       if allDefer then
+        return Result.unhandled
+      else
         return Result.surfacedError
-      else
-        return Result.unhandled
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +102,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,15 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
       return Result.value r
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
-      let mut allDefer := true
-      for o in operands do
-        allDefer := allDefer && o.defersToDefault
-      if allDefer then
+      if operands.any (·.defersToDefault) then
         return Result.surfacedError
       else
         return Result.unhandled
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +99,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,13 +82,10 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
       return Result.value r
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
       let mut allDefer := true
-      for o in operands do
+      for o in operands.dropLast do
         allDefer := allDefer && o.defersToDefault
       if allDefer then
         return Result.surfacedError
@@ -97,18 +94,6 @@
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +102,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,15 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
-      return Result.value r
+      return Result.unhandled
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
-      let mut allDefer := true
-      for o in operands do
-        allDefer := allDefer && o.defersToDefault
-      if allDefer then
+      if operands.all (·.defersToDefault) then
         return Result.surfacedError
       else
         return Result.unhandled
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +99,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,12 @@
     (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
   match inner with
   | Outcome.completes r =>
-      -- The evaluation completed: hand its value back unchanged.
       return Result.value r
   | Outcome.fails =>
-      -- The evaluation failed. Surface the error only when every operand
-      -- defers to the default handling; otherwise let another operand try.
-      let mut allDefer := true
-      for o in operands do
-        allDefer := allDefer && o.defersToDefault
-      if allDefer then
-        return Result.surfacedError
-      else
-        return Result.unhandled
+      return Result.unhandled
 -- impl-end
 
 -- proof-start
-
-theorem helper (operands : List Operand) (init : Bool) :
-    (forIn operands init (fun (o:Operand) r =>
-      ForInStep.yield (r && o.defersToDefault)) : Id Bool) = (init && operands.all (·.defersToDefault)) := by
-  induction operands generalizing init with
-  | nil => simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.all_cons, Bool.and_assoc]
-
 theorem correct_dispatchOp {α : Type} :
     ∀ (inner : Outcome α) (operands : List Operand),
       problem_spec_dispatchOp inner operands
@@ -117,9 +96,5 @@
   unfold problem_spec_dispatchOp implementation_dispatchOp
   cases inner with
   | completes r => rfl
-  | fails =>
-    simp only [Id.run, bind, pure]
-    have hall : (forIn operands true (fun (o:Operand) r => ForInStep.yield (r && o.defersToDefault)) : Id Bool)
-        = operands.all (·.defersToDefault) := by rw [helper]; simp
-    rw [hall]
+  | fails => simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Behavior of a unit-aware numeric operation's dispatch protocol when it is asked
to combine a unit-carrying value with one or more operands.

A single evaluation of the operation has one of two outcomes:

* it COMPLETES, producing some return value (a unit-carrying result, a plain
  value for comparisons, the "no value" result, or the "unhandled" sentinel);
* it FAILS to make sense of its operands (a type / value mismatch).

The protocol's contract is:

* When the evaluation completes, its return value is handed back unchanged.
* When the evaluation fails, the operation reports the "unhandled" sentinel —
  so that an operand able to handle the request itself may be tried instead —
  UNLESS every operand defers to the default handling (i.e. none of them
  supplies its own handler), in which case the original failure is surfaced.

Stated as an input→output relation on (evaluation outcome, operands) ↦ result.
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract: the evaluation outcome and
-- each operand's "defers to default handling" status are taken as the modeled
-- inputs (their production by the underlying numeric machinery is unchanged by
-- this behavior and is exercised end-to-end by the differential check), so there
-- is no `axiom <callee>_prop` for the proof to consume.

/-- One operand of the operation, abstracted to the only property this behavior
observes: whether it defers to the default handling (`true`) or supplies its own
handler (`false`). The operand list models the inputs together with any
preallocated outputs. -/
structure Operand where
  defersToDefault : Bool
deriving DecidableEq, Repr

/-- The outcome of a single evaluation of the operation:
* `completes r` — the evaluation finished and would return the value `r`;
* `fails`       — the evaluation could not make sense of its operands. -/
inductive Outcome (α : Type)
  | completes : α → Outcome α
  | fails : Outcome α
deriving Repr

/-- What the operation hands back:
* `value r`        — the completed evaluation's return value, unchanged;
* `unhandled`      — the "unhandled" sentinel (defer to another operand);
* `surfacedError`  — the original failure is surfaced. -/
inductive Result (α : Type)
  | value : α → Result α
  | unhandled : Result α
  | surfacedError : Result α
deriving Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers required)
-- pure-end

-- post-conditions-start
/-- The operation's result as a function of the evaluation outcome and the
operand list:
* a completed evaluation hands back its value unchanged;
* a failed evaluation surfaces the error only when every operand defers to the
  default handling; otherwise it reports the "unhandled" sentinel. -/
def problem_spec_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) (result : Result α) : Prop :=
  result = (match inner with
    | Outcome.completes r => Result.value r
    | Outcome.fails =>
        if operands.all (·.defersToDefault)
        then Result.surfacedError
        else Result.unhandled)
-- post-conditions-end

-- impl-start
def implementation_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) : Result α :=
  match inner with
  | Outcome.completes r => Result.value r
  | Outcome.fails =>
      if operands.all (·.defersToDefault) then Result.surfacedError
      else Result.unhandled
-- impl-end

-- proof-start
theorem correct_dispatchOp {α : Type} :
    ∀ (inner : Outcome α) (operands : List Operand),
      problem_spec_dispatchOp inner operands
        (implementation_dispatchOp inner operands) := by
  intro inner operands
  unfold problem_spec_dispatchOp implementation_dispatchOp
  cases inner with
  | completes r => rfl
  | fails => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all; same_spec confirmed True for all 7 files via swebench_unified.markers.same_spec against bundle Solution.lean).

SAME-SPEC: built by copying Solution.lean and editing ONLY the impl+proof regions; axioms/pure/pre/post byte-identical. same_spec=True for atk_1..6 and atk_pos.

ATTACKS (cmd: `bash scripts/lean_verify.sh <file>` from project root; 0=verifies, 1=error, 3=sorry). Run concurrently in 2 background batches of ≤4:
- atk_1 (PREPATCH BUG: fails=>surfacedError unconditionally): exit 1, line 99 'unsolved goals'. Reproduces prepatch bug (matches Solution_prepatch.lean). PREPATCH REPRODUCED=true.
- atk_2 (CONTROL-FLOW-EFFECT: inverted condition, allDefer=>unhandled else surfacedError): exit 1, unsolved goal `(if ... then pure surfacedError else pure unhandled).run = if ∀... then surfacedError else unhandled` — false.
- atk_3 (BOUNDARY: `operands.any` instead of `all`): exit 1, unsolved goal `if ∃ x∈operands, defers then surfacedError else unhandled = if ∀ x∈operands, defers then ...` — false for mixed operand lists.
- atk_4 (CONTROL-FLOW-EFFECT / off-by-one: fold over operands.dropLast): exit 1, unsolved goal quantifies foldl over dropLast vs ∀ over full list — false when the dropped last operand is the sole non-deferrer.
- atk_5 (WRONG PASSTHROUGH: completes r => unhandled): exit 1, line 101 rfl failed on completes branch (value r vs unhandled) — partial-domain wrong.
- atk_6 (UNGROUNDED-ORACLE ECHO: fails=>unhandled unconditionally): exit 1, line 99 unsolved goals — false when all operands defer (spec demands surfacedError).
All 6 errors are GENUINELY FALSE GOALS (equalities that do not hold for discriminating inputs), NOT tactic weakness — the spec is an equality to a total function, so any impl differing on any input fails definitionally.

POSITIVE CONTROL: atk_pos.lean is a genuinely DIFFERENT but extensionally-equivalent impl (pure match/if, no Id.run do-block, closed with `cases inner <;> rfl`). exit 0 (verifies, no sorry). `#print axioms correct_dispatchOp` (via atk_pos_ax.lean appended) => 'correct_dispatchOp does not depend on any axioms' — CLEAN, no sorryAx, no custom axioms.

NO RESOLVE RUNS REQUIRED: protocol step 2 mandates resolve only for wrong impls whose proof CLOSES with clean axioms. Zero such impls exist (all 6 fail to verify), so patches={} and no run_resolve invocation is needed. This is not a coverage gap — it is the direct consequence of the spec being a total functional pin.

REFINEMENT.MD AUDIT: all 5 legs tagged R (type refinement), no kind-3 (changed-inexpressible), no A-consumed, no A-reference, no I beyond structural control flow. The A-legs are VACUOUS: the axioms region declares only data structures (Operand/Outcome/Result) with NO `axiom <callee>_prop`, and the machine confirms `correct_dispatchOp does not depend on any axioms`. mapping.md's provenance rationale — the unchanged try-body callees (converters_and_unit, check_output, super().__array_ufunc__, _result_as_quantity, _to_own_unit) have their composite outcome taken as the modeled input `inner : Outcome α` rather than axiomatized — is legitimate: the patch only RELOCATES those callees under a try (does not alter them), the proof never reasons about how the body produces its outcome (only about what the wrapper does with it), and G-CONF (conf_skip=false) drives the real patched wrapper end-to-end.

Model↔patch correspondence holds: completes r↔try-body returns r (value passthrough, lines 643-682 relocated); fails↔except(TypeError,ValueError); operands.all(·.defersToDefault)↔all(getattr(type(io),'__array_ufunc__',None) in ignored_ufunc for io in inputs_and_outputs); surfacedError↔`raise e`; unhandled↔`return NotImplemented`. Empty-operands boundary matches: Python all([])=True → re-raise ↔ Lean [].all=true → surfacedError.

VERDICT: SOUND. ≥5 distinct wrong impls (6) attacked; prepatch reproduced; positive control verifies clean-axiom; none of the wrong impls verifies, so verify⇒correct is not falsified for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_dispatchOp is a TOTAL FUNCTIONAL EQUALITY: `result = (match inner with | completes r => value r | fails => if operands.all (·.defersToDefault) then surfacedError else unhandled)`. Because it pins `result` by equality to a complete total function of the inputs, ANY implementation that closes correct_dispatchOp is provably pointwise-identical to the gold I/O relation on every input. Therefore no same-spec wrong impl can close the proof, and there is no verifying impl whose faithful patch could fail to resolve. Discriminating input for the prepatch bug: inner=fails, operands=[⟨false⟩] (some operand overrides) — spec demands `unhandled`, the always-surfacedError impl gives `surfacedError`; goal is false and rfl/simp fail.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Behavior of a unit-aware numeric operation's dispatch protocol when it is asked
to combine a unit-carrying value with one or more operands.

A single evaluation of the operation has one of two outcomes:

* it COMPLETES, producing some return value (a unit-carrying result, a plain
  value for comparisons, the "no value" result, or the "unhandled" sentinel);
* it FAILS to make sense of its operands (a type / value mismatch).

The protocol's contract is:

* When the evaluation completes, its return value is handed back unchanged.
* When the evaluation fails, the operation reports the "unhandled" sentinel —
  so that an operand able to handle the request itself may be tried instead —
  UNLESS every operand defers to the default handling (i.e. none of them
  supplies its own handler), in which case the original failure is surfaced.

Stated as an input→output relation on (evaluation outcome, operands) ↦ result.
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract: the evaluation outcome and
-- each operand's "defers to default handling" status are taken as the modeled
-- inputs (their production by the underlying numeric machinery is unchanged by
-- this behavior and is exercised end-to-end by the differential check), so there
-- is no `axiom <callee>_prop` for the proof to consume.

/-- One operand of the operation, abstracted to the only property this behavior
observes: whether it defers to the default handling (`true`) or supplies its own
handler (`false`). The operand list models the inputs together with any
preallocated outputs. -/
structure Operand where
  defersToDefault : Bool
deriving DecidableEq, Repr

/-- The outcome of a single evaluation of the operation:
* `completes r` — the evaluation finished and would return the value `r`;
* `fails`       — the evaluation could not make sense of its operands. -/
inductive Outcome (α : Type)
  | completes : α → Outcome α
  | fails : Outcome α
deriving Repr

/-- What the operation hands back:
* `value r`        — the completed evaluation's return value, unchanged;
* `unhandled`      — the "unhandled" sentinel (defer to another operand);
* `surfacedError`  — the original failure is surfaced. -/
inductive Result (α : Type)
  | value : α → Result α
  | unhandled : Result α
  | surfacedError : Result α
deriving Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers required)
-- pure-end

-- post-conditions-start
/-- The operation's result as a function of the evaluation outcome and the
operand list:
* a completed evaluation hands back its value unchanged;
* a failed evaluation surfaces the error only when every operand defers to the
  default handling; otherwise it reports the "unhandled" sentinel. -/
def problem_spec_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) (result : Result α) : Prop :=
  result = (match inner with
    | Outcome.completes r => Result.value r
    | Outcome.fails =>
        if operands.all (·.defersToDefault)
        then Result.surfacedError
        else Result.unhandled)
-- post-conditions-end

-- impl-start
def implementation_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) : Result α :=
  match inner with
  | Outcome.completes r => Result.value r
  | Outcome.fails =>
      if operands.all (·.defersToDefault) then Result.surfacedError
      else Result.unhandled
-- impl-end

-- proof-start
theorem correct_dispatchOp {α : Type} :
    ∀ (inner : Outcome α) (operands : List Operand),
      problem_spec_dispatchOp inner operands
        (implementation_dispatchOp inner operands) := by
  intro inner operands
  unfold problem_spec_dispatchOp implementation_dispatchOp
  cases inner with
  | completes r => rfl
  | fails => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all; same_spec confirmed True for all 7 files via swebench_unified.markers.same_spec against bundle Solution.lean).

SAME-SPEC: built by copying Solution.lean and editing ONLY the impl+proof regions; axioms/pure/pre/post byte-identical. same_spec=True for atk_1..6 and atk_pos.

ATTACKS (cmd: `bash scripts/lean_verify.sh <file>` from project root; 0=verifies, 1=error, 3=sorry). Run concurrently in 2 background batches of ≤4:
- atk_1 (PREPATCH BUG: fails=>surfacedError unconditionally): exit 1, line 99 'unsolved goals'. Reproduces prepatch bug (matches Solution_prepatch.lean). PREPATCH REPRODUCED=true.
- atk_2 (CONTROL-FLOW-EFFECT: inverted condition, allDefer=>unhandled else surfacedError): exit 1, unsolved goal `(if ... then pure surfacedError else pure unhandled).run = if ∀... then surfacedError else unhandled` — false.
- atk_3 (BOUNDARY: `operands.any` instead of `all`): exit 1, unsolved goal `if ∃ x∈operands, defers then surfacedError else unhandled = if ∀ x∈operands, defers then ...` — false for mixed operand lists.
- atk_4 (CONTROL-FLOW-EFFECT / off-by-one: fold over operands.dropLast): exit 1, unsolved goal quantifies foldl over dropLast vs ∀ over full list — false when the dropped last operand is the sole non-deferrer.
- atk_5 (WRONG PASSTHROUGH: completes r => unhandled): exit 1, line 101 rfl failed on completes branch (value r vs unhandled) — partial-domain wrong.
- atk_6 (UNGROUNDED-ORACLE ECHO: fails=>unhandled unconditionally): exit 1, line 99 unsolved goals — false when all operands defer (spec demands surfacedError).
All 6 errors are GENUINELY FALSE GOALS (equalities that do not hold for discriminating inputs), NOT tactic weakness — the spec is an equality to a total function, so any impl differing on any input fails definitionally.

POSITIVE CONTROL: atk_pos.lean is a genuinely DIFFERENT but extensionally-equivalent impl (pure match/if, no Id.run do-block, closed with `cases inner <;> rfl`). exit 0 (verifies, no sorry). `#print axioms correct_dispatchOp` (via atk_pos_ax.lean appended) => 'correct_dispatchOp does not depend on any axioms' — CLEAN, no sorryAx, no custom axioms.

NO RESOLVE RUNS REQUIRED: protocol step 2 mandates resolve only for wrong impls whose proof CLOSES with clean axioms. Zero such impls exist (all 6 fail to verify), so patches={} and no run_resolve invocation is needed. This is not a coverage gap — it is the direct consequence of the spec being a total functional pin.

REFINEMENT.MD AUDIT: all 5 legs tagged R (type refinement), no kind-3 (changed-inexpressible), no A-consumed, no A-reference, no I beyond structural control flow. The A-legs are VACUOUS: the axioms region declares only data structures (Operand/Outcome/Result) with NO `axiom <callee>_prop`, and the machine confirms `correct_dispatchOp does not depend on any axioms`. mapping.md's provenance rationale — the unchanged try-body callees (converters_and_unit, check_output, super().__array_ufunc__, _result_as_quantity, _to_own_unit) have their composite outcome taken as the modeled input `inner : Outcome α` rather than axiomatized — is legitimate: the patch only RELOCATES those callees under a try (does not alter them), the proof never reasons about how the body produces its outcome (only about what the wrapper does with it), and G-CONF (conf_skip=false) drives the real patched wrapper end-to-end.

Model↔patch correspondence holds: completes r↔try-body returns r (value passthrough, lines 643-682 relocated); fails↔except(TypeError,ValueError); operands.all(·.defersToDefault)↔all(getattr(type(io),'__array_ufunc__',None) in ignored_ufunc for io in inputs_and_outputs); surfacedError↔`raise e`; unhandled↔`return NotImplemented`. Empty-operands boundary matches: Python all([])=True → re-raise ↔ Lean [].all=true → surfacedError.

VERDICT: SOUND. ≥5 distinct wrong impls (6) attacked; prepatch reproduced; positive control verifies clean-axiom; none of the wrong impls verifies, so verify⇒correct is not falsified for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified for astropy__astropy-13977 lean bundle (modeled fn: Quantity.__array_ufunc__ dispatch wrapper + error-recovery tail, gold patch, patch_equals_gold=True).

### SPEC/REAL AGREEMENT (checked every modeled input class against the postpatch gold behavior):
- inner=completes r  -> real: try-body returns r unchanged (`return result` / `_result_as_quantity(...)`); spec: Result.value r. AGREE (value-identity preserved; r opaque).
- inner=fails, operands.all defersToDefault  -> real: `else: raise e` (all io have __array_ufunc__ in ignored_ufunc); spec: Result.surfacedError. AGREE.
- inner=fails, NOT all defer  -> real: `if not all(...): return NotImplemented`; spec: Result.unhandled. AGREE (De Morgan: not all == exists non-deferring).
- empty operand list  -> Python all([])=True matches Lean List.all []=true; both -> surfacedError. AGREE.
- Distinction Result.value NotImplemented (body itself returned NotImplemented, unit-None/None/NotImplemented branch) vs Result.unhandled (recovery clause returned NotImplemented): both are observably NotImplemented at the wrapper boundary, so no divergence — value-identity abstraction is sound.

The spec takes the composite try-body outcome (returns-value vs raises TypeError/ValueError) as the modeled input `inner` — a legitimate R-refinement; the callees (converters_and_unit, check_output, super().__array_ufunc__, _result_as_quantity, _to_own_unit) are UNCHANGED by the patch, so no callee contract axiom is needed, and the 'how' is exercised end-to-end by G-CONF (conf_skip=false, all-R). The spec is neither too strong nor drifting: it is essentially the definitional model of the exact new control decision the patch introduces.

### Verification evidence
- same_spec(Solution_prepatch, Solution) = True via swebench_unified.markers with LeanBackend.language (spec region byte-identical, so no spec was smuggled into the impl/proof).
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/error).
- `#print axioms correct_dispatchOp` -> [propext, Quot.sound] only. No sorryAx, no custom/injected axioms — proof is genuine, not fake.
- Gold patch (reference lean-benchmarks-builder patch.diff) matches mapping.md line-for-line: try wraps lines 633-682, except (TypeError,ValueError) clause with ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__).

No diverging input exists; verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (imports + docstring + axioms/pure/post-conditions regions; impl & proof elided as 'supplied by the consumer') was computed via markers.spec_view over LeanBackend. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical), and mechanical leakage.screen passed with zero hard failures. The only distinctive changed symbol is 'array_ufunc'; it appears nowhere in the spec view. The spec view describes the behavior in fully abstract, edit-neutral terms (Outcome.completes/fails, Operand.defersToDefault, Result.value/unhandled/surfacedError, problem_spec_dispatchOp) with NO astropy-specific tokens: no __array_ufunc__, NotImplemented, TypeError/ValueError, Quantity, the file path astropy/units/quantity.py, no diff markers, and no try/except structural cue. Crucially, the target behavior itself is already public in problem_statement: the issue explicitly requests that __array_ufunc__ return NotImplemented instead of raising ValueError so __radd__ can be tried when an operand (duck type) supplies its own handler. The spec's tie-break clause ('surface the original failure only when every operand defers to default handling; otherwise report the unhandled sentinel') is the natural, abstractly-stated completion of that already-disclosed behavior and localizes no code edit. Nothing in the spec view reveals the gold edit beyond the public problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.