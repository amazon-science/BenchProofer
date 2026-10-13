# P2 adversarial audit — pydata__xarray-2905

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6b.lean`, `atk_7b.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong impl whose faithful refined patch fails to resolve was found. The only degrees of freedom for a verifying impl that differs textually from `forwarded` lie in the require-EXCLUDED (infeasible) domain isRecognized=true ∧ valuesPayload=none — a recognized pandas container (pd.Series/Index/DataFrame) that lacks a `.values` attribute, which cannot occur. atk_6b (returns w.obj+1 on that arm) and atk_7b (returns valuesPayload.getD 0, i.e. 0 on that arm) both VERIFY (lean exit 0, no sorry) yet their faithful materialized patches place the divergent code on the dead `not hasattr(data,'values')` branch inside the recognized-container guard, so the executed behavior is identical to gold — both RESOLVED=True under run_resolve (F2P test_unsupported_type success, all PASS_TO_PASS success).
```

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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,11 +81,13 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
+    -- ATTACK 1 (prepatch bug / ungrounded on presence): unwrap whenever ANY
+    -- values payload is exposed, regardless of type. Differs from `forwarded`
+    -- on isRecognized=false ∧ valuesPayload=some v (returns v, spec demands obj).
     let out :=
-      if w.isRecognized then
-        w.valuesPayload.getD w.obj
-      else
-        w.obj
+      match w.valuesPayload with
+      | some v => v
+      | none   => w.obj
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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,11 +81,9 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
-    let out :=
-      if w.isRecognized then
-        w.valuesPayload.getD w.obj
-      else
-        w.obj
+    -- ATTACK 2 (partial-domain / boundary): always forward the object unchanged.
+    -- Correct on the else arm but wrong on the recognized arm (fails to unwrap).
+    let out := w.obj
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,11 +81,12 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
+    -- ATTACK 3 (control-flow-effect / inverted arms): swap the two branches.
     let out :=
       if w.isRecognized then
+        w.obj
+      else
         w.valuesPayload.getD w.obj
-      else
-        w.obj
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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,8 +81,11 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
+    -- ATTACK 4 (control-flow-effect / OR-widened predicate): unwrap when the
+    -- object is recognized OR merely exposes a payload — the precise F2P bug.
+    -- Fails on isRecognized=false ∧ valuesPayload=some v.
     let out :=
-      if w.isRecognized then
+      if w.isRecognized || w.valuesPayload.isSome then
         w.valuesPayload.getD w.obj
       else
         w.obj
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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,11 +81,8 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
-    let out :=
-      if w.isRecognized then
-        w.valuesPayload.getD w.obj
-      else
-        w.obj
+    -- ATTACK 5 (ungrounded-oracle echo / constant): return a fixed object 0.
+    let out : Obj := 0
     return out
     -- impl-end
 
```

Attack 6 — `atk_6b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,9 +81,19 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
+    -- ATTACK 6 (require-excluded domain / the ONLY legal wiggle room):
+    -- behaves like `forwarded` everywhere the `require` holds, but on the
+    -- INFEASIBLE domain (isRecognized=true ∧ valuesPayload=none) returns a
+    -- DIFFERENT object (w.obj + 1) instead of forwarded's getD-fallback w.obj.
+    -- The `require` (isRecognized→valuesPayload.isSome) rules that case out, so
+    -- this still VERIFIES. The audit question: does its faithful refined patch
+    -- (which cannot express the infeasible arm and collapses to `data.values`)
+    -- still resolve? If it does, verify⇒correct holds on this leg.
     let out :=
       if w.isRecognized then
-        w.valuesPayload.getD w.obj
+        match w.valuesPayload with
+        | some v => v
+        | none   => w.obj + 1
       else
         w.obj
     return out
@@ -91,4 +101,10 @@
 
 prove_correct prepareData by
   loom_solve
-  simp_all [forwarded]
+  simp only [forwarded]
+  by_cases h : w.isRecognized = true
+  · have hs := require_1 h
+    cases hv : w.valuesPayload with
+    | none => simp [hv] at hs
+    | some v => simp [h, hv]
+  · simp [h]
```

Attack 7 — `atk_7b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
@@ -81,9 +81,15 @@
     -- recognized container types is unwrapped to its stored values payload;
     -- every other object (including one that merely exposes a values payload) is
     -- forwarded unchanged.
+    -- ATTACK 7 (second require-excluded exploit, distinct value): identical to
+    -- `forwarded` on every feasible input, but on the infeasible arm
+    -- (isRecognized=true ∧ valuesPayload=none) returns a constant 0 rather than
+    -- forwarded's w.obj. Still verifies (require excludes that case). A second
+    -- witness that ANY excluded-domain-only divergence verifies but maps to the
+    -- SAME faithful patch (`data = data.values`).
     let out :=
       if w.isRecognized then
-        w.valuesPayload.getD w.obj
+        w.valuesPayload.getD 0
       else
         w.obj
     return out
@@ -91,4 +97,10 @@
 
 prove_correct prepareData by
   loom_solve
-  simp_all [forwarded]
+  simp only [forwarded]
+  by_cases h : w.isRecognized = true
+  · have hs := require_1 h
+    cases hv : w.valuesPayload with
+    | none => simp [hv] at hs
+    | some v => simp [h, hv]
+  · simp [h]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
--  incoming object's own observable shape: whether it is one of the recognized
--  container types, and what stored values it exposes. Both are read deeply from
--  the input carrier's fields (`isRecognized`, `valuesPayload`) — there is no
--  outside callee whose contract the proof consumes, and no claim is made about
--  any unchanged routine, so there is nothing to check against a real callee,
--  hence no G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The identity of a data object (or of a stored values payload), modeled
   abstractly: the desired behaviour observes only WHICH object is forwarded —
   the object handed in, or the values it exposes — never the object's content.
   A single opaque carrier therefore suffices. -/
abbrev Obj := Nat

/- A data object as it arrives at the preparation step, described by exactly the
   three observables the dispatch consults:

   * `obj`           — the object's own identity (what "forward it unchanged"
                       yields);
   * `valuesPayload` — the stored values the object exposes, if it exposes any
                       (`some v`), or `none` if it exposes no such stored values;
   * `isRecognized`  — whether the object is one of the recognized container
                       types whose stored values are meant to be taken.

   Two incoming objects are the same exactly when all three observables agree. -/
structure Incoming where
  obj            : Obj
  valuesPayload  : Option Obj
  isRecognized   : Bool
  deriving DecidableEq

/- What the preparation step forwards.

   An object of one of the recognized container types is unwrapped to the stored
   values it exposes; EVERY other object is forwarded unchanged — even one that
   happens to expose a stored-values payload. In particular, exposing a values
   payload is NOT on its own grounds to unwrap: only the recognized container
   types are unwrapped. This is the behaviour an arbitrary user object with a
   values payload requires — it must be forwarded as itself, not silently
   replaced by its payload. -/
def forwarded (w : Incoming) : Obj :=
  if w.isRecognized then w.valuesPayload.getD w.obj else w.obj
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a data object for downstream wrapping.

   `w` carries the incoming object's three observables (above). The result is the
   object that should be handed downstream: an object of one of the recognized
   container types is replaced by the stored values it exposes; any other object
   — including one that merely exposes a values payload — is forwarded unchanged.

   `w` is read-only (not `mut`): the step inspects the incoming object's shape and
   returns the object to forward, mutating nothing it is handed (directive 5).

   `require`: an object of a recognized container type always exposes a stored
   values payload (`isRecognized → valuesPayload.isSome`), so unwrapping it
   genuinely yields that payload rather than falling back to the object itself. -/
method prepareData (w : Incoming) return (out : Obj)
  require w.isRecognized = true → w.valuesPayload.isSome = true
  ensures out = forwarded w
  do
    -- impl-start
    -- Dispatch on the incoming object's shape. An object of one of the
    -- recognized container types is unwrapped to its stored values payload;
    -- every other object (including one that merely exposes a values payload) is
    -- forwarded unchanged.
    let out :=
      if w.isRecognized then
        w.valuesPayload.getD w.obj
      else
        w.obj
    return out
    -- impl-end

prove_correct prepareData by
  loom_solve
  simp_all [forwarded]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & EVIDENCE. Byte-identical-spec confirmed for all 7 attacks + positive control + prepatch via swebench_unified.markers.same_spec (velvet lang) = True in every case (edits confined to impl region / proof tail, both outside the frozen spec markers).

SPEC SHAPE: postcondition `out = forwarded w` is a TOTAL pointwise equality to a transparent pure function forwarded w = if w.isRecognized then w.valuesPayload.getD w.obj else w.obj, guarded by require (isRecognized=true → valuesPayload.isSome=true). No axioms (empty block), no opaque oracle. The only region where a verifying impl can legally differ from forwarded is the require-EXCLUDED domain isRecognized=true ∧ valuesPayload=none.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (frozen correct impl) -> exit 0 (VERIFIES; spec satisfiable, non-vacuous).
- atk_1 (prepatch bug: match payload | some v=>v | none=>obj) -> exit 1 FAIL (residual fails on isRecognized=false ∧ payload=some v).
- atk_2 (always w.obj) -> exit 1 FAIL (recognized arm).
- atk_3 (inverted arms) -> exit 1 FAIL.
- atk_4 (OR-widened: if isRecognized || payload.isSome — the precise F2P bug) -> exit 1 FAIL (isRecognized=false ∧ payload=some).
- atk_5 (constant 0) -> exit 1 FAIL.
- atk_6/atk_7 under the FROZEN proof tail -> exit 1 (frozen tail does not discharge the require hypothesis on the excluded arm).
- atk_6b, atk_7b (SAME impl bodies as atk_6/atk_7 — divergence only on the require-excluded arm — with a proof tail adjusted to consume require_1, exactly as the positive control was adjusted) -> exit 0 VERIFY (no sorry; only an unusedSimpArg linter warning). These are the genuine verifying-but-textually-wrong impls.

prepatch.lean (official Solution_prepatch.lean) reproduced: same_spec=True, verify exit 1, residual fails exactly on the isRecognized=false ∧ payload=some clause -> G-DIFF genuine.

### RESOLVE RUNS (harness.run_resolve, official SWE-bench oracle, in-container at base_commit):
- atk_6b faithful patch -> RESOLVED=True, COMPLETED=True, note=resolved; FAIL_TO_PASS success=[TestAsCompatibleData::test_unsupported_type], all PASS_TO_PASS success, no failures.
- atk_7b faithful patch -> RESOLVED=True, COMPLETED=True, note=resolved; FAIL_TO_PASS success=[test_unsupported_type], failure=[].
Both verifying wrong impls' faithful patches RESOLVE -> verify⇒correct holds; spec NOT broken.

WHY THE VERIFYING IMPLS DON'T BREAK IT: the divergence (w.obj+1 / getD 0) is only reachable when a pd.Series/Index/DataFrame lacks a `.values` attribute — impossible (those types always expose `.values`; this is the very fact the require encodes). The faithful materialization puts that code on the dead `not hasattr(data,'values')` branch guarded by the isinstance check, so executed behavior == gold `data = data.values`. This is exactly why the require is sound and does NOT hide a real bug: it only excludes an infeasible domain, and any excluded-domain-only divergence materializes as dead code.

REFINEMENT.md AUDIT: 4 legs A1–A4, all tagged R or R+I; no consumed axioms, no A-reference, no kind-3. A1 (w:Incoming ↔ live data, opaque-identity carrier) R — only identity/values-presence/type observed, never content; sound. A2 (if w.isRecognized ↔ isinstance(data,(pd.Series,pd.Index,pd.DataFrame))) R — isinstance outcome is the free Bool input; sound. A3 (recognized arm w.valuesPayload.getD w.obj ↔ data=data.values) R+I — require guarantees the genuine payload is taken; sound. A4 (else arm w.obj ↔ data unchanged) R+I — the behavioral fix (unrecognized-with-payload forwarded unchanged); sound and confirmed by the F2P test. axioms block empty -> no A-consumed/A-reference legs to correspond to a real callee -> G-AX correctly N/A. G-CONF conf_skip justified (sole discriminating observable is forwarded-object identity on the live CPython/numpy machinery; no interpreter-free R/I shadow; soundness carried by G-VERIFY+G-DIFF).

CONCLUSION: ≥5 distinct attacks encoded and machine-verified (7 attack variants + prepatch + positive control); the prepatch bug + F2P bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle-echo classes all correctly verify-FAIL; the two impls that DO verify (require-excluded-domain exploits, the only legal wiggle room) both have faithful patches that RESOLVE. No falsification of verify⇒correct found. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6b.lean`, `atk_7b.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong impl whose faithful refined patch fails to resolve was found. The only degrees of freedom for a verifying impl that differs textually from `forwarded` lie in the require-EXCLUDED (infeasible) domain isRecognized=true ∧ valuesPayload=none — a recognized pandas container (pd.Series/Index/DataFrame) that lacks a `.values` attribute, which cannot occur. atk_6b (returns w.obj+1 on that arm) and atk_7b (returns valuesPayload.getD 0, i.e. 0 on that arm) both VERIFY (lean exit 0, no sorry) yet their faithful materialized patches place the divergent code on the dead `not hasattr(data,'values')` branch inside the recognized-container guard, so the executed behavior is identical to gold — both RESOLVED=True under run_resolve (F2P test_unsupported_type success, all PASS_TO_PASS success).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure dispatch on the
--  incoming object's own observable shape: whether it is one of the recognized
--  container types, and what stored values it exposes. Both are read deeply from
--  the input carrier's fields (`isRecognized`, `valuesPayload`) — there is no
--  outside callee whose contract the proof consumes, and no claim is made about
--  any unchanged routine, so there is nothing to check against a real callee,
--  hence no G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The identity of a data object (or of a stored values payload), modeled
   abstractly: the desired behaviour observes only WHICH object is forwarded —
   the object handed in, or the values it exposes — never the object's content.
   A single opaque carrier therefore suffices. -/
abbrev Obj := Nat

/- A data object as it arrives at the preparation step, described by exactly the
   three observables the dispatch consults:

   * `obj`           — the object's own identity (what "forward it unchanged"
                       yields);
   * `valuesPayload` — the stored values the object exposes, if it exposes any
                       (`some v`), or `none` if it exposes no such stored values;
   * `isRecognized`  — whether the object is one of the recognized container
                       types whose stored values are meant to be taken.

   Two incoming objects are the same exactly when all three observables agree. -/
structure Incoming where
  obj            : Obj
  valuesPayload  : Option Obj
  isRecognized   : Bool
  deriving DecidableEq

/- What the preparation step forwards.

   An object of one of the recognized container types is unwrapped to the stored
   values it exposes; EVERY other object is forwarded unchanged — even one that
   happens to expose a stored-values payload. In particular, exposing a values
   payload is NOT on its own grounds to unwrap: only the recognized container
   types are unwrapped. This is the behaviour an arbitrary user object with a
   values payload requires — it must be forwarded as itself, not silently
   replaced by its payload. -/
def forwarded (w : Incoming) : Obj :=
  if w.isRecognized then w.valuesPayload.getD w.obj else w.obj
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a data object for downstream wrapping.

   `w` carries the incoming object's three observables (above). The result is the
   object that should be handed downstream: an object of one of the recognized
   container types is replaced by the stored values it exposes; any other object
   — including one that merely exposes a values payload — is forwarded unchanged.

   `w` is read-only (not `mut`): the step inspects the incoming object's shape and
   returns the object to forward, mutating nothing it is handed (directive 5).

   `require`: an object of a recognized container type always exposes a stored
   values payload (`isRecognized → valuesPayload.isSome`), so unwrapping it
   genuinely yields that payload rather than falling back to the object itself. -/
method prepareData (w : Incoming) return (out : Obj)
  require w.isRecognized = true → w.valuesPayload.isSome = true
  ensures out = forwarded w
  do
    -- impl-start
    -- Dispatch on the incoming object's shape. An object of one of the
    -- recognized container types is unwrapped to its stored values payload;
    -- every other object (including one that merely exposes a values payload) is
    -- forwarded unchanged.
    let out :=
      if w.isRecognized then
        w.valuesPayload.getD w.obj
      else
        w.obj
    return out
    -- impl-end

prove_correct prepareData by
  loom_solve
  simp_all [forwarded]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & EVIDENCE. Byte-identical-spec confirmed for all 7 attacks + positive control + prepatch via swebench_unified.markers.same_spec (velvet lang) = True in every case (edits confined to impl region / proof tail, both outside the frozen spec markers).

SPEC SHAPE: postcondition `out = forwarded w` is a TOTAL pointwise equality to a transparent pure function forwarded w = if w.isRecognized then w.valuesPayload.getD w.obj else w.obj, guarded by require (isRecognized=true → valuesPayload.isSome=true). No axioms (empty block), no opaque oracle. The only region where a verifying impl can legally differ from forwarded is the require-EXCLUDED domain isRecognized=true ∧ valuesPayload=none.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (frozen correct impl) -> exit 0 (VERIFIES; spec satisfiable, non-vacuous).
- atk_1 (prepatch bug: match payload | some v=>v | none=>obj) -> exit 1 FAIL (residual fails on isRecognized=false ∧ payload=some v).
- atk_2 (always w.obj) -> exit 1 FAIL (recognized arm).
- atk_3 (inverted arms) -> exit 1 FAIL.
- atk_4 (OR-widened: if isRecognized || payload.isSome — the precise F2P bug) -> exit 1 FAIL (isRecognized=false ∧ payload=some).
- atk_5 (constant 0) -> exit 1 FAIL.
- atk_6/atk_7 under the FROZEN proof tail -> exit 1 (frozen tail does not discharge the require hypothesis on the excluded arm).
- atk_6b, atk_7b (SAME impl bodies as atk_6/atk_7 — divergence only on the require-excluded arm — with a proof tail adjusted to consume require_1, exactly as the positive control was adjusted) -> exit 0 VERIFY (no sorry; only an unusedSimpArg linter warning). These are the genuine verifying-but-textually-wrong impls.

prepatch.lean (official Solution_prepatch.lean) reproduced: same_spec=True, verify exit 1, residual fails exactly on the isRecognized=false ∧ payload=some clause -> G-DIFF genuine.

### RESOLVE RUNS (harness.run_resolve, official SWE-bench oracle, in-container at base_commit):
- atk_6b faithful patch -> RESOLVED=True, COMPLETED=True, note=resolved; FAIL_TO_PASS success=[TestAsCompatibleData::test_unsupported_type], all PASS_TO_PASS success, no failures.
- atk_7b faithful patch -> RESOLVED=True, COMPLETED=True, note=resolved; FAIL_TO_PASS success=[test_unsupported_type], failure=[].
Both verifying wrong impls' faithful patches RESOLVE -> verify⇒correct holds; spec NOT broken.

WHY THE VERIFYING IMPLS DON'T BREAK IT: the divergence (w.obj+1 / getD 0) is only reachable when a pd.Series/Index/DataFrame lacks a `.values` attribute — impossible (those types always expose `.values`; this is the very fact the require encodes). The faithful materialization puts that code on the dead `not hasattr(data,'values')` branch guarded by the isinstance check, so executed behavior == gold `data = data.values`. This is exactly why the require is sound and does NOT hide a real bug: it only excludes an infeasible domain, and any excluded-domain-only divergence materializes as dead code.

REFINEMENT.md AUDIT: 4 legs A1–A4, all tagged R or R+I; no consumed axioms, no A-reference, no kind-3. A1 (w:Incoming ↔ live data, opaque-identity carrier) R — only identity/values-presence/type observed, never content; sound. A2 (if w.isRecognized ↔ isinstance(data,(pd.Series,pd.Index,pd.DataFrame))) R — isinstance outcome is the free Bool input; sound. A3 (recognized arm w.valuesPayload.getD w.obj ↔ data=data.values) R+I — require guarantees the genuine payload is taken; sound. A4 (else arm w.obj ↔ data unchanged) R+I — the behavioral fix (unrecognized-with-payload forwarded unchanged); sound and confirmed by the F2P test. axioms block empty -> no A-consumed/A-reference legs to correspond to a real callee -> G-AX correctly N/A. G-CONF conf_skip justified (sole discriminating observable is forwarded-object identity on the live CPython/numpy machinery; no interpreter-free R/I shadow; soundness carried by G-VERIFY+G-DIFF).

CONCLUSION: ≥5 distinct attacks encoded and machine-verified (7 attack variants + prepatch + positive control); the prepatch bug + F2P bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle-echo classes all correctly verify-FAIL; the two impls that DO verify (require-excluded-domain exploits, the only legal wiggle room) both have faithful patches that RESOLVE. No falsification of verify⇒correct found. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True; pure `forwarded` region identical across Solution/Solution_prepatch, diff confined to impl skeleton). Modeled slice = as_compatible_data line 220-221 (xarray/core/variable.py). Post-patch real behavior: isinstance(data,(pd.Series,pd.Index,pd.DataFrame)) -> data=data.values, else data unchanged. Model forwarded w = if isRecognized then valuesPayload.getD obj else obj, with abstraction isRecognized<->isinstance, valuesPayload<->getattr(data,'values'), obj<->data. Recognized arm: precond isRecognized->valuesPayload.isSome holds for all real recognized types (pd.Series/Index/DataFrame always expose .values), so getD obj = genuine payload = data.values; precond excludes no reachable real input, hiding no drift. Unrecognized arm returns obj unchanged, matching real behavior including the discriminating case (unrecognized object exposing .values: valuesPayload=some v, isRecognized=false -> obj), which is exactly the fix. `ensures out=forwarded w` is a full functional equality on the concrete op: not too strong (no input where the model demands more than the repo delivers) and not too weak. Verified: Solution.lean elaborates (exit 0); Solution_prepatch.lean fails prove_correct precisely on isRecognized=false & valuesPayload=some v (G-DIFF sound). No input where the modeled function disagrees with the real callee on the modeled slice; conf_skip=true is justified (identity-only observable). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True under the VelvetBackend LanguageTables; only the impl and proof regions differ and both are correctly elided in the consumer spec view (confirmed by rendering markers.spec_view: impl shows '-- implementation elided', proof shows '-- proof elided').

Leakage baseline = public problem_statement (hints_text EXCLUDED). The problem_statement already fully discloses the discriminating behavior of the gold fix: it gives the HasValues() minimal example (an arbitrary user object exposing a .values attribute) and states the expected output is the object stored UNCHANGED (array([<HasValues instance>], dtype=object)) rather than coerced to its .values payload. So 'an unrecognized object exposing .values must be forwarded as itself, not unwrapped' is public.

Spec view content: opaque carrier Obj:=Nat, an Incoming struct {obj, valuesPayload, isRecognized}, and forwarded w := if w.isRecognized then w.valuesPayload.getD w.obj else w.obj, with a docstring stating only recognized container types are unwrapped and every other object (including one merely exposing a values payload) is forwarded unchanged. The postcondition `ensures out = forwarded w` and the `require w.isRecognized -> valuesPayload.isSome` are the minimum needed to state correctness and coincide with the problem_statement's expected output rather than exceeding it.

Critically, the spec view NEVER names the concrete gold edit: no pd.Series/pd.Index/pd.DataFrame, no isinstance, no getattr, no as_compatible_data, no variable.py, no line 220-221. The specific narrowing `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` appears ONLY in hints_text (excluded) and in the audit docs mapping.md/refinement.md (NOT in the spec view). The pandas type tuple is abstracted into an opaque isRecognized:Bool; knowing 'unwrap only recognized container types' without which types is exactly the altitude of the public problem statement and is not an actionable patch reconstruction. G-LEAK (lexical screen) also passed (spec view clean). No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
