import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the combined operation is modeled deeply via an explicit
--  store of object contents and a fresh-handle allocator. Soundness of that
--  deep model against the real object-copy semantics is audited by G-AX.)
-- axioms-end

-- pure-start
/- The contents carried by one mapping object: an ordered collection of
   key/value entries. Modeled as an association list so two objects holding the
   same entries compare equal while still being separable by identity. -/
abbrev Entries := List (String × String)

/- An object identity — a handle into the live store. Distinct handles denote
   distinct mutable objects, so an update made through one handle is invisible
   through every other handle. The store maps each live handle to its current
   contents; `fresh` is the next handle never yet handed out. -/
abbrev Handle := Int
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a non-empty sequence of mapping objects under the policy that takes
   the first object's contents. The returned object carries exactly those
   contents, is an object of its own (distinct from every input), and leaves
   every input object untouched — so later updates to the result are not seen
   through any input handle. -/
method combineFirst (mut store : Handle → Entries) (mut fresh : Handle)
    (sources : List Handle) return (result : Handle)
  require sources ≠ []
  require ∀ h, h ∈ sources → h < fresh
  ensures store result = storeOld (sources.head!)
  ensures result ∉ sources
  ensures ∀ h, h ∈ sources → store h = storeOld h
  ensures result = freshOld
  ensures fresh = freshOld + 1
  do
    -- impl-start
    let result := fresh
    store := Function.update store fresh (store sources.head!)
    fresh := fresh + 1
    return result
    -- impl-end

prove_correct combineFirst by
  loom_solve
  all_goals (
    try (intro h hmem)
    -- a handle differs from the freshly-allocated one iff it is an input handle
    first
    | (simp [Function.update_self])
    | (have hlt : h < freshOld := require_1 h hmem
       simp [Function.update_of_ne (ne_of_lt hlt)]))
