# P2 adversarial audit — pydata__xarray-3993

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

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,7 @@
 def implementation_integrate {α DS : Type}
     (integrateAlong : Option α → DS) (coord dim : Option α) :
     Except Unit (DS × Bool) := Id.run do
-  if dim.isSome && coord.isSome then
-    return Except.error ()
-  let mut effective := coord
-  let mut warned := false
-  if dim.isSome && coord.isNone then
-    effective := dim
-    warned := true
-  return Except.ok (integrateAlong effective, warned)
+  return Except.ok (integrateAlong dim, false)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,9 @@
   if dim.isSome && coord.isSome then
     return Except.error ()
   let mut effective := coord
-  let mut warned := false
   if dim.isSome && coord.isNone then
     effective := dim
-    warned := true
-  return Except.ok (integrateAlong effective, warned)
+  return Except.ok (integrateAlong effective, false)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,10 @@
     Except Unit (DS × Bool) := Id.run do
   if dim.isSome && coord.isSome then
     return Except.error ()
-  let mut effective := coord
   let mut warned := false
   if dim.isSome && coord.isNone then
-    effective := dim
     warned := true
-  return Except.ok (integrateAlong effective, warned)
+  return Except.ok (integrateAlong coord, warned)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,8 +77,6 @@
 def implementation_integrate {α DS : Type}
     (integrateAlong : Option α → DS) (coord dim : Option α) :
     Except Unit (DS × Bool) := Id.run do
-  if dim.isSome && coord.isSome then
-    return Except.error ()
   let mut effective := coord
   let mut warned := false
   if dim.isSome && coord.isNone then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,7 @@
 def implementation_integrate {α DS : Type}
     (integrateAlong : Option α → DS) (coord dim : Option α) :
     Except Unit (DS × Bool) := Id.run do
-  if dim.isSome && coord.isSome then
-    return Except.error ()
-  let mut effective := coord
-  let mut warned := false
-  if dim.isSome && coord.isNone then
-    effective := dim
-    warned := true
-  return Except.ok (integrateAlong effective, warned)
+  return Except.ok (integrateAlong coord, false)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,11 +79,11 @@
     Except Unit (DS × Bool) := Id.run do
   if dim.isSome && coord.isSome then
     return Except.error ()
-  let mut effective := coord
-  let mut warned := false
-  if dim.isSome && coord.isNone then
-    effective := dim
-    warned := true
+  let mut effective := dim
+  let mut warned := true
+  if dim.isNone then
+    effective := coord
+    warned := false
   return Except.ok (integrateAlong effective, warned)
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Integrating an array along a coordinate, with a consistent coordinate-selection
argument convention.

The operation integrates the array along one (or more) coordinate(s) using the
trapezoidal rule. The coordinate to integrate along may be supplied in two ways:

  * `coord` — the preferred argument naming the coordinate(s) to use;
  * `dim` — an older alternative spelling of the same choice, kept for
    compatibility but deprecated.

The argument-resolution rules are:

  * supplying BOTH `coord` and `dim` is contradictory and is rejected (an error);
  * supplying ONLY `dim` selects that coordinate to integrate along, but because
    this spelling is on its way out the call additionally signals a
    deprecation notice;
  * otherwise the coordinate named by `coord` (which may itself be absent) is
    used, with no notice.

Once the effective coordinate has been resolved, the integration itself is the
unchanged downstream step: integrating the array along the chosen coordinate.
The result therefore equals that downstream integration applied to whichever
coordinate the rules above select, and the deprecation notice is raised in
exactly the one case described.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical contract. The downstream
-- integration step (integrating the array along a resolved coordinate) is left
-- UNIVERSALLY QUANTIFIED as a parameter `integrateAlong : Option α → DS`: the
-- specification holds for EVERY such step, so it pins only that the correctly
-- resolved coordinate reaches it (plus the error / deprecation-notice logic),
-- which is exactly the behavior under specification. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the coordinate selection is expressed
-- directly in the post-condition and the implementation.
-- pure-end

-- post-conditions-start
/-- The outcome of resolving the integration coordinate and integrating.

`α` is the type of a coordinate selector and `DS` the type of an integrated
result. `integrateAlong c` is the unchanged downstream integration of the array
along the (optional) coordinate `c`. The result is `Except.error ()` when the
call is rejected, or `Except.ok (value, warned)` where `value` is the integrated
result and `warned` records whether a deprecation notice was raised.

The result is fully pinned for every input (directive 5 frame):

  * if both `coord` and `dim` are supplied, the call is rejected;
  * if only `dim` is supplied, the array is integrated along `dim` and a
    deprecation notice is raised (`warned = true`);
  * if `dim` is absent, the array is integrated along `coord` (which may itself
    be absent) and no notice is raised (`warned = false`).

These three antecedents are mutually exclusive and exhaustive, so no component
of the result is left free. -/
def problem_spec_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α)
    (result : Except Unit (DS × Bool)) : Prop :=
  (coord.isSome = true ∧ dim.isSome = true →
      result = Except.error ()) ∧
  (dim.isSome = true ∧ coord = none →
      result = Except.ok (integrateAlong dim, true)) ∧
  (dim = none →
      result = Except.ok (integrateAlong coord, false))
-- post-conditions-end

-- impl-start
def implementation_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    Except Unit (DS × Bool) := Id.run do
  if dim.isSome && coord.isSome then
    return Except.error ()
  let mut effective := coord
  let mut warned := false
  if dim.isSome && coord.isNone then
    effective := dim
    warned := true
  return Except.ok (integrateAlong effective, warned)
-- impl-end

-- proof-start
theorem correct_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    problem_spec_integrate integrateAlong coord dim
      (implementation_integrate integrateAlong coord dim) := by
  refine ⟨?_, ?_, ?_⟩ <;> intro h <;>
    cases coord <;> cases dim <;>
    simp_all [implementation_integrate, Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_integrate fully pins the output across all 4 input combos (both present -> error(); dim-only -> ok(integrateAlong dim, true); dim=none -> ok(integrateAlong coord, false)), with integrateAlong universally quantified (Option a -> DS) so the EXACT resolved Option must reach the callee.

Same_spec = True for all 6 attacks + positive control (checked via swebench_unified.markers.same_spec, lean backend), impl-region-only edits.

### VERIFY RESULTS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4):
- pos_control (gold): EXIT 0 (verifies). #print axioms correct_integrate -> [propext, Quot.sound] (clean).
- atk_1 (prepatch bug: always ok(integrateAlong dim, false), no warning, no both-rejection): EXIT 1 (fails; rfl mismatch dim-only warned false vs true, and both-supplied not error). prepatch_reproduced=true.
- atk_2 (boundary: correct resolution but warned never set true): EXIT 1.
- atk_3 (control-flow-effect: always integrateAlong coord, ignore dim->coord aliasing): EXIT 1.
- atk_4 (no both-supplied rejection: returns ok along coord when both present): EXIT 1.
- atk_5 (ungrounded-oracle echo: always ok(integrateAlong coord, false)): EXIT 1.
- atk_6 (control-flow reformulation: effective=dim/warned=true default, flip to coord/false when dim.isNone; both-supplied->error): EXIT 0 (verifies). #print axioms -> [propext, Quot.sound] (clean). This is a behaviorally-EQUIVALENT echo of gold (guaranteed by the fully-pinned spec) written with different control flow.

MANDATORY RESOLVE STEP for the sole verifying same-spec impl (atk_6):
- Materialized faithful patch atk_6_patch.diff (mirrors atk_6's control flow: effective=dim/warned=true default, flip when dim is None; ValueError when both; single warnings.warn gated on warned; downstream integrate(effective)).
- First two run_resolve attempts returned completed=False 'no report' -> diagnosed: (1) heavy docker contention from concurrent audit concurrent runs, and (2) a malformed hunk-3 header (@@ -3528,7 +3534,22 @@ but new-side was 26 lines because atk_6 adds 4 more lines than gold) causing patch-apply failure / empty run dir. Fixed header to +3534,26.
- run_resolve('pydata__xarray-3993', atk_6_patch, run_id='sbu-audit-atk6-3993-fix') -> RESOLVED: True, completed: True, patch_successfully_applied: True, FAIL_TO_PASS success=['test_integrate[True]','test_integrate[False]'], failure=[]. => verify => resolve holds for atk_6.
- Harness path validated with GOLD positive control: run_resolve on benchmark-verified/.../patch.diff -> RESOLVED: True, completed: True, F2P both pass.

No verifying same-spec impl fails to resolve -> verify does NOT imply broken. verify => correct holds.

REFINEMENT AUDIT (refinement.md): 6 legs. Ops 1,2,4 = R (isSome<->is not None; error<->ValueError; dim->coord alias + FutureWarning), ops 3,6 = I (warned init false; package return), op 5 = A-reference (self._to_temp_dataset().integrate(coord, datetime_unit) then _from_temp_dataset; universally quantified integrateAlong; UNCHANGED by patch, no property consumed). NO kind-3 (deep-model) legs. Confirmed grep: NO axiom/opaque decls in Solution.lean; axiom_check.py is a skip stub; meta axioms=[]. The A-reference correspondence is sound: the callee is genuinely unchanged by the gold patch (verified against patch.diff and mapping.md) and only the argument resolution changed, so leaving it universally quantified soundly isolates the R/I resolution content that G-CONF tests.

VERDICT: SOUND. >=6 attacks encoded+same-spec+verified; all 5 genuinely-wrong impls fail to close; the only closing same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES; gold positive control resolves; refinement legs are all R/A-reference/I with sound A-reference correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Integrating an array along a coordinate, with a consistent coordinate-selection
argument convention.

The operation integrates the array along one (or more) coordinate(s) using the
trapezoidal rule. The coordinate to integrate along may be supplied in two ways:

  * `coord` — the preferred argument naming the coordinate(s) to use;
  * `dim` — an older alternative spelling of the same choice, kept for
    compatibility but deprecated.

The argument-resolution rules are:

  * supplying BOTH `coord` and `dim` is contradictory and is rejected (an error);
  * supplying ONLY `dim` selects that coordinate to integrate along, but because
    this spelling is on its way out the call additionally signals a
    deprecation notice;
  * otherwise the coordinate named by `coord` (which may itself be absent) is
    used, with no notice.

Once the effective coordinate has been resolved, the integration itself is the
unchanged downstream step: integrating the array along the chosen coordinate.
The result therefore equals that downstream integration applied to whichever
coordinate the rules above select, and the deprecation notice is raised in
exactly the one case described.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical contract. The downstream
-- integration step (integrating the array along a resolved coordinate) is left
-- UNIVERSALLY QUANTIFIED as a parameter `integrateAlong : Option α → DS`: the
-- specification holds for EVERY such step, so it pins only that the correctly
-- resolved coordinate reaches it (plus the error / deprecation-notice logic),
-- which is exactly the behavior under specification. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the coordinate selection is expressed
-- directly in the post-condition and the implementation.
-- pure-end

-- post-conditions-start
/-- The outcome of resolving the integration coordinate and integrating.

`α` is the type of a coordinate selector and `DS` the type of an integrated
result. `integrateAlong c` is the unchanged downstream integration of the array
along the (optional) coordinate `c`. The result is `Except.error ()` when the
call is rejected, or `Except.ok (value, warned)` where `value` is the integrated
result and `warned` records whether a deprecation notice was raised.

The result is fully pinned for every input (directive 5 frame):

  * if both `coord` and `dim` are supplied, the call is rejected;
  * if only `dim` is supplied, the array is integrated along `dim` and a
    deprecation notice is raised (`warned = true`);
  * if `dim` is absent, the array is integrated along `coord` (which may itself
    be absent) and no notice is raised (`warned = false`).

These three antecedents are mutually exclusive and exhaustive, so no component
of the result is left free. -/
def problem_spec_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α)
    (result : Except Unit (DS × Bool)) : Prop :=
  (coord.isSome = true ∧ dim.isSome = true →
      result = Except.error ()) ∧
  (dim.isSome = true ∧ coord = none →
      result = Except.ok (integrateAlong dim, true)) ∧
  (dim = none →
      result = Except.ok (integrateAlong coord, false))
-- post-conditions-end

-- impl-start
def implementation_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    Except Unit (DS × Bool) := Id.run do
  if dim.isSome && coord.isSome then
    return Except.error ()
  let mut effective := coord
  let mut warned := false
  if dim.isSome && coord.isNone then
    effective := dim
    warned := true
  return Except.ok (integrateAlong effective, warned)
-- impl-end

-- proof-start
theorem correct_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    problem_spec_integrate integrateAlong coord dim
      (implementation_integrate integrateAlong coord dim) := by
  refine ⟨?_, ?_, ?_⟩ <;> intro h <;>
    cases coord <;> cases dim <;>
    simp_all [implementation_integrate, Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_integrate fully pins the output across all 4 input combos (both present -> error(); dim-only -> ok(integrateAlong dim, true); dim=none -> ok(integrateAlong coord, false)), with integrateAlong universally quantified (Option a -> DS) so the EXACT resolved Option must reach the callee.

Same_spec = True for all 6 attacks + positive control (checked via swebench_unified.markers.same_spec, lean backend), impl-region-only edits.

### VERIFY RESULTS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4):
- pos_control (gold): EXIT 0 (verifies). #print axioms correct_integrate -> [propext, Quot.sound] (clean).
- atk_1 (prepatch bug: always ok(integrateAlong dim, false), no warning, no both-rejection): EXIT 1 (fails; rfl mismatch dim-only warned false vs true, and both-supplied not error). prepatch_reproduced=true.
- atk_2 (boundary: correct resolution but warned never set true): EXIT 1.
- atk_3 (control-flow-effect: always integrateAlong coord, ignore dim->coord aliasing): EXIT 1.
- atk_4 (no both-supplied rejection: returns ok along coord when both present): EXIT 1.
- atk_5 (ungrounded-oracle echo: always ok(integrateAlong coord, false)): EXIT 1.
- atk_6 (control-flow reformulation: effective=dim/warned=true default, flip to coord/false when dim.isNone; both-supplied->error): EXIT 0 (verifies). #print axioms -> [propext, Quot.sound] (clean). This is a behaviorally-EQUIVALENT echo of gold (guaranteed by the fully-pinned spec) written with different control flow.

MANDATORY RESOLVE STEP for the sole verifying same-spec impl (atk_6):
- Materialized faithful patch atk_6_patch.diff (mirrors atk_6's control flow: effective=dim/warned=true default, flip when dim is None; ValueError when both; single warnings.warn gated on warned; downstream integrate(effective)).
- First two run_resolve attempts returned completed=False 'no report' -> diagnosed: (1) heavy docker contention from concurrent audit concurrent runs, and (2) a malformed hunk-3 header (@@ -3528,7 +3534,22 @@ but new-side was 26 lines because atk_6 adds 4 more lines than gold) causing patch-apply failure / empty run dir. Fixed header to +3534,26.
- run_resolve('pydata__xarray-3993', atk_6_patch, run_id='sbu-audit-atk6-3993-fix') -> RESOLVED: True, completed: True, patch_successfully_applied: True, FAIL_TO_PASS success=['test_integrate[True]','test_integrate[False]'], failure=[]. => verify => resolve holds for atk_6.
- Harness path validated with GOLD positive control: run_resolve on benchmark-verified/.../patch.diff -> RESOLVED: True, completed: True, F2P both pass.

No verifying same-spec impl fails to resolve -> verify does NOT imply broken. verify => correct holds.

REFINEMENT AUDIT (refinement.md): 6 legs. Ops 1,2,4 = R (isSome<->is not None; error<->ValueError; dim->coord alias + FutureWarning), ops 3,6 = I (warned init false; package return), op 5 = A-reference (self._to_temp_dataset().integrate(coord, datetime_unit) then _from_temp_dataset; universally quantified integrateAlong; UNCHANGED by patch, no property consumed). NO kind-3 (deep-model) legs. Confirmed grep: NO axiom/opaque decls in Solution.lean; axiom_check.py is a skip stub; meta axioms=[]. The A-reference correspondence is sound: the callee is genuinely unchanged by the gold patch (verified against patch.diff and mapping.md) and only the argument resolution changed, so leaving it universally quantified soundly isolates the R/I resolution content that G-CONF tests.

VERDICT: SOUND. >=6 attacks encoded+same-spec+verified; all 5 genuinely-wrong impls fail to close; the only closing same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES; gold positive control resolves; refinement legs are all R/A-reference/I with sound A-reference correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec faithfully models the pydata__xarray-3993 fix (DataArray.integrate coord/dim resolution). Truth table matches gold patch on all four input classes: (coord=some,dim=some)->error; (coord=none,dim=some)->integrateAlong dim + warned=true; (coord=some,dim=none)->integrateAlong coord + warned=false; (coord=none,dim=none)->integrateAlong none + warned=false. same_spec(Solution,prepatch)=True (spec region byte-identical). lean_verify exit 0; #print axioms = [propext, Quot.sound], no sorryAx. Downstream integration is a legitimate universally-quantified A-reference (unchanged by fix); G-CONF differential-tests it against the real patched callee over 100k inputs with 0 disagreements. One noted abstraction boundary: the total integrateAlong:Option a->DS cannot represent a downstream raise (e.g. da.integrate('x2d') ValueError), which the dim=none clause nominally treats as Except.ok — but this is an accepted A-reference boundary orthogonal to the fix, both G-CONF sides bind the same real (raising) callee, so no disagreement arises and the theorem holds for EVERY integrateAlong. Spec is not too strong on the fixed behavior. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). Findings: (1) Mechanical leakage.screen passes with zero hard failures. (2) same_spec(Solution.lean, Solution_prepatch.lean) = True — the spec region (docstring + problem_spec_integrate) is byte-identical pre/post-patch, so the spec view cannot encode anything patch-specific. (3) None of the gold-patch literals appear anywhere in the spec view: '0.19.0', 'FutureWarning', 'ValueError', 'Cannot pass both 'dim' and 'coord'', 'warnings.warn', 'stacklevel', 'dataarray.py'/'_to_temp_dataset'. No diff markers, patched file paths, or module paths. (4) The only patched repo symbols are `integrate`/`differentiate`, both already public verbatim in the problem_statement, so they are not leaks; the spec identifiers `coord`/`dim` are also public in the problem_statement, and `integrateAlong`/`problem_spec_integrate` are generic abstract names, not patched repo symbols. (5) No bug/fix/patch narration in comments. (6) The problem_statement already discloses the entire fix direction (DataArray.integrate should use `coord` not `dim`) and explicitly poses the open question 'whether it requires a deprecation cycle?'. The spec pins the deprecation-notice + both-supplied-error behavior abstractly — this is the spec's legitimate job of stating required behavior, expressed without quoting the gold edit's version string, warning class, or exact message text. No RELAXED_LEAKAGE.md / relaxed_leakage flag present (deferral not applicable). The spec view reveals nothing about the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
