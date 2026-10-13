import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is left opaque: the vocabulary-validation step and the
-- index-ordered feature-name extraction are both modeled DEEPLY below
-- (`validateList` / `featureNames`), so they are A-references (validated ==
-- the real callees by G-AX), not consumed axioms. The `axioms` region is empty.
-- axioms-end

-- pure-start
/-- Outcome of requesting the ordered feature names of a text vectorizer.
The three error shapes are the observable failure modes:
* `notFitted` — no usable vocabulary is available at all;
* `dup`       — a supplied vocabulary lists the same term more than once;
* `empty`     — the available vocabulary has no terms. -/
inductive VErr | notFitted | dup | empty
  deriving DecidableEq, Repr

/-- The state of a vectorizer at the moment feature names are requested.
* `learned` — `some v` when a vocabulary (term ↦ integer index) is already
  available on the object (e.g. established from data during fitting); `none`
  otherwise.
* `param`   — `some p` when a vocabulary was supplied at construction time as an
  ordered list of terms; `none` otherwise. -/
structure VecState where
  learned : Option (List (String × Nat))
  param   : Option (List String)

/-- Turn a constructor-supplied ordered term list into a term↦index vocabulary.
Mirrors the standard validation of a list vocabulary: an empty list is rejected
(`empty`); a list with a repeated term is rejected (`dup`); otherwise each term
is paired with its position in the list. -/
def validateList (p : List String) : Except VErr (List (String × Nat)) :=
  if p.isEmpty then Except.error VErr.empty
  else if p.dedup.length ≠ p.length then Except.error VErr.dup
  else Except.ok p.zipIdx

/-- The ordered feature names of a vocabulary: the terms taken in increasing
order of their integer index. -/
def featureNames (voc : List (String × Nat)) : List String :=
  (voc.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)
-- pure-end

-- post-conditions-start
/-- The ordered feature names are produced whenever a vocabulary is available,
and exactly the documented error is reported otherwise.

* If a vocabulary is already available (`learned = some v`): an empty vocabulary
  reports `empty`; a non-empty one yields its index-ordered feature names.
* Otherwise, if a vocabulary was supplied at construction (`param = some p`): the
  supplied list is validated; on a validation error that error is reported, and
  on success the (non-empty) validated vocabulary yields its index-ordered
  feature names.
* Otherwise (no vocabulary at all): `notFitted` is reported. -/
def problem_spec_getFeatureNames
    (st : VecState) (result : Except VErr (List String)) : Prop :=
  match st.learned with
  | some v =>
      (v.isEmpty → result = Except.error VErr.empty) ∧
      (¬ v.isEmpty → result = Except.ok (featureNames v))
  | none =>
      match st.param with
      | none => result = Except.error VErr.notFitted
      | some p =>
          match validateList p with
          | Except.error e => result = Except.error e
          | Except.ok v =>
              (v.isEmpty → result = Except.error VErr.empty) ∧
              (¬ v.isEmpty → result = Except.ok (featureNames v))
-- post-conditions-end

-- impl-start
def implementation_getFeatureNames
    (st : VecState) : Except VErr (List String) := Id.run do
  let mut voc : List (String × Nat) := []
  match st.learned with
  | some v => voc := v
  | none =>
    -- pre-patch behavior: with no already-available vocabulary, the request is
    -- rejected outright — a constructor-supplied vocabulary is NOT consulted to
    -- establish one before reporting the result.
    return Except.error VErr.notFitted
  if voc.isEmpty then return Except.error VErr.empty
  return Except.ok (featureNames voc)
-- impl-end

-- proof-start
theorem correct_getFeatureNames : ∀ st : VecState,
    problem_spec_getFeatureNames st (implementation_getFeatureNames st) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
