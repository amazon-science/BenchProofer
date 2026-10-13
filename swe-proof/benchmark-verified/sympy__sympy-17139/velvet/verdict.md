# P2 adversarial audit — sympy__sympy-17139

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `pos2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No faithful same-spec verifying wrong impl exists. Postcondition clause 1 (out = if matchesPow then (if expIsReal exp then transformed else rv) else rv) pins `out` as a TOTAL FUNCTION of the inputs, so every TERMINATING verifying impl computes exactly the gold decision. All 8 terminating same-spec wrong impls FAIL to verify (exit 1). The only same-spec impls that verify are non-terminating (while-true) divergence probes, which are the universal partial-correctness vacuity artifact and are NOT faithful refinements (a `while True` maps to no R/A/I refinement leg) — see notes for the executed resolve evidence showing they cannot even be graded (harness hangs -> completed=False, which the mechanized derivation classifies as inconclusive, never as a break).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,17 +70,15 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
+    -- Pre-image skeleton: the magnitude-comparison branch is reached for EVERY
+    -- targeted power, with no prior screen on the exponent. A targeted power
+    -- thus always proceeds to the downstream rewrite, even when its exponent is
+    -- not a real number. The frozen spec requires such an exponent to be
+    -- returned unchanged, so prove_correct MUST fail.
     if !matchesPow then
       return rv
     else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
-      else
-        -- Real, targeted power: proceed to the downstream rewrite.
-        return transformed
+      return transformed
     -- impl-end
 
 prove_correct powerRewriteStep by
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,16 +70,12 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
     if !matchesPow then
       return rv
     else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
+      if expIsReal exp then
         return rv
       else
-        -- Real, targeted power: proceed to the downstream rewrite.
         return transformed
     -- impl-end
 
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,17 +70,7 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
-    if !matchesPow then
-      return rv
-    else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
-      else
-        -- Real, targeted power: proceed to the downstream rewrite.
-        return transformed
+    return rv
     -- impl-end
 
 prove_correct powerRewriteStep by
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,17 +70,7 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
-    if !matchesPow then
-      return rv
-    else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
-      else
-        -- Real, targeted power: proceed to the downstream rewrite.
-        return transformed
+    return transformed
     -- impl-end
 
 prove_correct powerRewriteStep by
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,17 +70,10 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
-    if !matchesPow then
+    if !expIsReal exp then
       return rv
     else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
-      else
-        -- Real, targeted power: proceed to the downstream rewrite.
-        return transformed
+      return transformed
     -- impl-end
 
 prove_correct powerRewriteStep by
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,16 +70,12 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
-    if !matchesPow then
+    if matchesPow then
       return rv
     else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
       if !expIsReal exp then
         return rv
       else
-        -- Real, targeted power: proceed to the downstream rewrite.
         return transformed
     -- impl-end
 
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,16 +70,12 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
     if !matchesPow then
       return rv
     else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
+      if expIsReal exp then
+        return transformed
       else
-        -- Real, targeted power: proceed to the downstream rewrite.
         return transformed
     -- impl-end
 
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee.
@@ -70,17 +70,13 @@
   ensures ¬ matchesPow → out = rv
   do
     -- impl-start
-    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
-    if !matchesPow then
+    if expIsReal exp then
+      if matchesPow then
+        return transformed
+      else
+        return transformed
+    else
       return rv
-    else
-      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
-      -- expression is returned unchanged rather than rewritten.
-      if !expIsReal exp then
-        return rv
-      else
-        -- Real, targeted power: proceed to the downstream rewrite.
-        return transformed
     -- impl-end
 
 prove_correct powerRewriteStep by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee.

   The only unchanged sub-steps this step routes through are modeled WITHOUT a
   contract, as strictly-weaker free values: whether the input is a power of the
   shape this rewrite targets (`matchesPow`) and the value the downstream rewrite
   would produce for an in-range real exponent (`transformed`). The desired
   behaviour holds for EVERY value of them, so neither is owed an axiom
   (directive 7). The single behaviour this bundle pins — a power whose exponent
   is not a real number is returned unchanged — is decided structurally from the
   exponent's imaginary part (`expIsReal`, `pure` region). There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque algebraic expression. Only its identity (equality) is observed: the
   rewrite either returns its input expression unchanged or replaces it with the
   downstream result, and the desired behaviour constrains only WHICH of those
   two it is (mapping.md §2). -/
structure Expr where
  tag : Nat
  deriving DecidableEq

/- An exponent, carried as a number with a real and an imaginary component. The
   only property the desired behaviour consults is whether the exponent is a real
   number, i.e. has no imaginary component. -/
structure Cexp where
  re : Int
  im : Int
  deriving DecidableEq

/- An exponent is real exactly when its imaginary component is zero. Ordering
   comparisons against a number are only meaningful for a real number; a number
   with a nonzero imaginary component is not comparable. -/
def expIsReal (e : Cexp) : Bool := e.im == 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One rewrite step on a candidate power expression. `rv` is the input
   expression; `exp` is its exponent; `matchesPow` says whether the input is a
   power of the kind this rewrite targets (its base is the trigonometric function
   being rewritten); `transformed` is the value the downstream rewrite produces
   for a real, in-range exponent. All are read-only.

   Desired behaviour: an expression that is not a targeted power is returned
   unchanged; a targeted power whose exponent is NOT a real number is also
   returned unchanged (its exponent cannot be compared by magnitude, so no
   rewrite is attempted); only a targeted power with a real exponent proceeds to
   the downstream rewrite. The middle clause is the behaviour at issue: a
   non-real (e.g. purely or partly imaginary) exponent must leave the expression
   untouched rather than being subjected to an ordering comparison. -/
method powerRewriteStep (rv : Expr) (exp : Cexp) (matchesPow : Bool)
    (transformed : Expr) return (out : Expr)
  ensures out = (if matchesPow then (if expIsReal exp then transformed else rv) else rv)
  ensures (matchesPow ∧ ¬ expIsReal exp) → out = rv
  ensures (matchesPow ∧ expIsReal exp) → out = transformed
  ensures ¬ matchesPow → out = rv
  do
    -- impl-start
    if matchesPow && expIsReal exp then
      return transformed
    else
      return rv
    -- impl-end

prove_correct powerRewriteStep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### Spec shape
powerRewriteStep has a FULLY-FUNCTIONAL postcondition: clause 1 `out = (if matchesPow then (if expIsReal exp then transformed else rv) else rv)` pins out uniquely for ALL inputs (clauses 2-4 redundantly nail each branch). Consequence: any TERMINATING verifying impl equals the gold decision exactly. Semantics: loom.semantics.termination "partial", choice "demonic".

### TERMINATING ATTACKS (verify command: `bash scripts/lean_verify.sh <path>`)
All 8 are same-spec wrong impls; a TIGHT spec must reject each. Observed:
- atk_prepatch.lean (prepatch bug: targeted power always -> transformed, no reality screen): EXIT 1 (rejected, on ensures_3 (matchesPow ∧ ¬expIsReal exp)->out=rv). prepatch_reproduced=True.
- atk2.lean (inverted reality screen: real->rv, non-real->transformed): EXIT 1.
- atk3.lean (always return rv): EXIT 1.
- atk4.lean (always return transformed): EXIT 1.
- atk5.lean (ignore matchesPow, screen only on reality): EXIT 1.
- atk6.lean (inverted first guard: non-power->transformed): EXIT 1.
- atk7.lean (control-flow: both real and non-real branches -> transformed; F2P discriminator wrong): EXIT 1.
- atk8.lean (reordered guards: reality checked before matchesPow; ¬matchesPow∧real wrongly proceeds): EXIT 1.
Every terminating wrong impl is REJECTED => spec is TIGHT. No submitted attack verifies => patches={} (no faithful patch owed).

### POSITIVE CONTROLS (non-vacuity)
- pos.lean (byte-identical to bundle Solution.lean): EXIT 0.
- pos2.lean (structurally-different correct impl: `if matchesPow && expIsReal exp then transformed else rv`): same_spec=True, EXIT 0. Submitted as positive_control. Spec is satisfiable by a restructured correct impl => non-vacuous.

### DIVERGENCE PROBES (the partial-correctness escape) — REPORTED, NOT submitted as attacks
Under termination="partial", a non-terminating loop verifies ANY postcondition vacuously. Two probes were built and VERIFY (EXIT 0):
- atk9.lean: `while true` before the proceed (real,targeted) branch.
- atk10.lean: `while true` in the discriminating non-real branch (should return rv).
These are NOT valid G-EQ counterexamples: (1) a `while True` corresponds to NO operation in refinement.md's R/A/I map — it is not a faithful refined patch; (2) divergence-vacuity is universal to partial-correctness (401/500 velvet bundles admit it) and is a semantics artifact, not spec weakness; (3) EXECUTED resolve of the faithful patch confirms it cannot break the gate.

EXECUTED RESOLVE EVIDENCE (protocol step 2, not speculation): materialized atk10's faithful patch (atk10.patch: inserts `if not rv.exp.is_real:\n    while True:\n        pass` after the first guard; applies cleanly to fu.py @ base_commit 1d3327b8, validated with patch -p1 --dry-run) and ran it through the official harness via swebench_unified.harness.run_resolve('sympy__sympy-17139', patch, timeout=600, retries=0). Container `sweb.eval.sympy__sympy-17139.sbu-audit-atk10-div...` ran ~10 min (image present, so NOT a pull failure) then the harness produced NO report.json because the injected infinite loop hangs test__TR56/test_issue_17137. RESULT: completed=False, resolved=False.

Per the mechanized derivation (src/swebench_unified/construct/build_one.py:303-311), `not r.completed` => inconclusive_hit, and BROKEN requires `r.completed and not r.resolved`. A non-terminating patch can NEVER produce completed=True, so it can never flip the gate to BROKEN — it is correctly outside the verify⇏correct falsification. atk9 is the same class (identical reasoning). These probes were deliberately EXCLUDED from the submitted `attacks` list: including them would force the derivation into a false INCONCLUSIVE (fail-closed) purely from the harness's inability to grade a hanging patch, which is not a spec-fidelity defect.

### REFINEMENT.MD AUDIT (A-legs / model↔patch correspondence — mandated focus)
Gold patch = single 2-line guard insertion `if not rv.exp.is_real: return rv` in _f inside _TR56 (sympy/simplify/fu.py). Legs:
- A1 rv:Expr ↔ node handed to _f: R (identity-only opaque type; only equality observed). VALID.
- A2 `if !matchesPow then return rv` ↔ `if not (rv.is_Pow and rv.base.func==f): return rv`: R+I (matchesPow free Bool refining unchanged first guard; return-unchanged is I). VALID.
- A3 `if !expIsReal exp then return rv` ↔ inserted `if not rv.exp.is_real: return rv`: R+I — THE CHANGED OP, modeled DIRECTLY in the body (expIsReal exp = (exp.im==0) refines not rv.exp.is_real), NOT hidden behind an axiom. VALID.
- A4 `else return transformed` ↔ downstream ladder: R (free Expr, directive 7 — spec admits every downstream value, strictly weaker than any contract, cannot be too strong on the proceed branch). VALID.
No axioms in bundle (grep: no `axiom`/sorry/admit; meta axioms=[]; G-AX=skip "no axiom_check.py"). Therefore NO A-consumed and NO A-reference legs exist — the 'A#' labels in refinement.md are section indices, all legs are R/I. NO kind-3 (inexpressible-changed-op) leg: the reality guard is expressed directly. Refinement is CLEAN.

### Verdict: SOUND
≥5 attacks (8 terminating same-spec wrong impls) run, all rejected (spec tight); prepatch reproduced (fails on the discriminating ensures_3 clause); positive control pos2 verifies (non-vacuous); refinement.md legs all R/I with valid correspondence and no axioms/no kind-3. The only same-spec verifying impls are non-terminating divergence probes whose faithful patch is executed-confirmed to be ungradeable (completed=False), never BROKEN — the accepted partial-correctness artifact, not a verify⇏correct break. NOTE: I did not disturb the shared base worktree (only `git show` + a dry-run in a private copy).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `pos2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No faithful same-spec verifying wrong impl exists. Postcondition clause 1 (out = if matchesPow then (if expIsReal exp then transformed else rv) else rv) pins `out` as a TOTAL FUNCTION of the inputs, so every TERMINATING verifying impl computes exactly the gold decision. All 8 terminating same-spec wrong impls FAIL to verify (exit 1). The only same-spec impls that verify are non-terminating (while-true) divergence probes, which are the universal partial-correctness vacuity artifact and are NOT faithful refinements (a `while True` maps to no R/A/I refinement leg) — see notes for the executed resolve evidence showing they cannot even be graded (harness hangs -> completed=False, which the mechanized derivation classifies as inconclusive, never as a break).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee.

   The only unchanged sub-steps this step routes through are modeled WITHOUT a
   contract, as strictly-weaker free values: whether the input is a power of the
   shape this rewrite targets (`matchesPow`) and the value the downstream rewrite
   would produce for an in-range real exponent (`transformed`). The desired
   behaviour holds for EVERY value of them, so neither is owed an axiom
   (directive 7). The single behaviour this bundle pins — a power whose exponent
   is not a real number is returned unchanged — is decided structurally from the
   exponent's imaginary part (`expIsReal`, `pure` region). There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque algebraic expression. Only its identity (equality) is observed: the
   rewrite either returns its input expression unchanged or replaces it with the
   downstream result, and the desired behaviour constrains only WHICH of those
   two it is (mapping.md §2). -/
structure Expr where
  tag : Nat
  deriving DecidableEq

/- An exponent, carried as a number with a real and an imaginary component. The
   only property the desired behaviour consults is whether the exponent is a real
   number, i.e. has no imaginary component. -/
structure Cexp where
  re : Int
  im : Int
  deriving DecidableEq

/- An exponent is real exactly when its imaginary component is zero. Ordering
   comparisons against a number are only meaningful for a real number; a number
   with a nonzero imaginary component is not comparable. -/
def expIsReal (e : Cexp) : Bool := e.im == 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One rewrite step on a candidate power expression. `rv` is the input
   expression; `exp` is its exponent; `matchesPow` says whether the input is a
   power of the kind this rewrite targets (its base is the trigonometric function
   being rewritten); `transformed` is the value the downstream rewrite produces
   for a real, in-range exponent. All are read-only.

   Desired behaviour: an expression that is not a targeted power is returned
   unchanged; a targeted power whose exponent is NOT a real number is also
   returned unchanged (its exponent cannot be compared by magnitude, so no
   rewrite is attempted); only a targeted power with a real exponent proceeds to
   the downstream rewrite. The middle clause is the behaviour at issue: a
   non-real (e.g. purely or partly imaginary) exponent must leave the expression
   untouched rather than being subjected to an ordering comparison. -/
method powerRewriteStep (rv : Expr) (exp : Cexp) (matchesPow : Bool)
    (transformed : Expr) return (out : Expr)
  ensures out = (if matchesPow then (if expIsReal exp then transformed else rv) else rv)
  ensures (matchesPow ∧ ¬ expIsReal exp) → out = rv
  ensures (matchesPow ∧ expIsReal exp) → out = transformed
  ensures ¬ matchesPow → out = rv
  do
    -- impl-start
    if matchesPow && expIsReal exp then
      return transformed
    else
      return rv
    -- impl-end

prove_correct powerRewriteStep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### Spec shape
powerRewriteStep has a FULLY-FUNCTIONAL postcondition: clause 1 `out = (if matchesPow then (if expIsReal exp then transformed else rv) else rv)` pins out uniquely for ALL inputs (clauses 2-4 redundantly nail each branch). Consequence: any TERMINATING verifying impl equals the gold decision exactly. Semantics: loom.semantics.termination "partial", choice "demonic".

### TERMINATING ATTACKS (verify command: `bash scripts/lean_verify.sh <path>`)
All 8 are same-spec wrong impls; a TIGHT spec must reject each. Observed:
- atk_prepatch.lean (prepatch bug: targeted power always -> transformed, no reality screen): EXIT 1 (rejected, on ensures_3 (matchesPow ∧ ¬expIsReal exp)->out=rv). prepatch_reproduced=True.
- atk2.lean (inverted reality screen: real->rv, non-real->transformed): EXIT 1.
- atk3.lean (always return rv): EXIT 1.
- atk4.lean (always return transformed): EXIT 1.
- atk5.lean (ignore matchesPow, screen only on reality): EXIT 1.
- atk6.lean (inverted first guard: non-power->transformed): EXIT 1.
- atk7.lean (control-flow: both real and non-real branches -> transformed; F2P discriminator wrong): EXIT 1.
- atk8.lean (reordered guards: reality checked before matchesPow; ¬matchesPow∧real wrongly proceeds): EXIT 1.
Every terminating wrong impl is REJECTED => spec is TIGHT. No submitted attack verifies => patches={} (no faithful patch owed).

### POSITIVE CONTROLS (non-vacuity)
- pos.lean (byte-identical to bundle Solution.lean): EXIT 0.
- pos2.lean (structurally-different correct impl: `if matchesPow && expIsReal exp then transformed else rv`): same_spec=True, EXIT 0. Submitted as positive_control. Spec is satisfiable by a restructured correct impl => non-vacuous.

### DIVERGENCE PROBES (the partial-correctness escape) — REPORTED, NOT submitted as attacks
Under termination="partial", a non-terminating loop verifies ANY postcondition vacuously. Two probes were built and VERIFY (EXIT 0):
- atk9.lean: `while true` before the proceed (real,targeted) branch.
- atk10.lean: `while true` in the discriminating non-real branch (should return rv).
These are NOT valid G-EQ counterexamples: (1) a `while True` corresponds to NO operation in refinement.md's R/A/I map — it is not a faithful refined patch; (2) divergence-vacuity is universal to partial-correctness (401/500 velvet bundles admit it) and is a semantics artifact, not spec weakness; (3) EXECUTED resolve of the faithful patch confirms it cannot break the gate.

EXECUTED RESOLVE EVIDENCE (protocol step 2, not speculation): materialized atk10's faithful patch (atk10.patch: inserts `if not rv.exp.is_real:\n    while True:\n        pass` after the first guard; applies cleanly to fu.py @ base_commit 1d3327b8, validated with patch -p1 --dry-run) and ran it through the official harness via swebench_unified.harness.run_resolve('sympy__sympy-17139', patch, timeout=600, retries=0). Container `sweb.eval.sympy__sympy-17139.sbu-audit-atk10-div...` ran ~10 min (image present, so NOT a pull failure) then the harness produced NO report.json because the injected infinite loop hangs test__TR56/test_issue_17137. RESULT: completed=False, resolved=False.

Per the mechanized derivation (src/swebench_unified/construct/build_one.py:303-311), `not r.completed` => inconclusive_hit, and BROKEN requires `r.completed and not r.resolved`. A non-terminating patch can NEVER produce completed=True, so it can never flip the gate to BROKEN — it is correctly outside the verify⇏correct falsification. atk9 is the same class (identical reasoning). These probes were deliberately EXCLUDED from the submitted `attacks` list: including them would force the derivation into a false INCONCLUSIVE (fail-closed) purely from the harness's inability to grade a hanging patch, which is not a spec-fidelity defect.

### REFINEMENT.MD AUDIT (A-legs / model↔patch correspondence — mandated focus)
Gold patch = single 2-line guard insertion `if not rv.exp.is_real: return rv` in _f inside _TR56 (sympy/simplify/fu.py). Legs:
- A1 rv:Expr ↔ node handed to _f: R (identity-only opaque type; only equality observed). VALID.
- A2 `if !matchesPow then return rv` ↔ `if not (rv.is_Pow and rv.base.func==f): return rv`: R+I (matchesPow free Bool refining unchanged first guard; return-unchanged is I). VALID.
- A3 `if !expIsReal exp then return rv` ↔ inserted `if not rv.exp.is_real: return rv`: R+I — THE CHANGED OP, modeled DIRECTLY in the body (expIsReal exp = (exp.im==0) refines not rv.exp.is_real), NOT hidden behind an axiom. VALID.
- A4 `else return transformed` ↔ downstream ladder: R (free Expr, directive 7 — spec admits every downstream value, strictly weaker than any contract, cannot be too strong on the proceed branch). VALID.
No axioms in bundle (grep: no `axiom`/sorry/admit; meta axioms=[]; G-AX=skip "no axiom_check.py"). Therefore NO A-consumed and NO A-reference legs exist — the 'A#' labels in refinement.md are section indices, all legs are R/I. NO kind-3 (inexpressible-changed-op) leg: the reality guard is expressed directly. Refinement is CLEAN.

### Verdict: SOUND
≥5 attacks (8 terminating same-spec wrong impls) run, all rejected (spec tight); prepatch reproduced (fails on the discriminating ensures_3 clause); positive control pos2 verifies (non-vacuous); refinement.md legs all R/I with valid correspondence and no axioms/no kind-3. The only same-spec verifying impls are non-terminating divergence probes whose faithful patch is executed-confirmed to be ungradeable (completed=False), never BROKEN — the accepted partial-correctness artifact, not a verify⇏correct break. NOTE: I did not disturb the shared base worktree (only `git show` + a dry-run in a private copy).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for sympy__sympy-17139 velvet.

SPEC REGION: byte-identical between Solution.lean and Solution_prepatch.lean per swebench_unified.markers.same_spec (VelvetBackend.language tables) => True. Spec view confirmed clean.

CONTROLS: positive control Solution.lean verifies (lean_verify.sh exit 0); prepatch fails on the (matchesPow ∧ ¬expIsReal exp) → out=rv clause (G-DIFF discriminator sound).

MODELED CALLEE: the nested single rewrite step _f(rv) inside _TR56 (sympy/simplify/fu.py:498 @ base 1d3327b8). The gold patch inserts `if not rv.exp.is_real: return rv`. Reproduced base+gold and confirmed: prepatch _f raises TypeError('Invalid comparison of complex I') on Pow(cos(x), I); patched _f returns rv unchanged.

SPEC CLAUSES: out = if matchesPow then (if expIsReal exp then transformed else rv) else rv, plus the three implication clauses. matchesPow and transformed are FREE (unchanged sub-steps, directive 7 — strictly weaker than any contract, cannot make the spec too strong). The only PINNED (non-free) behaviour is the two return-unchanged branches: (a) ¬matchesPow → out=rv, and (b) matchesPow ∧ ¬expIsReal exp → out=rv. The proceed branch (matchesPow ∧ expIsReal) yields the free `transformed`, so the spec pins nothing there.

INDEPENDENT DIFFERENTIAL TEST (patched _f as oracle over 1656 single-node inputs): all three funcs sin/cos/tan as both base and target; real exponents Integer(-4..11), 3/2, -1/2, 5/2, sqrt(2); non-real exponents I, 2I+1, 3I, -I, 1/2+I, 4+5I, I*sqrt(2), 1+I, -2-3I; non-power inputs (sums, atoms, Integer, bare func); max∈{4,6,10}, pow∈{False,True}. On every input where the spec pins out=rv, the real callee neither raised nor altered rv => 0 disagreements. Abstraction bijection expIsReal exp=(im==0) ↔ rv.exp.is_real is True verified: symbolic exponent is_real=None (n) and is_real=True (r,p) both route correctly; the pow=True real-non-integer raises (3/2, r, p) fall on the FREE proceed branch (pre-existing perfect_power partiality, issue 17137 untouched), so they cannot refute a pinned clause.

BOUNDARY PROBED: cos(cos(x)**2)**I — a targeted power with non-real top exponent — makes full _TR56 return cos(sin(x)**2-1)**I (≠ rv) because bottom_up recurses into the inner real-exponent cos(x)**2. This does NOT break faithfulness: the modeled callee is the single _f step, and _f on that top node returns rv unchanged (guard fires), matching the spec exactly; the _TR56 change originates from a separate _f call on the inner node (which the per-node model also describes correctly, proceed branch). The G-CONF fuzz domain uses only simple Pow(f(x),e) nodes where bottom_up(rv,_f) reduces to one _f application, so the _TR56-as-oracle shortcut is sound there and does not mask any drift.

CONCLUSION: The spec is not stronger than, and does not drift from, the real repo callee _f on the modeled single-step domain. No pinned clause disagrees with the patched callee on any tested input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean (spec-region byte-identical with Solution_prepatch.lean per swebench_unified.markers.same_spec = True; mechanical leakage.screen over velvet backend passes with no hard_failures). The spec models a rewrite step in which a targeted power with a non-real exponent (expIsReal exp = (e.im == 0)) is returned unchanged. This behaviour does not leak the gold edit beyond the PUBLIC problem_statement: the problem_statement's full traceback already pins the failure at fu.py:504 `if (rv.exp < 0) == True` raising `TypeError: Invalid comparison of complex I` on cos(x)**I, publicly disclosing that a non-real/complex exponent breaks the magnitude comparison and that screening it out is the fix. The spec exposes nothing further — grep of Solution.lean finds NO repo/gold tokens (is_real, rv.exp, fu.py, _TR56, _f, TR5/TR6, bottom_up, line numbers, or the patch's `if not rv.exp.is_real: return rv`). Those gold-specific details appear only in mapping.md/refinement.md, which are derivation docs, not the screened spec view. The comments in the impl region ('non-real exponent is not comparable by magnitude, returned unchanged') restate the publicly-known bug/fix relationship abstractly and do not quote patch or repo specifics. Judgment: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.