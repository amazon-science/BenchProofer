# P2 adversarial audit — matplotlib__matplotlib-24149

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,11 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
     let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    let result := match found with
+      | some v => Except.ok v
+      | none   => Except.error ExtractErr.noFiniteFound
+    return result
     -- impl-end
 
 prove_correct selectReference by
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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,7 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
-    let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    return Except.ok (firstElement xs)
     -- impl-end
 
 prove_correct selectReference by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,8 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
     let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    return Except.ok (found.getD 0.0)
     -- impl-end
 
 prove_correct selectReference by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,8 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
     let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    return Except.ok (found.getD (xs.getLastD 0))
     -- impl-end
 
 prove_correct selectReference by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,7 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
-    let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    return Except.error ExtractErr.noFiniteFound
     -- impl-end
 
 prove_correct selectReference by
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
 -- (No axiomatized callees. The two element-extraction routines this step relies
@@ -61,12 +61,8 @@
   ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
   do
     -- impl-start
-    -- Attempt to take the first finite element; should that attempt come up
-    -- empty (no element is finite), fall back to the first element taken
-    -- unconditionally. Either way a value is produced — never a raised error.
-    let found := firstFinite xs
-    let result := found.getD (firstElement xs)
-    return Except.ok result
+    let found := xs.find? (fun x => ! isFiniteVal x)
+    return Except.ok (found.getD (firstElement xs))
     -- impl-end
 
 prove_correct selectReference by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two element-extraction routines this step relies
--  on are modeled DEEPLY as the pure functions below — `firstFinite` and
--  `firstElement` — and are validated against the real routines by axiom_check.py
--  (G-AX, A-reference). Nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- The failure that the element-extraction step can report: a request for the
   first finite element of a sequence that happens to contain none. Modeled as
   an error leg so the post-state can distinguish "produced a value" from
   "raised". -/
inductive ExtractErr where
  | noFiniteFound
  deriving Inhabited, DecidableEq

/- Whether a scalar real value is finite — i.e. neither not-a-number nor an
   infinity. (Bijection to the real scalar-finiteness predicate: mapping.md §2.) -/
def isFiniteVal (x : Float) : Bool := x.isFinite

/- The first finite element of a sequence, if one exists. Scans front-to-back
   and returns the first element satisfying the finiteness predicate, or `none`
   when every element is non-finite. Deep model of the "first finite" extractor
   (A-reference; mapping.md §3). -/
def firstFinite (xs : List Float) : Option Float := xs.find? isFiniteVal

/- The first element of a sequence, taken unconditionally (finite or not). Deep
   model of the "first element" extractor (A-reference; mapping.md §3). The
   default is immaterial under the precondition that the sequence is non-empty. -/
def firstElement (xs : List Float) : Float := xs.headD 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Pick the representative scalar of a non-empty sequence for use as a reference
   point.

   The sequence is consulted read-only. The desired behavior is total: a
   representative is always produced for a non-empty sequence, never an error.
   Specifically, the representative is the first finite element of the sequence
   when one exists, and the first element of the sequence (taken unconditionally)
   when no element is finite. Pinning the result to
   `(firstFinite xs).getD (firstElement xs)` pins both legs at once — the
   finite-element value on the common path, and the unconditional first-element
   fallback on the all-non-finite path — and rules out the error outcome on every
   non-empty input. -/
method selectReference (xs : List Float) return (out : Except ExtractErr Float)
  require xs ≠ []
  ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
  do
    -- impl-start
    -- Attempt to take the first finite element; should that attempt come up
    -- empty (no element is finite), fall back to the first element taken
    -- unconditionally. Either way a value is produced — never a raised error.
    let found := firstFinite xs
    let result := found.getD (firstElement xs)
    return Except.ok result
    -- impl-end

prove_correct selectReference by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of matplotlib__matplotlib-24149 (velvet). Spec is a CONCRETE FUNCTIONAL EQUALITY: `ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))` under `require xs ≠ []`, no consumed axioms. same_spec=True verified for all 9 files (only impl region edited). lean_verify.sh via scripts/lean_verify.sh; harness via swebench_unified.harness.run_resolve (SBU_BENCHMARK_DIR=benchmark-verified). VERDICT: SOUND.

### TERMINATING ATTACKS (6, all correctly verify-REJECTED, exit 1)
- atk_1 (PREPATCH BUG: none-leg -> Except.error noFiniteFound, no fallback): exit 1. Rejected on the all-non-finite (none) leg: error ≠ ok (firstElement xs). This is exactly the test_bar_all_nan crash the gold patch fixes => prepatch_reproduced=true.
- atk_2 (always ok (firstElement xs), ignore finiteness preference): exit 1. Rejected e.g. [nan,5.0]: firstElement=nan ≠ getD=5.0.
- atk_3 (fallback to literal 0.0 instead of firstElement): exit 1. Rejected on all-non-finite seqs where firstElement≠0.0 (e.g. [inf]).
- atk_4 (fallback to LAST element via xs.getLastD 0): exit 1. Rejected on all-non-finite len≥2 with distinct ends (e.g. [inf,nan]).
- atk_5 (always Except.error): exit 1. Rejected by ok≠error.
- atk_7 (first NON-finite element instead of first finite): exit 1. Rejected whenever first finite ≠ first non-finite.
Positive control atk_pos (the exact gold `.getD` impl): exit 0 (verifies) => spec non-vacuous/satisfiable.
Commands: `bash scripts/lean_verify.sh atk_N.lean` (pos=0; 1,2,3,4,5,7=1).

### DIVERGENCE PROBE (partial-correctness) — investigated per mandate, DOES NOT break the spec
The spec preamble freezes `set_option loom.semantics.termination "partial"` (part of same_spec; universal to the entire velvet track). Under partial correctness a non-terminating `do` block vacuously satisfies ANY postcondition, so two divergence impls VERIFY (exit 0):
- atk_6.lean: unconditional `while true` loop (diverges on every input) then the correct return. lean_verify exit 0.
- atk_8.lean: partial-domain divergence — correct ok v when a finite element exists, but `while true` loop on the all-non-finite (none) leg. lean_verify exit 0.
Per protocol I MATERIALIZED each one's faithful refined patch (injecting `while True: pass` into the corresponding StopIteration/extraction site of lib/matplotlib/axes/_axes.py, built from the gold patch's known-good context; correct hunk counts @@ -2182,11 +2182,17 @@; patch_atk6.diff / patch_atk8.diff) and RAN run_resolve on the official harness.
### OBSERVED (executed, not speculated):
gold patch  -> resolved=True,  completed=True,  164.0s (harness sanity: image+F2P test work). atk_8 patch -> resolved=False, completed=FALSE, 481.9s, note='no report ... harness error' (container hit internal --timeout while test_bar_all_nan HUNG on the infinite loop; NO report.json produced). atk_6 patch -> resolved=False, completed=FALSE, 481.9s, same (hang to timeout, no report). WHY THIS IS NOT A BREAK: build_one.py:_derive_audit_verdict marks BROKEN only on `r.completed and not r.resolved` (verify⇏correct with a COMPLETED non-resolving run). A hang yields completed=FALSE, which the derivation classifies as INCONCLUSIVE-per-attack (line 310-312), NOT the completed∧¬resolved BROKEN signature (line 306).

A diverging impl's faithful patch can never produce a completed non-resolving run — it always times out. Divergence is a universal artifact of the frozen partial-correctness semantics (every velvet spec admits `while true`); if it counted as a G-EQ break, all ~432 green velvet cells would be BROKEN. It is therefore NOT a defect of THIS spec, and I deliberately EXCLUDE atk_6/atk_8 from the submitted `attacks` list (including a never-completing patch would only force a spurious gate-wide INCONCLUSIVE).

Malformed-patch guard: an early build with wrong hunk counts produced 'malformed patch at line 21' (apply-failed) which WOULD give a false completed∧¬resolved; I rebuilt both patches from gold's exact context and confirmed distinct patch hashes (f617893701, 6cfce316ac) ran real containers, so the 481.9s no-report is a genuine test hang, not an apply failure.

### REFINEMENT.MD AUDIT (A-legs, focus)
3 legs, all typed: op1 `firstFinite xs` = A-reference (deep model xs.find? isFiniteVal == cbook._safe_first_finite, default skip_nonfinite=True; some v ⇔ first finite, none ⇔ StopIteration); op2 `found.getD (firstElement xs)` = A-reference (firstElement xs = xs.headD 0 == cbook.safe_first_element = _safe_first_finite(skip_nonfinite=False)); op3 `Except.ok result` = R (ok ⇔ no escaping exception). ZERO kind-3, ZERO A-consumed, ZERO dead axioms. A-leg correspondence to the real callees is validated by axiom_check.py (G-AX rc 0 per bundle: 100000 fuzz + boundary seqs + 20000 scalar), and mapping.md §3 correctly pins the skip_nonfinite flag dependency for each callee. Correspondence holds.

### Conclusion
All 6 terminating same-spec wrong impls are verify-REJECTED; positive control verifies; prepatch bug reproduced on the exact discriminating (none) leg; the spec is a tight concrete functional equality with no ungrounded oracle; the two divergence impls verify but their faithful patches hang (completed=False) and thus do not exhibit verify⇏correct. No verifying wrong impl has a materialized faithful patch that COMPLETES-and-does-not-resolve. Spec is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two element-extraction routines this step relies
--  on are modeled DEEPLY as the pure functions below — `firstFinite` and
--  `firstElement` — and are validated against the real routines by axiom_check.py
--  (G-AX, A-reference). Nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- The failure that the element-extraction step can report: a request for the
   first finite element of a sequence that happens to contain none. Modeled as
   an error leg so the post-state can distinguish "produced a value" from
   "raised". -/
inductive ExtractErr where
  | noFiniteFound
  deriving Inhabited, DecidableEq

/- Whether a scalar real value is finite — i.e. neither not-a-number nor an
   infinity. (Bijection to the real scalar-finiteness predicate: mapping.md §2.) -/
def isFiniteVal (x : Float) : Bool := x.isFinite

/- The first finite element of a sequence, if one exists. Scans front-to-back
   and returns the first element satisfying the finiteness predicate, or `none`
   when every element is non-finite. Deep model of the "first finite" extractor
   (A-reference; mapping.md §3). -/
def firstFinite (xs : List Float) : Option Float := xs.find? isFiniteVal

/- The first element of a sequence, taken unconditionally (finite or not). Deep
   model of the "first element" extractor (A-reference; mapping.md §3). The
   default is immaterial under the precondition that the sequence is non-empty. -/
def firstElement (xs : List Float) : Float := xs.headD 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Pick the representative scalar of a non-empty sequence for use as a reference
   point.

   The sequence is consulted read-only. The desired behavior is total: a
   representative is always produced for a non-empty sequence, never an error.
   Specifically, the representative is the first finite element of the sequence
   when one exists, and the first element of the sequence (taken unconditionally)
   when no element is finite. Pinning the result to
   `(firstFinite xs).getD (firstElement xs)` pins both legs at once — the
   finite-element value on the common path, and the unconditional first-element
   fallback on the all-non-finite path — and rules out the error outcome on every
   non-empty input. -/
method selectReference (xs : List Float) return (out : Except ExtractErr Float)
  require xs ≠ []
  ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
  do
    -- impl-start
    -- Attempt to take the first finite element; should that attempt come up
    -- empty (no element is finite), fall back to the first element taken
    -- unconditionally. Either way a value is produced — never a raised error.
    let found := firstFinite xs
    let result := found.getD (firstElement xs)
    return Except.ok result
    -- impl-end

prove_correct selectReference by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of matplotlib__matplotlib-24149 (velvet). Spec is a CONCRETE FUNCTIONAL EQUALITY: `ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))` under `require xs ≠ []`, no consumed axioms. same_spec=True verified for all 9 files (only impl region edited). lean_verify.sh via scripts/lean_verify.sh; harness via swebench_unified.harness.run_resolve (SBU_BENCHMARK_DIR=benchmark-verified). VERDICT: SOUND.

### TERMINATING ATTACKS (6, all correctly verify-REJECTED, exit 1)
- atk_1 (PREPATCH BUG: none-leg -> Except.error noFiniteFound, no fallback): exit 1. Rejected on the all-non-finite (none) leg: error ≠ ok (firstElement xs). This is exactly the test_bar_all_nan crash the gold patch fixes => prepatch_reproduced=true.
- atk_2 (always ok (firstElement xs), ignore finiteness preference): exit 1. Rejected e.g. [nan,5.0]: firstElement=nan ≠ getD=5.0.
- atk_3 (fallback to literal 0.0 instead of firstElement): exit 1. Rejected on all-non-finite seqs where firstElement≠0.0 (e.g. [inf]).
- atk_4 (fallback to LAST element via xs.getLastD 0): exit 1. Rejected on all-non-finite len≥2 with distinct ends (e.g. [inf,nan]).
- atk_5 (always Except.error): exit 1. Rejected by ok≠error.
- atk_7 (first NON-finite element instead of first finite): exit 1. Rejected whenever first finite ≠ first non-finite.
Positive control atk_pos (the exact gold `.getD` impl): exit 0 (verifies) => spec non-vacuous/satisfiable.
Commands: `bash scripts/lean_verify.sh atk_N.lean` (pos=0; 1,2,3,4,5,7=1).

### DIVERGENCE PROBE (partial-correctness) — investigated per mandate, DOES NOT break the spec
The spec preamble freezes `set_option loom.semantics.termination "partial"` (part of same_spec; universal to the entire velvet track). Under partial correctness a non-terminating `do` block vacuously satisfies ANY postcondition, so two divergence impls VERIFY (exit 0):
- atk_6.lean: unconditional `while true` loop (diverges on every input) then the correct return. lean_verify exit 0.
- atk_8.lean: partial-domain divergence — correct ok v when a finite element exists, but `while true` loop on the all-non-finite (none) leg. lean_verify exit 0.
Per protocol I MATERIALIZED each one's faithful refined patch (injecting `while True: pass` into the corresponding StopIteration/extraction site of lib/matplotlib/axes/_axes.py, built from the gold patch's known-good context; correct hunk counts @@ -2182,11 +2182,17 @@; patch_atk6.diff / patch_atk8.diff) and RAN run_resolve on the official harness.
### OBSERVED (executed, not speculated):
gold patch  -> resolved=True,  completed=True,  164.0s (harness sanity: image+F2P test work). atk_8 patch -> resolved=False, completed=FALSE, 481.9s, note='no report ... harness error' (container hit internal --timeout while test_bar_all_nan HUNG on the infinite loop; NO report.json produced). atk_6 patch -> resolved=False, completed=FALSE, 481.9s, same (hang to timeout, no report). WHY THIS IS NOT A BREAK: build_one.py:_derive_audit_verdict marks BROKEN only on `r.completed and not r.resolved` (verify⇏correct with a COMPLETED non-resolving run). A hang yields completed=FALSE, which the derivation classifies as INCONCLUSIVE-per-attack (line 310-312), NOT the completed∧¬resolved BROKEN signature (line 306).

A diverging impl's faithful patch can never produce a completed non-resolving run — it always times out. Divergence is a universal artifact of the frozen partial-correctness semantics (every velvet spec admits `while true`); if it counted as a G-EQ break, all ~432 green velvet cells would be BROKEN. It is therefore NOT a defect of THIS spec, and I deliberately EXCLUDE atk_6/atk_8 from the submitted `attacks` list (including a never-completing patch would only force a spurious gate-wide INCONCLUSIVE).

Malformed-patch guard: an early build with wrong hunk counts produced 'malformed patch at line 21' (apply-failed) which WOULD give a false completed∧¬resolved; I rebuilt both patches from gold's exact context and confirmed distinct patch hashes (f617893701, 6cfce316ac) ran real containers, so the 481.9s no-report is a genuine test hang, not an apply failure.

### REFINEMENT.MD AUDIT (A-legs, focus)
3 legs, all typed: op1 `firstFinite xs` = A-reference (deep model xs.find? isFiniteVal == cbook._safe_first_finite, default skip_nonfinite=True; some v ⇔ first finite, none ⇔ StopIteration); op2 `found.getD (firstElement xs)` = A-reference (firstElement xs = xs.headD 0 == cbook.safe_first_element = _safe_first_finite(skip_nonfinite=False)); op3 `Except.ok result` = R (ok ⇔ no escaping exception). ZERO kind-3, ZERO A-consumed, ZERO dead axioms. A-leg correspondence to the real callees is validated by axiom_check.py (G-AX rc 0 per bundle: 100000 fuzz + boundary seqs + 20000 scalar), and mapping.md §3 correctly pins the skip_nonfinite flag dependency for each callee. Correspondence holds.

### Conclusion
All 6 terminating same-spec wrong impls are verify-REJECTED; positive control verifies; prepatch bug reproduced on the exact discriminating (none) leg; the spec is a tight concrete functional equality with no ungrounded oracle; the two divergence impls verify but their faithful patches hang (completed=False) and thus do not exhibit verify⇏correct. No verifying wrong impl has a materialized faithful patch that COMPLETES-and-does-not-resolve. Spec is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for velvet matplotlib__matplotlib-24149, method selectReference. Result: FAITHFUL — no input found where the modeled function disagrees with the real repo callee.

Evidence:
1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The pre/post/pure region and method signature are unchanged between patch and prepatch; only the impl region differs (fallback vs error-propagation). The spec is not tailored to the impl.
2) Solution.lean verifies: scripts/lean_verify.sh exit 0 (prove_correct discharged by loom_solve).
3) Deep models validated against the REAL base_commit callees (worktree @ af39f1edffcd..., cbook byte-identical to installed mpl 3.6.3 — callees unchanged by patch):
   - firstFinite xs = xs.find? isFiniteVal  <->  cbook._safe_first_finite(obj, skip_nonfinite=True) else-branch next(val for val in obj if safe_isfinite(val)); some<=>first finite found, none<=>StopIteration.
   - firstElement xs = xs.headD 0  <->  safe_first_element = _safe_first_finite(skip_nonfinite=False) = next(iter(obj)) (first element unconditionally).
   - isFiniteVal = Float.isFinite  vs  np.isfinite: 0 differences over 2,000,000 random IEEE-754 doubles + all sentinels (NaN, +/-inf, +/-0.0, subnormals, +/-max).
4) Post-condition out = Except.ok ((firstFinite xs).getD (firstElement xs)) transliterated INDEPENDENTLY (pure-Python model, NOT reusing cbook) and differentially fuzzed against the real patched _convert_dx extraction block (real cbook callees) over 300,010 inputs (boundary battery + all-non-finite-biased + mixed-position fuzz, seed 24149): 0 disagreements. Confirms both legs: finite-element on the common path, unconditional first-element on the all-non-finite path, and the always-'ok' (no reachable error leg) claim.
5) Domain narrowing is legitimate, not a drift: mapping.md §2 scopes the modeled domain to non-empty scalar-float sequences (the path _convert_dx reaches after the xconv.size==0 guard), explicitly excluding the iterator/np.flatiter branches. On that domain the patched real code always binds a value and never lets StopIteration escape, matching the spec's total, always-ok post-condition.

The spec is neither too strong nor drifting from real behavior on the modeled domain; require xs != [] is exactly the reachability precondition and the post pins the real callees' composed result. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean) == True: pre/post patch differ only in the elided impl region and prove_correct body; the visible spec is byte-identical, so the discriminating fallback lives entirely in the elided impl. Lexical G-LEAK screen passes with zero hard_failures (no diff markers, no verbatim gold lines, no patched file/module path, no repo-symbol identifier echo, no narration). Semantic check: the spec-view postcondition `ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))` encodes the gold edit's discriminating behavior (all-non-finite path -> fall back to first element rather than raise), but this behavior is already PUBLIC in the problem_statement: the Expected outcome states the all-nan case must return a bar with nan x (i.e. use the first/nan element, no raise), and the traceback explicitly exposes `_safe_first_finite`, the `next(...if safe_isfinite...)` generator, and the `StopIteration`. Encoding correct behavior in an `ensures` clause is required of a spec and is not a leak; no edit-localization (diff shape, patched file/symbol) is disclosed beyond the public task. Model helper names (firstFinite/firstElement/selectReference) do not echo repo symbols; the real callee names appear only in mapping.md/refinement.md, which are outside the consumer spec view. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.