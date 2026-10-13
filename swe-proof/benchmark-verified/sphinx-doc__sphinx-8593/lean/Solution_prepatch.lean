import Mathlib
-- imports-end

/-!
Collecting the documentable entries of a module.

A documentation tool gathers the entries of a target module so they can later be
rendered. Each entry records four things about a member:

* its name,
* its value (or a sentinel marking an annotation-only member that has a declared
  type but no bound value),
* the documentation text recorded for that name in the module's source, and
* whether the entry is suppressed (not to be rendered).

The entries are collected in a stable order: first one entry for every name
visible on the module, in that order; then, for every name that has only a
declared annotation and was not already collected, an additional entry carrying
the annotation-only sentinel. Every collected entry carries the documentation
text recorded for its name (the empty string when none is recorded).

The collection then resolves into a result according to the requested mode:

* "all members, with no explicit export list": return every collected entry,
  paired with the flag that says all members were taken;
* "all members, with an explicit export list": return every collected entry, but
  mark as suppressed each entry whose name is not in the export list;
* "an explicit list of requested names": return, in request order, the collected
  entry for each requested name that exists (silently dropping names with no
  collected entry).

In every mode the entries that ARE returned keep their recorded documentation
text, value and name unchanged; only the suppression flag and the membership of
the result list depend on the mode.
-/

-- axioms-start
-- The two per-name observations the collection reads — a member's value
-- (looked up on the module with a default, so the lookup is total) and the
-- documentation text recorded for the name in the module source — are UNCHANGED
-- operations. They are taken here as input functions (`val`, `doc`) rather than
-- re-derived, so the proof consumes no property of either and no
-- `opaque`/`axiom … _prop` is declared.
-- axioms-end

-- pure-start
/-- A collected module entry: its name, its value (`none` is the annotation-only
sentinel), the documentation text recorded for the name, and whether the entry
is suppressed. -/
structure Member where
  name : String
  value : Option String
  doc : String
  skipped : Bool
deriving DecidableEq, Repr, Inhabited

/-- The entry table built by the collection: one entry per visible name carrying
its value and recorded documentation, followed by one entry per annotation-only
name not already present, carrying the annotation-only sentinel and its recorded
documentation. Every entry carries the documentation text recorded for its
name. -/
def baseTable (dirNames annotNames : List String) (val doc : String → String) :
    List Member :=
  dirNames.map (fun n => ⟨n, some (val n), doc n, false⟩)
  ++ (annotNames.filter (fun n => n ∉ dirNames)).map
        (fun n => ⟨n, none, doc n, false⟩)

/-- The full collection result for the given mode. -/
def expectedResult (wantAll : Bool) (allNames : Option (List String))
    (memberlist dirNames annotNames : List String) (val doc : String → String) :
    Bool × List Member :=
  let table := baseTable dirNames annotNames val doc
  if wantAll then
    match allNames with
    | some names =>
      if names ≠ [] then
        (false, table.map (fun m => if m.name ∈ names then m else { m with skipped := true }))
      else
        (true, table)
    | none => (true, table)
  else
    (false, memberlist.filterMap (fun n => table.find? (fun m => m.name == n)))
-- pure-end

-- post-conditions-start
/-- The result is exactly the entry table resolved for the requested mode: the
boolean flag and, for every returned entry, its name, value, recorded
documentation text and suppression flag are pinned. Nothing is left free. -/
def problem_spec_collectModuleEntries (wantAll : Bool)
    (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
    (val doc : String → String) (result : Bool × List Member) : Prop :=
  result = expectedResult wantAll allNames memberlist dirNames annotNames val doc
-- post-conditions-end

-- impl-start
def implementation_collectModuleEntries (wantAll : Bool)
    (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
    (val doc : String → String) : Bool × List Member := Id.run do
  -- PRE-PATCH behaviour: entries are built WITHOUT their recorded documentation
  -- text (the documentation comment is never attached), so every entry's `doc`
  -- field is the empty string regardless of what the module source records.
  let mut members : List Member := []
  for name in dirNames do
    members := members ++ [⟨name, some (val name), "", false⟩]
  for name in annotNames do
    if members.find? (fun m => m.name == name) |>.isNone then
      members := members ++ [⟨name, none, "", false⟩]
  -- resolve into the result for the requested mode
  if wantAll then
    match allNames with
    | some names =>
      if names ≠ [] then
        let mut ret : List Member := []
        for m in members do
          if m.name ∈ names then
            ret := ret ++ [m]
          else
            ret := ret ++ [{ m with skipped := true }]
        return (false, ret)
      else
        return (true, members)
    | none => return (true, members)
  else
    let mut ret : List Member := []
    for name in memberlist do
      match members.find? (fun m => m.name == name) with
      | some m => ret := ret ++ [m]
      | none => pure ()
    return (false, ret)
-- impl-end

-- proof-start
theorem correct_collectModuleEntries :
    ∀ (wantAll : Bool) (allNames : Option (List String))
      (memberlist dirNames annotNames : List String) (val doc : String → String),
      dirNames.Nodup → annotNames.Nodup →
      problem_spec_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc
        (implementation_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc) := by
  sorry
-- proof-end
