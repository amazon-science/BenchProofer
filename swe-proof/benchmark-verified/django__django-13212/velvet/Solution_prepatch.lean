import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   unchanged sub-step — the per-input validity test — is modeled as a FREE
   Boolean `isValid` (see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract (it is strictly weaker than any
   concrete test — directive 7). The behaviour this bundle actually pins — how
   the rejection report is constructed on the failing branch — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of a rejection report: a short machine `code` and an
   ordered list of named substitution bindings (`params`) consulted by message
   templating. These are the only fields the desired behaviour constrains
   (mapping.md §2). A report is carried by `Except.error`; acceptance is
   `Except.ok ()`. -/
structure Report where
  code : List Char
  params : List (String × List Char)
  deriving DecidableEq

/- Look up a named binding in the ordered params list — the front-to-back scan a
   `%(name)s` template performs. First match wins (mirrors dict semantics for the
   appended-last key, given the keys already present are distinct from it). -/
def lookupKey (k : String) : List (String × List Char) → Option (List Char)
  | []            => none
  | (k', v) :: rest => if k' = k then some v else lookupKey k rest

/- The rejection report built on the failing branch: the machine `code`, the
   bindings already present, AND the input itself bound to the `"value"` key so a
   custom message template can interpolate it. This is the deep model of the
   constructed report; the appended `("value", value)` is the whole of the
   desired behaviour. -/
def buildReport (code : List Char) (oldParams : List (String × List Char))
    (value : List Char) : Report :=
  { code := code, params := oldParams ++ [("value", value)] }

/- The outcome of validating one input: acceptance carries nothing; rejection
   carries the report built for the failing branch. -/
def checkOutcome (isValid : Bool) (code : List Char)
    (oldParams : List (String × List Char)) (value : List Char) :
    Except Report Unit :=
  if isValid then Except.ok () else Except.error (buildReport code oldParams value)

@[grind] lemma checkOutcome_ok (code oldParams value) :
    checkOutcome true code oldParams value = Except.ok () := rfl
@[grind] lemma checkOutcome_err (code oldParams value) :
    checkOutcome false code oldParams value
      = Except.error (buildReport code oldParams value) := rfl

/- Appending a binding under a key absent from the list makes that key resolve to
   the appended value: the scan misses every earlier entry and finds the tail. -/
@[grind] lemma lookupKey_append_fresh (k : String) (v : List Char)
    (xs : List (String × List Char)) (h : lookupKey k xs = none) :
    lookupKey k (xs ++ [(k, v)]) = some v := by
  induction xs with
  | nil => simp [lookupKey]
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp [hk] at h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h

/- Appending anything preserves a key that already resolves: the first match is
   found before the appended tail is reached (the unchanged-frame guarantee for
   the pre-existing bindings — directive 5). -/
@[grind] lemma lookupKey_append_pres (k : String) (v : List Char)
    (ys : List (String × List Char)) (xs : List (String × List Char))
    (h : lookupKey k xs = some v) :
    lookupKey k (xs ++ ys) = some v := by
  induction xs with
  | nil => simp [lookupKey] at h
  | cons p rest ih =>
    obtain ⟨k', v'⟩ := p
    simp only [lookupKey, List.cons_append] at h ⊢
    by_cases hk : k' = k
    · simp only [hk, reduceIte] at h ⊢; exact h
    · simp only [hk, reduceIte] at h ⊢
      exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Check one input and, on failure, construct the rejection report. The input
   `value` (as a custom message template would stringify it), the report's
   machine `code`, and any bindings the report already carries (`oldParams`) are
   read-only; `isValid` abstracts the input's (unchanged) validity test. Desired
   behaviour: a passing input is accepted with no report; a failing input is
   rejected with a report that keeps its `code` and every pre-existing binding
   AND additionally binds the input itself to the `"value"` key, so a custom
   message can interpolate the offending input. `require`: the report does not
   already bind `"value"` (none of the real sites do — mapping.md §1.1/§2). -/
method checkValue (value : List Char) (code : List Char)
    (oldParams : List (String × List Char)) (isValid : Bool)
    return (out : Except Report Unit)
  require lookupKey "value" oldParams = none
  ensures out = checkOutcome isValid code oldParams value
  ensures isValid = true → out = Except.ok ()
  ensures isValid = false → out = Except.error (buildReport code oldParams value)
  ensures isValid = false →
    lookupKey "value" (buildReport code oldParams value).params = some value
  ensures (buildReport code oldParams value).code = code
  ensures ∀ k v, k ≠ "value" → lookupKey k oldParams = some v →
    lookupKey k (buildReport code oldParams value).params = some v
  do
    -- impl-start
    -- The validity test is unchanged; only the failing branch's report changes.
    -- Accept a valid input with no report; reject an invalid one with a report
    -- carrying only its code and the bindings it already had.
    let result : Except Report Unit :=
      if isValid then Except.ok ()
      else Except.error { code := code, params := oldParams }
    return result
    -- impl-end

prove_correct checkValue by
  loom_solve <;>
    simp_all [buildReport, lookupKey_append_fresh, lookupKey_append_pres]
