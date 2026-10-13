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
Pre-patch: an entry that is itself a symbolic link is NOT treated as a directory,
so the walk never descends into a symlinked directory. -/
def entryIsDir : FSNode → Bool
  | .file => false
  | .dir isSymlink _ => !isSymlink

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
theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl
          -- (a symlinked directory entry is dropped from the walk) — G-DIFF.
-- proof-end
