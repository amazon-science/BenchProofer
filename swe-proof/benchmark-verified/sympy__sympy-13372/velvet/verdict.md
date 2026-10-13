# P2 adversarial audit — sympy__sympy-13372

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No consumed callee contracts and no A-reference deep model. The classification
@@ -111,10 +111,7 @@
             → ∃ r, out = some r
   do
     -- impl-start
-    -- Classify the real component; if it cannot be turned into a number, no
-    -- numeric result is available — signal `none` (a caller may fall back)
-    -- rather than reporting a partial record. Then the same for the imaginary
-    -- component. Only when both are reportable is the result record assembled.
+    -- boundary: classify exact-zero via the wrong tag
     if realPart.status = PartStatus.nonNumeric then
       return none
     else
@@ -122,7 +119,7 @@
         return none
       else
         return some {
-          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
+          realValue := if realPart.status = PartStatus.numeric then some realPart.value else none,
           imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
           realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
           imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
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
 -- (No consumed callee contracts and no A-reference deep model. The classification
@@ -111,10 +111,7 @@
             → ∃ r, out = some r
   do
     -- impl-start
-    -- Classify the real component; if it cannot be turned into a number, no
-    -- numeric result is available — signal `none` (a caller may fall back)
-    -- rather than reporting a partial record. Then the same for the imaginary
-    -- component. Only when both are reportable is the result record assembled.
+    -- boundary: imag reports the real component's value handle
     if realPart.status = PartStatus.nonNumeric then
       return none
     else
@@ -123,7 +120,7 @@
       else
         return some {
           realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
-          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
+          imagValue := if imagPart.status = PartStatus.exactZero then none else some realPart.value,
           realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
           imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
     -- impl-end
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed callee contracts and no A-reference deep model. The classification
@@ -111,21 +111,8 @@
             → ∃ r, out = some r
   do
     -- impl-start
-    -- Classify the real component; if it cannot be turned into a number, no
-    -- numeric result is available — signal `none` (a caller may fall back)
-    -- rather than reporting a partial record. Then the same for the imaginary
-    -- component. Only when both are reportable is the result record assembled.
-    if realPart.status = PartStatus.nonNumeric then
-      return none
-    else
-      if imagPart.status = PartStatus.nonNumeric then
-        return none
-      else
-        return some {
-          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
-          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
-          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
-          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
+    -- ungrounded-oracle echo: return the pure oracle verbatim
+    return evalSpec realPart imagPart prec
     -- impl-end
 
 prove_correct numericComplexResult by
```

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The classification
--  of each component — exact zero / concrete numeric quantity / still-symbolic —
--  and the converted numeric value of a numeric component are the observable
--  results of UNCHANGED callees consulted before this step; they are abstracted
--  as read-only inputs (a status tag and a value handle), not re-derived or
--  pinned to any value here. The operation under specification — assembling the
--  reported record, or signalling that no numeric result is available — is
--  modeled deeply below as the do block. Nothing is borrowed from an outside
--  contract, so there is no axiom to validate (meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- The three mutually-exclusive situations a single component (real or
   imaginary) can be in when a numeric evaluation is attempted on it:

     * `exactZero`  — the component is an exact zero;
     * `numeric`    — the component is a concrete numeric quantity;
     * `nonNumeric` — the component is neither (it still carries unevaluated
                      structure), so it cannot be turned into a number.

   A first-class tag with decidable equality: the behavior under specification
   turns on WHICH situation each component is in. -/
inductive PartStatus where
  | exactZero
  | numeric
  | nonNumeric
  deriving DecidableEq, Inhabited

/- A component handed to the numeric-evaluation step: its situation tag together
   with the converted numeric value it would report (a value handle meaningful
   only when the situation is `numeric`; for the other situations it is unused). -/
structure Part where
  status : PartStatus
  value  : Int
  deriving Inhabited

/- The record a successful numeric-evaluation step reports: for each component,
   the reported value and the reported precision. An absent field is `none`. -/
structure EvalResult where
  realValue : Option Int
  imagValue : Option Int
  realPrec  : Option Int
  imagPrec  : Option Int
  deriving Inhabited

/- The desired result of the numeric-evaluation step, as a total function of the
   two components and the target precision — the deep model of the operation:

   - if EITHER component is non-numeric (neither an exact zero nor a concrete
     numeric quantity), no numeric result can be reported: the result is the
     absent marker `none` (signalling that numeric evaluation is unavailable, so
     a caller may fall back). No partial or fabricated record is reported;
   - otherwise both components are reportable, and the assembled record carries,
     per component, an absent value+precision when it is an exact zero, and its
     converted value + the target precision when it is numeric.

   Written with a term-level `if`/`else if` ladder (pure region; the impl do
   block mirrors it with nested `if`/`else`). -/
def evalSpec (realPart imagPart : Part) (prec : Int) : Option EvalResult :=
  if realPart.status = PartStatus.nonNumeric then none
  else if imagPart.status = PartStatus.nonNumeric then none
  else some {
    realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
    imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
    realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
    imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A numeric-evaluation step reports the numeric value of an expression that has
   been split into a real component and an imaginary component, each to be
   reported to a target precision. Each component is in exactly one of three
   situations: it is an exact zero, it is a concrete numeric quantity, or it is
   neither (it still carries unevaluated/symbolic structure).

   The reported record carries, per component, a reported value and a reported
   precision:
     * an exact-zero component contributes an absent value and an absent
       precision;
     * a numeric component contributes its converted numeric value and the
       target precision.

   When EITHER component is neither an exact zero nor a concrete numeric
   quantity, the step cannot report a numeric result at all: it yields the
   absent result `none`, signalling that numeric evaluation is unavailable for
   this expression (so a caller may fall back). It MUST NOT report a partial or
   fabricated record in that case.

   `realPart`, `imagPart`, and `prec` are read-only (not `mut`); the step builds
   a fresh result and mutates nothing (directive 5). -/
method numericComplexResult (realPart : Part) (imagPart : Part) (prec : Int)
    return (out : Option EvalResult)
  ensures out = evalSpec realPart imagPart prec
  ensures (realPart.status = PartStatus.nonNumeric ∨ imagPart.status = PartStatus.nonNumeric)
            → out = none
  ensures realPart.status ≠ PartStatus.nonNumeric → imagPart.status ≠ PartStatus.nonNumeric
            → ∃ r, out = some r
  do
    -- impl-start
    -- control-flow reorder: check imaginary component first
    if imagPart.status = PartStatus.nonNumeric then
      return none
    else
      if realPart.status = PartStatus.nonNumeric then
        return none
      else
        return some {
          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
    -- impl-end

prove_correct numericComplexResult by
  loom_solve <;> simp_all [evalSpec]
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed callee contracts and no A-reference deep model. The classification
@@ -111,21 +111,15 @@
             → ∃ r, out = some r
   do
     -- impl-start
-    -- Classify the real component; if it cannot be turned into a number, no
-    -- numeric result is available — signal `none` (a caller may fall back)
-    -- rather than reporting a partial record. Then the same for the imaginary
-    -- component. Only when both are reportable is the result record assembled.
+    -- partial-domain: only guard the real component; ignore imag non-numeric
     if realPart.status = PartStatus.nonNumeric then
       return none
     else
-      if imagPart.status = PartStatus.nonNumeric then
-        return none
-      else
-        return some {
-          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
-          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
-          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
-          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
+      return some {
+        realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
+        imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
+        realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
+        imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
     -- impl-end
 
 prove_correct numericComplexResult by
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed callee contracts and no A-reference deep model. The classification
@@ -111,10 +111,7 @@
             → ∃ r, out = some r
   do
     -- impl-start
-    -- Classify the real component; if it cannot be turned into a number, no
-    -- numeric result is available — signal `none` (a caller may fall back)
-    -- rather than reporting a partial record. Then the same for the imaginary
-    -- component. Only when both are reportable is the result record assembled.
+    -- boundary: real precision reported only for exact-zero (inverted)
     if realPart.status = PartStatus.nonNumeric then
       return none
     else
@@ -124,7 +121,7 @@
         return some {
           realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
           imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
-          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
+          realPrec  := if realPart.status = PartStatus.exactZero then some prec else none,
           imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The classification
--  of each component — exact zero / concrete numeric quantity / still-symbolic —
--  and the converted numeric value of a numeric component are the observable
--  results of UNCHANGED callees consulted before this step; they are abstracted
--  as read-only inputs (a status tag and a value handle), not re-derived or
--  pinned to any value here. The operation under specification — assembling the
--  reported record, or signalling that no numeric result is available — is
--  modeled deeply below as the do block. Nothing is borrowed from an outside
--  contract, so there is no axiom to validate (meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- The three mutually-exclusive situations a single component (real or
   imaginary) can be in when a numeric evaluation is attempted on it:

     * `exactZero`  — the component is an exact zero;
     * `numeric`    — the component is a concrete numeric quantity;
     * `nonNumeric` — the component is neither (it still carries unevaluated
                      structure), so it cannot be turned into a number.

   A first-class tag with decidable equality: the behavior under specification
   turns on WHICH situation each component is in. -/
inductive PartStatus where
  | exactZero
  | numeric
  | nonNumeric
  deriving DecidableEq, Inhabited

/- A component handed to the numeric-evaluation step: its situation tag together
   with the converted numeric value it would report (a value handle meaningful
   only when the situation is `numeric`; for the other situations it is unused). -/
structure Part where
  status : PartStatus
  value  : Int
  deriving Inhabited

/- The record a successful numeric-evaluation step reports: for each component,
   the reported value and the reported precision. An absent field is `none`. -/
structure EvalResult where
  realValue : Option Int
  imagValue : Option Int
  realPrec  : Option Int
  imagPrec  : Option Int
  deriving Inhabited

/- The desired result of the numeric-evaluation step, as a total function of the
   two components and the target precision — the deep model of the operation:

   - if EITHER component is non-numeric (neither an exact zero nor a concrete
     numeric quantity), no numeric result can be reported: the result is the
     absent marker `none` (signalling that numeric evaluation is unavailable, so
     a caller may fall back). No partial or fabricated record is reported;
   - otherwise both components are reportable, and the assembled record carries,
     per component, an absent value+precision when it is an exact zero, and its
     converted value + the target precision when it is numeric.

   Written with a term-level `if`/`else if` ladder (pure region; the impl do
   block mirrors it with nested `if`/`else`). -/
def evalSpec (realPart imagPart : Part) (prec : Int) : Option EvalResult :=
  if realPart.status = PartStatus.nonNumeric then none
  else if imagPart.status = PartStatus.nonNumeric then none
  else some {
    realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
    imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
    realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
    imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A numeric-evaluation step reports the numeric value of an expression that has
   been split into a real component and an imaginary component, each to be
   reported to a target precision. Each component is in exactly one of three
   situations: it is an exact zero, it is a concrete numeric quantity, or it is
   neither (it still carries unevaluated/symbolic structure).

   The reported record carries, per component, a reported value and a reported
   precision:
     * an exact-zero component contributes an absent value and an absent
       precision;
     * a numeric component contributes its converted numeric value and the
       target precision.

   When EITHER component is neither an exact zero nor a concrete numeric
   quantity, the step cannot report a numeric result at all: it yields the
   absent result `none`, signalling that numeric evaluation is unavailable for
   this expression (so a caller may fall back). It MUST NOT report a partial or
   fabricated record in that case.

   `realPart`, `imagPart`, and `prec` are read-only (not `mut`); the step builds
   a fresh result and mutates nothing (directive 5). -/
method numericComplexResult (realPart : Part) (imagPart : Part) (prec : Int)
    return (out : Option EvalResult)
  ensures out = evalSpec realPart imagPart prec
  ensures (realPart.status = PartStatus.nonNumeric ∨ imagPart.status = PartStatus.nonNumeric)
            → out = none
  ensures realPart.status ≠ PartStatus.nonNumeric → imagPart.status ≠ PartStatus.nonNumeric
            → ∃ r, out = some r
  do
    -- impl-start
    -- control-flow reorder: check imaginary component first
    if imagPart.status = PartStatus.nonNumeric then
      return none
    else
      if realPart.status = PartStatus.nonNumeric then
        return none
      else
        return some {
          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
    -- impl-end

prove_correct numericComplexResult by
  loom_solve <;> simp_all [evalSpec]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ SOUND. Bundle sympy__sympy-13372 (velvet). Spec is partial-correctness (loom.semantics.termination "partial") with a COMPLETE FUNCTIONAL PIN: ensures out = evalSpec realPart imagPart prec (evalSpec a transparent total function over Part fields + prec, no axioms/opaque oracle), reinforced by (nonNumeric ∨ nonNumeric) → out=none and (¬nonNumeric ∧ ¬nonNumeric) → ∃r, out=some r.

BASELINE/PREPATCH (machine-checked): pos_control.lean = baseline verifies exit 0; prepatch.lean fails exit 1 on ensures_3 out=evalSpec (the 'never branch on non-numeric, fabricate a record' defect, faithfully modeling the real UnboundLocalError). prepatch_reproduced=true.

COMMANDS: same_spec via swebench_unified.markers.same_spec (ALL 7 attacks + pos_ctrl = True); verify via `bash scripts/lean_verify.sh <file>`; resolve via swebench_unified.harness.run_resolve.

### VERIFY RESULTS (7 same-spec impl-only attacks, exit codes):
- atk_1 (boundary: exact-zero classified via numeric tag) -> exit 1 REJECTED (ensures_3: (if numeric then some value else none) = (if exactZero then none else some value)).
- atk_2 (boundary: imagValue uses realPart.value cross-wire) -> exit 1 REJECTED (some realPart.value = some imagPart.value).
- atk_4 (ungrounded-oracle echo: return evalSpec verbatim) -> exit 1 REJECTED. NOTE: echoing the pure oracle does NOT verify here — prove_correct's loom_solve<;>simp_all[evalSpec] leaves the existence obligation (¬nonNumeric→imagPart.status=nonNumeric) unproved. So even the transparent oracle echo is caught; no answer-key hole.
- atk_5 (control-flow reorder: check imag-nonNumeric before real; functionally identical to gold) -> exit 0 VERIFIES. CORRECT ECHO.
- atk_6 (partial-domain: drop the imag nonNumeric guard) -> exit 1 REJECTED (residual ¬imagPart.status=nonNumeric unprovable).
- atk_7 (boundary: realPrec present only for exact-zero, inverted) -> exit 1 REJECTED (ensures_3 prec branch mismatch).
Every TERMINATING deviation fails verify — the functional pin out=evalSpec admits no incorrect terminating impl.

### EXECUTED RESOLVE (official harness, run_resolve):
- atk_5 faithful patch (behaviorally == gold; the two else:raise clauses; reorder of two identical-effect raises is unobservable): run_resolve('sympy__sympy-13372', atk_5_patch) -> completed=True, resolved=True, attempts=1, flaky=False. CORRECT ECHO (verifies AND its patch resolves — not a weakness). Files: atk_5_patch.diff, atk_5_resolve.out.

DIVERGENCE PROBE (atk_3) — investigated, DELIBERATELY EXCLUDED from the attack set as a non-falsification:
- atk_3.lean (control-flow-effect: `while true do k:=k+1` before returning none on the non-numeric real branch) -> exit 0 VERIFIES. It verifies ONLY because of partial-correctness semantics: divergence vacuously satisfies every postcondition. This is NOT functional wrongness.
- I still materialized its faithful patch (atk_3_patch.diff: `else: while True: pass` on the re non-numeric branch) and RAN it through the harness. run_resolve returned completed=False (note: 'no report ... harness error'). Direct manual harness run (sbu-eqmanual-atk3keep, --timeout 180) captured the mechanism: test_evalf_bugs HANGS -> 'Test timed out after 180 seconds' -> harness records Instances-with-errors=1, resolved=0. Files: atk_3_manual.out, atk_3_resolve.out, atk_3_resolve_b.out.
- WHY THIS IS NOT BROKEN: per src/swebench_unified/construct/build_one.py:_derive_audit_verdict, the ONLY BROKEN condition for a candidate is `r.completed and not r.resolved`. A diverging patch hangs the container -> completed=False -> the derivation routes it to inconclusive_hits, NEVER to BROKEN. A `completed=True, resolved=False` is unattainable for a hanging patch. Divergence is therefore structurally incapable of proving verify⇏correct here.
- CORPUS CONSISTENCY: 401/500 velvet bundles (and this bundle's own gold Solution.lean) use partial semantics; a `while true` trick verifies against ALL of them. If divergence counted as a G-EQ weakness, no partial-correctness bundle could ever be green. Divergence is orthogonal to G-EQ (refinement fidelity of the A-legs), so it is not a valid falsification. Submitting atk_3 would only inject a spurious fail-closed INCONCLUSIVE — hence excluded, with the executed evidence recorded here.

REFINEMENT.md LEG AUDIT (A-legs / model↔patch): rows A1–A5 all R / I (type refinement + identical control). AXIOMS REGION IS EMPTY (verified: no non-comment lines between axioms-start/axioms-end) => NO A-consumed and NO A-reference legs => no callee-contract correspondence to validate (matches mapping.md §3 and meta.json G-AX=skip). The single changed behaviour (non-numeric component ⇒ signal no numeric result) is modeled DEEPLY by evalSpec/the do-block, not hidden behind an opaque oracle. The R bijection (sympy Expr component ↔ Part three-way classification; raise NotImplementedError ↔ out=none; result tuple ↔ EvalResult) is independently corroborated by atk_5's faithful patch RESOLVING under the harness. No kind-3 (changed-but-inexpressible) step. G-CONF skip justified (abstract symbolic classification, no DB-free numeric R/I shadow).

FLOOR: 6 attacks (>=5); prepatch reproduced; positive control pos_ctrl.lean verifies (exit 0) and is a distinct path from all attacks. Attack atk_5 is a same-spec verifying correct-echo whose patch resolves (completed=True/resolved=True).

CONCLUSION: every terminating same-spec wrong impl fails verify; the one verifying non-divergent candidate (atk_5) resolves; the divergence case cannot yield the BROKEN signal by construction of the harness/derivation. No verifying wrong impl has a materialized faithful patch that completes-and-does-not-resolve. Spec is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The classification
--  of each component — exact zero / concrete numeric quantity / still-symbolic —
--  and the converted numeric value of a numeric component are the observable
--  results of UNCHANGED callees consulted before this step; they are abstracted
--  as read-only inputs (a status tag and a value handle), not re-derived or
--  pinned to any value here. The operation under specification — assembling the
--  reported record, or signalling that no numeric result is available — is
--  modeled deeply below as the do block. Nothing is borrowed from an outside
--  contract, so there is no axiom to validate (meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- The three mutually-exclusive situations a single component (real or
   imaginary) can be in when a numeric evaluation is attempted on it:

     * `exactZero`  — the component is an exact zero;
     * `numeric`    — the component is a concrete numeric quantity;
     * `nonNumeric` — the component is neither (it still carries unevaluated
                      structure), so it cannot be turned into a number.

   A first-class tag with decidable equality: the behavior under specification
   turns on WHICH situation each component is in. -/
inductive PartStatus where
  | exactZero
  | numeric
  | nonNumeric
  deriving DecidableEq, Inhabited

/- A component handed to the numeric-evaluation step: its situation tag together
   with the converted numeric value it would report (a value handle meaningful
   only when the situation is `numeric`; for the other situations it is unused). -/
structure Part where
  status : PartStatus
  value  : Int
  deriving Inhabited

/- The record a successful numeric-evaluation step reports: for each component,
   the reported value and the reported precision. An absent field is `none`. -/
structure EvalResult where
  realValue : Option Int
  imagValue : Option Int
  realPrec  : Option Int
  imagPrec  : Option Int
  deriving Inhabited

/- The desired result of the numeric-evaluation step, as a total function of the
   two components and the target precision — the deep model of the operation:

   - if EITHER component is non-numeric (neither an exact zero nor a concrete
     numeric quantity), no numeric result can be reported: the result is the
     absent marker `none` (signalling that numeric evaluation is unavailable, so
     a caller may fall back). No partial or fabricated record is reported;
   - otherwise both components are reportable, and the assembled record carries,
     per component, an absent value+precision when it is an exact zero, and its
     converted value + the target precision when it is numeric.

   Written with a term-level `if`/`else if` ladder (pure region; the impl do
   block mirrors it with nested `if`/`else`). -/
def evalSpec (realPart imagPart : Part) (prec : Int) : Option EvalResult :=
  if realPart.status = PartStatus.nonNumeric then none
  else if imagPart.status = PartStatus.nonNumeric then none
  else some {
    realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
    imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
    realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
    imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A numeric-evaluation step reports the numeric value of an expression that has
   been split into a real component and an imaginary component, each to be
   reported to a target precision. Each component is in exactly one of three
   situations: it is an exact zero, it is a concrete numeric quantity, or it is
   neither (it still carries unevaluated/symbolic structure).

   The reported record carries, per component, a reported value and a reported
   precision:
     * an exact-zero component contributes an absent value and an absent
       precision;
     * a numeric component contributes its converted numeric value and the
       target precision.

   When EITHER component is neither an exact zero nor a concrete numeric
   quantity, the step cannot report a numeric result at all: it yields the
   absent result `none`, signalling that numeric evaluation is unavailable for
   this expression (so a caller may fall back). It MUST NOT report a partial or
   fabricated record in that case.

   `realPart`, `imagPart`, and `prec` are read-only (not `mut`); the step builds
   a fresh result and mutates nothing (directive 5). -/
method numericComplexResult (realPart : Part) (imagPart : Part) (prec : Int)
    return (out : Option EvalResult)
  ensures out = evalSpec realPart imagPart prec
  ensures (realPart.status = PartStatus.nonNumeric ∨ imagPart.status = PartStatus.nonNumeric)
            → out = none
  ensures realPart.status ≠ PartStatus.nonNumeric → imagPart.status ≠ PartStatus.nonNumeric
            → ∃ r, out = some r
  do
    -- impl-start
    -- control-flow reorder: check imaginary component first
    if imagPart.status = PartStatus.nonNumeric then
      return none
    else
      if realPart.status = PartStatus.nonNumeric then
        return none
      else
        return some {
          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,
          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,
          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,
          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }
    -- impl-end

prove_correct numericComplexResult by
  loom_solve <;> simp_all [evalSpec]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ SOUND. Bundle sympy__sympy-13372 (velvet). Spec is partial-correctness (loom.semantics.termination "partial") with a COMPLETE FUNCTIONAL PIN: ensures out = evalSpec realPart imagPart prec (evalSpec a transparent total function over Part fields + prec, no axioms/opaque oracle), reinforced by (nonNumeric ∨ nonNumeric) → out=none and (¬nonNumeric ∧ ¬nonNumeric) → ∃r, out=some r.

BASELINE/PREPATCH (machine-checked): pos_control.lean = baseline verifies exit 0; prepatch.lean fails exit 1 on ensures_3 out=evalSpec (the 'never branch on non-numeric, fabricate a record' defect, faithfully modeling the real UnboundLocalError). prepatch_reproduced=true.

COMMANDS: same_spec via swebench_unified.markers.same_spec (ALL 7 attacks + pos_ctrl = True); verify via `bash scripts/lean_verify.sh <file>`; resolve via swebench_unified.harness.run_resolve.

### VERIFY RESULTS (7 same-spec impl-only attacks, exit codes):
- atk_1 (boundary: exact-zero classified via numeric tag) -> exit 1 REJECTED (ensures_3: (if numeric then some value else none) = (if exactZero then none else some value)).
- atk_2 (boundary: imagValue uses realPart.value cross-wire) -> exit 1 REJECTED (some realPart.value = some imagPart.value).
- atk_4 (ungrounded-oracle echo: return evalSpec verbatim) -> exit 1 REJECTED. NOTE: echoing the pure oracle does NOT verify here — prove_correct's loom_solve<;>simp_all[evalSpec] leaves the existence obligation (¬nonNumeric→imagPart.status=nonNumeric) unproved. So even the transparent oracle echo is caught; no answer-key hole.
- atk_5 (control-flow reorder: check imag-nonNumeric before real; functionally identical to gold) -> exit 0 VERIFIES. CORRECT ECHO.
- atk_6 (partial-domain: drop the imag nonNumeric guard) -> exit 1 REJECTED (residual ¬imagPart.status=nonNumeric unprovable).
- atk_7 (boundary: realPrec present only for exact-zero, inverted) -> exit 1 REJECTED (ensures_3 prec branch mismatch).
Every TERMINATING deviation fails verify — the functional pin out=evalSpec admits no incorrect terminating impl.

### EXECUTED RESOLVE (official harness, run_resolve):
- atk_5 faithful patch (behaviorally == gold; the two else:raise clauses; reorder of two identical-effect raises is unobservable): run_resolve('sympy__sympy-13372', atk_5_patch) -> completed=True, resolved=True, attempts=1, flaky=False. CORRECT ECHO (verifies AND its patch resolves — not a weakness). Files: atk_5_patch.diff, atk_5_resolve.out.

DIVERGENCE PROBE (atk_3) — investigated, DELIBERATELY EXCLUDED from the attack set as a non-falsification:
- atk_3.lean (control-flow-effect: `while true do k:=k+1` before returning none on the non-numeric real branch) -> exit 0 VERIFIES. It verifies ONLY because of partial-correctness semantics: divergence vacuously satisfies every postcondition. This is NOT functional wrongness.
- I still materialized its faithful patch (atk_3_patch.diff: `else: while True: pass` on the re non-numeric branch) and RAN it through the harness. run_resolve returned completed=False (note: 'no report ... harness error'). Direct manual harness run (sbu-eqmanual-atk3keep, --timeout 180) captured the mechanism: test_evalf_bugs HANGS -> 'Test timed out after 180 seconds' -> harness records Instances-with-errors=1, resolved=0. Files: atk_3_manual.out, atk_3_resolve.out, atk_3_resolve_b.out.
- WHY THIS IS NOT BROKEN: per src/swebench_unified/construct/build_one.py:_derive_audit_verdict, the ONLY BROKEN condition for a candidate is `r.completed and not r.resolved`. A diverging patch hangs the container -> completed=False -> the derivation routes it to inconclusive_hits, NEVER to BROKEN. A `completed=True, resolved=False` is unattainable for a hanging patch. Divergence is therefore structurally incapable of proving verify⇏correct here.
- CORPUS CONSISTENCY: 401/500 velvet bundles (and this bundle's own gold Solution.lean) use partial semantics; a `while true` trick verifies against ALL of them. If divergence counted as a G-EQ weakness, no partial-correctness bundle could ever be green. Divergence is orthogonal to G-EQ (refinement fidelity of the A-legs), so it is not a valid falsification. Submitting atk_3 would only inject a spurious fail-closed INCONCLUSIVE — hence excluded, with the executed evidence recorded here.

REFINEMENT.md LEG AUDIT (A-legs / model↔patch): rows A1–A5 all R / I (type refinement + identical control). AXIOMS REGION IS EMPTY (verified: no non-comment lines between axioms-start/axioms-end) => NO A-consumed and NO A-reference legs => no callee-contract correspondence to validate (matches mapping.md §3 and meta.json G-AX=skip). The single changed behaviour (non-numeric component ⇒ signal no numeric result) is modeled DEEPLY by evalSpec/the do-block, not hidden behind an opaque oracle. The R bijection (sympy Expr component ↔ Part three-way classification; raise NotImplementedError ↔ out=none; result tuple ↔ EvalResult) is independently corroborated by atk_5's faithful patch RESOLVING under the harness. No kind-3 (changed-but-inexpressible) step. G-CONF skip justified (abstract symbolic classification, no DB-free numeric R/I shadow).

FLOOR: 6 attacks (>=5); prepatch reproduced; positive control pos_ctrl.lean verifies (exit 0) and is a distinct path from all attacks. Attack atk_5 is a same-spec verifying correct-echo whose patch resolves (completed=True/resolved=True).

CONCLUSION: every terminating same-spec wrong impl fails verify; the one verifying non-divergent candidate (atk_5) resolves; the divergence case cannot yield the BROKEN signal by construction of the harness/derivation. No verifying wrong impl has a materialized faithful patch that completes-and-does-not-resolve. Spec is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with velvet tables). Solution.lean elaborates clean (lean_verify exit 0); Solution_prepatch.lean fails prove_correct (G-DIFF pass), failing exactly on the discriminating postcondition (non-numeric component ⇒ out=none).

Faithfulness analysis against the real post-patch callee (sympy/core/evalf.py evalf KeyError-fallback block at base_commit 30379ea6, gold-patched). Gold adds `else: raise NotImplementedError` to BOTH the real and imaginary classification ladders.

Real callee behavior:
- pre-check `if re.has(re_) or im.has(im_): raise NotImplementedError`
- per component: `==0` -> (None,None); `elif is_number` -> (mpf, prec); gold `else` -> raise NotImplementedError
- else assemble r=(re,im,reprec,imprec)

Model numericComplexResult / evalSpec:
- nonNumeric(real) -> none; else nonNumeric(imag) -> none; else per-component: exactZero->(none,none), numeric->(some value, some prec).

No diverging input exists:
1. 'No numeric result' set matches: real raises (modeled as none) exactly when >=1 component is neither ==0 nor is_number (i.e. nonNumeric). The has(re_/im_) pre-check is a strict subset of nonNumeric (a symbolic expr containing re_/im_ is not is_number), so it does not introduce a divergence.
2. 'Result' set matches: when neither component is nonNumeric, real always reaches r=... without raising, and per-component maps exactly to the record fields (None<->none, mpf<->value, prec<->prec).
3. The model does NOT re-derive the ==0/is_number classification; it consumes it as the abstract three-way-disjoint Part.status carrier (unchanged callees per mapping.md 2/3). Hence the modeled function cannot disagree with the real callee's classification — it inherits it. The only computed logic is the assembly/short-circuit, which is control-flow-identical to the gold hunk.

Type abstraction (Expr component -> Part = (status tag, opaque Int value handle); result tuple -> EvalResult; raise NotImplementedError -> none) is a legitimate refinement, not a strengthening. The spec forbids precisely the fabricated-record-for-non-numeric-component behavior that is the base_commit UnboundLocalError, matching gold exactly. conf_skip=true is justified (no DB-free numeric R/I shadow; oracle is sympy's symbolic engine). G-AX correctly skipped (no consumed axioms). Spec is neither too strong nor drifting.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region integrity verified independently: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True — the spec view (imports + axioms/pure/pre-conditions/post-conditions regions + method signature/ensures) is byte-identical between gold and prepatch; impl and proof regions are correctly ELIDED (confirmed by dumping markers.spec_view). Region hashes in G-HYGIENE consistent. So any discriminator lives entirely in the elided impl.

Leakage test (spec view vs PUBLIC problem_statement only; hints_text excluded):
- The public problem_statement ALREADY discloses the gold edit verbatim. It shows the crashing line `r = re, im, reprec, imprec` with `UnboundLocalError: local variable 'reprec' referenced before assignment`, and the reporter explicitly proposes the fix: "the elif clauses that define reprec and imprec should have an `else: raise NotImplementedError`. That appears to fix it." That is exactly the gold patch (two `else: raise NotImplementedError` clauses).
- The spec view's changed-behavior content is the three-way classification (exactZero/numeric/nonNumeric), evalSpec returning `none` when either component is nonNumeric, and the postcondition `(realPart.status=nonNumeric ∨ imagPart.status=nonNumeric) → out = none`. This is the model-level counterpart of `raise NotImplementedError` → caller fall-back (refinement per mapping.md §2 / refinement.md A2/A3). The exactZero/numeric arms are pre-existing UNCHANGED callee behavior already visible in the public traceback, not the gold edit.
- Consequently no spec-view line encodes gold-specific information beyond what problem_statement already hands the solver. The 'non-numeric component ⇒ no numeric result / fall back' behavior is precisely the publicly-stated fix, expressed at the model's abstraction level.

No line in axioms/pure/pre/post or the method signature/ensures over-specifies or reconstructs the gold edit beyond the public statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
