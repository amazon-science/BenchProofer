# P2 adversarial audit — sphinx-doc__sphinx-8551

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,19 +80,23 @@
     let mut result : XrefNode :=
       { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
     result := { result with refspecific := true }
-    result := { result with pyModule := ctx.module }
-    result := { result with pyClass := ctx.cls }
     if hasSigil target then
       result := { result with reftarget := target.drop 1 }
     return result
 -- impl-end
 
 -- proof-start
+-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
+-- implementation it cannot close: the produced node leaves the surrounding
+-- namespace context absent (`pyModule = none`, `pyClass = none`), so whenever a
+-- current module or enclosing class is in force (e.g. `ctx.module = some
+-- "example"`, `ctx.cls = some "Class"`) the node's module/class disagree with the
+-- specification's `result.pyModule = ctx.module` / `result.pyClass = ctx.cls`.
 theorem correct_makeXref :
     ∀ (ctx : RefContext) (target : String),
       problem_spec_makeXref ctx target (implementation_makeXref ctx target) := by
   intro ctx target
   unfold problem_spec_makeXref implementation_makeXref strippedTarget
-  simp only [Id.run, bind, pure]
-  by_cases h : hasSigil target <;> simp [h]
+  by_cases h : hasSigil target <;> simp only [Id.run, h, if_true, Bool.false_eq_true,
+    if_false] <;> exact ⟨rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,6 @@
       { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
     result := { result with refspecific := true }
     result := { result with pyModule := ctx.module }
-    result := { result with pyClass := ctx.cls }
     if hasSigil target then
       result := { result with reftarget := target.drop 1 }
     return result
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,6 @@
     result := { result with refspecific := true }
     result := { result with pyModule := ctx.module }
     result := { result with pyClass := ctx.cls }
-    if hasSigil target then
-      result := { result with reftarget := target.drop 1 }
     return result
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,8 +80,8 @@
     let mut result : XrefNode :=
       { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
     result := { result with refspecific := true }
-    result := { result with pyModule := ctx.module }
-    result := { result with pyClass := ctx.cls }
+    result := { result with pyModule := ctx.cls }
+    result := { result with pyClass := ctx.module }
     if hasSigil target then
       result := { result with reftarget := target.drop 1 }
     return result
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,6 @@
   Id.run do
     let mut result : XrefNode :=
       { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
-    result := { result with refspecific := true }
     result := { result with pyModule := ctx.module }
     result := { result with pyClass := ctx.cls }
     if hasSigil target then
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,7 @@
     result := { result with refspecific := true }
     result := { result with pyModule := ctx.module }
     result := { result with pyClass := ctx.cls }
-    if hasSigil target then
-      result := { result with reftarget := target.drop 1 }
+    result := { result with reftarget := target.drop 1 }
     return result
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     result := { result with refspecific := true }
     result := { result with pyModule := ctx.module }
     result := { result with pyClass := ctx.cls }
-    if hasSigil target then
+    if target.startsWith "." then
       result := { result with reftarget := target.drop 1 }
     return result
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building an implicit cross-reference node for a type name that appears in an
object's info field (the inline type annotations attached to documented
parameters and return values).

When such an annotation is turned into a cross-reference, the reference node it
produces carries the metadata a later resolution step uses to find the target:

  * the reference target (the name being linked to);
  * a marker requesting scope-aware (specific) resolution;
  * the surrounding namespace context — the current module name and the
    enclosing class name — so that an unqualified name is resolved relative to
    where the annotation sits rather than searched for everywhere.

Explicit cross-reference roles already record that surrounding namespace
context. The node built here is expected to record the very same context, so an
unqualified type name resolves the way an explicit reference to the same name
would. We model the namespace context as a `RefContext` (each component is
optional, since either may be absent) and the produced node as an `XrefNode`.

A leading `.` or `~` on the target is a sigil that only affects the link target
and display text, not the namespace context; the target with such a sigil
removed is the reference target.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The surrounding namespace context
-- (module, class) is an INPUT to the modeled node-building step, and every node
-- component the step writes is modeled directly. Hence no `opaque`/`axiom` decls.
-- axioms-end

-- pure-start
/-- The surrounding namespace context in force where an annotation sits: the
current module name and the enclosing class name, each optional (absent when
there is no current module / no enclosing class). -/
structure RefContext where
  module : Option String
  cls    : Option String
deriving DecidableEq, Repr, Inhabited

/-- A cross-reference node. `reftarget` is the name to resolve; `refspecific`
requests scope-aware resolution; `pyModule`/`pyClass` carry the surrounding
namespace context the resolver consults. -/
structure XrefNode where
  reftarget   : String
  refspecific : Bool
  pyModule    : Option String
  pyClass     : Option String
deriving DecidableEq, Repr, Inhabited

/-- Whether the target carries a leading `.` or `~` sigil. -/
def hasSigil (target : String) : Bool :=
  target.startsWith "." || target.startsWith "~"

/-- The reference target: the name with a leading sigil removed, if present. -/
def strippedTarget (target : String) : String :=
  if hasSigil target then target.drop 1 else target
-- pure-end

-- post-conditions-start
/-- The node built for an info-field type annotation, given the surrounding
namespace context `ctx` and the annotation `target`. The node requests
scope-aware resolution, its reference target is the sigil-stripped name, and —
crucially — it records the surrounding namespace context: its module and class
equal the current module and enclosing class. -/
def problem_spec_makeXref
    (ctx : RefContext) (target : String) (result : XrefNode) : Prop :=
  result.refspecific = true ∧
  result.reftarget = strippedTarget target ∧
  result.pyModule = ctx.module ∧
  result.pyClass = ctx.cls
-- post-conditions-end

-- impl-start
def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=
  Id.run do
    let mut result : XrefNode :=
      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
    result := { result with refspecific := true }
    result := { result with pyModule := ctx.module }
    result := { result with pyClass := ctx.cls }
    if hasSigil target then
      result := { result with reftarget := target.drop 1 }
    return result
-- impl-end

-- proof-start
theorem correct_makeXref :
    ∀ (ctx : RefContext) (target : String),
      problem_spec_makeXref ctx target (implementation_makeXref ctx target) := by
  intro ctx target
  unfold problem_spec_makeXref implementation_makeXref strippedTarget
  simp only [Id.run, bind, pure]
  by_cases h : hasSigil target <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Fully functional spec: problem_spec_makeXref is a forall over (ctx, target) pinning ALL FOUR observed node attributes exactly to input-functions (refspecific=true, reftarget=strippedTarget target, pyModule=ctx.module, pyClass=ctx.cls). No unconstrained output component exists. axioms region is comment-only (no axiom/opaque decls); refinement.md legs are all R (type refinements #1-3) or I (concrete/deep-modeled ops #4-9) with NO A-consumed/A-reference/kind-3 legs, so there is no callee correspondence that could drift; G-AX is a legitimate skip stub and G-CONF differential-tests the R/I leg. 

Protocol: all 8 files confirmed same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Verifications run concurrently (<=4/batch) via `bash scripts/lean_verify.sh $F` from project root.

Positive control (gold impl): exit 0; `#print axioms correct_makeXref` => depends on axioms: [propext] (clean, no sorry).

prepatch bug reproduced (atk_1, Solution_prepatch.lean impl: omits pyModule/pyClass writes so they stay none): exit 1, application-type-mismatch/unsolved goals from carried gold proof.

6 further DISTINCT wrong impls, each carrying the gold proof body: atk_2 partial-domain (drop pyClass write, stays none) exit1 unsolved goals; atk_3 control-flow-effect (never strip sigil, reftarget stays =target) exit1; atk_4 control-flow-effect (swap module<->class assignments) exit1 unsolved goals; atk_5 ungrounded-oracle echo (refspecific left false) exit1 unsolved goals; atk_6 boundary (unconditional target.drop 1 even without sigil) exit1 unsolved goals; atk_7 boundary/partial-domain (strip '.' only, not '~') exit1 unsolved goals.

Every same-spec wrong impl FAILED to verify with genuine proof errors (unsolved goals / type mismatch); NONE closed with clean axioms. Therefore protocol step 2 (materialize faithful patch + run_resolve) had no triggering candidate — no verifying-but-wrong impl exists to break the spec. verify=>correct holds. Verdict SOUND after >=5 distinct attacks (7 total incl. prepatch) all run and none breaking it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building an implicit cross-reference node for a type name that appears in an
object's info field (the inline type annotations attached to documented
parameters and return values).

When such an annotation is turned into a cross-reference, the reference node it
produces carries the metadata a later resolution step uses to find the target:

  * the reference target (the name being linked to);
  * a marker requesting scope-aware (specific) resolution;
  * the surrounding namespace context — the current module name and the
    enclosing class name — so that an unqualified name is resolved relative to
    where the annotation sits rather than searched for everywhere.

Explicit cross-reference roles already record that surrounding namespace
context. The node built here is expected to record the very same context, so an
unqualified type name resolves the way an explicit reference to the same name
would. We model the namespace context as a `RefContext` (each component is
optional, since either may be absent) and the produced node as an `XrefNode`.

A leading `.` or `~` on the target is a sigil that only affects the link target
and display text, not the namespace context; the target with such a sigil
removed is the reference target.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The surrounding namespace context
-- (module, class) is an INPUT to the modeled node-building step, and every node
-- component the step writes is modeled directly. Hence no `opaque`/`axiom` decls.
-- axioms-end

-- pure-start
/-- The surrounding namespace context in force where an annotation sits: the
current module name and the enclosing class name, each optional (absent when
there is no current module / no enclosing class). -/
structure RefContext where
  module : Option String
  cls    : Option String
deriving DecidableEq, Repr, Inhabited

/-- A cross-reference node. `reftarget` is the name to resolve; `refspecific`
requests scope-aware resolution; `pyModule`/`pyClass` carry the surrounding
namespace context the resolver consults. -/
structure XrefNode where
  reftarget   : String
  refspecific : Bool
  pyModule    : Option String
  pyClass     : Option String
deriving DecidableEq, Repr, Inhabited

/-- Whether the target carries a leading `.` or `~` sigil. -/
def hasSigil (target : String) : Bool :=
  target.startsWith "." || target.startsWith "~"

/-- The reference target: the name with a leading sigil removed, if present. -/
def strippedTarget (target : String) : String :=
  if hasSigil target then target.drop 1 else target
-- pure-end

-- post-conditions-start
/-- The node built for an info-field type annotation, given the surrounding
namespace context `ctx` and the annotation `target`. The node requests
scope-aware resolution, its reference target is the sigil-stripped name, and —
crucially — it records the surrounding namespace context: its module and class
equal the current module and enclosing class. -/
def problem_spec_makeXref
    (ctx : RefContext) (target : String) (result : XrefNode) : Prop :=
  result.refspecific = true ∧
  result.reftarget = strippedTarget target ∧
  result.pyModule = ctx.module ∧
  result.pyClass = ctx.cls
-- post-conditions-end

-- impl-start
def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=
  Id.run do
    let mut result : XrefNode :=
      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
    result := { result with refspecific := true }
    result := { result with pyModule := ctx.module }
    result := { result with pyClass := ctx.cls }
    if hasSigil target then
      result := { result with reftarget := target.drop 1 }
    return result
-- impl-end

-- proof-start
theorem correct_makeXref :
    ∀ (ctx : RefContext) (target : String),
      problem_spec_makeXref ctx target (implementation_makeXref ctx target) := by
  intro ctx target
  unfold problem_spec_makeXref implementation_makeXref strippedTarget
  simp only [Id.run, bind, pure]
  by_cases h : hasSigil target <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Fully functional spec: problem_spec_makeXref is a forall over (ctx, target) pinning ALL FOUR observed node attributes exactly to input-functions (refspecific=true, reftarget=strippedTarget target, pyModule=ctx.module, pyClass=ctx.cls). No unconstrained output component exists. axioms region is comment-only (no axiom/opaque decls); refinement.md legs are all R (type refinements #1-3) or I (concrete/deep-modeled ops #4-9) with NO A-consumed/A-reference/kind-3 legs, so there is no callee correspondence that could drift; G-AX is a legitimate skip stub and G-CONF differential-tests the R/I leg. 

Protocol: all 8 files confirmed same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Verifications run concurrently (<=4/batch) via `bash scripts/lean_verify.sh $F` from project root.

Positive control (gold impl): exit 0; `#print axioms correct_makeXref` => depends on axioms: [propext] (clean, no sorry).

prepatch bug reproduced (atk_1, Solution_prepatch.lean impl: omits pyModule/pyClass writes so they stay none): exit 1, application-type-mismatch/unsolved goals from carried gold proof.

6 further DISTINCT wrong impls, each carrying the gold proof body: atk_2 partial-domain (drop pyClass write, stays none) exit1 unsolved goals; atk_3 control-flow-effect (never strip sigil, reftarget stays =target) exit1; atk_4 control-flow-effect (swap module<->class assignments) exit1 unsolved goals; atk_5 ungrounded-oracle echo (refspecific left false) exit1 unsolved goals; atk_6 boundary (unconditional target.drop 1 even without sigil) exit1 unsolved goals; atk_7 boundary/partial-domain (strip '.' only, not '~') exit1 unsolved goals.

Every same-spec wrong impl FAILED to verify with genuine proof errors (unsolved goals / type mismatch); NONE closed with clean axioms. Therefore protocol step 2 (materialize faithful patch + run_resolve) had no triggering candidate — no verifying-but-wrong impl exists to break the spec. verify=>correct holds. Verdict SOUND after >=5 distinct attacks (7 total incl. prepatch) all run and none breaking it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack: does problem_spec_makeXref over-constrain / drift from the real callee (PyXrefMixin.make_xref post-patch at sphinx/domains/python.py:269-284)? Conclusion: FAITHFUL — no diverging input found.

Modeled step: PyXrefMixin.make_xref (post-patch). Real code writes exactly the four observed attributes:
  result['refspecific']=True; result['py:module']=env.ref_context.get('py:module'); result['py:class']=env.ref_context.get('py:class'); reftarget from super().make_xref = target, rewritten to target[1:] iff target.startswith(('.','~')).
super().make_xref (util/docfields.py:68) sets reftarget=target on a pending_xref; process_field_xref is a py-domain no-op (base Domain.process_field_xref = pass; python.py does NOT override it), so reftarget is untouched before the patched writes. The `~` display-TEXT rewrite (result.traverse(nodes.Text)) is UNCHANGED by the patch and not an observed node attribute — correctly framed out of the model.

The spec pins each of the four attributes to a direct function of the inputs (refspecific=true, reftarget=strippedTarget target, pyModule=ctx.module, pyClass=ctx.cls). This is precisely what the real callee produces; it is not stronger than reality. Bijection module/class: string↔some, missing/None↔none (dict.get semantics), exercised in conformance oracle with real dict-backed ref_context.

Evidence:
- same_spec(Solution, Solution_prepatch, lean.language) = True (spec region byte-identical; prepatch differs only in impl/proof, correctly).
- Solution.lean compiles via lean_verify.sh (exit 0, no sorry).
- #print axioms correct_makeXref => [propext] only (Mathlib-standard; no sorryAx, proof is real).
- conformance_check.py: checked=120480 disagreements=0 (exhaustive over structured pools + 120k fuzz, seed 8551), differential against in-process replica of post-patch attribute writes.
- Independent adversarial real-vs-model diff over 15 hand-picked edge cases (empty target, bare '.'/'~', '~~', '...', non-ASCII '§'/'π', whitespace-after-sigil, dotted names, empty module/class strings): 0 divergences. Note target.startswith(('.','~')) checks first char only; '. x' strips to ' x' in both real and model; empty string is non-sigil in both — aligned.

No input on which the modeled function disagrees with the real callee's observable node construction. Spec is faithful and not over-strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (not hints/mapping.md/refinement.md, which are auditor-only artifacts). Spec region confirmed canonical: same_spec(Solution, Solution_prepatch)=True; mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path, no patched-symbol identifier/comment echo, no narration). Gold edit = add result['py:module']=env.ref_context.get('py:module') and result['py:class']=env.ref_context.get('py:class') in sphinx/domains/python.py (+ env-threading plumbing in util/docfields.py). The public problem_statement ALREADY discloses: the bug (implicit :type:/:rtype: xrefs search every submodule rather than current-then-parent modules), that explicit xref roles resolve correctly, the expected scope-aware behavior, and the py:module/py:class/py:currentmodule vocabulary (verbatim in the repro RST). The spec view's postcondition (pyModule=ctx.module, pyClass=ctx.cls, refspecific=true, reftarget=strippedTarget) and docstring ('record the surrounding namespace context so an unqualified name resolves the way an explicit reference would') are a faithful formal restatement of that public expected behavior — behavior-level, not edit-level. It does not name the patched file/module, the env.ref_context.get read, or the docfields.py env= threading. A faithful behavioral spec necessarily pins correct output; that is not gold reconstruction beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
