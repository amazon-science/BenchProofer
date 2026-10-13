import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom. The directory-tree walk is
-- modeled deeply below (`collectTree`), and the per-level ordering operation is
-- modeled deeply as a name-keyed sort (`sortByName`). The recursion predicate is
-- an arbitrary caller-supplied Boolean filter and is taken as a function
-- parameter, not axiomatized.
-- axioms-end

-- pure-start
/-- A node in a directory tree as seen by the collector.
* `file` — a non-directory entry.
* `dir isSymlink children` — an entry that resolves to a directory; `isSymlink`
  records whether the entry itself is a symbolic link (its `children` are the
  contents of the resolved directory). -/
inductive FSNode where
  | file
  | dir (isSymlink : Bool) (children : List (String × FSNode))
  deriving Inhabited

/-- A directory entry: its name paired with the node it denotes. -/
abbrev DirEntry := String × FSNode

/-- Order the entries of a single directory level by name (ascending). -/
def sortByName (es : List DirEntry) : List DirEntry :=
  es.mergeSort (fun a b => a.1 ≤ b.1)

/-- The breadth-first directory walk that is the desired behavior: at each
directory level the entries are emitted in name order, and then, for every
entry that resolves to a directory and that the caller's `recurse` predicate
selects, the walk descends into that directory's contents and emits its subtree
in the same way — regardless of whether the entry is a symbolic link. The result
is the in-order concatenation of every emitted entry. -/
def collectTree (recurse : DirEntry → Bool) : List DirEntry → List DirEntry
  | xs =>
    let entries := sortByName xs
    entries ++ entries.attach.flatMap (fun ⟨e, he⟩ =>
      if recurse e then
        match h : e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []
      else [])
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp he
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [h]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- pure-end

-- post-conditions-start
/-- The collected list is exactly the in-order directory walk of the input
level: the entries of every directory reachable (through the caller's `recurse`
filter) appear, in name order per level and descending into every directory
entry — symbolic links to directories included. -/
def problem_spec_collect (recurse : DirEntry → Bool) (entries0 : List DirEntry)
    (result : List DirEntry) : Prop :=
  result = collectTree recurse entries0
-- post-conditions-end

-- impl-start
/-- Whether a directory entry should be treated as a directory to descend into.
A resolved directory counts as a directory whether or not the entry is itself a
symbolic link. -/
def entryIsDir : FSNode → Bool
  | .file => false
  | .dir _ _ => true

def implementation_collect (recurse : DirEntry → Bool) :
    List DirEntry → List DirEntry
  | xs => Id.run do
    let entries := sortByName xs
    let mut acc := entries
    for h : e in entries do
      if entryIsDir e.2 && recurse e then
        match h2 : e.2 with
        | .dir _ ch => acc := acc ++ implementation_collect recurse ch
        | .file => pure ()
    return acc
termination_by xs => sizeOf xs
decreasing_by
  simp_wf
  show sizeOf ch < sizeOf xs
  have hmem : e ∈ xs :=
    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h
  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)
  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega
-- impl-end


-- proof-start
/-- The plain functional value that the imperative body of `implementation_collect`
evaluates to: the sorted level followed by the per-entry concatenation over
`entries.attach`. -/
def loopBody (recurse : DirEntry → Bool) (entries : List DirEntry) : List DirEntry :=
  entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
    if entryIsDir p.1.2 && recurse p.1 then
      match p.1.2 with
      | .dir _ ch => implementation_collect recurse ch
      | .file => []
    else [])

theorem foldl_append_flatMap {α β : Type*} (l : List α) (f : α → List β) (a : List β) :
    l.foldl (fun acc x => acc ++ f x) a = a ++ l.flatMap f := by
  induction l generalizing a with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]

theorem impl_unfold (recurse : DirEntry → Bool) (xs : List DirEntry) :
    implementation_collect recurse xs =
      (let entries := sortByName xs;
       entries ++ entries.attach.flatMap (fun (p : {e // e ∈ entries}) =>
         if entryIsDir p.1.2 && recurse p.1 then
           match p.1.2 with
           | .dir _ ch => implementation_collect recurse ch
           | .file => []
         else [])) := by
  rw [← foldl_append_flatMap]
  conv_lhs => rw [implementation_collect]
  simp only [bind_pure_comp, map_pure, bind_pure, Id.run]
  rw [show (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        (if (entryIsDir a.2 && recurse a) = true then
          match h : a.2 with
          | .dir _ ch => pure (ForInStep.yield (b ++ implementation_collect recurse ch))
          | .file => pure (ForInStep.yield b)
        else pure (ForInStep.yield b) : Id (ForInStep (List DirEntry))))
      = (fun (a : DirEntry) (m : a ∈ sortByName xs) (b : List DirEntry) =>
        ForInStep.yield (b ++ (if (entryIsDir a.2 && recurse a) = true then
          match a.2 with
          | .dir _ ch => implementation_collect recurse ch
          | .file => []
        else []))) from by
      funext a m b
      obtain ⟨nm, nd⟩ := a
      cases nd with
      | file =>
        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
        rfl
      | dir s ch =>
        by_cases hr : recurse (nm, FSNode.dir s ch) = true
        · simp only [entryIsDir, Bool.true_and, hr, if_true]
          rfl
        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
          rfl]
  rw [List.forIn'_yield_eq_foldl]

theorem entry_body_eq (recurse : DirEntry → Bool) (e : DirEntry)
    (ih : ∀ (b : Bool) (ch : List DirEntry), e.2 = .dir b ch →
      implementation_collect recurse ch = collectTree recurse ch) :
    (if entryIsDir e.2 && recurse e then
       (match e.2 with
        | .dir _ ch => implementation_collect recurse ch
        | .file => []) else []) =
    (if recurse e then
       (match e.2 with
        | .dir _ ch => collectTree recurse ch
        | .file => []) else []) := by
  obtain ⟨name, node⟩ := e
  cases node with
  | file => simp [entryIsDir]
  | dir b ch =>
    simp only [entryIsDir, Bool.true_and]
    rw [ih b ch rfl]

theorem children_size_decreasing (entries0 : List DirEntry) (e : DirEntry)
    (b : Bool) (ch : List DirEntry) (hmem : e ∈ sortByName entries0)
    (hdir : e.2 = .dir b ch) : sizeOf ch < sizeOf entries0 := by
  simp only [sortByName] at hmem
  have hmem2 : e ∈ entries0 :=
    ((List.mergeSort_perm entries0 (fun a b => a.1 ≤ b.1)).mem_iff).mp hmem
  have h1 : sizeOf e ≤ sizeOf entries0 := le_of_lt (List.sizeOf_lt_of_mem hmem2)
  have h2 : sizeOf ch < sizeOf e.2 := by rw [hdir]; simp
  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp
  omega

theorem main_induction (recurse : DirEntry → Bool) (entries0 : List DirEntry) :
    implementation_collect recurse entries0 = collectTree recurse entries0 := by
  have key : ∀ n, ∀ es : List DirEntry, sizeOf es < n →
      implementation_collect recurse es = collectTree recurse es := by
    intro n
    induction n with
    | zero => intro es h; omega
    | succ n ih =>
      intro es hlt
      rw [impl_unfold]
      conv_rhs => rw [collectTree]
      simp only []
      congr 1
      apply List.flatMap_congr
      intro p _
      have ih' : ∀ (b : Bool) (ch : List DirEntry), p.1.2 = .dir b ch →
          implementation_collect recurse ch = collectTree recurse ch := by
        intro b ch hdir
        have hmem : p.1 ∈ sortByName es := p.2
        have hlt2 : sizeOf ch < sizeOf es :=
          children_size_decreasing es p.1 b ch hmem hdir
        exact ih ch (by omega)
      rw [entry_body_eq recurse p.1 ih']
      cases p.1.2 <;> rfl
  exact key (sizeOf entries0 + 1) entries0 (by omega)

theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  intro recurse entries0
  show implementation_collect recurse entries0 = collectTree recurse entries0
  exact main_induction recurse entries0

-- proof-end
