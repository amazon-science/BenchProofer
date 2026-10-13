# P2 adversarial audit — django__django-14373

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no same-spec wrong implementation verifies. The postcondition `ensures out = fourDigitString year` is a TOTAL functional equality quantified over the entire `require year ≤ 9999` domain — the tightest possible spec. Any verifying impl must produce exactly fourDigitString year for every admissible year, which is precisely the gold behavior ('%04d' % year, verified 0 disagreements over 0..9999). Therefore verify⇒correct with no residual freedom for a wrong impl to slip through.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,19 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+    let out : List Char :=
+      if year < 10 then [digitChar (year % 10)]
+      else
+        if year < 100 then
+          [digitChar (year / 10 % 10), digitChar (year % 10)]
+        else
+          if year < 1000 then
+            [digitChar (year / 100 % 10), digitChar (year / 10 % 10),
+             digitChar (year % 10)]
+          else
+            [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
+             digitChar (year / 10 % 10), digitChar (year % 10)]
+    return out
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,9 @@
   ensures out = fourDigitString year
   do
     -- impl-start
+    -- swap tens and ones digits (boundary/transposition bug)
     return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+            digitChar (year % 10), digitChar (year / 10 % 10)]
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
+    return [digitChar (year / 10000 % 10), digitChar (year / 100 % 10),
             digitChar (year / 10 % 10), digitChar (year % 10)]
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,12 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+    let mut acc : List Char := []
+    acc := acc ++ [digitChar (year / 1000 % 10)]
+    acc := acc ++ [digitChar (year / 100 % 10)]
+    acc := acc ++ [digitChar (year / 10 % 10)]
+    -- BUG: forgets the ones digit; emits only three chars
+    return acc
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,7 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+    return fourDigitString (year + 1)
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+    return [digitChar (year % 10), digitChar (year % 10),
+            digitChar (year % 10), digitChar (year % 10)]
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
   ensures out = fourDigitString year
   do
     -- impl-start
-    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
-            digitChar (year / 10 % 10), digitChar (year % 10)]
+    return [digitChar (year / 1000 % 10), digitChar (year / 10 % 10),
+            digitChar (year / 100 % 10), digitChar (year % 10)]
     -- impl-end
 
 prove_correct fourDigitYear by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,6 +47,9 @@
   ensures out = fourDigitString year
   do
     -- impl-start
+    let mut i : Nat := 1
+    while i > 0 do
+      i := i + 1
     return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
             digitChar (year / 10 % 10), digitChar (year % 10)]
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real rendering is a straight-line pure computation
   (four digit extractions and a fixed-width write) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
--  rendering is a pure character computation modeled in full below.)
-- axioms-end

-- pure-start
/- A single decimal digit (0..9) as its ASCII character. `48` is the code point
   of '0'; clamping by `% 10` keeps the map total. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d % 10)

/- The four-character rendering of a number below ten thousand: its thousands,
   hundreds, tens and ones digits, written as exactly four characters — most
   significant first — so a value below one thousand still occupies four slots
   (filled on the left with zeros). -/
def fourDigitString (n : Nat) : List Char :=
  [digitChar (n / 1000 % 10), digitChar (n / 100 % 10),
   digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The full form of a calendar year: the year written as a fixed-width
   four-character decimal. The year is a non-negative count below ten thousand
   (the only values a calendar date carries). The output is always exactly four
   characters: when the year is below one thousand the high-order slots are
   filled on the left with zeros, so the width never collapses for small years.
   Nothing is mutated (directive 5); the year is read-only and the result is a
   fresh character sequence. -/
method fourDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = fourDigitString year
  do
    -- impl-start
    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
            digitChar (year / 10 % 10), digitChar (year % 10)]
    -- impl-end

prove_correct fourDigitYear by
  loom_solve
  simp [fourDigitString]
```

Prepatch bug re-encoded as an attack: `True`.

 Project root (venv swebench-lean). 

SAME-SPEC: all 8 attacks + positive control confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True (axioms/pure/pre/post left untouched; edited impl region only).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
- pos.lean (exact Solution impl): exit 0 (VERIFIES) — positive control good.
- atk_1 (PREPATCH bug: variable-width, drops leading zeros for year<1000): exit 1, unsolved goals @ line 65. Prepatch reproduced & correctly rejected.
- atk_2 (transposition: tens/ones swap): exit 1, unsolved goals.
- atk_3 (off-by-one divisor /10000 for top slot): exit 1, unsolved goals.
- atk_4 (control-flow-effect: mutable accumulator drops ones digit → 3-char output): exit 1, unsolved goals @ line 58.
- atk_5 (ungrounded-oracle echo: fourDigitString (year+1)): exit 1, unsolved goals @ line 53.
- atk_6 (constant per-position: ones digit ×4): exit 1, unsolved goals.
- atk_7 (hundreds/tens middle-slot swap): exit 1, unsolved goals.
- atk_8 (re-encoded prior-pass DIVERGENCE counterexample dj14373_atk_diverge.lean: infinite while-loop then correct value): exit 1 — 'Decreasing annotations are required in total correctness semantics' + sorry. Total-correctness semantics (set_option loom.semantics.termination "total") correctly rejects divergence.

Attack families covered: prepatch bug, partial-domain/boundary (atk_1,3), transposition (atk_2,7), control-flow-effect (atk_4,8), ungrounded-oracle echo (atk_5), constant-collapse (atk_6). >=5 distinct wrong impls, none verifies.

STEP 2 (materialize+resolve): N/A — no wrong impl verified, so no faithful patch to run through run_resolve. The resolve trigger never fires; verify⇏correct falsification requires a VERIFYING wrong impl, which does not exist here.

REFINEMENT.MD AUDIT: legs A1=R (Nat↔int type bijection; require year≤9999 matches real MAXYEAR=9999 — correspondence holds), A2=I (deep-modeled fixed-width zero-padded rendering fourDigitString, spelled out, no abstraction). NO axioms (mapping.md §3 confirmed: patched expr '%04d' % self.data.year calls no repo callee; no axiom_check.py). No kind-3 legs. No A-consumed/A-reference legs exist to attack. I-leg correspondence independently verified: fourDigitString(n) == '%04d'%n for all n in 0..9999 (0 disagreements); conformance_check.py exits 0 (210011 cases, seed 14373).

I-leg soundness note: spec is a total functional equality over full domain, so it is maximally tight — cannot be satisfied by anything but the gold behavior. prepatch str(year) coincides with '%04d'%year only for year>=1000 (9000 years), differing exactly on year<1000 including F2P years 1→'0001', 999→'0999' — the discriminating clause the prepatch fails and the gold fixes.

VERDICT: SOUND. >=5 distinct attacks + prepatch + divergence counterexample all verified; none breaks the spec; positive control verifies; refinement legs (R/I only, no axioms) hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no same-spec wrong implementation verifies. The postcondition `ensures out = fourDigitString year` is a TOTAL functional equality quantified over the entire `require year ≤ 9999` domain — the tightest possible spec. Any verifying impl must produce exactly fourDigitString year for every admissible year, which is precisely the gold behavior ('%04d' % year, verified 0 disagreements over 0..9999). Therefore verify⇒correct with no residual freedom for a wrong impl to slip through.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real rendering is a straight-line pure computation
   (four digit extractions and a fixed-width write) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
--  rendering is a pure character computation modeled in full below.)
-- axioms-end

-- pure-start
/- A single decimal digit (0..9) as its ASCII character. `48` is the code point
   of '0'; clamping by `% 10` keeps the map total. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d % 10)

/- The four-character rendering of a number below ten thousand: its thousands,
   hundreds, tens and ones digits, written as exactly four characters — most
   significant first — so a value below one thousand still occupies four slots
   (filled on the left with zeros). -/
def fourDigitString (n : Nat) : List Char :=
  [digitChar (n / 1000 % 10), digitChar (n / 100 % 10),
   digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The full form of a calendar year: the year written as a fixed-width
   four-character decimal. The year is a non-negative count below ten thousand
   (the only values a calendar date carries). The output is always exactly four
   characters: when the year is below one thousand the high-order slots are
   filled on the left with zeros, so the width never collapses for small years.
   Nothing is mutated (directive 5); the year is read-only and the result is a
   fresh character sequence. -/
method fourDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = fourDigitString year
  do
    -- impl-start
    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
            digitChar (year / 10 % 10), digitChar (year % 10)]
    -- impl-end

prove_correct fourDigitYear by
  loom_solve
  simp [fourDigitString]
```

Prepatch bug re-encoded as an attack: `True`.

 Project root (venv swebench-lean). 

SAME-SPEC: all 8 attacks + positive control confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True (axioms/pure/pre/post left untouched; edited impl region only).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
- pos.lean (exact Solution impl): exit 0 (VERIFIES) — positive control good.
- atk_1 (PREPATCH bug: variable-width, drops leading zeros for year<1000): exit 1, unsolved goals @ line 65. Prepatch reproduced & correctly rejected.
- atk_2 (transposition: tens/ones swap): exit 1, unsolved goals.
- atk_3 (off-by-one divisor /10000 for top slot): exit 1, unsolved goals.
- atk_4 (control-flow-effect: mutable accumulator drops ones digit → 3-char output): exit 1, unsolved goals @ line 58.
- atk_5 (ungrounded-oracle echo: fourDigitString (year+1)): exit 1, unsolved goals @ line 53.
- atk_6 (constant per-position: ones digit ×4): exit 1, unsolved goals.
- atk_7 (hundreds/tens middle-slot swap): exit 1, unsolved goals.
- atk_8 (re-encoded prior-pass DIVERGENCE counterexample dj14373_atk_diverge.lean: infinite while-loop then correct value): exit 1 — 'Decreasing annotations are required in total correctness semantics' + sorry. Total-correctness semantics (set_option loom.semantics.termination "total") correctly rejects divergence.

Attack families covered: prepatch bug, partial-domain/boundary (atk_1,3), transposition (atk_2,7), control-flow-effect (atk_4,8), ungrounded-oracle echo (atk_5), constant-collapse (atk_6). >=5 distinct wrong impls, none verifies.

STEP 2 (materialize+resolve): N/A — no wrong impl verified, so no faithful patch to run through run_resolve. The resolve trigger never fires; verify⇏correct falsification requires a VERIFYING wrong impl, which does not exist here.

REFINEMENT.MD AUDIT: legs A1=R (Nat↔int type bijection; require year≤9999 matches real MAXYEAR=9999 — correspondence holds), A2=I (deep-modeled fixed-width zero-padded rendering fourDigitString, spelled out, no abstraction). NO axioms (mapping.md §3 confirmed: patched expr '%04d' % self.data.year calls no repo callee; no axiom_check.py). No kind-3 legs. No A-consumed/A-reference legs exist to attack. I-leg correspondence independently verified: fourDigitString(n) == '%04d'%n for all n in 0..9999 (0 disagreements); conformance_check.py exits 0 (210011 cases, seed 14373).

I-leg soundness note: spec is a total functional equality over full domain, so it is maximally tight — cannot be satisfied by anything but the gold behavior. prepatch str(year) coincides with '%04d'%year only for year>=1000 (9000 years), differing exactly on year<1000 including F2P years 1→'0001', 999→'0999' — the discriminating clause the prepatch fails and the gold fixes.

VERDICT: SOUND. >=5 distinct attacks + prepatch + divergence counterexample all verified; none breaks the spec; positive control verifies; refinement legs (R/I only, no axioms) hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independent verification performed (not trusting conformance_check.py or recorded verdicts):

1) SPEC BYTE-IDENTITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) = True. spec_view confirms only the impl region and prove_correct body are elided; the axioms/pure/pre/post regions and method signature (require year ≤ 9999; ensures out = fourDigitString year) are identical between gold and prepatch.

2) REAL CALLEE at base_commit: repo worktree shows prepatch DateFormat.Y = `return self.data.year`; gold patch (patch.diff / mapping.md) = `return '%04d' % self.data.year`. Matches the modeled function's target expression. No repo callee beyond integer / , % and %-string formatting — modeled deeply, NO axioms.

3) EXHAUSTIVE FAITHFULNESS: recomputed Python digitChar/fourDigitString vs oracle '%04d' % y for every y in 0..9999 → ZERO disagreements. The spec's `require year ≤ 9999` exactly matches the real upper bound MAXYEAR=9999, so the modeled domain (0..9999) is a superset of the reachable domain (1..9999) and agrees on every reachable input. Spec is NOT too strong and does NOT drift.

4) NON-VACUITY: Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0). The prepatch skeleton (variable-width, no zero-pad: 1/2/3 chars for year<1000) does NOT satisfy `out = fourDigitString year` and fails on every year<1000 — so the postcondition genuinely discriminates the zero-pad fix and pins the F2P test_Y_format_year_before_1000 (1→'0001', 999→'0999'). The spec is not vacuously satisfiable.

Conclusion: the modeled function agrees with the real repo callee on every input in the require domain (which coincides with the reachable domain). No faithfulness break. Verdict: FAITHFUL.

Counterexample / evidence:

```
N/A — no counterexample exists in the modeled domain. Exhaustive check over all y in 0..9999: fourDigitString(y) == '%04d' % y, 0 disagreements (including boundary years 1→'0001' and 999→'0999').
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (>=8 char normalized), no patched file path/module, no spec-view identifier embedding a patched symbol, no bug/fix/prepatch narration. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). Substantive check: the public problem_statement already discloses the ENTIRE fix — 'The Y specifier ... is supposed to always return a four-digit year padded with zeros. This doesn't seem to be the case for year < 1000.' Every semantic element in the spec view (fixed-width four characters, leading-zero fill, the discriminating year<1000 case) is thus already public. The spec view is a faithful model of the publicly-stated behavior and reveals nothing about the gold implementation beyond the problem statement: the gold's concrete edit ('%04d' % self.data.year, file django/utils/dateformat.py, method Y) appears ONLY in the auditor-facing refinement.md/mapping.md, never in the solver-visible spec view. Patched repo symbol 'Y' is len<4 after underscore-strip and is not distinctive; spec identifiers (fourDigitYear, fourDigitString, digitChar) echo no patched symbol. The 'year <= 9999' bound is the generic MAXYEAR domain fact, not an edit disclosure. Not a relaxed bundle; no RELAXED_LEAKAGE deferral needed. Clean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
