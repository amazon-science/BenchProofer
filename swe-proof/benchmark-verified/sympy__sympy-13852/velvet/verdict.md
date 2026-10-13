# P2 adversarial audit — sympy__sympy-13852

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch_A.lean`, `atk_B_polar.lean`, `atk_swap.lean`, `atk_partial.lean`, `atk_prio.lean`, `atk_zc.lean`, `atk_loop_term.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The two methods' postconditions TOTALLY pin the output. recognizeClosedForm requires out = closedFormFor s zTag, a total concrete Int priority cascade (z-keyed clauses first for any s; then the six s=2 specials; then s=0/s=-1; else cfUneval), reinforced by six explicit pointwise ensures (zC->cfZc, s2&z1->cfP1, s2&z2->cfP2, sKeyA&zOther->cfSa, sKeyB&zOther->cfSb, zA&sKeyA->cfZa which pins priority). seriesExpansionAtOne requires out = expansionCode ∧ out = expPlain ∧ out ≠ expPolar. Every TERMINATING impl is therefore pointwise identical to the gold cascade, so no terminating verifying-but-wrong impl exists. The only impls that verify while being behaviorally wrong are NON-TERMINATING (partial-correctness vacuity), which is not a materializable faithful refinement of the gold dispatch (see notes).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch_A.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,23 +125,10 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
     let result : Int :=
       if zTag = zA then cfZa
       else if zTag = zB then cfZb
       else if zTag = zC then cfZc
-      else if s = sSpecial then
-        (if zTag = z1 then cfP1
-         else if zTag = z2 then cfP2
-         else if zTag = z3 then cfP3
-         else if zTag = z4 then cfP4
-         else if zTag = z5 then cfP5
-         else if zTag = z6 then cfP6
-         else cfUneval)
-      else if s = sKeyA then cfSa
-      else if s = sKeyB then cfSb
       else cfUneval
     return result
     -- impl-end
```

Attack 2 — `atk_B_polar.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -163,7 +163,7 @@
   ensures out ≠ expPolar
   do
     -- impl-start
-    return expPlain
+    return expPolar
     -- impl-end
 
 prove_correct seriesExpansionAtOne by
```

Attack 3 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,16 +125,13 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
     let result : Int :=
       if zTag = zA then cfZa
       else if zTag = zB then cfZb
       else if zTag = zC then cfZc
       else if s = sSpecial then
-        (if zTag = z1 then cfP1
-         else if zTag = z2 then cfP2
+        (if zTag = z1 then cfP2
+         else if zTag = z2 then cfP1
          else if zTag = z3 then cfP3
          else if zTag = z4 then cfP4
          else if zTag = z5 then cfP5
```

Attack 4 — `atk_partial.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,9 +125,6 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
     let result : Int :=
       if zTag = zA then cfZa
       else if zTag = zB then cfZb
@@ -140,7 +137,6 @@
          else if zTag = z5 then cfP5
          else if zTag = z6 then cfP6
          else cfUneval)
-      else if s = sKeyA then cfSa
       else if s = sKeyB then cfSb
       else cfUneval
     return result
```

Attack 5 — `atk_prio.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,11 +125,10 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
     let result : Int :=
-      if zTag = zA then cfZa
+      if s = sKeyA then cfSa
+      else if s = sKeyB then cfSb
+      else if zTag = zA then cfZa
       else if zTag = zB then cfZb
       else if zTag = zC then cfZc
       else if s = sSpecial then
@@ -140,8 +139,6 @@
          else if zTag = z5 then cfP5
          else if zTag = z6 then cfP6
          else cfUneval)
-      else if s = sKeyA then cfSa
-      else if s = sKeyB then cfSb
       else cfUneval
     return result
     -- impl-end
```

Attack 6 — `atk_zc.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,13 +125,10 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
     let result : Int :=
       if zTag = zA then cfZa
       else if zTag = zB then cfZb
-      else if zTag = zC then cfZc
+      else if zTag = zC then cfUneval
       else if s = sSpecial then
         (if zTag = z1 then cfP1
          else if zTag = z2 then cfP2
```

Attack 7 — `atk_loop_term.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,25 +125,16 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
-    let result : Int :=
-      if zTag = zA then cfZa
-      else if zTag = zB then cfZb
-      else if zTag = zC then cfZc
-      else if s = sSpecial then
-        (if zTag = z1 then cfP1
-         else if zTag = z2 then cfP2
-         else if zTag = z3 then cfP3
-         else if zTag = z4 then cfP4
-         else if zTag = z5 then cfP5
-         else if zTag = z6 then cfP6
-         else cfUneval)
-      else if s = sKeyA then cfSa
-      else if s = sKeyB then cfSb
-      else cfUneval
-    return result
+    let mut r : Int := cfUneval
+    let mut i : Int := 0
+    while i < 3
+      invariant 0 ≤ i ∧ i ≤ 3
+      invariant r = cfUneval
+      done_with i = 3
+      decreasing 3 - i
+    do
+      i := i + 1
+    return r
     -- impl-end
 
 prove_correct recognizeClosedForm by
```

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -125,25 +125,7 @@
   ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
   do
     -- impl-start
-    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
-    -- z-keyed clauses first (for any s), then the distinguished-s special
-    -- arguments, then the two s-keyed clauses, else unevaluated.
-    let result : Int :=
-      if zTag = zA then cfZa
-      else if zTag = zB then cfZb
-      else if zTag = zC then cfZc
-      else if s = sSpecial then
-        (if zTag = z1 then cfP1
-         else if zTag = z2 then cfP2
-         else if zTag = z3 then cfP3
-         else if zTag = z4 then cfP4
-         else if zTag = z5 then cfP5
-         else if zTag = z6 then cfP6
-         else cfUneval)
-      else if s = sKeyA then cfSa
-      else if s = sKeyB then cfSb
-      else cfUneval
-    return result
+    return closedFormFor s zTag
     -- impl-end
 
 prove_correct recognizeClosedForm by
@@ -163,7 +145,7 @@
   ensures out ≠ expPolar
   do
     -- impl-start
-    return expPlain
+    return expansionCode
     -- impl-end
 
 prove_correct seriesExpansionAtOne by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure recognition cascade over the discrete argument pattern of a
   two-parameter special function: which closed form (if any) the function takes
   at a recognised pattern, and which series form its expansion takes at one
   distinguished parameter value. Every observable is computed from the inputs by
   a concrete dispatch; nothing is borrowed from an oracle. There is therefore no
   consumed axiom (mapping.md §3). That each abstract closed-form code names the
   value the real function actually takes at its pattern is an out-of-band
   obligation validated executably (axiom_check.py / G-AX), not assumed here. -/
-- axioms-end

-- pure-start
/- Closed-form result codes: opaque, pairwise-distinct identifiers, one per
   distinct closed form the recognition cascade can produce. `cfUneval` marks
   "no closed form" — the call stays unevaluated. The codes carry no arithmetic
   meaning inside the spec; that each names the value the real function takes at
   its pattern is the G-AX obligation (mapping.md / axiom_check.py). -/
def cfUneval : Int := 0   -- no closed form: the call stays unevaluated
def cfZa : Int := 1       -- first z-keyed pattern    (z = z_a)
def cfZb : Int := 2       -- second z-keyed pattern   (z = z_b)
def cfZc : Int := 3       -- third z-keyed pattern    (z = z_c)
def cfP1 : Int := 4       -- distinguished s, z = z_1
def cfP2 : Int := 5       -- distinguished s, z = z_2
def cfP3 : Int := 6       -- distinguished s, z = z_3
def cfP4 : Int := 7       -- distinguished s, z = z_4
def cfP5 : Int := 8       -- distinguished s, z = z_5
def cfP6 : Int := 9       -- distinguished s, z = z_6
def cfSa : Int := 10      -- first s-keyed pattern
def cfSb : Int := 11      -- second s-keyed pattern

/- Argument-pattern tags for the z component: the finite quotient of z by the
   nine equality tests the cascade branches on. `zOther` is any other z. -/
def zA : Int := 1
def zB : Int := 2
def zC : Int := 3
def z1 : Int := 4
def z2 : Int := 5
def z3 : Int := 6
def z4 : Int := 7
def z5 : Int := 8
def z6 : Int := 9
def zOther : Int := 0

/- Distinguished s-predicate values the cascade branches on. -/
def sSpecial : Int := 2   -- s value carrying the six special-z closed forms
def sKeyA : Int := 0      -- s value of the first s-keyed pattern
def sKeyB : Int := -1     -- s value of the second s-keyed pattern
def sExpand : Int := 1    -- s value whose series-expansion is pinned below

/- Series-expansion codes for the distinguished s. -/
def expPlain : Int := 1   -- elementary closed form in (1 - z): NO branch factor
def expPolar : Int := 2   -- carries a polar/branch factor on z

/- The closed-form code the function takes at argument pattern `(s, zTag)`,
   as a PRIORITY CASCADE. The three z-keyed clauses are matched first (for ANY
   s); then, at the distinguished `sSpecial`, the six special arguments; then the
   two s-keyed clauses. An unrecognised pattern yields no closed form
   (`cfUneval`). This map is concrete — it states only WHICH code each recognised
   pattern produces; the priority order (z-keyed before s-keyed) is part of the
   characterization. That the produced closed form equals the real function at
   the pattern is the G-AX obligation. -/
def closedFormFor (s : Int) (zTag : Int) : Int :=
  -- Priority 1: the z-keyed clauses, matched for any s.
  if zTag = zA then cfZa
  else if zTag = zB then cfZb
  else if zTag = zC then cfZc
  -- Priority 2: the six special arguments at the distinguished s.
  else if s = sSpecial then
    (if zTag = z1 then cfP1
     else if zTag = z2 then cfP2
     else if zTag = z3 then cfP3
     else if zTag = z4 then cfP4
     else if zTag = z5 then cfP5
     else if zTag = z6 then cfP6
     else cfUneval)
  -- Priority 3: the two s-keyed clauses.
  else if s = sKeyA then cfSa
  else if s = sKeyB then cfSb
  else cfUneval

/- The series-expansion closed-form code at the distinguished s: the elementary
   closed form in (1 - z) with NO polar/branch factor on z. -/
def expansionCode : Int := expPlain
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recognise the closed form of a two-parameter special function at an argument
   pattern. The pattern is the discrete quotient of the symbolic arguments: `s`
   is the discrete parameter (only its values `sSpecial`, `sKeyA`, `sKeyB` are
   distinguished), and `zTag` is the finite quotient of the second argument by
   the nine recognised values (else `zOther`).

   The desired behaviour is a priority cascade: some patterns are keyed on the
   second argument alone and win first (for any `s`); a further group is keyed on
   the distinguished `s` together with one of several special second-argument
   values; and two more patterns are keyed on `s` alone. A pattern matched
   earlier wins over a later one at the same argument. Any pattern matching
   nothing produces `cfUneval` — the call stays unevaluated; the cascade must not
   over-fire. The result is exactly the cascade's choice, so it must produce a
   genuine closed form (not `cfUneval`) for every recognised pattern.

   `s`, `zTag` are read-only: the method computes and returns a code and never
   mutates its inputs. -/
method recognizeClosedForm (s : Int) (zTag : Int) return (out : Int)
  ensures out = closedFormFor s zTag
  ensures zTag = zC → out = cfZc
  ensures (s = sSpecial ∧ zTag = z1) → out = cfP1
  ensures (s = sSpecial ∧ zTag = z2) → out = cfP2
  ensures (s = sKeyA ∧ zTag = zOther) → out = cfSa
  ensures (s = sKeyB ∧ zTag = zOther) → out = cfSb
  ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
  do
    -- impl-start
    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
    -- z-keyed clauses first (for any s), then the distinguished-s special
    -- arguments, then the two s-keyed clauses, else unevaluated.
    let result : Int :=
      if zTag = zA then cfZa
      else if zTag = zB then cfZb
      else if zTag = zC then cfZc
      else if s = sSpecial then
        (if zTag = z1 then cfP1
         else if zTag = z2 then cfP2
         else if zTag = z3 then cfP3
         else if zTag = z4 then cfP4
         else if zTag = z5 then cfP5
         else if zTag = z6 then cfP6
         else cfUneval)
      else if s = sKeyA then cfSa
      else if s = sKeyB then cfSb
      else cfUneval
    return result
    -- impl-end

prove_correct recognizeClosedForm by
  loom_solve <;>
    simp_all [closedFormFor, zA, zB, zC, z1, z2, z3, z4, z5, z6, zOther,
      sSpecial, sKeyA, sKeyB, cfUneval, cfZa, cfZb, cfZc,
      cfP1, cfP2, cfP3, cfP4, cfP5, cfP6, cfSa, cfSb]

/- The series-expansion of the same function at the distinguished parameter
   `sExpand`. The desired behaviour: the expansion is the elementary closed form
   in `(1 - z)` carrying NO polar/branch factor on the second argument
   (`expPlain`), never the polar-factored form (`expPolar`). `s` is read-only. -/
method seriesExpansionAtOne (s : Int) return (out : Int)
  require s = sExpand
  ensures out = expansionCode
  ensures out = expPlain
  ensures out ≠ expPolar
  do
    -- impl-start
    return expPlain
    -- impl-end

prove_correct seriesExpansionAtOne by
  loom_solve <;> simp_all [expansionCode, expPlain, expPolar]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh scratch Every attack copied Solution.lean and edited ONLY the two impl regions; same_spec=True verified for all 10 attack files + positive control via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>`. Resolve cmd: run_resolve(instance, patch_text) 

### VERIFY RESULTS (exit 0 = verifies):
- pos_control (exact gold cascade + return expPlain): exit 0 — VERIFIES (positive control good).
- atk_prepatch_A (only z-keyed clauses, rest cfUneval = the prepatch bug): exit 1 — REJECTED (fails out=closedFormFor at s2/sKey patterns). prepatch reproduced.
- atk_B_polar (method B returns expPolar = prepatch expansion bug): exit 1 — REJECTED (fails out=expPlain, out≠expPolar).
- atk_swap (boundary: swap cfP1/cfP2 at s=2): exit 1 — REJECTED.
- atk_partial (partial-domain: drop the sKeyA clause): exit 1 — REJECTED.
- atk_prio (control-flow-effect: s-keyed clauses moved before z-keyed, inverting priority): exit 1 — REJECTED (fails the explicit zA&sKeyA->cfZa ensures).
- atk_zc (boundary: cfZc->cfUneval at z=0): exit 1 — REJECTED.
- atk_loop_term (TERMINATING while-loop returning a wrong value cfUneval, with decreasing clause): exit 1 — REJECTED. This isolates that a loop per se does not evade the pinning; only NON-termination does.
- atk_echo (ungrounded-oracle echo: method A returns closedFormFor s zTag, method B returns expansionCode): exit 0 — VERIFIES. Its faithful refined patch = the gold patch verbatim; run_resolve => {resolved:true, completed:true} => CORRECT ECHO, not a weakness (matches the resolve-checked candidate policy in _derive_audit_verdict).

### RESOLVE RESULTS (executed, not speculated):
- atk_echo faithful patch (= gold patch.diff, applies cleanly at base_commit c935e1d): resolved=true, completed=true.

DIVERGENCE ATTACKS (partial-correctness vacuity) — investigated, NOT counted as breaks, with executed evidence:
- atk_div_A2 (gating method A: `while i>=0 invariant i>=0 done_with i<0` infinite loop, returns cfUneval): exit 0 — VERIFIES cleanly (only linter warnings). atk_div_B (method B same shape): exit 0 — VERIFIES. atk_div_A (naive infinite loop, invariant True): exit 1 (invariant too weak to discharge the pinned post at the vacuous exit) — shows the vacuity requires the negated-guard-contradicts-invariant construction.
- WHY THIS IS NOT A BROKEN VERDICT: (1) The spec sets loom.semantics.termination "partial" (partial correctness), shared by 401/500 velvet bundles; under it a diverging impl vacuously satisfies ANY postcondition. This is a universal semantic property of the modeling choice, not a spec-specific weakness of sympy-13852. (2) refinement.md has NO leg mapping to a non-terminating loop — every impl op is R/I/A-reference over a concrete TERMINATING dispatch clause; a `while True: pass` in polylog.eval is therefore not a faithful refinement of any modeled operation, so a divergent impl cannot be 'refined per the map.' (3) EXECUTED CHECK: I materialized the faithful divergent patch (`else: while True: pass` in polylog.eval, applies cleanly at base_commit) and ran it through the official run_resolve: result {resolved:false, completed:FALSE, note:'no report ... harness error'} — i.e. it HANGS the test process and produces no report. Per the official _derive_audit_verdict (src/swebench_unified/construct/build_one.py:305-308), a candidate whose resolve run has `not r.completed` is recorded INCONCLUSIVE, NOT the BROKEN label (which requires r.completed AND not r.resolved). So even if divergence attacks were submitted, the mechanized gate does not derive BROKEN from them; it would fail-closed to INCONCLUSIVE. They are excluded from the submitted attacks list because they are not valid refinement-fidelity counterexamples.

REFINEMENT.md AUDIT (A-legs focus; R/I pre-cleared by G-CONF pass): all legs are R / A-reference / I — NO kind-3 (unexpressible-changed-op) and NO A-consumed axiom (axioms region is empty; confirmed byte-identical). A6 (six s=2 dilog specials) and A7 (s=0->z/(1-z), s=-1->z/(1-z)**2) and B2 (s=1 expansion == -log(1-z), polar-free) are A-references validated by axiom_check.py/G-AX against the REAL gold-patched polylog/expand_func; meta.json records G-AX=pass, G-CONF=pass, G-DIFF=pass (both prepatch skeletons fail), G-RESOLVE=pass, G-MUT=13/13. The mapping.md neutral<->concrete key (zA<->z==1, sSpecial<->s==2, cfP1..cfP6 <-> the six gold closed forms, expPlain<->-log(1-z)) is consistent with patch.diff. The priority-cascade correspondence (z-keyed wins: polylog(0,1)==zeta(0) not division-by-zero) is pinned by the explicit ensures and validated on the real callee by G-AX. No correspondence defect found.

CONCLUSION: 8 same-spec attacks re-run (7 terminating wrong-impls all REJECTED including the reproduced prepatch bug; 1 echo VERIFIES and its faithful=gold patch RESOLVES). Positive control verifies. No terminating verifying-but-wrong impl exists; the totally-pinning postconditions make verify => behaviorally-identical-to-gold => resolves. Divergence attacks are a universal partial-correctness artifact with no faithful refinement and are treated as INCONCLUSIVE (not BROKEN) by the harness. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch_A.lean`, `atk_B_polar.lean`, `atk_swap.lean`, `atk_partial.lean`, `atk_prio.lean`, `atk_zc.lean`, `atk_loop_term.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The two methods' postconditions TOTALLY pin the output. recognizeClosedForm requires out = closedFormFor s zTag, a total concrete Int priority cascade (z-keyed clauses first for any s; then the six s=2 specials; then s=0/s=-1; else cfUneval), reinforced by six explicit pointwise ensures (zC->cfZc, s2&z1->cfP1, s2&z2->cfP2, sKeyA&zOther->cfSa, sKeyB&zOther->cfSb, zA&sKeyA->cfZa which pins priority). seriesExpansionAtOne requires out = expansionCode ∧ out = expPlain ∧ out ≠ expPolar. Every TERMINATING impl is therefore pointwise identical to the gold cascade, so no terminating verifying-but-wrong impl exists. The only impls that verify while being behaviorally wrong are NON-TERMINATING (partial-correctness vacuity), which is not a materializable faithful refinement of the gold dispatch (see notes).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch_A.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_B_polar.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_prio.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_zc.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_loop_term.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure recognition cascade over the discrete argument pattern of a
   two-parameter special function: which closed form (if any) the function takes
   at a recognised pattern, and which series form its expansion takes at one
   distinguished parameter value. Every observable is computed from the inputs by
   a concrete dispatch; nothing is borrowed from an oracle. There is therefore no
   consumed axiom (mapping.md §3). That each abstract closed-form code names the
   value the real function actually takes at its pattern is an out-of-band
   obligation validated executably (axiom_check.py / G-AX), not assumed here. -/
-- axioms-end

-- pure-start
/- Closed-form result codes: opaque, pairwise-distinct identifiers, one per
   distinct closed form the recognition cascade can produce. `cfUneval` marks
   "no closed form" — the call stays unevaluated. The codes carry no arithmetic
   meaning inside the spec; that each names the value the real function takes at
   its pattern is the G-AX obligation (mapping.md / axiom_check.py). -/
def cfUneval : Int := 0   -- no closed form: the call stays unevaluated
def cfZa : Int := 1       -- first z-keyed pattern    (z = z_a)
def cfZb : Int := 2       -- second z-keyed pattern   (z = z_b)
def cfZc : Int := 3       -- third z-keyed pattern    (z = z_c)
def cfP1 : Int := 4       -- distinguished s, z = z_1
def cfP2 : Int := 5       -- distinguished s, z = z_2
def cfP3 : Int := 6       -- distinguished s, z = z_3
def cfP4 : Int := 7       -- distinguished s, z = z_4
def cfP5 : Int := 8       -- distinguished s, z = z_5
def cfP6 : Int := 9       -- distinguished s, z = z_6
def cfSa : Int := 10      -- first s-keyed pattern
def cfSb : Int := 11      -- second s-keyed pattern

/- Argument-pattern tags for the z component: the finite quotient of z by the
   nine equality tests the cascade branches on. `zOther` is any other z. -/
def zA : Int := 1
def zB : Int := 2
def zC : Int := 3
def z1 : Int := 4
def z2 : Int := 5
def z3 : Int := 6
def z4 : Int := 7
def z5 : Int := 8
def z6 : Int := 9
def zOther : Int := 0

/- Distinguished s-predicate values the cascade branches on. -/
def sSpecial : Int := 2   -- s value carrying the six special-z closed forms
def sKeyA : Int := 0      -- s value of the first s-keyed pattern
def sKeyB : Int := -1     -- s value of the second s-keyed pattern
def sExpand : Int := 1    -- s value whose series-expansion is pinned below

/- Series-expansion codes for the distinguished s. -/
def expPlain : Int := 1   -- elementary closed form in (1 - z): NO branch factor
def expPolar : Int := 2   -- carries a polar/branch factor on z

/- The closed-form code the function takes at argument pattern `(s, zTag)`,
   as a PRIORITY CASCADE. The three z-keyed clauses are matched first (for ANY
   s); then, at the distinguished `sSpecial`, the six special arguments; then the
   two s-keyed clauses. An unrecognised pattern yields no closed form
   (`cfUneval`). This map is concrete — it states only WHICH code each recognised
   pattern produces; the priority order (z-keyed before s-keyed) is part of the
   characterization. That the produced closed form equals the real function at
   the pattern is the G-AX obligation. -/
def closedFormFor (s : Int) (zTag : Int) : Int :=
  -- Priority 1: the z-keyed clauses, matched for any s.
  if zTag = zA then cfZa
  else if zTag = zB then cfZb
  else if zTag = zC then cfZc
  -- Priority 2: the six special arguments at the distinguished s.
  else if s = sSpecial then
    (if zTag = z1 then cfP1
     else if zTag = z2 then cfP2
     else if zTag = z3 then cfP3
     else if zTag = z4 then cfP4
     else if zTag = z5 then cfP5
     else if zTag = z6 then cfP6
     else cfUneval)
  -- Priority 3: the two s-keyed clauses.
  else if s = sKeyA then cfSa
  else if s = sKeyB then cfSb
  else cfUneval

/- The series-expansion closed-form code at the distinguished s: the elementary
   closed form in (1 - z) with NO polar/branch factor on z. -/
def expansionCode : Int := expPlain
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recognise the closed form of a two-parameter special function at an argument
   pattern. The pattern is the discrete quotient of the symbolic arguments: `s`
   is the discrete parameter (only its values `sSpecial`, `sKeyA`, `sKeyB` are
   distinguished), and `zTag` is the finite quotient of the second argument by
   the nine recognised values (else `zOther`).

   The desired behaviour is a priority cascade: some patterns are keyed on the
   second argument alone and win first (for any `s`); a further group is keyed on
   the distinguished `s` together with one of several special second-argument
   values; and two more patterns are keyed on `s` alone. A pattern matched
   earlier wins over a later one at the same argument. Any pattern matching
   nothing produces `cfUneval` — the call stays unevaluated; the cascade must not
   over-fire. The result is exactly the cascade's choice, so it must produce a
   genuine closed form (not `cfUneval`) for every recognised pattern.

   `s`, `zTag` are read-only: the method computes and returns a code and never
   mutates its inputs. -/
method recognizeClosedForm (s : Int) (zTag : Int) return (out : Int)
  ensures out = closedFormFor s zTag
  ensures zTag = zC → out = cfZc
  ensures (s = sSpecial ∧ zTag = z1) → out = cfP1
  ensures (s = sSpecial ∧ zTag = z2) → out = cfP2
  ensures (s = sKeyA ∧ zTag = zOther) → out = cfSa
  ensures (s = sKeyB ∧ zTag = zOther) → out = cfSb
  ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
  do
    -- impl-start
    -- The recognition cascade, mirroring patch.diff's nested dispatch: the
    -- z-keyed clauses first (for any s), then the distinguished-s special
    -- arguments, then the two s-keyed clauses, else unevaluated.
    let result : Int :=
      if zTag = zA then cfZa
      else if zTag = zB then cfZb
      else if zTag = zC then cfZc
      else if s = sSpecial then
        (if zTag = z1 then cfP1
         else if zTag = z2 then cfP2
         else if zTag = z3 then cfP3
         else if zTag = z4 then cfP4
         else if zTag = z5 then cfP5
         else if zTag = z6 then cfP6
         else cfUneval)
      else if s = sKeyA then cfSa
      else if s = sKeyB then cfSb
      else cfUneval
    return result
    -- impl-end

prove_correct recognizeClosedForm by
  loom_solve <;>
    simp_all [closedFormFor, zA, zB, zC, z1, z2, z3, z4, z5, z6, zOther,
      sSpecial, sKeyA, sKeyB, cfUneval, cfZa, cfZb, cfZc,
      cfP1, cfP2, cfP3, cfP4, cfP5, cfP6, cfSa, cfSb]

/- The series-expansion of the same function at the distinguished parameter
   `sExpand`. The desired behaviour: the expansion is the elementary closed form
   in `(1 - z)` carrying NO polar/branch factor on the second argument
   (`expPlain`), never the polar-factored form (`expPolar`). `s` is read-only. -/
method seriesExpansionAtOne (s : Int) return (out : Int)
  require s = sExpand
  ensures out = expansionCode
  ensures out = expPlain
  ensures out ≠ expPolar
  do
    -- impl-start
    return expPlain
    -- impl-end

prove_correct seriesExpansionAtOne by
  loom_solve <;> simp_all [expansionCode, expPlain, expPolar]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh scratch Every attack copied Solution.lean and edited ONLY the two impl regions; same_spec=True verified for all 10 attack files + positive control via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>`. Resolve cmd: run_resolve(instance, patch_text) 

### VERIFY RESULTS (exit 0 = verifies):
- pos_control (exact gold cascade + return expPlain): exit 0 — VERIFIES (positive control good).
- atk_prepatch_A (only z-keyed clauses, rest cfUneval = the prepatch bug): exit 1 — REJECTED (fails out=closedFormFor at s2/sKey patterns). prepatch reproduced.
- atk_B_polar (method B returns expPolar = prepatch expansion bug): exit 1 — REJECTED (fails out=expPlain, out≠expPolar).
- atk_swap (boundary: swap cfP1/cfP2 at s=2): exit 1 — REJECTED.
- atk_partial (partial-domain: drop the sKeyA clause): exit 1 — REJECTED.
- atk_prio (control-flow-effect: s-keyed clauses moved before z-keyed, inverting priority): exit 1 — REJECTED (fails the explicit zA&sKeyA->cfZa ensures).
- atk_zc (boundary: cfZc->cfUneval at z=0): exit 1 — REJECTED.
- atk_loop_term (TERMINATING while-loop returning a wrong value cfUneval, with decreasing clause): exit 1 — REJECTED. This isolates that a loop per se does not evade the pinning; only NON-termination does.
- atk_echo (ungrounded-oracle echo: method A returns closedFormFor s zTag, method B returns expansionCode): exit 0 — VERIFIES. Its faithful refined patch = the gold patch verbatim; run_resolve => {resolved:true, completed:true} => CORRECT ECHO, not a weakness (matches the resolve-checked candidate policy in _derive_audit_verdict).

### RESOLVE RESULTS (executed, not speculated):
- atk_echo faithful patch (= gold patch.diff, applies cleanly at base_commit c935e1d): resolved=true, completed=true.

DIVERGENCE ATTACKS (partial-correctness vacuity) — investigated, NOT counted as breaks, with executed evidence:
- atk_div_A2 (gating method A: `while i>=0 invariant i>=0 done_with i<0` infinite loop, returns cfUneval): exit 0 — VERIFIES cleanly (only linter warnings). atk_div_B (method B same shape): exit 0 — VERIFIES. atk_div_A (naive infinite loop, invariant True): exit 1 (invariant too weak to discharge the pinned post at the vacuous exit) — shows the vacuity requires the negated-guard-contradicts-invariant construction.
- WHY THIS IS NOT A BROKEN VERDICT: (1) The spec sets loom.semantics.termination "partial" (partial correctness), shared by 401/500 velvet bundles; under it a diverging impl vacuously satisfies ANY postcondition. This is a universal semantic property of the modeling choice, not a spec-specific weakness of sympy-13852. (2) refinement.md has NO leg mapping to a non-terminating loop — every impl op is R/I/A-reference over a concrete TERMINATING dispatch clause; a `while True: pass` in polylog.eval is therefore not a faithful refinement of any modeled operation, so a divergent impl cannot be 'refined per the map.' (3) EXECUTED CHECK: I materialized the faithful divergent patch (`else: while True: pass` in polylog.eval, applies cleanly at base_commit) and ran it through the official run_resolve: result {resolved:false, completed:FALSE, note:'no report ... harness error'} — i.e. it HANGS the test process and produces no report. Per the official _derive_audit_verdict (src/swebench_unified/construct/build_one.py:305-308), a candidate whose resolve run has `not r.completed` is recorded INCONCLUSIVE, NOT the BROKEN label (which requires r.completed AND not r.resolved). So even if divergence attacks were submitted, the mechanized gate does not derive BROKEN from them; it would fail-closed to INCONCLUSIVE. They are excluded from the submitted attacks list because they are not valid refinement-fidelity counterexamples.

REFINEMENT.md AUDIT (A-legs focus; R/I pre-cleared by G-CONF pass): all legs are R / A-reference / I — NO kind-3 (unexpressible-changed-op) and NO A-consumed axiom (axioms region is empty; confirmed byte-identical). A6 (six s=2 dilog specials) and A7 (s=0->z/(1-z), s=-1->z/(1-z)**2) and B2 (s=1 expansion == -log(1-z), polar-free) are A-references validated by axiom_check.py/G-AX against the REAL gold-patched polylog/expand_func; meta.json records G-AX=pass, G-CONF=pass, G-DIFF=pass (both prepatch skeletons fail), G-RESOLVE=pass, G-MUT=13/13. The mapping.md neutral<->concrete key (zA<->z==1, sSpecial<->s==2, cfP1..cfP6 <-> the six gold closed forms, expPlain<->-log(1-z)) is consistent with patch.diff. The priority-cascade correspondence (z-keyed wins: polylog(0,1)==zeta(0) not division-by-zero) is pinned by the explicit ensures and validated on the real callee by G-AX. No correspondence defect found.

CONCLUSION: 8 same-spec attacks re-run (7 terminating wrong-impls all REJECTED including the reproduced prepatch bug; 1 echo VERIFIES and its faithful=gold patch RESOLVES). Positive control verifies. No terminating verifying-but-wrong impl exists; the totally-pinning postconditions make verify => behaviorally-identical-to-gold => resolves. Divergence attacks are a universal partial-correctness artifact with no faithful refinement and are treated as INCONCLUSIVE (not BROKEN) by the harness. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the velvet spec for sympy__sympy-13852 (polylog.eval dispatch + _eval_expand_func at s==1). No diverging input found; the modeled functions agree with the real gold-patched callee on every input tested.

Setup: gold worktree (base_commit c935e1d, patch.diff applied in tree — verified eval() has z==1/-1/0, s==2 six-way, s==0, s==-1 branches and _eval_expand_func returns -log(1-z)). Ran the real callee under a py3.8 venv + collections shim (old sympy needs `from collections import Mapping`).

spec-region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True with the velvet backend — spec regions frozen, only impl differs.

Faithfulness evidence (real gold-patched callee):
- Priority cascade: polylog(0,1)=-1/2 (=zeta(0); z-keyed clause wins over s==0's z/(1-z) division-by-zero), polylog(2,1)=pi**2/6, polylog(2,-1)=-pi**2/12, polylog(0,0)=0, polylog(-1,0)=0 — matches model's z-keyed-before-s-keyed order (closedFormFor).
- s==2 specials: all six gold closed forms match symbolically (simplify(real-expected)==0) at z=1/2, 2, and the four golden-ratio points → cfP1..cfP6.
- s-keyed: polylog(0,7)=-7/6=z/(1-z), polylog(-1,7)=7/36=z/(1-z)**2 → cfSa/cfSb.
- No over-fire: polylog(3,1/2), polylog(2,7), polylog(5,7) stay unevaluated → cfUneval.
- Expansion: expand_func(polylog(1,z))=-log(-z+1), exp_polar-free → expPlain, not expPolar.
- Broad transliteration probe (faith_13852.py, spec ladder vs polylog.eval over 15 s-values × ~34 z-values incl. symbols, floats, complex I, irrationals, pi, log): 0 divergences.

Type-refinement soundness: s,z modeled as Int discrete quotients (s∈{2,0,-1,1} distinguished; zTag = 9-way equality quotient else zOther). The real dispatch branches ONLY on those discrete equalities and is constant on each class, so the quotient is faithful — no observable the Int carrier drops. zOther collapse is safe: z1..z6 are special only under s==2; under s==0/-1 the real callee returns z/(1-z)[**2] for any z, matching model's cfSa/cfSb for zTag=zOther (and z-keyed clauses still win for zA/zB/zC).

Spec is at least as strong as the gold fix, not weaker/drifted: Solution.lean elaborates clean (lean_verify exit 0); both prepatch files fail (exit 1), confirming the postconditions sense the s==2/s∈{0,-1} cascade (behaviour A) and the polar-free expansion (behaviour B) — G-DIFF discriminating, spec not vacuous. Non-gating status of behaviour B is honestly documented (F2P test_polylog_values exercises only auto-eval), and the spec still requires it, so verify⟹resolved holds.

Conclusion: no input on which the modeled functions disagree with the real repo callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified rigorously. Spec regions (axioms/pure/pre/post + signatures) are byte-identical across Solution.lean, Solution_prepatch.lean, and Solution_prepatch_2.lean (markers.same_spec = True for both). Lexical G-LEAK screen passes (leakage.screen → passed, no hard_failures). Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so no deferral in play.

Public problem_statement discloses: the function polylog; polylog(2,1/2) == -log(2)**2/2 + pi**2/12 (the s=2 special value); expand_func(polylog(1,z)) should be -log(1-z) with no exp_polar factor (s=1 expansion); derivative z/(1-z).

Spec-view discloses only an ABSTRACT, function-anonymized recognition cascade: three z-keyed clauses, six special z-args at a distinguished s, two s-keyed clauses, plus a distinguished-s expansion that is 'elementary in (1 - z), NO polar/branch factor'. Function name 'polylog', the patched path 'zeta_functions.py', 'zeta', 'dirichlet_eta', 'exp_polar', 'sqrt', golden-ratio points, pi**2/12, z/(1-z), z/(1-z)**2 are ALL absent from the spec view — every closed form is hidden behind opaque, arithmetic-meaningless integer codes (cfP1..cfP6, cfSa, cfSb, expPlain/expPolar). The '.py' tokens in the view are only auxiliary-artifact references (axiom_check.py, mapping.md), not the patched file path.

Beyond-statement content: the carrier integers sSpecial=2, sKeyA=0, sKeyB=-1, sExpand=1 reveal that s=0/s=-1 are special-cased (not in the problem statement). This is the discrete branch structure any faithful behavioral model must expose; it does NOT reconstruct the gold edit — the substance (which closed-form expression each pattern returns) is fully abstracted behind opaque codes, and deriving those forms is the task itself. Knowing 'branch on s=0/-1' without the formulas is not the gold patch. The '1 - z' phrasing that does appear is verbatim public (problem statement discusses -log(1-z) and z/(1-z)).

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
