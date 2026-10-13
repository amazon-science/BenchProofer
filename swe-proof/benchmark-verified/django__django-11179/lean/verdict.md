# P2 adversarial audit — django__django-11179

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,11 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
     if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
-      return ([(label, [{ inst with pk := none }])], directCount)
+      return ([(label, [inst])], directCount)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
   return (clearAllPks data, generalTotal)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,12 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
     if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
-      return ([(label, [{ inst with pk := none }])], directCount)
+      return ([(label, [{ inst with pk := none }])], generalTotal)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
-  return (clearAllPks data, generalTotal)
+  return (clearAllPks data, directCount)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,11 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
     if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
-      return ([(label, [{ inst with pk := none }])], directCount)
+      return ([(label, [{ inst with pk := none }])], generalTotal)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
   return (clearAllPks data, generalTotal)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,6 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
-  match data with
-  | [(label, [inst])] =>
-    if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
-      return ([(label, [{ inst with pk := none }])], directCount)
-  | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
   return (clearAllPks data, generalTotal)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,15 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
     if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
       return ([(label, [{ inst with pk := none }])], directCount)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
-  return (clearAllPks data, generalTotal)
+  -- clear only the head group, leave the rest stale
+  match data with
+  | [] => return ([], generalTotal)
+  | g :: rest => return ((g.1, g.2.map (fun i => { i with pk := none })) :: rest, generalTotal)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,10 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
-    if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
       return ([(label, [{ inst with pk := none }])], directCount)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
   return (clearAllPks data, generalTotal)
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,11 @@
 def implementation_delete
     (data : List RecGroup) (directlyDeletable : Instance → Bool)
     (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
-  -- Optimize for the case with a single collected record and no dependents.
   match data with
   | [(label, [inst])] =>
     if directlyDeletable inst then
-      -- Remove the one record directly, clear its now-stale key, and return early.
-      return ([(label, [{ inst with pk := none }])], directCount)
+      return ([(label, [{ inst with pk := some 0 }])], directCount)
   | _ => pure ()
-  -- General path: after removal, clear every collected record's key.
   return (clearAllPks data, generalTotal)
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Removing a batch of collected records and reporting how many were removed.

The records to remove are organized into groups (one group per kind of record);
each record carries a single observable field: its primary-key identity, which is
either present (the record currently lives in the store under that key) or absent
(the record has no key, i.e. it does not correspond to any stored row).

Removal has TWO observable outcomes:

  * a count of how many rows were removed, and
  * a side effect on every removed record: once a record has been removed, it no
    longer corresponds to any stored row, so its primary-key identity must be
    cleared (made absent). This must hold for EVERY removed record, in every
    group — there is no record that is removed yet keeps a stale key.

There is a fast path for the smallest possible job — a single group holding a
single record that has no dependents and so can be removed by one direct
operation — and a general path for everything else. The reported count differs
between the two paths (each path tallies removals its own way), but the
key-clearing outcome is identical: after removal, no removed record retains a
key.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Whether the smallest job
-- qualifies for the direct single-record removal is an unchanged decision left
-- as the universally-quantified predicate `directlyDeletable` (the spec holds
-- for every such predicate). The two removal tallies are likewise the unchanged
-- counting machinery, taken as the parameters `directCount` / `generalTotal`.
-- The key-clearing side effect (the modeled behavior) is spelled out structurally
-- by `clearAllPks`, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A removed record, restricted to its single touched field: the primary-key
identity, `some v` when a key value `v` is present and `none` when absent. -/
structure Instance where
  pk : Option Int
deriving DecidableEq

/-- A group label (one per kind of record). Identity only; never compared. -/
abbrev Label := Nat

/-- One group: a label paired with the list of records collected under it. -/
abbrev RecGroup := Label × List Instance

/-- Clear the primary-key identity of every record in every group: each removed
record's key is made absent, every group's label and shape preserved. -/
def clearAllPks (data : List RecGroup) : List RecGroup :=
  data.map (fun g => (g.1, g.2.map (fun i => { i with pk := none })))

/-- Whether the job is the smallest possible one eligible for the direct
single-record removal: exactly one group holding exactly one record, and that
record qualifies for direct removal. -/
def isSingleFast (data : List RecGroup) (directlyDeletable : Instance → Bool) : Bool :=
  match data with
  | [(_, [inst])] => directlyDeletable inst
  | _ => false
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * the record groups are exactly the input groups with every record's key
    cleared (`clearAllPks data`) — identical whether the fast path or the general
    path was taken, so no removed record keeps a key; and
  * the reported count is the direct tally on the fast path and the general tally
    otherwise.

No output component is left free: the group structure is pinned to
`clearAllPks data`, and the count is pinned to the branch-selected tally. -/
def problem_spec_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int)
    (result : (List RecGroup) × Int) : Prop :=
  result.1 = clearAllPks data ∧
  result.2 = (if isSingleFast data directlyDeletable then directCount else generalTotal)
-- post-conditions-end

-- impl-start
def implementation_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
  -- Optimize for the case with a single collected record and no dependents.
  match data with
  | [(label, [inst])] =>
    if directlyDeletable inst then
      -- Remove the one record directly, clear its now-stale key, and return early.
      return ([(label, [{ inst with pk := none }])], directCount)
  | _ => pure ()
  -- General path: after removal, clear every collected record's key.
  return (clearAllPks data, generalTotal)
-- impl-end

-- proof-start
theorem correct_delete :
    ∀ (data : List RecGroup) (directlyDeletable : Instance → Bool)
      (directCount generalTotal : Int),
      problem_spec_delete data directlyDeletable directCount generalTotal
        (implementation_delete data directlyDeletable directCount generalTotal) := by
  intro data directlyDeletable directCount generalTotal
  unfold implementation_delete problem_spec_delete isSingleFast
  match data with
  | [(label, [inst])] =>
    by_cases h : directlyDeletable inst <;> simp [clearAllPks, h]
  | [] => simp [clearAllPks]
  | (label, []) :: rest => simp [clearAllPks]
  | (label, inst1 :: inst2 :: more) :: rest => simp [clearAllPks]
  | g1 :: g2 :: rest => simp [clearAllPks]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11179 (lean). VERDICT: SOUND.

SPEC SHAPE: problem_spec_delete pins BOTH output components as total functions of the inputs: result.1 = clearAllPks data (UNCONDITIONALLY, on every path) and result.2 = (if isSingleFast data directlyDeletable then directCount else generalTotal). Because both outputs are fully pinned, any impl not extensionally equal to this function makes correct_delete a FALSE proposition, so by Lean soundness no honest proof can close. This is the strongest possible spec shape for equivalence.

same_spec MECHANICS: markers.same_spec elides the impl AND proof regions (incl. the theorem header). A faithful attack therefore keeps axioms/pure/pre/post byte-identical AND keeps the honest theorem 'forall ..., problem_spec_delete ... (implementation_delete ...)' unchanged (adversary.check_attack re-runs the file as-submitted with the gold theorem), editing only the impl body. All 7 attacks confirmed same_spec=True.

### ATTACK BATTERY (all edit only the impl body; each is genuinely != the pinned spec function on some input):
- atk_1  PREPATCH BUG: fast path returns [(label,[inst])] WITHOUT pk clear (stale key). Code-identical to Solution_prepatch.lean impl (only comments differ). Exit 1, 'unsolved goals' at correct_delete.
- atk_2  SWAPPED COUNTS: fast path returns generalTotal, general returns directCount. Exit 1.
- atk_3  CONTROL-FLOW-EFFECT: fast path clears pk correctly but returns generalTotal instead of directCount (wrong branch count). Exit 1.
- atk_4  UNGROUNDED-ORACLE ECHO: drops the branch entirely, always (clearAllPks data, generalTotal); wrong count on the fast path. Exit 1.
- atk_5  PARTIAL-DOMAIN pk clear: general path clears pk only in the HEAD group, leaves the rest stale. Exit 1.
- atk_6  BOUNDARY/off-by: fast branch taken structurally regardless of directlyDeletable (returns directCount even when directlyDeletable=false, where spec demands generalTotal). Exit 1.
- atk_7  WRONG SIDE-EFFECT VALUE: fast path sets pk := some 0 instead of none. Exit 1.

### Commands
  bash scripts/lean_verify.sh <atk_N.lean>   (run concurrently, <=4 at a time)
RESULTS: atk_1..atk_7 ALL exit 1 (genuine 'unsolved goals' at correct_delete:105 — the pinned postcondition rejects each wrong impl). NO attack verifies, so NONE closes with clean axioms; per protocol step 2 there is no verifying attack requiring a materialized faithful patch + run_resolve. patches={} accordingly.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim, exit 0 (verifies, no sorry). #print axioms correct_delete => [propext, Quot.sound] subset of STANDARD_AXIOMS (propext, Classical.choice, Quot.sound) — clean, no sorryAx.

REFINEMENT.md A-LEG AUDIT (R/I mechanically covered by G-CONF; focus on A legs + correspondence):
- All legs tagged R / A-reference / I. No forbidden kind-3 leg; no A-consumed leg (consistent with meta.json axioms=[]; no opaque/axiom in Solution.lean; axiom_check.py is a skip stub).
- can_fast_delete (deletion.py:158, UNCHANGED) -> directlyDeletable : Instance -> Bool, universally quantified A-reference. FAITHFUL: verified against base repo delete() — its decision depends on model relations, not the instance pk, and the spec holds for EVERY predicate, so the impl cannot cheat through it (the branch-count is pinned for both truth values of the predicate; atk_6 confirms a predicate-ignoring impl is rejected).
- delete_batch count -> directCount ; sum(deleted_counter.values()) -> generalTotal: A-reference numerals fed IDENTICALLY to both legs (confirmed in conformance_check.py). FAITHFUL. atk_2/atk_3 confirm mis-assigning these is rejected.
- The FIX (setattr(instance, pk.attname, None) added at deletion.py:280 on the fast path) and the general-path clear loop (deletion.py:324-326) are modeled DEEPLY (pk := none / clearAllPks), NOT axiomatized — correct per SPEC_GUIDE §3 (changed op must not be axiomatized). atk_1 (no clear) and atk_7 (wrong value) confirm the deep model rejects an unfaithful side effect.
- result.1 = clearAllPks data unconditionally is faithful: verified against base delete() — the fast path fires only for single-group/single-record, where clearAllPks clears exactly that one instance's pk, matching the patched fast-path setattr; the general path clears all, matching the loop. atk_5 (partial clear) is rejected.

CONCLUSION: The A-reference legs' correspondence to the real callees holds; the changed operation is deeply modeled; both spec outputs are totally pinned. 7 distinct same-spec wrong impls (prepatch bug + swapped-count + control-flow + ungrounded-oracle echo + partial-domain + boundary + wrong-value) ALL fail verification with genuine unsolved goals; positive control verifies with clean axioms. verify=>correct holds. No verifying attack exists to route through run_resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Removing a batch of collected records and reporting how many were removed.

The records to remove are organized into groups (one group per kind of record);
each record carries a single observable field: its primary-key identity, which is
either present (the record currently lives in the store under that key) or absent
(the record has no key, i.e. it does not correspond to any stored row).

Removal has TWO observable outcomes:

  * a count of how many rows were removed, and
  * a side effect on every removed record: once a record has been removed, it no
    longer corresponds to any stored row, so its primary-key identity must be
    cleared (made absent). This must hold for EVERY removed record, in every
    group — there is no record that is removed yet keeps a stale key.

There is a fast path for the smallest possible job — a single group holding a
single record that has no dependents and so can be removed by one direct
operation — and a general path for everything else. The reported count differs
between the two paths (each path tallies removals its own way), but the
key-clearing outcome is identical: after removal, no removed record retains a
key.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Whether the smallest job
-- qualifies for the direct single-record removal is an unchanged decision left
-- as the universally-quantified predicate `directlyDeletable` (the spec holds
-- for every such predicate). The two removal tallies are likewise the unchanged
-- counting machinery, taken as the parameters `directCount` / `generalTotal`.
-- The key-clearing side effect (the modeled behavior) is spelled out structurally
-- by `clearAllPks`, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A removed record, restricted to its single touched field: the primary-key
identity, `some v` when a key value `v` is present and `none` when absent. -/
structure Instance where
  pk : Option Int
deriving DecidableEq

/-- A group label (one per kind of record). Identity only; never compared. -/
abbrev Label := Nat

/-- One group: a label paired with the list of records collected under it. -/
abbrev RecGroup := Label × List Instance

/-- Clear the primary-key identity of every record in every group: each removed
record's key is made absent, every group's label and shape preserved. -/
def clearAllPks (data : List RecGroup) : List RecGroup :=
  data.map (fun g => (g.1, g.2.map (fun i => { i with pk := none })))

/-- Whether the job is the smallest possible one eligible for the direct
single-record removal: exactly one group holding exactly one record, and that
record qualifies for direct removal. -/
def isSingleFast (data : List RecGroup) (directlyDeletable : Instance → Bool) : Bool :=
  match data with
  | [(_, [inst])] => directlyDeletable inst
  | _ => false
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * the record groups are exactly the input groups with every record's key
    cleared (`clearAllPks data`) — identical whether the fast path or the general
    path was taken, so no removed record keeps a key; and
  * the reported count is the direct tally on the fast path and the general tally
    otherwise.

No output component is left free: the group structure is pinned to
`clearAllPks data`, and the count is pinned to the branch-selected tally. -/
def problem_spec_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int)
    (result : (List RecGroup) × Int) : Prop :=
  result.1 = clearAllPks data ∧
  result.2 = (if isSingleFast data directlyDeletable then directCount else generalTotal)
-- post-conditions-end

-- impl-start
def implementation_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
  -- Optimize for the case with a single collected record and no dependents.
  match data with
  | [(label, [inst])] =>
    if directlyDeletable inst then
      -- Remove the one record directly, clear its now-stale key, and return early.
      return ([(label, [{ inst with pk := none }])], directCount)
  | _ => pure ()
  -- General path: after removal, clear every collected record's key.
  return (clearAllPks data, generalTotal)
-- impl-end

-- proof-start
theorem correct_delete :
    ∀ (data : List RecGroup) (directlyDeletable : Instance → Bool)
      (directCount generalTotal : Int),
      problem_spec_delete data directlyDeletable directCount generalTotal
        (implementation_delete data directlyDeletable directCount generalTotal) := by
  intro data directlyDeletable directCount generalTotal
  unfold implementation_delete problem_spec_delete isSingleFast
  match data with
  | [(label, [inst])] =>
    by_cases h : directlyDeletable inst <;> simp [clearAllPks, h]
  | [] => simp [clearAllPks]
  | (label, []) :: rest => simp [clearAllPks]
  | (label, inst1 :: inst2 :: more) :: rest => simp [clearAllPks]
  | g1 :: g2 :: rest => simp [clearAllPks]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11179 (lean). VERDICT: SOUND.

SPEC SHAPE: problem_spec_delete pins BOTH output components as total functions of the inputs: result.1 = clearAllPks data (UNCONDITIONALLY, on every path) and result.2 = (if isSingleFast data directlyDeletable then directCount else generalTotal). Because both outputs are fully pinned, any impl not extensionally equal to this function makes correct_delete a FALSE proposition, so by Lean soundness no honest proof can close. This is the strongest possible spec shape for equivalence.

same_spec MECHANICS: markers.same_spec elides the impl AND proof regions (incl. the theorem header). A faithful attack therefore keeps axioms/pure/pre/post byte-identical AND keeps the honest theorem 'forall ..., problem_spec_delete ... (implementation_delete ...)' unchanged (adversary.check_attack re-runs the file as-submitted with the gold theorem), editing only the impl body. All 7 attacks confirmed same_spec=True.

### ATTACK BATTERY (all edit only the impl body; each is genuinely != the pinned spec function on some input):
- atk_1  PREPATCH BUG: fast path returns [(label,[inst])] WITHOUT pk clear (stale key). Code-identical to Solution_prepatch.lean impl (only comments differ). Exit 1, 'unsolved goals' at correct_delete.
- atk_2  SWAPPED COUNTS: fast path returns generalTotal, general returns directCount. Exit 1.
- atk_3  CONTROL-FLOW-EFFECT: fast path clears pk correctly but returns generalTotal instead of directCount (wrong branch count). Exit 1.
- atk_4  UNGROUNDED-ORACLE ECHO: drops the branch entirely, always (clearAllPks data, generalTotal); wrong count on the fast path. Exit 1.
- atk_5  PARTIAL-DOMAIN pk clear: general path clears pk only in the HEAD group, leaves the rest stale. Exit 1.
- atk_6  BOUNDARY/off-by: fast branch taken structurally regardless of directlyDeletable (returns directCount even when directlyDeletable=false, where spec demands generalTotal). Exit 1.
- atk_7  WRONG SIDE-EFFECT VALUE: fast path sets pk := some 0 instead of none. Exit 1.

### Commands
  bash scripts/lean_verify.sh <atk_N.lean>   (run concurrently, <=4 at a time)
RESULTS: atk_1..atk_7 ALL exit 1 (genuine 'unsolved goals' at correct_delete:105 — the pinned postcondition rejects each wrong impl). NO attack verifies, so NONE closes with clean axioms; per protocol step 2 there is no verifying attack requiring a materialized faithful patch + run_resolve. patches={} accordingly.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim, exit 0 (verifies, no sorry). #print axioms correct_delete => [propext, Quot.sound] subset of STANDARD_AXIOMS (propext, Classical.choice, Quot.sound) — clean, no sorryAx.

REFINEMENT.md A-LEG AUDIT (R/I mechanically covered by G-CONF; focus on A legs + correspondence):
- All legs tagged R / A-reference / I. No forbidden kind-3 leg; no A-consumed leg (consistent with meta.json axioms=[]; no opaque/axiom in Solution.lean; axiom_check.py is a skip stub).
- can_fast_delete (deletion.py:158, UNCHANGED) -> directlyDeletable : Instance -> Bool, universally quantified A-reference. FAITHFUL: verified against base repo delete() — its decision depends on model relations, not the instance pk, and the spec holds for EVERY predicate, so the impl cannot cheat through it (the branch-count is pinned for both truth values of the predicate; atk_6 confirms a predicate-ignoring impl is rejected).
- delete_batch count -> directCount ; sum(deleted_counter.values()) -> generalTotal: A-reference numerals fed IDENTICALLY to both legs (confirmed in conformance_check.py). FAITHFUL. atk_2/atk_3 confirm mis-assigning these is rejected.
- The FIX (setattr(instance, pk.attname, None) added at deletion.py:280 on the fast path) and the general-path clear loop (deletion.py:324-326) are modeled DEEPLY (pk := none / clearAllPks), NOT axiomatized — correct per SPEC_GUIDE §3 (changed op must not be axiomatized). atk_1 (no clear) and atk_7 (wrong value) confirm the deep model rejects an unfaithful side effect.
- result.1 = clearAllPks data unconditionally is faithful: verified against base delete() — the fast path fires only for single-group/single-record, where clearAllPks clears exactly that one instance's pk, matching the patched fast-path setattr; the general path clears all, matching the loop. atk_5 (partial clear) is rejected.

CONCLUSION: The A-reference legs' correspondence to the real callees holds; the changed operation is deeply modeled; both spec outputs are totally pinned. 7 distinct same-spec wrong impls (prepatch bug + swapped-count + control-flow + ungrounded-oracle echo + partial-domain + boundary + wrong-value) ALL fail verification with genuine unsolved goals; positive control verifies with clean axioms. verify=>correct holds. No verifying attack exists to route through run_resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-11179 lean bundle. No divergence found between the modeled function (problem_spec_delete / implementation_delete) and the real Collector.delete at base_commit 19fc6376.

MECHANICAL: same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with LeanBackend.language tables — spec region (imports/pure/post-conditions incl. structure Instance, clearAllPks, isSingleFast, problem_spec_delete) is byte-identical; only impl+proof regions differ. Solution.lean compiles clean (lean_verify exit 0, no sorry). #print axioms correct_delete = [propext, Quot.sound] only — no sorryAx, proof is genuine.

FAITHFULNESS: Spec pins two observables: result.1 = clearAllPks data (pk cleared on BOTH paths — the fix), result.2 = branch-selected tally.
- Fast-path predicate isSingleFast (one group/one record/directlyDeletable) coincides exactly with real `len(self.data)==1 and len(instances)==1 and can_fast_delete`: when len(self.data)==1 the sort loop leaves `instances` = that group's list, so conditions align; multi-group/empty correctly short-circuit to general path (len(self.data)==1 guards before len(instances), so empty data is safe).
- pk-clearing: post-patch fast path setattr(instance,pk,None) + general-path unconditional loop both match clearAllPks. Instance sort/reverse in real code is not observable since all pks collapse to None (permutation-invariant).
- directCount/generalTotal are universally-quantified A-reference parameters standing for delete_batch / sum(counter); the spec holds for the real numeral by instantiation — this GENERALIZES, does not over-strengthen. This is the opposite of a spec-too-strong defect.
- conformance_check.py oracle faithfully replicates post-patch delete at the same abstraction; oracle and shadow legs structurally match the spec branch selection.

Tried to over-strengthen along count, ordering, empty-data, and branch-selection axes; every candidate input agrees. No diverging input exists. Spec is FAITHFUL (and appropriately abstract, not too strong).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: add `setattr(instance, model._meta.pk.attname, None)` in Collector.delete's single-object/no-dependency fast branch, clearing the removed instance's PK before the early return. The PUBLIC problem_statement already discloses this fully: 'delete() on instances of models without any dependencies doesn't clear PKs. ... It should be set to None after .delete() call. See ...deletion:276-281. Should update the model line 280.' So the required correct behavior (PK cleared even on the no-dependency path) is public.

Spec-view derivation verified faithful: markers.spec_view(Solution.lean, LeanBackend.language) sha256 = 60165d112bcfe47e7269f4a577c4d027353d977c6a9ed13073fa12a2a846f015, byte-identical to the recorded G-HYGIENE spec_view hash. same_spec(Solution.lean, Solution_prepatch.lean)=True and spec signatures equal -> spec region is byte-identical across the pre/post pair; only impl differs. impl and proof regions are elided to placeholders in the spec view (confirmed), so no leakage via impl/proof.

The post-conditions region pins `result.1 = clearAllPks data` unconditionally with prose that the key-clearing outcome is identical on both paths. This is the specification of the intended correct post-condition -- exactly the behavior the public problem_statement demands (PK set to None after delete regardless of path). Encoding the required correct behavior in a spec is expected and does not constitute leakage beyond problem_statement.

Lexical scan of the spec view for gold-patch specifics found NONE: no `setattr`, `can_fast_delete`, `delete_batch`, `DeleteQuery`, `_meta`, `attname`, `deletion.py`, line `280`, `transaction`, `mark_for_rollback`, `self.data`. All modeling is abstract (clearAllPks, directlyDeletable, directCount/generalTotal), disclosing no concrete mechanism, file, or line. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
