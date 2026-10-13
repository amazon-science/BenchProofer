import Mathlib
-- imports-end

/-!
Username admissibility checks.

A username is a finite sequence of characters. Two admissibility checks are
modeled, differing only in which characters they treat as *allowed*:

* one whose allowed set is the English-letter family — English letters, digits,
  the underscore, and the four punctuation characters `.`, `@`, `+`, `-`;
* one whose allowed set is the international-letter family — letters from any
  script, digits, the underscore, and the same four punctuation characters.

In both cases the intended rule is the same and is stated purely over the whole
sequence: a username is admissible exactly when it is non-empty AND every one of
its characters belongs to the relevant allowed set. In particular a sequence is
admissible only if it consists *entirely* of allowed characters from its first
character through its very last; a sequence that carries any non-allowed
character anywhere — including a terminating line-break character — is not
admissible.

The per-character membership test (whether a single character belongs to the
allowed set) is an unchanged building block and is left abstract here; only the
whole-sequence admissibility rule is modeled.
-/

-- axioms-start
/-- Whether a single character belongs to the English-letter allowed set
(English letters, digits, underscore, and `.` `@` `+` `-`). An unchanged
per-character building block; left abstract (its exact membership is
orthogonal to the whole-sequence rule modeled here — see mapping.md). -/
opaque isAllowedAscii : Char → Bool

/-- Whether a single character belongs to the international-letter allowed set
(letters from any script, digits, underscore, and `.` `@` `+` `-`). The
unicode-flavored counterpart of `isAllowedAscii`; likewise abstract. -/
opaque isAllowedUnicode : Char → Bool
-- axioms-end

-- pure-start
-- The whole-sequence admissibility rule is expressed directly with `List.all`
-- and emptiness in the post-condition; no additional functional helper is
-- needed here.
-- pure-end

-- post-conditions-start
/-- Admissibility against the English-letter allowed set: the result is `true`
exactly when the username is non-empty and every character is allowed. The whole
sequence must consist of allowed characters (frame: the result is pinned as this
exact boolean of the input — nothing about the result is left free). -/
def problem_spec_validateAscii (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedAscii)
-- post-conditions-end

-- impl-start
def implementation_validateAscii (username : List Char) : Bool := Id.run do
  -- A single terminating line-break character is tolerated: it is dropped before
  -- the whole-sequence check, so a sequence of allowed characters followed by one
  -- such character is still admitted.
  let core := if username.getLast? = some '\n' then username.dropLast else username
  if core.isEmpty then
    return false
  let mut ok := true
  for c in core do
    if !isAllowedAscii c then
      ok := false
  return ok
-- impl-end

-- proof-start
theorem correct_validateAscii : ∀ username : List Char,
    problem_spec_validateAscii username (implementation_validateAscii username) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end

-- post-conditions-start
/-- Admissibility against the international-letter allowed set: the result is
`true` exactly when the username is non-empty and every character is allowed. -/
def problem_spec_validateUnicode (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedUnicode)
-- post-conditions-end

-- impl-start
def implementation_validateUnicode (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedUnicode c then
      ok := false
  return ok
-- impl-end

-- proof-start
theorem correct_validateUnicode : ∀ username : List Char,
    problem_spec_validateUnicode username (implementation_validateUnicode username) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
