# P2 adversarial audit — scikit-learn__scikit-learn-13328

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,11 +89,8 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
+    let isObject : Bool := orig = DType.object
+    let out : DType := if isObject then DType.f64 else orig
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,12 +89,7 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
-    return out
+    return orig
     -- impl-end
 
 prove_correct validatedElementType by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,11 +89,7 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
+    let out : DType := if orig.isFloating then orig else DType.f64
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,12 +89,7 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
-    return out
+    return DType.f64
     -- impl-end
 
 prove_correct validatedElementType by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,11 +89,7 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
+    let out : DType := if orig.isAccepted then DType.f64 else orig
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,11 +89,13 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
+    let out : DType := match orig with
+      | DType.f64 => DType.f64
+      | DType.f32 => DType.f32
+      | DType.boolean => DType.f64
+      | DType.integer => DType.f64
+      | DType.f16 => DType.f16
+      | DType.object => DType.object
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -89,11 +89,7 @@
   ensures out.isFloating = true
   do
     -- impl-start
-    -- The requested element type is the floating accept-list {f64, f32}: an
-    -- input already carrying one of these is preserved; any other element type
-    -- is converted to the first accepted floating type.
-    let accepted : Bool := orig.isAccepted
-    let out : DType := if accepted then orig else DType.f64
+    let out : DType := if orig.isAccepted then orig else DType.f32
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   input-validation routine that resolves the element type of the training
   matrix — is modeled DEEPLY in the `pure` region (`resolveElemType`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3). It
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element type of a dense numeric matrix, abstracted to the categories the
   validation step distinguishes. `f64`/`f32` are the two floating element types
   that may be carried through unchanged; `f16` is a floating type that is NOT
   carried through; `boolean`, `integer`, `object` are non-floating element
   types (mapping.md §2 gives the bijection to the repository's element-type
   tags). -/
inductive DType where
  | f64
  | f32
  | f16
  | boolean
  | integer
  | object
  deriving DecidableEq

/- Whether an element type is a floating type. This is the property the desired
   behaviour must guarantee for the validated matrix: downstream numeric code
   (signed arithmetic on the matrix) is well-defined only on floating element
   types, so a non-floating input must not survive validation unconverted. -/
@[grind] def DType.isFloating : DType → Bool
  | .f64 => true
  | .f32 => true
  | .f16 => true
  | _    => false

/- The set of floating element types accepted *as-is* by the validation step:
   the two that are carried through unchanged when the input already has one of
   them. -/
@[grind] def DType.isAccepted : DType → Bool
  | .f64 => true
  | .f32 => true
  | _    => false

/- Deep model (A-reference, mapping.md §3.1) of the element-type resolution the
   validation routine performs when the requested element type is the floating
   accept-list {f64, f32}: an input element type that is already one of the
   accepted floating types is preserved; ANY other element type — floating or
   not — is converted to the first accepted floating type (`f64`). Validated
   == the real routine by axiom_check.py (G-AX). -/
@[grind] def resolveElemType (orig : DType) : DType :=
  if orig.isAccepted then orig else .f64

/- The resolved element type is always a floating type: an accepted input is
   already floating, and every other input is converted to `f64`. This is the
   guarantee the desired behaviour pins. -/
@[grind] lemma resolveElemType_isFloating (orig : DType) :
    (resolveElemType orig).isFloating = true := by
  cases orig <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The element type of the training matrix after the model's input-validation
   step. Desired behaviour: validation must hand downstream numeric code a
   matrix whose element type is a floating type, so that signed arithmetic on
   the matrix is well-defined for every supported input — in particular a
   non-floating input (e.g. a matrix of truth values) must be converted, not
   passed through. Concretely, an input whose element type is already one of the
   accepted floating types is kept; any other element type is converted to the
   default floating type.

   `orig` is read-only (not `mut`): the routine inspects the incoming element
   type and decides the validated element type; it does not mutate the input
   tag (directive 5). The result is pinned exactly by `resolveElemType` and is
   guaranteed floating by `resolveElemType_isFloating`. -/
method validatedElementType (orig : DType) return (out : DType)
  ensures out = resolveElemType orig
  ensures out.isFloating = true
  do
    -- impl-start
    let accepted : Bool := orig.isAccepted
    let out : DType := if accepted then orig else DType.f64
    return out
    -- impl-end

prove_correct validatedElementType by
  loom_solve
  cases orig <;> rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pointwise-deterministic. The postcondition `ensures out = resolveElemType orig` (plus `ensures out.isFloating = true`) pins the output as a TOTAL FUNCTION of the input, where resolveElemType orig = if orig.isAccepted then orig else .f64. This is the tightest possible G-EQ shape: any impl behaviorally distinct from resolveElemType on ANY DType is refuted at prove_correct. No behavioral wedge exists, so no verifying-wrong-impl can be produced and there is nothing to materialize/resolve.

 Each attack built by copying velvet/Solution.lean and editing ONLY the impl-start..impl-end region (axioms/pure/pre/post byte-identical). same_spec=True confirmed for ALL 8 files via swebench_unified.markers.same_spec with get_backend('velvet').language.

### RESULTS (exit 0=verifies, 1=proof error):
- pos_control (correct impl = Solution.lean body: if isAccepted then orig else f64): exit 0 — VERIFIES (positive control good).
- atk_1 PREPATCH-BUG reproduced (numeric policy: object->f64, else passthrough): exit 1 — fails `out.isFloating` on boolean/integer and `out=resolveElemType` (matches Solution_prepatch.lean semantics; prepatch_reproduced=true).
- atk_2 identity passthrough (return orig): exit 1 — fails on every non-accepted type.
- atk_3 floating-passthrough (if isFloating then orig else f64): exit 1 — fails on f16 (resolveElemType f16 = f64 but impl keeps f16).
- atk_4 constant f64 (return DType.f64): exit 1 — fails `out=resolveElemType` on f32 (should preserve f32).
- atk_5 inverted accept (accepted->f64, else passthrough): exit 1 — fails both obligations.
- atk_6 boundary/partial-domain match (boolean,integer->f64; f16,object passthrough): exit 1 — fails isFloating on object and =resolveElemType on f16/object.
- atk_7 wrong conversion target (non-accepted -> f32 instead of f64): exit 1 — fails `out=resolveElemType` (subtle: f32 is floating so isFloating passes, but the exact-equality postcondition catches it).

All 7 failures are genuine prove_correct postcondition proof errors (kernel: 'declaration has metavariables validatedElementType_correct' / `rfl` failed on the ensures goals), NOT build/infrastructure errors. Since NO wrong impl verifies, the patches map is empty and no run_resolve was required (verify⇏correct break is unreachable). Attack classes covered: prepatch-bug, partial-domain, boundary, control-flow/effect (identity, constant, inverted branch), wrong-target, and ungrounded-oracle echo (all pinned by the deterministic postcondition).

REFINEMENT.MD AUDIT: No kind-3 (inexpressible-changed-op) legs. A1/A2/A4 are R (+I), A3 is A-reference+I. The single A-leg (A3) models the UNCHANGED callee sklearn.utils.check_array's element-type resolution deeply as resolveElemType (NO consumed axiom). Correspondence is sound and grounded: check_array with a list dtype executes `if dtype_orig in dtype: dtype=None(preserve) else dtype=dtype[0](=float64)` (validation.py:459-466, conversion :496), which is exactly `if orig.isAccepted then orig else f64`. axiom_check.py (G-AX) executably validates resolveElemType == real check_array under dtype=[np.float64,np.float32] over all 6 DType categories (boundary, several shapes, 1-D path) + 4000 fuzz matrices, importing only numpy and the real sklearn.utils.check_array — a real reference check, not an ungrounded oracle echo. mapping.md §2 bijection is total and consistent (f64/f32/f16 floating; f64/f32 accepted; f16/boolean/integer/object handled). The discriminating content (non-accepted boolean/integer/f16 -> f64) is expressed in-model and exercised, and the prepatch skeleton fails on boolean AND integer AND f16 (>1 discriminating input).

VERDICT: SOUND — 7 distinct same-spec attacks encoded and verified, positive control verifies, none produced a verifying-wrong-impl, refinement.md is kind-3-free with a sound grounded A-reference.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   input-validation routine that resolves the element type of the training
   matrix — is modeled DEEPLY in the `pure` region (`resolveElemType`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3). It
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element type of a dense numeric matrix, abstracted to the categories the
   validation step distinguishes. `f64`/`f32` are the two floating element types
   that may be carried through unchanged; `f16` is a floating type that is NOT
   carried through; `boolean`, `integer`, `object` are non-floating element
   types (mapping.md §2 gives the bijection to the repository's element-type
   tags). -/
inductive DType where
  | f64
  | f32
  | f16
  | boolean
  | integer
  | object
  deriving DecidableEq

/- Whether an element type is a floating type. This is the property the desired
   behaviour must guarantee for the validated matrix: downstream numeric code
   (signed arithmetic on the matrix) is well-defined only on floating element
   types, so a non-floating input must not survive validation unconverted. -/
@[grind] def DType.isFloating : DType → Bool
  | .f64 => true
  | .f32 => true
  | .f16 => true
  | _    => false

/- The set of floating element types accepted *as-is* by the validation step:
   the two that are carried through unchanged when the input already has one of
   them. -/
@[grind] def DType.isAccepted : DType → Bool
  | .f64 => true
  | .f32 => true
  | _    => false

/- Deep model (A-reference, mapping.md §3.1) of the element-type resolution the
   validation routine performs when the requested element type is the floating
   accept-list {f64, f32}: an input element type that is already one of the
   accepted floating types is preserved; ANY other element type — floating or
   not — is converted to the first accepted floating type (`f64`). Validated
   == the real routine by axiom_check.py (G-AX). -/
@[grind] def resolveElemType (orig : DType) : DType :=
  if orig.isAccepted then orig else .f64

/- The resolved element type is always a floating type: an accepted input is
   already floating, and every other input is converted to `f64`. This is the
   guarantee the desired behaviour pins. -/
@[grind] lemma resolveElemType_isFloating (orig : DType) :
    (resolveElemType orig).isFloating = true := by
  cases orig <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The element type of the training matrix after the model's input-validation
   step. Desired behaviour: validation must hand downstream numeric code a
   matrix whose element type is a floating type, so that signed arithmetic on
   the matrix is well-defined for every supported input — in particular a
   non-floating input (e.g. a matrix of truth values) must be converted, not
   passed through. Concretely, an input whose element type is already one of the
   accepted floating types is kept; any other element type is converted to the
   default floating type.

   `orig` is read-only (not `mut`): the routine inspects the incoming element
   type and decides the validated element type; it does not mutate the input
   tag (directive 5). The result is pinned exactly by `resolveElemType` and is
   guaranteed floating by `resolveElemType_isFloating`. -/
method validatedElementType (orig : DType) return (out : DType)
  ensures out = resolveElemType orig
  ensures out.isFloating = true
  do
    -- impl-start
    let accepted : Bool := orig.isAccepted
    let out : DType := if accepted then orig else DType.f64
    return out
    -- impl-end

prove_correct validatedElementType by
  loom_solve
  cases orig <;> rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pointwise-deterministic. The postcondition `ensures out = resolveElemType orig` (plus `ensures out.isFloating = true`) pins the output as a TOTAL FUNCTION of the input, where resolveElemType orig = if orig.isAccepted then orig else .f64. This is the tightest possible G-EQ shape: any impl behaviorally distinct from resolveElemType on ANY DType is refuted at prove_correct. No behavioral wedge exists, so no verifying-wrong-impl can be produced and there is nothing to materialize/resolve.

 Each attack built by copying velvet/Solution.lean and editing ONLY the impl-start..impl-end region (axioms/pure/pre/post byte-identical). same_spec=True confirmed for ALL 8 files via swebench_unified.markers.same_spec with get_backend('velvet').language.

### RESULTS (exit 0=verifies, 1=proof error):
- pos_control (correct impl = Solution.lean body: if isAccepted then orig else f64): exit 0 — VERIFIES (positive control good).
- atk_1 PREPATCH-BUG reproduced (numeric policy: object->f64, else passthrough): exit 1 — fails `out.isFloating` on boolean/integer and `out=resolveElemType` (matches Solution_prepatch.lean semantics; prepatch_reproduced=true).
- atk_2 identity passthrough (return orig): exit 1 — fails on every non-accepted type.
- atk_3 floating-passthrough (if isFloating then orig else f64): exit 1 — fails on f16 (resolveElemType f16 = f64 but impl keeps f16).
- atk_4 constant f64 (return DType.f64): exit 1 — fails `out=resolveElemType` on f32 (should preserve f32).
- atk_5 inverted accept (accepted->f64, else passthrough): exit 1 — fails both obligations.
- atk_6 boundary/partial-domain match (boolean,integer->f64; f16,object passthrough): exit 1 — fails isFloating on object and =resolveElemType on f16/object.
- atk_7 wrong conversion target (non-accepted -> f32 instead of f64): exit 1 — fails `out=resolveElemType` (subtle: f32 is floating so isFloating passes, but the exact-equality postcondition catches it).

All 7 failures are genuine prove_correct postcondition proof errors (kernel: 'declaration has metavariables validatedElementType_correct' / `rfl` failed on the ensures goals), NOT build/infrastructure errors. Since NO wrong impl verifies, the patches map is empty and no run_resolve was required (verify⇏correct break is unreachable). Attack classes covered: prepatch-bug, partial-domain, boundary, control-flow/effect (identity, constant, inverted branch), wrong-target, and ungrounded-oracle echo (all pinned by the deterministic postcondition).

REFINEMENT.MD AUDIT: No kind-3 (inexpressible-changed-op) legs. A1/A2/A4 are R (+I), A3 is A-reference+I. The single A-leg (A3) models the UNCHANGED callee sklearn.utils.check_array's element-type resolution deeply as resolveElemType (NO consumed axiom). Correspondence is sound and grounded: check_array with a list dtype executes `if dtype_orig in dtype: dtype=None(preserve) else dtype=dtype[0](=float64)` (validation.py:459-466, conversion :496), which is exactly `if orig.isAccepted then orig else f64`. axiom_check.py (G-AX) executably validates resolveElemType == real check_array under dtype=[np.float64,np.float32] over all 6 DType categories (boundary, several shapes, 1-D path) + 4000 fuzz matrices, importing only numpy and the real sklearn.utils.check_array — a real reference check, not an ungrounded oracle echo. mapping.md §2 bijection is total and consistent (f64/f32/f16 floating; f64/f32 accepted; f16/boolean/integer/object handled). The discriminating content (non-accepted boolean/integer/f16 -> f64) is expressed in-model and exercised, and the prepatch skeleton fails on boolean AND integer AND f16 (>1 discriminating input).

VERDICT: SOUND — 7 distinct same-spec attacks encoded and verified, positive control verifies, none produced a verifying-wrong-impl, refinement.md is kind-3-free with a sound grounded A-reference.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check of the modeled function validatedElementType / resolveElemType against the real repo callee sklearn.utils.check_array (invoked via check_X_y with the gold-patch argument dtype=[np.float64, np.float32]) at base_commit 37b0e66c.

SPEC INTEGRITY: spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (velvet LanguageTables) => True. The postconditions are `out = resolveElemType orig` and `out.isFloating = true`, with resolveElemType orig = (if orig in {f64,f32} then orig else f64).

DIRECT EXECUTION against the real callee (sklearn 1.9.0, axenv), all six modeled DType categories, both check_array and the gold's actual check_X_y(..., dtype=[np.float64,np.float32]) path:
  f64 -> f64, f32 -> f32, f16 -> f64, boolean -> f64, integer -> f64, object(numeric) -> f64.
Model resolveElemType predicts exactly the same for every category. Zero divergence in the modeled domain. Second postcondition out.isFloating=true holds on every real output.

EDGE PROBING outside the modeled domain: complex dtype -> real callee RAISES 'Complex data not supported' (mapping.md §2 explicitly notes complex is rejected by _ensure_no_complex_data), uint8/int8/float128 -> f64 (all collapse into the modeled 'integer'/'floating-miss' behavior -> f64, consistent), object-of-strings -> raises (non-numeric, out of domain). None of these constitute a spec-too-strong disagreement: the spec makes no claim on inputs the real callee rejects, and every category it DOES model matches the real behavior.

The spec is NOT too strong / does not drift: the modeled function agrees with the real callee on every input in the modeled domain. Confirmed independently (not merely trusting recorded gates), though G-AX (36 boundary + 4000 fuzz), G-CONF (100024 inputs, 0 disagreements), and G-GOLD all pass and corroborate. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = markers.spec_view over Solution.lean (velvet tables): axioms/pure/pre/post regions + validatedElementType contract; impl/proof body elided. mapping.md and refinement.md (which quote the gold hunk 'dtype=[np.float64, np.float32]' and name check_X_y/check_array/huber.py) are auditor-only docs, NOT part of the screened consumer view. Verified: (1) spec region byte-identical to Solution_prepatch.lean via markers.same_spec = True; (2) mechanical leakage.screen (velvet/lean flavor) passes with zero hard failures — no diff markers, no >=8-char gold-patch line reproduced, no patched file path (sklearn/linear_model/huber.py) or dotted module, no spec-view identifier/comment echoing a patched repo symbol, no narration terms; (3) no relaxed_leakage flag / no RELAXED_LEAKAGE.md, so strict regime. Gold-reconstruction check: spec view is fully abstracted to a Lean DType inductive + validatedElementType method and exposes NO repo locators (no HuberRegressor, fit, check_X_y, dtype= kwarg, file path, or diff). The public problem_statement already reveals more repo detail (huber.py, the _huber_loss_and_gradient boolean-negative TypeError, and the expected 'convert boolean to float' fix). The spec's precision (accepted={f64,f32} preserved, else->f64, result must be floating) is legitimate behavioral specification of the desired outcome — it pins WHAT the validated element type must be, not the edit's location or mechanism (the added dtype=[np.float64,np.float32] argument). That does not exceed problem_statement in a way that reconstructs the gold edit. G-LEAK recorded pass, G-PANEL-3 recorded NO-LEAKAGE — concur.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
