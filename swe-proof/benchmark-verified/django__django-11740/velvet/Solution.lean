import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign computation — turning a referential
   field into the set of model dependencies it induces — is modeled DEEPLY by
   `relationDeps` (pure region) and validated `relationDeps == the real
   dependency computation` by axiom_check.py (G-AX, an A-reference; mapping.md
   §3.1). The modeled behaviour is pure data-flow over the field's referential
   configuration. -/
-- axioms-end

-- pure-start
/- A single ordering dependency a schema-change operation can carry: the
   `(app, object-name)` of the model it must be sequenced after, an optional
   field name, and whether the referenced model must already exist. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on an `(app, object-name)` pair, carrying no field
   name. -/
def mkDep (app name : String) : Dep :=
  { app := app, name := name, fieldName := none, create := true }

/- The referential configuration of a field that points at another model: the
   model it points to (`targetApp`/`targetObj`), the intermediary model the
   relation is routed through when there is one (`through`, an `(app, object)`
   pair), and a swappable-setting name when the target is a swappable model
   (`swappable`). -/
structure RelField where
  targetApp : String
  targetObj : String
  through : Option (String × String)
  swappable : Option String
deriving Inhabited

/- The base dependency a referential field induces on the model it points to:
   the swappable setting under a sentinel app when the target is swappable,
   otherwise the target model itself. -/
def baseDep (f : RelField) : Dep :=
  match f.swappable with
  | some s => mkDep "__setting__" s
  | none   => mkDep f.targetApp f.targetObj

/- The full set of dependencies a referential field induces: always the base
   dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model. Deeply models the repo's per-field dependency computation
   (mapping.md §3.1; validated == the real computation by G-AX, so it is an
   A-reference rather than a consumed axiom). -/
def relationDeps (f : RelField) : List Dep :=
  match f.through with
  | none           => [baseDep f]
  | some (ta, to_) => [baseDep f, mkDep ta to_]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the field configuration is always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- The ordering dependencies attached to the schema-change operation that
   alters one model field into its new form.

   Desired behavior: when the new form of the field references another model,
   the operation must record the dependencies that reference induces — a
   dependency on the model the field now points to, plus, when the relation is
   routed through an intermediary model, a dependency on that intermediary —
   so the change is sequenced after the models it now refers to. When the new
   form references no model, the operation carries no such dependency.

   `isReferential` says whether the new field references another model; `f` is
   its referential configuration (consulted only when `isReferential`). Both are
   read-only inputs (not `mut`): the routine reads the configuration and never
   alters it (directive 5). -/
method alteredFieldDependencies (isReferential : Bool) (f : RelField)
    return (out : List Dep)
  ensures out = (if isReferential then relationDeps f else [])
  do
    -- impl-start
    -- Start with no dependencies; when the new field references another model,
    -- add the dependencies that reference induces (the base dependency on the
    -- referenced model and, if routed through an intermediary, one on it).
    let mut deps : List Dep := []
    if isReferential then
      deps := relationDeps f
    return deps
    -- impl-end

prove_correct alteredFieldDependencies by
  loom_solve
