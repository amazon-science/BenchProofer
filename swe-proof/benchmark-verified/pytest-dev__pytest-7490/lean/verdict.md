# P2 adversarial audit — pytest-dev__pytest-7490

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
None — no same-spec wrong impl closed. The spec problem_spec_resolveExpectedFailure fully pins result for every input (before=some x → result=some x; before=none → result=after), so it is total+deterministic (result = before.orElse after) with axioms=[] and deep_model_references=[]. Every behaviorally-divergent impl leaves an unprovable result=spec equality.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,9 +65,7 @@
 -- impl-start
 def implementation_resolveExpectedFailure
     (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
-  let mut xfailed := before
-  if xfailed.isNone then
-    xfailed := after
+  let mut xfailed := after
   return xfailed
 -- impl-end
 
@@ -80,10 +78,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,8 +66,6 @@
 def implementation_resolveExpectedFailure
     (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
   let mut xfailed := before
-  if xfailed.isNone then
-    xfailed := after
   return xfailed
 -- impl-end
 
@@ -80,10 +78,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 def implementation_resolveExpectedFailure
     (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
   let mut xfailed := before
-  if xfailed.isNone then
+  if xfailed.isSome then
     xfailed := after
   return xfailed
 -- impl-end
@@ -80,10 +80,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,11 +64,7 @@
 
 -- impl-start
 def implementation_resolveExpectedFailure
-    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
-  let mut xfailed := before
-  if xfailed.isNone then
-    xfailed := after
-  return xfailed
+    (before after : Option ExpectedFailure) : Option ExpectedFailure := none
 -- impl-end
 
 -- proof-start
@@ -80,10 +76,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,11 +64,11 @@
 
 -- impl-start
 def implementation_resolveExpectedFailure
-    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
-  let mut xfailed := before
-  if xfailed.isNone then
-    xfailed := after
-  return xfailed
+    (before after : Option ExpectedFailure) : Option ExpectedFailure :=
+  match before, after with
+  | some _, some b => some b
+  | some a, none => some a
+  | none, a => a
 -- impl-end
 
 -- proof-start
@@ -80,10 +80,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,11 +64,10 @@
 
 -- impl-start
 def implementation_resolveExpectedFailure
-    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
-  let mut xfailed := before
-  if xfailed.isNone then
-    xfailed := after
-  return xfailed
+    (before after : Option ExpectedFailure) : Option ExpectedFailure :=
+  match before with
+  | some x => some { x with run := !x.run }
+  | none => after
 -- impl-end
 
 -- proof-start
@@ -80,10 +79,7 @@
   unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
   cases before with
   | none =>
-    refine ⟨fun x h => ?_, fun _ => rfl⟩
-    exact absurd h (by simp)
+    refine ⟨fun x h => ?_, fun _ => ?_⟩ <;> simp_all <;> rfl
   | some x =>
-    refine ⟨fun y h => ?_, fun h => ?_⟩
-    · simpa using h
-    · exact absurd h (by simp)
+    refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the effective expected-failure annotation that a test's outcome report
consults when deciding whether a failing run should be reported as an expected
failure rather than a hard failure.

An expected-failure annotation may be discovered at two moments:

  * before the test body runs — the annotation derived from the markers present
    at that point (`none` when no expected-failure marker applied yet);
  * after the test body has run — the annotation derived from the markers
    present then, which may differ because the body itself can introduce a new
    marker while executing.

The effective annotation is the most-specific-known-first cascade: an annotation
already established before the body runs is authoritative and is kept as-is;
only when no annotation was established beforehand is the after-the-body
annotation consulted. This guarantees that an annotation introduced while the
test body runs is still honored by the time the outcome is reported.

The annotation carries the reporting fields a report consults: the textual
reason, whether the body is meant to run at all, and whether an unexpected pass
is to be treated strictly.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two annotation observations (the
-- one known before the body runs and the one known afterwards) enter as plain
-- data (`Option ExpectedFailure`); the only operation performed is the
-- most-specific-known-first selection between them, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The reporting view of an expected-failure annotation: the touched fields a
test outcome report consults. `Option ExpectedFailure` carries an annotation,
with `none` meaning "no expected-failure annotation is in effect" and `some a`
the annotation `a`. -/
structure ExpectedFailure where
  reason : String
  run : Bool
  strict : Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The effective annotation is fully pinned to the two observations:

  * if an annotation `x` was already established before the body ran, the result
    is exactly `some x` (the earlier annotation is authoritative);
  * if no annotation was established before the body ran, the result is exactly
    the annotation observed after the body ran (whatever that is, including
    `none`).

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_resolveExpectedFailure
    (before after : Option ExpectedFailure) (result : Option ExpectedFailure) : Prop :=
  (∀ x, before = some x → result = some x) ∧
  (before = none → result = after)
-- post-conditions-end

-- impl-start
def implementation_resolveExpectedFailure
    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
  let mut xfailed := before
  if xfailed.isNone then
    xfailed := after
  return xfailed
-- impl-end

-- proof-start
theorem correct_resolveExpectedFailure :
    ∀ (before after : Option ExpectedFailure),
      problem_spec_resolveExpectedFailure before after
        (implementation_resolveExpectedFailure before after) := by
  intro before after
  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
  cases before with
  | none =>
    refine ⟨fun x h => ?_, fun _ => rfl⟩
    exact absurd h (by simp)
  | some x =>
    refine ⟨fun y h => ?_, fun h => ?_⟩
    · simpa using h
    · exact absurd h (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 6 attacks same_spec=True (swebench_unified.markers.same_spec, lean). Built by copying Solution.lean and editing ONLY the impl region (spec/axioms/pure/pre/post byte-identical, prefix through '-- impl-start' preserved verbatim).

VERIFY CMD (each): bash scripts/lean_verify.sh <file>. Each attack given a maximal-strength closing proof (refine ...; <;> simp_all <;> rfl) to genuinely try to close.

### Results
- pos_control.lean: exit 0 (verifies, no sorry). #print axioms correct_resolveExpectedFailure => [propext, Quot.sound] (clean, no sorryAx).
- atk_1 (return `after`, drops before): exit 1 — 'rfl failed: left-hand side ...' (before=some x, after=none => none != some x).
- atk_2 (return `before` = PREPATCH BUG, no post-body refresh): exit 1 — genuine obligation failure (before=none,after=some => none != after). Prepatch bug reproduced as a non-closing attack.
- atk_3 (reversed condition: refresh on isSome): exit 1 (both branches fail rfl).
- atk_4 (constant `none`): exit 1.
- atk_5 (partial-domain: uses after when before=some & after=some): exit 1.
- atk_6 (ungrounded-oracle echo: some {x with run:=!x.run} else after, mutated field): exit 1.
All 6 failures are genuine proof-obligation failures (goal reduces to unprovable result=spec equality), NOT syntax errors (verified in .out files: 'error: Tactic rfl failed: The left-hand side ...').

NO wrong impl closed with clean axioms => NO faithful patch to materialize/resolve (protocol step 2 vacuous). verify⇒correct holds for all attacks tried.

REFINEMENT AUDIT: refinement.md legs — op1 (let mut xfailed:=before) R, op2 (if isNone then after) R, op3 (return) I. No A-legs (axioms=[], deep_model_references=[]); 'no A row' claim is correct — the two observations (before/after) enter as plain Option ExpectedFailure data, patch does not change evaluate_xfail_marks, only the store-refresh selection is modeled. No kind-3 legs. A-leg correspondence audit vacuous (no deep-model references). mapping.md symbol bindings consistent. prepatch omits op2 exactly (matches atk_2).

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
None — no same-spec wrong impl closed. The spec problem_spec_resolveExpectedFailure fully pins result for every input (before=some x → result=some x; before=none → result=after), so it is total+deterministic (result = before.orElse after) with axioms=[] and deep_model_references=[]. Every behaviorally-divergent impl leaves an unprovable result=spec equality.
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
Resolving the effective expected-failure annotation that a test's outcome report
consults when deciding whether a failing run should be reported as an expected
failure rather than a hard failure.

An expected-failure annotation may be discovered at two moments:

  * before the test body runs — the annotation derived from the markers present
    at that point (`none` when no expected-failure marker applied yet);
  * after the test body has run — the annotation derived from the markers
    present then, which may differ because the body itself can introduce a new
    marker while executing.

The effective annotation is the most-specific-known-first cascade: an annotation
already established before the body runs is authoritative and is kept as-is;
only when no annotation was established beforehand is the after-the-body
annotation consulted. This guarantees that an annotation introduced while the
test body runs is still honored by the time the outcome is reported.

The annotation carries the reporting fields a report consults: the textual
reason, whether the body is meant to run at all, and whether an unexpected pass
is to be treated strictly.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two annotation observations (the
-- one known before the body runs and the one known afterwards) enter as plain
-- data (`Option ExpectedFailure`); the only operation performed is the
-- most-specific-known-first selection between them, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The reporting view of an expected-failure annotation: the touched fields a
test outcome report consults. `Option ExpectedFailure` carries an annotation,
with `none` meaning "no expected-failure annotation is in effect" and `some a`
the annotation `a`. -/
structure ExpectedFailure where
  reason : String
  run : Bool
  strict : Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The effective annotation is fully pinned to the two observations:

  * if an annotation `x` was already established before the body ran, the result
    is exactly `some x` (the earlier annotation is authoritative);
  * if no annotation was established before the body ran, the result is exactly
    the annotation observed after the body ran (whatever that is, including
    `none`).

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_resolveExpectedFailure
    (before after : Option ExpectedFailure) (result : Option ExpectedFailure) : Prop :=
  (∀ x, before = some x → result = some x) ∧
  (before = none → result = after)
-- post-conditions-end

-- impl-start
def implementation_resolveExpectedFailure
    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
  let mut xfailed := before
  if xfailed.isNone then
    xfailed := after
  return xfailed
-- impl-end

-- proof-start
theorem correct_resolveExpectedFailure :
    ∀ (before after : Option ExpectedFailure),
      problem_spec_resolveExpectedFailure before after
        (implementation_resolveExpectedFailure before after) := by
  intro before after
  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure
  cases before with
  | none =>
    refine ⟨fun x h => ?_, fun _ => rfl⟩
    exact absurd h (by simp)
  | some x =>
    refine ⟨fun y h => ?_, fun h => ?_⟩
    · simpa using h
    · exact absurd h (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 6 attacks same_spec=True (swebench_unified.markers.same_spec, lean). Built by copying Solution.lean and editing ONLY the impl region (spec/axioms/pure/pre/post byte-identical, prefix through '-- impl-start' preserved verbatim).

VERIFY CMD (each): bash scripts/lean_verify.sh <file>. Each attack given a maximal-strength closing proof (refine ...; <;> simp_all <;> rfl) to genuinely try to close.

### Results
- pos_control.lean: exit 0 (verifies, no sorry). #print axioms correct_resolveExpectedFailure => [propext, Quot.sound] (clean, no sorryAx).
- atk_1 (return `after`, drops before): exit 1 — 'rfl failed: left-hand side ...' (before=some x, after=none => none != some x).
- atk_2 (return `before` = PREPATCH BUG, no post-body refresh): exit 1 — genuine obligation failure (before=none,after=some => none != after). Prepatch bug reproduced as a non-closing attack.
- atk_3 (reversed condition: refresh on isSome): exit 1 (both branches fail rfl).
- atk_4 (constant `none`): exit 1.
- atk_5 (partial-domain: uses after when before=some & after=some): exit 1.
- atk_6 (ungrounded-oracle echo: some {x with run:=!x.run} else after, mutated field): exit 1.
All 6 failures are genuine proof-obligation failures (goal reduces to unprovable result=spec equality), NOT syntax errors (verified in .out files: 'error: Tactic rfl failed: The left-hand side ...').

NO wrong impl closed with clean axioms => NO faithful patch to materialize/resolve (protocol step 2 vacuous). verify⇒correct holds for all attacks tried.

REFINEMENT AUDIT: refinement.md legs — op1 (let mut xfailed:=before) R, op2 (if isNone then after) R, op3 (return) I. No A-legs (axioms=[], deep_model_references=[]); 'no A row' claim is correct — the two observations (before/after) enter as plain Option ExpectedFailure data, patch does not change evaluate_xfail_marks, only the store-refresh selection is modeled. No kind-3 legs. A-leg correspondence audit vacuous (no deep-model references). mapping.md symbol bindings consistent. prepatch omits op2 exactly (matches atk_2).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for pytest-dev__pytest-7490 lean bundle.

### Checks passed
1. Solution.lean compiles via lean_verify.sh (exit 0); `#print axioms correct_resolveExpectedFailure` => [propext, Quot.sound] only — no sorryAx, proof is genuine.
2. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True — spec region byte-identical; the two files differ only in the impl body (prepatch omits op #2, so it returns `before` unconditionally and its carried gold proof fails to typecheck on `before=none → result=after`, which is the real bug).

### MODELED FUNCTION vs REAL CALLEE:
Real patched post-yield fragment in pytest_runtest_call (src/_pytest/skipping.py):
  xfailed = item._store.get(xfailed_key, None)   # before
  if xfailed is None: item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)  # after
  # result = store[xfailed_key]
Net: result = before if before is not None else after.

Spec problem_spec_resolveExpectedFailure:
  (∀ x, before = some x → result = some x) ∧ (before = none → result = after)
This is exactly result = (if before.isSome then before else after), a total functional characterization matching the real store-refresh on every (before, after) input.

### Not too strong
- Conjunct 1 mirrors the real branch that leaves the store value unchanged (result = before) when before ≠ None. Not over-constrained.
- Conjunct 2: `after` is defined in mapping.md as evaluate_xfail_marks(item); real repo stores exactly that when before is None, including after = none. Spec permits after=none, so no phantom strengthening.
- Fields dropped (raises) and the pre-yield refresh are UNDER-specifications (weakenings), which cannot make the spec too strong.

No input distinguishes the modeled function from the real callee. conformance_check.py independently differential-tests the shadow against the real Store/Xfail over 1e5 fuzzed states (consistent with this analysis). Verdict: FAITHFUL — spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched repo symbol, no narration). same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical between buggy and fixed bundles, so the spec view does not encode the impl fix.

Semantic gold-reconstruction check: the spec view models a `resolveExpectedFailure` cascade over `before`/`after : Option ExpectedFailure` (before-body annotation authoritative, else after-body annotation), guaranteeing an xfail marker introduced during the test body is still honored at report time. This is a faithful BEHAVIORAL formalization of the fixed behavior that is ALREADY PUBLIC in problem_statement: the issue report demonstrates `request.node.add_marker(mark)` inside the test body followed by `assert 0`, and states the regression is that a dynamically-added xfail is no longer honored (reported as hard failure instead of xfail). The before/after two-moment distinction is directly derivable from that public example (a marker added *during* the run).

The spec view does NOT reveal anything beyond the public statement: the impl and proof regions are elided; it never names the patched file src/_pytest/skipping.py, the hook pytest_runtest_call, `yield`, evaluate_xfail_marks, item._store, or xfailed_key. It discloses the observable WHAT (honor a dynamically-added xfail — already public) not the edit's WHERE/HOW (post-yield store refresh in the hookwrapper). No line leaks the gold edit beyond problem_statement (hints_text, which only names the culprit commit, was correctly not used as a baseline).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
