# P2 adversarial audit — sympy__sympy-19637

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,18 +33,17 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
   let mut hit : Bool := false
   if parenBranch then
     if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
       hit := true
     else
-      -- no space was present, so the flag stays unset
-      hit := false
+      -- BUG: flag left set on the no-space boundary
+      hit := true
   return Except.ok hit
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,19 +33,12 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
-  let mut hit : Bool := false
-  if parenBranch then
-    if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
-      hit := true
-    else
-      -- no space was present, so the flag stays unset
-      hit := false
-  return Except.ok hit
+  -- BUG: gate dropped; flag depends only on space presence
+  return Except.ok (s.contains ' ')
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,19 +33,17 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
   let mut hit : Bool := false
   if parenBranch then
     if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
       hit := true
     else
-      -- no space was present, so the flag stays unset
       hit := false
-  return Except.ok hit
+  return Except.ok (parenBranch && s.contains ' ')
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,19 +33,12 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
-  let mut hit : Bool := false
-  if parenBranch then
-    if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
-      hit := true
-    else
-      -- no space was present, so the flag stays unset
-      hit := false
-  return Except.ok hit
+  -- BUG: disjunction instead of conjunction
+  return Except.ok (parenBranch || s.contains ' ')
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,18 +33,17 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
   let mut hit : Bool := false
   if parenBranch then
     if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
       hit := true
     else
-      -- no space was present, so the flag stays unset
-      hit := false
+      -- BUG: aborts on the no-space boundary (the pre-patch crash)
+      return Except.error ()
   return Except.ok hit
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,19 +33,12 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
-  let mut hit : Bool := false
-  if parenBranch then
-    if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
-      hit := true
-    else
-      -- no space was present, so the flag stays unset
-      hit := false
-  return Except.ok hit
+  -- BUG: tests for a tab, not a space
+  return Except.ok (parenBranch && s.contains '\t')
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,19 +33,12 @@
   result = Except.ok (parenBranch && s.contains ' ')
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_kernSHit
     (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
-  let mut hit : Bool := false
-  if parenBranch then
-    if s.contains ' ' then
-      -- a fresh marker is substituted for the spaces, so it now occurs in the
-      -- string: the membership test yields `true`
-      hit := true
-    else
-      -- no space was present, so the flag stays unset
-      hit := false
-  return Except.ok hit
+  -- BUG: negated gate
+  return Except.ok (!parenBranch && s.contains ' ')
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the flag-computation slice of a string-preprocessing
helper. The routine has an optional bracket-handling branch; within it a marker
is substituted for any spaces and a membership flag is computed. The desired
behaviour: the flag is computed for every input that enters the branch — never
left undefined — so an input that enters the branch without producing a space
yields an unset flag rather than aborting the routine.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the marker-membership step is
-- modeled DEEPLY (its value is determined by whether a space is present, below)
-- rather than axiomatized, and validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone functional helper is needed: the flag is the boolean
-- conjunction of the branch gate and space-presence, computed inline.
-- pure-end

-- post-conditions-start
/-- The result is always a well-defined flag (the routine never aborts). The
flag is set exactly when the bracket-handling branch is active AND the string
contains a space at the marker-substitution point: in that case a fresh marker
is substituted for the spaces and is therefore present, so the membership flag
is set; in every other case the flag is unset. -/
def problem_spec_kernSHit
    (parenBranch : Bool) (s : List Char) (result : Except Unit Bool) : Prop :=
  result = Except.ok (parenBranch && s.contains ' ')
-- post-conditions-end

-- impl-start
def implementation_kernSHit
    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
  let mut hit : Bool := false
  if parenBranch then
    if s.contains ' ' then
      -- a fresh marker is substituted for the spaces, so it now occurs in the
      -- string: the membership test yields `true`
      hit := true
    else
      -- no space was present, so the flag stays unset
      hit := false
  return Except.ok hit
-- impl-end

-- proof-start
theorem correct_kernSHit : ∀ (parenBranch : Bool) (s : List Char),
    problem_spec_kernSHit parenBranch s (implementation_kernSHit parenBranch s) := by
  intro parenBranch s
  unfold problem_spec_kernSHit implementation_kernSHit
  cases parenBranch <;> cases s.contains ' ' <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_kernSHit pins result = Except.ok (parenBranch && s.contains ' ') as a TOTAL exact-equality postcondition over all inputs, so any verifying impl must compute exactly the gold value on every input. Same_spec=True verified for all 7 attacks + pos_control (header lines 1-35 byte-identical; only impl+proof regions edited).

### VERIFICATION RESULTS (scripts/lean_verify.sh, cap 300s, run concurrently in batches of 4):
- pos_control (gold) EXIT=0; #print axioms => 'does not depend on any axioms'.
- atk_1 (boundary: parenBranch&&no-space returns true) EXIT=1, rfl failed (spec mismatch).
- atk_2 (control-flow: gate dropped, flag = s.contains ' ') EXIT=1, rfl failed.
- atk_3 (behavioral ECHO: returns Except.ok (parenBranch && s.contains ' ')) EXIT=0; #print axioms clean ('does not depend on any axioms').
- atk_4 (OR instead of AND) EXIT=1, rfl failed.
- atk_5 (partial-domain: returns Except.error () on the no-space boundary = the pre-patch crash) EXIT=1, rfl failed.
- atk_6 (wrong membership char '\t' instead of space) EXIT=1, rfl failed.
- atk_7 (negated gate !parenBranch) EXIT=1, rfl failed.
All six wrong impls fail because rfl genuinely cannot close the goal (real spec mismatch), NOT a syntax/typo error (confirmed from logs).

MANDATORY RESOLVE STEP: the ONLY non-gold impl whose proof closes with clean axioms is atk_3, which is a behavioral echo of the gold value. Its faithful refined patch equals the gold patch. Materialized to atk_3.patch and RAN through the official harness: run_resolve('sympy__sympy-19637', patch) => COMPLETED=True, RESOLVED=True, NOTE='resolved'. So the verifying candidate's faithful patch DOES resolve — verify does NOT contradict correct here. (This matches the fixed G-EQ/panel_1 policy: a same-spec verifying echo whose patch resolves is not a weakness.)

PREPATCH REPRODUCED: Solution_prepatch.lean models the UnboundLocalError as Except.error () on parenBranch=true & no-space. Replacing its sorry with the gold tactic (prepatch_repro.lean) => lean_verify EXIT=1, rfl failed at the Except.error () branch — confirms the prepatch impl cannot satisfy the frozen spec (G-DIFF signal reproduced).

REFINEMENT.MD AUDIT: 6 legs, all R/A-reference/I, NO kind-3 (changed-inexpressible). Rows 1,5,6 = I; rows 2,3 = R (bool predicate / str-in-membership refinements); row 4 = A-reference (hit:=true <-> kern in s). A-reference correspondence holds: the freshness loop (while kern in s: kern+=choice) guarantees kern absent before s.replace(' ',kern), so with >=1 space present kern necessarily occurs afterward => kern in s is True; when no space present the marker is unbound and hit stays False. Modeled deeply as parenBranch && s.contains ' ', validated by G-AX (pass: 9411 space-present probes, seed 19637) and G-CONF (pass: 120014 inputs, 0 disagreements). No A-consumed legs; axioms region empty and pos_control/atk_3 both print no axiom dependencies. A-leg <-> real post-patch kernS flag correspondence is sound.

CONCLUSION: >=6 distinct wrong-impl attacks (partial-domain atk_5, boundary atk_1/atk_6, control-flow-effect atk_2, ungrounded-oracle/logic-flip atk_4/atk_7) all FAIL to verify; the single verifying echo (atk_3) has a materialized faithful patch that RESOLVES under the harness. No verify=>~correct counterexample exists. Spec is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the flag-computation slice of a string-preprocessing
helper. The routine has an optional bracket-handling branch; within it a marker
is substituted for any spaces and a membership flag is computed. The desired
behaviour: the flag is computed for every input that enters the branch — never
left undefined — so an input that enters the branch without producing a space
yields an unset flag rather than aborting the routine.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the marker-membership step is
-- modeled DEEPLY (its value is determined by whether a space is present, below)
-- rather than axiomatized, and validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone functional helper is needed: the flag is the boolean
-- conjunction of the branch gate and space-presence, computed inline.
-- pure-end

-- post-conditions-start
/-- The result is always a well-defined flag (the routine never aborts). The
flag is set exactly when the bracket-handling branch is active AND the string
contains a space at the marker-substitution point: in that case a fresh marker
is substituted for the spaces and is therefore present, so the membership flag
is set; in every other case the flag is unset. -/
def problem_spec_kernSHit
    (parenBranch : Bool) (s : List Char) (result : Except Unit Bool) : Prop :=
  result = Except.ok (parenBranch && s.contains ' ')
-- post-conditions-end

-- impl-start
def implementation_kernSHit
    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
  let mut hit : Bool := false
  if parenBranch then
    if s.contains ' ' then
      -- a fresh marker is substituted for the spaces, so it now occurs in the
      -- string: the membership test yields `true`
      hit := true
    else
      -- no space was present, so the flag stays unset
      hit := false
  return Except.ok hit
-- impl-end

-- proof-start
theorem correct_kernSHit : ∀ (parenBranch : Bool) (s : List Char),
    problem_spec_kernSHit parenBranch s (implementation_kernSHit parenBranch s) := by
  intro parenBranch s
  unfold problem_spec_kernSHit implementation_kernSHit
  cases parenBranch <;> cases s.contains ' ' <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_kernSHit pins result = Except.ok (parenBranch && s.contains ' ') as a TOTAL exact-equality postcondition over all inputs, so any verifying impl must compute exactly the gold value on every input. Same_spec=True verified for all 7 attacks + pos_control (header lines 1-35 byte-identical; only impl+proof regions edited).

### VERIFICATION RESULTS (scripts/lean_verify.sh, cap 300s, run concurrently in batches of 4):
- pos_control (gold) EXIT=0; #print axioms => 'does not depend on any axioms'.
- atk_1 (boundary: parenBranch&&no-space returns true) EXIT=1, rfl failed (spec mismatch).
- atk_2 (control-flow: gate dropped, flag = s.contains ' ') EXIT=1, rfl failed.
- atk_3 (behavioral ECHO: returns Except.ok (parenBranch && s.contains ' ')) EXIT=0; #print axioms clean ('does not depend on any axioms').
- atk_4 (OR instead of AND) EXIT=1, rfl failed.
- atk_5 (partial-domain: returns Except.error () on the no-space boundary = the pre-patch crash) EXIT=1, rfl failed.
- atk_6 (wrong membership char '\t' instead of space) EXIT=1, rfl failed.
- atk_7 (negated gate !parenBranch) EXIT=1, rfl failed.
All six wrong impls fail because rfl genuinely cannot close the goal (real spec mismatch), NOT a syntax/typo error (confirmed from logs).

MANDATORY RESOLVE STEP: the ONLY non-gold impl whose proof closes with clean axioms is atk_3, which is a behavioral echo of the gold value. Its faithful refined patch equals the gold patch. Materialized to atk_3.patch and RAN through the official harness: run_resolve('sympy__sympy-19637', patch) => COMPLETED=True, RESOLVED=True, NOTE='resolved'. So the verifying candidate's faithful patch DOES resolve — verify does NOT contradict correct here. (This matches the fixed G-EQ/panel_1 policy: a same-spec verifying echo whose patch resolves is not a weakness.)

PREPATCH REPRODUCED: Solution_prepatch.lean models the UnboundLocalError as Except.error () on parenBranch=true & no-space. Replacing its sorry with the gold tactic (prepatch_repro.lean) => lean_verify EXIT=1, rfl failed at the Except.error () branch — confirms the prepatch impl cannot satisfy the frozen spec (G-DIFF signal reproduced).

REFINEMENT.MD AUDIT: 6 legs, all R/A-reference/I, NO kind-3 (changed-inexpressible). Rows 1,5,6 = I; rows 2,3 = R (bool predicate / str-in-membership refinements); row 4 = A-reference (hit:=true <-> kern in s). A-reference correspondence holds: the freshness loop (while kern in s: kern+=choice) guarantees kern absent before s.replace(' ',kern), so with >=1 space present kern necessarily occurs afterward => kern in s is True; when no space present the marker is unbound and hit stays False. Modeled deeply as parenBranch && s.contains ' ', validated by G-AX (pass: 9411 space-present probes, seed 19637) and G-CONF (pass: 120014 inputs, 0 disagreements). No A-consumed legs; axioms region empty and pos_control/atk_3 both print no axiom dependencies. A-leg <-> real post-patch kernS flag correspondence is sound.

CONCLUSION: >=6 distinct wrong-impl attacks (partial-domain atk_5, boundary atk_1/atk_6, control-flow-effect atk_2, ungrounded-oracle/logic-flip atk_4/atk_7) all FAIL to verify; the single verifying echo (atk_3) has a materialized faithful patch that RESOLVES under the harness. No verify=>~correct counterexample exists. Spec is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find any divergence. (1) Spec region byte-identical across the twin: same_spec(Solution, Solution_prepatch)=True, so the frozen spec problem_spec_kernSHit := result = Except.ok (parenBranch && s.contains ' ') is not impl-tailored. (2) Solution.lean compiles clean (lean_verify exit 0) and #print axioms correct_kernSHit reports no axiom dependence — genuine proof, no sorryAx. Real callee kernS post-patch (base_commit 63f8f465d4, gold already applied per git diff: `hit = kern in s` relocated inside `if ' ' in s:` plus new `else: hit=False`) computes the modeled hit-flag slice (lines 471-516) exactly as parenBranch && (space present at line 510): parenBranch=false → hit False; parenBranch=true & space present → fresh kern (kept absent from pre-subst s by the while loop) is substituted for the spaces, so kern in s is necessarily True → hit True; parenBranch=true & no space → else branch → hit False. All three match the spec on every input in the modeled domain. (4) The spec's total-okness (never Except.error) is faithful for THIS slice: post-patch there is no UnboundLocalError (that was the bug, captured only by the prepatch twin). The SympifyError('unmatched left parenthesis') abort sits at ~line 475, BEFORE the modeled input point s@510 (which is defined post-balance-check, post-rewrites) — outside the modeled slice, a documented slicing boundary in mapping.md, not spec drift. (5) conformance_check.py: 120,014 fuzzed inputs (seed 19637), 0 disagreements. No spec-too-strong / drift defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean) computed and screened. Mechanical G-LEAK screen: PASSED (no diff markers, no reproduced gold-patch lines, no patched file/module path, no narration terms, no patched repo symbol beyond the public 'kernS'). same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical. Public problem_statement ALREADY discloses: the function kernS, the exact buggy line 'hit = kern in s', and the failure 'UnboundLocalError: local variable kern referenced before assignment'. The gold edit (move 'hit = kern in s' inside `if ' ' in s:`, add `else: hit = False`) is NOT reconstructible from the spec view: the view only states the abstract postcondition result = Except.ok (parenBranch && s.contains ' ') and prose about a well-defined flag / never aborting — legitimate behavioral spec, and the abort/crash it alludes to is already public. Identifier kernSHit embeds 'kernS' but that symbol is in the problem statement, so exempt (correctly not flagged). The diff-quoting/'pre-patch'/'gold' text lives ONLY in refinement.md and mapping.md, which are internal derivation/audit artifacts, NOT the consumer spec view, hence out of scope. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
