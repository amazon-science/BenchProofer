# P2 adversarial audit — pytest-dev__pytest-7521

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,21 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
-def implementation_readCaptured (written : List Char) : List Char := Id.run do
-  let mut out : Array Char := #[]
-  for c in written do
-    out := out.push c
-  return out.toList
+/-- WRONG (prepatch bug echo): translate every \r to \n. -/
+def implementation_readCaptured (written : List Char) : List Char :=
+  written.map (fun c => if c = '\r' then '\n' else c)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,21 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
-def implementation_readCaptured (written : List Char) : List Char := Id.run do
-  let mut out : Array Char := #[]
-  for c in written do
-    out := out.push c
-  return out.toList
+/-- WRONG (boundary): drop the first char (tail). -/
+def implementation_readCaptured (written : List Char) : List Char :=
+  written.tail
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,21 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
-def implementation_readCaptured (written : List Char) : List Char := Id.run do
-  let mut out : Array Char := #[]
-  for c in written do
-    out := out.push c
-  return out.toList
+/-- WRONG (control-flow effect): append a trailing newline. -/
+def implementation_readCaptured (written : List Char) : List Char :=
+  written ++ ['\n']
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,21 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
-def implementation_readCaptured (written : List Char) : List Char := Id.run do
-  let mut out : Array Char := #[]
-  for c in written do
-    out := out.push c
-  return out.toList
+/-- WRONG (ungrounded oracle / constant): always return empty. -/
+def implementation_readCaptured (written : List Char) : List Char :=
+  []
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,23 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
-def implementation_readCaptured (written : List Char) : List Char := Id.run do
-  let mut out : Array Char := #[]
-  for c in written do
-    out := out.push c
-  return out.toList
+/-- WRONG (partial-domain): identity except returns ['x'] on empty input. -/
+def implementation_readCaptured (written : List Char) : List Char :=
+  match written with
+  | [] => ['x']
+  | l  => l
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,39 +22,35 @@
   result = written
 -- post-conditions-end
 
+
 -- impl-start
-/-- Read the buffered character stream back out. Each character that was written
-is handed back unchanged, in order, with no transformation applied. -/
+/-- WRONG (prepatch): universal-newline translation. -/
 def implementation_readCaptured (written : List Char) : List Char := Id.run do
   let mut out : Array Char := #[]
+  let mut prevCR := false
   for c in written do
-    out := out.push c
+    if c = '\r' then
+      out := out.push '\n'
+      prevCR := true
+    else if c = '\n' then
+      if prevCR then
+        prevCR := false
+      else
+        out := out.push '\n'
+    else
+      out := out.push c
+      prevCR := false
   return out.toList
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation over the array, generalized over the
-accumulator: writing each character in order appends `written` to the running
-array. Proven by induction with `List.forIn_cons`. -/
-theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
-    (forIn written init (fun c r =>
-        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
-    = pure (init ++ ⟨written⟩) := by
-  induction written generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind, ih]
-    apply congrArg
-    apply Array.ext'
-    simp
-
 theorem correct_readCaptured :
     ∀ (written : List Char),
     problem_spec_readCaptured written (implementation_readCaptured written) := by
   intro written
-  unfold problem_spec_readCaptured implementation_readCaptured
-  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
-  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
-  simp
+  simp only [problem_spec_readCaptured, implementation_readCaptured]
+  first
+    | rfl
+    | simp
+    | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification — turning the raw character stream that was written into the
-- capture buffer back into the text handed to the caller — is modeled DEEPLY as
-- the single read pass below, rather than abstracted behind any callee. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text read back out of a capture buffer must reproduce, character for
character, exactly the text that was written into it: nothing is dropped,
rewritten, merged, or inserted. The result is pinned entirely to the input
stream — the readback equals the written stream verbatim. -/
def problem_spec_readCaptured (written : List Char) (result : List Char) : Prop :=
  result = written
-- post-conditions-end

-- impl-start
/-- Read the buffered character stream back out. Each character that was written
is handed back unchanged, in order, with no transformation applied. -/
def implementation_readCaptured (written : List Char) : List Char := Id.run do
  let mut out : Array Char := #[]
  for c in written do
    out := out.push c
  return out.toList
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation over the array, generalized over the
accumulator: writing each character in order appends `written` to the running
array. Proven by induction with `List.forIn_cons`. -/
theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
    (forIn written init (fun c r =>
        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
    = pure (init ++ ⟨written⟩) := by
  induction written generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    apply congrArg
    apply Array.ext'
    simp

theorem correct_readCaptured :
    ∀ (written : List Char),
    problem_spec_readCaptured written (implementation_readCaptured written) := by
  intro written
  unfold problem_spec_readCaptured implementation_readCaptured
  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) verdict: SOUND. Spec byte-identical (same_spec=True for all 6 attacks + positive control, verified via swebench_unified.markers.same_spec). The frozen spec `problem_spec_readCaptured written result := result = written` is a TIGHT, SINGLE-VALUED identity contract: for each `written` exactly one satisfying `result` exists (= written verbatim). Any implementation whose `correct_readCaptured` closes with CLEAN axioms is therefore extensionally the identity on List Char, which IS exactly the post-patch (newline="") verbatim-readback behavior => it resolves. Divergence from `written` immediately falsifies `result = written`, so no closing clean-axiom impl maps to a non-resolving patch. verify => correct holds.

ATTACKS (6 distinct same-spec wrong impls, each a genuine closing attempt via `first | rfl | simp | decide`, all verified in /tmp): atk_1 partial/prepatch echo (map \r->\n); atk_2 boundary (written.tail, off-by-one); atk_3 control-flow effect (written ++ ['\n']); atk_4 ungrounded constant ([] always); atk_5 partial-domain (identity except ['x'] on empty input); atk_6 = the FAITHFUL prepatch bug (full universal-newline translation, byte-identical to Solution_prepatch.lean impl, prepatch_reproduced=true).

RESULTS (scripts/lean_verify.sh <f>, and adversary.check_attack): every one of atk_1..atk_6 => same_spec=True, verifies=FALSE (exit 1, unsolved/false goals) — the spec correctly REJECTS each. Concrete non-closures observed: atk_1 goal `List.map (...\r->\n) written = written` false; atk_2 `written.tail = written` false; atk_3 `... = written` reduces to `False`; atk_4 `written = []` false; atk_5 match-on-empty false; atk_6 forIn-translation != written. Because NO wrong impl closes with clean axioms, NO faithful-patch resolve run is mandated (the resolve step only triggers for a same-spec CLEAN-AXIOM-verifying candidate; there are none). Positive control (exact Solution.lean) verifies (exit 0) with `#print axioms correct_readCaptured` = [propext, Quot.sound] (clean).

AXIOM-INJECTION PROBE (atk_7, NOT submitted): a constant-empty impl "proven" via an injected `axiom cheat_readCaptured` in the proof region. It closes under lean_verify (exit 0, no sorry) but `#print axioms` = [cheat_readCaptured] — DIRTY, so it does NOT meet the clean-axiom break criterion and is not a spec weakness; strict G-VERIFY/G-HYGIENE reject it via gates/_lean_axioms.check_proof_axioms. I deliberately EXCLUDE it from `attacks`: (a) with no patch it would force a spurious INCONCLUSIVE, (b) with a non-resolving patch it would fabricate a false BROKEN — both dishonest given the axioms are unclean. HARNESS-HYGIENE NOTE (not a spec defect): adversary.check_attack -> _verify_attack -> check_bundle_file checks only compiles+no-sorry, NOT check_proof_axioms, so it reports atk_7 verifies=True; and _lean_axioms.declared_axiom_names scans the WHOLE file so an axiom declared in the (elided) proof region self-allowlists. This gap fails CLOSED for the spec question (it could only manufacture a false BROKEN, never let a weak spec pass), so it does not affect the G-EQ soundness of THIS bundle; flagged for maintainers.

REFINEMENT.MD A-LEG AUDIT: axioms region is empty (deep-modeling note only) => G-AX is a skip stub; refinement.md declares no A-consumed and no A-reference rows, consistent with the empty axioms region. All impl legs are R (type refinement str<->List Char) or R/I; the changed op (TextIOWrapper.read under newline="") is modeled DEEPLY as the identity scan, NOT axiomatized — so there is no A-leg correspondence to a real callee to validate, and no kind-3 (changed-inexpressible) leg. Correspondence is honest: post-patch identity <-> newline="" verbatim read; prepatch translation <-> newline=None universal-newline. Audit clean.

VERDICT: SOUND — 6 same-spec attacks run (>=5 floor), prepatch bug reproduced (atk_6), positive control verifies clean; none breaks the spec, and none even produces a clean-axiom-verifying candidate, so verify=>correct is upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification — turning the raw character stream that was written into the
-- capture buffer back into the text handed to the caller — is modeled DEEPLY as
-- the single read pass below, rather than abstracted behind any callee. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text read back out of a capture buffer must reproduce, character for
character, exactly the text that was written into it: nothing is dropped,
rewritten, merged, or inserted. The result is pinned entirely to the input
stream — the readback equals the written stream verbatim. -/
def problem_spec_readCaptured (written : List Char) (result : List Char) : Prop :=
  result = written
-- post-conditions-end

-- impl-start
/-- Read the buffered character stream back out. Each character that was written
is handed back unchanged, in order, with no transformation applied. -/
def implementation_readCaptured (written : List Char) : List Char := Id.run do
  let mut out : Array Char := #[]
  for c in written do
    out := out.push c
  return out.toList
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation over the array, generalized over the
accumulator: writing each character in order appends `written` to the running
array. Proven by induction with `List.forIn_cons`. -/
theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
    (forIn written init (fun c r =>
        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
    = pure (init ++ ⟨written⟩) := by
  induction written generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    apply congrArg
    apply Array.ext'
    simp

theorem correct_readCaptured :
    ∀ (written : List Char),
    problem_spec_readCaptured written (implementation_readCaptured written) := by
  intro written
  unfold problem_spec_readCaptured implementation_readCaptured
  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) verdict: SOUND. Spec byte-identical (same_spec=True for all 6 attacks + positive control, verified via swebench_unified.markers.same_spec). The frozen spec `problem_spec_readCaptured written result := result = written` is a TIGHT, SINGLE-VALUED identity contract: for each `written` exactly one satisfying `result` exists (= written verbatim). Any implementation whose `correct_readCaptured` closes with CLEAN axioms is therefore extensionally the identity on List Char, which IS exactly the post-patch (newline="") verbatim-readback behavior => it resolves. Divergence from `written` immediately falsifies `result = written`, so no closing clean-axiom impl maps to a non-resolving patch. verify => correct holds.

ATTACKS (6 distinct same-spec wrong impls, each a genuine closing attempt via `first | rfl | simp | decide`, all verified in /tmp): atk_1 partial/prepatch echo (map \r->\n); atk_2 boundary (written.tail, off-by-one); atk_3 control-flow effect (written ++ ['\n']); atk_4 ungrounded constant ([] always); atk_5 partial-domain (identity except ['x'] on empty input); atk_6 = the FAITHFUL prepatch bug (full universal-newline translation, byte-identical to Solution_prepatch.lean impl, prepatch_reproduced=true).

RESULTS (scripts/lean_verify.sh <f>, and adversary.check_attack): every one of atk_1..atk_6 => same_spec=True, verifies=FALSE (exit 1, unsolved/false goals) — the spec correctly REJECTS each. Concrete non-closures observed: atk_1 goal `List.map (...\r->\n) written = written` false; atk_2 `written.tail = written` false; atk_3 `... = written` reduces to `False`; atk_4 `written = []` false; atk_5 match-on-empty false; atk_6 forIn-translation != written. Because NO wrong impl closes with clean axioms, NO faithful-patch resolve run is mandated (the resolve step only triggers for a same-spec CLEAN-AXIOM-verifying candidate; there are none). Positive control (exact Solution.lean) verifies (exit 0) with `#print axioms correct_readCaptured` = [propext, Quot.sound] (clean).

AXIOM-INJECTION PROBE (atk_7, NOT submitted): a constant-empty impl "proven" via an injected `axiom cheat_readCaptured` in the proof region. It closes under lean_verify (exit 0, no sorry) but `#print axioms` = [cheat_readCaptured] — DIRTY, so it does NOT meet the clean-axiom break criterion and is not a spec weakness; strict G-VERIFY/G-HYGIENE reject it via gates/_lean_axioms.check_proof_axioms. I deliberately EXCLUDE it from `attacks`: (a) with no patch it would force a spurious INCONCLUSIVE, (b) with a non-resolving patch it would fabricate a false BROKEN — both dishonest given the axioms are unclean. HARNESS-HYGIENE NOTE (not a spec defect): adversary.check_attack -> _verify_attack -> check_bundle_file checks only compiles+no-sorry, NOT check_proof_axioms, so it reports atk_7 verifies=True; and _lean_axioms.declared_axiom_names scans the WHOLE file so an axiom declared in the (elided) proof region self-allowlists. This gap fails CLOSED for the spec question (it could only manufacture a false BROKEN, never let a weak spec pass), so it does not affect the G-EQ soundness of THIS bundle; flagged for maintainers.

REFINEMENT.MD A-LEG AUDIT: axioms region is empty (deep-modeling note only) => G-AX is a skip stub; refinement.md declares no A-consumed and no A-reference rows, consistent with the empty axioms region. All impl legs are R (type refinement str<->List Char) or R/I; the changed op (TextIOWrapper.read under newline="") is modeled DEEPLY as the identity scan, NOT axiomatized — so there is no A-leg correspondence to a real callee to validate, and no kind-3 (changed-inexpressible) leg. Correspondence is honest: post-patch identity <-> newline="" verbatim read; prepatch translation <-> newline=None universal-newline. Audit clean.

VERDICT: SOUND — 6 same-spec attacks run (>=5 floor), prepatch bug reproduced (atk_6), positive control verifies clean; none breaks the spec, and none even produces a clean-axiom-verifying candidate, so verify=>correct is upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-7521 lean bundle.

MODELED FUNCTION: implementation_readCaptured (post-patch) = identity copy of the written char stream; spec problem_spec_readCaptured := (result = written). This models FDCaptureBinary readback via EncodedFile(TemporaryFile, encoding='utf-8', errors='replace', newline='')  -> TextIOWrapper.read() in FDCapture.snap(). The patch adds newline='' which disables universal-newline translation, making read() verbatim.

REAL CALLEE CHECK: Reproduced the exact patched construction — io.TextIOWrapper(BytesIO(s.encode('utf-8')), encoding='utf-8', errors='replace', newline='') then .read(). Post-patch readback is VERBATIM for every input tried, so it agrees with the identity model on all of them. Tested: (a) the mapping.md/conformance fixed cases (\r, \n, \r\n, \r\r\n, x\r, '  0%\r', etc.) — all verbatim; (b) Unicode line-separator suspects U+2028, U+2029, U+0085 (NEL), \v, \f, \x1c-\x1e — all verbatim (newline='' also disables the extended Unicode newline handling, unlike newline=None); (c) 500,000 random strings drawn over the FULL Lean Char domain (0..0x10FFFF minus surrogates), lengths 0-12 — ZERO divergences; (d) all ordered pairs of newline-class code points — zero divergences. No input found where the real post-patch callee differs from the identity model. The spec is therefore NOT too strong: result=written holds on exactly the set where the real patched code returns text, over the whole modeled domain.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (spec region byte-identical; the elided spec view matches). Solution.lean compiles under lean_verify.sh (exit 0, no sorry). #print axioms correct_readCaptured => [propext, Quot.sound] only — no sorryAx, proof is real. Prepatch impl is genuine universal-newline translation and its correct_readCaptured is sorry (unclosable), so the spec genuinely discriminates the bug on \r / \r\n inputs (e.g. '  0%\r'). G-DIFF holds.

CONCLUSION: model faithfully tracks the real repo behavior; no divergence exists. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean) verified: axioms region is a generic meta-note naming no callee; pure region empty; post-conditions define problem_spec_readCaptured written result := result = written with a docstring describing verbatim character-for-character readback; impl and proof regions elided by spec_view. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical) and lexical leakage.screen passed (no hard failures).

The public problem_statement already fully states the desired behavior: capfd.readouterr() must NOT convert \r to \n; the reproducer does print(..., end='\r') and asserts out.endswith('\r'), i.e. carriage returns must survive readback verbatim. The spec view encodes exactly this publicly-stated contract (result = written). It does NOT name the gold edit mechanism or location: newline="", EncodedFile, TextIOWrapper, TemporaryFile, capture.py, FDCaptureBinary.__init__, or any line numbers appear ONLY in mapping.md / refinement.md, which are not part of the spec view. Nothing in the spec view points at the edit site or the newline flag beyond restating the public desired behavior. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
