# P2 adversarial audit — django__django-13670

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_twoDigitYear year result := (result = twoDigitYear year) is a TOTAL pointwise functional equality over all of Nat, so any impl whose correct_ proof closes must be extensionally equal to the gold deep model twoDigitYear on every input. The only wrong-shaped same-spec impl that closed a clean-axiom proof (atk_4, the ungrounded-oracle echo `return twoDigitYear year`) is behaviorally identical to the gold, and its faithful patch (byte-identical to the gold patch) RESOLVES under the official harness. No verify-but-incorrect impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,6 +43,8 @@
 
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
+  if year == 0 then
+    return []
   let r := year % 100
   let tens := r / 10
   let ones := r % 10
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,6 +44,8 @@
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
   let r := year % 100
+  if r == 99 then
+    return [digitChar 9, digitChar 8]
   let tens := r / 10
   let ones := r % 10
   return [digitChar tens, digitChar ones]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,10 @@
 
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
+  let mut acc : List Char := []
   let r := year % 100
-  let tens := r / 10
-  let ones := r % 10
-  return [digitChar tens, digitChar ones]
+  acc := acc ++ [digitChar (r % 10)]
+  return acc
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -43,16 +43,13 @@
 
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
-  let r := year % 100
-  let tens := r / 10
-  let ones := r % 10
-  return [digitChar tens, digitChar ones]
+  return twoDigitYear year
 -- impl-end
 
 -- proof-start
 theorem correct_twoDigitYear : ∀ year : Nat,
     problem_spec_twoDigitYear year (implementation_twoDigitYear year) := by
   intro year
-  unfold problem_spec_twoDigitYear implementation_twoDigitYear twoDigitYear
+  unfold problem_spec_twoDigitYear implementation_twoDigitYear
   rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   let r := year % 100
   let tens := r / 10
   let ones := r % 10
-  return [digitChar tens, digitChar ones]
+  return [digitChar ones, digitChar tens]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,9 +43,8 @@
 
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
-  let r := year % 100
-  let tens := r / 10
-  let ones := r % 10
+  let tens := year / 10
+  let ones := year % 10
   return [digitChar tens, digitChar ones]
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
 
 -- impl-start
 def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
-  let r := year % 100
+  let r := (year + 100) % 101
   let tens := r / 10
   let ones := r % 10
   return [digitChar tens, digitChar ones]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The two-digit representation of a calendar year.

The abstract behaviour: given a year (a non-negative whole number), produce the
two-digit short form of that year — that is, the value of the year reduced
modulo one hundred, rendered as exactly two decimal digits with a leading zero
when the reduced value is below ten. So a year of 476 yields `76`, a year of 42
yields `42`, a year of 4 yields `04`, and a year of 1999 yields `99`. The output
is always exactly two characters, each an ASCII decimal digit.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The two-digit short form is a pure
-- arithmetic function of the year (reduction modulo one hundred, then rendering
-- the tens and units digits); it is modeled DEEPLY below, so no `opaque`/`axiom`
-- callee contract is required. The proof agent may add `_prop` axioms only if
-- genuinely stuck.
-- axioms-end

-- pure-start
/-- Render a single decimal digit (`0`–`9`) as its ASCII character. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d)

/-- The two-digit short form of a year: reduce modulo one hundred, then emit the
tens digit followed by the units digit. The tens digit is `0` when the reduced
value is below ten, giving the leading-zero behaviour. The result is always
exactly two ASCII decimal digits. -/
def twoDigitYear (year : Nat) : List Char :=
  let r := year % 100
  [digitChar (r / 10), digitChar (r % 10)]
-- pure-end

-- post-conditions-start
/-- The result is exactly the two-digit short form of the year: the two ASCII
decimal digits of the year taken modulo one hundred, with a leading zero when
the reduced value is below ten. -/
def problem_spec_twoDigitYear (year : Nat) (result : List Char) : Prop :=
  result = twoDigitYear year
-- post-conditions-end

-- impl-start
def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
  let r := year % 100
  let tens := r / 10
  let ones := r % 10
  return [digitChar tens, digitChar ones]
-- impl-end

-- proof-start
theorem correct_twoDigitYear : ∀ year : Nat,
    problem_spec_twoDigitYear year (implementation_twoDigitYear year) := by
  intro year
  unfold problem_spec_twoDigitYear implementation_twoDigitYear twoDigitYear
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Used scripts/lean_verify.sh there, swebench_unified.markers.same_spec via python, and swebench_unified.harness.run_resolve for the resolve run.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited).

### VERIFICATION (bash scripts/lean_verify.sh <f>; exit 0=verifies):
- pos_control (gold impl): EXIT 0; #print axioms => 'does not depend on any axioms'.
- atk_1 (partial-domain: year==0 -> []): EXIT 1 (rejected).
- atk_2 (boundary: r==99 -> '98'): EXIT 1 (rejected).
- atk_3 (control-flow-effect: mutable acc, drops tens digit, one char): EXIT 1 (rejected).
- atk_4 (ungrounded-oracle echo: return twoDigitYear year): EXIT 0; #print axioms => 'does not depend on any axioms'.
- atk_5 (digit swap [ones,tens]): EXIT 1 (rejected).
- atk_6 (no mod-100, uses year directly): EXIT 1 (rejected).
- atk_7 (off-by-one modulus (year+100)%101): EXIT 1 (rejected).
Ran concurrently in two background batches of 4 (<=4 at a time) per protocol.

PREPATCH BUG: atk_prepatch.lean (impl = (toString year).toList |>.drop 2, the buggy str(year)[2:]) fails to close: EXIT 1 with goal (pure (List.drop 2 s)).run = [digitChar (r/10), digitChar (r%10)] — rfl mismatch. Bug reproduced; the frozen spec pins the correct leading-zero/modulo behavior.

RESOLVE (protocol step 2 — MANDATORY for every clean-axiom-closing wrong impl): only atk_4 closes among wrong-shaped impls. Its faithful patch is byte-identical to the gold patch. Executed run_resolve('django__django-13670', atk_4.patch, timeout=1200) => RESOLVED=True, completed=True, note='resolved'. So the sole verifying same-spec impl's faithful patch RESOLVES => no verify-but-not-resolve break.

REFINEMENT.MD AUDIT: axioms region empty (no A-consumed, no A-reference); all 5 impl legs tagged I or I/R (rows 1-5): input Nat<->int (R), year%100 (I), tens r/10 (I), ones r%10 (I), digit rendering + str<->List Char (I/R). No kind-3 (changed-inexpressible) op. The changed op ('%02d' % (year % 100)) underlies NO external UNCHANGED callee — % and %02d are language primitives, modeled DEEPLY as digitChar/twoDigitYear, so no A-reference correspondence to a real callee is needed (correctly absent). Correspondence is faithful.

VERDICT: SOUND. Spec is a total functional equality that admits exactly the gold behavior up to extensional equality; 6 distinct genuinely-wrong impls (partial-domain, boundary, control-flow-effect, digit-swap, no-mod, off-by-one) are all rejected, and the single verifying echo resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_twoDigitYear year result := (result = twoDigitYear year) is a TOTAL pointwise functional equality over all of Nat, so any impl whose correct_ proof closes must be extensionally equal to the gold deep model twoDigitYear on every input. The only wrong-shaped same-spec impl that closed a clean-axiom proof (atk_4, the ungrounded-oracle echo `return twoDigitYear year`) is behaviorally identical to the gold, and its faithful patch (byte-identical to the gold patch) RESOLVES under the official harness. No verify-but-incorrect impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The two-digit representation of a calendar year.

The abstract behaviour: given a year (a non-negative whole number), produce the
two-digit short form of that year — that is, the value of the year reduced
modulo one hundred, rendered as exactly two decimal digits with a leading zero
when the reduced value is below ten. So a year of 476 yields `76`, a year of 42
yields `42`, a year of 4 yields `04`, and a year of 1999 yields `99`. The output
is always exactly two characters, each an ASCII decimal digit.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The two-digit short form is a pure
-- arithmetic function of the year (reduction modulo one hundred, then rendering
-- the tens and units digits); it is modeled DEEPLY below, so no `opaque`/`axiom`
-- callee contract is required. The proof agent may add `_prop` axioms only if
-- genuinely stuck.
-- axioms-end

-- pure-start
/-- Render a single decimal digit (`0`–`9`) as its ASCII character. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d)

/-- The two-digit short form of a year: reduce modulo one hundred, then emit the
tens digit followed by the units digit. The tens digit is `0` when the reduced
value is below ten, giving the leading-zero behaviour. The result is always
exactly two ASCII decimal digits. -/
def twoDigitYear (year : Nat) : List Char :=
  let r := year % 100
  [digitChar (r / 10), digitChar (r % 10)]
-- pure-end

-- post-conditions-start
/-- The result is exactly the two-digit short form of the year: the two ASCII
decimal digits of the year taken modulo one hundred, with a leading zero when
the reduced value is below ten. -/
def problem_spec_twoDigitYear (year : Nat) (result : List Char) : Prop :=
  result = twoDigitYear year
-- post-conditions-end

-- impl-start
def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
  let r := year % 100
  let tens := r / 10
  let ones := r % 10
  return [digitChar tens, digitChar ones]
-- impl-end

-- proof-start
theorem correct_twoDigitYear : ∀ year : Nat,
    problem_spec_twoDigitYear year (implementation_twoDigitYear year) := by
  intro year
  unfold problem_spec_twoDigitYear implementation_twoDigitYear twoDigitYear
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Used scripts/lean_verify.sh there, swebench_unified.markers.same_spec via python, and swebench_unified.harness.run_resolve for the resolve run.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited).

### VERIFICATION (bash scripts/lean_verify.sh <f>; exit 0=verifies):
- pos_control (gold impl): EXIT 0; #print axioms => 'does not depend on any axioms'.
- atk_1 (partial-domain: year==0 -> []): EXIT 1 (rejected).
- atk_2 (boundary: r==99 -> '98'): EXIT 1 (rejected).
- atk_3 (control-flow-effect: mutable acc, drops tens digit, one char): EXIT 1 (rejected).
- atk_4 (ungrounded-oracle echo: return twoDigitYear year): EXIT 0; #print axioms => 'does not depend on any axioms'.
- atk_5 (digit swap [ones,tens]): EXIT 1 (rejected).
- atk_6 (no mod-100, uses year directly): EXIT 1 (rejected).
- atk_7 (off-by-one modulus (year+100)%101): EXIT 1 (rejected).
Ran concurrently in two background batches of 4 (<=4 at a time) per protocol.

PREPATCH BUG: atk_prepatch.lean (impl = (toString year).toList |>.drop 2, the buggy str(year)[2:]) fails to close: EXIT 1 with goal (pure (List.drop 2 s)).run = [digitChar (r/10), digitChar (r%10)] — rfl mismatch. Bug reproduced; the frozen spec pins the correct leading-zero/modulo behavior.

RESOLVE (protocol step 2 — MANDATORY for every clean-axiom-closing wrong impl): only atk_4 closes among wrong-shaped impls. Its faithful patch is byte-identical to the gold patch. Executed run_resolve('django__django-13670', atk_4.patch, timeout=1200) => RESOLVED=True, completed=True, note='resolved'. So the sole verifying same-spec impl's faithful patch RESOLVES => no verify-but-not-resolve break.

REFINEMENT.MD AUDIT: axioms region empty (no A-consumed, no A-reference); all 5 impl legs tagged I or I/R (rows 1-5): input Nat<->int (R), year%100 (I), tens r/10 (I), ones r%10 (I), digit rendering + str<->List Char (I/R). No kind-3 (changed-inexpressible) op. The changed op ('%02d' % (year % 100)) underlies NO external UNCHANGED callee — % and %02d are language primitives, modeled DEEPLY as digitChar/twoDigitYear, so no A-reference correspondence to a real callee is needed (correctly absent). Correspondence is faithful.

VERDICT: SOUND. Spec is a total functional equality that admits exactly the gold behavior up to extensional equality; 6 distinct genuinely-wrong impls (partial-domain, boundary, control-flow-effect, digit-swap, no-mod, off-by-one) are all rejected, and the single verifying echo resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Deep model twoDigitYear(year) = [digitChar((year%100)/10), digitChar((year%100)%10)] (digitChar d = Char.ofNat(48+d)) modeled against real post-patch callee DateFormat.y = '%02d' % (self.data.year % 100) at dateformat.py:305-307. Faithfulness checks: (1) same_spec(Solution, Solution_prepatch, LeanBackend.language) = True — spec region (docstring+digitChar+twoDigitYear+problem_spec) byte-identical between canonical and prepatch, so no spec drift smuggled via the impl. (2) Solution.lean lean_verify exit 0; #print axioms correct_twoDigitYear -> 'does not depend on any axioms' (no sorryAx, genuine proof). (3) Differential test model vs '%02d'%(year%100) over 0..99999 plus boundaries: 0 mismatches. Key over-strength risk examined: '%02d' pads to a MINIMUM of 2 digits, so a general '%02d' % n could exceed 2 chars for n>=100; but the argument is always year%100 in [0,99], so it emits EXACTLY 2 chars, matching the model's fixed 2-element list — no divergence. Domain: real year is int in 1..9999; model carrier Nat (>=0) is a faithful superset, no negative-year concern (precondition vacuous over Nat). No input found where the modeled function disagrees with the real callee, and the spec is not too strong within the real domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projection via markers.spec_view) is clean. Mechanical leakage.screen passes with zero hard failures. same_spec(prepatch, postpatch)=True — the discriminating behavior lives entirely in the elided impl/proof regions, not the frozen spec.

Semantic check vs. public problem_statement ONLY (not hints_text; hints_text is empty here anyway): the problem_statement already fully and publicly discloses the intended correct behavior — that dateformat.y() must match Python %y / PHP date('y'), i.e. the last two digits of the year with leading zeros, explicitly calling out the years < 1000 / <100 / <10 cases and showing 123 -> '23'. The spec-view docstrings ('year reduced modulo one hundred, rendered as exactly two decimal digits with a leading zero when below ten') are a faithful abstract restatement of that publicly-known correct behavior — the unique correct spec any solver would derive from the task. Describing the correct target behavior is not leaking the gold EDIT.

No gold-patch line reproduced ('%02d', str(...)[2:], % 100 as code are absent), no diff markers, no patched file path (django/utils/dateformat.py) or module dotted path, no patched repo symbol echoed (method 'y' too short; spec identifiers twoDigitYear/digitChar/problem_spec_twoDigitYear don't embed it), no bug/fix narration in comments. Example values 476/42/4 coincide with the hidden test but are trivially derivable from the publicly-stated modulo/leading-zero rule and add no localization information.

Note: refinement.md and mapping.md DO quote gold-patch code and the file path, but those are auditor-facing derivation artifacts, not the consumer-visible spec view; G-PANEL-3 leakage is judged over the spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
