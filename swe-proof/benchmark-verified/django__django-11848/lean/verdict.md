# P2 adversarial audit — django__django-11848

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
No same-spec wrong impl verified, so there is no verify⇏correct counterexample. All 7 same-spec wrong impls FAIL lean_verify (exit 1) and each has a genuine in-domain (year>=0) counterexample against the uniquely-pinned spec result: atk_1 prepatch pivot-70 -> year=0,CY=1: impl 2000 vs spec 0; atk_2 never-rollback -> year=52,CY=1: 52 vs -48; atk_3 >=50 off-by-one -> year=51,CY=1: -49 vs 51; atk_4 branch-swap -> year=0,CY=1: -100 vs 0; atk_5 dropped year<100 guard -> year=100,CY=1: 0 vs 100; atk_6 -50 wrong const -> year=52,CY=1: 2 vs -48; atk_7 +100 wrong direction -> year=0,CY=1: 100 vs 0.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,11 +50,10 @@
 def implementation_expandYear (year currentYear : Int) : Int := Id.run do
   let mut y := year
   if year < 100 then
-    let currentCentury := currentYear - currentYear % 100
-    if year - currentYear % 100 > 50 then
-      y := y + currentCentury - 100
+    if year < 70 then
+      y := y + 2000
     else
-      y := y + currentCentury
+      y := y + 1900
   return y
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,10 +51,7 @@
   let mut y := year
   if year < 100 then
     let currentCentury := currentYear - currentYear % 100
-    if year - currentYear % 100 > 50 then
-      y := y + currentCentury - 100
-    else
-      y := y + currentCentury
+    y := y + currentCentury
   return y
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
   let mut y := year
   if year < 100 then
     let currentCentury := currentYear - currentYear % 100
-    if year - currentYear % 100 > 50 then
+    if year - currentYear % 100 >= 50 then
       y := y + currentCentury - 100
     else
       y := y + currentCentury
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,9 +52,9 @@
   if year < 100 then
     let currentCentury := currentYear - currentYear % 100
     if year - currentYear % 100 > 50 then
+      y := y + currentCentury
+    else
       y := y + currentCentury - 100
-    else
-      y := y + currentCentury
   return y
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,13 +48,12 @@
 
 -- impl-start
 def implementation_expandYear (year currentYear : Int) : Int := Id.run do
+  let currentCentury := currentYear - currentYear % 100
   let mut y := year
-  if year < 100 then
-    let currentCentury := currentYear - currentYear % 100
-    if year - currentYear % 100 > 50 then
-      y := y + currentCentury - 100
-    else
-      y := y + currentCentury
+  if year - currentYear % 100 > 50 then
+    y := y + currentCentury - 100
+  else
+    y := y + currentCentury
   return y
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,7 @@
   if year < 100 then
     let currentCentury := currentYear - currentYear % 100
     if year - currentYear % 100 > 50 then
-      y := y + currentCentury - 100
+      y := y + currentCentury - 50
     else
       y := y + currentCentury
   return y
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
     if year - currentYear % 100 > 50 then
       y := y + currentCentury - 100
     else
-      y := y + currentCentury
+      y := y + currentCentury + 100
   return y
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee participates in the modeled behavior. The current year,
-- which serves as the reference point for interpreting a two-digit year, is
-- supplied to the computation as an explicit input. The whole computation is
-- integer arithmetic, modeled deeply below. Hence there is no `opaque`
-- declaration and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
-- (No standalone pure helpers are needed; the behavior is pinned directly by the
-- post-condition predicate and realized by the impl skeleton.)
-- pure-end

-- post-conditions-start
/-- Specification of how a parsed two-digit calendar year is expanded to a full
year, interpreted relative to the current year.

Inputs: `year` is the parsed year field (a two-digit year is in `0 … 99`; a
value `≥ 100` is already a full year and is taken verbatim), and `currentYear`
is the full current year used as the reference point. `result` is the expanded
full year.

Let `cc` be the century of the current year (its hundreds component). For a
two-digit `year`:

* the expanded year keeps the same last two digits as `year`;
* it is never read as lying more than 50 years in the future of the reference
  year (`result ≤ currentYear + 50`);
* by default the two-digit year is placed in the current century
  (`result = year + cc`); only when that placement would fall more than 50 years
  ahead of the reference year is it rolled back one century
  (`result = year + cc - 100`), interpreting it as the most recent past year with
  those last two digits.

A value already `≥ 100` is returned unchanged. -/
def problem_spec_expandYear (year currentYear result : Int) : Prop :=
  let cc := currentYear - currentYear % 100
  (year ≥ 100 → result = year) ∧
  (year < 100 →
      result % 100 = year ∧
      result ≤ currentYear + 50 ∧
      (year + cc ≤ currentYear + 50 → result = year + cc) ∧
      (currentYear + 50 < year + cc → result = year + cc - 100))
-- post-conditions-end

-- impl-start
def implementation_expandYear (year currentYear : Int) : Int := Id.run do
  let mut y := year
  if year < 100 then
    let currentCentury := currentYear - currentYear % 100
    if year - currentYear % 100 > 50 then
      y := y + currentCentury - 100
    else
      y := y + currentCentury
  return y
-- impl-end

-- proof-start
theorem correct_expandYear : ∀ (year currentYear : Int), 0 ≤ year →
    problem_spec_expandYear year currentYear (implementation_expandYear year currentYear) := by
  intro year currentYear hy
  unfold problem_spec_expandYear implementation_expandYear
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · split <;> rename_i h2 <;>
      refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
  · refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier = `bash scripts/lean_verify.sh <file>` run. same_spec confirmed True for all 8 files via swebench_unified.markers.same_spec + get_backend('lean').language (spec_view collapses impl+proof, so editing impl+proof preserves the signature).

### RESULTS (concurrent, <=4 background jobs per batch):
- positive_control pos_gold.lean (gold impl+proof, unchanged): exit 0. Axiom check: appended `#print axioms correct_expandYear` in pos_axcheck.lean -> exit 0, `depends on axioms: [propext, Quot.sound]` (CLEAN — no sorryAx, no native/Classical.choice-of-concern, no sorry).
- atk_1 (prepatch bug: hard-coded pivot year<70 -> +2000 else +1900, = Solution_prepatch.lean impl): exit 1. PREPATCH REPRODUCED.
- atk_2 (partial-domain: only current century, never roll back): exit 1.
- atk_3 (boundary off-by-one: `>= 50` instead of `> 50`): exit 1.
- atk_4 (control-flow-effect: rollback/default branches swapped): exit 1.
- atk_5 (ungrounded: `year<100` guard removed, expands full years too): exit 1.
- atk_6 (wrong rollback constant `- 50` instead of `- 100`): exit 1.
- atk_7 (wrong direction `+ 100` in default branch): exit 1.
Each attack used the gold proof skeleton (best-effort closing tactic: unfold/simp/split/omega); omega is complete for the linear-int obligation, so exit 1 = genuinely unprovable, not tactic fragility. Independently confirmed by exhaustive Python search over year in 0..4000, CY in 1..4000 (counterexamples above).

STEP 2 (materialize+resolve): NOT TRIGGERED — no wrong impl produced a closing clean-axiom proof, so no faithful patch required a run_resolve. patches={}.

REFINEMENT.MD AUDIT: 6 legs. Leg1 (year:Int input) R; Leg2 (currentYear:Int input) R; Legs3-6 (year<100 guard, current_century arithmetic, `>50` rollback branch, default-century else) all I (byte-identical to patch.diff). No A-consumed / A-reference legs (axioms region empty -> G-AX=skip, correct). No kind-3 (unjustified) legs. The datetime.utcnow().year callee is faithfully modeled as the explicit input currentYear, justified because the F2P regression test mocks utcnow, making the block a pure function of (year, currentYear); mapping.md documents the Int<->int bijection on the year>=0 domain where Lean Int.emod == Python %. A-leg correspondence holds (there are none to break; the callee-as-input modeling is sound).

SPEC TIGHTNESS: for year<100 the post-condition's two implications form an exhaustive, mutually-exclusive dichotomy (`year+cc <= CY+50` XOR `CY+50 < year+cc`) that uniquely pins result; for year>=100, result=year is pinned. gold's branch guard `year - currentYear%100 > 50` is exactly equivalent to `CY+50 < year+cc`. Theorem domain `0 <= year` is a SUPERSET of the real parsed-year domain (regex \d+ => year>=0), so any impl differing from gold anywhere on year>=0 is unprovable. verify==correct holds on this bundle.

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
No same-spec wrong impl verified, so there is no verify⇏correct counterexample. All 7 same-spec wrong impls FAIL lean_verify (exit 1) and each has a genuine in-domain (year>=0) counterexample against the uniquely-pinned spec result: atk_1 prepatch pivot-70 -> year=0,CY=1: impl 2000 vs spec 0; atk_2 never-rollback -> year=52,CY=1: 52 vs -48; atk_3 >=50 off-by-one -> year=51,CY=1: -49 vs 51; atk_4 branch-swap -> year=0,CY=1: -100 vs 0; atk_5 dropped year<100 guard -> year=100,CY=1: 0 vs 100; atk_6 -50 wrong const -> year=52,CY=1: 2 vs -48; atk_7 +100 wrong direction -> year=0,CY=1: 100 vs 0.
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
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee participates in the modeled behavior. The current year,
-- which serves as the reference point for interpreting a two-digit year, is
-- supplied to the computation as an explicit input. The whole computation is
-- integer arithmetic, modeled deeply below. Hence there is no `opaque`
-- declaration and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
-- (No standalone pure helpers are needed; the behavior is pinned directly by the
-- post-condition predicate and realized by the impl skeleton.)
-- pure-end

-- post-conditions-start
/-- Specification of how a parsed two-digit calendar year is expanded to a full
year, interpreted relative to the current year.

Inputs: `year` is the parsed year field (a two-digit year is in `0 … 99`; a
value `≥ 100` is already a full year and is taken verbatim), and `currentYear`
is the full current year used as the reference point. `result` is the expanded
full year.

Let `cc` be the century of the current year (its hundreds component). For a
two-digit `year`:

* the expanded year keeps the same last two digits as `year`;
* it is never read as lying more than 50 years in the future of the reference
  year (`result ≤ currentYear + 50`);
* by default the two-digit year is placed in the current century
  (`result = year + cc`); only when that placement would fall more than 50 years
  ahead of the reference year is it rolled back one century
  (`result = year + cc - 100`), interpreting it as the most recent past year with
  those last two digits.

A value already `≥ 100` is returned unchanged. -/
def problem_spec_expandYear (year currentYear result : Int) : Prop :=
  let cc := currentYear - currentYear % 100
  (year ≥ 100 → result = year) ∧
  (year < 100 →
      result % 100 = year ∧
      result ≤ currentYear + 50 ∧
      (year + cc ≤ currentYear + 50 → result = year + cc) ∧
      (currentYear + 50 < year + cc → result = year + cc - 100))
-- post-conditions-end

-- impl-start
def implementation_expandYear (year currentYear : Int) : Int := Id.run do
  let mut y := year
  if year < 100 then
    let currentCentury := currentYear - currentYear % 100
    if year - currentYear % 100 > 50 then
      y := y + currentCentury - 100
    else
      y := y + currentCentury
  return y
-- impl-end

-- proof-start
theorem correct_expandYear : ∀ (year currentYear : Int), 0 ≤ year →
    problem_spec_expandYear year currentYear (implementation_expandYear year currentYear) := by
  intro year currentYear hy
  unfold problem_spec_expandYear implementation_expandYear
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · split <;> rename_i h2 <;>
      refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
  · refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier = `bash scripts/lean_verify.sh <file>` run. same_spec confirmed True for all 8 files via swebench_unified.markers.same_spec + get_backend('lean').language (spec_view collapses impl+proof, so editing impl+proof preserves the signature).

### RESULTS (concurrent, <=4 background jobs per batch):
- positive_control pos_gold.lean (gold impl+proof, unchanged): exit 0. Axiom check: appended `#print axioms correct_expandYear` in pos_axcheck.lean -> exit 0, `depends on axioms: [propext, Quot.sound]` (CLEAN — no sorryAx, no native/Classical.choice-of-concern, no sorry).
- atk_1 (prepatch bug: hard-coded pivot year<70 -> +2000 else +1900, = Solution_prepatch.lean impl): exit 1. PREPATCH REPRODUCED.
- atk_2 (partial-domain: only current century, never roll back): exit 1.
- atk_3 (boundary off-by-one: `>= 50` instead of `> 50`): exit 1.
- atk_4 (control-flow-effect: rollback/default branches swapped): exit 1.
- atk_5 (ungrounded: `year<100` guard removed, expands full years too): exit 1.
- atk_6 (wrong rollback constant `- 50` instead of `- 100`): exit 1.
- atk_7 (wrong direction `+ 100` in default branch): exit 1.
Each attack used the gold proof skeleton (best-effort closing tactic: unfold/simp/split/omega); omega is complete for the linear-int obligation, so exit 1 = genuinely unprovable, not tactic fragility. Independently confirmed by exhaustive Python search over year in 0..4000, CY in 1..4000 (counterexamples above).

STEP 2 (materialize+resolve): NOT TRIGGERED — no wrong impl produced a closing clean-axiom proof, so no faithful patch required a run_resolve. patches={}.

REFINEMENT.MD AUDIT: 6 legs. Leg1 (year:Int input) R; Leg2 (currentYear:Int input) R; Legs3-6 (year<100 guard, current_century arithmetic, `>50` rollback branch, default-century else) all I (byte-identical to patch.diff). No A-consumed / A-reference legs (axioms region empty -> G-AX=skip, correct). No kind-3 (unjustified) legs. The datetime.utcnow().year callee is faithfully modeled as the explicit input currentYear, justified because the F2P regression test mocks utcnow, making the block a pure function of (year, currentYear); mapping.md documents the Int<->int bijection on the year>=0 domain where Lean Int.emod == Python %. A-leg correspondence holds (there are none to break; the callee-as-input modeling is sound).

SPEC TIGHTNESS: for year<100 the post-condition's two implications form an exhaustive, mutually-exclusive dichotomy (`year+cc <= CY+50` XOR `CY+50 < year+cc`) that uniquely pins result; for year>=100, result=year is pinned. gold's branch guard `year - currentYear%100 > 50` is exactly equivalent to `CY+50 < year+cc`. Theorem domain `0 <= year` is a SUPERSET of the real parsed-year domain (regex \d+ => year>=0), so any impl differing from gold anywhere on year>=0 is unprovable. verify==correct holds on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the two-digit-year expansion block of parse_http_date (django/utils/http.py:125-133 at base 859a87d873; patch replaces hard pivot-70 with current-year-relative expansion).

### Checks performed
1. Solution.lean elaborates (lean_verify.sh exit 0). `#print axioms correct_expandYear` => [propext, Quot.sound] only; NO sorryAx — proof is real, not fake.
2. Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean backend) = True.
3. Real callee behavior: post-patch block uses branch cond `year - (current_year % 100) > 50`; spec uses `currentYear + 50 < year + cc` with `cc = currentYear - currentYear%100`. These are algebraically identical.
4. Direct faithfulness brute force: evaluated the SPEC predicate problem_spec_expandYear(year, currentYear, result) with `result` = output of the REAL Python block, over currentYear in [-500,4000] u {100000}, year in [0,99] plus full-year samples {100,101,150,1994,2069,2100,3999}, and all boundary cases (49/50/51/70/71 at century starts/mid-century). ZERO violations. Each of the four spec conjuncts (result%100=year, result<=currentYear+50, default-century placement, rollback -100) matches real output exactly.
5. G-CONF conformance_check.py (120020 fuzzed inputs, pinned seed 11848): 0 disagreements.

MODELING BOUNDARY: currentYear correctly modeled as explicit input (real code reads datetime.now(utc).year; F2P test mocks it, confirming pure function of (year,currentYear)). Empty axioms region justified — no unchanged callee participates.

CONCLUSION: No input exists where the modeled function disagrees with the real callee on the parsed-year domain (year>=0). The spec is neither too strong nor drifted; it captures exactly the post-patch behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified: same_spec(Solution, Solution_prepatch, lean)=True (spec region byte-identical); leakage.screen passes with zero hard_failures; spec_view elides impl+proof regions. Semantic check: the spec-view discriminators are all faithful formalizations of content ALREADY public in problem_statement, not beyond it. The problem_statement discloses (a) the bug ('hard coded ... instead of comparing versus the current year') and (b) the RFC 7231 rule verbatim: 'interpret a timestamp that appears to be more than 50 years in the future as representing the most recent year in the past that had the same last two digits.' The post-condition problem_spec_expandYear encodes exactly this: result%100=year (RFC 'same last two digits'), result<=currentYear+50 (RFC 'more than 50 years in the future'), default current-century placement with one-century rollback otherwise (RFC 'most recent year in the past'), referenced to currentYear (statement's 'current year'). The specific gold arithmetic (year-(current_year%100)>50; current_century-100; current_century) appears only in the elided impl region, not the spec view. No spec-view line reveals the gold edit beyond the public problem_statement (hints_text not considered). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
