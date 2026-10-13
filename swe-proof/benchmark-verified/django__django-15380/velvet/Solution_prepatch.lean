import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign computation — resolving a model entry out
   of a name-keyed state map, and resolving a model's prior name through the
   rename record — is modeled DEEPLY by `lookupState` / `renameLookup` (pure
   region). The state maps and the rename record are association lists; the
   lookups are the per-key accesses the routine performs. Those deep models are
   validated against the real Django state maps and rename record by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1), not consumed as an
   axiom. -/
-- axioms-end

-- pure-start
/- A model entry, identified by its object name. Only its identity is observed
   (the routine selects WHICH entry to read), so the carrier records the name. -/
structure ModelEntry where
  name : String
deriving DecidableEq, Inhabited, Repr

/- Two keys (app label, model name) are equal componentwise. -/
def keyEq (a b : String × String) : Bool := a.1 == b.1 && a.2 == b.2

/- Resolve a model entry out of a name-keyed state map: the entry stored under
   the given (app label, model name), or none when no such key is present
   (the empty result that, in the repository, manifests as a missing key). -/
def lookupState (m : List ((String × String) × ModelEntry))
    (key : String × String) : Option ModelEntry :=
  (m.find? (fun kv => keyEq kv.1 key)).map Prod.snd

/- Resolve a model's name in the prior state from the rename record: when the
   model was renamed, the record maps its current key to its prior name; when it
   was not, its prior name equals its current name. -/
def renameLookup (renamed : List ((String × String) × String))
    (key : String × String) : String :=
  match renamed.find? (fun kv => keyEq kv.1 key) with
  | some kv => kv.2
  | none    => key.2
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the maps and names are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the prior-state and current-state model entries a field operation
   acts on, for a model whose current name is `curModelName` in app `app`.

   Desired behavior: the model's PRIOR name is its rename source recorded in
   `renamed` (or its current name when it was not renamed). The PRIOR-state entry
   is the one stored in the prior-state map under that prior name. The
   CURRENT-state entry is the one stored in the current-state map under the
   model's CURRENT name — the current-state map is keyed by current names, so a
   model whose name changed is found there under its new name, independently of
   its prior name.

   `priorModels` / `currentModels` are the prior- and current-state model maps;
   `renamed` is the rename record; all three and both names are read-only inputs
   (not `mut`): the routine only reads them (directive 5). -/
method frameRenamedField
    (priorModels : List ((String × String) × ModelEntry))
    (currentModels : List ((String × String) × ModelEntry))
    (renamed : List ((String × String) × String))
    (app : String)
    (curModelName : String)
    return (out : Option ModelEntry × Option ModelEntry)
  ensures out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))
  ensures out.2 = lookupState currentModels (app, curModelName)
  do
    -- impl-start
    -- Pre-image skeleton: both state entries are resolved under the model's
    -- prior name. The frozen spec resolves the current-state entry under the
    -- model's CURRENT name, so when the prior and current names differ this
    -- selects the wrong key and prove_correct MUST fail.
    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, priorName)
    return (oldState, newState)
    -- impl-end

prove_correct frameRenamedField by
  loom_solve
