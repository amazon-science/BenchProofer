import Mathlib
-- imports-end

/-!
Expanding a combined array into a labelled collection of its constituent
variables.

The data carries a list of variable labels along one axis. The operation walks
that list of labels and, for each label, extracts that variable's slice of the
data, assembling the slices into a labelled collection — one entry per label, in
the order the labels are listed.

Each slice is extracted in the label-removing mode: when the slice for a label is
selected, the selecting label is dropped from the slice rather than retained on
it as an attached scalar marker. The required behavior is that every slice is
extracted in this label-removing mode, and that the result lists exactly the
labels, in order, each paired with its extracted slice.

The extraction of a single slice (selecting it and reducing away the now-singleton
axes) is itself a self-contained step; what this bundle pins is the mode in which
that step is invoked and the structure of the assembled collection.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed as a logical property. The
-- per-label slice extraction (selecting the slice for a label and reducing away
-- the now-singleton axes) is left UNIVERSALLY QUANTIFIED as a parameter
-- `extractSlice : Bool → κ → ν`: the first argument is the extraction mode (the
-- label-removing mode when `true`, the label-retaining mode when `false`) and
-- the second is the variable label. The specification holds for EVERY such
-- extraction step, so it pins only that the label-removing mode reaches the
-- extraction for each label, which is exactly the behavior under specification.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the labelled collection is expressed
-- directly as a map over the list of labels.
-- pure-end

-- post-conditions-start
/-- The assembled collection of extracted variables.

`κ` is the type of a variable label and `ν` the type of an extracted slice.
`extractSlice mode k` is the extraction of the slice for label `k`, performed in
label-removing mode when `mode = true`. The result is the list of `(label, slice)`
entries.

The result is fully pinned for every input (directive 5 frame): it is exactly the
list of labels, in their given order, each paired with the slice extracted in the
label-removing mode (`extractSlice true k`). No entry, order, or extraction mode
is left free — in particular each slice must be the one produced with the label
removed, never the label-retaining extraction. -/
def problem_spec_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ)
    (result : List (κ × ν)) : Prop :=
  result = vars.map (fun k => (k, extractSlice true k))
-- post-conditions-end

-- impl-start
def implementation_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    List (κ × ν) := Id.run do
  -- PRE-PATCH (buggy): each slice is extracted WITHOUT the label-removing mode,
  -- i.e. in the label-retaining extraction (`extractSlice false k`). Every slice
  -- then still carries its selecting label as a scalar marker, so the assembled
  -- collection carries conflicting marker values and the round-trip is broken.
  let mut dataDict : List (κ × ν) := []
  for k in vars do
    dataDict := dataDict ++ [(k, extractSlice false k)]
  return dataDict
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: the loop here extracts each slice in the label-retaining
-- mode (`extractSlice false k`), so the accumulated list pairs every label with
-- `extractSlice false k`, whereas the spec demands `extractSlice true k`. On any
-- nonempty `vars` whose two extraction modes differ, the `forIn`→`map` bridge
-- below rewrites a loop over `extractSlice true k`, which does not match the
-- impl's `extractSlice false k`, so the rewrite (and hence the proof) fails.
theorem forIn_collect_eq {κ ν : Type} (extractSlice : Bool → κ → ν)
    (vars : List κ) (init : List (κ × ν)) :
    (Id.run (forIn vars init (fun k acc =>
        (ForInStep.yield (acc ++ [(k, extractSlice true k)]) :
          Id (ForInStep (List (κ × ν)))))))
    = init ++ vars.map (fun k => (k, extractSlice true k)) := by
  induction vars generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih, List.map_cons]
    simp [List.append_assoc]

theorem correct_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    problem_spec_toUnstackedDataset extractSlice vars
      (implementation_toUnstackedDataset extractSlice vars) := by
  unfold problem_spec_toUnstackedDataset implementation_toUnstackedDataset
  rw [forIn_collect_eq]
  simp
-- proof-end
