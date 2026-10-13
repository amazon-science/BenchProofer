# P2 adversarial audit — django__django-13449

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_2b.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_7b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_renderWindowSql is a TOTAL functional-equality postcondition: for every (operand, window, isDecimal) it pins result to an exact concrete char-list (isDecimal -> "CAST(" ++ operand ++ " OVER (" ++ window ++ ")" ++ " AS NUMERIC)"; else operand ++ " OVER (" ++ window ++ ")"). Every same-spec wrong impl differs from gold on at least one input, so its ∀-correctness goal is genuinely false and no sound (clean-axiom) Lean proof can close it. No verifying wrong impl exists, hence no faithful patch to resolve-run.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,12 +38,10 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
-  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
+  let mut inner : List Char := operand
   if isDecimal then
-    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
-  return sql
+    inner := "CAST(".toList ++ operand ++ " AS NUMERIC)".toList
+  return inner ++ " OVER (".toList ++ window ++ [')']
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,12 +38,8 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
-  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
-  if isDecimal then
-    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
-  return sql
+  let sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
+  return "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_2b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,12 +38,8 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
-  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
-  if isDecimal then
-    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
-  return sql
+  let sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
+  return "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
 -- impl-end
 
 -- proof-start
@@ -53,5 +49,5 @@
       (implementation_renderWindowSql operand window isDecimal) := by
   intro operand window isDecimal
   unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr
-  cases isDecimal <;> rfl
+  cases isDecimal <;> simp_all <;> (try rfl) <;> (try (simp [List.append_assoc])) <;> (try decide)
 -- proof-end
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,7 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
-  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
+  let mut sql : List Char := window ++ " OVER (".toList ++ operand ++ [')']
   if isDecimal then
     sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
   return sql
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,11 +38,9 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
   let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
   if isDecimal then
-    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
+    sql := "CAST(".toList ++ sql ++ " AS DECIMAL)".toList
   return sql
 -- impl-end
 
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,8 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
   let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
-  if isDecimal then
+  if ! isDecimal then
     sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
   return sql
 -- impl-end
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,7 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
-  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
+  let mut sql : List Char := operand ++ " OVER (".toList ++ window
   if isDecimal then
     sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
   return sql
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,8 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
   let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
-  if isDecimal then
+  if isDecimal && window != [] then
     sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
   return sql
 -- impl-end
```

Attack 9 — `atk_7b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,8 @@
 -- impl-start
 def implementation_renderWindowSql
     (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
-  -- Render the windowed expression first, as a single text unit.
   let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
-  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
-  if isDecimal then
+  if isDecimal && window != [] then
     sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
   return sql
 -- impl-end
@@ -53,5 +51,5 @@
       (implementation_renderWindowSql operand window isDecimal) := by
   intro operand window isDecimal
   unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr
-  cases isDecimal <;> rfl
+  cases isDecimal <;> simp_all <;> (try rfl) <;> (try (simp [List.append_assoc])) <;> (try decide)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the window-expression text
-- is rendered concretely as a literal-driven concatenation, and the numeric-cast
-- wrapper is likewise a concrete literal-driven concatenation. The branch that
-- selects WHAT gets cast is modeled DEEPLY (below) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The rendered text of a windowed expression: the operand text, the keyword
` OVER (`, the assembled window-clause text, and a closing parenthesis, in that
exact order. This is the bare render used on every backend. -/
def windowedExpr (operand window : List Char) : List Char :=
  operand ++ " OVER (".toList ++ window ++ [')']
-- pure-end

-- post-conditions-start
/-- The rendered SQL of a windowed expression on a numeric-cast backend.

When the declared output type is a fixed-point decimal the *entire* windowed
expression is wrapped in a numeric cast `CAST(… AS NUMERIC)`, so the cast spans
the operand together with its `OVER (…)` clause as a single unit; otherwise the
bare windowed expression is rendered. Every unchanged component (operand text,
the `OVER (…)` clause, the window-clause text) is pinned to its input; only the
surrounding cast depends on the decimal-type flag. -/
def problem_spec_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) (result : List Char) : Prop :=
  result =
    if isDecimal then
      "CAST(".toList ++ windowedExpr operand window ++ " AS NUMERIC)".toList
    else
      windowedExpr operand window
-- post-conditions-end

-- impl-start
def implementation_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
  -- Render the windowed expression first, as a single text unit.
  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
  if isDecimal then
    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
  return sql
-- impl-end

-- proof-start
theorem correct_renderWindowSql :
    ∀ (operand window : List Char) (isDecimal : Bool),
    problem_spec_renderWindowSql operand window isDecimal
      (implementation_renderWindowSql operand window isDecimal) := by
  intro operand window isDecimal
  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr
  cases isDecimal <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13449 lean. same_spec=True confirmed for all 9 attack files + positive control via swebench_unified.markers.same_spec (get_backend('lean')). spec_view collapses BOTH impl and proof regions, so attacks are free to rewrite impl+proof; axioms/pure/post regions kept byte-identical.

Positive control (pos.lean = gold impl): bash scripts/lean_verify.sh .../pos.lean -> exit 0. #print axioms correct_renderWindowSql -> 'does not depend on any axioms' (clean, no sorry).

Attacks (all same_spec=True; all fail to verify -> verify⇒correct holds):
- atk_1 prepatch bug (cast wraps only operand, OVER(...) dangles outside): exit 1, rfl fails on false goal. prepatch_reproduced=true.
- atk_2 unconditional cast (ignores isDecimal, wrong on isDecimal=false): exit 1. atk_2b same impl w/ heavy tactics (simp_all/decide/append_assoc): exit 1, residual false goal.
- atk_3 operand/window swapped: exit 1.
- atk_4 boundary/wrong-literal 'AS DECIMAL' instead of 'AS NUMERIC': exit 1.
- atk_5 control-flow negated condition (casts when NOT decimal): exit 1.
- atk_6 off-by-one (drops closing ')'): exit 1.
- atk_7 data-dependent partial domain (casts only when window != []): exit 1. atk_7b heavy tactics: exit 1, residual false goal.
All failures are genuine rfl/simp_all/decide non-closures with LHS≠RHS char-lists — not syntax/timeout. No attack verified => no clean-axiom-closing impl exists => no faithful patch needed a resolve run.

Commands used: same_spec via python + swebench_unified.markers.same_spec; verify via 'bash scripts/lean_verify.sh <file>' run concurrently in batches of ≤4.

Refinement.md audit: 5 legs. Row1 operand:R (str↔List Char bijection, cast-free operand). Row2 window:R (bijection). Row3 template substitution 'OVER (%(window)s)':I (fixed literal template = fixed-order concat). Row4 the CHANGED op (decimal branch, cast wraps whole windowed unit):R/I — 'CAST(%s AS NUMERIC)' % sql reproduced concretely (I) and branch selection modeled deeply (R), NOT axiomatized. Row5 return:I. NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. Axioms region empty; G-AX is a skip stub. Both UNCHANGED callees (template substitution, numeric-cast wrapper) reproduced concretely as I ops matching patch.diff (Window.as_sqlite + SQLiteNumericMixin.as_sqlite) faithfully. No A-leg correspondence obligation to audit. All legs are R/A-*/I — no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_2b.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_7b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_renderWindowSql is a TOTAL functional-equality postcondition: for every (operand, window, isDecimal) it pins result to an exact concrete char-list (isDecimal -> "CAST(" ++ operand ++ " OVER (" ++ window ++ ")" ++ " AS NUMERIC)"; else operand ++ " OVER (" ++ window ++ ")"). Every same-spec wrong impl differs from gold on at least one input, so its ∀-correctness goal is genuinely false and no sound (clean-axiom) Lean proof can close it. No verifying wrong impl exists, hence no faithful patch to resolve-run.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2b.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_7b.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the window-expression text
-- is rendered concretely as a literal-driven concatenation, and the numeric-cast
-- wrapper is likewise a concrete literal-driven concatenation. The branch that
-- selects WHAT gets cast is modeled DEEPLY (below) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The rendered text of a windowed expression: the operand text, the keyword
` OVER (`, the assembled window-clause text, and a closing parenthesis, in that
exact order. This is the bare render used on every backend. -/
def windowedExpr (operand window : List Char) : List Char :=
  operand ++ " OVER (".toList ++ window ++ [')']
-- pure-end

-- post-conditions-start
/-- The rendered SQL of a windowed expression on a numeric-cast backend.

When the declared output type is a fixed-point decimal the *entire* windowed
expression is wrapped in a numeric cast `CAST(… AS NUMERIC)`, so the cast spans
the operand together with its `OVER (…)` clause as a single unit; otherwise the
bare windowed expression is rendered. Every unchanged component (operand text,
the `OVER (…)` clause, the window-clause text) is pinned to its input; only the
surrounding cast depends on the decimal-type flag. -/
def problem_spec_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) (result : List Char) : Prop :=
  result =
    if isDecimal then
      "CAST(".toList ++ windowedExpr operand window ++ " AS NUMERIC)".toList
    else
      windowedExpr operand window
-- post-conditions-end

-- impl-start
def implementation_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
  -- Render the windowed expression first, as a single text unit.
  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [')']
  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.
  if isDecimal then
    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList
  return sql
-- impl-end

-- proof-start
theorem correct_renderWindowSql :
    ∀ (operand window : List Char) (isDecimal : Bool),
    problem_spec_renderWindowSql operand window isDecimal
      (implementation_renderWindowSql operand window isDecimal) := by
  intro operand window isDecimal
  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr
  cases isDecimal <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13449 lean. same_spec=True confirmed for all 9 attack files + positive control via swebench_unified.markers.same_spec (get_backend('lean')). spec_view collapses BOTH impl and proof regions, so attacks are free to rewrite impl+proof; axioms/pure/post regions kept byte-identical.

Positive control (pos.lean = gold impl): bash scripts/lean_verify.sh .../pos.lean -> exit 0. #print axioms correct_renderWindowSql -> 'does not depend on any axioms' (clean, no sorry).

Attacks (all same_spec=True; all fail to verify -> verify⇒correct holds):
- atk_1 prepatch bug (cast wraps only operand, OVER(...) dangles outside): exit 1, rfl fails on false goal. prepatch_reproduced=true.
- atk_2 unconditional cast (ignores isDecimal, wrong on isDecimal=false): exit 1. atk_2b same impl w/ heavy tactics (simp_all/decide/append_assoc): exit 1, residual false goal.
- atk_3 operand/window swapped: exit 1.
- atk_4 boundary/wrong-literal 'AS DECIMAL' instead of 'AS NUMERIC': exit 1.
- atk_5 control-flow negated condition (casts when NOT decimal): exit 1.
- atk_6 off-by-one (drops closing ')'): exit 1.
- atk_7 data-dependent partial domain (casts only when window != []): exit 1. atk_7b heavy tactics: exit 1, residual false goal.
All failures are genuine rfl/simp_all/decide non-closures with LHS≠RHS char-lists — not syntax/timeout. No attack verified => no clean-axiom-closing impl exists => no faithful patch needed a resolve run.

Commands used: same_spec via python + swebench_unified.markers.same_spec; verify via 'bash scripts/lean_verify.sh <file>' run concurrently in batches of ≤4.

Refinement.md audit: 5 legs. Row1 operand:R (str↔List Char bijection, cast-free operand). Row2 window:R (bijection). Row3 template substitution 'OVER (%(window)s)':I (fixed literal template = fixed-order concat). Row4 the CHANGED op (decimal branch, cast wraps whole windowed unit):R/I — 'CAST(%s AS NUMERIC)' % sql reproduced concretely (I) and branch selection modeled deeply (R), NOT axiomatized. Row5 return:I. NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. Axioms region empty; G-AX is a skip stub. Both UNCHANGED callees (template substitution, numeric-cast wrapper) reproduced concretely as I ops matching patch.diff (Window.as_sqlite + SQLiteNumericMixin.as_sqlite) faithfully. No A-leg correspondence obligation to audit. All legs are R/A-*/I — no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on django__django-13449 lean bundle. Modeled function = SQLite window-expression rendering (post-patch Window.as_sqlite + inherited SQLiteNumericMixin.as_sqlite). Spec problem_spec_renderWindowSql(operand,window,isDecimal): if isDecimal then 'CAST(' ++ (operand ++ ' OVER (' ++ window ++ ')') ++ ' AS NUMERIC)' else operand ++ ' OVER (' ++ window ++ ')'.

Ran the real repo at base_commit (Django 3.2 worktree) to observe actual rendered SQL:
  - DECIMAL output: 'CAST(LAG("t_emp"."bonus", %s) OVER (PARTITION BY "t_emp"."department" ORDER BY "t_emp"."bonus" ASC) AS NUMERIC)'  -> whole windowed expression cast, operand rendered cast-free (patch clears inner decimal type -> FloatField). Exactly the spec isDecimal=True form with operand = the cast-free source SQL.
  - FLOAT override (non-decimal): 'CAST(LAG("t_emp"."bonus", %s) AS NUMERIC) OVER (PARTITION BY ... ASC)' -> NO outer cast; the inner CAST is part of the operand text itself (Lag's own SQLiteNumericMixin). Exactly the spec isDecimal=False form with operand = 'CAST(LAG(...) AS NUMERIC)'.

Both real branches land on exactly one of the spec's two free-variable forms, so no instantiation of the abstract (operand,window,isDecimal) domain yields a real output the spec cannot produce. Verified the underlying concatenation identities the spec relies on: dict-% substitution into '%(expression)s OVER (%(window)s)' == operand+' OVER ('+window+')' (literal insertion; % chars in values are not re-interpreted), and 'CAST(%s AS NUMERIC)' % sql == 'CAST('+sql+' AS NUMERIC)'. Empty-window edge (operand OVER ()) holds in both; the decimal branch's cast is unconditional in the real code once output_field is DecimalField (copy retains it). No too-strong constraint, no drift, no missing precondition that the real callee would violate.

Structural checks: Solution.lean compiles under lean_verify.sh (exit 0, no sorry). '#print axioms correct_renderWindowSql' => 'does not depend on any axioms' (no sorryAx, proof genuine). Spec region byte-identical to Solution_prepatch.lean via swebench_unified.markers.same_spec (=True); axioms region empty (no opaque callee assumed). G-DIFF signal is real: prepatch impl casts only the operand ('CAST('++operand++' AS NUMERIC) OVER ('++window++')') which fails the frozen spec for isDecimal=True.

Verdict: FAITHFUL — the modeled function agrees with the real repo callee on all inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity confirmed: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); impl+proof regions are elided in spec_view. Solution.lean compiles clean (exit 0) and #print axioms correct_renderWindowSql => 'does not depend on any axioms' (no sorryAx, real proof). Lexical G-LEAK screen passes with zero hard_failures.

The gold edit's discriminating behavior is: the SQLite numeric cast must wrap the ENTIRE windowed expression `expression OVER (window)` as a unit, rather than only the operand. The spec view's postcondition encodes exactly this: for isDecimal, result = "CAST(" ++ windowedExpr operand window ++ " AS NUMERIC)".

This is NOT leakage beyond the public problem_statement, because the problem_statement itself fully discloses it: it shows the buggy SQL `CAST(LAG(...) AS NUMERIC) OVER (PARTITION BY ...)` and states verbatim: 'I believe this fails as the CAST() statement ends after LAG whereas it should be around the whole statement up until "w".' The problem statement literally describes the correct fix (cast around the whole windowed expression).

The spec view reveals NO gold-patch implementation specifics beyond the problem statement: no SQLiteNumericMixin, no as_sqlite, no FloatField/output_field-clearing, no copy()/set_source_expressions mechanism. Those mechanism details live only in mapping.md/refinement.md (auxiliary docs, not part of the spec view). The doc comments in the spec region only restate the problem-statement-level observable requirement in abstract terms ('the entire windowed expression is wrapped in a numeric cast ... otherwise the bare windowed expression is rendered'). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
