# P2 adversarial audit — django__django-14608

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,16 +59,17 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
     (raised : Option (List String)) : ErrorList := Id.run do
-  let mut nonForm := mkErrorList [] (some "nonform")
+  let mut nonForm := mkErrorList [] none
   if !isBound then
     return nonForm
   if !mgmtValid then
     nonForm := nonForm.append mgmtError
   if let some errs := raised then
-    nonForm := mkErrorList errs (some "nonform")
+    nonForm := mkErrorList errs none
   return nonForm
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,17 +59,11 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
-    (raised : Option (List String)) : ErrorList := Id.run do
-  let mut nonForm := mkErrorList [] (some "nonform")
-  if !isBound then
-    return nonForm
-  if !mgmtValid then
-    nonForm := nonForm.append mgmtError
-  if let some errs := raised then
-    nonForm := mkErrorList errs (some "nonform")
-  return nonForm
+    (raised : Option (List String)) : ErrorList :=
+  { messages := [], cssClass := "errorlist nonform" }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,14 +59,17 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
     (raised : Option (List String)) : ErrorList := Id.run do
-  let mut nonForm := mkErrorList [] (some "nonform")
+  -- partial-domain bug: only sets nonform on the management-error / raised paths;
+  -- the plain empty/valid path keeps the bare base class.
+  let mut nonForm := mkErrorList [] none
   if !isBound then
     return nonForm
   if !mgmtValid then
-    nonForm := nonForm.append mgmtError
+    nonForm := (mkErrorList [] (some "nonform")).append mgmtError
   if let some errs := raised then
     nonForm := mkErrorList errs (some "nonform")
   return nonForm
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,16 +59,19 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
     (raised : Option (List String)) : ErrorList := Id.run do
   let mut nonForm := mkErrorList [] (some "nonform")
   if !isBound then
     return nonForm
+  if let some errs := raised then
+    nonForm := mkErrorList errs (some "nonform")
+  -- control-flow-effect bug: append AFTER reconstruction, so a raised error does
+  -- NOT discard the management message (gold discards it).
   if !mgmtValid then
     nonForm := nonForm.append mgmtError
-  if let some errs := raised then
-    nonForm := mkErrorList errs (some "nonform")
   return nonForm
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,17 +59,13 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
-    (raised : Option (List String)) : ErrorList := Id.run do
-  let mut nonForm := mkErrorList [] (some "nonform")
-  if !isBound then
-    return nonForm
-  if !mgmtValid then
-    nonForm := nonForm.append mgmtError
-  if let some errs := raised then
-    nonForm := mkErrorList errs (some "nonform")
-  return nonForm
+    (raised : Option (List String)) : ErrorList :=
+  -- boundary bug: extra space in the CSS class string.
+  { messages := expectedMessages isBound mgmtValid mgmtError raised,
+    cssClass := "errorlist  nonform" }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,17 +59,14 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
-    (raised : Option (List String)) : ErrorList := Id.run do
-  let mut nonForm := mkErrorList [] (some "nonform")
-  if !isBound then
-    return nonForm
-  if !mgmtValid then
-    nonForm := nonForm.append mgmtError
-  if let some errs := raised then
-    nonForm := mkErrorList errs (some "nonform")
-  return nonForm
+    (raised : Option (List String)) : ErrorList :=
+  -- ungrounded-oracle echo: return the spec oracle's messages verbatim with the
+  -- pinned class. Extensionally equal to gold; closes by construction.
+  { messages := expectedMessages isBound mgmtValid mgmtError raised,
+    cssClass := "errorlist nonform" }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,12 +59,13 @@
   result.messages = expectedMessages isBound mgmtValid mgmtError raised
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
     (raised : Option (List String)) : ErrorList := Id.run do
+  -- partial-domain bug: does NOT early-return on unbound, so an unbound formset
+  -- with invalid mgmt bookkeeping wrongly carries the management message.
   let mut nonForm := mkErrorList [] (some "nonform")
-  if !isBound then
-    return nonForm
   if !mgmtValid then
     nonForm := nonForm.append mgmtError
   if let some errs := raised then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is axiomatized. The error-collection constructor used by
-- the modeled behavior (it records a CSS class string and an initial list of
-- messages) is modeled DEEPLY below (`mkErrorList`), so it is an A-reference
-- validated == the real callee by G-AX, not a consumed `_prop` axiom. There is
-- therefore no `opaque` declaration here.
-- axioms-end

-- pure-start
/-- An error collection that knows the CSS class it renders under and the list of
error messages it carries. -/
structure ErrorList where
  messages : List String
  cssClass : String
deriving DecidableEq, Repr

/-- Build an error collection from an initial list of messages and an optional
extra CSS class. With no extra class the collection renders under the base CSS
class `errorlist`; with an extra class `c` it renders under `errorlist c`
(the base class followed by a space and the extra class). -/
def mkErrorList (initlist : List String) (extraClass : Option String) : ErrorList :=
  { messages := initlist,
    cssClass := match extraClass with
                | none   => "errorlist"
                | some c => "errorlist " ++ c }

/-- Append one message to an error collection (the CSS class is unchanged). -/
def ErrorList.append (e : ErrorList) (msg : String) : ErrorList :=
  { e with messages := e.messages ++ [msg] }

/-- The messages the non-form error collection must carry, as a function of the
inputs that drive its production:
* if the data is unbound, processing stops immediately and the collection is empty;
* otherwise, if cross-collection validation reports errors, the collection holds
  exactly those reported messages;
* otherwise, if the management bookkeeping is invalid, the collection holds the
  single management error message;
* otherwise the collection is empty. -/
def expectedMessages (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : List String :=
  if !isBound then []
  else match raised with
       | some errs => errs
       | none => if !mgmtValid then [mgmtError] else []
-- pure-end

-- post-conditions-start
/-- The non-form error collection produced for a form-set always renders under
the CSS class `errorlist nonform`, and carries exactly the messages dictated by
the production path (`expectedMessages`). The non-form CSS class is present
regardless of which production path was taken (empty/unbound, management error,
or cross-collection validation error). -/
def problem_spec_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) (result : ErrorList) : Prop :=
  result.cssClass = "errorlist nonform" ∧
  result.messages = expectedMessages isBound mgmtValid mgmtError raised
-- post-conditions-end

-- impl-start
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList := Id.run do
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm
-- impl-end

-- proof-start
theorem correct_nonFormErrors :
    ∀ (isBound mgmtValid : Bool) (mgmtError : String) (raised : Option (List String)),
      problem_spec_nonFormErrors isBound mgmtValid mgmtError raised
        (implementation_nonFormErrors isBound mgmtValid mgmtError raised) := by
  intro isBound mgmtValid mgmtError raised
  unfold problem_spec_nonFormErrors implementation_nonFormErrors expectedMessages
  cases isBound <;> cases mgmtValid <;> cases raised <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14608 (lean). Spec is extensionally TIGHT: problem_spec_nonFormErrors pins BOTH observable fields by exact equality — result.cssClass = "errorlist nonform" AND result.messages = expectedMessages(...). Any closing correct_* is thus forced extensionally equal to gold on every input.

Same-spec: all 7 attacks + pc_gold verified same_spec==True (edited impl+proof only; axioms/pure/pre/post byte-identical).

Attacks (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (bare class 'errorlist' both sites): exit 1 (does NOT close; cssClass conjunct fails rfl). Prepatch bug reproduced.
- atk_2 dropped-messages ({[], 'errorlist nonform'}): exit 1 (messages conjunct fails).
- atk_3 partial-domain-css (nonform only on mgmt/raised paths, bare on empty/valid): exit 1 (cssClass fails on empty path).
- atk_4 control-flow-effect (append mgmt AFTER reconstruction, so raised does not discard mgmt msg): exit 1 (messages fail).
- atk_5 boundary ('errorlist  nonform' double-space): exit 1 (cssClass fails).
- atk_6 ungrounded-oracle echo ({expectedMessages(...), 'errorlist nonform'}, extensionally == gold): exit 0 CLOSES; #print axioms correct_nonFormErrors -> 'does not depend on any axioms' (clean, no sorryAx).
- atk_7 partial-domain-messages (no early-return on unbound -> spurious mgmt msg when unbound & invalid): exit 1 (messages fail).
- pc_gold positive control: exit 0, clean axioms.

MANDATORY resolve for the only closing wrong-impl (atk_6): its faithful Python realization is byte-identical to the gold patch because atk_6 is extensionally identical to gold on every input (same cssClass, same message list). Ran via swebench_unified.harness.run_resolve('django__django-14608', <atk_6 patch>, timeout=3600): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. This is exactly the RESOLVED echo-attack case (per 2026-08-06 policy) — a same-spec verifying candidate whose refined patch RESOLVES is NOT a weakness. No closing candidate has a non-resolving faithful patch, so verify does NOT ⇏ correct here.

refinement.md A-leg audit: legs are R (1), R/A-reference (2,5), I (3,4,6) — no kind-3 (changed-inexpressible). A-references (mkErrorList cssClass/messages) validated against the REAL callee: utils.py ErrorList.__init__ lines 122-128 confirm error_class is None -> 'errorlist' else 'errorlist {}'.format(c) — exactly the deep model; axiom_check.py (G-AX, seed 14608, 120008 inputs) corroborates 0 disagreements. I-legs confirmed against formsets.py full_clean: early return on not is_bound, single mgmt-error append, except ValidationError wholesale reassignment discarding the appended msg — matches expectedMessages precedence (raised=some errs yields errs regardless of mgmtValid). Axioms region is empty (no opaque, no consumed _prop). A-reference correspondence holds.

Verdict: SOUND. 6 distinct genuinely-wrong impls (prepatch, dropped-msg, partial-domain-css, boundary, control-flow-effect, partial-domain-msg) all fail to close; the single closing candidate is a gold-equivalent echo whose faithful patch RESOLVES.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is axiomatized. The error-collection constructor used by
-- the modeled behavior (it records a CSS class string and an initial list of
-- messages) is modeled DEEPLY below (`mkErrorList`), so it is an A-reference
-- validated == the real callee by G-AX, not a consumed `_prop` axiom. There is
-- therefore no `opaque` declaration here.
-- axioms-end

-- pure-start
/-- An error collection that knows the CSS class it renders under and the list of
error messages it carries. -/
structure ErrorList where
  messages : List String
  cssClass : String
deriving DecidableEq, Repr

/-- Build an error collection from an initial list of messages and an optional
extra CSS class. With no extra class the collection renders under the base CSS
class `errorlist`; with an extra class `c` it renders under `errorlist c`
(the base class followed by a space and the extra class). -/
def mkErrorList (initlist : List String) (extraClass : Option String) : ErrorList :=
  { messages := initlist,
    cssClass := match extraClass with
                | none   => "errorlist"
                | some c => "errorlist " ++ c }

/-- Append one message to an error collection (the CSS class is unchanged). -/
def ErrorList.append (e : ErrorList) (msg : String) : ErrorList :=
  { e with messages := e.messages ++ [msg] }

/-- The messages the non-form error collection must carry, as a function of the
inputs that drive its production:
* if the data is unbound, processing stops immediately and the collection is empty;
* otherwise, if cross-collection validation reports errors, the collection holds
  exactly those reported messages;
* otherwise, if the management bookkeeping is invalid, the collection holds the
  single management error message;
* otherwise the collection is empty. -/
def expectedMessages (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : List String :=
  if !isBound then []
  else match raised with
       | some errs => errs
       | none => if !mgmtValid then [mgmtError] else []
-- pure-end

-- post-conditions-start
/-- The non-form error collection produced for a form-set always renders under
the CSS class `errorlist nonform`, and carries exactly the messages dictated by
the production path (`expectedMessages`). The non-form CSS class is present
regardless of which production path was taken (empty/unbound, management error,
or cross-collection validation error). -/
def problem_spec_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) (result : ErrorList) : Prop :=
  result.cssClass = "errorlist nonform" ∧
  result.messages = expectedMessages isBound mgmtValid mgmtError raised
-- post-conditions-end

-- impl-start
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList := Id.run do
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm
-- impl-end

-- proof-start
theorem correct_nonFormErrors :
    ∀ (isBound mgmtValid : Bool) (mgmtError : String) (raised : Option (List String)),
      problem_spec_nonFormErrors isBound mgmtValid mgmtError raised
        (implementation_nonFormErrors isBound mgmtValid mgmtError raised) := by
  intro isBound mgmtValid mgmtError raised
  unfold problem_spec_nonFormErrors implementation_nonFormErrors expectedMessages
  cases isBound <;> cases mgmtValid <;> cases raised <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14608 (lean). Spec is extensionally TIGHT: problem_spec_nonFormErrors pins BOTH observable fields by exact equality — result.cssClass = "errorlist nonform" AND result.messages = expectedMessages(...). Any closing correct_* is thus forced extensionally equal to gold on every input.

Same-spec: all 7 attacks + pc_gold verified same_spec==True (edited impl+proof only; axioms/pure/pre/post byte-identical).

Attacks (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (bare class 'errorlist' both sites): exit 1 (does NOT close; cssClass conjunct fails rfl). Prepatch bug reproduced.
- atk_2 dropped-messages ({[], 'errorlist nonform'}): exit 1 (messages conjunct fails).
- atk_3 partial-domain-css (nonform only on mgmt/raised paths, bare on empty/valid): exit 1 (cssClass fails on empty path).
- atk_4 control-flow-effect (append mgmt AFTER reconstruction, so raised does not discard mgmt msg): exit 1 (messages fail).
- atk_5 boundary ('errorlist  nonform' double-space): exit 1 (cssClass fails).
- atk_6 ungrounded-oracle echo ({expectedMessages(...), 'errorlist nonform'}, extensionally == gold): exit 0 CLOSES; #print axioms correct_nonFormErrors -> 'does not depend on any axioms' (clean, no sorryAx).
- atk_7 partial-domain-messages (no early-return on unbound -> spurious mgmt msg when unbound & invalid): exit 1 (messages fail).
- pc_gold positive control: exit 0, clean axioms.

MANDATORY resolve for the only closing wrong-impl (atk_6): its faithful Python realization is byte-identical to the gold patch because atk_6 is extensionally identical to gold on every input (same cssClass, same message list). Ran via swebench_unified.harness.run_resolve('django__django-14608', <atk_6 patch>, timeout=3600): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. This is exactly the RESOLVED echo-attack case (per 2026-08-06 policy) — a same-spec verifying candidate whose refined patch RESOLVES is NOT a weakness. No closing candidate has a non-resolving faithful patch, so verify does NOT ⇏ correct here.

refinement.md A-leg audit: legs are R (1), R/A-reference (2,5), I (3,4,6) — no kind-3 (changed-inexpressible). A-references (mkErrorList cssClass/messages) validated against the REAL callee: utils.py ErrorList.__init__ lines 122-128 confirm error_class is None -> 'errorlist' else 'errorlist {}'.format(c) — exactly the deep model; axiom_check.py (G-AX, seed 14608, 120008 inputs) corroborates 0 disagreements. I-legs confirmed against formsets.py full_clean: early return on not is_bound, single mgmt-error append, except ValidationError wholesale reassignment discarding the appended msg — matches expectedMessages precedence (raised=some errs yields errs regardless of mgmtValid). Axioms region is empty (no opaque, no consumed _prop). A-reference correspondence holds.

Verdict: SOUND. 6 distinct genuinely-wrong impls (prepatch, dropped-msg, partial-domain-css, boundary, control-flow-effect, partial-domain-msg) all fail to close; the single closing candidate is a gold-equivalent echo whose faithful patch RESOLVES.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check for django__django-14608 lean bundle. Modeled function: production of BaseFormSet.full_clean's non-form error collection (self._non_form_errors), sites :336 (initial construction) and :383 (validation-error reconstruction), both gaining error_class='nonform' in the gold patch (patch confirmed from dataset; patch_equals_gold=True).

SPEC INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — axioms/pure/post-conditions regions byte-identical; spec not weakened to fit impl. Lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry). #print axioms correct_nonFormErrors => 'does not depend on any axioms' (no sorryAx; proof is real).

BEHAVIORAL FAITHFULNESS vs real repo (base 7f33c1e22d, @ 2c7846d992...): checked all production paths of full_clean POST-patch:
- initial: error_class(error_class='nonform') => empty, class 'errorlist nonform'. Spec: cssClass ALWAYS 'errorlist nonform'; !isBound => []. Match.
- if not is_bound: return => stays empty. Spec !isBound => []. Match.
- if not management_form.is_valid(): append(error) => [mgmtError]. Spec: none & !mgmtValid => [mgmtError]. Match.
- except ValidationError: self._non_form_errors = error_class(e.error_list, error_class='nonform') => wholesale replace with errs (discards appended mgmt msg), class 'errorlist nonform'. Spec: some errs => errs regardless of mgmtValid. Match (precedence == Python reassignment).
The error_class string semantics (None->'errorlist'; c->'errorlist {c}') is deeply modeled as mkErrorList and G-AX-validated (recorded pass: 120008 inputs, 0 disagreements, seed 14608). Confirmed only _non_form_errors mutation sites are the two constructions + one append (grep of full_clean body).

Unreachable input combos (e.g. !isBound with raised=some errs — unbound returns before the try) are modeled as [], consistent with real behavior; no reachable input where the modeled function disagrees with the real callee. Spec is a faithful, neither-too-strong-nor-too-weak input->output relation of the patched behavior. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard_failures). same_spec(Solution, Solution_prepatch)=True; no relaxed_leakage flag. Gold edit = pass error_class='nonform' at the two self.error_class(...) sites in BaseFormSet.full_clean so the non-form error collection's CSS class becomes 'errorlist nonform'. Public problem_statement already names the whole edit intent: 'Add nonform CSS class for non form errors in FormSets', 'ErrorList', and the base 'errorlist' documented class. The spec-view post-condition result.cssClass = "errorlist nonform" is exactly the observable outcome the task explicitly requests — both tokens ('nonform','errorlist') are public via problem_statement; their combination is the literal requested behavior, not extra edit-localization. No internal edit locators leak: full_clean, _non_form_errors, error_class, formsets.py, the two changed sites — none appear in spec-view identifiers or comments (verified against the projected view). The spec abstracts sites generically ('non-form error collection', 'form-set', 'management bookkeeping', 'cross-collection validation'). expectedMessages models unchanged message behavior (frame discipline), not the gold edit. Spec view reveals nothing about the gold edit beyond what problem_statement makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
