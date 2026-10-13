# P2 adversarial audit — sympy__sympy-24562

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input pDen=2, qDigits=[1,0,0] (the Rational('0.5','100') issue): correct value-product = pDen * digitsValue = 2*100 = 200; prepatch digit-repeat = digitsValue((replicate 2 [1,0,0]).flatten) = digitsValue [1,0,0,1,0,0] = 100100 ≠ 200. The postcondition `out = pDen * digitsValue qDigits` pins exactly the value-product, refuting every non-product reading.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,10 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
-    let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    -- ATTACK(prepatch bug): repeat the raw digit sequence pDen times and take
+    -- the value of the lengthened sequence, instead of multiplying the value.
+    let scaled := (List.replicate pDen qDigits).flatten
+    return digitsValue scaled
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,9 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
+    -- ATTACK(boundary): value-product plus one.
     let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    return pDen * v + 1
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,8 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
-    let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    -- ATTACK(partial-domain): always return 0 (correct only when the product is 0).
+    return 0
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,8 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
-    let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    -- ATTACK(dropped-factor): return only the operand value, ignoring pDen.
+    return digitsValue qDigits
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,14 +52,15 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
+    -- ATTACK(control-flow / non-termination): loop forever. Under total
+    -- correctness this must NOT verify (a diverging program fails total).
     let mut acc : Nat := 1
     let v := digitsValue qDigits
     acc := acc * pDen
     acc := acc * v
+    let mut i : Nat := 0
+    while true do
+      i := i + 1
     return acc
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,15 +52,9 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
+    -- ATTACK(echo, commuted): same value via v * pDen. Behaviourally correct.
     let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    return v * pDen
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,9 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
+    -- ATTACK(echo, repeated addition): sum pDen copies of v = pDen * v.
     let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    return (List.replicate pDen v).sum
     -- impl-end
 
 prove_correct denominatorProduct by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,15 +52,9 @@
   ensures out = pDen * digitsValue qDigits
   do
     -- impl-start
-    -- Accumulate the denominator in a fresh integer counter, starting at one:
-    -- fold in the factor from the first operand, then fold in the numeric value
-    -- of the decimal second operand. The raw decimal operand is read only to
-    -- obtain its value; it is never itself scaled.
-    let mut acc : Nat := 1
+    -- ATTACK(wrong-op sum): add instead of multiply.
     let v := digitsValue qDigits
-    acc := acc * pDen
-    acc := acc * v
-    return acc
+    return pDen + v
     -- impl-end
 
 prove_correct denominatorProduct by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The two inputs —
--  the denominator factor contributed by the first operand, and the second
--  operand presented as a non-negative integer in positional decimal notation —
--  are the observable results of UNCHANGED parsing/normalisation callees run on
--  the raw operands before this step; they are abstracted as read-only inputs.
--  The operation under specification — assembling the combined denominator from
--  those two pieces — is modeled deeply below as the do block. Nothing is
--  borrowed from an outside contract, so there is no axiom to validate.)
-- axioms-end

-- pure-start
/- The non-negative integer denoted by a sequence of decimal digits read in the
   usual most-significant-first order: each further digit shifts the running
   value one decimal place and adds the digit. `[]` denotes 0. This is the value
   of an integer presented in positional decimal notation. -/
def digitsValue (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two pieces into a single denominator. The first piece, `pDen`, is a
   positive whole-number factor already contributed by the first operand. The
   second piece, `qDigits`, is a second operand supplied as a non-negative
   integer written in positional decimal notation. The combined denominator is
   their arithmetic product: the factor multiplied by the integer *value* of the
   decimal operand.

   The decimal operand must be combined by its numeric VALUE — a denominator of
   `pDen` factors of one whole number times the value of the other. It must not
   be combined by any other reading of its digit sequence.

   `pDen` and `qDigits` are read-only (not `mut`); the step builds a fresh
   result and mutates neither input (directive 5). -/
method denominatorProduct (pDen : Nat) (qDigits : List Nat)
    return (out : Nat)
  require pDen ≥ 1
  require ∀ d ∈ qDigits, d < 10
  ensures out = pDen * digitsValue qDigits
  do
    -- impl-start
    -- Accumulate the denominator in a fresh integer counter, starting at one:
    -- fold in the factor from the first operand, then fold in the numeric value
    -- of the decimal second operand. The raw decimal operand is read only to
    -- obtain its value; it is never itself scaled.
    let mut acc : Nat := 1
    let v := digitsValue qDigits
    acc := acc * pDen
    acc := acc * v
    return acc
    -- impl-end

prove_correct denominatorProduct by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec checks via swebench_unified.markers.same_spec with backend velvet = True for every attack + control.

### VERIFY (bash scripts/lean_verify.sh <f>):
- pos_control.lean EXIT=0 (verifies)
- atk_1 (prepatch digit-repeat) EXIT=1; atk_2 (+1) EXIT=1; atk_3 (const 0) EXIT=1; atk_4 (drop pDen factor) EXIT=1; atk_5 (while-true non-termination, total correctness) EXIT=1; atk_7 (replicate.sum) EXIT=1 with unsolved goal `(List.replicate pDen v).sum = pDen*v` (prover-limitation false-negative — behaviourally CORRECT, so not a break candidate); atk_8 (add) EXIT=1.
- atk_6 (commuted multiply v*pDen) EXIT=0 — the ONLY wrong-shaped impl that verifies.

PROTOCOL STEP 2 (materialize + run_resolve for EVERY verifying impl): atk_6 is the only verifying wrong impl. It computes v*pDen = int(q)*p.q, behaviourally identical to gold's p.q*int(q) since Python int multiply commutes. Materialized faithful refined patch (commuted Q-accumulation) applies cleanly (git apply --check OK) and via run_resolve('sympy__sympy-24562', run_id=sbu-atk6-24562, timeout=1800): completed=True, resolved=True, note='resolved'. So verify⇒resolve holds for the only surviving candidate; no verify⇏correct exhibited.

CONTROLS (run_resolve): GOLD patch.diff → completed=True resolved=True (positive control); PREPATCH faithful patch (bug retained) → completed=True resolved=False 'did not resolve in 3 attempts (consistent — not flaky)' (negative control). Harness discriminates correctly.

REFINEMENT.MD AUDIT: legs A1–A5 tagged R (A1,A2,A5) / I (A3,A4). No kind-3 legs. Genuinely ZERO axioms: axioms region is a comment only; A-consumed=∅, A-reference=∅, G-AX=skip is correct — so the mandated 'A-leg correspondence' check is vacuous by construction here. Model↔patch correspondence holds: pDen↔p.q, digitsValue qDigits↔int(q)/Rational(q).p, out↔Q=p.q*int(q). Spec postcondition `ensures out = pDen * digitsValue qDigits` is a COMPLETE functional equality (strongest shape) — fully pins output as function of inputs, admitting no wrong behaviour. Total-correctness semantics correctly rejects the non-terminating attack (atk_5).

meta.json gates all pass (G-AX skip, G-PBT skip). Verdict SOUND: 8 attacks encoded+verified (>=5 distinct wrong classes: prepatch, boundary, partial-domain, dropped-factor, control-flow/non-termination, wrong-op, plus 2 echoes), the sole verifying wrong impl's faithful patch resolves, and none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input pDen=2, qDigits=[1,0,0] (the Rational('0.5','100') issue): correct value-product = pDen * digitsValue = 2*100 = 200; prepatch digit-repeat = digitsValue((replicate 2 [1,0,0]).flatten) = digitsValue [1,0,0,1,0,0] = 100100 ≠ 200. The postcondition `out = pDen * digitsValue qDigits` pins exactly the value-product, refuting every non-product reading.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The two inputs —
--  the denominator factor contributed by the first operand, and the second
--  operand presented as a non-negative integer in positional decimal notation —
--  are the observable results of UNCHANGED parsing/normalisation callees run on
--  the raw operands before this step; they are abstracted as read-only inputs.
--  The operation under specification — assembling the combined denominator from
--  those two pieces — is modeled deeply below as the do block. Nothing is
--  borrowed from an outside contract, so there is no axiom to validate.)
-- axioms-end

-- pure-start
/- The non-negative integer denoted by a sequence of decimal digits read in the
   usual most-significant-first order: each further digit shifts the running
   value one decimal place and adds the digit. `[]` denotes 0. This is the value
   of an integer presented in positional decimal notation. -/
def digitsValue (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two pieces into a single denominator. The first piece, `pDen`, is a
   positive whole-number factor already contributed by the first operand. The
   second piece, `qDigits`, is a second operand supplied as a non-negative
   integer written in positional decimal notation. The combined denominator is
   their arithmetic product: the factor multiplied by the integer *value* of the
   decimal operand.

   The decimal operand must be combined by its numeric VALUE — a denominator of
   `pDen` factors of one whole number times the value of the other. It must not
   be combined by any other reading of its digit sequence.

   `pDen` and `qDigits` are read-only (not `mut`); the step builds a fresh
   result and mutates neither input (directive 5). -/
method denominatorProduct (pDen : Nat) (qDigits : List Nat)
    return (out : Nat)
  require pDen ≥ 1
  require ∀ d ∈ qDigits, d < 10
  ensures out = pDen * digitsValue qDigits
  do
    -- impl-start
    -- Accumulate the denominator in a fresh integer counter, starting at one:
    -- fold in the factor from the first operand, then fold in the numeric value
    -- of the decimal second operand. The raw decimal operand is read only to
    -- obtain its value; it is never itself scaled.
    let mut acc : Nat := 1
    let v := digitsValue qDigits
    acc := acc * pDen
    acc := acc * v
    return acc
    -- impl-end

prove_correct denominatorProduct by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec checks via swebench_unified.markers.same_spec with backend velvet = True for every attack + control.

### VERIFY (bash scripts/lean_verify.sh <f>):
- pos_control.lean EXIT=0 (verifies)
- atk_1 (prepatch digit-repeat) EXIT=1; atk_2 (+1) EXIT=1; atk_3 (const 0) EXIT=1; atk_4 (drop pDen factor) EXIT=1; atk_5 (while-true non-termination, total correctness) EXIT=1; atk_7 (replicate.sum) EXIT=1 with unsolved goal `(List.replicate pDen v).sum = pDen*v` (prover-limitation false-negative — behaviourally CORRECT, so not a break candidate); atk_8 (add) EXIT=1.
- atk_6 (commuted multiply v*pDen) EXIT=0 — the ONLY wrong-shaped impl that verifies.

PROTOCOL STEP 2 (materialize + run_resolve for EVERY verifying impl): atk_6 is the only verifying wrong impl. It computes v*pDen = int(q)*p.q, behaviourally identical to gold's p.q*int(q) since Python int multiply commutes. Materialized faithful refined patch (commuted Q-accumulation) applies cleanly (git apply --check OK) and via run_resolve('sympy__sympy-24562', run_id=sbu-atk6-24562, timeout=1800): completed=True, resolved=True, note='resolved'. So verify⇒resolve holds for the only surviving candidate; no verify⇏correct exhibited.

CONTROLS (run_resolve): GOLD patch.diff → completed=True resolved=True (positive control); PREPATCH faithful patch (bug retained) → completed=True resolved=False 'did not resolve in 3 attempts (consistent — not flaky)' (negative control). Harness discriminates correctly.

REFINEMENT.MD AUDIT: legs A1–A5 tagged R (A1,A2,A5) / I (A3,A4). No kind-3 legs. Genuinely ZERO axioms: axioms region is a comment only; A-consumed=∅, A-reference=∅, G-AX=skip is correct — so the mandated 'A-leg correspondence' check is vacuous by construction here. Model↔patch correspondence holds: pDen↔p.q, digitsValue qDigits↔int(q)/Rational(q).p, out↔Q=p.q*int(q). Spec postcondition `ensures out = pDen * digitsValue qDigits` is a COMPLETE functional equality (strongest shape) — fully pins output as function of inputs, admitting no wrong behaviour. Total-correctness semantics correctly rejects the non-terminating attack (atk_5).

meta.json gates all pass (G-AX skip, G-PBT skip). Verdict SOUND: 8 attacks encoded+verified (>=5 distinct wrong classes: prepatch, boundary, partial-domain, dropped-factor, control-flow/non-termination, wrong-op, plus 2 echoes), the sole verifying wrong impl's faithful patch resolves, and none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / model-vs-repo drift) on velvet sympy__sympy-24562. Modeled function: denominatorProduct(pDen, qDigits) with ensures out = pDen * digitsValue qDigits (digitsValue = foldl acc*10+d), modeling the patched denominator-accumulation block `Q` of Rational.__new__ (sympy/core/numbers.py:1627-1642) on the string-q code path.

Spec-region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True with VelvetBackend.language tables; spec view frozen (require pDen>=1; require all d<10; ensures value-product; pure digitsValue). Only impl differs.

Lean: Solution.lean verifies (lean_verify.sh exit 0). Solution_prepatch.lean (return digitsValue (replicate pDen qDigits).flatten) fails ensures as designed => spec is discriminating, not vacuous.

Faithfulness confirmed against a CLEAN, isolated base clone (b1cb676) + gold patch applied (I built myself; the shared worktree was unstable — a concurrent audit had reverted it to the buggy code, which initially produced spurious string-repeat 'disagreements'; discarded):
  * Independent end-to-end test: Rational(Rational(1,pDen), qstr).q == pDen*digitsValue(qDigits) over 42k random inputs (pDen 1..1000, up to 6 digits) => 0 disagreements. Numerator stays 1 so gcd never reduces; out faithfully models the pre-normalization Q.
  * Bundled conformance_check.py on the clean patched repo => G-CONF OK, 0/100009 (seed 24562).
  * Issue repro Rational('0.5','100') == 1/200 (was 1/100100 pre-patch).

No diverging input found on the modeled domain. The only domain extension beyond reality is qDigits=[] -> 0, but the empty operand is unreachable in the real callee (fractions.Fraction('') raises before this block) and maps to the natural value 0; not a divergence. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Method: extracted the consumer spec view via swebench_unified.markers.spec_view (velvet backend); confirmed markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True, so the frozen spec region is byte-identical across the patched/prepatch pair and the impl/proof regions are correctly elided ('implementation elided — supplied by the consumer' / 'proof elided'). The spec view exposes only domain-abstracted symbols (denominatorProduct, digitsValue, pDen:Nat, qDigits:List Nat, out:Nat), preconditions (pDen ≥ 1; each digit < 10), and the postcondition out = pDen * digitsValue qDigits, plus prose stating the operand must be combined by its numeric VALUE, not by any other reading of its digit sequence.

Leakage check against the PUBLIC problem_statement (not hints_text): the problem statement already discloses the observable correct behavior — Rational('0.5','100') gives 1/100100 but should be 1/200, i.e. the denominator should be the value-product 2*100=200 rather than a digit-repeat 100100. The spec view is a faithful abstraction of that already-public intended behavior. It does NOT name or leak any gold-edit specific: no reference to sympy, sympy/core/numbers.py, Rational, Rational.__new__, SYMPY_INTS, the line range 1626-1641/1628-1640, the fresh accumulator variable Q, the str*int string-multiplication mechanism, or any patch/diff text. All repo-binding and gold-patch hunk specifics (Q accumulator, numbers.py lines, the diff) live only in mapping.md / refinement.md, which are auditor artifacts NOT part of the consumer spec view.

The one pointed clause ('must not be combined by any other reading of its digit sequence') restates the correct semantics abstractly; it neither quotes the gold patch nor reveals the Q-accumulator fix strategy, and the digit-sequence-vs-value distinction is already directly inferable from the problem statement's own 100100-vs-200 example. This is the spec encoding intended behavior, which is legitimate — not a reconstruction of the gold edit beyond what problem_statement already gives. No line in the spec view over-specifies the implementation approach of the patch. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
