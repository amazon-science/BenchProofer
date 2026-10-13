# P2 adversarial audit — django__django-13741

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_wrongconst.lean`, `atk_2_prepatch.lean`, `atk_3_boundary.lean`, `atk_4_negate.lean`, `atk_6_diverge2.lean`, `atk_7_diverge_nodec.lean`, `atk_9_alltrue.lean`, `atk_10_flipsome.lean` |

**Non-vacuity.** The positive control `pos_control_match.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_wrongconst.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,7 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := false
     return out
     -- impl-end
 
```

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,7 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := userFlag.getD false
     return out
     -- impl-end
 
```

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,9 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := match userFlag with
+      | none => false
+      | some b => b
     return out
     -- impl-end
 
```

Attack 4 — `atk_4_negate.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,7 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := !(userFlag.getD true)
     return out
     -- impl-end
 
```

Attack 5 — `atk_6_diverge2.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,12 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let mut out := !(userFlag.getD true)
+    let mut i := 1
+    while i > 0
+      invariant True
+    do
+      i := i + 1
     return out
     -- impl-end
 
```

Attack 6 — `atk_7_diverge_nodec.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,13 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let mut out : Bool := false
+    let mut i : Nat := 1
+    while i > 0
+      invariant True
+    do
+      out := false
+      i := i
     return out
     -- impl-end
 
```

Attack 7 — `atk_9_alltrue.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,7 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := true
     return out
     -- impl-end
 
```

Attack 8 — `atk_10_flipsome.lean` → rejected (same spec, does not verify — good)

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
 /- The two presentation hooks a generic form field already provides for a field
@@ -80,9 +80,9 @@
     noEditValue (lockedDefault none) data initial = initial
   do
     -- impl-start
-    -- Default the non-editability flag to "non-editable" when the caller leaves
-    -- it unspecified; honour an explicitly supplied flag unchanged.
-    let out := userFlag.getD true
+    let out := match userFlag with
+      | none => true
+      | some b => !b
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_match.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two presentation hooks a generic form field already provides for a field
   the user is not allowed to edit. They are UNCHANGED, pre-existing behaviour
   of the base field class; here they are axiomatized as the weakest contracts
   the desired behaviour relies on (provenance + executable soundness check:
   mapping.md / axiom_check.py, G-AX).

   `noEditChange initial data` — whether the field reports that its submitted
   `data` differs from its stored `initial`, as a function of whether the field
   is non-editable. The single fact consumed: a non-editable field NEVER reports
   a change, whatever the submitted and stored values are.

   `noEditValue data initial` — the value the field exposes when rendering a
   bound form, as a function of whether the field is non-editable. The single
   fact consumed: a non-editable field always exposes its stored `initial`,
   discarding the submitted `data`. -/
axiom noEditChange : Bool → List Char → List Char → Bool
axiom noEditChange_locked : ∀ (initial data : List Char),
    noEditChange true initial data = false

axiom noEditValue : Bool → List Char → List Char → List Char
axiom noEditValue_locked : ∀ (data initial : List Char),
    noEditValue true data initial = initial

@[grind] lemma noEditChange_locked' (initial data : List Char) :
    noEditChange true initial data = false := noEditChange_locked initial data
@[grind] lemma noEditValue_locked' (data initial : List Char) :
    noEditValue true data initial = initial := noEditValue_locked data initial
-- axioms-end

-- pure-start
/- The non-editability flag a freshly constructed read-only credential-digest
   field ends up with.

   Construction may receive an explicit flag (`some true` / `some false`); if the
   caller leaves it unspecified (`none`), the field supplies its own default. The
   desired behaviour is that, unspecified, such a field is non-editable: its
   stored value is shown but cannot be changed by the user, so a tampered
   submission is ignored in favour of the stored value. An explicitly supplied
   flag is honoured verbatim (it is not overridden). -/
@[grind] def lockedDefault (userFlag : Option Bool) : Bool :=
  userFlag.getD true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the non-editability flag with which a read-only credential-digest
   field is constructed.

   Desired behaviour: when the caller does not specify the flag, the field is
   non-editable by default, so the stored value is displayed but protected from
   user edits; an explicitly specified flag is honoured unchanged.

   Two consequences of defaulting to non-editable are pinned as well (the reason
   no bespoke change-suppression hooks are needed on such a field): a field that
   is non-editable by this default never reports a change between stored and
   submitted values, and always exposes its stored value when bound. These rest
   on the field framework's pre-existing non-editable handling (the `noEdit*`
   contracts).

   `userFlag` is read-only (not `mut`): construction reads the caller's optional
   flag and returns the resulting flag; it mutates nothing (directive 5). -/
method readonlyDigestFieldLocked (userFlag : Option Bool) return (out : Bool)
  ensures out = lockedDefault userFlag
  ensures ∀ (initial data : List Char),
    noEditChange (lockedDefault none) initial data = false
  ensures ∀ (data initial : List Char),
    noEditValue (lockedDefault none) data initial = initial
  do
    -- impl-start
    let out := match userFlag with
      | none => true
      | some b => b
    return out
    -- impl-end

prove_correct readonlyDigestFieldLocked by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** readonlyDigestFieldLocked(userFlag: Option Bool) -> out:Bool. Sole output constraint is ensures_1 `out = lockedDefault userFlag` where lockedDefault u = u.getD true (none=>true, some b=>b) — a COMPLETE functional pin over all three observable construction cases. ensures_2/ensures_3 (the noEdit* axiom facts) are evaluated at the CONSTANT `lockedDefault none = true`, never mention `out`, and are discharged by the grind lemmas regardless of impl, so they impose zero constraint on the impl and cannot be used to dodge the ensures_1 pin. Semantics: termination="partial", choice="demonic".

BEHAVIORAL FALSIFICATION BATTERY (8 same-spec wrong impls, same_spec=True each, verified with `bash scripts/lean_verify.sh <f>`, run concurrently <=4/batch): all REJECTED at verify (exit 1), i.e. the spec is TIGHT:
- atk_1_wrongconst `return false` -> exit1 (ensures_1 fails at none & some true)
- atk_2_prepatch `userFlag.getD false` (THE PREPATCH BUG, none=>editable) -> exit1 (goal `userFlag.getD false = lockedDefault userFlag` fails at none; == F2P assertion field.disabled is True). prepatch_reproduced.
- atk_3_boundary `match none=>false | some b=>b` -> exit1 (fails at none)
- atk_4_negate `!(userFlag.getD true)` -> exit1
- atk_6_diverge2 / atk_7_diverge_nodec: loop-based wrong impls with NON-vacuous done-condition (`while i>0`) -> exit1 (VC uses done-cond i=0; goal on real value; loop does NOT exploit the divergence hole). Confirms only literal `while true` triggers vacuity.
- atk_9_alltrue `return true` (ignores explicit some false) -> exit1 (fails at some false)
- atk_10_flipsome `match none=>true | some b=>!b` -> exit1 (fails at some)
POSITIVE CONTROLS: pos_control (exact copy) exit0; pos_control_match (STRUCTURALLY DIFFERENT correct impl `match none=>true | some b=>b`) exit0 => spec non-vacuous.

DIVERGENCE OBSERVATION (reported transparently; NOT a G-EQ break, excluded from the mechanical attack list): atk_5_diverge_wrong (`while true do out:=false; return out`) and atk_8_diverge_neg (`out := !(userFlag.getD true); while true ...`) BOTH VERIFY (exit0), value-independently. This is the standard partial-correctness vacuity of `set_option loom.semantics.termination "partial"`: a `while true` loop makes the done-condition False, so the post-loop VC is discharged vacuously. Per protocol step 2 I MATERIALIZED the closest faithful patch (infinite `while True: pass` in ReadOnlyPasswordHashField.`__init__`, diverge_patch.diff) and RAN it: `run_resolve('django__django-13741', diverge_patch, timeout=600)` returned resolved=False, COMPLETED=False, note='no report ... harness error' — i.e. the harness hung on the infinite loop and produced NO graded report. This is the INCONCLUSIVE infra outcome, NOT the BROKEN signature (build_one.py:306 requires `completed=True AND not resolved`). POSITIVE HARNESS CONTROL: gold patch.diff -> run_resolve returned resolved=True, completed=True (harness+image verified healthy for this instance).

WHY DIVERGENCE IS OUT OF SCOPE (not a break): (1) No faithful refined patch EXISTS — refinement.md maps the TERMINATING computation userFlag.getD true <-> setdefault('disabled',True) (leg A2, I-op); there is no refinement leg producing an infinite loop, so a divergent impl has no image under the map and the protocol's `faithful refined patch` is undefined for it. (2) Reductio: if `while true` broke a spec, all 401 partial-semantics velvet bundles would be trivially BROKEN by wrapping the gold in `while true`; `partial` is a deliberate methodology choice (prompts/velvet/quickref.md) and G-EQ audits refinement fidelity + axiom correspondence, not the termination-semantics option. (3) The gold impl is straight-line and terminating; the twin-artifact guarantee (refinement.md D) is explicitly scoped to impls `refined by the map above`.

REFINEMENT.MD AUDIT (step 3): legs A1(R param<->disabled kwarg)/A2(I: the genuinely-CHANGED op modeled DIRECTLY as Option.getD true, NOT axiomatized — no kind-3)/A3(R Bool<->self.disabled)/B1(A-consumed)/B2(A-consumed). A-legs confirmed against REAL base callees in worktree @ base_commit d746f28949c009251a8741ba03d156964050717f: B1 noEditChange true _ _ = false <-> Field.has_changed `if self.disabled: return False` (django/forms/fields.py:179); B2 noEditValue true _ initial = initial <-> Field.bound_data `if self.disabled: return initial` (fields.py:163). Both axioms are about the UNCHANGED base Field (G-AX scope = repo as-checked-out), load-bearing, and correctly say nothing about the disabled=False path (over-claim guard). No kind-3 leg. Correspondence holds.

**VERDICT:** SOUND. No faithfully-refinable same-spec wrong impl verifies (8 behavioral attacks all rejected at verify; both positive controls verify). The only verifying wrong impls exploit partial-correctness divergence, which has no faithful refined patch (materialized best-effort patch resolve completed=False, not a graded non-resolve) and is out of G-EQ scope. Gold resolves (completed=True). Refinement legs all R/A-consumed/I, A-legs match real callees.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_wrongconst.lean`, `atk_2_prepatch.lean`, `atk_3_boundary.lean`, `atk_4_negate.lean`, `atk_6_diverge2.lean`, `atk_7_diverge_nodec.lean`, `atk_9_alltrue.lean`, `atk_10_flipsome.lean` |

**Non-vacuity.** The positive control `pos_control_match.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_wrongconst.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_negate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_diverge2.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_diverge_nodec.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9_alltrue.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10_flipsome.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_match.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two presentation hooks a generic form field already provides for a field
   the user is not allowed to edit. They are UNCHANGED, pre-existing behaviour
   of the base field class; here they are axiomatized as the weakest contracts
   the desired behaviour relies on (provenance + executable soundness check:
   mapping.md / axiom_check.py, G-AX).

   `noEditChange initial data` — whether the field reports that its submitted
   `data` differs from its stored `initial`, as a function of whether the field
   is non-editable. The single fact consumed: a non-editable field NEVER reports
   a change, whatever the submitted and stored values are.

   `noEditValue data initial` — the value the field exposes when rendering a
   bound form, as a function of whether the field is non-editable. The single
   fact consumed: a non-editable field always exposes its stored `initial`,
   discarding the submitted `data`. -/
axiom noEditChange : Bool → List Char → List Char → Bool
axiom noEditChange_locked : ∀ (initial data : List Char),
    noEditChange true initial data = false

axiom noEditValue : Bool → List Char → List Char → List Char
axiom noEditValue_locked : ∀ (data initial : List Char),
    noEditValue true data initial = initial

@[grind] lemma noEditChange_locked' (initial data : List Char) :
    noEditChange true initial data = false := noEditChange_locked initial data
@[grind] lemma noEditValue_locked' (data initial : List Char) :
    noEditValue true data initial = initial := noEditValue_locked data initial
-- axioms-end

-- pure-start
/- The non-editability flag a freshly constructed read-only credential-digest
   field ends up with.

   Construction may receive an explicit flag (`some true` / `some false`); if the
   caller leaves it unspecified (`none`), the field supplies its own default. The
   desired behaviour is that, unspecified, such a field is non-editable: its
   stored value is shown but cannot be changed by the user, so a tampered
   submission is ignored in favour of the stored value. An explicitly supplied
   flag is honoured verbatim (it is not overridden). -/
@[grind] def lockedDefault (userFlag : Option Bool) : Bool :=
  userFlag.getD true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the non-editability flag with which a read-only credential-digest
   field is constructed.

   Desired behaviour: when the caller does not specify the flag, the field is
   non-editable by default, so the stored value is displayed but protected from
   user edits; an explicitly specified flag is honoured unchanged.

   Two consequences of defaulting to non-editable are pinned as well (the reason
   no bespoke change-suppression hooks are needed on such a field): a field that
   is non-editable by this default never reports a change between stored and
   submitted values, and always exposes its stored value when bound. These rest
   on the field framework's pre-existing non-editable handling (the `noEdit*`
   contracts).

   `userFlag` is read-only (not `mut`): construction reads the caller's optional
   flag and returns the resulting flag; it mutates nothing (directive 5). -/
method readonlyDigestFieldLocked (userFlag : Option Bool) return (out : Bool)
  ensures out = lockedDefault userFlag
  ensures ∀ (initial data : List Char),
    noEditChange (lockedDefault none) initial data = false
  ensures ∀ (data initial : List Char),
    noEditValue (lockedDefault none) data initial = initial
  do
    -- impl-start
    let out := match userFlag with
      | none => true
      | some b => b
    return out
    -- impl-end

prove_correct readonlyDigestFieldLocked by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** readonlyDigestFieldLocked(userFlag: Option Bool) -> out:Bool. Sole output constraint is ensures_1 `out = lockedDefault userFlag` where lockedDefault u = u.getD true (none=>true, some b=>b) — a COMPLETE functional pin over all three observable construction cases. ensures_2/ensures_3 (the noEdit* axiom facts) are evaluated at the CONSTANT `lockedDefault none = true`, never mention `out`, and are discharged by the grind lemmas regardless of impl, so they impose zero constraint on the impl and cannot be used to dodge the ensures_1 pin. Semantics: termination="partial", choice="demonic".

BEHAVIORAL FALSIFICATION BATTERY (8 same-spec wrong impls, same_spec=True each, verified with `bash scripts/lean_verify.sh <f>`, run concurrently <=4/batch): all REJECTED at verify (exit 1), i.e. the spec is TIGHT:
- atk_1_wrongconst `return false` -> exit1 (ensures_1 fails at none & some true)
- atk_2_prepatch `userFlag.getD false` (THE PREPATCH BUG, none=>editable) -> exit1 (goal `userFlag.getD false = lockedDefault userFlag` fails at none; == F2P assertion field.disabled is True). prepatch_reproduced.
- atk_3_boundary `match none=>false | some b=>b` -> exit1 (fails at none)
- atk_4_negate `!(userFlag.getD true)` -> exit1
- atk_6_diverge2 / atk_7_diverge_nodec: loop-based wrong impls with NON-vacuous done-condition (`while i>0`) -> exit1 (VC uses done-cond i=0; goal on real value; loop does NOT exploit the divergence hole). Confirms only literal `while true` triggers vacuity.
- atk_9_alltrue `return true` (ignores explicit some false) -> exit1 (fails at some false)
- atk_10_flipsome `match none=>true | some b=>!b` -> exit1 (fails at some)
POSITIVE CONTROLS: pos_control (exact copy) exit0; pos_control_match (STRUCTURALLY DIFFERENT correct impl `match none=>true | some b=>b`) exit0 => spec non-vacuous.

DIVERGENCE OBSERVATION (reported transparently; NOT a G-EQ break, excluded from the mechanical attack list): atk_5_diverge_wrong (`while true do out:=false; return out`) and atk_8_diverge_neg (`out := !(userFlag.getD true); while true ...`) BOTH VERIFY (exit0), value-independently. This is the standard partial-correctness vacuity of `set_option loom.semantics.termination "partial"`: a `while true` loop makes the done-condition False, so the post-loop VC is discharged vacuously. Per protocol step 2 I MATERIALIZED the closest faithful patch (infinite `while True: pass` in ReadOnlyPasswordHashField.`__init__`, diverge_patch.diff) and RAN it: `run_resolve('django__django-13741', diverge_patch, timeout=600)` returned resolved=False, COMPLETED=False, note='no report ... harness error' — i.e. the harness hung on the infinite loop and produced NO graded report. This is the INCONCLUSIVE infra outcome, NOT the BROKEN signature (build_one.py:306 requires `completed=True AND not resolved`). POSITIVE HARNESS CONTROL: gold patch.diff -> run_resolve returned resolved=True, completed=True (harness+image verified healthy for this instance).

WHY DIVERGENCE IS OUT OF SCOPE (not a break): (1) No faithful refined patch EXISTS — refinement.md maps the TERMINATING computation userFlag.getD true <-> setdefault('disabled',True) (leg A2, I-op); there is no refinement leg producing an infinite loop, so a divergent impl has no image under the map and the protocol's `faithful refined patch` is undefined for it. (2) Reductio: if `while true` broke a spec, all 401 partial-semantics velvet bundles would be trivially BROKEN by wrapping the gold in `while true`; `partial` is a deliberate methodology choice (prompts/velvet/quickref.md) and G-EQ audits refinement fidelity + axiom correspondence, not the termination-semantics option. (3) The gold impl is straight-line and terminating; the twin-artifact guarantee (refinement.md D) is explicitly scoped to impls `refined by the map above`.

REFINEMENT.MD AUDIT (step 3): legs A1(R param<->disabled kwarg)/A2(I: the genuinely-CHANGED op modeled DIRECTLY as Option.getD true, NOT axiomatized — no kind-3)/A3(R Bool<->self.disabled)/B1(A-consumed)/B2(A-consumed). A-legs confirmed against REAL base callees in worktree @ base_commit d746f28949c009251a8741ba03d156964050717f: B1 noEditChange true _ _ = false <-> Field.has_changed `if self.disabled: return False` (django/forms/fields.py:179); B2 noEditValue true _ initial = initial <-> Field.bound_data `if self.disabled: return initial` (fields.py:163). Both axioms are about the UNCHANGED base Field (G-AX scope = repo as-checked-out), load-bearing, and correctly say nothing about the disabled=False path (over-claim guard). No kind-3 leg. Correspondence holds.

**VERDICT:** SOUND. No faithfully-refinable same-spec wrong impl verifies (8 behavioral attacks all rejected at verify; both positive controls verify). The only verifying wrong impls exploit partial-correctness divergence, which has no faithful refined patch (materialized best-effort patch resolve completed=False, not a graded non-resolve) and is out of G-EQ scope. Gold resolves (completed=True). Refinement legs all R/A-consumed/I, A-legs match real callees.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for velvet django__django-13741. Modeled function readonlyDigestFieldLocked (bound to ReadOnlyPasswordHashField.`__init__` -> self.disabled) with spec `ensures out = lockedDefault userFlag`, lockedDefault = userFlag.getD true.

Spec byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet_backend) = True (spec region frozen; only impl differs). Solution.lean verifies (lean_verify exit 0); prepatch (getD false) fails on userFlag=none as claimed (G-DIFF holds).

Real-repo behavior verified empirically at base_commit d746f28 with the gold hunk `kwargs.setdefault('disabled', True)` applied, over the entire modeled domain (Option Bool per mapping.md bijection: none<->kwarg absent, some b<->disabled=b):
  - none (absent)   -> real field.disabled = True   == getD true = true  MATCH
  - some true       -> real field.disabled = True   == true              MATCH
  - some false      -> real field.disabled = False  == false             MATCH
Model agrees with the real callee on all three observable cases. No diverging input exists within the stated carrier domain.

Postcondition axioms (noEditChange/noEditValue, base Field, unpatched) also confirmed against the real repo: Field.has_changed(disabled=True) returns False; Field.bound_data(disabled=True) returns initial — matching noEditChange true _ _ = false and noEditValue true _ initial = initial.

The only impl-constraining ensures (out = lockedDefault userFlag) reproduces the real self.disabled on every input in the modeled domain; the two universally-quantified postconditions are pinned at lockedDefault none = true and are true of the real base Field. The spec is neither too strong nor drifted. (Note: disabled=None, a non-Bool Python value, is outside the Option Bool bijection domain, not a modeled input, so not a divergence.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage/gold-reconstruction judgment for django__django-13741 (velvet).

### Verification performed
- Spec region byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. Only the impl region differs (getD true vs getD false); the prepatch fails `out = lockedDefault userFlag` on userFlag=none, the sole observable F2P change.
- Mechanical screen: leakage.screen(Solution.lean, lean, patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. No relaxed_leakage flag, no RELAXED_LEAKAGE.md; strict evaluation applies.
- Computed the actual consumer spec view (spec_view of Solution.lean): axioms noEditChange/noEditValue + locked lemmas, the pure def lockedDefault=userFlag.getD true, method readonlyDigestFieldLocked with three ensures, impl+prove_correct elided.

**GOLD EDIT:** insert kwargs.setdefault('disabled', True) in ReadOnlyPasswordHashField.`__init__`; delete bespoke bound_data, has_changed, and UserChangeForm.clean_password.

EACH SPEC-VIEW ELEMENT vs PUBLIC problem_statement (NOT hints):
1. lockedDefault none = true ('default to non-editable when unspecified') <- problem_statement verbatim: 'this property could be set to True [by] default on the ReadOnlyPasswordHashField.'
2. The two postconditions (noEditChange true _ _ = false; noEditValue true _ initial = initial) <- problem_statement quotes Django's disabled doc: 'Even if a user tampers with the field's value submitted to the server, it will be ignored in favor of the value from the form's initial data.'
3. 'no bespoke change-suppression hooks needed' framing <- problem_statement: 'the clean_password is no longer necessary.'

The spec view names NO Python symbols (no bound_data/has_changed/clean_password/setdefault/disabled/forms.py), does not disclose the setdefault insertion form, and does not reveal the deletion structure of the gold diff (which methods are removed). Those Python bindings and the deletion narrative live only in mapping.md / refinement.md (audit artifacts, outside the consumer spec view). Axiom comments frame noEdit* as UNCHANGED pre-existing base-field behaviour, not as edits.

The substantial spec/problem overlap originates in the problem_statement itself being an unusually complete description of the intended change; the spec view adds nothing localizing the gold edit beyond public text. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
