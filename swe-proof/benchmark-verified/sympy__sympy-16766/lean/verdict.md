# P2 adversarial audit — sympy__sympy-16766

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
   let joined := String.intercalate ", " subscripts
-  return base ++ "[" ++ joined ++ "]"
+  return base ++ "(" ++ joined ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,7 @@
 -- impl-start
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
-  let joined := String.intercalate ", " subscripts
+  let joined := String.intercalate "," subscripts
   return base ++ "[" ++ joined ++ "]"
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,6 +37,8 @@
 -- impl-start
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
+  if subscripts = [] then
+    return base
   let joined := String.intercalate ", " subscripts
   return base ++ "[" ++ joined ++ "]"
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
   let joined := String.intercalate ", " subscripts
-  return base ++ "[" ++ joined ++ "]"
+  return "[" ++ base ++ joined ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
   let joined := String.intercalate ", " subscripts
-  return base ++ "[" ++ joined ++ "]"
+  return base ++ "[" ++ joined
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,7 @@
 -- impl-start
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
-  let joined := String.intercalate ", " subscripts
+  let joined := String.intercalate " ," subscripts
   return base ++ "[" ++ joined ++ "]"
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,8 +37,7 @@
 -- impl-start
 def implementation_indexedCode (base : String) (subscripts : List String) :
     String := Id.run do
-  let joined := String.intercalate ", " subscripts
-  return base ++ "[" ++ joined ++ "]"
+  return "# Not supported"
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an array element access as a line of Python source code.

An indexed access is written by a code printer as the array's name followed by
its subscripts in square brackets, the subscripts separated by `", "` — e.g. a
base named `p` accessed at subscripts `0, 1` is rendered `p[0, 1]`. The name and
each already-rendered subscript are supplied as inputs (each subscript is the
string a printer produces for that index expression).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the rendered base name
-- and the rendered subscripts are supplied as inputs (the outputs of the
-- ambient recursive printer), and the formatting is spelled out concretely.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The rendered indexed access is the base name, then the subscript strings
joined by `", "` enclosed in a single pair of square brackets. Every component
of the result is pinned to the inputs: the prefix is exactly `base`, the bracket
content is exactly the comma-joined subscripts, and the brackets are literal. -/
def problem_spec_indexedCode (base : String) (subscripts : List String)
    (result : String) : Prop :=
  result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"
-- post-conditions-end

-- impl-start
def implementation_indexedCode (base : String) (subscripts : List String) :
    String := Id.run do
  let joined := String.intercalate ", " subscripts
  return base ++ "[" ++ joined ++ "]"
-- impl-end

-- proof-start
theorem correct_indexedCode :
    ∀ (base : String) (subscripts : List String),
      problem_spec_indexedCode base subscripts
        (implementation_indexedCode base subscripts) := by
  intro base subscripts
  unfold problem_spec_indexedCode implementation_indexedCode
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_indexedCode is a TOTAL EXACT functional equality: result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]". No domain slack, no disjunctive/existential slack, no axioms declared or consumed (axioms region empty). Any impl closing correct_indexedCode with clean axioms must equal the gold function on every (base, subscripts), hence is behaviorally identical and its faithful patch would resolve => verify implies correct on the A side trivially (no A-legs exist).

SAME-SPEC: all 8 files (pos + atk_1..7) pass swebench_unified.markers.same_spec == True with Solution.lean (header axioms/pure/pre/post byte-identical; only impl+proof region edited).

POSITIVE CONTROL (pos.lean, exact gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0. Axiom check: appended `#print axioms correct_indexedCode` (pos_axcheck.lean) -> "'correct_indexedCode' does not depend on any axioms", exit 0. CLEAN.

ATTACKS (all `bash scripts/lean_verify.sh .../atk_N.lean`, all DISTINCT wrong impls, all exit 1 = genuine `rfl` proof failure 'Tactic rfl failed: The left-hand side ...', NOT build/syntax errors -> none verifies -> no patch to materialize/resolve):
  atk_1: brackets -> parens `base++"("++joined++")"` (control-flow/delimiter) exit=1
  atk_2: separator `","` instead of `", "` (boundary) exit=1
  atk_3: partial-domain special-case: if subscripts=[] then return base (partial-domain) exit=1
  atk_4: order swap `"["++base++joined++"]"` (prefix/structure) exit=1
  atk_5: missing closing bracket `base++"["++joined` (boundary/truncation) exit=1
  atk_6: separator `" ,"` (space-before-comma) exit=1
  atk_7: ungrounded-oracle echo of prepatch: return "# Not supported" (constant, ignores inputs) exit=1

PREPATCH REPRODUCED: atk_7 == prepatch skeleton behavior (returns fixed "# Not supported" marker); carried gold `rfl` proof fails to close, matching refinement.md G-DIFF (`pure "# Not supported" != base ++ "["+...`). true.

refinement.md AUDIT: axioms region empty (grep confirms no `axiom`); every leg is R or I (2 R inputs, 2 I ops); NO A-consumed / A-reference / kind-3 legs => the A-leg correspondence obligation is vacuous. R/I legs are G-CONF's job (mechanically covered). No falsification surface on the A side.

CONCLUSION: >=5 distinct same-spec wrong impls (7 total) attempted; none produces a closing clean-axiom proof, so no verify-not-correct witness exists. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an array element access as a line of Python source code.

An indexed access is written by a code printer as the array's name followed by
its subscripts in square brackets, the subscripts separated by `", "` — e.g. a
base named `p` accessed at subscripts `0, 1` is rendered `p[0, 1]`. The name and
each already-rendered subscript are supplied as inputs (each subscript is the
string a printer produces for that index expression).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the rendered base name
-- and the rendered subscripts are supplied as inputs (the outputs of the
-- ambient recursive printer), and the formatting is spelled out concretely.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The rendered indexed access is the base name, then the subscript strings
joined by `", "` enclosed in a single pair of square brackets. Every component
of the result is pinned to the inputs: the prefix is exactly `base`, the bracket
content is exactly the comma-joined subscripts, and the brackets are literal. -/
def problem_spec_indexedCode (base : String) (subscripts : List String)
    (result : String) : Prop :=
  result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"
-- post-conditions-end

-- impl-start
def implementation_indexedCode (base : String) (subscripts : List String) :
    String := Id.run do
  let joined := String.intercalate ", " subscripts
  return base ++ "[" ++ joined ++ "]"
-- impl-end

-- proof-start
theorem correct_indexedCode :
    ∀ (base : String) (subscripts : List String),
      problem_spec_indexedCode base subscripts
        (implementation_indexedCode base subscripts) := by
  intro base subscripts
  unfold problem_spec_indexedCode implementation_indexedCode
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_indexedCode is a TOTAL EXACT functional equality: result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]". No domain slack, no disjunctive/existential slack, no axioms declared or consumed (axioms region empty). Any impl closing correct_indexedCode with clean axioms must equal the gold function on every (base, subscripts), hence is behaviorally identical and its faithful patch would resolve => verify implies correct on the A side trivially (no A-legs exist).

SAME-SPEC: all 8 files (pos + atk_1..7) pass swebench_unified.markers.same_spec == True with Solution.lean (header axioms/pure/pre/post byte-identical; only impl+proof region edited).

POSITIVE CONTROL (pos.lean, exact gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0. Axiom check: appended `#print axioms correct_indexedCode` (pos_axcheck.lean) -> "'correct_indexedCode' does not depend on any axioms", exit 0. CLEAN.

ATTACKS (all `bash scripts/lean_verify.sh .../atk_N.lean`, all DISTINCT wrong impls, all exit 1 = genuine `rfl` proof failure 'Tactic rfl failed: The left-hand side ...', NOT build/syntax errors -> none verifies -> no patch to materialize/resolve):
  atk_1: brackets -> parens `base++"("++joined++")"` (control-flow/delimiter) exit=1
  atk_2: separator `","` instead of `", "` (boundary) exit=1
  atk_3: partial-domain special-case: if subscripts=[] then return base (partial-domain) exit=1
  atk_4: order swap `"["++base++joined++"]"` (prefix/structure) exit=1
  atk_5: missing closing bracket `base++"["++joined` (boundary/truncation) exit=1
  atk_6: separator `" ,"` (space-before-comma) exit=1
  atk_7: ungrounded-oracle echo of prepatch: return "# Not supported" (constant, ignores inputs) exit=1

PREPATCH REPRODUCED: atk_7 == prepatch skeleton behavior (returns fixed "# Not supported" marker); carried gold `rfl` proof fails to close, matching refinement.md G-DIFF (`pure "# Not supported" != base ++ "["+...`). true.

refinement.md AUDIT: axioms region empty (grep confirms no `axiom`); every leg is R or I (2 R inputs, 2 I ops); NO A-consumed / A-reference / kind-3 legs => the A-leg correspondence obligation is vacuous. R/I legs are G-CONF's job (mechanically covered). No falsification surface on the A side.

CONCLUSION: >=5 distinct same-spec wrong impls (7 total) attempted; none produces a closing clean-axiom proof, so no verify-not-correct witness exists. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. The Lean model implementation_indexedCode/problem_spec_indexedCode = `base ++ "[" ++ String.intercalate ", " subscripts ++ "]"` is a byte-exact transliteration of the gold-patched real callee PythonCodePrinter._print_Indexed = `"{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))`. Modeling boundary is correct: str(base) and self._print(ind) are UNCHANGED by the patch, so their outputs are legitimately taken as the inputs base/subscripts; the only patched op (string assembly) is modeled deeply. Verified: (1) Solution.lean compiles via lean_verify.sh exit 0; (2) #print axioms correct_indexedCode = 'does not depend on any axioms' — genuine rfl proof, no sorryAx; (3) same_spec(Solution, Solution_prepatch, lean backend) = True (spec region byte-identical); (4) String.intercalate ", " == ", ".join on empty/single/multi lists, and format string maps to literal-bracket concat exactly; (5) recorded G-CONF ran 120005 differential draws vs the real method with 0 disagreements. The spec is not over-strong — it pins the output to precisely the assembly the code performs, with no extra constraints (empty-subscript list is an admitted harmless superset, never a disagreement). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (markers.spec_view, lean backend) contains only: (1) a doc comment paraphrasing the array-access rendering with the p[0,1] example; (2) empty axioms/pure stubs; (3) the post-condition `problem_spec_indexedCode ... result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"`; impl and proof are correctly elided ('supplied by the consumer'). The gold edit is ALREADY FULLY PUBLIC in problem_statement, which literally reproduces the entire method to add: `def _print_Indexed(self, expr): base, *index = expr.args; return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))`, plus the worked example (`pycode(p[0])` emits the '# Not supported' marker). patch.diff is byte-for-byte that method. So the format string `{}[{}]`, the comma-space join, and the bracketed base[i1,i2,...] form are entirely disclosed by the public statement; the post-condition is only a faithful formalization of it and reveals nothing beyond problem_statement. Verified same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) == True: the graded spec region (axioms/pure/post-conditions) is byte-identical between gold and prepatch, so the fix (which lives solely in the elided impl/proof) cannot be smuggled through the spec. hints_text is empty and excluded regardless. No spec-view line names a non-public implementation detail, hidden callee contract, or edge case. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
