# P2 adversarial audit — matplotlib__matplotlib-20859

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,13 +110,12 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
+    -- Pre-image skeleton: the second test is the NARROW top-level-canvas
+    -- membership test, so a nested sub-canvas fails it and is rejected as an
+    -- unsupported parent. The frozen spec accepts any figure-like canvas
+    -- (isCanvas), so prove_correct MUST fail on the nested sub-canvas case.
     let parentIsRegion : Bool := isRegion parent
-    let parentIsCanvas : Bool := isCanvas parent
+    let parentIsCanvas : Bool := isTopCanvas parent
     let out : Except AnchorErr Anchor :=
       if parentIsRegion then
         Except.ok { fromRegion := true, canvas := regionCanvas parent }
@@ -131,4 +130,4 @@
 prove_correct anchorToParent by
   loom_solve
   cases parent <;>
-    simp_all [anchorSpec, isRegion, isCanvas, regionCanvas, canvasId]
+    simp_all [anchorSpec, isRegion, isTopCanvas, regionCanvas, canvasId]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,19 +110,14 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
     let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
       if parentIsRegion then
-        Except.ok { fromRegion := true, canvas := regionCanvas parent }
+        Except.ok { fromRegion := false, canvas := regionCanvas parent }
       else
         if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
+          Except.ok { fromRegion := true, canvas := canvasId parent }
         else
           Except.error .unsupportedParent
     return out
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,16 +110,11 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
     let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
       if parentIsRegion then
-        Except.ok { fromRegion := true, canvas := regionCanvas parent }
+        Except.ok { fromRegion := true, canvas := canvasId parent }
       else
         if parentIsCanvas then
           Except.ok { fromRegion := false, canvas := canvasId parent }
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,21 +110,8 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
-    let parentIsRegion : Bool := isRegion parent
-    let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
-      if parentIsRegion then
-        Except.ok { fromRegion := true, canvas := regionCanvas parent }
-      else
-        if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
-        else
-          Except.error .unsupportedParent
+      Except.ok { fromRegion := false, canvas := canvasId parent }
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,21 +110,12 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
-    let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
       if parentIsRegion then
         Except.ok { fromRegion := true, canvas := regionCanvas parent }
       else
-        if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
-        else
-          Except.error .unsupportedParent
+        Except.error .unsupportedParent
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,11 +110,6 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
     let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
@@ -122,7 +117,7 @@
         Except.ok { fromRegion := true, canvas := regionCanvas parent }
       else
         if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
+          Except.ok { fromRegion := true, canvas := canvasId parent }
         else
           Except.error .unsupportedParent
     return out
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,11 +110,6 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
     let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
@@ -122,7 +117,7 @@
         Except.ok { fromRegion := true, canvas := regionCanvas parent }
       else
         if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
+          Except.ok { fromRegion := false, canvas := regionCanvas parent }
         else
           Except.error .unsupportedParent
     return out
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -110,21 +110,16 @@
   ensures out = anchorSpec parent
   do
     -- impl-start
-    -- Select the branch on the parent's kind. A plotting region binds the child
-    -- to its owning canvas; otherwise, a figure-like canvas of EITHER kind binds
-    -- the child directly to itself; anything else is not a valid parent. The
-    -- second test is the BROAD figure-like-canvas membership test, so a nested
-    -- sub-canvas is accepted on the same footing as a top-level one.
     let parentIsRegion : Bool := isRegion parent
     let parentIsCanvas : Bool := isCanvas parent
     let out : Except AnchorErr Anchor :=
-      if parentIsRegion then
-        Except.ok { fromRegion := true, canvas := regionCanvas parent }
+      if parentIsCanvas then
+        Except.ok { fromRegion := false, canvas := canvasId parent }
       else
-        if parentIsCanvas then
-          Except.ok { fromRegion := false, canvas := canvasId parent }
+        if parentIsRegion then
+          Except.error .unsupportedParent
         else
-          Except.error .unsupportedParent
+          Except.ok { fromRegion := true, canvas := regionCanvas parent }
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   runtime type-membership test that selects the dispatch branch — is modeled
   DEEPLY in the `pure` region (the `isRegion` / `isCanvas` / `isTopCanvas`
   predicates, with the structural invariant that the narrow canvas kind is a
   special case of the broad one) and validated == the real test by G-AX (an
   A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A parent container that a child object may be anchored to. There are exactly
   three observable shapes:
   * `region`  — a plotting region; it carries an owning canvas, recorded as the
     identity of that canvas;
   * `canvas`  — a figure-like drawing canvas. There are two kinds, distinguished
     by `topLevel`: a top-level canvas (`topLevel = true`) and a nested
     sub-canvas (`topLevel = false`). Its `id` is its own identity.
   * `other`   — anything else, which is not a valid parent.
   A nested sub-canvas is just as much a figure-like canvas as a top-level one
   (`isTopCanvas → isCanvas`, lemma below): both are accepted. -/
inductive Container where
  | region (canvas : Nat)
  | canvas (id : Nat) (topLevel : Bool)
  | other
  deriving DecidableEq

/- The parent is a plotting region. -/
@[grind] def isRegion : Container → Bool
  | .region _ => true
  | _         => false

/- The parent is a figure-like canvas of EITHER kind (top-level or nested). This
   is the broad membership test the desired behavior keys on. -/
@[grind] def isCanvas : Container → Bool
  | .canvas _ _ => true
  | _           => false

/- The parent is specifically a top-level canvas — the narrow membership test
   that a nested sub-canvas does NOT satisfy. -/
@[grind] def isTopCanvas : Container → Bool
  | .canvas _ t => t
  | _           => false

/- The owning canvas of a plotting region (0 elsewhere — never consulted off the
   region shape). -/
@[grind] def regionCanvas : Container → Nat
  | .region c => c
  | _         => 0

/- The identity of a figure-like canvas (0 elsewhere — never consulted off the
   canvas shape). -/
@[grind] def canvasId : Container → Nat
  | .canvas i _ => i
  | _           => 0

/- The narrow canvas kind is a special case of the broad one: anything that
   passes the narrow membership test also passes the broad test. This is the
   structural fact about the container kinds that G-AX validates against the
   real runtime type hierarchy (mapping.md §3.1). -/
@[grind] lemma isTopCanvas_imp_isCanvas (p : Container) :
    isTopCanvas p = true → isCanvas p = true := by
  cases p <;> simp [isTopCanvas, isCanvas]

/- Failure of anchoring: the parent is neither a plotting region nor a
   figure-like canvas. -/
inductive AnchorErr where
  | unsupportedParent
  deriving DecidableEq

/- The result of anchoring a child to its parent: a flag recording whether the
   parent was a plotting region, and the identity of the canvas the child is
   bound to. -/
structure Anchor where
  fromRegion : Bool
  canvas : Nat
  deriving DecidableEq

/- The intended anchoring: a plotting region binds the child to that region's
   owning canvas (and records that it came from a region); a figure-like canvas
   of EITHER kind binds the child directly to that canvas; any other parent is
   rejected. -/
def anchorSpec : Container → Except AnchorErr Anchor
  | .region c   => Except.ok { fromRegion := true,  canvas := c }
  | .canvas i _ => Except.ok { fromRegion := false, canvas := i }
  | .other      => Except.error .unsupportedParent

@[grind] lemma anchorSpec_region (c : Nat) :
    anchorSpec (.region c) = Except.ok { fromRegion := true, canvas := c } := rfl
@[grind] lemma anchorSpec_canvas (i : Nat) (t : Bool) :
    anchorSpec (.canvas i t) = Except.ok { fromRegion := false, canvas := i } := rfl
@[grind] lemma anchorSpec_other :
    anchorSpec .other = Except.error .unsupportedParent := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method anchorToParent (parent : Container) return (out : Except AnchorErr Anchor)
  ensures out = anchorSpec parent
  do
    -- impl-start
    let out : Except AnchorErr Anchor :=
      match parent with
      | .region c   => Except.ok { fromRegion := true,  canvas := c }
      | .canvas i _ => Except.ok { fromRegion := false, canvas := i }
      | .other      => Except.error .unsupportedParent
    return out
    -- impl-end

prove_correct anchorToParent by
  loom_solve
  all_goals (cases parent <;> simp_all [anchorSpec])
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify⇒correct holds because the spec is an EXACT EQUALITY against a total, fully-concrete function: `method anchorToParent (parent : Container) ... ensures out = anchorSpec parent`, where anchorSpec is the total 3-branch dispatch (.region c → ok{fromRegion:=true,canvas:=c}; .canvas i _ → ok{fromRegion:=false,canvas:=i}; .other → error). Any impl that verifies is forced to be pointwise-equal to anchorSpec on all inputs, i.e. behaviorally correct by construction. There is therefore NO verifying-but-wrong impl, so the break condition (a verifying wrong impl whose faithful refined patch does NOT resolve) is unreachable — no patches to materialize/run through run_resolve (patches={} is correct, not a skipped step).

Ran lean_verify.sh from there with; same_spec via python (the module import needs that venv).

SAME-SPEC: all 8 attacks + positive_control confirmed same_spec=True against Solution.lean (axioms/pure/pre/post byte-identical; only impl region — and, for positive_control, the post-impl proof block, which is not part of the spec view — edited).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
- positive_control.lean (structurally-DIFFERENT correct impl: `match parent with ...` instead of the if isRegion/isCanvas ladder; proof `loom_solve; all_goals (cases parent <;> simp_all [anchorSpec])`): EXIT 0 (verifies, no sorry; only linter warnings). Spec is non-vacuous. [Note: an initial positive_control that reused the shipped if-ladder proof failed with 'No goals to be solved' because loom_solve already discharges the match form — a proof-tactic artifact, not a spec/impl issue; corrected proof verifies.]
- atk_1.lean = PREPATCH bug (narrow isTopCanvas for the canvas test): EXIT 1, unsolved goal `case canvas ⊢ topLevel✝ = true` — the exact nested-sub-canvas discriminator (spec forces acceptance of topLevel=false; narrow test rejects it). PREPATCH REPRODUCED; identical failure to Solution_prepatch.lean.
- atk_2.lean (fromRegion flags swapped, control-flow-effect): EXIT 1, `⊢ False` on region+canvas — caught by Anchor.fromRegion field.
- atk_3.lean (region binds canvasId≡0 instead of regionCanvas, wrong value): EXIT 1, `⊢ 0 = canvas✝` on region branch.
- atk_4.lean (partial-domain / ungrounded echo: accept EVERYTHING as canvas, echo canvasId, no .other error): EXIT 1, `⊢ False` on region+other — caught by region branch + .other→error clause.
- atk_5.lean (partial-domain: canvas rejected, only region accepted): EXIT 1, `⊢ False` on canvas branch.
- atk_6.lean (boundary/effect: canvas branch sets fromRegion:=true): EXIT 1, `⊢ False` on canvas branch.
- atk_7.lean (wrong canvas value: canvas branch binds regionCanvas≡0): EXIT 1, `⊢ 0 = id✝` on canvas branch.
- atk_8.lean (control-flow-effect: region/canvas consequences swapped): EXIT 1, `⊢ False` on region+other.
All failures are genuine unsolved-postcondition goals, not syntax errors.

REFINEMENT AUDIT (refinement.md): A-legs concentrated on. isRegion/isCanvas/isTopCanvas are A-REFERENCEs (deep models of the unchanged builtin `isinstance` against unchanged classes Axes/FigureBase/Figure), validated ==real by G-AX; NO consumed/module-level axiom exists. Correspondence holds: the discriminating change (Figure→FigureBase) is modeled by the BROAD isCanvas predicate (canvas branch accepts BOTH topLevel values) + the isTopCanvas→isCanvas lemma; anchorSpec's `.canvas i _` (wildcard on topLevel) pins acceptance of the nested sub-canvas (topLevel=false), i.e. the POST-gold behavior on the F2P input. Legs A1–A4 are R / A-reference / I; NO kind-3 (the one genuinely changed op is modeled deeply, never behind an axiom about the function under change). model↔patch: Container↔parent (region↔Axes, canvas id topLevel↔FigureBase w/ topLevel=isinstance(.,Figure), other↔else), Anchor.fromRegion↔self.isaxes, Anchor.canvas↔id of set_figure target, error↔TypeError — consistent with mapping.md §2 bijection.

CONCLUSION: ≥5 (8) distinct verifying-attack candidates spanning partial-domain (atk_4,atk_5), boundary/flag (atk_6), control-flow-effect (atk_2,atk_8), wrong-value (atk_3,atk_7), and the prepatch bug (atk_1); ungrounded-oracle echo (atk_4 + field echoes atk_3/atk_6/atk_7) all rejected. None verifies, so none can break the spec. Exact-equality-against-total-concrete-function ⇒ verify⇒correct. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   runtime type-membership test that selects the dispatch branch — is modeled
   DEEPLY in the `pure` region (the `isRegion` / `isCanvas` / `isTopCanvas`
   predicates, with the structural invariant that the narrow canvas kind is a
   special case of the broad one) and validated == the real test by G-AX (an
   A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A parent container that a child object may be anchored to. There are exactly
   three observable shapes:
   * `region`  — a plotting region; it carries an owning canvas, recorded as the
     identity of that canvas;
   * `canvas`  — a figure-like drawing canvas. There are two kinds, distinguished
     by `topLevel`: a top-level canvas (`topLevel = true`) and a nested
     sub-canvas (`topLevel = false`). Its `id` is its own identity.
   * `other`   — anything else, which is not a valid parent.
   A nested sub-canvas is just as much a figure-like canvas as a top-level one
   (`isTopCanvas → isCanvas`, lemma below): both are accepted. -/
inductive Container where
  | region (canvas : Nat)
  | canvas (id : Nat) (topLevel : Bool)
  | other
  deriving DecidableEq

/- The parent is a plotting region. -/
@[grind] def isRegion : Container → Bool
  | .region _ => true
  | _         => false

/- The parent is a figure-like canvas of EITHER kind (top-level or nested). This
   is the broad membership test the desired behavior keys on. -/
@[grind] def isCanvas : Container → Bool
  | .canvas _ _ => true
  | _           => false

/- The parent is specifically a top-level canvas — the narrow membership test
   that a nested sub-canvas does NOT satisfy. -/
@[grind] def isTopCanvas : Container → Bool
  | .canvas _ t => t
  | _           => false

/- The owning canvas of a plotting region (0 elsewhere — never consulted off the
   region shape). -/
@[grind] def regionCanvas : Container → Nat
  | .region c => c
  | _         => 0

/- The identity of a figure-like canvas (0 elsewhere — never consulted off the
   canvas shape). -/
@[grind] def canvasId : Container → Nat
  | .canvas i _ => i
  | _           => 0

/- The narrow canvas kind is a special case of the broad one: anything that
   passes the narrow membership test also passes the broad test. This is the
   structural fact about the container kinds that G-AX validates against the
   real runtime type hierarchy (mapping.md §3.1). -/
@[grind] lemma isTopCanvas_imp_isCanvas (p : Container) :
    isTopCanvas p = true → isCanvas p = true := by
  cases p <;> simp [isTopCanvas, isCanvas]

/- Failure of anchoring: the parent is neither a plotting region nor a
   figure-like canvas. -/
inductive AnchorErr where
  | unsupportedParent
  deriving DecidableEq

/- The result of anchoring a child to its parent: a flag recording whether the
   parent was a plotting region, and the identity of the canvas the child is
   bound to. -/
structure Anchor where
  fromRegion : Bool
  canvas : Nat
  deriving DecidableEq

/- The intended anchoring: a plotting region binds the child to that region's
   owning canvas (and records that it came from a region); a figure-like canvas
   of EITHER kind binds the child directly to that canvas; any other parent is
   rejected. -/
def anchorSpec : Container → Except AnchorErr Anchor
  | .region c   => Except.ok { fromRegion := true,  canvas := c }
  | .canvas i _ => Except.ok { fromRegion := false, canvas := i }
  | .other      => Except.error .unsupportedParent

@[grind] lemma anchorSpec_region (c : Nat) :
    anchorSpec (.region c) = Except.ok { fromRegion := true, canvas := c } := rfl
@[grind] lemma anchorSpec_canvas (i : Nat) (t : Bool) :
    anchorSpec (.canvas i t) = Except.ok { fromRegion := false, canvas := i } := rfl
@[grind] lemma anchorSpec_other :
    anchorSpec .other = Except.error .unsupportedParent := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method anchorToParent (parent : Container) return (out : Except AnchorErr Anchor)
  ensures out = anchorSpec parent
  do
    -- impl-start
    let out : Except AnchorErr Anchor :=
      match parent with
      | .region c   => Except.ok { fromRegion := true,  canvas := c }
      | .canvas i _ => Except.ok { fromRegion := false, canvas := i }
      | .other      => Except.error .unsupportedParent
    return out
    -- impl-end

prove_correct anchorToParent by
  loom_solve
  all_goals (cases parent <;> simp_all [anchorSpec])
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify⇒correct holds because the spec is an EXACT EQUALITY against a total, fully-concrete function: `method anchorToParent (parent : Container) ... ensures out = anchorSpec parent`, where anchorSpec is the total 3-branch dispatch (.region c → ok{fromRegion:=true,canvas:=c}; .canvas i _ → ok{fromRegion:=false,canvas:=i}; .other → error). Any impl that verifies is forced to be pointwise-equal to anchorSpec on all inputs, i.e. behaviorally correct by construction. There is therefore NO verifying-but-wrong impl, so the break condition (a verifying wrong impl whose faithful refined patch does NOT resolve) is unreachable — no patches to materialize/run through run_resolve (patches={} is correct, not a skipped step).

Ran lean_verify.sh from there with; same_spec via python (the module import needs that venv).

SAME-SPEC: all 8 attacks + positive_control confirmed same_spec=True against Solution.lean (axioms/pure/pre/post byte-identical; only impl region — and, for positive_control, the post-impl proof block, which is not part of the spec view — edited).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
- positive_control.lean (structurally-DIFFERENT correct impl: `match parent with ...` instead of the if isRegion/isCanvas ladder; proof `loom_solve; all_goals (cases parent <;> simp_all [anchorSpec])`): EXIT 0 (verifies, no sorry; only linter warnings). Spec is non-vacuous. [Note: an initial positive_control that reused the shipped if-ladder proof failed with 'No goals to be solved' because loom_solve already discharges the match form — a proof-tactic artifact, not a spec/impl issue; corrected proof verifies.]
- atk_1.lean = PREPATCH bug (narrow isTopCanvas for the canvas test): EXIT 1, unsolved goal `case canvas ⊢ topLevel✝ = true` — the exact nested-sub-canvas discriminator (spec forces acceptance of topLevel=false; narrow test rejects it). PREPATCH REPRODUCED; identical failure to Solution_prepatch.lean.
- atk_2.lean (fromRegion flags swapped, control-flow-effect): EXIT 1, `⊢ False` on region+canvas — caught by Anchor.fromRegion field.
- atk_3.lean (region binds canvasId≡0 instead of regionCanvas, wrong value): EXIT 1, `⊢ 0 = canvas✝` on region branch.
- atk_4.lean (partial-domain / ungrounded echo: accept EVERYTHING as canvas, echo canvasId, no .other error): EXIT 1, `⊢ False` on region+other — caught by region branch + .other→error clause.
- atk_5.lean (partial-domain: canvas rejected, only region accepted): EXIT 1, `⊢ False` on canvas branch.
- atk_6.lean (boundary/effect: canvas branch sets fromRegion:=true): EXIT 1, `⊢ False` on canvas branch.
- atk_7.lean (wrong canvas value: canvas branch binds regionCanvas≡0): EXIT 1, `⊢ 0 = id✝` on canvas branch.
- atk_8.lean (control-flow-effect: region/canvas consequences swapped): EXIT 1, `⊢ False` on region+other.
All failures are genuine unsolved-postcondition goals, not syntax errors.

REFINEMENT AUDIT (refinement.md): A-legs concentrated on. isRegion/isCanvas/isTopCanvas are A-REFERENCEs (deep models of the unchanged builtin `isinstance` against unchanged classes Axes/FigureBase/Figure), validated ==real by G-AX; NO consumed/module-level axiom exists. Correspondence holds: the discriminating change (Figure→FigureBase) is modeled by the BROAD isCanvas predicate (canvas branch accepts BOTH topLevel values) + the isTopCanvas→isCanvas lemma; anchorSpec's `.canvas i _` (wildcard on topLevel) pins acceptance of the nested sub-canvas (topLevel=false), i.e. the POST-gold behavior on the F2P input. Legs A1–A4 are R / A-reference / I; NO kind-3 (the one genuinely changed op is modeled deeply, never behind an axiom about the function under change). model↔patch: Container↔parent (region↔Axes, canvas id topLevel↔FigureBase w/ topLevel=isinstance(.,Figure), other↔else), Anchor.fromRegion↔self.isaxes, Anchor.canvas↔id of set_figure target, error↔TypeError — consistent with mapping.md §2 bijection.

CONCLUSION: ≥5 (8) distinct verifying-attack candidates spanning partial-domain (atk_4,atk_5), boundary/flag (atk_6), control-flow-effect (atk_2,atk_8), wrong-value (atk_3,atk_7), and the prepatch bug (atk_1); ungrounded-oracle echo (atk_4 + field echoes atk_3/atk_6/atk_7) all rejected. None verifies, so none can break the spec. Exact-equality-against-total-concrete-function ⇒ verify⇒correct. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (velvet backend) => same_spec: True. Solution.lean elaborates cleanly under scripts/lean_verify.sh (exit 0, no sorry/error). patch.diff is the verbatim gold (Figure -> FigureBase in isinstance test + message text). Faithfulness check of anchorSpec against the real post-patch Legend.__init__ dispatch (legend.py:451-461 in worktree): Axes -> isaxes=True, set_figure(parent.figure) matches .region c -> ok{fromRegion=true, canvas=c}; the region test is tried first in both, so the if/elif priority is preserved. (2) FigureBase (Figure OR SubFigure) -> isaxes=False, set_figure(parent) matches .canvas i _ -> ok{fromRegion=false, canvas=i} for BOTH topLevel values, exactly the broadened FigureBase membership; since SubFigure subclasses FigureBase, isinstance(subfig,FigureBase)==True, so the model accepting .canvas i false is faithful, not too strong. (3) any other object -> TypeError matches .other -> error .unsupportedParent. Class trees Axes and FigureBase are disjoint so no object triggers the wrong arm; the identity-Nat abstraction (id(parent.figure)/id(parent)) is a total faithful carrier for the only observable (which canvas). The only model gap is the unmodeled self.axes=parent side-effect, which makes the spec WEAKER (under-model), not stronger — irrelevant to a faithfulness/over-strength break. No input exists where anchorSpec disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: broaden isinstance(parent, Figure) -> isinstance(parent, FigureBase) at legend.py L437 (plus the local import Figure->FigureBase and the TypeError message text). The discriminating content is: a nested SubFigure (FigureBase but not Figure) must be accepted instead of rejected.

The public problem_statement (from test.jsonl, NOT hints_text) already discloses the fix verbatim: 'Changing L437 here to check against `FigureBase` fixes it.' Confirmed programmatically that both 'FigureBase' and 'L437' appear in problem_statement (True/True). The problem_statement also shows the pre-patch error message 'Legend needs either Axes or Figure as parent' and links directly to the L433-442 dispatch ladder. So the class name, the exact line, the pre-patch message, and the precise nature of the fix are all PUBLIC baseline.

The spec view (Solution.lean, what G-LEAK screens via bundle.solution_src()) is a strictly more abstract restatement: a Container inductive with region/canvas(topLevel)/other shapes, a broad isCanvas vs narrow isTopCanvas predicate, and anchorSpec that accepts a figure-like canvas of EITHER kind and rejects .other. This mirrors the fix's behavior (accept nested sub-canvas) but reveals nothing about the concrete gold edit beyond what problem_statement already states publicly — no Python class names, no line numbers, no message strings, just an abstracted behavioral spec whose key point (accept both canvas kinds) is exactly what the reporter prescribed.

Checked leak.py: G-LEAK is lexical over solution_src vs (patch, problem_statement); the baseline it subtracts is problem_statement, which here already contains the full fix. No spec-view line leaks the gold edit beyond that public baseline.

Note (out of scope for panel_3): the frozen spec region is NOT byte-identical between Solution.lean and Solution_prepatch.lean, but the divergence is confined to the impl block (isCanvas vs isTopCanvas) and the matching prove_correct proof tactic list — i.e. the impl/proof side, not the ensures/spec. same_spec could not be run directly (signature needs a 'tables' arg); manual masking of impl-start/impl-end shows only proof-line differences remain. This is an impl/G-DIFF concern, not a leakage concern.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
