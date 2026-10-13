# P2 adversarial audit — django__django-13449

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The postcondition `ensures out = windowSql isDecimal innerBase win` is exact functional equality, and the `pure` region fully defining windowSql/numericCast/overClause passes through the spec view byte-identically (only impl/proof regions elide). Any verifying impl must be extensionally equal to the gold model on both arms. All 6 distinct wrong impls fail verification; the only verifying non-control candidate (atk_7) is an echo of windowSql whose faithful patch IS the gold patch, which resolves.
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -75,10 +75,8 @@
     -- impl-start
     let mut out : List Char := []
     if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
+      let castInner := numericCast innerBase
+      out := overClause castInner win
     else
       out := overClause innerBase win
     return out
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -74,13 +74,7 @@
   do
     -- impl-start
     let mut out : List Char := []
-    if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
-    else
-      out := overClause innerBase win
+    out := overClause innerBase win
     return out
     -- impl-end
 
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -75,12 +75,9 @@
     -- impl-start
     let mut out : List Char := []
     if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
+      out := overClause innerBase win
     else
-      out := overClause innerBase win
+      out := numericCast (overClause innerBase win)
     return out
     -- impl-end
 
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -74,13 +74,7 @@
   do
     -- impl-start
     let mut out : List Char := []
-    if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
-    else
-      out := overClause innerBase win
+    out := numericCast (overClause innerBase win)
     return out
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -75,12 +75,9 @@
     -- impl-start
     let mut out : List Char := []
     if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
+      out := numericCast (overClause innerBase win)
     else
-      out := overClause innerBase win
+      out := innerBase ++ win
     return out
     -- impl-end
 
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -75,10 +75,7 @@
     -- impl-start
     let mut out : List Char := []
     if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
+      out := numericCast (overClause win innerBase)
     else
       out := overClause innerBase win
     return out
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -74,13 +74,7 @@
   do
     -- impl-start
     let mut out : List Char := []
-    if isDecimal then
-      -- The operand carries no inner cast; the OVER template is assembled first,
-      -- and the numeric cast wraps the whole windowed expression.
-      let windowed := overClause innerBase win
-      out := numericCast windowed
-    else
-      out := overClause innerBase win
+    out := windowSql isDecimal innerBase win
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure string-assembly decision over three abstracted inputs: whether the
   windowed expression's result type is a fixed-precision decimal, the SQL of the
   operand the window is computed over, and the already-assembled window clause.
   The two string operations involved — the numeric cast wrapper and the OVER
   template — are unchanged, shared rendering steps, transliterated directly; no
   foreign callee's behaviour is assumed (no consumed axiom, no deep-model
   reference). -/
-- axioms-end

-- pure-start
/- The numeric cast wrapper: a SQL fragment is wrapped so its value is coerced to
   a numeric type. (Concrete unchanged string operation; refinement.md §A.) -/
def numericCast (sql : List Char) : List Char :=
  "CAST(".toList ++ sql ++ " AS NUMERIC)".toList

/- The windowing template: an operand SQL fragment placed in front of its
   parenthesised window clause via the OVER keyword. (Concrete unchanged string
   template `expression OVER (window)`; refinement.md §A.) -/
def overClause (expr win : List Char) : List Char :=
  expr ++ " OVER (".toList ++ win ++ ")".toList

/- The SQL rendered for a windowed expression on a backend whose decimal results
   must be coerced with a numeric cast.

   * When the result type is a fixed-precision decimal, the numeric cast wraps
     the ENTIRE windowed expression — the operand together with its OVER clause —
     and the operand itself carries no inner cast. (The cast must be around the
     whole expression; a cast around the operand alone would split the OVER
     syntax.)
   * Otherwise the expression is rendered as the plain OVER template with no cast.

   This is the deep model of the rendering (refinement.md §A; mapping.md §2). -/
def windowSql (isDecimal : Bool) (innerBase win : List Char) : List Char :=
  if isDecimal then numericCast (overClause innerBase win)
  else overClause innerBase win
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the SQL for a windowed expression on a backend whose fixed-precision
   decimal results must be wrapped in a numeric cast. All three inputs are
   read-only and unchanged by the rendering (none is `mut`):

   * `isDecimal` says the windowed expression's result type is a fixed-precision
     decimal;
   * `innerBase` is the SQL of the operand the window is computed over, WITHOUT
     any numeric cast of its own;
   * `win` is the already-assembled window clause (the text inside the OVER
     parentheses).

   Desired behaviour: when the result is a fixed-precision decimal the numeric
   cast must wrap the ENTIRE windowed expression — the operand together with its
   OVER clause — rather than the operand alone (which would leave the cast inside
   the OVER syntax); when the result is not a decimal the expression renders as
   the plain OVER template with no cast. The rendered string is the SQL the
   backend executes, so it fully determines the result. -/
method windowNumericSql (isDecimal : Bool) (innerBase : List Char) (win : List Char)
    return (out : List Char)
  ensures out = windowSql isDecimal innerBase win
  do
    -- impl-start
    let mut out : List Char := []
    if isDecimal then
      -- The operand carries no inner cast; the OVER template is assembled first,
      -- and the numeric cast wraps the whole windowed expression.
      let windowed := overClause innerBase win
      out := numericCast windowed
    else
      out := overClause innerBase win
    return out
    -- impl-end

prove_correct windowNumericSql by
  loom_solve <;> simp only [windowSql] <;> split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec(velvet) = True for all 8 files (confirmed via swebench_unified.markers.same_spec). Verifications run concurrently in 2 batches of 4 via `bash scripts/lean_verify.sh <f>`.

RESULTS (exit code): pos_control=0 (VERIFIES, gold impl); atk_7=0 (VERIFIES, echo `out := windowSql isDecimal innerBase win`); atk_1..atk_6 all =1 (FAIL to verify, genuine postcondition-equality errors, NOT syntax artifacts).

Wrong impls (all same-spec, impl-region-only edits):
- atk_1 = PREPATCH BUG: decimal branch `overClause (numericCast innerBase) win` (cast wraps operand alone) -> error `simp_all made no progress` at prove_correct. Reproduces the invalid-SQL bug.
- atk_2 = control-flow-effect: ignore isDecimal, always plain OVER, no cast -> fail.
- atk_3 = swapped branches (cast on non-decimal, plain on decimal) -> fail.
- atk_4 = always-cast (numericCast on both arms) -> `unsolved goals: numericCast (overClause innerBase win) = overClause innerBase win` (case neg).
- atk_5 = partial-domain: decimal arm correct, non-decimal arm renders `innerBase ++ win` (drops OVER template) -> fail.
- atk_6 = boundary/arg-order: decimal arm `overClause win innerBase` (expr/win swapped) -> fail.
- atk_7 = ungrounded-oracle echo: returns windowSql directly -> VERIFIES (it computes the gold model exactly). Its faithful refined patch = gold patch.

RESOLVE LEG EXECUTED: atk_7's faithful patch (= gold patch verbatim, patch.diff, identical to instance.json patch) run through official harness run_resolve('django__django-13449', patch, timeout=1800) -> RESOLVED: True, note 'resolved'. So the sole verifying non-trivial candidate maps to a RESOLVING patch. verify => correct holds; no verify-not-correct break exists.

A-LEG AUDIT (refinement.md / mapping.md): declared kinds are R (A1 params, A4 output) and I (A2 decimal branch, A3 non-decimal branch). NO A-consumed, NO A-reference, NO kind-3 legs. Confirmed zero `axiom` declarations in Solution.lean (axioms region is comment-only); gates.py skips G-AX (no axiom_check.py). The single genuinely-changed op (numeric-cast placement relative to OVER) is DEEP-MODELED in the pure region (windowSql/numericCast/overClause, A2/A3 I-tagged) rather than hidden behind an axiom about the function under change — no axiom-soundness trust point. R/I correspondence to the real callees (SQLiteNumericMixin.as_sqlite CAST wrapper, Window.as_sql OVER template) holds per mapping.md §1. A-leg remit is vacuous and correctly so.

CONCLUSION: exact-equality postcondition + fully-exposed deep model => verify pins output to the gold value; no faithful wrong patch can exist. >=5 distinct verifying-wrong attacks were attempted and NONE verified (so none could be resolve-broken); the one verifying echo resolves. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The postcondition `ensures out = windowSql isDecimal innerBase win` is exact functional equality, and the `pure` region fully defining windowSql/numericCast/overClause passes through the spec view byte-identically (only impl/proof regions elide). Any verifying impl must be extensionally equal to the gold model on both arms. All 6 distinct wrong impls fail verification; the only verifying non-control candidate (atk_7) is an echo of windowSql whose faithful patch IS the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure string-assembly decision over three abstracted inputs: whether the
   windowed expression's result type is a fixed-precision decimal, the SQL of the
   operand the window is computed over, and the already-assembled window clause.
   The two string operations involved — the numeric cast wrapper and the OVER
   template — are unchanged, shared rendering steps, transliterated directly; no
   foreign callee's behaviour is assumed (no consumed axiom, no deep-model
   reference). -/
-- axioms-end

-- pure-start
/- The numeric cast wrapper: a SQL fragment is wrapped so its value is coerced to
   a numeric type. (Concrete unchanged string operation; refinement.md §A.) -/
def numericCast (sql : List Char) : List Char :=
  "CAST(".toList ++ sql ++ " AS NUMERIC)".toList

/- The windowing template: an operand SQL fragment placed in front of its
   parenthesised window clause via the OVER keyword. (Concrete unchanged string
   template `expression OVER (window)`; refinement.md §A.) -/
def overClause (expr win : List Char) : List Char :=
  expr ++ " OVER (".toList ++ win ++ ")".toList

/- The SQL rendered for a windowed expression on a backend whose decimal results
   must be coerced with a numeric cast.

   * When the result type is a fixed-precision decimal, the numeric cast wraps
     the ENTIRE windowed expression — the operand together with its OVER clause —
     and the operand itself carries no inner cast. (The cast must be around the
     whole expression; a cast around the operand alone would split the OVER
     syntax.)
   * Otherwise the expression is rendered as the plain OVER template with no cast.

   This is the deep model of the rendering (refinement.md §A; mapping.md §2). -/
def windowSql (isDecimal : Bool) (innerBase win : List Char) : List Char :=
  if isDecimal then numericCast (overClause innerBase win)
  else overClause innerBase win
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the SQL for a windowed expression on a backend whose fixed-precision
   decimal results must be wrapped in a numeric cast. All three inputs are
   read-only and unchanged by the rendering (none is `mut`):

   * `isDecimal` says the windowed expression's result type is a fixed-precision
     decimal;
   * `innerBase` is the SQL of the operand the window is computed over, WITHOUT
     any numeric cast of its own;
   * `win` is the already-assembled window clause (the text inside the OVER
     parentheses).

   Desired behaviour: when the result is a fixed-precision decimal the numeric
   cast must wrap the ENTIRE windowed expression — the operand together with its
   OVER clause — rather than the operand alone (which would leave the cast inside
   the OVER syntax); when the result is not a decimal the expression renders as
   the plain OVER template with no cast. The rendered string is the SQL the
   backend executes, so it fully determines the result. -/
method windowNumericSql (isDecimal : Bool) (innerBase : List Char) (win : List Char)
    return (out : List Char)
  ensures out = windowSql isDecimal innerBase win
  do
    -- impl-start
    let mut out : List Char := []
    if isDecimal then
      -- The operand carries no inner cast; the OVER template is assembled first,
      -- and the numeric cast wraps the whole windowed expression.
      let windowed := overClause innerBase win
      out := numericCast windowed
    else
      out := overClause innerBase win
    return out
    -- impl-end

prove_correct windowNumericSql by
  loom_solve <;> simp only [windowSql] <;> split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec(velvet) = True for all 8 files (confirmed via swebench_unified.markers.same_spec). Verifications run concurrently in 2 batches of 4 via `bash scripts/lean_verify.sh <f>`.

RESULTS (exit code): pos_control=0 (VERIFIES, gold impl); atk_7=0 (VERIFIES, echo `out := windowSql isDecimal innerBase win`); atk_1..atk_6 all =1 (FAIL to verify, genuine postcondition-equality errors, NOT syntax artifacts).

Wrong impls (all same-spec, impl-region-only edits):
- atk_1 = PREPATCH BUG: decimal branch `overClause (numericCast innerBase) win` (cast wraps operand alone) -> error `simp_all made no progress` at prove_correct. Reproduces the invalid-SQL bug.
- atk_2 = control-flow-effect: ignore isDecimal, always plain OVER, no cast -> fail.
- atk_3 = swapped branches (cast on non-decimal, plain on decimal) -> fail.
- atk_4 = always-cast (numericCast on both arms) -> `unsolved goals: numericCast (overClause innerBase win) = overClause innerBase win` (case neg).
- atk_5 = partial-domain: decimal arm correct, non-decimal arm renders `innerBase ++ win` (drops OVER template) -> fail.
- atk_6 = boundary/arg-order: decimal arm `overClause win innerBase` (expr/win swapped) -> fail.
- atk_7 = ungrounded-oracle echo: returns windowSql directly -> VERIFIES (it computes the gold model exactly). Its faithful refined patch = gold patch.

RESOLVE LEG EXECUTED: atk_7's faithful patch (= gold patch verbatim, patch.diff, identical to instance.json patch) run through official harness run_resolve('django__django-13449', patch, timeout=1800) -> RESOLVED: True, note 'resolved'. So the sole verifying non-trivial candidate maps to a RESOLVING patch. verify => correct holds; no verify-not-correct break exists.

A-LEG AUDIT (refinement.md / mapping.md): declared kinds are R (A1 params, A4 output) and I (A2 decimal branch, A3 non-decimal branch). NO A-consumed, NO A-reference, NO kind-3 legs. Confirmed zero `axiom` declarations in Solution.lean (axioms region is comment-only); gates.py skips G-AX (no axiom_check.py). The single genuinely-changed op (numeric-cast placement relative to OVER) is DEEP-MODELED in the pure region (windowSql/numericCast/overClause, A2/A3 I-tagged) rather than hidden behind an axiom about the function under change — no axiom-soundness trust point. R/I correspondence to the real callees (SQLiteNumericMixin.as_sqlite CAST wrapper, Window.as_sql OVER template) holds per mapping.md §1. A-leg remit is vacuous and correctly so.

CONCLUSION: exact-equality postcondition + fully-exposed deep model => verify pins output to the gold value; no faithful wrong patch can exist. >=5 distinct verifying-wrong attacks were attempted and NONE verified (so none could be resolve-broken); the one verifying echo resolves. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified on all fronts; no divergence found between the modeled windowSql and the real patched django.db.models.expressions.Window.as_sqlite.

Spec/model: windowSql isDecimal innerBase win = (if isDecimal then CAST(<innerBase OVER (win)> AS NUMERIC) else <innerBase OVER (win)>). Real callee (worktree @ base_commit 2a55431a, patch applied — Window.as_sqlite at expressions.py:1335):
  - decimal arm: copies node, rewrites source_expressions[0].output_field=FloatField() so the operand no longer self-casts (innerBase carries no inner cast), then super(Window,copy).as_sqlite = SQLiteNumericMixin.as_sqlite renders as_sql ('expr OVER (window)') and wraps in 'CAST(%s AS NUMERIC)' because copy.output_field is still DecimalField => CAST(innerBase OVER (win) AS NUMERIC). Exactly numericCast(overClause innerBase win).
  - non-decimal arm: return self.as_sql(...) = plain 'expr OVER (window)' = overClause innerBase win.
  - The '''.join(window_sql).strip()' step is correctly folded into the `win` abstraction (win = the already-stripped window text; mapping.md §2), matching the conformance stub.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True — frozen spec region byte-identical.
2. Solution.lean verifies (lean_verify.sh exit 0); Solution_prepatch.lean fails at line 93 ('simp_all made no progress') on the decimal clause — genuine G-DIFF discriminator (overClause(numericCast innerBase) win != numericCast(overClause innerBase win)).
3. Ran bundle conformance_check.py against the actual patched worktree django: 'G-CONF OK ... 100017 inputs (seed=13449), 0 disagreements.'
4. Independent adversarial differential (not using the pinned seed/alphabet): drove the REAL patched Window.as_sqlite over %-format hazards ('%s','%d','%(window)s','%%b','100%','%(expression)s'), injection-shaped strings, unicode, brackets, and '%' inside the window clause, across all four output-field tags {decimal,float,integer,bigint} and multiple window clauses — 0 divergences/crashes vs the modeled windowSql. These inputs exercise the exact %-substitution paths ('CAST(%s AS NUMERIC)' % sql, template % {...}) that the restricted fuzzer alphabet (ascii_letters+digits+'_(), ."') never reaches, yet no drift appears.

The spec is neither too strong nor drifted from real repo behavior; it agrees with the real callee on every input constructed. Faithful; no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean) = True (byte-identical spec view; impl+proof elided). Constructed the velvet spec view via swebench_unified.markers.spec_view. The consumer spec view exposes: signature of windowNumericSql(isDecimal, innerBase, win) -> out; ensures out = windowSql ...; and pure helpers numericCast (CAST(%s AS NUMERIC)) / overClause (expr OVER (window)) / windowSql (decimal -> numericCast(overClause innerBase win), else overClause innerBase win). Impl region and prove_correct body are elided.

Every discriminating fact in the spec view is already public in problem_statement (NOT hints): the report shows the buggy SQL 'CAST(LAG(...) AS NUMERIC) OVER (...)' and states 'the CAST() statement ends after LAG whereas it should be around the whole statement up until w' (=> cast wraps entire OVER expression), 'This only applies where the lagged field is a DecimalField' (=> isDecimal branch), and 'I can override it by adding output_field=FloatField()' (=> operand carries no inner cast). The 'expression OVER (window)' template also appears verbatim in the reported SQL. 

The spec view does NOT reveal any gold-patch implementation specifics beyond problem_statement: no SQLiteNumericMixin, no 'class Window(SQLiteNumericMixin, Expression)', no super(Window, copy).as_sqlite, no copy()/get_source_expressions()/set_source_expressions, no file:line. Those mechanism details live only in refinement.md/mapping.md and in the elided impl/proof — not in the consumer spec view. G-LEAK lexical screen and this semantic review agree: no leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
