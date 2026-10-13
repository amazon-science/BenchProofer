# P2 adversarial audit — django__django-12308

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -63,12 +63,7 @@
   ensures out = jsonDisplay v
   do
     -- impl-start
-    let out : String :=
-      if v.present then
-        match v.prep with
-        | PrepResult.json text => text
-        | PrepResult.unserializable => v.generic
-      else v.generic
+    let out : String := v.generic
     return out
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -64,11 +64,9 @@
   do
     -- impl-start
     let out : String :=
-      if v.present then
-        match v.prep with
-        | PrepResult.json text => text
-        | PrepResult.unserializable => v.generic
-      else v.generic
+      match v.prep with
+      | PrepResult.json text => text
+      | PrepResult.unserializable => v.generic
     return out
     -- impl-end
 
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -67,7 +67,7 @@
       if v.present then
         match v.prep with
         | PrepResult.json text => text
-        | PrepResult.unserializable => v.generic
+        | PrepResult.unserializable => ""
       else v.generic
     return out
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -68,7 +68,7 @@
         match v.prep with
         | PrepResult.json text => text
         | PrepResult.unserializable => v.generic
-      else v.generic
+      else ""
     return out
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -66,7 +66,7 @@
     let out : String :=
       if v.present then
         match v.prep with
-        | PrepResult.json text => text
+        | PrepResult.json _ => v.generic
         | PrepResult.unserializable => v.generic
       else v.generic
     return out
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -66,7 +66,7 @@
     let out : String :=
       if v.present then
         match v.prep with
-        | PrepResult.json text => text
+        | PrepResult.json text => text ++ "!"
         | PrepResult.unserializable => v.generic
       else v.generic
     return out
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -64,7 +64,7 @@
   do
     -- impl-start
     let out : String :=
-      if v.present then
+      if !v.present then
         match v.prep with
         | PrepResult.json text => text
         | PrepResult.unserializable => v.generic
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
 /- No consumed axioms. The display choice for a JSON-typed value is modeled
@@ -63,10 +63,11 @@
   ensures out = jsonDisplay v
   do
     -- impl-start
+    -- prepend a space to the JSON text (subtle boundary divergence)
     let out : String :=
       if v.present then
         match v.prep with
-        | PrepResult.json text => text
+        | PrepResult.json text => " " ++ text
         | PrepResult.unserializable => v.generic
       else v.generic
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The display choice for a JSON-typed value is modeled
   DEEPLY in the `pure` region (`jsonDisplay`): the outcomes of the two
   surrounding helpers the choice consults — preparing the value as JSON text,
   and the generic textual rendering — are carried as observable fields of the
   value view and validated against the real helpers by axiom_check.py (G-AX);
   there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The outcome of preparing a value as JSON text: either a successfully
   serialized JSON string, or a failure because the value has no JSON
   serialization (a non-serializable value). -/
inductive PrepResult where
  | json (text : String)
  | unserializable
  deriving DecidableEq

/- The observable facts about the value being rendered that the display choice
   depends on:
   * `present`  — whether the value counts as present (non-empty);
   * `prep`     — the outcome of preparing the value as JSON text;
   * `generic`  — the generic textual rendering used when no JSON form applies
                  (which renders an absent value as the empty marker).
   These are produced by the surrounding helpers; choosing among them is the
   modeled behaviour. The Lean↔repo bijection is in mapping.md §2. -/
structure ValueView where
  present : Bool
  prep : PrepResult
  generic : String
  deriving DecidableEq

/- The display chosen for a JSON-typed field's value when rendered read-only.
   Desired behaviour: a present value is shown as its JSON text; a present value
   with no JSON serialization falls back to the generic rendering; an absent
   value also uses the generic rendering. -/
def jsonDisplay (v : ValueView) : String :=
  if v.present then
    match v.prep with
    | PrepResult.json text => text
    | PrepResult.unserializable => v.generic
  else v.generic
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a JSON-typed field's stored value for read-only display. A present
   value is shown as its JSON text; a present value that cannot be serialized to
   JSON, and an absent value, are shown via the generic rendering instead. -/
method displayJson (v : ValueView) return (out : String)
  ensures out = jsonDisplay v
  do
    -- impl-start
    let out : String :=
      if v.present then
        match v.prep with
        | PrepResult.json text => text
        | PrepResult.unserializable => v.generic
      else v.generic
    return out
    -- impl-end

prove_correct displayJson by
  loom_solve
  simp [jsonDisplay]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a fully-concrete deterministic equality `ensures out = jsonDisplay v`, where `jsonDisplay v = if v.present then (match v.prep with json text => text | unserializable => v.generic) else v.generic`. Because the postcondition pins `out` to a total computable function of the input, any verifying impl must reproduce jsonDisplay exactly on every input — there is no opaque/axiomatized oracle to echo (ungrounded-oracle attack is impossible: jsonDisplay is concrete, not an answer key), so verify⇒correct.

All files edited in impl region only; same_spec=True for all 8 attacks + positive control (verified via swebench_unified.markers.same_spec, velvet backend).

### RESULTS (bash scripts/lean_verify.sh <f>, from project root; run concurrently ≤4):
- pos.lean (byte-identical to bundle Solution.lean; correct impl): exit 0 (VERIFIES).
- atk_1 prepatch bug `out := v.generic` (impl byte-identical to bundle Solution_prepatch.lean): exit 1, rejected on `ensures_1: out = jsonDisplay v` (goal `v.present = true -> v.generic = (match v.prep with json text => text | unser => v.generic)`, False). prepatch_reproduced=True.
- atk_2 drop `present` guard (partial-domain/control-flow): exit 1.
- atk_3 unserializable arm -> "" (boundary): exit 1.
- atk_4 absent branch -> "" (boundary): exit 1.
- atk_5 json arm -> v.generic (serializable shown as generic, core-bug inverted): exit 1.
- atk_6 json arm -> text ++ "!" (suffix): exit 1.
- atk_7 inverted present guard `if !v.present` (control-flow-effect): exit 1.
- atk_8 json arm -> " " ++ text (whitespace boundary divergence): exit 1.
Every rejection is on the postcondition case `ensures_1: out = jsonDisplay v` (genuine spec-strength rejection, not a syntax/type error) — logs kept *.lean.log.

Step 2 (materialize faithful refined patch + run_resolve): VACUOUS — zero wrong impls verified, so there is no verifying-but-wrong candidate whose patch could fail to resolve. Nothing to run through the harness; no BROKEN condition possible on this evidence.

Refinement.md A-leg audit (steps A1-A5): every leg is R / A-reference / I; no A-consumed and no kind-3. There is NO module-level `axiom` in Solution.lean (grep count 0). The changed op (JSON-dispatch arm + try/except fallback) is modeled DEEPLY in jsonDisplay's if/match ladder, not hidden behind an axiom about the function under change. The three A-references correspond to the real, patch-UNCHANGED callees: prep <-> JSONField.get_prep_value (json.dumps, django/db/models/fields/json.py:81), generic <-> display_for_value (django/contrib/admin/utils.py:405), present <-> bool(value). These are validated in-container by axiom_check.py/G-AX (meta.json G-AX pass: 20 boundary + 20000 fuzz, 15298 serializable / 4702 unserializable, 0 violations) and their branch-selection R/I shadow by G-CONF (100020 inputs, seed 12308, 0 disagreements). mapping.md's Lean<->Python bijection is consistent with these callees. Correspondence holds.

Note on positive control: a structurally-different-but-correct impl (`match v.prep, v.present with | json t, true => t | _,_ => generic`) does NOT verify under the bundle's frozen canned proof `loom_solve; simp [jsonDisplay]` (proof-automation limitation, not spec vacuity — the residual goal is a True definitional-unfold equality the canned tactic doesn't close). The valid positive control is therefore the bundle's own impl, which verifies (exit 0). This does not weaken the SOUND verdict: spec non-vacuity is established by pos verifying while all 8 behaviorally-distinct impls reject on the postcondition.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The display choice for a JSON-typed value is modeled
   DEEPLY in the `pure` region (`jsonDisplay`): the outcomes of the two
   surrounding helpers the choice consults — preparing the value as JSON text,
   and the generic textual rendering — are carried as observable fields of the
   value view and validated against the real helpers by axiom_check.py (G-AX);
   there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The outcome of preparing a value as JSON text: either a successfully
   serialized JSON string, or a failure because the value has no JSON
   serialization (a non-serializable value). -/
inductive PrepResult where
  | json (text : String)
  | unserializable
  deriving DecidableEq

/- The observable facts about the value being rendered that the display choice
   depends on:
   * `present`  — whether the value counts as present (non-empty);
   * `prep`     — the outcome of preparing the value as JSON text;
   * `generic`  — the generic textual rendering used when no JSON form applies
                  (which renders an absent value as the empty marker).
   These are produced by the surrounding helpers; choosing among them is the
   modeled behaviour. The Lean↔repo bijection is in mapping.md §2. -/
structure ValueView where
  present : Bool
  prep : PrepResult
  generic : String
  deriving DecidableEq

/- The display chosen for a JSON-typed field's value when rendered read-only.
   Desired behaviour: a present value is shown as its JSON text; a present value
   with no JSON serialization falls back to the generic rendering; an absent
   value also uses the generic rendering. -/
def jsonDisplay (v : ValueView) : String :=
  if v.present then
    match v.prep with
    | PrepResult.json text => text
    | PrepResult.unserializable => v.generic
  else v.generic
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a JSON-typed field's stored value for read-only display. A present
   value is shown as its JSON text; a present value that cannot be serialized to
   JSON, and an absent value, are shown via the generic rendering instead. -/
method displayJson (v : ValueView) return (out : String)
  ensures out = jsonDisplay v
  do
    -- impl-start
    let out : String :=
      if v.present then
        match v.prep with
        | PrepResult.json text => text
        | PrepResult.unserializable => v.generic
      else v.generic
    return out
    -- impl-end

prove_correct displayJson by
  loom_solve
  simp [jsonDisplay]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a fully-concrete deterministic equality `ensures out = jsonDisplay v`, where `jsonDisplay v = if v.present then (match v.prep with json text => text | unserializable => v.generic) else v.generic`. Because the postcondition pins `out` to a total computable function of the input, any verifying impl must reproduce jsonDisplay exactly on every input — there is no opaque/axiomatized oracle to echo (ungrounded-oracle attack is impossible: jsonDisplay is concrete, not an answer key), so verify⇒correct.

All files edited in impl region only; same_spec=True for all 8 attacks + positive control (verified via swebench_unified.markers.same_spec, velvet backend).

### RESULTS (bash scripts/lean_verify.sh <f>, from project root; run concurrently ≤4):
- pos.lean (byte-identical to bundle Solution.lean; correct impl): exit 0 (VERIFIES).
- atk_1 prepatch bug `out := v.generic` (impl byte-identical to bundle Solution_prepatch.lean): exit 1, rejected on `ensures_1: out = jsonDisplay v` (goal `v.present = true -> v.generic = (match v.prep with json text => text | unser => v.generic)`, False). prepatch_reproduced=True.
- atk_2 drop `present` guard (partial-domain/control-flow): exit 1.
- atk_3 unserializable arm -> "" (boundary): exit 1.
- atk_4 absent branch -> "" (boundary): exit 1.
- atk_5 json arm -> v.generic (serializable shown as generic, core-bug inverted): exit 1.
- atk_6 json arm -> text ++ "!" (suffix): exit 1.
- atk_7 inverted present guard `if !v.present` (control-flow-effect): exit 1.
- atk_8 json arm -> " " ++ text (whitespace boundary divergence): exit 1.
Every rejection is on the postcondition case `ensures_1: out = jsonDisplay v` (genuine spec-strength rejection, not a syntax/type error) — logs kept *.lean.log.

Step 2 (materialize faithful refined patch + run_resolve): VACUOUS — zero wrong impls verified, so there is no verifying-but-wrong candidate whose patch could fail to resolve. Nothing to run through the harness; no BROKEN condition possible on this evidence.

Refinement.md A-leg audit (steps A1-A5): every leg is R / A-reference / I; no A-consumed and no kind-3. There is NO module-level `axiom` in Solution.lean (grep count 0). The changed op (JSON-dispatch arm + try/except fallback) is modeled DEEPLY in jsonDisplay's if/match ladder, not hidden behind an axiom about the function under change. The three A-references correspond to the real, patch-UNCHANGED callees: prep <-> JSONField.get_prep_value (json.dumps, django/db/models/fields/json.py:81), generic <-> display_for_value (django/contrib/admin/utils.py:405), present <-> bool(value). These are validated in-container by axiom_check.py/G-AX (meta.json G-AX pass: 20 boundary + 20000 fuzz, 15298 serializable / 4702 unserializable, 0 violations) and their branch-selection R/I shadow by G-CONF (100020 inputs, seed 12308, 0 disagreements). mapping.md's Lean<->Python bijection is consistent with these callees. Correspondence holds.

Note on positive control: a structurally-different-but-correct impl (`match v.prep, v.present with | json t, true => t | _,_ => generic`) does NOT verify under the bundle's frozen canned proof `loom_solve; simp [jsonDisplay]` (proof-automation limitation, not spec vacuity — the residual goal is a True definitional-unfold equality the canned tactic doesn't close). The valid positive control is therefore the bundle's own impl, which verifies (exit 0). This does not weaken the SOUND verdict: spec non-vacuity is established by pos verifying while all 8 behaviorally-distinct impls reject on the postcondition.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. The modeled function jsonDisplay(v: ValueView) captures display_for_field's JSON-branch dispatch: present→(json text | fallback generic), absent→generic. I transliterated jsonDisplay to Python using the REAL repo callees (bool(value), JSONField().get_prep_value, display_for_value) per the mapping.md §2/§3 bijection and diffed it against the real patched display_for_field(value, models.JSONField(), '-') at base_commit 2e0f04507b. Results: (a) 32 hand-picked adversarial inputs {}, [], '', 0, 0.0, False, None, True, dicts/lists, Decimal, date, datetime, time, bytes, set, tuple, complex, lambda, object, range, frozenset → 0 divergences; (b) 200,000 independent fuzz inputs (seed 99991, richer distribution than the pinned G-CONF/G-AX seed 12308) → 0 divergences; (c) non-TypeError exception boundary (circular reference → ValueError; huge-int JSON key) → identical behavior on both sides, because the shadow invokes the real callee so any non-TypeError exception propagates identically (the TypeError-only mapping to `unserializable` is thus not a drift). Scope restriction is honest: field is fixed to JSONField (this method IS the JSON arm), earlier if/elif arms are orthogonal to the JSON value path, and the value-is-None/absent case is folded into `generic` via the real display_for_value. Spec integrity confirmed: same_spec(Solution, Solution_prepatch)=True; Solution.lean verifies (exit 0); Solution_prepatch.lean fails on exactly the discriminating clause (present∧serializable ⇒ text, where pre-patch gave generic), so G-DIFF is real. The spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously verified. (1) Spec region is frozen/byte-identical: markers.same_spec(Solution.lean, itself)=True and same_spec vs Solution_prepatch.lean=True; impl-start..impl-end and prove_correct bodies are elided in the consumer spec view. (2) Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor) passes with zero hard failures: no diff markers, no reproduced gold-patch line, no patched file path (django/contrib/admin/utils.py) and no dotted module path in the view, no spec-view identifier embedding a patched repo symbol, no narration terms. (3) Semantic judgment vs the PUBLIC problem_statement only (not hints_text): the spec view exposes only an ABSTRACT behavioral model (jsonDisplay: present value -> JSON text; present-but-unserializable -> generic rendering; absent -> generic rendering). The problem_statement already discloses strictly MORE: it names the target function django.contrib.admin.utils.display_for_field, prescribes adding a special case that calls the JSONField's prep/prepare_value rather than json.dumps directly, explicitly calls out the InvalidJSONInput/serialization-failure case, and shows the {'foo': 'bar'} vs {"foo": "bar"} symptom. The gold-edit specifics (isinstance(field, models.JSONField), try/except TypeError, field.get_prep_value, display_for_value) appear ONLY in mapping.md/refinement.md (audit artifacts, NOT the consumer spec view). The spec view names no repo symbols and adds nothing reconstructible beyond what the public statement already grants. No RELAXED_LEAKAGE.md present and relaxed_leakage flag unset, so no relaxation applies. Recorded meta status: G-LEAK pass, G-PANEL-3 NO-LEAKAGE — concur.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
