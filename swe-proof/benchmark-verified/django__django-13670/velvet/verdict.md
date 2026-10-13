# P2 adversarial audit — django__django-13670

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no counterexample to verify⇒correct. The postcondition `out = twoDigitString (year % 100)` is a total, concrete equational pin (twoDigitString n = [digitChar (n/10%10), digitChar (n%10)], digitChar d = Char.ofNat (48 + d%10)); every behaviorally-wrong impl leaves the false residual goal `<wrong RHS> = twoDigitString (year % 100)` and fails elaboration (exit 1).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -41,10 +41,15 @@
   ensures out = twoDigitString (year % 100)
   do
     -- impl-start
-    let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    let out : List Char :=
+      if year < 100 then []
+      else
+        if year < 1000 then [digitChar (year % 10)]
+        else [digitChar (year / 10 % 10), digitChar (year % 10)]
+    return out
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -42,9 +42,13 @@
   do
     -- impl-start
     let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    let out : List Char :=
+      if n < 10 then [digitChar (n % 10)]
+      else [digitChar (n / 10 % 10), digitChar (n % 10)]
+    return out
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -42,9 +42,10 @@
   do
     -- impl-start
     let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    return [digitChar (n % 10), digitChar (n / 10 % 10)]
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -41,10 +41,11 @@
   ensures out = twoDigitString (year % 100)
   do
     -- impl-start
-    let n := year % 100
+    let n := year % 10
     return [digitChar (n / 10 % 10), digitChar (n % 10)]
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -41,10 +41,10 @@
   ensures out = twoDigitString (year % 100)
   do
     -- impl-start
-    let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    return [digitChar 0, digitChar 0]
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -42,9 +42,13 @@
   do
     -- impl-start
     let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    let out : List Char :=
+      if year % 2 = 0 then [digitChar (n / 10 % 10), digitChar (n % 10)]
+      else [digitChar (n % 10), digitChar (n / 10 % 10)]
+    return out
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
@@ -42,9 +42,10 @@
   do
     -- impl-start
     let n := year % 100
-    return [digitChar (n / 10 % 10), digitChar (n % 10)]
+    return [digitChar (n / 10 % 10 + 1), digitChar (n % 10)]
     -- impl-end
 
 prove_correct twoDigitYear by
   loom_solve
-  simp [twoDigitString]
+  simp [twoDigitString, digitChar]
+  <;> (try omega) <;> (try decide) <;> (try rfl)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
--  rendering is a pure character computation modeled in full below.)
-- axioms-end

-- pure-start
/- A single decimal digit (0..9) as its ASCII character. `48` is the code point
   of '0'; clamping by `% 10` keeps the map total. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d % 10)

/- The two-character short rendering of a number: its value reduced to the last
   two decimal places, written as exactly two characters — tens digit then ones
   digit — so a value below ten still occupies two slots (a leading '0'). -/
def twoDigitString (n : Nat) : List Char :=
  [digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The abbreviated form of a calendar year: the part of the year below one
   hundred, written as a fixed-width two-character decimal. The year is a
   non-negative count below ten thousand (the only values a calendar date
   carries). The output is always exactly two characters: when the sub-hundred
   part is a single digit it is filled on the left with a zero, so the width
   never collapses for small values. Nothing is mutated (directive 5); the year
   is read-only and the result is a fresh character sequence. -/
method twoDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = twoDigitString (year % 100)
  do
    -- impl-start
    let n := year % 100
    return [digitChar (n / 10 % 10), digitChar (n % 10)]
    -- impl-end

prove_correct twoDigitYear by
  loom_solve
  simp [twoDigitString]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL SUMMARY (velvet, django__django-13670). Attacks built by copying Solution.lean and editing ONLY the impl region + proof (axioms/pure/pre/post byte-identical).

SAME-SPEC (all True, verified with swebench_unified.markers.same_spec + get_backend('velvet').language): atk_1..atk_7, pos, pos_gold all same_spec=True vs Solution.lean.

### VERIFY (bash scripts/lean_verify.sh <f>; run concurrently ≤4 at a time):
  atk_1 (PREPATCH BUG: str(year)[2:] decimal-width case split []/[ones]/[tens,ones]) -> exit 1 (1000 diffs, e.g. year 0 -> '' vs '00')
  atk_2 (no zero-pad: single char when n<10) -> exit 1 (1000 diffs, e.g. 0 -> '0' vs '00')
  atk_3 (swapped tens/ones digits) -> exit 1 (9000 diffs, e.g. 1 -> '10' vs '01')
  atk_4 (% 10 instead of % 100 - wrong-modulus/boundary) -> exit 1 (9000 diffs, e.g. 10 -> '00' vs '10')
  atk_5 (constant "00" - ungrounded/degenerate) -> exit 1 (9900 diffs)
  atk_6 (partial-domain/control-flow-effect: correct on even years, swapped digits on odd) -> exit 1 (4500 diffs, e.g. 1 -> '10' vs '01')
  atk_7 (boundary off-by-one on tens digit, +1) -> exit 1 (10000 diffs, e.g. 0 -> '10' vs '00')
  => 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-modulus, no-pad, digit-swap, ungrounded-constant); ALL are genuinely behaviorally wrong (independent diff-count over years 0..9999 all nonzero) AND ALL fail Lean verification. NONE verifies.

POSITIVE CONTROLS (must verify): pos_gold (exact gold impl, `let n := year % 100; return [digitChar (n/10%10), digitChar (n%10)]`, proof `loom_solve; simp [twoDigitString]`) -> exit 0. pos (STRUCTURALLY DISTINCT correct algorithm: renders last two digits of the FULL year with no %100, `return [digitChar (year/10%10), digitChar (year%10)]`; proof discharges year%10 = year%100%10 and year/10%10 = year%100/10%10 via omega then rw) -> exit 0. Spec is non-vacuous and satisfiable from >=2 structurally-distinct angles.

PATCHES/RESOLVE: no wrong impl verifies, so per protocol step 2 there is NO faithful refined patch to materialize and NO run_resolve execution is required or possible; the verify=>correct implication is not falsifiable here. patches={} accordingly.

A-LEG / DEEP-MODEL AUDIT (my mandated focus): meta.json axioms=[] and deep_model_references=[]; mapping.md §3 confirms the patched expression '%02d' % (self.data.year % 100) calls NO repo callee (only integer % and %-string formatting, both Python primitives). Therefore there are NO A-legs (no axiomatized callee, no deep-model reference) to attack and no axiom_check.py; G-AX correctly VACUOUS/skip. refinement.md legs: A1 = R (int<->Nat; require year<=9999 exactly matches real MAXYEAR=9999, and modeled domain Nat∩{<=9999} is a SUPERSET of reachable 1..9999, so the verified proof covers every reachable year and the R type-refinement cannot hide a mismatch); A2 = I (Nat.mod <-> Python %); A3 = I (twoDigitString/digitChar <-> '%02d'/chr(48+d)). No kind-3 leg. I-leg correspondence MACHINE-VALIDATED: re-ran conformance_check.py (exit 0, 210013 cases, 0 disagreements) AND independently re-derived shadow twoDigitString(year%100) vs oracle '%02d'%(year%100) over all 0..9999 -> 0 mismatches. Model<->patch correspondence holds.

PREPATCH: atk_1 reproduces the real string-slice bug (str(self.data.year)[2:]) verbatim as a decimal-width case split against the byte-identical spec; it fails exit 1 on the discriminating clause, matching the bundled Solution_prepatch.lean (G-DIFF pass). prepatch_reproduced=true.

CONCLUSION: >=5 distinct same-spec wrong impls run, none verifies; both positive controls verify; no A-legs to break; I-leg correspondence exact. verify=>correct is not falsified. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no counterexample to verify⇒correct. The postcondition `out = twoDigitString (year % 100)` is a total, concrete equational pin (twoDigitString n = [digitChar (n/10%10), digitChar (n%10)], digitChar d = Char.ofNat (48 + d%10)); every behaviorally-wrong impl leaves the false residual goal `<wrong RHS> = twoDigitString (year % 100)` and fails elaboration (exit 1).
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
--  rendering is a pure character computation modeled in full below.)
-- axioms-end

-- pure-start
/- A single decimal digit (0..9) as its ASCII character. `48` is the code point
   of '0'; clamping by `% 10` keeps the map total. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d % 10)

/- The two-character short rendering of a number: its value reduced to the last
   two decimal places, written as exactly two characters — tens digit then ones
   digit — so a value below ten still occupies two slots (a leading '0'). -/
def twoDigitString (n : Nat) : List Char :=
  [digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The abbreviated form of a calendar year: the part of the year below one
   hundred, written as a fixed-width two-character decimal. The year is a
   non-negative count below ten thousand (the only values a calendar date
   carries). The output is always exactly two characters: when the sub-hundred
   part is a single digit it is filled on the left with a zero, so the width
   never collapses for small values. Nothing is mutated (directive 5); the year
   is read-only and the result is a fresh character sequence. -/
method twoDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = twoDigitString (year % 100)
  do
    -- impl-start
    let n := year % 100
    return [digitChar (n / 10 % 10), digitChar (n % 10)]
    -- impl-end

prove_correct twoDigitYear by
  loom_solve
  simp [twoDigitString]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL SUMMARY (velvet, django__django-13670). Attacks built by copying Solution.lean and editing ONLY the impl region + proof (axioms/pure/pre/post byte-identical).

SAME-SPEC (all True, verified with swebench_unified.markers.same_spec + get_backend('velvet').language): atk_1..atk_7, pos, pos_gold all same_spec=True vs Solution.lean.

### VERIFY (bash scripts/lean_verify.sh <f>; run concurrently ≤4 at a time):
  atk_1 (PREPATCH BUG: str(year)[2:] decimal-width case split []/[ones]/[tens,ones]) -> exit 1 (1000 diffs, e.g. year 0 -> '' vs '00')
  atk_2 (no zero-pad: single char when n<10) -> exit 1 (1000 diffs, e.g. 0 -> '0' vs '00')
  atk_3 (swapped tens/ones digits) -> exit 1 (9000 diffs, e.g. 1 -> '10' vs '01')
  atk_4 (% 10 instead of % 100 - wrong-modulus/boundary) -> exit 1 (9000 diffs, e.g. 10 -> '00' vs '10')
  atk_5 (constant "00" - ungrounded/degenerate) -> exit 1 (9900 diffs)
  atk_6 (partial-domain/control-flow-effect: correct on even years, swapped digits on odd) -> exit 1 (4500 diffs, e.g. 1 -> '10' vs '01')
  atk_7 (boundary off-by-one on tens digit, +1) -> exit 1 (10000 diffs, e.g. 0 -> '10' vs '00')
  => 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-modulus, no-pad, digit-swap, ungrounded-constant); ALL are genuinely behaviorally wrong (independent diff-count over years 0..9999 all nonzero) AND ALL fail Lean verification. NONE verifies.

POSITIVE CONTROLS (must verify): pos_gold (exact gold impl, `let n := year % 100; return [digitChar (n/10%10), digitChar (n%10)]`, proof `loom_solve; simp [twoDigitString]`) -> exit 0. pos (STRUCTURALLY DISTINCT correct algorithm: renders last two digits of the FULL year with no %100, `return [digitChar (year/10%10), digitChar (year%10)]`; proof discharges year%10 = year%100%10 and year/10%10 = year%100/10%10 via omega then rw) -> exit 0. Spec is non-vacuous and satisfiable from >=2 structurally-distinct angles.

PATCHES/RESOLVE: no wrong impl verifies, so per protocol step 2 there is NO faithful refined patch to materialize and NO run_resolve execution is required or possible; the verify=>correct implication is not falsifiable here. patches={} accordingly.

A-LEG / DEEP-MODEL AUDIT (my mandated focus): meta.json axioms=[] and deep_model_references=[]; mapping.md §3 confirms the patched expression '%02d' % (self.data.year % 100) calls NO repo callee (only integer % and %-string formatting, both Python primitives). Therefore there are NO A-legs (no axiomatized callee, no deep-model reference) to attack and no axiom_check.py; G-AX correctly VACUOUS/skip. refinement.md legs: A1 = R (int<->Nat; require year<=9999 exactly matches real MAXYEAR=9999, and modeled domain Nat∩{<=9999} is a SUPERSET of reachable 1..9999, so the verified proof covers every reachable year and the R type-refinement cannot hide a mismatch); A2 = I (Nat.mod <-> Python %); A3 = I (twoDigitString/digitChar <-> '%02d'/chr(48+d)). No kind-3 leg. I-leg correspondence MACHINE-VALIDATED: re-ran conformance_check.py (exit 0, 210013 cases, 0 disagreements) AND independently re-derived shadow twoDigitString(year%100) vs oracle '%02d'%(year%100) over all 0..9999 -> 0 mismatches. Model<->patch correspondence holds.

PREPATCH: atk_1 reproduces the real string-slice bug (str(self.data.year)[2:]) verbatim as a decimal-width case split against the byte-identical spec; it fails exit 1 on the discriminating clause, matching the bundled Solution_prepatch.lean (G-DIFF pass). prepatch_reproduced=true.

CONCLUSION: >=5 distinct same-spec wrong impls run, none verifies; both positive controls verify; no A-legs to break; I-leg correspondence exact. verify=>correct is not falsified. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13670 velvet bundle. FINDINGS:

1. SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend.language) returns True. The spec view (axioms/pure/pre/post + method signature+require+ensures) is preserved between prepatch skeleton and patched Solution; only impl and proof differ. No spec smuggling.

2. LEAN VERIFIES: scripts/lean_verify.sh on Solution.lean exits 0 (loom_solve + simp [twoDigitString]).

3. SPEC: method twoDigitYear (year : Nat), require year <= 9999, ensures out = twoDigitString (year % 100), where twoDigitString n = [digitChar (n/10%10), digitChar (n%10)] and digitChar d = Char.ofNat(48 + d%10). This models the gold-patched DateFormat.y = '%02d' % (self.data.year % 100).

4. REAL CALLEE at base_commit c448e614 (django/utils/dateformat.py:324) is the PREPATCH buggy `str(self.data.year)[2:]`; gold patch replaces it with `'%02d' % (self.data.year % 100)`. The spec models the PATCHED behavior (correct — the modeled function should equal the fixed callee).

5. DIRECT DIFFERENTIAL TEST vs REAL REPO: monkey-patched the gold expression onto an actual django.utils.dateformat.DateFormat instance and compared to the spec formula twoDigitString(year%100) over the ENTIRE reachable domain year in 1..9999 (MINYEAR..MAXYEAR). Result: 0 mismatches. conformance_check.py independently confirms 0 disagreements over exhaustive 0..9999 + 200k fuzz (seed 13670).

6. DOMAIN: require year <= 9999 exactly matches stdlib MAXYEAR=9999 upper bound; Nat covers 1..9999. year=0 is in-Nat but unreachable (date year>=1); even there spec gives '00' matching '%02d'%(0%100). No over-broad or under-broad domain divergence.

7. NO AXIOMS: rendering modeled in full (integer % and %-string formatting are Python primitives), so there is no abstraction/callee gap to exploit for divergence.

CONCLUSION: The modeled function agrees with the real (patched) callee on every reachable input. The spec is not too strong and does not drift. No diverging input exists. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projected region) computed via markers.spec_view; same_spec(Solution, Solution_prepatch) = True (byte-identical spec), so I judged the canonical consumer view. Mechanical leakage.screen passes (no hard failures).

Gold edit: `return '%02d' % (self.data.year % 100)` — reduce year mod 100, zero-pad to width 2. The public problem_statement ALREADY discloses this exact behavior: it reports that 'y' prints no leading zero and is inconsistent with python's %y, giving worked examples (year 123 -> should be '23', matching python/php), i.e. 'last two decimal digits, zero-padded to width 2' is public knowledge, not hidden.

Spec view pins `ensures out = twoDigitString (year % 100)` where twoDigitString = [tens, ones] zero-padded — this encodes the CORRECT behavior a spec must state, and does not exceed the problem_statement disclosure. Checks:
- No diff markers, no gold-patch line reproduced (the patch string '%02d'/str(self.data.year)[2:] etc. do not appear).
- Patched file path django/utils/dateformat.py and dotted module path do NOT appear in the spec view.
- Patched symbol: gold touches `def y` (name 'y', len 1, below the len>=4 distinctive threshold and non-localizing); spec abstracts to `twoDigitYear`. No echo of 'dateformat'/'DateFormat'/'y' as a localizing identifier or docstring.
- Comments describe behavior abstractly ('abbreviated form of a calendar year', 'fixed-width two-character decimal', leading zero for small values); no bug/fix/prepatch narration terms, no reference to the str-slice bug or the edit.

The prepatch-bug narration and the verbatim gold-hunk quote live in refinement.md/mapping.md, which are NOT part of the G-LEAK/G-PANEL-3 spec view (screen runs over Solution.lean's projected region only). Conclusion: the spec view leaks nothing about the gold edit beyond what problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
