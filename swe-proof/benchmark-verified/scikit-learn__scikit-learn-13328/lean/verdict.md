# P2 adversarial audit — scikit-learn__scikit-learn-13328

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,10 @@
 -- impl-start
 def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
   let mut dt := orig
-  if orig ∈ acceptedKinds then
+  if orig = NpKind.object then
+    dt := NpKind.float64
+  else
     dt := orig
-  else
-    dt := defaultKind
   return dt
 -- impl-end
 
@@ -72,11 +72,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,6 +62,8 @@
   let mut dt := orig
   if orig ∈ acceptedKinds then
     dt := orig
+  else if orig = NpKind.object then
+    dt := NpKind.float32
   else
     dt := defaultKind
   return dt
@@ -72,11 +74,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
-  let mut dt := orig
-  if orig ∈ acceptedKinds then
-    dt := orig
-  else
-    dt := defaultKind
+def implementation_prepareInput (_orig : NpKind) : NpKind := Id.run do
+  let mut dt := NpKind.float64
+  dt := defaultKind
   return dt
 -- impl-end
 
@@ -72,11 +69,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,9 @@
 def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
   let mut dt := orig
   if orig ∈ acceptedKinds then
+    dt := defaultKind
+  else
     dt := orig
-  else
-    dt := defaultKind
   return dt
 -- impl-end
 
@@ -72,11 +72,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,7 @@
 -- impl-start
 def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
   let mut dt := orig
-  if orig ∈ acceptedKinds then
-    dt := orig
-  else
-    dt := defaultKind
+  dt := orig
   return dt
 -- impl-end
 
@@ -72,11 +69,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   if orig ∈ acceptedKinds then
     dt := orig
   else
-    dt := defaultKind
+    dt := NpKind.int64
   return dt
 -- impl-end
 
@@ -72,11 +72,7 @@
     ∀ (orig : NpKind),
       problem_spec_prepareInput orig (implementation_prepareInput orig) := by
   intro orig
-  unfold problem_spec_prepareInput implementation_prepareInput
-  simp only [Id.run]
-  by_cases h : orig ∈ acceptedKinds
-  · simp only [if_pos h]
-    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
-  · simp only [if_neg h]
-    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
+  cases orig <;>
+    simp_all [problem_spec_prepareInput, implementation_prepareInput,
+      acceptedKinds, defaultKind, isFloating] <;> decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
An input feature array carries an *element type* (its numeric storage kind).
Before numerical processing, a fitting routine normalizes that element type
against a predetermined set of accepted floating-point types.

The behavior modeled here is that normalization. There is a set of accepted
floating-point element types (single- and double-precision). If the array's
original element type is already one of the accepted floating types, it is left
unchanged. Otherwise — for any non-accepted element type, including a boolean or
integer storage kind — the element type is converted to the default
double-precision floating type. In particular the normalized element type is
always one of the accepted floating types, so subsequent signed arithmetic on the
array is well defined regardless of how the input was originally stored.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by this specification. The
-- element-type normalization is the substantive behavior and is modeled DEEPLY
-- below (an A-reference, validated against the real routine by axiom_check.py),
-- not axiomatized. Hence no `opaque`/`axiom` declaration.
-- axioms-end

-- pure-start
/-- The storage element type of an input array (the representative kinds reached
by the public input contract). -/
inductive NpKind where
  | float64
  | float32
  | bool
  | int64
  | object
  deriving DecidableEq, Repr

/-- The accepted floating-point element types, in priority order. The first is the
default chosen when a conversion is required. -/
def acceptedKinds : List NpKind := [NpKind.float64, NpKind.float32]

/-- The double-precision floating type used as the default conversion target. -/
def defaultKind : NpKind := NpKind.float64

/-- An element type is floating iff it is one of the accepted kinds. -/
def isFloating (k : NpKind) : Bool := k ∈ acceptedKinds
-- pure-end

-- post-conditions-start
/-- Element-type normalization against the accepted floating set. If the original
element type is already accepted, the result equals it unchanged (frame: an
already-floating input is not touched). Otherwise the result is the default
double-precision floating type. Both branches are pinned to the input, so a
non-accepted input — e.g. a boolean storage kind — must yield the floating
default, never its unconverted original type. -/
def problem_spec_prepareInput (orig : NpKind) (result : NpKind) : Prop :=
  (orig ∈ acceptedKinds → result = orig) ∧
  (orig ∉ acceptedKinds → result = defaultKind)
-- post-conditions-end

-- impl-start
def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
  let mut dt := orig
  if orig ∈ acceptedKinds then
    dt := orig
  else
    dt := defaultKind
  return dt
-- impl-end

-- proof-start
theorem correct_prepareInput :
    ∀ (orig : NpKind),
      problem_spec_prepareInput orig (implementation_prepareInput orig) := by
  intro orig
  unfold problem_spec_prepareInput implementation_prepareInput
  simp only [Id.run]
  by_cases h : orig ∈ acceptedKinds
  · simp only [if_pos h]
    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
  · simp only [if_neg h]
    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_prepareInput is TOTAL, DETERMINISTIC, DECIDABLE over the finite 5-element NpKind domain: the two clauses (orig ∈ accepted → result=orig; orig ∉ accepted → result=defaultKind=float64) partition the domain and uniquely pin the output for every input. Correctness is thus decidable per input.

ATTACK PROOF STRATEGY: each wrong impl edits ONLY the impl+proof region (prefix lines 1-60 byte-identical → same_spec=True for all 6, verified). For every attack I used the STRONGEST genuine closing proof, a complete decision procedure: `intro orig; cases orig <;> simp_all [problem_spec_prepareInput, implementation_prepareInput, acceptedKinds, defaultKind, isFloating] <;> decide`. SANITY: this exact tactic CLOSES the correct impl (sanity_correct.lean, exit 0), proving the tactic is capable — so any failure below is a genuine spec violation, not a weak proof.

Commands:
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." → True for atk_1..6 and pos.
  verify: bash scripts/lean_verify.sh <path>

### Results
  pos.lean (reference)          exit 0  — verifies clean, no sorry, no axioms/errors in output.
  sanity_correct.lean           exit 0  — correct impl closes under my decide-proof (tactic capability control).
  atk_1 (prepatch bug: only object→float64, else keep; bool stays bool)          exit 1 — `decide` proved goal `False` is false at line 77.
  atk_2 (partial-domain: object→float32, accepted-but-wrong)                      exit 1 — decide proved False.
  atk_3 (boundary: always →float64, drops frame; float32→float64 wrongly)         exit 1 — decide proved False.
  atk_4 (control-flow-effect: condition reversed)                                 exit 1 — decide proved False.
  atk_5 (ungrounded-oracle echo: identity, no conversion)                         exit 1 — decide proved False.
  atk_6 (boundary: non-accepted →int64, wrong non-float target)                   exit 1 — decide proved False.

No wrong impl closes with a clean-axiom proof, so there are NO faithful patches to materialize/resolve (patches={}). The spec rejects every same-spec deviation, including the prepatch bug (atk_1, reproduced → fails G-VERIFY as G-DIFF expects).

REFINEMENT.MD AUDIT (A-leg focus, R/I covered by G-CONF): legs are #1 R (dtype↔NpKind), #2 A-reference (no-conversion branch), #3 A-reference (conversion branch, the fix effect), #4 I (return). No kind-3 ungrounded axiom. The axioms-start block correctly declares no opaque/axiom (verified: #print axioms clean on pos). The proof uses NO property of any opaque callee — it closes purely by case split + rfl/decide over the concrete finite NpKind model, so there is no axiom-escape channel a wrong impl could exploit. The A-references model check_array's list-dtype resolution (validation.py:439-466,496) and are validated against the REAL check_X_y/check_array by axiom_check.py (G-AX); the model's total function matches mapping.md's POST truth table (accepted→keep, everything-else→float64). Correspondence holds.

VERDICT SOUND: verify ⇒ correct on this decidable finite-domain spec; 6 distinct same-spec wrong impls (partial-domain, boundary×2, control-flow-effect, ungrounded-oracle echo, prepatch bug) all FAIL to verify.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
An input feature array carries an *element type* (its numeric storage kind).
Before numerical processing, a fitting routine normalizes that element type
against a predetermined set of accepted floating-point types.

The behavior modeled here is that normalization. There is a set of accepted
floating-point element types (single- and double-precision). If the array's
original element type is already one of the accepted floating types, it is left
unchanged. Otherwise — for any non-accepted element type, including a boolean or
integer storage kind — the element type is converted to the default
double-precision floating type. In particular the normalized element type is
always one of the accepted floating types, so subsequent signed arithmetic on the
array is well defined regardless of how the input was originally stored.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by this specification. The
-- element-type normalization is the substantive behavior and is modeled DEEPLY
-- below (an A-reference, validated against the real routine by axiom_check.py),
-- not axiomatized. Hence no `opaque`/`axiom` declaration.
-- axioms-end

-- pure-start
/-- The storage element type of an input array (the representative kinds reached
by the public input contract). -/
inductive NpKind where
  | float64
  | float32
  | bool
  | int64
  | object
  deriving DecidableEq, Repr

/-- The accepted floating-point element types, in priority order. The first is the
default chosen when a conversion is required. -/
def acceptedKinds : List NpKind := [NpKind.float64, NpKind.float32]

/-- The double-precision floating type used as the default conversion target. -/
def defaultKind : NpKind := NpKind.float64

/-- An element type is floating iff it is one of the accepted kinds. -/
def isFloating (k : NpKind) : Bool := k ∈ acceptedKinds
-- pure-end

-- post-conditions-start
/-- Element-type normalization against the accepted floating set. If the original
element type is already accepted, the result equals it unchanged (frame: an
already-floating input is not touched). Otherwise the result is the default
double-precision floating type. Both branches are pinned to the input, so a
non-accepted input — e.g. a boolean storage kind — must yield the floating
default, never its unconverted original type. -/
def problem_spec_prepareInput (orig : NpKind) (result : NpKind) : Prop :=
  (orig ∈ acceptedKinds → result = orig) ∧
  (orig ∉ acceptedKinds → result = defaultKind)
-- post-conditions-end

-- impl-start
def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do
  let mut dt := orig
  if orig ∈ acceptedKinds then
    dt := orig
  else
    dt := defaultKind
  return dt
-- impl-end

-- proof-start
theorem correct_prepareInput :
    ∀ (orig : NpKind),
      problem_spec_prepareInput orig (implementation_prepareInput orig) := by
  intro orig
  unfold problem_spec_prepareInput implementation_prepareInput
  simp only [Id.run]
  by_cases h : orig ∈ acceptedKinds
  · simp only [if_pos h]
    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
  · simp only [if_neg h]
    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_prepareInput is TOTAL, DETERMINISTIC, DECIDABLE over the finite 5-element NpKind domain: the two clauses (orig ∈ accepted → result=orig; orig ∉ accepted → result=defaultKind=float64) partition the domain and uniquely pin the output for every input. Correctness is thus decidable per input.

ATTACK PROOF STRATEGY: each wrong impl edits ONLY the impl+proof region (prefix lines 1-60 byte-identical → same_spec=True for all 6, verified). For every attack I used the STRONGEST genuine closing proof, a complete decision procedure: `intro orig; cases orig <;> simp_all [problem_spec_prepareInput, implementation_prepareInput, acceptedKinds, defaultKind, isFloating] <;> decide`. SANITY: this exact tactic CLOSES the correct impl (sanity_correct.lean, exit 0), proving the tactic is capable — so any failure below is a genuine spec violation, not a weak proof.

Commands:
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." → True for atk_1..6 and pos.
  verify: bash scripts/lean_verify.sh <path>

### Results
  pos.lean (reference)          exit 0  — verifies clean, no sorry, no axioms/errors in output.
  sanity_correct.lean           exit 0  — correct impl closes under my decide-proof (tactic capability control).
  atk_1 (prepatch bug: only object→float64, else keep; bool stays bool)          exit 1 — `decide` proved goal `False` is false at line 77.
  atk_2 (partial-domain: object→float32, accepted-but-wrong)                      exit 1 — decide proved False.
  atk_3 (boundary: always →float64, drops frame; float32→float64 wrongly)         exit 1 — decide proved False.
  atk_4 (control-flow-effect: condition reversed)                                 exit 1 — decide proved False.
  atk_5 (ungrounded-oracle echo: identity, no conversion)                         exit 1 — decide proved False.
  atk_6 (boundary: non-accepted →int64, wrong non-float target)                   exit 1 — decide proved False.

No wrong impl closes with a clean-axiom proof, so there are NO faithful patches to materialize/resolve (patches={}). The spec rejects every same-spec deviation, including the prepatch bug (atk_1, reproduced → fails G-VERIFY as G-DIFF expects).

REFINEMENT.MD AUDIT (A-leg focus, R/I covered by G-CONF): legs are #1 R (dtype↔NpKind), #2 A-reference (no-conversion branch), #3 A-reference (conversion branch, the fix effect), #4 I (return). No kind-3 ungrounded axiom. The axioms-start block correctly declares no opaque/axiom (verified: #print axioms clean on pos). The proof uses NO property of any opaque callee — it closes purely by case split + rfl/decide over the concrete finite NpKind model, so there is no axiom-escape channel a wrong impl could exploit. The A-references model check_array's list-dtype resolution (validation.py:439-466,496) and are validated against the REAL check_X_y/check_array by axiom_check.py (G-AX); the model's total function matches mapping.md's POST truth table (accepted→keep, everything-else→float64). Correspondence holds.

VERDICT SOUND: verify ⇒ correct on this decidable finite-domain spec; 6 distinct same-spec wrong impls (partial-domain, boundary×2, control-flow-effect, ungrounded-oracle echo, prepatch bug) all FAIL to verify.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-13328 (lean).

### PRELIMINARIES (all pass):
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_prepareInput -> [propext] only; NO sorryAx, proof is genuine.
- same_spec(Solution.lean, Solution_prepatch.lean, lean backend) -> True (spec region byte-identical).

MODEL: implementation_prepareInput orig = (if orig ∈ {float64,float32} then orig else float64). Postcondition problem_spec_prepareInput: orig∈accepted → result=orig ; orig∉accepted → result=float64. This models the dtype-resolution of check_X_y(...,dtype=[np.float64,np.float32]) forwarded to check_array (validation.py:459-466 list-dtype branch).

REAL CALLEE CHECK against base_commit 37b0e66c (cloned validation.py + huber.py; call-site confirmed check_X_y(X,y,copy=False,accept_sparse=['csr'],y_numeric=True) pre, +dtype=[float64,float32] post). The list-dtype branch (`if dtype_orig in dtype: dtype=None else: dtype=dtype[0]`) is textually identical to the modeled resolution. Drove the REAL check_X_y exactly as fit does:
  float64->float64, float32->float32, bool->float64, int64->float64 (all match model).
  exotic non-accepted kinds float16/uint8/uint64/int8/int32/longdouble -> float64 (fold into model's else->float64 branch, faithful).
  numeric object -> float64 (matches model's object->float64 claim). Non-numeric object/complex128 RAISE (partial-correctness postcondition: no return => no obligation; complex128 also outside NpKind domain).
- axiom_check.py (G-AX) passes: 405 checked, 0 failures, on available sklearn (1.9.0), and the branch source is identical at base commit.

SWEEP: exhaustively covered every NpKind member (float64/float32/bool/int64/object) plus additional non-accepted numeric kinds. Found NO input where the real callee returns a dtype different from the model's prediction. The spec makes only claims that hold for the real check_array list-dtype resolution — it is neither too strong nor drifted. Discriminating F2P input (bool) is correctly captured: POST=float64 (well-defined -X), PRE keeps bool (crash); the prepatch model correctly fails G-VERIFY.

VERDICT: FAITHFUL. No diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view examined via markers.spec_view(Solution.lean, LeanBackend) — impl and proof regions are elided, so the auditor sees only: the docstring, the axioms comment, the `pure` region (NpKind enum, acceptedKinds=[float64,float32], defaultKind=float64, isFloating), and the post-condition problem_spec_prepareInput. None of this reveals the gold edit's location or form beyond the public problem_statement. The gold patch is a single-line addition of `dtype=[np.float64, np.float32]` to the check_X_y call in sklearn/linear_model/huber.py:251-254. The spec view names NO file, NO function (huber.py, check_X_y, check_array, fit), NO call site, NO line numbers, and NO concrete numpy/sklearn API or literal argument. It describes only the desired *behavior*: non-accepted element types (incl. boolean) normalize to a double-precision float default. That behavior is already essentially disclosed by the public problem_statement, which explicitly states 'Boolean array is expected to be converted to float by HuberRegressor.fit as it is done by, say LinearRegression' and identifies the `-X` TypeError on a boolean array. The only spec detail slightly beyond the problem_statement — that the accepted set is {float64, float32} — is legitimate post-condition content necessary to state correctness, not a disclosure of where/how to patch; a solver reading only the spec view still cannot recover the changed file, the validation callee, or the concrete `dtype=[...]` argument that constitutes the fix. The leak-prone specifics (file/callee names, the literal dtype argument, line numbers) live in refinement.md and mapping.md, which are NOT part of the spec view. G-LEAK gate also recorded pass with empty failures. Spec view stays appropriately abstract.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
