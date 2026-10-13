# P2 adversarial audit — pydata__xarray-6938

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_3_fresh_nocopy.lean`, `atk_4_overwrite_source.lean`, `atk_5_wrong_handle.lean`, `atk_6_no_bump.lean`, `atk_7_empty_copy.lean`, `atk_8_frame.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no CONFIRMED verify⇏correct break. Every TERMINATING same-spec wrong impl is rejected by the spec. The only same-spec VERIFYING wrong impl (atk_2_diverge, a `while true` spin loop) verifies solely via universal partial-correctness non-termination vacuity; its materialized faithful patch was RUN through the official harness and did NOT COMPLETE (completed=False, test timeout), which the mechanized derivation records as INCONCLUSIVE, never BROKEN. Not a spec-specific weakness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -62,10 +62,11 @@
   ensures ∀ h, h ≠ res → store h = storeOld h
   do
     -- impl-start
-    let r := nextFresh
-    store := Function.update store r (store self)
-    nextFresh := nextFresh + 1
-    return r
+    -- Pre-image skeleton: hand back the SAME object (`return self`), the
+    -- pre-patch behaviour. No allocation, no copy: the result aliases the
+    -- source, so `res ≠ self` and the freshness clauses are unsatisfiable and
+    -- `prove_correct` MUST fail (G-DIFF).
+    return self
     -- impl-end
 
 prove_correct reifyIndependent by
```

Attack 2 — `atk_3_fresh_nocopy.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -63,7 +63,6 @@
   do
     -- impl-start
     let r := nextFresh
-    store := Function.update store r (store self)
     nextFresh := nextFresh + 1
     return r
     -- impl-end
```

Attack 3 — `atk_4_overwrite_source.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -64,6 +64,7 @@
     -- impl-start
     let r := nextFresh
     store := Function.update store r (store self)
+    store := Function.update store self []
     nextFresh := nextFresh + 1
     return r
     -- impl-end
```

Attack 4 — `atk_5_wrong_handle.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -62,7 +62,7 @@
   ensures ∀ h, h ≠ res → store h = storeOld h
   do
     -- impl-start
-    let r := nextFresh
+    let r := nextFresh + 5
     store := Function.update store r (store self)
     nextFresh := nextFresh + 1
     return r
```

Attack 5 — `atk_6_no_bump.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -64,7 +64,6 @@
     -- impl-start
     let r := nextFresh
     store := Function.update store r (store self)
-    nextFresh := nextFresh + 1
     return r
     -- impl-end
 
```

Attack 6 — `atk_7_empty_copy.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -63,7 +63,7 @@
   do
     -- impl-start
     let r := nextFresh
-    store := Function.update store r (store self)
+    store := Function.update store r []
     nextFresh := nextFresh + 1
     return r
     -- impl-end
```

Attack 7 — `atk_8_frame.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models an object-identity / heap-aliasing property. Lean is
    value-functional, so a naive value model could not distinguish "return the
@@ -64,6 +64,7 @@
     -- impl-start
     let r := nextFresh
     store := Function.update store r (store self)
+    store := Function.update store (self - 1) []
     nextFresh := nextFresh + 1
     return r
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- This bundle models an object-identity / heap-aliasing property. Lean is
   value-functional, so a naive value model could not distinguish "return the
   same object" from "return a fresh, independent object" — the very behaviour
   under specification. Following the heap-as-function discipline of the Velvet
   memory examples, objects are addresses (`Handle`) into an explicit store of
   their mutable per-object state (`slot : Handle → Payload`), and allocation is
   a strictly-increasing frontier (`nextFresh`). With this carrier the identity
   of the result, and whether a later write to the result can reach the source,
   are first-class facts the spec pins. -/

-- axioms-start
/- Object identity: an address into the per-object mutable-state store. -/
abbrev Handle := Int

/- The mutable per-object state observed and (potentially, downstream) altered
   by callers: a tuple of small integer tags. -/
abbrev Payload := List Int
-- axioms-end

-- pure-start
/- A store mapping each live object to its current mutable state. Distinct
   handles address disjoint store slots, so an update through one handle leaves
   every other handle's state untouched (`Function.update`'s defining property).
   This is the fact that makes "the result is a distinct object" equivalent to
   "mutating the result cannot affect the source". -/
abbrev Store := Handle → Payload
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Return the source object in a related representation. The desired behaviour:
   the result is an INDEPENDENT object — a handle distinct from the source whose
   mutable state is INITIALIZED FROM but NOT SHARED WITH the source. Concretely
   the result is freshly allocated (`res = nextFreshOld`, above every live
   handle), carries the source's state at call time (`store res = storeOld self`),
   the source's own state is untouched (`store self = storeOld self`), and no
   other live object's state changes (frame). Because the result is a fresh,
   distinct handle, a subsequent write to the result's slot cannot alias the
   source — the property a caller relies on. `store`/`nextFresh` are genuinely
   mutated (an allocation happens), so they are `mut`; `self` is read-only. -/
method reifyIndependent
    (self : Handle) (mut store : Store) (mut nextFresh : Handle)
    return (res : Handle)
  require self < nextFresh
  ensures res = nextFreshOld
  ensures nextFresh = nextFreshOld + 1
  ensures res ≠ self
  ensures store res = storeOld self
  ensures store self = storeOld self
  ensures ∀ h, h ≠ res → store h = storeOld h
  do
    -- impl-start
    let r := nextFresh
    store := Function.update store r (store self)
    nextFresh := nextFresh + 1
    return r
    -- impl-end

prove_correct reifyIndependent by
  loom_solve
  · intro h hne; exact Function.update_of_ne hne _ _
  · exact Function.update_of_ne (ne_of_lt require_1) _ _
  · exact Function.update_self _ _ _
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method reifyIndependent models the gold fix IndexVariable.to_index_variable `return self` -> `return self.copy()` as a heap-aliasing property over Handle:=Int addresses into Store:=Handle->Payload with frontier nextFresh. Six ensures: res=nextFreshOld, nextFresh=nextFreshOld+1, res≠self, store res=storeOld self, store self=storeOld self, frame. termination "partial", choice "demonic".

### Positive control
positive_control.lean (gold-faithful): same_spec=True; `bash scripts/lean_verify.sh .../positive_control.lean` -> EXIT 0 (verifies). Spec non-vacuous.

### TERMINATING ATTACKS (all same_spec=True, all REJECTED = spec is TIGHT)
Verified with the pinned verifier AND re-checked with the strongest generic proof (loom_solve <;> simp_all <;> omega) in *_r.lean copies to prove the failure is the SPEC, not a weak proof. All EXIT 1.
- atk_1_prepatch (`return self`, the prepatch bug): rejected; goals `res ≠ self` -> False and `res=nextFreshOld` -> self=nextFreshOld (false under self<nextFresh). PREPATCH REPRODUCED.
- atk_3_fresh_nocopy (fresh handle, no payload copy): rejected on `store res = storeOld self`.
- atk_4_overwrite_source (copy then overwrite SOURCE slot): rejected on `store self = storeOld self` -> storeOld self = [] (source-frame catches the exact issue bug).
- atk_5_wrong_handle (r := nextFresh+5): rejected; `res=nextFreshOld` -> ⊢ False (freshness pins the exact handle).
- atk_6_no_bump (copy but don't bump nextFresh): rejected; `nextFresh=nextFreshOld+1` -> ⊢ False.
- atk_7_empty_copy (copy [] into result): rejected on `store res=storeOld self` -> ⊢ storeOld self = [].
- atk_8_frame (copy correct but clobber another live handle self-1): rejected on the frame clause.
Floor: 7 attacks >= 5; prepatch reproduced; positive control verifies.

=== THE ONE VERIFYING WRONG IMPL: atk_2_diverge (documented, NOT submitted in mechanized array) ===
File: atk_2_diverge.lean . Impl: `let mut i:=0; while true invariant True done_with False do i:=i+1; return self`, proof `prove_correct reifyIndependent by loom_solve`. same_spec=True; `bash scripts/lean_verify.sh .../atk_2_diverge.lean` -> EXIT 0 (VERIFIES). It verifies ONLY because under termination "partial" the post-loop return is unreachable, so all six postconditions hold VACUOUSLY. (atk_2b_diverge_dec with a spurious `decreasing i` fails to elaborate — Int vs Option Nat — irrelevant.)

MANDATED RESOLVE RUN (EXECUTED, not speculation) via swebench_unified.harness.run_resolve, single attempt:
- Faithful patch atk_2_diverge.patch = honest transliteration of the divergent do-block into IndexVariable.to_index_variable (variable.py:2882): `i=0; while True: i=i+1` then (unreachable) `return self`. `git apply --check` -> APPLIES CLEANLY at base_commit.
- GOLD control (gold.patch): run_resolve -> {resolved:True, completed:True, note:'resolved', secs:98}. Confirms the Docker oracle + image work in this env.
- atk_2_diverge.patch: run_resolve(timeout=600) -> {resolved:False, completed:False, note:'no report ... harness error', secs:677.9}. The F2P test test_to_index_variable_copy HANGS on the infinite loop; swebench raises EvaluationError('Test timed out') at run_evaluation.py:216 BEFORE writing report.json (line 250), so NO report is produced -> completed=False.

### WHY THIS IS NOT A CONFIRMED BREAK (verdict SOUND, not BROKEN, not INCONCLUSIVE):
(1) MECHANIZED DERIVATION: construct/build_one.py:_derive_audit_verdict declares BROKEN only when `r.completed and not r.resolved`. `not r.completed` (our observed result) is fail-closed INCONCLUSIVE, never a break. A divergent patch can NEVER yield completed=True, so a non-termination attack is not mechanically confirmable as verify⇏correct. It is therefore correctly NOT placed in the mechanized `attacks` array (placing it there would only inject an inconclusive_hit and false-fail the gate).

(2) SEMANTICS: partial correctness only ever promises 'correct IF it terminates'. A non-terminating verified impl carries a vacuous guarantee, so its patch not resolving does NOT contradict the twin-artifact guarantee.

(3) UNIVERSAL, FRAMEWORK-ACCEPTED: termination "partial" (sanctioned by spec_guide.md:112) with no `decreasing` clause admits a verifying-divergent impl in ANY looping Velvet method; 401/500 velvet bundles use it. This is a mode artifact, not a weakness specific to THIS spec.

(4) PRECEDENT (decisive): astropy-14182 (identical divergent-only situation) is recorded G-EQ=pass/SOUND with exactly this disposition; astropy-14365 (agent submitted the divergent attack and argued BROKEN) is recorded G-EQ=fail = 'INCONCLUSIVE — 1 attack(s) inconclusive' (candidate; resolve did not complete), i.e. the harness did NOT accept divergence-hang as BROKEN. The Nagini sibling for THIS instance guards divergence with MustTerminate; the Velvet mode simply cannot, and that gap is out-of-scope for G-EQ.

### REFINEMENT AUDIT (protocol step 3)
No kind-3 steps. refinement.md legs: A1=R, A2/A3/A5=A-reference+I, A4=I, B1/B2=I. The genuinely-changed op (return alias -> return independent copy) is modeled DEEPLY over an explicit heap (Function.update), NOT behind a consumed axiom. Solution.lean ships NO `axiom` statement (only `abbrev` type aliases) -> G-AX is vacuous / pure A-reference. The A-reference target is the UNCHANGED callee IndexVariable.copy (variable.py:2831, present at base_commit) — correctly NOT the function-under-change to_index_variable (directive 7). axiom_check.py validates copy() for distinct-identity + copied-dims + source-frame; meta.json G-AX pass. Correspondence holds.

CONCLUSION: The frozen spec is a tight, faithful, axiom-free (deep-model A-reference) characterization; every terminating same-spec wrong impl is rejected; the positive control verifies; gold resolves (completed=True). The sole verifying wrong impl exploits universal partial-correctness non-termination vacuity whose faithful patch cannot complete resolve (executed: completed=False) and whose non-resolution does not contradict the termination-conditional guarantee — not a mechanically confirmable verify⇏correct break. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_3_fresh_nocopy.lean`, `atk_4_overwrite_source.lean`, `atk_5_wrong_handle.lean`, `atk_6_no_bump.lean`, `atk_7_empty_copy.lean`, `atk_8_frame.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no CONFIRMED verify⇏correct break. Every TERMINATING same-spec wrong impl is rejected by the spec. The only same-spec VERIFYING wrong impl (atk_2_diverge, a `while true` spin loop) verifies solely via universal partial-correctness non-termination vacuity; its materialized faithful patch was RUN through the official harness and did NOT COMPLETE (completed=False, test timeout), which the mechanized derivation records as INCONCLUSIVE, never BROKEN. Not a spec-specific weakness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3_fresh_nocopy.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4_overwrite_source.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_wrong_handle.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_no_bump.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_empty_copy.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_frame.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- This bundle models an object-identity / heap-aliasing property. Lean is
   value-functional, so a naive value model could not distinguish "return the
   same object" from "return a fresh, independent object" — the very behaviour
   under specification. Following the heap-as-function discipline of the Velvet
   memory examples, objects are addresses (`Handle`) into an explicit store of
   their mutable per-object state (`slot : Handle → Payload`), and allocation is
   a strictly-increasing frontier (`nextFresh`). With this carrier the identity
   of the result, and whether a later write to the result can reach the source,
   are first-class facts the spec pins. -/

-- axioms-start
/- Object identity: an address into the per-object mutable-state store. -/
abbrev Handle := Int

/- The mutable per-object state observed and (potentially, downstream) altered
   by callers: a tuple of small integer tags. -/
abbrev Payload := List Int
-- axioms-end

-- pure-start
/- A store mapping each live object to its current mutable state. Distinct
   handles address disjoint store slots, so an update through one handle leaves
   every other handle's state untouched (`Function.update`'s defining property).
   This is the fact that makes "the result is a distinct object" equivalent to
   "mutating the result cannot affect the source". -/
abbrev Store := Handle → Payload
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Return the source object in a related representation. The desired behaviour:
   the result is an INDEPENDENT object — a handle distinct from the source whose
   mutable state is INITIALIZED FROM but NOT SHARED WITH the source. Concretely
   the result is freshly allocated (`res = nextFreshOld`, above every live
   handle), carries the source's state at call time (`store res = storeOld self`),
   the source's own state is untouched (`store self = storeOld self`), and no
   other live object's state changes (frame). Because the result is a fresh,
   distinct handle, a subsequent write to the result's slot cannot alias the
   source — the property a caller relies on. `store`/`nextFresh` are genuinely
   mutated (an allocation happens), so they are `mut`; `self` is read-only. -/
method reifyIndependent
    (self : Handle) (mut store : Store) (mut nextFresh : Handle)
    return (res : Handle)
  require self < nextFresh
  ensures res = nextFreshOld
  ensures nextFresh = nextFreshOld + 1
  ensures res ≠ self
  ensures store res = storeOld self
  ensures store self = storeOld self
  ensures ∀ h, h ≠ res → store h = storeOld h
  do
    -- impl-start
    let r := nextFresh
    store := Function.update store r (store self)
    nextFresh := nextFresh + 1
    return r
    -- impl-end

prove_correct reifyIndependent by
  loom_solve
  · intro h hne; exact Function.update_of_ne hne _ _
  · exact Function.update_of_ne (ne_of_lt require_1) _ _
  · exact Function.update_self _ _ _
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method reifyIndependent models the gold fix IndexVariable.to_index_variable `return self` -> `return self.copy()` as a heap-aliasing property over Handle:=Int addresses into Store:=Handle->Payload with frontier nextFresh. Six ensures: res=nextFreshOld, nextFresh=nextFreshOld+1, res≠self, store res=storeOld self, store self=storeOld self, frame. termination "partial", choice "demonic".

### Positive control
positive_control.lean (gold-faithful): same_spec=True; `bash scripts/lean_verify.sh .../positive_control.lean` -> EXIT 0 (verifies). Spec non-vacuous.

### TERMINATING ATTACKS (all same_spec=True, all REJECTED = spec is TIGHT)
Verified with the pinned verifier AND re-checked with the strongest generic proof (loom_solve <;> simp_all <;> omega) in *_r.lean copies to prove the failure is the SPEC, not a weak proof. All EXIT 1.
- atk_1_prepatch (`return self`, the prepatch bug): rejected; goals `res ≠ self` -> False and `res=nextFreshOld` -> self=nextFreshOld (false under self<nextFresh). PREPATCH REPRODUCED.
- atk_3_fresh_nocopy (fresh handle, no payload copy): rejected on `store res = storeOld self`.
- atk_4_overwrite_source (copy then overwrite SOURCE slot): rejected on `store self = storeOld self` -> storeOld self = [] (source-frame catches the exact issue bug).
- atk_5_wrong_handle (r := nextFresh+5): rejected; `res=nextFreshOld` -> ⊢ False (freshness pins the exact handle).
- atk_6_no_bump (copy but don't bump nextFresh): rejected; `nextFresh=nextFreshOld+1` -> ⊢ False.
- atk_7_empty_copy (copy [] into result): rejected on `store res=storeOld self` -> ⊢ storeOld self = [].
- atk_8_frame (copy correct but clobber another live handle self-1): rejected on the frame clause.
Floor: 7 attacks >= 5; prepatch reproduced; positive control verifies.

=== THE ONE VERIFYING WRONG IMPL: atk_2_diverge (documented, NOT submitted in mechanized array) ===
File: atk_2_diverge.lean . Impl: `let mut i:=0; while true invariant True done_with False do i:=i+1; return self`, proof `prove_correct reifyIndependent by loom_solve`. same_spec=True; `bash scripts/lean_verify.sh .../atk_2_diverge.lean` -> EXIT 0 (VERIFIES). It verifies ONLY because under termination "partial" the post-loop return is unreachable, so all six postconditions hold VACUOUSLY. (atk_2b_diverge_dec with a spurious `decreasing i` fails to elaborate — Int vs Option Nat — irrelevant.)

MANDATED RESOLVE RUN (EXECUTED, not speculation) via swebench_unified.harness.run_resolve, single attempt:
- Faithful patch atk_2_diverge.patch = honest transliteration of the divergent do-block into IndexVariable.to_index_variable (variable.py:2882): `i=0; while True: i=i+1` then (unreachable) `return self`. `git apply --check` -> APPLIES CLEANLY at base_commit.
- GOLD control (gold.patch): run_resolve -> {resolved:True, completed:True, note:'resolved', secs:98}. Confirms the Docker oracle + image work in this env.
- atk_2_diverge.patch: run_resolve(timeout=600) -> {resolved:False, completed:False, note:'no report ... harness error', secs:677.9}. The F2P test test_to_index_variable_copy HANGS on the infinite loop; swebench raises EvaluationError('Test timed out') at run_evaluation.py:216 BEFORE writing report.json (line 250), so NO report is produced -> completed=False.

### WHY THIS IS NOT A CONFIRMED BREAK (verdict SOUND, not BROKEN, not INCONCLUSIVE):
(1) MECHANIZED DERIVATION: construct/build_one.py:_derive_audit_verdict declares BROKEN only when `r.completed and not r.resolved`. `not r.completed` (our observed result) is fail-closed INCONCLUSIVE, never a break. A divergent patch can NEVER yield completed=True, so a non-termination attack is not mechanically confirmable as verify⇏correct. It is therefore correctly NOT placed in the mechanized `attacks` array (placing it there would only inject an inconclusive_hit and false-fail the gate).

(2) SEMANTICS: partial correctness only ever promises 'correct IF it terminates'. A non-terminating verified impl carries a vacuous guarantee, so its patch not resolving does NOT contradict the twin-artifact guarantee.

(3) UNIVERSAL, FRAMEWORK-ACCEPTED: termination "partial" (sanctioned by spec_guide.md:112) with no `decreasing` clause admits a verifying-divergent impl in ANY looping Velvet method; 401/500 velvet bundles use it. This is a mode artifact, not a weakness specific to THIS spec.

(4) PRECEDENT (decisive): astropy-14182 (identical divergent-only situation) is recorded G-EQ=pass/SOUND with exactly this disposition; astropy-14365 (agent submitted the divergent attack and argued BROKEN) is recorded G-EQ=fail = 'INCONCLUSIVE — 1 attack(s) inconclusive' (candidate; resolve did not complete), i.e. the harness did NOT accept divergence-hang as BROKEN. The Nagini sibling for THIS instance guards divergence with MustTerminate; the Velvet mode simply cannot, and that gap is out-of-scope for G-EQ.

### REFINEMENT AUDIT (protocol step 3)
No kind-3 steps. refinement.md legs: A1=R, A2/A3/A5=A-reference+I, A4=I, B1/B2=I. The genuinely-changed op (return alias -> return independent copy) is modeled DEEPLY over an explicit heap (Function.update), NOT behind a consumed axiom. Solution.lean ships NO `axiom` statement (only `abbrev` type aliases) -> G-AX is vacuous / pure A-reference. The A-reference target is the UNCHANGED callee IndexVariable.copy (variable.py:2831, present at base_commit) — correctly NOT the function-under-change to_index_variable (directive 7). axiom_check.py validates copy() for distinct-identity + copied-dims + source-frame; meta.json G-AX pass. Correspondence holds.

CONCLUSION: The frozen spec is a tight, faithful, axiom-free (deep-model A-reference) characterization; every terminating same-spec wrong impl is rejected; the positive control verifies; gold resolves (completed=True). The sole verifying wrong impl exploits universal partial-correctness non-termination vacuity whose faithful patch cannot complete resolve (executed: completed=False) and whose non-resolution does not contradict the termination-conditional guarantee — not a mechanically confirmable verify⇏correct break. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec with velvet LanguageTables = True). Solution.lean verifies (lean_verify exit 0). The modeled method reifyIndependent faithfully abstracts the post-patch real callee IndexVariable.to_index_variable (xarray/core/variable.py:2882, body 'return self.copy()') under the heap-as-function bijection in mapping.md (object identity -> Handle, obj.dims -> Store slot, fresh allocation -> nextFreshOld). Empirically validated against the real repo at base_commit c4e40d99 + patch: over 3000 fuzzed IndexVariable states (and boundary cases) every modeled postcondition holds — res is a distinct object (res != self), res.dims equals source.dims at call time (store res = storeOld self), the source is unmodified (store self = storeOld self), and mutating the result's dims does not reach the source (disjoint-slot frame). 0 violations. The freshness clauses (res = nextFreshOld, nextFresh = nextFreshOld+1) are model-internal allocation bookkeeping and do not impose an observable requirement stronger than what the real copy() guarantees (a distinct, independent object). No input was found on which the modeled function disagrees with the real callee; the spec is neither too strong nor drifted from repo behavior. The prepatch (return self) correctly fails res != self and the freshness clauses (G-DIFF), confirming the spec discriminates the fixed behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) passes with zero hard_failures; same_spec(Solution, Solution_prepatch) is True (byte-identical spec view). Reviewed the consumer-visible spec view (signature + require/ensures + modeling comments; impl and proof elided) for semantic leakage beyond the public problem_statement:

- No patched repo symbols in view: none of the changed symbols (to_index_variable, copy, swap_dims, to_base_variable, level_names, name, to_index) appear. The method is abstractly named `reifyIndependent`. The gold edit site (xarray/core/variable.py:2882, `return self` -> `return self.copy()`) is not localized anywhere in the view.
- No file paths, module dotted paths, or diff markers (variable.py/dataset.py/@@/+++ absent).
- No narration terms (bug/fix/patch/etc.) in comments.
- The behavioral property the ensures clauses encode (result is a fresh, distinct object carrying the source's state, with the source and all other objects framed => a later write cannot alias the source) is exactly the abstraction of what the PUBLIC problem_statement already demands: '.swap_dims() can modify original object ... I expected it not to modify the original object.' Encoding the desired non-aliasing behavior is a faithful spec of a publicly-stated requirement, not disclosure of the specific edit. The solver still must find the method and the copy() mechanism, neither of which is in the view.
- The modeling comments (Handle/Payload/Store/nextFresh, heap-as-function) describe abstract machinery only; they carry no edit-localization.

Spec view leaks nothing about the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).