# P2 adversarial audit — sympy__sympy-22914

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,7 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
-  if name = "Min" then renderCall "min" args
-  else if name = "Max" then renderCall "max" args
-  else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
+  if name = "Abs" then renderCall "abs" args
   else fallback
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,7 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
   if name = "Min" then renderCall "min" args
-  else if name = "Max" then renderCall "max" args
-  else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
   else fallback
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,9 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
-  if name = "Min" then renderCall "min" args
-  else if name = "Max" then renderCall "max" args
+  if name = "Min" then renderCall "max" args
+  else if name = "Max" then renderCall "min" args
   else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
   else fallback
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,10 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
   if name = "Min" then renderCall "min" args
   else if name = "Max" then renderCall "max" args
   else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
-  else fallback
+  else renderCall name args
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,13 +66,7 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
-  if name = "Min" then renderCall "min" args
-  else if name = "Max" then renderCall "max" args
-  else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
-  else fallback
+  fallback
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,9 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
-  if name = "Min" then renderCall "min" args
+  if name = "Min" then renderCall "min" args.reverse
   else if name = "Max" then renderCall "max" args
   else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
   else fallback
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,9 @@
 -- impl-start
 def implementation_printApp
     (name : String) (args : List String) (fallback : String) : String :=
-  -- the built-in-equivalent table now maps the minimum and maximum operations;
-  -- the absolute-value mapping is pre-existing
   if name = "Min" then renderCall "min" args
   else if name = "Max" then renderCall "max" args
-  else if name = "Abs" then renderCall "abs" args
-  -- no built-in equivalent: the node keeps the unchanged machinery's emission
+  else if name = "Abs" then renderCall "Abs" args
   else fallback
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the per-node emission decision of a code printer that
turns symbolic expressions into target-language source.

When printing a function application, the printer checks whether the function
is one it recognizes as having a direct built-in equivalent in the target
language. If so, it emits the built-in call `name(arg, …)` — the mapped
built-in name followed by the comma-separated, already-printed arguments in
parentheses. If the function has no built-in equivalent, the node is emitted
by the pre-existing surrounding printing machinery; that machinery is
unchanged infrastructure, and its output for the node arrives here as the
read-only input `fallback`, to be returned unaltered.

Desired behaviour: the minimum and maximum operations have built-in
equivalents and therefore render as `min(arg, …)` and `max(arg, …)`
respectively; the absolute-value operation keeps its pre-existing `abs`
rendering; EVERY other function is emitted exactly as the unchanged machinery
would emit it (`fallback`) — nothing but the minimum/maximum emission may
change.

Every branch of the result is pinned to the inputs (the function name, the
argument strings, and the fallback text), so no part of the rendered output is
left free: the specification is total, with no domain restriction.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The dispatch test and the built-in
-- call rendering are modeled DEEPLY (spelled out below: the name decision plus
-- a comma-join + parenthesization), so there is no `opaque`/`axiom` callee
-- contract. The per-argument printing is unchanged and abstracted into the
-- `args` strings; likewise the emission the unchanged surrounding machinery
-- produces for a function with no built-in equivalent is unchanged,
-- pre-existing infrastructure whose output arrives as the read-only input
-- `fallback`. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a recognized call: the built-in name applied to its already-printed
arguments, comma-separated inside parentheses (`name(a, b, …)`). This is the
unchanged formatting shared by every recognized built-in. -/
def renderCall (fn : String) (args : List String) : String :=
  fn ++ "(" ++ String.intercalate ", " args ++ ")"
-- pure-end

-- post-conditions-start
/-- The emission is fully determined by the inputs:
* the minimum operation renders as a `min(…)` call over its arguments;
* the maximum operation renders as a `max(…)` call over its arguments;
* the absolute-value operation keeps its pre-existing `abs(…)` rendering;
* EVERY other function is emitted exactly as the unchanged surrounding
  machinery emits it — the result is the read-only input `fallback`, verbatim,
  so no behaviour other than the minimum/maximum emission may change.
The four clauses cover every possible name: no output is left unconstrained. -/
def problem_spec_printApp
    (name : String) (args : List String) (fallback : String)
    (result : String) : Prop :=
  (name = "Min" → result = renderCall "min" args) ∧
  (name = "Max" → result = renderCall "max" args) ∧
  (name = "Abs" → result = renderCall "abs" args) ∧
  (name ≠ "Min" → name ≠ "Max" → name ≠ "Abs" → result = fallback)
-- post-conditions-end

-- impl-start
def implementation_printApp
    (name : String) (args : List String) (fallback : String) : String :=
  -- the built-in-equivalent table now maps the minimum and maximum operations;
  -- the absolute-value mapping is pre-existing
  if name = "Min" then renderCall "min" args
  else if name = "Max" then renderCall "max" args
  else if name = "Abs" then renderCall "abs" args
  -- no built-in equivalent: the node keeps the unchanged machinery's emission
  else fallback
-- impl-end

-- proof-start
theorem correct_printApp :
    ∀ (name : String) (args : List String) (fallback : String),
    problem_spec_printApp name args fallback
      (implementation_printApp name args fallback) := by
  intro name args fallback
  unfold problem_spec_printApp implementation_printApp
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h1 h2 h3; simp [h1, h2, h3]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, sympy__sympy-22914 (lean). Spec is a TOTAL, fully-pinned function graph: problem_spec_printApp has four mutually-exclusive & exhaustive clauses (name=Min -> renderCall min args; name=Max -> renderCall max args; name=Abs -> renderCall abs args; else -> fallback), so every (name,args,fallback) maps to a UNIQUE required output. Zero behavioral freedom for a verifying impl.

SAME-SPEC: all 7 attack files pass swebench_unified.markers.same_spec == True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited). Positive control same_spec True.

### ATTACKS (verified concurrently, batches of 4, cmd: bash scripts/lean_verify.sh <f>; run):
- atk_1 PREPATCH BUG (Abs only; Min/Max fall to fallback): exit=1 unsolved goals. Reproduces recorded prepatch/G-DIFF signal.
- atk_2 partial-domain (only Min handled): exit=1.
- atk_3 boundary/swap (Min->max, Max->min): exit=1 (error: unsolved goals at Min/Max clauses, lines 83-84).
- atk_4 control-flow-effect (non-mapped heads leak renderCall name args instead of fallback): exit=1.
- atk_5 ungrounded-oracle echo (always return fallback): exit=1 (simp made no progress on Min/Max/Abs clauses).
- atk_6 mapped-render-wrong (Min args reversed): exit=1.
- atk_7 name-echo (Abs -> renderCall Abs, i.e. Abs(...) not abs(...)): exit=1.

NONE of the 7 same-spec wrong impls closes. Because no verifying wrong impl exists, there is NO impl requiring a materialized faithful patch / resolve run (step 2 vacuous). POSITIVE CONTROL (=Solution.lean impl) verifies: exit=0, and `#print axioms correct_printApp` => depends on axioms: [propext] (clean; no sorryAx). lean_verify.sh confirms no sorry/admit.

REFINEMENT AUDIT (refinement.md): 5 legs, all R (rows 1-2: str->String / list[str]->List String type refinement for the two newly-mapped Min/Max table rows) or I (rows 3-5: pre-existing Abs row, renderCall==_print_known_func format, fallback pass-through). No A-consumed, no A-reference legs (axioms region EMPTY; axiom_check.py is a legitimate skip stub -- no `axiom *_prop` declarations in Solution.lean, confirmed). No kind-3 inexpressible op. A-leg audit vacuous by design; the deep model (if-ladder + renderCall) correctly corresponds to Python _known_functions membership + _print_known_func. G-CONF present (conformance_check.py, seed 22914, 1e5 inputs) covers R/I transliteration.

VERDICT: SOUND. verify => correct holds: the total fully-pinned spec admits only the gold behavior; all wrong-impl attacks (partial-domain, boundary/swap, control-flow-effect, ungrounded echo, mapped-render-wrong, name-echo, and the prepatch bug) fail to verify.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the per-node emission decision of a code printer that
turns symbolic expressions into target-language source.

When printing a function application, the printer checks whether the function
is one it recognizes as having a direct built-in equivalent in the target
language. If so, it emits the built-in call `name(arg, …)` — the mapped
built-in name followed by the comma-separated, already-printed arguments in
parentheses. If the function has no built-in equivalent, the node is emitted
by the pre-existing surrounding printing machinery; that machinery is
unchanged infrastructure, and its output for the node arrives here as the
read-only input `fallback`, to be returned unaltered.

Desired behaviour: the minimum and maximum operations have built-in
equivalents and therefore render as `min(arg, …)` and `max(arg, …)`
respectively; the absolute-value operation keeps its pre-existing `abs`
rendering; EVERY other function is emitted exactly as the unchanged machinery
would emit it (`fallback`) — nothing but the minimum/maximum emission may
change.

Every branch of the result is pinned to the inputs (the function name, the
argument strings, and the fallback text), so no part of the rendered output is
left free: the specification is total, with no domain restriction.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The dispatch test and the built-in
-- call rendering are modeled DEEPLY (spelled out below: the name decision plus
-- a comma-join + parenthesization), so there is no `opaque`/`axiom` callee
-- contract. The per-argument printing is unchanged and abstracted into the
-- `args` strings; likewise the emission the unchanged surrounding machinery
-- produces for a function with no built-in equivalent is unchanged,
-- pre-existing infrastructure whose output arrives as the read-only input
-- `fallback`. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a recognized call: the built-in name applied to its already-printed
arguments, comma-separated inside parentheses (`name(a, b, …)`). This is the
unchanged formatting shared by every recognized built-in. -/
def renderCall (fn : String) (args : List String) : String :=
  fn ++ "(" ++ String.intercalate ", " args ++ ")"
-- pure-end

-- post-conditions-start
/-- The emission is fully determined by the inputs:
* the minimum operation renders as a `min(…)` call over its arguments;
* the maximum operation renders as a `max(…)` call over its arguments;
* the absolute-value operation keeps its pre-existing `abs(…)` rendering;
* EVERY other function is emitted exactly as the unchanged surrounding
  machinery emits it — the result is the read-only input `fallback`, verbatim,
  so no behaviour other than the minimum/maximum emission may change.
The four clauses cover every possible name: no output is left unconstrained. -/
def problem_spec_printApp
    (name : String) (args : List String) (fallback : String)
    (result : String) : Prop :=
  (name = "Min" → result = renderCall "min" args) ∧
  (name = "Max" → result = renderCall "max" args) ∧
  (name = "Abs" → result = renderCall "abs" args) ∧
  (name ≠ "Min" → name ≠ "Max" → name ≠ "Abs" → result = fallback)
-- post-conditions-end

-- impl-start
def implementation_printApp
    (name : String) (args : List String) (fallback : String) : String :=
  -- the built-in-equivalent table now maps the minimum and maximum operations;
  -- the absolute-value mapping is pre-existing
  if name = "Min" then renderCall "min" args
  else if name = "Max" then renderCall "max" args
  else if name = "Abs" then renderCall "abs" args
  -- no built-in equivalent: the node keeps the unchanged machinery's emission
  else fallback
-- impl-end

-- proof-start
theorem correct_printApp :
    ∀ (name : String) (args : List String) (fallback : String),
    problem_spec_printApp name args fallback
      (implementation_printApp name args fallback) := by
  intro name args fallback
  unfold problem_spec_printApp implementation_printApp
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h1 h2 h3; simp [h1, h2, h3]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, sympy__sympy-22914 (lean). Spec is a TOTAL, fully-pinned function graph: problem_spec_printApp has four mutually-exclusive & exhaustive clauses (name=Min -> renderCall min args; name=Max -> renderCall max args; name=Abs -> renderCall abs args; else -> fallback), so every (name,args,fallback) maps to a UNIQUE required output. Zero behavioral freedom for a verifying impl.

SAME-SPEC: all 7 attack files pass swebench_unified.markers.same_spec == True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited). Positive control same_spec True.

### ATTACKS (verified concurrently, batches of 4, cmd: bash scripts/lean_verify.sh <f>; run):
- atk_1 PREPATCH BUG (Abs only; Min/Max fall to fallback): exit=1 unsolved goals. Reproduces recorded prepatch/G-DIFF signal.
- atk_2 partial-domain (only Min handled): exit=1.
- atk_3 boundary/swap (Min->max, Max->min): exit=1 (error: unsolved goals at Min/Max clauses, lines 83-84).
- atk_4 control-flow-effect (non-mapped heads leak renderCall name args instead of fallback): exit=1.
- atk_5 ungrounded-oracle echo (always return fallback): exit=1 (simp made no progress on Min/Max/Abs clauses).
- atk_6 mapped-render-wrong (Min args reversed): exit=1.
- atk_7 name-echo (Abs -> renderCall Abs, i.e. Abs(...) not abs(...)): exit=1.

NONE of the 7 same-spec wrong impls closes. Because no verifying wrong impl exists, there is NO impl requiring a materialized faithful patch / resolve run (step 2 vacuous). POSITIVE CONTROL (=Solution.lean impl) verifies: exit=0, and `#print axioms correct_printApp` => depends on axioms: [propext] (clean; no sorryAx). lean_verify.sh confirms no sorry/admit.

REFINEMENT AUDIT (refinement.md): 5 legs, all R (rows 1-2: str->String / list[str]->List String type refinement for the two newly-mapped Min/Max table rows) or I (rows 3-5: pre-existing Abs row, renderCall==_print_known_func format, fallback pass-through). No A-consumed, no A-reference legs (axioms region EMPTY; axiom_check.py is a legitimate skip stub -- no `axiom *_prop` declarations in Solution.lean, confirmed). No kind-3 inexpressible op. A-leg audit vacuous by design; the deep model (if-ladder + renderCall) correctly corresponds to Python _known_functions membership + _print_known_func. G-CONF present (conformance_check.py, seed 22914, 1e5 inputs) covers R/I transliteration.

VERDICT: SOUND. verify => correct holds: the total fully-pinned spec admits only the gold behavior; all wrong-impl attacks (partial-domain, boundary/swap, control-flow-effect, ungrounded echo, mapped-render-wrong, name-echo, and the prepatch bug) fail to verify.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the modeled per-node emission of CodePrinter._print_Function driven by _known_functions in sympy/printing/pycode.py.

### Verification performed
1. Worktree is at base_commit c4e836cdf7 with the gold hunk applied (git diff shows the 2 added rows 'Min':'min','Max':'max' in _known_functions; HEAD has only 'Abs':'abs').
2. Solution.lean compiles via lean_verify.sh (exit 0). `#print axioms correct_printApp` => only [propext]; NO sorryAx — the proof is genuine.
3. same_spec(Solution, Solution_prepatch, lean) = True — spec region (axioms/pure/post-conditions) is byte-identical; impl+proof elided in the consumer spec view.
4. Empirical real-repo behavior (post-patch PythonCodePrinter().doprint) matches every spec clause:
   - Min(x,y) -> 'min(x, y)' == renderCall "min" ["x","y"]
   - Max(x,y,z) -> 'max(x, y, z)' == renderCall "max" args
   - Abs(x) -> 'abs(x)' == renderCall "abs" args
   - non-mapped heads (sin->'math.sin(x)', undefined f->not-supported text, nested Min(x,Max(y,z))->'min(x, max(y, z))') are emitted by the unchanged machinery, which the model supplies as the read-only input `fallback` and returns verbatim (4th conjunct).
   - _module_format('min')='min' (identity on unqualified plain-table values), so renderCall's `name(args)` faithfully transliterates '{name}({args})'.format + ', '.join.
5. G-CONF independently agrees: transliterated shadow == real patched printer on 91,444 inputs (seed 22914), 0 disagreements.

The spec is TOTAL (all four conjuncts cover every name) and each branch is pinned exactly to what the real callee produces. No over-constraint and no drift: I could construct no input where problem_spec_printApp disagrees with the real _print_Function emission (with args/fallback bound to the printer's own outputs). The fourth conjunct correctly abstracts unchanged fallback machinery rather than over-specifying it. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction screen for sympy__sympy-22914 (lean). Gold edit (dataset patch): two additive rows to _known_functions in pycode.py — 'Min':'min' and 'Max':'max' — so Min(a,b)->min(a, b) and Max(...)->max(...).

The PUBLIC problem_statement (not hints_text) already discloses the entire gold edit: title 'PythonCodePrinter doesn't support Min and Max', shows Min(a,b) should print min(a, b), and gives the exact recipe "min({}).format(', '.join(self._print(arg) for arg in expr.args))" plus the max twin. So the behavioral content (Min->min, Max->max, comma-joined parenthesized calls) is public in problem_statement itself.

Verified the actual spec view via markers.spec_view(Solution.lean, LeanBackend.language): imports/docstring + axioms(empty note) + pure(renderCall) + post-conditions(problem_spec_printApp); impl and proof elided. Every element traces to problem_statement:
- name=Min -> renderCall "min" args, name=Max -> renderCall "max" args: exactly what problem_statement demands.
- renderCall fn args = fn ++ "(" ++ String.intercalate ", " args ++ ")": verbatim the problem_statement comma-join+parenthesize recipe.
- name=Abs -> renderCall "abs" args: models PRE-EXISTING, unchanged behavior. Abs is NOT part of the gold patch (gold adds only Min/Max rows); naming Abs describes unchanged context, not the edit (Abs also appears in hints_text, out of scope, but still is not the edit).
- fourth conjunct (result=fallback for every other name): abstract no-change half of the contract, no patch specifics.

The spec view uses abstract phrasing ('built-in equivalent', 'recognized') and quotes NO gold-patch specifics: no _known_functions identifier, no pycode.py path/line, no 'Min':'min' dict-literal form. Those patch-specific details live only in mapping.md / refinement.md (auditor docs), which are NOT part of the agent-consumed spec view.

markers.same_spec(Solution, Solution_prepatch)=True — spec regions byte-identical to the prepatch twin, so no leak was smuggled into a spec region. G-LEAK lexical screen also passes (meta.json, status pass, no failures).

Integrity note (not a leakage finding): freshly-computed markers.region_hashes do not match the recorded region_hashes in meta.json for ANY region (a global mismatch, so most likely a change in the hashing convention rather than in the file), but same_spec against the prepatch twin confirms spec-region byte-identity, so the leakage conclusion is unaffected.

Conclusion: the spec view reveals nothing about the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
