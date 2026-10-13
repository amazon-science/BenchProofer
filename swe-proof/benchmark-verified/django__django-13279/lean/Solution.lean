import Mathlib
-- imports-end

/-!
Serializing session data into a transport string, where two interchangeable
serialization schemes coexist during a cross-version transition.

A deployment may run several instances of the same project side by side while it
moves between two release lines, and those instances must be able to read each
other's serialized session data. To make that possible, the project exposes a
configured serialization-format identifier that selects which of two
interchangeable schemes is produced when session data is serialized:

  * a designated compatibility scheme, requested by the identifier value
    `"sha1"`, that produces strings in the older interchange format (the format
    the matching reader already accepts); and
  * the standard scheme used otherwise.

The desired behavior is therefore a dispatch on the configured identifier: when
the identifier is `"sha1"`, the session data is serialized with the
compatibility scheme; for every other identifier value, it is serialized with
the standard scheme. The chosen scheme fully determines the produced string.
-/

-- axioms-start
/-- The compatibility serialization scheme: it serializes session data into the
older interchange-format string. It is consumed here as an opaque carrier — the
behavior modeled in this bundle is *which* scheme is selected for given session
data, not the internal byte layout of the scheme itself. -/
opaque legacyEncode : List (String × String) → String

/-- The standard serialization scheme used outside the compatibility case. Like
`legacyEncode`, it is an opaque carrier: only the fact that it is the scheme
selected in the non-compatibility case is modeled, not its internal details. -/
opaque modernEncode : List (String × String) → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the single
-- dispatch between the two serialization schemes on the configured identifier.
-- pure-end

-- post-conditions-start
/-- The produced string is fully pinned to the inputs:

  * when the configured serialization-format identifier is `"sha1"`, it is
    exactly the compatibility scheme applied to the session data;
  * for every other identifier value, it is exactly the standard scheme applied
    to the session data.

Both cases together determine the result for every input, so no part of the
output is left free. -/
def problem_spec_encode
    (algo : String) (session : List (String × String)) (result : String) : Prop :=
  (algo = "sha1" → result = legacyEncode session) ∧
  (algo ≠ "sha1" → result = modernEncode session)
-- post-conditions-end

-- impl-start
def implementation_encode
    (algo : String) (session : List (String × String)) : String := Id.run do
  if algo == "sha1" then
    return legacyEncode session
  return modernEncode session
-- impl-end

-- proof-start
theorem correct_encode :
    ∀ (algo : String) (session : List (String × String)),
      problem_spec_encode algo session
        (implementation_encode algo session) := by
  intro algo session
  unfold problem_spec_encode implementation_encode
  by_cases h : algo = "sha1"
  · subst h
    refine ⟨fun _ => rfl, fun hne => ?_⟩
    exact absurd rfl hne
  · have hb : (algo == "sha1") = false := by
      simpa using h
    refine ⟨fun habs => absurd habs h, fun _ => ?_⟩
    simp only [Id.run, hb]
    rfl
-- proof-end
