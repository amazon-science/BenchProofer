# P2 adversarial audit — sphinx-doc__sphinx-8593

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,14 +96,12 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
-    members := members ++ [⟨name, some (val name), doc name, false⟩]
+    members := members ++ [⟨name, some (val name), "", false⟩]
   for name in annotNames do
     if members.find? (fun m => m.name == name) |>.isNone then
-      members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
+      members := members ++ [⟨name, none, "", false⟩]
   if wantAll then
     match allNames with
     | some names =>
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,14 +96,11 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
     members := members ++ [⟨name, some (val name), doc name, false⟩]
   for name in annotNames do
-    if members.find? (fun m => m.name == name) |>.isNone then
-      members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
+    members := members ++ [⟨name, none, doc name, false⟩]
   if wantAll then
     match allNames with
     | some names =>
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,18 +96,15 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
     members := members ++ [⟨name, some (val name), doc name, false⟩]
   for name in annotNames do
     if members.find? (fun m => m.name == name) |>.isNone then
       members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
   if wantAll then
     match allNames with
     | some names =>
-      if names ≠ [] then
         let mut ret : List Member := []
         for m in members do
           if m.name ∈ names then
@@ -115,8 +112,6 @@
           else
             ret := ret ++ [{ m with skipped := true }]
         return (false, ret)
-      else
-        return (true, members)
     | none => return (true, members)
   else
     let mut ret : List Member := []
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,14 +96,12 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
     members := members ++ [⟨name, some (val name), doc name, false⟩]
   for name in annotNames do
     if members.find? (fun m => m.name == name) |>.isNone then
       members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
   if wantAll then
     match allNames with
     | some names =>
@@ -122,7 +120,7 @@
     let mut ret : List Member := []
     for name in memberlist do
       match members.find? (fun m => m.name == name) with
-      | some m => ret := ret ++ [m]
+      | some m => ret := [m] ++ ret
       | none => pure ()
     return (false, ret)
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,225 +95,12 @@
 -- impl-start
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
-    (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
-  let mut members : List Member := []
-  for name in dirNames do
-    members := members ++ [⟨name, some (val name), doc name, false⟩]
-  for name in annotNames do
-    if members.find? (fun m => m.name == name) |>.isNone then
-      members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
-  if wantAll then
-    match allNames with
-    | some names =>
-      if names ≠ [] then
-        let mut ret : List Member := []
-        for m in members do
-          if m.name ∈ names then
-            ret := ret ++ [m]
-          else
-            ret := ret ++ [{ m with skipped := true }]
-        return (false, ret)
-      else
-        return (true, members)
-    | none => return (true, members)
-  else
-    let mut ret : List Member := []
-    for name in memberlist do
-      match members.find? (fun m => m.name == name) with
-      | some m => ret := ret ++ [m]
-      | none => pure ()
-    return (false, ret)
+    (val doc : String → String) : Bool × List Member :=
+  expectedResult wantAll allNames memberlist dirNames annotNames val doc
 -- impl-end
 
 
 -- proof-start
-/-- The entry list produced by the first (dir-names) loop: the pure `foldl`
-that the monadic `for name in dirNames do members := members ++ [⟨…⟩]` reduces
-to, starting from `[]`. -/
-def dirResult (dirNames : List String) (val doc : String → String) : List Member :=
-  List.foldl (fun acc name => acc ++ [⟨name, some (val name), doc name, false⟩]) [] dirNames
-
-/-- The value of the mutable `members` after BOTH table loops: the annot-names
-loop (with its `find?`-isNone guard) folded over `dirResult`. Claimed equal to
-`baseTable` by `table_eq`. -/
-def membersFinal (dirNames annotNames : List String) (val doc : String → String) :
-    List Member :=
-  List.foldl
-    (fun acc name =>
-      if (List.find? (fun m => m.name == name) acc).isNone = true then
-        acc ++ [⟨name, none, doc name, false⟩]
-      else acc)
-    (dirResult dirNames val doc) annotNames
-
-/-- Loop invariant for the annot-names loop: after processing prefix `p` of
-`annotNames`, `members` is `dirResult` followed by the annotation-only entries
-for exactly the names of `p` that are NOT in `dirNames` (a plain filter — the
-`find?`-guard never fires spuriously among annot entries because `annotNames`
-is `Nodup`). -/
-def AnnotDedupInv (dirNames : List String) (val doc : String → String)
-    (p : List String) (members : List Member) : Prop :=
-  members = dirResult dirNames val doc
-    ++ (p.filter (fun n => n ∉ dirNames)).map (fun n => ⟨n, none, doc n, false⟩)
-
-theorem dir_loop_foldl (dirNames : List String) (val doc : String → String) :
-    (forIn (m := Id) dirNames ([] : List Member)
-      (fun name r =>
-        ForInStep.yield (r ++ [⟨name, some (val name), doc name, false⟩])))
-    = dirResult dirNames val doc := by
-  simp only [dirResult, List.forIn_yield_eq_foldl]
-
-theorem annot_loop_foldl (dirNames annotNames : List String) (val doc : String → String) :
-    (forIn (m := Id) annotNames (dirResult dirNames val doc)
-      (fun name r =>
-        if (List.find? (fun m => m.name == name) r).isNone = true then
-          ForInStep.yield (r ++ [⟨name, none, doc name, false⟩])
-        else ForInStep.yield r))
-    = membersFinal dirNames annotNames val doc := by
-  simp only [membersFinal, ← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl]
-
-theorem mode_loop_foldl {α : Type} (xs : List α) (init : List Member)
-    (f : α → List Member → List Member) :
-    (forIn (m := Id) xs init (fun a r => ForInStep.yield (f a r)))
-    = List.foldl (fun r a => f a r) init xs := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a t ih => simp only [List.forIn_cons, List.foldl_cons]; exact ih (f a init)
-
-theorem dir_part_eq (dirNames : List String) (val doc : String → String) :
-    dirResult dirNames val doc
-    = dirNames.map (fun n => (⟨n, some (val n), doc n, false⟩ : Member)) := by
-  unfold dirResult
-  suffices h : ∀ (acc : List Member),
-      List.foldl (fun acc name => acc ++ [⟨name, some (val name), doc name, false⟩]) acc dirNames
-      = acc ++ dirNames.map (fun n => (⟨n, some (val n), doc n, false⟩ : Member)) by
-    simpa using h []
-  intro acc
-  induction dirNames generalizing acc with
-  | nil => simp
-  | cons x xs ih => simp [List.foldl_cons, ih, List.append_assoc]
-
-theorem annot_guard_char (dirNames p : List String) (val doc : String → String) (n : String)
-    (hn : n ∉ p) :
-    (List.find? (fun m => m.name == n)
-      (dirResult dirNames val doc
-        ++ (p.filter (fun x => x ∉ dirNames)).map
-              (fun x => (⟨x, none, doc x, false⟩ : Member)))).isNone = true
-    ↔ n ∉ dirNames := by
-  rw [dir_part_eq]
-  simp only [Option.isNone_iff_eq_none, List.find?_eq_none, List.mem_append, List.mem_map,
-    List.mem_filter, beq_iff_eq]
-  constructor
-  · intro h hmem
-    exact h ⟨n, some (val n), doc n, false⟩ (Or.inl ⟨n, hmem, rfl⟩) rfl
-  · intro h x hx
-    rcases hx with ⟨a, ha, rfl⟩ | ⟨a, ⟨ha, _⟩, rfl⟩
-    · intro he; exact h (he ▸ ha)
-    · intro he; exact hn (he ▸ ha)
-
-theorem annot_part_invariant (dirNames annotNames : List String) (val doc : String → String)
-    (ha : annotNames.Nodup) :
-    AnnotDedupInv dirNames val doc annotNames (membersFinal dirNames annotNames val doc) := by
-  unfold AnnotDedupInv membersFinal
-  induction annotNames using List.reverseRecOn with
-  | nil => simp
-  | append_singleton q x ih =>
-    rw [List.nodup_append] at ha
-    obtain ⟨hq, _, hdisj⟩ := ha
-    have hx : x ∉ q := fun hmem => hdisj x hmem x (List.mem_singleton.mpr rfl) rfl
-    have ihq := ih hq
-    rw [List.foldl_append, List.foldl_cons, List.foldl_nil, ihq]
-    have hguard := annot_guard_char dirNames q val doc x hx
-    by_cases hxd : x ∉ dirNames
-    · have : (List.find? (fun m => m.name == x)
-          (dirResult dirNames val doc ++
-            (List.filter (fun n => decide (n ∉ dirNames)) q).map
-              (fun n => (⟨n, none, doc n, false⟩ : Member)))).isNone = true :=
-        hguard.mpr hxd
-      simp only [this, if_pos]
-      rw [List.filter_append, List.map_append]
-      simp [hxd]
-    · have : ¬ (List.find? (fun m => m.name == x)
-          (dirResult dirNames val doc ++
-            (List.filter (fun n => decide (n ∉ dirNames)) q).map
-              (fun n => (⟨n, none, doc n, false⟩ : Member)))).isNone = true :=
-        fun h => hxd (hguard.mp h)
-      simp only [this, if_neg, Bool.not_eq_true] at *
-      rw [List.filter_append, List.map_append]
-      simp [hxd]
-
-theorem table_eq (dirNames annotNames : List String) (val doc : String → String)
-    (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
-    membersFinal dirNames annotNames val doc = baseTable dirNames annotNames val doc := by
-  have h := annot_part_invariant dirNames annotNames val doc ha
-  unfold AnnotDedupInv at h
-  rw [h, dir_part_eq]
-  rfl
-
-theorem branch_none_and_empty (dirNames annotNames : List String) (val doc : String → String)
-    (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
-    ((true, membersFinal dirNames annotNames val doc) : Bool × List Member)
-    = (true, baseTable dirNames annotNames val doc) := by
-  rw [table_eq dirNames annotNames val doc hd ha]
-
-theorem branch_suppress (dirNames annotNames : List String) (val doc : String → String)
-    (hd : dirNames.Nodup) (ha : annotNames.Nodup) (names : List String) :
-    (forIn (m := Id) (membersFinal dirNames annotNames val doc) ([] : List Member)
-      (fun m r =>
-        if m.name ∈ names then ForInStep.yield (r ++ [m])
-        else ForInStep.yield (r ++ [{ m with skipped := true }])))
-    = (baseTable dirNames annotNames val doc).map
-        (fun m => if m.name ∈ names then m else { m with skipped := true }) := by
-  rw [table_eq dirNames annotNames val doc hd ha]
-  have key : ∀ (l acc : List Member),
-      (forIn (m := Id) l acc
-        (fun m r =>
-          if m.name ∈ names then ForInStep.yield (r ++ [m])
-          else ForInStep.yield (r ++ [{ m with skipped := true }])))
-      = acc ++ l.map (fun m => if m.name ∈ names then m else { m with skipped := true }) := by
-    intro l
-    induction l with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil, pure]
-    | cons a as ih =>
-        intro acc
-        simp only [List.forIn_cons, List.map_cons]
-        split_ifs with h <;> (simp only [bind]; rw [ih]; simp)
-  have := key (baseTable dirNames annotNames val doc) []
-  simpa using this
-
-theorem branch_filtermap (dirNames annotNames memberlist : List String)
-    (val doc : String → String) (hd : dirNames.Nodup) (ha : annotNames.Nodup) :
-    (forIn (m := Id) memberlist ([] : List Member)
-      (fun name r =>
-        match List.find? (fun m => m.name == name) (membersFinal dirNames annotNames val doc) with
-        | some m => ForInStep.yield (r ++ [m])
-        | none => ForInStep.yield r))
-    = memberlist.filterMap
-        (fun n => (baseTable dirNames annotNames val doc).find? (fun m => m.name == n)) := by
-  rw [table_eq dirNames annotNames val doc hd ha]
-  set T := baseTable dirNames annotNames val doc with hT
-  have key : ∀ (xs : List String) (acc : List Member),
-      (forIn (m := Id) xs acc
-        (fun name r =>
-          match List.find? (fun m => m.name == name) T with
-          | some m => ForInStep.yield (r ++ [m])
-          | none => ForInStep.yield r))
-      = acc ++ xs.filterMap (fun n => T.find? (fun m => m.name == n)) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp; rfl
-    | cons a rest ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      cases h : List.find? (fun m => m.name == a) T with
-      | none => show forIn (m := Id) rest acc _ = _; rw [ih]
-      | some m =>
-        show forIn (m := Id) rest (acc ++ [m]) _ = _
-        rw [ih]; simp
-  have := key memberlist []
-  simpa using this
-
 theorem correct_collectModuleEntries :
     ∀ (wantAll : Bool) (allNames : Option (List String))
       (memberlist dirNames annotNames : List String) (val doc : String → String),
@@ -321,29 +108,6 @@
       problem_spec_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc
         (implementation_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc) := by
   intro wantAll allNames memberlist dirNames annotNames val doc hd ha
-  unfold problem_spec_collectModuleEntries implementation_collectModuleEntries expectedResult
-  simp only [Id.run, bind, pure]
-  rw [show (forIn (m := Id) dirNames ([] : List Member)
-        (fun name r => ForInStep.yield (r ++ [⟨name, some (val name), doc name, false⟩])))
-      = dirResult dirNames val doc from dir_loop_foldl dirNames val doc]
-  rw [show (forIn (m := Id) annotNames (dirResult dirNames val doc)
-        (fun name r =>
-          if (List.find? (fun m => m.name == name) r).isNone = true then
-            ForInStep.yield (r ++ [⟨name, none, doc name, false⟩])
-          else ForInStep.yield r))
-      = membersFinal dirNames annotNames val doc from annot_loop_foldl dirNames annotNames val doc]
-  split
-  · -- wantAll = true
-    split
-    · -- allNames = some names
-      split
-      · -- names ≠ []
-        rw [branch_suppress dirNames annotNames val doc hd ha]
-      · -- names = []
-        exact branch_none_and_empty dirNames annotNames val doc hd ha
-    · -- allNames = none
-      exact branch_none_and_empty dirNames annotNames val doc hd ha
-  · -- wantAll = false
-    rw [branch_filtermap dirNames annotNames memberlist val doc hd ha]
-
+  unfold problem_spec_collectModuleEntries implementation_collectModuleEntries
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,14 +96,12 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
     members := members ++ [⟨name, some (val name), doc name, false⟩]
   for name in annotNames do
     if members.find? (fun m => m.name == name) |>.isNone then
       members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
   if wantAll then
     match allNames with
     | some names =>
@@ -111,9 +109,9 @@
         let mut ret : List Member := []
         for m in members do
           if m.name ∈ names then
+            ret := ret ++ [{ m with skipped := true }]
+          else
             ret := ret ++ [m]
-          else
-            ret := ret ++ [{ m with skipped := true }]
         return (false, ret)
       else
         return (true, members)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,14 +96,12 @@
 def implementation_collectModuleEntries (wantAll : Bool)
     (allNames : Option (List String)) (memberlist dirNames annotNames : List String)
     (val doc : String → String) : Bool × List Member := Id.run do
-  -- build the entry table, each entry carrying its recorded documentation text
   let mut members : List Member := []
   for name in dirNames do
     members := members ++ [⟨name, some (val name), doc name, false⟩]
   for name in annotNames do
     if members.find? (fun m => m.name == name) |>.isNone then
-      members := members ++ [⟨name, none, doc name, false⟩]
-  -- resolve into the result for the requested mode
+      members := members ++ [⟨name, some (val name), doc name, false⟩]
   if wantAll then
     match allNames with
     | some names =>
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: TIGHT FUNCTIONAL EQUATION. problem_spec_collectModuleEntries pins result = expectedResult wantAll allNames memberlist dirNames annotNames val doc for ALL inputs with dirNames.Nodup & annotNames.Nodup. In Lean's total-function setting there is no partial-correctness/divergence escape hatch, so any verifying same-spec impl must genuinely equal expectedResult on the real (Nodup) domain. same_spec elides BOTH impl and proof regions in the Lean spec view, so I was free to rewrite both while keeping the signature True (confirmed same_spec=True for all 7 attacks).

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]; the axioms region declares no opaque/axiom. There are NO A-consumed / A-reference legs. refinement.md legs are all R (the doc-comment attachment on every entry = the fix; ops 1,2 and the '—' row) or I (ops 3,4,5 = the three unchanged resolution modes: no-__all__, __all__ skip-marking, explicit-name request). No kind-3 ungrounded-axiom leg. Each R/I leg corresponds faithfully to the gold-patch Python get_module_members / get_object_members (verified against the byte-identical gold diff). R/I legs are G-CONF territory per plan §4; the A-legs this pass targets are vacuous here.

### ATTACKS (7 distinct same-spec wrong impls + echo; all same_spec=True):
- atk_1 partial/degraded (PREPATCH BUG reproduced): entries built with doc="" -> FAILS verify (exit 1, rewrite pattern not found). Matches Solution_prepatch.lean semantics.
- atk_2 boundary: annotation loop drops the find?-isNone dedup guard (appends all annotNames) -> FAILS verify (exit 1).
- atk_3 control-flow: routes empty allNames through the suppress branch (drops names != [] guard) -> FAILS verify (exit 1).
- atk_4 control-flow-effect: explicit-name branch prepends (reverses request order) -> FAILS verify (exit 1).
- atk_6 boundary/inversion: __all__ branch marks IN-list entries skipped -> FAILS verify (exit 1).
- atk_7 sentinel error: annotation-only entries use some (val name) instead of the none sentinel -> FAILS verify (exit 1).
- atk_5 ungrounded-oracle ECHO: impl := expectedResult ... ; proof intro; unfold; rfl -> VERIFIES (exit 0), #print axioms correct_collectModuleEntries = [propext] (clean, no sorry).

RESOLVE (mandatory for every verifying clean-axiom impl): atk_5 is the ONLY verifying attack. Its faithful refined patch is behaviorally the gold behavior; I materialized it and confirmed it is BYTE-IDENTICAL to the dataset gold patch (len 4830 == 4830). run_resolve('sphinx-doc__sphinx-8593', patch, timeout=900, retries=1) => resolved=True completed=True note=resolved. A RESOLVING echo is not a weakness (G-EQ/G-PANEL-1 policy: same-spec verifying attack fails only if its refined patch does NOT resolve).

### Commands
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); same_spec(gold, atk_N, b.language)" => True for atk_1..7.
- verify: bash scripts/lean_verify.sh <atk>.lean. pos_control=0; atk_1=1 atk_2=1 atk_3=1 atk_4=1 atk_6=1 atk_7=1; atk_5=0.
- axioms: appended '#print axioms correct_collectModuleEntries'; pos=[propext, Quot.sound]; atk_5=[propext]; both clean, no sorry.
- resolve: bash run_resolve_atk5.sh -> ATK5 resolved=True completed=True note=resolved.

CONCLUSION: The 6 behaviorally-divergent same-spec impls all FAIL to verify (the tight equation spec is genuinely tight), and the single verifying same-spec impl (echo) has a materialized faithful patch that RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds on the exhibited attack surface. Prepatch bug (doc="") reproduced as atk_1 and is unclosable. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: TIGHT FUNCTIONAL EQUATION. problem_spec_collectModuleEntries pins result = expectedResult wantAll allNames memberlist dirNames annotNames val doc for ALL inputs with dirNames.Nodup & annotNames.Nodup. In Lean's total-function setting there is no partial-correctness/divergence escape hatch, so any verifying same-spec impl must genuinely equal expectedResult on the real (Nodup) domain. same_spec elides BOTH impl and proof regions in the Lean spec view, so I was free to rewrite both while keeping the signature True (confirmed same_spec=True for all 7 attacks).

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]; the axioms region declares no opaque/axiom. There are NO A-consumed / A-reference legs. refinement.md legs are all R (the doc-comment attachment on every entry = the fix; ops 1,2 and the '—' row) or I (ops 3,4,5 = the three unchanged resolution modes: no-__all__, __all__ skip-marking, explicit-name request). No kind-3 ungrounded-axiom leg. Each R/I leg corresponds faithfully to the gold-patch Python get_module_members / get_object_members (verified against the byte-identical gold diff). R/I legs are G-CONF territory per plan §4; the A-legs this pass targets are vacuous here.

### ATTACKS (7 distinct same-spec wrong impls + echo; all same_spec=True):
- atk_1 partial/degraded (PREPATCH BUG reproduced): entries built with doc="" -> FAILS verify (exit 1, rewrite pattern not found). Matches Solution_prepatch.lean semantics.
- atk_2 boundary: annotation loop drops the find?-isNone dedup guard (appends all annotNames) -> FAILS verify (exit 1).
- atk_3 control-flow: routes empty allNames through the suppress branch (drops names != [] guard) -> FAILS verify (exit 1).
- atk_4 control-flow-effect: explicit-name branch prepends (reverses request order) -> FAILS verify (exit 1).
- atk_6 boundary/inversion: __all__ branch marks IN-list entries skipped -> FAILS verify (exit 1).
- atk_7 sentinel error: annotation-only entries use some (val name) instead of the none sentinel -> FAILS verify (exit 1).
- atk_5 ungrounded-oracle ECHO: impl := expectedResult ... ; proof intro; unfold; rfl -> VERIFIES (exit 0), #print axioms correct_collectModuleEntries = [propext] (clean, no sorry).

RESOLVE (mandatory for every verifying clean-axiom impl): atk_5 is the ONLY verifying attack. Its faithful refined patch is behaviorally the gold behavior; I materialized it and confirmed it is BYTE-IDENTICAL to the dataset gold patch (len 4830 == 4830). run_resolve('sphinx-doc__sphinx-8593', patch, timeout=900, retries=1) => resolved=True completed=True note=resolved. A RESOLVING echo is not a weakness (G-EQ/G-PANEL-1 policy: same-spec verifying attack fails only if its refined patch does NOT resolve).

### Commands
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); same_spec(gold, atk_N, b.language)" => True for atk_1..7.
- verify: bash scripts/lean_verify.sh <atk>.lean. pos_control=0; atk_1=1 atk_2=1 atk_3=1 atk_4=1 atk_6=1 atk_7=1; atk_5=0.
- axioms: appended '#print axioms correct_collectModuleEntries'; pos=[propext, Quot.sound]; atk_5=[propext]; both clean, no sorry.
- resolve: bash run_resolve_atk5.sh -> ATK5 resolved=True completed=True note=resolved.

CONCLUSION: The 6 behaviorally-divergent same-spec impls all FAIL to verify (the tight equation spec is genuinely tight), and the single verifying same-spec impl (echo) has a materialized faithful patch that RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds on the exhibited attack surface. Prepatch bug (doc="") reproduced as atk_1 and is unclosable. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sphinx-doc__sphinx-8593 lean bundle. No diverging input found; the modeled expectedResult agrees with the real post-patch callee on its entire real input domain.

### Evidence
1. Lean is real: Solution.lean compiles clean via lean_verify.sh (exit 0, no sorry). `#print axioms correct_collectModuleEntries` = [propext, Quot.sound] only — no sorryAx, no bundle-declared axioms. Proof is genuine.
2. same_spec holds: pure-start, post-conditions-start, and axioms-start regions are BYTE-IDENTICAL between Solution.lean and Solution_prepatch.lean. The prepatch (builds every entry with doc="") legitimately cannot close the theorem when a collected name has a non-empty comment — the correct G-DIFF signal.
3. Model vs. real code (verified against gold_8593.diff, the gold patch to sphinx/ext/autodoc/__init__.py get_module_members/get_object_members):
   - dir loop -> entry ⟨n, some (val n), doc n, false⟩ mirrors `value=safe_getattr(self.object,name,None); docstring=attr_docs.get(('',name),[]); members[name]=ObjectMember(name,value,docstring="\n".join(docstring))`.
   - annot loop with the `members.find? isNone` guard mirrors `for name in inspect.getannotations: if name not in members: ObjectMember(name, INSTANCEATTR, ...)`; baseTable's `filter (n ∉ dirNames)` is equivalent under the Nodup preconditions.
   - want_all + not self.__all__ (None or empty) -> (true, table): matches `some []`/`none` branches.
   - want_all + __all__ present -> mark skipped for names not in list: matches `member.skipped=True`; comments/value preserved.
   - explicit-name path -> memberlist.filterMap find?: matches dict-membership append in request order, silently dropping absent names.
   - safe_getattr(...,None) is total (default => the `except AttributeError: continue` is dead for the module path; confirmed by reading safe_getattr), and attr_docs.get is total; both are correctly abstracted as FREE input functions val/doc, so the spec pins nothing about them the real code doesn't. No over-strengthening.
   - Nodup preconditions match the real domain (dir() names distinct, dict keys distinct) — domain scoping, not spec strengthening.
   - result fully pinned to expectedResult (frame discipline; nothing left free).
4. Conformance: conformance_check.py (SEED 8593) diffs the impl shadow against a faithful post-patch replica over 6 edge cases + 120000 fuzzed inputs -> checked=120006 disagreements=0 status=pass.

Conclusion: the spec is neither too strong nor drifted; the modeled function equals the real callee on every input in the modeled domain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean with impl/proof elided (imports + docstring + pure region [Member, baseTable, expectedResult] + post-conditions). Verified: same_spec(Solution.lean, Solution_prepatch.lean) = True for spec_view (spec region byte-identical); no RELAXED_LEAKAGE.md; mechanical G-LEAK screen passes clean (rep.passed=True, no hard_failures).

Checked every leak channel against the PUBLIC problem_statement ('autodoc :meta public: does not effect to variables'; _foo documented :meta public: should be shown):
- L1 diff markers / reproduced gold lines: none.
- L2 patched file path / module path: none.
- Patched repo symbols get_module_members, add_directive_header: neither appears in any spec-view identifier or comment. Lean identifiers (Member, baseTable, expectedResult, collectModuleEntries, dirNames, annotNames, val, doc) are abstract and do not echo repo symbols.
- L3 bug/fix narration (bug/fix/patch/prepatch/regression/etc.): none. Docstring + axioms comment describe behavior/modeling abstractly, not the edit; no pre/post distinction is drawn in the spec view.

Semantic assessment: the discriminating behavior the fix establishes ('every collected entry carries the documentation text recorded for its name') is expressed as the correct target specification of a module-entry collector, at the same abstraction level the public task already implies (honoring a variable's :meta public: metadata necessarily requires carrying its documentation text). No file, no repo function, no pre/post narration is revealed. The pre/post 'the fix'/'the bug' narration lives ONLY in mapping.md and refinement.md, which are auditor-facing and NOT part of the solver-visible spec view. A faithful spec at this level does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
