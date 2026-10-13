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
  -- the header slot starts at its pre-call value; only writes change it
  let mut clen : Option String := pre
  match body with
  | some n =>
      -- a body is present: its content length is reported
      clen := some (toString n)
  | none =>
      -- no body: only methods that may carry a payload write a zero length;
      -- for GET/HEAD nothing is written and the slot retains `pre`
      if method ≠ "GET" ∧ method ≠ "HEAD" then
        clen := some "0"
  return clen
-- impl-end

-- proof-start
theorem correct_prepare_content_length :
    ∀ (method : String) (pre : Option String) (body : Option Nat),
      problem_spec_prepare_content_length method pre body
        (implementation_prepare_content_length method pre body) := by
  intro method pre body
  unfold problem_spec_prepare_content_length implementation_prepare_content_length
  cases body with
  | some n => rfl
  | none =>
      simp only [Id.run]
      by_cases h : method = "GET" ∨ method = "HEAD"
      · rw [if_pos h]
        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
          rcases h with h | h <;> simp [h]
        simp only [if_neg h']
        rfl
      · rw [if_neg h]
        push_neg at h
        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
        simp only [if_pos h']
        rfl
-- proof-end
