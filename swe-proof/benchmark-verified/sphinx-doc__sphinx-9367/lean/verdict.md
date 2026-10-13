# P2 adversarial audit — sphinx-doc__sphinx-9367

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,8 @@
 
 -- impl-start
 def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
   if elts.length == 0 then
     return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
   else
     return "(" ++ String.intercalate ", " elts ++ ")"
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,11 +58,9 @@
 
 -- impl-start
 def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
   if elts.length == 0 then
     return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
+  else if elts.length == 2 then
     return "(" ++ elts.headI ++ ",)"
   else
     return "(" ++ String.intercalate ", " elts ++ ")"
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,15 +57,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
-  if elts.length == 0 then
-    return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
-  else
-    return "(" ++ String.intercalate ", " elts ++ ")"
+def implementation_renderTuple (elts : List String) : String :=
+  match elts with
+  | [] => "()"
+  | [e] => "(" ++ e ++ ")"
+  | _ => "(" ++ String.intercalate ", " elts ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,15 +57,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
-  if elts.length == 0 then
-    return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
-  else
-    return "(" ++ String.intercalate ", " elts ++ ")"
+def implementation_renderTuple (elts : List String) : String :=
+  match elts with
+  | [] => "()"
+  | [e] => "(" ++ e ++ ",)"
+  | _ => "(" ++ String.intercalate "," elts ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,15 +57,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
-  if elts.length == 0 then
-    return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
-  else
-    return "(" ++ String.intercalate ", " elts ++ ")"
+def implementation_renderTuple (elts : List String) : String :=
+  match elts with
+  | [] => ""
+  | [e] => "(" ++ e ++ ",)"
+  | _ => "(" ++ String.intercalate ", " elts ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,15 +57,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
-  if elts.length == 0 then
-    return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
-  else
-    return "(" ++ String.intercalate ", " elts ++ ")"
+def implementation_renderTuple (elts : List String) : String :=
+  match elts with
+  | [] => "()"
+  | [e] => "(" ++ e ++ ",)"
+  | _ => "(" ++ String.intercalate ", " elts ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,15 +57,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderTuple (elts : List String) : String := Id.run do
-  -- Distinguish the tuple's rendered form by how many components it has.
-  if elts.length == 0 then
-    return "()"
-  else if elts.length == 1 then
-    -- a one-component tuple keeps its trailing comma
-    return "(" ++ elts.headI ++ ",)"
-  else
-    return "(" ++ String.intercalate ", " elts ++ ")"
+def implementation_renderTuple (elts : List String) : String :=
+  match elts with
+  | [] => "()"
+  | [e] => "(" ++ e ++ ",)"
+  | [a, b] => "(" ++ String.intercalate ", " [a, b] ++ ")"
+  | _ => "(" ++ String.intercalate ", " elts ++ "))"
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a tuple expression to its source-text form.

A tuple is a parenthesized, comma-separated sequence of component expressions.
Its rendered form is built from the already-rendered text of its components by
wrapping them in parentheses with `", "` between consecutive components.

Three shapes are distinguished by how many components the tuple has:

  * with no components the rendered form is the empty pair of parentheses;
  * with exactly one component the rendered form is that component wrapped in
    parentheses WITH a trailing comma, so it reads as a one-element tuple rather
    than a merely parenthesized expression;
  * with two or more components the rendered form is the components joined by
    `", "` and wrapped in parentheses.

The per-component rendering is itself an unchanged step; here each component
arrives already rendered to text, so the behavior pinned below is exactly "how
the rendered component pieces are wrapped and joined for each arity."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-component
-- rendering step (turning one component expression into its source text) is the
-- SAME operation in every branch and is unaffected by the modeled change; here
-- it is absorbed into the input, which is the list of already-rendered component
-- strings. The modeled change is solely HOW those rendered pieces are wrapped and
-- joined as a function of the component count, so the result is pinned for every
-- possible per-component renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- parenthesized join of the already-rendered component strings, with the
-- one-component case carrying a trailing comma.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the input component list, by arity:

  * empty list  ⇒ the empty parentheses `"()"`;
  * a single component `e` ⇒ `"(" ++ e ++ ",)"` (parentheses WITH a trailing
    comma);
  * two or more components ⇒ `"("` then the components joined by `", "` then
    `")"`.

No output component is left free: the result is determined for every arity. -/
def problem_spec_renderTuple (elts : List String) (result : String) : Prop :=
  match elts with
  | [] => result = "()"
  | [e] => result = "(" ++ e ++ ",)"
  | _ => result = "(" ++ String.intercalate ", " elts ++ ")"
-- post-conditions-end

-- impl-start
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"
-- impl-end

-- proof-start
theorem correct_renderTuple :
    ∀ (elts : List String),
      problem_spec_renderTuple elts (implementation_renderTuple elts) := by
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] => rfl
  | a :: b :: rest => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec problem_spec_renderTuple is a TOTAL, TIGHT functional spec: it pins `result` to a unique string for every arity ([]->"()", [e]->"("++e++",)", >=2->"("++intercalate ++")"). Any verifying impl must therefore be pointwise-equal to gold on observable output; there is no observably-divergent spec-satisfier.

ATTACKS (7, all same_spec=True via swebench_unified.markers.same_spec; verified concurrently <=4 at a time with `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (single component -> "(e)", no trailing comma): exit=1. Fails exactly on the [e] clause: rfl error `"("++e++")" != "("++e++",)"`. Prepatch reproduced.
- atk_2 arity shift (trailing comma on 2-elt instead of 1-elt): exit=1.
- atk_3 control-flow variant (match, single -> "(e)" no comma): exit=1.
- atk_4 wrong separator (intercalate "," instead of ", " for >=2): exit=1.
- atk_5 boundary (empty -> "" instead of "()"): exit=1.
- atk_7 partial-domain (correct on 0/1/2, extra ")" on arity>=3): exit=1.
- atk_6 ungrounded-oracle echo (gold-equivalent match impl): exit=0, `#print axioms correct_renderTuple` => 'does not depend on any axioms' (clean, no sorry).
pos_control (gold impl verbatim): exit=0, clean axioms.

MANDATORY RESOLVE: atk_6 is the ONLY verifying wrong-impl. Its faithful Python patch is byte-identical to the gold visit_Tuple patch (diff shows IDENTICAL). Executed through official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9367', patch, timeout=1800, retries=0): RESOLVED=True, completed=True, note='resolved'. Therefore NO verified-but-not-resolved impl exists.

REFINEMENT AUDIT: legs = op1 (I, empty branch), op2 (R, fixed single-component trailing-comma), op3 (R, >=2 join), op4 (A-reference, per-component self.visit absorbed into input elts:List String, bound to real recursive visitor in G-CONF). No A-consumed, no kind-3 deep-model leg. meta.json axioms=[]; grep confirms NO axiom/opaque declarations in Solution.lean. The A-reference is sound: self.visit is unchanged by the patch, so absorbing it into the already-rendered input is faithful and the wrap/join logic (the actual modeled change) is isolated. Correspondence holds.

Commands used:
- same_spec: python -c 'from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ... ' => all 7 True.
- axioms: appended `#print axioms correct_renderTuple`, re-verified atk_6/pos_control => clean.
- resolve: run_resolve on atk_6.patch => RESOLVED=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a tuple expression to its source-text form.

A tuple is a parenthesized, comma-separated sequence of component expressions.
Its rendered form is built from the already-rendered text of its components by
wrapping them in parentheses with `", "` between consecutive components.

Three shapes are distinguished by how many components the tuple has:

  * with no components the rendered form is the empty pair of parentheses;
  * with exactly one component the rendered form is that component wrapped in
    parentheses WITH a trailing comma, so it reads as a one-element tuple rather
    than a merely parenthesized expression;
  * with two or more components the rendered form is the components joined by
    `", "` and wrapped in parentheses.

The per-component rendering is itself an unchanged step; here each component
arrives already rendered to text, so the behavior pinned below is exactly "how
the rendered component pieces are wrapped and joined for each arity."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-component
-- rendering step (turning one component expression into its source text) is the
-- SAME operation in every branch and is unaffected by the modeled change; here
-- it is absorbed into the input, which is the list of already-rendered component
-- strings. The modeled change is solely HOW those rendered pieces are wrapped and
-- joined as a function of the component count, so the result is pinned for every
-- possible per-component renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- parenthesized join of the already-rendered component strings, with the
-- one-component case carrying a trailing comma.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the input component list, by arity:

  * empty list  ⇒ the empty parentheses `"()"`;
  * a single component `e` ⇒ `"(" ++ e ++ ",)"` (parentheses WITH a trailing
    comma);
  * two or more components ⇒ `"("` then the components joined by `", "` then
    `")"`.

No output component is left free: the result is determined for every arity. -/
def problem_spec_renderTuple (elts : List String) (result : String) : Prop :=
  match elts with
  | [] => result = "()"
  | [e] => result = "(" ++ e ++ ",)"
  | _ => result = "(" ++ String.intercalate ", " elts ++ ")"
-- post-conditions-end

-- impl-start
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"
-- impl-end

-- proof-start
theorem correct_renderTuple :
    ∀ (elts : List String),
      problem_spec_renderTuple elts (implementation_renderTuple elts) := by
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] => rfl
  | a :: b :: rest => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec problem_spec_renderTuple is a TOTAL, TIGHT functional spec: it pins `result` to a unique string for every arity ([]->"()", [e]->"("++e++",)", >=2->"("++intercalate ++")"). Any verifying impl must therefore be pointwise-equal to gold on observable output; there is no observably-divergent spec-satisfier.

ATTACKS (7, all same_spec=True via swebench_unified.markers.same_spec; verified concurrently <=4 at a time with `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (single component -> "(e)", no trailing comma): exit=1. Fails exactly on the [e] clause: rfl error `"("++e++")" != "("++e++",)"`. Prepatch reproduced.
- atk_2 arity shift (trailing comma on 2-elt instead of 1-elt): exit=1.
- atk_3 control-flow variant (match, single -> "(e)" no comma): exit=1.
- atk_4 wrong separator (intercalate "," instead of ", " for >=2): exit=1.
- atk_5 boundary (empty -> "" instead of "()"): exit=1.
- atk_7 partial-domain (correct on 0/1/2, extra ")" on arity>=3): exit=1.
- atk_6 ungrounded-oracle echo (gold-equivalent match impl): exit=0, `#print axioms correct_renderTuple` => 'does not depend on any axioms' (clean, no sorry).
pos_control (gold impl verbatim): exit=0, clean axioms.

MANDATORY RESOLVE: atk_6 is the ONLY verifying wrong-impl. Its faithful Python patch is byte-identical to the gold visit_Tuple patch (diff shows IDENTICAL). Executed through official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9367', patch, timeout=1800, retries=0): RESOLVED=True, completed=True, note='resolved'. Therefore NO verified-but-not-resolved impl exists.

REFINEMENT AUDIT: legs = op1 (I, empty branch), op2 (R, fixed single-component trailing-comma), op3 (R, >=2 join), op4 (A-reference, per-component self.visit absorbed into input elts:List String, bound to real recursive visitor in G-CONF). No A-consumed, no kind-3 deep-model leg. meta.json axioms=[]; grep confirms NO axiom/opaque declarations in Solution.lean. The A-reference is sound: self.visit is unchanged by the patch, so absorbing it into the already-rendered input is faithful and the wrap/join logic (the actual modeled change) is isolated. Correspondence holds.

Commands used:
- same_spec: python -c 'from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ... ' => all 7 True.
- axioms: appended `#print axioms correct_renderTuple`, re-verified atk_6/pos_control => clean.
- resolve: run_resolve on atk_6.patch => RESOLVED=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift from real callee) check for sphinx-doc__sphinx-9367, modeling _UnparseVisitor.visit_Tuple (sphinx/pycode/ast.py, post-patch).

### Checks performed
1. lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). #print axioms correct_renderTuple -> 'does not depend on any axioms' (real proof, no sorryAx).
2. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (diff of post-conditions-start..end block is empty). The prepatch impl (two-way emptiness split) renders a single component as '(e)' and genuinely FAILS the spec's [e] clause ('(e)' != '(e,)'), so the discriminating clause is real, not degenerate; G-DIFF/G-GOLD consistent.
3. Faithfulness vs real repo: modeled spec branches are
   [] -> "()"; [e] -> "("++e++",)"; _ -> "("++intercalate ", " elts++")".
   Confirmed the real post-patch visit_Tuple (verified in worktree and others, e.g. base-commit-equivalent source) is exactly: len==0 -> "()"; len==1 -> "(%s,)"%visit(e0); else -> "("+", ".join+")". Op-for-op match.
4. The abstraction absorbing the recursive per-component self.visit into the input elts:List String is legitimate: visit_Tuple consumes its children ONLY through self.visit(e), and the patch changes only the wrap/join logic, not the per-component renderer. Spec therefore holds for every component renderer and pins exactly the modeled change.
5. Ran a direct differential test of the shadow wrap/join against the REAL patched sphinx.pycode.ast.unparse over empty/one/two/three/nested/lambda/list/atomic tuple cases: 0 disagreements. Consistent with recorded G-CONF (100000 fuzzed inputs, 0 disagreements).

Searched for a diverging input across all three arities and nested/edge component shapes; found none. The spec is fully-pinned (result determined for every arity) but NOT too strong — it reproduces exactly the deterministic output of the real callee. No drift.

VERDICT: FAITHFUL. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment echoing patched symbols visit_Tuple/visit_UnaryOp, no bug/fix narration). same_spec(Solution, Solution_prepatch)=True — spec region byte-identical across patched/prepatch, so the impl fix is not encoded in the spec view. Semantically, the discriminator the spec pins (single-component tuple => "("++e++",)" with a trailing comma, vs. a bare parenthesized expression) is ALREADY fully public in problem_statement: '(1,) is rendered as (1), but should keep the trailing comma.' The post-condition's arity branch is a faithful restatement of the openly-stated required behavior, not information disclosed beyond the public task. The docstring describes behavior abstractly ('reads as a one-element tuple rather than a merely parenthesized expression') without narrating the bug/fix or naming the patched symbol/file. The patched-file path (sphinx/pycode/ast.py:215) appears only in mapping.md/refinement.md, which are not part of the consumer spec view. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
