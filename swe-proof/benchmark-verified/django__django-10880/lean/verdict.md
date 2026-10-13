# P2 adversarial audit — django__django-10880

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,7 @@
     List Char := Id.run do
   let mut distinctSlot : List Char := []
   if distinct then
-    distinctSlot := "DISTINCT ".toList
+    distinctSlot := "DISTINCT".toList
   return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,7 @@
   let mut distinctSlot : List Char := []
   if distinct then
     distinctSlot := "DISTINCT ".toList
-  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
+  return function ++ ['('] ++ distinctSlot ++ expressions
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,9 +32,7 @@
 def implementation_buildCallSql
     (function : List Char) (distinct : Bool) (expressions : List Char) :
     List Char := Id.run do
-  let mut distinctSlot : List Char := []
-  if distinct then
-    distinctSlot := "DISTINCT ".toList
+  let distinctSlot : List Char := "DISTINCT ".toList
   return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,7 @@
   let mut distinctSlot : List Char := []
   if distinct then
     distinctSlot := "DISTINCT ".toList
-  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
+  return expressions ++ ['('] ++ distinctSlot ++ function ++ [')']
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,7 @@
     (function : List Char) (distinct : Bool) (expressions : List Char) :
     List Char := Id.run do
   let mut distinctSlot : List Char := []
-  if distinct then
+  if !distinct then
     distinctSlot := "DISTINCT ".toList
   return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
 -- impl-end
@@ -45,5 +45,5 @@
       (implementation_buildCallSql function distinct expressions) := by
   intro function distinct expressions
   unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword
-  cases distinct <;> rfl
+  cases distinct <;> simp [distinctKeyword]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,10 +32,10 @@
 def implementation_buildCallSql
     (function : List Char) (distinct : Bool) (expressions : List Char) :
     List Char := Id.run do
-  let mut distinctSlot : List Char := []
   if distinct then
-    distinctSlot := "DISTINCT ".toList
-  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
+    return function ++ ['('] ++ "DISTINCT ".toList ++ expressions ++ [')']
+  else
+    return function ++ ['('] ++ expressions
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,11 +31,8 @@
 -- impl-start
 def implementation_buildCallSql
     (function : List Char) (distinct : Bool) (expressions : List Char) :
-    List Char := Id.run do
-  let mut distinctSlot : List Char := []
-  if distinct then
-    distinctSlot := "DISTINCT ".toList
-  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
+    List Char :=
+  function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']
 -- impl-end
 
 -- proof-start
@@ -44,6 +41,5 @@
     problem_spec_buildCallSql function distinct expressions
       (implementation_buildCallSql function distinct expressions) := by
   intro function distinct expressions
-  unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword
-  cases distinct <;> rfl
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the SQL-fragment assembly
-- is rendered concretely as a literal-driven concatenation, and the DISTINCT
-- modifier text is modeled DEEPLY (below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The DISTINCT modifier fragment emitted before the argument text. When the
modifier is requested the keyword is followed by a single space so it is kept
separate from whatever argument text follows it; otherwise the fragment is
empty. -/
def distinctKeyword (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []
-- pure-end

-- post-conditions-start
/-- The rendered call text is exactly the function name, an opening parenthesis,
the DISTINCT modifier fragment, the argument text, and a closing parenthesis, in
that order. Every unchanged component (function name, parentheses, argument text)
is pinned to its input; only the modifier fragment depends on the flag. -/
def problem_spec_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char)
    (result : List Char) : Prop :=
  result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']
-- post-conditions-end

-- impl-start
def implementation_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char := Id.run do
  let mut distinctSlot : List Char := []
  if distinct then
    distinctSlot := "DISTINCT ".toList
  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
-- impl-end

-- proof-start
theorem correct_buildCallSql :
    ∀ (function : List Char) (distinct : Bool) (expressions : List Char),
    problem_spec_buildCallSql function distinct expressions
      (implementation_buildCallSql function distinct expressions) := by
  intro function distinct expressions
  unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword
  cases distinct <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_buildCallSql is a TOTAL EQUALITY pinning the output uniquely for every (function, distinct, expressions): result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']. By Lean soundness any impl whose correct_ proof closes must equal the gold on ALL inputs — leaving no room for verify AND NOT resolve. distinctKeyword is a DEEP MODEL (R/I), not an axiom; axioms region is EMPTY and #print axioms confirms clean (no dependency) for every closing proof.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (lean backend). Header (lines 1-30, through post-conditions-end) byte-identical across all; only impl+proof regions edited.

### VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- pos_control (gold impl verbatim): EXIT 0 (verifies). #print axioms: 'correct_buildCallSql does not depend on any axioms'.
- atk_1 PREPATCH BUG ('DISTINCT' no trailing space): EXIT 1 (does NOT close) => prepatch bug reproduced. Goal residue shows 'DISTINCT' vs 'DISTINCT '.
- atk_2 drop closing paren: EXIT 1 (does not close).
- atk_3 always emit 'DISTINCT ' regardless of flag (wrong when distinct=false): EXIT 1.
- atk_4 swap function/expressions order (structure wrong): EXIT 1.
- atk_5 negated flag (!distinct) control-flow-effect: EXIT 1 (honest proof, no sorry; simp residue 'DISTINCT ' :: ... ).
- atk_6 partial-domain/boundary (correct only when distinct; drops paren when not): EXIT 1.
- atk_7 UNGROUNDED-ORACLE ECHO (impl body literally = spec RHS, function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']): EXIT 0 (verifies by rfl), #print axioms clean (no dependency).

Commands (per attack N): bash scripts/lean_verify.sh atk_N.lean ; and appended '#print axioms correct_buildCallSql' for the two closing files (pos_control_ax.lean, atk_7_ax.lean, both EXIT 0, clean).

RESOLVE (protocol step 2 — every closing wrong-shaped impl's faithful patch MUST be run through the official harness): the ONLY closing non-gold impl is atk_7, which is extensionally IDENTICAL to the gold (its body is the spec RHS = distinctKeyword semantics = 'DISTINCT ' when distinct else ''). Its faithful patch is therefore the gold patch. Executed harness.run_resolve('django__django-10880', atk_7_patch): RESOLVED=True, COMPLETED=True; FAIL_TO_PASS test_count_distinct_expression PASSED; all 55 PASS_TO_PASS green. So the only verify->closing impl also RESOLVES. No verify AND NOT resolve witness exists.

REFINEMENT AUDIT: refinement.md rows are R (1,2,3) and I (4,5); NO A-consumed, NO A-reference, NO kind-3/changed-inexpressible. Axioms region empty (mapping.md + Solution.lean lines 4-9); G-AX is a genuine skip stub. The deep model distinctKeyword corresponds exactly to the patched Python extra_context['distinct'] = 'DISTINCT ' if self.distinct else '' (mapping.md/refinement.md row 3), and the literal-template substitution %(function)s(%(distinct)s%(expressions)s) is reproduced concretely as the fixed-order concatenation (I op) — correspondence holds. conformance_check.py independently fuzz-checks the R/I shadow vs a Python %-template reconstruction (seed 10880, 120k inputs).

CONCLUSION: A-legs vacuous (no axioms/deep-model-refs to break); model<->patch correspondence holds; the tight total-equality spec admits only gold-equivalent closing impls, and the sole such impl resolves. verify => correct upheld. No breakage found across 7 attacks (>=5 distinct wrong shapes: prepatch, boundary/partial-domain, control-flow-effect, structure, ungrounded-oracle echo).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the SQL-fragment assembly
-- is rendered concretely as a literal-driven concatenation, and the DISTINCT
-- modifier text is modeled DEEPLY (below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The DISTINCT modifier fragment emitted before the argument text. When the
modifier is requested the keyword is followed by a single space so it is kept
separate from whatever argument text follows it; otherwise the fragment is
empty. -/
def distinctKeyword (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []
-- pure-end

-- post-conditions-start
/-- The rendered call text is exactly the function name, an opening parenthesis,
the DISTINCT modifier fragment, the argument text, and a closing parenthesis, in
that order. Every unchanged component (function name, parentheses, argument text)
is pinned to its input; only the modifier fragment depends on the flag. -/
def problem_spec_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char)
    (result : List Char) : Prop :=
  result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']
-- post-conditions-end

-- impl-start
def implementation_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char := Id.run do
  let mut distinctSlot : List Char := []
  if distinct then
    distinctSlot := "DISTINCT ".toList
  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
-- impl-end

-- proof-start
theorem correct_buildCallSql :
    ∀ (function : List Char) (distinct : Bool) (expressions : List Char),
    problem_spec_buildCallSql function distinct expressions
      (implementation_buildCallSql function distinct expressions) := by
  intro function distinct expressions
  unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword
  cases distinct <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_buildCallSql is a TOTAL EQUALITY pinning the output uniquely for every (function, distinct, expressions): result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']. By Lean soundness any impl whose correct_ proof closes must equal the gold on ALL inputs — leaving no room for verify AND NOT resolve. distinctKeyword is a DEEP MODEL (R/I), not an axiom; axioms region is EMPTY and #print axioms confirms clean (no dependency) for every closing proof.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (lean backend). Header (lines 1-30, through post-conditions-end) byte-identical across all; only impl+proof regions edited.

### VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- pos_control (gold impl verbatim): EXIT 0 (verifies). #print axioms: 'correct_buildCallSql does not depend on any axioms'.
- atk_1 PREPATCH BUG ('DISTINCT' no trailing space): EXIT 1 (does NOT close) => prepatch bug reproduced. Goal residue shows 'DISTINCT' vs 'DISTINCT '.
- atk_2 drop closing paren: EXIT 1 (does not close).
- atk_3 always emit 'DISTINCT ' regardless of flag (wrong when distinct=false): EXIT 1.
- atk_4 swap function/expressions order (structure wrong): EXIT 1.
- atk_5 negated flag (!distinct) control-flow-effect: EXIT 1 (honest proof, no sorry; simp residue 'DISTINCT ' :: ... ).
- atk_6 partial-domain/boundary (correct only when distinct; drops paren when not): EXIT 1.
- atk_7 UNGROUNDED-ORACLE ECHO (impl body literally = spec RHS, function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']): EXIT 0 (verifies by rfl), #print axioms clean (no dependency).

Commands (per attack N): bash scripts/lean_verify.sh atk_N.lean ; and appended '#print axioms correct_buildCallSql' for the two closing files (pos_control_ax.lean, atk_7_ax.lean, both EXIT 0, clean).

RESOLVE (protocol step 2 — every closing wrong-shaped impl's faithful patch MUST be run through the official harness): the ONLY closing non-gold impl is atk_7, which is extensionally IDENTICAL to the gold (its body is the spec RHS = distinctKeyword semantics = 'DISTINCT ' when distinct else ''). Its faithful patch is therefore the gold patch. Executed harness.run_resolve('django__django-10880', atk_7_patch): RESOLVED=True, COMPLETED=True; FAIL_TO_PASS test_count_distinct_expression PASSED; all 55 PASS_TO_PASS green. So the only verify->closing impl also RESOLVES. No verify AND NOT resolve witness exists.

REFINEMENT AUDIT: refinement.md rows are R (1,2,3) and I (4,5); NO A-consumed, NO A-reference, NO kind-3/changed-inexpressible. Axioms region empty (mapping.md + Solution.lean lines 4-9); G-AX is a genuine skip stub. The deep model distinctKeyword corresponds exactly to the patched Python extra_context['distinct'] = 'DISTINCT ' if self.distinct else '' (mapping.md/refinement.md row 3), and the literal-template substitution %(function)s(%(distinct)s%(expressions)s) is reproduced concretely as the fixed-order concatenation (I op) — correspondence holds. conformance_check.py independently fuzz-checks the R/I shadow vs a Python %-template reconstruction (seed 10880, 120k inputs).

CONCLUSION: A-legs vacuous (no axioms/deep-model-refs to break); model<->patch correspondence holds; the tight total-equality spec admits only gold-equivalent closing impls, and the sole such impl resolves. verify => correct upheld. No breakage found across 7 attacks (>=5 distinct wrong shapes: prepatch, boundary/partial-domain, control-flow-effect, structure, ungrounded-oracle echo).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-10880 lean bundle.

Modeled function: Aggregate.as_sql no-filter path (django/db/models/aggregates.py). It renders `template % data` with template `'%(function)s(%(distinct)s%(expressions)s)'`, where the patched line sets extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''. The Lean spec models this as fixed-order concatenation: result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')'], with distinctKeyword true = "DISTINCT ".toList (matches the patch exactly), distinctKeyword false = [].

Verification performed:
1. lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/error).
2. #print axioms correct_buildCallSql -> 'does not depend on any axioms' (no sorryAx; proof is real, closed by `cases distinct <;> rfl`).
3. same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True -> spec region (axioms/pure/post-conditions) byte-identical; only impl+proof differ (post 'DISTINCT ' vs pre 'DISTINCT'). G-DIFF signal genuine.
4. Adversarial divergence test between real callee (`template % data`) and the concatenation model: Python %-dict formatting does a single pass over the template and never re-scans substituted values, so concatenation == template%data on ALL inputs, including values containing %, %s, %d, %%, and nested %(key)s tokens in both the function and expression slots (tested 'COUNT(DISTINCT CASE...)', '*', '50%', '%(function)s', '100%%', 'a % b %s %d', 'X%Y'). Zero disagreements.

Scoping (no-filter path only; params list out of model scope) is a legitimate modeling boundary, not spec drift: both filter branches re-render the same template with the same distinct slot, and the F2P test (test_count_distinct_expression) exercises the no-filter path. On the modeled function's domain (function/distinct/expressions), the frozen spec exactly matches the real repo callee's output.

No input where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: one char, `'DISTINCT'` -> `'DISTINCT '` (add trailing space) in django/db/models/aggregates.py `as_sql`. Public problem_statement already discloses the fix fully: 'A space is missing at least (... COUNT(DISTINCTCASE WHEN ...)' — i.e. correct output needs a space between DISTINCT and the following text, and that space is the bug.

Spec view (regenerated via markers.spec_view with LeanBackend tables; impl+proof correctly elided to placeholders) contains only: (pure) `distinctKeyword distinct := if distinct then "DISTINCT ".toList else []` and (post-conditions) `result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']`, with abstract doc comments ('keyword followed by a single space so it is kept separate from whatever argument text follows').

Assessment: the spec necessarily encodes correct behavior (inherent to any spec); the only revealed fact — corrected fragment is 'DISTINCT ' with a trailing space placed before the argument text — is exactly what the public problem_statement states. The spec view carries NO gold-patch specifics beyond the public statement: no extra_context['distinct'], no aggregates.py/file-line refs, no Python literal or `%(function)s` template, no COUNT/CASE example. Those mechanism details live only in mapping.md/refinement.md, which are NOT part of the spec view. Comments are abstract, not verbatim quotes of gold or problem_statement.

Checks: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical across variants; the differing edit is confined to the elided impl region). Solution.lean compiles clean, exit 0, real proof (`cases distinct <;> rfl`), no sorry. spec_provenance=cold. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
