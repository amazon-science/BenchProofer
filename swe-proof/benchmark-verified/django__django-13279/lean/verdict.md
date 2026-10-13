# P2 adversarial audit — django__django-13279

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
None. No same-spec wrong impl closes correct_encode. The spec problem_spec_encode fully pins result in BOTH branches over the opaque carriers: (algo='sha1' -> result=legacyEncode session) AND (algo!='sha1' -> result=modernEncode session). Because legacyEncode and modernEncode are distinct opaque symbols with no exploitable properties, any verifying impl must reproduce the exact dispatch; every deviation is caught by the correctness proof (type mismatch / rfl failure).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,8 +59,6 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
-    return legacyEncode session
   return modernEncode session
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,8 +60,8 @@
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
   if algo == "sha1" then
-    return legacyEncode session
-  return modernEncode session
+    return modernEncode session
+  return legacyEncode session
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
+  if algo == "sha256" then
     return legacyEncode session
   return modernEncode session
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,9 +59,7 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
-    return legacyEncode session
-  return modernEncode session
+  return legacyEncode session
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,9 +59,7 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
-    return legacyEncode session
-  return modernEncode session
+  return ""
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
+  if algo.length == 4 then
     return legacyEncode session
   return modernEncode session
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_encode
     (algo : String) (session : List (String × String)) : String := Id.run do
-  if algo == "sha1" then
+  if algo.startsWith "sha1" then
     return legacyEncode session
   return modernEncode session
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Serializing session data into a transport string, where two interchangeable
serialization schemes coexist during a cross-version transition.

A deployment may run several instances of the same project side by side while it
moves between two release lines, and those instances must be able to read each
other's serialized session data. To make that possible, the project exposes a
configured serialization-format identifier that selects which of two
interchangeable schemes is produced when session data is serialized:

  * a designated compatibility scheme, requested by the identifier value
    `"sha1"`, that produces strings in the older interchange format (the format
    the matching reader already accepts); and
  * the standard scheme used otherwise.

The desired behavior is therefore a dispatch on the configured identifier: when
the identifier is `"sha1"`, the session data is serialized with the
compatibility scheme; for every other identifier value, it is serialized with
the standard scheme. The chosen scheme fully determines the produced string.
-/

-- axioms-start
/-- The compatibility serialization scheme: it serializes session data into the
older interchange-format string. It is consumed here as an opaque carrier — the
behavior modeled in this bundle is *which* scheme is selected for given session
data, not the internal byte layout of the scheme itself. -/
opaque legacyEncode : List (String × String) → String

/-- The standard serialization scheme used outside the compatibility case. Like
`legacyEncode`, it is an opaque carrier: only the fact that it is the scheme
selected in the non-compatibility case is modeled, not its internal details. -/
opaque modernEncode : List (String × String) → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the single
-- dispatch between the two serialization schemes on the configured identifier.
-- pure-end

-- post-conditions-start
/-- The produced string is fully pinned to the inputs:

  * when the configured serialization-format identifier is `"sha1"`, it is
    exactly the compatibility scheme applied to the session data;
  * for every other identifier value, it is exactly the standard scheme applied
    to the session data.

Both cases together determine the result for every input, so no part of the
output is left free. -/
def problem_spec_encode
    (algo : String) (session : List (String × String)) (result : String) : Prop :=
  (algo = "sha1" → result = legacyEncode session) ∧
  (algo ≠ "sha1" → result = modernEncode session)
-- post-conditions-end

-- impl-start
def implementation_encode
    (algo : String) (session : List (String × String)) : String := Id.run do
  if algo == "sha1" then
    return legacyEncode session
  return modernEncode session
-- impl-end

-- proof-start
theorem correct_encode :
    ∀ (algo : String) (session : List (String × String)),
      problem_spec_encode algo session
        (implementation_encode algo session) := by
  intro algo session
  unfold problem_spec_encode implementation_encode
  by_cases h : algo = "sha1"
  · subst h
    refine ⟨fun _ => rfl, fun hne => ?_⟩
    exact absurd rfl hne
  · have hb : (algo == "sha1") = false := by
      simpa using h
    refine ⟨fun habs => absurd habs h, fun _ => ?_⟩
    simp only [Id.run, hb]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Worktree @ base 6e9c5ee88f, encode source matches patch.diff.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec + get_backend('lean').

VERIFICATION (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of 4:
- pos_control.lean EXIT=0 (verifies clean)
- atk_1 (prepatch bug: unconditional 'return modernEncode session', omits dispatch) EXIT=1 -> type mismatch at correct_encode algo='sha1' goal 'modernEncode session = legacyEncode session'. PREPATCH REPRODUCED.
- atk_2 (swapped branches: sha1->modern, else->legacy) EXIT=1
- atk_3 (wrong literal: algo=='sha256') EXIT=1
- atk_4 (unconditional 'return legacyEncode session') EXIT=1
- atk_5 (ungrounded-oracle echo: 'return ""') EXIT=1 -> ''=legacyEncode session unprovable
- atk_6 (boundary/partial-domain: algo.length==4) EXIT=1 -> rfl failed (length==4 does not decide algo=='sha1')
- atk_7 (control-flow-effect: algo.startsWith "sha1") EXIT=1
All 7 fail with genuine correctness-proof errors (type mismatch / unsolved rfl at correct_encode), NOT unrelated syntax/import errors.

CLEAN-AXIOM CHECK: appended '#print axioms correct_encode' to pos_control -> EXIT=0, "'correct_encode' depends on axioms: [propext]" (no sorryAx, no native_decide, no Classical beyond propext). opaque carriers introduce no axioms.

MATERIALIZE/RESOLVE: ZERO attacks closed with a clean-axiom proof, so there is nothing to materialize and no resolve run is required (protocol step 2 vacuously satisfied — no verify-but-wrong impl exists to break the spec).

REFINEMENT.MD A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[]. Solution.lean declares legacyEncode/modernEncode as 'opaque' (NOT axiom) — opaque introduces no proof obligation and no axiom. No 'axiom _prop' exists; the proof consumes NO property of either carrier (closes by case analysis on algo=='sha1'). Every leg is R (type-refinement, ops #1-3) or the implicit I control-flow skeleton; NO A-consumed, NO kind-3. Correspondence holds: legacyEncode<->_legacy_encode (real added callee), modernEncode<->signing.dumps(...) (real unchanged pre-patch body), both grounded and G-CONF-realized. axiom_check.py is a skip stub, consistent.

CONCLUSION: spec is TIGHT — verify => correct. No verify-not-correct gap found across 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch, swapped, wrong-literal).

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
None. No same-spec wrong impl closes correct_encode. The spec problem_spec_encode fully pins result in BOTH branches over the opaque carriers: (algo='sha1' -> result=legacyEncode session) AND (algo!='sha1' -> result=modernEncode session). Because legacyEncode and modernEncode are distinct opaque symbols with no exploitable properties, any verifying impl must reproduce the exact dispatch; every deviation is caught by the correctness proof (type mismatch / rfl failure).
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
Serializing session data into a transport string, where two interchangeable
serialization schemes coexist during a cross-version transition.

A deployment may run several instances of the same project side by side while it
moves between two release lines, and those instances must be able to read each
other's serialized session data. To make that possible, the project exposes a
configured serialization-format identifier that selects which of two
interchangeable schemes is produced when session data is serialized:

  * a designated compatibility scheme, requested by the identifier value
    `"sha1"`, that produces strings in the older interchange format (the format
    the matching reader already accepts); and
  * the standard scheme used otherwise.

The desired behavior is therefore a dispatch on the configured identifier: when
the identifier is `"sha1"`, the session data is serialized with the
compatibility scheme; for every other identifier value, it is serialized with
the standard scheme. The chosen scheme fully determines the produced string.
-/

-- axioms-start
/-- The compatibility serialization scheme: it serializes session data into the
older interchange-format string. It is consumed here as an opaque carrier — the
behavior modeled in this bundle is *which* scheme is selected for given session
data, not the internal byte layout of the scheme itself. -/
opaque legacyEncode : List (String × String) → String

/-- The standard serialization scheme used outside the compatibility case. Like
`legacyEncode`, it is an opaque carrier: only the fact that it is the scheme
selected in the non-compatibility case is modeled, not its internal details. -/
opaque modernEncode : List (String × String) → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the single
-- dispatch between the two serialization schemes on the configured identifier.
-- pure-end

-- post-conditions-start
/-- The produced string is fully pinned to the inputs:

  * when the configured serialization-format identifier is `"sha1"`, it is
    exactly the compatibility scheme applied to the session data;
  * for every other identifier value, it is exactly the standard scheme applied
    to the session data.

Both cases together determine the result for every input, so no part of the
output is left free. -/
def problem_spec_encode
    (algo : String) (session : List (String × String)) (result : String) : Prop :=
  (algo = "sha1" → result = legacyEncode session) ∧
  (algo ≠ "sha1" → result = modernEncode session)
-- post-conditions-end

-- impl-start
def implementation_encode
    (algo : String) (session : List (String × String)) : String := Id.run do
  if algo == "sha1" then
    return legacyEncode session
  return modernEncode session
-- impl-end

-- proof-start
theorem correct_encode :
    ∀ (algo : String) (session : List (String × String)),
      problem_spec_encode algo session
        (implementation_encode algo session) := by
  intro algo session
  unfold problem_spec_encode implementation_encode
  by_cases h : algo = "sha1"
  · subst h
    refine ⟨fun _ => rfl, fun hne => ?_⟩
    exact absurd rfl hne
  · have hb : (algo == "sha1") = false := by
      simpa using h
    refine ⟨fun habs => absurd habs h, fun _ => ?_⟩
    simp only [Id.run, hb]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Worktree @ base 6e9c5ee88f, encode source matches patch.diff.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec + get_backend('lean').

VERIFICATION (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of 4:
- pos_control.lean EXIT=0 (verifies clean)
- atk_1 (prepatch bug: unconditional 'return modernEncode session', omits dispatch) EXIT=1 -> type mismatch at correct_encode algo='sha1' goal 'modernEncode session = legacyEncode session'. PREPATCH REPRODUCED.
- atk_2 (swapped branches: sha1->modern, else->legacy) EXIT=1
- atk_3 (wrong literal: algo=='sha256') EXIT=1
- atk_4 (unconditional 'return legacyEncode session') EXIT=1
- atk_5 (ungrounded-oracle echo: 'return ""') EXIT=1 -> ''=legacyEncode session unprovable
- atk_6 (boundary/partial-domain: algo.length==4) EXIT=1 -> rfl failed (length==4 does not decide algo=='sha1')
- atk_7 (control-flow-effect: algo.startsWith "sha1") EXIT=1
All 7 fail with genuine correctness-proof errors (type mismatch / unsolved rfl at correct_encode), NOT unrelated syntax/import errors.

CLEAN-AXIOM CHECK: appended '#print axioms correct_encode' to pos_control -> EXIT=0, "'correct_encode' depends on axioms: [propext]" (no sorryAx, no native_decide, no Classical beyond propext). opaque carriers introduce no axioms.

MATERIALIZE/RESOLVE: ZERO attacks closed with a clean-axiom proof, so there is nothing to materialize and no resolve run is required (protocol step 2 vacuously satisfied — no verify-but-wrong impl exists to break the spec).

REFINEMENT.MD A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[]. Solution.lean declares legacyEncode/modernEncode as 'opaque' (NOT axiom) — opaque introduces no proof obligation and no axiom. No 'axiom _prop' exists; the proof consumes NO property of either carrier (closes by case analysis on algo=='sha1'). Every leg is R (type-refinement, ops #1-3) or the implicit I control-flow skeleton; NO A-consumed, NO kind-3. Correspondence holds: legacyEncode<->_legacy_encode (real added callee), modernEncode<->signing.dumps(...) (real unchanged pre-patch body), both grounded and G-CONF-realized. axiom_check.py is a skip stub, consistent.

CONCLUSION: spec is TIGHT — verify => correct. No verify-not-correct gap found across 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch, swapped, wrong-literal).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with lean backend). (2) Solution.lean compiles (lean_verify exit 0); #print axioms correct_encode = [propext] only, no sorryAx — proof is genuine. Real patched repo (@ base 6e9c5ee88f) SessionBase.encode is exactly: if settings.DEFAULT_HASHING_ALGORITHM=='sha1': return self._legacy_encode(session_dict); else return signing.dumps(..., compress=True). (4) Modeled problem_spec_encode pins result to legacyEncode session when algo=='sha1' and modernEncode session otherwise — precisely the real dispatch. legacyEncode/modernEncode are opaque carriers with NO consumed axioms (axioms region declares only opaque signatures, meta axioms=[], deep_model_references=[]), so the spec constrains ONLY the dispatch, not the internal byte layout — it is not too strong. (5) The one plausible drift — signing.dumps is time-dependent while modernEncode is modeled as pure(session) — is a deliberate abstraction (the modeled behavior is WHICH scheme is selected, not its bytes) and is handled by G-CONF freezing the clock; G-CONF ran 100000 fuzzed (algo, session_dict) inputs with 0 disagreements against the real callee. No input distinguishes the modeled function from the real encode on the modeled property. Spec is a faithful (neither too strong nor drifting) abstraction of the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean, sha256 270b1cdf… matching G-HYGIENE) discloses only what the PUBLIC problem_statement already states: the discriminating value 'sha1' ("setting DEFAULT_HASHING_ALGORITHM to 'sha1'") and the dispatch itself ("We could use the legacy encode() when DEFAULT_HASHING_ALGORITHM == 'sha1'"). The docstring/post-condition encode exactly that legacy-when-sha1 vs modern-otherwise dispatch — no information beyond problem_statement. Both schemes are declared `opaque` carriers, so the gold's internal specifics (_legacy_encode body: base64/HMAC hash; signing.dumps salt=key_salt/compress=True; _legacy_decode round-trip) are NOT exposed in the spec view — those appear only in mapping.md/refinement.md, which are outside the spec-view surface. impl and proof regions elided. same_spec(Solution, Solution_prepatch)=True. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
