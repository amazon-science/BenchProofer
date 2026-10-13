# P2 adversarial audit — pydata__xarray-2905

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,8 +45,7 @@
 -- impl-start
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
-  if data.isContainer then
-    result := data.payload.getD data
+  result := data.payload.getD data
   return result
 -- impl-end
 
@@ -55,10 +54,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,8 +45,6 @@
 -- impl-start
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
-  if data.isContainer then
-    result := data.payload.getD data
   return result
 -- impl-end
 
@@ -55,10 +53,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
 -- impl-start
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
-  if data.isContainer then
+  if !data.isContainer then
     result := data.payload.getD data
   return result
 -- impl-end
@@ -55,10 +55,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
   if data.isContainer then
-    result := data.payload.getD data
+    result := data
   return result
 -- impl-end
 
@@ -55,10 +55,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,8 @@
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
   if data.isContainer then
-    result := data.payload.getD data
+    let inner := data.payload.getD data
+    result := inner.payload.getD inner
   return result
 -- impl-end
 
@@ -55,10 +56,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
 def implementation_prepare (data : Obj) : Obj := Id.run do
   let mut result := data
   if data.isContainer then
-    result := data.payload.getD data
+    result := data.payload.getD (Obj.node false none)
   return result
 -- impl-end
 
@@ -55,10 +55,8 @@
     problem_spec_prepare data (implementation_prepare data) := by
   intro data
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
-      map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
-  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
-      if_false, bind_pure_comp, map_pure]
+  · simp only [implementation_prepare, Id.run, h, bind_pure_comp, map_pure]
     rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Abstract behavior under specification.

A preparation step normalizes an incoming object before it is stored. Some
objects are recognized *wrapper containers* that merely re-expose an underlying
payload; for those, the step must replace the object by that underlying payload.
Every other object — including ones that incidentally expose a payload — must be
stored unchanged.
-/

-- axioms-start
-- No unchanged callee needs an axiomatized contract: the changed decision is
-- modeled deeply (a structural case split on the object), not assumed.
-- axioms-end

-- pure-start
/-- An incoming object, modeled by the only two properties the preparation step
observes: whether it is a recognized wrapper container, and the underlying
payload it exposes (if any). The payload is itself such an object, since the
result is stored the same way as the original. -/
inductive Obj where
  | node (isContainer : Bool) (payload : Option Obj)

/-- Whether the object is a recognized wrapper container kind. -/
def Obj.isContainer : Obj → Bool
  | .node c _ => c

/-- The underlying payload the object exposes, if any. -/
def Obj.payload : Obj → Option Obj
  | .node _ p => p
-- pure-end

-- post-conditions-start
/-- The prepared object: a recognized wrapper container is replaced by its
underlying payload; every other object (even one that exposes a payload) is kept
unchanged. -/
def problem_spec_prepare (data : Obj) (result : Obj) : Prop :=
  (data.isContainer = true  → result = data.payload.getD data) ∧
  (data.isContainer = false → result = data)
-- post-conditions-end

-- impl-start
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  if data.isContainer then
    result := data.payload.getD data
  return result
-- impl-end

-- proof-start
theorem correct_prepare : ∀ data : Obj,
    problem_spec_prepare data (implementation_prepare data) := by
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
      map_pure]
    rfl
  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
      if_false, bind_pure_comp, map_pure]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT (fully deterministic, total postcondition). problem_spec_prepare pins result on BOTH branches with no preconditions and no free cases: (isContainer=true -> result = data.payload.getD data) AND (isContainer=false -> result = data). Any same-spec impl must equal the gold function pointwise; any deviation yields an unprovable goal. All 6 same-spec wrong impls (verified same_spec=True via swebench_unified.markers.same_spec) FAIL to verify, so NO verifying wrong impl exists and there is no faithful patch to materialize/resolve (patches={}).

Attacks (cmd per file: `bash scripts/lean_verify.sh <path>`):
- atk_1 (PREPATCH BUG, unconditional unwrap `result:=data.payload.getD data`): exit=1. False goal `pure (data.payload.getD data) = data` in isContainer=false branch. Reproduces the F2P bug and is correctly rejected.
- atk_2 (always identity, never unwrap): exit=1. False goal `pure data = data.payload.getD data` in container branch.
- atk_3 (inverted condition `!data.isContainer`): exit=1. Both branch goals false.
- atk_4 (boundary: container branch returns `data`, ignores payload): exit=1. False goal `if True then pure data else pure data = data.payload.getD data`.
- atk_5 (ungrounded-oracle echo: double unwrap `inner.payload.getD inner`): exit=1. False goal `(payload.getD data).payload.getD (...) = data.payload.getD data`.
- atk_6 (control-flow-effect: wrong getD default `Obj.node false none`): exit=1. False goal `data.payload.getD (Obj.node false none) = data.payload.getD data` when container payload=none.

Positive control pc.lean = exact gold impl: verifies, exit=0. `#print axioms correct_prepare` => `[propext, Quot.sound]` (clean; no sorryAx / custom axioms).

Refinement audit: legs #1(I), #2(R), #3(R), #4(I). No A-consumed / A-reference legs; the changed isinstance+.values decision is modeled deeply via structural case split on Obj, so axiom_check.py is a legitimate SKIP stub and there are NO kind-3 legs. A-leg correspondence concern is vacuous (no axiomatized callee). Consistent with mapping.md bijection and refinement.md. R/I legs are G-CONF territory.

Verify=>correct holds: the spec admits only the gold behavior. No verify-not-correct counterexample could be constructed after 6 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, inverted-condition, prepatch). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Abstract behavior under specification.

A preparation step normalizes an incoming object before it is stored. Some
objects are recognized *wrapper containers* that merely re-expose an underlying
payload; for those, the step must replace the object by that underlying payload.
Every other object — including ones that incidentally expose a payload — must be
stored unchanged.
-/

-- axioms-start
-- No unchanged callee needs an axiomatized contract: the changed decision is
-- modeled deeply (a structural case split on the object), not assumed.
-- axioms-end

-- pure-start
/-- An incoming object, modeled by the only two properties the preparation step
observes: whether it is a recognized wrapper container, and the underlying
payload it exposes (if any). The payload is itself such an object, since the
result is stored the same way as the original. -/
inductive Obj where
  | node (isContainer : Bool) (payload : Option Obj)

/-- Whether the object is a recognized wrapper container kind. -/
def Obj.isContainer : Obj → Bool
  | .node c _ => c

/-- The underlying payload the object exposes, if any. -/
def Obj.payload : Obj → Option Obj
  | .node _ p => p
-- pure-end

-- post-conditions-start
/-- The prepared object: a recognized wrapper container is replaced by its
underlying payload; every other object (even one that exposes a payload) is kept
unchanged. -/
def problem_spec_prepare (data : Obj) (result : Obj) : Prop :=
  (data.isContainer = true  → result = data.payload.getD data) ∧
  (data.isContainer = false → result = data)
-- post-conditions-end

-- impl-start
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  if data.isContainer then
    result := data.payload.getD data
  return result
-- impl-end

-- proof-start
theorem correct_prepare : ∀ data : Obj,
    problem_spec_prepare data (implementation_prepare data) := by
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
      map_pure]
    rfl
  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
      if_false, bind_pure_comp, map_pure]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT (fully deterministic, total postcondition). problem_spec_prepare pins result on BOTH branches with no preconditions and no free cases: (isContainer=true -> result = data.payload.getD data) AND (isContainer=false -> result = data). Any same-spec impl must equal the gold function pointwise; any deviation yields an unprovable goal. All 6 same-spec wrong impls (verified same_spec=True via swebench_unified.markers.same_spec) FAIL to verify, so NO verifying wrong impl exists and there is no faithful patch to materialize/resolve (patches={}).

Attacks (cmd per file: `bash scripts/lean_verify.sh <path>`):
- atk_1 (PREPATCH BUG, unconditional unwrap `result:=data.payload.getD data`): exit=1. False goal `pure (data.payload.getD data) = data` in isContainer=false branch. Reproduces the F2P bug and is correctly rejected.
- atk_2 (always identity, never unwrap): exit=1. False goal `pure data = data.payload.getD data` in container branch.
- atk_3 (inverted condition `!data.isContainer`): exit=1. Both branch goals false.
- atk_4 (boundary: container branch returns `data`, ignores payload): exit=1. False goal `if True then pure data else pure data = data.payload.getD data`.
- atk_5 (ungrounded-oracle echo: double unwrap `inner.payload.getD inner`): exit=1. False goal `(payload.getD data).payload.getD (...) = data.payload.getD data`.
- atk_6 (control-flow-effect: wrong getD default `Obj.node false none`): exit=1. False goal `data.payload.getD (Obj.node false none) = data.payload.getD data` when container payload=none.

Positive control pc.lean = exact gold impl: verifies, exit=0. `#print axioms correct_prepare` => `[propext, Quot.sound]` (clean; no sorryAx / custom axioms).

Refinement audit: legs #1(I), #2(R), #3(R), #4(I). No A-consumed / A-reference legs; the changed isinstance+.values decision is modeled deeply via structural case split on Obj, so axiom_check.py is a legitimate SKIP stub and there are NO kind-3 legs. A-leg correspondence concern is vacuous (no axiomatized callee). Consistent with mapping.md bijection and refinement.md. R/I legs are G-CONF territory.

Verify=>correct holds: the spec admits only the gold behavior. No verify-not-correct counterexample could be constructed after 6 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, inverted-condition, prepatch). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) check for pydata__xarray-2905 lean bundle.

Mechanical checks:
- Solution.lean compiles under lean_verify.sh (exit 0).
- #print axioms correct_prepare = [propext, Quot.sound]; NO sorryAx -> proof is genuine.
- same_spec(Solution.lean, Solution_prepatch.lean, lean TABLES) = True: axioms/pure/pre/post spec regions byte-identical; only impl+proof differ (prepatch impl drops the isContainer guard -> unconditional unwrap, proof=sorry). Correct F2P discrimination.
- conformance_check.py differential test: 200000 fuzzed inputs, 0 disagreements, status pass.

Modeled function: as_compatible_data(data, fastpath=False) @ xarray/core/variable.py, single changed site (line 171 in worktree base commit). Gold patch changes `data = getattr(data,'values',data)` -> `if isinstance(data,(pd.Series,pd.Index,pd.DataFrame)): data = data.values`.

Spec models the local value of `data` immediately after the changed unwrap block:
  isContainer=true  -> result = payload.getD data   (real: container => data=data.values; a real pandas container always has .values so payload=some p, getD -> p). MATCHES.
  isContainer=false -> result = data                (real: non-container leaves data unchanged through block). MATCHES.

The only place the model could differ from real behavior is isContainer=true & payload=none, where the model yields `data` instead of the payload. This state is unreachable under the documented pandas invariant (a recognized container always exposes .values), and even there the model value equals the real value. No input exists where the modeled function disagrees with the real post-patch callee at the chosen abstraction boundary (value of local `data` after the changed block, before the shared np.asarray/_maybe_wrap_data tail identical in both patches).

The spec is a tight bi-implication that exactly captures the deterministic post-patch behavior; it is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the lean spec view) passes with 0 hard failures: no diff markers, no reproduced gold-patch line, no patched file/module path, no repo-symbol echo, no narration terms. Semantic review confirms no leakage beyond the public problem_statement. The gold edit is: replace `data = getattr(data, "values", data)` with `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values` — i.e. unwrap ONLY recognized pandas containers, not any object incidentally exposing `.values`. The public problem_statement ALREADY states this exact expected behavior: the `HasValues` minimal example plus 'Expected Output' explicitly require that an object which merely has a `.values` property be stored unchanged. The spec view restates this abstractly (an object is a 'recognized wrapper container' via opaque trait `Obj.isContainer`; only containers are replaced by their payload; 'ones that incidentally expose a payload' stay unchanged). It does NOT reveal the gold discriminator (the pandas type tuple pd.Series/pd.Index/pd.DataFrame), the `.values`/getattr line, the modeled function name `as_compatible_data`, the file path xarray/core/variable.py, or any changed line. `isContainer`/`payload` are generalized model traits, not repo symbols. All gold-edit-specific information is generalized away; the fix direction disclosed is already fully public in problem_statement's example and Expected Output section. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
