# P2 adversarial audit — pytest-dev__pytest-8399

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a total functional equation (result = '_' :: descriptiveName setupName qualname) with zero output slack, so every closing impl is extensionally equal to gold and its refined patch is byte-identical to the gold edit (resolves). No closing-but-non-resolving impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 def implementation_generatedFixtureName
     (setupName qualname : List Char) : List Char := Id.run do
   let mut name : List Char := []
-  name := name ++ "_".toList
   name := name ++ "unittest_".toList
   name := name ++ setupName
   name := name ++ "_fixture_".toList
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
 def implementation_generatedFixtureName
     (setupName qualname : List Char) : List Char := Id.run do
   let mut name : List Char := []
-  name := name ++ "_".toList
+  name := name ++ "__".toList
   name := name ++ "unittest_".toList
   name := name ++ setupName
   name := name ++ "_fixture_".toList
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,14 +47,8 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  descriptiveName setupName qualname ++ ['_']
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,14 +47,8 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  '_' :: ("unittest_".toList ++ qualname ++ "_fixture_".toList ++ setupName)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,14 +47,10 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  match setupName with
+  | [] => descriptiveName setupName qualname
+  | _  => '_' :: descriptiveName setupName qualname
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,14 +47,8 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  '_' :: ("unittest_".toList ++ setupName ++ "_fixture".toList ++ qualname)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,14 +47,8 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  '_' :: descriptiveName setupName qualname ++ ['x']
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,14 +47,8 @@
 
 -- impl-start
 def implementation_generatedFixtureName
-    (setupName qualname : List Char) : List Char := Id.run do
-  let mut name : List Char := []
-  name := name ++ "_".toList
-  name := name ++ "unittest_".toList
-  name := name ++ setupName
-  name := name ++ "_fixture_".toList
-  name := name ++ qualname
-  return name
+    (setupName qualname : List Char) : List Char :=
+  ('_' :: "unittest_".toList) ++ setupName ++ ("_fixture_".toList ++ qualname)
 -- impl-end
 
 -- proof-start
@@ -64,6 +58,5 @@
         (implementation_generatedFixtureName setupName qualname) := by
   intro setupName qualname
   simp only [problem_spec_generatedFixtureName, implementation_generatedFixtureName,
-    descriptiveName, Id.run, List.append_assoc, List.nil_append]
-  rfl
+    descriptiveName, List.cons_append, List.append_assoc, List.nil_append]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Naming an automatically generated test fixture.

When the test framework synthesizes a fixture to run a class/module/function
setup–teardown pair, it assigns that fixture a unique name built from a constant
descriptive template and the owning object's qualified name. Such synthesized
fixtures carry no documentation of their own, so they belong to the framework's
internal machinery rather than the user-facing fixture surface. By convention the
fixture listing hides a fixture whose name begins with an underscore at the
default verbosity (showing it only when extra verbosity is requested); a name
that does NOT begin with an underscore is always shown.

The desired behavior: a generated fixture's name is private — it begins with an
underscore — while every following component of the name (the descriptive
template and the owning object's qualified name) is exactly the descriptive name
built from the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The fixture name is built purely from
-- the constant descriptive template and the two string inputs (the setup-hook name
-- and the owning object's qualified name); there is no callee contract to model,
-- so the `axioms` region is empty and G-AX skips.
-- axioms-end

-- pure-start
/-- The descriptive part of a generated setup–teardown fixture's name: the constant
template woven together with the setup-hook name and the owning object's
qualified name. Modeled per code point as `List Char` (total, sound indexing). -/
def descriptiveName (setupName qualname : List Char) : List Char :=
  "unittest_".toList ++ setupName ++ "_fixture_".toList ++ qualname
-- pure-end

-- post-conditions-start
/-- The generated fixture name is the descriptive name for the given inputs made
private: an underscore followed by the full descriptive name. This pins every
component — the leading private marker, the constant template, and both string
inputs — so the result is the descriptive name and nothing else, with the private
marker at the front. -/
def problem_spec_generatedFixtureName
    (setupName qualname : List Char) (result : List Char) : Prop :=
  result = '_' :: descriptiveName setupName qualname
-- post-conditions-end

-- impl-start
def implementation_generatedFixtureName
    (setupName qualname : List Char) : List Char := Id.run do
  let mut name : List Char := []
  name := name ++ "_".toList
  name := name ++ "unittest_".toList
  name := name ++ setupName
  name := name ++ "_fixture_".toList
  name := name ++ qualname
  return name
-- impl-end

-- proof-start
theorem correct_generatedFixtureName :
    ∀ (setupName qualname : List Char),
      problem_spec_generatedFixtureName setupName qualname
        (implementation_generatedFixtureName setupName qualname) := by
  intro setupName qualname
  simp only [problem_spec_generatedFixtureName, implementation_generatedFixtureName,
    descriptiveName, Id.run, List.append_assoc, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True verified for all 8 attacks and pos_control (swebench_unified.markers.same_spec, lean). Base commit 6e7dc8bac (worktree) callee unittest.py:147 = name=f"unittest_{setup_name}_fixture_{obj.__qualname__}" — matches mapping.md.

VERIFY COMMANDS: bash scripts/lean_verify.sh <f>.lean

### Results
- pos_control.lean (gold impl): EXIT 0; #print axioms correct_generatedFixtureName -> [propext] only, clean.
- atk_1 (prepatch bug: bare descriptive name, no leading '_'): EXIT 1 (does not close). Prepatch bug reproduced.
- atk_2 (double-underscore prefix '__'): EXIT 1.
- atk_3 (trailing underscore instead of leading): EXIT 1.
- atk_4 (swapped setupName/qualname positions): EXIT 1.
- atk_5 (control-flow-effect: bare name when setupName=[], '_'-prefixed otherwise): EXIT 1.
- atk_6 (wrong literal '_fixture' instead of '_fixture_'): EXIT 1.
- atk_7 (extra trailing 'x' char): EXIT 1.
- atk_8 (gold-EQUIVALENT echo, structurally different: ('_' :: "unittest_".toList) ++ setupName ++ ("_fixture_".toList ++ qualname)): EXIT 0, closes; #print axioms -> [propext] only, clean.

### RESOLVE (official harness, run_resolve, docker, image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-8399:latest present):
- atk_8 faithful patch (= gold edit, since atk_8 is extensionally gold) -> RESOLVED: True, completed: True, attempts: 1, note 'resolved'. (First run hit a transient 'no report/image pull' non-completion under contention; retry completed and resolved. This also serves as the harness positive control.)

The only impl that closed with clean axioms (atk_8) is gold-equivalent and its faithful patch RESOLVES => not a weakness (G-PANEL-1 resolving-echo policy). All 6+ genuinely-wrong impls fail to close. verify => correct holds.

REFINEMENT.MD AUDIT: 5 legs, all R or I (no kind-3, no A-legs). Leg1 prepend '_' = I (the fix); leg2 'unittest_' = I; leg3 setupName = R (str<->List Char); leg4 '_fixture_' = I; leg5 qualname = R. axioms region empty and G-AX correctly skips (modeled op is pure literal+input concatenation consuming no repo callee). Consumer-side visibility check (python.py verbose<=0 and name.startswith('_')) is unchanged context, correctly not modeled. G-CONF independently ran: 120008 inputs, 0 disagreements (seed 8399).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a total functional equation (result = '_' :: descriptiveName setupName qualname) with zero output slack, so every closing impl is extensionally equal to gold and its refined patch is byte-identical to the gold edit (resolves). No closing-but-non-resolving impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Naming an automatically generated test fixture.

When the test framework synthesizes a fixture to run a class/module/function
setup–teardown pair, it assigns that fixture a unique name built from a constant
descriptive template and the owning object's qualified name. Such synthesized
fixtures carry no documentation of their own, so they belong to the framework's
internal machinery rather than the user-facing fixture surface. By convention the
fixture listing hides a fixture whose name begins with an underscore at the
default verbosity (showing it only when extra verbosity is requested); a name
that does NOT begin with an underscore is always shown.

The desired behavior: a generated fixture's name is private — it begins with an
underscore — while every following component of the name (the descriptive
template and the owning object's qualified name) is exactly the descriptive name
built from the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The fixture name is built purely from
-- the constant descriptive template and the two string inputs (the setup-hook name
-- and the owning object's qualified name); there is no callee contract to model,
-- so the `axioms` region is empty and G-AX skips.
-- axioms-end

-- pure-start
/-- The descriptive part of a generated setup–teardown fixture's name: the constant
template woven together with the setup-hook name and the owning object's
qualified name. Modeled per code point as `List Char` (total, sound indexing). -/
def descriptiveName (setupName qualname : List Char) : List Char :=
  "unittest_".toList ++ setupName ++ "_fixture_".toList ++ qualname
-- pure-end

-- post-conditions-start
/-- The generated fixture name is the descriptive name for the given inputs made
private: an underscore followed by the full descriptive name. This pins every
component — the leading private marker, the constant template, and both string
inputs — so the result is the descriptive name and nothing else, with the private
marker at the front. -/
def problem_spec_generatedFixtureName
    (setupName qualname : List Char) (result : List Char) : Prop :=
  result = '_' :: descriptiveName setupName qualname
-- post-conditions-end

-- impl-start
def implementation_generatedFixtureName
    (setupName qualname : List Char) : List Char := Id.run do
  let mut name : List Char := []
  name := name ++ "_".toList
  name := name ++ "unittest_".toList
  name := name ++ setupName
  name := name ++ "_fixture_".toList
  name := name ++ qualname
  return name
-- impl-end

-- proof-start
theorem correct_generatedFixtureName :
    ∀ (setupName qualname : List Char),
      problem_spec_generatedFixtureName setupName qualname
        (implementation_generatedFixtureName setupName qualname) := by
  intro setupName qualname
  simp only [problem_spec_generatedFixtureName, implementation_generatedFixtureName,
    descriptiveName, Id.run, List.append_assoc, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True verified for all 8 attacks and pos_control (swebench_unified.markers.same_spec, lean). Base commit 6e7dc8bac (worktree) callee unittest.py:147 = name=f"unittest_{setup_name}_fixture_{obj.__qualname__}" — matches mapping.md.

VERIFY COMMANDS: bash scripts/lean_verify.sh <f>.lean

### Results
- pos_control.lean (gold impl): EXIT 0; #print axioms correct_generatedFixtureName -> [propext] only, clean.
- atk_1 (prepatch bug: bare descriptive name, no leading '_'): EXIT 1 (does not close). Prepatch bug reproduced.
- atk_2 (double-underscore prefix '__'): EXIT 1.
- atk_3 (trailing underscore instead of leading): EXIT 1.
- atk_4 (swapped setupName/qualname positions): EXIT 1.
- atk_5 (control-flow-effect: bare name when setupName=[], '_'-prefixed otherwise): EXIT 1.
- atk_6 (wrong literal '_fixture' instead of '_fixture_'): EXIT 1.
- atk_7 (extra trailing 'x' char): EXIT 1.
- atk_8 (gold-EQUIVALENT echo, structurally different: ('_' :: "unittest_".toList) ++ setupName ++ ("_fixture_".toList ++ qualname)): EXIT 0, closes; #print axioms -> [propext] only, clean.

### RESOLVE (official harness, run_resolve, docker, image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-8399:latest present):
- atk_8 faithful patch (= gold edit, since atk_8 is extensionally gold) -> RESOLVED: True, completed: True, attempts: 1, note 'resolved'. (First run hit a transient 'no report/image pull' non-completion under contention; retry completed and resolved. This also serves as the harness positive control.)

The only impl that closed with clean axioms (atk_8) is gold-equivalent and its faithful patch RESOLVES => not a weakness (G-PANEL-1 resolving-echo policy). All 6+ genuinely-wrong impls fail to close. verify => correct holds.

REFINEMENT.MD AUDIT: 5 legs, all R or I (no kind-3, no A-legs). Leg1 prepend '_' = I (the fix); leg2 'unittest_' = I; leg3 setupName = R (str<->List Char); leg4 '_fixture_' = I; leg5 qualname = R. axioms region empty and G-AX correctly skips (modeled op is pure literal+input concatenation consuming no repo callee). Consumer-side visibility check (python.py verbose<=0 and name.startswith('_')) is unchanged context, correctly not modeled. G-CONF independently ran: 120008 inputs, 0 disagreements (seed 8399).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-8399. Modeled routine: the `name=` expression that names the synthesized setup-teardown fixture in `_make_xunit_fixture` (src/_pytest/unittest.py:147).

Real callee behavior:
- Base commit 6e7dc8b (pre-patch): name=f"unittest_{setup_name}_fixture_{obj.__qualname__}".
- Gold patch (commit 19a2f7425, PR #8399): name=f"_unittest_{setup_name}_fixture_{obj.__qualname__}" — a single leading `_` prepended.

Spec: problem_spec_generatedFixtureName requires result = '_' :: descriptiveName setupName qualname, where descriptiveName = "unittest_" ++ setupName ++ "_fixture_" ++ qualname. This equals `_unittest_<setupName>_fixture_<qualname>`, exactly the post-patch f-string for EVERY (setup_name, obj.__qualname__) pair. setup_name and obj.__qualname__ are always Python str; the f-string is pure literal+field concatenation with no format specifiers, truncation, or conditionals, so the List-Char code-point model is an identity. Searched for a diverging input over empty strings, dotted qualnames, long/mixed identifier chars, and the F2P scenario — none diverges.

The spec pins the full result but does NOT over-constrain: the real name is a total deterministic function of exactly these two observables, so pinning them all is faithful, not too strong. Surrounding fixture logic is unchanged context, correctly excluded from the modeling boundary.

Corroboration:
- lean_verify.sh Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_generatedFixtureName -> [propext] only; no sorryAx (proof is real).
- same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical).
- conformance_check.py: post-patch f-string oracle vs impl shadow, 120008 inputs, 0 disagreements, seed 8399.
- Prepatch buggy impl (bare name, no leading '_') cannot satisfy the spec -> correct G-DIFF signal; the fix is the single prepended '_'.

Conclusion: the modeled function agrees with the real post-patch callee on all inputs. No divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (backend=lean): True. The spec view (imports/docstring/axioms/pure/post-conditions; impl and proof elided) leaks nothing beyond the public problem_statement.

Gold edit: prepend a single '_' to the generated xunit/unittest fixture name f-string (name=f"unittest_..." -> name=f"_unittest_..."), applied at five sites.

Mapping to spec-view content, each element already public in problem_statement:
- descriptiveName = "unittest_" ++ setupName ++ "_fixture_" ++ qualname: the template literals 'unittest_' and '_fixture_' are read directly off the problem_statement's own example output line `unittest_setUpClass_fixture_Tests`.
- postcondition result = '_' :: descriptiveName ...: the leading underscore is a verbatim restatement of the problem_statement's expected behavior ("this fixture's name would start with an underscore, and would therefore only get printed if the additional -v flag was used").
- docstring prose about the underscore-hides-at-default-verbosity convention likewise mirrors the '-v flag' sentence in problem_statement.

The spec necessarily pins the target postcondition (an underscore prepended to the descriptive name) — but that target is exactly what the reporter spelled out, not new gold-patch mechanics. The genuinely gold-specific details (the five edit sites, the concrete Python f-string, the '_' + name transformation skeleton) appear only in mapping.md/refinement.md, which are NOT part of the spec view, and the impl/proof regions that would show the concatenation skeleton are elided. No line of the spec view exceeds the public problem_statement.

Note: G-LEAK/leak.py is a lexical screen; this panel_3 judgment is the semantic gold-reconstruction check. Both clear: a reader with only problem_statement + spec view learns nothing about the fix that problem_statement did not already state.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
