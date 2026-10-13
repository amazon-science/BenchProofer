import Mathlib
-- imports-end

/-!
Deciding whether a model triggers the "auto-created primary key" advisory.

A model is examined for one specific advisory (identifier `models.W042`): it is
emitted when the model's primary key was created automatically (the author did
not declare a primary key type) AND the project has not opted into a configured
default primary-key type at either the project level or the owning application
level.

There is one situation in which an auto-created primary key must NOT raise the
advisory even when no default type is configured: when the model's primary key
is not really the model's own field but a to-one relation that links the model
to a parent model — i.e. the model takes its primary key from a parent it
extends. In that case the primary key is the responsibility of the parent, so
the advisory belongs (if anywhere) to the parent and is suppressed here.

The result is the list of advisories this examination contributes: it is either
empty, or the single `models.W042` advisory carrying the model it concerns and
the standard message/hint text supplied for it. The advisory's contents are
constant inputs carried through unchanged; only WHETHER it is emitted is
decided here.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. Every value
-- the decision inspects (whether the primary key was auto-created, whether it
-- is a to-one relation, whether that relation links to a parent, and whether a
-- default primary-key type was opted into at the project or application level)
-- is a pure boolean observation of the model, carried in as input data; and the
-- advisory's message/hint/identifier are constant text carried through verbatim.
-- So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A single advisory produced by the examination.
* `id`   — the advisory identifier (the constant tag `models.W042`);
* `obj`  — the model the advisory concerns (modeled as a `Nat` identity; the
           name↔`Nat` bijection is in mapping.md);
* `msg`  — the advisory message text;
* `hint` — the advisory hint text. -/
structure Advisory where
  id : String
  obj : Nat
  msg : String
  hint : String
deriving DecidableEq, Repr

/-- The boolean observations the examination reads about a model. -/
structure CheckInput where
  /-- The primary key was created automatically (no primary key was declared). -/
  autoCreated : Bool
  /-- The primary key field is a to-one relation. -/
  pkIsToOneRelation : Bool
  /-- That to-one relation links this model to a parent model it extends. -/
  pkRelationIsParentLink : Bool
  /-- A default primary-key type was opted into at the project level. -/
  defaultAutoFieldOverridden : Bool
  /-- A default primary-key type was opted into at the owning application level. -/
  appConfigOverridden : Bool
  /-- Identity of the model the advisory would concern. -/
  modelObj : Nat
  /-- The advisory message text supplied for this model. -/
  warnMsg : String
  /-- The advisory hint text supplied for this model. -/
  warnHint : String

/-- The decision: the advisory is emitted exactly when the primary key was
auto-created, is NOT a parent-linking to-one relation, and no default
primary-key type was opted into at either the project or application level. -/
def reportAutoPkIssue (c : CheckInput) : Bool :=
  c.autoCreated
    && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
    && !c.defaultAutoFieldOverridden
    && !c.appConfigOverridden

/-- The advisory carried for a model when it is emitted: the constant `models.W042`
identifier, the model identity, and the supplied message/hint text. -/
def autoPkWarning (c : CheckInput) : Advisory :=
  { id := "models.W042", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint }
-- pure-end

-- post-conditions-start
/-- The examination contributes exactly the single `models.W042` advisory when
`reportAutoPkIssue` holds, and contributes nothing otherwise. Both the presence
of the advisory and — when present — its full contents are pinned to the input:
nothing else may appear and no field of the advisory may be invented. -/
def problem_spec_checkDefaultPk (c : CheckInput) (result : List Advisory) : Prop :=
  result = (if reportAutoPkIssue c then [autoPkWarning c] else [])
-- post-conditions-end

-- impl-start
def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
  if c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden then
    return [{ id := "models.W042", obj := c.modelObj,
              msg := c.warnMsg, hint := c.warnHint }]
  return []
-- impl-end

-- proof-start
theorem correct_checkDefaultPk :
    ∀ (c : CheckInput),
      problem_spec_checkDefaultPk c (implementation_checkDefaultPk c) := by
  intro c
  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning
  by_cases h : c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden
  · simp only [h, Id.run, if_true]; rfl
  · simp only [h, Id.run]; rfl
-- proof-end
