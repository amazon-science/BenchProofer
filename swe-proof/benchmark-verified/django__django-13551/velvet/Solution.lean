import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single-use token-invalidation hash input is a
   straight-line concatenation of the user-state fields it depends on; it is
   modeled DEEPLY in the `pure` region (`hashInput`). Every component is a value
   already in hand (the string forms of the durable user-state fields and the
   timestamp); there is no unchanged callee whose contract the proof consumes,
   hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The slice of user state the single-use hash input depends on. It carries only
   the fields that feed the input, in their value (string) form:
     * `pk`             — the user's primary-key value;
     * `password`       — the stored password, which changes on a reset;
     * `loginTimestamp` — the last-login instant (already reduced to its stable
                          string form; empty when there is no last login);
     * `emailRaw`       — the user's email address when the account has one
                          (`some e`), or its absence (`none`) when the account
                          carries no email or a null email.
   Everything else about the user is orthogonal to this input (mapping.md §2). -/
structure UserState where
  pk : String
  password : String
  loginTimestamp : String
  emailRaw : Option String
deriving DecidableEq

/- The email address as it contributes to the hash input: the stored address
   when present, otherwise the empty string. An account without an email
   contributes nothing, so a user that never had an email is unaffected. -/
def emailValue (u : UserState) : String :=
  u.emailRaw.getD ""

/- The single-use token-invalidation hash input: the ordered concatenation of
   the durable user-state fields and the request timestamp, WITH the user's
   email folded in. Folding the email in is what makes changing the email
   invalidate any outstanding token: two states that differ only in the email
   produce different inputs, since the email is appended after a common prefix
   (string concatenation is left-cancellative). -/
def hashInput (u : UserState) (timestamp : String) : String :=
  u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single-use hash input from the user's durable state and the request
   timestamp. Desired behaviour: the input must incorporate the user's email
   address (when the account has one), so that updating the email changes the
   input and thereby invalidates any token built from the old input. An account
   with no email contributes the empty string and so is unaffected. -/
method makeHashInput (u : UserState) (timestamp : String) return (out : String)
  ensures out = hashInput u timestamp
  do
    -- impl-start
    -- The email folded into the input: the stored address when present,
    -- otherwise the empty string (an account with no/blank email).
    let email := u.emailRaw.getD ""
    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
    -- impl-end

prove_correct makeHashInput by
  loom_solve
  simp [hashInput, emailValue]
