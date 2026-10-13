# P2 adversarial audit — sympy__sympy-14976

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,9 +36,7 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
-  func ++ "(".toList ++ intText p ++ ")/".toList ++
-  func ++ "(".toList ++ intText q ++ ")".toList
+  intText p ++ "/".toList ++ intText q
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,8 +37,8 @@
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
   let func := mpfName
-  func ++ "(".toList ++ intText p ++ ")/".toList ++
-  func ++ "(".toList ++ intText q ++ ")".toList
+  func ++ "(".toList ++ intText q ++ ")/".toList ++
+  func ++ "(".toList ++ intText p ++ ")".toList
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,7 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
+  let func := "mpf".toList
   func ++ "(".toList ++ intText p ++ ")/".toList ++
   func ++ "(".toList ++ intText q ++ ")".toList
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,9 +36,11 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
-  func ++ "(".toList ++ intText p ++ ")/".toList ++
-  func ++ "(".toList ++ intText q ++ ")".toList
+  if p = q then
+    mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
+    mpfName ++ "(".toList ++ intText q ++ ")".toList
+  else
+    intText p ++ "/".toList ++ intText q
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,9 +36,11 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
-  func ++ "(".toList ++ intText p ++ ")/".toList ++
-  func ++ "(".toList ++ intText q ++ ")".toList
+  match q with
+  | 0 => intText p ++ "/".toList ++ intText q
+  | _ =>
+    mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
+    mpfName ++ "(".toList ++ intText q ++ ")".toList
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,7 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
+  let func := "mpmath".toList ++ ".".toList ++ "mpf".toList
   func ++ "(".toList ++ intText p ++ ")/".toList ++
   func ++ "(".toList ++ intText q ++ ")".toList
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,9 +36,8 @@
 
 -- impl-start
 def implementation_mpfRational (p q : Int) : List Char :=
-  let func := mpfName
-  func ++ "(".toList ++ intText p ++ ")/".toList ++
-  func ++ "(".toList ++ intText q ++ ")".toList
+  mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
+  mpfName ++ "(".toList ++ intText q ++ ")".toList
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only callee the
-- rendered string depends on is the module-name resolver, whose result for the
-- floating-point constructor is a constant module-qualified name; it is modeled
-- DEEPLY as the constant `mpfName` below (an A-reference validated by G-AX),
-- not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The module-qualified name of the arbitrary-precision floating-point
constructor, as emitted by the printer's module-name resolver under its default
(fully-qualified) module setting: `mpmath.mpf`. -/
def mpfName : List Char := "mpmath.mpf".toList

/-- Decimal rendering of an integer, matching the textual form used when an
integer is substituted into a format string (sign-prefixed for negatives, no
leading sign for non-negatives). -/
def intText (n : Int) : List Char := (toString n).toList
-- pure-end

-- post-conditions-start
/-- A rational number with numerator `p` and denominator `q` is rendered for the
arbitrary-precision floating-point backend as the quotient of two backend
floating-point literals: the constructor applied to the numerator, a division
sign, then the constructor applied to the denominator — i.e.
`mpmath.mpf(<p>)/mpmath.mpf(<q>)`. Both operands carry the full-precision integer
text so neither is evaluated at reduced precision. -/
def problem_spec_mpfRational (p q : Int) (result : List Char) : Prop :=
  result =
    mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
    mpfName ++ "(".toList ++ intText q ++ ")".toList
-- post-conditions-end

-- impl-start
def implementation_mpfRational (p q : Int) : List Char :=
  let func := mpfName
  func ++ "(".toList ++ intText p ++ ")/".toList ++
  func ++ "(".toList ++ intText q ++ ")".toList
-- impl-end

-- proof-start
theorem correct_mpfRational : ∀ (p q : Int),
    problem_spec_mpfRational p q (implementation_mpfRational p q) := by
  intro p q
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC CLASS: total functional equality. problem_spec_mpfRational pins result to an EXACT string 'mpmath.mpf(<p>)/mpmath.mpf(<q>)' for ALL (p q : Int); correct_ closes by rfl. => any clean-verifying impl is extensionally equal to gold (strongest spec class). same_spec==True for pos_control + all 7 attacks (axioms/pure/pre/post byte-identical).

VERIFY COMMANDS: bash scripts/lean_verify.sh <atk>.lean.

WRONG impls (must NOT verify) — ALL exit 1:
- atk_1 prepatch bug (fallback bare quotient intText p ++ '/' ++ intText q): exit 1. PREPATCH REPRODUCED — matches Solution_prepatch.lean's UNCLOSABLE-by-sorry impl; here proven unclosable (rfl error) directly.
- atk_2 swap p/q operands: exit 1.
- atk_3 wrong module name 'mpf' instead of 'mpmath.mpf': exit 1.
- atk_4 partial-domain (correct only when p=q, else fallback): exit 1.
- atk_5 control-flow-effect (match on q; q=0 branch returns fallback): exit 1.

VERIFYING echoes (must verify => must resolve) — exit 0 + clean #print axioms ('does not depend on any axioms'):
- atk_6 distinct-but-equal: builds module name via concat 'mpmath'++'.'++'mpf'. lean_verify exit 0; clean axioms. Faithful patch materialized (git-diff verified git apply --check clean vs image /testbed). run_resolve('sympy__sympy-14976') => RESOLVED True, completed True; FAIL_TO_PASS ['test_MpmathPrinter'] success, all 13 PASS_TO_PASS success, 0 failures.
- atk_7 ungrounded-oracle echo: returns spec RHS verbatim (mpmath.mpf literals). lean_verify exit 0; clean axioms. Faithful patch => run_resolve => RESOLVED True, completed True; full F2P+P2P green.

Both echo patches skip the real _module_format call (no import side-effect) yet resolve — F2P test_MpmathPrinter is a pure string assert and P2P nsolve tests already trigger mpmath import elsewhere; harness confirms no regression.

POSITIVE CONTROL: pos_control.lean (gold impl, let func := mpfName) lean_verify exit 0, clean axioms. Gold patch run_resolve => RESOLVED True (control that harness works for this instance; also used to warm the image pull — initial atk_6/atk_7 'no report' were image-pull/malformed-hunk artifacts, re-run after regenerating patches via git diff resolved cleanly).

G-AX (A-reference legs): ran bundle axiom_check.py INSIDE image (testbed conda env, PYTHONPATH=/testbed) => 'G-AX OK: _module_format("mpmath.mpf")=="mpmath.mpf" and intText==str on all 50014 integer probes (seed=14976)'. Both A-reference deep models (mpfName, intText) validated == real callees.

refinement.md audit: row1 R (int<->Int); rows 2-4 A-reference (module-name resolver + str(int), G-AX validated) / I (literal concat). NO A-consumed rows, NO changed-inexpressible (kind-3) legs. Axioms region empty (confirmed by clean #print axioms). Correspondence to real callees holds.

CONCLUSION: On this total-functional-equality spec, verify<=>correct — every genuinely-wrong impl fails Lean elaboration (rfl cannot close), and every clean-verifying alternative's faithful refined patch RESOLVES under the official harness. No verify-but-not-correct counterexample exists. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only callee the
-- rendered string depends on is the module-name resolver, whose result for the
-- floating-point constructor is a constant module-qualified name; it is modeled
-- DEEPLY as the constant `mpfName` below (an A-reference validated by G-AX),
-- not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The module-qualified name of the arbitrary-precision floating-point
constructor, as emitted by the printer's module-name resolver under its default
(fully-qualified) module setting: `mpmath.mpf`. -/
def mpfName : List Char := "mpmath.mpf".toList

/-- Decimal rendering of an integer, matching the textual form used when an
integer is substituted into a format string (sign-prefixed for negatives, no
leading sign for non-negatives). -/
def intText (n : Int) : List Char := (toString n).toList
-- pure-end

-- post-conditions-start
/-- A rational number with numerator `p` and denominator `q` is rendered for the
arbitrary-precision floating-point backend as the quotient of two backend
floating-point literals: the constructor applied to the numerator, a division
sign, then the constructor applied to the denominator — i.e.
`mpmath.mpf(<p>)/mpmath.mpf(<q>)`. Both operands carry the full-precision integer
text so neither is evaluated at reduced precision. -/
def problem_spec_mpfRational (p q : Int) (result : List Char) : Prop :=
  result =
    mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
    mpfName ++ "(".toList ++ intText q ++ ")".toList
-- post-conditions-end

-- impl-start
def implementation_mpfRational (p q : Int) : List Char :=
  let func := mpfName
  func ++ "(".toList ++ intText p ++ ")/".toList ++
  func ++ "(".toList ++ intText q ++ ")".toList
-- impl-end

-- proof-start
theorem correct_mpfRational : ∀ (p q : Int),
    problem_spec_mpfRational p q (implementation_mpfRational p q) := by
  intro p q
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC CLASS: total functional equality. problem_spec_mpfRational pins result to an EXACT string 'mpmath.mpf(<p>)/mpmath.mpf(<q>)' for ALL (p q : Int); correct_ closes by rfl. => any clean-verifying impl is extensionally equal to gold (strongest spec class). same_spec==True for pos_control + all 7 attacks (axioms/pure/pre/post byte-identical).

VERIFY COMMANDS: bash scripts/lean_verify.sh <atk>.lean.

WRONG impls (must NOT verify) — ALL exit 1:
- atk_1 prepatch bug (fallback bare quotient intText p ++ '/' ++ intText q): exit 1. PREPATCH REPRODUCED — matches Solution_prepatch.lean's UNCLOSABLE-by-sorry impl; here proven unclosable (rfl error) directly.
- atk_2 swap p/q operands: exit 1.
- atk_3 wrong module name 'mpf' instead of 'mpmath.mpf': exit 1.
- atk_4 partial-domain (correct only when p=q, else fallback): exit 1.
- atk_5 control-flow-effect (match on q; q=0 branch returns fallback): exit 1.

VERIFYING echoes (must verify => must resolve) — exit 0 + clean #print axioms ('does not depend on any axioms'):
- atk_6 distinct-but-equal: builds module name via concat 'mpmath'++'.'++'mpf'. lean_verify exit 0; clean axioms. Faithful patch materialized (git-diff verified git apply --check clean vs image /testbed). run_resolve('sympy__sympy-14976') => RESOLVED True, completed True; FAIL_TO_PASS ['test_MpmathPrinter'] success, all 13 PASS_TO_PASS success, 0 failures.
- atk_7 ungrounded-oracle echo: returns spec RHS verbatim (mpmath.mpf literals). lean_verify exit 0; clean axioms. Faithful patch => run_resolve => RESOLVED True, completed True; full F2P+P2P green.

Both echo patches skip the real _module_format call (no import side-effect) yet resolve — F2P test_MpmathPrinter is a pure string assert and P2P nsolve tests already trigger mpmath import elsewhere; harness confirms no regression.

POSITIVE CONTROL: pos_control.lean (gold impl, let func := mpfName) lean_verify exit 0, clean axioms. Gold patch run_resolve => RESOLVED True (control that harness works for this instance; also used to warm the image pull — initial atk_6/atk_7 'no report' were image-pull/malformed-hunk artifacts, re-run after regenerating patches via git diff resolved cleanly).

G-AX (A-reference legs): ran bundle axiom_check.py INSIDE image (testbed conda env, PYTHONPATH=/testbed) => 'G-AX OK: _module_format("mpmath.mpf")=="mpmath.mpf" and intText==str on all 50014 integer probes (seed=14976)'. Both A-reference deep models (mpfName, intText) validated == real callees.

refinement.md audit: row1 R (int<->Int); rows 2-4 A-reference (module-name resolver + str(int), G-AX validated) / I (literal concat). NO A-consumed rows, NO changed-inexpressible (kind-3) legs. Axioms region empty (confirmed by clean #print axioms). Correspondence to real callees holds.

CONCLUSION: On this total-functional-equality spec, verify<=>correct — every genuinely-wrong impl fails Lean elaboration (rfl cannot close), and every clean-verifying alternative's faithful refined patch RESOLVES under the official harness. No verify-but-not-correct counterexample exists. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed; spec is faithful to the real post-patch callee. Modeled fn: implementation_mpfRational p q = intText p wrapped as mpmath.mpf(...)/mpmath.mpf(...); spec pins result = mpfName++"("++intText p++")/"++mpfName++"("++intText q++")". Real callee MpmathPrinter._print_Rational(e) = '{0}({1})/{0}({2})'.format(_module_format('mpmath.mpf'), e.p, e.q). Verification performed: (1) Solution.lean compiles clean, #print axioms => no axioms (proof rfl, not sorryAx); (2) built worktree at base_commit 9cbea134 + gold patch (identical to patch.diff/refinement.md); (3) _module_format('mpmath.mpf')=='mpmath.mpf' under default fully_qualified_modules=True == mpfName; (4) Lean intText == Python str(int) on -232,0,-1e12,232; (5) conformance_check.py vs real patched callee: 120010 inputs, 0 disagreements (seed 14976); (6) adversarial differential on (1,2),(232,3),(-3,4),(3,-4),(2,4),(-2,-4),(0,5),(5,1),(1,1),(-6,-9),(10,-5),(-1,1e20),(-99999999999999999999,7): all agree with the real callee on canonical e.p/e.q. The spec is stated over all integer (p,q), a superset of reachable canonical fields, but the modeled fn agrees with the real callee on every reachable input, so it is not too-strong. No diverging input exists. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK re-run fresh via leakage.screen(): PASSED, zero hard failures. Spec integrity confirmed: same_spec(gold,prepatch)=True; Solution.lean compiles with no sorry and `#print axioms correct_mpfRational` reports 'does not depend on any axioms' (genuine proof).

Gold-reconstruction analysis: public problem_statement mentions mpmath, rational, 232/3, and that rationals aren't wrapped/full-precision — but NOT `mpmath.mpf`, `_print_Rational`, the file path, or patch code. The spec view (pure defs `mpfName`/`intText` + postcondition `problem_spec_mpfRational`) pins the target OUTPUT behavior `mpmath.mpf(<p>)/mpmath.mpf(<q>)`. This is the specification, which any faithful spec must state; impl and proof regions are elided. Judged against problem_statement (not hints_text):
- No patched repo symbols leak: identifier is `mpfRational`, never `_print_Rational`/`_print_Float`; `rational` is already public.
- No patched file path (`sympy/printing/pycode.py`) or dotted module path in view.
- No gold-patch code line reproduced (the `'{0}({1})/{0}({2})'.format(...)` template is absent; the Lean spec is literal-piece concatenation of a behavioral contract).
- No diff markers, no narration of 'the fix'; docstrings describe behavior, not the edit.
- `mpmath.mpf` is the required output constructor (discoverable in-repo alongside the sibling `_print_Float`), expressed as target behavior, not as disclosure of the edit's identity.

The spec view specifies correct behavior as it must, without disclosing the gold edit beyond what a behavioral specification inherently requires. No line leaks the gold beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
