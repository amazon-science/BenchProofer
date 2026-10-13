# P2 adversarial audit — astropy__astropy-14995

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK1 prepatch bug: self-only mask errors instead of copying.
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok none
+    | none,    some om => return   .ok (some om)
+    | some _,  none => return     .error ()
+    | some sm, some om => return  .ok (some (hm sm om))
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK2: self-only mask returns no mask (drops self's mask).
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok none
+    | none,    some om => return   .ok (some om)
+    | some _,  none => return     .ok none
+    | some sm, some om => return  .ok (some (hm sm om))
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK3: both-mask arm swaps combine arg order (hm om sm).
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok none
+    | none,    some om => return   .ok (some om)
+    | some sm, none => return     .ok (some sm)
+    | some sm, some om => return  .ok (some (hm om sm))
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK4: neither-mask arm invents an empty mask instead of none.
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok (some [])
+    | none,    some om => return   .ok (some om)
+    | some sm, none => return     .ok (some sm)
+    | some sm, some om => return  .ok (some (hm sm om))
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,16 +66,14 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK5: no-combine branch invents an empty mask instead of none.
   match handleMask with
-  | none => return .ok none
+  | none => return .ok (some [])
   | some hm =>
     match selfMask, operandMask with
     | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
     | none,    some om => return .ok (some om)
     | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
     | some sm, some om => return .ok (some (hm sm om))
 -- impl-end
 
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK6: both-mask arm ignores the combine fn, returns self's mask.
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok none
+    | none,    some om => return   .ok (some om)
+    | some sm, none => return     .ok (some sm)
+    | some sm, some om => return  .ok (some sm)
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,15 @@
 def implementation_maskPropagation
     (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
     Except Unit (Option Mask) := Id.run do
-  -- No combining requested, or neither operand carries a mask: no result mask.
+  -- ATK7: operand-only mask arm drops the operand's mask.
   match handleMask with
   | none => return .ok none
   | some hm =>
     match selfMask, operandMask with
-    | none,    none    => return .ok none
-    -- Exactly one operand carries a mask: copy it over unchanged.
-    | none,    some om => return .ok (some om)
-    | some sm, none    => return .ok (some sm)
-    -- Both operands carry a mask: merge them with the combining function.
-    | some sm, some om => return .ok (some (hm sm om))
+    | none,    none => return     .ok none
+    | none,    some _ => return   .ok none
+    | some sm, none => return     .ok (some sm)
+    | some sm, some om => return  .ok (some (hm sm om))
 -- impl-end
 
 -- proof-start
@@ -85,11 +83,7 @@
       problem_spec_maskPropagation selfMask operandMask handleMask
         (implementation_maskPropagation selfMask operandMask handleMask) := by
   intro selfMask operandMask handleMask
-  unfold problem_spec_maskPropagation implementation_maskPropagation
-  cases handleMask with
-  | none => rfl
-  | some hm =>
-    cases selfMask with
-    | none => cases operandMask <;> rfl
-    | some sm => cases operandMask <;> rfl
+  simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]
+  cases handleMask <;> cases selfMask <;> cases operandMask <;>
+    first | rfl | simp_all | (try decide) | aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the masks of two operands during array arithmetic.

When an arithmetic operation is performed between two array-like operands, the
result's mask is derived from the operands' masks. Each operand may or may not
carry a mask, and the caller may optionally supply a function that merges two
masks together (e.g. an element-wise bitwise/logical combination).

The desired behaviour:

  * if no combining function is supplied, or NEITHER operand carries a mask, the
    result carries no mask;
  * if exactly one operand carries a mask, that mask is copied over to the
    result unchanged — the combining function is not consulted;
  * if BOTH operands carry a mask, the result is the combining function applied
    to the two masks.

In particular, when one operand lacks a mask the mask that does exist is simply
propagated to the result; the combining function is never asked to merge an
existing mask with a missing one. (This is the behaviour the issue's
"Expected behavior" section asks for.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The combining
-- function is an explicit input (a parameter of the modeled routine), and the
-- mask-propagation decision is modeled structurally over the observable inputs
-- (whether each operand carries a mask, whether a combining function was
-- supplied). No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A mask is modeled as the (flattened) integer bitmask grid of an operand;
`none` denotes an operand that carries no mask. The combining function is the
optional mask-merging callback the caller may supply (e.g. an element-wise
bitwise-or); `none` denotes that no combining was requested. The result is
either the produced mask (`some`/`none`) or an error, modeling the situation in
which the merge cannot be carried out. -/
abbrev Mask := List Int
abbrev Combine := Mask → Mask → Mask
-- pure-end

-- post-conditions-start
/-- The mask carried by the result of the operation, as a function of the two
operands' masks and the optional combining function. An error result models a
failed merge (the combining callback cannot run on a missing operand mask); a
correct propagation never errors in this domain. -/
def problem_spec_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine)
    (result : Except Unit (Option Mask)) : Prop :=
  result =
    (match handleMask with
     | none => .ok none
     | some hm =>
       match selfMask, operandMask with
       | none,    none    => .ok none
       | none,    some om => .ok (some om)
       | some sm, none    => .ok (some sm)
       | some sm, some om => .ok (some (hm sm om)))
-- post-conditions-end

-- impl-start
def implementation_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
    Except Unit (Option Mask) := Id.run do
  -- No combining requested, or neither operand carries a mask: no result mask.
  match handleMask with
  | none => return .ok none
  | some hm =>
    match selfMask, operandMask with
    | none,    none    => return .ok none
    -- Exactly one operand carries a mask: copy it over unchanged.
    | none,    some om => return .ok (some om)
    | some sm, none    => return .ok (some sm)
    -- Both operands carry a mask: merge them with the combining function.
    | some sm, some om => return .ok (some (hm sm om))
-- impl-end

-- proof-start
theorem correct_maskPropagation :
    ∀ (selfMask operandMask : Option Mask) (handleMask : Option Combine),
      problem_spec_maskPropagation selfMask operandMask handleMask
        (implementation_maskPropagation selfMask operandMask handleMask) := by
  intro selfMask operandMask handleMask
  unfold problem_spec_maskPropagation implementation_maskPropagation
  cases handleMask with
  | none => rfl
  | some hm =>
    cases selfMask with
    | none => cases operandMask <;> rfl
    | some sm => cases operandMask <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for astropy__astropy-14995 (lean). Spec problem_spec_maskPropagation is a TOTAL FUNCTIONAL EQUATION: result = <closed-form match over handleMask, selfMask, operandMask>. This pins result to exactly one value per input triple, so any impl whose correct_ closes is extensionally forced equal to gold on every arm (incl. the discriminating `some sm, none => .ok (some sm)` fix arm). No closing-but-non-resolving impl can exist.

Same_spec=True verified for all 7 attacks + positive control via swebench_unified.markers.same_spec (impl region only differs; axioms/pure/pre/post byte-identical).

Attacks (7 DISTINCT wrong-impl classes, each given a STRONG closing attempt: `simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]; cases handleMask <;> cases selfMask <;> cases operandMask <;> first | rfl | simp_all | (try decide) | aesop`):
- atk_1 (boundary / PREPATCH BUG): some _,none => .error ()  -> lean_verify exit 1 (unsolved goals @ line 84, proof tactic)
- atk_2 (partial-domain): some _,none => .ok none (drops self mask) -> exit 1
- atk_3 (control-flow-effect): some sm,some om => .ok (some (hm om sm)) swapped combine args -> exit 1
- atk_4 (ungrounded-oracle echo): none,none => .ok (some []) -> exit 1
- atk_5 (boundary): handleMask=none => .ok (some []) -> exit 1
- atk_6: both-mask arm ignores combine, => .ok (some sm) -> exit 1
- atk_7: none,some _ => .ok none (drops operand mask) -> exit 1
All 7 fail with genuine 'error: unsolved goals' at the proof tactic (verified via grep of lean_verify output), NOT syntax errors. Command each: `bash scripts/lean_verify.sh <path>` from project root. Verifications run concurrently in two batches of <=4.

Because NO wrong impl produced a closing clean-axiom proof, there is no verifying attack to materialize/resolve; step-2 resolve runs are vacuous (patches={}). verify=>correct holds.

Positive control (gold Solution.lean): `lean_verify.sh positive_control.lean` -> exit 0. `#print axioms correct_maskPropagation` (appended in pos_axcheck.lean) -> "'correct_maskPropagation' does not depend on any axioms" (clean, no sorryAx).

prepatch_reproduced=True: atk_1 re-encodes the prepatch bug (.error () on self-only mask) and correctly FAILS to verify against the frozen post-patch spec (exit 1), confirming the spec discriminates the bug.

refinement.md audit: all 5 legs are R (type refinement over observable inputs). Axioms region is EMPTY; there are NO A-consumed / A-reference / kind-3 legs, so no A-correspondence to the real callee to falsify. Empty-axioms justification is sound: the changed mask-propagation decision is modeled deeply/structurally (per-operand mask present/absent, combine supplied/not) and handle_mask is an explicit input the spec quantifies over (SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision). mapping.md symbol binding (_arithmetic_mask, self.mask/operand.mask/handle_mask) and the two-operand-domain deadness of `operand is None` are consistent with the model.

Verdict: SOUND. Spec is a total functional pin; >=5 (7) distinct wrong impls, all fail to verify; positive control verifies with clean axioms; no A-legs to break; verify=>correct not falsifiable here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the masks of two operands during array arithmetic.

When an arithmetic operation is performed between two array-like operands, the
result's mask is derived from the operands' masks. Each operand may or may not
carry a mask, and the caller may optionally supply a function that merges two
masks together (e.g. an element-wise bitwise/logical combination).

The desired behaviour:

  * if no combining function is supplied, or NEITHER operand carries a mask, the
    result carries no mask;
  * if exactly one operand carries a mask, that mask is copied over to the
    result unchanged — the combining function is not consulted;
  * if BOTH operands carry a mask, the result is the combining function applied
    to the two masks.

In particular, when one operand lacks a mask the mask that does exist is simply
propagated to the result; the combining function is never asked to merge an
existing mask with a missing one. (This is the behaviour the issue's
"Expected behavior" section asks for.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The combining
-- function is an explicit input (a parameter of the modeled routine), and the
-- mask-propagation decision is modeled structurally over the observable inputs
-- (whether each operand carries a mask, whether a combining function was
-- supplied). No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A mask is modeled as the (flattened) integer bitmask grid of an operand;
`none` denotes an operand that carries no mask. The combining function is the
optional mask-merging callback the caller may supply (e.g. an element-wise
bitwise-or); `none` denotes that no combining was requested. The result is
either the produced mask (`some`/`none`) or an error, modeling the situation in
which the merge cannot be carried out. -/
abbrev Mask := List Int
abbrev Combine := Mask → Mask → Mask
-- pure-end

-- post-conditions-start
/-- The mask carried by the result of the operation, as a function of the two
operands' masks and the optional combining function. An error result models a
failed merge (the combining callback cannot run on a missing operand mask); a
correct propagation never errors in this domain. -/
def problem_spec_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine)
    (result : Except Unit (Option Mask)) : Prop :=
  result =
    (match handleMask with
     | none => .ok none
     | some hm =>
       match selfMask, operandMask with
       | none,    none    => .ok none
       | none,    some om => .ok (some om)
       | some sm, none    => .ok (some sm)
       | some sm, some om => .ok (some (hm sm om)))
-- post-conditions-end

-- impl-start
def implementation_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
    Except Unit (Option Mask) := Id.run do
  -- No combining requested, or neither operand carries a mask: no result mask.
  match handleMask with
  | none => return .ok none
  | some hm =>
    match selfMask, operandMask with
    | none,    none    => return .ok none
    -- Exactly one operand carries a mask: copy it over unchanged.
    | none,    some om => return .ok (some om)
    | some sm, none    => return .ok (some sm)
    -- Both operands carry a mask: merge them with the combining function.
    | some sm, some om => return .ok (some (hm sm om))
-- impl-end

-- proof-start
theorem correct_maskPropagation :
    ∀ (selfMask operandMask : Option Mask) (handleMask : Option Combine),
      problem_spec_maskPropagation selfMask operandMask handleMask
        (implementation_maskPropagation selfMask operandMask handleMask) := by
  intro selfMask operandMask handleMask
  unfold problem_spec_maskPropagation implementation_maskPropagation
  cases handleMask with
  | none => rfl
  | some hm =>
    cases selfMask with
    | none => cases operandMask <;> rfl
    | some sm => cases operandMask <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for astropy__astropy-14995 (lean). Spec problem_spec_maskPropagation is a TOTAL FUNCTIONAL EQUATION: result = <closed-form match over handleMask, selfMask, operandMask>. This pins result to exactly one value per input triple, so any impl whose correct_ closes is extensionally forced equal to gold on every arm (incl. the discriminating `some sm, none => .ok (some sm)` fix arm). No closing-but-non-resolving impl can exist.

Same_spec=True verified for all 7 attacks + positive control via swebench_unified.markers.same_spec (impl region only differs; axioms/pure/pre/post byte-identical).

Attacks (7 DISTINCT wrong-impl classes, each given a STRONG closing attempt: `simp only [problem_spec_maskPropagation, implementation_maskPropagation, Id.run, pure, bind]; cases handleMask <;> cases selfMask <;> cases operandMask <;> first | rfl | simp_all | (try decide) | aesop`):
- atk_1 (boundary / PREPATCH BUG): some _,none => .error ()  -> lean_verify exit 1 (unsolved goals @ line 84, proof tactic)
- atk_2 (partial-domain): some _,none => .ok none (drops self mask) -> exit 1
- atk_3 (control-flow-effect): some sm,some om => .ok (some (hm om sm)) swapped combine args -> exit 1
- atk_4 (ungrounded-oracle echo): none,none => .ok (some []) -> exit 1
- atk_5 (boundary): handleMask=none => .ok (some []) -> exit 1
- atk_6: both-mask arm ignores combine, => .ok (some sm) -> exit 1
- atk_7: none,some _ => .ok none (drops operand mask) -> exit 1
All 7 fail with genuine 'error: unsolved goals' at the proof tactic (verified via grep of lean_verify output), NOT syntax errors. Command each: `bash scripts/lean_verify.sh <path>` from project root. Verifications run concurrently in two batches of <=4.

Because NO wrong impl produced a closing clean-axiom proof, there is no verifying attack to materialize/resolve; step-2 resolve runs are vacuous (patches={}). verify=>correct holds.

Positive control (gold Solution.lean): `lean_verify.sh positive_control.lean` -> exit 0. `#print axioms correct_maskPropagation` (appended in pos_axcheck.lean) -> "'correct_maskPropagation' does not depend on any axioms" (clean, no sorryAx).

prepatch_reproduced=True: atk_1 re-encodes the prepatch bug (.error () on self-only mask) and correctly FAILS to verify against the frozen post-patch spec (exit 1), confirming the spec discriminates the bug.

refinement.md audit: all 5 legs are R (type refinement over observable inputs). Axioms region is EMPTY; there are NO A-consumed / A-reference / kind-3 legs, so no A-correspondence to the real callee to falsify. Empty-axioms justification is sound: the changed mask-propagation decision is modeled deeply/structurally (per-operand mask present/absent, combine supplied/not) and handle_mask is an explicit input the spec quantifies over (SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision). mapping.md symbol binding (_arithmetic_mask, self.mask/operand.mask/handle_mask) and the two-operand-domain deadness of `operand is None` are consistent with the model.

Verdict: SOUND. Spec is a total functional pin; >=5 (7) distinct wrong impls, all fail to verify; positive control verifies with clean axioms; no A-legs to break; verify=>correct not falsifiable here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. The spec problem_spec_maskPropagation models _arithmetic_mask in the two-operand domain (operand always present — the real call path; mapping.md/refinement.md correct). Compared spec against the POST-PATCH real callee (gold commit 39310ebc3e: `elif operand is None:` -> `elif operand.mask is None:`) over all 8 combinations of (selfMask present/absent, operandMask present/absent, handleMask some/none): all agree. handleMask is universally quantified over Combine=Mask->Mask->Mask (an explicit input param, not an axiomatized callee), so the both-present case `.ok (some (hm sm om))` faithfully abstracts handle_mask(self.mask, operand.mask) for any merge fn. The spec never emits .error() (only the pre-patch variant does), matching the post-patch code which never crashes in this domain. Verified: (1) spec region (post-conditions/pure/axioms) byte-identical between Solution.lean and Solution_prepatch.lean — only impl differs; (2) Lean compiles exit 0, no sorry; (3) #print axioms correct_maskPropagation -> 'does not depend on any axioms' (no sorryAx, genuine proof); (4) conformance_check.py: 120010 inputs, 0 disagreements vs faithful post-patch oracle; (5) G-AX skip justified. The modeling-domain restriction (operand present) is legitimate: the `operand is None` branch is provably dead on this call path (collapse path does not invoke _arithmetic_mask), so it is not a hidden input the spec ignores. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view extracted mechanically via markers.spec_view(Solution.lean, lean backend): contains only the doc comment, empty axioms note, pure region (Mask/Combine abbrevs), and post-conditions (the functional equation). Impl and proof regions are correctly elided. same_spec(Solution.lean, Solution_prepatch.lean, lean) == True (spec region byte-identical). lean_verify.sh Solution.lean => exit 0.

Gold edit = branch condition `elif operand is None:` -> `elif operand.mask is None:` in NDArithmeticMixin._arithmetic_mask (plus a cosmetic 'lets'->"let's" comment typo fix). The exact Python lines appear ONLY in hints_text (chris-simpson/bmorris3 quote `elif operand.mask is None: return deepcopy(self.mask)` verbatim and link the culprit commit) -- hints_text is excluded from the leakage baseline.

Spec view encodes 3 behaviors: (a) no combining fn or neither operand has a mask => no result mask; (b) exactly one operand has a mask => copy it over unchanged; (c) both have masks => merge via the combining function. Each is present in the PUBLIC problem_statement: the 'Expected behavior' section states verbatim 'When one of the operand does not have mask, the mask that exists should just be copied over to the output'; the reproduction block enumerates nomask*nomask (no mask, 'OK'), mask*mask with handle_mask=np.bitwise_or (returns merged array), and mask*nomask (the TypeError being fixed, whose expected result is the copy-over of (b)).

The spec view never mentions Python, `operand is None`, `operand.mask`, `deepcopy`, `_arithmetic_mask`, or any branch/line structure -- it exposes no code-level detail of the gold edit beyond what problem_statement already states behaviorally. The doc comment's reference to 'the issue's Expected behavior section' points at the public problem_statement, not the hints. The handle_mask=None => no-mask arm is unchanged pre/post-patch and cannot leak the fix. Conclusion: faithful translation of publicly-stated expected behavior, no gold-reconstruction leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
