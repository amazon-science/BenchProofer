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
  -- build the entry table, each entry carrying its recorded documentation text
  let mut members : List Member := []
  for name in dirNames do
    members := members ++ [⟨name, some (val name), doc name, false⟩]
  for name in annotNames do
    if members.find? (fun m => m.name == name) |>.isNone then
      members := members ++ [⟨name, none, doc name, false⟩]
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
/-- The entry list produced by the first (dir-names) loop: the pure `foldl`
that the monadic `for name in dirNames do members := members ++ [⟨…⟩]` reduces
to, starting from `[]`. -/
def dirResult (dirNames : List String) (val doc : String → String) : List Member :=
  List.foldl (fun acc name => acc ++ [⟨name, some (val name), doc name, false⟩]) [] dirNames

/-- The value of the mutable `members` after BOTH table loops: the annot-names
loop (with its `find?`-isNone guard) folded over `dirResult`. Claimed equal to
`baseTable` by `table_eq`. -/
def membersFinal (dirNames annotNames : List String) (val doc : String → String) :
    List Member :=
  List.foldl
    (fun acc name =>
      if (List.find? (fun m => m.name == name) acc).isNone = true then
        acc ++ [⟨name, none, doc name, false⟩]
      else acc)
    (dirResult dirNames val doc) annotNames

/-- Loop invariant for the annot-names loop: after processing prefix `p` of
`annotNames`, `members` is `dirResult` followed by the annotation-only entries
for exactly the names of `p` that are NOT in `dirNames` (a plain filter — the
`find?`-guard never fires spuriously among annot entries because `annotNames`
is `Nodup`). -/
def AnnotDedupInv (dirNames : List String) (val doc : String → String)
    (p : List String) (members : List Member) : Prop :=
  members = dirResult dirNames val doc
    ++ (p.filter (fun n => n ∉ dirNames)).map (fun n => ⟨n, none, doc n, false⟩)

theorem dir_loop_foldl (dirNames : List String) (val doc : String → String) :
    (forIn (m := Id) dirNames ([] : List Member)
      (fun name r =>
        ForInStep.yield (r ++ [⟨name, some (val name), doc name, false⟩])))
    = dirResult dirNames val doc := by
  simp only [dirResult, List.forIn_yield_eq_foldl]

theorem annot_loop_foldl (dirNames annotNames : List String) (val doc : String → String) :
    (forIn (m := Id) annotNames (dirResult dirNames val doc)
      (fun name r =>
        if (List.find? (fun m => m.name == name) r).isNone = true then
          ForInStep.yield (r ++ [⟨name, none, doc name, false⟩])
        else ForInStep.yield r))
    = membersFinal dirNames annotNames val doc := by
  simp only [membersFinal, ← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl]

theorem mode_loop_foldl {α : Type} (xs : List α) (init : List Member)
    (f : α → List Member → List Member) :
    (forIn (m := Id) xs init (fun a r => ForInStep.yield (f a r)))
    = List.foldl (fun r a => f a r) init xs := by
  induction xs generalizing init with
  | nil => rfl
  | cons a t ih => simp only [List.forIn_cons, List.foldl_cons]; exact ih (f a init)

theorem dir_part_eq (dirNames : List String) (val doc : String → String) :
    dirResult dirNames val doc
    = dirNames.map (fun n => (⟨n, some (val n), doc n, false⟩ : Member)) := by
  unfold dirResult
  suffices h : ∀ (acc : List Member),
      List.foldl (fun acc name => acc ++ [⟨name, some (val name), doc name, false⟩]) acc dirNames
      = acc ++ dirNames.map (fun n => (⟨n, some (val n), doc n, false⟩ : Member)) by
    simpa using h []
  intro acc
  induction dirNames generalizing acc with
  | nil => simp
  | cons x xs ih => simp [List.foldl_cons, ih, List.append_assoc]

theorem annot_guard_char (dirNames p : List String) (val doc : String → String) (n : String)
    (hn : n ∉ p) :
    (List.find? (fun m => m.name == n)
      (dirResult dirNames val doc
        ++ (p.filter (fun x => x ∉ dirNames)).map
              (fun x => (⟨x, none, doc x, false⟩ : Member)))).isNone = true
    ↔ n ∉ dirNames := by
  rw [dir_part_eq]
  simp only [Option.isNone_iff_eq_none, List.find?_eq_none, List.mem_append, List.mem_map,
    List.mem_filter, beq_iff_eq]
  constructor
  · intro h hmem
    exact h ⟨n, some (val n), doc n, false⟩ (Or.inl ⟨n, hmem, rfl⟩) rfl
  · intro h x hx
    rcases hx with ⟨a, ha, rfl⟩ | ⟨a, ⟨ha, _⟩, rfl⟩
    · intro he; exact h (he ▸ ha)
    · intro he; exact hn (he ▸ ha)

theorem annot_part_invariant (dirNames annotNames : List String) (val doc : String → String)
    (ha : annotNames.Nodup) :
    AnnotDedupInv dirNames val doc annotNames (membersFinal dirNames annotNames val doc) := by
  unfold AnnotDedupInv membersFinal
  induction annotNames using List.reverseRecOn with
  | nil => simp
  | append_singleton q x ih =>
    rw [List.nodup_append] at ha
    obtain ⟨hq, _, hdisj⟩ := ha
    have hx : x ∉ q := fun hmem => hdisj x hmem x (List.mem_singleton.mpr rfl) rfl
    have ihq := ih hq
    rw [List.foldl_append, List.foldl_cons, List.foldl_nil, ihq]
    have hguard := annot_guard_char dirNames q val doc x hx
    by_cases hxd : x ∉ dirNames
    · have : (List.find? (fun m => m.name == x)
          (dirResult dirNames val doc ++
            (List.filter (fun n => decide (n ∉ dirNames)) q).map
              (fun n => (⟨n, none, doc n, false⟩ : Member)))).isNone = true :=
        hguard.mpr hxd
      simp only [this, if_pos]
      rw [List.filter_append, List.map_append]
      simp [hxd]
    · have : ¬ (List.find? (fun m => m.name == x)
          (dirResult dirNames val doc ++
            (List.filter (fun n => decide (n ∉ dirNames)) q).map
              (fun n => (⟨n, none, doc n, false⟩ : Member)))).isNone = true :=
        fun h => hxd (hguard.mp h)
      simp only [this, if_neg, Bool.not_eq_true] at *
      rw [List.filter_append, List.map_append]
      simp [hxd]

theorem table_eq (dirNames annotNames : List String) (val doc : String → String)
    (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
    membersFinal dirNames annotNames val doc = baseTable dirNames annotNames val doc := by
  have h := annot_part_invariant dirNames annotNames val doc ha
  unfold AnnotDedupInv at h
  rw [h, dir_part_eq]
  rfl

theorem branch_none_and_empty (dirNames annotNames : List String) (val doc : String → String)
    (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
    ((true, membersFinal dirNames annotNames val doc) : Bool × List Member)
    = (true, baseTable dirNames annotNames val doc) := by
  rw [table_eq dirNames annotNames val doc hd ha]

theorem branch_suppress (dirNames annotNames : List String) (val doc : String → String)
    (hd : dirNames.Nodup) (ha : annotNames.Nodup) (names : List String) :
    (forIn (m := Id) (membersFinal dirNames annotNames val doc) ([] : List Member)
      (fun m r =>
        if m.name ∈ names then ForInStep.yield (r ++ [m])
        else ForInStep.yield (r ++ [{ m with skipped := true }])))
    = (baseTable dirNames annotNames val doc).map
        (fun m => if m.name ∈ names then m else { m with skipped := true }) := by
  rw [table_eq dirNames annotNames val doc hd ha]
  have key : ∀ (l acc : List Member),
      (forIn (m := Id) l acc
        (fun m r =>
          if m.name ∈ names then ForInStep.yield (r ++ [m])
          else ForInStep.yield (r ++ [{ m with skipped := true }])))
      = acc ++ l.map (fun m => if m.name ∈ names then m else { m with skipped := true }) := by
    intro l
    induction l with
    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil, pure]
    | cons a as ih =>
        intro acc
        simp only [List.forIn_cons, List.map_cons]
        split_ifs with h <;> (simp only [bind]; rw [ih]; simp)
  have := key (baseTable dirNames annotNames val doc) []
  simpa using this

theorem branch_filtermap (dirNames annotNames memberlist : List String)
    (val doc : String → String) (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
    (forIn (m := Id) memberlist ([] : List Member)
      (fun name r =>
        match List.find? (fun m => m.name == name) (membersFinal dirNames annotNames val doc) with
        | some m => ForInStep.yield (r ++ [m])
        | none => ForInStep.yield r))
    = memberlist.filterMap
        (fun n => (baseTable dirNames annotNames val doc).find? (fun m => m.name == n)) := by
  rw [table_eq dirNames annotNames val doc hd ha]
  set T := baseTable dirNames annotNames val doc with hT
  have key : ∀ (xs : List String) (acc : List Member),
      (forIn (m := Id) xs acc
        (fun name r =>
          match List.find? (fun m => m.name == name) T with
          | some m => ForInStep.yield (r ++ [m])
          | none => ForInStep.yield r))
      = acc ++ xs.filterMap (fun n => T.find? (fun m => m.name == n)) := by
    intro xs
    induction xs with
    | nil => intro acc; simp; rfl
    | cons a rest ih =>
      intro acc
      simp only [List.forIn_cons, List.filterMap_cons]
      cases h : List.find? (fun m => m.name == a) T with
      | none => show forIn (m := Id) rest acc _ = _; rw [ih]
      | some m =>
        show forIn (m := Id) rest (acc ++ [m]) _ = _
        rw [ih]; simp
  have := key memberlist []
  simpa using this

theorem correct_collectModuleEntries :
    ∀ (wantAll : Bool) (allNames : Option (List String))
      (memberlist dirNames annotNames : List String) (val doc : String → String),
      dirNames.Nodup → annotNames.Nodup →
      problem_spec_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc
        (implementation_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc) := by
  intro wantAll allNames memberlist dirNames annotNames val doc hd ha
  unfold problem_spec_collectModuleEntries implementation_collectModuleEntries expectedResult
  simp only [Id.run, bind, pure]
  rw [show (forIn (m := Id) dirNames ([] : List Member)
        (fun name r => ForInStep.yield (r ++ [⟨name, some (val name), doc name, false⟩])))
      = dirResult dirNames val doc from dir_loop_foldl dirNames val doc]
  rw [show (forIn (m := Id) annotNames (dirResult dirNames val doc)
        (fun name r =>
          if (List.find? (fun m => m.name == name) r).isNone = true then
            ForInStep.yield (r ++ [⟨name, none, doc name, false⟩])
          else ForInStep.yield r))
      = membersFinal dirNames annotNames val doc from annot_loop_foldl dirNames annotNames val doc]
  split
  · -- wantAll = true
    split
    · -- allNames = some names
      split
      · -- names ≠ []
        rw [branch_suppress dirNames annotNames val doc hd ha]
      · -- names = []
        exact branch_none_and_empty dirNames annotNames val doc hd ha
    · -- allNames = none
      exact branch_none_and_empty dirNames annotNames val doc hd ha
  · -- wantAll = false
    rw [branch_filtermap dirNames annotNames memberlist val doc hd ha]

-- proof-end
