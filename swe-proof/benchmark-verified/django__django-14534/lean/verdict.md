# P2 adversarial audit — django__django-14534

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Every same-spec wrong impl FAILS to verify. The spec problem_spec_idForLabel data result := (result = data.attrs.lookup "id") is a FULL FUNCTIONAL EQUALITY to an input-grounded expression — no unconstrained output component, no ungrounded oracle, no partial domain. Any impl whose correct_idForLabel closes is thereby provably extensionally equal to data.attrs.lookup "id" (the reference function), so verify => correct holds. No closing clean-axiom wrong impl exists, so no faithful patch needed a resolve run.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  return some ("id_" ++ data.name ++ "_" ++ data.index)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,9 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  match data.attrs.lookup "id" with
+  | some v => return some v
+  | none => return some ""
 -- impl-end
 
 -- proof-start
@@ -62,5 +64,5 @@
       problem_spec_idForLabel data (implementation_idForLabel data) := by
   intro data
   unfold problem_spec_idForLabel implementation_idForLabel
-  rfl
+  simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  return data.attrs.lookup "name"
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  if data.name = "" then return none else return data.attrs.lookup "id"
 -- impl-end
 
 -- proof-start
@@ -62,5 +62,5 @@
       problem_spec_idForLabel data (implementation_idForLabel data) := by
   intro data
   unfold problem_spec_idForLabel implementation_idForLabel
-  rfl
+  simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
-  return data.attrs.lookup "id"
+  return data.attrs.reverse.lookup "id"
 -- impl-end
 
 -- proof-start
@@ -62,5 +62,5 @@
       problem_spec_idForLabel data (implementation_idForLabel data) := by
   intro data
   unfold problem_spec_idForLabel implementation_idForLabel
-  rfl
+  simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the DOM identifier to associate with the label of one rendered choice
inside an iterable, multi-option form widget.

When such a widget is rendered, each individual option is described by a small
record of presentation data. Among that data is an attribute table — the set of
HTML attributes that will be emitted on the option's input element — together
with the option's symbolic name and its positional index within the group.

The identifier a caller should point a `<label for=…>` at is exactly the `id`
attribute that the option's input element will actually carry. That value lives
in the option's attribute table under the key `"id"`. If the attribute table
holds no such key, there is no associated identifier and the answer is "none".

The desired behavior is therefore: look the `"id"` key up in the option's
attribute table and report whatever is found there (or its absence), so that the
reported identifier always agrees with the identifier the element is rendered
with — including any caller-supplied identifier scheme.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reported
-- identifier is the value stored under the `"id"` key of the option's attribute
-- table; that lookup is modeled structurally over the table itself, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The presentation data describing one option of an iterable choice widget,
restricted to the touched fields:
* `attrs` — the option's attribute table: an association list of
  `(attribute-name, attribute-value)` pairs with distinct keys (see mapping.md),
  modeling the HTML attributes the option's input element carries;
* `name` — the option group's symbolic name;
* `index` — the option's positional index within the group, as a string. -/
structure WidgetData where
  attrs : List (String × String)
  name : String
  index : String
-- pure-end

-- post-conditions-start
/-- The reported label identifier is exactly the value stored under the `"id"`
key of the option's attribute table: `some v` when the table maps `"id"` to `v`,
and `none` when the table has no `"id"` entry. The option's `name` and `index`
do not constrain the result. -/
def problem_spec_idForLabel (data : WidgetData) (result : Option String) : Prop :=
  result = data.attrs.lookup "id"
-- post-conditions-end

-- impl-start
def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
  return data.attrs.lookup "id"
-- impl-end

-- proof-start
theorem correct_idForLabel :
    ∀ (data : WidgetData),
      problem_spec_idForLabel data (implementation_idForLabel data) := by
  intro data
  unfold problem_spec_idForLabel implementation_idForLabel
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pure R/I bundle. meta.json confirms axioms=[], deep_model_references=[], conf_skip=false => the A-legs are vacuous (nothing to attack on axioms/deep-model correspondence). All legs are R (leg1 self.data carrier -> WidgetData; leg2 self.data['attrs'] -> List(String×String); leg4 return -> Option String) or I (leg3: the changed op self.data['attrs'].get('id') deeply modeled as data.attrs.lookup "id"). No kind-3 (ungrounded) legs. Correspondence holds: List.lookup first-match under distinct HTML-attribute keys == Python dict.get.

SAME-SPEC: all 6 attacks + positive control return same_spec=True under swebench_unified.markers.same_spec (lean backend) vs the bundle Solution.lean (impl region edited only).

### VERIFICATION (bash scripts/lean_verify.sh <f>, run concurrently in 2 batches of ≤4):
- pos_control.lean (byte-identical gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_idForLabel => 'does not depend on any axioms' (clean).
- atk_1.lean prepatch-bug synthesize some("id_"++name++"_"++index): EXIT 1 (rfl fails; goal (pure (some ...)).run = List.lookup "id" data.attrs unprovable). Reproduces prepatch bug.
- atk_2.lean partial-domain (correct when id present, some "" when absent): EXIT 1 (simp made no progress).
- atk_3.lean wrong-key lookup "name": EXIT 1 (rfl fails).
- atk_4.lean control-flow-effect always none: EXIT 1 (rfl fails; (pure none).run = List.lookup "id" data.attrs unprovable).
- atk_5.lean ungrounded-oracle echo, branch on name (none if name="" else lookup id): EXIT 1 (simp made no progress).
- atk_6.lean boundary/duplicate-key sensitivity reverse.lookup "id": EXIT 1 (unsolved goal List.lookup "id" data.attrs.reverse = List.lookup "id" data.attrs — model has NO distinctness invariant, so reverse.lookup genuinely differs on duplicate keys, but this only makes the impl WRONG, never able to verify a stricter equality).

RESULT: 6/6 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-key, ungrounded-oracle echo, prepatch-bug) FAIL to close against the full-equality spec; positive control closes with clean axioms. No verify=>correct violation found. Because no wrong impl closed, the mandatory resolve-run obligation (which fires only for a CLOSING clean-axiom wrong impl) is vacuously satisfied. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Every same-spec wrong impl FAILS to verify. The spec problem_spec_idForLabel data result := (result = data.attrs.lookup "id") is a FULL FUNCTIONAL EQUALITY to an input-grounded expression — no unconstrained output component, no ungrounded oracle, no partial domain. Any impl whose correct_idForLabel closes is thereby provably extensionally equal to data.attrs.lookup "id" (the reference function), so verify => correct holds. No closing clean-axiom wrong impl exists, so no faithful patch needed a resolve run.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the DOM identifier to associate with the label of one rendered choice
inside an iterable, multi-option form widget.

When such a widget is rendered, each individual option is described by a small
record of presentation data. Among that data is an attribute table — the set of
HTML attributes that will be emitted on the option's input element — together
with the option's symbolic name and its positional index within the group.

The identifier a caller should point a `<label for=…>` at is exactly the `id`
attribute that the option's input element will actually carry. That value lives
in the option's attribute table under the key `"id"`. If the attribute table
holds no such key, there is no associated identifier and the answer is "none".

The desired behavior is therefore: look the `"id"` key up in the option's
attribute table and report whatever is found there (or its absence), so that the
reported identifier always agrees with the identifier the element is rendered
with — including any caller-supplied identifier scheme.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reported
-- identifier is the value stored under the `"id"` key of the option's attribute
-- table; that lookup is modeled structurally over the table itself, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The presentation data describing one option of an iterable choice widget,
restricted to the touched fields:
* `attrs` — the option's attribute table: an association list of
  `(attribute-name, attribute-value)` pairs with distinct keys (see mapping.md),
  modeling the HTML attributes the option's input element carries;
* `name` — the option group's symbolic name;
* `index` — the option's positional index within the group, as a string. -/
structure WidgetData where
  attrs : List (String × String)
  name : String
  index : String
-- pure-end

-- post-conditions-start
/-- The reported label identifier is exactly the value stored under the `"id"`
key of the option's attribute table: `some v` when the table maps `"id"` to `v`,
and `none` when the table has no `"id"` entry. The option's `name` and `index`
do not constrain the result. -/
def problem_spec_idForLabel (data : WidgetData) (result : Option String) : Prop :=
  result = data.attrs.lookup "id"
-- post-conditions-end

-- impl-start
def implementation_idForLabel (data : WidgetData) : Option String := Id.run do
  return data.attrs.lookup "id"
-- impl-end

-- proof-start
theorem correct_idForLabel :
    ∀ (data : WidgetData),
      problem_spec_idForLabel data (implementation_idForLabel data) := by
  intro data
  unfold problem_spec_idForLabel implementation_idForLabel
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pure R/I bundle. meta.json confirms axioms=[], deep_model_references=[], conf_skip=false => the A-legs are vacuous (nothing to attack on axioms/deep-model correspondence). All legs are R (leg1 self.data carrier -> WidgetData; leg2 self.data['attrs'] -> List(String×String); leg4 return -> Option String) or I (leg3: the changed op self.data['attrs'].get('id') deeply modeled as data.attrs.lookup "id"). No kind-3 (ungrounded) legs. Correspondence holds: List.lookup first-match under distinct HTML-attribute keys == Python dict.get.

SAME-SPEC: all 6 attacks + positive control return same_spec=True under swebench_unified.markers.same_spec (lean backend) vs the bundle Solution.lean (impl region edited only).

### VERIFICATION (bash scripts/lean_verify.sh <f>, run concurrently in 2 batches of ≤4):
- pos_control.lean (byte-identical gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_idForLabel => 'does not depend on any axioms' (clean).
- atk_1.lean prepatch-bug synthesize some("id_"++name++"_"++index): EXIT 1 (rfl fails; goal (pure (some ...)).run = List.lookup "id" data.attrs unprovable). Reproduces prepatch bug.
- atk_2.lean partial-domain (correct when id present, some "" when absent): EXIT 1 (simp made no progress).
- atk_3.lean wrong-key lookup "name": EXIT 1 (rfl fails).
- atk_4.lean control-flow-effect always none: EXIT 1 (rfl fails; (pure none).run = List.lookup "id" data.attrs unprovable).
- atk_5.lean ungrounded-oracle echo, branch on name (none if name="" else lookup id): EXIT 1 (simp made no progress).
- atk_6.lean boundary/duplicate-key sensitivity reverse.lookup "id": EXIT 1 (unsolved goal List.lookup "id" data.attrs.reverse = List.lookup "id" data.attrs — model has NO distinctness invariant, so reverse.lookup genuinely differs on duplicate keys, but this only makes the impl WRONG, never able to verify a stricter equality).

RESULT: 6/6 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-key, ungrounded-oracle echo, prepatch-bug) FAIL to close against the full-equality spec; positive control closes with clean axioms. No verify=>correct violation found. Because no wrong impl closed, the mandatory resolve-run obligation (which fires only for a CLOSING clean-axiom wrong impl) is vacuously satisfied. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the modeled function vs the real post-patch callee. Real callee: BoundWidget.id_for_label returns self.data['attrs'].get('id') (patch.diff, django/forms/boundfield.py:277-278). Spec: problem_spec_idForLabel pins result = data.attrs.lookup "id". dict.get('id') and List.lookup "id" agree on every input: present key -> value/some v, absent key -> None/none. attrs is modeled as an assoc list with distinct keys (HTML attribute dicts have unique names), so lookup returns the unique value == dict.get. name/index are correctly left free (only read by pre-patch synthesis) and do NOT constrain the result, matching the post-patch code which ignores them. No diverging input exists — the spec is neither too strong nor drifted from repo behavior. Corroboration: (1) same_spec(Solution, Solution_prepatch, LeanBackend) == True (spec region byte-identical; only impl/proof differ); (2) lean_verify.sh exit 0, #print axioms correct_idForLabel => 'does not depend on any axioms' (real proof, no sorryAx); (3) G-CONF conformance_check.py oracle (data['attrs'].get('id')) is a faithful transliteration of the patched body and the R/I shadow is identical, agreeing over hand-picked edge cases (custom prefix id, missing 'id' -> None, default-style id) + 120k fuzzed inputs. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (=True); impl/proof are elided in the spec view. The gold edit is: id_for_label body changes from 'id_%s_%s' % (self.data['name'], self.data['index']) to self.data['attrs'].get('id'). The PUBLIC problem_statement already discloses this entire fix verbatim: it shows the buggy body, identifies widget['attrs']['id'] as the value 'we would like to use', and explicitly instructs 'By changing the code from above to return self.data['attrs']['id'] that function behaves as expected.' The spec view therefore cannot leak the edit beyond what is public. The spec (report the value under the 'id' key of the option's attribute table, none if absent) describes exactly the publicly-known desired behavior, expressed in abstract Lean modeling terms (WidgetData / attrs.lookup "id"), without quoting any gold-patch specifics not already in the problem_statement. The only elaboration past the statement's literal ['id'] indexing is the none-when-absent semantics (.get vs []), which is a natural correctness detail rather than gold-patch-derived secret information. No line in the spec view leaks gold beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
