# P2 adversarial audit — django__django-11999

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,8 +58,7 @@
   let mut result := attrs
   if hasChoices then
     let key := displayKey name
-    if !hasKey result key then
-      result := setKey result key display
+    result := setKey result key display
   return result
 -- impl-end
 
@@ -73,7 +72,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
   let mut result := attrs
   if hasChoices then
     let key := displayKey name
-    if !hasKey result key then
+    if hasKey result key then
       result := setKey result key display
   return result
 -- impl-end
@@ -73,7 +73,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
     (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
     Attrs := Id.run do
   let mut result := attrs
-  if hasChoices then
+  if !hasChoices then
     let key := displayKey name
     if !hasKey result key then
       result := setKey result key display
@@ -73,7 +73,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
     (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
     Attrs := Id.run do
   let mut result := attrs
-  if hasChoices then
+  if hasChoices && name != "" then
     let key := displayKey name
     if !hasKey result key then
       result := setKey result key display
@@ -73,7 +73,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,13 +54,8 @@
 -- impl-start
 def implementation_registerDisplay
     (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
-    Attrs := Id.run do
-  let mut result := attrs
-  if hasChoices then
-    let key := displayKey name
-    if !hasKey result key then
-      result := setKey result key display
-  return result
+    Attrs :=
+  attrs ++ [(displayKey name, display)]
 -- impl-end
 
 -- proof-start
@@ -73,7 +68,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,8 +58,7 @@
   let mut result := attrs
   if hasChoices then
     let key := displayKey name
-    if !hasKey result key then
-      result := setKey result key display
+    result := result ++ [(key, display)]
   return result
 -- impl-end
 
@@ -73,7 +72,5 @@
   simp only [Id.run]
   by_cases hc : hasChoices = true <;>
     by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>
-    simp only [hc, hk, Bool.not_true, Bool.not_false,
-      Bool.and_true, Bool.and_false, if_true] <;>
-    rfl
+    simp_all [hc, hk] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_echo.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The attribute-namespace
-- primitives (key presence test, key lookup, key assignment) and the accessor
-- key name are all modeled concretely below as plain functional helpers (R/I
-- ops), not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The attribute namespace of a class is modeled as an association list from
attribute name to a stored value (the value type is opaque to the modeled
behavior; here `Int` stands in for an arbitrary attribute value). Only key
presence and the stored value are observable. -/
abbrev Attrs := List (String × Int)

/-- The accessor name generated for a field: `get_<name>_display`. -/
def displayKey (name : String) : String := "get_" ++ name ++ "_display"

/-- Whether the namespace already binds `key`. -/
def hasKey (attrs : Attrs) (key : String) : Bool :=
  attrs.any (fun p => p.1 == key)

/-- Assign `key := v` in the namespace: replace an existing binding in place, or
append a new one. -/
def setKey (attrs : Attrs) (key : String) (v : Int) : Attrs :=
  if attrs.any (fun p => p.1 == key)
  then attrs.map (fun p => if p.1 == key then (key, v) else p)
  else attrs ++ [(key, v)]
-- pure-end

-- post-conditions-start
/-- Registering the generated display accessor for a field.

`attrs` is the class' attribute namespace, `name` the field name, `hasChoices`
whether the field carries an enumerated choice set, and `display` the generated
accessor value.

The whole namespace is pinned exactly: it is left untouched, EXCEPT in the one
case where the field carries a choice set AND the generated accessor name is not
already bound — there the accessor is appended. In particular, when the field has
a choice set but the accessor name is already bound (e.g. the class declares its
own accessor), the namespace is unchanged, so the existing binding is preserved.
The entire result is pinned to the input, leaving no output component
unconstrained. -/
def problem_spec_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int)
    (result : Attrs) : Prop :=
  let key := displayKey name
  result = (if hasChoices && !hasKey attrs key then attrs ++ [(key, display)] else attrs)
-- post-conditions-end

-- impl-start
def implementation_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
    Attrs :=
  let key := displayKey name
  if !hasKey attrs key && hasChoices then
    attrs ++ [(key, display)]
  else
    attrs
-- impl-end

-- proof-start
theorem correct_registerDisplay :
    ∀ (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int),
    problem_spec_registerDisplay attrs name hasChoices display
      (implementation_registerDisplay attrs name hasChoices display) := by
  intro attrs name hasChoices display
  unfold problem_spec_registerDisplay implementation_registerDisplay
  by_cases hc : hasChoices = true <;>
    by_cases hk : hasKey attrs (displayKey name) = true <;>
    simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec pins the ENTIRE result to a total deterministic function of inputs: result = (if hasChoices && !hasKey attrs key then attrs ++ [(key,display)] else attrs). No output component unconstrained => any behaviorally-different impl is unprovable. Axioms region empty; refinement.md legs are all R/I (no A-consumed/A-reference/kind-3), so there is NO opaque-callee attack surface to exploit. G-CONF differential test independently reconstructs the post-patch behaviour via real hasattr/setattr over >=1.3e5 inputs.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; all built by editing ONLY the impl region of Solution.lean; verified with: bash scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug: unconditional setKey when hasChoices) -> EXIT 1, rfl failed (false thm). This is the prepatch impl.
- atk_2 (inverted guard: install only when key ALREADY present) -> EXIT 1, rfl failed.
- atk_3 (control-flow effect: guard on !hasChoices) -> EXIT 1, rfl failed.
- atk_4 (partial domain: act only when name != "") -> EXIT 1, rfl failed.
- atk_5 (ungrounded echo: always append displayKey regardless of choices/presence) -> EXIT 1, unfold failed / false.
- atk_6 (boundary: append without !hasKey guard) -> EXIT 1, unfold failed / false.
NONE of the 6 wrong impls verifies, so NO faithful-patch resolve is mandated (protocol step 2 vacuously satisfied — there is no verifying wrong impl to materialize).

### POSITIVE CONTROLS (same_spec=True, must verify with clean axioms):
- pc_setkey.lean (gold monadic shape) -> lean_verify EXIT 0; #print axioms => [propext, Quot.sound] (clean).
- pc_echo.lean (STRUCTURALLY DISTINCT: non-monadic, direct if-then-else, guard order swapped) -> lean_verify EXIT 0; #print axioms => [propext] (clean). Both are behaviorally identical to gold, so their faithful refined patch IS the gold patch.

### RESOLVE (official harness run_resolve via docker, retries=1, timeout=1800):
- GOLD patch (benchmark-verified/.../patch.diff, = faithful patch of both verifying impls) -> resolved=True, completed=True, note='resolved'.
- PREPATCH faithful patch (prepatch.patch: no-op comment leaving unconditional setattr intact; git apply --check passes) -> resolved=False, completed=True, note='patch did not resolve in 2 attempts (consistent - not flaky)'. Confirms the F2P discrimination is real and the harness works.

**CONCLUSION:** every same-spec impl that closes with clean axioms (pc_setkey, pc_echo) has a faithful patch that RESOLVES; every impl whose faithful patch does NOT resolve (prepatch, atk_2..6) FAILS to verify. verify <=> correct holds. No verify-not-correct witness exists. Refinement.md audit: R/I-only, axioms empty, hasattr/setattr/%-format modeled concretely as hasKey/setKey/displayKey — correspondence to CPython builtins holds; no A-leg to falsify.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_echo.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The attribute-namespace
-- primitives (key presence test, key lookup, key assignment) and the accessor
-- key name are all modeled concretely below as plain functional helpers (R/I
-- ops), not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The attribute namespace of a class is modeled as an association list from
attribute name to a stored value (the value type is opaque to the modeled
behavior; here `Int` stands in for an arbitrary attribute value). Only key
presence and the stored value are observable. -/
abbrev Attrs := List (String × Int)

/-- The accessor name generated for a field: `get_<name>_display`. -/
def displayKey (name : String) : String := "get_" ++ name ++ "_display"

/-- Whether the namespace already binds `key`. -/
def hasKey (attrs : Attrs) (key : String) : Bool :=
  attrs.any (fun p => p.1 == key)

/-- Assign `key := v` in the namespace: replace an existing binding in place, or
append a new one. -/
def setKey (attrs : Attrs) (key : String) (v : Int) : Attrs :=
  if attrs.any (fun p => p.1 == key)
  then attrs.map (fun p => if p.1 == key then (key, v) else p)
  else attrs ++ [(key, v)]
-- pure-end

-- post-conditions-start
/-- Registering the generated display accessor for a field.

`attrs` is the class' attribute namespace, `name` the field name, `hasChoices`
whether the field carries an enumerated choice set, and `display` the generated
accessor value.

The whole namespace is pinned exactly: it is left untouched, EXCEPT in the one
case where the field carries a choice set AND the generated accessor name is not
already bound — there the accessor is appended. In particular, when the field has
a choice set but the accessor name is already bound (e.g. the class declares its
own accessor), the namespace is unchanged, so the existing binding is preserved.
The entire result is pinned to the input, leaving no output component
unconstrained. -/
def problem_spec_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int)
    (result : Attrs) : Prop :=
  let key := displayKey name
  result = (if hasChoices && !hasKey attrs key then attrs ++ [(key, display)] else attrs)
-- post-conditions-end

-- impl-start
def implementation_registerDisplay
    (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int) :
    Attrs :=
  let key := displayKey name
  if !hasKey attrs key && hasChoices then
    attrs ++ [(key, display)]
  else
    attrs
-- impl-end

-- proof-start
theorem correct_registerDisplay :
    ∀ (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int),
    problem_spec_registerDisplay attrs name hasChoices display
      (implementation_registerDisplay attrs name hasChoices display) := by
  intro attrs name hasChoices display
  unfold problem_spec_registerDisplay implementation_registerDisplay
  by_cases hc : hasChoices = true <;>
    by_cases hk : hasKey attrs (displayKey name) = true <;>
    simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec pins the ENTIRE result to a total deterministic function of inputs: result = (if hasChoices && !hasKey attrs key then attrs ++ [(key,display)] else attrs). No output component unconstrained => any behaviorally-different impl is unprovable. Axioms region empty; refinement.md legs are all R/I (no A-consumed/A-reference/kind-3), so there is NO opaque-callee attack surface to exploit. G-CONF differential test independently reconstructs the post-patch behaviour via real hasattr/setattr over >=1.3e5 inputs.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; all built by editing ONLY the impl region of Solution.lean; verified with: bash scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug: unconditional setKey when hasChoices) -> EXIT 1, rfl failed (false thm). This is the prepatch impl.
- atk_2 (inverted guard: install only when key ALREADY present) -> EXIT 1, rfl failed.
- atk_3 (control-flow effect: guard on !hasChoices) -> EXIT 1, rfl failed.
- atk_4 (partial domain: act only when name != "") -> EXIT 1, rfl failed.
- atk_5 (ungrounded echo: always append displayKey regardless of choices/presence) -> EXIT 1, unfold failed / false.
- atk_6 (boundary: append without !hasKey guard) -> EXIT 1, unfold failed / false.
NONE of the 6 wrong impls verifies, so NO faithful-patch resolve is mandated (protocol step 2 vacuously satisfied — there is no verifying wrong impl to materialize).

### POSITIVE CONTROLS (same_spec=True, must verify with clean axioms):
- pc_setkey.lean (gold monadic shape) -> lean_verify EXIT 0; #print axioms => [propext, Quot.sound] (clean).
- pc_echo.lean (STRUCTURALLY DISTINCT: non-monadic, direct if-then-else, guard order swapped) -> lean_verify EXIT 0; #print axioms => [propext] (clean). Both are behaviorally identical to gold, so their faithful refined patch IS the gold patch.

### RESOLVE (official harness run_resolve via docker, retries=1, timeout=1800):
- GOLD patch (benchmark-verified/.../patch.diff, = faithful patch of both verifying impls) -> resolved=True, completed=True, note='resolved'.
- PREPATCH faithful patch (prepatch.patch: no-op comment leaving unconditional setattr intact; git apply --check passes) -> resolved=False, completed=True, note='patch did not resolve in 2 attempts (consistent - not flaky)'. Confirms the F2P discrimination is real and the harness works.

**CONCLUSION:** every same-spec impl that closes with clean axioms (pc_setkey, pc_echo) has a faithful patch that RESOLVES; every impl whose faithful patch does NOT resolve (prepatch, atk_2..6) FAILS to verify. verify <=> correct holds. No verify-not-correct witness exists. Refinement.md audit: R/I-only, axioms empty, hasattr/setattr/%-format modeled concretely as hasKey/setKey/displayKey — correspondence to CPython builtins holds; no A-leg to falsify.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function = the `if self.choices is not None:` display-accessor registration block of Field.contribute_to_class (django/db/models/fields/`__init__`.py, base_commit worktree confirms base is the unconditional setattr; gold patch wraps it in `if not hasattr(cls, 'get_%s_display' % self.name)`). Spec: result = (if hasChoices && !hasKey attrs key then attrs ++ [(key,display)] else attrs). Mapping is exact: hasChoices↔self.choices is not None; displayKey↔'get_%s_display'%self.name; hasKey↔hasattr; append-branch↔setattr. No drift found on any input class: (1) key-present + hasChoices → spec leaves attrs unchanged == patched guard skip (the F2P override case); (2) key-absent + hasChoices → append == setattr (no replace-semantics drift since branch unreachable when present); (3) hasChoices=false → attrs untouched. `attrs` is DEFINED (mapping.md) as the resolved namespace as seen by hasattr/setattr, so MRO/inherited attrs are folded into the input — no lookup-scope divergence exists. Verification: lean_verify exit 0; #print axioms = [propext, Quot.sound] (no sorryAx); same_spec(Solution,prepatch)=True (byte-identical spec region); conformance_check.py = 0/130006 disagreements (seed 11999) against a real Python hasattr/setattr reconstruction incl. override boundary cases. No input on which the model disagrees with the real callee was found. Spec is neither too strong nor drifting; it is a total functional pin equal to the post-patch behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen over the lean spec view returns passed=True, no hard failures); meta G-LEAK status=pass, no relaxed_leakage flag. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec view is byte-identical across the pre/post-patch variants — no leakage smuggled into a differing spec.

Manual semantic check of the spec view (imports/axioms/pure/post-conditions; impl+proof elided) against the PUBLIC problem_statement only (not hints):
- Gold edit: unconditional setattr('get_%s_display'%name, ...) -> guarded with `if not hasattr(cls, 'get_%s_display' % self.name)` to preserve a user-declared accessor.
- Public problem_statement already discloses the ENTIRE scenario and required behavior: title 'Cannot override get_FOO_display() in Django 2.2+', a FooBar model with choices=[...] AND a user-defined get_foo_bar_display, and 'What I expect is that I should be able to override this function.' The override-preservation behavior is publicly required, not private.
- The spec's discriminating clause `result = (if hasChoices && !hasKey attrs key then attrs ++ [(key,display)] else attrs)` and the docstring ('when ... the accessor name is already bound (e.g. the class declares its own accessor), the namespace is unchanged, so the existing binding is preserved') are the faithful formalization of that publicly-stated requirement. A spec encoding correct post-patch behavior as its oracle is expected, not leakage.
- No leak channels beyond that inherent content: no diff markers, no gold-patch line reproduced, patched file path django/db/models/fields/`__init__`.py absent, no fix/bug narration terms in comments, and `get_..._display` naming appears verbatim in the public problem_statement so displayKey is not a beyond-statement leak.

No spec-view line reveals the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
