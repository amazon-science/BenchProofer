# P2 adversarial audit — django__django-16950

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing proof, so there is no verifying-yet-nonresolving patch. The spec postcondition is a TOTAL pointwise equality result = (if shouldReset adding hasDefault isParentPk hasFormData then none else some current) over the finite 16-combination boolean domain, with V an opaque type variable so the impl can only emit `none` or `some current`. Any divergent impl differs from the pinned expression on >=1 input, yielding a propositionally-false goal (e.g. atk_1: `some current = none` at adding=T,hasDefault=T,isParentPk=F,hasFormData=T) that no tactic can close. Since the proof region is elided by same_spec, arbitrary tactics were permissible, yet falsity is structural — verify => correct here.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     Option V := Id.run do
   let mut keyAttr : Option V := some current
   if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
+    if hasDefault then
       keyAttr := none
   return keyAttr
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,11 +59,7 @@
 def implementation_clearParentKeyDefault {V : Type}
     (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
     Option V := Id.run do
-  let mut keyAttr : Option V := some current
-  if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
-      keyAttr := none
-  return keyAttr
+  return some current
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,10 @@
     (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
     Option V := Id.run do
   let mut keyAttr : Option V := some current
-  if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
-      keyAttr := none
+  if adding && hasDefault && (isParentPk || !hasFormData) then
+    keyAttr := none
+  if adding && hasDefault && isParentPk && hasFormData then
+    keyAttr := some current
   return keyAttr
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     Option V := Id.run do
   let mut keyAttr : Option V := some current
   if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
+    if hasDefault && (isParentPk && !hasFormData) then
       keyAttr := none
   return keyAttr
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,10 +59,9 @@
 def implementation_clearParentKeyDefault {V : Type}
     (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
     Option V := Id.run do
-  let mut keyAttr : Option V := some current
-  if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
-      keyAttr := none
+  let mut keyAttr : Option V := none
+  if adding && hasDefault && (isParentPk || !hasFormData) then
+    keyAttr := some current
   return keyAttr
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,8 @@
     (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
     Option V := Id.run do
   let mut keyAttr : Option V := some current
-  if adding then
-    if hasDefault && (isParentPk || !hasFormData) then
-      keyAttr := none
+  if adding && (isParentPk || !hasFormData) then
+    keyAttr := none
   return keyAttr
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to clear a parent record's key attribute while preparing an
inline child form.

When an inline child form is being prepared for a parent record that is in the
process of being newly added, the parent's linked key attribute may need to be
cleared (set to "absent") so that it is regenerated when the parent is saved.
Whether to clear it depends on four observables of the situation:

  * `adding` — whether the parent record is being newly added (not yet saved).
    Only a parent being added is ever a candidate for clearing; otherwise the
    attribute is always kept.
  * `hasDefault` — whether the linked key field carries a default value. A field
    with no default is never cleared (there is nothing to regenerate).
  * `isParentPk` — whether the linked key field IS the parent record's primary
    key (as opposed to some alternate key the child links to).
  * `hasFormData` — whether the child form carries submitted data.

The attribute is cleared exactly when the parent is being added, the key field
has a default, AND either the key field is the parent's primary key OR the form
carries no submitted data. In every other case the attribute keeps its current
value. In particular, an alternate (non-primary) key with a default is left
untouched whenever the form carries submitted data, so its value survives.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- a pure boolean function of four observables of the situation (`adding`,
-- `hasDefault`, `isParentPk`, `hasFormData`), and the attribute's current value
-- is carried through as opaque data, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether the parent's key attribute should be cleared: the parent is being
added, the key field has a default, and either the key field is the parent's
primary key or the form carries no submitted data. -/
def shouldReset (adding hasDefault isParentPk hasFormData : Bool) : Bool :=
  adding && hasDefault && (isParentPk || !hasFormData)
-- pure-end

-- post-conditions-start
/-- The result is the value of the parent's key attribute after the decision:
`none` (cleared) exactly when `shouldReset` holds, and `some current` (the
existing value carried through unchanged) otherwise. Every component is pinned —
whether it is cleared is determined by the four observables, and when it is not
cleared the retained value equals the input `current`; nothing is invented. -/
def problem_spec_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V)
    (result : Option V) : Prop :=
  result = (if shouldReset adding hasDefault isParentPk hasFormData then none
            else some current)
-- post-conditions-end

-- impl-start
def implementation_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
    Option V := Id.run do
  let mut keyAttr : Option V := some current
  if adding then
    if hasDefault && (isParentPk || !hasFormData) then
      keyAttr := none
  return keyAttr
-- impl-end

-- proof-start
theorem correct_clearParentKeyDefault {V : Type} :
    ∀ (adding hasDefault isParentPk hasFormData : Bool) (current : V),
      problem_spec_clearParentKeyDefault adding hasDefault isParentPk hasFormData
        current
        (implementation_clearParentKeyDefault adding hasDefault isParentPk
          hasFormData current) := by
  intro adding hasDefault isParentPk hasFormData current
  unfold problem_spec_clearParentKeyDefault implementation_clearParentKeyDefault
    shouldReset
  cases adding <;> cases hasDefault <;> cases isParentPk <;> cases hasFormData <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** verifier: `bash scripts/lean_verify.sh <file>`. same_spec confirmed True for all 6 attacks via swebench_unified.markers.same_spec (lean backend); each edits ONLY the impl region (axioms/pure/pre/post byte-identical).

POSITIVE CONTROL (gold impl): positive_control.lean -> lean_verify EXIT 0 (compiles, no sorry). `#print axioms correct_clearParentKeyDefault` (via pc_axioms.lean) => "'correct_clearParentKeyDefault' does not depend on any axioms" (clean, no sorryAx).

ATTACKS (6 DISTINCT same-spec wrong impls, all carry the gold-style `cases <;> rfl` proof; proof region is elided by same_spec so any tactic was allowed — none closes):
- atk_1 (prepatch bug / dropped-factor): `if adding then if hasDefault then keyAttr:=none`. lean_verify EXIT 1; rfl FAILS at case true.true.false.true (some current vs none) — the exact FAIL_TO_PASS fix case (alternate UUID key w/ default + form data). PREPATCH REPRODUCED.
- atk_2 (ungrounded / never clears): `return some current`. EXIT 1; rfl fails at true.true.false.false, true.true.true.false, true.true.true.true.
- atk_3 (partial-domain): correct except returns some current at all-true combo. EXIT 1; rfl fails at case true.true.true.true (should be none).
- atk_4 (boundary: AND for OR in 2nd factor): `hasDefault && (isParentPk && !hasFormData)`. EXIT 1; rfl fails.
- atk_5 (control-flow-effect: none/some swapped): init none, set some current when shouldReset. EXIT 1; rfl fails (16 error lines — diverges broadly).
- atk_6 (ungrounded-oracle echo: drops hasDefault factor): `if adding && (isParentPk || !hasFormData) then none`. EXIT 1; rfl fails.

STEP-2 (materialize+resolve): VACUOUS — no wrong impl closed with clean axioms, so there is no faithful refined patch to run through run_resolve. Reported honestly; nothing to execute.

**A-LEG AUDIT:** axioms region is empty PROSE ("No unchanged outside callee is consumed"). There are NO axioms/opaque declarations and NO deep-model axiom references => `#print axioms` clean, no A-legs to falsify. refinement.md legs: row1 R (init attr value <-> Option V), row2 I (outer `adding` guard, unchanged), row3 I 'deep model of changed op' (hasDefault<->has_default(), isParentPk<->attname==`_meta`.pk.name, !hasFormData<->not form.data — reproduces post-patch guard exactly), row4 R (result attr value <-> Option V). No kind-3 leg; model<->patch.diff correspondence holds (patch adds `(attname==pk.name or not form.data)` factor === `(isParentPk || !hasFormData)`).

**VERDICT:** SOUND. >=6 distinct same-spec attacks run, none closes; the totally-pinned pointwise-equality spec (with opaque V) structurally forecloses any divergent-yet-verifying impl, so verify => correct is upheld. G-EQ = pass.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing proof, so there is no verifying-yet-nonresolving patch. The spec postcondition is a TOTAL pointwise equality result = (if shouldReset adding hasDefault isParentPk hasFormData then none else some current) over the finite 16-combination boolean domain, with V an opaque type variable so the impl can only emit `none` or `some current`. Any divergent impl differs from the pinned expression on >=1 input, yielding a propositionally-false goal (e.g. atk_1: `some current = none` at adding=T,hasDefault=T,isParentPk=F,hasFormData=T) that no tactic can close. Since the proof region is elided by same_spec, arbitrary tactics were permissible, yet falsity is structural — verify => correct here.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to clear a parent record's key attribute while preparing an
inline child form.

When an inline child form is being prepared for a parent record that is in the
process of being newly added, the parent's linked key attribute may need to be
cleared (set to "absent") so that it is regenerated when the parent is saved.
Whether to clear it depends on four observables of the situation:

  * `adding` — whether the parent record is being newly added (not yet saved).
    Only a parent being added is ever a candidate for clearing; otherwise the
    attribute is always kept.
  * `hasDefault` — whether the linked key field carries a default value. A field
    with no default is never cleared (there is nothing to regenerate).
  * `isParentPk` — whether the linked key field IS the parent record's primary
    key (as opposed to some alternate key the child links to).
  * `hasFormData` — whether the child form carries submitted data.

The attribute is cleared exactly when the parent is being added, the key field
has a default, AND either the key field is the parent's primary key OR the form
carries no submitted data. In every other case the attribute keeps its current
value. In particular, an alternate (non-primary) key with a default is left
untouched whenever the form carries submitted data, so its value survives.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- a pure boolean function of four observables of the situation (`adding`,
-- `hasDefault`, `isParentPk`, `hasFormData`), and the attribute's current value
-- is carried through as opaque data, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether the parent's key attribute should be cleared: the parent is being
added, the key field has a default, and either the key field is the parent's
primary key or the form carries no submitted data. -/
def shouldReset (adding hasDefault isParentPk hasFormData : Bool) : Bool :=
  adding && hasDefault && (isParentPk || !hasFormData)
-- pure-end

-- post-conditions-start
/-- The result is the value of the parent's key attribute after the decision:
`none` (cleared) exactly when `shouldReset` holds, and `some current` (the
existing value carried through unchanged) otherwise. Every component is pinned —
whether it is cleared is determined by the four observables, and when it is not
cleared the retained value equals the input `current`; nothing is invented. -/
def problem_spec_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V)
    (result : Option V) : Prop :=
  result = (if shouldReset adding hasDefault isParentPk hasFormData then none
            else some current)
-- post-conditions-end

-- impl-start
def implementation_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
    Option V := Id.run do
  let mut keyAttr : Option V := some current
  if adding then
    if hasDefault && (isParentPk || !hasFormData) then
      keyAttr := none
  return keyAttr
-- impl-end

-- proof-start
theorem correct_clearParentKeyDefault {V : Type} :
    ∀ (adding hasDefault isParentPk hasFormData : Bool) (current : V),
      problem_spec_clearParentKeyDefault adding hasDefault isParentPk hasFormData
        current
        (implementation_clearParentKeyDefault adding hasDefault isParentPk
          hasFormData current) := by
  intro adding hasDefault isParentPk hasFormData current
  unfold problem_spec_clearParentKeyDefault implementation_clearParentKeyDefault
    shouldReset
  cases adding <;> cases hasDefault <;> cases isParentPk <;> cases hasFormData <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** verifier: `bash scripts/lean_verify.sh <file>`. same_spec confirmed True for all 6 attacks via swebench_unified.markers.same_spec (lean backend); each edits ONLY the impl region (axioms/pure/pre/post byte-identical).

POSITIVE CONTROL (gold impl): positive_control.lean -> lean_verify EXIT 0 (compiles, no sorry). `#print axioms correct_clearParentKeyDefault` (via pc_axioms.lean) => "'correct_clearParentKeyDefault' does not depend on any axioms" (clean, no sorryAx).

ATTACKS (6 DISTINCT same-spec wrong impls, all carry the gold-style `cases <;> rfl` proof; proof region is elided by same_spec so any tactic was allowed — none closes):
- atk_1 (prepatch bug / dropped-factor): `if adding then if hasDefault then keyAttr:=none`. lean_verify EXIT 1; rfl FAILS at case true.true.false.true (some current vs none) — the exact FAIL_TO_PASS fix case (alternate UUID key w/ default + form data). PREPATCH REPRODUCED.
- atk_2 (ungrounded / never clears): `return some current`. EXIT 1; rfl fails at true.true.false.false, true.true.true.false, true.true.true.true.
- atk_3 (partial-domain): correct except returns some current at all-true combo. EXIT 1; rfl fails at case true.true.true.true (should be none).
- atk_4 (boundary: AND for OR in 2nd factor): `hasDefault && (isParentPk && !hasFormData)`. EXIT 1; rfl fails.
- atk_5 (control-flow-effect: none/some swapped): init none, set some current when shouldReset. EXIT 1; rfl fails (16 error lines — diverges broadly).
- atk_6 (ungrounded-oracle echo: drops hasDefault factor): `if adding && (isParentPk || !hasFormData) then none`. EXIT 1; rfl fails.

STEP-2 (materialize+resolve): VACUOUS — no wrong impl closed with clean axioms, so there is no faithful refined patch to run through run_resolve. Reported honestly; nothing to execute.

**A-LEG AUDIT:** axioms region is empty PROSE ("No unchanged outside callee is consumed"). There are NO axioms/opaque declarations and NO deep-model axiom references => `#print axioms` clean, no A-legs to falsify. refinement.md legs: row1 R (init attr value <-> Option V), row2 I (outer `adding` guard, unchanged), row3 I 'deep model of changed op' (hasDefault<->has_default(), isParentPk<->attname==`_meta`.pk.name, !hasFormData<->not form.data — reproduces post-patch guard exactly), row4 R (result attr value <-> Option V). No kind-3 leg; model<->patch.diff correspondence holds (patch adds `(attname==pk.name or not form.data)` factor === `(isParentPk || !hasFormData)`).

**VERDICT:** SOUND. >=6 distinct same-spec attacks run, none closes; the totally-pinned pointwise-equality spec (with opaque V) structurally forecloses any divergent-yet-verifying impl, so verify => correct is upheld. G-EQ = pass.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) check for django__django-16950 lean bundle. Modeled function: BaseInlineFormSet.add_fields parent-key reset decision. Model = shouldReset(adding,hasDefault,isParentPk,hasFormData) = adding && hasDefault && (isParentPk || !hasFormData); result none if shouldReset else some current. Verified against real post-patch callee (base_commit f64fd47a + patch.diff in models.py:1173-1183). Differential test over ALL 16 boolean combinations with opaque `current`: zero mismatches — model agrees with real reset decision on every input, including the fix-case adding&hasDefault&!isParentPk&hasFormData where the attribute must be RETAINED. Observable bijection sound: adding=`_state`.adding, hasDefault=to_field.has_default(), isParentPk=(to_field.attname==...pk.name), hasFormData=bool(form.data); current/Option V lossless carrier of the single touched attribute; to_field resolution is unchanged context folded into the observables. Compiles clean (lean_verify exit 0), proof by exhaustive cases…rfl, #print axioms reports NO axioms (no sorryAx). same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Prepatch impl faithfully reproduces PRE-FIX guard (drops 2nd factor) — valid discriminator. No spec drift or over-strength found; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard_failures): no diff markers, no gold-patch lines reproduced, patched file path django/forms/models.py absent, no patched module path, only distinctive changed symbol 'add_fields' — which does NOT appear as any spec-view identifier or in any comment/docstring — and no narration words (bug/fix/patched/etc.). same_spec(Solution, Solution_prepatch)=True, so the elided prepatch carries no pre/post-fix contrast in the spec view. Semantically, the spec view's docstring/`shouldReset`/`problem_spec` describe the CORRECT behavior abstractly via four observables (adding, hasDefault, isParentPk, hasFormData) — this is the unavoidable content of any faithful spec, not a leak of the gold edit. The public problem_statement reveals only the bug SYMPTOM (UUIDField default nulled in admin inlines); the fix discriminator (pk-vs-form-data) is described only as correct behavior, not as an edit, and the fix code that appears in hints_text is correctly not used as the leakage baseline. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
