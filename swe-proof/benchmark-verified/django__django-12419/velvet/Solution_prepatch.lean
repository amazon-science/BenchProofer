import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the shipped default policy is a value the framework
--  supplies directly, modeled deeply as its concrete token sequence.)
-- axioms-end

-- pure-start
/- The concrete default referrer-policy token the framework ships, modeled as a
   `List Char`. A definite, restrictive policy that confines the referrer to the
   same origin, so that by default the framework does not disclose the
   originating address to third-party destinations. The provider never yields an
   absent/unset sentinel. -/
def sameOriginPolicy : List Char := "same-origin".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default referrer-policy token — the value used to
   populate the corresponding response header for every served response. The
   query returns that default policy. A definite same-origin restriction is
   provided (rather than the unset/absent sentinel that emits no policy at all)
   so that, out of the box, responses carry an information-confining default.
   The provider takes no input and never mutates anything (directive 5). The
   policy token is modeled as a `List Char`. -/
method defaultReferrerPolicy return (policy : List Char)
  ensures policy = sameOriginPolicy
  ensures policy = "same-origin".toList
  ensures policy ≠ []
  do
    -- impl-start
    -- Pre-image: no definite policy was provided (the default was the unset
    -- sentinel, emitting no policy at all); the closest faithful buggy skeleton
    -- yields the absent value, modeled as the empty token sequence. MUST fail
    -- `policy = sameOriginPolicy` (and `policy ≠ []`).
    return []
    -- impl-end

prove_correct defaultReferrerPolicy by
  loom_solve <;> simp [sameOriginPolicy]
