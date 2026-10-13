# P2 adversarial audit — django__django-15375

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
   do
     -- impl-start
     if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
+      return { isTerminal := false, hasFallback := true }
     else
       return { isTerminal := terminal, hasFallback := false }
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,9 @@
   do
     -- impl-start
     if defaultVal.isSome then
+      return { isTerminal := terminal, hasFallback := false }
+    else
       return { isTerminal := terminal, hasFallback := true }
-    else
-      return { isTerminal := terminal, hasFallback := false }
     -- impl-end
 
 prove_correct prepareAggregate by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,7 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
-    if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
-    else
-      return { isTerminal := terminal, hasFallback := false }
+    return { isTerminal := true, hasFallback := defaultVal.isSome }
     -- impl-end
 
 prove_correct prepareAggregate by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
-    if defaultVal.isSome then
+    if defaultVal.isNone then
       return { isTerminal := terminal, hasFallback := true }
     else
       return { isTerminal := terminal, hasFallback := false }
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,10 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
+    let mut r : Resolved := { isTerminal := terminal, hasFallback := false }
     if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
-    else
-      return { isTerminal := terminal, hasFallback := false }
+      r := { isTerminal := terminal, hasFallback := false }
+    return r
     -- impl-end
 
 prove_correct prepareAggregate by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,7 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
-    if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
-    else
-      return { isTerminal := terminal, hasFallback := false }
+    return { isTerminal := false, hasFallback := false }
     -- impl-end
 
 prove_correct prepareAggregate by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,10 +79,7 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
-    if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
-    else
-      return { isTerminal := terminal, hasFallback := false }
+    return prepared terminal defaultVal
     -- impl-end
 
 prove_correct prepareAggregate by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,10 @@
   ensures out.hasFallback = defaultVal.isSome
   do
     -- impl-start
-    if defaultVal.isSome then
-      return { isTerminal := terminal, hasFallback := true }
+    if defaultVal.isSome && terminal then
+      return { isTerminal := false, hasFallback := true }
     else
-      return { isTerminal := terminal, hasFallback := false }
+      return { isTerminal := terminal, hasFallback := defaultVal.isSome }
     -- impl-end
 
 prove_correct prepareAggregate by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line branch (wrap
   the fallback form or return the bare aggregation) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over the
-- observable shape of the prepared clause (see `pure` region). The unchanged
-- callees the model relies on (how base resolution sets the terminal marker, and
-- what marker a freshly built fallback wrapper carries) are facts about real
-- objects, audited executably by axiom_check.py (G-AX) — not assumed here.
-- axioms-end

-- pure-start
/- The observable shape of a prepared aggregation clause, restricted to the two
   aspects that decide how the query builder later places it:

   * `isTerminal` — whether the clause is marked as a terminal (top-level)
     aggregation. The query builder consults exactly this marker to decide
     whether the clause is computed at the outer level; a clause that is
     terminal-in-fact but unmarked is mis-placed and yields malformed output.
   * `hasFallback` — whether the clause is the fallback form that substitutes a
     supplied value when the aggregation has no rows, rather than the bare
     aggregation.

   Other attributes of the clause (the column, the function name, output type)
   are untouched by this preparation step and are not part of this carrier
   (mapping.md §2). -/
structure Resolved where
  isTerminal : Bool
  hasFallback : Bool
  deriving DecidableEq, Inhabited, Repr

/- Preparing an aggregation clause to be added to a query, given whether it is
   requested as a terminal (top-level) aggregation and whether a fallback value
   is supplied for the empty-rows case.

   * With no fallback supplied, the clause is the bare aggregation, carrying the
     terminal marker as requested.
   * With a fallback supplied, the clause becomes the fallback form — and it
     MUST carry the SAME terminal marker the bare aggregation would have. The
     terminal status is a property of the aggregation itself and may not be
     dropped merely because the empty-rows fallback was wrapped around it. -/
def prepared (terminal : Bool) (defaultVal : Option Int) : Resolved :=
  match defaultVal with
  | none   => { isTerminal := terminal, hasFallback := false }
  | some _ => { isTerminal := terminal, hasFallback := true }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare an aggregation clause as it is added to a query. `terminal` says the
   aggregation is requested at the top level; `defaultVal` optionally supplies a
   value to substitute when the aggregation matches no rows.

   The frozen guarantee: the prepared clause ALWAYS carries the requested
   terminal marker — whether or not a fallback value is supplied — and reports
   the fallback form exactly when a fallback value is supplied. The terminal
   marker must never be lost when the fallback form is produced; otherwise a
   top-level aggregation with a fallback would be mis-placed by the query builder
   and produce malformed output.

   `terminal` and `defaultVal` are read-only inputs (not `mut`); the routine
   produces a fresh clause description and mutates nothing (directive 5). -/
method prepareAggregate (terminal : Bool) (defaultVal : Option Int) return (out : Resolved)
  ensures out = prepared terminal defaultVal
  ensures out.isTerminal = terminal
  ensures out.hasFallback = defaultVal.isSome
  do
    -- impl-start
    if defaultVal.isSome then
      return { isTerminal := terminal, hasFallback := true }
    else
      return { isTerminal := terminal, hasFallback := false }
    -- impl-end

prove_correct prepareAggregate by
  loom_solve
  all_goals (cases defaultVal <;> simp_all [prepared])
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: the three postconditions (out = prepared terminal defaultVal; out.isTerminal = terminal; out.hasFallback = defaultVal.isSome) together determine the exact Resolved value for every (terminal, defaultVal), so any verifying impl is observably identical to gold on the full terminal x fallback grid.

PROTOCOL. same_spec(velvet) = True for pos + atk_1..8 (axioms/pure/pre/post byte-identical; only impl region edited). Verify cmd per file: `bash scripts/lean_verify.sh <file>`.

### ATTACKS (verify exit; 0=verifies, 1=fails):
- atk_1.lean prepatch bug (fallback arm drops terminal marker, isTerminal:=false) => exit 1 FAILS (goal `terminal = false`).
- atk_2.lean hasFallback swapped between arms => exit 1 FAILS.
- atk_3.lean ungrounded-oracle: isTerminal hard-wired true => exit 1 FAILS (goal `terminal = true`).
- atk_4.lean boundary/guard flip (branch on isNone, arms swapped) => exit 1 FAILS.
- atk_5.lean control-flow-effect (mut var, always bare/no fallback) => exit 1 FAILS.
- atk_6.lean constant all-false => exit 1 FAILS.
- atk_8.lean partial-domain (drops marker only when terminal AND fallback) => exit 1 FAILS (goal False under if_pos terminal=true).
- atk_7.lean oracle echo `return prepared terminal defaultVal` => exit 0 VERIFIES. This is NOT a wrong impl: its observable equals `prepared`, i.e. gold's observable on every input; behaviorally gold-equivalent.

Positive control pos.lean (= Solution.lean) verifies (exit 0). Bundled Solution_prepatch.lean also reproduced (copied to prepatch.lean, exit 1, fails out.isTerminal=terminal on some-branch) => prepatch_reproduced=true.

RESOLVE (protocol step 2): atk_7 is the only verifying attack. Its faithful refined patch is the gold patch verbatim (observable identical to gold across the whole grid). Materialized at atk_7.patch and RUN through the official harness: `sudo -n python -c "run_resolve('django__django-15375', patch, timeout=1800)"` => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying wrong-shaped candidate's patch RESOLVES; no verify-not-correct break found.

REFINEMENT AUDIT: meta.json axioms=[] and deep_model_references=[] — no A-consumed / A-reference legs exist (the 'A#' labels in refinement.md's table are row ids, not axiom tags). Every leg is R (A1 summarize<->terminal, A2 default<->Option) or I / R+I (A3 branch, A4 bare arm, A5 fallback arm). The genuinely-changed op (propagate terminal marker onto fallback wrapper) is modeled DIRECTLY as isTerminal:=terminal in prepared's some-branch, matching gold's added `coalesce.is_summary = c.is_summary`. NO kind-3 leg. Model<->patch correspondence holds. G-AX facts (base resolution sets is_summary==summarize; fresh Coalesce defaults False) are unchanged-callee facts checked executably, non-circular.

VERDICT: SOUND. 8 same-spec attacks run and verified; 7 wrong-shaped attacks all FAIL verification; the single verifier is behaviorally gold and its faithful patch RESOLVES under the official harness. verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line branch (wrap
   the fallback form or return the bare aggregation) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over the
-- observable shape of the prepared clause (see `pure` region). The unchanged
-- callees the model relies on (how base resolution sets the terminal marker, and
-- what marker a freshly built fallback wrapper carries) are facts about real
-- objects, audited executably by axiom_check.py (G-AX) — not assumed here.
-- axioms-end

-- pure-start
/- The observable shape of a prepared aggregation clause, restricted to the two
   aspects that decide how the query builder later places it:

   * `isTerminal` — whether the clause is marked as a terminal (top-level)
     aggregation. The query builder consults exactly this marker to decide
     whether the clause is computed at the outer level; a clause that is
     terminal-in-fact but unmarked is mis-placed and yields malformed output.
   * `hasFallback` — whether the clause is the fallback form that substitutes a
     supplied value when the aggregation has no rows, rather than the bare
     aggregation.

   Other attributes of the clause (the column, the function name, output type)
   are untouched by this preparation step and are not part of this carrier
   (mapping.md §2). -/
structure Resolved where
  isTerminal : Bool
  hasFallback : Bool
  deriving DecidableEq, Inhabited, Repr

/- Preparing an aggregation clause to be added to a query, given whether it is
   requested as a terminal (top-level) aggregation and whether a fallback value
   is supplied for the empty-rows case.

   * With no fallback supplied, the clause is the bare aggregation, carrying the
     terminal marker as requested.
   * With a fallback supplied, the clause becomes the fallback form — and it
     MUST carry the SAME terminal marker the bare aggregation would have. The
     terminal status is a property of the aggregation itself and may not be
     dropped merely because the empty-rows fallback was wrapped around it. -/
def prepared (terminal : Bool) (defaultVal : Option Int) : Resolved :=
  match defaultVal with
  | none   => { isTerminal := terminal, hasFallback := false }
  | some _ => { isTerminal := terminal, hasFallback := true }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare an aggregation clause as it is added to a query. `terminal` says the
   aggregation is requested at the top level; `defaultVal` optionally supplies a
   value to substitute when the aggregation matches no rows.

   The frozen guarantee: the prepared clause ALWAYS carries the requested
   terminal marker — whether or not a fallback value is supplied — and reports
   the fallback form exactly when a fallback value is supplied. The terminal
   marker must never be lost when the fallback form is produced; otherwise a
   top-level aggregation with a fallback would be mis-placed by the query builder
   and produce malformed output.

   `terminal` and `defaultVal` are read-only inputs (not `mut`); the routine
   produces a fresh clause description and mutates nothing (directive 5). -/
method prepareAggregate (terminal : Bool) (defaultVal : Option Int) return (out : Resolved)
  ensures out = prepared terminal defaultVal
  ensures out.isTerminal = terminal
  ensures out.hasFallback = defaultVal.isSome
  do
    -- impl-start
    if defaultVal.isSome then
      return { isTerminal := terminal, hasFallback := true }
    else
      return { isTerminal := terminal, hasFallback := false }
    -- impl-end

prove_correct prepareAggregate by
  loom_solve
  all_goals (cases defaultVal <;> simp_all [prepared])
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: the three postconditions (out = prepared terminal defaultVal; out.isTerminal = terminal; out.hasFallback = defaultVal.isSome) together determine the exact Resolved value for every (terminal, defaultVal), so any verifying impl is observably identical to gold on the full terminal x fallback grid.

PROTOCOL. same_spec(velvet) = True for pos + atk_1..8 (axioms/pure/pre/post byte-identical; only impl region edited). Verify cmd per file: `bash scripts/lean_verify.sh <file>`.

### ATTACKS (verify exit; 0=verifies, 1=fails):
- atk_1.lean prepatch bug (fallback arm drops terminal marker, isTerminal:=false) => exit 1 FAILS (goal `terminal = false`).
- atk_2.lean hasFallback swapped between arms => exit 1 FAILS.
- atk_3.lean ungrounded-oracle: isTerminal hard-wired true => exit 1 FAILS (goal `terminal = true`).
- atk_4.lean boundary/guard flip (branch on isNone, arms swapped) => exit 1 FAILS.
- atk_5.lean control-flow-effect (mut var, always bare/no fallback) => exit 1 FAILS.
- atk_6.lean constant all-false => exit 1 FAILS.
- atk_8.lean partial-domain (drops marker only when terminal AND fallback) => exit 1 FAILS (goal False under if_pos terminal=true).
- atk_7.lean oracle echo `return prepared terminal defaultVal` => exit 0 VERIFIES. This is NOT a wrong impl: its observable equals `prepared`, i.e. gold's observable on every input; behaviorally gold-equivalent.

Positive control pos.lean (= Solution.lean) verifies (exit 0). Bundled Solution_prepatch.lean also reproduced (copied to prepatch.lean, exit 1, fails out.isTerminal=terminal on some-branch) => prepatch_reproduced=true.

RESOLVE (protocol step 2): atk_7 is the only verifying attack. Its faithful refined patch is the gold patch verbatim (observable identical to gold across the whole grid). Materialized at atk_7.patch and RUN through the official harness: `sudo -n python -c "run_resolve('django__django-15375', patch, timeout=1800)"` => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying wrong-shaped candidate's patch RESOLVES; no verify-not-correct break found.

REFINEMENT AUDIT: meta.json axioms=[] and deep_model_references=[] — no A-consumed / A-reference legs exist (the 'A#' labels in refinement.md's table are row ids, not axiom tags). Every leg is R (A1 summarize<->terminal, A2 default<->Option) or I / R+I (A3 branch, A4 bare arm, A5 fallback arm). The genuinely-changed op (propagate terminal marker onto fallback wrapper) is modeled DIRECTLY as isTerminal:=terminal in prepared's some-branch, matching gold's added `coalesce.is_summary = c.is_summary`. NO kind-3 leg. Model<->patch correspondence holds. G-AX facts (base resolution sets is_summary==summarize; fresh Coalesce defaults False) are unchanged-callee facts checked executably, non-circular.

VERDICT: SOUND. 8 same-spec attacks run and verified; 7 wrong-shaped attacks all FAIL verification; the single verifier is behaviorally gold and its faithful patch RESOLVES under the official harness. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of Aggregate.resolve_expression (django/db/models/aggregates.py:50). Model: prepared terminal defaultVal = {isTerminal:=terminal, hasFallback:=defaultVal.isSome}; postconditions out.isTerminal=terminal (always) and out.hasFallback=defaultVal.isSome. Real patched behavior: super().resolve_expression sets c.is_summary=summarize (expressions.py:246, unchanged); when default supplied, gold patch wraps in Coalesce(c,default) and copies coalesce.is_summary=c.is_summary; so result.is_summary==summarize ALWAYS and isinstance(result,Coalesce) iff default supplied. Model matches exactly. EVIDENCE: applied gold patch to, ran conformance_check.py against real Django -> G-CONF OK 0 disagreements over 100008 inputs, seed=15375. (2) direct oracle probe over Sum/Avg/Max x terminal{F,T} x default{None,0,5} all match model, no divergence. (3) same_spec(Solution.lean, Solution_prepatch.lean, velvet tables)=True; pure/impl/axioms region hashes match meta.json. (4) Solution.lean verifies exit 0; Solution_prepatch.lean (fallback arm isTerminal:=false) FAILS out.isTerminal=terminal on some case, so G-DIFF discriminates. Option Int abstraction of default is sound (only presence observable; value content I-tagged, flows unchanged). No diverging input found; spec is not too strong and does not drift from the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean, velvet tables)=True (verified via swebench_unified.markers) — spec/pure/pre/post regions byte-identical; prepatch differs only in the elided impl arm. Lexical G-LEAK screen (leakage.screen against problem_statement) PASSES with zero hard failures; meta G-LEAK status=pass; no RELAXED_LEAKAGE.md and relaxed_leakage unset. Leakage judged vs public problem_statement only (hints_text, which contains the diff, excluded). Gold edit = `coalesce.is_summary = c.is_summary` (propagate terminal/top-level marker onto the Coalesce fallback wrapper, aggregates.py). Spec view discloses NONE of the repo-internal discriminators: is_summary/summarize/Coalesce/resolve_expression/aggregates.py/_output_field all absent (confirmed by scan). Instead it abstracts to a generic 'prepared aggregation clause' with isTerminal (outer-level placement marker) and hasFallback (empty-rows fallback form). The PS already exhibits the full symptom+cause: malformed SQL 'SELECT FROM (SELECT … COALESCE(SUM(...), ?) …) subquery' — empty outer SELECT with the aggregate trapped in the inner subquery = a top-level aggregation not placed at outer level; plus the Coalesce long-form workaround. The spec's frozen guarantee (fallback form must retain the same terminal marker else a top-level aggregation with a fallback is mis-placed → malformed output) is a de-narrated diagnosis of that publicly-visible malformed SQL, not new gold-internal information; the mechanism token is never named. Overlapping words (aggregation/default/query/clause) are inherent to the public issue title. Faithful spec discriminator is reconstructible from the PS symptom alone. Clean NO-LEAKAGE — relaxation not required.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
