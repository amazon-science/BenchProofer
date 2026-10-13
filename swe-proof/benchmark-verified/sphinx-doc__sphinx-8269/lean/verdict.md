# P2 adversarial audit — sphinx-doc__sphinx-8269

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_partial503.lean`, `atk_boundary600.lean`, `atk_swaporder.lean`, `atk_echo.lean`, `atk_msg401.lean`, `atk_code1.lean`, `atk_lower300.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,6 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
-  if 400 ≤ statusCode ∧ statusCode < 600 then
-    if statusCode = 401 then
-      return ⟨"working", " - unauthorized", 0⟩
-    if statusCode = 503 then
-      return ⟨"ignored", httpErrMsg, 0⟩
-    return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

Attack 2 — `atk_partial503.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,10 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
   if 400 ≤ statusCode ∧ statusCode < 600 then
     if statusCode = 401 then
       return ⟨"working", " - unauthorized", 0⟩
-    if statusCode = 503 then
-      return ⟨"ignored", httpErrMsg, 0⟩
     return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

Attack 3 — `atk_boundary600.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,12 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
-  if 400 ≤ statusCode ∧ statusCode < 600 then
+  if 400 ≤ statusCode ∧ statusCode < 601 then
     if statusCode = 401 then
       return ⟨"working", " - unauthorized", 0⟩
     if statusCode = 503 then
       return ⟨"ignored", httpErrMsg, 0⟩
     return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

Attack 4 — `atk_swaporder.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,17 +84,14 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
+  if anchorFound = false then
+    return ⟨"broken", anchorErrMsg, 0⟩
   if 400 ≤ statusCode ∧ statusCode < 600 then
     if statusCode = 401 then
       return ⟨"working", " - unauthorized", 0⟩
     if statusCode = 503 then
       return ⟨"ignored", httpErrMsg, 0⟩
     return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
-  if anchorFound = false then
-    return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
 -- impl-end
 
```

Attack 5 — `atk_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,17 +84,6 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
-  if 400 ≤ statusCode ∧ statusCode < 600 then
-    if statusCode = 401 then
-      return ⟨"working", " - unauthorized", 0⟩
-    if statusCode = 503 then
-      return ⟨"ignored", httpErrMsg, 0⟩
-    return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
-  if anchorFound = false then
-    return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
 -- impl-end
 
```

Attack 6 — `atk_msg401.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,12 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
   if 400 ≤ statusCode ∧ statusCode < 600 then
     if statusCode = 401 then
-      return ⟨"working", " - unauthorized", 0⟩
+      return ⟨"working", httpErrMsg, 0⟩
     if statusCode = 503 then
       return ⟨"ignored", httpErrMsg, 0⟩
     return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

Attack 7 — `atk_code1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,12 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
   if 400 ≤ statusCode ∧ statusCode < 600 then
     if statusCode = 401 then
       return ⟨"working", " - unauthorized", 0⟩
     if statusCode = 503 then
       return ⟨"ignored", httpErrMsg, 0⟩
-    return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
+    return ⟨"broken", httpErrMsg, 1⟩
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

Attack 8 — `atk_lower300.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,15 +84,12 @@
 def implementation_classifyLink
     (statusCode : Nat) (anchorFound : Bool)
     (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
-  -- The reply's HTTP status is consulted before its body: an error status in the
-  -- 4xx/5xx range settles the outcome on its own.
-  if 400 ≤ statusCode ∧ statusCode < 600 then
+  if 300 ≤ statusCode ∧ statusCode < 600 then
     if statusCode = 401 then
       return ⟨"working", " - unauthorized", 0⟩
     if statusCode = 503 then
       return ⟨"ignored", httpErrMsg, 0⟩
     return ⟨"broken", httpErrMsg, 0⟩
-  -- A non-error status: now the in-page fragment is consulted.
   if anchorFound = false then
     return ⟨"broken", anchorErrMsg, 0⟩
   return onSuccess
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the outcome of validating one remote hyperlink that carries both a
target document and an in-page fragment, when fragment-level validation is
enabled.

Validating such a link involves two independent observations about the server's
reply:

  * the reply's HTTP status code, and
  * whether the requested in-page fragment is present in the returned document.

The reported outcome is a triple (a status label, an explanatory message, a
numeric code). The desired behavior is that the reply's HTTP status is the FIRST
thing consulted: an error status in the 4xx/5xx range determines the outcome on
its own, independently of the fragment search. Within that error range two codes
are treated specially — an "unauthorized" status is reported as a working link,
and a "service unavailable" status is reported as an ignored link — while every
other error status is reported as a failure carrying the HTTP-level message.

Only when the status is NOT an error is the fragment consulted: a missing
fragment is reported as a failure carrying the fragment-level message, and a
present fragment defers to the outcome of the (unchanged) success continuation
that determines whether the link is plain-working or redirected.

The HTTP-level message, the fragment-level message, and the success-continuation
outcome are taken as arbitrary inputs here: the behavior pinned below is exactly
"which observation governs, and which message/outcome it routes through," for
every possible choice of those strings and that outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two server
-- observations (the reply's status code and whether the requested fragment is
-- present) are modeled as inputs `statusCode : Nat` and `anchorFound : Bool`;
-- the candidate explanatory messages and the outcome of the unchanged
-- success-continuation are modeled as arbitrary inputs (`httpErrMsg`,
-- `anchorErrMsg`, `onSuccess`). The modeled change is solely WHICH observation
-- governs the reported outcome, so the result is pinned for every choice of
-- those inputs. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The reported result of validating a hyperlink: a status label, an
explanatory message, and a numeric code (the analogue of the repo's
`Tuple[str, str, int]`). -/
structure Outcome where
  status : String
  info   : String
  code   : Int
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The reported outcome is fully pinned to the inputs:

  * when the status is an HTTP error (in the 4xx/5xx range) the result is
    determined by the status ALONE — "unauthorized" maps to a working report
    (with a constant unauthorized note and code 0), "service unavailable" maps to
    an ignored report carrying the HTTP-level message (code 0), and every other
    error status maps to a failure carrying the HTTP-level message (code 0);
  * otherwise, a missing fragment maps to a failure carrying the fragment-level
    message (code 0), and a present fragment defers to the success-continuation
    outcome.

No output component is left free: the status label, the message, and the code are
each pinned to the inputs in every branch. -/
def problem_spec_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome)
    (result : Outcome) : Prop :=
  result =
    (if 400 ≤ statusCode ∧ statusCode < 600 then
       if statusCode = 401 then ⟨"working", " - unauthorized", 0⟩
       else if statusCode = 503 then ⟨"ignored", httpErrMsg, 0⟩
       else ⟨"broken", httpErrMsg, 0⟩
     else if anchorFound = false then ⟨"broken", anchorErrMsg, 0⟩
     else onSuccess)
-- post-conditions-end

-- impl-start
def implementation_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
  -- The reply's HTTP status is consulted before its body: an error status in the
  -- 4xx/5xx range settles the outcome on its own.
  if 400 ≤ statusCode ∧ statusCode < 600 then
    if statusCode = 401 then
      return ⟨"working", " - unauthorized", 0⟩
    if statusCode = 503 then
      return ⟨"ignored", httpErrMsg, 0⟩
    return ⟨"broken", httpErrMsg, 0⟩
  -- A non-error status: now the in-page fragment is consulted.
  if anchorFound = false then
    return ⟨"broken", anchorErrMsg, 0⟩
  return onSuccess
-- impl-end

-- proof-start
theorem correct_classifyLink :
    ∀ (statusCode : Nat) (anchorFound : Bool)
      (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome),
      problem_spec_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
        (implementation_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess) := by
  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
  unfold problem_spec_classifyLink implementation_classifyLink
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_classifyLink is a TOTAL FUNCTIONAL EQUALITY — `result = f(statusCode, anchorFound, httpErrMsg, anchorErrMsg, onSuccess)` with every output component (status label, message, code) pinned in every branch, universally quantified over all inputs. Consequently ANY impl that differs from f on even one input yields an unsolved goal and cannot close correct_classifyLink. This is the strongest possible spec shape; verify⇒correct holds structurally.

SAME-SPEC: all 8 attacks edit ONLY the impl region (axioms/pure/pre/post byte-identical); swebench_unified.markers.same_spec(gold, attack, lean) = True for every one of them (verified against /fsx .../lean/Solution.lean via the lean backend).

POSITIVE CONTROL (gold, atk_pos.lean): `bash scripts/lean_verify.sh atk_pos.lean` -> exit=0. `#print axioms correct_classifyLink` (atk_posax.lean) -> 'depends on axioms: [propext]' — clean (no sorryAx, no bundle-specific axiom), no sorry. meta.json axioms=[].

ATTACKS — command `bash scripts/lean_verify.sh atk_N.lean` for each; all exit=1 with genuine 'error: unsolved goals' (confirmed via grep, not syntax errors):
  1. atk_prepatch.lean (PREPATCH BUG reproduced): never consults status; wrong at statusCode=500 (returns broken/anchorErrMsg instead of broken/httpErrMsg). exit=1, unsolved goals @97.
  2. atk_partial503.lean (partial-domain): drops the 503 special-case -> falls to broken; wrong at 503. exit=1.
  3. atk_boundary600.lean (boundary off-by-one): uses `< 601` instead of `< 600`; wrong at statusCode=600 (should defer to anchor). exit=1, unsolved goals @103.
  4. atk_swaporder.lean (control-flow-effect): consults anchor BEFORE status; wrong at error status with anchor absent. exit=1.
  5. atk_echo.lean (ungrounded-oracle echo): always `return onSuccess`; wrong broadly. exit=1, unsolved goals @95.
  6. atk_msg401.lean (boundary/message): 401 returns httpErrMsg instead of the constant ' - unauthorized' note; wrong at 401. exit=1, unsolved goals @103.
  7. atk_code1.lean (code-effect): broken branch returns code 1 instead of 0; wrong at generic error. exit=1.
  8. atk_lower300.lean (lower-bound widened): uses `300 <=` instead of `400 <=`; wrong at 3xx. exit=1.

No wrong impl closed with a clean-axiom proof, so NO faithful patch materialization / run_resolve was required (the resolve step is triggered only for a verifying same-spec wrong impl; there were none). patches={} accordingly.

REFINEMENT AUDIT (refinement.md): 6 legs, all R / I / A-reference — NO A-consumed, NO kind-3. Op1 (R, raise_for_status threshold 400<=code<600 modeled deeply), Op2 (I, 401 literal triple), Op3 (R, 503 httpErrMsg), Op4 (R, other-error httpErrMsg), Op5 (R, anchor branch anchorErrMsg) are the differential-tested content. Op6 is the sole A-reference: `onSuccess` stands for the UNCHANGED success/redirect tail — correctly universally quantified rather than axiomatized (no opaque/axiom in Solution.lean; axiom_check.py is a skip stub; meta.json axioms=[]). The A-reference correspondence to the real callee (the unchanged success/redirect continuation reached when status is fine and fragment present) is faithful and is bound to the real tail value in G-CONF (conformance_check.py oracle matches the patched check_uri dispatch). A-leg correspondence holds.

CONCLUSION: exact functional-equality spec; only the behaviorally-correct impl verifies; refinement legs sound with a legitimate A-reference. Nothing breaks verify⇒correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_partial503.lean`, `atk_boundary600.lean`, `atk_swaporder.lean`, `atk_echo.lean`, `atk_msg401.lean`, `atk_code1.lean`, `atk_lower300.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_partial503.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_boundary600.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_swaporder.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_echo.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_msg401.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_code1.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_lower300.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the outcome of validating one remote hyperlink that carries both a
target document and an in-page fragment, when fragment-level validation is
enabled.

Validating such a link involves two independent observations about the server's
reply:

  * the reply's HTTP status code, and
  * whether the requested in-page fragment is present in the returned document.

The reported outcome is a triple (a status label, an explanatory message, a
numeric code). The desired behavior is that the reply's HTTP status is the FIRST
thing consulted: an error status in the 4xx/5xx range determines the outcome on
its own, independently of the fragment search. Within that error range two codes
are treated specially — an "unauthorized" status is reported as a working link,
and a "service unavailable" status is reported as an ignored link — while every
other error status is reported as a failure carrying the HTTP-level message.

Only when the status is NOT an error is the fragment consulted: a missing
fragment is reported as a failure carrying the fragment-level message, and a
present fragment defers to the outcome of the (unchanged) success continuation
that determines whether the link is plain-working or redirected.

The HTTP-level message, the fragment-level message, and the success-continuation
outcome are taken as arbitrary inputs here: the behavior pinned below is exactly
"which observation governs, and which message/outcome it routes through," for
every possible choice of those strings and that outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two server
-- observations (the reply's status code and whether the requested fragment is
-- present) are modeled as inputs `statusCode : Nat` and `anchorFound : Bool`;
-- the candidate explanatory messages and the outcome of the unchanged
-- success-continuation are modeled as arbitrary inputs (`httpErrMsg`,
-- `anchorErrMsg`, `onSuccess`). The modeled change is solely WHICH observation
-- governs the reported outcome, so the result is pinned for every choice of
-- those inputs. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The reported result of validating a hyperlink: a status label, an
explanatory message, and a numeric code (the analogue of the repo's
`Tuple[str, str, int]`). -/
structure Outcome where
  status : String
  info   : String
  code   : Int
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The reported outcome is fully pinned to the inputs:

  * when the status is an HTTP error (in the 4xx/5xx range) the result is
    determined by the status ALONE — "unauthorized" maps to a working report
    (with a constant unauthorized note and code 0), "service unavailable" maps to
    an ignored report carrying the HTTP-level message (code 0), and every other
    error status maps to a failure carrying the HTTP-level message (code 0);
  * otherwise, a missing fragment maps to a failure carrying the fragment-level
    message (code 0), and a present fragment defers to the success-continuation
    outcome.

No output component is left free: the status label, the message, and the code are
each pinned to the inputs in every branch. -/
def problem_spec_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome)
    (result : Outcome) : Prop :=
  result =
    (if 400 ≤ statusCode ∧ statusCode < 600 then
       if statusCode = 401 then ⟨"working", " - unauthorized", 0⟩
       else if statusCode = 503 then ⟨"ignored", httpErrMsg, 0⟩
       else ⟨"broken", httpErrMsg, 0⟩
     else if anchorFound = false then ⟨"broken", anchorErrMsg, 0⟩
     else onSuccess)
-- post-conditions-end

-- impl-start
def implementation_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
  -- The reply's HTTP status is consulted before its body: an error status in the
  -- 4xx/5xx range settles the outcome on its own.
  if 400 ≤ statusCode ∧ statusCode < 600 then
    if statusCode = 401 then
      return ⟨"working", " - unauthorized", 0⟩
    if statusCode = 503 then
      return ⟨"ignored", httpErrMsg, 0⟩
    return ⟨"broken", httpErrMsg, 0⟩
  -- A non-error status: now the in-page fragment is consulted.
  if anchorFound = false then
    return ⟨"broken", anchorErrMsg, 0⟩
  return onSuccess
-- impl-end

-- proof-start
theorem correct_classifyLink :
    ∀ (statusCode : Nat) (anchorFound : Bool)
      (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome),
      problem_spec_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
        (implementation_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess) := by
  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
  unfold problem_spec_classifyLink implementation_classifyLink
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_classifyLink is a TOTAL FUNCTIONAL EQUALITY — `result = f(statusCode, anchorFound, httpErrMsg, anchorErrMsg, onSuccess)` with every output component (status label, message, code) pinned in every branch, universally quantified over all inputs. Consequently ANY impl that differs from f on even one input yields an unsolved goal and cannot close correct_classifyLink. This is the strongest possible spec shape; verify⇒correct holds structurally.

SAME-SPEC: all 8 attacks edit ONLY the impl region (axioms/pure/pre/post byte-identical); swebench_unified.markers.same_spec(gold, attack, lean) = True for every one of them (verified against /fsx .../lean/Solution.lean via the lean backend).

POSITIVE CONTROL (gold, atk_pos.lean): `bash scripts/lean_verify.sh atk_pos.lean` -> exit=0. `#print axioms correct_classifyLink` (atk_posax.lean) -> 'depends on axioms: [propext]' — clean (no sorryAx, no bundle-specific axiom), no sorry. meta.json axioms=[].

ATTACKS — command `bash scripts/lean_verify.sh atk_N.lean` for each; all exit=1 with genuine 'error: unsolved goals' (confirmed via grep, not syntax errors):
  1. atk_prepatch.lean (PREPATCH BUG reproduced): never consults status; wrong at statusCode=500 (returns broken/anchorErrMsg instead of broken/httpErrMsg). exit=1, unsolved goals @97.
  2. atk_partial503.lean (partial-domain): drops the 503 special-case -> falls to broken; wrong at 503. exit=1.
  3. atk_boundary600.lean (boundary off-by-one): uses `< 601` instead of `< 600`; wrong at statusCode=600 (should defer to anchor). exit=1, unsolved goals @103.
  4. atk_swaporder.lean (control-flow-effect): consults anchor BEFORE status; wrong at error status with anchor absent. exit=1.
  5. atk_echo.lean (ungrounded-oracle echo): always `return onSuccess`; wrong broadly. exit=1, unsolved goals @95.
  6. atk_msg401.lean (boundary/message): 401 returns httpErrMsg instead of the constant ' - unauthorized' note; wrong at 401. exit=1, unsolved goals @103.
  7. atk_code1.lean (code-effect): broken branch returns code 1 instead of 0; wrong at generic error. exit=1.
  8. atk_lower300.lean (lower-bound widened): uses `300 <=` instead of `400 <=`; wrong at 3xx. exit=1.

No wrong impl closed with a clean-axiom proof, so NO faithful patch materialization / run_resolve was required (the resolve step is triggered only for a verifying same-spec wrong impl; there were none). patches={} accordingly.

REFINEMENT AUDIT (refinement.md): 6 legs, all R / I / A-reference — NO A-consumed, NO kind-3. Op1 (R, raise_for_status threshold 400<=code<600 modeled deeply), Op2 (I, 401 literal triple), Op3 (R, 503 httpErrMsg), Op4 (R, other-error httpErrMsg), Op5 (R, anchor branch anchorErrMsg) are the differential-tested content. Op6 is the sole A-reference: `onSuccess` stands for the UNCHANGED success/redirect tail — correctly universally quantified rather than axiomatized (no opaque/axiom in Solution.lean; axiom_check.py is a skip stub; meta.json axioms=[]). The A-reference correspondence to the real callee (the unchanged success/redirect continuation reached when status is fine and fragment present) is faithful and is bound to the real tail value in G-CONF (conformance_check.py oracle matches the patched check_uri dispatch). A-leg correspondence holds.

CONCLUSION: exact functional-equality spec; only the behaviorally-correct impl verifies; refinement legs sound with a legitimate A-reference. Nothing breaks verify⇒correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo behavior) confirmed for sphinx-doc__sphinx-8269 lean bundle.

### Checks performed
1. Spec region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language)=True and same_spec(sol,sol)=True. The structure/post-conditions/pure regions are byte-identical between prepatch and patched; only the impl/proof legs differ.
2. Compilation + axiom hygiene: scripts/lean_verify.sh exit 0. `#print axioms correct_classifyLink` = [propext] only — no sorryAx/admit/native_decide. Proof is genuine.
3. Real callee = check_uri anchor-enabled branch (sphinx/builders/linkcheck.py:165-199 @ base_commit 1e2ccd8f, verified). Post-patch (patch.diff adds `response.raise_for_status()`). Real behavior as a pure function of (statusCode, anchorFound, httpErrMsg, anchorErrMsg, onSuccess): 400<=code<600 raises HTTPError -> 401->('working',' - unauthorized',0), 503->('ignored',str(err),0), else->('broken',str(err),0); non-error status -> check_anchor; not found raises plain Exception caught by `except Exception`, is_ssl_error==False for that message -> ('broken', anchorErrMsg,0); found -> success/redirect tail (onSuccess).
4. Modeled function problem_spec_classifyLink matches this exactly. Threshold verified against the REAL requests.Response.raise_for_status: 400/401/499/500/503/599 raise; 0/99/100/200/399/600/601/999 do not -> matches the modeled `400 <= statusCode < 600`.
5. Exhaustive Python differential over statusCode 0..699 x anchorFound in {True,False} (real reconstruction vs spec): 0 divergences.
6. conformance_check.py: 120,011 cases (edge + fuzz), oracle driven through the real requests.raise_for_status, disagreements=0, status=pass.

MODELING BOUNDARY ANALYSIS: httpErrMsg/anchorErrMsg/onSuccess are universally quantified arbitrary inputs; the spec pins only WHICH observation governs (the actual bug fixed) and which message/outcome each branch routes through. This is neither too strong (arbitrary messages/success outcome left free) nor too weak (every output component pinned per branch). For any concrete real invocation, instantiating these inputs reproduces the real output. is_ssl_error==False assumption for the anchor-not-found message is correct (SSLError not involved). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK mechanical screen passes (rep.passed=True, no hard_failures). Spec regions byte-identical: same_spec(Solution, Solution_prepatch)=True. Gold edit is a single line `response.raise_for_status()` making an HTTP error status govern the outcome before the anchor search. The public problem_statement ('Linkcheck should report HTTP errors instead of Anchor not found'; expected output shows the '404 Client Error...' HTTP-level message replacing 'Anchor test not found') already fully discloses this behavior. Spec view checks: (1) no diff markers, (2) gold changed line `response.raise_for_status()` not reproduced, (3) patched path sphinx/builders/linkcheck.py absent, (4) patched symbol check_uri (and check_anchor/raise_for_status) never echoed as identifier or in comments — spec uses abstract inputs statusCode/anchorFound/httpErrMsg/anchorErrMsg/onSuccess, (5) no fix/bug narration flagged. The 401->working / 503->ignored dispatch modeled in the spec is PRE-EXISTING except-HTTPError code at base_commit, not part of the gold edit, so its presence is faithful context, not edit-leakage. Nothing in the spec view reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
