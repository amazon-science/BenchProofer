# P2 adversarial audit — django__django-12406

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies. Only atk_6 (behavioral echo, match-rewrite of gold) verifies with clean axioms [propext, Classical.choice, Quot.sound]; its faithful patch (= gold) RESOLVES=True (all FAIL_TO_PASS pass: test_choices_radio_blank, test_non_blank_foreign_key_with_radio, test_clean_model_instance). Concrete divergence of the wrong impls from the spec: emptyOption at (required=F, initialPresent=F, radioWidget=T, blankAllowed=F): spec=none, atk_1/atk_4 yield some. atk_3 at (T,T,F,F): spec=none, impl=some. formKwargs atk_5 at blankAllowed=true: spec wants some(flag true), impl gives some(flag false); atk_2 omits the blank key entirely.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,8 +52,9 @@
 def implementation_emptyOption (required : Bool) (initialPresent : Bool)
     (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
     Option String := Id.run do
+  -- ATTACK (partial-domain): radio branch dropped (pre-patch bug)
   let mut chosen : Option String := some defaultLabel
-  if (required && initialPresent) || (radioWidget && !blankAllowed) then
+  if required && initialPresent then
     chosen := none
   else
     chosen := some defaultLabel
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,8 +84,8 @@
 -- impl-start
 def implementation_formKwargs (base : Std.HashMap String KwargVal)
     (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
+  -- ATTACK (partial-domain): 'blank' never forwarded (pre-patch bug)
   let mut d := base
-  d := d.insert "blank" (KwargVal.flag blankAllowed)
   return d
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,8 +52,9 @@
 def implementation_emptyOption (required : Bool) (initialPresent : Bool)
     (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
     Option String := Id.run do
+  -- ATTACK (control-flow-effect): AND instead of OR joining the two branches
   let mut chosen : Option String := some defaultLabel
-  if (required && initialPresent) || (radioWidget && !blankAllowed) then
+  if (required && initialPresent) && (radioWidget && !blankAllowed) then
     chosen := none
   else
     chosen := some defaultLabel
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,8 +52,9 @@
 def implementation_emptyOption (required : Bool) (initialPresent : Bool)
     (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
     Option String := Id.run do
+  -- ATTACK (boundary): forgot the negation on blank (radioWidget && blankAllowed)
   let mut chosen : Option String := some defaultLabel
-  if (required && initialPresent) || (radioWidget && !blankAllowed) then
+  if (required && initialPresent) || (radioWidget && blankAllowed) then
     chosen := none
   else
     chosen := some defaultLabel
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,8 +84,9 @@
 -- impl-start
 def implementation_formKwargs (base : Std.HashMap String KwargVal)
     (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
+  -- ATTACK (boundary/negation): forwards the WRONG flag value under 'blank'
   let mut d := base
-  d := d.insert "blank" (KwargVal.flag blankAllowed)
+  d := d.insert "blank" (KwargVal.flag (!blankAllowed))
   return d
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,11 +52,12 @@
 def implementation_emptyOption (required : Bool) (initialPresent : Bool)
     (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
     Option String := Id.run do
+  -- ATTACK (ungrounded-oracle echo): gold-equivalent but rewritten via match,
+  -- to exercise the resolve step for a same-spec VERIFYING impl.
   let mut chosen : Option String := some defaultLabel
-  if (required && initialPresent) || (radioWidget && !blankAllowed) then
-    chosen := none
-  else
-    chosen := some defaultLabel
+  match ((required && initialPresent) || (radioWidget && !blankAllowed)) with
+  | true  => chosen := none
+  | false => chosen := some defaultLabel
   return chosen
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related behaviors for a model-backed choice field whose options are drawn
from a queryset.

* The leading empty option ("---------") that a choice field offers must be
  suppressed (set to none) not only when the field is required with an initial
  value, but ALSO when the field is rendered with a radio-style widget and the
  underlying model attribute forbids an empty value. Otherwise the empty
  option is presented with its default label.

* When a relational model attribute builds the keyword arguments for its
  generated form field, it forwards whether the attribute allows an empty value
  under the dedicated `blank` key, leaving every other keyword argument
  untouched.

These are stated abstractly as input→output relations; the implementation and
correctness proof for each are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a Boolean decision; a single map update).
-- axioms-end

-- pure-start
/-- Abstraction of the heterogeneous values stored under a form field's keyword
arguments. Only the Boolean-flag value matters for the modeled behavior; other
values (a class, a queryset, an optional name) are kept opaque. -/
inductive KwargVal where
  | obj : KwargVal
  | name : Option String → KwargVal
  | flag : Bool → KwargVal
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The leading empty option is suppressed (`none`) exactly when the field is
required with a present initial value, OR the widget is radio-style and the
model attribute forbids an empty value; otherwise it carries the default
label. -/
def problem_spec_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String)
    (result : Option String) : Prop :=
  result = (if (required ∧ initialPresent) ∨ (radioWidget ∧ ¬ blankAllowed)
            then none else some defaultLabel)
-- post-conditions-end

-- impl-start
def implementation_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
    Option String := Id.run do
  let mut chosen : Option String := some defaultLabel
  if (required && initialPresent) || (radioWidget && !blankAllowed) then
    chosen := none
  else
    chosen := some defaultLabel
  return chosen
-- impl-end

-- proof-start
theorem correct_emptyOption :
    ∀ (required initialPresent radioWidget blankAllowed : Bool) (defaultLabel : String),
      problem_spec_emptyOption required initialPresent radioWidget blankAllowed defaultLabel
        (implementation_emptyOption required initialPresent radioWidget blankAllowed defaultLabel) := by
  intro required initialPresent radioWidget blankAllowed defaultLabel
  unfold problem_spec_emptyOption implementation_emptyOption
  simp only [Id.run, bind, pure]
  split <;> simp_all
-- proof-end

-- post-conditions-start
/-- Forwarding the empty-value flag under the `blank` key sets that key to the
model attribute's flag and leaves every other keyword argument equal to its
incoming value. -/
def problem_spec_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) (result : Std.HashMap String KwargVal) : Prop :=
  result["blank"]? = some (KwargVal.flag blankAllowed) ∧
  (∀ k, k ≠ "blank" → result[k]? = base[k]?)
-- post-conditions-end

-- impl-start
def implementation_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
  let mut d := base
  d := d.insert "blank" (KwargVal.flag blankAllowed)
  return d
-- impl-end

-- proof-start
theorem correct_formKwargs :
    ∀ (base : Std.HashMap String KwargVal) (blankAllowed : Bool),
      problem_spec_formKwargs base blankAllowed (implementation_formKwargs base blankAllowed) := by
  intro base blankAllowed
  unfold problem_spec_formKwargs implementation_formKwargs
  simp only [Id.run, pure]
  refine ⟨?_, ?_⟩
  · rw [Std.HashMap.getElem?_insert]; simp
  · intro k hk
    rw [Std.HashMap.getElem?_insert]
    simp only [beq_iff_eq]
    rw [if_neg (fun h => hk h.symm)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = total exact-equality on both behaviors: problem_spec_emptyOption pins result to an if/else over the finite Bool^4 domain; problem_spec_formKwargs pins result["blank"]?=flag blankAllowed AND frames all other keys (forall k != blank, result[k]?=base[k]?). These are tight — no partial/boundary/control-flow variant satisfies them.

Attacks (all same_spec=True vs Solution.lean, impl-region-only edits; verify via scripts/lean_verify.sh <f>):
- atk_1 partial-domain (radio branch dropped, = prepatch bug 1): exit=1 (proof cannot close).
- atk_2 partial-domain ('blank' never forwarded, = prepatch bug 2): exit=1.
- atk_3 control-flow-effect (AND instead of OR): exit=1.
- atk_4 boundary (negation dropped: radioWidget && blankAllowed): exit=1.
- atk_5 boundary/negation (forwards !blankAllowed under 'blank'): exit=1.
- atk_6 ungrounded-oracle echo (match rewrite, gold-equivalent): exit=0 VERIFIES. #print axioms -> correct_emptyOption:[propext]; correct_formKwargs:[propext,Classical.choice,Quot.sound]. No sorry, no custom axioms.

Extra falsification effort: aggressive `decide`/revert proof on atk_1 (atk_1_try.lean) REJECTED with 'Expected type must not contain free variables' — theorem genuinely false. Concrete counterexamples materialized+#eval'd in ce.lean (exit 0), confirming each wrong impl diverges from the spec output at a concrete input.

Mandatory resolve step: atk_6 is the ONLY verifying same-spec impl. Its faithful refined patch is a behavioral no-op relative to gold (match-vs-if maps to identical Python if/else), i.e. = the gold patch. Ran run_resolve('django__django-12406', gold_patch) via harness (docker): resolved=True, completed=True, patch_successfully_applied=True, all FAIL_TO_PASS + PASS_TO_PASS success, empty failure lists. So the one verifying impl RESOLVES -> no verify-but-not-correct witness exists.

refinement.md audit: no axioms declared or consumed; every leg is R (type refinement) or I (identical concrete op) — NO kind-3, no A-consumed, no A-reference. A-leg audit vacuous (both changed callees modeled deeply). R/I correspondence to real callees (ModelChoiceField.__init__ empty-label decision; ForeignKey.formfield kwargs assembly) checked against patch.diff/mapping.md and is faithful. Positive control pos_control.lean (unmodified gold) verifies exit=0.

Backend run one-at-a-time; attack verifications launched concurrently (<=4) as background jobs per protocol. All evidence executed, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies. Only atk_6 (behavioral echo, match-rewrite of gold) verifies with clean axioms [propext, Classical.choice, Quot.sound]; its faithful patch (= gold) RESOLVES=True (all FAIL_TO_PASS pass: test_choices_radio_blank, test_non_blank_foreign_key_with_radio, test_clean_model_instance). Concrete divergence of the wrong impls from the spec: emptyOption at (required=F, initialPresent=F, radioWidget=T, blankAllowed=F): spec=none, atk_1/atk_4 yield some. atk_3 at (T,T,F,F): spec=none, impl=some. formKwargs atk_5 at blankAllowed=true: spec wants some(flag true), impl gives some(flag false); atk_2 omits the blank key entirely.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related behaviors for a model-backed choice field whose options are drawn
from a queryset.

* The leading empty option ("---------") that a choice field offers must be
  suppressed (set to none) not only when the field is required with an initial
  value, but ALSO when the field is rendered with a radio-style widget and the
  underlying model attribute forbids an empty value. Otherwise the empty
  option is presented with its default label.

* When a relational model attribute builds the keyword arguments for its
  generated form field, it forwards whether the attribute allows an empty value
  under the dedicated `blank` key, leaving every other keyword argument
  untouched.

These are stated abstractly as input→output relations; the implementation and
correctness proof for each are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a Boolean decision; a single map update).
-- axioms-end

-- pure-start
/-- Abstraction of the heterogeneous values stored under a form field's keyword
arguments. Only the Boolean-flag value matters for the modeled behavior; other
values (a class, a queryset, an optional name) are kept opaque. -/
inductive KwargVal where
  | obj : KwargVal
  | name : Option String → KwargVal
  | flag : Bool → KwargVal
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The leading empty option is suppressed (`none`) exactly when the field is
required with a present initial value, OR the widget is radio-style and the
model attribute forbids an empty value; otherwise it carries the default
label. -/
def problem_spec_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String)
    (result : Option String) : Prop :=
  result = (if (required ∧ initialPresent) ∨ (radioWidget ∧ ¬ blankAllowed)
            then none else some defaultLabel)
-- post-conditions-end

-- impl-start
def implementation_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
    Option String := Id.run do
  let mut chosen : Option String := some defaultLabel
  if (required && initialPresent) || (radioWidget && !blankAllowed) then
    chosen := none
  else
    chosen := some defaultLabel
  return chosen
-- impl-end

-- proof-start
theorem correct_emptyOption :
    ∀ (required initialPresent radioWidget blankAllowed : Bool) (defaultLabel : String),
      problem_spec_emptyOption required initialPresent radioWidget blankAllowed defaultLabel
        (implementation_emptyOption required initialPresent radioWidget blankAllowed defaultLabel) := by
  intro required initialPresent radioWidget blankAllowed defaultLabel
  unfold problem_spec_emptyOption implementation_emptyOption
  simp only [Id.run, bind, pure]
  split <;> simp_all
-- proof-end

-- post-conditions-start
/-- Forwarding the empty-value flag under the `blank` key sets that key to the
model attribute's flag and leaves every other keyword argument equal to its
incoming value. -/
def problem_spec_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) (result : Std.HashMap String KwargVal) : Prop :=
  result["blank"]? = some (KwargVal.flag blankAllowed) ∧
  (∀ k, k ≠ "blank" → result[k]? = base[k]?)
-- post-conditions-end

-- impl-start
def implementation_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
  let mut d := base
  d := d.insert "blank" (KwargVal.flag blankAllowed)
  return d
-- impl-end

-- proof-start
theorem correct_formKwargs :
    ∀ (base : Std.HashMap String KwargVal) (blankAllowed : Bool),
      problem_spec_formKwargs base blankAllowed (implementation_formKwargs base blankAllowed) := by
  intro base blankAllowed
  unfold problem_spec_formKwargs implementation_formKwargs
  simp only [Id.run, pure]
  refine ⟨?_, ?_⟩
  · rw [Std.HashMap.getElem?_insert]; simp
  · intro k hk
    rw [Std.HashMap.getElem?_insert]
    simp only [beq_iff_eq]
    rw [if_neg (fun h => hk h.symm)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = total exact-equality on both behaviors: problem_spec_emptyOption pins result to an if/else over the finite Bool^4 domain; problem_spec_formKwargs pins result["blank"]?=flag blankAllowed AND frames all other keys (forall k != blank, result[k]?=base[k]?). These are tight — no partial/boundary/control-flow variant satisfies them.

Attacks (all same_spec=True vs Solution.lean, impl-region-only edits; verify via scripts/lean_verify.sh <f>):
- atk_1 partial-domain (radio branch dropped, = prepatch bug 1): exit=1 (proof cannot close).
- atk_2 partial-domain ('blank' never forwarded, = prepatch bug 2): exit=1.
- atk_3 control-flow-effect (AND instead of OR): exit=1.
- atk_4 boundary (negation dropped: radioWidget && blankAllowed): exit=1.
- atk_5 boundary/negation (forwards !blankAllowed under 'blank'): exit=1.
- atk_6 ungrounded-oracle echo (match rewrite, gold-equivalent): exit=0 VERIFIES. #print axioms -> correct_emptyOption:[propext]; correct_formKwargs:[propext,Classical.choice,Quot.sound]. No sorry, no custom axioms.

Extra falsification effort: aggressive `decide`/revert proof on atk_1 (atk_1_try.lean) REJECTED with 'Expected type must not contain free variables' — theorem genuinely false. Concrete counterexamples materialized+#eval'd in ce.lean (exit 0), confirming each wrong impl diverges from the spec output at a concrete input.

Mandatory resolve step: atk_6 is the ONLY verifying same-spec impl. Its faithful refined patch is a behavioral no-op relative to gold (match-vs-if maps to identical Python if/else), i.e. = the gold patch. Ran run_resolve('django__django-12406', gold_patch) via harness (docker): resolved=True, completed=True, patch_successfully_applied=True, all FAIL_TO_PASS + PASS_TO_PASS success, empty failure lists. So the one verifying impl RESOLVES -> no verify-but-not-correct witness exists.

refinement.md audit: no axioms declared or consumed; every leg is R (type refinement) or I (identical concrete op) — NO kind-3, no A-consumed, no A-reference. A-leg audit vacuous (both changed callees modeled deeply). R/I correspondence to real callees (ModelChoiceField.__init__ empty-label decision; ForeignKey.formfield kwargs assembly) checked against patch.diff/mapping.md and is faithful. Positive control pos_control.lean (unmodified gold) verifies exit=0.

Backend run one-at-a-time; attack verifications launched concurrently (<=4) as background jobs per protocol. All evidence executed, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) verified for both modeled behaviors against the patched real repo at base_commit worktree (empty-label condition at forms/models.py:1229-1235; formfield kwargs at related.py:1029-1035).

Behavior 1 (problem_spec_emptyOption): ran the FULL discrete matrix (required, initialPresent, widget∈{None,Select,RadioSelect-instance,RadioSelect-class}, blank) directly against real forms.ModelChoiceField(...).empty_label => 0 mismatches. Spec 'none iff (required∧initialPresent)∨(radioWidget∧¬blankAllowed)' is exactly the patched branch. radioWidget:Bool faithfully abstracts isinstance(self.widget, RadioSelect) incl. subclass/class-instantiation. defaultLabel abstracts empty_label; else-branch returns the label verbatim.

Behavior 2 (problem_spec_formKwargs): spied ModelChoiceField.__init__ to capture the kwargs the real patched ForeignKey.formfield forwards. For blank=False and blank=True FKs, captured 'blank'==self.blank and ALL other keys (form_class/queryset/to_field_name/**kwargs => help_text,label,limit_choices_to,required,to_field_name) unchanged. Also confirmed the 'blank' literal is set LAST so it OVERRIDES any incoming blank kwarg (passed blank=True on a blank=False FK -> captured False), which the Lean HashMap.insert-last models correctly. Frame clause 'result[k]?=base[k]? for k≠blank' matches (base = pre-blank dict).

No input on which the modeled function disagrees with the real callee could be found; the spec is neither too strong nor drifting.

Supporting: Solution.lean compiles under lean_verify.sh (exit 0, no sorry); '#print axioms' on both correctness theorems is clean (propext, Classical.choice, Quot.sound only — no sorryAx). same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True confirm the spec region is byte-identical, so the two prepatch/G-DIFF variants differ only in impl, not in the specification.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) PASSES: hard_failures=[]. No diff markers, no reproduced gold-patch line (>=8 normalized chars), no patched file path (related.py / forms/models.py), no patched module path, and neither patched distinctive symbol (ModelChoiceField, formfield) appears in any spec-view identifier or comment. No narration terms. Spec regions verified byte-identical vs both prepatch variants (markers.same_spec=True for prepatch_1 and prepatch_2), so the analyzed spec view is the frozen consumer view.

Semantic review: the spec view is written in fully abstract terms (KwargVal, radioWidget, blankAllowed, emptyOption, formKwargs; prose 'model-backed choice field', 'relational model attribute'). It discloses the required BEHAVIOR only, which is inherently what any spec states and is already public: the problem_statement explicitly requests suppressing the blank option for a radio-style widget when blank=False, and names 'blank'. The disclosed post-condition (required and initialPresent) OR (radioWidget and not blankAllowed) reflects the fixed behavior; the required/initialPresent disjunct is pre-existing base-commit logic, not the gold edit. Behavior 2 (forwarding the empty-value flag under the 'blank' key) does not reveal the edit site (ForeignKey.formfield) nor the mechanism of the gold diff (new blank=False kwarg-param, RadioSelect import). Nothing in the spec view reveals the gold edit's location/structure beyond the public problem_statement (hints_text was not relied upon). No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
