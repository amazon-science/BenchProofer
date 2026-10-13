import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The body-length
-- computation (whether obtained by querying a seekable stream or by measuring a
-- value) is abstracted to the length itself (a `Nat`) — a type refinement, not a
-- callee — so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is a small,
-- finite case analysis on the body and the request method.
-- pure-end

-- post-conditions-start
/-- Determination of the message-length header for a prepared HTTP request.

Inputs:
* `method` — the (normalized, upper-case) HTTP request method.
* `pre`    — the value held by the message-length header slot *before* the
  call (`none` when the header is absent, e.g. the caller supplied no such
  header).
* `body`   — `some n` when a request body carrying `n` units of content is
  present; `none` when there is no request body.

`result : Option String` is the value held by the message-length header slot
*after* the call, with `none` meaning the header is absent.

Required behavior:
* If a body is present, the header is its content length, rendered in decimal.
* If there is no body, the header is the literal `"0"` for methods that may
  carry a payload; for the `"GET"` and `"HEAD"` methods (which must not
  advertise a zero-length body) the slot is **not written** — it keeps its
  prior value `pre` (in particular the header stays absent when it was
  absent before the call). -/
def problem_spec_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat)
    (result : Option String) : Prop :=
  match body with
  | some n => result = some (toString n)
  | none   =>
      if method = "GET" ∨ method = "HEAD" then result = pre
      else result = some "0"
-- post-conditions-end

-- impl-start
def implementation_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat) :
    Option String := Id.run do
  -- pre-patch behavior: the zero-length header is written unconditionally
  -- first (clobbering whatever value `pre` held), and is only overridden
  -- (never cleared) when a body is present. There is no method-dependent
  -- suppression, so GET/HEAD requests with no body still carry a zero-length
  -- header instead of retaining their pre-call slot value.
  let mut clen : Option String := some "0"
  match body with
  | some n =>
      clen := some (toString n)
  | none =>
      pure ()
  return clen
-- impl-end

-- proof-start
theorem correct_prepare_content_length :
    ∀ (method : String) (pre : Option String) (body : Option Nat),
      problem_spec_prepare_content_length method pre body
        (implementation_prepare_content_length method pre body) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
