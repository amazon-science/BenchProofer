# P2 adversarial audit — scikit-learn__scikit-learn-12973

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing proof, so verify⇏correct cannot be exhibited. Machine-checked non-existence: for every wrong impl, the correctness goal reduces (over the finite Bool × Option Bool domain) to a proposition that Lean's `decide` proves is FALSE — e.g. atk_1 (prepatch bug) leaves the goal `configured = (some b).getD configured`, false at configured≠b.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,9 +54,8 @@
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
   let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  -- prepatch: never fall back; ignore call, deliver the configured field
+  return configured
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,9 @@
 
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
-  let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  match call with
+  | some b => return b
+  | none   => return !configured
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,7 @@
 
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
-  let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  return call.getD (!configured)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
   let mut copyX : CallChoice := call
-  if copyX = none then
+  if copyX ≠ none then
     copyX := some configured
   return copyX.getD configured
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,7 @@
 
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
-  let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  return !(call.getD configured)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,7 @@
 
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
-  let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,8 @@
 
 -- impl-start
 def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
-  let mut copyX : CallChoice := call
-  if copyX = none then
-    copyX := some configured
-  return copyX.getD configured
+  -- configured always wins; per-call choice only used if configured were absent (it never is)
+  return (some configured).getD (call.getD configured)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A linear-model estimator carries a configured boolean that decides whether the
input feature matrix is duplicated before the data-preparation step runs, or may
instead be reused in place. The fitting routine also accepts a per-call boolean of
the same meaning, so a caller can state the choice at fit time without rebuilding
the estimator.

The behavior modeled here is the contract between these two settings and the
single boolean actually delivered to the data-preparation step (the flag that
governs whether the feature matrix is duplicated). The per-call setting is
optional: when the caller supplies an explicit value it takes precedence; when the
caller supplies nothing, the estimator's configured value is used. Either way the
delivered flag is one definite boolean, and it is exactly the value the data-
preparation step receives.

We model the estimator by the only field that participates in this contract — its
configured duplicate-input boolean — together with the optional per-call boolean,
and the modeled result is the boolean delivered to the data-preparation step. A
faithful routine delivers the per-call value whenever one is supplied, and the
configured value otherwise.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The data-
-- preparation step and the path solver are not modeled; only the single boolean
-- delivered to the data-preparation step is, and that boolean is pure data threaded
-- through the routine. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The optional per-call duplicate-input boolean. `none` is the absent per-call
choice (the caller supplied nothing); `some b` is an explicit caller choice `b`. -/
abbrev CallChoice := Option Bool

/-- Resolve the duplicate-input boolean delivered to the data-preparation step:
the explicit per-call choice when one is present, otherwise the estimator's
configured value. -/
def resolveCopy (configured : Bool) (call : CallChoice) : Bool := call.getD configured
-- pure-end

-- post-conditions-start
/-- The boolean delivered to the data-preparation step equals the per-call choice
when the caller supplies one, and the estimator's configured value otherwise. This
fully pins the modeled result to the inputs: no configuration leaves the delivered
boolean free, and in particular an explicit per-call choice that differs from the
configured value must still be the one delivered. -/
def problem_spec_deliveredCopy (configured : Bool) (call : CallChoice) (result : Bool) : Prop :=
  result = call.getD configured
-- post-conditions-end

-- impl-start
def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
  let mut copyX : CallChoice := call
  if copyX = none then
    copyX := some configured
  return copyX.getD configured
-- impl-end

-- proof-start
theorem correct_deliveredCopy :
    ∀ (configured : Bool) (call : CallChoice),
      problem_spec_deliveredCopy configured call
        (implementation_deliveredCopy configured call) := by
  intro configured call
  unfold problem_spec_deliveredCopy implementation_deliveredCopy
  cases call with
  | none => rfl
  | some b => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_deliveredCopy configured call result := result = call.getD configured, and correct_deliveredCopy quantifies over ALL (configured : Bool) (call : Option Bool). This is a TOTAL, EXACT pin over a finite 6-point domain with axioms=[] and deep_model_references=[] (verified: `#print axioms correct_deliveredCopy` => 'does not depend on any axioms', pos_axioms.lean EXIT=0). A same-spec impl verifies IFF it equals call.getD configured on every one of the 6 points; any deviation on any point is provably unclosable.

A-LEG AUDIT (my mandate): refinement.md declares NO A-legs. Ops #1/#2/#4 = R (Bool/Option Bool type refinement), op #3 = I (identical control flow `if copy_X is None: copy_X = self.copy_X`). No axiom is consumed and no unchanged callee (_preprocess_data, lars_path) is deep-modeled — only the pure boolean threaded into _preprocess_data is modeled. Every leg is R or I; NO kind-3 (unjustified) leg. The A-leg falsification surface is therefore vacuous — nothing to break. Model↔patch correspondence holds: the spec exactly captures the gold `if copy_X is None: copy_X=self.copy_X; _preprocess_data(..., copy_X)`, and the prepatch bug (deliver self.copy_X regardless) is exactly atk_1, discriminated at call=some b, b≠configured — the F2P case fit(copy_X=False) on copy_X=True default.

ATTACKS (all same_spec=True vs Solution.lean, confirmed via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG: `return configured` (discards per-call choice). cmd: `bash scripts/lean_verify.sh atk_1.lean` EXIT=1; original-proof error goal `configured = (some b).getD configured`. decide-variant dec_1 EXIT=1 'decide proved the proposition is false'.
- atk_2 PARTIAL-DOMAIN: correct on call=some b, flips to `!configured` on call=none. EXIT=1; dec_2 decide=false.
- atk_3 BOUNDARY: `call.getD (!configured)` (fallback uses negated field). EXIT=1; dec_3 decide=false.
- atk_4 CONTROL-FLOW-EFFECT: inverted guard `if copyX ≠ none then copyX := some configured`. EXIT=1; dec_4 decide=false.
- atk_5 UNGROUNDED-ORACLE ECHO: `!(call.getD configured)` (fully negated resolved value). EXIT=1; dec_5 decide=false.
- atk_6 CONSTANT: `return true` (ignores both inputs). EXIT=1; dec_6 decide=false.
- atk_7 SWAPPED-PRECEDENCE: `(some configured).getD (call.getD configured)` — configured always wins over explicit call. EXIT=1; dec_7 decide=false.

VERIFICATION METHOD: each wrong impl was checked with BOTH the carried gold proof (rfl-based, EXIT=1 error) AND a `decide`-based proof over the reverted finite domain. The decide result is DECISIVE non-provability: `decide` closes iff the statement is genuinely true, and it reported every wrong impl FALSE. Positive control dec_0 (correct impl + decide) EXIT=0, confirming decide works and the domain is decidable — so the false verdicts are not decide-failures. Commands run concurrently (≤4 background jobs per batch) under scripts/lean_verify.sh; heavy host contention from sibling audit concurrent runs caused one detached-job batch to lose output, which was re-run in-foreground to completion (all results captured).

STEP-2 RESOLVE: vacuous — NO wrong impl produced a closing clean-axiom proof, so there is no faithful patch to materialize/resolve. patches={} accordingly. BROKEN could only arise from a verifying-but-wrong impl; none exists.

VERDICT: SOUND. 7 distinct same-spec wrong impls (prepatch + partial-domain + boundary + control-flow + ungrounded-echo + constant + swapped-precedence) all machine-proven unclosable; the exact-equality total pin over the finite domain leaves no slack for a divergent impl to verify.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing proof, so verify⇏correct cannot be exhibited. Machine-checked non-existence: for every wrong impl, the correctness goal reduces (over the finite Bool × Option Bool domain) to a proposition that Lean's `decide` proves is FALSE — e.g. atk_1 (prepatch bug) leaves the goal `configured = (some b).getD configured`, false at configured≠b.
```

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
A linear-model estimator carries a configured boolean that decides whether the
input feature matrix is duplicated before the data-preparation step runs, or may
instead be reused in place. The fitting routine also accepts a per-call boolean of
the same meaning, so a caller can state the choice at fit time without rebuilding
the estimator.

The behavior modeled here is the contract between these two settings and the
single boolean actually delivered to the data-preparation step (the flag that
governs whether the feature matrix is duplicated). The per-call setting is
optional: when the caller supplies an explicit value it takes precedence; when the
caller supplies nothing, the estimator's configured value is used. Either way the
delivered flag is one definite boolean, and it is exactly the value the data-
preparation step receives.

We model the estimator by the only field that participates in this contract — its
configured duplicate-input boolean — together with the optional per-call boolean,
and the modeled result is the boolean delivered to the data-preparation step. A
faithful routine delivers the per-call value whenever one is supplied, and the
configured value otherwise.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The data-
-- preparation step and the path solver are not modeled; only the single boolean
-- delivered to the data-preparation step is, and that boolean is pure data threaded
-- through the routine. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The optional per-call duplicate-input boolean. `none` is the absent per-call
choice (the caller supplied nothing); `some b` is an explicit caller choice `b`. -/
abbrev CallChoice := Option Bool

/-- Resolve the duplicate-input boolean delivered to the data-preparation step:
the explicit per-call choice when one is present, otherwise the estimator's
configured value. -/
def resolveCopy (configured : Bool) (call : CallChoice) : Bool := call.getD configured
-- pure-end

-- post-conditions-start
/-- The boolean delivered to the data-preparation step equals the per-call choice
when the caller supplies one, and the estimator's configured value otherwise. This
fully pins the modeled result to the inputs: no configuration leaves the delivered
boolean free, and in particular an explicit per-call choice that differs from the
configured value must still be the one delivered. -/
def problem_spec_deliveredCopy (configured : Bool) (call : CallChoice) (result : Bool) : Prop :=
  result = call.getD configured
-- post-conditions-end

-- impl-start
def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
  let mut copyX : CallChoice := call
  if copyX = none then
    copyX := some configured
  return copyX.getD configured
-- impl-end

-- proof-start
theorem correct_deliveredCopy :
    ∀ (configured : Bool) (call : CallChoice),
      problem_spec_deliveredCopy configured call
        (implementation_deliveredCopy configured call) := by
  intro configured call
  unfold problem_spec_deliveredCopy implementation_deliveredCopy
  cases call with
  | none => rfl
  | some b => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_deliveredCopy configured call result := result = call.getD configured, and correct_deliveredCopy quantifies over ALL (configured : Bool) (call : Option Bool). This is a TOTAL, EXACT pin over a finite 6-point domain with axioms=[] and deep_model_references=[] (verified: `#print axioms correct_deliveredCopy` => 'does not depend on any axioms', pos_axioms.lean EXIT=0). A same-spec impl verifies IFF it equals call.getD configured on every one of the 6 points; any deviation on any point is provably unclosable.

A-LEG AUDIT (my mandate): refinement.md declares NO A-legs. Ops #1/#2/#4 = R (Bool/Option Bool type refinement), op #3 = I (identical control flow `if copy_X is None: copy_X = self.copy_X`). No axiom is consumed and no unchanged callee (_preprocess_data, lars_path) is deep-modeled — only the pure boolean threaded into _preprocess_data is modeled. Every leg is R or I; NO kind-3 (unjustified) leg. The A-leg falsification surface is therefore vacuous — nothing to break. Model↔patch correspondence holds: the spec exactly captures the gold `if copy_X is None: copy_X=self.copy_X; _preprocess_data(..., copy_X)`, and the prepatch bug (deliver self.copy_X regardless) is exactly atk_1, discriminated at call=some b, b≠configured — the F2P case fit(copy_X=False) on copy_X=True default.

ATTACKS (all same_spec=True vs Solution.lean, confirmed via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG: `return configured` (discards per-call choice). cmd: `bash scripts/lean_verify.sh atk_1.lean` EXIT=1; original-proof error goal `configured = (some b).getD configured`. decide-variant dec_1 EXIT=1 'decide proved the proposition is false'.
- atk_2 PARTIAL-DOMAIN: correct on call=some b, flips to `!configured` on call=none. EXIT=1; dec_2 decide=false.
- atk_3 BOUNDARY: `call.getD (!configured)` (fallback uses negated field). EXIT=1; dec_3 decide=false.
- atk_4 CONTROL-FLOW-EFFECT: inverted guard `if copyX ≠ none then copyX := some configured`. EXIT=1; dec_4 decide=false.
- atk_5 UNGROUNDED-ORACLE ECHO: `!(call.getD configured)` (fully negated resolved value). EXIT=1; dec_5 decide=false.
- atk_6 CONSTANT: `return true` (ignores both inputs). EXIT=1; dec_6 decide=false.
- atk_7 SWAPPED-PRECEDENCE: `(some configured).getD (call.getD configured)` — configured always wins over explicit call. EXIT=1; dec_7 decide=false.

VERIFICATION METHOD: each wrong impl was checked with BOTH the carried gold proof (rfl-based, EXIT=1 error) AND a `decide`-based proof over the reverted finite domain. The decide result is DECISIVE non-provability: `decide` closes iff the statement is genuinely true, and it reported every wrong impl FALSE. Positive control dec_0 (correct impl + decide) EXIT=0, confirming decide works and the domain is decidable — so the false verdicts are not decide-failures. Commands run concurrently (≤4 background jobs per batch) under scripts/lean_verify.sh; heavy host contention from sibling audit concurrent runs caused one detached-job batch to lose output, which was re-run in-foreground to completion (all results captured).

STEP-2 RESOLVE: vacuous — NO wrong impl produced a closing clean-axiom proof, so there is no faithful patch to materialize/resolve. patches={} accordingly. BROKEN could only arise from a verifying-but-wrong impl; none exists.

VERDICT: SOUND. 7 distinct same-spec wrong impls (prepatch + partial-domain + boundary + control-flow + ungrounded-echo + constant + swapped-precedence) all machine-proven unclosable; the exact-equality total pin over the finite domain leaves no slack for a divergent impl to verify.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the Lean spec for scikit-learn__scikit-learn-12973 (LassoLarsIC.fit, boolean delivered to LinearModel._preprocess_data's copy slot). The spec models the delivered boolean as `result = call.getD configured` (post-conditions region), where `configured : Bool` = self.copy_X and `call : Option Bool` = fit's copy_X arg (None/True/False).

Gold patch (verified against test.jsonl) makes fit(self,X,y,copy_X=None): `if copy_X is None: copy_X = self.copy_X` then `_preprocess_data(..., copy_X)`. Real post-patch semantics: deliver call when call is not None, else configured — exactly Option.getD.

The modeled domain is finite and small: Bool × Option Bool = exactly 6 inputs. I exhaustively enumerated all 6 and the spec agrees with the real repo on every one (configured∈{T,F} × call∈{None,T,F}): none diverge. In particular the discriminating case configured=True, call=some false yields delivered=False in both spec and real fit (the F2P test's copy_X=False case). No too-strong / drifting behavior found — there is NO input where the modeled function disagrees with the real callee.

Corroborating checks: (1) Lean Solution.lean compiles under lean_verify.sh (exit 0, no sorry) and `#print axioms correct_deliveredCopy` reports 'does not depend on any axioms' — proof is real, not sorryAx-faked. (2) Spec regions byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True via swebench_unified.markers with LeanBackend). (3) conformance_check.py drives the REAL patched fit via a _preprocess_data monkeypatch capturing the delivered copy bool, diffs vs shadow `configured if call is None else call` over the exhaustive 2×3 grid + 120k fuzz, seed 12973 — matches the spec. (4) axioms=[], deep_model_references=[] consistent with an all-R/I pure-dataflow model; no unmodeled callee contract to be unfaithful about. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reconstructed the solver-visible spec view via swebench_unified.markers.spec_view(Solution.lean, LeanBackend): impl and proof regions collapse to placeholders; only the docstring, axioms note, pure region (CallChoice/resolveCopy) and post-condition (problem_spec_deliveredCopy: result = call.getD configured) are visible. same_spec(patched, prepatch)=True confirms spec-region byte-identity. The spec view is fully abstracted: it never names any patched repo symbol (copy_X, self.copy_X, fit, None default, _preprocess_data), no file path (least_angle.py), no line numbers, no diff markers, and no bug/fix narration — all repo-specific detail lives only in refinement.md/mapping.md (not part of the spec view). Its only semantic content — 'the delivered flag equals the per-call value when the caller supplies one, otherwise the configured value' — is ALREADY disclosed in the public problem_statement, which explicitly proposes the exact gold edit: 'fit takes a default value of None and only overwrites the existing value if the user has explicitly passed it as an argument.' Thus the spec view reveals nothing about the gold edit beyond the public problem_statement. Lexical G-LEAK screen (leakage.screen over the spec view against patch + problem_statement, hints excluded) also returns passed=True with zero hard failures and zero warnings, corroborating the semantic judgment. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
