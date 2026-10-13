import Mathlib
-- imports-end

/-!
Collecting the labels attached to a class together with the labels attached to
all of the classes it descends from.

A class may carry a list of labels of its own. When a class participates in an
inheritance hierarchy, the labels that apply to it are not only the ones stored
directly on it: the labels stored on each of its ancestor classes apply as well.
The ancestors are visited in the hierarchy's own resolution order — the class
itself first, then its parents, and so on — and the labels they carry are
gathered into a single flat list, preserving that order and keeping duplicates.

A class is permitted to store its labels either as an explicit list or as a
single bare label; both forms contribute their label(s) to the gathered result.

The operation also supports a restricted mode in which only the labels stored
directly on the class itself are gathered, ignoring everything inherited.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only auxiliary step —
-- coercing each stored entry into a sequence of labels and validating it — is an
-- order-preserving identity on values that are already labels, so it is modeled
-- concretely (the per-entry flattening below) rather than axiomatized.
-- axioms-end

-- pure-start
/-- A label (the abstract carrier of a single annotation). Only the data the
behavior observes is modeled: a name and its positional arguments. -/
structure Mark where
  name : String
  args : List String
deriving DecidableEq, Repr

/-- What one class stores under its label attribute: either an explicit list of
labels, or a single bare label. -/
inductive ClassMarks where
  | many : List Mark → ClassMarks
  | one  : Mark → ClassMarks
deriving Repr

/-- The labels contributed by one class's stored entry: a stored list passes
through verbatim; a single bare label becomes a one-element list. -/
def flattenClassMarks : ClassMarks → List Mark
  | .many xs => xs
  | .one m   => [m]
-- pure-end

-- post-conditions-start
/-- `hierarchy` lists, in resolution order, what each class in the inheritance
chain stores directly (index `0` is the class itself). `wholeHierarchy` selects
the mode:

* when `true`, the result is every class's own labels concatenated in
  resolution order (the class's labels first, then each ancestor's);
* when `false`, the result is only the labels stored directly on the class
  itself (the head of the chain), ignoring all ancestors.

Each class's stored entry contributes its label(s) via `flattenClassMarks`. -/
def problem_spec_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool)
    (result : List Mark) : Prop :=
  result =
    (if wholeHierarchy then hierarchy.flatMap flattenClassMarks
     else flattenClassMarks (hierarchy.headD (ClassMarks.many [])))
-- post-conditions-end

-- impl-start
def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark := Id.run do
  -- restricted mode: only the class's own stored entry; full mode: every class
  -- in the resolution chain.
  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy
  let mut markList : List Mark := []
  for item in markLists do
    match item with
    | .many xs => markList := markList ++ xs
    | .one m   => markList := markList ++ [m]
  return markList
-- impl-end

-- proof-start
theorem loop_helper :
    ∀ (markLists : List ClassMarks) (init : List Mark),
      (Id.run (do
        let r ← forIn markLists init (fun item markList =>
          (match item with
            | .many xs => do pure PUnit.unit; pure (ForInStep.yield (markList ++ xs))
            | .one m   => do pure PUnit.unit; pure (ForInStep.yield (markList ++ [m]))))
        pure r)) =
        init ++ markLists.flatMap flattenClassMarks := by
  intro markLists
  induction markLists with
  | nil => intro init; simp only [List.forIn_nil, List.flatMap_nil, List.append_nil, Id.run, bind, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    cases a with
    | many xs =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]
    | one m =>
      simp only [Id.run, bind] at ih ⊢
      simp only [flattenClassMarks, List.flatMap_cons, ih, List.append_assoc]

theorem correct_inheritedMarks :
    ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
      problem_spec_inheritedMarks hierarchy wholeHierarchy
        (implementation_inheritedMarks hierarchy wholeHierarchy) := by
  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  rw [loop_helper]
  simp only [List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false =>
    simp only [Bool.not_false, if_true]
    cases h2 : hierarchy.headD (ClassMarks.many []) with
    | many xs => simp [flattenClassMarks]
    | one m => simp [flattenClassMarks]
-- proof-end
