# P2 adversarial audit — django__django-13109

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
None found. Every same-spec wrong impl fails to verify, so there is no closing-proof candidate to materialize into a patch. The prepatch bug itself (atk_1) is refuted by the discriminating input parentLink=false, value=some v, rows=[{key:=v, defaultVisible:=false, limitOk:=true}]: spec requires true (underlying stored eligible record exists) but a default-presentation scan returns false.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     match value with
     | none => return true
     | some v =>
-      let mut qs := rows
+      let mut qs := rows.filter (fun r => r.defaultVisible)
       qs := qs.filter (fun r => r.key == v)
       qs := qs.filter (fun r => r.limitOk)
       return !qs.isEmpty
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,6 @@
     | some v =>
       let mut qs := rows
       qs := qs.filter (fun r => r.key == v)
-      qs := qs.filter (fun r => r.limitOk)
       return !qs.isEmpty
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
       let mut qs := rows
       qs := qs.filter (fun r => r.key == v)
       qs := qs.filter (fun r => r.limitOk)
-      return !qs.isEmpty
+      return qs.length > 1
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
     if parentLink then
       return true
     match value with
-    | none => return true
+    | none => return false
     | some v =>
       let mut qs := rows
       qs := qs.filter (fun r => r.key == v)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,15 +77,7 @@
 def implementation_validateReference
     (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=
   Id.run do
-    if parentLink then
-      return true
-    match value with
-    | none => return true
-    | some v =>
-      let mut qs := rows
-      qs := qs.filter (fun r => r.key == v)
-      qs := qs.filter (fun r => r.limitOk)
-      return !qs.isEmpty
+    return true
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
     | some v =>
       let mut qs := rows
       qs := qs.filter (fun r => r.key == v)
-      qs := qs.filter (fun r => r.limitOk)
+      qs := qs.filter (fun r => r.defaultVisible)
       return !qs.isEmpty
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating a reference from one record to another stored record.

A record may hold a reference (a "foreign key") to a target record of another
kind, identified by a key value. Validation must confirm that the reference is
sound: that some stored target record actually carries that key value (and meets
any standing choice constraint attached to the reference).

The target kind exposes two views of its stored records:

  * a DEFAULT presentation view, which a target kind may narrow with a standing
    filter so that some genuinely-stored records are not presented (for example,
    records flagged as retired); and
  * the UNDERLYING stored collection, which contains every stored record
    irrespective of any such presentation filter.

The desired behavior is that a reference is sound exactly when the UNDERLYING
stored collection contains a record with the referenced key value that also
satisfies the choice constraint — i.e. soundness depends only on whether the
target record genuinely exists and is eligible, never on whether the target
kind's default presentation happens to hide it. Two references need no existence
check at all: a reference that merely links a record to its parent record, and a
reference whose value is absent (null); both are sound outright.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled here — selecting the underlying stored collection rather than the
-- narrowed default presentation, and checking key-and-eligibility membership
-- over it — is modeled structurally over the per-record observables the stored
-- collection already exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A stored target record, paired with the observables the existence check
consults.
* `key` — the record's value for the referenced field (the reference matches a
  record iff this equals the referenced value);
* `defaultVisible` — whether the record survives the target kind's default
  presentation filter (`false` ⇒ genuinely stored but hidden from the default
  presentation view);
* `limitOk` — whether the record satisfies the standing choice constraint
  attached to the reference. -/
structure Row where
  key : Nat
  defaultVisible : Bool
  limitOk : Bool

/-- A reference value `v` is matched by some eligible record in the given
collection: a record whose `key` equals `v` and which satisfies the choice
constraint. -/
def existsValid (v : Nat) (rows : List Row) : Bool :=
  rows.any (fun r => r.key == v && r.limitOk)
-- pure-end

-- post-conditions-start
/-- The soundness verdict is fully pinned by the inputs. A parent-link reference,
or an absent (null) value, is sound outright. Otherwise the reference is sound
exactly when the UNDERLYING stored collection (`rows` in full, independent of
each record's `defaultVisible` presentation flag) contains an eligible record
matching the referenced value. The entire result is determined; no component is
left free. -/
def problem_spec_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row)
    (result : Bool) : Prop :=
  result =
    (if parentLink then true
     else match value with
          | none => true
          | some v => existsValid v rows)
-- post-conditions-end

-- impl-start
def implementation_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=
  Id.run do
    if parentLink then
      return true
    match value with
    | none => return true
    | some v =>
      let mut qs := rows
      qs := qs.filter (fun r => r.key == v)
      qs := qs.filter (fun r => r.limitOk)
      return !qs.isEmpty
-- impl-end

-- proof-start
theorem correct_validateReference :
    ∀ (parentLink : Bool) (value : Option Nat) (rows : List Row),
      problem_spec_validateReference parentLink value rows
        (implementation_validateReference parentLink value rows) := by
  have helper : ∀ (l : List Row) (p : Row → Bool),
      (!(l.filter p).isEmpty) = l.any p := by
    intro l p
    induction l with
    | nil => rfl
    | cons a as ih =>
      simp only [List.filter_cons, List.any_cons]
      by_cases h : p a = true
      · simp [h]
      · simp only [Bool.not_eq_true] at h
        simp [h, ih]
  intro parentLink value rows
  unfold problem_spec_validateReference implementation_validateReference existsValid
  simp only [Id.run, bind, pure]
  cases parentLink <;> simp only [Bool.false_eq_true, if_false, if_true]
  cases value with
  | none => rfl
  | some v =>
    show (!(List.filter (fun r => r.limitOk) (List.filter (fun r => r.key == v) rows)).isEmpty)
        = rows.any (fun r => r.key == v && r.limitOk)
    rw [List.filter_filter, helper]
    have hp : (fun r : Row => r.limitOk && r.key == v)
        = (fun r : Row => r.key == v && r.limitOk) := by
      funext r; rw [Bool.and_comm]
    rw [hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validateReference pins result to EXACT Bool equality with a fully-grounded function: result = (if parentLink then true else match value with | none => true | some v => existsValid v rows), where existsValid quantifies over the FULL rows (ignoring defaultVisible). No output component is free; no ungrounded oracle. Any impl differing on even one input is a false forall, un-dischargeable.

A-LEG AUDIT (focus per instructions): axioms-start/end is EMPTY; grep confirms NO axiom/opaque declarations in Solution.lean. refinement.md legs are all R/I -- no A-consumed, no A-reference, no kind-3. The core fix (_base_manager vs _default_manager, i.e. ignore vs honor defaultVisible) is modeled DEEPLY/structurally as scanning the full rows list, not axiomatized; mapping.md's Row-field bijection (key/defaultVisible/limitOk) to the real callee observables holds. No A-leg correspondence hazard exists to break.

SAME_SPEC: all 6 attacks + pos_control return True under swebench_unified.markers.same_spec (lean). Impl region edited only; axioms/pure/pre/post byte-identical.

### ATTACKS (all carry gold proof; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (filter defaultVisible first) -> exit 1 (unsolved goals; bug reproduced)
- atk_2 drop limitOk filter -> exit 1
- atk_3 boundary: require qs.length > 1 -> exit 1
- atk_4 control-flow effect: null value returns false -> exit 1
- atk_5 ungrounded-oracle echo: constant `return true` -> exit 1
- atk_6 wrong observable: filter defaultVisible instead of limitOk -> exit 1
No wrong impl proof closed => step-2 patch materialization is vacuous (nothing to resolve-run). patches={}.

POSITIVE CONTROL: pos_control.lean verifies, exit 0. #print axioms correct_validateReference => [propext, Quot.sound] (standard only; no sorryAx, no custom axioms). Clean.

No closing clean-axiom wrong impl found across 6 distinct attack classes; A-legs absent so nothing to break there. verify<=>correct holds. VERDICT: SOUND.

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
None found. Every same-spec wrong impl fails to verify, so there is no closing-proof candidate to materialize into a patch. The prepatch bug itself (atk_1) is refuted by the discriminating input parentLink=false, value=some v, rows=[{key:=v, defaultVisible:=false, limitOk:=true}]: spec requires true (underlying stored eligible record exists) but a default-presentation scan returns false.
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
Validating a reference from one record to another stored record.

A record may hold a reference (a "foreign key") to a target record of another
kind, identified by a key value. Validation must confirm that the reference is
sound: that some stored target record actually carries that key value (and meets
any standing choice constraint attached to the reference).

The target kind exposes two views of its stored records:

  * a DEFAULT presentation view, which a target kind may narrow with a standing
    filter so that some genuinely-stored records are not presented (for example,
    records flagged as retired); and
  * the UNDERLYING stored collection, which contains every stored record
    irrespective of any such presentation filter.

The desired behavior is that a reference is sound exactly when the UNDERLYING
stored collection contains a record with the referenced key value that also
satisfies the choice constraint — i.e. soundness depends only on whether the
target record genuinely exists and is eligible, never on whether the target
kind's default presentation happens to hide it. Two references need no existence
check at all: a reference that merely links a record to its parent record, and a
reference whose value is absent (null); both are sound outright.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled here — selecting the underlying stored collection rather than the
-- narrowed default presentation, and checking key-and-eligibility membership
-- over it — is modeled structurally over the per-record observables the stored
-- collection already exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A stored target record, paired with the observables the existence check
consults.
* `key` — the record's value for the referenced field (the reference matches a
  record iff this equals the referenced value);
* `defaultVisible` — whether the record survives the target kind's default
  presentation filter (`false` ⇒ genuinely stored but hidden from the default
  presentation view);
* `limitOk` — whether the record satisfies the standing choice constraint
  attached to the reference. -/
structure Row where
  key : Nat
  defaultVisible : Bool
  limitOk : Bool

/-- A reference value `v` is matched by some eligible record in the given
collection: a record whose `key` equals `v` and which satisfies the choice
constraint. -/
def existsValid (v : Nat) (rows : List Row) : Bool :=
  rows.any (fun r => r.key == v && r.limitOk)
-- pure-end

-- post-conditions-start
/-- The soundness verdict is fully pinned by the inputs. A parent-link reference,
or an absent (null) value, is sound outright. Otherwise the reference is sound
exactly when the UNDERLYING stored collection (`rows` in full, independent of
each record's `defaultVisible` presentation flag) contains an eligible record
matching the referenced value. The entire result is determined; no component is
left free. -/
def problem_spec_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row)
    (result : Bool) : Prop :=
  result =
    (if parentLink then true
     else match value with
          | none => true
          | some v => existsValid v rows)
-- post-conditions-end

-- impl-start
def implementation_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=
  Id.run do
    if parentLink then
      return true
    match value with
    | none => return true
    | some v =>
      let mut qs := rows
      qs := qs.filter (fun r => r.key == v)
      qs := qs.filter (fun r => r.limitOk)
      return !qs.isEmpty
-- impl-end

-- proof-start
theorem correct_validateReference :
    ∀ (parentLink : Bool) (value : Option Nat) (rows : List Row),
      problem_spec_validateReference parentLink value rows
        (implementation_validateReference parentLink value rows) := by
  have helper : ∀ (l : List Row) (p : Row → Bool),
      (!(l.filter p).isEmpty) = l.any p := by
    intro l p
    induction l with
    | nil => rfl
    | cons a as ih =>
      simp only [List.filter_cons, List.any_cons]
      by_cases h : p a = true
      · simp [h]
      · simp only [Bool.not_eq_true] at h
        simp [h, ih]
  intro parentLink value rows
  unfold problem_spec_validateReference implementation_validateReference existsValid
  simp only [Id.run, bind, pure]
  cases parentLink <;> simp only [Bool.false_eq_true, if_false, if_true]
  cases value with
  | none => rfl
  | some v =>
    show (!(List.filter (fun r => r.limitOk) (List.filter (fun r => r.key == v) rows)).isEmpty)
        = rows.any (fun r => r.key == v && r.limitOk)
    rw [List.filter_filter, helper]
    have hp : (fun r : Row => r.limitOk && r.key == v)
        = (fun r : Row => r.key == v && r.limitOk) := by
      funext r; rw [Bool.and_comm]
    rw [hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validateReference pins result to EXACT Bool equality with a fully-grounded function: result = (if parentLink then true else match value with | none => true | some v => existsValid v rows), where existsValid quantifies over the FULL rows (ignoring defaultVisible). No output component is free; no ungrounded oracle. Any impl differing on even one input is a false forall, un-dischargeable.

A-LEG AUDIT (focus per instructions): axioms-start/end is EMPTY; grep confirms NO axiom/opaque declarations in Solution.lean. refinement.md legs are all R/I -- no A-consumed, no A-reference, no kind-3. The core fix (_base_manager vs _default_manager, i.e. ignore vs honor defaultVisible) is modeled DEEPLY/structurally as scanning the full rows list, not axiomatized; mapping.md's Row-field bijection (key/defaultVisible/limitOk) to the real callee observables holds. No A-leg correspondence hazard exists to break.

SAME_SPEC: all 6 attacks + pos_control return True under swebench_unified.markers.same_spec (lean). Impl region edited only; axioms/pure/pre/post byte-identical.

### ATTACKS (all carry gold proof; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (filter defaultVisible first) -> exit 1 (unsolved goals; bug reproduced)
- atk_2 drop limitOk filter -> exit 1
- atk_3 boundary: require qs.length > 1 -> exit 1
- atk_4 control-flow effect: null value returns false -> exit 1
- atk_5 ungrounded-oracle echo: constant `return true` -> exit 1
- atk_6 wrong observable: filter defaultVisible instead of limitOk -> exit 1
No wrong impl proof closed => step-2 patch materialization is vacuous (nothing to resolve-run). patches={}.

POSITIVE CONTROL: pos_control.lean verifies, exit 0. #print axioms correct_validateReference => [propext, Quot.sound] (standard only; no sorryAx, no custom axioms). Clean.

No closing clean-axiom wrong impl found across 6 distinct attack classes; A-legs absent so nothing to break there. verify<=>correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous checks performed: (1) Lean compiles via scripts/lean_verify.sh (exit 0); #print axioms correct_validateReference = [propext, Quot.sound] — genuine proof, no sorryAx. (2) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — spec region byte-identical between gold and prepatch. patch.diff verified worktree: base_commit uses `_default_manager`; patch swaps to `_base_manager` (the one-token fix). Spec models the full-rows (base_manager) existence check, ignoring defaultVisible — faithful to post-patch. (4) limitOk correctly models the unchanged complex_filter(get_limit_choices_to()); applied in both pre/post so non-discriminating. (5) Prepatch models the real bug (rows.filter(·.defaultVisible)) and G-DIFF confirms it fails to verify; discriminating case rows=[{key:=v,defaultVisible:=false,limitOk:=true}] returns false pre-fix, true post-fix — matches FAIL_TO_PASS tests. Spec is neither too strong nor drifting: it pins the output exactly to the real post-patch existence verdict on the modeled domain. Verdict FAITHFUL.

Counterexample / evidence:

```
N/A — no divergence between the modeled function and the real callee on the modeled domain. Within domain the spec (result = if parentLink then true else match value | none => true | some v => rows.any (key==v && limitOk)) reproduces post-patch `ForeignKey.validate` exactly: 120,011-case differential vs an in-process `_base_manager` replica (incl. defaultVisible=False discriminators) yields 0 disagreements.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is a one-token swap _default_manager -> _base_manager in ForeignKey.validate. The PUBLIC problem_statement already discloses the entire fix concretely: it names both _base_manager and _default_manager, explains the default manager hides archived rows while the base manager returns the unfiltered collection, and states verbatim 'the ForeignKey validation should use the _base_manager instead'. The spec view is a strictly more-abstract restatement (DEFAULT presentation view vs UNDERLYING stored collection; soundness depends only on the underlying collection ignoring the defaultVisible flag) and never even names the manager symbols. So the spec discloses nothing beyond problem_statement. Mechanical leakage.screen() PASSES (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier/comment echoing a patched symbol; only changed symbol is 'validate' which is public; no bug/fix narration). same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Proof verified real: lean_verify exit 0; #print axioms correct_validateReference -> [propext, Quot.sound], no sorryAx. Note: leakage judged against problem_statement ONLY, not hints_text (hints also point to the PR/base-manager but are correctly excluded from the screen).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
