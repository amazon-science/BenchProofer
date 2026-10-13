# P2 adversarial audit — django__django-13821

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
None. The frozen problem_spec_ensureSupportedVersion is a TOTAL, point-wise functional constraint: for each (versionInfo, versionStr) it pins result to exactly one Except value (Except.error (errorMessage versionStr) iff versionLt versionInfo [3,9,0], else Except.ok ()). No input admits two distinct satisfying results, so every impl whose correct_ proof closes is behaviorally identical to gold on every input — including the F2P discriminating input (3,8,11,1). Therefore no closing-but-divergent impl exists and none could map to a non-resolving patch. No clean-axiom closing wrong impl was found, so no faithful patch needed to be materialized/resolve-run.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,15 @@
 -- post-conditions-end
 
 -- impl-start
+def requiredMinBug : List Nat := [3, 8, 3]
+
+def errorMessageBug (versionStr : List Char) : List Char :=
+  "SQLite 3.8.3 or later is required (found ".toList ++ versionStr ++ ").".toList
+
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
-  if versionLt versionInfo requiredMin then
-    return Except.error (errorMessage versionStr)
+  if versionLt versionInfo requiredMinBug then
+    return Except.error (errorMessageBug versionStr)
   return Except.ok ()
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
 -- impl-start
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
-  if versionLt versionInfo requiredMin then
+  if versionLt versionInfo [3, 9, 1] then
     return Except.error (errorMessage versionStr)
   return Except.ok ()
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,7 @@
 -- impl-start
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
-  if versionLt versionInfo requiredMin then
-    return Except.error (errorMessage versionStr)
-  return Except.ok ()
+  return Except.error (errorMessage versionStr)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
+def implementation_ensureSupportedVersion (_versionInfo : List Nat) (_versionStr : List Char) :
     Except (List Char) Unit := Id.run do
-  if versionLt versionInfo requiredMin then
-    return Except.error (errorMessage versionStr)
   return Except.ok ()
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,8 @@
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
   if versionLt versionInfo requiredMin then
-    return Except.error (errorMessage versionStr)
-  return Except.ok ()
+    return Except.ok ()
+  return Except.error (errorMessage versionStr)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
   if versionLt versionInfo requiredMin then
-    return Except.error (errorMessage versionStr)
+    return Except.error ("SQLite 3.9.0 or later is required (found ).".toList)
   return Except.ok ()
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
 -- impl-start
 def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
     Except (List Char) Unit := Id.run do
-  if versionLt versionInfo requiredMin then
+  if versionLt requiredMin versionInfo then
     return Except.error (errorMessage versionStr)
   return Except.ok ()
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two inputs are the
-- runtime version data (a numeric component tuple and the version display
-- string); the order comparison on the tuple and the message formatting are
-- modeled DEEPLY (below), not axiomatized. The proof agent may add `_prop`
-- axioms only if stuck.
-- axioms-end

-- pure-start
/-- Lexicographic strict order on component tuples, matching Python tuple `<`:
compare element-wise; a strict prefix is smaller than its extension; equal-length
equal tuples are not less than one another. -/
def versionLt : List Nat → List Nat → Bool
  | [],      [] => false
  | [],      _ :: _ => true
  | _ :: _,  [] => false
  | a :: as, b :: bs =>
      if a < b then true
      else if b < a then false
      else versionLt as bs

/-- The minimum supported version: components `3, 9, 0`. -/
def requiredMin : List Nat := [3, 9, 0]

/-- The configuration-error message reported for an unsupported runtime: a
constant prefix naming the minimum supported version, the actual version display
string substituted in, and a closing parenthesis and period. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList
-- pure-end

-- post-conditions-start
/-- A runtime whose version components are strictly below the minimum supported
version is rejected with the configuration-error message carrying its version
string; any other runtime is accepted. Both branches are pinned. -/
def problem_spec_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char)
    (result : Except (List Char) Unit) : Prop :=
  if versionLt versionInfo requiredMin then
    result = Except.error (errorMessage versionStr)
  else
    result = Except.ok ()
-- post-conditions-end

-- impl-start
def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
    Except (List Char) Unit := Id.run do
  if versionLt versionInfo requiredMin then
    return Except.error (errorMessage versionStr)
  else
    return Except.ok ()
-- impl-end

-- proof-start
theorem correct_ensureSupportedVersion : ∀ (versionInfo : List Nat) (versionStr : List Char),
    problem_spec_ensureSupportedVersion versionInfo versionStr
      (implementation_ensureSupportedVersion versionInfo versionStr) := by
  intro versionInfo versionStr
  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion
  by_cases h : versionLt versionInfo requiredMin <;>
    simp only [h, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (lean backend); axioms/pure/pre/post regions byte-identical to Solution.lean. All verifications via scripts/lean_verify.sh (300s cap), run concurrently in 2 batches of 4.

### RESULTS (exit code; failure reason):
- pos_control (behaviorally-correct if/else Id.run rephrase): EXIT 0, VERIFIES. #print axioms correct_ensureSupportedVersion => [propext] only (clean; no sorryAx, no injected _prop).
- atk_1 PREPATCH BUG (requiredMinBug=[3,8,3], msg 3.8.3): EXIT 1 — real proof failure (rfl failed, LHS if versionLt _ requiredMinBug ...). Prepatch bug reproduced: correct_ cannot close.
- atk_2 BOUNDARY off-by-one (threshold [3,9,1]): EXIT 1 — rfl failed.
- atk_3 PARTIAL-DOMAIN always-reject (return error unconditionally): EXIT 1 — rfl failed (pure(error ...) vs ok).
- atk_4 UNGROUNDED always-accept (return ok unconditionally): EXIT 1 — rfl failed (pure(ok()) not defeq).
- atk_5 CONTROL-FLOW-EFFECT swapped branches (ok on <min, error otherwise): EXIT 1 — rfl failed.
- atk_6 UNGROUNDED-ORACLE ECHO correct threshold but wrong message dropping versionStr ('...(found ).'): EXIT 1 — rfl failed.
- atk_7 swapped comparison args (versionLt requiredMin versionInfo): EXIT 1 — rfl failed.

No wrong impl closed with clean axioms => step 2 (materialize faithful patch + run_resolve) was VACUOUS: there was no verifying wrong impl to resolve-check. This is the correct outcome for a total functional spec, not missing evidence.

refinement.md AUDIT: rows 1-2 = R (tuple[int]->List Nat, str->List Char input lifts); rows 3-5 = I (versionLt reproduces Python tuple lexicographic <; %-format modeled as concatenation; normal-return/raise). NO A-consumed, NO A-reference, NO kind-3 legs. Axioms region is comment-only (empty) — verified byte-identical in every attack. Deep-model correspondence (versionLt <-> tuple <, concatenation <-> % ) is exercised by G-CONF (conformance_check.py present, 120k fuzz + boundary incl (3,8,11,1)), not by axioms; the mapping.md/refinement.md A-leg narrative is accurate. No deep-model reference that could smuggle unsoundness.

Verify=>correct holds: the spec admits no closing wrong impl. Verdict SOUND after 7 distinct attacks (>=5 required) + verifying positive control.

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
None. The frozen problem_spec_ensureSupportedVersion is a TOTAL, point-wise functional constraint: for each (versionInfo, versionStr) it pins result to exactly one Except value (Except.error (errorMessage versionStr) iff versionLt versionInfo [3,9,0], else Except.ok ()). No input admits two distinct satisfying results, so every impl whose correct_ proof closes is behaviorally identical to gold on every input — including the F2P discriminating input (3,8,11,1). Therefore no closing-but-divergent impl exists and none could map to a non-resolving patch. No clean-axiom closing wrong impl was found, so no faithful patch needed to be materialized/resolve-run.
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

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two inputs are the
-- runtime version data (a numeric component tuple and the version display
-- string); the order comparison on the tuple and the message formatting are
-- modeled DEEPLY (below), not axiomatized. The proof agent may add `_prop`
-- axioms only if stuck.
-- axioms-end

-- pure-start
/-- Lexicographic strict order on component tuples, matching Python tuple `<`:
compare element-wise; a strict prefix is smaller than its extension; equal-length
equal tuples are not less than one another. -/
def versionLt : List Nat → List Nat → Bool
  | [],      [] => false
  | [],      _ :: _ => true
  | _ :: _,  [] => false
  | a :: as, b :: bs =>
      if a < b then true
      else if b < a then false
      else versionLt as bs

/-- The minimum supported version: components `3, 9, 0`. -/
def requiredMin : List Nat := [3, 9, 0]

/-- The configuration-error message reported for an unsupported runtime: a
constant prefix naming the minimum supported version, the actual version display
string substituted in, and a closing parenthesis and period. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList
-- pure-end

-- post-conditions-start
/-- A runtime whose version components are strictly below the minimum supported
version is rejected with the configuration-error message carrying its version
string; any other runtime is accepted. Both branches are pinned. -/
def problem_spec_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char)
    (result : Except (List Char) Unit) : Prop :=
  if versionLt versionInfo requiredMin then
    result = Except.error (errorMessage versionStr)
  else
    result = Except.ok ()
-- post-conditions-end

-- impl-start
def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
    Except (List Char) Unit := Id.run do
  if versionLt versionInfo requiredMin then
    return Except.error (errorMessage versionStr)
  else
    return Except.ok ()
-- impl-end

-- proof-start
theorem correct_ensureSupportedVersion : ∀ (versionInfo : List Nat) (versionStr : List Char),
    problem_spec_ensureSupportedVersion versionInfo versionStr
      (implementation_ensureSupportedVersion versionInfo versionStr) := by
  intro versionInfo versionStr
  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion
  by_cases h : versionLt versionInfo requiredMin <;>
    simp only [h, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (lean backend); axioms/pure/pre/post regions byte-identical to Solution.lean. All verifications via scripts/lean_verify.sh (300s cap), run concurrently in 2 batches of 4.

### RESULTS (exit code; failure reason):
- pos_control (behaviorally-correct if/else Id.run rephrase): EXIT 0, VERIFIES. #print axioms correct_ensureSupportedVersion => [propext] only (clean; no sorryAx, no injected _prop).
- atk_1 PREPATCH BUG (requiredMinBug=[3,8,3], msg 3.8.3): EXIT 1 — real proof failure (rfl failed, LHS if versionLt _ requiredMinBug ...). Prepatch bug reproduced: correct_ cannot close.
- atk_2 BOUNDARY off-by-one (threshold [3,9,1]): EXIT 1 — rfl failed.
- atk_3 PARTIAL-DOMAIN always-reject (return error unconditionally): EXIT 1 — rfl failed (pure(error ...) vs ok).
- atk_4 UNGROUNDED always-accept (return ok unconditionally): EXIT 1 — rfl failed (pure(ok()) not defeq).
- atk_5 CONTROL-FLOW-EFFECT swapped branches (ok on <min, error otherwise): EXIT 1 — rfl failed.
- atk_6 UNGROUNDED-ORACLE ECHO correct threshold but wrong message dropping versionStr ('...(found ).'): EXIT 1 — rfl failed.
- atk_7 swapped comparison args (versionLt requiredMin versionInfo): EXIT 1 — rfl failed.

No wrong impl closed with clean axioms => step 2 (materialize faithful patch + run_resolve) was VACUOUS: there was no verifying wrong impl to resolve-check. This is the correct outcome for a total functional spec, not missing evidence.

refinement.md AUDIT: rows 1-2 = R (tuple[int]->List Nat, str->List Char input lifts); rows 3-5 = I (versionLt reproduces Python tuple lexicographic <; %-format modeled as concatenation; normal-return/raise). NO A-consumed, NO A-reference, NO kind-3 legs. Axioms region is comment-only (empty) — verified byte-identical in every attack. Deep-model correspondence (versionLt <-> tuple <, concatenation <-> % ) is exercised by G-CONF (conformance_check.py present, 120k fuzz + boundary incl (3,8,11,1)), not by axioms; the mapping.md/refinement.md A-leg narrative is accurate. No deep-model reference that could smuggle unsoundness.

Verify=>correct holds: the spec admits no closing wrong impl. Verdict SOUND after 7 distinct attacks (>=5 required) + verifying positive control.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-13821 (lean). The spec models post-patch check_sqlite_version(): reject (Except.error msg) iff sqlite_version_info < (3,9,0), else accept (Except.ok ()), with msg = 'SQLite 3.9.0 or later is required (found <versionStr>).'.

### Verification performed
1. Spec byte-identity: markers.same_spec(Solution, Solution_prepatch, LeanBackend) = True. pure/axioms/post-conditions regions diff-identical between patched and prepatch; only impl+proof differ (prepatch uses requiredMinBug=[3,8,3]/errorMessageBug, the real pre-patch bug). Good G-DIFF signal.
2. Lean: lean_verify.sh exit 0; #print axioms correct_ensureSupportedVersion => [propext] only. No sorryAx, no fake proof.
3. Real callee ground truth: gold patch at base e64c1d8 changes `< (3,8,3)` -> `< (3,9,0)` and message '3.8.3'->'3.9.0'; raise ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version). The spec's requiredMin=[3,9,0] and errorMessage prefix match EXACTLY. F2P test input (3,8,11,1)/'3.8.11.1' -> rejected with 'SQLite 3.9.0 or later is required (found 3.8.11.1).' matches spec.
4. Adversarial differentials (all 0 diffs): (a) versionLt vs Python tuple `<` over prefix/extension/equal/boundary tuples [(),(3,),(3,9),(3,9,0),(3,9,0,0),(3,8,999999),(3,10),(4,),(2,),(3,8,3),(3,8,11,1)]; Python lexicographic-with-prefix rule reproduced exactly. (b) '%s' concatenation model vs real Python % formatting over tricky strings ('', '%s', '50%', '%%', '\n', quotes, unicode) — %s with a str operand never re-interprets, so concatenation is faithful. (c) conformance_check.py: 120010 fuzzed inputs, 0 disagreements (seed 13821).

Both branches of the spec are pinned to equality (result = error(...) / result = ok ()), so the spec is not too weak; and every pinned value agrees with the real repo, so it is not too strong / drifted. No diverging input exists. Threshold, message string, ordering semantics, and error/ok mapping all faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl/proof elided) reviewed for gold-edit leakage beyond the public problem_statement (hints_text excluded).

Gold edit: bump threshold (3,8,3)->(3,9,0) and update message 'SQLite 3.8.3...'->'SQLite 3.9.0...' in django/db/backends/sqlite3/base.py::check_sqlite_version.

Public problem_statement already discloses the new threshold explicitly: 'Drop support for SQLite < 3.9.0', 'supported on SQLite 3.9.0+', 'SQLite 3.9.0 was released in October 2015'. So 3.9.0 — the sole discriminating value of the fix — is public.

Spec-view content: requiredMin := [3,9,0] and "SQLite 3.9.0 or later is required (found " embed only 3.9.0 (public). The spec view does NOT reveal: the buggy old value 3.8.3, the F2P input (3,8,11,1), the patched file path django/db/backends/sqlite3/base.py, the patched symbol check_sqlite_version, any diff marker, or any bug/fix narration. Comments describe behavior abstractly ('minimum supported version', 'matching Python tuple <'). The leak-bearing material (old value 3.8.3, F2P tuple, symbol, path) resides only in auditor-only refinement.md/mapping.md, which are NOT part of the consumer spec view.

Mechanical checks: leakage.screen() over the lean spec view PASSES (no hard failures). markers.same_spec(Solution.lean, Solution_prepatch.lean) = True, so the judged spec region is the frozen consumer view. No relaxation flag/RELAXED_LEAKAGE.md present, and none needed.

Conclusion: the spec pins correct behavior using only the threshold the task publicly asks for; nothing exceeds the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
