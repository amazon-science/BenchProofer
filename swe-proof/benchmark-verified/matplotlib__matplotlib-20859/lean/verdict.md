# P2 adversarial audit — matplotlib__matplotlib-20859

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     (p : Parent) : Except Unit (Bool × Nat) := Id.run do
   if isAxesKind p.kind then
     return .ok (true, p.ownerFigureId)
-  else if isCanvasKind p.kind then
+  else if p.kind = .topCanvas then
     return .ok (false, p.selfId)
   else
     return .error ()
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
 def implementation_resolveLegendParent
     (p : Parent) : Except Unit (Bool × Nat) := Id.run do
   if isAxesKind p.kind then
-    return .ok (true, p.ownerFigureId)
+    return .ok (true, p.selfId)
   else if isCanvasKind p.kind then
     return .ok (false, p.selfId)
   else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
 def implementation_resolveLegendParent
     (p : Parent) : Except Unit (Bool × Nat) := Id.run do
   if isAxesKind p.kind then
-    return .ok (true, p.ownerFigureId)
+    return .ok (false, p.ownerFigureId)
   else if isCanvasKind p.kind then
     return .ok (false, p.selfId)
   else
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
   if isAxesKind p.kind then
     return .ok (true, p.ownerFigureId)
   else if isCanvasKind p.kind then
-    return .ok (false, p.selfId)
+    return .ok (false, p.ownerFigureId)
   else
     return .error ()
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,10 +90,8 @@
     (p : Parent) : Except Unit (Bool × Nat) := Id.run do
   if isAxesKind p.kind then
     return .ok (true, p.ownerFigureId)
-  else if isCanvasKind p.kind then
+  else
     return .ok (false, p.selfId)
-  else
-    return .error ()
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     (p : Parent) : Except Unit (Bool × Nat) := Id.run do
   if isAxesKind p.kind then
     return .ok (true, p.ownerFigureId)
-  else if isCanvasKind p.kind then
+  else if p.kind = .subCanvas then
     return .ok (false, p.selfId)
   else
     return .error ()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the parent a legend is attached to.

A legend is created against a *parent* artist. From the kind of that parent the
constructor decides three things at once: whether the legend is an axes-level
legend, which underlying canvas object it records, and whether the parent is
acceptable at all.

The parent can be one of four kinds:

  * an **axes** — a plotting region that itself belongs to a canvas; the legend
    is an axes legend and records the canvas the axes lives on;
  * a **top-level canvas** — the whole drawing surface; the legend is not an axes
    legend and records that surface itself;
  * a **nested sub-canvas** — a canvas embedded inside another canvas; it is just
    as much a drawing surface as the top-level one, so the legend is again not an
    axes legend and records the sub-canvas itself;
  * **anything else** — not a drawing surface at all; such a parent is rejected.

Both the top-level canvas and a nested sub-canvas are *canvas-like* parents and
are treated identically: the legend is a non-axes legend recording the parent
object. Only a genuinely non-canvas, non-axes parent is rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The parent's
-- kind, its own object identity, and (for an axes parent) the identity of the
-- canvas it belongs to all enter as plain data. The two kind-tests are modeled
-- directly as predicates on the kind; recording a canvas object is modeled as
-- returning that object's identity. Hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The kind of artist a legend may be attached to. Mutually exclusive and
exhaustive. -/
inductive ParentKind
  | axes        -- a plotting region belonging to a canvas
  | topCanvas   -- the whole drawing surface
  | subCanvas   -- a drawing surface embedded inside another one
  | other       -- not a drawing surface
  deriving DecidableEq, Repr

/-- The parent a legend is attached to: its kind, its own object identity, and —
for an axes parent — the identity of the canvas it belongs to. -/
structure Parent where
  kind : ParentKind
  selfId : Nat
  ownerFigureId : Nat
  deriving Repr

/-- Whether the parent is a plotting region (an axes). -/
def isAxesKind : ParentKind → Bool
  | .axes => true
  | _ => false

/-- Whether the parent is a drawing surface (a canvas) of any nesting level —
both the top-level surface and an embedded sub-surface qualify. -/
def isCanvasKind : ParentKind → Bool
  | .topCanvas => true
  | .subCanvas => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- The dispatch result is fully pinned to the parent's kind:

  * an axes parent yields an axes legend (`isaxes = true`) recording the canvas
    the axes belongs to (`ownerFigureId`);
  * a non-axes parent that is canvas-like yields a non-axes legend
    (`isaxes = false`) recording the parent object itself (`selfId`);
  * a parent that is neither an axes nor canvas-like is rejected.

All three kinds of outcome are determined for every input, so no component of the
result is left free. -/
def problem_spec_resolveLegendParent
    (p : Parent) (result : Except Unit (Bool × Nat)) : Prop :=
  (isAxesKind p.kind = true → result = .ok (true, p.ownerFigureId)) ∧
  (isAxesKind p.kind = false → isCanvasKind p.kind = true →
      result = .ok (false, p.selfId)) ∧
  (isAxesKind p.kind = false → isCanvasKind p.kind = false →
      result = .error ())
-- post-conditions-end

-- impl-start
def implementation_resolveLegendParent
    (p : Parent) : Except Unit (Bool × Nat) :=
  match p.kind with
  | .axes => .ok (true, p.ownerFigureId)
  | .topCanvas => .ok (false, p.selfId)
  | .subCanvas => .ok (false, p.selfId)
  | .other => .error ()
-- impl-end

-- proof-start
theorem correct_resolveLegendParent :
    ∀ (p : Parent),
      problem_spec_resolveLegendParent p (implementation_resolveLegendParent p) := by
  intro p
  unfold problem_spec_resolveLegendParent implementation_resolveLegendParent
  cases p with
  | mk kind selfId ownerFigureId =>
    cases kind <;>
      simp [isAxesKind, isCanvasKind, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for matplotlib__matplotlib-20859 (lean). Spec is a TOTAL FUNCTIONAL specification: isAxesKind/isCanvasKind partition ParentKind into 3 exhaustive, mutually-exclusive classes (axes / topCanvas|subCanvas / other), each pinning the output uniquely (.ok(true,ownerFigureId) / .ok(false,selfId) / .error()). selfId and ownerFigureId are independent free Nat data fields, so no slack exists for a wrong impl to exploit. ANY impl that closes correct_resolveLegendParent is extensionally equal to gold on every input.

 Verify cmd: `bash scripts/lean_verify.sh <file>`. same_spec via swebench_unified.markers.same_spec(...,LeanBackend). Verifications run concurrently in 2 background batches of <=4.

same_spec=True for ALL 7 files (6 attacks + positive control) — impl region is the only edit; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL (pos_control.lean, distinct match-based correct impl): lean_verify exit=0; #print axioms correct_resolveLegendParent = [propext] only (clean, no sorryAx). Confirms verification is meaningful.

6 DISTINCT wrong impls, all FAIL to close (exit=1), unsolved goals:
- atk_1 (prepatch bug / control-flow: reject subCanvas via `else if p.kind=.topCanvas`): `case mk.subCanvas ⊢ False`. Reproduces the real bug (test_subfigure_legend F2P).
- atk_2 (ungrounded-oracle / wrong data: axes records selfId not ownerFigureId): `case mk.axes ⊢ selfId = ownerFigureId` (independent free Nats, unprovable).
- atk_3 (control-flow-effect: axes returns isaxes=false): `case mk.axes ⊢ False`.
- atk_4 (wrong data: canvas records ownerFigureId not selfId): `case mk.topCanvas ⊢ ownerFigureId = selfId` and `case mk.subCanvas ⊢ ownerFigureId = selfId`.
- atk_5 (partial-domain / over-accept: drop else, `other`→.ok(false,selfId)): `case mk.other ⊢ False`.
- atk_6 (boundary: reject topCanvas, accept only subCanvas): `case mk.topCanvas ⊢ False`.

No wrong impl produced a closing clean-axiom proof, therefore step-2 (materialize faithful patch + run_resolve) had ZERO candidates — there is no verify-but-not-resolve witness to exhibit. Speculation avoided; every attack was machine-checked.

REFINEMENT AUDIT (refinement.md + mapping.md + meta.json): all 5 legs are tagged R (1:1 with the post-patch isinstance dispatch ladder). NO A-legs: meta.json axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a legitimate skip stub (no consumed callee axiom, no deep-model reference — isinstance modeled deeply as isAxesKind/isCanvasKind predicates; figure object identity enters as data selfId/ownerFigureId). Every leg is R/I; no kind-3 leg. The A-leg correspondence audit is trivially satisfied because no A-legs exist. G-CONF conformance_check.py oracle faithfully mirrors the patched ladder (kind==axes→(True,owner); kind in {topCanvas,subCanvas}→(False,self); else error).

Verdict: SOUND — total functional spec over an exact 4-way kind partition; positive control verifies with clean [propext] axioms; 6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle, prepatch-bug) all fail to close. No closing-but-non-resolving impl exists; verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the parent a legend is attached to.

A legend is created against a *parent* artist. From the kind of that parent the
constructor decides three things at once: whether the legend is an axes-level
legend, which underlying canvas object it records, and whether the parent is
acceptable at all.

The parent can be one of four kinds:

  * an **axes** — a plotting region that itself belongs to a canvas; the legend
    is an axes legend and records the canvas the axes lives on;
  * a **top-level canvas** — the whole drawing surface; the legend is not an axes
    legend and records that surface itself;
  * a **nested sub-canvas** — a canvas embedded inside another canvas; it is just
    as much a drawing surface as the top-level one, so the legend is again not an
    axes legend and records the sub-canvas itself;
  * **anything else** — not a drawing surface at all; such a parent is rejected.

Both the top-level canvas and a nested sub-canvas are *canvas-like* parents and
are treated identically: the legend is a non-axes legend recording the parent
object. Only a genuinely non-canvas, non-axes parent is rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The parent's
-- kind, its own object identity, and (for an axes parent) the identity of the
-- canvas it belongs to all enter as plain data. The two kind-tests are modeled
-- directly as predicates on the kind; recording a canvas object is modeled as
-- returning that object's identity. Hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The kind of artist a legend may be attached to. Mutually exclusive and
exhaustive. -/
inductive ParentKind
  | axes        -- a plotting region belonging to a canvas
  | topCanvas   -- the whole drawing surface
  | subCanvas   -- a drawing surface embedded inside another one
  | other       -- not a drawing surface
  deriving DecidableEq, Repr

/-- The parent a legend is attached to: its kind, its own object identity, and —
for an axes parent — the identity of the canvas it belongs to. -/
structure Parent where
  kind : ParentKind
  selfId : Nat
  ownerFigureId : Nat
  deriving Repr

/-- Whether the parent is a plotting region (an axes). -/
def isAxesKind : ParentKind → Bool
  | .axes => true
  | _ => false

/-- Whether the parent is a drawing surface (a canvas) of any nesting level —
both the top-level surface and an embedded sub-surface qualify. -/
def isCanvasKind : ParentKind → Bool
  | .topCanvas => true
  | .subCanvas => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- The dispatch result is fully pinned to the parent's kind:

  * an axes parent yields an axes legend (`isaxes = true`) recording the canvas
    the axes belongs to (`ownerFigureId`);
  * a non-axes parent that is canvas-like yields a non-axes legend
    (`isaxes = false`) recording the parent object itself (`selfId`);
  * a parent that is neither an axes nor canvas-like is rejected.

All three kinds of outcome are determined for every input, so no component of the
result is left free. -/
def problem_spec_resolveLegendParent
    (p : Parent) (result : Except Unit (Bool × Nat)) : Prop :=
  (isAxesKind p.kind = true → result = .ok (true, p.ownerFigureId)) ∧
  (isAxesKind p.kind = false → isCanvasKind p.kind = true →
      result = .ok (false, p.selfId)) ∧
  (isAxesKind p.kind = false → isCanvasKind p.kind = false →
      result = .error ())
-- post-conditions-end

-- impl-start
def implementation_resolveLegendParent
    (p : Parent) : Except Unit (Bool × Nat) :=
  match p.kind with
  | .axes => .ok (true, p.ownerFigureId)
  | .topCanvas => .ok (false, p.selfId)
  | .subCanvas => .ok (false, p.selfId)
  | .other => .error ()
-- impl-end

-- proof-start
theorem correct_resolveLegendParent :
    ∀ (p : Parent),
      problem_spec_resolveLegendParent p (implementation_resolveLegendParent p) := by
  intro p
  unfold problem_spec_resolveLegendParent implementation_resolveLegendParent
  cases p with
  | mk kind selfId ownerFigureId =>
    cases kind <;>
      simp [isAxesKind, isCanvasKind, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for matplotlib__matplotlib-20859 (lean). Spec is a TOTAL FUNCTIONAL specification: isAxesKind/isCanvasKind partition ParentKind into 3 exhaustive, mutually-exclusive classes (axes / topCanvas|subCanvas / other), each pinning the output uniquely (.ok(true,ownerFigureId) / .ok(false,selfId) / .error()). selfId and ownerFigureId are independent free Nat data fields, so no slack exists for a wrong impl to exploit. ANY impl that closes correct_resolveLegendParent is extensionally equal to gold on every input.

 Verify cmd: `bash scripts/lean_verify.sh <file>`. same_spec via swebench_unified.markers.same_spec(...,LeanBackend). Verifications run concurrently in 2 background batches of <=4.

same_spec=True for ALL 7 files (6 attacks + positive control) — impl region is the only edit; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL (pos_control.lean, distinct match-based correct impl): lean_verify exit=0; #print axioms correct_resolveLegendParent = [propext] only (clean, no sorryAx). Confirms verification is meaningful.

6 DISTINCT wrong impls, all FAIL to close (exit=1), unsolved goals:
- atk_1 (prepatch bug / control-flow: reject subCanvas via `else if p.kind=.topCanvas`): `case mk.subCanvas ⊢ False`. Reproduces the real bug (test_subfigure_legend F2P).
- atk_2 (ungrounded-oracle / wrong data: axes records selfId not ownerFigureId): `case mk.axes ⊢ selfId = ownerFigureId` (independent free Nats, unprovable).
- atk_3 (control-flow-effect: axes returns isaxes=false): `case mk.axes ⊢ False`.
- atk_4 (wrong data: canvas records ownerFigureId not selfId): `case mk.topCanvas ⊢ ownerFigureId = selfId` and `case mk.subCanvas ⊢ ownerFigureId = selfId`.
- atk_5 (partial-domain / over-accept: drop else, `other`→.ok(false,selfId)): `case mk.other ⊢ False`.
- atk_6 (boundary: reject topCanvas, accept only subCanvas): `case mk.topCanvas ⊢ False`.

No wrong impl produced a closing clean-axiom proof, therefore step-2 (materialize faithful patch + run_resolve) had ZERO candidates — there is no verify-but-not-resolve witness to exhibit. Speculation avoided; every attack was machine-checked.

REFINEMENT AUDIT (refinement.md + mapping.md + meta.json): all 5 legs are tagged R (1:1 with the post-patch isinstance dispatch ladder). NO A-legs: meta.json axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a legitimate skip stub (no consumed callee axiom, no deep-model reference — isinstance modeled deeply as isAxesKind/isCanvasKind predicates; figure object identity enters as data selfId/ownerFigureId). Every leg is R/I; no kind-3 leg. The A-leg correspondence audit is trivially satisfied because no A-legs exist. G-CONF conformance_check.py oracle faithfully mirrors the patched ladder (kind==axes→(True,owner); kind in {topCanvas,subCanvas}→(False,self); else error).

Verdict: SOUND — total functional spec over an exact 4-way kind partition; positive control verifies with clean [propext] axioms; 6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle, prepatch-bug) all fail to close. No closing-but-non-resolving impl exists; verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) verified for the modeled parent-kind dispatch at the head of Legend.__init__ (lib/matplotlib/legend.py), post-patch (FigureBase arm).

### Spec integrity
- same_spec(Solution.lean, Solution_prepatch.lean) = True under real LeanBackend.language tables; spec views byte-identical + idempotent. Impl/proof regions are elided from the spec view, so the spec is not tainted by the impl.
- Solution.lean compiles via scripts/lean_verify.sh (exit 0); #print axioms correct_resolveLegendParent = [propext] only. No sorryAx: the proof is genuine.

### EMPIRICAL FAITHFULNESS (matplotlib 3.6.3 with the FigureBase fix, cross-checked by applying patch.diff to the base worktree @64619e53e9):
- axes parent: real isaxes=True, leg.figure IS parent.figure -> spec .ok(true, ownerFigureId). MATCH.
- top-level Figure: real isaxes=False, leg.figure IS parent -> spec .ok(false, selfId). MATCH.
- nested SubFigure: real isaxes=False, leg.figure IS the subfigure (not the parent fig); isinstance(sub, FigureBase)=True, isinstance(sub, Figure)=False -> spec .ok(false, selfId). MATCH (this is the F2P discriminator test_subfigure_legend).
- other (Line2D): real raises TypeError -> spec .error(). MATCH.

### No over-strong postcondition found
- I tested the FULL constructor observable (self.isaxes, id(self.figure)), not just the dispatch snippet, to catch any later __init__ mutation of self.figure that the spec would forbid. None occurs.
- Enum disjointness/exhaustiveness is faithful to the real class hierarchy: issubclass(Axes, FigureBase)=False and issubclass(SubFigure, Axes)=False, so no real parent object satisfies two isinstance branches; the if/elif priority (axes tested first) is correctly mirrored by testing isAxesKind before isCanvasKind. The 4-way ParentKind is genuinely mutually exclusive + exhaustive over {Axes, top Figure, SubFigure, other}.

The spec is neither too strong nor drifting: on every one of the four real parent kinds the modeled function agrees with the real (post-patch) callee. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: isinstance(parent, Figure) -> isinstance(parent, FigureBase) in Legend.__init__, accepting a nested SubFigure as a legend parent instead of raising TypeError. Baseline: the PUBLIC problem_statement already discloses far more than the spec view — it includes the full traceback ending in `raise TypeError("Legend needs either Axes or Figure as parent")` AND the explicit sentence 'Changing L437 here to check against `FigureBase` fixes it' with the exact GitHub line link (L433-L442). So the exact class name, lines, and fix are already public (hints_text, which only adds the unrelated bbox_extra_artists issue, is excluded per instructions).

Spec-view assessment: the Lean spec view (docstring + ParentKind/Parent/isAxesKind/isCanvasKind + problem_spec_resolveLegendParent) is STRICTLY MORE ABSTRACT than the public statement. It uses neutral identifiers (topCanvas, subCanvas, isCanvasKind) and never quotes any patched repo symbol (Figure, FigureBase, Legend, set_figure, isinstance) nor any gold-diff line. The only behavioral fact it encodes — a nested sub-canvas is a valid canvas-like parent that records itself — is exactly the bug's public subject and adds nothing beyond problem_statement.

Mechanical corroboration (PYTHONPATH=src): leakage.screen(Solution.lean, lean-backend, gold_patch, problem_statement) -> passed=True, hard_failures=[]. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) -> True (spec region byte-identical across the fix, so the spec was not re-tailored to the gold answer). spec_view renders with impl/proof stripped as expected. Conclusion: no line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
