# P2 adversarial audit — django__django-13212

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := oldParams }
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,13 +118,8 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
-    let result : Except Report Unit :=
-      if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
-    return result
+
+    return Except.ok ()
     -- impl-end
 
 prove_correct checkValue by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
-      if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      if isValid then Except.error (buildReport code oldParams value)
+      else Except.ok ()
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := [], params := oldParams ++ [("value", value)] }
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := oldParams ++ [("val", value)] }
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := oldParams ++ [("value", [])] }
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := [("value", value)] }
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,10 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := [("value", value)] ++ oldParams }
     return result
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -118,12 +118,14 @@
     lookupKey k (buildReport code oldParams value).params = some v
   do
     -- impl-start
-    -- The validity test is unchanged; only the failing branch's report changes.
-    -- Accept a valid input with no report; reject an invalid one with the report
-    -- that additionally carries the input bound to the templating key.
+
+    let newParams : List (String × List Char) :=
+      match oldParams with
+      | [] => []
+      | ps => ps ++ [("value", value)]
     let result : Except Report Unit :=
       if isValid then Except.ok ()
-      else Except.error (buildReport code oldParams value)
+      else Except.error { code := code, params := newParams }
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   unchanged sub-step — the per-input validity test — is modeled as a FREE
   Boolean `isValid` (see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract (it is strictly weaker than any
   concrete test — directive 7). The behaviour this bundle actually pins — how
   the rejection report is constructed on the failing branch — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of a rejection report: a short machine `code` and an
   ordered list of named substitution bindings (`params`) consulted by message
   templating. These are the only fields the desired behaviour constrains
   (mapping.md §2). A report is carried by `Except.error`; acceptance is
   `Except.ok ()`. -/
structure Report where
  code : List Char
  params : List (String × List Char)
  deriving DecidableEq

/- Look up a named binding in the ordered params list — the front-to-back scan a
   `%(name)s` template performs. First match wins (mirrors dict semantics for the
   appended-last key, given the keys already present are distinct from it). -/
def lookupKey (k : String) : List (String × List Char) → Option (List Char)
  | []            => none
  | (k', v) :: rest => if k' = k then some v else lookupKey k rest

/- The rejection report built on the failing branch: the machine `code`, the
   bindings already present, AND the input itself bound to the `"value"` key so a
   custom message template can interpolate it. This is the deep model of the
   constructed report; the appended `("value", value)` is the whole of the
   desired behaviour. -/
def buildReport (code : List Char) (oldParams : List (String × List Char))
    (value : List Char) : Report :=
  { code := code, params := oldParams ++ [("value", value)] }

/- The outcome of validating one input: acceptance carries nothing; rejection
   carries the report built for the failing branch. -/
def checkOutcome (isValid : Bool) (code : List Char)
    (oldParams : List (String × List Char)) (value : List Char) :
    Except Report Unit :=
  if isValid then Except.ok () else Except.error (buildReport code oldParams value)

@[grind] lemma checkOutcome_ok (code oldParams value) :
    checkOutcome true code oldParams value = Except.ok () := rfl
@[grind] lemma checkOutcome_err (code oldParams value) :
    checkOutcome false code oldParams value
      = Except.error (buildReport code oldParams value) := rfl

/- Appending a binding under a key absent from the list makes that key resolve to
   the appended value: the scan misses every earlier entry and finds the tail. -/
@[grind] lemma lookupKey_append_fresh (k : String) (v : List Char)
    (xs : List (String × List Char)) (h : lookupKey k xs = none) :
    lookupKey k (xs ++ [(k, v)]) = some v := by
  induction xs with
  | nil => simp [lookupKey]
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp [hk] at h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h

/- Appending anything preserves a key that already resolves: the first match is
   found before the appended tail is reached (the unchanged-frame guarantee for
   the pre-existing bindings — directive 5). -/
@[grind] lemma lookupKey_append_pres (k : String) (v : List Char)
    (ys : List (String × List Char)) (xs : List (String × List Char))
    (h : lookupKey k xs = some v) :
    lookupKey k (xs ++ ys) = some v := by
  induction xs with
  | nil => simp [lookupKey] at h
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp only [hk, reduceIte] at h ⊢; exact h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Check one input and, on failure, construct the rejection report. The input
   `value` (as a custom message template would stringify it), the report's
   machine `code`, and any bindings the report already carries (`oldParams`) are
   read-only; `isValid` abstracts the input's (unchanged) validity test. Desired
   behaviour: a passing input is accepted with no report; a failing input is
   rejected with a report that keeps its `code` and every pre-existing binding
   AND additionally binds the input itself to the `"value"` key, so a custom
   message can interpolate the offending input. `require`: the report does not
   already bind `"value"` (none of the real sites do — mapping.md §1.1/§2). -/
method checkValue (value : List Char) (code : List Char)
    (oldParams : List (String × List Char)) (isValid : Bool)
    return (out : Except Report Unit)
  require lookupKey "value" oldParams = none
  ensures out = checkOutcome isValid code oldParams value
  ensures isValid = true → out = Except.ok ()
  ensures isValid = false → out = Except.error (buildReport code oldParams value)
  ensures isValid = false →
    lookupKey "value" (buildReport code oldParams value).params = some value
  ensures (buildReport code oldParams value).code = code
  ensures ∀ k v, k ≠ "value" → lookupKey k oldParams = some v →
    lookupKey k (buildReport code oldParams value).params = some v
  do
    -- impl-start

    let rej : Report := buildReport code oldParams value
    if !isValid then
      return Except.error rej
    else
      return Except.ok ()
    -- impl-end

prove_correct checkValue by
  loom_solve <;>
    simp_all [buildReport, lookupKey_append_fresh, lookupKey_append_pres]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the output via ensures_1 (out = checkOutcome isValid code oldParams value) plus discriminating clauses ensures_4 (isValid=false -> out = Except.error (buildReport code oldParams value)), ensures_5 (lookupKey "value" (buildReport...).params = some value), ensures_6 (code preserved), ensures_7 (frame preservation of pre-existing keys). All carriers (buildReport/checkOutcome/lookupKey) are transparent defs, not opaque oracles.

ENV: real project root. All attacks same_spec=True vs bundle Solution.lean (velvet backend).

### VERIFICATION RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in batches of 4):
- atk_1 prepatch bug (report = {code, oldParams}, no value append) -> exit 1 (metavariables 'checkValue_correct'; unsolved ensures_4/ensures_6). PREPATCH REPRODUCED (byte-identical to bundle Solution_prepatch.lean impl).
- atk_2 always accept (return Except.ok ()) -> exit 1 (unsolved ensures_4/ensures_5).
- atk_3 inverted validity (control-flow-effect: branches swapped) -> exit 1 (unsolved ensures_4, if isValid then error else ok).
- atk_4 empty code in report -> exit 1 (unsolved; code != []).
- atk_5 value under wrong key "val" -> exit 1 (unsolved ensures_5 lookupKey "value").
- atk_6 value bound to empty list (ungrounded/dropped content) -> exit 1 (unsolved value-binding).
- atk_7 drop oldParams, keep only [("value",value)] -> exit 1 (unsolved frame ensures_7).
- atk_8 order-echo: prepend [("value",value)]++oldParams instead of append -> exit 1 (unsolved ensures_4 exact-equality: ("value",value)::oldParams != oldParams++[("value",value)]).
- atk_9 partial-domain: append value only when oldParams nonempty (empty->[]) -> exit 1 (unsolved). NOTE first draft had a Lean syntax error (parse fail = weak evidence); rewritten with valid match syntax, re-checked same_spec=True, re-verified -> genuine semantic exit 1 (unsolved goals, not parse).
- POSITIVE CONTROL atk_pos (correct, structurally different: error hoisted into let rej, branch via `if !isValid`) -> exit 0, clean, no sorry/admit. Spec is non-vacuous.

No attack file contains sorry/admit/native_decide (scanned). All wrong-impl failures are genuine unsolved-goal / kernel-metavariable errors, NOT parse errors (verified atk_9 after syntax fix; all others parse cleanly and fail in prove_correct).

RESOLVE STEP: vacuous. Zero same-spec wrong impls VERIFIED, so there is no verifying-but-diverging candidate to materialize a faithful refined patch for; patches={} accordingly. verify=>correct is not falsified.

A-LEG / REFINEMENT AUDIT (focus per assignment): refinement.md declares NO A-consumed and NO A-reference rows (§C); every leg is R or I. Legitimate: (1) the one UNCHANGED callee (per-site validity test) is modeled as free Boolean isValid, quantified over ALL values in every postcondition (directive-7, strictly weaker than any concrete test) => owed no contract, G-AX skip by design, no axiom_check.py ships (django-16667 precedent). (2) The one CHANGED op (failure-branch report construction) is modeled DEEPLY via transparent defs buildReport/checkOutcome/lookupKey (no module-level axiom, no opaque oracle => no ungrounded-oracle echo possible; atk_6/atk_7/atk_8 confirm the postconditions are grounded in code/oldParams/value carriers and pin exact append equality). (3) No kind-3 (inexpressible-changed-op) leg. Model<->patch correspondence holds: append ("value",value) <-> patch.diff params={...,'value':value} across all 12 sites; `require lookupKey "value" oldParams = none` <-> no real site pre-binds 'value' (BaseValidator excluded, mapping.md §1.1). R/I legs are G-CONF's job (conformance_check.py present, seed 13212).

VERDICT: SOUND (≥5 distinct attacks run + prepatch + boundary/partial-domain/control-flow-effect/ungrounded-oracle-echo classes; none verifies; positive control verifies; A-legs sound). Spec is TIGHT; verify does NOT imply incorrect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   unchanged sub-step — the per-input validity test — is modeled as a FREE
   Boolean `isValid` (see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract (it is strictly weaker than any
   concrete test — directive 7). The behaviour this bundle actually pins — how
   the rejection report is constructed on the failing branch — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of a rejection report: a short machine `code` and an
   ordered list of named substitution bindings (`params`) consulted by message
   templating. These are the only fields the desired behaviour constrains
   (mapping.md §2). A report is carried by `Except.error`; acceptance is
   `Except.ok ()`. -/
structure Report where
  code : List Char
  params : List (String × List Char)
  deriving DecidableEq

/- Look up a named binding in the ordered params list — the front-to-back scan a
   `%(name)s` template performs. First match wins (mirrors dict semantics for the
   appended-last key, given the keys already present are distinct from it). -/
def lookupKey (k : String) : List (String × List Char) → Option (List Char)
  | []            => none
  | (k', v) :: rest => if k' = k then some v else lookupKey k rest

/- The rejection report built on the failing branch: the machine `code`, the
   bindings already present, AND the input itself bound to the `"value"` key so a
   custom message template can interpolate it. This is the deep model of the
   constructed report; the appended `("value", value)` is the whole of the
   desired behaviour. -/
def buildReport (code : List Char) (oldParams : List (String × List Char))
    (value : List Char) : Report :=
  { code := code, params := oldParams ++ [("value", value)] }

/- The outcome of validating one input: acceptance carries nothing; rejection
   carries the report built for the failing branch. -/
def checkOutcome (isValid : Bool) (code : List Char)
    (oldParams : List (String × List Char)) (value : List Char) :
    Except Report Unit :=
  if isValid then Except.ok () else Except.error (buildReport code oldParams value)

@[grind] lemma checkOutcome_ok (code oldParams value) :
    checkOutcome true code oldParams value = Except.ok () := rfl
@[grind] lemma checkOutcome_err (code oldParams value) :
    checkOutcome false code oldParams value
      = Except.error (buildReport code oldParams value) := rfl

/- Appending a binding under a key absent from the list makes that key resolve to
   the appended value: the scan misses every earlier entry and finds the tail. -/
@[grind] lemma lookupKey_append_fresh (k : String) (v : List Char)
    (xs : List (String × List Char)) (h : lookupKey k xs = none) :
    lookupKey k (xs ++ [(k, v)]) = some v := by
  induction xs with
  | nil => simp [lookupKey]
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp [hk] at h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h

/- Appending anything preserves a key that already resolves: the first match is
   found before the appended tail is reached (the unchanged-frame guarantee for
   the pre-existing bindings — directive 5). -/
@[grind] lemma lookupKey_append_pres (k : String) (v : List Char)
    (ys : List (String × List Char)) (xs : List (String × List Char))
    (h : lookupKey k xs = some v) :
    lookupKey k (xs ++ ys) = some v := by
  induction xs with
  | nil => simp [lookupKey] at h
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp only [hk, reduceIte] at h ⊢; exact h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Check one input and, on failure, construct the rejection report. The input
   `value` (as a custom message template would stringify it), the report's
   machine `code`, and any bindings the report already carries (`oldParams`) are
   read-only; `isValid` abstracts the input's (unchanged) validity test. Desired
   behaviour: a passing input is accepted with no report; a failing input is
   rejected with a report that keeps its `code` and every pre-existing binding
   AND additionally binds the input itself to the `"value"` key, so a custom
   message can interpolate the offending input. `require`: the report does not
   already bind `"value"` (none of the real sites do — mapping.md §1.1/§2). -/
method checkValue (value : List Char) (code : List Char)
    (oldParams : List (String × List Char)) (isValid : Bool)
    return (out : Except Report Unit)
  require lookupKey "value" oldParams = none
  ensures out = checkOutcome isValid code oldParams value
  ensures isValid = true → out = Except.ok ()
  ensures isValid = false → out = Except.error (buildReport code oldParams value)
  ensures isValid = false →
    lookupKey "value" (buildReport code oldParams value).params = some value
  ensures (buildReport code oldParams value).code = code
  ensures ∀ k v, k ≠ "value" → lookupKey k oldParams = some v →
    lookupKey k (buildReport code oldParams value).params = some v
  do
    -- impl-start

    let rej : Report := buildReport code oldParams value
    if !isValid then
      return Except.error rej
    else
      return Except.ok ()
    -- impl-end

prove_correct checkValue by
  loom_solve <;>
    simp_all [buildReport, lookupKey_append_fresh, lookupKey_append_pres]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the output via ensures_1 (out = checkOutcome isValid code oldParams value) plus discriminating clauses ensures_4 (isValid=false -> out = Except.error (buildReport code oldParams value)), ensures_5 (lookupKey "value" (buildReport...).params = some value), ensures_6 (code preserved), ensures_7 (frame preservation of pre-existing keys). All carriers (buildReport/checkOutcome/lookupKey) are transparent defs, not opaque oracles.

ENV: real project root. All attacks same_spec=True vs bundle Solution.lean (velvet backend).

### VERIFICATION RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in batches of 4):
- atk_1 prepatch bug (report = {code, oldParams}, no value append) -> exit 1 (metavariables 'checkValue_correct'; unsolved ensures_4/ensures_6). PREPATCH REPRODUCED (byte-identical to bundle Solution_prepatch.lean impl).
- atk_2 always accept (return Except.ok ()) -> exit 1 (unsolved ensures_4/ensures_5).
- atk_3 inverted validity (control-flow-effect: branches swapped) -> exit 1 (unsolved ensures_4, if isValid then error else ok).
- atk_4 empty code in report -> exit 1 (unsolved; code != []).
- atk_5 value under wrong key "val" -> exit 1 (unsolved ensures_5 lookupKey "value").
- atk_6 value bound to empty list (ungrounded/dropped content) -> exit 1 (unsolved value-binding).
- atk_7 drop oldParams, keep only [("value",value)] -> exit 1 (unsolved frame ensures_7).
- atk_8 order-echo: prepend [("value",value)]++oldParams instead of append -> exit 1 (unsolved ensures_4 exact-equality: ("value",value)::oldParams != oldParams++[("value",value)]).
- atk_9 partial-domain: append value only when oldParams nonempty (empty->[]) -> exit 1 (unsolved). NOTE first draft had a Lean syntax error (parse fail = weak evidence); rewritten with valid match syntax, re-checked same_spec=True, re-verified -> genuine semantic exit 1 (unsolved goals, not parse).
- POSITIVE CONTROL atk_pos (correct, structurally different: error hoisted into let rej, branch via `if !isValid`) -> exit 0, clean, no sorry/admit. Spec is non-vacuous.

No attack file contains sorry/admit/native_decide (scanned). All wrong-impl failures are genuine unsolved-goal / kernel-metavariable errors, NOT parse errors (verified atk_9 after syntax fix; all others parse cleanly and fail in prove_correct).

RESOLVE STEP: vacuous. Zero same-spec wrong impls VERIFIED, so there is no verifying-but-diverging candidate to materialize a faithful refined patch for; patches={} accordingly. verify=>correct is not falsified.

A-LEG / REFINEMENT AUDIT (focus per assignment): refinement.md declares NO A-consumed and NO A-reference rows (§C); every leg is R or I. Legitimate: (1) the one UNCHANGED callee (per-site validity test) is modeled as free Boolean isValid, quantified over ALL values in every postcondition (directive-7, strictly weaker than any concrete test) => owed no contract, G-AX skip by design, no axiom_check.py ships (django-16667 precedent). (2) The one CHANGED op (failure-branch report construction) is modeled DEEPLY via transparent defs buildReport/checkOutcome/lookupKey (no module-level axiom, no opaque oracle => no ungrounded-oracle echo possible; atk_6/atk_7/atk_8 confirm the postconditions are grounded in code/oldParams/value carriers and pin exact append equality). (3) No kind-3 (inexpressible-changed-op) leg. Model<->patch correspondence holds: append ("value",value) <-> patch.diff params={...,'value':value} across all 12 sites; `require lookupKey "value" oldParams = none` <-> no real site pre-binds 'value' (BaseValidator excluded, mapping.md §1.1). R/I legs are G-CONF's job (conformance_check.py present, seed 13212).

VERDICT: SOUND (≥5 distinct attacks run + prepatch + boundary/partial-domain/control-flow-effect/ungrounded-oracle-echo classes; none verifies; positive control verifies; A-legs sound). Spec is TIGHT; verify does NOT imply incorrect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True for velvet); Solution verifies (lean_verify.sh exit 0). The spec models checkValue with a FREE isValid:Bool (weakest possible model of the unchanged per-site validity test) and a deep buildReport model: on failure the report is {code, params := oldParams ++ [('value', value)]}. Differential-tested the modeled behavior against the REAL gold-patched repo at base_commit f4e93919 across all 9 representative mapped failure sites (RegexValidator, validate_email, validate_ipv4/ipv6_address, ProhibitNullCharacters, DecimalValidator invalid/max_digits/max_decimal_places, FileExtensionValidator) plus acceptance branches: on every failure the real ValidationError.params['value']==str(value), code preserved, and pre-existing bindings (max/extension/allowed_extensions) preserved — 0 mismatches; valid inputs raise nothing, matching Except.ok(). The require (oldParams lacks 'value') is honored by all 12 modeled sites; BaseValidator (which pre-binds 'value') is correctly excluded as not part of the fix, so require does not over-narrow the fix. Type abstraction str(value)<->List Char is faithful to the %(value)s placeholder rendering. No input found where the modeled function disagrees with the real callee; spec is not too strong and does not drift. (Note: conformance_check.py crashes on one fuzz input 'http://[::1:2::3]/' due to a Python-3.11 urlsplit incompatibility — a harness/env artifact, not a spec-vs-repo divergence.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen (leakage.screen) passes with zero hard failures on the velvet spec view: no diff markers, no reproduced gold-patch lines, no patched file/module paths, no spec-view identifier or comment echoing a patched repo symbol (changed symbols: validate, to_python, validate_ipv4_address, validate_ipv46_address — none appear), no narration terms. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical; only impl/prove_correct differ), so the prepatch pair does not leak either.

Substantive judgment: every discriminating element of the spec view is already public in the problem_statement, which explicitly says 'Make validators include the provided value in ValidationError' and 'one can override an error message and use a %(value)s placeholder.' The spec view's core content — a Report(code, params) with a lookupKey/%(name)s templating model, and buildReport appending ("value", value) to params on the failing branch while preserving code and pre-existing bindings — is exactly the behavior the statement discloses (the 'value' key, %(value)s templating, and 'include the provided value on the error branch').

The edit-localization details that WOULD leak (the twelve validators.py sites, the specific validators, and the DecimalField.validate removal in forms/fields.py) live only in mapping.md and refinement.md, which are NOT part of the spec view. Spec-view comments are abstract ('rejection report', 'failing branch', 'the input's validity test'); no site enumeration, no params={'value': value} literal, no file/symbol names. Describing intended behavior that is already public in the problem_statement is not leakage. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
