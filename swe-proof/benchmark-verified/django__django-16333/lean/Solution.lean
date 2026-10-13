import Mathlib
-- imports-end

/-!
Persisting a model-backed registration form.

A model-backed form, when asked to persist, builds a model instance from its
cleaned data, applies any derived field handling (here: deriving the stored
password from the supplied raw password), and — when the caller asks for an
immediate commit — writes the instance and ALSO writes the form's multi-valued
related selections so they are not lost. When the caller defers the commit,
nothing is written now: both the instance write and the related-selection write
are postponed.

The behavior exercised here is that a committed save of such a form persists
*both* the instance and the full set of multi-valued related selections the form
collected; a deferred save persists neither. The returned instance always carries
its derived password regardless of whether the save was committed. Every output
component is determined by the form's contents together with the commit choice.
-/

-- axioms-start
-- No UNCHANGED callee needs a consumed `opaque`/`axiom` contract here. The three
-- persistence sub-operations — building the instance from the form, writing the
-- instance, and writing the form's multi-valued related selections — are modeled
-- DEEPLY in the `pure`/impl regions as transformations of a `SaveOutcome` record
-- (A-reference: validated against the real persistence layer, not axiomatized).
-- The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- A model-backed form, observed through only the features that determine what a
persist does:

  * `password` — the raw secret the stored password is derived from;
  * `m2m` — the identities of the multi-valued related selections the form
    collected (a list of related-object ids). -/
structure FormData where
  /-- the raw password supplied in the form -/
  password : String
  /-- the identities of the multi-valued related selections collected by the form -/
  m2m : List Int
deriving Repr

/-- The built model instance, observed through the only touched fact: whether its
derived (stored) password has been applied. -/
structure UserObj where
  /-- whether the stored password has been derived from the form's raw password -/
  passwordSet : Bool
deriving Repr

/-- The outcome of persisting the form:

  * `user` — the built instance (always returned);
  * `instanceSaved` — whether the instance row was written;
  * `relatedSaved` — the multi-valued related selections that were written. -/
structure SaveOutcome where
  /-- the built (and returned) model instance -/
  user : UserObj
  /-- whether the instance row was written -/
  instanceSaved : Bool
  /-- the multi-valued related selections that were written -/
  relatedSaved : List Int
deriving Repr

/-- Build the model instance from the form, deferring the commit. Building this
way installs the deferred related-selection writer on the form, so a writer is
always available afterwards. The freshly built instance has no derived password
yet. -/
def buildInstance (_f : FormData) : UserObj := { passwordSet := false }
-- pure-end

-- post-conditions-start
/-- Persisting a model-backed form. The returned instance always carries its
derived password. On a committed save the instance row is written and the full
set of the form's multi-valued related selections is written; on a deferred save
neither is written. Every output component is pinned to the form contents and the
commit choice (directive 5 frame: `user.passwordSet` always true,
`instanceSaved` = `commit`, `relatedSaved` grounded in `f.m2m`; directive 8:
`relatedSaved` is produced from the form's own selections, never an oracle). -/
def problem_spec_persistForm
    (f : FormData) (commit : Bool) (result : SaveOutcome) : Prop :=
  result.user.passwordSet = true ∧
  result.instanceSaved = commit ∧
  result.relatedSaved = (if commit then f.m2m else [])
-- post-conditions-end

-- impl-start
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  Id.run do
    -- super().save(commit=False): build the instance and install the deferred
    -- related-selection writer (so a writer is always present afterwards).
    let mut user := buildInstance f
    let hasRelatedWriter := true
    -- derive the stored password from the form's raw password (always).
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      -- write the instance row …
      instanceSaved := true
      -- … and, when the related-selection writer is present, write the form's
      -- multi-valued related selections so they are not lost.
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }
-- impl-end

-- proof-start
theorem correct_persistForm : ∀ (f : FormData) (commit : Bool),
    problem_spec_persistForm f commit (implementation_persistForm f commit) := by
  intro f commit
  unfold problem_spec_persistForm implementation_persistForm
  cases commit <;> exact ⟨rfl, rfl, rfl⟩
-- proof-end
