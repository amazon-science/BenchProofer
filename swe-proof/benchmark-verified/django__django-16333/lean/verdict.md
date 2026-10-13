# P2 adversarial audit — django__django-16333

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -88,21 +88,12 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
     let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
+    let relatedSaved : List Int := []
     if commit then
-      -- write the instance row …
       instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
     return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,9 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    return { user := user, instanceSaved := commit, relatedSaved := f.m2m }
 -- impl-end
 
 -- proof-start
@@ -111,5 +98,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,10 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    let relatedSaved : List Int := f.m2m
+    return { user := user, instanceSaved := commit, relatedSaved := relatedSaved }
 -- impl-end
 
 -- proof-start
@@ -111,5 +99,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,9 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    return { user := user, instanceSaved := true, relatedSaved := (if commit then f.m2m else []) }
 -- impl-end
 
 -- proof-start
@@ -111,5 +98,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,9 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    return { user := user, instanceSaved := commit, relatedSaved := (if commit then f.m2m.reverse else []) }
 -- impl-end
 
 -- proof-start
@@ -111,5 +98,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,8 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
-    let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
-    user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    let user := buildInstance f
+    return { user := user, instanceSaved := commit, relatedSaved := (if commit then f.m2m else []) }
 -- impl-end
 
 -- proof-start
@@ -111,5 +97,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,9 @@
 -- impl-start
 def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
   Id.run do
-    -- super().save(commit=False): build the instance and install the deferred
-    -- related-selection writer (so a writer is always present afterwards).
     let mut user := buildInstance f
-    let hasRelatedWriter := true
-    -- derive the stored password from the form's raw password (always).
     user := { user with passwordSet := true }
-    let mut instanceSaved := false
-    let mut relatedSaved : List Int := []
-    if commit then
-      -- write the instance row …
-      instanceSaved := true
-      -- … and, when the related-selection writer is present, write the form's
-      -- multi-valued related selections so they are not lost.
-      if hasRelatedWriter then
-        relatedSaved := f.m2m
-    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
+    return { user := user, instanceSaved := commit, relatedSaved := (if commit then (0 :: f.m2m) else []) }
 -- impl-end
 
 -- proof-start
@@ -111,5 +98,5 @@
     problem_spec_persistForm f commit (implementation_persistForm f commit) := by
   intro f commit
   unfold problem_spec_persistForm implementation_persistForm
-  cases commit <;> exact ⟨rfl, rfl, rfl⟩
+  cases commit <;> simp_all <;> exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Persisting a model-backed registration form.

A model-backed form, when asked to persist, builds a model instance from its
cleaned data, applies any derived field handling (here: deriving the stored
password from the supplied raw password), and — when the caller asks for an
immediate commit — writes the instance and ALSO writes the form's multi-valued
related selections so they are not lost. When the caller defers the commit,
nothing is written now: both the instance write and the related-selection write
are postponed.

The behavior exercised here is that a committed save of such a form persists
*both* the instance and the full set of multi-valued related selections the form
collected; a deferred save persists neither. The returned instance always carries
its derived password regardless of whether the save was committed. Every output
component is determined by the form's contents together with the commit choice.
-/

-- axioms-start
-- No UNCHANGED callee needs a consumed `opaque`/`axiom` contract here. The three
-- persistence sub-operations — building the instance from the form, writing the
-- instance, and writing the form's multi-valued related selections — are modeled
-- DEEPLY in the `pure`/impl regions as transformations of a `SaveOutcome` record
-- (A-reference: validated against the real persistence layer, not axiomatized).
-- The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A model-backed form, observed through only the features that determine what a
persist does:

  * `password` — the raw secret the stored password is derived from;
  * `m2m` — the identities of the multi-valued related selections the form
    collected (a list of related-object ids). -/
structure FormData where
  /-- the raw password supplied in the form -/
  password : String
  /-- the identities of the multi-valued related selections collected by the form -/
  m2m : List Int
deriving Repr

/-- The built model instance, observed through the only touched fact: whether its
derived (stored) password has been applied. -/
structure UserObj where
  /-- whether the stored password has been derived from the form's raw password -/
  passwordSet : Bool
deriving Repr

/-- The outcome of persisting the form:

  * `user` — the built instance (always returned);
  * `instanceSaved` — whether the instance row was written;
  * `relatedSaved` — the multi-valued related selections that were written. -/
structure SaveOutcome where
  /-- the built (and returned) model instance -/
  user : UserObj
  /-- whether the instance row was written -/
  instanceSaved : Bool
  /-- the multi-valued related selections that were written -/
  relatedSaved : List Int
deriving Repr

/-- Build the model instance from the form, deferring the commit. Building this
way installs the deferred related-selection writer on the form, so a writer is
always available afterwards. The freshly built instance has no derived password
yet. -/
def buildInstance (_f : FormData) : UserObj := { passwordSet := false }
-- pure-end

-- post-conditions-start
/-- Persisting a model-backed form. The returned instance always carries its
derived password. On a committed save the instance row is written and the full
set of the form's multi-valued related selections is written; on a deferred save
neither is written. Every output component is pinned to the form contents and the
commit choice (directive 5 frame: `user.passwordSet` always true,
`instanceSaved` = `commit`, `relatedSaved` grounded in `f.m2m`; directive 8:
`relatedSaved` is produced from the form's own selections, never an oracle). -/
def problem_spec_persistForm
    (f : FormData) (commit : Bool) (result : SaveOutcome) : Prop :=
  result.user.passwordSet = true ∧
  result.instanceSaved = commit ∧
  result.relatedSaved = (if commit then f.m2m else [])
-- post-conditions-end

-- impl-start
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  Id.run do
    -- super().save(commit=False): build the instance and install the deferred
    -- related-selection writer (so a writer is always present afterwards).
    let mut user := buildInstance f
    let hasRelatedWriter := true
    -- derive the stored password from the form's raw password (always).
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      -- write the instance row …
      instanceSaved := true
      -- … and, when the related-selection writer is present, write the form's
      -- multi-valued related selections so they are not lost.
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
-- impl-end

-- proof-start
theorem correct_persistForm : ∀ (f : FormData) (commit : Bool),
    problem_spec_persistForm f commit (implementation_persistForm f commit) := by
  intro f commit
  unfold problem_spec_persistForm implementation_persistForm
  cases commit <;> exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec=True (byte-identical axioms/pure/pre/post; only impl edited), verified via swebench_unified.markers.same_spec.

SPEC ANALYSIS: problem_spec_persistForm is TOTAL and DETERMINISTIC — it pins all three SaveOutcome components as pure functions of (f, commit): result.user.passwordSet = true, result.instanceSaved = commit, result.relatedSaved = (if commit then f.m2m else []). Therefore any impl that closes correct_persistForm must compute exactly the reference output; no same-spec wrong impl can verify.

POSITIVE CONTROL: cmd `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0. `#print axioms correct_persistForm` -> "does not depend on any axioms" (clean, no sorry).

### ATTACKS (cmd `bash scripts/lean_verify.sh .../atk_N.lean`):
- atk_1 prepatch bug (relatedSaved always [] on commit): exit 1. PREPATCH REPRODUCED — matches Solution_prepatch.lean semantics; carried proof cannot close.
- atk_2 partial-domain (relatedSaved=f.m2m ignoring commit; wrong on commit=false): exit 1.
- atk_3 boundary (relatedSaved=f.m2m always): exit 1.
- atk_4 control-flow-effect (instanceSaved always true): exit 1.
- atk_5 ungrounded-oracle echo (relatedSaved=f.m2m.reverse on commit — permutation not identity): exit 1.
- atk_6 passwordSet left false (set_password not applied): exit 1.
- atk_7 off-by-one boundary (0 :: f.m2m): exit 1.
Ran concurrently in batches of 4 (background Bash jobs). Re-ran all as robust variants atk_2b..7b with closing tactic `cases commit <;> simp_all`; every one still failed with genuine `error: unsolved goals` — confirming true spec mismatch, not a tactic artifact.

No wrong impl produced a closing clean-axiom proof, so patches={} and no run_resolve was required (nothing to materialize; the definition of BROKEN — a verifying wrong impl whose faithful patch fails to resolve — is vacuously not met).

REFINEMENT AUDIT (refinement.md): rows 1-5 A-reference, row 6 I. No A-consumed, no kind-3 (changed-inexpressible) rows. Axioms region is empty and pos_control proof depends on NO axioms — so the A-reference legs are realized as concrete, fully-determined SaveOutcome data transformations rather than opaque contracts. The correspondence holds: buildInstance/hasRelatedWriter <- super().save(commit=False) (builds instance + installs deferred m2m writer); passwordSet:=true <- user.set_password(...); instanceSaved:=commit <- if commit: user.save(); relatedSaved:=f.m2m (the changed line, inside commit branch) <- if hasattr(self,'save_m2m'): self.save_m2m(). The discriminating clause is row 5 (committed save must write f.m2m), exactly the F2P test test_custom_form_saves_many_to_many_field. verify => correct holds.

Verdict SOUND: 7 distinct same-spec wrong impls (>=5 required) all verified to FAIL to close; positive control closes with clean axioms; refinement legs faithful.

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
Persisting a model-backed registration form.

A model-backed form, when asked to persist, builds a model instance from its
cleaned data, applies any derived field handling (here: deriving the stored
password from the supplied raw password), and — when the caller asks for an
immediate commit — writes the instance and ALSO writes the form's multi-valued
related selections so they are not lost. When the caller defers the commit,
nothing is written now: both the instance write and the related-selection write
are postponed.

The behavior exercised here is that a committed save of such a form persists
*both* the instance and the full set of multi-valued related selections the form
collected; a deferred save persists neither. The returned instance always carries
its derived password regardless of whether the save was committed. Every output
component is determined by the form's contents together with the commit choice.
-/

-- axioms-start
-- No UNCHANGED callee needs a consumed `opaque`/`axiom` contract here. The three
-- persistence sub-operations — building the instance from the form, writing the
-- instance, and writing the form's multi-valued related selections — are modeled
-- DEEPLY in the `pure`/impl regions as transformations of a `SaveOutcome` record
-- (A-reference: validated against the real persistence layer, not axiomatized).
-- The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A model-backed form, observed through only the features that determine what a
persist does:

  * `password` — the raw secret the stored password is derived from;
  * `m2m` — the identities of the multi-valued related selections the form
    collected (a list of related-object ids). -/
structure FormData where
  /-- the raw password supplied in the form -/
  password : String
  /-- the identities of the multi-valued related selections collected by the form -/
  m2m : List Int
deriving Repr

/-- The built model instance, observed through the only touched fact: whether its
derived (stored) password has been applied. -/
structure UserObj where
  /-- whether the stored password has been derived from the form's raw password -/
  passwordSet : Bool
deriving Repr

/-- The outcome of persisting the form:

  * `user` — the built instance (always returned);
  * `instanceSaved` — whether the instance row was written;
  * `relatedSaved` — the multi-valued related selections that were written. -/
structure SaveOutcome where
  /-- the built (and returned) model instance -/
  user : UserObj
  /-- whether the instance row was written -/
  instanceSaved : Bool
  /-- the multi-valued related selections that were written -/
  relatedSaved : List Int
deriving Repr

/-- Build the model instance from the form, deferring the commit. Building this
way installs the deferred related-selection writer on the form, so a writer is
always available afterwards. The freshly built instance has no derived password
yet. -/
def buildInstance (_f : FormData) : UserObj := { passwordSet := false }
-- pure-end

-- post-conditions-start
/-- Persisting a model-backed form. The returned instance always carries its
derived password. On a committed save the instance row is written and the full
set of the form's multi-valued related selections is written; on a deferred save
neither is written. Every output component is pinned to the form contents and the
commit choice (directive 5 frame: `user.passwordSet` always true,
`instanceSaved` = `commit`, `relatedSaved` grounded in `f.m2m`; directive 8:
`relatedSaved` is produced from the form's own selections, never an oracle). -/
def problem_spec_persistForm
    (f : FormData) (commit : Bool) (result : SaveOutcome) : Prop :=
  result.user.passwordSet = true ∧
  result.instanceSaved = commit ∧
  result.relatedSaved = (if commit then f.m2m else [])
-- post-conditions-end

-- impl-start
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  Id.run do
    -- super().save(commit=False): build the instance and install the deferred
    -- related-selection writer (so a writer is always present afterwards).
    let mut user := buildInstance f
    let hasRelatedWriter := true
    -- derive the stored password from the form's raw password (always).
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      -- write the instance row …
      instanceSaved := true
      -- … and, when the related-selection writer is present, write the form's
      -- multi-valued related selections so they are not lost.
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
-- impl-end

-- proof-start
theorem correct_persistForm : ∀ (f : FormData) (commit : Bool),
    problem_spec_persistForm f commit (implementation_persistForm f commit) := by
  intro f commit
  unfold problem_spec_persistForm implementation_persistForm
  cases commit <;> exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec=True (byte-identical axioms/pure/pre/post; only impl edited), verified via swebench_unified.markers.same_spec.

SPEC ANALYSIS: problem_spec_persistForm is TOTAL and DETERMINISTIC — it pins all three SaveOutcome components as pure functions of (f, commit): result.user.passwordSet = true, result.instanceSaved = commit, result.relatedSaved = (if commit then f.m2m else []). Therefore any impl that closes correct_persistForm must compute exactly the reference output; no same-spec wrong impl can verify.

POSITIVE CONTROL: cmd `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0. `#print axioms correct_persistForm` -> "does not depend on any axioms" (clean, no sorry).

### ATTACKS (cmd `bash scripts/lean_verify.sh .../atk_N.lean`):
- atk_1 prepatch bug (relatedSaved always [] on commit): exit 1. PREPATCH REPRODUCED — matches Solution_prepatch.lean semantics; carried proof cannot close.
- atk_2 partial-domain (relatedSaved=f.m2m ignoring commit; wrong on commit=false): exit 1.
- atk_3 boundary (relatedSaved=f.m2m always): exit 1.
- atk_4 control-flow-effect (instanceSaved always true): exit 1.
- atk_5 ungrounded-oracle echo (relatedSaved=f.m2m.reverse on commit — permutation not identity): exit 1.
- atk_6 passwordSet left false (set_password not applied): exit 1.
- atk_7 off-by-one boundary (0 :: f.m2m): exit 1.
Ran concurrently in batches of 4 (background Bash jobs). Re-ran all as robust variants atk_2b..7b with closing tactic `cases commit <;> simp_all`; every one still failed with genuine `error: unsolved goals` — confirming true spec mismatch, not a tactic artifact.

No wrong impl produced a closing clean-axiom proof, so patches={} and no run_resolve was required (nothing to materialize; the definition of BROKEN — a verifying wrong impl whose faithful patch fails to resolve — is vacuously not met).

REFINEMENT AUDIT (refinement.md): rows 1-5 A-reference, row 6 I. No A-consumed, no kind-3 (changed-inexpressible) rows. Axioms region is empty and pos_control proof depends on NO axioms — so the A-reference legs are realized as concrete, fully-determined SaveOutcome data transformations rather than opaque contracts. The correspondence holds: buildInstance/hasRelatedWriter <- super().save(commit=False) (builds instance + installs deferred m2m writer); passwordSet:=true <- user.set_password(...); instanceSaved:=commit <- if commit: user.save(); relatedSaved:=f.m2m (the changed line, inside commit branch) <- if hasattr(self,'save_m2m'): self.save_m2m(). The discriminating clause is row 5 (committed save must write f.m2m), exactly the F2P test test_custom_form_saves_many_to_many_field. verify => correct holds.

Verdict SOUND: 7 distinct same-spec wrong impls (>=5 required) all verified to FAIL to close; positive control closes with clean axioms; refinement legs faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: UserCreationForm.save(self, commit) (django/contrib/auth/forms.py:139-145 @ base 60a7bd89, post-patch body). Lean impl_persistForm : FormData → Bool → SaveOutcome.

COMPILE/AXIOM: Solution.lean compiles clean (lean_verify exit 0, no sorry). `#print axioms correct_persistForm` → 'does not depend on any axioms' (no sorryAx; proof is genuine).

SPEC-REGION IDENTITY: same_spec(Solution, Solution_prepatch, lean tables) = True — spec region byte-identical; prepatch differs only in impl/proof (drops the m2m write) → valid G-DIFF signal, not a spec change.

FAITHFULNESS vs real callee, clause by clause:
1. result.user.passwordSet = true (always): real set_password() runs unconditionally BEFORE the `if commit` guard → returned user always has password derived. FAITHFUL.
2. result.instanceSaved = commit: real `if commit: user.save()` gates the row write exactly on commit. FAITHFUL.
3. result.relatedSaved = if commit then f.m2m else []: post-patch adds `if hasattr(self,'save_m2m'): self.save_m2m()` inside the commit block. Verified in real source that super().save(commit=False) resolves to BaseModelForm.save(commit=False) (django/forms/models.py:547) which UNCONDITIONALLY sets `self.save_m2m = self._save_m2m`. Hence on this code path hasattr is ALWAYS True — the guard is purely defensive — so modeling hasRelatedWriter := true is faithful, not spec-too-strong. _save_m2m (forms/models.py:505) writes exactly the form's collected m2m/cleaned selections → abstracted as f.m2m. On deferred save nothing runs → []. FAITHFUL.

Searched for a diverging input: (a) commit=True with save_m2m absent — unreachable, since the commit=False sub-call always installs it; (b) ordering/duplicate concerns on relatedSaved as List Int — relatedSaved and f.m2m share the same abstract source (the selections _save_m2m writes), so the deep-model (A-reference) abstraction is internally consistent and agrees with the callee. No mapped (f, commit) input makes problem_spec disagree with the real function. G-CONF is a legitimate conf_skip (pure ORM-persistence A-reference ops, no standalone stdlib-shadowable transform). Spec is NOT too strong / does not drift. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen (lean flavor) over the projected spec_view returns PASSED with zero hard failures: no diff markers, no gold-patch line reproduced (the added `if hasattr(self, "save_m2m"):` / `self.save_m2m()` do not appear), no patched file path (`django/contrib/auth/forms.py`) or module path, no narration terms, and no spec-view identifier/comment embedding the only distinctive patched symbol (`save`). same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical). The impl (`hasRelatedWriter`, `implementation_persistForm`) and proof are elided from the consumer view; only the docstring, structures, `buildInstance`, and `problem_spec_persistForm` are visible. The public problem_statement itself already fully discloses the edit (it names `self.save_m2m()` and the ManyToMany-save requirement); the spec view describes the same behavior more abstractly (`relatedSaved = if commit then f.m2m else []`) and even avoids the literal `save_m2m` token, so it reveals nothing about the gold edit beyond the public problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
