import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the flag-computation slice of a string-preprocessing
helper. The routine has an optional bracket-handling branch; within it a marker
is substituted for any spaces and a membership flag is computed. The desired
behaviour: the flag is computed for every input that enters the branch — never
left undefined — so an input that enters the branch without producing a space
yields an unset flag rather than aborting the routine.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the marker-membership step is
-- modeled DEEPLY (its value is determined by whether a space is present, below)
-- rather than axiomatized, and validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone functional helper is needed: the flag is the boolean
-- conjunction of the branch gate and space-presence, computed inline.
-- pure-end

-- post-conditions-start
/-- The result is always a well-defined flag (the routine never aborts). The
flag is set exactly when the bracket-handling branch is active AND the string
contains a space at the marker-substitution point: in that case a fresh marker
is substituted for the spaces and is therefore present, so the membership flag
is set; in every other case the flag is unset. -/
def problem_spec_kernSHit
    (parenBranch : Bool) (s : List Char) (result : Except Unit Bool) : Prop :=
  result = Except.ok (parenBranch && s.contains ' ')
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) skeleton: the membership flag is read UNCONDITIONALLY
after the space branch, but the marker is bound only inside that branch. When
the bracket-handling branch is active and no space is present, the marker is
unbound, so reading it aborts the routine (the reported referenced-before-
assignment failure), modeled as `Except.error ()`. -/
def implementation_kernSHit
    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do
  let mut hit : Bool := false
  let mut kernBound : Bool := false   -- whether the marker has been assigned
  if parenBranch then
    if s.contains ' ' then
      -- a fresh marker is bound and substituted for the spaces
      kernBound := true
    -- the membership read runs unconditionally inside the branch:
    if kernBound then
      hit := true            -- the substituted marker is present
    else
      return Except.error ()  -- marker referenced before assignment
  return Except.ok hit
-- impl-end

-- proof-start
theorem correct_kernSHit : ∀ (parenBranch : Bool) (s : List Char),
    problem_spec_kernSHit parenBranch s (implementation_kernSHit parenBranch s) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF):
          -- for parenBranch = true and a space-free s the impl returns
          -- `Except.error ()` while the spec demands `Except.ok false`.
-- proof-end
