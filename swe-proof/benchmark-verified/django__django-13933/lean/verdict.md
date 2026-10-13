# P2 adversarial audit — django__django-13933

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
       return Except.error
         { messageTemplate := invalidMessage,
           code := invalidChoiceCode,
-          params := [(valueParamName, value)] }
+          params := [] }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,7 @@
   | none =>
       return Except.error
         { messageTemplate := invalidMessage,
-          code := invalidChoiceCode,
+          code := "bad_code",
           params := [(valueParamName, value)] }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
       return Except.error
         { messageTemplate := invalidMessage,
           code := invalidChoiceCode,
-          params := [(valueParamName, value)] }
+          params := [(valueParamName, value), ("extra", value)] }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
   if value ∈ emptyValues then
     return Except.ok none
   match lookup with
-  | some r => return Except.ok (some r)
+  | some _ => return Except.ok none
   | none =>
       return Except.error
         { messageTemplate := invalidMessage,
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,15 +101,16 @@
     (invalidMessage : String) (emptyValues : List Val)
     (value : Val) (lookup : Option Resolved) :
     Except ChoiceError (Option Resolved) := Id.run do
-  if value ∈ emptyValues then
-    return Except.ok none
   match lookup with
   | some r => return Except.ok (some r)
   | none =>
-      return Except.error
-        { messageTemplate := invalidMessage,
-          code := invalidChoiceCode,
-          params := [(valueParamName, value)] }
+      if value ∈ emptyValues then
+        return Except.ok none
+      else
+        return Except.error
+          { messageTemplate := invalidMessage,
+            code := invalidChoiceCode,
+            params := [(valueParamName, value)] }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
       return Except.error
         { messageTemplate := invalidMessage,
           code := invalidChoiceCode,
-          params := [(valueParamName, value)] }
+          params := [(valueParamName, invalidMessage)] }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -101,15 +101,16 @@
     (invalidMessage : String) (emptyValues : List Val)
     (value : Val) (lookup : Option Resolved) :
     Except ChoiceError (Option Resolved) := Id.run do
-  if value ∈ emptyValues then
+  if h : value ∉ emptyValues then
+    match lookup with
+    | some r => return Except.ok (some r)
+    | none =>
+        return Except.error
+          { messageTemplate := invalidMessage,
+            code := invalidChoiceCode,
+            params := [(valueParamName, value)] }
+  else
     return Except.ok none
-  match lookup with
-  | some r => return Except.ok (some r)
-  | none =>
-      return Except.error
-        { messageTemplate := invalidMessage,
-          code := invalidChoiceCode,
-          params := [(valueParamName, value)] }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the offending input when a single-choice field backed by a record set
rejects a submitted value.

A field whose permitted answers come from a stored collection coerces a raw
submitted value into one of those answers. The coercion has three outcomes:

  * the submission is one of the recognised "no answer" sentinels — the field
    yields an empty result and no error;
  * the submission resolves to exactly one stored answer — the field yields that
    answer;
  * the submission resolves to no stored answer — the field rejects it with a
    validation error.

The validation error carries a constant error code and a human-readable message
template configured for the rejection case. A template may refer to the rejected
value through a named placeholder. For that placeholder to render, the error must
ALSO carry the binding of that name to the actual submitted value. The desired
behavior is that a rejection always reports the offending value: the error's
parameter bindings map the value-placeholder name to exactly the submission that
was rejected, so a caller-supplied message naming that placeholder shows the
value the caller actually sent.

Inputs:
  * `invalidMessage` — the message template used for a rejected submission;
  * `emptyValues`    — the recognised "no answer" sentinels;
  * `value`          — the submitted value;
  * `lookup`         — the resolution of the submission against the stored
                       collection: `some r` when it resolves to the stored
                       answer `r`, `none` when it resolves to nothing (the
                       resolution attempt failed).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- of a submission against the stored collection is an UNCHANGED dependency whose
-- observable outcome (`some answer` / `none`) enters as the plain `lookup` datum;
-- the recognised "no answer" sentinels enter as the plain `emptyValues` datum.
-- The only modeled operation — assembling the rejection report so it carries the
-- offending value — is modeled directly over that data, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A submitted value. Modeled as a `String` (the raw textual submission); only
its identity is observed. -/
abbrev Val := String

/-- The identity of a stored answer the submission resolves to (e.g. its primary
key). Only its identity is observed. -/
abbrev Resolved := Nat

/-- A validation error report, restricted to the touched fields:
* `messageTemplate` — the human-readable message template for the rejection;
* `code` — the machine-readable rejection code;
* `params` — the named parameter bindings the template may interpolate. -/
structure ChoiceError where
  messageTemplate : String
  code : String
  params : List (String × Val)
deriving DecidableEq, Repr

/-- The constant rejection code for an unrecognised submission. -/
def invalidChoiceCode : String := "invalid_choice"

/-- The placeholder name a message template uses to refer to the offending
submission. -/
def valueParamName : String := "value"
-- pure-end

-- post-conditions-start
/-- The coercion outcome is fully pinned to the inputs:

  * a submission among the recognised sentinels yields the empty result with no
    error;
  * a submission that resolves to a stored answer yields exactly that answer;
  * a submission that resolves to nothing is rejected with a validation error
    carrying the configured template, the constant rejection code, AND a single
    parameter binding mapping the value-placeholder name to the offending
    submission itself.

The three cases cover every input, so no component of the result is left free. -/
def problem_spec_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved)
    (result : Except ChoiceError (Option Resolved)) : Prop :=
  (value ∈ emptyValues → result = Except.ok none) ∧
  (value ∉ emptyValues → ∀ r, lookup = some r → result = Except.ok (some r)) ∧
  (value ∉ emptyValues → lookup = none →
      result = Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [(valueParamName, value)] })
-- post-conditions-end

-- impl-start
def implementation_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved) :
    Except ChoiceError (Option Resolved) := Id.run do
  if value ∈ emptyValues then
    return Except.ok none
  match lookup with
  | some r => return Except.ok (some r)
  | none =>
      return Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [(valueParamName, value)] }
-- impl-end

-- proof-start
theorem correct_coerceChoice :
    ∀ (invalidMessage : String) (emptyValues : List Val)
      (value : Val) (lookup : Option Resolved),
      problem_spec_coerceChoice invalidMessage emptyValues value lookup
        (implementation_coerceChoice invalidMessage emptyValues value lookup) := by
  intro invalidMessage emptyValues value lookup
  unfold problem_spec_coerceChoice implementation_coerceChoice
  refine ⟨?_, ?_, ?_⟩
  · intro hv; simp only [hv, if_true, Id.run]; rfl
  · intro hv r hr; simp only [hv, if_false, Id.run, hr]; rfl
  · intro hv hr; simp only [hv, if_false, Id.run, hr]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_coerceChoice is a TOTAL, fully-determined conjunction over 3 mutually-exclusive exhaustive cases (value∈emptyValues → ok none; ∉ ∧ lookup=some r → ok (some r); ∉ ∧ lookup=none → error{msg, invalid_choice, [("value",value)]}). No input is uncovered and no output component is free, so any verifying impl is extensionally equal to gold on the whole modeled domain (Val:=String).

A-LEG AUDIT: refinement.md declares all-R, NO A rows. Confirmed honest: Solution.lean has ZERO axiom/opaque decls (axioms block is comment-only); meta.json axioms=[] and deep_model_references=[]. queryset.get / getattr / empty_values genuinely enter as DATA (lookup:Option Resolved, emptyValues:List Val), not as axiomatized callee contracts. No model↔patch A-correspondence to break. axiom_check.py is a legitimate skip stub. No kind-3 legs.

ATTACKS (7 built, all same_spec=True byte-identical spec region; verified concurrently ≤4 at a time via scripts/lean_verify.sh, project root):
- atk_1 partial/prepatch bug (rejection params:=[]): bash scripts/lean_verify.sh atk_1.lean → exit 1 (proof final rfl fails: pure(error{...params:=[]}) ≠ error{...params:=[(valueParamName,value)]}). Prepatch bug reproduced.
- atk_2 wrong code (code:="bad_code"): exit 1.
- atk_3 extra bogus param ([("value",value),("extra",value)]): exit 1.
- atk_4 wrong ok payload on resolve (some _ → ok none, drops r): exit 1.
- atk_5 control-flow-effect: check lookup BEFORE emptyValues (order swap; breaks clause 1 when value∈emptyValues ∧ lookup=some r): exit 1.
- atk_6 ungrounded-oracle echo: params carries invalidMessage instead of value: exit 1.
- atk_7 gold-equivalent echo (reordered: guard value∉emptyValues first via dite, else ok none; identical 3-way behavior): bash scripts/lean_verify.sh atk_7.lean → exit 0. #print axioms correct_coerceChoice → [propext] (clean, NO sorryAx).
Positive control (pos_control.lean = gold Solution.lean): exit 0; #print axioms → [propext, Quot.sound] (clean).

MANDATED RESOLVE: atk_7 is the ONLY wrong-impl slot whose proof closes with clean axioms. Materialized its faithful refined patch (atk_7_patch.diff, behaviorally the gold edit adding params={'value':value}) and RAN it through the official harness: run_resolve('django__django-13933', patch, timeout=3600) → completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying impl corresponds to a RESOLVING patch — verify⇒correct holds here.

No verifying same-spec impl corresponds to a non-resolving patch. All 6 genuinely-wrong impls fail to close; the 1 that closes resolves. Spec is TIGHT. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the offending input when a single-choice field backed by a record set
rejects a submitted value.

A field whose permitted answers come from a stored collection coerces a raw
submitted value into one of those answers. The coercion has three outcomes:

  * the submission is one of the recognised "no answer" sentinels — the field
    yields an empty result and no error;
  * the submission resolves to exactly one stored answer — the field yields that
    answer;
  * the submission resolves to no stored answer — the field rejects it with a
    validation error.

The validation error carries a constant error code and a human-readable message
template configured for the rejection case. A template may refer to the rejected
value through a named placeholder. For that placeholder to render, the error must
ALSO carry the binding of that name to the actual submitted value. The desired
behavior is that a rejection always reports the offending value: the error's
parameter bindings map the value-placeholder name to exactly the submission that
was rejected, so a caller-supplied message naming that placeholder shows the
value the caller actually sent.

Inputs:
  * `invalidMessage` — the message template used for a rejected submission;
  * `emptyValues`    — the recognised "no answer" sentinels;
  * `value`          — the submitted value;
  * `lookup`         — the resolution of the submission against the stored
                       collection: `some r` when it resolves to the stored
                       answer `r`, `none` when it resolves to nothing (the
                       resolution attempt failed).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- of a submission against the stored collection is an UNCHANGED dependency whose
-- observable outcome (`some answer` / `none`) enters as the plain `lookup` datum;
-- the recognised "no answer" sentinels enter as the plain `emptyValues` datum.
-- The only modeled operation — assembling the rejection report so it carries the
-- offending value — is modeled directly over that data, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A submitted value. Modeled as a `String` (the raw textual submission); only
its identity is observed. -/
abbrev Val := String

/-- The identity of a stored answer the submission resolves to (e.g. its primary
key). Only its identity is observed. -/
abbrev Resolved := Nat

/-- A validation error report, restricted to the touched fields:
* `messageTemplate` — the human-readable message template for the rejection;
* `code` — the machine-readable rejection code;
* `params` — the named parameter bindings the template may interpolate. -/
structure ChoiceError where
  messageTemplate : String
  code : String
  params : List (String × Val)
deriving DecidableEq, Repr

/-- The constant rejection code for an unrecognised submission. -/
def invalidChoiceCode : String := "invalid_choice"

/-- The placeholder name a message template uses to refer to the offending
submission. -/
def valueParamName : String := "value"
-- pure-end

-- post-conditions-start
/-- The coercion outcome is fully pinned to the inputs:

  * a submission among the recognised sentinels yields the empty result with no
    error;
  * a submission that resolves to a stored answer yields exactly that answer;
  * a submission that resolves to nothing is rejected with a validation error
    carrying the configured template, the constant rejection code, AND a single
    parameter binding mapping the value-placeholder name to the offending
    submission itself.

The three cases cover every input, so no component of the result is left free. -/
def problem_spec_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved)
    (result : Except ChoiceError (Option Resolved)) : Prop :=
  (value ∈ emptyValues → result = Except.ok none) ∧
  (value ∉ emptyValues → ∀ r, lookup = some r → result = Except.ok (some r)) ∧
  (value ∉ emptyValues → lookup = none →
      result = Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [(valueParamName, value)] })
-- post-conditions-end

-- impl-start
def implementation_coerceChoice
    (invalidMessage : String) (emptyValues : List Val)
    (value : Val) (lookup : Option Resolved) :
    Except ChoiceError (Option Resolved) := Id.run do
  if value ∈ emptyValues then
    return Except.ok none
  match lookup with
  | some r => return Except.ok (some r)
  | none =>
      return Except.error
        { messageTemplate := invalidMessage,
          code := invalidChoiceCode,
          params := [(valueParamName, value)] }
-- impl-end

-- proof-start
theorem correct_coerceChoice :
    ∀ (invalidMessage : String) (emptyValues : List Val)
      (value : Val) (lookup : Option Resolved),
      problem_spec_coerceChoice invalidMessage emptyValues value lookup
        (implementation_coerceChoice invalidMessage emptyValues value lookup) := by
  intro invalidMessage emptyValues value lookup
  unfold problem_spec_coerceChoice implementation_coerceChoice
  refine ⟨?_, ?_, ?_⟩
  · intro hv; simp only [hv, if_true, Id.run]; rfl
  · intro hv r hr; simp only [hv, if_false, Id.run, hr]; rfl
  · intro hv hr; simp only [hv, if_false, Id.run, hr]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_coerceChoice is a TOTAL, fully-determined conjunction over 3 mutually-exclusive exhaustive cases (value∈emptyValues → ok none; ∉ ∧ lookup=some r → ok (some r); ∉ ∧ lookup=none → error{msg, invalid_choice, [("value",value)]}). No input is uncovered and no output component is free, so any verifying impl is extensionally equal to gold on the whole modeled domain (Val:=String).

A-LEG AUDIT: refinement.md declares all-R, NO A rows. Confirmed honest: Solution.lean has ZERO axiom/opaque decls (axioms block is comment-only); meta.json axioms=[] and deep_model_references=[]. queryset.get / getattr / empty_values genuinely enter as DATA (lookup:Option Resolved, emptyValues:List Val), not as axiomatized callee contracts. No model↔patch A-correspondence to break. axiom_check.py is a legitimate skip stub. No kind-3 legs.

ATTACKS (7 built, all same_spec=True byte-identical spec region; verified concurrently ≤4 at a time via scripts/lean_verify.sh, project root):
- atk_1 partial/prepatch bug (rejection params:=[]): bash scripts/lean_verify.sh atk_1.lean → exit 1 (proof final rfl fails: pure(error{...params:=[]}) ≠ error{...params:=[(valueParamName,value)]}). Prepatch bug reproduced.
- atk_2 wrong code (code:="bad_code"): exit 1.
- atk_3 extra bogus param ([("value",value),("extra",value)]): exit 1.
- atk_4 wrong ok payload on resolve (some _ → ok none, drops r): exit 1.
- atk_5 control-flow-effect: check lookup BEFORE emptyValues (order swap; breaks clause 1 when value∈emptyValues ∧ lookup=some r): exit 1.
- atk_6 ungrounded-oracle echo: params carries invalidMessage instead of value: exit 1.
- atk_7 gold-equivalent echo (reordered: guard value∉emptyValues first via dite, else ok none; identical 3-way behavior): bash scripts/lean_verify.sh atk_7.lean → exit 0. #print axioms correct_coerceChoice → [propext] (clean, NO sorryAx).
Positive control (pos_control.lean = gold Solution.lean): exit 0; #print axioms → [propext, Quot.sound] (clean).

MANDATED RESOLVE: atk_7 is the ONLY wrong-impl slot whose proof closes with clean axioms. Materialized its faithful refined patch (atk_7_patch.diff, behaviorally the gold edit adding params={'value':value}) and RAN it through the official harness: run_resolve('django__django-13933', patch, timeout=3600) → completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying impl corresponds to a RESOLVING patch — verify⇒correct holds here.

No verifying same-spec impl corresponds to a non-resolving patch. All 6 genuinely-wrong impls fail to close; the 1 that closes resolves. Spec is TIGHT. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigor checks: (1) Solution.lean compiles under lean_verify.sh (exit 0); #print axioms correct_coerceChoice = [propext, Quot.sound] only — no sorryAx, proof is genuine. (2) same_spec(Solution.lean, Solution_prepatch.lean, lean_lang)=True; they differ only in the impl region (params:=[(valueParamName,value)] vs params:=[]), a real G-DIFF bug twin. Real callee = ModelChoiceField.to_python, django/forms/models.py:1301-1314 @ base 42e8cf47c7.

Faithfulness of problem_spec_coerceChoice vs real to_python over the modeled domain (invalidMessage:String, emptyValues:List String, value:String, lookup:Option Nat):
- Clause 1 (value∈emptyValues → ok none) ↔ 'if value in self.empty_values: return None'. Match.
- Clause 2 (value∉emptyValues, lookup=some r → ok (some r)) ↔ successful queryset.get then 'return value'. Match.
- Clause 3 (value∉emptyValues, lookup=none → error{invalidMessage, "invalid_choice", [("value",value)]}) ↔ 'except (...): raise ValidationError(self.error_messages[\'invalid_choice\'], code=\'invalid_choice\', params={\'value\': value})'. Match: template, literal code, and singleton dict {'value': value}↔[("value",value)] (membership-keyed dict↔assoc-list bijection is exact for a singleton).

Strongest divergence candidate examined and refuted: real code has 'if isinstance(value, self.queryset.model): value = getattr(value, key)' BEFORE the get(); if a model-instance submission then fails lookup, params reports the extracted pk, not the original submission — which WOULD contradict the spec's 'reports the submission verbatim.' But value is modeled as Val:=String, and a Python str is never an instance of queryset.model, so that branch is dead for every modeled input; value is never reassigned and the original string is reported, matching the spec. This is a legitimate domain restriction (textual submissions), which can only make the spec NARROWER, never too strong. No input in the modeled domain makes the modeled function disagree with the real callee. Spec is not too strong and does not drift.

Note on strength: the spec fully pins the result on all three branches (total case split value∈/∉emptyValues × lookup some/none), so it is exactly as strong as the patched behavior — the added params binding on the rejection branch is the discriminating clause the prepatch twin cannot satisfy (params:=[] ≠ [("value",value)]), which is correct and matches FAIL_TO_PASS test_modelchoicefield_value_placeholder. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical with prepatch via swebench_unified.markers.same_spec (True) on the lean backend. Gold edit: adds params={'value': value} to the ValidationError raised in the invalid_choice branch of ModelChoiceField.to_python, so the offending value is reported. This fix is ALREADY fully disclosed by the public problem_statement, which states 'Passing in parameters with the invalid value and modifying the default error message for the code invalid_choice should fix this' and quotes invalid_choice and %(value)s from source. The spec view: (1) uses a neutral modeled identifier `coerceChoice` sharing no patched symbol name (patch touches only to_python); (2) describes behavior only ('a rejection always reports the offending value', 'parameter bindings map the value-placeholder name to the submission') and never narrates the diff or the pre-patch bug; (3) the literal constants invalidChoiceCode="invalid_choice" and valueParamName="value" are behavioral constants exhibited by the problem_statement itself (invalid_choice, %(value)s). No file:line, no Python/django symbols, no queryset/getattr, no verbatim params={'value': value}, no reference to the removed pre-patch line appear in the spec view. Every post-condition constraint is at or below the disclosure level of the public problem_statement; nothing leaks the gold edit beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
