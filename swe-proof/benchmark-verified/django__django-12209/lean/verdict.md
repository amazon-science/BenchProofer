# P2 adversarial audit — django__django-12209

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_saveDecision is a total functional pin: both SaveDecision fields are equated to total functions of the 5 boolean inputs over all 32 points, leaving zero degrees of freedom. Any impl that closes correct_saveDecision must agree with gold on all 32 inputs, so it is extensionally identical to gold and resolves. Every divergent wrong impl fails to close at exactly its divergent input; the only non-gold impl that closes (atk_2) is extensionally EQUAL to gold and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,13 +81,8 @@
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
   let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
-  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
+  if (!forced) && isNew && keyHasDefault then
     forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
   let attemptsUpdate := keySet && !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -80,14 +80,7 @@
 -- impl-start
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
-  let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
-  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
-    forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
+  let forced := forceFresh || (!verbatimLoad && isNew && keyHasDefault)
   let attemptsUpdate := keySet && !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,14 +81,9 @@
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
   let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
   if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
     forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
-  let attemptsUpdate := keySet && !forced
+  let attemptsUpdate := keySet || !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,14 +81,9 @@
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
   let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
+  let attemptsUpdate := keySet && !forced
   if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
     forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
-  let attemptsUpdate := keySet && !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,14 +81,9 @@
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
   let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
   if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
     forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
-  let attemptsUpdate := keySet && !forced
+  let attemptsUpdate := keySet
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,14 +80,7 @@
 -- impl-start
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
-  let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
-  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
-    forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
+  let forced := (!verbatimLoad && !forceFresh && isNew && keyHasDefault)
   let attemptsUpdate := keySet && !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,13 +81,8 @@
 def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
     : SaveDecision := Id.run do
   let mut forced := forceFresh
-  -- Skip the update attempt (force a fresh insert) when adding a newly created
-  -- record whose key field has a default — but only for an ordinary save, never
-  -- for a verbatim replay carrying an explicit key.
-  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
+  if (!verbatimLoad) && (!forced) && isNew then
     forced := true
-  -- An in-place update is attempted only when a key value is present and a fresh
-  -- insert is not being forced.
   let attemptsUpdate := keySet && !forced
   return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Routing a single-row persistence operation between two strategies: attempting an
in-place UPDATE of an existing row first, or going straight to a fresh INSERT.

When persisting one record the routine must decide whether to try updating an
existing row before falling back to inserting a new one. Five observable facts
drive the decision:

* whether the caller is replaying records verbatim — e.g. reloading a stored data
  set whose values (including the primary key) are supplied as-is, rather than an
  ordinary application-level save;
* whether the caller has explicitly demanded a fresh insert;
* whether the record is newly created (not yet known to originate from storage);
* whether the record's primary-key field supplies its own default value;
* whether a primary-key value is actually present.

The routine first determines an effective "force a fresh insert" verdict. The
verdict is forced on precisely when EITHER the caller already demanded a fresh
insert, OR all of the following hold together: the operation is an ordinary save
(not a verbatim replay), no fresh insert was already demanded, the record is
newly created, and its primary-key field carries a default. An in-place update is
then attempted exactly when a primary-key value is present AND the effective
verdict does not force a fresh insert.

The decisive subtlety: a verbatim replay must NOT have a fresh insert forced on it
merely because the key field has a default — such a replay carries an explicit key
and should still attempt to update the matching existing row. The behavior is
stated abstractly as an input→output relation; the implementation and correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every fact the decision
-- consults — whether the save is a verbatim replay, whether a fresh insert was
-- demanded, whether the record is new, whether the key field has a default, and
-- whether a key value is present — is supplied as a boolean input, and the
-- routing logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The routing decision for one single-row persistence operation: the effective
verdict on forcing a fresh insert, and whether an in-place update is attempted
first. -/
structure SaveDecision where
  forcesFresh : Bool
  attemptsUpdate : Bool
deriving Repr, DecidableEq

/-- The effective "force a fresh insert" verdict. It is set when the caller
already demanded a fresh insert, or when an ordinary (non-verbatim) save of a
newly created record whose key field has a default has no fresh insert already
demanded. -/
def forcesFreshInsert (verbatimLoad forceFresh isNew keyHasDefault : Bool) : Bool :=
  forceFresh || (!verbatimLoad && !forceFresh && isNew && keyHasDefault)
-- pure-end

-- post-conditions-start
/-- Input→output relation for routing one single-row persistence operation.

Inputs:
* `verbatimLoad`  — the operation is replaying caller-supplied records verbatim;
* `forceFresh`    — the caller explicitly demanded a fresh insert;
* `isNew`         — the record is newly created (not known to come from storage);
* `keyHasDefault` — the primary-key field supplies its own default value;
* `keySet`        — a primary-key value is present.

Both result components are pinned. The effective fresh-insert verdict is exactly
`forcesFreshInsert` of the four routing inputs, and an in-place update is
attempted exactly when a key value is present and the verdict does not force a
fresh insert. Neither component is left free. -/
def problem_spec_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    (result : SaveDecision) : Prop :=
  result.forcesFresh = forcesFreshInsert verbatimLoad forceFresh isNew keyHasDefault ∧
  result.attemptsUpdate = (keySet && !result.forcesFresh)
-- post-conditions-end

-- impl-start
def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    : SaveDecision := Id.run do
  let mut forced := forceFresh
  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
    forced := true
  let attemptsUpdate := keySet && !forced
  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
-- impl-end

-- proof-start
theorem correct_saveDecision :
    ∀ (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool),
      problem_spec_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet
        (implementation_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet) := by
  intro verbatimLoad forceFresh isNew keyHasDefault keySet
  cases verbatimLoad <;> cases forceFresh <;> cases isNew <;>
    cases keyHasDefault <;> cases keySet <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME_SPEC: all 7 attacks + pc = True (axioms/pure/pre/post byte-identical; only impl region edited).

### LEAN_VERIFY (scripts/lean_verify.sh, 300s, run in parallel batches of <=4):
- pc (GOLD positive control): exit 0 (closes). '#print axioms correct_saveDecision' -> 'does not depend on any axioms' (clean).
- atk_1 (PREPATCH BUG, drops !verbatimLoad guard): exit 1 (FAILS to close). Diverges at (verbatimLoad,forceFresh,isNew,keyHasDefault,keySet) e.g. (T,F,T,T,F): impl forcesFresh=T vs gold F. => prepatch_reproduced.
- atk_2 (semantically-equivalent rewrite: forceFresh || (!verbatimLoad && isNew && keyHasDefault), drops redundant !forceFresh): exit 0 (closes). '#print axioms' -> clean, no axioms. Extensionally EQUAL to gold (verified over all 32 tuples in Python). Faithful patch materialized (atk_2.patch) and RUN through official harness run_resolve('django__django-12209') => RESOLVED=True, completed=True, note='resolved', flaky=False. Benign echo, NOT a break.
- atk_3 (BOUNDARY: attemptsUpdate = keySet || !forced): exit 1 (16 divergent inputs).
- atk_4 (CONTROL-FLOW-EFFECT: compute attemptsUpdate before forcing): exit 1 (1 divergent input, (F,F,T,T,T)).
- atk_5 (UNGROUNDED-ORACLE ECHO: attemptsUpdate := keySet, drops !forced): exit 1 (9 divergent inputs).
- atk_6 (drops leading forceFresh short-circuit): exit 1 (16 divergent inputs).
- atk_7 (PARTIAL-DOMAIN: drops keyHasDefault conjunct): exit 1 (2 divergent inputs).

CONCLUSION: 6 genuinely-divergent same-spec wrong impls all fail to close (verify rejects them); the only closing non-gold impl (atk_2) is gold-equivalent and its faithful patch RESOLVES. No closing clean-axiom impl has a faithful patch that does NOT resolve => verify => correct holds.

REFINEMENT.MD AUDIT: all 4 legs tagged I / boolean-R; NO A-legs (no axiomatized callee, G-AX is a legitimate skip stub). The prompt's A-leg / deep-model correspondence focus is moot for this bundle. The R legs collapse Python's two-part keyHasDefault (pk.default truthy AND != NOT_PROVIDED) into one input boolean, faithful and untouched by the patch; every op is a boolean conjunction directly expressible in Lean. No kind-3 (changed-inexpressible) leg. Correspondence to the real _save_table decision block + 'if pk_set and not force_insert' guard holds.

VERDICT: SOUND (>=5 distinct attacks run; positive control + the one closing echo both verified clean-axiom AND resolve; every divergent impl rejected by verify).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_saveDecision is a total functional pin: both SaveDecision fields are equated to total functions of the 5 boolean inputs over all 32 points, leaving zero degrees of freedom. Any impl that closes correct_saveDecision must agree with gold on all 32 inputs, so it is extensionally identical to gold and resolves. Every divergent wrong impl fails to close at exactly its divergent input; the only non-gold impl that closes (atk_2) is extensionally EQUAL to gold and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Routing a single-row persistence operation between two strategies: attempting an
in-place UPDATE of an existing row first, or going straight to a fresh INSERT.

When persisting one record the routine must decide whether to try updating an
existing row before falling back to inserting a new one. Five observable facts
drive the decision:

* whether the caller is replaying records verbatim — e.g. reloading a stored data
  set whose values (including the primary key) are supplied as-is, rather than an
  ordinary application-level save;
* whether the caller has explicitly demanded a fresh insert;
* whether the record is newly created (not yet known to originate from storage);
* whether the record's primary-key field supplies its own default value;
* whether a primary-key value is actually present.

The routine first determines an effective "force a fresh insert" verdict. The
verdict is forced on precisely when EITHER the caller already demanded a fresh
insert, OR all of the following hold together: the operation is an ordinary save
(not a verbatim replay), no fresh insert was already demanded, the record is
newly created, and its primary-key field carries a default. An in-place update is
then attempted exactly when a primary-key value is present AND the effective
verdict does not force a fresh insert.

The decisive subtlety: a verbatim replay must NOT have a fresh insert forced on it
merely because the key field has a default — such a replay carries an explicit key
and should still attempt to update the matching existing row. The behavior is
stated abstractly as an input→output relation; the implementation and correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every fact the decision
-- consults — whether the save is a verbatim replay, whether a fresh insert was
-- demanded, whether the record is new, whether the key field has a default, and
-- whether a key value is present — is supplied as a boolean input, and the
-- routing logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The routing decision for one single-row persistence operation: the effective
verdict on forcing a fresh insert, and whether an in-place update is attempted
first. -/
structure SaveDecision where
  forcesFresh : Bool
  attemptsUpdate : Bool
deriving Repr, DecidableEq

/-- The effective "force a fresh insert" verdict. It is set when the caller
already demanded a fresh insert, or when an ordinary (non-verbatim) save of a
newly created record whose key field has a default has no fresh insert already
demanded. -/
def forcesFreshInsert (verbatimLoad forceFresh isNew keyHasDefault : Bool) : Bool :=
  forceFresh || (!verbatimLoad && !forceFresh && isNew && keyHasDefault)
-- pure-end

-- post-conditions-start
/-- Input→output relation for routing one single-row persistence operation.

Inputs:
* `verbatimLoad`  — the operation is replaying caller-supplied records verbatim;
* `forceFresh`    — the caller explicitly demanded a fresh insert;
* `isNew`         — the record is newly created (not known to come from storage);
* `keyHasDefault` — the primary-key field supplies its own default value;
* `keySet`        — a primary-key value is present.

Both result components are pinned. The effective fresh-insert verdict is exactly
`forcesFreshInsert` of the four routing inputs, and an in-place update is
attempted exactly when a key value is present and the verdict does not force a
fresh insert. Neither component is left free. -/
def problem_spec_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    (result : SaveDecision) : Prop :=
  result.forcesFresh = forcesFreshInsert verbatimLoad forceFresh isNew keyHasDefault ∧
  result.attemptsUpdate = (keySet && !result.forcesFresh)
-- post-conditions-end

-- impl-start
def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    : SaveDecision := Id.run do
  let mut forced := forceFresh
  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
    forced := true
  let attemptsUpdate := keySet && !forced
  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
-- impl-end

-- proof-start
theorem correct_saveDecision :
    ∀ (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool),
      problem_spec_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet
        (implementation_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet) := by
  intro verbatimLoad forceFresh isNew keyHasDefault keySet
  cases verbatimLoad <;> cases forceFresh <;> cases isNew <;>
    cases keyHasDefault <;> cases keySet <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME_SPEC: all 7 attacks + pc = True (axioms/pure/pre/post byte-identical; only impl region edited).

### LEAN_VERIFY (scripts/lean_verify.sh, 300s, run in parallel batches of <=4):
- pc (GOLD positive control): exit 0 (closes). '#print axioms correct_saveDecision' -> 'does not depend on any axioms' (clean).
- atk_1 (PREPATCH BUG, drops !verbatimLoad guard): exit 1 (FAILS to close). Diverges at (verbatimLoad,forceFresh,isNew,keyHasDefault,keySet) e.g. (T,F,T,T,F): impl forcesFresh=T vs gold F. => prepatch_reproduced.
- atk_2 (semantically-equivalent rewrite: forceFresh || (!verbatimLoad && isNew && keyHasDefault), drops redundant !forceFresh): exit 0 (closes). '#print axioms' -> clean, no axioms. Extensionally EQUAL to gold (verified over all 32 tuples in Python). Faithful patch materialized (atk_2.patch) and RUN through official harness run_resolve('django__django-12209') => RESOLVED=True, completed=True, note='resolved', flaky=False. Benign echo, NOT a break.
- atk_3 (BOUNDARY: attemptsUpdate = keySet || !forced): exit 1 (16 divergent inputs).
- atk_4 (CONTROL-FLOW-EFFECT: compute attemptsUpdate before forcing): exit 1 (1 divergent input, (F,F,T,T,T)).
- atk_5 (UNGROUNDED-ORACLE ECHO: attemptsUpdate := keySet, drops !forced): exit 1 (9 divergent inputs).
- atk_6 (drops leading forceFresh short-circuit): exit 1 (16 divergent inputs).
- atk_7 (PARTIAL-DOMAIN: drops keyHasDefault conjunct): exit 1 (2 divergent inputs).

CONCLUSION: 6 genuinely-divergent same-spec wrong impls all fail to close (verify rejects them); the only closing non-gold impl (atk_2) is gold-equivalent and its faithful patch RESOLVES. No closing clean-axiom impl has a faithful patch that does NOT resolve => verify => correct holds.

REFINEMENT.MD AUDIT: all 4 legs tagged I / boolean-R; NO A-legs (no axiomatized callee, G-AX is a legitimate skip stub). The prompt's A-leg / deep-model correspondence focus is moot for this bundle. The R legs collapse Python's two-part keyHasDefault (pk.default truthy AND != NOT_PROVIDED) into one input boolean, faithful and untouched by the patch; every op is a boolean conjunction directly expressible in Lean. No kind-3 (changed-inexpressible) leg. Correspondence to the real _save_table decision block + 'if pk_set and not force_insert' guard holds.

VERDICT: SOUND (>=5 distinct attacks run; positive control + the one closing echo both verified clean-axiom AND resolve; every divergent impl rejected by verify).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec with LeanBackend.language = True). Solution.lean compiles via lean_verify.sh (exit 0), and `#print axioms correct_saveDecision` reports 'does not depend on any axioms' (no sorryAx; proof is a genuine finite `cases <;> exact ⟨rfl,rfl⟩`).

Verified against the real callee at base_commit 5a68f024987e6d16c2626a31bf653a2edddea579 (git worktree of). Patched `Model._save_table` (django/db/models/base.py:849-860) computes post-block force_insert = force_insert OR (not raw and not force_insert and self._state.adding and self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED), and the update-attempt guard `pk_set and not force_insert`. Confirmed the base commit lacks `not raw` and patch.diff adds exactly that conjunct.

Mapping: verbatimLoad↔raw, forceFresh↔force_insert, isNew↔self._state.adding, keyHasDefault↔(bool(pk.default) and pk.default is not NOT_PROVIDED), keySet↔pk_set. Under this mapping the model's forcesFreshInsert v f n k = f || (!v && !f && n && k) and attemptsUpdate = keySet && !forcesFresh are the exact same boolean expressions as the patched code. The keyHasDefault two-part collapse is faithful — decision consumes only its truth value and the patch does not alter that computation. Downstream callees (_do_update/_do_insert/get_pk_value_on_save) are outside the modeled decision boundary and correctly summarized by keySet.

G-CONF (conformance_check.py) run: 32-point exhaustive + 1e5 fuzz vs gold oracle = 0 disagreements. The spec is a total functional pin over 5 booleans; it is not too strong — it matches the patched callee on every one of the 32 input tuples. No diverging input exists.

Verdict: FAITHFUL (no defect).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical + semantic review of the lean spec view for django__django-12209.

Mechanical checks (all PASS):
- leakage.screen(): passed=True, zero hard failures.
- Gold changed line 'not raw and' NOT reproduced in spec view; changed file path 'django/db/models/base.py' NOT present; changed symbol 'save_table' NOT embedded in any spec-view identifier nor named in comments.
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True: axioms/pure/post-conditions regions byte-identical (only impl/proof differ).

Semantic judgment (the substantive question G-PANEL-3 must decide):
The gold edit adds the conjunct `not raw and` to the force-insert block, keying the fix off the verbatim-replay / fixture-loading (`raw`) dimension. The spec models this as the `verbatimLoad` input inside `forcesFreshInsert` and states the 'decisive subtlety' that a verbatim replay carrying an explicit key must still attempt an UPDATE.

Provenance check — is this beyond the public problem_statement?
- The public problem_statement explicitly surfaces the loaddata/fixture-replay-with-explicit-pk scenario as the broken, behavior-to-preserve case: 'side effect of changing the behaviour of the loaddata management command when the fixture contains explicit pk values and the objects already exist (e.g. when loading the fixture multiple times).' So the verbatim-replay dimension the spec abstracts as `verbatimLoad` is squarely public.
- The problem_statement also states the desired direction ('only change the behaviour if an explicit pk value was not set').
- The distinctive `raw`/'branch off raw ... serialization framework' wording lives in hints_text, and the spec does NOT echo it: no `raw`, no file/line, no 'one-line change', and it does not reproduce the hints' proposed pk_set-based alternative fix.

The spec's framing (fix keyed on verbatim replay rather than merely pk presence) is reconstructable from the public loaddata disclosure, not dependent on the private hints. The spec exposes no gold-diff literal, path, or hints-only content. Information disclosed <= public problem_statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
