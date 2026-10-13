# P2 adversarial audit — django__django-14792

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,9 +48,6 @@
 def implementation_getTimezoneName
     (tzLabel : Option String) (tzStr : String) : String := Id.run do
   let mut name := tzStr
-  match tzLabel with
-  | some s => if s ≠ "" then name := s
-  | none => pure ()
   return name
 -- impl-end
 
@@ -64,7 +61,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,8 @@
 
 -- impl-start
 def implementation_getTimezoneName
-    (tzLabel : Option String) (tzStr : String) : String := Id.run do
-  let mut name := tzStr
-  match tzLabel with
-  | some s => if s ≠ "" then name := s
-  | none => pure ()
-  return name
+    (tzLabel : Option String) (tzStr : String) : String :=
+  tzLabel.getD tzStr
 -- impl-end
 
 -- proof-start
@@ -64,7 +60,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     (tzLabel : Option String) (tzStr : String) : String := Id.run do
   let mut name := tzStr
   match tzLabel with
-  | some s => if s ≠ "" then name := s
+  | some s => if s = "" then name := s
   | none => pure ()
   return name
 -- impl-end
@@ -64,7 +64,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     (tzLabel : Option String) (tzStr : String) : String := Id.run do
   let mut name := tzStr
   match tzLabel with
-  | some s => if s ≠ "" then name := s
+  | some s => if s.length > 3 then name := s
   | none => pure ()
   return name
 -- impl-end
@@ -64,7 +64,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     (tzLabel : Option String) (tzStr : String) : String := Id.run do
   let mut name := tzStr
   match tzLabel with
-  | some s => if s ≠ "" then name := s
+  | some s => if s ≠ "" then name := s ++ "x"
   | none => pure ()
   return name
 -- impl-end
@@ -64,7 +64,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,7 @@
 
 -- impl-start
 def implementation_getTimezoneName
-    (tzLabel : Option String) (tzStr : String) : String := Id.run do
-  let mut name := tzStr
-  match tzLabel with
-  | some s => if s ≠ "" then name := s
-  | none => pure ()
-  return name
+    (tzLabel : Option String) (tzStr : String) : String := ""
 -- impl-end
 
 -- proof-start
@@ -64,7 +59,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     (tzLabel : Option String) (tzStr : String) : String := Id.run do
   let mut name := tzStr
   match tzLabel with
-  | some s => if s ≠ "" then name := s
+  | some s => if s ≠ "" then name := tzStr else name := s
   | none => pure ()
   return name
 -- impl-end
@@ -64,7 +64,6 @@
   constructor
   · intro s hs hne
     subst hs
-    simp only [Id.run, if_pos hne]
-    rfl
-  · rintro (h | h) <;> subst h <;> rfl
+    simp_all [Id.run]
+  · rintro (h | h) <;> subst h <;> simp_all [Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the display name of a time zone.

A time zone exposes two pieces of textual information about itself:

  * a short self-reported label (for example a constant UTC-offset designation),
    which may be absent altogether or be the empty string when the zone does not
    advertise one; and
  * a full textual form that is always available.

The display name is the short label whenever it is present and non-empty;
otherwise it is the full textual form. This makes constant-offset zones present
themselves by their offset designation while named zones fall back to their full
textual form.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the short self-reported label and the
-- full textual form of the time zone enter as plain data (an optional string and
-- a string), and the only operation performed is choosing between them by
-- truthiness. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no auxiliary helpers needed)
-- pure-end

-- post-conditions-start
/-- The display name is fully pinned to the inputs:

  * when the short self-reported label is present and non-empty, the result is
    exactly that label;
  * otherwise (the label is absent or empty) the result is exactly the full
    textual form.

Both cases together determine the result for every input, so no output component
is left free. -/
def problem_spec_getTimezoneName
    (tzLabel : Option String) (tzStr : String) (result : String) : Prop :=
  (∀ s, tzLabel = some s → s ≠ "" → result = s) ∧
  ((tzLabel = none ∨ tzLabel = some "") → result = tzStr)
-- post-conditions-end

-- impl-start
def implementation_getTimezoneName
    (tzLabel : Option String) (tzStr : String) : String := Id.run do
  let mut name := tzStr
  match tzLabel with
  | some s => if s ≠ "" then name := s
  | none => pure ()
  return name
-- impl-end

-- proof-start
theorem correct_getTimezoneName :
    ∀ (tzLabel : Option String) (tzStr : String),
      problem_spec_getTimezoneName tzLabel tzStr
        (implementation_getTimezoneName tzLabel tzStr) := by
  intro tzLabel tzStr
  unfold problem_spec_getTimezoneName implementation_getTimezoneName
  constructor
  · intro s hs hne
    subst hs
    simp only [Id.run, if_pos hne]
    rfl
  · rintro (h | h) <;> subst h <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the output over the ENTIRE input domain Option String: clause1 (∀ s, tzLabel=some s → s≠"" → result=s) and clause2 ((tzLabel=none ∨ tzLabel=some "") → result=tzStr). These two clauses are exhaustive AND mutually exclusive over Option String — some(nonempty)→s, some("")→tzStr, none→tzStr — leaving no output component free. Therefore any behaviorally-distinct impl must violate a concrete clause and cannot close correct_getTimezoneName.

Attacked with 7 same-spec wrong impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec on backend 'lean'; regions 1-45 confirmed byte-identical). Verifications run concurrently in two ≤4-wide background batches via `bash scripts/lean_verify.sh <f>`:
  atk_1 prepatch bug (always returns tzStr, never consults label) — exit 1 (unsolved goals). Reproduces the real prepatch/F2P bug (matches G-DIFF). prepatch_reproduced=true.
  atk_2 partial-domain (tzLabel.getD tzStr — returns "" for some "", must be tzStr) — exit 1.
  atk_3 reversed truthiness (keeps label only when s="") — exit 1.
  atk_4 boundary off-by (uses label only if s.length>3, drops short nonempty labels like "+10") — exit 1.
  atk_5 control-flow-effect (label ++ "x", breaks clause1 exact equality) — exit 1.
  atk_6 ungrounded-oracle echo (always "") — exit 1.
  atk_7 swapped selection (uses tzStr when nonempty, s when empty) — exit 1.
Every attack failed with genuine 'error: unsolved goals' (not incidental/tactic artifacts) — no closing proof exists. Positive control pos.lean (= Solution.lean) verifies exit 0; `#print axioms correct_getTimezoneName` → 'does not depend on any axioms' (clean).

Because NO attack produced a closing clean-axiom proof, there is no verifying-but-wrong impl to materialize a faithful patch for; patches={} and no resolve run was required (Protocol step 2 is vacuous here). This is the correct outcome for a fully-pinned total spec, not missing evidence.

Refinement audit: refinement.md declares all 4 legs R (rows 1-3) or I (row 4), NO A row — consistent with meta.json axioms=[], deep_model_references=[], G-AX skip stub. No kind-3 legs. There are NO A-legs (no consumed callee axiom, no deep-model reference): both observables timezone.tzname(None) (↔ Option String) and str(timezone) (↔ String) enter as plain data; the only op is Python-`or` truthiness selection, modeled faithfully as Lean match + `if s ≠ ""`. The R/I correspondence (or's falsy cases for str|None are exactly None and '') is exactly what the spec's two clauses encode, and is mechanically covered by G-CONF (120000 inputs, 0 disagreements per meta.json). Model↔patch correspondence holds; nothing ungrounded to audit for callee fidelity.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the display name of a time zone.

A time zone exposes two pieces of textual information about itself:

  * a short self-reported label (for example a constant UTC-offset designation),
    which may be absent altogether or be the empty string when the zone does not
    advertise one; and
  * a full textual form that is always available.

The display name is the short label whenever it is present and non-empty;
otherwise it is the full textual form. This makes constant-offset zones present
themselves by their offset designation while named zones fall back to their full
textual form.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the short self-reported label and the
-- full textual form of the time zone enter as plain data (an optional string and
-- a string), and the only operation performed is choosing between them by
-- truthiness. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no auxiliary helpers needed)
-- pure-end

-- post-conditions-start
/-- The display name is fully pinned to the inputs:

  * when the short self-reported label is present and non-empty, the result is
    exactly that label;
  * otherwise (the label is absent or empty) the result is exactly the full
    textual form.

Both cases together determine the result for every input, so no output component
is left free. -/
def problem_spec_getTimezoneName
    (tzLabel : Option String) (tzStr : String) (result : String) : Prop :=
  (∀ s, tzLabel = some s → s ≠ "" → result = s) ∧
  ((tzLabel = none ∨ tzLabel = some "") → result = tzStr)
-- post-conditions-end

-- impl-start
def implementation_getTimezoneName
    (tzLabel : Option String) (tzStr : String) : String := Id.run do
  let mut name := tzStr
  match tzLabel with
  | some s => if s ≠ "" then name := s
  | none => pure ()
  return name
-- impl-end

-- proof-start
theorem correct_getTimezoneName :
    ∀ (tzLabel : Option String) (tzStr : String),
      problem_spec_getTimezoneName tzLabel tzStr
        (implementation_getTimezoneName tzLabel tzStr) := by
  intro tzLabel tzStr
  unfold problem_spec_getTimezoneName implementation_getTimezoneName
  constructor
  · intro s hs hne
    subst hs
    simp only [Id.run, if_pos hne]
    rfl
  · rintro (h | h) <;> subst h <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the output over the ENTIRE input domain Option String: clause1 (∀ s, tzLabel=some s → s≠"" → result=s) and clause2 ((tzLabel=none ∨ tzLabel=some "") → result=tzStr). These two clauses are exhaustive AND mutually exclusive over Option String — some(nonempty)→s, some("")→tzStr, none→tzStr — leaving no output component free. Therefore any behaviorally-distinct impl must violate a concrete clause and cannot close correct_getTimezoneName.

Attacked with 7 same-spec wrong impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec on backend 'lean'; regions 1-45 confirmed byte-identical). Verifications run concurrently in two ≤4-wide background batches via `bash scripts/lean_verify.sh <f>`:
  atk_1 prepatch bug (always returns tzStr, never consults label) — exit 1 (unsolved goals). Reproduces the real prepatch/F2P bug (matches G-DIFF). prepatch_reproduced=true.
  atk_2 partial-domain (tzLabel.getD tzStr — returns "" for some "", must be tzStr) — exit 1.
  atk_3 reversed truthiness (keeps label only when s="") — exit 1.
  atk_4 boundary off-by (uses label only if s.length>3, drops short nonempty labels like "+10") — exit 1.
  atk_5 control-flow-effect (label ++ "x", breaks clause1 exact equality) — exit 1.
  atk_6 ungrounded-oracle echo (always "") — exit 1.
  atk_7 swapped selection (uses tzStr when nonempty, s when empty) — exit 1.
Every attack failed with genuine 'error: unsolved goals' (not incidental/tactic artifacts) — no closing proof exists. Positive control pos.lean (= Solution.lean) verifies exit 0; `#print axioms correct_getTimezoneName` → 'does not depend on any axioms' (clean).

Because NO attack produced a closing clean-axiom proof, there is no verifying-but-wrong impl to materialize a faithful patch for; patches={} and no resolve run was required (Protocol step 2 is vacuous here). This is the correct outcome for a fully-pinned total spec, not missing evidence.

Refinement audit: refinement.md declares all 4 legs R (rows 1-3) or I (row 4), NO A row — consistent with meta.json axioms=[], deep_model_references=[], G-AX skip stub. No kind-3 legs. There are NO A-legs (no consumed callee axiom, no deep-model reference): both observables timezone.tzname(None) (↔ Option String) and str(timezone) (↔ String) enter as plain data; the only op is Python-`or` truthiness selection, modeled faithfully as Lean match + `if s ≠ ""`. The R/I correspondence (or's falsy cases for str|None are exactly None and '') is exactly what the spec's two clauses encode, and is mechanically covered by G-CONF (120000 inputs, 0 disagreements per meta.json). Model↔patch correspondence holds; nothing ungrounded to audit for callee fidelity.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Solution.lean compiles clean via lean_verify.sh (exit 0) and `#print axioms correct_getTimezoneName` reports no axiom dependence (no sorryAx). Real post-patch callee `_get_timezone_name(timezone)` = `timezone.tzname(None) or str(timezone)`. `tzname(None)` yields `str|None` (tzinfo protocol); Python `or` returns the left operand iff truthy, and a str is falsy only for "". Modeled as `tzLabel : Option String` (None↔none, str v↔some v; identity String↔str bijection) and `tzStr : String` = str(timezone). Spec: (some s, s≠"" ⇒ s) ∧ (none ∨ some "" ⇒ tzStr) is EXHAUSTIVE over the Option and pins the result exactly. Every case matches the real callee: nonempty label → label; None or empty label → full form. Edge case: whitespace label " " is Python-truthy and satisfies " "≠"", so both return the label — consistent. No input where the modeled function disagrees with the real callee; the spec is neither too strong nor drifting. The two clauses are complete and leave no output component free (implication is bidirectional coverage of the Option). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: passed=True, no hard failures). Semantic review of the lean spec view (docstring + problem_spec_getTimezoneName post-condition; impl/proof elided by the projection) confirms no disclosure of the gold edit beyond the public problem_statement.

Gold edit: `_get_timezone_name` return changed from `str(timezone)` to `timezone.tzname(None) or str(timezone)`.

Public problem_statement already names `_get_timezone_name` and fully specifies the target behavior: on 3.1 the fixed-offset zone Etc/GMT-10 displayed as its offset label '+10', on 3.2 it wrongly returns the full name 'Etc/GMT-10'; the fix must restore offset-designation display for fixed-offset zones while named zones keep their full form. Thus the desired behavior (prefer the short offset label when present, else the full textual form) is public.

Spec view relative to that baseline:
- Docstring/post-condition describe the required behavior (short label when present & non-empty else full textual form), an abstraction of the already-public task — not the specific edit.
- No `tzname`, no `str(timezone)`, no Python `or` idiom, no file path (django/utils/timezone.py), no module path, no diff markers, no patched-symbol echo, no bug/fix narration.
- The `some ""` empty-string fallback branch is the natural truthiness boundary implied by the task, not a disclosure of the gold mechanism.

The spec necessarily encodes the required behavior, but that behavior is already fully public; the view reveals nothing of the gold implementation edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
