import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign callee — the relation resolver that turns
   a model reference into an (app, object-name) pair — is modeled DEEPLY by
   `resolveRef` (pure region) and validated `resolveRef == the real resolver` by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1). The modeled behaviour
   itself is a pure data-flow over the field's configuration. -/
-- axioms-end

-- pure-start
/- How a related model is referenced from a field: as an explicit
   self-reference, by an app-qualified name (`"app.Model"`), by a bare app-local
   name (`"Model"`), or by an already-resolved model object that carries its own
   app and object name. -/
inductive RelRef where
  | selfRef
  | qualified (app : String) (name : String)
  | bare (name : String)
  | resolved (app : String) (name : String)
deriving DecidableEq, Inhabited, Repr

/- Resolve a model reference to its `(app, object-name)` pair, in the scope of
   the model that owns the field. A self-reference resolves to the owning model;
   an app-qualified or bare name is normalized with the object name lower-cased;
   an already-resolved object reports its own app and object name. Models the
   repo's relation resolver (mapping.md §3.1; validated == the real resolver by
   G-AX, so it is an A-reference rather than a consumed axiom). -/
def resolveRef (m : RelRef) (appLabel modelName : String) : String × String :=
  match m with
  | .selfRef        => (appLabel, modelName)
  | .qualified a n  => (a, n.toLower)
  | .bare n         => (appLabel, n.toLower)
  | .resolved a n   => (a, n)

/- A single migration dependency: the `(app, object-name)` it points at, an
   optional field name, and whether it must exist before the dependent is
   created. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on a resolved `(app, name)` pair, with no field. -/
def mkDep (p : String × String) : Dep :=
  { app := p.1, name := p.2, fieldName := none, create := true }

/- A relational field's configuration relevant to its migration dependencies:
   the model it points to (`target`), the intermediary model the relation is
   routed through if any (`through`), and a swappable-setting name when the
   target is a swappable model (`swappable`). -/
structure RelField where
  target : RelRef
  through : Option RelRef
  swappable : Option String
deriving Inhabited

/- The base dependency a field induces on the model it points to: the swappable
   setting under a sentinel app when the target is swappable, otherwise the
   resolved target. -/
def baseDep (f : RelField) (appLabel modelName : String) : Dep :=
  match f.swappable with
  | some s => { app := "__setting__", name := s, fieldName := none, create := true }
  | none   => mkDep (resolveRef f.target appLabel modelName)

/- The full set of migration dependencies a relational field induces: always the
   base dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model, resolved (in the field owner's scope) from the intermediary's own
   reference. -/
def relationDeps (f : RelField) (appLabel modelName : String) : List Dep :=
  match f.through with
  | none     => [baseDep f appLabel modelName]
  | some thr => [baseDep f appLabel modelName, mkDep (resolveRef thr appLabel modelName)]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; appLabel/modelName are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Compute the migration dependencies of one relational field, in the scope of
   the model that owns it. The result lists the base dependency on the model the
   field points to and, when the relation is routed through an intermediary
   model, the additional dependency on that intermediary model. -/
method relationDependencies (f : RelField) (appLabel : String) (modelName : String)
    return (out : List Dep)
  ensures out = relationDeps f appLabel modelName
  do
    -- impl-start
    let d : Dep := baseDep f appLabel modelName
    let deps : List Dep := match f.through with
      | none     => [d]
      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
    return deps
    -- impl-end

prove_correct relationDependencies by
  loom_solve
  simp_all [relationDeps]
