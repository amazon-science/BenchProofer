import Mathlib
-- imports-end

/-!
Building a user's password-reset token state string.

A single-use password-reset token is derived from a state string that fingerprints
the security-sensitive parts of a user account. The token stays valid only while
that fingerprint is unchanged; as soon as any contributing piece of account state
changes, the recomputed fingerprint differs and the outstanding token no longer
matches.

The state string is the ordered concatenation of:

  * `pk`        — the user's primary-key value;
  * `password`  — the stored password representation;
  * `loginTs`   — the last-login timestamp (rendered empty when there is none);
  * `ts`        — the token's own timestamp; and
  * the user's email address.

A user is not required to have an email address. The email contribution is
therefore normalized: a present address contributes its own characters, while an
absent address (no value on the account) contributes the empty string — so the
state string is always well defined.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The mechanism
-- that locates and reads the user's email address is abstracted at the I/O
-- boundary into the `emailRaw` input (an optional string: the value carried by
-- the account, or none when the account has none). The state string is then
-- assembled structurally, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Normalize the optional email contribution to the characters it adds to the
state string: a present value contributes itself; an absent value contributes
the empty string. -/
def emailPart (emailRaw : Option String) : String := emailRaw.getD ""
-- pure-end

-- post-conditions-start
/-- The state string is exactly the ordered concatenation of the user's
primary-key value, password representation, last-login timestamp, token
timestamp, and (normalized) email contribution. Every component — including the
email — is pinned to its input, so the fingerprint is fully determined by the
account state and changes whenever any component (the email included) changes. -/
def problem_spec_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String)
    (result : String) : Prop :=
  result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw
-- post-conditions-end

-- impl-start
def implementation_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String) : String :=
  Id.run do
    let email := emailPart emailRaw
    let mut s := pk
    s := s ++ password
    s := s ++ loginTs
    s := s ++ ts
    s := s ++ email
    return s
-- impl-end

-- proof-start
theorem correct_tokenState :
    ∀ (pk password loginTs ts : String) (emailRaw : Option String),
      problem_spec_tokenState pk password loginTs ts emailRaw
        (implementation_tokenState pk password loginTs ts emailRaw) := by
  intro pk password loginTs ts emailRaw
  unfold problem_spec_tokenState implementation_tokenState
  rfl
-- proof-end
