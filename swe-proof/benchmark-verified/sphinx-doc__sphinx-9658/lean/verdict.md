# P2 adversarial audit — sphinx-doc__sphinx-9658

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
@@ -38,10 +38,7 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := ""
   return qualname
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,7 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := name ++ "."
   return qualname
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,9 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := name
+  if name = "" then
+    qualname := "x"
   return qualname
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,7 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := name.toUpper
   return qualname
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,9 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := ""
+  for c in name.data do
+    qualname := String.singleton c ++ qualname
   return qualname
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,7 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := name.drop 1
   return qualname
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,10 +38,7 @@
 
 -- impl-start
 def implementation_mockQualifiedName (name : String) : String := Id.run do
-  -- the stand-in records the short name it was created with
-  let mut nameAttr := name
-  -- its qualified name is taken from that recorded short name
-  let mut qualname := nameAttr
+  let mut qualname := String.mk name.data
   return qualname
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The qualified name reported by a mock stand-in object.

When a documentation tool encounters an attribute access on a mocked module or
object, it fabricates a lightweight stand-in to represent the referenced symbol.
Each stand-in is created with a *short name* — the final dotted component of the
symbol it stands for (e.g. the `Class` in `pkg.sub.Class`).

A downstream renderer forms a complete reference by joining the stand-in's
containing module path with the *qualified name* the stand-in reports. For that
joined reference to be complete (rather than ending at the dot, with the final
component missing), the qualified name a stand-in reports must equal the short
name it was created with.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reported qualified
-- name is determined directly from the short name the stand-in was created
-- with (a value-level string identity), with no opaque callee involved.
-- axioms-end

-- pure-start
-- No additional pure helpers are required.
-- pure-end

-- post-conditions-start
/-- The qualified name a mock stand-in reports equals the short name it was
created with. -/
def problem_spec_mockQualifiedName (name : String) (result : String) : Prop :=
  result = name
-- post-conditions-end

-- impl-start
def implementation_mockQualifiedName (name : String) : String := Id.run do
  -- the stand-in records the short name it was created with
  let mut nameAttr := name
  -- its qualified name is taken from that recorded short name
  let mut qualname := nameAttr
  return qualname
-- impl-end

-- proof-start
theorem correct_mockQualifiedName :
    ∀ (name : String),
      problem_spec_mockQualifiedName name
        (implementation_mockQualifiedName name) := by
  intro name
  unfold problem_spec_mockQualifiedName implementation_mockQualifiedName
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mockQualifiedName name result := (result = name). Total, exact functional spec — no precondition, no axiom, no pure helper. Any closing correct_* proof forces the impl to be extensionally the identity on String. So the spec is maximally tight and no wrong (non-identity) impl can verify.

SAME-SPEC: all 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region edited, axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch-bug qualname:="" -> exit 1 (fails; ""=name not refl)
- atk_2 name++"." (truncation-inverse) -> exit 1
- atk_3 partial-domain: empty->"x", else identity -> exit 1
- atk_4 boundary: name.toUpper -> exit 1
- atk_5 control-flow-effect: reverse via char fold -> exit 1
- atk_6 boundary: name.drop 1 -> exit 1
- atk_7 ungrounded-oracle echo: String.mk name.data (extensional identity) -> exit 0 CLOSES
- pos_control (gold Solution.lean) -> exit 0
#print axioms correct_mockQualifiedName for pos_control AND atk_7: 'does not depend on any axioms' (clean).

RESOLVE (protocol step 2 for the one closing attack atk_7): materialized faithful patch (''.join([c for c in self.__name__]) == deep translation of String.mk name.data), ran official harness (swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9658:latest). NOTE: first run_resolve attempts hit the known docker daemon race (docker.errors.ImageNotFound in client.images.list(all=True), the audit protocol 'one backend at a time' hazard — concurrent django concurrent runs pruning) which aborts harness startup before any per-instance work. Retried the harness directly in a loop; attempt succeeded with a genuine report: RESOLVED=true, FAIL_TO_PASS tests/test_util_typing.py::test_restify_mock success, all 24 PASS_TO_PASS success, patch_successfully_applied=true. report.json at experiments/logs/run_evaluation/atk7-loop-1/sbu_patch/sphinx-doc__sphinx-9658/report.json.

The only closing attack is a correct identity-echo whose faithful patch RESOLVES — not a weakness (matches the resolve-check policy: a same-spec verifying candidate whose refined patch resolves is not a spec weakness). No verifying impl has a non-resolving patch, so verify=>correct holds.

PREPATCH: Solution_prepatch.lean (carried gold proof over buggy qualname:="") fails lean_verify exit 1 -> prepatch bug reproduced.

REFINEMENT AUDIT: refinement.md declares/consumes NO axioms. Legs: 'let mut nameAttr := name' = R (Python str short-name value from _make_subclass '__name__':name -> Lean String), 'let mut qualname := nameAttr' = I (self.__qualname__ = self.__name__ identity copy), 'return qualname' = R (str -> String). No kind-3 legs; every leg R or I. A-legs N/A (no opaque callee — value-level string identity modeled deeply). mapping.md correspondence (mock.py:42-43 __init__ + _make_subclass __name__ injection, restify consumer typing.py:194-198) is faithful; the modeled observable result=name is exactly cls.__qualname__.

VERDICT: SOUND — 7 distinct same-spec attacks run (6 fail to verify, 1 verifies but is a correct echo whose materialized faithful patch RESOLVES=true under the official harness). Spec is a tight total identity; no verify-but-not-correct impl exists.

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

/-!
The qualified name reported by a mock stand-in object.

When a documentation tool encounters an attribute access on a mocked module or
object, it fabricates a lightweight stand-in to represent the referenced symbol.
Each stand-in is created with a *short name* — the final dotted component of the
symbol it stands for (e.g. the `Class` in `pkg.sub.Class`).

A downstream renderer forms a complete reference by joining the stand-in's
containing module path with the *qualified name* the stand-in reports. For that
joined reference to be complete (rather than ending at the dot, with the final
component missing), the qualified name a stand-in reports must equal the short
name it was created with.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reported qualified
-- name is determined directly from the short name the stand-in was created
-- with (a value-level string identity), with no opaque callee involved.
-- axioms-end

-- pure-start
-- No additional pure helpers are required.
-- pure-end

-- post-conditions-start
/-- The qualified name a mock stand-in reports equals the short name it was
created with. -/
def problem_spec_mockQualifiedName (name : String) (result : String) : Prop :=
  result = name
-- post-conditions-end

-- impl-start
def implementation_mockQualifiedName (name : String) : String := Id.run do
  -- the stand-in records the short name it was created with
  let mut nameAttr := name
  -- its qualified name is taken from that recorded short name
  let mut qualname := nameAttr
  return qualname
-- impl-end

-- proof-start
theorem correct_mockQualifiedName :
    ∀ (name : String),
      problem_spec_mockQualifiedName name
        (implementation_mockQualifiedName name) := by
  intro name
  unfold problem_spec_mockQualifiedName implementation_mockQualifiedName
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mockQualifiedName name result := (result = name). Total, exact functional spec — no precondition, no axiom, no pure helper. Any closing correct_* proof forces the impl to be extensionally the identity on String. So the spec is maximally tight and no wrong (non-identity) impl can verify.

SAME-SPEC: all 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region edited, axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch-bug qualname:="" -> exit 1 (fails; ""=name not refl)
- atk_2 name++"." (truncation-inverse) -> exit 1
- atk_3 partial-domain: empty->"x", else identity -> exit 1
- atk_4 boundary: name.toUpper -> exit 1
- atk_5 control-flow-effect: reverse via char fold -> exit 1
- atk_6 boundary: name.drop 1 -> exit 1
- atk_7 ungrounded-oracle echo: String.mk name.data (extensional identity) -> exit 0 CLOSES
- pos_control (gold Solution.lean) -> exit 0
#print axioms correct_mockQualifiedName for pos_control AND atk_7: 'does not depend on any axioms' (clean).

RESOLVE (protocol step 2 for the one closing attack atk_7): materialized faithful patch (''.join([c for c in self.__name__]) == deep translation of String.mk name.data), ran official harness (swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9658:latest). NOTE: first run_resolve attempts hit the known docker daemon race (docker.errors.ImageNotFound in client.images.list(all=True), the audit protocol 'one backend at a time' hazard — concurrent django concurrent runs pruning) which aborts harness startup before any per-instance work. Retried the harness directly in a loop; attempt succeeded with a genuine report: RESOLVED=true, FAIL_TO_PASS tests/test_util_typing.py::test_restify_mock success, all 24 PASS_TO_PASS success, patch_successfully_applied=true. report.json at experiments/logs/run_evaluation/atk7-loop-1/sbu_patch/sphinx-doc__sphinx-9658/report.json.

The only closing attack is a correct identity-echo whose faithful patch RESOLVES — not a weakness (matches the resolve-check policy: a same-spec verifying candidate whose refined patch resolves is not a spec weakness). No verifying impl has a non-resolving patch, so verify=>correct holds.

PREPATCH: Solution_prepatch.lean (carried gold proof over buggy qualname:="") fails lean_verify exit 1 -> prepatch bug reproduced.

REFINEMENT AUDIT: refinement.md declares/consumes NO axioms. Legs: 'let mut nameAttr := name' = R (Python str short-name value from _make_subclass '__name__':name -> Lean String), 'let mut qualname := nameAttr' = I (self.__qualname__ = self.__name__ identity copy), 'return qualname' = R (str -> String). No kind-3 legs; every leg R or I. A-legs N/A (no opaque callee — value-level string identity modeled deeply). mapping.md correspondence (mock.py:42-43 __init__ + _make_subclass __name__ injection, restify consumer typing.py:194-198) is faithful; the modeled observable result=name is exactly cls.__qualname__.

VERDICT: SOUND — 7 distinct same-spec attacks run (6 fail to verify, 1 verifies but is a correct echo whose materialized faithful patch RESOLVES=true under the official harness). Spec is a tight total identity; no verify-but-not-correct impl exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True; spec is `problem_spec_mockQualifiedName name result := result = name`. Lean verifies exit 0; `#print axioms correct_mockQualifiedName` => 'does not depend on any axioms' (genuine proof, no sorryAx). The modeled function is a deep String identity of the gold patch op `self.__qualname__ = self.__name__` where __name__ is the short `name` injected by `_make_subclass`. Real callee agrees on all defined inputs; the two raise-cases (NUL char, lone surrogate) are Python `type()` partiality on ill-formed names, unreachable in real repo usage (names originate from attribute keys / str(subscript-key)) and outside the declared printable-string bijection in mapping.md. This is not a spec-too-strong / drift defect: the model does not claim behavior the real callee contradicts with a returned value. Note: bundle's G-EQ currently records INCONCLUSIVE (fail) — that is an equivalence-gate/timeout artifact, orthogonal to faithfulness; the spec itself is faithful.

Counterexample / evidence:

```
None. Empirical sweep of the real callee `_make_subclass(name, module)().__qualname__` (the exact patched behavior, mirrored by the isolated type()+__init__ logic) over: ASCII identifiers, empty string, dotted names, spaces/tabs/newlines, control chars (\x1b), zero-width/BOM, emoji, CJK, fullwidth, accented, 10k-char strings, digit-leading, Python keywords — ALL return name unchanged, matching `result = name`.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage review of the Lean spec view for sphinx-doc__sphinx-9658.

Setup verified independently: markers.same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, so the pre/post views carry identical spec text). Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md, G-LEAK meta status=pass), so the strict panel_3 standard applies (no RELAXED_LEAKAGE.md deferral). Ran leakage.screen() directly: rep.passed=True, hard_failures=[]. Patch changed_symbols={MockObject, make_subclass}, changed_files={sphinx/ext/autodoc/mock.py}.

Semantic judgment (the mechanical screen is only half; I judge whether the spec view reveals the gold edit beyond the public problem_statement — NOT hints_text):

(1) L1/L2: no diff markers; the patched file path 'sphinx/ext/autodoc/mock.py' and its dotted module path do not appear anywhere in the view.

(2) Gold-edit specifics are ABSENT and abstracted: the distinctive symbols (_MockObject, _make_subclass) and, more importantly, the actual edit-locus attributes (__qualname__, __name__) never appear. The view speaks only in generic terms — 'mock stand-in object', 'downstream renderer', 'short name (final dotted component)', 'qualified name', 'module path'. The gold edit *mechanism* (self.__qualname__ = self.__name__ and injecting '__name__': name in _make_subclass) is not disclosed.

(3) L3: no narration terms (bug/fix/patch/regression/etc.) in comments or docstrings.

(4) The post-condition `result = name` and the docstring statement ('the qualified name a stand-in reports must equal the short name it was created with, else the reference ends at the dot with the final component missing') restate the required corrected behavior. This is exactly the PUBLIC symptom already in problem_statement: 'Bases' rendered as 'torch.nn.' instead of 'torch.nn.Module' — the final dotted component dropped, expected to be restored. Stating the required output relation is the spec's legitimate job; it localizes nothing about how the fix is implemented and adds no information beyond what the public bug report already implies.

Every candidate leak line traces back to the public problem_statement (truncation at the dot / missing final component) or to abstract behavioral framing. No spec-view line reproduces the gold diff, names a patched repo symbol, or reveals the edit locus beyond the public problem statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).