import Mathlib
-- imports-end

-- axioms-start
/-- An identified principal in the credential store. Only its identity is
observed by the modeled behavior. -/
structure User where
  uid : Nat
deriving Repr, DecidableEq, Inhabited

/-- The credential-store lookup, keyed by the resolved login name. Returns the
matching principal, or `none` when no principal carries that name. UNCHANGED by
the modeled behavior; the same lookup is referenced in the specification and the
implementation. -/
opaque lookupUser : List Char → Option User

/-- Whether the supplied secret matches the stored principal's secret. UNCHANGED;
referenced identically in the specification and the implementation. -/
opaque passwordMatches : User → List Char → Bool

/-- Whether the stored principal is permitted to authenticate (e.g. is active).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque userAllowed : User → Bool

/-- The number of secret-hashing operations that checking the supplied secret
against the stored principal's secret performs — an inherent cost of the check
itself, determined by the principal's stored state and the supplied secret
(e.g. zero when the stored secret is unusable, one in the ordinary case).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque checkHashCount : User → List Char → Nat
-- axioms-end

-- pure-start
/-- The outcome of a credential check: the authenticated principal (if any) plus
the two observable resource costs — the number of credential-store queries and
the number of secret-hashing operations performed. -/
structure AuthOutcome where
  user : Option User
  queries : Nat
  hasherCalls : Nat
deriving Repr, DecidableEq, Inhabited

/-- The login name actually used: the positional name when present, otherwise the
fallback name taken from the keyword argument. -/
def resolveName (name fallback : Option (List Char)) : Option (List Char) :=
  if name.isNone then fallback else name
-- pure-end

-- post-conditions-start
/-- Relates the outcome of a credential check to its inputs.

When either the resolved login name or the secret is absent, the check is
abandoned immediately: no principal is returned and neither a credential-store
query nor a secret-hashing operation is performed (both costs are zero).

When both are present, exactly one credential-store query is performed; if no
principal carries that name, exactly one secret-hashing operation is performed
(to keep the timing uniform) and no principal is returned; if a principal is
found, exactly the secret-hashing operations inherent in checking the supplied
secret against it are performed, and the principal is returned exactly when its
secret matches and it is permitted to authenticate. Every component of the
outcome is pinned to the inputs in every branch. -/
def problem_spec_credentialAuth
    (name fallback secret : Option (List Char)) (result : AuthOutcome) : Prop :=
  match resolveName name fallback, secret with
  | some login, some pw =>
      result.queries = 1 ∧
      (match lookupUser login with
       | none => result.user = none ∧ result.hasherCalls = 1
       | some u =>
           result.hasherCalls = checkHashCount u pw ∧
           result.user = (if passwordMatches u pw && userAllowed u then some u else none))
  | _, _ =>
      result.user = none ∧ result.queries = 0 ∧ result.hasherCalls = 0
-- post-conditions-end

-- impl-start
def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  -- Pre-patch (buggy): no missing-credential guard. The credential-store query
  -- runs even when a credential is absent, and the secret hasher runs whenever
  -- a secret was supplied (an absent secret is rejected without hashing).
  let mut login := name
  if login.isNone then
    login := fallback
  match login with
  | some loginName =>
      match lookupUser loginName with
      | none =>
          -- Miss: the uniform-timing hash runs only when a secret was supplied.
          return { user := none, queries := 1,
                   hasherCalls := if secret.isSome then 1 else 0 }
      | some u =>
          match secret with
          | none =>
              -- Checking an absent secret fails without hashing.
              return { user := none, queries := 1, hasherCalls := 0 }
          | some pw =>
              -- Checking the supplied secret performs the check's inherent
              -- hashing cost, match or not.
              if passwordMatches u pw && userAllowed u then
                return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
              else
                return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | none =>
      -- A null name still issues the store query (`... WHERE name IS NULL`),
      -- finds nothing, and (when a secret was supplied) runs the hasher.
      return { user := none, queries := 1,
               hasherCalls := if secret.isSome then 1 else 0 }
-- impl-end

-- proof-start
theorem correct_credentialAuth :
    ∀ (name fallback secret : Option (List Char)),
    problem_spec_credentialAuth name fallback secret
      (implementation_credentialAuth name fallback secret) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
