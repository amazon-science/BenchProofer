import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decoration count is
-- modeled DEEPLY over an abstraction of each decoration (below): whether it binds
-- a named attribute, whether its replacement is one of the recognised sentinel
-- defaults, and whether comparing that replacement for equality yields an
-- ordinary boolean. No outside callee property is consumed; the proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- Abstraction of a single mock-patch decoration attached to a test function.

* `attributeName` — `true` when the decoration binds a named attribute (so it
  does NOT consume one of the function's positional arguments).
* `isSentinel` — `true` when the decoration's replacement value is one of the
  recognised sentinel "default" objects (the marker meaning "auto-create a mock
  for this argument").
* `eqWellDefined` — `true` when comparing this replacement value for equality
  against another object yields an ordinary boolean. It is `false` for values
  (such as numeric arrays) whose equality comparison produces a non-boolean and
  therefore has an ambiguous truth value. -/
structure Patching where
  attributeName : Bool
  isSentinel : Bool
  eqWellDefined : Bool
deriving DecidableEq, Repr

/-- A decoration consumes one mandatory argument exactly when it does not bind a
named attribute and its replacement is one of the recognised sentinel defaults. -/
def isCounted (p : Patching) : Bool := !p.attributeName && p.isSentinel
-- pure-end

-- post-conditions-start
/-- The number of mandatory arguments consumed by mock-patch decorations is
returned as `some n`, where `n` is exactly the count of decorations that consume
an argument (do not bind a named attribute and replace with a sentinel default).
The count is always produced (`some _`): determining it must never depend on the
ambiguous truth value of an equality comparison, so a decoration whose
replacement compares with an ill-defined truth value is still classified totally
by the structural criterion above. -/
def problem_spec_num_mock_patch_args
    (patchings : List Patching) (result : Option Nat) : Prop :=
  result = some ((patchings.filter isCounted).length)
-- post-conditions-end

-- impl-start
-- Pre-patch skeleton: a decoration is classified by comparing its replacement
-- for EQUALITY against each sentinel default. For a non-attribute decoration
-- whose replacement has an ambiguous equality truth value, that comparison
-- aborts the whole computation (`none`) instead of yielding a count.
def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
  if patchings.isEmpty then
    return some 0
  let mut count : Nat := 0
  for p in patchings do
    if !p.attributeName then
      if !p.eqWellDefined then
        return none
      if p.isSentinel then
        count := count + 1
  return some count
-- impl-end

-- proof-start
theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
    problem_spec_num_mock_patch_args patchings
      (implementation_num_mock_patch_args patchings) := by
  intro patchings
  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
  -- carries the gold proof shape; UNCLOSABLE against the buggy impl (G-DIFF):
  -- the equality-membership skeleton returns `none` for inputs with an
  -- ill-defined equality truth value, contradicting `some _`.
  simp
-- proof-end
