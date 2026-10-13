import Mathlib
-- imports-end

/-!
Reporting the outcome of validating one remote hyperlink that carries both a
target document and an in-page fragment, when fragment-level validation is
enabled.

Validating such a link involves two independent observations about the server's
reply:

  * the reply's HTTP status code, and
  * whether the requested in-page fragment is present in the returned document.

The reported outcome is a triple (a status label, an explanatory message, a
numeric code). The desired behavior is that the reply's HTTP status is the FIRST
thing consulted: an error status in the 4xx/5xx range determines the outcome on
its own, independently of the fragment search. Within that error range two codes
are treated specially — an "unauthorized" status is reported as a working link,
and a "service unavailable" status is reported as an ignored link — while every
other error status is reported as a failure carrying the HTTP-level message.

Only when the status is NOT an error is the fragment consulted: a missing
fragment is reported as a failure carrying the fragment-level message, and a
present fragment defers to the outcome of the (unchanged) success continuation
that determines whether the link is plain-working or redirected.

The HTTP-level message, the fragment-level message, and the success-continuation
outcome are taken as arbitrary inputs here: the behavior pinned below is exactly
"which observation governs, and which message/outcome it routes through," for
every possible choice of those strings and that outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two server
-- observations (the reply's status code and whether the requested fragment is
-- present) are modeled as inputs `statusCode : Nat` and `anchorFound : Bool`;
-- the candidate explanatory messages and the outcome of the unchanged
-- success-continuation are modeled as arbitrary inputs (`httpErrMsg`,
-- `anchorErrMsg`, `onSuccess`). The modeled change is solely WHICH observation
-- governs the reported outcome, so the result is pinned for every choice of
-- those inputs. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The reported result of validating a hyperlink: a status label, an
explanatory message, and a numeric code (the analogue of the repo's
`Tuple[str, str, int]`). -/
structure Outcome where
  status : String
  info   : String
  code   : Int
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The reported outcome is fully pinned to the inputs:

  * when the status is an HTTP error (in the 4xx/5xx range) the result is
    determined by the status ALONE — "unauthorized" maps to a working report
    (with a constant unauthorized note and code 0), "service unavailable" maps to
    an ignored report carrying the HTTP-level message (code 0), and every other
    error status maps to a failure carrying the HTTP-level message (code 0);
  * otherwise, a missing fragment maps to a failure carrying the fragment-level
    message (code 0), and a present fragment defers to the success-continuation
    outcome.

No output component is left free: the status label, the message, and the code are
each pinned to the inputs in every branch. -/
def problem_spec_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome)
    (result : Outcome) : Prop :=
  result =
    (if 400 ≤ statusCode ∧ statusCode < 600 then
       if statusCode = 401 then ⟨"working", " - unauthorized", 0⟩
       else if statusCode = 503 then ⟨"ignored", httpErrMsg, 0⟩
       else ⟨"broken", httpErrMsg, 0⟩
     else if anchorFound = false then ⟨"broken", anchorErrMsg, 0⟩
     else onSuccess)
-- post-conditions-end

-- impl-start
def implementation_classifyLink
    (statusCode : Nat) (anchorFound : Bool)
    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do
  -- PRE-PATCH (buggy): the reply's HTTP status is never consulted on this path;
  -- the in-page fragment is the only observation that can make the link fail, so
  -- an error status is silently masked by the fragment search.
  if anchorFound = false then
    return ⟨"broken", anchorErrMsg, 0⟩
  return onSuccess
-- impl-end

-- proof-start
theorem correct_classifyLink :
    ∀ (statusCode : Nat) (anchorFound : Bool)
      (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome),
      problem_spec_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
        (implementation_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess) := by
  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess
  unfold problem_spec_classifyLink implementation_classifyLink
  simp only [Id.run, Id.pure_eq]
  split
  · split
    · rfl
    · split <;> rfl
  · cases anchorFound <;> rfl
-- proof-end
