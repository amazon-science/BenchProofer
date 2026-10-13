# P2 adversarial audit — django__django-11790

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,8 @@
   let umax := usernameMaxLength configuredMax
   let mut field : UField := { maxLength := 0, attrs := initAttrs }
   field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +67,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,9 @@
     (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
   let umax := usernameMaxLength configuredMax
   let mut field : UField := { maxLength := 0, attrs := initAttrs }
-  field := { field with maxLength := umax }
   field := { field with attrs := setAttr field.attrs "maxlength" umax }
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +67,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,9 @@
   let umax := usernameMaxLength configuredMax
   let mut field : UField := { maxLength := 0, attrs := initAttrs }
   field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
+  field := { field with attrs := setAttr field.attrs "maxlength" 254 }
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +68,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,9 @@
   let umax := usernameMaxLength configuredMax
   let mut field : UField := { maxLength := 0, attrs := initAttrs }
   field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
+  field := { field with attrs := setAttr field.attrs "maxLength" umax }
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +68,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,10 @@
     (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
   let umax := usernameMaxLength configuredMax
   let mut field : UField := { maxLength := 0, attrs := initAttrs }
+  field := { field with attrs := setAttr field.attrs "maxlength" field.maxLength }
   field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +68,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,12 @@
 def implementation_authUsernameField
     (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
   let umax := usernameMaxLength configuredMax
-  let mut field : UField := { maxLength := 0, attrs := initAttrs }
-  field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
+  let mut field : UField := { maxLength := umax, attrs := initAttrs }
+  match initAttrs with
+  | [] => field := { field with attrs := setAttr field.attrs "maxlength" umax }
+  | _  => pure ()
   return field
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +69,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,14 +53,10 @@
 
 -- impl-start
 def implementation_authUsernameField
-    (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
-  let umax := usernameMaxLength configuredMax
-  let mut field : UField := { maxLength := 0, attrs := initAttrs }
-  field := { field with maxLength := umax }
-  field := { field with attrs := setAttr field.attrs "maxlength" umax }
-  return field
+    (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField :=
+  { maxLength := usernameMaxLength configuredMax,
+    attrs := setAttr initAttrs "maxlength" (usernameMaxLength configuredMax) }
 -- impl-end
-
 -- proof-start
 theorem correct_authUsernameField :
     ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
@@ -69,5 +65,5 @@
   intro configuredMax initAttrs
   unfold problem_spec_authUsernameField implementation_authUsernameField
   simp only [Id.run]
-  exact ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only computed value is
-- a total integer-valued selection over an optional configured bound (modeled
-- deeply as `usernameMaxLength`, below); the attribute store is modeled concretely
-- as an association list. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A rendered text-input field carrying its effective maximum length and the
integer-valued HTML attributes of its widget (an association list keyed by
attribute name). Only the touched components are modeled. -/
structure UField where
  maxLength : Nat
  attrs : List (String × Nat)
  deriving Repr, DecidableEq

/-- The effective maximum length: the configured bound when it is present and
positive, otherwise the standard fallback of 254. A configured bound that is
absent or zero is treated as unset. -/
def usernameMaxLength : Option Nat → Nat
  | none        => 254
  | some 0      => 254
  | some (n+1)  => n + 1

/-- Look up an integer-valued attribute by name (the first binding wins). -/
def attrLookup (attrs : List (String × Nat)) (k : String) : Option Nat :=
  (attrs.find? (fun p => p.1 = k)).map (·.2)

/-- Set an integer-valued attribute, overwriting any existing binding for the
same name and otherwise inserting it. -/
def setAttr (attrs : List (String × Nat)) (k : String) (v : Nat) : List (String × Nat) :=
  attrs.filter (fun p => p.1 ≠ k) ++ [(k, v)]
-- pure-end

-- post-conditions-start
/-- Configuring the username field from an optional configured length bound and
the field's initial widget attributes yields a field whose effective maximum
length equals the resolved bound, and whose widget attributes are exactly the
input attributes with the `maxlength` attribute set to that same resolved bound
(overwriting any prior `maxlength` and preserving every other attribute). Pinning
the attribute map to this concrete update — rather than only its `maxlength`
lookup — frames the whole result against the input, so no implementation that
fails to perform the update can satisfy the spec. -/
def problem_spec_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat))
    (result : UField) : Prop :=
  result.maxLength = usernameMaxLength configuredMax ∧
  result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)
-- post-conditions-end

-- impl-start
def implementation_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
  let umax := usernameMaxLength configuredMax
  let mut field : UField := { maxLength := 0, attrs := initAttrs }
  field := { field with maxLength := umax }
  field := { field with attrs := setAttr field.attrs "maxlength" umax }
  return field
-- impl-end
-- proof-start
theorem correct_authUsernameField :
    ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
      problem_spec_authUsernameField configuredMax initAttrs
        (implementation_authUsernameField configuredMax initAttrs) := by
  intro configuredMax initAttrs
  unfold problem_spec_authUsernameField implementation_authUsernameField
  simp only [Id.run]
  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11790 (lean). VERDICT: SOUND.

SPEC SHAPE: fully functional. UField has exactly 2 fields (maxLength:Nat, attrs:List(String×Nat)); problem_spec pins BOTH to closed forms of the inputs (result.maxLength = usernameMaxLength configuredMax AND result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)). Any verifying impl must therefore compute the exact gold output on every input — no closing-but-non-resolving alternative can exist unless it produces gold output, in which case its faithful patch is gold and resolves.

A-LEG AUDIT: meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[]. refinement.md is entirely R/I (rows 1=R, 2-5=I); NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. The A-leg/callee-correspondence requirement is vacuously satisfied — there are no axioms or deep-model references to validate. axiom_check.py is a legitimate skip stub (empty axioms region). Correspondence of the R/I legs to the real gold patch is exact (row 1: max_length or 254 -> usernameMaxLength truthiness split; row 4 discriminating op: widget.attrs['maxlength']=v -> setAttr overwrite/insert).

Same_spec (swebench_unified.markers.same_spec, lean backend) = True for all 8 files (7 attacks + positive control); only impl region edited, frozen prefix (lines 1-53) byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos.lean (correct impl, Id.run mutation form): exit 0. #print axioms correct_authUsernameField -> 'does not depend on any axioms'. CLEAN.
- atk_1.lean (PREPATCH BUG re-encoded: attrs left = initAttrs, maxlength update omitted): exit 1 (unsolved goals @ correct_ thm). Cannot close 2nd conjunct.
- atk_2.lean (maxLength never overwritten, stays 0): exit 1 (unsolved goals).
- atk_3.lean (boundary: attr value hard-coded 254, ignores configuredMax): exit 1.
- atk_4.lean (wrong key "maxLength" instead of "maxlength"): exit 1.
- atk_5.lean (control-flow-effect: setAttr uses field.maxLength while still 0, ordering bug): exit 1.
- atk_6.lean (partial-domain: only updates attrs when initAttrs=[], else prepatch bug): exit 1.
- atk_7.lean (ungrounded-oracle/echo: computes the EXACT gold output via a plain record literal instead of Id.run): exit 0. #print axioms -> depends on [propext] only (standard, NOT sorryAx). Clean, genuine proof.

Per protocol, the only verifying same-spec attack (atk_7, the gold-equivalent echo) had its faithful refined patch materialized. Since atk_7 computes exactly the gold output, its faithful patch is the gold patch. RESOLVE RUN (run_resolve via docker, run_id sbu-audit-atk7-11790): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So verify⇒resolve holds for the echo; it does NOT break the spec (matches the RESOLVED echo-attack policy: a same-spec verifying attack whose refined patch resolves is NOT a weakness).

CONCLUSION: 6 distinct genuinely-wrong impls (prepatch bug, const-254 boundary, wrong-key, always-0, effect-ordering, partial-domain) all FAIL to verify (proof cannot close — the spec's full functional determinism excludes them). The 7th (gold-equivalent echo) verifies with clean axioms and its faithful patch RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch => verify⇏correct is NOT demonstrated => spec is SOUND for G-EQ. Positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only computed value is
-- a total integer-valued selection over an optional configured bound (modeled
-- deeply as `usernameMaxLength`, below); the attribute store is modeled concretely
-- as an association list. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A rendered text-input field carrying its effective maximum length and the
integer-valued HTML attributes of its widget (an association list keyed by
attribute name). Only the touched components are modeled. -/
structure UField where
  maxLength : Nat
  attrs : List (String × Nat)
  deriving Repr, DecidableEq

/-- The effective maximum length: the configured bound when it is present and
positive, otherwise the standard fallback of 254. A configured bound that is
absent or zero is treated as unset. -/
def usernameMaxLength : Option Nat → Nat
  | none        => 254
  | some 0      => 254
  | some (n+1)  => n + 1

/-- Look up an integer-valued attribute by name (the first binding wins). -/
def attrLookup (attrs : List (String × Nat)) (k : String) : Option Nat :=
  (attrs.find? (fun p => p.1 = k)).map (·.2)

/-- Set an integer-valued attribute, overwriting any existing binding for the
same name and otherwise inserting it. -/
def setAttr (attrs : List (String × Nat)) (k : String) (v : Nat) : List (String × Nat) :=
  attrs.filter (fun p => p.1 ≠ k) ++ [(k, v)]
-- pure-end

-- post-conditions-start
/-- Configuring the username field from an optional configured length bound and
the field's initial widget attributes yields a field whose effective maximum
length equals the resolved bound, and whose widget attributes are exactly the
input attributes with the `maxlength` attribute set to that same resolved bound
(overwriting any prior `maxlength` and preserving every other attribute). Pinning
the attribute map to this concrete update — rather than only its `maxlength`
lookup — frames the whole result against the input, so no implementation that
fails to perform the update can satisfy the spec. -/
def problem_spec_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat))
    (result : UField) : Prop :=
  result.maxLength = usernameMaxLength configuredMax ∧
  result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)
-- post-conditions-end

-- impl-start
def implementation_authUsernameField
    (configuredMax : Option Nat) (initAttrs : List (String × Nat)) : UField := Id.run do
  let umax := usernameMaxLength configuredMax
  let mut field : UField := { maxLength := 0, attrs := initAttrs }
  field := { field with maxLength := umax }
  field := { field with attrs := setAttr field.attrs "maxlength" umax }
  return field
-- impl-end
-- proof-start
theorem correct_authUsernameField :
    ∀ (configuredMax : Option Nat) (initAttrs : List (String × Nat)),
      problem_spec_authUsernameField configuredMax initAttrs
        (implementation_authUsernameField configuredMax initAttrs) := by
  intro configuredMax initAttrs
  unfold problem_spec_authUsernameField implementation_authUsernameField
  simp only [Id.run]
  refine ⟨?_, ?_⟩ <;> first | rfl | (cases configuredMax <;> simp_all [usernameMaxLength, setAttr, attrLookup]) | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11790 (lean). VERDICT: SOUND.

SPEC SHAPE: fully functional. UField has exactly 2 fields (maxLength:Nat, attrs:List(String×Nat)); problem_spec pins BOTH to closed forms of the inputs (result.maxLength = usernameMaxLength configuredMax AND result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)). Any verifying impl must therefore compute the exact gold output on every input — no closing-but-non-resolving alternative can exist unless it produces gold output, in which case its faithful patch is gold and resolves.

A-LEG AUDIT: meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[]. refinement.md is entirely R/I (rows 1=R, 2-5=I); NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. The A-leg/callee-correspondence requirement is vacuously satisfied — there are no axioms or deep-model references to validate. axiom_check.py is a legitimate skip stub (empty axioms region). Correspondence of the R/I legs to the real gold patch is exact (row 1: max_length or 254 -> usernameMaxLength truthiness split; row 4 discriminating op: widget.attrs['maxlength']=v -> setAttr overwrite/insert).

Same_spec (swebench_unified.markers.same_spec, lean backend) = True for all 8 files (7 attacks + positive control); only impl region edited, frozen prefix (lines 1-53) byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos.lean (correct impl, Id.run mutation form): exit 0. #print axioms correct_authUsernameField -> 'does not depend on any axioms'. CLEAN.
- atk_1.lean (PREPATCH BUG re-encoded: attrs left = initAttrs, maxlength update omitted): exit 1 (unsolved goals @ correct_ thm). Cannot close 2nd conjunct.
- atk_2.lean (maxLength never overwritten, stays 0): exit 1 (unsolved goals).
- atk_3.lean (boundary: attr value hard-coded 254, ignores configuredMax): exit 1.
- atk_4.lean (wrong key "maxLength" instead of "maxlength"): exit 1.
- atk_5.lean (control-flow-effect: setAttr uses field.maxLength while still 0, ordering bug): exit 1.
- atk_6.lean (partial-domain: only updates attrs when initAttrs=[], else prepatch bug): exit 1.
- atk_7.lean (ungrounded-oracle/echo: computes the EXACT gold output via a plain record literal instead of Id.run): exit 0. #print axioms -> depends on [propext] only (standard, NOT sorryAx). Clean, genuine proof.

Per protocol, the only verifying same-spec attack (atk_7, the gold-equivalent echo) had its faithful refined patch materialized. Since atk_7 computes exactly the gold output, its faithful patch is the gold patch. RESOLVE RUN (run_resolve via docker, run_id sbu-audit-atk7-11790): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So verify⇒resolve holds for the echo; it does NOT break the spec (matches the RESOLVED echo-attack policy: a same-spec verifying attack whose refined patch resolves is NOT a weakness).

CONCLUSION: 6 distinct genuinely-wrong impls (prepatch bug, const-254 boundary, wrong-key, always-0, effect-ordering, partial-domain) all FAIL to verify (proof cannot close — the spec's full functional determinism excludes them). The 7th (gold-equivalent echo) verifies with clean axioms and its faithful patch RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch => verify⇏correct is NOT demonstrated => spec is SOUND for G-EQ. Positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-11790 lean bundle. Modeled callee: the post-patch username-field configuration block in AuthenticationForm.__init__ (django/contrib/auth/forms.py:191-196 @ b1d6b35), whose gold patch hoists `username_max_length = self.username_field.max_length or 254` and sets BOTH `self.fields['username'].max_length = username_max_length` AND `self.fields['username'].widget.attrs['maxlength'] = username_max_length`.

Mechanical checks: Solution.lean compiles (lean_verify exit 0, no sorry); `#print axioms correct_authUsernameField` -> 'does not depend on any axioms' (genuine, no sorryAx). same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True (frozen imports/axioms/pure/post-conditions byte-identical; prepatch differs only in impl/proof, the intended G-DIFF signal).

Faithfulness argument (searched for a diverging input, found none):
1. `usernameMaxLength : Option Nat -> Nat` (none->254, some 0->254, some (n+1)->n+1) is an exact match for Python `max_length or 254`: None and 0 are the only falsy values -> 254, any positive int -> itself. Django's Field.max_length is a non-negative int or None, so `Option Nat` covers the entire real domain with no gap (no negatives possible). Verified over boundaries {None,0,1,254,255,large}.
2. `result.maxLength = usernameMaxLength configuredMax` <-> `field.max_length = username_max_length`. Matches.
3. `result.attrs = setAttr initAttrs "maxlength" umax` <-> `widget.attrs['maxlength'] = umax`. setAttr = filter-out-key ++ [(k,v)] (overwrite/insert). The ONLY representational difference vs a Python dict in-place update is LIST ORDER (setAttr appends maxlength to the tail; dict keeps position on overwrite). This is unobservable: Python dict equality is order-insensitive and the sole observable used anywhere (F2P tests + attrLookup) is `.get('maxlength')`, which is order-independent. So no input produces an observable disagreement. In every F2P path the integer attr map has no preexisting 'maxlength' (UsernameField declared without max_length; CharField.widget_attrs only seeds maxlength when max_length is not None at construction), so even the tail-vs-position nuance never surfaces.
4. Projection soundness: real widget.attrs also holds non-integer attrs (autofocus:bool, autocomplete/autocapitalize:str). These are untouched by the patch and excluded from the `List (String x Nat)` integer projection; both the real dict assignment and setAttr preserve all non-maxlength keys, so the projection is observationally faithful for the assertion widget.attrs.get('maxlength') == expected (254 default / 255 custom).

G-CONF (conformance_check.py) independently fuzzes the R/I shadow vs a reconstruction of the patched block over 120010 inputs incl. maps already carrying maxlength; recorded 0 disagreements (seed=11790). Consistent with the above.

Conclusion: the modeled function agrees with the real callee on every input over the modeled projection; the spec is neither too strong nor too weak. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage audit of the same_spec spec view for django__django-11790 (lean).

Mechanical checks: Solution.lean compiles (lean_verify exit 0); `#print axioms correct_authUsernameField` => 'does not depend on any axioms' (genuine proof, no sorryAx); same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True (spec regions byte-identical, differing only in the elided impl/proof regions).

Gold edit (from frozen dataset patch): adds exactly `username_max_length = self.username_field.max_length or 254` hoist + `self.fields['username'].widget.attrs['maxlength'] = username_max_length`. The discriminating fix is setting the widget 'maxlength' HTML attribute (the `max_length or 254` computation already existed prepatch and is UNCHANGED).

Public problem_statement already discloses the entire fix in plain English: 'AuthenticationForm's username field doesn't set maxlength HTML attribute ... doesn't render with maxlength HTML attribute anymore.' The 'maxlength' HTML-attribute behavior IS the publicly stated bug.

Spec-view line-by-line:
- post-condition `result.attrs = setAttr initAttrs "maxlength" (usernameMaxLength configuredMax)` formalizes 'set the maxlength widget attribute to the effective max length' — the exact behavior named in problem_statement; the string literal "maxlength" is verbatim from problem_statement, not beyond it.
- `usernameMaxLength` (none->254 / some 0->254 / some n->n) models `max_length or 254`, which is UNCHANGED prepatch control flow, NOT the gold edit — pinning it leaks nothing about the fix.
- pure-region structure/`setAttr`/`attrLookup` and all docstrings stay at problem-statement altitude ('set the maxlength attribute'); no gold-patch-specific code or phrasing is quoted.

No spec-view line reveals the gold edit beyond what the public problem_statement already states. refinement.md/mapping.md are audit artifacts outside the same_spec view and excluded from this judgment. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
