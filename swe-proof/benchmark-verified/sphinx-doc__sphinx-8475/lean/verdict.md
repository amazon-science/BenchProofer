# P2 adversarial audit — sphinx-doc__sphinx-8475

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_probeUri light full result := result = (if retryWithFull light then full else light) is a FUNCTIONAL equality: for every (light, full) pair over the finite 4x4 ReqOutcome enum it pins result to a single determined value. Any implementation whose correct_probeUri closes must therefore return exactly that value on every input, i.e. be extensionally identical to the gold post-patch behavior (retry iff light in {statusError, redirectLoop} == except (HTTPError, TooManyRedirects)). No closing-but-divergent implementation exists, hence no closing-but-non-resolving one. All 7 distinct wrong impls leave a decidably-false goal at their discriminating input (decide proved the proposition False), so none closes; there is no verifying wrong impl to materialize a patch for. verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,9 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  match light with
+  | ReqOutcome.statusError => full
+  | _                      => light
 -- impl-end
 
 -- proof-start
@@ -78,6 +76,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,11 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  match light with
+  | ReqOutcome.statusError  => full
+  | ReqOutcome.redirectLoop => full
+  | ReqOutcome.otherFailure => full
+  | ReqOutcome.ok           => light
 -- impl-end
 
 -- proof-start
@@ -78,6 +78,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,9 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  match light with
+  | ReqOutcome.redirectLoop => full
+  | _                       => light
 -- impl-end
 
 -- proof-start
@@ -78,6 +76,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  light
 -- impl-end
 
 -- proof-start
@@ -78,6 +74,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  full
 -- impl-end
 
 -- proof-start
@@ -78,6 +74,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,7 @@
     let mut response := light
     if retryWithFull light then
       response := full
+    response := light
     return response
 -- impl-end
 
@@ -78,6 +79,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
 
 -- impl-start
 def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
-  Id.run do
-    let mut response := light
-    if retryWithFull light then
-      response := full
-    return response
+  if retryWithFull light then light else full
 -- impl-end
 
 -- proof-start
@@ -78,6 +74,7 @@
     ∀ (light full : ReqOutcome),
       problem_spec_probeUri light full (implementation_probeUri light full) := by
   intro light full
-  unfold problem_spec_probeUri implementation_probeUri
-  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
+  cases light <;> cases full <;>
+    simp_all [problem_spec_probeUri, implementation_probeUri, retryWithFull, Id.run] <;>
+    decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Probing a URL with a lightweight request and a full-request fallback.

To check whether a link works, a lightweight probe is attempted first (it is
easier on the server and the network than downloading the whole resource). That
probe can finish in one of several ways:

  * it succeeds and yields a usable response;
  * it fails with an HTTP status error (the server answered, but with an error
    status);
  * it fails because the server keeps redirecting without ever settling — a
    redirect loop;
  * it fails for some other reason (the connection could not be established, the
    certificate was rejected, and so on).

When the lightweight probe fails with a *retryable* condition — an HTTP status
error, OR a redirect loop (some servers only loop on the lightweight probe and
answer a full request fine) — the check falls back to a full request and reports
that request's outcome instead. Any other failure is reported as-is; a successful
probe is reported as-is.

We model the surviving outcome as `ReqOutcome`. The result is fully determined by
the two probe outcomes (the lightweight one and the fallback one): it is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome otherwise.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the two request outcomes are the
-- modeled function's INPUTS (the network results), and the retry decision is
-- modeled deeply in the `pure` region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- The possible outcomes of a single network probe. `ok` is a usable response;
the others are the distinct failure modes that the decision below treats
differently. -/
inductive ReqOutcome where
  | ok             -- a usable response was obtained
  | statusError    -- the server answered with an error status
  | redirectLoop   -- the server kept redirecting without settling
  | otherFailure   -- any other failure (connection, certificate, …)
deriving DecidableEq, Repr, Inhabited

/-- Whether a failed lightweight probe should be retried with a full request.
A retry is warranted for an HTTP status error and for a redirect loop; every
other outcome (including success) is not retried. -/
def retryWithFull : ReqOutcome → Bool
  | ReqOutcome.statusError  => true
  | ReqOutcome.redirectLoop => true
  | _                       => false
-- pure-end

-- post-conditions-start
/-- The surviving outcome of probing a URL. `light` is the lightweight probe's
outcome and `full` is the fallback full-request outcome. The result is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome itself otherwise. -/
def problem_spec_probeUri
    (light full : ReqOutcome) (result : ReqOutcome) : Prop :=
  result = if retryWithFull light then full else light
-- post-conditions-end

-- impl-start
def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
  Id.run do
    let mut response := light
    if retryWithFull light then
      response := full
    return response
-- impl-end

-- proof-start
theorem correct_probeUri :
    ∀ (light full : ReqOutcome),
      problem_spec_probeUri light full (implementation_probeUri light full) := by
  intro light full
  unfold problem_spec_probeUri implementation_probeUri
  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Scratch dir same_spec(Solution.lean, atk_N)=True for ALL 7 attacks + positive control + gold-closer sanity file (verified via swebench_unified.markers.same_spec, lean backend). Only the impl+proof regions edited; axioms/pure/pre/post byte-identical.

CLOSER VALIDITY. First pass used top-level `decide`, which FAILED even on wrong impls only because ReqOutcome has no Fintype (failed to synthesize Decidable for the forall) — an inconclusive closer, so discarded. Final closer = `intro light full; cases light <;> cases full <;> simp_all [...] <;> decide`, which reduces each of the 16 concrete (light,full) goals to a decidable equality. Validity confirmed two ways: (a) gold impl carried in Solution.lean verifies exit 0 (atk_pos); (b) gold impl re-proved with the SAME strong closer verifies exit 0 (atk_goldcloser). So the closer closes IFF the impl matches the spec.

 Verify: `bash scripts/lean_verify.sh <D>/<f>.lean`. Run concurrently in 2 batches of 4 (<=4 rule).
  RESULTS (exit code):
  atk_pos (gold, carried proof)        = 0  VERIFIES
  atk_goldcloser (gold, strong closer) = 0  VERIFIES (closer valid)
  atk1 prepatch bug: retry statusError only          = 1  FAILS (decide: goal False at light=redirectLoop,full=ok)
  atk2 over-retry: also retry otherFailure           = 1  FAILS
  atk3 boundary swap: retry redirectLoop only         = 1  FAILS
  atk4 never retry: return light always               = 1  FAILS
  atk5 always full                                    = 1  FAILS
  atk6 control-flow-effect: set full then clobber to light = 1  FAILS
  atk7 ungrounded-oracle echo: negated cond (full when NOT retry) = 1  FAILS
  All 7 failure logs show `error: Tactic \`decide\` proved that the proposition ... False` — genuine unsolvable goals, NOT synth artifacts.

ATTACK FAMILIES COVERED: prepatch bug (atk1), partial-domain/boundary (atk3), over-retry/wrong-domain (atk2), degenerate constants (atk4,atk5), control-flow-effect ordering (atk6), ungrounded/negated echo (atk7). 7 distinct wrong impls > the >=5-6 requirement.

STEP 2 (materialize+resolve): VACUOUS. No wrong impl has a closing clean-axiom proof, so there is no faithful patch to run through run_resolve. verify => correct is not falsified.

AXIOMS. Solution.lean axioms region is an empty comment (grep: no `axiom`/`opaque` decls). Positive control `#print axioms correct_probeUri` => `[propext]` only (no sorryAx, no user axioms, no Classical.choice). Clean.

A-LEG / refinement.md AUDIT. refinement.md legs: #1,#2,#3 tagged R (type refinement of ReqOutcome for the two network-outcome INPUTS and the surviving-response output); #4,#5,#6 tagged I (deep model of the changed control-flow decision). There are NO A-consumed and NO A-reference legs — consistent with the empty axioms region and G-AX being a legitimate skip stub (no unchanged pure callee is consumed). No kind-3 (unmodeled/opaque-oracle) leg. The one deep-modeled decision `retryWithFull light` (true iff light in {statusError,redirectLoop}) corresponds EXACTLY to the post-patch `except (HTTPError, TooManyRedirects)` clause under the mapping.md bijection (statusError<->HTTPError, redirectLoop<->TooManyRedirects); ok/otherFailure not caught => no retry. This correspondence is the actual edited line (`except HTTPError` -> `except (HTTPError, TooManyRedirects)` at linkcheck.py:174). G-CONF exhaustively differential-tests this R/I decision against a real-`requests.exceptions` in-process replica (conformance_check.py, seed 8475, 4x4 exhaustive + 120k fuzz). A-leg correspondence holds.

CONCLUSION: functional spec admits no wrong closing impl; A/R/I decomposition is sound with no kind-3 and correct deep-model<->callee correspondence. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_probeUri light full result := result = (if retryWithFull light then full else light) is a FUNCTIONAL equality: for every (light, full) pair over the finite 4x4 ReqOutcome enum it pins result to a single determined value. Any implementation whose correct_probeUri closes must therefore return exactly that value on every input, i.e. be extensionally identical to the gold post-patch behavior (retry iff light in {statusError, redirectLoop} == except (HTTPError, TooManyRedirects)). No closing-but-divergent implementation exists, hence no closing-but-non-resolving one. All 7 distinct wrong impls leave a decidably-false goal at their discriminating input (decide proved the proposition False), so none closes; there is no verifying wrong impl to materialize a patch for. verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Probing a URL with a lightweight request and a full-request fallback.

To check whether a link works, a lightweight probe is attempted first (it is
easier on the server and the network than downloading the whole resource). That
probe can finish in one of several ways:

  * it succeeds and yields a usable response;
  * it fails with an HTTP status error (the server answered, but with an error
    status);
  * it fails because the server keeps redirecting without ever settling — a
    redirect loop;
  * it fails for some other reason (the connection could not be established, the
    certificate was rejected, and so on).

When the lightweight probe fails with a *retryable* condition — an HTTP status
error, OR a redirect loop (some servers only loop on the lightweight probe and
answer a full request fine) — the check falls back to a full request and reports
that request's outcome instead. Any other failure is reported as-is; a successful
probe is reported as-is.

We model the surviving outcome as `ReqOutcome`. The result is fully determined by
the two probe outcomes (the lightweight one and the fallback one): it is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome otherwise.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the two request outcomes are the
-- modeled function's INPUTS (the network results), and the retry decision is
-- modeled deeply in the `pure` region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- The possible outcomes of a single network probe. `ok` is a usable response;
the others are the distinct failure modes that the decision below treats
differently. -/
inductive ReqOutcome where
  | ok             -- a usable response was obtained
  | statusError    -- the server answered with an error status
  | redirectLoop   -- the server kept redirecting without settling
  | otherFailure   -- any other failure (connection, certificate, …)
deriving DecidableEq, Repr, Inhabited

/-- Whether a failed lightweight probe should be retried with a full request.
A retry is warranted for an HTTP status error and for a redirect loop; every
other outcome (including success) is not retried. -/
def retryWithFull : ReqOutcome → Bool
  | ReqOutcome.statusError  => true
  | ReqOutcome.redirectLoop => true
  | _                       => false
-- pure-end

-- post-conditions-start
/-- The surviving outcome of probing a URL. `light` is the lightweight probe's
outcome and `full` is the fallback full-request outcome. The result is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome itself otherwise. -/
def problem_spec_probeUri
    (light full : ReqOutcome) (result : ReqOutcome) : Prop :=
  result = if retryWithFull light then full else light
-- post-conditions-end

-- impl-start
def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
  Id.run do
    let mut response := light
    if retryWithFull light then
      response := full
    return response
-- impl-end

-- proof-start
theorem correct_probeUri :
    ∀ (light full : ReqOutcome),
      problem_spec_probeUri light full (implementation_probeUri light full) := by
  intro light full
  unfold problem_spec_probeUri implementation_probeUri
  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Scratch dir same_spec(Solution.lean, atk_N)=True for ALL 7 attacks + positive control + gold-closer sanity file (verified via swebench_unified.markers.same_spec, lean backend). Only the impl+proof regions edited; axioms/pure/pre/post byte-identical.

CLOSER VALIDITY. First pass used top-level `decide`, which FAILED even on wrong impls only because ReqOutcome has no Fintype (failed to synthesize Decidable for the forall) — an inconclusive closer, so discarded. Final closer = `intro light full; cases light <;> cases full <;> simp_all [...] <;> decide`, which reduces each of the 16 concrete (light,full) goals to a decidable equality. Validity confirmed two ways: (a) gold impl carried in Solution.lean verifies exit 0 (atk_pos); (b) gold impl re-proved with the SAME strong closer verifies exit 0 (atk_goldcloser). So the closer closes IFF the impl matches the spec.

 Verify: `bash scripts/lean_verify.sh <D>/<f>.lean`. Run concurrently in 2 batches of 4 (<=4 rule).
  RESULTS (exit code):
  atk_pos (gold, carried proof)        = 0  VERIFIES
  atk_goldcloser (gold, strong closer) = 0  VERIFIES (closer valid)
  atk1 prepatch bug: retry statusError only          = 1  FAILS (decide: goal False at light=redirectLoop,full=ok)
  atk2 over-retry: also retry otherFailure           = 1  FAILS
  atk3 boundary swap: retry redirectLoop only         = 1  FAILS
  atk4 never retry: return light always               = 1  FAILS
  atk5 always full                                    = 1  FAILS
  atk6 control-flow-effect: set full then clobber to light = 1  FAILS
  atk7 ungrounded-oracle echo: negated cond (full when NOT retry) = 1  FAILS
  All 7 failure logs show `error: Tactic \`decide\` proved that the proposition ... False` — genuine unsolvable goals, NOT synth artifacts.

ATTACK FAMILIES COVERED: prepatch bug (atk1), partial-domain/boundary (atk3), over-retry/wrong-domain (atk2), degenerate constants (atk4,atk5), control-flow-effect ordering (atk6), ungrounded/negated echo (atk7). 7 distinct wrong impls > the >=5-6 requirement.

STEP 2 (materialize+resolve): VACUOUS. No wrong impl has a closing clean-axiom proof, so there is no faithful patch to run through run_resolve. verify => correct is not falsified.

AXIOMS. Solution.lean axioms region is an empty comment (grep: no `axiom`/`opaque` decls). Positive control `#print axioms correct_probeUri` => `[propext]` only (no sorryAx, no user axioms, no Classical.choice). Clean.

A-LEG / refinement.md AUDIT. refinement.md legs: #1,#2,#3 tagged R (type refinement of ReqOutcome for the two network-outcome INPUTS and the surviving-response output); #4,#5,#6 tagged I (deep model of the changed control-flow decision). There are NO A-consumed and NO A-reference legs — consistent with the empty axioms region and G-AX being a legitimate skip stub (no unchanged pure callee is consumed). No kind-3 (unmodeled/opaque-oracle) leg. The one deep-modeled decision `retryWithFull light` (true iff light in {statusError,redirectLoop}) corresponds EXACTLY to the post-patch `except (HTTPError, TooManyRedirects)` clause under the mapping.md bijection (statusError<->HTTPError, redirectLoop<->TooManyRedirects); ok/otherFailure not caught => no retry. This correspondence is the actual edited line (`except HTTPError` -> `except (HTTPError, TooManyRedirects)` at linkcheck.py:174). G-CONF exhaustively differential-tests this R/I decision against a real-`requests.exceptions` in-process replica (conformance_check.py, seed 8475, 4x4 exhaustive + 120k fuzz). A-leg correspondence holds.

CONCLUSION: functional spec admits no wrong closing impl; A/R/I decomposition is sound with no kind-3 and correct deep-model<->callee correspondence. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True, Lean backend). Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_probeUri => [propext] only, no sorryAx (proof is genuine, not faked). Patch confirmed: base_commit linkcheck.py:174 `except HTTPError` -> post-patch `except (HTTPError, TooManyRedirects)`; the HEAD-probe->GET-fallback block and unchanged downstream classification verified against the base_commit source (git show 3ea1ec84...) and a post-patch worktree. Faithfulness proven exhaustively: transliterated the REAL post-patch fragment with the actual requests.exceptions classes (verified TooManyRedirects is NOT a subclass of HTTPError, so the enum<->exception bijection is non-trivial) and compared the surviving-outcome against problem_spec_probeUri over all 16 (light,full) pairs -> 0 divergences. conformance_check.py ran 120016 cases against the in-repo requests library -> 0 disagreements. The modeled function agrees with the real callee on every input; the modeling boundary is honest (light/full are genuine network inputs, retryWithFull is modeled deeply not axiomatized, G-AX skip is justified). Spec is not too strong and does not drift from real repo behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) => True (spec region byte-identical; the buggy prepatch bundle carries the SAME spec view, so the spec view itself does not encode the fix in a distinguishing way). Rendered spec_view line-by-line: it comprises only (1) a doc comment, (2) empty axioms region, (3) the 4-constructor ReqOutcome enum, (4) retryWithFull = true for {statusError, redirectLoop}, and (5) postcondition problem_spec_probeUri = (if retryWithFull light then full else light). impl and proof are elided.

Gold edit = `except HTTPError:` -> `except (HTTPError, TooManyRedirects):` in sphinx/builders/linkcheck.py (retry GET fallback also on a HEAD redirect loop).

The PUBLIC problem_statement already discloses this fix explicitly and in more concrete terms than the spec view: title 'fallback to GET requests when HEAD requests returns Too Many Redirects'; body names the `TooManyRedirects` exception type, states the GET fallback is currently skipped for it, and says 'This extends the except clause to retry with a GET request for such scenarios.' hints_text is empty (not relied upon).

The spec view encodes correct post-patch behavior (any valid spec must) but STRICTLY MORE ABSTRACTLY than the public statement: generic 'redirect loop' constructor over a 4-value enum, NO `requests.exceptions.TooManyRedirects` class name, NO `except` syntax, NO file/line reference. It reveals nothing about the gold edit beyond the public problem_statement; if anything it discloses less. G-LEAK lexical screen also passes (no gold/PS phrasing quoted). No spec-view line leaks the edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
