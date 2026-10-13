# P2 adversarial audit — scikit-learn__scikit-learn-14496

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 13 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only verifying wrong-impl candidate (atk_10, a vacuous-guard probe returning 0 when population = 0, a state excluded by `require 1 <= population`) had its faithful refined patch materialized and RUN through the official harness: RESOLVED=True (FAIL_TO_PASS sklearn/cluster/tests/test_optics.py::test_extract_xi success; 40/40 PASS_TO_PASS success). The guard is unreachable in the real repo because n_samples = X.shape[0] / len(reachability) is >= 1 on any array that reaches the conditioning step, and `_validate_size` raises on size > n_samples, so the extra branch is dead code and cannot change behaviour. No verifying impl produced a non-resolving patch, so verify => correct was not falsified.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      size := max 2 scaled
     return size
     -- impl-end
 
@@ -120,12 +120,12 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      primary := max 2 scaledPrimary
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := max 2 scaledSecondary
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      size := (((max 2 (Rat.floor (value * (population : Rat)))) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +120,12 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      primary := (((max 2 (Rat.floor (value * (population : Rat)))) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := (((max 2 (Rat.floor (secondary * (population : Rat)))) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      size := (((max 2 (Rat.ceil scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +120,12 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      primary := (((max 2 (Rat.ceil scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := (((max 2 (Rat.ceil scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
   do
     -- impl-start
     let mut size : Rat := value
-    if value ≤ 1 then
+    if value < 1 then
       size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
     return size
     -- impl-end
@@ -119,12 +119,12 @@
   do
     -- impl-start
     let mut primary : Rat := value
-    if value ≤ 1 then
+    if value < 1 then
       primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
-    if secondary ≤ 1 then
+    if secondary < 1 then
       secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      size := (((Rat.floor scaled) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +120,12 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      primary := (((Rat.floor scaledPrimary) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := (((Rat.floor scaledSecondary) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,8 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      if 1 < scaled then
+        size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +121,14 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      if 1 < scaledPrimary then
+        primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      if 1 < scaledSecondary then
+        secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,7 +125,7 @@
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      size := (((Rat.floor (max 2 scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +120,12 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      primary := (((Rat.floor (max 2 scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      secondary := (((Rat.floor (max 2 scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,8 @@
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
-    if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      if secondary ≤ 1 then
+        secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,7 +90,10 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      if population = 0 then
+        size := 0
+      else
+        size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +123,18 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      if population = 0 then
+        primary := 0
+      else
+        primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      if population = 0 then
+        secondary := 0
+      else
+        secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,10 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      if value = 0 then
+        size := 999
+      else
+        size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +123,18 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      if value = 0 then
+        primary := 999
+      else
+        primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      if secondary = 0 then
+        secondary := 999
+      else
+        secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,10 @@
     -- impl-start
     let mut size : Rat := value
     if value ≤ 1 then
-      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
+      if population = 1 then
+        size := 2
+      else
+        size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
     return size
     -- impl-end
 
@@ -120,12 +123,18 @@
     -- impl-start
     let mut primary : Rat := value
     if value ≤ 1 then
-      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
+      if population = 1 then
+        primary := 2
+      else
+        primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
     let mut secondary : Rat := primary
     if secondaryGiven then
       secondary := secondaryValue
     if secondary ≤ 1 then
-      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
+      if population = 1 then
+        secondary := 2
+      else
+        secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
     -- impl-end
 
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,12 +118,12 @@
     resolvedPairedSizes value secondaryValue scaledPrimary scaledSecondary secondaryGiven
   do
     -- impl-start
+    let mut secondary : Rat := value
+    if secondaryGiven then
+      secondary := secondaryValue
     let mut primary : Rat := value
     if value ≤ 1 then
       primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
-    let mut secondary : Rat := primary
-    if secondaryGiven then
-      secondary := secondaryValue
     if secondary ≤ 1 then
       secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
     return { primary := primary, secondary := secondary }
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. A size-validation guard runs before the conditioning
   step and only restricts the input domain; its guarantee is captured as a
   `require` precondition rather than an axiom, so there is no dead/over-claimed
   axiom (SPEC_GUIDE §0 directive 7). -/
-- axioms-end

-- pure-start
/- A sizing parameter may be given in two forms: as an absolute count (a value
   strictly greater than one) or as a fraction of the population (a value in the
   half-open interval (0, 1]).  When it is given as a fraction it must be turned
   into a concrete absolute count: take the value it scales to against the
   population, reduce that to a whole number by discarding any fractional part,
   and never let the result fall below two.  When the parameter is already an
   absolute count it is used as-is.

   The scaling is performed in the ambient inexact numeric type, so the scaled
   value the conditioning step actually receives is only guaranteed to agree with
   the ideal product to within that type's relative precision — one part in
   2^53.  It is therefore an INPUT to the routines below (`scaled`) rather than
   something recomputed here, and the contracts pin the reduction to a whole
   count *of the value that was actually produced*.  `scaledFromPopulation`
   states exactly that admissible relationship; a routine may not invent a
   different scaled value.

   Modeled with `Rat`: once the scaled value is in hand the remaining behavior is
   an exact order/integer relation (discard the fractional part, clamp), and on a
   non-negative value discarding the fractional part coincides with the floor, so
   `Rat.floor` models it exactly (mapping.md §2). -/
def scaledFromPopulation (scaled value : Rat) (population : Nat) : Prop :=
  value * (population : Rat) - value * (population : Rat) / 9007199254740992 ≤ scaled ∧
    scaled ≤ value * (population : Rat) + value * (population : Rat) / 9007199254740992

def asAbsoluteCount (value scaled : Rat) : Rat :=
  if value ≤ 1 then
    (((max 2 (Rat.floor scaled)) : Int) : Rat)
  else
    value

structure SizePair where
  primary   : Rat
  secondary : Rat
deriving DecidableEq

/- The secondary parameter is optional: when it is not supplied it defaults to
   the already-conditioned primary value. -/
def pairedSecondarySource
    (value scaledPrimary secondaryValue : Rat) (secondaryGiven : Bool) : Rat :=
  if secondaryGiven then secondaryValue else asAbsoluteCount value scaledPrimary

/- The conditioned pair: condition the primary; the secondary is the supplied
   value if present, otherwise the conditioned primary, and is then conditioned
   in turn. -/
def resolvedPairedSizes
    (value secondaryValue scaledPrimary scaledSecondary : Rat)
    (secondaryGiven : Bool) : SizePair :=
  { primary := asAbsoluteCount value scaledPrimary,
    secondary :=
      asAbsoluteCount
        (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven)
        scaledSecondary }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- First routine: a single sizing parameter is conditioned against the
   population before it is consumed downstream.  The output must be the absolute
   count `asAbsoluteCount` describes — in particular, when the input was a
   fraction the output is a *whole* count (the scaled value with its fractional
   part discarded, floored at two), never a leftover fractional value. -/
method conditionSizeParameter
    (value : Rat) (scaled : Rat) (population : Nat) return (out : Rat)
  require 0 < value
  require 1 ≤ population
  require scaledFromPopulation scaled value population
  ensures out = asAbsoluteCount value scaled
  do
    -- impl-start
    let mut size : Rat := value
    if value ≤ 1 then
      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
    return size
    -- impl-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Second routine: two sizing parameters are conditioned.  The primary one is
   conditioned first.  The secondary one is optional: when it is not supplied it
   defaults to the (already conditioned) primary value, and either way it is
   then conditioned against the population in the same manner.  Both outputs must
   be the absolute counts `asAbsoluteCount` describes. -/
method resolvePairedSizes
    (value : Rat) (secondaryValue : Rat) (scaledPrimary : Rat) (scaledSecondary : Rat)
    (secondaryGiven : Bool) (population : Nat) return (out : SizePair)
  require 0 < value
  require 0 < secondaryValue
  require 1 ≤ population
  require scaledFromPopulation scaledPrimary value population
  require scaledFromPopulation scaledSecondary
    (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven) population
  ensures out =
    resolvedPairedSizes value secondaryValue scaledPrimary scaledSecondary secondaryGiven
  do
    -- impl-start
    let mut primary : Rat := value
    if value ≤ 1 then
      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
    let mut secondary : Rat := primary
    if secondaryGiven then
      secondary := secondaryValue
    if secondary ≤ 1 then
      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
    return { primary := primary, secondary := secondary }
    -- impl-end

prove_correct conditionSizeParameter by
  loom_solve <;> simp_all [asAbsoluteCount]

prove_correct resolvePairedSizes by
  loom_solve <;> simp_all [resolvedPairedSizes, pairedSecondarySource, asAbsoluteCount]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 13 same-spec attacks + positive control, all confirmed byte-identical in the spec regions via swebench_unified.markers.same_spec (all True; attacks generated by gen.py which asserts the two impl-start/impl-end regions match verbatim and edits ONLY those). Verified with `bash scripts/lean_verify.sh <file>` from the repo root, launched 3-4 concurrently as background jobs.

POSITIVE CONTROL: pos_control.lean (byte copy of the shipped Solution.lean) -> EXIT=0 (verifies, no sorry).

### ATTACK RESULTS (exit 1 = rejected by the frozen spec = spec is strong here):
- atk_1 PREPATCH BUG re-encode (`max 2 scaled`, no truncation, BOTH methods) -> EXIT=1. Rejected on exactly the documented G-DIFF discriminator: `2 sup scaled = up(max 2 scaled.floor)`. prepatch_reproduced = true.
- atk_2 UNGROUNDED-ORACLE ECHO: ignores the band-constrained `scaled` input and recomputes the product exactly in Rat (`Rat.floor (value * population)`) -- the unfaithful revision the faithfulness panel killed (0.7*90 -> exact 63 vs real machine 62) -> EXIT=1. The spec does NOT admit the idealized-product surrogate; it pins the count of the value actually produced.
- atk_3 BOUNDARY: `Rat.ceil` instead of `Rat.floor` (round the fraction up) -> EXIT=1.
- atk_4 BOUNDARY on the branch guard: `value < 1` instead of `value <= 1` (mis-handles value = 1) -> EXIT=1.
- atk_5 CLAMP DROPPED: truncates but never floors the count at two -> EXIT=1.
- atk_6 PARTIAL DOMAIN: conditions only when `1 < scaled`, leaving a fractional residue on the tiny-fraction / small-population corner -> EXIT=1. This is the exact defect class of the original bug and the spec catches it.
- atk_7 CONTROL-FLOW EFFECT / wrong dataflow: secondary conditioned against scaledPrimary, dropping the second callee's product -> EXIT=1.
- atk_8 REROUTED: `floor (max 2 scaled)` instead of `max 2 (floor scaled)` -> EXIT=1 on `(2 sup scaled).floor = max 2 scaled.floor`.
- atk_9 DEAD-BRANCH ELISION: skips secondary conditioning on the default path -> EXIT=1 on `up(max 2 scaledPrimary.floor) <= 1 -> ...`.
- atk_10 VACUOUS-GUARD (population = 0, excluded by `require 1 <= population`) -> EXIT=0 VERIFIES. Mandatory resolve executed, see below.
- atk_11 VACUOUS-GUARD (value = 0 / secondary = 0, excluded by `require 0 < value`) -> EXIT=1. Notably this does NOT go vacuous on the paired method: the secondary branch guard `secondary = 0` is reachable because `0 < secondaryValue` does not constrain the defaulted-from-primary path the way the probe needs, so the spec rejects it.
- atk_12 BAND-CONSUMED shortcut: returns the literal 2 when population = 1 (where the band forces floor scaled <= 1) -> EXIT=1. The band precondition is NOT strong enough to license the shortcut, i.e. the spec is not over-constraining the input.
- atk_13 DATAFLOW: the `min_cluster_size = min_samples` default hoisted ABOVE the primary conditioning, so the secondary defaults to the RAW rather than the CONDITIONED primary -> EXIT=1. This pins refinement.md leg B2 exactly.

### MANDATORY RESOLVE (the one verifying attack):
  Patch: atk_10.patch
  Command: python -u -c "from swebench_unified.harness import run_resolve; r = run_resolve('scikit-learn__scikit-learn-14496', open('.../atk_10.patch').read()); print(r.resolved, r.report)"
  OBSERVED: RESOLVED=True (note: 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'; patch_successfully_applied=True; FAIL_TO_PASS test_extract_xi in success, failure=[]; PASS_TO_PASS 40 success, failure=[]). => NOT a break. This is the expected outcome for a vacuous-guard probe: the guarded state is excluded by a precondition that the real callee `_validate_size` genuinely enforces, so the faithful patch's extra branch is dead code.

### A-LEG AUDIT (refinement.md / mapping.md):
- Leg tags: A1, A1b, A5, B2, B5 = R; A2, A3(part), A4, B1, B3, B4 = I; A3/B1/B4's changed op = A-reference (deep model). NO A-consumed legs and NO kind-3 legs. The axioms region is empty and says so -- the changed op is spelled out in the `pure` region (`asAbsoluteCount` with `Rat.floor`), never axiomatized, satisfying SPEC_GUIDE directive 7. Confirmed by reading the axioms-start/axioms-end block: no `axiom` declarations exist, so there is no dead or over-claimed axiom and no way to smuggle the fix into a hypothesis.
- A-reference correspondence INDEPENDENTLY re-fuzzed (I did not trust axiom_check.py): 299,625 in-domain inputs (value in (0,1], populations 1..1e6, plus the named witnesses 0.7@90/170/180, 0.29@100, 0.03@100, 0.6@90 and the F2P values 0.1/0.08@31), comparing the real patched expression `max(2, int(value*n_samples))` against the model `max(2, math.floor(Fraction(fl(value*n_samples))))` with `scaled` bound to the actual machine product. Result: trunc_mismatch = 0, band_violations = 0. Both legs of mapping.md 3.1 hold: the 2^-53 relative band of `scaledFromPopulation` is sound for IEEE double multiplication, and the truncation is EXACT with zero tolerated divergences. The 0.7@90 -> 62 witness that killed the earlier exact-rational revision is reproduced and matched by the current model.
- `_validate_size` at base_commit reads `if size <= 0 or (size != int(size) and size > 1): raise ... elif size > n_samples: raise`, so the non-raising domain gives `0 < size` and `size <= n_samples`. The spec's `require 0 < value` / `require 1 <= population` are implied by (and strictly weaker than) that guard, so capturing it as a precondition rather than an axiom is faithful and conservative -- it does not shrink the domain below what the real code accepts in a way that would hide the bug.
- The scaled-value-as-INPUT decision is load-bearing and correct: atk_2 confirms the spec rejects any impl that recomputes the product exactly, which is precisely the unfaithfulness the previous revision had.

CONCLUSION: the prepatch bug and 11 further distinct wrong impls (partial-domain, two boundary, clamp-dropped, two control-flow/dataflow, rerouted, dead-branch, ungrounded-oracle echo, band-shortcut) are all REJECTED by the frozen spec; the single verifying candidate is a provably-dead vacuous guard whose faithful patch RESOLVES under the official harness. No verify-but-not-correct witness exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 13 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only verifying wrong-impl candidate (atk_10, a vacuous-guard probe returning 0 when population = 0, a state excluded by `require 1 <= population`) had its faithful refined patch materialized and RUN through the official harness: RESOLVED=True (FAIL_TO_PASS sklearn/cluster/tests/test_optics.py::test_extract_xi success; 40/40 PASS_TO_PASS success). The guard is unreachable in the real repo because n_samples = X.shape[0] / len(reachability) is >= 1 on any array that reaches the conditioning step, and `_validate_size` raises on size > n_samples, so the extra branch is dead code and cannot change behaviour. No verifying impl produced a non-resolving patch, so verify => correct was not falsified.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. A size-validation guard runs before the conditioning
   step and only restricts the input domain; its guarantee is captured as a
   `require` precondition rather than an axiom, so there is no dead/over-claimed
   axiom (SPEC_GUIDE §0 directive 7). -/
-- axioms-end

-- pure-start
/- A sizing parameter may be given in two forms: as an absolute count (a value
   strictly greater than one) or as a fraction of the population (a value in the
   half-open interval (0, 1]).  When it is given as a fraction it must be turned
   into a concrete absolute count: take the value it scales to against the
   population, reduce that to a whole number by discarding any fractional part,
   and never let the result fall below two.  When the parameter is already an
   absolute count it is used as-is.

   The scaling is performed in the ambient inexact numeric type, so the scaled
   value the conditioning step actually receives is only guaranteed to agree with
   the ideal product to within that type's relative precision — one part in
   2^53.  It is therefore an INPUT to the routines below (`scaled`) rather than
   something recomputed here, and the contracts pin the reduction to a whole
   count *of the value that was actually produced*.  `scaledFromPopulation`
   states exactly that admissible relationship; a routine may not invent a
   different scaled value.

   Modeled with `Rat`: once the scaled value is in hand the remaining behavior is
   an exact order/integer relation (discard the fractional part, clamp), and on a
   non-negative value discarding the fractional part coincides with the floor, so
   `Rat.floor` models it exactly (mapping.md §2). -/
def scaledFromPopulation (scaled value : Rat) (population : Nat) : Prop :=
  value * (population : Rat) - value * (population : Rat) / 9007199254740992 ≤ scaled ∧
    scaled ≤ value * (population : Rat) + value * (population : Rat) / 9007199254740992

def asAbsoluteCount (value scaled : Rat) : Rat :=
  if value ≤ 1 then
    (((max 2 (Rat.floor scaled)) : Int) : Rat)
  else
    value

structure SizePair where
  primary   : Rat
  secondary : Rat
deriving DecidableEq

/- The secondary parameter is optional: when it is not supplied it defaults to
   the already-conditioned primary value. -/
def pairedSecondarySource
    (value scaledPrimary secondaryValue : Rat) (secondaryGiven : Bool) : Rat :=
  if secondaryGiven then secondaryValue else asAbsoluteCount value scaledPrimary

/- The conditioned pair: condition the primary; the secondary is the supplied
   value if present, otherwise the conditioned primary, and is then conditioned
   in turn. -/
def resolvedPairedSizes
    (value secondaryValue scaledPrimary scaledSecondary : Rat)
    (secondaryGiven : Bool) : SizePair :=
  { primary := asAbsoluteCount value scaledPrimary,
    secondary :=
      asAbsoluteCount
        (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven)
        scaledSecondary }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- First routine: a single sizing parameter is conditioned against the
   population before it is consumed downstream.  The output must be the absolute
   count `asAbsoluteCount` describes — in particular, when the input was a
   fraction the output is a *whole* count (the scaled value with its fractional
   part discarded, floored at two), never a leftover fractional value. -/
method conditionSizeParameter
    (value : Rat) (scaled : Rat) (population : Nat) return (out : Rat)
  require 0 < value
  require 1 ≤ population
  require scaledFromPopulation scaled value population
  ensures out = asAbsoluteCount value scaled
  do
    -- impl-start
    let mut size : Rat := value
    if value ≤ 1 then
      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
    return size
    -- impl-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Second routine: two sizing parameters are conditioned.  The primary one is
   conditioned first.  The secondary one is optional: when it is not supplied it
   defaults to the (already conditioned) primary value, and either way it is
   then conditioned against the population in the same manner.  Both outputs must
   be the absolute counts `asAbsoluteCount` describes. -/
method resolvePairedSizes
    (value : Rat) (secondaryValue : Rat) (scaledPrimary : Rat) (scaledSecondary : Rat)
    (secondaryGiven : Bool) (population : Nat) return (out : SizePair)
  require 0 < value
  require 0 < secondaryValue
  require 1 ≤ population
  require scaledFromPopulation scaledPrimary value population
  require scaledFromPopulation scaledSecondary
    (pairedSecondarySource value scaledPrimary secondaryValue secondaryGiven) population
  ensures out =
    resolvedPairedSizes value secondaryValue scaledPrimary scaledSecondary secondaryGiven
  do
    -- impl-start
    let mut primary : Rat := value
    if value ≤ 1 then
      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
    let mut secondary : Rat := primary
    if secondaryGiven then
      secondary := secondaryValue
    if secondary ≤ 1 then
      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
    return { primary := primary, secondary := secondary }
    -- impl-end

prove_correct conditionSizeParameter by
  loom_solve <;> simp_all [asAbsoluteCount]

prove_correct resolvePairedSizes by
  loom_solve <;> simp_all [resolvedPairedSizes, pairedSecondarySource, asAbsoluteCount]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 13 same-spec attacks + positive control, all confirmed byte-identical in the spec regions via swebench_unified.markers.same_spec (all True; attacks generated by gen.py which asserts the two impl-start/impl-end regions match verbatim and edits ONLY those). Verified with `bash scripts/lean_verify.sh <file>` from the repo root, launched 3-4 concurrently as background jobs.

POSITIVE CONTROL: pos_control.lean (byte copy of the shipped Solution.lean) -> EXIT=0 (verifies, no sorry).

### ATTACK RESULTS (exit 1 = rejected by the frozen spec = spec is strong here):
- atk_1 PREPATCH BUG re-encode (`max 2 scaled`, no truncation, BOTH methods) -> EXIT=1. Rejected on exactly the documented G-DIFF discriminator: `2 sup scaled = up(max 2 scaled.floor)`. prepatch_reproduced = true.
- atk_2 UNGROUNDED-ORACLE ECHO: ignores the band-constrained `scaled` input and recomputes the product exactly in Rat (`Rat.floor (value * population)`) -- the unfaithful revision the faithfulness panel killed (0.7*90 -> exact 63 vs real machine 62) -> EXIT=1. The spec does NOT admit the idealized-product surrogate; it pins the count of the value actually produced.
- atk_3 BOUNDARY: `Rat.ceil` instead of `Rat.floor` (round the fraction up) -> EXIT=1.
- atk_4 BOUNDARY on the branch guard: `value < 1` instead of `value <= 1` (mis-handles value = 1) -> EXIT=1.
- atk_5 CLAMP DROPPED: truncates but never floors the count at two -> EXIT=1.
- atk_6 PARTIAL DOMAIN: conditions only when `1 < scaled`, leaving a fractional residue on the tiny-fraction / small-population corner -> EXIT=1. This is the exact defect class of the original bug and the spec catches it.
- atk_7 CONTROL-FLOW EFFECT / wrong dataflow: secondary conditioned against scaledPrimary, dropping the second callee's product -> EXIT=1.
- atk_8 REROUTED: `floor (max 2 scaled)` instead of `max 2 (floor scaled)` -> EXIT=1 on `(2 sup scaled).floor = max 2 scaled.floor`.
- atk_9 DEAD-BRANCH ELISION: skips secondary conditioning on the default path -> EXIT=1 on `up(max 2 scaledPrimary.floor) <= 1 -> ...`.
- atk_10 VACUOUS-GUARD (population = 0, excluded by `require 1 <= population`) -> EXIT=0 VERIFIES. Mandatory resolve executed, see below.
- atk_11 VACUOUS-GUARD (value = 0 / secondary = 0, excluded by `require 0 < value`) -> EXIT=1. Notably this does NOT go vacuous on the paired method: the secondary branch guard `secondary = 0` is reachable because `0 < secondaryValue` does not constrain the defaulted-from-primary path the way the probe needs, so the spec rejects it.
- atk_12 BAND-CONSUMED shortcut: returns the literal 2 when population = 1 (where the band forces floor scaled <= 1) -> EXIT=1. The band precondition is NOT strong enough to license the shortcut, i.e. the spec is not over-constraining the input.
- atk_13 DATAFLOW: the `min_cluster_size = min_samples` default hoisted ABOVE the primary conditioning, so the secondary defaults to the RAW rather than the CONDITIONED primary -> EXIT=1. This pins refinement.md leg B2 exactly.

### MANDATORY RESOLVE (the one verifying attack):
  Patch: atk_10.patch
  Command: python -u -c "from swebench_unified.harness import run_resolve; r = run_resolve('scikit-learn__scikit-learn-14496', open('.../atk_10.patch').read()); print(r.resolved, r.report)"
  OBSERVED: RESOLVED=True (note: 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'; patch_successfully_applied=True; FAIL_TO_PASS test_extract_xi in success, failure=[]; PASS_TO_PASS 40 success, failure=[]). => NOT a break. This is the expected outcome for a vacuous-guard probe: the guarded state is excluded by a precondition that the real callee `_validate_size` genuinely enforces, so the faithful patch's extra branch is dead code.

### A-LEG AUDIT (refinement.md / mapping.md):
- Leg tags: A1, A1b, A5, B2, B5 = R; A2, A3(part), A4, B1, B3, B4 = I; A3/B1/B4's changed op = A-reference (deep model). NO A-consumed legs and NO kind-3 legs. The axioms region is empty and says so -- the changed op is spelled out in the `pure` region (`asAbsoluteCount` with `Rat.floor`), never axiomatized, satisfying SPEC_GUIDE directive 7. Confirmed by reading the axioms-start/axioms-end block: no `axiom` declarations exist, so there is no dead or over-claimed axiom and no way to smuggle the fix into a hypothesis.
- A-reference correspondence INDEPENDENTLY re-fuzzed (I did not trust axiom_check.py): 299,625 in-domain inputs (value in (0,1], populations 1..1e6, plus the named witnesses 0.7@90/170/180, 0.29@100, 0.03@100, 0.6@90 and the F2P values 0.1/0.08@31), comparing the real patched expression `max(2, int(value*n_samples))` against the model `max(2, math.floor(Fraction(fl(value*n_samples))))` with `scaled` bound to the actual machine product. Result: trunc_mismatch = 0, band_violations = 0. Both legs of mapping.md 3.1 hold: the 2^-53 relative band of `scaledFromPopulation` is sound for IEEE double multiplication, and the truncation is EXACT with zero tolerated divergences. The 0.7@90 -> 62 witness that killed the earlier exact-rational revision is reproduced and matched by the current model.
- `_validate_size` at base_commit reads `if size <= 0 or (size != int(size) and size > 1): raise ... elif size > n_samples: raise`, so the non-raising domain gives `0 < size` and `size <= n_samples`. The spec's `require 0 < value` / `require 1 <= population` are implied by (and strictly weaker than) that guard, so capturing it as a precondition rather than an axiom is faithful and conservative -- it does not shrink the domain below what the real code accepts in a way that would hide the bug.
- The scaled-value-as-INPUT decision is load-bearing and correct: atk_2 confirms the spec rejects any impl that recomputes the product exactly, which is precisely the unfaithfulness the previous revision had.

CONCLUSION: the prepatch bug and 11 further distinct wrong impls (partial-domain, two boundary, clamp-dropped, two control-flow/dataflow, rerouted, dead-branch, ungrounded-oracle echo, band-shortcut) are all REJECTED by the frozen spec; the single verifying candidate is a provably-dead vacuous guard whose faithful patch RESOLVES under the official harness. No verify-but-not-correct witness exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ARTIFACT STATE: Solution.lean verifies clean (lean_verify.sh exit 0). markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True, so the spec region is byte-identical across the rival triple. Both rivals FAIL (exit 1), each on the discriminating goal `2 ⊔ scaled = ↑(max 2 scaled.floor)` (and the paired analogue for scaledPrimary/scaledSecondary in rival 2) — the spec is non-vacuous and genuinely pins the added `int(...)` truncation.

MODELED UNIT: conditioning block bodies at optics_.py:439-440 (site 1) and 619-627 (site 2), base_commit d49a6f13af. _validate_size (optics_.py:280) is unchanged by the fix and captured as `require`, not an axiom.

LEG 1 — BAND SOUNDNESS of scaledFromPopulation (the 2^-53 relative band around value*population). Zero violations across ~1.09M inputs with population <= 2^53: 341k mixed/structured (exact-decimal v, powers of two, 1-2^-k), 634k adversarial, 150k subnormal-range (v = k*5e-324, products crossing into normal range, smallest-normal neighborhood). Max observed relative error for n <= 2^53 is 1.1089e-16 = 0.9988 * 2^-53 — inside the band with margin, and zero exact-tie cases (|s-i| == i/2^53) were produced, so the inclusive endpoints are never load-bearing.
  Residual over-claim, unreachable: the band DOES break once population > 2^53, first at n = 9007199254740995 (v=0.7: fl == 6305039478318697 vs ideal 6305039478318696), because Python converts the int operand to double and double-rounds. This is not a divergence of the modeled function from the real callee on any reachable input — population is `X.shape[0]` / `len(reachability)`, so n > 2^53 would need a ~9e15-element array. I did NOT count this as a defect, but I record it as the exact boundary of the claim in mapping.md §2.1 ("the guarantee IEEE double multiplication honors" is honored only for |n| <= 2^53, not universally).

LEG 2 — TRUNCATION EXACTNESS. With `scaled` bound to the REAL machine product, `max(2, Rat.floor scaled)` == `max(2, int(value * n_samples))` with ZERO mismatches over ~1.5M inputs: 357k site-1 + 180k site-2 differential vs the patched Python executed directly; 634k adversarial boundary hunt (for each n and target integer k, v swept over k/n and two nextafter steps either side, so fl(v*n) straddles k in both directions); 200k numpy dtypes (np.float64/np.float32/np.int64 — the types the estimator actually receives); 150k subnormals. The old revision's witness class is now handled correctly: 0.7 @ 90 -> real 62, model floor(62.99999999999999) = 62; likewise 0.03@100, 0.29@100, 0.6@90, 0.7@170/180. F2P values reproduce exactly: 0.1/0.08 @ n=31 -> 3 and 2 in both. Sign is safe — require 0<value with 1<=population forces ideal>0 hence scaled>0, so Rat.floor and Python truncation-toward-zero coincide (no negative-input gap).

LEG 3 — SITE-2 SECONDARY DATAFLOW (the sharpest candidate for an over-strong claim). resolvedPairedSizes applies asAbsoluteCount a SECOND time on the None path, where the real code instead re-tests `if min_cluster_size <= 1` after `min_cluster_size = min_samples`. These agree only if the conditioned primary is always > 1. Verified: over 300k mixed fraction/absolute inputs the conditioned primary is > 1 in every case, so the model's second conditioning fires 0 times and the guard is a no-op exactly as in the repo. Sound, though it is a real coupling the narrative understates (refinement.md B2 calls it plain R+I).

LEG 4 — DOMAIN GAP. The requires (0 < value, 1 <= population) are strictly WEAKER than what _validate_size guarantees: inputs like value=1.5/n=10, value=10/n=3 satisfy the requires but make the real function RAISE ValueError. Weaker preconditions make the postcondition obligation harder, not easier, so this cannot hide a divergence — and I confirmed the block-level model still agrees on precisely those raise-domain inputs (200k cases, 0 mismatches), consistent with mapping.md's framing of _validate_size as a separate unchanged callee running before the modeled block. Also checked value=1.0/n=1 (site 1 -> 2, agrees) and the site-2 None path at n=1, where the real code raises on the min_cluster_size bound — again a raise-domain input, not a value disagreement.

CONCLUSION: I could not construct a reachable input on which the modeled function disagrees with the real callee. The faithfulness repair (hoisting the IEEE product to an input constrained by a relative band, rather than recomputing it in exact rationals) is the correct fix for the prior defect, and it left the changed operation — the truncation — modeled deeply and still discriminating. No diverging input, so no defect to claim. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** AUDITED ARTIFACT IDENTITY. Regenerated the consumer spec view via swebench_unified.markers.spec_view(velvet backend): sha256 = a2e3317bb27ea1cd082a11f8064ef5abf8682cf7ec17d0498081dd78d21db17b, byte-identical to meta.json gates.G-HYGIENE.data.region_hashes.spec_view, so the view I screened is the one that ships. Elision complete and idempotent: spec_view(spec_view(x))==spec_view(x); no 'let mut', no 'Rat.floor scaledPrimary', no 'loom_solve'/'simp_all' survive. same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True (spec region byte-identical; only impl differs). scripts/lean_verify.sh Solution.lean -> EXIT=0. patch.diff == instance.json['patch'] (verbatim gold).

MECHANICAL SCREEN + POSITIVE CONTROLS. leakage.screen(...) against the frozen problem_statement returns zero hard failures and zero warnings. I refused to trust a clean result without proving the screen is live, so I injected five leaks into the spec view: (C1) 'sklearn/cluster/optics_.py' -> fired L2; (C2) 'cluster_optics_xi' (a hints_text-only symbol) -> fired L2/L3; (C3) the gold line 'min_cluster_size = max(2, int(min_cluster_size * n_samples))' -> fired L1; (C4) 'this fixes the bug' -> fired L3. Four of five controls fire, so the clean verdict is meaningful.

HARNESS BLIND SPOT FOUND (not a defect of this bundle). Control C5 renamed asAbsoluteCount -> clusterOpticsXiCount and the screen did NOT fire: leakage.screen's identifier check tests `sym.lower() in ident.lower()`, so an underscored repo symbol ('cluster_optics_xi') can never match a camel-cased Lean identifier that spells it out. I therefore did not rely on the screen for identifier echoes and ran an independent punctuation-squashed check of every identifier (len>=6) in the real optics_.py against the squashed spec view. Only generic English words collide (number, fraction, parameter, integer, absolute, default, ...). The spec view's declared identifiers are all abstract: conditionSizeParameter, resolvePairedSizes, asAbsoluteCount, scaledFromPopulation, pairedSecondarySource, resolvedPairedSizes, SizePair, population, scaled, secondaryGiven. None echoes min_samples, min_cluster_size, n_samples, optics, OPTICS, cluster_optics_xi, compute_optics_graph, _validate_size, _xi_cluster, or NearestNeighbors. No file path, no dotted module path, no diff markers, no narration vocabulary.

HINTS-ONLY CONTAINMENT (the rule that matters most here). The multi-site instruction lives ONLY in hints_text ('please fix similar issues in cluster_optics_xi'), never in problem_statement. Confirmed absent from the spec view: cluster_optics_xi, min_cluster_size, python2, 0.21, whats_new. Test identity also absent: test_extract_xi, expected_labels, cluster_method, max_eps, and the F2P constants 0.1 / 0.08 / 31.

TWO CLOSEST CALLS, BOTH RESOLVED AGAINST LEAKAGE WITH EVIDENCE.

(A) The spec view models TWO routines, the second with an optional secondary parameter defaulting to the conditioned primary -- while problem_statement mentions only l439-440. Does the two-method shape hand over localization only hints_text carries? Tested in a real worktree at base_commit d49a6f13: grepping the line problem_statement itself quotes verbatim ('min_samples = max(2, min_samples * n_samples)') returns BOTH optics_.py:440 and :622, and the ten lines around 622 expose the third site (min_cluster_size at :627) together with 'if min_cluster_size is None: min_cluster_size = min_samples'. So all three edit sites and the None-defaults dataflow are derivable from the public statement alone. The spec view confers no localization the public task withholds; covering every site is a faithfulness obligation, not leakage.

(B) The spec view pins TRUNCATION ('discarding any fractional part', Rat.floor) whereas problem_statement proposes int(round(...)) -- i.e. the spec resolves a public-vs-gold discrepancy in gold's favor. Weighed carefully and rejected as leakage on two grounds. First, the mechanism itself is already public: the token 'int(' and the phrase 'the int(...) is for backwards compatibility' appear verbatim in problem_statement, as does the docstring language 'rounded to be at least 2', so 'wrap the scaled value in an integer conversion, floor at 2' is public knowledge. Second, the residual floor-vs-round choice is not test-discriminating: at the F2P inputs 0.1@n=31 -> 3 and 0.08@n=31 -> 2 under BOTH truncation and rounding, and PASS_TO_PASS contains no float min_samples/min_cluster_size case. The spec view is more precise than a sloppy issue -- which in modes 1/2 is the artifact's intended value -- without quoting the edit, naming a patched symbol, or narrating bug->fix.

CONCLUSION: the spec view states abstract desired behavior (condition a sizing parameter given as a fraction of a population into a whole count clamped at two, with an optional second parameter defaulting to the first) in fully de-narrated, repo-agnostic vocabulary. Nothing in it reconstructs the gold edit beyond the public problem_statement. Worktree removed after the audit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.