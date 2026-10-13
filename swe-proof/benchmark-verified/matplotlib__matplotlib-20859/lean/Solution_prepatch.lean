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
    (p : Parent) : Except Unit (Bool × Nat) := Id.run do
  if isAxesKind p.kind then
    return .ok (true, p.ownerFigureId)
  else if p.kind = .topCanvas then
    return .ok (false, p.selfId)
  else
    return .error ()
-- impl-end

-- proof-start
theorem correct_resolveLegendParent :
    ∀ (p : Parent),
      problem_spec_resolveLegendParent p (implementation_resolveLegendParent p) := by
  intro p
  refine ⟨?_, ?_, ?_⟩
  · intro hax
    unfold implementation_resolveLegendParent
    simp [hax]
  · intro hax hcv
    unfold implementation_resolveLegendParent
    cases p.kind <;> simp_all [isAxesKind, isCanvasKind]
  · intro hax hcv
    unfold implementation_resolveLegendParent
    cases p.kind <;> simp_all [isAxesKind, isCanvasKind]
-- proof-end
