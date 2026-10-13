import Mathlib
-- imports-end

/-!
Normalizing the *method name* of an outgoing HTTP request before the request is
assembled.

A request's method (`GET`, `POST`, …) arrives as a text string. Two things must
hold of the method that is finally stored on the request:

* its textual content is the upper-cased form of the supplied name (HTTP method
  tokens are case-insensitive and are canonicalized to upper case);
* it is a *native* text string — never a "wide" text string. A caller is free to
  supply the name as a wide string, but the stored method must not carry that
  wide character type forward, because a wide method name later contaminates the
  assembled request with wide text and corrupts transmission.

A text string is modeled by its sequence of code points together with a flag
recording whether it is a wide string. The behavior is pinned below as an
input → output relation on the supplied method name; the implementation and the
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two operations the
-- behavior performs — upper-casing the code points and producing a native (not
-- wide) text string — are modeled DEEPLY (`List.map Char.toUpper` and clearing
-- the wide flag), so there is no `opaque`/`axiom` callee contract for the proof
-- to consume. ASCII upper-casing is total and is exercised end-to-end by the
-- differential check.

/-- A Python text string, abstracted to the two properties this behavior
observes: its sequence of code points (`chars`) and whether it is a *wide* text
string (`wide`) as opposed to a native one. -/
structure PyStr where
  chars : List Char
  wide : Bool
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- The native, upper-cased normalization of a text string: its code points are
upper-cased and the result is a native (non-wide) text string regardless of the
input's width. -/
def normalizedMethod (m : PyStr) : PyStr :=
  { chars := m.chars.map Char.toUpper, wide := false }
-- pure-end

-- post-conditions-start
/-- The stored method is fully pinned to the supplied name: its content is the
upper-cased code points of the input, and it is a native (non-wide) text string
— independent of whether the supplied name was wide. No output component is left
free: the `wide` flag is pinned to `false` and every code point is pinned to the
upper-cased input code point at the same position. -/
def problem_spec_normalizeMethod (method : PyStr) (result : PyStr) : Prop :=
  result.chars = method.chars.map Char.toUpper ∧ result.wide = false
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the supplied name is upper-cased in place WITHOUT
-- first coercing it to a native text string. A wide supplied name therefore
-- stays wide (`result.wide = method.wide`), so a wide method name is carried
-- forward and later corrupts the assembled request.
def implementation_normalizeMethod (method : PyStr) : PyStr := Id.run do
  let mut m := method
  m := { m with chars := m.chars.map Char.toUpper }
  return m
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: when
-- the supplied name is wide the spec demands `result.wide = false` but the buggy
-- impl leaves `result.wide = true`.
theorem correct_normalizeMethod :
    ∀ (method : PyStr),
      problem_spec_normalizeMethod method
        (implementation_normalizeMethod method) := by
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  simp only [Id.run]
  exact ⟨rfl, rfl⟩
-- proof-end
