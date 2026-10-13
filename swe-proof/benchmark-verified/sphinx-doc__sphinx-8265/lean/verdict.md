# P2 adversarial audit — sphinx-doc__sphinx-8265

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
 def implementation_tupleDisplay
     (elts : List (List Char)) : List Char := Id.run do
   if elts ≠ [] then
-    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
+    return List.intercalate [',', ' '] elts
   else
     return ['(', ')']
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
     (valueStr : List Char) (idx : IndexForm) : List Char := Id.run do
   match idx with
   | .elementTuple elts =>
-      let inner := List.intercalate [',', ' '] elts
+      let inner := ['('] ++ List.intercalate [',', ' '] elts ++ [')']
       return valueStr ++ ['['] ++ inner ++ [']']
   | .plain rendered =>
       return valueStr ++ ['['] ++ rendered ++ [']']
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
   if elts ≠ [] then
     return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
   else
-    return ['(', ')']
+    return []
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 -- impl-start
 def implementation_tupleDisplay
     (elts : List (List Char)) : List Char := Id.run do
-  if elts ≠ [] then
+  if elts = [] then
     return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
   else
     return ['(', ')']
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
       let inner := List.intercalate [',', ' '] elts
       return valueStr ++ ['['] ++ inner ++ [']']
   | .plain rendered =>
-      return valueStr ++ ['['] ++ rendered ++ [']']
+      return ['['] ++ rendered ++ [']']
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
 def implementation_tupleDisplay
     (elts : List (List Char)) : List Char := Id.run do
   if elts ≠ [] then
-    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
+    return ['('] ++ List.intercalate [','] elts ++ [')']
   else
     return ['(', ')']
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,11 +39,9 @@
 
 -- impl-start
 def implementation_tupleDisplay
-    (elts : List (List Char)) : List Char := Id.run do
-  if elts ≠ [] then
-    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
-  else
-    return ['(', ')']
+    (elts : List (List Char)) : List Char :=
+  (if elts = [] then ['(', ')']
+   else ['('] ++ List.intercalate [',', ' '] elts ++ [')'])
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- assemble their result text directly from already-rendered fragments by
-- straight-line code; the per-element rendering recursion supplies the inputs
-- and is not part of the modeled joining behavior, so no callee contract is
-- consumed. The proof agent may add `_prop` axioms only if a proof obligation
-- needs one.
-- axioms-end

-- pure-start
/-- The shape of a subscription index as seen by the text renderer.

* `elementTuple elts` — the index is a multi-component grouping, carrying the
  already-rendered text of each component (`elts`); by construction it is
  non-empty and carries no spread component.
* `plain rendered` — any other index, carrying its own already-rendered text. -/
inductive IndexForm where
  | elementTuple (elts : List (List Char))
  | plain (rendered : List Char)
-- pure-end

-- post-conditions-start
/-- Specification of rendering a comma-separated display of a sequence of
already-rendered component texts (`elts`).

A non-empty sequence is shown as its components joined by `", "` and enclosed in
a matching pair of round brackets, so that the display is a single grouped unit.
An empty sequence is shown as the empty grouping `"()"`. The whole result is
determined by `elts` alone. -/
def problem_spec_tupleDisplay
    (elts : List (List Char)) (result : List Char) : Prop :=
  result =
    (if elts = [] then ['(', ')']
     else ['('] ++ List.intercalate [',', ' '] elts ++ [')'])
-- post-conditions-end

-- impl-start
def implementation_tupleDisplay
    (elts : List (List Char)) : List Char := Id.run do
  if elts ≠ [] then
    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
  else
    return ['(', ')']
-- impl-end

-- proof-start
theorem correct_tupleDisplay : ∀ (elts : List (List Char)),
    problem_spec_tupleDisplay elts (implementation_tupleDisplay elts) := by
  intro elts
  unfold problem_spec_tupleDisplay implementation_tupleDisplay
  by_cases h : elts = []
  · simp [h, Id.run, pure]
  · simp [h, Id.run, pure]
-- proof-end

-- post-conditions-start
/-- Specification of rendering a subscription `value[index]` to text.

`valueStr` is the already-rendered text of the subscripted value and `idx` is
the index. The result is `valueStr`, then `'['`, then the index text, then `']'`.
When the index is a multi-component grouping, its components are listed directly
between the brackets — joined by `", "`, with no extra surrounding grouping —
so each component is a separate subscript argument. Any other index contributes
its own rendered text unchanged. -/
def problem_spec_subscription
    (valueStr : List Char) (idx : IndexForm) (result : List Char) : Prop :=
  result =
    valueStr ++ ['['] ++
      (match idx with
       | .elementTuple elts => List.intercalate [',', ' '] elts
       | .plain rendered => rendered)
    ++ [']']
-- post-conditions-end

-- impl-start
def implementation_subscription
    (valueStr : List Char) (idx : IndexForm) : List Char := Id.run do
  match idx with
  | .elementTuple elts =>
      let inner := List.intercalate [',', ' '] elts
      return valueStr ++ ['['] ++ inner ++ [']']
  | .plain rendered =>
      return valueStr ++ ['['] ++ rendered ++ [']']
-- impl-end

-- proof-start
theorem correct_subscription : ∀ (valueStr : List Char) (idx : IndexForm),
    problem_spec_subscription valueStr idx
      (implementation_subscription valueStr idx) := by
  intro valueStr idx
  unfold problem_spec_subscription implementation_subscription
  cases idx with
  | elementTuple elts => simp [Id.run, pure]
  | plain rendered => simp [Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sphinx-doc__sphinx-8265 (lean). Both specs are TIGHT functional-equality specs: problem_spec_tupleDisplay and problem_spec_subscription each pin `result` to a UNIQUE value for every input (`result = <closed form>`), so any impl whose correct_* closes must be extensionally equal to the gold. same_spec=True verified for all 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited).

ATTACKS (all same_spec=True). Verification via scripts/lean_verify.sh <f>, run concurrently (<=4 at a time):
- atk_1 (prepatch bug / FAIL_TO_PASS: non-empty tuple drops surrounding parens -> `join` instead of `(join)`): exit=1. Goal left unclosable: `[',',' '].intercalate elts = '(' :: (... ++ [')'])`.
- atk_2 (prepatch_2 bug: subscription elementTuple wraps inner in parens): exit=1. Goal: `'(' :: (... ++ [')',']']) = ... ++ [']']`.
- atk_3 (boundary: empty tuple returns [] instead of "()"): exit=1. Goal `elts=[] -> False`.
- atk_4 (control-flow-effect: inverted branch condition `elts = []`): exit=1.
- atk_5 (boundary: plain-branch drops valueStr prefix): exit=1. Goal `valueStr = []`.
- atk_6 (separator variant: `,` without space): exit=1. Goal `[','].intercalate elts = [',',' '].intercalate elts`.
- atk_7 (ungrounded-oracle ECHO: impl written literally as the spec RHS): exit=0, VERIFIES. `#print axioms` for both correct_* = [propext] only (clean, no sorry), identical to gold's axioms.

Positive control gold.lean: exit=0; #print axioms both = [propext].

PROTOCOL step 2 (materialize+resolve every verifying same-spec impl): atk_7 is extensionally equal to the gold output (tupleDisplay = spec RHS = gold's `(...)` form; subscription byte-identical to gold), so its faithful Python patch equals the gold patch. Executed run_resolve('sphinx-doc__sphinx-8265', atk_7_faithful.patch, timeout=1800) under SBU_BENCHMARK=swe_bench_verified via the official Docker harness => RESOLVED=True, note='resolved'. Therefore verify => correct holds for the only verifying attack; NO break.

REFINEMENT.MD AUDIT: every leg is R (str per-code-point <-> List Char; `", ".join` <-> `List.intercalate [',',' ']`; `"%s[%s]"` template <-> `++`) or I (branch selections, literals). NO A-consumed and NO A-reference legs: the per-element recursion self.visit(e)/self.visit(node.value) is NOT modeled — its results ARE the modeled inputs (elts element renderings, valueStr). G-AX is a legitimate SKIP stub (meta.json: axioms=[], deep_model_references=[], G-AX pass 'no consumed axiom and no A-reference'). The in-function helper is_simple_tuple is captured by the IndexForm constructor chosen, NOT axiomatized; conformance_check.py's index_form mirrors is_simple_tuple incl. the py<3.8 ast.Index branch. No kind-3 legs. G-CONF (meta.json) passed: checked=119191, tuples=64930, subs=54261, mismatches=0, feeding real sphinx.pycode.ast.unparse output back as the modeled inputs — validates the R/I correspondence and the recursion boundary.

VERDICT: SOUND. >=5 distinct wrong impls (6 wrong + 1 echo) attacked; every wrong impl's proof FAILS to close (tight functional-equality spec), and the sole closing clean-axiom impl (atk_7) has a materialized faithful patch that RESOLVES. verify<=>correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- assemble their result text directly from already-rendered fragments by
-- straight-line code; the per-element rendering recursion supplies the inputs
-- and is not part of the modeled joining behavior, so no callee contract is
-- consumed. The proof agent may add `_prop` axioms only if a proof obligation
-- needs one.
-- axioms-end

-- pure-start
/-- The shape of a subscription index as seen by the text renderer.

* `elementTuple elts` — the index is a multi-component grouping, carrying the
  already-rendered text of each component (`elts`); by construction it is
  non-empty and carries no spread component.
* `plain rendered` — any other index, carrying its own already-rendered text. -/
inductive IndexForm where
  | elementTuple (elts : List (List Char))
  | plain (rendered : List Char)
-- pure-end

-- post-conditions-start
/-- Specification of rendering a comma-separated display of a sequence of
already-rendered component texts (`elts`).

A non-empty sequence is shown as its components joined by `", "` and enclosed in
a matching pair of round brackets, so that the display is a single grouped unit.
An empty sequence is shown as the empty grouping `"()"`. The whole result is
determined by `elts` alone. -/
def problem_spec_tupleDisplay
    (elts : List (List Char)) (result : List Char) : Prop :=
  result =
    (if elts = [] then ['(', ')']
     else ['('] ++ List.intercalate [',', ' '] elts ++ [')'])
-- post-conditions-end

-- impl-start
def implementation_tupleDisplay
    (elts : List (List Char)) : List Char := Id.run do
  if elts ≠ [] then
    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
  else
    return ['(', ')']
-- impl-end

-- proof-start
theorem correct_tupleDisplay : ∀ (elts : List (List Char)),
    problem_spec_tupleDisplay elts (implementation_tupleDisplay elts) := by
  intro elts
  unfold problem_spec_tupleDisplay implementation_tupleDisplay
  by_cases h : elts = []
  · simp [h, Id.run, pure]
  · simp [h, Id.run, pure]
-- proof-end

-- post-conditions-start
/-- Specification of rendering a subscription `value[index]` to text.

`valueStr` is the already-rendered text of the subscripted value and `idx` is
the index. The result is `valueStr`, then `'['`, then the index text, then `']'`.
When the index is a multi-component grouping, its components are listed directly
between the brackets — joined by `", "`, with no extra surrounding grouping —
so each component is a separate subscript argument. Any other index contributes
its own rendered text unchanged. -/
def problem_spec_subscription
    (valueStr : List Char) (idx : IndexForm) (result : List Char) : Prop :=
  result =
    valueStr ++ ['['] ++
      (match idx with
       | .elementTuple elts => List.intercalate [',', ' '] elts
       | .plain rendered => rendered)
    ++ [']']
-- post-conditions-end

-- impl-start
def implementation_subscription
    (valueStr : List Char) (idx : IndexForm) : List Char := Id.run do
  match idx with
  | .elementTuple elts =>
      let inner := List.intercalate [',', ' '] elts
      return valueStr ++ ['['] ++ inner ++ [']']
  | .plain rendered =>
      return valueStr ++ ['['] ++ rendered ++ [']']
-- impl-end

-- proof-start
theorem correct_subscription : ∀ (valueStr : List Char) (idx : IndexForm),
    problem_spec_subscription valueStr idx
      (implementation_subscription valueStr idx) := by
  intro valueStr idx
  unfold problem_spec_subscription implementation_subscription
  cases idx with
  | elementTuple elts => simp [Id.run, pure]
  | plain rendered => simp [Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sphinx-doc__sphinx-8265 (lean). Both specs are TIGHT functional-equality specs: problem_spec_tupleDisplay and problem_spec_subscription each pin `result` to a UNIQUE value for every input (`result = <closed form>`), so any impl whose correct_* closes must be extensionally equal to the gold. same_spec=True verified for all 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited).

ATTACKS (all same_spec=True). Verification via scripts/lean_verify.sh <f>, run concurrently (<=4 at a time):
- atk_1 (prepatch bug / FAIL_TO_PASS: non-empty tuple drops surrounding parens -> `join` instead of `(join)`): exit=1. Goal left unclosable: `[',',' '].intercalate elts = '(' :: (... ++ [')'])`.
- atk_2 (prepatch_2 bug: subscription elementTuple wraps inner in parens): exit=1. Goal: `'(' :: (... ++ [')',']']) = ... ++ [']']`.
- atk_3 (boundary: empty tuple returns [] instead of "()"): exit=1. Goal `elts=[] -> False`.
- atk_4 (control-flow-effect: inverted branch condition `elts = []`): exit=1.
- atk_5 (boundary: plain-branch drops valueStr prefix): exit=1. Goal `valueStr = []`.
- atk_6 (separator variant: `,` without space): exit=1. Goal `[','].intercalate elts = [',',' '].intercalate elts`.
- atk_7 (ungrounded-oracle ECHO: impl written literally as the spec RHS): exit=0, VERIFIES. `#print axioms` for both correct_* = [propext] only (clean, no sorry), identical to gold's axioms.

Positive control gold.lean: exit=0; #print axioms both = [propext].

PROTOCOL step 2 (materialize+resolve every verifying same-spec impl): atk_7 is extensionally equal to the gold output (tupleDisplay = spec RHS = gold's `(...)` form; subscription byte-identical to gold), so its faithful Python patch equals the gold patch. Executed run_resolve('sphinx-doc__sphinx-8265', atk_7_faithful.patch, timeout=1800) under SBU_BENCHMARK=swe_bench_verified via the official Docker harness => RESOLVED=True, note='resolved'. Therefore verify => correct holds for the only verifying attack; NO break.

REFINEMENT.MD AUDIT: every leg is R (str per-code-point <-> List Char; `", ".join` <-> `List.intercalate [',',' ']`; `"%s[%s]"` template <-> `++`) or I (branch selections, literals). NO A-consumed and NO A-reference legs: the per-element recursion self.visit(e)/self.visit(node.value) is NOT modeled — its results ARE the modeled inputs (elts element renderings, valueStr). G-AX is a legitimate SKIP stub (meta.json: axioms=[], deep_model_references=[], G-AX pass 'no consumed axiom and no A-reference'). The in-function helper is_simple_tuple is captured by the IndexForm constructor chosen, NOT axiomatized; conformance_check.py's index_form mirrors is_simple_tuple incl. the py<3.8 ast.Index branch. No kind-3 legs. G-CONF (meta.json) passed: checked=119191, tuples=64930, subs=54261, mismatches=0, feeding real sphinx.pycode.ast.unparse output back as the modeled inputs — validates the R/I correspondence and the recursion boundary.

VERDICT: SOUND. >=5 distinct wrong impls (6 wrong + 1 echo) attacked; every wrong impl's proof FAILS to close (tight functional-equality spec), and the sole closing clean-axiom impl (atk_7) has a materialized faithful patch that RESOLVES. verify<=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real repo) found NO diverging input. Summary of the rigorous checks:

1) LEAN INTEGRITY. scripts/lean_verify.sh on Solution.lean exits 0 (compiles, no sorry). `#print axioms correct_tupleDisplay/correct_subscription` => both depend only on [propext]; NO sorryAx, so the proofs are genuine. Each implementation_* is literally the RHS of its problem_spec_*, and correctness is proven ∀ inputs, so spec ⟺ impl exactly (the modeled function IS the spec).

2) SPEC MARKERS. swebench_unified.markers.same_spec (lean backend) returns True for Solution vs Solution_prepatch and vs Solution_prepatch_2; the prepatch variants differ only in the impl/proof regions, spec region byte-identical.

3) FAITHFULNESS vs REAL PATCHED CALLEE. Modeled sites: _UnparseVisitor.visit_Tuple (ast.py:174-178 post-patch) and visit_Subscript (168-181 post-patch). Built the patched repo at base_commit b428cd24 (git checkout base ast.py + git apply patch.diff, verified). Real callee = sphinx.pycode.ast.unparse. Boundary per mapping.md: per-element recursion self.visit(e)/self.visit(node.value) is NOT modeled — its results ARE the inputs (elts renderings, valueStr); the model captures only the joining/wrapping logic and the is_simple_tuple dispatch via IndexForm.

 - Bundle conformance_check.py against patched repo: status=pass checked=119191 tuples=64930 subs=54261 mismatches=0.
 - INDEPENDENT 400,000-case differential (my own, not the bundle's fuzzer) with HARDER inputs: non-identity-rendering atoms (1.5, 'str', f(1), a+b, -1, x.y, None, True), extended/multi slices, nested tuples, starred tuples, empty tuple a[()], double subscription a[b][c,d], curated edge list — 0 mismatches.
 - Hand-checked boundary edges: a[()] -> 'a[()]' (empty tuple => .plain '()', correct — is_simple_tuple false on empty elts), (1,) -> '(1)', a[b][c,d] -> 'a[b][c, d]', obj.x[y,z] -> 'obj.x[y, z]'. Inputs where the real callee RAISES NotImplementedError (bare slices a[1:2], starred slices a[*b,], mixed a[1:2,3]) make the corresponding .plain 'rendered' input itself undefined through the same unmodeled recursion, so there is no defined divergence — the model is faithful at the modeled boundary.

The IndexForm classification (elementTuple iff ast.Tuple with non-empty elts and no Starred, else plain — with the py<3.8 ast.Index wrapper collapsed) precisely mirrors the patch's dispatch. No input found where problem_spec disagrees with the real patched callee. Spec is neither too strong nor drifted. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage audit of sphinx-doc__sphinx-8265 (lean). Spec-region integrity confirmed: derived spec_view via markers.spec_view with LeanBackend.language hashes to 59a76de4f0ebe1056745de8d5fd21559d37bd6664554736dc3fc5b1f41c354aa, byte-identical to meta.json; markers.same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True, so the leakage screen is over the legitimate spec view. Mechanical leakage.screen(sol, tables, gold_patch, problem_statement) => hard_failures=[] warnings=[]. Proofs genuine: lean_verify.sh exit 0; meta #print axioms = [propext] only (no sorryAx). No RELAXED_LEAKAGE.md on the lean bundle (only velvet/nagini), so this is a strict NO-LEAKAGE judgment, not a panel_3 deferral. Token scan of the full spec view for the gold-edit distinctive symbols {visit_Tuple, visit_Subscript, is_simple_tuple, node.slice, node.elts, ast.Index, ast.Starred, ast.Tuple, visit_Set, ast.py, '%s[%s]', self.visit, unparse, patch/diff/bug/fix narration} => zero matches. The tuple round-bracket behavior (color=(1,1,1)) is already public in problem_statement's Expected behavior. The subscription behavior (tuple-index components listed directly between brackets with no surrounding grouping) is NOT in problem_statement but is expressed purely as an abstract behavioral postcondition using the modeling abstraction IndexForm (elementTuple/plain), which carries no Python identifiers, no file path, no diff line, and no bug/fix narration. This is the uniform spec formulation (a spec always encodes desired post-patch behavior) and does not hand the auditor the gold edit beyond the public problem_statement. Gold-diff specifics (is_simple_tuple predicate, ast.Index py<3.8 wrapper, Starred exclusion) appear only in the auditor artifacts mapping.md/refinement.md, which are NOT part of the panel spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
