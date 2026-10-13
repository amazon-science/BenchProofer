# P2 adversarial audit — sphinx-doc__sphinx-9320

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_validateRootEntry is a FULLY-PINNED total specification: it constrains BOTH branches to exact functions of the input (x="" -> result = Except.ok x, i.e. .ok ""; and x != "" -> result = checkExistingDir x). Any impl that verifies must therefore be pointwise-identical to gold on the observable outcome. No same-spec wrong impl can close its proof, so verify => correct holds and there is no verifying-but-incorrect impl to materialize a non-resolving patch from.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,6 @@
 -- impl-start
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
-    if x == "" then
-      return Except.ok x
     return checkExistingDir x
 -- impl-end
 
@@ -60,12 +58,10 @@
       problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
   intro x
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
-  by_cases h : x = ""
-  · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
-    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
-    simp only [Id.run, hne]
+  refine ⟨fun hx => ?_, fun hx => ?_⟩
+  · subst hx
+    simp only [Id.run]
+    rfl
+  · simp only [Id.run]
     rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
 -- impl-start
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
-    if x == "" then
+    if x == " " then
       return Except.ok x
     return checkExistingDir x
 -- impl-end
@@ -62,10 +62,9 @@
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
   by_cases h : x = ""
   · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
-    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
-    simp only [Id.run, hne]
+    refine ⟨fun _ => ?_, fun hx => absurd rfl hx⟩
+    simp only [Id.run]
     rfl
+  · refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
+    by_cases hs : x = " " <;> simp_all [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
     if x == "" then
-      return Except.ok x
+      return Except.error "rejected"
     return checkExistingDir x
 -- impl-end
 
@@ -62,9 +62,10 @@
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
   by_cases h : x = ""
   · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
+    refine ⟨fun _ => ?_, fun hx => absurd rfl hx⟩
+    simp only [Id.run]
+    rfl
+  · have hne : (x == "") = false := by simp [beq_eq_false_iff_ne, h]
     refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
     simp only [Id.run, hne]
     rfl
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,9 +49,7 @@
 -- impl-start
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
-    if x == "" then
-      return Except.ok x
-    return checkExistingDir x
+    return Except.ok x
 -- impl-end
 
 -- proof-start
@@ -60,12 +58,9 @@
       problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
   intro x
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
-  by_cases h : x = ""
-  · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
-    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
-    simp only [Id.run, hne]
+  refine ⟨fun _ => ?_, fun _ => ?_⟩
+  · simp only [Id.run]
+    rfl
+  · simp only [Id.run]
     rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,8 +50,8 @@
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
     if x == "" then
-      return Except.ok x
-    return checkExistingDir x
+      return checkExistingDir x
+    return Except.ok x
 -- impl-end
 
 -- proof-start
@@ -62,9 +62,10 @@
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
   by_cases h : x = ""
   · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
+    refine ⟨fun _ => ?_, fun hx => absurd rfl hx⟩
+    simp only [Id.run]
+    rfl
+  · have hne : (x == "") = false := by simp [beq_eq_false_iff_ne, h]
     refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
     simp only [Id.run, hne]
     rfl
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,9 +49,7 @@
 -- impl-start
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
-    if x == "" then
-      return Except.ok x
-    return checkExistingDir x
+    return Except.error "nope"
 -- impl-end
 
 -- proof-start
@@ -60,12 +58,5 @@
       problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
   intro x
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
-  by_cases h : x = ""
-  · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
-    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
-    simp only [Id.run, hne]
-    rfl
+  refine ⟨fun _ => ?_, fun _ => ?_⟩ <;> simp only [Id.run] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
 def implementation_validateRootEntry (x : String) : Except String String :=
   Id.run do
     if x == "" then
-      return Except.ok x
+      return Except.ok "x"
     return checkExistingDir x
 -- impl-end
 
@@ -62,9 +62,10 @@
   unfold problem_spec_validateRootEntry implementation_validateRootEntry
   by_cases h : x = ""
   · subst h
-    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
-  · have hne : (x == "") = false := by
-      simp [beq_eq_false_iff_ne, h]
+    refine ⟨fun _ => ?_, fun hx => absurd rfl hx⟩
+    simp only [Id.run]
+    rfl
+  · have hne : (x == "") = false := by simp [beq_eq_false_iff_ne, h]
     refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
     simp only [Id.run, hne]
     rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating the entry a user supplies at the "enter a new root path (or just
Enter to exit)" prompt.

The entry is interpreted as follows:

  * an EMPTY entry is accepted verbatim — the caller reads back the empty value
    and treats it as the user declining to supply a path (so the surrounding
    flow can stop);
  * a NON-EMPTY entry must name an existing directory: it is handed to the
    standard existing-directory validator, which either returns the validated
    entry or reports a validation error.

We model the validator's result as `Except String String`: a `.ok s` is an
accepted entry `s`; a `.error m` is a validation error with message `m`. The
existing-directory validator is an unchanged input routine, modeled as an opaque
callee `checkExistingDir` so it appears identically in the specification and the
implementation; the specification pins only WHICH entries reach it.
-/

-- axioms-start
-- The existing-directory validator is an UNCHANGED library routine: given a
-- candidate entry it returns the validated entry (`.ok`) or a validation error
-- (`.error`). It is modeled as an opaque callee so the same routine appears in
-- both the specification and the implementation (an A-reference that cancels in
-- the differential), since the behavior of interest is WHICH entries are routed
-- to it, not what it computes. No property of this callee is consumed by the
-- proof, so no `axiom … _prop` is declared.
opaque checkExistingDir : String → Except String String
-- axioms-end

-- pure-start
-- (No additional pure helpers are needed.)
-- pure-end

-- post-conditions-start
/-- The validated result for an entry `x`. An empty entry is accepted verbatim
(`.ok x`, i.e. `.ok ""`); a non-empty entry yields exactly the existing-directory
validator's result for that entry. Every case is pinned to the input. -/
def problem_spec_validateRootEntry
    (x : String) (result : Except String String) : Prop :=
  (x = "" → result = Except.ok x) ∧
  (x ≠ "" → result = checkExistingDir x)
-- post-conditions-end

-- impl-start
def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir x
-- impl-end

-- proof-start
theorem correct_validateRootEntry :
    ∀ (x : String),
      problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  · have hne : (x == "") = false := by
      simp [beq_eq_false_iff_ne, h]
    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, hne]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: All work same_spec (lean backend) = True for all 7 attacks + pos_control (axioms/pure/pre/post left byte-identical; only impl+proof region edited). Verifications run concurrently as background jobs, <=4 at a time. Command per file: `bash scripts/lean_verify.sh <file>` from project root with.

### RESULTS (exit code / behavior):
- pos_control.lean (gold impl): exit 0 (verifies). `#print axioms correct_validateRootEntry` => depends on axioms: [propext] only — CLEAN, no sorryAx.
- atk_1 (prepatch bug: `return checkExistingDir x` for ALL x): exit 1. Genuine failure: `pure (checkExistingDir "") = Except.ok ""` unprovable (checkExistingDir opaque). => PREPATCH REPRODUCED.
- atk_2 (single-space discriminator `x == " "` instead of `""`, boundary): exit 1. Unsolved goals on x="" and x=" " branches.
- atk_3 (empty entry returns `.error "rejected"`, control-flow-effect): exit 1. `Except.error "rejected" = Except.ok ""` unprovable.
- atk_4 (ungrounded oracle echo: always `.ok x`): exit 1. Fails nonempty branch `pure (Except.ok x) = checkExistingDir x`.
- atk_5 (swapped branches: empty->delegate, nonempty->.ok x): exit 1. Fails BOTH branches.
- atk_6 (constant `.error "nope"` for all x, partial/degenerate domain): exit 1. Fails both branches.
- atk_7 (empty -> `.ok "x"`, wrong accepted value): exit 1. `Except.ok "x" = Except.ok ""` unprovable.

All 7 same-spec wrong impls FAIL to close with real unsolved-goals/`rfl`-mismatch errors on exactly the discriminating clause(s) — none produces a clean-axiom closing proof. STEP 2 (materialize faithful refined patch + run_resolve) is therefore VACUOUS: there is no verifying-but-incorrect impl. patches={} accordingly.

A-LEG / refinement.md AUDIT: Legs are R (op1 x:String, op2 Except carrier), I (op3 empty-branch, deeply modeled as direct .ok x write — NOT axiomatized), A-reference (op4 checkExistingDir <-> is_path). No kind-3 answer-key leg. The single A-reference `opaque checkExistingDir` occurs byte-identically in the spec's non-empty clause and the impl's non-empty branch, cancels in the differential, and the proof consumes NO property of it (empty branch discharged structurally; nonempty branch is a syntactic identity) — so no `axiom ..._prop` is declared and G-AX is a legitimate skip stub. Correspondence to the real callee (is_path, sphinx/cmd/quickstart.py:90-94, unchanged by patch) holds per mapping.md. G-CONF differential-tests the R/I routing (empty-accept vs delegate) with the existing-dir validator shared/cancelled between oracle and shadow — sound.

CONCLUSION: verify => correct is preserved; spec is not too weak. VERDICT SOUND (>=5 distinct attacks run — 7 total; none breaks the spec; positive control verifies with clean axioms).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_validateRootEntry is a FULLY-PINNED total specification: it constrains BOTH branches to exact functions of the input (x="" -> result = Except.ok x, i.e. .ok ""; and x != "" -> result = checkExistingDir x). Any impl that verifies must therefore be pointwise-identical to gold on the observable outcome. No same-spec wrong impl can close its proof, so verify => correct holds and there is no verifying-but-incorrect impl to materialize a non-resolving patch from.
```

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
import Mathlib
-- imports-end

/-!
Validating the entry a user supplies at the "enter a new root path (or just
Enter to exit)" prompt.

The entry is interpreted as follows:

  * an EMPTY entry is accepted verbatim — the caller reads back the empty value
    and treats it as the user declining to supply a path (so the surrounding
    flow can stop);
  * a NON-EMPTY entry must name an existing directory: it is handed to the
    standard existing-directory validator, which either returns the validated
    entry or reports a validation error.

We model the validator's result as `Except String String`: a `.ok s` is an
accepted entry `s`; a `.error m` is a validation error with message `m`. The
existing-directory validator is an unchanged input routine, modeled as an opaque
callee `checkExistingDir` so it appears identically in the specification and the
implementation; the specification pins only WHICH entries reach it.
-/

-- axioms-start
-- The existing-directory validator is an UNCHANGED library routine: given a
-- candidate entry it returns the validated entry (`.ok`) or a validation error
-- (`.error`). It is modeled as an opaque callee so the same routine appears in
-- both the specification and the implementation (an A-reference that cancels in
-- the differential), since the behavior of interest is WHICH entries are routed
-- to it, not what it computes. No property of this callee is consumed by the
-- proof, so no `axiom … _prop` is declared.
opaque checkExistingDir : String → Except String String
-- axioms-end

-- pure-start
-- (No additional pure helpers are needed.)
-- pure-end

-- post-conditions-start
/-- The validated result for an entry `x`. An empty entry is accepted verbatim
(`.ok x`, i.e. `.ok ""`); a non-empty entry yields exactly the existing-directory
validator's result for that entry. Every case is pinned to the input. -/
def problem_spec_validateRootEntry
    (x : String) (result : Except String String) : Prop :=
  (x = "" → result = Except.ok x) ∧
  (x ≠ "" → result = checkExistingDir x)
-- post-conditions-end

-- impl-start
def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir x
-- impl-end

-- proof-start
theorem correct_validateRootEntry :
    ∀ (x : String),
      problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  · have hne : (x == "") = false := by
      simp [beq_eq_false_iff_ne, h]
    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, hne]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: All work same_spec (lean backend) = True for all 7 attacks + pos_control (axioms/pure/pre/post left byte-identical; only impl+proof region edited). Verifications run concurrently as background jobs, <=4 at a time. Command per file: `bash scripts/lean_verify.sh <file>` from project root with.

### RESULTS (exit code / behavior):
- pos_control.lean (gold impl): exit 0 (verifies). `#print axioms correct_validateRootEntry` => depends on axioms: [propext] only — CLEAN, no sorryAx.
- atk_1 (prepatch bug: `return checkExistingDir x` for ALL x): exit 1. Genuine failure: `pure (checkExistingDir "") = Except.ok ""` unprovable (checkExistingDir opaque). => PREPATCH REPRODUCED.
- atk_2 (single-space discriminator `x == " "` instead of `""`, boundary): exit 1. Unsolved goals on x="" and x=" " branches.
- atk_3 (empty entry returns `.error "rejected"`, control-flow-effect): exit 1. `Except.error "rejected" = Except.ok ""` unprovable.
- atk_4 (ungrounded oracle echo: always `.ok x`): exit 1. Fails nonempty branch `pure (Except.ok x) = checkExistingDir x`.
- atk_5 (swapped branches: empty->delegate, nonempty->.ok x): exit 1. Fails BOTH branches.
- atk_6 (constant `.error "nope"` for all x, partial/degenerate domain): exit 1. Fails both branches.
- atk_7 (empty -> `.ok "x"`, wrong accepted value): exit 1. `Except.ok "x" = Except.ok ""` unprovable.

All 7 same-spec wrong impls FAIL to close with real unsolved-goals/`rfl`-mismatch errors on exactly the discriminating clause(s) — none produces a clean-axiom closing proof. STEP 2 (materialize faithful refined patch + run_resolve) is therefore VACUOUS: there is no verifying-but-incorrect impl. patches={} accordingly.

A-LEG / refinement.md AUDIT: Legs are R (op1 x:String, op2 Except carrier), I (op3 empty-branch, deeply modeled as direct .ok x write — NOT axiomatized), A-reference (op4 checkExistingDir <-> is_path). No kind-3 answer-key leg. The single A-reference `opaque checkExistingDir` occurs byte-identically in the spec's non-empty clause and the impl's non-empty branch, cancels in the differential, and the proof consumes NO property of it (empty branch discharged structurally; nonempty branch is a syntactic identity) — so no `axiom ..._prop` is declared and G-AX is a legitimate skip stub. Correspondence to the real callee (is_path, sphinx/cmd/quickstart.py:90-94, unchanged by patch) holds per mapping.md. G-CONF differential-tests the R/I routing (empty-accept vs delegate) with the existing-dir validator shared/cancelled between oracle and shadow — sound.

CONCLUSION: verify => correct is preserved; spec is not too weak. VERDICT SOUND (>=5 distinct attacks run — 7 total; none breaks the spec; positive control verifies with clean axioms).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for the modeled function is_path_or_empty (sphinx/cmd/quickstart.py:115-118 in the worktree). Real code: `def is_path_or_empty(x): if not x: return ''; return is_path(x)`. For a str, `if not x` is exactly `x == ''`, so: empty entry -> returns '' (verbatim empty), non-empty -> delegates unchanged to is_path. Spec problem_spec_validateRootEntry: (x="" -> result = .ok x) AND (x!="" -> result = checkExistingDir x). The empty branch pins .ok x = .ok "" which matches `return ''`; the non-empty branch is pinned to the opaque callee checkExistingDir, which is the SAME A-reference standing in for the unchanged is_path and appears identically in spec and impl, so it imposes no extra constraint on the real validator — the spec cannot be too strong on the delegated leg. Every input is covered by exactly one branch with no unconstrained/underdetermined result and no over-restriction. No diverging input exists between the modeled function and the real callee. Checks performed: same_spec(Solution, prepatch)=True via LeanBackend.language tables; lean_verify.sh exit 0 (compiles, no sorry); `#print axioms correct_validateRootEntry` = [propext] only (clean, no sorryAx — proof genuine). Spec region byte-identical between Solution.lean and Solution_prepatch.lean.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl + proof elided; verified via markers.spec_view over LeanBackend.language, and same_spec vs Solution_prepatch.lean = True) exposes only: (a) docstrings stating empty entry accepted verbatim so the surrounding flow can stop, and non-empty entry routed to a standard existing-directory validator; (b) an abstractly-named opaque callee `checkExistingDir` (NOT the gold name `is_path`); (c) `problem_spec_validateRootEntry`: (x="" → result=Except.ok x) ∧ (x≠"" → result=checkExistingDir x). Compared against the PUBLIC problem_statement, which already states: pressing Enter (empty entry) at 'enter a new root path (or just Enter to exit)' must NOT error with 'Please enter a valid path name' and instead 'After pressing Enter, sphinx-quickstart exits'; non-empty entries stay subject to path-name validation. The spec merely formalizes this publicly-stated input→outcome behavior. It does NOT reveal the gold EDIT's identifying specifics beyond the public statement: it never names the gold-added function `is_path_or_empty`, never mentions the do_prompt validator swap at the call site (line 232), and never mentions the pre-existing `sys.exit(1)` guard. Modeling names (validateRootEntry, checkExistingDir) are abstract, not lifted from the patch. The 'so the surrounding flow can stop' phrasing maps directly to problem_statement's 'sphinx-quickstart exits' — not new information. No spec-view line leaks the gold edit beyond problem_statement (hints_text excluded from the baseline, and the hint 'exit with status 1 immediately' is not needed to derive this spec).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
