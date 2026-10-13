# P2 adversarial audit — django__django-10914

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -64,7 +64,7 @@
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
     Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
+  let mut setting : Option Nat := none
   match projectSetting with
   | some v => setting := v
   | none   => pure ()
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
     Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
+  let mut setting : Option Nat := some 0o600
   match projectSetting with
   | some v => setting := v
   | none   => pure ()
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,10 @@
 -- impl-start
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
-    Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
-  match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
+    Option Nat :=
   match storageOverride with
-  | some m => return some m
-  | none   => return setting
+  | some m => some m
+  | none   => defaultUploadMode
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,12 @@
 -- impl-start
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
-    Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
+    Option Nat :=
   match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
-  match storageOverride with
-  | some m => return some m
-  | none   => return setting
+  | some v => v
+  | none   => match storageOverride with
+              | some m => some m
+              | none   => defaultUploadMode
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,8 @@
 -- impl-start
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
-    Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
-  match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
-  match storageOverride with
-  | some m => return some m
-  | none   => return setting
+    Option Nat :=
+  defaultUploadMode
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,12 @@
 -- impl-start
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
-    Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
-  match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
+    Option Nat :=
   match storageOverride with
-  | some m => return some m
-  | none   => return setting
+  | some m => some (m + 1)
+  | none   => match projectSetting with
+              | some v => v
+              | none   => defaultUploadMode
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,13 @@
 -- impl-start
 def implementation_effectiveFilePermissionsMode
     (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
-    Option Nat := Id.run do
-  let mut setting : Option Nat := defaultUploadMode
-  match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
+    Option Nat :=
   match storageOverride with
-  | some m => return some m
-  | none   => return setting
+  | some m => some m
+  | none   => match projectSetting with
+              | some (some k) => some k
+              | some none     => defaultUploadMode
+              | none          => defaultUploadMode
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the numeric permission mode that newly uploaded files are given by the
filesystem-backed storage.

The effective mode is decided in three layers, most specific first:

  * a per-storage-instance override (the mode passed when the storage object was
    constructed): if it carries a concrete mode, that mode wins outright;
  * otherwise the project-wide configured mode is consulted. The project may
    leave this unconfigured, in which case the framework's built-in default
    applies; or it may pin it to a concrete choice (which itself may be a
    definite mode or the explicit "no special mode" choice);
  * the framework's built-in default mode, used when nothing more specific was
    supplied.

A mode of "absent" (no concrete number) means the storage performs no explicit
permission adjustment and the surrounding operating-system behavior is left in
effect; a concrete number is the octal mode to apply.

The built-in default is a concrete, predictable mode (`0o644`) so that uploaded
files receive consistent permissions regardless of how the upload was buffered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The per-instance override, the
-- project-configured mode, and the built-in default all enter as plain data
-- (modeled as `Option`), and the only operation performed is the most-specific
-- wins selection, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default permission mode: a concrete octal mode
(`0o644`). `Option Nat` carries a permission mode, with `none` meaning "no
explicit mode" and `some m` the octal number `m`. -/
def defaultUploadMode : Option Nat := some 0o644
-- pure-end

-- post-conditions-start
/-- The resolved permission mode is fully pinned to the inputs:

  * if the per-storage override carries a concrete mode `m`, the result is
    exactly `some m` (the override wins, whatever the project setting);
  * if there is no per-storage override, the result is exactly the
    project-configured mode when one is configured, and otherwise the built-in
    default mode.

Both layers together determine the result for every input, so no output is left
free. -/
def problem_spec_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat))
    (result : Option Nat) : Prop :=
  (∀ m, storageOverride = some m → result = some m) ∧
  (storageOverride = none →
      result = (match projectSetting with
                | some v => v
                | none   => defaultUploadMode))
-- post-conditions-end

-- impl-start
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting
-- impl-end

-- proof-start
theorem correct_effectiveFilePermissionsMode :
    ∀ (storageOverride : Option Nat) (projectSetting : Option (Option Nat)),
      problem_spec_effectiveFilePermissionsMode storageOverride projectSetting
        (implementation_effectiveFilePermissionsMode storageOverride projectSetting) := by
  intro storageOverride projectSetting
  constructor
  · intro m hm
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hm]
    | some v => simp [implementation_effectiveFilePermissionsMode, hm]
  · intro hnone
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hnone]
    | some v => simp [implementation_effectiveFilePermissionsMode, hnone]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-10914 (lean). Spec is FUNCTIONAL: problem_spec_effectiveFilePermissionsMode pins the result uniquely for every input — clause A (∀ m, storageOverride=some m → result=some m) fixes the override case, clause B (storageOverride=none → result = match projectSetting | some v => v | none => defaultUploadMode) fixes the no-override case, with defaultUploadMode=some 0o644 frozen in the pure region. Hence any same-spec impl whose correct_ closes must equal the gold resolution pointwise → resolves identically. There is no closing-but-divergent impl, so verify⇒correct holds.

Same-spec confirmed via swebench_unified.markers.same_spec = True for all 7 attacks (spec/axioms/pure/pre/post byte-identical to Solution.lean; only impl region edited).

Attacks (all same-spec, distinct wrong impls; command: bash scripts/lean_verify.sh <atk>.lean):
- atk_1 = prepatch bug (default seed none): exit 1, unsolved goals (line 89, right.none clause) — reproduces the captured F2P bug (storageOverride=none,projectSetting=none returns none ≠ some 0o644).
- atk_2 = wrong default 0o600: exit 1, unsolved goals.
- atk_3 = ignore projectSetting (return defaultUploadMode on no-override): exit 1, unsolved goals.
- atk_4 = control-flow swap (projectSetting overrides storageOverride): exit 1, unsolved goals.
- atk_5 = ungrounded-oracle echo (constant defaultUploadMode): exit 1, unsolved goals (multiple).
- atk_6 = boundary off-by-one (override → some (m+1)): exit 1, unsolved goals.
- atk_7 = partial-domain (projectSetting=some none → defaultUploadMode instead of none): exit 1, unsolved goals.
NONE of the 7 closes → 0 candidates with clean-axiom proofs → protocol step 2 (materialize+resolve faithful patch) has no applicable candidate; patches={}. 

**Robustness:** atk_3 and atk_5 re-attempted with maximal tactics (unfold + refine + cases storageOverride <;> cases projectSetting <;> simp_all <;> omega <;> aesop) in atk_3_hard.lean / atk_5_hard.lean → both exit 1 (omega could not prove goal), confirming the goals are genuinely unprovable, not weak-tactic artifacts.

**Positive control:** pos_control.lean (byte-identical to Solution.lean) → exit 0. #print axioms correct_effectiveFilePermissionsMode (pos_axcheck.lean) → 'depends on axioms: [propext, Quot.sound]' — clean, no sorryAx.

refinement.md / meta.json audit: axioms=[], deep_model_references=[]; all 3 operation legs are R/I (leg1 I: defaultUploadMode=some 0o644 seed; leg2 R: Option(Option Nat) models declared-vs-default; leg3 R: `_value_or_setting` most-specific-wins). No A-consumed, no A-reference, NO kind-3 leg. No A-leg correspondence to callees to audit (none exist); R/I legs covered by G-CONF (100000 inputs, 0 disagreements per meta). Consistent and faithful.

**Verdict:** SOUND — ≥7 distinct same-spec wrong impls attempted, none verifies, positive control verifies with clean axioms, prepatch reproduced. verify⇒correct holds for this bundle.

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
import Mathlib
-- imports-end

/-!
Resolving the numeric permission mode that newly uploaded files are given by the
filesystem-backed storage.

The effective mode is decided in three layers, most specific first:

  * a per-storage-instance override (the mode passed when the storage object was
    constructed): if it carries a concrete mode, that mode wins outright;
  * otherwise the project-wide configured mode is consulted. The project may
    leave this unconfigured, in which case the framework's built-in default
    applies; or it may pin it to a concrete choice (which itself may be a
    definite mode or the explicit "no special mode" choice);
  * the framework's built-in default mode, used when nothing more specific was
    supplied.

A mode of "absent" (no concrete number) means the storage performs no explicit
permission adjustment and the surrounding operating-system behavior is left in
effect; a concrete number is the octal mode to apply.

The built-in default is a concrete, predictable mode (`0o644`) so that uploaded
files receive consistent permissions regardless of how the upload was buffered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The per-instance override, the
-- project-configured mode, and the built-in default all enter as plain data
-- (modeled as `Option`), and the only operation performed is the most-specific
-- wins selection, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default permission mode: a concrete octal mode
(`0o644`). `Option Nat` carries a permission mode, with `none` meaning "no
explicit mode" and `some m` the octal number `m`. -/
def defaultUploadMode : Option Nat := some 0o644
-- pure-end

-- post-conditions-start
/-- The resolved permission mode is fully pinned to the inputs:

  * if the per-storage override carries a concrete mode `m`, the result is
    exactly `some m` (the override wins, whatever the project setting);
  * if there is no per-storage override, the result is exactly the
    project-configured mode when one is configured, and otherwise the built-in
    default mode.

Both layers together determine the result for every input, so no output is left
free. -/
def problem_spec_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat))
    (result : Option Nat) : Prop :=
  (∀ m, storageOverride = some m → result = some m) ∧
  (storageOverride = none →
      result = (match projectSetting with
                | some v => v
                | none   => defaultUploadMode))
-- post-conditions-end

-- impl-start
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting
-- impl-end

-- proof-start
theorem correct_effectiveFilePermissionsMode :
    ∀ (storageOverride : Option Nat) (projectSetting : Option (Option Nat)),
      problem_spec_effectiveFilePermissionsMode storageOverride projectSetting
        (implementation_effectiveFilePermissionsMode storageOverride projectSetting) := by
  intro storageOverride projectSetting
  constructor
  · intro m hm
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hm]
    | some v => simp [implementation_effectiveFilePermissionsMode, hm]
  · intro hnone
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hnone]
    | some v => simp [implementation_effectiveFilePermissionsMode, hnone]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-10914 (lean). Spec is FUNCTIONAL: problem_spec_effectiveFilePermissionsMode pins the result uniquely for every input — clause A (∀ m, storageOverride=some m → result=some m) fixes the override case, clause B (storageOverride=none → result = match projectSetting | some v => v | none => defaultUploadMode) fixes the no-override case, with defaultUploadMode=some 0o644 frozen in the pure region. Hence any same-spec impl whose correct_ closes must equal the gold resolution pointwise → resolves identically. There is no closing-but-divergent impl, so verify⇒correct holds.

Same-spec confirmed via swebench_unified.markers.same_spec = True for all 7 attacks (spec/axioms/pure/pre/post byte-identical to Solution.lean; only impl region edited).

Attacks (all same-spec, distinct wrong impls; command: bash scripts/lean_verify.sh <atk>.lean):
- atk_1 = prepatch bug (default seed none): exit 1, unsolved goals (line 89, right.none clause) — reproduces the captured F2P bug (storageOverride=none,projectSetting=none returns none ≠ some 0o644).
- atk_2 = wrong default 0o600: exit 1, unsolved goals.
- atk_3 = ignore projectSetting (return defaultUploadMode on no-override): exit 1, unsolved goals.
- atk_4 = control-flow swap (projectSetting overrides storageOverride): exit 1, unsolved goals.
- atk_5 = ungrounded-oracle echo (constant defaultUploadMode): exit 1, unsolved goals (multiple).
- atk_6 = boundary off-by-one (override → some (m+1)): exit 1, unsolved goals.
- atk_7 = partial-domain (projectSetting=some none → defaultUploadMode instead of none): exit 1, unsolved goals.
NONE of the 7 closes → 0 candidates with clean-axiom proofs → protocol step 2 (materialize+resolve faithful patch) has no applicable candidate; patches={}. 

**Robustness:** atk_3 and atk_5 re-attempted with maximal tactics (unfold + refine + cases storageOverride <;> cases projectSetting <;> simp_all <;> omega <;> aesop) in atk_3_hard.lean / atk_5_hard.lean → both exit 1 (omega could not prove goal), confirming the goals are genuinely unprovable, not weak-tactic artifacts.

**Positive control:** pos_control.lean (byte-identical to Solution.lean) → exit 0. #print axioms correct_effectiveFilePermissionsMode (pos_axcheck.lean) → 'depends on axioms: [propext, Quot.sound]' — clean, no sorryAx.

refinement.md / meta.json audit: axioms=[], deep_model_references=[]; all 3 operation legs are R/I (leg1 I: defaultUploadMode=some 0o644 seed; leg2 R: Option(Option Nat) models declared-vs-default; leg3 R: `_value_or_setting` most-specific-wins). No A-consumed, no A-reference, NO kind-3 leg. No A-leg correspondence to callees to audit (none exist); R/I legs covered by G-CONF (100000 inputs, 0 disagreements per meta). Consistent and faithful.

**Verdict:** SOUND — ≥7 distinct same-spec wrong impls attempted, none verifies, positive control verifies with clean axioms, prepatch reproduced. verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) check for django__django-10914 lean bundle.

**MODELED FUNCTION:** FileSystemStorage.file_permissions_mode resolution via `_value_or_setting` layered over the (patched) FILE_UPLOAD_PERMISSIONS default. Real callee at worktree (post-patch, global_settings.py:319 FILE_UPLOAD_PERMISSIONS=0o644; storage.py:212-213 `_value_or_setting`(value,setting)=setting if value is None else value; :230-231 file_permissions_mode=`_value_or_setting`(self.`_file_permissions_mode`, settings.FILE_UPLOAD_PERMISSIONS)).

TYPE BIJECTION (matches mapping.md): storageOverride:Option Nat ↔ self.`_file_permissions_mode` (none↔None, some m↔int m); projectSetting:Option(Option Nat) ↔ resolved settings.FILE_UPLOAD_PERMISSIONS (outer none = left at built-in default 0o644; outer some v = project-declared v; inner none↔None, some k↔int k); result:Option Nat ↔ return. Octal 0o644=420 identical Python/Lean. defaultUploadMode=some 0o644 matches the patched default.

EXHAUSTIVE CASE EQUIVALENCE (impl vs real callee), all agree:
  (some m, *)      → model some m ; real: value=m≠None → m. ✓
  (none, some v)   → model v      ; real: value=None → setting=v. ✓
  (none, none)     → model some 0o644 ; real: value=None → setting=default 0o644. ✓
Edge inputs (some 0, large m, inner none) all covered by the same case split — no divergence.

**SPEC STRENGTH:** problem_spec is a total pinning of result to inputs: (∀m, override=some m → result=some m) ∧ (override=none → result = match projectSetting {some v=>v | none=>default}). This exactly characterizes the real callee's output for every input — neither too strong (no input the real callee produces is rejected) nor too weak. Not an echo/trivial-true spec: it fully determines result.

### Checks performed
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True → spec region byte-identical between post/prepatch; only impl initializer differs (0o644 vs none).
- lean_verify.sh exit 0 (compiles, no sorry/error).
- #print axioms correct_effectiveFilePermissionsMode = [propext, Quot.sound] — NO sorryAx; proof is genuine.
- Prepatch impl (seeds none) fails the no-override/no-project clause (returns none vs required some 0o644), consistent with F2P test test_override_file_upload_permissions. Confirms the spec discriminates the real bug.

**CONCLUSION:** No diverging input between the modeled function and the real repo callee. Spec is faithful and appropriately strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is a one-line default change in django/conf/global_settings.py: FILE_UPLOAD_PERMISSIONS None -> 0o644. The public problem_statement's TITLE already states 'Set default FILE_UPLOAD_PERMISSION to 0o644.' and its body discusses 'in absence of explicitly configured FILE_UPLOAD_PERMISSIONS'. So the specific gold value 0o644 and the fact that the default is set to it are already public.

Spec view (verified via markers.spec_view over lean backend; same_spec(Solution, Solution_prepatch)=True, spec region byte-identical, impl+proof elided) contains: (1) defaultUploadMode := some 0o644 and prose 'built-in default is a concrete, predictable mode (0o644)' — the value is precisely what problem_statement's title announces, not a leak beyond it. (2) The three-layer resolution model (per-storage override / project setting / built-in default) and problem_spec_effectiveFilePermissionsMode — this is the general permission-resolution structure needed to STATE any spec; it does not reveal the mechanical one-line edit site in global_settings.py. Nothing in the spec view reconstructs the gold edit beyond the public problem_statement. The only gold-specific token (0o644) is disclosed by problem_statement itself.

same_spec True confirms the prepatch/postpatch discriminator lives only in the elided impl initializer (none vs defaultUploadMode), so it never enters the public spec surface. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
