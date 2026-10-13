import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is computed inside the modeled decision. The per-widget
-- "should this control expose a required marker" predicate is an input the
-- caller supplies (`widgetUseReq` / `subUseReq` below); its result is consumed,
-- not recomputed, so there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The attribute-relevant view of a bound field and its widget.
* `required` / `disabled` — the field-level flags.
* `hasRequireAllFields` — whether the field exposes the per-subfield-optional
  switch (a composite field does; a plain field does not).
* `requireAllFields` — that switch's value (relevant only when present).
* `isMultiWidget` — whether the field's widget is a composite of subwidgets.
* `subPairs` — one entry per (subfield, subwidget) pair taken together in order
  (mirroring the single paired walk over the two aligned sequences); each entry
  is `(subUseReq, subRequired)`: the subwidget's "expose a required marker"
  predicate result paired with that subfield's own required flag. -/
structure FieldInfo where
  required : Bool
  disabled : Bool
  hasRequireAllFields : Bool
  requireAllFields : Bool
  isMultiWidget : Bool
  subPairs : List (Bool × Bool)

/-- The attribute decisions produced for a bound field's widget.
* `parentRequired` — a required marker placed on the field's own widget.
* `parentDisabled` — a disabled marker placed on the field's own widget.
* `subwidgetRequired` — the required markers written to each subwidget, in order
  (empty unless the per-subwidget branch ran).
* `perSubBranch` — whether the per-subwidget placement branch ran. -/
structure Result where
  parentRequired : Bool
  parentDisabled : Bool
  subwidgetRequired : List Bool
  perSubBranch : Bool
-- pure-end

-- post-conditions-start
/-- The required-marker placement. The guard holds when the widget would expose a
required marker, the field is required, and the form enables required markers.
When the field is a composite of individually-optional subfields rendered through
a composite widget, the required markers are placed per subwidget — each one set
exactly when that subwidget would expose a marker AND its subfield is required —
and the field's own widget receives no required marker. Otherwise the field's own
widget receives the required marker. The disabled marker is placed on the field's
own widget exactly when the field is disabled. -/
def problem_spec_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) (result : Result) : Prop :=
  let guard := widgetUseReq && field.required && formUseReq
  let subBranch :=
    field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget
  result.parentDisabled = field.disabled ∧
  result.perSubBranch = (guard && subBranch) ∧
  result.parentRequired = (guard && !subBranch) ∧
  result.subwidgetRequired =
    (if guard && subBranch
     then field.subPairs.map (fun p => p.1 && p.2)
     else [])
-- post-conditions-end

-- impl-start
def implementation_requiredAttrs
    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do
  let mut parentRequired := false
  let mut parentDisabled := false
  let subwidgetRequired : List Bool := []
  let perSubBranch := false
  -- pre-patch placement: under the guard the required marker is always written to
  -- the field's own widget; the per-subwidget composite case is never considered.
  if widgetUseReq && field.required && formUseReq then
    parentRequired := true
  if field.disabled then
    parentDisabled := true
  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }
-- impl-end

-- proof-start
theorem correct_requiredAttrs :
    ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),
      problem_spec_requiredAttrs widgetUseReq formUseReq field
        (implementation_requiredAttrs widgetUseReq formUseReq field) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
