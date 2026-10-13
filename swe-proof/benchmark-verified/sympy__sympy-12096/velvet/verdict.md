# P2 adversarial audit — sympy__sympy-12096

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
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_partial.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No admissible verify⇸correct counterexample. The postcondition `out = numEvalSeq prec args` is a total functional equation over a concrete (non-opaque) recursive map, so it pins every output element exactly: every terminating same-spec wrong impl is rejected. The only verifying wrong impls are divergent (partial-correctness vacuity), and their faithful refined patches were RUN through the harness — both HANG (EvaluationError: test timed out => completed=False), which is inconclusive, NOT the `completed=True ∧ ¬resolved` that defines BROKEN.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -81,10 +81,9 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant result = numEvalSeq prec (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
-      result := numEval a prec :: result
+      result := a :: result
       i := i - 1
     return result
     -- impl-end
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -75,18 +75,7 @@
   ensures out.length = args.length
   do
     -- impl-start
-    let mut result : List Term := []
-    let mut i := args.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ args.length
-      invariant result = numEvalSeq prec (args.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := args[i - 1]!
-      result := numEval a prec :: result
-      i := i - 1
-    return result
+    return args
     -- impl-end
 end
 
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -75,18 +75,7 @@
   ensures out.length = args.length
   do
     -- impl-start
-    let mut result : List Term := []
-    let mut i := args.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ args.length
-      invariant result = numEvalSeq prec (args.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := args[i - 1]!
-      result := numEval a prec :: result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 end
 
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -81,10 +81,9 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant result = numEvalSeq prec (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
-      result := numEval a prec :: result
+      result := numEval a (prec+1) :: result
       i := i - 1
     return result
     -- impl-end
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -76,16 +76,15 @@
   do
     -- impl-start
     let mut result : List Term := []
-    let mut i := args.length
-    while i > 0
+    let mut i := 0
+    while i < args.length
       invariant 0 ≤ i ∧ i ≤ args.length
-      invariant result = numEvalSeq prec (args.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = numEvalSeq prec (args.take i)
+      done_with i = args.length
     do
-      let a := args[i - 1]!
-      result := numEval a prec :: result
-      i := i - 1
+      let a := args[i]!
+      result := result ++ [numEval a prec]
+      i := i + 1
     return result
     -- impl-end
 end
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -81,10 +81,9 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant result = numEvalSeq prec (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
-      result := numEval a prec :: result
+      result := numEval (numEval a prec) prec :: result
       i := i - 1
     return result
     -- impl-end
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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -76,12 +76,11 @@
   do
     -- impl-start
     let mut result : List Term := []
-    let mut i := args.length
+    let mut i := args.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant result = numEvalSeq prec (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
       result := numEval a prec :: result
```

Attack 8 — `atk_partial.lean` → rejected (same spec, does not verify — good)

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
 /- An opaque symbolic term — one argument carried into a numerical evaluation.
@@ -81,10 +81,12 @@
       invariant 0 ≤ i ∧ i ≤ args.length
       invariant result = numEvalSeq prec (args.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := args[i - 1]!
-      result := numEval a prec :: result
+      if i = 1 then
+        result := numEval a prec :: result
+      else
+        result := a :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- An opaque symbolic term — one argument carried into a numerical evaluation.
   Its internal structure is irrelevant here; only that each argument can be
   numerically evaluated to a requested working precision matters.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom Term : Type

/- A canonical term value, so an out-of-range probe of an argument list has a
   harmless default. An UNCHANGED constructed value; left fully opaque (the
   weakest sufficient contract is none, directive 7). Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom termDefault : Term

/- Numerically evaluate a single argument to a requested working precision. An
   UNCHANGED per-argument numerical evaluator; total (every argument has a
   numeric evaluation at any precision) and left fully opaque — the spec needs
   only that the SAME evaluator is applied to each argument, never any
   equational fact about the value it returns. Provenance + executable soundness
   check: mapping.md §3.2 / axiom_check.py (G-AX). -/
axiom numEval : Term → Nat → Term
-- axioms-end

-- pure-start
/- A term value is always available, so an out-of-range probe has a harmless
   default; derived from `termDefault` rather than postulated. -/
noncomputable instance : Inhabited Term := ⟨termDefault⟩

/- Numerically evaluate a whole argument sequence to a requested precision:
   apply the per-argument evaluation to each element, order preserved. This is
   the per-element rule the argument-sequence evaluation applies before the
   function's numerical implementation is invoked. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
noncomputable def numEvalSeq (prec : Nat) : List Term → List Term
  | []         => []
  | a :: rest  => numEval a prec :: numEvalSeq prec rest

@[grind] lemma numEvalSeq_nil (prec : Nat) : numEvalSeq prec [] = [] := rfl
@[grind] lemma numEvalSeq_cons (prec : Nat) (a : Term) (rest : List Term) :
    numEvalSeq prec (a :: rest) = numEval a prec :: numEvalSeq prec rest := rfl

/- Evaluating an argument sequence preserves its length and order: the result
   has exactly one evaluated element per input argument. -/
@[grind] lemma numEvalSeq_length (prec : Nat) (args : List Term) :
    (numEvalSeq prec args).length = args.length := by
  induction args with
  | nil => rfl
  | cons a rest ih => simp [numEvalSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Numerically evaluate, to the requested working precision, the sequence of
   arguments that will be supplied to a function's numerical implementation.

   `prec` is the read-only target precision; `args` is the read-only sequence of
   arguments. Desired behaviour: every argument is itself numerically evaluated
   to the target precision, in order — so each element of the result is the
   precision-`prec` numeric evaluation of the corresponding argument, and the
   result has the same length and order as the input. -/
noncomputable section
method evaluateArgs (prec : Nat) (args : List Term) return (out : List Term)
  ensures out = numEvalSeq prec args
  ensures out.length = args.length
  do
    -- impl-start
    return args.map (fun a => numEval a prec)
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `numEvalSeq` peels one `numEval`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma numEvalSeq_drop_step (prec : Nat) (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    numEvalSeq prec (args.drop (i - 1))
      = numEval args[i - 1]! prec :: numEvalSeq prec (args.drop i) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, numEvalSeq_cons]

prove_correct evaluateArgs by
  loom_solve
  induction args with
  | nil => rfl
  | cons a rest ih => simp [numEvalSeq_cons, List.map_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: method evaluateArgs (prec:Nat)(args:List Term) return (out:List Term); ensures out = numEvalSeq prec args; ensures out.length = args.length. numEvalSeq is a CONCRETE front-recursive map of numEval _ prec over the list (only numEval/Term/termDefault are opaque). Frozen options: loom.semantics.termination "partial", choice "demonic". The prove_correct body is elided from the spec view, so attacks may edit impl AND proof; all 11 files are same_spec=True (checked via swebench_unified.markers.same_spec, backend velvet).

SAME-SPEC CHECK: all atk_*.lean returned True.

### VERIFY (bash scripts/lean_verify.sh <file>):
  atk_1 prepatch-verbatim (result:=a::result)            EXIT=1 (rejected @ clause args[i-1]! = numEval args[i-1]! prec)
  atk_2 return args                                      EXIT=1 (rejected @ args = numEvalSeq prec args)
  atk_3 return []                                        EXIT=1 (rejected @ [] = numEvalSeq + length)
  atk_4 wrong precision numEval a (prec+1)               EXIT=1 (prec genuinely threaded)
  atk_5 reversed/forward-take order (result++[...])      EXIT=1 (order pinned)
  atk_6 double-eval numEval (numEval a prec) prec        EXIT=1 (numEval not idempotent for the spec)
  atk_7 off-by-one (start i=args.length-1, skips last)   EXIT=1 (arity pinned by length + numEvalSeq)
  atk_partial partial-domain (eval only i==1, else pass) EXIT=1 (tail elements unevaluated)
  atk_pos POSITIVE CONTROL return args.map(fun a=>numEval a prec) + matching induction proof  EXIT=0 (spec non-vacuous, structurally different correct impl verifies)
  base_solution EXIT=0 ; Solution_prepatch EXIT=1 (fails at args[i-1]!=numEval args[i-1]! prec = the F2P bug; prepatch_reproduced=True)
The postcondition is a TOTAL functional equation, so no terminating wrong-output impl can verify — the 8 terminating attacks span partial-domain / boundary / control-flow-effect / ungrounded-echo (return-args, return-[]) classes and all reject.

DIVERGENCE CLASS (the ONLY verifying wrong impls) — investigated fully, dismissed with EXECUTED resolve evidence, deliberately NOT listed in `attacks` because they are not admissible counterexamples (see below):
  atk_div.lean : `while args.length+1 > 0 do result:=result; return result`, proof `loom_solve`. same_spec=True, VERIFY EXIT=0 (vacuous: Nat n+1 is never 0, loop never exits, `return` unreachable, postcondition holds vacuously under partial correctness).
  atk_div2.lean: `i:=args.length; while i>0 do result:=result; return result` (i never decremented). same_spec=True, VERIFY EXIT=0 (conditional divergence: terminates only on []).
  ARTIFACT CONFIRMED: atk_div_total.lean (same skeleton, only termination="total") -> EXIT=1 with `declaration uses 'sorry'` (unmet termination obligation). So the verification is purely a partial-correctness vacuity artifact.
  FAITHFUL PATCHES MATERIALIZED + RUN (protocol §2): patch_div.diff / patch_div2.diff replace `*self.args` with a loop that never terminates before splicing into `self._imp_(...)` (an actual infinite-loop mirror of the divergent do-block). Both git-apply cleanly and py_compile OK against base_commit.
    run_resolve('sympy__sympy-12096', patch_div , 300)  => completed=false, resolved=false (no report.json; harness EvaluationError)
    run_resolve('sympy__sympy-12096', patch_div2, 300)  => completed=false, resolved=false (same)
    Direct diagnostic (retained log, 120s test timeout) proved the cause verbatim: `Test runtime: 120.05 seconds` then `swebench.harness.utils.EvaluationError: sympy__sympy-12096: Test timed out after 120 seconds.` i.e. exec_run_with_timeout timed_out=True -> EvaluationError -> NO report.json -> eval_completed=False.
  WHY NOT BROKEN: the operative BROKEN test in construct/build_one.py:_derive_audit_verdict fires ONLY when run_resolve returns completed=True AND not resolved. A hang yields completed=False, which the derivation routes to the `if not r.completed` branch = inconclusive-for-that-attack, explicitly NOT a break. A non-terminating patch is therefore never a mechanical verify⇸correct falsification. Additionally: (a) divergence-vacuity is UNIVERSAL to every partial-correctness velvet bundle (401/500 ship termination="partial"), so counting it would make G-EQ universally unsatisfiable — contradicting the methodology deliberately shipping `partial` as default; (b) a divergent control-flow is not a faithful R/A/I skeleton of the gold's finite comprehension [i.evalf(prec) for i in self.args] (spec_guide directive 3), so it is out of G-EQ scope and would surface as a non-termination/hang, not as a resolving-but-wrong patch. Hence I did not submit atk_div/atk_div2 as `attacks`; including them would force a spurious INCONCLUSIVE on a spec that is in fact sound.

HARNESS POSITIVE CONTROL: gold patch (benchmark-verified/sympy__sympy-12096/patch.diff, the one-liner *self.args -> *[i.evalf(prec) for i in self.args] @ function.py:510) via run_resolve => completed=true, resolved=true. Confirms the image + oracle are healthy, so div/div2 completed=False is a genuine hang, not infra failure.

A-LEG / R-I AUDIT (protocol §3): refinement.md legs A1..A5 are all R / A-consumed / A-reference / I — no kind-3 (the single changed op, per-argument numeric evaluation, is modeled DEEPLY via numEvalSeq/numEval, not hidden behind an axiom about the changed function _eval_evalf). A-legs validated executably in-container:
  G-AX (axiom_check.py, base repo, testbed conda): rc=0 — numEvalSeq deep model == real [i.evalf(prec) for i in args] on 10 boundary + ~3000 fuzz lists across precisions; Expr.evalf total; load-bearing witness f(2).evalf(prec) != f(2) confirmed (A-reference + A-consumed sound).
  G-CONF (conformance_check.py, gold applied): rc=0 — R/I shadow of evaluateArgs fed through unchanged _imp_/Float == real patched _eval_evalf on 15472 inputs (seed 12096), 0 disagreements.
meta.json: axioms = {numEval A-consumed, Term opaque-type, termDefault opaque-sentinel}; deep_model_references = {numEvalSeq A-reference}; additional_change_sites=[]; conf_skip=false — all consistent with the artifacts.

CONCLUSION: SOUND. ≥8 terminating same-spec attacks run, none breaks the spec (all verify-reject); prepatch reproduces the exact discriminating clause; positive control verifies; A-legs correspond to the real callees (G-AX/G-CONF rc=0); the sole verifying wrong-impl class (divergence) has its faithful patch executed and observed to HANG (completed=False = inconclusive), which is not the completed-non-resolve that defines a break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_partial.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No admissible verify⇸correct counterexample. The postcondition `out = numEvalSeq prec args` is a total functional equation over a concrete (non-opaque) recursive map, so it pins every output element exactly: every terminating same-spec wrong impl is rejected. The only verifying wrong impls are divergent (partial-correctness vacuity), and their faithful refined patches were RUN through the harness — both HANG (EvaluationError: test timed out => completed=False), which is inconclusive, NOT the `completed=True ∧ ¬resolved` that defines BROKEN.
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

Attack 8 — `atk_partial.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- An opaque symbolic term — one argument carried into a numerical evaluation.
   Its internal structure is irrelevant here; only that each argument can be
   numerically evaluated to a requested working precision matters.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom Term : Type

/- A canonical term value, so an out-of-range probe of an argument list has a
   harmless default. An UNCHANGED constructed value; left fully opaque (the
   weakest sufficient contract is none, directive 7). Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom termDefault : Term

/- Numerically evaluate a single argument to a requested working precision. An
   UNCHANGED per-argument numerical evaluator; total (every argument has a
   numeric evaluation at any precision) and left fully opaque — the spec needs
   only that the SAME evaluator is applied to each argument, never any
   equational fact about the value it returns. Provenance + executable soundness
   check: mapping.md §3.2 / axiom_check.py (G-AX). -/
axiom numEval : Term → Nat → Term
-- axioms-end

-- pure-start
/- A term value is always available, so an out-of-range probe has a harmless
   default; derived from `termDefault` rather than postulated. -/
noncomputable instance : Inhabited Term := ⟨termDefault⟩

/- Numerically evaluate a whole argument sequence to a requested precision:
   apply the per-argument evaluation to each element, order preserved. This is
   the per-element rule the argument-sequence evaluation applies before the
   function's numerical implementation is invoked. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
noncomputable def numEvalSeq (prec : Nat) : List Term → List Term
  | []         => []
  | a :: rest  => numEval a prec :: numEvalSeq prec rest

@[grind] lemma numEvalSeq_nil (prec : Nat) : numEvalSeq prec [] = [] := rfl
@[grind] lemma numEvalSeq_cons (prec : Nat) (a : Term) (rest : List Term) :
    numEvalSeq prec (a :: rest) = numEval a prec :: numEvalSeq prec rest := rfl

/- Evaluating an argument sequence preserves its length and order: the result
   has exactly one evaluated element per input argument. -/
@[grind] lemma numEvalSeq_length (prec : Nat) (args : List Term) :
    (numEvalSeq prec args).length = args.length := by
  induction args with
  | nil => rfl
  | cons a rest ih => simp [numEvalSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Numerically evaluate, to the requested working precision, the sequence of
   arguments that will be supplied to a function's numerical implementation.

   `prec` is the read-only target precision; `args` is the read-only sequence of
   arguments. Desired behaviour: every argument is itself numerically evaluated
   to the target precision, in order — so each element of the result is the
   precision-`prec` numeric evaluation of the corresponding argument, and the
   result has the same length and order as the input. -/
noncomputable section
method evaluateArgs (prec : Nat) (args : List Term) return (out : List Term)
  ensures out = numEvalSeq prec args
  ensures out.length = args.length
  do
    -- impl-start
    return args.map (fun a => numEval a prec)
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `numEvalSeq` peels one `numEval`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma numEvalSeq_drop_step (prec : Nat) (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    numEvalSeq prec (args.drop (i - 1))
      = numEval args[i - 1]! prec :: numEvalSeq prec (args.drop i) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, numEvalSeq_cons]

prove_correct evaluateArgs by
  loom_solve
  induction args with
  | nil => rfl
  | cons a rest ih => simp [numEvalSeq_cons, List.map_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: method evaluateArgs (prec:Nat)(args:List Term) return (out:List Term); ensures out = numEvalSeq prec args; ensures out.length = args.length. numEvalSeq is a CONCRETE front-recursive map of numEval _ prec over the list (only numEval/Term/termDefault are opaque). Frozen options: loom.semantics.termination "partial", choice "demonic". The prove_correct body is elided from the spec view, so attacks may edit impl AND proof; all 11 files are same_spec=True (checked via swebench_unified.markers.same_spec, backend velvet).

SAME-SPEC CHECK: all atk_*.lean returned True.

### VERIFY (bash scripts/lean_verify.sh <file>):
  atk_1 prepatch-verbatim (result:=a::result)            EXIT=1 (rejected @ clause args[i-1]! = numEval args[i-1]! prec)
  atk_2 return args                                      EXIT=1 (rejected @ args = numEvalSeq prec args)
  atk_3 return []                                        EXIT=1 (rejected @ [] = numEvalSeq + length)
  atk_4 wrong precision numEval a (prec+1)               EXIT=1 (prec genuinely threaded)
  atk_5 reversed/forward-take order (result++[...])      EXIT=1 (order pinned)
  atk_6 double-eval numEval (numEval a prec) prec        EXIT=1 (numEval not idempotent for the spec)
  atk_7 off-by-one (start i=args.length-1, skips last)   EXIT=1 (arity pinned by length + numEvalSeq)
  atk_partial partial-domain (eval only i==1, else pass) EXIT=1 (tail elements unevaluated)
  atk_pos POSITIVE CONTROL return args.map(fun a=>numEval a prec) + matching induction proof  EXIT=0 (spec non-vacuous, structurally different correct impl verifies)
  base_solution EXIT=0 ; Solution_prepatch EXIT=1 (fails at args[i-1]!=numEval args[i-1]! prec = the F2P bug; prepatch_reproduced=True)
The postcondition is a TOTAL functional equation, so no terminating wrong-output impl can verify — the 8 terminating attacks span partial-domain / boundary / control-flow-effect / ungrounded-echo (return-args, return-[]) classes and all reject.

DIVERGENCE CLASS (the ONLY verifying wrong impls) — investigated fully, dismissed with EXECUTED resolve evidence, deliberately NOT listed in `attacks` because they are not admissible counterexamples (see below):
  atk_div.lean : `while args.length+1 > 0 do result:=result; return result`, proof `loom_solve`. same_spec=True, VERIFY EXIT=0 (vacuous: Nat n+1 is never 0, loop never exits, `return` unreachable, postcondition holds vacuously under partial correctness).
  atk_div2.lean: `i:=args.length; while i>0 do result:=result; return result` (i never decremented). same_spec=True, VERIFY EXIT=0 (conditional divergence: terminates only on []).
  ARTIFACT CONFIRMED: atk_div_total.lean (same skeleton, only termination="total") -> EXIT=1 with `declaration uses 'sorry'` (unmet termination obligation). So the verification is purely a partial-correctness vacuity artifact.
  FAITHFUL PATCHES MATERIALIZED + RUN (protocol §2): patch_div.diff / patch_div2.diff replace `*self.args` with a loop that never terminates before splicing into `self._imp_(...)` (an actual infinite-loop mirror of the divergent do-block). Both git-apply cleanly and py_compile OK against base_commit.
    run_resolve('sympy__sympy-12096', patch_div , 300)  => completed=false, resolved=false (no report.json; harness EvaluationError)
    run_resolve('sympy__sympy-12096', patch_div2, 300)  => completed=false, resolved=false (same)
    Direct diagnostic (retained log, 120s test timeout) proved the cause verbatim: `Test runtime: 120.05 seconds` then `swebench.harness.utils.EvaluationError: sympy__sympy-12096: Test timed out after 120 seconds.` i.e. exec_run_with_timeout timed_out=True -> EvaluationError -> NO report.json -> eval_completed=False.
  WHY NOT BROKEN: the operative BROKEN test in construct/build_one.py:_derive_audit_verdict fires ONLY when run_resolve returns completed=True AND not resolved. A hang yields completed=False, which the derivation routes to the `if not r.completed` branch = inconclusive-for-that-attack, explicitly NOT a break. A non-terminating patch is therefore never a mechanical verify⇸correct falsification. Additionally: (a) divergence-vacuity is UNIVERSAL to every partial-correctness velvet bundle (401/500 ship termination="partial"), so counting it would make G-EQ universally unsatisfiable — contradicting the methodology deliberately shipping `partial` as default; (b) a divergent control-flow is not a faithful R/A/I skeleton of the gold's finite comprehension [i.evalf(prec) for i in self.args] (spec_guide directive 3), so it is out of G-EQ scope and would surface as a non-termination/hang, not as a resolving-but-wrong patch. Hence I did not submit atk_div/atk_div2 as `attacks`; including them would force a spurious INCONCLUSIVE on a spec that is in fact sound.

HARNESS POSITIVE CONTROL: gold patch (benchmark-verified/sympy__sympy-12096/patch.diff, the one-liner *self.args -> *[i.evalf(prec) for i in self.args] @ function.py:510) via run_resolve => completed=true, resolved=true. Confirms the image + oracle are healthy, so div/div2 completed=False is a genuine hang, not infra failure.

A-LEG / R-I AUDIT (protocol §3): refinement.md legs A1..A5 are all R / A-consumed / A-reference / I — no kind-3 (the single changed op, per-argument numeric evaluation, is modeled DEEPLY via numEvalSeq/numEval, not hidden behind an axiom about the changed function _eval_evalf). A-legs validated executably in-container:
  G-AX (axiom_check.py, base repo, testbed conda): rc=0 — numEvalSeq deep model == real [i.evalf(prec) for i in args] on 10 boundary + ~3000 fuzz lists across precisions; Expr.evalf total; load-bearing witness f(2).evalf(prec) != f(2) confirmed (A-reference + A-consumed sound).
  G-CONF (conformance_check.py, gold applied): rc=0 — R/I shadow of evaluateArgs fed through unchanged _imp_/Float == real patched _eval_evalf on 15472 inputs (seed 12096), 0 disagreements.
meta.json: axioms = {numEval A-consumed, Term opaque-type, termDefault opaque-sentinel}; deep_model_references = {numEvalSeq A-reference}; additional_change_sites=[]; conf_skip=false — all consistent with the artifacts.

CONCLUSION: SOUND. ≥8 terminating same-spec attacks run, none breaks the spec (all verify-reject); prepatch reproduces the exact discriminating clause; positive control verifies; A-legs correspond to the real callees (G-AX/G-CONF rc=0); the sole verifying wrong-impl class (divergence) has its faithful patch executed and observed to HANG (completed=False = inconclusive), which is not the completed-non-resolve that defines a break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attack: NONE found. Evidence:

(1) SPEC REGION BYTE-IDENTICAL. same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True. spec_view (imports, opaque axioms Term/termDefault/numEval, pure region numEvalSeq + lemmas, method signature `method evaluateArgs (prec:Nat)(args:List Term)` with `ensures out = numEvalSeq prec args` and `ensures out.length = args.length`, empty pre/post) is identical between patched and prepatch bundles; only the elided impl region differs. Spec is genuinely frozen.

(2) SPEC STRONG BUT NOT TOO STRONG. Solution.lean verifies (lean_verify exit 0). Solution_prepatch.lean (verbatim-passthrough `result := a :: result`) FAILS at exactly the discriminating clause: `args[i-1]?.getD default = numEval (args[i-1]?.getD default) prec` — i.e. it fails precisely when an argument's numeric evaluation differs from the argument itself, the bug test_issue_12092 exercises. So the spec discriminates the gold fix from the pre-patch impl on the right operation.

(3) MODEL == REAL CALLEE (no drift). Gold patch changes only ARGS spliced into Float(self._imp_(*ARGS), prec): self.args -> [i.evalf(prec) for i in self.args] (function.py:510). Modeled deeply by numEvalSeq = per-element map of numEval; numEval is OPAQUE (weakest contract, asserts no equational fact about evalf's value), so the postcondition asserts nothing beyond 'apply the real per-argument evaluator in order, preserving length/order' — exactly the real comprehension. Ran axiom_check.py against the REAL BASE REPO (commit d7c3045115, confirmed pre-patch source `return Float(self._imp_(*self.args), prec)`) under Python 3.8: asserts numEvalSeq(prec,args) == [i.evalf(prec) for i in args] over 10 boundary cases + ~3000 randomized fuzz argument lists (seed 12096) across precisions {15,24,53,80,113}; also confirms Expr.evalf total and the load-bearing witness f(2).evalf(prec) != f(2). PASSED, exit 0.

(4) MODELING BOUNDARY LEGITIMATE. _imp_/Float context is byte-unchanged by the patch and identity under refinement, so correctly abstracted out; termDefault is an out-of-range indexing sentinel never observed on in-range loop indexing (0<i<=length). No consumed axiom about the function-under-change.

The modeled function agrees with the real repo callee on every tested input, including the issue's own witness. No diverging input exists. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (projection of Solution.lean; the refinement.md/mapping.md docs are auditor-facing and explicitly excluded from the consumer view) does not leak the gold edit beyond the public problem_statement.

Gold edit: sympy/core/function.py:510, `self._imp_(*self.args)` -> `self._imp_(*[i.evalf(prec) for i in self.args])`.

Public problem_statement already discloses: the bug is in Function._eval_evalf, that it 'isn't calling evalf recursively on the return of _imp_', and the f(g(2)).evalf() witness — so the desired behavior (numerically evaluate the arguments) is public.

Evidence:
- Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor) PASSES: no diff markers, no reproduced gold-patch line, no patched file path/module, no patched-symbol echo in identifiers, no narration keywords.
- Edit-specific tokens absent from spec view: 'evalf'=False, '_imp_'=False, 'self.args'=False, 'function.py'=False, '_eval_evalf'=False, 'Float'=False, 'implemented_function'=False.
- Only 'recursiv' hit is 'Front-recursive', a Lean fold-pattern descriptor, not the problem's 'recursively'.
- The spec models a generic evaluateArgs mapping each argument through an opaque numEval (numeric evaluation to a working precision), order/length preserved — an abstract behavioral restatement of the already-public desired behavior, not the specific gold code or location. The `prec` parameter is inherent to the modeled callee's API, not an edit-locus disclosure.
- same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True: the spec region is byte-identical pre/post, so no discriminator leaks through a differing spec.

Conclusion: the spec view reveals nothing about the gold edit's location, symbols, or exact expression beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.