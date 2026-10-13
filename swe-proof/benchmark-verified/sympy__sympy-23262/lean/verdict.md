# P2 adversarial audit — sympy__sympy-23262

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
       "[" ++ String.intercalate ", " parts ++ "]"
   | .tuple xs =>
       let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+      "(" ++ String.intercalate ", " parts ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,10 @@
   | .leaf s   => s
   | .list xs  =>
       let parts := xs.map implementation_renderArg
-      "[" ++ String.intercalate ", " parts ++ "]"
+      "(" ++ String.intercalate ", " parts ++ ",)"
   | .tuple xs =>
       let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+      "[" ++ String.intercalate ", " parts ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,8 +45,11 @@
       let parts := xs.map implementation_renderArg
       "[" ++ String.intercalate ", " parts ++ "]"
   | .tuple xs =>
-      let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+      match xs with
+      | [] => "()"
+      | _ =>
+        let parts := xs.map implementation_renderArg
+        "(" ++ String.intercalate ", " parts ++ ",)"
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
   | .leaf s   => s
   | .list xs  =>
       let parts := xs.map implementation_renderArg
-      "[" ++ String.intercalate ", " parts ++ "]"
+      "[" ++ String.intercalate "," parts ++ "]"
   | .tuple xs =>
       let parts := xs.map implementation_renderArg
       "(" ++ String.intercalate ", " parts ++ ",)"
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,14 +39,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderArg : Arg → String
-  | .leaf s   => s
-  | .list xs  =>
-      let parts := xs.map implementation_renderArg
-      "[" ++ String.intercalate ", " parts ++ "]"
-  | .tuple xs =>
-      let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+def implementation_renderArg : Arg → String := specRender
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 
 -- impl-start
 def implementation_renderArg : Arg → String
-  | .leaf s   => s
+  | .leaf s   => "\"" ++ s ++ "\""
   | .list xs  =>
       let parts := xs.map implementation_renderArg
       "[" ++ String.intercalate ", " parts ++ "]"
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,14 +39,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderArg : Arg → String
-  | .leaf s   => s
-  | .list xs  =>
-      let parts := xs.map implementation_renderArg
-      "[" ++ String.intercalate ", " parts ++ "]"
-  | .tuple xs =>
-      let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+def implementation_renderArg : Arg → String := fun _ => ""
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
       "[" ++ String.intercalate ", " parts ++ "]"
   | .tuple xs =>
       let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+      String.intercalate ", " parts
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -42,11 +42,9 @@
 def implementation_renderArg : Arg → String
   | .leaf s   => s
   | .list xs  =>
-      let parts := xs.map implementation_renderArg
-      "[" ++ String.intercalate ", " parts ++ "]"
+      "[" ++ String.intercalate ", " (xs.map implementation_renderArg) ++ "]"
   | .tuple xs =>
-      let parts := xs.map implementation_renderArg
-      "(" ++ String.intercalate ", " parts ++ ",)"
+      "(" ++ String.intercalate ", " (xs.map implementation_renderArg) ++ ",)"
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee is consumed by the proof. Leaf rendering (the per-element
-- printed source string) is refined to the leaf's own string value (type-only
-- refinement, see refinement.md / mapping.md), so no `opaque` callee or
-- `_prop` axiom is required.
-- axioms-end

-- pure-start
/-- A nested argument structure: a printed leaf, a list node, or a tuple node.
This mirrors the recursive shape consumed when rendering a nested container of
already-printed elements to its source-string form. -/
inductive Arg where
  | leaf  : String → Arg
  | list  : List Arg → Arg
  | tuple : List Arg → Arg
deriving Repr

/-- Front-recursive reference rendering of a nested argument structure to its
source string. A leaf renders to its own string. A list node renders as its
elements, comma-and-space separated, wrapped in square brackets. A tuple node
renders the same way but wrapped in parentheses **with a trailing comma before
the closing parenthesis**, so that the rendering of every tuple — including a
one-element tuple — is unambiguously a tuple rather than a parenthesised value. -/
def specRender : Arg → String
  | .leaf s   => s
  | .list xs  => "[" ++ String.intercalate ", " (xs.map specRender) ++ "]"
  | .tuple xs => "(" ++ String.intercalate ", " (xs.map specRender) ++ ",)"
-- pure-end

-- post-conditions-start
/-- The rendered string is exactly the source rendering of the argument
structure: leaves verbatim, list nodes bracketed, and tuple nodes parenthesised
with a trailing comma so a singleton tuple stays a tuple. -/
def problem_spec_renderArg (arg : Arg) (result : String) : Prop :=
  result = specRender arg
-- post-conditions-end

-- impl-start
def implementation_renderArg : Arg → String
  | .leaf s   => s
  | .list xs  =>
      let parts := xs.map implementation_renderArg
      "[" ++ String.intercalate ", " parts ++ "]"
  | .tuple xs =>
      let parts := xs.map implementation_renderArg
      "(" ++ String.intercalate ", " parts ++ ",)"
-- impl-end

-- proof-start
theorem correct_renderArg : ∀ arg : Arg,
    problem_spec_renderArg arg (implementation_renderArg arg)
  | .leaf s => by simp only [problem_spec_renderArg, implementation_renderArg, specRender]
  | .list xs => by
      simp only [problem_spec_renderArg, implementation_renderArg, specRender]
      have : xs.map implementation_renderArg = xs.map specRender :=
        List.map_congr_left (fun a _ => correct_renderArg a)
      rw [this]
  | .tuple xs => by
      simp only [problem_spec_renderArg, implementation_renderArg, specRender]
      have : xs.map implementation_renderArg = xs.map specRender :=
        List.map_congr_left (fun a _ => correct_renderArg a)
      rw [this]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition problem_spec_renderArg is a TOTAL FUNCTIONAL EQUALITY (result = specRender arg) against a fully-defined structural-recursion reference specRender. Any behaviorally-distinct impl therefore cannot close the proof; only impls extensionally equal to specRender verify.

SAME-SPEC: all 9 attacks + pos_control verified byte-identical spec via swebench_unified.markers.same_spec => True (axioms/pure/pre/post regions untouched).

 Verify cmd: `bash scripts/lean_verify.sh <file>`. Ran attack verifications concurrently in 3 background batches (<=4 each).

### WRONG IMPLS (all FAIL to verify, exit 1 'unsolved goals'/'No goals'):
- atk_1 (prepatch bug: tuple closes with ')' no trailing comma) exit=1 @ proof line — the exact F2P bug; prepatch_reproduced=true.
- atk_2 (control-flow: list<->tuple delimiter swap) exit=1.
- atk_3 (partial-domain: empty tuple special-cased to '()' , non-empty correct) exit=1 (fails on []).
- atk_4 (boundary: separator ',' instead of ', ') exit=1.
- atk_5 (ungrounded-oracle echo: impl := specRender directly) exit=1 (proof 'No goals to be solved' — even the literal oracle body does NOT trivially close the gold structural proof, and same_spec still True; not exploitable).
- atk_6 (control-flow-effect on leaf: wraps leaf in quotes) exit=1.
- atk_7 (ungrounded constant: fun _ => "") exit=1.
- atk_8 (control-flow: tuple emits bare join, no parens) exit=1.

### Verifying impl
- pos_control (gold Solution.lean) exit=0; #print axioms correct_renderArg => [propext, Classical.choice, Quot.sound] (clean, standard Mathlib; no sorryAx/custom).
- atk_echo (gold behavior, alternate inline map formulation) exit=0; clean axioms [propext, Classical.choice, Quot.sound]. Behaviorally identical to specRender => its FAITHFUL refined patch is the gold patch.

MANDATORY RESOLVE RUN (echo is the only clean-axiom verifying non-gold-source impl): materialized atk_echo_patch.diff (= gold patch, since echo == specRender behavior) and ran through OFFICIAL harness run_resolve('sympy__sympy-23262', patch). RESULT: completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Report: resolved=true, FAIL_TO_PASS test_issue_14941 success, all PASS_TO_PASS success. (First wrapper call returned a transient 'no report' image-warmup error; manual inner harness invocation AND a second run_resolve wrapper call both RESOLVED — executed, not speculated.) No verifying same-spec impl has a non-resolving patch => verify NOT weaker than correct on the tested axis.

REFINEMENT.MD AUDIT: 6 legs, all R or I (rows 1-2 R type-refinement, rows 3-6 I identical concrete op). NO A-consumed, NO A-reference, NO kind-3 legs. doprint legitimately refined away as type-only R (each leaf refined to its already-printed string Arg.leaf s); it is neither applied in the impl nor consumed as an axiom => axiom_check.py skip stub is correct and #print axioms shows no custom axiom. No A-leg callee correspondence to audit. R/I legs mechanically covered by G-CONF (Python shadow differential test, seed 23262, >=1e5 nested trees).

CONCLUSION: >=5 distinct wrong impls attempted (8 wrong + echo); every wrong impl fails to verify; the single clean-axiom verifying non-source impl (echo) has a materialized faithful patch that RESOLVES under the official harness. No falsification found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee is consumed by the proof. Leaf rendering (the per-element
-- printed source string) is refined to the leaf's own string value (type-only
-- refinement, see refinement.md / mapping.md), so no `opaque` callee or
-- `_prop` axiom is required.
-- axioms-end

-- pure-start
/-- A nested argument structure: a printed leaf, a list node, or a tuple node.
This mirrors the recursive shape consumed when rendering a nested container of
already-printed elements to its source-string form. -/
inductive Arg where
  | leaf  : String → Arg
  | list  : List Arg → Arg
  | tuple : List Arg → Arg
deriving Repr

/-- Front-recursive reference rendering of a nested argument structure to its
source string. A leaf renders to its own string. A list node renders as its
elements, comma-and-space separated, wrapped in square brackets. A tuple node
renders the same way but wrapped in parentheses **with a trailing comma before
the closing parenthesis**, so that the rendering of every tuple — including a
one-element tuple — is unambiguously a tuple rather than a parenthesised value. -/
def specRender : Arg → String
  | .leaf s   => s
  | .list xs  => "[" ++ String.intercalate ", " (xs.map specRender) ++ "]"
  | .tuple xs => "(" ++ String.intercalate ", " (xs.map specRender) ++ ",)"
-- pure-end

-- post-conditions-start
/-- The rendered string is exactly the source rendering of the argument
structure: leaves verbatim, list nodes bracketed, and tuple nodes parenthesised
with a trailing comma so a singleton tuple stays a tuple. -/
def problem_spec_renderArg (arg : Arg) (result : String) : Prop :=
  result = specRender arg
-- post-conditions-end

-- impl-start
def implementation_renderArg : Arg → String
  | .leaf s   => s
  | .list xs  =>
      let parts := xs.map implementation_renderArg
      "[" ++ String.intercalate ", " parts ++ "]"
  | .tuple xs =>
      let parts := xs.map implementation_renderArg
      "(" ++ String.intercalate ", " parts ++ ",)"
-- impl-end

-- proof-start
theorem correct_renderArg : ∀ arg : Arg,
    problem_spec_renderArg arg (implementation_renderArg arg)
  | .leaf s => by simp only [problem_spec_renderArg, implementation_renderArg, specRender]
  | .list xs => by
      simp only [problem_spec_renderArg, implementation_renderArg, specRender]
      have : xs.map implementation_renderArg = xs.map specRender :=
        List.map_congr_left (fun a _ => correct_renderArg a)
      rw [this]
  | .tuple xs => by
      simp only [problem_spec_renderArg, implementation_renderArg, specRender]
      have : xs.map implementation_renderArg = xs.map specRender :=
        List.map_congr_left (fun a _ => correct_renderArg a)
      rw [this]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition problem_spec_renderArg is a TOTAL FUNCTIONAL EQUALITY (result = specRender arg) against a fully-defined structural-recursion reference specRender. Any behaviorally-distinct impl therefore cannot close the proof; only impls extensionally equal to specRender verify.

SAME-SPEC: all 9 attacks + pos_control verified byte-identical spec via swebench_unified.markers.same_spec => True (axioms/pure/pre/post regions untouched).

 Verify cmd: `bash scripts/lean_verify.sh <file>`. Ran attack verifications concurrently in 3 background batches (<=4 each).

### WRONG IMPLS (all FAIL to verify, exit 1 'unsolved goals'/'No goals'):
- atk_1 (prepatch bug: tuple closes with ')' no trailing comma) exit=1 @ proof line — the exact F2P bug; prepatch_reproduced=true.
- atk_2 (control-flow: list<->tuple delimiter swap) exit=1.
- atk_3 (partial-domain: empty tuple special-cased to '()' , non-empty correct) exit=1 (fails on []).
- atk_4 (boundary: separator ',' instead of ', ') exit=1.
- atk_5 (ungrounded-oracle echo: impl := specRender directly) exit=1 (proof 'No goals to be solved' — even the literal oracle body does NOT trivially close the gold structural proof, and same_spec still True; not exploitable).
- atk_6 (control-flow-effect on leaf: wraps leaf in quotes) exit=1.
- atk_7 (ungrounded constant: fun _ => "") exit=1.
- atk_8 (control-flow: tuple emits bare join, no parens) exit=1.

### Verifying impl
- pos_control (gold Solution.lean) exit=0; #print axioms correct_renderArg => [propext, Classical.choice, Quot.sound] (clean, standard Mathlib; no sorryAx/custom).
- atk_echo (gold behavior, alternate inline map formulation) exit=0; clean axioms [propext, Classical.choice, Quot.sound]. Behaviorally identical to specRender => its FAITHFUL refined patch is the gold patch.

MANDATORY RESOLVE RUN (echo is the only clean-axiom verifying non-gold-source impl): materialized atk_echo_patch.diff (= gold patch, since echo == specRender behavior) and ran through OFFICIAL harness run_resolve('sympy__sympy-23262', patch). RESULT: completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Report: resolved=true, FAIL_TO_PASS test_issue_14941 success, all PASS_TO_PASS success. (First wrapper call returned a transient 'no report' image-warmup error; manual inner harness invocation AND a second run_resolve wrapper call both RESOLVED — executed, not speculated.) No verifying same-spec impl has a non-resolving patch => verify NOT weaker than correct on the tested axis.

REFINEMENT.MD AUDIT: 6 legs, all R or I (rows 1-2 R type-refinement, rows 3-6 I identical concrete op). NO A-consumed, NO A-reference, NO kind-3 legs. doprint legitimately refined away as type-only R (each leaf refined to its already-printed string Arg.leaf s); it is neither applied in the impl nor consumed as an axiom => axiom_check.py skip stub is correct and #print axioms shows no custom axiom. No A-leg callee correspondence to audit. R/I legs mechanically covered by G-CONF (Python shadow differential test, seed 23262, >=1e5 nested trees).

CONCLUSION: >=5 distinct wrong impls attempted (8 wrong + echo); every wrong impl fails to verify; the single clean-axiom verifying non-source impl (echo) has a materialized faithful patch that RESOLVES under the official harness. No falsification found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled fn: _recursive_to_string(doprint, arg) at sympy/utilities/lambdify.py:948-967, gold patch tuple branch left,right="(",",)" (patch_equals_gold=True; base fdc707f73a). Verified against real base-commit source.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean, lean_backend)=True — the spec view (axioms/pure/post-conditions: inductive Arg + specRender + problem_spec_renderArg) is byte-identical across pre/post-patch variants; only impl+proof differ (trailing-comma fix). Spec region is intact.

Lean: compiles (exit 0, no sorry). #print axioms correct_renderArg => [propext, Classical.choice, Quot.sound] — clean, no sorryAx; proof is genuine (structural induction via List.map_congr_left).

Faithfulness differential test vs a faithful standalone reproduction of the PATCHED _recursive_to_string over the modeled domain (list/tuple/str leaves):
 - 200,010 fuzzed nested trees (a-z + empty leaves): 0 disagreements
 - 300,000 adversarial trees with leaves containing ',', '()', '[]', spaces: 0 disagreements
 - Boundary cases all match incl. F2P ('1',)->'(1,)', empty tuple ()->'(,)' (the real patched fn genuinely emits '(,)' for the empty tuple; the spec reproduces this exactly rather than a cleaner/stronger variant), empty list []->'[]', nested singleton tuples, list-containing-tuple.

doprint refinement is sound: the real fn's isinstance(arg,str): return arg branch is identity, exactly what Arg.leaf s models; the modeled Lean domain contains no input mapping to Basic/set/generator that would exercise unmodeled leaf behavior. No input in the modeled domain diverges from the real patched callee. The spec (specRender) is the exact behavior of the patched function, not too strong and not drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for sympy__sympy-23262 (lean).

PUBLIC BASELINE: the problem_statement already fully discloses the observable fix. It shows SymPy 1.10 emitting (1) for a one-element tuple, gives the expected (1,), and explicitly diagnoses 'the missing comma after 1 that causes an integer to be returned instead of a tuple.' So 'tuples must render with a trailing comma so a singleton stays a tuple' is public knowledge, NOT a leak.

SPEC VIEW (verified via markers.spec_view over Solution.lean): contains only Arg inductive, specRender, and problem_spec_renderArg. The tuple branch specRender '(' ++ intercalate ', ' ++ ',)' plus its docstring ('trailing comma before the closing parenthesis, so … a one-element tuple … is unambiguously a tuple') encode exactly the behavior the public problem_statement demands and nothing beyond it. The impl and proof regions are elided in the projection ('implementation elided' / 'proof elided'), so the modeled behavior is stated declaratively without exposing the concrete gold edit.

GOLD-EDIT MECHANICS ARE ABSENT FROM THE SPEC VIEW: the actual patch specifics (left,right = '(',',)'; the '()' sequence-unpack bug; _recursive_to_string; lambdify.py:961) appear only in mapping.md/refinement.md, which are NOT part of the spec view and NOT in scope for the leak screen. The list branch in the spec view is unchanged-behavior context (list already rendered correctly pre-patch), not the discriminating edit.

### Mechanical corroboration
- leakage.screen(Solution.lean, lean, gold_patch, problem_statement) -> passed=True, hard_failures=[] (lexical screen clean).
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True: the spec region (post-conditions/pure/axioms) is byte-identical between the buggy prepatch variant and the fixed variant, i.e. the spec does not itself carry the discriminator distinguishing gold vs buggy impl — the tuple ',)' lives in the impl/specRender leg which is projected declaratively but the region hash confirms spec parity across variants.

CONCLUSION: the spec view reveals only what the public problem_statement already states (singleton tuple must close with a trailing comma). No gold-patch mechanic, no problem-statement phrasing beyond the public content, and no reconstruction of the concrete edit is exposed. G-LEAK not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag needed). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
